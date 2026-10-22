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

    def test_bible_ligature_substitutions_are_corrected_across_the_tested_passage(self):
        root = Path(__file__).resolve().parents[1]
        with gzip.open(root / "data-v47" / "book-335.json.gz", "rt", encoding="utf-8") as handle:
            shard = json.load(handle)
        pages = {item["page"]: item["text"] for item in shard["pages"]
                 if item.get("page") in {5542, 5546, 5547, 5548}}
        normalized = {number: " ".join(text.split()) for number, text in pages.items()}
        self.assertIn("Little children", normalized[5542])
        self.assertIn("practices righteousness", normalized[5542])
        self.assertIn("only begotten Son", normalized[5546])
        self.assertIn("propitiation for our sins", normalized[5546])
        self.assertIn("at any time", normalized[5546])
        self.assertIn("testify that the Father", normalized[5547])
        self.assertIn("who is begotten of Him", normalized[5548])
        for text in pages.values():
            self.assertNotRegex(text, r"(?:Ɵ|Ʃ)")

        with (root / "reader-fingerprints-v1" / "books" / "335" / "173.json").open(encoding="utf-8") as handle:
            fingerprint = json.load(handle)
        for page_number, text in pages.items():
            record = next(item for item in fingerprint["pages"] if item["page"] == page_number)
            raw = text.encode("utf-8")
            self.assertEqual(record["utf8Bytes"], len(raw))
            self.assertEqual(record["sha256"], hashlib.sha256(raw).hexdigest())

    def test_thucydides_truce_duration_ocr_is_corrected_and_fingerprinted(self):
        root = Path(__file__).resolve().parents[1]
        with gzip.open(root / "data-v47" / "book-152.json.gz", "rt", encoding="utf-8") as handle:
            shard = json.load(handle)
        page = next(item for item in shard["pages"] if item.get("page") == 38)
        self.assertIn("thirty years' truce", page["text"])
        self.assertNotIn("thiry years' truce", page["text"])

        with (root / "reader-fingerprints-v1" / "books" / "152" / "1.json").open(encoding="utf-8") as handle:
            fingerprint = json.load(handle)
        record = next(item for item in fingerprint["pages"] if item["page"] == 38)
        raw = page["text"].encode("utf-8")
        self.assertEqual(record["utf8Bytes"], len(raw))
        self.assertEqual(record["sha256"], hashlib.sha256(raw).hexdigest())


if __name__ == "__main__":
    unittest.main()
