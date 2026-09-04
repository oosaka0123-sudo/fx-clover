"""Validate the committed metadata-only official Poconical post catalog.

This validator enforces source/governance boundaries only. It does not inspect
or change WATCH/READY/TRIGGER logic and has no broker/order connectivity.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parent
DEFAULT_CATALOG = ROOT / "knowledge" / "poconical_post_catalog.json"
EXPECTED_CATEGORY = 526
EXPECTED_CLASSIFICATION = "OFFICIAL_BLOG_CATALOG_ENTRY_UNREVIEWED"


def validate(path: Path = DEFAULT_CATALOG) -> dict:
    errors: list[str] = []
    if not path.is_file():
        return {
            "status": "FAIL",
            "errors": [f"catalog not found: {path}"],
            "post_count": 0,
            "orders_enabled": False,
        }

    data = json.loads(path.read_text(encoding="utf-8"))
    posts = data.get("posts")
    if not isinstance(posts, list) or not posts:
        errors.append("posts must be a non-empty list")
        posts = []

    if data.get("classification") != "OFFICIAL_BLOG_METADATA_CATALOG":
        errors.append("unexpected catalog classification")
    if data.get("category_id") != EXPECTED_CATEGORY:
        errors.append("unexpected category_id")
    if data.get("storage_policy") != "metadata_only_no_article_body":
        errors.append("unexpected storage_policy")
    if data.get("orders_enabled") is not False:
        errors.append("orders_enabled must be false")
    if data.get("post_count") != len(posts):
        errors.append("post_count does not match posts length")

    seen: set[int] = set()
    max_page = 0
    for index, post in enumerate(posts, start=1):
        prefix = f"posts[{index}]"
        post_id = post.get("post_id")
        url = post.get("url", "")
        parsed = urlparse(url)
        query_id = parse_qs(parsed.query).get("p", [None])[0]
        page = post.get("source_archive_page")

        if not isinstance(post_id, int) or post_id <= 0:
            errors.append(f"{prefix}: invalid post_id")
        elif post_id in seen:
            errors.append(f"{prefix}: duplicate post_id {post_id}")
        else:
            seen.add(post_id)

        if parsed.scheme != "https" or parsed.netloc != "fx-clover.com":
            errors.append(f"{prefix}: non-official URL {url}")
        if str(post_id) != str(query_id):
            errors.append(f"{prefix}: post_id/url mismatch")
        if post.get("category_id") != EXPECTED_CATEGORY:
            errors.append(f"{prefix}: category mismatch")
        if not isinstance(page, int) or page < 1:
            errors.append(f"{prefix}: invalid source_archive_page")
        else:
            max_page = max(max_page, page)
        if post.get("classification") != EXPECTED_CLASSIFICATION:
            errors.append(f"{prefix}: unexpected classification")
        if post.get("rule_promotion_allowed") is not False:
            errors.append(f"{prefix}: rule promotion must remain false")
        if "body" in post or "content" in post:
            errors.append(f"{prefix}: article body/content must not be stored")
        if not str(post.get("title", "")).strip():
            errors.append(f"{prefix}: title is empty")

    if posts and data.get("pages_scanned") != max_page:
        errors.append("pages_scanned does not match highest source_archive_page")

    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "post_count": len(posts),
        "pages_scanned": data.get("pages_scanned"),
        "orders_enabled": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    args = parser.parse_args()
    result = validate(args.catalog)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
