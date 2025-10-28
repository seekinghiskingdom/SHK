# Seeking His Kingdom — v1.0.0 To‑Do

> Scope: everything needed to ship a stable v1.0.0 of the site + data tools.  
> Note: This list excludes initial SCS feature UI and Bible Viewer UI polish beyond data/behavioral fixes; those are tracked separately.

---

## 🚀 Frontend (Site & Tools)

### PPS (Proverb Pair Search)
- [ ] Replace stub logic with real loader for `docs/data/v1/tools/pps/shk_pairs.json`.
- [ ] Remove all references to legacy `docs/data/shk_pairs.json`.
- [ ] Filters UI: book, chapter range, X term, Y term, “has X only / has Y only / has both”.
- [ ] Results list: verse ref, matched terms highlight, pair meta (score/counts).
- [ ] Empty state + error state (bad bundle, fetch failure).
- [ ] Deep-linking (querystring ↔ UI state sync).
- [ ] Lightweight client index (token→pairIds) for snappy filtering.
- [ ] “Copy link to results” button.
- [ ] Footer: data bundle version + builtAt display.

### Bible Viewer
- [ ] Fix multi-verse range rendering (e.g., `Prov 1:1–7` shows all verses).
- [ ] Translation switcher (KJV/ASV/WEB) with state preserved in URL.
- [ ] Normalize book ids vs `books.json` mapping.
- [ ] Loading/empty/error states; guard against missing verses.
- [ ] Keyboard nav (←/→ verse stepping) — optional but quick win.

### Global UI / Docs
- [ ] “What’s New” panel pulling `bundleVersion`/`builtAt` from manifest.
- [ ] 404 page polish; confirm `robots.txt` and add minimal `sitemap.xml`.
- [ ] Ensure `resources_nav.json` drives sidebar consistently (no dead links).

---

## 🧰 Backend (Build, Data, Validation)

### Build Pipeline (`scripts/`)
- [ ] `scripts/build_data.py`: copy/version tool outputs → `docs/data/v1/...`; write `bundleVersion`, `builtAt`, and a top-level `manifest.json`.
- [ ] `scripts/validate_data.py`: run all schema checks (PPS, Bible books, manifest).
- [ ] Deterministic IDs for PPS (hash of canonical fields) to prevent churn.
- [ ] `scripts/diff_bundles.py`: added/removed/changed report for any two bundles.
- [ ] Size gates: warn/fail if bundles exceed thresholds (raw + gzip).

### Schemas (`schemas/`)
- [ ] `schemas/pps.schema.json`
- [ ] `schemas/bible_book.schema.json`
- [ ] `schemas/manifest.schema.json`

### Data Hygiene (`tools/pps`, `tools/lit-import`)
- [ ] Token canonicalization (trim, case, punctuation) before pairing.
- [ ] Dedupe PPS entries; remove empty/stopword-only pairs.
- [ ] Bible JSON normalization (consistent whitespace & punctuation).
- [ ] QA report emit (CSV/HTML) into `qa/out/` for missing/odd fields.

### Config & Consistency
- [ ] Normalize translation ids: `kjv`, `asv`, `web` across config and paths.
- [ ] Add ASV/Web attribution into `docs/data/config.json`.
- [ ] Generate `docs/data/resources_nav.json` via script (avoid manual drift).

### Strong’s (SCS) — v1 seed
- [ ] Create `docs/data/v1/tools/scs/` with minimal bundle (schema + 1–2 lemmas).
- [ ] Document planned fields and lookup keys (lemmaId, gloss, refs).
- [ ] Add loader stub page that verifies bundle presence (even if UI is basic).

---

## ✅ QA & Tests (`qa/`)
- [ ] PPS smoke tests: run canned queries → assert known ids/counts.
- [ ] Bible smoke test: render known range (e.g., `Prov 3:5–6`) → assert verse count & order.
- [ ] Manifest test: no orphaned files; all referenced paths exist.
- [ ] Performance spot-check: PPS filter round-trip under X ms with N pairs (document X,N).

---

## ⚙️ CI/CD (GitHub Actions)
- [ ] `validate.yml`: install deps → run validators & tests on PRs; fail on schema/size errors.
- [ ] `publish.yml` (on `main`): build → validate → commit/copy bundles to `docs/data/v1/...`; attach artifact.
- [ ] Cache Python deps & intermediate artifacts for faster runs.
- [ ] Short release notes generated from provenance + git shortlog.

---

## 🧾 Provenance & Versioning
- [ ] Embed `bundleVersion` (semver + short sha) and `builtAt` (UTC ISO) in every bundle.
- [ ] `data/_provenance.json`: source repo sha, build params, script versions.
- [ ] `data/VERSION` file → surfaced on site footer.

---

## 📚 Developer Experience
- [ ] `tools/pps/README.md`: inputs → transforms → outputs; example commands.
- [ ] `tools/lit-import/README.md`: ingestion steps; where processed files land.
- [ ] Top-level `README.md`: repo map, local dev notes, deploy notes.
- [ ] Makefile / task runner: `make build`, `make validate`, `make test`, `make publish`.

---

## 🧪 Nice-to-Have (v1.1+)
- [ ] Content-hash filenames (e.g., `shk_pairs.a1b2c3.json`) + tiny manifest for cache-busting.
- [ ] Delta bundles (only changed entries) if PPS grows large.
- [ ] Local preview server with cache-simulation toggles.
- [ ] Basic client telemetry schema (disabled by default) for search/filter events.

---

## 🗑️ Cleanups
- [ ] Remove `docs/data/shk_pairs.json` (legacy) and any codepaths that reference it.
- [ ] Verify there are no hardcoded paths to non-`v1` data.
- [ ] Trim leftover placeholder JS/CSS once real components are in place.

---

## 📌 Definition of Done (v1)
- [ ] PPS loads v1 bundle, filters work, shareable links OK, empty/error states OK.
- [ ] Bible Viewer renders full ranges, translation switch works, deep-link stable.
- [ ] Build/validate pass locally and in CI; size limits respected.
- [ ] Manifest + provenance present; site shows bundle version/date.
- [ ] No dead links; 404/robots/sitemap verified.
- [ ] Tag created: `v1.0.0` with release notes.
