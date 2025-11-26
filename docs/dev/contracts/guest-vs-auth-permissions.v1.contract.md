# SHK Guest vs Authenticated Permissions – v1 Contract (Draft v0.1)

> NOTE: THIS IS A PLACEHOLDER.  
> v1 focuses on simple, clear differences between:
> - Guests (not logged in)
> - Authenticated users (`status = active`)
> - Restricted users (`status = suspended` / `banned`, treated like guests)

## 1. Role States

- **Guest**
  - Not logged in.
  - Has no `User` account or is not currently authenticated.

- **Authenticated (Active User)**
  - Logged in with a valid `User` account.
  - `status = active`.

- **Restricted (Suspended / Banned)**
  - Logged in or known to the system, but `status = suspended` or `banned`.
  - Treated like a guest for public-facing features (read-only), with no ability to affect other users or public content.

## 2. Permissions by State (High-Level)

### 2.1 Guest

- **Allowed:**
  - View public SHK pages and content (Bible texts, public testimonies, public daily content, etc.).
  - Browse public tools in a read-only manner where possible.
- **Not allowed:**
  - Create or edit testimonies / prayers / blessings.
  - Save personal preferences or streaks.
  - Access any account-specific dashboards or “My content” views.
  - Perform moderation or admin actions.

### 2.2 Authenticated (Active User)

- **Allowed (general):**
  - All guest actions.
  - Create and manage their own content in supported modules, including:
    - Testimony / prayer / blessing posts.
    - Daily streak progress (by completing the daily).
    - Tool-specific saved data (as modules are implemented).
  - Save and update global preferences (language, time zone, region, theme, notifications_opt_in).
- **Not allowed:**
  - Direct moderation or admin actions (unless `role = moderator` or `admin`).
  - Viewing other users’ internal data (email, legal flags, etc.).

### 2.3 Restricted (Suspended / Banned)

- **Allowed:**
  - Access SHK content in a read-only way that is equivalent to guest access, where safe.
- **Not allowed:**
  - Any actions that affect public content or other users:
    - No posting or editing testimonies.
    - No creating or editing any other public-facing content.
    - No tool usage that sends new dynamic data to the backend (subject to module-specific rules). `[DECIDE-AFTER]`
  - No moderation or admin actions, even if the account previously had elevated roles.

- **Behavior note:**
  - Exact per-module behavior for restricted users (e.g., whether they can still save purely private data like drafts) will be defined in each module contract and/or updated here later. `[UNDECIDED]`

## 3. Modules and This Contract

- Each module (Testimony, Daily, Bible tools, etc.) must:
  - Respect this high-level permission model.
  - Define module-specific actions that map to:
    - Guest-only actions.
    - Authenticated-only actions.
    - Actions blocked for restricted users.
- A future revision may include a full matrix (module × state × action). For v1, this document only sets the **global pattern**.
