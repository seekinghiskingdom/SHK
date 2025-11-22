# lit_import / helper_scripts

This directory contains **maintenance and validation utilities** for the literature data.

They do not define the main pipeline; instead, they help check or normalize data after imports or before tagging a new data version.

Examples:

- `check_bible_translations.py` – validate that each Bible translation has the expected files and counts.
- `bible_cleanup_structure.py` – normalize Bible translation folder structure and clean stray files.
- `bible_registry_update.py` – update translation manifests and regenerate `lit/bible/translations.json`.
- `data_manifest_check.py` – check that `docs/data/v1/manifest.json` only references real datasets.
- `historical_check.py` – structural checks for `lit/historical`.

The `old/` subfolder contains **one-off scripts** used to prepare the v1 dataset (e.g. mass cleanup or migration). They are kept for reference but are not intended for regular use.
