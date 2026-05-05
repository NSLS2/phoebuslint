from pathlib import Path

from phoebusgen.v4 import Screen
from phoebusgen.v4.properties import (
    OpenDisplayAction,
    OpenFileAction,
    OpenWebpageAction,
)
from phoebusgen.v4.properties.behavior import HasActionsRulesAndScripts
from phoebusgen.v4.properties.display import HasItemsFromPV, HasPVName
from phoebusgen.v4.widgets import (
    ActionButton,
    EmbeddedDisplay,
    Label,
    TextUpdate,
    Widget,
)

from ..linter import LintRule, RuleViolation, SeverityLevel


class WidgetHeightOrWidthZeroOrNegative(LintRule):
    """Rule that checks if a widget has zero or negative height or width."""

    rule_code = "W101"
    description = "Widget has zero or negative height or width."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        rule_violations = []
        for widget in screen.get_widgets():
            if widget.width <= 0 or widget.height <= 0:
                rule_violations.append(
                    cls.rule_violation_factory(screen=screen, widget=widget)
                )
        return rule_violations


class WidgetOutOfBounds(LintRule):
    """Rule that checks for widgets that are out of screen bounds."""

    rule_code = "W102"
    description = "Widget is out of screen bounds"

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        rule_violations = []
        for widget in screen.get_widgets():
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


class ActionButtonWithNoActions(LintRule):
    """Rule that checks for ActionButton widgets that have no actions defined."""

    rule_code = "W103"
    description = "ActionButton has no actions defined."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        rule_violations = []
        for widget in screen.get_widgets_by_type(ActionButton):
            if len(widget.actions) == 0:
                rule_violations.append(
                    cls.rule_violation_factory(screen=screen, widget=widget)
                )
        return rule_violations


class EmptyLabel(LintRule):
    """Rule that checks for Label widgets that have empty text."""

    rule_code = "W104"
    description = "Label has empty text."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        rule_violations = []
        for widget in screen.get_widgets_by_type(Label):
            if widget.text.strip() == "":
                rule_violations.append(
                    cls.rule_violation_factory(screen=screen, widget=widget)
                )
        return rule_violations


class LabelWithExcessiveTextLength(LintRule):
    """Rule that checks for Label widgets that have excessively long text."""

    rule_code = "W105"
    description = "Label has excessively long text."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        rule_violations = []
        for widget in screen.get_widgets_by_type(Label):
            # Assumes typical DPI of 96 and average character width of font size * 0.5
            # TODO: Make this configurable
            if (
                len(widget.text) * widget.font.size * 0.5 * 96 / 72 > widget.width
                and not widget.auto_size
            ):
                rule_violations.append(
                    cls.rule_violation_factory(screen=screen, widget=widget)
                )
        return rule_violations


class TextUpdateWithNoDefinedPV(LintRule):
    """Rule that checks for widgets with text updates that have no defined PV."""

    rule_code = "W106"
    description = "Text update widget with no defined PV."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        rule_violations = []
        for text_update in screen.get_widgets_by_type(TextUpdate):
            if text_update.pv_name is None or text_update.pv_name.strip() == "":
                rule_violations.append(
                    cls.rule_violation_factory(screen=screen, widget=text_update)
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
        for widget in screen.get_widgets_by_type(EmbeddedDisplay):
            if not widget.file:
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
        for widget in screen.get_widgets_by_type(EmbeddedDisplay):
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
        for widget in screen.get_widgets_by_type(EmbeddedDisplay):
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
        for widget in screen.get_widgets_by_property_class(HasActionsRulesAndScripts):
            if not isinstance(widget, Widget):
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
        for widget in screen.get_widgets_by_property_class(HasActionsRulesAndScripts):
            if not isinstance(widget, Widget):
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
        for widget in screen.get_widgets_by_property_class(HasActionsRulesAndScripts):
            if not isinstance(widget, Widget):
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
        for widget in screen.get_widgets_by_property_class(HasActionsRulesAndScripts):
            if not isinstance(widget, Widget):
                continue
            for action in widget.actions:
                if isinstance(action, OpenFileAction):
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


class OpenWebpageActionInvalidUrl(LintRule):
    """Rule that checks if an OpenWebpageAction has an invalid URL."""

    rule_code = "W114"
    description = "OpenWebpageAction has an invalid URL."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        rule_violations = []
        for widget in screen.get_widgets_by_property_class(HasActionsRulesAndScripts):
            if not isinstance(widget, Widget):
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
        for widget in screen.get_widgets_by_property_class(HasPVName):
            if (
                not isinstance(widget, Widget)
                or (isinstance(widget, HasItemsFromPV) and not widget.items_from_pv)
                or isinstance(widget, ActionButton)
            ):
                continue
            if not widget.pv_name or widget.pv_name.strip() == "":
                rule_violations.append(
                    cls.rule_violation_factory(screen=screen, widget=widget)
                )

        return rule_violations
