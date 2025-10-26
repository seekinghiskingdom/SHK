
from pathlib import Path
import json

# Adjust if your repo root differs
REPO_ROOT = Path(r"C:\Users\hrbncv\SHK\SHK").resolve()
BASE = REPO_ROOT / "docs/data/v1/lit/bible/en"
OUT  = REPO_ROOT / "docs/data/v1/lit/bible/translations.json"

TRANSLATIONS = [
    {"id":"kjv",         "name":"King James Version",          "path":"kjv"},
    {"id":"kjv_strongs", "name":"KJV + Strong's (tokenized)",  "path":"kjv_strongs"},
    {"id":"asv",         "name":"American Standard Version",   "path":"asv"},
    {"id":"web",         "name":"World English Bible",         "path":"web"}
]

def count_verses(book_path: Path):
    try:
        data = json.loads(book_path.read_text(encoding="utf-8"))
    except Exception:
        return 0
    chapters = data.get("chapters", {})
    total = 0
    for ch in chapters.values():
        # Strong's verses are dicts with "tokens"; plain verses are strings
        # Either way, count number of verse keys
        total += len(ch)
    return total

def main():
    out = []
    for tr in TRANSLATIONS:
        folder = BASE / tr["path"]
        if not folder.exists():
            out.append({**tr, "books": 0, "verses": 0, "base_url": f"/data/v1/lit/bible/en/{tr['path']}"})
            continue
        books = sorted([p for p in folder.glob("*.json") if p.name.lower() != "manifest.json"])
        verses = sum(count_verses(p) for p in books)
        out.append({**tr, "books": len(books), "verses": verses, "base_url": f"/data/v1/lit/bible/en/{tr['path']}"})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Wrote", OUT)

if __name__ == "__main__":
    main()
