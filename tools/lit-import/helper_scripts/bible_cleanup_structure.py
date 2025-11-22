# tools/lit-import/helper_scripts/bible_cleanup_structure.py
from pathlib import Path
import json

# Repo root = .../SHK, three levels up from this file
ROOT = Path(__file__).resolve().parents[3]
BIBLE_BASE = ROOT / "docs" / "data" / "v1" / "lit" / "bible"

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def save_json(path: Path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

def normalize_manifest(manifest_path: Path):
    m = load_json(manifest_path)

    files = m.get("files", {})
    files["books"] = "books.json"
    files["chapters_dir"] = "chapters/"
    files["meta"] = "meta.json"
    m["files"] = files

    # if status missing, leave as-is; otherwise keep whatever is there
    save_json(manifest_path, m)
    return m.get("id", f"{manifest_path.parent.name}")

def cleanup_translation(lang_dir: Path, code_dir: Path):
    lang = lang_dir.name
    code = code_dir.name
    root = code_dir

    manifest = root / "manifest.json"
    meta = root / "meta.json"
    books = root / "books.json"
    chapters_dir = root / "chapters"

    issues = []

    if not manifest.exists():
        issues.append("MISSING manifest.json")
    if not meta.exists():
        issues.append("MISSING meta.json")
    if not books.exists():
        issues.append("MISSING books.json")
    if not chapters_dir.exists():
        issues.append("MISSING chapters/")

    if manifest.exists():
        _ = normalize_manifest(manifest)

    # delete orphans: chapters.jsonl
    cj = root / "chapters.jsonl"
    if cj.exists():
        cj.unlink()
        print(f"[{lang}/{code}] removed chapters.jsonl")

    return issues

def main():
    print(f"Base: {BIBLE_BASE}")
    for lang_dir in sorted(p for p in BIBLE_BASE.iterdir() if p.is_dir()):
        for code_dir in sorted(p for p in lang_dir.iterdir() if p.is_dir()):
            issues = cleanup_translation(lang_dir, code_dir)
            label = f"{lang_dir.name}/{code_dir.name}"
            if issues:
                print(f"[{label}] issues:")
                for i in issues:
                    print("  -", i)
            else:
                print(f"[{label}] OK")

if __name__ == "__main__":
    main()
