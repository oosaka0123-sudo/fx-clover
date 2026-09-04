import unittest

from sync_fxclover_catalog import category_url, extract_posts, sync_category


PAGE1 = r'''
<html><body>
<h3><a href="https://fx-clover.com/?p=9001">First &amp; Test</a></h3>
<div>2023/07/15 &nbsp; summary</div>
<h3 class="entry-title"><a href="https://fx-clover.com/?p=9000"><span>Second</span> Post</a></h3>
<div>2023/07/01</div>
<h5><a href="https://fx-clover.com/?p=9999">Footer recent post must be ignored</a></h5>
</body></html>
'''

PAGE2 = r'''
<html><body>
<h3><a href="https://fx-clover.com/?p=9000">Second Post duplicate</a></h3><div>2023/07/01</div>
<h3><a href="https://fx-clover.com/?p=8999">Third Post</a></h3><div>2023-06-24</div>
</body></html>
'''

PAGE3_NO_NEW = r'''
<html><body>
<h3><a href="https://fx-clover.com/?p=9001">First Test again</a></h3><div>2023/07/15</div>
</body></html>
'''


class CatalogParserTests(unittest.TestCase):
    def test_category_url(self):
        self.assertEqual(category_url(526, 1), "https://fx-clover.com/?cat=526")
        self.assertEqual(category_url(526, 2), "https://fx-clover.com/?cat=526&paged=2")
        with self.assertRaises(ValueError):
            category_url(526, 0)

    def test_extract_posts_metadata_only(self):
        posts = extract_posts(PAGE1, category_id=526, source_page=1)
        self.assertEqual([p["post_id"] for p in posts], [9001, 9000])
        self.assertEqual(posts[0]["title"], "First & Test")
        self.assertEqual(posts[0]["published_or_archive_date"], "2023-07-15")
        self.assertEqual(posts[1]["title"], "Second Post")
        self.assertNotIn("body", posts[0])
        self.assertFalse(posts[0]["rule_promotion_allowed"])

    def test_missing_date_does_not_borrow_next_post_date(self):
        html = r'''
        <h3><a href="https://fx-clover.com/?p=9101">No Date Here</a></h3>
        <div>summary without a date</div>
        <h3><a href="https://fx-clover.com/?p=9100">Next Post</a></h3>
        <div>2024/01/02</div>
        '''
        posts = extract_posts(html, category_id=526, source_page=1)
        self.assertIsNone(posts[0]["published_or_archive_date"])
        self.assertEqual(posts[1]["published_or_archive_date"], "2024-01-02")

    def test_external_and_non_post_links_are_ignored(self):
        html = r'''
        <h3><a href="https://example.com/?p=1">external</a></h3>
        <h3><a href="https://fx-clover.com/?cat=526">category</a></h3>
        <h3><a href="https://fx-clover.com/?p=abc">bad id</a></h3>
        '''
        self.assertEqual(extract_posts(html, category_id=526, source_page=1), [])

    def test_sync_deduplicates_and_stops_when_no_new_posts(self):
        requested = []

        def fake_fetcher(url, *, timeout):
            requested.append((url, timeout))
            if "paged=2" in url:
                return PAGE2
            if "paged=3" in url:
                return PAGE3_NO_NEW
            return PAGE1

        catalog = sync_category(
            category_id=526,
            max_pages=20,
            timeout=1.0,
            sleep_seconds=0,
            fetcher=fake_fetcher,
        )
        self.assertEqual([p["post_id"] for p in catalog["posts"]], [9001, 9000, 8999])
        self.assertEqual(catalog["pages_scanned"], 2)
        self.assertEqual(catalog["post_count"], 3)
        self.assertEqual(len(requested), 3)
        self.assertEqual(catalog["storage_policy"], "metadata_only_no_article_body")
        self.assertFalse(catalog["orders_enabled"])


if __name__ == "__main__":
    unittest.main()
