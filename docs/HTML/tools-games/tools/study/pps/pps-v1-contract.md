# Proverb Pair Search (PPS) – v1 Data & Pipeline Contract

This document defines the v1 contract for Proverb Pair Search (PPS) data and the pipeline that builds the site-facing JSON used by the PPS tool.

---

## 0. High-Level Flow

PPS v1 takes a manually maintained spreadsheet of Proverb pairs and produces a clean, slim JSON file for the site.

**Pipeline overview**

1. **1.0 – Source prep (manual)**  
   - You maintain `pairs.xlsx` (sheet `pairs`).  
   - You export `pairs.csv`.

2. **2.0 – Master build (automated)**  
   - `pairs.csv` → `input_pairs.json` (full, structured, pair-based master).

3. **3.0 – Scripture enrichment (skipped in v1)**  
   - Bible text is not embedded in PPS data in v1.  
   - Bible text is fetched at runtime by Bible tools from shared Bible data.

4. **4.0 – Site export (automated)**  
   - `input_pairs.json` + `pps_export_config.json` →  
     - `final_pairs.json` (slim, site-facing data)  
     - `final_pairs_warnings.json` (diagnostic log)

All automated steps treat upstream files as read-only.

---

## 1. Files and Locations

### 1.1 Recommended locations

- **Spec (this file)**  
  - `docs/specs/tools/pps/pps-v1-contract.md`

- **Pipeline data/config**  
  - `docs/data/v1/pps/`
    - `pairs.csv` (intermediate, from `pairs.xlsx`)  
    - `input_pairs.json`  
    - `final_pairs.json`  
    - `final_pairs_warnings.json`  
    - `pps_export_config.json`

Bible data and Bible tools contracts live elsewhere (e.g. `docs/data/v1/tools/bible-viewer/…`) and are not duplicated here.

### 1.2 Source files

- `pairs.xlsx`
  - Maintained manually.
  - Sheet: `pairs`.
  - Columns logically grouped into six sections using prefixes:
    - `S.` – Status / version info
    - `R.` – Reference info
    - `P.` – Pair-level info
    - `X.` – Antecedent info
    - `Y.` – Consequent info
    - `T.` – Relationship info

- `pairs.csv`
  - Export from `pairs.xlsx` / `pairs` sheet.
  - First row is header.
  - Column names use prefixes `S.`, `R.`, `P.`, `X.`, `Y.`, `T.` wherever possible.
  - Non-prefixed headers are allowed and will be mapped or defaulted.

---

## 2. Step 2.0 – Master Build (`pairs.csv` → `input_pairs.json`)

### 2.1 Purpose

Convert `pairs.csv` into a “master” JSON with:

- One object per valid pair (row).
- Fields grouped into `S`, `R`, `P`, `X`, `Y`, `T` sections.
- Minimal metadata and stats.

### 2.2 Input

- `pairs.csv` (exported from `pairs.xlsx` / `pairs` sheet).

### 2.3 Output: `input_pairs.json`

Top-level structure:

```jsonc
{
  "meta": {
    "generated_at": "2025-..",
    "source": {
      "file": "pairs.csv",
      "sheet": "pairs",
      "version": "v1"
    },
    "schema": {
      "S": ["status", "rv", "uv", "..."],
      "R": ["book", "book_name", "chapter", "pv", "verse", "ref_id", "ref_str", "..."],
      "P": ["..."],
      "X": ["..."],
      "Y": ["..."],
      "T": ["..."]
    },
    "stats": {
      "pairs_total": 0,
      "books": [],
      "chapters": [],
      "skipped_rows": 0
    }
  },
  "pairs": [
    {
      "pair_id": "pro.18.10.a",
      "S": { /* all S.* columns for this row */ },
      "R": { /* all R.* columns for this row */ },
      "P": { /* all P.* columns for this row */ },
      "X": { /* all X.* columns for this row */ },
      "Y": { /* all Y.* columns for this row */ },
      "T": { /* all T.* columns for this row */ }
    }
  ]
}
```

### 2.4 Column grouping rules

For each header in `pairs.csv`:

- If prefixed:
  - `S.xxx` → section `S`, field `xxx`.
  - `R.xxx` → section `R`, field `xxx`.
  - `P.xxx` → section `P`, field `xxx`.
  - `X.xxx` → section `X`, field `xxx`.
  - `Y.xxx` → section `Y`, field `xxx`.
  - `T.xxx` → section `T`, field `xxx`.

- If **not** prefixed:
  - May be mapped by a small internal rule (e.g. `Book` → `R.book`), or
  - Defaulted into a reasonable section (e.g. `P`) if no mapping exists.

`meta.schema` is the discovered field list for each section, after prefix removal.

### 2.5 Row inclusion rules

A row becomes a PPS pair if it passes basic checks, for example:

- `R.book` and `R.chapter` are not empty, and  
- At least one of:
  - `X.key`  
  - `Y.key`  
  - `P.label`  
  is non-empty.

Rows that fail these checks:

- Are **skipped** from the `pairs` array.
- Are counted in `meta.stats.skipped_rows`.

### 2.6 Pair ID rules

Each pair object has a `pair_id`:

- If a dedicated ID column exists in the sheet: use that.
- Otherwise, construct:

```text
<book>.<chapter>.<pv>[.<index>]
```

- `<index>` is only added if there are multiple pairs with the same `<book>.<chapter>.<pv>`.

### 2.7 Blanks

- Blank cells in `pairs.csv` become `null` (or consistently empty string) in `input_pairs.json`.
- No synthetic placeholder strings like `"undefined"` are introduced at this stage.

---

## 3. Reference (`R`) Contract for `input_pairs.json`

Each pair’s `R` section must include at least the following fields, which are used to integrate with the shared Bible tools.

### 3.1 Required `R` fields

- `book` (string)  
  Canonical book code used by Bible tools (e.g. `"pro"`).

- `book_name` (string)  
  Human-readable book name (e.g. `"Proverbs"`).

- `chapter` (integer)  
  Chapter number (e.g. `18`).

- `pv` (integer or string)  
  “Pair verse” / entry index within the chapter (e.g. `10`).

- `verse` (integer or null)  
  Actual verse number if distinct from `pv`. If same, may be identical or `null`.

- `ref_id` (string)  
  Canonical reference id, e.g. `"pro.18.10"`.

- `ref_str` (string)  
  Display reference string, e.g. `"Proverbs 18:10"`.

Other `R.*` columns from the sheet may exist but are optional and not required by the v1 PPS contract.

### 3.2 Scripture for v1

- PPS v1 does **not** embed Bible text in its own JSON.
- All Bible text is resolved at runtime using:
  - `ref.book`
  - `ref.chapter`
  - `ref.pv` / `ref_id`
- The Bible tools index and translation files (elsewhere in the project) are the source of truth for verse text.

---

## 4. Step 3.0 – Scripture Enrichment (Future)

- No enrichment step is used in v1.
- `input_pairs.json` remains free of verse text.
- This step is reserved for possible future versions if pre-attached verse text is ever needed.

---

## 5. Step 4.0 – Site Export

### 5.1 Purpose

Transform the master `input_pairs.json` into a slim, site-ready `final_pairs.json` and a diagnostic `final_pairs_warnings.json`, controlled by a configuration file.

Inputs:

- `input_pairs.json`
- `pps_export_config.json`

Outputs:

- `final_pairs.json`
- `final_pairs_warnings.json`

---

## 6. `pps_export_config.json` – Config Contract

### 6.1 Purpose

The config decides which fields from `input_pairs.json` are exported, where they go in `final_pairs.json`, and which are considered required.

### 6.2 Structure

Example v1 config:

```jsonc
{
  "input_file": "input_pairs.json",
  "output_file": "final_pairs.json",
  "warnings_file": "final_pairs_warnings.json",

  "mappings": {
    "id": "pair_id",

    "ref": {
      "book": "R.book",
      "book_name": "R.book_name",
      "chapter": "R.chapter",
      "pv": "R.pv",
      "ref_id": "R.ref_id",
      "ref_str": "R.ref_str"
    },

    "status": {
      "status": "S.status",
      "rv": "S.rv",
      "uv": "S.uv"
    },

    "x": {
      "key": "X.key",
      "group": "X.group"
    },

    "y": {
      "key": "Y.key",
      "group": "Y.group"
    }
  },

  "required_fields": [
    "ref.book",
    "ref.chapter",
    "ref.ref_id",
    "x.key",
    "y.key"
  ]
}
```

### 6.3 Rules

- Only fields listed in `mappings` appear in `final_pairs.json`.
- All other fields remain in `input_pairs.json` only.
- `required_fields` list paths in the **final** object shape:
  - e.g. `"ref.book"`, `"x.key"`.

---

## 7. `final_pairs.json` – v1 Contract

### 7.1 Top-level

```jsonc
{
  "meta": {
    "generated_at": "2025-..",
    "source": {
      "master_file": "input_pairs.json",
      "config_file": "pps_export_config.json"
    },
    "stats": {
      "pairs_total": 0,
      "books": [],
      "chapters": []
    }
  },
  "pairs": [
    {
      "id": "pro.18.10.a",
      "ref": { ... },
      "status": { ... },
      "x": { ... },
      "y": { ... }
    }
  ]
}
```

### 7.2 `pairs` objects

Each pair object has:

- **Top-level**
  - `id` (string)  
    - Stable pair identifier, e.g. `"pro.18.10.a"`.

- **`ref` block**

  ```jsonc
  "ref": {
    "book": "pro",
    "book_name": "Proverbs",
    "chapter": 18,
    "pv": 10,
    "ref_id": "pro.18.10",
    "ref_str": "Proverbs 18:10"
  }
  ```

  - `book` – canonical book code (string).
  - `book_name` – human-readable book name (string).
  - `chapter` – chapter number (integer).
  - `pv` – pair verse / entry index (int or string).
  - `ref_id` – canonical reference id (`"book.chapter.pv"`).
  - `ref_str` – formatted reference string.

- **`status` block**

  ```jsonc
  "status": {
    "status": "r",
    "rv": "1.0.0",
    "uv": "1.0.1"
  }
  ```

  - `status` – status code (e.g. `r`, `p`, `ip`).
  - `rv` – release version (e.g. `"1.0.0"`).
  - `uv` – last update version (e.g. `"1.1.0"`).

- **`x` block**

  ```jsonc
  "x": {
    "key": "righteousness",
    "group": "righteousness"
  }
  ```

  - `key` – X-side key (e.g. main concept).
  - `group` – X-side group/category.

- **`y` block**

  ```jsonc
  "y": {
    "key": "safety",
    "group": "salvation"
  }
  ```

  - `key` – Y-side key.
  - `group` – Y-side group/category.

No additional fields are guaranteed in `final_pairs.json` for v1.

---

## 8. `final_pairs_warnings.json` – Contract

### 8.1 Top-level

```jsonc
{
  "meta": {
    "generated_at": "2025-..",
    "source": {
      "master_file": "input_pairs.json",
      "config_file": "pps_export_config.json"
    },
    "stats": {
      "pairs_total": 0,
      "warnings_total": 0
    }
  },
  "warnings": [
    {
      "id": "pro.18.10.a",
      "missing_fields": ["ref.ref_id", "x.key"],
      "notes": "Missing required fields; pair kept in output."
    }
  ]
}
```

### 8.2 Rules

- Each warning corresponds to a pair that **does** exist in `final_pairs.json`.
- `missing_fields` lists any paths from `required_fields` that were blank/missing.
- Pairs are **never removed** from `final_pairs.json` because of warnings; this file is for diagnostics only.

---

## 9. v1 Summary

- You maintain only `pairs.xlsx` and export `pairs.csv`.
- The pipeline guarantees:
  - `pairs.csv` → `input_pairs.json` (full, structured, pair-based master).
  - `input_pairs.json` + `pps_export_config.json` → `final_pairs.json` + `final_pairs_warnings.json` (slim, site-facing).
- Bible text and highlighting are provided by the shared Bible tools at runtime, using the `ref` block (especially `book`, `chapter`, `pv`, `ref_id`).

This contract describes the PPS v1 data shapes and pipeline behavior. Any pipeline implementation must conform to this document.
