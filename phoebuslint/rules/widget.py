from phoebusgen import Screen
from ..linter import LintRule, RuleViolation


class WidgetHeightOrWidthZeroOrNegative(LintRule):
    """Rule that checks if a widget has zero or negative height or width."""

    rule_code = "W101"
    description = "Widget has zero or negative height or width."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation] | None:
        rule_violations = []
        for widget in screen.get_widgets():
            if widget.width <= 0 or widget.height <= 0:
                rule_violations.append(
                    cls.rule_violation_factory(screen=screen, widget=widget)
                )
        return rule_violations if len(rule_violations) > 0 else None


class WidgetOutOfBounds(LintRule):
    """Rule that checks for widgets that are out of screen bounds."""

    rule_code = "W102"
    description = "Widget is out of screen bounds"

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation] | None:
        rule_violations = []
        for widget in screen.get_widgets():
            if (
                widget.x < 0
                or widget.y < 0
                or widget.x + widget.width > screen.width
                or widget.y + widget.height > screen.height
            ):
                rule_violations.append(
                    cls.rule_violation_factory(screen=screen, widget=widget)
                )
        return rule_violations if len(rule_violations) > 0 else None
