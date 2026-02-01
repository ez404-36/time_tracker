import time

import flet as ft


class StatisticsOneRow(ft.Container):
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
        kwargs.setdefault('visible', not has_parent)
        kwargs.setdefault('width', 500)
        super().__init__(**kwargs)
        self.has_parent = has_parent
        self.has_children = has_children
        self.title = title
        self.duration = duration
        self.is_expanded = False
        self.text_width = 14 if not self.has_parent else 12
        self.text_bold = True if not self.has_parent else False

        self._text: ft.Text | None = None
        self._duration_text: ft.Text | None = None
        self._expand_children_icon: ft.IconButton | None = None

    def build(self):
        if self.has_children:
            self.build_expand_children_icon()
        self.build_text()
        self.build_duration_text()

        controls: list[ft.Control] = [self._text]

        if self.has_children:
            controls.append(self._expand_children_icon)

        controls.append(self._duration_text)

        self.content = ft.Row(controls)
        # self.controls = controls

    def build_text(self):
        self._text = ft.Text(
            self.title,
            size=self.text_width,
            weight=ft.FontWeight.W_500 if self.text_bold else ft.FontWeight.NORMAL,
            width=120 if not self.has_parent else 200,
        )

    def build_duration_text(self):
        struct_time = time.gmtime(self.duration)
        txt = time.strftime("%H:%M:%S", struct_time)

        self._duration_text = ft.Text(
            value=txt,
            weight=ft.FontWeight.W_500 if self.text_bold else ft.FontWeight.NORMAL,
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
        self.build_expand_children_icon()

        parent = self.parent.parent

        show_children = self.is_expanded
        for control in parent.controls:
            control.visible = show_children or isinstance(control, ft.Row)

        parent.update()
