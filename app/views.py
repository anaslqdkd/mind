import os
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
    QScrollArea,
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
    ParamBoolean,
    ParamCategory,
    ParamComponent,
    ParamComponentSelector,
    ParamFileChooser,
    ParamFixedWithInput,
    ParamInput,
    ParamSelect,
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
        self.resize(700, 600)

        # stack
        self.stack = QStackedWidget()

        # tabs
        self.tabs = QTabWidget()
        self.tab_param = QWidget()
        self.tab_versions = QWidget()
        self.tab_buttons = QWidget()
        self.param_registry: dict[str, Param] = {}

        tab_param_layout = QVBoxLayout()
        tab_versions_layout = QVBoxLayout()
        tab_buttons_layout = QVBoxLayout()

        tab_param_layout.addWidget(QLabel("Parameters"))
        tab_versions_layout.addWidget(QLabel("Versions"))

        self.tabs.addTab(self.tab_param, "Parameters")
        self.tabs.addTab(self.tab_versions, "Versions")
        self.tabs.addTab(self.tab_buttons, "Importer")

        # sidebar
        self.sidebar = QListWidget()
        sidebar_widget = QWidget()
        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_layout.addWidget(self.sidebar)
        sidebar_layout.addStretch()

        # tab importer
        import_config_button = QPushButton("Import config")
        import_config_button.setFixedSize(100, 30)
        import_perm_button = QPushButton("Import perm")
        import_perm_button.setFixedSize(100, 30)
        import_eco_button = QPushButton("Import eco")
        import_eco_button.setFixedSize(100, 30)
        tab_buttons_layout.addWidget(import_config_button)
        tab_buttons_layout.addWidget(import_perm_button)
        tab_buttons_layout.addWidget(import_eco_button)
        import_config_button.clicked.connect(self.load_config)
        import_perm_button.clicked.connect(self.load_perm)
        import_eco_button.clicked.connect(self.load_eco)
        self.tab_buttons.setLayout(tab_buttons_layout)

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
        # self.config_builder = ConfigBuilder(self.all_params)

        # add pages to the stack
        self._define_pages()
        self._init_pages()
        self._build_builders()
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
    def load_config(self):
        tuning, instance = load_configuration()
        for el, value in tuning.items():
            if el in self.param_registry.keys():
                self.param_registry[el].set_value(int(value))

        # TODO: manage all other params

        for el, value in instance.items():
            if el in self.param_registry.keys():
                if isinstance(self.param_registry[el], ParamBoolean):
                    self.param_registry[el].set_value(bool(value))
                if isinstance(self.param_registry[el], ParamInput):
                    self.param_registry[el].set_value(int(value))

                pass

    def load_perm(self):
        res = {}
        filepath = "data/example_perm.dat"
        with open(filepath, "r") as file:
            # TODO: see the diff between fixed and variable parser for perm
            perm_param = parser_fixed_permeability_data_simple(file)
            # perm_param = parser_fixed_permeability_data(file, res)
        # for key, value in perm_param.items():
        #     debug_print(f"the key is {key}, and the value is {value}")
        #     for attr_, value_ in vars(value).items():
        #         if type(value_) == list:
        #             for el in value_:
        #                 if isinstance(el, GasItemPerm):
        #                     debug_print(f"component item {attr_}", el)
        #             debug_print("component item", value_)

    def load_eco(self):
        res = load_coef("data/example_eco.dat")
        for el, value in res.items():
            if f"param {el}" in self.param_registry.keys():
                self.param_registry[f"param {el}"].set_value(value)

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
                # "visualise",
                # "opex",
                # "capex",
                "save_log_sol",
            ],
            "Surfaces": ["num_membranes", "ub_area", "lb_area", "ub_acell"],
            "Membranes": [
                # "num_membranes",
                # "ub_area",
                # "lb_area",
                # "ub_acell",
                "fixing_var",
                "uniform_pup",
                "vp",
                "variable_perm",
                "pressure_ratio",
                "iteration",
                "max_no_improve",
                "max_trials",
                "pop_size",
                "seed1",
                "seed2",
                "prototype_data",
                "generations",
                "n1_element",
                "fname_mask",
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
                # "param nb_gas",
                "param Permeability",
                "param thickness",
                "param mem_product",
                "param mem_type",
                "alpha",
                # "perm_ref",
            ],
            "Perm2": [
                    "param Robeson_multi",
                    "param Robeson_power",
                    "param alpha_ub_bounds",
                    "param alpha_lb_bounds",
                    "param lb_permeability",
                    "param ub_permeability",
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
                "param UF_2000",
                "param MPFc",
                "param i",
                "param i",
                "param z",
                "param eta_vp_1",
                "param eta_vp_0",
            ],
        }

    def _build_builders(self):
        self.command_builder = CommandBuilder(self.param_registry)
        self.config_builder = ConfigBuilder(self.param_registry)
        self.data_builder = DataBuilder(self.param_registry)
        self.eco_builder = EcoBuilder(self.param_registry)

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

        self.tab_categories = {
            "Tab 1": [self.category_instances["General"]],
            "Tab a": [self.category_instances["Surfaces"]],
            "Tab 2": [self.category_instances["Membranes"]],
            "Tab 3": [self.category_instances["Data"]],
            "Tab 4": [self.category_instances["Data2"]],
            "Tab 5": [self.category_instances["Perm"]],
            "Tab b": [self.category_instances["Perm2"]],
            "Tab 6": [self.category_instances["Eco"]],
            "Tab 7": [self.category_instances["Eco2"]],
        }
        self.tabs_names = {
            "Page 1": ["Tab 1"],
            "Page 2": ["Tab 2", "Tab a"],
            "Page 3": ["Tab 3"],
            "Page 4": ["Tab 4"],
            "Page 5": ["Tab b"],
            "Page 6": ["Tab 6", "Tab 7"],
        }
        for page, tab_list in self.tabs_names.items():
            self.sidebar.addItem(page)
            page_tabs_categories = self.tab_categories
            page_temp = PageParameters(
                self, self.stack, self.sidebar, tab_list, page_tabs_categories
            )
            self.pages.append(page_temp)

        pass

    def _set_dependencies(self):
        dependency_manager = DependencyManager()
        for param in self.param_registry.values():
            param.manager = dependency_manager

        def register_param_dependencies(param_registry, dependency_manager):
            dependency_manager.add_dependency(
                param_registry["num_membranes"],
                # ub_area depends on num_mebranes
                param_registry["ub_area"],
                self.update_fn,
            )
            dependency_manager.add_dependency(
                param_registry["num_membranes"],
                param_registry["lb_area"],
                self.update_fn,
            )
            dependency_manager.add_dependency(
                param_registry["num_membranes"],
                param_registry["ub_acell"],
                self.update_fn,
            )
            dependency_manager.add_dependency(
                param_registry["set components"],
                param_registry["param Permeability"],
                self.update_permeability2,
            )
            dependency_manager.add_dependency(
                param_registry["set mem_types_set"],
                param_registry["param Permeability"],
                self.update_permeability2,
            )
            dependency_manager.add_dependency(
                param_registry["set mem_types_set"],
                param_registry["param thickness"],
                self.update_permeability,
            )
            dependency_manager.add_dependency(
                param_registry["set components"],
                param_registry["param mem_type"],
                self.update_permeability,
            )
            dependency_manager.add_dependency(
                param_registry["set mem_types_set"],
                param_registry["param mem_product"],
                self.update_permeability,
            )
            dependency_manager.add_dependency(
                param_registry["set components"],
                param_registry["param xin"],
                self.update_permeability,
            )
            dependency_manager.add_dependency(
                param_registry["set components"],
                param_registry["param molarmass"],
                self.update_permeability,
            )
            dependency_manager.add_dependency(
                param_registry["set components"],
                param_registry["param lb_perc_prod"],
                self.update_permeability,
            )
            dependency_manager.add_dependency(
                param_registry["set components"],
                param_registry["param lb_perc_prod"],
                self.update_permeability,
            )
            dependency_manager.add_dependency(
                param_registry["algorithm"],
                param_registry["generations"],
                self.update_generations,
            )
            dependency_manager.add_dependency(
                param_registry["algorithm"],
                param_registry["generations"],
                self.update_generations,
            )
            dependency_manager.add_dependency(
                param_registry["algorithm"],
                param_registry["generations"],
                self.update_config_algo_params,
            )
            dependency_manager.add_dependency(
                param_registry["set components"],
                param_registry["param final_product"],
                self.update_final_product,
            )
            dependency_manager.add_dependency(
                param_registry["fixing_var"],
                param_registry["fname_mask"],
                self.update_fixing,
            )

        register_param_dependencies(self.param_registry, dependency_manager)

    def update_final_product(self, target: ParamSelect, source: ParamComponentSelector):
        target.set_values(source.selected_components)

    def update_permeability(self, target: ParamFixedWithInput, source: ParamComponent):
        target.set_rows(int(source.get_value()), source)
        target.category.update_category()

    def update_permeability2(
        self, target: ParamFixedWithInput, source: ParamComponentSelector
    ):
        target.set_rows_nb(int(source.get_value()), source)
        target.category.update_category()

    def update_fn(self, target: ParamFixedWithInput, source: ParamInput):
        target.set_row(int(float(source.get_value())))
        # target.set_row(int(source.get_value()))
        target.category.update_category()

    def update_pages(self):
        for page in self.pages:
            page.update_param_page()

    def update_generations(self, target: Param, source: Param):
        if source.last_combo_box != "genetic":
            target.hide()
        else:
            target.show()
        target.category.update_category()

    def update_fixing(self, target: ParamFileChooser, source: ParamBoolean):
        if source.last_check_box:
            target.show()
            target.category.update_category()
        else:
            target.hide()
            target.category.update_category()

    def update_config_algo_params(self, target: ParamInput, source: ParamSelect):
        var_params = [
            "iteration",
            "seed1",
            "max_trials",
            "max_no_improve",
            "seed2",
            "pop_size",
            "generations",
            "prototype_data",
            "n1_element",
        ]
        shown_params = set()
        if source.last_combo_box == "multistart":
            for param_name in ["iteration", "seed1"]:
                param = self.param_registry.get(param_name)
                if param:
                    param.show()
                    shown_params.add(param_name)
                    param.category.update_category()
        if source.last_combo_box == "mbh":
            for param_name in ["max_trials", "max_no_improve", "seed1", "seed2"]:
                param = self.param_registry.get(param_name)
                if param:
                    shown_params.add(param_name)
                    param.show()
                    # if hasattr(param, "category") and param.category:
                    param.category.update_category()
        if source.last_combo_box == "global_opt":
            for param_name in [
                "max_trials",
                "max_no_improve",
                "iteration",
                "seed1",
                "seed2",
            ]:
                param = self.param_registry.get(param_name)
                if param:
                    shown_params.add(param_name)
                    param.show()
                    param.category.update_category()
        if source.last_combo_box == "population":
            for param_name in ["prototype_data", "n1_element"]:
                param = self.param_registry.get(param_name)
                if param:
                    shown_params.add(param_name)
                    param.show()
                    param.category.update_category()
        if source.last_combo_box == "genetic":
            for param_name in ["pop_size", "generations"]:
                param = self.param_registry.get(param_name)
                if param:
                    shown_params.add(param_name)
                    param.show()
                    param.category.update_category()
        for param_name in var_params:
            if param_name not in shown_params:
                param = self.param_registry.get(param_name)
                if param:
                    param.hide()
                    param.category.update_category()

    # FIXME: hide all other params

    def build_command(self):
        self.update_pages()
        command = self.command_builder.build_command()
        config = self.config_builder.build_config()
        data = self.data_builder.build_data()
        eco = self.eco_builder.build_eco()
        debug_print("the command is", command)
        debug_print("the config is", config)
        debug_print("the config is", data)
        debug_print("the config is", eco)


# -----------------------------------------------------------

# TODO: sidebar categories based on the dict pages name
# TODO: to_command for select, bool with input, spin box


class CommandBuilder:
    def __init__(self, param_registry: dict[str, Param]) -> None:
        self.param_registry = param_registry

        # for reference
        self.validated_params = [
            "verbose",
            "debug",
            "config",
            "exec",
            "no_starting_point",
            "no_simplified_model",
            "gams",
            "solver",
            "maxiter",
            "maxtime",
            "algorithm",
            "instance",
            "visualise",
            "opex",
            "capex",
            "save_log_sol",
            "version",
        ]

    def build_command(self):
        args = []
        for param_name in self.validated_params:
            if param_name in self.param_registry:
                param = self.param_registry[param_name]
                if hasattr(param, "file") and param.file == FILE.COMMAND:
                    arg = param.to_command_arg()
                    if arg:
                        args.append(arg)
        return " ".join(args)


class ConfigBuilder:
    def __init__(self, params) -> None:
        self.param_registry = params
        self.tuning_params = [
            "pressure_ratio",
            "epsilon",
            "seed1",
            "seed2",
            "iteration",
            "max_no_improve",
            "max_trials",
            "pop_size",
            "generations",
            "n1_element",
        ]
        self.instance_params = [
            "data_dir",
            "log_dir",
            "num_membranes",
            "ub_area",
            "lb_area",
            "ub_acell",
            "fixing_var",
            "fname",
            "fname_perm",
            "fname_eco",
            "uniform_pup",
            "prototype_data",
            "vp",
            "variable_perm",
            "fname_mask",
        ]
        self.config_args = {}

    def build_config(self):
        self.config_args = {"tuning": [], "instance": []}
        for param_name in self.tuning_params:
            if param_name in self.param_registry.keys():
                param = self.param_registry[param_name]
                if param.file == FILE.CONFIG:
                    arg = param.to_config_entry()
                    if arg is not None:
                        self.config_args["tuning"].append(arg)
        for param_name in self.instance_params:
            if param_name in self.param_registry.keys():
                param = self.param_registry[param_name]
                if param.file == FILE.CONFIG:
                    arg = param.to_config_entry()
                    if arg is not None:
                        self.config_args["instance"].append(arg)
        debug_print(self.config_args)
        self.write_config_ini()

    def write_config_ini(self, filename="test/config.ini"):
        dir_path = os.path.dirname(filename)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        config = configparser.ConfigParser()
        config["tuning"] = {}
        config["instance"] = {}

        for entry in self.config_args.get("tuning", []):
            key, value = entry.split("=", 1)
            config["tuning"][key.strip()] = value.strip()
        for entry in self.config_args.get("instance", []):
            key, value = entry.split("=", 1)
            config["instance"][key.strip()] = value.strip()

        with open(filename, "w") as configfile:
            config.write(configfile)


class DataBuilder:
    # TODO: add to_data_entry for param fixed with input
    def __init__(self, params) -> None:
        self.param_registry = params
        self.validated_params = [
            "set components",
            "param ub_perc_waste",
            "param lb_perc_prod",
            "param normalized_product_qt",
            "param final_product",
            "param FEED",
            "param XIN",
            "param molarmass",
            "param ub_press_down",
            "param lb_press_down",
            "param lb_press_up",
            "param ub_press_up",
        ]

    def build_data(self):
        self.data_args = []
        for param_name in self.validated_params:
            if param_name in self.param_registry.keys():
                param = self.param_registry[param_name]
                if param.file == FILE.DATA:
                    arg = param.to_data_entry()
                    if arg is not None:
                        self.data_args.append(arg)
        debug_print(f"---{self.data_args}\n")
        pass


class EcoBuilder:
    def __init__(self, params) -> None:
        self.param_registry = params

        self.validated_params = [
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
            "param MFc",
            "param nu",
            "param UF_2000",
            "param UF_1968",
            "param MPFc",
            "param i",
            "param z",
            "param eta_vp_1",
            "param eta_vp_0",
        ]
        self.args = []

    def build_eco(self):
        self.args = []
        for param_name in self.validated_params:
            if param_name in self.param_registry.keys():
                self.print_list_diff(self.validated_params, self.param_registry)
                param = self.param_registry[param_name]
                if param.file == FILE.ECO:
                    arg = param.to_eco_entry()
                    if arg:
                        self.args.append(arg)
        self.write_eco()
        return self.args

    def write_eco(self, filename="test/eco.dat"):
        dir_path = os.path.dirname(filename)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        with open(filename, "w") as f:
            for entry in self.args:
                f.write(f"{entry}\n")

    def print_list_diff(
        self,
        list1,
        list2,
        label1="Only in self.validated_params",
        label2="Only in list2",
    ):
        only_in_1 = set(list1) - set(list2)
        only_in_2 = set(list2) - set(list1)
        if only_in_1:
            print(f"{label1}: {sorted(only_in_1)}")
        # if only_in_2:
        #     print(f"{label2}: {sorted(only_in_2)}")


class PageParameters(QWidget):
    def __init__(
        self, main_window, stack, sidebar, tabs_for_page=None, tab_categories=None
    ):
        super().__init__()
        self.main_window = main_window
        # self.param_category = param_category
        self.stack = stack
        self.sidebar = sidebar
        self.sidebar.setCurrentRow(0)
        self.categories: list[ParamCategory] = []
        self.tab_categories = tab_categories
        self.tabs: list[QWidget] = []

        main_layout = QVBoxLayout()

        content_layout = QVBoxLayout()
        content_widget = QWidget()
        content_widget.setLayout(content_layout)

        tab1_widget = QWidget()
        tab1_layout = QVBoxLayout(tab1_widget)
        tab1_layout.setSpacing(0)
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)

        if tabs_for_page and tab_categories:
            for tab_name in tabs_for_page:
                tab_widget = QWidget()
                tab_layout = QVBoxLayout(tab_widget)
                for cat in tab_categories.get(tab_name, []):
                    self.categories.append(cat)
                    tab_layout.addWidget(cat)

                scroll_area = QScrollArea()
                scroll_area.setWidgetResizable(True)
                scroll_area.setWidget(tab_widget)
                # scroll_area.setStyleSheet("background: white;")
                tab_widget.setStyleSheet("background-color: white;")
                self.tab_widget.addTab(scroll_area, tab_name)

        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)

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
        if hasattr(self, "tab_widget"):
            current_tab = self.tab_widget.currentIndex()
            tab_count = self.tab_widget.count()
            if current_tab < tab_count - 1:
                self.tab_widget.setCurrentIndex(current_tab + 1)
                return
        current_index = self.sidebar.currentRow()
        count = self.sidebar.count()
        next_index = (current_index + 1) % count
        self.sidebar.setCurrentRow(next_index)
        if hasattr(self, "tab_widget"):
            self.tab_widget.setCurrentIndex(0)


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


class PermType:
    """Data structure used to store permeability's information.

    Attributes:
        robeson_multi (flaot) : robeson bound multiplicater

        robeson_power (flaot) : robeson bound power

        ub_alpha (flaot) : upper bound of \\(\\alpha\\)

        lb_alpha (flaot) : lower bound of \\(\\alpha\\)

        thickness (flaot) : thickness of membrane

        mem_out_prod (`str`) : 'RET' or 'PERM' indicating the position of `final_product`

        component_item (`mind.builder.GasItemPerm`) : component permeances's value

        which_mem (`List[Int]`) : data structure manipulating information about
        association of membrane's postion and membrane's type.

    """

    def __init__(
        self,
        robeson_multi,
        robeson_power,
        ub_alpha,
        lb_alpha,
        component_item,
        thickness,
        mem_out_prod,
        which_mem,
    ):
        # Initalise some values
        self.robeson_multi = robeson_multi
        self.robeson_power = robeson_power
        self.ub_alpha = ub_alpha
        self.lb_alpha = lb_alpha
        self.thickness = thickness
        self.mem_out_prod = mem_out_prod
        self.component_item = component_item  # list of class GasItemPerm
        self.thickness = thickness
        self.which_mem = which_mem  # list of integer

    def __str__(self):
        # for i in range(0, len(self.component_item)):
        #     print(self.component_item[i])
        return (
            "PermType ("
            + "\nrobeson_multi = "
            + str(self.robeson_multi)
            + "\nrobeson_power = "
            + str(self.robeson_power)
            + "\nub_alpha = "
            + str(self.ub_alpha)
            + "\nlb_alpha = "
            + str(self.lb_alpha)
            + "\nthickness = "
            + str(self.thickness)
            + "\ncomponent_item = "
            + str(self.component_item)
            + "\nmem_out_prod = "
            + str(self.mem_out_prod)
            + "\nwhich_mem = "
            + str(self.which_mem)
        )


def delete_value_from(list_of_line, value):
    index = 0
    while index < len(list_of_line):
        if list_of_line[index][0] == value:
            list_of_line.pop(index)
        else:
            index += 1


def parser_variable_permeability_data(file, permeability_data):
    """Permeability's data parser.

    When permeability's variables in model are not fixed.

    Args:
        file (`_io.TextIOWrapper`) : permeability 's datafile

        permeability_data (dict) : data structure which will finally
        contain permeability's informations.

    Returns:
        a dictionary containing permeability's data

    Raises:
        Exception : if datafile format are not repected during lecture of file
    """
    contents = file.readlines()
    delete_value_from(contents, "#")
    delete_value_from(contents, "\n")
    txt = []
    for line in contents:
        txt.append(line.replace("\n", ""))

    contents = txt

    # set mem_type_set := A B
    mem_type = contents[0]
    begining_index = mem_type.find("=")
    mem_type = mem_type[begining_index + 1 :]
    mem_type = mem_type.split()
    contents.remove(contents[0])

    for type_mem in mem_type:
        robeson_multiplicater = None
        robeson_power = None
        ub_alpha = None
        lb_alpha = None
        component_item = []
        thickness = 1
        mem_out_prod = "RET"

        permeability_data[type_mem] = PermType(
            robeson_multiplicater,
            robeson_power,
            ub_alpha,
            lb_alpha,
            component_item,
            thickness,
            mem_out_prod,
            [],
        )

    # param Robeson_multi :=
    contents.remove(contents[0])
    for type_mem in mem_type:
        multiplicater = contents[0].split()
        index = multiplicater[0]
        value = float(multiplicater[-1])
        contents.remove(contents[0])
        # convert from barrer to xxx
        permeability_data[index].robeson_multi = value * 3.347e-05

    # param Robeson_power :=
    contents.remove(contents[0])
    for type_mem in mem_type:
        power = contents[0].split()
        index = power[0]
        value = float(power[-1])
        contents.remove(contents[0])
        permeability_data[index].robeson_power = value

    # param alpha_ub_bounds :=
    contents.remove(contents[0])
    for type_mem in mem_type:
        alpha_bounds = contents[0].split()
        index = alpha_bounds[0]
        value = float(alpha_bounds[-1])
        contents.remove(contents[0])
        permeability_data[index].ub_alpha = value

    # param alpha_lb_bounds :=
    contents.remove(contents[0])
    for type_mem in mem_type:
        alpha_bounds = contents[0].split()
        index = alpha_bounds[0]
        value = float(alpha_bounds[-1])
        contents.remove(contents[0])
        permeability_data[index].lb_alpha = value

    # permeability bounds lb
    contents.remove(contents[0])
    for type_mem in mem_type:
        perm_bounds = contents[0].split()
        index = perm_bounds[0]
        element = perm_bounds[1]
        value = float(perm_bounds[2]) * 3.347e-05
        contents.remove(contents[0])
        item = GasItemPerm(element, value, None, None)
        permeability_data[index].component_item.append(item)

    # permeability bounds ub
    contents.remove(contents[0])
    for type_mem in mem_type:
        perm_bounds = contents[0].split()
        index = perm_bounds[0]
        element = perm_bounds[1]
        value = float(perm_bounds[2]) * 3.347e-05
        contents.remove(contents[0])
        permeability_data[index].component_item[0].ub = value

    # param thickness :=
    contents.remove(contents[0])
    for type_mem in mem_type:
        thickness = contents[0].split()
        index = thickness[0]
        value = float(thickness[-1])
        contents.remove(contents[0])
        permeability_data[index].thickness = value

    # param mem_product :=
    contents.remove(contents[0])
    for type_mem in mem_type:
        mem_product = contents[0].split()
        index = mem_product[0]
        value = mem_product[1]
        permeability_data[index].mem_out_prod = value
        contents.remove(contents[0])

    # param mem_type :=
    if len(contents) > 0:
        contents.remove(contents[0])
    while len(contents) > 0:
        mem_list = contents[0]
        mem_list = mem_list.split()
        mem = int(mem_list[0])
        index = mem_list[-1]
        permeability_data[index].which_mem.append(mem)
        contents.remove(contents[0])

    return permeability_data


def parser_fixed_permeability_data(file, permeability_data):
    """Permeability's data parser.

    When permeability's variables in model are fixed.

    Args:
        file (`_io.TextIOWrapper`) : permeability 's datafile

        permeability_data (dict) : data structure which will finally
        contain permeability's informations.

    Returns:
        a dictionary containing permeability's data

    Raises:
        Exception : if datafile format are not repected during lecture of file
    """
    contents = file.readlines()
    delete_value_from(contents, "#")
    delete_value_from(contents, "\n")

    txt = []
    for line in contents:
        txt.append(line.replace("\n", ""))

    contents = txt
    # set mem_type_set := A B
    mem_type = contents[0]
    begining_index = mem_type.find("=")
    mem_type = mem_type[begining_index + 1 :]
    mem_type = mem_type.split()
    contents.remove(contents[0])

    # param nb_gas := 2
    nb_components = contents[0]
    nb_gas = int(nb_components[-1])
    contents.remove(contents[0])

    # param permeability
    contents.remove(contents[0])

    for type_membrane in mem_type:
        # initialisation
        # defining the dictionary entry for each type of membrane

        robeson_multi = None
        robeson_power = None
        ub_alpha = None
        lb_alpha = None
        component_item = []
        thickness = 1  # default value
        mem_out_prod = "RET"  # default value

        permeability_data[type_membrane] = PermType(
            robeson_multi,
            robeson_power,
            ub_alpha,
            lb_alpha,
            component_item,
            thickness,
            mem_out_prod,
            [],
        )

    for type_membrane in mem_type:
        # read and save pair of (component -> perm value)
        for j in range(nb_gas):
            permeance = contents[0]
            permeance = permeance.split()
            index = permeance[0]
            element = permeance[1]
            # convert from barrer to # XXX
            value = float(permeance[2]) * 3.347e-05
            item = GasItemPerm(element, value, value, value)
            permeability_data[index].component_item.append(item)
            contents.remove(contents[0])

    # param thickness
    contents.remove(contents[0])
    for type_membrane in mem_type:
        thickness = contents[0]
        thickness = thickness.split()
        index = thickness[0]
        thick = float(thickness[-1])
        permeability_data[index].thickness = float(thick)
        contents.remove(contents[0])

    # param mem_product
    contents.remove(contents[0])
    for type_membrane in mem_type:
        mem_product = contents[0]
        mem_product = mem_product.split()
        index = mem_product[0]
        mem_out_prod = mem_product[1]
        permeability_data[index].mem_out_prod = mem_out_prod
        contents.remove(contents[0])

    if len(contents) > 0:
        contents.remove(contents[0])
    while len(contents) > 0:
        mem_list = contents[0]
        mem_list = mem_list.split()
        mem = int(mem_list[0])
        index = mem_list[-1]
        permeability_data[index].which_mem.append(mem)
        contents.remove(contents[0])

    return permeability_data


class GasItemPerm:
    """Data structure used to store gas components permeances's value when
     `permeability's variables` are fixed (constant).

    Attributes:
        index (`Int`): Index of component
        lb (`Float`): lower bound of component permeance
        value (`Float`): value of component permeance if given
        ub (`Float`): lower bound of component permeance

    """

    def __init__(self, index, lb, value, ub):
        # initialisation of gas permeance bound or values
        self.index = index
        self.lb = lb
        self.value = value
        self.ub = ub

    def __str__(self):
        return "index = {} \t lb = {} value = {} \t ub = {}".format(
            self.index, self.lb, self.value, self.ub
        )


def parser_fixed_permeability_data_simple(file):
    # TODO: finir
    contents = file.readlines()
    # Remove comments and empty lines
    contents = [
        line.strip()
        for line in contents
        if line.strip() and not line.strip().startswith("#")
    ]

    # set mem_type_set := A B
    mem_type_line = contents.pop(0)
    mem_type = mem_type_line.split("=")[-1].split()
    # param nb_gas := 2
    nb_gas = int(contents.pop(0).split()[-1])

    # param permeability
    contents.pop(0)

    permeability_dict = {}
    for _ in range(nb_gas * len(mem_type)):
        permeance = contents.pop(0).split()
        type_membrane = permeance[0]
        element = permeance[1]
        value = float(permeance[2])
        if type_membrane not in permeability_dict:
            permeability_dict[type_membrane] = {
                "Permeability": {},
                "thickness": None,
                "mem_out_prod": None,
                "which_mem": [],
            }
        permeability_dict[type_membrane]["Permeability"][element] = value

    # param thickness
    contents.pop(0)
    for type_membrane in mem_type:
        thickness_line = contents.pop(0).split()
        index = thickness_line[0]
        thick = float(thickness_line[-1])
        permeability_dict[index]["thickness"] = thick

    # param mem_product
    contents.pop(0)
    for type_membrane in mem_type:
        mem_product_line = contents.pop(0).split()
        index = mem_product_line[0]
        mem_out_prod = mem_product_line[1]
        permeability_dict[index]["mem_out_prod"] = mem_out_prod

    # param mem_type (optional)
    # if contents:
    #     contents.pop(0)
    # while contents:
    #     mem_list = contents.pop(0).split()
    #     mem = int(mem_list[0])
    #     index = mem_list[-1]
    #     permeability_dict[index]["which_mem"].append(mem)

    # The rest of the file is ignored for this simple dictionary output
    return permeability_dict


def load_coef(filename):
    """Parser for objective function's coefficient.
    Args:
        filename (str) : filename containing economic data information

    Raises:
        Exception : if datafile format is not respected

    Returns:
        a dictionary `economic` containing essential information to send
        to objective function's object
    """

    # list of validated coef
    validated_coefficients = [
        "R",
        "T",
        "eta_cp",
        "eta_vp_0",
        "eta_vp_1",
        "C_cp",
        "C_vp",
        "C_exp",
        "K_m",
        "K_mf",
        "K_mr",
        "K_el",
        "K_gp",
        "K_er",
        "MDFc",
        "MPFc",
        "MFc",
        "UF_2000",
        "UF_2000",
        "UF_2011",
        "UF_1968",
        "ICF",
        "nu",
        "t_op",
        "gamma",
        "phi",
        "a",
        "i",
        "z",
    ]

    economic = {}

    with open(filename, "r") as file:
        for line in file:
            if line == "\n":
                pass
            else:
                line = line.split()
                if line[0] != "param":
                    raise ValueError(
                        "Unkown keyword ({} != param)"
                        " in economic datafile ({})".format(line[0], filename)
                    )
                if line[1] not in validated_coefficients:
                    raise ValueError(
                        "Unkown keyword coefficient ({})"
                        " in economic datafile ({})".format(line[1], filename)
                    )

                economic[line[1]] = float(line[-1])

    return economic
