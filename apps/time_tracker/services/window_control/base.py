import platform

from apps.time_tracker.services.window_control.abstract import WindowControlAbstract, WindowData
from apps.time_tracker.services.window_control.linux import WindowControlLinux
from apps.time_tracker.services.window_control.mac import WindowControlMac
from apps.time_tracker.services.window_control.windows import WindowControlWindows


class WindowControl:
    """
    Сервис, отвечающий за получение информации о текущих активных приложениях
    """

    service: WindowControlAbstract

    def __init__(self):
        system = platform.system()
        if system == 'Linux':
            self.service = WindowControlLinux()
        elif system == 'Windows':
            self.service = WindowControlWindows()
        elif system == 'Darwin':
            self.service = WindowControlMac()

    def get_active_window(self) -> WindowData | None:
        return self.service.get_active_window()

    def get_all_windows(self) -> list[WindowData]:
        return self.service.get_all_windows()

    def get_idle_seconds(self) -> int:
        return self.service.get_idle_seconds()
