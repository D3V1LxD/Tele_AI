import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from telegram import Bot

from app.database import SessionLocal
from app.models import Reminder

logger = logging.getLogger(__name__)


async def dispatch_due_reminders(bot: Bot) -> None:
    while True:
        try:
            now = datetime.now(timezone.utc)
            with SessionLocal() as session:
                due = list(session.scalars(select(Reminder).where(Reminder.status == "active", Reminder.scheduled_time <= now)))
                for reminder in due:
                    try:
                        await bot.send_message(chat_id=reminder.telegram_user_id, text=f"🔔 Reminder\n\n{reminder.message}")
                        reminder.status = "completed"
                        reminder.completed_at = now
                    except Exception:
                        logger.exception("Failed to deliver reminder %s", reminder.id)
                if due:
                    session.commit()
        except Exception:
            logger.exception("Reminder worker cycle failed")
        await asyncio.sleep(30)
