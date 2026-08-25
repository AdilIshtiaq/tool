# PostgreSQL Backup and Restore

Per `16_SECURITY_COMPLIANCE_AND_ERROR_HANDLING.md`: "Before deployment, define a
PostgreSQL backup and restore process." This covers the local/pre-deployment
process; production scheduling is out of scope until Phase 11.

## Database

- Name: `nexcraft_salesos`
- Host: `localhost:5432`
- User: `postgres` (local trust auth)

## Backup

Run from `D:\Automation\backend`:

```bash
pg_dump -U postgres -h localhost -Fc nexcraft_salesos > backups/nexcraft_salesos_$(date +%Y%m%d_%H%M%S).dump
```

- `-Fc` uses PostgreSQL's custom compressed format, required for `pg_restore` (not
  plain SQL) and supports partial/selective restore if ever needed.
- Create the `backups/` directory first if it doesn't exist; it's git-ignored —
  dumps contain real business data and must never be committed.

## Restore

**To a new, empty database** (e.g. disaster recovery):

```bash
createdb -U postgres -h localhost nexcraft_salesos_restored
pg_restore -U postgres -h localhost -d nexcraft_salesos_restored backups/<file>.dump
```

Verify the restored data, then point `DATABASE_URL` in `.env` at the restored
database (or rename databases) once confirmed good.

**To overwrite the existing database** (only when you're certain — this is
destructive):

```bash
pg_restore -U postgres -h localhost -d nexcraft_salesos --clean --if-exists backups/<file>.dump
```

`--clean --if-exists` drops existing objects before recreating them, so this
replaces current data with the backup's contents.

## What is NOT backed up by this process

- n8n's own database (`n8n_internal`) — back it up the same way if its workflows
  ever contain irreplaceable configuration:
  `pg_dump -U postgres -h localhost -Fc n8n_internal > backups/n8n_internal_$(date +%Y%m%d_%H%M%S).dump`
- Secrets in `.env` (never stored in the database — keep your own secure copy)
- Alembic migration files (already version-controlled in `alembic/versions/`)

## Recommended cadence (once deployed)

Not yet scheduled — this is a Phase 11 (Deployment Readiness) task. For now,
run a manual backup before any risky operation (schema migration, bulk data
change, upgrading dependencies).
