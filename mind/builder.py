"""Module providing callable to build the optimization model.

Called by `mind.launcher` (or any interface to users)
to create `mind.liquid` or `mind.gas` model,
given some configuration informations
and instances file (which describing real world problem).
"""
import logging
import math

from mind.gas import MembranesDesignGas

# logging variable
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)
handler = logging.StreamHandler()
# handler = logging.FileHandler(filename)
logger.addHandler(handler)
formatter = logging.Formatter(fmt='[%(asctime)s] %(levelname)s : %(message)s',
                              datefmt='%a, %d %b %Y %H:%M:%S')
handler.setFormatter(formatter)


# This class contains all parameters necessary to configurate model
# with respect of a selected case study :
# (uniform/not uniform Pressures_up, presence of Vacuum Pumps, Valves, etc
class Configuration():
    """ Initialization of design process configuration.

        Attributes:
            num_membranes (`Int`) : number of membranes (`default = 2`)

            lb_area (`List[Int]`) :  lower bound for each membrane's area

            ub_area (`List[Int]`) :  upper bound for each membrane's area

            ub_acell (`List[Int]`) :  upper bound for each membrane's acell

            uniform_pup (`Bool`) : `True` if `pressure_up` are uniform (`default = True`)

            vp (`Bool`) : `True` if Vacuum Pump is available(`default = True`)

            variable_perm (`Bool`) : `True` if permeability's variable are not
            constant (`default = True`)

            fixing_var (`Bool`) : `True` if users want to fix some models's
            variables (`default = False`)

            init_status (dict) : datastruct that manipulate informations about
            which varaibles are initialized initially by users

            pressure_ratio (`Float`) : Thresold value for model's variable
             relative to pressure (`default = 0.03`)

            epsilon (dict) : Default Thresolds values using in algorithms (`mind.solve`)

        Notes:
            - Membranes'area are splitted into small cells (method: `discretise_membrane`)
            - `self.discretisation` (`List[Int]`): datastruct manipulating
            information on membrane's area discretisation into small cells

        """

    def __init__(self,
                 num_membranes=2,
                 ub_area=None,
                 lb_area=None,
                 ub_acell=None,
                 uniform_pup=True,
                 vp=True,
                 variable_perm=True,
                 fixing_var=False,
                 init_status={},
                 pressure_ratio=0.03,
                 epsilon={
                     'At': 0.3,
                     'press_up_f': 0.2,
                     'press_down_f': 0.2,
                     'feed': 0.3,
                     'perm_ref': 0.1,
                     'alpha': 0.1,
                     'delta': 0.1
                 }):
        # Initialization
        self.num_membranes = num_membranes
        self.lb_area, self.ub_area, self.ub_acell = Configuration.default_bounds(
            self.num_membranes)
        # TODO: replace assert by if and raise
        try:
            if ub_area:
                assert len(ub_area) == num_membranes
                self.ub_area = ub_area
            if lb_area:
                assert len(lb_area) == num_membranes
                self.lb_area = lb_area
            if ub_acell:
                assert len(ub_acell) == num_membranes
                self.ub_acell = ub_acell

        except Exception:
            logger.exception("Size of ub_area; lb_area and ub_acell must "
                             "match with number's number")
            raise

        self.uniform_pup = uniform_pup
        self.vp = vp
        self.variable_perm = variable_perm
        self.fixing_var = fixing_var
        self.init_status = init_status
        self.labels = None

        self.pressure_ratio = pressure_ratio
        self.epsilon = epsilon

        # creation of discretisation table
        self.discretisation = []
        self.discretise_membrane()

    @staticmethod
    def default_bounds(num_membranes):
        """Generate default bounds if not given.

        For `lb_area`, `ub_area`, `ub_acell` respecting the number of membrane.

        Args:
            num_membranes (`Int`) : number of membranes

        Returns:
            Not empty list of (`lb_area`, `ub_area`, `ub_acell`)

        Raises:
            ValueError: If membranes's number is bigger than 3 (`num_membranes > 3`)
        """

        if num_membranes == 1:
            lb_area = [1]
            ub_area = [10000]
            ub_acell = [25]

        elif num_membranes == 2:
            lb_area = [1, 0.5]
            ub_area = [10000, 5000]
            ub_acell = [25, 10]

        elif num_membranes == 3:
            lb_area = [1, 0.5, 1]
            ub_area = [10000, 5000, 1000]
            ub_acell = [25, 10, 15]
        else:
            logger.exception("ERROR : Number of membranes must be <= 3")
            raise ValueError("Number of membranes must be <= 3")

        return lb_area, ub_area, ub_acell

    def discretise_membrane(self):
        """Discretise each membranes's area surface into small cells."""
        self.discretisation = [mem + 1 for mem in range(self.num_membranes)]
        # initialisation of discretisation with the formula below
        for mem in range(self.num_membranes):
            n = self.ub_area[mem] / self.ub_acell[mem]
            try:
                assert n >= 20
            except Exception:
                logger.exception("Error : number of discretisation too low"
                                 "(n[{}] = {})".format(mem + 1, n))
                raise
            else:
                self.discretisation[mem] = math.ceil(n)


def build_model(parameter, fname, perm_filename, fname_eco, fname_mask=''):
    """ callback to create the `Pyomo` model (`mind.system.MembranesDesignModel`).

    Args:
        parameter (`mind.builder.Configuration`) : configuration of desing process

        fname (`str`) : filename containing real world instance's description.

        perm_filename (`str`) : filename containing permeability's informations.

        fname_eco (`str`) : filename containing objective funcion data's informations.

        fname_mask (`str`) : filename containing fixing's variable informations (`default = ''`).

    Returns:
        return `mind.system.MembranesDesignModel` object (model created).

    Raises:
        Exception : if `Pyomo` model's instance creation failed.
        Exception : if datafile's format are not respected (`see N2Capture's example`).
    """
    # # Build the model
    logger.info('Creation of the pyomo model object ...')

    # loading permeability parameter informations
    try:
        permeability_data = parse_permeability_data(perm_filename, parameter)
    except Exception:
        logger.exception('Error in Permeability datafile lecture : %s',
                         perm_filename)
        raise
    else:
        # loading economic data
        # data_eco =
        # modelisation = MembranesDesignGas(parameter, permeability_data, data_eco)

        # TODO: check if liquid or not
        try:
            modelisation = MembranesDesignGas(parameter, permeability_data,
                                              fname_eco)
            assert modelisation.abstractModel is not None
        except Exception:
            logger.exception('Model object creation failed')
            raise
        else:
            modelisation.filename = fname
            modelisation.perm_filename = perm_filename
            modelisation.eco_filename = fname_eco
            modelisation.mask_filename = fname_mask
            #  create instance
            modelisation.create_process_model()
            logger.info("Instantiation  of the model object ...")
            modelisation.create_process_instance(fname)
        return modelisation


class GasItemPerm:
    """Data structure used to store gas components permeances's value when
     `permeability's variables` are fixed (constant).

    Attributes:
        index (`Int`): Index of component
        lb (`Float`): lower bound of component permeance
        value (`Float`): value of component permeance if given
        ub (`Float`): lower bound of component permeance

    """

    def __init__(self, index, lb, value, ub):
        # initialisation of gas permeance bound or values
        self.index = index
        self.lb = lb
        self.value = value
        self.ub = ub

    def __str__(self):
        return ('index = {} \t lb = {} value = {} \t ub = {}'.format(
            self.index, self.lb, self.value, self.ub))


class PermType:
    """Data structure used to store permeability's information.

    Attributes:
        robeson_multi (flaot) : robeson bound multiplicater

        robeson_power (flaot) : robeson bound power

        ub_alpha (flaot) : upper bound of \\(\\alpha\\)

        lb_alpha (flaot) : lower bound of \\(\\alpha\\)

        thickness (flaot) : thickness of membrane

        mem_out_prod (`str`) : 'RET' or 'PERM' indicating the position of `final_product`

        component_item (`mind.builder.GasItemPerm`) : component permeances's value

        which_mem (`List[Int]`) : data structure manipulating information about
        association of membrane's postion and membrane's type.

    """

    def __init__(self, robeson_multi, robeson_power, ub_alpha, lb_alpha,
                 component_item, thickness, mem_out_prod, which_mem):
        # Initalise some values
        self.robeson_multi = robeson_multi
        self.robeson_power = robeson_power
        self.ub_alpha = ub_alpha
        self.lb_alpha = lb_alpha
        self.thickness = thickness
        self.mem_out_prod = mem_out_prod
        self.component_item = component_item  # list of class GasItemPerm
        self.thickness = thickness
        self.which_mem = which_mem  # list of integer

    def __str__(self):
        # for i in range(0, len(self.component_item)):
        #     print(self.component_item[i])
        return ("PermType (" + '\nrobeson_multi = ' + str(self.robeson_multi) +
                '\nrobeson_power = ' + str(self.robeson_power) +
                '\nub_alpha = ' + str(self.ub_alpha) + '\nlb_alpha = ' +
                str(self.lb_alpha) + '\nthickness = ' + str(self.thickness) +
                '\ncomponent_item = ' + str(self.component_item) +
                '\nmem_out_prod = ' + str(self.mem_out_prod) +
                '\nwhich_mem = ' + str(self.which_mem))


def delete_value_from(list_of_line, value):
    index = 0
    while index < len(list_of_line):
        if list_of_line[index][0] == value:
            list_of_line.pop(index)
        else:
            index += 1


def parser_variable_permeability_data(file, permeability_data):
    """Permeability's data parser.

    When permeability's variables in model are not fixed.

    Args:
        file (`_io.TextIOWrapper`) : permeability 's datafile

        permeability_data (dict) : data structure which will finally
        contain permeability's informations.

    Returns:
        a dictionary containing permeability's data

    Raises:
        Exception : if datafile format are not repected during lecture of file
    """

    contents = file.readlines()
    delete_value_from(contents, "#")
    delete_value_from(contents, "\n")
    txt = []
    for line in contents:
        txt.append(line.replace('\n', ''))

    contents = txt

    # set mem_type_set := A B
    mem_type = contents[0]
    begining_index = mem_type.find('=')
    mem_type = mem_type[begining_index + 1:]
    mem_type = mem_type.split()
    contents.remove(contents[0])

    for type_mem in mem_type:
        robeson_multiplicater = None
        robeson_power = None
        ub_alpha = None
        lb_alpha = None
        component_item = []
        thickness = 1
        mem_out_prod = "RET"

        permeability_data[type_mem] = PermType(robeson_multiplicater,
                                               robeson_power, ub_alpha,
                                               lb_alpha, component_item,
                                               thickness, mem_out_prod, [])

    # param Robeson_multi :=
    contents.remove(contents[0])
    for type_mem in mem_type:
        multiplicater = contents[0].split()
        index = multiplicater[0]
        value = float(multiplicater[-1])
        contents.remove(contents[0])
        # convert from barrer to xxx
        permeability_data[index].robeson_multi = value * 3.347e-05

    # param Robeson_power :=
    contents.remove(contents[0])
    for type_mem in mem_type:
        power = contents[0].split()
        index = power[0]
        value = float(power[-1])
        contents.remove(contents[0])
        permeability_data[index].robeson_power = value

    # param alpha_ub_bounds :=
    contents.remove(contents[0])
    for type_mem in mem_type:
        alpha_bounds = contents[0].split()
        index = alpha_bounds[0]
        value = float(alpha_bounds[-1])
        contents.remove(contents[0])
        permeability_data[index].ub_alpha = value

    # param alpha_lb_bounds :=
    contents.remove(contents[0])
    for type_mem in mem_type:
        alpha_bounds = contents[0].split()
        index = alpha_bounds[0]
        value = float(alpha_bounds[-1])
        contents.remove(contents[0])
        permeability_data[index].lb_alpha = value

    # permeability bounds lb
    contents.remove(contents[0])
    for type_mem in mem_type:
        perm_bounds = contents[0].split()
        index = perm_bounds[0]
        element = perm_bounds[1]
        value = float(perm_bounds[2]) * 3.347e-05
        contents.remove(contents[0])
        item = GasItemPerm(element, value, None, None)
        permeability_data[index].component_item.append(item)

    # permeability bounds ub
    contents.remove(contents[0])
    for type_mem in mem_type:
        perm_bounds = contents[0].split()
        index = perm_bounds[0]
        element = perm_bounds[1]
        value = float(perm_bounds[2]) * 3.347e-05
        contents.remove(contents[0])
        permeability_data[index].component_item[0].ub = value

    # param thickness :=
    contents.remove(contents[0])
    for type_mem in mem_type:
        thickness = contents[0].split()
        index = thickness[0]
        value = float(thickness[-1])
        contents.remove(contents[0])
        permeability_data[index].thickness = value

    # param mem_product :=
    contents.remove(contents[0])
    for type_mem in mem_type:
        mem_product = contents[0].split()
        index = mem_product[0]
        value = mem_product[1]
        permeability_data[index].mem_out_prod = value
        contents.remove(contents[0])

    # param mem_type :=
    if len(contents) > 0:
        contents.remove(contents[0])
    while len(contents) > 0:
        mem_list = contents[0]
        mem_list = mem_list.split()
        mem = int(mem_list[0])
        index = mem_list[-1]
        permeability_data[index].which_mem.append(mem)
        contents.remove(contents[0])

    return permeability_data


def parser_fixed_permeability_data(file, permeability_data):
    """Permeability's data parser.

    When permeability's variables in model are fixed.

    Args:
        file (`_io.TextIOWrapper`) : permeability 's datafile

        permeability_data (dict) : data structure which will finally
        contain permeability's informations.

    Returns:
        a dictionary containing permeability's data

    Raises:
        Exception : if datafile format are not repected during lecture of file
    """
    contents = file.readlines()
    delete_value_from(contents, "#")
    delete_value_from(contents, "\n")

    txt = []
    for line in contents:
        txt.append(line.replace('\n', ''))

    contents = txt
    # set mem_type_set := A B
    mem_type = contents[0]
    begining_index = mem_type.find('=')
    mem_type = mem_type[begining_index + 1:]
    mem_type = mem_type.split()
    contents.remove(contents[0])

    # param nb_gas := 2
    nb_components = contents[0]
    nb_gas = int(nb_components[-1])
    contents.remove(contents[0])

    # param permeability
    contents.remove(contents[0])

    for type_membrane in mem_type:
        # initialisation
        # defining the dictionary entry for each type of membrane

        robeson_multi = None
        robeson_power = None
        ub_alpha = None
        lb_alpha = None
        component_item = []
        thickness = 1  # default value
        mem_out_prod = "RET"  # default value

        permeability_data[type_membrane] = PermType(robeson_multi,
                                                    robeson_power, ub_alpha,
                                                    lb_alpha, component_item,
                                                    thickness, mem_out_prod, [])

    for type_membrane in mem_type:
        # read and save pair of (component -> perm value)
        for j in range(nb_gas):
            permeance = contents[0]
            permeance = permeance.split()
            index = permeance[0]
            element = permeance[1]
            # convert from barrer to # XXX
            value = float(permeance[2]) * 3.347e-05
            item = GasItemPerm(element, value, value, value)
            permeability_data[index].component_item.append(item)
            contents.remove(contents[0])

    # param thickness
    contents.remove(contents[0])
    for type_membrane in mem_type:
        thickness = contents[0]
        thickness = thickness.split()
        index = thickness[0]
        thick = float(thickness[-1])
        permeability_data[index].thickness = float(thick)
        contents.remove(contents[0])

    # param mem_product
    contents.remove(contents[0])
    for type_membrane in mem_type:
        mem_product = contents[0]
        mem_product = mem_product.split()
        index = mem_product[0]
        mem_out_prod = mem_product[1]
        permeability_data[index].mem_out_prod = mem_out_prod
        contents.remove(contents[0])

    if len(contents) > 0:
        contents.remove(contents[0])
    while len(contents) > 0:
        mem_list = contents[0]
        mem_list = mem_list.split()
        mem = int(mem_list[0])
        index = mem_list[-1]
        permeability_data[index].which_mem.append(mem)
        contents.remove(contents[0])

    return permeability_data


def parse_permeability_data(filename, parameter):
    """Permeability's data parser.

    Args:
        filename (`str`) : permeability 's datafile

        parameter (`mind.builder.Configuration`) : process design configuration

    Returns:
        a dictionary containing permeability's data

    Raises:
        Exception : if datafile format are not repected during lecture of file
    """

    permeability_data = {}
    with open(filename, 'r') as file:
        if parameter.variable_perm:
            # permeability is variable
            permeability_data = parser_variable_permeability_data(
                file, permeability_data)

        else:
            # permeability is fixed
            permeability_data = parser_fixed_permeability_data(
                file, permeability_data)

    return permeability_data
