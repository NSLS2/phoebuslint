from pathlib import Path

from phoebusgen.v4 import Screen

from ..linter import LintRule, RuleViolation, SeverityLevel


# Phoebus builtin macros. Not all-encompassing.
PHOEBUS_BUILTIN_MACROS = {"pv_name", "pv_value", "DID", "DNAME", "WID", "HEI", "SHOW"}

class UndefinedMacrosInScreenTransition(LintRule):
    """Rule that checks if screen transitions pass all macros required by the target."""

    rule_code = "M101"
    description = "Screen transition leads to undefined macros in target screen."
    rule_severity = SeverityLevel.ERROR

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        rule_violations: list[RuleViolation] = []

        nav_graph = screen.build_navigation_graph()
        source_path = Path(screen.bob_file)
        source_used_macros = screen.get_used_macros()

        for edge in nav_graph.transitions:
            if Path(edge.source) != source_path:
                continue

            target_path = source_path.parent / edge.target
            if not target_path.is_file():
                continue

            try:
                target_screen = Screen(f_name=str(target_path))
            except Exception:
                continue

            target_required_macros = target_screen.get_used_macros()
            available_macros = source_used_macros | set(edge.macros.keys())

            # pv_name and pv_value are special macros often used in tooltips
            available_macros |= PHOEBUS_BUILTIN_MACROS

            undefined_macros = target_required_macros - available_macros

            if undefined_macros:
                sorted_undefined = sorted(undefined_macros)
                rule_violations.append(
                    cls.rule_violation_factory(
                        screen=screen,
                        details=(
                            f"Transition to '{edge.target}' has undefined macros: "
                            f"{', '.join(sorted_undefined)}"
                        ),
                    )
                )

        return rule_violations


def _can_expand_macros(value: str, macros: dict[str, str]) -> bool:
    """Helper function to determine if a string with macros can be fully expanded."""
    while "$(" in value:
        start_index = value.find("$(")
        end_index = value.find(")", start_index)
        if end_index == -1:
            break  # No closing parenthesis found, invalid macro syntax
        macro_name = value[start_index + 2 : end_index]
        if macro_name not in macros:
            return False  # Macro cannot be expanded
        macro_value = macros[macro_name]
        value = value[:start_index] + macro_value + value[end_index + 1 :]
    return True
