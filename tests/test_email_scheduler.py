from datetime import datetime, timezone
import json
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from email_scheduler import run_scheduler, safe_counts, check_due, record_health
from app_runtime import supervise, APP_COMMAND


class ClockStop:
    def __init__(self, epoch, ticks):
        self.epoch = epoch
        self.ticks = ticks
        self.waits = []
    def is_set(self):
        return self.ticks <= 0
    def wait(self, seconds):
        self.waits.append(seconds)
        self.epoch += seconds
        self.ticks -= 1
        return self.is_set()


class SchedulerTests(unittest.TestCase):
    def test_next_check_crosses_five_am_without_an_hourly_queue(self):
        epoch = datetime(2026, 10, 20, 10, 59, 50, tzinfo=timezone.utc).timestamp()
        stop = ClockStop(epoch, 3)
        checked = []
        def check():
            checked.append(datetime.fromtimestamp(stop.epoch, timezone.utc))
            return None, "ok", {"not_due": 2}
        run_scheduler(stop, check=check, record=lambda *args: True, clock=lambda: stop.epoch, emit=Mock())
        self.assertEqual(checked[0].hour, 10)
        self.assertEqual((checked[1].hour, checked[1].minute), (11, 0))
        self.assertLess(checked[1].second, 2)
        self.assertTrue(all(0 < seconds <= 60.05 for seconds in stop.waits))

    def test_failed_check_is_sanitized_and_next_minute_still_runs(self):
        stop = ClockStop(0, 2)
        check = Mock(side_effect=[RuntimeError("private-token reader@example.com"), (None, "ok", {"already_handled": 2})])
        output = []
        run_scheduler(stop, check=check, record=lambda *args: True, clock=lambda: stop.epoch,
                      emit=lambda text, **kwargs: output.append(text))
        self.assertEqual(check.call_count, 2)
        self.assertEqual(json.loads(output[0])["email_scheduler"], "failed")
        self.assertEqual(json.loads(output[1])["outcomes"], {"already_handled": 2})
        self.assertNotIn("private-token", " ".join(output))
        self.assertNotIn("reader@example.com", " ".join(output))

    def test_health_failure_does_not_stop_the_delivery_checker(self):
        stop = ClockStop(0, 2)
        check = Mock(return_value=(None, "ok", {"already_handled": 1}))
        run_scheduler(stop, check=check, record=Mock(side_effect=RuntimeError("unavailable")),
                      clock=lambda: stop.epoch, emit=Mock())
        self.assertEqual(check.call_count, 2)

    def test_only_fixed_nonnegative_counters_can_leave_the_worker(self):
        self.assertEqual(safe_counts({"sent": 1, "email": "private@example.com", "unknown": -1, "not_due": True}), {"sent": 1})

    def test_delivery_switch_is_respected_before_calling_the_worker(self):
        settings = SimpleNamespace(delivery_enabled=False)
        worker = Mock()
        with patch.dict("sys.modules", {"email_subscription": SimpleNamespace(EmailSettings=SimpleNamespace(from_env=lambda: settings)),
                                       "email_worker": SimpleNamespace(run_worker=worker)}):
            self.assertEqual(check_due()[1:], ("disabled", {"disabled": 1}))
        worker.assert_not_called()

    def test_heartbeat_is_backend_only_and_excludes_private_values(self):
        settings = SimpleNamespace(https_database_ready=True,
                                   supabase_url="https://example.supabase.co",
                                   supabase_secret_key="private-backend-key")
        post = Mock(return_value=SimpleNamespace(status_code=204))
        fake_requests = SimpleNamespace(post=post, RequestException=RuntimeError)
        with patch.dict("sys.modules", {"requests": fake_requests}):
            self.assertTrue(record_health(settings, "ok", {"sent": 1, "email": "private@example.com"}))
        args = post.call_args
        self.assertEqual(args.args[0], "https://example.supabase.co/rest/v1/rpc/angel_email_scheduler_heartbeat")
        self.assertFalse(args.kwargs["allow_redirects"])
        self.assertEqual(args.kwargs["json"]["p_counters"], {"sent": 1})
        self.assertNotIn("private-backend-key", json.dumps(args.kwargs["json"]))


class RuntimeTests(unittest.TestCase):
    def test_failed_worker_restarts_without_restarting_streamlit(self):
        stop = ClockStop(0, 5)
        app = Mock(); app.poll.return_value = None
        failed = Mock(); failed.poll.return_value = 1
        replacement = Mock(); replacement.poll.return_value = None
        spawn = Mock(side_effect=[app, failed, replacement])
        self.assertEqual(supervise(stop, popen=spawn, emit=Mock()), 0)
        self.assertEqual(spawn.call_count, 3)
        self.assertEqual(spawn.call_args_list[0].args[0], APP_COMMAND)
        replacement.terminate.assert_called_once()
        app.terminate.assert_called_once()

    def test_shutdown_terminates_both_processes(self):
        stop = ClockStop(0, 1)
        app = Mock(); app.poll.return_value = None
        worker = Mock(); worker.poll.return_value = None
        supervise(stop, popen=Mock(side_effect=[app, worker]))
        app.terminate.assert_called_once()
        worker.terminate.assert_called_once()


if __name__ == "__main__":
    unittest.main()
