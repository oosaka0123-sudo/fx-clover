"""Build a metadata-only catalog of official FX-Clover category posts.

This tool intentionally does NOT persist article bodies.  The catalog is a
retrieval queue for later source-by-source review by an AI or a human.

No broker connectivity. No trading/order functionality.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from html import unescape
import json
from pathlib import Path
import re
import time
from typing import Callable
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
from urllib.request import Request, urlopen


BASE_URL = "https://fx-clover.com/"
DEFAULT_CATEGORY = 526
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "knowledge" / "poconical_post_catalog.json"
USER_AGENT = "FX-Clover-Knowledge-Catalog/1.0 (+metadata-only; no article-body storage)"

# Category archive titles are currently rendered as h3 links.  h5 is
# deliberately excluded because the site footer contains unrelated recent posts.
HEADING_LINK_RE = re.compile(
    r"<h(?:2|3)\b[^>]*>\s*<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>.*?</h(?:2|3)>",
    re.IGNORECASE | re.DOTALL,
)
NEXT_HEADING_RE = re.compile(r"<h(?:2|3)\b", re.IGNORECASE)
TAG_RE = re.compile(r"<[^>]+>")
DATE_RE = re.compile(r"(?P<y>20\d{2})[/-](?P<m>\d{1,2})[/-](?P<d>\d{1,2})")


def category_url(category_id: int, page: int) -> str:
    """Return the WordPress category archive URL for a 1-based page."""
    if page < 1:
        raise ValueError("page must be >= 1")
    query = {"cat": str(category_id)}
    if page > 1:
        query["paged"] = str(page)
    parsed = urlparse(BASE_URL)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", urlencode(query), ""))


def _clean_title(raw: str) -> str:
    text = TAG_RE.sub(" ", raw)
    return " ".join(unescape(text).split())


def _post_id(url: str) -> int | None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return None
    if parsed.netloc.lower() not in {"fx-clover.com", "www.fx-clover.com"}:
        return None
    values = parse_qs(parsed.query).get("p", [])
    if not values or not values[0].isdigit():
        return None
    return int(values[0])


def _nearby_date(html: str, end_pos: int) -> str | None:
    # Search only inside this post's archive block.  Never borrow a date from
    # the next h2/h3 title when the current entry does not expose one.
    tail = html[end_pos : end_pos + 800]
    next_heading = NEXT_HEADING_RE.search(tail)
    if next_heading:
        tail = tail[: next_heading.start()]
    window = TAG_RE.sub(" ", tail)
    match = DATE_RE.search(unescape(window))
    if not match:
        return None
    y, m, d = (int(match.group(name)) for name in ("y", "m", "d"))
    try:
        return datetime(y, m, d).date().isoformat()
    except ValueError:
        return None


def extract_posts(html: str, *, category_id: int, source_page: int) -> list[dict]:
    """Extract metadata for article links from one category archive page."""
    posts: list[dict] = []
    for match in HEADING_LINK_RE.finditer(html):
        url = unescape(match.group(1)).strip()
        post_id = _post_id(url)
        if post_id is None:
            continue
        title = _clean_title(match.group(2))
        if not title:
            continue
        posts.append(
            {
                "post_id": post_id,
                "url": f"https://fx-clover.com/?p={post_id}",
                "title": title,
                "published_or_archive_date": _nearby_date(html, match.end()),
                "category_id": category_id,
                "source_archive_page": source_page,
                "classification": "OFFICIAL_BLOG_CATALOG_ENTRY_UNREVIEWED",
                "rule_promotion_allowed": False,
            }
        )
    return posts


def fetch_text(url: str, *, timeout: float = 20.0) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"})
    with urlopen(request, timeout=timeout) as response:  # nosec B310 - fixed official host is validated downstream
        content_type = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(content_type, errors="replace")


def sync_category(
    *,
    category_id: int = DEFAULT_CATEGORY,
    max_pages: int = 30,
    timeout: float = 20.0,
    sleep_seconds: float = 0.25,
    fetcher: Callable[..., str] = fetch_text,
) -> dict:
    """Crawl category archive pages and return a deduplicated metadata catalog.

    Crawling stops when a page yields no new post IDs.  This also protects
    against WordPress redirecting an out-of-range page back to page 1.
    """
    if max_pages < 1:
        raise ValueError("max_pages must be >= 1")

    seen: set[int] = set()
    catalog: list[dict] = []
    pages_scanned = 0

    for page in range(1, max_pages + 1):
        url = category_url(category_id, page)
        html = fetcher(url, timeout=timeout)
        page_posts = extract_posts(html, category_id=category_id, source_page=page)
        new_posts = [post for post in page_posts if post["post_id"] not in seen]
        if not new_posts:
            break
        for post in new_posts:
            seen.add(post["post_id"])
            catalog.append(post)
        pages_scanned = page
        if sleep_seconds and page < max_pages:
            time.sleep(sleep_seconds)

    return {
        "schema_version": "1.0",
        "classification": "OFFICIAL_BLOG_METADATA_CATALOG",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "base_url": BASE_URL,
        "category_id": category_id,
        "category_url": category_url(category_id, 1),
        "pages_scanned": pages_scanned,
        "post_count": len(catalog),
        "storage_policy": "metadata_only_no_article_body",
        "rule_policy": "catalog entries are unreviewed sources and cannot become production rules without source review",
        "orders_enabled": False,
        "posts": catalog,
    }


def write_catalog(catalog: dict, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--category", type=int, default=DEFAULT_CATEGORY)
    parser.add_argument("--max-pages", type=int, default=30)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--sleep", type=float, default=0.25)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--dry-run", action="store_true", help="Fetch and print summary without writing a file")
    args = parser.parse_args()

    catalog = sync_category(
        category_id=args.category,
        max_pages=args.max_pages,
        timeout=args.timeout,
        sleep_seconds=args.sleep,
    )
    if not args.dry_run:
        write_catalog(catalog, args.output)
    print(
        json.dumps(
            {
                "category_id": catalog["category_id"],
                "pages_scanned": catalog["pages_scanned"],
                "post_count": catalog["post_count"],
                "output": None if args.dry_run else str(args.output),
                "orders_enabled": False,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
