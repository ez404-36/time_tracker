# import win32gui
# import win32process
import psutil
import ctypes

from apps.time_tracker.services.window_control.abstract import WindowControlAbstract, WindowData

win32gui = object   # TODO
win32process = object   # TODO


class LastInputInfo(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_uint),
        ("dwTime", ctypes.c_uint),
    ]


class WindowControlWindows(WindowControlAbstract):
    """
    Сервис, отвечающий за получение информации о текущих активных приложениях в Linux-системах
    """

    def get_active_window(self) -> WindowData | None:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return None

        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        try:
            process = psutil.Process(pid)
            return WindowData(
                app_name=process.name(),
                title=win32gui.GetWindowText(hwnd),
            )
        except psutil.Error:
            return None

    def get_idle_seconds(self) -> int:
        lii = LastInputInfo()
        lii.cbSize = ctypes.sizeof(lii)
        ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii))
        millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
        return millis // 1000
