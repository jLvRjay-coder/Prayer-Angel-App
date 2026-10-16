from dataclasses import replace
from datetime import datetime, time, timedelta, timezone
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from daily_encouragement import DAILY_MESSAGES
import email_private_test as private
from email_subscription import EmailSettings, SubscriptionError
from hostinger_email import SendResult


NOW = datetime(2026, 10, 16, 3, 0, tzinfo=timezone.utc)
RECIPIENT = "test-reader@example.com"


def configuration(**overrides):
    return replace(EmailSettings(
        supabase_url="https://example.supabase.co", supabase_secret_key="sb_secret_test",
        signing_key="a" * 64, api_token="test-api-token",
        postal_address="Private business mailing address",
    ), **overrides)


def subscriber(email=RECIPIENT):
    return {
        "id": "test-subscriber", "email": email, "status": "active",
        "timezone": "America/Denver", "delivery_time": time(8),
        "manage_nonce": "private-manage-nonce", "confirmation_nonce": "private-confirm-nonce",
        "confirmation_expires": NOW + timedelta(hours=24),
    }


def request(operation="confirmation", **overrides):
    return {"operation": operation, "request_id": "authorized-private-test-1",
            "requested_at": NOW.isoformat(), "message_id": DAILY_MESSAGES[0]["id"], **overrides}


class PrivateTestGuards(unittest.TestCase):
    def test_check_request_never_creates_store_or_mailer_even_with_send_switch(self):
        with patch.object(private, "subscription_store") as store, patch.object(private, "HostingerMailer") as mailer:
            self.assertEqual(private.run_private_test(
                configuration(), {"operation": "check"}, send_authorized=True,
            ), "checked_without_sending")
        store.assert_not_called()
        mailer.assert_not_called()

    def test_missing_authorization_recipient_or_configuration_never_sends(self):
        cases = [
            (configuration(), RECIPIENT, False),
            (configuration(), "", True),
            (configuration(signups_enabled=True), RECIPIENT, True),
            (configuration(delivery_enabled=True), RECIPIENT, True),
            (configuration(postal_address=""), RECIPIENT, True),
        ]
        for settings, recipient, authorized in cases:
            with self.subTest(settings=settings, authorized=authorized), \
                    patch.object(private, "subscription_store") as store, \
                    patch.object(private, "HostingerMailer") as mailer:
                with self.assertRaises(SubscriptionError):
                    private.run_private_test(settings, request(), recipient, authorized, now=NOW)
                store.assert_not_called()
                mailer.assert_not_called()

    def test_stale_future_naive_or_invalid_requests_never_touch_records(self):
        invalid = [
            request(requested_at=(NOW - timedelta(minutes=31)).isoformat()),
            request(requested_at=(NOW + timedelta(minutes=1)).isoformat()),
            request(requested_at=NOW.replace(tzinfo=None).isoformat()),
            request(request_id="invalid/request/id"),
            request(requested_at="invalid"),
            request(operation="send_everyone"),
        ]
        for item in invalid:
            with self.subTest(item=item), patch.object(private, "subscription_store") as store:
                with self.assertRaises(SubscriptionError):
                    private.run_private_test(configuration(), item, RECIPIENT, True, now=NOW)
                store.assert_not_called()

    def test_guard_refuses_a_different_dispatch_recipient(self):
        underlying = Mock()
        mailer = private.RecipientOnlyMailer(RECIPIENT, underlying)
        with self.assertRaises(SubscriptionError):
            mailer.send("someone-else@example.com", "Subject", "Text", "HTML")
        underlying.send.assert_not_called()

    def test_confirmation_uses_real_signed_template_without_changing_public_flags(self):
        settings, store, mailer = configuration(), Mock(), Mock()
        row = subscriber()
        store.request.return_value = row
        store.reserve.return_value = "confirmation-delivery"
        store.dispatch.side_effect = lambda delivery, send, now: send(row)
        mailer.send.return_value = SendResult("sent")
        result = private.run_private_test(settings, request(), RECIPIENT, True, store, mailer, NOW)
        self.assertEqual(result, "sent")
        self.assertFalse(settings.signups_enabled)
        self.assertFalse(settings.delivery_enabled)
        args = mailer.send.call_args.args
        self.assertEqual(args[0], RECIPIENT)
        self.assertTrue(args[1].startswith("[Private test] Confirm"))
        self.assertIn("action=confirm", args[2])
        self.assertIn(settings.postal_address, args[3])
        self.assertIn("Automatic daily delivery remains off", args[2])
        mailer.send.assert_called_once()

    def test_recent_confirmation_request_does_not_send_again(self):
        store, mailer = Mock(), Mock()
        store.request.return_value = None
        self.assertEqual(private.run_private_test(
            configuration(), request(), RECIPIENT, True, store, mailer, NOW,
        ), "recent_request")
        store.reserve.assert_not_called()
        mailer.send.assert_not_called()

    def test_devotional_requires_a_confirmed_inbox(self):
        store, mailer = Mock(), Mock()
        store.active_subscribers.return_value = []
        with self.assertRaises(SubscriptionError):
            private.run_private_test(configuration(), request("devotional"), RECIPIENT, True, store, mailer, NOW)
        store.reserve.assert_not_called()
        mailer.send.assert_not_called()

    def test_devotional_selects_only_test_inbox_and_preserves_draft_status(self):
        store, mailer = Mock(), Mock()
        row = subscriber()
        store.active_subscribers.return_value = [subscriber("other@example.com"), row]
        store.reserve.return_value = "sample-delivery"
        store.dispatch.side_effect = lambda delivery, send, now: send(row)
        mailer.send.return_value = SendResult("sent")
        self.assertEqual(private.run_private_test(
            configuration(), request("devotional"), RECIPIENT, True, store, mailer, NOW,
        ), "sent")
        self.assertEqual(store.reserve.call_args.args[0], row["id"])
        self.assertTrue(store.reserve.call_args.args[1].startswith("private-test:"))
        args = mailer.send.call_args.args
        self.assertEqual(args[0], RECIPIENT)
        self.assertIn(DAILY_MESSAGES[0]["devotional"], args[2])
        self.assertIn("action=unsubscribe", args[2])
        self.assertIn("action=manage", args[2])
        self.assertTrue(all(m["approved_for_delivery"] is False for m in DAILY_MESSAGES))

    def test_already_reserved_sample_never_reaches_send(self):
        store, mailer = Mock(), Mock()
        store.active_subscribers.return_value = [subscriber()]
        store.reserve.return_value = None
        self.assertEqual(private.run_private_test(
            configuration(), request("devotional"), RECIPIENT, True, store, mailer, NOW,
        ), "already_handled")
        store.dispatch.assert_not_called()
        mailer.send.assert_not_called()

    def test_uncertain_send_is_not_retried(self):
        store, mailer = Mock(), Mock()
        row = subscriber()
        store.active_subscribers.return_value = [row]
        store.reserve.return_value = "sample-delivery"
        store.dispatch.side_effect = lambda delivery, send, now: send(row)
        mailer.send.return_value = SendResult("unknown")
        self.assertEqual(private.run_private_test(
            configuration(), request("devotional"), RECIPIENT, True, store, mailer, NOW,
        ), "unknown")
        mailer.send.assert_called_once()


class PrivatePreflightTests(unittest.TestCase):
    def api(self):
        api = Mock(spec=["get_space_secrets", "get_space_variables"])
        api.get_space_secrets.return_value = {name: object() for name in private.SPACE_SECRETS}
        api.get_space_variables.return_value = {
            "EMAIL_SUPABASE_URL": SimpleNamespace(value=configuration().supabase_url),
        }
        return api

    def test_metadata_check_never_reads_secret_values(self):
        api = self.api()
        with patch.object(private, "check_connections", return_value={"Backend health": True}):
            checks = private.check_configuration(configuration(), api)
        self.assertTrue(all(checks.values()))
        api.get_space_secrets.assert_called_once_with(repo_id=private.SPACE_ID)
        api.get_space_variables.assert_called_once_with(repo_id=private.SPACE_ID)

    def test_missing_address_or_enabled_or_secret_flags_fail_preflight(self):
        for mode in ("missing_address", "enabled", "secret_flag"):
            api = self.api()
            if mode == "missing_address":
                api.get_space_secrets.return_value.pop("EMAIL_POSTAL_ADDRESS")
            elif mode == "enabled":
                api.get_space_variables.return_value["EMAIL_SIGNUPS_ENABLED"] = SimpleNamespace(value="true")
            else:
                api.get_space_secrets.return_value["EMAIL_DELIVERY_ENABLED"] = object()
            with self.subTest(mode=mode), patch.object(private, "check_connections", return_value={"Backend health": True}):
                self.assertFalse(all(private.check_configuration(configuration(), api).values()))

    def test_metadata_failure_never_returns_provider_error_or_private_values(self):
        api = self.api()
        api.get_space_secrets.side_effect = RuntimeError("private-provider-error")
        with patch.object(private, "check_connections", return_value={"Backend health": True}):
            checks = private.check_configuration(configuration(), api)
        self.assertFalse(all(checks.values()))
        self.assertNotIn("private-provider-error", str(checks))
        self.assertNotIn(configuration().postal_address, str(checks))


if __name__ == "__main__":
    unittest.main()
