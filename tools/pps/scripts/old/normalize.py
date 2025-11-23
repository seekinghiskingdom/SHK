# tools/pps/scripts/normalize.py
from __future__ import annotations
import re
import unicodedata
from typing import List, Dict

# --- Canonical book codes (expand later as you add books) ---
_BOOK_ALIASES: Dict[str, str] = {
    # Proverbs
    "proverbs": "PRO",
    "prov": "PRO",
    "pro": "PRO",
    "pro  ": "PRO",   # sloppy inputs get trimmed anyway
    "proverb": "PRO",
    "pro  v": "PRO",
    "pro  verbs": "PRO",
    "pro.": "PRO",
    "pro  v.": "PRO",
    # Already-coded
    "pro*": "PRO",    # if you pass "PRO" we'll accept it below
}

def canon_book(book: str) -> str:
    """
    Return 3-letter canonical code (e.g., 'PRO' for Proverbs).
    Accepts 'Prov', 'Proverbs', 'PRO', etc.
    """
    if not book:
        raise ValueError("Empty book string.")
    s = " ".join(book.strip().split()).lower()
    if s == "pro":   # fast-path common case
        return "PRO"
    if s in _BOOK_ALIASES:
        return _BOOK_ALIASES[s]
    # If already a 3-letter uppercase code like 'PRO', accept it
    if len(book) == 3 and book.isalpha() and book.upper() == book:
        return book
    # Minimal fuzzy: strip punctuation and try again
    s2 = re.sub(r"[^a-z]", "", s)
    if s2 in _BOOK_ALIASES:
        return _BOOK_ALIASES[s2]
    raise ValueError(f"Unknown book name/code: {book!r}")

# --- Ref parsing ---

_REF_RE = re.compile(r"""
    ^\s*
    (?P<ch>\d+)
    \s*:\s*
    (?P<start>\d+)
    (?:\s*-\s*(?P<end>\d+))?
    \s*$
""", re.VERBOSE)

def parse_ref(book: str, ref: str) -> Dict[str, int | str]:
    """
    Parse Ref like '21:11' or '1:1-4' together with Book.
    Returns: {'book': 'PRO', 'ch': 21, 'start': 11, 'end': 11}
    """
    book_code = canon_book(book)
    m = _REF_RE.match(ref or "")
    if not m:
        raise ValueError(f"Bad Ref format: {ref!r}")
    ch = int(m.group("ch"))
    start = int(m.group("start"))
    end = int(m.group("end") or start)
    if end < start:
        raise ValueError(f"Ref end < start: {ref!r}")
    return {"book": book_code, "ch": ch, "start": start, "end": end}

# --- PV parsing ---

def parse_pv(pv: str) -> List[int]:
    """
    Accepts '11' | '1-2' | '1;2;3' | '1; 3-5'.
    Returns sorted unique list of ints.
    """
    if pv is None or str(pv).strip() == "":
        raise ValueError("PV is required for each pair row.")
    tokens = re.split(r"[;]+", str(pv))
    out: set[int] = set()
    for t in tokens:
        t = t.strip()
        if not t:
            continue
        if "-" in t:
            a, b = [x.strip() for x in t.split("-", 1)]
            a_i, b_i = int(a), int(b)
            if b_i < a_i:
                a_i, b_i = b_i, a_i
            out.update(range(a_i, b_i + 1))
        else:
            out.add(int(t))
    return sorted(out)

# --- Slug and key normalization ---

_SLUG_RE = re.compile(r"[^a-z0-9]+")

def slug(s: str) -> str:
    """
    Slug for IDs: lowercase, alnum, dashes for gaps, no leading/trailing dash.
    """
    s = (s or "").lower().strip()
    s = _SLUG_RE.sub("-", s)
    return s.strip("-")

def norm_key(s: str) -> str:
    """
    Normalize a search key for indexing/lookup:
    - casefold
    - collapse whitespace
    - strip leading/trailing spaces
    """
    s = unicodedata.normalize("NFKC", s or "").casefold()
    s = " ".join(s.split())
    return s

# --- Splitters for synonyms/roots ---

def split_synonyms(s: str | None) -> List[str]:
    """
    Split semicolon-separated synonyms. Empty/None -> [].
    Trims each token and drops empties.
    """
    if not s:
        return []
    return [t.strip() for t in s.split(";") if t.strip()]

def split_roots(s: str | None) -> List[str]:
    """
    Split pipe-separated root phrases for highlighting.
    Empty/None -> [].
    """
    if not s:
        return []
    return [t.strip() for t in s.split("|") if t.strip()]

# --- Text normalization for root matching ---

_WS_RE = re.compile(r"\s+")

def norm_text_for_match(s: str) -> str:
    """
    Normalize verse text and roots before substring matching:
    - Unicode NFKC
    - casefold
    - collapse whitespace to a single space
    - strip leading/trailing spaces
    (Keep punctuation by default; only collapse spaces—safer for KJV punctuation.)
    """
    s = unicodedata.normalize("NFKC", s or "").casefold()
    s = _WS_RE.sub(" ", s)
    return s.strip()

# --- Quick self-test ---
if __name__ == "__main__":
    assert canon_book("Prov") == "PRO"
    assert canon_book("Proverbs") == "PRO"
    assert parse_ref("Prov", "21:11") == {"book": "PRO", "ch": 21, "start": 11, "end": 11}
    assert parse_ref("PRO", "1:1-4") == {"book": "PRO", "ch": 1, "start": 1, "end": 4}
    assert parse_pv("11") == [11]
    assert parse_pv("1-3") == [1,2,3]
    assert parse_pv("1;3-4;6") == [1,3,4,6]
    assert slug("Wise Man Is Instructed!") == "wise-man-is-instructed"
    assert norm_key("  Fear  of  the  LORD ") == "fear of the lord"
    assert split_synonyms("correction; punishment ; discipline") == ["correction","punishment","discipline"]
    assert split_roots("withhold not | thou beatest | thou shalt beatest") == ["withhold not","thou beatest","thou shalt beatest"]
    print("normalize.py self-test OK")
