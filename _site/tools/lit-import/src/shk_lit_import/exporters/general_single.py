from ..utils.fs import ensure_dir, write_json
import pathlib

def export(spec, processed_root: pathlib.Path, api_root: pathlib.Path, meta: dict):
    target = api_root / spec['export']['path_template']
    ensure_dir(target.parent)
    write_json(target, {'version':'v1','segments': meta.get('segments', 0)})
    return target
