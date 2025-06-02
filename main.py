from PyQt6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget
import sys
from PyQt6.QtWidgets import QApplication


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("App")
        self.setMinimumSize(600, 400)

        label = QLabel("Bonjour ?")

        layout = QVBoxLayout()
        layout.addWidget(label)

        central_widget = QWidget()
        central_widget.setLayout(layout)

        self.setCentralWidget(central_widget)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
