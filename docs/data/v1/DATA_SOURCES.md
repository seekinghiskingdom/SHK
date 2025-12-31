# Data Sources (v1)

This file summarizes the primary data sources used in `docs/data/v1`.  
For exact raw file paths, formats, and counts, see each dataset’s `meta.json`.

## Bible translations

All Bible translations in `lit/bible/` were imported from:

- **eBible.org** – Public-domain and permissively licensed Bible texts in USFM or similar formats.  
  - Website: https://ebible.org

Many of these are historical or specialized editions (e.g., Tyndale, Wycliffe portions, certain LXX/Greek editions) that are distributed via eBible.org. Any such details are recorded in each translation’s `meta.json`.

For each translation:

- `meta.json.source.provider` names the upstream provider (for v1, `eBible.org`).
- `meta.json.source.raw_dir` and related fields point to the raw source bundle under `tools/lit-import/data/raw/bible/...`.
- `meta.json.source.license` and/or `license_note` describe the license or public-domain status as applicable.

Only plain-text chapter files are deployed in `docs/data/v1/lit/bible/...`; the original tagged USFM/XML is kept under `tools/lit-import/data/raw/` for reproducible rebuilds.


## Strong’s lexicon

Strong’s data under `lit/strongs/` is imported via `tools/lit-import` and normalized into JSONL for use by Strong’s-aware tools (e.g., SCS / concordance). The v1 sources are:

* **Greek Strong’s (G####):** MorphGNT “Strong’s Greek Dictionary in XML with real Greek” (Ulrik Sandborg-Petersen), **CC0 1.0**

  * GitHub: [https://github.com/morphgnt/strongs-dictionary-xml](https://github.com/morphgnt/strongs-dictionary-xml)
  * License: [https://creativecommons.org/publicdomain/zero/1.0/](https://creativecommons.org/publicdomain/zero/1.0/)

* **Hebrew Strong’s (H####):** Open Scriptures Hebrew Lexicon (Open Scriptures Hebrew Bible Project), **CC BY 4.0**

  * GitHub: [https://github.com/openscriptures/HebrewLexicon](https://github.com/openscriptures/HebrewLexicon)
  * License: [https://creativecommons.org/licenses/by/4.0/](https://creativecommons.org/licenses/by/4.0/)

Exact source and license information is recorded in:

* `lit/strongs/grc/meta.json` – Greek Strong’s provenance and license.
* `lit/strongs/he/meta.json` – Hebrew Strong’s provenance and license.

These lexicon files power Strong’s-aware features (lookup, concordance, index pages) and are not required for basic Bible text display.


## Historical texts

Historical creeds under `lit/historical/creeds/` (Apostles’, Nicene, Athanasian, Chalcedonian) are taken from public-domain English editions (e.g., Schaff’s translations or equivalent public-domain forms).

Each work’s `manifest.json` and/or `meta.json` includes:

- A short title and group (e.g. `"creeds"`).
- A `files.text` pointer to the deployed text file.
- A brief `source` or `notes` field (where available) describing the edition or known source.

When in doubt, prefer the edition/attribution information in each `meta.json` or `manifest.json` file over this summary.
