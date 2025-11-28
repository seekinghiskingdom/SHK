# SHK Accounts and User Data – v1 Contract (v1.0)

> Single source of truth for how SHK accounts, core user data, and roles work in v1.  
> This updates and replaces “Draft v0.9”.

---

## 0. Scope and non-goals

### 0.1 In-scope for v1.0

This contract covers:

- **Authentication & identity**
  - Email/password sign-up and sign-in
  - Email confirmation and password reset flows
- **Canonical profile data**
  - Public-facing profile info (handle, display_name, avatar)
  - Minimal per-account flags (role, onboarding flags)
- **Roles & moderation foundation**
  - `user`, `mod`, `admin` roles, stored in `public.profiles`
  - Admin-only avatars
- **Core pages & wiring**
  - `/account/` (My Testimony / profile home)
  - `/account/settings/`
  - `/account/sign-in/`, `/account/sign-up/`, `/account/confirm/`
  - `/u/` public profile (by handle)
- **Supabase schema, RLS, and high-level wiring**
  - `auth.users` usage (metadata only)
  - `public.profiles` table and RLS shape
  - Basic admin tooling via SQL + future `/admin/` pages

### 0.2 Out-of-scope (future contracts)

These will be defined in their own module contracts and only *reference* this account spec:

- Testimony system (salvation testimony + other testimonies) and Testimony Wall
- Daily module (streaks, completion, reflection storage)
- Bible Viewer per-user state (bookmarks, highlights, last-place-read)
- Language-learning tools, SCS/BLL state, PPS saved data
- Full moderator/admin dashboards (`/admin/*`), report queues, etc.

---

## 1. Mental model and responsibilities

### 1.1 Supabase vs Jekyll

- **Jekyll/GitHub Pages**
  - Static HTML/CSS/JS (no secrets in repo)
  - Calls Supabase from the browser (publishable key only)
  - Renders account and profile UI based on data returned from Supabase
- **Supabase**
  - Auth: email/password sign-up, email confirmation, password reset
  - DB: `public.profiles` and later testimony-related tables
  - Security: RLS + policies to ensure users can only see/modify what is appropriate

### 1.2 Where account data lives

- **`auth.users`** (Supabase-managed, private, not directly exposed on site):
  - Email, hashed password, confirmation state, last_sign_in, etc.
  - A *small* `user_metadata` JSON used at **auth-time only**, not as the canonical source.
- **`public.profiles`** (SHK-managed, canonical profile record):
  - One row per user, keyed by `auth.users.id`
  - Fields used by profile pages, testimonies, and future modules
  - Queried by: handle, role, id

**Key rule:** `auth.user().user_metadata` is treated as a convenience cache; `public.profiles` is the source of truth for profile info and roles.

---

## 2. Data model

### 2.1 `auth.users` (Supabase auth)

SHK does **not** modify this schema directly; we only rely on:

- `id` – UUID for the user (primary identity key)
- `email` – login + contact address
- `user_metadata` – JSON bag for simple fields at sign-up or user updates
- Standard timestamps: `created_at`, `confirmed_at`, `last_sign_in_at`, etc.

#### 2.1.1 Allowed `user_metadata` keys (v1.0)

These may be written via `supabase.auth.signUp` / `supabase.auth.updateUser`:

- `display_name` – optional, 2–40 chars; not canonical, but used for convenience
- `handle` – optional; canonical handle lives in `public.profiles.handle`
- `avatar_key` – optional; canonical avatar lives in `public.profiles.avatar_key`

Down the line, we will **sync** into `public.profiles` and eventually stop depending on `user_metadata` except as a bridge.

### 2.2 `public.profiles` (canonical profile table)

Schema (SQL-level; types may be tuned during implementation):

- `id` (uuid, PK)
  - Matches `auth.users.id` 1:1.
- `created_at` (timestamptz, default `now()`)
- `updated_at` (timestamptz, default `now()` via trigger)

- `email` (text, nullable)
  - May be stored for convenience or left null; **not** required for public display.

- `display_name` (text, nullable)
  - Optional human-readable name; 2–40 chars enforced at UI layer.

- `handle` (citext or text with unique index, nullable)
  - User-chosen unique handle for public profile, e.g. `hunter123`.
  - Constraint: lowercased, 3–24 chars, `[a-z0-9_]` only.
  - Used in URLs: `/u/?handle=…` in v1.0; can later become `/u/handle/`.

- `avatar_key` (text, nullable)
  - Key into the `SHK_PROFILE_AVATARS` list in front-end code, e.g. `avatar-7` or `avatar-998`.
  - UI enforces which keys are selectable (e.g., admin-only avatars).

- `role` (text, not null, default `'user'`)
  - Enum-like: `'user' | 'mod' | 'admin'` for v1.x.
  - This is the canonical application role; UI and permissions MUST use this field.
  - Detailed semantics are defined in the Roles & Account Management contract (ACC-ROLES v1.x).

- `account_status` (text, not null, default `'active'`)
  - CHECK at DB layer:
    - `'active'`
    - `'suspended_pending_review'`
    - `'suspended'`
    - `'banned_pending_review'`
    - `'banned'`
  - Drives "active vs read-only" behavior across modules; detailed semantics in ACC-ROLES / Moderation contract (ACC-MOD).

- `strike_count` (integer, not null, default `0`)
  - Lifetime count of confirmed violations (strikes) for this account.
  - Used by moderation logic to trigger suspensions/bans.

- `show_sensitive` (boolean, not null, default `true`)
  - User preference for whether to see content marked as sensitive.
  - v1 does not implement age-based defaults; that is reserved for a future extension.

- `is_active` (boolean, not null, default `true`)
  - Legacy/soft-disable flag.
  - For v1, `account_status` is primary; `is_active` is reserved for potential hard-deactivation or system-level deactivation.

- `onboarding_step` (smallint, nullable)
  - Simple marker for onboarding progress (optional in v1.0).

- `notes` (text, nullable)
  - Admin-only comments (not surfaced in UI in v1.0).

Indexes / constraints:

- `PK(id)`
- `UNIQUE(handle)` on lowercased handle
- Index on `role` for quick admin/mod listing
- Index on `account_status` for moderation and admin views
- Optional: index on `display_name` to speed up search

**Authority note:** For roles, account status, strikes, and sensitivity preference, `public.profiles` is the single source of truth. Any values mirrored into `auth.users.user_metadata` are considered a convenience cache only.
### 2.3 Roles and semantics

- `user`
  - Default for all new accounts.
  - Can create/edit own testimonies, daily data, etc. (as modules are added).
- `mod`
  - Trusted helpers (family/friends/team).
  - Can do limited moderation tasks (testimony reviews, reports) in later phases.
- `admin`
  - Full control over moderation and account management.
  - Can change roles, deactivate accounts, see certain flags.

Role is stored only in `public.profiles.role` and is authoritative for UI and permissions.

### 2.4 Avatar catalogue

Front-end definition (in `site.js`):

- `window.SHK_PROFILE_AVATARS` – array of `{ key, src, adminOnly? }`:
  - Standard avatars: `avatar-1` through `avatar-123` → `/img/profiles/1.png` etc.
  - Reserved SHK admin avatars: e.g. `avatar-998`, `avatar-999` with `adminOnly: true`.
- `window.SHK_getAvatarUrlByKey(avatarKey)` – helper for lookup.

Back-end rules:

- `public.profiles.avatar_key` can hold any key in that list.
- Front-end hides admin-only options from non-admin users in the avatar picker UI.
- Extra guard: if a non-admin somehow stores an `adminOnly` key, the UI treats it as invalid and falls back to an initial.

---

## 3. Pages and flows (v1.0)

### 3.1 Auth pages

1. **Sign up** – `/account/sign-up/`
   - Fields:
     - `display_name` (optional)
     - `handle` (required, validated client-side)
     - `email` (required)
     - `password` (required, min 8)
   - On submit:
     - Call `supabase.auth.signUp` with `email`, `password`, and `user_metadata` (`display_name`, `handle`).
     - Email redirect: `/account/confirm/` after confirmation.
   - Errors displayed inline.

2. **Sign in** – `/account/sign-in/`
   - Fields: `email`, `password`.
   - On success:
     - Redirect to `/account/`.

3. **Confirm** – `/account/confirm/`
   - Landing page for Supabase email confirmation redirect.
   - Simple message: success / error and link to `/account/sign-in/`.

4. **Reset password** – `/account/reset/` (name may vary)
   - Triggered via Supabase “reset password” email.
   - v1.0: minimal skin over Supabase default flow (or simple note with link).

### 3.2 Account “My Testimony” home – `/account/`

Serves as the logged-in user’s personal home:

- Header block:
  - Avatar (circle) with image or initial.
  - Display name and `@handle` line.
  - Buttons:
    - `Account settings` → `/account/settings/`
    - `Sign out` → Call `supabase.auth.signOut()` and redirect to `/account/sign-in/`.
- Sharing buttons:
  - `Share your testimony` – copies the public profile URL (`/u/?handle=…`) to clipboard.
  - `See all testimonies` – links to `/testimony/wall/`.
- Salvation testimony section:
  - Title: `My Salvation Testimony` + help toggle (`?`).
  - Help panel: static guidance text (non-stored) with questions/prompts.
  - Buttons:
    - `Write my salvation story` – for v1.0, goes to `/testimony/#write-salvation` or opens inline editor (Phase 1.1 testimony module).
    - `Learn more about salvation & testimonies` – links to `/testimony/` hub.
- Other testimonies section:
  - Tabs: All / Prayers / Blessings / Miracles / General / Private drafts / + Testimony
    - `+ Testimony` → `/testimony/add/` (phase 2).
    - Tabs themselves will be wired once testimony module exists.

If user is not signed in, `/account/` shows a “please sign in” state and a button to `/account/sign-in/`.

### 3.3 Account settings – `/account/settings/`

For logged-in users to change profile info and credentials.

Sections:

1. **Profile** (display_name + handle):
   - Inputs: `display_name`, `handle`.
   - Validations:
     - `display_name` 2–40 chars if present.
     - `handle` 3–24 chars, lowercase letters, numbers, underscores (`^[a-z0-9_]{3,24}$`).
   - On save:
     - `supabase.auth.updateUser({ data: { display_name, handle } })` for metadata convenience.
     - Future Phase: upsert to `public.profiles`.

2. **Avatar**:
   - Grid of allowed avatars from `SHK_PROFILE_AVATARS`.
   - Admin-only avatars hidden for non-admin.
   - On save:
     - `supabase.auth.updateUser({ data: { avatar_key } })`.
     - Future Phase: upsert to `public.profiles.avatar_key`.

3. **Email**:
   - Field: `new_email`.
   - On submit:
     - `supabase.auth.updateUser({ email: new_email })`.
     - Supabase sends confirmation link.

4. **Password**:
   - Fields: `new_password`, `confirm_password`.
   - On submit:
     - `supabase.auth.updateUser({ password: new_password })`.

If `supabase.auth.getUser()` returns no user, the page displays a signed-out message and links to `/account/sign-in/` and `/account/sign-up/`.

### 3.4 Public profile – `/u/`

- Query parameter: `?handle=…`.
- v1.0 minimal behavior:
  - Look up in `public.profiles` by `handle` (once populated).
  - Show avatar, display_name, `@handle`, and eventually testimonies (testimony module).
  - If handle not found, show custom “This user does not exist” message and maybe link to `/account/sign-up/`.

Later we may move to path-based URLs like `/u/{handle}/`, but v1.0 uses query param for simplicity.

---

## 4. Supabase schema & RLS

### 4.1 `public.profiles` creation (outline)

High-level (not executable SQL here, just intent):

- Create table with columns in §2.2, PK on `id`.
- Add unique index on `lower(handle)`.
- Add index on `role`.
- Trigger to auto-update `updated_at` on row changes.

### 4.2 RLS strategy (v1.0)

- **Enable RLS** on `public.profiles`.

Policies:

1. **Select public profiles**
   - Allow `SELECT` for all (anon + authenticated) on limited fields needed for public display.
   - Implementation detail: either
     - Use a `SECURITY DEFINER` function and only expose safe columns, or
     - Keep `profiles` lightweight and explicitly avoid sensitive fields.
2. **Select own profile**
   - Allow authenticated users to `SELECT` their own row by matching `auth.uid()` to `profiles.id`.
3. **Update own profile**
   - Allow authenticated users to `UPDATE` their own row, but only on allowed columns:
     - `display_name`, `handle`, `avatar_key`, maybe some onboarding flags.
4. **Admin override**
   - Allow users where `role = 'admin'` (or a separate mechanism like `auth.jwt` claim) to `SELECT` and `UPDATE` any row.
   - This is the foundation for `/admin/` tooling.

Exact SQL will be written when we implement the schema; this contract only defines intent.

### 4.3 Initial backfill and sync

For existing users created before `public.profiles`:

- Write a one-off SQL or script to:
  - Iterate all `auth.users`.
  - For each user that has no `profiles` row, insert one:
    - `id` = auth.id
    - `email` = auth.email
    - `display_name`, `handle`, `avatar_key` from `user_metadata` if present.
    - `role` default `'user'` unless manually set for admins.
- For Hunter + trusted admins, manually set `role = 'admin'` or `role = 'mod'` via SQL or future admin UI.

Long term, we may add a trigger or scheduled job so that changes to `auth.user().user_metadata` are mirrored into `public.profiles` or vice versa. That will be specified in a small “sync” sub-contract when needed.

---

## 5. Front-end wiring (high level)

### 5.1 Header account pill

- Uses `supabase.auth.getUser()` to determine signed-in state.
- If signed out:
  - Show `Sign in` text button → `/account/sign-in/`.
- If signed in:
  - Show circular avatar with image or initial using `avatar_key` from metadata/profiles.
  - Clicking opens `/account/`.

### 5.2 Account + settings pages

- Both pages call `supabase.auth.getUser()` on load.
- Account page:
  - Uses `email`, `display_name`, `handle`, `avatar_key` to populate header.
  - Uses `handle` to build share URL.
- Settings page:
  - Before we have `public.profiles`, uses `supabase.auth.updateUser` to update metadata.
  - After `public.profiles` exists, we may:
    - Read current values from `public.profiles`.
    - Write via a small RPC or direct `update` on `public.profiles` where allowed by RLS.

### 5.3 Public profile page

- Anonymous or authenticated users can view.
- For v1.0, minimal behavior:
  - Accept `handle` query param.
  - Fetch profile data via a Supabase query (once RLS allows it).
  - Render avatar, names, and placeholders for testimonies.

---

## 6. Monitoring, QA, and post-deploy checks

### 6.1 Phase 1.0 QA checklist

Before calling Accounts v1.0 “done”:

1. **Auth flows**
   - Sign up with new email:
     - Requires handle that passes validation.
     - Sends confirmation email.
     - After confirm, can sign in successfully.
   - Sign in errors behave cleanly (wrong password, unconfirmed email).
2. **Account page**
   - Signed-out users:
     - See a clear prompt to sign in or sign up.
   - Signed-in users:
     - See avatar, display_name, and `@handle` as expected.
     - `Share your testimony` copies the correct `/u/?handle=…` URL when handle is set.
     - `See all testimonies` links to `/testimony/wall/`.
3. **Settings page**
   - Display name and handle:
     - Validation messages show for invalid input.
     - Updating fields persists across refresh and new sessions.
   - Avatar selection:
     - Standard avatars selectable for all users.
     - Admin-only avatars only visible/usable for admin accounts.
   - Email and password changes:
     - Trigger Supabase flows without breaking sessions unexpectedly.
4. **Public profile (interim)**
   - `/u/?handle=valid` shows something reasonable (even if just a placeholder block).
   - `/u/?handle=missing` shows “user not found” message.
5. **Security sanity checks**
   - Confirm publishable key only in repo and config.
   - No Supabase service key or Google Workspace credentials in HTML/JS.
   - `public.profiles` RLS enabled (once created) and basic policies working in local tests.

### 6.2 Post-deploy monitoring

Once live, we will:

- Watch Supabase dashboard for:
  - Auth errors (sign-up/sign-in failures, rate-limiting issues).
  - Policy errors when accessing future `public.profiles` endpoints.
- Track:
  - Number of accounts created.
  - Frequency of confirmation emails and password reset requests.
- Collect manual feedback from early users (family, close friends) on:
  - Confusion in sign-up or sign-in flows.
  - Handle/display name expectations.
  - Avatar picker usability.

Any issues here feed into Phase 1.1 adjustments.

---

## 7. Phase roadmap for Accounts

This contract is **Phase 1.0 – Core Accounts**. Later documents will extend it:

- **Phase 1.1 – Roles & Admin/Mod Tools**
  - Flesh out `role` semantics and RLS-based permissions.
  - `/admin/` and `/manage/` entry points.
  - Simple dashboard for viewing profiles, changing roles, and performing soft actions (deactivate, reset flags, etc.).
- **Phase 2 – Testimony Module**
  - Separate contract defining testimony tables and how they join to profiles.
  - Public vs private testimonies, Testimony Wall behavior, “follow” system.
- **Phase 3 – Daily Module**
  - Per-user daily streaks, completion flags, and reflection storage.
- **Phase 4+ – Tool-specific state**
  - Bible Viewer bookmarks, SCS/BLL sets, etc.

Each subsequent module contract will **depend on** this v1.0 account contract rather than redefining user data.

---

## 8. Versioning

- This file: **SHK Accounts and User Data – v1 Contract (v1.0)**.
- Stored in repo as: `docs/data/contracts/user_account_data.v1.contract.md` (or equivalent path).
- Changes that affect DB schema, RLS, or public behavior require:
  - Version bump (e.g. v1.1, v1.2).
  - Changelog entry near the top summarizing what changed and migration steps if needed.
