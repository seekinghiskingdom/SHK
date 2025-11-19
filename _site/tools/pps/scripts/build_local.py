from tools.pps.scripts.build import main

def run():
    argv = [
        "--pairs", "tools/pps/data/input/pairs/pairs.csv",
        "--bible-root", "docs/data/v1/lit/bible/en",
        "--trans", "kjv",
        "--out", "tools/pps/data/output/shk_pairs.json",
        "--bundle-version", "auto",
        "--gzip",
        "--publish-dir", "docs/data/v1/tools/pps",
        "--ignore-synonyms",
    ]
    raise SystemExit(main(argv))

if __name__ == "__main__":
    run()
