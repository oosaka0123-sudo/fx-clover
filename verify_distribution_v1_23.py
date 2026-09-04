"""Verify critical v1.23 multi-timeframe distribution files."""

from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EXPECTED = {
    "fx_clover_engine.py": "87f7c2bf75eba70534913dd978c314e97f607a02e5d8fbef95582c397b8e2ee4",
    "trigger_review_v1_9.py": "c67f578698d95b188cac00261d68bff57b5db7b2dd256a8d319278df2d55894d",
    "watch_monitor_v1_4.py": "b8a18ad1b446f4d9ddd1074bcff41d94c65c18963cc218cfd613a4483ad2ce91",
    "build_review_desk_v1_13.py": "923a47f349d11f87b4c6a73520ba813e89d48ac17bda5737704f6e514b8813f3",
    "windows_local_notify_v1_17.py": "4ee72e84b98f7e970daed962354edf0099a69eef492f6c8c6c2914084796184d",
    "live_cycle_v1_23.py": "1a322adbfa0940a2f4dac838a5f9163bfc8be454df931a14635496968bb34aa3",
    "m5_monitor_v1_23.py": "0462520b9806c9f8568aaf07e5ce48a3e0059de1570ca592824f0498808ffed2",
    "mt4_mtf_data_feed_v1_23.py": "c0472081eda1053475c7612d0a0757f366793e02e6ee4d31f893585bbce84718",
    "system_health_check_v1_23.py": "c478b9a937bcb1290220a7addb49c2cff10a840c1db5135f9cd3df0cfbfebf72",
    "FX_Clover_MTF_Exporter_v1_23.mq4": "b6c68d6601ded4d77963eced8c995f786d3eb67109c0c6efd7128b8d9e145a7f",
}
IMPORTS = [
    "fx_clover_engine", "trigger_review_v1_9", "watch_monitor_v1_4",
    "build_review_desk_v1_13", "windows_local_notify_v1_17",
    "live_cycle_v1_23", "m5_monitor_v1_23", "mt4_mtf_data_feed_v1_23",
    "system_health_check_v1_23",
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(root: Path = ROOT, import_modules: bool = True) -> dict:
    files = []
    for name, expected in EXPECTED.items():
        path = root / name
        actual = digest(path) if path.is_file() else ""
        files.append({"file": name, "exists": path.is_file(), "sha256": actual,
                      "expected_sha256": expected, "hash_matches": actual == expected})
    imports = {}
    if import_modules and all(row["hash_matches"] for row in files):
        for name in IMPORTS:
            try:
                importlib.import_module(name); imports[name] = "OK"
            except Exception as exc:
                imports[name] = f"FAILED:{type(exc).__name__}:{exc}"
    passed = all(row["hash_matches"] for row in files) and all(v == "OK" for v in imports.values())
    return {"schema_version": "1.23", "status": "PASS" if passed else "FAIL",
            "critical_files": files, "imports": imports, "orders_enabled": False}


def run() -> dict:
    result = verify()
    (ROOT / "FX_Clover_distribution_check_v1_23.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    raise SystemExit(0 if run()["status"] == "PASS" else 1)
