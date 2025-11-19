# tools/pps/scripts/build.py
from __future__ import annotations
import argparse, json, os, shutil, sys
from datetime import datetime, timezone

from .schema import Bundle
from .loaders import load_csv, discover_trans_ids, load_bibles
from .assemble import build_entries
# from .indexer import build_indexs
from . import indexer
from .writer import make_bundle, write_json, write_gzip
from .id_utils import ref_string

# ---- default config (can be overridden by CLI flags) ----
DEFAULT_TRANS = "kjv"          # must match your translation folder name
SCHEMA_VERSION = 1

def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def _bundle_version_auto() -> str:
    # yyyy.mm.dd.hhmmss (UTC)
    t = datetime.now(timezone.utc)
    return t.strftime("%Y.%m.%d.%H%M%S")

def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Build PPS pairs bundle (entries + index).")
    p.add_argument("--pairs", required=True, help="Path to pairs.csv")
    p.add_argument("--bible-root", required=False, default=None,
                   help="Root to translations (e.g., docs/data/v1/lit/bible/en)")
    p.add_argument("--trans", default=DEFAULT_TRANS, help="Default translation id (e.g., kjv)")
    p.add_argument("--trans-ids", default="auto",
               help="'auto' to discover all under --bible-root, or a comma list like 'kjv,asv,web'")
    p.add_argument("--out", required=True, help="Output JSON path (e.g., tools/.../output/shk_pairs.json)")
    p.add_argument("--bundle-version", default="auto", help="Bundle version string or 'auto'")
    p.add_argument("--built-at", default=None, help="ISO timestamp or omitted for now")
    p.add_argument("--gzip", action="store_true", help="Also write a .gz next to the JSON")
    p.add_argument("--publish-dir", default=None, help="Optional folder to copy final JSON (e.g., docs/data)")
    p.add_argument("--pretty", action="store_true", help="Write pretty-printed JSON (for debugging)")
    # dev flags (override assemble/indexer defaults)
    # optional trans meta file
    p.add_argument("--trans-meta", default=None, help="Path to translations.json to embed minimal metadata")
    return p.parse_args(argv)

def main(argv=None) -> int:
    args = parse_args(argv)
    pairs_csv = args.pairs
    out_json  = args.out
    trans_id  = args.trans
    bible_root = args.bible_root
    bundle_version = _bundle_version_auto() if args.bundle_version == "auto" else args.bundle_version
    built_at = args.built_at or _iso_now()

    # --- Load authoring rows ---
    rows = load_csv(pairs_csv)
    if not rows:
        print("ERROR: no rows found in CSV", file=sys.stderr)
        return 2

    # Determine which translations to load
    # precedence: CLI --trans-ids → config.TRANS_IDS → auto
    trans_ids = None
    if args.trans_ids and args.trans_ids != "auto":
        trans_ids = [t.strip() for t in args.trans_ids.split(",") if t.strip()]
    else:
        try:
            from . import config
            cfg = getattr(config, "TRANS_IDS", "auto")
            if cfg == "auto":
                ex = getattr(config, "EXCLUDE_TRANS", [])
                trans_ids = discover_trans_ids(bible_root, ex)
            else:
                trans_ids = list(cfg)
        except Exception:
            trans_ids = discover_trans_ids(bible_root, [])

    if not trans_ids:
        print("ERROR: no translations discovered/selected.", file=sys.stderr)
        return 3


    # After computing trans_ids (and before load_bibles)
    # 1) Guard: default must not be excluded/absent
    if args.trans not in trans_ids:
        print(f"ERROR: default trans '{args.trans}' not in discovered set: {trans_ids}", file=sys.stderr)
        return 3

    # 2) Optional: show excluded ids (useful when TRANS_IDS='auto')
    try:
        from . import config
        excluded = set(getattr(config, "EXCLUDE_TRANS", []))
    except Exception:
        excluded = set()
    if excluded:
        print(f"Excluded translations: {', '.join(sorted(excluded))}")


    # Load all selected translations
    try:
        bibles_by_trans = load_bibles(bible_root, trans_ids)
    except Exception as e:
        print(f"ERROR: failed loading translations {trans_ids}: {e}", file=sys.stderr)
        return 3

    # Ensure the chosen default (--trans) is one we loaded
    if trans_id not in bibles_by_trans:
        print(f"ERROR: default trans '{trans_id}' not among loaded {trans_ids}", file=sys.stderr)
        return 3

    print(f"Loaded translations: {', '.join(trans_ids)} (default: {trans_id})")

    # --- Build entries ---
    entries = build_entries(rows, bibles_by_trans=bibles_by_trans, default_trans=trans_id)
    # small log
    print(f"Built {len(entries)} entries with {sum(len(e.pairs) for e in entries)} total pairs.")

    # --- Build index (active pairs only) ---
    index = indexer.build_index(entries, include_deprecated=False)
    print(f"Indexed X keys: {len(index['x'])} | Y keys: {len(index['y'])}")

    # --- Minimal translation metadata ---
    trans_meta = { tid: {"id": tid} for tid in bibles_by_trans.keys() }
    if args.trans_meta and os.path.isfile(args.trans_meta):
        try:
            with open(args.trans_meta, "r", encoding="utf-8") as f:
                meta_all = json.load(f)
            # if your translations.json is a list of objects with 'id', extract the matching one
            if isinstance(meta_all, list):
                for t in meta_all:
                    if t.get("id") == trans_id:
                        trans_meta[trans_id] = t
                        break
            elif isinstance(meta_all, dict):
                # support meta keyed by id
                trans_meta[trans_id] = meta_all.get(trans_id, trans_meta[trans_id])
        except Exception as e:
            print(f"WARN: could not read trans-meta: {e}")

    # --- Make bundle + write JSON ---
    bundle: Bundle = make_bundle(
        schema_version=SCHEMA_VERSION,
        bundle_version=bundle_version,
        default_trans=trans_id,
        trans_meta=trans_meta,
        entries=entries,
        index=index,
        built_at=built_at,
    )
    write_json(bundle, out_json, pretty=args.pretty)
    print(f"Wrote bundle: {out_json}")

    # --- Optional gzip ---
    if args.gzip:
        from .writer import write_gzip
        gz = write_gzip(out_json)
        print(f"Wrote gzip: {gz}")

    # --- Optional publish copy ---
    if args.publish_dir:
        os.makedirs(args.publish_dir, exist_ok=True)
        dest = os.path.join(args.publish_dir, os.path.basename(out_json))
        shutil.copy2(out_json, dest)
        print(f"Copied to publish dir: {dest}")

    # Final stats
    print("Stats:",
          f"entries={len(entries)}",
          f"pairs={sum(len(e.pairs) for e in entries)}",
          f"active={sum(sum(1 for p in e.pairs if p.status=='active') for e in entries)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
