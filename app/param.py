import enum
from typing import Optional, Tuple
from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QAction, QTabletEvent
from PyQt6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QToolTip,
    QVBoxLayout,
    QWidget,
)
import inspect

from app.param_enums import FILE, DependencyType
from app.param_validator import LineEditValidation, NonOptionalInputValidation

def debug_print(*args, **kwargs):
    frame = inspect.currentframe().f_back
    func_name = frame.f_code.co_name
    line_no = frame.f_lineno
    print(f"[{func_name}:{line_no}]", *args, **kwargs)

# -----------------------------------------------------------
class SquareCheckboxSelector(QDialog):
    def __init__(self, components, selected=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Components")
        self.setFixedSize(300, 400)

        self.selected = selected or []

        layout = QVBoxLayout()
        self.checkboxes = []

        for comp in components:
            checkbox = QCheckBox(comp)
            checkbox.setChecked(comp in self.selected)
            self.checkboxes.append(checkbox)
            layout.addWidget(checkbox)

        layout.addStretch()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)
        self.setLayout(layout)

    def get_selected(self):
        # print(selected)
        for cb in self.checkboxes:
            if cb.isChecked():
                self.selected.append(cb.text())

        return [cb.text() for cb in self.checkboxes if cb.isChecked()]


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
                + (" between 0 and 1" if expected_type == float else ""),
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
        description: str = ""
    ) -> None:
        self.name = name  # the exact name in the data files
        self.category: ParamCategory
        self.file = file
        self.optional = optional
        self.depends_on_names: dict[str, DependencyType] = depends_on or {}
        self.depends_on_params: dict[Param, DependencyType] = {}
        self.dependants: dict[Param, DependencyType] = {}
        self.expected_type = expected_type
        self.description = description

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

    def to_command_arg(self) -> str:
        return ""

    def to_file_entry(self):
        return ""

    to_config_entry = to_file_entry

    def build_header(self, label: str, description: str, optional: bool) -> QWidget:
        header_container = QWidget()
        header_layout = QHBoxLayout(header_container)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        header_layout.setContentsMargins(0, 0, 0, 0)
        label_text = f'{label}{" " if optional else " <span style=\"color:red;\">*</span>"}'
        question_label = QLabel(label_text)
        icon_label = HelpButtonDemo(description)
        header_layout.addWidget(question_label)
        header_layout.addWidget(icon_label)
        return header_container

    # def trigger_update(self) -> None:
    #     self.category.update_category()


# -----------------------------------------------------------


class ParamInput(Param, LineEditValidation, NonOptionalInputValidation):
    def __init__(
        self,
        name: str,
        file: FILE,
        depends_on: Optional[dict[str, DependencyType]],
        optional: bool = False,
        expected_type=str,
        description: str = "",
        default: Optional[int] =None,
        min_value: Optional[int] = None,
        max_value: Optional[int] =None,
        step: Optional[int]= None,
        hidden: bool = False,
    ) -> None:
        super().__init__(name, file, depends_on=depends_on, description=description)
        LineEditValidation.__init__(self)
        self.question_label = None
        self.line_edit = None
        self.last_line_edit = ""
        self.file = file
        self.optional = optional
        self.expected_type = expected_type
        self.default = default
        self.min_value = min_value
        self.max_value = max_value
        self.step = step
        # FIXME: take from the constructor
        self.expected_value = ["population", "genetic"]
        self.header = None
        self.hidden = hidden
        pass

    def build_widget(self, row: int, label: str, grid_layout: QGridLayout):
        if self.hidden:
            # self.hide()
            return
        if type(self.default) == int:
            line_edit = QSpinBox()
        else:
            line_edit = QDoubleSpinBox()

        if self.min_value is not None:
            line_edit.setMinimum(self.min_value)
        if self.max_value is not None:
            line_edit.setMaximum(self.max_value)
        if self.default is not None:
            line_edit.setValue(self.default)
        if self.step is not None:
            line_edit.setSingleStep(self.step)
        header = self.build_header(label, self.description, self.optional)
        self.header = header
        grid_layout.addWidget(self.header, row, 0)
        self.line_edit = line_edit
        self.restore_values()
        grid_layout.addWidget(self.line_edit, row, 1)

        if self.line_edit is not None:
            line_edit = self.line_edit  # local variable guaranteed not None
            expected_type = self.expected_type
            # line_edit.editingFinished.connect(
            #     lambda: InputValidation.validate_input(line_edit, expected_type)
            # )
            # TODO: add this for all input parameters
            # self.line_edit.editingFinished.connect(self.validate_and_highlight)
            self.line_edit.valueChanged.connect(self.notify_dependants)

    def validate_and_highlight(self):
        if self.validation_rules == {}:
            return
        print(self.validation_rules)
        text = self.line_edit.text()
        if self.validate_input(text):
            self.line_edit.setStyleSheet("")  # Clear any red border
        else:
            self.line_edit.setStyleSheet("border: 1px solid red;")
            self.show_error_message(
                "Invalid input. Please enter a valid value "
                # f"({self.validation_rules['type'].__name__})"
                f"{' between ' + str(self.validation_rules['min']) + ' and ' + str(self.validation_rules['max']) if self.validation_rules['min'] is not None and self.validation_rules['max'] is not None else ''}."
            )

    def show_error_message(self, message: str):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle("Input Error")
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()

    def restore_values(self):
        if self.line_edit is not None and self.last_line_edit != "":
            try:
                value = int(self.last_line_edit)
            except ValueError:
                try:
                    value = float(self.last_line_edit)
                except ValueError:
                    return
            self.line_edit.setValue(value)


    # NOTE: add maybe a use_spin_box attribute and build accordingly

    def store_value(self):
        if not self.hidden:
            if self.line_edit is not None:
                self.last_line_edit = str(self.line_edit.value())

    def notify_dependants(self) -> None:
        for dep in self.dependants.keys():
            dep.on_dependency_updated(self)
        pass

    def get_dependency_value(self, dependency_type: DependencyType) -> int | float | str:
        if dependency_type == DependencyType.COMPONENT_COUNT:
            if self.line_edit is not None:
                return self.line_edit.value()
            try:
                return int(self.last_line_edit)
            except Exception:
                return 0
        if self.line_edit is not None:
            return self.line_edit.value()
        try:
            return int(self.last_line_edit)
        except Exception:
            return 0

    def on_dependency_updated(self, changed_param):
        # FIXME: hide all widget not only the line edit
        if self.depends_on_params.get(changed_param) == DependencyType.VISIBLE:
            if changed_param.get_value() in self.expected_value:
                # self.line_edit.show()
                self.show()
            else:
                # self.line_edit.hide()
                self.hide()

    def hide(self):
        self.hidden = True
        # if self.line_edit is not None:
        #     self.line_edit.hide()
        # if self.header is not None:
            # self.header.hide()

    def show(self):
        self.hidden = False
        # if self.line_edit is not None:
        #     self.line_edit.show()
        # if self.header is not None:
        #     self.header.show()


    def to_file(self) -> str:
        return f"{self.name} := {self.last_line_edit}"

    def to_config_entry(self) -> str:
        return f"{self.name}:= {self.last_line_edit}"


# -----------------------------------------------------------


class ParamSelect(Param):
    def __init__(
        self,
        name: str,
        file: FILE,
        values: list[str],
        depends_on: Optional[dict[str, DependencyType]],
        optional: bool = False,
        description: str = "",
        expected_type=str,
    ) -> None:
        super().__init__(name, file, depends_on=depends_on)
        self.question_label = None
        self.combo_box = None
        self.last_combo_box = ""
        self.values = values
        self.optional = optional
        self.description = description
        pass

    def build_widget(self, row: int, label: str, grid_layout: QGridLayout):
        question_label = QLabel(label)
        combo_box = QComboBox()
        # combo_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        combo_box.addItems(self.values)

        self.question_label = question_label
        self.combo_box = combo_box
        self.combo_box.currentIndexChanged.connect(self.notify_dependants)
        self.restore_values()


        header = self.build_header(label, self.description, self.optional)
        grid_layout.addWidget(header, row, 0)

        spacer = QSpacerItem(
            0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        grid_layout.addItem(spacer, row, 1)

        grid_layout.addWidget(self.combo_box, row, 2, 1, 2)

    def notify_dependants(self) -> None:
        self.category.update_category()
        for dep in self.dependants.keys():
            dep.on_dependency_updated(self)
        pass

    def restore_values(self):
        if self.combo_box:
            index = self.combo_box.findText(self.last_combo_box)
            if index != -1:
                self.combo_box.setCurrentIndex(index)

    def store_value(self):
        if self.combo_box is not None:
            self.last_combo_box = self.combo_box.currentText()
        pass

    def to_command_arg(self) -> str:
        return f"--{self.name} {self.last_combo_box}"

    def to_file(self) -> str:
        return f"{self.name} := {self.last_combo_box}"

    def get_value(self) -> str:
        return self.last_combo_box



# -----------------------------------------------------------


class ParamBoolean(Param):
    def __init__(
        self,
        name: str,
        file: FILE,
        depends_on: Optional[dict[str, DependencyType]],
        optional: bool = False,
        description: str = "",
        expected_type=str,
    ) -> None:
        super().__init__(name, file, depends_on=depends_on)
        self.question_label = None
        self.check_box = None
        self.last_check_box = False
        self.optional = optional
        self.description = description

    def build_widget(self, row: int, label: str, grid_layout: QGridLayout):
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
        header = self.build_header(label, self.description, self.optional)
        h_layout.addWidget(header)
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

    def to_command_arg(self) -> str:
        if self.last_check_box == True:
            return f"--{self.name}"
        else:
            return ""
    def get_value(self) -> bool:
        return self.last_check_box


# -----------------------------------------------------------
class ParamInputWithUnity(Param):
    def __init__(
        self,
        name: str,
        file: FILE,
        values: list[str],
        depends_on: Optional[dict[str, DependencyType]],
        description: str = "",
        optional: bool = False,
        expected_type=str,
    ) -> None:
        super().__init__(name, file=file, depends_on=depends_on)
        self.question_label = None
        self.line_edit = None
        self.combo_box = None
        self.description = description

        self.last_line_edit = ""
        self.last_combo_box = ""

        self.values = values
        self.optional = optional
        pass

    def build_widget(self, row: int, label: str, grid_layout: QGridLayout):
        header = self.build_header(label, self.description, self.optional)
        grid_layout.addWidget(header, row, 0)
        line_edit = QLineEdit()
        combo_box = QComboBox()
        combo_box.addItems(self.values)
        grid_layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum),
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

    def to_command_arg(self):
        return f"--{self.name}"


# -----------------------------------------------------------
class ParamBooleanWithInput(Param):
    def __init__(
        self,
        name: str,
        file: FILE,
        depends_on: Optional[dict[str, DependencyType]],
        optional: bool = False,
        description: str = "",
        expected_type=str,
    ) -> None:
        super().__init__(name, file, depends_on=depends_on)
        self.question_label = None
        self.line_edit = None
        self.check_box = None
        self.description = description

        self.last_check_box = False
        self.last_line_edit = ""

        self.optional = optional
        pass

    def build_widget(self, row: int, label: str, grid_layout: QGridLayout):
        header = self.build_header(label, self.description, self.optional)
        grid_layout.addWidget(header, row, 0)

        checkbox_container = QWidget()
        checkbox_layout = QHBoxLayout(checkbox_container)
        checkbox_layout.setContentsMargins(0, 0, 0, 0)
        checkbox_layout.setSpacing(5)

        check_box = QCheckBox()

        line_edit = QLineEdit()
        line_edit.setEnabled(False)

        checkbox_layout.addWidget(check_box)
        checkbox_layout.addWidget(header)
        checkbox_layout.addStretch()

        self.line_edit = line_edit
        self.check_box = check_box

        self.restore_values()

        grid_layout.addWidget(checkbox_container, row, 0, 1, 2)

        t_label = QLabel(label)

        check_box.toggled.connect(line_edit.setEnabled)
        check_box.toggled.connect(self.trigger_update)

        t_label.setVisible(self.last_check_box)
        line_edit.setVisible(self.last_check_box)

        grid_layout.addWidget(t_label, row + 1, 0)
        grid_layout.addWidget(line_edit, row + 1, 2)

    def trigger_update(self):
        self.category.update_category()

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

    def to_command_arg(self) -> str:
        if self.last_check_box == True:
            return f"--{self.name} {self.last_line_edit}"
        else:
            return ""

    def to_file(self) -> str:
        return f"{self.name} := {self.last_check_box}\n{self.name} := {self.last_line_edit}"


# -----------------------------------------------------------


class ParamBooleanWithInputWithUnity(Param):
    def __init__(
        self,
        name: str,
        file: FILE,
        values: list[str],
        depends_on: Optional[dict[str, DependencyType]],
        optional: bool = False,
        description: str = "",
        expected_type=str,
    ) -> None:
        super().__init__(name, file, depends_on=depends_on)
        self.question_label = None
        self.check_box = None
        self.combo_box = None
        self.line_edit = None
        self.description = description

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
        check_box.toggled.connect(self.trigger_update)

        self.check_box = check_box
        self.combo_box = combo_box
        self.line_edit = line_edit

        self.restore_values()

        header = self.build_header(label, self.description, self.optional)
        checkbox_layout.addWidget(check_box)
        checkbox_layout.addWidget(header)
        checkbox_layout.addStretch()

        grid_layout.addWidget(checkbox_container, row, 0, 1, 2)

        t_label = QLabel(label)

        t_label.setVisible(self.last_check_box)
        line_edit.setVisible(self.last_check_box)
        combo_box.setVisible(self.last_check_box)

        grid_layout.addWidget(t_label, row + 1, 0)
        spacer = QWidget()
        grid_layout.addWidget(spacer, row + 1, 1)
        grid_layout.addWidget(line_edit, row + 1, 2)
        grid_layout.addWidget(combo_box, row + 1, 3)

    def trigger_update(self) -> None:
        self.category.update_category()

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
    def __init__(
        self,
        name: str,
        file: FILE,
        values: list[str],
        depends_on: Optional[dict[str, DependencyType]],
        optional: bool = False,
        description: str = "",
        expected_type=str,
    ) -> None:
        super().__init__(name, file, depends_on=depends_on)
        self.question_label = None
        self.combo_box = None
        self.extra_rows = 0
        self.description = description

        self.combo_boxes = []
        self.last_combo_boxes = []
        self.optional = optional
        self.values = values

    def build_widget(self, row: int, label: str, grid_layout: QGridLayout):
        header = self.build_header(label, self.description, self.optional)
        grid_layout.addWidget(header, row, 0)
        self.combo_boxes = []

        # update method
        # FIXME: move this to a restore value function
        if self.extra_rows > 0:
            for i in range(self.extra_rows):
                combo = QComboBox()
                combo.setPlaceholderText("Extra input")
                combo.addItems(self.values)
                combo.setCurrentText(self.last_combo_boxes[i])
                combo.setSizePolicy(
                    QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
                )
                remove_button = QPushButton("✕")
                remove_button.setFixedWidth(30)
                remove_button.clicked.connect(
                    lambda _, c=combo, b=remove_button: self.remove_widget_pair(
                        c, b, grid_layout
                    )
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
        extra_combo.currentIndexChanged.connect(
            lambda: self.add_component_row(row, grid_layout)
        )

    def add_component_row(self, row: int, grid_layout: QGridLayout):
        self.component_base_row = row
        self.extra_rows += 1

        combo = QComboBox()
        combo.setPlaceholderText("Extra input")
        combo.addItems(["Item 1", "Item 2", "Item 3"])
        combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.combo_boxes.append(combo)

        remove_button = QPushButton("✕")
        remove_button.setFixedWidth(30)

        grid_layout.addWidget(combo, row + 1, 2)
        grid_layout.addWidget(remove_button, row + 1, 3)

        combo.currentIndexChanged.connect(
            lambda: self.add_component_row(row + 1, grid_layout)
        )

        self.category.update_category()

    def store_value(self):
        self.last_combo_boxes.clear()
        for el in self.combo_boxes:
            self.last_combo_boxes.append(el.currentText())

    def remove_widget_pair(
        self, widget1: QWidget, widget2: QWidget, layout: QGridLayout
    ):
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
            value += f'"{el}" '

        return f"{self.name} := {value}\n"


# -----------------------------------------------------------
class ParamFixedWithInput(Param):
    def __init__(
        self,
        name: str,
        file: FILE,
        depends_on: Optional[dict[str, DependencyType]],
        optional: bool = False,
        description: str = "",
        expected_type=str,
        default: Optional[int] =None,
        min_value: Optional[int] = None,
        max_value: Optional[int] =None,
        step: Optional[int]= None
    ) -> None:
        super().__init__(name, file=file, depends_on=depends_on)
        self.question_label = None
        self.line_edit = None
        self.combo_box = None
        self.description = description

        self.last_line_edit = ""
        self.last_combo_box = ""

        self.row_nb = 0

        self.optional = optional
        self.rows = 0
        self.default = default

        self.min_value = min_value
        self.max_value = max_value
        self.step = step
        pass
    def build_widget(self, row: int, label: str, grid_layout: QGridLayout):
        self.row = row
        self.label = label
        self.grid_layout = grid_layout
        header = self.build_header(label, self.description, self.optional)
        grid_layout.addWidget(header, row, 0)
        row += 1

        group_box = QGroupBox()
        group_layout = QGridLayout(group_box)
        group_box.setLayout(group_layout)
        group_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        for r in range(self.row_nb):
            group_layout.addWidget(QLabel(f"{r+1}"), r, 0)
            for c in range(1, 2):
                # line_edit = QSpinBox()
                if type(self.default) == int:
                    line_edit = QSpinBox()
                else:
                    line_edit = QDoubleSpinBox()

                if self.min_value is not None:
                    line_edit.setMinimum(self.min_value)
                if self.max_value is not None:
                    line_edit.setMaximum(self.max_value)
                if self.default is not None:
                    line_edit.setValue(self.default)
                if self.step is not None:
                    line_edit.setSingleStep(self.step)
                group_layout.addWidget(
                    line_edit, r, c, alignment=Qt.AlignmentFlag.AlignCenter
                )

        self.grid_layout.addWidget(group_box, row, 0, 1, -1)

    def row_span(self) -> int:
        return self.row_nb + 2

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

    def on_dependency_updated(self, changed_param: Param):
        for param, dependency_type in self.depends_on_params.items():
            if param == changed_param:
                match dependency_type:
                    case DependencyType.COMPONENT_COUNT:
                        self.category.update_category()
                        self.row_nb = param.get_dependency_value(DependencyType.COMPONENT_COUNT)
                        self.category.update_category()

# -----------------------------------------------------------
# TODO: add default value
class ParamRadio(Param):
    def __init__(
        self,
        name: str,
        file: FILE,
        depends_on: Optional[dict[str, DependencyType]],
        values: list[str],
        optional: bool = False,
        expected_type=str,
        description: str = "",

    ) -> None:
        super().__init__(name, file=file, depends_on=depends_on)
        self.question_label = None
        self.description = description

        self.optional = optional
        self.rows = 1
        self.values = values
        self.last_radio_button = None
        pass

    def build_widget(self, row: int, label: str, grid_layout: QGridLayout):
        self.row = row
        self.label = label
        self.grid_layout = grid_layout
        header = self.build_header(label, self.description, self.optional)
        grid_layout.addWidget(header, row, 0)

        self.button_group = QButtonGroup()
        for i, el in enumerate(self.values):
            # FIXME: clear the grid before
            radio_button = QRadioButton(el)
            self.button_group.addButton(radio_button, id=i)
            grid_layout.addWidget(radio_button, self.row, 2)
            self.row += 1
        grid_layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum),
            row,
            1,
        )
        self.restore_value()

    def row_span(self) -> int:
        return 1 + len(self.values)

    def restore_value(self):
        if self.last_radio_button is not None:
            button = self.button_group.button(self.last_radio_button)
            if button:
                button.setChecked(True)

    def store_value(self):
        checked_id = self.button_group.checkedId()
        if checked_id != -1:
            self.last_radio_button = checked_id

    def to_file(self) -> str:
        # TODO:
        return f"ta mere"



# -----------------------------------------------------------


class ParamComponentSelector(Param):
    def __init__(
        self,
        name: str,
        file: FILE,
        depends_on: Optional[dict[str, DependencyType]],
        values: list[str],
        optional: bool = False,
        description: str = "",
        expected_type=str,
    ) -> None:
        super().__init__(name, file=file, depends_on=depends_on)
        self.question_label = None
        self.description = description

        self.optional = optional
        self.rows = 1
        self.values = values
        self.last_radio_button = None
        self.components = ["compo1", "compo2", "compo3"]
        self.selected_components = []
        pass

    def build_widget(self, row: int, label: str, grid_layout: QGridLayout):
        self.button = QPushButton("Select Components")
        self.button.clicked.connect(self.open_selector)
        header = self.build_header(label, self.description, self.optional)
        grid_layout.addWidget(header, row, 0)
        grid_layout.addWidget(self.button, row, 2)
        row += 1

        for el in self.selected_components:
            line_edit = QLineEdit()
            line_edit.setText(el)
            line_edit.setReadOnly(True)
            remove_button = QPushButton("x")
            remove_button.setFixedWidth(30)
            remove_button.clicked.connect(
                lambda _, comp=el, b=remove_button, le=line_edit: self.remove_selected_component(
                    comp, grid_layout, b, le
                )
            )
            grid_layout.addWidget(line_edit, row, 2)
            grid_layout.addWidget(remove_button, row, 3)
            row += 1

    def open_selector(self):
        dialog = SquareCheckboxSelector(self.values, self.selected_components)
        if dialog.exec():
            self.selected_components = dialog.get_selected()
            self.button.setText(f"Selected: {len(self.selected_components)}")
            self.notify_dependants()
            self.category.update_category()

    def notify_dependants(self) -> None:
        for dep in self.dependants.keys():
            dep.on_dependency_updated(self)
        pass

    def get_dependency_value(self, dependency_type: DependencyType) -> int | float | str:
        if dependency_type == DependencyType.COMPONENT_COUNT:
            return (len(self.selected_components))
        else:
            return 0

    def remove_selected_component(
        self, component, grid_layout, remove_button, line_edit
    ):
        if component in self.selected_components:
            self.selected_components.remove(component)
        grid_layout.removeWidget(line_edit)
        grid_layout.removeWidget(remove_button)
        line_edit.deleteLater()
        remove_button.deleteLater()
        self.notify_dependants()
        self.category.update_category()

    def restore_value(self):
        return

    def row_span(self) -> int:
        return 1 + len(self.selected_components)

    def store_value(self):
        return

    def to_file(self) -> str:
        # TODO:
        return f""



# -----------------------------------------------------------
class ParamSpinBoxWithBool(Param):
    def __init__(
        self,
        name: str,
        file: FILE,
        depends_on: Optional[dict[str, DependencyType]],
        optional: bool = False,
        expected_type=str,
        description: str = "",
    ) -> None:
        super().__init__(name, file, depends_on=depends_on)
        self.question_label = None
        self.time_spin_box = None
        self.last_spin_box = ""
        self.file = file
        self.optional = optional
        self.expected_type = expected_type
        self.last_check_box = False
        self.last_time_spin_box = None
        self.last_unity = None
        self.description = description
        self.check_box = None
        pass

    def trigger_update(self):
        self.category.update_category()

    def to_file(self) -> str:
        return ""

    def row_span(self) -> int:
        return 2

    def build_widget(self, row: int, label: str, grid_layout: QGridLayout):
        label = f"{label}{'' if self.optional else ' *'}"
        checkbox_container = QWidget()
        checkbox_layout = QHBoxLayout(checkbox_container)
        checkbox_layout.setContentsMargins(0, 0, 0, 0)
        checkbox_layout.setSpacing(5)

        check_box = QCheckBox()

        time_spin_box = TimeSpinBox()

        checkbox_layout.addWidget(check_box)
        header = self.build_header(label, self.description, self.optional)
        checkbox_layout.addWidget(header)
        checkbox_layout.addStretch()

        self.time_spin_box = time_spin_box
        self.check_box = check_box

        self.restore_values()

        grid_layout.addWidget(checkbox_container, row, 0, 1, 2)

        t_label = QLabel(label)

        check_box.toggled.connect(self.trigger_update)

        t_label.setVisible(self.last_check_box)
        time_spin_box.setVisible(self.last_check_box)

        grid_layout.addWidget(t_label, row + 1, 0)
        grid_layout.addWidget(time_spin_box, row + 1, 2)

    def store_value(self):
        if self.check_box is not None:
            self.last_check_box = self.check_box.isChecked()
        if self.time_spin_box is not None:
            self.time_spin_box.get_value()
            self.last_time_spin_box, self.last_unity = self.time_spin_box.get_value()

    def restore_values(self):
        if self.last_check_box:
            if self.check_box:
                self.check_box.setChecked(True)
        if self.last_time_spin_box is not None and self.last_unity is not None:
            if self.time_spin_box:
                print(f"the self.last_unity was {self.last_unity}")
                self.time_spin_box.set_value(self.last_time_spin_box, self.last_unity)

    def to_command_arg(self) -> str:
        if self.last_check_box == True:
            # pour que le lsp ne râle pas, mais techniquement impossible
            if self.last_time_spin_box and self.last_unity and self.time_spin_box:
                return f"--{self.name} {self.time_spin_box.to_seconds(self.last_time_spin_box, self.last_unity)}"
            else:
                return ""
        else:
            return ""


# -----------------------------------------------------------
class ParamFileChooser(Param):
    def __init__(
        self,
        name: str,
        file: FILE,
        depends_on: Optional[dict[str, DependencyType]] = None,
        optional: bool = False,
        description: str = "",
        expected_type=str,
    ) -> None:
        super().__init__(name, file, depends_on=depends_on)
        self.question_label = None
        self.line_edit = None
        self.button = None
        self.last_file_path = ""
        self.optional = optional
        self.description = description

    def build_widget(self, row: int, label: str, grid_layout: QGridLayout):
        header = self.build_header(label, self.description, self.optional)
        grid_layout.addWidget(header, row, 0)

        self.line_edit = QLineEdit()
        self.line_edit.setReadOnly(True)
        self.button = QPushButton("Browse")
        self.button.clicked.connect(self.open_file_dialog)

        grid_layout.addWidget(self.line_edit, row, 1)
        grid_layout.addWidget(self.button, row, 2)

        self.restore_value()

    def open_file_dialog(self):
        from PyQt6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(
            None, "Select File", "", "All Files (*)"
        )
        if file_path:
            self.line_edit.setText(file_path)
            self.last_file_path = file_path

    def restore_value(self):
        if self.last_file_path and self.line_edit:
            self.line_edit.setText(self.last_file_path)

    def store_value(self):
        if self.line_edit is not None:
            self.last_file_path = self.line_edit.text()

    def to_file(self) -> str:
        return f"{self.name} := {self.last_file_path}"

    def to_command_arg(self) -> str:
        if self.last_file_path:
            return f"--{self.name} \"{self.last_file_path}\""
        return ""

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
            font-size: 12px;
            color: #000;
"""
        )
        group_box = QGroupBox()
        # group_box.setCheckable(True)
        # group_box.setChecked(False)  # Collapsed by default
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setVerticalSpacing(0)
        group_layout = QVBoxLayout(group_box)
        group_layout.setContentsMargins(0, 0, 0, 0)
        group_layout.addWidget(self.grid_widget)
        self.grid_widget.setMinimumWidth(370)

        layout.addWidget(self.label)
        # layout.setSpacing(4)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(group_box)
        layout.addStretch()

        # test button
        self.test_button.setFixedWidth(50)
        self.test_button.clicked.connect(self.notify_dependents)

        # NOTE: restore to test
        # layout.addWidget(self.test_button)

        self.build_param()

    def notify_dependents(self):
        for name, param in self.param.items():
            param.notify_dependants()
    def build_param(self) -> QWidget:
        self.row = 0
        for label, param_obj in self.param.items():
            param_obj.category = self  
        for label, param_obj in self.param.items():
            param_obj.build_widget(self.row, label, self.grid_layout)
            self.row += param_obj.row_span()
        return self

    def store_values(self):
        for name, param in self.param.items():
            param.store_value()

    def update_category(self):
        if getattr(self, "_updating", False):
            return
        self._updating = True
        self.store_values()
        self.clear_grid_layout()
        self.build_param()
        # self.write_to_file()
        self._updating = False

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
            FILE.COMMAND: "command.sh",
        }
        self.build_command()
        # used_files = {
        #     file_map[param.file]
        #     for param in self.param.values()
        #     if param.file in file_map
        # }
        # for file_name in used_files:
        #     open(file_name, "w").close()

        for _, param in self.param.items():
            print("the self.params is", self.param)
            file_name = file_map.get(param.file)
            print("the file name is", {file_name})
            lines = []
            if not file_name:
                print(f"Unknown file type for param {param.name}")
            else:
                value = param.to_file()
                print("the value is", value)
                if value != "":
                    lines.append(value)
            print(lines)

            with open(file_name, "a") as f:
                f.writelines(lines)
        # f.write(f"{value}\n")

    def build_command(self):
        file_map = {
            FILE.DATA: "data.dat",
            FILE.CONFIG: "config.ini",
            FILE.PERM: "perm.dat",
            FILE.ECO: "eco.dat",
            FILE.COMMAND: "command.sh",
        }
        res = ""
        for _, param in self.param.items():
            if param.file == FILE.COMMAND:
                print("AAAA", param.name)
                res += f"--{param.name}"
            file_name = file_map.get(param.file)
        print("SDQFSDGHJFHKGDSFQ", res)
        # if fi


# -----------------------------------------------------------


class TimeSpinBox(QWidget):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)

        self.spin = QSpinBox()
        self.spin.setRange(0, 9999)
        self.spin.setValue(10)
        self.spin.setSuffix(" hours")  # Default suffix

        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["sec", "min", "hours", "days"])
        self.unit_combo.setCurrentIndex(2)
        self.unit_combo.currentIndexChanged.connect(self.change_unit)

        layout.addWidget(self.spin)
        layout.addWidget(self.unit_combo)

    def change_unit(self, idx):
        units = [" sec", " min", " hours", " days"]
        self.spin.setSuffix(units[idx])

    def to_seconds(self, value: int, unity_index: int) -> int:
        units = ["sec", "min", "hours", "days"]
        unit = units[unity_index]
        if unit == "sec":
            return value
        elif unit == "min":
            return value * 60
        elif unit == "hours":
            return value * 3600
        elif unit == "days":
            return value * 86400
        else:
            return value

    def get_value(self) -> Tuple[int, int]:
        return self.spin.value(), self.unit_combo.currentIndex()

    def set_value(self, value: int, index: int) -> None:
        self.unit_combo.setCurrentIndex(index)
        self.spin.setValue(value)


# TODO: search filter
# TODO: restore the size after the collapsable menu were disabled
# TODO: solve the problem with dynamic resizing of grid fields


# -----------------------------------------------------------
class CollapsibleGroupBox(QGroupBox):
    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self.setCheckable(True)
        self.setChecked(False)  # Start collapsed
        self.toggled.connect(self.on_toggled)

        # Your content
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("This is inside the collapsible section!"))

    def on_toggled(self, checked):
        # Show/hide children when toggled
        for i in range(self.layout().count()):
            widget = self.layout().itemAt(i).widget()
            if widget:
                widget.setVisible(checked)


# -----------------------------------------------------------


class MembraneOptions(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Membrane Options")

        self.main_layout = QVBoxLayout(self)

        # Number of membranes control
        spin_layout = QHBoxLayout()
        spin_layout.addWidget(QLabel("Number of membranes *"))
        self.num_membranes = QSpinBox()
        self.num_membranes.setMinimum(0)
        self.num_membranes.valueChanged.connect(self.update_grid)
        spin_layout.addWidget(self.num_membranes)
        self.main_layout.addLayout(spin_layout)

        # Scroll area for grid
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        # self.scroll_area.setWidget(self.grid_container)
        self.main_layout.addWidget(self.grid_container)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.edit_widgets = []

    def update_grid(self, count):
        # Clear previous widgets from grid layout
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.edit_widgets = []

        # Header row
        self.grid_layout.addWidget(QLabel("Membrane"), 0, 0)
        self.grid_layout.addWidget(QLabel("ub_area"), 0, 1)
        self.grid_layout.addWidget(QLabel("lb_area"), 0, 2)
        self.grid_layout.addWidget(QLabel("ub_acell"), 0, 3)

        # Membrane rows
        for i in range(count):
            self.grid_layout.addWidget(QLabel(f"Membrane {i+1}"), i + 1, 0)
            ub_area = QLineEdit()
            lb_area = QLineEdit()
            ub_acell = QLineEdit()
            self.grid_layout.addWidget(ub_area, i + 1, 1)
            self.grid_layout.addWidget(lb_area, i + 1, 2)
            self.grid_layout.addWidget(ub_acell, i + 1, 3)
            self.edit_widgets.append((ub_area, lb_area, ub_acell))


class GridOptions(QWidget):
    def __init__(self, column_names, row_names, parent=None):
        super().__init__(parent)
        self.column_names = column_names
        self.row_names = row_names
        self.cell_widgets = {}

        main_layout = QVBoxLayout(self)

        grid_container = QWidget()
        grid_layout = QGridLayout(grid_container)

        grid_layout.addWidget(QLabel(""), 0, 0)
        for col, cname in enumerate(column_names, start=1):
            grid_layout.addWidget(QLabel(cname), 0, col)

        for row, rname in enumerate(row_names, start=1):
            grid_layout.addWidget(QLabel(rname), row, 0)
            for col, cname in enumerate(column_names, start=1):
                le = QLineEdit()
                grid_layout.addWidget(le, row, col)
                self.cell_widgets[(rname, cname)] = le

        grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        main_layout.addWidget(grid_container)


# -----------------------------------------------------------
class HelpButtonDemo(QWidget):
    def __init__(self, description: str):
        super().__init__()
        self.description = description
        layout = QHBoxLayout(self)

        help_btn = QToolButton()
        help_btn.setText("?")
        help_btn.setToolTip(description)
        help_btn.setFixedSize(14, 14)
        help_btn.clicked.connect(self.show_help_tooltip)

        # Round style via stylesheet
        help_btn.setStyleSheet(
            """
            QToolButton {
                border: 1px solid #888;
                border-radius: 7px;        /* Half of width/height */
                background: #f5f5f5;
                font-weight: bold;
                font-size: 14px;
                color: #3366cc;
            }
            QToolButton:hover {
                background: #e0eaff;
                border: 1.5px solid #0057b8;
            }
        """
        )

        layout.addWidget(help_btn)

    def show_help_tooltip(self):
        # Show a tooltip near the button when clicked
        QToolTip.showText(
            self.mapToGlobal(self.sender().pos()) + QPoint(0, self.sender().height()),
            self.description,
            self.sender(),
        )
