#!/usr/bin/env python
# -*- coding: utf-8 -*-
#  ___________________________________________________________________________
#
#  Mind: Python Optimization Software for Process Design Membranes
#  LICENCE.
#  rights in this software.
#  ___________________________________________________________________________
"""Launcher or gateway to the project.

This module call others modules to construct and execute an instance model
of the project.

Example:
    - modelisation = builder.build_model(configuration, parameter_file)
    - my_solver = GlobalOptimisation(optsolver,
                                     modelisation,
                                     log_dir).

"""
# Note:
#     - Inline equation: \\( v_t *\\frac{1}{2}* j_i + [a] < 3 \\).
#     - Block equation: \\[ v_t *\\frac{1}{2}* j_i + [a] < 3 \\]
#     - Block equation: $$ v_t *\\frac{1}{2}* j_i + [a] < 3 $$
#     - test1: $$W_{tot} = \\frac{ W_{cp_f}}{1} + \\sum_{ s \\in {\\cal S}} (W_{cp_{s}}) $$
#     - test2: \\[W_{tot} = \\frac{ W_{cp_f}}{1} + \\sum_{ s \\in {\\cal S}}  (W_{cp_{s}}) \\]

import time
import sys
import os
import argparse
import configparser
import logging
import pprint

import pyomo.environ as pe

# Own modules
from mind.builder import Configuration, build_model
from mind.solve import GlobalOptimisation
from mind.post_process import PostProcess

# from mind.analyse_sol import generate_datafiles
# from mind.optmodel_utilities import initZero
from mind.util import generate_absolute_path
from mind.interfaceSolver import SolverObject


pp = pprint.PrettyPrinter(indent=4)
default_use_case = "n2capture"
use_cases = "n2capture, CO2N2He, co2capture, ch4co2, h2selectivityco2, h2co2selectivity, n2capture_multi, co2capture_air, co2capture_combustion, orano, CEA_VALDUC, VEOLIA, ARKEMA_1, ARKEMA_2"
algorithms = ["multistart", "mbh", "global_opt", "genetic", "population"]

# logging variable
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)
handler = logging.StreamHandler()
# handler = logging.FileHandler(filename)
logger.addHandler(handler)
formatter = logging.Formatter(
    fmt="[%(asctime)s] %(levelname)s : %(message)s", datefmt="%a, %d %b %Y %H:%M:%S"
)
handler.setFormatter(formatter)


def parse_args():
    """Input arguments or options traitements.

    Print below usage informations:

        -h, --help : show this help message and exit

        --verbose : when *verbose* then logging informations are printed

        --debug : debug_mode

        --no_starting_point : starting point flag

        --no_simplified_model : simplified model flag

        --gams : `True` if GAMS solver is available

        --solver SOLVER_NAME : solver name

        --version : print software version

        Note: Further documentation is available by contacting <bernardetta.addis@loria.fr>.

    """
    # Handling args
    parser = argparse.ArgumentParser(
        description=(
            "SATT SAYENS ENTREPRISE'S PROJECT: "
            "Optimization program aiding process engineer "
            "for membrane system design separation"
        ),
        epilog=(
            "Further documentation is available "
            "by contacting <bernardetta.addis@loria.fr>."
        ),
    )

    parser.add_argument(
        "--verbose", action="store_true", help=("Enable mind_api 's logging")
    )

    parser.add_argument(
        "--debug", action="store_true", help="debug_mode : Display solvers's logging"
    )

    parser.add_argument(
        "--config", action="store_true", help="generate configuration file : config.ini"
    )

    parser.add_argument(
        "--exec",
        action="store_true",
        help="execute instance described in configuration file (config.ini)",
    )

    parser.add_argument(
        "--no_starting_point", action="store_true", help="""Starting point flag"""
    )

    parser.add_argument(
        "--no_simplified_model", action="store_true", help="""Simplified model flag"""
    )

    parser.add_argument(
        "--gams",
        action="store_true",
        help=("True if gams (General Algebraic Modeling " "Language) solver available"),
    )

    parser.add_argument(
        "--solver",
        action="store",
        dest="solver_name",
        type=str,
        default="knitroampl",
        help="""Solver name""",
    )

    parser.add_argument(
        "--maxiter",
        action="store",
        dest="maxiter",
        type=int,
        help="""max. iterations of selected algorithms""",
    )

    parser.add_argument(
        "--maxtime",
        action="store",
        dest="maxtime",
        type=int,
        help="""time limit execution of algorithms""",
    )

    parser.add_argument(
        "--algorithm",
        action="store",
        dest="algorithm_choice",
        type=str,
        default="multistart",
        help="""Choice of algorithms in ({})""".format(", ".join(algorithms)),
    )

    parser.add_argument(
        "--instance",
        action="store",
        dest="instance_name",
        type=str,
        # default=argparse.SUPPRESS,
        help="""Use case's name in ({})""".format(use_cases),
    )

    parser.add_argument(
        "--visualise", action="store_true", help="visualise desing process's result"
    )

    parser.add_argument(
        "--opex",
        action="store_true",
        help="graphic visualisation of process desing economic cost opex",
    )

    parser.add_argument(
        "--capex",
        action="store_true",
        help="graphic visualisation of process desing economic cost capex",
    )

    parser.add_argument(
        "--save_log_sol",
        action="store_true",
        help="save some of desing process economic informations in solution.txt",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="Mind's software version: V.0.5",
        help="""print software version""",
    )

    return parser.parse_args()


def data_instance(case_study):
    """Real world instance data description.
    Returns:
        return problem instance to solve
    """
    if not case_study or (case_study not in use_cases):
        logger.warning("Given instance's name ('{}') is not defined".format(case_study))
        logger.warning(f"Default instance ({default_use_case}) will be executed")
        case_study = default_use_case

    instance = {}
    instance["data_dir"] = generate_absolute_path() + "data" + os.path.sep
    instance["log_dir"] = generate_absolute_path() + "log" + os.path.sep
    # instance['f_log'] = open(instance['log_dir'] + 'solverModel.log', 'w')

    instance["num_membranes"] = 3
    instance["ub_area"] = [50, 50, 50]
    instance["lb_area"] = [1, 1, 1]
    instance["ub_acell"] = [1, 1, 1]

    # instance['ub_area'] = [50,50]
    # instance['lb_area'] = [0.1, 0.1]
    # instance['ub_acell'] = [0.1, 0.1]

    # instance['ub_area'] = [200]
    # instance['lb_area'] = [0.1]
    # instance['ub_acell'] = [1]

    instance["fixing_var"] = False

    instance["fname_mask"] = instance["data_dir"] + "fixing" + os.path.sep + "mask.dat"
    instance["prototype_data"] = instance["data_dir"] + "prototype_individuals.yaml"

    if case_study == "n2capture":
        instance["fname"] = instance["data_dir"] + "N2Capture.dat"
        instance["fname_perm"] = instance["data_dir"] + "N2Capture_perm.dat"
        instance["fname_perm"] = instance["data_dir"] + "N2Capture_fix_perm.dat"
        instance["fname_eco"] = instance["data_dir"] + "N2Capture_eco.dat"
        instance["uniform_pup"] = True
        instance["vp"] = True
        instance["variable_perm"] = False

    if case_study == "CO2N2He":
        instance["fname"] = instance["data_dir"] + "CO2_N2_458.dat"
        instance["fname_perm"] = instance["data_dir"] + "CO2_N2_458_fix_perm.dat"
        instance["fname_eco"] = instance["data_dir"] + "CO2_N2_458_eco.dat"
        # instance['fname_mask'] = (instance['data_dir'] + 'fixing' + os.path.sep +
        #                        'CO2N2458_mask.dat')
        instance["uniform_pup"] = False
        instance["vp"] = False
        instance["variable_perm"] = False

    if case_study == "ARKEMA_1":
        instance["fname"] = instance["data_dir"] + "Arkema_1.dat"
        instance["fname_perm"] = instance["data_dir"] + "Arkema_1_fix_perm.dat"
        instance["fname_eco"] = instance["data_dir"] + "Arkema_1_eco.dat"
        # instance['fname_mask'] = (instance['data_dir'] + 'fixing' + os.path.sep +
        #                        'Arkema_1_mask.dat')
        instance["uniform_pup"] = False
        instance["vp"] = True
        instance["variable_perm"] = False

    if case_study == "ARKEMA_2":
        instance["fname"] = instance["data_dir"] + "Arkema_1.dat"
        instance["fname_perm"] = instance["data_dir"] + "Arkema_1_fix_perm.dat"
        instance["fname_eco"] = instance["data_dir"] + "Arkema_1_eco.dat"
        # instance['fname_mask'] = (instance['data_dir'] + 'fixing' + os.path.sep +
        #                        'Arkema_1_mask.dat')
        instance["uniform_pup"] = False
        instance["vp"] = True
        instance["variable_perm"] = False

    elif case_study == "h2selectivityco2":
        instance["fname"] = instance["data_dir"] + "H2selectivityCO2.dat"
        instance["fname_perm"] = instance["data_dir"] + "H2selectivityCO2_perm.dat"
        instance["fname_perm"] = instance["data_dir"] + "H2selectivityCO2_fix_perm.dat"
        instance["fname_eco"] = instance["data_dir"] + "H2selectivityCO2_eco.dat"
        instance["uniform_pup"] = True
        instance["vp"] = False
        instance["variable_perm"] = False

    elif case_study == "h2co2selectivity":
        instance["fname"] = instance["data_dir"] + "H2CO2selectivity.dat"
        instance["fname_perm"] = instance["data_dir"] + "H2CO2selectivity_perm.dat"
        instance["fname_perm"] = instance["data_dir"] + "H2CO2selectivity_fix_perm.dat"
        instance["fname_mask"] = (
            instance["data_dir"] + "fixing" + os.path.sep + "N2Capture_mask.dat"
        )
        instance["fname_eco"] = instance["data_dir"] + "H2CO2selectivity_eco.dat"
        instance["uniform_pup"] = True
        instance["vp"] = False
        instance["variable_perm"] = False

    elif case_study == "n2capture_multi":
        instance["fname"] = instance["data_dir"] + "N2Capture_multiProfile.dat"
        instance["fname_perm"] = (
            instance["data_dir"] + "N2Capture_multiProfile_perm.dat"
        )
        instance["fname_eco"] = instance["data_dir"] + "N2Capture_multiProfile_eco.dat"
        instance["uniform_pup"] = True
        instance["vp"] = True
        instance["variable_perm"] = True

    elif case_study == "co2capture":
        instance["fname"] = instance["data_dir"] + "CO2Capture.dat"
        instance["fname_perm"] = instance["data_dir"] + "CO2Capture_perm.dat"
        # instance['fname_perm'] = (instance['data_dir'] + 'CO2Capture_combustion_perm_tradeoff.dat')
        instance["fname_eco"] = instance["data_dir"] + "CO2_N2_458_eco.dat"
        instance["uniform_pup"] = True
        instance["vp"] = True
        instance["variable_perm"] = False

    elif case_study == "co2capture_air":
        instance["fname"] = instance["data_dir"] + "CO2Capture_fromair.dat"
        instance["fname_perm"] = instance["data_dir"] + "CO2Capture_fromair_perm.dat"
        instance["fname_eco"] = instance["data_dir"] + "CO2Capture_fromair_eco.dat"
        instance["uniform_pup"] = True
        instance["vp"] = True
        instance["variable_perm"] = False

    elif case_study == "co2capture_combustion":
        instance["fname"] = instance["data_dir"] + "CO2Capture_combustion.dat"
        instance["fname_perm"] = instance["data_dir"] + "CO2Capture_combustion_perm.dat"
        instance["fname_eco"] = instance["data_dir"] + "CO2Capture_combustion_eco.dat"
        instance["uniform_pup"] = False
        instance["vp"] = True
        instance["variable_perm"] = False

    elif case_study == "ch4co2":
        instance["fname"] = instance["data_dir"] + "CH4CO2.dat"
        instance["fname_perm"] = instance["data_dir"] + "CH4CO2_perm.dat"
        instance["fname_eco"] = instance["data_dir"] + "CH4CO2_eco.dat"
        instance["uniform_pup"] = True
        instance["vp"] = True
        instance["variable_perm"] = False

    elif case_study == "orano":
        instance["fname"] = instance["data_dir"] + "Orano.dat"
        instance["fname_perm"] = instance["data_dir"] + "Orano_fix_perm.dat"
        instance["fname_eco"] = instance["data_dir"] + "Orano_eco.dat"
        instance["uniform_pup"] = False
        instance["vp"] = True
        instance["variable_perm"] = False

    elif case_study == "CEA_VALDUC":
        instance["fname"] = instance["data_dir"] + "CEA_VALDUC.dat"
        instance["fname_perm"] = instance["data_dir"] + "CEA_VALDUC_perm.dat"
        instance["fname_eco"] = instance["data_dir"] + "CEA_VALDUC_eco.dat"
        instance["uniform_pup"] = False
        instance["vp"] = False
        instance["variable_perm"] = False

    elif case_study == "VEOLIA":
        instance["fname"] = instance["data_dir"] + "VEOLIA.dat"
        instance["fname_perm"] = instance["data_dir"] + "VEOLIA_perm.dat"
        instance["fname_eco"] = instance["data_dir"] + "VEOLIA_eco.dat"
        instance["uniform_pup"] = False
        instance["vp"] = True
        instance["variable_perm"] = False

    # else:
    #     assert False
        # logger.exception("Given instance ('{}') is not defined".format(case_study))
        # raise ValueError("Given instance ('{}') is not defined".format(case_study))
    return instance


def printing_post_process_operation(
    model, parameter, obj_object, arg_capex=False, arg_opex=False, save_sol=False
):
    """Printing post resolution of model's instance solve.

    Args:
        model (mind.model.MembranesDesignModel) : desing process model's instance

        parameter (`mind.builder.Configuration`) : design process configuration

        logger (`Python.logging`) : desing process model's instance

    """

    post_traitement = PostProcess()

    val = post_traitement.evaluate_objective(model)
    # evaluate_feasibility(model)
    # Evaluate objective function
    logger.info("Evaluation [obj func = {}]".format(val))

    if arg_capex:
        post_traitement.histogram_capex(model, obj_object)

    if arg_opex:
        post_traitement.histogramme_opex(obj_object)

    if save_sol:
        post_traitement.generate_sol_log(model, "solution.txt", obj_object)


def tuning_param():
    tuning = {}

    tuning["pressure_ratio"] = 0.03
    tuning["epsilon"] = {
        "At": 0.3,
        "press_up_f": 0.2,
        "press_down_f": 0.2,
        "feed": 0.3,
        "perm_ref": 0.1,
        "alpha": 0.1,
        "delta": 0.1,
        "xout": 1e-4,
    }
    tuning["seed1"] = 2
    tuning["seed2"] = 1
    tuning["iteration"] = 50
    tuning["max_no_improve"] = 5
    tuning["max_trials"] = 10
    tuning["pop_size"] = 30
    tuning["generations"] = 5
    tuning["n1_element"] = 5
    return tuning


def generate_configuration():
    config = configparser.ConfigParser()
    config["tuning"] = tuning_param()
    config["instance"] = data_instance(default_use_case)

    with open("config.ini", "w") as config_file:
        config.write(config_file)


def load_configuration():
    tuning_params = [
        "seed1",
        "seed2",
        "iteration",
        "max_no_improve",
        "epsilon",
        "pressure_ratio",
        "max_trials",
        "pop_size",
        "generations",
        "n1_element",
    ]

    instance_params = [
        "fname",
        "fname_perm",
        "fname_eco",
        "num_membranes",
        "ub_area",
        "lb_area",
        "ub_acell",
        "vp",
        "uniform_pup",
        "variable_perm",
        "fixing_var",
    ]
    config = configparser.ConfigParser()
    try:
        config.read("/home/ash/mind/temp/config.ini")
        print(os.getcwd())
        print(config.sections())
        if not ("tuning" in config.sections() and "instance" in config.sections()):
            raise ValueError(
                f"Errror: config.ini is not set correctly, generate new one with option (--config)"
            )
        for param in tuning_params:
            if param not in config["tuning"]:
                raise ValueError(
                    f"Eroor: {param} not defined in config.ini (section: tuning)"
                )

        for param in instance_params:
            if param not in config["instance"]:
                raise ValueError(
                    f"Eroor: {param} not defined in config.ini (section: instance)"
                )
    except Exception as e:
        raise

    #  convert functions
    convert_list = lambda type_, table: [
        type_(x) for x in table[1 : len(table) - 1].split(", ")
    ]
    convert_dict = lambda type_, table: {
        x.split(":")[0][1 : len(x.split(":")[0]) - 1]: type_(x.split(":")[1])
        for x in table[1 : len(table) - 1].split(", ")
    }
    convert_bool = lambda name: (
        True if name in ["true", "True", "on", "ON", "yes", "YES"] else False
    )

    tuning = dict(config.items("tuning"))
    instance = dict(config.items("instance"))
    # convert instances
    instance["ub_area"] = convert_list(float, instance["ub_area"])
    instance["lb_area"] = convert_list(float, instance["lb_area"])
    instance["ub_acell"] = convert_list(float, instance["ub_acell"])

    instance["vp"] = convert_bool(instance["vp"])
    instance["uniform_pup"] = convert_bool(instance["uniform_pup"])
    instance["variable_perm"] = convert_bool(instance["variable_perm"])
    instance["fixing_var"] = convert_bool(instance["fixing_var"])

    tuning["pressure_ratio"] = float(tuning["pressure_ratio"])
    tuning["epsilon"] = convert_dict(float, tuning["epsilon"])

    return tuning, instance


def execute(tuning, instance, my_solver, modelisation):
    if tuning["algo"] == "multistart":
        my_solver.multistart(
            modelisation, int(tuning.get("iteration")), int(tuning.get("seed1"))
        )

    elif tuning["algo"] == "mbh":
        my_solver.mbh(
            modelisation,
            int(tuning.get("max_trials")),
            int(tuning.get("max_no_improve")),
            int(tuning.get("seed1")),
            int(tuning.get("seed2")),
        )

    elif tuning["algo"] == "global_opt":
        my_solver.global_optimisation_algorithm(
            modelisation,
            int(tuning.get("max_trials")),
            int(tuning.get("max_no_improve")),
            int(tuning.get("iteration")),
            int(tuning.get("seed1")),
            int(tuning.get("seed2")),
        )

    elif tuning["algo"] == "genetic":
        my_solver.launching_evolutionary_algorithm(
            modelisation,
            int(tuning.get("pop_size")),
            int(tuning.get("generations")),
        )

    elif tuning["algo"] == "population":
        my_solver.launching_modified_evolutionary_algorithm(
            modelisation,
            instance["prototype_data"],
            int(tuning.get("n1_element")),
        )
    else:
        raise ValueError("Unknow algorithms")

    return my_solver, modelisation


def main():
    """Main launcher of our optimization software project."""
    args = parse_args()

    if args.verbose:
        # logging.basicConfig(level=logging.DEBUG)
        logging.basicConfig(level=logging.INFO)

    if args.config:
        logger.info("Generating config.ini ...")
        generate_configuration()
    else:
        # setting timer
        t_init = time.time()

        # Chosing the solver
        maxtime = args.maxtime or 180
        optsolver = SolverObject(maxtime)
        choice_of_solver = args.solver_name or "knitroampl_s"
        optsolver.solver_factory(solver_name=choice_of_solver, gams=args.gams)

        if args.exec:
            if args.instance_name:
                raise ValueError(
                    "Instance option must be deactivated when exec are provided"
                )

            logger.info("Loading config.ini ...")
            tuning, instance = load_configuration()
        else:
            logger.info("Loading use case instance ...")
            instance = data_instance(args.instance_name)
            tuning = tuning_param()

        if args.maxiter and isinstance(args.maxiter, int):
            tuning["iteration"] = str(args.maxiter)

        logger.info("Initializing process configuration ...")
        parameter = Configuration(
            num_membranes=int(instance["num_membranes"]),
            ub_area=instance["ub_area"],
            lb_area=instance["lb_area"],
            ub_acell=instance["ub_acell"],
            vp=instance["vp"],
            uniform_pup=instance["uniform_pup"],
            variable_perm=instance["variable_perm"],
            fixing_var=instance["fixing_var"],
            pressure_ratio=float(tuning["pressure_ratio"]),
            epsilon=tuning["epsilon"],
        )

        logger.debug(f"instance datafile {instance['fname']} loaded")

        # Creation of the model and it's instance
        # TODO: change the creation of the model here
        modelisation = build_model(
            parameter,
            instance["fname"],
            instance["fname_perm"],
            instance["fname_eco"],
            instance.setdefault("fname_mask", ""),
        )

        # pp.pprint(modelisation)
        # Instance of the solver which will execute the model
        my_solver = GlobalOptimisation(
            optsolver,
            instance["log_dir"],
            args.debug,
            not args.no_starting_point,
            not args.no_simplified_model,
        )

        tuning["algo"] = (
            "multistart"
            if args.algorithm_choice not in algorithms
            else args.algorithm_choice
        )

        logger.info(f"Executing {tuning['algo']} 's algorithm ...")

        my_solver, modelisation = execute(tuning, instance, my_solver, modelisation)

        if my_solver.feasible:
            print()
            printing_post_process_operation(
                modelisation.instance,
                modelisation.parameter,
                modelisation.obj_,
                args.capex,
                args.opex,
                args.save_log_sol,
            )

        # my_solver.modelisation.instance.write("fileNL.nl")
        # my_solver.modelisation.instance.pprint(isntance['f_log'])

        my_solver.print_statistics()
        t_end = time.time()
        print()
        logger.info("Tps execution = {}".format(t_end - t_init))

        # plotting solver optimization result if it exists
        if my_solver.feasible and args.visualise:
            my_solver.visualise_solutions(
                modelisation.instance, modelisation.parameter, True
            )
        elif my_solver.feasible:
            my_solver.visualise_solutions(
                modelisation.instance, modelisation.parameter, False
            )


if __name__ == "__main__":
    main()
