import time

import flet as ft

from controls.activity_tab_controls import ActivityTabControl
from controls.new_activity_modal_controls import NewActivityModalControl
from controls.todo_tab_controls import TodoTabControl
from helpers import StateDBHelpers
from state import State, init_state

state: State = init_state(State)


class DesktopApp:
    def __init__(self, page: ft.Page):
        state['page'] = page
        StateDBHelpers(state).refresh_actions()
        StateDBHelpers(state).refresh_activities()

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
        # # page.on_window_event = self.window_event_handler
        # page.window.
        # page.update()

        self._new_activity_modal_control = NewActivityModalControl(state).init()
        self._activity_tab_control = ActivityTabControl(state).init()
        self._todo_tab_control = TodoTabControl(state).init()

        row = ft.Row(
            controls=[
                self._activity_tab_control.component,
                ft.VerticalDivider(width=10),
                self._todo_tab_control.component,
            ]
        )

        activity_track_row = ft.Row(
            controls=[
                self._activity_tab_control.activity_track_component,
            ]
        )

        page.add(row)
        page.add(activity_track_row)

    def window_event_handler(self, e):
        if e.data == 'close':
            print("Приложение закрывается!")
            state['page'].window.destroy()
            if activity_track := state['selected']['activity_track']:
                activity_track.stop = int(time.time())
                activity_track.save(only=['stop'])

def main(page: ft.Page):
    app = DesktopApp(page)
    app.init()


if __name__ == "__main__":
    ft.app(target=main)
