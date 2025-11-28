# SHK Accounts – Phase 1.1 Contract  
**Tag:** ACC‑P1.1 – Roles, Moderation Flags, and Admin Scaffolding  
**Status:** Draft (ready for implementation after ACC‑P1.0 is fully green)  

---

## A. Scope and Goals

Phase 1.1 builds directly on ACC‑P1.0 and introduces:

1. A small, explicit role model (`user`, `mod`, `admin`) that is:
   - **Authoritative in `auth.users.user_metadata.role`**.
   - **Mirrored (read‑only for app logic) in `profiles.role`** for simpler querying.
2. Minimal moderation flags on profiles for future tooling.
3. Very thin `/admin/` page scaffolding so admins/mods can be routed into a dedicated area (even if the first version just shows “coming soon”).
4. No new user‑visible features beyond possible subtle badges later; this is mostly infrastructure.

Out of scope: full moderation UI, reporting systems, content queues, or analytics dashboards (these become later phases under “community / moderation module”).

---

## B. Data Model – Tables and Fields

### B1. `auth.users.user_metadata` (Supabase‑managed)

We rely on Supabase Auth as the source of truth for identity. Phase 1.1 standardises the following metadata keys (some already in use in P1.0):

- `display_name: string | null` – Human display name (already used).
- `handle: string | null` – Unique username/handle. Pattern: `^[a-z0-9_]{3,24}$`.
- `avatar_key: string | null` – Chosen avatar key (e.g., `avatar-7`, `avatar-999`).
- `role: "user" | "mod" | "admin"` – Authoritative role.  
  - Default: `"user"` for all new sign‑ups.
  - Managed only by trusted paths (SQL/admin tools or future `/admin/` UI).
- Future‑safe keys (not implemented yet, but reserved):  
  - `onboarded: boolean` – Whether user completed onboarding.
  - `terms_version: string` – Last accepted ToS version.

Implementation notes:

- Role changes for v1 are done via **SQL in the dashboard** or future `/admin/` tools (no public UI for changing your own role).
- Admin‑only avatars (e.g., `avatar-999`) are enforced by **front‑end filters plus role checks** and can be enforced at query level later if needed.

---

### B2. `public.profiles` (already created in ACC‑P1.0)

We extend the existing `profiles` table with a few columns and clarify semantics.

Required columns (Phase 1.0 + 1.1):

- `id uuid primary key references auth.users (id)`
- `handle text unique not null` – canonical username.
- `display_name text` – last known display name.
- `avatar_key text` – last chosen avatar key.
- `role text not null default 'user'` – cached role, must mirror `user_metadata.role`.
  - Allowed values: `'user'`, `'mod'`, `'admin'`.  
  - Used for quick queries and flags in admin tooling.
- `is_banned boolean not null default false` – soft ban flag (Phase 1.1 reserves it; enforcement comes later).
- `created_at timestamptz not null default now()`
- `updated_at timestamptz not null default now()`

Triggers / sync behaviour (high‑level):

- Phase 1.1 continues to use the **front‑end upsert** path built in P1.0:
  - On sign‑up / first visit: `insert` or `upsert` profile with `handle`, `display_name`, `avatar_key`, `role`.
  - On settings change: update `display_name`, `handle`, `avatar_key`.
- Role sync for v1:
  - We assume role changes happen rarely.
  - When `user_metadata.role` is updated via admin SQL, **an additional SQL update** should be run to keep `profiles.role` in sync (manual but simple).
  - A trigger‑based auto‑sync could be added later.

---

### B3. RLS and Security

High‑level RLS expectations on `profiles` (details live in the DB itself):

- **Select**:
  - Public read of basic profile fields is allowed: `handle`, `display_name`, `avatar_key`, `role` (treated as a non‑secret flag), `created_at`.
  - For v1, we do **not** expose contact details or any private fields in `profiles`.
- **Insert/Update**:
  - Only the **authenticated user** can insert/update their own profile row:
    - `auth.uid() = profiles.id`.
- **Delete**:
  - No one deletes profiles directly via the app; account deletion is handled later as a separate flow.

---

## C. SQL / Setup Tasks (high‑level list)

This section only lists the operations; detailed SQL can be written from this.

1. **Add role + moderation columns to `profiles`**  
   - `ALTER TABLE public.profiles ADD COLUMN role text NOT NULL DEFAULT 'user';`  
   - `ALTER TABLE public.profiles ADD COLUMN is_banned boolean NOT NULL DEFAULT false;`

2. **Backfill existing profiles with canonical role**  
   - For now, run manual updates:
     - Set `role = 'admin'` for known admin user IDs.
     - Set `role = 'mod'` for known moderator user IDs (if any).
     - Ensure all others are `'user'`.

3. **Ensure RLS policies still work as intended**  
   - Confirm:
     - Anonymous users can only `SELECT`.
     - Authenticated users can `INSERT/UPDATE` their own row only.

4. **Seed admin roles in `auth.users.user_metadata`** (manual SQL already tested):
   - For each admin/mod, set `user_metadata->>'role'` appropriately.
   - Ensure `profiles.role` matches.

5. **Create a placeholder `public.admin_events` table (optional but recommended)**  
   - Columns like:
     - `id bigserial primary key`
     - `actor_id uuid not null references auth.users (id)`
     - `action text not null` (e.g., `'set_role'`, `'ban_user'`)
     - `target_user_id uuid`
     - `details jsonb`
     - `created_at timestamptz default now()`  
   - Used later for audit logging; v1 may only collect a small subset of actions.

---

## D. Pages and Routes

Phase 1.1 introduces / clarifies these routes:

1. **Existing Account pages (no major new UI)**  
   - `/account/` – My Testimony page, with avatar, handle, “Share your testimony”, and testimony scaffolding.
   - `/account/settings/` – Profile settings (display name, handle, email, password, avatar selection).
   - `/u/` – Public profile view by handle query (`?handle=…`), to be fully wired in the testimony phases.

2. **New Admin scaffolding routes** (v1.1 shells only):

   - `/admin/` – Main entry for admins/mods.  
     - v1 contents: simple dashboard stub (“You are signed in as admin/mod; tools coming soon”), plus links to child pages.

   - `/admin/accounts/` – Placeholder page for future account lookup / management.
   - `/admin/content/` – Placeholder for future testimony / report queues.

Routing rules (front‑end only):

- Non‑signed‑in users hitting `/admin/*` should be redirected to `/account/sign-in/`.
- Signed‑in users with `role: 'user'` should see a “not authorised” panel (no leaks about internal tools).
- `mod` and `admin` users may access the stub pages.

---

## E. Supabase Wiring (Behaviour, not code)

1. **Role‑aware client context**  
   - On every authenticated page load (`site.js` global or page‑specific JS):
     - Fetch `supabase.auth.getUser()`.
     - Read `user.user_metadata.role` (default `'user'` if missing).
     - Attach `window.SHK_ROLE` or equivalent for conditional UI (e.g., showing admin links in the header).

2. **Admin routing guard**  
   - Admin pages should:
     - Redirect to sign‑in if `!user`.
     - Show “not authorised” if `role === 'user'`.
     - Load normal content only if `role === 'mod' || role === 'admin'`.

3. **Avatar gating**  
   - In the avatar picker:
     - Filter `window.SHK_PROFILE_AVATARS` by `adminOnly` and role.
     - If a user somehow has an Admin‑only avatar but `role !== 'admin'`:
       - Front‑end should gracefully fall back to a regular avatar or initial.

4. **Profiles sync**  
   - Each time the settings page updates handle / display name / avatar:
     - Call `supabase.auth.updateUser()` for metadata.
     - Then `upsert` into `public.profiles` to keep the mirror in sync.

---

## F. Public vs Private Data

**Private (Auth / internal):**

- Email, password, login history (all in `auth.users`).
- Admin audit events (future `admin_events` table).
- Any per‑account flags that are not meant to be public (bans, internal notes).

**Public (exposed via site):**

- `handle` – Public identifier, appears in URLs.
- `display_name` – Public display name.
- `avatar_key` – Drives public avatar image selection.
- `role` – May be used for small visual cues (e.g., a subtle “team” badge), but not for status/follower gamification.
- These are always subject to future content rules (no offensive handles, etc.).

---

## G. QA and Monitoring

**Functional checks:**

1. **Role defaults:**
   - Create a new account; verify `user_metadata.role` is missing or `'user'`, and `profiles.role` resolves to `'user'`.

2. **Admin / mod detection:**
   - Mark one user as `'admin'` and one as `'mod'` via SQL.
   - Confirm:
     - `/admin/` loads for them.
     - Regular users see a “not authorised” state.
     - Anonymous users are redirected to sign‑in.

3. **Avatar gating:**
   - Confirm non‑admins never see Admin‑only avatar options.
   - Confirm admins can select special avatars and they render in header + account page.

4. **RLS:**
   - From the console, test that signed‑out `supabaseAnonClient` cannot insert/update `profiles`.
   - Test that a signed‑in user can only update their own `profiles` row.

**Monitoring / post‑launch:**

- Track:
  - Number of profiles with each `role` value.
  - Any anomalies in `admin_events` once wired.
  - Error logs from `/admin/*` pages (e.g., failed role checks).

---

## H. Versioning and Relation to Other Phases

- This contract **extends** ACC‑P1.0 and assumes it is fully implemented and QA’d.
- It must be complete before:
  - Testimony modules rely on role/moderation logic.
  - Any community / reporting / moderation tooling is exposed.
- Identifier: `ACC-P1.1`.  
  - When substantially updated, bump to `ACC-P1.1.1`, etc., and keep change notes at the top.

