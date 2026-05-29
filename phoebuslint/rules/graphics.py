from ..log import logger
from ..linter import LintRule, RuleViolation, RuleViolationFactory, FixableLintRule
from phoebusgen.v4 import Screen
from phoebusgen.v4.widgets import Arc, Rectangle, Ellipse, Image, Polygon, Polyline
from phoebusgen.v4.properties.display import HasTransparent, HasLineWidth


class TransparentGraphicWithZeroLineWidth(LintRule):
    rule_code = "G101"
    description = "Transparent graphic has zero line width."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        rule_violations = []
        for widget in screen.get_all_widgets():
            if isinstance(widget, HasTransparent) and isinstance(widget, HasLineWidth):
                if widget.transparent and widget.line_width == 0:
                    rule_violations.append(
                        cls.rule_violation_factory(screen=screen, widget=widget)
                    )
        return rule_violations

    @classmethod
    def fix(cls, screen: Screen) -> None:
        for widget in screen.get_all_widgets():
            if isinstance(widget, HasTransparent) and isinstance(widget, HasLineWidth):
                if widget.transparent and widget.line_width == 0:
                    widget.line_width = 1