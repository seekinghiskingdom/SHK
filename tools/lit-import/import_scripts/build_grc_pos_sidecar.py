#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import unicodedata
import collections
from pathlib import Path
import xml.etree.ElementTree as ET


# ---------- Inputs (raw) ----------
RAW_DIR = Path("tools/lit-import/data/raw/strongs/grc")
GRC_XML = RAW_DIR / "strongsgreek.xml"  # adjust if your filename differs

# ---------- Outputs (v1) ----------
OUT_DIR = Path("docs/data/v1/lit/strongs/grc/pos")
OUT_POS_JSONL = OUT_DIR / "pos.jsonl"
OUT_CATALOG = OUT_DIR / "catalog.json"
OUT_REPORT = OUT_DIR / "_build_report.json"


POS_CATALOG = {
    "verb": "Verb",
    "noun": "Noun (incl. many defaulted)",
    "proper_noun": "Proper Noun",
    "adverb": "Adverb",
    "adjective": "Adjective",
    "pronoun": "Pronoun",
    "preposition": "Preposition",
    "conjunction": "Conjunction",
    "particle": "Particle",
    "interjection": "Interjection",
    "article": "Article",
    "numeral": "Numeral",
    "unknown": "Unknown"
}

# Text-based signals (Strong's-style phrasing is inconsistent in this XML; still useful when present)
TEXT_RULES = [
    ("proper_noun", re.compile(r"\bproper\s+noun\b", re.I)),
    ("preposition", re.compile(r"\bpreposition\b", re.I)),
    ("conjunction", re.compile(r"\bconjunction\b", re.I)),
    ("particle", re.compile(r"\bparticle\b", re.I)),
    ("interjection", re.compile(r"\binterjection\b", re.I)),
    ("pronoun", re.compile(r"\bpronoun\b", re.I)),
    ("article", re.compile(r"\barticle\b", re.I)),
    ("adverb", re.compile(r"\badverb\b", re.I)),
    ("adjective", re.compile(r"\badjective\b|\badj\.\b", re.I)),
    ("verb", re.compile(r"\bverb\b", re.I)),
    ("noun", re.compile(r"\bnoun\b", re.I)),
    ("numeral", re.compile(r"\bnumeral\b|\bnumber\b", re.I)),
]


def strip_diacritics(s: str) -> str:
    return "".join(
        ch for ch in unicodedata.normalize("NFD", s)
        if unicodedata.category(ch) != "Mn"
    )


def norm_g_id(raw_id: str) -> str:
    raw_id = (raw_id or "").strip()
    if not raw_id:
        return raw_id
    # entry attribute is often "00001"; sometimes inner <strongs> is "1"
    if raw_id.startswith("G") and raw_id[1:].isdigit():
        return "G" + raw_id[1:].zfill(4)
    if raw_id.isdigit():
        return "G" + raw_id.zfill(4)
    return raw_id


def get_text(entry: ET.Element, tag: str) -> str:
    el = entry.find(tag)
    if el is None:
        return ""
    return " ".join("".join(el.itertext()).split()).strip()


def lemma_unicode(entry: ET.Element) -> str:
    # In this XML, the lemma is the first <greek .../> child inside <entry>
    g = entry.find("greek")
    return (g.get("unicode", "") or "").strip() if g is not None else ""


def infer_pos(entry: ET.Element) -> tuple[str, str, float]:
    """
    Returns (pos, method, confidence).
    Goal: high coverage with transparent confidence/method for later refinement.
    """
    sdef = get_text(entry, "strongs_def")
    deriv = get_text(entry, "strongs_derivation")
    kjv = get_text(entry, "kjv_def")
    text = " ".join(x for x in [sdef, deriv, kjv] if x).strip()

    # 1) Text rules (when present)
    if text:
        for pos, pat in TEXT_RULES:
            if pat.search(text):
                return pos, "text_rule", 0.95

    # 2) Lemma form rules (very effective for verbs/adverbs)
    uni = lemma_unicode(entry)
    if uni:
        u = strip_diacritics(uni)

        # adverbs: -ως (covers many; accent-stripped)
        if u.endswith("ως"):
            return "adverb", "lemma_suffix", 0.95

        # verbs: -ω / -μαι / -ομαι / -μι
        if u.endswith("ω") or u.endswith("μαι") or u.endswith("ομαι") or u.endswith("μι"):
            return "verb", "lemma_suffix", 0.98

        # proper noun heuristic: lemma starts uppercase and definition starts uppercase (names/places)
        if u[:1].isupper() and sdef and re.match(r"^[A-ZΑ-Ω]", sdef):
            return "proper_noun", "caps_heuristic", 0.75

    # 3) Default (coarse)
    return "unknown", "default", 0.55


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_CATALOG.write_text(json.dumps(POS_CATALOG, ensure_ascii=False, indent=2), encoding="utf-8")

    root = ET.parse(GRC_XML).getroot()
    entries = root.findall(".//entry")

    pos_counts = collections.Counter()
    method_counts = collections.Counter()
    low_conf = 0

    with OUT_POS_JSONL.open("w", encoding="utf-8") as f:
        for entry in entries:
            raw_id = entry.get("strongs") or entry.findtext("strongs") or ""
            sid = norm_g_id(raw_id)
            if not sid:
                continue

            pos, method, conf = infer_pos(entry)
            pos_counts[pos] += 1
            method_counts[method] += 1
            if conf < 0.8:
                low_conf += 1

            out = {
                "id": sid,
                "pos": pos,
                "pos_label": POS_CATALOG.get(pos),
                "method": method,
                "confidence": conf
            }
            f.write(json.dumps(out, ensure_ascii=False) + "\n")

    report = {
        "source_file": str(GRC_XML).replace("\\", "/"),
        "entries_total": len(entries),
        "pos_counts": dict(pos_counts),
        "method_counts": dict(method_counts),
        "low_confidence_count": low_conf,
        "outputs": {
            "pos_jsonl": str(OUT_POS_JSONL).replace("\\", "/"),
            "catalog_json": str(OUT_CATALOG).replace("\\", "/"),
            "report_json": str(OUT_REPORT).replace("\\", "/")
        }
    }
    OUT_REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
