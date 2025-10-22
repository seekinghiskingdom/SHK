import json, pathlib, os

# Build simple placeholder indexes and export small page shards

def run(in_dir: str, out_dir: str):
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "indexes").mkdir(exist_ok=True)
    (out / "indexes" / "by_strongs.json").write_text("{}", encoding="utf-8")
    (out / "indexes" / "by_verse.json").write_text("{}", encoding="utf-8")
    print(f"[index] Wrote placeholder indexes to {out/'indexes'}")

def export_pages(in_dir: str, out_dir: str):
    out = pathlib.Path(out_dir)
    (out / "strongs").mkdir(parents=True, exist_ok=True)
    (out / "kjv" / "verses").mkdir(parents=True, exist_ok=True)

    # minimal placeholder sharded files
    (out / "strongs" / "index.json").write_text('{"version":"v1","count":0}', encoding="utf-8")
    (out / "kjv" / "meta.json").write_text('{"version":"v1","books":[]}', encoding="utf-8")
    print(f"[export-pages] Created shard folders at {out}")
