"""Defining liquid optimization model of Membrane design process."""

import logging

import pyomo.environ as pe

from mind.system import MembranesDesignModel

# logging variable
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)
handler = logging.StreamHandler()
# handler = logging.FileHandler(filename)
logger.addHandler(handler)
formatter = logging.Formatter(fmt='[%(asctime)s] %(levelname)s : %(message)s',
                              datefmt='%a, %d %b %Y %H:%M:%S')
handler.setFormatter(formatter)


class MembranesDesignLiquid(MembranesDesignModel):
    """Implement MembranesDesignModel class.
    It define parameter, varaibles and some constraint of liquid optimization
    model.

    Args:
        conf_param (dict): process design configuration parameter.

    Attributes:
        abstractModel (pyomo.abstractModel): the abstract model
        instance (pyomo.concreteModel): creation of an instance of model
        parameter (dict): some essential configuration parameter for
            model construction
        labels (dict): names or lables of all variables in the model

    Note:
        Callback described below are called by module builder to construct
        the model.
    """

    def __init__(self, conf_param, perm_data):
        """ Initialise components (abstractModel, parameter, labels
            and instances) for model construction. """
        self.parameter = conf_param
        self.perm_data = perm_data
        self.abstractModel = pe.AbstractModel()
        self.instance = None
        super().init_model()
        # self.arg = arg

    def define_process_contraints(self):
        """ Add problem contraints to model """
        pass

    def define_process_objective(self):
        """ State the objective function of the model"""
        pass

    def create_process_model(self):
        """ callback to defining constraints and objective function. """
        pass

    def create_process_instance(self, fname):
        """ creation of an instance of the model object
            (pyomo construction). """
        pass
