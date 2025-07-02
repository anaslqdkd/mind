"""Defining optimization model of Membrane design process.

This module contain common part of model shared by liquid and gas model.
"""

from abc import ABC, abstractmethod
import logging
from sys import exit

import pyomo.environ as pe
try:
    from pyomo.core.base.componentuid import ComponentUID
except Exception:
    exit("Sorry, invalid version of pyomo (>= 5.7.3)")

from mind.optmodel_utilities import initZero

# logging variable
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)
handler = logging.StreamHandler()
# handler = logging.FileHandler('log1.txt')
logger.addHandler(handler)
formatter = logging.Formatter(fmt='[%(asctime)s] %(levelname)s : %(message)s',
                              datefmt='%a, %d %b %Y %H:%M:%S')
handler.setFormatter(formatter)


class MembranesDesignModel(ABC):
    """An abstract class.
    It define parameter, varaibles and some constraint of the optimization
    model shared by both `mind.liquid` and `mind.gas` model template.

    It contain also some Not-Implemented functions,
    deleguate to its subclasses.

    Attributes:
        parameter (`mind.builder.Configuration`): design process configuration

        permeability_data (`DICT`): membrane permeability's data information

        abstractModel (`pyomo.environ.AbstractModel`): design process abstract model

        instance (`pyomo.environ.AbstractModel.create_instance`): design process model's instance

        membrane_behavior (`mind.membranes.MembranesTypes`): membrane representation object

    """

    # Parameters definitions
    def __overall_system_parameters(self) -> None:
        """Defining global system parameter."""
        # set of membranes
        self.abstractModel.states = pe.Set(ordered=True)
        # set of components of each mixture gaseous
        self.abstractModel.components = pe.Set(ordered=True)
        # Bounds on RET and PERM
        self.abstractModel.ub_perc_prod = pe.Param(
            self.abstractModel.components, default=1.0)
        self.abstractModel.lb_perc_prod = pe.Param(
            self.abstractModel.components, default=0.0)
        self.abstractModel.ub_perc_waste = pe.Param(
            self.abstractModel.components, default=1.0)
        self.abstractModel.lb_perc_waste = pe.Param(
            self.abstractModel.components, default=0.0)

        # number of pieces of the division of each membrane
        self.abstractModel.n = pe.Param(default=200,
                                        initialize=max(
                                            self.parameter.discretisation))
        # set of pieces of the division of each membrane
        self.abstractModel.N = pe.RangeSet(self.abstractModel.n)
        # set of pieces of the division of each membrane except last one
        self.abstractModel.N_minuslast = pe.RangeSet(self.abstractModel.n - 1)
        # flow rate of a FEED
        self.abstractModel.FEED = pe.Param()
        # fractions of the components in the FEED
        self.abstractModel.XIN = pe.Param(self.abstractModel.components)

        self.abstractModel.final_product = pe.Param(
            within=self.abstractModel.components)
        # qt of product that must exit the system
        self.abstractModel.normalized_product_qt = pe.Param(default=0)

        # parameter used to impose some flows larger then zero
        # it is used in the GO algorithm
        # but it is considered as a property of the model
        self.abstractModel.tol_zero = pe.Param(default=0.001)

        # pressure
        self.abstractModel.pressure_in = pe.Param()

        # Defining pressure prod param
        self.abstractModel.pressure_prod = pe.Param(default=-1)

    def __some_components_bound(self) -> None:
        """Defining some bounds in membrane stage level of the model."""
        # maximal percentage of the retracted flow (retentated or permeated)
        # of a membrane into itself
        self.abstractModel.p_retr_max = pe.Param()
        self.abstractModel.ub_press_down = pe.Param(mutable=True)
        self.abstractModel.lb_press_down = pe.Param(mutable=True)
        self.abstractModel.lb_press_up = pe.Param(mutable=True)
        self.abstractModel.ub_press_up = pe.Param(mutable=True)
        self.abstractModel.ub_feed = pe.Param(mutable=True)
        self.abstractModel.ub_out_prod = pe.Param(
            mutable=True, default=self.abstractModel.ub_feed)
        self.abstractModel.ub_out_waste = pe.Param(
            mutable=True, default=self.abstractModel.ub_feed)
        self.abstractModel.ub_feed_tot = pe.Param(mutable=True)

        def init_ub_acell(model, mem):
            return self.parameter.ub_acell[mem - 1]

        self.abstractModel.ub_acell = pe.Param(self.abstractModel.states,
                                               mutable=True,
                                               initialize=init_ub_acell)

        self.abstractModel.lb_acell = pe.Param(self.abstractModel.states,
                                               mutable=True,
                                               initialize=0)

    def __bounding_area_variable(self):

        def init_ub_area(model, mem):
            return self.parameter.ub_area[mem - 1]

        self.abstractModel.ub_area = pe.Param(self.abstractModel.states,
                                              mutable=True,
                                              initialize=init_ub_area)

        def init_lb_area(model, mem):
            return self.parameter.lb_area[mem - 1]

        self.abstractModel.lb_area = pe.Param(self.abstractModel.states,
                                              mutable=True,
                                              initialize=init_lb_area)

    def __split_flows_bounds_paramaters(self):
        """Defining split flows bounds parameters."""
        self.abstractModel.lb_splitRET_frac = pe.Param(
            self.abstractModel.states,
            self.abstractModel.states,
            default=0.0,
            within=pe.UnitInterval,
            mutable=True)
        self.abstractModel.ub_splitRET_frac = pe.Param(
            self.abstractModel.states,
            self.abstractModel.states,
            default=1.0,
            within=pe.UnitInterval,
            mutable=True)
        self.abstractModel.lb_splitPERM_frac = pe.Param(
            self.abstractModel.states,
            self.abstractModel.states,
            default=0.0,
            within=pe.UnitInterval,
            mutable=True)
        self.abstractModel.ub_splitPERM_frac = pe.Param(
            self.abstractModel.states,
            self.abstractModel.states,
            default=1.0,
            within=pe.UnitInterval,
            mutable=True)

        self.abstractModel.lb_splitRET_frac_full = pe.Param(
            self.abstractModel.states,
            self.abstractModel.states,
            default=0.0,
            within=pe.UnitInterval,
            mutable=True)
        self.abstractModel.ub_splitRET_frac_full = pe.Param(
            self.abstractModel.states,
            self.abstractModel.states,
            default=1.0,
            within=pe.UnitInterval,
            mutable=True)
        self.abstractModel.lb_splitPERM_frac_full = pe.Param(
            self.abstractModel.states,
            self.abstractModel.states,
            default=0.0,
            within=pe.UnitInterval,
            mutable=True)
        self.abstractModel.ub_splitPERM_frac_full = pe.Param(
            self.abstractModel.states,
            self.abstractModel.states,
            default=1.0,
            within=pe.UnitInterval,
            mutable=True)

    def __objective_parameters(self):
        """Defining parameter involving in objective."""

        self.abstractModel.ub_PERM = pe.Param()
        # molar mass of each component
        self.abstractModel.molarmass = pe.Param(self.abstractModel.components)

    def set_parameters(self):
        """Defining parameters for model construction."""
        self.__overall_system_parameters()
        self.__some_components_bound()
        self.__bounding_area_variable()
        self.__split_flows_bounds_paramaters()
        self.__objective_parameters()

    # Variables definitions
    def __flow_rate_membranes_variables(self):
        """Defining flows quantity variables in membranes stages levels."""

        # Variables related to each membrane
        # flow rate at the entrance of the membrane s
        self.abstractModel.Feed_mem = pe.Var(
            self.abstractModel.states,
            bounds=(0.0, self.abstractModel.ub_feed_tot))
        # flow rate of the retentated flux at the outlet of a membrane s
        self.abstractModel.Flux_RET_mem = pe.Var(
            self.abstractModel.states,
            bounds=(0.0, self.abstractModel.ub_feed_tot))
        # flow rate of the permeated flux at the outlet of a membrane s
        self.abstractModel.Flux_PERM_mem = pe.Var(
            self.abstractModel.states,
            bounds=(0.0, self.abstractModel.ub_feed_tot))

    def __component_flow_rate_membranes_variables(self):
        """Defining components percentage var in membrane stages levels."""

        # fract. of a component at the inlet of a membrane s
        self.abstractModel.XIN_mem = pe.Var(self.abstractModel.states,
                                            self.abstractModel.components,
                                            bounds=(0.0, 1.0))
        # fract. of a component for the ret flux at the outlet of membrane s
        self.abstractModel.X_RET_mem = pe.Var(self.abstractModel.states,
                                              self.abstractModel.components,
                                              bounds=(0.0, 1.0))
        # fract. of a component for the perm flux at the outlet of the mem
        self.abstractModel.X_PERM_mem = pe.Var(self.abstractModel.states,
                                               self.abstractModel.components,
                                               bounds=(0.0, 1.0))

    def __flows_split_variables(self):
        """Defining interconnection flows variables between membranes.

        Feed can be split and send some quantity to each membranes ,
        Each membrane can also split its flow and send some quantity to
        another membrane."""

        # Variables related to interconnection between membranes
        # There are different splits:  1 for the feed
        # (can be splitted amond all the membranes
        self.abstractModel.splitFEED = pe.Var(
            self.abstractModel.states,
            bounds=(0.0, self.abstractModel.ub_feed_tot))
        self.abstractModel.splitFEED_frac = pe.Var(self.abstractModel.states,
                                                   bounds=(0.0, 1.0))
        # 1 for each Ret and Perm of each membrane each of
        # them can be send to another membrane
        self.abstractModel.splitRET = pe.Var(
            self.abstractModel.states,
            self.abstractModel.states,
            bounds=(0.0, self.abstractModel.ub_feed_tot))
        self.abstractModel.splitPERM = pe.Var(
            self.abstractModel.states,
            self.abstractModel.states,
            bounds=(0.0, self.abstractModel.ub_feed_tot))

        # out of the system
        self.abstractModel.splitOutRET = pe.Var(
            self.abstractModel.states,
            bounds=(0.0, self.abstractModel.ub_feed_tot))
        self.abstractModel.splitOutPERM = pe.Var(
            self.abstractModel.states,
            bounds=(0.0, self.abstractModel.ub_feed_tot))

    def __components_split_variables(self):
        """ Components percentage variables related to split variables. """

        # Fractions for splits
        def splitRET_frac_bounds(model, i, j):
            return (model.lb_splitRET_frac[i, j], model.ub_splitRET_frac[i, j])

        self.abstractModel.splitRET_frac = pe.Var(self.abstractModel.states,
                                                  self.abstractModel.states,
                                                  bounds=splitRET_frac_bounds)

        def splitPERM_frac_bounds(model, i, j):
            return (model.lb_splitPERM_frac[i, j], model.ub_splitPERM_frac[i,
                                                                           j])

        self.abstractModel.splitPERM_frac = pe.Var(self.abstractModel.states,
                                                   self.abstractModel.states,
                                                   bounds=splitPERM_frac_bounds)

        # directly out the system NB may need bounds here as well
        self.abstractModel.splitOutRET_frac = pe.Var(self.abstractModel.states,
                                                     bounds=(0.0, 1.0))
        self.abstractModel.splitOutPERM_frac = pe.Var(self.abstractModel.states,
                                                      bounds=(0.0, 1.0))

    def __overall_system_variables(self):
        """System level-1 variables. """
        # Variables related to the entire system
        # flow rate of product flux
        # the way this variable is calculated depends on the type of membranes

        # TODO: Change bound name
        # self.abstractModel.OUT_prod = pe.Var(
        #     bounds=(0.0, self.abstractModel.ub_feed))
        self.abstractModel.OUT_prod = pe.Var(
            bounds=(self.parameter.epsilon.get('xout'), self.abstractModel.ub_out_prod))
        # flow rate of secondary product or waste
        # self.abstractModel.OUT_waste = pe.Var(
        #     bounds=(0.0, self.abstractModel.ub_feed))
        self.abstractModel.OUT_waste = pe.Var(
            bounds=(self.parameter.epsilon.get('xout'), self.abstractModel.ub_out_waste))
        # fractions for all the gaseous components in the product flux
        # TODO: aks and add ub_perc_prod in bounds
        self.abstractModel.XOUT_prod = pe.Var(self.abstractModel.components,
                                              bounds=(self.parameter.epsilon.get('xout'), 1.0))
        # fractions for all the gaseous components in secondary product/waste
        self.abstractModel.XOUT_waste = pe.Var(self.abstractModel.components,
                                               bounds=(self.parameter.epsilon.get('xout'), 1.0))

        if (self.parameter.uniform_pup):
            self.abstractModel.pressure_up = pe.Var(
                bounds=(self.abstractModel.lb_press_up,
                        self.abstractModel.ub_press_up))
        else:
            # upstream pressure in Bar  (different for each membrane)
            self.abstractModel.pressure_up = pe.Var(
                self.abstractModel.states,
                bounds=(self.abstractModel.lb_press_up,
                        self.abstractModel.ub_press_up))

        self.abstractModel.pressure_down = pe.Var(
            self.abstractModel.states,
            bounds=(self.abstractModel.lb_press_down,
                    self.abstractModel.ub_press_down))

        # membrane's area
        def bounding_area(model, mem):
            return (self.parameter.lb_area[mem - 1],
                    self.parameter.ub_area[mem - 1])

        self.abstractModel.area = pe.Var(self.abstractModel.states,
                                         bounds=bounding_area)

    # General or global callback which 'll construct variables
    def set_variables(self):
        """Set all necessary variables to build model. """
        # membranes levels variables
        self.__flow_rate_membranes_variables()
        self.__component_flow_rate_membranes_variables()
        # Membranes interconnection
        self.__flows_split_variables()
        self.__components_split_variables()
        # Overall system variables
        self.__overall_system_variables()

    def init_model(self):
        """Wrapper callback to define parameters and variables
        of the model. """
        # call functions
        self.set_parameters()
        self.set_variables()

    # Define constraints and objective function
    def create_process_model(self):
        """Wrapper callback to define constraints and objective function."""
        self.define_process_contraints()
        self.define_process_objective()

    def define_process_contraints(self):
        """Add problem contraints to the model """
        self.__flow_conservation_overall_sytem_constraint()
        self.__flow_conservation_membranes_levels_constraint()
        self.__fractions_components_constraint()
        self.__superstructure_flow_conservation_constraint()
        self.__pressures_constraint()
        # removing Isolated membranes
        self.__no_isolated_membrane_constraint()
        self.__flow_composition_bound_constraint()
        self.__coherence_frac_variables_constraint()
        self.__recovery_constraint()
        self.__activated_constraint_simplified_model()
        # self.__no_loss_flow_constraint()

    def define_process_objective(self):
        """State the objective function of the model"""

        # New generalized form for the cost function
        def min_waste(model):
            return model.OUT_waste

        def obj_cost(model):
            objective = self.obj_.objective_function(model)
            # return self.obj_.objective_function(model)
            return objective

        self.abstractModel.obj = pe.Objective(rule=obj_cost, sense=pe.minimize)

        self.abstractModel.simplified_obj = pe.Objective(expr=0,
                                                         sense=pe.minimize)

    def __insert_datafile_line(self, fname, insert_position=3):
        """Insert number of states and mem_types_set necessary to
        datafile in some position."""
        f = open(fname, "r")
        contents = f.readlines()
        f.close()

        # Insert number of states
        states = list(range(1, self.parameter.num_membranes + 1))
        states = ' '.join(str(ind) for ind in states)
        txt = "set states := " + states + ";\n"
        # insert txt value in insert_position
        contents.insert(insert_position, txt)

        # Insert states and mem_type information
        type_mem = list(self.permeability_data.keys())
        type_mem = ' '.join("\"{}\"".format(item) for item in type_mem)
        txt = "set mem_types_set := " + type_mem + ";\n"
        # insert txt value in insert_position
        contents.insert(insert_position, txt)

        f = open(self.filename, "w")
        contents = ''.join(contents)

        f.write(contents)
        f.close()

    def __delete_datafile_line(self, delete_position=3):
        """Insert number of states necessary to datafile in some position."""
        f = open(self.filename, "r")
        contents = f.readlines()
        f.close()

        # Delete two consecutives lines
        contents = contents[:delete_position] + contents[delete_position + 2:]

        f = open(self.filename, "w")
        contents = ''.join(contents)

        f.write(contents)
        f.close()

    def __test_coherence_parameter_data(self):
        if (self.instance.pressure_in.value > self.instance.lb_press_up.value
                and self.instance.pressure_in.value <
                self.instance.ub_press_up.value):
            # raise Exception
            logger.exception(
                "Incoherence between feed pressure and pressure up's bounds"
                "pressure_in > lb_press_up and pressure_in < ub_press_up")
            raise ValueError(
                "Incoherence between feed pressure and bounds on pressure up"
                "pressure_in > lb_press_up and pressure_in < ub_press_up")

        elif self.instance.pressure_in.value > self.instance.ub_press_up.value:
            # raise Exception
            logger.exception(
                "Incoherence between feed pressure and pressure up's bounds"
                "pressure_in > ub_press_up")
            raise ValueError(
                "Incoherence between feed pressure and bounds on pressure up"
                "pressure_in > ub_press_up")


        # Vacuum Pump coherence
        if ((self.parameter.vp and self.instance.ub_press_down.value > 1.0) or
            (not self.parameter.vp and
             self.instance.lb_press_down.value < 1.0)):
            # raise Exception
            logger.exception(
                " Incoherence between Vacuum Pump and pressure down values")

            raise ValueError(
                "Incoherence between pressure down and Vacuum pump")

        # Permeability can be variable only for bi-components
        if (self.parameter.variable_perm):
            if len(self.instance.components) != 2:
                logger.exception(
                    "Permeability variable is authorised only for bi-components [{} != 2]"
                    .format(len(self.instance.components)))

                raise ValueError(
                    "Error: Permeability is variable only for bi-components")

        # check if pressure_prod is valid
        if self.instance.pressure_prod.value != -1:
            if not (self.instance.ub_press_up.value <=
                    self.instance.pressure_prod.value or
                    self.instance.lb_press_up.value >=
                    self.instance.pressure_prod.value):
                # raise Exception on pressure_prod values
                logger.exception(
                    "pressure_prod value is misconfigured with pressure bounds")
                raise ValueError(
                    "we need to split in several sub cases (combinatorics)")

        # check if pressure_prod's presence is valiated
        if self.instance.pressure_prod.value != -1:
            if not self.parameter.uniform_pup or self.parameter.variable_perm:
                logger.exception(
                    'Incoherence when defining pressure_prod :'
                    '[pressure are not uniform or permeability is variable]')

                raise ValueError(
                    "Incoherence when defining pressure_prod :"
                    "[pressure must be uniform and permeability must be fixed]")

    def __prevent_loops_upper_bound_splitted_flows(self):
        # upper bound on flows splitted : loop case
        for s in self.instance.states:
            self.instance.ub_splitRET_frac[s, s] = 0.9
            self.instance.ub_splitPERM_frac[s, s] = 0.9
            self.instance.ub_splitRET_frac_full[s, s] = 0.9
            self.instance.ub_splitPERM_frac_full[s, s] = 0.9

    def load_permeability_data(self):
        """Loading permeability informations into desing process model's instance_file

        from permeability data dictionary.
        """
        # permeability varaibles bounds
        if self.parameter.variable_perm:
            # fix ref component permeability bound
            self.membrane_behavior.fix_ref_perm_bound(self.instance,
                                                      self.parameter)

            # Check the validity of alpha bounds
            self.membrane_behavior.check_alpha_validity(self.instance)

            # Calculate bounds for permeability of the other element
            self.membrane_behavior.init_other_component_perm_bounds(
                self.instance)

        else:
            # Load perm data from permeability_data [parser from builder]
            for type_mem in self.permeability_data.keys():
                list_mem = self.membrane_behavior.permeability_data[
                    type_mem].which_mem
                for state in list_mem:
                    self.instance.mem_type[state] = type_mem
            self.membrane_behavior.set_permeabiliy_when_fixed(
                self.instance, self.parameter)

        # Update thickness param from permeability_data
        for type_mem in self.permeability_data.keys():
            self.instance.thickness[type_mem] = self.permeability_data[
                type_mem].thickness

    def generate_labels_and_initvars(self):
        """Generation of variables labels and initialization of variables."""
        # Generate vars_init_status dictionary elements
        # which tracks variables initialization status
        self.parameter.labels = ComponentUID.generate_cuid_string_map(
            self.instance)

        for var in self.instance.component_data_objects(pe.Var, active=True):
            self.parameter.init_status[self.parameter.labels[var]] = False

    def create_process_instance(self, fname):
        """Creation of design process model's instance (`PYOMO construction`).

        Args:
            fname (`str`) : input filename containing instance description
        """
        # assert self.abstractModel is an abstractmodel
        # update this self.filename with the number of membranes
        self.__insert_datafile_line(fname, insert_position=3)

        try:
            self.instance = self.abstractModel.create_instance(self.filename)

        except Exception as e:
            logger.exception('Problem with file format %s', fname)
            raise e
        else:
            """ Test if some conditions are respected, ensuring that instance
            reflect a real world instance.
            """
            # initialize everything to zero except for area and pressure
            initZero(self.instance)

            self.__test_coherence_parameter_data()
            self.__prevent_loops_upper_bound_splitted_flows()

            self.instance.ub_feed = self.instance.FEED.value
            self.instance.ub_feed_tot = 2 * self.instance.FEED.value
            #print('ub_feed_tot =',self.instance.ub_feed_tot)
            logger.info('alors gros ca getz ?')

            # self.instance.ub_out_prod = self.instance.FEED.value
            # self.instance.ub_out_waste = self.instance.FEED.value

            self.load_permeability_data()
            self.generate_labels_and_initvars()

            # deactivate simplified model objective
            self.instance.simplified_obj.deactivate()


        finally:
            # states are already initialized via fname
            self.__delete_datafile_line(delete_position=3)

    def __flow_conservation_overall_sytem_constraint(self):
        """ System flow conservation :
            FEED equals output (RET+PERM). """

        def balanceGlobal_rule(model):
            return model.FEED == sum(model.splitOutRET[s] +
                                     model.splitOutPERM[s]
                                     for s in model.states)

        self.abstractModel.balanceGlobal = pe.Constraint(
            rule=balanceGlobal_rule)

        # System output in terms of Flows and Flows-Composition
        def totalProdFlux_rule(model):
            try:
                return (model.OUT_prod == sum(
                    model.splitOutPERM[s]
                    for s in model.states
                    if self.permeability_data[
                        model.mem_type[s].value].mem_out_prod == "PERM") +
                        sum(model.splitOutRET[s]
                            for s in model.states
                            if self.permeability_data[
                                model.mem_type[s].value].mem_out_prod == "RET"))
            except KeyError:
                logger.error(
                    "Information on selected membrane type is not complete")
                raise

            except Exception:
                logger.error(
                    "Information on selected membrane type is not complete")
                raise

        self.abstractModel.totalProdFlux = pe.Constraint(
            rule=totalProdFlux_rule)

        # collect for final
        def totalwasteFlux_rule(model):
            # here we sum the part of RET if the product is in PERM
            # Same, if the product is in RET, we take the part of PERM.
            try:
                return (model.OUT_waste == sum(
                    model.splitOutRET[s]
                    for s in model.states
                    if self.permeability_data[
                        model.mem_type[s].value].mem_out_prod == "PERM") +
                        sum(model.splitOutPERM[s]
                            for s in model.states
                            if self.permeability_data[
                                model.mem_type[s].value].mem_out_prod == "RET"))
            except Exception:
                logger.error(
                    "Information on selected membrane type is not complete")
                raise

        self.abstractModel.totalwasteFlux = pe.Constraint(
            rule=totalwasteFlux_rule)

        # composition of prod flow
        # TODO: this constraint depends on membranes' types
        # for the moment we consider the case of prod-selective membranes
        # these constraints are enough to define also the composition of the
        # secondary product/waste

        def build_XOUTprod_rule(model, j):
            try:
                return (model.XOUT_prod[j] * model.OUT_prod == sum(
                    model.X_PERM_mem[s, j] * model.splitOutPERM[s]
                    for s in model.states
                    if self.permeability_data[
                        model.mem_type[s].value].mem_out_prod == "PERM") +
                        sum(model.X_RET_mem[s, j] * model.splitOutRET[s]
                            for s in model.states
                            if self.permeability_data[
                                model.mem_type[s].value].mem_out_prod == "RET"))
            except Exception:
                logger.error(
                    "Information on selected membrane type is not complete")
                raise

        self.abstractModel.build_XOUTprod = pe.Constraint(
            self.abstractModel.components, rule=build_XOUTprod_rule)

        def build_XOUTwaste_rule(model, j):
            try:
                return (model.XOUT_waste[j] * model.OUT_waste == sum(
                    model.X_RET_mem[s, j] * model.splitOutRET[s]
                    for s in model.states
                    if self.permeability_data[
                        model.mem_type[s].value].mem_out_prod == "PERM") +
                        sum(model.X_PERM_mem[s, j] * model.splitOutPERM[s]
                            for s in model.states
                            if self.permeability_data[
                                model.mem_type[s].value].mem_out_prod == "RET"))
            except Exception:
                logger.error(
                    "Information on selected membrane type is not complete")
                raise

        self.abstractModel.build_XOUTwaste = pe.Constraint(
            self.abstractModel.components, rule=build_XOUTwaste_rule)

    def __flow_conservation_membranes_levels_constraint(self):
        """ System flow conservation :
            FEED in membrane equals membrane output (RET+PERM). """

        def balanceMem_rule(model, s):
            return (model.Feed_mem[s] == model.Flux_RET_mem[s] +
                    model.Flux_PERM_mem[s])

        self.abstractModel.balanceMem = pe.Constraint(self.abstractModel.states,
                                                      rule=balanceMem_rule)

    def __superstructure_flow_conservation_constraint(self):
        """Flow conservation constraints related to the superstructure."""

        # Split for initial FEED
        def balanceFEEDsplit_rule(model):
            """ Initial feed spliting conservation flow constraint  """
            return model.FEED == sum(model.splitFEED[s] for s in model.states)

        self.abstractModel.balanceFEEDsplit = pe.Constraint(
            rule=balanceFEEDsplit_rule)

        def mixEntranceF_rule(model, s):
            """ Flow conservation on each membrane feed """
            return model.Feed_mem[s] == (
                sum(model.splitRET[s1, s] + model.splitPERM[s1, s]
                    for s1 in model.states) + model.splitFEED[s])

        self.abstractModel.mixEntranceF = pe.Constraint(
            self.abstractModel.states, rule=mixEntranceF_rule)

        # same constraint but with more precision with components
        def mixEntranceX_rule(model, s, j):
            """ Flow conservation on each membrane feed """
            flow_from_other_membranes = sum(
                model.splitRET[s1, s] * model.X_RET_mem[s1, j] +
                model.splitPERM[s1, s] * model.X_PERM_mem[s1, j]
                for s1 in model.states)

            flow_from_feed = model.splitFEED[s] * model.XIN[j]

            init_mem_flow = model.XIN_mem[s, j] * model.Feed_mem[s]

            return (init_mem_flow == flow_from_other_membranes + flow_from_feed)

        self.abstractModel.mixEntranceX = pe.Constraint(
            self.abstractModel.states,
            self.abstractModel.components,
            rule=mixEntranceX_rule)

        # splitting RET flows
        def balanceSplitRetF_rule(model, s):
            """RET conservation flows.

            (quantity of outstream and splited flows RET for others
            membranes)."""

            return (model.Flux_RET_mem[s] == sum(
                model.splitRET[s, s1] for s1 in model.states) +
                    model.splitOutRET[s])

        self.abstractModel.balanceSplitRetF = pe.Constraint(
            self.abstractModel.states, rule=balanceSplitRetF_rule)

        def balanceSplitPermF_rule(model, s):
            """ PERM conservation flows.

            (quantity of outstream and splited flows PERM for
            others membranes).
            """

            return (model.Flux_PERM_mem[s] == sum(
                model.splitPERM[s, s1] for s1 in model.states) +
                    model.splitOutPERM[s])

        self.abstractModel.balanceSplitPermF = pe.Constraint(
            self.abstractModel.states, rule=balanceSplitPermF_rule)

    def __fractions_components_constraint(self):
        """ Composition coherence (total fractions==1)."""

        # System
        # RET
        def balanceXOUTprod_rule(model):
            return sum(model.XOUT_prod[j] for j in model.components) == 1

        self.abstractModel.balanceXOUTprod = pe.Constraint(
            rule=balanceXOUTprod_rule)

        # PERM
        def balanceXOUTwaste_rule(model):
            return sum(model.XOUT_waste[j] for j in model.components) == 1

        self.abstractModel.balanceXOUTwaste = pe.Constraint(
            rule=balanceXOUTwaste_rule)

        # State (Membrane)
        # RET
        def balanceXOUTR0_rule(model, s):
            return sum(model.X_RET_mem[s, j] for j in model.components) == 1

        self.abstractModel.balanceXOUTR0 = pe.Constraint(
            self.abstractModel.states, rule=balanceXOUTR0_rule)

        # PERM
        def balanceXOUTR1_rule(model, s):
            return sum(model.X_PERM_mem[s, j] for j in model.components) == 1

        self.abstractModel.balanceXOUTR1 = pe.Constraint(
            self.abstractModel.states, rule=balanceXOUTR1_rule)

    def __pressures_constraint(self):
        """ Coherence pressure and ordering constraint.
        constraint which will define that pressure_down <= min(pressure_up).
        Ordering on the membranes with respect of pressures_up (if not uniform)
        """

        def coherence_pressures_rule(model, s, s_up):
            if (self.parameter.uniform_pup):
                return model.pressure_down[s] <= model.pressure_up
            else:
                # FIXME: case failed
                # function last() return the last element
                # of an ordered Pyomo Set
                # return (
                #     model.pressure_down[s]
                #     <= model.pressure_up[model.States.last()]
                #     )

                # my proposition
                return (model.pressure_down[s] <= model.pressure_up[s_up])

        self.abstractModel.coherence_pressures = pe.Constraint(
            self.abstractModel.states,
            self.abstractModel.states,
            rule=coherence_pressures_rule)

        if not self.parameter.uniform_pup:

            def order_pressure_rule(model, s):
                if s > 1:
                    return model.pressure_up[s] <= model.pressure_up[s - 1]
                else:
                    return pe.Constraint.Skip

            self.abstractModel.orderMembranes = pe.Constraint(
                self.abstractModel.states, rule=order_pressure_rule)

    def __no_isolated_membrane_constraint(self):
        """ Removing Isolated membranes. """

        def noIsolated_rule(model, s):
            # TODO: Ask bernerdetta to # REVIEW:  this constraint
            outflow = sum(model.splitRET[s, s1] + model.splitPERM[s, s1]
                          for s1 in model.states
                          if s1 != s)

            inflow = sum(model.splitRET[s1, s] + model.splitPERM[s1, s]
                         for s1 in model.states
                         if s1 != s)

            return outflow + inflow >= model.tol_zero

        self.abstractModel.noIsolated = pe.Constraint(self.abstractModel.states,
                                                      rule=noIsolated_rule)

    # may be move this part in variables declarations
    def __flow_composition_bound_constraint(self):
        """ Imposing ub/lb on ret and perm flow composition variables. """

        def additionalMaxPercProd_rule(model, c):
            return model.XOUT_prod[c] <= model.ub_perc_prod[c]

        self.abstractModel.additionalMaxPercProd = pe.Constraint(
            self.abstractModel.components, rule=additionalMaxPercProd_rule)

        # purity constraint if final product located in prod
        def additionalMinPercProd_rule(model, c):
            return model.XOUT_prod[c] >= model.lb_perc_prod[c]

        self.abstractModel.additionalMinPercProd = pe.Constraint(
            self.abstractModel.components, rule=additionalMinPercProd_rule)

        def additionalMaxPercwaste_rule(model, c):
            return model.XOUT_waste[c] <= model.ub_perc_waste[c]

        self.abstractModel.additionalMaxPercwaste = pe.Constraint(
            self.abstractModel.components, rule=additionalMaxPercwaste_rule)

        # purity constraint if final product located in waste
        def additionalMinPercwaste_rule(model, c):
            return model.XOUT_waste[c] >= model.lb_perc_waste[c]

        self.abstractModel.additionalMinPercwaste = pe.Constraint(
            self.abstractModel.components, rule=additionalMinPercwaste_rule)

    def __coherence_frac_variables_constraint(self):
        """ Additional constraint to have coherence with frac variables. """

        def coherence_splitRET_rule(model, s, s1):
            return (model.splitRET[s, s1] == model.splitRET_frac[s, s1] *
                    model.Flux_RET_mem[s])

        self.abstractModel.coherence_splitRET = pe.Constraint(
            self.abstractModel.states,
            self.abstractModel.states,
            rule=coherence_splitRET_rule)

        def coherence_splitPERM_rule(model, s, s1):
            return (model.splitPERM[s, s1] == model.splitPERM_frac[s, s1] *
                    model.Flux_PERM_mem[s])

        self.abstractModel.coherence_splitPERM = pe.Constraint(
            self.abstractModel.states,
            self.abstractModel.states,
            rule=coherence_splitPERM_rule)

        # directly out the system
        def coherence_splitOutRET_rule(model, s):
            return (model.splitOutRET[s] == model.splitOutRET_frac[s] *
                    model.Flux_RET_mem[s])

        self.abstractModel.coherence_splitOutRET = pe.Constraint(
            self.abstractModel.states, rule=coherence_splitOutRET_rule)

        def coherence_splitOutPERM_rule(model, s):
            return (model.splitOutPERM[s] == model.splitOutPERM_frac[s] *
                    model.Flux_PERM_mem[s])

        self.abstractModel.coherence_splitOutPERM = pe.Constraint(
            self.abstractModel.states, rule=coherence_splitOutPERM_rule)

        def coherence_FEED_rule(model, s):
            return model.splitFEED[s] == model.splitFEED_frac[s] * model.FEED

        self.abstractModel.coherence_FEED = pe.Constraint(
            self.abstractModel.states, rule=coherence_FEED_rule)

    def __recovery_constraint(self):

        def limiting_product_loss_rule(model):
            """ The system must product at least normalized_product_qt """
            # # TODO: if product in ret then use perm in this constraint
            # else use ret
            return (model.OUT_prod * model.XOUT_prod[model.final_product.value]
                    >= (model.normalized_product_qt * model.FEED *
                        model.XIN[model.final_product.value]))

        self.abstractModel.limiting_product_loss = pe.Constraint(
            rule=limiting_product_loss_rule)

    def __activated_constraint_simplified_model(self):
        # Simplified model - modified constraints
        # no loss of component flow: FEED_component = out_component (RET+PERM)
        def BalanceComponentMem_simplified_rule(model, s, j):
            tmp = (model.Flux_RET_mem[s] * model.X_RET_mem[s, j] +
                   model.Flux_PERM_mem[s] * model.X_PERM_mem[s, j])

            return model.Feed_mem[s] * model.XIN_mem[s, j] == tmp

        self.abstractModel.BalanceComponentMem_simplified = pe.Constraint(
            self.abstractModel.states,
            self.abstractModel.components,
            rule=BalanceComponentMem_simplified_rule)

    # def __no_loss_flow_constraint(self):
    #     """ No loss of components percentage in output. """
    #     def noLossRET_rule(model, s):
    #         return (
    #             sum(model.splitRET_frac[s, s1] for s1 in model.states)
    #             + model.splitOutRET_frac[s] == 1
    #             )
    #
    #     self.abstractModel.noLossRET = pe.Constraint(
    #         self.abstractModel.states,
    #         rule=noLossRET_rule)
    #
    #     def noLossPERM_rule(model, s):
    #         return (
    #             sum(model.splitPERM_frac[s, s1] for s1 in model.states)
    #             + model.splitOutPERM_frac[s] == 1
    #             )
    #     self.abstractModel.noLossPERM = pe.Constraint(
    #         self.abstractModel.states,
    #         rule=noLossPERM_rule)
