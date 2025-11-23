@echo off
setlocal
set Pairs=tools/pps/data/input/pairs/pairs.csv
set BibleRoot=docs/data/v1/lit/bible/en
set Trans=kjv
set OutScratch=tools/pps/data/output/shk_pairs.json
set PublishDir=docs/data/v1/tools/pps

python -m tools.pps.scripts.build ^
  --pairs "%Pairs%" ^
  --bible-root "%BibleRoot%" ^
  --trans "%Trans%" ^
  --out "%OutScratch%" ^
  --bundle-version auto ^
  --gzip ^
  --publish-dir "%PublishDir%" ^
  --pretty
