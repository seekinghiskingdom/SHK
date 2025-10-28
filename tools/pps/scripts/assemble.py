# tools/pps/scripts/assemble.py
from __future__ import annotations
from typing import Dict, List, Tuple, DefaultDict
from collections import defaultdict

from .schema import PairRow, Entry, Pair, XSide, YSide, BookFile
from .normalize import (
    canon_book, parse_ref, parse_pv,
    split_roots, split_synonyms, norm_key,
)
from .id_utils import entry_id, ref_string, osis_string, make_pair_id, ensure_unique
from .validator import validate_ref, validate_pv_subset, validate_roots, ValidationError

# Optional config flags (can also pass as args to functions if you prefer)
try:
    from . import config
    SYNONYMS_MODE = getattr(config, "SYNONYMS_MODE", "ignore")
    DEFAULT_TRANS = getattr(config, "DEFAULT_TRANS", "kjv")   # string as-is
except Exception:
    SYNONYMS_MODE = "ignore"
    DEFAULT_TRANS = "kjv"

IGNORE_SYNONYMS = (SYNONYMS_MODE == "ignore")


# ---------- Grouping ----------

def _ref_key(row: PairRow) -> Tuple[str, int, int, int]:
    """
    Group key for rows: (BOOKCODE, ch, start, end)
    Uses Book + Ref columns.
    """
    ref_parts = parse_ref(canon_book(row["Book"]), row["Ref"])
    return (ref_parts["book"], ref_parts["ch"], ref_parts["start"], ref_parts["end"])  # type: ignore[return-value]


def group_rows_by_ref(rows: List[PairRow]) -> Dict[Tuple[str, int, int, int], List[PairRow]]:
    groups: DefaultDict[Tuple[str, int, int, int], List[PairRow]] = defaultdict(list)
    for r in rows:
        groups[_ref_key(r)].append(r)
    return dict(groups)


# ---------- Bible slicing (default translation only for v1) ----------
# def slice_bible_text(
#     bible_by_book: Dict[str, BookFile] | None,
#     book_code: str,
#     ch: int,
#     start: int,
#     end: int,
#     # inline_text_fallback: str | None = None,
# ) -> Dict[str, str]:
#     """
#     Returns { DEFAULT_TRANS: joined_text }.
#     If bible_by_book is None or missing, and ALLOW_INLINE_TEXT is True,
#     uses inline_text_fallback (first non-empty Text in the group).
#     """

#     book = bible_by_book[book_code]
#     verses = book["chapters"][str(ch)]
#     parts = [verses[str(v)] for v in range(start, end + 1)]
#     return {DEFAULT_TRANS: " ".join(parts)}


# ---------- Pair builders ----------

def _build_side(
    primary_key: str,
    roots_cell: str | None,
    synonyms_cell: str | None,
) -> Tuple[str, List[str], str, List[str]]:
    """
    Returns (key, keys_list, root, roots_list)
    """
    key = primary_key
    syns = [] if IGNORE_SYNONYMS else split_synonyms(synonyms_cell)
    keys_list = [key] if not syns else [key] + [s for s in syns if s.lower() != key.lower()]
    roots_list = split_roots(roots_cell)
    root = roots_list[0] if roots_list else ""
    return key, keys_list if keys_list else [key], root, roots_list if roots_list else ([root] if root else [])


def build_entry(
    ref_tuple: Tuple[str, int, int, int],
    rows_for_ref: List[PairRow],
    # bible_by_book: Dict[str, BookFile] | None = None,
    bibles_by_trans: dict[str, Dict[str, BookFile]], 
    default_trans: str
) -> Entry:
    """
    Build a single Entry from grouped rows (same Book/Ref).
    - Validates refs/PV subset.
    - Soft-validates roots against the PV slice (if VALIDATE_ROOTS and bible available).
    - Creates stable pairIds (content-derived).
    """
    book_code, ch, start, end = ref_tuple
    ref_parts = {"book": book_code, "ch": ch, "start": start, "end": end}

    # Hard validation if Bible present
    # if bible_by_book:
    #     validate_ref(bible_by_book, book_code, ch, start, end)
    default_bible = bibles_by_trans[default_trans]     # single-trans view
    validate_ref(default_bible, book_code, ch, start, end)

    # # Inline text fallback (first non-empty Text cell)
    # inline_text = next((r.get("Text") for r in rows_for_ref if r.get("Text")), None)

    # Build pairs
    pairs: List[Pair] = []
    seen_ids: set[str] = set()
    warnings: List[str] = []

    for row in rows_for_ref:
        pv_list = parse_pv(row["PV"])
        validate_pv_subset(start, end, pv_list)

        # Build sides
        x_key, x_keys, x_root, x_roots = _build_side(row["X_key"], row.get("X_root"), row.get("X_keys"))
        y_key, y_keys, y_root, y_roots = _build_side(row["Y_key"], row.get("Y_root"), row.get("Y_keys"))


        book_file = default_bible[book_code]
        warnings_x = validate_roots(book_file, ch, pv_list, x_roots or ([x_root] if x_root else []))
        warnings_y = validate_roots(book_file, ch, pv_list, y_roots or ([y_root] if y_root else []))
        # you can log or collect warnings_x + warnings_y if you want; they’re soft warnings
        if warnings_x or warnings_y:
            print(f"[root-warn] {book_code} {ch}:{start}-{end} pv={pv_list} X={x_roots or [x_root]}={warnings_x} Y={y_roots or [y_root]}={warnings_y}")


        # Stable pairId (content hash uses PV + roots — NOT synonyms)
        pid = make_pair_id(ref_parts, pv_list, x_key, y_key, x_roots or [x_root], y_roots or [y_root])
        pid = ensure_unique(pid, seen_ids)
        seen_ids.add(pid)

        pairs.append(
            Pair(
                pairId=pid,
                pv=pv_list,
                x=XSide(key=x_key, keys=x_keys, root=x_root, roots=x_roots or ([x_root] if x_root else [])),
                y=YSide(key=y_key, keys=y_keys, root=y_root, roots=y_roots or ([y_root] if y_root else [])),
                status=row.get("Status", "active"),  # type: ignore[arg-type]
            )
        )

    # Entry texts (all loaded translations)
    texts: Dict[str, str] = {}
    for tid, bible_by_book in bibles_by_trans.items():
        verses_map = bible_by_book[book_code]["chapters"][str(ch)]
        parts = [verses_map[str(v)] for v in range(start, end + 1)]
        texts[tid] = " ".join(parts)

    entry = Entry(
        entryId=entry_id(ref_parts),
        ref=ref_string(ref_parts),
        osis=osis_string(ref_parts),
        chapter=ch,
        verses=list(range(start, end + 1)),
        text=texts,
        pairs=pairs,
        notes="",
    )
    # You could log warnings here; for v1 just return. Caller can collect.
    return entry


def build_entries(
    rows: List[PairRow],
    # bible_by_book: Dict[str, BookFile] | None = None,
    bibles_by_trans: dict[str, Dict[str, BookFile]],
    default_trans: str,
) -> List[Entry]:
    """
    Group rows by (Book,Ref) and build all Entry objects.
    Keeps input order by sorting groups by (book_code, ch, start, end).
    """
    groups = group_rows_by_ref(rows)
    out: List[Entry] = []
    # for key in sorted(groups.keys(), key=lambda t: (t[0], t[1], t[2], t[3])):
    #     out.append(build_entry(key, groups[key], bible_by_book=bible_by_book))
    for key in sorted(groups.keys(), key=lambda t: (t[0], t[1], t[2], t[3])):
        out.append(
            build_entry(
                key,
                groups[key],
                bibles_by_trans=bibles_by_trans,
                default_trans=default_trans,
            )
        )

    return out
