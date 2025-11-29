
# SHK Backend Phase Template (v1)

> Working template for any **single backend phase** (e.g., `ACC P1.2 – Account search`, `TEST P2.0 – Salvation testimonies`).
> Fill this out before implementation, keep it updated during dev, and finalize it at QA.

---

## A. Phase name, scope, and goals

**Phase ID:**  
**Short name:**  
**Owner(s):**  
**Target release (v1.0 / later):**

**Scope summary (1–3 bullets):**
- 
- 

**Primary goals / outcomes:**
- 
- 

**Out of scope (for this phase):**
- 
- 

---

## B. Data model – tables and columns

For each table touched in this phase, list purpose and schema. Mark (NEW), (CHANGED), or (READ‑ONLY).

### B1. Tables overview

- **Table 1:** `schema.table_name` — purpose (e.g., “user-facing profiles, 1:1 with auth.users”)
- **Table 2:** `schema.table_name` — purpose
- …  

### B2. Detailed schema

Repeat per table.

**Table:** `schema.table_name`  (NEW / CHANGED / READ‑ONLY)  
**Row identity:** (e.g., `id` UUID, or composite key)

**Columns:**

| Column name | Type        | Null? | Default | Notes / meaning |
|------------|-------------|-------|---------|-----------------|
|            |             |       |         |                 |

**Indexes & constraints:**

- PK:  
- Unique:  
- FKs:  
- Other constraints (CHECK, etc.):  

---

## C. SQL / migrations required

List each distinct change that needs to be applied via SQL or migration, not the literal code (you can link to .sql files).

1. **Migration C1 – Create/alter tables**
   - What it does:
   - Tables affected:
2. **Migration C2 – Indexes**
   - What it does:
   - Tables affected:
3. **Migration C3 – Seed / backfill**
   - What it does:
   - Tables affected:

Note any ordering requirements or rollback notes.

---

## D. Pages, routes, and UI entry points

List all site surfaces this phase touches (existing or new).

### D1. Public/guest routes

- `/path/` — purpose, anon vs. signed‑in behavior
- …

### D2. Authenticated user routes

- `/account/...`  
- `/testimony/...`  
- …

### D3. Admin / moderator routes

- `/admin/...` or `/manage/...`  
- What this phase adds/enables on those routes:

### D4. Components and partials

- Shared components/partials this phase depends on or modifies:
  - `header.html` (account pill, nav)  
  - `site.js` (global Supabase client, helpers)  
  - etc.

---

## E. Supabase / wiring behavior

High‑level description of how this phase talks to Supabase (no code).

### E1. Reads

- Which tables are read?
- By whom (guest vs. logged‑in vs. admin)?
- Typical filters (by `user_id`, `handle`, public flags, etc.):

### E2. Writes / updates

- Which tables can be inserted/updated/deleted in this phase?
- Who is allowed to perform each kind of write?
- Any rate‑limit or “safety” rules (e.g., “user can change handle at most once per 30 days”)?

### E3. Cross‑module interactions

- Does this phase rely on data written by another module/phase?
- Does it produce data that later phases depend on?

---

## F. Data flows and visibility (private vs public)

### F1. Per‑field privacy

For each user‑visible field, specify where it lives and who can see it.

Example table:

| Concept / Field         | Source table.column | Visible to self | Visible to other signed‑in users | Visible to guests | Notes |
|------------------------|---------------------|-----------------|----------------------------------|-------------------|-------|
| Display name           |                     | Yes             | Yes                              | Yes               |       |
| Email                  |                     | Yes             | No                               | No                |       |
| Salvation testimony    |                     | Yes             | Yes/No (depending on flag)       | Yes/No            |       |

### F2. RLS‑sensitive behaviors

- For **signed‑out** users:
  - Which tables can they query?
  - Which columns can they see?
- For **signed‑in regular** users:
  - Which rows can they see (ownership rules)?
  - Which rows can they write (INSERT/UPDATE/DELETE)?
- For **mods/admins**:
  - Any elevated visibility or write powers specific to this phase?

---

## G. Row‑Level Security (RLS) and policies

Summarize the intended RLS model for this phase. You’ll still write the real policies in SQL elsewhere.

### G1. Policy overview (per table)

For each table touched:

- `schema.table`:
  - `SELECT` — who and under what conditions?
  - `INSERT` — who and under what conditions?
  - `UPDATE` — who and under what conditions?
  - `DELETE` — who and under what conditions?

### G2. Test scenarios

List concrete test cases you’ll run later (e.g., via Supabase SQL editor or app behavior):

- Guest tries to `SELECT` from `table` with filter X → expected result.
- User A tries to update resource owned by User B → expected error.
- Admin tries to moderate content → expected success.

---

## H. QA and acceptance criteria

What must be true to call this phase “done” and safe?

### H1. Manual test checklist (in app)

Numbered list of specific user flows to test:

1. 
2. 
3. 

Cover: happy path, edge cases, error messages, role differences.

### H2. Technical validation

- Queries behave as expected for guest/user/admin.
- RLS policy tests pass.
- No console errors or Supabase warnings in normal flows.
- Migrations apply cleanly on a fresh database.

### H3. Definition of Done (DoD)

Short bullet list:

- 
- 
- 

---

## I. Post‑deploy monitoring and maintenance

What you’ll watch after deployment, and what actions you’ll be ready to take.

### I1. Metrics / logs to watch

- Auth failures, sign‑up error rates
- RLS violation logs or 401/403 responses for specific endpoints
- Table growth (e.g., new rows per day)

### I2. Operational runbook

- Common issues and how to troubleshoot (1–2 bullets each).
- When to roll back vs. hot‑fix.
- Any planned clean‑up jobs or periodic scripts related to this phase.

### I3. Future TODOs / follow‑ons

Short list of work intentionally deferred to later phases:

- 
- 

