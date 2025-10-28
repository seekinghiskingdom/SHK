# tools/pps/scripts/writer.py
from __future__ import annotations
import json, gzip, os
from datetime import datetime, timezone
from typing import Dict, List, Optional
from .schema import Entry, Stats, Bundle

def iso_now() -> str:
    """UTC timestamp for metadata."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def compute_stats(entries: List[Entry]) -> Stats:
    entry_count = len(entries)
    pair_count = sum(len(e.pairs) for e in entries)
    pair_count_active = sum(sum(1 for p in e.pairs if p.status == "active") for e in entries)
    return Stats(entryCount=entry_count, pairCount=pair_count, pairCountActive=pair_count_active)

def make_bundle(
    *,
    schema_version: int,
    bundle_version: str,
    default_trans: str,
    trans_meta: Dict[str, Dict[str, str]],
    entries: List[Entry],
    index: Dict[str, Dict[str, List[str]]],
    built_at: Optional[str] = None,
) -> Bundle:
    stats = compute_stats(entries)
    built_at = built_at or iso_now()
    return Bundle(
        schemaVersion=schema_version,
        bundleVersion=bundle_version,
        builtAt=built_at,
        defaultTrans=default_trans,
        transMeta=trans_meta,
        stats=stats,
        entries=entries,
        index=index,
    )

def _bundle_to_dict(bundle: Bundle) -> dict:
    """Dataclasses → plain dict for JSON dumping."""
    # dataclasses.asdict would work, but manual composition avoids accidental recursion
    return {
        "schemaVersion": bundle.schemaVersion,
        "bundleVersion": bundle.bundleVersion,
        "builtAt": bundle.builtAt,
        "defaultTrans": bundle.defaultTrans,
        "transMeta": bundle.transMeta,
        "stats": {
            "entryCount": bundle.stats.entryCount,
            "pairCount": bundle.stats.pairCount,
            "pairCountActive": bundle.stats.pairCountActive,
        },
        "entries": [
            {
                "entryId": e.entryId,
                "ref": e.ref,
                "osis": e.osis,
                "chapter": e.chapter,
                "verses": e.verses,
                "text": e.text,
                "pairs": [
                    {
                        "pairId": p.pairId,
                        "pv": p.pv,
                        "x": {
                            "key": p.x.key,
                            "keys": p.x.keys,
                            "root": p.x.root,
                            "roots": p.x.roots,
                        },
                        "y": {
                            "key": p.y.key,
                            "keys": p.y.keys,
                            "root": p.y.root,
                            "roots": p.y.roots,
                        },
                        "status": p.status,
                    }
                    for p in e.pairs
                ],
                "notes": e.notes,
            }
            for e in bundle.entries
        ],
        "index": bundle.index,
    }

def write_json(bundle: Bundle, path: str, pretty: bool = False) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = _bundle_to_dict(bundle)
    with open(path, "w", encoding="utf-8") as f:
        if pretty:
            json.dump(data, f, ensure_ascii=False, indent=2)
        else:
            json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

def write_gzip(json_path: str, gz_path: Optional[str] = None) -> str:
    """
    Gzip a JSON file alongside it. Returns the gz path.
    """
    gz_path = gz_path or (json_path + ".gz")
    with open(json_path, "rb") as src, gzip.open(gz_path, "wb", compresslevel=6) as dst:
        dst.write(src.read())
    return gz_path
