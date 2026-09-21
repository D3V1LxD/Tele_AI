from datetime import timezone
import logging
import re

from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy import func

from app.ai.gemini import gemini
from app.config import settings
from app.database import SessionLocal
from app.email_rules import add_rule, list_rules, remove_rule
from app.gmail import create_authorization_url, disconnect_gmail, gmail_connected
from app.models import GmailCredential
from app.reminders import active_reminders, cancel_reminder, create_reminder

logger = logging.getLogger(__name__)


def authorized(update: Update) -> bool:
    user = update.effective_user
    if not user:
        return False
    allowed = user.id in settings.allowed_user_ids
    if not allowed:
        logger.warning("Unauthorized Telegram user ID: %s", user.id)
    return allowed


async def identify(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if update.effective_message and user:
        await update.effective_message.reply_text(f"Your Telegram user ID is: {user.id}")


async def reject_unauthorized(update: Update) -> None:
    if update.effective_message:
        await update.effective_message.reply_text("Unauthorized access.")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not authorized(update):
        return await reject_unauthorized(update)
    await update.effective_message.reply_text("🤖 Personal AI Assistant\n\nAsk me a question or use /help to see commands.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not authorized(update):
        return await reject_unauthorized(update)
    await update.effective_message.reply_text(
        "/ask <question>\n"
        "/remind <when> to <message>\n"
        "/myreminders\n"
        "/cancelreminder <id>\n"
        "/connect_gmail\n"
        "/gmail\n"
        "/gmail_count\n"
        "/disconnect_gmail\n"
        "/watch_email sender@example.com or example.com\n"
        "/email_rules\n"
        "/unwatch_email <rule_id>\n"
        "/status"
    )


async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not authorized(update):
        return await reject_unauthorized(update)
    question = " ".join(context.args).strip()
    if not question:
        await update.effective_message.reply_text("Usage: /ask <question>")
        return
    await update.effective_message.reply_text(await gemini.ask(question, update.effective_user.id))


async def natural_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not authorized(update):
        return await reject_unauthorized(update)
    text = update.effective_message.text.strip()
    lowered = text.lower()
    if lowered.startswith("remind me ") or lowered.startswith("remind "):
        request = text[10:] if lowered.startswith("remind me ") else text[7:]
        with SessionLocal() as session:
            reminder = create_reminder(session, update.effective_user.id, request)
        if reminder:
            local_time = reminder.scheduled_time.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            await update.effective_message.reply_text(f"✅ Reminder created for {local_time}: {reminder.message}")
            return
    email_match = re.search(
        r"(?:email|emails|mail)\s+(?:from|by)\s+([\w.+-]+@[\w.-]+|[a-z0-9.-]+\.[a-z]{2,})",
        lowered,
    )
    wants_email_alert = any(
        phrase in lowered
        for phrase in ("notify me", "alert me", "let me know", "watch for", "watch my")
    )
    if email_match and wants_email_alert:
        pattern = email_match.group(1)
        with SessionLocal() as session:
            rule = add_rule(session, update.effective_user.id, pattern)
        await update.effective_message.reply_text(f"✅ I will notify you about emails from {rule.pattern}.")
        return
    asks_gmail_access = "gmail" in lowered and any(
        phrase in lowered
        for phrase in ("access", "connected", "connection", "authorized", "permission")
    )
    if asks_gmail_access:
        with SessionLocal() as session:
            connected = gmail_connected(session, update.effective_user.id)
        await update.effective_message.reply_text(
            "✅ Gmail is connected and read-only access is available."
            if connected
            else "Gmail is not connected yet. Use /connect_gmail to authorize read-only access."
        )
        return
    await update.effective_message.reply_text(await gemini.ask(text, update.effective_user.id))


async def remind(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not authorized(update):
        return await reject_unauthorized(update)
    request = " ".join(context.args).strip()
    with SessionLocal() as session:
        reminder = create_reminder(session, update.effective_user.id, request)
    if not reminder:
        await update.effective_message.reply_text("I couldn't understand that date. Try: /remind tomorrow at 10 AM to call my supervisor")
        return
    local_time = reminder.scheduled_time.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    await update.effective_message.reply_text(f"✅ Reminder created for {local_time}: {reminder.message}")


async def my_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not authorized(update):
        return await reject_unauthorized(update)
    with SessionLocal() as session:
        reminders = active_reminders(session, update.effective_user.id)
    if not reminders:
        await update.effective_message.reply_text("You have no active reminders.")
        return
    await update.effective_message.reply_text("\n".join(f"{item.id}. {item.scheduled_time:%Y-%m-%d %H:%M UTC} — {item.message}" for item in reminders))


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not authorized(update):
        return await reject_unauthorized(update)
    try:
        reminder_id = int(context.args[0])
    except (IndexError, ValueError):
        await update.effective_message.reply_text("Usage: /cancelreminder <id>")
        return
    with SessionLocal() as session:
        cancelled = cancel_reminder(session, update.effective_user.id, reminder_id)
    await update.effective_message.reply_text("✅ Reminder cancelled." if cancelled else "I couldn't find that reminder.")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not authorized(update):
        return await reject_unauthorized(update)
    await update.effective_message.reply_text(f"🤖 Personal Assistant\n\nAI: {'🟢 Connected' if gemini.available else '🔴 Not configured'}\nTelegram: 🟢 Connected\nDatabase: 🟢 Connected\nTimezone: {settings.default_timezone}")


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not authorized(update):
        return await reject_unauthorized(update)
    with SessionLocal() as session:
        connected = gmail_connected(session, update.effective_user.id)
    await update.effective_message.reply_text(
        f"Timezone: {settings.default_timezone}\n"
        f"AI model: {settings.openrouter_model}\n"
        f"Gmail: {'Connected' if connected else 'Not connected'}"
    )


async def connect_gmail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not authorized(update):
        return await reject_unauthorized(update)
    try:
        with SessionLocal() as session:
            authorization_url = create_authorization_url(session, update.effective_user.id)
    except RuntimeError as exc:
        await update.effective_message.reply_text(f"Gmail is not configured: {exc}")
        return
    await update.effective_message.reply_text(
        "Open this Google authorization link, approve read-only Gmail access, then return here:\n\n"
        + authorization_url
    )


async def gmail_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not authorized(update):
        return await reject_unauthorized(update)
    with SessionLocal() as session:
        connected = gmail_connected(session, update.effective_user.id)
    await update.effective_message.reply_text("Gmail: Connected" if connected else "Gmail: Not connected")


async def gmail_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not authorized(update):
        return await reject_unauthorized(update)
    with SessionLocal() as session:
        linked_count = session.query(func.count(GmailCredential.telegram_user_id)).scalar() or 0
    await update.effective_message.reply_text(f"Gmail accounts linked to this bot: {linked_count}")


async def disconnect_gmail_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not authorized(update):
        return await reject_unauthorized(update)
    with SessionLocal() as session:
        disconnected = disconnect_gmail(session, update.effective_user.id)
    await update.effective_message.reply_text(
        "Gmail disconnected and stored authorization removed."
        if disconnected
        else "Gmail was not connected."
    )


async def add_email_rule_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not authorized(update):
        return await reject_unauthorized(update)
    pattern = " ".join(context.args).strip()
    if not pattern or ("@" not in pattern and "." not in pattern):
        await update.effective_message.reply_text("Usage: /watch_email sender@example.com or example.com")
        return
    with SessionLocal() as session:
        rule = add_rule(session, update.effective_user.id, pattern)
    await update.effective_message.reply_text(f"✅ I will notify you about emails from {rule.pattern}.")


async def email_rules_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not authorized(update):
        return await reject_unauthorized(update)
    with SessionLocal() as session:
        rules = list_rules(session, update.effective_user.id)
    await update.effective_message.reply_text("\n".join(f"{rule.id}. {rule.pattern}" for rule in rules) if rules else "No email notification rules configured.")


async def remove_email_rule_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not authorized(update):
        return await reject_unauthorized(update)
    try:
        rule_id = int(context.args[0])
    except (IndexError, ValueError):
        await update.effective_message.reply_text("Usage: /unwatch_email <rule_id>")
        return
    with SessionLocal() as session:
        removed = remove_rule(session, update.effective_user.id, rule_id)
    await update.effective_message.reply_text("✅ Email rule removed." if removed else "I couldn't find that email rule.")
