import pathlib, json

def ensure_dir(p: pathlib.Path): p.mkdir(parents=True, exist_ok=True)

def write_json(p: pathlib.Path, obj): ensure_dir(p.parent); p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')
