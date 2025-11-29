# SHK Daily Module – v1 Contract (Draft v0.1)

> NOTE: THIS IS A PLACEHOLDER.  
> v1 focuses on:
> - A daily experience (reading/interaction across several sections).
> - A simple per-user **completion log** and **streak** mechanic.
> Notifications/reminders and broader gamification are out-of-scope for v1.

## 1. Purpose & Goals

- Provide a **Daily** experience that encourages regular engagement with:
  - Scripture
  - Reflection
  - Simple interactive tools
- Track a simple **streak** for each authenticated user based on daily completion.

## 2. Core Concepts

- **Daily Entry (per calendar day)**
  - The content for a given date (e.g., verse, reflection questions, mini-tools).
  - Defined and stored separately from user data.

- **Daily Completion**
  - For v1, completion is defined as:
    - The user reaches the end of the Daily flow for that date and submits the final reflection/response OR triggers a clear “completed” action.
    - Exact UX behavior will be defined on the frontend but must boil down to “completed = yes/no for date D”.

- **Streak**
  - A simple count of **consecutive days** for which the user has completed the Daily.
  - Exact rules about what counts as a “missed day” (e.g., timezone boundaries) will follow `preferred_time_zone` or a global default. `[DECIDE-AFTER]`

## 3. Data Model (Conceptual)

- `DailyEntry` (content, not user-specific):
  - `id` (or date key).
  - `date` (e.g., `YYYY-MM-DD`).
  - Content fields (verse reference, reflection text, questions, etc.).

- `DailyLog` (per user, per day):
  - `user_id` → `User.id`.
  - `date` (same format as `DailyEntry`).
  - `completed` (boolean).
  - `completed_at` (timestamp, optional).

- `DailyStreak` (optional optimization):
  - Either computed on the fly from `DailyLog`, or cached as:
    - `user_id` → `User.id`.
    - `current_streak` (integer).
    - `longest_streak` (optional, future). `[DECIDE-AFTER]`
  - Implementation detail: for v1, a simple recomputation from `DailyLog` may be enough.

## 4. Behavior Rules (v1)

- A user can complete the Daily at most **once per date** for streak purposes:
  - Additional submissions or edits do not increment the streak again.
- Streaks:
  - Increment when the user completes the Daily for a new qualifying date.
  - Break when there is a gap day (according to the chosen timezone logic). `[DECIDE-AFTER]`
- Guests:
  - May view the Daily content but do **not** have a persisted streak.
- Restricted users (suspended/banned):
  - May view the Daily content as guests.
  - May not have new completion events persisted (module-specific decision; default assumption is **no new streak tracking**). `[UNDECIDED]`

## 5. Out of Scope for v1

The following are explicitly **out of scope** for v1:

- Notifications/reminders:
  - No daily email or push notifications to remind users to complete the Daily.
  - Any such behavior would require using `notifications_opt_in` and updated contracts. `[DECIDE-AFTER]`
- Broader gamification:
  - Achievements, badges, leaderboards.
  - Social comparisons of streaks.
- Per-question analytics or detailed tracking of individual answers (beyond minimal storage needed for the feature itself).
