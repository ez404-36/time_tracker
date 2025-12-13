import datetime
from typing import Self

import flet as ft

from apps.time_tracker.controls.view.activity_track_action import ActivityTrackActionControl
from apps.time_tracker.helpers import ActivityTabHelpers
from apps.time_tracker.models import Action, ActivityTrack
from core.state import ActivityTabState


class ActivityTabActivityDropdown(ft.Dropdown):
    """Селектор выбора активности"""

    def __init__(self, state: ActivityTabState, edit_activity_button: ft.IconButton, **kwargs):
        kwargs.setdefault('editable', True)
        kwargs.setdefault('width', 300)
        super().__init__(**kwargs)
        self._state = state
        self._edit_activity_button = edit_activity_button

    def build(self) -> Self:
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
        self.on_change = self._on_change

    def _on_change(self, e):
        val = int(self.value)
        activity = self._state['db']['activities'].get(val)

        if activity == self._state['selected']['activity']:
            return

        self._state['selected']['activity'] = activity
        self._edit_activity_button.visible = True

        actions_view = self.parent.parent.controls[1]

        existing_activity_track = ActivityTrack.filter(
            activity=activity,
            date=datetime.date.today(),
        ).first()

        self._state['selected']['activity_track'] = existing_activity_track

        actions_view.controls.clear()

        for action in activity.actions.order_by(Action.is_target.desc(), Action.is_useful.desc()):
            action_control = ActivityTrackActionControl(self._state, action)
            actions_view.controls.append(action_control)

        actions_view.update()
        self._edit_activity_button.update()
