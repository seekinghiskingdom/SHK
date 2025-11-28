## 1) SHK Roles & Account Management Contract (ACC-ROLES v1.0)

### A. Purpose & Scope

This document defines the role system, account states, and high-level management rules for the Seeking His Kingdom (SHK) platform.
It is an internal technical contract intended to guide:

* Backend schema and RLS design
* Frontend behavior and gating
* Future formal documents (Terms & Conditions, Community Guidelines, Privacy Policy)

Moderation-specific mechanics (reports, queues, strikes, etc.) are defined in the separate **Moderation & Safety Contract (ACC-MOD v1.0)** and referenced here only at a high level.

---

### B. Core Concepts & Definitions

1. **Account / Auth record**

   * Stored in Supabase `auth.users`.
   * Contains security-sensitive data: email, password hash, verification status, `user_metadata`, etc.
   * Not directly exposed to frontend except through Supabase client libraries.

2. **Profile**

   * Stored in `public.profiles`, 1:1 with `auth.users.id`.
   * Canonical source for user-facing identity and roles:

     * `id` (UUID, FK to `auth.users.id`)
     * `handle`, `display_name`, `avatar_key`, etc.
     * `role` (app-level role, see below)
     * `account_status` (active/suspended/banned)
     * `strike_count` and related moderation fields
     * `show_sensitive` preference
   * Readable to the public with restricted fields per existing guest vs. auth contracts.

3. **Guest**

   * Any visitor not authenticated with Supabase.
   * Has no `auth.users` record and no `public.profiles` row.

4. **Role**

   * Application-level classification stored in `public.profiles.role`.
   * Supported v1 values:

     * `user`
     * `mod`
     * `admin`
   * May be mirrored in `auth.users.user_metadata.role` for convenience, but **`profiles.role` is canonical**.

5. **Account Status**

   * Stored in `public.profiles.account_status`.
   * Supported v1 values:

     * `active`
     * `suspended`
     * `suspended_pending_review`
     * `banned_pending_review`
     * `banned`
   * Combined with `role` to determine effective permissions.

6. **Modules / Features (context)**

   * **Static content**: informational pages, Bible tools, literature viewer, etc.
   * **Account-dependent features**:

     * Personal account page
     * Salvation testimony
     * Additional testimonies
     * Prayer requests
     * Daily streaks / daily tools data
     * Following / “Amen” / reactions (future)
   * **Admin area**:

     * `/admin/` entry
     * Moderation queues
     * Penalty review
     * Settings & keyword management

---

### C. Role Set & Global Responsibilities

#### 1. Guest

* Not authenticated, no `profiles` row.
* Capabilities:

  * Full read-only access to all **public** content:

    * Testimony Wall (public testimonies only)
    * Public user/testimony pages
    * Bible tools, literature, static pages
  * Cannot:

    * Create or edit testimonies or salvation testimony
    * Create or edit prayer requests
    * Participate in daily streaks or any saved daily data
    * Follow users, “Amen”, react, or save favorites
    * Access `/admin/*` or any moderation/admin tools

Guests are effectively “public viewers.”

---

#### 2. User

* Authenticated account with a `public.profiles` row.
* `role = 'user'`, `account_status = 'active'`.
* Capabilities:

  * All guest capabilities (read public content).
  * Account-scoped features:

    * Manage their own profile (display name, handle, avatar, etc.).
    * Maintain a salvation testimony (once per account).
    * Create and edit their own additional testimonies.
    * Create and edit their own prayer requests.
    * Participate in daily tools and streaks (where implemented).
    * Interact with others’ content:

      * View public accounts and public testimonies.
      * Future: follow, amen, react, etc.
  * Restrictions:

    * No access to `/admin/*` or moderation queues.
    * Cannot see other users’ private drafts.
    * Subject to moderation and penalties described in ACC-MOD.

---

#### 3. Moderator (`mod`)

* Authenticated account with elevated responsibilities for content safety.
* `role = 'mod'`, `account_status = 'active'`.
* Everything a normal user can do, **plus**:

**Moderation responsibilities (content):**

* Access to **Moderation > Content** queue:

  * See reported content and content flagged by keyword filters.
  * Mark reports as:

    * “No violation” (clear content and allow it back to public).
    * “Violation recommended” (escalate with a recommendation).
    * “Escalate to admin” explicitly when unsure.
* Depending on config (from moderation settings):

  * `mod_can_final_approve`:

    * If `true`: a moderator’s **approve** action can move content from `pending_*` back to `published`.
    * If `false`: approve moves to an admin queue (`pending_admin`), admin must finalize.
  * `mod_can_final_reject`:

    * If `true`: a moderator’s **reject** action can mark content as removed for violation, but **strikes are still applied by admins**.
    * If `false`: reject moves to admin queue; admin must finalize.

**Moderation responsibilities (accounts):**

* Access to **Moderation > Accounts** queue (read and recommend only):

  * View reported accounts, account history, and visible strikes.
  * Recommend actions (e.g., “suspend recommended”) but **cannot**:

    * Change `account_status`.
    * Change `role`.
    * Apply strikes directly.

**Explicit limits:**

* Mods **cannot**:

  * Change any user’s `role`.
  * Change any user’s `account_status`.
  * Edit `moderation_settings` or `moderation_keywords`.
  * Directly increment `strike_count` (recommend only).
  * See other users’ private drafts (unless explicitly exposed via admin-only UI; default is no).

---

#### 4. Admin (`admin`)

* Highest application-level role; reserved for project owner(s) and trusted core staff.
* `role = 'admin'` with any `account_status` (though practically admins should remain `active`).

**Capabilities (superset of mod + global management):**

* Everything users and mods can do.
* Full access to `/admin/*`, including:

1. **Moderation > Content**

   * Final authority on all content decisions.
   * Approve or remove content (including private violations).
   * Apply strikes to account owners.
   * Mark content as sensitive (`is_sensitive = true`, with `sensitivity_reason`).
   * Override keyword hits for specific posts.

2. **Moderation > Accounts**

   * Set `account_status`:

     * `active`, `suspended`, `suspended_pending_review`, `banned_pending_review`, `banned`.
   * Adjust `strike_count` (for corrections or testing).
   * Change `role` between `user`, `mod`, and `admin`.
   * View complete moderation history and penalties for any account.

3. **Penalty Review**

   * Review auto-generated “pending suspension/ban” entries.
   * Confirm or overturn:

     * Suspensions (short or long).
     * Bans.
   * While in `*_pending_review`, the system behaves as if the suspension/ban is in force.

4. **Settings & Keywords**

   * Edit **moderation settings** (global behavior toggles and thresholds).
   * Edit **keyword lists**:

     * Add/remove/update `never_allowed`, `needs_review`, `sensitive_allowed` terms.
   * Manage other configuration (e.g., default `show_sensitive` behavior).

5. **Admin-only visibility**

   * May view all content, including:

     * Other users’ private drafts.
     * Removed/violation content.
     * Historical versions where stored.

---

### D. Account Status & Behavioral Rules

All authenticated accounts have an `account_status` in `public.profiles`:

1. **`active`**

   * Default status when an account is created.
   * Full functionality according to their `role`.

2. **`suspended_pending_review`**

   * Auto-assigned when a threshold event (e.g., 3 strikes/30 days or other configured triggers) calls for a suspension, but final admin review is still pending.
   * Behavior:

     * Account is effectively **read-only**:

       * Cannot create or edit testimonies, prayers, or other UGC.
       * Cannot change profile fields beyond minimal account integrity (exact scope configurable).
     * All public content belonging to the account is hidden or treated as non-public during the suspension.
   * Admin must confirm or adjust the suspension via Penalty Review.

3. **`suspended`**

   * Confirmed suspension state after admin review.
   * Same effective behavior as `suspended_pending_review`, but review is completed and the suspension is time-bound:

     * Short suspension (e.g., 3 strikes in 30 days → 7 days).
     * Long suspension (e.g., 6th lifetime strike → 7 weeks).
   * At suspension end, system returns account to `active` (unless admin overrides).

4. **`banned_pending_review`**

   * Auto-assigned when a threshold for permanent ban is reached (e.g., 7 lifetime strikes).
   * Behaves like a permanent suspension **until admin confirms**:

     * Account is read-only.
     * All UGC remains hidden.
   * Admin must confirm ban or downgrade to another status.

5. **`banned`**

   * Confirmed permanent restriction.
   * Behavior:

     * Login may remain allowed for legal/communication purposes, but account is permanently read-only.
     * All public content remains hidden by default unless an admin explicitly restores specific items.
   * Reversal requires an explicit admin decision.

---

### E. Strikes & Penalties (Summary View)

Full details are in ACC-MOD; here is the account-level summary:

* **Strike definition**: a confirmed violation linked to an account increments `profiles.strike_count` by 1.
* Thresholds (configurable; v1 default):

  * **Short suspension trigger**:

    * 3 strikes within a rolling 30-day window → 7-day suspension.
  * **Long suspension trigger**:

    * 6th lifetime strike → 7-week suspension.
  * **Ban trigger**:

    * 7th lifetime strike → permanent ban.
* Each strike and penalty:

  * Generates a log record (who/when/why).
  * Triggers an in-site warning and email notification with explanations.
  * Auto-creates an entry in the **Penalty Review** queue for admin confirmation.

---

### F. Role Assignment & Governance

1. **Default assignment**

   * New verified account:

     * `role = 'user'`
     * `account_status = 'active'`
     * `strike_count = 0`
     * `show_sensitive = true` (default; age-based changes are future work)
   * No automatic assignment of `mod` or `admin`.

2. **Role changes**

   * Only `admin` accounts may change `role` of another account.
   * Changes are logged with:

     * Previous role
     * New role
     * Admin who performed the change
     * Timestamp
     * Reason (free-text)

3. **Status changes**

   * Status changes to any of `suspended*` or `banned*` are:

     * Driven by automated rules from ACC-MOD.
     * Confirmed and/or adjusted by admins.
   * All changes are logged similarly to role changes.

4. **Profiles vs `auth.users.user_metadata`**

   * `public.profiles.role` and `public.profiles.account_status` are canonical for application behavior.
   * `auth.users.user_metadata.role` may mirror the role for convenience, but:

     * Frontend must rely on `profiles.role` for gating features.
     * Any discrepancy is resolved in favor of `public.profiles`.

---

### G. Sensitivity Preference (Account-Level)

* Field: `public.profiles.show_sensitive boolean NOT NULL DEFAULT true`.
* Behavior:

  * If `true`: account may see sensitive-flagged content by default.
  * If `false`: sensitive content is omitted or collapsed (see ACC-MOD).
* Age-based defaults and restrictions:

  * For v1, **no age logic is implemented**.
  * Future: minors may default to `show_sensitive = false` and have limited ability to change it.

---

### H. Admin Config & Settings (Summary)

A single-row **moderation/app settings** table (described fully in ACC-MOD) controls key behaviors:

* `review_all_new_content` (bool)
* `mod_can_final_approve` (bool)
* `mod_can_final_reject` (bool)
* `reports_for_auto_hide` (int; default 2)
* Strike/suspension/ban thresholds and durations

Admins modify this via `/admin/settings`. Roles and status semantics in this contract must remain consistent with those settings.
