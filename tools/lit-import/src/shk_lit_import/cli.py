import argparse, pathlib, json
from shk_lit_import.fetchers.http import fetch_to
from shk_lit_import.parsers import bible_osis_plain, bible_osis_plus_strongs, strongs_xml, general_plain
from shk_lit_import.exporters import bible_per_book, lexicon_az, general_single
from shk_lit_import.utils.fs import ensure_dir, write_json
from shk_lit_import.utils.jsonio import write_jsonl

def load_spec(path: str):
    p = pathlib.Path(path); return json.loads(p.read_text(encoding='utf-8'))

def main():
    parser = argparse.ArgumentParser(prog='shk-lit', description='SHK literature import tool')
    parser.add_argument('--spec', required=True, help='Path to a corpus spec JSON')
    sub = parser.add_subparsers(dest='cmd', required=True)

    sub.add_parser('fetch')
    sub.add_parser('normalize')
    sub.add_parser('index')
    p_export = sub.add_parser('export-pages')
    p_export.add_argument('--out', default='../../docs/data/v1', help='API root override')

    args = parser.parse_args()
    spec = load_spec(args.spec)
    corpus = spec.get('corpus_id','corpus').replace(':','_')
    raw_root = pathlib.Path('data/raw') / corpus
    proc_root = pathlib.Path('data/processed') / corpus

    if args.cmd == 'fetch':
        fetch_to(raw_root, spec)

    elif args.cmd == 'normalize':
        proc_root.mkdir(parents=True, exist_ok=True)
        if spec['type'] == 'bible' and spec.get('mode') == 'plain':
            recs, meta = bible_osis_plain.parse_to_tokens([], spec)
            write_jsonl(proc_root / 'tokens.jsonl', recs)
            write_json(proc_root / 'verses.meta.json', meta)
        elif spec['type'] == 'bible' and spec.get('mode') == 'plus-strongs':
            recs, meta = bible_osis_plus_strongs.parse_to_tokens([], spec)
            write_jsonl(proc_root / 'tokens.jsonl', recs)
            write_json(proc_root / 'verses.meta.json', meta)
        elif spec['type'] == 'lexicon':
            entries = strongs_xml.parse_to_entries([], spec)
            write_jsonl(proc_root / 'lexicon.jsonl', entries)
        elif spec['type'] == 'general':
            segs, meta = general_plain.parse_to_segments([], spec)
            write_jsonl(proc_root / 'segments.jsonl', segs)
            write_json(proc_root / 'meta.json', meta)
        print(f"[normalize] Wrote processed placeholders under {proc_root}")

    elif args.cmd == 'index':
        ensure_dir(proc_root / 'indexes')
        (proc_root / 'indexes' / 'placeholder.json').write_text('{}', encoding='utf-8')
        print(f"[index] Created placeholder index under {proc_root/'indexes'}")

    elif args.cmd == 'export-pages':
        api_root = pathlib.Path(args.out)
        if spec['type'] == 'bible':
            meta = json.loads((proc_root / 'verses.meta.json').read_text(encoding='utf-8')) if (proc_root / 'verses.meta.json').exists() else {'books': []}
            bible_per_book.export(spec, proc_root, api_root, meta)
        elif spec['type'] == 'lexicon':
            entries_count = sum(1 for _ in (proc_root / 'lexicon.jsonl').open('r', encoding='utf-8')) if (proc_root / 'lexicon.jsonl').exists() else 0
            lexicon_az.export(spec, proc_root, api_root, entries_count)
        elif spec['type'] == 'general':
            meta = json.loads((proc_root / 'meta.json').read_text(encoding='utf-8')) if (proc_root / 'meta.json').exists() else {'segments': 0}
            general_single.export(spec, proc_root, api_root, meta)
        print(f"[export-pages] Wrote placeholders to {api_root}")
