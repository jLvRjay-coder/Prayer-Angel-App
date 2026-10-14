---
title: Prayer Angel
emoji: 😇
colorFrom: blue
colorTo: yellow
sdk: docker
app_port: 7860
tags:
- streamlit
pinned: false
short_description: A faith-based reflection app helping users connect with God.
license: other
---

# Prayer Angel — Beyond the Message

A faith-based reflection app (Streamlit + Docker).

## Privacy Promise

Prayer Angel (Angel Chat) is designed as a **safe space — not a profile**.

- **No accounts. No ads.**
- Conversation state is saved in `.btm_sessions` on the app server so a session can be restored after a reload. A session link contains the ID used to restore that conversation; keep it private.
- Messages are sent to OpenAI to generate replies. Conversation context is used within the session.
- **New conversation** clears that session's saved chat, prayer burden, and share-card state. The current app has no automatic retention limit.
- Daily-message sharing links contain only the message ID, never the conversation session ID.
- Optional email subscriptions are stored separately in a private PostgreSQL schema. Email addresses and subscription details are not sent to OpenAI.

If we ever introduce optional features that remember or follow your journey (like reminders or continuity), they will be **clearly labeled and opt-in** — never assumed.

## Daily Encouragement preview

The draft adds a seven-day collection adapted from Daily Compass with one additional reflection on rest. Each entry has an explicit Scripture reference, KJV excerpt, encouragement, passage context, connection across Scripture, reflection question, and prayer.

- Open `?v=daily` or `?v=daily&message=compass-w01-god-sends`.
- ISO-date links such as `?v=daily&message=2026-10-14` are accepted too.
- Home, Angel Chat, and How It Works have a Daily Encouragement button.
- Follow-up buttons prepare an editable question in Angel Chat. Nothing is submitted to OpenAI until the user sends a question.
- The exact teaching is added to the model's context, including the passage's original setting. Returning to the teaching preserves its message ID.
- Dates cover **October 14–20, 2026** in **America/Denver**, as a finite preview schedule. Before or after this period, the page labels the collection as a preview or archive rather than claiming a new daily message.
- All entries are drafts (`approved_for_delivery=False`). Signup and scheduled delivery are disabled by default until the database, sender details, and rollout are configured. The email preview shows content only. SMS is not implemented.

### Email signup and Hostinger delivery

The draft now includes consent-based signup, confirmation emails, timezone/time preferences, unsubscribe, signed links, a private PostgreSQL subscriber store, Hostinger's mailbox API, and an external GitHub Actions delivery worker. It sends only approved content on explicit dates, deduplicates daily messages, and reserves a rolling 24-hour budget across confirmation and daily-send attempts. See [EMAIL_SETUP.md](EMAIL_SETUP.md) for deployment settings and remaining connection steps, and [EMAIL_PRIVACY_NOTICE.md](EMAIL_PRIVACY_NOTICE.md) for a draft privacy-policy addition.

Test the draft with `python -m unittest discover -s tests -v` after installing `requirements.txt`. Set `EMAIL_TEST_DATABASE_URL` to an isolated PostgreSQL test database to include database integration tests. Hostinger and OpenAI calls are stubbed; no external messages or AI requests are made.

## Files
- `app.py` — main Streamlit app
- `daily_encouragement.py` — reviewed-content format and seven draft teachings
- `email_subscription.py` — subscriptions, signed links, and durable delivery records
- `email_ui.py` — signup, confirmation, preferences, and unsubscribe screens
- `hostinger_email.py` — sending transport and read-only mailbox verification
- `email_worker.py` — scheduled worker outside Streamlit
- `manifest.json` — PWA manifest (HF-safe paths)
- `sw.js` — service worker
- `icon-192.png`, `icon-512.png` — PWA icons

## Run locally (optional)
```bash
streamlit run app.py --server.port 7860 --server.address 0.0.0.0
