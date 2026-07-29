from datetime import datetime, timedelta, timezone

from services.reputation_service.period import week_key


def _sunday_anchor() -> datetime:
    """An arbitrary UTC instant, walked back to the most recent Sunday midnight, so
    tests don't depend on hardcoded calendar dates matching a particular weekday."""
    now = datetime(2026, 1, 5, 12, 0, tzinfo=timezone.utc)
    days_since_sunday = (now.weekday() - 6) % 7
    sunday = now - timedelta(days=days_since_sunday)
    return sunday.replace(hour=0, minute=0, second=0, microsecond=0)


def test_same_week_maps_to_the_same_key():
    sunday = _sunday_anchor()
    mid_week = sunday + timedelta(days=3, hours=5)
    end_of_week = sunday + timedelta(days=6, hours=23, minutes=59)

    assert week_key(sunday) == week_key(mid_week) == week_key(end_of_week) == sunday.date().isoformat()


def test_next_sunday_starts_a_new_week():
    sunday = _sunday_anchor()
    end_of_week = sunday + timedelta(days=6, hours=23, minutes=59)
    next_sunday = sunday + timedelta(days=7)

    assert week_key(end_of_week) != week_key(next_sunday)
    assert week_key(next_sunday) == next_sunday.date().isoformat()


def test_week_start_day_is_configurable():
    sunday = _sunday_anchor()
    monday = sunday + timedelta(days=1)

    assert week_key(monday, week_start_day=0) == monday.date().isoformat()
    assert week_key(sunday, week_start_day=0) != week_key(monday, week_start_day=0)


def test_week_key_is_timezone_normalizing():
    from datetime import timezone as tz

    utc_time = datetime(2026, 7, 20, 1, 0, tzinfo=tz.utc)
    same_instant_other_offset = utc_time.astimezone(tz(timedelta(hours=-5)))

    assert week_key(utc_time) == week_key(same_instant_other_offset)
