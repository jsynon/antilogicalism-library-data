# Reader packets v1 — CPU feasibility pilot

This directory will contain a **small, static, trusted-source lookup format** derived from the existing compressed v47 dataset. The existing `data-v47/` search index is **not modified**. Nothing is published until the maintainer chooses to run the workflow.

Why: the Cloudflare Workers Free source-retrieval probe worked, but measured 24.35 ms P90 CPU over a small sample, exceeding its 10 ms CPU allowance. The Worker currently decompresses and parses an enormous manifest plus an entire book shard for one source page.

**Pilot only**: a single, deterministic, plain UTF-8 JSON file containing at most 32 consecutive physical PDF pages of the same book: `reader-packets-v1/books/152/1.json` for Thucydides pages 33–64, including page 38. It binds v47 book ID, title, original PDF Drive identifier, per-page global index ID and full OCR text. It is generated from the original v47 `manifest.json.gz` and `book-152.json.gz`; it does not rewrite citations or OCR. The Worker reconstructs its own excerpts after loading this trusted packet.

To generate it from GitHub (once the PR is merged), open **Actions → Publish reader pilot packet → Run workflow**. The workflow runs integrity unit tests, generates only the one pilot file, and commits the new file to the repository. Wait for GitHub Pages to publish it, then check `https://jsynon.github.io/antilogicalism-library-data/reader-packets-v1/books/152/1.json`. The new file is public **book text**, not a credential; never put AI secrets into this repo.

From a local clone of this data repo, an equivalent command is:

```powershell
python tools/build_reader_packet.py --book-id 152 --page 38
```

To test the generator without the real library corpus:

```powershell
python -m unittest discover -s tools -p test_reader_packet.py -v
```

**Do not generate all 280,699 indexed pages yet.** First benchmark this one 32-page file against the existing trusted-source Worker probe in the separate `book-chatbot` repository. Only if the new method stays comfortably within Workers Free's actual CPU allowance should we plan library-wide packet generation. The number and total size of files also need to be checked against GitHub Pages publishing limits. Citation source ownership verification happens in the offline generator; the Worker validates the packet's expected schema and page IDs but **does not provide cryptographic immutability or claim-level fact checking**.

The first reader packet pilot was generated successfully from the v47 library.
