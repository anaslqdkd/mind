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
    ParamFixedComponent,
    ParamFixedComponentWithCheckbox,
    ParamFixedMembrane,
    ParamFixedPerm,
    ParamFixedWithInput,
    ParamGrid,
    ParamGrid2,
    ParamInput,
    ParamInputWithUnity,
    ParamMemType,
    ParamMembraneSelect,
    ParamRadio,
    ParamSelect,
    ParamSpinBoxWithBool,
    ParamFixedWithSelect,
    debug_print,
)
from app.param_enums import FILE, ParamType
import inspect


# -----------------------------------------------------------
def create_param(name: str, param_type: ParamType, file: FILE, **kwargs) -> Param:
    optional = kwargs.get("optional", False)
    label = kwargs.get("label", "")
    values = kwargs.get("values", [])
    depends_on = kwargs.get("depends_on", {})
    expected_type = kwargs.get("expected_type", str)
    description = kwargs.get("description", "")
    default = kwargs.get("default")
    min_value = kwargs.get("min_value")
    max_value = kwargs.get("max_value")
    step = kwargs.get("step")
    hidden = kwargs.get("hidden", False)
    select_dir = kwargs.get("select_dir", False)
    match param_type:
        case ParamType.INPUT:
            return ParamInput(
                name,
                optional=optional,
                label=label,
                file=file,
                depends_on=depends_on,
                expected_type=expected_type,
                description=description,
                default=default,
                min_value=min_value,
                max_value=max_value,
                step=step,
                hidden=hidden,
            )
        case ParamType.SELECT:
            return ParamSelect(
                name,
                file=file,
                values=values,
                label=label,
                hidden=hidden,
                depends_on=depends_on,
                optional=optional,
                expected_type=expected_type,
                description=description,
            )
        case ParamType.BOOLEAN:
            return ParamBoolean(
                name,
                file,
                label=label,
                depends_on=depends_on,
                expected_type=expected_type,
                optional=optional,
                description=description,
            )
        case ParamType.INPUT_WITH_UNITY:
            return ParamInputWithUnity(
                name,
                file=file,
                label=label,
                values=values,
                depends_on=depends_on,
                optional=optional,
                expected_type=expected_type,
                default=default,
                # description=description,
            )
        case ParamType.BOOLEAN_WITH_INPUT:
            return ParamBooleanWithInput(
                name,
                file,
                label=label,
                depends_on=depends_on,
                expected_type=expected_type,
                optional=optional,
                description=description,
            )
        case ParamType.BOOLEAN_WITH_INPUT_WITH_UNITY:
            return ParamBooleanWithInputWithUnity(
                name,
                file=file,
                label=label,
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
                label=label,
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
                label=label,
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
                label=label,
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
                label=label,
                depends_on=depends_on,
                optional=optional,
                expected_type=expected_type,
                # description=description,
            )
        case ParamType.FIXED_WITH_SELECT:
            return ParamFixedWithSelect(
                name,
                file,
                label=label,
                values=values,
                depends_on=depends_on,
                optional=optional,
                expected_type=expected_type,
                # description=description,
            )
        case ParamType.FILECHOOSER:
            return ParamFileChooser(
                name,
                file,
                label=label,
                hidden=hidden,
                depends_on=depends_on,
                optional=optional,
                expected_type=expected_type,
                select_dir = select_dir,
                default = default,
                # description=description,
            )
        case ParamType.FIXED_PERM:
            return ParamFixedPerm(
                name,
                file,
                label=label,
                hidden=hidden,
                depends_on=depends_on,
                # membranes=["M1", "M2"],
                # components=["O2", "H2"],
                optional=optional,
                expected_type=expected_type,
                default = default,
                # description=description,
            )
        case ParamType.FIXED_MEMBRANE:
            return ParamFixedMembrane(
                name,
                file,
                label=label,
                hidden=hidden,
                depends_on=depends_on,
                optional=optional,
                expected_type=expected_type,
                default=default,
                min_value = min_value,
                max_value = max_value,
                # description=description,
            )
        case ParamType.FIXED_COMPONENT:
            return ParamFixedComponent(
                name,
                file,
                label=label,
                hidden=hidden,
                depends_on=depends_on,
                optional=optional,
                expected_type=expected_type,
                default=default
                # description=description,
            )
        case ParamType.FIXED_MEMBRANE_SELECT:
            return ParamMembraneSelect(
                name,
                file,
                values=values,
                label=label,
                hidden=hidden,
                depends_on=depends_on,
                optional=optional,
                # description=description,
            )
        case ParamType.FIXED_MEM_TYPE:
            return ParamMemType(
                name,
                file,
                # values=values,
                label=label,
                hidden=hidden,
                depends_on=depends_on,
                optional=optional,
                # description=description,
            )
        case ParamType.FIXED_COMPONENT_WITH_CHECKBOX:
            return ParamFixedComponentWithCheckbox(
                name,
                file,
                # values=values,
                # components=["buu", "gaga"],
                # values = ["value 1", "value 2"],
                label=label,
                hidden=hidden,
                depends_on=depends_on,
                optional=optional,
                # description=description,
            )
        case ParamType.FIXED_COMPONENT_WITH_CHECKBOX_MATRIX:
            return ParamGrid(
                name,
                file,
                # nb_components=3,
                # values=values,
                # components=["buu", "gaga"],
                label=label,
                hidden=hidden,
                depends_on=depends_on,
                optional=optional,
                # description=description,
            )
        case ParamType.FIXED_MATRIX:
            return ParamGrid2(
                name,
                file,
                # nb_components=3,
                # values=values,
                # components=["buu", "gaga"],
                label=label,
                hidden=hidden,
                depends_on=depends_on,
                optional=optional,
                max_value = max_value,
                min_value = min_value,
                default = default,
                step = step,
                # description=description,
            )
        case _:
            raise ValueError(f"Unsupported param type: {param_type}")


# -----------------------------------------------------------
