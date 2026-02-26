import flet as ft

from apps.to_do.controls.todo_mutate_modal import ToDoMutateModal
from apps.to_do.helpers import refresh_todo_list
from apps.to_do.models import ToDo
from core.state import TodoTabState
from ui.consts import Colors, Icons, FontSize


class ToDoListItem(ft.ExpansionTile):
    """
    Отображение одной задачи
    """

    def __init__(self, state: TodoTabState, instance: ToDo, **kwargs):
        kwargs['title'] = None
        kwargs['affinity'] = ft.TileAffinity.TRAILING

        super().__init__(**kwargs)
        self._state = state
        self._instance = instance

    def build(self):
        is_done = self._instance.is_done

        self.leading = ft.Checkbox(
            value=is_done,
            fill_color=Colors.GREY if is_done else None,
            on_change=self._on_change_checkbox,
        )

        self.bgcolor = Colors.RED_LIGHT if self._instance.is_expired else None
        self.collapsed_bgcolor = Colors.RED_LIGHT if self._instance.is_expired else None

        self.title = self.get_text_label()

        self.subtitle = ft.Text(
            value=self._instance.description,
            size=FontSize.REGULAR if not self._instance.parent_id else FontSize.SMALL
        )

        self.trailing = ft.PopupMenuButton(
            icon=Icons.MORE_ACTIONS,
            items=self.get_popup_menu_items(),
        )

        children_tasks = self._instance.children

        self.controls = [
            self.__class__(state=self._state, instance=child)
            for child in children_tasks
        ]

    def _on_change_checkbox(self, e):
        is_done = e.control.value
        self._instance.is_done = is_done
        self._instance.save(only=['is_done'])
        refresh_todo_list(self._state)

    def _on_click_delete(self, e):
        self._instance.delete_instance()
        refresh_todo_list(self._state)

    def get_text_label(self) -> ft.Row:
        instance = self._instance

        font_size = FontSize.H5 if not self._instance.parent_id else FontSize.REGULAR

        text = ft.Text(
            value=f'(#{instance.id}) {instance.title}',
            size=font_size,
        )

        controls = []

        if deadline_str := instance.deadline_str:
            deadline = ft.Text(
                f'[{deadline_str}]',
                weight=ft.FontWeight.W_500,
                size=font_size
            )
            controls.append(deadline)

        is_any_children_expired = any([child.is_expired for child in instance.children])
        if is_any_children_expired and not self._instance.is_expired:
            controls.append(
                ft.Icon(
                    icon=ft.Icons.WARNING,
                    color=Colors.RED_LIGHT,
                    tooltip='Одна или несколько вложенных задач просрочены',
                ),
            )

        controls.append(text)
        return ft.Row(controls=controls)

    def get_popup_menu_items(self) -> list[ft.PopupMenuItem]:
        edit_menu_item = ft.PopupMenuItem(
           icon=Icons.EDIT,
           content='Редактировать',
           on_click=lambda e: self.page.show_dialog(ToDoMutateModal(self._state, instance=self._instance)),
        )

        add_children_menu_item = ft.PopupMenuItem(
            icon=Icons.ADD,
            content='Добавить вложенную задачу',
            on_click=lambda e: self.page.show_dialog(ToDoMutateModal(self._state, parent_instance=self._instance)),
        )

        delete_menu_item = ft.PopupMenuItem(
            icon=Icons.DELETE,
            content='Удалить',
            on_click=self._on_click_delete,
        )

        items = [edit_menu_item]

        if not self._instance.parent_id:
            items.append(add_children_menu_item)

        items.append(delete_menu_item)

        return items

