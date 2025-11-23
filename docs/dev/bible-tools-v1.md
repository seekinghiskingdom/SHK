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

## 5.5. Scripture Core API (SCA)

New Scripture tools (including Infinite Bible) do not read Bible files directly. Instead, they should call a small helper, the Scripture Core API (SCA), which wraps the existing Bible Tools v1 / Bible Viewer data:

- `listBooks(translation)`  
  - Returns ordered list of books with 3-letter codes and chapter counts.  
  - Used to populate the Book and Chapter selectors.

- `getChapter(translation, bookCode3, chapterNumber)`  
  - Returns an array of `{ verse: number, text: string }` for that chapter.  
  - Used for Bible Mode chapter templates and Notes Mode when inserting full chapters.

- `getPassage(translation, bookCode3, chapterNumber, versesArray)`  
  - Returns an array of `{ verse, text }` for the specific verses requested.  
  - Used when inserting single verses or verse ranges into Notes Mode boards.

- `parseReference(inputString)`  
  - Parses strings like `"Proverbs 1:7–9"` or `"Luke 12:31"`  
  - Returns `{ bookCode3, chapterNumber, versesArray }` or an error state for invalid input.


### Scripture Core API – JS module contract (v1)

Front-end tools that read Scripture (Bible Viewer, Infinite Bible, etc.) should depend on a shared JS helper, e.g. `scripture-core.js`, which exposes:

- `loadIndex(dataVersion: string = "v1") → Promise<Index>`
  - Loads `/data/<dataVersion>/tools/bible-viewer/index.json`.
  - Caches the result in memory so multiple calls do not re-fetch.

- `listBooks(translationCode: string) → BookMeta[]`
  - Uses the loaded index.
  - Returns an ordered list of books for the given translation with:
    - `code3` (3-letter book code, e.g. `PRO`, `JHN`),
    - `title` (e.g. `"Proverbs"`),
    - `chapters` (number of chapters).

- `getChapter(translationCode: string, bookCode3: string, chapterNumber: number) → Promise<Verse[]>`
  - Builds the chapter URL using `translation.path`, `translation.chapters_dir`, book code, and 3-digit chapter.
  - Fetches and normalizes the JSON into an array of `{ verse: number, text: string }`.

- `getPassage(translationCode: string, bookCode3: string, chapterNumber: number, verses: number[]) → Promise<Verse[]>`
  - Calls `getChapter` internally and filters to the requested verse numbers.
  - Returns the same `{ verse, text }` shape.

- `parseReference(input: string) → ParsedRef | Error`
  - Parses user input like `"Proverbs 1:7–9"` or `"Luke 12:31"`.
  - Returns `{ bookCode3, chapter: number, verses: number[] }` on success, or an error object/enum for invalid or unsupported input.

Notes:
- All URLs must respect `{{ site.baseurl }}` in templates.
- Verse text is always resolved through these helpers; tools never read chapter files directly.



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


# Specific Tool Uses & Notes

## Bible Viewer



## Infinite Bible (Tool) – Data & Modes (v1 concept)

Infinite Bible (Tool) uses the shared Scripture Core API defined in §5.5 for all Scripture lookups.

- Infinite Bible has two modes sharing the same underlying data:
  - **Bible Mode (“Infinite Bible”)** – one global Bible board, with chapters loaded as needed.
  - **Notes Mode (“Infinite Bible Notes”)** – multiple named boards, each a free-form canvas.

### Boards and items

- Each device stores:
  - A `schemaVersion` number.
  - Global settings (default verse-number behavior, long-passage warning, export filename style).
  - A list of **boards** and a `lastOpenBoardId`.

- Each **board** has:
  - An `id`, `name`, `createdAt`, `updatedAt`.
  - A `viewState` (canvas pan/zoom).
  - An `items` array.

- Each **verse item** stores only:
  - `translation` code (e.g., `"KJV"`),
  - 3-letter `book` code,
  - `chapter` number,
  - `verses` array (one or more verse numbers),
  - `layout` (at minimum: `x`, `y`, optionally width/height),
  - optional `decorations` (stickers, highlights, connection endpoints; empty in v1).

- Each **note item** stores:
  - `text`,
  - `layout` (x/y/width/height),
  - optional `decorations`.

- Verse text is **never** stored in boards. Rendering always resolves `{translation, book, chapter, verses[]}`
  through the existing Bible Tools v1 / Bible Viewer data.

### Mode behavior (v1)

- **Bible Mode**
  - Treats all loaded chapters as part of one “Bible board”.
  - Chapters are loaded on demand from the Bible data (one chapter at a time, with an option to split into one block per verse).
  - UI may collapse non-active chapters to keep the canvas manageable; layouts and notes remain saved.

- **Notes Mode**
  - Supports multiple named boards (soft limit, e.g., 50 boards per device).
  - Each board can contain any mix of verse items and notes.
  - Boards save automatically in local browser storage and can be exported/imported as JSON files.



## PPS



## SCS



## 
