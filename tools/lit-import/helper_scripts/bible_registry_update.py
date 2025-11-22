# tools/lit-import/helper_scripts/bible_registry_update.py
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[3]
BIBLE_BASE = ROOT / "docs" / "data" / "v1" / "lit" / "bible"
TRANSLATIONS_JSON = ROOT / "docs" / "data" / "v1" / "lit" / "bible" / "translations.json"

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def save_json(path: Path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

def update_manifests_and_collect():
    entries = []
    for lang_dir in sorted(p for p in BIBLE_BASE.iterdir() if p.is_dir()):
        for code_dir in sorted(p for p in lang_dir.iterdir() if p.is_dir()):
            manifest_path = code_dir / "manifest.json"
            meta_path = code_dir / "meta.json"
            if not manifest_path.exists() or not meta_path.exists():
                continue

            manifest = load_json(manifest_path)
            meta = load_json(meta_path)

            lang = lang_dir.name
            code = code_dir.name

            # 1) Force all Bible translations to available for v1.0
            manifest["status"] = "available"

            # 2) Set Strong's feature flag
            feats = manifest.get("features", {})
            if lang == "en" and code == "kjv_strongs":
                feats["has_strongs"] = True
            else:
                feats["has_strongs"] = False
            manifest["features"] = feats

            save_json(manifest_path, manifest)

            # 3) Collect entry for translations.json
            counts = meta.get("counts", {})
            entries.append({
                "code": code,
                "language": lang,
                "path": f"/data/v1/lit/bible/{lang}/{code}",
                "books": counts.get("books"),
                "chapters": counts.get("chapters"),
                "verses": counts.get("verses"),
            })

    return entries

def main():
    entries = update_manifests_and_collect()
    entries = sorted(entries, key=lambda e: (e["language"], e["code"]))
    save_json(TRANSLATIONS_JSON, entries)
    print(f"Wrote {len(entries)} entries to {TRANSLATIONS_JSON}")

if __name__ == "__main__":
    main()
