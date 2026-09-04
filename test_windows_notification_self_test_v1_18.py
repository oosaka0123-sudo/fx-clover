import tempfile
import unittest
from pathlib import Path

import pandas as pd

from windows_notification_self_test_v1_18 import diagnose


class WindowsNotificationSelfTestTests(unittest.TestCase):
    def test_windows_success_reports_pass_without_history_write(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pd.DataFrame({"timestamp": ["2026-08-18 10:00:00"]}).to_csv(
                root / "GBPJPY_ohlc.csv", index=False
            )
            result = diagnose(
                root, system_name="Windows", sender=lambda _: True,
                task_checker=lambda: True,
            )
            self.assertEqual(result["status"], "PASS")
            self.assertTrue(result["scheduled_task_registered"])
            self.assertFalse(result["notification_history_modified"])
            self.assertFalse(result["orders_enabled"])

    def test_windows_sender_failure_is_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            result = diagnose(
                Path(directory), system_name="Windows", sender=lambda _: False,
                task_checker=lambda: False,
            )
            self.assertEqual(result["status"], "NOTIFICATION_COMMAND_FAILED")
            self.assertFalse(result["notification_display_command_succeeded"])

    def test_non_windows_does_not_attempt_notification(self):
        called = []
        with tempfile.TemporaryDirectory() as directory:
            result = diagnose(
                Path(directory), system_name="Linux",
                sender=lambda _: called.append(True) or True,
            )
            self.assertEqual(result["status"], "UNSUPPORTED_NON_WINDOWS_TEST_ENVIRONMENT")
            self.assertFalse(result["notification_attempted"])
            self.assertEqual(called, [])


if __name__ == "__main__":
    unittest.main()
