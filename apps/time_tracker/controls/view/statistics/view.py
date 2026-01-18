import datetime

import flet as ft

from core.state import ActivityTabState


class ActivityStatisticsView(ft.Column):
    """
    Компонент статистики активности пользователя
    """

    page: ft.Page

    def __init__(self, state: ActivityTabState, **kwargs):
        self._state = state
        super().__init__(**kwargs)

        self._date_filter_btn: ft.TextButton | None = None
        self._date_filter_modal: ft.DateRangePicker | None = None

        self._filter_date_value_start = datetime.datetime.now()
        self._filter_date_value_end = datetime.datetime.now()

    def build(self):
        self._build_filter_btn()
        self._build_date_filter_modal()

        self.controls = [
            ft.Text('Статистика', size=20, weight=ft.FontWeight.BOLD),
            self._date_filter_btn,
        ]

    def _build_filter_btn(self):
        self._date_filter_btn = ft.TextButton(
            self._get_text_for_filter_btn(),
            on_click=lambda e: self.page.show_dialog(self._date_filter_modal),
            visible=True,
        )

    def _build_date_filter_modal(self):
        start_date = datetime.datetime(
            year=2000,
            month=1,
            day=1,
            tzinfo=self._filter_date_value_start.tzinfo,
        )

        last_date = datetime.datetime(
            year=self._filter_date_value_end.year,
            month=12,
            day=31,
            tzinfo=self._filter_date_value_end.tzinfo,
        )

        self._date_filter_modal = ft.DateRangePicker(
            start_value=self._filter_date_value_start,
            end_value=self._filter_date_value_end,
            first_date=start_date,
            last_date=last_date,
            on_change=self._on_change_date_filter_modal,
            modal=True,
        )

    @staticmethod
    def _format_date(date: datetime.datetime):
        return date.strftime("%d.%m.%Y")

    def _get_text_for_filter_btn(self):
        start = self._format_date(self._filter_date_value_start)
        end = self._format_date(self._filter_date_value_end)

        if start == end:
            return f'Дата: {start}'
        else:
            return f'Дата: {start} - {end}'

    def _on_change_date_filter_modal(self, e: ft.Event[ft.DateRangePicker]):
        self._filter_date_value_start = e.control.start_value
        self._filter_date_value_end = e.control.end_value

        self._date_filter_btn.content = self._get_text_for_filter_btn()
        self._date_filter_btn.update()
