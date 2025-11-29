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
