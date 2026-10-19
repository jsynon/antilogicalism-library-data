import gzip
import json
import tempfile
import unittest
from pathlib import Path
from build_reader_collection import build_collection, load_cohort


class CollectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "data"
        self.root.mkdir()
        self.out = Path(self.temp.name) / "fingerprints"
        self.pdf = "https://drive.google.com/file/d/SomeValidLongPdfIdentifier1234/view"
        self.manifest = {"version": 47, "books": {
            "7": {"title": "Nicomachean Ethics — Aristotle", "drive_url": self.pdf},
            "529": {"title": "Origin of Species — Darwin", "drive_url": self.pdf}},
            "page_books": [7, 7, 529]}
        self.books = {
            7: [{"page": 1, "id": 0, "text": "Virtue through practice.\n" * 10},
                {"page": 33, "id": 1, "text": "Practical reason and happiness.\n" * 10}],
            529: [{"page": 5, "id": 2, "text": "Natural selection operates over generations.\n" * 10}]}
        self.save()

    def save(self):
        with gzip.open(self.root / "manifest.json.gz", "wt", encoding="utf-8") as f:
            json.dump(self.manifest, f)
        for book, pages in self.books.items():
            with gzip.open(self.root / f"book-{book}.json.gz", "wt", encoding="utf-8") as f:
                json.dump({"pages": pages}, f)

    def test_full_books_and_exact_hashes(self):
        result = build_collection(self.root, self.out, [7, 529])
        self.assertEqual(set(result["books"]), {"7", "529"})
        self.assertEqual(result["books"]["7"]["chunks"], 2)
        packet = json.loads((self.out / "books/7/1.json").read_text())
        self.assertEqual(packet["pages"][0]["page"], 33)
        self.assertEqual(packet["pages"][0]["globalPageId"], 1)
        import hashlib
        expected = hashlib.sha256(self.books[7][1]["text"].encode()).hexdigest()
        self.assertEqual(packet["pages"][0]["sha256"], expected)
        self.assertNotIn("text", packet["pages"][0])
        first = (self.out / "coverage-v1.json").read_bytes()
        build_collection(self.root, self.out, [7, 529])
        self.assertEqual((self.out / "coverage-v1.json").read_bytes(), first)

    def test_rejects_incorrect_page_ownership_before_publishing(self):
        self.manifest["page_books"][2] = 7
        self.save()
        with self.assertRaisesRegex(ValueError, "owner mismatch"):
            build_collection(self.root, self.out, [7, 529])
        self.assertFalse((self.out / "coverage-v1.json").exists())

    def test_oversized_page_reported_and_hashed_without_truncation(self):
        self.books[7][0]["text"] = "a" * 15000
        self.save()
        result = build_collection(self.root, self.out, [7])
        self.assertEqual(result["books"]["7"]["oversizedPages"], 1)
        page = json.loads((self.out / "books/7/0.json").read_text())["pages"][0]
        self.assertEqual(page["utf8Bytes"], 15000)

    def test_duplicate_pages_fail_closed(self):
        self.books[7].append({"page": 1, "id": 1, "text": "Another page"})
        self.save()
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            build_collection(self.root, self.out, [7])

    def test_cohort_loader_accepts_full_library_and_requires_unique_v47_selection(self):
        path = self.out / "cohort.json"
        ids = list(range(100, 228))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "schema": "antilogicalism-reader-cohort-v1",
            "libraryVersion": 47,
            "bookIds": ids,
        }), encoding="utf-8")
        self.assertEqual(load_cohort(path), ids)

        full_ids = list(range(2, 644))
        path.write_text(json.dumps({"schema":"antilogicalism-reader-cohort-v1",
            "libraryVersion":47,"bookIds":full_ids}), encoding="utf-8")
        self.assertEqual(len(load_cohort(path)), 642)

        for bad_ids, message in [
            (ids[:99], "100–644"),
            (list(range(1, 646)), "100–644"),
            (ids[:-1] + [ids[0]], "unique"),
            (ids[:-1] + ["not-a-book"], "positive integers"),
        ]:
            path.write_text(json.dumps({
                "schema": "antilogicalism-reader-cohort-v1",
                "libraryVersion": 47,
                "bookIds": bad_ids,
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, message):
                load_cohort(path)


if __name__ == "__main__":
    unittest.main()
