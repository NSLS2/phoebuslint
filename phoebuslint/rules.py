from collections.abc import ABC, abstractmethod
from phoebusgen import Screen

class LintRule(ABC):
    """Abstract base class for linting rules."""

    rule_code: int
    description: str

    @abstractmethod
    def check(self, screen: Screen) -> list[str]:
        """Check the given screen for linting issues.

        Args:
            screen (Screen): The screen to be checked.
        Returns:
            list[str]: A list of linting issues found in the screen.
        """
        pass

class NoTitleSetRule(LintRule):
    """Rule that checks if a screen has a title set."""

    rule_code = 1001
    description = "Screen does not have a title set."

    def check(self, screen: Screen) -> list[str]:
        if not screen.title or screen.title.strip() == "":
            return [f"[{self.rule_code}] {self.description}"]
        return []


class DefaultTitleSet(LintRule):
    """Rule that checks if a screen has the default title set."""

    rule_code = 1002
    description = "Screen has the default title set."

    def check(self, screen: Screen) -> list[str]:
        if screen.title == "Display":
            return [f"[{self.rule_code}] {self.description}"]
        return []
    
class EmptyScreen(LintRule):
    """Rule that checks if a screen is empty (has no widgets)."""

    rule_code = 1003
    description = "Screen is empty (has no widgets)."

    def check(self, screen: Screen) -> list[str]:
        if not screen.widgets or len(screen.widgets) == 0:
            return [f"[{self.rule_code}] {self.description}"]
        return []