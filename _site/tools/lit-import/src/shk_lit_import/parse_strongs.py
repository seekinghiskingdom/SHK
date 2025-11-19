import json, pathlib

# Target: data/processed/strongs.lexicon.jsonl
def run(raw_dir: str, out_dir: str):
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "strongs.lexicon.jsonl").write_text("", encoding="utf-8")
    print(f"[normalize/strongs] Created placeholder {out/'strongs.lexicon.jsonl'}")
