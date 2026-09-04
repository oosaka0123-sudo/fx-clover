"""Portable 15-minute FX-Clover cycle using CSV + optional webhook.

The common-denominator design uses only Python's standard HTTP client and local
files. No broker connection or order execution is included.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import traceback
import urllib.request
from urllib.parse import urlparse

import pandas as pd

from trigger_review_v1_9 import acknowledge_events, run as run_trigger_review
from watch_monitor_v1_4 import MANUAL_COLUMNS, run as run_watch


ROOT = Path(__file__).resolve().parent
PRESERVE_COLUMNS = MANUAL_COLUMNS + [
    "formation_type", "stop_anchor_price", "review_status", "review_note",
    "ready_confirmed_at", "reviewer",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_ohlc(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(path)
    df = pd.read_csv(path)
    required = {"timestamp", "open", "high", "low", "close"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"OHLC columns missing: {sorted(missing)}")
    ts = pd.to_datetime(df["timestamp"], utc=True, errors="raise")
    if ts.duplicated().any():
        raise ValueError("Duplicate timestamps in OHLC CSV")
    if not ts.is_monotonic_increasing:
        raise ValueError("OHLC timestamps are not increasing")
    return {"rows": len(df), "first_bar": ts.iloc[0].isoformat(), "last_bar": ts.iloc[-1].isoformat()}


def merge_reviews(new_queue: pd.DataFrame, old_queue: pd.DataFrame) -> pd.DataFrame:
    out = new_queue.copy()
    for col in PRESERVE_COLUMNS:
        if col not in out:
            out[col] = ""
    if old_queue.empty or "candidate_key" not in old_queue:
        return out
    old = old_queue.drop_duplicates("candidate_key", keep="last").set_index("candidate_key")
    for col in PRESERVE_COLUMNS:
        if col not in old:
            continue
        mapped = out["candidate_key"].map(old[col])
        keep = mapped.notna() & mapped.astype(str).ne("")
        out.loc[keep, col] = mapped[keep]
    # Keep reviewed/READY candidates even after they fall outside recent_limit.
    existing_keys = set(out["candidate_key"].astype(str))
    review_status = old_queue.get("review_status", pd.Series("", index=old_queue.index)).astype(str)
    ready_at = old_queue.get("ready_confirmed_at", pd.Series("", index=old_queue.index)).astype(str)
    active = old_queue[(review_status.str.upper().ne("UNREVIEWED") & review_status.ne("")) |
                       ready_at.ne("")]
    active = active[~active["candidate_key"].astype(str).isin(existing_keys)]
    if not active.empty:
        out = pd.concat([out, active], ignore_index=True, sort=False).fillna("")
    return out


def webhook_payload(row, provider="generic") -> dict:
    text = (f"FX-Clover {row.event}\n{row.candidate_key}\n"
            f"確定足: {row.evaluation_bar_time}\n参考価格: {row.entry_reference_price}\n"
            "※監視通知のみ。売買注文ではありません。")
    if provider == "discord":
        return {"content": text}
    if provider == "slack":
        return {"text": text}
    return {"text": text, "event": row.event, "candidate_key": row.candidate_key,
            "orders_enabled": False}


def send_webhook(url: str, payload: dict, timeout=10) -> int:
    if urlparse(url).scheme.lower() != "https":
        raise ValueError("Webhook URL must use HTTPS")
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return int(response.status)


def run_cycle(ohlc: Path, force=False, provider="generic") -> dict:
    info = validate_ohlc(ohlc)
    state_path = ROOT / "auto_cycle_state_v1_9.json"
    old_state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
    digest = sha256(ohlc)
    if not force and old_state.get("ohlc_sha256") == digest:
        return {**info, "status": "SKIPPED_UNCHANGED", "orders_enabled": False}

    old_review_path = ROOT / "GBPJPY_manual_review_queue_v1_5.csv"
    old_reviews = (pd.read_csv(old_review_path, keep_default_na=False, dtype=str)
                   if old_review_path.exists() else pd.DataFrame())
    run_watch(ohlc, recent_limit=30)
    new_reviews = pd.read_csv(ROOT / "GBPJPY_manual_review_queue_v1_4.csv",
                              keep_default_na=False, dtype=str)
    merged = merge_reviews(new_reviews, old_reviews)
    merged.to_csv(old_review_path, index=False)
    sent_state_path = ROOT / "sent_alert_state_v1_5.json"
    run_trigger_review(ohlc, old_review_path, sent_state_path, acknowledge=False)

    alerts_path = ROOT / "GBPJPY_local_alerts_v1_5.csv"
    alerts = pd.read_csv(alerts_path, keep_default_na=False, dtype=str)
    url = os.environ.get("FX_CLOVER_WEBHOOK_URL", "").strip()
    sent = 0
    failed = 0
    delivered = []
    if url:
        for row in alerts.itertuples(index=False):
            try:
                status = send_webhook(url, webhook_payload(row, provider))
                if 200 <= status < 300:
                    sent += 1
                    delivered.append(row._asdict())
                else:
                    failed += 1
            except Exception:
                failed += 1
                with (ROOT / "auto_cycle_errors_v1_9.log").open("a", encoding="utf-8") as log:
                    log.write(traceback.format_exc() + "\n")
        acknowledge_events(sent_state_path, pd.DataFrame(delivered))
    else:
        # The durable local alert CSV is the delivery target when no webhook is configured.
        acknowledge_events(sent_state_path, alerts)
    result = {**info, "status": "COMPLETED", "fresh_alerts": len(alerts),
              "webhook_sent": sent, "webhook_failed": failed,
              "webhook_configured": bool(url), "orders_enabled": False}
    state_path.write_text(json.dumps({**result, "ohlc_sha256": digest}, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ohlc", type=Path, default=ROOT / "GBPJPY_ohlc.csv")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--provider", choices=["generic", "discord", "slack"], default="generic")
    args = parser.parse_args()
    try:
        print(json.dumps(run_cycle(args.ohlc, args.force, args.provider), ensure_ascii=False, indent=2))
    except Exception:
        with (ROOT / "auto_cycle_errors_v1_9.log").open("a", encoding="utf-8") as log:
            log.write(traceback.format_exc() + "\n")
        raise
