"""Solve optimization problem with polpulation methode."""

import os
import logging

from mind.fixing import fixing_method
from mind.genetic_pop_ranking import population_ranking
from mind.printing import print_model_solution
# import mind.solve
from mind.util import store_object_to_file

# logging variable
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)
handler = logging.StreamHandler()
# handler = logging.FileHandler('log.txt')
logger.addHandler(handler)
formatter = logging.Formatter(fmt='[%(asctime)s] %(levelname)s : %(message)s',
                              datefmt='%a, %d %b %Y %H:%M:%S')
handler.setFormatter(formatter)


class Individual:
    """Description of genetic population's individual.
        Attributes:

            model(`Pyomo's model instance`) : constructed model of membrane design model.

            obj (`DICT`) : associative data structure containing
            pair of models' variables and it's values

            active (`Bool`) : `True` if current individual is a feasible solution

            index (`Int`) : Identifier of individual

            fixed_value (`Bool`) : `True` if some variables must be fixed for individual

            init_file (`str`) : filename containing information
            on variables to be fixed for individual

            rank (`Int`) : rank of individual in the population when
            sorting needed
    """

    def __init__(self,
                 model={},
                 obj=None,
                 active=False,
                 fixed_value=False,
                 init_file="",
                 rank=None):
        """ Individual description."""
        self.model = model
        self.obj = obj
        self.active = active
        self.index = None
        # are some values of individual, fixed
        self.fixed_value = fixed_value
        self.init_file = init_file
        # raking individual
        self.rank = rank


class Population:
    """Evolutionary solving method class.

    Attributes:

        solver (`mind.solve.GlobalOptimisation`) : `mind` solver's object

        modelisation (`mind.system.MembranesDesignModel`) : desing process model's object

        population (`List(`mind.genetic.Individual`)`) : list of individuals

        fixed_pop_size (`Int`) : Size of population list

        best_individu (`mind.genetic.Individual`) : pointer to the best individual in population
    """

    def __init__(self, my_solver, modelisation, population=[]):
        try:
            assert modelisation.instance is not None
        except Exception:
            logger.exception("No pyomo model instance detected")
            raise

        self.solver = my_solver
        self.modelisation = modelisation
        self.population = population
        self.fixed_pop_size = None
        self.best_individu = None

    def storing_model(self):
        """Store optimization model's instance to the `Pyomo` 's model object."""
        self.solver.store_model_to_point(self.modelisation.instance,
                                         self.modelisation.parameter)
        return self.solver.Z_point

    def printing_population(self, pop=[]):
        """Print population list."""
        pop_size = len(self.population)
        print("\n--- POPULATION ----\n")
        print("Index \t Obj func \t OUT_prod \t " "OUT_waste \t Rank \t Active")

        for individu in range(pop_size):
            print("{} \t {} \t {} \t {} \t {} \t {}".format(
                individu + 1, self.population[individu].obj,
                self.population[individu].model['OUT_prod'],
                self.population[individu].model['OUT_waste'],
                self.population[individu].rank,
                self.population[individu].active))

            # store_object_to_file(self.population[individu].model, file)

        print("-------------------------------------------")
        if pop != []:
            pop_size = len(pop)
            for individu in range(pop_size):
                print("{} \t {} \t {} \t {} \t {} \t {}".format(
                    individu + 1, pop[individu].obj,
                    pop[individu].model['OUT_prod'],
                    pop[individu].model['OUT_waste'], pop[individu].rank,
                    pop[individu].active))
        print()

    def initiate_population(self, pop_size):
        """Initialization of population list.
        Args:
            pop_size (`Int`) : size used to fix the number of elements in population.
        """
        logger.info("Initialisation of initial population")
        self.population = []
        #  store solver.modelisation.instance  to Z_point
        self.solver.store_model_to_point(self.modelisation.instance,
                                         self.modelisation.parameter)
        # copying solver.modelisation.instance pop_size time [dict format]
        for individu in range(pop_size):
            # original_point
            self.population.append(
                Individual(dict(self.solver.Z_point), None, False))

            # Evaluation
            print()
            logger.info("Individual_{}'s evaluation".format(individu + 1))
            # change context of solver model
            self.solver.Z_point = self.population[individu].model
            self.solver.restore_model_from_point(self.modelisation.instance)

            feasible = self.solver.find_starting_solution(
                self.modelisation, max_trials_starting_points=1)

            if feasible:
                # marking that this individu is active
                self.population[individu].active = True
                self.population[individu].obj = self.modelisation.instance.obj()
                self.index = individu
                # how to know that solution must be initialized
                self.population[individu].fixed_value = False
                self.population[individu].init_file = (
                    self.solver.log_dir + 'population' + os.path.sep +
                    'individu_{}.dat'.format(individu + 1))

            # recovery the state of the model
            self.population[individu].model = self.storing_model()

    def select_individual(self):
        """Genetic method 's selection operations.

        Select within population some individu in which evolution operation are performed.
        """
        logger.info(
            "Selection of candidates which participe in gerations production")
        # selecting all active Individuals
        index_individu = 0
        while index_individu < len(self.population):
            if self.population[index_individu].active:
                index_individu = index_individu + 1
            else:
                self.population.pop(index_individu)

        self.fixed_pop_size = len(self.population)

    def perturb_optimize_operation(self, individu):
        """Part of evolution operation of genetic's algorithm.

        Perturb a given model's solution and do localSearch around the perturbed solution.

        Args:
            individu (`mind.genetic.Individual`) : individual to be evoluated

        Returns:
            return `True` if a new generated individual (`child`) is active

        Raises:
            Exception : `if` individu is not `active`.
        """
        my_model = self.modelisation.instance
        my_param = self.modelisation.parameter

        try:
            assert self.population[individu].active
        except Exception:
            logger.exception('Perturbing infeasible solution is not allowed')
            raise

        # Perturb the current local optimum
        self.solver.perturb_solution(self.modelisation)
        # if fixing individual
        if self.population[individu].fixed_value:
            fixing_method(self.population[individu].init_file, my_model,
                          my_param)

        feasible = self.solver.run_local_search(self.modelisation.instance)

        if feasible:
            f_current = my_model.obj()
            # save solution in file
            self.solver.stationaryfile.write("pert_optimize : " + "obj " +
                                             str(f_current) + "\n")
            print_model_solution(my_model, self.solver.stationaryfile, my_param,
                                 self.modelisation.membrane_behavior, True)
            logger.info("obtain solution and saved in stationaryfile")
            logger.info("f_obj = {}".format(f_current))
        else:
            logger.info("model infeasible")
            None
        return feasible

    def reproduction_operation(self, individu):
        """Evolution operation of genetic's algorithm.

        Args:
            individu (`mind.genetic.Individual`) : individual to be evoluated

        Returns:
            generate a new individual (`child`)

        Raises:
            Exception : `if` individu is not `active`.
        """

        logger.info(
            "Evolutionary reproduction method Operations individu_{}".format(
                individu + 1))

        # change context of solver model
        self.solver.Z_point = dict(self.population[individu].model)
        self.solver.restore_model_from_point(self.modelisation.instance)

        # perturb and optimize model solution
        feasible = self.perturb_optimize_operation(individu)

        # Recovery child
        # child individual is generated
        # recovery the state of the model
        obj_value = 0
        try:
            obj_value = self.modelisation.instance.obj()
        except Exception as e:
            logger.warning('model infeasible and getting ZeroDivisionError')
            obj_value = 1e6

        child_individual = Individual(dict(self.storing_model()), obj_value,
                                      feasible)

        child_individual.index = individu

        # TODO: init_file for child
        return child_individual

    def exchange_individual(self, new_population, individu, child):
        """Swap individual in population list.

        Args:

            new_population (`List[mind.genetic.Individual]`) : new list of individual handling generated childs

            individu (`mind.genetic.Individual`) : individual to be evoluated

            child (`mind.genetic.Individual`) : derived child of individual

        """
        logger.info("Exchange pop1 individual_{} "
                    "and pop2 individual_{}".format(individu + 1, child + 1))
        self.population[individu].obj = new_population[child].obj
        self.population[individu].model = new_population[child].model
        self.population[individu].rank = new_population[child].rank
        # fixing (false) : don't reproducted to child individual
        self.population[individu].fixed_value = False
        self.population[individu].init_file = ""

    def closest_kmeans(self, new_population, child):
        """Evaluate the closest element to `child` individual in `population`
        according to `Kmeans` 's distance.

        Args:
            new_population (`mind.genetic.Individual`) : List of individual containing generated childs

            child (`mind.genetic.Individual`) : child individual

        Returns:
            return index of the closest individual of (`child`) in population.

        """
        closest_index = None
        # rank_found means the presence of child rank in popualtion
        rank_found = False
        if new_population[child].active:
            for individu in range(self.fixed_pop_size):
                # if individu and child have same ranking
                if self.population[individu].rank == new_population[child].rank:
                    rank_found = True
                    if new_population[child].obj < self.population[individu].obj:
                        # child is better than individu
                        closest_index = individu
                        break

            # if child rank is not listed or found in population
            if not rank_found:
                # list containing population rank
                rank_list = list(
                    map(lambda individual: individual.rank, self.population))

                # test if duplicates values are in rank_list
                if len(rank_list) == len(set(rank_list)):
                    # no duplicate rank's value in pop1 (probability almost 0)
                    # insert this child into population
                    closest_index = -1
                else:
                    # duplicated line detected
                    # creation of list : containing rank that are duplicated
                    rank_times = list(
                        set([x for x in rank_list if rank_list.count(x) > 1]))
                    # index = None
                    obj = float('-inf')
                    for individu in range(self.fixed_pop_size):
                        if self.population[individu].rank == rank_times[0]:
                            if self.population[individu].obj > obj:
                                # index = individu
                                closest_index = individu
                                obj = self.population[individu].obj

        return closest_index

    def closest_father_index(self, new_population, child):
        """Evaluate the closest element to `child` individual in `population`
        according to an `Naive` 's distance based on element of the same index.

        Args:
            new_population (`mind.genetic.Individual`) : List of individual containing generated childs

            child (`mind.genetic.Individual`) : child individual

        Returns:
            return index of the closest individual of (`child`) in population.

        """
        closest_index = None
        # Same index
        individu = child
        if (new_population[child].active and
                new_population[child].obj < self.population[individu].obj):
            # if child better than father then exchange
            closest_index = individu

        return closest_index

    def distance(self, new_population, child, closest):
        """Evaluate the closest element to `child` individual in `population`
        according to `closest` distance.

        Args:
            new_population (`mind.genetic.Individual`) : List of individual containing generated childs

            child (`mind.genetic.Individual`) : child individual

            closest (`str`) : `'kmeans'` or `'father_index'` `(default = 'kmeans')`

        Returns:
            return index of the closest individual of (`child`) in population.

        """
        individu = None
        if closest == "kmeans":
            individu = self.closest_kmeans(new_population, child)
        elif closest == "father_index":
            individu = self.closest_father_index(new_population, child)
        else:
            logger.exception(
                "ERROR : closest element's distance notion unknown")
            raise ValueError(
                "ERROR : closest element's distance notion unknown")

        return individu

    def update_population(self, new_population, closest="kmeans"):
        """Update operation of genetic's algorithm.

        Upgrade population list by replacing bad performed `individual` by good
        performed one in the new list generated of child population.

        Args:
            new_population (`mind.genetic.Individual`) : List of individual containing generated childs

            closest (`str`) : `'kmeans'` or `'father_index'` `(default = 'kmeans')`

        """
        logger.info("Updating our population pool")
        try:
            assert self.fixed_pop_size is not None
        except Exception:
            logger.exception("Error : No candidates selected")
            raise

        self.printing_population(new_population)

        # ranking populations
        if closest == "kmeans":
            try:
                population_ranking(self, new_population)
            except Exception:
                logger.exception(
                    "Error : Try to do a kmeans with number of cluster "
                    " bigger than number of observations")
                raise

        # printing populations
        self.printing_population(new_population)

        # Updating elements
        for child in range(self.fixed_pop_size):
            individu = self.distance(new_population, child, closest)
            if individu is None:
                # Do nothing, bad value for child [no updatating]
                pass

            elif individu == -1:
                # adding new child to population
                logger.info("Inserting  pop2 individual_{} "
                            " to pop1 [which is extended]".format(child + 1))
                self.population.append(new_population[child])
            else:
                # Exchange individu in population with child
                self.exchange_individual(new_population, individu, child)

        # Update also population size in case we added new individual
        self.fixed_pop_size = len(self.population)

    def recovery_best_individual(self):
        """Restore to the pyomo model's object, the best individual of population list.
        """
        obj_val = self.solver.fputative + 1
        for individu in range(len(self.population)):
            if self.population[individu].obj < obj_val:
                self.solver.Z_point = dict(self.population[individu].model)
                self.solver.restore_model_from_point(self.modelisation.instance)
                self.best_individu = individu
                obj_val = self.population[individu].obj

    def run(self, pop_size, generations):
        """Run the genetic's algorithm.

        Args:
            pop_size (`Int`) : size of individuals population list

            generations (`Int`) : genetic's algorithm number of generations

        """
        logger.info("Running evolutionary algorithm ...")
        # initialiser population pool (also evaluate it)
        self.initiate_population(pop_size)
        # Selection of candidates
        self.select_individual()

        for generation in range(generations):
            print()
            logger.info("Generation {}".format(generation + 1))
            # Defining new population structure (list)
            new_population = []
            for individu in range(len(self.population)):
                # reproduction operation
                child = self.reproduction_operation(individu)
                new_population.append(child)

            # updating populations
            self.update_population(new_population, closest="kmeans")
            self.printing_population()

        # At this step model contain last resolution model
        # return individual with best obj found
        self.recovery_best_individual()
        # plus one, because of index
        logger.info("Best individu = {}".format(self.best_individu + 1))
