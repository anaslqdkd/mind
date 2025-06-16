from app.param import Param
from app.param_enums import FILE, DependencyType, ParamType
from app.param_utils import create_param
from app.param_validator import LineEditValidation

all_params = {
    "Execution settings": {
        "Enable Logging Output": {
            "name": "logging",
            "param_type": ParamType.BOOLEAN,
            "file": FILE.COMMAND,
            "optional": True,
        },
        "Enable Debug Mode": {
            "name": "debug",
            "param_type": ParamType.BOOLEAN,
            "file": FILE.COMMAND,
            "optional": True,
        },
    },
    "Algorithm Options": {
        "Solver": {
            "name": "solver",
            "param_type": ParamType.SELECT,
            "file": FILE.COMMAND,
            "optional": True,
            "values": ["knitro", "gurobi"],
        },
        "Use GAMS": {
            "name": "gams",
            "param_type": ParamType.BOOLEAN,
            "file": FILE.COMMAND,
            "optional": True,
        },
        "Max Iterations": {
            "name": "maxiter",
            "param_type": ParamType.BOOLEAN_WITH_INPUT,
            "file": FILE.COMMAND,
            "optional": True,
        },
        "Time Limit": {
            "name": "maxtime",
            "param_type": ParamType.BOOLEAN_WITH_INPUT_WITH_UNITY,
            "file": FILE.COMMAND,
            "optional": True,
            "values": ["i1", "i2", "i3", "i4"],
        },
        "Algorithm": {
            "name": "algorithm",
            "param_type": ParamType.SELECT,
            "file": FILE.COMMAND,
            "values": ["multistart", "mbh", "global", "genetic", "population"],
            "optional": True,
        },
        "Do Not Generate Starting Point": {
            "name": "no_starting_point",
            "param_type": ParamType.BOOLEAN,
            "file": FILE.COMMAND,
            "optional": True,
        },
        "Do Not Use Simplified Model": {
            "name": "no_simplified_model",
            "param_type": ParamType.BOOLEAN,
            "file": FILE.COMMAND,
            "optional": True,
        },
    },
    "Visualization": {
        "Enable Visualization": {
            "name": "visualise",
            "param_type": ParamType.BOOLEAN,
            "file": FILE.COMMAND,
            "optional": True,
        },
        "Show OPEX Visualization": {
            "name": "opex",
            "param_type": ParamType.BOOLEAN,
            "file": FILE.COMMAND,
            "optional": True,
        },
        "Show CAPEX Visualization": {
            "name": "capex",
            "param_type": ParamType.BOOLEAN,
            "file": FILE.COMMAND,
            "optional": True,
        },
    },
    "Output Options": {
        "Save Solution Log": {
            "name": "save_log_sol",
            "param_type": ParamType.BOOLEAN,
            "file": FILE.COMMAND,
            "optionnal": True,
        }
    },
}


def build_param_dict(param_specs):
    params = {}
    for label, spec in param_specs.items():
        params[label] = create_param(**spec)
    set_dependency(params)
    set_validation(params)
    return params


def build_all_params(all_param_specs):
    all_params = {}
    for category, param_specs in all_param_specs.items():
        all_params[category] = build_param_dict(param_specs)
    return all_params


def set_param(all_param_specs: dict):
    all_params = build_all_params(all_param_specs)
    return all_params


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
