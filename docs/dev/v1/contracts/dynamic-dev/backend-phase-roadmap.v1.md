# SHK Backend Phases – High‑Level Roadmap (v1, Phases 1–3)

> Concise map of the major backend / Supabase phases for SHK v1 up through the Testimony module.  
> Each phase has or will have its own detailed contract (e.g., `p1.user_account_data.v1.contract.md`, Phase 2 admin/mod contract, Phase 3 testimony contract).

---

## Phase 1 – Core Accounts and Profiles (P1 – Accounts & User Data)

**Goal:** Give every user a stable SHK identity and a single profile row that all other modules can attach to.

- **Auth & identity**
  - Supabase `auth.users` with email + password, email verification, reset flows.
  - `auth.users.user_metadata` stores convenience fields: `display_name`, `handle`, `avatar_key` (non‑authoritative).
- **Profiles (canonical app record) – `public.profiles`**
  - One row per account, keyed by `id` (FK to `auth.users.id`).
  - Core fields: `display_name`, `handle`, `avatar_key`, timestamps.
  - v1.1 adds: `role`, `account_status`, `strike_count`, `show_sensitive` as canonical app‑level fields.
- **Front‑end pages**
  - `/account/sign-up/`, `/account/sign-in/`, `/account/confirm/`, `/account/reset-password/`.
  - `/account/` – account home (“My Testimony” shell, avatar + name + high‑level account overview).
  - `/account/settings/` – change display name, handle, email, password, avatar, and account preferences (e.g., `show_sensitive`).
- **RLS & security**
  - Public read of a limited safe subset of profile fields (for search and profile pages).
  - Each user can only insert/update their own `profiles` row.
  - `auth.users` remains Supabase‑managed; all app logic keys off `public.profiles`.

**Source contract:** `p1.user_account_data.v1.contract.md`.

---

## Phase 2 – Roles, Admin Config, and Moderation Scaffolding (P2 – Admin/Mod)

**Goal:** Introduce minimal roles, account‑level moderation fields, and basic admin tooling without building the full moderation engine yet.

- **Roles & account status (on `public.profiles`)**
  - `role text not null default 'user'` – values: `user`, `mod`, `admin`.
  - `account_status text not null default 'active'` – values: `active`, `suspended_pending_review`, `suspended`, `banned_pending_review`, `banned`.
  - `strike_count integer not null default 0` – lifetime confirmed violations (used later for suspensions/bans).
  - `show_sensitive boolean not null default true` – preference for sensitive content visibility.
- **Global admin config – `public.admin_config`**
  - Single‑row table (id = 1) with moderation/app settings:
    - `review_all_new_content`, `mod_can_final_approve`, `mod_can_final_reject`.
    - Strike/suspension/ban thresholds and durations.
    - `reports_for_auto_hide` and related knobs for future moderation engine.
  - Phase 2: primarily read‑only; enforcement is wired in later phases.
- **Front‑end admin & search surfaces**
  - `/admin/` – admin dashboard shell, gated to `role='admin'`.
  - `/admin/accounts/` – basic accounts list/search (read‑only): email, handle, role, status, created_at.
  - `/admin/settings/` – view the `admin_config` singleton (edit UI deferred).
  - `/account/search/` – public account finder by handle/display name; uses safe subset of `profiles`.
  - Header search pill button (monochrome magnifying‑glass icon) linking to `/account/search/`.
- **Supabase & JS integration**
  - Single global Supabase client (`window.shkSupabase`) created once in `site.js` and reused everywhere.
  - Global avatar registry (`window.SHK_PROFILE_AVATARS` + `window.SHK_getAvatarUrlByKey`) used by header, account pages, search, and admin.
  - Header account pill uses Supabase to detect logged‑in state and show avatar/initial + link to `/account/`.
- **Security / RLS assumptions**
  - `admin_config` initially with simple/no RLS, guarded via role checks in the client.
  - Future moderation tables (`reports`, `moderation_events`, `account_penalties`, etc.) are defined conceptually but not yet created.

**Source contracts:** Phase‑2 admin/mod contract (ACC‑MOD / roles & moderation docs) + Phase‑1 Accounts contract for the shared `profiles` fields.

---

## Phase 3 – Testimony and Prayer Data Model (P3 – Testimonies & Prayer)

**Goal:** Create a robust, RLS‑safe data model for testimonies and prayer requests that any UI (account pages, Testimony Wall, tools) can consume, and that can plug into the moderation system defined in Phase 2.

- **Core testimony/prayer tables**
  - `public.testimonies` – one row per testimony or prayer event:
    - `id`, `author_id` (FK to `profiles.id`), `type` (e.g., `salvation`, `testimony`, `prayer`), `title`, `body`, `visibility` (`public`/`private`), timestamps.
    - Moderation fields: `status` (draft/pending/published/removed), `is_sensitive`, `sensitivity_reason` (as defined in moderation contracts).
  - Optional `public.testimony_tags` – for topics / categories (e.g., `healing`, `provision`, `family`).
- **Primary flows & pages**
  - `/testimony/` – Testimony home/info hub (explains what testimonies are, guidelines, how to share).
  - `/testimony/add/` – create/edit testimony or salvation testimony, with type selector and visibility controls.
  - `/testimony/wall/` – public “Testimony Wall” listing `visibility='public'` testimonies with filters and pagination.
  - Account integrations:
    - `/account/` shows “My Salvation Testimony” (most recent `type='salvation'`) and a list of “Other testimonies” for that user.
    - `/u/{handle}/` shows public testimonies belonging to that profile, respecting visibility and moderation status.
- **Moderation hooks (using Phase‑2 fields)**
  - New content creation automatically sets initial `status` (e.g., `draft_private` or `published`), then applies keyword checks and `admin_config` rules where available.
  - Future phases will wire in:
    - Keyword scanning via `moderation_keywords`.
    - Reporting and auto‑hide via `reports` and `reports_for_auto_hide`.
    - Strikes/suspensions via `moderation_events`, `account_penalties`, and `profiles.strike_count`.
- **RLS & security**
  - Users can only CRUD their own testimony rows.
  - Public queries (Testimony Wall, profile pages) see only `visibility='public'` and allowed `status` values (e.g., `published`).
  - Admin and moderator tools (Phase 4+) will access broader views via service‑role or mod/admin RLS policies.

**Source contracts:** Phase‑3 testimony data contract (to be created) plus Phase‑2 moderation contract for the moderation‐related fields and flows.

---

## Dependencies and Order (Phases 1–3)

- **Phase 1 (Accounts & Profiles)** must be complete and stable before:
  - Any testimony, prayer, daily, or tool module writes user‑scoped data.
  - Admin roles or moderation fields are relied on.
- **Phase 2 (Roles & Admin/Mod Scaffolding)** should be in place before:
  - Exposing any `/admin/*` tooling.
  - Attaching moderation/status semantics to testimonies or other content.
- **Phase 3 (Testimonies & Prayer)** depends on:
  - Phase 1 for profiles and identity.
  - Phase 2 for role and basic moderation semantics, so testimonies can be reviewable and filterable from day one, even if the full moderation engine is rolled out incrementally.

Later documents can extend this roadmap with Phase 4+ for the full moderation engine, community/follow system, daily tools, and saved Bible tools data, but those are intentionally out of scope for this “up to Phase 3” summary.
