"""Validate that the Poconical review queue exactly covers the official catalog."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CATALOG = ROOT / "knowledge" / "poconical_post_catalog.json"
QUEUE = ROOT / "knowledge" / "poconical_review_queue.json"
ALLOWED_STATUS = {"EVIDENCE_REVIEWED", "CURRICULUM_INDEXED_NOT_RULE_REVIEWED", "UNREVIEWED"}
ALLOWED_PRIORITY = {"P0", "P1", "P2", "P3", "DONE"}


def validate(catalog_path: Path = CATALOG, queue_path: Path = QUEUE) -> dict:
    errors: list[str] = []
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    queue = json.loads(queue_path.read_text(encoding="utf-8"))
    catalog_ids = [int(post["post_id"]) for post in catalog.get("posts", [])]
    items = queue.get("items", [])
    queue_ids = [int(item["post_id"]) for item in items]

    if queue.get("orders_enabled") is not False:
        errors.append("queue orders_enabled must be false")
    if queue.get("priority_policy") != "metadata_only_research_triage_not_rule_promotion":
        errors.append("unexpected priority_policy")
    if queue.get("catalog_post_count") != len(catalog_ids):
        errors.append("catalog_post_count mismatch")
    if queue.get("queue_post_count") != len(items):
        errors.append("queue_post_count mismatch")
    if len(queue_ids) != len(set(queue_ids)):
        errors.append("duplicate queue post IDs")
    if set(queue_ids) != set(catalog_ids):
        missing = sorted(set(catalog_ids) - set(queue_ids))
        extra = sorted(set(queue_ids) - set(catalog_ids))
        errors.append(f"catalog/queue drift missing={missing} extra={extra}")

    expected_orders = set(range(1, len(items) + 1))
    actual_orders = {int(item.get("review_order", 0)) for item in items}
    if actual_orders != expected_orders:
        errors.append("review_order must cover 1..N exactly once")

    catalog_by_id = {int(post["post_id"]): post for post in catalog.get("posts", [])}
    for item in items:
        post_id = int(item["post_id"])
        prefix = f"post {post_id}"
        source = catalog_by_id.get(post_id, {})
        if item.get("url") != source.get("url"):
            errors.append(f"{prefix}: URL mismatch")
        if item.get("title") != source.get("title"):
            errors.append(f"{prefix}: title mismatch")
        if item.get("review_status") not in ALLOWED_STATUS:
            errors.append(f"{prefix}: invalid review_status")
        if item.get("priority") not in ALLOWED_PRIORITY:
            errors.append(f"{prefix}: invalid priority")
        if item.get("review_status") == "EVIDENCE_REVIEWED" and item.get("priority") != "DONE":
            errors.append(f"{prefix}: evidence-reviewed item must be DONE")
        if item.get("review_status") != "EVIDENCE_REVIEWED" and not item.get("priority_reasons"):
            errors.append(f"{prefix}: non-reviewed item needs priority reason")
        if item.get("classification") != "RESEARCH_REVIEW_QUEUE_METADATA_ONLY":
            errors.append(f"{prefix}: unexpected classification")
        if item.get("rule_promotion_allowed") is not False:
            errors.append(f"{prefix}: rule promotion must remain false")
        if "body" in item or "content" in item:
            errors.append(f"{prefix}: article body/content prohibited")

    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "catalog_post_count": len(catalog_ids),
        "queue_post_count": len(items),
        "orders_enabled": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=CATALOG)
    parser.add_argument("--queue", type=Path, default=QUEUE)
    args = parser.parse_args()
    result = validate(args.catalog, args.queue)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
