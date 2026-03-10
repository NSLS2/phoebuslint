<<<<<<< HEAD
=======
from phoebusgen.v4 import Screen
>>>>>>> e028c9a78aaeafe17aa94d1289bb423569f2affe
from phoebuslint import LintRule, RecursiveLintRule



def test_all_rule_codes_unique():
    """Test to ensure all LintRule subclasses have unique rule codes."""
    rule_codes = set()
    all_rule_classes = LintRule.__subclasses__() + RecursiveLintRule.__subclasses__()
    for rule_cls in all_rule_classes:
        assert rule_cls.rule_code not in rule_codes, (
            f"Duplicate rule code found: {rule_cls.rule_code}"
        )
        rule_codes.add(rule_cls.rule_code)


def test_rule_violation_factory():
    """Test the rule_violation factory method for LintRule subclasses."""
    all_rule_classes = LintRule.__subclasses__() + RecursiveLintRule.__subclasses__()
    for rule_cls in all_rule_classes:
        violation = rule_cls.rule_violation_factory(
            screen=Screen(f_name="test_screen.bob")
        )  # screen can be None for this test
        assert violation.rule_code == rule_cls.rule_code, (
            f"Rule code mismatch in {rule_cls.__name__}"
        )
        assert violation.rule_severity == rule_cls.rule_severity, (
            f"Rule severity mismatch in {rule_cls.__name__}"
        )
        assert violation.screen.bob_file == "test_screen.bob", (
            f"Screen file mismatch in {rule_cls.__name__}"
        )
