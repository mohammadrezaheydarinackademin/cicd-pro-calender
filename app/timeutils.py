from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

STOCKHOLM = ZoneInfo("Europe/Stockholm")
UTC = timezone.utc


def utcnow() -> datetime:
    """Return the current UTC time as a naive datetime for database storage."""
    return datetime.now(UTC).replace(tzinfo=None)


def stockholm_now() -> datetime:
    return datetime.now(STOCKHOLM)


def stockholm_today() -> date:
    return stockholm_now().date()


def to_stockholm(dt_naive_utc: datetime) -> datetime:
    return dt_naive_utc.replace(tzinfo=UTC).astimezone(STOCKHOLM)


def to_utc_naive(dt_stockholm: datetime) -> datetime:
    return dt_stockholm.astimezone(UTC).replace(tzinfo=None)


def parse_local_datetime(date_string: str, time_string: str) -> datetime:
    """Interpret a date/time pair as Europe/Stockholm wall time and return UTC."""
    try:
        day = date.fromisoformat((date_string or "").strip())
    except ValueError as exc:
        raise ValueError("Use a valid date in YYYY-MM-DD format.") from exc

    try:
        clock = time.fromisoformat((time_string or "").strip())
    except ValueError as exc:
        raise ValueError("Use a valid time in HH:MM format.") from exc

    local = datetime.combine(day, clock, tzinfo=STOCKHOLM)
    return to_utc_naive(local)


def week_start_for(day: date) -> date:
    """Return the Monday of the week containing the given date."""
    return day - timedelta(days=day.weekday())
