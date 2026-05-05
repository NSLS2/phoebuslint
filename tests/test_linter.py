from pathlib import Path

import pytest
from phoebusgen.v4 import Screen
from phoebusgen.v4.widgets import Label
from phoebuslint import (
    PhoebusLinter,
    RuleViolation,
    SeverityLevel,
)
from phoebuslint.linter import RuleViolationFactory


def test_rule_violation():
    violation = RuleViolation(
        rule_name="TestRule",
        rule_code="T001",
        rule_severity=SeverityLevel.ERROR,
        screen=Path("test_screen.bob"),
        widget=None,
        property=None,
        property_element=None,
        details="Test violation",
    )
    assert violation.rule_name == "TestRule"
    assert violation.rule_code == "T001"
    assert violation.rule_severity == SeverityLevel.ERROR
    assert violation.screen == Path("test_screen.bob")
    assert violation.details == "Test violation"

    assert str(violation) == "[T001] TestRule: Test violation (Screen: test_screen.bob)"


def test_all_rule_codes_unique(all_rule_classes):
    """Test to ensure all LintRule subclasses have unique rule codes."""
    rule_codes = set()
    for rule_cls in all_rule_classes:
        assert rule_cls.rule_code not in rule_codes, (
            f"Duplicate rule code found: {rule_cls.rule_code}"
        )
        rule_codes.add(rule_cls.rule_code)


class TestRule(RuleViolationFactory):
    rule_code = "T001"
    description = "Example rule for testing."
    rule_severity = SeverityLevel.WARNING


def test_rule_violation_factory(tmp_path):
    screen_path = tmp_path / "test_screen.bob"
    screen = Screen(f_name=screen_path)
    violation = TestRule.rule_violation_factory(
        screen=screen,
    )
    assert violation.rule_name == "TestRule"  # Assuming the factory sets this
    assert violation.rule_code == "T001"  # Assuming the factory sets this
    assert (
        violation.rule_severity == SeverityLevel.WARNING
    )  # Assuming the factory sets this
    assert violation.screen == screen
    assert violation.widget is None
    assert violation.property is None
    assert violation.property_element is None
    assert (
        violation.details == "Example rule for testing."
    )  # Assuming the factory sets this
    assert (
        str(violation)
        == f"[T001] TestRule: Example rule for testing. (Screen: {screen_path})"
    )

    # Now add a widget and make a more typical violation
    label = Label("test_label", "Test Label", 0, 0, 10, 10)
    screen.add_widget(label)
    violation = TestRule.rule_violation_factory(
        screen=screen,
        widget=label,
        property="text",
        property_element="text_elem",
        details="Test violation details",
    )
    assert violation.rule_name == "TestRule"  # Assuming the factory sets this
    assert violation.rule_code == "T001"  # Assuming the factory sets this
    assert (
        violation.rule_severity == SeverityLevel.WARNING
    )  # Assuming the factory sets this
    assert violation.screen == screen
    assert violation.widget == label
    assert violation.property == "text"
    assert violation.property_element == "text_elem"
    assert violation.details == "Test violation details"
    assert (
        str(violation)
        == f"[T001] TestRule: Test violation details (Screen: {screen_path}, Widget: test_label, Property: text, Element: text_elem)"  # noqa: E501
    )


def test_rule_violation_factory_rule_classes(all_rule_classes):
    """Test the rule_violation factory method for LintRule subclasses."""
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


def test_base_linter_configuration(all_rule_classes):
    linter = PhoebusLinter()
    assert linter._enabled_rules == all_rule_classes
    assert linter._fail_severity == SeverityLevel.WARNING


def test_linter_configuration_from_yaml(tmp_path, all_rule_classes):
    yaml_content = """
    fail_severity: ERROR
    disabled_rule_codes:
      - S102
      - S103
    """
    yaml_file = tmp_path / "config.yaml"
    with open(yaml_file, "w") as f:
        f.write(yaml_content)

    linter = PhoebusLinter.from_yaml(yaml_file)
    assert linter._fail_severity == SeverityLevel.ERROR
    assert len(linter._enabled_rules) == len(all_rule_classes) - 2
    assert all(
        rule_cls.rule_code not in ["S102", "S103"] for rule_cls in linter._enabled_rules
    )


@pytest.mark.parametrize(
    "num_warnings, num_errors, num_criticals, fail_sevr, expected",
    [
        (0, 0, 0, SeverityLevel.INFO, True),
        (1, 0, 0, SeverityLevel.INFO, False),
        (0, 0, 0, SeverityLevel.WARNING, True),
        (1, 0, 0, SeverityLevel.WARNING, False),
        (0, 1, 0, SeverityLevel.WARNING, False),
        (0, 0, 1, SeverityLevel.WARNING, False),
        (1, 1, 1, SeverityLevel.WARNING, False),
        (1, 0, 0, SeverityLevel.ERROR, True),
        (0, 1, 0, SeverityLevel.ERROR, False),
        (0, 0, 1, SeverityLevel.ERROR, False),
        (1, 1, 1, SeverityLevel.ERROR, False),
        (1, 0, 0, SeverityLevel.CRITICAL, True),
        (0, 1, 0, SeverityLevel.CRITICAL, True),
        (0, 0, 1, SeverityLevel.CRITICAL, False),
        (1, 1, 1, SeverityLevel.CRITICAL, False),
    ],
)
def test_did_linting_pass(
    tmp_path, num_warnings, num_errors, num_criticals, fail_sevr, expected
):
    linter = PhoebusLinter(fail_severity=fail_sevr)
    all_violations = []

    def _make_violation(severity, code):
        return RuleViolation(
            rule_name="TestRule",
            rule_code=code,
            rule_severity=severity,
            screen=Path("test_screen.bob"),
            details=f"Test {severity.name.lower()} violation",
        )

    for i in range(num_warnings):
        all_violations.append(_make_violation(SeverityLevel.WARNING, f"W{i + 1:03}"))
    for i in range(num_errors):
        all_violations.append(_make_violation(SeverityLevel.ERROR, f"E{i + 1:03}"))
    for i in range(num_criticals):
        all_violations.append(_make_violation(SeverityLevel.CRITICAL, f"C{i + 1:03}"))

    assert linter.did_linting_pass({tmp_path: all_violations}) == expected


def test_display_linting_report(capsys):
    linter = PhoebusLinter()
    violations = [
        RuleViolation(
            rule_name="TestRule1",
            rule_code="T001",
            rule_severity=SeverityLevel.WARNING,
            screen=Path("test_screen.bob"),
            details="Test warning violation",
        ),
        RuleViolation(
            rule_name="TestRule2",
            rule_code="T002",
            rule_severity=SeverityLevel.ERROR,
            screen=Path("test_screen.bob"),
            details="Test error violation",
        ),
    ]
    linter.display_linting_report({Path("test_screen.bob"): violations})
    captured = capsys.readouterr()
    assert "PhoebusLint scanned 1 screens,  1 with violations." in captured.out
    assert "# PhoebusLint Rule Violation Report" in captured.out
    assert (
        "[T001] TestRule1: Test warning violation (Screen: test_screen.bob)"
        in captured.out
    )
    assert (
        "[T002] TestRule2: Test error violation (Screen: test_screen.bob)"
        in captured.out
    )
    assert "Total Warnings: 1" in captured.out
    assert "Total Errors: 1" in captured.out
    assert "Found 2 total issues." in captured.out
