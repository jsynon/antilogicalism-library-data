import gzip
import hashlib
import json
import unittest
from pathlib import Path


class V47TranscriptionCorrectionTests(unittest.TestCase):
    def test_hawking_page_49_corrected_text_matches_trusted_fingerprint(self):
        root = Path(__file__).resolve().parents[1]
        with gzip.open(root / "data-v47" / "book-102.json.gz", "rt", encoding="utf-8") as handle:
            shard = json.load(handle)
        page = next(item for item in shard["pages"] if item.get("page") == 49)
        self.assertIn("a black hole still exerts a gravitational force on nearby objects", page["text"])
        self.assertNotIn("gravitational fierce", page["text"])

        with (root / "reader-fingerprints-v1" / "books" / "102" / "1.json").open(encoding="utf-8") as handle:
            fingerprint = json.load(handle)
        record = next(item for item in fingerprint["pages"] if item["page"] == 49)
        self.assertEqual(record["sha256"], hashlib.sha256(page["text"].encode("utf-8")).hexdigest())


if __name__ == "__main__":
    unittest.main()
