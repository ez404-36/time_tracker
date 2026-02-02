import asyncio
import datetime

import flet as ft


class TimerComponent(ft.Text):
    """
    Счетчик времени
    """

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

    async def update_timer(self):
        while self.running:
            self.update_value()
            self.seconds -= 1
            await asyncio.sleep(1)


class TimerStaticComponent(TimerComponent):
    def update_value(self, with_refresh=True):
        self.value = f'(Всего сегодня: {datetime.timedelta(seconds=self.seconds)})'
        self.update()

    def did_mount(self):
        self.update_value()
