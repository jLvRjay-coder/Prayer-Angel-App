# Daily encouragement email setup

The app now has opt-in signup, email confirmation, preferences, and unsubscribe. The separate worker uses Hostinger Mail to deliver scheduled, approved teachings. All delivery features remain off by default. The existing Hugging Face mail token is only the sending credential; durable subscriber storage and the external worker's credentials still need configuration.

## Storage

Use a private hosted PostgreSQL database, such as Supabase or Neon. The app and worker use the same database. Normal Hugging Face container files are ephemeral and must not hold the subscriber list. Do not use a public repository, CSV, or chat-session files for contacts.

For this pilot, use a dedicated Supabase project in the **Beyond the Message.** Free organization:

1. Open the organization dashboard and create a project named `angel-daily-encouragement`.
2. Choose **West US / us-west-1** and standard PostgreSQL. Save the generated database password in your password manager; do not post it in chat.
3. After the project is ready, open **Connect**, choose **Session pooler**, and copy its PostgreSQL URI. Insert the database password locally, URL-encoding special characters if needed, then save the complete URI directly as the `EMAIL_DATABASE_URL` Secret.

The code requires TLS for a remote database. Use the server-side `postgres` table-owner connection from the Connect panel, not an anon/publishable API key. The app creates tables in the private `angel_email_private` schema, outside Supabase's default public Data API schema. It also enables row-level security with no client policies and revokes public and Supabase client-role access. Only the server-side table owner manages contacts. Do not expose this schema through the Data API. This feature does not use the Data API, so you may disable it for the dedicated project.

## Hugging Face settings

| Setting | Type | Purpose |
|---|---|---|
| `HOSTINGER_MAIL_API_TOKEN` | Secret | Already added by Jamie; restricted to contact@beyondthemessage.org. |
| `EMAIL_DATABASE_URL` | Secret | Private PostgreSQL connection URI. |
| `EMAIL_SIGNING_KEY` | Secret | At least 32 random characters; use the same value in the app and worker. |
| `EMAIL_POSTAL_ADDRESS` | Variable or Secret | Valid ministry/business mailing address included in every email. |
| `EMAIL_SIGNUPS_ENABLED` | Variable | Leave `false` until database connectivity, confirmation, policy, and public links are tested. |
| `EMAIL_BUDGET_24H` | Variable | Default `750`; accepts 1–900. Counts this feature's confirmation and daily-send attempts together over a rolling 24 hours. |
| `EMAIL_MAX_SUBSCRIBERS` | Variable | Default `50` for the initial pilot. |

Create a signing key locally, for example with Python:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Save the value directly as a Secret. Never put the key, mail token, or database password in code, chat, screenshots, or public logs.

Deploy all the new Python modules and updated requirements together. The existing Dockerfile copies them automatically. A GitHub change does not itself prove that the live Hugging Face Space has the same version; verify the deployed commit before testing public links.

## External delivery worker

The draft includes `.github/workflows/daily-email.yml`, scheduled at minutes 17 and 47 of each hour. It runs independently of Streamlit and can send while the Space is asleep. Preferences are interpreted in the subscriber's selected timezone, including daylight saving changes. Delivery occurs in the next successful scheduled run after the selected time; GitHub can delay or drop scheduled runs, and public repository schedules can be disabled after inactivity. Monitor the workflow and delivery outcomes rather than promising an exact minute.

Add these to **Prayer-Angel-App → Settings → Secrets and variables → Actions**:

- Secrets: `HOSTINGER_MAIL_API_TOKEN`, `EMAIL_DATABASE_URL`, and `EMAIL_SIGNING_KEY` (same values as Hugging Face).
- Variables: `EMAIL_POSTAL_ADDRESS`; keep `EMAIL_DELIVERY_ENABLED=false` until ready.

The Hugging Face Secret is not automatically available to GitHub Actions. The workflow is inactive while this PR is a draft branch; scheduled workflows require the default branch.

To initialize tables without sending:

```bash
python email_worker.py --initialize
```

To start scheduled delivery, after deployment and confirmation testing, set the GitHub repository variable `EMAIL_DELIVERY_ENABLED=true`. Run only approved content with valid publication dates. Nothing in the draft flips this setting on.

## Content and unsubscribe

`daily_encouragement.py` contains a finite seven-day preview calendar for October 14–20, 2026. All entries have `approved_for_delivery=False`. Review both wording and dates before setting an entry to `True`; extend the calendar before it runs out. The worker never repeats an old entry just because no new one is available, and it does not generate daily teaching through AI.

Signup requires an unchecked-by-default consent box. A subscriber becomes active only after opening a confirmation email and clicking Confirm. Email scanners opening links do not change state. Confirmation expires after 24 hours, and repeat requests are limited to one per address per hour. The initial cap includes active subscribers and unexpired pending confirmations.

Each outgoing message goes to one person, without CC, BCC, or attachments. It includes ministry contact details, an unsubscribe link, preferences, and a public link to that exact teaching. The Hostinger API does not expose arbitrary mail headers in its published sending schema; the current unsubscribe flow is a normal link plus an explicit Unsubscribe button, not an RFC 8058 one-click POST endpoint.

Unsubscribe and preferences remain usable when daily delivery is disabled or the Hostinger token is removed, as long as the database and signing key remain configured. An unsubscribe invalidates a pending confirmation; opting back in requires a new confirmation. Subscription details are not sent to OpenAI or stored in chat-session files.

## Sending budget and uncertain outcomes

Your Business Starter mailbox limit is 1,000 outgoing messages over a rolling 24 hours. The application uses a conservative 750-attempt budget, including confirmation sends, leaving headroom for regular email. Ordinary messages sent outside this app are not visible to the budget ledger, so this is not a measurement of the mailbox's total usage. Hostinger still enforces its actual limit.

The sender follows `Retry-After` on HTTP 429 by deferring that delivery until a later eligible run; it does not invent a separate API quota. Daily deliveries are deduplicated by subscriber and message ID in PostgreSQL. A durable `sending` record is written before calling the provider. Timeouts and uncertain server responses become `unknown`; interrupted sends remain `sending`. Neither is automatically replayed. Investigate those records against Hostinger's Sent folder/delivery logs before any operator retry. A missing email is preferable to silently duplicating an uncertain send.

The app throttles confirmations and limits the pilot size, but this is not a full public abuse-prevention system. For a broad public launch, add stronger form verification and monitoring as usage grows.

## Privacy and release

`EMAIL_PRIVACY_NOTICE.md` is a draft addition to the public privacy policy, covering email addresses, delivery preferences, consent, delivery records, Hostinger, and the database host. Choose and document the retention period, identify the actual database provider, and publish the completed wording before opening signup. Unsubscribed records currently remain stored to honor opt-out and preserve consent; there is no automatic purge in this draft.

Before the Android subscription feature goes live, update relevant Google Play Data safety declarations and the privacy policy, and inspect the Android packaging project for any required build/link changes. The repositories inspected so far contain the web application, not the Android package project.

## Validation

Install `requirements.txt`, then run:

```bash
python -m unittest discover -s tests -v
```

Set `EMAIL_TEST_DATABASE_URL` to an **isolated test PostgreSQL database** to include database integration tests. Those tests truncate only the `angel_email_` test tables; never point this variable at production. Local validation used an isolated PGlite PostgreSQL engine through its wire-protocol server and stubbed all Hostinger sends. Hosted database connection, real API-token authentication from the Space, and actual inbox delivery remain deployment checks.
