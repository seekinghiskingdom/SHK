#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable, List, Dict, Any, Optional

from usfm_import import import_bible_from_raw_plan


def find_repo_root() -> Path:
    # This file lives at <repo_root>/tools/lit-import/cli.py
    here = Path(__file__).resolve()
    return here.parents[2]


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="shk-lit-import")
    subparsers = parser.add_subparsers(dest="command", required=True)

    bible_p = subparsers.add_parser("bible", help="Import Bible translations from raw USFM")
    bible_p.add_argument(
        "--lang",
        choices=["en", "grc", "he"],
        help="Limit to a single language (default: all found in plan).",
    )
    bible_p.add_argument(
        "--code",
        nargs="+",
        help="Limit to one or more specific translation codes (e.g. kjv asv grctr).",
    )
    bible_p.add_argument(
        "--group",
        help="Limit to a specific plan group id (e.g. v1_core_en).",
    )
    bible_p.add_argument(
        "--tier",
        choices=["must", "extra-B1", "extra-B2"],
        help="Limit to translations of a specific tier.",
    )
    bible_p.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing books.json/chapters.jsonl/meta.json if present.",
    )

    args = parser.parse_args(argv)

    repo_root = find_repo_root()
    lit_import_root = repo_root / "tools" / "lit-import"
    raw_root = lit_import_root / "data" / "raw"
    docs_lit_root = repo_root / "docs" / "data" / "v1" / "lit"

    if args.command == "bible":
        plan_path = raw_root / "bible" / "bible_plan.json"
        if not plan_path.is_file():
            print(f"ERROR: bible_plan.json not found at {plan_path}", file=sys.stderr)
            return 1

        with plan_path.open("r", encoding="utf-8") as f:
            plan = json.load(f)

        translations: Iterable[Dict[str, Any]] = plan.get("translations", [])
        filtered: List[Dict[str, Any]] = []

        for t in translations:
            if args.lang and t.get("language") != args.lang:
                continue
            if args.group and t.get("group") != args.group:
                continue
            if args.tier and t.get("tier") != args.tier:
                continue
            if args.code and t.get("code") not in args.code:
                continue
            filtered.append(t)

        if not filtered:
            print("No translations matched the given filters.", file=sys.stderr)
            return 1

        print(f"Importing {len(filtered)} translation(s)...")
        for t in filtered:
            code = t["code"]
            lang = t["language"]
            print(f"==> {lang}/{code} ({t.get('title', '')})")
            raw_dir = raw_root / "bible" / lang / code
            out_dir = docs_lit_root / "bible" / lang / code
            try:
                import_bible_from_raw_plan(
                    repo_root=repo_root,
                    raw_dir=raw_dir,
                    out_dir=out_dir,
                    force=args.force,
                )

            except Exception as e:
                print(f"ERROR importing {lang}/{code}: {e}", file=sys.stderr)
                return 1

        print("Done.")
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
