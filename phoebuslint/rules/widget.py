from phoebusgen.v4 import Screen
from phoebusgen.v4.properties import GroupStyle
from phoebusgen.v4.properties.display import (
    HasBackgroundColor,
    HasFont,
    HasForegroundColor,
    HasItemsFromPV,
    HasTransparent,
    HasVisible,
)
from phoebusgen.v4.properties.widget import HasName, HasPVName
from phoebusgen.v4.widgets import (
    ActionButton,
    Group,
    Label,
    TextEntry,
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
                    cls.rule_violation_factory(
                        screen=screen, widget=widget, fixable=True
                    )
                )
        return rule_violations

    @classmethod
    def fix(cls, violation: RuleViolation) -> bool:
        screen = violation.screen
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


class WidgetFontTooLargeForHeight(FixableLintRule):
    """Check if the font size of a widget is too large for its height."""

    rule_code = "W119"
    rule_severity = SeverityLevel.WARNING
    description = "Font size of widget is too large given its height."

    # Rendered line height exceeds the nominal font size; this factor approximates
    # that overhead for Liberation Sans, matching the width model used by W105.
    _LINE_HEIGHT_FACTOR = 1.14
    # Total vertical padding (top + bottom) reserved inside the widget.
    _VERTICAL_PADDING = 0
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
                    cls.rule_violation_factory(
                        screen=screen, widget=widget, fixable=True
                    )
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
            w.name
            for w in get_all_widgets(screen)
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
            # For Group widgets with a TITLE_BAR style, use the line color as the
            # background color (foreground = text color, line = title bar color)
            bg = (
                widget.background_color
                if not (
                    isinstance(widget, Group) and widget.style == GroupStyle.TITLE_BAR
                )
                else widget.line_color
            )
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


class WidgetHasInvalidDecimalFontSize(FixableLintRule):
    """Check if a widget's font size is a decimal value instead of an integer.

    Auto-converted screens from other display managers can produce floating point
    font-sizes, but phoebus only accepts integral ones.
    """

    rule_code = "W120"
    description = "Widget has a font size that is a float value instead of an integer."

    @classmethod
    def _extract_font_size(cls, widget: HasFont) -> float | None:

        font_element = widget.root.find("font/font")
        if font_element is None:
            return None
        font_size_attrib = font_element.attrib.get("size")
        if font_size_attrib is None:
            return None
        return float(font_size_attrib)

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        rule_violations = []
        for widget in get_all_widgets(screen):
            if not isinstance(widget, HasFont):
                continue
            font_size_attrib = cls._extract_font_size(widget)
            if font_size_attrib is None:
                continue
            if not float(
                font_size_attrib
            ).is_integer():  # Check if it can be converted to float
                rule_violations.append(
                    cls.rule_violation_factory(
                        screen=screen,
                        widget=widget,
                        details=f"Font size is a non-integral: {font_size_attrib}",
                        fixable=True,
                    )
                )
        return rule_violations

    @classmethod
    def fix(cls, violation: RuleViolation) -> bool:
        widget = violation.widget
        if not isinstance(widget, HasFont):
            return False
        font_size_attrib = cls._extract_font_size(widget)
        if font_size_attrib is None:
            return False
        if not float(font_size_attrib).is_integer():
            font_element = widget.root.find("font/font")
            if font_element is None:
                return False
            font_element.set("size", str(int(round(float(font_size_attrib)))))
            return True
        return False
