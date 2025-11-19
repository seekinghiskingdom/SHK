# Data Sources & Provenance

This repo ships per-book JSON exports for several English Bible translations (v1) plus a Strong’s‑tagged KJV set. All sources are public‑domain or permissively licensed; verify licenses for your deployment.

> Tip: Record checksums for each raw file so you can reproduce builds exactly.

---

## KJV (plain, OSIS)
- **Raw path:** `tools/lit-import/data/raw/kjv/osis/eng-kjv.osis.xml`
- **Format:** OSIS XML (milestone verses or `<verse osisID="...">`)
- **Output:** `docs/data/v1/lit/bible/en/kjv/*.json`
- **License:** Public Domain
- **Retrieved:** 2025-10-25
- **Checksum:**
  ```bash
  python - <<'PY'
  import hashlib, pathlib
  p = pathlib.Path("tools/lit-import/data/raw/kjv/osis/eng-kjv.osis.xml")
  print("KJV OSIS SHA256:", hashlib.sha256(p.read_bytes()).hexdigest())
  PY
  ```

## KJV + Strong’s (USFX)
- **Raw dir:** `tools/lit-import/data/raw/kjv/eng-kjv_usfx/` (main text typically `eng-kjv_usfx.xml`)
- **Format:** USFX XML (`<v bcv="GEN.1.1">` or `<v id="…">…</ve>`; word tokens in `<w s="H####|G####">`)
- **Output:** `docs/data/v1/lit/bible/en/kjv_strongs/*.json`
- **License:** Public Domain
- **Retrieved:** 2025-10-25
- **Checksum (per file):**
  ```bash
  python - <<'PY'
  import hashlib, pathlib
  for p in pathlib.Path("tools/lit-import/data/raw/kjv/eng-kjv_usfx").rglob("*.xml"):
      print(p.name, hashlib.sha256(p.read_bytes()).hexdigest())
  PY
  ```

## WEB (plain, USFX)
- **Raw path:** `tools/lit-import/data/raw/web/usfx/eng-web.usfx.xml`
- **Format:** USFX XML (verse start `<v id="n">`, end `</ve>`; books via `<book code="GEN">` or `<scriptureBook ubsAbbreviation="GEN">`)
- **Output:** `docs/data/v1/lit/bible/en/web/*.json`
- **License:** Public Domain (World English Bible)
- **Retrieved:** 2025-10-26
- **Checksum:**
  ```bash
  python - <<'PY'
  import hashlib, pathlib
  p = pathlib.Path("tools/lit-import/data/raw/web/usfx/eng-web.usfx.xml")
  print("WEB USFX SHA256:", hashlib.sha256(p.read_bytes()).hexdigest())
  PY
  ```

## ASV (plain, Zefania)
- **Raw path:** `tools/lit-import/data/raw/asv/zefania/eng-asv.zefania.xml`
- **Format:** Zefania XML (`<XMLBIBLE>/<BIBLEBOOK>/<CHAPTER>/<VERS>`)
- **Output:** `docs/data/v1/lit/bible/en/asv/*.json`
- **License:** Public Domain
- **Retrieved:** 2025-10-26
- **Checksum:**
  ```bash
  python - <<'PY'
  import hashlib, pathlib
  p = pathlib.Path("tools/lit-import/data/raw/asv/zefania/eng-asv.zefania.xml")
  print("ASV Zefania SHA256:", hashlib.sha256(p.read_bytes()).hexdigest())
  PY
  ```

## Strong’s Lexicon (for later)
- **Raw dir (expected):** `tools/lit-import/data/raw/strongs/` (e.g., `strongs-hebrew.xml`, `strongs-greek.xml`, or Zefania-style dictionary XMLs)
- **Output (after build):** `docs/data/v1/lit/strongs/lexicon.json`
- **License:** Use a public-domain or permissive lexicon source
- **Checksum (per file):**
  ```bash
  python - <<'PY'
  import hashlib, pathlib
  d = pathlib.Path("tools/lit-import/data/raw/strongs")
  if d.exists():
      for p in d.rglob("*.xml"):
          print(p.name, hashlib.sha256(p.read_bytes()).hexdigest())
  else:
      print("No strongs source dir yet:", d)
  PY
  ```

---

## Rebuild commands

From repo root:

```bash
python tools\lit-import\scripts\kjv_manual_export.py
python tools\lit-import\scripts\kjv_strongs_from_usfx.py
python tools\lit-import\scripts\web_manual_export_usfx.py
python tools\lit-import\scripts\asv_manual_export.py
# Later when you add raw lexicon XMLs:
# python tools\lit-import\scripts\strongs_lexicon_build.py
python tools\lit-import\scripts\build_bible_manifests.py
```
