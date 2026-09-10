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

def _open_display_button(name: str, target: str) -> str:
    return (
        f'  <widget type="action_button" version="3.0.0">\n'
        f"    <name>{name}</name>\n"
        "    <actions>\n"
        '      <action type="open_display">\n'
        f"        <file>{target}</file>\n"
        "        <target>replace</target>\n"
        "      </action>\n"
        "    </actions>\n"
        "  </widget>\n"
    )


def test_no_violation_for_circular_transition_dependency(tmp_path):
    """Macros required within a navigation cycle are assumed supplied externally.

    ``main`` is a root screen that receives ``$(Q)`` from a launcher and opens
    ``more``; ``more`` does not reference ``Q`` itself but has a "back" button to
    ``main``. Checking ``more`` must not flag ``Q`` on the return transition,
    since the whole cycle shares the launcher-provided macro context.
    """
    main_bob = tmp_path / "main.bob"
    main_bob.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<display version="2.0.0">\n'
        "  <name>Main</name>\n"
        '  <widget type="label" version="2.0.0">\n'
        "    <name>Label</name>\n"
        "    <text>$(Q)</text>\n"
        "  </widget>\n"
        + _open_display_button("Open More", "more.bob")
        + "</display>\n"
    )

    more_bob = tmp_path / "more.bob"
    more_bob.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<display version="2.0.0">\n'
        "  <name>More</name>\n"
        + _open_display_button("Back To Main", "main.bob")
        + "</display>\n"
    )

    screen = Screen(f_name=str(more_bob))
    violations = UndefinedMacrosInScreenTransition.check(screen)
    assert len(violations) == 0


def test_violation_when_target_not_in_cycle(tmp_path):
    """A non-cyclic transition still flags macros the source cannot provide."""
    target_bob = tmp_path / "target.bob"
    target_bob.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<display version="2.0.0">\n'
        "  <name>Target</name>\n"
        '  <widget type="label" version="2.0.0">\n'
        "    <name>Label</name>\n"
        "    <text>$(Q)</text>\n"
        "  </widget>\n"
        "</display>\n"
    )

    source_bob = tmp_path / "source.bob"
    source_bob.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<display version="2.0.0">\n'
        "  <name>Source</name>\n"
        + _open_display_button("Open Target", "target.bob")
        + "</display>\n"
    )

    screen = Screen(f_name=str(source_bob))
    violations = UndefinedMacrosInScreenTransition.check(screen)
    assert len(violations) == 1
    assert "Q" in violations[0].details
