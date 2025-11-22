from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[3]
V1_ROOT = ROOT / "docs" / "data" / "v1"

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def save_json(path: Path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

def ensure_source_block(data):
    src = data.get("source")
    if not isinstance(src, dict):
        src = {}
    data["source"] = src
    return src

def fill_bible_sources():
    bible_root = V1_ROOT / "lit" / "bible"
    updated = 0
    for meta_path in bible_root.rglob("meta.json"):
        rel = meta_path.relative_to(V1_ROOT)
        data = load_json(meta_path)
        src = ensure_source_block(data)

        # derive lang/code from path: lit/bible/<lang>/<code>/meta.json
        parts = rel.parts  # ('lit', 'bible', lang, code, 'meta.json')
        if len(parts) < 5:
            continue
        lang = parts[2]
        code = parts[3]

        # provider and url: always eBible for v1
        src["provider"] = "eBible.org"
        src["url"] = "https://ebible.org"

        # raw_dir: keep existing if present, otherwise infer
        raw_dir = src.get("raw_dir")
        if not raw_dir:
            src["raw_dir"] = f"tools/lit-import/data/raw/bible/{lang}/{code}"

        # license: simple standardized note for v1
        src["license"] = src.get("license") or "Public domain / permissive license; see eBible.org"

        save_json(meta_path, data)
        updated += 1
    print(f"Bible meta.json updated: {updated}")

def fill_strongs_sources():
    strongs_root = V1_ROOT / "lit" / "strongs"
    updated = 0
    for meta_path in strongs_root.rglob("meta.json"):
        rel = meta_path.relative_to(V1_ROOT)
        data = load_json(meta_path)
        src = ensure_source_block(data)

        # derive lang from path: lit/strongs/<lang>/meta.json
        parts = rel.parts  # ('lit', 'strongs', lang, 'meta.json')
        if len(parts) < 4:
            continue
        lang = parts[2]

        src["provider"] = "Open Scriptures"
        src["url"] = "https://github.com/openscriptures/strongs"

        if not src.get("raw_dir"):
            src["raw_dir"] = f"tools/lit-import/data/raw/strongs/{lang}"

        # DO NOT overwrite license; keep whatever is there
        # if none exists, add a generic note
        if "license" not in src and "license_note" not in src:
            src["license"] = "See repository for license details"

        save_json(meta_path, data)
        updated += 1
    print(f"Strong's meta.json updated: {updated}")

def main():
    fill_bible_sources()
    fill_strongs_sources()

if __name__ == "__main__":
    main()
