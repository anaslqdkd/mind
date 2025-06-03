from PyQt6.QtWidgets import (
    QFormLayout,
    QLineEdit,
    QMainWindow,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
import sys
from PyQt6.QtWidgets import QApplication


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("App")
        self.setMinimumSize(600, 400)

        central_widget = QWidget()
        form_layout = QFormLayout()
        self.param1_input = QLineEdit()
        self.param2_input = QLineEdit()
        self.param3_input = QLineEdit()
        form_layout.addRow("Parameter 1:", self.param1_input)
        form_layout.addRow("Parameter 2:", self.param2_input)
        form_layout.addRow("Parameter 3:", self.param3_input)
        central_widget.setLayout(form_layout)
        self.submit_button = QPushButton("Submit", self)
        self.submit_button.clicked.connect(self.generate_file)
        self.submit_button.clicked.connect(self.generate_file_eco)
        self.submit_button.clicked.connect(self.generate_file_perm)
        form_layout.addWidget(self.submit_button)

        self.setCentralWidget(central_widget)

    def generate_file(self):
        param1 = self.param1_input.text()

        with open("data/file_eco.dap", "w") as f:
            f.write(f"param pressure_in := {param1};\n")
        print("the file file_eco.dap was generated successfully")

    def generate_file_eco(self):
        param2 = self.param2_input.text()

        with open("data/file_perm.dap", "w") as f:
            f.write(f"param pressure_in := {param2};\n")
        print("the file file_perm.dap was generated successfully")

    def generate_file_perm(self):
        param3 = self.param3_input.text()

        with open("data/file.dap", "w") as f:
            f.write(f"param pressure_in := {param3};\n")
        print("the file file.dap was generated successfully")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
