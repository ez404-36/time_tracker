from typing import Any, TypedDict

import flet as ft

from apps.time_tracker.controls.view.statistics.one_row import StatisticsOneRow
from core.flet_helpers import get_from_store


class WindowTitleSessionData(TypedDict):
    window_title: str
    duration: int


class OneAppView(ft.Column):
    """
    Компонент отображения статистики по одному приложению
    """

    def __init__(
            self,
            app_name: str,
            total_time: int,
            sessions: list[WindowTitleSessionData] | None = None,
            **kwargs,
    ):
        super().__init__(**kwargs)
        self._app_name = app_name
        self._sessions = sessions
        self._total_time = total_time

        self._main_row: StatisticsOneRow | None = None
        self._children_component: ft.ListView | None = None

    def build(self):
        self._main_row = StatisticsOneRow(self._app_name, self._total_time, False, bool(self._sessions))

        expanded_statistics = get_from_store(self.page, 'expanded_statistics')
        self._children_component = ft.ListView(
            visible=bool(expanded_statistics and self._app_name in expanded_statistics),
        )

        controls: list[Any] = [
            self._main_row,
            self._children_component,
        ]

        if self._sessions:
            for session in self._sessions:
                self._children_component.controls.append(
                    StatisticsOneRow(
                        title=session['window_title'],
                        duration=session['duration'],
                        has_parent=True,
                        has_children=False,
                    )
                )

        self.controls = controls
