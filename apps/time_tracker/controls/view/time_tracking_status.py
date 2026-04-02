import flet as ft

from core.di import container
from core.system_events.types import SystemEventStartMainTracker, SystemEvent, SystemEventTimestampData
from ui.components.timer import TimerComponent, CountdownComponent
from ui.consts import FontSize


class TimeTrackingStatus(ft.Row):
    """
    Компонент состояния отслеживания активности.
    Содержит заголовок + опциональный таймер (если отслеживание запущено)
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._store = container.session_store
        self._app_settings = container.app_settings
        self._event_bus = container.event_bus

    def build(self):
        self.controls = [
            self._get_default_label(),
        ]

        self._event_bus.subscribe('main_tracker.start', self._on_system_event_main_tracker_start)
        self._event_bus.subscribe('main_tracker.stop', self._on_system_event_main_tracker_stop)

        self._event_bus.subscribe('pomodoro_tracker.start_work', self._on_system_event_pomodoro_start_work)
        self._event_bus.subscribe('pomodoro_tracker.end_work', self._on_system_event_pomodoro_end_work)
        self._event_bus.subscribe('pomodoro_tracker.start_rest', self._on_system_event_pomodoro_start_rest)
        self._event_bus.subscribe('pomodoro_tracker.end_rest', self._on_system_event_pomodoro_end_rest)

    def _on_system_event_main_tracker_start(self, data: SystemEventStartMainTracker):
        if data.pomodoro_tracking:
            self._start_working()
        else:
            self._start_with_total_timer()

    def _on_system_event_main_tracker_stop(self, _data: SystemEventTimestampData):
        self.controls.clear()

        self.controls = [
            self._get_default_label(),
        ]

        self.update()

    def _on_system_event_pomodoro_start_work(self, _data: SystemEventTimestampData):
        self._start_working()

    def _on_system_event_pomodoro_end_work(self, _data: SystemEventTimestampData):
        self.controls.clear()

        self.controls = [
            self._get_label_component('Начать отдыхать'),
        ]

        self.update()

    def _on_system_event_pomodoro_start_rest(self, _data: SystemEventTimestampData):
        self._start_resting()

    def _on_system_event_pomodoro_end_rest(self, _data: SystemEventTimestampData):
        self.controls.clear()

        self.controls = [
            self._get_label_component('Начать работать'),
        ]

        self.update()

    def _start_with_total_timer(self):
        self.controls.clear()

        self.controls = [
            self._get_label_component('Общее время:'),
            TimerComponent(),
        ]

    def _start_working(self):
        self.controls.clear()

        timer = CountdownComponent(
            seconds=self._app_settings.pomodoro_work_time * 1,  # TODO: 60
            on_end=lambda: self._event_bus.publish(
                SystemEvent(
                    type='pomodoro_tracker.end_work',
                    data=SystemEventTimestampData(),
                )
            )
        )

        self.controls = [
            self._get_label_component('Работа:'),
            timer,
        ]

    def _start_resting(self):
        self.controls.clear()

        timer = CountdownComponent(
            seconds=self._app_settings.pomodoro_rest_time * 1,  # TODO: 60
            on_end=lambda: self._event_bus.publish(
                SystemEvent(
                    type='pomodoro_tracker.end_rest',
                    data=SystemEventTimestampData(),
                )
            )
        )

        self.controls = [
            self._get_label_component('Отдых:'),
            timer,
        ]

    def _get_default_label(self) -> ft.Text:
        return self._get_label_component('Отслеживание активности выключено')

    @staticmethod
    def _get_label_component(text: str) -> ft.Text:
        return ft.Text(
            value=text,
            size=FontSize.H5,
        )