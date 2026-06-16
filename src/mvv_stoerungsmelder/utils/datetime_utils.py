from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from src.mvv_stoerungsmelder.constants import DEFAULT_TIMEZONE


def datetime_from_milliseconds(value: int) -> datetime | None:
    if value is None:
        return None
    dt = datetime.fromtimestamp(
        value / 1000,
        tz=ZoneInfo(DEFAULT_TIMEZONE)
    )
    dt = dt.astimezone(timezone.utc)
    return dt

def datetime_now() -> datetime:
    return datetime.now(timezone.utc)