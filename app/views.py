import enum
from typing import Optional
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

# TODO: same but for actual input types


class ParamType(enum.Enum):
    INPUT = enum.auto()  # seulement de l'input
    INPUT_WITH_UNITY = enum.auto()  # parametre avec unité dans un menu deroulant
    BOOLEAN = enum.auto()  # checkbox
    SELECT = enum.auto()  # menu deroulable
    BOOLEAN_WITH_INPUT = enum.auto()  # maxiteration
    BOOLEAN_WITH_INPUT_WITH_UNITY = enum.auto()  # pour maxtime


class Param:
    def __init__(
        self, name: str, type: ParamType, values: Optional[list[str]] = None
    ) -> None:
        self.name = name
        self.type = type
        self.values = values or []


class ParamCategory(QWidget):
    def __init__(self, name: str, param: dict["str", Param]) -> None:
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.param = param

        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.label = QLabel(f"{name}")
        self.label.setStyleSheet(
            """
            font-weight: bold;
            font-size: 14px;
            color: #000;
"""
        )
        layout.addWidget(self.label)
        layout.addWidget(self.grid_widget)
        self.build_param()

    def build_param(self) -> QWidget:
        row = 0
        for label, param_obj in self.param.items():
            match param_obj.type:
                case ParamType.INPUT:
                    self.add_param_input(row, label, param_obj)
                    row += 1
                case ParamType.INPUT_WITH_UNITY:
                    self.add_param_input_with_unity(row, label, param_obj)
                    row += 1
                    pass
                case ParamType.BOOLEAN:
                    self.add_param_boolean(row, label, param_obj)
                    row += 1
                case ParamType.SELECT:
                    self.add_param_select(row, label, param_obj)
                    row += 1
                    # pass
                case ParamType.BOOLEAN_WITH_INPUT:
                    self.add_param_boolean_with_input(row, label, param_obj)
                    row += 2
                    pass
                case ParamType.BOOLEAN_WITH_INPUT_WITH_UNITY:
                    self.add_param_boolean_with_input_with_unity(row, label, param_obj)
                    row += 2

        return self

    def add_param_input(self, row: int, label: str, param_obj: Param):
        question_label = QLabel(label)
        line_edit = QLineEdit()
        self.grid_layout.addWidget(question_label, row, 0)
        self.grid_layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum),
            row,
            1,
        )
        self.grid_layout.addWidget(line_edit, row, 2)

    def add_param_input_with_unity(self, row: int, label: str, param_obj: Param):
        question_label = QLabel(label)
        line_edit = QLineEdit()
        combo_box = QComboBox()
        combo_box.addItems(param_obj.values)
        # self.grid_layout.addWidget(question_label, row, 0)
        # self.grid_layout.addWidget(line_edit, row, 1)
        # self.grid_layout.addWidget(combo_box, row, 2)
        self.grid_layout.addWidget(question_label, row, 0)
        self.grid_layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum),
            row,
            1,
        )
        self.grid_layout.addWidget(line_edit, row, 2)
        self.grid_layout.addWidget(combo_box, row, 3)

    def add_param_boolean(self, row: int, label: str, param_obj: Param):
        container = QWidget()
        h_layout = QHBoxLayout(container)
        h_layout.setContentsMargins(0, 0, 0, 0)  # remove margins for tighter layout
        # h_layout.setSpacing(5)  # optional: tweak spacing between checkbox and label

        check_box = QCheckBox()
        question_label = QLabel(label)

        h_layout.addWidget(check_box)
        h_layout.addWidget(question_label)
        h_layout.addStretch()

        self.grid_layout.addWidget(container, row, 0, 1, 2)  # span 2 columns if needed

    def add_param_boolean_with_input(self, row: int, label: str, param_obj: Param):
        checkbox_container = QWidget()
        checkbox_layout = QHBoxLayout(checkbox_container)
        checkbox_layout.setContentsMargins(0, 0, 0, 0)
        checkbox_layout.setSpacing(5)

        check_box = QCheckBox()
        question_label = QLabel(label)

        checkbox_layout.addWidget(check_box)
        checkbox_layout.addWidget(question_label)
        checkbox_layout.addStretch()

        self.grid_layout.addWidget(checkbox_container, row, 0, 1, 2)

        # Second row: Label + input field
        t_label = QLabel(label)
        line_edit = QLineEdit()
        line_edit.setEnabled(False)
        check_box.toggled.connect(line_edit.setEnabled)

        self.grid_layout.addWidget(t_label, row + 1, 0)
        spacer = QWidget()
        self.grid_layout.addWidget(spacer, row + 1, 1)
        self.grid_layout.addWidget(line_edit, row + 1, 2)

    def add_param_boolean_with_input_with_unity(
        self, row: int, label: str, param_obj: Param
    ):
        checkbox_container = QWidget()
        checkbox_layout = QHBoxLayout(checkbox_container)
        checkbox_layout.setContentsMargins(0, 0, 0, 0)
        checkbox_layout.setSpacing(5)

        check_box = QCheckBox()
        question_label = QLabel(label)

        combo_box = QComboBox()
        combo_box.addItems(param_obj.values)

        checkbox_layout.addWidget(check_box)
        checkbox_layout.addWidget(question_label)
        checkbox_layout.addStretch()

        self.grid_layout.addWidget(checkbox_container, row, 0, 1, 2)

        # Second row: Label + input field
        t_label = QLabel(label)
        line_edit = QLineEdit()
        line_edit.setEnabled(False)
        check_box.toggled.connect(line_edit.setEnabled)

        self.grid_layout.addWidget(t_label, row + 1, 0)
        spacer = QWidget()
        self.grid_layout.addWidget(spacer, row + 1, 1)
        self.grid_layout.addWidget(line_edit, row + 1, 2)
        self.grid_layout.addWidget(combo_box)

    def add_param_select(self, row: int, label: str, param_obj: Param):
        question_label = QLabel(label)
        combo_box = QComboBox()
        combo_box.addItems(param_obj.values)
        combo_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.grid_layout.addWidget(question_label, row, 0)

        # Spacer to push the combo box to the right
        spacer = QSpacerItem(
            0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        self.grid_layout.addItem(spacer, row, 1)

        # self.grid_layout.addWidget(combo_box, row, 2)
        # TODO: same for the other menus
        self.grid_layout.addWidget(combo_box, row, 2, 1, 2)


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
        tab1_layout = QHBoxLayout(self.main_area)
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
        tab1_layout.addWidget(self.sidebar)
        tab1_layout.addWidget(self.page1)
        tab1_layout.addWidget(self.stack)
        tab1_layout.addStretch()

        self.stack.addWidget(self.page1)
        self.stack.addWidget(self.page_components)
        self.sidebar.currentRowChanged.connect(self.stack.setCurrentIndex)

        self.tab1.setLayout(tab1_layout)
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)


params = {
    "Generate starting point": Param(name="starting_point", type=ParamType.BOOLEAN),
    "Pressure": Param(
        name="pressure_in", type=ParamType.INPUT_WITH_UNITY, values=["bar", "kPa", "Pa"]
    ),
    "Use simplified model": Param(name="simplified_model", type=ParamType.BOOLEAN),
    "Algorithm": Param(
        name="Algorithm",
        type=ParamType.SELECT,
        values=["multistart", "mbh", "global", "genetic", "population"],
    ),
    "Set max time": Param(
        name="max_time",
        type=ParamType.BOOLEAN_WITH_INPUT_WITH_UNITY,
        values=["s", "h", "ms", "days"],
    ),
    "Set max iterations": Param(
        name="max_iterations", type=ParamType.BOOLEAN_WITH_INPUT
    ),
    "Pressure ratio": Param(
        name="pressure_ratio",
        type=ParamType.INPUT,
        # values=["s", "h", "ms", "days"],
    ),
}

param = {
    "Alpha": Param(
        name="Alpha", type=ParamType.BOOLEAN_WITH_INPUT, values=["bar", "kPa", "Pa"]
    )
}


class Parameter:
    def __init__(self, name: str, measure: list[str]) -> None:
        self.name = name
        self.measure = measure


class PageParametersGlobal(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.parameters = {}

        main_layout = QVBoxLayout()

        content_layout = QVBoxLayout()
        content_widget = QWidget()
        content_widget.setLayout(content_layout)

        category_widget = QWidget()
        category_layout = QVBoxLayout(category_widget)
        category_label = QLabel("Smaller category")
        category_label.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed
        )
        category_layout.addWidget(category_label)

        ex_params = ParamCategory("Algorithm parameters", params)
        main_layout.addWidget(ex_params)

        ex_params1 = ParamCategory("Second category", param)
        main_layout.addWidget(ex_params1)

        # NOTE: à remettre si jamais
        # group_box = QGroupBox("Global Settings")
        # group_box.setLayout(category_layout)
        # main_layout.addWidget(group_box)

        main_layout.addWidget(category_widget)
        category_layout.addStretch()

        self.setLayout(main_layout)

    def get_parameters(self):
        # test fonction to get parameters
        results = {}
        for key, (line_edit, combo_box) in self.parameters.items():
            results[key] = {"value": line_edit.text(), "unit": combo_box.currentText()}
        print(results)
        return results


class PageParametersComponent(QWidget):
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
