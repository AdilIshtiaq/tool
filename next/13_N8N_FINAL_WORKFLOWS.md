# Final n8n Workflow Specification

## Rule

Do not build one giant workflow.

Use separate workflows with clear inputs and outputs.

## Workflow A — Manual Lead Search

Webhook
→ validate request
→ call source API
→ normalize results
→ send to backend
→ duplicate check
→ save
→ return run result

## Workflow B — Semi-Automatic Lead Search

Manual trigger from dashboard
→ load saved search
→ run source
→ normalize
→ deduplicate
→ save
→ return results
→ mark run complete

## Workflow C — Automatic Lead Search

Schedule Trigger
→ find enabled search configurations
→ check schedule
→ fetch source data
→ normalize
→ deduplicate
→ save new leads
→ update run
→ log errors

## Workflow D — Qualification

Trigger
→ load lead
→ load rules
→ execute rules
→ calculate score
→ save result

## Workflow E — AI Analysis

Trigger
→ load lead
→ load rules
→ load services
→ gather approved information
→ call OpenAI
→ validate structured output
→ save analysis
→ save recommendation

## Workflow F — Outreach

Trigger
→ load approved lead
→ load template
→ personalize
→ validate
→ send SMTP
→ save provider result

## Workflow G — Reply Processing

Incoming email
→ match lead
→ save reply
→ classify
→ suggest action
→ update CRM

## Workflow H — Follow-up

Schedule Trigger
→ find due follow-ups
→ check stop conditions
→ prepare message
→ approval/automatic send
→ save result

## Workflow requirements

Every workflow must have:
- clear trigger
- clear input
- clear output
- success path
- error path
- logging
- safe retry behavior
- workflow/run ID

## Schedule

The schedule must be configurable per saved search.

Do not hard-code one global interval.
