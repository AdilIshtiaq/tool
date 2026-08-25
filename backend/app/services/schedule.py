from datetime import datetime, timedelta

# Supported schedule options per the blueprint (04_MODULE_01_LEAD_DISCOVERY_FINAL.md, section 6).
# Interval is configured per saved search — never a single hard-coded global interval.
SCHEDULE_INTERVALS: dict[str, timedelta] = {
    "hourly": timedelta(hours=1),
    "every_2_hours": timedelta(hours=2),
    "every_6_hours": timedelta(hours=6),
    "daily": timedelta(days=1),
}


def is_valid_schedule(schedule: str) -> bool:
    return schedule in SCHEDULE_INTERVALS


def is_due(schedule: str, last_completed_run_at: datetime | None, now: datetime) -> bool:
    if last_completed_run_at is None:
        return True
    interval = SCHEDULE_INTERVALS[schedule]
    return now - last_completed_run_at >= interval
