# tools/pps/scripts/indexer.py
from __future__ import annotations
from typing import Dict, List
from .schema import Entry
from .normalize import norm_key

# Optional config flags (or pass as args)
try:
    from . import config
    SYNONYMS_MODE = getattr(config, "SYNONYMS_MODE", "ignore")
    DEFAULT_TRANS = getattr(config, "DEFAULT_TRANS", "kjv")   # string as-is
except Exception:
    SYNONYMS_MODE = "ignore"
    DEFAULT_TRANS = "kjv"

IGNORE_SYNONYMS = (SYNONYMS_MODE == "ignore")



def _keys_for_side(side_obj) -> List[str]:
    """
    Returns the list of keys to index for one side (primary + synonyms),
    honoring IGNORE_SYNONYMS.
    """
    if IGNORE_SYNONYMS:
        return [side_obj.key]
    # Ensure primary is included first, then uniques
    seen = set()
    out: List[str] = []
    for k in [side_obj.key] + (side_obj.keys or []):
        nk = k.strip()
        if not nk or nk in seen:
            continue
        seen.add(nk)
        out.append(nk)
    return out


def build_index(entries: List[Entry], include_deprecated: bool = False) -> Dict[str, Dict[str, List[str]]]:
    """
    Build reverse lookup index:
      { "x": { norm_key -> [pairId, ...] }, "y": { ... } }
    If include_deprecated=False, deprecated pairs are excluded.
    """
    ix_x: Dict[str, List[str]] = {}
    ix_y: Dict[str, List[str]] = {}

    for entry in entries:
        for pair in entry.pairs:
            if (not include_deprecated) and pair.status == "deprecated":
                continue

            # X-side
            for k in _keys_for_side(pair.x):
                nk = norm_key(k)
                ix_x.setdefault(nk, []).append(pair.pairId)

            # Y-side
            for k in _keys_for_side(pair.y):
                nk = norm_key(k)
                ix_y.setdefault(nk, []).append(pair.pairId)

    # Optional: de-duplicate while preserving order
    for m in (ix_x, ix_y):
        for key, ids in m.items():
            seen = set()
            deduped = []
            for pid in ids:
                if pid in seen:
                    continue
                seen.add(pid)
                deduped.append(pid)
            m[key] = deduped

    return {"x": ix_x, "y": ix_y}
