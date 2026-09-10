from pathlib import Path

from phoebusgen.v4 import Screen
from phoebusgen.v4.properties import OpenDisplayAction, OpenFileAction
from phoebusgen.v4.properties.behavior import (
    HasActionsRulesAndScripts,
)
from phoebusgen.v4.properties.widget import HasFile

from ..linter import LintRule, RuleViolation, UnsafeFixableLintRule
from ..log import logger


def check_path_exists_relative_to_screen(screen: Screen, file_path: Path) -> bool:
    """Check if a given file path exists relative to the screen's bob file location."""
    if screen.bob_file is None:
        relative_to = Path.cwd()
    else:
        relative_to = Path(screen.bob_file).parent
    full_path = relative_to / file_path
    return full_path.is_file()


def find_closest_match(
    filename: str, origin: Path, bob_file_tree: list[Path]
) -> Path | None:
    """Find the closest .bob file with the given filename relative to origin.

    If multiple files match the filename, return the one with the shortest
    relative path from the origin directory.

    Parameters
    ----------
    filename : str
        The filename to search for (e.g. "motor.bob").
    origin : Path
        The directory of the screen file that references this path.
    bob_file_tree : list[Path]
        All .bob files available in the project tree.

    Returns
    -------
    Path | None
        The relative path from origin to the closest match, or None if not found.
    """
    candidates = [p for p in bob_file_tree if p.name == filename]
    if not candidates:
        return None

    # Find the candidate with the shortest relative path from origin
    def relative_path_length(candidate: Path) -> int:
        try:
            rel = candidate.resolve().relative_to(origin.resolve())
            return len(rel.parts)
        except ValueError:
            # Not a subpath, compute via os.path.relpath
            from os.path import relpath

            rel_str = relpath(candidate.resolve(), origin.resolve())
            return len(Path(rel_str).parts)

    best = min(candidates, key=relative_path_length)
    from os.path import relpath

    return Path(relpath(best.resolve(), origin.resolve()))


class FilePropertyPathDoesNotExist(LintRule):
    """Rule that checks if file paths in widgets and screen properties exist."""

    rule_code = "P101"
    description = "File path does not exist."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        violations = []
        for widget in screen.get_widgets_by_property_class(HasFile):
            if widget.file is not None and not Path(widget.file).is_file():
                violations.append(
                    cls.rule_violation_factory(
                        screen,
                        widget,  # type: ignore
                        details=f"{cls.description} Path: {widget.file}",
                    )
                )

        return violations


class OpenFileActionPathDoesNotExist(UnsafeFixableLintRule):
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
                            screen, Path(action.file)
                        )
                    ):
                        violations.append(
                            cls.rule_violation_factory(
                                screen,
                                widget,  # type: ignore
                                details=f"{cls.description} Path: {action.file}",
                                fixable=True,
                            )
                        )

        return violations

    @classmethod
    def fix(cls, violation: RuleViolation) -> bool:
        if not cls.get_parent_linter() or not cls.get_bob_file_tree():
            return False

        screen = violation.screen
        widget = violation.widget
        origin = Path(screen.bob_file).parent if screen.bob_file else Path.cwd()

        if widget is None or not isinstance(widget, HasActionsRulesAndScripts):
            return False

        for action in widget.actions:
            if not isinstance(action, (OpenFileAction, OpenDisplayAction)):
                continue
            if action.file is None:
                continue
            if f"Path: {action.file}" not in violation.details:
                continue
            filename = Path(action.file).name
            new_path = find_closest_match(filename, origin, cls.get_bob_file_tree())
            if new_path is not None:
                logger.info(
                    f"Repointing {action.file} -> {new_path} in {screen.bob_file}"
                )
                action.file = new_path
                return True
        return False


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


class EmbeddedDisplayPathDoesNotExist(UnsafeFixableLintRule):
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
                    screen, Path(embedded_display.file)
                )
            ):
                violations.append(
                    cls.rule_violation_factory(
                        screen,
                        embedded_display,  # type: ignore
                        details=f"{cls.description} Path: {embedded_display.file}",
                        fixable=True,
                    )
                )
        return violations

    @classmethod
    def fix(cls, violation: RuleViolation) -> bool:
        if not cls.get_parent_linter() or not cls.get_bob_file_tree():
            return False

        screen = violation.screen
        widget = violation.widget
        origin = Path(screen.bob_file).parent if screen.bob_file else Path.cwd()

        if widget is None or not isinstance(widget, HasFile):
            return False

        if widget.file is None:
            return True  # File not set is not an error

        filename = Path(widget.file).name
        new_path = find_closest_match(filename, origin, cls.get_bob_file_tree())
        if new_path is not None:
            logger.info(f"Repointing {widget.file} -> {new_path} in {screen.bob_file}")
            widget.file = new_path
            return True
        return False


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
