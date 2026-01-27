from ..linter import LintRule, RecursiveLintRule
from phoebusgen.widgets import EmbeddedDisplay
from phoebusgen.properties import ResizeBehavior
from phoebusgen import Screen
from pathlib import Path

# class EmbeddedDisplayFileDoesNotExist(LintRule):
#     """Rule that checks if an EmbeddedDisplay widget references a non-existent file."""

#     rule_code = "ED101"
#     description = "EmbeddedDisplay references a non-existent file."

#     @classmethod
#     def check(cls, screen: Screen) -> bool:

#         for embedded_display in screen.get_widgets_by_type(EmbeddedDisplay):
#             if embedded_display.file is not None and not Path(embedded_display.file).is_file() :
#                 return True
#         return embedded_display.file is None or not Path(embedded_display.file).is_file() or not Path(embedded_display.file).suffix in [".bob", ".opi"]
    
# class EmbeddedDisplayTooLargeForGivenDims(LintRule):
#     """Rule that checks if an EmbeddedDisplay widget has dimensions larger than the referenced screen."""

#     rule_code = "ED102"
#     description = "Screen linked to by EmbeddedDisplay is larger than the EmbeddedDisplay dimensions."

#     @classmethod
#     def check(cls, element: EmbeddedDisplay) -> bool:
#         referenced_screen = Screen(f_name=element.file)
#         return element.resize_behavior == ResizeBehavior.NO_RESIZE and (referenced_screen.width > element.width or referenced_screen.height > element.height)
