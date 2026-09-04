from pathlib import Path
import tempfile
import unittest

import pandas as pd

from windows_local_notify_v1_17 import collect_events, notify_new_events


ROOT = Path(__file__).resolve().parent


class V123WiringNotificationTests(unittest.TestCase):
    def test_five_minute_task_wiring(self):
        text = (ROOT / "INSTALL_5MIN_LIVE_TASK_v1_23.bat").read_text(
            encoding="utf-8", errors="replace").lower()
        self.assertIn("/mo 5", text)
        self.assertIn("/it", text)
        self.assertIn("run_live_cycle_v1_23.bat", text)
        self.assertIn("fx_clover_live_monitor_15min", text)
        self.assertIn("/disable", text)

    def test_run_bat_calls_v123_live_cycle(self):
        text = (ROOT / "RUN_LIVE_CYCLE_v1_23.bat").read_text(
            encoding="utf-8", errors="replace").lower()
        self.assertIn("python live_cycle_v1_23.py", text)

    def test_m5_watch_is_collected_and_baselined(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            pd.DataFrame([{
                "candidate_key": "GBPJPY|M5|2026-08-18T09:00:00+00:00",
                "symbol": "GBPJPY", "timeframe": "M5",
                "timestamp": "2026-08-18T09:00:00+00:00", "state": "WATCH",
                "notification_event": "WATCH_REVIEW_REQUIRED",
            }]).to_csv(root / "GBPJPY_M5_notification_queue_v1_23.csv", index=False)
            events = collect_events(root)
            self.assertEqual(len(events), 1)
            self.assertIn("M5", events.iloc[0]["message"])
            sent = []
            result = notify_new_events(
                events, root / "state.json", sender=lambda event: sent.append(event) or True)
            self.assertEqual(result["baseline_watch_keys"], 1)
            self.assertEqual(sent, [])


if __name__ == "__main__":
    unittest.main()
