import psutil
import pywinctl
from ewmhlib import defaultEwmhRoot
from pywinctl._pywinctl_linux import LinuxWindow


class WindowControl:
    """
    Сервис, отвечающий за получение информации о текущих активных приложениях
    """

    def get_all_windows(self):
        try:
            windows = pywinctl.getAllWindows()
        except Exception as e:
            windows = defaultEwmhRoot.getClientListStacking()

        return self.remove_bad_windows(windows)

    def remove_bad_windows(self, windows: list[str | int] | None) -> list[LinuxWindow]:
        outList = []
        if windows is not None:
            for window in windows:
                try:
                    if window: outList.append(LinuxWindow(window))
                except Exception as e:
                    pass
        return outList

    def get_executable_path(self, window: LinuxWindow) -> str:
        pid = window.getPID()
        p = psutil.Process(pid)
        return p.exe()

