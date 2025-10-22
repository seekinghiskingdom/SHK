import json, pathlib

# TARGET OUTPUTS (examples):
# - data/processed/kjv.tokens.jsonl
# - data/processed/verses.meta.json
# token record: { "verse": "Gen.1.1", "idx": 0, "surface": "In", "strongs": [] }

def run(raw_dir: str, out_dir: str):
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "kjv.tokens.jsonl").write_text("", encoding="utf-8")
    (out / "verses.meta.json").write_text(json.dumps({"count": 0}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[normalize/kjv] Created placeholders in {out}")
