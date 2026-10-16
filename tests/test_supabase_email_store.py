from dataclasses import replace
from datetime import time
from pathlib import Path
from types import SimpleNamespace
import os
import unittest
from unittest.mock import Mock, patch

import psycopg
from psycopg.types.json import Jsonb
import requests

from email_subscription import EmailSettings, SubscriptionError, SubscriptionStore, subscription_store
from hostinger_email import SendResult
from supabase_email_store import SupabaseSubscriptionStore
import test_email_subscription as flow


ROOT = Path(__file__).resolve().parents[1]
RPC_SQL = next((ROOT / "supabase" / "migrations").glob("*_backend_email_https_rpc.sql"))


def https_settings(configuration=None):
    return replace(configuration or flow.settings(),
        supabase_url="https://srjstdtnabzkmnuilceb.supabase.co",
        supabase_secret_key="sb_secret_local-test-backend-key",
    )


class HTTPSStorageTests(unittest.TestCase):
    def test_factory_uses_https_and_keeps_the_key_on_the_server(self):
        configuration = https_settings()
        self.assertIsInstance(subscription_store(configuration), SupabaseSubscriptionStore)
        self.assertNotIn(configuration.supabase_secret_key, repr(configuration))
        session = Mock()
        session.post.return_value = SimpleNamespace(status_code=200, json=lambda: {"version": 1})
        SupabaseSubscriptionStore(configuration, session).initialize()
        args, kwargs = session.post.call_args
        self.assertEqual(args[0], configuration.supabase_url + "/rest/v1/rpc/angel_email_backend")
        self.assertEqual(kwargs["headers"]["apikey"], configuration.supabase_secret_key)
        self.assertNotIn("Authorization", kwargs["headers"])
        self.assertFalse(kwargs["allow_redirects"])
        self.assertEqual(kwargs["json"], {"p_action": "health", "p_data": {}})

    def test_publishable_key_is_not_accepted_as_a_backend_credential(self):
        configuration = replace(https_settings(), database_url="", supabase_secret_key="sb_publishable_test")
        self.assertFalse(configuration.storage_ready)
        session = Mock()
        with self.assertRaises(SubscriptionError):
            SupabaseSubscriptionStore(configuration, session).initialize()
        session.post.assert_not_called()

    def test_network_errors_are_safe_and_never_automatically_retried(self):
        configuration = https_settings()
        session = Mock()
        session.post.side_effect = requests.Timeout("private response including sensitive details")
        with self.assertRaises(SubscriptionError) as captured:
            SupabaseSubscriptionStore(configuration, session).initialize()
        self.assertNotIn("sensitive", str(captured.exception))
        session.post.assert_called_once()

    def test_mistyped_url_does_not_crash_readiness_check(self):
        for value in ("https://project.supabase.co:wrong", "https://[invalid"):
            configuration = replace(https_settings(), database_url="", supabase_url=value)
            self.assertFalse(configuration.storage_ready)


class SQLBackedSession:
    """Use the real RPC SQL locally instead of making any network calls."""

    def __init__(self, postgres):
        self.postgres = postgres

    def post(self, url, *, json, **kwargs):
        with self.postgres.connection() as connection:
            connection.execute("SET LOCAL ROLE service_role")
            result = connection.execute(
                "SELECT public.angel_email_backend(%s,%s) AS result",
                (json["p_action"], Jsonb(json["p_data"])),
            ).fetchone()["result"]
        return SimpleNamespace(status_code=200, json=lambda: result)


@unittest.skipUnless(os.environ.get("EMAIL_TEST_DATABASE_URL"), "Requires an isolated PostgreSQL test database")
class HTTPSDatabaseFlowTests(flow.DatabaseFlowTests):
    def setUp(self):
        self.settings = https_settings(flow.settings())
        self.postgres = SubscriptionStore(self.settings)
        self.postgres.initialize()
        with self.postgres.connection() as connection:
            connection.execute("""DO $$ BEGIN
                IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='anon') THEN CREATE ROLE anon NOLOGIN; END IF;
                IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='authenticated') THEN CREATE ROLE authenticated NOLOGIN; END IF;
                IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='service_role') THEN CREATE ROLE service_role NOLOGIN BYPASSRLS; END IF;
                END $$;""")
            connection.execute(RPC_SQL.read_text())
            connection.execute("TRUNCATE angel_email_attempts,angel_email_deliveries,angel_email_subscribers CASCADE")
        self.store = self.make_store(self.settings)

    def make_store(self, configuration):
        return SupabaseSubscriptionStore(configuration, SQLBackedSession(self.postgres))

    def preferences_screen(self, token):
        screen = flow.AppTest.from_file(str(ROOT / "app.py"), default_timeout=15)
        screen.query_params.update({"v": "email", "action": "manage", "token": token})
        screen.run()
        self.assertFalse(screen.exception)
        return screen

    def test_preference_form_persists_changes_and_reload_with_sending_off(self):
        active = self.activate(self.requested())
        token = flow.make_token(self.settings, active, "manage", flow.NOW)
        paused = replace(self.settings, signups_enabled=False, delivery_enabled=False, api_token="")
        with patch("email_ui.email_settings", return_value=paused), \
             patch("email_ui.subscription_store", return_value=self.store), \
             patch("email_subscription.utc_now", return_value=flow.NOW), \
             patch("supabase_email_store.utc_now", return_value=flow.NOW), \
             patch("hostinger_email.HostingerMailer") as mailer:
            screen = self.preferences_screen(token)
            self.assertEqual(self.store.token_subscriber(token, "manage", flow.NOW)["delivery_time"], time(8))
            screen.selectbox[0].select("America/New_York")
            screen.time_input[0].set_value(time(9, 30))
            next(b for b in screen.button if b.label == "Save email preferences").click().run()
            self.assertFalse(screen.exception)
            self.assertIn("Your email preferences have been saved.", [s.value for s in screen.success])
            self.assertNotIn("token", screen.query_params)
            self.assertNotIn("action", screen.query_params)
            reloaded = self.preferences_screen(token)
            self.assertEqual(reloaded.selectbox[0].value, "America/New_York")
            self.assertEqual(reloaded.time_input[0].value, time(9, 30))
            self.assertEqual(self.store.active_subscribers()[0]["status"], "active")
            mailer.assert_not_called()

    def test_preference_form_cannot_reactivate_an_unsubscribed_reader(self):
        active = self.activate(self.requested())
        token = flow.make_token(self.settings, active, "manage", flow.NOW)
        unsubscribe = flow.make_token(self.settings, active, "unsubscribe", flow.NOW)
        self.store.apply_action(unsubscribe, "unsubscribe", now=flow.NOW)
        paused = replace(self.settings, signups_enabled=False, delivery_enabled=False, api_token="")
        with patch("email_ui.email_settings", return_value=paused), \
             patch("email_ui.subscription_store", return_value=self.store), \
             patch("email_subscription.utc_now", return_value=flow.NOW), \
             patch("supabase_email_store.utc_now", return_value=flow.NOW), \
             patch("hostinger_email.HostingerMailer") as mailer:
            screen = self.preferences_screen(token)
            screen.selectbox[0].select("America/New_York")
            screen.time_input[0].set_value(time(9, 30))
            next(b for b in screen.button if b.label == "Save email preferences").click().run()
            self.assertFalse(screen.exception)
            self.assertTrue(screen.error)
            self.assertFalse(screen.success)
            row = self.store.token_subscriber(token, "manage", flow.NOW)
            self.assertEqual(row["status"], "unsubscribed")
            self.assertEqual(row["timezone"], "America/Denver")
            self.assertEqual(row["delivery_time"], time(8))
            self.assertEqual(self.store.active_subscribers(), [])
            mailer.assert_not_called()

    def test_client_cannot_read_or_write_contacts_even_after_accidental_grants(self):
        self.requested()
        with self.postgres.connection() as connection:
            for role in ("anon", "authenticated"):
                self.assertFalse(connection.execute(
                    "SELECT has_function_privilege(%s,'public.angel_email_backend(text,jsonb)','EXECUTE') AS allowed", (role,),
                ).fetchone()["allowed"])
                self.assertFalse(connection.execute(
                    "SELECT has_schema_privilege(%s,'angel_email_private','USAGE') AS allowed", (role,),
                ).fetchone()["allowed"])
                with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                    with connection.transaction():
                        connection.execute(f"SET LOCAL ROLE {role}")
                        connection.execute("SELECT public.angel_email_backend('active_subscribers')")
        # The base test proves RLS still blocks a non-bypass role even if granted.
        original = self.store
        try:
            self.store = self.postgres
            super().test_client_cannot_read_or_write_contacts_even_after_accidental_grants()
        finally:
            self.store = original

    def test_lost_completion_after_provider_acceptance_never_resends(self):
        active = self.activate(self.requested())
        delivery = self.store.reserve(active["id"], "daily:lost-completion", "daily", now=flow.NOW)
        original_post = self.store.session.post

        def interrupted_post(url, *, json, **kwargs):
            if json["p_action"] == "complete":
                raise requests.Timeout()
            return original_post(url, json=json, **kwargs)

        self.store.session.post = interrupted_post
        sender = Mock(return_value=SendResult("sent"))
        with self.assertRaises(SubscriptionError):
            self.store.dispatch(delivery, sender, flow.NOW)
        self.assertIsNone(self.store.reserve(active["id"], "daily:lost-completion", "daily", now=flow.NOW))
        self.assertEqual(self.store.dispatch(delivery, sender, flow.NOW).state, "skipped")
        sender.assert_called_once()
