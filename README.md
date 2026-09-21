# Personal AI Telegram Assistant

This private Telegram assistant provides OpenRouter-backed questions, persistent reminders, and read-only Gmail OAuth access. The deployment shape is a FastAPI web dyno plus a Telegram polling worker.

## Local setup

1. Use Python 3.11 or newer and create a virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and set `TELEGRAM_BOT_TOKEN`, `ALLOWED_TELEGRAM_USER_IDS`, and `OPENROUTER_API_KEY` for AI replies.
4. Start the bot with `python -m app.telegram.bot`.
5. Start the health service with `uvicorn app.main:app --reload` and verify `GET /health`.

The default local database is SQLite. Set `DATABASE_URL` to a PostgreSQL SQLAlchemy URL for Heroku Postgres.

## OpenRouter models

Set `OPENROUTER_MODEL` to any OpenRouter model ID. The default is `nvidia/nemotron-3-ultra-550b-a55b:free`. The other supplied examples can be selected with `google/gemma-4-26b-a4b-it:free` or `qwen/qwen3.8-27b:free`. Reasoning is enabled by default, and the assistant preserves `reasoning_details` between messages for each Telegram user.

## Gmail connection

1. In Google Cloud Console, create/select a project and enable the Gmail API.
2. Configure the OAuth consent screen. For local testing, add your Google account as a test user if the app is in testing mode.
3. Create an OAuth 2.0 Client ID for a Web application.
4. Add this exact authorized redirect URI:
   `http://127.0.0.1:8000/oauth/google/callback`
5. Put the client ID and client secret in `.env` as `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`.
6. Generate a Fernet key for `ENCRYPTION_KEY`; do not reuse the Telegram token or a Google secret.
7. Restart the bot and send `/connect_gmail`. Open the Google link it returns and approve the read-only Gmail permission.
8. Use `/gmail` to verify the connection. `/disconnect_gmail` removes the stored authorization.

The bot requests only `gmail.readonly`; it never asks for your Gmail password or permission to send mail. OAuth tokens are encrypted before they are stored in the database.

## Email notifications

After connecting Gmail, send `/watch_email sender@example.com` or `/watch_email example.com`. The worker checks connected Gmail accounts every minute, reads recent message metadata and snippets, and notifies you only when a sender or domain rule matches. Use `/email_rules` to list rules and `/unwatch_email <rule_id>` to remove one. Each Gmail message ID is stored once so it cannot trigger duplicate notifications.

Reminders can be created with `/remind tomorrow at 10 AM to call my supervisor` or by writing `Remind me tomorrow at 10 AM to call my supervisor`. The worker sends due reminders automatically even when you are not chatting with the bot.

## Security

Never commit `.env`, tokens, or API keys. The bot rejects every Telegram user whose ID is not listed in `ALLOWED_TELEGRAM_USER_IDS`.

## Heroku

Set the variables from `.env.example`, provision Heroku Postgres, and scale one `web` dyno and one `worker` dyno. The worker runs the Telegram bot process. Use Python 3.11 as specified by `runtime.txt`.
