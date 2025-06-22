from app import dependency_manager
from app.param import Param, ParamFixedWithInput, ParamInput, debug_print
from app.param_enums import FILE, DependencyType, ParamType
from app.param_utils import create_param
from app.param_validator import LineEditValidation

execution_settings = {
    "Enable Logging Output": {
        "name": "verbose",
        "param_type": ParamType.BOOLEAN,
        "file": FILE.COMMAND,
        "optional": True,
        "description": "Verbose option for debugging",
    },
    "Enable Debug Mode": {
        "name": "debug",
        "param_type": ParamType.BOOLEAN,
        "file": FILE.COMMAND,
        "optional": True,
    },
}

algorithm_options = {
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
        "optional": False,
    },
    "Time Limit": {
        "name": "maxtime",
        "param_type": ParamType.SPIN_BOX,
        "file": FILE.COMMAND,
        "optional": True,
        "values": ["i1", "i2", "i3", "i4"],
    },
    "Algorithm": {
        "name": "algorithm",
        "param_type": ParamType.SELECT,
        "file": FILE.COMMAND,
        "values": ["multistart", "mbh", "global", "genetic", "population"],
        "description": "Selected algorithm for the simulation",
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
    "Population Size": {
        "name": "pop_size",
        "param_type": ParamType.INPUT,
        "file": FILE.CONFIG,
        "optional": False,
        # "depends_on": {"Algorithm": DependencyType.VISIBLE},
        "expected_value": ["population", "genetic"],
        "hidden": True,
    },
}

visualization = {
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
}

output_options = {
    "Save Solution Log": {
        "name": "save_log_sol",
        "param_type": ParamType.BOOLEAN,
        "file": FILE.COMMAND,
        "optional": True,
        "description": "",
    },
}

advanced = {
    "Save Solution Log": {
        "name": "save_log_sol",
        "param_type": ParamType.BOOLEAN,
        "file": FILE.COMMAND,
        "optional": True,
    },
    "Spin box test": {
        "name": "spin box",
        "param_type": ParamType.SPIN_BOX,
        "file": FILE.COMMAND,
        "optional": True,
    },
}
membranes_options = {
    "Number of membranes": {
        "name": "num_membranes",
        "param_type": ParamType.INPUT,
        "file": FILE.CONFIG,
        "optional": False,
        "description": "number of membranes",
        "default": 0,
        "min_value": 0,
        "max_value": 3,  # the inital program assert <= 3
    },
    "Upper bound area": {
        "name": "ub_area",
        "param_type": ParamType.FIXED_WITH_INPUT,
        "file": FILE.CONFIG,
        # "depends_on": {"Number of membranes": DependencyType.COMPONENT_COUNT},
        "default": 5,
        "min_value": 0,
        "max_value": 10,
        "step": 1,
    },
    "Lower bound area": {
        "name": "lb_area",
        "param_type": ParamType.FIXED_WITH_INPUT,
        "file": FILE.CONFIG,
        # "depends_on": {"Number of membranes": DependencyType.COMPONENT_COUNT},
        "default": 0.1,
        "min_value": 0,
        "max_value": 10,
        "step": 0.1,
    },
    "Upper bound cell": {
        "name": "ub_acell",
        "param_type": ParamType.FIXED_WITH_INPUT,
        "file": FILE.CONFIG,
        # "depends_on": {"Number of membranes": DependencyType.COMPONENT_COUNT},
        "default": 0.1,
        "min_value": 0,
        "max_value": 10,
        "step": 0.1,
    },
}
membranes_behaviour_flags = {
    "Fixing": {
        "name": "fixing_var",
        "param_type": ParamType.BOOLEAN,
        "file": FILE.CONFIG,
        "optional": False,
    },
    "Uniform Pup": {
        "name": "uniform_pup",
        "param_type": ParamType.BOOLEAN,
        "file": FILE.CONFIG,
        "optional": False,
    },
    "Vacuum Pump": {
        "name": "vp",
        "param_type": ParamType.BOOLEAN,
        "file": FILE.CONFIG,
        "optional": False,
    },
    "Variable Permeability": {
        "name": "variable_perm",
        "param_type": ParamType.BOOLEAN,
        "file": FILE.CONFIG,
        "optional": False,
    },
}
algo_iteration_control = {
    "Iteration": {
        "name": "iteration",
        "param_type": ParamType.INPUT,
        "file": FILE.CONFIG,
        "optional": False,
        "default": 200,
        "min_value": 1,
        "max_value": 10000,
        "step": 10,
    },
    "Max no improve": {
        "name": "max_no_improve",
        "param_type": ParamType.INPUT,
        "file": FILE.CONFIG,
        "optional": False,
        "default": 5,
        "min_value": 1,
        "max_value": 10000,
        "step": 1,
    },
    "Max trials": {
        "name": "max_trials",
        "param_type": ParamType.INPUT,
        "file": FILE.CONFIG,
        "optional": False,
        "default": 10,
        "min_value": 1,
        "max_value": 10000,
        "step": 1,
    },
    "Pressure ratio": {
        "name": "pressure_ratio",
        "param_type": ParamType.INPUT,
        "file": FILE.CONFIG,
        "optional": False,
        "default": 0.03,
        "min_value": 0,
        "max_value": 1,
        "step": 0.01,
    },
    # eventually, pop_size, generation, and n1_element
    # TODO: add dependency for pop_size, generation and n1_element
}
components = {
    "Components": {
        "name": "set components",
        "param_type": ParamType.COMPONENT_SELECTOR,
        "file": FILE.DATA,
        "values": ["H20", "O2", "H2"],
        "optional": False,
    },
    "XIN": {
        "name": "param xin",
        "param_type": ParamType.FIXED_WITH_INPUT,
        "file": FILE.DATA,
        "optional": False,
        # "depends_on": {"Components": DependencyType.COMPONENT_COUNT},
    },
    "Molar Mass": {
        "name": "param molarmass",
        "param_type": ParamType.FIXED_WITH_INPUT,
        "file": FILE.DATA,
        "optional": False,
        # "depends_on": {"Components": DependencyType.COMPONENT_COUNT},
    },
    "Filechooser test": {
        "name": "param molarmass",
        "param_type": ParamType.FILECHOOSER,
        "file": FILE.DATA,
        "optional": False,
    },
}

all_params = {
    "Dict 1": {
        "Execution settings": execution_settings,
        "Algorithm Options": algorithm_options,
        "Visualisation": visualization,
        "Output Options": output_options,
    },
    "Dict 2": {
        "Visualization": visualization,
        "Output Options": output_options,
        "Advanced": advanced,
    },
    "Dict 3": {
        "Membrane options": membranes_options,
        "Membrane behaviour": membranes_behaviour_flags,
        "Algorithm iteration control": algo_iteration_control,
    },
    "Dict 4": {
        "Components": components,
    },
}

param_registry = {}


def build_param_dict(param_specs) -> dict[str, Param]:
    params = {}
    for label, spec in param_specs.items():
        params[label] = create_param(**spec)
        param_registry[label] = params[label]
    # set_dependency(params)
    # TODO: manage dependency between parameters that are not in the same category
    set_validation(params)
    return params


def build_all_params(all_param_specs) -> dict[str, dict[str, Param]]:
    all_params = {}
    for category, param_specs in all_param_specs.items():
        all_params[category] = build_param_dict(param_specs)
    # debug_print(param_registry.keys())
    return all_params


dependency_manager = dependency_manager.DependencyManager()


def set_param(all_param_specs: dict) -> dict[str, dict[str, Param]]:
    all_params = build_all_params(all_param_specs)
    return all_params


def set_dep():
    debug_print(param_registry)
    register_param_dependencies(param_registry, dependency_manager)
    for param in param_registry.values():
        param.manager = dependency_manager


# -----------------------------------------------------------
def register_param_dependencies(param_registry, dependency_manager):
    dependency_manager.add_dependency(
        param_registry["Number of membranes"],
        param_registry["Upper bound area"],
        update_fn,
    )
    dependency_manager.add_dependency(
        param_registry["Number of membranes"],
        param_registry["Lower bound area"],
        update_fn,
    )
    debug_print(dependency_manager.dependencies)


def update_fn(target: ParamFixedWithInput, source: ParamInput):
    debug_print(f"the source is {source.name} and the target is {target.name}")
    target.set_rows_nb(int(source.get_value()))
    target.category.update_category()
    debug_print("in the update fn fucntion")

def update_fn_2(source: Param, target: Param):
    debug_print("in the update fn function 2")


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
            dep_param = params.get(el)
            if dep_param:
                dep_type = value.depends_on.get(el)
                value.depends_on_params[dep_param] = dep_type
                if not hasattr(dep_param, "dependants"):
                    dep_param.dependants = {}
                dep_param.dependants[value] = dep_type

    # link dependencies
    for key, value in params.items():
        depends_on = getattr(value, "depends_on_names", None)
        if not depends_on:
            continue
        for dep_name, dep_type in value.depends_on_names.items():
            dep_param = params.get(dep_name)
            if dep_param:
                print(f"Dependency found: {dep_name} → {dep_type}")
                value.depends_on_params[dep_param] = dep_type
                if not hasattr(dep_param, "dependants"):
                    dep_param.dependants = {}
                dep_param.dependants[value] = dep_type


# -----------------------------------------------------------
