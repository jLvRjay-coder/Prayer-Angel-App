import contextlib
import io
from pathlib import Path
import subprocess
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from email_http_probe import URL, probe


class HttpProbeTests(unittest.TestCase):
    def test_empty_or_malformed_secret_never_makes_a_request(self):
        for token in ["", "   ", "Bearer private-key", "private-key\n", '"private-key"']:
            with self.subTest(token_kind=repr(token[:1])):
                run = Mock()
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(probe(token, {}, run), 1)
                run.assert_not_called()

    def test_only_safe_metadata_is_printed_and_token_stays_out_of_argv(self):
        token = "123|private-test-token"

        def run(argv, **kwargs):
            self.assertNotIn(token, " ".join(argv))
            self.assertIn(f'url = "{URL}"', kwargs["input"])
            self.assertIn('request = "GET"', kwargs["input"])
            self.assertIn(f'Authorization: Bearer {token}', kwargs["input"])
            self.assertNotIn("--location", argv)
            self.assertEqual(argv[argv.index("--output") + 1], "/dev/null")
            Path(argv[argv.index("--dump-header") + 1]).write_text(
                "HTTP/1.1 403 Forbidden\r\nContent-Type: text/html\r\n"
                "Server: example-edge\r\nX-Mitmproxy-Blocked-Reason: DENIED\r\n"
                f"X-Request-Id: {token}\r\nSet-Cookie: private-cookie\r\n"
            )
            return SimpleNamespace(stdout="403", stderr=token, returncode=0)

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(probe(token, {"HTTPS_PROXY": "private-proxy-value"}, run), 0)
        text = output.getvalue()
        self.assertIn("Hostinger secret present: yes", text)
        self.assertIn("Curl HTTP status: 403", text)
        self.assertIn("x-mitmproxy-blocked-reason: DENIED", text)
        for private in [token, "private-cookie", "private-proxy-value"]:
            self.assertNotIn(private, text)

    def test_provider_header_cannot_inject_a_bearer_value_into_logs(self):
        token = "private-test-token"

        def run(argv, **kwargs):
            Path(argv[argv.index("--dump-header") + 1]).write_text(
                "HTTP/1.1 403 Forbidden\nVia: Bearer another-private-value\n"
            )
            return SimpleNamespace(stdout="403", stderr="", returncode=0)

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(probe(token, {}, run), 0)
        self.assertNotIn("another-private-value", output.getvalue())

    def test_curl_failure_does_not_print_stderr(self):
        token = "private-test-token"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = probe(token, {}, Mock(return_value=SimpleNamespace(stdout="000", stderr=token, returncode=7)))
        self.assertEqual(result, 1)
        self.assertNotIn(token, output.getvalue())

    def test_timeout_does_not_print_exception_details(self):
        token = "private-test-token"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = probe(token, {}, Mock(side_effect=subprocess.TimeoutExpired(token, 35)))
        self.assertEqual(result, 1)
        self.assertNotIn(token, output.getvalue())


if __name__ == "__main__":
    unittest.main()
