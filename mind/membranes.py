"""This module describe the membranes object.

By this module, we delegate the creation of thickness and permeability
parameters.
"""

import logging

import pyomo.environ as pe

# logging variable
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)
handler = logging.StreamHandler()
# handler = logging.FileHandler(filename)
logger.addHandler(handler)
formatter = logging.Formatter(fmt='[%(asctime)s] %(levelname)s : %(message)s',
                              datefmt='%a, %d %b %Y %H:%M:%S')
handler.setFormatter(formatter)


class MembranesTypes():
    """Decribe the behavior of membranes type.

    When an instance of this class is created, its mean that there at least
    two differents kinds of membranes.

    Args:
        model (Pyomo.abstractmodel): abstractModel of the pyomo model.
    """

    def __init__(self, model, perm_data):
        self._model = model
        self.permeability_data = perm_data

    def set_membranes_types(self):
        self._model.mem_types_set = pe.Set(ordered=True)
        # type is assigned to each membrane as a parameter
        # (in future extensions can be a variable)
        self._model.mem_type = pe.Param(self._model.states,
                                        within=self._model.mem_types_set,
                                        mutable=True,
                                        default="A")

    def set_tickness(self) -> None:
        # thickness of the membrane for a given state
        self._model.thickness = pe.Param(self._model.mem_types_set,
                                         default=1.0,
                                         mutable=True)

    def set_permeability(self, parameter):
        if not parameter.variable_perm:
            # fixed permeabilities are entered from the input
            self._model.Permeability = pe.Param(self._model.components,
                                                self._model.states,
                                                default=0.1,
                                                mutable=True)
        else:
            # Different types of membranes exist
            self._model.ub_permeability = pe.Param(self._model.components,
                                                   self._model.mem_types_set,
                                                   default=10,
                                                   mutable=True)

            self._model.lb_permeability = pe.Param(self._model.components,
                                                   self._model.mem_types_set,
                                                   default=0.1,
                                                   mutable=True)

            def perm_bounds_rule(model, j, s):
                type = model.mem_type[s].value
                return (model.lb_permeability[j, type],
                        model.ub_permeability[j, type])

            self._model.Permeability = pe.Var(self._model.components,
                                              self._model.states,
                                              bounds=perm_bounds_rule)

    def set_mem_behavior_contraint(self, parameter):
        # Membrane Permeability Equation
        # TODO: redundant contraint appear in this function
        # (doublon for the same j)
        def mainEquationMem_rule(model, s, j, i):
            type_mem = model.mem_type[s].value
            mem = s - 1
            tmp = ((model.area[s] / parameter.discretisation[mem]) *
                   model.Permeability[j, s] / model.thickness[type_mem])

            if parameter.uniform_pup:
                return (model.Flux_PERM_cell[s, i] *
                        model.X_PERM_cell[s, j, i] == tmp *
                        (model.pressure_up * model.X_RET_cell[s, j, i] -
                         model.pressure_down[s] * model.X_PERM_cell[s, j, i]))
            else:
                return (model.Flux_PERM_cell[s, i] *
                        model.X_PERM_cell[s, j, i] == tmp *
                        (model.pressure_up[s] * model.X_RET_cell[s, j, i] -
                         model.pressure_down[s] * model.X_PERM_cell[s, j, i]))

        self._model.mainEquationMem = pe.Constraint(self._model.states,
                                                    self._model.components,
                                                    self._model.N,
                                                    rule=mainEquationMem_rule)

    def simplified_mem_behavior_contraint(self, parameter):
        # Membrane Permeability Equation
        # TODO: redundant contraint appear in this function
        # (doublon for the same j)
        def mainEquationMem_simplified_rule(model, s, j):
            type_mem = model.mem_type[s].value
            tmp = (model.area[s] * model.Permeability[j, s] /
                   model.thickness[type_mem])

            if parameter.uniform_pup:
                tmp2 = (tmp * (model.pressure_up * model.X_RET_mem[s, j] -
                               model.pressure_down[s] * model.X_PERM_mem[s, j]))
            else:
                tmp2 = (tmp * (model.pressure_up[s] * model.X_RET_mem[s, j] -
                               model.pressure_down[s] * model.X_PERM_mem[s, j]))
            return model.Flux_PERM_mem[s] * model.X_PERM_mem[s, j] == tmp2

        self._model.mainEquationMem_simplified = pe.Constraint(
            self._model.states,
            self._model.components,
            rule=mainEquationMem_simplified_rule)

    def robeson_equation_constraint(self, parameter):
        try:
            assert parameter.variable_perm
        except Exception:
            logger.exception("Robeson equation can't be applied :"
                             "permeability is not varaiable")
            raise

        def robeson_equation_rule(model, mem):
            type_mem = model.mem_type[mem].value
            ref_index = self.permeability_data[type_mem].component_item[0].index
            other_index = [
                item for item in model.components.data() if item != ref_index
            ][0]

            alpha = (model.Permeability[ref_index, mem] /
                     model.Permeability[other_index, mem])
            robeson_lines = (
                self.permeability_data[type_mem].robeson_multi *
                alpha**self.permeability_data[type_mem].robeson_power)

            if self.permeability_data[type_mem].robeson_power > 0:
                # linear form is monotonic increasing
                if self.permeability_data[type_mem].lb_alpha > 1:
                    return (model.Permeability[ref_index, mem] >= robeson_lines)
                else:
                    None

                if self.permeability_data[type_mem].ub_alpha < 1:
                    return (model.Permeability[ref_index, mem] <= robeson_lines)
                else:
                    None
            else:
                # linear form is monotonic decreasing
                if self.permeability_data[type_mem].lb_alpha > 1:
                    return (model.Permeability[ref_index, mem] <= robeson_lines)
                else:
                    None

                if self.permeability_data[type_mem].ub_alpha < 1:
                    return (model.Permeability[ref_index, mem] >= robeson_lines)
                else:
                    None

        self._model.Robeson_equation = pe.Constraint(self._model.states,
                                                     rule=robeson_equation_rule)

    def robeson_Selectivity(self, parameter):
        pass

    def mem_type_same_value(self, parameter):
        """Constrait membrane type
        to have same value of permeability on differents states."""
        try:
            assert parameter.variable_perm
        except Exception:
            logger.exception("Robeson equation can't be applied :"
                             "permeability is not varaiable")
            raise

        def mem_type_value_rule(model, mem1, mem2):
            if mem1 < mem2:
                type_mem = model.mem_type[mem1].value
                ref_index = self.permeability_data[type_mem].component_item[
                    0].index
                other_index = [
                    item for item in model.components.data()
                    if item != ref_index
                ][0]
                ref_equal = (
                    model.Permeability[ref_index,
                                       mem1] == model.Permeability[ref_index,
                                                                   mem2])
                other_equal = (
                    model.Permeability[other_index,
                                       mem1] == model.Permeability[other_index,
                                                                   mem2])

                return ref_equal
            else:
                return pe.Constraint.Skip

        self._model.mem_type_value = pe.Constraint(self._model.states,
                                                   self._model.states,
                                                   rule=mem_type_value_rule)

    def mem_type_element_generation(self, model_instance, parameter,
                                    random_generation):
        # random generation
        self._instance = model_instance
        # Permeability must be generated using Robeson's bound
        try:
            assert parameter.variable_perm
        except Exception:
            logger.exception("Robeson equation can't be applied :"
                             "permeability is not varaiable")
            raise
        # doing that for each kind of membranes
        for type_mem in self.permeability_data.keys():
            logger.info("Membrane type {} permeances values generation".format(
                type_mem))

            # generate a random alpha (selectivity) inside the bounds
            alpha = random_generation.uniform(
                self.permeability_data[type_mem].lb_alpha,
                self.permeability_data[type_mem].ub_alpha)
            logger.info("Random selectivity values = {}".format(round(alpha,
                                                                      3)))

            # calculate the value of Perm of ref permeable
            # component on the Robeson's bound
            ref_index = self.permeability_data[type_mem].component_item[0].index

            # self._instance.Permeability[ref_index, mem]
            perm_ref = (self.permeability_data[type_mem].robeson_multi *
                        alpha**self.permeability_data[type_mem].robeson_power)

            perm_ref = min(
                perm_ref, self.permeability_data[type_mem].component_item[0].ub)

            perm_ref = max(
                perm_ref, self.permeability_data[type_mem].component_item[0].lb)

            convertedPerm = (perm_ref / 3.347e-05)

            convertedLB = (
                self._instance.lb_permeability[ref_index, type_mem].value /
                3.347e-05)

            convertedUB = (
                self._instance.ub_permeability[ref_index, type_mem].value /
                3.347e-05)

            # calculate a random reduction of the Permeability
            delta = random_generation.uniform(0, parameter.epsilon.get('delta'))

            # adjust sign (if necessary)
            if self.permeability_data[type_mem].robeson_power > 0:
                # linear form is monotonic increasing
                # if self.permeability_data[type_mem].lb_alpha > 1:
                # perm_ref >= k * alpha ** n
                if self.permeability_data[type_mem].ub_alpha < 1:
                    # perm_ref <= k * alpha ** n
                    delta = -delta
                else:
                    None
            else:
                # linear form is monotonic decreasing
                if self.permeability_data[type_mem].lb_alpha > 1:
                    # perm_ref >= k * alpha ** n
                    delta = -delta
                else:
                    None
                # if self.permeability_data[type_mem].ub_alpha < 1:
                # perm_ref <= k * alpha ** n

            # move permeability away from border
            perm_ref = (perm_ref * (1 + delta))
            # restore bounds
            perm_ref = min(
                self._instance.ub_permeability[ref_index, type_mem].value,
                max(self._instance.lb_permeability[ref_index, type_mem].value,
                    perm_ref))

            other_index = [
                item for item in self._instance.components.data()
                if item != ref_index
            ][0]

            perm_other = (perm_ref / alpha)

            convertedPerm = (perm_ref / 3.347e-05)
            convertedLB = (
                self._instance.lb_permeability[ref_index, type_mem].value /
                3.347e-05)
            convertedUB = (
                self._instance.ub_permeability[ref_index, type_mem].value /
                3.347e-05)

            logger.info("REF permeability ({}) = {} in [{}, {}]".format(
                ref_index, round(convertedPerm, 3), round(convertedLB, 3),
                round(convertedUB, 3)))

            convertedPerm = (perm_other / 3.347e-05)
            convertedLB = (
                self._instance.lb_permeability[other_index, type_mem].value /
                3.347e-05)
            convertedUB = (
                self._instance.ub_permeability[other_index, type_mem].value /
                3.347e-05)

            logger.info("Other permeability ({}) = {} in [{}, {}]".format(
                other_index, round(convertedPerm, 3), round(convertedLB, 3),
                round(convertedUB, 3)))

            # Initialising permeability for each states with this mem_type
            for mem in self._instance.states:
                if type_mem == self._instance.mem_type[mem].value:
                    if not self._instance.Permeability[ref_index, mem].fixed:
                        self._instance.Permeability[ref_index, mem] = perm_ref
                    if not self._instance.Permeability[other_index, mem].fixed:
                        self._instance.Permeability[other_index,
                                                    mem] = perm_other

    def mem_type_element_perturbation(self, model_instance, parameter, center,
                                      random_generationPert):
        self._instance = model_instance
        # Permeability must be perturbated according to Robeson's UB
        try:
            assert parameter.variable_perm
        except Exception:
            logger.exception("Robeson equation can't be applied :"
                             "permeability is not varaiable")
            raise

        for mem in self._instance.states:
            type_mem = self._instance.mem_type[mem].value
            ref_index = self.permeability_data[type_mem].component_item[0].index
            other_index = [
                item for item in self._instance.components.data()
                if item != ref_index
            ][0]

            perm_center_value = center.get(
                parameter.labels[self._instance.Permeability[ref_index, mem]])
            alpha_center_value = perm_center_value / center.get(
                parameter.labels[self._instance.Permeability[other_index, mem]])

            # perturbation of alpha (selectivity)
            eps = parameter.epsilon.get('alpha')
            eps_alpha = random_generationPert.uniform(
                0,
                eps * (self.permeability_data[type_mem].ub_alpha -
                       self.permeability_data[type_mem].lb_alpha))
            alpha = max(
                self.permeability_data[type_mem].lb_alpha,
                min(alpha_center_value + eps_alpha,
                    self.permeability_data[type_mem].ub_alpha))

            # perturbation of permeability of ref permeable
            eps = parameter.epsilon.get('perm_ref')
            eps_perm = random_generationPert.uniform(
                0,
                eps *
                (self._instance.ub_permeability[ref_index, type_mem].value -
                 self._instance.lb_permeability[ref_index, type_mem].value))

            self._instance.Permeability[ref_index, mem] = max(
                self._instance.lb_permeability[ref_index, type_mem].value,
                min(perm_center_value + eps_perm,
                    self._instance.ub_permeability[ref_index, type_mem].value))

            # projecting inside Robeson's bound (if necessary)
            self._instance.Permeability[ref_index, mem] = min(
                self._instance.Permeability[ref_index, mem].value,
                (self.permeability_data[type_mem].robeson_multi *
                 alpha**self.permeability_data[type_mem].robeson_power))

            self._instance.Permeability[other_index, mem] = (
                self._instance.Permeability[ref_index, mem].value / alpha)

    # it will be interesting to known the unit of permeability before any
    # conversion
    def init_other_component_perm_bounds(self, model_instance):
        self._instance = model_instance
        for type_mem in self.permeability_data.keys():
            ref_index = self.permeability_data[type_mem].component_item[0].index
            other_index = [
                item for item in self._instance.components.data()
                if item != ref_index
            ][0]

            if self.permeability_data[type_mem].robeson_power > 0:
                # linear form is monotonic increasing

                # lb definition
                self._instance.lb_permeability[other_index, type_mem] = (
                    self._instance.lb_permeability[ref_index, type_mem].value /
                    self.permeability_data[type_mem].lb_alpha)

                # ub definition
                self._instance.ub_permeability[other_index, type_mem] = (
                    self._instance.ub_permeability[ref_index, type_mem].value /
                    self.permeability_data[type_mem].ub_alpha)
            else:
                # linear form is monotonic decreasing

                # lb defintion
                self._instance.lb_permeability[other_index, type_mem] = (
                    self._instance.lb_permeability[ref_index, type_mem].value /
                    self.permeability_data[type_mem].ub_alpha)

                # ub definition
                self._instance.ub_permeability[other_index, type_mem] = (
                    self._instance.ub_permeability[ref_index, type_mem].value /
                    self.permeability_data[type_mem].lb_alpha)

    def convert_permeability_to_barrer(self, model_instance, parameter):
        # if parameter.variable_perm:
        for mem in model_instance.states:
            for j in model_instance.components:
                model_instance.Permeability[j, mem] = (
                    model_instance.Permeability[j, mem].value / 3.347e-05)
        # else:
        #     # can't call convert to barrer on param permeability
        #     raise AssertionError(
        #         "Can't call convert to barrer on Permeability param")

    def convert_permeability_to_xxx(self, model_instance, parameter):
        # if parameter.variable_perm:
        for mem in model_instance.states:
            for j in model_instance.components:
                model_instance.Permeability[j, mem] = (
                    model_instance.Permeability[j, mem].value * 3.347e-05)
        # else:
        #     # can't call convert to barrer on param permeability
        #     raise AssertionError(
        #         "Can't call convert to barrer on Permeability param")

    def check_alpha_validity(self, model_instance):
        # for eah type of membranes
        for type_mem in self.permeability_data.keys():
            # Check if alpha bounds are valid
            if (self.permeability_data[type_mem].ub_alpha == 1 and
                    self.permeability_data[type_mem].lb_alpha == 1):
                # Suspend cas where alpha = 1
                raise ValueError(
                    "Alpha (selectivity of ref component) must be different to 1"
                )

            elif (self.permeability_data[type_mem].ub_alpha == 0 and
                  self.permeability_data[type_mem].lb_alpha == 0):
                # Suspend cas where alpha = 1
                raise ValueError(
                    "Alpha (selectivity of ref component) must be different to 0"
                )
            else:
                # TODO: add nonnegative to param definition in ub_alpha
                if (self.permeability_data[type_mem].lb_alpha < 1 and
                        self.permeability_data[type_mem].ub_alpha > 1):
                    # Impossible case : lb < 1 < ub
                    raise ValueError(
                        "Impossible case : lb_alpha < 1 < ub_alpha")

                elif (self.permeability_data[type_mem].ub_alpha > 1 and
                      self.permeability_data[type_mem].lb_alpha < 1):
                    # Impossible case : lb < 1 < ub
                    raise ValueError(
                        "Impossible case : lb_alpha < 1 < ub_alpha")
                else:
                    None

    def fix_ref_perm_bound(self, model_instance, parameter):
        for type_mem in self.permeability_data.keys():
            ref_index = self.permeability_data[type_mem].component_item[0].index
            lb_perm_ref = self.permeability_data[type_mem].component_item[0].lb
            ub_perm_ref = self.permeability_data[type_mem].component_item[0].ub

            model_instance.lb_permeability[ref_index, type_mem] = lb_perm_ref
            model_instance.ub_permeability[ref_index, type_mem] = ub_perm_ref

    def set_permeabiliy_when_fixed(self, model_instance, parameter):
        # permeability fixed
        for mem in model_instance.states:
            type_mem = model_instance.mem_type[mem].value
            for item in self.permeability_data[type_mem].component_item:
                model_instance.Permeability[item.index, mem] = item.value

    def print_permeability_variable(self, model_instance, parameter, outfile):
        if (parameter.variable_perm):
            for mem in model_instance.states:
                outfile.write("membrane " + str(mem) + " :" + "\n")
                type_mem = model_instance.mem_type[mem].value
                # convert from xxx to barrer
                self.convert_permeability_to_barrer(model_instance, parameter)
                for j in model_instance.components:
                    outfile.write("Perm[" + str(j) + " of type " +
                                  str(type_mem) + "] " + ' {0:4.6f}'.format(
                                      model_instance.Permeability[j,
                                                                  mem].value) +
                                  "\n")
                # restore convertion
                self.convert_permeability_to_xxx(model_instance, parameter)
        else:
            outfile.write("Permeability is constant\n")
            for mem in model_instance.states:
                type_mem = model_instance.mem_type[mem].value
                # outfile.write(
                #     "membrane "
                #     + str(mem)
                #     + " :"
                #     + " type "
                #     + str(type_mem)
                #     + "\n"
                #     )

                # convert from xxx to barrer
                self.convert_permeability_to_barrer(model_instance, parameter)
                for j in model_instance.components:
                    outfile.write("Perm[" + str(j) + " of type " +
                                  str(type_mem) + "] " + ' {0:4.6f}'.format(
                                      model_instance.Permeability[j,
                                                                  mem].value) +
                                  "\n")
                # restore convertion
                self.convert_permeability_to_xxx(model_instance, parameter)
