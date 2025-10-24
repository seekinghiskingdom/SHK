#!/usr/bin/env bash
set -euo pipefail

echo "[make_all] fetch"
shk-lit fetch --out data/raw

echo "[make_all] normalize"
shk-lit normalize --in-raw data/raw --out data/processed

echo "[make_all] index"
shk-lit index --in-proc data/processed --out data/processed

echo "[make_all] export-pages -> docs/data/v1"
shk-lit export-pages --in-proc data/processed --out ../../docs/data/v1
