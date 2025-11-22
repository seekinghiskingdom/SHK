#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def find_repo_root() -> Path:
    # tools/lit-import/split_chapters.py -> repo root
    here = Path(__file__).resolve()
    return here.parents[2]


def split_for_translation(
    base_dir: Path,
    lang: str,
    code: str,
    force: bool = False,
) -> None:
    t_dir = base_dir / lang / code
    chapters_jsonl = t_dir / "chapters.jsonl"

    if not chapters_jsonl.exists():
        print(f"[{lang}/{code}] SKIP: no chapters.jsonl at {chapters_jsonl}")
        return

    out_root = t_dir / "chapters"
    out_root.mkdir(parents=True, exist_ok=True)

    written = 0
    with chapters_jsonl.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                raise RuntimeError(
                    f"[{lang}/{code}] JSON error on line {line_no} of {chapters_jsonl}: {e}"
                )

            book_id = obj.get("book_id")
            chapter = obj.get("chapter")

            if not book_id or not isinstance(chapter, int):
                raise ValueError(
                    f"[{lang}/{code}] invalid chapter object on line {line_no}: "
                    f"missing book_id or integer chapter"
                )

            out_dir = out_root / book_id
            out_dir.mkdir(parents=True, exist_ok=True)

            out_path = out_dir / f"{chapter:03d}.json"
            if out_path.exists() and not force:
                # already split; leave as-is
                continue

            with out_path.open("w", encoding="utf-8") as out_f:
                # write exactly the same object that was in chapters.jsonl
                json.dump(obj, out_f, ensure_ascii=False, indent=2)

            written += 1

    print(f"[{lang}/{code}] wrote {written} chapter file(s) under {out_root}")


def discover_translations(
    base_dir: Path,
    lang: str | None = None,
    code: str | None = None,
) -> list[tuple[str, str]]:
    """Find (lang, code) pairs under docs/data/v1/lit/bible/."""
    langs: list[str]
    if lang:
        langs = [lang]
    else:
        langs = [
            d.name for d in base_dir.iterdir()
            if d.is_dir()
        ]

    result: list[tuple[str, str]] = []
    for lg in sorted(langs):
        lang_dir = base_dir / lg
        if not lang_dir.is_dir():
            continue
        if code:
            codes = [code]
        else:
            codes = [
                d.name for d in lang_dir.iterdir()
                if d.is_dir()
            ]
        for cd in sorted(codes):
            t_dir = lang_dir / cd
            if (t_dir / "chapters.jsonl").exists():
                result.append((lg, cd))

    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Split chapters.jsonl into per-book/per-chapter JSON files."
    )
    parser.add_argument(
        "--lang",
        help="Language code to filter (e.g., en, grc, he). If omitted, process all languages.",
    )
    parser.add_argument(
        "--code",
        help="Translation code to filter (e.g., kjv, web). If omitted, process all codes for the language(s).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing per-chapter files if they already exist.",
    )
    args = parser.parse_args()

    repo_root = find_repo_root()
    bible_dir = repo_root / "docs" / "data" / "v1" / "lit" / "bible"

    translations = discover_translations(
        base_dir=bible_dir,
        lang=args.lang,
        code=args.code,
    )

    if not translations:
        print("No matching translations found (check --lang/--code and chapters.jsonl presence).")
        return

    for lang, code in translations:
        split_for_translation(
            base_dir=bible_dir,
            lang=lang,
            code=code,
            force=args.force,
        )


if __name__ == "__main__":
    main()
