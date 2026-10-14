from dataclasses import replace
from datetime import datetime, time, timedelta, timezone
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlparse

import requests
import psycopg
from streamlit.testing.v1 import AppTest

from daily_encouragement import DAILY_MESSAGES
from email_subscription import (
    CONSENT_VERSION, EmailService, EmailSettings, SubscriptionError, SubscriptionStore,
    action_url, due_message, make_token, read_token, render_email,
)
from email_worker import run_worker
from hostinger_email import HostingerMailer, MailUnavailable, SendResult


NOW = datetime(2026, 10, 14, 15, 0, tzinfo=timezone.utc)
ROOT = Path(__file__).resolve().parents[1]


def settings(**overrides):
    return replace(EmailSettings(
        database_url=os.environ.get("EMAIL_TEST_DATABASE_URL", "postgresql://localhost/test"),
        signing_key="local-test-signing-key-32-characters", api_token="test-api-token",
        signups_enabled=True, delivery_enabled=True, postal_address="Test ministry postal address",
    ), **overrides)


def subscriber():
    return {
        "id": "subscriber-test", "email": "reader@example.com", "status": "active",
        "timezone": "America/Denver", "delivery_time": time(8),
        "manage_nonce": "manage-nonce", "confirmation_nonce": "confirmation-nonce",
        "confirmation_expires": NOW + timedelta(hours=24),
    }


class TransportTests(unittest.TestCase):
    def mailer(self, code=204):
        session = Mock()
        session.get.return_value.json.return_value = {"data": {"mailboxes": [{"address": "contact@beyondthemessage.org", "resourceId": "authorized-box"}]}}
        session.post.return_value = SimpleNamespace(status_code=code, headers={"Retry-After": "300"})
        return HostingerMailer("not-a-real-token", session=session), session

    def test_sends_to_one_person_using_verified_mailbox(self):
        mailer, session = self.mailer()
        self.assertEqual(mailer.send("reader@example.com", "Title", "Text", "<p>Text</p>").state, "sent")
        arguments = session.post.call_args.kwargs
        self.assertEqual(arguments["json"]["to"], ["reader@example.com"])
        self.assertNotIn("cc", arguments["json"])
        self.assertNotIn("bcc", arguments["json"])
        self.assertFalse(arguments["allow_redirects"])

    def test_uncertain_send_is_not_retried(self):
        mailer, session = self.mailer()
        session.post.side_effect = requests.Timeout()
        self.assertEqual(mailer.send("reader@example.com", "Title", "Text", "HTML").state, "unknown")
        session.post.assert_called_once()

    def test_rate_limit_honors_retry_after(self):
        mailer, _ = self.mailer(429)
        self.assertEqual(mailer.send("reader@example.com", "Title", "Text", "HTML"), SendResult("deferred", 300))

    def test_wrong_mailbox_cannot_send(self):
        mailer, session = self.mailer()
        session.get.return_value.json.return_value = {"data": {"mailboxes": [{"address": "other@example.com", "resourceId": "other-box"}]}}
        with self.assertRaises(MailUnavailable):
            mailer.send("reader@example.com", "Title", "Text", "HTML")
        session.post.assert_not_called()


class LinkAndScheduleTests(unittest.TestCase):
    def test_signed_links_are_purpose_bound_and_expire(self):
        token = make_token(settings(), subscriber(), "confirm", NOW)
        self.assertEqual(read_token(settings(), token, "confirm", NOW)["id"], "subscriber-test")
        for invalid in (token + "a", token.replace(".", "x", 1)):
            with self.assertRaises(SubscriptionError):
                read_token(settings(), invalid, "confirm", NOW)
        with self.assertRaises(SubscriptionError):
            read_token(settings(), token, "unsubscribe", NOW)
        with self.assertRaises(SubscriptionError):
            read_token(settings(), token, "confirm", NOW + timedelta(days=2))

    def test_email_has_unsubscribe_preferences_and_specific_message_link(self):
        _, text, body = render_email(settings(), subscriber(), DAILY_MESSAGES[0], NOW)
        self.assertIn("message=compass-w01-god-sends", text)
        self.assertIn("Unsubscribe:", text)
        self.assertIn("Email preferences:", text)
        self.assertIn("Test ministry postal address", body)
        self.assertNotIn("sid=", text)
        url = action_url(settings(), subscriber(), "unsubscribe", NOW)
        query = parse_qs(urlparse(url).query)
        self.assertEqual(set(query), {"v", "action", "token"})
        self.assertNotIn("reader@example.com", url)

    def test_unapproved_or_wrong_date_message_is_never_due(self):
        self.assertIsNone(due_message(subscriber(), DAILY_MESSAGES, NOW))
        approved = {**DAILY_MESSAGES[0], "approved_for_delivery": True}
        self.assertEqual(due_message(subscriber(), [approved], NOW)["id"], approved["id"])
        self.assertIsNone(due_message(subscriber(), [approved], NOW - timedelta(hours=2)))
        self.assertIsNone(due_message(subscriber(), [approved], NOW + timedelta(days=1)))

    def test_different_timezones_get_their_local_scheduled_date(self):
        late = datetime(2026, 10, 15, 2, tzinfo=timezone.utc)
        west = {**subscriber(), "timezone": "America/Los_Angeles"}
        east = {**subscriber(), "timezone": "Asia/Tokyo"}
        approved = [{**m, "approved_for_delivery": True} for m in DAILY_MESSAGES]
        self.assertEqual(due_message(west, approved, late)["date"], "2026-10-14")
        self.assertEqual(due_message(east, approved, late)["date"], "2026-10-15")

    def test_disabled_worker_has_no_side_effects(self):
        store, mailer = Mock(), Mock()
        self.assertEqual(run_worker(settings(delivery_enabled=False), store, mailer), {"disabled": 1})
        store.initialize.assert_not_called()
        mailer.verify_mailbox.assert_not_called()

    def test_subscriber_credentials_are_not_in_settings_repr(self):
        rendered = repr(settings())
        self.assertNotIn("test-api-token", rendered)
        self.assertNotIn("local-test-signing", rendered)
        self.assertNotIn("postgresql://", rendered)


@unittest.skipUnless(os.environ.get("EMAIL_TEST_DATABASE_URL"), "Set EMAIL_TEST_DATABASE_URL for PostgreSQL integration tests")
class DatabaseFlowTests(unittest.TestCase):
    def setUp(self):
        self.settings = settings()
        self.store = SubscriptionStore(self.settings)
        self.store.initialize()
        with self.store.connection() as connection:
            connection.execute("TRUNCATE angel_email_attempts,angel_email_deliveries,angel_email_subscribers CASCADE")

    def requested(self, email="reader@example.com", now=NOW):
        return self.store.request(email, "America/Denver", time(8), True, now)

    def activate(self, row):
        self.store.apply_action(make_token(self.settings, row, "confirm", NOW), "confirm", now=NOW)
        return self.store.active_subscribers()[0]

    def test_client_cannot_read_or_write_contacts_even_after_accidental_grants(self):
        self.requested()
        with self.store.connection() as connection:
            # All role/grant changes roll back; only the isolated test DB is used.
            try:
                connection.execute("CREATE ROLE angel_email_privacy_test NOLOGIN")
                connection.execute("GRANT USAGE ON SCHEMA angel_email_private TO angel_email_privacy_test")
                connection.execute("GRANT SELECT, INSERT ON ALL TABLES IN SCHEMA angel_email_private TO angel_email_privacy_test")
                connection.execute("SET LOCAL ROLE angel_email_privacy_test")
                for table in ("angel_email_subscribers", "angel_email_deliveries", "angel_email_attempts"):
                    self.assertEqual(connection.execute(f"SELECT count(*) AS n FROM {table}").fetchone()["n"], 0)
                with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                    with connection.transaction():
                        connection.execute("""INSERT INTO angel_email_subscribers
                            (id,email,status,timezone,delivery_time,manage_nonce,requested_at,updated_at)
                            VALUES ('blocked','blocked@example.com','pending','UTC','08:00','test',now(),now())""")
            finally:
                connection.rollback()

    def test_consent_confirmation_and_unsubscribe(self):
        with self.assertRaises(SubscriptionError):
            self.store.request("reader@example.com", "America/Denver", time(8), False, NOW)
        row = self.requested()
        self.assertEqual(self.store.active_subscribers(), [])
        confirmation = make_token(self.settings, row, "confirm", NOW)
        self.store.token_subscriber(confirmation, "confirm", NOW)  # Opening link is read-only.
        self.assertEqual(self.store.active_subscribers(), [])
        active = self.activate(row)
        self.assertEqual(active["consent_version"], CONSENT_VERSION)
        unsubscribe = make_token(self.settings, active, "unsubscribe", NOW)
        self.store.apply_action(unsubscribe, "unsubscribe", now=NOW)
        self.assertEqual(self.store.active_subscribers(), [])
        with self.assertRaises(SubscriptionError):
            self.store.apply_action(confirmation, "confirm", now=NOW)

    def test_duplicate_send_and_opt_out_after_reservation(self):
        active = self.activate(self.requested())
        key = "daily:example-message"
        delivery = self.store.reserve(active["id"], key, "daily", now=NOW)
        self.assertIsNone(self.store.reserve(active["id"], key, "daily", now=NOW))
        self.store.apply_action(make_token(self.settings, active, "unsubscribe", NOW), "unsubscribe", now=NOW)
        send = Mock(return_value=SendResult("sent"))
        self.assertEqual(self.store.dispatch(delivery, send, NOW).state, "skipped")
        send.assert_not_called()

    def test_uncertain_provider_result_never_replays_same_message(self):
        active = self.activate(self.requested())
        delivery = self.store.reserve(active["id"], "daily:uncertain", "daily", now=NOW)
        self.store.dispatch(delivery, lambda row: SendResult("unknown"), NOW)
        self.assertIsNone(self.store.reserve(active["id"], "daily:uncertain", "daily", now=NOW + timedelta(hours=2)))

    def test_rolling_budget_includes_confirmation_attempts(self):
        limited = SubscriptionStore(replace(self.settings, budget_24h=1))
        pending = self.requested()
        limited.reserve(pending["id"], "confirmation:first", "confirmation", pending["confirmation_nonce"], now=NOW)
        active = self.activate(pending)
        with self.assertRaises(SubscriptionError):
            limited.reserve(active["id"], "daily:second", "daily", now=NOW + timedelta(hours=23))
        self.assertTrue(limited.reserve(active["id"], "daily:second", "daily", now=NOW + timedelta(hours=24, seconds=1)))

    def test_signup_confirmation_email_completes_the_flow(self):
        mailer = Mock()
        mailer.send.return_value = SendResult("sent")
        service = EmailService(self.settings, self.store, mailer)
        self.assertEqual(service.signup("reader@example.com", "America/Denver", time(8), True, NOW), "sent")
        self.assertEqual(self.store.active_subscribers(), [])
        recipient, subject, body, html_body = mailer.send.call_args.args
        self.assertEqual(recipient, "reader@example.com")
        confirm_url = next(line for line in body.splitlines() if line.startswith("https://") and "action=confirm" in line)
        token = parse_qs(urlparse(confirm_url).query)["token"][0]
        self.store.apply_action(token, "confirm", now=NOW)
        self.assertEqual(len(self.store.active_subscribers()), 1)
        self.assertIn("Confirm your email", html_body)

    def test_preferences_and_unsubscribe_work_when_sending_credentials_are_removed(self):
        active = self.activate(self.requested())
        store = SubscriptionStore(replace(self.settings, api_token="", delivery_enabled=False))
        manage = make_token(self.settings, active, "manage", NOW)
        store.apply_action(manage, "manage", "America/New_York", time(9), NOW)
        self.assertEqual(store.active_subscribers()[0]["timezone"], "America/New_York")
        store.apply_action(make_token(self.settings, active, "unsubscribe", NOW), "unsubscribe", now=NOW)
        self.assertEqual(store.active_subscribers(), [])

    def test_pilot_cap_counts_pending_and_active_subscribers(self):
        capped = SubscriptionStore(replace(self.settings, max_subscribers=1))
        capped.request("first@example.com", "America/Denver", time(8), True, NOW)
        with self.assertRaises(SubscriptionError):
            capped.request("second@example.com", "America/Denver", time(8), True, NOW)

    def test_repeated_confirmation_requests_are_throttled(self):
        self.requested()
        self.assertIsNone(self.requested(now=NOW + timedelta(minutes=10)))
        self.assertIsNotNone(self.requested(now=NOW + timedelta(hours=2)))

    def test_reopt_in_requires_new_confirmation_and_invalidates_old_links(self):
        active = self.activate(self.requested())
        old_link = make_token(self.settings, active, "unsubscribe", NOW)
        self.store.apply_action(old_link, "unsubscribe", now=NOW)
        pending = self.requested(now=NOW + timedelta(hours=2))
        self.assertEqual(self.store.active_subscribers(), [])
        with self.assertRaises(SubscriptionError):
            self.store.apply_action(old_link, "unsubscribe", now=NOW + timedelta(hours=2))
        self.store.apply_action(make_token(self.settings, pending, "confirm", NOW + timedelta(hours=2)), "confirm", now=NOW + timedelta(hours=2))
        self.assertEqual(len(self.store.active_subscribers()), 1)

    def test_worker_sends_once_then_respects_unsubscribe(self):
        active = self.activate(self.requested())
        mailer = Mock()
        mailer.send.return_value = SendResult("sent")
        approved = [{**DAILY_MESSAGES[0], "approved_for_delivery": True}]
        result = run_worker(self.settings, self.store, mailer, approved, NOW, pause=lambda _: None)
        self.assertEqual(result, {"sent": 1})
        run_worker(self.settings, self.store, mailer, approved, NOW, pause=lambda _: None)
        mailer.send.assert_called_once()
        self.store.apply_action(make_token(self.settings, active, "unsubscribe", NOW), "unsubscribe", now=NOW)
        run_worker(self.settings, self.store, mailer, approved, NOW, pause=lambda _: None)
        mailer.send.assert_called_once()


class EmailScreenTests(unittest.TestCase):
    def test_only_mail_token_does_not_enable_signup(self):
        with patch.dict(os.environ, {"HOSTINGER_MAIL_API_TOKEN": "local-token"}, clear=True):
            at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=15)
            at.query_params["v"] = "email"
            at.run()
            self.assertFalse(at.exception)
            self.assertEqual(len(at.text_input), 0)
            self.assertIn("Daily email signup will open soon", at.info[0].value)

    def test_opening_confirmation_link_never_confirms_automatically(self):
        with patch("email_ui.email_settings", return_value=settings()), patch("email_ui.SubscriptionStore") as store:
            store.return_value.token_subscriber.return_value = subscriber()
            at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=15)
            at.query_params.update({"v": "email", "action": "confirm", "token": "private-test-token"})
            at.run()
            self.assertFalse(at.exception)
            store.return_value.apply_action.assert_not_called()
            nav = "\n".join(e.value for e in at.markdown if "btm-bottom-nav" in e.value)
            self.assertNotIn("private-test-token", nav)
            at.button(key="email_confirm_action").click().run()
            self.assertFalse(at.exception)
            store.return_value.apply_action.assert_called_once()
            self.assertNotIn("token", at.query_params)


if __name__ == "__main__":
    unittest.main()
