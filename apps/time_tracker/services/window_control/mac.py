from apps.time_tracker.services.window_control.abstract import WindowControlAbstract, WindowData


class WindowControlMac(WindowControlAbstract):
    """
    Сервис, отвечающий за получение информации о текущих активных приложениях в Mac OS
    """

    def get_active_window(self) -> WindowData | None:
        # TODO: реализация
        return None
