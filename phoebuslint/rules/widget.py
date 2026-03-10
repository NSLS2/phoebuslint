from phoebusgen.v4 import Screen
from phoebusgen.v4.widgets import ActionButton, Label, TextUpdate

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


class ActionButtonWithNoActions(LintRule):
    """Rule that checks for ActionButton widgets that have no actions defined."""

    rule_code = "W103"
    description = "ActionButton has no actions defined."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation] | None:
        rule_violations = []
        for widget in screen.get_widgets_by_type(ActionButton):
            if len(widget.actions) == 0:
                rule_violations.append(
                    cls.rule_violation_factory(screen=screen, widget=widget)
                )
        return rule_violations if len(rule_violations) > 0 else None


class EmptyLabel(LintRule):
    """Rule that checks for Label widgets that have empty text."""

    rule_code = "W104"
    description = "Label has empty text."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation] | None:
        rule_violations = []
        for widget in screen.get_widgets_by_type(Label):
            if widget.text.strip() == "":
                rule_violations.append(
                    cls.rule_violation_factory(screen=screen, widget=widget)
                )
        return rule_violations if len(rule_violations) > 0 else None


class LabelWithExcessiveTextLength(LintRule):
    """Rule that checks for Label widgets that have excessively long text."""

    rule_code = "W105"
    description = "Label has excessively long text."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation] | None:
        rule_violations = []
        for widget in screen.get_widgets_by_type(Label):
            # Assumes typical DPI of 96 and average character width of font size * 0.5
            # TODO: Make this configurable
            if (
                len(widget.text) * widget.font.size * 0.5 * 96 / 72 > widget.width
                and not widget.auto_size
            ):
                rule_violations.append(
                    cls.rule_violation_factory(screen=screen, widget=widget)
                )
        return rule_violations if len(rule_violations) > 0 else None


class TextUpdateWithNoDefinedPV(LintRule):
    """Rule that checks for widgets with text updates that have no defined PV."""

    rule_code = "W106"
    description = "Text update widget with no defined PV."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation] | None:
        rule_violations = []
        for text_update in screen.get_widgets_by_type(TextUpdate):
            if text_update.pv_name is None or text_update.pv_name.strip() == "":
                rule_violations.append(
                    cls.rule_violation_factory(screen=screen, widget=text_update)
                )
        return rule_violations if len(rule_violations) > 0 else None
