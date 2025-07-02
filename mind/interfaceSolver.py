"""SolverOject interface module."""

import sys
import os
import logging

import pyomo.environ as pe
from pyomo.opt import SolverStatus, TerminationCondition
from pyomo.common.errors import ApplicationError
import shutil

from mind.util import generate_absolute_path

# logging variable
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)
handler = logging.StreamHandler()
# handler = logging.FileHandler(filename)
logger.addHandler(handler)
formatter = logging.Formatter(fmt='[%(asctime)s] %(levelname)s : %(message)s',
                              datefmt='%a, %d %b %Y %H:%M:%S')
handler.setFormatter(formatter)

try:
    solver_utilities = generate_absolute_path() + "utilities" + os.path.sep
    sys.path.insert(0, solver_utilities)
except Exception as e:
    logger.warn("No utilities directory detected for solver definition")


class SolverObject:
    """Wrapper of `PYOMO`'s solver callback to solve `PYOMO`'s instance model.
    Attributes:

        the_solver (`Solver`) : `PYOMO`'s solver object

        solver_name (`str`) : name of solver

        is_gams_model (`Bool`) : `True` if `GAMS` 's modelizer is available

        tmp (`str`) : path to temporary directory

        options (`DICT`) : list of options to `PYOMO`'s solver when `GAMS`'s available
    """

    def __init__(self, maxtime=180):
        self.the_solver = None
        self.solver_name = None
        self.is_gams_model = False
        # self.results = None
        self.tmp = generate_absolute_path() + "tmp" + os.path.sep
        self.options = []
        self.maxtime = maxtime

    def solver_factory(self, solver_name='knitroampl', solver_path='', gams=False):
        """Construction of `PYOMO`'s solver instance.
        Args:

            solver_name (`str`) : name of solver

            gams (`Bool`) : `True` if `GAMS` 's modelizer is available (`default = False`)

            solver_path (`str`) : path to solver executable

        """
        logger.info("Creation of solver's object ...")
        self.is_gams_model = gams
        try:
            if solver_path:
                if self.is_gams_model:
                    self.the_solver = pe.SolverFactory(
                        'gams', executable=str(solver_path))
                else:
                    self.the_solver = pe.SolverFactory(
                        solver_name,
                        executable=str(solver_path),
                        solver_io='nl')
            else:
                if self.is_gams_model:
                    self.the_solver = pe.SolverFactory('gams')
                else:
                    self.the_solver = pe.SolverFactory(solver_name,
                                                       solver_io='nl')
        except Exception:
            logger.exception("Failed to create solver")
            raise
        else:
            self.solver_name = solver_name
            self.is_gams_model = (
                gams and self.the_solver.available(exception_flag=False))
            logger.info('Configuring solver options')
            if self.is_gams_model:
                self.options.append(f'option ResLim={self.maxtime};')
                self.options.append('option SysOut = On;')
            else:
                # For knitro initialize options before solve
                if self.solver_name.lower() == "knitroampl":
                    self.the_solver.options['presolve'] = 0
                    self.the_solver.options['outlev'] = 3
                    self.the_solver.options['outmode'] = 1
                    self.the_solver.options['maxtime_cpu'] = self.maxtime
                elif self.solver_name.lower() == "ipopt":
                    self.the_solver.options['max_cpu_time'] = self.maxtime
                # self.the_solver.options['presolve'] = 0
                # self.the_solver.options['outlev'] = 3
                # self.the_solver.options['outmode'] = 1
                # self.the_solver.options['maxtime_cpu'] = self.maxtime
                # self.the_solver.options['feastol'] = 1.0e-5 #added for test

    def call_solver(
            self,
            model,
            tee=False,
            logfile=None,
            load_solutions=True,
            keepfiles=False,
            # tmpdir=None,
            report_timing=False,
            exception_flag=True):
        """Callback to `PYOMO`'s solver instance to solve the model's instance.

        Args:

            model (`mind.system.MembranesDesignModel`) : model's instance

            tee (`Bool`) : `PYOMO`'s solver  tee parameter (`default = False`)

            logfile (`str`) : `PYOMO`'s solver exception_flag logfile (`default = None`)

            load_solutions (`str`) : `PYOMO`'s solver load_solutions parameter (`default = True`)

            keepfiles (`str`) : `PYOMO`'s solver keepfiles parameter (`default = False`)

            report_timing (`Bool`) : `PYOMO`'s solver report_timing parameter (`default = False`)

            exception_flag (`Bool`) : `PYOMO`'s solver exception_flag parameter (`default = True`)

        """
        # wrapper to solve model
        local_tee = tee
        local_logfile = logfile
        local_load_solutions = load_solutions
        local_keepfiles = keepfiles
        # local_tmpdir = tmpdir if tmpdir else self.tmp
        local_report_timing = report_timing
        try:
            if self.is_gams_model:
                local_logfile = logfile or 'gams.log'
                return self.the_solver.solve(
                    model,
                    tee=local_tee,
                    logfile=local_logfile,
                    load_solutions=local_load_solutions,
                    keepfiles=local_keepfiles,
                    # tmpdir=local_tmpdir,
                    report_timing=local_report_timing,
                    add_options=self.options,
                    warmstart=True,
                    solver=self.solver_name)
            else:
                return self.the_solver.solve(
                    model,
                    tee=local_tee,
                    logfile=local_logfile,
                    load_solutions=local_load_solutions,
                    keepfiles=local_keepfiles,
                    # tmpdir=local_tmpdir,
                    report_timing=local_report_timing)
        except ApplicationError as e:
            logger.error("ApplicationError: "
                         "(An exception used when "
                         "an external application generates an error)")

            logger.error(" ** Check Solver ({}) LICENCE **".format(
                self.solver_name))
            if not exception_flag:
                sys.exit(1)
            raise

    def check_solve_status(self, results):
        """Checking solver's resolution status.

        Args:

            results (`Pyomo 's results instance`) : results's object of solver

        """
        ok = (results.solver.status == SolverStatus.ok)
        opt_termination = results.solver.termination_condition == TerminationCondition.optimal
        local_termination = results.solver.termination_condition == TerminationCondition.locallyOptimal
        global_termination = results.solver.termination_condition == TerminationCondition.globallyOptimal

        final_result = (opt_termination or local_termination or
                        global_termination)

        return (ok and final_result)

    def print_log_to_file(self, file_path):
        """Print solver's logging into `file_path` .

        Args:

            file_path (`str`) : path to file to deverse logging information of solve's resolution

        """
        try:
            solver_log_file = 'knitro.log'
            if self.is_gams_model:
                if 'option SysOut = On;' in self.options:
                    if self.solver_name == 'knitroampl':
                        solver_log_file = 'knitro.log'
                        shutil.copyfile(solver_log_file, file_path)
                    else:
                        # TODO: Update solver_log_file
                        # solver_log_file = 'knitro.log'
                        # logger.info(
                        # "NOT IMPLEMENTED YET : solver_log file not identified"
                        # )
                        solver_log_file = 'gams.log'
                        shutil.copyfile(solver_log_file, file_path)
                        shutil.copyfile(solver_log_file, file_path)

            else:
                mode_1 = self.the_solver.options['outmode'] == 1
                mode_2 = self.the_solver.options['outmode'] == 2
                if (mode_1 or mode_2):
                    # save solver(knitro) log to another file
                    shutil.copyfile(solver_log_file, file_path)
        except Exception:
            logger.warn("Problem with solver_Log path")
