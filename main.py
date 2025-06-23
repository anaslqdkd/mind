from PyQt6.QtWidgets import QApplication

from app.param import debug_print
from app.views import MainWindow, load_configuration


if __name__ == "__main__":
    app = QApplication([])
    main_window = MainWindow()
    main_window.show()
    app.exec()
