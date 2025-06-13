from app.param import (
    Param,
    ParamBoolean,
    ParamBooleanWithInput,
    ParamBooleanWithInputWithUnity,
    ParamComponent,
    ParamComponentSelector,
    ParamFixedWithInput,
    ParamInput,
    ParamInputWithUnity,
    ParamRadio,
    ParamSelect,
)
from app.param_enums import FILE, ParamType


# -----------------------------------------------------------
def create_param(name: str, param_type: ParamType, file: FILE, **kwargs) -> Param:
    optional = kwargs.get("optional", False)
    values = kwargs.get("values", [])
    depends_on = kwargs.get("depends_on", [])
    expected_type = kwargs.get("expected_type", str)
    print("the expected type in create param is", expected_type)
    match param_type:
        case ParamType.INPUT:
            return ParamInput(
                name,
                optional=optional,
                file=file,
                depends_on=depends_on,
                expected_type=expected_type,
            )
        case ParamType.SELECT:
            return ParamSelect(
                name,
                file=file,
                values=values,
                depends_on=depends_on,
                expected_type=expected_type,
            )
        case ParamType.BOOLEAN:
            return ParamBoolean(
                name, file, depends_on=depends_on, expected_type=expected_type
            )
        case ParamType.INPUT_WITH_UNITY:
            return ParamInputWithUnity(
                name,
                file=file,
                values=values,
                depends_on=depends_on,
                expected_type=expected_type,
            )
        case ParamType.BOOLEAN_WITH_INPUT:
            return ParamBooleanWithInput(
                name, file, depends_on=depends_on, expected_type=expected_type
            )
        case ParamType.BOOLEAN_WITH_INPUT_WITH_UNITY:
            return ParamBooleanWithInputWithUnity(
                name,
                file=file,
                values=values,
                depends_on=depends_on,
                expected_type=expected_type,
            )
        case ParamType.COMPONENT:
            return ParamComponent(
                name,
                file,
                values=values,
                depends_on=depends_on,
                expected_type=expected_type,
            )
        case ParamType.FIXED_WITH_INPUT:
            return ParamFixedWithInput(
                name, file, depends_on=depends_on, expected_type=expected_type
            )
        case ParamType.RADIO:
            return ParamRadio(
                name,
                file,
                depends_on=depends_on,
                values=values,
                expected_type=expected_type,
            )
        case ParamType.COMPONENT_SELECTOR:
            return ParamComponentSelector(
                name,
                file,
                depends_on=depends_on,
                values=values,
                expected_type=expected_type,
            )
        case _:
            raise ValueError(f"Unsupported param type: {param_type}")


# -----------------------------------------------------------
