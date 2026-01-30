from abc import ABC, abstractmethod
from phoebusgen import Screen
from phoebusgen.widgets import Widget
from ..utils import SeverityLevel
from ..linter import PhoebusLinter
from pathlib import Path
from dataclasses import dataclass


@dataclass
class RuleViolation:
    """Dataclass representing a rule violation found during linting.

    Attributes:
        rule_name (str): The name of the rule that was violated.
        rule_code (str): The code of the rule that was violated.
        rule_severity (SeverityLevel): The severity level of the rule violation.
        screen (Screen): The screen where the violation was found.
        widget (Widget | None): The widget where the violation was found, if applicable.
        property (str | None): The property name where the violation was found, if applicable.
        property_element (str | None): The specific element of the property where the violation was found, if applicable.
        details (str | None): Additional details about the violation, if applicable.
    """

    rule_name: str
    rule_code: str
    rule_severity: SeverityLevel
    screen: Screen
    widget: Widget | None = None
    property: str | None = None
    property_element: str | None = None
    details: str | None = None

    def __str__(self) -> str:
        location = f"Screen: {self.screen.bob_file}"
        if self.widget:
            location += f", Widget: {self.widget.name}"
        if self.property:
            location += f", Property: {self.property}"
        if self.property_element:
            location += f", Element: {self.property_element}"
        return f"[{self.rule_code}] {self.rule_name}: {self.details} ({location})"


class LintRule(ABC):
    """Abstract base class for linting stateless linting rule."""

    rule_code: str
    description: str
    rule_severity: SeverityLevel = SeverityLevel.WARNING

    @classmethod
    @abstractmethod
    def check(cls, screen: Screen) -> list[RuleViolation] | None:
        """Check the given  element for issue covered by specific rule.

        Args:
            element (PhoebusElementT): The phoebus element to be checked.
        Returns:
            list[RuleViolation] | None: List of issues found, or None if no issues found.
        """
        ...

    @classmethod
    def rule_violation_factory(
        cls,
        screen: Screen,
        widget: Widget | None = None,
        property: str | None = None,
        property_element: str | None = None,
        details: str | None = None,
    ) -> RuleViolation:
        """Factory method to create a RuleViolation instance for this rule.

        Args:
            screen (Screen): The screen where the violation was found.
            widget (Widget | None): The widget where the violation was found, if applicable.
            property (str | None): The property name where the violation was found, if applicable.
            property_element (str | None): The specific element of the property where the violation was found, if applicable.
            details (str | None): Additional details about the violation, if applicable.
        Returns:
            RuleViolation: The created RuleViolation instance.
        """
        return RuleViolation(
            rule_name=cls.__name__,
            rule_code=cls.rule_code,
            rule_severity=cls.rule_severity,
            screen=screen,
            widget=widget,
            property=property,
            property_element=property_element,
            details=details if details else cls.description,
        )


class RecursiveLintRule(ABC):
    """Abstract base class for linting rules that require recursive linting of linked screens."""

    rule_code: str
    description: str
    rule_severity: SeverityLevel = SeverityLevel.WARNING

    @classmethod
    @abstractmethod
    def check(
        cls,
        linter: PhoebusLinter,
        screen: Screen,
        visited_screens: dict[Path, list[RuleViolation]],
    ) -> list[RuleViolation] | None:
        """Check the given phoebus element for issue covered by specific rule, potentially requiring recursive linting.

        Args:
            linter (PhoebusLinter): The linter instance. Used to recursively lint linked screens.
            screen (Screen): The screen to be checked.
            visited_screens (dict[Path, list[RuleViolation]]): Dictionary of already visited screens to avoid re-linting.
        Returns:
            dict[Path, list[RuleViolation]] | None: Dictionary of rule violations found, or None if no violations found.
        """
        ...
