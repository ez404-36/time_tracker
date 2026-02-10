import re

telegram_msg_count_regex = re.compile(r'.{1,3}\(\d+\)')


class AppNameTransformBase:
    """
    Базовый класс трансмформации названия приложения и заголовка окна
    """

    def __init__(self, app_name: str, window_title: str):
        self.app_name = app_name.replace(' ', ' ').replace('‎', '')
        self.window_title = window_title.replace(' ', ' ').replace('‎', '')

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
        user_or_channel_name = self.window_title.split('@')[0].strip()
        return telegram_msg_count_regex.sub('', user_or_channel_name)


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


class WindowsExplorerTransform(AppNameTransformBase):
    def transform_app_name(self) -> str:
        return 'Проводник Windows'

    def transform_window_title(self) -> str | None:
        return self.window_title or 'Проводник'


class WindowsSteamGameTransform(AppNameTransformBase):
    def transform_app_name(self) -> str:
        return self.window_title.split('PID')[0].strip()

    def transform_window_title(self) -> str | None:
        return None


class WindowsSnippingToolsTransform(AppNameTransformBase):
    def transform_app_name(self) -> str:
        return self.window_title or 'Ножницы'

    def transform_window_title(self) -> str | None:
        return None


def transform_app_name_and_window_title(app_name: str, title: str) -> tuple[str, str]:
    transform_cls = None

    match app_name:
        case 'telegram-desktop' | 'Telegram.exe':
            transform_cls = TelegramTransform
        case 'yandex_browser' | 'browser.exe':
            transform_cls = YandexBrowserTransform
        case 'java':
            if 'dbeaver' in title.lower():
                transform_cls = DBeaverTransform
            else:
                transform_cls = YandexBrowserTransform
        case 'flet' | 'flet.exe':
            transform_cls = FletTransform
        case str() if 'steamapps' in title:
            transform_cls = WindowsSteamGameTransform
        case _:
            transform_cls = AppNameTransformBase

    return transform_cls(app_name, title).transform()
