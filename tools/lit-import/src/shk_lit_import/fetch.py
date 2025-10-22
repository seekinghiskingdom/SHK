import os, pathlib

# TODO: add actual downloads (requests or urllib). Keep files out of git.
# Consider writing sha256 alongside each file and recording in DATA_SOURCES.md.

DUMMY_FILES = {
    "strongs.xml": "<strongs-xml-placeholder/>",
    "kjv_mapped.xml": "<osis-xml-placeholder/>"
}

def run(out_dir: str):
    p = pathlib.Path(out_dir)
    p.mkdir(parents=True, exist_ok=True)
    for name, content in DUMMY_FILES.items():
        (p / name).write_text(content, encoding="utf-8")
    print(f"[fetch] Wrote placeholder raw files to {p}")
