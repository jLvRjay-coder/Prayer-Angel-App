"""Run outside Streamlit: python email_worker.py [--initialize].

The worker uses the same durable database and signing key as the app. It sends
only explicitly approved teachings on their scheduled local date. Logs are
counts and outcome categories only, with no recipient or credential values.
"""

import argparse
from collections import Counter
import time

from daily_encouragement import DAILY_MESSAGES
from email_subscription import (
    EmailSettings, SubscriptionError, SubscriptionStore, due_message, render_email, utc_now,
)
from hostinger_email import HostingerMailer


def run_worker(settings, store=None, mailer=None, messages=DAILY_MESSAGES, now=None, pause=time.sleep):
    if not settings.delivery_enabled:
        return {"disabled": 1}
    if not settings.ready:
        raise SubscriptionError("The email worker is not configured.")
    store = store or SubscriptionStore(settings)
    mailer = mailer or HostingerMailer(settings.api_token, settings.mailbox_address)
    store.initialize()
    mailer.verify_mailbox()
    totals = Counter()
    for subscriber in store.active_subscribers():
        current_time = now or utc_now()
        message = due_message(subscriber, messages, current_time)
        if not message:
            totals["not_due"] += 1
            continue
        try:
            delivery_id = store.reserve(subscriber["id"], "daily:" + message["id"], "daily", now=current_time)
        except SubscriptionError:
            totals["budget_full"] += 1
            break
        if not delivery_id:
            totals["already_handled"] += 1
            continue
        result = store.dispatch(
            delivery_id, lambda row: mailer.send(row["email"], *render_email(settings, row, message, current_time)),
            current_time,
        )
        totals[result.state] += 1
        if result.state in {"unknown", "rejected", "deferred"}:
            break
        # A conservative pace; this does not assume an undocumented API quota.
        pause(1)
    return dict(totals)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--initialize", action="store_true", help="Create the database tables without sending email")
    args = parser.parse_args()
    settings = EmailSettings.from_env()
    try:
        if args.initialize:
            SubscriptionStore(settings).initialize()
            print("Subscription tables initialized; no email sent.")
        else:
            print(run_worker(settings))
    except Exception:
        print("Email worker stopped. Check the configured database, credentials, and delivery records; no private values are logged.")
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
