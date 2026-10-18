#!/usr/bin/env python3
"""Build one deterministic, uncompressed 32-PDF-page trusted reader packet.

Reads existing v47 gzip sources OFFLINE, during GitHub Actions or local builds.
No source text or PDF metadata is synthesized. Existing v47 is never modified.
"""
import argparse
import gzip
import json
import re
from pathlib import Path

PACKET_SIZE = 32
PDF = re.compile(r"^https://drive\.google\.com/file/d/([A-Za-z0-9_-]{10,})/(?:view|preview)(?:[?#]|$)")


def load_gzip_json(path: Path):
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def build_packet(root: Path, book_id: int, page: int):
    if book_id <= 0 or book_id > 9999 or page <= 0 or page > 10000:
        raise ValueError("Invalid PDF book/page locator")
    manifest = load_gzip_json(root / "manifest.json.gz")
    if manifest.get("version") != 47:
        raise ValueError("Requires v47 corpus")
    meta = manifest.get("books", {}).get(str(book_id))
    if not isinstance(meta, dict) or not isinstance(meta.get("title"), str):
        raise ValueError("Book is absent from the v47 manifest")
    drive_url = meta.get("drive_url", "")
    pdf_match = PDF.match(drive_url)
    if not pdf_match:
        raise ValueError("Book has no canonical Google Drive PDF")
    page_books = manifest.get("page_books")
    if not isinstance(page_books, list):
        raise ValueError("Missing global page ownership table")
    shard = load_gzip_json(root / f"book-{book_id}.json.gz")
    if not isinstance(shard.get("pages"), list):
        raise ValueError("Book shard does not contain pages")

    chunk = (page - 1) // PACKET_SIZE
    first_page = chunk * PACKET_SIZE + 1
    last_page = first_page + PACKET_SIZE - 1
    selected = {}
    for item in shard["pages"]:
        if not isinstance(item, dict):
            continue
        physical = item.get("page")
        if not isinstance(physical, int) or isinstance(physical, bool):
            continue
        if not first_page <= physical <= last_page:
            continue
        global_id = item.get("id")
        if not isinstance(global_id, int) or isinstance(global_id, bool):
            raise ValueError("Invalid global page ID in selected chunk")
        if global_id < 0 or global_id >= len(page_books) or str(page_books[global_id]) != str(book_id):
            raise ValueError("Global page owner does not match cited book")
        content = item.get("text")
        if not isinstance(content, str) or not content.strip():
            continue
        if physical in selected:
            raise ValueError("Ambiguous duplicate physical PDF page")
        selected[physical] = {
            "page": physical,
            "globalPageId": global_id,
            "text": content,
        }
    if page not in selected:
        raise ValueError("Requested physical PDF page is not indexed")
    return {
        "schema": "antilogicalism-reader-packet-v1",
        "libraryVersion": 47,
        "bookId": str(book_id),
        "title": meta["title"],
        "pdfDriveId": pdf_match.group(1),
        "chunk": chunk,
        "firstPage": first_page,
        "lastPage": last_page,
        "pages": [selected[p] for p in sorted(selected)],
    }


def write_packet(root: Path, output: Path, book_id: int, page: int):
    packet = build_packet(root, book_id, page)
    path = output / "books" / str(book_id) / f"{packet['chunk']}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    # UTF-8 characters are preserved; no lossy OCR or title transformations.
    path.write_text(
        json.dumps(packet, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("data-v47"))
    parser.add_argument("--output", type=Path, default=Path("reader-packets-v1"))
    parser.add_argument("--book-id", type=int, required=True)
    parser.add_argument("--page", type=int, required=True)
    args = parser.parse_args()
    print(write_packet(args.root, args.output, args.book_id, args.page))


if __name__ == "__main__":
    main()
