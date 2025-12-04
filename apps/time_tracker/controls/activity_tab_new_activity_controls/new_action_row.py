import flet as ft

from apps.time_tracker.controls.activity_tab_new_activity_controls.base import BaseNewActivityModalControl


class NewActivityModalActionRowControl(BaseNewActivityModalControl):
    def build(self, default: str = None):
        def on_click_action_remove(e):
            self._state['actions_view'].controls.remove(self._component)
            self._state['actions_view'].update()

        action_input = ft.TextField(width=200)
        is_target_action_checkbox = ft.Checkbox(label='Полезное действие')
        other_action_delete_button = ft.IconButton(ft.Icons.REMOVE, on_click=on_click_action_remove)

        self._component = ft.Row(
            controls=[
                action_input,
                is_target_action_checkbox,
                other_action_delete_button,
            ]
        )

        self._state['actions_view'].controls.append(self._component)
        self._state['actions_view'].update()

        return self
