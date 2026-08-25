# Architecture and Technology Stack

## 1. Architecture

Use a simple modular monolith for the application.

### Frontend
Next.js + TypeScript

### Backend
Python + FastAPI

### Database
PostgreSQL

### Automation
n8n

### AI
OpenAI API

### Email
SMTP

## 2. Responsibility boundaries

### Next.js
Responsible for:
- pages
- forms
- tables
- filters
- dashboards
- lead detail
- analysis review
- outreach editor
- calling workspace
- CRM views

### FastAPI
Responsible for:
- API
- validation
- business rules
- database access
- permissions
- workflow triggers
- AI output validation
- audit logs

### PostgreSQL
The main source of truth.

### n8n
Responsible for:
- workflow orchestration
- external API calls
- scheduled jobs
- automation
- workflow retries
- sending workflow results back to the backend

### OpenAI
Responsible for:
- analysis
- recommendations
- content generation
- classification

## 3. Do not use initially

Do not add:
- microservices
- Kubernetes
- Kafka
- Celery
- Redis
- complex agent frameworks

unless a real technical requirement appears.

## 4. Local architecture

Browser
→ Next.js
→ FastAPI
→ PostgreSQL

FastAPI
↔ n8n
↔ external APIs
↔ OpenAI
↔ SMTP

## 5. Security

Secrets must stay in environment variables or secure n8n credentials.

Never expose API keys in the frontend.

## 6. Correlation IDs

Every automation run should have a workflow/run ID so a user can trace:
lead → workflow → result → error.
