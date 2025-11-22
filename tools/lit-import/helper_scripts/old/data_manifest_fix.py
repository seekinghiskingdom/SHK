# tools/lit-import/helper_scripts/data_manifest_fix.py
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[3]
DATA_ROOT = ROOT / "docs" / "data" / "v1"
MANIFEST_PATH = DATA_ROOT / "manifest.json"

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def save_json(path: Path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

def filter_existing_paths(family_name, paths):
    kept = []
    removed = []
    for rel in paths:
        d = DATA_ROOT / rel
        m = d / "manifest.json"
        if d.exists() and m.exists():
            kept.append(rel)
        else:
            removed.append(rel)
    return kept, removed

def main():
    if not MANIFEST_PATH.exists():
        print(f"ERROR: manifest.json not found at {MANIFEST_PATH}")
        return

    manifest = load_json(MANIFEST_PATH)
    datasets = manifest.get("datasets", {})

    for family in ("bible", "tools"):
        info = datasets.get(family)
        if not info:
            continue
        paths = info.get("paths", [])
        kept, removed = filter_existing_paths(family, paths)
        info["paths"] = kept
        datasets[family] = info
        print(f"[{family}] kept {len(kept)} path(s), removed {len(removed)}:")
        for r in removed:
            print(f"  - {r}")

    manifest["datasets"] = datasets
    save_json(MANIFEST_PATH, manifest)
    print(f"\nUpdated {MANIFEST_PATH}")

if __name__ == "__main__":
    main()
