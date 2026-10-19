from dataclasses import replace
from datetime import date, datetime, time, timedelta, timezone
from html.parser import HTMLParser
import re
import unittest

from daily_encouragement import DAILY_MESSAGES, email_preview, email_preview_html
from devotional_design import BRAND_MARK_URL, devotional_markdown
from email_subscription import EmailSettings, render_email


class Document(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.text = []
        self.elements = []
        self.feed(source)

    def handle_data(self, data):
        self.text.append(data)

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))

    @property
    def visible_text(self):
        return " ".join(" ".join(self.text).split())


def configuration():
    return EmailSettings(signing_key="private-local-test-key-at-least-32-characters", postal_address="Example business postal address")


def subscriber():
    now = datetime(2026, 10, 19, 15, tzinfo=timezone.utc)
    return {
        "id": "private-preview", "manage_nonce": "manage-test", "confirmation_nonce": "confirm-test",
        "confirmation_expires": now + timedelta(hours=24), "timezone": "America/Denver", "delivery_time": time(8),
    }


class DevotionalDesignTests(unittest.TestCase):
    def test_every_email_keeps_every_reading_and_devotional_paragraph(self):
        for message in DAILY_MESSAGES:
            with self.subTest(message=message["id"]):
                document = Document(email_preview_html(message))
                for field in ("reading", "devotional", "encouragement", "reflection", "prayer"):
                    for paragraph in message[field].split("\n\n"):
                        self.assertIn(" ".join(paragraph.split()), document.visible_text)
                self.assertIn("Daily Encouragement", document.visible_text)
                self.assertIn("Open Angel Chat in your browser", document.visible_text)
                self.assertIn("Get Angel Chat for Android", document.visible_text)

    def test_emphasis_adds_formatting_without_changing_the_approved_words(self):
        for message in DAILY_MESSAGES:
            with self.subTest(message=message["id"]):
                marked = devotional_markdown(message)
                self.assertEqual(marked.replace("**", ""), message["devotional"])
                for phrase in message["emphasis"]:
                    self.assertIn(phrase, message["devotional"])
                    self.assertIn("**" + phrase + "**", marked)
                self.assertIn(message["devotional"], email_preview(message))

    def test_message_content_remains_readable_when_the_logo_is_blocked(self):
        message = DAILY_MESSAGES[0]
        without_images = re.sub(r"<img\b[^>]*>", "", email_preview_html(message))
        visible = Document(without_images).visible_text
        self.assertIn("BEYOND THE MESSAGE", visible)
        self.assertIn(message["title"], visible)
        self.assertIn(message["reading"].split("\n\n")[-1], visible)
        self.assertIn(message["reflection"], visible)
        self.assertIn(message["prayer"], visible)

    def test_html_escapes_untrusted_message_fields_and_sender_address(self):
        payload = '<script>alert("unsafe")</script><img src=x onerror="unsafe">'
        message = {**DAILY_MESSAGES[0], **{key: payload for key in (
            "title", "reading", "verse", "verse_reference", "reference", "encouragement", "devotional", "reflection", "prayer",
        )}, "emphasis": (payload,)}
        settings = replace(configuration(), postal_address=payload)
        _, _, body = render_email(settings, subscriber(), message)
        document = Document(body)
        self.assertIn(payload, document.visible_text)
        self.assertFalse(any(tag == "script" for tag, _ in document.elements))
        self.assertFalse(any("onerror" in attrs or "onload" in attrs for _, attrs in document.elements))
        images = [attrs for tag, attrs in document.elements if tag == "img"]
        self.assertEqual([image["src"] for image in images], [BRAND_MARK_URL])

    def test_both_email_types_keep_signed_action_links_and_the_business_footer(self):
        for message in (None, DAILY_MESSAGES[0]):
            with self.subTest(confirmation=message is None):
                _, plain, body = render_email(configuration(), subscriber(), message)
                document = Document(body)
                links = [attrs["href"] for tag, attrs in document.elements if tag == "a"]
                self.assertTrue(any("action=manage" in link for link in links))
                self.assertTrue(any("action=unsubscribe" in link for link in links))
                self.assertIn(configuration().postal_address, document.visible_text)
                self.assertIn(configuration().postal_address, plain)
                if message is None:
                    self.assertTrue(any("action=confirm" in link for link in links))

    def test_calendar_appends_connected_series_after_original_ninety_one_days(self):
        dates = [date.fromisoformat(message["date"]) for message in DAILY_MESSAGES]
        self.assertEqual(dates, [date(2026, 10, 17) + timedelta(days=index) for index in range(139)])
        self.assertTrue(all(message["approved_for_delivery"] is True for message in DAILY_MESSAGES))
        self.assertEqual(DAILY_MESSAGES[0]["id"], "compass-w01-god-sends")
        self.assertEqual(DAILY_MESSAGES[6]["id"], "angel-w01-rest")
        self.assertEqual(DAILY_MESSAGES[90]["date"], "2027-01-15")
        self.assertEqual(DAILY_MESSAGES[91]["date"], "2027-01-16")
        self.assertEqual(DAILY_MESSAGES[-1]["date"], "2027-03-04")
        self.assertEqual(DAILY_MESSAGES[91]["previous_message_id"], DAILY_MESSAGES[90]["id"])


if __name__ == "__main__":
    unittest.main()

