"""FX-Clover research backtester v1.

No broker connection and no order execution are included.  GBPJPY is the
official-reference instrument; USDJPY, EURJPY and GBPUSD are research
extensions using the same engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

import numpy as np
import pandas as pd


class State(str, Enum):
    NO_TRADE = "NO_TRADE"
    WATCH = "WATCH"
    READY = "READY"
    SIMULATED_POSITION = "SIMULATED_POSITION"


@dataclass(frozen=True)
class Config:
    symbol: str
    upper_timeframe: str = "1h"
    execution_timeframe: str = "15m"
    applied_price: str = "close"
    initial_size: float = 1.0
    stop_fe_priority: str = "STOP"  # research specification
    prohibit_same_bar_reentry: bool = True


REQUIRED_OHLC = {"timestamp", "open", "high", "low", "close"}
MANUAL_DEFAULTS = {
    "watch_scene_a": False,
    "watch_scene_b": False,
    "mid_range": False,
    "lower_right_shoulder": False,
    "inside_dma25x5": False,
    "ma_path_clear": False,
    "has_room": False,
    "upper_environment_valid": False,
    "early_exit_alert": False,
    "stop_anchor_price": np.nan,
    # Safety design: a missing spread must not silently become zero.
    "spread_price": np.nan,
    "fe_target_1": np.nan,
    "fe_target_2": np.nan,
    "fe_target_3": np.nan,
    "fe_fraction_1": 0.0,
    "fe_fraction_2": 0.0,
    "fe_fraction_3": 0.0,
}


def prepare_bars(ohlc: pd.DataFrame, manual: pd.DataFrame | None = None,
                 applied_price: str = "close") -> pd.DataFrame:
    """Validate bars, calculate DMA values and merge human-labelled inputs."""
    missing = REQUIRED_OHLC - set(ohlc.columns)
    if missing:
        raise ValueError(f"OHLC columns missing: {sorted(missing)}")
    if applied_price not in ohlc.columns:
        raise ValueError(f"Applied price column not found: {applied_price}")

    bars = ohlc.copy()
    bars["timestamp"] = pd.to_datetime(bars["timestamp"], utc=True)
    bars = bars.sort_values("timestamp").drop_duplicates("timestamp").reset_index(drop=True)
    for column in ("open", "high", "low", "close", applied_price):
        bars[column] = pd.to_numeric(bars[column], errors="raise")

    price = bars[applied_price]
    bars["sma3"] = price.rolling(3, min_periods=3).mean()
    bars["sma25"] = price.rolling(25, min_periods=25).mean()
    bars["dma3x3"] = bars["sma3"].shift(3)
    bars["dma25x5"] = bars["sma25"].shift(5)
    bars["bearish"] = bars["close"] < bars["open"]
    bars["bullish"] = bars["close"] > bars["open"]
    # Research rule: doji belongs to neither side.
    bars["trigger_dma_break"] = bars["bearish"] & (bars["close"] < bars["dma3x3"])
    bars["dma_exit"] = bars["bullish"] & (bars["close"] > bars["dma3x3"])
    bars["all_rates_below_dma3x3"] = bars[["open", "high", "low", "close"]].max(axis=1) < bars["dma3x3"]

    if manual is not None:
        labels = manual.copy()
        if "timestamp" not in labels:
            raise ValueError("Manual input requires timestamp")
        labels["timestamp"] = pd.to_datetime(labels["timestamp"], utc=True)
        bars = bars.merge(labels, on="timestamp", how="left", suffixes=("", "_manual"))
    for name, default in MANUAL_DEFAULTS.items():
        if name not in bars:
            bars[name] = default
        else:
            bars[name] = bars[name].fillna(default)
    return bars


def _is_true(value) -> bool:
    """Strict manual-flag parser; notably, the string 'FALSE' is false."""
    if pd.isna(value):
        return False
    if isinstance(value, str):
        return value.strip().upper() == "TRUE"
    return bool(value is True or value == 1)


def _ready(row: pd.Series) -> bool:
    return all(_is_true(row[x]) for x in (
        "mid_range", "lower_right_shoulder", "inside_dma25x5",
        "ma_path_clear", "has_room", "all_rates_below_dma3x3",
    ))


def _trigger(row: pd.Series) -> bool:
    return _ready(row) and bool(row["trigger_dma_break"])


def run_backtest(bars: pd.DataFrame, config: Config) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run a deterministic short-only simulated state machine."""
    state = State.NO_TRADE
    position = None
    events: list[dict] = []
    trades: list[dict] = []
    blocked_bar = None

    def log(ts, event, **values):
        events.append({"timestamp": ts, "symbol": config.symbol,
                       "state": state.value, "event": event, **values})

    for i, row in bars.iterrows():
        ts = row["timestamp"]
        watch = _is_true(row["watch_scene_a"]) or _is_true(row["watch_scene_b"])
        became_ready = False

        if state == State.SIMULATED_POSITION:
            assert position is not None
            stop_hit = row["high"] >= position["stop_price"]
            targets_hit = [
                n for n in (1, 2, 3)
                if not position[f"fe_done_{n}"]
                and pd.notna(position[f"fe_target_{n}"])
                and row["low"] <= position[f"fe_target_{n}"]
            ]
            if stop_hit and targets_hit and config.stop_fe_priority == "STOP":
                targets_hit = []
            if stop_hit:
                exit_size = position["remaining_size"]
                pnl = (position["entry_price"] - position["stop_price"]) * exit_size
                position["realized_pnl"] += pnl
                position["remaining_size"] = 0.0
                log(ts, "STOP_LOSS", price=position["stop_price"], size=exit_size)
                reason = "STOP"
            else:
                reason = None
                for n in targets_hit:
                    requested = config.initial_size * position[f"fe_fraction_{n}"]
                    exit_size = min(position["remaining_size"], requested)
                    if exit_size > 0:
                        price_at = position[f"fe_target_{n}"]
                        position["remaining_size"] -= exit_size
                        position["realized_pnl"] += (position["entry_price"] - price_at) * exit_size
                        log(ts, "PARTIAL_TAKE_PROFIT", target=n, price=price_at,
                            size=exit_size, remaining_size=position["remaining_size"])
                    position[f"fe_done_{n}"] = True
                if position["remaining_size"] <= 1e-12:
                    reason = "FE"
                elif bool(row["dma_exit"]):
                    exit_size = position["remaining_size"]
                    position["realized_pnl"] += (position["entry_price"] - row["close"]) * exit_size
                    position["remaining_size"] = 0.0
                    log(ts, "DMA_EXIT", price=row["close"], size=exit_size)
                    reason = "DMA"
                elif _is_true(row["early_exit_alert"]):
                    log(ts, "EARLY_EXIT_ALERT")

            if reason:
                trades.append({
                    "symbol": config.symbol,
                    "entry_time": position["entry_time"], "exit_time": ts,
                    "entry_price": position["entry_price"], "stop_price": position["stop_price"],
                    "exit_reason": reason, "pnl_price_units": position["realized_pnl"],
                })
                state = State.NO_TRADE
                log(ts, "EXIT", exit_reason=reason)
                position = None
                blocked_bar = i if config.prohibit_same_bar_reentry else None
            continue

        if blocked_bar == i:
            continue
        if state == State.NO_TRADE and watch:
            state = State.WATCH
            log(ts, "WATCH")
        if state == State.WATCH:
            if not watch and not _is_true(row["upper_environment_valid"]):
                state = State.NO_TRADE
                log(ts, "WATCH_INVALIDATED")
            elif _ready(row):
                state = State.READY
                log(ts, "READY")
                became_ready = True
        if state == State.READY:
            if not (_is_true(row["upper_environment_valid"]) or watch):
                state = State.NO_TRADE
                log(ts, "READY_INVALIDATED")
            elif not _ready(row):
                state = State.WATCH
                log(ts, "READY_TO_WATCH")
            elif became_ready:
                # Design parity with live monitoring: trigger evaluation starts
                # strictly after the READY-confirmation bar.
                continue
            elif _trigger(row):
                if pd.isna(row["stop_anchor_price"]):
                    log(ts, "TRIGGER_REJECTED_MISSING_STOP")
                    continue
                if pd.isna(row["spread_price"]):
                    log(ts, "TRIGGER_REJECTED_MISSING_SPREAD")
                    continue
                entry = float(row["close"])
                stop = float(row["stop_anchor_price"] + row["spread_price"])
                if stop <= entry:
                    log(ts, "TRIGGER_REJECTED_INVALID_STOP")
                    continue
                position = {
                    "entry_time": ts, "entry_price": entry, "stop_price": stop,
                    "remaining_size": config.initial_size, "realized_pnl": 0.0,
                }
                for n in (1, 2, 3):
                    position[f"fe_target_{n}"] = row[f"fe_target_{n}"]
                    position[f"fe_fraction_{n}"] = float(row[f"fe_fraction_{n}"])
                    position[f"fe_done_{n}"] = False
                state = State.SIMULATED_POSITION
                log(ts, "TRIGGER", price=entry, stop_price=stop,
                    remaining_size=config.initial_size)

    return pd.DataFrame(events), pd.DataFrame(trades)


def performance_summary(trades: pd.DataFrame) -> pd.DataFrame:
    """Return symbol-level metrics without claiming profitability."""
    if trades.empty:
        return pd.DataFrame(columns=["symbol", "trades", "wins", "win_rate", "net_pnl",
                                     "profit_factor", "max_drawdown", "max_losing_streak"])
    rows = []
    for symbol, group in trades.groupby("symbol"):
        pnl = group["pnl_price_units"].astype(float)
        # Include starting equity=0; otherwise a first losing trade would
        # incorrectly report zero drawdown because the first loss is also the
        # initial cumulative maximum.
        equity = pd.Series([0.0, *pnl.cumsum().tolist()], dtype=float)
        drawdown = equity.cummax() - equity
        gross_profit = pnl[pnl > 0].sum()
        gross_loss = -pnl[pnl < 0].sum()
        losing = pnl < 0
        streak = losing.groupby((~losing).cumsum()).sum().max() if losing.any() else 0
        rows.append({"symbol": symbol, "trades": len(group), "wins": int((pnl > 0).sum()),
                     "win_rate": float((pnl > 0).mean()), "net_pnl": pnl.sum(),
                     "profit_factor": gross_profit / gross_loss if gross_loss else np.inf,
                     "max_drawdown": drawdown.max(), "max_losing_streak": int(streak)})
    return pd.DataFrame(rows)


def monthly_counts(events: pd.DataFrame) -> pd.DataFrame:
    if events.empty:
        return pd.DataFrame(columns=["symbol", "month", "WATCH", "READY", "TRIGGER"])
    selected = events[events["event"].isin(["WATCH", "READY", "TRIGGER"])].copy()
    # Period has no timezone representation; explicitly remove UTC first to
    # avoid a warning while retaining the same UTC calendar month.
    selected["month"] = (pd.to_datetime(selected["timestamp"], utc=True)
                         .dt.tz_localize(None).dt.to_period("M").astype(str))
    return (selected.groupby(["symbol", "month", "event"]).size().unstack(fill_value=0)
            .reindex(columns=["WATCH", "READY", "TRIGGER"], fill_value=0).reset_index())


def research_diagnostics(
    bars: pd.DataFrame,
    candidate_times: Iterable,
    lookback_bars: int = 15,
    horizons: tuple[int, ...] = (20, 40, 80),
) -> pd.DataFrame:
    """Return non-official MAE/MFE diagnostics for short candidates.

    The preceding-bar high is only a research proxy.  It must not be treated
    as Poko's official stop anchor or as a substitute for the manual
    double-top / head-and-shoulders classification.
    """
    data = bars.copy()
    data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True)
    data = data.sort_values("timestamp").reset_index(drop=True)
    rows: list[dict] = []

    for raw_time in candidate_times:
        ts = pd.to_datetime(raw_time, utc=True)
        matches = data.index[data["timestamp"].eq(ts)]
        if len(matches) == 0:
            rows.append({"timestamp": ts, "status": "TIMESTAMP_NOT_FOUND"})
            continue

        i = int(matches[0])
        entry = float(data.loc[i, "close"])
        preceding = data.iloc[max(0, i - lookback_bars):i + 1]
        proxy_stop = float(preceding["high"].max())
        proxy_r = proxy_stop - entry
        row = {
            "timestamp": ts,
            "status": "OK",
            "entry_price": entry,
            "proxy_stop_price": proxy_stop,
            "proxy_r_price_units": proxy_r,
        }
        for horizon in horizons:
            future = data.iloc[i + 1:min(len(data), i + 1 + horizon)]
            row[f"mfe_{horizon}_price_units"] = (
                entry - float(future["low"].min()) if not future.empty else np.nan
            )
            row[f"mae_{horizon}_price_units"] = (
                float(future["high"].max()) - entry if not future.empty else np.nan
            )
        rows.append(row)
    return pd.DataFrame(rows)


def manual_review_template(symbol: str, candidate_times: Iterable) -> pd.DataFrame:
    """Create blank official-rule review fields without guessing them."""
    times = pd.to_datetime(list(candidate_times), utc=True)
    return pd.DataFrame({
        "timestamp": times,
        "symbol": symbol,
        "watch_scene_a": "",
        "watch_scene_b": "",
        "upper_environment_valid": "",
        "mid_range": "",
        "lower_right_shoulder": "",
        "inside_dma25x5": "",
        "ma_path_clear": "",
        "has_room": "",
        "formation_type": "",
        "stop_anchor_price": "",
        "spread_price": "",
        "fe_target_1": "",
        "fe_target_2": "",
        "fe_target_3": "",
        "fe_fraction_1": "",
        "fe_fraction_2": "",
        "fe_fraction_3": "",
        "review_status": "UNREVIEWED",
        "notes": "",
    })


def run_many(items: Iterable[tuple[pd.DataFrame, pd.DataFrame | None, Config]]):
    all_events, all_trades = [], []
    for ohlc, manual, config in items:
        bars = prepare_bars(ohlc, manual, config.applied_price)
        events, trades = run_backtest(bars, config)
        all_events.append(events)
        all_trades.append(trades)
    return (pd.concat(all_events, ignore_index=True) if all_events else pd.DataFrame(),
            pd.concat(all_trades, ignore_index=True) if all_trades else pd.DataFrame())
