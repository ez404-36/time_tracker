import asyncio
import datetime
from inspect import isawaitable
from typing import Callable, Coroutine

import flet as ft


class TimerComponent(ft.Text):
    """
    Счетчик времени
    """
    page: ft.Page

    def __init__(self, seconds: int = 0, **kwargs):
        super().__init__(**kwargs)
        self.running = False
        self.seconds = seconds

    def did_mount(self):
        self.running = True
        self.page.run_task(self.update_timer)

    def will_unmount(self):
        self.running = False

    def update_value(self):
        self.value = str(datetime.timedelta(seconds=self.seconds))
        self.update()

    async def update_timer(self):
        while self.running:
            self.update_value()
            self.seconds += 1
            await asyncio.sleep(1)


class CountdownComponent(TimerComponent):
    """
    Обратный отсчёт
    """

    def __init__(
            self,
            seconds: int = 0,
            on_end: Coroutine[None, None, None] | Callable[[], None] = None,
            **kwargs,
    ):
        super().__init__(seconds=seconds, **kwargs)
        self.on_end = on_end

    async def update_timer(self):
        while self.running:
            self.update_value()

            if self.seconds == 0:
                self.running = False
                if self.on_end:
                    if isawaitable(self.on_end):
                        await self.on_end
                    else:
                        self.on_end()

            self.seconds -= 1
            await asyncio.sleep(1)
