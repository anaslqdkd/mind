class LineEditValidation:
    def __init__(self) -> None:
        self.validation_rules = {}
        pass

    def set_validation(self, min_value=None, max_value=None, optional=False):
        self.validation_rules["min"] = min_value
        self.validation_rules["max"] = max_value
        self.validation_rules["optional"] = optional

    def validate_input(self, text: str) -> bool:
        if text == "":
            return self.validation_rules.get("optional", False)

        try:
            value = float(text)
            min_val = self.validation_rules.get("min", float("-inf"))
            max_val = self.validation_rules.get("max", float("inf"))
            if value is not None:
                # FIXME: adapt if min_value or max_value is missing
                return min_val <= value <= max_val
        except ValueError:
            return False
