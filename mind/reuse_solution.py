""" Reusing solution or architecture.

loading a solution from ampl solution (respecting a file format).
storing a python solution to file, and routine to load it to pyomo instance.
"""

import logging

import pyomo.environ as pe

from mind.util import store_object_to_file, load_object_to_file
from mind.optmodel_utilities import initZero

# logging variable
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)
handler = logging.StreamHandler()
# handler = logging.FileHandler(filename)
logger.addHandler(handler)
formatter = logging.Formatter(fmt='[%(asctime)s] %(levelname)s : %(message)s',
                              datefmt='%a, %d %b %Y %H:%M:%S')
handler.setFormatter(formatter)


def get_from_file(file):
    """get the couple (idex, value) of a reading file line.

    Args:
        file (`_io.TextIOWrapper`) : opened file descriptor

    """
    line = file.readline()
    line = line.split()
    # print(line)
    # return float(line[-1])
    return (float(line[1]), float(line[3]))


def get_last_value_file_line(file):
    """get the last value of a reading file line.

    Args:
        file (`_io.TextIOWrapper`) : opened file descriptor

    """
    line = file.readline()
    line = line.split()
    return float(line[-1])


def load_generated_ampl(filename,
                        model,
                        parameter,
                        permeability_data,
                        perm_or_ret_choice="PERM"):
    """Load `AMPL` 's solution into our instance's model.

    Args:

        model (`mind.system.MembranesDesignModel`): design process model instance

        filename (`str`) : input file of `AMPL`'s solution

        parameter (`mind.builder.Configuration`) : design process configuration

        permeability_data (`DICT`) : permeability data information

        perm_or_ret_choice (`str`) : 'PERM' or 'RET' (`default = 'PERM'`)

    """
    # Laod ampl solution result in the pyomo model instance
    try:
        assert model.is_constructed()
    except Exception:
        logger.exception('Invalid pyomo model instance')
        raise

    try:
        assert parameter.uniform_pup
    except Exception:
        logger.exception("Invalid pressure's value : must be uniform")
        raise

    with open(filename, 'r') as file:
        file.readline()  # read text (number of membrane)
        # nb = int(get_last_value_file_line(file))
        get_last_value_file_line(file)

        file.readline()  # read text (membrane area)
        for mem in model.states:
            value = get_last_value_file_line(file)
            model.acell[mem].value = value
            # model.acell[mem].fixed = True

        file.readline()  # read blank lines
        file.readline()  # read text (pressure)
        model.pressure_up.value = get_last_value_file_line(file)
        for mem in model.states:
            value = get_last_value_file_line(file)
            model.pressure_down[mem].value = value

        file.readline()  # read blank lines
        file.readline()  # read text

        # Permeability
        if parameter.variable_perm:
            for mem in model.states:
                type_mem = model.mem_type[mem]
                model.Permeability[permeability_data[type_mem].ref_permeable,
                                   type_mem].value = get_last_value_file_line(
                                       file)

                model.Permeability[permeability_data[type_mem].other_permeable,
                                   type_mem].value = get_last_value_file_line(
                                       file)

                # can't load alpha (not a variable)
                file.readline()  # read text
        else:
            # permeability are fixed
            for j in model.components:
                get_last_value_file_line(file)

        file.readline()  # read BlankLine
        file.readline()  # read text

        for mem in model.states:
            value_1, value_2 = get_from_file(file)
            model.splitFEED[mem].value = value_1
            model.splitFEED_frac[mem].value = value_2

        for mem in model.states:
            value_1, value_2 = get_from_file(file)
            model.splitOutRET[mem].value = value_1
            model.splitOutRET_frac[mem].value = value_2

        for mem in model.states:
            value_1, value_2 = get_from_file(file)
            model.splitOutPERM[mem].value = value_1
            model.splitOutPERM_frac[mem].value = value_2

        for mem_1 in model.states:
            for mem_2 in model.states:
                value_1, value_2 = get_from_file(file)
                model.splitRET[mem_1, mem_2].value = value_1
                model.splitRET_frac[mem_1, mem_2].value = value_2

        for mem_1 in model.states:
            for mem_2 in model.states:
                value_1, value_2 = get_from_file(file)
                model.splitPERM[mem_1, mem_2].value = value_1
                model.splitPERM_frac[mem_1, mem_2].value = value_2

        file.readline()  # read BlankLine
        for mem in model.states:
            model.Feed_mem[mem].value = get_last_value_file_line(file)

        file.readline()  # read BlankLine
        for mem in model.states:
            for j in model.components:
                model.XIN_mem[mem, j].value = get_last_value_file_line(file)

        file.readline()  # read BlankLine
        for mem in model.states:
            model.Flux_RET_mem[mem].value = get_last_value_file_line(file)
        for mem in model.states:
            model.Flux_PERM_mem[mem].value = get_last_value_file_line(file)

        # updated format
        file.readline()  # read BlankLine
        file.readline()  # read text (Feed cell)

        for mem in model.states:
            for i in model.N:
                model.Feed_cell[mem, i].value = get_last_value_file_line(file)

        file.readline()  # read BlankLine
        file.readline()  # read text (Flux RET cell)
        for mem in model.states:
            for i in model.N:
                model.Flux_RET_cell[mem,
                                    i].value = get_last_value_file_line(file)

        file.readline()  # read BlankLine
        file.readline()  # read text (Flux PERM cell)
        for mem in model.states:
            for i in model.N:
                model.Flux_PERM_cell[mem,
                                     i].value = get_last_value_file_line(file)

        file.readline()  # read BlankLine
        file.readline()  # read text (Xin_cell)
        for mem in model.states:
            for j in model.components:
                for i in model.N:
                    model.XIN_cell[mem, j,
                                   i].value = get_last_value_file_line(file)

        file.readline()  # read text (X_RET_cell)
        for mem in model.states:
            for j in model.components:
                for i in model.N:
                    model.X_RET_cell[mem, j,
                                     i].value = get_last_value_file_line(file)

        file.readline()  # read text (X_PERM_cell)
        for mem in model.states:
            for j in model.components:
                for i in model.N:
                    model.X_PERM_cell[mem, j,
                                      i].value = get_last_value_file_line(file)

        file.readline()  # read BlankLine
        file.readline()  # read text (Feed mem)

        for mem in model.states:
            model.Feed_mem[mem].value = get_last_value_file_line(file)

        file.readline()  # read BlankLine
        file.readline()  # read text (x_ret_mem)

        for mem in model.states:
            for j in model.components:
                model.X_RET_mem[mem, j].value = get_last_value_file_line(file)

        file.readline()  # read BlankLine
        file.readline()  # read text (x_perm_mem)

        for mem in model.states:
            for j in model.components:
                model.X_PERM_mem[mem, j].value = get_last_value_file_line(file)

        file.readline()  # read BlankLine
        file.readline()  # read text (System output)
        # Carrefull in this part
        # for example outprod equivalent to perm in the case of CO2Capture
        # but it's ret in the case of N2Capture
        if perm_or_ret_choice == "RET":
            for j in model.components:
                model.XOUT_prod[j].value = get_last_value_file_line(file)

            file.readline()  # read BlankLine

            for j in model.components:
                model.XOUT_waste[j].value = get_last_value_file_line(file)

            file.readline()  # read BlankLine
            model.OUT_prod.value = get_last_value_file_line(file)
            model.OUT_waste.value = get_last_value_file_line(file)
        else:
            for j in model.components:
                model.XOUT_waste[j].value = get_last_value_file_line(file)

            file.readline()  # read BlankLine

            for j in model.components:
                model.XOUT_prod[j].value = get_last_value_file_line(file)

            file.readline()  # read BlankLine
            model.OUT_waste.value = get_last_value_file_line(file)
            model.OUT_prod.value = get_last_value_file_line(file)


def load_ampl_solution(my_solver, filename):
    """Load `AMPL` 's solution into our instance's model.

    Args:

        my_solver (`mind.solve.GlobalOptimisation`): design process's solver object

        filename (`str`) : input file of `AMPL`'s solution
    """
    # load via given file
    parameter = my_solver.modelisation.parameter
    model = my_solver.modelisation.instance
    permeability_data = my_solver.modelisation.permeability_data
    initZero(model)

    logger.info("Loading ampl data to pyomo instance ...")
    load_generated_ampl(filename, model, parameter, permeability_data)
    model.BalanceComponentMem_simplified.deactivate()
    model.mainEquationMem_simplified.deactivate()
    model.preprocess()
    # my_solver.try_something()   # model simplified
    # my_solver.feasible = my_solver.run_local_search()


def store_point_to_file(my_solver, filename="test.json"):
    """Store process design model instance to a file using `JSON`.

    Args:

        my_solver (`mind.solve.GlobalOptimisation`): design process's solver object

        filename (`str`) : output file to store object
    """
    logger.info(
        "Storing solution or architecture to file {}...".format(filename))
    parameter = my_solver.modelisation.parameter
    model = my_solver.modelisation.instance
    try:
        assert my_solver.feasible
    except Exception:
        logger.warn("Trying to store infeasible solution")
        logger.warn("Storing is aborted")
    else:
        solution = {}
        for var in model.component_data_objects(pe.Var):
            solution[parameter.labels[var]] = var.value

        store_object_to_file(solution, filename)


def load_file_solution(my_solver, filename="test.json"):
    """Load process design model instance from a file using `JSON`.

    Args:

        my_solver (`mind.solve.GlobalOptimisation`): design process's solver object

        filename (`str`) : input file to load object
    """
    logger.info(
        "Loading solution or architecture from file {} ...".format(filename))
    # parameter = my_solver.modelisation.parameter
    model = my_solver.modelisation.instance
    solution = {}

    load_object_to_file(solution, filename)

    # Loading solution (tyoe dict) to model (Pyomo instance)
    try:
        for cuid, val in solution.items():
            model.find_component(cuid).value = val
    except Exception:
        logger.error(
            "Error when loading solution, are all variables name defined")
