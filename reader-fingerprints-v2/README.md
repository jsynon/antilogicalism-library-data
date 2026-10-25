# Full v48 public reader fingerprint coverage

This directory contains exact-text SHA-256 fingerprints for the 642 public
catalog books with canonical v48 PDF records. Fingerprints contain page
metadata and hashes, not OCR text. They preserve the physical PDF page number,
global page ID, title, and source Google Drive file ID.

The cohort is recorded in [cohort-full-v48.json](cohort-full-v48.json). The
builder produces one file per 32-page PDF chunk under `books/{bookId}/` and a
`coverage-v2.json` summary. Existing v47 fingerprints stay in
`reader-fingerprints-v1/`.

The v48 fingerprints are not compatible with the current Reading Companion
Worker, which accepts only the v47 schema and version. Publish them only after
the corresponding website and Worker changes are deployed and verified.

```sh
python tools/build_reader_collection.py \
  --root data-v48 --output reader-fingerprints-v2 \
  --library-version 48 \
  --books-file reader-fingerprints-v2/cohort-full-v48.json
```
