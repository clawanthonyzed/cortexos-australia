# SPEC-COS-16 — Direct Agent Write Access to Memory/KG

Status: PROPOSED — awaiting Anthony approval before build
Owner: Orbit | API: Turing | Security review: Hex
Repo: clawanthonyzed/cortexos-australia (NOT business-idea-dash — CLAUDE.md has stale repo name, flagged for fix)

## Problem

329 agents produce work. Memory/KG only grow via celery-beat cron scraping
EMPIRE-WORK-LOG.md (15m) and agent .md files (4h) — passive, batched, lossy.
Agents cannot write to memory/KG as part of normal operation. Only path today:
POST /api/v1/memory and POST /api/v1/kg/episodes exist but require a human
dashboard User JWT + RBAC role (admin/operator/viewer) — no agent identity,
no service-to-service auth. That's the bottleneck.

## What already exists (verified against live code, not assumed)

- `memory_items` table: already has `agent_id` FK, `venture_id` FK (SPEC-COS-04
  multi-tenant, already shipped), `external_id`, `source_task_id`, `tags`,
  `importance_score`. No schema blocker.
- `agents` table: 337 rows already synced (registry has 329 — minor drift,
  not blocking), each with `name`, `venture_id`, `tags` (JSON list incl.
  "specialist"). This IS the identity source — reuse it, don't invent a
  parallel agent-identity system.
- `ventures` table: `slug`, `manager_name` — maps 1:1 to registry venture field.
- `POST /api/v1/memory`, `POST /api/v1/kg/episodes` — write logic already
  correct (MemoryManager.remember / add_to_knowledge_graph). Only the AUTH
  layer needs to change, not the write logic.
- `AuditLog` model already exists (action/resource/before/after/success) —
  reusable for provenance instead of a new event-log table.
- Redis already running as a compose service — free rate-limit substrate.
- Backend already reachable on the Docker internal network (`cortexos_net`)
  from any container/host process on 46.250.244.248 — agents run on the SAME
  box, so no public exposure needed for this.

## Design

### 1. Auth — shared internal service token, not 329 individual API keys

Issuing/rotating per-agent keys for 329 agents is needless ops overhead for
same-box callers. Instead:

- One `AGENT_WRITE_TOKEN` secret in `/opt/cortexos/.env`, injected to the
  local hook environment only (never leaves the server, never routed through
  Traefik/public internet).
- New FastAPI dependency `get_agent_identity`: requires header
  `Authorization: Bearer <AGENT_WRITE_TOKEN>` + `X-Agent-Name: <name>`.
  Token proves "this is empire infrastructure," name is resolved server-side
  against the `agents` table (name -> agent_id, venture_id, is_specialist).
  Client-supplied agent_id/venture_id in the request body is IGNORED — server
  stamps identity from the DB lookup, not from trusted client input. Prevents
  spoofing another agent's writes.
- Endpoint bound to internal network only (backend service, not exposed via
  new Traefik route). Existing `dash.anthonyzed.work` route is for the human
  dashboard (User JWT); agent writes go over `http://backend:8200` internally
  or `http://localhost:8200` from the host — never internet-facing with just
  a shared secret. This is the load-bearing security property Hex should
  verify before ship.

### 2. Write path — extend the hook, not build new infra

`agent-session-writer.py` already fires PostToolUse on every agent (where
wired) and already computes agent name + venture slug. Extend its `flush()`
to POST each buffered insight to `/api/v1/memory` (using the shared token)
in addition to (not instead of) the existing second-brain raw-file capture —
keep the file fallback for when the API is down. This turns an existing,
already-partially-deployed mechanism into the live write path instead of
inventing a second one. Remaining gap: confirm which of the 329 agent .md
files actually have this hook wired — likely not all. Nexus to audit and
backfill hook config as part of build phase (not a blocker for the API/auth
work).

### 3. Conflict handling — append-only, confirmed correct

No updates. Every agent write = new `memory_items` row. Matches existing
pattern (`ingest_work_log`, `sync_agent_files` are the only two places that
dedupe via `external_id`, and only because they're re-scraping the same
source file repeatedly — direct agent writes have no such re-scrape problem,
so no dedup key needed). Audit trail > tidy table, per directive.

### 4. Permission boundary — reuse `is_specialist` + `venture_id`, already in schema

- Venture-scoped agent (is_specialist=false): write forced to
  `agent.venture_id`. Any venture_slug in the request body is ignored for
  these agents — server always stamps their own.
- Specialist (is_specialist=true — Bolt/Hex/Nexus/Einstein/Zoe per registry):
  may pass an explicit `venture_slug` to target any venture, or omit it for
  `venture_id=NULL` (empire-wide). Matches the existing "specialist = no
  single venture" convention already in the registry schema.
- Same rule applied to `POST /kg/episodes` `group_id` (currently defaults to
  `"default"` for everyone — change default to caller's venture slug,
  specialists can override).

### 5. Rate/volume guard — Redis counters, no review queue

- Sliding-window cap: 60 writes/agent/hour (Redis INCR + EXPIRE). 429 past
  that — cheap, no queue, no human in the loop.
- Content validation at the API layer (already a FastAPI Pydantic boundary,
  natural place for this): reject content <10 chars or >8000 chars (guards
  empty/garbage and "dumped whole file" cases).
- Loop guard: hash(agent_id + content) in Redis with 5-min TTL — identical
  content from the same agent within 5 min is silently deduped (not
  rejected — just skipped, no error surfaced to the agent, since a malformed
  loop shouldn't need the agent to handle a new error case).

### 6. Migration

- Alembic migration: add `source` column to `memory_items`
  (`"agent_direct" | "dashboard" | "auto_ingest"`, default `"dashboard"` for
  backward compat) — the only real schema gap, everything else already
  exists. Backfill existing rows: `worklog:%`/`agentfile:%` external_id rows
  -> `"auto_ingest"`, rest -> `"dashboard"`.
- No new Docker Compose service — reuses the running `backend` container.
- No new Traefik route — internal-only by design (see Auth section).
- `AGENT_WRITE_TOKEN` added to `.env` + `.env.example` (placeholder), synced
  to every agent's hook environment (Nexus, as part of hook backfill above).

## Open questions for Hex (security) before build

1. Confirm internal-network-only exposure is actually enforced (Traefik
   dynamic.yml doesn't accidentally proxy `/api/v1/memory` or `/api/v1/kg`
   to the public route today — need to check `traefik/dynamic.yml`, not
   assumed safe).
2. Token rotation policy for `AGENT_WRITE_TOKEN` — single shared secret means
   one leak = every agent's write path compromised. Acceptable given
   same-box/internal-only exposure, but Hex should sign off explicitly.
3. Should specialist cross-venture writes also hit AuditLog (not just
   memory_items), given they're the highest-blast-radius write path?
   Recommend yes.

## Verification plan (after approval + build)

- Query DB directly (`SELECT count(*), source FROM memory_items GROUP BY
  source`) to confirm agent-direct writes are landing — not just assumed
  from a 200 response.
- Confirm rate limit actually 429s past 60/hr with a scripted burst test.
- Confirm venture-scoped agent cannot write cross-venture (expect 403/silent
  ignore of venture_slug override) — test with one venture agent + one
  specialist.
- Update WORKFORCE.md + MASTER-DASH.md with the new capability once verified
  live, not before.
