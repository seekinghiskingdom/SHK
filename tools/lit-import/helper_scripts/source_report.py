from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[3]
V1_ROOT = ROOT / "docs" / "data" / "v1"

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def main():
    print(f"Scanning meta.json files under {V1_ROOT}...\n")
    count = 0
    missing_source = []

    for meta_path in V1_ROOT.rglob("meta.json"):
        rel = meta_path.relative_to(V1_ROOT)
        data = load_json(meta_path)
        src = data.get("source")
        count += 1

        print(f"[{rel}]")
        if not src:
            print("  source: MISSING\n")
            missing_source.append(str(rel))
            continue

        provider = src.get("provider")
        url = src.get("url")
        raw_dir = src.get("raw_dir")
        license_ = src.get("license") or src.get("license_note")

        print(f"  provider: {provider}")
        print(f"  url:      {url}")
        print(f"  raw_dir:  {raw_dir}")
        print(f"  license:  {license_}\n")

    print(f"Total meta.json files: {count}")
    print(f"Missing source blocks: {len(missing_source)}")
    if missing_source:
        print("\nFiles missing source:")
        for rel in missing_source:
            print("  -", rel)

if __name__ == "__main__":
    main()
