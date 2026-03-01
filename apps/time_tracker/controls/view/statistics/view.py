import datetime
from collections import Counter, defaultdict

import flet as ft
from peewee import fn

from apps.time_tracker.controls.view.statistics.one_app_view import OneAppView, WindowTitleSessionData
from apps.time_tracker.controls.view.statistics.statistics_list import StatisticsListView
from apps.time_tracker.models import WindowSession, IdleSession
from core.utils import to_current_tz


class ActivityStatisticsView(ft.Column):
    """
    Компонент статистики активности пользователя
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._date_filter_btn: ft.TextButton | None = None
        self._date_filter_modal: ft.DatePicker | None = None
        self._app_statistics: StatisticsListView | None = None
        self._show_button: ft.TextButton | None = None
        self._refresh_button: ft.IconButton | None = None
        self._params_row: ft.Row | None = None

        self._filter_date_value: datetime.date = datetime.datetime.now(datetime.UTC).date()
        self._is_showed = False
        self._window_sessions: list[WindowSession] = []
        self._idle_sessions: list[IdleSession] = []

    def build(self):
        self._build_show_button()
        self._build_refresh_button()
        self._build_filter_btn()
        self._build_date_filter_modal()
        self._build_app_statistics()

        self._params_row = ft.Row(
            controls=[
                self._date_filter_btn,
            ],
            visible=False,
        )

        self.controls = [
            ft.Row(
                controls=[
                    ft.Text('Статистика', size=20, weight=ft.FontWeight.BOLD),
                    self._show_button,
                    self._refresh_button,
                ]
            ),
            self._params_row,
            ft.Container(margin=10),
            self._app_statistics,
        ]

        self._rebuild_app_statistics()

    def _build_app_statistics(self):
        self._app_statistics = StatisticsListView(
            visible=False,
        )

    def _rebuild_app_statistics(self, with_update=False):
        self._app_statistics.controls.clear()
        self._refresh_sessions_db()

        grouped_sessions: dict[str, Counter] = defaultdict(Counter)
        total_duration_apps = Counter()

        for session in self._window_sessions:
            app_name = session.app_name
            window_title = session.window_title
            duration = session.duration

            data = grouped_sessions[app_name]
            data[window_title] += duration
            total_duration_apps[app_name] += duration

        if self._idle_sessions:
            self._app_statistics.controls.append(
                OneAppView(
                    'Бездействие',
                    sum([it.duration for it in self._idle_sessions]),
                )
            )

        for app_name, duration in total_duration_apps.most_common():
            sessions = grouped_sessions[app_name]

            sessions_data = [
                WindowTitleSessionData(
                    window_title=window_title,
                    duration=duration,
                )
                for window_title, duration in sessions.most_common()
            ]

            self._app_statistics.controls.append(
                OneAppView(
                    app_name,
                    duration,
                    [it for it in sessions_data if it.get('window_title')],
                )
            )

        if with_update:
            self._app_statistics.update()

    def _refresh_sessions_db(self):
        self._idle_sessions = list(
            IdleSession.select()
            .where(
                fn.date(IdleSession.start_ts) == self._filter_date_value,
                IdleSession.duration > 0,
            )
            .order_by(IdleSession.duration.desc())
        )
        self._window_sessions = list(
            WindowSession.select()
            .where(
                fn.date(WindowSession.start_ts) == self._filter_date_value,
                WindowSession.duration > 0,
            )
        )

    def _build_show_button(self):
        if self._is_showed:
            text = 'Скрыть'
        else:
            text = 'Показать'

        if self._show_button:
            self._show_button.content = text
        else:
            self._show_button = ft.TextButton(
                content=text,
                on_click=self._on_click_show_button,
            )

    def _build_refresh_button(self):
        self._refresh_button = ft.IconButton(
            icon=ft.Icons.REFRESH,
            tooltip='Обновить',
            visible=False,
            on_click=self._on_click_refresh,
        )

    def _on_click_refresh(self, e):
        self.refresh_statistics()

    def _on_click_show_button(self, e):
        self.toggle_show_statistics()

    def refresh_statistics(self):
        self._rebuild_app_statistics(with_update=True)

    def toggle_show_statistics(self, force_show=False):
        self._is_showed = not self._is_showed or force_show

        for children in [self._params_row, self._app_statistics, self._refresh_button]:
            children.visible = self._is_showed

        self._build_show_button()
        self._rebuild_app_statistics()

        self.update()

    def _build_filter_btn(self):
        text = f'По дате: {self._filter_date_value.strftime("%d.%m.%y")}'

        if self._date_filter_btn:
            self._date_filter_btn.content = text
        else:
            self._date_filter_btn = ft.TextButton(
                content=text,
                on_click=lambda e: self.page.show_dialog(
                    self._date_filter_modal
                ),
            )

    def _build_date_filter_modal(self):
        start_date = datetime.date(year=2000, month=1, day=1)

        last_date = datetime.date(year=datetime.date.today().year, month=12, day=31)

        self._date_filter_modal = ft.DatePicker(
            value=self._filter_date_value,
            first_date=start_date,
            last_date=last_date,
            on_change=self._on_change_date_filter_modal,
        )

    def _on_change_date_filter_modal(self, e):
        date: datetime.date = to_current_tz(e.control.value).date()
        self._filter_date_value = date
        self._build_filter_btn()
        self._rebuild_app_statistics(with_update=False)
        self.update()
