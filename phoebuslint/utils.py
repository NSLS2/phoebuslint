from enum import Enum


class SeverityLevel(int, Enum):
    WARNING = 1
    ERROR = 2
    CRITICAL = 3
