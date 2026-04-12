from apps.time_tracker.services.window_control.abstract import WindowControlAbstract, WindowData


# TODO: реализация
class WindowControlMac(WindowControlAbstract):
    """
    Сервис, отвечающий за получение информации о текущих активных приложениях в Mac OS
    """

    def get_active_window(self) -> WindowData | None:
        return None

    def get_all_windows(self) -> list[WindowData]:
        return []

    def get_idle_seconds(self) -> int:
        return 0
