import flet as ft

from apps.time_tracker.helpers import ActivityTabHelpers
from core.state import ActivityTabState


class ActivityTabActivityDropdown(ft.Dropdown):
    """Селектор выбора активности"""

    def __init__(self, state: ActivityTabState, **kwargs):
        kwargs.setdefault('editable', True)
        kwargs.setdefault('width', 300)
        super().__init__(**kwargs)
        self._state = state

    def build(self):
        options = ActivityTabHelpers(self._state).get_activity_selector_options()
        disabled = not options

        if disabled:
            label = 'Добавьте активность -->'
            tooltip = 'У вас не добавлено ни одной активности.\nНажмите на кнопку "Добавить активность"'
        else:
            label = 'Чем сегодня займемся?'
            tooltip = None

        self.label = label
        self.options = options
        self.disabled = disabled
        self.tooltip = tooltip
