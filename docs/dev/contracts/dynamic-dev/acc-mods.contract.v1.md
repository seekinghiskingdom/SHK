Here is an updated, consolidated ACC-P1.1 contract reflecting everything we’ve actually implemented/configured so far (roles, profiles, avatars, singleton Supabase client, and the new `admin_config` + admin pages). 

---

# SHK Accounts – Phase 1.1 Contract (Updated)

**Tag:** ACC-P1.1 – Roles, Profiles, Admin Config, and Admin Scaffolding
**Status:** v1.0 (implemented baseline; future edits bump to ACC-P1.1.x)

---

## A. Scope and Goals

Phase 1.1 extends ACC-P1.0 and introduces:

1. A **small, explicit role model** (`user`, `mod`, `admin`) that is:

   * Source-of-truth in `auth.users.user_metadata.role`.
   * Mirrored in `public.profiles.role` for querying and UI.
2. A **singleton Supabase client** (`window.shkSupabase`) used across the site to avoid multiple GoTrue instances.
3. A **global avatar registry** (`window.SHK_PROFILE_AVATARS`) with reserved admin-only avatars.
4. A new **`admin_config` table** holding global moderation settings (review-all toggle, report thresholds, etc.) wired to `/admin/`.
5. Minimal, role-gated **admin scaffolding pages**:

   * `/admin/` – global moderation settings UI (read-only for mods; editable by admins).
   * `/admin/accounts/` – read-only account list for mods/admins.
6. No user-facing “fancy” features yet (no full moderation queues, no rich account management); this phase is infrastructure for later Testimony/Community phases.

Out of scope: full report queues, strike dashboards, per-post moderation UI, or full testimony tooling (covered under the moderation + Testimony module contracts).

---

## B. Data Model

### B1. `auth.users.user_metadata` (source of truth)

Supabase Auth remains the identity system. ACC-P1.1 standardises these metadata keys:

* `display_name: string | null`
* `handle: string | null`

  * Canonical username; pattern: `^[a-z0-9_-]{3,24}$`.
* `avatar_key: string | null`

  * e.g. `"avatar-7"`, `"avatar-998"`.
* `role: "user" | "mod" | "admin"`

  * Default: `"user"` for all normal sign-ups.
  * Only set/changed via trusted paths: SQL in dashboard and future `/admin/` UI.
* Reserved (not yet implemented but reserved):

  * `onboarded: boolean`
  * `terms_version: string`

Notes:

* Role is authoritative here. `profiles.role` is a **mirror**, not the source of truth.
* Admin-only avatars (e.g. SHK logos) are enforced via role checks and the avatar registry.

---

### B2. `public.profiles`

`profiles` mirrors public account information and adds a couple of moderation flags.

Required schema (post-P1.1):

* `id uuid primary key references auth.users (id)`
* `handle text unique not null` – canonical username (required once created).
* `display_name text` – last known display name.
* `avatar_key text` – last chosen avatar key.
* `role text not null default 'user'`

  * Allowed: `'user'`, `'mod'`, `'admin'`.
  * Maintained to match `user_metadata.role`.
* `is_banned boolean not null default false`

  * Soft ban flag; enforcement comes in moderation phases.
* `created_at timestamptz not null default now()`
* `updated_at timestamptz not null default now()`

Behaviour:

* P1.0/P1.1 continue to use a **front-end upsert** path:

  * On settings change, call `supabase.auth.updateUser()` and then upsert into `profiles`.
  * On first handle assignment, create/upsert the profile row.
* Role sync (v1 baseline):

  * Role changes are **rare and manual**.
  * When an admin updates `user_metadata.role` (via SQL/dashboard), they also update `profiles.role` with a simple SQL statement.
  * A trigger-based auto-sync can be added later.

---

### B3. `public.admin_config` (new global moderation settings)

This table holds the **single row** of global moderation configuration that admins can edit via `/admin/`.

Suggested schema (implemented):

* `id uuid primary key default gen_random_uuid()`
* `review_all boolean not null default false`

  * If `true`, all new testimonies/posts must be reviewed before publication.
* `mod_can_final_accept boolean not null default true`

  * If `true`, moderators can fully restore content to public without admin re-approval.
* `mod_can_final_reject boolean not null default false`

  * If `false`, only admins can finalize a “violation” decision that counts toward strikes.
* `reports_required_for_hide integer not null default 2`

  * Unique user reports required to auto-hide content pending review.
* `sensitivity_toggle_enabled boolean not null default true`

  * Enables per-user “hide sensitive content” toggles.
* `abuse_reports_threshold integer not null default 7`

  * Lifetime violation/strike threshold for permanent ban recommendation.
* `abuse_reports_window_days integer not null default 30`

  * Time window used by “X violations in Y days” logic for temporary suspensions.
* `created_at timestamptz not null default now()`
* `updated_at timestamptz not null default now()`

Assumptions:

* For v1 there is **exactly one row**. The `/admin/` page:

  * Fetches `.select('*').limit(1).single()`.
  * Uses that row’s `id` when updating.
* Values are authoritative and should be read by any future moderation/Testimony logic.

RLS (high-level intent):

* Public/anonymous: **no access**.
* Authenticated:

  * Only users with `role = 'mod'` or `'admin'` may `select`.
  * **Only admins** may `update`.
* For v1, it is acceptable if we enforce this partly via front-end gating plus dashboard policy; proper RLS policies are expected before heavy use.

---

### B4. `public.admin_events` (optional audit log placeholder)

Recommended but not yet heavily used:

* `id bigserial primary key`
* `actor_id uuid not null references auth.users (id)`
* `action text not null` – e.g. `'set_role'`, `'ban_user'`, `'update_admin_config'`
* `target_user_id uuid` – optional
* `details jsonb` – arbitrary structured payload
* `created_at timestamptz not null default now()`

Usage:

* Only trusted roles can `insert`.
* Used later to audit role changes, bans, and major moderation actions.

---

## C. Supabase Client and JS Integration

### C1. Singleton client (`window.shkSupabase`)

To avoid multiple GoTrue instances (and the warning we saw), the site must use a **single Supabase client** per browser context:

* In the **global site JS** (`site.js`):

  ```js
  if (window.supabase && !window.shkSupabase) {
    const SUPABASE_URL = 'https://vubmekxghtydatmofsit.supabase.co';
    const SUPABASE_PUBLISHABLE_KEY = 'sb_publishable_…'; // publishable key

    window.shkSupabase = window.supabase.createClient(
      SUPABASE_URL,
      SUPABASE_PUBLISHABLE_KEY
    );
  }
  ```

* All page-specific scripts (account pages, admin pages, etc.) must follow:

  ```js
  if (!window.supabase || !window.supabase.createClient) {
    // show "Supabase unavailable" message
    return;
  }
  const supabase = window.shkSupabase;
  if (!supabase) {
    // show "client not available" message
    return;
  }
  ```

* **No page** should call `window.supabase.createClient(...)` directly anymore, except the single initialization block in `site.js`.

### C2. Global avatar registry

`site.js` exposes a global registry and helper:

* `window.SHK_PROFILE_AVATARS: { key, src, adminOnly }[]`

  * For IDs 1–123: `key: "avatar-N"`, `src: `${SHK_BASEURL}/img/profiles/N.png`, `adminOnly: false` (unless explicitly reserved).
  * Two explicit SHK logos: `avatar-998`, `avatar-999` with `adminOnly: true`.
* `window.SHK_getAvatarUrlByKey(key)`

  * Returns `src` for a given key or `null` if unknown.

This registry is:

* Used by `/account/settings/` to build the avatar grid.
* Used by `/account/` and the header account pill to resolve avatars from metadata.

### C3. Header account pill

The header pill:

* Uses `window.shkSupabase` to call `supabase.auth.getUser()`.
* Defaults to “Sign in” (✝ initial) and link `/account/sign-in/` if no user.
* For signed-in users:

  * Resolves avatar via `avatar_key` → `SHK_getAvatarUrlByKey`.
  * Falls back to initial from `display_name` or email.
  * Links to `/account/`.

This logic must not create a second client and must not make admin-only avatars visible for non-admins.

---

## D. Pages and Routes

### D1. Existing account pages (P1.0 + P1.1 refinements)

1. `/account/` – “My Testimony” hub

   * Uses `window.shkSupabase` to:

     * Detect signed-in vs signed-out.
     * Display display_name, handle, avatar, and share link (when handle is set).
     * Manage **inline salvation testimony** stored in `user_metadata.salvation_testimony`.
   * Behaviour:

     * Signed-out: explanatory copy and “Sign In” CTA.
     * Signed-in:

       * If `handle` present: show share button that copies `/u/?handle=…`.
       * If no `handle`: hide share button and show “pick a username” prompt.
       * Salvation testimony editor:

         * Uses `supabase.auth.updateUser({ data: { salvation_testimony } })`.
         * Provides basic UX (“Write testimony” / “Edit testimony”, save/cancel, error handling).

2. `/account/settings/`

   * Uses `window.shkSupabase` to:

     * Show email, display name, handle.
     * Allow updates to display name and handle.
     * Upsert `profiles` row (with `id`, `handle`, `display_name`, `avatar_key`, `role` mirror).
     * Change email and password via `supabase.auth.updateUser()`.

   * Validation:

     * Display name 2–40 chars.
     * Handle pattern `^[a-z0-9_-]{3,24}$`.
     * Handle uniqueness enforced via `profiles.handle` unique constraint (error surfaced in UI).

   * Avatar picker:

     * Builds grid from `window.SHK_PROFILE_AVATARS`.
     * Hides `adminOnly` avatars from non-admins.
     * Writes `avatar_key` to `user_metadata` with `supabase.auth.updateUser`.
     * Non-admins are additionally blocked from saving admin-only keys (double guard).

3. `/u/` – public profile (by handle)

   * Contract-level expectation:

     * Reads from `public.profiles` where `handle = :handle`.
     * Shows handle, display_name, avatar, and public testimony footprint.
   * Full UI wiring is in the Testimony phase; for ACC-P1.1 it’s enough that this route and design expectations exist.

### D2. New admin routes (P1.1)

1. `/admin/` – global moderation config UI

   * Front-end gate:

     * Uses `window.shkSupabase` and `auth.getUser()`.
     * If no user: show “you must be signed in” and do **not** fetch config.
     * If `role === 'user'`: show “not authorised”.
     * If `role === 'mod'` or `'admin'`: fetch `admin_config` and show form.
   * Behaviour:

     * Mods: values are loaded and fields are **disabled** (read-only view). Save button disabled.
     * Admins:

       * Form values populated from `admin_config` row.
       * On submit, `supabase.from('admin_config').update(payload).eq('id', config.id)`.
       * Status text: “Saving settings… / Settings updated / Error saving…”.
   * Fields:

     * `review_all` (checkbox).
     * `reports_required_for_hide` (number).
     * `mod_can_final_accept` (checkbox).
     * `mod_can_final_reject` (checkbox).
     * `sensitivity_toggle_enabled` (checkbox).
     * `abuse_reports_threshold` (number).
     * `abuse_reports_window_days` (number).

2. `/admin/accounts/` – read-only accounts table

   * Gate:

     * Same user/role checks as above.
     * Signed-out → “You are not signed in”.
     * `role === 'user'` → “Not authorised” block.
     * `role in ('mod','admin')` → show content.
   * Behaviour:

     * Shows **current session**: email + role from `user_metadata.role`.
     * Queries `public.profiles`:

       ```js
       supabase
         .from('profiles')
         .select('email, handle, role, created_at')
         .order('created_at', { ascending: false })
         .limit(50);
       ```

       (If `email` is not in `profiles`, this column can be removed in favour of handle only.)
     * Table is read-only; all role changes and bans still occur in Supabase dashboard for v1.

---

## E. RLS and Security (High-Level)

### E1. `public.profiles`

Intent (some may already be implemented from P1.0):

* Anonymous:

  * `SELECT` allowed for public fields: `handle`, `display_name`, `avatar_key`, `role`, `created_at`.
* Authenticated:

  * `SELECT` same as above.
  * `INSERT` / `UPDATE` allowed only when `profiles.id = auth.uid()`.
* `DELETE`:

  * No app path; handled by future account-deletion logic if ever needed.

### E2. `public.admin_config`

Intent:

* Anonymous: no access.
* Authenticated:

  * `SELECT` restricted to users where `user_metadata.role IN ('mod','admin')`.
  * `UPDATE` restricted to users where `role = 'admin'`.
* If RLS is not fully wired, the **front-end gating** and Supabase dashboard discipline must be honoured until policies are in place.

### E3. `public.admin_events`

Intent:

* `INSERT` restricted to `role IN ('mod','admin')`.
* `SELECT` restricted to `role = 'admin'` (or also `mod` depending on future needs).
* No app-level delete.

---

## F. QA and Monitoring Checklist

### F1. Functional checks

1. **Role defaults**

   * Create a new user.
   * Confirm:

     * `user_metadata.role` is absent or `'user'`.
     * `profiles.role` ends up `'user'`.

2. **Admin routing**

   * Mark one account as `role = 'admin'` and another as `role = 'mod'` (via SQL + profiles backfill).
   * Logged out:

     * `/admin/` and `/admin/accounts/` show sign-in requirement.
   * Logged in as normal `user`:

     * Both routes show “not authorised” block.
   * Logged in as `mod`:

     * `/admin/`: settings visible, form fields disabled, “read-only” note visible.
     * `/admin/accounts/`: account table loads.
   * Logged in as `admin`:

     * `/admin/`: form fields editable and persist to `admin_config`.
     * `/admin/accounts/`: account table loads.

3. **Singleton client behaviour**

   * DevTools console: confirm **only one** `GoTrueClient` instance is created.
   * Ensure no direct `createClient` calls remain in page scripts (search for `createClient(`).

4. **Avatar gating**

   * As non-admin:

     * Avatar picker shows only non-admin avatars.
     * Even if someone tries to set `avatar-998` manually, front-end rejects or reverts.
   * As admin:

     * Admin-only avatars (e.g. SHK logo) visible and selectable.
     * Header pill and account page render them correctly.

5. **Profiles upsert**

   * Change display name, handle, and avatar in `/account/settings/`.
   * Confirm:

     * `auth.users.user_metadata` updated.
     * `public.profiles` row updated or created with matching fields.

6. **Admin config persistence**

   * As admin:

     * Change `review_all`, thresholds, etc.
     * Confirm row in `admin_config` updates.
   * As mod:

     * Confirm values reflect latest state but are not editable.

### F2. Monitoring

After launch of P1.1:

* Periodically inspect:

  * `profiles.role` vs `user_metadata.role` for drift.
  * `admin_config` row for unexpected changes.
  * Any `admin_events` (once wired) for suspicious activity.
* Track metric counts:

  * Number of admins/mods.
  * Number of banned accounts (`is_banned = true`).

---

## G. Versioning and Dependencies

* This document **extends and depends on** ACC-P1.0 (basic accounts, sign-up, sign-in).
* It should be treated as **implemented baseline** for:

  * Testimony module v1 (wall, add, personal testimony pages).
  * Moderation & reporting module (which will lean on `admin_config`, roles, and `is_banned`).
* Identifier: `ACC-P1.1`.

  * Non-breaking tweaks → `ACC-P1.1.1`, etc., with a short change log at top.
