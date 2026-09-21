# Project: Personal AI Telegram Assistant

## 1. Project Overview

Build a secure, modular, production-ready **personal AI assistant accessible through Telegram**.

The assistant will run on **Heroku** and use the **Google Gemini API** as its primary AI/LLM engine. It should also integrate with **Gmail through Google OAuth 2.0**, allowing the assistant to monitor emails, search/summarize emails, and send Telegram notifications when relevant emails arrive.

The bot should also support reminders, alarms, scheduled notifications, personal memory, and natural-language interaction.

The overall goal is to create a personal "Jarvis-style" assistant that I can communicate with entirely through Telegram.

---

# 2. Core Architecture

Use the following architecture:

```text
                    ┌─────────────────────┐
                    │      Telegram       │
                    │       User          │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Telegram Bot      │
                    │    Interface        │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    Heroku Backend   │
                    │                     │
                    │  AI Agent           │
                    │  Command Handler    │
                    │  Gmail Service      │
                    │  Reminder Service   │
                    │  Memory Service     │
                    │  Notification       │
                    └───────┬───────┬─────┘
                            │       │
                 ┌──────────┘       └──────────┐
                 ▼                             ▼
        ┌─────────────────┐           ┌─────────────────┐
        │   Gemini API    │           │   PostgreSQL    │
        │   AI/LLM        │           │   Database      │
        └─────────────────┘           └─────────────────┘
                 │
                 ▼
        ┌─────────────────┐
        │     Gmail       │
        │    API/OAuth    │
        └─────────────────┘
```

The application should be designed so that additional integrations can be added later without rewriting the entire system.

---

# 3. Technology Requirements

Prefer the following technology stack:

### Backend

* Python 3.11+
* FastAPI or Flask
* `python-telegram-bot` or another actively maintained Telegram Bot API library
* Async architecture where appropriate

### AI

* Google Gemini API
* Use the official/current Google Gemini SDK/API
* Keep the Gemini integration modular so another LLM provider can be added later

### Database

* PostgreSQL
* SQLAlchemy or another clean ORM/database abstraction
* Database migrations using Alembic if appropriate

### Authentication

* Google OAuth 2.0
* Gmail API
* Secure token storage

### Deployment

* Heroku
* Heroku Web Dyno for HTTP/webhook functionality
* Heroku Worker Dyno for background tasks
* Heroku PostgreSQL
* Environment variables/config vars for secrets

### Optional

* Redis if required for task queues or distributed scheduling
* APScheduler or another reliable scheduling mechanism for reminders/background jobs

---

# 4. Telegram Bot

The Telegram bot should be the primary user interface.

The bot must support both:

1. Traditional Telegram commands
2. Natural-language instructions

For example:

```text
/remind me to call my supervisor tomorrow at 10 AM
```

and:

```text
Remind me tomorrow at 10 AM to call my supervisor.
```

should produce the same result.

---

# 5. Telegram Commands

Implement at least the following commands:

### General

```text
/start
/help
/status
/settings
```

### AI

```text
/ask <question>
```

Example:

```text
/ask Explain what a ballast system does in a ship.
```

However, the user should also be able to simply write:

```text
Explain what a ballast system does in a ship.
```

and have the AI respond.

---

# 6. Reminder System

Create a complete reminder system.

The user should be able to create reminders using natural language.

Examples:

```text
Remind me tomorrow at 10 AM to submit my assignment.

Remind me in 30 minutes to check the oven.

Remind me every Monday at 8 AM to review my weekly tasks.

Remind me on September 30 at 5 PM about my meeting.
```

The assistant should parse:

* Reminder text
* Date
* Time
* Time zone
* Recurrence
* Optional priority

Store reminders in PostgreSQL.

Example database structure:

```text
reminders
---------
id
telegram_user_id
message
scheduled_time
timezone
recurrence
status
created_at
completed_at
```

When a reminder becomes due:

```text
🔔 Reminder

Submit your assignment.
```

must be sent to Telegram.

The scheduler must continue working even when the user is not actively communicating with the bot.

---

# 7. Recurring Reminders

Support:

* Daily
* Weekly
* Monthly
* Custom recurring schedules

Examples:

```text
Remind me every day at 8 PM to study.

Remind me every Friday at 6 PM to review my projects.

Remind me on the 1st of every month to pay my bills.
```

Provide commands to:

```text
List my reminders
Cancel a reminder
Edit a reminder
Pause a reminder
Resume a reminder
```

For example:

```text
/myreminders
/cancelreminder <id>
```

Natural-language cancellation should also work:

```text
Cancel my reminder about the assignment.
```

---

# 8. Gmail Integration

Implement Gmail integration using **Google OAuth 2.0**.

Do NOT ask the user for their Gmail password.

The authentication flow should be:

```text
Telegram
   ↓
/connect_gmail
   ↓
Google OAuth
   ↓
User grants permission
   ↓
OAuth callback
   ↓
Securely store token
   ↓
Gmail connected
```

After successful authentication:

```text
✅ Gmail connected successfully.
```

---

# 9. Gmail Permissions

Use the minimum required Gmail scopes.

Initially support read-only functionality.

The assistant should be able to:

* Read emails
* Search emails
* Detect new emails
* Retrieve sender
* Retrieve subject
* Retrieve date
* Retrieve message body where permitted
* Summarize emails
* Identify potentially important emails

Do NOT request email sending permissions unless explicitly implemented later.

---

# 10. New Email Notifications

The assistant should notify the user through Telegram when new emails arrive.

Example:

```text
📧 New Email

From: professor@example.com
Subject: Final Project Submission

Received: 6:42 PM

Preview:
Please submit your final project report...
```

The notification should contain a button such as:

```text
[Summarize]
[Open Gmail]
[Ignore]
```

Do not expose sensitive email content unnecessarily.

---

# 11. Email Filtering

Allow the user to define notification rules.

Examples:

```text
Notify me immediately when I receive an email from my university.

Notify me when I receive an email containing "interview".

Don't notify me about newsletters.

Don't notify me about promotional emails.

Only notify me about important emails.
```

Store filtering rules in PostgreSQL.

Example:

```text
email_rules
-----------
id
telegram_user_id
sender_pattern
subject_pattern
keyword
rule_type
enabled
created_at
```

---

# 12. Email Summarization

The Gemini API should be able to summarize emails.

Examples:

```text
Summarize my latest email.

Summarize my unread emails.

What did my professor say in the latest email?

Show me the important emails from today.
```

The system should retrieve the relevant Gmail content first and then send only the required content to Gemini.

Avoid sending unnecessary personal email data to the AI API.

---

# 13. AI Agent

Gemini should act as the reasoning engine.

The assistant should support tool/function calling where appropriate.

Potential tools:

```text
create_reminder()
list_reminders()
cancel_reminder()
update_reminder()

search_gmail()
get_email()
summarize_email()

get_current_time()
get_user_settings()

save_memory()
retrieve_memory()
delete_memory()
```

The AI should determine which tool is required from the user's natural-language request.

Example:

User:

```text
Remind me tomorrow at 9 AM to call my supervisor.
```

Gemini determines:

```text
create_reminder(
    message="Call my supervisor",
    datetime="...",
)
```

The backend executes the function and returns:

```text
Reminder created successfully.
```

The AI should NOT directly access the database or Gmail credentials. All actions must go through controlled backend tools/functions.

---

# 14. AI Memory

Implement optional long-term memory.

The assistant should be able to remember useful information explicitly provided by the user.

Example:

```text
Remember that my thesis presentation is on October 10.
```

Then later:

```text
When is my thesis presentation?
```

The system should retrieve the stored memory.

Database:

```text
memories
--------
id
telegram_user_id
memory_text
category
created_at
updated_at
```

Memory should NOT automatically store highly sensitive information unless explicitly requested.

Provide:

```text
What do you remember about me?

Forget what you remember about X.
```

---

# 15. User Settings

Create a settings system.

Allow the user to configure:

* Time zone
* Notification preferences
* Gmail notification settings
* Reminder preferences
* AI response style
* Email filtering
* Quiet hours
* Memory preferences

For example:

```text
My timezone is Asia/Dhaka.

Don't send notifications between 11 PM and 7 AM.

Only notify me immediately for important emails.
```

Default timezone should be configurable and should not be hard-coded.

---

# 16. Security Requirements

Security is extremely important.

NEVER hard-code:

```text
Telegram Bot Token
Gemini API Key
Google Client Secret
Database Password
OAuth Tokens
```

Use environment variables/configuration.

Example:

```text
TELEGRAM_BOT_TOKEN=
GEMINI_API_KEY=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
DATABASE_URL=
ENCRYPTION_KEY=
```

Use `.env` locally but NEVER commit `.env` to GitHub.

Add:

```text
.env
*.env
__pycache__/
```

to `.gitignore`.

---

# 17. OAuth Security

OAuth tokens must be securely stored.

Prefer encryption at rest for refresh tokens.

Never expose:

* Access tokens
* Refresh tokens
* Client secrets
* API keys

through Telegram messages, logs, error messages, or HTTP responses.

---

# 18. Telegram Security

Initially make the bot private to my Telegram account.

Implement an allowed-user system:

```text
ALLOWED_TELEGRAM_USER_IDS=
```

Only authorized Telegram user IDs can interact with the assistant.

If an unauthorized user sends a message:

```text
Unauthorized access.
```

Do not reveal whether the bot is connected to Gmail or other services.

---

# 19. Logging

Implement structured logging.

Log:

* Application startup
* Errors
* Tool execution
* Reminder execution
* Gmail synchronization events
* Authentication events

DO NOT log:

* Gmail passwords
* OAuth tokens
* Gemini API keys
* Full email contents
* Sensitive personal data

---

# 20. Background Worker

Create a separate background worker responsible for:

* Reminder processing
* Gmail monitoring
* Scheduled tasks
* Notification delivery
* Periodic token/watch renewal
* Cleanup tasks

The worker must not block Telegram message handling.

Recommended architecture:

```text
Heroku Web Dyno
        │
        ├── Telegram webhook
        ├── OAuth callback
        └── Health endpoint

Heroku Worker Dyno
        │
        ├── Reminder scheduler
        ├── Gmail monitor
        ├── Notification service
        └── Background tasks

PostgreSQL
        │
        ├── Users
        ├── Reminders
        ├── Memories
        ├── Gmail accounts
        └── Notification rules
```

---

# 21. Gmail Monitoring Strategy

Prefer Gmail's push notification mechanism where practical.

Use Gmail API watch/Pub/Sub if the deployment architecture supports it correctly.

If implementing polling initially, make the polling interval configurable.

Do not create an inefficient system that makes excessive Gmail API requests.

The Gmail monitoring system should also avoid sending duplicate notifications.

Store processed email/message IDs.

Example:

```text
processed_emails
----------------
id
telegram_user_id
gmail_message_id
processed_at
```

---

# 22. Duplicate Prevention

The bot must not repeatedly notify the user about the same email or reminder.

For email notifications:

```text
Gmail message ID
       ↓
Already processed?
   ├── YES → Ignore
   └── NO  → Process → Notify → Store ID
```

For reminders:

```text
Reminder due
    ↓
Already executed?
    ├── YES → Ignore
    └── NO → Send → Mark executed
```

---

# 23. Error Handling

The bot must gracefully handle:

* Gemini API failure
* Gmail API failure
* OAuth failure
* Expired OAuth tokens
* Database failure
* Telegram API failure
* Invalid reminder date
* Invalid user input
* Rate limits
* Network failures

Example:

```text
I couldn't access Gmail right now.
Please try again in a few minutes.
```

Do not expose technical stack traces to the user.

Log detailed errors server-side.

---

# 24. AI Conversation Handling

Maintain conversation context where appropriate.

Example:

User:

```text
What's my latest email?
```

Bot:

```text
Your latest email is from your supervisor.
```

User:

```text
Summarize it.
```

The bot should understand that "it" refers to the previously retrieved email.

Conversation history should be limited to a sensible amount to control Gemini API costs.

---

# 25. Commands / Interface

Provide a clean command menu.

Suggested commands:

```text
/start
/help
/ask
/remind
/myreminders
/cancelreminder
/gmail
/connect_gmail
/disconnect_gmail
/inbox
/searchmail
/memory
/settings
/status
```

Also support natural-language interaction so the user does not need to memorize commands.

---

# 26. Status Command

Implement:

```text
/status
```

Example output:

```text
🤖 Personal Assistant

AI:              🟢 Gemini Connected
Telegram:        🟢 Connected
Gmail:           🟢 Connected
Database:        🟢 Connected
Reminder Engine: 🟢 Running

Timezone:
Asia/Dhaka

Active reminders:
5
```

Do not expose credentials or internal infrastructure details.

---

# 27. Health Check

Create:

```text
GET /health
```

Response:

```json
{
  "status": "ok"
}
```

This endpoint can be used to verify that the Heroku web dyno is running.

---

# 28. Project Structure

Use a clean modular project structure similar to:

```text
personal-ai-assistant/
│
├── app/
│   ├── main.py
│   ├── config.py
│   │
│   ├── telegram/
│   │   ├── bot.py
│   │   ├── handlers.py
│   │   └── keyboards.py
│   │
│   ├── ai/
│   │   ├── gemini.py
│   │   ├── agent.py
│   │   └── tools.py
│   │
│   ├── gmail/
│   │   ├── oauth.py
│   │   ├── client.py
│   │   └── monitor.py
│   │
│   ├── reminders/
│   │   ├── scheduler.py
│   │   └── service.py
│   │
│   ├── memory/
│   │   └── service.py
│   │
│   ├── database/
│   │   ├── models.py
│   │   ├── database.py
│   │   └── migrations/
│   │
│   └── utils/
│       ├── security.py
│       └── logging.py
│
├── tests/
│
├── requirements.txt
├── Procfile
├── runtime.txt
├── .env.example
├── .gitignore
├── README.md
└── alembic.ini
```

Modify the structure if a better architecture is appropriate.

---

# 29. Heroku Deployment

Create a Heroku-ready deployment configuration.

Example Procfile:

```text
web: gunicorn app.main:app
worker: python -m app.worker
```

If using FastAPI, use an appropriate ASGI server configuration.

Provide complete instructions for:

1. Creating the Telegram bot with BotFather
2. Creating a Google Cloud project
3. Enabling Gmail API
4. Creating Google OAuth credentials
5. Creating Gemini API credentials
6. Creating a Heroku application
7. Creating Heroku PostgreSQL
8. Setting environment variables
9. Deploying from GitHub
10. Running database migrations
11. Configuring web and worker dynos
12. Testing Telegram
13. Testing Gmail OAuth
14. Testing reminders

---

# 30. Environment Variables

Create `.env.example`:

```text
TELEGRAM_BOT_TOKEN=

GEMINI_API_KEY=

GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=

DATABASE_URL=

ENCRYPTION_KEY=

ALLOWED_TELEGRAM_USER_IDS=

APP_BASE_URL=
```

Do not include actual credentials.

---

# 31. Cost Optimization

Design the system to minimize unnecessary API usage.

For Gemini:

* Avoid sending excessive conversation history
* Summarize long conversations
* Use the appropriate Gemini model for each task
* Avoid calling Gemini for simple deterministic commands
* Use normal backend functions for reminders and database operations

For Gmail:

* Avoid unnecessary polling
* Cache processed message IDs
* Use push notifications where practical
* Avoid repeatedly downloading the same email

---

# 32. Important Design Principle

The AI should NOT control everything directly.

Use this architecture:

```text
User
 ↓
Gemini
 ↓
Tool decision
 ↓
Backend validates request
 ↓
Backend executes tool
 ↓
Result returned to Gemini
 ↓
Telegram response
```

For example:

```text
User:
"Remind me tomorrow at 9 AM to submit my thesis."

Gemini:
create_reminder()

Backend:
Validate date/time
Validate user
Save reminder

Gemini:
Generate confirmation

Telegram:
"✅ Reminder created for tomorrow at 9 AM."
```

This prevents the LLM from directly performing uncontrolled actions.

---

# 33. Future Integrations

Design the architecture so the following can be added later:

### Google Calendar

```text
What's on my calendar tomorrow?
```

### Google Drive

```text
Find my thesis PDF.
```

### Weather

```text
Will it rain tomorrow?
```

### Web Search

```text
Search the latest research papers on AUV fish detection.
```

### Spotify

```text
Create a playlist for studying.
```

### Task Management

```text
Add "finish thesis methodology" to my tasks.
```

### Voice

Eventually support Telegram voice messages:

```text
Voice message
      ↓
Speech-to-text
      ↓
Gemini
      ↓
Action
      ↓
Telegram response
```

The initial implementation does not need these features, but the architecture should make them easy to add.

---

# 34. User Experience

The bot should feel like a personal assistant rather than a collection of commands.

For example:

```text
User:
I just got an email from my professor. What does he want?

Assistant:
Your professor's latest email asks you to submit the revised methodology section by September 25.

User:
Remind me two days before.

Assistant:
Sure. I'll remind you on September 23.
```

Another example:

```text
User:
What do I have tomorrow?

Assistant:
You have:
• 9:00 AM — Thesis meeting
• 2:00 PM — Submit assignment
• 8:00 PM — Study reminder
```

---

# 35. Privacy

Treat this as a private personal assistant.

The application should:

* Minimize stored email content
* Encrypt sensitive OAuth tokens
* Never expose credentials
* Restrict Telegram access
* Provide Gmail disconnect functionality
* Allow deletion of stored memories
* Allow deletion of processed email metadata
* Avoid unnecessary third-party data sharing

Gemini should receive only the information required to answer the user's request.

---

# 36. Testing Requirements

Before deployment, test:

### Telegram

* `/start`
* `/help`
* Normal conversation
* Unauthorized users
* Error handling

### Gemini

* Normal question
* Tool calling
* Invalid tool parameters
* API failure

### Gmail

* OAuth login
* Token refresh
* Email retrieval
* Email search
* New email notification
* Duplicate prevention
* Disconnect

### Reminders

* One-time reminder
* Recurring reminder
* Cancellation
* Editing
* Timezone handling
* Restart recovery
* Duplicate prevention

### Database

* Connection failure
* Migration
* Data persistence

### Deployment

* Heroku startup
* Web dyno
* Worker dyno
* Environment variables
* PostgreSQL
* Health endpoint

---

# 37. Deliverables

Produce a complete working project, not just pseudocode.

Provide:

1. Complete source code
2. `requirements.txt`
3. `Procfile`
4. `.env.example`
5. `.gitignore`
6. Database models
7. Database migrations
8. Telegram bot implementation
9. Gemini integration
10. Gmail OAuth implementation
11. Gmail monitoring
12. Reminder scheduler
13. PostgreSQL integration
14. Security implementation
15. Error handling
16. Logging
17. Tests
18. README
19. Heroku deployment instructions
20. Google Cloud OAuth setup instructions
21. Telegram BotFather setup instructions

---

# 38. Development Approach

Do not attempt to build everything as one huge script.

Build the system incrementally:

### Phase 1

Telegram + Gemini

### Phase 2

PostgreSQL + reminders

### Phase 3

Google OAuth + Gmail

### Phase 4

Email monitoring + notifications

### Phase 5

AI tool/function calling

### Phase 6

Memory

### Phase 7

Security hardening

### Phase 8

Heroku deployment

### Phase 9

Testing and documentation

After each phase, verify that the previous functionality still works.

---

# 39. Final Requirement

The final application should allow me to interact with my personal AI assistant almost entirely through Telegram.

I should be able to say things like:

```text
"What's in my latest email?"

"Remind me tomorrow at 9 AM to submit my thesis."

"Notify me whenever my professor emails me."

"Summarize today's important emails."

"What reminders do I have?"

"Cancel my 5 PM reminder."

"Remember that my thesis presentation is on October 10."

"What do you remember about my thesis?"

"Don't notify me about promotional emails."

"Search my Gmail for emails containing 'scholarship'."

"Explain this email to me."

"What should I prioritize today?"
```

The system should intelligently determine whether the request requires:

* Gemini
* Gmail
* Reminder service
* Memory
* Database
* Multiple tools

and execute the appropriate backend function securely.

The final product should be **modular, secure, maintainable, scalable, Heroku-compatible, and easy to extend with additional AI tools and integrations later.**
