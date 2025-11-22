import json
import os
from pathlib import Path
from collections import Counter

BASE = Path("docs/data/v1/lit/bible")

def load_json(p: Path):
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)

def scan_translation(lang_dir: Path, code_dir: Path):
    lang = lang_dir.name
    code = code_dir.name
    root = code_dir

    manifest = root / "manifest.json"
    meta = root / "meta.json"
    books = root / "books.json"
    chapters_dir = root / "chapters"

    issues = []

    # Required files/folders
    if not manifest.exists():
        issues.append("MISSING manifest.json")
    if not meta.exists():
        issues.append("MISSING meta.json")
    if not books.exists():
        issues.append("MISSING books.json")
    if not chapters_dir.exists():
        issues.append("MISSING chapters/ directory")

    # If core files exist, do deeper checks
    verses_count = None
    chapters_count = None
    meta_counts = None
    raw_dir = None

    if meta.exists():
        m = load_json(meta)
        meta_counts = m.get("counts", {})
        raw_dir = m.get("source", {}).get("raw_dir")
        # warn on absolute/raw Windows paths
        if isinstance(raw_dir, str) and (":" in raw_dir or raw_dir.startswith("\\")):
            issues.append(f"raw_dir looks machine-specific: {raw_dir}")

    if books.exists() and chapters_dir.exists():
        bj = load_json(books)
        # support both {"order":[...],"names":{...}} and simple list
        book_ids = bj["order"] if isinstance(bj, dict) and "order" in bj else [b["id"] for b in bj]
        missing_book_dirs = [b for b in book_ids if not (chapters_dir / b).exists()]
        if missing_book_dirs:
            issues.append(f"Missing chapter dir(s) for books: {missing_book_dirs}")

        # count chapters and verses
        chapters_count = 0
        verses_count = 0
        for b in book_ids:
            bdir = chapters_dir / b
            if not bdir.exists():
                continue
            for fname in sorted(bdir.glob("*.json")):
                chapters_count += 1
                cj = load_json(fname)
                verses = cj.get("verses", [])
                verses_count += len(verses)

    # Compare counts
    if meta_counts and chapters_count is not None:
        if meta_counts.get("chapters") != chapters_count:
            issues.append(f"chapter count mismatch: meta={meta_counts.get('chapters')} actual={chapters_count}")
        if meta_counts.get("verses") != verses_count:
            issues.append(f"verse count mismatch: meta={meta_counts.get('verses')} actual={verses_count}")

    return {
        "lang": lang,
        "code": code,
        "has_manifest": manifest.exists(),
        "has_meta": meta.exists(),
        "has_books": books.exists(),
        "has_chapters_dir": chapters_dir.exists(),
        "meta_counts": meta_counts,
        "actual_chapters": chapters_count,
        "actual_verses": verses_count,
        "raw_dir": raw_dir,
        "issues": issues,
    }

def main():
    summaries = []
    for lang_dir in sorted([p for p in BASE.iterdir() if p.is_dir()]):
        for code_dir in sorted([p for p in lang_dir.iterdir() if p.is_dir()]):
            summaries.append(scan_translation(lang_dir, code_dir))

    # Print a compact report
    for s in summaries:
        flag = "OK" if not s["issues"] else "ISSUES"
        print(f"{s['lang']}/{s['code']}: {flag}")
        for issue in s["issues"]:
            print(f"  - {issue}")
    print("\nTotals:")
    print("  translations:", len(summaries))

if __name__ == "__main__":
    main()
