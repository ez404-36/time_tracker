import os
import re
import subprocess

import psutil
import pywinctl

try:
    from ewmhlib import defaultEwmhRoot
    from pywinctl._pywinctl_linux import LinuxWindow
except ModuleNotFoundError:
    defaultEwmhRoot = object
    LinuxWindow = object

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

    def get_all_windows(self):
        try:
            windows = pywinctl.getAllWindows()
        except Exception as e:
            windows = defaultEwmhRoot.getClientListStacking()

        all_windows = self._remove_bad_windows(windows)
        return [
            self._as_window_data(it)
            for it in all_windows
        ]

    def get_idle_seconds(self) -> int:
        session = os.environ.get("XDG_SESSION_TYPE")

        # X11
        if session == "x11" and "DISPLAY" in os.environ:
            try:
                out = subprocess.check_output(["xprintidle"], stderr=subprocess.DEVNULL)
                return int(out.strip()) // 1000
            except Exception:
                pass

        # Wayland (GNOME)
        if session == "wayland":
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

    def _remove_bad_windows(self, windows: list[str | int] | None) -> list[LinuxWindow]:
        outList = []
        if windows is not None:
            for window in windows:
                try:
                    if window: outList.append(LinuxWindow(window))
                except Exception as e:
                    print(e)
                    pass
        return outList

    def get_executable_path(self, window: LinuxWindow) -> str:
        pid = window.getPID()
        p = psutil.Process(pid)
        return p.exe()

    @staticmethod
    def _as_window_data(window: LinuxWindow) -> WindowData:
        return WindowData(
            app_name=window.getAppName(),
            title=window.title,
        )
