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

The draft adds a seven-day collection adapted from Daily Compass with one additional reflection on rest. Each entry includes its complete selected KJV passage, encouragement, passage context, connection across Scripture, reflection question, and prayer. Scripture is visible directly on the page and in the email, without opening another site.

All seven entries use the expanded devotional format established by “God Sends the Reluctant”: a complete KJV reading, a brief opening thought, approximately 300–450 words of original reflection, a personal question, and a prayer. Each develops its own theme through the passage's setting and relevant connections across Scripture. The email preview and eventual sender use the same complete content, and Angel Chat receives the reading and expanded devotional as context. The collection remains a draft for review before email delivery is enabled.

The app and HTML email now share the existing Beyond the Message crest, navy/gold/parchment styling, a highlighted Scripture excerpt, selective sentence emphasis, and distinct reflection/prayer sections. The complete reading and devotional remain text, including when the email logo is blocked. Confirmation emails share the same identity. See `PILOT_LAUNCH.md` for the proposed October 19–25 pilot and remaining activation steps. Public signup and scheduled sending are still off.

The October 16 live website test passed signup, confirmation sending, confirmation, saved delivery preferences, and unsubscribe. Read-only checks verified the saved preference and final opt-out. The test ended with one unsubscribed record and zero active or pending subscribers; both public enable flags are false again, and the live signup screen is closed. See `docs/live-email-test-2026-10-16.md`. The Android privacy review remains open: Google Play links a separate older policy and currently declares no data collection. `ANDROID_PRIVACY_REVIEW.md` records the required review and the unpublished policy draft; no Play Console declaration has been changed.

The email and its preview end with two named, clickable links: **Open Angel Chat in your browser**, which opens that message's context directly in chat, and **Get Angel Chat for Android**, which opens the [verified Google Play listing](https://play.google.com/store/apps/details?id=org.beyondthemessage.angel). The browser option covers iPhone, iPad, and computers; no Apple App Store listing is implied. Plain-text emails retain descriptive labels and full URLs. Neither public link contains conversation identifiers or subscription tokens.

Angel Chat's home page is prepared to show **Sign up for Daily Encouragement** only when the email configuration is ready and signup is explicitly enabled. That button opens the existing email signup screen. When email delivery launches, add the same invitation to the Beyond the Message website home page, linking to `https://angel.beyondthemessage.org/?v=email`; the WordPress home page has not been modified by this preview update.

- Open `?v=daily` or `?v=daily&message=compass-w01-god-sends`.
- ISO-date links such as `?v=daily&message=2026-10-19` are accepted too.
- Home, Angel Chat, and How It Works have a Daily Encouragement button.
- Follow-up buttons prepare an editable question in Angel Chat. Nothing is submitted to OpenAI until the user sends a question.
- The exact teaching is added to the model's context, including the passage's original setting. Returning to the teaching preserves its message ID.
- Dates cover **October 19–25, 2026** in **America/Denver**, as a finite preview schedule. Before or after this period, the page labels the collection as a preview or archive rather than claiming a new daily message.
- All entries are drafts (`approved_for_delivery=False`). Signup and scheduled delivery are disabled by default until the database, sender details, and rollout are configured. The email preview shows content only. SMS is not implemented.

### Phase two: recorded devotionals

After the written devotional and subscription flow are settled, Jamie plans to record each devotional for YouTube. Attach the recording URL to that devotional's stable message ID and show an optional **Listen instead** link in both the daily email and the app. Each link should open the specific day's recording. Keep the complete Scripture reading and written devotional available, and show the listening link only when that recording is ready. Recordings and YouTube links are planned; this preview does not publish videos or include placeholder listening links.

### Email signup and Hostinger delivery

The draft now includes consent-based signup, confirmation emails, timezone/time preferences, unsubscribe, signed links, a private Supabase PostgreSQL subscriber store accessed by a backend-only HTTPS RPC, Hostinger's mailbox API, and an external GitHub Actions delivery worker. It sends only approved content on explicit dates, deduplicates daily messages, and reserves a rolling 24-hour budget across confirmation and daily-send attempts. The HTTPS route fits Hugging Face's network restrictions; its secret key stays on the Python server. See [EMAIL_SETUP.md](EMAIL_SETUP.md) for deployment settings and remaining checks. The approved email privacy addition is now [published on the website](https://beyondthemessage.org/privacy-policy/); [EMAIL_PRIVACY_NOTICE.md](EMAIL_PRIVACY_NOTICE.md) records the approval and verified publication. Public signup and automatic delivery remain off.

Test the draft with `python -m unittest discover -s tests -v` after installing `requirements.txt`. Set `EMAIL_TEST_DATABASE_URL` to an isolated PostgreSQL test database to include database integration tests. Hostinger and OpenAI calls are stubbed; no external messages or AI requests are made.

## Files
- `app.py` — main Streamlit app
- `daily_encouragement.py` — reviewed-content format and seven draft teachings
- `email_subscription.py` — subscriptions, signed links, and durable delivery records
- `supabase_email_store.py` — backend HTTPS storage adapter
- `supabase/migrations` — installed private tables and restricted backend RPC
- `email_ui.py` — signup, confirmation, preferences, and unsubscribe screens
- `hostinger_email.py` — sending transport and read-only mailbox verification
- `email_worker.py` — scheduled worker outside Streamlit
- `manifest.json` — PWA manifest (HF-safe paths)
- `sw.js` — service worker
- `icon-192.png`, `icon-512.png` — PWA icons

## Run locally (optional)
```bash
streamlit run app.py --server.port 7860 --server.address 0.0.0.0
