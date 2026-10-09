"""Time-related tools."""

from datetime import datetime
from zoneinfo import ZoneInfo


def current_time(time_zone: str = "UTC") -> str:
    """Get current time in the requested IANA timezone."""
    try:
        now = datetime.now(ZoneInfo(time_zone))
    except Exception:
        now = datetime.now(ZoneInfo("UTC"))
        time_zone = "UTC"
    return now.isoformat(timespec="seconds") + f" ({time_zone})"
