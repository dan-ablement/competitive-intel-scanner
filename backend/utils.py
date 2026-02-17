from datetime import datetime, timezone


def utc_isoformat(dt: datetime | None) -> str | None:
    """Format a datetime as ISO 8601 with explicit UTC offset.

    Handles naive datetimes (assumes UTC) and aware datetimes.
    Returns None if dt is None.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()

