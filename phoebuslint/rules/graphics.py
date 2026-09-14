from phoebusgen.v4 import Screen
from phoebusgen.v4.properties.display import HasLineWidth, HasTransparent

from ..linter import FixableLintRule, RuleViolation


class TransparentGraphicWithZeroLineWidth(FixableLintRule):
    """Check if a graphics widget has transparent set to true and line width set to 0.

    With transparent set to true, line width should be set to 1 or greater, otherwise
    the graphic will not be visible.
    """

    rule_code = "G101"
    description = "Transparent graphic has zero line width."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        rule_violations = []
        for widget in screen.get_all_widgets():
            if isinstance(widget, HasTransparent) and isinstance(widget, HasLineWidth):
                for rule in widget.rules:
                    # Skip check if there is a rule that adjusts the visible, line
                    # width, or transparent property
                    if rule.prop_id in ("visible", "line_width", "transparent"):
                        continue
                if widget.transparent and widget.line_width == 0:
                    rule_violations.append(
                        cls.rule_violation_factory(
                            screen=screen, widget=widget, fixable=True
                        )
                    )
        return rule_violations

    @classmethod
    def fix(cls, violation: RuleViolation) -> bool:
        widget = violation.widget
        if widget is None or not isinstance(widget, HasLineWidth):
            return False
        widget.line_width = 1
        return True
