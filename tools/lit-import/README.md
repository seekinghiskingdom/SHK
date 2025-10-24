# shk-lit-import

Pipeline to fetch, normalize, index, and export literature data for the SHK site.

## Export targets (API v1)
- KJV per-book JSON → `docs/data/v1/lit/bible/en/kjv/`
- Strong’s shards → `docs/data/v1/lit/strongs/`
- Tool indices → `docs/data/v1/tools/{scs,pps}/`

## Quick start
```bash
cd tools/lit-import
python -m venv .venv && source .venv/bin/activate
pip install -e .
shk-lit --help
```
