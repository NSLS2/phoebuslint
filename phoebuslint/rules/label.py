

from phoebusgen.v4 import Screen
from phoebusgen.v4.widgets import Label

from phoebuslint.linter import FixableLintRule, LintRule, RuleViolation, get_all_widgets


class EmptyLabel(FixableLintRule):
    """Rule that checks for Label widgets that have empty text."""

    rule_code = "L101"
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
        violation.screen.remove_widget(violation.widget)
        return True


class LabelWithExcessiveTextLength(LintRule):
    """Rule that checks for Label widgets that have excessively long text."""

    rule_code = "L102"
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
