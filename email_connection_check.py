"""Check backend credentials without subscriptions, delivery records, or email sends."""

import re

from email_subscription import EmailSettings
from hostinger_email import HostingerMailer
from supabase_email_store import SupabaseSubscriptionStore


def check_connections(settings):
    """Return fixed labels and pass/fail only; never return provider error text.

    Supabase's health RPC reads only a version marker. Hostinger's /me endpoint
    reads mailbox authorization. Neither probe calls subscription/delivery APIs,
    even if a caller accidentally enables signup or delivery flags.
    """
    checks = {
        "Signing key format": bool(re.fullmatch(r"[A-Za-z0-9_+/=-]{32,256}", settings.signing_key)),
        "Supabase backend storage": False,
        "Hostinger mailbox authorization": False,
    }
    if settings.https_database_ready and checks["Signing key format"]:
        try:
            # Use the HTTPS adapter explicitly. The legacy PostgreSQL initializer
            # can create tables and is intentionally unavailable to this check.
            SupabaseSubscriptionStore(settings).initialize()
            checks["Supabase backend storage"] = True
        except Exception:
            pass
    if settings.api_token:
        try:
            checks["Hostinger mailbox authorization"] = bool(
                HostingerMailer(settings.api_token, settings.mailbox_address).verify_mailbox()
            )
        except Exception:
            pass
    return checks


def main():
    try:
        checks = check_connections(EmailSettings.from_env())
    except Exception:
        print("FAIL: Email settings could not be loaded. No email sent.")
        return 1
    for label, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'}: {label}")
    print("No email sent. No subscriber or delivery records changed.")
    print("Hugging Face key matching, public links, and inbox delivery still require separate tests.")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
