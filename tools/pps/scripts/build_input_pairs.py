#!/usr/bin/env python3
"""
PPS v1 – Step 2.1: CSV → input_pairs.json

Reads pairs.csv (exported from pairs.xlsx / sheet "pairs"), builds the
master input_pairs.json in the v1 contract shape:

- Groups fields into S/R/P/X/Y/T sections.
- Adds meta.schema + meta.stats.
- Computes basic reference fields (book_name, ref_id, ref_str) when possible.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Sections used in the PPS v1 contract
SECTION_PREFIXES = {"S", "R", "P", "X", "Y", "T"}

# Map non-prefixed header labels (from the sheet) into S./R. fields.
SPECIAL_HEADER_MAP: Dict[str, Tuple[str, str]] = {
    # Status / meta block
    "Status": ("S", "status"),
    "RV": ("S", "rv"),
    "UV": ("S", "uv"),
    "Stage": ("S", "stage"),
    "X": ("S", "stage_x"),
    "Y": ("S", "stage_y"),
    "T": ("S", "stage_t"),
    "Confidence": ("S", "confidence"),
    # Reference block
    "Book": ("R", "book"),
    "Ch": ("R", "chapter"),
    "Entry": ("R", "entry"),
    "PV": ("R", "pv"),
}


@dataclass
class HeaderMapping:
    """Mapping of CSV columns → (section, field) plus discovered schema."""
    column_map: List[Optional[Tuple[str, str]]]
    schema: Dict[str, List[str]]


def _build_header_mapping(header_row: List[str]) -> HeaderMapping:
    """
    Build mapping from CSV header cells to (section, field) pairs and
    discover the schema for each section.
    """
    column_map: List[Optional[Tuple[str, str]]] = []
    schema: Dict[str, List[str]] = {sec: [] for sec in SECTION_PREFIXES}

    for h in header_row:
        if h is None:
            column_map.append(None)
            continue

        h_str = str(h).strip()
        if not h_str:
            column_map.append(None)
            continue

        sec: Optional[str] = None
        field: Optional[str] = None

        # Case 1: Prefix form like "X.key", "R.book", etc.
        if "." in h_str:
            prefix, rest = h_str.split(".", 1)
            prefix = prefix.strip()
            rest = rest.strip()
            if prefix in SECTION_PREFIXES and rest:
                sec, field = prefix, rest

        # Case 2: Non-prefixed sheet headers like "Status", "RV", "Book", ...
        if sec is None:
            if h_str in SPECIAL_HEADER_MAP:
                sec, field = SPECIAL_HEADER_MAP[h_str]

        if sec is None or field is None:
            column_map.append(None)
            continue

        column_map.append((sec, field))
        if field not in schema[sec]:
            schema[sec].append(field)

    return HeaderMapping(column_map=column_map, schema=schema)


def _read_csv_rows(path: Path) -> List[List[str]]:
    """Read all rows from CSV as raw lists of strings."""
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        return [row for row in reader]


def _parse_pairs(
    rows: List[List[str]],
    mapping: HeaderMapping,
    books_names: Optional[Dict[str, str]] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Convert CSV rows + header mapping into PPS master pair objects and stats.

    - Assumes rows[0] is header.
    - Applies row-inclusion rules.
    - Fills S/R/P/X/Y/T sections for each kept row.
    - Computes book_name, ref_id, ref_str when possible.
    """
    if not rows:
        return [], {"pairs_total": 0, "books": [], "chapters": [], "skipped_rows": 0}

    header_map = mapping.column_map
    data_rows = rows[1:]  # skip header row

    pairs: List[Dict[str, Any]] = []
    skipped_rows = 0
    book_set = set()
    chapter_set = set()
    id_counter: Counter[str] = Counter()

    for idx, row in enumerate(data_rows, start=1):
        sections: Dict[str, Dict[str, Any]] = {sec: {} for sec in SECTION_PREFIXES}

        # Fill sections from the row using the header mapping.
        for col_idx, cell in enumerate(row):
            col_mapping = header_map[col_idx] if col_idx < len(header_map) else None
            if col_mapping is None:
                continue

            sec, field = col_mapping
            if isinstance(cell, str):
                val = cell.strip()
            elif cell is None:
                val = ""
            else:
                val = str(cell).strip()

            if val == "":
                # Treat blanks as missing (do not insert the key)
                continue

            sections[sec][field] = val

        R = sections["R"]
        X = sections["X"]
        Y = sections["Y"]
        P = sections["P"]

        book = str(R.get("book", "")).strip()
        chapter_raw = str(R.get("chapter", "")).strip()

        # Inclusion rule: must have a usable reference AND at least some content on X/Y/P.
        has_ref = bool(book) and bool(chapter_raw)
        has_content = bool(X or Y or P)

        if not (has_ref and has_content):
            skipped_rows += 1
            continue

        # Normalize chapter (int if possible, but keep raw for IDs).
        try:
            ch_int = int(chapter_raw)
        except (TypeError, ValueError):
            ch_int = None

        chapter_val: Any = ch_int if ch_int is not None else chapter_raw
        R["chapter"] = chapter_val

        # book_name from books_names (if provided)
        book_name: Optional[str] = None
        if book and books_names:
            # books.json is assumed to use upper-case codes as keys
            book_upper = book.upper()
            if book_upper in books_names:
                book_name = books_names[book_upper]

        if book_name and "book_name" not in R:
            R["book_name"] = book_name

        # pv (pair verse / index)
        pv = str(R.get("pv", "")).strip()

        # ref_id: "book.chapter[.pv]"
        if book and chapter_raw:
            base_ref_id = f"{book}.{chapter_raw}"
            ref_id = f"{base_ref_id}.{pv}" if pv else base_ref_id
        else:
            ref_id = ""

        if ref_id and "ref_id" not in R:
            R["ref_id"] = ref_id

        # ref_str: "BookName chapter[:pv]" if we have a name
        if book_name and chapter_raw:
            ref_str = f"{book_name} {chapter_raw}"
            if pv:
                ref_str += f":{pv}"
            if "ref_str" not in R:
                R["ref_str"] = ref_str

        # Stats
        if book:
            book_set.add(book)
        if book and chapter_raw:
            chapter_set.add(f"{book}.{chapter_raw}")

        # pair_id: use ref_id if available, else row-based fallback.
        base_id = ref_id if ref_id else f"row{idx}"
        id_counter[base_id] += 1
        count = id_counter[base_id]
        pair_id = base_id if count == 1 else f"{base_id}.{count}"

        pair_obj: Dict[str, Any] = {
            "pair_id": pair_id,
            "S": sections["S"],
            "R": R,
            "P": P,
            "X": X,
            "Y": Y,
            "T": sections["T"],
        }
        pairs.append(pair_obj)

    stats = {
        "pairs_total": len(pairs),
        "books": sorted(book_set),
        "chapters": sorted(chapter_set),
        "skipped_rows": skipped_rows,
    }
    return pairs, stats


def build_input_pairs(
    csv_path: Path,
    out_path: Path,
    books_json_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    High-level entry: CSV → input_pairs.json object (also written to disk).
    """
    rows = _read_csv_rows(csv_path)
    if not rows:
        raise SystemExit(f"CSV appears to be empty: {csv_path}")

    # First, assume row 0 is the header.
    header_row = rows[0]
    mapping = _build_header_mapping(header_row)

    def _schema_has_fields(m: HeaderMapping) -> bool:
        return any(m.schema[sec] for sec in m.schema)

    # If we didn't recognize any fields at all, try treating row 1 as header instead.
    rows_for_parse = rows
    if not _schema_has_fields(mapping) and len(rows) > 1:
        alt_header_row = rows[1]
        alt_mapping = _build_header_mapping(alt_header_row)
        if _schema_has_fields(alt_mapping):
            mapping = alt_mapping
            rows_for_parse = rows[1:]  # drop row 0, use row 1 as header

    # Load book names, if available.
    books_names: Optional[Dict[str, str]] = None
    if books_json_path and books_json_path.exists():
        with books_json_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        # Expecting a mapping of code → name under a "names" key
        names_field = data.get("names")
        if isinstance(names_field, dict):
            books_names = names_field

    pairs, stats = _parse_pairs(rows_for_parse, mapping, books_names)

    meta = {
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "source": {
            "file": str(csv_path),
            "sheet": "pairs",
            "version": "v1",
        },
        "schema": mapping.schema,
        "stats": stats,
    }

    out_obj: Dict[str, Any] = {
        "meta": meta,
        "pairs": pairs,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(out_obj, f, ensure_ascii=False, indent=2)

    return out_obj


def _default_paths() -> Tuple[Path, Path, Optional[Path]]:
    """
    Provide reasonable default paths when running from the repo root.

    - Input CSV:  tools/pps/data/input/pairs.csv
    - Output JSON: tools/pps/data/input/input_pairs.json
    """
    base = Path(".").resolve()
    csv_default = base / "tools" / "pps" / "data" / "input" / "pairs.csv"
    out_default = base / "tools" / "pps" / "data" / "input" / "input_pairs.json"

    # books.json is at docs/data/v1/lit/bible/books.json per your layout.
    candidates = [
        base / "docs" / "data" / "v1" / "lit" / "bible" / "books.json",
    ]
    books_default: Optional[Path] = None
    for cand in candidates:
        if cand.exists():
            books_default = cand
            break

    return csv_default, out_default, books_default


def main() -> None:
    csv_default, out_default, books_default = _default_paths()

    parser = argparse.ArgumentParser(
        description="Build PPS v1 input_pairs.json from pairs.csv"
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=csv_default,
        help=f"Path to pairs.csv (default: {csv_default})",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=out_default,
        help=f"Path for input_pairs.json (default: {out_default})",
    )
    parser.add_argument(
        "--books-json",
        type=Path,
        default=books_default,
        help=(
            "Path to books.json (for book_name lookup). "
            f"Default will be auto-detected (current: {books_default})"
        ),
    )

    args = parser.parse_args()

    result = build_input_pairs(
        csv_path=args.csv,
        out_path=args.out,
        books_json_path=args.books_json,
    )

    # Light CLI feedback
    stats = result["meta"]["stats"]
    print(f"Built {args.out}")
    print(
        f"Pairs: {stats['pairs_total']} (skipped rows: {stats['skipped_rows']}) | "
        f"Books: {len(stats['books'])}, Chapters: {len(stats['chapters'])}"
    )


if __name__ == "__main__":
    main()
