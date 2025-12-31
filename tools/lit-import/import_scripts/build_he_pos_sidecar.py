#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import xml.etree.ElementTree as ET
import collections


# ---------- Inputs (raw) ----------
RAW_DIR = Path("tools/lit-import/data/raw/strongs/he")
HE_STRONGS_XML = RAW_DIR / "HebrewStrong.xml"
POS_XML = RAW_DIR / "PartsOfSpeech.xml"
BDB_POS_XML = RAW_DIR / "BDBPartsOfSpeech.xml"

# ---------- Outputs (v1) ----------
OUT_DIR = Path("docs/data/v1/lit/strongs/he/pos")
OUT_POS_JSONL = OUT_DIR / "pos.jsonl"
OUT_POS_CATALOG = OUT_DIR / "catalog.json"
OUT_REPORT = OUT_DIR / "_build_report.json"


def norm_h_id(sid: str) -> str:
    """
    Normalize HebrewStrong.xml IDs (commonly H1..H8674) to canonical H0001..H8674.
    If it's already padded, it stays unchanged.
    """
    sid = (sid or "").strip()
    if sid.startswith("H") and sid[1:].isdigit():
        return "H" + sid[1:].zfill(4)
    return sid


def get_ns(root: ET.Element) -> dict[str, str]:
    """Namespace map for HebrewStrong.xml."""
    if root.tag.startswith("{") and "}" in root.tag:
        uri = root.tag.split("}", 1)[0].strip("{")
        return {"m": uri}
    return {}


def parse_pos_catalog(xml_path: Path) -> dict[str, dict]:
    """
    PartsOfSpeech.xml / BDBPartsOfSpeech.xml schema:
      <PartsOfSpeech>
        <POS><Code>n-m</Code><Name>Noun Masculine</Name></POS>
        ...
      </PartsOfSpeech>
    """
    root = ET.parse(xml_path).getroot()
    out: dict[str, dict] = {}

    for pos_el in root.findall(".//POS"):
        code = (pos_el.findtext("Code") or "").strip()
        name = (pos_el.findtext("Name") or "").strip()
        if not code or not name:
            continue
        out[code] = {
            "label": name,
            "source_file": xml_path.name,
        }

    return out


def extract_entry_pos(xml_path: Path) -> list[dict]:
    """
    HebrewStrong.xml schema (namespaced):
      <entry id="H1">
        <w pos="n-m" ... />
      </entry>

    'pos' may contain multiple codes separated by whitespace.
    """
    root = ET.parse(xml_path).getroot()
    ns = get_ns(root)

    entries = root.findall(".//m:entry", ns) if ns else root.findall(".//entry")
    rows: list[dict] = []

    for entry in entries:
        sid_raw = entry.get("id")
        if not sid_raw:
            continue

        sid = norm_h_id(sid_raw)

        w = entry.find("m:w", ns) if ns else entry.find("w")
        if w is None:
            continue

        pos_raw = (w.get("pos") or "").strip()
        if not pos_raw:
            continue

        codes = [c.strip() for c in pos_raw.split() if c.strip()]
        rows.append({"id": sid, "id_raw": sid_raw, "pos_raw": pos_raw, "pos_codes": codes})

    return rows


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Build catalogs
    cat_pos = parse_pos_catalog(POS_XML)
    cat_bdb = parse_pos_catalog(BDB_POS_XML)

    # Merge catalogs: prefer PartsOfSpeech.xml labels, fall back to BDBPartsOfSpeech.xml
    catalog = dict(cat_bdb)
    catalog.update(cat_pos)

    OUT_POS_CATALOG.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    # Extract POS per entry
    rows = extract_entry_pos(HE_STRONGS_XML)

    unknown = collections.Counter()
    multi = 0

    def sort_key(r: dict):
        # H0001..H9999 numeric sort
        s = r["id"][1:]
        return int(s) if s.isdigit() else r["id"]

    with OUT_POS_JSONL.open("w", encoding="utf-8") as f:
        for r in sorted(rows, key=sort_key):
            labels = []
            for code in r["pos_codes"]:
                info = catalog.get(code)
                if not info:
                    unknown[code] += 1
                    labels.append(None)
                else:
                    labels.append(info["label"])

            if len(r["pos_codes"]) > 1:
                multi += 1

            out = {
                "id": r["id"],          # canonical join key (H####)
                "id_raw": r["id_raw"],  # original (often H#)
                "pos_raw": r["pos_raw"],
                "pos_codes": r["pos_codes"],
                "pos_labels": labels,
            }
            f.write(json.dumps(out, ensure_ascii=False) + "\n")

    report = {
        "entries_with_pos": len(rows),
        "catalog_size": len(catalog),
        "multi_pos_entries": multi,
        "unknown_pos_codes_count": len(unknown),
        "unknown_pos_codes_top": unknown.most_common(50),
        "outputs": {
            "pos_jsonl": str(OUT_POS_JSONL).replace("\\", "/"),
            "catalog_json": str(OUT_POS_CATALOG).replace("\\", "/"),
            "report_json": str(OUT_REPORT).replace("\\", "/"),
        },
    }
    OUT_REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
