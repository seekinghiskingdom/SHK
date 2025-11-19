import pathlib

def fetch_to(raw_root: pathlib.Path, spec: dict):
    raw_root.mkdir(parents=True, exist_ok=True)
    (raw_root/ 'source.placeholder').write_text('placeholder', encoding='utf-8')
    return [raw_root/'source.placeholder']
