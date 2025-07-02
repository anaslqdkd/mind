""" Global functions.

This module contain callback functions used to generate starting point, to
perturb a feasible one.
"""

import os
import sys
import logging

import pyomo.environ as pe

from mind.optmodel_utilities import initZero
from mind.fixing import fixing_method, remove_var_initialisations

# logging variable
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)
handler = logging.StreamHandler()
# handler = logging.FileHandler('log1.txt')
logger.addHandler(handler)
formatter = logging.Formatter(fmt='[%(asctime)s] %(levelname)s : %(message)s',
                              datefmt='%a, %d %b %Y %H:%M:%S')
handler.setFormatter(formatter)


# Some variables can be initialize to try to have a almost
# feasible-starting point
def initFlows(model, random_generation, parameter):
    """Initialise flows variables.

    Args:
        model (`mind.system.MembranesDesignModel`): design process 's model

        random_generation (`Random`): Random object.

        parameter (`mind.builder.Configuration`) : design process configuration
    """
    for s in model.states:
        # at least the quantity of FEED
        var_init = parameter.init_status[parameter.labels[model.Feed_mem[s]]]
        if not model.Feed_mem[s].fixed and not var_init:
            model.Feed_mem[s] = model.splitFEED[s].value

        for j in model.components:
            # same composition as FEED
            var_init = parameter.init_status[parameter.labels[model.XIN_mem[s,
                                                                            j]]]
            if not model.XIN_mem[s, j].fixed and not var_init:
                model.XIN_mem[s, j] = model.XIN[j]

    # TODO: relation in the outlet of the membrane
    # Can we determine a guess of permeated using permeability and pressures?
    for s in model.states:
        var_init = parameter.init_status[parameter.labels[
            model.Flux_PERM_mem[s]]]
        if not model.Flux_PERM_mem[s].fixed and not var_init:
            model.Flux_PERM_mem[s] = (random_generation.uniform(0, 1) *
                                      model.Feed_mem[s].value)

        var_init = parameter.init_status[parameter.labels[
            model.Flux_RET_mem[s]]]
        if not model.Flux_RET_mem[s].fixed and not var_init:
            model.Flux_RET_mem[s] = (model.Feed_mem[s].value -
                                     model.Flux_PERM_mem[s].value)

    for s in model.states:
        var_init = parameter.init_status[parameter.labels[model.splitOutRET[s]]]
        if not model.splitOutRET[s].fixed and not var_init:
            model.splitOutRET[s] = (model.splitOutRET_frac[s].value *
                                    model.Flux_RET_mem[s].value)

        var_init = parameter.init_status[parameter.labels[
            model.splitOutPERM[s]]]
        if not model.splitOutPERM[s].fixed and not var_init:
            model.splitOutPERM[s] = (model.splitOutPERM_frac[s].value *
                                     model.Flux_PERM_mem[s].value)

        for j in model.states:
            var_init = parameter.init_status[parameter.labels[model.splitRET[
                s, j]]]
            if not model.splitRET[s, j].fixed and not var_init:
                model.splitRET[s, j] = (model.splitRET_frac[s, j].value *
                                        model.Flux_RET_mem[s].value)

            var_init = parameter.init_status[parameter.labels[model.splitPERM[
                s, j]]]
            if not model.splitPERM[s, j].fixed and not var_init:
                model.splitPERM[s, j] = (model.splitPERM_frac[s, j].value *
                                         model.Flux_PERM_mem[s].value)


def generate_area(model, random_generation, parameter):
    """Generate random values for cell area variable.

    Args:
        model (`mind.system.MembranesDesignModel`): design process 's model

        random_generation (`Random`): Random object.

        parameter (`mind.builder.Configuration`) : design process configuration
    """
    for s in model.states:
        var_init = parameter.init_status[parameter.labels[model.area[s]]]
        if not model.area[s].fixed and not var_init:
            model.area[s] = random_generation.uniform(model.lb_area[s].value,
                                                      model.ub_area[s].value)


def generate_pressure(model, parameter, random_generation):
    """Generate random values for pressures variables.
    Pressure_up and pressure_down variables.

    Args:
        model (`mind.system.MembranesDesignModel`): design process 's model

        random_generation (`Random`): Random object.

        parameter (`mind.builder.Configuration`) : design process configuration
    """
    if parameter.uniform_pup:
        var_init = parameter.init_status[parameter.labels[model.pressure_up]]
        if not model.pressure_up.fixed and not var_init:
            ub_fixed_pressure_down = model.lb_press_up.value
            if True in [model.pressure_down[s].fixed for s in model.states]:
                # there are at least one pressure_down fixed
                ub_fixed_pressure_down = max(
                    [model.pressure_down[s].value for s in model.states])
            if ub_fixed_pressure_down > model.ub_press_up.value:
                logger.exception('Fixed pressure_down \'s value > ub_press_up')
                raise ValueError('Fixed pressure_down \'s value > ub_press_up')
            model.pressure_up = random_generation.uniform(
                max(ub_fixed_pressure_down, model.lb_press_up.value),
                model.ub_press_up.value)

    else:
        for s in model.states:
            var_init = parameter.init_status[parameter.labels[
                model.pressure_up[s]]]
            if not model.pressure_up[s].fixed and not var_init:
                ub_fixed_pressure_down = model.lb_press_up.value
                if True in [model.pressure_down[s].fixed for s in model.states]:
                    # there are at least one pressure_down fixed
                    ub_fixed_pressure_down = max(
                        [model.pressure_down[s].value for s in model.states])
                if ub_fixed_pressure_down > model.ub_press_up.value:
                    logger.exception(
                        'Fixed pressure_down \'s value > ub_press_up')
                    raise ValueError(
                        'Fixed pressure_down \'s value > ub_press_up')

                if s == 1:
                    model.pressure_up[s] = random_generation.uniform(
                        max(ub_fixed_pressure_down, model.lb_press_up.value),
                        model.ub_press_up.value)
                else:
                    model.pressure_up[s] = random_generation.uniform(
                        max(ub_fixed_pressure_down,
                            model.pressure_up[s - 1].value),
                        model.ub_press_up.value)

    for s in model.states:
        var_init = parameter.init_status[parameter.labels[
            model.pressure_down[s]]]
        if not model.pressure_down[s].fixed and not var_init:
            if parameter.uniform_pup:
                model.pressure_down[s] = max(
                    model.lb_press_down.value,
                    min((model.pressure_up.value * parameter.pressure_ratio),
                        model.ub_press_down.value))
            else:
                model.pressure_down[s] = max(
                    model.lb_press_down.value,
                    min((model.pressure_up[model.states.last()].value *
                         parameter.pressure_ratio), model.ub_press_down.value))


def generate_splitFeed(model, random_generation, parameter):
    """Generate random values for splitFEED variables.
    The Feed is splitted in the input of the global system.

    Args:
        model (`mind.system.MembranesDesignModel`): design process 's model

        random_generation (`Random`): Random object.

        parameter (`mind.builder.Configuration`) : design process configuration
    """
    tmp = sum(model.splitFEED_frac[s].value for s in model.states)
    if tmp > 1:
        logger.exception('sum of splitFEED_frac \'s fixed values > 1')
        raise ValueError('splitFEED_frac \'s fixed values')

    states_fixed_bool = [model.splitFEED_frac[s].fixed for s in model.states]
    nb_free_elem = len([1 for elem in states_fixed_bool if elem is False])

    if nb_free_elem == 0 and tmp < 1:
        logger.exception('sum of splitFEED_frac \'s fixed values < 1')
        raise ValueError('splitFEED_frac \'s fixed values')

    not_fixed = []
    for s in model.states:
        init_var = parameter.init_status[parameter.labels[
            model.splitFEED_frac[s]]]
        if not (model.splitFEED_frac[s].fixed or init_var):
            not_fixed.append('FEED_frac{}'.format(s))
            model.splitFEED_frac[s] = random_generation.uniform(0, 1 - tmp)
            tmp += model.splitFEED_frac[s].value

    if not_fixed:
        s = int((not_fixed[0])[9])
        model.splitFEED_frac[s] = (model.splitFEED_frac[s].value + (1 - tmp))

    for s in model.states:
        model.splitFEED[s] = model.splitFEED_frac[s].value * model.FEED


def generate_splitRet(model, random_generation, parameter):
    """Generate random values for splitRET variables.
    The output RET is also splitted (see mathematic model for more details).

    Args:
        model (`mind.system.MembranesDesignModel`): design process 's model

        random_generation (`Random`): Random object.

        parameter (`mind.builder.Configuration`) : design process configuration
    """

    for s in model.states:
        tmp = (sum(model.splitRET_frac[s, s1].value for s1 in model.states) +
               model.splitOutRET_frac[s].value)
        if tmp > 1:
            logger.exception('sum of splitRET_frac \'s fixed values > 1 '
                             'when states = {}'.format(s))
            raise ValueError('splitRET_frac \'s fixed values')

        states_fixed_bool = ([
            model.splitRET_frac[s, s1].fixed or
            parameter.init_status[parameter.labels[model.splitRET_frac[s, s1]]]
            for s1 in model.states
        ] + [
            model.splitOutRET_frac[s].fixed or
            parameter.init_status[parameter.labels[model.splitOutRET_frac[s]]]
        ])

        nb_free_elem = len([1 for elem in states_fixed_bool if elem is False])

        if nb_free_elem == 0 and tmp < 1:
            logger.exception('sum of splitRET_frac \'s fixed values < 1')
            raise ValueError('splitRET_frac \'s fixed values')

        not_fixed = []
        for s1 in model.states:
            init_var = parameter.init_status[parameter.labels[
                model.splitRET_frac[s, s1]]]
            if not (model.splitRET_frac[s, s1].fixed or init_var):
                not_fixed.append('RET_frac{}, {}'.format(s, s1))
                model.splitRET_frac[s, s1] = random_generation.uniform(
                    max(0, model.lb_splitRET_frac[s, s1].value),
                    min(1 - tmp, model.ub_splitRET_frac[s, s1].value))
                tmp += model.splitRET_frac[s, s1].value

        init_var = parameter.init_status[parameter.labels[
            model.splitOutRET_frac[s]]]
        if not (model.splitOutRET_frac[s].fixed or init_var):
            not_fixed.append('OutRET_frac{}'.format(s))
            model.splitOutRET_frac[s] = random_generation.uniform(0, 1 - tmp)
            tmp += model.splitOutRET_frac[s].value

        if not_fixed:
            if (not_fixed[0])[0:8] == "RET_frac":
                s = int((not_fixed[0])[8])
                s1 = int((not_fixed[0])[11])
                model.splitRET_frac[s, s1] = (model.splitRET_frac[s, s1].value +
                                              (1 - tmp))
            elif (not_fixed[0])[0:11] == "OutRET_frac":
                s = int((not_fixed[0])[11])
                model.splitOutRET_frac[s] = (model.splitOutRET_frac[s].value +
                                             (1 - tmp))
            else:
                raise ValueError('Error in splitRET generation')


def generate_splitPerm(model, random_generation, parameter):
    """Generate random values for splitPERM variables.
    The output PERM is also splitted (see mathematic model for more details).

    Args:
        model (`mind.system.MembranesDesignModel`): design process 's model

        random_generation (`Random`): Random object.

        parameter (`mind.builder.Configuration`) : design process configuration
    """

    for s in model.states:
        tmp = (sum(model.splitPERM_frac[s, s1].value for s1 in model.states) +
               model.splitOutPERM_frac[s].value)
        if tmp > 1:
            logger.exception('sum of splitPERM_frac \'s fixed values > 1 '
                             'when states = {}'.format(s))
            raise ValueError('splitPERM_frac \'s fixed values')

        states_fixed_bool = ([
            model.splitPERM_frac[s, s1].fixed or
            parameter.init_status[parameter.labels[model.splitPERM_frac[s, s1]]]
            for s1 in model.states
        ] + [
            model.splitOutPERM_frac[s].fixed or
            parameter.init_status[parameter.labels[model.splitOutPERM_frac[s]]]
        ])

        nb_free_elem = len([1 for elem in states_fixed_bool if elem is False])

        if nb_free_elem == 0 and tmp < 1:
            logger.exception('sum of splitPERM_frac \'s fixed values < 1')
            raise ValueError('splitPERM_frac \'s fixed values')

        not_fixed = []
        for s1 in model.states:
            init_var = parameter.init_status[parameter.labels[
                model.splitPERM_frac[s, s1]]]
            if not (model.splitPERM_frac[s, s1].fixed or init_var):
                not_fixed.append('PERM_frac{}, {}'.format(s, s1))
                model.splitPERM_frac[s, s1] = random_generation.uniform(
                    max(0, model.lb_splitPERM_frac[s, s1].value),
                    min(1 - tmp, model.ub_splitPERM_frac[s, s1].value))
                tmp += model.splitPERM_frac[s, s1].value

        init_var = parameter.init_status[parameter.labels[
            model.splitOutPERM_frac[s]]]
        if not (model.splitOutPERM_frac[s].fixed or init_var):
            not_fixed.append('OutPERM_frac{}'.format(s))
            model.splitOutPERM_frac[s] = random_generation.uniform(0, 1 - tmp)
            tmp += model.splitOutPERM_frac[s].value

        if not_fixed:
            if (not_fixed[0])[0:9] == "PERM_frac":
                s = int((not_fixed[0])[9])
                s1 = int((not_fixed[0])[12])
                model.splitPERM_frac[s, s1] = (model.splitPERM_frac[s, s1].value +
                                               (1 - tmp))
            elif (not_fixed[0])[0:12] == "OutPERM_frac":
                s = int((not_fixed[0])[12])
                model.splitOutPERM_frac[s] = (model.splitOutPERM_frac[s].value +
                                              (1 - tmp))
            else:
                raise ValueError('Error in splitPERM generation')


def random_generation(model, random_generation, parameter, behavior,
                      fname_mask):
    """Generate random values for independants variables of the optimization
    model. Its correspond to all variables, expect cells variables.

    Args:
        model (`mind.system.MembranesDesignModel`): design process 's model

        random_generation (`Random`): Random object.

        parameter (`mind.builder.Configuration`) : design process configuration

        behavior (`mind.membranes.MembranesTypes`): desing process membrane's description
    """
    initZero(model)
    remove_var_initialisations(parameter)
    logger.info('Random generation OK')
    if parameter.fixing_var:
        fixing_method(fname_mask, model, parameter)

    logger.info("Random generation method")

    generate_area(model, random_generation, parameter)
    generate_pressure(model, parameter, random_generation)

    # generate_permeability(model, parameter, random_generation)
    # # TODO: Can not fix this element
    if parameter.variable_perm:
        behavior.mem_type_element_generation(model, parameter,
                                             random_generation)
    # Generation of variables related to interconnection between membranes
    # There are different splits: FEED and Ret/Perm flows
    generate_splitFeed(model, random_generation, parameter)
    # random generation for split fractions of RET/PERM: values in (lb,ub)
    generate_splitRet(model, random_generation, parameter)
    # perm random generation
    generate_splitPerm(model, random_generation, parameter)

    # Out=1-sum(all other splits)
    # # # OPTIMIZE: by using sum , difference (list) : built-in function
    # # TODO: Can not fix this element

    initFlows(model, random_generation, parameter)


# epsilon is a dictionary to keep the different values of perturbation
# for different variables
# eps_At => epsilon['At']
# eps_press_up_f => epsilon['press_up_f']
# eps_press_down_f => epsilon['press_down_f']
# eps_feed => epsilon['feed']


def perturb_area(model, random_generationPert, parameter, center):
    """Perturb slightly model area values.

        Args:
            model (`mind.system.MembranesDesignModel`): design process 's model

            random_generationPert (`Random`): Random object.

            parameter (`mind.builder.Configuration`) : design process configuration

            center (`DICT`): copy of a model's instance solution
    """
    for s in model.states:
        var_init = parameter.init_status[parameter.labels[model.area[s]]]
        if not model.area[s].fixed and not var_init:
            area_eps = random_generationPert.uniform(
                0, (parameter.epsilon.get('At') *
                    (model.ub_area[s].value - model.lb_area[s].value)))

            center_value = center.get(parameter.labels[model.area[s]])
            model.area[s] = max(
                model.lb_area[s].value,
                min(center_value + area_eps, model.ub_area[s].value))


def perturb_pressure(model, random_generationPert, parameter, center):
    """ perturb slightly model pressures values (pressure_up & pressure_down).

    Args:
        model (`mind.system.MembranesDesignModel`): design process 's model

        random_generationPert (`Random`): Random object.

        parameter (`mind.builder.Configuration`) : design process configuration

        center (`DICT`): copy of a model's instance solution
    """
    eps_press = random_generationPert.uniform(
        0,
        parameter.epsilon.get('press_up_f') *
        (model.ub_press_up.value - model.lb_press_up.value))

    if parameter.uniform_pup:
        center_value = center.get(parameter.labels[model.pressure_up])
        tmp = min(center_value + eps_press, model.ub_press_up.value)
        model.pressure_up = max(model.lb_press_up.value, tmp)
    else:
        for s in model.states:
            if (s == 1):
                # model.pressure_up[s] = random_generation.uniform(
                # model.lb_press_up.value,
                # model.ub_press_up.value)

                center_value = center.get(
                    parameter.labels[model.pressure_up[s]])
                tmp = min(center_value + eps_press, model.ub_press_up.value)
                model.pressure_up[s] = max(model.lb_press_up.value, tmp)
            else:
                # model.pressure_up[s] =
                # random_generation.uniform(model.lb_press_up.value,
                # value(model.pressure_up[s-1]))

                center_value = center.get(
                    parameter.labels[model.pressure_up[s]])
                tmp = min(center_value + eps_press,
                          pe.value(model.pressure_up[s - 1]))
                model.pressure_up[s] = max(model.lb_press_up.value, tmp)

    # Pressure_down
    for s in model.states:
        eps_press = random_generationPert.uniform(
            0,
            parameter.epsilon.get('press_down_f') *
            (model.ub_press_down.value - model.lb_press_down.value))

        center_value = center.get(parameter.labels[model.pressure_down[s]])
        if (parameter.uniform_pup):
            model.pressure_down[s] = max(
                model.lb_press_down.value,
                min(center_value + eps_press,
                    min(model.ub_press_down.value, model.pressure_up.value)))

        else:
            model.pressure_down[s] = max(
                model.lb_press_down.value,
                min(
                    center_value + eps_press,
                    min(model.ub_press_down.value,
                        model.pressure_up[model.states.last()].value)))


def perturb_splitFeed(model, random_generationPert, parameter, center):
    """Perturb slightly model splitFEED variable values.

    Args:
        model (`mind.system.MembranesDesignModel`): design process 's model

        random_generationPert (`Random`): Random object.

        parameter (`mind.builder.Configuration`) : design process configuration

        center (`DICT`): copy of a model's instance solution
    """
    tmp = sum(model.splitFEED_frac[s].value for s in model.states)
    if tmp > 1:
        logger.exception('sum of splitFEED_frac \'s fixed values > 1')
        raise ValueError('splitFEED_frac \'s fixed values')

    states_fixed_bool = [model.splitFEED_frac[s].fixed for s in model.states]
    nb_free_elem = len([1 for elem in states_fixed_bool if elem is False])

    if nb_free_elem == 0 and tmp < 1:
        logger.exception('sum of splitFEED_frac \'s fixed values < 1')
        raise ValueError('splitFEED_frac \'s fixed values')

    not_fixed = []
    for s in model.states:
        init_var = parameter.init_status[parameter.labels[
            model.splitFEED_frac[s]]]
        if not (model.splitFEED_frac[s].fixed or init_var):
            not_fixed.append('FEED_frac{}'.format(s))
            split_eps = random_generationPert.uniform(
                -1. * parameter.epsilon.get('feed'),
                parameter.epsilon.get('feed'))
            center_value = center.get(parameter.labels[model.splitFEED_frac[s]])
            generated_value = center_value + split_eps
            # if 0 <= generated_value <= 1-tmp then keep generated_value
            if generated_value < 0:
                generated_value = random_generationPert.uniform(
                    0 - generated_value, 0)
            elif generated_value > 1 - tmp:
                generated_value = random_generationPert.uniform((1 - tmp),
                                                                generated_value)
                generated_value = generated_value - (1 - tmp)
            # generated_value = max(0, generated_value)
            # generated_value = min(1-tmp, generated_value)
            model.splitFEED_frac[s] = generated_value
            tmp += generated_value

    if not_fixed:
        s = int((not_fixed[0])[9])
        model.splitFEED_frac[s] = (model.splitFEED_frac[s].value + (1 - tmp))

    for s in model.states:
        model.splitFEED[s] = model.splitFEED_frac[s].value * model.FEED

    # print(sum(model.splitFEED_frac[s].value for s in model.states))
    # print()


def perturb_splitRet(model, random_generationPert, parameter, center):
    """Perturb slightly model splitRET variable values for a given membrane.

    Args:
        model (`mind.system.MembranesDesignModel`): design process 's model

        random_generationPert (`Random`): Random object.

        parameter (`mind.builder.Configuration`) : design process configuration

        center (`DICT`): copy of a model's instance solution
    """
    for s in model.states:
        tmp = (sum(model.splitRET_frac[s, s1].value for s1 in model.states) +
               model.splitOutRET_frac[s].value)
        if tmp > 1:
            logger.exception('sum of splitRET_frac \'s fixed values > 1 '
                             'when states = {}'.format(s))
            raise ValueError('splitRET_frac \'s fixed values')

        states_fixed_bool = ([
            model.splitRET_frac[s, s1].fixed or
            parameter.init_status[parameter.labels[model.splitRET_frac[s, s1]]]
            for s1 in model.states
        ] + [
            model.splitOutRET_frac[s].fixed or
            parameter.init_status[parameter.labels[model.splitOutRET_frac[s]]]
        ])

        nb_free_elem = len([1 for elem in states_fixed_bool if elem is False])

        if nb_free_elem == 0 and tmp < 1:
            logger.exception('sum of splitRET_frac \'s fixed values < 1')
            raise ValueError('splitRET_frac \'s fixed values')

        not_fixed = []
        for s1 in model.states:
            init_var = parameter.init_status[parameter.labels[
                model.splitRET_frac[s, s1]]]
            if not (model.splitRET_frac[s, s1].fixed or init_var):
                not_fixed.append('RET_frac{}, {}'.format(s, s1))
                split_eps = random_generationPert.uniform(
                    -parameter.epsilon.get('feed'),
                    parameter.epsilon.get('feed'))
                center_value = center.get(
                    parameter.labels[model.splitRET_frac[s, s1]])
                generated_value = center_value + split_eps
                # if 0 <= generated_value <= 1-tmp then keep generated_value
                if generated_value < 0:
                    generated_value = random_generationPert.uniform(
                        0 - generated_value, 0)
                elif generated_value > 1 - tmp:
                    generated_value = random_generationPert.uniform(
                        (1 - tmp), generated_value)
                    generated_value = generated_value - (1 - tmp)
                # generated_value = max(0, generated_value)
                # generated_value = min(1-tmp, generated_value)
                model.splitRET_frac[s, s1] = generated_value
                tmp += generated_value

        init_var = parameter.init_status[parameter.labels[
            model.splitOutRET_frac[s]]]
        if not (model.splitOutRET_frac[s].fixed or init_var):
            not_fixed.append('OutRET_frac{}'.format(s))
            center_value = center.get(
                parameter.labels[model.splitOutRET_frac[s]])
            generated_value = center_value + split_eps
            # if 0 <= generated_value <= 1-tmp then keep generated_value
            if generated_value < 0:
                generated_value = random_generationPert.uniform(
                    0 - generated_value, 0)
            elif generated_value > 1 - tmp:
                generated_value = random_generationPert.uniform((1 - tmp),
                                                                generated_value)
                generated_value = generated_value - (1 - tmp)
            # generated_value = max(0, generated_value)
            # generated_value = min(1-tmp, generated_value)
            model.splitOutRET_frac[s] = generated_value
            tmp += generated_value

        if (not_fixed[0])[0:8] == "RET_frac":
            s = int((not_fixed[0])[8])
            s1 = int((not_fixed[0])[11])
            model.splitRET_frac[s, s1] = (model.splitRET_frac[s, s1].value +
                                          (1 - tmp))
        elif (not_fixed[0])[0:11] == "OutRET_frac":
            s = int((not_fixed[0])[11])
            model.splitOutRET_frac[s] = (model.splitOutRET_frac[s].value +
                                         (1 - tmp))
        else:
            raise ValueError('Error in splitRET generation')

        # print(
        #     sum(model.splitRET_frac[s, s1].value for s1 in model.states)
        #     + model.splitOutRET_frac[s].value
        # )
        #
        # print()


def perturb_splitPerm(model, random_generationPert, parameter, center):
    """Perturb slightly model splitPERM variable values for a given membrane.

    Args:
        model (`mind.system.MembranesDesignModel`): design process 's model

        random_generationPert (`Random`): Random object.

        parameter (`mind.builder.Configuration`) : design process configuration

        center (`DICT`): copy of a model's instance solution
    """
    for s in model.states:
        tmp = (sum(model.splitPERM_frac[s, s1].value for s1 in model.states) +
               model.splitOutPERM_frac[s].value)
        if tmp > 1:
            logger.exception('sum of splitPERM_frac \'s fixed values > 1 '
                             'when states = {}'.format(s))
            raise ValueError('splitPERM_frac \'s fixed values')

        states_fixed_bool = ([
            model.splitPERM_frac[s, s1].fixed or
            parameter.init_status[parameter.labels[model.splitPERM_frac[s, s1]]]
            for s1 in model.states
        ] + [
            model.splitOutPERM_frac[s].fixed or
            parameter.init_status[parameter.labels[model.splitOutPERM_frac[s]]]
        ])

        nb_free_elem = len([1 for elem in states_fixed_bool if elem is False])

        if nb_free_elem == 0 and tmp < 1:
            logger.exception('sum of splitPERM_frac \'s fixed values < 1')
            raise ValueError('splitPERM_frac \'s fixed values')

        not_fixed = []
        for s1 in model.states:
            init_var = parameter.init_status[parameter.labels[
                model.splitPERM_frac[s, s1]]]
            if not (model.splitPERM_frac[s, s1].fixed or init_var):
                not_fixed.append('PERM_frac{}, {}'.format(s, s1))
                split_eps = random_generationPert.uniform(
                    -parameter.epsilon.get('feed'),
                    parameter.epsilon.get('feed'))
                center_value = center.get(
                    parameter.labels[model.splitPERM_frac[s, s1]])
                generated_value = center_value + split_eps
                # if 0 <= generated_value <= 1-tmp then keep generated_value
                if generated_value < 0:
                    generated_value = random_generationPert.uniform(
                        0 - generated_value, 0)
                elif generated_value > 1 - tmp:
                    generated_value = random_generationPert.uniform(
                        (1 - tmp), generated_value)
                    generated_value = generated_value - (1 - tmp)
                # generated_value = max(0, generated_value)
                # generated_value = min(1-tmp, generated_value)
                model.splitPERM_frac[s, s1] = generated_value
                tmp += generated_value

        init_var = parameter.init_status[parameter.labels[
            model.splitOutPERM_frac[s]]]
        if not (model.splitOutPERM_frac[s].fixed or init_var):
            not_fixed.append('OutPERM_frac{}'.format(s))
            center_value = center.get(
                parameter.labels[model.splitOutPERM_frac[s]])
            generated_value = center_value + split_eps
            # if 0 <= generated_value <= 1-tmp then keep generated_value
            if generated_value < 0:
                generated_value = random_generationPert.uniform(
                    0 - generated_value, 0)
            elif generated_value > 1 - tmp:
                generated_value = random_generationPert.uniform((1 - tmp),
                                                                generated_value)
                generated_value = generated_value - (1 - tmp)
            # generated_value = max(0, generated_value)
            # generated_value = min(1-tmp, generated_value)
            model.splitOutPERM_frac[s] = generated_value
            tmp += generated_value

        if (not_fixed[0])[0:9] == "PERM_frac":
            s = int((not_fixed[0])[9])
            s1 = int((not_fixed[0])[12])
            model.splitPERM_frac[s, s1] = (model.splitPERM_frac[s, s1].value +
                                           (1 - tmp))
        elif (not_fixed[0])[0:12] == "OutPERM_frac":
            s = int((not_fixed[0])[12])
            model.splitOutPERM_frac[s] = (model.splitOutPERM_frac[s].value +
                                          (1 - tmp))
        else:
            raise ValueError('Error in splitPERM generation')

        # print(
        #     sum(model.splitPERM_frac[s, s1].value for s1 in model.states)
        #     + model.splitOutPERM_frac[s].value
        # )
        # print()


def Perturbation_membranes(model, center, random_generationPert, parameter,
                           behavior, fname_mask):
    """Perturb slightly a feasible solution of the model. The feasible
    solution is also overwrite by the obtained solution (perturbated one).

    Args:
        model (`mind.system.MembranesDesignModel`): design process 's model

        random_generationPert (`Random`): Random object.

        parameter (`mind.builder.Configuration`) : design process configuration

        center (`DICT`): copy of a model's instance solution

        behavior (`mind.membranes.MembranesTypes`): desing process membrane 's description.

        fname_mask (`str`) : path to file containing information about fixed variables
    """

    initZero(model)
    remove_var_initialisations(parameter)
    if parameter.fixing_var:
        fixing_method(fname_mask, model, parameter)

    logger.info("Perturabation method")

    # area perturbation
    perturb_area(model, random_generationPert, parameter, center)
    # Pressures perturbation
    perturb_pressure(model, random_generationPert, parameter, center)

    if parameter.variable_perm:
        behavior.mem_type_element_perturbation(model, parameter, center,
                                               random_generationPert)

    perturb_splitFeed(model, random_generationPert, parameter, center)
    perturb_splitRet(model, random_generationPert, parameter, center)
    perturb_splitPerm(model, random_generationPert, parameter, center)

    initFlows(model, random_generationPert, parameter)


def initCells(model, parameter):
    """Intialise variables related to cells level.

    Args:
        model (`pyomo.concreteModel`): design process constructed model.

        parameter (`mind.builder.Configuration`): process Design configuration.
    """

    for s in model.states:
        last_cell_index = parameter.discretisation[s - 1]
        # first cell Feed
        model.Feed_cell[s, 1] = model.Feed_mem[s].value
        for j in model.components:
            model.XIN_cell[s, j, 1] = model.XIN_mem[s, j].value

        delta = model.Feed_mem[s].value - model.Flux_RET_mem[s].value
        delta = delta / last_cell_index

        # all cells except last
        for i in range(1, last_cell_index):
            # calculate RET for current cell supposing linearity along cells
            model.Flux_RET_cell[s, i] = model.Feed_mem[s].value - i * delta

            # calculate PERM for current cell
            model.Flux_PERM_cell[s, i] = (model.Feed_cell[s, i].value -
                                          model.Flux_RET_cell[s, i].value)
            # input next cell update
            model.Feed_cell[s, i + 1] = model.Flux_RET_cell[s, i].value

            for j in model.components:
                model.X_RET_cell[s, j, i] = (
                    model.XIN_mem[s, j].value - i *
                    (model.XIN_mem[s, j].value - model.X_RET_mem[s, j].value) /
                    last_cell_index)

            for j in model.components:
                model.XIN_cell[s, j, i + 1] = (model.X_RET_cell[s, j, i].value)

        # last (and output) cell
        model.Flux_RET_cell[s, last_cell_index] = (model.Flux_RET_mem[s].value)
        for j in model.components:
            model.X_RET_cell[s, j, last_cell_index] = (model.X_RET_mem[s,
                                                                       j].value)

        # calculate PERM
        model.Flux_PERM_cell[s, last_cell_index] = (
            model.Feed_cell[s, last_cell_index].value -
            model.Flux_RET_cell[s, last_cell_index].value)

        # normalizing to 1
        for i in range(1, last_cell_index + 1):
            total = sum(
                model.X_RET_cell[s, j, i].value for j in model.components)
            if total > 0:
                for j in model.components:
                    model.X_RET_cell[s, j,
                                     i] = (model.X_RET_cell[s, j, i].value /
                                           total)

            # TODO:   numerical value to handle
            if model.Flux_PERM_cell[s, i].value >= 1.e-3:
                # TODO: ask bernardetta why we don't divise tmp1 by thickness
                # TODO: delete .value
                for j in model.components:
                    tmp1 = ((model.area[s].value /
                             parameter.discretisation[s - 1]) *
                            model.Permeability[j, s].value)

                    if (parameter.uniform_pup):
                        tmp2 = (model.pressure_up.value *
                                model.X_RET_cell[s, j, i].value)
                    else:
                        tmp2 = (model.pressure_up[s].value *
                                model.X_RET_cell[s, j, i].value)
                    # print(model.pressure_down[s].value)
                    # print(model.X_PERM_cell[s, j, i].value)
                    tmp3 = (model.pressure_down[s].value *
                            model.X_PERM_cell[s, j, i].value)
                    tmp4 = (tmp1 * (tmp2 - tmp3) /
                            model.Flux_PERM_cell[s, i].value)
                    model.X_PERM_cell[s, j, i] = min(1, max(0, tmp4))
                    # normalizing to 1 the mixture
                    total = sum(model.X_PERM_cell[s, j, i].value
                                for j in model.components)
                    if total > 0:
                        for j in model.components:
                            model.X_PERM_cell[s, j, i] = (
                                model.X_PERM_cell[s, j, i].value / total)
                        else:
                            # just to avoid all init to zero
                            for j in model.components:
                                model.X_PERM_cell[s, j, i] = (
                                    1 / len(model.components))
