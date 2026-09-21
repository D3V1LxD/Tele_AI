import asyncio
import logging

from telegram import Bot
from sqlalchemy import select

from app.database import SessionLocal
from app.email_rules import already_processed, list_rules, mark_processed, matches_rule
from app.gmail import recent_messages
from app.models import GmailCredential

logger = logging.getLogger(__name__)


def fetch_messages_for_user(user_id: int) -> list[dict]:
    with SessionLocal() as session:
        return recent_messages(session, user_id)


async def monitor_gmail(bot: Bot) -> None:
    while True:
        try:
            with SessionLocal() as session:
                user_ids = list(session.scalars(select(GmailCredential.telegram_user_id)))
                for user_id in user_ids:
                    rules = list_rules(session, user_id)
                    if not rules:
                        continue
                    try:
                        messages = await asyncio.to_thread(fetch_messages_for_user, user_id)
                        for message in messages:
                            if already_processed(session, user_id, message["id"]):
                                continue
                            if any(matches_rule(message["sender"], rule.pattern) for rule in rules):
                                await bot.send_message(
                                    chat_id=user_id,
                                    text=(f"📧 New matching email\n\nFrom: {message['sender']}\n"
                                          f"Subject: {message['subject']}\nDate: {message['date']}\n\n"
                                          f"Preview: {message['snippet'][:500]}"),
                                )
                            mark_processed(session, user_id, message["id"])
                        session.commit()
                    except Exception:
                        logger.exception("Gmail monitoring failed for user %s", user_id)
        except Exception:
            logger.exception("Gmail monitor cycle failed")
        await asyncio.sleep(60)
