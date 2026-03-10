from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import yaml
from phoebusgen.v4 import Screen
from phoebusgen.v4.widgets import Widget

# Define color codes as constants for readability
RED = "\033[31m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
BLUE = "\033[34m"
RESET = "\033[0m"  # Resets the color to default

PropertyBaseT = TypeVar("PropertyBaseT", bound=PropertyBase)

@dataclass
class RuleViolation:
    """Dataclass representing a rule violation found during linting.

    Attributes:
        rule_name (str): The name of the rule that was violated.
        rule_code (str): The code of the rule that was violated.
        rule_severity (SeverityLevel): The severity level of the rule violation.
        screen (Screen): The screen where the violation was found.
        widget (Widget | None): The widget where the violation was found.
        property (str | None): The property name where the violation was found.
        property_element (str | None): Property elem where the violation was found.
        details (str): Additional details about the violation.
    """

    rule_name: str
    rule_code: str
    rule_severity: SeverityLevel
    screen: Screen
    widget: Widget | None = None
    property: str | None = None
    property_element: str | None = None
    details: str = ""

    def __str__(self) -> str:
        location = f"Screen: {self.screen.bob_file}"
        if self.widget:
            location += f", Widget: {self.widget.name}"
        if self.property:
            location += f", Property: {self.property}"
        if self.property_element:
            location += f", Element: {self.property_element}"
        return f"[{self.rule_code}] {self.rule_name}: {self.details} ({location})"


class RuleViolationFactory:
    """Mixin class providing a factory method to create RuleViolation instances."""

    rule_code: str
    description: str
    rule_severity: SeverityLevel = SeverityLevel.WARNING

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
            widget (Widget | None): The widget where the violation was found.
            property (str | None): Property name where the violation was found.
            property_element (str | None): Property elem where the violation was found.
            details (str | None): Additional details about the violation.
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


class LintRule(RuleViolationFactory, Generic[PropertyBaseT], ABC):
    """Abstract base class for stateless linting rules."""

    @classmethod
    @abstractmethod
    def check(cls: type[PropertyBaseT], screen: Screen) -> list[RuleViolation] | None:
        """Check the given  element for issue covered by specific rule.

        Args:
            element (PhoebusElementT): The phoebus element to be checked.
        Returns:
            list[RuleViolation] | None: List of issues found, or None.
        """
        ...


class RecursiveLintRule(RuleViolationFactory, ABC):
    """ABC for linting rules that require recursive linting of linked screens."""

    @classmethod
    @abstractmethod
    def check(
        cls,
        linter: "PhoebusLinter",
        screen: Screen,
        visited: dict[Path, list[RuleViolation]] | None,
    ) -> list[RuleViolation] | None:
        """Recursively check the given screen for issues covered by this rule.

        Args:
            linter (PhoebusLinter): The linter instance. Recursively lints screens.
            screen (Screen): The screen to be checked.
            visited (dict[Path, list[RuleViolation]] | None):
                Map of paths to violations.
        Returns:
            dict[Path, list[RuleViolation]] | None: Map of paths to violations.
        """
        ...


class FixableLintRule(LintRule, ABC):
    """Abstract base class for linting rules that can be automatically fixed."""

    @classmethod
    @abstractmethod
    def fix(cls, screen: Screen) -> bool:
        """Attempt to automatically fix the issue covered by this rule on the given screen.

        Args:
            screen (Screen): The screen to attempt to fix.
        Returns:
            bool: True if a fix was applied, False otherwise.
        """
        ...


class FixableRecursiveLintRule(RecursiveLintRule, ABC):
    """Abstract base class for recursive linting rules that can be automatically fixed."""

    @classmethod
    @abstractmethod
    def fix(
        cls, linter: "PhoebusLinter", screen: Screen, visited_screens: dict[Path, bool]
    ) -> bool:
        """Attempt to automatically fix the issue covered by this rule on the given screen, potentially requiring recursive linting.

        Args:
            linter (PhoebusLinter): The linter instance. Used to recursively lint linked screens.
            screen (Screen): The screen to attempt to fix.
            visited_screens (dict[Path, bool]): Dictionary of already visited screens to avoid re-linting.
        Returns:
            bool: True if a fix was applied, False otherwise.
        """
        ...


class FixableLintRule(LintRule, ABC):
    """Abstract base class for linting rules that can be automatically fixed."""

    @classmethod
    @abstractmethod
    def fix(cls, screen: Screen) -> bool:
        """Attempt to automatically fix the issue covered by this rule on the given screen.

        Args:
            screen (Screen): The screen to attempt to fix.
        Returns:
            bool: True if a fix was applied, False otherwise.
        """
        ...


class FixableRecursiveLintRule(RecursiveLintRule, ABC):
    """Abstract base class for recursive linting rules that can be automatically fixed."""

    @classmethod
    @abstractmethod
    def fix(
        cls, linter: "PhoebusLinter", screen: Screen, visited_screens: dict[Path, bool]
    ) -> bool:
        """Attempt to automatically fix the issue covered by this rule on the given screen, potentially requiring recursive linting.

        Args:
            linter (PhoebusLinter): The linter instance. Used to recursively lint linked screens.
            screen (Screen): The screen to attempt to fix.
            visited_screens (dict[Path, bool]): Dictionary of already visited screens to avoid re-linting.
        Returns:
            bool: True if a fix was applied, False otherwise.
        """
        ...


class PhoebusLinter:
    """Class containing main linting logic for Phoebus screens."""

    def __init__(
        self,
        fail_severity: SeverityLevel = SeverityLevel.WARNING,
        disabled_rule_codes: list[str] | None = None,
    ):
        if disabled_rule_codes is None:
            disabled_rule_codes = []
        self._enabled_rules = (
            LintRule.__subclasses__() + RecursiveLintRule.__subclasses__()
        )
        for disabled_rule_code in disabled_rule_codes:
            disabled_rule = next(
                (
                    rule
                    for rule in self._enabled_rules
                    if rule.rule_code == disabled_rule_code
                ),
                None,
            )
            if disabled_rule is not None:
                self._enabled_rules.remove(disabled_rule)
        self._fail_severity = fail_severity

    @classmethod
    def from_yaml(cls, yaml_content: str) -> "PhoebusLinter":
        data = yaml.safe_load(yaml_content)
        disabled_rule_codes = data.get("disable_rules", [])
        fail_severity = SeverityLevel[data.get("fail_severity", "warning").upper()]
        return cls(fail_severity=fail_severity, disabled_rule_codes=disabled_rule_codes)

    def lint_screen(
        self, screen: Screen, visited: dict[Path, list[RuleViolation]] | None = None
    ) -> dict[Path, list[RuleViolation]]:
        """Lint a single Phoebus screen.

        Args:
            screen (Screen): The Phoebus screen to lint.
            visited (dict[Path, list[RuleViolation]]): Map of paths to violations
        Returns:
            dict[Path, list[RuleViolation]]: Map of paths to violations.
        Raises:
            ValueError: If the screen is not associated with a file path.
        """

        if visited is None:
            visited = {}
        if screen.bob_file is None:
            raise ValueError("Screen must be associated with a file path to be linted.")

        file_path = Path(screen.bob_file)

        if file_path in visited:
            return {file_path: visited[file_path]}

        visited[file_path] = []
        for rule_cls in self._enabled_rules:
            try:
                if issubclass(rule_cls, RecursiveLintRule):
                    violations_for_rule = rule_cls.check(self, screen, visited)
                else:
                    violations_for_rule = rule_cls.check(screen)
                visited[file_path].extend(
                    violations_for_rule if violations_for_rule is not None else []
                )
            except Exception as e:
                visited[file_path].append(
                    RuleViolation(
                        rule_name=rule_cls.__name__,
                        rule_code=rule_cls.rule_code,
                        rule_severity=SeverityLevel.ERROR,
                        screen=screen,
                        details=f"Error while checking rule: {e}",
                    )
                )

        # If being called from higher level function, store results to avoid re-linting

        return {file_path: visited[file_path]}

    def lint_file(
        self, file_path: Path, visited: dict[Path, list[RuleViolation]] | None = None
    ) -> dict[Path, list[RuleViolation]]:
        """Lint a single .bob file.

        Args:
            file_path (Path): The path to the .bob file to lint.
            visited (dict[Path, list[RuleViolation]]): Map of paths to violations
        Returns:
            dict[Path, list[RuleViolation]]: Map of paths to violations.
        Raises:
            ValueError: If the file does not exist or is not a .bob file.
        """

        if visited is None:
            visited = {}
        if not file_path.is_file() or file_path.suffix != ".bob":
            raise ValueError(f"File {file_path} does not exist or is not a .bob file.")

        screen = Screen(f_name=str(file_path))
        return self.lint_screen(screen, visited=visited)

    def lint_directory(self, dir_path: Path) -> dict[Path, list[RuleViolation]]:
        """Lint all .bob files in the given directory and its subdirectories.

        Args:
            dir_path (Path): The directory path to lint.
        Returns:
            dict[Path, list[RuleViolation]]: Map of paths to violations.
        """

        visited: dict[Path, list[RuleViolation]] = {}
        for file_path in dir_path.glob("**/*.bob"):
            self.lint_file(file_path, visited=visited)

        return visited

    def display_linting_report(self, results: dict[Path, list[RuleViolation]]) -> None:
        """Display a linting report based on the given linting results.

        Args:
            results (dict[Path, list[RuleViolation]]): Map of paths to violations.
        """

        n_screens = len(results)
        n_screens_with_issues = sum(1 for issues in results.values() if len(issues) > 0)
        print(
            f"PhoebusLint scanned {n_screens} screens, ",
            f"{n_screens_with_issues} with violations.\n",
        )
        if n_screens_with_issues == 0:
            print(f"{GREEN}No violations found!{RESET}\n")
            return

        print(f"{BLUE}# PhoebusLint Rule Violation Report{RESET}\n")
        violations_count: dict[str, int] = {}

        # Get count of how many times each rule was violated
        for violations in results.values():
            for violation in violations:
                violations_count[violation.rule_name] = (
                    violations_count.get(violation.rule_name, 0) + 1
                )

        for violations in results.values():
            for violation in violations:
                color = (
                    RED if violation.rule_severity >= SeverityLevel.ERROR else YELLOW
                )
                print(f"{color}{violation}{RESET}")

        print()

        for sevr in SeverityLevel:
            n_severity = sum(
                1
                for violations in results.values()
                for violation in violations
                if violation.rule_severity == sevr
            )
            if n_severity > 0:
                color = RED if sevr >= SeverityLevel.ERROR else YELLOW
                print(f"{color}Total {sevr.name.capitalize()}s: {n_severity}{RESET}")
        print()

        total_issues = sum(len(issues) for issues in results.values())
        if total_issues > 0:
            print(f"Found {total_issues} total issues.")

    def did_linting_pass(self, results: dict[Path, list[RuleViolation]]) -> bool:
        """Determine if the linting results pass based on the configured fail severity.
        Args:
            results (dict[Path, list[RuleViolation]]): Map of paths to violations.
        Returns:
            bool: True if linting passed, False otherwise.
        """

        return all(
            all(
                violation.rule_severity < self._fail_severity
                for violation in violations_by_screen
            )
            for violations_by_screen in results.values()
        )
