import enum
from typing import Optional
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from app.param_enums import FILE, DependencyType
from app.param_validator import LineEditValidation

# -----------------------------------------------------------
class InputValidation:
    @staticmethod
    def validate_input(line_edit: QLineEdit, expected_type: type):
        # TODO: remove the text from the input after warning
        text = line_edit.text().strip()

        if text == "":
            # Empty input is allowed — clear any error state
            line_edit.setStyleSheet("")
            return

        try:
            if expected_type == int:
                value = int(text)
            elif expected_type == float:
                value = float(text)
            else:
                value = text  # fallback to string

            # Example: for float, check range 0-1
            if expected_type == float and not (0 <= value <= 1):
                raise ValueError("Out of range")
            line_edit.setStyleSheet("")  # Valid
        except ValueError:
            line_edit.setStyleSheet("border: 1px solid red;")
            QMessageBox.warning(
                line_edit,
                "Invalid Input",
                f"Please enter a valid {expected_type.__name__}"
                + (" between 0 and 1" if expected_type == float else "")
            )
    @staticmethod
    def check_required(name: str, line_edit: QLineEdit, optional: bool) -> bool:
        if not optional and line_edit.text() == "":
            print(f"Error, the param {name} is not inserted")
            return False
        return True
            # print("Error not all non optional params insterted")

# -----------------------------------------------------------


class Param:
    def __init__(
        self,
        name: str,
        file: FILE,
        depends_on: Optional[dict[str, DependencyType]] = None,
        optional: bool = False,
        expected_type=str,
    ) -> None:
        self.name = name  # the exact name in the data files
        self.category: ParamCategory 
        self.file = file
        self.optional = optional
        self.depends_on_names: dict[str, DependencyType] = depends_on or {}
        self.depends_on_params: dict[Param, DependencyType] = {}
        self.dependants: dict[Param, DependencyType] = {}
        self.expected_type = expected_type

    def build_widget(self, row: int, label: str, grid_layout: QGridLayout):
        raise NotImplementedError("Subclasses must implement build_widgets")

    def store_value(self):
        raise NotImplementedError("Subclasses must implement store_values")

    def row_span(self) -> int:
        return 1
    def to_file(self) -> str:
        raise NotImplementedError("Subclasses must implement to_file")

    def notify_dependants(self) -> None:
        print("In the notify dependants !")


# -----------------------------------------------------------

class ParamInput(Param, LineEditValidation):
    def __init__(self, name: str, file: FILE, depends_on: Optional[dict[str, DependencyType]], optional: bool = False, expected_type=str) -> None:
        super().__init__(name, file, depends_on=depends_on)
        LineEditValidation.__init__(self)
        # TODO: set validation rules when creating the parameter:
        #     param.set_validation(min_value=0, max_value=1, optional=True)
        self.question_label = None
        self.line_edit = None
        self.last_line_edit = ""
        self.file = file
        self.optional = optional
        self.expected_type = expected_type
        pass

    def build_widget(self, row: int, label: str, grid_layout: QGridLayout):
        label = f"{label}{'' if self.optional else ' *'}"
        question_label = QLabel(label)
        line_edit = QLineEdit()

        self.question_label = question_label
        self.line_edit = line_edit

        self.restore_values()
        grid_layout.addWidget(self.question_label, row, 0)
        grid_layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding,
                        QSizePolicy.Policy.Minimum),
            row,
            1,
        )
        grid_layout.addWidget(self.line_edit, row, 2)

        if self.line_edit is not None:
            line_edit = self.line_edit  # local variable guaranteed not None
            expected_type = self.expected_type
            # line_edit.editingFinished.connect(
            #     lambda: InputValidation.validate_input(line_edit, expected_type)
            # )
            # TODO: add this for all input parameters
            self.line_edit.editingFinished.connect(self.validate_and_highlight)


    def validate_and_highlight(self):
        if self.validation_rules == {}:
            return
        print(self.validation_rules)
        text = self.line_edit.text()
        if self.validate_input(text):
            self.line_edit.setStyleSheet("")  # Clear any red border
        else:
            self.line_edit.setStyleSheet("border: 1px solid red;")
            self.show_error_message("Invalid input. Please enter a valid value "
                                    # f"({self.validation_rules['type'].__name__})"
                                    f"{' between ' + str(self.validation_rules['min']) + ' and ' + str(self.validation_rules['max']) if self.validation_rules['min'] is not None and self.validation_rules['max'] is not None else ''}.")

    def show_error_message(self, message: str):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle("Input Error")
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()

    def restore_values(self):
        if self.line_edit is not None:
            self.line_edit.setText(self.last_line_edit)

    def store_value(self):
        if self.line_edit is not None:
            self.last_line_edit = self.line_edit.text()

    def notify_dependants(self) -> None:
        print("TATATATATA")
        print(self.dependants)
        for dep in self.dependants.keys():
            print("the dep before TATATATA", dep)
            dep.on_dependency_updated(self)
        pass

    def to_file(self) -> str:
        return f"{self.name} := {self.last_line_edit}"



# -----------------------------------------------------------

class ParamSelect(Param):
    def __init__(self, name: str, file: FILE, values: list[str], depends_on: Optional[dict[str, DependencyType]], optional: bool = False, expected_type=str) -> None:
        super().__init__(name, file, depends_on=depends_on)
        self.question_label = None
        self.combo_box = None
        self.last_combo_box = ""
        self.values = values
        self.optional = optional
        pass

    def build_widget(self, row: int, label: str, grid_layout: QGridLayout):
        label = f"{label}{'' if self.optional else ' *'}"
        question_label = QLabel(label)
        combo_box = QComboBox()
        combo_box.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        combo_box.addItems(self.values)

        self.question_label = question_label
        self.combo_box = combo_box

        self.restore_values()

        grid_layout.addWidget(self.question_label, row, 0)

        spacer = QSpacerItem(
            0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        grid_layout.addItem(spacer, row, 1)

        grid_layout.addWidget(self.combo_box, row, 2, 1, 2)

    def restore_values(self):
        if self.combo_box:
            index = self.combo_box.findText(self.last_combo_box)
            if index != -1:
                self.combo_box.setCurrentIndex(index)

    def store_value(self):
        if self.combo_box is not None:
            self.last_combo_box = self.combo_box.currentText()
        pass

    def to_file(self) -> str:
        return f"{self.name} := {self.last_combo_box}"


# -----------------------------------------------------------

class ParamBoolean(Param):
    def __init__(self, name: str, file: FILE, depends_on: Optional[dict[str, DependencyType]], optional: bool = False, expected_type=str) -> None:
        super().__init__(name, file, depends_on=depends_on)
        self.question_label = None
        self.check_box = None
        self.last_check_box = False
        self.optional = optional

    def build_widget(self, row: int, label: str, grid_layout: QGridLayout):
        label = f"{label}{'' if self.optional else ' *'}"
        container = QWidget()
        h_layout = QHBoxLayout(container)
        h_layout.setContentsMargins(0, 0, 0, 0)

        check_box = QCheckBox()
        question_label = QLabel(label)

        self.check_box = check_box
        self.question_label = question_label

        self.check_box = check_box

        self.restore_values()
        h_layout.addWidget(self.check_box)
        h_layout.addWidget(self.question_label)
        h_layout.addStretch()

        grid_layout.addWidget(container, row, 0, 1, 2)

    def restore_values(self):
        if self.last_check_box:
            if self.check_box:
                self.check_box.setChecked(True)

    def store_value(self):
        if self.check_box is not None:
            self.last_check_box = self.check_box.isChecked()

    def to_file(self) -> str:
        return f"{self.name} := {self.last_check_box}"

# -----------------------------------------------------------
class ParamInputWithUnity(Param):
    def __init__(self, name: str, file: FILE, values: list[str], depends_on: Optional[dict[str, DependencyType]], optional: bool = False, expected_type=str) -> None:
        super().__init__(name, file = file, depends_on=depends_on)
        self.question_label = None
        self.line_edit = None
        self.combo_box = None

        self.last_line_edit = ""
        self.last_combo_box = ""

        self.values = values
        self.optional = optional
        pass

    def build_widget(self, row: int, label: str, grid_layout: QGridLayout):
        label = f"{label}{'' if self.optional else ' *'}"
        question_label = QLabel(label)
        line_edit = QLineEdit()
        combo_box = QComboBox()
        combo_box.addItems(self.values)
        grid_layout.addWidget(question_label, row, 0)
        grid_layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding,
                        QSizePolicy.Policy.Minimum),
            row,
            1,
        )
        self.line_edit = line_edit
        self.combo_box = combo_box

        self.restore_value()

        grid_layout.addWidget(self.line_edit, row, 2)
        grid_layout.addWidget(self.combo_box, row, 3)

    def restore_value(self):
        if self.last_combo_box:
            if self.combo_box:
                index = self.combo_box.findText(self.last_combo_box)
                if index != -1:
                    self.combo_box.setCurrentIndex(index)
        if self.last_line_edit:
            if self.line_edit:
                self.line_edit.setText(self.last_line_edit)

    def store_value(self):
        if self.line_edit is not None:
            self.last_line_edit = self.line_edit.text()
            pass
        if self.combo_box is not None:
            self.last_combo_box = self.combo_box.currentText()
        pass

    def to_file(self) -> str:
        return f"{self.name} := {self.last_line_edit} #{self.last_combo_box}"

# -----------------------------------------------------------
class ParamBooleanWithInput(Param):
    def __init__(self, name: str, file: FILE, depends_on: Optional[dict[str, DependencyType]], optional:bool = False, expected_type=str) -> None:
        super().__init__(name, file, depends_on=depends_on)
        self.question_label = None
        self.line_edit = None
        self.check_box = None

        self.last_check_box = False
        self.last_line_edit = ""

        self.optional = optional
        pass

    def build_widget(self, row: int, label: str, grid_layout: QGridLayout):
        label = f"{label}{'' if self.optional else ' *'}"
        checkbox_container = QWidget()
        checkbox_layout = QHBoxLayout(checkbox_container)
        checkbox_layout.setContentsMargins(0, 0, 0, 0)
        checkbox_layout.setSpacing(5)

        check_box = QCheckBox()
        question_label = QLabel(label)

        line_edit = QLineEdit()
        line_edit.setEnabled(False)

        checkbox_layout.addWidget(check_box)
        checkbox_layout.addWidget(question_label)
        checkbox_layout.addStretch()

        self.line_edit = line_edit
        self.check_box = check_box

        self.restore_values()

        grid_layout.addWidget(checkbox_container, row, 0, 1, 2)

        t_label = QLabel(label)

        check_box.toggled.connect(line_edit.setEnabled)

        grid_layout.addWidget(t_label, row + 1, 0)
        grid_layout.addWidget(line_edit, row + 1, 2)

    def restore_values(self):
        if self.last_check_box:
            if self.check_box:
                self.check_box.setChecked(True)
            if self.line_edit:
                self.line_edit.setEnabled(True)
        if self.last_line_edit:
            if self.line_edit:
                self.line_edit.setText(self.last_line_edit)

    def store_value(self):
        if self.line_edit is not None:
            self.last_line_edit = self.line_edit.text()
        if self.check_box is not None:
            self.last_check_box = self.check_box.isChecked()

    def row_span(self) -> int:
        return 2

    def to_file(self) -> str:
        return f"{self.name} := {self.last_check_box}\n{self.name} := {self.last_line_edit}"


# -----------------------------------------------------------

class ParamBooleanWithInputWithUnity(Param):
    def __init__(self, name: str, file: FILE, values: list[str], depends_on: Optional[dict[str, DependencyType]], optional: bool = False, expected_type=str) -> None:
        super().__init__(name, file, depends_on = depends_on)
        self.question_label = None
        self.check_box = None
        self.combo_box = None
        self.line_edit = None

        self.last_check_box = False
        self.last_combo_box = ""
        self.last_line_edit = ""

        self.optional = optional

        self.values = values

    def build_widget(self, row: int, label: str, grid_layout: QGridLayout):
        label = f"{label}{'' if self.optional else ' *'}"
        checkbox_container = QWidget()
        checkbox_layout = QHBoxLayout(checkbox_container)
        checkbox_layout.setContentsMargins(0, 0, 0, 0)
        checkbox_layout.setSpacing(5)

        check_box = QCheckBox()
        question_label = QLabel(label)

        combo_box = QComboBox()
        combo_box.addItems(self.values)

        line_edit = QLineEdit()
        line_edit.setEnabled(False)
        check_box.toggled.connect(line_edit.setEnabled)

        self.check_box = check_box
        self.combo_box = combo_box
        self.line_edit = line_edit

        self.restore_values()

        checkbox_layout.addWidget(check_box)
        checkbox_layout.addWidget(question_label)
        checkbox_layout.addStretch()

        grid_layout.addWidget(checkbox_container, row, 0, 1, 2)

        t_label = QLabel(label)

        grid_layout.addWidget(t_label, row + 1, 0)
        spacer = QWidget()
        grid_layout.addWidget(spacer, row + 1, 1)
        grid_layout.addWidget(line_edit, row + 1, 2)
        grid_layout.addWidget(combo_box, row + 1, 3)

    def restore_values(self):
        if self.last_check_box:
            if self.check_box:
                self.check_box.setChecked(True)
        if self.line_edit:
            self.line_edit.setText(self.last_line_edit)
        if self.last_combo_box:
            if self.combo_box:
                index = self.combo_box.findText(self.last_combo_box)
                if index != -1:
                    self.combo_box.setCurrentIndex(index)

    def store_value(self):
        if self.combo_box is not None:
            self.last_combo_box = self.combo_box.currentText()
        if self.check_box is not None:
            self.last_check_box = self.check_box.isChecked()
        if self.line_edit is not None:
            self.last_line_edit = self.line_edit.text()


    def row_span(self) -> int:
        return 2

    def to_file(self) -> str:
        return f"{self.name} := {self.last_check_box}\n{self.name} := {self.last_line_edit} #{self.last_combo_box}"
# -----------------------------------------------------------

class ParamComponent(Param):
    def __init__(self, name: str, file: FILE, values: list[str], depends_on:Optional[dict[str, DependencyType]], optional: bool = False, expected_type=str) -> None:
        super().__init__(name, file, depends_on=depends_on)
        self.question_label = None
        self.combo_box = None
        self.extra_rows = 0

        self.combo_boxes = []
        self.last_combo_boxes = []
        self.optional = optional
        self.values = values

    def build_widget(self, row: int, label: str, grid_layout: QGridLayout):
        label = f"{label}{'' if self.optional else ' *'}"
        question_label = QLabel(label)
        grid_layout.addWidget(question_label, row, 0)
        self.combo_boxes = []

        # update method
        # FIXME: move this to a restore value function
        if self.extra_rows > 0:
            for i in range(self.extra_rows):
                combo = QComboBox()
                combo.setPlaceholderText("Extra input")
                combo.addItems(self.values)
                combo.setCurrentText(self.last_combo_boxes[i])
                combo.setSizePolicy(QSizePolicy.Policy.Expanding,
                                    QSizePolicy.Policy.Fixed)
                remove_button = QPushButton("✕")
                remove_button.setFixedWidth(30)
                remove_button.clicked.connect(
                lambda _, c=combo, b=remove_button: self.remove_widget_pair(c, b, grid_layout)
            )
                grid_layout.addWidget(combo, row, 2)
                grid_layout.addWidget(remove_button, row, 3)
                self.combo_boxes.append(combo)

                row += 1

        extra_combo = QComboBox()
        extra_combo.setPlaceholderText("Extra input")
        extra_combo.addItems(self.values)
        self.combo_boxes.append(extra_combo)
        grid_layout.addWidget(extra_combo, row, 2)
        extra_combo.currentIndexChanged.connect(lambda : self.add_component_row(row, grid_layout))


    def add_component_row(self, row: int, grid_layout: QGridLayout):
        self.component_base_row = row
        self.extra_rows += 1

        combo = QComboBox()
        combo.setPlaceholderText("Extra input")
        combo.addItems(["Item 1", "Item 2", "Item 3"])
        combo.setSizePolicy(QSizePolicy.Policy.Expanding,
                            QSizePolicy.Policy.Fixed)
        self.combo_boxes.append(combo)

        remove_button = QPushButton("✕")
        remove_button.setFixedWidth(30)

        grid_layout.addWidget(combo, row + 1, 2)
        grid_layout.addWidget(remove_button, row + 1, 3)


        combo.currentIndexChanged.connect(lambda: self.add_component_row(row + 1, grid_layout))

        self.category.update_category()

    def store_value(self):
        self.last_combo_boxes.clear()
        for el in self.combo_boxes:
            self.last_combo_boxes.append(el.currentText())

    def remove_widget_pair(self, widget1: QWidget, widget2: QWidget, layout: QGridLayout):
        layout.removeWidget(widget1)
        layout.removeWidget(widget2)
        widget1.deleteLater()
        widget2.deleteLater()

        self.extra_rows = max(0, self.extra_rows - 1)
        self.category.update_category()

    def row_span(self) -> int:
        return 1 + self.extra_rows

    def to_file(self) -> str:
        value = ""
        for el in self.last_combo_boxes:
            value += f"\"{el}\" "

        return f"{self.name} := {value}\n"

# -----------------------------------------------------------
class ParamFixedWithInput(Param):
    def __init__(self, name: str, file: FILE, depends_on: Optional[dict[str, DependencyType]], optional: bool = False, expected_type=str) -> None:
        super().__init__(name, file = file, depends_on = depends_on)
        self.question_label = None
        self.line_edit = None
        self.combo_box = None

        self.last_line_edit = ""
        self.last_combo_box = ""

        self.optional = optional
        self.rows = 0
        pass

    def build_widget(self, row: int, label: str, grid_layout: QGridLayout):
        self.row = row
        self.label = label
        self.grid_layout = grid_layout
        label = f"{label}{'' if self.optional else ' *'}"
        question_label = QLabel(label)
        line_edit = QLineEdit()
        grid_layout.addWidget(question_label, row, 0)
        for i in range(self.rows):
            # FIXME: clear the grid before
            combo_box = QComboBox()
            grid_layout.addWidget(combo_box, self.row, 1)
            self.row += 1
        grid_layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding,
                        QSizePolicy.Policy.Minimum),
            row,
            1,
        )
        self.line_edit = line_edit

        self.restore_value()

        grid_layout.addWidget(self.line_edit, row, 2)

    def restore_value(self):
        if self.last_combo_box:
            if self.combo_box:
                index = self.combo_box.findText(self.last_combo_box)
                if index != -1:
                    self.combo_box.setCurrentIndex(index)
        if self.last_line_edit:
            if self.line_edit:
                self.line_edit.setText(self.last_line_edit)

    def store_value(self):
        if self.line_edit is not None:
            self.last_line_edit = self.line_edit.text()
            pass
        if self.combo_box is not None:
            self.last_combo_box = self.combo_box.currentText()
        pass

    def to_file(self) -> str:
        return f"{self.name} := {self.last_line_edit} #{self.last_combo_box}"

    def on_dependency_updated(self, changed_param:Param):
        print("%%%%: in the dependency updated", changed_param.name)
        # print(self.dep)
        # for el in self.
        if changed_param in self.depends_on_params.keys():
            print("YAAAA")
        for param, dependency_type in self.depends_on_params.items():
            match dependency_type:
                case DependencyType.COMPONENT_COUNT:
                    # FIXME: retrieve method in each because some parameters may not have a line edit + call the update method or store method
                    # TODO: clear the grid before

                    print("6666666", param.last_line_edit)
                    
                    try:
                        self.rows = int(param.last_line_edit)
                        self.build_widget(self.row, self.label, self.grid_layout)
                    except (ValueError, TypeError):
                        print(f"Invalid integer input: {param.last_line_edit}")


        # match 
        print(f"{self.name} updated because the dependant {changed_param.name} changed")


# -----------------------------------------------------------

class ParamCategory(QWidget):
    def __init__(self, name: str, param: dict["str", Param]) -> None:
        super().__init__()
        layout = QVBoxLayout()
        self.name = name
        self.setLayout(layout)
        self.param = param
        self.row = 0

        self.component_widgets = []
        self.components_index = []
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.label = QLabel(f"{name}")
        self.extra_rows = 0

        self.test_button = QPushButton("Test")

        # self.combo_boxes = []
        self.label.setStyleSheet(
            """
            font-weight: bold;
            font-size: 14px;
            color: #000;
"""
        )
        layout.addWidget(self.label)
        layout.addWidget(self.grid_widget)

        # test button
        self.test_button.setFixedWidth(50)
        self.test_button.clicked.connect(self.notify_dependents)
        layout.addWidget(self.test_button)


        self.build_param()

    def notify_dependents(self):
        for name, param in self.param.items():
            param.notify_dependants()

    def build_param(self) -> QWidget:
        self.row = 0
        for label, param_obj in self.param.items():
            param_obj.build_widget(self.row, label, self.grid_layout)
            self.row += param_obj.row_span()
        return self

    def store_values(self):
        for name, param in self.param.items():
            param.store_value()

    def update_category(self):
        self.store_values()
        self.clear_grid_layout()
        self.build_param()
        self.write_to_file()

    def clear_grid_layout(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)
                    widget.deleteLater()

    def write_to_file(self):
        file_map = {
            FILE.DATA: "data.dat",
            FILE.CONFIG: "config.ini",
            FILE.PERM: "perm.dat",
            FILE.ECO: "eco.dat",
            FILE.COMMAND: "command.sh"
        }
        used_files = {file_map[param.file] for param in self.param.values() if param.file in file_map}
        for file_name in used_files:
            open(file_name, "w").close()

        for _, param in self.param.items():
            file_name = file_map.get(param.file)
            if not file_name:
                print(f"Unknown file type for param {param.name}")
            else:
                with open(file_name, "a") as f:
                    value = param.to_file()
                    if value != "":
                        f.write(f"{value}\n")

