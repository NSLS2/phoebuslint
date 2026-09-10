from phoebusgen.v4 import Screen
from phoebusgen.v4.properties.display import HasLineWidth, HasTransparent

from ..linter import FixableLintRule, RuleViolation


class TransparentGraphicWithZeroLineWidth(FixableLintRule):
    rule_code = "G101"
    description = "Transparent graphic has zero line width."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        rule_violations = []
        for widget in screen.get_all_widgets():
            if isinstance(widget, HasTransparent) and isinstance(widget, HasLineWidth):
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
