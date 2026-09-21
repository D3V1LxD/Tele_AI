import asyncio
import logging

from telegram import BotCommand, BotCommandScopeChat, BotCommandScopeDefault
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from app.config import settings
from app.database import init_database
from app.email_worker import monitor_gmail
from app.reminder_worker import dispatch_due_reminders
from app.telegram.handlers import add_email_rule_command, ask, cancel, connect_gmail, disconnect_gmail_command, email_rules_command, gmail_count, gmail_status, help_command, identify, my_reminders, natural_language, remind, remove_email_rule_command, settings_command, start, status


async def set_commands(application: Application) -> None:
    asyncio.create_task(dispatch_due_reminders(application.bot), name="reminder-dispatcher")
    asyncio.create_task(monitor_gmail(application.bot), name="gmail-monitor")
    commands = [
        BotCommand("start", "Start the assistant"),
        BotCommand("help", "Show available commands"),
        BotCommand("ask", "Ask the AI a question"),
        BotCommand("remind", "Create a reminder"),
        BotCommand("myreminders", "List active reminders"),
        BotCommand("cancelreminder", "Cancel a reminder"),
        BotCommand("status", "Show service status"),
        BotCommand("settings", "Show assistant settings"),
        BotCommand("id", "Show your Telegram user ID"),
        BotCommand("connect_gmail", "Connect Gmail with Google OAuth"),
        BotCommand("gmail", "Show Gmail connection status"),
        BotCommand("gmail_count", "Count linked Gmail accounts"),
        BotCommand("disconnect_gmail", "Disconnect Gmail"),
        BotCommand("watch_email", "Notify for an email or domain"),
        BotCommand("email_rules", "List email notification rules"),
        BotCommand("unwatch_email", "Remove an email notification rule"),
    ]
    await application.bot.set_my_commands([], scope=BotCommandScopeDefault())
    for user_id in settings.allowed_user_ids:
        await application.bot.set_my_commands(
            commands,
            scope=BotCommandScopeChat(chat_id=user_id),
        )


def build_application() -> Application:
    settings.validate_bot_runtime()
    init_database()
    application = Application.builder().token(settings.telegram_bot_token).post_init(set_commands).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("ask", ask))
    application.add_handler(CommandHandler("remind", remind))
    application.add_handler(CommandHandler("myreminders", my_reminders))
    application.add_handler(CommandHandler("cancelreminder", cancel))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(CommandHandler("id", identify))
    application.add_handler(CommandHandler("connect_gmail", connect_gmail))
    application.add_handler(CommandHandler("gmail", gmail_status))
    application.add_handler(CommandHandler("gmail_count", gmail_count))
    application.add_handler(CommandHandler("disconnect_gmail", disconnect_gmail_command))
    application.add_handler(CommandHandler("watch_email", add_email_rule_command))
    application.add_handler(CommandHandler("email_rules", email_rules_command))
    application.add_handler(CommandHandler("unwatch_email", remove_email_rule_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, natural_language))
    return application


def main() -> None:
    logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    build_application().run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    main()
