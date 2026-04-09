from typing import Protocol


class FletControlProtocol(Protocol):
    visible: bool

    def update(self): ...



class ShowHideMixin(FletControlProtocol):
    def show(self):
        self.visible = True
        self.update()

    def hide(self):
        self.visible = False
        self.update()
