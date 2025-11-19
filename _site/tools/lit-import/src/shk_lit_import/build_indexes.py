import json, pathlib

def run(in_dir: str, out_dir: str):
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "indexes").mkdir(exist_ok=True)
    (out / "indexes" / "by_strongs.json").write_text("{}", encoding="utf-8")
    (out / "indexes" / "by_verse.json").write_text("{}", encoding="utf-8")
    print(f"[index] Wrote placeholder indexes to {out/'indexes'}")

def export_pages(in_dir: str, api_root: str):
    root = pathlib.Path(api_root)

    # Ensure target directories exist (API v1 layout)
    (root / "lit" / "bible" / "en" / "kjv").mkdir(parents=True, exist_ok=True)
    (root / "lit" / "strongs").mkdir(parents=True, exist_ok=True)
    (root / "tools" / "scs").mkdir(parents=True, exist_ok=True)
    (root / "tools" / "pps").mkdir(parents=True, exist_ok=True)

    # Minimal placeholders to prove export works
    (root / "lit" / "strongs" / "index.json").write_text('{"version":"v1","count":0}', encoding="utf-8")
    (root / "tools" / "scs" / "index.json").write_text('{"uses":"lit/strongs"}', encoding="utf-8")
    (root / "tools" / "pps" / "index.json").write_text('{"entries":0}', encoding="utf-8")
    print(f"[export-pages] Initialized API shards at {root}")
