from .base import LintRule, RuleViolation
from phoebusgen import Screen
from ..linter import PhoebusLinter
from pathlib import Path

class TitleEmptyOrNotSet(LintRule):
    """Rule that checks if a screen has an empty or not set title."""

    rule_code = "S1001"
    description = "Screen has an empty or not set title."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation] | None:
        if screen.name is None or screen.name.strip() == "":
            return [cls.rule_violation_factory(screen)]


class DefaultTitleSet(LintRule):
    """Rule that checks if a screen has the default title set."""

    rule_code = "S1002"
    description = "Screen has the default title set."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation] | None:

        # Phoebusgen will automatically set the screen name to "Display" if no name is found
        if screen.name == "Display":
            return [cls.rule_violation_factory(screen)]


class EmptyScreen(LintRule):
    """Rule that checks if a screen is empty (has no widgets)."""

    rule_code = "S1003"
    description = "Screen is empty (has no widgets)."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation] | None:
        if len(screen.get_widgets()) == 0:
            return [cls.rule_violation_factory(screen=screen)]