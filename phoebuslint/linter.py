import inspect
from abc import ABC, abstractmethod
from dataclasses import dataclass
<<<<<<< Updated upstream
from enum import IntEnum
=======
from enum import Enum
from itertools import chain
>>>>>>> Stashed changes
from pathlib import Path
import graphlib

import yaml
from phoebusgen.v4 import Screen
from phoebusgen.v4.widgets import Widget

# Define color codes as constants for readability
RED = "\033[31m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
BLUE = "\033[34m"
RESET = "\033[0m"  # Resets the color to default


class SeverityLevel(IntEnum):
    """Enum representing severity levels for rule violations."""

    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4


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
        """Check the given  element for issue covered by specific rule.

        Args:
            element (PhoebusElementT): The phoebus element to be checked.
        Returns:
            list[RuleViolation]: List of issues found, or None.
        """
        ...

# class FixableLintRule(LintRule, ABC):
#     """ABC for linting rules that can also provide fixes for the issues they find."""

#     @classmethod
#     @abstractmethod
#     def fix(cls, screen: Screen) -> None:
#         """Apply a fix for the given rule violation.

#         Args:
#             screen (Screen): The screen to be fixed.
#         """
#         ...


class RecursiveLintRule(RuleViolationFactory, ABC):
    """ABC for linting rules that require recursive linting of linked screens."""

    @classmethod
    @abstractmethod
    def check(
        cls,
        screen: Screen,
        visited: set[Path] = set(),
    ) -> dict[Path, list[RuleViolation]]:
        """Recursively check the given screen for issues covered by this rule.

        Args:
            screen (Screen): The screen to be checked.
            visited (set[Path]): Set of visited paths to avoid infinite recursion.
        Returns:
            dict[Path, list[RuleViolation]]: Map of paths to violations found.
        """
        ...


<<<<<<< Updated upstream
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
=======
@dataclass(frozen=True)
class NavigationStep:
    from_screen: Path
    to_screen: Path
    macros: tuple[tuple[str, str], ...]  # Macros to apply when navigating, as sorted tuple of key-value pairs

    def __eq__(self, other):
        if not isinstance(other, NavigationStep):
            return NotImplemented
        return (
            self.from_screen == other.from_screen
            and self.to_screen == other.to_screen
        )
    
    @property
    def macros_dict(self) -> dict[str, str]:
        """Convert macros tuple back to a dictionary."""
        return dict(self.macros)


class ScreenNavigationDAG:
    """Class representing the navigation structure of screens as a directed acyclic graph (DAG).
    
    Each node represents a screen, and edges represent navigation actions (e.g., opening another screen)
    with optional macros passed during navigation.
    """

    def __init__(self):
        self.graph: dict[Path, set[NavigationStep]] = {}

    def add_navigation(self, from_screen: Path, to_screen: Path, macros: dict[str, str] | None = None) -> None:
        """Add a navigation link between two screens in the graph.

        Args:
            from_screen (Path): The screen where the navigation starts.
            to_screen (Path): The screen where the navigation ends.
            macros (dict[str, str] | None): Macros passed when navigating to the destination screen.
        """
        if from_screen not in self.graph:
            self.graph[from_screen] = set()
        if macros is None:
            macros = {}
        # Convert macros dict to sorted tuple of tuples for hashability
        macros_tuple = tuple(sorted(macros.items()))
        self.graph[from_screen].add(NavigationStep(from_screen=from_screen, to_screen=to_screen, macros=macros_tuple))

    def get_all_nodes(self) -> set[Path]:
        """Get all unique screens (nodes) in the graph.

        Returns:
            set[Path]: All screens that appear in the navigation graph.
        """
        all_nodes = set(self.graph.keys())
        for navigation_steps in self.graph.values():
            for step in navigation_steps:
                all_nodes.add(step.to_screen)
        return all_nodes

    def get_destination_nodes(self) -> set[Path]:
        """Get all screens that are opened by at least one other screen.

        Returns:
            set[Path]: All screens that appear as destinations in navigation actions.
        """
        destination_nodes = set()
        for navigation_steps in self.graph.values():
            for step in navigation_steps:
                destination_nodes.add(step.to_screen)
        return destination_nodes

    def get_root_nodes(self) -> set[Path]:
        """Get root nodes - screens that open other screens but are not opened by anything.

        Root nodes are entry points in the navigation graph. They have outgoing edges 
        but no incoming edges.

        Returns:
            set[Path]: Set of screens that are root nodes in the navigation graph.
        """
        destination_nodes = self.get_destination_nodes()
        root_nodes = set()
        for from_screen in self.graph.keys():
            if from_screen not in destination_nodes:
                root_nodes.add(from_screen)
        return root_nodes

    def get_leaf_nodes(self) -> set[Path]:
        """Get leaf nodes - screens that don't open any other screens.

        Leaf nodes are terminal screens in the navigation graph. They have incoming 
        edges but no outgoing edges.

        Returns:
            set[Path]: Set of screens that are leaf nodes in the navigation graph.
        """
        all_nodes = self.get_all_nodes()
        leaf_nodes = set()
        for node in all_nodes:
            if node not in self.graph or len(self.graph[node]) == 0:
                leaf_nodes.add(node)
        return leaf_nodes


    @classmethod
    def from_screen(cls, screen: Screen) -> "ScreenNavigationDAG":
        """Construct a ScreenNavigationDAG from a given screen by analyzing its linked screens.

        Args:
            screen (Screen): The screen to analyze for navigation links.
        Returns:
            ScreenNavigationDAG: The constructed navigation graph for the given screen.
        """
        dag = cls()
        visited: set[Path] = set()

        def dfs(current_screen: Screen):
            if current_screen.bob_file is None:
                return
            current_path = Path(current_screen.bob_file)
            visited.add(current_path)

            for to_screen_path, macros in current_screen.get_linked_screens().items():
                dag.add_navigation(current_path, to_screen_path, macros)
                if to_screen_path not in visited:
                    try:
                        to_screen = Screen(f_name=str(to_screen_path))
                        dfs(to_screen)
                    except Exception as e:
                        # If we can't load the linked screen, we can choose to log this or ignore it
                        print(f"Warning: Could not load linked screen at {to_screen_path}: {e}")

        dfs(screen)
        return dag


    @classmethod
    def from_directory(cls, dir_path: Path) -> "ScreenNavigationDAG":
        """Construct a ScreenNavigationDAG from all .bob files in the given directory.

        Args:
            dir_path (Path): The directory to scan for .bob files and analyze for navigation links.
        Returns:
            ScreenNavigationDAG: The constructed navigation graph for all screens in the directory.
        """
        dag = cls()
        # Search both the directory itself and all subdirectories
        for bob_file in dir_path.glob("**/*.bob"):
            print(bob_file)
            try:
                screen = Screen(f_name=str(bob_file))
                screen_dag = cls.from_screen(screen)
                print(screen_dag.graph)
                exit()
                for from_screen, navigation_steps in screen_dag.graph.items():
                    for step in navigation_steps:
                        dag.add_navigation(from_screen, step.to_screen, step.macros_dict)
            except Exception as e:
                print(f"Warning: Could not load screen at {bob_file}: {e}")
        return dag
>>>>>>> Stashed changes


class PhoebusLinter:
    """Class containing main linting logic for Phoebus screens."""

    def __init__(
        self,
        fail_severity: SeverityLevel = SeverityLevel.WARNING,
<<<<<<< Updated upstream
        disable_rules: list[str] = [],
=======
        disabled_rule_codes: list[str] | None = None,
        enable_fixes: bool = False,
>>>>>>> Stashed changes
    ):
        self._enabled_rules = {
            rule
            for rule in (LintRule.__subclasses__() + RecursiveLintRule.__subclasses__())
            if not inspect.isabstract(rule)
            and rule.rule_code not in disable_rules
        }

        self._fail_severity = fail_severity
        self._enable_auto_fixes = enable_fixes

    @classmethod
    def from_yaml(cls, config_path: Path | str) -> "PhoebusLinter":
        with open(config_path, "r") as f:
            data = yaml.safe_load(f)
        disable_rules = data.get("disable_rules", [])
        fail_severity = SeverityLevel[data.get("fail_severity", "warning").upper()]
<<<<<<< Updated upstream
        return cls(fail_severity=fail_severity, disable_rules=disable_rules)
=======
        enable_fixes = data.get("enable_fixes", False)
        return cls(fail_severity=fail_severity, disabled_rule_codes=disabled_rule_codes, enable_fixes=enable_fixes)
>>>>>>> Stashed changes

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
                    violations_by_path = rule_cls.check(screen)
                    for visited_file_path in violations_by_path:
                        visited[visited_file_path].extend(violations_by_path.get(visited_file_path, []))
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


        screen_nav_dag = ScreenNavigationDAG.from_directory(dir_path)
        print(screen_nav_dag.get_root_nodes())

        visited: dict[Path, list[RuleViolation]] = {}
        for file_path in chain(dir_path.glob("*.bob"), dir_path.glob("**/*.bob")):
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
