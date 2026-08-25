# Final API Specification

## Lead

POST /api/leads/search
GET /api/leads
GET /api/leads/{id}
PATCH /api/leads/{id}

## Search configurations

POST /api/search-configurations
GET /api/search-configurations
PATCH /api/search-configurations/{id}
POST /api/search-configurations/{id}/run
POST /api/search-configurations/{id}/enable
POST /api/search-configurations/{id}/disable

## Qualification

POST /api/leads/{id}/qualify
GET /api/leads/{id}/qualification

## Analysis

POST /api/leads/{id}/analyze
GET /api/leads/{id}/analysis

## Services

GET /api/services
POST /api/services
PATCH /api/services/{id}

## Outreach

GET /api/templates
POST /api/templates
PATCH /api/templates/{id}
POST /api/outreach/preview
POST /api/outreach/send

## Replies

GET /api/leads/{id}/messages
POST /api/messages/{id}/classify

## Calls

GET /api/leads/{id}/call-workspace
POST /api/calls
PATCH /api/calls/{id}

## CRM

GET /api/leads/{id}/timeline
PATCH /api/leads/{id}/stage

## Automation

GET /api/runs
GET /api/runs/{id}
POST /api/runs/{id}/retry

## API rules

All endpoints must:
- validate input
- return predictable errors
- log important actions
- use authentication/authorization boundaries
- prevent duplicate execution where required
