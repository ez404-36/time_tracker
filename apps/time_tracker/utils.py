import re

from core.utils import remove_spaces

telegram_msg_count_regex = re.compile(r'.{1,3}\(\d+\)')


class AppNameAndWindowTitleTransformerBase:
    """
    Базовый класс трансмформации названия приложения и заголовка окна
    """

    def __init__(self, executable_name: str, window_title: str | None):
        self.executable_name = remove_spaces(executable_name)
        self.window_title = remove_spaces(window_title)

    def transform(self) -> tuple[str, str]:
        return self.transform_app_name(), self.transform_window_title()

    def transform_app_name(self) -> str:
        return self.executable_name

    def transform_window_title(self) -> str | None:
        return self.window_title


class TelegramTransform(AppNameAndWindowTitleTransformerBase):
    def transform_app_name(self) -> str:
        return 'Telegram'

    def transform_window_title(self) -> str:
        user_or_channel_name = self.window_title.split('@')[0].strip()
        return telegram_msg_count_regex.sub('', user_or_channel_name)


class YandexBrowserTransform(AppNameAndWindowTitleTransformerBase):
    def transform_app_name(self) -> str:
        return 'Яндекс Браузер'

    def transform_window_title(self) -> str:
        return self.window_title.split(' — Яндекс Браузер')[0].replace(' вкладка закреплена', '')


class WindowsSteamGameTransform(AppNameAndWindowTitleTransformerBase):
    def transform_app_name(self) -> str:
        return self.window_title.split('PID')[0].strip()

    def transform_window_title(self) -> str | None:
        return None


def get_app_name_and_transform_window_title(executable_name: str, window_title: str) -> tuple[str, str]:
    """
    :param executable_name: название исполняемого файла
    :param window_title: заголовок окна
    :return: Название приложения, Трансформированный заголовок окна
    """

    transform_cls = None

    match executable_name:
        case 'telegram-desktop' | 'Telegram.exe':
            transform_cls = TelegramTransform
        case 'yandex_browser' | 'browser.exe':
            transform_cls = YandexBrowserTransform
        case str() if 'steamapps' in window_title:
            transform_cls = WindowsSteamGameTransform
        case _:
            transform_cls = AppNameAndWindowTitleTransformerBase

    return transform_cls(executable_name, window_title).transform()
