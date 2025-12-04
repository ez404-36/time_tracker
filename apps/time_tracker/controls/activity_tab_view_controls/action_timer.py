import asyncio
import datetime

import flet as ft

from apps.time_tracker.models import Action


class ActionTimerComponent(ft.Text):
    def __init__(self, action: Action, seconds: int, **kwargs):
        super().__init__(**kwargs)
        self.running = False
        self.disabled = True
        self.seconds = seconds
        self._action = action

    @property
    def action(self) -> Action:
        return self._action

    def did_mount(self):
        self.running = True
        self.page.run_task(self.update_timer)
        self.update_value()

    def will_unmount(self):
        self.running = False

    def update_value(self, with_refresh=True):
        if self.seconds:
            self.value = datetime.timedelta(seconds=self.seconds)
        else:
            self.value = None

        if with_refresh:
            self.update()

    def reset_timer(self, with_refresh=True):
        self.disabled = True
        self.seconds = 0
        self.update_value(with_refresh)

    async def update_timer(self):
        while self.running:
            if not self.disabled:
                self.update_value()
                self.seconds += 1
            await asyncio.sleep(1)


class ActionTimerStaticComponent(ActionTimerComponent):
    def update_value(self, with_refresh=True):
        self.value = f'(Всего сегодня: {datetime.timedelta(seconds=self.seconds)})'
        self.update()

    def did_mount(self):
        self.update_value()
