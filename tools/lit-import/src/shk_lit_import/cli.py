import argparse
import json
from pathlib import Path

from shk_lit_import.fetchers.http import fetch_to
from shk_lit_import.parsers import (
    bible_osis_plain,
    bible_osis_plus_strongs,
    strongs_xml,
    general_plain,
)
from shk_lit_import.exporters import bible_per_book, lexicon_az, general_single
from shk_lit_import.utils.fs import ensure_dir, write_json
from shk_lit_import.utils.jsonio import write_jsonl


def load_spec(path: str) -> dict:
    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8"))

def discover_inputs(spec: dict) -> list[Path]:
    """Return a list of input files based on spec.source"""
    src = spec.get("source", {})
    mode = src.get("mode", "local")
    fmt = src.get("format", "")
    files: list[Path] = []

    if mode == "local":
        root = Path(src.get("local_path", "."))
        if fmt.endswith("xml"):
            files = sorted(root.rglob("*.xml"))
        else:
            # default to any files; narrow later if needed
            files = sorted(root.rglob("*"))
    elif mode == "http":
        # HTTP fetch puts files under data/raw; normalize() should then read from there
        pass
    return files


def main():
    parser = argparse.ArgumentParser(prog="shk-lit", description="SHK literature import tool")
    parser.add_argument("--spec", required=True, help="Path to a corpus spec JSON")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("fetch")
    sub.add_parser("normalize")
    sub.add_parser("index")
    p_export = sub.add_parser("export-pages")
    p_export.add_argument("--out", default="../../docs/data/v1", help="API root override")

    args = parser.parse_args()
    spec = load_spec(args.spec)

    corpus = spec.get("corpus_id", "corpus").replace(":", "_")
    raw_root = Path("data/raw") / corpus
    proc_root = Path("data/processed") / corpus

    if args.cmd == "fetch":
        fetch_to(raw_root, spec)

    elif args.cmd == "normalize":
        proc_root.mkdir(parents=True, exist_ok=True)
        inputs = discover_inputs(spec)

        if spec["type"] == "bible" and spec.get("mode") == "plain":
            recs, meta = bible_osis_plain.parse_to_tokens(inputs, spec)
            write_jsonl(proc_root / "tokens.jsonl", recs)
            write_json(proc_root / "verses.meta.json", meta)

        elif spec["type"] == "bible" and spec.get("mode") == "plus-strongs":
            recs, meta = bible_osis_plus_strongs.parse_to_tokens(inputs, spec)
            write_jsonl(proc_root / "tokens.jsonl", recs)
            write_json(proc_root / "verses.meta.json", meta)

        elif spec["type"] == "lexicon":
            entries = strongs_xml.parse_to_entries(inputs, spec)
            write_jsonl(proc_root / "lexicon.jsonl", entries)

        elif spec["type"] == "general":
            segs, meta = general_plain.parse_to_segments(inputs, spec)
            write_jsonl(proc_root / "segments.jsonl", segs)
            write_json(proc_root / "meta.json", meta)

        print(f"[normalize] Inputs={len(inputs)} → {proc_root}")

    elif args.cmd == "index":
        ensure_dir(proc_root / "indexes")
        (proc_root / "indexes" / "placeholder.json").write_text("{}", encoding="utf-8")
        print(f"[index] Created placeholder index under {proc_root/'indexes'}")

    elif args.cmd == "export-pages":
        api_root = Path(args.out)

        if spec["type"] == "bible":
            meta_path = proc_root / "verses.meta.json"
            meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {"books": []}
            bible_per_book.export(spec, proc_root, api_root, meta)

        elif spec["type"] == "lexicon":
            lex_path = proc_root / "lexicon.jsonl"
            entries_count = sum(1 for _ in lex_path.open("r", encoding="utf-8")) if lex_path.exists() else 0
            lexicon_az.export(spec, proc_root, api_root, entries_count)

        elif spec["type"] == "general":
            meta_path = proc_root / "meta.json"
            meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {"segments": 0}
            general_single.export(spec, proc_root, api_root, meta)

        print(f"[export-pages] Wrote pages to {api_root}")


if __name__ == "__main__":
    main()
