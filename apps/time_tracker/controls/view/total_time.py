from typing import Callable, Coroutine

import flet as ft

from core.di import container
from ui.components.timer import TimerComponent, CountdownComponent
from ui.consts import FontWeight, FontSize


class PomodoroTimerComponent(ft.Row):
    def __init__(
            self,
            label_text: str,
            on_end: Coroutine[None, None, None] | Callable[[], None] = None,
            **kwargs,
    ):
        super().__init__(**kwargs)
        self._app_settings = container.app_settings
        self._on_end = on_end
        self._label_text = label_text

    def build(self):
        _label = ft.Text(
            value=self._label_text,
            size=FontSize.H5,
            weight=FontWeight.W_500,
        )

        work_minutes = self._app_settings.pomodoro_work_time
        _timer = CountdownComponent(
            seconds=work_minutes * 60,
            on_end=self._on_end,

        )

        self.controls = [
            _label,
            _timer,
        ]


class TotalTimeComponent(ft.Row):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def build(self):
        _timer = TimerComponent(seconds=0)
        _label = ft.Text(
            value='Общее время: ',
            size=FontSize.H5,
            weight=FontWeight.W_500,
        )

        self.controls = [
            _label,
            _timer,
        ]

