"""WATCH-only monitoring prototype for FX-Clover.

No broker connection or order execution. READY/TRIGGER are emitted only when
the required manual fields are explicitly TRUE.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import pandas as pd

from research_pipeline_v1_3 import ResearchConfig, attach_h1_proxy, prepare


ROOT = Path(__file__).resolve().parent
MANUAL_COLUMNS = [
    "mid_range", "lower_right_shoulder", "inside_dma25x5",
    "ma_path_clear", "has_room", "upper_environment_valid",
]


def candidate_key(symbol: str, timeframe: str, timestamp) -> str:
    ts = pd.Timestamp(timestamp).isoformat()
    return f"{symbol}|{timeframe}|{ts}"


def build_watch_candidates(bars: pd.DataFrame, symbol="GBPJPY") -> pd.DataFrame:
    mask = bars["bearish"] & bars["new_below_dma3x3"] & bars["h1_watch_proxy"]
    out = bars.loc[mask, ["timestamp", "open", "high", "low", "close", "dma3x3", "dma25x5"]].copy()
    out.insert(0, "candidate_key", [candidate_key(symbol, "M15", x) for x in out.timestamp])
    out.insert(1, "symbol", symbol)
    out.insert(2, "timeframe", "M15")
    out["state"] = "WATCH"
    out["classification"] = "RESEARCH_H1_PROXY"
    return out.reset_index(drop=True)


def make_manual_queue(watch: pd.DataFrame) -> pd.DataFrame:
    queue = watch[["candidate_key", "symbol", "timeframe", "timestamp", "state"]].copy()
    for col in MANUAL_COLUMNS:
        queue[col] = ""
    queue["formation_type"] = ""
    queue["stop_anchor_price"] = ""
    queue["review_status"] = "UNREVIEWED"
    queue["review_note"] = ""
    return queue


def evaluate_manual_queue(queue: pd.DataFrame) -> pd.DataFrame:
    out = queue.copy()
    truth = {True, "TRUE", "True", "true", 1, "1"}
    ready = out[MANUAL_COLUMNS].apply(lambda s: s.map(lambda x: x in truth)).all(axis=1)
    stop_ok = pd.to_numeric(out["stop_anchor_price"], errors="coerce").notna()
    out["state"] = np.where(ready, "READY", "WATCH")
    out["notification_event"] = np.where(ready & stop_ok, "READY_FOR_TRIGGER_REVIEW", "WATCH_REVIEW_REQUIRED")
    return out


def deduplicate_alerts(events: pd.DataFrame, sent_keys: set[str]) -> tuple[pd.DataFrame, set[str]]:
    fresh = events[~events["candidate_key"].isin(sent_keys)].copy()
    return fresh, sent_keys | set(fresh["candidate_key"])


def plot_watch_pdf(bars: pd.DataFrame, watch: pd.DataFrame, output: Path, limit=30):
    selected = watch.tail(limit)
    with PdfPages(output) as pdf:
        for row in selected.itertuples(index=False):
            idx = bars.index[bars["timestamp"] == row.timestamp]
            if len(idx) != 1:
                continue
            i = int(idx[0])
            x = bars.iloc[max(0, i - 64): min(len(bars), i + 17)].copy()
            fig, ax = plt.subplots(figsize=(13, 6))
            colors = np.where(x["close"] >= x["open"], "green", "red")
            ax.vlines(x["timestamp"], x["low"], x["high"], color=colors, linewidth=0.7)
            ax.bar(x["timestamp"], x["close"] - x["open"], bottom=x["open"],
                   width=0.008, color=colors, alpha=0.85)
            ax.plot(x["timestamp"], x["dma3x3"], color="blue", label="DMA3x3")
            ax.plot(x["timestamp"], x["dma25x5"], color="orange", label="DMA25x5")
            ax.axvline(row.timestamp, color="magenta", linewidth=1.4, label="WATCH")
            ax.set_title(f"{row.candidate_key} | WATCH / research H1 proxy")
            ax.grid(alpha=0.2)
            ax.legend()
            fig.autofmt_xdate()
            fig.tight_layout()
            pdf.savefig(fig)
            plt.close(fig)


def run(input_csv: Path, recent_limit: int = 30):
    bars = attach_h1_proxy(prepare(pd.read_csv(input_csv)), ResearchConfig())
    watch = build_watch_candidates(bars)
    recent = watch.tail(recent_limit).copy()
    queue = make_manual_queue(recent)
    events = evaluate_manual_queue(queue)
    watch.to_csv(ROOT / "GBPJPY_watch_candidates_all_v1_4.csv", index=False)
    queue.to_csv(ROOT / "GBPJPY_manual_review_queue_v1_4.csv", index=False)
    events.to_csv(ROOT / "GBPJPY_notification_queue_v1_4.csv", index=False)
    plot_watch_pdf(bars, watch, ROOT / "GBPJPY_watch_charts_latest30_v1_4.pdf", recent_limit)
    state = {
        "schema_version": "1.4", "last_bar_time": bars.iloc[-1]["timestamp"].isoformat(),
        "watch_candidates_total": len(watch), "review_queue_count": len(queue),
        "orders_enabled": False,
    }
    (ROOT / "monitor_state_v1_4.json").write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(state, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=ROOT / "GBPJPY_ohlc.csv")
    parser.add_argument("--recent-limit", type=int, default=30)
    args = parser.parse_args()
    run(args.input, args.recent_limit)
