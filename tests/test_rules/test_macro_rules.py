from phoebusgen.v4 import Screen
from phoebuslint.rules.macros import UndefinedMacrosInScreenTransition


def test_no_violation_when_all_macros_passed(tmp_path):
    """Transition passes all macros required by target - no violation."""
    target_bob = tmp_path / "target.bob"
    target_bob.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<display version="2.0.0">\n'
        "  <name>Target</name>\n"
        '  <widget type="label" version="2.0.0">\n'
        "    <name>Label</name>\n"
        "    <text>$(X)$(Y)</text>\n"
        "  </widget>\n"
        "</display>\n"
    )

    source_bob = tmp_path / "source.bob"
    source_bob.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<display version="2.0.0">\n'
        "  <name>Source</name>\n"
        '  <widget type="embedded" version="2.0.0">\n'
        "    <name>Embedded Display</name>\n"
        "    <macros>\n"
        "      <X>1</X>\n"
        "      <Y>2</Y>\n"
        "    </macros>\n"
        "    <file>target.bob</file>\n"
        "  </widget>\n"
        "</display>\n"
    )

    screen = Screen(f_name=str(source_bob))
    violations = UndefinedMacrosInScreenTransition.check(screen)
    assert len(violations) == 0


def test_violation_when_macros_missing(tmp_path):
    """Transition does not pass all macros required by target - violation."""
    target_bob = tmp_path / "target.bob"
    target_bob.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<display version="2.0.0">\n'
        "  <name>Target</name>\n"
        '  <widget type="label" version="2.0.0">\n'
        "    <name>Label</name>\n"
        "    <text>$(X)$(Y)$(Z)</text>\n"
        "  </widget>\n"
        "</display>\n"
    )

    source_bob = tmp_path / "source.bob"
    source_bob.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<display version="2.0.0">\n'
        "  <name>Source</name>\n"
        '  <widget type="embedded" version="2.0.0">\n'
        "    <name>Embedded Display</name>\n"
        "    <macros>\n"
        "      <X>1</X>\n"
        "    </macros>\n"
        "    <file>target.bob</file>\n"
        "  </widget>\n"
        "</display>\n"
    )

    screen = Screen(f_name=str(source_bob))
    violations = UndefinedMacrosInScreenTransition.check(screen)
    assert len(violations) == 1
    assert "Y" in violations[0].details
    assert "Z" in violations[0].details
    assert violations[0].rule_code == "M101"


def test_source_macros_count_as_available(tmp_path):
    """Macros used by the source screen are considered available for the target."""
    target_bob = tmp_path / "target.bob"
    target_bob.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<display version="2.0.0">\n'
        "  <name>Target</name>\n"
        '  <widget type="label" version="2.0.0">\n'
        "    <name>Label</name>\n"
        "    <text>$(P)$(R)</text>\n"
        "  </widget>\n"
        "</display>\n"
    )

    # Source uses macro P itself, and passes R to target
    source_bob = tmp_path / "source.bob"
    source_bob.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<display version="2.0.0">\n'
        "  <name>Source</name>\n"
        '  <widget type="label" version="2.0.0">\n'
        "    <name>SourceLabel</name>\n"
        "    <text>$(P)</text>\n"
        "  </widget>\n"
        '  <widget type="embedded" version="2.0.0">\n'
        "    <name>Embedded Display</name>\n"
        "    <macros>\n"
        "      <R>val</R>\n"
        "    </macros>\n"
        "    <file>target.bob</file>\n"
        "  </widget>\n"
        "</display>\n"
    )

    screen = Screen(f_name=str(source_bob))
    violations = UndefinedMacrosInScreenTransition.check(screen)
    assert len(violations) == 0


def test_no_violation_when_target_has_no_macros(tmp_path):
    """No violation when target screen does not use any macros."""
    target_bob = tmp_path / "target.bob"
    target_bob.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<display version="2.0.0">\n'
        "  <name>Target</name>\n"
        '  <widget type="label" version="2.0.0">\n'
        "    <name>Label</name>\n"
        "    <text>Hello</text>\n"
        "  </widget>\n"
        "</display>\n"
    )

    source_bob = tmp_path / "source.bob"
    source_bob.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<display version="2.0.0">\n'
        "  <name>Source</name>\n"
        '  <widget type="embedded" version="2.0.0">\n'
        "    <name>Embedded Display</name>\n"
        "    <file>target.bob</file>\n"
        "  </widget>\n"
        "</display>\n"
    )

    screen = Screen(f_name=str(source_bob))
    violations = UndefinedMacrosInScreenTransition.check(screen)
    assert len(violations) == 0


def test_no_violation_when_target_does_not_exist(tmp_path):
    """No violation (gracefully skip) when target file does not exist."""
    source_bob = tmp_path / "source.bob"
    source_bob.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<display version="2.0.0">\n'
        "  <name>Source</name>\n"
        '  <widget type="embedded" version="2.0.0">\n'
        "    <name>Embedded Display</name>\n"
        "    <file>nonexistent.bob</file>\n"
        "  </widget>\n"
        "</display>\n"
    )

    screen = Screen(f_name=str(source_bob))
    violations = UndefinedMacrosInScreenTransition.check(screen)
    assert len(violations) == 0
