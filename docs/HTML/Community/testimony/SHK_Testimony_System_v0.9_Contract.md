
# SHK Testimony System – v0.9 Contract (-AI)

Version: 0.9 (soft final planning draft)  
Scope: Testimonies Wall, Personal Testimony Pages, core accounts + data model for v1.0  
Project: Seeking His Kingdom (SHK)

---

## 1. Vision and Core Concepts

**Goal:**  
Create a Christ-centered testimony system where:

- Each user has a **Personal Testimony Page** that becomes a living archive of what God is doing in their life (salvation story + ongoing testimonies).
- A global **Testimonies Wall** shows a community feed of public testimonies (with filters/modes).
- Future tools (timeline, maps, bubble views, etc.) are just alternate visualizations of the same core testimony data.

**Key ideas:**

- The user’s “account identity” is primarily their **Testimony** (capital T), not just a profile.
- Users add many smaller testimonies (prayer requests, answered prayers, blessings, miracles, life events) that collectively build their larger salvation testimony.
- Sharing is strongly encouraged, but users retain control via visibility and drafts.

---

## 2. Architecture Overview (Non-technical)

- **Static SHK site** (Jekyll) for content/layout.
- **Hosted dynamic backend** (managed service) for:
  - Accounts and login (email + password).
  - Testimony storage and retrieval.
  - Follows and moderation.
- Front-end pages are built now as static HTML/CSS/JS with **placeholder data**; later, JS is wired to backend APIs without major layout changes.

---

## 3. Data Model (Conceptual Tables)

### 3.1 `users` – Accounts

Each row = one SHK account.

Fields (conceptual):

- `id` – internal user ID.
- `email` – login; password handled securely by auth provider.
- `display_name` – global public name.
- `profile_image_url` – optional avatar.
- `email_verified` – bool or timestamp.
- `country` / `region` – optional, coarse location (for future localization).
- `role` / `is_admin` – basic admin flag.
- `settings` – JSON blob or separate table for user preferences (see §8).

### 3.2 `testimonies` – All Testimony Entries

Each row = one testimony event (small t), tied to a user.

**Core fields:**

- `id`
- `author_user_id` → `users.id`
- `category` (primary type):
  - `salvation_testimony`
  - `prayer_request`
  - `answered_prayer`
  - `daily_blessing`
  - `miracle_testimony`
  - `life_testimony` (general/other)
- `status`:
  - `draft` – only visible to owner, appears only in Drafts tab.
  - `submitted` – appears on personal page + (if allowed) on Testimonies Wall.
- `title`
- `body`

**Visibility & safety:**

- `visibility`:
  - `public` – shown with display name.
  - `public_anonymous` – shown as “Anonymous” (or similar).
  - `private` – only visible on owner’s page; never on Wall.
- `age_bracket`: `adult` | `minor` (simple v1 model).
- `consent_public` (for adults) – checkbox; yes/no.
- `minor_guardian_confirmed` – checkbox for testimonies about minors (v1 simple policy).
- `is_hidden` – admin-hidden from public (still in DB).
- `is_sensitive` – may require clickthrough or limited display.

**Linking & metadata:**

- `tags` – thematic labels (e.g., healing, provision, family, etc.).
- `scripture_refs` – optional list of references tied to the story.
- `event_date` – when it happened (if known).
- `submitted_at` – when it was posted.
- `linked_testimony_id` – for connecting an `answered_prayer` to its original `prayer_request`.
- `location_country`, `location_region`, `location_city` – optional manual fields.

### 3.3 `follows` – Private Follow Relationships

Each row = “User A follows User B’s testimonies.”

Fields:

- `id`
- `follower_user_id`
- `followee_user_id`
- `created_at`

Notes:

- No public follower counts or “who follows whom” lists.
- Used only for filtering the Wall with “Show only people I follow.”

### 3.4 `moderation_events` – Audit Log (Admins)

Each row = one moderator action on a testimony.

Fields:

- `id`
- `moderator_user_id`
- `testimony_id`
- `action` – e.g., `hide`, `unhide`, `change_visibility`, `mark_sensitive`, `feature`.
- `reason` – short note.
- `created_at`

Purpose: transparency and review of moderator actions; does not directly control display (that’s handled via fields on `testimonies`).

---

## 4. Accounts and Sign-Up

**Sign-up form (v1.0 minimal):**

- Email
- Password
- Display name

Everything else (salvation testimony, location, preferences) is set later on the Personal Testimony Page and settings.

**Age policy (v1 simple baseline):**

- Each testimony asks: “Is this about an adult or a minor (under 18)?”
- Minor-related testimonies:
  - Encouraged to be anonymous/private.
  - Public sharing requires a guardian confirmation checkbox.
- More nuanced age tiers (`<12`, 13–17 with parent verification, etc.) are flagged as a **v1.0 finalization/TBD** detail; current contract keeps it simple but future expansion is expected.

---

## 5. Visibility, Drafts, and Editing

- Any testimony can be edited by its owner:
  - Change `visibility` (public / anonymous / private).
  - Change `category`.
  - Edit text, tags, location, etc.
- `status`:
  - `draft` → appears only in Drafts tab; not counted as “submitted” or shown on Wall.
  - `submitted` → appears in All/type tabs; can show on Wall if public or public_anonymous (and not hidden by mods).
- Visibility is changeable at any time (e.g., public → private, or vice versa).

---

## 6. Moderation Model (v1.0)

- **Automated pre-check:**  
  - Basic computational moderation runs on each submitted testimony (profanity/abuse checks).
  - Obviously bad content is blocked or auto-flagged.

- **Auto-live:**  
  - If it passes pre-check, testimony appears immediately on:
    - Personal Testimony Page (owner view, per visibility).
    - Testimonies Wall (if `status=submitted` and `visibility` is public/public_anonymous and not `is_hidden`).

- **Post-moderation:**  
  - Moderators have a “Recent & Flagged” queue.
  - Actions: hide/unhide, change visibility, mark sensitive, etc.
  - All actions recorded in `moderation_events`.

- **User reports:**  
  - Each public testimony has a “Report” link.
  - Simple flow: pick 1 of a few reasons:
    - Inappropriate/offensive
    - Spam/scam
    - Personal info/privacy concern
    - Something else
  - Optional comment.
  - Reports push entries up in the mod queue; no direct replies to reporters.

- **Content guidelines (high-level):**
  - Not allowed:
    - Explicit sexual content, graphic violence/gore.
    - Hate speech, harassment, threats, promotion of harm or criminal acts.
    - Doxxing (private addresses/contact info).
    - Spam or non-testimony promotions.
  - Allowed but may be sensitive/edited:
    - Stories involving abuse, trauma, self-harm, etc., even when Christ-centered.
    - Stories identifying others without their consent.
  - Tone expectation: Christ-focused, honest, non-attacking, disagreements handled respectfully.

Specific moderation algorithms and thresholds are left as **implementation details**, to be tuned later.

---

## 7. Pages and URLs

### 7.1 Testimony Hub (Info Page)

- **URL:**  
  - `"/testimonies/"` (or `/community/testimonies/` depending on site structure)
- **Content:**
  - Explanation of what a testimony is, why it matters for the gospel, Scripture references.
  - Guidance on how to write and share a testimony.
  - Big buttons linking to:
    - **Testimonies Wall** (`/testimony-wall/`)
    - Mode-specific views: Prayer / Blessings / Miracles (via query params).
    - Future: Timeline view, Map view, etc.

### 7.2 Testimonies Wall (Global Feed)

- **URL:**  
  - `"/testimony-wall/"`

- **Default view:**
  - All testimonies, **Today** (last 24h in user’s timezone), newest first.

- **Top section:**
  - Title: “Testimonies Wall”.
  - Subtitle: “See how God is moving today through prayers, blessings, miracles, and testimonies.”
  - CTA: “Share a testimony” → goes to add-testimony flow on My Testimony page.

- **Filters row:**
  - **Type:**  
    - All / Prayer / Blessings / Miracles / General  
    - (Categories map to underlying `category` values.)
  - **Time:**  
    - `Today` (default)  
    - `Last 7 days`  
    - `Last 30 days`  
    - `All time`  
    - `Custom range…` (start/end date)
  - **Tags:**  
    - Free-text search or dropdown for common tags (e.g., healing, provision, family, identity).
  - **Follow filter:**  
    - `[ ] Show only people I follow` (applies on top of other filters).

- **Time model (timeline-ready):**
  - All time filters internally treated as a **date range**.
  - Future timeline/map will add a toggle between:
    - “Only this period” vs “Cumulative up to end date”.

- **Feed layout:**
  - One-column on mobile; optional two-column grid on wider screens.
  - Header for current time selection (e.g., “Today”).
  - Testimony cards (see below).
  - End-of-results behavior:
    - Button: “See more from this week” → expands time filter to `Last 7 days`.
    - If no results: Empty state:
      - “No testimonies match these filters yet.”
      - Button:  
        - “Share a testimony – Are you sure you haven’t missed something God has done in your life recently?”

- **Card design (each testimony):**
  - **Header:**
    - Type pill:  
      - Prayer (🙏), Blessing (🎁), Miracle (✨), General (📖), Salvation (✝️), Answered Prayer (✅).
    - Follow icon if from someone user follows (simple symbol, e.g., small star/cross).
    - Visibility icon:
      - Public (e.g., 🌍), Anonymous (e.g., 👤 with mask), Private never shown on Wall.
  - **Body:**
    - Title.
    - Short snippet of body text.
  - **Footer:**
    - Date (event or submitted; v1 uses submitted for display).
    - Tag chips.
    - Actions:
      - “View details”
      - “Report”
      - (Future: “Share” – can be hidden in v1.0 if not implemented.)

- **Entry points from other pages:**
  - Prayer page → `/testimony-wall/?mode=prayer`
  - Blessings page → `/testimony-wall/?mode=blessings`
  - Miracles page → `/testimony-wall/?mode=miracles`
  - These just pre-select the type filter.

### 7.3 Personal Testimony Page (“My Testimony”)

- **URL:**  
  - `"/account/testimony/"`

- **Header:**
  - Title: “My Testimony”.
  - Subtitle: “This is your story of how God is moving in your life.”
  - Button: “Add testimony”.

- **Salvation block (top):**
  - If salvation testimony exists:
    - Title: “✝️ My Salvation Story”.
    - Short preview.
    - Button: “View / Edit my salvation story”.
  - If not:
    - Banner:  
      - “Your salvation testimony isn’t written yet… Do you know why you follow Jesus and trust Him for salvation?”
      - Buttons:
        - “Write my salvation story”
        - “Learn more about salvation and testimony” → Testimony Hub.

- **Tabs/filters for user’s testimonies:**
  - All (default)
  - Prayer (🙏)
  - Blessings (🎁)
  - Miracles (✨)
  - General (📖)
  - Private (🔒)
  - Drafts (📝)

- **Behavior:**
  - **All:** all submitted testimonies (any visibility), with private entries clearly marked by a lock icon + muted style.
  - **Private:** only testimonies with `visibility=private`.
  - **Drafts:** only testimonies with `status=draft`.
  - Default sort: newest submitted first; possible later option to sort by event date.

- **Card actions (owner-only):**
  - Edit
  - Change visibility
  - Delete
  - For prayer requests:
    - If no linked answer: “Mark as answered / Add how God answered”.
      - Creates an `answered_prayer` and links via `linked_testimony_id`.
    - If linked: “Answered on {date} – View answer”.

---

## 8. User Settings (v1.0)

Minimal v1 settings stored per user:

1. **Default testimony visibility:**
   - Default value = **Public**.
   - Options: public / public-anonymous / private.
   - Located under a “Security/Privacy” or similar section (not front-and-center), to avoid discouraging sharing.

2. **Default Testimonies Wall filter:**
   - Initial mode: All.
   - Initial time window: Today.
   - Users may change these preferences later; default is used when visiting the Wall.

3. **Location behavior (v1.0):**
   - No special behavior; each testimony simply has optional fields:
     - Country
     - State/Province/Region
     - City
   - Strong encouragement (with a “Why?” help text) to fill at least country/region, explaining it helps future map views.  
   - No auto-detection/geolocation stored in v1.0 (future “Use my location” is v1.x).

---

## 9. Following UX

- On other users’ Personal Testimony pages:
  - Button: “Follow testimonies” / “Following” (toggle).
- On Testimonies Wall:
  - Filter: `[ ] Show only people I follow`.
  - Cards from followed users show a small icon (“from someone you follow”).

No public follower lists or counts in v1.0.

---

## 10. Metrics (v1.0)

Core health metrics to track (weekly/monthly):

1. **New testimonies:**
   - Counts by category.
   - Counts by visibility (public vs anonymous vs private).

2. **Wall usage:**
   - Number of visits to Testimonies Wall.
   - Fraction of sessions using “Following only”.
   - Breakdown of type filters used (Prayer/Blessings/Miracles/General).

3. **Moderation health:**
   - Number of reports.
   - Number of testimonies hidden or marked sensitive.
   - Approximate time-to-first-review for reported items.

---

## 11. Future v1.x Features (Out of v1.0 Scope, but Designed For)

These are intentionally **not** in v1.0, but v1.0 is architected so they can be added without major refactors:

1. **Timeline + Map Tool (coupled):**
   - Zoomable time axis (day ⇄ week ⇄ month ⇄ year ⇄ all-time).
   - Switch between:
     - Timeline view (events along time).
     - Map view (bubbles by region).
   - Both share the same filters (category, tags, follow, visibility, date range, cumulative toggle).

2. **Bubble (“Blessings Jar”) view:**
   - Bubble size driven by count of testimonies per tag/category.
   - Works on the same filtered set currently shown on Wall.

3. **Image attachments:**
   - Per-testimony image uploads via safe storage (later).
   - Thumbnails, size limits, moderation for visual content.

4. **Infinite Bible integration:**
   - Use same `users` + `settings` to store Infinite Bible notes/canvases later.
   - v1.0: front-end only or separate; data model prepared for future `ib_*` tables keyed by `user_id`.

5. **More detailed minors policy and guardian flows.**

---

This document should be sufficient context for any new chat or developer to understand the current v0.9 plan for:

- The **Testimonies Wall** (what it is, where it lives, how it behaves).
- **Personal Testimony Pages** and how users add/manage testimonies.
- Core **data structures**, **visibility rules**, **moderation model**, **user settings**, **follow system**, and **future expansions**.
