# tools/lit-import/helper_scripts/bible_plaintext_pass.py
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[3]
BIBLE_BASE = ROOT / "docs" / "data" / "v1" / "lit" / "bible"

# crude but effective USFM-ish cleaners
WORD_TAG_RE = re.compile(r"""\\\+?w\s+([^|\\]+)\|[^\\]*?\\w\*""")
FOOTNOTE_RE = re.compile(r"""\\f\s+.*?\\f\*""", re.DOTALL)
CROSSREF_RE = re.compile(r"""\\x\s+.*?\\x\*""", re.DOTALL)
GENERIC_MARKER_RE = re.compile(r"""\\[a-zA-Z0-9*]+\s?""")

def strip_usfm_markup(text: str) -> str:
    if not text:
        return text

    # replace \w ... |... \w* and \+w ... |... \w* with just the word
    text = WORD_TAG_RE.sub(r"\1", text)

    # drop footnotes and cross-references blocks entirely
    text = FOOTNOTE_RE.sub("", text)
    text = CROSSREF_RE.sub("", text)

    # remove bare markers like \sc, \it, \p, etc. (but leave the words)
    text = GENERIC_MARKER_RE.sub("", text)

    # normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def save_json(path: Path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

def process_translation(lang_dir: Path, code_dir: Path):
    lang = lang_dir.name
    code = code_dir.name
    label = f"{lang}/{code}"

    # skip Strong's-aware KJV+
    if lang == "en" and code == "kjv_strongs":
        print(f"[{label}] SKIP (Strong's-aware)")
        return

    chapters_dir = code_dir / "chapters"
    if not chapters_dir.exists():
        print(f"[{label}] no chapters/ dir, skipping")
        return

    total_chapters = 0
    total_verses = 0

    for book_dir in sorted(p for p in chapters_dir.iterdir() if p.is_dir()):
        for chapter_file in sorted(book_dir.glob("*.json")):
            chapter = load_json(chapter_file)
            changed = False
            for v in chapter.get("verses", []):
                t = v.get("text", "")
                new_t = strip_usfm_markup(t)
                if new_t != t:
                    v["text"] = new_t
                    changed = True
                total_verses += 1
            if changed:
                save_json(chapter_file, chapter)
            total_chapters += 1

    print(f"[{label}] processed chapters={total_chapters}, verses~={total_verses}")

def main():
    print(f"Base: {BIBLE_BASE}")
    for lang_dir in sorted(p for p in BIBLE_BASE.iterdir() if p.is_dir()):
        for code_dir in sorted(p for p in lang_dir.iterdir() if p.is_dir()):
            process_translation(lang_dir, code_dir)

if __name__ == "__main__":
    main()
