from pathlib import Path
from xml.etree import ElementTree as ET
import json, re

# --- EDIT these if your paths differ ---
REPO_ROOT = Path(r"C:\Users\hrbncv\SHK\SHK").resolve()
ZEF_FILE  = REPO_ROOT / "tools/lit-import/data/raw/asv/zefania/eng-asv.zefania.xml"
OUT_DIR   = REPO_ROOT / "docs/data/v1/lit/bible/en/asv"
# ---------------------------------------

OUT_DIR.mkdir(parents=True, exist_ok=True)

# Map Zefania book order (1..66) to your 3-letter codes
ORDER_TO_CODE = [
    "GEN","EXO","LEV","NUM","DEU","JOS","JDG","RUT","1SA","2SA","1KI","2KI",
    "1CH","2CH","EZR","NEH","EST","JOB","PSA","PRO","ECC","SNG","ISA","JER",
    "LAM","EZK","DAN","HOS","JOL","AMO","OBA","JON","MIC","NAM","HAB","ZEP",
    "HAG","ZEC","MAL","MAT","MRK","LUK","JHN","ACT","ROM","1CO","2CO","GAL",
    "EPH","PHP","COL","1TH","2TH","1TI","2TI","TIT","PHM","HEB","JAS","1PE",
    "2PE","1JN","2JN","3JN","JUD","REV"
]

def strip_ns(tag: str) -> str:
    return tag.split("}", 1)[-1]

def clean(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())

def main():
    print("Reading:", ZEF_FILE)
    root = ET.parse(str(ZEF_FILE)).getroot()
    if strip_ns(root.tag) != "XMLBIBLE":
        print("Warning: root is not <XMLBIBLE>; trying anyway…")

    books = {}  # { "GEN": {"chapters": {"1":{"1":"text"}}}}
    # Structure: <XMLBIBLE> -> <BIBLEBOOK bnumber="1" bname="Genesis"> -> <CHAPTER cnumber="1"> -> <VERS vnumber="1">
    for b in root.findall(".//BIBLEBOOK"):
        bnum_attr = b.attrib.get("bnumber")
        try:
            idx = int(bnum_attr) - 1 if bnum_attr else None
        except ValueError:
            idx = None

        if idx is not None and 0 <= idx < 66:
            bk = ORDER_TO_CODE[idx]
        else:
            # fallback by name (best-effort)
            bname = (b.attrib.get("bname") or "")[:3].upper()
            bk = bname if bname in ORDER_TO_CODE else None
        if not bk:
            continue

        bdict = books.setdefault(bk, {"chapters": {}})

        for ch in b.findall("./CHAPTER"):
            cnum = ch.attrib.get("cnumber")
            if not (cnum and cnum.isdigit()):
                continue
            chd = bdict["chapters"].setdefault(cnum, {})

            for v in ch.findall("./VERS"):
                vnum = v.attrib.get("vnumber")
                if not (vnum and vnum.isdigit()):
                    continue
                # Zefania sometimes nests <STYLE> etc.; use itertext
                text = clean("".join(v.itertext()))
                if text:
                    chd[vnum] = text

    # write per-book
    for bk, data in books.items():
        out_path = OUT_DIR / f"{bk}.json"
        out_path.write_text(json.dumps({"book": bk, **data}, ensure_ascii=False), encoding="utf-8")
        print("Wrote", out_path)

    manifest = {"version": "v1", "corpus": "ASV (Zefania)", "books": sorted(books.keys())}
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    print(f"Done. Books: {len(books)}  Output: {OUT_DIR}")

if __name__ == "__main__":
    main()
