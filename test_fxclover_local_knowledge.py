import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from fxclover_local_knowledge import (
    chunk_text,
    extract_article_text,
    search_knowledge,
    sync_knowledge,
)


SAMPLE_HTML = r'''
<html><body>
<nav>MENU MUST NOT ENTER KNOWLEDGE</nav>
<h1>Sample title</h1>
<div class="entry-content">
  <p>上位環境を確認して DMA を使います。</p>
  <div><h2>右肩</h2><p>フォーメーションの右肩まで待ちます。</p></div>
  <script>SECRET_NOISE = 'must not be indexed';</script>
  <p>次の障害までの伸びしろを確認します。</p>
</div>
<section>RELATED POSTS MUST NOT ENTER KNOWLEDGE</section>
</body></html>
'''


class LocalKnowledgeTests(unittest.TestCase):
    def test_extracts_only_entry_content(self):
        text = extract_article_text(SAMPLE_HTML)
        self.assertIn("DMA", text)
        self.assertIn("右肩", text)
        self.assertIn("伸びしろ", text)
        self.assertNotIn("MENU MUST", text)
        self.assertNotIn("RELATED POSTS", text)
        self.assertNotIn("SECRET_NOISE", text)

    def test_chunking_has_content_and_terminates(self):
        text = "\n".join(f"段落 {i} DMA 右肩" for i in range(300))
        chunks = chunk_text(text, target_chars=500, overlap_chars=50)
        self.assertGreater(len(chunks), 2)
        self.assertTrue(all(chunk.strip() for chunk in chunks))

    def test_sync_and_search_private_sqlite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            catalog = root / "catalog.json"
            db = root / "private.sqlite3"
            catalog.write_text(json.dumps({
                "posts": [{
                    "post_id": 123,
                    "url": "https://fx-clover.com/?p=123",
                    "title": "Sample official post",
                    "published_or_archive_date": "2022-01-01"
                }]
            }, ensure_ascii=False), encoding="utf-8")

            requested = []
            def fake_fetcher(url, *, timeout):
                requested.append((url, timeout))
                return SAMPLE_HTML

            result = sync_knowledge(
                catalog_path=catalog,
                db_path=db,
                fetcher=fake_fetcher,
                sleep_seconds=0,
                timeout=1,
            )
            self.assertEqual(result["catalog_count"], 1)
            self.assertEqual(result["db_article_count"], 1)
            self.assertEqual(result["fetched_count"], 1)
            self.assertFalse(result["orders_enabled"])
            self.assertEqual(len(requested), 1)

            conn = sqlite3.connect(db)
            try:
                stored = conn.execute("SELECT article_text FROM articles WHERE post_id=123").fetchone()[0]
            finally:
                conn.close()
            self.assertNotIn("MENU MUST", stored)

            hits = search_knowledge(db, "DMA", limit=5)
            self.assertTrue(hits)
            self.assertEqual(hits[0]["post_id"], 123)
            self.assertEqual(hits[0]["url"], "https://fx-clover.com/?p=123")


if __name__ == "__main__":
    unittest.main()
