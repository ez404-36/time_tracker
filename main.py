import flet as ft

from apps.time_tracker.consts import ActionIds
from apps.time_tracker.controls.view.activity_tab import ActivityTabViewControl
from apps.to_do.controls.todo_tab import TodoTabViewControl
from core.state import State, init_state


state: State = init_state(State)


class DesktopApp:
    def __init__(self, page: ft.Page):
        self.page: ft.Page = page

        self._activity_tab_control: ActivityTabViewControl | None = None
        self._todo_tab_control: TodoTabViewControl | None = None

    def init(self):
        """
        Инициализация десктопного приложения:
        * первичная отрисовка компонентов
        * определение обработчиков кнопок и селекторов
        """
        page = self.page

        page.title = 'Персональный менеджер'
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        page.vertical_alignment = ft.MainAxisAlignment.START

        page.window.prevent_close = True
        page.window.on_event = self.window_event_handler

        self._activity_tab_control = ActivityTabViewControl(state)
        self._todo_tab_control = TodoTabViewControl(state)

        tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            expand=1,
            tabs=[
                ft.Tab(
                    text='Трекер активности',
                    content=self._activity_tab_control,
                ),
                ft.Tab(
                    text='TODO',
                    content=self._todo_tab_control,
                )
            ]
        )

        page.add(tabs)

    def window_event_handler(self, e):
        if e.data == 'close':
            self.page.window.destroy()
            if activity_track := state['tabs']['activity']['selected']['day_track']:
                activity_track.change_action(ActionIds.STOP)

def main(page: ft.Page):
    app = DesktopApp(page)
    app.init()


if __name__ == "__main__":
    ft.app(target=main)
