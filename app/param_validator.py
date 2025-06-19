from typing import Optional
from PyQt6.QtWidgets import QLineEdit


class LineEditValidation:
    def __init__(self) -> None:
        self.validation_rules = {}
        pass

    # TODO: add type verification

    # FIXME: change text to line_edit instance
    def set_validation(self, min_value=None, max_value=None):
        self.validation_rules["min"] = min_value
        self.validation_rules["max"] = max_value

    def validate_input(self, text: str) -> bool:
        # TODO: allow str and int etc
        try:
            value = float(text)
            print("the value is", value)
            min_val = self.validation_rules.get("min", float("-inf"))
            max_val = self.validation_rules.get("max", float("inf"))
            if value is not None:
                # FIXME: adapt if min_value or max_value is missing
                return min_val <= value <= max_val
            else:
                return True
        except ValueError:
            return False


class NonOptionalInputValidation:
    def __init__(self, line_edit: Optional[QLineEdit]) -> None:
        self.line_edit = line_edit

    def is_filled(self):
        if self.line_edit is not None:
            return bool(self.line_edit.text().strip())
        else:
            return


# TODO: file import
