"""Validate and merge closed MT4 bars for D1/H4/H1/M15/M5. No orders."""

from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path

from mt4_data_feed_v1_10 import (
    assert_source_fresh, atomic_write_csv, merge_history, read_export,
)


ROOT = Path(__file__).resolve().parent
TIMEFRAMES = ("D1", "H4", "H1", "M15", "M5")


def default_common_dir() -> Path:
    configured = os.environ.get("FX_CLOVER_MT4_COMMON_FILES", "").strip()
    if configured:
        return Path(configured).expanduser()
    appdata = os.environ.get("APPDATA", "").strip()
    if not appdata:
        raise RuntimeError("APPDATA unavailable; set FX_CLOVER_MT4_COMMON_FILES")
    return Path(appdata) / "MetaQuotes" / "Terminal" / "Common" / "Files"


def source_path(common_dir: Path, timeframe: str) -> Path:
    return common_dir / f"FX_Clover_GBPJPY_{timeframe}_closed.csv"


def destination_path(root: Path, timeframe: str) -> Path:
    return root / f"GBPJPY_{timeframe}_ohlc_v1_23.csv"


def refresh_all(common_dir: Path, destination_root: Path = ROOT,
                max_file_age_minutes: int = 10,
                now_utc: datetime | None = None) -> dict:
    now = now_utc or datetime.now(timezone.utc)
    results = {}
    for timeframe in TIMEFRAMES:
        source = source_path(common_dir, timeframe)
        age = assert_source_fresh(source, max_file_age_minutes, now)
        incoming = read_export(source)
        destination = destination_path(destination_root, timeframe)
        merged = merge_history(destination, incoming)
        atomic_write_csv(merged, destination)
        results[timeframe] = {
            "status": "UPDATED", "source": str(source),
            "destination": str(destination), "file_age_minutes": round(age, 3),
            "incoming_closed_bars": len(incoming), "total_bars": len(merged),
            "last_closed_bar_server_time": incoming.iloc[-1]["timestamp"].isoformat(),
        }
    return {
        "schema_version": "1.23", "status": "UPDATED",
        "timeframes": results, "execution_timeframe": "M5",
        "timezone_status": "XM_SERVER_TIME_UNCONVERTED",
        "classification": "DESIGN_TIMEFRAME_CONFIGURATION_USER_CONFIRMED",
        "orders_enabled": False,
    }
