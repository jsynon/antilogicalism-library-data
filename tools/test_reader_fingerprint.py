import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from test_reader_packet import ReaderPacketTests
from build_reader_fingerprint import build_fingerprint,write_fingerprint

BOOK=152

class FingerprintTests(unittest.TestCase):
    def setUp(self):
        # Reuse the exact synthetic v47 book fixture used by the packet builder.
        ReaderPacketTests.setUp(self)

    def test_digests_match_exact_original_utf8_text(self):
        result=build_fingerprint(self.root,BOOK,38)
        self.assertEqual(result["schema"],"antilogicalism-reader-fingerprints-v1")
        self.assertEqual(result["libraryVersion"],47)
        self.assertEqual((result["chunk"],result["firstPage"],result["lastPage"]),(1,33,64))
        self.assertEqual(len(result["pages"]),2)
        self.assertNotIn("text",result["pages"][0])
        first=result["pages"][0]
        raw=self.shard["pages"][0]["text"].encode("utf-8")
        self.assertEqual(first["page"],38)
        self.assertEqual(first["globalPageId"],0)
        self.assertEqual(first["sha256"],hashlib.sha256(raw).hexdigest())
        self.assertEqual(first["utf8Bytes"],len(raw))

    def test_unicode_and_whitespace_changes_are_not_silently_normalized(self):
        original="Athens — Sparta. The\npower of Athens."
        self.shard["pages"][0]["text"]=original
        self.save()
        result=build_fingerprint(self.root,BOOK,38)
        entry=result["pages"][0]
        self.assertEqual(entry["sha256"],hashlib.sha256(original.encode("utf-8")).hexdigest())
        self.assertNotEqual(entry["sha256"],hashlib.sha256(original.replace("\n"," ").encode("utf-8")).hexdigest())
        self.assertNotEqual(entry["sha256"],hashlib.sha256(original.replace("Athens","Rome").encode("utf-8")).hexdigest())

    def test_deterministic_small_packet_preserves_original_data(self):
        out=Path(self.temp.name)/"fingerprints"
        source_before=(self.root/"book-152.json.gz").read_bytes()
        path=write_fingerprint(self.root,out,BOOK,38)
        once=path.read_bytes()
        write_fingerprint(self.root,out,BOOK,38)
        self.assertEqual(path.read_bytes(),once)
        self.assertEqual((self.root/"book-152.json.gz").read_bytes(),source_before)
        self.assertEqual(path.relative_to(out).as_posix(),"books/152/1.json")
        self.assertLess(len(once),1500)

    def test_unindexed_page_and_forged_owner_fail_closed(self):
        with self.assertRaises(ValueError):
            build_fingerprint(self.root,BOOK,99)
        self.manifest["page_books"][0]=7
        self.save()
        with self.assertRaises(ValueError):
            build_fingerprint(self.root,BOOK,38)


if __name__=="__main__":
    unittest.main()
