#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional, List, Dict, Any


def find_repo_root() -> Path:
    # This file lives at <repo_root>/tools/lit-import/check_imports.py
    here = Path(__file__).resolve()
    return here.parents[2]


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def count_chapters_and_verses(chapters_path: Path) -> Dict[str, int]:
    chapters = 0
    verses = 0
    with chapters_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            chapters += 1
            verses += len(obj.get("verses", []))
    return {"chapters": chapters, "verses": verses}


def check_translation(root: Path, lang: str, code: str) -> bool:
    t_root = root / "bible" / lang / code
    books_path = t_root / "books.json"
    chapters_path = t_root / "chapters.jsonl"
    meta_path = t_root / "meta.json"

    ok = True
    missing = []

    for p in (books_path, chapters_path, meta_path):
        if not p.exists():
            missing.append(p.name)

    if missing:
        print(f"[{lang}/{code}] MISSING: {', '.join(missing)}")
        return False

    # load and sanity-check
    books = load_json(books_path)
    meta = load_json(meta_path)

    order = books.get("order", [])
    names = books.get("names", {})

    if not isinstance(order, list) or not isinstance(names, dict):
        print(f"[{lang}/{code}] books.json shape looks wrong")
        ok = False

    # recompute chapter/verse counts
    counts = count_chapters_and_verses(chapters_path)

    meta_counts = meta.get("counts", {})
    mb = meta_counts.get("books")
    mc = meta_counts.get("chapters")
    mv = meta_counts.get("verses")

    if mb is not None and mb != len(order):
        print(f"[{lang}/{code}] book count mismatch: meta={mb}, actual={len(order)}")
        ok = False
    if mc is not None and mc != counts["chapters"]:
        print(f"[{lang}/{code}] chapter count mismatch: meta={mc}, actual={counts['chapters']}")
        ok = False
    if mv is not None and mv != counts["verses"]:
        print(f"[{lang}/{code}] verse count mismatch: meta={mv}, actual={counts['verses']}")
        ok = False

    if ok:
        print(f"[{lang}/{code}] OK (books={len(order)}, chapters={counts['chapters']}, verses={counts['verses']})")
    return ok


def main(argv: Optional[List[str]] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="shk-lit-check")
    parser.add_argument("--lang", choices=["en", "grc", "he"], help="Filter by language")
    parser.add_argument("--code", nargs="+", help="Filter by one or more codes (e.g. kjv asv grctr)")
    args = parser.parse_args(argv)

    repo_root = find_repo_root()
    docs_lit_root = repo_root / "docs" / "data" / "v1" / "lit"

    # discover all translations present under docs/data/v1/lit/bible
    bible_root = docs_lit_root / "bible"
    langs = [p.name for p in bible_root.iterdir() if p.is_dir()]
    results: List[bool] = []

    for lang in sorted(langs):
        if args.lang and lang != args.lang:
            continue
        for code_dir in sorted((bible_root / lang).iterdir()):
            if not code_dir.is_dir():
                continue
            code = code_dir.name
            if args.code and code not in args.code:
                continue
            results.append(check_translation(docs_lit_root, lang, code))

    if not results:
        print("No translations matched filters / nothing to check.")
        return 1

    if all(results):
        print("All checked translations OK.")
        return 0
    else:
        print("Some translations had problems; see messages above.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
