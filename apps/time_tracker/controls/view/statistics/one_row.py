import time

import flet as ft

from core.flet_helpers import get_from_store, get_or_create_from_store
from ui.consts import Colors


class StatisticsOneRow(ft.Container):
    """
    Компонент отображения одного пункта статистики:
    конкретной вкладки приложения или название приложения, по которому сгруппированы дочерние вкладки
    """

    def __init__(
            self,
            title: str,
            duration: int,  # секунд
            has_parent: bool,
            has_children: bool,
            **kwargs
    ):
        if has_parent:
            kwargs.setdefault('margin', ft.Margin(left=50, top=0, bottom=0, right=0))
        kwargs.setdefault('width', 500)
        super().__init__(**kwargs)
        self.has_parent = has_parent
        self.has_children = has_children
        self.title = title
        self.duration = duration
        self.is_expanded = False
        self.text_width = 14 if not self.has_parent else 12
        self.text_bold = True if not self.has_parent else False
        self.text_color = Colors.RED_LIGHT if title == 'Бездействие' else Colors.BLACK

        self._text: ft.Text | None = None
        self._duration_text: ft.Text | None = None
        self._expand_children_icon: ft.IconButton | None = None

    def build(self):
        expanded_statistics = get_from_store(self.page, 'expanded_statistics')
        self.is_expanded = expanded_statistics and self.title in expanded_statistics

        if self.has_children:
            self.build_expand_children_icon()
        self.build_text()
        self.build_duration_text()

        controls: list[ft.Control] = [self._text]

        if self.has_children:
            controls.append(self._expand_children_icon)

        controls.append(self._duration_text)

        self.content = ft.Row(controls)

    def build_text(self):
        self._text = ft.Text(
            self.title,
            size=self.text_width,
            weight=ft.FontWeight.W_500 if self.text_bold else ft.FontWeight.NORMAL,
            color=self.text_color,
            width=120 if not self.has_parent else 200,
        )

    def build_duration_text(self):
        struct_time = time.gmtime(self.duration)
        txt = time.strftime("%H:%M:%S", struct_time)

        self._duration_text = ft.Text(
            value=txt,
            weight=ft.FontWeight.W_500 if self.text_bold else ft.FontWeight.NORMAL,
            color=self.text_color,
            size=self.text_width,
        )

    def build_expand_children_icon(self):
        if self.is_expanded:
            icon = ft.Icons.KEYBOARD_ARROW_DOWN
            tooltip = 'Скрыть подробности'
        else:
            icon = ft.Icons.KEYBOARD_ARROW_RIGHT
            tooltip = 'Показать подробности'

        if self._expand_children_icon:
            self._expand_children_icon.icon = icon
            self._expand_children_icon.tooltip = tooltip
            self._expand_children_icon.visible = self.has_children
        else:
            self._expand_children_icon = ft.IconButton(
                icon=icon,
                tooltip=tooltip,
                visible=self.has_children,
                on_click=self.on_click_expand_children_icon,
            )

    def on_click_expand_children_icon(self, e):
        self.is_expanded = not self.is_expanded

        expanded_statistics: set[str] = get_or_create_from_store(self.page, 'expanded_statistics', set())

        if self.is_expanded:
            expanded_statistics.add(self.title)
        else:
            expanded_statistics.discard(self.title)

        self.build_expand_children_icon()

        parent = self.parent

        parent._children_component.visible = self.is_expanded

        parent.update()
