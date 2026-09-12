"""Private local FX-Clover knowledge cache.

Fetches official article bodies from catalog URLs and stores them only in a
local SQLite database under runtime_private/. Article bodies are intentionally
never written to tracked repository files. No trading or order functionality.
"""

from __future__ import annotations

import hashlib
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sqlite3
import time
from typing import Callable, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
CATALOG_PATH = ROOT / "knowledge" / "poconical_post_catalog.json"
DEFAULT_DB_PATH = ROOT / "runtime_private" / "fxclover_knowledge.sqlite3"
USER_AGENT = "FX-Entry-Lab-Private-Knowledge/1.0 (+local-only; source-grounded)"
OFFICIAL_HOSTS = {"fx-clover.com", "www.fx-clover.com"}
BLOCK_TAGS = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "br", "blockquote", "tr"}
SKIP_TAGS = {"script", "style", "noscript", "svg"}


class EntryContentParser(HTMLParser):
    """Extract only the WordPress article body's `entry-content` div."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.capture = False
        self.depth = 0
        self.skip_depth = 0
        self.parts: list[str] = []

    @staticmethod
    def _classes(attrs: list[tuple[str, str | None]]) -> set[str]:
        value = next((v for k, v in attrs if k == "class"), "") or ""
        return set(value.split())

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if not self.capture:
            if tag == "div" and "entry-content" in self._classes(attrs):
                self.capture = True
                self.depth = 1
            return

        if tag == "div":
            self.depth += 1
        if tag in SKIP_TAGS:
            self.skip_depth += 1
            return
        if self.skip_depth == 0 and tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if not self.capture:
            return
        if tag in SKIP_TAGS and self.skip_depth:
            self.skip_depth -= 1
            return
        if self.skip_depth == 0 and tag in BLOCK_TAGS:
            self.parts.append("\n")
        if tag == "div":
            self.depth -= 1
            if self.depth <= 0:
                self.capture = False
                self.depth = 0

    def handle_data(self, data: str) -> None:
        if self.capture and self.skip_depth == 0:
            self.parts.append(data)


def normalize_text(text: str) -> str:
    text = unescape(text).replace("\u00a0", " ")
    lines: list[str] = []
    for raw in text.splitlines():
        line = re.sub(r"[\t\r\f\v ]+", " ", raw).strip()
        if line and (not lines or line != lines[-1]):
            lines.append(line)
    return "\n".join(lines).strip()


def extract_article_text(html: str) -> str:
    parser = EntryContentParser()
    parser.feed(html)
    text = normalize_text("".join(parser.parts))
    if not text:
        raise ValueError("entry-content article body was not found")
    return text


def official_post_id(url: str) -> int:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc.lower() not in OFFICIAL_HOSTS:
        raise ValueError(f"non-official source URL: {url}")
    values = parse_qs(parsed.query).get("p", [])
    if len(values) != 1 or not values[0].isdigit():
        raise ValueError(f"invalid official post URL: {url}")
    return int(values[0])


def fetch_html(url: str, *, timeout: float = 20.0, attempts: int = 3) -> str:
    official_post_id(url)
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"})
            with urlopen(request, timeout=timeout) as response:  # nosec B310 - official host validated above
                charset = response.headers.get_content_charset() or "utf-8"
                return response.read().decode(charset, errors="replace")
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            last_error = exc
            if attempt < attempts:
                time.sleep(float(attempt))
    assert last_error is not None
    raise last_error


def chunk_text(text: str, *, target_chars: int = 1200, overlap_chars: int = 180) -> list[str]:
    if target_chars < 300 or overlap_chars < 0 or overlap_chars >= target_chars:
        raise ValueError("invalid chunk sizing")
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + target_chars)
        if end < len(text):
            boundary = text.rfind("\n", start + target_chars // 2, end)
            if boundary > start:
                end = boundary
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(start + 1, end - overlap_chars)
    return chunks


def connect_db(path: Path) -> tuple[sqlite3.Connection, bool]:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS articles (
            post_id INTEGER PRIMARY KEY,
            url TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            published_date TEXT,
            article_text TEXT NOT NULL,
            content_sha256 TEXT NOT NULL,
            fetched_at_utc TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS chunks (
            post_id INTEGER NOT NULL,
            chunk_index INTEGER NOT NULL,
            text TEXT NOT NULL,
            PRIMARY KEY (post_id, chunk_index),
            FOREIGN KEY (post_id) REFERENCES articles(post_id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """
    )
    fts5 = True
    try:
        conn.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts "
            "USING fts5(text, post_id UNINDEXED, chunk_index UNINDEXED, tokenize='unicode61')"
        )
    except sqlite3.OperationalError as exc:
        if "fts5" not in str(exc).lower():
            raise
        fts5 = False
    conn.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('fts5',?)", ("true" if fts5 else "false",))
    conn.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('orders_enabled','false')")
    conn.commit()
    return conn, fts5


def load_catalog(path: Path = CATALOG_PATH) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    posts = payload.get("posts", [])
    if not posts:
        raise ValueError("official catalog is empty")
    seen: set[int] = set()
    for post in posts:
        post_id = int(post["post_id"])
        if post_id in seen:
            raise ValueError(f"duplicate catalog post_id: {post_id}")
        seen.add(post_id)
        if official_post_id(str(post["url"])) != post_id:
            raise ValueError(f"post id / URL mismatch: {post_id}")
    return posts


def sync_knowledge(
    *,
    catalog_path: Path = CATALOG_PATH,
    db_path: Path = DEFAULT_DB_PATH,
    fetcher: Callable[..., str] = fetch_html,
    selected_post_ids: set[int] | None = None,
    sleep_seconds: float = 0.20,
    timeout: float = 20.0,
) -> dict:
    posts = load_catalog(catalog_path)
    if selected_post_ids is not None:
        known = {int(post["post_id"]) for post in posts}
        unknown = selected_post_ids - known
        if unknown:
            raise ValueError(f"post ids not present in official catalog: {sorted(unknown)}")
        posts = [post for post in posts if int(post["post_id"]) in selected_post_ids]

    conn, fts5 = connect_db(db_path)
    fetched: list[int] = []
    errors: list[dict] = []
    try:
        for index, post in enumerate(posts):
            post_id = int(post["post_id"])
            url = str(post["url"])
            try:
                html = fetcher(url, timeout=timeout)
                text = extract_article_text(html)
                if len(text) < 80:
                    raise ValueError(f"article body suspiciously short: {len(text)} chars")
                digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
                conn.execute(
                    """INSERT INTO articles(post_id,url,title,published_date,article_text,content_sha256,fetched_at_utc)
                       VALUES(?,?,?,?,?,?,CURRENT_TIMESTAMP)
                       ON CONFLICT(post_id) DO UPDATE SET
                         url=excluded.url,title=excluded.title,published_date=excluded.published_date,
                         article_text=excluded.article_text,content_sha256=excluded.content_sha256,
                         fetched_at_utc=CURRENT_TIMESTAMP""",
                    (post_id, url, str(post.get("title", "")), post.get("published_or_archive_date"), text, digest),
                )
                conn.execute("DELETE FROM chunks WHERE post_id=?", (post_id,))
                if fts5:
                    conn.execute("DELETE FROM chunks_fts WHERE post_id=?", (post_id,))
                for chunk_index, chunk in enumerate(chunk_text(text)):
                    conn.execute("INSERT INTO chunks(post_id,chunk_index,text) VALUES(?,?,?)", (post_id, chunk_index, chunk))
                    if fts5:
                        conn.execute(
                            "INSERT INTO chunks_fts(text,post_id,chunk_index) VALUES(?,?,?)",
                            (chunk, post_id, chunk_index),
                        )
                conn.commit()
                fetched.append(post_id)
            except Exception as exc:  # preserve other articles, but fail the overall sync below
                errors.append({"post_id": post_id, "url": url, "error": f"{type(exc).__name__}: {exc}"})
            if sleep_seconds and index + 1 < len(posts):
                time.sleep(sleep_seconds)

        catalog_count = len(load_catalog(catalog_path))
        article_count = int(conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0])
        chunk_count = int(conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0])
        conn.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('catalog_count',?)", (str(catalog_count),))
        conn.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('article_count',?)", (str(article_count),))
        conn.commit()
    finally:
        conn.close()

    result = {
        "requested_count": len(posts),
        "fetched_count": len(fetched),
        "catalog_count": catalog_count,
        "db_article_count": article_count,
        "db_chunk_count": chunk_count,
        "fts5": fts5,
        "errors": errors,
        "db_path": str(db_path),
        "storage_policy": "PRIVATE_LOCAL_ONLY_NOT_GIT_TRACKED",
        "rule_promotion_allowed": False,
        "orders_enabled": False,
    }
    if errors:
        raise RuntimeError(json.dumps(result, ensure_ascii=False))
    if selected_post_ids is None and article_count != catalog_count:
        raise RuntimeError(
            f"INCOMPLETE_CORPUS: DB has {article_count} articles but catalog has {catalog_count}"
        )
    return result


def _fts_query(query: str) -> str:
    terms = [part for part in re.split(r"\s+", query.strip()) if part]
    if not terms:
        raise ValueError("query must not be empty")
    return " OR ".join('"' + term.replace('"', '""') + '"' for term in terms)


def search_knowledge(db_path: Path, query: str, *, limit: int = 8, max_chars: int = 700) -> list[dict]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        has_fts = conn.execute("SELECT value FROM meta WHERE key='fts5'").fetchone()
        fts5 = bool(has_fts and has_fts[0] == "true")
        if fts5:
            rows = conn.execute(
                """SELECT f.post_id, f.chunk_index, f.text, a.url, a.title, a.published_date,
                          bm25(chunks_fts) AS rank
                   FROM chunks_fts AS f JOIN articles AS a ON a.post_id=CAST(f.post_id AS INTEGER)
                   WHERE chunks_fts MATCH ? ORDER BY rank LIMIT ?""",
                (_fts_query(query), int(limit)),
            ).fetchall()
        else:
            terms = [part for part in re.split(r"\s+", query.strip()) if part]
            clauses = " OR ".join("c.text LIKE ?" for _ in terms)
            params: list[object] = [f"%{term}%" for term in terms]
            params.append(int(limit))
            rows = conn.execute(
                f"""SELECT c.post_id,c.chunk_index,c.text,a.url,a.title,a.published_date,0 AS rank
                    FROM chunks c JOIN articles a ON a.post_id=c.post_id
                    WHERE {clauses} LIMIT ?""",
                params,
            ).fetchall()
        return [
            {
                "post_id": int(row["post_id"]),
                "chunk_index": int(row["chunk_index"]),
                "title": row["title"],
                "published_date": row["published_date"],
                "url": row["url"],
                "excerpt": str(row["text"])[:max_chars],
                "rank": float(row["rank"] or 0),
            }
            for row in rows
        ]
    finally:
        conn.close()
