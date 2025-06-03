import os
from PyQt6.QtGui import QWindow
from PyQt6.QtWidgets import (
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

PARAMETERS_ECO = [
    "param R ",
    "param phi ",
    "param T ",
    "param gamma ",
    "param C_cp ",
    "param C_exp ",
    "param C_vp ",
    "param eta_cp ",
    "param K_mr ",
    "param K_gp ",
    "param K_m ",
    "param K_mf ",
    "param K_el ",
    "param t_op ",
    "param MFc ",
    "param nu ",
    "param UF_2000 ",
    "param UF_1968 ",
    "param MPFc ",
    "param i",
    "param z",
    "param eta_vp_1",
    "param eta_vp_0",
]

PARAMETERS_DATA = [
    "param pressure_in",
    "set components",
    "param ub_perc_waste",
    "param lb_perc_prod",
    "param normalized_product_qt",
    "param final_product",
    "param FEED",
    "param XIN",
    "param molarmass",
    "param ub_press_down",
    "param ib_press_down",
    "param ib_press_up",
    "param ub_press_up",
]

PARAMETERS_PERM = [
    "set mem_type_set",
    "param nb_gas",
    "param Permeability",
    "param thickness",
    "param mem_product",
]


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
        form_widget.setFixedWidth(300)
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
        self.parameters_eco = {}
        self.parameters_data = {}
        self.parameters_perm = {}

        eco_form_layout = QFormLayout()
        data_form_layout = QFormLayout()
        perm_form_layout = QFormLayout()

        for key in PARAMETERS_ECO:
            parameter_edit = QLineEdit()
            eco_form_layout.addRow(key.capitalize() + ":", parameter_edit)
            self.parameters_eco[key] = parameter_edit
        for key in PARAMETERS_DATA:
            parameter_edit = QLineEdit()
            data_form_layout.addRow(key.capitalize() + ":", parameter_edit)
            self.parameters_data[key] = parameter_edit
        for key in PARAMETERS_PERM:
            parameter_edit = QLineEdit()
            perm_form_layout.addRow(key.capitalize() + ":", parameter_edit)
            self.parameters_perm[key] = parameter_edit

        self.stack = stack
        layout = QVBoxLayout()
        form_layout = QHBoxLayout()
        form_widget = QWidget()
        form_widget.setLayout(form_layout)

        eco_form_widget = QWidget()
        eco_form_widget.setLayout(eco_form_layout)
        eco_form_widget.setFixedWidth(300)
        form_layout.addWidget(
            eco_form_widget,
            alignment=Qt.AlignmentFlag.AlignHCenter,
        )
        data_form_widget = QWidget()
        data_form_widget.setLayout(data_form_layout)
        data_form_widget.setFixedWidth(300)
        form_layout.addWidget(
            data_form_widget,
            alignment=Qt.AlignmentFlag.AlignHCenter,
        )
        perm_form_widget = QWidget()
        perm_form_widget.setLayout(perm_form_layout)
        perm_form_widget.setFixedWidth(300)
        form_layout.addWidget(
            perm_form_widget,
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
        self.main_window.generate_file(self.parameters_eco, "example_eco.dap")
        self.main_window.generate_file(self.parameters_data, "example.dap")
        self.main_window.generate_file(self.parameters_perm, "example_perm.dap")

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
        os.makedirs("data", exist_ok=True)
        filepath = f"data/{filename}"
        with open(filepath, "w") as f:
            for key, value in parameters.items():
                value = parameters[key].text()
                f.write(f"{key} := {value}\n")
            print(f"the file {filepath} was generated successfully")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
