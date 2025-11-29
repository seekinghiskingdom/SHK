# SHK Backend & Environments – v1 Contract (Draft v0.1)

> NOTE: THIS IS A PLACEHOLDER.  
> For v1, SHK will rely on a **single managed backend service** (e.g., Supabase/Firebase-style) rather than a custom microservice stack.
> Any detailed API gateway, separate auth service, custom job processor, or advanced caching plans are **aspirational** and out-of-scope for v1.

## 1. v1 Architecture Overview

- Frontend:
  - Static Jekyll site hosted on GitHub Pages (or equivalent).
  - Communicates with the backend via a JS SDK or HTTPS API calls.
- Backend (managed platform):
  - Provides:
    - Email/password authentication with email verification & password reset.
    - A relational or document database for `User`, Testimony, Daily, and other module data.
    - Row-level or rules-based access control so users can only access their own records.
  - No custom backend code is required for v1 beyond what the platform offers (if possible).

## 2. Environments

- **Development environment**:
  - One “SHK-dev” backend project.
  - Used for:
    - Schema design and migrations.
    - Testing features before they go live.
    - Test data only (no real user data).
- **Production environment**:
  - One “SHK-prod” backend project.
  - Used for:
    - Real user accounts and content.
    - Strict access controls (limited admin access).
- Environments must not share user data; test accounts in dev should be clearly separated from prod accounts.

## 3. Secrets & Configuration

- API keys and service tokens must:
  - Never be committed to the public repo.
  - Be stored in backend/host configuration or environment variables.
- The frontend only uses **public** or client-safe keys (e.g., anon/public keys provided by the backend).
- Any server-side keys (e.g., admin keys) are only used in:
  - Backend dashboards, or
  - Future server functions, not in the static frontend.

## 4. Database Overview (conceptual)

- Minimal required tables/collections for v1:
  - `User` (as defined in the Accounts & User Data contract).
  - `TestimonyItem` (unified testimony/prayer/blessing module).
  - `DailyLog` or similar (per-user daily completion + streak inputs).
  - `Follow` (if follow system is included in v1; otherwise v1.1+).
- Exact DDL/schema will be defined in separate module contracts (Testimony, Daily, etc.).

## 5. Out of Scope for v1

These backend features are explicitly **out of scope** for v1:

- Custom microservices architecture (multiple independently deployed services).
- Dedicated API gateway with complex routing and rate-limiting policies.
- Separate authentication microservice (beyond the managed backend’s auth).
- Dedicated background job infrastructure (e.g., custom job queues and workers).
- Redis/memory caching layers.
- Multi-region or multi-tenant deployments.

These can be revisited if SHK grows significantly beyond the initial v1 launch.
