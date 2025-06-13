from app.param import Param
from app.param_enums import FILE, DependencyType, ParamType
from app.param_utils import create_param
from app.param_validator import LineEditValidation

algo_param_specs = {
    "num_membranes": {
        "name": "num_membranes",
        "param_type": ParamType.INPUT,
        "file": FILE.DATA,
        "optional": False,
        "expected_type": int,
    },
    "Another one": {
        "name": "idk",
        "param_type": ParamType.INPUT,
        "file": FILE.DATA,
        "expected_type": int,
    },
    "Select test": {
        "name": "select",
        "param_type": ParamType.SELECT,
        "values": ["multistart", "mbh", "global", "population", "genetic"],
        "file": FILE.DATA,
    },
    "Bool test": {"name": "check", "param_type": ParamType.BOOLEAN, "file": FILE.DATA},
    "Input with unity test": {
        "name": "input with unity",
        "param_type": ParamType.INPUT_WITH_UNITY,
        "values": ["bar", "Pa", "kPa"],
        "file": FILE.DATA,
    },
    "Boolean with input test": {
        "name": "boolean with input",
        "param_type": ParamType.BOOLEAN_WITH_INPUT,
        "file": FILE.DATA,
    },
    "Boolean with input and unity": {
        "name": "boolean with input and unity",
        "param_type": ParamType.BOOLEAN_WITH_INPUT_WITH_UNITY,
        "values": ["option 1", "option 2", "option 3"],
        "file": FILE.DATA,
    },
    "Component": {
        "name": "component test",
        "param_type": ParamType.COMPONENT,
        "file": FILE.DATA,
        "values": ["H2O", "H2", "CO2"],
    },
    "Radio text": {
        "name": "bu",
        "param_type": ParamType.RADIO,
        "file": FILE.DATA,
        # "depends_on": {"num_membranes": DependencyType.COMPONENT_COUNT},
        "values": ["option 1", "option 2", "option 3"],
        "expected_type": int,
    },
    "Another flds": {
        "name": "bu",
        "param_type": ParamType.COMPONENT_SELECTOR,
        "file": FILE.DATA,
        "depends_on": {"num_membranes": DependencyType.COMPONENT_COUNT},
        "expected_type": int,
    },
    "AAAA": {
        "name": "bu",
        "param_type": ParamType.FIXED_WITH_INPUT,
        "file": FILE.DATA,
        "depends_on": {"num_membranes": DependencyType.COMPONENT_COUNT},
        "expected_type": int,
    },
}
algo_param_specs2 = {
    "num_membranes": {
        "name": "num_membranes",
        "param_type": ParamType.INPUT,
        "file": FILE.DATA,
        "optional": False,
        "expected_type": int,
    },
    "Another one": {
        "name": "idk",
        "param_type": ParamType.INPUT,
        "file": FILE.DATA,
        "expected_type": int,
    },
    "Select test": {
        "name": "select",
        "param_type": ParamType.SELECT,
        "values": ["multistart", "mbh", "global", "population", "genetic"],
        "file": FILE.DATA,
    },
}


def build_param_dict(param_specs):
    params = {}
    for label, spec in param_specs.items():
        params[label] = create_param(**spec)
    set_dependency(params)
    set_validation(params)
    return params


def set_param(params: dict):
    algo_params = build_param_dict(params)
    param = {}
    param_page1 = {"Algorithm parameters": algo_params, "Other parameters": param}
    return param_page1


# -----------------------------------------------------------


def set_validation(params: dict["str", Param]):
    def apply_validation_rules(param: Param, rules: dict):
        if isinstance(param, LineEditValidation):
            param.set_validation(**rules)

    for _, param in params.items():
        if param.name == "num_membranes":
            apply_validation_rules(param, {"min_value": 1, "max_value": 2})
    pass


# -----------------------------------------------------------


def set_dependency(params: dict["str", Param]):
    for key, value in params.items():
        depends_on = getattr(value, "depends_on", None)
        if not depends_on:
            continue
        for el in value.depends_on_names:
            print("the value.name is", el)
            dep_param = params.get(el)
            if dep_param:
                print("here")
                print(dep_param.name)
                dep_type = value.depends_on.get(el)
                value.depends_on_params[dep_param] = dep_type
                if not hasattr(dep_param, "dependants"):
                    dep_param.dependants = {}
                dep_param.dependants[value] = dep_type

    # link dependencies
    for key, value in params.items():
        # print("++++", value.depends_on_names)
        depends_on = getattr(value, "depends_on_names", None)
        if not depends_on:
            # print("°))) here")
            continue
        for dep_name, dep_type in value.depends_on_names.items():
            # print("TTTTTT")
            dep_param = params.get(dep_name)
            print(dep_param)
            if dep_param:
                print(f"Dependency found: {dep_name} → {dep_type}")
                value.depends_on_params[dep_param] = dep_type
                if not hasattr(dep_param, "dependants"):
                    dep_param.dependants = {}
                dep_param.dependants[value] = dep_type
