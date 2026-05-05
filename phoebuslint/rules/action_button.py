from ..linter import LintRule, RuleViolation
from phoebusgen.v4 import Screen
from phoebusgen.v4.widgets import Widget, ActionButton


class ActionButtonHasNoActions(LintRule):
    """Rule that checks if an ActionButton widget has no actions defined."""

    rule_code = "AB101"
    description = "ActionButton widget has no actions defined."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        rule_violations = []
        for widget in screen.get_widgets_by_type(ActionButton):
            if not widget.actions:
                rule_violations.append(
                    cls.rule_violation_factory(screen=screen, widget=widget)
                )
        return rule_violations


class ActionButtonHasTooManyActions(LintRule):
    """Rule that checks if an ActionButton widget has more than 3 actions defined."""

    rule_code = "AB102"
    description = "ActionButton widget has more than 3 actions defined."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        rule_violations = []
        for widget in screen.get_widgets_by_type(ActionButton):
            if len(widget.actions) > 3:
                rule_violations.append(
                    cls.rule_violation_factory(screen=screen, widget=widget)
                )
        return rule_violations