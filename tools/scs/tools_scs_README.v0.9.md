# Strong's Concordance Search (SCS) Tools – README v0.9 -AI

This directory contains backend tooling for the Strong's Concordance Search (SCS) feature.

---

## 1. SCS entries builder

**Tool:** `scs_entries_builder`  
**Config:** `tools/scs/config/scs_entries_builder.config.v1.json`  
**Script:** `tools/scs/src/scs_entries_builder.py`

Purpose:

- Read Strong's lexicon data (Greek + Hebrew) from `docs/data/v1/lit/strongs/...`.
- Read aligned KJV+Strong's Bible text from the work `bible.en.kjv_strongs`.
- Aggregate both into one normalized dataset of entries for the SCS frontend.

Output:

- `docs/data/v1/lit/strongs/concordance/entries.v1.jsonl`  
  - One JSON object per Strong's ID.
  - Schema documented in `scs_entries_builder.contract.md`.

---

## 2. How to run

From repo root (with the `shk` environment active):

```bash
python tools/scs/src/scs_entries_builder.py --log-level INFO
```

The script will:

1. Load configuration from `tools/scs/config/scs_entries_builder.config.v1.json`.
2. Resolve the KJV+Strong's chapters directory using `docs/data/v1/lit/index.json`.
3. Build or update `entries.v1.jsonl`.

Re-run this command whenever:

- Strong's lexicon data changes, or
- The aligned KJV+Strong's dataset is updated.

---

## 3. Related files

- `tools/scs/scs_entries_builder.contract.md`  
  Backend contract and algorithm details for the entries builder.
- `docs/data/v1/tools/scs/index.json`  
  Frontend config for the SCS page (filters and data paths).
- `docs/tools-games/tools/scs/index.html`  
  SCS frontend HTML/JS implementation.
