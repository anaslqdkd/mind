""" Fixing variables with values.

or in other words, fix certain equipment or installation structures for
Optimize operational conditions with the architecture or an existing solution.

Notes :
    respect certain format in the input of pair (variable = values)].
"""

import logging

# logging variable
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)
handler = logging.StreamHandler()
# handler = logging.FileHandler('log1.txt')
logger.addHandler(handler)
formatter = logging.Formatter(fmt='[%(asctime)s] %(levelname)s : %(message)s',
                              datefmt='%a, %d %b %Y %H:%M:%S')
handler.setFormatter(formatter)


def fixing_method(filename, model, parameter):
    """Fixing or initializing some variables with their values given a file.

    Args:
        filename (`str`) : filename containing informations on variables to be fixed
        model (`mind.system.MembranesDesignModel`): desing Process model's instance
        parameter (`mind.builder.Configuration`): desing process configuration

    Usage:
        - fix Feed_mem:#1 5 -> (means) fix  Feed_mem[1] to value 5
        - init XIN_mem:#1,$O2 2 -> (means) initialize XIN_mem[1, o2] to value 2
        - fix splitRET:#1,#1 0.5 -> (means) fix splitRET[1][1] to value 0.5
        - fix OUT_prod 5 -> (means) fix OUT_prod to value 5
    Raises:
        Exception : `If` datafile of filename format is not respected.
    """
    logger.info("Fixing some variables listed in the file %s", filename)

    # defined_sequence = ['fix', 'init', 'bound']

    with open(filename, 'r') as file:
        for line in file:
            if line == "\n":
                pass
            elif line[0] == "#" or line[0] == "/*":
                logger.info("Comments are ignored : %s", line)
            else:
                line = line.split()
                if not line:
                    logger.warn('Undifined sequence character [correct the file format \n]')
                elif line[0] == 'fix' or line[0] == 'init':
                    try:
                        model.find_component(line[1]).value = float(line[2])
                    except Exception:
                        logger.warn('Problem with variable name %s', line[1])
                        logger.warn("Variable '%s' can\'t be fixed", line[1])
                    else:
                        model.find_component(line[1]).fixed = True

                elif line[0] == 'bound':
                    try:
                        model.find_component(line[1]).setlb(float(line[2]))
                        model.find_component(line[1]).setub(float(line[3]))
                    except Exception as e:
                        logger.warn('Problem with variable name %s', line[1])
                        logger.warn("Variable '%s' can\'t be bounded", line[1])
                        raise
                else:
                    logger.warn('Undifined sequence character %s', line[0])
                    # raise


def remove_var_initialisations(parameter):
    """Clear initialization status of each variables.

    Args:

        parameter (`mind.builder.Configuration`): desing process configuration
    """
    for elem in parameter.init_status.keys():
        parameter.init_status[elem] = False
