#!/usr/bin/env bash
shk-lit --spec src/shk_lit_import/specs/bible_en_kjv_plain.json fetch
shk-lit --spec src/shk_lit_import/specs/bible_en_kjv_plain.json normalize
shk-lit --spec src/shk_lit_import/specs/bible_en_kjv_plain.json index
shk-lit --spec src/shk_lit_import/specs/bible_en_kjv_plain.json export-pages --out ../../docs/data/v1
