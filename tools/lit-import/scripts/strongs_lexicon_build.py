
from pathlib import Path
from xml.etree import ElementTree as ET
import json, re

# --- Paths (edit if needed) ---
REPO_ROOT = Path(r"C:\Users\hrbncv\SHK\SHK").resolve()
RAW_DIR   = REPO_ROOT / "tools/lit-import/data/raw/strongs"
OUT_DIR   = REPO_ROOT / "docs/data/v1/lit/strongs"
OUT_FILE  = OUT_DIR / "lexicon.json"
# --------------------------------

OUT_DIR.mkdir(parents=True, exist_ok=True)

HINTS_HEB = re.compile(r"(heb|hebr|strongs.?heb|h[0-9]{3,5})", re.I)
HINTS_GRK = re.compile(r"(grk|greek|strongs.?gr(eek)?|g[0-9]{3,5})", re.I)

def strip_ns(tag): return tag.split("}", 1)[-1]

def to_sid(raw: str, is_greek: bool | None = None):
    """Normalize an identifier into 'H####' or 'G####'."""
    if not raw: return None
    m = re.search(r"([HhGg])\s*0*([0-9]{1,5})", raw)
    if m:
        return m.group(1).upper() + m.group(2).zfill(4)
    # If no letter, infer from context and digits:
    m2 = re.search(r"\b0*([0-9]{1,5})\b", raw)
    if m2:
        n = m2.group(1).zfill(4)
        if is_greek is True: return "G"+n
        if is_greek is False: return "H"+n
    return None

def text_join(node):
    return "".join(node.itertext()).strip()

def parse_variant_generic(root, default_greek=None):
    """
    Best-effort parser for unknown XML shapes: look for elements with an 'id-ish'
    attribute and sub-tags that look like lemma/gloss/def/translit, etc.
    """
    out = {}
    for e in root.iter():
        tag = strip_ns(e.tag).lower()
        # candidate id in attributes
        sid = None
        for k in ("id","n","n_str","nStrong","strong","strongs","index","entry","lemma"):
            if k in e.attrib:
                sid = to_sid(e.attrib[k], default_greek)
                if sid: break
        # candidate id in text like "<id>H7225</id>"
        if not sid:
            for child in e:
                ctag = strip_ns(child.tag).lower()
                if ctag in {"id","strong","strongs","index","n"}:
                    sid = to_sid(text_join(child), default_greek)
                    if sid: break
        if not sid:
            continue

        rec = out.setdefault(sid, {"id": sid})
        # harvest nearby fields
        for child in e:
            ctag = strip_ns(child.tag).lower()
            val = text_join(child)
            if not val: continue
            if "lemma" in ctag and "hebrew" not in ctag and "greek" not in ctag:
                rec.setdefault("lemma", val)
            elif ctag in {"translit","transliteration"}:
                rec.setdefault("translit", val)
            elif ctag in {"pron","pronunciation"}:
                rec.setdefault("pron", val)
            elif ctag in {"pos","partofspeech","part_of_speech"}:
                rec.setdefault("pos", val)
            elif ctag in {"gloss","shortdef","short_def","meaning"}:
                rec.setdefault("gloss", val)
            elif "def" in ctag:
                rec.setdefault("def", val)
            elif "deriv" in ctag:
                rec.setdefault("derivation", val)
            elif ctag in {"refs","ref","see","seealso"}:
                rec.setdefault("refs", val)
        # also grab inline text if nothing else
        if "def" not in rec:
            body = text_join(e)
            if body:
                rec.setdefault("def", body)

    return out

def parse_zefania_dictionary(root, default_greek=None):
    """
    Zefania dictionaries commonly use <strongs-dictionary> or <dictionary> or <lexicon>
    with entries like <entry id="H7225"><w>…</w><translit>…</translit><def>…</def></entry>.
    """
    out = {}
    for ent in root.iter():
        tag = strip_ns(ent.tag).lower()
        if tag not in {"entry","lex","item","record"}:  # flexible
            continue
        sid = None
        # id in attribute
        for k in ("id","n","strong","strongs"):
            if k in ent.attrib:
                sid = to_sid(ent.attrib[k], default_greek)
                if sid: break
        if not sid:
            continue
        rec = out.setdefault(sid, {"id": sid})
        for child in ent:
            ctag = strip_ns(child.tag).lower()
            val = text_join(child)
            if not val: continue
            if ctag in {"w","lemma","headword"}:
                rec.setdefault("lemma", val)
            elif ctag in {"translit","transliteration"}:
                rec.setdefault("translit", val)
            elif ctag in {"pron","pronunciation"}:
                rec.setdefault("pron", val)
            elif ctag in {"pos","partofspeech","part_of_speech"}:
                rec.setdefault("pos", val)
            elif ctag in {"gloss","shortdef","short_def","meaning"}:
                rec.setdefault("gloss", val)
            elif ctag in {"def","definition","content","text"}:
                rec.setdefault("def", val)
            elif "deriv" in ctag:
                rec.setdefault("derivation", val)
            elif ctag in {"refs","ref","see","seealso"}:
                rec.setdefault("refs", val)
    return out

def parse_file(path: Path):
    print("Parsing:", path.name)
    is_greek = None
    name_lower = path.name.lower()
    if HINTS_GRK.search(name_lower): is_greek = True
    if HINTS_HEB.search(name_lower): is_greek = False
    root = ET.parse(str(path)).getroot()

    # Try zefania-ish first
    out = parse_zefania_dictionary(root, default_greek=is_greek)
    if out:
        for k in out.values(): k["source"] = path.name
        return out

    # Fallback: generic
    out = parse_variant_generic(root, default_greek=is_greek)
    for k in out.values(): k["source"] = path.name
    return out

def main():
    if not RAW_DIR.exists():
        print("ERROR: missing", RAW_DIR)
        return
    files = sorted([p for p in RAW_DIR.rglob("*.xml")])
    if not files:
        print("No XML files found under", RAW_DIR)
        return

    merged = {}
    count_h = count_g = 0
    for f in files:
        part = parse_file(f)
        for sid, rec in part.items():
            # merge, prefer first non-empty fields
            tgt = merged.setdefault(sid, {"id": sid})
            for k, v in rec.items():
                if k == "id": continue
                if v and not tgt.get(k):
                    tgt[k] = v
    for sid in merged:
        if sid.startswith("H"): count_h += 1
        if sid.startswith("G"): count_g += 1

    OUT_FILE.write_text(json.dumps(merged, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {OUT_FILE}")
    print(f"Entries: total={len(merged)}  Hebrew={count_h}  Greek={count_g}")

if __name__ == "__main__":
    main()
