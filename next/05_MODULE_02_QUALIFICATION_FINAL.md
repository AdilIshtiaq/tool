# Module 2 — Lead Qualification

## Purpose

Decide whether a lead should move to AI analysis.

## Rule types

Examples:
- business category
- location
- website available
- email available
- phone available
- business data completeness
- exclusion list
- target customer profile

## Rule builder

Admin can:
- create
- edit
- enable
- disable
- reorder

Each rule contains:
- name
- description
- field
- operator
- expected value
- enabled
- priority

## Result

Return:
- Qualified
- Not Qualified
- Needs Review

Also save:
- score
- passed rules
- failed rules
- run timestamp

## AI

AI may help with ambiguous qualification.

Deterministic checks should remain deterministic.

## Manual override

User can override a qualification result.

Save:
- old result
- new result
- user
- reason
- timestamp
