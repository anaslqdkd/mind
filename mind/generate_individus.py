from random import randint, choice
import yaml
import os
import pprint
from collections import ChainMap

pp = pprint.PrettyPrinter(indent=4)

def generate(filename, nb_inds, mem_type, mem=3):
    """Generate random prototypes individu.
    Attributes:
        mem_type (list): authorized types of membranes
    """
    with open(filename, "a") as file:
        for ind in range(1, nb_inds + 1):
            mem = randint(1, mem + 1)
            mem = 3 if mem > 3 else mem

            mem_dict = {'num_membranes':mem}
            type_dict = {'mem_type':{s:choice(mem_type) for s in range(1, mem + 1)}}

            lb_area_dict = {'lb_area':{s:choice(range(1, 101)) for s in range(1, mem + 1)}}

            ub_acell_dict = {'ub_acell':{s:choice(range(1, 50)) for s in range(1, mem + 1)}}

            ub_area_dict = {'ub_area':{s:choice(range(200, 1000)) for s in range(1, mem + 1)}}

            template_dict = dict(
                ChainMap(
                    {'lb_bounds': None},
                    {'ub_bounds': None},
                    {'fixing': None},
                    ub_area_dict, ub_acell_dict,
                    lb_area_dict, type_dict,
                    mem_dict))

            # pp.pprint(template_dict)

            final = {
                f'ind_{ind}' : template_dict
            }

            d = yaml.dump(final, file)




if __name__ == "__main__":
    mem_type = ['A', 'B']

    CURR_DIR = os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))) + os.path.sep

    # data = parse_list_prototype(CURR_DIR + filename)
    generate(CURR_DIR + "test.yml", 100, mem_type)
