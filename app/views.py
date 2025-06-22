from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QStackedWidget,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)
import configparser

from app.param import (
    GridOptions,
    InputValidation,
    MembraneOptions,
    Param,
    ParamCategory,
    debug_print,
)
from app.param_enums import FILE
from app.param_factory import set_dep, set_param
from app.param_factory import all_params
from app.param_validator import LineEditValidation, NonOptionalInputValidation

# TODO: close button verification before quitting, to abort modifs
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

        self.all_params: list[Param] = []

        self.pages: list[PageParameters] = []
        for key, items in all_params.items():
            params_page = set_param(items)
            self.pages.append(
                PageParameters(self, params_page, self.stack, self.sidebar)
            )
            for name, dict in params_page.items():
                for el, param in dict.items():
                    self.all_params.append(param)
        set_dep()

        self.main_area = QWidget()
        tab1_layout = QHBoxLayout(self.main_area)
        header = QLabel("Main Area Header")

        layout = QVBoxLayout()
        layout.addWidget(header)
        layout.addWidget(self.tabs)

        button = QPushButton("A propos")
        quit_button = QPushButton("Fermer")
        self.apply_button = QPushButton("Appliquer")

        end_buttons = QWidget()
        end_buttons_layout = QHBoxLayout(end_buttons)
        end_buttons_layout.addWidget(button)
        spacer = QSpacerItem(
            0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        end_buttons_layout.addSpacerItem(spacer)
        end_buttons_layout.addStretch()
        end_buttons_layout.addWidget(quit_button)

        layout.addWidget(end_buttons)
        tab1_layout.addWidget(self.sidebar)
        tab1_layout.addWidget(self.stack)
        tab1_layout.addStretch()

        self.command_builder = CommandBuilder(self.all_params)
        self.config_builder = ConfigBuilder(self.all_params)
        # command = builder.build_command()
        # print("the command is", command)

        for el in self.pages:
            self.stack.addWidget(el)

        self.sidebar.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.apply_button.clicked.connect(self.build_command)
        end_buttons_layout.addWidget(self.apply_button)

        self.tab1.setLayout(tab1_layout)
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def update_pages(self):
        for page in self.pages:
            page.update_param_page()

    def build_command(self):
        self.update_pages()
        command = self.command_builder.build_command()
        config = self.config_builder.build_config()
        debug_print("the command is", command)
        debug_print("the config is", config)


# -----------------------------------------------------------

# TODO: sidebar categories based on the dict pages name
# TODO: to_command for select, bool with input, spin box


class CommandBuilder:
    def __init__(self, params) -> None:
        self.params = params

    def build_command(self):
        args = [
            param.to_command_arg()
            for param in self.params
            if param.file == FILE.COMMAND
        ]
        return " ".join(arg for arg in args if arg)


class ConfigBuilder:
    def __init__(self, params) -> None:
        self.params = params

    def build_config(self):
        args = [
            param.to_config_entry()
            for param in self.params
            if param.file == FILE.CONFIG
        ]
        return " ".join(arg for arg in args if arg)


class PageParameters(QWidget):
    def __init__(
        self,
        main_window,
        param_category: dict["str", dict[str, Param]],
        stack: QStackedWidget,
        sidebar: QListWidget,
    ) -> None:
        super().__init__()
        self.main_window = main_window
        self.param_category = param_category
        self.stack = stack
        self.sidebar = sidebar
        self.sidebar.setCurrentRow(0)
        self.categories: list[ParamCategory] = []

        main_layout = QVBoxLayout()

        content_layout = QVBoxLayout()
        content_widget = QWidget()
        content_widget.setLayout(content_layout)

        tab1_widget = QWidget()
        # self.tab_widget.addTab(QWidget(), "Tab 2")
        tab1_layout = QVBoxLayout(tab1_widget)
        tab1_layout.setSpacing(0)

        for key, value in param_category.items():
            widget = ParamCategory(key, value)
            self.categories.append(widget)
            if key == "Advanced":
                section = CollapsibleSection("Advanced section")
                ex_params = ParamCategory("Title", value)
                section.addWidget(ex_params)
                widget = section
            else:
                for name, param in value.items():
                    param.category = widget
            tab1_layout.addWidget(widget)
        self.tab_widget = QTabWidget()
        self.tab_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.tab_widget.addTab(tab1_widget, "Tab 1")
        main_layout.addWidget(self.tab_widget, 1, Qt.AlignmentFlag.AlignTop)
        # main_layout.addWidget(self.tab_widget, stretch=1)
        # NOTE: here
        main_layout.addStretch()

        next_button = QPushButton("next")
        self.tab_widget.addTab(
            GridOptions(
                ["Molar Mass"],
                ["Component 1", "Component 2", "Component 3"],
            ),
            "Tab 2",
        )  # Placeholder for Tab 2

        end_button_widget = QWidget()
        end_button_layout = QHBoxLayout(end_button_widget)
        end_button_layout.addStretch()
        next_button.clicked.connect(self.go_to_next_page)
        end_button_layout.addWidget(next_button)
        main_layout.addWidget(end_button_widget)

        # main_layout.addWidget(MembraneOptions)
        main_layout.addStretch()

        self.setLayout(main_layout)

    def update_param_page(self):
        for category in self.categories:
            category.update_category()

    # TODO: move this to the validator class
    def go_to_next_page(self):
        # TODO: trigger errors for not optional values
        # if self.validate_required_params():
        # FIXME: restore when validate input works properly
        # and self.validate_all_input():

        current_index = self.sidebar.currentRow()
        count = self.sidebar.count()
        next_index = (current_index + 1) % count
        self.sidebar.setCurrentRow(next_index)
        # FIXME: same
        # elif not self.validate_all_input():
        #     QMessageBox.warning(
        #         self, "text" "Invalid Input", f"Please input the right values"
        #     )
        # else:
        #     # TODO: put in red all parameters that are non optional and not selected
        #     for category in self.param_category.values():
        #         for param in category.values():
        #             if isinstance(param, NonOptionalInputValidation):
        #                 if not param.is_filled():
        #                     line_edit = param.line_edit
        #                     if line_edit is not None:
        #                         line_edit.setStyleSheet("border: 1px solid red")
        #     QMessageBox.warning(
        #         self, "text" "Invalid Input", f"Please input all required forms"
        #     )

    def validate_required_params(self):
        for category in self.param_category.values():
            for param in category.values():
                if isinstance(param, NonOptionalInputValidation):
                    print("param is a instance of non optional input validation")
                    if not param.is_filled():
                        return False
        return True

    def validate_all_input(self):
        for category in self.param_category.values():
            for param in category.values():
                if isinstance(param, LineEditValidation):
                    print("param is a instance of non optional input validation")
                    text = param.line_edit.text()
                    print("the text in ", text)
                    if not param.validate_input(param.line_edit.text()):
                        print("2345678", param.name)
                        return False
        return True

        # if not getattr(param, "optional", False):
        #     # TODO: validate input (or another function that checks if there is input)
        #     # if has line input
        #     if hasattr(param, "line_edit"):
        #         # InputValidation.validate_input(param.line_edit, param.expected_type)
        #         InputValidation.check_required(
        #             param.name, param.line_edit, param.optional
        #         )


# -----------------------------------------------------------
class CollapsibleGroupBox(QGroupBox):
    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self.setCheckable(True)
        self.setChecked(False)  # Start collapsed
        self.toggled.connect(self.on_toggled)
        self.setStyleSheet("font-weight: bold;")
        self.setStyleSheet("QGroupBox { font-size: 12px; font-weight: bold; }")

        self.label = QLabel("the is a label")
        self.label.setVisible(False)
        layout = QVBoxLayout(self)
        layout.addWidget(self.label)

    def on_toggled(self, checked):
        for i in range(self.layout().count()):
            widget = self.layout().itemAt(i).widget()
            if widget:
                widget.setVisible(checked)
        self.adjustSize()
        self.updateGeometry()
        parent = self.parentWidget()
        if parent:
            parent.adjustSize()
            parent.updateGeometry()
            layout = parent.layout()
            if layout:
                layout.invalidate()
                layout.activate()


class CollapsibleSection(QWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.toggle_button = QPushButton("▶ " + title)
        font = self.toggle_button.font()
        font.setBold(True)
        self.toggle_button.setFont(font)
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(False)
        self.toggle_button.setStyleSheet("text-align: left; border: none;")
        self.toggle_button.clicked.connect(self.toggle)

        self.content_area = QFrame()
        self.content_area.setVisible(False)
        self.content_layout = QVBoxLayout(self.content_area)

        layout = QVBoxLayout(self)
        layout.addWidget(self.toggle_button)
        layout.addWidget(self.content_area)
        layout.setContentsMargins(0, 0, 0, 0)

    def toggle(self):
        checked = self.toggle_button.isChecked()
        if checked:
            self.toggle_button.setText("▼ " + self.toggle_button.text()[2:])
        else:
            self.toggle_button.setText("▶ " + self.toggle_button.text()[2:])
        self.content_area.setVisible(checked)

    def addWidget(self, widget):
        self.content_layout.addWidget(widget)


# NOTE: question sur le nombre d'iterations, dans commande ou config.ini
def load_configuration():
    tuning_params = [
        "seed1",
        "seed2",
        "iteration",
        "max_no_improve",
        "epsilon",
        "pressure_ratio",
        "max_trials",
        "pop_size",
        "generations",
        "n1_element",
    ]

    instance_params = [
        "fname",
        "fname_perm",
        "fname_eco",
        "num_membranes",
        "ub_area",
        "lb_area",
        "ub_acell",
        "vp",
        "uniform_pup",
        "variable_perm",
        "fixing_var",
    ]
    config = configparser.ConfigParser()
    try:
        config.read("data/config.ini")
        if not ("tuning" in config.sections() and "instance" in config.sections()):
            raise ValueError(
                f"Errror: config.ini is not set correctly, generate new one with option (--config)"
            )
        for param in tuning_params:
            if param not in config["tuning"]:
                raise ValueError(
                    f"Eroor: {param} not defined in config.ini (section: tuning)"
                )

        for param in instance_params:
            if param not in config["instance"]:
                raise ValueError(
                    f"Eroor: {param} not defined in config.ini (section: instance)"
                )
    except Exception as e:
        raise

    #  convert functions
    convert_list = lambda type_, table: [
        type_(x) for x in table[1 : len(table) - 1].split(", ")
    ]
    convert_dict = lambda type_, table: {
        x.split(":")[0][1 : len(x.split(":")[0]) - 1]: type_(x.split(":")[1])
        for x in table[1 : len(table) - 1].split(", ")
    }
    convert_bool = lambda name: (
        True if name in ["true", "True", "on", "ON", "yes", "YES"] else False
    )

    tuning = dict(config.items("tuning"))
    instance = dict(config.items("instance"))
    # convert instances
    # FIXME: replace with the actual parameters with param_registry["ub_area"]
    instance["ub_area"] = convert_list(float, instance["ub_area"])
    instance["lb_area"] = convert_list(float, instance["lb_area"])
    instance["ub_acell"] = convert_list(float, instance["ub_acell"])

    instance["vp"] = convert_bool(instance["vp"])
    instance["uniform_pup"] = convert_bool(instance["uniform_pup"])
    instance["variable_perm"] = convert_bool(instance["variable_perm"])
    instance["fixing_var"] = convert_bool(instance["fixing_var"])

    tuning["pressure_ratio"] = float(tuning["pressure_ratio"])
    tuning["epsilon"] = convert_dict(float, tuning["epsilon"])

    return tuning, instance
