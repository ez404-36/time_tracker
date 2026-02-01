import datetime
from collections import Counter, defaultdict

import flet as ft

from apps.time_tracker.controls.view.statistics.one_app_view import OneAppView, WindowTitleSessionData
from apps.time_tracker.controls.view.statistics.sort_dropdown import StatisticsSortDropdown
from core.state import ActivityTabState
from apps.time_tracker.models import WindowSession, IdleSession


class ActivityStatisticsView(ft.Column):
    """
    Компонент статистики активности пользователя
    """

    page: ft.Page

    def __init__(self, state: ActivityTabState, **kwargs):
        super().__init__(**kwargs)
        self._state = state

        self._date_filter_btn: ft.TextButton | None = None
        self._date_filter_modal: ft.DatePicker | None = None
        self._app_statistics: ft.Column | None = None
        self._sort_dropdown: StatisticsSortDropdown | None = None
        self._show_button: ft.TextButton | None = None
        self._params_row: ft.Row | None = None

        self._filter_date_value: datetime.date = datetime.datetime.now(datetime.UTC).date()
        self._is_showed = False

    def build(self):
        self._build_show_button()
        self._build_filter_btn()
        self._build_date_filter_modal()

        self._sort_dropdown = StatisticsSortDropdown(border_width=0)
        self._app_statistics = ft.Column(
            visible=False,
            scroll=ft.ScrollMode.ADAPTIVE,
            height=600,
        )

        self._params_row = ft.Row(
            controls=[
                self._date_filter_btn,
                # self._sort_dropdown,
            ],
            visible=False,
        )

        self.controls = [
            ft.Row(
                controls=[
                    ft.Text('Статистика', size=20, weight=ft.FontWeight.BOLD),
                    self._show_button,
                ]
            ),
            self._params_row,
            ft.Container(margin=10),
            self._app_statistics,
        ]

        # TODO: Выборка по дате

        # TODO: get total duration
        idle_sessions = list(
            IdleSession.select()
            .order_by(IdleSession.duration.desc())
        )

        grouped_sessions: dict[str, Counter] = defaultdict(Counter)
        total_duration_apps = Counter()

        for session in WindowSession.select():
            app_name = session.app_name
            window_title = session.window_title
            duration = session.duration

            data = grouped_sessions[app_name]
            data[window_title] += duration
            total_duration_apps[app_name] += duration

        if idle_sessions:
            self._app_statistics.controls.append(
                OneAppView(
                    'Бездействие',
                    0,   # TODO
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
                    sessions_data,
                )
            )

    def _build_show_button(self):
        if self._is_showed:
            text = 'Скрыть'
        else:
            text = 'Показать'

        if self._show_button:
            self._show_button.text = text
        else:
            self._show_button = ft.TextButton(
                text=text,
                on_click=self._on_click_show_button,
            )

    def _on_click_show_button(self, e):
        self._is_showed = not self._is_showed

        for children in [self._params_row, self._app_statistics]:
            children.visible = self._is_showed

        self._build_show_button()

        self.update()

    def _build_filter_btn(self):
        self._date_filter_btn = ft.TextButton(
            f'По дате: {self._filter_date_value.strftime("%d.%m.%y")}',
            on_click=lambda e: self.page.open(
                self._date_filter_modal
            ),
        )

    def _build_date_filter_modal(self):
        start_date = datetime.date(
            year=2000,
            month=1,
            day=1,
            # tzinfo=self._filter_date_value.tzinfo,
        )

        last_date = datetime.date(
            year=2099,
            month=12,
            day=31,
            # tzinfo=self._filter_date_value.tzinfo,
        )

        self._date_filter_modal = ft.DatePicker(
            value=self._filter_date_value,
            first_date=start_date,
            last_date=last_date,
            on_change=self._on_change_date_filter_modal,
        )

    def _on_change_date_filter_modal(self, e):
        print('Changed', e)
