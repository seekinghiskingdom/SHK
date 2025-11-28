# SHK Backend Phases – High‑Level Roadmap (Accounts, Testimonies, Daily, Tools)

> This document is a concise map of the major data / Supabase phases for SHK v1 and beyond.  
> Each phase has its own detailed contract (ACC‑P1.0, ACC‑P1.1, TST‑P2.0, etc.).

---

## Phase 1.0 – Core Accounts and Profiles (ACC‑P1.0)

**Goal:** Give every user a stable SHK identity and a single profile row other modules can attach to.

- Auth via Supabase (`auth.users`) with email + password, email verification, reset flows.
- Front‑end pages:
  - `/account/sign-up/`, `/account/sign-in/`, `/account/confirm/`, `/account/reset-password/`.
  - `/account/` (My Testimony – account home, avatar + name + testimony scaffolding).
  - `/account/settings/` (manage display name, handle, email, password, avatar).
- Data:
  - `auth.users.user_metadata` for `display_name`, `handle`, `avatar_key`.
  - `public.profiles` table mirrors these and exposes non‑sensitive profile data.
- RLS:
  - Public read of basic profiles; each user can only write their own row.

---

## Phase 1.1 – Roles and Admin Scaffolding (ACC‑P1.1)

**Goal:** Introduce minimal roles and admin scaffolding without exposing complex moderation UI.

- Data:
  - `user_metadata.role` in `auth.users` (source of truth: `user`, `mod`, `admin`).
  - `profiles.role` and `profiles.is_banned` for quick checks and future moderation.
  - Optional `admin_events` audit log for later.
- Pages:
  - `/admin/` (stub dashboard).
  - `/admin/accounts/`, `/admin/content/` as placeholders.
- Behaviour:
  - Only `mod`/`admin` allowed into `/admin/*`.
  - Admin‑only avatars gated by role.
  - Profiles upsert remains the single attach point for modules.

---

## Phase 2.0 – Testimony Data Model (TST‑P2.0)

**Goal:** Create a robust, RLS‑safe data model for testimonies that any UI (account page, wall, tools) can consume.

- Data:
  - `public.testimonies` (core table) – one row per testimony event.
    - Includes: `id`, `author_id`, `type` (`salvation`, `prayer`, `blessing`, `miracle`, `general`), `title`, `body`, `visibility` (`public`/`private`), timestamps, etc.
  - Optional `public.testimony_tags` for topic tags.
  - Derived views (later) for “my testimonies”, “public feed”, etc.
- Behaviour:
  - Submission via `/testimony/add/` (single form for salvation + other testimonies, with type selector).
  - Account page reads:
    - “My Salvation Testimony” block shows the most recent `type='salvation'` row for that user.
    - “Other testimonies” list is filterable by `type` and `visibility`.
  - RLS ensures:
    - Users can CRUD only their own testimonies.
    - Public endpoints can see only `visibility='public'`.

---

## Phase 2.1 – Connections and Community Layer (CON‑P2.1)

**Goal:** Add a light‑weight following and interaction layer, purely for filtering / experience, not gamification.

- Data:
  - `public.follows` – `(follower_id, followee_id, created_at)`; no public counts; used only for filters.
  - Optional `public.testimony_reactions` – `amen`/`heart` counters with per‑user uniqueness.
- Behaviour:
  - “Follow this testimony / person” on public profile and wall routes.
  - Testimony Wall filters:
    - “Everyone” vs “People I follow (and me)”.
  - No public follower/following counts in v1; data is for experience only.
- RLS:
  - Users can see their own follow graph; aggregate counts, if ever exposed, should be anonymised.

---

## Phase 3.0 – Daily Module (DAY‑P3.0)

**Goal:** Track simple daily completion and optionally reflections to support “streak”‑style encouragement.

- Pages:
  - `/daily/` – unified daily flow (trivia, BibleLE, verse, proverb, listening, reflection, finish).
  - Possible `/daily/history/` – calendar or list view of completion history.
- Data:
  - `public.daily_checkins` – one row per user per day:
    - Flags like `did_trivia`, `did_biblele`, `did_verse`, `did_proverb`, `did_plan`, `did_quiet`, `did_reflection`, `completed_day`.
  - Optional `public.daily_reflections` – text responses keyed by user + day.
- Behaviour:
  - Front‑end marks completion flags as user interacts, then POSTs to Supabase to upsert that day’s record.
  - Streaks calculated from `daily_checkins` (client‑side or view).
- RLS:
  - Users can only read/write their own daily rows.

---

## Phase 4.0 – Future Tools and Saved Data (FUT‑P4.x)

**Goal:** Prepare a pattern for tool‑specific saved data without committing to full implementations pre‑launch.

Candidate sub‑phases (each would get its own mini‑contract later):

1. **Bible Viewer / reading convenience**
   - Tables for:
     - `bible_last_read` per user (book/chapter/verse).
     - `bible_bookmarks` (small number per user).
     - Possibly `bible_highlights`/`notes` if storage is acceptable.

2. **Strong’s Concordance + Biblical Language Learning (SCS / BLL)**
   - Tables for:
     - `scs_sets` (saved notecard sets = lists of Strong’s numbers).
     - `bll_progress` (per‑user mastery stats and quiz history).
   - Tight caps per user for v1 (e.g., max N sets / entries).

3. **PPS convenience**
   - If needed, small tables for:
     - Saved searches or favourite pairs.
   - This is very optional; likely post‑v1.

---

## Dependencies and Order

- **Phase 1.0** must be fully implemented and QA’d before any module writes user‑scoped data.
- **Phase 1.1** should be in place before exposing any `/admin/` tooling or moderation behaviour.
- **Phase 2.0** depends on 1.0 (profiles) and should be stable before building the Testimony Wall UI.
- **Phase 2.1** depends on 2.0 (needs `testimonies` table to follow against).
- **Phase 3.0** depends only on 1.0, but it is safer to complete testimonies first for launch focus.
- **Phase 4.x** is explicitly optional and can be layered whenever capacity allows, reusing the patterns in 2.x and 3.0.

