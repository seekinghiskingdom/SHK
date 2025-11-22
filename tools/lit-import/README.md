# lit-import

lit-import contains the import and build pipeline for all literature data used by the SHK site.

It is responsible for:
- Downloading or ingesting raw source files (USFM, XML, text, etc.).
- Converting them into normalized JSON/CSV structures.
- Writing the final site data under `docs/data/v1/lit/...`.

## Layout

- `import_scripts/`  
  Main pipeline scripts (end-to-end import/build commands).

- `helper_scripts/`  
  Reusable maintenance and validation utilities, for example:
  - `bible_cleanup_structure.py` – normalize Bible translation folder structure.
  - `bible_registry_update.py` – set Strong’s feature flags and regenerate `translations.json`.
  - `data_manifest_check.py` – validate `docs/data/v1/manifest.json` against disk.
  - `historical_check.py` – structural check for `lit/historical`.

- `helper_scripts/old/`  
  One-off scripts used to prepare the v1 dataset. These are kept for reference but are not intended for regular use.

- `data/raw/`  
  Raw source inputs (e.g., USFM bundles, Strong’s XML), organized by family (bible, strongs, historical, etc.).

- `data/processed/`  
  Intermediate processed outputs that can be regenerated from `data/raw/`. The final deployed data lives under `docs/data/v1/lit/...`.

## Usage (high level)

- Use scripts in `import_scripts/` to import or refresh data from `data/raw/`.
- After adding or changing translations:
  - Run `bible_cleanup_structure.py` and `bible_registry_update.py`.
  - Optionally run `data_manifest_check.py` to confirm the global manifest still matches the data.
- The `data/raw/` directory is the long-term archive of inputs; `data/processed/` and `docs/data/v1/lit/` can always be rebuilt from it.
