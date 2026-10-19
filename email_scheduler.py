"""Check the existing consented sender every minute in the app container.

No new send path is introduced. The existing worker owns local-time selection,
daily reservations, unsubscribe checks, budgets, and uncertain-send handling.
Only fixed outcome counters are logged or included in the health record.
"""

import json
from pathlib import Path
import signal
from threading import Event
import time


COUNTERS = frozenset({
    "sent", "already_handled", "not_due", "disabled", "budget_full",
    "unknown", "rejected", "deferred", "cancelled",
})


def safe_counts(values):
    return {key: value for key, value in values.items()
            if key in COUNTERS and type(value) is int and value >= 0}


def seconds_to_next_minute(now):
    # Align to the clock, rather than adding the worker's runtime to every tick.
    return 60 - (now % 60) + 0.05


def check_due():
    from email_subscription import EmailSettings
    from email_worker import run_worker

    settings = EmailSettings.from_env()
    if not settings.delivery_enabled:
        return settings, "disabled", {"disabled": 1}
    if not settings.ready:
        return settings, "not_configured", {}
    try:
        counts = safe_counts(run_worker(settings))
    except Exception:
        # Provider errors can contain private addresses or authorization headers.
        return settings, "failed", {}
    state = "failed" if any(counts.get(key) for key in (
        "budget_full", "unknown", "rejected", "deferred",
    )) else "ok"
    return settings, state, counts


def record_health(settings, state, counts):
    if not settings or not settings.https_database_ready:
        return False
    import requests

    try:
        metadata = json.loads(Path(__file__).with_name("deployment.json").read_text())
        source = metadata.get("source_commit", "")
        if len(source) != 40 or any(ch not in "0123456789abcdef" for ch in source):
            source = ""
    except (OSError, ValueError, TypeError):
        source = ""
    try:
        response = requests.post(
            settings.supabase_url.rstrip("/") + "/rest/v1/rpc/angel_email_scheduler_heartbeat",
            headers={"apikey": settings.supabase_secret_key, "Content-Type": "application/json"},
            json={"p_state": state, "p_counters": safe_counts(counts), "p_source": source},
            timeout=(3, 5), allow_redirects=False,
        )
        return response.status_code in (200, 204)
    except requests.RequestException:
        return False


def run_scheduler(stop, check=check_due, record=record_health, clock=time.time, emit=print):
    while not stop.is_set():
        try:
            settings, state, counts = check()
        except Exception:
            settings, state, counts = None, "failed", {}
        counts = safe_counts(counts)
        try:
            recorded = record(settings, state, counts)
        except Exception:
            recorded = False
        emit(json.dumps({"email_scheduler": state, "health_recorded": bool(recorded), "outcomes": counts}), flush=True)
        if stop.wait(seconds_to_next_minute(clock())):
            break


def main():
    stop = Event()
    def shutdown(signum, frame):
        stop.set()
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    run_scheduler(stop)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
