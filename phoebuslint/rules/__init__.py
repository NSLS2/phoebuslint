from .macros import UndefinedMacrosInScreenTransition
from .screen import (
    DefaultTitleSet,
    EmptyScreen,
    ExtraTagsInDisplay,
    ScreenHeightOrWidthZeroOrNegative,
    TitleEmptyOrNotSet,
    TopLevelTagNotDisplay,
)
from .widget import (
    EmbeddedDisplayNoFilePathSet,
    EmbeddedDisplayPathDoesNotExist,
    EmbeddedDisplayPathIsOpiFile,
    OpenDisplayActionPathDoesNotExist,
    OpenDisplayActionPathIsOpiFile,
    OpenDisplayActionPathNotSet,
    OpenFileActionPathDoesNotExist,
    OpenWebpageActionInvalidUrl,
    WidgetHeightOrWidthZeroOrNegative,
    WidgetOutOfBounds,
)

__all__ = [
    "UndefinedMacrosInScreenTransition",
    "TitleEmptyOrNotSet",
    "DefaultTitleSet",
    "EmptyScreen",
    "WidgetHeightOrWidthZeroOrNegative",
    "WidgetOutOfBounds",
    "ScreenHeightOrWidthZeroOrNegative",
    "ExtraTagsInDisplay",
    "TopLevelTagNotDisplay",
    "EmbeddedDisplayNoFilePathSet",
    "OpenWebpageActionInvalidUrl",
    "OpenDisplayActionPathDoesNotExist",
    "OpenFileActionPathDoesNotExist",
    "OpenDisplayActionPathIsOpiFile",
    "OpenDisplayActionPathNotSet",
    "EmbeddedDisplayPathIsOpiFile",
    "EmbeddedDisplayPathDoesNotExist",
]
