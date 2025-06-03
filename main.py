import os
from PyQt6.QtGui import QWindow
from PyQt6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMainWindow,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtCore import Qt
import sys
from PyQt6.QtWidgets import QApplication

PAGE_MAIN = 2
PAGE_START = 1
PAGE_PARAMETERS = 0


PARAMETERS_ECO = {
    "param R": "var",
    "param phi": "var",
    "param T": "var",
    "param gamma": "var",
    "param C_cp": "var",
    "param C_exp": "var",
    "param C_vp": "var",
    "param eta_cp": "var",
    "param K_mr": "var",
    "param K_gp": "var",
    "param K_m": "var",
    "param K_mf": "var",
    "param K_el": "var",
    "param t_op": "var",
    "param MFc": "var",
    "param nu": "var",
    "param UF_2000": "var",
    "param UF_1968": "var",
    "param MPFc": "var",
    "param i": "var",
    "param z": "var",
    "param eta_vp_1": "var",
    "param eta_vp_0": "var",
}

PARAMETERS_DATA = {
    "param pressure_in": "var",
    "param pressure_prod": "var",  # optionnel ?
    "set components": "var",  # plusieurs composants de str
    "param ub_perc_waste": "var",
    "param lb_perc_prod": "var",  # pour l'élément produit
    "param normalized_product_qt": "var",
    "param final_product": "var",
    "param FEED": "var",  # unité
    "param XIN": "var",  # pour chaque composant
    "param molarmass": "var",  # pour chaque composant aussi
    "param ub_press_down": "var",
    "param ib_press_down": "var",
    "param ib_press_up": "var",
    "param ub_press_up": "var",
}

PARAMETERS_PERM = {
    "set mem_type_set": "var",
    "param nb_gas": "var",
    "param Permeability": "var",
    "param thickness": "var",
    "param mem_product": "var",
}

CONFIG_TUNING = {
    "pressure_ratio": "var",
    "epsilon": "var",
    "seed1": "var",
    "seed2": "var",
    "iteration": "var",
    "max_no_improve": "var",
    "max_trials": "var",
    "pop_size": "var",
    "generations": "var",
    "n1_element": "var",
}
CONFIG_INSTANCE = {
    "data dir": "var",
    "log_dir": "var",
    "num_membranes": "var",
    "ub_area": "var",
    "lb_area": "var",
    "ub_acell": "var",
    "fixing_var": "var",
    "fname": "var",
    "fname_perm": "var",
    "fname_eco": "var",
    "fname_mask": "bool",  # bool # remove if fixing_var = false else indicate the fname_mask fil:
    "prototype_data": "var",
    "bool"  # if genetic algo:
    "uniform_pup": "var",
    "vp": "bool",  # bool:
    "variable_perm": "bool",  # bool:
}


class StartPage(QWidget):
    def __init__(self, stack):
        super().__init__()
        self.stack = stack
        form_layout = QFormLayout()
        layout = QVBoxLayout()
        button = QPushButton("go to main page")
        button.clicked.connect(self.on_submit)
        form_layout.addWidget(button)
        form_widget = QWidget()
        form_widget.setLayout(form_layout)
        form_widget.setFixedWidth(200)
        layout.addWidget(
            form_widget,
            alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
        )
        self.setLayout(layout)

    def on_submit(self):
        self.stack.setCurrentIndex(PAGE_MAIN)


class ParameterPage(QWidget):
    def __init__(self, stack, main_window):
        super().__init__()
        self.main_window = main_window
        self.parameters_eco_input = {}
        self.parameters_data_input = {}
        self.parameters_perm_input = {}
        self.config_tuning = {}
        self.config_instance = {}

        eco_form_layout = QFormLayout()
        data_form_layout = QFormLayout()
        perm_form_layout = QFormLayout()
        config_form_layout = QFormLayout()

        for key in PARAMETERS_ECO.keys():
            parameter_type = PARAMETERS_ECO[key]
            parameter_edit = QLineEdit()
            eco_form_layout.addRow(key.capitalize() + ":", parameter_edit)
            self.parameters_eco_input[key] = parameter_edit
        for key in PARAMETERS_DATA.keys():
            parameter_type = PARAMETERS_DATA[key]
            parameter_edit = QLineEdit()
            data_form_layout.addRow(key.capitalize() + ":", parameter_edit)
            self.parameters_data_input[key] = parameter_edit
        for key in PARAMETERS_PERM.keys():
            parameter_type = PARAMETERS_PERM[key]
            parameter_edit = QLineEdit()
            perm_form_layout.addRow(key.capitalize() + ":", parameter_edit)
            self.parameters_perm_input[key] = parameter_edit
        for key in CONFIG_INSTANCE.keys():
            parameter_type = CONFIG_INSTANCE[key]
            print(parameter_type)
            if parameter_type == "bool":
                print("here")
                parameter_edit = QCheckBox()
            else:
                parameter_edit = QLineEdit()
            # parameter_edit = QLineEdit()
            config_form_layout.addRow(key.capitalize() + ":", parameter_edit)
            self.config_instance[key] = parameter_edit
        for key in CONFIG_TUNING.keys():
            parameter_type = CONFIG_TUNING[key]
            if parameter_type == "bool":
                print("here")
                parameter_edit = QCheckBox()
            else:
                parameter_edit = QLineEdit()
            config_form_layout.addRow(key.capitalize() + ":", parameter_edit)
            self.config_tuning[key] = parameter_edit

        self.stack = stack
        layout = QVBoxLayout()
        form_layout = QHBoxLayout()
        form_widget = QWidget()
        form_widget.setLayout(form_layout)

        eco_form_widget = QWidget()
        eco_form_widget.setLayout(eco_form_layout)
        eco_form_widget.setFixedWidth(200)
        form_layout.addWidget(
            eco_form_widget,
            alignment=Qt.AlignmentFlag.AlignHCenter,
        )
        data_form_widget = QWidget()
        data_form_widget.setLayout(data_form_layout)
        data_form_widget.setFixedWidth(200)
        form_layout.addWidget(
            data_form_widget,
            alignment=Qt.AlignmentFlag.AlignHCenter,
        )
        perm_form_widget = QWidget()
        perm_form_widget.setLayout(perm_form_layout)
        perm_form_widget.setFixedWidth(200)
        form_layout.addWidget(
            perm_form_widget,
            alignment=Qt.AlignmentFlag.AlignHCenter,
        )
        config_form_widget = QWidget()
        config_form_widget.setLayout(config_form_layout)
        config_form_widget.setFixedWidth(200)
        form_layout.addWidget(
            config_form_widget,
            alignment=Qt.AlignmentFlag.AlignHCenter,
        )
        layout.addWidget(form_widget)

        button_generate = QPushButton("generate files")
        button_generate.clicked.connect(self.on_button_generate)
        layout.addWidget(button_generate, alignment=Qt.AlignmentFlag.AlignHCenter)

        button_next_window = QPushButton("next")
        button_next_window.clicked.connect(self.on_button_next_window)
        layout.addWidget(button_next_window, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.setLayout(layout)

    def on_button_generate(self):
        self.main_window.generate_file(self.parameters_eco_input, "example_eco.dap")
        self.main_window.generate_file(self.parameters_data_input, "example.dap")
        self.main_window.generate_file(self.parameters_perm_input, "example_perm.dap")
        self.main_window.generate_config(self.config_tuning, self.config_instance)

    def on_button_next_window(self):
        self.stack.setCurrentIndex(PAGE_START)


class MainPage(QWidget):
    def __init__(self, stack):
        super().__init__()
        layout = QVBoxLayout()
        button = QPushButton("Next page")
        button.clicked.connect(lambda: stack.setCurrentIndex(PAGE_START))
        layout.addWidget(button)
        self.setLayout(layout)


class Parameter:
    def __init__(self, type: str):
        self.type = type


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.stack = QStackedWidget()
        self.start_page = StartPage(self.stack)
        self.main_page = MainPage(self.stack)
        self.parameter_page = ParameterPage(self.stack, self)

        self.setWindowTitle("App")
        self.setMinimumSize(600, 400)

        central_widget = QWidget()
        form_layout = QFormLayout()
        central_widget.setLayout(form_layout)
        self.submit_button = QPushButton("Submit", self)
        form_layout.addWidget(self.submit_button)
        self.stack.addWidget(self.main_page)
        self.stack.addWidget(self.start_page)
        self.stack.addWidget(self.parameter_page)
        # self.stack.setCurrentWidget(self.start_page)
        self.stack.setCurrentWidget(self.parameter_page)

        self.setCentralWidget(self.stack)

    def generate_file(self, parameters: dict, filename: str):
        # TODO: default version for eco data
        os.makedirs("data", exist_ok=True)
        filepath = f"data/{filename}"
        with open(filepath, "w") as f:
            for key, value in parameters.items():
                value = parameters[key].text()
                f.write(f"{key} := {value}\n")
            print(f"the file {filepath} was generated successfully")

    def generate_config(self, config_tuning: dict, config_instance: dict):
        os.makedirs("data", exist_ok=True)
        filepath = f"data/config.ini"
        with open(filepath, "w") as f:
            f.write(f"[tuning]\n")
            for key, value in config_tuning.items():
                value = config_tuning[key].text()
                f.write(f"{key} = {value}\n")
            f.write(f"\n[instance]\n")
            for key, value in config_instance.items():
                value = config_instance[key].text()
                f.write(f"{key} = {value}\n")


# TODO: in dap files sometimes values are wrapped with ""

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
