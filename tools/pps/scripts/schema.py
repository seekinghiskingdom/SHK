# scripts/schema.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional, TypedDict

# ---------- CSV row (authoring) ----------
class PairRow(TypedDict, total=False):
    # Authoring fields (v1)
    Book: str          # e.g., "Prov" or "Proverbs"
    Ref: str           # e.g., "21:11" or "1:1-4"
    PV: str            # e.g., "11" or "1-2" or "1;2"
    Text: str          # OPTIONAL (dev only) inline passage text
    X_key: str         # primary concept (antecedent)
    X_keys: str        # OPTIONAL semicolon-separated synonyms (ignored in v1 if configured)
    X_root: str        # exact phrase(s); multiple with pipe: "a | b | c"
    Y_key: str         # primary concept (consequent)
    Y_keys: str        # OPTIONAL semicolon-separated synonyms (ignored in v1 if configured)
    Y_root: str        # exact phrase(s); multiple with pipe
    Status: Literal["active", "deprecated"]  # default "active"
    Notes: str

# ---------- Bible data ----------
# Expected per-translation file shape:
# { "book": "PRO", "chapters": { "21": { "11": "When the scorner...", ... }, ... } }
VerseMap = Dict[str, str]          # "11" -> "verse text"
ChapterMap = Dict[str, VerseMap]   # "21" -> { "11": "...", ... }

class BookFile(TypedDict):
    book: str                       # 3-letter code, e.g., "PRO"
    chapters: ChapterMap

BibleByBook = Dict[str, BookFile]   # "PRO" -> BookFile

# ---------- Final bundle (output) ----------
@dataclass(slots=True)
class XSide:
    key: str                        # primary concept (used for IDs)
    keys: List[str]                 # primary + synonyms (v1 may contain only [key])
    root: str                       # first highlight phrase
    roots: List[str] = field(default_factory=list)  # all highlight phrases (>=1)

@dataclass(slots=True)
class YSide:
    key: str
    keys: List[str]
    root: str
    roots: List[str] = field(default_factory=list)

@dataclass(slots=True)
class Pair:
    pairId: str                     # stable content-derived id
    pv: List[int]                   # verses used by this pair within the entry
    x: XSide
    y: YSide
    status: Literal["active", "deprecated"] = "active"

@dataclass(slots=True)
class Entry:
    entryId: str                    # stable from book/chapter/start/end
    ref: str                        # e.g., "Prov 21:11" or "Prov 1:1-4"
    osis: Optional[str]             # e.g., "Prov.21.11" or "Prov.1.1-Prov.1.4"
    chapter: int
    verses: List[int]               # full span for this entry
    text: Dict[str, str]            # { "kjv": "...", ... } (v1 may include only default)
    pairs: List[Pair]               # pairs for this entry
    notes: str = ""                 # optional freeform

@dataclass(slots=True)
class Stats:
    entryCount: int
    pairCount: int
    pairCountActive: int

@dataclass(slots=True)
class Bundle:
    schemaVersion: int
    bundleVersion: str
    builtAt: str                    # ISO8601
    defaultTrans: str               # e.g., "kjv"
    transMeta: Dict[str, Dict[str, str]]  # minimal metadata per translation
    stats: Stats
    entries: List[Entry]
    index: Dict[str, Dict[str, List[str]]]  # {"x": {...}, "y": {...}}

__all__ = [
    "PairRow",
    "VerseMap", "ChapterMap", "BookFile", "BibleByBook",
    "XSide", "YSide", "Pair", "Entry", "Stats", "Bundle",
]
