#!/usr/bin/env python3
from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional


# ----------------- repo root helper -----------------

def find_repo_root() -> Path:
    # tools/lit-import/strongs_import.py -> repo root
    here = Path(__file__).resolve()
    return here.parents[2]


# ----------------- shared data structures -----------------

@dataclass
class StrongLexEntry:
    id: str           # e.g. "G0001" or "H0001"
    n: int            # e.g. 1
    lemma_unicode: str
    lemma_translit: str
    lemma_beta: str
    pronunciation: str
    derivation: str   # etymology / source
    definition: str   # main gloss / sense
    kjv_def: str      # KJV-style gloss list
    refs_raw: List[str] = field(default_factory=list)

    def to_json(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "n": self.n,
            "lemma_unicode": self.lemma_unicode,
            "lemma_translit": self.lemma_translit,
            "lemma_beta": self.lemma_beta,
            "pronunciation": self.pronunciation,
            "derivation": self.derivation,
            "definition": self.definition,
            "kjv_def": self.kjv_def,
            "refs_raw": self.refs_raw,
        }


# ----------------- shared helpers -----------------

def _normalize_strongs_code(raw: Optional[str], prefix: str) -> tuple[str, int]:
    """
    Turn things like '00011' or 'H1' into ('G0011', 11) / ('H0001', 1).
    """
    s = (raw or "").strip()
    digits = "".join(ch for ch in s if ch.isdigit())
    n = int(digits or "0")
    return f"{prefix}{n:04d}", n


def _collapse(s: Optional[str]) -> str:
    if not s:
        return ""
    return " ".join(s.split())


# =====================================================================
#  GREEK: strongsgreek.xml
# =====================================================================

def _find_strongs_greek_xml(repo_root: Path) -> Path:
    # You put strongsgreek.xml in data/raw/strongs/grc/
    cand = (
        repo_root
        / "tools"
        / "lit-import"
        / "data"
        / "raw"
        / "strongs"
        / "grc"
        / "strongsgreek.xml"
    )
    if not cand.exists():
        raise FileNotFoundError(f"Expected Greek Strong's at {cand}")
    return cand


def parse_strongs_greek(xml_path: Path) -> List[StrongLexEntry]:
    tree = ET.parse(xml_path)
    root = tree.getroot()  # <strongsdictionary>
    entries = root.find("entries")
    if entries is None:
        raise ValueError(f"No <entries> in {xml_path}")

    out: List[StrongLexEntry] = []

    for e in entries.findall("entry"):
        strongs_attr = e.attrib.get("strongs", "")
        code, n = _normalize_strongs_code(strongs_attr, "G")

        g_elem = e.find("greek")
        lemma_unicode = g_elem.attrib.get("unicode", "") if g_elem is not None else ""
        lemma_beta = g_elem.attrib.get("BETA", "") if g_elem is not None else ""
        lemma_translit = g_elem.attrib.get("translit", "") if g_elem is not None else ""

        pronunciation = _collapse((e.findtext("pronunciation") or ""))
        derivation = _collapse((e.findtext("strongs_derivation") or ""))
        definition = _collapse((e.findtext("strongs_def") or ""))
        kjv_def = _collapse((e.findtext("kjv_def") or ""))

        refs_raw: List[str] = []
        for r in e.findall("strongsref"):
            if r.text and r.text.strip():
                refs_raw.append(_collapse(r.text))

        out.append(
            StrongLexEntry(
                id=code,
                n=n,
                lemma_unicode=lemma_unicode,
                lemma_translit=lemma_translit,
                lemma_beta=lemma_beta,
                pronunciation=pronunciation,
                derivation=derivation,
                definition=definition,
                kjv_def=kjv_def,
                refs_raw=refs_raw,
            )
        )

    return out


def import_strongs_greek(force: bool = False) -> None:
    repo_root = find_repo_root()
    xml_path = _find_strongs_greek_xml(repo_root)

    out_dir = repo_root / "docs" / "data" / "v1" / "lit" / "strongs" / "grc"
    out_dir.mkdir(parents=True, exist_ok=True)

    lexicon_path = out_dir / "lexicon.jsonl"
    meta_path = out_dir / "meta.json"

    if not force and lexicon_path.exists():
        raise FileExistsError(f"{lexicon_path} already exists (use --force to overwrite)")

    entries = parse_strongs_greek(xml_path)

    with lexicon_path.open("w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry.to_json(), ensure_ascii=False) + "\n")

    meta = {
        "id": "lexicon.strongs.grc",
        "language": "grc",
        "kind": "lexicon",
        "source": {
            "file": str(xml_path.relative_to(repo_root)),
            "format": "xml-strongs-greek",
            "license_note": "Strong's text public domain; XML encoding per upstream source.",
        },
        "counts": {
            "entries": len(entries),
        },
    }
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"[GRC] Wrote {len(entries)} entries to {lexicon_path}")
    print(f"[GRC] Wrote meta to {meta_path}")


# =====================================================================
#  HEBREW: HebrewStrong.xml (Open Scriptures)
# =====================================================================

_HE_NS = {"m": "http://openscriptures.github.com/morphhb/namespace"}


def _find_strongs_hebrew_xml(repo_root: Path) -> Path:
    # You placed HebrewStrong.xml here:
    # tools/lit-import/data/raw/strongs/he/HebrewStrong.xml
    cand = (
        repo_root
        / "tools"
        / "lit-import"
        / "data"
        / "raw"
        / "strongs"
        / "he"
        / "HebrewStrong.xml"
    )
    if not cand.exists():
        raise FileNotFoundError(f"Expected Hebrew Strong's at {cand}")
    return cand


def parse_strongs_hebrew(xml_path: Path) -> List[StrongLexEntry]:
    tree = ET.parse(xml_path)
    root = tree.getroot()  # <lexicon> with namespace

    entries = root.findall("m:entry", _HE_NS)
    if not entries:
        raise ValueError(f"No <entry> elements found in {xml_path}")

    out: List[StrongLexEntry] = []

    for e in entries:
        id_attr = e.attrib.get("id", "")  # e.g. "H1"
        # strip the H, keep digits
        code, n = _normalize_strongs_code(id_attr, "H")

        w = e.find("m:w", _HE_NS)
        lemma_unicode = (w.text or "").strip() if w is not None else ""
        lemma_translit = w.attrib.get("xlit", "") if w is not None else ""
        lemma_beta = ""  # not provided in this source
        pronunciation = w.attrib.get("pron", "") if w is not None else ""

        source_text = _collapse(e.findtext("m:source", default="", namespaces=_HE_NS))
        meaning_text = _collapse(e.findtext("m:meaning", default="", namespaces=_HE_NS))
        usage_text = _collapse(e.findtext("m:usage", default="", namespaces=_HE_NS))

        # Map to the same slots we used for Greek:
        derivation = source_text  # "a primitive root", "from ...", etc.
        # If meaning is empty, fall back to usage as the 'definition'
        definition = meaning_text or usage_text
        kjv_def = usage_text

        refs_raw: List[str] = []  # OS HebrewStrong.xml doesn't carry explicit Strong's refs

        out.append(
            StrongLexEntry(
                id=code,
                n=n,
                lemma_unicode=lemma_unicode,
                lemma_translit=lemma_translit,
                lemma_beta=lemma_beta,
                pronunciation=pronunciation,
                derivation=derivation,
                definition=definition,
                kjv_def=kjv_def,
                refs_raw=refs_raw,
            )
        )

    return out


def import_strongs_hebrew(force: bool = False) -> None:
    repo_root = find_repo_root()
    xml_path = _find_strongs_hebrew_xml(repo_root)

    out_dir = repo_root / "docs" / "data" / "v1" / "lit" / "strongs" / "he"
    out_dir.mkdir(parents=True, exist_ok=True)

    lexicon_path = out_dir / "lexicon.jsonl"
    meta_path = out_dir / "meta.json"

    if not force and lexicon_path.exists():
        raise FileExistsError(f"{lexicon_path} already exists (use --force to overwrite)")

    entries = parse_strongs_hebrew(xml_path)

    with lexicon_path.open("w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry.to_json(), ensure_ascii=False) + "\n")

    meta = {
        "id": "lexicon.strongs.he",
        "language": "he",
        "kind": "lexicon",
        "source": {
            "file": str(xml_path.relative_to(repo_root)),
            "format": "xml-strongs-hebrew",
            "license_note": "Underlying Strong's text public domain; XML per Open Scriptures Hebrew Lexicon (CC BY 4.0).",
        },
        "counts": {
            "entries": len(entries),
        },
    }
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"[HE] Wrote {len(entries)} entries to {lexicon_path}")
    print(f"[HE] Wrote meta to {meta_path}")


# =====================================================================
#  CLI
# =====================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Import Strong's Greek and Hebrew lexicons into JSONL."
    )
    parser.add_argument(
        "--lang",
        choices=["grc", "he", "both"],
        default="both",
        help="Which lexicon(s) to import (default: both).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing outputs.",
    )
    args = parser.parse_args()

    if args.lang in ("grc", "both"):
        import_strongs_greek(force=args.force)
    if args.lang in ("he", "both"):
        import_strongs_hebrew(force=args.force)
