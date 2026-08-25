# Phase-by-Phase Implementation Plan

## Phase 0 — Foundation

Build:
- project structure
- environment configuration
- PostgreSQL
- FastAPI
- Next.js
- local n8n
- logging
- basic health checks

Definition of Done:
All services start locally and communicate successfully.

---

## Phase 1 — Lead Discovery

### Stage 1A: Manual

User chooses:
- location
- latitude/longitude if required
- radius
- business type
- keywords
- source
- result limit

User clicks Search.

System:
→ fetches leads
→ normalizes data
→ checks duplicates
→ saves leads
→ displays results

### Stage 1B: Semi-Automatic

User saves a search configuration.

User starts the job.

System fetches leads automatically.

User reviews results.

### Stage 1C: Fully Automatic

User enables automation.

User chooses a schedule, for example:
- every 1 hour
- every 2 hours
- every 6 hours
- daily

System runs automatically.

Important:
The default schedule must not be hard-coded. It must be configurable.

Definition of Done:
All three modes work and have visible run status.

---

## Phase 2 — Qualification

Manual → Semi-Automatic → Fully Automatic.

Rules decide whether a lead is worth analyzing.

---

## Phase 3 — AI Business Analysis

AI analyzes qualified leads using approved data and user rules.

---

## Phase 4 — Service Recommendation

AI chooses the best service from the service catalog.

---

## Phase 5 — Email Outreach

User templates and AI-generated templates are supported.

Manual approval is available.

---

## Phase 6 — Reply Tracking

Replies are matched to leads and classified.

---

## Phase 7 — Manual Calling Workspace

The system gives the user:
- phone number
- reason for calling
- lead summary
- service recommendation
- call script
- notes
- outcome
- follow-up

The user makes the call manually.

---

## Phase 8 — CRM

Pipeline, timeline, tasks, and stage history.

---

## Phase 9 — Analytics

Show:
- lead volume
- qualification rate
- service recommendations
- outreach results
- replies
- calls
- meetings
- wins/losses

---

## Phase 10 — Testing and Hardening

Full integration tests, failure handling, security review, backups, and performance review.

---

## Phase 11 — Deployment Readiness

Only after local stability is confirmed.
