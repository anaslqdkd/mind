from PyQt6.QtWidgets import QPushButton


class MainController:
    def __init__(self, view):
        self.view = view
        # self.view.menubar.quit_action.triggered.connect(self.test)
        self.view.sidebar.currentRowChanged.connect(self.view.stack.setCurrentIndex)
        # view.button.clicked.connect(self.view.page1.get_parameters)

    def test(self):
        print("T")


class ComponentsController:
    def __init__(self, view) -> None:
        self.view = view
        # self.view.add_component_button.clicked.connect(self.view.add_component)

    def add_components(self):
        print("in add components")
