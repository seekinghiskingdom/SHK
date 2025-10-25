from ..utils.fs import ensure_dir, write_json
import pathlib

def export(spec, processed_root: pathlib.Path, api_root: pathlib.Path, meta: dict):
    tpl = spec['export']['path_template']
    base = tpl.split('{BOOK}')[0]
    out = api_root / base
    ensure_dir(out)
    write_json(out / 'manifest.json', {'version':'v1','books': meta.get('books', []), 'token_count': meta.get('token_count', 0)})
    return out
