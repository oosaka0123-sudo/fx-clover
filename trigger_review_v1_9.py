"""Post-review READY/TRIGGER evaluator. No broker/order connectivity."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from research_pipeline_v1_3 import prepare
from watch_monitor_v1_4 import MANUAL_COLUMNS, evaluate_manual_queue


ROOT = Path(__file__).resolve().parent
EVENT_COLUMNS = [
    "candidate_key", "ready_confirmed_at", "evaluation_bar_time", "event",
    "entry_reference_price", "stop_anchor_price", "orders_enabled",
]


def upgrade_review_queue(queue: pd.DataFrame) -> pd.DataFrame:
    out = queue.copy()
    for col in ["ready_confirmed_at", "reviewer"]:
        if col not in out:
            out[col] = ""
    return out


def confirmed_ready(queue: pd.DataFrame) -> pd.DataFrame:
    out = evaluate_manual_queue(upgrade_review_queue(queue))
    out["ready_confirmed_at"] = pd.to_datetime(out["ready_confirmed_at"], utc=True, errors="coerce")
    return out[(out["state"] == "READY") & out["ready_confirmed_at"].notna()].copy()


def evaluate_triggers(bars: pd.DataFrame, queue: pd.DataFrame) -> pd.DataFrame:
    ready = confirmed_ready(queue)
    events = []
    for item in ready.itertuples(index=False):
        future = bars[bars["timestamp"] > item.ready_confirmed_at]
        # First eligible closed bar only. Later bars require a new READY review.
        if future.empty:
            continue
        row = future.iloc[0]
        trigger = bool(row["bearish"] and row["all_rates_below_dma3x3"] and row["close"] < row["dma3x3"])
        events.append({
            "candidate_key": item.candidate_key,
            "ready_confirmed_at": item.ready_confirmed_at,
            "evaluation_bar_time": row["timestamp"],
            "event": "TRIGGER" if trigger else "READY_RECHECK_FAILED",
            "entry_reference_price": float(row["close"]) if trigger else "",
            "stop_anchor_price": item.stop_anchor_price,
            "orders_enabled": False,
        })
    return pd.DataFrame(events, columns=EVENT_COLUMNS)


def load_sent(path: Path) -> set[str]:
    if not path.exists():
        return set()
    data = json.loads(path.read_text(encoding="utf-8"))
    return set(data.get("sent_event_keys", []))


def event_key(row) -> str:
    return f"{row.candidate_key}|{row.event}|{pd.Timestamp(row.evaluation_bar_time).isoformat()}"


def fresh_events(events: pd.DataFrame, sent: set[str]) -> tuple[pd.DataFrame, set[str]]:
    if events.empty:
        return events.copy(), sent
    out = events.copy()
    out["event_key"] = [event_key(x) for x in out.itertuples(index=False)]
    fresh = out[~out["event_key"].isin(sent)].copy()
    return fresh, sent | set(fresh["event_key"])


def save_sent(path: Path, sent: set[str]) -> None:
    path.write_text(json.dumps({"sent_event_keys": sorted(sent),
                                "orders_enabled": False}, indent=2), encoding="utf-8")


def acknowledge_events(path: Path, events: pd.DataFrame) -> set[str]:
    """Persist only events that were actually delivered or locally accepted."""
    sent = load_sent(path)
    if not events.empty:
        if "event_key" in events:
            sent.update(events["event_key"].astype(str))
        else:
            sent.update(event_key(x) for x in events.itertuples(index=False))
    save_sent(path, sent)
    return sent


def run(ohlc_path: Path, review_path: Path, state_path: Path, acknowledge=True):
    bars = prepare(pd.read_csv(ohlc_path))
    queue = upgrade_review_queue(pd.read_csv(review_path, keep_default_na=False, dtype=str))
    queue.to_csv(ROOT / "GBPJPY_manual_review_queue_v1_5.csv", index=False)
    events = evaluate_triggers(bars, queue)
    fresh, _ = fresh_events(events, load_sent(state_path))
    events.to_csv(ROOT / "GBPJPY_trigger_evaluations_v1_5.csv", index=False)
    fresh.to_csv(ROOT / "GBPJPY_local_alerts_v1_5.csv", index=False)
    if acknowledge:
        acknowledge_events(state_path, fresh)
    print(json.dumps({"ready_confirmed": len(confirmed_ready(queue)),
                      "evaluations": len(events), "fresh_alerts": len(fresh),
                      "orders_enabled": False}, indent=2))
    return fresh


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ohlc", type=Path, default=ROOT / "GBPJPY_ohlc.csv")
    parser.add_argument("--reviews", type=Path, default=ROOT / "GBPJPY_manual_review_queue_v1_5.csv")
    parser.add_argument("--state", type=Path, default=ROOT / "sent_alert_state_v1_5.json")
    args = parser.parse_args()
    run(args.ohlc, args.reviews, args.state)
