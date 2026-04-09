import datetime

from core.di import container


def to_current_tz(value: datetime.datetime) -> datetime.datetime:
    app_settings = container.app_settings

    tz = app_settings.get_tz()
    return value.astimezone(tz)


def get_client_timezone_hour_offset() -> int:
    now = datetime.datetime.now()
    now_utc = datetime.datetime.now(datetime.timezone.utc)

    now_hour = now.hour or 24
    now_utc_hour = now_utc.hour or 24

    offset = now_hour - now_utc_hour
    return offset
