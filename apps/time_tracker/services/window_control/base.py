from apps.time_tracker.services.window_control.abstract import WindowControlAbstract, WindowData
from apps.time_tracker.services.window_control.linux import WindowControlLinux
from apps.time_tracker.services.window_control.mac import WindowControlMac
from apps.time_tracker.services.window_control.windows import WindowControlWindows
from core.settings import PLATFORM


class WindowControl:
    """
    Сервис, отвечающий за получение информации о текущих активных приложениях
    """

    service: WindowControlAbstract

    def __init__(self):
        if PLATFORM == 'Linux':
            self.service = WindowControlLinux()
        elif PLATFORM == 'Windows':
            self.service = WindowControlWindows()
        elif PLATFORM == 'Darwin':
            self.service = WindowControlMac()

    def __str__(self) -> str:
        return f'WindowControl({self.service.__class__.__name__})'

    def get_active_window(self) -> WindowData | None:
        return self.service.get_active_window()

    def get_all_windows(self) -> list[WindowData]:
        return self.service.get_all_windows()

    def get_idle_seconds(self) -> int:
        return self.service.get_idle_seconds()
