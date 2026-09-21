from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse

from app.database import SessionLocal, init_database
from app.gmail import complete_authorization

app = FastAPI(title="Personal AI Telegram Assistant")


@app.on_event("startup")
def startup() -> None:
    init_database()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def root() -> dict[str, str]:
    return {"name": "Personal AI Telegram Assistant", "status": "running"}


@app.get("/oauth/google/callback", response_class=HTMLResponse)
def google_oauth_callback(
    state: str = Query(...),
    code: str | None = Query(default=None),
    error: str | None = Query(default=None),
) -> str:
    if error:
        return "<h1>Gmail authorization was cancelled</h1><p>You can close this window.</p>"
    if not code:
        return "<h1>Gmail authorization failed</h1><p>No authorization code was provided.</p>"
    try:
        with SessionLocal() as session:
            complete_authorization(session, state, code)
    except (RuntimeError, ValueError) as exc:
        return HTMLResponse(
            f"<h1>Gmail authorization failed</h1><p>{exc}</p>",
            status_code=400,
        )
    return "<h1>Gmail connected successfully.</h1><p>You can close this window and return to Telegram.</p>"
