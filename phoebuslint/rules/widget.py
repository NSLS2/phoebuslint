from pathlib import Path

from phoebusgen.v4 import Screen
from phoebusgen.v4.properties import (
    OpenDisplayAction,
    OpenFileAction,
    OpenWebpageAction,
)
from phoebusgen.v4.properties.behavior import HasActionsRulesAndScripts
from phoebusgen.v4.properties.display import (
    HasBackgroundColor,
    HasForegroundColor,
    HasItemsFromPV,
    HasVisible,
)
from phoebusgen.v4.properties.widget import HasName, HasPVName
from phoebusgen.v4.widgets import (
    ActionButton,
    EmbeddedDisplay,
    Label,
    TextUpdate,
    Widget,
)

from ..linter import (
    FixableLintRule,
    LintRule,
    RuleViolation,
    SeverityLevel,
    get_all_widgets,
)


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
                    cls.rule_violation_factory(screen=screen, widget=widget)
                )
        return rule_violations

    @classmethod
    def fix(cls, screen: Screen) -> None:
        max_widget_x = max([widget.x + widget.width for widget in screen.widgets])
        max_widget_y = max([widget.y + widget.height for widget in screen.widgets])
        screen.width = max(screen.width, max_widget_x + 10)
        screen.height = max(screen.height, max_widget_y + 10)


class EmptyLabel(LintRule):
    """Rule that checks for Label widgets that have empty text."""

    rule_code = "W104"
    description = "Label has empty text."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        rule_violations = []
        for widget in get_all_widgets(screen):
            if (
                isinstance(widget, Label)
                and widget.text.strip() == ""
                and not any(rule.prop_id == "text" for rule in widget.rules)
            ):
                rule_violations.append(
                    cls.rule_violation_factory(screen=screen, widget=widget)
                )
        return rule_violations


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


class EmbeddedDisplayPathDoesNotExist(LintRule):
    """Rule that checks if an EmbeddedDisplay widget has a path that does not exist."""

    rule_code = "W108"
    rule_severity = SeverityLevel.ERROR
    description = "EmbeddedDisplay widget has a path that does not exist."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        rule_violations = []
        for widget in get_all_widgets(screen):
            if not isinstance(widget, EmbeddedDisplay):
                continue
            path = Path(widget.file)
            if not path.is_absolute() and screen.bob_file:
                path = Path(screen.bob_file).parent / path
            if not path.exists() or not path.is_file():
                rule_violations.append(
                    cls.rule_violation_factory(
                        screen=screen,
                        widget=widget,
                        details=f"{cls.description} Path: {widget.file}",
                    )
                )

        return rule_violations


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
            if not isinstance(widget, EmbeddedDisplay):
                continue
            path = Path(widget.file)
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


class OpenDisplayActionPathDoesNotExist(LintRule):
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
                if isinstance(action, OpenDisplayAction):
                    path = Path(action.file)
                    if not path.is_absolute() and screen.bob_file:
                        path = Path(screen.bob_file).parent / path
                    if not path.exists() or not path.is_file():
                        rule_violations.append(
                            cls.rule_violation_factory(
                                screen=screen,
                                widget=widget,
                                details=f"{cls.description} Path: {action.file}",
                            )
                        )

        return rule_violations


class OpenDisplayActionPathIsOpiFile(LintRule):
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
                if isinstance(action, OpenDisplayAction):
                    path = Path(action.file)
                    if not path.is_absolute() and screen.bob_file:
                        path = Path(screen.bob_file).parent / path
                    if path.suffix.lower() == ".opi":
                        rule_violations.append(
                            cls.rule_violation_factory(
                                screen=screen,
                                widget=widget,
                                details=f"{cls.description} Path: {action.file}",
                            )
                        )

        return rule_violations


class OpenFileActionPathDoesNotExist(LintRule):
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
                            )
                        )

        return rule_violations


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
                    cls.rule_violation_factory(screen=screen, widget=widget)
                )
            else:
                seen_names.add(widget.name)

        return rule_violations

    @classmethod
    def fix(cls, screen: Screen) -> None:
        seen_names: dict[str, int] = {}
        for widget in get_all_widgets(screen):
            if not isinstance(widget, HasName):
                continue
            if widget.name in seen_names:
                seen_names[widget.name] += 1
                new_name = f"{widget.name}_{seen_names[widget.name]}"
                while new_name in seen_names:
                    seen_names[widget.name] += 1
                    new_name = f"{widget.name}_{seen_names[widget.name]}"
                widget.name = new_name
                seen_names[new_name] = 0
            else:
                seen_names[widget.name] = 0


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
            if widget.foreground_color == widget.background_color:
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
                cls.rule_violation_factory(screen=screen, widget=widget)
            )

        return rule_violations

    @classmethod
    def fix(cls, screen: Screen) -> None:
        for widget in cls.get_not_visible_widgets(screen):
            screen.remove_widget(widget)
