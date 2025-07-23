import enum
from typing import Optional, OrderedDict, Tuple, Union
from PyQt6.QtCore import QEvent, QPoint, Qt
from PyQt6.QtGui import QAction, QTabletEvent
from PyQt6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QSpinBox,
    QToolButton,
    QToolTip,
    QVBoxLayout,
    QWidget,
)
import inspect

from app.dependency_manager import DependencyManager
from app.param_enums import FILE, DependencyType

# -----------------------------------------------------------

def debug_print(*args, **kwargs):
    frame = inspect.currentframe().f_back
    func_name = frame.f_code.co_name
    line_no = frame.f_lineno
    print(f"[{func_name}:{line_no}]", *args, **kwargs)

# -----------------------------------------------------------
class ComponentWindow(QDialog):
    """
    Dialog window for selecting components with an optional maximum selection limit.

    Args:
        components (list): List of component names to display as checkboxes.
        selected (list, optional): List of initially selected components.
        parent (QWidget, optional): Parent widget.
        max_selected (int, optional): Maximum number of components that can be selected.

    Features:
        - Displays a list of components as checkboxes.
        - Enforces a maximum selection limit if specified.
        - Returns the selected components.
    """
    def __init__(self, components, selected=None, parent=None, max_selected=None, min_selected=None):
        super().__init__(parent)
        self.setWindowTitle("Select Components")
        self.setFixedSize(300, 400)

        self.selected = selected or []
        self.max_selected = max_selected
        self.min_selected = min_selected

        layout = QVBoxLayout()
        self.checkboxes = []

        for comp in components:
            checkbox = QCheckBox(comp)
            checkbox.setChecked(comp in self.selected)
            checkbox.stateChanged.connect(self.handle_checkbox)
            self.checkboxes.append(checkbox)
            layout.addWidget(checkbox)

        layout.addStretch()

        self.ok_button = None
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)
        self.setLayout(layout)
        self.update_ok_button()

    def get_selected(self) -> list[str]:
        """Returns a list of selected components

        Returns:
            list: List of selected components
        """
        for cb in self.checkboxes:
            if cb.isChecked():
                self.selected.append(cb.text())

        return [cb.text() for cb in self.checkboxes if cb.isChecked()]

    def handle_checkbox(self):
        """
        Handles checkbox state changes to enforce a maximum selection limit.

        - If the number of checked boxes exceeds `max_selected`, the last toggled box is unchecked.
        - Disables unchecked boxes when the maximum is reached, re-enables them otherwise.

        Used to enforce bi-components for variable permeability
        """
        if self.max_selected is not None:
            checked_count = sum(cb.isChecked() for cb in self.checkboxes)
            if checked_count > self.max_selected:
                sender = self.sender()
                if isinstance(sender, QCheckBox):
                    sender.setChecked(False)
            for cb in self.checkboxes:
                if not cb.isChecked():
                    cb.setEnabled(checked_count < self.max_selected)
        self.update_ok_button()

    def update_ok_button(self):
        """Enable or disable OK button based on min_selected constraint."""
        if self.ok_button is not None and self.min_selected is not None:
            checked_count = sum(cb.isChecked() for cb in self.checkboxes)
            self.ok_button.setEnabled(checked_count >= self.min_selected)

# -----------------------------------------------------------


class Param:
    """
    Base class representing a parameter in the application.

    Args:
        name (str): The exact name of the parameter in the data files.
        optional (bool, optional): Whether the parameter is optional. Defaults to False.
        label (str, optional): The label shown in the interface. Defaults to "".
        expected_type (type, optional): The expected type of the parameter value. Defaults to str.
        description (str, optional): Description of the parameter. Defaults to "".
        manager (Optional[DependencyManager], optional): Dependency manager for the parameter. Defaults to None.

    Attributes:
        name (str): Parameter name.
        category (ParamCategory): Category of the parameter.
        optional (bool): Whether the parameter is optional.
        expected_type (type): Expected type of the parameter value.
        description (str): Description of the parameter.
        label (str): Label shown in the interface.
        manager (Optional[DependencyManager]): Dependency manager.
    """
    def __init__(
        self,
        name: str,
        optional: bool = False,
        label: str = "",
        expected_type=str,
        description: str = "",
        manager: Optional[DependencyManager] = None,
    ) -> None:
        self.name = name  
        self.category: ParamCategory
        self.optional = optional
        self.expected_type = expected_type
        self.description = description
        self.label = label
        self.manager = manager

    def build_widget(self, row: int, label: str, grid_layout: QGridLayout):
        """
        Abstract method to build the parameter's widget in the UI.

        Args:
            row (int): Row position in the layout.
            label (str): Label for the widget.
            grid_layout (QGridLayout): Layout to add the widget to.

        Raises:
            NotImplementedError: Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement build_widgets")

    def store_value(self):
        """
        Abstract method to store the parameter's value. Called before rebuilding the ui to re-populate the ui with the right values during the update.

        Raises:
            NotImplementedError: Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement store_values")

    def restore_value(self):
        """
        Abstract method to restore the parameter's value. Called after rebuilding the ui during the update.
        """

    def row_span(self) -> int:
        """
        Returns the number of rows the widget should span in the layout.

        Returns:
            int: Number of rows to span.
        """
        return 1

    def hide(self) -> None:
        """
        Hides the parameter widget in the UI.
        """
        pass
        # self.hidden = True

    def show(self) -> None:
        """
        Shows the parameter widget in the UI.
        """
        pass
        self.hidden = False


    def to_config_entry(self) -> Optional[str]:
        """
        Converts the parameter value to a config file entry.
        Used to build the config.ini file.

        Returns:
            Optional[str]: Config entry string or None.
        """
        return None

    def to_command_arg(self) -> Optional[str]:
        """
        Converts the parameter value to a command entry for the program launcher.
        Used to build command.sh.
        """
        raise NotImplementedError(self.name, "to_command_arg not implemented") 

    def to_data_entry(self) -> Optional[str]:
        """
        Converts the parameter value to a eco file entry.
        Used to build the data.dat file.

        Returns:
            Optional[str]: Eco entry string or None 
        """
        return None

    def to_perm_entry(self) -> Optional[str]:
        """
        Converts the parameter value to a perm file entry.
        Used to build the perm.dat file.

        Returns:
            Optional[str]: Perm entry string or None 
        """
        return None

    def to_mask_entry(self) -> Optional[str]:
        """
        Converts the parameter value to a (optionnal) mask file entry.
        Used to build the mask.dat file.

        Returns:
            Optional[str]: Mask entry string or None 
        """
        return None

    def update_param(self):
        """
        Abstract method to update the parameter value.

        Raises:
            NotImplementedError: Must be implemented by subclasses.
        """
        raise NotImplementedError(self.name, "Update param not implemented")


    def build_header(self, label: str, description: str, optional: bool) -> QWidget:
        """
        Builds a header widget for the parameter, including label and help icon.

        Args:
            label (str): Label for the parameter.
            description (str): Description for the help tooltip.
            optional (bool): Whether the parameter is optional.

        Returns:
            QWidget: The constructed header widget.
        """
        header_container = QWidget()
        header_layout = QHBoxLayout(header_container)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        header_layout.setContentsMargins(0, 0, 0, 0)
        required_mark = ' ' if optional else ' <span style="color:red;">*</span>'
        label_text = f"{label}{required_mark}"
        question_label = QLabel(label_text)
        icon_label = HelpButtonDemo(description)
        header_layout.addWidget(question_label)
        header_layout.addWidget(icon_label)
        return header_container



    def create_spinbox( self, min_value: Optional[Union[int, float]] = None, max_value: Optional[Union[int, float]] = None, step: Optional[Union[int, float]] = None, default: Optional[Union[int, float]] = None) -> Union[QSpinBox, QDoubleSpinBox]:
        """
        Creates and configures a spinbox widget for integer or float input.

        Args:
            min_value (Optional[int|float], optional): Minimum value.
            max_value (Optional[int|float], optional): Maximum value.
            step (Optional[int|float], optional): Step size.
            default (Optional[int|float], optional): Default value.

        Returns:
            QSpinBox or QDoubleSpinBox: Configured spinbox widget.
        """
        if self.expected_type == int:
            spin = QSpinBox()
            if min_value is not None:
                spin.setMinimum(int(min_value))
            if max_value is not None:
                spin.setMaximum(int(max_value))
            if step is not None:
                spin.setSingleStep(int(step))
            if default is not None:
                spin.setValue(int(default))
        else:
            spin = QDoubleSpinBox()
            if min_value is not None:
                spin.setMinimum(float(min_value))
            if max_value is not None:
                spin.setMaximum(float(max_value))
            if step is not None:
                spin.setSingleStep(float(step))
            if default is not None:
                spin.setValue(float(default))
        return spin

    def set_spin_value(self, spin, value: Union[int, float]):
            """
            Set the value in the line_edit widget, handling int/float types and decimals.

            Args: 
                value: Value to set in the spinbox (int/float).
            """
            if spin is not None:
                if isinstance(spin, QSpinBox):
                    try:
                        spin.setValue(int(float(value)))
                    except (ValueError, TypeError):
                        pass
                elif isinstance(spin, QDoubleSpinBox):
                    try:
                        float_val = float(value)
                        str_val = str(float_val)
                        if '.' in str_val:
                            decimals = len(str_val.split('.')[-1])
                        else:
                            decimals = 2
                        spin.setDecimals(decimals)
                        spin.setMaximum(1e10)
                        spin.setValue(float_val)
                    except (ValueError, TypeError):
                        debug_print("Error")
                        pass
            # debug_print(spin.value())
    def set_value_from_import(self, values: dict):
            """
            Sets the value from imported data.

            Args:
                value: Value to set.
            """
            raise NotImplementedError("Subclasses must implement set_value_from_import")

    def _on_value_changed(self):
        """
        Handles spinbox value changes, stores the value and notifies dependencies.
        """
        if self.manager is not None:
            self.store_value()
            self.manager.notify_change(self)



# -----------------------------------------------------------

class ParamInput(Param):
    """Represents a numeric input parameter with optional constraints.
    Args:
        See Attributes below for parameter descriptions.

    Attributes:
        spin_box: Spinbox widget for input.
        last_line_edit: Last entered value as string.
        optional: Whether the parameter is optional.
        expected_type: Expected type of the value.
        default: Default value.
        min_value: Minimum allowed value.
        max_value: Maximum allowed value.
        step: Step size for spinbox.
        expected_value: List of expected value types.
        header: Header widget for UI.
        hidden: Whether the parameter is hidden.
        manager: Dependency manager.
        checkbox: Checkbox for optional input.
        with_checkbox: Whether to show the checkbox.
        last_checkbox: Last checkbox state.
    """

    def __init__(
        self,
        name: str,
        optional: bool = False,
        expected_type=str,
        description: str = "",
        label: str = "",
        default: Optional[int] = None,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        step: Optional[int] = None,
        hidden: bool = False,
        with_checkbox: bool = False,
    ) -> None:
        super().__init__(name, description=description, label=label)
        self.spin_box = None
        self.last_line_edit = ""
        self.optional = optional
        self.expected_type = expected_type
        self.default = default
        self.min_value = min_value
        self.max_value = max_value
        self.step = step
        self.header = None
        self.hidden = hidden
        self.manager: Optional[DependencyManager] = None
        self.checkbox: Optional[QCheckBox] = None
        self.with_checkbox = with_checkbox
        self.last_checkbox = False

    def build_widget(self, row: int, label: str, grid_layout: QGridLayout):
        self.spin_box = None
        if self.hidden:
            return
        self.row = row
        self.spin_box = self.create_spinbox(self.min_value, self.max_value, self.step, self.default)
        self.grid_layout = grid_layout
        self.header = self.build_header(label, self.description, self.optional)
        grid_layout.addWidget(self.header, row, 0)
        grid_layout.addWidget(self.spin_box, row, 1)
        self.spin_box.valueChanged.connect(self._on_value_changed)
        if self.with_checkbox:
            self.checkbox = QCheckBox(f"Set {self.name}")
            self.checkbox.setChecked(False)
            self.checkbox.stateChanged.connect(self._on_checkbox_changed)
            self.spin_box.setVisible(False)
            grid_layout.addWidget(self.checkbox, row, 0)
        self.restore_values()

    def _on_checkbox_changed(self, state):
        if self.spin_box is not None:
            self.spin_box.setVisible(bool(state))
        if not state:
            self.last_line_edit = ""

    def set_value(self, value):
        """
        Set the value in the line_edit widget, handling int/float types and decimals.

        Args: 
            value: Value to set in the spinbox (int/float).
        """
        self.set_spin_value(self.spin_box, value)
        self.last_line_edit = str(value)

    def set_value_from_import(self, values: dict):
        value = values[self.name]
        self.set_value(value)
        if self.checkbox is not None:
            self.checkbox.setChecked(True)
        debug_print(f"The param {self.name} was imported")

    def set_last_line_edit(self, value):
        """
        Sets the last entered value as a string.

        Args:
            value: Value to store.
        """
        self.last_line_edit = value

    def restore_values(self):
        if self.with_checkbox:
            if self.last_checkbox:
                if self.checkbox is not None:
                    self.checkbox.setChecked(True)
        if self.spin_box is not None and self.last_line_edit != "":
            try:
                if self.expected_type == int:
                    value = int(float(self.last_line_edit))
                else:
                    value = float(self.last_line_edit)
            except ValueError:
                debug_print("value error")
                return
            # FIXME: replace with set_spin_box_value
            self.spin_box.setValue(value)

    def store_value(self):
        if not self.hidden:
            if self.spin_box is not None:
                self.last_line_edit = str(self.spin_box.value())
            if self.with_checkbox:
                debug_print(self.name)
                if self.checkbox is not None:
                    self.last_checkbox = self.checkbox.isChecked()

    def get_value(self) -> str:
        """
        Returns the last entered value as a string.

        Returns:
            str: Last entered value.
        """
        return self.last_line_edit

    def get_value_float(self) -> float:
        """
        Returns the last entered value as a float.

        Returns:
            float: Last entered value.

        Raises:
            ValueError: If conversion fails.
        """
        self.store_value()
        try:
            return float(self.last_line_edit)
        except (ValueError, TypeError):
           raise ValueError

    def hide(self):
        self.hidden = True

    def show(self):
        self.hidden = False

    def to_config_entry(self) -> Optional[str]:
        if self.last_line_edit != "" and self.last_line_edit != None:
            return f"{self.name} = {self.last_line_edit}"
        if self.hidden and self.default is not None:
            return f"{self.name} = {self.default}"

    def to_data_entry(self) -> Optional[str]:
        if self.with_checkbox and self.checkbox is not None and not self.checkbox.isChecked():
            return None
        if self.last_line_edit != "" and self.last_line_edit != None:
            return f"{self.name} := {self.last_line_edit}"

    def to_eco_entry(self) -> Optional[str]:
        return self.to_data_entry()

    def to_perm_entry(self) -> Optional[str]:
        return self.to_data_entry()

    def to_command_arg(self) -> Optional[str]:
        if self.last_line_edit:
            return f"--{self.name} {self.last_line_edit}"
        return None
    
# -----------------------------------------------------------

class ParamSelect(Param):
    """
    Represents a parameter with a selectable value from a predefined list, integrated with UI.

    Args:
        See Attributes below for parameter descriptions.
    Attributes:
        question_label: Label for help/question icon.
        combo_box: ComboBox widget for selection.
        last_combo_box: Last selected value.
        values: List of selectable values.
        optional: Whether the parameter is optional.
        description: Description of the parameter.
        manager: Dependency manager.
        label: Label for the parameter.
        hidden: Whether the parameter is hidden.
    """
    def __init__(
        self,
        name: str,
        values: list[str],
        label: str,
        hidden: bool = False,
        optional: bool = False,
        description: str = "",
    ) -> None:
        super().__init__(name, description=description, label=label)
        self.question_label = None
        self.combo_box = None
        self.last_combo_box = ""
        self.values = values
        self.optional = optional
        self.description = description
        self.manager: Optional[DependencyManager] = None
        self.label = label
        self.hidden = hidden
        pass
    
    def set_values(self, values: list[str]):
        self.values = values

    def build_widget(self, row: int, label: str, grid_layout: QGridLayout):
        if self.hidden:
            return
        question_label = QLabel(label)
        combo_box = QComboBox()
        self.row = row
        self.grid_layout = grid_layout
        self.label = label

        combo_box.addItems(self.values)

        self.question_label = question_label
        self.combo_box = combo_box
        self.combo_box.currentIndexChanged.connect(self._on_value_changed)
        self.restore_values()

        header = self.build_header(label, self.description, self.optional)
        grid_layout.addWidget(header, row, 0)

        grid_layout.addWidget(self.combo_box, row, 1)

    def set_value_from_import(self, values: dict):
        value = values[self.name]
        self.combo_box = QComboBox()
        if value:
            self.combo_box.setCurrentText(value)
        if self.name == "param final_product":
            components = values["set components"]
            self.values = components
            self.combo_box.addItems(components)
        debug_print(f"The param {self.name} was imported")

    def hide(self):
        self.hidden = True

    def show(self):
        self.hidden = False

    def restore_values(self):
        if self.combo_box is not None:
            index = self.combo_box.findText(self.last_combo_box)
            if index != -1:
                self.combo_box.setCurrentIndex(index)

    def store_value(self):
        if self.combo_box is not None:
            self.last_combo_box = self.combo_box.currentText()
        pass

    def get_value_select(self) -> Optional[str]:
        if self.combo_box is not None:
            return self.combo_box.currentText()
        return None

    def update_param(self):
        if getattr(self, "_updating", False):
            return
        self._updating = True
        self.store_value()  
        self.build_widget(self.row, self.label, self.grid_layout)
        self._updating = False

    def to_command_arg(self) -> Optional[str]:
        if self.last_combo_box:
            return f"--{self.name} {self.last_combo_box}"
        return None

    def to_config_entry(self):
        if self.last_combo_box:
            return f"{self.name} = {self.last_combo_box}"
        if self.hidden:
            return f"{self.name} = {self.values[0]}"

    def to_data_entry(self):
        if self.last_combo_box:
            return f"{self.name} := \"{self.last_combo_box}\""

    def get_value(self) -> str:
        return self.last_combo_box

# -----------------------------------------------------------


class ParamBoolean(Param):
    """
    Represents a boolean parameter with an associated checkbox widget.

    Args:
        See Attributes below for parameter descriptions.

    Attributes:
        question_label: label widget for the question.
        check_box: checkbox widget for boolean input.
        last_check_box: last checkbox state.
        optional: whether the parameter is optional.
        description: description of the parameter.
        label: label for the parameter.
        manager: dependency manager.
    """
    def __init__(
        self,
        name: str,
        label: str,
        optional: bool = False,
        description: str = "",
    ) -> None:
        super().__init__(name, description=description, label=label)
        self.question_label = None
        self.check_box = None
        self.last_check_box = False
        self.optional = optional
        self.description = description
        self.label = label
        self.manager: Optional[DependencyManager] = None

    def build_widget(self, row: int, label: str, grid_layout: QGridLayout):
        container = QWidget()
        h_layout = QHBoxLayout(container)
        h_layout.setContentsMargins(0, 0, 0, 0)

        check_box = QCheckBox()
        question_label = QLabel(label)

        self.check_box = check_box
        self.question_label = question_label

        self.restore_values()
        h_layout.addWidget(self.check_box)
        header = self.build_header(label, self.description, self.optional)
        h_layout.addWidget(header)
        h_layout.addStretch()

        if self.check_box is not None:
            self.check_box.toggled.connect(self._on_value_changed)

        grid_layout.addWidget(container, row, 0, 1, 2)

    def restore_values(self):
        if self.last_check_box:
            if self.check_box:
                self.check_box.setChecked(True)

    def store_value(self):
        if self.check_box is not None:
            self.last_check_box = self.check_box.isChecked()

    def set_value(self, value: bool):
        if self.check_box is not None:
            self.check_box.setChecked(value)

    def to_command_arg(self) -> str:
        if self.last_check_box == True:
            return f"--{self.name}"
        else:
            return ""

    def to_config_entry(self):
        return f"{self.name} = {self.last_check_box}"

    def get_value(self) -> bool:
        return self.last_check_box

# TODO: modify input class to allow unity also
# -----------------------------------------------------------
class ParamInputWithUnity(Param):
    def __init__(
        self,
        name: str,
        values: list[str],
        description: str = "",
        optional: bool = False,
        label: str = "",
        expected_type=str,
        default: Optional[int] = None,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
        step: Optional[int] = None,
    ) -> None:
        super().__init__(name, description=description, label=label)
        self.question_label = None
        self.spin_box = None
        self.combo_box = None
        self.description = description
        self.min_value = min_value
        self.max_value = max_value
        self.step = step

        self.last_line_edit = ""
        self.last_combo_box = ""

        self.values = values
        self.optional = optional
        self.default = default
        self.expected_type = expected_type
        pass

    def build_widget(self, row: int, label: str, grid_layout: QGridLayout):
        header = self.build_header(label, self.description, self.optional)
        grid_layout.addWidget(header, row, 0)
        self.spin_box = self.create_spinbox(self.min_value, self.max_value, self.step, self.default)
        combo_box = QComboBox()
        combo_box.addItems(self.values)
        self.combo_box = combo_box
        grid_layout.addWidget(self.spin_box, row, 1)
        grid_layout.addWidget(self.combo_box, row, 2)
        self.restore_value()


    def restore_value(self):
        if self.last_combo_box:
            if self.combo_box:
                index = self.combo_box.findText(self.last_combo_box)
                if index != -1:
                    self.combo_box.setCurrentIndex(index)
        if self.last_line_edit:
            if self.spin_box:
                self.spin_box.setValue(int(self.last_line_edit))

    def store_value(self):
        if self.spin_box is not None:
            self.last_line_edit = self.spin_box.value()
            pass
        if self.combo_box is not None:
            self.last_combo_box = self.combo_box.currentText()
        pass


    def to_data_entry(self) -> Optional[str]:
        # TODO: convert unity before assignment
        if self.last_line_edit != "" and self.last_line_edit is not None:
            return f"{self.name} := {self.last_line_edit}"

    def to_command_arg(self):
        return f"--{self.name}"


# -----------------------------------------------------------
class ParamBooleanWithInput(Param):
    def __init__(
        self,
        name: str,
        label: str,
        optional: bool = False,
        description: str = "",
        default: Optional[int] = None,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        step: Optional[int] = None,
        expected_type=str,
    ) -> None:
        super().__init__(name, description=description, label=label)
        self.question_label = None
        self.spin_box = None
        self.check_box = None
        self.description = description

        self.last_check_box = False
        self.last_spin_value = 0

        self.expected_type = expected_type
        self.optional = optional
        self.default = default
        self.min_value = min_value
        self.max_value = max_value
        self.step = step
        self.widgets = []
        pass

    def build_widget(self, row: int, label: str, grid_layout: QGridLayout):
        self.widgets.clear()
        self.grid_layout = grid_layout
        self.row = row
        header = self.build_header(label, self.description, self.optional)
        grid_layout.addWidget(header, row, 0)

        checkbox_container = QWidget()
        checkbox_layout = QHBoxLayout(checkbox_container)
        checkbox_layout.setContentsMargins(0, 0, 0, 0)
        checkbox_layout.setSpacing(5)

        self.check_box = QCheckBox()
        self.spin_box = self.create_spinbox(self.min_value, self.max_value, self.step, self.default)

        self.spin_box.setEnabled(False)

        checkbox_layout.addWidget(self.check_box)
        checkbox_layout.addWidget(header)
        checkbox_layout.addStretch()

        self.restore_values()

        grid_layout.addWidget(checkbox_container, row, 0, 1, 2)

        t_label = QLabel(label)

        self.check_box.toggled.connect(self.spin_box.setEnabled)
        self.check_box.toggled.connect(self.update_param)

        t_label.setVisible(self.last_check_box)
        self.spin_box.setVisible(self.last_check_box)

        grid_layout.addWidget(t_label, row + 1, 0)
        grid_layout.addWidget(self.spin_box, row + 1, 1)
        self.widgets.extend([self.spin_box, self.check_box])

    def update_param(self):
        if getattr(self, "_updating", False):
            return
        self._updating = True
        self.store_value()
        if hasattr(self, "widgets"):
            for widget in self.widgets:
                self.grid_layout.removeWidget(widget)
                widget.deleteLater()
            self.widgets.clear()
        self.build_widget(self.row, self.label, self.grid_layout)
        self._updating = False
    

    def restore_values(self):
        if self.last_check_box:
            if self.check_box:
                self.check_box.setChecked(True)
            if self.spin_box:
                self.spin_box.setEnabled(True)
        if self.last_spin_value:
            if self.spin_box:
                self.spin_box.setValue(self.last_spin_value)

    def store_value(self):
        if self.spin_box is not None:
            self.last_spin_value = self.spin_box.value()
        if self.check_box is not None:
            self.last_check_box = self.check_box.isChecked()

    def row_span(self) -> int:
        return 2

    def to_command_arg(self) -> str:
        if self.last_check_box == True:
            return f"--{self.name} {self.last_spin_value}"
        else:
            return ""



# -----------------------------------------------------------


class ParamBooleanWithInputWithUnity(Param):
    def __init__(
        self,
        name: str,
        label: str,
        values: list[str],
        optional: bool = False,
        description: str = "",
        expected_type=str,
    ) -> None:
        super().__init__(name, description=description, label=label)
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



# TODO: implement header for input with checkbox
# -----------------------------------------------------------

class ParamComponent(Param):
    def __init__(
        self,
        name: str,
        label: str,
        values: list[str],
        optional: bool = False,
        description: str = "",
        expected_type=str,
    ) -> None:
        super().__init__(name, description=description, label=label)
        self.question_label = None
        self.combo_box = None
        self.extra_rows = 0
        self.description = description

        self.combo_boxes = []
        self.last_combo_boxes = []
        self.optional = optional
        self.values = values
        self.manager: Optional[DependencyManager] = None

    def build_widget(self, row: int, label: str, grid_layout: QGridLayout):
            header = self.build_header(label, self.description, self.optional)
            grid_layout.addWidget(header, row, 0)
            self.combo_boxes = []

            # Build existing combos for extra_rows
            for i in range(self.extra_rows):
                used_values = [cb.currentText() for cb in self.combo_boxes]
                available_values = [v for v in self.values if v not in used_values]
                combo = QComboBox()
                combo.setPlaceholderText("Extra input")
                combo.addItem(available_values[0])
                # Set current text to last_combo_boxes[i] if exists, else next available
                if self.last_combo_boxes and i < len(self.last_combo_boxes):
                    combo.setCurrentText(self.last_combo_boxes[i])
                elif available_values:
                    combo.setCurrentText(available_values[0])
                remove_button = QPushButton("✕")
                remove_button.setFixedWidth(30)
                remove_button.clicked.connect(
                    lambda _, c=combo, b=remove_button: self.remove_widget_pair(
                        c, b, grid_layout
                    )
                )
                grid_layout.addWidget(combo, row, 1)
                grid_layout.addWidget(remove_button, row, 2)
                self.combo_boxes.append(combo)
                row += 1

            add_button = QPushButton("Add membrane")
            grid_layout.addWidget(add_button, row, 1)
            add_button.clicked.connect(lambda: self.add_component_row(row, grid_layout))
    
    def _on_value_changed(self):
        if self.manager is not None:
            self.store_value()
            self.manager.notify_change(self)

    def add_component_row(self, row: int, grid_layout: QGridLayout):
            self.component_base_row = row
            self.extra_rows += 1

            used_values = [cb.currentText() for cb in self.combo_boxes]
            available_values = [v for v in self.values if v not in used_values]
            combo = QComboBox()
            combo.setPlaceholderText("Extra input")
            combo.addItems(self.values)
            # Set to next available value if any
            if available_values:
                combo.setCurrentText(available_values[0])
            self.combo_boxes.append(combo)

            remove_button = QPushButton("✕")
            remove_button.setFixedWidth(30)

            grid_layout.addWidget(combo, row + 1, 1)
            grid_layout.addWidget(remove_button, row + 1, 2)

            combo.currentIndexChanged.connect(self._on_value_changed)
            remove_button.clicked.connect(
                lambda _, c=combo, b=remove_button: self.remove_widget_pair(c, b, grid_layout)
            )
            self._on_value_changed()
    

    def get_value(self):
        return len(self.last_combo_boxes)

    def set_value_from_import(self, values: dict):
        value = values[self.name] 
        self.extra_rows = len(value)
        self.category.update_category()
        debug_print(f"The param {self.name} was imported")

    def get_items(self):
        return self.last_combo_boxes

    def store_value(self):
        self.last_combo_boxes.clear()
        for el in self.combo_boxes:
            if el.currentText() != "":
                self.last_combo_boxes.append(el.currentText())

    def remove_widget_pair(
        self, widget1: QWidget, widget2: QWidget, layout: QGridLayout
    ):
        self._on_value_changed()
        layout.removeWidget(widget1)
        layout.removeWidget(widget2)
        widget1.deleteLater()
        widget2.deleteLater()

        self.extra_rows = max(0, self.extra_rows - 1)
        self.category.update_category()
        self._on_value_changed()

    def row_span(self) -> int:
        return 1 + self.extra_rows


    def to_perm_entry(self) -> Optional[str]:
        if self.last_combo_boxes:
            values = " ".join(str(x) for x in self.last_combo_boxes)
            return f"{self.name} := {values}"
        return None


# -----------------------------------------------------------
class ParamFixedWithInput(Param):
    def __init__(
        self,
        name: str,
        label: str,
        optional: bool = False,
        description: str = "",
        expected_type=str,
        default: Optional[int] = None,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
        step: Optional[int] = None,
        hidden: bool = False,
    ) -> None:
        super().__init__(name, label=label)
        self.question_label = None
        self.line_edit = None
        self.combo_box = None
        self.description = description

        self.last_line_edit = ""
        self.last_combo_box = ""

        self.row_nb = 1

        self.optional = optional
        self.rows = 0
        self.default = default

        self.min_value = min_value
        self.max_value = max_value
        self.step = step
        self.sizes = {}
        self.keys = ["set components", "set mem_types_set"]
        self.sizes = {k: 0 for k in self.keys}
        self.last_line_edits = []
        self.line_edits = []
        self.hidden = hidden
        self.manager: Optional[DependencyManager] = None
        self.expected_type = expected_type
        self.elements = dict(zip([i for i in range(1, self.row_nb)], [{k: None for k in ("min_value", "max_value")}]*self.row_nb))
        self.widgets = []
        pass

    def set_rows_nb(self, rows: int, source: Param):
        self.sizes[source.name] = rows
        self.row_nb = 1
        for val in self.sizes.values():
            self.row_nb *= int(val)
        # self.row_nb = rows

    def set_rows(self, rows: int, source: Param):
        self.sizes[source.name] = rows
        self.row_nb = rows

    def set_row(self, rows: int):
        self.row_nb = rows


    def build_widget(self, row: int, label: str, grid_layout: QGridLayout):
        self.line_edits.clear()
        self.widgets.clear()
        if self.hidden:
            return
        self.row = row
        # self.label = label
        self.grid_layout = grid_layout
        self.label = label
        header = self.build_header(label, self.description, self.optional)
        grid_layout.addWidget(header, row, 0)
        row += 1

        self.line_edits = []

        old_elements = getattr(self, "elements", {})
        self.elements = {
            i: {
                "min_value": old_elements.get(i, {}).get("min_value"),
                "max_value": old_elements.get(i, {}).get("max_value"),
            }
            for i in range(self.row_nb)
        }

        for r in range(self.row_nb):
            label_widget = QLabel(f"{r+1}")
            grid_layout.addWidget(label_widget, row + r, 0)
            for c in range(1, 2):
                if self.expected_type == int:
                    line_edit = QSpinBox()
                else:
                    line_edit = QDoubleSpinBox()

                component = self.elements[r]

                if self.min_value is not None:
                    if self.elements[r]["min_value"] is None:
                        component["min_value"] = self.min_value
                if self.max_value is not None:
                    if self.elements[r]["max_value"] is None:
                        component["max_value"] = self.max_value

                if component["min_value"] is not None:
                    line_edit.setMinimum(component["min_value"])
                if component["max_value"] is not None:
                    line_edit.setMaximum(component["max_value"])

                if self.default is not None:
                    if isinstance(line_edit, QSpinBox):
                        line_edit.setValue(int(self.default))
                    else:
                        line_edit.setValue(float(self.default))

                if self.step is not None:
                    line_edit.setSingleStep(self.step)
                grid_layout.addWidget(
                    line_edit, row + r, c, alignment=Qt.AlignmentFlag.AlignCenter
                )
                if line_edit is not None:
                    # line_edit.valueChanged.connect(self._on_value_changed)
                    line_edit.valueChanged.connect(lambda _, le=line_edit: self._on_value_changed(le))
                self.widgets.extend([line_edit, label_widget])
                self.line_edits.append(line_edit)
        self.restore_value()

    def _on_value_changed(self, sender=None):
        # FIXME: move this to the param class to avoid repeating it in all the param classses
        if self.manager is not None:
            self.store_value()
            self.manager.notify_change(self, sender)
    # TODO: add a widget list everywhere

    def update_param(self):
        if getattr(self, "_updating", False):
            return
        self._updating = True
        self.store_value()
        if hasattr(self, "widgets"):
            for widget in self.widgets:
                self.grid_layout.removeWidget(widget)
                widget.deleteLater()
            self.widgets.clear()
        self.build_widget(self.row, self.label, self.grid_layout)
        self._updating = False

    def row_span(self) -> int:
        return self.row_nb + 2

    def store_value(self):
        self.last_line_edits = []
        for line_edit in self.line_edits:
            self.last_line_edits.append(line_edit.value())

    def restore_value(self):
        for index, value in enumerate(self.last_line_edits):
            if index < len(self.line_edits):
                self.line_edits[index].setValue(value)

    def hide(self):
        self.hidden = True

    def show(self):
        self.hidden = False

        # FIXME: adapt to params

    def to_config_entry(self):
        values_str = ", ".join(str(value) for value in self.last_line_edits)
        res = f"{self.name} = [{values_str}]"
        return res
    def to_data_entry(self):
        return self.to_config_entry()



# -----------------------------------------------------------
class ParamRadio(Param):
    def __init__(
        self,
        name: str,
        depends_on: Optional[dict[str, DependencyType]],
        values: list[str],
        optional: bool = False,
        expected_type=str,
        description: str = "",
    ) -> None:
        super().__init__(name)
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



# -----------------------------------------------------------

class ParamComponentSelector(Param):
    def __init__(
        self,
        name: str,
        label: str,
        values: list[str],
        optional: bool = False,
        description: str = "",
        expected_type=str,
    ) -> None:
        super().__init__(name, label=label)
        self.question_label = None
        self.description = description

        self.optional = optional
        self.rows = 1
        self.values = values
        self.last_radio_button = None
        self.components = ["compo1", "compo2", "compo3"]
        self.selected_components = []
        self.manager: Optional[DependencyManager] = None
        self.max_selected: Optional[int] = None
        self.min_selected: Optional[int] = None
        pass

    def get_value(self):
        return len(self.selected_components)

    def get_selected_items(self) -> list[str]:
        return self.selected_components


    def build_widget(self, row: int, label: str, grid_layout: QGridLayout):
        # TODO: fix the appearance
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
        dialog = ComponentWindow(self.values, self.selected_components, max_selected=self.max_selected, min_selected=self.min_selected)
        if dialog.exec():
            self.selected_components = dialog.get_selected()
            self.button.setText(f"Selected: {len(self.selected_components)}")
            self._on_value_changed()
            self.category.update_category()

    def set_value_from_import(self, values: dict):
        value = values[self.name]
        self.selected_components = value
        debug_print(f"The param {self.name} was imported")


    def _on_value_changed(self):
        if self.manager is not None:
            self.store_value()
            self.manager.notify_change(self)

    def remove_selected_component(
        self, component, grid_layout, remove_button, line_edit
    ):
        if component in self.selected_components:
            self.selected_components.remove(component)
        grid_layout.removeWidget(line_edit)
        grid_layout.removeWidget(remove_button)
        line_edit.deleteLater()
        remove_button.deleteLater()
        self.category.update_category()

    def restore_value(self):
        return

    def row_span(self) -> int:
        return 1 + len(self.selected_components)

    def store_value(self):
        return

    def to_data_entry(self) -> Optional[str]:
        if len(self.selected_components) > 0:
            values = ' '.join(f'"{str(x)}"' for x in self.selected_components)
            return f"{self.name} := {values}"
        else:
            return None


# -----------------------------------------------------------
class ParamSpinBoxWithBool(Param):
    def __init__(
        self,
        name: str,
        label: str,
        optional: bool = False,
        expected_type=str,
        description: str = "",
    ) -> None:
        super().__init__(name, description=description, label=label)
        self.question_label = None
        self.time_spin_box = None
        self.last_spin_box = ""
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
        label: str,
        hidden: bool = False,
        optional: bool = False,
        description: str = "",
        expected_type=str,
        select_dir: bool = False,
        default: Optional[str] = None
    ) -> None:
        super().__init__(name, description=description, label=label)
        self.question_label = None
        self.line_edit = None
        self.button = None
        self.last_path = ""
        self.optional = optional
        self.description = description
        self.hidden = hidden
        self.select_dir = select_dir
        self.default = default
        self.widgets = []

    def build_widget(self, row: int, label: str, grid_layout: QGridLayout):
        self.widgets.clear()
        self.row = row
        self.label = label
        self.grid_layout = grid_layout

        if self.hidden:
            return
        header = self.build_header(label, self.description, self.optional)
        grid_layout.addWidget(header, row, 0)

        if self.default is not None:
            self.line_edit

        self.line_edit = QLineEdit()
        self.line_edit.setReadOnly(True)

        if self.default is not None:
            self.line_edit.setText(self.default)

        self.button = QPushButton("Browse")
        self.button.clicked.connect(self.open_file_dialog)

        grid_layout.addWidget(self.line_edit, row, 1)
        grid_layout.addWidget(self.button, row, 2)

        self.widgets.extend([self.line_edit, self.button])
        self.restore_value()

    def open_file_dialog(self):
        from PyQt6.QtWidgets import QFileDialog

        if self.select_dir:
            path = QFileDialog.getExistingDirectory(
                None, "Select Directory", ""
            )
        else:
            path, _ = QFileDialog.getOpenFileName(
                None, "Select File", "", "All Files (*)"
            )
        if path:
            if self.line_edit:
                self.line_edit.setText(path)
                self.last_path = path

    def restore_value(self):
        if self.last_path and self.line_edit:
            self.line_edit.setText(self.last_path)

    def hide(self):
        self.hidden = True

    def update_param(self):
        # NOTE: does not work
        if getattr(self, "_updating", False):
            return
        self._updating = True
        self.store_value()
        if hasattr(self, "widgets"):
            for widget in self.widgets:
                self.grid_layout.removeWidget(widget)
                widget.deleteLater()
            self.widgets.clear()
        self.build_widget(self.row, self.label, self.grid_layout)
        self._updating = False

    def show(self):
        self.hidden = False

    def get_path(self) -> str:
        return self.last_path

    def store_value(self):
        if not self.hidden:
            if self.line_edit is not None:
                self.last_path = self.line_edit.text()


    def to_command_arg(self) -> str:
        if self.last_path:
            return f'--{self.name} "{self.last_path}"'
        return ""

    def to_config_entry(self) -> Optional[str]:
        if self.last_path:
            return f'{self.name} = {self.last_path}'
        return None


# -----------------------------------------------------------


class ParamCategory(QWidget):
    def __init__(self, name: str, param: list[Param]) -> None:
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
        # for label, param_obj in self.param.items():
        for param_obj in self.param:
            param_obj.category = self
        # for label, param_obj in self.param.items():
        for param_obj in self.param:
            param_obj.build_widget(self.row, param_obj.label, self.grid_layout)
            self.row += param_obj.row_span()
        return self

    def store_values(self):
        for param in self.param:
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
                    for param in self.param:
                        if hasattr(param, "line_edit") and param.line_edit is widget:
                            param.line_edit = None
                        if hasattr(param, "combo_box") and param.combo_box is widget:
                            param.combo_box = None
                        if hasattr(param, "check_box") and param.check_box is widget:
                            param.check_box = None

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

# -----------------------------------------------------------
class ParamFixedWithSelect(Param):
    def __init__(
        self,
        name: str,
        values: list[str],
        optional: bool = False,
        description: str = "",
        expected_type=str,
        label: str = "",
        default: Optional[int] = None,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
        step: Optional[int] = None,
        hidden: bool = False,
    ) -> None:
        super().__init__(name, description=description, label=label)
        self.question_label = None
        self.line_edit = None
        self.combo_box = None
        self.description = description

        self.last_line_edit = ""
        self.last_combo_box = ""

        self.row_nb = 1

        self.optional = optional
        self.rows = 0
        self.default = default

        self.min_value = min_value
        self.values = values
        self.max_value = max_value
        self.step = step
        self.sizes = {}
        self.keys = ["set components", "set mem_types_set"]
        self.sizes = {k: 0 for k in self.keys}
        self.hidden = hidden
        pass

    def set_rows_nb(self, rows: int, source: Param):
        self.sizes[source.name] = rows
        self.row_nb = 1
        for val in self.sizes.values():
            self.row_nb *= int(val)
        # self.row_nb = rows

    def set_rows(self, rows: int, source: Param):
        self.sizes[source.name] = rows
        self.row_nb = rows



    def build_widget(self, row: int, label: str, grid_layout: QGridLayout):
        if self.hidden:
            return
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
                line_edit = QComboBox()
                line_edit.addItems(self.values)

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

    def hide(self):
        self.hidden = True

    def show(self):
        self.hidden = False

    def store_value(self):
        if self.line_edit is not None:
            self.last_line_edit = self.line_edit.text()
            pass
        if self.combo_box is not None:
            self.last_combo_box = self.combo_box.currentText()
        pass


# -----------------------------------------------------------

class ParamFixedPerm(Param):
    def __init__(
        self,
        name: str,
        membranes: list[str] = [],
        components: list[str] = [],
        optional: bool = False,
        expected_type=str,
        description: str = "",
        label: str = "",
        default: Optional[float] = None,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        step: Optional[float] = None,
        hidden: bool = False,
    ) -> None:
        super().__init__(name, description=description, label=label)
        self.question_label = None
        self.line_edits = {}  # {(membrane, component): QDoubleSpinBox}
        self.last_line_edits = {}  # {(membrane, component): str}
        self.optional = optional
        self.expected_type = expected_type
        self.default = default
        self.min_value = min_value
        self.max_value = max_value
        self.step = step
        self.header = None
        self.hidden = hidden
        self.manager: Optional[DependencyManager] = None
        self.membranes = membranes
        self.components = components
        self.widgets = []

    def build_widget(self, row: int, label: str, grid_layout: QGridLayout):
        self.line_edits.clear()
        self.row = row
        self.grid_layout = grid_layout
        self.label = label
        self.widgets.clear()
        if self.hidden:
            return
        header = self.build_header(label, self.description, self.optional)
        self.header = header
        grid_layout.addWidget(self.header, row, 0, 1, 3)
        # Add table headers
        grid_layout.addWidget(QLabel("Membrane"), row + 1, 0)
        grid_layout.addWidget(QLabel("Component"), row + 1, 1)
        grid_layout.addWidget(QLabel("Permeability"), row + 1, 2)
        current_row = row + 2
        for membrane in self.membranes:
            for component in self.components:
                label_membranes = QLabel(str(membrane))
                grid_layout.addWidget(label_membranes, current_row, 0)
                label_component = QLabel(str(component))
                grid_layout.addWidget(label_component, current_row, 1)
                # FIXME: use create spin box for this
                line_edit = QDoubleSpinBox()
                line_edit = self.create_spinbox(self.max_value, self.min_value, self.step, self.default)
                # if self.min_value is not None:
                #     line_edit.setMinimum(self.min_value)
                # if self.max_value is not None:
                #     line_edit.setMaximum(self.max_value)
                # if self.default is not None:
                #     line_edit.setValue(self.default)
                # if self.step is not None:
                #     line_edit.setSingleStep(self.step)
                key = (membrane, component)
                self.line_edits[key] = line_edit
                self.restore_value(key)
                grid_layout.addWidget(line_edit, current_row, 2)
                line_edit.valueChanged.connect(lambda _, k=key: self._on_value_changed())
                current_row += 1
                self.widgets.extend([label_component, label_membranes, line_edit])

    def _on_value_changed(self):
        if self.manager is not None:
            self.store_value()
            self.manager.notify_change(self)

    def update_param(self):
        if getattr(self, "_updating", False):
            debug_print("updating")
            return
        self._updating = True
        self.store_value()
        if hasattr(self, "widgets"):
            for widget in self.widgets:
                self.grid_layout.removeWidget(widget)
                widget.deleteLater()
            self.widgets.clear()
        self.build_widget(self.row, self.label, self.grid_layout)
        self._updating = False

    def set_value(self, membranes: list[str], components: list[str]):
        self.membranes = membranes
        self.components = components

    def set_membranes(self, membranes: list[str]):
        self.membranes = membranes

    def set_components(self, components: list[str]):
        self.components = components

    # def set_value(self, key, value):
    #     if key in self.line_edits:
    #         line_edit = self.line_edits[key]
    #         if hasattr(line_edit, "setDecimals"):
    #             if isinstance(value, float):
    #                 str_val = str(value)
    #                 if '.' in str_val:
    #                     decimals = len(str_val.split('.')[-1].rstrip('0'))
    #                 else:
    #                     decimals = 2
    #                 line_edit.setDecimals(decimals)
    #             else:
    #                 line_edit.setDecimals(0)
    #         line_edit.setMaximum(1e10)
    #         line_edit.setValue(value)
    def set_value_from_import(self, values: dict):
        value: dict[str, dict[str, Union[int, float]]] = values[self.name]
        self.membranes = value.keys()
        components = set()
        for subdict in value.values():
            components.update(subdict.keys())
        for membrane, comp_values in value.items():
            for el, spin_value in comp_values.items():
                spin = self.create_spinbox(self.max_value, self.min_value, self.step, self.default)
                self.set_spin_value(spin, spin_value)
                key = (membrane, el)
                self.line_edits[key] = spin
        self.components = list(components)
        debug_print(f"The param {self.name} was imported")

    def restore_value(self, key):
        if key in self.line_edits and key in self.last_line_edits and self.last_line_edits[key] != "":
            try:
                value = int(self.last_line_edits[key])
            except ValueError:
                try:
                    value = float(self.last_line_edits[key])
                except ValueError:
                    return
            self.line_edits[key].setValue(value)

    def store_value(self):
        self.last_line_edits.clear()
        if not self.hidden:
            for key, line_edit in self.line_edits.items():
                self.last_line_edits[key] = str(line_edit.value())

    def get_value(self) -> dict:
        return self.last_line_edits

    def hide(self):
        self.hidden = True

    def show(self):
        self.hidden = False


    def to_config_entry(self) -> Optional[str]:
        if self.last_line_edits:
            return f"{self.name} = {self.last_line_edits}"

    def to_data_entry(self) -> Optional[str]:
        if self.last_line_edits:
            return f"{self.name} := {self.last_line_edits}"

    def to_perm_entry(self) -> Optional[str]:
        if self.last_line_edits:
            lines = []
            for (membrane, component), value in self.last_line_edits.items():
                lines.append(f"{membrane}\t{component}\t{value}")
            return f"{self.name} :=\n" + "\n".join(lines)
        return None

    def to_eco_entry(self) -> Optional[str]:
        if self.last_line_edits:
            return f"{self.name} := {self.last_line_edits}"
    def row_span(self) -> int:
        return 2 + len(self.components) * len(self.membranes)


# TODO: search filter

# -----------------------------------------------------------
class ParamFixedMembrane(Param):
    def __init__(
        self,
        name: str,
        label: str,
        hidden: bool = False,
        membranes: list[str] = [],
        optional: bool = False,
        description: str = "",
        expected_type=str,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
        step: float = 1.0,
        decimals: int = 2,
        default: Optional[int] = None,
    ) -> None:
        super().__init__(name, description=description, label=label)
        self.question_label = None
        self.spin_boxes = []
        self.last_spin_boxes = []
        self.optional = optional
        self.membranes = membranes
        self.manager: Optional[DependencyManager] = None
        self.description = description
        self.hidden = hidden
        self.min_value = min_value
        self.max_value = max_value
        self.step = step
        self.decimals = decimals
        self.default = default
        self.step = step
        self.expected_type = expected_type
        self.elements = dict(zip([i for i in range(1, len(self.membranes))], [{k: None for k in ("min_value", "max_value")}]*(len(self.membranes))))

    def build_widget(self, row: int, label: str, grid_layout: QGridLayout):
        self.row = row
        self.grid_layout = grid_layout
        self.label = label
        self.spin_boxes.clear()
        if self.hidden:
            return
        header = self.build_header(label, self.description, self.optional)
        grid_layout.addWidget(header, row, 0)
        self.spin_boxes = []
        grid_layout.addWidget(QLabel("Membrane"), row + 1, 0)
        grid_layout.addWidget(QLabel("Value"), row + 1, 1)
        current_row = row + 2
        old_elements = getattr(self, "elements", {})
        self.elements = {
            i: {
                "min_value": old_elements.get(i, {}).get("min_value"),
                "max_value": old_elements.get(i, {}).get("max_value"),
            }
            for i in range(len(self.membranes))
        }
        for i, membrane in enumerate(self.membranes):
            grid_layout.addWidget(QLabel(str(membrane)), current_row, 0)
            if self.expected_type == int:
                spin = QSpinBox()
            else:
                spin = QDoubleSpinBox()

            component = self.elements[i]
            if self.min_value is not None:
                if self.elements[i]["min_value"] is None:
                    component["min_value"] = self.min_value
            if self.max_value is not None:
                if self.elements[i]["max_value"] is None:
                    component["max_value"] = self.max_value
            if component["min_value"] is not None:
                spin.setMinimum(component["min_value"])
            if component["max_value"] is not None:
                spin.setMaximum(component["max_value"])

            if self.default is not None:
                if isinstance(spin, QSpinBox):
                    spin.setValue(int(self.default))
                else:
                    spin.setValue(float(self.default))
            if self.step is not None:
                spin.setSingleStep(int(self.step))
            grid_layout.addWidget(spin, current_row, 1)
            current_row += 1
            if spin is not None:
                spin.valueChanged.connect(lambda _, le=spin: self._on_value_changed(le))
            self.spin_boxes.append(spin)
        self.restore_value()

    def _on_value_changed(self, sender=None):
        if getattr(self, "_updating", False):
            return
        self._updating = True
        if self.manager is not None:
            self.store_value()
            self.manager.notify_change(self, sender)
        self._updating = False

    def set_value_from_import(self, values: dict):
        value: dict[str, Union[int, float]] = values[self.name]
        self.membranes = value.keys() 
        self.spin_boxes = []
        for i, value_ in enumerate(value.values()):
            spin = self.create_spinbox(self.min_value, self.max_value, self.step, self.default) 
            self.set_spin_value(spin, value_)
            self.spin_boxes.append(spin)
        debug_print(f"The param {self.name} was imported")

        pass

    def set_membranes(self, membranes: list[str]):
        self.membranes = membranes

    def get_value(self):
        return len(self.last_spin_boxes)

    def get_items(self):
        return self.last_spin_boxes

    def store_value(self):
        self.last_spin_boxes.clear()
        if not self.hidden:
            for el in self.spin_boxes:
                if isinstance(el, QSpinBox):
                    self.last_spin_boxes.append(int(el.value()))
                else:
                    self.last_spin_boxes.append(float(el.value()))

    def restore_value(self):
        for index, value in enumerate(self.last_spin_boxes):
            if index < len(self.spin_boxes):
                self.spin_boxes[index].setValue(value)

    def update_param(self):
        if getattr(self, "_updating", False):
            return
        self._updating = True
        self.store_value()  
        self.build_widget(self.row, self.label, self.grid_layout)
        self._updating = False

    def hide(self):
        self.hidden = True

    def show(self):
        self.hidden = False

    def row_span(self) -> int:
        return 2 + len(self.membranes)

    def to_perm_entry(self) -> Optional[str]:
        if self.hidden:
            return None
        if self.last_spin_boxes and self.membranes:
            lines = [
                    f'{component} :=\t{value}'
                for component, value in zip(self.membranes, self.last_spin_boxes)
            ]
            content = "\n".join(lines)
            return f"{self.name} :=\n{content}\n"
        return None


# -----------------------------------------------------------
class ParamMembraneSelect(Param):
    def __init__(
        self,
        name: str,
        label: str,
        hidden: bool = False,
        membranes: list[str] = [],
        values: Optional[dict[str, list[str]]] = None,
        optional: bool = False,
        description: str = "",
    ) -> None:
        super().__init__(name, description=description, label=label)
        self.question_label = None
        self.combo_boxes = []
        self.last_combo_boxes = []
        self.optional = optional
        self.membranes = membranes
        self.values = values or {}
        self.manager: Optional[DependencyManager] = None
        self.description = description
        self.hidden = hidden

    def build_widget(self, row: int, label: str, grid_layout: QGridLayout):
        header = self.build_header(label, self.description, self.optional)
        grid_layout.addWidget(header, row, 0)
        self.combo_boxes = []
        grid_layout.addWidget(QLabel("Membrane"), row + 1, 0)
        grid_layout.addWidget(QLabel("Option"), row + 1, 1)
        current_row = row + 2
        for membrane in self.membranes:
            grid_layout.addWidget(QLabel(str(membrane)), current_row, 0)
            combo = QComboBox()
            combo.addItems(self.values)
            self.combo_boxes.append(combo)
            grid_layout.addWidget(combo, current_row, 1)
            current_row += 1
        self.restore_value()

    def set_membranes(self, membranes: list[str]):
        self.membranes = membranes

    def _on_value_changed(self):
        if self.manager is not None:
            self.store_value()
            self.manager.notify_change(self)

    def restore_value(self):
        for idx, value in enumerate(self.last_combo_boxes):
            if idx < len(self.combo_boxes):
                combo = self.combo_boxes[idx]
                index = combo.findText(value)
                if index != -1:
                    combo.setCurrentIndex(index)

    def set_value_from_import(self, values: dict):
        self.combo_boxes = []
        value = values[self.name]
        self.membranes = value.keys()
        for el in value.values():
            combo = QComboBox()
            combo.addItems(self.values)
            index = combo.findText(el)
            if index != -1:
                combo.setCurrentIndex(index)
            self.combo_boxes.append(combo)
        debug_print(f"The param {self.name} was imported")

    def get_value(self):
        return len(self.last_combo_boxes)

    def get_items(self):
        return self.last_combo_boxes

    def store_value(self):
        self.last_combo_boxes.clear()
        if not self.hidden:
            for combo in self.combo_boxes:
                self.last_combo_boxes.append(combo.currentText())

    def row_span(self) -> int:
        return 3 + len(self.membranes)

    def to_perm_entry(self) -> Optional[str]:
        if self.hidden:
            return None
        if self.last_combo_boxes and self.membranes:
            lines = [
                f'{component}  \t{value}'
                for component, value in zip(self.membranes, self.last_combo_boxes)
            ]
            content = "\n".join(lines)
            return f"{self.name} :=\n{content}\n"
        return None


# -----------------------------------------------------------

class ParamMemType(Param):
    def __init__(
        self,
        name: str,
        label: str,
        hidden: bool = False,
        num_membrane_floors: int = 1,
        membranes: list[str] = [],
        optional: bool = False,
        description: str = "",
    ) -> None:
        super().__init__(name, description=description, label=label)
        self.question_label = None
        self.combo_boxes = []
        self.last_combo_boxes = []
        self.optional = optional
        self.num_membrane_floors = num_membrane_floors
        self.membranes = membranes
        self.manager: Optional[DependencyManager] = None
        self.description = description
        self.hidden = hidden

    def build_widget(self, row: int, label: str, grid_layout: QGridLayout):
        self.row = row
        self.label = label
        self.grid_layout = grid_layout
        header = self.build_header(label, self.description, self.optional)
        grid_layout.addWidget(header, row, 0)
        self.combo_boxes = []
        grid_layout.addWidget(QLabel("Floor"), row + 1, 0)
        grid_layout.addWidget(QLabel("Membrane Type"), row + 1, 1)
        current_row = row + 2
        for i in range(self.num_membrane_floors):
            grid_layout.addWidget(QLabel(str(i + 1)), current_row, 0)
            combo = QComboBox()
            combo.addItems(self.membranes)
            self.combo_boxes.append(combo)
            grid_layout.addWidget(combo, current_row, 1)
            current_row += 1
        self.restore_value()

    def restore_value(self):
        for idx, value in enumerate(self.last_combo_boxes):
            if idx < len(self.combo_boxes):
                combo = self.combo_boxes[idx]
                index = combo.findText(value)
                if index != -1:
                    combo.setCurrentIndex(index)

    def update_param(self):
        if getattr(self, "_updating", False):
            return
        self._updating = True
        self.store_value()  
        self.build_widget(self.row, self.label, self.grid_layout)
        self._updating = False


    def set_num_components(self, num_components: int):
        self.num_membrane_floors = num_components

    def set_membranes(self, membranes: list[str]):
        self.membranes = membranes

    def set_floors(self, floors: int):
        self.num_membrane_floors = floors

    def set_value_from_import(self, values: dict):
        value = values[self.name]
        if not value:
            return
        self.membranes = value.keys()
        self.num_membrane_floors = max(max(lst) for lst in value.values() if lst)
        self.combo_boxes = []
        res = {num: key for key, nums in value.items() for num in nums}
        res_ord = OrderedDict(sorted(res.items()))
        for key, el in res_ord.items():
            combo = QComboBox()
            combo.addItems(self.membranes)
            index = combo.findText(el)
            if index != -1:
                combo.setCurrentIndex(index)
            self.combo_boxes.append(combo)
        debug_print(f"The param {self.name} was imported")
        pass

    def _on_value_changed(self):
        if self.manager is not None:
            self.store_value()
            self.manager.notify_change(self)

    def get_value(self):
        return len(self.last_combo_boxes)

    def get_items(self):
        return self.last_combo_boxes

    def store_value(self):
        self.last_combo_boxes.clear()
        for combo in self.combo_boxes:
            self.last_combo_boxes.append(combo.currentText())

    def row_span(self) -> int:
        return 2 + self.num_membrane_floors

    def to_perm_entry(self) -> Optional[str]:
        if self.hidden:
            return None
        if self.last_combo_boxes and self.num_membrane_floors:
            lines = [
                f"{i+1}\t{value}"
                for i, value in enumerate(self.last_combo_boxes)
            ]
            content = "\n".join(lines)
            return f"{self.name} :=\n{content}\n"
        return None


# -----------------------------------------------------------
class ParamFixedComponent(Param):
    def __init__(
        self,
        name: str,
        label: str,
        hidden: bool = False,
        components: list[str] = [],
        optional: bool = False,
        description: str = "",
        expected_type=str,
        default: Optional[int] = None,
        min_value: float = 0.0,
        max_value: float = 1e6,
        step: float = 1.0,
        decimals: int = 2,
    ) -> None:
        super().__init__(name, description=description, label=label)
        self.question_label = None
        self.spin_boxes = []
        self.last_spin_boxes = []
        self.optional = optional
        self.components = components
        self.manager: Optional[DependencyManager] = None
        self.description = description
        self.hidden = hidden
        self.min_value = min_value
        self.max_value = max_value
        self.step = step
        self.decimals = decimals
        self.expected_type = expected_type
        self.default = default


    def build_widget(self, row: int, label: str, grid_layout: QGridLayout):
        header = self.build_header(label, self.description, self.optional)
        self.row = row
        self.label = label
        grid_layout.addWidget(header, row, 0)
        self.spin_boxes = []
        grid_layout.addWidget(QLabel("Component"), row + 1, 0)
        grid_layout.addWidget(QLabel("Value"), row + 1, 1)
        current_row = row + 2
        for component in self.components:
            grid_layout.addWidget(QLabel(str(component)), current_row, 0)
            spin = QDoubleSpinBox()
            spin.setMinimum(self.min_value)
            spin.setMaximum(self.max_value)
            spin.setSingleStep(self.step)
            spin.setDecimals(self.decimals)
            spin.setValue(self.min_value)
            if self.default is not None:
                spin.setValue(self.default)
            self.spin_boxes.append(spin)
            grid_layout.addWidget(spin, current_row, 1)
            current_row += 1
        self.grid_layout = grid_layout
        self.restore_value()

    def set_components(self, components: list[str]):
        self.components = components

    def restore_value(self):
        for idx, value in enumerate(self.last_spin_boxes):
            if idx < len(self.spin_boxes):
                try:
                    val = float(value)
                    self.spin_boxes[idx].setValue(val)
                except ValueError:
                    continue

    def set_value_from_import(self, values: dict):
        self.spin_boxes = []
        value = values[self.name].copy()
        self.components = value.keys()
        for component, value_ in value.items():
            spin = self.create_spinbox(self.min_value, self.max_value, self.step, self.default)
            self.set_spin_value(spin, value_)
            self.spin_boxes.append(spin)
        debug_print(f"The param {self.name} was imported")

    def _on_value_changed(self):
        if self.manager is not None:
            self.store_value()
            self.manager.notify_change(self)

    def update_param(self):
        if getattr(self, "_updating", False):
            return
        self._updating = True
        self.store_value()  
        self.build_widget(self.row, self.label, self.grid_layout)
        self._updating = False

    def get_value(self):
        return len(self.last_spin_boxes)

    def get_items(self):
        return self.last_spin_boxes

    def store_value(self):
        self.last_spin_boxes.clear()
        for el in self.spin_boxes:
            self.last_spin_boxes.append(str(el.value()))

    def row_span(self) -> int:
        return 3 + len(self.components)

    def to_data_entry(self) -> Optional[str]:
        if self.hidden:
            return None
        if self.last_spin_boxes and self.components:
            lines = [
                f'\t"{component}"\t{value}'
                for component, value in zip(self.components, self.last_spin_boxes)
            ]
            content = "\n".join(lines)
            return f"{self.name} :=\n{content}\n"
        return None


# -----------------------------------------------------------
class ParamFixedComponentWithCheckbox(Param):
    def __init__(
        self,
        name: str,
        label: str,
        # values: list[str],
        optional: bool = False,
        description: str = "",
        expected_type=str,
        hidden: bool = False,
        values: Optional[list[str]] = []
    ) -> None:
        super().__init__(name, description=description, label=label)
        self.checkbox = None
        self.combo_boxes = []
        self.extra_rows = 0
        self.last_combo_boxes = []
        self.spin_boxes = []
        self.last_spin_boxes: list[str] = []
        self.hidden = hidden
        self.values = values
        self.manager = None
        self.last_check_box = None

    def build_widget(self, row: int, label: str, grid_layout: QGridLayout):
        self.checkbox = QCheckBox(label)
        self._build_component_grid(row + 1, grid_layout)
        if self.last_check_box is not None:
            self.checkbox.setChecked(self.last_check_box)
            self._set_grid_visible(self.last_check_box)
        else:
            self.checkbox.setChecked(False)
            self._set_grid_visible(False)
        # self.checkbox.setChecked(False)
        self.checkbox.stateChanged.connect(self._on_checkbox_changed)
        grid_layout.addWidget(self.checkbox, row, 0, 1, 2)
        # self._set_grid_visible(False)

    def _build_component_grid(self, row: int, grid_layout: QGridLayout):
        self.grid_widgets = []
        self.combo_boxes = []
        self.spin_boxes = []

        used_values = set(self.last_combo_boxes)

        if self.extra_rows > 0:
            for i in range(self.extra_rows):
                combo = QComboBox()
                spin_box = QSpinBox()
                combo.setPlaceholderText("Extra input")
                if self.values is not None:
                    available_values = [v for v in self.values if v not in used_values or v == self.last_combo_boxes[i]]
                    combo.addItems(available_values)
                if self.last_combo_boxes and i < len(self.last_combo_boxes):
                    combo.setCurrentText(self.last_combo_boxes[i])
                if self.last_spin_boxes and i < len(self.last_spin_boxes):
                    spin_box.setValue(int(self.last_spin_boxes[i]))
                remove_button = QPushButton("✕")
                remove_button.setFixedWidth(30)
                remove_button.clicked.connect(
                        lambda _, c=combo, b=remove_button, a=spin_box: self.remove_widget_pair(
                        c, b, grid_layout, a
                    )
                )
                label = QLabel(self.name)
                grid_layout.addWidget(label, row, 1)
                grid_layout.addWidget(combo, row, 2)
                grid_layout.addWidget(spin_box, row, 3)
                grid_layout.addWidget(remove_button, row, 4)
                self.combo_boxes.append(combo)
                self.spin_boxes.append(spin_box)
                self.grid_widgets.extend([label, combo, remove_button, spin_box])
                row += 1

        extra_combo = QComboBox()
        extra_combo.setPlaceholderText("Extra input")
        if self.values is not None:
            available_values = [v for v in self.values if v not in used_values]
            extra_combo.addItems(available_values)
        self.combo_boxes.append(extra_combo)
        grid_layout.addWidget(extra_combo, row, 2)
        extra_combo.currentIndexChanged.connect(
            lambda: self.add_component_row(row, grid_layout)
        )
        self.grid_widgets.append(extra_combo)

    def remove_widget_pair(
            self, widget1: QWidget, widget2: QWidget, layout: QGridLayout,widget3: Optional[QWidget] = None, 
    ):
        layout.removeWidget(widget1)
        layout.removeWidget(widget2)
        layout.removeWidget(widget3)
        widget1.deleteLater()
        widget2.deleteLater()
        if widget3 is not None:
            widget3.deleteLater()
        if widget1 in self.combo_boxes:
            self.combo_boxes.remove(widget1)

        self.extra_rows = max(0, self.extra_rows - 1)
        # self.store_value()
        value = widget1.currentText()
        if value in self.last_combo_boxes:
            self.last_combo_boxes.remove(value)
        self.category.update_category()

    def add_component_row(self, row: int, grid_layout: QGridLayout):
        self.component_base_row = row
        self.extra_rows += 1

        combo = QComboBox()
        combo.setPlaceholderText("BB input")
        combo.addItems(["Item 1", "Item 2", "Item 3"])
        combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.combo_boxes.append(combo)

        remove_button = QPushButton("✕")
        remove_button.setFixedWidth(30)
        remove_button.clicked.connect(
                lambda _, c=combo, b=remove_button: self.remove_widget_pair(
                c, b, grid_layout 
            )
        )

        grid_layout.addWidget(combo, row + 1, 2)
        grid_layout.addWidget(remove_button, row + 1, 3)

        combo.currentIndexChanged.connect(
            lambda: self.add_component_row(row + 1, grid_layout)
        )

        self.category.update_category()

    def set_values(self, values: list[str]):
        self.values = values

    def store_value(self):
        self.last_combo_boxes.clear()
        self.last_spin_boxes.clear()
        for combo in self.combo_boxes:
            if combo.currentText() != "":
                self.last_combo_boxes.append(combo.currentText())
        for spin_box in self.spin_boxes:
            self.last_spin_boxes.append(spin_box.value())
        if self.checkbox is not None:
            self.last_check_box = self.checkbox.isChecked()


    def _set_grid_visible(self, visible: bool):
        for widget in getattr(self, "grid_widgets", []):
            widget.setVisible(visible)

    def _on_checkbox_changed(self, state):
        self._set_grid_visible(bool(state))
        if not state:
            self.last_combo_boxes.clear()
        else:
            self.store_value()

    def set_value_from_import(self, values: dict):
        if self.checkbox:
            self.checkbox.setChecked(True)
        self.combo_boxes = []
        self.spin_boxes = []
        value = values[self.name]
        self.extra_rows = len(value.keys())
        self.values = value.keys()
        for key, value_ in value.items():
            combo = QComboBox()
            # FIXME: use create spin_box everywhere
            spin_box = QSpinBox()
            combo.addItems(self.values)
            combo.setCurrentText(key)
            spin_box.setValue(value_)
            self.combo_boxes.append(combo)
            self.spin_boxes.append(spin_box)
        debug_print(f"The param {self.name} was imported")


    def get_value(self):
        if self.checkbox and self.checkbox.isChecked():
            return super().get_value()
        return 0

    def row_span(self) -> int:
        return 3 + self.extra_rows

    def get_items(self):
        if self.checkbox and self.checkbox.isChecked():
            return super().get_items()
        return []

    def to_data_entry(self) -> Optional[str]:
        if self.checkbox:
            if self.checkbox.isChecked():
                if not self.last_spin_boxes or not self.last_combo_boxes:
                    return None
                lines = [f'"{self.last_combo_boxes[i]}" {self.last_spin_boxes[i]}' for i in range(min(len(self.last_combo_boxes), len(self.last_spin_boxes)))]
                return f'{self.name} :=\n' + "\n".join(lines) + "\n"

    def to_mask_entry(self) -> str:
        lines = []
        for i, value in enumerate(self.last_spin_boxes):
            lines.append(f"{self.name}:#{i+1} {value}")
        return "\n".join(lines)

    
# -----------------------------------------------------------
class ParamGrid(Param):
    def __init__(
        self,
        name: str,
        label: str,
        optional: bool = False,
        description: str = "",
        expected_type=str,
        hidden: bool = False,
    ) -> None:
        super().__init__(name, description=description, label=label)
        self.checkbox = None
        self.combo_boxes = []
        self.combo_boxes2 = []
        self.extra_rows = 0
        self.last_combo_boxes = []
        self.last_combo_boxes2 = []
        self.spin_boxes = []
        self.last_spin_boxes: list[str] = []
        self.hidden = hidden
        self.values = ["1"]
        self.manager = None
        self.last_check_box = None

    def build_widget(self, row: int, label: str, grid_layout: QGridLayout):
        self.checkbox = QCheckBox(label)
        self._build_component_grid(row + 1, grid_layout)

        if self.last_check_box is not None:
            self.checkbox.setChecked(self.last_check_box)
            self._set_grid_visible(self.last_check_box)
        else:
            self.checkbox.setChecked(False)
            self._set_grid_visible(False)

        self.checkbox.stateChanged.connect(self._on_checkbox_changed)
        grid_layout.addWidget(self.checkbox, row, 0, 1, 2)

    def _build_component_grid(self, row: int, grid_layout: QGridLayout):
        self.grid_widgets = []
        self.combo_boxes = []
        self.combo_boxes2 = []
        self.spin_boxes = []

        if self.extra_rows > 0:
            for i in range(self.extra_rows):
                combo = QComboBox()
                combo2 = QComboBox()
                spin_box = QSpinBox()
                combo.setPlaceholderText("Extra input 1")
                combo.addItems(self.values)
                combo2.addItems(self.values)
                if self.last_combo_boxes and i < len(self.last_combo_boxes):
                    combo.setCurrentText(self.last_combo_boxes[i])
                if self.last_combo_boxes2 and i < len(self.last_combo_boxes2):
                    combo2.setCurrentText(self.last_combo_boxes2[i])
                if self.last_spin_boxes and i < len(self.last_spin_boxes):
                    spin_box.setValue(int(self.last_spin_boxes[i]))
                remove_button = QPushButton("✕")
                remove_button.setFixedWidth(30)
                remove_button.clicked.connect(
                    lambda _, c=combo, c2=combo2, b=remove_button, a=spin_box: self.remove_widget_pair(
                        c, c2, b, grid_layout, a
                    )
                )
                label = QLabel(self.name)
                grid_layout.addWidget(label, row, 1)
                grid_layout.addWidget(combo, row, 2)
                grid_layout.addWidget(combo2, row, 3)
                grid_layout.addWidget(spin_box, row, 4)
                grid_layout.addWidget(remove_button, row, 5)
                self.combo_boxes.append(combo)
                self.combo_boxes2.append(combo2)
                self.spin_boxes.append(spin_box)
                self.grid_widgets.extend([label, combo, combo2, spin_box, remove_button])
                row += 1

        extra_combo = QComboBox()
        extra_combo.setPlaceholderText("Extra input ")
        extra_combo.addItems(self.values)
        self.combo_boxes.append(extra_combo)
        grid_layout.addWidget(extra_combo, row, 2)
        extra_combo.currentIndexChanged.connect(
            lambda: self.add_component_row(row, grid_layout)
        )
        self.grid_widgets.append(extra_combo)

    def remove_widget_pair(
            self, widget1: QWidget, widget2: QWidget, widget3: QWidget, layout: QGridLayout, widget4: Optional[QWidget] = None, 
    ):
        layout.removeWidget(widget1)
        layout.removeWidget(widget2)
        layout.removeWidget(widget3)
        layout.removeWidget(widget4)
        widget1.deleteLater()
        widget2.deleteLater()
        widget3.deleteLater()
        if widget4 is not None:
            widget4.deleteLater()
        if widget1 in self.combo_boxes:
            self.combo_boxes.remove(widget1)
        if widget2 in self.combo_boxes2:
            self.combo_boxes2.remove(widget2)
        if widget4 in self.spin_boxes:
            self.spin_boxes.remove(widget4)

        self.extra_rows = max(0, self.extra_rows - 1)
        value = widget1.currentText()
        value2 = widget2.currentText()
        if value in self.last_combo_boxes:
            self.last_combo_boxes.remove(value)
        if value2 in self.last_combo_boxes2:
            self.last_combo_boxes2.remove(value2)
        self.category.update_category()

    def add_component_row(self, row: int, grid_layout: QGridLayout):
        self.component_base_row = row
        self.extra_rows += 1

        combo = QComboBox()
        combo.setPlaceholderText("BB input 1")
        combo.addItems(self.values)
        combo2 = QComboBox()
        combo2.setPlaceholderText("BB input 2")
        combo2.addItems(self.values)
        combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        combo2.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.combo_boxes.append(combo)
        self.combo_boxes2.append(combo2)

        remove_button = QPushButton("✕")
        remove_button.setFixedWidth(30)
        remove_button.clicked.connect(
            lambda _, c=combo, c2=combo2, b=remove_button: self.remove_widget_pair(
                c, c2, b, grid_layout
            )
        )

        grid_layout.addWidget(combo, row + 1, 2)
        grid_layout.addWidget(combo2, row + 1, 3)
        grid_layout.addWidget(remove_button, row + 1, 4)

        combo.currentIndexChanged.connect(
            lambda: self.add_component_row(row + 1, grid_layout)
        )
        combo2.currentIndexChanged.connect(
            lambda: self.add_component_row(row + 1, grid_layout)
        )

        self.category.update_category()

    def set_values(self, values: list[str]):
        self.values = values

    def store_value(self):
        self.last_combo_boxes.clear()
        self.last_combo_boxes2.clear()
        self.last_spin_boxes.clear()
        for combo in self.combo_boxes:
            if combo.currentText() != "":
                self.last_combo_boxes.append(combo.currentText())
        for combo2 in self.combo_boxes2:
            if combo2.currentText() != "":
                self.last_combo_boxes2.append(combo2.currentText())
        for spin_box in self.spin_boxes:
            self.last_spin_boxes.append(spin_box.value())
        if self.checkbox:
            self.last_check_box = self.checkbox.isChecked()

    def _set_grid_visible(self, visible: bool):
        for widget in getattr(self, "grid_widgets", []):
            widget.setVisible(visible)

    def _on_checkbox_changed(self, state):
        self._set_grid_visible(bool(state))
        if not state:
            self.last_combo_boxes.clear()
            self.last_combo_boxes2.clear()
        else:
            self.store_value()

    def row_span(self) -> int:
        return 3 + self.extra_rows

    def to_data_entry(self) -> Optional[str]:
        if self.checkbox and self.checkbox.isChecked():
            return super().to_data_entry()
        return None

    def to_mask_entry(self) -> str:
        lines = []
        for i, value in enumerate(self.last_spin_boxes):
            lines.append(f"{self.name}:#{self.last_combo_boxes[i]},#{self.last_combo_boxes2[i]} {value}")
        return "\n".join(lines)

    
# -----------------------------------------------------------
class ParamGrid2(Param):
    def __init__(
        self,
        name: str,
        label: str,
        optional: bool = False,
        description: str = "",
        expected_type=str,
        hidden: bool = False,
        default: Optional[int] = None,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
        step: Optional[int] = None,
    ) -> None:
        super().__init__(name, description=description, label=label)
        self.checkbox = None
        self.combo_boxes = []
        self.combo_boxes2 = []
        self.extra_rows = 0
        self.last_combo_boxes = []
        self.last_combo_boxes2 = []
        self.spin_boxes = []
        self.last_spin_boxes: list[str] = []
        self.hidden = hidden
        self.membranes = []
        self.components = []
        self.manager = None
        self.last_check_box = None
        self.expected_type = expected_type
        self.default = default
        self.min_value = min_value
        self.max_value = max_value
        self.elements = dict(zip([i for i in range(1, self.extra_rows)], [{k: None for k in ("min_value", "max_value")}]*self.extra_rows))
        self.step = step

    def build_widget(self, row: int, label: str, grid_layout: QGridLayout):
        self.grid_layout = grid_layout
        self.row = row
        self.combo_boxes.clear()
        self.combo_boxes2.clear()
        self.spin_boxes.clear()
        if self.hidden:
            return
        self.checkbox = QCheckBox(label)
        self._build_component_grid(row + 1, grid_layout)
        self._set_grid_visible(True)

        header = self.build_header(label, self.description, self.optional)
        grid_layout.addWidget(header, row, 0, 1, 2)
    # TODO: in the dict add proper types for the min and max values

    def _build_component_grid(self, row: int, grid_layout: QGridLayout):
        self.grid_widgets = []
        self.combo_boxes = []
        self.combo_boxes2 = []
        self.spin_boxes = []

        old_elements = getattr(self, "elements", {})
        self.elements = {
            i: {
                "min_value": old_elements.get(i, {}).get("min_value"),
                "max_value": old_elements.get(i, {}).get("max_value"),
            }
            for i in range(self.extra_rows)
        }

        if self.extra_rows > 0:
            for i in range(self.extra_rows):
                combo = QComboBox()
                combo2 = QComboBox()
                # spin_box = QSpinBox()
                if self.expected_type == int:
                    spin_box = QSpinBox()
                else:
                    spin_box = QDoubleSpinBox()
                component = self.elements[i]

                combo.setPlaceholderText("Extra input 1")
                combo.addItems(self.membranes)
                combo2.addItems(self.components)
                if self.last_combo_boxes and i < len(self.last_combo_boxes):
                    combo.setCurrentText(self.last_combo_boxes[i])
                if self.last_combo_boxes2 and i < len(self.last_combo_boxes2):
                    combo2.setCurrentText(self.last_combo_boxes2[i])
                if self.last_spin_boxes and i < len(self.last_spin_boxes):
                    if isinstance(spin_box, QSpinBox):
                        spin_box.setValue(int(self.last_spin_boxes[i]))
                    else:
                        spin_box.setValue(float(self.last_spin_boxes[i]))

                remove_button = QPushButton("✕")
                remove_button.setFixedWidth(30)
                remove_button.clicked.connect(
                    lambda _, c=combo, c2=combo2, b=remove_button, a=spin_box: self.remove_widget_pair(
                        c, c2, b, grid_layout, a
                    )
                )
                label = QLabel(self.name)
                grid_layout.addWidget(label, row, 1)
                grid_layout.addWidget(combo, row, 2)
                grid_layout.addWidget(combo2, row, 3)
                grid_layout.addWidget(spin_box, row, 4)
                grid_layout.addWidget(remove_button, row, 5)
                self.combo_boxes.append(combo)
                self.combo_boxes2.append(combo2)
                self.spin_boxes.append(spin_box)
                self.grid_widgets.extend([label, combo, combo2, spin_box, remove_button])
                row += 1

        extra_combo = QComboBox()
        extra_combo.setPlaceholderText("Extra input ")
        # extra_combo.addItems(self.values)
        extra_combo.addItems(self.membranes)
        self.combo_boxes.append(extra_combo)
        grid_layout.addWidget(extra_combo, row, 2)
        extra_combo.currentIndexChanged.connect(
            lambda: self.add_component_row(row, grid_layout)
        )
        self.grid_widgets.append(extra_combo)

    def update_param(self):
        if getattr(self, "_updating", False):
            return
        self._updating = True
        self.store_value()
        if hasattr(self, "widgets"):
            for widget in self.grid_widgets:
                self.grid_layout.removeWidget(widget)
                widget.deleteLater()
            self.grid_widgets.clear()
        self.build_widget(self.row, self.label, self.grid_layout)
        self._updating = False

    def remove_widget_pair(
            self, widget1: QWidget, widget2: QWidget, widget3: QWidget, layout: QGridLayout, widget4: Optional[QWidget] = None, 
    ):
        layout.removeWidget(widget1)
        layout.removeWidget(widget2)
        layout.removeWidget(widget3)
        layout.removeWidget(widget4)
        widget1.deleteLater()
        widget2.deleteLater()
        widget3.deleteLater()
        if widget4 is not None:
            widget4.deleteLater()
        if widget1 in self.combo_boxes:
            self.combo_boxes.remove(widget1)
        if widget2 in self.combo_boxes2:
            self.combo_boxes2.remove(widget2)
        if widget4 in self.spin_boxes:
            self.spin_boxes.remove(widget4)

        self.extra_rows = max(0, self.extra_rows - 1)
        value = widget1.currentText()
        value2 = widget2.currentText()
        if value in self.last_combo_boxes:
            self.last_combo_boxes.remove(value)
        if value2 in self.last_combo_boxes2:
            self.last_combo_boxes2.remove(value2)
        self.category.update_category()

    def add_component_row(self, row: int, grid_layout: QGridLayout):
        self.component_base_row = row
        self.extra_rows += 1

        combo = QComboBox()
        combo.setPlaceholderText("BB input 1")
        # combo.addItems(self.values)
        combo.addItems(self.membranes)
        combo2 = QComboBox()
        combo2.setPlaceholderText("BB input 2")
        combo2.addItems(self.components)
        combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        combo2.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.combo_boxes.append(combo)
        self.combo_boxes2.append(combo2)

        remove_button = QPushButton("✕")
        remove_button.setFixedWidth(30)
        remove_button.clicked.connect(
            lambda _, c=combo, c2=combo2, b=remove_button: self.remove_widget_pair(
                c, c2, b, grid_layout
            )
        )

        grid_layout.addWidget(combo, row + 1, 2)
        grid_layout.addWidget(combo2, row + 1, 3)
        grid_layout.addWidget(remove_button, row + 1, 4)

        combo.currentIndexChanged.connect(
            lambda: self.add_component_row(row + 1, grid_layout)
        )
        combo2.currentIndexChanged.connect(
            lambda: self.add_component_row(row + 1, grid_layout)
        )

        self.category.update_category()

    def set_value_from_import(self, values: dict):
        value = values[self.name]
        value2 = values["param lb_permeability"]
        value3 = values["param ub_permeability"]
        self.extra_rows = len(value.keys())
        self.membranes = value.keys()
        self.combo_boxes = []
        self.combo_boxes2 = []
        self.spin_boxes = []
        self.components = set()
        for subdict in value2.values():
            self.components.update(subdict.keys())
        for subdict in value3.values():
            self.components.update(subdict.keys())
        debug_print(self.components)
        for membrane, comp_values in value.items():
            for component, value_ in comp_values.items():
                combo = QComboBox()
                combo.addItems(self.membranes)
                combo.setCurrentText(membrane)
                combo2 = QComboBox()
                combo2.addItems(self.components)
                combo2.setCurrentText(component)
                spin_box = self.create_spinbox(self.min_value, self.max_value, self.step, self.default)
                self.set_spin_value(spin_box, value_)
                self.combo_boxes.append(combo)
                self.combo_boxes2.append(combo2)
                self.spin_boxes.append(spin_box)
        debug_print(f"The param {self.name} was imported")

    # def set_values(self, values: list[str]):
    #     self.values = values

    # def set_components(self, components: list[str]):
    #     self.last_combo_boxes2.clear()
    #     self.components = components
    def set_components(self, components: list[str]):
        self.last_combo_boxes2.clear()
        self.components = components
        # Update all existing combo_boxes2 with new components
        for combo2 in self.combo_boxes2:
            current = combo2.currentText()
            combo2.clear()
            combo2.addItems(self.components)
            if current in self.components:
                combo2.setCurrentText(current)

    def set_membranes(self, membranes: list[str]):
        self.last_combo_boxes.clear()
        self.membranes = membranes

    def store_value(self):
        self.last_combo_boxes.clear()
        self.last_combo_boxes2.clear()
        self.last_spin_boxes.clear()
        for combo in self.combo_boxes:
            if combo.currentText() != "":
                self.last_combo_boxes.append(combo.currentText())
        for combo2 in self.combo_boxes2:
            if combo2.currentText() != "":
                self.last_combo_boxes2.append(combo2.currentText())
        for spin_box in self.spin_boxes:
            self.last_spin_boxes.append(spin_box.value())
        if self.checkbox:
            self.last_check_box = self.checkbox.isChecked()

    def _set_grid_visible(self, visible: bool):
        for widget in getattr(self, "grid_widgets", []):
            widget.setVisible(visible)

    def _on_checkbox_changed(self, state):
        self._set_grid_visible(bool(state))
        if not state:
            self.last_combo_boxes.clear()
            self.last_combo_boxes2.clear()
        else:
            self.store_value()

    def row_span(self) -> int:
        return 3 + self.extra_rows
    
    def hide(self):
        self.hidden = True

    def show(self):
        self.hidden = False

    def to_data_entry(self) -> Optional[str]:
        if self.checkbox and self.checkbox.isChecked():
            return super().to_data_entry()
        return None

    def to_mask_entry(self) -> str:
        lines = []
        for i, value in enumerate(self.last_spin_boxes):
            lines.append(f"{self.name}:#{self.last_combo_boxes[i]},#{self.last_combo_boxes2[i]} {value}")
        return "\n".join(lines)

    def to_perm_entry(self) -> Optional[str]:
        if self.hidden:
            return None
        lines = [f"{self.name} :="]
        for i in range(len(self.last_spin_boxes)):
            membrane = self.last_combo_boxes[i] if i < len(self.last_combo_boxes) else None
            component = self.last_combo_boxes2[i] if i < len(self.last_combo_boxes2) else None
            value = self.last_spin_boxes[i]
            lines.append(f"{membrane} {component} {value}")
        return "\n".join(lines)

    
    
    
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

        self.help_btn = QToolButton()
        self.help_btn.setText("?")
        self.help_btn.setFixedSize(14, 14)
        self.help_btn.clicked.connect(self.show_help_tooltip)

        self.help_btn.setStyleSheet("""
            QToolButton {
                border: 1px solid #888;
                border-radius: 7px;
                background: #f5f5f5;
                font-weight: bold;
                font-size: 14px;
                color: #3366cc;
            }
            QToolButton:hover {
                background: #e0eaff;
                border: 1.5px solid #0057b8;
            }
        """)

        layout.addWidget(self.help_btn)
        # Install event filter for hover tooltips
        self.help_btn.installEventFilter(self)

    def show_help_tooltip(self):
        wrapped_description = f'<div style="max-width: 300px; white-space: pre-wrap;">{self.description}</div>'
        QToolTip.showText(
            self.help_btn.mapToGlobal(QPoint(0, self.help_btn.height())),
            wrapped_description,
            self.help_btn,
        )

    def eventFilter(self, obj, event):
        if obj == self.help_btn:
            if event.type() == QEvent.Type.Enter:  # Mouse entered
                self.show_help_tooltip()
            elif event.type() == QEvent.Type.Leave:  # Mouse left
                QToolTip.hideText()
        return super().eventFilter(obj, event)
