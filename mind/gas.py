"""Defining gas optimization model of membrane design process."""

import logging

import pyomo.environ as pe

from mind.membranes import MembranesTypes
from mind.system import MembranesDesignModel
from mind import obj

# logging variable
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)
handler = logging.StreamHandler()
# handler = logging.FileHandler(filename)
logger.addHandler(handler)
formatter = logging.Formatter(fmt='[%(asctime)s] %(levelname)s : %(message)s',
                              datefmt='%a, %d %b %Y %H:%M:%S')
handler.setFormatter(formatter)


class MembranesDesignGas(MembranesDesignModel):
    """Implement `MembranesDesignModel` class.
    It define parameter, varaibles and some constraint of `gas optimization
    model`.

    Attributes:
        parameter (`mind.builder.Configuration`): design process configuration

        permeability_data (`DICT`): membrane permeability's data information

        abstractModel (`pyomo.environ.AbstractModel`): design process abstract model

        instance (`pyomo.environ.AbstractModel.create_instance`): design process model's instance

        membrane_behavior (`mind.membranes.MembranesTypes`): membrane representation object

    """

    def __init__(self, conf_param, perm_data, eco_file):
        self.parameter = conf_param
        self.permeability_data = perm_data
        try:
            self.obj_ = obj.ObjFunction(eco_file, self.parameter)

        except Exception as e:
            logger.exception("Economic file is not correctly setted : %s",
                             eco_file)
            raise

        self.abstractModel = pe.AbstractModel()
        self.instance = None
        super().init_model()

    def __membranes_stages_levels(self):
        """Callback deleguated to create membrane's object."""

        self.membrane_behavior = MembranesTypes(self.abstractModel,
                                                self.permeability_data)

        self.membrane_behavior.set_membranes_types()

        # define thickness parameter
        self.membrane_behavior.set_tickness()

        # define permeability (param or variable)
        self.membrane_behavior.set_permeability(self.parameter)

    def set_parameters(self):
        """Settings optimization model parameters."""
        super().set_parameters()
        self.__membranes_stages_levels()

    def __flow_rate_cells_variables(self):
        """Defining variables keeping flows quantity in cells stages levels."""
        # Variables related to single cell in each membrane
        # flow rate of the feed at the entrance of the cell i of a membrane s
        self.abstractModel.Feed_cell = pe.Var(
            self.abstractModel.states,
            self.abstractModel.N,
            bounds=(0.0, self.abstractModel.ub_feed_tot))
        # flow rate of the ret flux at the outlet of the cell i of a membrane s
        self.abstractModel.Flux_RET_cell = pe.Var(
            self.abstractModel.states,
            self.abstractModel.N,
            bounds=(0.0, self.abstractModel.ub_feed_tot))
        # flow rate of the perm flux at the outlet of the cell i
        # of a membrane s
        self.abstractModel.Flux_PERM_cell = pe.Var(
            self.abstractModel.states,
            self.abstractModel.N,
            bounds=(0.0, self.abstractModel.ub_feed_tot))

    def __component_flow_rate_cells_variables(self):
        """Defining variables keeping component percentage of
        flows quantity in cells stages levels.
        """

        # fract. of a component at the inlet of the cell i of a membrane s
        self.abstractModel.XIN_cell = pe.Var(self.abstractModel.states,
                                             self.abstractModel.components,
                                             self.abstractModel.N,
                                             bounds=(0.0, 1.0))
        # fract. of a component for the ret flux at the outlet of
        # cell i of membrane s
        self.abstractModel.X_RET_cell = pe.Var(self.abstractModel.states,
                                               self.abstractModel.components,
                                               self.abstractModel.N,
                                               bounds=(0.0, 1.0))
        # fract. of a component for the perm flux at the outlet of cell i
        # of membrane s
        self.abstractModel.X_PERM_cell = pe.Var(self.abstractModel.states,
                                                self.abstractModel.components,
                                                self.abstractModel.N,
                                                bounds=(0.0, 1.0))

    def set_variables(self):
        """Setting all necessary variables to build optimization model. """
        super().set_variables()
        # cells levels variables
        self.__flow_rate_cells_variables()
        self.__component_flow_rate_cells_variables()

    def create_process_instance(self, fname):
        """Creation of the instance of the design process model object
        (`pyomo construction`). """
        super().create_process_instance(fname)
        self.fixing_unused_cells_var()

    def __flow_conservation_cells_levels_constraint(self):
        """Constraint relative to system flow conservation.

        FEED in cell equals cell output (RET+PERM). """

        def balanceCellMem_rule(model, s, i):
            return (model.Feed_cell[s, i] == model.Flux_RET_cell[s, i] +
                    model.Flux_PERM_cell[s, i])

        self.abstractModel.balanceCellMem = pe.Constraint(
            self.abstractModel.states,
            self.abstractModel.N,
            rule=balanceCellMem_rule)

        # FEED_component = out_component (RET+PERM)
        def BalanceComponentCellMem_rule(model, s, j, i):
            return (model.Feed_cell[s, i] * model.XIN_cell[s, j, i] == (
                model.Flux_RET_cell[s, i] * model.X_RET_cell[s, j, i] +
                model.Flux_PERM_cell[s, i] * model.X_PERM_cell[s, j, i]))

        self.abstractModel.BalanceComponentCellMem = pe.Constraint(
            self.abstractModel.states,
            self.abstractModel.components,
            self.abstractModel.N,
            rule=BalanceComponentCellMem_rule)

    def __correlation_between_cell_contraint(self):
        """Constraint relative to the connection between cells.

        RET cell i is the Feed of cell i+1 and Composition of RET cell i
        is the composition in input at cell i+1. """

        # Flow
        def ConnectionFeeds_cellMem_rule(model, s, i):
            mem = s - 1
            if i + 1 <= self.parameter.discretisation[mem]:
                # if not last cell of mem discretisation
                return model.Feed_cell[s, i + 1] == model.Flux_RET_cell[s, i]
            else:
                return pe.Constraint.Skip

        self.abstractModel.ConnectionFeeds_cellMem = pe.Constraint(
            self.abstractModel.states,
            self.abstractModel.N_minuslast,
            rule=ConnectionFeeds_cellMem_rule)

        # components
        def ConnectionPercinsMem_rule(model, s, j, i):
            mem = s - 1
            if i + 1 <= self.parameter.discretisation[mem]:
                return model.XIN_cell[s, j, i + 1] == model.X_RET_cell[s, j, i]
            else:
                return pe.Constraint.Skip

        self.abstractModel.ConnectionPercinsMem = pe.Constraint(
            self.abstractModel.states,
            self.abstractModel.components,
            self.abstractModel.N_minuslast,
            rule=ConnectionPercinsMem_rule)

    def __cell_fractions_components_constraint(self):
        """Constraint relative to the satisfaction of the coherence of components.

        Composition coherence (total fractions==1)."""

        # State-Cell
        def balanceXRetCellMem_rule(model, s, i):
            return sum(model.X_RET_cell[s, j, i] for j in model.components) == 1

        self.abstractModel.balanceXRetCellMem = pe.Constraint(
            self.abstractModel.states,
            self.abstractModel.N,
            rule=balanceXRetCellMem_rule)

        def balanceXPermCellMem_rule(model, s, i):
            return sum(
                model.X_PERM_cell[s, j, i] for j in model.components) == 1

        self.abstractModel.balanceXPermCellMem = pe.Constraint(
            self.abstractModel.states,
            self.abstractModel.N,
            rule=balanceXPermCellMem_rule)

    # interconnection
    def __correlation_membrane_cell_contraint(self):
        """Constraint relative to the connection between membranes and cells.

        Equation that model the correlation between membranes and cells. """

        # Input Feed in a membrane == Input Feed in first cell
        def connetionFeed_FeedCell_rule(model, s):
            return model.Feed_mem[s] == model.Feed_cell[s, 1]

        self.abstractModel.connetionFeed_FeedCell = pe.Constraint(
            self.abstractModel.states, rule=connetionFeed_FeedCell_rule)

        # Same for percentages of each components
        def xinPercin_rule(model, s, j):
            return model.XIN_mem[s, j] == model.XIN_cell[s, j, 1]

        self.abstractModel.xinPercin = pe.Constraint(
            self.abstractModel.states,
            self.abstractModel.components,
            rule=xinPercin_rule)

        # Retentated membrane flow is the last cell retentated flow
        def FluxRETMem_rule(model, s):
            mem = s - 1
            # last_cell_index = model.n.value
            last_cell_index = self.parameter.discretisation[mem]
            return (
                model.Flux_RET_mem[s] == model.Flux_RET_cell[s,
                                                             last_cell_index])

        self.abstractModel.FluxRETMem = pe.Constraint(self.abstractModel.states,
                                                      rule=FluxRETMem_rule)

        # Retentated membrane composition is
        # the last cell retentated composition
        def XoutRETMem_rule(model, s, j):
            mem = s - 1
            # last_cell_index = model.n.value
            last_cell_index = self.parameter.discretisation[mem]
            return (model.X_RET_mem[s, j] == model.X_RET_cell[s, j,
                                                              last_cell_index])

        self.abstractModel.XoutRETMem = pe.Constraint(
            self.abstractModel.states,
            self.abstractModel.components,
            rule=XoutRETMem_rule)

        # Permeated membrane flow of a membrane is the sum
        # of all permeated flows in the cells Flow
        def FluxPERMMem_rule(model, s):
            return model.Flux_PERM_mem[s] == sum(
                model.Flux_PERM_cell[s, i] for i in model.N)

        self.abstractModel.FluxPERMMem = pe.Constraint(
            self.abstractModel.states, rule=FluxPERMMem_rule)

        # Composition (components fractions)
        def XoutPERMMem_rule(model, s, j):
            return (model.X_PERM_mem[s, j] * model.Flux_PERM_mem[s] == sum(
                model.Flux_PERM_cell[s, i] * model.X_PERM_cell[s, j, i]
                for i in model.N))

        self.abstractModel.XoutPERMMem = pe.Constraint(
            self.abstractModel.states,
            self.abstractModel.components,
            rule=XoutPERMMem_rule)

    def define_process_contraints(self):
        """Wrapper which generate contraints of the optimization model """
        super().define_process_contraints()

        self.__flow_conservation_cells_levels_constraint()
        self.__correlation_between_cell_contraint()

        # contraint depending of the type of membrane
        self.membrane_behavior.set_mem_behavior_contraint(self.parameter)

        self.__cell_fractions_components_constraint()
        self.__correlation_membrane_cell_contraint()

        # Membrane Permeability Equation
        self.membrane_behavior.simplified_mem_behavior_contraint(self.parameter)

        if self.parameter.variable_perm:
            self.membrane_behavior.robeson_equation_constraint(self.parameter)
            self.membrane_behavior.robeson_Selectivity(self.parameter)
            # self.membrane_behavior.mem_type_same_value(self.parameter)

    # solve reduced problem with total area (like a single large cell)
    def simplified_split_flows_bound(self):
        """Fixing some split_flows variables bounds in simplified model."""
        for s in self.instance.states:
            for s1 in self.instance.states:
                tmpA = 0.6 * self.instance.splitRET_frac[s, s1].value
                tmpA = max(self.instance.lb_splitRET_frac_full[s, s1].value,
                           tmpA)
                # redundant
                tmpA = min(self.instance.ub_splitRET_frac_full[s, s1].value,
                           tmpA)
                self.instance.lb_splitRET_frac[s, s1] = tmpA

                tmpA = 0.6 * self.instance.splitPERM_frac[s, s1].value
                tmpA = max(self.instance.lb_splitPERM_frac_full[s, s1].value,
                           tmpA)
                # redundant
                tmpA = min(self.instance.ub_splitPERM_frac_full[s, s1].value,
                           tmpA)
                self.instance.lb_splitPERM_frac[s, s1] = tmpA

                tmpA = 1.4 * self.instance.splitRET_frac[s, s1].value
                # redundant
                tmpA = max(self.instance.lb_splitRET_frac_full[s, s1].value,
                           tmpA)
                tmpA = min(self.instance.ub_splitRET_frac_full[s, s1].value,
                           tmpA)
                self.instance.ub_splitRET_frac[s, s1] = tmpA

                tmpA = 1.4 * self.instance.splitPERM_frac[s, s1].value
                # redundant
                tmpA = max(self.instance.lb_splitPERM_frac_full[s, s1].value,
                           tmpA)
                tmpA = min(self.instance.ub_splitPERM_frac_full[s, s1].value,
                           tmpA)
                self.instance.ub_splitPERM_frac[s, s1] = tmpA

    def simplified_model(self):
        """Set simplified model.

        Set the model object to a reduced one, which is easy to perform.

        Raises:
            Exception : `If` model's instance is `None` or `not constructed`

        """

        try:
            assert self.instance is not None and self.instance.is_constructed()
        except Exception:
            logger.exception("Invalid pyomo model instance ...")
            raise

        # putting some bounds on flows frac variables before solve simpl
        self.simplified_split_flows_bound()

        if self.parameter.variable_perm:
            self.instance.Permeability.fix()

        # setting up the constraints
        # removing constraints related to cells
        self.instance.balanceCellMem.deactivate()
        self.instance.BalanceComponentCellMem.deactivate()
        self.instance.ConnectionFeeds_cellMem.deactivate()
        self.instance.ConnectionPercinsMem.deactivate()
        self.instance.mainEquationMem.deactivate()
        self.instance.connetionFeed_FeedCell.deactivate()
        self.instance.xinPercin.deactivate()
        self.instance.FluxRETMem.deactivate()
        self.instance.XoutRETMem.deactivate()
        self.instance.FluxPERMMem.deactivate()
        self.instance.XoutPERMMem.deactivate()
        self.instance.balanceXRetCellMem.deactivate()
        self.instance.balanceXPermCellMem.deactivate()

        # removing performance constraints
        self.instance.additionalMaxPercProd.deactivate()
        self.instance.additionalMinPercProd.deactivate()
        self.instance.additionalMaxPercwaste.deactivate()
        self.instance.additionalMinPercwaste.deactivate()
        self.instance.limiting_product_loss.deactivate()
        # removing objective function
        self.instance.obj.deactivate()
        self.instance.simplified_obj.activate()

        # fixing unused variables
        self.instance.Feed_cell.fix()
        self.instance.Flux_RET_cell.fix()
        self.instance.Flux_PERM_cell.fix()
        self.instance.XIN_cell.fix()
        self.instance.X_RET_cell.fix()
        self.instance.X_PERM_cell.fix()

        # activate simplified model constraints
        self.instance.BalanceComponentMem_simplified.activate()
        self.instance.mainEquationMem_simplified.activate()

        self.instance.noIsolated.deactivate()

        self.instance.preprocess()

    def fixing_unused_cells_var(self):
        """Fixing unused cells variables before simplied model solving."""
        for mem in self.instance.states:
            # Pyomo index begin with 1 and python list with 0
            if self.instance.n.value != self.parameter.discretisation[mem - 1]:
                begin_index = self.parameter.discretisation[mem - 1] + 1
                for cell_index in range(begin_index, self.instance.n.value + 1):
                    self.instance.Feed_cell[mem, cell_index].fix(0)
                    self.instance.Flux_RET_cell[mem, cell_index].fix(0)
                    self.instance.Flux_PERM_cell[mem, cell_index].fix(0)
                    # for j in self.instance.components:
                    #     self.instance.XIN_cell[mem, j, cell_index].fix(0)
                    #     self.instance.X_RET_cell[mem, j, cell_index].fix(0)
                    #     self.instance.X_PERM_cell[mem, j, cell_index].fix(0)

        self.instance.preprocess()

    # back to the  original model
    def restore_original_model(self):
        """ Retore the model object.

        This function is called after the modification of the original model,
        especially by simplied model.
        """
        assert self.instance is not None and self.instance.is_constructed()
        # reset bounds
        for s in self.instance.states:
            for s1 in self.instance.states:
                self.instance.lb_splitRET_frac[s, s1] = (
                    self.instance.lb_splitRET_frac_full[s, s1].value)

                self.instance.lb_splitPERM_frac[s, s1] = (
                    self.instance.lb_splitPERM_frac_full[s, s1].value)

                self.instance.ub_splitRET_frac[s, s1] = (
                    self.instance.ub_splitRET_frac_full[s, s1].value)

                self.instance.ub_splitPERM_frac[s, s1] = (
                    self.instance.ub_splitPERM_frac_full[s, s1].value)

        if self.parameter.variable_perm:
            self.instance.Permeability.unfix()

        # restore constraints related to cells
        self.instance.balanceCellMem.activate()
        self.instance.BalanceComponentCellMem.activate()
        self.instance.ConnectionFeeds_cellMem.activate()
        self.instance.ConnectionPercinsMem.activate()
        self.instance.mainEquationMem.activate()
        self.instance.connetionFeed_FeedCell.activate()
        self.instance.xinPercin.activate()
        self.instance.FluxRETMem.activate()
        self.instance.XoutRETMem.activate()
        self.instance.FluxPERMMem.activate()
        self.instance.XoutPERMMem.activate()
        self.instance.balanceXRetCellMem.activate()
        self.instance.balanceXPermCellMem.activate()

        # restore performance constraints
        self.instance.additionalMaxPercProd.activate()
        self.instance.additionalMinPercProd.activate()
        self.instance.additionalMaxPercwaste.activate()
        self.instance.additionalMinPercwaste.activate()
        self.instance.limiting_product_loss.activate()

        # restoring objective function
        self.instance.obj.activate()
        self.instance.simplified_obj.deactivate()

        # unfixing unused variables
        self.instance.Feed_cell.unfix()
        self.instance.Flux_RET_cell.unfix()
        self.instance.Flux_PERM_cell.unfix()
        self.instance.XIN_cell.unfix()
        self.instance.X_RET_cell.unfix()
        self.instance.X_PERM_cell.unfix()

        self.fixing_unused_cells_var()
        # remove simplified model constraints
        self.instance.BalanceComponentMem_simplified.deactivate()
        self.instance.mainEquationMem_simplified.deactivate()

        if self.parameter.num_membranes > 1:
            self.instance.noIsolated.activate()

        self.instance.preprocess()
