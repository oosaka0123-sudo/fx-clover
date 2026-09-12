"""Search the private local FX-Clover knowledge cache and return source-grounded excerpts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from fxclover_local_knowledge import DEFAULT_DB_PATH, search_knowledge


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--max-chars", type=int, default=700)
    args = parser.parse_args()

    results = search_knowledge(args.db, args.query, limit=args.limit, max_chars=args.max_chars)
    print(json.dumps({
        "query": args.query,
        "result_count": len(results),
        "results": results,
        "storage_policy": "PRIVATE_LOCAL_ONLY_NOT_GIT_TRACKED",
        "rule_promotion_allowed": False,
        "orders_enabled": False,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
