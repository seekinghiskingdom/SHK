# tools/lit-import/helper_scripts/historical_check.py
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[3]
HIST_ROOT = ROOT / "docs" / "data" / "v1" / "lit" / "historical"

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def main():
    if not HIST_ROOT.exists():
        print(f"Historical root not found at {HIST_ROOT}")
        return

    print(f"Checking historical works under {HIST_ROOT}...\n")

    total_works = 0
    issues = []

    # Look for any manifest.json under lit/historical/*
    for mpath in HIST_ROOT.rglob("manifest.json"):
        work_dir = mpath.parent
        rel = work_dir.relative_to(HIST_ROOT)
        total_works += 1

        m = load_json(mpath)
        files = m.get("files", {})
        work_issues = []

        if not files:
            work_issues.append("manifest.files is empty or missing")

        for key, fname in files.items():
            fpath = work_dir / fname
            if not fpath.exists():
                work_issues.append(f"missing file for '{key}': {fname}")

        if work_issues:
            issues.append((str(rel), work_issues))
            print(f"[{rel}] ISSUES:")
            for i in work_issues:
                print("  -", i)
        else:
            print(f"[{rel}] OK")

    print(f"\nSummary: {total_works} work(s) checked")
    if issues:
        print(f"{len(issues)} work(s) with issues")
    else:
        print("no issues found")

if __name__ == "__main__":
    main()
