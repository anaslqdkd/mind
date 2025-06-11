import enum
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QStackedWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from app.param import Param, ParamBoolean, ParamBooleanWithInput, ParamBooleanWithInputWithUnity, ParamCategory, ParamComponent, ParamInput, ParamInputWithUnity, ParamSelect, ParamType

# TODO: same but for actual input types


class FILE(enum.Enum):
    CONFIG = enum.auto()
    DATA = enum.auto()
    PERM = enum.auto()
    ECO = enum.auto()
    COMMAND = enum.auto()
# TODO: for each param add a to_file method

# -----------------------------------------------------------

def create_param(name: str, param_type: ParamType) -> Param:
    match param_type:
        case ParamType.INPUT:
            return ParamInput(name)
        case ParamType.SELECT:
            return ParamSelect(name)
        case ParamType.BOOLEAN:
            return ParamBoolean(name)
        case ParamType.INPUT_WITH_UNITY:
            return ParamInputWithUnity(name)
        case ParamType.BOOLEAN_WITH_INPUT:
            return ParamBooleanWithInput(name)
        case ParamType.BOOLEAN_WITH_INPUT_WITH_UNITY:
            return ParamBooleanWithInputWithUnity(name)
        case ParamType.COMPONENT:
            return ParamComponent(name)
        case _:
            raise ValueError(f"Unsupported param type: {param_type}")

# -----------------------------------------------------------

# TODO: advanced button to unlock more "unusual" settings

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
        tab1_layout.addWidget(QLabel("Parameters"))
        tab2_layout = QVBoxLayout()
        tab2_layout.addWidget(QLabel("Versions"))
        self.tab2.setLayout(tab2_layout)

        self.tabs.addTab(self.tab1, "Parameters")
        self.tabs.addTab(self.tab2, "Versions")

        # pages
        param_page1 = self.set_param()
        self.page_components = PageParametersGlobal(self, param_page1)
        self.page1 = PageParametersGlobal(self, param_page1)

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

    def set_param(self):
        algo_params = {
            "Algorithm": 
                create_param(name="algorithm", param_type=ParamType.INPUT)
            ,
            "Another one": 
                create_param(name="idk", param_type=ParamType.INPUT)
            ,
            "Select test": 
                create_param(name="select", param_type=ParamType.SELECT)
            ,
            "Bool test": 
                create_param(name="check", param_type=ParamType.BOOLEAN)
            ,
            "Input with unity test": 
                create_param(name="input with unity", param_type=ParamType.INPUT_WITH_UNITY)
            ,
            "Boolean with input test": 
                create_param(name="boolean with input", param_type=ParamType.BOOLEAN_WITH_INPUT)
            ,
            "Boolean with input and unity": 
                create_param(name="boolean with input and unity", param_type=ParamType.BOOLEAN_WITH_INPUT_WITH_UNITY)
            ,
            "Component": 
                create_param(name="component test", param_type=ParamType.COMPONENT)
            ,
            "Another flds": 
                create_param(name="bu", param_type=ParamType.INPUT)
            ,
        }
        param = {
        }
        param_page1 = {"Algorithm parameters": algo_params,
                       "Other parameters": param}
        return param_page1


class PageParametersGlobal(QWidget):
    def __init__(
        self, main_window, param_category: dict["str", dict[str, Param]]
    ) -> None:
        super().__init__()
        self.main_window = main_window
        self.param_category = param_category

        main_layout = QVBoxLayout()

        content_layout = QVBoxLayout()
        content_widget = QWidget()
        content_widget.setLayout(content_layout)

        for key, value in param_category.items():
            ex_params = ParamCategory(key, value)
            for name, param in value.items():
                param.category = ex_params
            main_layout.addWidget(ex_params)

        main_layout.addStretch()

        self.setLayout(main_layout)

