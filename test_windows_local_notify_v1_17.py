import tempfile
import unittest
from pathlib import Path

import pandas as pd

from windows_local_notify_v1_17 import notify_new_events


def events(rows):
    return pd.DataFrame(rows, columns=["event_key", "event", "candidate_key", "time", "message"])


class WindowsLocalNotifyTests(unittest.TestCase):
    def test_first_run_baselines_watch_without_flood(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            seen = []
            result = notify_new_events(events([
                ["WATCH|k1", "WATCH", "k1", "t1", "m1"],
                ["WATCH|k2", "WATCH", "k2", "t2", "m2"],
            ]), path, lambda item: seen.append(item) or True)
            self.assertEqual(result["baseline_watch_keys"], 2)
            self.assertEqual(result["notifications_sent"], 0)
            self.assertEqual(seen, [])

    def test_new_watch_is_delivered_once(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            notify_new_events(events([["WATCH|k1", "WATCH", "k1", "t1", "m1"]]), path, lambda _: True)
            sent = []
            batch = events([
                ["WATCH|k1", "WATCH", "k1", "t1", "m1"],
                ["WATCH|k2", "WATCH", "k2", "t2", "m2"],
            ])
            first = notify_new_events(batch, path, lambda item: sent.append(item["event_key"]) or True)
            second = notify_new_events(batch, path, lambda _: True)
            self.assertEqual(first["notifications_sent"], 1)
            self.assertEqual(sent, ["WATCH|k2"])
            self.assertEqual(second["fresh_events"], 0)

    def test_failed_delivery_is_retried(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            notify_new_events(events([]), path, lambda _: True)
            trigger = events([["TRIGGER|k1|t", "TRIGGER", "k1", "t", "m"]])
            failed = notify_new_events(trigger, path, lambda _: False)
            retried = notify_new_events(events([]), path, lambda _: True)
            self.assertEqual(failed["status"], "DELIVERY_FAILED_WILL_RETRY")
            self.assertEqual(retried["notifications_sent"], 1)

    def test_trigger_is_not_suppressed_on_first_run(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            result = notify_new_events(events([
                ["WATCH|k1", "WATCH", "k1", "t1", "m1"],
                ["TRIGGER|k1|t2", "TRIGGER", "k1", "t2", "m2"],
            ]), path, lambda _: True)
            self.assertEqual(result["baseline_watch_keys"], 1)
            self.assertEqual(result["notifications_sent"], 1)


if __name__ == "__main__":
    unittest.main()
