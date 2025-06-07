from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
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
    QSpacerItem,
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
        self.resize(800, 600)

        # stack
        self.stack = QStackedWidget()

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

        # pages
        self.page1 = PageParametersGlobal(self)
        self.page_components = PageParametersComponent(self)

        self.main_area = QWidget()
        main_area_layout = QHBoxLayout(self.main_area)
        header = QLabel("Main Area Header")

        # sidebar
        self.sidebar = QListWidget()
        self.sidebar.addItems(
            [
                "Global Parameters",
                "Components",
                "Membrane/Permeability",
                "Operational Constraints",
                "Fixed variables",
            ]
        )
        sidebar_layout = QVBoxLayout()
        sidebar_layout.addWidget(self.sidebar)
        sidebar_layout.addStretch()
        sidebar_widget = QWidget()
        sidebar_widget.setLayout(sidebar_layout)

        layout = QVBoxLayout()
        layout.addWidget(header)
        layout.addWidget(self.tabs)

        button = QPushButton("A propos")
        quit_button = QPushButton("Fermer")
        apply_button = QPushButton("Appliquer")

        end_buttons = QWidget()
        end_buttons_layout = QHBoxLayout(end_buttons)
        end_buttons_layout.addWidget(button)
        spacer = QSpacerItem(
            0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        end_buttons_layout.addSpacerItem(spacer)
        end_buttons_layout.addStretch()
        end_buttons_layout.addWidget(quit_button)
        end_buttons_layout.addWidget(apply_button)

        layout.addWidget(end_buttons)
        main_area_layout.addWidget(self.sidebar)
        main_area_layout.addWidget(self.page1)
        main_area_layout.addStretch()

        self.tab1.setLayout(main_area_layout)
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)


global_params = {
    # TODO: add the general algo params
    "pressure_in": ["bar", "Pa", "kPa"],
    "pressure_out": ["bar", "Pa", "kPa"],
    "f2ed a fost odata ": ["mol/s"],
    "f3ed do not": ["mol/s"],
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
        main_layout = QVBoxLayout()

        content_layout = QVBoxLayout()
        content_widget = QWidget()
        content_widget.setLayout(content_layout)

        # scroll area
        scroll_area = QScrollArea()
        # scroll_area.setWidget(content_widget)

        category_widget = QWidget()
        category_layout = QVBoxLayout(category_widget)
        category_label = QLabel("Smaller category")
        category_label.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed
        )
        category_layout.addWidget(category_label)

        container_widget = QWidget()
        grid_layout = QGridLayout(container_widget)
        # grid_layout.setHorizontalSpacing(10)
        # grid_layout.setVerticalSpacing(8)
        # grid_layout.setContentsMargins(0, 0, 0, 0)

        form_layout = QFormLayout()
        # parameters

        for i, (key, value) in enumerate(global_params.items(), start=0):
            question_label = QLabel(key)
            line_edit = QLineEdit()
            combo_box = QComboBox()
            combo_box.addItems(value)

            grid_layout.addWidget(question_label, i, 0)
            grid_layout.addWidget(line_edit, i, 1)
            grid_layout.addWidget(combo_box, i, 2)

        combo_box = QComboBox()
        combo_box.addItems(["ls", "ldkf", "ldk"])
        grid_layout.addWidget(QLabel("flksdj:"))
        grid_layout.addWidget(combo_box, i + 1, 1, 1, 2)

        check_box = QCheckBox()
        grid_layout.addWidget(check_box)
        grid_layout.addWidget(QLabel("label for the checkbox"))

        category_layout.addWidget(container_widget)
        category_layout.addWidget(QLabel("Activate verification"))

        # group_box = QGroupBox("Category 1")
        # group_box.setLayout(grid_layout)
        # main_layout.addWidget(group_box)

        check_widget = QWidget()
        check_grid = QGridLayout(check_widget)
        check_box = QCheckBox()
        # check_grid.addWidget(check_box)
        check_grid_label = QLabel("Activate verification:")
        # category_label.setSizePolicy(
        #     QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed
        # )
        # check_grid.addWidget(check_grid_label)
        # check_grid.addWidget(check_box, 0, 1, 1, 2)

        check_grid.addWidget(check_box, 0, 0)  # Checkbox in column 0
        check_grid.addWidget(check_grid_label, 0, 1)
        check_grid.setAlignment(Qt.AlignmentFlag.AlignLeft)

        category_layout.addWidget(check_widget)

        # NOTE: à remettre si jamais
        # group_box = QGroupBox("Global Settings")
        # group_box.setLayout(category_layout)
        # main_layout.addWidget(group_box)

        main_layout.addWidget(category_widget)

        form_widget = QWidget()
        category_layout.addStretch()

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
        # self.add_component_button.setFixedSize(100, 30)
        line_edit = QLineEdit()
        row_layout = QHBoxLayout()
        row_layout.addWidget(line_edit)
        row_widget = QWidget()
        row_widget.setLayout(row_layout)
        # row_widget.setFixedSize(70, 40)
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
        # row_widget.setFixedSize(70, 40)
        self.components_layout.addWidget(row_widget)
        # row_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        row_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        # self.components.append((line_edit, combo_box))
