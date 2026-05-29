from pathlib import Path

from phoebusgen.v4 import Screen
from phoebusgen.v4.properties import OpenDisplayAction, OpenFileAction
from phoebusgen.v4.properties.behavior import (
    HasActionsRulesAndScripts,
)
from phoebusgen.v4.properties.widget import HasFile

from ..linter import LintRule, RuleViolation


def check_path_exists_relative_to_screen(screen: Screen, file_path: Path) -> bool:
    """Check if a given file path exists relative to the screen's bob file location."""
    if screen.bob_file is None:
        relative_to = Path.cwd()
    else:
        relative_to = Path(screen.bob_file).parent
    full_path = relative_to / file_path
    return full_path.is_file()


class FilePropertyPathDoesNotExist(LintRule):
    """Rule that checks if file paths in widgets and screen properties exist."""

    rule_code = "P101"
    description = "File path does not exist."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        violations = []
        for widget in screen.get_widgets_by_property_class(HasFile):
            if widget.file is not None and not widget.file.is_file():
                violations.append(
                    cls.rule_violation_factory(
                        screen,
                        widget,  # type: ignore
                        details=f"{cls.description} Path: {widget.file}",
                    )
                )

        return violations


class OpenFileActionPathDoesNotExist(LintRule):
    """Rule that checks if file paths in OpenFileAction actions exist."""

    rule_code = "P102"
    description = "OpenFileAction file path does not exist."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:

        violations = []
        for widget in screen.get_widgets_by_property_class(HasActionsRulesAndScripts):
            for action in widget.actions:
                if isinstance(action, OpenFileAction) or isinstance(
                    action, OpenDisplayAction
                ):
                    if (
                        action.file is not None
                        and not check_path_exists_relative_to_screen(
                            screen, action.file
                        )
                    ):
                        violations.append(
                            cls.rule_violation_factory(
                                screen,
                                widget,  # type: ignore
                                details=f"{cls.description} Path: {action.file}",
                            )
                        )

        return violations


class OpenDisplayActionPathIsNotABobfile(LintRule):
    """Rule that checks if file paths in OpenDisplayAction actions exist."""

    rule_code = "P103"
    description = "OpenDisplayAction file path is not a .bob file."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        violations = []
        for widget in screen.get_widgets_by_property_class(HasActionsRulesAndScripts):
            for action in widget.actions:
                if isinstance(action, OpenDisplayAction):
                    if (
                        action.file is not None
                        and not Path(action.file).suffix == ".bob"
                    ):
                        violations.append(
                            cls.rule_violation_factory(
                                screen,
                                widget,  # type: ignore
                                details=f"{cls.description} Path: {action.file}",
                            )
                        )

        return violations


class ScriptFilePathDoesNotExist(LintRule):
    """Rule that checks if script file paths in widgets exist."""

    rule_code = "P104"
    description = "Script file path does not exist."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        violations = []
        for widget in screen.get_widgets_by_property_class(HasActionsRulesAndScripts):
            for script in widget.scripts:
                if script.file is not None and not Path(script.file).is_file():
                    violations.append(
                        cls.rule_violation_factory(
                            screen,
                            widget,  # type: ignore
                            details=f"{cls.description} Path: {script.file}",
                        )
                    )

        return violations


class EmbeddedDisplayPathDoesNotExist(LintRule):
    """Rule that checks if an EmbeddedDisplay widget references a non-existent file."""

    rule_code = "P105"
    description = "EmbeddedDisplay references a non-existent file."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:

        violations = []
        for embedded_display in screen.get_widgets_by_property_class(HasFile):
            if (
                embedded_display.file is not None
                and not check_path_exists_relative_to_screen(
                    screen, embedded_display.file
                )
            ):
                violations.append(
                    cls.rule_violation_factory(
                        screen,
                        embedded_display,  # type: ignore
                        details=f"{cls.description} Path: {embedded_display.file}",
                    )
                )
        return violations


class EmbeddedDisplayPathIsNotABobfile(LintRule):
    """Rule that checks if an EmbeddedDisplay widget references a non-.bob file."""

    rule_code = "P106"
    description = "EmbeddedDisplay references a non-.bob file."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:

        violations = []
        for embedded_display in screen.get_widgets_by_property_class(HasFile):
            if (
                embedded_display.file is not None
                and not Path(embedded_display.file).suffix == ".bob"
            ):
                violations.append(
                    cls.rule_violation_factory(
                        screen,
                        embedded_display,  # type: ignore
                        details=f"{cls.description} Path: {embedded_display.file}",
                    )
                )
        return violations
