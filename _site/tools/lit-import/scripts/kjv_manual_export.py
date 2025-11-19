from pathlib import Path
from xml.etree import ElementTree as ET
import json

# --- EDIT if your paths differ ---
REPO_ROOT = Path(r"C:\Users\hrbncv\SHK\SHK").resolve()
OSIS_FILE = REPO_ROOT / "tools/lit-import/data/raw/kjv/osis/eng-kjv.osis.xml"
OUT_DIR   = REPO_ROOT / "docs/data/v1/lit/bible/en/kjv"
# ----------------------------------

OUT_DIR.mkdir(parents=True, exist_ok=True)

OSIS_TO_CODE = {
    "Gen":"GEN","Exod":"EXO","Lev":"LEV","Num":"NUM","Deut":"DEU","Josh":"JOS","Judg":"JDG","Ruth":"RUT",
    "1Sam":"1SA","2Sam":"2SA","1Kgs":"1KI","2Kgs":"2KI","1Chr":"1CH","2Chr":"2CH","Ezra":"EZR","Neh":"NEH",
    "Esth":"EST","Job":"JOB","Ps":"PSA","Prov":"PRO","Eccl":"ECC","Song":"SNG","Isa":"ISA","Jer":"JER",
    "Lam":"LAM","Ezek":"EZK","Dan":"DAN","Hos":"HOS","Joel":"JOL","Amos":"AMO","Obad":"OBA","Jonah":"JON",
    "Mic":"MIC","Nah":"NAM","Hab":"HAB","Zeph":"ZEP","Hag":"HAG","Zech":"ZEC","Mal":"MAL","Matt":"MAT",
    "Mark":"MRK","Luke":"LUK","John":"JHN","Acts":"ACT","Rom":"ROM","1Cor":"1CO","2Cor":"2CO","Gal":"GAL",
    "Eph":"EPH","Phil":"PHP","Col":"COL","1Thess":"1TH","2Thess":"2TH","1Tim":"1TI","2Tim":"2TI","Titus":"TIT",
    "Phlm":"PHM","Heb":"HEB","Jas":"JAS","1Pet":"1PE","2Pet":"2PE","1John":"1JN","2John":"2JN","3John":"3JN",
    "Jude":"JUD","Rev":"REV"
}

def strip_ns(tag: str) -> str:
    return tag.split("}", 1)[-1]

def parse_osis_triplet(osis: str):
    """Return (osis_book, chap:int, verse:int) from 'Gen.1.1'."""
    first = osis.split(" ", 1)[0].split("-", 1)[0]
    parts = first.split(".")
    if len(parts) < 3:
        return None
    b, c, v = parts[0], parts[1], parts[2]
    try:
        return b, int(c), int(v)
    except ValueError:
        return None

print("Reading:", OSIS_FILE)
tree = ET.parse(str(OSIS_FILE))
root = tree.getroot()

books: dict[str, dict] = {}  # "GEN": {"chapters": {"1": {"1": "In the beginning...", ...}, ...}}
count = 0

inside = False
current_id = None
buffer = []

# Two modes: (A) milestone verses with sID/eID; (B) wrapped verses with osisID
for node in root.iter():
    tag = strip_ns(node.tag)

    # (B) Wrapped verse: <verse osisID="Gen.1.1"> ... </verse>
    if tag == "verse" and "osisID" in node.attrib and not {"sID","eID"} & node.attrib.keys():
        trip = parse_osis_triplet(node.attrib["osisID"])
        if not trip:
            continue
        osis_book, chap, ver = trip
        bk = OSIS_TO_CODE.get(osis_book)
        if not bk:
            continue
        text = "".join(node.itertext()).strip()
        if not text:
            continue
        book = books.setdefault(bk, {"chapters": {}})
        ch = book["chapters"].setdefault(str(chap), {})
        ch[str(ver)] = text
        count += 1
        continue

    # (A) Milestones: start
    if tag == "verse" and "sID" in node.attrib:
        current_id = node.attrib["sID"]
        inside = True
        buffer = []
        # text immediately after the start milestone lives in .tail
        if node.tail:
            buffer.append(node.tail)
        continue

    # (A) Milestones: accumulating text
    if inside:
        if node.text:
            buffer.append(node.text)
        if node.tail:
            buffer.append(node.tail)

    # (A) Milestones: end
    if tag == "verse" and "eID" in node.attrib and inside:
        # close the verse
        trip = parse_osis_triplet(current_id)
        inside = False
        if not trip:
            continue
        osis_book, chap, ver = trip
        bk = OSIS_TO_CODE.get(osis_book)
        if not bk:
            continue
        text = "".join(buffer).strip()
        buffer = []
        current_id = None
        if not text:
            continue
        book = books.setdefault(bk, {"chapters": {}})
        ch = book["chapters"].setdefault(str(chap), {})
        ch[str(ver)] = text
        count += 1

print(f"Collected {count} verses across {len(books)} books.")

# Write per-book JSON
OUT_DIR.mkdir(parents=True, exist_ok=True)
for bk, data in books.items():
    out_path = OUT_DIR / f"{bk}.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump({"book": bk, **data}, f, ensure_ascii=False)
    print("Wrote", out_path)

# Manifest
manifest = {
    "version": "v1",
    "corpus": "KJV (plain, OSIS)",
    "books": sorted(books.keys()),
}
(OUT_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
print("Done. Files at:", OUT_DIR)
