# SHK Data v1

This directory contains the version 1 snapshot of static data used by the SHK site.

## Layout

- `lit/` – Literature datasets
  - `bible/` – Bible translations
  - `strongs/` – Strong’s lexicon data
  - `historical/` – Historical Christian texts (e.g., creeds)
- `manifest.json` – Registry of datasets grouped by family (bible, strongs, historical, etc.).
- `index.json` – Optional higher-level index of works for tools and UI.

## Bible translations

Each translation lives in:

- `lit/bible/<lang>/<code>/`

and contains:

- `manifest.json` – identity (id, code, language, title, canon, status, features) and file pointers.
- `meta.json` – provenance (source provider, raw file path, license note) and basic counts (books, chapters, verses).
- `books.json` – book IDs and names for that translation’s canon.
- `chapters/BOOK/NNN.json` – one JSON file per chapter with a `verses` array.

In v1:

- All translations store **plain human-readable verse text** in `verses[].text`, except:
- `en/kjv_strongs`, which is marked with `features.has_strongs = true` and keeps Strong’s-style tagging in the text for Strong’s-aware tools.

Raw USFM/XML sources and richer tagged forms are kept under `tools/lit-import/data/raw/` (not deployed).

## Strong’s

The Strong’s lexicon lives under:

- `lit/strongs/`

with subdirectories for Greek and Hebrew. These provide dictionary/lexicon entries keyed by Strong’s IDs and are used by Strong’s-aware tools.

## Historical texts

Historical Christian texts (e.g., creeds) live under:

- `lit/historical/<group>/<slug>/`

Each such directory has:

- `manifest.json` – identity and file pointers.
- One or more text files (e.g., `apostles-creed.txt`) referenced from `manifest.files.text`.
