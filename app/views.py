from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
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
    QVBoxLayout,
    QWidget,
)

from app.param import InputValidation, Param, ParamCategory
from app.param_factory import set_param
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

        # pages
        param_page1 = set_param(all_params)
        param_page2 = set_param(all_params)

        self.page1 = PageParameters(self, param_page1, self.stack, self.sidebar)
        self.page_components = PageParameters(
            self, param_page2, self.stack, self.sidebar
        )

        self.main_area = QWidget()
        tab1_layout = QHBoxLayout(self.main_area)
        header = QLabel("Main Area Header")

        layout = QVBoxLayout()
        layout.addWidget(header)
        layout.addWidget(self.tabs)

        button = QPushButton("A propos")
        quit_button = QPushButton("Fermer")
        apply_button = QPushButton("Appliquer")

        end_buttons = QWidget()
        end_buttons_layout = QHBoxLayout(end_buttons)
        end_buttons_layout.addWidget(button)
        spacer = QSpacerItem(
            0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        end_buttons_layout.addSpacerItem(spacer)
        end_buttons_layout.addStretch()
        end_buttons_layout.addWidget(quit_button)
        end_buttons_layout.addWidget(apply_button)

        layout.addWidget(end_buttons)
        tab1_layout.addWidget(self.sidebar)
        tab1_layout.addWidget(self.page1)
        tab1_layout.addWidget(self.stack)
        tab1_layout.addStretch()

        self.stack.addWidget(self.page1)
        self.stack.addWidget(self.page_components)
        self.sidebar.currentRowChanged.connect(self.stack.setCurrentIndex)

        self.tab1.setLayout(tab1_layout)
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)


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

        main_layout = QVBoxLayout()

        content_layout = QVBoxLayout()
        content_widget = QWidget()
        content_widget.setLayout(content_layout)

        tab1_widget = QWidget()
        # self.tab_widget.addTab(QWidget(), "Tab 2")
        tab1_layout = QVBoxLayout(tab1_widget)

        for key, value in param_category.items():
            ex_params = ParamCategory(key, value)
            for name, param in value.items():
                param.category = ex_params
            # main_layout.addWidget(ex_params)
            tab1_layout.addWidget(ex_params)
            # self.tab_widget.addTab(ex_params, key)
        self.tab_widget = QTabWidget()
        self.tab_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.tab_widget.addTab(tab1_widget, "Tab 1")
        self.tab_widget.addTab(QWidget(), "Tab 2")  # Placeholder for Tab 2
        # main_layout.addWidget(self.tab_widget, stretch=1)
        main_layout.addWidget(self.tab_widget, 0, Qt.AlignmentFlag.AlignTop)

        next_button = QPushButton("next")

        end_button_widget = QWidget()
        end_button_layout = QHBoxLayout(end_button_widget)
        end_button_layout.addStretch()
        next_button.clicked.connect(self.go_to_next_page)
        end_button_layout.addWidget(next_button)
        main_layout.addWidget(end_button_widget)

        main_layout.addStretch()

        self.setLayout(main_layout)

    # TODO: move this to the validator class
    def go_to_next_page(self):
        # TODO: trigger errors for not optional values
        print("the rest of validate_all_input", self.validate_all_input())
        if self.validate_required_params():
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
        else:
            # TODO: put in red all parameters that are non optional and not selected
            for category in self.param_category.values():
                for param in category.values():
                    if isinstance(param, NonOptionalInputValidation):
                        if not param.is_filled():
                            line_edit = param.line_edit
                            line_edit.setStyleSheet("border: 1px solid red")
            QMessageBox.warning(
                self, "text" "Invalid Input", f"Please input all required forms"
            )

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
