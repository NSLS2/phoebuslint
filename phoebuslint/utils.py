from enum import Enum

class SeverityLevel(int, Enum):
    INFO = 0
    WARNING = 1
    ERROR = 2
    CRITICAL = 3
