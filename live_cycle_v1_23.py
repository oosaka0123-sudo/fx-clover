"""Five-minute M5 execution cycle with multi-timeframe MT4 refresh. No orders."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import traceback

from m5_monitor_v1_23 import run as run_m5_monitor
from mt4_mtf_data_feed_v1_23 import ROOT, default_common_dir, destination_path, refresh_all
from windows_local_notify_v1_17 import run as run_local_notifications


def run(common_dir: Path, destination_root: Path = ROOT,
        max_file_age_minutes: int = 10) -> dict:
    feed = refresh_all(common_dir, destination_root, max_file_age_minutes)
    monitor = run_m5_monitor(destination_path(destination_root, "M5"))
    notifications = run_local_notifications(ROOT)
    return {
        "schema_version": "1.23", "data_feed": feed,
        "m5_monitor": monitor, "local_notifications": notifications,
        "strategy": "POCONICAL_ONLY",
        "execution_timeframe": "M5", "orders_enabled": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--common-dir", type=Path, default=None)
    parser.add_argument("--destination-root", type=Path, default=ROOT)
    parser.add_argument("--max-file-age-minutes", type=int, default=10)
    args = parser.parse_args()
    try:
        print(json.dumps(run(
            args.common_dir or default_common_dir(), args.destination_root,
            args.max_file_age_minutes,
        ), ensure_ascii=False, indent=2))
    except Exception:
        with (ROOT / "live_cycle_errors_v1_23.log").open("a", encoding="utf-8") as log:
            log.write(traceback.format_exc() + "\n")
        raise
