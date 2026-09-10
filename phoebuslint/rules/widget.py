from pathlib import Path

from phoebusgen.v4 import Screen
from phoebusgen.v4.properties import (
    OpenDisplayAction,
    OpenFileAction,
    OpenWebpageAction,
    GroupStyle,
)
from phoebusgen.v4.properties.behavior import HasActionsRulesAndScripts
from phoebusgen.v4.properties.display import (
    HasBackgroundColor,
    HasForegroundColor,
    HasItemsFromPV,
    HasTransparent,
    HasVisible,
)
from phoebusgen.v4.properties.widget import HasName, HasPVName
from phoebusgen.v4.widgets import (
    ActionButton,
    EmbeddedDisplay,
    Label,
    TextEntry,
    TextUpdate,
    Widget,
    Group,
)

from ..linter import (
    FixableLintRule,
    LintRule,
    RuleViolation,
    SeverityLevel,
    UnsafeFixableLintRule,
    get_all_widgets,
)
from ..log import logger


def _find_closest_bob_match(
    filename: str, origin: Path, bob_file_tree: list[Path]
) -> Path | None:
    """Find the closest .bob file with the given filename relative to origin.

    If multiple files match the filename, return the one with the shortest
    relative path from the origin directory.
    """
    from os.path import relpath

    candidates = [p for p in bob_file_tree if p.name == filename]
    if not candidates:
        return None

    def relative_path_length(candidate: Path) -> int:
        rel_str = relpath(candidate.resolve(), origin.resolve())
        return len(Path(rel_str).parts)

    best = min(candidates, key=relative_path_length)
    return Path(relpath(best.resolve(), origin.resolve()))


class WidgetHeightOrWidthZeroOrNegative(LintRule):
    """Rule that checks if a widget has zero or negative height or width."""

    rule_code = "W101"
    description = "Widget has zero or negative height or width."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        rule_violations = []
        for widget in get_all_widgets(screen):
            if widget.width <= 0 or widget.height <= 0:
                rule_violations.append(
                    cls.rule_violation_factory(screen=screen, widget=widget)
                )
        return rule_violations


class WidgetOutOfBounds(FixableLintRule):
    """Rule that checks for widgets that are out of screen bounds."""

    rule_code = "W102"
    description = "Widget is out of screen bounds"

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        rule_violations = []
        for widget in get_all_widgets(screen):
            if (
                widget.x < 0
                or widget.y < 0
                or widget.x + widget.width > screen.width
                or widget.y + widget.height > screen.height
            ):
                rule_violations.append(
                    cls.rule_violation_factory(screen=screen, widget=widget, fixable=True)
                )
        return rule_violations

    @classmethod
    def fix(cls, violation: RuleViolation) -> bool:
        screen = violation.get_screen()
        widget = violation.widget
        fixed = False

        # A negative position puts the widget off the top/left edge, which
        # cannot be resolved by growing the screen, so clamp it into bounds.
        if widget is not None:
            if widget.x < 0:
                widget.x = 0
                fixed = True
            if widget.y < 0:
                widget.y = 0
                fixed = True

        all_widgets = get_all_widgets(screen)
        max_widget_x = max([w.x + w.width for w in all_widgets])
        max_widget_y = max([w.y + w.height for w in all_widgets])
        new_width = max(screen.width, max_widget_x + 10)
        new_height = max(screen.height, max_widget_y + 10)
        if new_width != screen.width or new_height != screen.height:
            screen.width = new_width
            screen.height = new_height
            fixed = True
        return fixed



class EmptyLabel(FixableLintRule):
    """Rule that checks for Label widgets that have empty text."""

    rule_code = "W104"
    description = "Label has empty text."

    @classmethod
    def get_empty_labels(cls, screen: Screen) -> list[Label]:
        return [
            widget
            for widget in get_all_widgets(screen)
            if isinstance(widget, Label)
            and widget.text.strip() == ""
            and not any(rule.prop_id == "text" for rule in widget.rules)
        ]

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        rule_violations = []
        for label in cls.get_empty_labels(screen):
            rule_violations.append(
                cls.rule_violation_factory(screen=screen, widget=label, fixable=True)
            )
        return rule_violations

    @classmethod
    def fix(cls, violation: RuleViolation) -> bool:
        if violation.widget is None:
            return False
        violation.get_screen().remove_widget(violation.widget)
        return True


class LabelWithExcessiveTextLength(LintRule):
    """Rule that checks for Label widgets that have excessively long text."""

    rule_code = "W105"
    description = "Label has excessively long text."

    # Approximate character width as a fraction of font size for proportional
    # sans-serif fonts. Based on typical glyph advance widths in Liberation Sans.
    _CHAR_WIDTH: dict[str, float] = {}
    for _c in "ilI|!.,;:'`":
        _CHAR_WIDTH[_c] = 0.17
    for _c in "fjrt()-[]{}/ \t1":
        _CHAR_WIDTH[_c] = 0.26
    for _c in "abcdeghknopqsuvxyz023456789":
        _CHAR_WIDTH[_c] = 0.38
    for _c in "ABCDEFGHJKLNOPQRSTUVXYZ":
        _CHAR_WIDTH[_c] = 0.47
    for _c in "mw":
        _CHAR_WIDTH[_c] = 0.51
    for _c in "MW":
        _CHAR_WIDTH[_c] = 0.60
    _DEFAULT_CHAR_WIDTH = 0.38

    @classmethod
    def _estimate_text_width(cls, text: str, font_size: float) -> float:
        """Estimate pixel width of text based on per-character weights and font size."""
        total_width_factor = sum(
            cls._CHAR_WIDTH.get(c, cls._DEFAULT_CHAR_WIDTH) for c in text
        )
        return total_width_factor * font_size * 1.33

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        rule_violations = []
        for widget in get_all_widgets(screen):
            if not isinstance(widget, Label):
                continue
            estimated_text_width = cls._estimate_text_width(
                widget.text, widget.font.size
            )
            if (
                estimated_text_width > widget.width
                and not widget.auto_size  # Ignore auto sized widgets
                and not widget.wrap_words  # Ignore widgets that wrap words
            ):
                rule_violations.append(
                    cls.rule_violation_factory(
                        screen=screen,
                        widget=widget,
                        details=cls.description
                        + f"Text: {widget.text} (Widget Width: {widget.width},"
                        + f" Estimated Text Width: {estimated_text_width})",
                    )
                )
        return rule_violations


class WidgetFontTwoLargeForHeight(FixableLintRule):
    """Rule that checks if the font size of a Label or TextUpdate widget is too large for its height."""

    rule_code = "W119"
    rule_severity = SeverityLevel.WARNING
    description = "Font size of Label or TextUpdate widget is too large for its height."

    # Rendered line height exceeds the nominal font size; this factor approximates
    # that overhead for Liberation Sans, matching the width model used by W105.
    _LINE_HEIGHT_FACTOR = 1.33
    # Total vertical padding (top + bottom) reserved inside the widget.
    _VERTICAL_PADDING = 2
    _WIDGET_TYPES = (Label, TextUpdate, TextEntry, ActionButton)

    @classmethod
    def _max_font_size(cls, height: float) -> int:
        """Largest font size whose rendered line height fits within the widget."""
        usable_height = height - cls._VERTICAL_PADDING
        return max(1, int(usable_height / cls._LINE_HEIGHT_FACTOR))

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        rule_violations = []
        for widget in get_all_widgets(screen):
            if not isinstance(widget, cls._WIDGET_TYPES):
                continue
            if widget.font.size > cls._max_font_size(widget.height):
                rule_violations.append(
                    cls.rule_violation_factory(
                        screen=screen,
                        widget=widget,
                        details=cls.description
                        + f"(Widget Height: {widget.height},"
                        + f" Font Size: {widget.font.size})",
                        fixable=True,
                    )
                )
        return rule_violations

    @classmethod
    def fix(cls, violation: RuleViolation) -> bool:
        widget = violation.widget
        if not isinstance(widget, cls._WIDGET_TYPES):
            return False
        max_size = cls._max_font_size(widget.height)
        if widget.font.size > max_size:
            widget.font.size = max_size
            return True
        return False



class TextUpdateWithNoDefinedPV(LintRule):
    """Rule that checks for widgets with text updates that have no defined PV."""

    rule_code = "W106"
    description = "Text update widget with no defined PV."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        rule_violations = []
        for widget in get_all_widgets(screen):
            if isinstance(widget, TextUpdate) and (
                widget.pv_name is None or widget.pv_name.strip() == ""
            ):
                rule_violations.append(
                    cls.rule_violation_factory(screen=screen, widget=widget)
                )
        return rule_violations


class EmbeddedDisplayNoFilePathSet(LintRule):
    """Rule that checks if an EmbeddedDisplay widget has no file path set."""

    rule_code = "W107"
    rule_severity = SeverityLevel.ERROR
    description = "EmbeddedDisplay widget has no file path set."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        rule_violations = []
        for widget in get_all_widgets(screen):
            if isinstance(widget, EmbeddedDisplay) and not widget.file:
                rule_violations.append(
                    cls.rule_violation_factory(screen=screen, widget=widget)
                )
        return rule_violations


class EmbeddedDisplayPathDoesNotExist(UnsafeFixableLintRule):
    """Rule that checks if an EmbeddedDisplay widget has a path that does not exist."""

    rule_code = "W108"
    rule_severity = SeverityLevel.ERROR
    description = "EmbeddedDisplay widget has a path that does not exist."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        rule_violations = []
        for widget in get_all_widgets(screen):
            if not isinstance(widget, EmbeddedDisplay) or widget.file is None:
                continue

            path = widget.file
            if not path.is_absolute() and screen.bob_file:
                path = Path(screen.bob_file).parent / path
            if not path.exists() or not path.is_file():
                rule_violations.append(
                    cls.rule_violation_factory(
                        screen=screen,
                        widget=widget,
                        details=f"{cls.description} Path: {widget.file}",
                        fixable=True,
                    )
                )

        return rule_violations

    @classmethod
    def fix(cls, violation: RuleViolation) -> bool:
        if not cls._linter or not cls._linter._bob_file_tree:
            return False

        screen = violation.screen
        widget = violation.widget
        if not isinstance(widget, EmbeddedDisplay) or widget.file is None:
            return False

        origin = Path(screen.bob_file).parent if screen.bob_file else Path.cwd()
        filename = Path(widget.file).name
        new_path = _find_closest_bob_match(filename, origin, cls._linter._bob_file_tree)
        if new_path is not None:
            logger.info(
                f"Repointing {widget.file} -> {new_path} in {screen.bob_file}"
            )
            widget.file = new_path
            return True
        return False


class EmbeddedDisplayPathIsOpiFile(LintRule):
    """Checks if EmbeddedDisplay has a path that points to an OPI file."""

    rule_code = "W109"

    # TODO: Make this ERROR. We want to get out of the habit of mixing bob and opi
    rule_severity = SeverityLevel.WARNING

    description = (
        "EmbeddedDisplay widget has a path that points to an OPI file, not a bob file."
    )

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        rule_violations = []
        for widget in get_all_widgets(screen):
            if not isinstance(widget, EmbeddedDisplay) or widget.file is None:
                continue
            path = widget.file
            if not path.is_absolute() and screen.bob_file:
                path = Path(screen.bob_file).parent / path
            if path.suffix.lower() == ".opi":
                rule_violations.append(
                    cls.rule_violation_factory(
                        screen=screen,
                        widget=widget,
                        details=f"{cls.description} Path: {widget.file}",
                    )
                )

        return rule_violations


class OpenDisplayActionPathNotSet(LintRule):
    """Rule that checks if an OpenDisplayAction has no file path set."""

    rule_code = "W110"
    rule_severity = SeverityLevel.ERROR
    description = "OpenDisplayAction has no file path set."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        rule_violations = []
        for widget in get_all_widgets(screen):
            if not isinstance(widget, HasActionsRulesAndScripts):
                continue
            for action in widget.actions:
                if isinstance(action, OpenDisplayAction) and not action.file:
                    rule_violations.append(
                        cls.rule_violation_factory(screen=screen, widget=widget)
                    )
        return rule_violations


class OpenDisplayActionPathDoesNotExist(UnsafeFixableLintRule):
    """Rule that checks if an OpenDisplayAction has a path that does not exist."""

    rule_code = "W111"
    rule_severity = SeverityLevel.ERROR
    description = "OpenDisplayAction has a path that does not exist."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        rule_violations = []
        for widget in get_all_widgets(screen):
            if not isinstance(widget, HasActionsRulesAndScripts):
                continue
            for action in widget.actions:
                if isinstance(action, OpenDisplayAction) and action.file is not None:
                    path = action.file
                    if not path.is_absolute() and screen.bob_file:
                        path = Path(screen.bob_file).parent / path
                    if not path.exists() or not path.is_file():
                        rule_violations.append(
                            cls.rule_violation_factory(
                                screen=screen,
                                widget=widget,
                                details=f"{cls.description} Path: {action.file}",
                                fixable=True,
                            )
                        )

        return rule_violations

    @classmethod
    def fix(cls, violation: RuleViolation) -> bool:
        if not cls._linter or not cls._linter._bob_file_tree:
            return False

        screen = violation.screen
        widget = violation.widget
        origin = Path(screen.bob_file).parent if screen.bob_file else Path.cwd()
        if not isinstance(widget, HasActionsRulesAndScripts):
            return False

        # Find the action matching this violation's details
        for action in widget.actions:
            if not isinstance(action, OpenDisplayAction) or action.file is None:
                continue
            if f"Path: {action.file}" not in violation.details:
                continue
            filename = Path(action.file).name
            new_path = _find_closest_bob_match(filename, origin, cls._linter._bob_file_tree)
            if new_path is not None:
                logger.info(
                    f"Repointing {action.file} -> {new_path} in {screen.bob_file}"
                )
                action.file = new_path
                return True
        return False


class OpenDisplayActionPathIsOpiFile(UnsafeFixableLintRule):
    """Checks if OpenDisplayAction has a path that points to an OPI file."""

    rule_code = "W112"
    rule_severity = SeverityLevel.WARNING
    description = (
        "OpenDisplayAction has a path that points to an OPI file, not a bob file."
    )

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        rule_violations = []
        for widget in get_all_widgets(screen):
            if not isinstance(widget, HasActionsRulesAndScripts):
                continue
            for action in widget.actions:
                if isinstance(action, OpenDisplayAction) and action.file is not None:
                    path = action.file
                    if not path.is_absolute() and screen.bob_file:
                        path = Path(screen.bob_file).parent / path
                    if path.suffix.lower() == ".opi":
                        rule_violations.append(
                            cls.rule_violation_factory(
                                screen=screen,
                                widget=widget,
                                details=f"{cls.description} Path: {action.file}",
                                fixable=path.with_suffix(".bob").is_file(),
                            )
                        )

        return rule_violations

    @classmethod
    def fix(cls, violation: RuleViolation) -> bool:
        screen = violation.screen
        widget = violation.widget
        if not isinstance(widget, HasActionsRulesAndScripts):
            return False

        for action in widget.actions:
            if not isinstance(action, OpenDisplayAction) or action.file is None:
                continue
            if f"Path: {action.file}" not in violation.details:
                continue
            resolved = action.file
            if not resolved.is_absolute() and screen.bob_file:
                resolved = Path(screen.bob_file).parent / resolved
            if resolved.with_suffix(".bob").is_file():
                new_path = action.file.with_suffix(".bob")
                logger.info(
                    f"Repointing {action.file} -> {new_path} in {screen.bob_file}"
                )
                action.file = new_path
                return True
        return False


class OpenFileActionPathDoesNotExist(UnsafeFixableLintRule):
    """Rule that checks if an OpenFileAction has a path that does not exist."""

    rule_code = "W113"
    description = "OpenFileAction has a path that does not exist."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        rule_violations = []
        for widget in get_all_widgets(screen):
            if not isinstance(widget, HasActionsRulesAndScripts):
                continue
            for action in widget.actions:
                if isinstance(action, OpenFileAction):
                    path = action.file
                    if path is None:
                        continue
                    if not path.is_absolute() and screen.bob_file:
                        path = Path(screen.bob_file).parent / path
                    if not path.exists() or not path.is_file():
                        rule_violations.append(
                            cls.rule_violation_factory(
                                screen=screen,
                                widget=widget,
                                details=f"{cls.description} Path: {action.file}",
                                fixable=True,
                            )
                        )

        return rule_violations

    @classmethod
    def fix(cls, violation: RuleViolation) -> bool:
        if not cls._linter or not cls._linter._bob_file_tree:
            return False

        screen = violation.screen
        widget = violation.widget
        origin = Path(screen.bob_file).parent if screen.bob_file else Path.cwd()
        if widget is None:
            return False

        for action in widget.actions:
            if not isinstance(action, OpenFileAction):
                continue
            if action.file is None:
                continue
            if f"Path: {action.file}" not in violation.details:
                continue
            filename = Path(action.file).name
            new_path = _find_closest_bob_match(filename, origin, cls._linter._bob_file_tree)
            if new_path is not None:
                logger.info(
                    f"Repointing {action.file} -> {new_path} in {screen.bob_file}"
                )
                action.file = new_path
                return True
        return False


class OpenWebpageActionInvalidUrl(LintRule):
    """Rule that checks if an OpenWebpageAction has an invalid URL."""

    rule_code = "W114"
    description = "OpenWebpageAction has an invalid URL."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        rule_violations = []
        for widget in get_all_widgets(screen):
            if not isinstance(widget, HasActionsRulesAndScripts):
                continue
            for action in widget.actions:
                if isinstance(action, OpenWebpageAction):
                    if not action.url.startswith(("http://", "https://")):
                        rule_violations.append(
                            cls.rule_violation_factory(
                                screen=screen,
                                widget=widget,
                                details=f"{cls.description} URL: {action.url}",
                            )
                        )

        return rule_violations


class PVNamePropertyNotSet(LintRule):
    """Rule that checks if a widget with a PVName property has it set."""

    rule_code = "W115"
    rule_severity = SeverityLevel.ERROR
    description = "Widget with PVName property has it not set."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        rule_violations = []
        for widget in get_all_widgets(screen):
            if (
                not isinstance(widget, HasPVName)
                or (isinstance(widget, HasItemsFromPV) and not widget.items_from_pv)
                or isinstance(widget, ActionButton)
            ):
                continue
            if not widget.pv_name or widget.pv_name.strip() == "":
                rule_violations.append(
                    cls.rule_violation_factory(screen=screen, widget=widget)
                )

        return rule_violations


class DuplicateWidgetNames(FixableLintRule):
    """Rule that checks for duplicate widget names."""

    rule_code = "W116"
    description = "Duplicate widget names found."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        rule_violations = []
        seen_names = set()
        for widget in get_all_widgets(screen):
            if not isinstance(widget, HasName):
                continue
            if widget.name in seen_names:
                rule_violations.append(
                    cls.rule_violation_factory(screen=screen, widget=widget, fixable=True)
                )
            else:
                seen_names.add(widget.name)

        return rule_violations

    @classmethod
    def fix(cls, violation: RuleViolation) -> bool:
        screen = violation.screen
        widget = violation.widget
        if widget is None:
            return False
        # Collect all names in the screen to avoid collisions
        existing_names = {
            w.name for w in get_all_widgets(screen)
            if isinstance(w, HasName) and w is not widget
        }
        base_name = widget.name
        counter = 1
        new_name = f"{base_name}_{counter}"
        while new_name in existing_names:
            counter += 1
            new_name = f"{base_name}_{counter}"
        widget.name = new_name
        return True


class FGAndBGColorAreIdentical(LintRule):
    """Rule that checks if a widget's foreground and background colors are identical."""

    rule_code = "W117"
    description = "Foreground and background colors are identical."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        rule_violations = []
        for widget in (
            w
            for w in get_all_widgets(screen)
            if isinstance(w, HasForegroundColor) and isinstance(w, HasBackgroundColor)
        ):
            fg = widget.foreground_color
            # For Group widgets with a TITLE_BAR style, use the line color as the background color (foreground = text color, line = title bar color)
            bg = widget.background_color if not (isinstance(widget, Group) and widget.style == GroupStyle.TITLE_BAR) else widget.line_color
            if fg == bg:
                if isinstance(widget, HasTransparent) and widget.transparent:
                    continue
                if isinstance(widget, Group) and widget.style == GroupStyle.NONE:
                    continue
                rule_violations.append(
                    cls.rule_violation_factory(
                        screen=screen,
                        widget=widget,
                        details=cls.description
                        + f" (foreground: {widget.foreground_color},"
                        + f" background: {widget.background_color})",
                    )
                )

        return rule_violations


class WidgetNotVisibleAndNoRules(FixableLintRule):
    """Check if a widget is not visible and doesn't have a visibility rule."""

    rule_code = "W118"
    description = "Widget is not visible and doesn't have a visibility rule."

    @classmethod
    def get_not_visible_widgets(cls, screen: Screen) -> list[Widget]:
        not_visible_widgets = []
        for widget in get_all_widgets(screen):
            if not isinstance(widget, HasVisible):
                continue
            if widget.visible is False and len(widget.rules) == 0:
                not_visible_widgets.append(widget)
            elif not widget.visible:
                if not any(rule.prop_id == "visible" for rule in widget.rules):
                    not_visible_widgets.append(widget)
        return not_visible_widgets

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        rule_violations = []
        for widget in cls.get_not_visible_widgets(screen):
            rule_violations.append(
                cls.rule_violation_factory(screen=screen, widget=widget, fixable=True)
            )

        return rule_violations

    @classmethod
    def fix(cls, violation: RuleViolation) -> bool:
        screen = violation.screen
        widget = violation.widget
        if widget is None:
            return False
        screen.remove_widget(widget)
        return True
