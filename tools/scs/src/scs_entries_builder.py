"""
SCS Entries Builder -AI

Builds the Strong's Concordance Search (SCS) entries dataset
from the Strong's lexicon (Greek + Hebrew) and the aligned
KJV+Strong's Bible text.

Configured by tools/scs/config/scs_entries_builder.config.v1.json
"""

from __future__ import annotations

import argparse
import json
import logging
import string
from pathlib import Path
from typing import Any, Dict, List, Tuple


# ---------------------------
# Config loading / utilities
# ---------------------------


def load_config(path: str | Path) -> Dict[str, Any]:
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        cfg = json.load(f)

    # Basic defaults
    cfg.setdefault("top_kjv_words_limit", 5)
    cfg.setdefault("include_zero_occurrence_entries", True)
    cfg.setdefault("missing_strongs_policy", "log_and_skip")

    return cfg


def load_books_metadata(books_file: str | Path) -> Tuple[List[str], Dict[str, str]]:
    """
    Load books.json and derive:
      - books_order: canonical book id order
      - book_to_testament: mapping book_id -> "ot" | "nt"
    """
    books_file = Path(books_file)
    with books_file.open("r", encoding="utf-8") as f:
        data = json.load(f)

    books_order: List[str] = data.get("order", [])
    if not books_order:
        raise RuntimeError("books.json has no 'order' field or it is empty")

    # Derive testament mapping from order.
    # For a standard 66-book canon, MAT marks the start of NT.
    try:
        mat_idx = books_order.index("MAT")
    except ValueError:
        # Fallback: assume OT/NT split at 39/27 if we see 66 books.
        if len(books_order) >= 66:
            mat_idx = 39
        else:
            mat_idx = len(books_order)

    book_to_testament: Dict[str, str] = {}
    for i, bid in enumerate(books_order):
        if i < mat_idx:
            book_to_testament[bid] = "ot"
        else:
            book_to_testament[bid] = "nt"

    return books_order, book_to_testament


def resolve_kjv_chapters_root(cfg: Dict[str, Any]) -> Path:
    """
    Use works_index + aligned_bible_work_id to locate the
    KJV+Strong's chapters directory.
    """
    data_root = Path(cfg["data_root"])
    works_index_path = Path(cfg["works_index"])
    aligned_id = cfg["aligned_bible_work_id"]

    with works_index_path.open("r", encoding="utf-8") as f:
        idx = json.load(f)

    works = idx.get("works", [])
    target = None
    for w in works:
        if w.get("id") == aligned_id:
            target = w
            break

    if target is None:
        raise RuntimeError(f"Work id {aligned_id!r} not found in {works_index_path}")

    data_path = target.get("data_path")
    if not data_path:
        raise RuntimeError(f"Work {aligned_id!r} has no 'data_path' in {works_index_path}")

    manifest_rel = Path(data_path)  # e.g. lit/bible/en/kjv_strongs/manifest.json
    base_dir = (data_root / manifest_rel).parent
    chapters_root = base_dir / "chapters"

    if not chapters_root.is_dir():
        raise RuntimeError(f"Chapters directory not found: {chapters_root}")

    return chapters_root


# ---------------------------
# Core algorithm helpers
# ---------------------------


def normalize_strongs_id(raw: str) -> str:
    """
    Normalize Strong's ID to prefix + 4-digit zero-padded format,
    e.g. "G1" -> "G0001", "H0430" -> "H0430".
    """
    raw = raw.strip()
    if not raw:
        return raw
    prefix = raw[0].upper()
    num_part = raw[1:]
    # Some inputs may already be padded; int() handles both.
    try:
        n = int(num_part)
    except ValueError:
        # If malformed, just return upper-cased as-is.
        return raw.upper()
    return f"{prefix}{n:04d}"


def normalize_word_surface(word: str) -> str:
    """
    Normalize a surface word for counting: lowercased, basic punctuation stripped.
    """
    if not word:
        return ""
    # Strip leading/trailing punctuation, lower-case
    return word.strip(string.punctuation).lower()


def load_lexicon(cfg: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Load Greek and Hebrew Strong's lexicon JSONL files and
    initialize the entries dict keyed by Strong's ID.
    """
    lex_cfg = cfg["lexicon"]
    paths = [
        ("grc", Path(lex_cfg["grc"])),
        ("he", Path(lex_cfg["he"])),
    ]

    entries: Dict[str, Dict[str, Any]] = {}

    for lang, path in paths:
        if not path.is_file():
            raise RuntimeError(f"Lexicon file not found: {path}")

        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                lex = json.loads(line)
                sid = lex["id"]  # expected "G0001"/"H0001" already
                # Normalize once more for safety
                sid = normalize_strongs_id(sid)

                entry = {
                    "id": sid,
                    "lang": lang,
                    "strongs_num": lex.get("n"),

                    "testament": None,

                    "lemma_unicode": lex.get("lemma_unicode", ""),
                    "lemma_translit": lex.get("lemma_translit", ""),
                    "lemma_beta": lex.get("lemma_beta", ""),
                    "pronunciation": lex.get("pronunciation", ""),
                    "derivation": lex.get("derivation", ""),
                    "definition": lex.get("definition", ""),
                    "kjv_def": lex.get("kjv_def", ""),

                    "occurrence_count": 0,
                    "books": set(),         # temporary
                    "book_stats": {},       # temporary
                    "word_counts": {},      # temporary
                    "example": None,
                }

                entries[sid] = entry

    logging.info("Loaded %d Strong's lexicon entries", len(entries))
    return entries


def iter_chapter_files(chapters_root: Path):
    """
    Yield all chapter JSON files under chapters_root in
    (book_id, chapter_path) order.
    """
    # Expect structure: chapters_root / {BOOK_ID} / {CHAPTER}.json
    for book_dir in sorted(chapters_root.iterdir()):
        if not book_dir.is_dir():
            continue
        for chapter_path in sorted(book_dir.glob("*.json"), key=lambda p: chapter_sort_key(p)):
            yield chapter_path


def chapter_sort_key(path: Path) -> Tuple[int, str]:
    """
    Sort chapters by numeric stem if possible, then by name.
    """
    try:
        n = int(path.stem)
    except ValueError:
        n = 0
    return (n, path.name)


def scan_kjv_strongs(
    cfg: Dict[str, Any],
    entries: Dict[str, Dict[str, Any]],
    chapters_root: Path,
) -> None:
    """
    Walk KJV+Strong's chapters and update occurrence stats in-place.
    """
    missing_policy = cfg.get("missing_strongs_policy", "log_and_skip")
    log_missing = (missing_policy == "log_and_skip")
    strict_missing = (missing_policy == "error")

    chapter_files = list(iter_chapter_files(chapters_root))
    logging.info("Scanning %d chapter files from %s", len(chapter_files), chapters_root)

    for chapter_path in chapter_files:
        with chapter_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        book_id = data.get("book_id")
        chapter_num = data.get("chapter")
        verses = data.get("verses", [])

        for verse in verses:
            verse_num = verse.get("verse")
            verse_text = verse.get("text", "")
            tokens = verse.get("tokens", [])

            for tok in tokens:
                word = tok.get("t", "")
                word_key = normalize_word_surface(word)
                if not word_key:
                    continue

                tags = tok.get("s", []) or []
                for raw_tag in tags:
                    sid = normalize_strongs_id(raw_tag)
                    entry = entries.get(sid)

                    if entry is None:
                        msg = f"Strong's ID {sid!r} in {chapter_path} not found in lexicon"
                        if strict_missing:
                            raise RuntimeError(msg)
                        if log_missing:
                            logging.debug(msg)
                        continue

                    entry["occurrence_count"] += 1

                    # books set
                    entry["books"].add(book_id)

                    # book_stats
                    bs = entry["book_stats"]
                    bs[book_id] = bs.get(book_id, 0) + 1

                    # word_counts
                    wc = entry["word_counts"]
                    wc[word_key] = wc.get(word_key, 0) + 1

                    # example (first occurrence)
                    if entry["example"] is None:
                        entry["example"] = {
                            "book_id": book_id,
                            "chapter": chapter_num,
                            "verse": verse_num,
                            "text": verse_text,
                        }


def finalize_entries(
    cfg: Dict[str, Any],
    entries: Dict[str, Dict[str, Any]],
    books_order: List[str],
    book_to_testament: Dict[str, str],
) -> List[Dict[str, Any]]:
    """
    Finalize entries: convert sets to lists, derive testament,
    compute top_kjv_words, strip internals, and optionally
    drop zero-occurrence entries.
    """
    top_limit = int(cfg.get("top_kjv_words_limit", 5))
    include_zero = bool(cfg.get("include_zero_occurrence_entries", True))

    # Map book_id -> index for canonical sort
    book_index = {bid: i for i, bid in enumerate(books_order)}

    finalized: List[Dict[str, Any]] = []

    for entry in entries.values():
        # Optionally skip zero-occurrence entries
        if not include_zero and entry["occurrence_count"] == 0:
            continue

        # books: set -> sorted list
        book_set = entry["books"]
        sorted_books = sorted(
            book_set,
            key=lambda b: book_index.get(b, 10_000),
        )
        entry["books"] = sorted_books

        # book_stats: sort by canonical order
        bs = entry["book_stats"]
        sorted_bs_items = sorted(
            bs.items(),
            key=lambda kv: book_index.get(kv[0], 10_000),
        )
        entry["book_stats"] = {b: c for b, c in sorted_bs_items}

        # derive testament
        testaments = {book_to_testament.get(b) for b in sorted_books if b in book_to_testament}
        testaments.discard(None)
        if len(testaments) == 1:
            entry["testament"] = next(iter(testaments))
        elif len(testaments) == 0:
            entry["testament"] = None
        else:
            # Mixed (should not happen); mark as None
            entry["testament"] = None

        # top_kjv_words
        wc = entry.get("word_counts", {})
        sorted_words = sorted(
            wc.items(),
            key=lambda kv: (-kv[1], kv[0]),
        )
        top_words = [
            {"w": w, "c": c}
            for w, c in sorted_words[:top_limit]
        ]
        entry["top_kjv_words"] = top_words

        # strip internal field
        if "word_counts" in entry:
            del entry["word_counts"]

        finalized.append(entry)

    # Sort finalized list by (id[0], strongs_num)
    def entry_sort_key(e: Dict[str, Any]):
        sid = e.get("id", "")
        prefix = sid[0] if sid else ""
        num = e.get("strongs_num")
        try:
            num = int(num)
        except Exception:
            num = 0
        return (prefix, num)

    finalized.sort(key=entry_sort_key)
    logging.info("Finalized %d entries for output", len(finalized))
    return finalized


def write_entries(cfg: Dict[str, Any], entries_list: List[Dict[str, Any]]) -> None:
    """
    Write entries to JSONL file at output_entries.
    """
    out_path = Path(cfg["output_entries"])
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as f:
        for entry in entries_list:
            json.dump(entry, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")

    logging.info("Wrote %d entries to %s", len(entries_list), out_path)


# ---------------------------
# Orchestration
# ---------------------------


def build_entries(config_path: str | Path) -> None:
    """
    Orchestrate full build: config -> metadata -> lexicon -> scan -> finalize -> write.
    """
    cfg = load_config(config_path)

    logging.info("Using config: %s", config_path)

    books_order, book_to_testament = load_books_metadata(cfg["books_file"])
    logging.info("Loaded %d books from %s", len(books_order), cfg["books_file"])

    entries = load_lexicon(cfg)

    chapters_root = resolve_kjv_chapters_root(cfg)
    scan_kjv_strongs(cfg, entries, chapters_root)

    finalized = finalize_entries(cfg, entries, books_order, book_to_testament)
    write_entries(cfg, finalized)


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Build SCS entries JSONL from Strong's + KJV-Strong's -AI")
    parser.add_argument(
        "--config",
        default="tools/scs/config/scs_entries_builder.config.v1.json",
        help="Path to config JSON (default: tools/scs/config/scs_entries_builder.config.v1.json)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR)",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="[%(levelname)s] %(message)s",
    )

    build_entries(args.config)


if __name__ == "__main__":
    main()
