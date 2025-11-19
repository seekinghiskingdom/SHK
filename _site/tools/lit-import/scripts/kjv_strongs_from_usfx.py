from pathlib import Path
from xml.etree import ElementTree as ET
import json, re

# --- Paths (edit if needed) ---
REPO_ROOT = Path(r"C:\Users\hrbncv\SHK\SHK").resolve()
USFX_DIR  = REPO_ROOT / "tools/lit-import/data/raw/kjv/eng-kjv_usfx"
OUT_DIR   = REPO_ROOT / "docs/data/v1/lit/bible/en/kjv_strongs"
# -------------------------------

OUT_DIR.mkdir(parents=True, exist_ok=True)

# GEN/EXO/..., already correct in your USFX's bcv values
VALID_BOOK_CODES = {
    "GEN","EXO","LEV","NUM","DEU","JOS","JDG","RUT","1SA","2SA","1KI","2KI",
    "1CH","2CH","EZR","NEH","EST","JOB","PSA","PRO","ECC","SNG","ISA","JER",
    "LAM","EZK","DAN","HOS","JOL","AMO","OBA","JON","MIC","NAM","HAB","ZEP",
    "HAG","ZEC","MAL","MAT","MRK","LUK","JHN","ACT","ROM","1CO","2CO","GAL",
    "EPH","PHP","COL","1TH","2TH","1TI","2TI","TIT","PHM","HEB","JAS","1PE",
    "2PE","1JN","2JN","3JN","JUD","REV"
}

def strip_ns(tag: str) -> str:
    return tag.split("}", 1)[-1]

def parse_bcv(bcv: str):
    """Parse 'GEN.1.1' → ('GEN', 1, 1) with sanity checks."""
    if not bcv:
        return None
    parts = bcv.strip().split(".")
    if len(parts) != 3:
        return None
    b, c, v = parts
    b = b.upper()
    if b not in VALID_BOOK_CODES:
        return None
    try:
        return b, int(c), int(v)
    except ValueError:
        return None

def extract_strongs(attrs: dict):
    """Strong's from <w s="H####"> (and a few aliases just in case)."""
    candidates = []
    for k in ("s","lemma","lemmas","strong","x-strong","x_strong"):
        val = attrs.get(k)
        if val:
            candidates.append(val)
    if not candidates:
        return []
    toks = []
    for val in candidates:
        for piece in re.split(r"[|\s;,]+", val.strip()):
            if not piece:
                continue
            m = re.search(r"([HhGg]\d{1,5})", piece)
            if m:
                toks.append(m.group(1).upper())
    out, seen = [], set()
    for s in toks:
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out

def tokenize_min(text: str):
    parts = re.split(r"(\s+)", text or "")
    return [p for p in parts if p and not p.isspace()]

def process_file(path: Path, books_accum: dict, counters: dict):
    root = ET.parse(str(path)).getroot()

    current_trip = None           # tuple ('GEN', 1, 1)
    verse_tokens, verse_strongs = [], []

    def flush_verse():
        nonlocal current_trip, verse_tokens, verse_strongs
        if current_trip and verse_tokens:
            bk, chap, ver = current_trip
            bdict = books_accum.setdefault(bk, {"chapters": {}})
            ch = bdict["chapters"].setdefault(str(chap), {})
            ch[str(ver)] = {"tokens": verse_tokens, "s": verse_strongs}
            counters["verses"] += 1
        verse_tokens, verse_strongs = [], []

    for node in root.iter():
        tag = strip_ns(node.tag)
        attrs = node.attrib

        # Verse start: <v ... bcv="GEN.1.1" ...>
        if tag == "v" and "bcv" in attrs:
            flush_verse()
            trip = parse_bcv(attrs["bcv"])
            if trip:
                current_trip = trip
                counters["starts"] += 1
                # text immediately after <v> marker lives in node.tail
                if node.tail:
                    for part in tokenize_min(node.tail):
                        verse_tokens.append({"t": part, "s": []})
            else:
                current_trip = None
            continue

        # Within an open verse → accumulate text + Strong's
        if current_trip:
            if tag == "w":  # Strong's-bearing token
                s_list = extract_strongs(attrs)
                text = "".join(node.itertext()).strip()
                if text:
                    for part in tokenize_min(text):
                        verse_tokens.append({"t": part, "s": s_list})
                        for s in s_list:
                            if s not in verse_strongs:
                                verse_strongs.append(s)
                if node.tail:
                    for part in tokenize_min(node.tail):
                        verse_tokens.append({"t": part, "s": []})
                continue

            # Skip notes/xrefs/titles if present
            if tag in {"note","xref","title","toc","rem"}:
                continue

            # Generic text accumulation (paragraphs, quotes, etc.)
            if node.text:
                for part in tokenize_min(node.text):
                    verse_tokens.append({"t": part, "s": []})
            if node.tail:
                for part in tokenize_min(node.tail):
                    verse_tokens.append({"t": part, "s": []})

    # flush trailing verse at EOF
    flush_verse()

def main():
    print("Scanning USFX:", USFX_DIR)
    xmls = sorted(USFX_DIR.rglob("*.xml"))
    print(f"Found {len(xmls)} XML file(s).")

    books, counters = {}, {"files": len(xmls), "verses": 0, "starts": 0}
    # Prefer the big content file if present, but we’ll just process all .xml
    for p in xmls:
        process_file(p, books, counters)

    # Write per-book JSON
    for bk, data in books.items():
        out_path = OUT_DIR / f"{bk}.json"
        out_path.write_text(json.dumps({"book": bk, **data}, ensure_ascii=False), encoding="utf-8")
        print("Wrote", out_path)

    manifest = {
        "version": "v1",
        "corpus": "KJV + Strong's (USFX)",
        "books": sorted(books.keys()),
        "files": counters["files"],
        "verses": counters["verses"],
        "starts": counters["starts"],
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    print(f"Done. Books: {len(books)}  Verses: {counters['verses']}  Files: {counters['files']}  Starts: {counters['starts']}")

if __name__ == "__main__":
    main()
