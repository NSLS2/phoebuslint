import os
from xml.etree import ElementTree as ET

from phoebusgen.v4 import Screen

from ..linter import FixableLintRule, LintRule, RuleViolation, SeverityLevel


class MissingDisplayTag(LintRule):
    """Rule that checks if a screen is missing the top-level <display> tag."""

    rule_code = "S102"
    description = "Screen is missing the top-level <display> tag."
    rule_severity = SeverityLevel.CRITICAL

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        if screen.bob_file is None:
            raise ValueError("Screen must have a bob_file attribute!")

        tree = ET.parse(screen.bob_file)
        root = tree.getroot()
        if root.tag != "display":
            return [cls.rule_violation_factory(screen)]
        return []


class TopLevelTagNotDisplay(LintRule):
    """Rule that checks if a screen has top-level tags other than <display>."""

    rule_code = "S103"
    description = "Root tag is not <display>."
    rule_severity = SeverityLevel.CRITICAL

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        if screen.root.tag != "display":
            return [
                cls.rule_violation_factory(
                    screen, details=f"{cls.description} Tag: {screen.root.tag}"
                )
            ]
        return []


class ExtraTagsInDisplay(LintRule):
    """Rule that checks if a screen has extra tags inside the <display> tag."""

    rule_code = "S104"
    description = "Unexpected tag found in <display>."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        violations = []
        for display_child in screen.root:
            if display_child.tag not in ["widget", *screen.get_property_names()]:
                violations.append(
                    cls.rule_violation_factory(
                        screen, details=f"{cls.description} Tag: {display_child.tag}"
                    )
                )
        return violations


class TitleEmptyOrNotSet(LintRule):
    """Rule that checks if a screen has an empty or not set title."""

    rule_code = "S105"
    description = "Screen has an empty or not set title."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        if screen.name is None or screen.name.strip() == "":
            return [cls.rule_violation_factory(screen)]
        return []


class DefaultTitleSet(LintRule):
    """Rule that checks if a screen has the default title set."""

    rule_code = "S106"
    description = "Screen has the default title set."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        # Phoebusgen will set the screen name to "Display" if no name is found
        if screen.name == "Display":
            return [cls.rule_violation_factory(screen)]
        return []


class EmptyScreen(FixableLintRule):
    """Rule that checks if a screen is empty (has no widgets)."""

    rule_code = "S107"
    description = "Screen is empty (has no widgets)."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        if len(screen.get_widgets()) == 0:
            return [cls.rule_violation_factory(screen=screen)]
        return []

    @classmethod
    def fix(cls, screen: Screen) -> None:
        if screen.bob_file is not None:
            os.remove(screen.bob_file)


class ScreenHeightOrWidthZeroOrNegative(LintRule):
    """Rule that checks if a screen has zero or negative height."""

    rule_code = "S108"
    description = "Screen has zero or negative height or width."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        if screen.height <= 0 or screen.width <= 0:
            return [cls.rule_violation_factory(screen=screen)]
        return []
