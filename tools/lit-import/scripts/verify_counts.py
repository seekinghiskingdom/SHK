
from pathlib import Path
import json
from collections import defaultdict

REPO_ROOT = Path(r"C:\Users\hrbncv\SHK\SHK").resolve()
BASE = REPO_ROOT / "docs/data/v1/lit/bible/en"

SETS = ["kjv","kjv_strongs","asv","web"]

def count_book(book_path: Path):
    data = json.loads(book_path.read_text(encoding="utf-8"))
    chapters = data.get("chapters", {})
    return sum(len(ch) for ch in chapters.values())

def main():
    totals = {}
    per_book = defaultdict(dict)
    for s in SETS:
        folder = BASE / s
        if not folder.exists():
            totals[s] = 0
            continue
        books = sorted([p for p in folder.glob("*.json") if p.name.lower() != "manifest.json"])
        totals[s] = 0
        for p in books:
            v = count_book(p)
            per_book[s][p.stem] = v
            totals[s] += v
    print("Totals:", json.dumps(totals, indent=2))
    # Optional: write a CSV of counts per book per set
    rows = []
    all_books = sorted({b for s in per_book.values() for b in s.keys()})
    header = ["BOOK"] + SETS
    rows.append(",".join(header))
    for b in all_books:
        row = [b] + [str(per_book[s].get(b,"")) for s in SETS]
        rows.append(",".join(row))
    out = REPO_ROOT / "docs/data/v1/lit/bible/verse_counts.csv"
    out.write_text("\n".join(rows), encoding="utf-8")
    print("Wrote", out)

if __name__ == "__main__":
    main()
