from ..linter import RecursiveLintRule, RuleViolation
from pathlib import Path
from phoebusgen.v4 import Screen
from phoebusgen.v4.properties import HasPVName, HasText, HasMacros
import copy

def _can_expand_macros(value: str, macros: dict[str, str]) -> bool:
    """Helper function to determine if a string with macros can be fully expanded."""
    while "$(" in value:
        start_index = value.find("$(")
        end_index = value.find(")", start_index)
        if end_index == -1:
            break  # No closing parenthesis found, invalid macro syntax
        macro_name = value[start_index + 2 : end_index]
        if macro_name not in macros:
            return False  # Macro cannot be expanded
        macro_value = macros[macro_name]
        value = value[:start_index] + macro_value + value[end_index + 1 :]
    return True

class SubscreensWithUnexpandedMacros(RecursiveLintRule):
    """Rule that checks for subscreens with unexpanded macros in their file paths."""

    rule_code = "M101"
    description = "Unexpanded macros found in subscreen."

    @classmethod
    def check_for_unexpanded_macros(cls, navigation_path: list[Path], all_macros: dict[str, str], screen: Screen) -> dict[Path, list[RuleViolation]]:
        rule_violations = {}
        screen_macros = copy.deepcopy(all_macros)
        for macro in screen.macros:
            if not _can_expand_macros(screen.macros[macro], screen_macros):
                rule_violations.append(
                    cls.rule_violation_factory(screen=screen, details=f"{cls.description} Macro: {macro} Value: {screen.macros[macro]}")
                )

        screen_macros.update(screen.macros)
        for widget in screen.get_widgets():
            widget_macros = copy.deepcopy(screen_macros)
            if isinstance(widget, HasMacros):
                for macro in widget.macros:
                    if not _can_expand_macros(widget.macros[macro], screen_macros):
                        rule_violations.append(
                            cls.rule_violation_factory(screen=screen, widget=widget, details=f"{cls.description} Macro: {macro} Value: {widget.macros[macro]}")
                        )
                    else:
                        widget_macros[macro] = widget.macros[macro]

            if isinstance(widget, HasPVName):
                wi
                if not _can_expand_macros(widget.pv_name, screen_macros):
                    rule_violations.append(
                        cls.rule_violation_factory(screen=screen, widget=widget, details=f"{cls.description} PVName: {widget.pv_name}")
                    )
        return rule_violations

    @classmethod
    def check(cls, screen: Screen, visited: set[Path] = set()) -> dict[Path, list[RuleViolation]]:
        rule_violations = {}
        all_macros = copy.deepcopy(screen.macros)

        for widget in screen
        for widget in screen.get_widgets_by_type("SubScreen"):
            if widget.file and "${" in widget.file:
                rule_violations.append(
                    cls.rule_violation_factory(screen=screen, widget=widget, details=f"{cls.description} Path: {widget.file}")
                )
        return rule_violations