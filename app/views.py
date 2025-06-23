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

from app import dependency_manager, param_dict
from app.param import (
    GridOptions,
    MembraneOptions,
    Param,
    ParamCategory,
    ParamFixedWithInput,
    ParamInput,
    debug_print,
)
from app.param_enums import FILE
from app.param_factory import set_param
from app.param_dict import params_dict
from app.dependency_manager import DependencyManager

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
        self.tab_param = QWidget()
        self.tab_versions = QWidget()

        tab_param_layout = QVBoxLayout()
        tab_versions_layout = QVBoxLayout()

        tab_param_layout.addWidget(QLabel("Parameters"))
        tab_versions_layout.addWidget(QLabel("Versions"))

        self.tabs.addTab(self.tab_param, "Parameters")
        self.tabs.addTab(self.tab_versions, "Versions")

        # sidebar
        self.sidebar = QListWidget()
        sidebar_widget = QWidget()
        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_layout.addWidget(self.sidebar)
        sidebar_layout.addStretch()

        self.all_params: list[Param] = []
        self.pages: list[PageParameters] = []

        self.main_area = QWidget()
        header = QLabel("Main Area Header")

        tab_param_layout = QHBoxLayout(self.main_area)

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
        tab_param_layout.addWidget(self.sidebar)
        tab_param_layout.addWidget(self.stack)
        tab_param_layout.addStretch()

        # FIXME: probably change the passed param
        # self.command_builder = CommandBuilder(self.all_params)
        # self.config_builder = ConfigBuilder(self.all_params)

        # add pages to the stack
        self._define_pages()
        self._init_pages()
        for el in self.pages:
            self.stack.addWidget(el)

        self._set_dependencies()
        self.sidebar.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.apply_button.clicked.connect(self.build_command)
        end_buttons_layout.addWidget(self.apply_button)

        self.tab_param.setLayout(tab_param_layout)
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    # TODO: add spin_box everywhere

    def _define_pages(self):
        self.pages_names = {
            "Page 1": ["General"],
            "Page 2": ["Membranes"],
            "Page 3": ["Data"],
            "Page 4": ["Data2"],
            "Page 5": ["Perm"],
            "Page 6": ["Eco"],
            "Page 7": ["Eco2"],
        }

        self.categories_names = {
            "General": [
                "verbose",
                "debug",
                "solver",
                "gams",
                "maxiter",
                "maxtime",
                "algorithm",
                "no_starting_point",
                "no_simplified_model",
                "pop_size",
                "visualise",
                "opex",
                "capex",
                "save_log_sol",
            ],
            "Membranes": [
                "num_membranes",
                "ub_area",
                "lb_area",
                "ub_acell",
                "fixing_var",
                "uniform_pup",
                "vp",
                "variable_perm",
                "iteration",
                "max_no_improve",
                "max_trials",
                "pressure_ratio",
                "pop_size",
                "generations",
            ],
            "Data": [
                "set components",
                "param xin",
                "param molarmass",
                "param pressure_in",
                "param lb_perc_prod",
                "param lb_perc_waste",
                "param FEED",
                "param normalized_product_qt",
                "param final_product",
                "param ub_press_down",
                "param lb_press_down",
                "param ub_press_up",
            ],
            "Data2": [
                "param pressure_prod",
                "param lb_press_down",
                "param ub_feed",
                "param ub_out_prod",
                "param ub_out_waste",
                "param ub_feed",
                "param tol_zero",
                "param n",
                "states",
            ],
            "Perm": [
                "set mem_types_set",
                "param nb_gas",
                "param Permeability",
                "param thickness",
                "param mem_product",
                "alpha",
                "perm_ref",
            ],
            "Eco": [
                "param R",
                "param phi",
                "param T",
                "param gamma",
                "param C_cp",
                "param C_exp",
                "param C_vp",
                "param eta_cp",
                "param K_mr",
                "param K_gp",
                "param K_m",
                "param K_mf",
                "param K_el",
                "param K_er",
                "param t_op",
            ],
            "Eco2": [
                "param MFc",
                "param nu",
                "param UF_1968",
                "param MPFc",
                "param i",
                "param i",
                "param z",
                "param eta_vp_1",
            ],
        }

    def _init_pages(self):
        self.param_registry = set_param(params_dict)
        self.category_params = {
            cat: [self.param_registry[name] for name in names]
            for cat, names in self.categories_names.items()
        }

        self.category_instances = {}
        for key, list_param in self.category_params.items():
            temp_category = ParamCategory(key, list_param)
            self.category_instances[key] = temp_category

        for page, category_name_list in self.pages_names.items():
            self.sidebar.addItem(page)
            page_categories = []
            for el in category_name_list:
                page_categories.append(self.category_instances[el])
            page_temp = PageParameters(self, page_categories, self.stack, self.sidebar)
            self.pages.append(page_temp)
        pass

    def _set_dependencies(self):
        dependency_manager = DependencyManager()
        for param in self.param_registry.values():
            param.manager = dependency_manager

        def register_param_dependencies(param_registry, dependency_manager):
            dependency_manager.add_dependency(
                param_registry["num_membranes"],
                param_registry["ub_area"],
                self.update_fn,
            )
            dependency_manager.add_dependency(
                param_registry["num_membranes"],
                param_registry["lb_area"],
                self.update_fn,
            )
        register_param_dependencies(self.param_registry, dependency_manager)

    def update_fn(self, target: ParamFixedWithInput, source: ParamInput):
        debug_print(f"the source is {source.name} and the target is {target.name}")
        target.set_rows_nb(int(source.get_value()))
        target.category.update_category()
        debug_print("in the update fn fucntion")


    def update_pages(self):
        for page in self.pages:
            page.update_param_page()

    def build_command(self):
        self.update_pages()
        # command = self.command_builder.build_command()
        # config = self.config_builder.build_config()
        # debug_print("the command is", command)
        # debug_print("the config is", config)


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
        param_category: list[ParamCategory],
        stack: QStackedWidget,
        sidebar: QListWidget,
    ) -> None:
        super().__init__()
        self.main_window = main_window
        # self.param_category = param_category
        self.stack = stack
        self.sidebar = sidebar
        self.sidebar.setCurrentRow(0)
        self.categories: list[ParamCategory] = []

        main_layout = QVBoxLayout()

        content_layout = QVBoxLayout()
        content_widget = QWidget()
        content_widget.setLayout(content_layout)

        tab1_widget = QWidget()
        tab1_layout = QVBoxLayout(tab1_widget)
        tab1_layout.setSpacing(0)

        for el in param_category:
            tab1_layout.addWidget(el)

        self.tab_widget = QTabWidget()
        self.tab_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.tab_widget.addTab(tab1_widget, "Tab 1")
        main_layout.addWidget(self.tab_widget, 1, Qt.AlignmentFlag.AlignTop)
        main_layout.addStretch()

        next_button = QPushButton("next")

        end_button_widget = QWidget()
        end_button_layout = QHBoxLayout(end_button_widget)
        end_button_layout.addStretch()
        next_button.clicked.connect(self.go_to_next_page)
        end_button_layout.addWidget(next_button)
        main_layout.addWidget(end_button_widget)

        main_layout.addStretch()

        self.setLayout(main_layout)

    def update_param_page(self):
        for category in self.categories:
            category.update_category()

    def go_to_next_page(self):
        current_index = self.sidebar.currentRow()
        count = self.sidebar.count()
        next_index = (current_index + 1) % count
        self.sidebar.setCurrentRow(next_index)


# -----------------------------------------------------------
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

# -----------------------------------------------------------

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
