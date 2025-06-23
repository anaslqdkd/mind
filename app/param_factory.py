from app import dependency_manager, param_dict
from app.param import Param, ParamFixedWithInput, ParamInput, debug_print
from app.param_enums import FILE, DependencyType, ParamType
from app.param_utils import create_param
from app.param_dict import params_dict

# -----------------------------------------------------------

def build_all_params(all_param_specs):
    all_params = {}
    for name, param_specs in all_param_specs.items():
        all_params[name] = create_param(**param_specs)
    return all_params


def set_param(all_param_specs: dict):
    param_registry = {}
    all_params = build_all_params(all_param_specs)
    for name, param in all_params.items():
        param_registry[name] = param
    return param_registry

# -----------------------------------------------------------
