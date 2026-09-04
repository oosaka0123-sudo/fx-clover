import json
from pathlib import Path
import tempfile
import unittest

from build_poconical_review_queue import build_queue, classify_title, priority_for


class ReviewQueueTests(unittest.TestCase):
    def test_title_scoring_is_research_triage(self):
        score, topics, reasons = classify_title("右肩とDMA3-3 エントリーのタイミング")
        self.assertGreaterEqual(score, 8)
        self.assertIn("right_shoulder_formation", topics)
        self.assertIn("dma_ma", topics)
        self.assertIn("entry_initial_move", topics)
        self.assertTrue(reasons)

    def test_priority_thresholds(self):
        self.assertEqual(priority_for(9, "UNREVIEWED"), "P0")
        self.assertEqual(priority_for(5, "UNREVIEWED"), "P1")
        self.assertEqual(priority_for(3, "UNREVIEWED"), "P2")
        self.assertEqual(priority_for(0, "UNREVIEWED"), "P3")
        self.assertEqual(priority_for(99, "EVIDENCE_REVIEWED"), "DONE")
        self.assertEqual(priority_for(0, "CURRICULUM_INDEXED_NOT_RULE_REVIEWED"), "P0")

    def test_queue_status_and_no_rule_promotion(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            catalog = root / "catalog.json"
            evidence = root / "evidence.json"
            curriculum = root / "curriculum.json"
            catalog.write_text(json.dumps({
                "posts": [
                    {"post_id": 1, "url": "https://fx-clover.com/?p=1", "title": "既読", "published_or_archive_date": "2020-01-01", "source_archive_page": 1},
                    {"post_id": 2, "url": "https://fx-clover.com/?p=2", "title": "マスター講座 環境認識", "published_or_archive_date": "2020-01-02", "source_archive_page": 1},
                    {"post_id": 3, "url": "https://fx-clover.com/?p=3", "title": "右肩 DMA エントリー", "published_or_archive_date": "2020-01-03", "source_archive_page": 1},
                    {"post_id": 4, "url": "https://fx-clover.com/?p=4", "title": "雑記", "published_or_archive_date": "2020-01-04", "source_archive_page": 1},
                ]
            }), encoding="utf-8")
            evidence.write_text(json.dumps({"url": "https://fx-clover.com/?p=1"}), encoding="utf-8")
            curriculum.write_text(json.dumps({"blog_url": "https://fx-clover.com/?p=2"}), encoding="utf-8")

            queue = build_queue(catalog, [evidence], curriculum)
            by_id = {item["post_id"]: item for item in queue["items"]}

            self.assertEqual(by_id[1]["review_status"], "EVIDENCE_REVIEWED")
            self.assertEqual(by_id[1]["priority"], "DONE")
            self.assertEqual(by_id[2]["review_status"], "CURRICULUM_INDEXED_NOT_RULE_REVIEWED")
            self.assertEqual(by_id[2]["priority"], "P0")
            self.assertEqual(by_id[3]["review_status"], "UNREVIEWED")
            self.assertIn(by_id[3]["priority"], {"P0", "P1"})
            self.assertEqual(by_id[4]["priority"], "P3")
            self.assertTrue(all(item["rule_promotion_allowed"] is False for item in queue["items"]))
            self.assertFalse(queue["orders_enabled"])
            self.assertEqual({item["review_order"] for item in queue["items"]}, {1, 2, 3, 4})


if __name__ == "__main__":
    unittest.main()
