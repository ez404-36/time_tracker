import flet as ft

from apps.time_tracker.services.pomodoro import Pomodoro
from core.di import container
from ui.base.components.containers import BorderedContainer
from ui.components.timer import CountdownComponent
from ui.consts import Colors, FontSize, FontWeight, Icons


class PomodoroComponent(BorderedContainer):
    def __init__(self, **kwargs):
        kwargs.update({
            'width': 200,
            'height': 60,
        })

        super().__init__(**kwargs)

        self._store = container.session_store
        self._app_settings = container.app_settings
        self._service = Pomodoro()

        self._timer: CountdownComponent | None = None

        self._label: ft.Text | None = None
        self._start_button: ft.IconButton | None = None
        self._stop_button: ft.IconButton | None = None
        self._continue_button: ft.IconButton | None = None
        self._pause_button: ft.IconButton | None = None

    def build(self):
        self._label = self.get_label()
        self._start_button = self.get_start_button()
        self._pause_button = self.get_pause_button(visible=False)
        self._continue_button = self.get_continue_button(visible=False)
        self._stop_button = self.get_stop_button(visible=False)

        self.content = ft.Row(
            controls=[
                self._label,
                self._timer,
                self._start_button,
                self._pause_button,
                self._continue_button,
            ]
        )

    def get_label(self) -> ft.Text:
        return ft.Text(
            value=self._service.status,
            size=FontSize.H5,
            weight=FontWeight.W_500,
        )

    def get_timer(self) -> CountdownComponent:
        return CountdownComponent(
            seconds=self._service.rest_seconds,
            on_update_value=self.on_update_timer_value,
            on_end=self._service.stop_current_timer,
        )

    def on_update_timer_value(self, seconds: int) -> None:
        self._service.rest_seconds = seconds

    def get_start_button(self, visible=True) -> ft.IconButton:
        return ft.IconButton(
            icon=ft.Icon(
                icon=Icons.PAUSE,
                color=Colors.BLUE_LIGHT,
            ),
            visible=visible,
            on_click=self._on_click_start,
            tooltip='Запустить таймер',
        )

    def _on_click_start(self, e):
        self._service.start()

        self._start_button.visible = False
        self._pause_button.visible = True
        self._continue_button.visible = False
        self._stop_button.visible = False

        self.update()

    def get_stop_button(self, visible=True) -> ft.IconButton:
        return ft.IconButton(
            icon=ft.Icon(
                icon=Icons.STOP,
                color=Colors.RED_LIGHT,
            ),
            visible=visible,
            on_click=self._on_click_stop,
            tooltip='Выключить таймер',
        )

    def _on_click_stop(self, e):
        self._service.stop()

        self._start_button.visible = True
        self._pause_button.visible = False
        self._continue_button.visible = False
        self._stop_button.visible = False

        self.update()

    def get_pause_button(self, visible=True) -> ft.IconButton:
        return ft.IconButton(
            icon=ft.Icon(
                icon=Icons.PAUSE,
                color=Colors.RED_LIGHT,
            ),
            visible=visible,
            on_click=self._on_click_pause,
            tooltip='Приостановить',
        )

    def _on_click_pause(self, e):
        self._service.pause_current_timer(rest_seconds=self._timer.seconds)

        self._start_button.visible = False
        self._pause_button.visible = False
        self._continue_button.visible = True
        self._stop_button.visible = True

        self.update()

    def get_continue_button(self, visible=True) -> ft.IconButton:
        return ft.IconButton(
            icon=ft.Icon(
                icon=Icons.PLAY_ARROW,
                color=Colors.GREEN_LIGHT,
            ),
            visible=visible,
            on_click=self._on_click_continue,
            tooltip='Возобновить',
        )

    def _on_click_continue(self, e):
        if self._service.is_on_pause:
            method = self._service.resume
        else:
            method = self._service.start_next_timer

        method()

        self._start_button.visible = False
        self._pause_button.visible = True
        self._continue_button.visible = False
        self._stop_button.visible = True

        self.update()

    # def start(self):
    #     self._service.start()
    #
    #     self._timer = self.get_timer()
    #
    #     self.controls = [
    #         self.get_label(),
    #         self._timer,
    #         self.get_pause_button(),
    #     ]
    #     self.update()
    #
    # def stop(self):
    #     self._service.stop()
    #
    #     self._timer = None
    #
    #     self.controls.clear()
    #     self.update()
