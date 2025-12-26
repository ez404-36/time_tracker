import asyncio

import flet as ft
import pywinctl

from apps.time_tracker.controls.view.timer import CountdownComponent, TimerComponent
from apps.time_tracker.services.window_control import WindowControl


class ActiveWindowAndTimerContainer(ft.Container):
    parent: ft.Column
    content: ft.Column

    def __init__(self, pomodoro_mode: bool, seconds: int = 0, **kwargs):
        super().__init__(**kwargs)
        self.running = False
        self.pomodoro_mode = pomodoro_mode
        self.seconds = seconds

        self._active_window_title: ft.Text | None = None
        self._active_window_timer: TimerComponent | CountdownComponent | None = None
        self._opened_apps: ft.Text | None = None

    def build(self):
        self._active_window_title = ft.Text()
        self._opened_apps = ft.Text()
        if self.pomodoro_mode:
            timer = CountdownComponent
            size = 36

        else:
            timer = TimerComponent
            size = 14

        self._active_window_timer = timer(self.seconds, size=size)

        self.content = ft.Column(
            controls=[
                self._active_window_timer,
                self._active_window_title,
                ft.Divider(),
                ft.Text('Открытые приложения'),
                ft.Container(padding=6),
                self._opened_apps,
            ]
        )

    def did_mount(self):
        self.running = True
        self.page.run_task(self.update_state)

    def will_unmount(self):
        self.running = False

    async def update_state(self):
        while self.running:
            win_ctl = WindowControl()
            all_windows = win_ctl.get_all_windows()
            self._opened_apps.value = ' | '.join([
                it.getAppName() for it in sorted(all_windows, key=lambda it: it.getPID())
            ])

            window = pywinctl.getActiveWindow()

            if window:
                app_path = win_ctl.get_executable_path(window)

                title =  f'{window.getAppName()} {window.title} (Path: {app_path})'

                self._active_window_title.value = title
            else:
                self._active_window_title.value = None

            self.update()
            await asyncio.sleep(1)
