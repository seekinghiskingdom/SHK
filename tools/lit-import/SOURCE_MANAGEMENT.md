# Source Management Guide (lit_import)

This document explains where and how to record provenance (source info) for any
data imported through `lit_import`. The goal is:

- Every dataset has a clear upstream source (provider, URL, license).
- The same information is reflected both in **per-dataset metadata** and in a
  **high-level summary** for the version (e.g., `docs/data/v1/DATA_SOURCES.md`).

Use this as a checklist any time you add or update data.

---

## 1. Key locations

There are three main places where source information lives:

1. **Raw inputs (not deployed)**  
   - `tools/lit_import/data/raw/...`  
   - Contains original USFM/XML/text bundles and any download metadata.  
   - This is the “archive” that lets you recreate processed/site data.

2. **Per-dataset metadata (deployed)**  
   - `docs/data/<version>/lit/.../<dataset>/meta.json`  
   - For Bibles: `docs/data/<version>/lit/bible/<lang>/<code>/meta.json`  
   - For Strong’s: `docs/data/<version>/lit/strongs/<lang>/meta.json`  
   - For historical texts: typically under `docs/data/<version>/lit/historical/.../meta.json` (or `manifest.json` if you keep it simple).

3. **Version-level summary (deployed)**  
   - `docs/data/<version>/DATA_SOURCES.md`  
   - High-level overview of what families exist (bible, strongs, historical, etc.)
     and where they came from (e.g., eBible.org, Open Scriptures, etc.).

---

## 2. Per-dataset `meta.json` structure

Each dataset’s `meta.json` should have a `source` block like:

```json
"source": {
  "provider": "eBible.org",
  "url": "https://ebible.org",
  "raw_dir": "tools/lit_import/data/raw/bible/en/kjv",
  "license": "Public domain / permissive license; see eBible.org",
  "notes": "Imported via lit_import from eBible USFM bundle."
}
