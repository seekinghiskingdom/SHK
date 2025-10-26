# tools/lit-import/src/shk_lit_import/parsers/bible_osis_plain.py
from pathlib import Path
from xml.etree import ElementTree as ET

# Minimal OSIS book-code map (expand after GEN test)
OSIS_TO_CODE = {
    "Gen": "GEN",
    # "Exod": "EXO", "Lev": "LEV", "Num": "NUM", "Deut": "DEU", ...
}

def _iter_verses(osis_xml: Path):
    tree = ET.parse(str(osis_xml))
    root = tree.getroot()
    for v in root.iter():
        tag = v.tag.split("}", 1)[-1]  # strip namespace
        if tag != "verse":
            continue
        osis_id = v.attrib.get("osisID")
        if not osis_id:
            continue

        # Normalize to a single osis_id like "Gen.1.1"
        first = osis_id.split(" ", 1)[0].split("-", 1)[0]
        parts = first.split(".")
        if len(parts) < 3:
            continue

        osis_book, chap_s, verse_s = parts[0], parts[1], parts[2]
        book_code = OSIS_TO_CODE.get(osis_book)
        if not book_code:
            continue

        try:
            chap = int(chap_s)
            ver = int(verse_s)
        except ValueError:
            continue

        text = "".join(v.itertext()).strip()

        # IMPORTANT: exporter expects a dotted string field
        yield {
            "osis_id": f"{osis_book}.{chap}.{ver}",  # e.g., "Gen.1.1"
            "book": book_code,                       # e.g., "GEN"
            "chapter": chap,
            "verse": ver,
            "text": text,
        }

def parse_to_tokens(inputs, spec):
    if not inputs:
        return [], {"books": []}

    wanted = set(spec.get("books", [])) if isinstance(spec.get("books"), list) else None
    recs = []
    for xml_path in inputs:
        for rec in _iter_verses(Path(xml_path)):
            if wanted and rec["book"] not in wanted:
                continue
            recs.append(rec)

    meta = {"books": sorted({r["book"] for r in recs})}
    return recs, meta
