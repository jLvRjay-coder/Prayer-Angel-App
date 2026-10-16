# Daily encouragement email setup

The app now has opt-in signup, email confirmation, preferences, and unsubscribe. The separate worker uses Hostinger Mail to deliver scheduled, approved teachings. All delivery features remain off by default. The existing Hugging Face mail token is only the sending credential; durable subscriber storage and the external worker's credentials still need configuration.

## Storage

This pilot uses a private PostgreSQL database hosted by Supabase. The app and worker use the same database. Normal Hugging Face container files are ephemeral and must not hold the subscriber list. Do not use a public repository, CSV, or chat-session files for contacts.

The dedicated project is already created in the **Beyond the Message.** Free organization:

| Project setting | Verified value |
|---|---|
| Name | `angel-daily-encouragement` |
| Reference | `srjstdtnabzkmnuilceb` |
| Region | East US / `us-east-1` (selected through Americas) |
| Database | Standard PostgreSQL 17 |
| Dashboard | [Open project](https://supabase.com/dashboard/project/srjstdtnabzkmnuilceb) |

Migration `20261014042040_create_private_daily_email_storage` created the three tables. Migration `20261014043827_backend_email_https_rpc` added a narrow, backend-only HTTPS RPC. Migration `20261014054746_expose_protected_email_api` configures exposure of its `public` schema. All three migrations are recorded in `supabase/migrations` with the same versions as the hosted database.

Hugging Face [documents that Spaces block outgoing ports other than 80, 443, and 8080](https://huggingface.co/docs/hub/spaces-overview#networking). Standard PostgreSQL connections use 5432/6543, so the selected deployment uses Supabase over HTTPS on 443 instead of a PostgreSQL URI. The Python server sends a secret API key in the `apikey` header. It never sends that key to the browser or OpenAI.

To connect the app:

1. Keep **Enable Data API** on in [Data API settings](https://supabase.com/dashboard/project/srjstdtnabzkmnuilceb/integrations/data_api/overview). The migration already exposes `public` for the protected RPC. Keep the subscriber schema out of exposed schemas and leave automatic table exposure off.
2. Open [API Keys](https://supabase.com/dashboard/project/srjstdtnabzkmnuilceb/settings/api-keys). Use a **secret** key beginning `sb_secret_`; a publishable key is not accepted by the app.
3. In Hugging Face, add the Variable `EMAIL_SUPABASE_URL=https://srjstdtnabzkmnuilceb.supabase.co` and Secret `EMAIL_SUPABASE_SECRET_KEY` containing that secret key. Copy the key directly between settings screens, keeping it out of chat, code, and screenshots.
4. Configure the shared signing key and remaining settings below. The HTTPS connection does not need `EMAIL_DATABASE_URL` or the database password.

The RPC exposes only defined subscription/delivery actions, with no generic SQL endpoint. It runs as `SECURITY INVOKER`, with execute permission only for the backend `service_role`. That backend role has SELECT/INSERT/UPDATE on the three private tables and bypasses RLS; `anon`, `authenticated`, and PUBLIC have no access to the private schema, tables, or RPC. The server validates signed email links before invoking mutations, and the database checks their current nonce again under lock. All tables keep RLS enabled with no client policies. Never add `angel_email_private` to Data API exposed schemas.

Hosted SQL checks verified owner writes, RLS on each table, denied execution for anonymous and signed-in clients, backend health, no email tables in `public` or Realtime, and zero retained test records. Supabase reported no warning/error advisories. Its informational [RLS without policies notice](https://supabase.com/docs/guides/database/database-linter?lint=0008_rls_enabled_no_policy) is intentional for these private tables. Its [unused index notices](https://supabase.com/docs/guides/database/database-linter?lint=0005_unused_index) are expected in an empty database.

The hosted Data API initially had no exposed schema and could not build its cache (`PGRST002`, with the `pg_pgrst_no_exposed_schemas` placeholder in its logs). The exposure migration sets `pgrst.db_schemas=public` on `authenticator` and reloads the API configuration. The HTTPS check now reaches the function and denies the publishable/anonymous caller with HTTP 401 / `42501`, rather than returning a service error. There are no tables in `public`; subscriber records remain private.

This [database role override](https://supabase.com/docs/guides/troubleshooting/postgrest-error-pgrst002-could-not-query-the-database-for-the-schema-cache-c396e9) takes precedence over the Dashboard's Exposed schemas field. Manage future API schema exposure through a migration. To return to Dashboard management, first configure `public` there, then reset `pgrst.db_schemas` on `authenticator` and reload configuration; resetting it before configuring the Dashboard would restore the empty exposure.

Direct PostgreSQL support remains available for other hosts and isolated tests through `EMAIL_DATABASE_URL`. It requires TLS on hosted databases and uses the table-owner connection; do not use this route for Hugging Face Spaces.

## Postal address and the devotional format

Jamie confirmed that Beyond the Message and Angel Chat are entirely free. The planned messages contain Scripture, encouragement, reflection, prayer, and a link to continue the discussion in Angel Chat. Based on that described purpose, they appear to be noncommercial. The [FTC explains that CAN-SPAM does not apply to noncommercial bulk email](https://www.ftc.gov/business-guidance/blog/2015/08/candid-answers-can-spam-questions). A link to a free devotional service does not by itself establish a commercial purpose; reassess the message if paid products, services, or advertising are introduced.

[Hostinger's no-spam policy](https://www.hostinger.com/legal/universal-terms-of-service-agreement#12-no-spam-policy) also lists a sender's physical address among requirements that apply as applicable to commercial advertising or bulk communications. Its wording does not explicitly resolve this free devotional use case. Clarify that requirement with Hostinger before enabling delivery without a postal address. If an address is needed, the [FTC's commercial-email guide](https://www.ftc.gov/business-guidance/resources/can-spam-act-compliance-guide-business) accepts a registered USPS PO Box or qualifying private mailbox as well as a current street address.

Jamie has offered to use a Utah or Texas address. Choose one current, valid postal address where the sender receives mail and is comfortable disclosing it to email recipients; either state can be used. Save the complete address as `EMAIL_POSTAL_ADDRESS` in **Secrets** on both Hugging Face and GitHub Actions. The address is printed in confirmation and devotional email footers. Secret storage keeps it out of source code and public configuration; it does not hide it from recipients.

No address has been supplied or verified as saved yet. The current sender still requires it and therefore will not accept signups or send confirmation/daily emails without it. Adding the address does not enable signup or scheduled delivery: keep both enable flags off until the private test is authorized and prepared. Credential setup and the `--initialize` storage check can continue without a postal address. No address exception has been enabled in code, and there is no live delivery yet.

## Hugging Face settings

| Setting | Type | Purpose |
|---|---|---|
| `HOSTINGER_MAIL_API_TOKEN` | Secret | Already added by Jamie; restricted to contact@beyondthemessage.org. |
| `EMAIL_SUPABASE_URL` | Variable | `https://srjstdtnabzkmnuilceb.supabase.co` |
| `EMAIL_SUPABASE_SECRET_KEY` | Secret | Backend key beginning `sb_secret_`; never use a publishable key here. |
| `EMAIL_SIGNING_KEY` | Secret | At least 32 random characters; use the same value in the app and worker. |
| `EMAIL_POSTAL_ADDRESS` | Secret | Complete chosen postal address for email footers; use the same value in GitHub Actions. Visible to email recipients. |
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

- Secrets: `HOSTINGER_MAIL_API_TOKEN`, `EMAIL_SUPABASE_SECRET_KEY`, `EMAIL_SIGNING_KEY`, and `EMAIL_POSTAL_ADDRESS` (same values as Hugging Face). The worker reads the postal address from Secrets, not Variables.
- Variables: `EMAIL_SUPABASE_URL`; keep `EMAIL_DELIVERY_ENABLED=false` until ready.

The Hugging Face Secret is not automatically available to GitHub Actions. The workflow is inactive while this PR is a draft branch; scheduled workflows require the default branch.

Jamie reports that Hugging Face now has the Hostinger mail token, Supabase URL/backend key, and generated signing key. GitHub Actions also has those three secrets, `EMAIL_SUPABASE_URL`, and `EMAIL_DELIVERY_ENABLED=false`. The read-only checks below verify GitHub's service connections; the GitHub signing key must also match the Space's key exactly. The postal address is the next setting to add; private end-to-end inbox testing remains outstanding.

### Check credentials without sending

The separate `.github/workflows/email-connections.yml` runs when its diagnostic code changes on `feat/daily-encouragement-preview`. It uses the saved GitHub settings and runs local tests before checking the live services. This workflow has no scheduled sender and explicitly disables signup and delivery. Its manual trigger becomes available once the file is on the default branch; failed runs can be re-run after correcting settings.

To run the same check from an already configured backend environment:

```bash
python email_connection_check.py
```

The check validates signing-key format, calls only the Supabase `health` action over HTTPS, and verifies that the Hostinger token authorizes `contact@beyondthemessage.org` using `/me`. It does not read subscriber records, create subscriptions or delivery attempts, or send email. It works without a postal address. Output is limited to fixed labels and pass/fail, with no raw provider errors or secret values. A successful check does not establish that the two hosts have matching signing keys, that the code is deployed to Hugging Face, or that emails reach an inbox.

Verified on October 15, 2026 at 03:43 UTC in [GitHub run 38677730312](https://github.com/jLvRjay-coder/Prayer-Angel-App/actions/runs/38677730312):

- Signing-key format: passed. This does not verify entropy or matching Hugging Face values.
- Supabase backend health over HTTPS using GitHub's saved secret: passed.
- Hostinger token and authorization for `contact@beyondthemessage.org`: passed through the application's Python transport.
- No email sent; no subscriber or delivery records changed.

Jamie generated a new Agentic Mail API token for the intended mailbox, and reports saving the same value as `HOSTINGER_MAIL_API_TOKEN` in GitHub and Hugging Face. The curl comparison changed from JSON 401 to HTTP 200 after that update. Python's read-only mailbox check passed after identifying the client with `User-Agent: AngelChat-Mail/1.0`. The old credential rejection and observed Python 403 are resolved in GitHub. Hugging Face credentials and deployed code still need their own check.

The project consistently uses `HOSTINGER_MAIL_API_TOKEN`; Hostinger support's example name `HOSTINGER_MAIL_TOKEN` is not this project's setting. The actual diagnostic event is a same-repository push, and the secret is present as a bare value without whitespace or surrounding quotes. `email_http_probe.py` remains a failure-only diagnostic: Authorization is passed to curl over stdin, redirects are not followed, response bodies are discarded, and output is limited to selected headers with redaction. Twelve diagnostic tests passed in GitHub; those plus four existing mail-transport tests passed locally (16 focused tests).

Jamie has offered a postal address for the footer, but it has not yet been supplied or verified as saved. Successful API authorization does not enable subscriptions or sending. `EMAIL_DELIVERY_ENABLED` remains reported as `false`, signup remains disabled, and all daily messages are unapproved drafts.

Before the preview deployment, the public Hugging Face Space was checked at commit `806b90258b8e9e55a4a64e480efa91631a2d5ee9`, without the new daily/email modules.

### Deploy the preview to the existing Space

Jamie created a fine-grained Hugging Face token and added it to GitHub as `HF_TOKEN`. It must have write access to the existing `lvRJay18950/Prayer-Angel` Space. Do not put this token in source files or browser code.

`.github/workflows/deploy-space-preview.yml` runs when its deployment helper, workflow, or safety tests change on `feat/daily-encouragement-preview`. It first tests the application and runs the read-only GitHub backend checks. Only its final step receives `HF_TOKEN`. The manual trigger becomes available once this workflow is on the default branch.

The helper uploads an explicit list of application files in one commit, with a parent-commit check to avoid overwriting concurrent source updates. It preserves the Space's existing stories and assets, does not copy local environment/session files, and does not modify hardware, billing, stored credentials, or the daily sender's settings. It verifies that signup and delivery flags are absent (the tested application defaults are `false`) or explicitly `false`; secret-based or enabled flags block the deployment. A public `deployment.json` records only the source repository, GitHub commit, and preview mode.

An upload starts a Docker rebuild. Check the Space's running commit, `/_stcore/health`, and the Daily Encouragement page at the custom domain before considering the preview deployed. A successful upload alone does not prove startup. This deployment does not verify Hugging Face's saved email credentials or matching signing keys across hosts, and it sends no email. Signup, daily delivery, and content approval remain separate rollout steps.

The migrations already created the selected hosted storage. To verify HTTPS storage without sending, after configuring credentials and enabling the Data API:

```bash
python email_worker.py --initialize
```

To start scheduled delivery, after deployment and confirmation testing, set the GitHub repository variable `EMAIL_DELIVERY_ENABLED=true`. Run only approved content with valid publication dates. Nothing in the draft flips this setting on.

## Content and unsubscribe

### Private inbox test before launch

Jamie reports saving the business mailing address as `EMAIL_POSTAL_ADDRESS` in both hosts' Secrets. The private test workflow runs only when `email_test_request.json` changes on the preview branch, or when manually invoked after the workflow is on the default branch. Its initial request is `{"operation": "check"}`: it checks GitHub credentials/address readiness, Hugging Face secret names, storage URL, and disabled public email flags without creating subscriptions or sending. It never reads Hugging Face secret values; matching signing keys and working Space credentials must be verified through the live email links.

Before authorizing a send, save the chosen inbox as the GitHub Actions Secret `EMAIL_TEST_RECIPIENT`. Keep public signup and daily delivery disabled. This single-recipient setting is not a mailing list and does not appear in source or logs.

After Jamie explicitly authorizes the private test, prepare a fresh request with `operation: confirmation`, a unique lowercase `request_id`, and a timezone-aware ISO `requested_at`. Requests expire after 30 minutes. The runner uses the existing consent/confirmation flow only for that inbox, with a process-local signup override; it does not change either host's public flags. Test emails have a `[Private test]` subject and explain that automatic daily delivery is paused. Confirmation throttling still applies, and uncertain outcomes must be investigated rather than retried.

Jamie then opens the confirmation link and clicks Confirm. A separate freshly authorized `operation: devotional` request with `message_id: compass-w01-god-sends` sends the complete sample only to that confirmed inbox. It uses the existing delivery reservation/claim ledger, a distinct private-test message key, the actual business footer, and signed preferences/unsubscribe links. It does not approve draft content or activate scheduled delivery. Recipient checks run again immediately before the provider call.

Finish by testing preference changes and clicking Unsubscribe in the private sample. The test subscriber must be unsubscribed before a later pilot; the normal opt-out and delivery records are retained under the documented storage behavior. None of the private test runner/request files are deployed to the public Space.

`daily_encouragement.py` contains a finite seven-day preview calendar for October 14–20, 2026. All entries have `approved_for_delivery=False`. Review both wording and dates before setting an entry to `True`; extend the calendar before it runs out. The worker never repeats an old entry just because no new one is available, and it does not generate daily teaching through AI.

Signup requires an unchecked-by-default consent box. A subscriber becomes active only after opening a confirmation email and clicking Confirm. Email scanners opening links do not change state. Confirmation expires after 24 hours, and repeat requests are limited to one per address per hour. The initial cap includes active subscribers and unexpired pending confirmations.

Each outgoing message goes to one person, without CC, BCC, or attachments. It includes ministry contact details, an unsubscribe link, preferences, and a public link to that exact teaching. The Hostinger API does not expose arbitrary mail headers in its published sending schema; the current unsubscribe flow is a normal link plus an explicit Unsubscribe button, not an RFC 8058 one-click POST endpoint.

Unsubscribe and preferences remain usable when daily delivery is disabled or the Hostinger token is removed, as long as the database and signing key remain configured. An unsubscribe invalidates a pending confirmation; opting back in requires a new confirmation. Subscription details are not sent to OpenAI or stored in chat-session files.

## Sending budget and uncertain outcomes

Your Business Starter mailbox limit is 1,000 outgoing messages over a rolling 24 hours. The application uses a conservative 750-attempt budget, including confirmation sends, leaving headroom for regular email. Ordinary messages sent outside this app are not visible to the budget ledger, so this is not a measurement of the mailbox's total usage. Hostinger still enforces its actual limit.

The sender follows `Retry-After` on HTTP 429 by deferring that delivery until a later eligible run; it does not invent a separate API quota. Daily deliveries are deduplicated by subscriber and message ID in PostgreSQL. A durable `sending` record is written before calling the provider. Timeouts and uncertain server responses become `unknown`; interrupted sends remain `sending`. Neither is automatically replayed. Investigate those records against Hostinger's Sent folder/delivery logs before any operator retry. A missing email is preferable to silently duplicating an uncertain send.

Each HTTPS mutation commits as one database transaction. Capacity/reservation operations use an advisory lock; claiming a send checks consent under a row lock and records `sending` before the provider request. The HTTP client never automatically retries a mutation. If saving the final outcome fails after provider acceptance, the durable `sending` record still prevents replay. Unsubscribe prevents future claims; an email request already in flight cannot be recalled.

The app throttles confirmations and limits the pilot size, but this is not a full public abuse-prevention system. For a broad public launch, add stronger form verification and monitoring as usage grows.

## Privacy and release

`EMAIL_PRIVACY_NOTICE.md` is a draft addition to the public privacy policy, covering email addresses, delivery preferences, consent, delivery records, Hostinger, and Supabase. Choose and document the retention period and deletion process, and publish the completed wording before opening signup. Unsubscribed records currently remain stored to honor opt-out and preserve consent; there is no automatic purge in this draft.

Before the Android subscription feature goes live, update relevant Google Play Data safety declarations and the privacy policy, and inspect the Android packaging project for any required build/link changes. The repositories inspected so far contain the web application, not the Android package project.

## Validation

Install `requirements.txt`, then run:

```bash
python -m unittest discover -s tests -v
```

Set `EMAIL_TEST_DATABASE_URL` to an **isolated test PostgreSQL database** to include database integration tests. Those tests truncate only the `angel_email_` test tables; never point this variable at production. Initial feature validation used an isolated PGlite PostgreSQL engine through its wire-protocol server. The HTTPS adapter was tested against the real RPC SQL through a local session stub, including normal subscription flows, access denial, and a lost outcome update after provider acceptance. All Hostinger and OpenAI calls in those tests were stubbed. Hosted SQL write/access checks passed separately. The new connection checker has seven tests, including no-send guarantees and safe failure classification; all seven passed in GitHub, and those plus four existing mail-transport tests passed locally. GitHub's live Supabase HTTPS authentication has now passed. Hugging Face connectivity/key matching, direct Hostinger authorization, and actual inbox delivery remain deployment checks.
