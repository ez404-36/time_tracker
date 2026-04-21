import os
import re
import subprocess

import psutil

from core.settings import USE_WAYLAND, USE_X11

try:
    from ewmhlib import defaultEwmhRoot
    import pywinctl
    from pywinctl._pywinctl_linux import LinuxWindow
except ModuleNotFoundError:
    defaultEwmhRoot = object
    LinuxWindow = object
    pywinctl = object

from apps.time_tracker.services.window_control.abstract import WindowControlAbstract, WindowData


class WindowControlLinux(WindowControlAbstract):
    """
    Сервис, отвечающий за получение информации о текущих активных приложениях в Linux-системах
    """

    def get_active_window(self) -> WindowData | None:
        window = pywinctl.getActiveWindow()
        if not window:
            return None

        return self._as_window_data(window)

    def get_all_windows(self) -> list[WindowData]:
        try:
            windows = pywinctl.getAllWindows()
        except Exception as e:
            print(e)
            windows = defaultEwmhRoot.getClientListStacking()

        all_windows = self._remove_bad_windows(windows)
        return [
            self._as_window_data(it)
            for it in all_windows
        ]

    def get_idle_seconds(self) -> int:
        # X11
        if USE_X11 and "DISPLAY" in os.environ:
            try:
                out = subprocess.check_output(["xprintidle"], stderr=subprocess.DEVNULL)
                return int(out.strip()) // 1000
            except Exception as e:
                print(e)

        # Wayland (GNOME)
        if USE_WAYLAND:
            try:
                out = subprocess.check_output([
                    "gdbus", "call",
                    "--session",
                    "--dest", "org.gnome.Mutter.IdleMonitor",
                    "--object-path", "/org/gnome/Mutter/IdleMonitor/Core",
                    "--method", "org.gnome.Mutter.IdleMonitor.GetIdletime"
                ])
                ms = int(re.search(rb"\d+", out).group())
                return ms // 1000
            except Exception as e:
                print(e)
                pass

        return 0

    @staticmethod
    def _remove_bad_windows(windows: list[str | int] | None) -> list[LinuxWindow]:
        output = []
        if windows is not None:
            for window in windows:
                try:
                    if window: output.append(window)
                except Exception as e:
                    print(e)
                    pass
        return output

    @staticmethod
    def get_executable_path(window: LinuxWindow) -> str:
        pid = window.getPID()
        p = psutil.Process(pid)
        return p.exe()

    def _as_window_data(self, window: LinuxWindow) -> WindowData:
        return WindowData(
            executable_name=window.getAppName(),
            window_title=window.title,
            executable_path=self.get_executable_path(window),
        )
