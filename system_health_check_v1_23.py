"""Read-only health check for the five-minute multi-timeframe runtime."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import platform
from pathlib import Path
import subprocess

from mt4_data_feed_v1_10 import assert_source_fresh, read_export
from mt4_mtf_data_feed_v1_23 import ROOT, TIMEFRAMES, default_common_dir, source_path


TASK_NAME = "FX_Clover_Live_Monitor_5min"
REQUIRED_FILES = [
    "FX_Clover_MTF_Exporter_v1_23.mq4", "live_cycle_v1_23.py",
    "m5_monitor_v1_23.py", "mt4_mtf_data_feed_v1_23.py",
    "windows_local_notify_v1_17.py", "RUN_LIVE_CYCLE_v1_23.bat",
    "INSTALL_5MIN_LIVE_TASK_v1_23.bat",
]


def task_status() -> dict:
    if platform.system() != "Windows":
        return {"status": "NOT_CHECKED_NON_WINDOWS", "task_name": TASK_NAME}
    proc = subprocess.run(
        ["schtasks", "/query", "/tn", TASK_NAME, "/fo", "LIST"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return {"status": "PASS" if proc.returncode == 0 else "FAIL",
            "registration": "REGISTERED" if proc.returncode == 0 else "NOT_FOUND",
            "task_name": TASK_NAME, "returncode": proc.returncode}


def inspect(common_dir: Path, max_file_age_minutes: int = 10,
            now_utc: datetime | None = None, root: Path = ROOT) -> dict:
    now = now_utc or datetime.now(timezone.utc)
    checks = {}
    missing = [x for x in REQUIRED_FILES if not (root / x).is_file()]
    checks["required_files"] = {"status": "PASS" if not missing else "FAIL", "missing": missing}
    installer = root / "INSTALL_5MIN_LIVE_TASK_v1_23.bat"
    text = installer.read_text(encoding="utf-8", errors="replace").lower() if installer.is_file() else ""
    wiring = "/it" in text and "/mo 5" in text and "run_live_cycle_v1_23.bat" in text
    checks["task_wiring"] = {"status": "PASS" if wiring else "FAIL"}
    for timeframe in TIMEFRAMES:
        path = source_path(common_dir, timeframe)
        try:
            age = assert_source_fresh(path, max_file_age_minutes, now)
            frame = read_export(path)
            checks[f"mt4_{timeframe}"] = {
                "status": "PASS", "path": str(path), "file_age_minutes": round(age, 3),
                "closed_bars": len(frame),
                "last_closed_bar_server_time": frame.iloc[-1]["timestamp"].isoformat(),
            }
        except Exception as exc:
            checks[f"mt4_{timeframe}"] = {
                "status": "FAIL", "path": str(path),
                "error": f"{type(exc).__name__}: {exc}",
            }
    checks["scheduled_task"] = task_status()
    failed = [name for name, value in checks.items() if value.get("status") == "FAIL"]
    return {
        "schema_version": "1.23", "status": "PASS" if not failed else "ACTION_REQUIRED",
        "checked_at_utc": now.isoformat(), "failed_checks": failed, "checks": checks,
        "execution_timeframe": "M5", "orders_enabled": False,
        "classification": "DESIGN_OPERATIONAL_DIAGNOSTIC_NOT_OFFICIAL_RULE",
    }


def main() -> int:
    result = inspect(default_common_dir())
    (ROOT / "FX_Clover_health_v1_23.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

