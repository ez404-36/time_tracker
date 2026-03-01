import psutil
import ctypes


from apps.time_tracker.services.window_control.abstract import WindowControlAbstract, WindowData

try:
    import win32gui
    import win32process
except ModuleNotFoundError:
    win32gui = object
    win32process = object


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
            proc = psutil.Process(pid)
            exe = proc.exe()
            name = proc.name()
            return WindowData(
                executable_name=name,
                window_title=win32gui.GetWindowText(hwnd),
                executable_path=exe,
            )
        except psutil.Error:
            return None

    def get_all_windows(self) -> list[WindowData]:
        windows: list[WindowData] = []

        def callback(hwnd, _):
            if not win32gui.IsWindowVisible(hwnd):
                return

            title = win32gui.GetWindowText(hwnd)
            if not title:
                return

            _, pid = win32process.GetWindowThreadProcessId(hwnd)

            try:
                proc = psutil.Process(pid)
                exe = proc.exe()
                name = proc.name()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return

            windows.append(
                WindowData(
                    executable_name=name,
                    window_title=title,
                    executable_path=exe,
                )
            )

        win32gui.EnumWindows(callback, None)
        return windows

    def get_idle_seconds(self) -> int:
        lii = LastInputInfo()
        lii.cbSize = ctypes.sizeof(lii)
        ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii))
        millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
        return millis // 1000
