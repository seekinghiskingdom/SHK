# Bible Tools v1 – Data + Front-End Contract

This document defines the standard way v1 SHK tools access Scripture text.  
Any tool that reads Bible text (Bible Viewer, Infinite Bible, red-letter, POS highlighter, etc.) should follow this contract.

---

## 1. Single entrypoint config per data version

For data version **v1**, the authoritative Bible metadata file is:

- `docs/data/v1/tools/bible-viewer/index.json`

This file lists the languages, translations, paths, and translation pages to use.

**Required shape (simplified):**

```jsonc
{
  "version": "1.0",
  "data_version": "v1",
  "default_language": "en",
  "default_translation": "kjv",
  "languages": [
    {
      "code": "en",
      "label": "English",
      "translations": [
        {
          "code": "kjv",
          "slug": "kjv",
          "title": "King James Version",
          "short_label": "KJV",
          "language_code": "en",
          "language_label": "English",
          "path": "/data/v1/lit/bible/en/kjv",
          "chapters_dir": "chapters",
          "translation_page": "/literature/bible/translations/en/kjv/",
          "manifest_path": "/data/v1/lit/bible/en/kjv/manifest.json"
        }
      ]
    }
  ]
}
```

Notes:

- **No full text** is stored here, only metadata and paths.
- Future data versions (e.g., `v2`) should have a corresponding file under `docs/data/v2/...`.

---

## 2. Path + URL building rules

All tools should:

1. Load the index JSON for the relevant data version.
2. Use the combination of:
   - `translation.path` – root path for that translation, e.g. `/data/v1/lit/bible/en/kjv`
   - `translation.chapters_dir` – directory inside that root, usually `"chapters"`
   - `BOOK` code – 3-letter code like `GEN`, `EXO`, `JHN`, `1CH`, etc.
   - `CHAP` – chapter number, zero-padded to 3 digits (`001`, `002`, …)

**Standard chapter URL:**

```text
{{ site.baseurl }} + translation.path
+ "/" + translation.chapters_dir
+ "/" + BOOK
+ "/" + CHAP + ".json"
```

Example (KJV, 1 Chronicles 1):

```text
{{ site.baseurl }}/data/v1/lit/bible/en/kjv/chapters/1CH/001.json
```

**Important rules:**

- Respect `{{ site.baseurl }}` (for GitHub Pages under `/SHK`).
- Do not “walk folders” in the browser; always rely on the index file.

---

## 3. Translation objects

Each translation object inside `languages[].translations[]` must include:

- `code` – short code for the translation (`"kjv"`, `"web"`, etc.)
- `slug` – should generally match `code`
- `title` – human-readable title (`"King James Version"`)
- `short_label` – compact label (`"KJV"`) for dropdowns
- `language_code` – ISO-like language code (`"en"`, `"grc"`, `"he"`, etc.)
- `language_label` – full language name (`"English"`, `"Greek"`, etc.)
- `path` – root path to that translation’s data (no trailing slash)
- `chapters_dir` – directory under `path` where chapter JSONs live (usually `"chapters"`)
- `translation_page` – permalink for the translation info page
- `manifest_path` – path to the translation’s own manifest JSON

These fields should be stable across tools.

---

## 4. Book codes

All Bible tools should use the same **book codes**.  
Examples (not exhaustive):

- `GEN`, `EXO`, `LEV`, `NUM`, `DEU`, `JOS`, `JDG`, `RUT`, `1SA`, `2SA`, `1KI`, `2KI`, `1CH`, `2CH`, `EZR`, `NEH`, `EST`, `JOB`, `PSA`, `PRO`, `ECC`, `SNG`, `ISA`, `JER`, `LAM`, `EZK`, `DAN`, `HOS`, `JOL`, `AMO`, `OBA`, `JON`, `MIC`, `NAM`, `HAB`, `ZEP`, `HAG`, `ZEC`, `MAL`
- `MAT`, `MRK`, `LUK`, `JHN`, `ACT`, `ROM`, `1CO`, `2CO`, `GAL`, `EPH`, `PHP`, `COL`, `1TH`, `2TH`, `1TI`, `2TI`, `TIT`, `PHM`, `HEB`, `JAS`, `1PE`, `2PE`, `1JN`, `2JN`, `3JN`, `JUD`, `REV`

These codes must:

- Match the directory names used in the chapter paths.
- Be treated as the canonical book identifiers across tools.

---

## 5. Chapter JSON schema expectations

Long term, the preferred shape for a chapter file is:

```jsonc
{
  "book": "JHN",
  "chapter": 3,
  "translation": "kjv",
  "verses": [
    { "verse": 16, "text": "For God so loved the world, ..." }
  ]
}
```

However, for v1, tools must be able to handle any of the following:

1. `data.verses` is an array:  
   `data = { "verses": [ { "verse": 1, "text": "..." }, ... ] }`
2. `data` is an array:  
   `data = [ { "verse": 1, "text": "..." }, ... ]`
3. `data` is an object with numeric keys:  
   `data = { "1": "First verse text", "2": "Second verse text", ... }`

Front-end tools should normalize these into a list of:

```ts
{ verse: number, text: string }
```

for rendering.

For **plain-text tools** (Bible Viewer, Infinite Bible as text, etc.), the data pipeline should:

- Strip Strong’s numbers, morphology codes, and Greek/lexical fields.
- Only output the clean English (or target language) verse text.

Other tools (e.g., Strong’s-based tools) can use richer schemas, but those should be separate datasets.

---

## 6. Front-end usage checklist (any new tool)

For any new Scripture tool:

1. **Load index**
   - Load `/data/v1/tools/bible-viewer/index.json` (or the appropriate version).
2. **Build lookups**
   - Map: `languageCode → { code, label, translations[] }`
   - Map: `translationCode → translation object`
3. **Select translations**
   - Use these maps for dropdowns or configuration.
   - Do not hard-code translation paths in the tool.
4. **Build chapter URLs**
   - Use `path + chapters_dir + BOOK + CHAP` and `{{ site.baseurl }}` as described.
5. **Parse chapter JSON**
   - Normalize to `(verse, text)` pairs as in §5.
6. **Respect baseurl**
   - All asset/data URLs must be prefixed with `{{ site.baseurl }}` in templates.

---

## 7. How to brief ChatGPT when building a new Bible tool

When starting a new tool that reads Scripture (e.g., Infinite Bible, POS highlighter, red-letter):

Tell ChatGPT explicitly:

> Use the existing Bible tools v1 contract:  
> – Translation metadata + paths come from `/data/v1/tools/bible-viewer/index.json`.  
> – Build chapter URLs from `translation.path`, `translation.chapters_dir`, `BOOK` code, and 3-digit `CHAP` number.  
> – Respect `{{ site.baseurl }}`.  
> – Assume chapter JSON is either `{ verses: [...] }`, `[...]`, or an object keyed by verse numbers, and normalize to `(verse, text)`.

Then describe only the additional behavior unique to that tool (UI, modes, filters, etc.), so all tools stay consistent with the same Bible data contract.
