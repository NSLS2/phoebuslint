from .config import PhoebusLintConfig
from phoebusgen import Screen
from phoebusgen.widgets import Widget
from pathlib import Path
from .rules import LintRule
from dataclasses import dataclass
from .utils import SeverityLevel


# Define color codes as constants for readability
RED = '\033[31m'
YELLOW = '\033[33m'
GREEN = '\033[32m'
BLUE = '\033[34m'
RESET = '\033[0m' # Resets the color to default


class PhoebusLinter:

    def __init__(self, config: PhoebusLintConfig):
        self._config = config
        self._all_rules = self._config.rules

    def lint_screen(self, screen: Screen, visited_screens: dict[Path, list[str]] = {}, display_report: bool = False) -> bool:

        if screen.bob_file is None:
            raise ValueError("Screen must be associated with a file path to be linted.")

        if Path(screen.bob_file) in visited_screens:
            return len(visited_screens[Path(screen.bob_file)]) == 0

        issues: list[str] = []
        for rule_cls in self._all_rules:
            violations_found = rule_cls.check(screen)
            if violations_found:
                issues.extend(violations_found)

        # If being called from higher level function, store results to avoid re-linting
        visited_screens[Path(screen.bob_file)] = issues

        lint_ok = len([issue for issue in issues if issue.rule_cls.rule_severity >= self._config._fail_severity.value]) == 0
        if not lint_ok and display_report:
            self.display_linting_report({Path(screen.bob_file): issues})
        return lint_ok


    def lint_file(self, file_path: Path, visited_screens: dict[Path, list[RuleViolation]] = {}, display_results: bool = False) -> bool:
        screen = Screen(f_name=str(file_path))
        return self.lint_screen(screen, visited_screens=visited_screens, display_report=display_results)


    def lint_directory(self, dir_path: Path, display_results: bool = True) -> bool:
        visited_screens: dict[Path, list[RuleViolation]] = {}
        lint_ok = all(
            self.lint_file(file_path, visited_screens=visited_screens)
            for file_path in dir_path.glob("**/*.bob")
        )
        if display_results:
            self.display_linting_report(visited_screens)
        return lint_ok


    def display_linting_report(self, linting_results: dict[Path, list[RuleViolation]]) -> None:

        n_screens = len(linting_results)
        n_screens_with_issues = sum(1 for issues in linting_results.values() if len(issues) > 0)
        print(f"PhoebusLint scanned {n_screens} screens, {n_screens_with_issues} with rule violations.\n")
        if n_screens_with_issues == 0:
            print(f"{GREEN}No violations found!{RESET}\n")
            return

        print(f"{BLUE}# PhoebusLint Rule Violation Report{RESET}\n")
        violations_count: dict[type['LintRule'], int] = {}

        # Get count of how many times each rule was violated
        for violations in linting_results.values():
            for violation in violations:
                violations_count[violation.rule_cls] = violations_count.get(violation.rule_cls, 0) + 1
        
        for rule_cls, count in violations_count.items():
            color = RED if rule_cls.rule_severity == SeverityLevel.ERROR else YELLOW
            print(f"  {color}{count} [{rule_cls.rule_code}]: {rule_cls.description}{RESET}")

        print()

        n_errors = sum(
            1 for violations in linting_results.values()
            for violation in violations
            if violation.rule_cls.rule_severity == SeverityLevel.ERROR
        )
        n_warnings = sum(
            1 for violations in linting_results.values()
            for violation in violations
            if violation.rule_cls.rule_severity == SeverityLevel.WARNING
        )


                    


        total_issues = sum(len(issues) for issues in linting_results.values())
        if total_issues > 0:
            print(f"Found {total_issues} total issues.")


        