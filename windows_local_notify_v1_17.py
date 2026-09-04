"""Windows desktop notifications for FX-Clover monitoring events.

Local display only. No network, broker, or order execution is present.
"""

from __future__ import annotations

import json
import platform
from pathlib import Path
import subprocess
from typing import Callable

import pandas as pd

from watch_monitor_v1_4 import evaluate_manual_queue


ROOT = Path(__file__).resolve().parent
STATE_PATH = ROOT / "local_notification_state_v1_17.json"
SCRIPT_PATH = ROOT / "SHOW_FX_CLOVER_NOTIFICATION_v1_17.ps1"


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, keep_default_na=False, dtype=str) if path.is_file() else pd.DataFrame()


def collect_events(root: Path = ROOT) -> pd.DataFrame:
    rows: list[dict] = []
    watch = _read_csv(root / "GBPJPY_notification_queue_v1_4.csv")
    for item in watch.itertuples(index=False):
        if str(item.notification_event) == "WATCH_REVIEW_REQUIRED":
            rows.append({
                "event_key": f"WATCH|{item.candidate_key}",
                "event": "WATCH", "candidate_key": item.candidate_key,
                "time": item.timestamp,
                "message": f"GBPJPY M15 WATCH候補\n{item.timestamp}",
            })

    manual_path = root / "GBPJPY_manual_review_queue_v1_5.csv"
    if manual_path.is_file():
        manual = evaluate_manual_queue(_read_csv(manual_path))
        ready = manual[manual["notification_event"].eq("READY_FOR_TRIGGER_REVIEW")]
        for item in ready.itertuples(index=False):
            rows.append({
                "event_key": f"READY|{item.candidate_key}",
                "event": "READY", "candidate_key": item.candidate_key,
                "time": item.timestamp,
                "message": f"GBPJPY M15 READY（手動確認済み）\n{item.timestamp}",
            })

    triggers = _read_csv(root / "GBPJPY_local_alerts_v1_5.csv")
    for item in triggers.itertuples(index=False):
        rows.append({
            "event_key": f"{item.event}|{item.candidate_key}|{item.evaluation_bar_time}",
            "event": item.event, "candidate_key": item.candidate_key,
            "time": item.evaluation_bar_time,
            "message": (
                f"GBPJPY M15 {item.event}\n{item.evaluation_bar_time}\n"
                f"参考価格: {item.entry_reference_price}\n監視通知のみ・注文ではありません"
            ),
        })

    # v1.23 M5 execution-timeframe path. Kept separate from historical M15 files.
    m5_watch = _read_csv(root / "GBPJPY_M5_notification_queue_v1_23.csv")
    for item in m5_watch.itertuples(index=False):
        if str(item.notification_event) == "WATCH_REVIEW_REQUIRED":
            rows.append({
                "event_key": f"M5_WATCH|{item.candidate_key}",
                "event": "WATCH", "candidate_key": item.candidate_key,
                "time": item.timestamp,
                "message": f"GBPJPY M5 WATCH候補\n{item.timestamp}",
            })

    m5_manual = _read_csv(root / "GBPJPY_M5_manual_review_queue_v1_23.csv")
    if not m5_manual.empty:
        m5_ready = evaluate_manual_queue(m5_manual)
        m5_ready = m5_ready[m5_ready["notification_event"].eq("READY_FOR_TRIGGER_REVIEW")]
        for item in m5_ready.itertuples(index=False):
            rows.append({
                "event_key": f"M5_READY|{item.candidate_key}",
                "event": "READY", "candidate_key": item.candidate_key,
                "time": item.timestamp,
                "message": f"GBPJPY M5 READY（手動確認済み）\n{item.timestamp}",
            })

    m5_triggers = _read_csv(root / "GBPJPY_M5_local_alerts_v1_23.csv")
    for item in m5_triggers.itertuples(index=False):
        rows.append({
            "event_key": f"M5_{item.event}|{item.candidate_key}|{item.evaluation_bar_time}",
            "event": item.event, "candidate_key": item.candidate_key,
            "time": item.evaluation_bar_time,
            "message": (
                f"GBPJPY M5 {item.event}\n{item.evaluation_bar_time}\n"
                f"参考価格: {item.entry_reference_price}\n監視通知のみ・注文ではありません"
            ),
        })
    return pd.DataFrame(rows, columns=["event_key", "event", "candidate_key", "time", "message"])


def load_state(path: Path = STATE_PATH) -> dict:
    if not path.is_file():
        return {"initialized": False, "delivered_event_keys": [],
                "pending_events": [], "orders_enabled": False}
    data = json.loads(path.read_text(encoding="utf-8"))
    data.setdefault("initialized", True)
    data.setdefault("delivered_event_keys", [])
    data.setdefault("pending_events", [])
    data["orders_enabled"] = False
    return data


def save_state(state: dict, path: Path = STATE_PATH) -> None:
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def powershell_sender(event: dict) -> bool:
    if platform.system() != "Windows":
        return False
    result = subprocess.run(
        [
            "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-File", str(SCRIPT_PATH), "-Title", f"FX-Clover {event['event']}",
            "-Message", event["message"],
        ],
        check=False, capture_output=True, text=True, timeout=20,
    )
    return result.returncode == 0


def notify_new_events(
    events: pd.DataFrame,
    state_path: Path = STATE_PATH,
    sender: Callable[[dict], bool] = powershell_sender,
) -> dict:
    state = load_state(state_path)
    delivered = set(map(str, state["delivered_event_keys"]))
    pending = pd.DataFrame(state["pending_events"], columns=events.columns)
    candidates = pd.concat([pending, events], ignore_index=True).drop_duplicates(
        "event_key", keep="last"
    )
    baseline = 0
    if not state["initialized"]:
        # Avoid showing up to 30 historical WATCH balloons on first install.
        watch_keys = set(events.loc[events["event"].eq("WATCH"), "event_key"].astype(str))
        delivered.update(watch_keys)
        baseline = len(watch_keys)
        state["initialized"] = True

    fresh = candidates[~candidates["event_key"].astype(str).isin(delivered)]
    sent = 0
    failed = 0
    retry_queue: list[dict] = []
    for item in fresh.to_dict("records"):
        if sender(item):
            delivered.add(str(item["event_key"]))
            sent += 1
        else:
            failed += 1
            retry_queue.append(item)
    state["delivered_event_keys"] = sorted(delivered)
    state["pending_events"] = retry_queue
    state["orders_enabled"] = False
    save_state(state, state_path)
    return {
        "status": "COMPLETED" if failed == 0 else "DELIVERY_FAILED_WILL_RETRY",
        "events_seen": len(events), "pending_before_attempt": len(pending),
        "pending_after_attempt": len(retry_queue), "baseline_watch_keys": baseline,
        "fresh_events": len(fresh), "notifications_sent": sent,
        "notifications_failed": failed, "orders_enabled": False,
    }


def run(root: Path = ROOT) -> dict:
    return notify_new_events(collect_events(root))


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
