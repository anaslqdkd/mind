import enum
from PyQt6.QtCore import QLine
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
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
from app.param import FILE, DependencyType, InputValidation, LineEditValidation, Param, ParamBoolean, ParamBooleanWithInput, ParamBooleanWithInputWithUnity, ParamCategory, ParamComponent, ParamFixedWithInput, ParamInput, ParamInputWithUnity, ParamSelect, ParamType

# TODO: same but for actual input types
# TODO: close button verification before quitting, to abort modifs

# -----------------------------------------------------------

def create_param(name: str, param_type: ParamType, file: FILE, **kwargs) -> Param:
    optional = kwargs.get("optional", False)
    values = kwargs.get("values", [])
    depends_on = kwargs.get("depends_on", [])
    expected_type = kwargs.get("expected_type", str) 
    print("the expected type in create param is", expected_type)
    match param_type:
        case ParamType.INPUT:
            return ParamInput(name, optional=optional, file=file, depends_on = depends_on, expected_type=expected_type)
        case ParamType.SELECT:
            return ParamSelect(name, file=file, values=values, depends_on = depends_on, expected_type=expected_type)
        case ParamType.BOOLEAN:
            return ParamBoolean(name, file, depends_on = depends_on, expected_type=expected_type)
        case ParamType.INPUT_WITH_UNITY:
            return ParamInputWithUnity(name, file=file, values = values, depends_on = depends_on, expected_type=expected_type)
        case ParamType.BOOLEAN_WITH_INPUT:
            return ParamBooleanWithInput(name, file, depends_on = depends_on, expected_type=expected_type)
        case ParamType.BOOLEAN_WITH_INPUT_WITH_UNITY:
            return ParamBooleanWithInputWithUnity(name, file = file, values = values, depends_on = depends_on, expected_type=expected_type)
        case ParamType.COMPONENT:
            return ParamComponent(name, file, values = values, depends_on = depends_on, expected_type=expected_type)
        case ParamType.FIXED_WITH_INPUT:
            return ParamFixedWithInput(name, file, depends_on = depends_on, expected_type=expected_type)
        case _:
            raise ValueError(f"Unsupported param type: {param_type}")



# -----------------------------------------------------------

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
        param_page1 = self.set_param()
        param_page2 = self.set_param2()
        self.page1 = PageParameters(self, param_page1, self.stack, self.sidebar)
        self.page_components = PageParameters(self, param_page2, self.stack, self.sidebar)

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

    def set_param(self):
        algo_params = {
            "num_membranes": 
                create_param(name="num_membranes", param_type=ParamType.INPUT, file = FILE.DATA, optional = False, expected_type=int)
            ,
            "Another one": 
                create_param(name="idk", param_type=ParamType.INPUT, file = FILE.DATA, expected_type=int)
            ,
            "Select test": 
                create_param(name="select", param_type=ParamType.SELECT, values=["multistart", "mbh", "global", "population", "genetic"], file = FILE.DATA)
            ,
            "Bool test": 
                create_param(name="check", param_type=ParamType.BOOLEAN, file = FILE.DATA)
            ,
            "Input with unity test": 
                create_param(name="input with unity", param_type=ParamType.INPUT_WITH_UNITY, values=["bar", "Pa", "kPa"], file = FILE.DATA)
            ,
            "Boolean with input test": 
                create_param(name="boolean with input", param_type=ParamType.BOOLEAN_WITH_INPUT, file = FILE.DATA)
            ,
            "Boolean with input and unity": 
                create_param(name="boolean with input and unity", param_type=ParamType.BOOLEAN_WITH_INPUT_WITH_UNITY, values=["option 1", "option 2", "option 3"], file = FILE.DATA)
            ,
            "Component": 
                create_param(name="component test", param_type=ParamType.COMPONENT, file = FILE.DATA, values=["H2O", "H2", "CO2"])
            ,
            "Another flds": 
            create_param(name="bu", param_type=ParamType.FIXED_WITH_INPUT, file = FILE.DATA, depends_on = {"num_membranes": DependencyType.COMPONENT_COUNT}, expected_type=int)
            ,
        }
        param = {
        }

        for key, value in algo_params.items():
            # FIXME: put this in a function, and get the param name not the label
            depends_on = getattr(value, "depends_on", None)
            if not depends_on:
                continue
            for el in value.depends_on_names:
                print("the value.name is", el)
                dep_param = algo_params.get(el)
                if dep_param:
                    print("here")
                    print(dep_param.name)
                    dep_type = value.depends_on.get(el)
                    value.depends_on_params[dep_param] = dep_type
                    if not hasattr(dep_param, "dependants"):
                        dep_param.dependants = {}
                    dep_param.dependants[value] = dep_type

        for key, value in algo_params.items():
            # print("++++", value.depends_on_names)
            depends_on = getattr(value, "depends_on_names", None)
            if not depends_on:
                # print("°))) here")
                continue
            for dep_name, dep_type in value.depends_on_names.items():
                # print("TTTTTT")
                dep_param = algo_params.get(dep_name)
                print(dep_param)
                if dep_param:
                    print(f"Dependency found: {dep_name} → {dep_type}")
                    value.depends_on_params[dep_param] = dep_type
                    if not hasattr(dep_param, "dependants"):
                        dep_param.dependants = {}
                    dep_param.dependants[value] = dep_type
        def apply_validation_rules(param: Param, rules: dict):
            if isinstance(param, LineEditValidation):
                param.set_validation(**rules)

        for key, value in algo_params.items():
            print(value.name)
            if value.name == "num_membranes":
                apply_validation_rules(value, {"min_value":1, "max_value":2})
                # if isinstance(value, LineEditValidation):
                #     value.set_validation(min_value=1, max_value=10)
                #     print("the param validation rules are: ++++", value.validation_rules)


        # FIXME: refactor with: 
        #     def apply_validation_rules(param: Param, rules: dict):
        #         if isinstance(param, LineEditValidationMixin):
        #             param.set_validation(**rules)
        # then use with 
        # apply_validation_rules(param, {"min_value": 0, "max_value": 1, "expected_type": float})


        # for name, param in  algo_params.items():
        #     print("buu")
        #     for dep_name in param.depends_on_names:
        #         dep_param = algo_params.get(dep_name)
        #         if dep_param:
        #             param.depens_on_params.append(dep_param)
        param_page1 = {"Algorithm parameters": algo_params,
                       "Other parameters": param}
        return param_page1
    def set_param2(self):
        algo_params = {
            "gaga": 
                create_param(name="num_membranes", param_type=ParamType.INPUT, file = FILE.DATA, optional = True, expected_type=int)
            ,
            "Another one": 
                create_param(name="idk", param_type=ParamType.INPUT, file = FILE.DATA)
            ,
            "Select test": 
                create_param(name="select", param_type=ParamType.SELECT, values=["multistart", "mbh", "global", "population", "genetic"], file = FILE.DATA)
            ,
            "Bool test": 
                create_param(name="check", param_type=ParamType.BOOLEAN, file = FILE.DATA)
            ,
            "Input with unity test": 
                create_param(name="input with unity", param_type=ParamType.INPUT_WITH_UNITY, values=["bar", "Pa", "kPa"], file = FILE.DATA)
            ,
            "Boolean with input test": 
                create_param(name="boolean with input", param_type=ParamType.BOOLEAN_WITH_INPUT, file = FILE.DATA)
            ,
            "Boolean with input and unity": 
                create_param(name="boolean with input and unity", param_type=ParamType.BOOLEAN_WITH_INPUT_WITH_UNITY, values=["option 1", "option 2", "option 3"], file = FILE.DATA)
            ,
            "Component": 
                create_param(name="component test", param_type=ParamType.COMPONENT, file = FILE.DATA, values=["H2O", "H2", "CO2"])
            ,
            "Another flds": 
            create_param(name="bu", param_type=ParamType.FIXED_WITH_INPUT, file = FILE.DATA, depends_on = {"num_membranes": DependencyType.COMPONENT_COUNT}, expected_type=int)
            ,
        }
        param = {
        }

        for key, value in algo_params.items():
            # FIXME: put this in a function, and get the param name not the label
            depends_on = getattr(value, "depends_on", None)
            if not depends_on:
                continue
            for el in value.depends_on_names:
                print("the value.name is", el)
                dep_param = algo_params.get(el)
                if dep_param:
                    print("here")
                    print(dep_param.name)
                    dep_type = value.depends_on.get(el)
                    value.depends_on_params[dep_param] = dep_type
                    if not hasattr(dep_param, "dependants"):
                        dep_param.dependants = {}
                    dep_param.dependants[value] = dep_type

        for key, value in algo_params.items():
            # print("++++", value.depends_on_names)
            depends_on = getattr(value, "depends_on_names", None)
            if not depends_on:
                # print("°))) here")
                continue
            for dep_name, dep_type in value.depends_on_names.items():
                # print("TTTTTT")
                dep_param = algo_params.get(dep_name)
                print(dep_param)
                if dep_param:
                    print(f"Dependency found: {dep_name} → {dep_type}")
                    value.depends_on_params[dep_param] = dep_type
                    if not hasattr(dep_param, "dependants"):
                        dep_param.dependants = {}
                    dep_param.dependants[value] = dep_type


        # for name, param in  algo_params.items():
        #     print("buu")
        #     for dep_name in param.depends_on_names:
        #         dep_param = algo_params.get(dep_name)
        #         if dep_param:
        #             param.depens_on_params.append(dep_param)
        param_page1 = {"Algorithm parameters": algo_params,
                       "Other parameters": param}
        return param_page1


class PageParameters(QWidget):
    def __init__(
            self, main_window, param_category: dict["str", dict[str, Param]], stack: QStackedWidget, sidebar: QListWidget
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

        for key, value in param_category.items():
            ex_params = ParamCategory(key, value)
            for name, param in value.items():
                param.category = ex_params
            main_layout.addWidget(ex_params)

        next_button = QPushButton("next")

        end_button_widget = QWidget()
        end_button_layout = QHBoxLayout(end_button_widget)
        end_button_layout.addStretch()
        next_button.clicked.connect(self.go_to_next_page)
        end_button_layout.addWidget(next_button)
        main_layout.addWidget(end_button_widget)


        main_layout.addStretch()

        self.setLayout(main_layout)

# TODO: button radio
# TODO: window for component selection

    def go_to_next_page(self):
        # TODO: trigger errors for not optional values
        if self.validate_required_params():
            current_index = self.sidebar.currentRow()
            count = self.sidebar.count()
            next_index = (current_index + 1) % count
            self.sidebar.setCurrentRow(next_index)
        else:
            # TODO: put in red all parameters that are non optional and not selected
            for category in self.param_category.values():
                for param in category.values():
                    if not getattr(param, "optional", False):
                        if hasattr(param, "line_edit"):
                            if param.line_edit.text() == "":
                                line_edit = param.line_edit
                                line_edit.setStyleSheet("border: 1px solid red;")
                                print("pb")
            QMessageBox.warning(
                self,
                "text"
                "Invalid Input",
                f"Please input all forms"
            )


    def validate_required_params(self):
        for category in self.param_category.values():
            for param in category.values():
                if not getattr(param, "optional", False):
                    # TODO: validate input (or another function that checks if there is input)
                    # if has line input
                    if hasattr(param, "line_edit"):
                        # InputValidation.validate_input(param.line_edit, param.expected_type)
                        InputValidation.check_required(param.name, param.line_edit, param.optional)
                        
