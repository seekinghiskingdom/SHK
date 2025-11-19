# SHK Lit Import

This tool ingests raw Bible and lexicon source files (mainly from eBible) and converts them into the JSON formats used under `docs/data/v1/lit/`.

## Directory layout

- `tools/lit-import/`
  - `cli.py` – command-line entry point (`shk-lit-import`).
  - `usfm_import.py` – generic USFM → `books.json` + `chapters.jsonl` importer.
  - `usfm_parser.py` – minimal USFM line parser.
  - `kjv_strongs_import.py` – special importer for KJV+Strong’s from USFX XML.
  - `check_imports.py` – sanity checker for imported Bibles.
  - `data/raw/` – raw source files and planning JSON:
    - `bible/bible_plan.json` – master list of translations, groups, tiers, and codes.
    - `bible/<lang>/<code>/manifest.json` – per-translation metadata.
    - `bible/<lang>/<code>/*_usfm.zip` – raw USFM zips.
    - `bible/en/kjv_strongs/eng-kjv-usfx.zip` – USFX source for KJV+Strong’s.
    - `strongs/manifest.json` – placeholder for Strong’s lexicon (to be populated later).

## Data flow (Bible imports)

1. Raw sources are stored under `tools/lit-import/data/raw/bible/<lang>/<code>/`:
   - `manifest.json` defines `code`, `language`, `source.format`, `canon`, and target files.
   - Exactly one `*_usfm.zip` (or `*_usfx.zip` for KJV+Strong’s) contains the original text.

2. Running the importer:
   - From the repo root:
     - Import all Greek originals:
       ```bash
       python tools/lit-import/cli.py bible --lang grc --force
       ```
     - Import all English Bibles:
       ```bash
       python tools/lit-import/cli.py bible --lang en --force
       ```
     - Import a single translation (e.g. ASV):
       ```bash
       python tools/lit-import/cli.py bible --lang en --code asv --force
       ```

3. For each selected translation, the importer:
   - Reads `bible_plan.json` to find the translation definitions.
   - Loads the raw `manifest.json` and discovers the source zip.
   - If `source.format == "usfm"`:
     - Uses `usfm_import.import_bible_from_raw_plan` to:
       - Parse USFM into an in-memory book model.
       - Write:
         - `docs/data/v1/lit/bible/<lang>/<code>/books.json`
         - `docs/data/v1/lit/bible/<lang>/<code>/chapters.jsonl`
         - `docs/data/v1/lit/bible/<lang>/<code>/meta.json`
   - If `source.format == "usfx"` (KJV+Strong’s):
     - Uses `kjv_strongs_import.import_kjv_strongs_from_usfx` to:
       - Parse USFX XML and extract tokens with Strong’s IDs.
       - Write the same three files, but each verse also includes a `tokens` array
         with Strong’s annotations.

## Output formats

### `books.json`

```json
{
  "order": ["GEN", "EXO", "..."],
  "names": {
    "GEN": "Genesis",
    "EXO": "Exodus"
  }
}
