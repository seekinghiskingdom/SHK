# tools/lit-import/helper_scripts/historical_fix.py
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[3]
HIST_ROOT = ROOT / "docs" / "data" / "v1" / "lit" / "historical"

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def save_json(path: Path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

def main():
    if not HIST_ROOT.exists():
        print(f"Historical root not found at {HIST_ROOT}")
        return

    print(f"Fixing historical manifests under {HIST_ROOT}...\n")

    for mpath in HIST_ROOT.rglob("manifest.json"):
        work_dir = mpath.parent
        rel = work_dir.relative_to(HIST_ROOT)

        manifest = load_json(mpath)
        files = manifest.get("files", {})

        # If 'text' already points to an existing file, leave it alone
        text_name = files.get("text")
        if text_name and (work_dir / text_name).exists():
            print(f"[{rel}] text file already OK: {text_name}")
            continue

        # Otherwise, pick the first .txt file in this directory
        txt_files = sorted(work_dir.glob("*.txt"))
        if not txt_files:
            print(f"[{rel}] WARNING: no .txt files found; leaving manifest unchanged")
            continue

        chosen = txt_files[0].name
        files["text"] = chosen
        manifest["files"] = files
        save_json(mpath, manifest)
        print(f"[{rel}] set files.text = {chosen}")

    print("\nDone.")

if __name__ == "__main__":
    main()
