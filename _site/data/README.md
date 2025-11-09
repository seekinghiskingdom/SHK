# Site Data API (v1)

All browser-fetched JSON lives under `docs/data/v1/` (API/schema version 1).

- **Bible texts** (per-book JSON): `docs/data/v1/lit/bible/en/kjv/GEN.json`, etc.
- **Strong’s lexicon shards**: `docs/data/v1/lit/strongs/…`
- **Tool indices/config**: `docs/data/v1/tools/<tool>/…`

Only create `v2/` if the JSON format changes in a breaking way.
Content refreshes are tracked via per-dataset `manifest.json` files.
