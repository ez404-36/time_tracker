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

        self._date_filter_btn: ft.TextButton | None = None
        self._date_filter_modal: ft.DateRangePicker | None = None

        self._filter_date_value = datetime.datetime.now(datetime.UTC)

    def build(self):
        self._build_filter_btn()
        self._build_date_filter_modal()

        self.controls = [
            ft.Text('Статистика', size=20, weight=ft.FontWeight.BOLD),
            self._date_filter_btn,
        ]

    def _build_filter_btn(self):
        self._date_filter_btn = ft.TextButton(
            f'Дата: {self._filter_date_value.strftime("%d.%m.%y")}',
            on_click=lambda e: self.page.show_dialog(
                self._date_filter_modal,
            ),
        )

    def _build_date_filter_modal(self):
        start_date = datetime.datetime(
            year=1900,
            month=1,
            day=1,
            tzinfo=self._filter_date_value.tzinfo,
        )

        last_date = datetime.datetime(
            year=2099,
            month=12,
            day=31,
            tzinfo=self._filter_date_value.tzinfo,
        )

        self._date_filter_modal = ft.DateRangePicker(
            start_value=self._filter_date_value,
            end_value=self._filter_date_value,
            first_date=start_date,
            last_date=last_date,
            on_change=self._on_change_date_filter_modal,
        )

    def _on_change_date_filter_modal(self, e: ft.Event[ft.DateRangePicker]):
        print('Changed', e)
