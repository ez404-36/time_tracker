import flet as ft

from apps.time_tracker.models import WindowSession


class WindowStatisticsRow(ft.Row):
    def __init__(self, app_name: str, windows: list[WindowSession]):
        self.app_name = app_name
        self.windows = windows

    def build(self):
        controls: list[ft.Control] = [
            ft.Text(self.app_name)
        ]

        if windows := self.windows:
            window_titles: list[ft.Text] = []
            for window in windows:
                window_titles.append(ft.Text(f'{window.window_title}: {window.duration}'))

            controls.append(
                ft.Column(controls=window_titles)
            )

        self.controls = controls
