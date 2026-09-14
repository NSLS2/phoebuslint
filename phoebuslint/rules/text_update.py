
from phoebusgen.v4 import Screen
from phoebusgen.v4.widgets import TextUpdate

from phoebuslint.linter import LintRule, RuleViolation, get_all_widgets


class TextUpdateWithNoDefinedPV(LintRule):
    """Rule that checks for widgets with text updates that have no defined PV."""

    rule_code = "W106"
    description = "Text update widget with no defined PV."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        rule_violations = []
        for widget in get_all_widgets(screen):
            if isinstance(widget, TextUpdate) and (
                widget.pv_name is None or widget.pv_name.strip() == ""
            ):
                rule_violations.append(
                    cls.rule_violation_factory(screen=screen, widget=widget)
                )
        return rule_violations
