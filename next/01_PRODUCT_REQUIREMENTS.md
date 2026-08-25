# Product Requirements

## 1. Product goal

Next Craft Solutions needs an internal AI-assisted sales system that finds potential business leads, evaluates them, identifies suitable services, prepares outreach, tracks responses, and supports manual sales calls.

## 2. Main user

The primary user is the Next Craft Solutions sales operator/admin.

The system is designed for controlled internal use first.

## 3. Main business flow

Lead Discovery
→ Data Cleaning
→ Deduplication
→ Qualification
→ AI Analysis
→ Service Recommendation
→ Outreach
→ Reply Tracking
→ Manual Calling
→ Follow-up
→ CRM
→ Analytics

## 4. User control

Every major module must support:

### Manual
The user starts the action.

### Semi-Automatic
The user configures the process. The system performs the repetitive work, but the user reviews important results/actions.

### Fully Automatic
The system runs according to saved configuration and schedule.

Automatic mode must have:
- enable/disable switch
- schedule
- limits
- failure handling
- activity log
- stop control

## 5. Global UI requirement

The user must always be able to understand:
- What is running
- What finished
- What failed
- What needs review
- What the system did
- What AI decided
- Why AI made the decision
- What the next action is

## 6. Global AI requirement

AI is an assistant, not an unrestricted system administrator.

AI may:
- analyze
- classify
- summarize
- recommend
- generate drafts
- generate scripts

AI may not independently:
- change system architecture
- delete important data
- change database structure
- invent services
- send uncontrolled bulk outreach
- change security settings
- perform irreversible actions without the defined approval rules

## 7. Business services

Services must be stored in a service catalog.

Examples:
- Website Design
- Website Redesign
- SEO
- Local SEO
- Automation
- CRM Setup

The actual catalog must be editable by the admin.

AI must select from the catalog.
