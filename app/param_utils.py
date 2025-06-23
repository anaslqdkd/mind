from PyQt6.QtCore import QPoint
from PyQt6.QtWidgets import QHBoxLayout, QToolButton, QToolTip
from app.param import (
    Param,
    ParamBoolean,
    ParamBooleanWithInput,
    ParamBooleanWithInputWithUnity,
    ParamComponent,
    ParamComponentSelector,
    ParamFileChooser,
    ParamFixedWithInput,
    ParamInput,
    ParamInputWithUnity,
    ParamRadio,
    ParamSelect,
    ParamSpinBoxWithBool,
)
from app.param_enums import FILE, ParamType
import inspect


# -----------------------------------------------------------
def create_param(name: str, param_type: ParamType, file: FILE, **kwargs) -> Param:
    optional = kwargs.get("optional", False)
    values = kwargs.get("values", [])
    depends_on = kwargs.get("depends_on", {})
    expected_type = kwargs.get("expected_type", str)
    description = kwargs.get("description", "")
    default = kwargs.get("default")
    min_value = kwargs.get("min_value")
    max_value = kwargs.get("max_value")
    step = kwargs.get("step")
    hidden = kwargs.get("hidden")
    match param_type:
        case ParamType.INPUT:
            return ParamInput(
                name,
                optional=optional,
                file=file,
                depends_on=depends_on,
                expected_type=expected_type,
                description=description,
                default=default,
                min_value=min_value,
                max_value=max_value,
                step=step,
                hidden=hidden
            )
        case ParamType.SELECT:
            return ParamSelect(
                name,
                file=file,
                values=values,
                depends_on=depends_on,
                optional=optional,
                expected_type=expected_type,
                description=description,
            )
        case ParamType.BOOLEAN:
            return ParamBoolean(
                name,
                file,
                depends_on=depends_on,
                expected_type=expected_type,
                optional=optional,
                description=description,
            )
        case ParamType.INPUT_WITH_UNITY:
            return ParamInputWithUnity(
                name,
                file=file,
                values=values,
                depends_on=depends_on,
                optional=optional,
                expected_type=expected_type,
                # description=description,
            )
        case ParamType.BOOLEAN_WITH_INPUT:
            return ParamBooleanWithInput(
                name,
                file,
                depends_on=depends_on,
                expected_type=expected_type,
                optional=optional,
                description=description,
            )
        case ParamType.BOOLEAN_WITH_INPUT_WITH_UNITY:
            return ParamBooleanWithInputWithUnity(
                name,
                file=file,
                values=values,
                optional=optional,
                depends_on=depends_on,
                expected_type=expected_type,
                # description=description,
            )
        case ParamType.COMPONENT:
            return ParamComponent(
                name,
                file,
                values=values,
                depends_on=depends_on,
                optional=optional,
                expected_type=expected_type,
                description=description,
            )
        case ParamType.FIXED_WITH_INPUT:
            return ParamFixedWithInput(
                name,
                file,
                depends_on=depends_on,
                expected_type=expected_type,
                optional=optional,
                description=description,
                default=default,
                min_value=min_value,
                max_value=max_value,
                step=step,
            )
        case ParamType.RADIO:
            return ParamRadio(
                name,
                file,
                depends_on=depends_on,
                values=values,
                optional=optional,
                expected_type=expected_type,
                # description=description,
            )
        case ParamType.COMPONENT_SELECTOR:
            return ParamComponentSelector(
                name,
                file,
                depends_on=depends_on,
                values=values,
                optional=optional,
                expected_type=expected_type,
                # description=description,
            )
        case ParamType.SPIN_BOX:
            return ParamSpinBoxWithBool(
                name,
                file,
                depends_on=depends_on,
                optional=optional,
                expected_type=expected_type,
                # description=description,
            )
        case ParamType.FILECHOOSER:
            return ParamFileChooser(
                name,
                file,
                depends_on=depends_on,
                optional=optional,
                expected_type=expected_type,
                # description=description,
            )
        case _:
            raise ValueError(f"Unsupported param type: {param_type}")


# -----------------------------------------------------------
