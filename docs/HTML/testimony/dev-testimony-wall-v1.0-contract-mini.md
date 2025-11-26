# SHK Testimony Module – v1 Contract (Depends on Accounts Contract)

> Scope: Testimony Wall / Testimony system as a module that sits on top of the SHK Accounts and User Data system defined in `SHK_Accounts_and_UserData_v1_Contract.md`.

---

## 1. Purpose and Dependencies

- Provide a way for users to share testimonies of what God has done in their lives, with simple privacy controls and manual moderation.  
- Surface testimonies primarily in:
  - A public Testimony Wall.
  - A “My Testimonies” view in the user’s account area.

This module depends on the Accounts contract:

- Uses `User.id`, `User.role`, and `User.email_verified`.  
- Uses global preferences: `default_testimony_visibility`, `default_testimony_anonymous` (if implemented).  
- Uses avatar and display name for author labeling when visibility allows.

---

## 2. Testimony Data Model (Conceptual)

Each `Testimony` record includes:

- Identity:
  - `id`
  - `owner_user_id` → `User.id`
- Content:
  - `title` (required, short)
  - `body` (required, long text)
  - `category` (required; from a fixed list, e.g., `Salvation`, `Healing`, `Provision`, `Restoration`, `Guidance`, `Other`)
  - `tags` (optional small list of strings)
  - `event_date` (optional; date the testimony event occurred)
- Visibility and status:
  - `visibility` (enum):
    - `PUBLIC_NAMED`
    - `PUBLIC_ANONYMOUS`
    - `PRIVATE`
  - `status` (enum):
    - `PENDING`
    - `APPROVED`
    - `HIDDEN`
- Moderation-related:
  - `moderation_note` (optional short text; latest moderator explanation)
  - `last_moderated_by` (optional; `User.id` of moderator/admin)
  - `last_moderated_at` (timestamp)
- Meta:
  - `submitted_at` (timestamp when user submitted)
  - `updated_at` (timestamp when user last edited)
  - Optional light counters (e.g., number of reports), or a separate `Report` entity may track this.

---

## 3. Visibility and Status Semantics

### 3.1 Visibility

- `PUBLIC_NAMED`
  - If `status == APPROVED`, testimony is eligible to appear on the public wall.
  - Public viewers see content + author’s `display_name` and preset avatar.
- `PUBLIC_ANONYMOUS`
  - If `status == APPROVED`, testimony is eligible to appear on the public wall.
  - Public viewers see content but not the author’s identity (e.g., label “Shared by a member”).
  - Moderators/admins always see true ownership internally.
- `PRIVATE`
  - Visible only to:
    - The owner (in “My Testimonies”).
    - Moderators/admins (for safety and moderation).
  - Never appears on the public wall, regardless of status.

### 3.2 Status

- `PENDING`
  - Submitted by user; waiting for moderation.
  - Visible in:
    - Owner’s “My Testimonies”, labeled as “Pending review”.
    - Moderation queue.
  - Not visible on the public wall.
- `APPROVED`
  - Reviewed and accepted by a moderator.
  - Eligible for public wall if `visibility` is `PUBLIC_NAMED` or `PUBLIC_ANONYMOUS`.
  - `PRIVATE` testimonies remain private even when approved.
- `HIDDEN`
  - Moderator has decided it should not be public.
  - Visible to:
    - Owner (with clear “Hidden” status and, if provided, `moderation_note`).
    - Moderators/admins.
  - Never visible on the public wall.

---

## 4. Creation, Editing, and Deletion

### 4.1 Creation

- Only logged-in users can create testimonies.
- At creation:
  - Required: `title`, `body`, `category`.
  - Optional: `tags`, `event_date`.
  - `visibility` is chosen by the user; default is taken from `default_testimony_visibility` if available.
- Verification rule:
  - If `User.email_verified == false`:
    - Backend restricts `visibility` to `PRIVATE` only (ignores public choices).
  - If `User.email_verified == true`:
    - All three visibility options are available.
- On submit:
  - `status` is set to `PENDING`.
  - `submitted_at` is set to current timestamp.
  - Testimony appears in the moderation queue and in owner’s “My Testimonies” as “Pending”.

### 4.2 Editing

- Owners can edit their own testimonies at any time.
- v1 behavior (TBD when revisited, documented here as options):
  - Option A (simpler to start): editing an `APPROVED` testimony leaves status as `APPROVED` and changes are applied immediately.
  - Option B (stricter): editing an `APPROVED` testimony moves it back to `PENDING` for re-review.
- For now this contract marks the choice as **to be finalized** when the module is actively implemented.
- Unverified users remain restricted to `PRIVATE` visibility on edits.

### 4.3 Deletion

- Owners can request deletion of their testimonies from the UI.
- v1 backend behavior:
  - Soft delete: mark as deleted (or equivalent) so it is:
    - No longer visible to the owner or public.
    - Still available internally for audit/safety until retention policy is defined.
- Retention/anonymization details may be refined later; user-facing guarantee is that deleted testimonies disappear from their lists and the wall.

---

## 5. Public Wall

### 5.1 Contents

- The wall displays only testimonies where:
  - `status == APPROVED`, and
  - `visibility` is `PUBLIC_NAMED` or `PUBLIC_ANONYMOUS`.

### 5.2 Filters and search (v1)

- Filters:
  - Category filter (single or multi-select).
- Search:
  - Simple text search across title and body (basic “contains” behavior is sufficient in v1).
- Sorting:
  - Default: newest first (by `submitted_at` or `approved_at`, to be chosen at implementation time).

### 5.3 Presentation

- For each testimony in the wall:
  - Show title, truncated body, category, event_date (if present), and some notion of when it was shared.
  - For `PUBLIC_NAMED`:
    - Show author’s `display_name` and avatar (preset).
  - For `PUBLIC_ANONYMOUS`:
    - Show label such as “Shared by a member” instead of identity.
- Clicking a testimony opens a single-testimony view:
  - Shows full body, title, category, event_date, tags, and appropriate identity label (named or anonymous).
  - Respects `visibility` rules.

---

## 6. “My Testimonies” (User Account Area)

- Shows all testimonies where `owner_user_id == current_user.id`, regardless of `visibility` or `status` (except ones soft-deleted, if hidden from user).
- For each testimony, display:
  - Title, category, visibility, status, and `updated_at`.
- Actions:
  - View full testimony.
  - Edit.
  - Delete (soft delete).
- For `HIDDEN` testimonies:
  - Show a clear label (“Hidden by moderation”) and `moderation_note` if available.

---

## 7. Moderation and Reports

### 7.1 Moderation queue

- Accessible only to `moderator` and `admin` roles.
- Shows testimonies with `status == PENDING` (and optionally recently reported testimonies).
- For each testimony:
  - Display title, snippet of body, owner identity (internal), requested visibility, submitted_at.

### 7.2 Moderator actions

- `APPROVE`:
  - Sets `status = APPROVED`.
- `HIDE`:
  - Sets `status = HIDDEN`.
  - Moderator may add or update `moderation_note`.
- Moderators/admins can view all testimonies regardless of visibility.

### 7.3 Reports

Conceptual `Report` entity:

- Fields:
  - `id`
  - `testimony_id`
  - `reporter_user_id`
  - `reason` (short text)
  - `created_at`
- Any logged-in user can report a testimony.
- Moderators see a list of reports, each linked to the relevant testimony.
- v1: reports do not trigger automatic changes; they are signals for moderators.

---

## 8. Interactions with Accounts Contract

- Depends on:
  - `User.id` for ownership and moderation fields.
  - `User.role` for access control (user vs moderator/admin).
  - `User.email_verified` to enforce public vs private visibility rules.
  - Global preferences `default_testimony_visibility` and `default_testimony_anonymous` (if implemented) for form defaults.
  - `User.display_name` and `User.avatar_id` for author labels on the wall (respecting anonymity).
- Does not redefine or expand the `User` model beyond what is in the Accounts contract.

---

## 9. Out of Scope for v1 (Testimony Module)

Explicitly not included in v1:

- Follow system (following users or testimonies).  
- Comments or threaded discussions under testimonies.  
- Likes/reactions or engagement counters.  
- Draft status and full draft workflow.  
- Rich text formatting or media attachments (images, video, audio).  
- Advanced search (full-text indexing, maps, complex filters).  
- Email notifications for testimony events (approval, hidden, reports).  
- Public user profile pages beyond labels in Testimony views.

---

## 10. Status of This Contract

- This is the working v1 contract for the Testimony module, assumed to be implemented after or alongside the Accounts and User Data contract.  
- “TBD” items (e.g., how edited `APPROVED` testimonies behave) will be resolved prior to implementation but do not affect the overall structure.  
- If the Testimony module is delayed, the Accounts system remains valid and usable for other tools; Testimony can be added when ready without changing the core `User` model.
