"""M5 execution-timeframe WATCH/READY/TRIGGER monitoring. No order execution."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

from auto_cycle_v1_9 import merge_reviews
from research_pipeline_v1_3 import ResearchConfig, attach_h1_proxy, prepare
from trigger_review_v1_9 import evaluate_triggers, fresh_events, load_sent, save_sent
from watch_monitor_v1_4 import MANUAL_COLUMNS, candidate_key, evaluate_manual_queue, make_manual_queue


ROOT = Path(__file__).resolve().parent
WATCH_PATH = ROOT / "GBPJPY_M5_watch_candidates_v1_23.csv"
REVIEW_PATH = ROOT / "GBPJPY_M5_manual_review_queue_v1_23.csv"
NOTIFICATION_PATH = ROOT / "GBPJPY_M5_notification_queue_v1_23.csv"
EVALUATION_PATH = ROOT / "GBPJPY_M5_trigger_evaluations_v1_23.csv"
ALERT_PATH = ROOT / "GBPJPY_M5_local_alerts_v1_23.csv"
SENT_PATH = ROOT / "GBPJPY_M5_sent_alert_state_v1_23.json"
STATE_PATH = ROOT / "GBPJPY_M5_monitor_state_v1_23.json"


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_m5_watch(bars: pd.DataFrame, symbol: str = "GBPJPY") -> pd.DataFrame:
    mask = bars["bearish"] & bars["new_below_dma3x3"] & bars["h1_watch_proxy"]
    columns = ["timestamp", "open", "high", "low", "close", "dma3x3", "dma25x5"]
    out = bars.loc[mask, columns].copy()
    out.insert(0, "candidate_key", [candidate_key(symbol, "M5", x) for x in out.timestamp])
    out.insert(1, "symbol", symbol)
    out.insert(2, "timeframe", "M5")
    out["state"] = "WATCH"
    out["classification"] = "RESEARCH_H1_PROXY_M5_EXECUTION_DESIGN"
    return out.reset_index(drop=True)


def run(m5_csv: Path, recent_limit: int = 30) -> dict:
    bars = attach_h1_proxy(prepare(pd.read_csv(m5_csv)), ResearchConfig())
    watch = build_m5_watch(bars)
    new_queue = make_manual_queue(watch.tail(recent_limit))
    old_queue = (pd.read_csv(REVIEW_PATH, keep_default_na=False, dtype=str)
                 if REVIEW_PATH.is_file() else pd.DataFrame())
    queue = merge_reviews(new_queue, old_queue)
    queue["execution_timeframe"] = "M5"
    queue["classification"] = "MANUAL_INPUT_REQUIRED_M5_EXECUTION"
    notification = evaluate_manual_queue(queue)

    prepared = prepare(pd.read_csv(m5_csv))
    events = evaluate_triggers(prepared, queue)
    fresh, pending_sent = fresh_events(events, load_sent(SENT_PATH))

    watch.to_csv(WATCH_PATH, index=False)
    queue.to_csv(REVIEW_PATH, index=False)
    notification.to_csv(NOTIFICATION_PATH, index=False)
    events.to_csv(EVALUATION_PATH, index=False)
    fresh.to_csv(ALERT_PATH, index=False)
    # Local durable CSV is the accepted delivery target. Windows display has its own retry state.
    save_sent(SENT_PATH, pending_sent)
    result = {
        "schema_version": "1.23", "status": "COMPLETED",
        "execution_timeframe": "M5", "last_bar_time": bars.iloc[-1]["timestamp"].isoformat(),
        "watch_candidates_total": len(watch), "review_queue_count": len(queue),
        "ready_confirmed": int((notification["state"] == "READY").sum()),
        "fresh_alerts": len(fresh), "ohlc_sha256": _digest(m5_csv),
        "upper_timeframes": "DATA_ACQUIRED_MANUAL_INTERPRETATION",
        "orders_enabled": False,
    }
    STATE_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result

