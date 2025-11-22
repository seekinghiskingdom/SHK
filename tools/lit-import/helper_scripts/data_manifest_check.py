# tools/lit-import/helper_scripts/data_manifest_check.py
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[3]
DATA_ROOT = ROOT / "docs" / "data" / "v1"
MANIFEST_PATH = DATA_ROOT / "manifest.json"

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def main():
    if not MANIFEST_PATH.exists():
        print(f"ERROR: manifest.json not found at {MANIFEST_PATH}")
        return

    manifest = load_json(MANIFEST_PATH)
    datasets = manifest.get("datasets", {})

    print(f"Checking dataset paths relative to {DATA_ROOT}...\n")

    total_paths = 0
    missing_dirs = []
    missing_manifests = []

    for family, info in datasets.items():
        paths = info.get("paths", [])
        print(f"[{family}]")
        for rel in paths:
            total_paths += 1
            d = DATA_ROOT / rel
            if not d.exists():
                missing_dirs.append(rel)
                print(f"  - MISSING DIR: {rel}")
                continue
            m_path = d / "manifest.json"
            if not m_path.exists():
                missing_manifests.append(rel)
                print(f"  - MISSING manifest.json in {rel}")
            else:
                print(f"  - OK: {rel}")
        print()

    print("Summary:")
    print(f"  total dataset paths: {total_paths}")
    print(f"  missing dirs: {len(missing_dirs)}")
    print(f"  missing manifests: {len(missing_manifests)}")

    if missing_dirs:
        print("\nMissing dirs:")
        for rel in missing_dirs:
            print("  -", rel)
    if missing_manifests:
        print("\nMissing manifest.json:")
        for rel in missing_manifests:
            print("  -", rel)

if __name__ == "__main__":
    main()
