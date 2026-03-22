from typing import Callable, Coroutine

import flet as ft

from core.di import container
from ui.components.timer import TimerComponent, CountdownComponent
from ui.consts import FontWeight, FontSize


class TotalTimeComponent(ft.Row):
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

        self._timer: TimerComponent | None = None
        self._label: ft.Text | None = None

    def build(self):
        self._label = ft.Text(size=FontSize.H5, weight=FontWeight.W_500)

        if self._app_settings.enable_pomodoro:
            work_minutes = self._app_settings.pomodoro_work_time
            self._timer = CountdownComponent(
                seconds=work_minutes,
                on_end=self._on_end,

            )
            self._label.value = self._label_text
        else:
            self._timer = TimerComponent(seconds=0)
            self._label.value = 'Общее время: '

        self.controls = [
            self._label,
            self._timer,
        ]
