from abc import ABC, abstractmethod
from phoebusgen.properties import PropertyBase, HasText
from .utils import SeverityLevel
from typing import Generic, TypeVar

PhoebusElementT = TypeVar("PhoebusElementT", bound=PropertyBase)


class LintRule(ABC, Generic[PhoebusElementT]):
    """Abstract base class for linting rules."""

    rule_code: str
    description: str
    rule_severity: SeverityLevel = SeverityLevel.WARNING

    @classmethod
    @abstractmethod
    def check(cls, element: PhoebusElementT) -> bool:
        """Check the given phoebus element for issue covered by specific rule.

        Args:
            element (PhoebusElementT): The phoebus element to be checked.
        Returns:
            bool: True if the rule check passes, False if it fails.
        """
        ...


class EmptyText(LintRule[HasText]):
    """Rule that checks for labels with empty text."""

    rule_code = "S1004"
    description = "Label has empty text."

    @classmethod
    def check(cls, element: HasText) -> bool:
        return element.text is not None and element.text.strip() == ""
