# SCS Entries Builder — Backend Contract -AI

This document defines the backend contract for building the SCS entry dataset used by the Strong’s Concordance Search tool.

The goal is to take the existing Strong’s lexicon data + aligned KJV+Strong’s Bible text and produce a single normalized JSONL file of one entry per Strong’s ID, matching the SCS v1 front-end contract and `docs/data/v1/tools/scs/index.json`.

---

## 1. Scope

**Tool name (backend):** `scs_entries_builder`  
**Primary output:** `docs/data/v1/lit/strongs/concordance/entries.v1.jsonl`  

Responsibilities:

- Read Strong’s lexicon (Greek + Hebrew) from the v1 data tree.
- Read aligned KJV+Strong’s Bible text for usage statistics and example verses.
- Aggregate and normalize everything into per-Strong’s-ID entries for SCS.
- Keep output shape stable for the SCS front-end, even if input formats evolve.

Out of scope for this builder:

- UI behavior, search UI, or SCS HTML rendering.
- Morphological or POS tagging (future extension).
- Multi-translation usage stats (v1 is KJV+Strong’s only).

---

## 2. Inputs and dependencies

All paths are relative to `docs/data/v1/` unless otherwise noted.

### 2.1 Bible works index

- `index.json` (top-level works index), e.g.:

  - `docs/data/v1/index.json`

Must contain at least:

- `bible.en.kjv_strongs` with:

  - `"data_path": "lit/bible/en/kjv_strongs/manifest.json"`

The builder uses this to locate the aligned KJV+Strong’s dataset.

### 2.2 Aligned KJV+Strong’s dataset

- `lit/bible/en/kjv_strongs/manifest.json`
- Chapter files below:

  - `lit/bible/en/kj_strongs/chapters/{BOOK}/{CHAPTER}.json`

Expected minimal chapter schema:

```jsonc
{
  "book_id": "ROM",
  "chapter": 8,
  "verses": [
    {
      "verse": 1,
      "text": "There is therefore now no condemnation...",
      "tokens": [
        { "t": "There", "s": [] },
        { "t": "is", "s": ["G1510"] },
        { "t": "condemnation", "s": ["G2631"] }
      ]
    }
  ]
}
```

Notes:

- `book_id` is a canonical 3–4 letter code (`GEN`, `ROM`, etc.).
- Each token has:

  - `t`: surface word text
  - `s`: list of Strong’s IDs like `"G1510"`, `"H0430"` (already zero-padded).

### 2.3 Strong’s lexicon (Greek + Hebrew)

- Greek: `lit/strongs/grc/lexicon.jsonl`
- Hebrew: `lit/strongs/he/lexicon.jsonl`

Expected minimal per-line schema:

```jsonc
{
  "id": "G0004",
  "n": 4,
  "lemma_unicode": "ἀβαρής",
  "lemma_translit": "abarēs",
  "lemma_beta": "*ABARHS",
  "pronunciation": "ab-ar-ACE'",
  "derivation": "...",
  "definition": "not burdensome",
  "kjv_def": ":--without burden."
}
```

### 2.4 Books metadata

- `books.json`:

  - `docs/data/v1/books.json`

Used for:

- Canonical book ordering (via `order[]`).
- Mapping `book_id → human-readable name` (for optional diagnostics or tooling).
- Optionally, a testament mapping; otherwise a separate hard-coded map can be used.

Minimum assumptions:

- `order` is a list of ordered book IDs.
- `names` maps IDs to names.

---

## 3. Output: `entries.v1.jsonl` schema

**File path (v1):**

- `docs/data/v1/lit/strongs/concordance/entries.v1.jsonl`

Each line is one JSON object representing a Strong’s entry (Greek or Hebrew), designed to match the SCS `index.json` contract.

### 3.1 Required fields

```jsonc
{
  "id": "G0004",          // Strong's ID, prefix + 4-digit zero-padded number
  "lang": "grc",          // "grc" | "he"
  "strongs_num": 4,       // integer n from lexicon

  "testament": "nt",      // "ot" | "nt" | "dc" | null

  "lemma_unicode": "ἀβαρής",
  "lemma_translit": "abarēs",
  "lemma_beta": "*ABARHS",
  "pronunciation": "ab-ar-ACE'",
  "derivation": "of Hebrew origin ...",
  "definition": "weightless, i.e. not burdensome",
  "kjv_def": ":--from being burdensome.",

  "occurrence_count": 5,  // total tokens in KJV+Strong's

  "books": ["ACT", "ROM"],  // sorted list of book_ids where the Strong's ID occurs

  "book_stats": {          // per-book counts (keys = book_ids)
    "ACT": 3,
    "ROM": 2
  },

  "top_kjv_words": [       // most common KJV surface forms for this Strong's ID
    { "w": "light", "c": 3 },
    { "w": "not burdensome", "c": 2 }
  ],

  "example": {             // one representative verse (for tiles/snippets)
    "book_id": "ROM",
    "chapter": 15,
    "verse": 1,
    "text": "We then that are strong ought to bear the infirmities of the weak..."
  }

  // future expansion: "pos", "domain", "person_type", etc.
}
```

### 3.2 Invariants

- Every Strong’s ID present in the lexicon must produce one output entry.
- Entries with 0 aligned KJV occurrences:

  - `occurrence_count = 0`
  - `books = []`
  - `book_stats = {}`
  - `top_kjv_words = []`
  - `example = null`

---

## 4. Algorithm (high-level)

The builder runs in three phases:

1. **Lexicon load + base entry initialization**

   - Stream Greek and Hebrew lexicon JSONL files.
   - For each line, construct a base entry with core lexicon fields and zeroed usage stats:

     - `occurrence_count = 0`
     - `books = set()` (temporary)
     - `book_stats = {}`
     - `word_counts = {}` (temporary, for top_kjv_words)
     - `example = null`

   - Store entries in a dict keyed by `id`:

     - `entries: Dict[str, Entry]` (e.g., `"G0004" → {...}`).

2. **Usage aggregation from KJV+Strong’s**

   - Locate KJV+Strong’s via `bible.en.kjv_strongs` in `index.json`.
   - Iterate all chapter files under the aligned dataset.
   - For each verse:

     - For each token:

       - Normalize the surface word to a `word_key` (e.g., lowercase + strip punctuation).
       - For each Strong’s tag in `token.s`:

         - Normalize to `G0004` / `H0430`.
         - Lookup entry in `entries`.
         - Increment:

           - `occurrence_count`
           - `book_stats[book_id]`
           - `books` set
           - `word_counts[word_key]`

         - If `example` is `null`, set it to this verse object (book/chapter/verse/text).

3. **Finalization + JSONL write**

   - For each entry:

     - Convert `books` from set to sorted list (using canonical `books.order`).
     - Normalize and sort `book_stats` by book id.
     - Derive `testament`:

       - From a mapping `book_id -> "ot" | "nt" | "dc"`.
       - If an entry appears in multiple testaments (should not occur in practice), set `testament = null`.

     - Compute `top_kjv_words`:

       - Sort `word_counts` by frequency desc, then alphabetically.
       - Take the top N (default: 5).
       - Build `[{ "w": word, "c": count }, ...]`.

     - Remove internal field `word_counts`.

   - Write `entries.v1.jsonl`:

     - Sort entries by `(id[0], strongs_num)` (i.e., group by `G` vs `H`, then numeric).
     - Emit one compact JSON object per line, UTF-8, `ensure_ascii=false`.

---

## 5. Code layout (tools/scs)

Recommended layout under the repo root:

```text
tools/
  scs/
    scs_entries_builder.contract.md   # this file
    README.md                         # optional brief summary + usage
    config/
      scs_entries_builder.config.v1.json   # input/output paths, options
    src/
      __init__.py
      scs_entries_builder.py          # main implementation of the algorithm
    scripts/
      build_scs_entries.py            # thin CLI wrapper for local runs
```

### 5.1 `config/scs_entries_builder.config.v1.json`

Configuration file to decouple code from specific paths. Example:

```jsonc
{
  "version": "1.0.0",
  "data_root": "docs/data/v1",
  "works_index": "docs/data/v1/index.json",
  "books_file": "docs/data/v1/books.json",

  "lexicon": {
    "grc": "docs/data/v1/lit/strongs/grc/lexicon.jsonl",
    "he":  "docs/data/v1/lit/strongs/he/lexicon.jsonl"
  },

  "aligned_bible_work_id": "bible.en.kjv_strongs",

  "output_entries": "docs/data/v1/lit/strongs/concordance/entries.v1.jsonl",

  "top_kjv_words_limit": 5,
  "include_zero_occurrence_entries": true
}
```

### 5.2 `src/scs_entries_builder.py`

Responsibilities:

- Load config JSON.
- Resolve all input/output paths.
- Implement the three-phase algorithm:

  1. Build `entries` dict from lexicon.
  2. Scan aligned KJV+Strong’s to fill usage stats.
  3. Finalize entries and write JSONL.

- Expose a main function, e.g.:

  - `build_entries(config: dict) -> None`

### 5.3 `scripts/build_scs_entries.py`

Thin CLI entry point:

- Parse a `--config` argument (default to `tools/scs/config/scs_entries_builder.config.v1.json`).
- Import and call `build_entries(config)`.

---

## 6. Decisions and configurable choices

The following are considered configuration or policy decisions and not hard-coded in the contract:

1. **Whether to include zero-occurrence entries**

   - Default: `include_zero_occurrence_entries = true`.

2. **Top KJV words cutoff**

   - Default: `top_kjv_words_limit = 5` (can be changed via config).

3. **Surface word normalization**

   - Default: lowercase and strip basic punctuation.
   - Exact normalization rules should be implemented in one helper function and referenced in this contract once stabilized.

4. **Book → testament mapping**

   - Can be embedded in code or stored as a separate config file.
   - Must map each `book_id` in the aligned dataset to `"ot"`, `"nt"`, `"dc"`, or `null`.

5. **Error handling**

   - Policy for missing entries (e.g., Strong’s ID in aligned text not present in lexicon) should be:

     - Log + skip (default), or
     - Strict (raise error).

   - This should be configurable for debugging vs production runs.

---

## 7. Implementation checklist

For v1, a build is considered complete when:

1. `config/scs_entries_builder.config.v1.json` exists and points to real files.
2. `src/scs_entries_builder.py` implements the algorithm in this contract.
3. `scripts/build_scs_entries.py` successfully generates `entries.v1.jsonl` from a clean checkout.
4. `entries.v1.jsonl` passes basic validation:

   - One JSON object per line.
   - All Strong’s IDs from both lexicons present.
   - A sample of entries match expected counts from the aligned KJV+Strong’s dataset.

Once this is stable, SCS front-end work can rely on `entries.v1.jsonl` and `docs/data/v1/tools/scs/index.json` as the canonical data sources.
