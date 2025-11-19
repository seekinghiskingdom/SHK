from pathlib import Path
from xml.etree import ElementTree as ET
import json, re

# --- EDIT if needed ---
REPO_ROOT = Path(r"C:\Users\hrbncv\SHK\SHK").resolve()
USFX_FILE = REPO_ROOT / "tools/lit-import/data/raw/web/usfx/eng-web.usfx.xml"
OUT_DIR   = REPO_ROOT / "docs/data/v1/lit/bible/en/web"
# ----------------------

OUT_DIR.mkdir(parents=True, exist_ok=True)

VALID_BOOKS = {
    "GEN","EXO","LEV","NUM","DEU","JOS","JDG","RUT","1SA","2SA","1KI","2KI",
    "1CH","2CH","EZR","NEH","EST","JOB","PSA","PRO","ECC","SNG","ISA","JER",
    "LAM","EZK","DAN","HOS","JOL","AMO","OBA","JON","MIC","NAM","HAB","ZEP",
    "HAG","ZEC","MAL","MAT","MRK","LUK","JHN","ACT","ROM","1CO","2CO","GAL",
    "EPH","PHP","COL","1TH","2TH","1TI","2TI","TIT","PHM","HEB","JAS","1PE",
    "2PE","1JN","2JN","3JN","JUD","REV"
}

SKIP_TAGS = {"note","xref","title","toc","rem"}

def strip_ns(tag: str) -> str:
    return tag.split("}", 1)[-1]

def as_int(x):
    try:
        return int(x)
    except Exception:
        return None

def main():
    print("Reading:", USFX_FILE)
    if not USFX_FILE.exists():
        raise FileNotFoundError(USFX_FILE)

    # Stream parse so we can react to verse start (<v ...>) and end (<ve ...>)
    context = ET.iterparse(str(USFX_FILE), events=("start","end"))
    _, root = next(context)

    books: dict[str, dict] = {}
    current_book: str | None = None
    current_chapter: int | None = None
    current_verse: int | None = None
    buffering = False
    buffer_parts: list[str] = []

    verse_count = 0
    verse_starts = 0

    def flush():
        nonlocal buffer_parts, current_book, current_chapter, current_verse, verse_count
        if current_book and current_chapter and current_verse and buffer_parts:
            text = "".join(buffer_parts).strip()
            if text:
                bdict = books.setdefault(current_book, {"chapters": {}})
                ch = bdict["chapters"].setdefault(str(current_chapter), {})
                ch[str(current_verse)] = text
                verse_count += 1
        buffer_parts = []

    for event, elem in context:
        tag = strip_ns(elem.tag)
        attrs = elem.attrib

        if event == "start":
            # Book markers
            if tag == "book":
                # e.g., <book code="GEN"> … </book>
                maybe = (attrs.get("code") or attrs.get("id") or "").upper()
                if maybe in VALID_BOOKS:
                    flush()
                    current_book = maybe
                    current_chapter = None
                    current_verse = None
                continue
            if tag == "scriptureBook":
                # e.g., <scriptureBook ubsAbbreviation="GEN" …>
                maybe = (attrs.get("ubsAbbreviation") or "").upper()
                if maybe in VALID_BOOKS:
                    flush()
                    current_book = maybe
                    current_chapter = None
                    current_verse = None
                continue

            # Chapter markers
            if tag in {"c","chapter"}:
                # e.g., <c id="1">
                cid = as_int(attrs.get("id") or attrs.get("number"))
                if cid is not None:
                    flush()
                    current_chapter = cid
                    current_verse = None
                continue

            # Verse START (no bcv; use id + current book/chapter)
            if tag == "v":
                vnum = as_int(attrs.get("id") or attrs.get("number"))
                if vnum is not None and current_book in VALID_BOOKS and current_chapter is not None:
                    flush()
                    current_verse = vnum
                    buffering = True
                    verse_starts += 1
                    # Any immediate text after <v ...> will appear in elem.tail at 'end'
                continue

        else:  # event == "end"
            # Verse END tag used by many USFXs
            if tag == "ve":
                if buffering:
                    # include any tail after </ve>
                    if elem.tail:
                        buffer_parts.append(elem.tail)
                    flush()
                buffering = False
                current_verse = None
                elem.clear()
                continue

            # Accumulate text while inside a verse
            if buffering and current_book in VALID_BOOKS and current_chapter is not None and current_verse is not None:
                if tag in SKIP_TAGS:
                    if elem.tail:
                        buffer_parts.append(elem.tail)
                else:
                    if elem.text:
                        buffer_parts.append(elem.text)
                    if elem.tail:
                        buffer_parts.append(elem.tail)

            # Handle <v> end (include tail)
            if tag == "v":
                if buffering and elem.tail:
                    buffer_parts.append(elem.tail)

            # Regular cleanup
            if elem is not root:
                elem.clear()
            else:
                root.clear()

    # Final flush at EOF
    flush()

    # Write per-book JSON
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for bk, data in books.items():
        out = OUT_DIR / f"{bk}.json"
        out.write_text(json.dumps({"book": bk, **data}, ensure_ascii=False), encoding="utf-8")
        print("Wrote", out)

    # Manifest
    (OUT_DIR / "manifest.json").write_text(
        json.dumps(
            {"version":"v1","corpus":"WEB (plain, USFX)","books":sorted(books.keys()),
             "starts": verse_starts, "verses": verse_count},
            ensure_ascii=False),
        encoding="utf-8"
    )
    print(f"Done. Books: {len(books)}  Verses: {verse_count}  Starts: {verse_starts}")

if __name__ == "__main__":
    main()
