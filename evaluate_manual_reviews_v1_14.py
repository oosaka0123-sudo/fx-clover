"""Validate blind manual reviews and evaluate research proxies (v1.14).

This module never fills discretionary fields, promotes a proxy to an official
rule, changes the live monitor, or sends orders.  It evaluates only after
explicit design gates are satisfied.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
EXPECTED = ROOT / "GBPJPY_blind_review_input_v1_12.csv"
DIAGNOSTICS = ROOT / "GBPJPY_blind_review_diagnostics_v1_12.csv"
STATUS_OUT = ROOT / "GBPJPY_manual_review_validation_v1_14.json"
METRICS_OUT = ROOT / "GBPJPY_manual_proxy_metrics_v1_14.csv"

ALLOWED_DECISIONS = {
    "", "FINAL_SHAPE_CANDIDATE", "HOLD", "EXCLUDED_SHAPE", "UNDETERMINED",
}
PROXIES = [
    "baseline_shape_proxy", "common_filter_proxy", "dma25x5_falling",
    "all_rates_below_dma25x5", "dma_bear_stack", "h1_watch_proxy",
]


def _text(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip()


def find_review_file(explicit: str | None = None) -> Path:
    if explicit:
        path = Path(explicit).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        return path
    candidates = [ROOT / "GBPJPY_blind_review_input_v1_13.csv"]
    downloads = Path.home() / "Downloads"
    if downloads.is_dir():
        candidates.extend(downloads.glob("GBPJPY_blind_review_input_v1_13*.csv"))
    existing = [path for path in candidates if path.is_file()]
    if not existing:
        raise FileNotFoundError(
            "GBPJPY_blind_review_input_v1_13.csv が見つかりません。"
            "レビューデスクからCSVを書き出してください。"
        )
    return max(existing, key=lambda path: path.stat().st_mtime)


def validate_reviews(
    reviews: pd.DataFrame,
    expected: pd.DataFrame,
    minimum_completed: int = 50,
    minimum_evaluable: int = 30,
    minimum_each_class: int = 10,
) -> tuple[pd.DataFrame, dict]:
    required = {"candidate_key", "manual_decision"}
    missing = sorted(required - set(reviews.columns))
    errors: list[str] = []
    if missing:
        errors.append("MISSING_COLUMNS:" + ",".join(missing))
        return reviews, {
            "status": "INVALID_REVIEW_FILE", "errors": errors,
            "orders_enabled": False,
            "classification": "DESIGN_SAFETY_GATE_NOT_OFFICIAL_RULE",
        }

    work = reviews.copy()
    work["candidate_key"] = _text(work["candidate_key"])
    work["manual_decision"] = _text(work["manual_decision"])
    if work["candidate_key"].duplicated().any():
        errors.append("DUPLICATE_CANDIDATE_KEY")
    invalid = sorted(set(work["manual_decision"]) - ALLOWED_DECISIONS)
    if invalid:
        errors.append("INVALID_MANUAL_DECISION:" + ",".join(invalid))

    expected_keys = set(_text(expected["candidate_key"]))
    actual_keys = set(work["candidate_key"])
    if actual_keys != expected_keys:
        errors.append(
            f"CANDIDATE_SET_MISMATCH:missing={len(expected_keys-actual_keys)},"
            f"extra={len(actual_keys-expected_keys)}"
        )

    completed = int(work["manual_decision"].ne("").sum())
    positive = int(work["manual_decision"].eq("FINAL_SHAPE_CANDIDATE").sum())
    negative = int(work["manual_decision"].eq("EXCLUDED_SHAPE").sum())
    evaluable = positive + negative
    status = "INVALID_REVIEW_FILE" if errors else "READY_FOR_RESEARCH_ONLY_VALIDATION"
    if not errors and completed < minimum_completed:
        status = "INSUFFICIENT_COMPLETED_REVIEWS"
    elif not errors and evaluable < minimum_evaluable:
        status = "INSUFFICIENT_CLEAR_LABELS"
    elif not errors and min(positive, negative) < minimum_each_class:
        status = "INSUFFICIENT_CLASS_BALANCE"

    summary = {
        "schema_version": "1.14",
        "status": status,
        "rows": len(work),
        "completed_reviews": completed,
        "minimum_completed_design_gate": minimum_completed,
        "clear_evaluable_labels": evaluable,
        "minimum_evaluable_design_gate": minimum_evaluable,
        "manual_positive": positive,
        "manual_negative": negative,
        "minimum_each_class_design_gate": minimum_each_class,
        "withheld_hold_or_undetermined": int(work["manual_decision"].isin(
            ["HOLD", "UNDETERMINED"]
        ).sum()),
        "errors": errors,
        "promotion_to_official": False,
        "production_filter_change_allowed": False,
        "orders_enabled": False,
        "classification": "DESIGN_SAFETY_GATE_NOT_OFFICIAL_RULE",
    }
    return work, summary


def _as_bool(series: pd.Series) -> pd.Series:
    return _text(series).str.upper().map({"TRUE": True, "FALSE": False})


def evaluate_proxies(reviews: pd.DataFrame, diagnostics: pd.DataFrame) -> pd.DataFrame:
    labels = reviews[reviews["manual_decision"].isin(
        ["FINAL_SHAPE_CANDIDATE", "EXCLUDED_SHAPE"]
    )][["candidate_key", "manual_decision"]].copy()
    labels["manual_positive"] = labels["manual_decision"].eq("FINAL_SHAPE_CANDIDATE")
    merged = labels.merge(diagnostics, on="candidate_key", how="left", validate="one_to_one")
    rows = []
    for proxy in PROXIES:
        selected = _as_bool(merged[proxy])
        valid = selected.notna()
        actual = merged.loc[valid, "manual_positive"].astype(bool)
        predicted = selected.loc[valid].astype(bool)
        tp = int((actual & predicted).sum())
        fn = int((actual & ~predicted).sum())
        fp = int((~actual & predicted).sum())
        tn = int((~actual & ~predicted).sum())
        rows.append({
            "research_proxy": proxy,
            "evaluable": int(valid.sum()),
            "true_positive": tp, "false_negative": fn,
            "false_positive": fp, "true_negative": tn,
            "recall": tp / (tp + fn) if tp + fn else np.nan,
            "precision": tp / (tp + fp) if tp + fp else np.nan,
            "specificity": tn / (tn + fp) if tn + fp else np.nan,
            "balanced_accuracy": np.mean([
                tp / (tp + fn) if tp + fn else np.nan,
                tn / (tn + fp) if tn + fp else np.nan,
            ]),
            "classification": "RESEARCH_DIAGNOSTIC_NOT_OFFICIAL",
            "decision": "DO_NOT_PROMOTE_AUTOMATICALLY",
        })
    return pd.DataFrame(rows)


def run(review_path: str | None = None) -> dict:
    source = find_review_file(review_path)
    reviews = pd.read_csv(source, keep_default_na=False, dtype=str)
    expected = pd.read_csv(EXPECTED, keep_default_na=False, dtype=str)
    checked, status = validate_reviews(reviews, expected)
    status["review_file"] = str(source)
    STATUS_OUT.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    if status["status"] == "READY_FOR_RESEARCH_ONLY_VALIDATION":
        diagnostics = pd.read_csv(DIAGNOSTICS, keep_default_na=False, dtype=str)
        metrics = evaluate_proxies(checked, diagnostics)
        metrics.to_csv(METRICS_OUT, index=False)
        status["metrics_output"] = str(METRICS_OUT)
    else:
        METRICS_OUT.unlink(missing_ok=True)
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return status


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reviews")
    args = parser.parse_args()
    run(args.reviews)


if __name__ == "__main__":
    main()
