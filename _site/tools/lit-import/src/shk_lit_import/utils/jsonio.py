import json, pathlib

def write_jsonl(p: pathlib.Path, records):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('w', encoding='utf-8') as f:
        for r in records: f.write(json.dumps(r)+'\n')
