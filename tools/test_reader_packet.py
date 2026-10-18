import gzip
import json
import tempfile
import unittest
from pathlib import Path

from build_reader_packet import build_packet, write_packet

PDF_ID = "SomeValidPdf1234567890"
BOOK = 152


class ReaderPacketTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "data-v47"
        self.root.mkdir()
        self.manifest = {
            "version": 47,
            "books": {str(BOOK): {
                "title": "History — Thucydides",
                "drive_url": f"https://drive.google.com/file/d/{PDF_ID}/view",
            }},
            "page_books": [BOOK] * 3,
        }
        self.shard = {"pages": [
            {"id": 0, "page": 38, "text": "The immediate disputes were visible, but the deeper cause involved fear of increasing power."},
            {"id": 1, "page": 39, "text": "Diplomats argued about the obligations of their allies."},
            {"id": 2, "page": 70, "text": "Later events are not part of this chunk."},
        ]}
        self.save()

    def save(self):
        for filename, value in [
            ("manifest.json.gz", self.manifest),
            (f"book-{BOOK}.json.gz", self.shard),
        ]:
            with gzip.open(self.root / filename, "wt", encoding="utf-8") as output:
                json.dump(value, output)

    def test_emits_canonical_32_page_chunk_and_exact_page_ids(self):
        packet = build_packet(self.root, BOOK, 38)
        self.assertEqual(packet["schema"], "antilogicalism-reader-packet-v1")
        self.assertEqual(packet["libraryVersion"], 47)
        self.assertEqual(packet["bookId"], "152")
        self.assertEqual(packet["pdfDriveId"], PDF_ID)
        self.assertEqual((packet["chunk"], packet["firstPage"], packet["lastPage"]), (1, 33, 64))
        self.assertEqual([(p["page"], p["globalPageId"]) for p in packet["pages"]], [(38, 0), (39, 1)])
        self.assertIn("deeper cause", packet["pages"][0]["text"])

    def test_repeatable_output_without_modifying_corpus(self):
        before = (self.root / "book-152.json.gz").read_bytes()
        output = Path(self.temp.name) / "packets"
        path = write_packet(self.root, output, BOOK, 38)
        first = path.read_bytes()
        write_packet(self.root, output, BOOK, 38)
        self.assertEqual(first, path.read_bytes())
        self.assertEqual(before, (self.root / "book-152.json.gz").read_bytes())
        self.assertEqual(path.relative_to(output).as_posix(), "books/152/1.json")

    def test_fails_closed_for_unknown_page_and_corrupt_ownership(self):
        with self.assertRaises(ValueError):
            build_packet(self.root, BOOK, 99)
        self.manifest["page_books"][0] = 7
        self.save()
        with self.assertRaises(ValueError):
            build_packet(self.root, BOOK, 38)

    def test_rejects_duplicate_physical_pages(self):
        self.shard["pages"].append({"id": 1, "page": 38, "text": "A second ambiguous record"})
        self.save()
        with self.assertRaises(ValueError):
            build_packet(self.root, BOOK, 38)


if __name__ == "__main__":
    unittest.main()
