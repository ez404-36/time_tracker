import datetime


def remove_spaces(value: str | None) -> str | None:
    return value and (
        value
        .replace(' ', ' ')
        .replace('‎', '')
        .strip()
    )


def to_current_tz(value: datetime.datetime) -> datetime.datetime:
    from .settings import AppSettings

    tz = AppSettings.get_solo().get_tz()
    return value.astimezone(tz)


def get_client_timezone_hour_offset() -> int:
    now = datetime.datetime.now()
    now_utc = datetime.datetime.now(datetime.timezone.utc)

    now_hour = now.hour or 24
    now_utc_hour = now_utc.hour or 24

    offset = now_hour - now_utc_hour
    return offset
