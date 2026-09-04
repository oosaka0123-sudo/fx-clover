"""Build a metadata-only prioritized review queue for official Poconical posts.

Priority is research triage only. Title/curriculum heuristics never promote a
trading rule and never change WATCH/READY/TRIGGER behavior.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
from typing import Any, Iterable
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parent
CATALOG = ROOT / "knowledge" / "poconical_post_catalog.json"
OUTPUT = ROOT / "knowledge" / "poconical_review_queue.json"

EVIDENCE_FILES = [
    ROOT / "knowledge" / "official_sources.json",
    ROOT / "knowledge" / "dma25x5_official_sources.json",
    ROOT / "knowledge" / "right_shoulder_official_sources.json",
    ROOT / "knowledge" / "p0_master_course_blog_review.json",
]
CURRICULUM_FILE = ROOT / "knowledge" / "poconical_curriculum.json"

POST_URL_RE = re.compile(r"^https://(?:www\.)?fx-clover\.com/\?p=(\d+)$")

# Explicit metadata-only triage heuristics. Weights represent review urgency,
# not trading importance or confidence.
TOPIC_RULES: dict[str, tuple[int, tuple[str, ...]]] = {
    "dma_ma": (4, ("dma", "ma", "移動平均", "3-3", "３の３", "25-5", "25×5", "サンド")),
    "right_shoulder_formation": (4, ("右肩", "フォーメーション", "wトップ", "ｗトップ", "ダブルトップ", "三尊")),
    "environment_timeframe": (4, ("環境", "上位", "時間足", "ゾーン", "レジスタンス", "サポート")),
    "fibonacci": (3, ("フィボ", "fibonacci", "fr", "fe")),
    "entry_initial_move": (3, ("エントリー", "タイミング", "初動", "お告げ")),
    "stop_exit": (3, ("損切", "決済", "利確", "ストップ", "出口")),
    "room_obstacle": (4, ("伸びしろ", "障害", "サンド", "余地")),
    "master_course": (5, ("マスター講座", "問題集", "理解度", "基礎", "ポコニカル")),
}


def _post_id_from_url(value: str) -> int | None:
    match = POST_URL_RE.match(value.strip())
    if match:
        return int(match.group(1))
    parsed = urlparse(value)
    if parsed.scheme in {"http", "https"} and parsed.netloc.lower() in {"fx-clover.com", "www.fx-clover.com"}:
        vals = parse_qs(parsed.query).get("p", [])
        if vals and vals[0].isdigit():
            return int(vals[0])
    return None


def _walk_urls(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for item in value.values():
            yield from _walk_urls(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_urls(item)
    elif isinstance(value, str) and "fx-clover.com" in value:
        yield value


def source_post_ids(path: Path) -> set[int]:
    data = json.loads(path.read_text(encoding="utf-8"))
    result: set[int] = set()
    for url in _walk_urls(data):
        post_id = _post_id_from_url(url)
        if post_id is not None:
            result.add(post_id)
    return result


def classify_title(title: str) -> tuple[int, list[str], list[str]]:
    lowered = title.casefold()
    score = 0
    topics: list[str] = []
    reasons: list[str] = []
    for topic, (weight, keywords) in TOPIC_RULES.items():
        matched = [keyword for keyword in keywords if keyword.casefold() in lowered]
        if matched:
            score += weight
            topics.append(topic)
            reasons.append(f"title:{topic} ({', '.join(matched)})")
    return score, topics, reasons


def priority_for(score: int, status: str) -> str:
    if status == "EVIDENCE_REVIEWED":
        return "DONE"
    if status == "CURRICULUM_INDEXED_NOT_RULE_REVIEWED":
        return "P0"
    if score >= 8:
        return "P0"
    if score >= 5:
        return "P1"
    if score >= 3:
        return "P2"
    return "P3"


def build_queue(
    catalog_path: Path = CATALOG,
    evidence_files: Iterable[Path] = EVIDENCE_FILES,
    curriculum_file: Path = CURRICULUM_FILE,
) -> dict:
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    posts = catalog.get("posts", [])

    evidence_ids: set[int] = set()
    evidence_sources: dict[int, list[str]] = {}
    for path in evidence_files:
        ids = source_post_ids(path)
        evidence_ids.update(ids)
        for post_id in ids:
            evidence_sources.setdefault(post_id, []).append(path.name)

    curriculum_ids = source_post_ids(curriculum_file)
    queue: list[dict] = []

    for post in posts:
        post_id = int(post["post_id"])
        title = str(post.get("title", ""))
        score, topics, reasons = classify_title(title)

        if post_id in evidence_ids:
            status = "EVIDENCE_REVIEWED"
            reasons = ["already represented in official evidence ledger"]
            score = 0
        elif post_id in curriculum_ids:
            status = "CURRICULUM_INDEXED_NOT_RULE_REVIEWED"
            score += 10
            reasons.insert(0, "official curriculum source; detailed rule extraction still pending")
            if "master_course" not in topics:
                topics.insert(0, "master_course")
        else:
            status = "UNREVIEWED"
            if not reasons:
                reasons = ["no unresolved-topic keyword in title; retain for complete corpus review"]

        queue.append({
            "post_id": post_id,
            "url": post["url"],
            "title": title,
            "published_or_archive_date": post.get("published_or_archive_date"),
            "source_archive_page": post.get("source_archive_page"),
            "review_status": status,
            "priority": priority_for(score, status),
            "priority_score": score,
            "matched_topics": topics,
            "priority_reasons": reasons,
            "evidence_files": sorted(evidence_sources.get(post_id, [])),
            "classification": "RESEARCH_REVIEW_QUEUE_METADATA_ONLY",
            "rule_promotion_allowed": False,
        })

    rank = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "DONE": 4}
    queue.sort(key=lambda item: (
        rank[item["priority"]],
        -int(item["priority_score"]),
        item.get("published_or_archive_date") or "9999-99-99",
        int(item["post_id"]),
    ))
    for index, item in enumerate(queue, start=1):
        item["review_order"] = index

    status_counts = Counter(item["review_status"] for item in queue)
    priority_counts = Counter(item["priority"] for item in queue)
    return {
        "schema_version": "1.0",
        "classification": "POCONICAL_METADATA_RESEARCH_REVIEW_QUEUE",
        "priority_policy": "metadata_only_research_triage_not_rule_promotion",
        "catalog_post_count": len(posts),
        "queue_post_count": len(queue),
        "status_counts": dict(sorted(status_counts.items())),
        "priority_counts": {key: priority_counts.get(key, 0) for key in ("P0", "P1", "P2", "P3", "DONE")},
        "evidence_files": [path.name for path in evidence_files],
        "curriculum_file": curriculum_file.name,
        "orders_enabled": False,
        "items": queue,
    }


def write_queue(queue: dict, output: Path = OUTPUT) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(queue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=CATALOG)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    queue = build_queue(catalog_path=args.catalog)
    write_queue(queue, args.output)
    print(json.dumps({
        "catalog_post_count": queue["catalog_post_count"],
        "queue_post_count": queue["queue_post_count"],
        "status_counts": queue["status_counts"],
        "priority_counts": queue["priority_counts"],
        "output": str(args.output),
        "orders_enabled": False,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
