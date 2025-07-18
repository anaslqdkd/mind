import os
import subprocess
from typing import Optional, cast
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import (
    QAbstractScrollArea,
    QApplication,
    QDial,
    QDialog,
    QFileDialog,
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

from numpy import fix

from app import dependency_manager, param_dict
from app.param import (
    Param,
    ParamBoolean,
    ParamCategory,
    ParamComponent,
    ParamComponentSelector,
    ParamFileChooser,
    ParamFixedComponent,
    ParamFixedComponentWithCheckbox,
    ParamFixedMembrane,
    ParamFixedPerm,
    ParamFixedWithInput,
    ParamGrid,
    ParamGrid2,
    ParamInput,
    ParamMemType,
    ParamMembraneSelect,
    ParamSelect,
    debug_print,
)
from app.param_enums import FILE
from app.param_factory import set_param
from app.param_dict import params_dict
from app.dependency_manager import DependencyManager

# TODO: close button verification before quitting, to abort modifs


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("App")
        self.resize(700, 600)
        self.incoherence_manager: Optional[IncoherenceManager] = None

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
        self.pages: dict[str, PageParameters] = {}

        self.main_area = QWidget()
        header = QLabel("Main Area Header")

        tab_param_layout = QHBoxLayout(self.main_area)

        layout = QVBoxLayout()
        layout.addWidget(header)
        layout.addWidget(self.tabs)

        about_button = QPushButton("A propos")
        # about_button.clicked.connect(self.show_about)
        about_window = AboutDialog()
        about_button.clicked.connect(lambda: AboutDialog(self).exec())
        quit_button = QPushButton("Fermer")
        quit_button.clicked.connect(self.quit_app)
        self.apply_button = QPushButton("Appliquer")

        end_buttons = QWidget()
        end_buttons_layout = QHBoxLayout(end_buttons)
        end_buttons_layout.addWidget(about_button)
        spacer = QSpacerItem(
            0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        end_buttons_layout.addSpacerItem(spacer)
        end_buttons_layout.addStretch()
        end_buttons_layout.addWidget(quit_button)

        layout.addWidget(end_buttons)
        tab_param_layout.addWidget(self.sidebar)
        tab_param_layout.addWidget(self.stack)

        # self.config_builder = ConfigBuilder(self.all_params)

        # add pages to the stack
        self._define_pages()
        self._init_pages()
        self._build_builders()

        for page_name, page in self.pages.items():
            if page_name != "Fixing":
                self.stack.addWidget(page)

        self._set_dependencies()
        self._set_incoherences()

        for el in self.pages.values():
            el.command_button.set_incoherence_manager(self.incoherence_manager)

        self.sidebar.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.apply_button.clicked.connect(self.build_command)
        end_buttons_layout.addWidget(self.apply_button)

        self.tab_param.setLayout(tab_param_layout)
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def quit_app(self):
        QApplication.quit()

    def show_about(self):
        QMessageBox.about(self, "A propos", "A voir quoi mettre dedans")

    def load_config(self):
        # file_path, _ = QFileDialog.getOpenFileName(self, "Open Configuration File", "", "INI files (*.ini);;All Files (*)")
        tuning, instance = load_configuration()
        for el, value in tuning.items():
            if el in self.param_registry.keys():
                if isinstance(self.param_registry[el], ParamInput):
                    self.param_registry[el].set_value_from_import(value)
                    # TODO: continue, add debugging prints
                # self.param_registry[el].set_value(int(value))

                # for el, value in instance.items():
                #     if el in self.param_registry.keys():
                #         if isinstance(self.param_registry[el], ParamBoolean):
                #             self.param_registry[el].set_value(bool(value))
                #         if isinstance(self.param_registry[el], ParamInput):
                #             self.param_registry[el].set_value(int(value))

                pass

    # TODO: in the eco importer put a specific method for params for clarity (not "set value")

    def load_perm(self):
        res = {}
        filepath = "/home/ash/mind/temp/perm.dat"
        with open(filepath, "r") as file:
            perm_data = {}
            perm_param = parser_variable_permeability_data(file, perm_data)
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
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Eco File", "", "Data files (*.dat);;All Files (*)"
        )
        if file_path:
            res = load_coef(file_path)
            for el, value in res.items():
                if f"param {el}" in self.param_registry.keys():
                    self.param_registry[f"param {el}"].set_value(value)

    def _define_pages(self):
        self.categories_names = {
            "General": [
                "gams",
                "no_starting_point",
                "no_simplified_model",
                # "visualise",
                # "opex",
                # "capex",
                "save_log_sol",
            ],
            "Algorithm options": [
                "algorithm",
                "solver",
                "maxiter",
                "maxtime",
                "verbose",
                "debug",
            ],
            "Membranes design": ["num_membranes", "ub_area", "lb_area", "ub_acell"],
            "Model options": [
                "fixing_var",
                "uniform_pup",
                "vp",
                "variable_perm",
                "fname_mask",
                "prototype_data",
                "file_dir",
                "data_dir",
                "log_dir",
            ],
            "File paths": [
                "fname",
                "fname_perm",
                "fname_eco",
            ],
            "Tuning settings": [
                "pressure_ratio",
                "seed1",
                "seed2",
                "iteration",
                "max_no_improve",
                "max_trials",
                "pop_size",
                "generations",
                "n1_element",
            ],
            "Components": [
                "set components",
                "param XIN",
                "param molarmass",
                "param nb_gas",
            ],
            "Product constraints": [
                "param final_product",
                "param normalized_product_qt",
                "param lb_perc_prod",
                "param ub_perc_waste",
            ],
            "Process constraints": [
                "param lb_press_up",
                "param ub_press_up",
                "param ub_press_down",
                "param lb_press_down",
                "param pressure_in",
                "param pressure_prod",
                "param FEED",
            ],
            "Membrane Types": [
                "set mem_types_set",
                "param thickness",
                "param mem_product",
                "param Robeson_multi",
                "param Robeson_power",
                "param ub_alpha",
                "param lb_alpha",
            ],
            "Membrane Options": [
                "param Permeability",
                "param mem_type",
                "param lb_permeability",
                "param ub_permeability",
            ],
            "Thermodynamic & Physical Constants": [
                "param R",
                "param T",
                "param gamma",
                "param phi",
            ],
            "Equipement costs": [
                "param C_cp",
                "param C_exp",
                "param C_vp",
                "param K_m",
                "param K_mf",
                "param K_mr",
                "param K_el",
                "param K_gp",
                "param K_er",
            ],
            "Operation & Replacement": [
                "param t_op",
                "param nu",
            ],
            "Compressor/Expander Factors": [
                "param MFc",
                "param MPFc",
                "param UF_2000",
                "param UF_1968",
                "param i",
                "param z",
            ],
            "Vacuum Pump/Expander Efficiency": [
                "param eta_cp",
                "param eta_vp_1",
                "param eta_vp_0",
            ],
            "Fixing": [
                "fix area",
                "fix splitFEED_frac",
                "fix pressure_up",
                "fix pressure_down",
                "fix splitRET_frac",
                "fix splitPERM_frac",
                "fix splitOutPERM_frac",
                "fix splitOutRET_frac",
            ],
        }

    def _build_builders(self):
        self.command_builder = CommandBuilder(self.param_registry)
        self.config_builder = ConfigBuilder(self.param_registry)
        self.data_builder = DataBuilder(self.param_registry)
        self.eco_builder = EcoBuilder(self.param_registry)
        self.perm_builder = PermBuilder(self.param_registry)
        self.mask_builder = MaskBuilder(self.param_registry)

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
            "Basic": [self.category_instances["Algorithm options"]],
            "Advanced": [self.category_instances["General"]],
            "Instance": [
                self.category_instances["Membranes design"],
                self.category_instances["Model options"],
            ],
            "Tuning": [self.category_instances["Tuning settings"]],
            "Components": [self.category_instances["Components"]],
            "Product": [self.category_instances["Product constraints"]],
            "Process": [self.category_instances["Process constraints"]],
            "Membrane": [self.category_instances["Membrane Types"]],
            "Options": [self.category_instances["Membrane Options"]],
            "Eco": [
                self.category_instances["Thermodynamic & Physical Constants"],
                self.category_instances["Operation & Replacement"],
            ],
            "Eco2": [self.category_instances["Equipement costs"]],
            "Eco3": [
                self.category_instances["Compressor/Expander Factors"],
                self.category_instances["Vacuum Pump/Expander Efficiency"],
            ],
            "Fixing": [self.category_instances["Fixing"]],
            "Files": [self.category_instances["File paths"]],
        }
        self.fixing_page_added = False
        self.page_names = {
            "Program options": ["Basic", "Advanced"],
            "Configuration": ["Instance", "Tuning"],
            "General Data": ["Components", "Product", "Process"],
            "Permeability": ["Membrane", "Options"],
            "Economics": ["Eco", "Eco2", "Eco3"],
            "Fixing": ["Fixing"],
        }

        fixing_param = self.param_registry.get("fixing_var")
        if fixing_param:
            fixing_param.check_box.stateChanged.connect(self.toggle_fixing_page)
        for page, tab_list in self.page_names.items():
            page_tabs_categories = self.tab_categories
            page_temp = PageParameters(
                self, self.stack, self.sidebar, page, tab_list, page_tabs_categories
            )
            max_width = self.sidebar.sizeHintForColumn(0)
            self.sidebar.setFixedWidth(max_width + 90)
            self.pages[page] = page_temp
            if page != "Fixing":
                self.sidebar.addItem(page)

    def toggle_fixing_page(self, state):
        current_index = self.stack.currentIndex()
        sidebar_index = self.sidebar.currentRow()
        if state and not self.fixing_page_added:
            self.stack.addWidget(self.pages["Fixing"])
            self.sidebar.addItem("Fixing")
            self.fixing_page_added = True
        elif not state and self.fixing_page_added:
            self.fixing_page_added = False
            for i in range(self.sidebar.count()):
                if self.sidebar.item(i).text() == "Fixing":
                    self.sidebar.takeItem(i)
                    self.stack.removeWidget(self.pages["Fixing"])
        fixing_param = self.param_registry.get("fixing_var")
        if fixing_param and hasattr(fixing_param, "check_box"):
            fixing_param.check_box.stateChanged.connect(self.toggle_fixing_page)
        if 0 <= current_index < self.stack.count():
            self.stack.setCurrentIndex(current_index)
        else:
            self.stack.setCurrentIndex(0)  # fallback to first page
        if 0 <= sidebar_index < self.sidebar.count():
            self.sidebar.setCurrentRow(sidebar_index)
        else:
            self.sidebar.setCurrentRow(0)
        pass

    def _set_incoherences(self):
        self.incoherence_manager = IncoherenceManager(self)
        self.incoherence_manager.params = self.param_registry
        self.incoherence_manager.test()
        for param in self.param_registry.values():
            param.incoherence_manager = self.incoherence_manager
        param_registry = self.param_registry

        # TODO: add all incoherences
        self.incoherence_manager.add_incoherence(
            # param1, param2, check_fn, message
            param_registry["vp"],
            param_registry["param lb_press_down"],
            self.check_vp_lb_press_down,
            "Incoherence between pressure down and Vacuum pump",
        )
        self.incoherence_manager.add_incoherence(
            # param1, param2, check_fn, message
            param_registry["param lb_press_down"],
            param_registry["param pressure_prod"],
            self.check_pressure_prod_bounds,
            "Pressure_prod value is misconfigured with pressure boundsd",
        )

        pass

    def check_vp_lb_press_down(
        self, vp: ParamBoolean, lb_press_down: ParamInput
    ) -> bool:
        if (vp.get_value() and lb_press_down.get_value_float() > 1.0) or (
            not vp.get_value() and lb_press_down.get_value_float() < 1.0
        ):
            return False
        return True

    def check_pressure_prod_bounds(
        self, lb_press_up: ParamInput, pressure_prod: ParamInput
    ) -> bool:
        ub_press_up = self.param_registry["param ub_press_up"]
        return not (
            ub_press_up.get_value_float() <= pressure_prod.get_value_float()
            or lb_press_up.get_value_float() >= pressure_prod.get_value_float()
        )

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
                # self.update_components,
                self.update_components,
            )
            dependency_manager.add_dependency(
                param_registry["set mem_types_set"],
                param_registry["param Permeability"],
                # self.update_membranes,
                self.update_membranes,
            )

            # dependency_manager.add_dependency(
            #     param_registry["set mem_types_set"],
            #     param_registry["param Permeability"],
            #     self.update_permeability2,
            # )
            # dependency_manager.add_dependency(
            #     param_registry["set components"],
            #     param_registry["param Permeability"],
            #     self.update_permeability2,
            # )

            dependency_manager.add_dependency(
                param_registry["set mem_types_set"],
                param_registry["param thickness"],
                self.update_membranes,
            )
            dependency_manager.add_dependency(
                param_registry["set mem_types_set"],
                param_registry["param Robeson_multi"],
                self.update_membranes,
            )
            dependency_manager.add_dependency(
                param_registry["set mem_types_set"],
                param_registry["param Robeson_power"],
                self.update_membranes,
            )
            dependency_manager.add_dependency(
                param_registry["set mem_types_set"],
                param_registry["param ub_alpha"],
                self.update_membranes,
            )
            dependency_manager.add_dependency(
                param_registry["set mem_types_set"],
                param_registry["param lb_alpha"],
                self.update_membranes,
            )
            dependency_manager.add_dependency(
                param_registry["set mem_types_set"],
                param_registry["param lb_permeability"],
                self.update_membranes_grid,
            )
            dependency_manager.add_dependency(
                param_registry["set mem_types_set"],
                param_registry["param ub_permeability"],
                self.update_membranes_grid,
            )
            dependency_manager.add_dependency(
                param_registry["set components"],
                param_registry["param ub_permeability"],
                self.update_components_grid,
            )
            dependency_manager.add_dependency(
                param_registry["set components"],
                param_registry["param lb_permeability"],
                self.update_components_grid,
            )
            # dependency_manager.add_dependency(
            #     param_registry["set components"],
            #     param_registry["param mem_type"],
            #     self.update_components,
            # )

            # dependency_manager.add_dependency(
            #     param_registry["set mem_types_set"],
            #     param_registry["param mem_product"],
            #     self.update_permeability,
            # )
            dependency_manager.add_dependency(
                param_registry["set mem_types_set"],
                param_registry["param mem_product"],
                self.update_mem_product,
            )
            dependency_manager.add_dependency(
                param_registry["set components"],
                param_registry["param XIN"],
                self.update_xin,
            )
            dependency_manager.add_dependency(
                param_registry["set components"],
                param_registry["param molarmass"],
                self.update_xin,
            )
            dependency_manager.add_dependency(
                param_registry["param final_product"],
                param_registry["param lb_perc_prod"],
                self.update_lb_perc_prod,
            )
            dependency_manager.add_dependency(
                param_registry["set components"],
                param_registry["param lb_perc_prod"],
                self.update_lb_perc_prod_after_components,
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
            dependency_manager.add_dependency(
                param_registry["variable_perm"],
                None,
                self.update_variable_perm,
            )
            dependency_manager.add_dependency(
                param_registry["set components"],
                param_registry["param nb_gas"],
                self.update_nb_gas,
            )
            dependency_manager.add_dependency(
                param_registry["num_membranes"],
                param_registry["param mem_type"],
                self.update_mem_type,
            )
            dependency_manager.add_dependency(
                param_registry["set mem_types_set"],
                param_registry["param mem_type"],
                self.update_mem_type_membranes,
            )
            dependency_manager.add_dependency(
                param_registry["num_membranes"],
                param_registry["fix area"],
                self.update_fix_area,
            )
            dependency_manager.add_dependency(
                param_registry["num_membranes"],
                param_registry["fix splitFEED_frac"],
                self.update_fix_area,
            )
            dependency_manager.add_dependency(
                param_registry["num_membranes"],
                param_registry["fix pressure_up"],
                self.update_fix_area,
            )
            dependency_manager.add_dependency(
                param_registry["num_membranes"],
                param_registry["fix pressure_down"],
                self.update_fix_area,
            )
            dependency_manager.add_dependency(
                param_registry["num_membranes"],
                param_registry["fix splitRET_frac"],
                self.update_fix_matrix,
            )
            dependency_manager.add_dependency(
                param_registry["num_membranes"],
                param_registry["fix splitPERM_frac"],
                self.update_fix_matrix,
            )
            dependency_manager.add_dependency(
                param_registry["num_membranes"],
                param_registry["fix splitOutPERM_frac"],
                self.update_fix_area,
            )
            dependency_manager.add_dependency(
                param_registry["num_membranes"],
                param_registry["fix splitOutRET_frac"],
                self.update_fix_area,
            )
            dependency_manager.add_dependency(
                param_registry["variable_perm"],
                param_registry["param pressure_prod"],
                self.update_pressure_prod,
            )
            dependency_manager.add_dependency(
                param_registry["uniform_pup"],
                param_registry["param pressure_prod"],
                self.update_pressure_prod,
            )
            dependency_manager.add_dependency(
                # pressure_in > lb_press_up
                param_registry["param lb_press_up"],
                param_registry["param pressure_in"],
                self.update_pressure_lower_bound,
            )
            dependency_manager.add_dependency(
                # pressure_in < up_press_up
                param_registry["param ub_press_up"],
                param_registry["param pressure_in"],
                self.update_pressure_upper_bound,
            )
            dependency_manager.add_dependency(
                # lb_press_up < up_press_up
                param_registry["param lb_press_up"],
                param_registry["param ub_press_up"],
                self.update_pressure_ub_inf_lb,
            )
            dependency_manager.add_dependency(
                # lb_press_up < up_press_up
                param_registry["param ub_press_up"],
                param_registry["param lb_press_up"],
                self.update_pressure_lb_sup_ub,
            )
            dependency_manager.add_dependency(
                # permeability variable is authorised only for bi-components
                param_registry["variable_perm"],
                param_registry["set components"],
                self.set_bi_components,
            )
            dependency_manager.add_dependency(
                # if vp ub_press_down < 1.0, if not vp lb_press_down > 1.0
                param_registry["vp"],
                param_registry["param ub_press_down"],
                self.update_ub_press_down_vp,
            )
            dependency_manager.add_dependency(
                # lb_press_down < ub_press_down
                param_registry["param lb_press_down"],
                param_registry["param ub_press_down"],
                self.update_press_lb_down_inf_ub_down,
            )
            dependency_manager.add_dependency(
                # lb_press_down < ub_press_down
                param_registry["param ub_press_down"],
                param_registry["param lb_press_down"],
                self.update_press_lb_down_sup_ub_down,
                # TODO: use lamdba to switch orders instead of defining two separate functions
            )
            dependency_manager.add_dependency(
                # lb_area < ub_area
                param_registry["ub_area"],
                param_registry["lb_area"],
                self.update_lb_area_bounds,
            )
            dependency_manager.add_dependency(
                # lb_area < ub_area
                param_registry["lb_area"],
                param_registry["ub_area"],
                self.update_lb_area_bounds2,
            )
            dependency_manager.add_dependency(
                # molar mass update
                param_registry["set components"],
                param_registry["param molarmass"],
                self.update_molarmass,
            )
            dependency_manager.add_dependency(
                # lb_alpha < ub_alpha
                param_registry["param lb_alpha"],
                param_registry["param ub_alpha"],
                self.update_alpha_bounds,
            )
            dependency_manager.add_dependency(
                # lb_alpha < ub_alpha
                param_registry["param ub_alpha"],
                param_registry["param lb_alpha"],
                self.update_alpha_bounds2,
            )
            dependency_manager.add_dependency(
                # lb_alpha < ub_alpha
                param_registry["param lb_permeability"],
                param_registry["param ub_permeability"],
                self.update_permeability_bounds,
            )
            dependency_manager.add_dependency(
                param_registry["set components"],
                param_registry["param ub_perc_waste"],
                self.update_ub_perc_waste,
            )

        register_param_dependencies(self.param_registry, dependency_manager)

    def update_ub_perc_waste(self, ub_perc_waste: ParamFixedComponentWithCheckbox, param_set_components: ParamComponentSelector, sender):
        ub_perc_waste.set_values(param_set_components.get_selected_items())
        ub_perc_waste.category.update_category()

    def update_permeability_bounds(self, ub_permeabiliy: ParamGrid2, lb_permeability: ParamGrid2 , sender):
        pass

    def update_lb_perc_prod(self, lb_perc_prod: ParamFixedComponent, final_product: ParamSelect, sender):
        debug_print("in update lb_perc prod")
        final_component = final_product.get_value_select()
        if final_component is not None:
            lb_perc_prod.set_components([final_component])
        lb_perc_prod.update_param()


    def update_molarmass(self, molarmass: ParamFixedComponent, components_selector: ParamComponentSelector, sender):
        molar_masses = {
            "O2": 31.998,
            "H2": 2.016,
            "CO2": 44.009,
            "N2": 28.014,
        }
        components = components_selector.selected_components
        for i, spin_box in enumerate(molarmass.spin_boxes):
            if components[i] in molar_masses.keys():
                spin_box.setValue(molar_masses[components[i]])

    def update_alpha_bounds(self, ub_alpha: ParamFixedMembrane, lb_alpha: ParamFixedMembrane, sender):
        if sender in lb_alpha.spin_boxes:
            index = lb_alpha.spin_boxes.index(sender)
            if index in range(len(ub_alpha.elements)):
                ub_alpha.elements[index]["min_value"] = sender.value()
        lb_alpha.category.update_category()

    def update_alpha_bounds2(self, lb_alpha: ParamFixedMembrane, ub_alpha: ParamFixedMembrane, sender):
        if sender in ub_alpha.spin_boxes:
            index = ub_alpha.spin_boxes.index(sender)
            if index in range(len(lb_alpha.elements)):
                lb_alpha.elements[index]["max_value"] = sender.value()
        ub_alpha.category.update_category()

    def update_lb_area_bounds2(self, ub_area: ParamFixedWithInput, lb_area: ParamFixedWithInput, sender):
        if sender in lb_area.line_edits:
            index = lb_area.line_edits.index(sender)
            if index in ub_area.elements:
                ub_area.elements[index]["min_value"] = sender.value()
        lb_area.category.update_category()

    def update_lb_area_bounds(self, lb_area: ParamFixedWithInput, ub_area: ParamFixedWithInput, sender):
        if sender in ub_area.line_edits:
            index = ub_area.line_edits.index(sender)
            if index in lb_area.elements:
                lb_area.elements[index]["max_value"] = sender.value()
        lb_area.category.update_category()

    def update_press_lb_down_inf_ub_down(self, ub_press_down: ParamInput, lb_press_down: ParamInput, sender):
        ub_press_down.min_value = lb_press_down.get_value_float()
        ub_press_down.category.update_category()

    def update_press_lb_down_sup_ub_down(self, lb_press_down: ParamInput, ub_press_down: ParamInput, sender):
        lb_press_down.max_value = ub_press_down.get_value_float()
        lb_press_down.category.update_category()

    def update_ub_press_down_vp(self, ub_press_down: ParamInput, vp: ParamBoolean, sender):
        lb_press_down = cast(ParamInput, self.param_registry["param lb_press_down"])
        if vp.get_value():
            # if vp then ub_press_down < 1.0
            ub_press_down.max_value = 1.0
            ub_press_down.min_value = 0.0
            lb_press_down.max_value = ub_press_down.min_value
            lb_press_down.min_value = 0.0
        else:
            # if not vp then lb_press_down > 1.0
            lb_press_down.min_value = 1.0
            lb_press_down.max_value = 10
            ub_press_down.min_value = 1.0
            ub_press_down.max_value = 10
        ub_press_down.category.update_category()


    def set_bi_components(self, components_selector: ParamComponentSelector, variable_perm: ParamBoolean, sender):
        # if variable perm is checked:
        if variable_perm.get_value():
            components_selector.max_selected = 2
            # in case the components were already set and the variable perm was checked afterwards
            components_selector.selected_components = components_selector.selected_components[:2]
        else:
            components_selector.max_selected = None
        components_selector.category.update_category()

    def update_pressure_lb_sup_ub(self, lb_press_up: ParamInput, ub_press_up: ParamInput, sender):
        lb_press_up.max_value = ub_press_up.get_value_float()
        lb_press_up.category.update_category()

    def update_pressure_ub_inf_lb(self, ub_press_up: ParamInput, lb_press_up: ParamInput, sender):
        ub_press_up.min_value = lb_press_up.get_value_float()
        ub_press_up.category.update_category()

    def update_pressure_lower_bound(self, pressure_in: ParamInput, lb_press_up: ParamInput, sender):
        lower_bound = lb_press_up.get_value_float()
        pressure_in.min_value = lower_bound
        pressure_in.category.update_category()
        # NOTE: or update param?

    def update_pressure_upper_bound(self, pressure_in: ParamInput, up_press_up: ParamInput, sender):
        upper_bound = up_press_up.get_value_float()
        pressure_in.max_value = upper_bound
        pressure_in.category.update_category()
        # NOTE: or update param?


    def update_pressure_prod(self, target: ParamInput, source: ParamBoolean, sender):
        # for pressure prod pressure must be uniform and permeability must be fixed
        variable_perm = self.param_registry["variable_perm"].get_value()
        uniform_pressure = self.param_registry["uniform_pup"].get_value()
        if source.get_value():
            target.hide()
        elif not uniform_pressure or not variable_perm:
            target.show()
        target.category.update_category()

    def update_nb_gas(self, target: ParamInput, source: ParamComponentSelector, sender):
        target.set_last_line_edit(int(source.get_value()))

    def update_mem_product(self, target: ParamMembraneSelect, source: ParamComponent, sender):
        target.set_membranes(source.get_items())
        target.category.update_category()

    def update_mem_type_membranes(
        self, target: ParamMembraneSelect, source: ParamComponent, sender
    ):
        target.set_membranes(source.get_items())
        target.category.update_category()

    def update_mem_type(self, target: ParamMemType, source: ParamInput, sender):
        target.set_floors(int(float(source.get_value())))
        # target.category.update_category()
        target.update_param()

    def update_final_product(self, target: ParamSelect, source: ParamComponentSelector, sender):
        target.set_values(source.selected_components)
        # target.category.update_category()
        target.update_param()

    def update_lb_perc_prod_after_components(self, lb_perc_prod: ParamFixedComponent, param_set_components: ParamComponentSelector, sender):
        lb_perc_prod.set_components([param_set_components.selected_components[0]])
        lb_perc_prod.update_param()


    def update_permeability(self, target: ParamFixedWithInput, source: ParamComponent, sender):
        debug_print(target.name, source.name)
        target.set_rows(int(source.get_value()), source)
        # target.category.update_category()
        target.update_param()

    def update_permeability2(
        self, target: ParamFixedWithInput, source: ParamComponentSelector, sender
    ):
        target.set_rows_nb(int(source.get_value()), source)
        # target.category.update_category()
        target.update_param()

    def update_components(self, target: ParamFixedPerm, source: ParamComponentSelector, sender):
        target.set_components(source.get_selected_items())
        # target.category.update_category()
        target.update_param()

    def update_xin(self, target: ParamFixedComponent, source: ParamComponentSelector, sender):
        target.set_components(source.get_selected_items())
        # target.category.update_category()
        target.update_param()

    def update_membranes(self, target: ParamFixedPerm, source: ParamComponent, sender):
        target.set_membranes(source.get_items())
        debug_print(source.get_items())
        target.update_param()

    # def update_permeability(self, target: ParamFixedMembrane, source: ParamComponent):
    #     debug_print("the target name is:", target.name)
    #     target.set_membranes(source.get_items())
    #     target.category.update_category()

    def update_fn(self, target: ParamFixedWithInput, source: ParamInput, sender):
        target.set_row(int(float(source.get_value())))
        # target.set_row(int(source.get_value()))
        # target.category.update_category()
        target.update_param()

    def update_pages(self):
        for page in self.pages.values():
            page.update_param_page()

    def update_generations(self, target: Param, source: Param, sender):
        if source.last_combo_box != "genetic":
            target.hide()
        else:
            target.show()
        target.category.update_category()

    def update_fixing(self, target: ParamFileChooser, source: ParamBoolean, sender):
        if source.last_check_box:
            target.show()
        else:
            target.hide()
        target.category.update_category()

    # def update_fix_area(self, target: ParamFixedComponentWithCheckbox, source: ParamInput):
    #     target.set_components([str(i) for i in range(1, int(source.get_value()) + 1)])
    #     target.category.update_category()
    def update_fix_area(
        self, target: ParamFixedComponentWithCheckbox, source: ParamInput, sender
    ):
        target.set_values([str(i) for i in range(1, int(source.get_value()) + 1)])
        target.category.update_category()

    def update_fix_matrix(self, target: ParamGrid, source: ParamInput, sender):
        target.set_values([str(i) for i in range(1, int(source.get_value()) + 1)])
        target.category.update_category()

    def store_value(self):
        pass

    def update_membranes_grid(self, target: ParamGrid2, source: ParamComponent, sender):
        target.set_membranes(source.get_items())
        # target.category.update_category()
        target.update_param()

    def update_components_grid(
        self, target: ParamGrid2, source: ParamComponentSelector, sender
    ):
        target.set_components(source.get_selected_items())

    def update_config_algo_params(self, target: ParamInput, source: ParamSelect, sender):
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

    def update_variable_perm(self, target: Param, source: ParamBoolean, sender):
        # TODO: optimize
        variable_perm_params = [
            "param Robeson_multi",
            "param Robeson_power",
            "param ub_alpha",
            "param lb_alpha",
            "param ub_permeability",
            "param lb_permeability",
            # "param thickness",
            "param mem_product",
        ]
        fixed_variable_params = [
            "set mem_type_set",
            "param nb_gas",
            "param Permeability",
            # "param thickness",
            "param mem_product",
            "param mem_type",
        ]

        if source.last_check_box:
            # if perm variable
            for param_name in variable_perm_params:
                param = self.param_registry.get(param_name)
                if param:
                    param.show()
                    param.category.update_category()
            for param_name in fixed_variable_params:
                param = self.param_registry.get(param_name)
                if param:
                    param.hide()
                    param.category.update_category()
        else:
            for param_name in fixed_variable_params:
                param = self.param_registry.get(param_name)
                if param:
                    param.show()
                    param.category.update_category()
            for param_name in variable_perm_params:
                param = self.param_registry.get(param_name)
                if param:
                    param.hide()
                    param.category.update_category()

    def build_command(self):
        self.update_pages()
        command = self.command_builder.build_command()
        config = self.config_builder.build_config()
        data = self.data_builder.build_data()
        eco = self.eco_builder.build_eco()
        perm = self.perm_builder.build_perm()
        mask = self.mask_builder.build_mask()
        # debug_print("the command is", command)
        # debug_print("the config is", config)
        # debug_print("the data is", data)
        # debug_print("the eco is", eco)
        # debug_print("the perm is", perm)


# -----------------------------------------------------------
class IncoherenceManager:
    def __init__(self, main_window: MainWindow) -> None:
        self.params: dict[str, "Param"] = {}
        self.rules = {}
        self.main_window: MainWindow = main_window

    def test(self):
        print("in test function of incoherence mananger")

    def add_param(self, param):
        self.params[param.name] = param
        param.manager = self

    def add_incoherence(self, param1, param2, check_fn, message=None):
        self.rules[(param1.name, param2.name)] = (check_fn, message)

    def check_incoherences(self) -> list[str]:
        self.main_window.update_pages()
        errors = []
        for (param1_name, param2_name), (check_fn, message) in self.rules.items():
            p1 = self.params.get(param1_name)
            p2 = self.params.get(param2_name)
            if p1 is None or p2 is None:
                continue

            if not check_fn(p1, p2):
                errors.append(
                    message or f"Incoherence between {param1_name} and {param2_name}"
                )
        return errors


# -----------------------------------------------------------


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
        self.args = []
        for param_name in self.validated_params:
            if param_name in self.param_registry:
                param = self.param_registry[param_name]
                arg = param.to_command_arg()
                if arg is not None and arg != "":
                    self.args.append(arg)
        self.command = " ".join(self.args)
        self.write_command_script()

    def write_command_script(self, filename="run_command.sh"):
        filename = f"{self.param_registry['file_dir'].get_path()}/command.sh"
        dir_path = os.path.dirname(filename)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        with open(filename, "w") as f:
            f.write("#!/bin/bash\n")
            f.write("source mind/env/bin/activate\n")
            f.write(f"python3.10 -m mind.launcher {self.command} --exec\n")


# TODO: assert lb pressure <= ub pressure etc
# TODO: parmeability varaible autorised only for bi-components


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
            "fname",
        ]
        self.config_args = {}

    def build_config(self):
        self.config_args = {"tuning": [], "instance": []}
        for param_name in self.tuning_params:
            if param_name in self.param_registry.keys():
                param = self.param_registry[param_name]
                arg = param.to_config_entry()
                if arg is not None:
                    self.config_args["tuning"].append(arg)
        for param_name in self.instance_params:
            if param_name in self.param_registry.keys():
                param = self.param_registry[param_name]
                arg = param.to_config_entry()
                if arg is not None:
                    self.config_args["instance"].append(arg)
        self.write_config_ini()

    def write_config_ini(self, filename="test/config.ini"):
        dir = self.param_registry['file_dir'].get_path()

        filename = f"{self.param_registry['file_dir'].get_path()}/config.ini"
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

        epsilon = "{'At': 0.3, 'press_up_f': 0.2, 'press_down_f': 0.2, 'feed': 0.3, 'perm_ref': 0.1, 'alpha': 0.1, 'delta': 0.1, 'xout': 0.0001}"
        config["tuning"]["epsilon"] = epsilon
        if "fname" not in config["instance"]:
            config["instance"]["fname"] = f"{dir}/data.dat"
        if "fname_perm" not in config["instance"]:
            config["instance"]["fname_perm"] = f"{dir}/perm.dat"
        if "fname_eco" not in config["instance"]:
            config["instance"]["fname_eco"] = f"{dir}/eco.dat"

        if self.param_registry["fixing_var"].get_value():
            if "fname_mask" not in config["instance"]:
                config["instance"]["fname_mask"] = f"{dir}/mask.dat"

        with open(filename, "w") as configfile:
            config.write(configfile)


# -----------------------------------------------------------
class MaskBuilder:
    def __init__(self, params) -> None:
        self.param_registry = params
        self.validated_params = [
            "fix area",
            "fix splitFEED_frac",
            "fix pressure_up",
            "fix pressure_down",
            "fix splitPERM_frac",
            "fix splitRET_frac",
            "fix splitOutPERM_frac",
            "fix splitOutRET_frac",
        ]
        self.mask_args = {}

    def build_mask(self):
        self.mask_args = []
        for param_name in self.validated_params:
            if param_name in self.param_registry.keys():
                param = self.param_registry[param_name]
                arg = param.to_mask_entry()
                if arg is not None and arg != "":
                    self.mask_args.append(arg)
        self.write_data()
        pass

    def write_data(self, filename="test/perm.dat"):
        filename = f"{self.param_registry['file_dir'].get_path()}/mask.dat"
        dir_path = os.path.dirname(filename)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        with open(filename, "w") as f:
            for entry in self.mask_args:
                f.write(f"{entry}\n\n")


# -----------------------------------------------------------
class DataBuilder:
    def __init__(self, params) -> None:
        self.param_registry = params
        self.validated_params = [
            "param pressure_in",
            "set components",
            # TODO: uncomment
            # "param pressure_prod",
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
        self.data_args = []

    # TODO: see for lb_perc_prod, ub_perc prod, what are the components

    def build_data(self):
        self.data_args = []
        for param_name in self.validated_params:
            if param_name in self.param_registry.keys():
                param = self.param_registry[param_name]
                arg = param.to_data_entry()
                if arg is not None:
                    self.data_args.append(arg)
        self.write_data()
        pass

    def write_data(self, filename="test/data.dat"):
        filename = f"{self.param_registry['file_dir'].get_path()}/data.dat"
        dir_path = os.path.dirname(filename)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        with open(filename, "w") as f:
            f.write(f"data;\n\n")
            for entry in self.data_args:
                f.write(f"{entry};\n\n")


class PermBuilder:
    def __init__(self, params) -> None:
        self.param_registry = params
        self.validated_params = [
            "set mem_types_set",
            "param nb_gas",
            "param Robeson_multi",
            "param Robeson_power",
            "param ub_alpha",
            "param lb_alpha",
            "param lb_permeability",
            "param ub_permeability",
            "param Permeability",
            "param thickness",
            "param mem_product",
            "param mem_type",
        ]
        self.fixed_params = [
                "set mem_types_set",
                "param nb_gas",
                "param Permeability",
                "param thickness",
                "param mem_product",
                "param mem_type"
                ]
        self.variable_params = [
                "set mem_types_set",
                "param Robeson_multi",
                "param Robeson_power",
                "param ub_alpha",
                "param lb_alpha",
                "param lb_permeability",
                "param ub_permeability",
                "param thickness",
                "param mem_product"
                ]
        self.perm_args = []

    def build_perm(self):
        self.perm_args = []
        params_list = self.variable_params if self.param_registry["variable_perm"].get_value() else self.fixed_params
        for param_name in params_list:
            if param_name in self.param_registry.keys():
                param = self.param_registry[param_name]
                arg = param.to_perm_entry()
                if arg is not None and (
                    param_name != "nb_gas"
                    or not self.param_registry["variable_perm"].get_value()
                ):
                    self.perm_args.append(arg)
        self.write_data()
        pass

    def write_data(self, filename="test/perm.dat"):
        filename = f"{self.param_registry['file_dir'].get_path()}/perm.dat"
        dir_path = os.path.dirname(filename)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        with open(filename, "w") as f:
            for entry in self.perm_args:
                f.write(f"{entry}\n\n")


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
                param = self.param_registry[param_name]
                arg = param.to_eco_entry()
                if arg:
                    self.args.append(arg)
        self.write_eco()
        return self.args

    def write_eco(self, filename="test/eco.dat"):
        filename = f"{self.param_registry['file_dir'].get_path()}/eco.dat"
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
        self,
        main_window,
        stack,
        sidebar,
        name: str,
        tabs_for_page=None,
        tab_categories=None,
    ):
        super().__init__()
        self.main_window = main_window
        self.name = name
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
        self.tab_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

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
                tab_layout.addStretch()
                tab_widget.setSizePolicy(
                    QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
                )
                scroll_area.setSizePolicy(
                    QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
                )
                self.tab_widget.addTab(scroll_area, tab_name)

        main_layout.addWidget(self.tab_widget, stretch=1)

        next_button = QPushButton("next")

        # command_path = ""
        print(os.getcwd())
        command_button = CommandLauncherButton(
            "test/command.sh", incoherence_manager=self.main_window.incoherence_manager
        )
        self.command_button = command_button

        end_button_widget = QWidget()
        end_button_layout = QHBoxLayout(end_button_widget)
        end_button_layout.addStretch()
        next_button.clicked.connect(self.go_to_next_page)
        end_button_layout.addWidget(next_button)
        main_layout.addWidget(end_button_widget)
        main_layout.addWidget(command_button)

        main_layout.addStretch()

        self.setLayout(main_layout)

        # TODO: see for command to have execution permissions
        # TODO: remove nb_gas for variable perm
        # TODO: remove mem_type for perm variable
        # TODO: forgot lb_alpha

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


def load_configuration(filepath: str = "/home/ash/mind/temp/config.ini"):
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
        config.read(filepath)
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


class CommandLauncherButton(QPushButton):
    def __init__(
        self,
        script_path,
        incoherence_manager: IncoherenceManager,
        terminal_cmd="alacritty",
        parent=None,
    ):
        super().__init__("Run Command", parent)
        self.script_path = script_path
        self.terminal_cmd = terminal_cmd
        self.clicked.connect(self.launch_terminal)
        self.incoherence_manager = incoherence_manager

    def set_incoherence_manager(self, incoherence_manager: IncoherenceManager):
        self.incoherence_manager = incoherence_manager

    def launch_terminal(self):

        subprocess.Popen(
            [
                "alacritty",
                "-e",
                "bash",
                "-c",
                # f"{self.script_path}; read -p 'Done. Press enter...'",
                f"{self.script_path}; exec bash"
            ]
        )
        # NOTE: uncomment for the gnome terminal
        # subprocess.Popen(
        #     [
        #         "gnome-terminal",
        #         "--",
        #         "bash",
        #         "-c",
        #         f"{self.script_path}; read -p 'Done. Press enter...'",
        #     ]
        # )

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("À propos de Mind")
        self.setFixedSize(230, 150)
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QLabel#TitleLabel {
                color: #222;
                font-weight: bold;
                font-size: 15px;
            }
            QLabel#SubtitleLabel, QLabel#CopyrightLabel {
                color: #444;
                font-size: 10px;
            }
            QLabel#LinkLabel {
                color: #0066cc;
            }
            QPushButton {
                background-color: #f5f5f5;
                color: #222;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        layout = QVBoxLayout()
        # layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Top Icon
        icon_label = QLabel()
        pixmap = QPixmap(48, 48)
        pixmap.fill(Qt.GlobalColor.transparent)
        icon_label.setPixmap(pixmap)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # layout.addWidget(icon_label)

        # Main Title
        title = QLabel("Mind 1.0.0")
        title.setObjectName("TitleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Python Optimization Software for Process Design Membranes")
        subtitle.setWordWrap(True)
        subtitle.setObjectName("SubtitleLabel")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        # Copyright
        copyright = QLabel("Copyright (C) 2025 Mind Project")
        copyright.setObjectName("CopyrightLabel")
        copyright.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(copyright)

        # Hyperlink
        link = QLabel('<a href="https://github.com/anaslqdkd/mind">mind site</a>')
        link.setObjectName("LinkLabel")
        link.setAlignment(Qt.AlignmentFlag.AlignCenter)
        link.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        link.setOpenExternalLinks(True)
        layout.addWidget(link)

        # Buttons
        buttons_layout = QHBoxLayout()
        # buttons_layout.setSpacing(15)
        # Crédit Button
        credit_button = QPushButton("🛈 Crédits")
        credit_button.setIcon(QIcon()) # Add your icon if desired
        credit_button.clicked.connect(self.show_credits)
        buttons_layout.addWidget(credit_button)

        # Licence Button
        licence_button = QPushButton("Licence")
        licence_button.setIcon(QIcon())
        licence_button.clicked.connect(self.show_licence)
        buttons_layout.addWidget(licence_button)

        # Fermer Button
        fermer_button = QPushButton("✖ Fermer")
        fermer_button.setIcon(QIcon())
        fermer_button.clicked.connect(self.close)
        buttons_layout.addWidget(fermer_button)

        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def show_credits(self):
        QMessageBox.information(self, "Crédits", "Développé par ...")

    def show_licence(self):
        QMessageBox.information(self, "Licence", "Licence MIT © 2025")
