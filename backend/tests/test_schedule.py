from datetime import datetime, timedelta, timezone

from app.services.schedule import is_due, is_valid_schedule


def test_valid_schedule_names():
    assert is_valid_schedule("hourly") is True
    assert is_valid_schedule("every_2_hours") is True
    assert is_valid_schedule("every_6_hours") is True
    assert is_valid_schedule("daily") is True


def test_invalid_schedule_name():
    assert is_valid_schedule("weekly") is False


def test_never_run_is_always_due():
    assert is_due("daily", None, datetime.now(timezone.utc)) is True


def test_not_due_within_interval():
    now = datetime.now(timezone.utc)
    last_run = now - timedelta(minutes=30)
    assert is_due("hourly", last_run, now) is False


def test_due_after_interval_elapsed():
    now = datetime.now(timezone.utc)
    last_run = now - timedelta(hours=2)
    assert is_due("hourly", last_run, now) is True


def test_daily_schedule_not_due_after_a_few_hours():
    now = datetime.now(timezone.utc)
    last_run = now - timedelta(hours=5)
    assert is_due("daily", last_run, now) is False
