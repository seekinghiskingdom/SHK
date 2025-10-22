import json, pathlib

# TARGET OUTPUT (example): data/processed/strongs.lexicon.jsonl
# Each line: { "id": "G3056", "lang": "grc", "lemma": "λόγος", "translit": "logos",
#              "gloss_short": "...", "gloss_long": "...", "search": {"ascii": "logos","strip": "λογος"} }

def run(raw_dir: str, out_dir: str):
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "strongs.lexicon.jsonl").write_text("", encoding="utf-8")
    print(f"[normalize/strongs] Created placeholder {out/'strongs.lexicon.jsonl'}")
