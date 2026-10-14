import json
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from datetime import date, datetime, timezone
from urllib.parse import parse_qs, urlparse

from streamlit.testing.v1 import AppTest
from daily_encouragement import (
    DAILY_MESSAGES, default_message, local_today, message_by_key, message_url,
)


ROOT = Path(__file__).resolve().parents[1]


class ContentTests(unittest.TestCase):
    def test_catalog_has_a_unique_reference_and_date_for_every_message(self):
        self.assertEqual(len({m["id"] for m in DAILY_MESSAGES}), 7)
        self.assertEqual(len({m["date"] for m in DAILY_MESSAGES}), 7)
        for message in DAILY_MESSAGES:
            self.assertTrue(message["reference"])
            self.assertTrue(message["verse_reference"])
            self.assertTrue(message["context"])
            self.assertFalse(message["approved_for_delivery"])
            self.assertEqual(message_by_key(message["id"]), message_by_key(message["date"]))

    def test_invalid_message_does_not_resolve_to_another_teaching(self):
        self.assertIsNone(message_by_key("not-a-real-message"))
        self.assertIsNone(message_by_key("../../private"))

    def test_calendar_uses_denver_day_at_utc_midnight(self):
        self.assertEqual(local_today(datetime(2026, 10, 14, 2, tzinfo=timezone.utc)), date(2026, 10, 13))
        self.assertEqual(local_today(datetime(2026, 10, 14, 8, tzinfo=timezone.utc)), date(2026, 10, 14))
        self.assertEqual(default_message(date(2026, 10, 14))["id"], DAILY_MESSAGES[0]["id"])

    def test_calendar_does_not_loop_after_preview_ends(self):
        self.assertEqual(default_message(date(2026, 12, 1))["date"], "2026-10-20")

    def test_share_link_has_only_public_message_information(self):
        query = parse_qs(urlparse(message_url(DAILY_MESSAGES[2])).query)
        self.assertEqual(query, {"v": ["daily"], "message": [DAILY_MESSAGES[2]["id"]]})


class AppFlowTests(unittest.TestCase):
    def setUp(self):
        self.previous_cwd = Path.cwd()
        os.chdir(ROOT)
        self.at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=15)

    def tearDown(self):
        sid = self.at.query_params.get("sid", "")
        if sid:
            (ROOT / ".btm_sessions" / f"{sid}.json").unlink(missing_ok=True)
        os.chdir(self.previous_cwd)

    def run_daily(self, message_id="compass-w01-words"):
        self.at.query_params.update({"v": "daily", "message": message_id})
        self.at.run()
        self.assertFalse(self.at.exception)
        return self.at

    def test_home_entry_and_back_navigation(self):
        self.at.run()
        self.at.button(key="home_open_daily").click().run()
        self.assertFalse(self.at.exception)
        self.assertEqual(self.at.session_state["view"], "daily")
        self.at.button(key="daily_back_home").click().run()
        self.assertEqual(self.at.session_state["view"], "home")
        self.assertNotIn("message", self.at.query_params)

    def test_deep_link_and_switching_teachings(self):
        at = self.run_daily()
        self.assertEqual(at.subheader[0].value, "When the Words Feel Difficult")
        at.selectbox[0].select("angel-w01-rest").run()
        self.assertFalse(at.exception)
        self.assertEqual(at.query_params["message"], "angel-w01-rest")
        self.assertEqual(at.subheader[0].value, "Make Room to Be Still")

    def test_unknown_deep_link_has_recovery(self):
        at = self.run_daily("invalid-id")
        self.assertEqual(at.error[0].value, "This message link could not be found.")
        self.assertEqual(len(at.subheader), 0)
        at.button(key="daily_invalid_link").click().run()
        self.assertFalse(at.exception)
        self.assertEqual(at.subheader[1].value, "Go deeper with Angel Chat")

    def test_followup_is_editable_and_does_not_send_automatically(self):
        with patch("openai.OpenAI") as api:
            at = self.run_daily()
            at.button(key="daily_question_compass-w01-words_0").click().run()
            self.assertFalse(at.exception)
            self.assertEqual(at.query_params["v"], "angel")
            self.assertEqual(at.chat_input[0].value, "Help me understand Exodus 4:10-12 in its original context.")
            self.assertEqual(at.session_state["chat"], [])
            api.return_value.chat.completions.create.assert_not_called()
            at.button(key="angel_back_daily").click().run()
            self.assertEqual(at.subheader[0].value, "When the Words Feel Difficult")

    def test_submitted_question_has_teaching_context_and_reset_clears_it(self):
        response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="A local test response."))])
        with patch.dict(os.environ, {"OPENAI_API_KEY": "local-test-key"}), patch("openai.OpenAI") as api:
            api.return_value.chat.completions.create.return_value = response
            at = self.run_daily()
            at.button(key="daily_question_compass-w01-words_0").click().run()
            at.chat_input[0].set_value("How does listening fit this passage?").run()
            self.assertFalse(at.exception)
            api.return_value.chat.completions.create.assert_called_once()
            system = api.return_value.chat.completions.create.call_args.kwargs["messages"][0]["content"]
            self.assertIn("When the Words Feel Difficult", system)
            self.assertIn("Exodus 4:10-12", system)
            self.assertIn("James 1:19", system)
            self.assertNotIn("Make Room to Be Still", system)
            at.button(key="angel_new_chat").click().run()
            self.assertFalse(at.exception)
            self.assertEqual(at.session_state["chat"], [])
            self.assertNotIn("message", at.query_params)
            self.assertNotIn("daily_chat_message_id", at.session_state)
            saved = json.loads((ROOT / ".btm_sessions" / f"{at.query_params['sid']}.json").read_text())
            self.assertEqual(saved["chat"], [])
            self.assertEqual(saved["burden"], "")

    def test_existing_routes_render(self):
        for view in ("home", "angel", "about", "bible", "steps"):
            self.at.query_params["v"] = view
            self.at.run()
            self.assertFalse(self.at.exception, view)


if __name__ == "__main__":
    unittest.main()
