import os
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

import pandas as pd

from m5_monitor_v1_23 import build_m5_watch
from mt4_mtf_data_feed_v1_23 import TIMEFRAMES, destination_path, refresh_all, source_path
from research_pipeline_v1_3 import ResearchConfig, attach_h1_proxy, prepare
from system_health_check_v1_23 import REQUIRED_FILES, inspect


CSV = "timestamp,open,high,low,close,tick_volume\n2026-08-18T08:00,200,201,199,200.5,10\n"


class MTFV123Tests(unittest.TestCase):
    def test_refresh_all_writes_all_five_timeframes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            common = root / "common"; common.mkdir()
            now = datetime.now(timezone.utc)
            for tf in TIMEFRAMES:
                path = source_path(common, tf); path.write_text(CSV, encoding="utf-8")
                os.utime(path, (now.timestamp(), now.timestamp()))
            result = refresh_all(common, root, 10, now)
            self.assertEqual(set(result["timeframes"]), set(TIMEFRAMES))
            self.assertTrue(all(destination_path(root, tf).is_file() for tf in TIMEFRAMES))
            self.assertEqual(result["execution_timeframe"], "M5")
            self.assertFalse(result["orders_enabled"])

    def test_m5_candidate_key_is_m5(self):
        timestamps = pd.date_range("2026-08-01", periods=400, freq="5min", tz="UTC")
        close = pd.Series(range(400), dtype=float).rsub(400) + 200
        frame = pd.DataFrame({"timestamp": timestamps, "open": close + .1,
                              "high": close + .2, "low": close - .2, "close": close})
        bars = attach_h1_proxy(prepare(frame), ResearchConfig())
        watch = build_m5_watch(bars)
        if not watch.empty:
            self.assertTrue(watch["candidate_key"].str.contains("\\|M5\\|").all())
            self.assertTrue(watch["timeframe"].eq("M5").all())

    def test_health_check_requires_all_timeframes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); common = root / "common"; common.mkdir()
            for name in REQUIRED_FILES:
                content = "/it /mo 5 RUN_LIVE_CYCLE_v1_23.bat" if name.startswith("INSTALL_") else "safe"
                (root / name).write_text(content, encoding="utf-8")
            now = datetime.now(timezone.utc)
            for tf in TIMEFRAMES[:-1]:
                path = source_path(common, tf); path.write_text(CSV, encoding="utf-8")
                os.utime(path, (now.timestamp(), now.timestamp()))
            result = inspect(common, 10, now, root)
            self.assertEqual(result["status"], "ACTION_REQUIRED")
            self.assertIn("mt4_M5", result["failed_checks"])

    def test_exporter_contains_no_order_functions(self):
        source = (Path(__file__).parent / "FX_Clover_MTF_Exporter_v1_23.mq4").read_text(encoding="utf-8")
        for token in ("OrderSend", "OrderClose", "OrderModify", "OrderDelete"):
            self.assertNotIn(token, source)
        self.assertIn("shift >= 1", source)


if __name__ == "__main__":
    unittest.main()
