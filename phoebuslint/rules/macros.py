from pathlib import Path

from phoebusgen.v4 import Screen

from ..linter import LintRule, RuleViolation, SeverityLevel


class UndefinedMacrosInScreenTransition(LintRule):
    """Rule that checks if screen transitions pass all macros required by the target."""

    rule_code = "M101"
    description = "Screen transition leads to undefined macros in target screen."
    rule_severity = SeverityLevel.ERROR

    @classmethod
    def _collect_cycle_macros(cls, start: Path, visited: set[Path]) -> set[str]:
        """Pool the required macros of every screen reachable from ``start``.

        Follows navigation links depth-first, recording each visited screen in
        ``visited`` (so callers can detect whether a particular screen lies on
        the traversal) and accumulating the macros each screen references
        without a default.
        """
        start = start.resolve()
        if start in visited or not start.is_file():
            return set()
        visited.add(start)

        try:
            screen = Screen(f_name=str(start))
        except Exception:
            return set()

        required_macros, _ = screen.get_used_macros()
        for transition in screen.get_linked_screens():
            next_path = start.parent / transition.target
            required_macros |= cls._collect_cycle_macros(next_path, visited)
        return required_macros

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        rule_violations: list[RuleViolation] = []

        if screen.bob_file is None:
            return []

        nav_graph = screen.build_navigation_graph()
        source_path = Path(screen.bob_file)
        source_used_macros, source_default_macros = screen.get_used_macros()

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

            target_required_macros, target_default_macros = (
                target_screen.get_used_macros()
            )
            available_macros = source_used_macros | set(edge.macros.keys())

            # Circular transition dependency: if the target can navigate back to
            # the source, the two screens belong to the same navigation cycle.
            # Macros required anywhere in that cycle are assumed to be supplied by
            # whatever external launcher enters the cycle (the same root-node
            # assumption applied to a group of mutually-linked screens), so treat
            # every macro referenced within the cycle as available.
            cycle_visited: set[Path] = set()
            cycle_macros = cls._collect_cycle_macros(target_path, cycle_visited)
            if source_path.resolve() in cycle_visited:
                available_macros |= cycle_macros

            undefined_macros = (
                target_required_macros - available_macros - target_default_macros
            )

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
