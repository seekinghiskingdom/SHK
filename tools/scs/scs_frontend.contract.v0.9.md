# Strong's Concordance Search (SCS) – Frontend Contract v0.9 -AI

This document describes the current (v0.9) frontend contract for the Strong's Concordance Search (SCS) tool. It is intended to keep the HTML/JS implementation and the data contracts aligned while we test and refine for v1.

---

## 1. Page location and layout

- **Jekyll file path:** `docs/tools-games/tools/scs/index.html`
- **Permalink:** `/tools-games/tools/scs/`
- **Layout:** Uses the global `default` layout (`layout: default`) and `{{ site.baseurl }}` for all data URLs.

High-level structure:

1. **Header**
   - Title, short description.
   - Status chip (loading/ready/error) that reflects data load state.

2. **Main content** (two-column grid on desktop, stacked on small screens)
   - **Left panel – Filters**
     - Filter UI is auto-built at runtime from `docs/data/v1/tools/scs/index.json`.
     - Includes:
       - Language (single-select: Greek/Hebrew).
       - Testament (single-select: OT/NT/DC).
       - Book (multi-select).
       - Occurrence count range (min/max).
       - Free-text query (search across Strong's ID, lemma, definitions, and KJV renderings).
   - **Right panel – Results**
     - List of entries rendered as tiles/cards.
     - Summary chip (total entries vs visible entries).
     - Message on empty results or when only a subset is rendered.

---

## 2. Data dependencies

The SCS HTML page depends on:

1. **SCS tool index (frontend config)**
   - Path: `docs/data/v1/tools/scs/index.json`
   - Jekyll URL in HTML:
     - `BASEURL + "/data/v1/tools/scs/index.json"`
   - Key fields used:
     - `filters[]`: describes the filter facets (`language`, `testament`, `book`, `occurrence_range`, `query`).
     - `data.entries`: relative path to the entries JSONL file.

2. **SCS entries dataset**
   - Path (on disk): `docs/data/v1/lit/strongs/concordance/entries.v1.jsonl`
   - URL resolution in HTML:
     - The script builds a URL under `/data/v1/` for this path at runtime.
   - Format:
     - JSON Lines, one Strong's entry per line.
     - Each entry matches the schema in `scs_entries_builder.contract.md` (id, lang, lemma fields, definitions, occurrence_count, books, book_stats, top_kjv_words, example).

The frontend assumes these files exist and are static under `/data/v1/`.

---

## 3. Filter behavior and mapping

Filters are configured by `docs/data/v1/tools/scs/index.json` and interpreted as follows:

- **language**
  - `type: "single-select"`, `field: "lang"`.
  - Values: `"grc"` (Greek), `"he"` (Hebrew).
  - Filter rule: keep entries where `entry.lang === selected`.

- **testament**
  - `type: "single-select"`, `field: "testament"`.
  - Values: `"ot"`, `"nt"`, `"dc"`.
  - Filter rule: keep entries where `entry.testament === selected`.

- **book**
  - `type: "multi-select"`, `field: "books"`.
  - Options are derived from the union of all `entry.books`.
  - Filter rule: entry passes if it has at least one book in the selected set.

- **occurrence_range**
  - `type: "range"`, `field: "occurrence_count"`.
  - Two numeric inputs: `min`, `max`.
  - Filter rule:
    - If `min` is set: `entry.occurrence_count >= min`.
    - If `max` is set: `entry.occurrence_count <= max`.

- **query**
  - `type: "text"`, `fields: ["id","lemma_unicode","lemma_translit","definition","kjv_def","top_kjv_words.w"]`.
  - Filter rule:
    - Lowercased substring match across each field.
    - For `top_kjv_words.w`, matches any rendering string in the array.

Filters are intersected (AND logic). Query is applied last.

---

## 4. Rendering rules (results list)

For each entry:

- **Header**
  - Strong's ID badge (e.g. `G0001`).
  - Lemma (Unicode).
  - Transliteration.

- **Chips**
  - Language (Greek/Hebrew).
  - Testament (OT/NT/DC, or `–` if unknown).
  - Occurrence count in KJV.

- **Definition block**
  - Combined lexicon `definition` and `kjv_def` (if both present).

- **Example verse**
  - If `example` exists, render `book_id chapter:verse – text`.

- **Book metadata (left)**
  - Inline list of `books[]` (short codes like `GEN`, `ROM`).

- **KJV words & per-book stats (right)**
  - Top KJV renderings (`top_kjv_words`) as `word (count)` pairs.
  - Up to 5 `book_stats` entries as `BOOK (count)`, followed by `…` if truncated.
  - Strong's numeric index (`strongs_num`) in a small metadata line.

Rendering limits:

- At most 200 entries are rendered at once. If more match, a message is shown prompting the user to refine filters.

---

## 5. Status, error, and reset behavior

- On initial load:
  - Status chip: `Loading dataset…` (yellow dot).
- On success:
  - Status chip: `Ready` (green dot), meta text shows total entries loaded.
- On error:
  - Status chip: `Error` (red dot), error banner shows the message.

- **Reset button**
  - Clears all filters (language, testament, books, occurrence range, query).
  - Re-renders the full dataset.

---

## 6. Versioning notes

- This contract is **frontend v0.9** for SCS.
- It assumes:
  - Entries dataset is named `entries.v1.jsonl` and compatible with the backend contract.
  - SCS index config is at `docs/data/v1/tools/scs/index.json` and uses the current `filters[]` structure.
- For v1:
  - New facets (e.g., part-of-speech) can be added by extending `filters[]` and updating the frontend logic to handle new `type`/`field` combinations.
