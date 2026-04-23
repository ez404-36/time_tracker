import flet as ft

from apps.time_tracker.types import PomodoroTimerStatus
from core.consts import SECONDS_PER_MINUTE
from core.di import container
from core.system_events import types as system_event_type
from ui.base.components.text import TextComponent
from ui.components.timer import TimerComponent, CountdownComponent
from ui.consts import FontSize


class TimeTrackingStatus(ft.Row):
    """
    Компонент состояния отслеживания активности.
    Содержит заголовок + опциональный таймер (если отслеживание запущено)
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._timer: TimerComponent | None = None

        self._store = container.session_store
        self._app_settings = container.app_settings
        self._event_bus = container.event_bus
        self._main_tracker = container.main_tracker

    def build(self):
        self.controls = [
            self._get_default_label(),
        ]

        self._event_bus.subscribe('main_tracker.start', self._on_system_event_main_tracker_start)
        self._event_bus.subscribe('main_tracker.pause', lambda e: self._timer.pause())
        self._event_bus.subscribe('main_tracker.resume', lambda e: self._timer.resume())
        self._event_bus.subscribe('main_tracker.stop', self._on_system_event_main_tracker_stop)

        self._event_bus.subscribe('pomodoro_tracker.change_status', self._on_pomodoro_tracker_change_status)

    def _on_system_event_main_tracker_start(self, data: system_event_type.SystemEventStartMainTracker):
        if data.pomodoro_tracking:
            self._start_working()
        else:
            self._start_with_total_timer()

    def _on_system_event_main_tracker_stop(self, _data: system_event_type.SystemEventTimestampData):
        self.controls.clear()

        self.controls = [
            self._get_default_label(),
        ]

        self.update()

    def _on_pomodoro_tracker_change_status(self, data: system_event_type.SystemEventPomodoroChangeStatus):
        new_status: PomodoroTimerStatus = data.new_status

        if data.prev_status in ['working_pause', 'resting_pause']:
            self._timer.resume()
        elif new_status == 'resting':
            self._start_resting()
        elif new_status == 'working':
            self._start_working()
        elif new_status == 'working_stop':
            self._pomodoro_end_work()
        elif new_status == 'resting_stop':
            self._pomodoro_end_rest()

    def _pomodoro_end_work(self):
        self._reset()

        self.controls = [
            self._get_label_component('Отдых'),
        ]

        self.update()

    def _pomodoro_end_rest(self):
        self._reset()

        self.controls = [
            self._get_label_component('Работа'),
        ]

        self.update()

    def _start_with_total_timer(self):
        self._reset()

        self._timer = TimerComponent()

        self.controls = [
            self._get_label_component('Общее время:'),
            self._timer,
        ]

    def _start_working(self):
        self._reset()

        self._timer = CountdownComponent(
            seconds=self._app_settings.pomodoro_work_time * SECONDS_PER_MINUTE,
            on_end=self._main_tracker.hold,
        )

        self.controls = [
            self._get_label_component('Работа:'),
            self._timer,
        ]

    def _start_resting(self):
        self.controls.clear()

        self._timer = CountdownComponent(
            seconds=self._app_settings.pomodoro_rest_time * SECONDS_PER_MINUTE,
            on_end=self._main_tracker.hold,
        )

        self.controls = [
            self._get_label_component('Отдых:'),
            self._timer,
        ]

    def _get_default_label(self) -> ft.Text:
        return self._get_label_component('Отслеживание активности выключено')

    @staticmethod
    def _get_label_component(text: str) -> ft.Text:
        return TextComponent(
            value=text,
            size=FontSize.H5,
        )

    def _reset(self):
        self.controls.clear()
        self._timer = None
