from datetime import timezone

import dateparser
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Reminder, User


def ensure_user(session: Session, telegram_user_id: int) -> User:
    user = session.get(User, telegram_user_id)
    if user is None:
        user = User(telegram_user_id=telegram_user_id, timezone=settings.default_timezone)
        session.add(user)
        session.commit()
    return user


def create_reminder(session: Session, telegram_user_id: int, request: str) -> Reminder | None:
    marker = request.lower().find(" to ")
    date_text = request[:marker] if marker >= 0 else request
    parsed = dateparser.parse(date_text, settings={"RETURN_AS_TIMEZONE_AWARE": True, "TIMEZONE": settings.default_timezone})
    if parsed is None:
        return None
    message = request[marker + 4 :].strip() if marker >= 0 else request.strip()
    user = ensure_user(session, telegram_user_id)
    reminder = Reminder(telegram_user_id=user.telegram_user_id, message=message or "Reminder", scheduled_time=parsed.astimezone(timezone.utc))
    session.add(reminder)
    session.commit()
    session.refresh(reminder)
    return reminder


def active_reminders(session: Session, telegram_user_id: int) -> list[Reminder]:
    return list(session.scalars(select(Reminder).where(Reminder.telegram_user_id == telegram_user_id, Reminder.status == "active").order_by(Reminder.scheduled_time)))


def cancel_reminder(session: Session, telegram_user_id: int, reminder_id: int) -> bool:
    reminder = session.get(Reminder, reminder_id)
    if not reminder or reminder.telegram_user_id != telegram_user_id:
        return False
    reminder.status = "cancelled"
    session.commit()
    return True
