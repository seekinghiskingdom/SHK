# tools/pps/scripts/validator.py
from __future__ import annotations
from typing import Dict, List, Tuple
from .schema import BookFile
from .normalize import norm_text_for_match

class ValidationError(Exception):
    """Hard failure (bad ref, PV outside span, missing chapter/verse, etc.)."""

def validate_ref(bible_by_book: Dict[str, BookFile], book_code: str, ch: int,
                 start: int, end: int) -> None:
    """
    Verify the book exists and the chapter/start..end verses exist.
    Raises ValidationError on structural problems.
    """
    if book_code not in bible_by_book:
        raise ValidationError(f"Unknown book code: {book_code}")
    book = bible_by_book[book_code]
    chapters = book["chapters"]
    if str(ch) not in chapters:
        raise ValidationError(f"Missing chapter {ch} in {book_code}")
    verses = chapters[str(ch)]
    for v in range(start, end + 1):
        if str(v) not in verses:
            raise ValidationError(f"Missing verse {ch}:{v} in {book_code}")

def validate_pv_subset(start: int, end: int, pv_list: List[int]) -> None:
    """
    Ensure every pv in pv_list is within [start, end].
    Raises ValidationError if out-of-range.
    """
    lo, hi = start, end
    for v in pv_list:
        if v < lo or v > hi:
            raise ValidationError(f"PV {v} outside entry span {lo}-{hi}")

def validate_roots(
    book_file: BookFile,
    ch: int,
    pv_list: List[int],
    roots: List[str],
    *,
    join_with_space: str = " "
) -> List[str]:
    """
    Soft-validate that each root substring appears in the joined PV text
    (case/space-insensitive). Returns a list of WARNINGS (strings).
    Does not raise unless the book_file is malformed.
    """
    warnings: List[str] = []
    # Join the PV verses in order
    verse_map = book_file["chapters"][str(ch)]
    texts: List[str] = []
    for v in pv_list:
        try:
            texts.append(verse_map[str(v)])
        except KeyError as e:
            # This is a structural issue—bubble up as a hard error.
            raise ValidationError(f"Missing verse {ch}:{v}") from e

    joined = norm_text_for_match(join_with_space.join(texts))
    for root in roots:
        if not root:
            continue
        norm_root = norm_text_for_match(root)
        if norm_root and norm_root not in joined:
            warnings.append(f"Root not found in PV text: {root!r}")
    return warnings
