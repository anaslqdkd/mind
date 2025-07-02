"""Solve optimization problem with polpulation methode."""

import os
import pprint
import copy
import logging

import yaml
import pyomo.environ as pe

from mind.builder import Configuration, build_model
from mind.fixing import fixing_method
from mind.util import generate_absolute_path

# logging variable
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)
handler = logging.StreamHandler()
# handler = logging.FileHandler('log.txt')
logger.addHandler(handler)
formatter = logging.Formatter(fmt='[%(asctime)s] %(levelname)s : %(message)s',
                              datefmt='%a, %d %b %Y %H:%M:%S')
handler.setFormatter(formatter)


class Individu:
    """Description of genetic population's individual.
        Attributes:

            modelisation(`mind.system.MembranesDesignModel`) : design process model.

            fixing (`DICT`) : associative data structure containing
            informations on variables to be fixed

            active (`Bool`) : `True` if current individual is a feasible solution

            index_family (`Int`) : Identifier of individual

            fixed_value (`Bool`) : `True` if some variables must be fixed for individual

            init_file (`str`) : filename containing information
            on variables to be fixed for individual

            rank (`Int`) : rank of individual in the population when
            sorting needed

            period (`Int`) : number of period passed without upgrading
            solution of this `family_index`

            model_value (`DICT`) : associative data structure containing
            pair of models' variables and it's values

            obj (`Float`) : objective's function value of current individual
    """

    def __init__(self,
                 modelisation,
                 fixing,
                 index_family,
                 active=False,
                 rank=None):
        """ initialisation of individual."""
        self.modelisation = modelisation
        self.fixing = fixing
        self.index_family = index_family
        self.active = active
        self.rank = rank
        self.period = 0
        self.model_value = {}
        self.obj = None

    def __str__(self):
        return (
            "Individu_{} \t nb_membrane:{} \t nb_variables:{} \t active: {} "
            "\t epoq:{} \t out_prod:{} \t out_waste:{} \t obj:{}".format(
                self.index_family, self.modelisation.parameter.num_membranes,
                len(self.model_value), self.active, self.period,
                round(self.modelisation.instance.OUT_prod.value, 3),
                round(self.modelisation.instance.OUT_waste.value, 3), self.obj))

    def fixing_variable(self):
        """Fixing some variables according to the `fixing` dictionary."""
        try:
            if self.fixing:
                # print("here voila ", self.fixing)
                for k, v in self.fixing.items():
                    self.modelisation.instance.find_component(k).value = v
                    self.modelisation.instance.find_component(k).fixed = True
        except Exception as e:
            logger.exception("Not enable to fix variables")
            raise

    def storing_model_values(self, solver):
        """Store optimization model's instance status.

        Args:

            solver (`mind.solve.GlobalOptimisation`) : design process's solver
        """
        solver.store_model_to_point(self.modelisation.instance,
                                    self.modelisation.parameter)
        self.model_value = dict(solver.Z_point)

    def restoring_model_values(self, solver):
        """Restoring optimization model's instance status to `Pyomo` 's model object.

        Args:

            solver (`mind.solve.GlobalOptimisation`) : design process's solver
        """
        solver.Z_point = dict(self.model_value)
        solver.restore_model_from_point(self.modelisation.instance)


def parse_list_prototype(filename):
    """Parse prototype datafiles respecting `YAML`'s format.

    Args:

        filename (`str`) : path to datafile

    Returns:
        return list of individuals prototypes
    """
    with open(filename) as yaml_file:
        data = yaml.full_load(yaml_file)
        if not isinstance(data, dict):
            raise TypeError(
                "Expected dictionnary object (<class 'dict'>) of "
                "individuals prototype "
                "But {} are given, "
                "Modify your yaml's file".format(data.__class__)
                )
    return list(data.values())


class PopAlgortihm:
    """Evolutionary solving method class.

    Attributes:

        solver (`mind.solve.GlobalOptimisation`) : `mind` solver's object

        modelisation (`mind.system.MembranesDesignModel`) : desing process model's object

        population (`List(`mind.population.Individual`)`) : list of individuals

        population_altered (`List(`mind.population.Individual`)`) : list of
        child individual obtained from upgrading individuals

        pop_size (`Int`) : Size of population list

        best_individu (`mind.genetic.Individual`) : pointer to the best individual in population

        max_trials (`Int`) : number of localSearch performed on uninitialized
        model's value to construct a solution

        cond_beta (`Int`) : increment index needed to ensure condition check

        individual_list (`List(DICt)`) : list of individual prototype

        marker_in_list (`Int`) : cursor for visiting each element in `individual_list`

    """

    def __init__(self, my_solver, instance_file):
        self.solver = my_solver
        self.population = []
        self.population_altered = []
        self.pop_size = 0
        # number of localSearch doing to an individu prototype
        self.max_trials = 1
        self.cond_beta = 0
        self.best_individu = None
        self.individual_list = parse_list_prototype(instance_file)
        self.marker_in_list = 0

    def create_individu(self, modelisation_template, individu_prototype,
                        identifier):
        """Create an individual.

        Args:

            modelisation_template (`mind.system.MembranesDesignModel`) : desing process model

            individu_prototype (`DICT`) : prototype of individual

            identifier (`Int`) : cursor of individual to create in prototype list
        """
        try:
            # create new configuration object (default one)
            parameter = Configuration(
                individu_prototype['num_membranes'],
                uniform_pup=modelisation_template.parameter.uniform_pup,
                vp=modelisation_template.parameter.vp,
                variable_perm=modelisation_template.parameter.variable_perm,
                fixing_var=modelisation_template.parameter.fixing_var)

            # Loading some information about the given prototype
            if 'lb_area' in individu_prototype.keys():
                for k, v in individu_prototype['lb_area'].items():
                    parameter.lb_area[(k - 1)] = v

            if 'ub_area' in individu_prototype.keys():
                for k, v in individu_prototype['ub_area'].items():
                    parameter.ub_area[(k - 1)] = v

            if 'ub_acell' in individu_prototype.keys():
                for k, v in individu_prototype['ub_acell'].items():
                    parameter.ub_acell[(k - 1)] = v

            modelisation = build_model(parameter,
                                       modelisation_template.filename,
                                       modelisation_template.perm_filename,
                                       modelisation_template.eco_filename,
                                       modelisation_template.mask_filename)

            # modifing perm data and update model
            for type_mem in modelisation.permeability_data.keys():
                modelisation.permeability_data[type_mem].which_mem = []

            if 'mem_type' in individu_prototype.keys():
                for k, v in individu_prototype['mem_type'].items():
                    # print(k, ' -> ', v)
                    type_mem = v
                    modelisation.permeability_data[type_mem].which_mem.append(
                        int(k))

            # model object update permeability data
            modelisation.load_permeability_data()

            if 'fixing' in individu_prototype.keys():
                fixing = individu_prototype['fixing']
            index_family = identifier

        except KeyError as e:
            logger.exception("Failed to create individu from "
                             "prototype information [individu_{}]"
                             " : invalid data".format(identifier + 1))
            raise

        except Exception as e:
            logger.exception(
                "Failed to create model from"
                "prototype information [individu_{}]".format(identifier + 1))
            raise
        else:
            individu = Individu(modelisation,
                                fixing,
                                index_family,
                                active=False,
                                rank=None)

            # fixing element
            individu.fixing_variable()

            return individu

    def extracting_prototype(self, modelisation_template, init_marker,
                             end_marker):
        """Extracting from prototype list.

        Args:
            modelisation_template (`mind.system.MembranesDesignModel`) : desing process model

            init_marker (`Int`) : cursor from which begining extraction

            end_marker (`Int`) : cursor to end extraction
        """
        assert init_marker <= end_marker
        for identifier in range(init_marker, end_marker):
            individu_prototype = self.individual_list[identifier]
            # create individu
            print("\n")
            logger.info("Creation of individu_{}".format(identifier))
            individu = self.create_individu(modelisation_template,
                                            individu_prototype, identifier)

            individu.active = self.solver.find_starting_solution(
                individu.modelisation, self.max_trials)
            try:
                individu.obj = individu.modelisation.instance.obj()
            except Exception:
                individu.obj = None
            individu.storing_model_values(self.solver)
            # insert individu in population
            self.population.append(individu)

        return end_marker

    def initiate_population(self, modelisation_template, nb_extracted):
        """Initialise population list.

        Args:
            modelisation_template (`mind.system.MembranesDesignModel`) : desing process model

            nb_extracted (`Int`) : number of element to extract in the prototype list
        """
        if len(self.individual_list) < nb_extracted:
            msg = ("Trying to extract N1 = {} elements"
                   " from prototype list of size {}".format(
                       nb_extracted, len(self.individual_list)))

            logger.exception(msg)
            raise ValueError(msg)

        self.extracting_prototype(modelisation_template, 0, nb_extracted)

    def local_search(self, individu):
        """LocalSearch's algorithm around a feasible solution.

        Args:
            individu (`mind.population.Individu`) : individual to evolve
        """
        feasible = self.solver.run_local_search(individu.modelisation.instance)
        try:
            individu.obj = individu.modelisation.instance.obj()
        except Exception:
            individu.obj = None

        # print("Check individu obj -> ",individu.obj)

        if feasible:
            self.solver.save_solution(individu.modelisation,
                                      algo_identifier_str="Evolutionary method")

        return feasible

    def evolve_population(self, individu, k_iterations):
        """Evolve operation of population's method.

        Args:
            individu (`mind.population.Individu`) : individual to evolve

            k_iterations (`Int`) : number of iteration to perform for evolving
        """
        print()
        logger.info("Evolving population's individu_{}".format(
            individu.index_family))
        derivated_individu = copy.deepcopy(individu)
        current_best = None
        init_obj = derivated_individu.obj
        final_status = derivated_individu.active

        for k in range(k_iterations):
            print()
            if derivated_individu.active:
                self.solver.perturb_solution(derivated_individu.modelisation)
            else:
                self.solver.construct_starting_point(
                    derivated_individu.modelisation)

            derivated_individu.active = self.local_search(derivated_individu)

            # TODO: watch mis à jour
            if derivated_individu.active:
                final_status = True
                if current_best:
                    if derivated_individu.obj < current_best:
                        current_best = derivated_individu.obj
                        derivated_individu.storing_model_values(self.solver)
                else:
                    current_best = derivated_individu.obj
                    derivated_individu.storing_model_values(self.solver)

        derivated_individu.restoring_model_values(self.solver)
        derivated_individu.obj = current_best if current_best else init_obj
        derivated_individu.active = final_status
        self.population_altered.append(derivated_individu)

    def update_population(self):
        """Update operation of population's method.
        """
        logger.info("Update population")
        # parent replaced by child if condition match
        self.pop_size = len(self.population)
        assert self.pop_size == len(self.population_altered)
        for element in range(self.pop_size):
            parent = self.population[element]
            child = self.population_altered[element]
            if child.active:
                if parent.active and parent.obj:
                    if child.obj < parent.obj:
                        # replace parent by child
                        self.population[element] = child
                        self.population_altered[element] = parent
                        self.population_altered[element].period = 0
                else:
                    # replace parent by child
                    self.population[element] = child
                    self.population_altered[element] = parent
                    self.population_altered[element].period = 0

    def printing_population(self):
        """Printing population list.
        """
        print()
        for individu in self.population:
            print(individu)

        print()
        for individu in self.population_altered:
            print(individu)
        print()

    def update_epoque(self):
        """Update epoque of algorithm's method.

        """
        for individu in self.population:
            individu.period += 1
        self.cond_beta += 1

    def beta_two_condition_quality_check(self):
        """Kepping individual `if` condition check is valid.

        """
        max_epoque = max([individu.period for individu in self.population])
        for epoque in range(1, max_epoque + 1):
            # print(epoque)
            same_age_individu = [
                individu for individu in self.population
                if individu.period == epoque
            ]

            if same_age_individu:
                avg_obj_same_age = (
                    sum(individu.obj for individu in same_age_individu) /
                    len(same_age_individu))

                for individu in same_age_individu:
                    if individu.obj >= avg_obj_same_age:
                        self.population.remove(individu)

        if self.population:
            avg_obj = (sum(individu.obj for individu in self.population) /
                       len(self.population))

            for individu in reversed(self.population):
                if individu.obj >= avg_obj:
                    self.population.remove(individu)

    def check_population_quality(self, beta_one, beta_two):
        """Check population quality.

        Args:

            beta_one (`Int`) : \\(\\beta_1\\) coefficient

            beta_two (`Int`) : \\(\\beta_2\\) coefficient

        """
        # infeasible individu
        for individu in reversed(self.population):
            if not individu.active:
                self.population.remove(individu)

        # increment epoque
        self.update_epoque()

        # compare epoque to beta_one
        for individu in reversed(self.population):
            if individu.period >= beta_one:
                self.population.remove(individu)

        # compare epoque to beta_two
        if self.cond_beta == beta_two:
            self.beta_two_condition_quality_check()
            self.cond_beta = 0

    def recovery_best_individual(self):
        """Restore to the pyomo model object, the best individual of population.
        """
        obj_val = self.solver.fputative + 1
        # for individu in self.population:
        for individu in self.population:
            if individu.active:
                if individu.obj < obj_val:
                    self.best_individu = individu
                    obj_val = individu.obj
        logger.info("Best individu :\n {}".format(self.best_individu))

    def execute_algorithm(self, beta_one, beta_two, k_iterations):
        """Execute evolutionary algorithm.

        Args:

            beta_one (`Int`) : $$\\beta_1$$ coefficient

            beta_two (`Int`) : $$\\beta_2$$ coefficient

            k_iterations (`Int`) : $$\\k_{iteration}$$ coefficient
        """
        for individu in self.population:
            self.evolve_population(individu, k_iterations)

        self.update_population()
        self.population_altered = []
        self.recovery_best_individual()
        self.check_population_quality(beta_one, beta_two)
        self.printing_population()

    def run(self, modelisation, nb_extracted, beta_one=3, beta_two=5):
        """Run the population's algorithm method.

        Args:

            modelisation (`mind.system.MembranesDesignModel`) : design process model

            nb_extracted (`Int`) : size of individual population list

            beta_one (`Int`) : $$\\beta_1$$ coefficient

            beta_two (`Int`) : $$\\beta_2$$ coefficient

        """
        logger.info("Running modified evolutionary algorithm ...")
        k_iterations = 3
        self.initiate_population(modelisation, nb_extracted)

        marker = nb_extracted
        while marker < len(self.individual_list):
            self.execute_algorithm(beta_one, beta_two, k_iterations)
            # marker = self.extracting_prototype(marker)
            end_marker = min(marker + (nb_extracted - len(self.population)),
                             len(self.individual_list))
            print("marker = {} and end_marker = {}".format(marker, end_marker))
            marker = self.extracting_prototype(modelisation, marker, end_marker)
            # update marker
            marker = len(self.individual_list) + 1 if not marker else marker

        # repace modelisation template by best individu (optionnal)
        if self.best_individu:
            modelisation = self.best_individu.modelisation

        return True if self.best_individu else False
