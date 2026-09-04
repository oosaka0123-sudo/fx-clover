"""Import closed M15 bars exported by MT4. No broker/order connectivity."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile

import pandas as pd


ROOT = Path(__file__).resolve().parent
EXPORT_NAME = "FX_Clover_GBPJPY_M15_closed.csv"
REQUIRED = ["timestamp", "open", "high", "low", "close"]


def default_mt4_source() -> Path:
    configured = os.environ.get("FX_CLOVER_MT4_EXPORT_CSV", "").strip()
    if configured:
        return Path(configured).expanduser()
    appdata = os.environ.get("APPDATA", "").strip()
    if not appdata:
        raise RuntimeError("APPDATA unavailable; set FX_CLOVER_MT4_EXPORT_CSV")
    return Path(appdata) / "MetaQuotes" / "Terminal" / "Common" / "Files" / EXPORT_NAME


def read_export(path: Path) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(f"MT4 export not found: {path}")
    df = pd.read_csv(path, keep_default_na=False)
    missing = set(REQUIRED) - set(df.columns)
    if missing:
        raise ValueError(f"MT4 export columns missing: {sorted(missing)}")
    if df.empty:
        raise ValueError("MT4 export contains no closed bars")
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="raise")
    for col in ["open", "high", "low", "close"]:
        df[col] = pd.to_numeric(df[col], errors="raise")
    if "tick_volume" in df:
        df["tick_volume"] = pd.to_numeric(df["tick_volume"], errors="raise").astype("int64")
    else:
        df["tick_volume"] = 0
    df = df[["timestamp", "open", "high", "low", "close", "tick_volume"]]
    if df["timestamp"].duplicated().any():
        raise ValueError("Duplicate timestamps in MT4 export")
    if not df["timestamp"].is_monotonic_increasing:
        raise ValueError("MT4 export timestamps are not increasing")
    if len(df) >= 2:
        gaps = df["timestamp"].diff().dropna()
        if (gaps <= pd.Timedelta(0)).any():
            raise ValueError("Invalid MT4 timestamp sequence")
    return df


def assert_source_fresh(path: Path, max_file_age_minutes: int = 20,
                        now_utc: datetime | None = None) -> float:
    now = now_utc or datetime.now(timezone.utc)
    modified = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
    age_minutes = (now - modified).total_seconds() / 60.0
    if age_minutes < -2:
        raise ValueError("MT4 export modification time is in the future")
    if age_minutes > max_file_age_minutes:
        raise RuntimeError(f"STALE_MT4_EXPORT: file age {age_minutes:.1f} minutes")
    return age_minutes


def merge_history(existing_path: Path, incoming: pd.DataFrame) -> pd.DataFrame:
    if existing_path.is_file():
        old = pd.read_csv(existing_path)
        old["timestamp"] = pd.to_datetime(old["timestamp"], errors="raise")
        combined = pd.concat([old, incoming], ignore_index=True, sort=False)
    else:
        combined = incoming.copy()
    combined = (combined.sort_values("timestamp")
                .drop_duplicates("timestamp", keep="last")
                .reset_index(drop=True))
    if combined["timestamp"].duplicated().any() or not combined["timestamp"].is_monotonic_increasing:
        raise ValueError("Merged OHLC history is invalid")
    return combined[["timestamp", "open", "high", "low", "close", "tick_volume"]]


def atomic_write_csv(df: pd.DataFrame, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=destination.name + ".", suffix=".tmp",
                                     dir=destination.parent)
    os.close(fd)
    temp_path = Path(temp_name)
    try:
        out = df.copy()
        out["timestamp"] = pd.to_datetime(out["timestamp"]).dt.strftime("%Y-%m-%dT%H:%M")
        out.to_csv(temp_path, index=False)
        os.replace(temp_path, destination)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def refresh(source: Path, destination: Path, max_file_age_minutes: int = 20) -> dict:
    age = assert_source_fresh(source, max_file_age_minutes)
    incoming = read_export(source)
    merged = merge_history(destination, incoming)
    atomic_write_csv(merged, destination)
    result = {
        "status": "UPDATED",
        "source": str(source),
        "destination": str(destination),
        "source_file_age_minutes": round(age, 3),
        "incoming_closed_bars": len(incoming),
        "total_bars": len(merged),
        "last_closed_bar_server_time": pd.Timestamp(merged.iloc[-1]["timestamp"]).isoformat(),
        "timezone_status": "XM_SERVER_TIME_UNCONVERTED",
        "orders_enabled": False,
    }
    (ROOT / "mt4_data_feed_state_v1_10.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=None)
    parser.add_argument("--destination", type=Path, default=ROOT / "GBPJPY_ohlc.csv")
    parser.add_argument("--max-file-age-minutes", type=int, default=20)
    args = parser.parse_args()
    print(json.dumps(refresh(args.source or default_mt4_source(), args.destination,
                             args.max_file_age_minutes), ensure_ascii=False, indent=2))
