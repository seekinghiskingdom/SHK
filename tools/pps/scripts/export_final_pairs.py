#!/usr/bin/env python3
"""
PPS v1 – Step 4.2: input_pairs.json → final_pairs.json (+ warnings)

- Reads the master input_pairs.json (Step 2.1 output).
- Reads pps_export_config.v1.json (tools-side).
- Produces:
  - final_pairs.json (site-facing data under docs/)
  - final_pairs_warnings.json (diagnostic log under tools/)
- Also writes a site-side copy of the config to docs/data/v1/pps/ with
  export_meta attached, so the front-end can see which fields/filters
  are in use and when the export was built.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class ExportConfig:
    input_file: Path
    output_file: Path
    warnings_file: Path
    mappings: Dict[str, Any]
    required_fields: List[str]
    config_path: Path


def _default_paths() -> Tuple[Path, Path]:
    """
    Default locations when running from repo root.

    - Config: tools/pps/data/config/pps_export_config.v1.json
    """
    base = Path(".").resolve()
    config_default = base / "tools" / "pps" / "data" / "config" / "pps_export_config.v1.json"
    return base, config_default


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _get_nested(obj: Dict[str, Any], path: str) -> Any:
    """
    Resolve a dotted path like "R.book" or "X.key" inside a pair object.
    Returns None if any segment is missing.
    """
    parts = path.split(".")
    cur: Any = obj
    for part in parts:
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


def _build_section(
    pair_obj: Dict[str, Any],
    section_mapping: Dict[str, str],
) -> Dict[str, Any]:
    """
    Build a block (ref / status / x / y) using the mapping for that section.
    """
    out: Dict[str, Any] = {}
    for out_key, src_path in section_mapping.items():
        val = _get_nested(pair_obj, src_path)
        # Keep keys even if val is None; required-field checks happen separately.
        out[out_key] = val
    return out


def _load_export_config(config_path: Path, base: Path) -> Tuple[ExportConfig, Dict[str, Any]]:
    cfg_raw = _load_json(config_path)

    def _to_path(value: str) -> Path:
        # Treat paths in the config as relative to repo root.
        return (base / value).resolve()

    input_file = _to_path(cfg_raw["input_file"])
    output_file = _to_path(cfg_raw["output_file"])
    warnings_file = _to_path(cfg_raw["warnings_file"])

    mappings = cfg_raw.get("mappings", {})
    required_fields = cfg_raw.get("required_fields", [])

    cfg = ExportConfig(
        input_file=input_file,
        output_file=output_file,
        warnings_file=warnings_file,
        mappings=mappings,
        required_fields=required_fields,
        config_path=config_path.resolve(),
    )
    return cfg, cfg_raw


def _build_final_pairs(
    master: Dict[str, Any],
    cfg: ExportConfig,
) -> Tuple[Dict[str, Any], Dict[str, Any], str]:
    """
    Apply mappings and required-field checks to build final_pairs + warnings.
    Returns:
      final_obj, warnings_obj, generated_at timestamp.
    """
    master_pairs: List[Dict[str, Any]] = master.get("pairs", [])
    mappings = cfg.mappings

    id_mapping = mappings.get("id")
    ref_mapping = mappings.get("ref", {})
    status_mapping = mappings.get("status", {})
    x_mapping = mappings.get("x", {})
    y_mapping = mappings.get("y", {})

    final_pairs: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []

    for pair in master_pairs:
        # ID
        if isinstance(id_mapping, str):
            pair_id = _get_nested(pair, id_mapping)
        else:
            pair_id = pair.get("pair_id")

        # Build blocks
        ref_block = _build_section(pair, ref_mapping)
        status_block = _build_section(pair, status_mapping)
        x_block = _build_section(pair, x_mapping)
        y_block = _build_section(pair, y_mapping)

        final_pair = {
            "id": pair_id,
            "ref": ref_block,
            "status": status_block,
            "x": x_block,
            "y": y_block,
        }

        # Required-field checks (operate on final shape)
        missing_fields: List[str] = []
        for path in cfg.required_fields:
            parts = path.split(".")
            cur: Any = final_pair
            for part in parts:
                if isinstance(cur, dict) and part in cur:
                    cur = cur[part]
                else:
                    cur = None
                    break
            if cur is None or (isinstance(cur, str) and cur.strip() == ""):
                missing_fields.append(path)

        if missing_fields:
            warnings.append(
                {
                    "id": pair_id,
                    "missing_fields": missing_fields,
                    "notes": "Missing required fields; pair kept in output.",
                }
            )

        final_pairs.append(final_pair)

    generated_at = datetime.utcnow().isoformat(timespec="seconds") + "Z"

    # meta for final_pairs.json
    final_meta = {
        "generated_at": generated_at,
        "source": {
            "master_file": str(cfg.input_file),
            "config_file": str(cfg.config_path),
        },
        "stats": {
            "pairs_total": len(final_pairs),
            "books": sorted(
                {p["ref"].get("book") for p in final_pairs if p.get("ref")}
            ),
            "chapters": sorted(
                {
                    f"{p['ref'].get('book')}.{p['ref'].get('chapter')}"
                    for p in final_pairs
                    if p.get("ref")
                    and p["ref"].get("book") is not None
                    and p["ref"].get("chapter") is not None
                }
            ),
        },
    }

    # meta for warnings file
    warnings_meta = {
        "generated_at": generated_at,
        "source": {
            "master_file": str(cfg.input_file),
            "config_file": str(cfg.config_path),
        },
        "stats": {
            "pairs_total": len(final_pairs),
            "warnings_total": len(warnings),
        },
    }

    final_obj = {"meta": final_meta, "pairs": final_pairs}
    warnings_obj = {"meta": warnings_meta, "warnings": warnings}

    return final_obj, warnings_obj, generated_at


def build_final_pairs(config_path: Path) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    base, _ = _default_paths()
    config_path = config_path.resolve()
    cfg, cfg_raw = _load_export_config(config_path, base)

    master = _load_json(cfg.input_file)
    final_obj, warnings_obj, generated_at = _build_final_pairs(master, cfg)

    # Ensure directories exist
    cfg.output_file.parent.mkdir(parents=True, exist_ok=True)
    cfg.warnings_file.parent.mkdir(parents=True, exist_ok=True)

    with cfg.output_file.open("w", encoding="utf-8") as f:
        json.dump(final_obj, f, ensure_ascii=False, indent=2)

    with cfg.warnings_file.open("w", encoding="utf-8") as f:
        json.dump(warnings_obj, f, ensure_ascii=False, indent=2)

    # Also write a site-side copy of the config with export_meta
    site_cfg_path = base / "docs" / "data" / "v1" / "pps" / cfg.config_path.name
    site_cfg_path.parent.mkdir(parents=True, exist_ok=True)

    site_cfg = dict(cfg_raw)  # shallow copy is fine here
    site_cfg["export_meta"] = {
        "generated_at": generated_at,
        "master_file": str(cfg.input_file),
        "config_source_file": str(cfg.config_path),
        "final_pairs_file": str(cfg.output_file),
        "warnings_file": str(cfg.warnings_file),
    }

    with site_cfg_path.open("w", encoding="utf-8") as f:
        json.dump(site_cfg, f, ensure_ascii=False, indent=2)

    return final_obj, warnings_obj


def main() -> None:
    base, config_default = _default_paths()

    parser = argparse.ArgumentParser(
        description="Build PPS v1 final_pairs.json from input_pairs.json + config"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=config_default,
        help=f"Path to pps_export_config JSON (default: {config_default})",
    )

    args = parser.parse_args()
    config_path = args.config if args.config.is_absolute() else (base / args.config)

    final_obj, warnings_obj = build_final_pairs(config_path)

    print(f"Built final data: {len(final_obj['pairs'])} pairs")
    print(
        f"Warnings: {warnings_obj['meta']['stats']['warnings_total']}"
    )


if __name__ == "__main__":
    main()
