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

If we ever introduce optional features that remember or follow your journey (like reminders or continuity), they will be **clearly labeled and opt-in** — never assumed.

## Daily Encouragement preview

The draft adds a seven-day collection adapted from Daily Compass with one additional reflection on rest. Each entry has an explicit Scripture reference, KJV excerpt, encouragement, passage context, connection across Scripture, reflection question, and prayer.

- Open `?v=daily` or `?v=daily&message=compass-w01-god-sends`.
- ISO-date links such as `?v=daily&message=2026-10-14` are accepted too.
- Home, Angel Chat, and How It Works have a Daily Encouragement button.
- Follow-up buttons prepare an editable question in Angel Chat. Nothing is submitted to OpenAI until the user sends a question.
- The exact teaching is added to the model's context, including the passage's original setting. Returning to the teaching preserves its message ID.
- Dates cover **October 14–20, 2026** in **America/Denver**, as a finite preview schedule. Before or after this period, the page labels the collection as a preview or archive rather than claiming a new daily message.
- All entries are drafts (`approved_for_delivery=False`). **No addresses are collected and no email or SMS is sent.** The email preview shows content only.

### Next: connect email signup and delivery

Configure a sending service and an authenticated sending domain, then add a subscriber store separate from conversations. Implement explicit opt-in, address confirmation, preferences, unsubscribe/suppression handling, and a scheduler outside the Streamlit process. The sender must require approved content, a defined publication calendar, and deduplication per subscriber/message. Complete sender/footer information and privacy disclosures before sending. SMS is a later phase with its own consent and sender-registration flow.

Test the draft with `python -m unittest discover -s tests -v` after installing `requirements.txt`. The integration tests replace OpenAI with a local stub; no external messages or AI requests are made.

## Files
- `app.py` — main Streamlit app
- `manifest.json` — PWA manifest (HF-safe paths)
- `sw.js` — service worker
- `icon-192.png`, `icon-512.png` — PWA icons

## Run locally (optional)
```bash
streamlit run app.py --server.port 7860 --server.address 0.0.0.0
