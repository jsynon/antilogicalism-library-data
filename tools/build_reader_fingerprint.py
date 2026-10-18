#!/usr/bin/env python3
"""Build one compact SHA-256 fingerprint packet from canonical v47 PDF-page text.

No OCR text is published twice. The unhashed title and PDF ID are copied from
the canonical v47 manifest; the Worker uses these trusted metadata fields.
SHA-256 hashes exact UTF-8 bytes of page.text, without whitespace normalization.
"""
import argparse
import hashlib
import json
from pathlib import Path
from build_reader_packet import build_packet


def build_fingerprint(root: Path, book_id: int, page: int):
    canonical = build_packet(root, book_id, page)
    return {
        "schema": "antilogicalism-reader-fingerprints-v1",
        "libraryVersion": canonical["libraryVersion"],
        "bookId": canonical["bookId"],
        "title": canonical["title"],
        "pdfDriveId": canonical["pdfDriveId"],
        "chunk": canonical["chunk"],
        "firstPage": canonical["firstPage"],
        "lastPage": canonical["lastPage"],
        "hashAlgorithm": "SHA-256-utf8-exact",
        "pages": [
            {
                "page": item["page"],
                "globalPageId": item["globalPageId"],
                "utf8Bytes": len(item["text"].encode("utf-8")),
                "sha256": hashlib.sha256(item["text"].encode("utf-8")).hexdigest(),
            }
            for item in canonical["pages"]
        ],
    }


def write_fingerprint(root: Path, output: Path, book_id: int, page: int):
    result = build_fingerprint(root, book_id, page)
    path = output / "books" / str(book_id) / f"{result['chunk']}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n",
                    encoding="utf-8")
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("data-v47"))
    parser.add_argument("--output", type=Path, default=Path("reader-fingerprints-v1"))
    parser.add_argument("--book-id", type=int, required=True)
    parser.add_argument("--page", type=int, required=True)
    args = parser.parse_args()
    print(write_fingerprint(args.root, args.output, args.book_id, args.page))


if __name__ == "__main__":
    main()
