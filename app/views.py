from PyQt6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMenuBar,
    QPushButton,
    QStackedWidget,
    QWidget,
)


class MenuBar(QMenuBar):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.file_menu = self.addMenu("File")
        self.help_menu = self.addMenu("Help")
        self.help_menu = self.addMenu("Versions")
        self.quit_menu = self.addMenu("Exit")

        if self.quit_menu != None:
            self.quit_action = self.quit_menu.addAction("Exit")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("App")

        # pages
        self.page1 = PageParametersGlobal(self)
        self.page2 = PageParametersComponent(self)

        # menubar
        self.menubar = MenuBar()
        self.setMenuBar(self.menubar)
        # quit_menu = self.menubar.addMenu("Quit")

        # stack
        self.stack = QStackedWidget()
        self.stack.addWidget(self.page1)
        self.stack.addWidget(self.page2)

        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(280)
        self.sidebar.addItems(
            [
                "Global Parameters",
                "Components",
                "Membrane/Permeability",
                "Operational Constraints",
                "Fixed variables",
            ]
        )
        self.sidebar.currentRowChanged.connect(self.stack.setCurrentIndex)

        layout = QHBoxLayout()
        layout.addWidget(self.sidebar)
        layout.addWidget(self.stack)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)


global_params = ["pressure_in", ["Pa", "kPa", "bar"]]


class PageParametersGlobal(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        # TODO: add a list and iterate with a loop for every input and unit box, and store the references to a dictionary to collect later on

        # parameters
        self.pressure_in_input = QLineEdit()
        self.pressure_in_unit = QComboBox()
        self.pressure_in_unit.addItems(["bar", "Pa", "kPa"])
        layout = QFormLayout()
        row_widget = QWidget()
        row_widget.setFixedWidth(300)
        row_layout = QHBoxLayout(row_widget)
        row_layout.addWidget(self.pressure_in_input)
        row_layout.addWidget(self.pressure_in_unit)
        layout.addRow("pressure_in:", row_widget)
        self.setLayout(layout)


class PageParametersComponent(QWidget):
    # TODO:
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        layout = QHBoxLayout()
        layout.addWidget(QLabel("lfksd"))
        self.setLayout(layout)
