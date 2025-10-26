
# Full 66-book mapping and canonical order for OSIS -> 3-letter codes
BOOKS_CANON = [
    # Pentateuch
    ("Gen", "GEN"), ("Exod", "EXO"), ("Lev", "LEV"), ("Num", "NUM"), ("Deut", "DEU"),
    # History
    ("Josh", "JOS"), ("Judg", "JDG"), ("Ruth", "RUT"), ("1Sam", "1SA"), ("2Sam", "2SA"),
    ("1Kgs", "1KI"), ("2Kgs", "2KI"), ("1Chr", "1CH"), ("2Chr", "2CH"), ("Ezra", "EZR"),
    ("Neh", "NEH"), ("Esth", "EST"),
    # Poetry/Wisdom
    ("Job", "JOB"), ("Ps", "PSA"), ("Prov", "PRO"), ("Eccl", "ECC"), ("Song", "SNG"),
    # Major Prophets
    ("Isa", "ISA"), ("Jer", "JER"), ("Lam", "LAM"), ("Ezek", "EZK"), ("Dan", "DAN"),
    # Minor Prophets
    ("Hos", "HOS"), ("Joel", "JOL"), ("Amos", "AMO"), ("Obad", "OBA"), ("Jonah", "JON"),
    ("Mic", "MIC"), ("Nah", "NAH"), ("Hab", "HAB"), ("Zeph", "ZEP"), ("Hag", "HAG"),
    ("Zech", "ZEC"), ("Mal", "MAL"),
    # Gospels/Acts
    ("Matt", "MAT"), ("Mark", "MRK"), ("Luke", "LUK"), ("John", "JHN"), ("Acts", "ACT"),
    # Pauline Epistles
    ("Rom", "ROM"), ("1Cor", "1CO"), ("2Cor", "2CO"), ("Gal", "GAL"), ("Eph", "EPH"),
    ("Phil", "PHP"), ("Col", "COL"), ("1Thess", "1TH"), ("2Thess", "2TH"), ("1Tim", "1TI"),
    ("2Tim", "2TI"), ("Titus", "TIT"), ("Phlm", "PHM"),
    # General Epistles + Revelation
    ("Heb", "HEB"), ("Jas", "JAS"), ("1Pet", "1PE"), ("2Pet", "2PE"), ("1John", "1JN"),
    ("2John", "2JN"), ("3John", "3JN"), ("Jude", "JUD"), ("Rev", "REV"),
]

OSIS_TO_BK3 = {osis: bk3 for osis, bk3 in BOOKS_CANON}
BK3_TO_OSIS = {bk3: osis for osis, bk3 in BOOKS_CANON}
BOOKS_3LTR = [bk3 for _, bk3 in BOOKS_CANON]
OSIS_ORDER = [osis for osis, _ in BOOKS_CANON]
