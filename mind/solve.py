"""Describing solving's algorithm for optimization problems."""

import random
import time
import os
import logging
import copy

import pyomo.environ as pe
from pyomo.opt import SolverStatus, TerminationCondition
import pyutilib.subprocess.GlobalData as GlobalData

from mind.builder import build_model
from mind.genetic import Population
from mind.printing import print_model_solution, plotting_solution
from mind.population import PopAlgortihm
from mind.random_initialisation import random_generation, \
    Perturbation_membranes, initCells
from datetime import datetime

GlobalData.DEFINE_SIGNAL_HANDLERS_DEFAULT = False
# logging variable
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)
handler = logging.StreamHandler()
# handler = logging.FileHandler('log.txt')
logger.addHandler(handler)
formatter = logging.Formatter(fmt='[%(asctime)s] %(levelname)s : %(message)s',
                              datefmt='%a, %d %b %Y %H:%M:%S')
handler.setFormatter(formatter)


class GlobalOptimisation:
    """Design process optimization solver.

    Attributes:

        optsolver (`pyomo.solver`): `PYOMO`'s solver istance.

        nb_point (`Int`) : number of feasible point found during localsearh

        no_improve (`Int`) : number of non imprevement during `mbh`

        nloc (`Int`) : number of localsearch on original model

        nloc_simpl (`Int`) : number of localsearch on simplified model

        n_unfeas (`Int`) : number of unfeasible solution on original model resolution

        n_unfeas_simpl (`Int`) : number of unfeasible solution on simplified model resolution

        solver_result_simpl (`str`) : simplified model execution status summary

        solver_result (`str`) : model execution status summary

        solver_result_small (`str`) : execution status summary

        random_generationMulti (`Random`) : random object used to generate initial  values to variables

        random_generationPert (`Random`) : random object used in solution perturbation

        active_generationMulti (`Bool`) : `True` if random's object `random_generationMulti` is initialized

        active_generationPert  (`Bool`) : `True` if random's object `random_generationPert` is initialized

        fputative (`Float`): Value of best objective function finded (`default = 1e6`)

        tol (`Float`): tolerance over which a new solution is better than the old one (`default = 1e6`).

        debug_mode (`Bool`) : `True` if debug option is active (`default = False`)

        start_point_flag (`Bool`) : `True` if starting point are generated
        by this solver object and `False` if Pyomo's solver do it on it's own (`default = True`)

        simplified_flag (`Bool`) : `True` if simplified model are executed
        during desing process's solve (`default = True`)


        log_dir (`str`) : path to log directory of the project

        logfile (`str`) : path to `log.txt` in which we store starting point values

        stationaryfile (`str`) : path to `stationary.txt` in which we store feasible solution

        bestfile (`str`) : path to `bestfile.txt` in which we store best feasible solution

        feasible (`Bool`) : `True` if design process's solver find a feasible solution

        Z_point (`DICT`): data structure used to store association of variables and values

        putative_solution (`Float`): data structure used to store best solution obtained

        keep_sols (`Bool`) : list used to keep trace of feasible solution

        evolutionary_algorithm (`Bool`): `True` if evolutionary algorithm's used.
    """

    def __init__(self,
                 optsolver,
                 log_dir,
                 debug=False,
                 starting_point=True,
                 simplified_model=True):
        """Initializing solver resolution caller object."""
        logger.info(
            'Creation of an instance of solver class, module for optimization')
        self.optsolver = optsolver
        self.nb_point = 0
        self.no_improve = 0
        self.nloc = 0
        self.nloc_simpl = 0
        # self.nloc_small = 0
        self.n_unfeas = 0
        self.n_unfeas_simpl = 0
        # solver results for the 3 optimization steps
        # to be used at the place of summary
        self.solver_result_simpl = " "
        self.solver_result = " "
        self.solver_result_small = " "
        # Random object
        self.random_generationMulti = random.Random()
        self.random_generationPert = random.Random()
        self.active_generationMulti = False
        self.active_generationPert = False
        # putative global optimum value
        self.fputative = 10e6
        # tolerance to be used for comparisons between the best values
        self.tol = 1.e-6
        self.debug_mode = debug
        self.start_point_flag = starting_point
        self.simplified_flag = simplified_model

        # # TODO: close these files
        self.log_dir = log_dir
        self.logfile = open(self.log_dir + 'log.txt', 'w')
        self.stationaryfile = open(self.log_dir + 'stationarypoints.txt', 'w')
        self.bestfile = open(self.log_dir + 'bestpoints.txt', 'w')

        # self.active = False
        # indicate if fonded a solution during exploration
        self.feasible = False
        # Current point
        self.Z_point = {}
        self.putative_solution = {}
        # keep obtained solution (just objective function value)
        self.keep_sols = []

        # population component
        self.evolutionary_algorithm = None

    def init_independant_variables(self, modelisation):
        """Generate random values for independant variables in the model.

        These variables are related  to global system and membranes
        stage level.

        Args:

            modelisation (`mind.system.MembranesDesignModel`) : desing process model
        """
        my_model = modelisation.instance
        my_param = modelisation.parameter
        logger.info('Random value generations for dependents variables')
        random_generation(my_model, self.random_generationMulti, my_param,
                          modelisation.membrane_behavior,
                          modelisation.mask_filename)
        
        self.logfile.write("Random generated point\n")
        print_model_solution(my_model, self.logfile, my_param,
                             modelisation.membrane_behavior)
        self.logfile.flush()

    # solve reduced problem with total area (like a single large cell)
    def solve_simplified_model(self, modelisation):
        """Callback to solve simplified model.

        Args:

            modelisation (`mind.system.MembranesDesignModel`) : desing process model

        """
        logger.info('Launching Simplified model')
        my_model = modelisation.instance
        modelisation.simplified_model()
        # then solve this model
        if self.debug_mode:
            results = self.optsolver.call_solver(my_model,
                                                 keepfiles=True,
                                                 load_solutions=False,
                                                 tee=True)

        else:
            results = self.optsolver.call_solver(
                my_model,
                load_solutions=False,
            )

        # print expression
        # self.print_expression("simplified")
        file_path = (self.log_dir + "solver" + os.path.sep + "nloc_simpl" +
                     str(self.nloc_simpl) + ".log")
        self.optsolver.print_log_to_file(file_path)

        if self.optsolver.check_solve_status(results):
            # Solution is optimal
            self.nloc_simpl += 1
            my_model.solutions.load_from(results)
            logger.info('Get Optimal solution when running simplified model')
            self.solver_result_simpl = "LS_simpl OPT"
        else:
            # simplied model resolution return infeasible
            self.n_unfeas_simpl += 1

            self.solver_result_simpl = (
                "LS_simpl " + str(results.solver.termination_condition))
            logger.info(
                'Get infeasible solution when running simplified model - [%s, %s]',
                str(results.solver.termination_condition),
                results.solver.termination_condition)

        # Restore the original method
        modelisation.restore_original_model()

    def deduce_dependant_variables(self, my_model, my_param):
        """Deduce some values (random) to dependent varaibles.

        These varaibles are variable related  to cells stage level.

        Args:

            my_model (`mind.system.MembranesDesignModel`) : desing process model's instance

            my_parma (`mind.builder.Configuration`) : desing process configuration
        """
        logger.info('Deduction of independents variables (related to cells)')
        # init cell variables
        initCells(my_model, my_param)

    def construct_starting_point(self, modelisation):
        """Generate randomly starting point.

        Point obtained is not necessarily feasible.

        Args:

            modelisation (`mind.system.MembranesDesignModel`) : desing process model

        """
        if self.start_point_flag:
            self.init_independant_variables(modelisation)

            if self.simplified_flag:
                self.solve_simplified_model(modelisation)
                self.deduce_dependant_variables(modelisation.instance,
                                            modelisation.parameter)

    def run_local_search(self, my_model):
        """Run local searh on the current model.

        Args:

            my_model (`mind.system.MembranesDesignModel`) : desing process model's instance

        Returns:
                bool: True if feasible point obtained, False otherwise.
        """

        logger.info(
            'Running localSearch around the current starting  point ...')
        t_i = time.time()
        if self.debug_mode:
            results = self.optsolver.call_solver(my_model,
                                                 keepfiles=True,
                                                 load_solutions=False,
                                                 tee=True)

        else:
            results = self.optsolver.call_solver(
                my_model,
                load_solutions=False,
            )
        t_e = time.time()

        logger.info("LocalSearch time = {}".format(t_e - t_i))

        # check alway solutions (solver status) befoore loading it
        self.nloc += 1

        file_path = (self.log_dir + "solver" + os.path.sep + "nloc_" +
                     str(self.nloc) + ".log")
        self.optsolver.print_log_to_file(file_path)

        if self.optsolver.check_solve_status(results):
            # Load solution into results object
            my_model.solutions.load_from(results)
            feasible = True
            self.solver_result = "LS  OPT "
            logger.info("Optimal localSearch - [obj function = %f]",
                        my_model.obj())
        else:
            logger.info(
                'Solver localSearch return [status : %s] and [TerminationCondition : %s] ',
                results.solver.status, results.solver.termination_condition)
            logger.info("Infeasible localSearch")

            feasible = False
            self.n_unfeas += 1

            self.solver_result = " LS " + \
                str(results.solver.termination_condition) + " "

        # overall feasibility status of the solution
        return feasible

    # Save your model before the perturbation process
    def perturb_solution(self, modelisation):
        """Perturb current feasible solution.

        This function overwrite the current solution by the perturbated one.

        Args:

            modelisation (`mind.system.MembranesDesignModel`) : desing process model

        """

        my_model = modelisation.instance
        my_param = modelisation.parameter

        # try:
        #     assert self.feasible
        # except Exception:
        #     logger.exception('Perturbing infeasible solution is not allowed')
        #     raise

        # my_model will be perturbed
        self.store_model_to_point(my_model, my_param)
        # then keep or save the values of actual model in a dict
        saved_model_value = dict(self.Z_point)
        # TODO: handle case with mutltiple membranes
        Perturbation_membranes(my_model, saved_model_value,
                               self.random_generationPert, my_param,
                               modelisation.membrane_behavior,
                               modelisation.mask_filename)
        if self.simplified_flag:
            self.solve_simplified_model(modelisation)
            self.deduce_dependant_variables(modelisation.instance,
                                            modelisation.parameter)

    def save_solution(self,
                      modelisation,
                      algo_identifier_str="",
                      mbh_function=False):
        """Save model's instance solution to logs.

        Args:

            modelisation (`mind.system.MembranesDesignModel`) : desing process model

            algo_identifier_str (`str`) : algorithm identifier

            mbh_function (`Bool`) : `True` if `mbh` is used
        """
        f_current = modelisation.instance.obj()
        self.feasible = True

        # Variable stating if improving or not
        improving = False

        if f_current in self.keep_sols:
            logger.info("get redundant point")
            self.no_improve = self.no_improve + 1 if mbh_function else self.no_improve
        else:
            # New solution found
            self.nb_point += 1
            logger.info("New point obtained")
            self.keep_sols.append(f_current)

            # Check improvement on objective function value
            if f_current < (self.fputative - self.tol):
                logger.info("Improvement on putative")
                improving = True
                self.update_putative(modelisation, f_current)
                self.store_solution(modelisation, f_current, self.bestfile,
                                    algo_identifier_str, mbh_function,
                                    improving)

                self.no_improve = 0 if mbh_function else self.no_improve

        # save solution in stationaryfile file
        self.store_solution(modelisation, f_current, self.stationaryfile,
                            algo_identifier_str, mbh_function, improving)

        logger.info("obtained solution, saved in stationaryfile")

    def find_starting_solution(self,
                               modelisation,
                               max_trials_starting_points=1):
        """ Constructing starting point max_trials times.

        Args:

            modelisation (`mind.system.MembranesDesignModel`) : desing process model

            max_trials_starting_points (`Int`) : number of iteration or
            time trying to find starting solution (`default = 1`)
        """
        feasible = False
        trials = 1
        while not feasible and trials <= max_trials_starting_points:
            print("\t-----")
            logger.info("starting point : trial {}".format(trials))
            self.construct_starting_point(modelisation)

            feasible = self.run_local_search(modelisation.instance)
            trials += 1
        if feasible:
            self.save_solution(modelisation,
                               algo_identifier_str="Starting point")

        logger.info("feasible = %s", feasible)
        return feasible

    def multistart(self, modelisation, nb_points_randomized, seed=1):
        """A metaheuristic to find feasible solution
        using a non linear solver. It consist to generate some
        starting point and doing local searh around them. The best solution
        is keeped as `f_putative` value.

        Args:

            modelisation (`mind.system.MembranesDesignModel`) : desing process model

            nb_points_randomized (`Int`): number of starting points to generate

            seed (`Int`): random seed (`default = 1`)

        Returns:
                bool: `True` if feasible point found during iterations,
                    False otherwise.

        """
        # pre-condition : there are no solution in the model yet
        # post-condition : function return true if feasible solution found

        # add an default argument which will take acount if pre-condition
        # TODO: parallel multistart : in this case, you must remove
        # construction method and simplified model

        my_model = modelisation.instance
        my_param = modelisation.parameter
        if not self.active_generationMulti:
            self.random_generationMulti.seed(seed)
            self.active_generationMulti = True

        # Multistart
        for i in range(1, nb_points_randomized + 1):
            # TODO: while feas trials
            logger.info('')
            logger.info("Multistart iteration {}".format(i))
            self.construct_starting_point(modelisation)

            feasible = self.run_local_search(modelisation.instance)

            if feasible:
                self.save_solution(modelisation,
                                   algo_identifier_str="Multistart")
            else:
                # No feasible solution found for a my_model
                # logger.info("model infeasible")
                None
        # Restore the best solution found, function 'll return with this contex
        self.restore_model_from_point(my_model)
        # return random_generationMulti.getstate()
        return self.feasible

    def mbh(self,
            modelisation,
            max_trials_starting_points,
            max_no_improve,
            seed1=1,
            seed2=1,
            given_starting_point=False):
        """A metaheuristic to find feasible solution
        using a non linear solver. It consist to perturb a feasible solution
        and search around perturbated solution for better points. The best
        solution is keeped as `f_putative` value.

        Args:

            modelisation (`mind.system.MembranesDesignModel`) : desing process model

            max_trials_starting_points (`Int`): maximal number of trials
                needed to generate starting point. If no feasible point got
                before this maximum value, then the iteration is interrupted.

            max_no_improve (`Int`): Terminaison condition of `mbh`

            seed1 (`Int`): random seed for `random_generationMulti`

            seed2 (`Int`): random seed for `random_generationPert`

        Returns:
                bool: `True` if feasible point found during iterations,
                    False otherwise.

        """
        # pre-condition : there are no solution in the model yet
        # post-condition : function return true if feasible solution found

        my_model = modelisation.instance
        my_param = modelisation.parameter
        i = 0
        self.no_improve = 0
        if not self.active_generationMulti:
            self.random_generationMulti.seed(seed1)
            self.active_generationMulti = True
        if not self.active_generationPert:
            self.random_generationPert.seed(seed2)
            self.active_generationPert = True
        # Generate the centrer point x_0 :
        t_init_iter = time.time()
        feasible = False
        if not given_starting_point:
            # generate starting point
            # (if not feasible, iterate until max_tials)
            feasible = self.find_starting_solution(modelisation,
                                                   max_trials_starting_points)

        else:
            # by given solution, we affirm that
            feasible = True

        if feasible:
            # MBH outer iteration loop
            # while (mbhIter < max_trials_starting_points
            #        and i < 10*max_trials_starting_points):

            # logger.info("\t  |")
            # logger.info("\t  |")
            # logger.info("\t  |")
            while (self.no_improve < max_no_improve):
                i += 1
                logger.info('')
                logger.info("MBH iteration {}".format(i))
                # Perturb the current local optimum
                self.perturb_solution(modelisation)
                feasible = self.run_local_search(modelisation.instance)
                # # TODO: find a way to find allway feasible point

                if feasible:
                    # the perturbed solution is feasible
                    self.save_solution(modelisation, "IMP MBH", True)
                    f_current = modelisation.instance.obj()
                    if f_current >= (self.fputative - self.tol):
                        # Feasible solution but not an Improvement
                        logger.info("No improvement on putative")
                        # restore a centrer point and continues iteration
                        self.restore_model_from_point(modelisation.instance)
                        self.no_improve = self.no_improve + 1

                else:
                    # the perturbed solution is not feasible
                    # retore the old or center point
                    self.restore_model_from_point(my_model)
                    self.no_improve += 1
        else:
            logger.info(
                "No feasible starting point obtained in max trials time")
        # At the end, return True if we get a feasible solution
        t_end_iter = time.time()
        logger.info("Tps for iteration = {}".format(t_end_iter - t_init_iter))
        # return random_generationMulti.getstate()
        return self.feasible

    def global_optimisation_algorithm(self, modelisation,
                                      max_trials_starting_points,
                                      max_no_improve, nb_points_randomized,
                                      seed1, seed2):
        """A metaheuristic to find feasible solution
        using a non linear solver. It consist to generate some feasible
        starting point and perturb. Then, local searh are performed around
        perturbated solution. The best solution found during iteration are keep
        as `f_putative` value.

        Args:
            modelisation (`mind.system.MembranesDesignModel`) : desing process model

            max_trials_starting_points (`Int`): maximal number of trials

            max_no_improve (`Int`): Terminaison condition of `mbh`

            nb_points_randomized (`Int`): number of starting points to generate
                needed to generate starting point. If no feasible point got
                before this maximum value, then the iteration is interrupted.

            seed1 (`Int`): random seed for `random_generationMulti`

            seed2 (`Int`): random seed for `random_generationPert`

        Returns:
                bool: `True` if feasible point found during iterations,
                    False otherwise.

        """

        # my_model = modelisation.instance
        # my_param = algorithm_search.modelisation.parameter
        # maxfeastrials = 10

        if not self.active_generationMulti:
            self.random_generationMulti.seed(seed1)
            self.active_generationMulti = True
        if not self.active_generationPert:
            self.random_generationPert.seed(seed2)
            self.active_generationPert = True

        # Multistart
        for t in range(1, nb_points_randomized + 1):
            print("-------------------------------------")
            logger.info("Global optimization iteration {}".format(t))
            print("-------------------------------------")
            # construct x_t_start
            feasible = self.find_starting_solution(modelisation,
                                                   max_trials_starting_points)

            if feasible:
                # Call mbh function
                # TODO: extract parameter random object
                self.mbh(modelisation,
                         max_trials_starting_points,
                         max_no_improve,
                         seed1,
                         seed2,
                         given_starting_point=True)

                # comparison with putative are done in mbh
            else:
                logger.info("No feasible starting point obtained")

        # Restore the best solution found, function 'll return with this contex
        self.restore_model_from_point(modelisation.instance)
        # return random_generationMulti.getstate()
        return self.feasible

    def store_model_to_point(self, model, parameter):
        """Store the current model.

        This function is called when a solution is feasible and generaly if
        it's better than existing solution stored in point `Z_point`.

        Args:
            model (`mind.system.MembranesDesignModel`) : design process model's instance

            parameter (`mind.builder.Configuration`) : design process configuration
        """
        self.Z_point = {}
        for var in model.component_data_objects(pe.Var):
            # logger.info('variable %s', var)
            self.Z_point[parameter.labels[var]] = var.value

    def restore_model_from_point(self, model, putative=False):
        """Restore the model with values in `z.point`.

        Args:
            model (`mind.system.MembranesDesignModel`) : design process model's instance

            putative (`Float`) : best objective's function value found
        """
        except_cuid = None
        except_val = None
        try:
            """ Loading the solution keeped.
            from attribute z.point to the model."""
            if putative:
                for cuid, val in self.putative_solution.items():
                    model.find_component(cuid).value = val
            else:
                for cuid, val in self.Z_point.items():
                    except_cuid = cuid
                    except_val = val
                    # logger.info("identifier = %s and value = %s", cuid, val)
                    model.find_component(cuid).value = val
        except Exception:
            print(except_cuid)
            print(except_val)
            logger.warn("No value saved "
                        ": resolution method failed to find a solution ")
            raise

    def print_statistics(self):
        """Print statistics informations after execution.

        Notes:
            - `nb_point`
            - `nloc_simpl`
            - `self.nloc`
            - `n_unfeas_simpl`
            - `n_unfeas`
        """
        print()
        # TODO: nb_point stated it correctly
        logger.info("Number solutions found (without redundancy) :  {}".format(
            self.nb_point))
        logger.info("Number of local search on simplied model:  {}".format(
            self.nloc_simpl))
        logger.info("Number of local search :  {}".format(self.nloc))
        logger.info(
            "Number of unfeasible solution on simplied model :  {}".format(
                self.n_unfeas_simpl))
        logger.info("Number of unfeasible solution:  {}".format(self.n_unfeas))

    def update_putative(self, modelisation, f_current):
        """Update the value of best know objective function.

        Args:

            modelisation (`mind.system.MembranesDesignModel`) : design process model

            f_current (`Float`) : value of the current objective function
        """

        logger.info("Last obj value = {} ---> New obj value = {}".format(
            self.fputative, f_current))

        self.fputative = f_current
        # We get a new centrer point, then store it
        self.store_model_to_point(modelisation.instance, modelisation.parameter)
        self.putative_solution = dict(self.Z_point)

    def store_solution(self,
                       modelisation,
                       f_current,
                       my_file,
                       algo_identifier_str,
                       mbh_function=False,
                       improving=False):
        """Store also some informations about this solution in a file.

        Args:
            modelisation (`mind.system.MembranesDesignModel`) : membrane design
            process's model object

            f_current (float) : Value of the current objective function

            my_file (_io.TextIOWrapper) : output file to store solution

            algo_identifier_str (str) : identifier of solving's algorithm.

            mbh_function (Bool) : `True` if mbh's algorithm used.
        """

        obj_str = "obj = {}".format(f_current)
        localsolve_str = "local solve = {},".format(self.nloc)
        improving_msg = "improving = {},".format(improving)

        if mbh_function:
            no_improve_str = "No improve = {},".format(self.no_improve)

        else:
            no_improve_str = ""

        my_file.write(algo_identifier_str + ": {" + localsolve_str + " " +
                      no_improve_str + " " + improving_msg + " " + obj_str +
                      "}\n")

        print_model_solution(modelisation.instance, my_file,
                             modelisation.parameter,
                             modelisation.membrane_behavior, True)
        my_file.flush()

    def visualise_solutions(self, model, parameter, plotting=False):
        """Callback funcion to plotting the resulting optimization process.

        Args:

            model (`mind.system.MembranesDesignModel`) : design process model's instance

            parameter (`mind.builder.Configuration`) : design process configuration

            plotting (`Bool`) : `True` if showing plot in screen (`default = False`)
        """
        try:
            assert self.feasible
            plotting_solution(model, parameter, plotting)

        except ValueError:
            logger.exception(
                'Problem for visualising solution : check if solution is valid')
            raise

        except Exception:
            logger.exception('Visualising infeasible solution is not allowed')
            raise

    def print_expression(self, model, text):
        """Print constraint expression into `simpl_expr.log`.

        Args:

            model (`mind.system.MembranesDesignModel`) : design process model's instance

            text (`str`) : identifier

        """
        i = 0
        j = 0
        if text == "simplified":
            filename_simpl = self.log_dir + 'simpl_expr.log'
            outfile_simpl = open(filename_simpl, 'w')
            for ctr in model.component_data_objects(ctype=pe.Constraint,
                                                    active=True):
                j += 1
                outfile_simpl.write(ctr.name + "\n")
                #
                # outfile_simpl.write(
                #     ctr.name
                #     + ": "
                #     + "\t"
                #     + str(ctr.expr)
                #     + "\n"
                # )

            print("nb constraint = ", j)

            # for var in model.component_data_objects(ctype=pe.Var, active=True):
            #     if not "_cell" in str(var):
            #         outfile_simpl.write(
            #             str(var)
            #             + " = "
            #             + str(var.value)
            #             + "\n"
            #         )
            #
            #         i += 1
            #
            # print("nb variables = ", i)
        else:
            filename_original = self.log_dir + 'original_expr.log'
            outfile_original = open(filename_original, 'w')
            for ctr in model.component_data_objects(ctype=pe.Constraint,
                                                    active=True):
                j += 1
                outfile_original.write(ctr.name + " : \t" + str(ctr.expr) +
                                       "\n")
                # outfile_original.write(
                #     ctr.name
                #     + ": "
                #     + "\t"
                #     + str(ctr.expr)
                #     #+ "\t"
                #     #+ str(ctr.rhs)
                #     + "\n"
                # )

            print("nb constraint = ", j)

            # for var in model.component_data_objects(ctype=pe.Var, active=True):
            #     if not "_cell" in str(var):
            #         outfile_original.write(
            #             str(var)
            #             + " = "
            #             + str(var.value)
            #             + "\n"
            #         )
            #
            #         i += 1
            #
            # print("nb variables = ", i)

    def launching_evolutionary_algorithm(self,
                                         modelisation,
                                         pop_size,
                                         generations=10):
        """Launching genetic evolutionary algorithm.

        Args:

            modelisation (`mind.system.MembranesDesignModel`) : design process model

            pop_size (`str`) : population size

            generations (`Int`) : number of generations to create
        """

        if self.evolutionary_algorithm is None:
            self.evolutionary_algorithm = Population(self, modelisation)
        self.evolutionary_algorithm.run(pop_size, generations)

    def launching_modified_evolutionary_algorithm(self, modelisation,
                                                  instance_file, n1_element):
        """Launching modified evolutionary algorithm.

        Args:

            modelisation (`mind.system.MembranesDesignModel`) : design process model

            instance_file (`str`) : path to instance datafile

            n1_element (`Int`) : number of population list handled.
        """
        if self.evolutionary_algorithm is None:
            self.evolutionary_algorithm = PopAlgortihm(self, instance_file)
        self.evolutionary_algorithm.run(modelisation, n1_element)
        # TODO: delete below line
        self.feasible = False

    def create_new_model(self, parameter):
        """Create of model with different number of membranes.

        Args:

            parameter (`mind.builder.Configuration`) : design process configuration
        """
        if parameter.num_membranes == 1:
            param_2 = copy.deepcopy(parameter)
            param_2.num_membranes = 2
            param_2.lb_acell = [parameter.lb_acell[0]] * 2
            param_2.ub_acell = [parameter.ub_acell[0]] * 2
            param_2.discretisation = [parameter.discretisation[0]] * 2
            self.two_mem = build_model(param_2, modelisation.filename,
                                       modelisation.perm_filename,
                                       modelisation.eco_filename)

            param_3 = copy.deepcopy(parameter)
            param_3.num_membranes = 3
            param_3.lb_acell = [parameter.lb_acell[0]] * 3
            param_3.ub_acell = [parameter.ub_acell[0]] * 3
            param_3.discretisation = [parameter.discretisation[0]] * 3
            self.three_mem = build_model(param_3, modelisation.filename,
                                         modelisation.perm_filename,
                                         modelisation.eco_filename)

        elif parameter.num_membranes == 2:
            param_1 = copy.deepcopy(parameter)
            param_1.num_membranes = 1
            param_1.lb_acell = [parameter.lb_acell[0]] * 1
            param_1.ub_acell = [parameter.ub_acell[0]] * 1
            param_1.discretisation = [parameter.discretisation[0]] * 1
            self.one_mem = build_model(param_1, modelisation.filename,
                                       modelisation.perm_filename,
                                       modelisation.eco_filename)

            param_3 = copy.deepcopy(parameter)
            param_3.num_membranes = 3
            param_3.lb_acell = [parameter.lb_acell[0]] * 3
            param_3.ub_acell = [parameter.ub_acell[0]] * 3
            param_3.discretisation = [parameter.discretisation[0]] * 3
            self.three_mem = build_model(param_3, modelisation.filename,
                                         modelisation.perm_filename,
                                         modelisation.eco_filename)
        elif parameter.num_membranes == 3:
            param_1 = copy.deepcopy(parameter)
            param_1.num_membranes = 1
            param_1.lb_acell = [parameter.lb_acell[0]] * 1
            param_1.ub_acell = [parameter.ub_acell[0]] * 1
            param_1.discretisation = [parameter.discretisation[0]] * 1
            self.one_mem = build_model(param_1, modelisation.filename,
                                       modelisation.perm_filename,
                                       modelisation.eco_filename)

            param_2 = copy.deepcopy(parameter)
            param_2.num_membranes = 2
            param_2.lb_acell = parameter.lb_acell * 2
            param_2.ub_acell = parameter.ub_acell * 2
            param_2.discretisation = [parameter.discretisation[0]] * 2

            self.two_mem = build_model(param_2, modelisation.filename,
                                       modelisation.perm_filename,
                                       modelisation.eco_filename)
        else:
            param_1 = copy.deepcopy(parameter)
            param_1.num_membranes = 1
            param_1.lb_acell = parameter.lb_acell * 1
            param_1.ub_acell = parameter.ub_acell * 1
            param_1.discretisation = [parameter.discretisation[0]] * 1
            self.one_mem = build_model(param_1, modelisation.filename,
                                       modelisation.perm_filename,
                                       modelisation.eco_filename)

            param_2 = copy.deepcopy(parameter)
            param_2.num_membranes = 2
            param_2.lb_acell = parameter.lb_acell * 2
            param_2.ub_acell = parameter.ub_acell * 2
            param_2.discretisation = [parameter.discretisation[0]] * 2
            self.two_mem = build_model(param_2, modelisation.filename,
                                       modelisation.perm_filename,
                                       modelisation.eco_filename)

            param_3 = copy.deepcopy(parameter)
            param_3.num_membranes = 3
            param_3.lb_acell = parameter.lb_acell * 3
            param_3.ub_acell = parameter.ub_acell * 3
            param_3.discretisation = [parameter.discretisation[0]] * 3
            self.three_mem = build_model(param_3, modelisation.filename,
                                         modelisation.perm_filename,
                                         modelisation.eco_filename)

        # boolean variable which means that 1, 2 and 3 mem models are created
        self.model_created = True

    def change_model(self, modelisation, nb_membrane=2):
        """Change model.

        Args:

            modelisation (`mind.system.MembranesDesignModel`) : design process model

            nb_membrane (`Int`) : number of membrane
        """
        try:
            assert self.model_created
        except Exception:
            logger.warn("Create models for 1, 2 and 3 membranes")
            self.create_new_model()

        old_modelisation = modelisation
        old_modelisation_point = self.Z_point
        try:
            if nb_membrane == 1:
                modelisation = self.one_mem
            elif nb_membrane == 2:
                modelisation = self.two_mem
            else:
                modelisation = self.three_mem
        except Exception:
            logger.warn(
                "Problem in loading new model with nb_membrane = {}".format(
                    nb_membrane))
        else:
            # modify z.point
            self.Z_point = {}

        return (old_modelisation, old_modelisation_point)
