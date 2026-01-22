import pytest
from phoebuslint.rules import LintRule

def test_unique_rule_codes():
    """Test to ensure all LintRule subclasses have unique rule codes."""
    rule_codes = set()
    for rule_cls in LintRule.__subclasses__():
        assert rule_cls.rule_code not in rule_codes, f"Duplicate rule code found: {rule_cls.rule_code}"
        rule_codes.add(rule_cls.rule_code)