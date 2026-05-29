from phoebusgen.v4 import Screen
from phoebusgen.v4.widgets import ActionButton

from ..linter import FixableLintRule, LintRule, RuleViolation
from ..log import logger


class ActionButtonHasNoActions(FixableLintRule):
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

    @classmethod
    def fix(cls, screen: Screen) -> None:
        for widget in (w for w in screen.get_all_widgets() if isinstance(w, ActionButton)):
            if not widget.actions:
                if widget.parent:
                    logger.info(f"Removing button {widget.name} with no actions")
                    widget.parent.remove_widget(widget)


# TODO: Make this threshold configurable
class ActionButtonHasTooManyActions(LintRule):
    """Rule that checks if an ActionButton widget has more than 15 actions defined."""

    rule_code = "AB102"
    description = "ActionButton widget has more than 15 actions defined."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        rule_violations = []
        for widget in screen.get_widgets_by_type(ActionButton):
            if len(widget.actions) > 15:
                rule_violations.append(
                    cls.rule_violation_factory(screen=screen, widget=widget, details=cls.description + f" ({len(widget.actions)} actions)")
                )
        return rule_violations
