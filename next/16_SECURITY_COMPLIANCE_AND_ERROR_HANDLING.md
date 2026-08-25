# Security, Data, and Error Handling

## Secrets

Never put:
- OpenAI API key
- Google API key
- SMTP password
- database password

inside frontend code.

## External sources

Only use sources and collection methods that are permitted.

## Email outreach

Include appropriate suppression/opt-out handling and respect applicable marketing and privacy requirements.

## Errors

Every external integration must handle:
- timeout
- invalid response
- rate limit
- authentication failure
- server error
- partial result

## Retry

Only retry errors that are safe to retry.

Do not blindly retry sending an email because it can create duplicates.

## Audit

Log:
- user action
- automation action
- AI decision
- manual override
- email send
- CRM stage change
- important data change

## Backup

Before deployment, define a PostgreSQL backup and restore process.
