from datetime import datetime, timedelta, timezone


def get_current_time() -> datetime:
    """Get the current time."""
    return datetime.now(timezone.utc)


def get_time_in_future(hours: int) -> datetime:
    """Get the time in the future."""
    current_time = get_current_time()
    future_time = current_time + timedelta(hours=hours)
    return future_time


def get_iso8601_time(hours: int) -> str:
    """Get the time in the future in ISO 8601 format."""
    future_time = get_time_in_future(hours)
    iso_format = future_time.isoformat()
    return iso_format
