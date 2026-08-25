# Final Database Specification

## Core tables

### leads
Main normalized business record.

### lead_sources
Source and raw collection information.

### contacts
People connected to leads.

### qualification_rules
Qualification rule definitions.

### lead_qualification
Qualification results.

### analysis_rules
AI analysis rule definitions.

### lead_analysis
AI analysis results.

### services
Service catalog.

### service_recommendations
AI service recommendations.

### templates
Email templates.

### campaigns
Outreach campaign settings.

### messages
Sent and received messages.

### calls
Manual call records.

### tasks
Follow-up and sales tasks.

### crm_stage_history
Pipeline changes.

### audit_logs
Important actions.

## Database rules

- Use primary keys.
- Use foreign keys.
- Add indexes for frequently searched fields.
- Keep created_at and updated_at.
- Keep raw data separate.
- Do not store AI guesses as original business facts.
- Use soft deletion where appropriate for important records.
