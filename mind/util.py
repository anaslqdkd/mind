"""Utils callback functions."""

import logging
import os
import sys

# import pickle
import json

# logging variable
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)
handler = logging.StreamHandler()
# handler = logging.FileHandler('log1.txt')
logger.addHandler(handler)
formatter = logging.Formatter(fmt='[%(asctime)s] %(levelname)s : %(message)s',
                              datefmt='%a, %d %b %Y %H:%M:%S')
handler.setFormatter(formatter)


def store_object_to_file(my_object, filename):
    """Storing an object to file using JSON

    Args:
        filename (`str`) : path to output filename
    """
    with open(filename, 'w') as file:
        json.dump(my_object, file, indent=4)


def load_object_to_file(my_object, filename):
    """Loading an object from file using JSON

    Args:
        filename (`str`) : path to input filename
    """
    with open(filename, 'r') as file:
        my_object = json.load(file)


def project_root_dir(function):
    """Decorater : return root directory of the project

    Args:

        function (`Function`) : function called

    Returns:

        return the path of the root directory
    """

    def extract_path():
        """Extract absolute path of the root directory."""
        CURR_DIR = os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))) + os.path.sep

        return CURR_DIR

    return extract_path


@project_root_dir
def generate_absolute_path():
    """Root directory of the project (absolute path)

    Returns:

        return the path of the root directory
    """

    # print(sys.path)
    # get the execution dir path
    dir = os.getcwd()
    file = sys.argv[0]

    # if file[0] == ".":
    #     file = file[1:]
    # else:
    #     None

    # traitement of file attribute
    # if file first caracter is not '.'
    # then it's launch by an application or makefile
    # else it's lauch in command line like .\mind\launcher.py
    if file[0] == ".":
        file = file[1:]
    else:
        # add separator to file
        file = os.path.sep + file

    path = dir + file
    # print(path)

    dir = os.path.dirname(path)
    # -4 because len("mind") = 4
    dir = dir[:-4]
    # print(dir)
    # print(os.path.exists(dir))

    # file = os.path.basename(path)
    # print(file)

    return dir
