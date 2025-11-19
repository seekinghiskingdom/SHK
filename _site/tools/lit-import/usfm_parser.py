from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class USFMVerse:
    verse: int
    text: str = ""


@dataclass
class USFMBook:
    book_id: Optional[str] = None
    name: str = ""
    chapters: Dict[int, List[USFMVerse]] = field(default_factory=dict)


class USFMParser:
    def __init__(self) -> None:
        pass

    def parse_usfm(self, text: str) -> USFMBook:
        book = USFMBook()
        current_chapter: Optional[int] = None
        current_verse: Optional[USFMVerse] = None

        for raw_line in text.splitlines():
            line = raw_line.rstrip("\n").strip()
            if not line:
                continue

            if line.startswith("\\id "):
                parts = line.split(maxsplit=2)
                if len(parts) >= 2:
                    book.book_id = parts[1].upper()
                continue

            if line.startswith("\\h "):
                name = line[3:].strip()
                if name:
                    book.name = name
                continue

            if line.startswith("\\c "):
                parts = line.split(maxsplit=1)
                if len(parts) == 2:
                    try:
                        current_chapter = int(parts[1].strip())
                        if current_chapter not in book.chapters:
                            book.chapters[current_chapter] = []
                        current_verse = None
                    except ValueError:
                        pass
                continue

            if line.startswith("\\v "):
                parts = line.split(maxsplit=2)
                if len(parts) >= 2:
                    try:
                        vnum = int(parts[1])
                    except ValueError:
                        # verse ranges or non-numeric; skip for now
                        continue
                    verse_text = parts[2].strip() if len(parts) == 3 else ""
                    if current_chapter is None:
                        current_chapter = 1
                        if current_chapter not in book.chapters:
                            book.chapters[current_chapter] = []
                    current_verse = USFMVerse(verse=vnum, text=verse_text)
                    book.chapters[current_chapter].append(current_verse)
                continue

            # Any other line: treat as continuation / formatting
            if current_verse is not None:
                if line.startswith("\\"):
                    parts = line.split(maxsplit=1)
                    if len(parts) == 2:
                        extra_text = parts[1].strip()
                    else:
                        extra_text = ""
                else:
                    extra_text = line
                if extra_text:
                    if current_verse.text:
                        current_verse.text += " " + extra_text
                    else:
                        current_verse.text = extra_text

        if not book.name and book.book_id:
            book.name = book.book_id

        return book
