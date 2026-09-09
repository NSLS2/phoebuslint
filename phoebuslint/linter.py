import inspect
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import IntEnum
from itertools import chain
from pathlib import Path

from phoebusgen.v4 import Screen
from phoebusgen.v4.widgets import HasWidgets, Tabs, Widget

from .log import BLUE, GREEN, RED, RESET, YELLOW, logger


def get_all_widgets(container: HasWidgets) -> list[Widget]:
    """Recursively collect all widgets from a container, including nested ones."""
    widgets: list[Widget] = []
    for widget in container.get_widgets():
        widgets.append(widget)
        if isinstance(widget, HasWidgets):
            widgets.extend(get_all_widgets(widget))
        elif isinstance(widget, Tabs):
            for tab in widget.tabs:
                widgets.extend(get_all_widgets(tab))
    return widgets


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
    fixable : bool, default = False
        Whether this violation can be automatically fixed.
    """

    rule_name: str
    rule_code: str
    rule_severity: SeverityLevel
    screen: Screen
    widget: Widget | None = None
    property: str | None = None
    property_element: str | None = None
    details: str = ""
    fixable: bool = False

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
        fixable: bool = False,
    ) -> RuleViolation:
        """Factory method to create a RuleViolation instance for this rule.

        Args:
            screen (Screen): The screen where the violation was found.
            widget (Widget | None): The widget where the violation was found.
            property (str | None): Property name where the violation was found.
            property_element (str | None): Property elem where the violation was found.
            details (str | None): Additional details about the violation.
            fixable (bool): Whether this violation can be automatically fixed.
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
            fixable=fixable,
        )


class LintRule(RuleViolationFactory, ABC):
    """Abstract base class for stateless linting rules."""

    _linter: "PhoebusLinter | None" = None

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


class FixableLintRule(LintRule, ABC):
    """Abstract base class for linting rules that can be automatically fixed."""

    @classmethod
    @abstractmethod
    def fix(cls, violation: RuleViolation) -> bool:
        """Attempt to fix a single violation.

        The violation already contains references to the screen and widget.
        Access cls._linter for the parent linter instance (e.g. bob_file_tree).

        Parameters
        ----------
        violation : RuleViolation
            The violation to fix.

        Returns
        -------
        bool
            True if the violation was fixed, False otherwise.
        """
        ...


class UnsafeFixableLintRule(FixableLintRule, ABC):
    """Abstract base class for fixable rules whose fixes may introduce breaking changes.

    Unsafe fixes require the --unsafe-fixes flag to be applied.
    """

    ...


def get_all_rules() -> list[type[LintRule]]:
    basic_rules = [
        rule for rule in LintRule.__subclasses__() if not inspect.isabstract(rule)
    ]
    fixable_rules = [
        rule
        for rule in FixableLintRule.__subclasses__()
        if not inspect.isabstract(rule)
    ]
    unsafe_fixable_rules = [
        rule
        for rule in UnsafeFixableLintRule.__subclasses__()
        if not inspect.isabstract(rule)
    ]
    return basic_rules + fixable_rules + unsafe_fixable_rules


def get_all_rule_codes() -> list[str]:
    """Get all rule codes from registered LintRule subclasses."""
    return [rule.rule_code for rule in get_all_rules()]


class PhoebusLinter:
    """Class containing main linting logic for Phoebus screens."""

    def __init__(
        self,
        fail_severity: SeverityLevel = SeverityLevel.WARNING,
        disabled_rule_codes: list[str] | None = None,
        enable_fixes: bool = False,
        enable_unsafe_fixes: bool = False,
        ignore_paths: list[str] | None = None,
        show_counts: bool = False,
    ):
        self._enabled_rules = {
            rule
            for rule in get_all_rules()
            if rule.rule_code not in (disabled_rule_codes or [])
        }
        logger.debug(f"Disabled rules: {disabled_rule_codes}")
        logger.debug(f"Fail severity: {fail_severity.name}")
        logger.debug(f"Enable automatic fixes: {enable_fixes}")
        logger.debug(f"Enable unsafe fixes: {enable_unsafe_fixes}")
        logger.debug(f"Ignore paths: {ignore_paths}")
        logger.debug(f"Show counts: {show_counts}")

        self._fail_severity = fail_severity
        self._enable_auto_fixes = enable_fixes
        self._enable_unsafe_fixes = enable_unsafe_fixes
        self._ignore_paths = ignore_paths or []
        self._show_counts = show_counts
        self._bob_file_tree: list[Path] = []
        LintRule._linter = self

    def build_bob_file_tree(self, root: Path) -> None:
        """Build a list of all .bob files available from the given root directory down.

        Parameters
        ----------
        root : Path
            The root directory to search for .bob files.
        """
        self._bob_file_tree = sorted(root.rglob("*.bob"))

    def lint_screen(
        self,
        screen: Screen,
        visited: dict[Path, list[RuleViolation]] | None = None,
        num_fixable: int = 0,
    ) -> tuple[dict[Path, list[RuleViolation]], int]:
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
        int
            The number of fixable violations found.

        Raises
        ------
        ValueError
            If the screen is not associated with a file path.
        """

        if screen.bob_file is None:
            raise ValueError("Screen must be associated with a file path to be linted.")

        if any(str(screen.bob_file).startswith(path) for path in self._ignore_paths):
            logger.debug(f"Skipping ignored screen: {screen.bob_file}")
            return {}, num_fixable

        if visited is None:
            visited = {}

        file_path = Path(screen.bob_file).resolve()

        if file_path in visited:
            logger.debug(f"Skipping already-visited screen: {file_path}")
            return visited, num_fixable

        logger.info(f"Linting screen: {screen.bob_file}")

        visited[file_path] = []
        for rule_cls in self._enabled_rules:
            logger.debug(f"Checking rule: {rule_cls.__name__}")
            try:
                violations = rule_cls.check(screen)
            except Exception as e:
                violations = [
                    RuleViolation(
                        rule_name=rule_cls.__name__,
                        rule_code=rule_cls.rule_code,
                        rule_severity=SeverityLevel.ERROR,
                        screen=screen,
                        details=f"Error while checking rule: {e}",
                    )
                ]
            if violations:
                should_fix = (
                    issubclass(rule_cls, FixableLintRule)
                    and self._enable_auto_fixes
                    and (
                        not issubclass(rule_cls, UnsafeFixableLintRule)
                        or self._enable_unsafe_fixes
                    )
                )
                if should_fix:
                    screen_deleted = False
                    for violation in violations:
                        if not violation.fixable:
                            visited[file_path].append(violation)
                            continue
                        logger.info(f"Fixing violation: {violation}")
                        fixed = rule_cls.fix(violation)  # type: ignore
                        if not fixed:
                            visited[file_path].append(violation)
                        # In some cases, a screen will just be deleted by the fix.
                        if not os.path.exists(screen.bob_file):
                            screen_deleted = True
                            break
                    if screen_deleted:
                        break
                    screen.write_screen()
                else:
                    num_fixable += sum(1 for v in violations if v.fixable)
                    visited[file_path].extend(violations)

        for screen_transition in screen.get_linked_screens():
            target_path = (file_path.parent / screen_transition.target).resolve()
            try:
                visited, num_fixable = self.lint_file(
                    target_path, visited=visited, num_fixable=num_fixable
                )
            except FileNotFoundError as e:
                logger.debug(
                    f"Cannot lint linked screen {screen_transition.target}: {e}"
                )

        # If being called from higher level function, store results to avoid re-linting

        return visited, num_fixable

    def lint_file(
        self,
        file_path: Path,
        visited: dict[Path, list[RuleViolation]] | None = None,
        num_fixable: int = 0,
    ) -> tuple[dict[Path, list[RuleViolation]], int]:
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
        FileNotFoundError
            If the file does not exist or is not a .bob file.
        """

        if visited is None:
            visited = {}

        file_path = file_path.resolve()

        if file_path in visited:
            logger.debug(f"Skipping already-visited file: {file_path}")
            return visited, num_fixable

        if not file_path.is_file() or file_path.suffix != ".bob":
            raise FileNotFoundError(
                f"File {file_path} does not exist or is not a .bob file."
            )

        screen = Screen(f_name=str(file_path))
        try:
            # If a screen has widgets that are not valid phoebus XML this will raise.
            screen.get_all_widgets()
        except Exception as e:
            logger.error(f"{file_path} is not a valid phoebus .bob xml file!")
            visited[file_path] = [
                RuleViolation(
                    rule_name="ScreenNotParsable",
                    rule_code="S101",
                    rule_severity=SeverityLevel.ERROR,
                    screen=screen,
                    details=f"Error parsing .bob file: {e}",
                )
            ]
            return visited, num_fixable
        return self.lint_screen(screen, visited=visited, num_fixable=num_fixable)

    def lint_directory(
        self, dir_path: Path
    ) -> tuple[dict[Path, list[RuleViolation]], int]:
        """Lint all .bob files in the given directory and its subdirectories.

        Args:
            dir_path (Path): The directory path to lint.
        Returns:
            dict[Path, list[RuleViolation]]: Map of paths to violations.
        """
        num_fixable = 0
        visited: dict[Path, list[RuleViolation]] = {}
        for file_path in chain(dir_path.glob("*.bob"), dir_path.glob("**/*.bob")):
            visited, num_fixable = self.lint_file(
                file_path, visited=visited, num_fixable=num_fixable
            )
        return visited, num_fixable

    def display_rules(self) -> None:
        """Print all enabled rules and their descriptions."""
        enabled = sorted(self._enabled_rules, key=lambda rule: rule.rule_code)
        print(f"{BLUE}# PhoebusLint Rules ({len(enabled)} enabled){RESET}\n")
        for rule in enabled:
            color = RED if rule.rule_severity >= SeverityLevel.ERROR else YELLOW
            if issubclass(rule, UnsafeFixableLintRule):
                fixable = "fixable (unsafe)"
            elif issubclass(rule, FixableLintRule):
                fixable = "fixable"
            else:
                fixable = "not fixable"
            print(
                f"  {color}{rule.rule_code}{RESET} "
                f"[{rule.rule_severity.name}] [{fixable}] {rule.description}"
            )
        print()

    def display_linting_report(
        self, results: dict[Path, list[RuleViolation]], num_fixable: int
    ) -> None:
        """Display a linting report based on the given linting results.

        Parameters
        ----------
        results : dict[Path, list[RuleViolation]]
            Map of paths to violations.
        num_fixable : int
            The number of fixable issues.
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
                violations_count[violation.rule_name + f" [{violation.rule_code}]"] = (
                    violations_count.get(violation.rule_name + f" [{violation.rule_code}]", 0) + 1
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

        if self._show_counts:
            print()
            for rule_name, count in violations_count.items():
                print(f"  {rule_name}: {count}")
            print()

        if num_fixable > 0:
            print(
                f"{num_fixable} issue{'s are' if num_fixable > 1 else ' is'} fixable. Re-run with --fix to automatically apply fixes."  # noqa: E501
            )

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
