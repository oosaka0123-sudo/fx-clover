"""Read-only Windows environment check and one local test notification."""

from __future__ import annotations

import json
import platform
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Callable

import pandas as pd

from windows_local_notify_v1_17 import ROOT, SCRIPT_PATH, powershell_sender


OUTPUT = ROOT / "FX_Clover_environment_diagnostic_v1_18.json"
TASK_NAME = "FX_Clover_Live_Monitor_15min"


def scheduled_task_exists() -> bool:
    if platform.system() != "Windows":
        return False
    result = subprocess.run(
        ["schtasks.exe", "/query", "/tn", TASK_NAME],
        check=False, capture_output=True, text=True, timeout=15,
    )
    return result.returncode == 0


def latest_bar(root: Path) -> str:
    path = root / "GBPJPY_ohlc.csv"
    if not path.is_file():
        return ""
    frame = pd.read_csv(path, usecols=["timestamp"])
    return "" if frame.empty else str(frame.iloc[-1]["timestamp"])


def diagnose(
    root: Path = ROOT,
    system_name: str | None = None,
    sender: Callable[[dict], bool] = powershell_sender,
    task_checker: Callable[[], bool] = scheduled_task_exists,
) -> dict:
    system = system_name or platform.system()
    is_windows = system == "Windows"
    test_event = {
        "event": "TEST",
        "message": "ローカル通知の表示テストです。監視通知のみ・注文ではありません。",
    }
    notification_attempted = is_windows
    notification_display_command_succeeded = sender(test_event) if is_windows else False
    result = {
        "schema_version": "1.18",
        "status": (
            "PASS" if is_windows and notification_display_command_succeeded
            else "NOTIFICATION_COMMAND_FAILED" if is_windows
            else "UNSUPPORTED_NON_WINDOWS_TEST_ENVIRONMENT"
        ),
        "operating_system": system,
        "python_version": sys.version.split()[0],
        "powershell_available": bool(shutil.which("powershell.exe")) if is_windows else False,
        "notification_script_exists": SCRIPT_PATH.is_file(),
        "scheduled_task_registered": task_checker() if is_windows else False,
        "ohlc_csv_exists": (root / "GBPJPY_ohlc.csv").is_file(),
        "latest_ohlc_bar": latest_bar(root),
        "notification_attempted": notification_attempted,
        "notification_display_command_succeeded": notification_display_command_succeeded,
        "notification_history_modified": False,
        "external_communication_used": False,
        "orders_enabled": False,
        "note": "PASSはPowerShell表示処理の成功。画面表示は利用者が目視確認する。",
    }
    return result


def run() -> dict:
    result = diagnose()
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    run()
