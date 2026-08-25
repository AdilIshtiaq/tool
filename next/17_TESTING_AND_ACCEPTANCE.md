# Testing and Acceptance

## Unit tests

Test:
- validation
- rules
- scoring
- duplicate detection
- database functions
- permissions

## Integration tests

Test:
- Google/source → lead
- lead → qualification
- qualification → analysis
- analysis → service recommendation
- outreach → SMTP
- reply → lead
- call → timeline
- CRM stage → history

## Automation tests

Test:
- manual run
- semi-auto run
- scheduled run
- failure
- retry
- duplicate run
- partial data

## AI tests

Test:
- structured output
- no invented facts
- valid service selection
- confidence
- low-confidence review

## Acceptance rule

A module is not complete because the UI looks finished.

It is complete only when:
- backend works
- database works
- API works
- n8n workflow works
- UI uses real data
- errors are handled
- tests pass
- manual/semi-auto/auto behavior works for that phase
