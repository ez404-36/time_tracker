class AppNameTransformBase:
    """
    Базовый класс трансмформации названия приложения и заголовка окна
    """

    def __init__(self, app_name: str, window_title: str):
        self.app_name = app_name.replace(' ', ' ')
        self.window_title = window_title.replace(' ', ' ')

    def transform(self) -> tuple[str, str]:
        return self.transform_app_name(), self.transform_window_title()

    def transform_app_name(self) -> str:
        return self.app_name

    def transform_window_title(self) -> str | None:
        return self.window_title


class TelegramTransform(AppNameTransformBase):
    def transform_app_name(self) -> str:
        return 'Telegram'

    def transform_window_title(self) -> str:
        return self.window_title.split('@')[0].strip()


class YandexBrowserTransform(AppNameTransformBase):
    def transform_app_name(self) -> str:
        return 'Яндекс Браузер'

    def transform_window_title(self) -> str:
        return self.window_title.split(' — Яндекс Браузер')[0].replace(' вкладка закреплена', '')


class DBeaverTransform(AppNameTransformBase):
    def transform_app_name(self) -> str:
        return 'DBeaver'


class FletTransform(AppNameTransformBase):
    def transform_app_name(self) -> str:
        return self.window_title

    def transform_window_title(self) -> str | None:
        return None


def transform_app_name_and_window_title(app_name: str, title: str) -> tuple[str, str]:
    transform_cls = None

    match app_name:
        case 'telegram-desktop':
            transform_cls = TelegramTransform
        case 'yandex_browser':
            transform_cls = YandexBrowserTransform
        case 'java':
            if 'dbeaver' in title.lower():
                transform_cls = DBeaverTransform
            else:
                transform_cls = YandexBrowserTransform
        case 'flet':
            transform_cls = FletTransform
        case _:
            transform_cls = AppNameTransformBase

    return transform_cls(app_name, title).transform()
