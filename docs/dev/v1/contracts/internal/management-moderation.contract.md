Below are the two contracts as standalone markdown docs. You can copy/paste into separate files (e.g., `shk-roles-management.v1.contract.md` and `shk-moderation.v1.contract.md`).

---

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

---

## 2) SHK Moderation & Safety Contract (ACC-MOD v1.0)

### A. Purpose & Scope

This document defines the moderation and safety system for SHK:

* Pre-publish checks and keyword filtering
* Reporting flows and auto-hide behavior
* Review queues, mod/admin powers
* Strikes, suspensions, and bans
* Sensitive content handling
* Logging, analytics, and future extensibility

It complements the **Roles & Account Management Contract (ACC-ROLES v1.0)** and assumes those role and status definitions.

---

### B. Moderation Targets

Moderation applies to:

1. **Content (target_type = 'content')**

   * Salvation testimonies
   * Additional testimonies
   * Prayer requests
   * Future UGC (comments, reactions, etc.) as they are added

2. **Accounts (target_type = 'account')**

   * Profile fields (username, display_name, avatar, bio)
   * Salvation testimony and other account-level statements
   * Patterns of abusive behavior independent of individual posts

Both content and accounts share common moderation machinery but appear in separate queues/tabs in the admin UI for clarity.

---

### C. Data Model (Core Tables)

#### 1. Content moderation fields

Each moderatable content record (e.g., `testimonies`, `prayer_requests`) includes:

* `status` (text enum), v1 values:

  * `draft_private`
  * `pending_mod`
  * `pending_admin`
  * `published`
  * `hidden_reported` (auto-hidden due to reports)
  * `removed_violation` (confirmed violation)
  * `removed_other` (non-violation removal, e.g., user request/duplicate)
  * `hidden_author_suspended` (hidden due to account status)
* `is_sensitive boolean NOT NULL DEFAULT false`
* `sensitivity_reason text NULL` (short code or label; e.g., `sexual_trauma`, `abuse`, `self_harm`)

These fields interact with keyword filters, reports, and account status to drive behavior.

---

#### 2. `moderation_keywords`

Stores dynamic keyword lists used by pre-publish checks.

* Columns (conceptual):

  * `id` (PK)
  * `keyword text`
  * `category enum('never_allowed','needs_review','sensitive_allowed')`
  * `language text` (e.g., `'en'`; future: `'es'`, `'pt'`, etc.)
  * `is_active boolean DEFAULT true`
  * `created_at timestamptz`
  * `updated_at timestamptz`

* Category semantics:

  * **`never_allowed`**

    * Default: hard block (user must edit).
    * Option B in roles contract: user may choose a small “submit anyway for special admin review” path, which:

      * Does **not** publish the content.
      * Sends it directly to an admin-only queue.
  * **`needs_review`**

    * Content may be authored but is never auto-published.
    * Goes into `pending_mod` (or `pending_admin`, depending on config) immediately.
  * **`sensitive_allowed`**

    * Marks content as potentially sensitive but not automatically disallowed.
    * Typically:

      * `is_sensitive = true`.
      * Subject to `review_all_new_content` toggle; may be published immediately or queued.

Keyword handling is performed per language, with the ability to add localized lists later.

---

#### 3. `moderation_settings` (global single-row config)

A central configuration table, used by backend and frontend.

* Example columns:

  * `id` (PK, constant)
  * `review_all_new_content boolean` (default v1: `false`)
  * `mod_can_final_approve boolean`
  * `mod_can_final_reject boolean`
  * `reports_for_auto_hide integer` (default 2)
  * `strikes_window_days integer` (for short suspension; default 30)
  * `strikes_for_short_suspension integer` (default 3)
  * `short_suspension_days integer` (default 7)
  * `strikes_for_long_suspension integer` (default 6)
  * `long_suspension_days integer` (default 49)
  * `strikes_for_ban integer` (default 7)
  * Additional future toggles:

    * `allow_guests_to_view_X` fields
    * extra mod powers
* Modified only by admins via `/admin/settings`.

---

#### 4. `reports` (user reports)

Captures all user-initiated reports on content or accounts.

* Columns:

  * `id` (PK)
  * `reporter_id uuid` (FK to `profiles.id`; null if guest reports are ever allowed; v1: auth only)
  * `target_type enum('content','account')`
  * `target_id uuid` (content id or profile id)
  * `reason_category enum('spam','harassment','hate','sexual','self_harm','violence','other')`
  * `reason_text text NULL` (optional free-text explanation)
  * `created_at timestamptz`
  * `handled boolean DEFAULT false`
  * `handled_at timestamptz NULL`

Distinct reporter count per `target_type` + `target_id` is used to trigger auto-hide behavior.

---

#### 5. `moderation_events` (log / audit trail)

Records all moderation decisions and transitions.

* Columns:

  * `id` (PK)
  * `target_type enum('content','account')`
  * `target_id uuid`
  * `performed_by uuid` (FK to `profiles.id`; null for automated system events)
  * `role_at_action enum('mod','admin','system')`
  * `action enum('report_received','auto_hidden','moved_pending_mod','moved_pending_admin','approved','removed_violation','removed_other','strike_added','strike_removed','status_changed','role_changed','sensitive_marked','sensitive_unmarked','override_keyword','penalty_created','penalty_confirmed','penalty_overturned')`
  * `from_status text NULL`
  * `to_status text NULL`
  * `details jsonb NULL` (structured info such as reason, keyword hit, notes)
  * `created_at timestamptz`

All significant decisions must write a row here.

---

#### 6. `account_penalties` (penalty summary / review queue)

Represents suspensions and bans as objects for admin review.

* Columns:

  * `id` (PK)
  * `profile_id uuid` (FK to `profiles.id`)
  * `penalty_type enum('short_suspension','long_suspension','ban')`
  * `strike_count_at_creation integer`
  * `effective_from timestamptz`
  * `effective_until timestamptz NULL` (null for ban)
  * `status enum('pending_review','confirmed','overturned')`
  * `created_by uuid NULL` (null for auto, or admin id)
  * `confirmed_by uuid NULL`
  * `created_at timestamptz`
  * `updated_at timestamptz`
  * `notes text NULL`

Admins manage this via a **Penalty Review** screen.

---

### D. Pre-Publish Flow (Keyword Filters)

When a user submits or updates content (e.g., a testimony or prayer):

1. **Step 1: Keyword scan**

   * System checks the content body against `moderation_keywords` for the relevant language.
   * For each hit, the highest-severity category determines behavior:

     * `never_allowed`
     * `needs_review`
     * `sensitive_allowed`

2. **Step 2: User-facing response**

   * If `never_allowed`:

     * Show a blocking message: content violates guidelines due to specific language.
     * Options:

       * “Edit and resubmit” (recommended).
       * “Submit anyway for special review” (small secondary action).
     * If user chooses special review:

       * Content status: `pending_admin`.
       * Content is **not published**; goes to an admin-only queue.
   * If `needs_review`:

     * Content is accepted as a draft and sent to moderation.
     * Status: `pending_mod` (or `pending_admin` if `mod_can_final_approve = false` or policy demands).
     * Not visible publicly until approved.
   * If `sensitive_allowed`:

     * Mark `is_sensitive = true`, possibly set `sensitivity_reason`.
     * If `review_all_new_content = false` (v1 default):

       * Content may be published directly (`published`) unless other conditions intervene.
     * If `review_all_new_content = true`:

       * Content goes to `pending_*` queue before publishing.

3. **Step 3: No keyword hits**

   * If `review_all_new_content = false`:

     * Content goes directly to `published`.
   * If `review_all_new_content = true`:

     * Content goes to `pending_mod` (or `pending_admin`) and is not public until approved.

All flows record a `moderation_events` entry with details (keyword hits, category, etc.).

---

### E. Reporting & Auto-Hide

#### 1. Reporting behavior

* Any authenticated user may report:

  * Content (testimony, prayer, etc.).
  * Accounts (profiles).
* For each report:

  * Insert row into `reports`.
  * Log `moderation_events` with `action = 'report_received'`.

#### 2. Auto-hide rule

* Let `N = reports_for_auto_hide` from `moderation_settings` (default v1: `N = 2`).
* When a content item receives reports from **N distinct accounts**:

  * If content is `published`:

    * Status becomes `hidden_reported`.
    * Item disappears from public views (Testimony Wall, profile pages).
  * A moderation queue entry is created:

    * For mods (content queue).
  * `moderation_events` logs `action = 'auto_hidden'`.

#### 3. Handling reports that are cleared

* When a mod/admin reviews a reported item:

  * If they decide **no violation**:

    * Content is set back to `published` (subject to any account status).
    * A flag is set at content-level, e.g., `was_cleared_by_mod = true` and/or stored in `details` in `moderation_events`.
  * If that same item is reported again:

    * It automatically routes to **admin-only** queue, bypassing mods.
    * Goal: repeated concern over previously cleared content gets higher scrutiny.

---

### F. Review Queues & Role-Specific Powers

#### 1. Queues

There are two main queues, each with two “levels”:

1. **Content Queue**

   * Mod view:

     * New content in `pending_mod`.
     * `hidden_reported` content.
     * Items escalated to mod from keyword filters.
   * Admin view:

     * Everything mod sees plus:

       * Items in `pending_admin`.
       * Special `never_allowed` “submit anyway” items.
       * Any items routed admin-only after mod clearing.

2. **Accounts Queue**

   * Mod view:

     * Reported accounts where recommendations are needed.
   * Admin view:

     * All reported accounts.
     * Accounts reaching key thresholds (strikes, suspensions, ban triggers).

#### 2. Moderator actions (content)

Within the Content Queue, a moderator may:

* **Approve**:

  * If `mod_can_final_approve = true`:

    * `pending_mod` → `published`.
  * If `mod_can_final_approve = false`:

    * `pending_mod` → `pending_admin`.
* **Reject (non-violation)**:

  * Mark a report as **no violation** and:

    * Restore `hidden_reported` → `published`.
    * Set flags indicating “cleared by mod; review if re-reported.”
* **Recommend violation**:

  * Mark content as likely violating; moves case to `pending_admin` with recommendation.
* **Escalate**:

  * Explicit “escalate to admin” for unclear cases.

Moderators **do not** apply strikes or change account_status; they only manage visibility and recommendations.

#### 3. Admin actions (content)

Admins may:

* Do everything mods can do, plus:

  * Make final decisions on `pending_admin` and special review items:

    * Confirm `published`.
    * Set `status = 'removed_violation'` or `removed_other`.
  * Set `is_sensitive` and `sensitivity_reason`.
  * Apply strikes to owners (see G).
  * Override previous decisions and keyword flags.

---

### G. Strikes, Suspensions, and Bans

Details here complement the summary in ACC-ROLES.

#### 1. Strike application

* When an admin confirms `removed_violation` on content or confirms an account-level violation:

  * Increment `profiles.strike_count` by 1.
  * Log `moderation_events` with `action = 'strike_added'`.
  * Generate or update an `account_penalties` record if thresholds are hit.
  * Trigger in-site warning + email to the user.

#### 2. Thresholds (v1 defaults; configurable)

From `moderation_settings`:

* `strikes_window_days = 30`
* `strikes_for_short_suspension = 3`
* `short_suspension_days = 7`
* `strikes_for_long_suspension = 6`
* `long_suspension_days = 49` (7 weeks)
* `strikes_for_ban = 7`

Behavior:

1. **Short Suspensions**

   * When an account accumulates at least 3 strikes **within the last 30 days**:

     * Create short-suspension `account_penalties` entry.
     * Set `account_status = 'suspended_pending_review'`.
     * Admin reviews; upon confirmation:

       * `account_status = 'suspended'` for `short_suspension_days`.
       * Content hidden (`hidden_author_suspended`).

2. **Long Suspensions**

   * On the **6th lifetime strike**:

     * Create long-suspension `account_penalties` entry.
     * Same flow as above, but for `long_suspension_days` (≈7 weeks).
     * Admin warning should be more prominent and mention risk of permanent ban.

3. **Ban**

   * On the **7th lifetime strike**:

     * Create ban `account_penalties` entry.
     * Set `account_status = 'banned_pending_review'`.
     * On admin confirmation:

       * `account_status = 'banned'`.
       * Account permanently read-only; all content hidden by default.

All auto-suspensions/bans go through Penalty Review; they are **not** final until an admin confirms.

---

### H. Sensitive Content System

#### 1. Content-level flags

* `is_sensitive boolean`
* `sensitivity_reason text` (optional structured code / label)

Set by:

* Keyword classification (`sensitive_allowed` hits).
* Mod/admin decisions during review.

#### 2. Viewer preference

* `profiles.show_sensitive boolean` (see ACC-ROLES):

  * `true`: user sees sensitive content normally.
  * `false`: sensitive content is hidden or collapsed.

#### 3. Frontend behavior (conceptual)

When rendering content:

* If `content.is_sensitive = true` and viewer is:

  * Guest (no preference field): treat as if `show_sensitive = true` for v1, or follow later policy.
  * Auth user with `show_sensitive = true`: show normally, but optionally with a “Sensitive content” label.
  * Auth user with `show_sensitive = false`:

    * Either:

      * Hide entirely (omit from lists), or
      * Show a collapsed placeholder: “Sensitive content hidden per your settings” with an optional “view once” button (does not change `show_sensitive`).

Exact UX can be adjusted later without changing data model.

---

### I. Rate Limiting & Abuse Mitigation

Rate limiting is designed to prevent spam and abuse, not detailed here as exact numbers; they will be parameters in `moderation_settings` or related config.

Conceptual rules:

* **Posting limits**:

  * Max number of testimonies/prayers per user per unit time (e.g., per hour/day).
  * Excess attempts are soft-rejected with a clear user message.

* **Reporting limits**:

  * Max number of reports per user per unit time.
  * Excessive reporting can be rate-limited and flagged in `moderation_events`.

* **Repeated false reports**:

  * If a user repeatedly reports content that admins mark as “no violation”, this may be subject to review and potential strike as abuse of the report system (policy decision for T&C later).

Implementation details (exact numbers) are left as configurable via settings.

---

### J. Privacy & Access Control (RLS Considerations)

* `reports` and `moderation_events`:

  * Not publicly readable.
  * Accessible only to mods/admins under appropriate RLS and to server-side service roles.

* Sensitive/removal content:

  * `removed_violation` and `removed_other` content is not exposed in normal public queries.
  * Admin tools use service-role access to query them for compliance and review.

* Drafts:

  * `draft_private` visible only:

    * To the owner (user itself).
    * To admins via admin tools.
  * Mods do not see private drafts by default.

These patterns must be enforced via Supabase RLS and not just frontend checks.

---

### K. Future Extensions (Notes Only)

The following are intentionally not v1 requirements, but this contract is written to accommodate them:

* Age-based defaults (e.g., minors forced to `show_sensitive = false`).
* Separate mod performance analytics and “mod strikes.”
* Finer-grained role types (e.g., `reviewer`, `staff`, `legal`).
* Stronger content categorization for T&C (e.g., self-harm, promotion of illegal activity, etc.).
* Cross-module policies (e.g., testifying about certain types of content may require extra review or disclaimers).

These extensions should reuse the same tables and patterns defined here where possible.

---

If you want, the next step can be to take these two documents and:

* Add specific field names/types aligned with your existing `user_account_data.v1.contract.md`, and
* Extract a short, non-technical “policy summary” that can later be adapted into public-facing T&C and community guidelines.
