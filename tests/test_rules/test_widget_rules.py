from phoebusgen.v4 import Screen
from phoebusgen.v4.widgets import Label
from phoebuslint.rules.widget import (
    DuplicateWidgetNames,
    WidgetHeightOrWidthZeroOrNegative,
    WidgetOutOfBounds,
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


def test_duplicate_widget_names_check(sample_empty_screen: Screen):
    """Test that duplicate widget names are detected."""
    l1 = Label("label1", "A", 0, 0, 50, 20)
    l2 = Label("label2", "B", 0, 20, 50, 20)
    sample_empty_screen.add_widget([l1, l2])
    assert len(DuplicateWidgetNames.check(sample_empty_screen)) == 0

    l3 = Label("label1", "C", 0, 40, 50, 20)
    sample_empty_screen.add_widget(l3)
    violations = DuplicateWidgetNames.check(sample_empty_screen)
    assert len(violations) == 1
    assert violations[0].widget.name == "label1"


def test_duplicate_widget_names_fix_two_duplicates(sample_empty_screen: Screen):
    """Test that fixing two widgets with the same name produces unique names."""
    l1 = Label("dup", "A", 0, 0, 50, 20)
    l2 = Label("dup", "B", 0, 20, 50, 20)
    sample_empty_screen.add_widget([l1, l2])

    DuplicateWidgetNames.fix(sample_empty_screen)
    names = [w.name for w in sample_empty_screen.get_all_widgets()]
    assert len(names) == len(set(names)), f"Names not unique after fix: {names}"


def test_duplicate_widget_names_fix_many_duplicates(sample_empty_screen: Screen):
    """Test that fixing many widgets with the same name all get unique names."""
    widgets = [Label("same", f"text{i}", 0, i * 20, 50, 20) for i in range(10)]
    sample_empty_screen.add_widget(widgets)

    DuplicateWidgetNames.fix(sample_empty_screen)
    names = [w.name for w in sample_empty_screen.get_all_widgets()]
    assert len(names) == len(set(names)), f"Names not unique after fix: {names}"


def test_duplicate_widget_names_fix_no_false_collisions(sample_empty_screen: Screen):
    """Test that the fix doesn't create new collisions with existing widget names."""
    # "dup" appears twice, and "dup_1" already exists
    l1 = Label("dup", "A", 0, 0, 50, 20)
    l2 = Label("dup_1", "B", 0, 20, 50, 20)
    l3 = Label("dup", "C", 0, 40, 50, 20)
    sample_empty_screen.add_widget([l1, l2, l3])

    DuplicateWidgetNames.fix(sample_empty_screen)
    names = [w.name for w in sample_empty_screen.get_all_widgets()]
    assert len(names) == len(set(names)), f"Names not unique after fix: {names}"
