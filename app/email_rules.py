from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import EmailRule, ProcessedEmail


def add_rule(session: Session, telegram_user_id: int, pattern: str) -> EmailRule:
    normalized = pattern.strip().lower().lstrip("@")
    rule = EmailRule(telegram_user_id=telegram_user_id, pattern=normalized)
    session.add(rule)
    session.commit()
    session.refresh(rule)
    return rule


def list_rules(session: Session, telegram_user_id: int) -> list[EmailRule]:
    return list(session.scalars(select(EmailRule).where(EmailRule.telegram_user_id == telegram_user_id, EmailRule.enabled.is_(True)).order_by(EmailRule.id)))


def remove_rule(session: Session, telegram_user_id: int, rule_id: int) -> bool:
    rule = session.get(EmailRule, rule_id)
    if not rule or rule.telegram_user_id != telegram_user_id:
        return False
    rule.enabled = False
    session.commit()
    return True


def matches_rule(sender: str, pattern: str) -> bool:
    sender = sender.lower()
    address = sender.rsplit("<", 1)[-1].strip(" >")
    return address == pattern or address.endswith("@" + pattern)


def already_processed(session: Session, telegram_user_id: int, message_id: str) -> bool:
    return session.scalar(select(ProcessedEmail.id).where(ProcessedEmail.telegram_user_id == telegram_user_id, ProcessedEmail.gmail_message_id == message_id)) is not None


def mark_processed(session: Session, telegram_user_id: int, message_id: str) -> None:
    session.add(ProcessedEmail(telegram_user_id=telegram_user_id, gmail_message_id=message_id))
