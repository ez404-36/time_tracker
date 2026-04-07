from core.system_events.types import SystemEventStartMainTracker


class TrackerInfoMixin:
    """
    Миксин с информацией о состоянии трекера активности
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._is_tracker_running: bool = False
        self._tracker_config = SystemEventStartMainTracker.default()

    def _set_tracker_config_on_start(self, data: SystemEventStartMainTracker):
        self._is_tracker_running = True
        self._tracker_config = data

    def _set_tracker_config_on_stop(self):
        self._is_tracker_running = True
        self._tracker_config = SystemEventStartMainTracker.default()