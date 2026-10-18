"""Collect Mail API HTTP metadata with curl; never print tokens or response bodies."""

import os
from pathlib import Path
import re
import subprocess
import tempfile


URL = "https://api.mail.hostinger.com/api/v1/me"
HEADER_NAMES = {
    "content-type", "server", "via", "x-cache", "x-cache-status", "cf-ray",
    "cf-mitigated", "x-request-id", "x-correlation-id", "x-trace-id",
    "x-mitmproxy-blocked-reason", "proxy-status", "x-squid-error",
}
PROXY_NAMES = ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy", "ALL_PROXY", "all_proxy")


def probe(token, environ=None, run=None):
    environ = os.environ if environ is None else environ
    run = subprocess.run if run is None else run
    present = bool(token.strip())
    bare = bool(
        present and token.isascii() and not any(c.isspace() for c in token)
        and not token.lower().startswith("bearer ")
        and not token.startswith(("'", '"')) and not token.endswith(("'", '"'))
    )
    print(f"Hostinger secret present: {'yes' if present else 'no'}")
    print(f"Hostinger secret is a bare token without whitespace or surrounding quotes: {'yes' if bare else 'no'}")
    proxies = [name for name in PROXY_NAMES if environ.get(name)]
    print("Runner proxy variables configured: " + (", ".join(proxies) or "none"))
    if not bare:
        print("No HTTP request made. Check the saved HOSTINGER_MAIL_API_TOKEN value.")
        return 1

    # Keep Authorization out of argv and logs. Curl reads it from stdin, with
    # config escaping; no shell is involved and redirects are never followed.
    escaped = token.replace("\\", "\\\\").replace('"', '\\"')
    config = (
        f'url = "{URL}"\nrequest = "GET"\n'
        'header = "Accept: application/json"\n'
        'header = "Content-Type: application/json"\n'
        f'header = "Authorization: Bearer {escaped}"\n'
    )
    with tempfile.TemporaryDirectory(prefix="angel-mail-probe-") as directory:
        headers = Path(directory) / "headers.txt"
        try:
            result = run([
                "curl", "--config", "-", "--silent", "--show-error",
                "--connect-timeout", "5", "--max-time", "25", "--proto", "=https",
                "--max-redirs", "0", "--dump-header", str(headers),
                "--output", os.devnull, "--write-out", "%{http_code}",
            ], input=config, text=True, capture_output=True, timeout=35, check=False)
        except (OSError, subprocess.TimeoutExpired):
            print("Curl transport check could not complete; private error text omitted.")
            return 1
        status = result.stdout.strip()
        print("Curl HTTP status: " + (status if re.fullmatch(r"[1-5][0-9]{2}|000", status) else "unavailable"))
        if headers.exists():
            for line in headers.read_text(errors="replace")[:32768].splitlines():
                name, separator, value = line.partition(":")
                name = name.strip().lower()
                if separator and name in HEADER_NAMES:
                    value = value.strip().replace(token, "[redacted]")
                    value = re.sub(r"(?i)Bearer\s+\S+", "Bearer [redacted]", value)
                    value = "".join(c for c in value if 32 <= ord(c) <= 126)[:180]
                    print(f"Response header {name}: {value}")
                elif separator and name == "location":
                    print("Response redirect location present: yes (not followed)")
        print("Response body discarded. No email sent.")
        if result.returncode:
            print("Curl transport reported an error; private error text omitted.")
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(probe(os.environ.get("HOSTINGER_MAIL_API_TOKEN", "")))
