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

# -----------------------------------------------------------

class DependencyType(enum.Enum):
    COMPONENT_COUNT = enum.auto()  
    VALUE = enum.auto()  

# -----------------------------------------------------------

class FILE(enum.Enum):
    CONFIG = enum.auto()
    DATA = enum.auto()
    PERM = enum.auto()
    ECO = enum.auto()
    COMMAND = enum.auto()
