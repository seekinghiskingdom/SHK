# tools/pps/scripts/loaders.py
from __future__ import annotations
import csv, json, os
from typing import List, Dict
from .schema import PairRow, BookFile, BibleByBook

# ---------- CSV loader ----------

_HEADER_MAP = {
    # CSV headers (with dots) -> PairRow keys (underscored)
    "Book": "Book",
    "Ref": "Ref",
    "PV": "PV",
    "Text": "Text",
    "X.key": "X_key",
    "X.keys": "X_keys",
    "X.root": "X_root",
    "Y.key": "Y_key",
    "Y.keys": "Y_keys",
    "Y.root": "Y_root",
    "Status": "Status",
    "Notes": "Notes",
}

def load_csv(path: str) -> List[PairRow]:
    """
    Load the authoring CSV (one row per pair). Maps dotted headers to schema keys.
    Skips rows that are missing required fields.
    """
    rows: List[PairRow] = []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        # remap headers once
        field_map = {h: _HEADER_MAP.get(h, h) for h in (reader.fieldnames or [])}

        for r in reader:
            out: PairRow = {}
            for k, v in r.items():
                if k is None:
                    continue
                key = field_map.get(k, k)
                if v is None:
                    continue
                v = v.strip()
                if v == "":
                    continue
                out[key] = v

            # ⬇️ REQUIRED FIELDS — skip empty/incomplete rows
            required = ("Book", "Ref", "PV", "X_key", "X_root", "Y_key", "Y_root")
            if not all(out.get(k) for k in required):
                continue

            rows.append(out)
    return rows


# ---------- Bible loader (per-translation, per-book files) ----------
# --- NEW: discover and bulk-load translations ---

import os

def discover_trans_ids(trans_root: str, exclude: list[str] | None = None) -> list[str]:
    """
    Return a sorted list of translation ids under trans_root that look valid
    (contain at least one 3-letter book JSON like PRO.json).
    """
    exclude_set = set(exclude or [])
    out = []
    for name in os.listdir(trans_root):
        p = os.path.join(trans_root, name)
        if not os.path.isdir(p) or name in exclude_set:
            continue
        # must have at least one 3-letter uppercase book json
        files = [f for f in os.listdir(p) if f.lower().endswith(".json")]
        if any((os.path.splitext(f)[0].isalpha() and len(os.path.splitext(f)[0]) == 3
                and os.path.splitext(f)[0].upper() == os.path.splitext(f)[0])
               for f in files):
            out.append(name)
    return sorted(out)

def load_bibles(trans_root: str, trans_ids: list[str]) -> dict[str, BibleByBook]:
    """
    Load multiple translations in one shot.
    Returns: { trans_id: { BOOKCODE: BookFile, ... }, ... }
    """
    return {tid: load_bible(trans_root, tid) for tid in trans_ids}


# tools/pps/scripts/loaders.py
def load_bible_dir(trans_dir: str) -> BibleByBook:
    by_book: BibleByBook = {}
    for name in os.listdir(trans_dir):
        if not name.lower().endswith(".json"):
            continue
        # accept only 3-letter book files like PRO.json, PSA.json, etc.
        stem = os.path.splitext(name)[0]
        if not (len(stem) == 3 and stem.isalpha() and stem.upper() == stem):
            continue  # skip bible_kjv.min.json and others
        path = os.path.join(trans_dir, name)
        with open(path, "r", encoding="utf-8") as f:
            j = json.load(f)
        # defensive: verify expected shape
        if not (isinstance(j, dict) and "book" in j and "chapters" in j):
            continue
        by_book[j["book"]] = j
    if not by_book:
        raise FileNotFoundError(f"No per-book files found in {trans_dir}")
    return by_book


def load_bible(trans_root: str, trans_id: str) -> BibleByBook:
    """
    Load a translation by id (e.g., 'kjv') from a root like:
      docs/data/v1/lit/bible/en/<trans_id>/
    or your local tools/ path during dev.
    """
    trans_dir = os.path.join(trans_root, trans_id)
    if not os.path.isdir(trans_dir):
        raise FileNotFoundError(f"Translation dir not found: {trans_dir}")
    return load_bible_dir(trans_dir)

# ---------- Tiny helpers used later ----------

def get_verse(book_file: BookFile, ch: int, v: int) -> str:
    """
    Safe accessor for a single verse; raises KeyError if missing.
    """
    return book_file["chapters"][str(ch)][str(v)]

def join_verses(book_file: BookFile, ch: int, verses: list[int]) -> str:
    """
    Concatenate verse texts (with a single space) in order for matching/highlighting.
    """
    parts = [book_file["chapters"][str(ch)][str(v)] for v in verses]
    return " ".join(parts)
