"""Supervise Streamlit and the minute-based email checker in one container."""

import signal
import subprocess
import sys
from threading import Event


APP_COMMAND = [
    sys.executable, "-m", "streamlit", "run", "app.py",
    "--server.port=7860", "--server.address=0.0.0.0",
    "--browser.gatherUsageStats=false",
]
WORKER_COMMAND = [sys.executable, "-u", "email_scheduler.py"]


def stop_child(child):
    if child.poll() is None:
        child.terminate()
        try:
            child.wait(timeout=10)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait(timeout=5)


def supervise(stop, popen=subprocess.Popen, emit=print):
    app = popen(APP_COMMAND)
    worker = None
    try:
        worker = popen(WORKER_COMMAND)
        while not stop.wait(1):
            code = app.poll()
            if code is not None:
                return code
            if worker.poll() is not None:
                # Restart a failed worker without disturbing the web session.
                emit("Email scheduler process restarting.", flush=True)
                if stop.wait(5):
                    break
                worker = popen(WORKER_COMMAND)
        return 0
    finally:
        if worker is not None:
            stop_child(worker)
        stop_child(app)


def main():
    stop = Event()
    def shutdown(signum, frame):
        stop.set()
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    return supervise(stop)


if __name__ == "__main__":
    raise SystemExit(main())
