from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from os.path import relpath
from pathlib import Path

from phoebusgen.v4 import Screen
from phoebusgen.v4.properties import (
    OpenDisplayAction,
    OpenFileAction,
    OpenWebpageAction,
)
from phoebusgen.v4.properties.behavior import HasActionsRulesAndScripts
from phoebusgen.v4.widgets import (
    EmbeddedDisplay,
    NavigationTabs,
    TemplateInstance,
    Widget,
)

from ..linter import (
    LintRule,
    RuleViolation,
    SeverityLevel,
    UnsafeFixableLintRule,
    get_all_widgets,
)
from ..log import logger

_VALID_DISPLAY_SUFFIXES = (".bob", ".opi")


# ---------------------------------------------------------------------------
# Path resolution helpers
# ---------------------------------------------------------------------------
def find_closest_bob_match(
    filename: str, origin: Path, bob_file_tree: list[Path]
) -> Path | None:
    """Find the closest .bob file with the given filename relative to origin.

    If multiple files match the filename, return the one with the shortest
    relative path from the origin directory.

    Parameters
    ----------
    filename : str
        The name of the .bob file to find.
    origin : Path
        The directory from which to resolve the relative path.
    bob_file_tree : list[Path]
        A list of all .bob files to consider.

    Returns
    -------
    Path | None
        The closest matching .bob file, or None if no match is found.
    """

    candidates = [p for p in bob_file_tree if p.name == filename]
    if not candidates:
        return None

    def relative_path_length(candidate: Path) -> int:
        rel_str = relpath(candidate.resolve(), origin.resolve())
        return len(Path(rel_str).parts)

    best = min(candidates, key=relative_path_length)
    return Path(relpath(best.resolve(), origin.resolve()))


def resolve_screen_relative(file: str | Path, screen: Screen) -> Path:
    """Resolve a possibly-relative file reference against the screen's directory.

    Parameters
    ----------
    file : str | Path
        The file path to resolve, which may be relative or absolute.
    screen : Screen
        The screen whose directory is used as the base for relative paths.

    Returns
    -------
    Path
        The resolved file path, which will be absolute if the original path
        was relative to the screen's directory.
    """

    path = Path(file)
    if not path.is_absolute() and screen.bob_file:
        path = Path(screen.bob_file).parent / path
    return path


def closest_bob_match(
    file: str | Path, screen: Screen, bob_file_tree: list[Path]
) -> Path | None:
    """Find the closest same-named .bob file to ``screen``, if one exists.

    Parameters
    ----------
    file : str | Path
        The name of the .bob file to find.
    screen : Screen
        The screen whose directory is used as the base for relative path resolution.
    bob_file_tree : list[Path]
        A list of all .bob files to consider.

    Returns
    -------
    Path | None
        The closest matching .bob file, or None if no match is found.
    """

    origin = Path(screen.bob_file).parent if screen.bob_file else Path.cwd()
    return find_closest_bob_match(Path(file).name, origin, bob_file_tree)


def _attr_file_setter(obj: object) -> Callable[[Path], None]:
    """Return a callback that repoints the ``file`` attribute of ``obj``.

    Parameters
    ----------
    obj : object
        The object whose ``file`` attribute will be repointed.

    Returns
    -------
    Callable[[Path], None]
        A callback that sets the ``file`` attribute of ``obj`` to a new path.
    """

    def setter(new_path: Path) -> None:
        setattr(obj, "file", new_path)

    return setter


def _is_unset(file: str | Path | None) -> bool:
    """True when a file reference is missing or empty."""
    return file is None or str(file).strip() in ("", ".")


def _set_file(file: str | Path | None) -> str | Path | None:
    """Return the file when it is actually set, otherwise ``None``.

    Used to narrow ``str | Path | None`` references to a concrete path inside
    the check/fix loops.
    """
    return None if _is_unset(file) else file


# ---------------------------------------------------------------------------
# Path references: a file reference plus a callback to repoint it. Rules only
# declare which references they inspect; all check/fix logic lives in the free
# functions below so it is written exactly once. Iterators yield every
# reference, including those with no file set, so a single set of checks can
# distinguish "unset", "missing", "wrong suffix" and "opi" cases.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class PathReference:
    """A single file reference within a screen and how to repoint it."""

    widget: Widget
    file: str | Path | None
    repoint: Callable[[Path], None]


def embedded_display_refs(screen: Screen) -> Iterator[PathReference]:
    """Yield all embedded display file references within a screen.

    Parameters
    ----------
    screen : Screen
        The screen to inspect for embedded display widgets.

    Yields
    ------
    PathReference
        A reference to an embedded display file within the screen.
    """

    for widget in get_all_widgets(screen):
        if isinstance(widget, EmbeddedDisplay):
            yield PathReference(widget, widget.file, _attr_file_setter(widget))


def template_instance_refs(screen: Screen) -> Iterator[PathReference]:
    """Yield all template instance file references within a screen.

    Parameters
    ----------
    screen : Screen
        The screen to inspect for template instance widgets.

    Yields
    ------
    PathReference
        A reference to a template instance file within the screen.
    """

    for widget in get_all_widgets(screen):
        if isinstance(widget, TemplateInstance):
            yield PathReference(widget, widget.file, _attr_file_setter(widget))


def open_display_action_refs(screen: Screen) -> Iterator[PathReference]:
    """Yield all open-display action file references within a screen.

    Parameters
    ----------
    screen : Screen
        The screen to inspect for open-display action widgets.

    Yields
    ------
    PathReference
        A reference to an open-display action file within the screen.
    """

    for widget in get_all_widgets(screen):
        host = widget
        if not isinstance(widget, HasActionsRulesAndScripts):
            continue
        for action in widget.actions:
            if isinstance(action, OpenDisplayAction):
                yield PathReference(host, action.file, _attr_file_setter(action))


def open_file_action_refs(screen: Screen) -> Iterator[PathReference]:
    """Yield all open-file action file references within a screen.

    Parameters
    ----------
    screen : Screen
        The screen to inspect for open-file action widgets.

    Yields
    ------
    PathReference
        A reference to an open-file action file within the screen.
    """
    for widget in get_all_widgets(screen):
        host = widget
        if not isinstance(widget, HasActionsRulesAndScripts):
            continue
        for action in widget.actions:
            if isinstance(action, OpenFileAction):
                yield PathReference(host, action.file, _attr_file_setter(action))


def navigation_tabs_refs(screen: Screen) -> Iterator[PathReference]:
    """Yield all navigation tab file references within a screen.

    Parameters
    ----------
    screen : Screen
        The screen to inspect for navigation tab widgets.

    Yields
    ------
    PathReference
        A reference to a navigation tab file within the screen.
    """

    for widget in get_all_widgets(screen):
        if not isinstance(widget, NavigationTabs):
            continue
        for tab in widget.tabs:
            yield PathReference(widget, tab.file, _attr_file_setter(tab))


def display_file_refs(screen: Screen) -> Iterator[PathReference]:
    """Yield all display file references within a screen.

    Parameters
    ----------
    screen : Screen
        The screen to inspect for display file references.

    Yields
    ------
    PathReference
        A reference to a display file within the screen.
    """
    yield from embedded_display_refs(screen)
    yield from open_display_action_refs(screen)
    yield from template_instance_refs(screen)
    yield from navigation_tabs_refs(screen)


# ---------------------------------------------------------------------------
# Generic check/fix functions shared by the thin rule classes below.
# ---------------------------------------------------------------------------
def check_missing_paths(
    rule: type[LintRule], screen: Screen, refs: Iterable[PathReference]
) -> list[RuleViolation]:
    """Flag references whose file does not exist relative to the screen.

    Parameters
    ----------
    rule : type[LintRule]
        The lint rule class that is performing the check.
    screen : Screen
        The screen to inspect for missing file references.
    refs : Iterable[PathReference]
        The file references to check for existence.

    Returns
    -------
    list[RuleViolation]
        A list of rule violations for references whose file does not exist.
    """

    violations = []
    for ref in refs:
        file = _set_file(ref.file)
        if file is None:
            continue
        path = resolve_screen_relative(file, screen)
        if not path.is_file():
            match = closest_bob_match(file, screen, rule.get_bob_file_tree())
            violations.append(
                rule.rule_violation_factory(
                    screen=screen,
                    widget=ref.widget,
                    details=f"{rule.description} Path: {file}",
                    fixable=match is not None,
                )
            )
    return violations


def fix_missing_path(
    rule: type[LintRule], violation: RuleViolation, refs: Iterable[PathReference]
) -> bool:
    """Repoint the reference named in ``violation`` to its closest .bob match.

    Parameters
    ----------
    rule : type[LintRule]
        The lint rule class that is performing the fix.
    violation : RuleViolation
        The rule violation that indicates the reference to be fixed.
    refs : Iterable[PathReference]
        The file references to search for the one to be repointed.

    Returns
    -------
    bool
        True if the reference was successfully repointed, False otherwise.
    """

    if not rule.get_bob_file_tree():
        return False

    screen = violation.screen
    for ref in refs:
        file = _set_file(ref.file)
        if file is None or f"Path: {file}" not in violation.details:
            continue
        new_path = closest_bob_match(file, screen, rule.get_bob_file_tree())
        if new_path is not None:
            logger.info(f"Repointing {ref.file} -> {new_path} in {screen.bob_file}")
            ref.repoint(new_path)
            return True
        logger.warning(
            f"No matching .bob file found for {ref.file} in {screen.bob_file}"
        )
    return False


def check_opi_paths(
    rule: type[LintRule], screen: Screen, refs: Iterable[PathReference]
) -> list[RuleViolation]:
    """Flag references that point at an OPI file rather than a .bob file.

    A violation is fixable when a same-named .bob file is found in the bob file
    tree, exactly as the missing-path rule locates replacements.

    Parameters
    ----------
    rule : type[LintRule]
        The lint rule class that is performing the check.
    screen : Screen
        The screen to inspect for OPI file references.
    refs : Iterable[PathReference]
        The file references to check for OPI files.

    Returns
    -------
    list[RuleViolation]
        A list of rule violations for references that point at an OPI
        file rather than a .bob file.
    """

    violations = []
    for ref in refs:
        file = _set_file(ref.file)
        if file is None:
            continue
        path = resolve_screen_relative(file, screen)
        if path.suffix.lower() == ".opi":
            match = closest_bob_match(
                Path(file).with_suffix(".bob"), screen, rule.get_bob_file_tree()
            )
            violations.append(
                rule.rule_violation_factory(
                    screen=screen,
                    widget=ref.widget,
                    details=f"{rule.description} Path: {file}",
                    fixable=match is not None,
                )
            )
    return violations


def fix_opi_path(
    rule: type[LintRule], violation: RuleViolation, refs: Iterable[PathReference]
) -> bool:
    """Repoint an OPI reference to a same-named .bob file found in the tree.

    Parameters
    ----------
    rule : type[LintRule]
        The lint rule class that is performing the fix.
    violation : RuleViolation
        The rule violation that indicates the reference to be fixed.
    refs : Iterable[PathReference]
        The file references to search for the one to be repointed.

    Returns
    -------
    bool
        True if the reference was successfully repointed, False otherwise.
    """

    if not rule.get_bob_file_tree():
        return False

    screen = violation.screen
    for ref in refs:
        file = _set_file(ref.file)
        if file is None or f"Path: {file}" not in violation.details:
            continue
        new_path = closest_bob_match(
            Path(file).with_suffix(".bob"), screen, rule.get_bob_file_tree()
        )
        if new_path is not None:
            logger.info(f"Repointing {ref.file} -> {new_path} in {screen.bob_file}")
            ref.repoint(new_path)
            return True
        logger.warning(
            f"No matching .bob file found for {ref.file} in {screen.bob_file}"
        )
    return False


def check_non_display_paths(
    rule: type[LintRule], screen: Screen, refs: Iterable[PathReference]
) -> list[RuleViolation]:
    """Flag references whose file is neither a .bob nor a .opi file.

    Parameters
    ----------
    rule : type[LintRule]
        The lint rule class that is performing the check.
    screen : Screen
        The screen to inspect for non-display file references.
    refs : Iterable[PathReference]
        The file references to check for non-display paths.

    Returns
    -------
    list[RuleViolation]
        A list of rule violations for references with non-display paths.
    """

    violations = []
    for ref in refs:
        file = _set_file(ref.file)
        if file is None:
            continue
        if Path(file).suffix.lower() not in _VALID_DISPLAY_SUFFIXES:
            violations.append(
                rule.rule_violation_factory(
                    screen=screen,
                    widget=ref.widget,
                    details=f"{rule.description} Path: {file}",
                )
            )
    return violations


def check_unset_paths(
    rule: type[LintRule], screen: Screen, refs: Iterable[PathReference]
) -> list[RuleViolation]:
    """Flag references that have no file path set.

    Parameters
    ----------
    rule : type[LintRule]
        The lint rule class that is performing the check.
    screen : Screen
        The screen to inspect for unset file references.
    refs : Iterable[PathReference]
        The file references to check for unset paths.

    Returns
    -------
    list[RuleViolation]
        A list of rule violations for references with unset paths.
    """

    return [
        rule.rule_violation_factory(screen=screen, widget=ref.widget)
        for ref in refs
        if _is_unset(ref.file)
    ]


# ---------------------------------------------------------------------------
# Unified display-file rules: applied to every widget/action that references a
# bob/opi display file (embedded displays, open-display actions, template
# instances and navigation tabs).
# ---------------------------------------------------------------------------
class DisplayFilePathNotSet(LintRule):
    """Checks for display-file references that have no file path set."""

    rule_code = "P101"
    rule_severity = SeverityLevel.ERROR
    description = "Display file reference has no file path set."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        return check_unset_paths(cls, screen, display_file_refs(screen))


class DisplayFilePathDoesNotExist(UnsafeFixableLintRule):
    """Checks for display-file references whose path does not exist."""

    rule_code = "P102"
    rule_severity = SeverityLevel.ERROR
    description = "Display file reference has a path that does not exist."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        return check_missing_paths(cls, screen, display_file_refs(screen))

    @classmethod
    def fix(cls, violation: RuleViolation) -> bool:
        return fix_missing_path(cls, violation, display_file_refs(violation.screen))


class DisplayFilePathNotBobOrOpiFile(LintRule):
    """Checks that a display-file reference points to a bob or opi file."""

    rule_code = "P103"
    rule_severity = SeverityLevel.WARNING
    description = "Display file reference is neither a bob nor an opi file."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        return check_non_display_paths(cls, screen, display_file_refs(screen))


class DisplayFileIsOpiFile(UnsafeFixableLintRule):
    """Checks for display-file references that point to an OPI file."""

    rule_code = "P104"
    rule_severity = SeverityLevel.WARNING
    description = "Display file reference points to an OPI file, not a bob file."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        return check_opi_paths(cls, screen, display_file_refs(screen))

    @classmethod
    def fix(cls, violation: RuleViolation) -> bool:
        return fix_opi_path(cls, violation, display_file_refs(violation.screen))


# ---------------------------------------------------------------------------
# OpenFileAction rules
# ---------------------------------------------------------------------------
class OpenFileActionPathDoesNotExist(UnsafeFixableLintRule):
    """Rule that checks if an OpenFileAction has a path that does not exist."""

    rule_code = "P105"
    description = "OpenFileAction has a path that does not exist."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        return check_missing_paths(cls, screen, open_file_action_refs(screen))

    @classmethod
    def fix(cls, violation: RuleViolation) -> bool:
        return fix_missing_path(cls, violation, open_file_action_refs(violation.screen))


# ---------------------------------------------------------------------------
# OpenWebpageAction rules
# ---------------------------------------------------------------------------
class OpenWebpageActionInvalidUrl(LintRule):
    """Rule that checks if an OpenWebpageAction has an invalid URL."""

    rule_code = "P106"
    description = "OpenWebpageAction has an invalid URL."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        violations = []
        for widget in get_all_widgets(screen):
            host = widget
            if not isinstance(widget, HasActionsRulesAndScripts):
                continue
            for action in widget.actions:
                if isinstance(action, OpenWebpageAction) and not action.url.startswith(
                    ("http://", "https://")
                ):
                    violations.append(
                        cls.rule_violation_factory(
                            screen=screen,
                            widget=host,
                            details=f"{cls.description} URL: {action.url}",
                        )
                    )
        return violations


# ---------------------------------------------------------------------------
# Script rules
# ---------------------------------------------------------------------------
class ScriptFilePathDoesNotExist(LintRule):
    """Rule that checks if script file paths in widgets exist."""

    rule_code = "P107"
    description = "Script file path does not exist."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        violations = []
        for widget in get_all_widgets(screen):
            host = widget
            if not isinstance(widget, HasActionsRulesAndScripts):
                continue
            for script in widget.scripts:
                if (
                    script.file is not None
                    and not resolve_screen_relative(script.file, screen).is_file()
                ):
                    violations.append(
                        cls.rule_violation_factory(
                            screen=screen,
                            widget=host,
                            details=f"{cls.description} Path: {script.file}",
                        )
                    )
        return violations
