import contextlib
from dataclasses import replace
import io
import unittest
from unittest.mock import Mock, patch

import requests

import email_connection_check as check
from email_subscription import EmailSettings
from hostinger_email import HostingerMailer
from supabase_email_store import SupabaseSubscriptionStore


class ConnectionCheckTests(unittest.TestCase):
    def configuration(self, **overrides):
        settings = EmailSettings(
            supabase_url="https://example.supabase.co",
            supabase_secret_key="sb_secret_test_backend_only",
            signing_key="a" * 64,
            api_token="not-a-real-token",
        )
        return replace(settings, **overrides)

    def test_probes_only_health_and_mailbox_even_with_delivery_enabled(self):
        settings = self.configuration(signups_enabled=True, delivery_enabled=True)
        self.assertFalse(settings.ready)  # Postal address intentionally absent.
        storage_session = Mock(spec=["post"])
        storage_session.post.return_value.status_code = 200
        storage_session.post.return_value.json.return_value = {"version": 1}
        mail_session = Mock(spec=["get", "post"])
        mail_session.get.return_value.json.return_value = {
            "data": {"mailboxes": [{"address": settings.mailbox_address, "resourceId": "test-mailbox"}]}
        }
        store = SupabaseSubscriptionStore(settings, storage_session)
        mailer = HostingerMailer(settings.api_token, settings.mailbox_address, mail_session)
        with patch.object(check, "SupabaseSubscriptionStore", return_value=store), \
                patch.object(check, "HostingerMailer", return_value=mailer):
            self.assertTrue(all(check.check_connections(settings).values()))
        storage_session.post.assert_called_once()
        self.assertEqual(storage_session.post.call_args.kwargs["json"], {"p_action": "health", "p_data": {}})
        self.assertEqual(storage_session.post.call_args.args[0], settings.supabase_url + "/rest/v1/rpc/angel_email_backend")
        mail_session.get.assert_called_once()
        self.assertEqual(mail_session.get.call_args.args[0], HostingerMailer.API_URL + "/me")
        self.assertEqual(mail_session.get.call_args.kwargs["headers"]["Content-Type"], "application/json")
        mail_session.post.assert_not_called()

    def test_mail_rejections_have_safe_reasons_and_never_send(self):
        settings = self.configuration()
        for status, reason in [(401, "HTTP 401: token rejected"), (403, "HTTP 403: access denied"), (429, "HTTP 429: rate limited")]:
            with self.subTest(status=status):
                session = Mock(spec=["get", "post"])
                session.get.return_value.status_code = status
                mailer = HostingerMailer(settings.api_token, settings.mailbox_address, session)
                with patch.object(check, "SupabaseSubscriptionStore"), \
                        patch.object(check, "HostingerMailer", return_value=mailer):
                    checks = check.check_connections(settings)
                self.assertFalse(checks[f"Hostinger mailbox authorization ({reason})"])
                session.get.return_value.json.assert_not_called()
                session.post.assert_not_called()

    def test_missing_credentials_do_not_make_network_calls(self):
        with patch.object(check, "SupabaseSubscriptionStore") as store, \
                patch.object(check, "HostingerMailer") as mailer:
            self.assertFalse(any(check.check_connections(EmailSettings()).values()))
        store.assert_not_called()
        mailer.assert_not_called()

    def test_upstream_access_block_is_distinguished_without_printing_body(self):
        settings = self.configuration()
        for headers, reason in [
            ({"CF-Mitigated": "challenge"}, "provider security challenge"),
            ({"Content-Type": "text/html; charset=utf-8"}, "HTML access-denied response, not the JSON API"),
        ]:
            with self.subTest(headers=headers):
                session = Mock(spec=["get", "post"])
                session.get.return_value.status_code = 403
                session.get.return_value.headers = headers
                mailer = HostingerMailer(settings.api_token, settings.mailbox_address, session)
                with patch.object(check, "SupabaseSubscriptionStore"), \
                        patch.object(check, "HostingerMailer", return_value=mailer):
                    checks = check.check_connections(settings)
                self.assertFalse(checks[f"Hostinger mailbox authorization (HTTP 403: {reason})"])
                session.get.return_value.json.assert_not_called()
                session.post.assert_not_called()

    def test_pasted_powershell_command_does_not_pass_signing_key_check(self):
        with patch.object(check, "SupabaseSubscriptionStore") as store, \
                patch.object(check, "HostingerMailer") as mailer:
            result = check.check_connections(self.configuration(signing_key="[Convert]::ToBase64String($angelKeyBytes)"))
        self.assertFalse(result["Signing key format"])
        self.assertFalse(result["Supabase backend storage"])
        store.assert_not_called()
        mailer.return_value.verify_mailbox.assert_called_once()

    def test_failed_provider_errors_are_not_printed_and_other_checks_run(self):
        settings = self.configuration()
        with patch.object(check.EmailSettings, "from_env", return_value=settings), \
                patch.object(check, "SupabaseSubscriptionStore") as store, \
                patch.object(check, "HostingerMailer") as mailer:
            store.return_value.initialize.side_effect = requests.ConnectionError(settings.supabase_secret_key)
            mailer.return_value.verify_mailbox.side_effect = requests.ConnectionError(settings.api_token)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(check.main(), 1)
        mailer.return_value.verify_mailbox.assert_called_once()
        self.assertIn("FAIL: Supabase backend storage", output.getvalue())
        self.assertIn("FAIL: Hostinger mailbox authorization", output.getvalue())
        self.assertNotIn(settings.supabase_secret_key, output.getvalue())
        self.assertNotIn(settings.api_token, output.getvalue())

    def test_invalid_settings_exit_without_printing_the_invalid_value(self):
        with patch.object(check.EmailSettings, "from_env", side_effect=ValueError("private-invalid-value")):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(check.main(), 1)
        self.assertNotIn("private-invalid-value", output.getvalue())


if __name__ == "__main__":
    unittest.main()
