# Full v47 public reader coverage (642 books)

**Purpose:** Expand the public Reading Companion from the 128-book staged cohort to every work in the current public digital-library catalog that has a canonical v47 PDF. The browser searches existing v47 OCR. The Worker independently verifies submitted page text against owner-published SHA-256 fingerprints before it uses the page or constructs a citation. These files contain hashes and page metadata only; they do not duplicate OCR.

## Scope

The reproducible selection is [cohort-full-v47.json](cohort-full-v47.json): **642 books, 280,069 indexed pages, 9,149 fingerprint chunks**. It is derived from all public `digital-library/library-catalog.json` entries that have a valid canonical Google Drive PDF URL in the v47 manifest. The raw v47 manifest contains 644 books, while the public catalog contains 643 records. Book ID `1` is not in the public catalog. Public catalog book ID `628` has no canonical PDF URL and is excluded. Neither is included in Worker support or coverage.

The measured packet output is approximately **38.5 MB**. The existing v47 full-text index and OCR remain unchanged. Forty-five pages exceed the current 14,000-byte submission limit; their fingerprints are included, but those pages cannot be submitted until page-size handling is expanded. This is a known small edge case for the whole-library milestone.

## Coordinated rollout

1. Merge and deploy the Worker allowlist change for the same 642 IDs. The Worker remains disabled unless its existing public safety bindings and opt-in flags are configured.
2. Merge this data workflow/cohort change.
3. In **Actions → Publish full v47 public reader fingerprints → Run workflow**, manually dispatch the publishing workflow. It checks the full cohort against the canonical v47 manifest and publishes only the fingerprint packets and `coverage-v1.json`; it does not touch OCR data.
4. Confirm the workflow commit and Pages availability, then run representative end-to-end questions across the newly covered disciplines, checking citations, source links, cross-turn context, and unsupported-question behavior.

The workflow is manual so coverage is not published before the matching Worker allowlist is deployed. If the fingerprint files appear on `main` but their public Pages URLs return 404, GitHub Pages may not have rebuilt from the automatic `GITHUB_TOKEN` commit. Make a harmless direct commit through GitHub's website to trigger Pages; do not rerun the builder or alter v47 OCR.

## Data format and local validation

Each `reader-fingerprints-v1/books/{bookId}/{chunk}.json` file covers one 32-PDF-page chunk. Page records contain `page`, `globalPageId`, `utf8Bytes`, and exact SHA-256 of the canonical OCR UTF-8 bytes. The exporter validates global page ownership, rejects duplicate physical pages, and writes output only after all selected shards pass validation.

```powershell
python tools/build_reader_collection.py --books-file reader-fingerprints-v1/cohort-full-v47.json
python -m unittest discover -s tools -p 'test_reader_*.py' -v
```

A hash match verifies that submitted bytes match owner-published source data. It does not certify OCR accuracy, historical truth, or claim-level entailment.
