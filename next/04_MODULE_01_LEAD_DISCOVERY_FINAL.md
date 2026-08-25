# Module 1 — Lead Discovery
## Final Functional Specification

## 1. Purpose

Find potential business leads from configured data sources and save clean lead records.

## 2. Supported sources

The source layer must be modular.

Initial source:
- Google Maps/Places through an approved API integration.

Additional sources:
- approved public directories
- approved websites/data providers

Do not hard-code the application around one source.

## 3. Search configuration

The user can set:

### Required
- Business type/category
- Location

### Optional
- City
- Country
- Latitude
- Longitude
- Search radius
- Keywords
- Source
- Maximum results

## 4. Manual mode

User selects search settings.

User clicks `Search`.

System:
1. Validates the settings.
2. Creates a search run.
3. Calls the selected source.
4. Receives results.
5. Normalizes the results.
6. Checks duplicates.
7. Saves new leads.
8. Updates existing leads when appropriate.
9. Shows results.
10. Shows run summary.

The UI must show:
- queued
- running
- completed
- failed

## 5. Semi-Automatic mode

User creates a saved search.

Example:
Business type = Hotels
Location = Lahore
Radius = 20 km

User clicks `Run`.

The system executes the saved search.

After completion:
- new leads are shown
- duplicate count is shown
- failed records are shown
- user can review results
- user can approve the batch for the next module

## 6. Fully Automatic mode

User enables the saved search.

User chooses schedule.

Supported initial schedule options:
- every hour
- every 2 hours
- every 6 hours
- daily

The system runs through n8n.

Before saving a new lead:
- check source ID
- check normalized website
- check normalized phone
- check business name + address

The system must avoid creating duplicate leads.

## 7. Lead fields

A lead can contain:

- Lead ID
- Business name
- Category
- Address
- City
- Country
- Latitude
- Longitude
- Phone
- Email
- Website
- Social links
- Source
- Source ID
- Source URL/reference
- Rating, where available and allowed
- Review count, where available and allowed
- First seen
- Last seen
- Status
- Created at
- Updated at

## 8. Raw data

Keep raw source data separately from normalized data.

Never overwrite original source data with AI-generated information.

## 9. Lead list

The lead list must support:
- search
- filter
- sort
- pagination
- status
- source
- date
- category
- location

## 10. Lead detail

Clicking a lead opens a detailed view with:
- business information
- contact information
- website
- social links
- source
- collection history
- qualification status
- analysis status
- outreach status
- timeline

## 11. Error handling

If one source request fails:
- do not lose previous results
- record the error
- show the failed run
- allow retry

If one lead record is incomplete:
- save available valid data
- mark missing fields
- do not reject the entire batch

## 12. Limits

Every automatic search must have:
- maximum results
- schedule
- enabled/disabled status
- run history

## 13. Acceptance criteria

Module 1 is complete only when:

- Manual search works.
- Semi-automatic saved search works.
- Automatic scheduled search works.
- Duplicate prevention works.
- Lead details are saved correctly.
- Failed runs are visible.
- Retry works.
- Run history is available.
- Real backend data appears in the UI.
- No fake progress or fake results exist.
