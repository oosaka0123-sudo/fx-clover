import tempfile
from pathlib import Path
import unittest

from verify_distribution_v1_23 import EXPECTED, verify


class DistributionV123Tests(unittest.TestCase):
    def test_current_distribution_passes(self):
        self.assertEqual(verify(import_modules=False)["status"], "PASS")

    def test_missing_distribution_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(verify(Path(folder), import_modules=False)["status"], "FAIL")

    def test_changed_files_fail(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name in EXPECTED:
                (root / name).write_text("changed", encoding="utf-8")
            self.assertEqual(verify(root, import_modules=False)["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
