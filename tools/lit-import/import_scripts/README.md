# lit_import / import_scripts

This directory contains the **runnable pipeline entrypoints** for literature imports.

These scripts are thin CLIs that call into the core `lit_import` modules (e.g. `usfm_import`, `usfm_parser`, `kjv_strongs_import`) to build the site data under `docs/data/v1/lit/...`.

Typical usage:

- `bible_import_cli.py`  
  Import one or more Bible translations from raw USFM bundles into the processed format.

- `strongs_import.py`  
  Import Strong’s Greek/Hebrew lexicon data into `lit/strongs`.

- `split_chapters.py`  
  Split a `chapters.jsonl` file into per-book, per-chapter JSON files under `chapters/BOOK/NNN.json`.

These scripts are safe to run repeatedly; they rebuild data from `lit_import/data/raw/` and write into `lit_import/data/processed/` and/or `docs/data/v1/lit/`.
