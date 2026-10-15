"""Durable opt-in subscriptions and delivery records, separate from chat state.

Hosted storage uses HTTPS or PostgreSQL with TLS. Every outgoing API attempt reserves
rolling-24-hour capacity before sending. A durable 'sending' state prevents a
crash after provider acceptance from silently producing a duplicate.
"""

import base64
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta, timezone
import hashlib
import hmac
import html
import json
import os
import secrets
from urllib.parse import urlencode, urlparse
from uuid import uuid4
from zoneinfo import ZoneInfo

from email_validator import EmailNotValidError, validate_email
import psycopg
from psycopg.rows import dict_row

from daily_encouragement import email_preview
from hostinger_email import HostingerMailer, SendResult


UTC = timezone.utc
CONSENT_VERSION = "daily-email-2026-10-14"
CONSENT_TEXT = "I agree to receive one daily Scripture-rooted encouragement email from Angel Chat / Beyond the Message. I can unsubscribe at any time."
LOCK_ID = 318100014


class SubscriptionError(ValueError):
    """Safe user-facing error; never include tokens, email addresses, or DSNs."""


@dataclass(frozen=True)
class EmailSettings:
    database_url: str = field(default="", repr=False)
    supabase_url: str = ""
    supabase_secret_key: str = field(default="", repr=False)
    signing_key: str = field(default="", repr=False)
    api_token: str = field(default="", repr=False)
    signups_enabled: bool = False
    delivery_enabled: bool = False
    postal_address: str = ""
    budget_24h: int = 750
    max_subscribers: int = 50
    base_url: str = "https://angel.beyondthemessage.org/"
    mailbox_address: str = "contact@beyondthemessage.org"

    @classmethod
    def from_env(cls, values=None):
        values = os.environ if values is None else values
        return cls(
            database_url=values.get("EMAIL_DATABASE_URL", ""),
            supabase_url=values.get("EMAIL_SUPABASE_URL", ""),
            supabase_secret_key=values.get("EMAIL_SUPABASE_SECRET_KEY", ""),
            signing_key=values.get("EMAIL_SIGNING_KEY", ""),
            api_token=values.get("HOSTINGER_MAIL_API_TOKEN", ""),
            signups_enabled=str(values.get("EMAIL_SIGNUPS_ENABLED", "false")).lower() == "true",
            delivery_enabled=str(values.get("EMAIL_DELIVERY_ENABLED", "false")).lower() == "true",
            postal_address=values.get("EMAIL_POSTAL_ADDRESS", ""),
            budget_24h=int(values.get("EMAIL_BUDGET_24H", "750")),
            max_subscribers=int(values.get("EMAIL_MAX_SUBSCRIBERS", "50")),
        )

    @property
    def https_database_ready(self):
        try:
            url = urlparse(self.supabase_url)
            port = url.port
        except ValueError:
            return False
        return bool(
            url.scheme == "https" and url.hostname
            and url.hostname.endswith(".supabase.co")
            and not url.username and not url.password and not port
            and url.path in {"", "/"} and not url.query and not url.fragment
            and self.supabase_secret_key.startswith("sb_secret_")
        )

    @property
    def storage_ready(self):
        return bool(
            (self.https_database_ready or self.database_url.startswith(("postgresql://", "postgres://")))
            and len(self.signing_key) >= 32
        )

    @property
    def ready(self):
        return bool(
            self.storage_ready and self.api_token
            and self.postal_address.strip()
            and 1 <= self.budget_24h <= 900 and self.max_subscribers >= 1
        )


SCHEMA = """
CREATE SCHEMA IF NOT EXISTS angel_email_private;
REVOKE ALL ON SCHEMA angel_email_private FROM PUBLIC;
CREATE TABLE IF NOT EXISTS angel_email_private.angel_email_subscribers (
    id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending','active','unsubscribed')),
    timezone TEXT NOT NULL, delivery_time TIME NOT NULL,
    manage_nonce TEXT NOT NULL, confirmation_nonce TEXT,
    confirmation_expires TIMESTAMPTZ, pending_timezone TEXT, pending_time TIME,
    requested_at TIMESTAMPTZ NOT NULL, consent_at TIMESTAMPTZ,
    confirmed_at TIMESTAMPTZ, consent_version TEXT,
    unsubscribed_at TIMESTAMPTZ, updated_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS angel_email_private.angel_email_deliveries (
    id TEXT PRIMARY KEY,
    subscriber_id TEXT NOT NULL REFERENCES angel_email_private.angel_email_subscribers(id),
    message_key TEXT NOT NULL, kind TEXT NOT NULL CHECK(kind IN ('confirmation','daily')),
    nonce TEXT, status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL, sent_at TIMESTAMPTZ, retry_at TIMESTAMPTZ,
    UNIQUE(subscriber_id, message_key)
);
CREATE TABLE IF NOT EXISTS angel_email_private.angel_email_attempts (
    id TEXT PRIMARY KEY, delivery_id TEXT NOT NULL REFERENCES angel_email_private.angel_email_deliveries(id),
    reserved_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS angel_email_attempts_time_idx ON angel_email_private.angel_email_attempts(reserved_at);
CREATE INDEX IF NOT EXISTS angel_email_attempts_delivery_idx ON angel_email_private.angel_email_attempts(delivery_id);
CREATE INDEX IF NOT EXISTS angel_email_active_idx ON angel_email_private.angel_email_subscribers(status);

-- No browser/client policies exist. RLS denies ordinary client roles even
-- after accidental grants; the HTTPS migration separately authorizes backend service_role.
ALTER TABLE angel_email_private.angel_email_subscribers ENABLE ROW LEVEL SECURITY;
ALTER TABLE angel_email_private.angel_email_deliveries ENABLE ROW LEVEL SECURITY;
ALTER TABLE angel_email_private.angel_email_attempts ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON ALL TABLES IN SCHEMA angel_email_private FROM PUBLIC;
ALTER DEFAULT PRIVILEGES IN SCHEMA angel_email_private REVOKE ALL ON TABLES FROM PUBLIC;

-- Supabase roles are optional so ordinary PostgreSQL works too.
DO $private_access$
DECLARE client_role TEXT;
BEGIN
    FOR client_role IN
        SELECT rolname FROM pg_catalog.pg_roles
        WHERE rolname IN ('anon', 'authenticated')
    LOOP
        EXECUTE format('REVOKE ALL ON SCHEMA angel_email_private FROM %I', client_role);
        EXECUTE format('REVOKE ALL ON ALL TABLES IN SCHEMA angel_email_private FROM %I', client_role);
        EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA angel_email_private REVOKE ALL ON TABLES FROM %I', client_role);
    END LOOP;
END
$private_access$;
"""


def utc_now():
    return datetime.now(UTC)


def normalize_email(value):
    try:
        return validate_email(value.strip(), check_deliverability=False, allow_smtputf8=False).normalized.casefold()
    except (EmailNotValidError, AttributeError):
        raise SubscriptionError("Please enter a valid email address.") from None


def validate_preferences(tz, clock):
    try:
        ZoneInfo(tz)
        parsed = time.fromisoformat(str(clock))
        if parsed.tzinfo is not None:
            raise ValueError
        return parsed.replace(second=0, microsecond=0)
    except (ValueError, TypeError, KeyError):
        raise SubscriptionError("Please choose a valid timezone and delivery time.") from None


def _b64(data):
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def make_token(settings, subscriber, purpose, now=None):
    now = now or utc_now()
    nonce = subscriber["confirmation_nonce"] if purpose == "confirm" else subscriber["manage_nonce"]
    expires = subscriber["confirmation_expires"] if purpose == "confirm" else now + timedelta(days=365)
    payload = _b64(json.dumps({
        "id": subscriber["id"], "nonce": nonce, "purpose": purpose,
        "exp": int(expires.timestamp()),
    }, separators=(",", ":")).encode())
    signature = _b64(hmac.new(settings.signing_key.encode(), payload.encode(), hashlib.sha256).digest())
    return payload + "." + signature


def read_token(settings, token, purpose, now=None):
    now = now or utc_now()
    try:
        if not isinstance(token, str) or len(token) > 1024 or len(settings.signing_key) < 32:
            raise ValueError
        payload, signature = token.split(".")
        expected = _b64(hmac.new(settings.signing_key.encode(), payload.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            raise ValueError
        data = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        if data["purpose"] != purpose or data["exp"] <= now.timestamp() or not data["nonce"]:
            raise ValueError
        return data
    except (ValueError, KeyError, TypeError, UnicodeError):
        raise SubscriptionError("This link is invalid or expired. Please use the latest email or request a new confirmation.") from None


def action_url(settings, subscriber, purpose, now=None):
    return settings.base_url + "?" + urlencode({
        "v": "email", "action": purpose,
        "token": make_token(settings, subscriber, purpose, now),
    })


def render_email(settings, subscriber, message=None, now=None):
    unsubscribe = action_url(settings, subscriber, "unsubscribe", now)
    manage = action_url(settings, subscriber, "manage", now)
    footer = (
        f"Angel Chat / Beyond the Message\n{settings.postal_address}\n"
        f"Questions or delivery problems: {settings.mailbox_address}\n"
        f"Unsubscribe: {unsubscribe}\nEmail preferences: {manage}"
    )
    if message is None:
        confirm = action_url(settings, subscriber, "confirm", now)
        subject = "Confirm your daily encouragement emails — Angel Chat"
        main = (
            "You requested one daily Scripture-rooted encouragement email from Angel Chat.\n\n"
            "Confirm your email address using this link, then select Confirm on the page:\n"
            f"{confirm}\n\nThis confirmation expires in 24 hours. "
            "If you did not request this, you can ignore this email. No daily emails will begin without confirmation."
        )
    else:
        subject = f"Angel Chat — {message['title']}"
        main = email_preview(message).rstrip()
    text = main + "\n\n---\n" + footer
    # Escape the complete body before making HTTPS URLs clickable.
    parts = []
    for line in text.splitlines():
        if line.startswith("https://"):
            escaped = html.escape(line, quote=True)
            label = "Confirm your email" if message is None else "Dive deeper in Angel Chat"
            parts.append(f'<p><a href="{escaped}">{label}</a></p>')
        elif line.startswith(("Unsubscribe: https://", "Email preferences: https://")):
            label, url = line.split(": ", 1)
            parts.append(f'<p><a href="{html.escape(url, quote=True)}">{html.escape(label)}</a></p>')
        elif line:
            parts.append(f"<p>{html.escape(line)}</p>")
    body = '<div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;line-height:1.6;color:#1a1b26">' + "".join(parts) + '</div>'
    return subject, text, body


class SubscriptionStore:
    def __init__(self, settings, connect=None):
        self.settings = settings
        self._connect_override = connect

    @contextmanager
    def connection(self):
        if self._connect_override:
            connection = self._connect_override()
        else:
            if not self.settings.storage_ready:
                raise SubscriptionError("Email signup is not available yet.")
            # URL credentials stay server-side. Require TLS for a hosted DB.
            local = urlparse(self.settings.database_url).hostname in {"localhost", "127.0.0.1", "::1"}
            connection = psycopg.connect(
                self.settings.database_url, row_factory=dict_row, connect_timeout=10,
                sslmode="disable" if local else "require", prepare_threshold=None,
            )
        with connection:
            # Keep subscriber data outside Supabase's default public Data API
            # schema. These settings are transaction-local and pooler-safe.
            connection.execute("SET LOCAL search_path TO angel_email_private, pg_catalog")
            connection.execute("SET LOCAL statement_timeout = '60s'")
            connection.execute("SET LOCAL lock_timeout = '45s'")
            yield connection

    def initialize(self):
        with self.connection() as connection:
            connection.execute("SELECT pg_advisory_xact_lock(%s)", (LOCK_ID,))
            connection.execute(SCHEMA)

    def request(self, email, tz, clock, consent, now=None):
        now = now or utc_now()
        if not consent:
            raise SubscriptionError("Please agree to daily emails before signing up.")
        email = normalize_email(email)
        clock = validate_preferences(tz, clock)
        with self.connection() as connection:
            connection.execute("SELECT pg_advisory_xact_lock(%s)", (LOCK_ID,))
            row = connection.execute("SELECT * FROM angel_email_subscribers WHERE email=%s FOR UPDATE", (email,)).fetchone()
            if row and row["requested_at"] > now - timedelta(hours=1):
                return None
            count = connection.execute("SELECT count(*) AS n FROM angel_email_subscribers WHERE status='active' OR (status='pending' AND confirmation_expires > %s)", (now,)).fetchone()["n"]
            counted = row and (row["status"] == "active" or (row["status"] == "pending" and row["confirmation_expires"] > now))
            if not counted and count >= self.settings.max_subscribers:
                raise SubscriptionError("The email pilot is currently full. Please try again later.")
            nonce = secrets.token_urlsafe(24)
            expires = now + timedelta(hours=24)
            if row:
                connection.execute(
                    """UPDATE angel_email_subscribers SET confirmation_nonce=%s, confirmation_expires=%s,
                    pending_timezone=%s, pending_time=%s, requested_at=%s, updated_at=%s,
                    status=%s, manage_nonce=%s WHERE id=%s""",
                    (nonce, expires, tz, clock, now, now,
                     "pending" if row["status"] == "unsubscribed" else row["status"],
                     secrets.token_urlsafe(24) if row["status"] == "unsubscribed" else row["manage_nonce"], row["id"]),
                )
                subscriber_id = row["id"]
            else:
                subscriber_id = str(uuid4())
                connection.execute(
                    """INSERT INTO angel_email_subscribers
                    (id,email,status,timezone,delivery_time,manage_nonce,confirmation_nonce,confirmation_expires,
                     pending_timezone,pending_time,requested_at,updated_at)
                    VALUES (%s,%s,'pending',%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (subscriber_id, email, tz, clock, secrets.token_urlsafe(24), nonce, expires, tz, clock, now, now),
                )
            return connection.execute("SELECT * FROM angel_email_subscribers WHERE id=%s", (subscriber_id,)).fetchone()

    def token_subscriber(self, token, purpose, now=None):
        claims = read_token(self.settings, token, purpose, now)
        with self.connection() as connection:
            row = connection.execute("SELECT * FROM angel_email_subscribers WHERE id=%s", (claims["id"],)).fetchone()
        field = "confirmation_nonce" if purpose == "confirm" else "manage_nonce"
        if not row or not hmac.compare_digest(row[field] or "", claims["nonce"]):
            raise SubscriptionError("This link is no longer valid. Please use the latest email.")
        return row

    def apply_action(self, token, purpose, tz=None, clock=None, now=None):
        now = now or utc_now()
        claims = read_token(self.settings, token, purpose, now)
        with self.connection() as connection:
            row = connection.execute("SELECT * FROM angel_email_subscribers WHERE id=%s FOR UPDATE", (claims["id"],)).fetchone()
            field = "confirmation_nonce" if purpose == "confirm" else "manage_nonce"
            if not row or not hmac.compare_digest(row[field] or "", claims["nonce"]):
                raise SubscriptionError("This link is no longer valid. Please use the latest email.")
            if purpose == "confirm":
                if row["confirmation_expires"] <= now:
                    raise SubscriptionError("This confirmation expired. Please request a new one.")
                connection.execute(
                    """UPDATE angel_email_subscribers SET status='active', timezone=pending_timezone,
                    delivery_time=pending_time, consent_at=requested_at, consent_version=%s,
                    confirmed_at=%s, confirmation_nonce=NULL, confirmation_expires=NULL,
                    unsubscribed_at=NULL, updated_at=%s WHERE id=%s""",
                    (CONSENT_VERSION, now, now, row["id"]),
                )
            elif purpose == "unsubscribe":
                connection.execute(
                    """UPDATE angel_email_subscribers SET status='unsubscribed', confirmation_nonce=NULL,
                    confirmation_expires=NULL, unsubscribed_at=%s, updated_at=%s WHERE id=%s""",
                    (now, now, row["id"]),
                )
            elif purpose == "manage":
                if row["status"] != "active":
                    raise SubscriptionError("Please confirm your subscription before changing delivery preferences.")
                clock = validate_preferences(tz, clock)
                connection.execute("UPDATE angel_email_subscribers SET timezone=%s,delivery_time=%s,updated_at=%s WHERE id=%s", (tz, clock, now, row["id"]))
            else:
                raise SubscriptionError("This action is not available.")

    def active_subscribers(self):
        with self.connection() as connection:
            return connection.execute("SELECT * FROM angel_email_subscribers WHERE status='active' ORDER BY id").fetchall()

    def reserve(self, subscriber_id, message_key, kind, nonce=None, now=None):
        now = now or utc_now()
        with self.connection() as connection:
            connection.execute("SELECT pg_advisory_xact_lock(%s)", (LOCK_ID,))
            row = connection.execute("SELECT * FROM angel_email_subscribers WHERE id=%s FOR UPDATE", (subscriber_id,)).fetchone()
            if not row or (kind == "daily" and row["status"] != "active"):
                return None
            if kind == "confirmation" and row["confirmation_nonce"] != nonce:
                return None
            previous = connection.execute("SELECT * FROM angel_email_deliveries WHERE subscriber_id=%s AND message_key=%s", (subscriber_id, message_key)).fetchone()
            if previous and (previous["status"] != "deferred" or previous["retry_at"] > now):
                return None
            count = connection.execute("SELECT count(*) AS n FROM angel_email_attempts WHERE reserved_at > %s", (now - timedelta(hours=24),)).fetchone()["n"]
            if count >= self.settings.budget_24h:
                raise SubscriptionError("The email sending budget is full. Please try again later.")
            delivery_id = previous["id"] if previous else str(uuid4())
            if previous:
                connection.execute("UPDATE angel_email_deliveries SET status='reserved', retry_at=NULL WHERE id=%s", (delivery_id,))
            else:
                connection.execute(
                    """INSERT INTO angel_email_deliveries (id,subscriber_id,message_key,kind,nonce,status,created_at)
                    VALUES (%s,%s,%s,%s,%s,'reserved',%s)""",
                    (delivery_id, subscriber_id, message_key, kind, nonce, now),
                )
            connection.execute("INSERT INTO angel_email_attempts(id,delivery_id,reserved_at) VALUES (%s,%s,%s)", (str(uuid4()), delivery_id, now))
            return delivery_id

    def dispatch(self, delivery_id, send, now=None):
        now = now or utc_now()
        # Commit 'sending' BEFORE the API request. Interrupted requests are never
        # silently replayed: a subsequent run sees this state and skips the row.
        with self.connection() as connection:
            changed = connection.execute(
                "UPDATE angel_email_deliveries SET status='sending' WHERE id=%s AND status='reserved' RETURNING id",
                (delivery_id,),
            ).fetchone()
            if not changed:
                return SendResult("skipped")
        with self.connection() as connection:
            delivery = connection.execute("SELECT * FROM angel_email_deliveries WHERE id=%s FOR UPDATE", (delivery_id,)).fetchone()
            subscriber = connection.execute("SELECT * FROM angel_email_subscribers WHERE id=%s FOR UPDATE", (delivery["subscriber_id"],)).fetchone()
            allowed = (
                subscriber["status"] == "active" if delivery["kind"] == "daily"
                else subscriber["confirmation_nonce"] == delivery["nonce"] and subscriber["confirmation_expires"] > now
            )
            if not allowed:
                result = SendResult("skipped")
            else:
                result = send(subscriber)
            connection.execute(
                "UPDATE angel_email_deliveries SET status=%s,sent_at=%s,retry_at=%s WHERE id=%s",
                (result.state, now if result.state == "sent" else None,
                 now + timedelta(seconds=result.retry_after) if result.state == "deferred" else None, delivery_id),
            )
            return result


class EmailService:
    def __init__(self, settings, store=None, mailer=None):
        self.settings = settings
        self.store = store or subscription_store(settings)
        self.mailer = mailer or HostingerMailer(settings.api_token, settings.mailbox_address)

    def signup(self, email, tz, clock, consent, now=None):
        if not self.settings.ready or not self.settings.signups_enabled:
            raise SubscriptionError("Email signup is not available yet.")
        if not consent:
            raise SubscriptionError("Please agree to daily emails before signing up.")
        normalize_email(email)
        validate_preferences(tz, clock)
        self.mailer.verify_mailbox()
        self.store.initialize()
        subscriber = self.store.request(email, tz, clock, consent, now)
        if subscriber is None:
            return "recent_request"
        key = "confirmation:" + subscriber["confirmation_nonce"]
        delivery = self.store.reserve(subscriber["id"], key, "confirmation", subscriber["confirmation_nonce"], now)
        if not delivery:
            return "recent_request"
        result = self.store.dispatch(
            delivery, lambda row: self.mailer.send(row["email"], *render_email(self.settings, row, now=now)), now,
        )
        if result.state != "sent":
            raise SubscriptionError("We could not confirm delivery of the email. Please try again later.")
        return "sent"


def subscription_store(settings):
    if settings.https_database_ready:
        from supabase_email_store import SupabaseSubscriptionStore
        return SupabaseSubscriptionStore(settings)
    return SubscriptionStore(settings)


def due_message(subscriber, messages, now=None):
    now = now or utc_now()
    local = now.astimezone(ZoneInfo(subscriber["timezone"]))
    if local.time().replace(tzinfo=None) < subscriber["delivery_time"]:
        return None
    # Explicit approved date only; no random daily AI generation or rollover.
    return next((m for m in messages if m["date"] == local.date().isoformat() and m["approved_for_delivery"] is True), None)
