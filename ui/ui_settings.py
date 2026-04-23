from dataclasses import asdict, dataclass
from typing import Any

from apps.app_settings.models import AppSettings
from ui.consts import Theme


@dataclass
class UISettings:
    theme: Theme = 'light'


class AppSettingsUI:
    """
    Визуальные настройки приложения
    """

    def __init__(self, app_settings: AppSettings):
        self._app_settings = app_settings
        self._ui_settings = UISettings(**self._app_settings.ui_settings)

    @property
    def theme(self) -> Theme:
        return self._ui_settings.theme

    def switch_theme(self):
        theme_switch_map: dict[Theme, Theme] = {
            'light': 'dark',
            'dark': 'light',
        }
        current_theme = self.theme

        new_theme = theme_switch_map.get(current_theme)

        if new_theme:
            self._update_value('theme', new_theme)

    def get_settings(self) -> UISettings:
        return self._ui_settings

    def update_settings(self, ui_settings_dto: UISettings):
        ui_settings = asdict(ui_settings_dto)
        self._app_settings.ui_settings = ui_settings
        self._app_settings.save(only=['ui_settings'])

    def _update_value(self, key: str, value: Any):
        settings = self.get_settings()
        try:
            setattr(settings, key, value)
        except (AttributeError, ValueError):
            pass
        else:
            self.update_settings(settings)
