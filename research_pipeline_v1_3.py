"""FX-Clover reproducible research pipeline v1.3.

This module never sends orders. Objective filters in this file are research
proxies and must not be presented as Poko's official Poconiccal rules.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent


@dataclass(frozen=True)
class ResearchConfig:
    h1_require_bearish: bool = True
    h1_require_falling_dma3x3: bool = True
    swing_width: int = 2
    shape_lookback_bars: int = 32
    max_bars_since_right_peak: int = 12
    min_peak_separation_bars: int = 2
    max_peak_separation_bars: int = 20
    lower_right_min_price: float = 0.001
    stop_spread_price: float = 0.0


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    x = df.copy()
    x["timestamp"] = pd.to_datetime(x["timestamp"], utc=True)
    x = x.sort_values("timestamp").drop_duplicates("timestamp").reset_index(drop=True)
    for col in ["open", "high", "low", "close"]:
        x[col] = pd.to_numeric(x[col], errors="raise")
    x["sma3"] = x["close"].rolling(3, min_periods=3).mean()
    x["sma25"] = x["close"].rolling(25, min_periods=25).mean()
    x["dma3x3"] = x["sma3"].shift(3)
    x["dma25x5"] = x["sma25"].shift(5)
    x["bearish"] = x["close"] < x["open"]
    x["bullish"] = x["close"] > x["open"]
    x["all_rates_below_dma3x3"] = x[["open", "high", "low", "close"]].max(axis=1) < x["dma3x3"]
    x["new_below_dma3x3"] = x["all_rates_below_dma3x3"] & ~x["all_rates_below_dma3x3"].shift(1, fill_value=False)
    x["dma_exit"] = x["bullish"] & (x["close"] > x["dma3x3"])
    return x


def attach_h1_proxy(m15: pd.DataFrame, cfg: ResearchConfig) -> pd.DataFrame:
    src = m15.set_index("timestamp")
    # M15 timestamps are bar-open times. Label each H1 aggregate at the time
    # it becomes closed/observable, so no M15 row can see its own unfinished H1.
    h1 = src.resample("1h", label="right", closed="left").agg(
        open=("open", "first"), high=("high", "max"),
        low=("low", "min"), close=("close", "last"),
    ).dropna().reset_index()
    h1 = prepare(h1)
    valid = pd.Series(True, index=h1.index)
    if cfg.h1_require_bearish:
        valid &= h1["bearish"]
    if cfg.h1_require_falling_dma3x3:
        valid &= h1["dma3x3"] < h1["dma3x3"].shift(1)
    lookup = pd.Series(valid.to_numpy(), index=h1["timestamp"])
    out = m15.copy()
    aligned = lookup.reindex(out["timestamp"], method="ffill")
    out["h1_watch_proxy"] = aligned.where(aligned.notna(), False).astype(bool).to_numpy()
    return out


def local_high_indices(high: pd.Series, width: int) -> list[int]:
    values = high.to_numpy()
    result = []
    for i in range(width, len(values) - width):
        left = values[i - width:i]
        right = values[i + 1:i + width + 1]
        if values[i] > left.max() and values[i] >= right.max():
            result.append(i)
    return result


def label_shapes(bars: pd.DataFrame, cfg: ResearchConfig) -> pd.DataFrame:
    candidate_mask = bars["bearish"] & bars["new_below_dma3x3"] & bars["h1_watch_proxy"]
    rows = []
    for i in bars.index[candidate_mask]:
        start = max(0, i - cfg.shape_lookback_bars)
        window = bars.iloc[start:i]
        peaks = local_high_indices(window["high"], cfg.swing_width)
        if len(peaks) < 2:
            continue
        left, right = peaks[-2], peaks[-1]
        separation = right - left
        since_right = len(window) - 1 - right
        left_price = float(window.iloc[left]["high"])
        right_price = float(window.iloc[right]["high"])
        lower_right = right_price <= left_price - cfg.lower_right_min_price
        timing_ok = (
            cfg.min_peak_separation_bars <= separation <= cfg.max_peak_separation_bars
            and since_right <= cfg.max_bars_since_right_peak
        )
        if not (lower_right and timing_ok):
            continue
        rows.append({
            "bar_index": int(i), "timestamp": bars.loc[i, "timestamp"],
            "entry_price": float(bars.loc[i, "close"]),
            "formation_type": "LOWER_DOUBLE_TOP_PROXY",
            "left_peak_time": window.iloc[left]["timestamp"],
            "left_peak_price": left_price,
            "right_peak_time": window.iloc[right]["timestamp"],
            "right_peak_price": right_price,
            "stop_anchor_price": left_price,
            "peak_separation_bars": separation,
            "bars_since_right_peak": since_right,
        })
    return pd.DataFrame(rows)


def simulate_non_overlapping(bars: pd.DataFrame, candidates: pd.DataFrame, cfg: ResearchConfig) -> pd.DataFrame:
    trades = []
    next_free_index = -1
    for c in candidates.itertuples(index=False):
        if c.bar_index <= next_free_index:
            continue
        stop = c.stop_anchor_price + cfg.stop_spread_price
        if stop <= c.entry_price:
            continue
        exit_i = None
        exit_price = np.nan
        reason = "OPEN_AT_DATA_END"
        for i in range(c.bar_index + 1, len(bars)):
            row = bars.iloc[i]
            if row["high"] >= stop:
                exit_i, exit_price, reason = i, stop, "STOP"
                break
            if bool(row["dma_exit"]):
                exit_i, exit_price, reason = i, float(row["close"]), "DMA_EXIT"
                break
        if exit_i is None:
            exit_i = len(bars) - 1
        pnl = c.entry_price - exit_price if pd.notna(exit_price) else np.nan
        risk = stop - c.entry_price
        trades.append({
            "entry_time": c.timestamp, "exit_time": bars.iloc[exit_i]["timestamp"],
            "entry_price": c.entry_price, "stop_price": stop,
            "exit_price": exit_price, "exit_reason": reason,
            "pnl_price_units": pnl, "r_multiple": pnl / risk if pd.notna(pnl) else np.nan,
        })
        next_free_index = exit_i
    return pd.DataFrame(trades)


def max_losing_streak(pnl: pd.Series) -> int:
    best = run = 0
    for value in pnl:
        run = run + 1 if value < 0 else 0
        best = max(best, run)
    return best


def summarize(trades: pd.DataFrame) -> pd.DataFrame:
    closed = trades.dropna(subset=["pnl_price_units"]).copy()
    pnl = closed["pnl_price_units"]
    equity = pd.Series([0.0, *pnl.cumsum().tolist()])
    dd = equity.cummax() - equity
    gp, gl = pnl[pnl > 0].sum(), -pnl[pnl < 0].sum()
    return pd.DataFrame([{
        "trades": len(closed), "wins": int((pnl > 0).sum()),
        "win_rate": float((pnl > 0).mean()) if len(pnl) else np.nan,
        "net_pnl_price_units": float(pnl.sum()),
        "profit_factor": float(gp / gl) if gl else np.inf,
        "max_drawdown_price_units": float(dd.max()) if len(dd) else 0.0,
        "max_losing_streak": max_losing_streak(pnl),
        "mean_r": float(closed["r_multiple"].mean()),
        "median_r": float(closed["r_multiple"].median()),
    }])


def run(input_csv: Path = ROOT / "GBPJPY_ohlc.csv") -> None:
    cfg = ResearchConfig()
    bars = attach_h1_proxy(prepare(pd.read_csv(input_csv)), cfg)
    candidates = label_shapes(bars, cfg)
    trades = simulate_non_overlapping(bars, candidates, cfg)
    summary = summarize(trades)
    monthly = candidates.assign(month=candidates["timestamp"].dt.strftime("%Y-%m")).groupby("month").size().rename("research_candidates").reset_index()
    pd.DataFrame([asdict(cfg)]).to_csv(ROOT / "research_config_v1_3.csv", index=False)
    candidates.to_csv(ROOT / "GBPJPY_research_candidates_v1_3.csv", index=False)
    trades.to_csv(ROOT / "GBPJPY_research_trades_v1_3.csv", index=False)
    summary.to_csv(ROOT / "GBPJPY_research_summary_v1_3.csv", index=False)
    monthly.to_csv(ROOT / "GBPJPY_research_monthly_v1_3.csv", index=False)
    print("TECHNICAL NEW-BELOW:", int((bars["bearish"] & bars["new_below_dma3x3"]).sum()))
    print("H1 PROXY:", int((bars["bearish"] & bars["new_below_dma3x3"] & bars["h1_watch_proxy"]).sum()))
    print("SHAPE PROXY:", len(candidates))
    print(summary.to_string(index=False))


if __name__ == "__main__":
    run()
