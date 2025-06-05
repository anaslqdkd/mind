from PyQt6.QtWidgets import QApplication
from app.controllers import MainController
from app.views import MainWindow

# from app.views import

if __name__ == "__main__":
    app = QApplication([])
    # model = Parameters()
    # param_page = ParameterPage()
    # controller = ParameterController(model, param_page)
    main_window = MainWindow()
    main_controller = MainController(main_window)
    # parameter_page = ParameterPage(main_window)
    main_window.show()
    app.exec()
