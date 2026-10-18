"""Backend-only HTTPS storage for Spaces, which block Postgres TCP ports.

Every mutation is a narrow, transaction-safe RPC. There is no generic SQL
endpoint. Supabase's secret API key remains on the Python server, never in UI.
"""

from datetime import datetime, time
import hmac
import secrets
from uuid import uuid4

import requests

from email_subscription import (
    CONSENT_VERSION, SubscriptionError, normalize_email, read_token,
    utc_now, validate_preferences,
)
from hostinger_email import SendResult


SAFE_ERRORS = {
    "pilot_full": "The email pilot is currently full. Please try again later.",
    "budget_full": "The email sending budget is full. Please try again later.",
    "invalid_link": "This link is no longer valid. Please use the latest email.",
    "expired_confirmation": "This confirmation expired. Please request a new one.",
    "not_active": "Please confirm your subscription before changing delivery preferences.",
}


def _subscriber(row):
    if not row:
        return None
    row = dict(row)
    for key in ("delivery_time", "pending_time"):
        if row.get(key) is not None:
            row[key] = time.fromisoformat(row[key])
    for key in (
        "confirmation_expires", "requested_at", "consent_at", "confirmed_at",
        "unsubscribed_at", "updated_at",
    ):
        if row.get(key) is not None:
            row[key] = datetime.fromisoformat(row[key].replace("Z", "+00:00"))
    return row


class SupabaseSubscriptionStore:
    def __init__(self, settings, session=None):
        self.settings = settings
        self.session = session or requests.Session()

    def rpc(self, action, data=None):
        if not self.settings.storage_ready or not self.settings.https_database_ready:
            raise SubscriptionError("Email signup is not available yet.")
        try:
            response = self.session.post(
                self.settings.supabase_url.rstrip("/") + "/rest/v1/rpc/angel_email_backend",
                headers={"apikey": self.settings.supabase_secret_key, "Content-Type": "application/json"},
                json={"p_action": action, "p_data": data or {}},
                timeout=(5, 20), allow_redirects=False,
            )
            if response.status_code != 200:
                raise SubscriptionError("Email storage is temporarily unavailable. Please try again later.")
            result = response.json()
        except (requests.RequestException, ValueError):
            # RPCs are never automatically retried: a timeout may have committed.
            raise SubscriptionError("Email storage is temporarily unavailable. Please try again later.") from None
        if isinstance(result, dict) and "error" in result:
            raise SubscriptionError(SAFE_ERRORS.get(result["error"], "Email storage is temporarily unavailable. Please try again later."))
        return result

    def initialize(self):
        # Tables/RPCs are installed by a migration, not by public signup requests.
        if self.rpc("health") != {"version": 1}:
            raise SubscriptionError("Email storage is not configured yet.")

    def request(self, email, tz, clock, consent, now=None):
        if not consent:
            raise SubscriptionError("Please agree to daily emails before signing up.")
        now = now or utc_now()
        row = self.rpc("request", {
            "email": normalize_email(email), "timezone": tz,
            "delivery_time": validate_preferences(tz, clock).isoformat(),
            "now": now.isoformat(), "max_subscribers": self.settings.max_subscribers,
            "new_id": str(uuid4()), "manage_nonce": secrets.token_urlsafe(24),
            "confirmation_nonce": secrets.token_urlsafe(24),
        })
        return _subscriber(row)

    def token_subscriber(self, token, purpose, now=None):
        claims = read_token(self.settings, token, purpose, now)
        row = _subscriber(self.rpc("read_subscriber", {"id": claims["id"]}))
        field = "confirmation_nonce" if purpose == "confirm" else "manage_nonce"
        if not row or not hmac.compare_digest(row[field] or "", claims["nonce"]):
            raise SubscriptionError("This link is no longer valid. Please use the latest email.")
        return row

    def apply_action(self, token, purpose, tz=None, clock=None, now=None):
        now = now or utc_now()
        claims = read_token(self.settings, token, purpose, now)
        data = {
            "id": claims["id"], "nonce": claims["nonce"], "purpose": purpose,
            "now": now.isoformat(), "consent_version": CONSENT_VERSION,
        }
        if purpose == "manage":
            data.update(timezone=tz, delivery_time=validate_preferences(tz, clock).isoformat())
        self.rpc("apply_action", data)

    def active_subscribers(self):
        return [_subscriber(row) for row in self.rpc("active_subscribers")]

    def reserve(self, subscriber_id, message_key, kind, nonce=None, now=None):
        return self.rpc("reserve", {
            "id": subscriber_id, "message_key": message_key, "kind": kind,
            "nonce": nonce, "now": (now or utc_now()).isoformat(),
            "budget_24h": self.settings.budget_24h,
            "delivery_id": str(uuid4()), "attempt_id": str(uuid4()),
        })

    def dispatch(self, delivery_id, send, now=None):
        now = now or utc_now()
        # Atomically check consent and commit 'sending' before calling Hostinger.
        # A request already in flight cannot be recalled by a later opt-out.
        row = _subscriber(self.rpc("claim", {"delivery_id": delivery_id, "now": now.isoformat()}))
        if not row:
            return SendResult("skipped")
        result = send(row)
        saved = self.rpc("complete", {
            "delivery_id": delivery_id, "state": result.state,
            "retry_after": result.retry_after, "now": now.isoformat(),
        })
        if saved is not True:
            raise SubscriptionError("We could not confirm the delivery record. Please try again later.")
        return result
