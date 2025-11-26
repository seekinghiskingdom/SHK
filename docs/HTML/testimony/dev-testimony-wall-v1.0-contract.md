# SHK Testimony v1 – Snapshot Contract (Parked)

> Snapshot of all currently agreed decisions for the Testimony module, based on v0.9 + Phase 1 discussions. This will be parked while we design a separate Global Accounts & User Data contract.

---

## 1. Overall Scope (v1)

- Purpose: A Testimony system where users can share what God has done in their lives, with simple privacy controls and manual moderation, surfaced primarily as:
  - A public Testimony Wall.
  - A “My Testimonies” area in the user account.
- Site is mostly static (Jekyll).  
- A separate managed backend handles:
  - Accounts and auth.
  - Storage of testimonies and moderation data.
  - Basic privacy and role-based access.

v1 focuses on:
- Submitting, editing, and (soft) deleting testimonies.
- Basic visibility settings (public / anonymous public / private).
- A simple moderation queue and “report” flow.
- A minimal public wall with filters + basic text search.

Social features (follows, comments, notifications, etc.) are explicitly **not** part of v1.

---

## 2. Account Assumptions (as used by Testimony module)

These are not the full account contract, just what Testimony depends on.

### 2.1 Identity

- Every testimony belongs to exactly one `User`.
- Each `User` has, at minimum:
  - `id` (internal, stable).
  - `email` (private).
  - `display_name` (public label, required).
  - `role` (one of: `user`, `moderator`, `admin`).
  - `accepted_terms` (boolean).
  - `is_13_plus` (boolean).
  - `is_minor_with_parent_consent` (boolean, optional).
  - `avatar_id` (optional, from a pre-defined list).
- Age/consent flags and `role` are **never shown** publicly; they are internal only.

### 2.2 Roles

- `user`: can create, edit, and delete their own testimonies; can report testimonies.
- `moderator`: everything a user can do, plus:
  - View all testimonies regardless of visibility.
  - Approve, hide, and annotate testimonies.
  - View and manage reports.
- `admin`: everything a moderator can do, plus:
  - Manage roles (promote/demote moderators, etc.).
  - Potentially higher-level actions (not yet defined here).

- v1: All new sign-ups are `user`. Moderators/admins are set manually via backend console (no codes/links/UI-based promotion at launch).

### 2.3 Verification & posting rules

- Backend provides:
  - Email+password auth.
  - Email verification.
  - Password reset.
- Behavior rule for Testimony:
  - Unverified users **may** create testimonies, but these are limited to **Private** visibility.
  - Only verified users can set testimonies to any “public” visibility option and be eligible for public Approval.

### 2.4 Avatars (pre-set, no uploads)

- v1 allows users to choose from a small, curated set of Christian-themed avatars:
  - A few “cartoonized” generic male/female silhouettes.
  - A small set of symbolic designs/objects (e.g., simple cross forms, fish symbol, non-denomination-specific Christian symbols).
- No image upload from users; the backend only stores an `avatar_id` referencing the chosen preset.
- Abuse or overuse of avatar changes can be monitored later; no hard limit in v1.

### 2.5 User preferences (as relevant to Testimony)

- v1 stores a very small set of global user preferences that affect testimonies:
  - `default_testimony_visibility`  
    - One of: `PUBLIC_NAMED`, `PUBLIC_ANONYMOUS`, `PRIVATE`.  
    - Controls which option is pre-selected when opening the “New Testimony” form.
  - `default_testimony_anonymous` (if needed)  
    - Whether public testimonies default to showing the display name or being anonymous.
  - Optional `preferred_language` (simple code like `en`) for future use; no behavior tied to it yet.

UI-only preferences (theme, layout, etc.) are front-end/local-storage concerns and not part of this contract.

---

## 3. Testimony Data Model (Conceptual)

Each `Testimony` record includes at least:

- Identity:
  - `id`
  - `owner_user_id` (references `User.id`)
- Content:
  - `title` (short, required)
  - `body` (long text, required)
  - `category` (required; from a fixed list, e.g., `Salvation`, `Healing`, `Provision`, `Restoration`, `Guidance`, `Other`)
  - `tags` (optional, small list of short strings)
  - `event_date` (optional; date representing when the main event took place)
- Visibility & status:
  - `visibility` (one of: `PUBLIC_NAMED`, `PUBLIC_ANONYMOUS`, `PRIVATE`)
  - `status` (one of: `PENDING`, `APPROVED`, `HIDDEN`)
- Moderation-related:
  - `moderation_note` (optional short text; latest moderator note)
  - `last_moderated_by` (optional moderator `user_id`)
  - `last_moderated_at` (timestamp)
- Meta:
  - `submitted_at` (timestamp when user submitted)
  - `updated_at` (timestamp when user last edited)
  - Possibly lightweight counters (e.g., number of reports), or this may instead be handled via a separate `Report` entity.

---

## 4. Visibility & Status – Meaning

### 4.1 Visibility options

- `PUBLIC_NAMED`
  - If `status == APPROVED`, testimony can appear on the public wall.
  - Public viewers see the content and the owner’s **display name**.
- `PUBLIC_ANONYMOUS`
  - If `status == APPROVED`, testimony can appear on the public wall.
  - Public viewers see the content but **do not** see the owner’s identity (e.g., “Shared by a member”).
  - Moderators/admins can still see the true owner in internal tools.
- `PRIVATE`
  - Testimony is visible to:
    - The owner.
    - Moderators/admins.
  - It **never** appears on the public wall, regardless of status.
  - Used for truly private sharing, journaling, or early drafts that the user wants to keep between themselves and moderators.

### 4.2 Status values

- `PENDING`
  - User has submitted the testimony.
  - Visible in:
    - Owner’s “My Testimonies” list (with a “Pending review” label).
    - Moderation queue.
  - Not visible on the public wall, regardless of visibility choice.
- `APPROVED`
  - Moderators have approved the testimony.
  - If `visibility` is `PUBLIC_NAMED` or `PUBLIC_ANONYMOUS`, it can be shown on the public wall.
  - If `visibility` is `PRIVATE`, it remains private (no wall exposure).
- `HIDDEN`
  - Moderators have decided the testimony should not be publicly visible.
  - Visible to owner (with a clear “Hidden” status and optionally a reason) and to moderators/admins.
  - Never visible on the public wall.

No separate “DRAFT” status for v1 (to keep flow simple). Draft-like use cases can be approximated by `PRIVATE` + `PENDING` or by editing before submission.

---

## 5. Core Behaviors

### 5.1 Creation

- Any logged-in user can create a testimony.
- At creation:
  - Required: title, body, category.
  - Optional: tags, event_date.
  - User picks visibility; the form defaults to `default_testimony_visibility`.
- Verification rule:
  - If user is **unverified**, backend restricts `visibility` to `PRIVATE` only.
  - If user is **verified**, all three visibility options are available.
- On submit:
  - `status` is set to `PENDING`.
  - Testimony enters the moderation queue.
  - User sees it in their “My Testimonies” list as “Pending review”.

### 5.2 Editing

- Owner can edit their own testimonies at any time.
- v1 behavior (parked, to refine later if needed):
  - Editing a `PENDING` or `HIDDEN` testimony keeps its status as-is.
  - Editing an `APPROVED` testimony may:
    - Either keep it `APPROVED`, or
    - Move it back to `PENDING` for re-review.  
  - This exact rule is **TBD** and will be finalized when we return to the module.
- Unverified users remain restricted to `PRIVATE` visibility even on edits.

### 5.3 Deletion

- Owner can “delete” their own testimonies.
- v1: treat deletion as a **soft delete** at backend level (still present for audit/moderation, but not visible to owner or public).
- Public behavior: deleted testimonies disappear from:
  - Public wall.
  - Owner’s “My Testimonies” list.

Exact archival/anonymization rules can be refined later; the key v1 guarantee is that end-users experience it as removed.

---

## 6. Public Wall & “My Testimonies”

### 6.1 Testimony Wall (public)

- Contents:
  - Only testimonies with `status == APPROVED` and `visibility` in (`PUBLIC_NAMED`, `PUBLIC_ANONYMOUS`).
- Basic filters:
  - Category (single or multiple).
  - Simple text search in title/body (basic contains match).
  - Possibly date range based on event_date or submitted_at (TBD).
- Sorting:
  - Default: newest first (by submitted_at or approved_at).
- Display:
  - For `PUBLIC_NAMED`: show testimony + display_name + avatar (preset) as author.
  - For `PUBLIC_ANONYMOUS`: show testimony, with a label like “Shared by a member” (no identity).
- Single testimony view:
  - Full text and metadata (category, event_date, tags, status label if appropriate).
  - Respect anonymity and visibility rules.

### 6.2 “My Testimonies” (account area)

- Shows all testimonies owned by the logged-in user, regardless of `visibility` or `status`.
- For each testimony, show:
  - Title, short excerpt, category, visibility.
  - Status label: Pending, Approved, Hidden.
  - Last updated timestamp.
- Actions per item:
  - View (full).
  - Edit.
  - Delete (soft delete).
- Clear explanation when status is `HIDDEN` (e.g., “Hidden by moderation” plus optional moderator note).

---

## 7. Moderation & Reports (Conceptual)

### 7.1 Moderation

- Moderation queue:
  - List of testimonies with `status == PENDING` (and possibly recent reports).
  - For each: title, snippet, visibility choice, owner (internal), submitted_at.
- Moderator actions:
  - `APPROVE`: sets status to `APPROVED`.
  - `HIDE`: sets status to `HIDDEN` (optionally with a short `moderation_note`).
- Moderators and admins can view:
  - All testimonies regardless of visibility, with ownership info and flags.

No automated emails for approvals/hidden decisions in v1; feedback is visible only inside “My Testimonies”.

### 7.2 Reports

- Any logged-in user can “Report” a testimony.
- Report capture (conceptually):
  - `reporter_user_id`
  - `testimony_id`
  - `reason` (short text)
  - `created_at`
- Moderators see a list of reports in a simple view, linked to the relevant testimony.
- v1: no automated outcomes (like auto-hiding on many reports); moderator judgment only.

---

## 8. Explicitly Out of Scope for v1 (Testimony Module)

These are **future** features and not required or expected for initial launch:

- Follow system (following users or testimonies; feed of “people I follow”).
- Comment threads under testimonies.
- Reactions/likes or other engagement metrics.
- Draft status and full draft workflow.
- Rich text formatting (bold/italic, headings) beyond very basic formatting, if any.
- Media uploads (images, video, audio) attached to testimonies.
- Advanced search (full-text search, complex filters, maps, etc.).
- Email notifications related to testimonies (approved/hidden/report notifications).
- Newsletters or periodic stats emails.
- Fine-grained notification settings.
- Self-serve role changes or moderator/admin promotion flows in UI.

---

## 9. Status of This Document

- This is a **parked snapshot** of the Testimony v1 module contract as of now.
- It assumes a separate **Global Accounts & User Data** contract will be created that:
  - Formalizes the `User` model.
  - Defines global preferences.
  - Specifies auth, roles, and data retention policies in more detail.
- When we return to the Testimony module, we will:
  - Align this contract to the finalized global account model.
  - Clarify any “TBD” rules (e.g., how edited Approved testimonies behave).
  - Extend or cut scope based on time and launch priorities.
