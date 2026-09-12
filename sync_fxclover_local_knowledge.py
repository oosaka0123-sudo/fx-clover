"""Sync the full official FX-Clover catalog into a private local SQLite cache."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from fxclover_local_knowledge import CATALOG_PATH, DEFAULT_DB_PATH, sync_knowledge


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=CATALOG_PATH)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--post-id", type=int, action="append", default=None,
                        help="Sync only a selected official post id; repeatable. Full corpus when omitted.")
    parser.add_argument("--sleep", type=float, default=0.20)
    parser.add_argument("--timeout", type=float, default=20.0)
    args = parser.parse_args()

    result = sync_knowledge(
        catalog_path=args.catalog,
        db_path=args.db,
        selected_post_ids=set(args.post_id) if args.post_id else None,
        sleep_seconds=args.sleep,
        timeout=args.timeout,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
