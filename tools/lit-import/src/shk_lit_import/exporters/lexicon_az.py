from ..utils.fs import ensure_dir, write_json
import pathlib

def export(spec, processed_root: pathlib.Path, api_root: pathlib.Path, entries_count: int):
    root = api_root / spec['export']['path_root']
    ensure_dir(root)
    write_json(root / 'index.json', {'version':'v1','count': entries_count, 'shards': []})
    return root
