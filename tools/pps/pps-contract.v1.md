# Proverb Pair Search (PPS) – v1 Contract

_Last updated: 2025-11-23_

This document defines the v1 contract for the **Proverb Pair Search (PPS)** data, pipeline, and front-end tools. It is intended as a reference for any scripts, tools, or visualizations (including the Bubble Map view) that consume PPS data.

---

## 1. Concept and Purpose

- **Name:** Proverb Pair Search (**PPS**)
- **Scope:** Currently operates on curated proverb pairs from **Proverbs**.
- **Core object:** A **pair** is an X→Y relationship for a particular verse (or verse span) in Proverbs.
  - **X side** = antecedent concept (e.g., behavior, condition).
  - **Y side** = consequent concept (e.g., result, outcome, virtue, warning).
- **Primary tools:**
  - **PPS list view** (current HTML page): filter pairs and display them as a list.
  - **Future Bubble Map view:** aggregate keys/groups into nodes (bubbles) and X–Y relationships into edges between bubbles.

PPS is driven entirely by a JSON export (`final_pairs.json`) that is generated from a manually curated CSV via a small conversion pipeline.

---

## 2. Data Pipeline Overview and File Locations

### 2.1. Raw input

- **Source:** Hand-maintained Excel/CSV of proverb pairs.
- **Canonical CSV used by the pipeline:**
  - `tools/pps/data/input/pps.data.input.pairs.csv`
- **Column sections (by prefix in the header row):**
  1. `S.*` – **Status / metadata**
     - Examples: `S.status`, `S.rv`, `S.uv`.
  2. `R.*` – **Reference**
     - Examples: `R.book`, `R.book_name`, `R.chapter`, `R.verse_start`, `R.verse_end`, `R.ref_id`, `R.ref_str`.
  3. `P.*` – **Primary info** (key/type; largely ignored in v1 output).
  4. `X.*` – **X-side info** (antecedent)
     - At minimum: `X.key`, `X.group`.
  5. `Y.*` – **Y-side info** (consequent)
     - At minimum: `Y.key`, `Y.group`.
  6. `T.*` – **Type / relationship** (mostly ignored in v1 output).

The sheet may also contain additional columns within each section; the pipeline is designed not to break if extra columns are present.

### 2.2. Intermediate JSON

- **Script:** `tools/pps/scripts/build_input_pairs.py`
- **Input:** `tools/pps/data/input/pps.data.input.pairs.csv`
- **Output:** `tools/pps/data/input/input_pairs.json`

Purpose of `input_pairs.json`:
- Preserve almost all CSV information with a structured grouping by sections.
- Provide a stable intermediate representation for later conversions or checks.
- Not required by client-side tools; only used by backend scripts.

### 2.3. Final site-facing data and config

These are the files consumed by front-end tools (list view, Bubble Map, etc.).

1. **Final pairs data (main source of truth):**
   - Repo path: `docs/data/v1/pps/final_pairs.json`
   - Jekyll URL: `{{ '/data/v1/pps/final_pairs.json' | relative_url }}`

2. **Export config (describes which fields are exposed):**
   - Repo path: `docs/data/v1/pps/pps_export_config.v1.json`
   - Jekyll URL: `{{ '/data/v1/pps/pps_export_config.v1.json' | relative_url }}`

3. **Warnings report (non-fatal issues during export):**
   - Repo path: `docs/data/v1/pps/final_pairs_warnings.json`
   - Jekyll URL: `{{ '/data/v1/pps/final_pairs_warnings.json' | relative_url }}`

All front-end tooling should treat `final_pairs.json` as the canonical data file, and may optionally read the config/warnings files for metadata and diagnostics.

---

## 3. `final_pairs.json` – Structure and Semantics

### 3.1. Top-level shape

```jsonc
{
  "meta": {
    "generated_at": "YYYY-MM-DDTHH:MM:SSZ",
    "source_files": [
      "tools/pps/data/input/pps.data.input.pairs.csv"
    ],
    "stats": {
      "pairs_total": 476,
      "books": ["prov"],
      "chapters": [ /* list of unique chapter numbers */ ]
      // (optionally other summary stats)
    }
  },
  "pairs": [
    {
      "id": "prov.18.01.a",
      "status": { ... },
      "ref": { ... },
      "x": { ... },
      "y": { ... }
    }
    // ...
  ]
}
```

### 3.2. Per-pair structure

Each entry in `pairs` represents one X→Y relationship.

```jsonc
{
  "id": "prov.18.01.a",

  "status": {
    "status": "R",       // e.g., R=Ready (string, may be empty)
    "rv": "1.0.0",       // release version (string, may be empty)
    "uv": "1.0.0"        // last update version (string, may be empty)
  },

  "ref": {
    "book": "prov",          // book code (string, e.g., "prov")
    "book_name": "Proverbs", // friendly name for display
    "chapter": 18,           // numeric chapter where possible
    "verse_start": 1,        // numeric, where possible
    "verse_end": 1,          // numeric, where possible
    "ref_id": "Prov 18:1",   // reference ID, safe for sorting
    "ref_str": "Proverbs 18:1" // human-readable reference string
  },

  "x": {
    "key":   "SELF-ISOLATION", // X.key; string or empty
    "group": "COMMUNITY"       // X.group; string or empty
  },

  "y": {
    "key":   "SELFISH DESIRE", // Y.key; string or empty
    "group": "MOTIVATION"      // Y.group; string or empty
  }
}
```

### 3.3. Important conventions

- `status.status`, `status.rv`, `status.uv`:
  - Always present in the object, but may be `""` (empty).
  - v1 front-end uses `status.status` as a main filter (e.g., `"R"` for ready).
- `ref.book` vs `ref.book_name`:
  - `ref.book` is a short, machine-oriented code (e.g., `"prov"`).
  - `ref.book_name` is the full display name (e.g., `"Proverbs"`).
- `ref.chapter` and `ref.verse_*`:
  - Typically numeric; tools should be robust if values are stored as strings.
- `ref.ref_id` / `ref.ref_str`:
  - Safe, displayable ID strings for sorting and labels.
- `x.*` and `y.*` fields:
  - `x.key`, `x.group`, `y.key`, `y.group` may be empty strings.
  - Client tools should treat empty as “blank / undefined” (often displayed as `–`).

All aggregation, filtering, and visualization logic should work directly on these fields, without needing to know the original CSV structure.

---

## 4. Current PPS List View – Behavior and Filters

### 4.1. Page and paths

- **PPS list view URL:** `/tools-games/tools/pps/`
- **Data loaded:**  
  - `final_pairs.json` (core data)  
  - `pps_export_config.v1.json` (metadata)  
  - `final_pairs_warnings.json` (warnings count)

### 4.2. Filters

The list view currently supports:

1. **Book**
   - Single-select `<select>`; currently mostly just `"Proverbs"` (`"prov"`), but designed to support multiple books later.
2. **Chapter**
   - Single-select `<select>`; options are derived from the selected book.
3. **Status**
   - Single-select `<select>`; values come from `status.status` across all pairs.
4. **Mode: Key vs Group**
   - Toggle (`"key"` / `"group"`), persisted in `localStorage` under key `"pps_mode"`.
   - Determines whether X/Y filters and displays use `.key` fields or `.group` fields.
5. **X filter**
   - Multi-select **dropdown with checkboxes**.
   - Values depend on the current **Book/Chapter/Status** filters.
   - Options include a special “blank” value for pairs where the selected field is empty.
   - Selecting none = “All X” (no extra filter).
6. **Y filter**
   - Same behavior as X filter, but for Y side.

### 4.3. Sorting

- Sort dropdown options:
  - `ref` (default): by `ref.ref_id` / `ref.ref_str`.
  - `book_ch`: by `ref.book`, then `chapter`, then `ref_id`.
  - `x_key`: by `x.key`, then `ref.ref_id`.
  - `y_key`: by `y.key`, then `ref.ref_id`.
  - `x_group`: by `x.group`, then `ref.ref_id`.
  - `y_group`: by `y.group`, then `ref.ref_id`.

The list view always sorts the final filtered set using one of these strategies.

### 4.4. Filtering order and logic

1. Start from all pairs in `final_pairs.json`.
2. Apply **Book**, **Chapter**, and **Status** filters to get a **base subset**.
3. Build **X/Y option sets** from that base subset:
   - If mode = `key`, options come from `x.key` / `y.key` in the base subset.
   - If mode = `group`, options come from `x.group` / `y.group` in the base subset.
   - Include a special “blank” option for any empty values.
4. Apply **X** and **Y** selections on top of the base subset:
   - If no X values selected: no X-filter is applied (equivalent to “All X”).  
   - If no Y values selected: no Y-filter is applied (equivalent to “All Y”).  
   - Otherwise: a pair is kept if its X or Y value is in the selected set.
5. Apply the chosen sort mode to the final filtered list.
6. Render the cards for each pair, showing:
   - Reference (`ref.ref_str` or `ref.ref_id`).
   - Status chip (`status.status` + `status.uv`/`status.rv` if present).
   - X side (`x.key`, `x.group`).
   - Y side (`y.key`, `y.group`).
   - Meta row (`id` and `ref.ref_id`).

---

## 5. Bubble Map View – Contract for Downstream Tools

The Bubble Map (or any future PPS visualizations) should follow these rules:

1. **Data source**
   - Use **only** `docs/data/v1/pps/final_pairs.json` for the pair-level data.
   - Optionally use `pps_export_config.v1.json` for sanity checks (fields, versions, etc.).

2. **Shared filters**
   - Reuse the same conceptual filters as the list view:
     - Book (from `ref.book` / `ref.book_name`).
     - Chapter (from `ref.chapter`).
     - Status (from `status.status`).
     - Mode: `key` vs `group` (determines how nodes are defined).
   - Filtering order: Book/Chapter/Status → subset → mode-specific X/Y processing.

3. **Node construction (bubbles)**
   - For the current filtered subset:
     - Collect all distinct values from either:
       - `x.key` and `y.key` (if mode = `key`), or
       - `x.group` and `y.group` (if mode = `group`).
     - Each distinct value becomes a **node**.
     - Node size (radius) is proportional to its frequency in the subset:
       - e.g., count how many times it appears in X or Y positions across all pairs.
     - A “blank” or “undefined” node may be created if empty values are included.

4. **Edge construction (lines)**
   - For each pair in the filtered subset:
     - Define an edge between the X node and the Y node, based on the chosen mode.
   - Multiple pairs with the same X–Y combination can be:
     - Aggregated by an **edge weight** (thicker/darker line), or
     - Counted and displayed as metadata on the edge.
   - The exact visual mapping (e.g., thickness/opacity) is up to the specific tool, but must be based on counts from `final_pairs.json`.

5. **UI expectations**
   - Bubble Map view will likely:
     - Embed a simplified version of the **same filters** as PPS list view at the top.
     - Render only the **visualization** (no list of pairs) in the main area.
   - Any additional interactions (e.g., clicking a node to highlight its edges or show a list of related verses) should derive from the same `final_pairs.json` pairs and the active filters.

---

## 6. Versioning Notes

- **Current contract:** PPS v1 (`final_pairs.json` + `pps_export_config.v1.json`).
- Any incompatible changes to:
  - JSON shape,
  - field names,
  - or semantics (e.g., how `key`/`group` or `status` are used)
  
  should be treated as a **new version** (e.g., `v1.1`, `v2`) and mirrored under a new path such as `docs/data/v2/pps/` with an updated contract file.

- This contract file should live somewhere like:
  - `docs/specs/pps-contract.v1.md`
  - or `tools/pps/docs/pps-contract.v1.md`

and should be updated whenever the PPS pipeline or front-end behavior changes in a way that affects consumers.
