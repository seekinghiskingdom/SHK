from pathlib import Path
from xml.etree import ElementTree as ET
import re, json
from collections import Counter, defaultdict

REPO_ROOT = Path(r"C:\Users\hrbncv\SHK\SHK").resolve()
USFX_DIR  = REPO_ROOT / "tools/lit-import/data/raw/kjv/eng-kjv_usfx"

def strip_ns(tag: str) -> str:
    return tag.split("}", 1)[-1]

tag_counts = Counter()
attr_keys_by_tag = defaultdict(Counter)
samples = {
    "verse_like": [],
    "word_with_strongs": [],
    "chapter_like": [],
    "book_like": [],
}

VERSE_ID_PAT = re.compile(r"[A-Za-z][A-Za-z0-9]+\s*[\.: ]\s*\d+\s*[\.: ]\s*\d+")
STRONGS_PAT  = re.compile(r"\b[HhGg]\d{1,5}\b")

files = sorted(USFX_DIR.rglob("*.xml"))
print(f"Scanning {len(files)} XML file(s) under: {USFX_DIR}")

def add_sample(bucket, info, limit=8):
    if len(samples[bucket]) < limit:
        samples[bucket].append(info)

for p in files:
    try:
        root = ET.parse(str(p)).getroot()
    except Exception as e:
        print(f"ERROR parsing {p}: {e}")
        continue

    for node in root.iter():
        tag = strip_ns(node.tag)
        tag_counts[tag] += 1
        for k in node.attrib.keys():
            attr_keys_by_tag[tag][k] += 1

        # Look for verse-like markers in attributes
        for k, v in node.attrib.items():
            if VERSE_ID_PAT.search(v or ""):
                add_sample("verse_like", {
                    "file": str(p.name), "tag": tag, "attr": k, "val": v[:80]
                })

        # Look for explicit verse tags (common names)
        if tag in {"v","verse"}:
            add_sample("verse_like", {
                "file": str(p.name), "tag": tag, "attrs": dict(list(node.attrib.items())[:4])
            })

        # Word-with-strongs candidates
        if any(STRONGS_PAT.search((node.attrib.get(k) or "")) for k in node.attrib):
            add_sample("word_with_strongs", {
                "file": str(p.name), "tag": tag,
                "attrs": {k: node.attrib[k] for k in list(node.attrib)[:6]}
            })

        # Chapter/book heuristics
        if tag in {"c","chapter"}:
            add_sample("chapter_like", {
                "file": str(p.name), "tag": tag, "attrs": dict(list(node.attrib.items())[:4])
            })
        if tag == "book":
            add_sample("book_like", {
                "file": str(p.name), "tag": tag, "attrs": dict(list(node.attrib.items())[:4])
            })

print("\n=== Top tags ===")
for t, c in tag_counts.most_common(20):
    print(f"{t:>15} : {c}")

print("\n=== Attr keys by tag (top few) ===")
for t, cnt in list(attr_keys_by_tag.items())[:12]:
    top = ", ".join([f"{k}({n})" for k,n in cnt.most_common(8)])
    print(f"{t:>15} : {top}")

print("\n=== Samples: verse-like ===")
print(json.dumps(samples["verse_like"], indent=2))

print("\n=== Samples: word-with-strongs ===")
print(json.dumps(samples["word_with_strongs"], indent=2))

print("\n=== Samples: chapter-like ===")
print(json.dumps(samples["chapter_like"], indent=2))

print("\n=== Samples: book-like ===")
print(json.dumps(samples["book_like"], indent=2))
