import flet as ft


# TODO: сделать
class StatisticsSortDropdown(ft.Dropdown):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.value = 'time_desc'
        self.label = 'Сортировка'
        self.on_select = self.handle_select

        self.options = [
            ft.DropdownOption(key='name', text='По названию (А-Я)'),
            ft.DropdownOption(key='name_desc', text='По названию (Я-А)'),
            ft.DropdownOption(key='time', text='По времени (от меньшего)'),
            ft.DropdownOption(key='time_desc', text='По времени (от большего)'),
        ]

    def handle_select(self, e):
        print(self.parent, e)
