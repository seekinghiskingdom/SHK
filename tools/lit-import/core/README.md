# lit_import / core

This directory contains the **core library modules** for the literature import pipeline.
They implement the parsing and import logic that is used by the CLI scripts in
`import_scripts/` and the maintenance tools in `helper_scripts/`.

Modules:

- `usfm_parser.py`  
  Low-level USFM parser: reads USFM source files and produces structured
  representations of books, chapters, and verses.

- `usfm_import.py`  
  High-level Bible import logic: orchestrates reading raw USFM bundles and
  writing normalized translation data (books, chapters, meta) into the processed
  and site data directories.

- `kjv_strongs_import.py`  
  Special-case importer for the KJV+Strong’s translation, preserving Strong’s
  tagging and any additional structure needed by Strong’s-aware tools.

These modules should remain importable and stable; any new pipeline entrypoints
in `import_scripts/` should call into this core layer rather than duplicating
import logic.
