import flet as ft

from apps.time_tracker.consts import STOP_ACTION_ID
from apps.time_tracker.controls.activity_tab_new_activity_controls.modal import NewActivityModalControl
from apps.time_tracker.controls.activity_tab_view_controls.activity_tab import ActivityTabControl
from apps.to_do.controls.todo_tab import TodoTabControl
from core.state import State, init_state


state: State = init_state(State)


class DesktopApp:
    def __init__(self, page: ft.Page):
        state['page'] = page

        self._new_activity_modal_control: NewActivityModalControl | None = None
        self._activity_tab_control: ActivityTabControl | None = None
        self._todo_tab_control: TodoTabControl | None = None

    def init(self):
        """
        Инициализация десктопного приложения:
        * первичная отрисовка компонентов
        * определение обработчиков кнопок и селекторов
        """
        page = state['page']

        page.title = 'Персональный менеджер'
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        page.vertical_alignment = ft.CrossAxisAlignment.START

        page.window.prevent_close = True
        page.window.on_event = self.window_event_handler

        self._new_activity_modal_control = NewActivityModalControl(state).build()
        self._activity_tab_control = ActivityTabControl(state).build()
        self._todo_tab_control = TodoTabControl(state).build()

        tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            expand=1,
            tabs=[
                ft.Tab(
                    text='Трекер активности',
                    content=self._activity_tab_control.component,
                ),
                ft.Tab(
                    text='TODO',
                    content=self._todo_tab_control.component,
                )
            ]
        )

        page.add(tabs)

    def window_event_handler(self, e):
        if e.data == 'close':
            state['page'].window.destroy()
            if activity_track := state['tabs']['activity']['selected']['activity_track']:
                activity_track.change_action(STOP_ACTION_ID)

def main(page: ft.Page):
    app = DesktopApp(page)
    app.init()


if __name__ == "__main__":
    ft.app(target=main)
