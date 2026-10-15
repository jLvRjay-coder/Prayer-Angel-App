"""Hostinger Mail API transport. No inbox access and no automatic POST retries."""

from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import requests


@dataclass(frozen=True)
class SendResult:
    state: str
    retry_after: int = 0


class MailUnavailable(RuntimeError):
    def __init__(self, message, reason="unavailable"):
        super().__init__(message)
        self.reason = reason


class HostingerMailer:
    API_URL = "https://api.mail.hostinger.com/api/v1"

    def __init__(self, token, mailbox_address="contact@beyondthemessage.org", session=None):
        self.token = token
        self.mailbox_address = mailbox_address
        self.session = session or requests.Session()
        self.mailbox_id = None

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}", "Accept": "application/json", "Content-Type": "application/json"}

    def verify_mailbox(self):
        """Read-only token verification; the From address is set by the mailbox."""
        try:
            response = self.session.get(
                f"{self.API_URL}/me", headers=self._headers(),
                timeout=(5, 20), allow_redirects=False,
            )
            failures = {401: "unauthorized", 403: "forbidden", 429: "rate_limited"}
            if response.status_code == 403:
                content_type = response.headers.get("Content-Type", "")
                if response.headers.get("CF-Mitigated") == "challenge":
                    failures[403] = "forbidden_challenge"
                elif isinstance(content_type, str) and "text/html" in content_type.lower():
                    failures[403] = "forbidden_html"
            if response.status_code in failures:
                raise MailUnavailable("The email service is temporarily unavailable.", failures[response.status_code])
            response.raise_for_status()
            boxes = response.json()["data"]["mailboxes"]
            matches = [b for b in boxes if b["address"].casefold() == self.mailbox_address.casefold()]
            if len(matches) != 1:
                raise MailUnavailable("The configured mailbox is not authorized.", "mailbox_not_authorized")
            self.mailbox_id = matches[0]["resourceId"]
            return True
        except requests.RequestException:
            raise MailUnavailable("The email service is temporarily unavailable.") from None
        except (KeyError, ValueError, TypeError):
            raise MailUnavailable("The email service is temporarily unavailable.", "unrecognized_response") from None

    def send(self, recipient, subject, text, html):
        if not self.mailbox_id:
            self.verify_mailbox()
        # Exactly one subscriber per message. No CC, BCC, or attachments.
        payload = {
            "to": [recipient], "displayName": "Angel Chat | Beyond the Message",
            "subject": subject, "text": text, "html": html,
        }
        try:
            response = self.session.post(
                f"{self.API_URL}/mailboxes/{self.mailbox_id}/send",
                headers=self._headers(), json=payload,
                timeout=(5, 20), allow_redirects=False,
            )
        except requests.RequestException:
            # The provider might have accepted the message before a timeout.
            # Do not retry an ambiguous send without provider-side reconciliation.
            return SendResult("unknown")
        if response.status_code == 204:
            return SendResult("sent")
        if response.status_code == 429:
            raw = response.headers.get("Retry-After", "1800")
            try:
                seconds = int(raw)
            except ValueError:
                try:
                    seconds = int((parsedate_to_datetime(raw) - datetime.now(timezone.utc)).total_seconds())
                except (ValueError, TypeError, OverflowError):
                    seconds = 1800
            return SendResult("deferred", max(60, min(seconds, 86400)))
        if response.status_code in {400, 401, 403, 404, 413, 422}:
            return SendResult("rejected")
        return SendResult("unknown")
