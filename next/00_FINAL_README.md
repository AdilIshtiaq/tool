# Next Craft Solutions
## AI Sales Operating System
### Final Implementation Blueprint

**Document status:** FINAL / BASELINE

This documentation is the implementation source of truth for the first complete version of the system.

## Company

NexCraft Solutions

## Development principle

The project must be developed phase by phase.

The architecture, database, APIs, workflows, AI rules, and UI behavior defined in this pack are the baseline.

Do not change the architecture just because a different implementation looks easier.

If a requirement is not documented, do not invent it. Mark it as `OPEN QUESTION` and ask for clarification before implementing it.

## Important

This is a final blueprint, but development is still phased.

That means:
- The full system is defined now.
- Only the current phase is implemented at a time.
- Later phases must not be built early unless explicitly requested.
- Small bug fixes are allowed without changing the architecture.
- Any architectural change requires a documented change request.

## Current environment

- Local development first
- No production hosting required now
- n8n runs locally
- PostgreSQL runs locally
- FastAPI runs locally
- Next.js runs locally
- OpenAI API is external
- Approved external data APIs are external
- SMTP provider is external

## Final development order

Phase 0: Foundation
Phase 1: Lead Discovery
Phase 2: Lead Qualification
Phase 3: AI Business Analysis
Phase 4: Service Recommendation
Phase 5: Email Outreach
Phase 6: Reply Tracking and Follow-up
Phase 7: Manual Calling Workspace
Phase 8: CRM and Pipeline
Phase 9: Dashboard and Analytics
Phase 10: Testing and Hardening
Phase 11: Deployment Readiness

## Automation rule

Where a module supports automation, implement it in this order:

1. Manual
2. Semi-Automatic
3. Fully Automatic

Do not skip the manual stage.

## Product principle

Backend correctness comes before UI polish.

Every screen must represent real backend functionality. No fake buttons, fake progress, or placeholder automation should be presented as working functionality.
