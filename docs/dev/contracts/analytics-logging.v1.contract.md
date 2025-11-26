# SHK Analytics & Logging – v1 Contract (Draft v0.1)

> NOTE: THIS IS A PLACEHOLDER.  
> v1 focuses on **basic, aggregate analytics** and minimal logging, not detailed per-user behavior tracking.  
> `userId` is *optional* and is **not required or used** in v1. Future versions may expand this.

## 1. Purpose & Scope

- Provide a **high-level pattern** for analytics and logging across SHK.
- Ensure analytics stays:
  - Lightweight.
  - Respectful of user privacy.
  - Easy to describe in the public Privacy Policy.

## 2. v1 Scope (what we actually do)

For v1, analytics is limited to **aggregate, non-identifying metrics**, such as:

- Page views (by page path).
- Tool usage counts (e.g., how often Testimony, Daily, Bible Viewer pages are opened).
- Simple event counts (e.g., “testimony submitted”, “daily completed”) without storing per-user histories here.

Constraints:

- No detailed per-user behavior profiles.
- No cross-site tracking.
- No use of `User.id` as a required analytics key in v1.

## 3. Event Model (conceptual)

> NOTE: This is conceptual schema for future use; v1 may not implement every field.

- `LoggedEvent` (conceptual):

  - `id`: internal event id.
  - `timestamp`: when the event occurred.
  - `category`: e.g., `"pageview"`, `"tool_usage"`, `"action"`.
  - `name`: e.g., `"daily_opened"`, `"testimony_submitted"`.
  - `metadata`: small JSON blob with non-identifying details (e.g., page path, tool id).
  - `userId` (optional):
    - May be used in **future** versions for per-user metrics.
    - For v1, this field **must not** be relied on; it should be omitted or ignored. `[UNDECIDED][REVIEW-ADVISOR]`

## 4. Data Sources

- v1 analytics may be implemented via:
  - A third-party service (e.g., basic web analytics), **or**
  - A minimal custom logging table in the backend.
- In either case:
  - The default behavior is aggregate reports (counts, charts) at the project level.
  - Any per-user breakdowns (if ever enabled) must be explicitly documented and may require contract updates. `[DECIDE-AFTER][REVIEW-ADVISOR]`

## 5. Privacy & Retention

- Analytics data should:
  - Avoid storing direct identifiers like email or `User.id` wherever possible.
  - Avoid storing IP addresses long-term unless required for security. `[REVIEW-ADVISOR]`
- Retention:
  - v1 may retain aggregated analytics indefinitely for trend analysis.
  - Raw event logs (if any) should have a reasonable retention limit (e.g., 6–24 months) to be decided later. `[UNDECIDED][REVIEW-ADVISOR]`

## 6. Out of Scope for v1

The following are explicitly **out of scope** for v1 analytics:

- Full per-user behavior histories (e.g., detailed clickstreams per account).
- Cross-device or cross-site profiling.
- Personalized recommendations driven by analytics.
- Advanced abuse-detection logic based on behavioral analytics (beyond what the backend provides by default). `[DECIDE-AFTER]`
