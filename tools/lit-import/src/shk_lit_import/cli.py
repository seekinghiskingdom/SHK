import argparse
from . import fetch, parse_strongs, parse_kjv, build_indexes, manifest

def main():
    parser = argparse.ArgumentParser(prog="shk-lit", description="SHK literature import tool")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_fetch = sub.add_parser("fetch", help="Download raw sources (local only)")
    p_fetch.add_argument("--out", default="data/raw", help="Output folder for raw downloads")

    p_norm = sub.add_parser("normalize", help="Parse & normalize sources")
    p_norm.add_argument("--in-raw", default="data/raw", help="Folder with raw sources")
    p_norm.add_argument("--out", default="data/processed", help="Output folder for normalized artifacts")

    p_index = sub.add_parser("index", help="Build crosswalks and frequency tables")
    p_index.add_argument("--in-proc", default="data/processed", help="Processed input folder")
    p_index.add_argument("--out", default="data/processed", help="Output folder (indexes)")

    p_export = sub.add_parser("export-pages", help="Export small JSON shards for GH Pages")
    p_export.add_argument("--in-proc", default="data/processed", help="Processed input folder")
    p_export.add_argument("--out", required=True, help="Output folder (e.g., ../../docs/data/v1)")

    p_release = sub.add_parser("release-bundle", help="Create heavy artifact bundle + manifest")
    p_release.add_argument("--in-proc", default="data/processed", help="Processed input folder")
    p_release.add_argument("--out", default="dist", help="Output folder for zip + manifest")

    args = parser.parse_args()

    if args.cmd == "fetch":
        fetch.run(args.out)
    elif args.cmd == "normalize":
        parse_strongs.run(args.in_raw, args.out)
        parse_kjv.run(args.in_raw, args.out)
    elif args.cmd == "index":
        build_indexes.run(args.in_proc, args.out)
    elif args.cmd == "export-pages":
        build_indexes.export_pages(args.in_proc, args.out)
    elif args.cmd == "release-bundle":
        manifest.bundle(args.in_proc, args.out)
