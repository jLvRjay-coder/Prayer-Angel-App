"""Private inbox test; public signup and scheduled delivery stay disabled.

Only a fresh, explicit send request can use EMAIL_TEST_RECIPIENT. The initial
check request performs read-only probes and cannot create a subscription.
"""

import argparse
from dataclasses import replace
from datetime import datetime, time, timedelta
import json
import os
from pathlib import Path
import re

from daily_encouragement import DAILY_MESSAGES
from deploy_space_preview import PREVIEW_FLAGS, SPACE_ID
from email_connection_check import check_connections
from email_subscription import (
    EmailService, EmailSettings, SubscriptionError, normalize_email,
    render_email, subscription_store, utc_now,
)
from hostinger_email import HostingerMailer


SPACE_SECRETS = {
    "HOSTINGER_MAIL_API_TOKEN", "EMAIL_SUPABASE_SECRET_KEY",
    "EMAIL_SIGNING_KEY", "EMAIL_POSTAL_ADDRESS",
}


def check_configuration(settings, space_api):
    checks = check_connections(settings)
    checks.update({
        "Postal address configured": bool(settings.postal_address.strip()),
        "Sender configuration ready": settings.ready,
        "GitHub public signup and delivery disabled": not (
            settings.signups_enabled or settings.delivery_enabled
        ),
        "Hugging Face required secret names present": False,
        "Hugging Face public signup and delivery disabled": False,
        "Hugging Face storage URL matches GitHub": False,
    })
    try:
        # These endpoints return secret names/metadata, never secret values.
        names = space_api.get_space_secrets(repo_id=SPACE_ID)
        variables = space_api.get_space_variables(repo_id=SPACE_ID)
        checks["Hugging Face required secret names present"] = SPACE_SECRETS <= set(names)
        checks["Hugging Face public signup and delivery disabled"] = all(
            flag not in names and (
                flag not in variables or variables[flag].value.strip().lower() in {"", "false"}
            ) for flag in PREVIEW_FLAGS
        )
        url = variables.get("EMAIL_SUPABASE_URL")
        checks["Hugging Face storage URL matches GitHub"] = bool(
            url and url.value.rstrip("/") == settings.supabase_url.rstrip("/")
        )
    except Exception:
        pass
    return checks


class RecipientOnlyMailer:
    def __init__(self, recipient, mailer):
        self.recipient = normalize_email(recipient)
        self.mailer = mailer

    def verify_mailbox(self):
        return self.mailer.verify_mailbox()

    def send(self, recipient, subject, text, html):
        if normalize_email(recipient) != self.recipient:
            raise SubscriptionError("The private test recipient did not match.")
        note = "This is your private email test. Automatic daily delivery remains off."
        return self.mailer.send(
            self.recipient, "[Private test] " + subject,
            note + "\n\n" + text, "<p>" + note + "</p>" + html,
        )


def run_private_test(settings, request, recipient="", send_authorized=False,
                     store=None, mailer=None, now=None):
    operation = request.get("operation")
    if operation == "check":
        return "checked_without_sending"
    if operation not in {"confirmation", "devotional"}:
        raise SubscriptionError("Unknown private test operation.")
    if not send_authorized:
        raise SubscriptionError("A private send must be explicitly authorized.")
    if not settings.ready or settings.signups_enabled or settings.delivery_enabled:
        raise SubscriptionError("Private testing requires configured email with both public enable flags off.")
    now = now or utc_now()
    try:
        requested = datetime.fromisoformat(request["requested_at"])
        age = now - requested
        valid_id = re.fullmatch(r"[a-z0-9-]{1,64}", request["request_id"])
        if not valid_id or not timedelta(0) <= age <= timedelta(minutes=30):
            raise ValueError
    except (KeyError, TypeError, ValueError):
        raise SubscriptionError("Private send requests expire after 30 minutes. Prepare a new authorized request.") from None
    recipient = normalize_email(recipient)
    store = store or subscription_store(settings)
    mailer = RecipientOnlyMailer(
        recipient, mailer or HostingerMailer(settings.api_token, settings.mailbox_address),
    )
    if operation == "confirmation":
        # This override exists only in this process; no public setting changes.
        return EmailService(replace(settings, signups_enabled=True), store, mailer).signup(
            recipient, "America/Denver", time(8), True, now,
        )
    message = next((m for m in DAILY_MESSAGES if m["id"] == request.get("message_id")), None)
    if message is None:
        raise SubscriptionError("Choose an existing devotional for the private test.")
    store.initialize()
    rows = [row for row in store.active_subscribers() if normalize_email(row["email"]) == recipient]
    if len(rows) != 1:
        raise SubscriptionError("Confirm the private test inbox before requesting its devotional.")
    mailer.verify_mailbox()
    # Explicitly testing a draft does not approve it for scheduled delivery.
    key = "private-test:" + request["request_id"] + ":" + message["id"]
    delivery = store.reserve(rows[0]["id"], key, "daily", now=now)
    if not delivery:
        return "already_handled"
    return store.dispatch(
        delivery, lambda row: mailer.send(row["email"], *render_email(settings, row, message, now)), now,
    ).state


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", default="email_test_request.json")
    parser.add_argument("--send", action="store_true")
    args = parser.parse_args()
    try:
        from huggingface_hub import HfApi

        settings = EmailSettings.from_env()
        token = os.environ.get("HF_TOKEN", "")
        checks = check_configuration(settings, HfApi(token=token) if token else None)
        for label, passed in checks.items():
            print(f"{'PASS' if passed else 'FAIL'}: {label}")
        if not all(checks.values()):
            print("Preflight stopped. No email sent; no subscriber records changed.")
            return 1
        request = json.loads(Path(args.request).read_text(encoding="utf-8"))
        result = run_private_test(
            settings, request, os.environ.get("EMAIL_TEST_RECIPIENT", ""), args.send,
        )
        print("Private test outcome: " + result)
        print("Hugging Face secret values and key matching require the live confirmation-link test.")
        if result in {"unknown", "rejected", "deferred"}:
            print("Check the delivery record and provider before preparing another send. No automatic retry.")
            return 1
        return 0
    except Exception:
        # Provider exceptions, recipients, addresses, tokens, and links stay private.
        print("Private test stopped. Check configuration and delivery records before any new send; no private values are logged.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
