# shk-lit-import

Minimal, reproducible pipeline to fetch, normalize, index, and export literature data for the SHK site.

### Goals
- Import **Strong's XML** (public domain) and **KJV with Strong's mapping**.
- Normalize to stable IDs (OSIS verse refs; H####/G####).
- Export **small JSON shards** for GitHub Pages consumption (`docs/data/v1/...`).

### Quick start
```bash
# from repo root after unzipping into tools/lit-import
cd tools/lit-import
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
shk-lit --help
```

### CLI outline
- `shk-lit fetch` — download raw sources (not committed; temp/local only).
- `shk-lit normalize` — parse Strong's + KJV to normalized tables.
- `shk-lit index` — crosswalks (strongs↔verses), frequencies.
- `shk-lit export-pages --out ../../docs/data/v1` — shard JSON for the website.
- `shk-lit release-bundle --out dist/` — zip heavy artifacts + manifest.

> This is a starter skeleton. Functions are stubs to be implemented next.


---
**Note on site placeholders**
This starter includes `docs/data/v1/strongs/.gitkeep` and `docs/data/v1/kjv/verses/.gitkeep`
so the site data directories persist in git before your first build.
