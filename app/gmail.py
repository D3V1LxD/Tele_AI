from datetime import datetime, timedelta, timezone
import json
import secrets

from cryptography.fernet import Fernet
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.config import settings
from app.models import GmailCredential, GmailOAuthState

GMAIL_READONLY_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"


def _client_config() -> dict[str, dict[str, dict[str, list[str] | str]]]:
    if not settings.google_client_id or not settings.google_client_secret:
        raise RuntimeError("GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are required")
    return {
        "web": {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.google_redirect_uri],
        }
    }


def _cipher() -> Fernet:
    if not settings.encryption_key:
        raise RuntimeError("ENCRYPTION_KEY is required for Gmail token storage")
    try:
        return Fernet(settings.encryption_key.encode("ascii"))
    except (ValueError, TypeError) as exc:
        raise RuntimeError("ENCRYPTION_KEY must be a valid Fernet key") from exc


def create_authorization_url(session: Session, telegram_user_id: int) -> str:
    client_config = _client_config()
    state = secrets.token_urlsafe(32)
    session.add(
        GmailOAuthState(
            state=state,
            telegram_user_id=telegram_user_id,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        )
    )
    session.commit()
    flow = Flow.from_client_config(
        client_config,
        scopes=[GMAIL_READONLY_SCOPE],
        state=state,
    )
    flow.redirect_uri = settings.google_redirect_uri
    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return authorization_url


def complete_authorization(session: Session, state: str, code: str) -> int:
    oauth_state = session.get(GmailOAuthState, state)
    expires_at = oauth_state.expires_at if oauth_state else None
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if not oauth_state or expires_at < datetime.now(timezone.utc):
        raise ValueError("OAuth state is invalid or expired")

    flow = Flow.from_client_config(
        _client_config(),
        scopes=[GMAIL_READONLY_SCOPE],
        state=state,
    )
    flow.redirect_uri = settings.google_redirect_uri
    flow.fetch_token(code=code)
    token_json = json.dumps(json.loads(flow.credentials.to_json()))
    encrypted_token = _cipher().encrypt(token_json.encode("utf-8")).decode("ascii")

    credential = session.get(GmailCredential, oauth_state.telegram_user_id)
    if credential:
        credential.encrypted_token = encrypted_token
    else:
        session.add(
            GmailCredential(
                telegram_user_id=oauth_state.telegram_user_id,
                encrypted_token=encrypted_token,
            )
        )
    session.delete(oauth_state)
    session.commit()
    return oauth_state.telegram_user_id


def disconnect_gmail(session: Session, telegram_user_id: int) -> bool:
    credential = session.get(GmailCredential, telegram_user_id)
    if not credential:
        return False
    session.delete(credential)
    session.execute(delete(GmailOAuthState).where(GmailOAuthState.telegram_user_id == telegram_user_id))
    session.commit()
    return True


def gmail_connected(session: Session, telegram_user_id: int) -> bool:
    return session.get(GmailCredential, telegram_user_id) is not None


def gmail_service(session: Session, telegram_user_id: int):
    credential = session.get(GmailCredential, telegram_user_id)
    if not credential:
        return None
    token_json = _cipher().decrypt(credential.encrypted_token.encode("ascii")).decode("utf-8")
    credentials = Credentials.from_authorized_user_info(json.loads(token_json), scopes=[GMAIL_READONLY_SCOPE])
    service = build("gmail", "v1", credentials=credentials, cache_discovery=False)
    return service


def recent_messages(session: Session, telegram_user_id: int, limit: int = 50) -> list[dict]:
    service = gmail_service(session, telegram_user_id)
    if service is None:
        return []
    response = service.users().messages().list(userId="me", maxResults=limit, q="in:anywhere newer_than:7d").execute()
    messages = []
    for item in response.get("messages", []):
        message = service.users().messages().get(userId="me", id=item["id"], format="metadata", metadataHeaders=["From", "Subject", "Date"]).execute()
        headers = {header["name"].lower(): header["value"] for header in message.get("payload", {}).get("headers", [])}
        messages.append({
            "id": message["id"],
            "sender": headers.get("from", ""),
            "subject": headers.get("subject", "(no subject)"),
            "date": headers.get("date", ""),
            "snippet": message.get("snippet", ""),
        })
    return messages
