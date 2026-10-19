# v1.11 — staged 128-book SHA-256 fingerprints (no duplicate full-text storage)

**Purpose:** The browser searches the existing v47 index. The Worker independently verifies the exact submitted page text against small owner-published SHA-256 records before using it to answer or construct a canonical citation. This staged alpha enables 128 varied books from v47, including the existing Aristotle, Darwin, Thucydides, and Dostoevsky tests. It stores hashes and page metadata only; it does not duplicate full-text OCR.

The existing `data-v47/` data and `reader-packets-v1/` pilot are not modified. No credentials, API keys, model outputs or additional copies of page text are stored here.

## Data format

`reader-fingerprints-v1/books/{bookId}/{chunk}.json` contains records for one 32-page chunk. Each page record contains only `page`, `globalPageId`, `utf8Bytes`, and `sha256` (lowercase 64-character hex). At the packet level, the schema identifies v47, canonical title, and PDF Drive file ID from the original manifest.

The exporter computes SHA-256 over the **exact UTF-8 bytes** of `page.text` stored in canonical `data-v47/book-152.json.gz`. It does not trim, normalize whitespace, reflow OCR or replace punctuation; even changing a line break changes the digest. It uses the already-tested canonical v47 ownership check from `tools/build_reader_packet.py` and writes no full-page text.

## Publish the staged cohort

The reproducible selection is [cohort-128-v1.json](cohort-128-v1.json). It includes the four current pilot titles and all eight fixed cross-disciplinary benchmark titles; the rest are selected by a stable round-robin across catalog subject labels. Those labels are catalog cues rather than expert classifications.

After the code and site changes are merged, go to **Actions → Publish v1.11 staged 128-book reader fingerprints → Run workflow**. The workflow checks all book shards against the canonical v47 manifest, enforces a 100–150 book cohort, writes the fingerprint packets and coverage manifest, and commits only those fingerprint files. It does not modify `data-v47/` or any existing OCR.

**GitHub Pages caveat:** when the workflow commits using the automatic `GITHUB_TOKEN`, a branch-backed Pages site might not rebuild on that commit alone. If the file is visible in the main branch but its public `jsynon.github.io` link returns 404, make one harmless direct commit through GitHub's website (for example update this README), as was required for the plaintext pilot. Do NOT rerun the builder or delete v47.

Expected public URL after publishing:

`https://jsynon.github.io/antilogicalism-library-data/reader-fingerprints-v1/books/102/0.json`

To validate the cohort locally without publishing it:

```powershell
python tools/build_reader_collection.py --books-file reader-fingerprints-v1/cohort-128-v1.json
python -m unittest discover -s tools -p test_reader_collection.py -v
```

## What it proves (and doesn't)

The public Worker proof in the **separate** `jsynon/book-chatbot` repo will retrieve this small hash packet, independently calculate `crypto.subtle.digest('SHA-256', ...)` for the page text sent by the browser, and accept **only exact matches**. It will bind PDF page IDs/links from this trusted metadata rather than browser claims.

A SHA-256 match strongly verifies the submitted bytes against data published by the repo owner. It does **not** certify OCR accuracy, the historical truth of the text, model reasoning correctness, or claim-level entailment. The current test doesn't enable public AI. No new paid services are involved.

The 128-book local preflight covers 49,780 pages in 1,641 fingerprint chunks (about 6.83 MB of JSON). This is the intermediate alpha, not the entire 644-book library. Keep the existing v47 full-text index and OCR unchanged. After the expanded pilot is live, check valid and tampered page verification and review cross-discipline answer quality before scheduling full-library fingerprint publication.
