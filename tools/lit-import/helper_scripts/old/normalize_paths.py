from pathlib import Path
import json

BASE = Path("docs/data/v1/lit/bible")

for lang_dir in BASE.iterdir():
    if not lang_dir.is_dir():
        continue
    for code_dir in lang_dir.iterdir():
        if not code_dir.is_dir():
            continue
        meta_path = code_dir / "meta.json"
        if not meta_path.exists():
            continue
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        src = meta.get("source", {})
        raw_dir = src.get("raw_dir")
        if not raw_dir:
            continue
        # Force canonical, repo-relative raw_dir
        src["raw_dir"] = f"tools/lit-import/data/raw/bible/{lang_dir.name}/{code_dir.name}"
        meta["source"] = src
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        print("Updated", meta_path)
