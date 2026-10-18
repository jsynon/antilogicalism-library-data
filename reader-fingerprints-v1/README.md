# v1.9.3 — SHA-256 fingerprint pilot (no duplicate full-text storage)

**Purpose:** Replace the CPU-heavy trusted book-shard lookup and 32-page plaintext packet with small SHA-256 fingerprint records. The already-existing browser v47 search pipeline has the page text; the Worker must independently verify the exact raw text before trusting it or constructing a canonical citation. This pilot tests only **Thucydides book 152, original PDF page 38**.

The existing `data-v47/` data and `reader-packets-v1/` pilot are not modified. No credentials, API keys, model outputs or additional copies of page text are stored here.

## Data format

`reader-fingerprints-v1/books/152/1.json` is a tiny UTF-8 JSON file for book 152 physical pages 33–64. Each page record contains only `page`, `globalPageId`, `utf8Bytes`, `sha256` (lowercase 64-character hex). At the packet level, the schema identifies v47, 32-page chunk boundaries, canonical title and PDF Drive file ID from the original manifest.

The exporter computes SHA-256 over the **exact UTF-8 bytes** of `page.text` stored in canonical `data-v47/book-152.json.gz`. It does not trim, normalize whitespace, reflow OCR or replace punctuation; even changing a line break changes the digest. It uses the already-tested canonical v47 ownership check from `tools/build_reader_packet.py` and writes no full-page text.

## Generate one pilot

After the PR is merged, go to **Actions → Publish reader fingerprint pilot → Run workflow (main)**. It runs integrity tests, creates just `reader-fingerprints-v1/books/152/1.json`, and commits it to the data repository.

**GitHub Pages caveat:** when the workflow commits using the automatic `GITHUB_TOKEN`, a branch-backed Pages site might not rebuild on that commit alone. If the file is visible in the main branch but its public `jsynon.github.io` link returns 404, make one harmless direct commit through GitHub's website (for example update this README), as was required for the plaintext pilot. Do NOT rerun the builder or delete v47.

Expected public URL after publishing:

`https://jsynon.github.io/antilogicalism-library-data/reader-fingerprints-v1/books/152/1.json`

To build from a local clone of this data repo instead:

```powershell
python tools/build_reader_fingerprint.py --book-id 152 --page 38
python -m unittest discover -s tools -p test_reader_fingerprint.py -v
```

## What it proves (and doesn't)

The public Worker proof in the **separate** `jsynon/book-chatbot` repo will retrieve this small hash packet, independently calculate `crypto.subtle.digest('SHA-256', ...)` for the page text sent by the browser, and accept **only exact matches**. It will bind PDF page IDs/links from this trusted metadata rather than browser claims.

A SHA-256 match strongly verifies the submitted bytes against data published by the repo owner. It does **not** certify OCR accuracy, the historical truth of the text, model reasoning correctness, or claim-level entailment. The current test doesn't enable public AI. No new paid services are involved.

**Do not export the full library yet.** Benchmark both successful and intentionally tampered page requests first. If successful, estimate all-book fingerprint size and GitHub Pages file-count overhead before deciding how to batch publication.
