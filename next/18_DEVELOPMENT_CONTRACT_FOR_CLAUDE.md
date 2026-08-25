# Development Contract for Claude / AI Coding Assistant

## Role

You are implementing the Next Craft Solutions AI Sales Operating System according to this final blueprint.

## Non-negotiable rules

1. Read the relevant documentation before coding.
2. Work only on the current phase.
3. Do not invent missing requirements.
4. Do not redesign the architecture without approval.
5. Do not add libraries unless necessary.
6. Keep backend logic separate from UI.
7. Use PostgreSQL as the source of truth.
8. Use FastAPI for application business logic.
9. Use n8n for workflow orchestration.
10. Validate all AI output.
11. Keep secrets out of source code.
12. Add tests with important functionality.
13. Do not create fake UI functionality.
14. Do not mark unfinished features as complete.
15. Preserve existing working functionality.

## Phase rule

Implement:

Manual
→ test
→ Semi-Automatic
→ test
→ Fully Automatic
→ test

Do not jump directly to full automation.

## Change control

If a change affects:
- database architecture
- API architecture
- n8n architecture
- AI architecture
- core workflow

stop and ask for approval.

A normal bug fix does not require approval.

## Required completion report

At the end of every task, report:

### 1. Completed
What was implemented.

### 2. Files changed
List files.

### 3. Database
Any schema/migration changes.

### 4. APIs
New or changed endpoints.

### 5. n8n
New or changed workflows.

### 6. AI
Prompts/schema changes.

### 7. Tests
Tests added and result.

### 8. Known limitations
Anything not finished.

### 9. Next phase
What should be implemented next.

## Definition of Done

Never say "complete" unless the documented acceptance criteria for the current task are satisfied.
