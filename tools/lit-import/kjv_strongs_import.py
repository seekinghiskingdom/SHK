from __future__ import annotations

import json
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

# ----------------- data structures -----------------

@dataclass
class StrongToken:
    text: str
    strongs: List[str]


@dataclass
class StrongVerse:
    verse: int
    tokens: List[StrongToken] = field(default_factory=list)

    @property
    def text(self) -> str:
        # basic reconstruction of the plain verse text
        return " ".join(t.text for t in self.tokens).replace(" .", ".")


@dataclass
class StrongBook:
    book_id: str
    name: str
    chapters: Dict[int, List[StrongVerse]] = field(default_factory=dict)


# ----------------- raw zip helpers -----------------

def _find_kjvd_usfm_zip(repo_root: Path) -> Path:
    """
    Reuse the same eng-kjv_usfm.zip as bible.en.kjvd.
    """
    kjvd_raw = (
        repo_root
        / "tools"
        / "lit-import"
        / "data"
        / "raw"
        / "bible"
        / "en"
        / "kjvd"
    )
    cands = list(kjvd_raw.glob("*usfm.zip"))
    if not cands:
        raise FileNotFoundError(f"No *usfm.zip found in {kjvd_raw}")
    cands.sort()
    return cands[0]


# ----------------- USFM parsing (Strong's) -----------------

_w_tag_re = re.compile(r"\\w\s+([^|]+)\|([^\\]+?)\\w\*")


def _extract_strongs_ids(attr_block: str) -> List[str]:
    """Parse Strong's IDs like H7225, G3056, etc., from the attribute block."""
    return re.findall(r"[HG]\d+", attr_block)


def _parse_tokens_usfm_segment(segment: str) -> List[StrongToken]:
    """
    Given the verse text portion after '\\v N ', break it into tokens:
    - '\\w word|strong="H7225" ...\\w*' → token with Strong's IDs
    - plain text between tags → tokens without Strong's
    """
    tokens: List[StrongToken] = []
    pos = 0

    for m in _w_tag_re.finditer(segment):
        start, end = m.span()

        # plain text before this w-tag
        if start > pos:
            before = segment[pos:start].strip()
            if before:
                for w in before.split():
                    tokens.append(StrongToken(text=w, strongs=[]))

        word_text = m.group(1).strip()
        attrs = m.group(2)
        strongs = _extract_strongs_ids(attrs)

        if word_text:
            tokens.append(StrongToken(text=word_text, strongs=strongs))

        pos = end

    # trailing plain text
    if pos < len(segment):
        after = segment[pos:].strip()
        if after:
            for w in after.split():
                tokens.append(StrongToken(text=w, strongs=[]))

    return tokens


def _parse_kjv_strongs_from_usfm_zip(usfm_zip: zipfile.ZipFile) -> Dict[str, StrongBook]:
    """
    Walk all *.usfm files in the KJVD zip and build a StrongBook map with
    tokens + Strong's IDs per verse.
    """
    books: Dict[str, StrongBook] = {}
    current_book_id: str | None = None
    current_chapter: int | None = None
    current_verse: StrongVerse | None = None

    # iterate all book files, including Apocrypha, in sorted order
    for fname in sorted(n for n in usfm_zip.namelist() if n.lower().endswith(".usfm")):
        text = usfm_zip.read(fname).decode("utf-8-sig", errors="replace")

        for raw_line in text.splitlines():
            line = raw_line.rstrip("\n")
            stripped = line.strip()
            if not stripped:
                continue

            # \id GEN
            if stripped.startswith("\\id "):
                parts = stripped.split(maxsplit=2)
                if len(parts) >= 2:
                    current_book_id = parts[1].upper()
                    if current_book_id not in books:
                        books[current_book_id] = StrongBook(
                            book_id=current_book_id, name=current_book_id
                        )
                current_chapter = None
                current_verse = None
                continue

            # \h Genesis
            if stripped.startswith("\\h "):
                if current_book_id:
                    name = stripped[3:].strip()
                    if name:
                        books[current_book_id].name = name
                continue

            # \c 1
            if stripped.startswith("\\c "):
                parts = stripped.split(maxsplit=1)
                if len(parts) == 2:
                    try:
                        cnum = int(parts[1].strip())
                        current_chapter = cnum
                        if current_book_id:
                            books[current_book_id].chapters.setdefault(cnum, [])
                        current_verse = None
                    except ValueError:
                        pass
                continue

            # \v 1 In the beginning...
            if stripped.startswith("\\v "):
                parts = stripped.split(maxsplit=2)
                if len(parts) < 2:
                    continue
                try:
                    vnum = int(parts[1])
                except ValueError:
                    continue

                verse_text_part = parts[2] if len(parts) == 3 else ""
                tokens = _parse_tokens_usfm_segment(verse_text_part)

                if current_book_id is None:
                    continue
                if current_chapter is None:
                    current_chapter = 1
                    books[current_book_id].chapters.setdefault(current_chapter, [])

                verse_obj = StrongVerse(verse=vnum, tokens=tokens)
                books[current_book_id].chapters[current_chapter].append(verse_obj)
                current_verse = verse_obj
                continue

            # continuation lines: treat as more text for the current verse
            if current_book_id and current_chapter and current_verse:
                tokens = _parse_tokens_usfm_segment(stripped)
                if tokens:
                    current_verse.tokens.extend(tokens)

    return books


# ----------------- public entry point -----------------

def import_kjv_strongs_from_usfm(
    repo_root: Path, raw_dir: Path, out_dir: Path, force: bool = False
) -> None:
    """
    Build bible.en.kjv_strongs using the same eng-kjv_usfm.zip as bible.en.kjvd,
    but preserving Strong's IDs on each token.
    """
    manifest_path = raw_dir / "manifest.json"
    with manifest_path.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    code = manifest.get("code", "kjv_strongs")
    language = manifest.get("language", "en")

    usfm_zip_path = _find_kjvd_usfm_zip(repo_root)
    with zipfile.ZipFile(usfm_zip_path, "r") as usfm_zip:
        books_map = _parse_kjv_strongs_from_usfm_zip(usfm_zip)

    out_dir.mkdir(parents=True, exist_ok=True)
    books_json = out_dir / "books.json"
    chapters_jsonl = out_dir / "chapters.jsonl"
    meta_json = out_dir / "meta.json"

    if not force and books_json.exists() and chapters_jsonl.exists():
        raise FileExistsError(
            f"Output already exists in {out_dir} (use --force to overwrite)"
        )

    ordered_ids = sorted(books_map.keys())

    # books.json
    books_payload = {
        "order": ordered_ids,
        "names": {bid: books_map[bid].name for bid in ordered_ids},
    }
    with books_json.open("w", encoding="utf-8") as f:
        json.dump(books_payload, f, ensure_ascii=False, indent=2)

    # chapters.jsonl
    total_chapters = 0
    total_verses = 0
    with chapters_jsonl.open("w", encoding="utf-8") as f:
        for bid in ordered_ids:
            book = books_map[bid]
            for chapter_no in sorted(book.chapters.keys()):
                verses = book.chapters[chapter_no]
                if not verses:
                    continue
                total_chapters += 1
                total_verses += len(verses)
                obj = {
                    "book_id": bid,
                    "chapter": chapter_no,
                    "verses": [
                        {
                            "verse": v.verse,
                            "text": v.text,
                            "tokens": [
                                {"t": t.text, "s": t.strongs} for t in v.tokens
                            ],
                        }
                        for v in verses
                    ],
                }
                f.write(json.dumps(obj, ensure_ascii=False) + "\n")

    # meta.json
    meta = {
        "code": code,
        "language": language,
        "source": {
            "raw_dir": str(raw_dir),
            "usfm_zip": usfm_zip_path.name,
        },
        "counts": {
            "books": len(ordered_ids),
            "chapters": total_chapters,
            "verses": total_verses,
        },
        "annotations": {"strongs_tokens": True},
    }
    with meta_json.open("w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
