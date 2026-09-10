from phoebusgen.v4 import Screen
from phoebusgen.v4.widgets import Label
from phoebuslint.rules.widget import (
    DuplicateWidgetNames,
    OpenDisplayActionPathIsOpiFile,
    WidgetHeightOrWidthZeroOrNegative,
    WidgetOutOfBounds,
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
    """Violation is reported but not fixable when no sibling .bob file exists."""
    screen = screen_given_xml_factory(_OPI_ACTION_XML)

    violations = OpenDisplayActionPathIsOpiFile.check(screen)
    assert len(violations) == 1
    assert violations[0].fixable is False


def test_open_display_action_opi_fixable_switches_to_bob(
    tmp_path, screen_given_xml_factory
):
    """When a sibling .bob file exists, the fix repoints the action to it."""
    (tmp_path / "target.bob").write_text("")
    screen = screen_given_xml_factory(_OPI_ACTION_XML)

    violations = OpenDisplayActionPathIsOpiFile.check(screen)
    assert len(violations) == 1
    assert violations[0].fixable is True

    assert OpenDisplayActionPathIsOpiFile.fix(violations[0]) is True

    action = screen.get_widgets()[0].actions[0]
    assert str(action.file) == "target.bob"
    assert len(OpenDisplayActionPathIsOpiFile.check(screen)) == 0

