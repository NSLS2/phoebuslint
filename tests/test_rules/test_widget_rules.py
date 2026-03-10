from phoebusgen.v4 import Screen
from phoebusgen.v4.widgets import Label
from phoebuslint.rules.widget import (
    WidgetHeightOrWidthZeroOrNegative,
    WidgetOutOfBounds,
)


def test_widget_height_or_width_zero_or_negative_rule(sample_empty_screen: Screen):
    label_valid = Label("label1", "Valid", 10, 10, 100, 30)
    sample_empty_screen.add_widget(label_valid)
    assert WidgetHeightOrWidthZeroOrNegative.check(sample_empty_screen) is None

    label_zero_width = Label("label2", "Zero Width", 20, 50, 0, 30)
    sample_empty_screen.add_widget(label_zero_width)
    assert WidgetHeightOrWidthZeroOrNegative.check(sample_empty_screen) is not None

    label_negative_height = Label("label3", "Negative Height", 50, 100, 100, -10)
    sample_empty_screen.add_widget(label_negative_height)
    assert WidgetHeightOrWidthZeroOrNegative.check(sample_empty_screen) is not None


def test_widget_out_of_bounds_rule(sample_empty_screen: Screen):
    sample_empty_screen.width = 400
    sample_empty_screen.height = 300

    label_in_bounds = Label("label1", "In Bounds", 50, 50, 100, 30)
    sample_empty_screen.add_widget(label_in_bounds)
    assert WidgetOutOfBounds.check(sample_empty_screen) is None

    label_out_of_bounds = Label("label2", "Out of Bounds", 350, 280, 100, 30)
    sample_empty_screen.add_widget(label_out_of_bounds)
    assert WidgetOutOfBounds.check(sample_empty_screen) is not None
