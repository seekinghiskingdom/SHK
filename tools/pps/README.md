# Proverb Pairs Search (PPS)
Part of _Seeking His Kingdom_ (SHK)

**v1.0 scope:** Site live with PPS page; positive, unambiguous, causal pairs only; **KJV (default)** + **WEB** display (include WEB at launch unless it becomes a blocker).

---

## v1.0 — Features

### Site-wide
- Pages: **Home**, **Resources**, **About**, **PPS**
- **Disclaimers & About PPS** (goal, method, interpretation limits, non-commercial)
- **Feedback:** Google Form link in footer
- **Attribution:** KJV courtesy; WEB Public Domain, shown in footer

### PPS
- **Inputs** multi-select; **Outputs** multi-select (full canonical lists; no type-ahead/Top-10)
- **Filters:** **Chapter** (multi; includes “All”), **Display Translation** (KJV/WEB)
- **Search** button + **result count**
- **Results:** Bible order only; one row per verse/range; ref + verse text (KJV/WEB); input→output **pair pills**; **bold/underline/color** for up to 2 anchor phrases
- **Not in v1.0:** per-verse BG links, selection/bulk actions, sorting toggle

---

## v1.0 — To-Do

### Backend
- **Schema (minimal):**
  - `id`, `ref`, `text_KJV`, `text_WEB`
  - `pairs: [{ input_tag, output_tag, type: "causal", anchor_phrases: [...] }]`
  - optional `note`
- **Controlled vocab:** `input_tags.json`, `output_tags.json` (canonical lists)
- **Config:** `config.json` (chapters, display translations, attribution text, defaults)
- **Indexes (optional):** `tag→[ids]`, `chapter→[ids]`
- **Dataset (seed):** only positive, clear causal pairs (Proverbs)

### Frontend
- **Pages:** Home, Resources, About, PPS
- **PPS UI:** Inputs/Outputs multi-selects; Chapter; Translation; Search; counts
- **Render:** Bible order; verse + ref; pair pills; anchor highlighting
- **Footer:** attribution + **Google Form** feedback link
- **QA:**
  - Empty Inputs/Outputs = **show all verses** (default) (or sample set via config)
  - No-match state; multi-chapter filter; anchor rendering

_Optional v0.0 soft launch = skeleton pages + About/Disclaimers + Feedback live; PPS placeholder._

---

## Roadmap

### v1.1
- Per-verse **BibleGateway** icon/link (opens chosen translation)
- Sorting toggle (Bible order ↔ group by tag)
- Selector QoL: type-to-search; optional Top-10

### v1.2
- Add more **positive pairs** (including **correlative/interpretive**)
- Filters: **Relationship Type** (causal/correlative/sequential/contrast)
- Sub-result indicators: type marker and optional confidence rating
- Synonyms/alternatives from other versions shown in pill (can align with future auto-groups)
- **Selection & bulk actions:** copy refs, copy refs+text, export TXT/CSV, **BG multi-passage link** (auto-batch)

### v1.3 (Language & Negatives)
- **Strong’s / original anchor** per verse
- **Interlinear view** (original under each English result; same ref/pills/anchors)
- **Multilingual outputs** (translate keywords/anchors/verses where free translations exist; otherwise English verse + translated tags)
- **Introduce Polarity (Negative)** and enable **Polarity filter**; add clear causal negatives; finalize all positives

### vXX.XX (Later)
- **ESV API**; permissions to other translations
- **Finalize all negatives & complete Proverbs**
- **Expand to other books** + Book/OT/NT filters
- **Bubble map** visualization (click nodes/edges to run searches)

---

## Mockups (optional)
> Place images in `docs/img/` and update paths below.

- Desktop wireframe  
  ![PPS Desktop Wireframe](docs/img/pps_desktop_wireframe.png)

- Styled desktop (grey + gold, SHK branding)  
  ![PPS Styled Desktop](docs/img/pps_desktop_styled.png)

- Mobile responsive layout  
  ![PPS Mobile Web](docs/img/pps_mobile_web.png)

- Native app variant (concept)  
  ![PPS Native App Concept](docs/img/pps_native_app.png)

- Bubble map (network of keyword hubs with verse panel)  
  ![PPS Bubble Map](docs/img/pps_bubble_map.png)

---

## Notes
- On-page text is **public-domain** (KJV/WEB). Other translations via links/APIs only.
- On load, the PPS page **shows all verses** (Bible order).
- Feedback via Google Form (link in footer).
