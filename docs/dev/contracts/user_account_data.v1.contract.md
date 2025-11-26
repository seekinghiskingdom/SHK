# SHK Accounts and User Data – v1 Contract (Draft v0.9)

> Scope: Shared account and user-data system for all SHK tools (Testimony Wall, Infinite Bible, Daily Tools, Bible Viewer, etc.). This defines how users exist, authenticate, what global data is stored about them, and how feature modules attach their own data.

---

**Tag legend for open items**

- `[REVIEW-SELF]` – Looks right, but you want to personally re-check before launch.
- `[REVIEW-ADVISOR]` – You intend to confirm with an external advisor (legal, technical, pastoral, etc.).
- `[DECIDE-AFTER]` – Depends on later sections/decisions; finalize after the rest of this contract is drafted.
- `[UNDECIDED]` – Intentionally not decided; must be resolved before v1 is considered final.

---

## 1. Purpose and Goals

- Provide a **single, simple user identity** across the entire SHK ecosystem so all tools/features share the same `user_id`.
- **Minimize stored personal data** and keep it clearly documented, with privacy and safety as a priority.
- Make it easy for each tool/module (Testimonies, Infinite Bible, Daily Tools, etc.) to attach its own per-user data using that shared identity (always keyed by `user_id`).
- **Rely on a managed backend** for authentication, security, and email flows, avoiding custom security engineering.
- Keep the design **vendor-neutral** so the contract doesn’t depend on a specific platform (Supabase/Firebase/etc.), even if a specific provider is chosen for implementation.

---

## 2. Authentication and Identity

### 2.1 Auth assumptions

- Authentication is handled entirely by the managed backend (e.g., Supabase/Firebase-style service); SHK does not implement its own auth protocol.
- Supported flows in v1:
  - Email + password sign-up.
  - Email + password login.
  - Email verification via a verification link sent by the backend.
  - Password reset via an email flow provided by the backend.
- The SHK front-end:
  - Never stores or processes raw passwords beyond submitting them to backend auth endpoints over HTTPS.
  - Treats “logged in vs logged out” and “email verified vs not” as flags provided by the backend.
- Session management (tokens, refresh, expiry, etc.) is fully owned by the backend platform; SHK only checks whether a session is currently valid.

### 2.2 Core `User` model (global identity)

Each user in SHK is represented by a single `User` record. All tools/modules reference this `User.id` when storing per-user data.

#### 2.2.1 Technical & lifecycle fields

- `id`  
  - Stable internal identifier for the user (primary key for all user-related data).
- `created_at`  
  - Timestamp when the user account was created (backend-managed).
- `updated_at`  
  - Timestamp when the user account was last updated (backend-managed).
- `last_login_at`  
  - Timestamp of the user’s most recent successful login (backend-managed). `[REVIEW-SELF]`

#### 2.2.2 Login-related fields

- `email`  
  - User’s login email; not exposed publicly.
- `email_verified`  
  - Boolean; `true` once the backend’s email verification flow completes.
- `password_hash` (or equivalent backend field)  
  - Stored and managed by the backend; not exposed to SHK front-end logic.

#### 2.2.3 Public-facing identity

- `display_name`  
  - Required; human-readable name shown in modules that display authorship (e.g., Testimony Wall when not anonymous).
- `avatar_id`  
  - Optional string key referencing one of the preset Christian-themed avatars (no uploads in v1).

#### 2.2.4 Legal / consent flags

- `accepted_terms`  
  - Boolean; `true` when the user has accepted the current Terms of Use.
- `accepted_privacy_policy`  
  - Boolean; `true` when the user has accepted the current Privacy Policy (may be combined with `accepted_terms` in implementation, but conceptually tracked). `[REVIEW-SELF]`
- `is_13_plus`  
  - Boolean; `true` when the user confirms they are at least 13 years old. `[REVIEW-ADVISOR]`
- `is_minor_with_parent_consent`  
  - Optional boolean; `true` when the user (13–17) confirms parent/guardian consent. `[REVIEW-ADVISOR]`

> Exact legal wording and display text for age/consent will be validated with a legal advisor before launch. `[REVIEW-ADVISOR]`

#### 2.2.5 Role / permissions and account status

- `role`  
  - Enum: `user`, `moderator`, `admin`.
  - All new accounts start as `user`.
  - Role changes are performed manually in the backend for v1 (no self-promotion flows or codes in the UI).

- `status`  
  - Enum:  
    - `active` – normal account; user can log in and use allowed features.  
    - `suspended` – login blocked; intended for temporary blocks.  
    - `banned` – login blocked; intended for long-term or permanent bans.  
  - Used for internal moderation and safety; not surfaced directly to other users. `[DECIDE-AFTER]`

- `suspended_until` (optional)  
  - Optional datetime indicating the intended end of a suspension (for admin reference). No automatic re-activation logic is required at v1; admins change `status` manually. `[DECIDE-AFTER]`

#### 2.2.6 Privacy of internal fields

- Internal-only fields (`email`, legal/consent flags, `role`, `status`, `suspended_until`, timestamps) are **never shown directly** to other users.
- Modules may only surface:
  - `display_name` and `avatar_id` when their own visibility rules allow it.
- Any additional per-module exposure of user-related information must be defined explicitly in that module’s contract.

---

## 3. Roles and Global Permissions `[REVIEW-SELF]`

### 3.1 Role overview

SHK uses a simple, global role model that applies across all tools/modules:

- `user` – normal account; can use public features and create/manage their own content where modules allow.
- `moderator` – trusted account; can review and manage other users’ content within specific modules (e.g., testimonies).
- `admin` – highest-level account; can manage roles, account status, and sensitive administrative actions.

Fine-grained actions (exactly what each role can do in a given tool) are defined in each module’s contract, but must not violate the global privacy rules defined here.

### 3.2 Global capabilities per role (high level)

- `user`
  - Create and manage their own content in modules that support it (e.g., testimonies, saved Infinite Bible data).
  - View public content and their own private content.
  - Update their own profile fields (display_name, avatar choice, global preferences).
  - Request account deletion through the support/admin process (v1).

- `moderator`
  - All `user` capabilities.
  - Additional privileges in selected modules (e.g., Testimony Wall, future community tools), such as:
    - View and moderate user-generated content (approve/hide, review reports, view items marked as private where necessary for safety).
  - May see:
    - The owner’s `display_name` and `avatar_id`.
    - Internal IDs needed for moderation (e.g., `user_id`, `testimony_id`).
  - May **not** see:
    - User email addresses.
    - Legal/consent flags or account status fields.
  - Moderation powers are intended for a wider trusted group and are consistent across all SHK tools that support moderation. `[REVIEW-SELF]`

- `admin`
  - All `moderator` capabilities.
  - Manage roles:
    - Promote/demote between `user`, `moderator`, and `admin`.
  - Manage account status:
    - Change `status` (`active`, `suspended`, `banned`) and set/clear `suspended_until`.
  - Handle sensitive account-level operations:
    - Respond to deletion/data requests.
    - Oversee high-risk or legal/financial aspects as needed.
  - May see:
    - User email addresses (for support and critical communication). `[REVIEW-ADVISOR]`
    - Legal/consent flags (`accepted_terms`, `is_13_plus`, etc.) when necessary for compliance and safety. `[REVIEW-ADVISOR]`

### 3.3 Role assignment and changes (v1)

- All new accounts are created with `role = user`.
- A small, trusted set of internal team members are configured as `admin` accounts.
- A larger but still curated group of trusted friends/mentors may be given `moderator` accounts to help with content moderation across tools.
- Role changes (promotion/demotion) are performed manually via the backend/admin console in v1.
- No self-service promotion, invite codes, or in-UI role changes are supported at launch.

### 3.4 Account status interaction with roles

- `status` (`active` / `suspended` / `banned`) applies to all roles:
  - `active` – user can log in and use allowed authenticated features.
  - `suspended` / `banned` – user is not allowed to perform authenticated actions (e.g., posting, editing, saving) while the status is in effect.
- Suspended/banned users may still access publicly available SHK content in a way equivalent to guests (read-only), subject to per-module rules. `[DECIDE-AFTER]`
- `suspended_until` (if set) is advisory for admins (for reminder/notes) but does not automatically change `status` in v1. `[DECIDE-AFTER]`
- Role changes do not override `status`; an account must be `active` to function normally as an authenticated user.


### 3.5 Cross-module principles

- Each module (Testimony, Infinite Bible, Daily Tools, etc.) defines:
  - Which roles can perform which actions in that module.
  - What additional internal data moderators/admins can see in that module’s context.
- No module may:
  - Expose internal-only fields (email, legal/consent flags, `status`, `suspended_until`) directly to other users.
  - Grant permissions that conflict with or bypass the global role and status rules defined here.
- Moderation behavior (what `moderator` can do) should be kept conceptually consistent across modules so the team can apply the same patterns and expectations platform-wide. `[REVIEW-SELF]`

---


## 4. Global User Preferences

### 4.1 Preference model

- Each user has **one preferences record/object**, keyed by `user_id`.
- This record can contain:
  - A small set of **global** preferences that apply across SHK.
  - **Module-specific** preference sections (e.g., Testimony, Infinite Bible), defined in each module contract.
- Modules must not overwrite or reinterpret other modules’ preference keys; shared keys are defined here in the global section.

### 4.2 Global preferences for v1

The following preferences are stored once per user and may be read by multiple tools:

- `preferred_language`
  - A simple language code, e.g., `"en"`.
  - For v1:
    - Used primarily to choose defaults for Bible-related tools and content where multiple language options exist.
    - In the future, may be used to influence site-wide language once more pages/content are localized.
  - Settable by the user after account creation (e.g., in an “Account settings” or onboarding checklist).

- `preferred_time_zone`
  - An IANA time zone string, e.g., `"America/Chicago"`.
  - Used for:
    - Displaying dates/times (e.g., in tools that reference “today,” “this week,” or schedule-based features).
    - Future daily/weekly tools that may depend on the user’s local day.
  - Settable by the user post-signup; SHK does not infer or track physical location automatically in v1. `[REVIEW-SELF]`

- `default_region` (optional, coarse location)
  - A coarse, user-provided region string (e.g., country, state, or city) used for convenience in tools that reference location (e.g., map views, region filters). `[REVIEW-ADVISOR]`
  - Intended to be:
    - Optional.
    - High-level (no precise address; typical formats like “USA”, “Brazil”, “India – Chennai”).
  - For v1, primarily used to:
    - Pre-fill region/location fields in modules like the Testimony system or map-based tools.
    - Support future visualizations (e.g., maps showing where testimonies or activity are coming from).
  - Exact recommended granularity and wording to be confirmed with a legal/privacy advisor. `[REVIEW-ADVISOR]`

- `ui_theme` `[REVIEW-SELF]`
  - A simple UI theme preference, one of `"light"` or `"dark"`.
  - Behavior:
    - If `ui_theme` is not set yet, the front-end should read the system/OS preference (`prefers-color-scheme`) and apply that theme for the session.
    - On first save (e.g., when the user confirms settings), the chosen theme is stored as `ui_theme` so it stays consistent across devices.
  - If `ui_theme` is already set, the stored value overrides system preference and is used across SHK tools for logged-in users.

- `notifications_opt_in`
  - Boolean; default `false`. `[REVIEW-SELF][REVIEW-ADVISOR]`
  - Global flag indicating whether the user has opted in to non-essential SHK updates (see Section 6.4 for details).



### 4.3 Module-specific preferences (pattern)

- Each module (Testimony, Infinite Bible, Daily Tools, etc.) may define its own preference keys under a module-specific namespace or structure in the user’s preferences record (e.g., `preferences.testimony.default_visibility`, `preferences.ib.default_translation`).

- All such keys:
  - Are keyed by `user_id`.
  - Are defined in the respective module’s contract.
  - Must not leak sensitive information or conflict with global privacy rules.

### 4.4 Onboarding and setup (UX note)

- The account creation flow should remain **simple** (email, password, display_name, required legal checkboxes).
- After account creation, users may be guided through an optional “setup checklist” (UX only, not enforced at backend) which can include:
  - Choosing an avatar.
  - Setting `preferred_language`.
  - Setting `preferred_time_zone`.
  - Optionally setting `default_region`.
  - Optionally choosing `ui_theme`.
  - Initial module-specific steps such as:
    - Writing a first testimony.
    - Choosing default testimony visibility.
- Exact onboarding UX is not enforced by this contract but should be designed to encourage users to fill these fields over time without gatekeeping basic access. `[DECIDE-AFTER]`


---


## 5. Account Lifecycle and Retention

### 5.1 Creation

- New accounts are created through the standard signup flow:
  - Required: `email`, `password`, `display_name`, required legal checkboxes (terms/privacy, 13+ confirmation).
  - Optional: avatar selection and preferences (e.g., language, time zone, region) can be set later.
- Default values:
  - `role = user`
  - `status = active`
  - `email_verified = false` until the backend verification flow is completed.

### 5.2 Suspension and bans

- `status` encodes whether an account can log in and use authenticated features:
  - `active` – normal use allowed.
  - `suspended` – login blocked; intended for temporary or investigative blocks.
  - `banned` – login blocked; intended for long-term or permanent bans.
- For v1:
  - Status changes (`active` ↔ `suspended` / `banned`) are performed manually by an `admin` via the backend/admin console.
  - `suspended_until` may be set as an internal reminder for admins but does not automatically change `status`. `[DECIDE-AFTER]`
- Modules must treat `suspended` and `banned` accounts as **not allowed** to create or interact with content while the status is in effect.

### 5.3 “Deletion” behavior (v1 default pattern)

- SHK uses **deactivation + content hiding/anonymization** as the default “delete” behavior for v1:
  - Admins normally set `status = banned` instead of hard-deleting the `User` record.
  - Module data (e.g., testimonies, IB data) remains in storage but:
    - Is hidden from public lists and user-facing views by default, or
    - Is anonymized where the module contract specifies.
- Hard deletion of the `User` record (and full data removal) is considered an exceptional, manual operation and is not the default v1 pattern. `[REVIEW-ADVISOR]`

### 5.4 Appeals and long-term bans

- Bans are intended to be **long-term** by default; there is no automatic unban schedule in v1.
- Appeals process (v1):
  - Users may request review of a ban/suspension only by explicitly contacting SHK through external channels (e.g., support email or contact form).
  - Admins review context and, if appropriate, may:
    - Change `status` from `banned`/`suspended` back to `active`.
    - Adjust module-level visibility/anonymization according to module contracts.
- No automated unban logic or in-app appeal UI is required in v1; all appeals are handled manually by admins on a case-by-case basis. `[DECIDE-AFTER]`


### 5.5 Data retention (global)

- By default, SHK retains account and per-module data for safety, audit, and abuse prevention, even when a user is banned or deactivated. `[REVIEW-ADVISOR]`
- Exact retention periods and deletion/anonymization rules (e.g., after X years of inactivity or upon verified legal request) will be:
  - Documented in Terms/Privacy.
  - Further refined in module contracts where necessary (e.g., how testimonies are handled on account “deletion”).


---


## 6. Security and Email

### 6.1 Security baseline

- SHK relies on the managed backend for:
  - Secure password storage (hashing, salting, etc.).
  - Protection against common attacks (rate limiting, brute-force protection, etc.).
  - Secure session management (tokens, refresh, expiry).
- SHK front-end responsibilities:
  - Only send credentials over HTTPS to the backend’s auth endpoints.
  - Never log or persist raw passwords or tokens in insecure storage.
  - Respect “logged in / logged out” and `email_verified` flags from the backend when deciding what actions are allowed.

- Password rules:
  - Complexity and length rules **fully follow backend defaults**; SHK does not implement separate mandatory password checks in the front-end for v1. `[REVIEW-SELF]`
  - Where possible, password strength and requirements should be configured using backend/platform settings rather than custom code. `[REVIEW-SELF]`

### 6.2 System vs non-essential emails

- **System emails (required)** – provided by the backend:
  - Email verification (on sign-up or email change).
  - Password reset.
  - Optional security alerts (e.g., suspicious login notifications) if enabled at the backend; these are not required for v1 behavior and may be configured later via backend settings without changing this contract. `[DECIDE-AFTER]`

- System emails:
  - Do not require extra opt-in; they are part of having an account.
  - Must be limited to security/account functions, not general marketing or promotional content.

- **Non-essential emails (optional)** – e.g., newsletters, monthly stats, general updates:
  - Are treated as one possible type of “non-essential notifications” and must be governed by the `notifications_opt_in` preference (see 6.4). `[REVIEW-ADVISOR]`
  - v1 does **not** require sending any such non-essential notifications; the flag may remain unused until a later release.
  - Any future non-essential email features must:
    - Check `notifications_opt_in == true` before sending.
    - Be clearly described in Terms/Privacy and/or the settings UI.

### 6.3 Email visibility and access

- Email addresses are treated as sensitive internal data:
  - Not shown to other users.
  - Visible only to `admin` roles in support and safety contexts, not to `moderator` roles. `[REVIEW-ADVISOR]`
- Modules must not expose email addresses in any public or user-to-user interface unless a future module contract explicitly and narrowly allows it (e.g., a dedicated, controlled contact mechanism). `[REVIEW-ADVISOR]`

### 6.4 Non-essential notifications preference

- `notifications_opt_in`
  - Boolean; default `false`. `[REVIEW-SELF][REVIEW-ADVISOR]`
  - Indicates whether the user has explicitly opted in to receive **non-essential** updates from SHK (e.g., newsletters, monthly stats, feature change announcements).
  - For v1:
    - No non-essential notifications are required; this flag may remain unused until a later release.
    - When non-essential notifications (email or in-app) are introduced, they must:
      - Check `notifications_opt_in == true` before sending.
      - Respect any additional, more granular notification settings defined later (e.g., separate opt-ins for email vs in-app).


---


## 7. Integration with Feature Modules

### 7.1 Per-module data pattern (ID-only link rule)

- Every feature module (e.g., Testimony, Infinite Bible, Daily Tools, Bible Viewer) stores its own data in its own tables/collections.
- All per-user data in modules:
  - Must reference `User.id` as a foreign key field (e.g., `user_id`, `owner_user_id`).
  - Must **not** define its own separate user identity model.
- Modules **must not** store independent copies of core user fields such as:
  - `email`, `display_name`, `role`, `status`, legal/consent flags.
- When modules need user information (e.g., display name, avatar), they look it up through `User.id` instead of duplicating it in their own records.

Examples (conceptual):

- Testimony module:
  - `Testimony.owner_user_id` → `User.id`
- Infinite Bible module:
  - `IBBoard.user_id` → `User.id`
  - `IBSettings.user_id` → `User.id`
- Daily tools and other modules:
  - `{ModuleThing}.user_id` → `User.id` in the same way.

### 7.2 Respecting global privacy, roles, and status

- All modules must obey the global rules defined in this contract:
  - Privacy:
    - Internal-only fields (`email`, legal/consent flags, `status`, `suspended_until`, etc.) remain internal; modules cannot expose them directly.
  - Roles:
    - `user`, `moderator`, `admin` meanings come from this contract.
    - Modules may define finer-grained permissions per role (in module contracts) but cannot contradict these global meanings.
  - Status:
    - If a user’s `status` is `active`, modules treat them as a normal authenticated user (subject to module-specific rules).
    - If a user’s `status` is `suspended` or `banned`:
      - They must not be allowed to perform actions that affect public content or other users (e.g., posting, editing, sending messages). `[DECIDE-AFTER]`
      - They should still be able to access SHK content in a way that is equivalent to a guest (read-only access where safe), subject to per-module rules. `[DECIDE-AFTER][UNDECIDED]`

### 7.3 Module-specific preferences (namespaced)

- Each module may define its own preference keys under a module-specific namespace or structure within the user’s preferences record, for example:
  - `preferences.testimony.default_visibility`
  - `preferences.testimony.default_anonymous`
  - `preferences.ib.default_translation`
  - `preferences.daily_tools.show_intro`
- All such keys:
  - Are keyed by `user_id`.
  - Are documented in the respective module’s contract.
  - Must not overwrite or reinterpret global keys defined in Section 4.
- If a module-specific setting becomes widely used across multiple modules (e.g., language, region, theme), it should be **promoted** into the global preferences section, and modules should read it from there going forward. `[REVIEW-SELF]`

### 7.4 Module independence and evolution

- Modules should be designed so they can be:
  - Added or removed without changing the core `User` model.
  - Evolved (v1 → v1.1 → v2) with their own contracts, as long as they remain keyed by `user_id` and respect global rules.
- The Accounts and User Data contract is the **source of truth** for:
  - Identity, roles, legal/consent flags, and global preferences.
- Modules depend on this contract; this contract does **not** depend on any single module.

### 7.5 Guest vs authenticated behavior (placeholder)

- SHK distinguishes between:
  - **Guest users** (not logged in).
  - **Authenticated users** (`status = active`).
  - **Authenticated but restricted users** (`status = suspended` or `banned`).
- For v1:
  - Guests and restricted users should both be able to access Bible content and other resources in a read-only way, as safely as possible. `[DECIDE-AFTER][UNDECIDED]`
  - The exact capabilities of guests vs authenticated users (per module) will be defined in:
    - Module contracts (for tool-specific actions), and/or
    - A separate “Guest vs Authenticated Permissions” doc to be drafted later. `[UNDECIDED]`


---


## 8. Explicitly Out of Scope for v1 (Accounts & Backend)

The items below are **not required for v1 launch** of the SHK accounts system. They may be added in later releases without changing the core `User` model.

### 8.1 Authentication and security features 

- OAuth / social login (Google, Apple, etc.). `[DECIDE-AFTER]`
- Multi-factor authentication (MFA) / 2FA. `[DECIDE-AFTER]`
- Device/session management UI (listing active sessions, remote logout, etc.). `[DECIDE-AFTER]`
- Per-IP or per-device blocking rules (beyond what the backend provides by default). `[DECIDE-AFTER]`
- Automated security alerts configuration (e.g., “new device login” emails) beyond basic verification/reset. `[DECIDE-AFTER]`

### 8.2 Account management and user rights UI

- Self-service account deletion UI; v1 uses admin-handled deletion/deactivation only. `[DECIDE-AFTER]`
- Self-service role changes or moderator/admin applications (no in-app promotion flows).  
- Automated unban/suspension expiry logic (no scheduled status changes; all manual). `[DECIDE-AFTER]`
- In-app appeals workflow for bans/suspensions (handled manually via external contact in v1). `[DECIDE-AFTER]`
- Automated data export tools (e.g., “download my data”); any such requests are handled manually by admins in v1. `[DECIDE-AFTER][REVIEW-ADVISOR]`

### 8.3 Profile and social features

- Public profile pages beyond what individual modules display (e.g., no global “/user/username” pages). `[DECIDE-AFTER]`
- Extended profile fields (bio, links, denomination, detailed location, etc.). `[DECIDE-AFTER][REVIEW-ADVISOR]`
- Direct messaging between users, friend/follow systems, or social graphs. `[DECIDE-AFTER]`
- Rich media in profiles (user-uploaded avatar images, banners, etc.). `[DECIDE-AFTER]`

### 8.4 Notifications and communication

- Granular notification categories (separate toggles for newsletters, feature announcements, per-module alerts, etc.); v1 uses a single `notifications_opt_in` flag only. `[DECIDE-AFTER]`
- In-app notification center or notification feed UI. `[DECIDE-AFTER]`
- Scheduled or automated newsletters / monthly stats emails (enabled only in a future release that uses `notifications_opt_in`). `[DECIDE-AFTER][REVIEW-ADVISOR]`

### 8.5 Backend configuration and analytics

- Custom abuse-detection logic (per-user rate limits, heuristics for spam detection, etc.) beyond the backend’s built-in protections; may be added later as separate policies or services. `[DECIDE-AFTER]`
- Detailed behavioral analytics tied to individual users (beyond minimal metrics needed for operations). `[REVIEW-ADVISOR]`
- Multi-tenant or organization/“team account” features (separate from individual user accounts). `[DECIDE-AFTER]`

### 8.6 Likely early upgrades vs later features

The following items are **potential early upgrades** (v1.1+), if time and capacity allow:

- A separate “Guest vs Authenticated Permissions” doc that defines, per module, what guests, active users, and banned/suspended users can do. `[DECIDE-AFTER]`
- Enabling optional backend-provided security alerts (e.g., new device / suspicious login), **only if this can be done via simple backend configuration** without custom logic. `[DECIDE-AFTER]`
- Using `notifications_opt_in` for a single, rare “important updates” channel (e.g., occasional email announcements), not routine newsletters. `[DECIDE-AFTER][REVIEW-ADVISOR]`

Everything else listed in Section 8 should be treated as **longer-term** (well after v1) and not considered for launch planning.


---


## 9. PWA and Installed App Considerations (v0.1 Placeholder)

> Scope: This section captures high-level requirements and questions for running SHK as a Progressive Web App (PWA) and/or packaging it for app stores. It does **not** expand the core `User` model; it constrains how that model is used on devices and in distribution.

### 9.1 Canonical data vs local caches

- Canonical account data:
  - The managed backend remains the **source of truth** for all `User` fields and module data.
  - Local/device storage (PWA caches, IndexedDB, etc.) is treated as a **cache** or temporary workspace only.
- Sensitive fields:
  - The following must **not** be stored unencrypted in long-term client storage (localStorage, IndexedDB, file exports, etc.):  
    - `email`, legal/consent flags, `role`, `status`, `suspended_until`, and any similar internal-only fields.
  - Local caches should contain at most:
    - Public or quasi-public content (e.g., Bible texts, public testimonies).
    - User settings that are safe to store locally (theme, last open tool, board layouts, etc.).
- Sync behavior:
  - When offline, the app may allow local editing of module data (e.g., notes), but once online:
    - Changes sync to the backend under the same privacy/role/status rules.
  - Exact offline/sync rules are defined per module and may be added later. `[DECIDE-AFTER]`

### 9.2 Notifications (email vs push)

- `notifications_opt_in`:
  - Continues to govern all **non-essential** notifications, regardless of channel (email and/or push). `[REVIEW-ADVISOR]`
- Push notifications (PWA / app):
  - Any future push notifications must:
    - Respect `notifications_opt_in == true`.
    - Respect operating system–level notification settings (if the user blocks notifications in the OS, no pushes are sent).
  - v1 (web-only) does not require push notifications.
  - If push is added later, this section will be expanded with per-channel/per-module rules. `[DECIDE-AFTER]`
- System emails (verification, password reset, critical security notices) remain **outside** `notifications_opt_in` (they are mandatory for account operation), as defined in Section 6.

### 9.3 Guest vs authenticated vs banned in PWA

- The states defined in Section 7.5 apply directly to the PWA/app:
  - Guest: installed or opened app, not logged in.
  - Authenticated: logged in with `status = active`.
  - Restricted: logged in user with `status = suspended` or `banned`.
- Behavioral rule:
  - Restricted users must be treated like guests for all public-facing actions:
    - Read-only access to content where safe.
    - No posting, editing, or other actions that affect public content or other users. `[DECIDE-AFTER]`
  - Guests and restricted users may be subject to the same per-module rate limits and constraints to protect performance and abuse. `[DECIDE-AFTER]`
- Exact capabilities for each state (per module) will be defined in:
  - Module contracts, and/or
  - A dedicated “Guest vs Authenticated Permissions” document referenced from this section. `[UNDECIDED]`

### 9.4 App-store distribution and account controls

- If SHK is distributed through app stores (Apple/Google):
  - Platform policies may require:
    - In-app **account deletion** or deactivation flows.
    - Clear explanations of data usage and retention.
  - This contract currently treats:
    - Self-service account deletion as **out of scope** for web v1 (Section 8.2).
- Before any App Store submission:
  - Section 8.2 must be revisited to:
    - Add a user-visible “Delete my account” or “Request deletion” flow that matches store requirements. `[DECIDE-AFTER][REVIEW-ADVISOR]`
    - Clarify how retained data (e.g., anonymized testimonies) is handled when an account is deleted.
  - Terms/Privacy must be updated to align with store policies. `[REVIEW-ADVISOR]`

### 9.5 Analytics and telemetry in installed contexts

- v1 (web-only) treats detailed per-user analytics as out of scope (Section 8.5).
- For PWA/app contexts:
  - Minimal, non-identifying telemetry (e.g., crash reports, performance metrics) may be acceptable **only if**:
    - It does not conflict with the “minimal data” goal of this contract.
    - It is disclosed in Terms/Privacy. `[REVIEW-ADVISOR]`
  - Any move to richer per-user analytics (per-device session traces, behavior profiles, etc.) would:
    - Require a revision of Section 8.5 (removing it from “out of scope”), and
    - Additional user controls (e.g., opt-outs) where appropriate. `[DECIDE-AFTER][REVIEW-ADVISOR]`

### 9.6 Status of this section

- This PWA/App section is a **placeholder** for planning and constraints:
  - It does not change the core `User` model.
  - It sets guardrails around local storage, notifications, and distribution requirements.
- Before a serious PWA push or any app-store submission:
  - This section will be reviewed together with:
    - Section 6 (Security & Email),
    - Section 7.5 (Guest vs authenticated behavior),
    - Section 8.2 and 8.5 (deletion and analytics),
  - And updated to reflect concrete implementation choices and legal advice. `[REVIEW-ADVISOR]`


---


> v1 focuses on: a single `User` model, basic email/password auth, simple roles (`user`/`moderator`/`admin`), minimal global preferences, and a ban/suspension system that restricts public-impact actions while still allowing guest-level access to core content where safe. All other account-related features are explicitly optional and deferred.
