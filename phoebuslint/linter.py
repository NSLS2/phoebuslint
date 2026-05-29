import inspect
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import IntEnum
from itertools import chain
from pathlib import Path

import yaml
from phoebusgen.v4 import Screen
from phoebusgen.v4.widgets import Widget
import logging
import sys

from .log import logger, BLUE, GREEN, YELLOW, RED, RESET


class SeverityLevel(IntEnum):
    """Enum representing severity levels for rule violations."""

    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4


@dataclass
class RuleViolation:
    """Dataclass representing a rule violation found during linting.

    Attributes
    ----------
    rule_name : str
        The name of the rule that was violated.
    rule_code : str
        The code of the rule that was violated.
    rule_severity : SeverityLevel
        The severity level of the rule violation.
    screen : Screen | Path
        The screen where the violation was found.
    widget : optional, Widget
        The widget where the violation was found.
    property : optional, str
        The property name where the violation was found.
    property_element : optional, str
        The property element where the violation was found.
    details : str, default = ""
        Additional details about the violation.
    """

    rule_name: str
    rule_code: str
    rule_severity: SeverityLevel
    screen: Screen | Path
    widget: Widget | None = None
    property: str | None = None
    property_element: str | None = None
    details: str = ""

    def __str__(self) -> str:
        screen_path = (
            self.screen.bob_file if isinstance(self.screen, Screen) else self.screen
        )
        location = f"Screen: {screen_path}"
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


class LintRule(RuleViolationFactory, ABC):
    """Abstract base class for stateless linting rules."""

    @classmethod
    @abstractmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        """Check the given screen for issues covered by this rule.

        Parameters
        ----------
        screen : Screen
            The reference to the phoebusgen screen object being checked for the rule.

        Returns
        -------
        list[RuleViolation]
            List of issues found, or empty list if none found.
        """
        ...


class RecursiveLintRule(RuleViolationFactory, ABC):
    """ABC for linting rules that require recursive linting of linked screens."""

    @classmethod
    @abstractmethod
    def check(
        cls,
        screen: Screen,
        visited: set[Path] | None = None,
    ) -> dict[Path, list[RuleViolation]]:
        """Recursively check the given screen for issues covered by this rule.

        Parameters
        ----------
        screen : Screen
            The screen to be checked.
        visited : optional, set[Path]
            Set of visited paths to avoid infinite recursion.

        Returns
        -------
        dict[Path, list[RuleViolation]]
            Map of paths to violations found.
        """
        ...


class FixableLintRule(LintRule, ABC):
    """Abstract base class for linting rules that can be automatically fixed."""

    @classmethod
    @abstractmethod
    def fix(cls, screen: Screen) -> bool:
        """Attempt to fix the issue covered by this rule on the given screen.

        Args:
            screen (Screen): The screen to attempt to fix.
        Returns:
            bool: True if a fix was applied, False otherwise.
        """
        ...


class FixableRecursiveLintRule(RecursiveLintRule, ABC):
    """Abstract base class for recursive linting rules that can be fixed."""

    @classmethod
    @abstractmethod
    def fix(
        cls, linter: "PhoebusLinter", screen: Screen, visited_screens: dict[Path, bool]
    ) -> bool:
        """Attempt to fix the issue on the screen, potentially requiring recursion.

        Args:
            linter (PhoebusLinter): Linter instance. Used in recursive fixes.
            screen (Screen): The screen to attempt to fix.
            visited_screens (dict[Path, bool]): Visited screens dict to avoid repeats.
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
        enable_fixes: bool = False,
        ignore_paths: list[str] | None = None,
    ):
        self._enabled_rules = {
            rule
            for rule in (LintRule.__subclasses__() + RecursiveLintRule.__subclasses__())
            if not inspect.isabstract(rule)
            and rule.rule_code not in (disabled_rule_codes or [])
        }
        logger.debug(
            f"Disabled rules: {disabled_rule_codes}"
        )
        logger.debug(f"Fail severity: {fail_severity.name}")
        logger.debug(f"Enable automatic fixes: {enable_fixes}")
        logger.debug(f"Ignore paths: {ignore_paths}")

        self._fail_severity = fail_severity
        self._enable_auto_fixes = enable_fixes
        self._ignore_paths = ignore_paths or []

    def lint_screen(
        self, screen: Screen, visited: dict[Path, list[RuleViolation]] | None = None
    ) -> dict[Path, list[RuleViolation]]:
        """Lint a single Phoebus screen.

        Parameters
        ----------
        screen : Screen
            The Phoebus screen to lint.
        visited : dict[Path, list[RuleViolation]], optional
            A dictionary mapping file paths to lists of rule violations.
            Used to track which files have already been linted and their
            violations to avoid redundant work. If None, a new empty dictionary
            will be created and used.

        Returns
        -------
        dict[Path, list[RuleViolation]]
            A dict mapping file paths to lists of violations found in those screens.

        Raises
        ------
        ValueError
            If the screen is not associated with a file path.
        """

        if screen.bob_file is None:
            raise ValueError("Screen must be associated with a file path to be linted.")
        
        if any(str(screen.bob_file).startswith(path) for path in self._ignore_paths):
            logger.debug(f"Skipping ignored screen: {screen.bob_file}")
            return {}

        logger.info(f"Linting screen: {screen.bob_file}")

        if visited is None:
            visited = {}

        file_path = Path(screen.bob_file)

        if file_path in visited:
            return {file_path: visited[file_path]}

        visited[file_path] = []
        for rule_cls in self._enabled_rules:
            logger.debug(f"Checking rule: {rule_cls.__name__}")
            try:
                if issubclass(rule_cls, RecursiveLintRule):
                    violations_by_path = rule_cls.check(screen)
                    for visited_file_path in violations_by_path:
                        visited[visited_file_path].extend(
                            violations_by_path.get(visited_file_path, [])
                        )
                else:
                    visited[file_path].extend(rule_cls.check(screen))
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

        Parameters
        ----------
        file_path : Path
            The path to the .bob file to lint.
        visited : dict[Path, list[RuleViolation]], optional
            A dictionary mapping file paths to lists of rule violations.
            Used to track which files have already been linted and their
            violations to avoid redundant work. If None, a new empty dictionary
            will be created and used.

        Returns
        -------
        dict[Path, list[RuleViolation]]
            A dict mapping file paths to lists of violations found in those files.

        Raises
        ------
        ValueError
            If the file does not exist or is not a .bob file.
        """

        if visited is None:
            visited = {}
        if not file_path.is_file() or file_path.suffix != ".bob":
            raise ValueError(f"File {file_path} does not exist or is not a .bob file.")

        try:
            screen = Screen(f_name=str(file_path))
        except Exception as e:
            return {
                file_path: [
                    RuleViolation(
                        rule_name="ScreenNotParsable",
                        rule_code="S101",
                        rule_severity=SeverityLevel.ERROR,
                        screen=file_path,
                        details=f"Error parsing .bob file: {e}",
                    )
                ]
            }
        return self.lint_screen(screen, visited=visited)

    def lint_directory(self, dir_path: Path) -> dict[Path, list[RuleViolation]]:
        """Lint all .bob files in the given directory and its subdirectories.

        Args:
            dir_path (Path): The directory path to lint.
        Returns:
            dict[Path, list[RuleViolation]]: Map of paths to violations.
        """

        visited: dict[Path, list[RuleViolation]] = {}
        for file_path in chain(dir_path.glob("*.bob"), dir_path.glob("**/*.bob")):
            self.lint_file(file_path, visited=visited)

        return visited

    def display_linting_report(self, results: dict[Path, list[RuleViolation]]) -> None:
        """Display a linting report based on the given linting results.

        Parameters
        ----------
        results : dict[Path, list[RuleViolation]]
            Map of paths to violations.
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

        Parameters
        ----------
        results : dict[Path, list[RuleViolation]]
            Map of paths to violations.

        Returns
        -------
        bool
            True if linting passed, False otherwise.
        """

        return all(
            all(
                violation.rule_severity < self._fail_severity
                for violation in violations_by_screen
            )
            for violations_by_screen in results.values()
        )
