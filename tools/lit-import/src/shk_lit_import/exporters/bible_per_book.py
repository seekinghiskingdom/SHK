
from __future__ import annotations
import json, pathlib, collections
from ..utils.fs import ensure_dir, write_json
from ..utils.books import OSIS_TO_BK3

def _base_dir(api_root: pathlib.Path, tpl: str) -> pathlib.Path:
    assert '{BOOK}' in tpl, 'path_template must contain {BOOK}'
    return api_root / tpl.split('{BOOK}')[0]

def export(spec, processed_root: pathlib.Path, api_root: pathlib.Path, meta: dict):
    tpl = spec['export']['path_template']
    out_dir = _base_dir(api_root, tpl)
    ensure_dir(out_dir)

    token_path = processed_root / 'tokens.jsonl'
    by_book = collections.defaultdict(lambda: collections.defaultdict(list))

    if token_path.exists():
        with token_path.open('r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                osis_id = rec.get('verse', '')
                if '.' not in osis_id:
                    continue
                osis_book = osis_id.split('.', 1)[0]
                bk3 = OSIS_TO_BK3.get(osis_book)
                if not bk3:
                    continue
                by_book[bk3][osis_id].append({'idx': rec['idx'], 't': rec['t']})

    # Write per-book JSON files deterministically
    files_written = 0
    for bk3 in sorted(by_book.keys(), key=lambda x: x):
        verses = by_book[bk3]
        ordered = {k: sorted(v, key=lambda x: x['idx']) for k, v in sorted(verses.items())}
        write_json(out_dir / f'{bk3}.json', ordered)
        files_written += 1

    write_json(out_dir / 'manifest.json', {
        'version': 'v1',
        'books': meta.get('books', []),
        'token_count': meta.get('token_count', 0),
        'files_written': files_written
    })
    return out_dir
