# tools/pps/scripts/id_utils.py
from __future__ import annotations
import hashlib
from typing import List, Dict
from .normalize import slug

# --- Book code ↔ readable maps (expand as you add books) ---
BOOK_CODE_TO_REF = {
    "PRO": "Prov",   # Proverbs
}
BOOK_CODE_TO_OSIS = {
    "PRO": "Prov",
}

def _z(n: int, width: int = 3) -> str:
    """Zero-pad integers for IDs."""
    return str(n).zfill(width)

# ---------- Entry-level IDs / refs ----------

def entry_id(ref_parts: Dict[str, int | str]) -> str:
    """
    Deterministic, stable entry id from ref:
    {'book':'PRO','ch':21,'start':11,'end':11} -> 'prov-021-011-011'
    """
    code = str(ref_parts["book"]).upper()
    ch   = int(ref_parts["ch"])
    st   = int(ref_parts["start"])
    en   = int(ref_parts["end"])
    return f"{code.lower()}-{_z(ch)}-{_z(st)}-{_z(en)}"

def ref_string(ref_parts: Dict[str, int | str]) -> str:
    """
    Human-readable reference string used in the bundle:
    -> 'Prov 21:11' or 'Prov 1:1-4'
    """
    abbr = BOOK_CODE_TO_REF.get(str(ref_parts["book"]).upper(), str(ref_parts["book"]))
    ch   = int(ref_parts["ch"])
    st   = int(ref_parts["start"])
    en   = int(ref_parts["end"])
    if st == en:
        return f"{abbr} {ch}:{st}"
    return f"{abbr} {ch}:{st}-{en}"

def osis_string(ref_parts: Dict[str, int | str]) -> str:
    """
    OSIS-style reference:
    -> 'Prov.21.11' or 'Prov.1.1-Prov.1.4'
    """
    osis_book = BOOK_CODE_TO_OSIS.get(str(ref_parts["book"]).upper(), str(ref_parts["book"]))
    ch   = int(ref_parts["ch"])
    st   = int(ref_parts["start"])
    en   = int(ref_parts["end"])
    if st == en:
        return f"{osis_book}.{ch}.{st}"
    return f"{osis_book}.{ch}.{st}-{osis_book}.{ch}.{en}"

# ---------- Pair-level stable hash & ID ----------

def pair_hash(
    ref_parts: Dict[str, int | str],
    pv_list: List[int],
    x_roots: List[str],
    y_roots: List[str],
    hash_len: int = 8,
) -> str:
    """
    Short content hash that changes only if the pair's *content* changes.
    Includes: book, ch, start, end, pv list, X roots, Y roots.
    (Primary keys are *not* included—IDs should stay stable if you tweak synonyms.)
    """
    code = str(ref_parts["book"]).upper()
    ch   = int(ref_parts["ch"])
    st   = int(ref_parts["start"])
    en   = int(ref_parts["end"])

    pv_norm   = ",".join(str(v) for v in sorted(set(pv_list)))
    x_norm    = " || ".join(r.strip() for r in x_roots if r and r.strip())
    y_norm    = " || ".join(r.strip() for r in y_roots if r and r.strip())

    payload = f"{code}|{ch}|{st}|{en}|pv:{pv_norm}|x:{x_norm}|y:{y_norm}"
    h = hashlib.sha1(payload.encode("utf-8")).hexdigest()
    return h[:hash_len]

def pair_id(
    entry_id_str: str,
    x_primary_key: str,
    y_primary_key: str,
    short_hash: str,
) -> str:
    """
    Final pairId string:
    '{entryId}__x-{slug(x)}__y-{slug(y)}__{hash8}'
    """
    xs = slug(x_primary_key)
    ys = slug(y_primary_key)
    return f"{entry_id_str}__x-{xs}__y-{ys}__{short_hash}"

def ensure_unique(candidate: str, existing: set[str]) -> str:
    """
    Guard against the (very unlikely) case of a collision:
    if 'foo__abcd1234' exists, returns 'foo__abcd1234~1', '~2', ... as needed.
    """
    if candidate not in existing:
        return candidate
    i = 1
    out = f"{candidate}~{i}"
    while out in existing:
        i += 1
        out = f"{candidate}~{i}"
    return out

# ---------- Convenience: build full pairId in one call ----------

def make_pair_id(
    ref_parts: Dict[str, int | str],
    pv_list: List[int],
    x_primary_key: str,
    y_primary_key: str,
    x_roots: List[str],
    y_roots: List[str],
) -> str:
    """
    One-shot helper:
      - builds entryId
      - computes short content hash
      - returns the final pairId
    """
    eid = entry_id(ref_parts)
    h8  = pair_hash(ref_parts, pv_list, x_roots, y_roots, hash_len=8)
    return pair_id(eid, x_primary_key, y_primary_key, h8)

# ---------- Quick self-test ----------
if __name__ == "__main__":
    ref = {"book": "PRO", "ch": 21, "start": 11, "end": 11}
    assert entry_id(ref) == "pro-021-011-011"
    assert ref_string(ref) == "Prov 21:11"
    assert osis_string(ref) == "Prov.21.11"
    h1 = pair_hash(ref, [11], ["scoffer is punished"], ["the simple is made wise"])
    pid = pair_id(entry_id(ref), "scoffer is punished", "simple becomes wise", h1[:8])
    assert pid.startswith("pro-021-011-011__x-scoffer-is-punished__y-simple-becomes-wise__")
    print("id_utils self-test OK")
