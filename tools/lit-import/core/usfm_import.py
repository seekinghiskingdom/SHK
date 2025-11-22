from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from usfm_parser import USFMBook, USFMParser

from kjv_strongs_import import import_kjv_strongs_from_usfm



@dataclass
class ImportContext:
    code: str
    language: str
    source_manifest: Dict[str, Any]
    raw_dir: Path
    out_dir: Path
    usfm_zip_path: Path
    overwrite: bool = False


def find_usfm_zip(raw_dir: Path) -> Path:
    candidates = list(raw_dir.glob("*usfm.zip"))
    if not candidates:
        raise FileNotFoundError(f"No *usfm.zip found in {raw_dir}")
    if len(candidates) > 1:
        candidates.sort()
    return candidates[0]


def load_raw_manifest(raw_dir: Path) -> Dict[str, Any]:
    m_path = raw_dir / "manifest.json"
    if not m_path.is_file():
        raise FileNotFoundError(f"manifest.json not found in {raw_dir}")
    with m_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def import_bible_from_raw_plan(
    repo_root: Path,
    raw_dir: Path,
    out_dir: Path,
    force: bool = False,
) -> None:
    """
    Import a single Bible translation from raw USFM ZIP into docs/data/v1/lit/bible.

    Assumptions:
    - raw_dir contains manifest.json and exactly one *_usfm.zip
    - manifest.json has at least: code, language
    """
    manifest = load_raw_manifest(raw_dir)
    code = manifest.get("code")
    language = manifest.get("language")
    if not code or not language:
        raise ValueError("manifest.json must define 'code' and 'language'")

    if code == "kjv_strongs":
        import_kjv_strongs_from_usfm(
            repo_root=repo_root,
            raw_dir=raw_dir,
            out_dir=out_dir,
            force=force,
        )
        return

    usfm_zip = find_usfm_zip(raw_dir)

    ctx = ImportContext(
        code=code,
        language=language,
        source_manifest=manifest,
        raw_dir=raw_dir,
        out_dir=out_dir,
        usfm_zip_path=usfm_zip,
        overwrite=force,
    )

    out_dir.mkdir(parents=True, exist_ok=True)

    books_json = out_dir / "books.json"
    chapters_jsonl = out_dir / "chapters.jsonl"
    meta_json = out_dir / "meta.json"

    if not ctx.overwrite and books_json.exists() and chapters_jsonl.exists():
        raise FileExistsError(f"Output already exists in {out_dir} (use --force to overwrite)")

    books, meta = parse_usfm_zip_to_books(ctx)

    # books.json
    books_payload = {
        "order": [b.book_id for b in books],
        "names": {b.book_id: b.name for b in books},
    }
    with books_json.open("w", encoding="utf-8") as f:
        json.dump(books_payload, f, ensure_ascii=False, indent=2)

    # chapters.jsonl
    with chapters_jsonl.open("w", encoding="utf-8") as f:
        for b in books:
            for chapter_no in sorted(b.chapters.keys()):
                verses = b.chapters[chapter_no]
                if not verses:
                    continue
                obj = {
                    "book_id": b.book_id,
                    "chapter": chapter_no,
                    "verses": [
                        {"verse": v.verse, "text": v.text}
                        for v in verses
                    ],
                }
                json_line = json.dumps(obj, ensure_ascii=False)
                f.write(json_line + "\n")

    # meta.json
    with meta_json.open("w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def parse_usfm_zip_to_books(ctx: ImportContext) -> Tuple[List[USFMBook], Dict[str, Any]]:
    books: Dict[str, USFMBook] = {}
    parser = USFMParser()

    with zipfile.ZipFile(ctx.usfm_zip_path, "r") as z:
        for name in sorted(z.namelist()):
            if not name.lower().endswith(".usfm"):
                continue
            with z.open(name, "r") as f:
                raw = f.read().decode("utf-8-sig", errors="replace")
            book = parser.parse_usfm(raw)
            if book.book_id is None:
                continue
            if book.book_id in books:
                existing = books[book.book_id]
                for chap, verses in book.chapters.items():
                    if chap in existing.chapters:
                        existing.chapters[chap].extend(verses)
                    else:
                        existing.chapters[chap] = verses
            else:
                books[book.book_id] = book

    # Canonical-ish order
    ordered_ids = sorted(
        books.keys(),
        key=lambda bid: (CANONICAL_ORDER.get(bid, 999), bid),
    )
    ordered_books: List[USFMBook] = [books[bid] for bid in ordered_ids]

    total_books = len(ordered_books)
    total_chapters = sum(len(b.chapters) for b in ordered_books)
    total_verses = sum(len(vs) for b in ordered_books for vs in b.chapters.values())

    meta: Dict[str, Any] = {
        "code": ctx.code,
        "language": ctx.language,
        "source": {
            "raw_dir": str(ctx.raw_dir),
            "usfm_zip": ctx.usfm_zip_path.name,
        },
        "counts": {
            "books": total_books,
            "chapters": total_chapters,
            "verses": total_verses,
        },
    }

    return ordered_books, meta


# Minimal canonical order (66 + some common Apocrypha; extend as needed)
CANONICAL_ORDER: Dict[str, int] = {
    # OT
    "GEN": 10, "EXO": 20, "LEV": 30, "NUM": 40, "DEU": 50,
    "JOS": 60, "JDG": 70, "RUT": 80,
    "1SA": 90, "2SA": 100,
    "1KI": 110, "2KI": 120,
    "1CH": 130, "2CH": 140,
    "EZR": 150, "NEH": 160, "EST": 170,
    "JOB": 180, "PSA": 190, "PRO": 200, "ECC": 210, "SNG": 220,
    "ISA": 230, "JER": 240, "LAM": 250, "EZK": 260, "DAN": 270,
    "HOS": 280, "JOL": 290, "AMO": 300, "OBA": 310, "JON": 320,
    "MIC": 330, "NAM": 340, "HAB": 350, "ZEP": 360, "HAG": 370,
    "ZEC": 380, "MAL": 390,
    # NT
    "MAT": 400, "MRK": 410, "LUK": 420, "JHN": 430, "ACT": 440,
    "ROM": 450, "1CO": 460, "2CO": 470, "GAL": 480,
    "EPH": 490, "PHP": 500, "COL": 510,
    "1TH": 520, "2TH": 530,
    "1TI": 540, "2TI": 550, "TIT": 560, "PHM": 570,
    "HEB": 580, "JAS": 590,
    "1PE": 600, "2PE": 610,
    "1JN": 620, "2JN": 630, "3JN": 640,
    "JUD": 650, "REV": 660,
    # Common Apocrypha (rough order; tweak if needed)
    "TOB": 700, "JDT": 710, "ESG": 720, "WIS": 730, "SIR": 740,
    "BAR": 750, "LJE": 760, "S3Y": 770, "SUS": 780, "BEL": 790,
    "1MA": 800, "2MA": 810, "3MA": 820, "4MA": 830,
    "1ES": 840, "2ES": 850, "MAN": 860, "PS2": 870,
}
