import enum
import re
from typing import Optional, Union
from PyQt6.QtCore import QEvent, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenuBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QStackedWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

# TODO: same but for actual input types


class ParamType(enum.Enum):
    INPUT = enum.auto()  # seulement de l'input
    INPUT_WITH_UNITY = enum.auto()  # parametre avec unité dans un menu deroulant
    BOOLEAN = enum.auto()  # checkbox
    SELECT = enum.auto()  # menu deroulable
    BOOLEAN_WITH_INPUT = enum.auto()  # maxiteration
    BOOLEAN_WITH_INPUT_WITH_UNITY = enum.auto()  # pour maxtime
    COMPONENT = enum.auto()  # set components
    COMPONENT_WITH_VALUE = enum.auto()  # components xin
    COMPONENT_WITH_VALUE_WITH_UNITY = enum.auto()  # components xin
    # TODO: add a param type for components attributes

# -----------------------------------------------------------

class FILE(enum.Enum):
    CONFIG = enum.auto()
    DATA = enum.auto()
    PERM = enum.auto()
    ECO = enum.auto()
    COMMAND = enum.auto()

# -----------------------------------------------------------

class Param:
    def __init__(
        self,
        name: str,
        # type: Union[ParamInput, ParamSelect],
        # type: ParamType,
        # file: FILE,
        # values: Optional[list[str]] = None,
    ) -> None:
        self.name = name  # the exact name in the data files
        # self.type = type  # the type as an Enum in ParamType
        # self.values = values or []  # values taken if it is a select param
        # self.file = file
        self.category: ParamCategory 

        self.widgets: dict[str, dict["str", Union[QLineEdit, QComboBox, QCheckBox]]] = (
            {}
        )
        # TODO: add widget dictionnary builder according to param type
        # TODO: add optional attribute

    def build_widget(self, row: int, label: str, grid_layout: QGridLayout):
        raise NotImplementedError("Subclasses must implement build_widgets")
    def store_value(self):
        raise NotImplementedError("Subclasses must implement store_values")
    def row_span(self) -> int:
        return 1



# -----------------------------------------------------------

class ParamInput(Param):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.question_label = None
        self.line_edit = None
        self.last_line_edit = ""
        pass

    def build_widget(self, row: int, label: str, grid_layout: QGridLayout):
        # TODO: restore the value if it is rebuild after
        question_label = QLabel(label)
        line_edit = QLineEdit()
        self.question_label = question_label
        self.line_edit = line_edit
        line_edit.setText(self.last_line_edit)
        grid_layout.addWidget(question_label, row, 0)
        grid_layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding,
                        QSizePolicy.Policy.Minimum),
            row,
            1,
        )
        grid_layout.addWidget(line_edit, row, 2)
        self.question_label = question_label
        self.line_edit = line_edit
        pass

    def store_value(self):
        if self.line_edit is not None:
            self.last_line_edit = self.line_edit.text()
        pass

# -----------------------------------------------------------

class ParamSelect(Param):
    # TODO: add values somewhere
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.question_label = None
        self.combo_box = None
        self.last_combo_box = ""
        pass

    def build_widget(self, row: int, label: str, grid_layout: QGridLayout):
        # TODO: restore the value if it is rebuild after
        question_label = QLabel(label)
        combo_box = QComboBox()
        combo_box.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        combo_box.addItems(["item 1", "item 2", "item 3"])

        # FIXME: encapsulate all this in a method "restore"
        if self.last_combo_box:
            index = combo_box.findText(self.last_combo_box)
            if index != -1:
                combo_box.setCurrentIndex(index)

        self.question_label = question_label
        self.combo_box = combo_box

        grid_layout.addWidget(question_label, row, 0)

        # Spacer to push the combo box to the right
        spacer = QSpacerItem(
            0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        grid_layout.addItem(spacer, row, 1)

        grid_layout.addWidget(combo_box, row, 2, 1, 2)
        self.combo_box = combo_box
        self.question_label = question_label

        pass
    def store_value(self):
        # TODO:
        if self.combo_box is not None:
            self.last_combo_box = self.combo_box.currentText()
        pass


# -----------------------------------------------------------

class ParamBoolean(Param):
    # TODO: add values somewhere
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.question_label = None
        self.check_box = None
        self.last_check_box = False

    def build_widget(self, row: int, label: str, grid_layout: QGridLayout):
        container = QWidget()
        h_layout = QHBoxLayout(container)
        h_layout.setContentsMargins(0, 0, 0, 0)

        check_box = QCheckBox()
        question_label = QLabel(label)

        self.check_box = check_box

        if self.last_check_box:
            check_box.setChecked(True)

        h_layout.addWidget(check_box)
        h_layout.addWidget(question_label)
        h_layout.addStretch()

        # span 2 columns if needed
        grid_layout.addWidget(container, row, 0, 1, 2)

        pass
    def store_value(self):
        if self.check_box is not None:
            self.last_check_box = self.check_box.isChecked()

# -----------------------------------------------------------
class ParamInputWithUnity(Param):
    # TODO: add values somewhere
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.question_label = None
        self.line_edit = None
        self.combo_box = None

        self.last_line_edit = ""
        self.last_combo_box = ""
        pass

    def build_widget(self, row: int, label: str, grid_layout: QGridLayout):
        # TODO: restore the value if it is rebuild after
        question_label = QLabel(label)
        line_edit = QLineEdit()
        combo_box = QComboBox()
        combo_box.addItems(["unity 1", "unity 2", "unity 3"])
        grid_layout.addWidget(question_label, row, 0)
        grid_layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding,
                        QSizePolicy.Policy.Minimum),
            row,
            1,
        )
        self.line_edit = line_edit
        self.combo_box = combo_box

        if self.last_combo_box:
            index = combo_box.findText(self.last_combo_box)
            if index != -1:
                combo_box.setCurrentIndex(index)
        if self.last_line_edit:
            line_edit.setText(self.last_line_edit)

        grid_layout.addWidget(line_edit, row, 2)
        grid_layout.addWidget(combo_box, row, 3)
        # param_obj.widgets[param_obj.name] = {"line_edit": line_edit}
        # param_obj.widgets[param_obj.name] = {"combo_box": combo_box}

        pass
    def store_value(self):
        if self.line_edit is not None:
            self.last_line_edit = self.line_edit.text()
            pass
        if self.combo_box is not None:
            self.last_combo_box = self.combo_box.currentText()
        pass

# -----------------------------------------------------------
class ParamBooleanWithInput(Param):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.question_label = None
        self.line_edit = None
        self.check_box = None

        self.last_check_box = False
        self.last_line_edit = ""
        pass

    def build_widget(self, row: int, label: str, grid_layout: QGridLayout):
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

        if self.last_check_box:
            check_box.setChecked(True)
            line_edit.setEnabled(True)
        if self.last_line_edit:
            line_edit.setText(self.last_line_edit)

        grid_layout.addWidget(checkbox_container, row, 0, 1, 2)

        t_label = QLabel(label)
        # line_edit.setEnabled(False)


        check_box.toggled.connect(line_edit.setEnabled)

        grid_layout.addWidget(t_label, row + 1, 0)
        grid_layout.addWidget(line_edit, row + 1, 2)

    def store_value(self):
        if self.line_edit is not None:
            self.last_line_edit = self.line_edit.text()
        if self.check_box is not None:
            self.last_check_box = self.check_box.isChecked()

    def row_span(self) -> int:
        return 2


# -----------------------------------------------------------

class ParamBooleanWithInputWithUnity(Param):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.question_label = None
        self.check_box = None
        self.combo_box = None
        self.line_edit = None

        self.last_check_box = False
        self.last_combo_box = ""
        self.last_line_edit = ""

    def build_widget(self, row: int, label: str, grid_layout: QGridLayout):
        checkbox_container = QWidget()
        checkbox_layout = QHBoxLayout(checkbox_container)
        checkbox_layout.setContentsMargins(0, 0, 0, 0)
        checkbox_layout.setSpacing(5)

        check_box = QCheckBox()
        question_label = QLabel(label)

        combo_box = QComboBox()
        combo_box.addItems(["Item 1", "Item 2", "Item 3"])

        line_edit = QLineEdit()
        line_edit.setEnabled(False)
        check_box.toggled.connect(line_edit.setEnabled)

        self.check_box = check_box
        self.combo_box = combo_box
        self.line_edit = line_edit


        if self.last_check_box:
            check_box.setChecked(True)
        if self.line_edit:
            line_edit.setText(self.last_line_edit)
        if self.last_combo_box:
            index = combo_box.findText(self.last_combo_box)
            if index != -1:
                combo_box.setCurrentIndex(index)

        checkbox_layout.addWidget(check_box)
        checkbox_layout.addWidget(question_label)
        checkbox_layout.addStretch()

        grid_layout.addWidget(checkbox_container, row, 0, 1, 2)

        # Second row: Label + input field
        t_label = QLabel(label)

        grid_layout.addWidget(t_label, row + 1, 0)
        spacer = QWidget()
        grid_layout.addWidget(spacer, row + 1, 1)
        grid_layout.addWidget(line_edit, row + 1, 2)
        grid_layout.addWidget(combo_box, row + 1, 3)

    def store_value(self):
        if self.combo_box is not None:
            self.last_combo_box = self.combo_box.currentText()
        if self.check_box is not None:
            self.last_check_box = self.check_box.isChecked()
        if self.line_edit is not None:
            self.last_line_edit = self.line_edit.text()


    def row_span(self) -> int:
        return 2

# -----------------------------------------------------------

class ParamComponent(Param):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.question_label = None
        self.combo_box = None
        self.extra_rows = 0
        self.combo_boxes = []

        self.last_combo_boxes = []

    def build_widget(self, row: int, label: str, grid_layout: QGridLayout):
        question_label = QLabel(label)
        grid_layout.addWidget(question_label, row, 0)
        self.combo_boxes = []

        # update method
        if self.extra_rows > 0:
            for i in range(self.extra_rows):
                combo = QComboBox()
                combo.setPlaceholderText("Extra input")
                combo.addItems(["Item 1", "Item 2", "Item 3"])
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
        extra_combo.addItems(["Item 1", "Item 2", "Item 3"])
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


        # pass



    def row_span(self) -> int:
        return 1 + self.extra_rows

# -----------------------------------------------------------

def create_param(name: str, param_type: ParamType) -> Param:
    match param_type:
        case ParamType.INPUT:
            return ParamInput(name)
        case ParamType.SELECT:
            return ParamSelect(name)
        case ParamType.BOOLEAN:
            return ParamBoolean(name)
        case ParamType.INPUT_WITH_UNITY:
            return ParamInputWithUnity(name)
        case ParamType.BOOLEAN_WITH_INPUT:
            return ParamBooleanWithInput(name)
        case ParamType.BOOLEAN_WITH_INPUT_WITH_UNITY:
            return ParamBooleanWithInputWithUnity(name)
        case ParamType.COMPONENT:
            return ParamComponent(name)
        case _:
            raise ValueError(f"Unsupported param type: {param_type}")

# -----------------------------------------------------------


# TODO: advanced button to unlock more "unusual" settings
# TODO: see for alpha parameter, lower bounds etc, to set them maybe with a cursor instead of having 3 possible fields?
# TODO: store the input


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
        self.build_param()

    def build_param(self) -> QWidget:
        self.row = 0
        for label, param_obj in self.param.items():
            # print("+++++ the type is", param_obj.type)
            # if isinstance(param_obj.type, ParamInput):
            #     print("55555")
            #     print(param_obj.name)
            #     self.add_param_input(self.row, label, param_obj)
            #     self.row += 1
            # if isinstance(param_obj.type, ParamSelect):
            #     print("in the param select in the build param")
            #     self.add_param_select(self.row, label, param_obj)
            #     self.row += 1
            param_obj.build_widget(self.row, label, self.grid_layout)
            self.row += param_obj.row_span()
        self.build_param_values()
        # TODO: add method to rebuild the inserted values

        return self

    # TODO: a update method, clear_grid -> rebuild with the values

    def build_components(self, row: int, label: "str"):
        print("the label is", label)
        question_label = QLabel(label)
        self.grid_layout.addWidget(question_label, row, 0)
        for i in range(len(self.components_index)):
            combo = QComboBox()
            combo.setPlaceholderText("Extra input")
            combo.addItems(["Item 1", "Item 2", "Item 3"])
            combo.setCurrentIndex(self.components_index[i])
            print("self.components_index", self.components_index)
            combo.setSizePolicy(QSizePolicy.Policy.Expanding,
                                QSizePolicy.Policy.Fixed)
            remove_button = QPushButton("✕")
            remove_button.setFixedWidth(30)
            remove_button.clicked.connect(lambda: self.remove_component(i))
            self.grid_layout.addWidget(combo, row, 2)
            self.grid_layout.addWidget(remove_button, row, 3)
            row += 1
        self.extra_combo = QComboBox()
        self.extra_combo.setPlaceholderText("Extra input")
        self.extra_combo.addItems(["Item 1", "Item 2", "Item 3"])
        self.grid_layout.addWidget(self.extra_combo, row, 2)
        remove_button = QPushButton("✕")
        remove_button.setFixedWidth(30)
        self.extra_combo.currentIndexChanged.connect(
            lambda idx, combo=self.extra_combo: self.store_value(combo)
        )
        self.extra_combo.currentIndexChanged.connect(self.add_component_row)
        self.grid_layout.addWidget(remove_button, row, 3)
        pass

    def remove_component(self, index: int):
        # print(self.components_index)
        self.components_index.pop(index)
        self.clear_grid_layout()
        self.build_param()

    # TODO: refactor this into classes, class param_input etc instead of an enum, to have a unique reference to all atributes
    def add_param_input(self, row: int, label: str, param_obj: Param):
        # TODO: do the same for other components
        question_label = QLabel(label)
        line_edit = QLineEdit()
        if param_obj.type.last_line_edit != "":
            line_edit.setText(param_obj.type.last_line_edit)
        self.grid_layout.addWidget(question_label, row, 0)
        self.grid_layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding,
                        QSizePolicy.Policy.Minimum),
            row,
            1,
        )
        self.grid_layout.addWidget(line_edit, row, 2)
        param_obj.widgets[param_obj.name] = {"line_edit": line_edit}
        param_obj.type.question_label = question_label
        param_obj.type.line_edit = line_edit
        # print("dic param_obj widgets", param_obj.widgets)

    def add_param_input_with_unity(self, row: int, label: str, param_obj: Param):
        question_label = QLabel(label)
        line_edit = QLineEdit()
        combo_box = QComboBox()
        combo_box.addItems(param_obj.values)
        # self.grid_layout.addWidget(question_label, row, 0)
        # self.grid_layout.addWidget(line_edit, row, 1)
        # self.grid_layout.addWidget(combo_box, row, 2)
        self.grid_layout.addWidget(question_label, row, 0)
        self.grid_layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Expanding,
                        QSizePolicy.Policy.Minimum),
            row,
            1,
        )
        self.grid_layout.addWidget(line_edit, row, 2)
        self.grid_layout.addWidget(combo_box, row, 3)
        param_obj.widgets[param_obj.name] = {"line_edit": line_edit}
        param_obj.widgets[param_obj.name] = {"combo_box": combo_box}

    def add_param_boolean(self, row: int, label: str, param_obj: Param):
        container = QWidget()
        h_layout = QHBoxLayout(container)
        # remove margins for tighter layout
        h_layout.setContentsMargins(0, 0, 0, 0)
        # h_layout.setSpacing(5)  # optional: tweak spacing between checkbox and label

        check_box = QCheckBox()
        question_label = QLabel(label)

        h_layout.addWidget(check_box)
        h_layout.addWidget(question_label)
        h_layout.addStretch()

        # span 2 columns if needed
        self.grid_layout.addWidget(container, row, 0, 1, 2)

    def add_param_boolean_with_input(self, row: int, label: str, param_obj: Param):
        checkbox_container = QWidget()
        checkbox_layout = QHBoxLayout(checkbox_container)
        checkbox_layout.setContentsMargins(0, 0, 0, 0)
        checkbox_layout.setSpacing(5)

        check_box = QCheckBox()
        question_label = QLabel(label)

        checkbox_layout.addWidget(check_box)
        checkbox_layout.addWidget(question_label)
        checkbox_layout.addStretch()

        self.grid_layout.addWidget(checkbox_container, row, 0, 1, 2)

        # Second row: Label + input field
        t_label = QLabel(label)
        line_edit = QLineEdit()
        line_edit.setEnabled(False)
        check_box.toggled.connect(line_edit.setEnabled)

        self.grid_layout.addWidget(t_label, row + 1, 0)
        spacer = QWidget()
        self.grid_layout.addWidget(spacer, row + 1, 1)
        self.grid_layout.addWidget(line_edit, row + 1, 2)
        param_obj.widgets[param_obj.name] = {"line_edit": line_edit}
        param_obj.widgets[param_obj.name] = {"checkbox": check_box}

    def add_param_boolean_with_input_with_unity(
        self, row: int, label: str, param_obj: Param
    ):
        checkbox_container = QWidget()
        checkbox_layout = QHBoxLayout(checkbox_container)
        checkbox_layout.setContentsMargins(0, 0, 0, 0)
        checkbox_layout.setSpacing(5)

        check_box = QCheckBox()
        question_label = QLabel(label)

        combo_box = QComboBox()
        combo_box.addItems(param_obj.values)

        checkbox_layout.addWidget(check_box)
        checkbox_layout.addWidget(question_label)
        checkbox_layout.addStretch()

        self.grid_layout.addWidget(checkbox_container, row, 0, 1, 2)

        # Second row: Label + input field
        t_label = QLabel(label)
        line_edit = QLineEdit()
        line_edit.setEnabled(False)
        check_box.toggled.connect(line_edit.setEnabled)

        self.grid_layout.addWidget(t_label, row + 1, 0)
        spacer = QWidget()
        self.grid_layout.addWidget(spacer, row + 1, 1)
        self.grid_layout.addWidget(line_edit, row + 1, 2)
        self.grid_layout.addWidget(combo_box, row + 1, 3)
        param_obj.widgets[param_obj.name] = {"line_edit": line_edit}
        param_obj.widgets[param_obj.name] = {"checkbox": check_box}
        param_obj.widgets[param_obj.name] = {"combo_box": combo_box}

    def add_param_select(self, row: int, label: str, param_obj: Param):
        question_label = QLabel(label)
        combo_box = QComboBox()
        combo_box.addItems(param_obj.values)
        combo_box.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # FIXME: check isinstance of to avoir lsp errors
        if isinstance(param_obj.type, ParamSelect):
            if param_obj.type.last_combo_box != "":
                print("°°°°°", param_obj.type.last_combo_box)
                combo_box.setCurrentText(param_obj.type.last_combo_box)

        self.grid_layout.addWidget(question_label, row, 0)

        # Spacer to push the combo box to the right
        spacer = QSpacerItem(
            0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        self.grid_layout.addItem(spacer, row, 1)

        # self.grid_layout.addWidget(combo_box, row, 2)
        self.grid_layout.addWidget(combo_box, row, 2, 1, 2)
        param_obj.type.combo_box = combo_box

        param_obj.widgets[param_obj.name] = {"combo_box": combo_box}

    def add_param_component(self, row: int, label: str, param_obj: Param):
        self.row = row

        self.label = QLabel(label)
        self.line_edit = QComboBox()
        self.line_edit.setPlaceholderText("Select a component")
        self.line_edit.addItems(["item 1", "item 2", "item 3"])

        self.line_edit.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )

        # Add widgets to layout
        self.grid_layout.addWidget(self.label, row, 0)
        self.grid_layout.addWidget(self.line_edit, row, 2)

        self.line_edit.currentIndexChanged.connect(
            lambda idx, combo=self.line_edit: self.store_value(combo)
        )
        self.line_edit.currentIndexChanged.connect(self.add_component_row)
        self.component_base_row = row

    def store_value(self, combo: QComboBox):
        selected_index = combo.currentIndex()
        self.components_index.append(selected_index)
        print("Selected:", selected_index)
        self.selected_value = selected_index
        # TODO: store it in the param dictionnary

    def add_component(self):
        self.extra_box = QComboBox()
        self.extra_box.setPlaceholderText("Extra input")
        self.extra_box.addItems(["Item 1", "Item 2", "Item3"])
        remove_button = QPushButton("✕")
        remove_button.setFixedWidth(30)
        # self.row += 1
        self.grid_layout.addWidget(self.extra_box, self.row, 1)
        self.grid_layout.addWidget(remove_button, self.row, 2)
        self.extra_box.currentIndexChanged.connect(self.add_component)
        # self = ParamCategory(self.name, self.param)
        # self.build_param()

    def add_component_row(self):
        self.component_base_row = self.row
        self.extra_rows += 1
        row = self.component_base_row + self.extra_rows

        combo = QComboBox()
        combo.setPlaceholderText("Extra input")
        combo.addItems(["Item 1", "Item 2", "Item 3"])
        combo.setSizePolicy(QSizePolicy.Policy.Expanding,
                            QSizePolicy.Policy.Fixed)

        remove_button = QPushButton("✕")
        remove_button.setFixedWidth(30)

        self.grid_layout.addWidget(combo, row, 1)
        self.grid_layout.addWidget(remove_button, row, 2)

        combo.currentIndexChanged.connect(self.add_component_row)
        self.component_widgets.append((combo, remove_button))
        self.update_category()
    def store_values(self):
        for name, param in self.param.items():
            param.store_value()

    def update_category(self):
        self.store_values()
        self.clear_grid_layout()
        self.build_param()

    def clear_grid_layout(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()
            elif item.layout():
                self.clear_grid_layout(item.layout())
                item.layout().deleteLater()

    # TODO: restore all input if the grid is regenerated
    def build_param_values(self):
        values = {}
        for label, param_obj in self.param.items():
            # dict = param_obj.widgets
            for key, dict in param_obj.widgets.items():
                for el, widget in dict.items():
                    # if el == "line_edit":
                    if isinstance(widget, QLineEdit):
                        print(el)
                        print(widget)
                        print("HERE")
                        print(widget.text())
                        values[label] = widget.text()
                    # elif el == "combo_box":
                    elif isinstance(widget, QComboBox):
                        values[label] = widget.currentText()
                        # elif el == "check_box":
                    elif isinstance(widget, QCheckBox):
                        values[label] = widget.isChecked()

        pass


class MenuBar(QMenuBar):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.file_menu = self.addMenu("File")
        self.help_menu = self.addMenu("Help")
        self.help_menu = self.addMenu("Versions")
        self.quit_menu = self.addMenu("Exit")

        if self.quit_menu != None:
            self.quit_action = self.quit_menu.addAction("Exit")


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

        # pages
        param_page1 = self.set_param()
        self.page_components = PageParametersGlobal(self, param_page1)
        self.page1 = PageParametersGlobal(self, param_page1)

        self.main_area = QWidget()
        tab1_layout = QHBoxLayout(self.main_area)
        header = QLabel("Main Area Header")

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
            "Algorithm": 
                create_param(name="algorithm", param_type=ParamType.INPUT)
            ,
            "Another one": 
                create_param(name="idk", param_type=ParamType.INPUT)
            ,
            "Select test": 
                create_param(name="select", param_type=ParamType.SELECT)
            ,
            "Bool test": 
                create_param(name="check", param_type=ParamType.BOOLEAN)
            ,
            "Input with unity test": 
                create_param(name="input with unity", param_type=ParamType.INPUT_WITH_UNITY)
            ,
            "Boolean with input test": 
                create_param(name="boolean with input", param_type=ParamType.BOOLEAN_WITH_INPUT)
            ,
            "Boolean with input and unity": 
                create_param(name="boolean with input and unity", param_type=ParamType.BOOLEAN_WITH_INPUT_WITH_UNITY)
            ,
            "Component": 
                create_param(name="component test", param_type=ParamType.COMPONENT)
            ,
            "Another flds": 
                create_param(name="bu", param_type=ParamType.INPUT)
            ,
            # "Set max time": Param(
            #     name="max_time",
            #     type=ParamType.BOOLEAN_WITH_INPUT_WITH_UNITY,
            #     values=["s", "h", "ms", "m"],
            # ),
            # "Set max iterations": Param(
            #     name="max_iterations",
            #     type=ParamType.BOOLEAN_WITH_INPUT,
            # ),
            # "Alpha": Param(
            #     name="BY", type=ParamType.COMPONENT, values=["bar", "kPa", "Pa"]
            # ),
            # "Enable verbose": Param(name="verbose", type=ParamType.BOOLEAN),
            # "Enable debug mode": Param(name="debug", type=ParamType.BOOLEAN),
            # "No starting point": Param(
            #     name="no_starting_point", type=ParamType.BOOLEAN
            # ),
            # "No simplified model": Param(
            #     name="no_simplified_model", type=ParamType.BOOLEAN
            # ),
        }
        param = {
            # "Alpha": Param(
            #     name="Alpha", type=ParamType.BOOLEAN_WITH_INPUT, values=["bar", "kPa", "Pa"]
            # ),
            # "Pressure ratio": Param(
            #     name="pressure_ratio",
            #     type=ParamType.INPUT,
            #     # values=["s", "h", "ms", "days"],
            # ),
            # "Alpha": Param(
            #     name="BY", type=ParamType.COMPONENT, values=["bar", "kPa", "Pa"]
            # ),
        }
        param_page1 = {"Algorithm parameters": algo_params,
                       "Other parameters": param}
        return param_page1


# params = {
#     "Generate starting point": Param(name="starting_point", type=ParamType.BOOLEAN),
#     "Pressure": Param(
#         name="pressure_in", type=ParamType.INPUT_WITH_UNITY, values=["bar", "kPa", "Pa"]
#     ),
#     "Use simplified model": Param(name="simplified_model", type=ParamType.BOOLEAN),
#     "Algorithm": Param(
#         name="Algorithm",
#         type=ParamType.SELECT,
#         values=["multistart", "mbh", "global", "genetic", "population"],
#     ),
#     "Set max time": Param(
#         name="max_time",
#         type=ParamType.BOOLEAN_WITH_INPUT_WITH_UNITY,
#         values=["s", "h", "ms", "days"],
#     ),
#     "Set max iterations": Param(
#         name="max_iterations", type=ParamType.BOOLEAN_WITH_INPUT
#     ),
#     "Pressure ratio": Param(
#         name="pressure_ratio",
#         type=ParamType.INPUT,
#         # values=["s", "h", "ms", "days"],
#     ),
#     "Pressure ratio": Param(
#         name="pressure_ratio",
#         type=ParamType.INPUT,
#         # values=["s", "h", "ms", "days"],
#     ),
#     "Alpha": Param(name="BY", type=ParamType.COMPONENT, values=["bar", "kPa", "Pa"]),
# }
#
# param = {
#     # "Alpha": Param(
#     #     name="Alpha", type=ParamType.BOOLEAN_WITH_INPUT, values=["bar", "kPa", "Pa"]
#     # ),
#     "Pressure ratio": Param(
#         name="pressure_ratio",
#         type=ParamType.INPUT,
#         # values=["s", "h", "ms", "days"],
#     ),
#     "Alpha": Param(name="BY", type=ParamType.COMPONENT, values=["bar", "kPa", "Pa"]),
# }
#
# param_page2 = {"Algorithm parameters": params}
#
#
# algo_params = {
#     "Algorithm": Param(
#         name="algorithm",
#         type=ParamInput(name="algorithm", label="algorithm"),
#         values=["multistart", "mbh", "global", "population", "genetic"],
#     ),
#     "Set max time": Param(
#         name="max_time",
#         type=ParamType.BOOLEAN_WITH_INPUT_WITH_UNITY,
#         values=["s", "h", "ms", "m"],
#     ),
#     "Set max iterations": Param(
#         name="max_iterations",
#         type=ParamType.BOOLEAN_WITH_INPUT,
#     ),
#     "Enable verbose": Param(name="verbose", type=ParamType.BOOLEAN),
#     "Enable debug mode": Param(name="debug", type=ParamType.BOOLEAN),
#     "No starting point": Param(name="no_starting_point", type=ParamType.BOOLEAN),
#     "No simplified model": Param(name="no_simplified_model", type=ParamType.BOOLEAN),
# }
#
# params = {
#     "Generate starting point": Param(name="starting_point", type=ParamType.BOOLEAN),
#     "Pressure": Param(
#         name="pressure_in", type=ParamType.INPUT_WITH_UNITY, values=["bar", "kPa", "Pa"]
#     ),
#     "Use simplified model": Param(name="simplified_model", type=ParamType.BOOLEAN),
#     "Algorithm": Param(
#         name="Algorithm",
#         type=ParamType.SELECT,
#         values=["multistart", "mbh", "global", "genetic", "population"],
#     ),
#     "Set max time": Param(
#         name="max_time",
#         type=ParamType.BOOLEAN_WITH_INPUT_WITH_UNITY,
#         values=["s", "h", "ms", "days"],
#     ),
#     "Set max iterations": Param(
#         name="max_iterations", type=ParamType.BOOLEAN_WITH_INPUT
#     ),
#     "Pressure ratio": Param(
#         name="pressure_ratio",
#         type=ParamType.INPUT,
#         # values=["s", "h", "ms", "days"],
#     ),
#     "Pressure ratio": Param(
#         name="pressure_ratio",
#         type=ParamType.INPUT,
#         # values=["s", "h", "ms", "days"],
#     ),
#     "Alpha": Param(name="BY", type=ParamType.COMPONENT, values=["bar", "kPa", "Pa"]),
# }
#
# param = {
#     # "Alpha": Param(
#     #     name="Alpha", type=ParamType.BOOLEAN_WITH_INPUT, values=["bar", "kPa", "Pa"]
#     # ),
#     "Pressure ratio": Param(
#         name="pressure_ratio",
#         type=ParamType.INPUT,
#         # values=["s", "h", "ms", "days"],
#     ),
#     "Alpha": Param(name="BY", type=ParamType.COMPONENT, values=["bar", "kPa", "Pa"]),
# }
#
# param_page1 = {"Algorithm parameters": algo_params, "Other parameters": param}
# param_page2 = {"Algorithm parameters": params}


class Parameter:
    def __init__(self, name: str, measure: list[str]) -> None:
        self.name = name
        self.measure = measure


class PageParametersGlobal(QWidget):
    def __init__(
        self, main_window, param_category: dict["str", dict[str, Param]]
    ) -> None:
        super().__init__()
        self.main_window = main_window
        self.param_category = param_category
        # self.param_category = param_category

        main_layout = QVBoxLayout()

        content_layout = QVBoxLayout()
        content_widget = QWidget()
        content_widget.setLayout(content_layout)

        for key, value in param_category.items():
            ex_params = ParamCategory(key, value)
            for name, param in value.items():
                param.category = ex_params
            main_layout.addWidget(ex_params)

        # ex_params = ParamCategory("Algorithm parameters", param)
        # main_layout.addWidget(ex_params)
        main_layout.addStretch()

        self.setLayout(main_layout)


class PageParametersComponent(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        # self.components_layout = QVBoxLayout()
        self.components_widget = QWidget()
        # self.components_widget.setFixedSize(400, 300)  # width, height in pixels
        self.components_layout = QVBoxLayout(self.components_widget)
        self.add_component_button = QPushButton("Add Component")
        # self.add_component_button.setFixedSize(100, 30)
        line_edit = QLineEdit()
        row_layout = QHBoxLayout()
        row_layout.addWidget(line_edit)
        row_widget = QWidget()
        row_widget.setLayout(row_layout)
        # row_widget.setFixedSize(70, 40)
        # self.components_widget.setFixedSize(100, 100)
        self.components_layout.addWidget(row_widget)
        self.components_layout.setSpacing(1)  # Reduce space between items
        self.components_layout.setContentsMargins(
            0, 0, 0, 0)  # Remove outer margins
        self.components_layout.setAlignment(
            # keeps items on top
            Qt.AlignmentFlag.AlignTop
        )
        layout = QVBoxLayout()
        # layout.addWidget(QLabel("lfksd"))
        # layout.addLayout(self.components_layout)
        layout.addWidget(self.components_widget)
        # self.components_layout(self.add_component_button)
        self.components_layout.addWidget(self.add_component_button)
        self.components_widget.adjustSize()
        self.setLayout(layout)

    def add_component(self):
        line_edit = QLineEdit()
        # combo_box = QComboBox()
        # combo_box.addItems(["unit1", "unit2"])  # or dynamic units
        row_layout = QHBoxLayout()
        row_layout.addWidget(line_edit)
        # row_layout.addWidget(combo_box)
        row_widget = QWidget()
        row_widget.setLayout(row_layout)
        # row_widget.setFixedSize(70, 40)
        self.components_layout.addWidget(row_widget)
        # row_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        row_widget.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        # self.components.append((line_edit, combo_box))
