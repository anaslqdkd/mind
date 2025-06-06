from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenuBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QTabWidget,
    QVBoxLayout,
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
        self.page_components = PageParametersComponent(self)

        # test button
        self.button = QPushButton()

        # menubar
        # self.menubar = MenuBar()
        # self.setMenuBar(self.menubar)

        # stack
        self.stack = QStackedWidget()
        # self.stack.addWidget(self.page1)
        # self.stack.addWidget(self.page_components)

        # tabs
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        tab1_layout = QVBoxLayout()
        tab1_layout.addWidget(QLabel("Tab 1"))
        tab2_layout = QVBoxLayout()
        tab2_layout.addWidget(QLabel("Tab 2"))
        self.tab2.setLayout(tab2_layout)

        self.tabs.addTab(self.tab1, "Tab 1")
        self.tabs.addTab(self.tab2, "Tab 2")

        self.main_area = QWidget()
        main_area_layout = QHBoxLayout(self.main_area)
        header = QLabel("Main Area Header")
        style = "border: 1px solid gray; padding: 4px;"
        header.setStyleSheet(style)
        header.setFixedHeight(50)
        self.main_area.setStyleSheet(style)

        # nav bar
        nav_bar_layout = QHBoxLayout()
        nav_bar = QWidget()
        nav_bar.setFixedHeight(50)
        nav_bar.setLayout(nav_bar_layout)
        home_button = QPushButton("Home")
        form_button = QPushButton("Form")
        nav_bar_layout.addWidget(home_button)
        nav_bar_layout.addWidget(form_button)
        nav_bar_layout.addStretch()
        nav_bar.setStyleSheet(style)

        # sidebar
        self.sidebar = QListWidget()
        self.sidebar.setFixedSize(300, 600)
        self.sidebar.addItems(
            [
                "Global Parameters",
                "Components",
                "Membrane/Permeability",
                "Operational Constraints",
                "Fixed variables",
            ]
        )

        # button_item = QListWidgetItem()
        # self.sidebar.addItem(button_item)
        button_widget = QPushButton("Button")
        # self.sidebar.setItemWidget(button_item, button_widget)
        # button_item.setSizeHint(button_widget.sizeHint())

        # ----------------------------------------------------
        sidebar_layout = QVBoxLayout()
        self.sidebar.setFixedWidth(310)
        sidebar_layout.addWidget(self.sidebar)
        sidebar_layout.addWidget(button_widget)
        sidebar_layout.addStretch()
        sidebar_widget = QWidget()
        sidebar_widget.setLayout(sidebar_layout)
        sidebar_widget.setFixedWidth(330)

        layout = QVBoxLayout()
        layout.addWidget(header)
        layout.addWidget(nav_bar)
        layout.addWidget(self.main_area)
        # main_area_layout.addWidget(self.sidebar)
        main_area_layout.addWidget(sidebar_widget)
        main_area_layout.addWidget(self.page1)
        self.page1.setFixedWidth(1000)
        main_area_layout.addStretch()
        # layout.addLayout(nav_bar_layout)
        # layout.addWidget(self.main_area)
        # layout.addWidget(self.sidebar)
        # layout.addWidget(self.tabs)
        # main_area_layout.addWidget(self.sidebar)
        # layout.addWidget(self.stack)
        # layout.addWidget(self.button)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)


global_params = {
    # TODO: add the general algo params
    "pressure_in": ["bar", "Pa", "kPa"],
    "pressure_out": ["bar", "Pa", "kPa"],
    "f2ed": ["mol/s"],
    "f3ed": ["mol/s"],
    # "f4ed": ["mol/s"],
    # "f5ed": ["m1l/s"],
    # "f6ed": ["m2l/s"],
    # "f7ed": ["m3l/s"],
    # "f2ed": ["m4l/s"],
    # "f1ed": ["m4l/s"],
    # "f1ed": ["m4l/s"],
    # "f1ed": ["m4l/s"],
    # "f1ed": ["m4l/s"],
    # "f11d": ["m4l/s"],
    # "f12d": ["m4l/s"],
    # "f15d": ["m4l/s"],
    # "f17d": ["m4l/s"],
    # "f18d": ["m4l/s"],
    # "f18d": ["m4l/s"],
    # "118d": ["m4l/s"],
    # "218d": ["m4l/s"],
    # "518d": ["m4l/s"],
}


class Parameter:
    # TODO:
    def __init__(self, name: str, measure: list[str]) -> None:
        self.name = name
        self.measure = measure


class PageParametersGlobal(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.parameters = {}

        header2 = QLabel("Main Area Header")
        style = "border: 1px solid gray; padding: 4px;"
        header2.setStyleSheet(style)
        header2.setFixedHeight(50)
        main_layout = QVBoxLayout()

        # wrapper_form_layout = QHBoxLayout()

        content_layout = QVBoxLayout()
        content_widget = QWidget()
        content_widget.setLayout(content_layout)
        # content_layout.setSpacing(10)

        form_layout = QFormLayout()
        # parameters

        for i, (key, value) in enumerate(global_params.items(), start=1):
            # Horizontal row: number + input area
            row_layout = QHBoxLayout()
            # row_layout.setSpacing(50)

            # Number
            number_label = QLabel(f"{i}.")
            number_label.setFixedSize(50, 50)
            number_label.setAlignment(Qt.AlignmentFlag.AlignTop)

            # Vertical input area
            input_layout = QVBoxLayout()
            # input_layout.setSpacing(5)

            question_label = QLabel(key)
            question_label.setFixedHeight(25)
            line_edit = QLineEdit()
            combo_box = QComboBox()
            combo_box.addItems(value)

            answer_widget = QWidget()
            answer_layout = QHBoxLayout(answer_widget)
            answer_widget.setFixedHeight(45)

            answer_layout.addWidget(line_edit)
            answer_layout.addWidget(combo_box)

            input_layout.addWidget(question_label)

            # FIXME: replace with line_layout
            input_layout.addWidget(answer_widget)

            # input_layout.addWidget(line_edit)
            # input_layout.addWidget(combo_box)

            row_layout.addWidget(number_label)
            # row_layout.addWidget(combo_box)
            row_layout.addLayout(input_layout)

            # Wrap in widget and add to content
            row_widget = QWidget()
            row_widget.setFixedHeight(130)
            row_widget.setLayout(row_layout)
            content_layout.addWidget(row_widget)

        main_layout.addWidget(header2)
        main_layout.addWidget(content_widget)
        form_widget = QWidget()
        # form_widget.setFixedWidth()
        # form_widget.setLayout(form_layout)

        # scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(form_widget)
        scroll.setStyleSheet(
            """
    QScrollBar:vertical {
        width: 16px;
        background: #eee;
    }
    QScrollBar::handle:vertical {
        background: #999;
        border-radius: 6px;
    }
"""
        )

        # wrapper_form_layout.addWidget(scroll)
        # wrapper_form_widget = QWidget()
        # wrapper_form_widget.setLayout(wrapper_form_layout)
        # main_layout.addWidget(wrapper_form_widget)
        # main_layout.addWidget(scroll)

        self.setLayout(main_layout)

    def get_parameters(self):
        # test fonction to get parameters
        results = {}
        for key, (line_edit, combo_box) in self.parameters.items():
            results[key] = {"value": line_edit.text(), "unit": combo_box.currentText()}
        print(results)
        return results


class PageParametersComponent(QWidget):
    # TODO:
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        # self.components_layout = QVBoxLayout()
        self.components_widget = QWidget()
        # self.components_widget.setFixedSize(400, 300)  # width, height in pixels
        self.components_layout = QVBoxLayout(self.components_widget)
        self.add_component_button = QPushButton("Add Component")
        self.add_component_button.setFixedSize(100, 30)
        line_edit = QLineEdit()
        row_layout = QHBoxLayout()
        row_layout.addWidget(line_edit)
        row_widget = QWidget()
        row_widget.setLayout(row_layout)
        row_widget.setFixedSize(70, 40)
        # self.components_widget.setFixedSize(100, 100)
        self.components_layout.addWidget(row_widget)
        self.components_layout.setSpacing(1)  # Reduce space between items
        self.components_layout.setContentsMargins(0, 0, 0, 0)  # Remove outer margins
        self.components_layout.setAlignment(
            # keeps items on top
            Qt.AlignmentFlag.AlignTop
        )
        layout = QVBoxLayout()
        # layout.addWidget(QLabel("lfksd"))
        # layout.addLayout(self.components_layout)
        layout.addWidget(self.components_widget)
        # self.components_layout(self.add_component_button)
        self.components_layout.addWidget(self.add_component_button)
        self.components_widget.adjustSize()
        self.setLayout(layout)

    def add_component(self):
        line_edit = QLineEdit()
        # combo_box = QComboBox()
        # combo_box.addItems(["unit1", "unit2"])  # or dynamic units
        row_layout = QHBoxLayout()
        row_layout.addWidget(line_edit)
        # row_layout.addWidget(combo_box)
        row_widget = QWidget()
        row_widget.setLayout(row_layout)
        row_widget.setFixedSize(70, 40)
        self.components_layout.addWidget(row_widget)
        # row_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        row_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        # self.components.append((line_edit, combo_box))
