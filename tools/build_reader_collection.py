#!/usr/bin/env python3
"""Publish complete v47 fingerprint coverage for a bounded set of books.

Reads each canonical gzip shard ONCE. SHA-256 is always over exact OCR UTF-8
bytes, with original PDF page and manifest global-page ownership checked.
Produces only hashes/metadata: never duplicates book OCR or changes v47.
"""
import argparse
import hashlib
import json
from pathlib import Path
from build_reader_packet import load_gzip_json, PDF, PACKET_SIZE

PILOT_BOOKS = (7, 114, 152, 529)


def build_collection(root: Path, output: Path, book_ids=PILOT_BOOKS):
    if not book_ids or len(set(book_ids)) != len(book_ids):
        raise ValueError("Book IDs must be a nonempty unique selection")
    manifest = load_gzip_json(root / "manifest.json.gz")
    if manifest.get("version") != 47 or not isinstance(manifest.get("page_books"), list):
        raise ValueError("Expected canonical v47 manifest")
    original_books = manifest.get("books", {})
    owners = manifest["page_books"]
    coverage = {"schema": "antilogicalism-reader-coverage-v1",
                "libraryVersion": 47, "chunkSize": PACKET_SIZE, "books": {}}
    planned = {}
    for book_id in book_ids:
        if isinstance(book_id, bool) or not isinstance(book_id, int) or not 1 <= book_id <= 9999:
            raise ValueError("Invalid book ID")
        key = str(book_id)
        meta = original_books.get(key)
        pdf = PDF.match(meta.get("drive_url", "")) if isinstance(meta, dict) else None
        if not pdf or not isinstance(meta.get("title"), str) or not meta["title"].strip():
            raise ValueError("Missing canonical title or PDF for " + key)
        shard = load_gzip_json(root / f"book-{book_id}.json.gz")
        if not isinstance(shard.get("pages"), list):
            raise ValueError("Invalid canonical book shard for " + key)
        by_chunk, seen = {}, set()
        oversized = 0
        for p in shard["pages"]:
            if not isinstance(p, dict):
                continue
            page, global_id, value = p.get("page"), p.get("id"), p.get("text")
            if not isinstance(page, int) or isinstance(page, bool) or not 1 <= page <= 10000:
                continue
            if not isinstance(global_id, int) or isinstance(global_id, bool) or not 0 <= global_id < len(owners):
                raise ValueError("Invalid global page ID in book " + key)
            if str(owners[global_id]) != key:
                raise ValueError("Global owner mismatch for " + key + ":" + str(page))
            if not isinstance(value, str) or not value.strip():
                continue
            if page in seen:
                raise ValueError("Duplicate physical PDF page in book " + key)
            seen.add(page)
            utf8 = value.encode("utf-8")
            if len(utf8) > 14000:
                oversized += 1
            chunk = (page - 1) // PACKET_SIZE
            by_chunk.setdefault(chunk, []).append({
                "page": page, "globalPageId": global_id,
                "utf8Bytes": len(utf8),
                "sha256": hashlib.sha256(utf8).hexdigest()
            })
        if not seen:
            raise ValueError("No pages to fingerprint in " + key)
        for chunk, records in by_chunk.items():
            records.sort(key=lambda x: x["page"])
            packet = {
                "schema": "antilogicalism-reader-fingerprints-v1",
                "libraryVersion": 47, "bookId": key, "title": meta["title"],
                "pdfDriveId": pdf.group(1), "chunk": chunk,
                "firstPage": chunk * PACKET_SIZE + 1,
                "lastPage": (chunk + 1) * PACKET_SIZE,
                "hashAlgorithm": "SHA-256-utf8-exact", "pages": records,
            }
            data = (json.dumps(packet, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
            if len(data) > 12000:
                raise ValueError("Fingerprint chunk exceeds Worker cap")
            planned[output / "books" / key / f"{chunk}.json"] = data
        coverage["books"][key] = {
            "title": meta["title"], "pages": len(seen),
            "chunks": len(by_chunk), "oversizedPages": oversized,
        }
    # Write only after all validation succeeds, so incomplete shards don't
    # produce a misleading ready-to-publish coverage index.
    for path, data in planned.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    index = output / "coverage-v1.json"
    index.parent.mkdir(parents=True, exist_ok=True)
    index.write_text(json.dumps(coverage, ensure_ascii=False, separators=(",", ":")) + "\n",
                     encoding="utf-8")
    return coverage


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("data-v47"))
    parser.add_argument("--output", type=Path, default=Path("reader-fingerprints-v1"))
    parser.add_argument("--books", nargs="+", type=int, default=list(PILOT_BOOKS))
    args = parser.parse_args()
    coverage = build_collection(args.root, args.output, args.books)
    print("Built", len(coverage["books"]), "books /",
          sum(b["pages"] for b in coverage["books"].values()), "pages /",
          sum(b["chunks"] for b in coverage["books"].values()), "fingerprint chunks")
    for book_id, info in coverage["books"].items():
        print(book_id, info["title"], "pages:", info["pages"],
              "over 14KB:", info["oversizedPages"])


if __name__ == "__main__":
    main()
