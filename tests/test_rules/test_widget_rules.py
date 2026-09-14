import logging

from phoebusgen.v4 import Screen
from phoebusgen.v4.widgets import Label
from phoebuslint.linter import PhoebusLinter
from phoebuslint.rules.paths import (
    DisplayFileIsOpiFile,
    DisplayFilePathDoesNotExist,
    DisplayFilePathNotBobOrOpiFile,
)
from phoebuslint.rules.widget import (
    DuplicateWidgetNames,
    WidgetHasInvalidDecimalFontSize,
    WidgetHeightOrWidthZeroOrNegative,
    WidgetOutOfBounds,
)


def _embedded_display_source(file: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<display version="2.0.0">\n'
        "  <name>Source</name>\n"
        '  <widget type="embedded" version="2.0.0">\n'
        "    <name>Embedded Display</name>\n"
        f"    <file>{file}</file>\n"
        "  </widget>\n"
        "</display>\n"
    )


def _open_display_source(target: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<display version="2.0.0">\n'
        "  <name>Source</name>\n"
        '  <widget type="action_button" version="3.0.0">\n'
        "    <name>Action Button</name>\n"
        "    <actions>\n"
        '      <action type="open_display">\n'
        f"        <file>{target}</file>\n"
        "        <target>replace</target>\n"
        "      </action>\n"
        "    </actions>\n"
        "  </widget>\n"
        "</display>\n"
    )


def _label_font_xml(size: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<display version="2.0.0">\n'
        "  <name>T</name>\n"
        "  <width>400</width>\n"
        "  <height>300</height>\n"
        '  <widget type="label" version="2.0.0">\n'
        "    <name>l1</name>\n"
        "    <x>0</x><y>0</y><width>100</width><height>20</height>\n"
        "    <text>hi</text>\n"
        f"    <font>\n"
        f'      <font family="Liberation Sans" size="{size}" style="REGULAR" />\n'
        f"    </font>\n"
        "  </widget>\n"
        "</display>\n"
    )


_OPI_ACTION_XML = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    "<display>\n"
    "  <name>Test</name>\n"
    "  <width>800</width>\n"
    "  <height>600</height>\n"
    '  <widget type="action_button">\n'
    "    <name>Action Button</name>\n"
    "    <actions>\n"
    '      <action type="open_display">\n'
    "        <file>target.opi</file>\n"
    "        <target>replace</target>\n"
    "      </action>\n"
    "    </actions>\n"
    "    <x>0</x><y>0</y><width>100</width><height>30</height>\n"
    "  </widget>\n"
    "</display>\n"
)


def test_widget_height_or_width_zero_or_negative_rule(sample_empty_screen: Screen):
    label_valid = Label("label1", "Valid", 10, 10, 100, 30)
    sample_empty_screen.add_widget(label_valid)
    assert len(WidgetHeightOrWidthZeroOrNegative.check(sample_empty_screen)) == 0

    label_zero_width = Label("label2", "Zero Width", 20, 50, 0, 30)
    sample_empty_screen.add_widget(label_zero_width)
    assert len(WidgetHeightOrWidthZeroOrNegative.check(sample_empty_screen)) > 0

    label_negative_height = Label("label3", "Negative Height", 50, 100, 100, -10)
    sample_empty_screen.add_widget(label_negative_height)
    assert len(WidgetHeightOrWidthZeroOrNegative.check(sample_empty_screen)) > 0


def test_widget_out_of_bounds_rule(sample_empty_screen: Screen):
    sample_empty_screen.width = 400
    sample_empty_screen.height = 300

    label_in_bounds = Label("label1", "In Bounds", 50, 50, 100, 30)
    sample_empty_screen.add_widget(label_in_bounds)
    assert len(WidgetOutOfBounds.check(sample_empty_screen)) == 0

    label_out_of_bounds = Label("label2", "Out of Bounds", 350, 280, 100, 30)
    sample_empty_screen.add_widget(label_out_of_bounds)
    assert len(WidgetOutOfBounds.check(sample_empty_screen)) > 0


def test_widget_out_of_bounds_fix_grows_screen(sample_empty_screen: Screen):
    """A widget past the right/bottom edge is fixed by growing the screen."""
    sample_empty_screen.width = 400
    sample_empty_screen.height = 300
    label = Label("label1", "Too wide", 350, 280, 100, 30)
    sample_empty_screen.add_widget(label)

    violations = WidgetOutOfBounds.check(sample_empty_screen)
    assert len(violations) == 1
    assert WidgetOutOfBounds.fix(violations[0]) is True
    assert len(WidgetOutOfBounds.check(sample_empty_screen)) == 0


def test_widget_out_of_bounds_fix_clamps_negative_position(sample_empty_screen: Screen):
    """A widget with a negative position is clamped back into bounds."""
    sample_empty_screen.width = 412
    sample_empty_screen.height = 118
    label = Label("label1", "Off the top", 40, -2, 300, 22)
    sample_empty_screen.add_widget(label)

    violations = WidgetOutOfBounds.check(sample_empty_screen)
    assert len(violations) == 1
    assert WidgetOutOfBounds.fix(violations[0]) is True
    assert label.x == 40
    assert label.y == 0
    assert len(WidgetOutOfBounds.check(sample_empty_screen)) == 0


def test_duplicate_widget_names_check(screen_given_xml_factory):
    """Test that duplicate widget names are detected."""
    # Use XML directly because phoebusgen auto-deduplicates names on add_widget
    screen = screen_given_xml_factory(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<display>\n"
        "  <name>Test</name>\n"
        "  <width>800</width>\n"
        "  <height>600</height>\n"
        '  <widget type="label">\n'
        "    <name>label1</name>\n"
        "    <text>A</text>\n"
        "    <x>0</x><y>0</y><width>50</width><height>20</height>\n"
        "  </widget>\n"
        '  <widget type="label">\n'
        "    <name>label2</name>\n"
        "    <text>B</text>\n"
        "    <x>0</x><y>20</y><width>50</width><height>20</height>\n"
        "  </widget>\n"
        '  <widget type="label">\n'
        "    <name>label1</name>\n"
        "    <text>C</text>\n"
        "    <x>0</x><y>40</y><width>50</width><height>20</height>\n"
        "  </widget>\n"
        "</display>\n"
    )
    violations = DuplicateWidgetNames.check(screen)
    assert len(violations) == 1
    assert violations[0].widget is not None
    assert violations[0].widget.name == "label1"


def test_duplicate_widget_names_fix_two_duplicates(sample_empty_screen: Screen):
    """Test that fixing two widgets with the same name produces unique names."""
    l1 = Label("dup", "A", 0, 0, 50, 20)
    l2 = Label("dup", "B", 0, 20, 50, 20)
    sample_empty_screen.add_widget([l1, l2])

    violations = DuplicateWidgetNames.check(sample_empty_screen)
    for v in violations:
        DuplicateWidgetNames.fix(v)
    names = [w.name for w in sample_empty_screen.get_all_widgets()]
    assert len(names) == len(set(names)), f"Names not unique after fix: {names}"


def test_duplicate_widget_names_fix_many_duplicates(sample_empty_screen: Screen):
    """Test that fixing many widgets with the same name all get unique names."""
    widgets = [Label("same", f"text{i}", 0, i * 20, 50, 20) for i in range(10)]
    sample_empty_screen.add_widget(widgets)

    violations = DuplicateWidgetNames.check(sample_empty_screen)
    for v in violations:
        DuplicateWidgetNames.fix(v)
    names = [w.name for w in sample_empty_screen.get_all_widgets()]
    assert len(names) == len(set(names)), f"Names not unique after fix: {names}"


def test_duplicate_widget_names_fix_no_false_collisions(sample_empty_screen: Screen):
    """Test that the fix doesn't create new collisions with existing widget names."""
    # "dup" appears twice, and "dup_1" already exists
    l1 = Label("dup", "A", 0, 0, 50, 20)
    l2 = Label("dup_1", "B", 0, 20, 50, 20)
    l3 = Label("dup", "C", 0, 40, 50, 20)
    sample_empty_screen.add_widget([l1, l2, l3])

    violations = DuplicateWidgetNames.check(sample_empty_screen)
    for v in violations:
        DuplicateWidgetNames.fix(v)
    names = [w.name for w in sample_empty_screen.get_all_widgets()]
    assert len(names) == len(set(names)), f"Names not unique after fix: {names}"


def test_open_display_action_opi_not_fixable_without_bob(
    tmp_path, screen_given_xml_factory
):
    """Violation is reported but not fixable when no matching .bob file exists."""
    screen = screen_given_xml_factory(_OPI_ACTION_XML)

    linter = PhoebusLinter()
    linter.build_bob_file_tree(tmp_path)

    violations = DisplayFileIsOpiFile.check(screen)
    assert len(violations) == 1
    assert violations[0].fixable is False


def test_open_display_action_opi_fixable_switches_to_bob(
    tmp_path, screen_given_xml_factory
):
    """When a matching .bob file exists, the fix repoints the action to it."""
    (tmp_path / "target.bob").write_text("")
    screen = screen_given_xml_factory(_OPI_ACTION_XML)

    linter = PhoebusLinter()
    linter.build_bob_file_tree(tmp_path)

    violations = DisplayFileIsOpiFile.check(screen)
    assert len(violations) == 1
    assert violations[0].fixable is True

    assert DisplayFileIsOpiFile.fix(violations[0]) is True

    action = screen.get_widgets()[0].actions[0]
    assert str(action.file) == "target.bob"
    assert len(DisplayFileIsOpiFile.check(screen)) == 0


def test_invalid_decimal_font_size_detected(screen_given_xml_factory):
    """A non-integral font size is flagged as fixable."""
    screen = screen_given_xml_factory(_label_font_xml("14.5"))

    violations = WidgetHasInvalidDecimalFontSize.check(screen)
    assert len(violations) == 1
    assert violations[0].fixable is True


def test_integral_font_size_not_flagged(screen_given_xml_factory):
    """An integer font size produces no violation."""
    screen = screen_given_xml_factory(_label_font_xml("14"))

    assert len(WidgetHasInvalidDecimalFontSize.check(screen)) == 0


def test_invalid_decimal_font_size_fix_rounds_to_int(screen_given_xml_factory):
    """The fix rounds the font size half up and clears the violation."""
    screen = screen_given_xml_factory(_label_font_xml("14.5"))

    violations = WidgetHasInvalidDecimalFontSize.check(screen)
    assert len(violations) == 1
    assert WidgetHasInvalidDecimalFontSize.fix(violations[0]) is True

    widget = screen.get_widgets()[0]
    assert widget.font.size == 15
    assert len(WidgetHasInvalidDecimalFontSize.check(screen)) == 0


def test_open_display_missing_path_fixable_only_with_match(tmp_path):
    """Violation is fixable only when a same-named .bob exists in the file tree."""
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "target.bob").write_text("")

    source_bob = tmp_path / "source.bob"
    source_bob.write_text(_open_display_source("target.bob"))

    linter = PhoebusLinter()
    linter.build_bob_file_tree(tmp_path)
    screen = Screen(f_name=str(source_bob))

    violations = DisplayFilePathDoesNotExist.check(screen)
    assert len(violations) == 1
    assert violations[0].fixable is True
    assert DisplayFilePathDoesNotExist.fix(violations[0]) is True
    assert len(DisplayFilePathDoesNotExist.check(screen)) == 0


def test_open_display_missing_path_not_fixable_without_match(tmp_path, caplog):
    """Violation is not fixable and fix logs a warning when no match exists."""
    source_bob = tmp_path / "source.bob"
    source_bob.write_text(_open_display_source("missing.bob"))

    linter = PhoebusLinter()
    linter.build_bob_file_tree(tmp_path)
    screen = Screen(f_name=str(source_bob))

    violations = DisplayFilePathDoesNotExist.check(screen)
    assert len(violations) == 1
    assert violations[0].fixable is False

    # The phoebuslint logger does not propagate, so attach caplog's handler to it.
    phoebus_logger = logging.getLogger("phoebuslint")
    phoebus_logger.addHandler(caplog.handler)
    try:
        assert DisplayFilePathDoesNotExist.fix(violations[0]) is False
    finally:
        phoebus_logger.removeHandler(caplog.handler)
    assert any("missing.bob" in record.message for record in caplog.records)


def test_embedded_display_missing_path_fixable_only_with_match(tmp_path):
    """EmbeddedDisplay violation is fixable only when a same-named .bob exists."""
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "target.bob").write_text("")

    source_bob = tmp_path / "source.bob"
    source_bob.write_text(_embedded_display_source("target.bob"))

    linter = PhoebusLinter()
    linter.build_bob_file_tree(tmp_path)
    screen = Screen(f_name=str(source_bob))

    violations = DisplayFilePathDoesNotExist.check(screen)
    assert len(violations) == 1
    assert violations[0].fixable is True
    assert DisplayFilePathDoesNotExist.fix(violations[0]) is True
    assert len(DisplayFilePathDoesNotExist.check(screen)) == 0


def test_embedded_display_missing_path_not_fixable_without_match(tmp_path):
    """EmbeddedDisplay violation is not fixable when no matching .bob exists."""
    source_bob = tmp_path / "source.bob"
    source_bob.write_text(_embedded_display_source("missing.bob"))

    linter = PhoebusLinter()
    linter.build_bob_file_tree(tmp_path)
    screen = Screen(f_name=str(source_bob))

    violations = DisplayFilePathDoesNotExist.check(screen)
    assert len(violations) == 1
    assert violations[0].fixable is False
    assert DisplayFilePathDoesNotExist.fix(violations[0]) is False


def test_display_path_not_bob_or_opi_flags_embedded(tmp_path):
    """An embedded display pointing to a non-bob/opi file is flagged."""
    source_bob = tmp_path / "source.bob"
    source_bob.write_text(_embedded_display_source("target.txt"))
    screen = Screen(f_name=str(source_bob))

    violations = DisplayFilePathNotBobOrOpiFile.check(screen)
    assert len(violations) == 1
    assert "target.txt" in violations[0].details
    assert violations[0].rule_code == "P103"


def test_display_path_not_bob_or_opi_flags_open_display_action(tmp_path):
    """An open-display action pointing to a non-bob/opi file is flagged."""
    source_bob = tmp_path / "source.bob"
    source_bob.write_text(_open_display_source("target.txt"))
    screen = Screen(f_name=str(source_bob))

    violations = DisplayFilePathNotBobOrOpiFile.check(screen)
    assert len(violations) == 1
    assert "target.txt" in violations[0].details


def test_display_path_bob_and_opi_not_flagged(tmp_path):
    """Valid .bob and .opi display paths produce no violation."""
    bob_source = tmp_path / "bob_source.bob"
    bob_source.write_text(_open_display_source("target.bob"))
    opi_source = tmp_path / "opi_source.bob"
    opi_source.write_text(_embedded_display_source("target.opi"))

    assert (
        len(DisplayFilePathNotBobOrOpiFile.check(Screen(f_name=str(bob_source)))) == 0
    )
    assert (
        len(DisplayFilePathNotBobOrOpiFile.check(Screen(f_name=str(opi_source)))) == 0
    )
