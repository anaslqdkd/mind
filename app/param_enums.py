import enum


class ParamType(enum.Enum):
    INPUT = enum.auto()  # seulement de l'input
    INPUT_WITH_UNITY = enum.auto()  # parametre avec unité dans un menu deroulant
    BOOLEAN = enum.auto()  # checkbox
    SELECT = enum.auto()  # menu deroulable
    BOOLEAN_WITH_INPUT = enum.auto()  # maxiteration
    BOOLEAN_WITH_INPUT_WITH_UNITY = enum.auto()  # pour maxtime
    COMPONENT = enum.auto()  # set components
    COMPONENT_WITH_VALUE = enum.auto()  # components xin
    COMPONENT_WITH_VALUE_WITH_UNITY = enum.auto()  # components xin
    FIXED_WITH_INPUT = enum.auto()  # components xin
    RADIO = enum.auto()
    COMPONENT_SELECTOR = enum.auto()
    SPIN_BOX = enum.auto()
    FILECHOOSER = enum.auto()
    FIXED_WITH_SELECT = enum.auto()
    FIXED_PERM = enum.auto()
    FIXED_MEMBRANE = enum.auto()
    FIXED_COMPONENT = enum.auto()
    FIXED_MEMBRANE_SELECT = enum.auto()
    FIXED_MEM_TYPE = enum.auto()


# -----------------------------------------------------------


class DependencyType(enum.Enum):
    COMPONENT_COUNT = enum.auto()
    VALUE = enum.auto()
    VISIBLE = enum.auto()

# TODO: add dependency type for if visible or not
# -----------------------------------------------------------


class FILE(enum.Enum):
    CONFIG = enum.auto()
    DATA = enum.auto()
    PERM = enum.auto()
    ECO = enum.auto()
    COMMAND = enum.auto()
