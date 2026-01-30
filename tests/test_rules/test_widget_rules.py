from phoebusgen import Screen
from phoebusgen.widgets import Label
from phoebuslint.rules.widget import WidgetOutOfBounds


def test_widget_out_of_bounds_rule(sample_empty_screen: Screen):
    sample_empty_screen.width = 400
    sample_empty_screen.height = 300

    label_in_bounds = Label("label1", "In Bounds", 50, 50, 100, 30)
    sample_empty_screen.add_widget(label_in_bounds)
    assert WidgetOutOfBounds.check(sample_empty_screen) is None

    label_out_of_bounds = Label("label2", "Out of Bounds", 350, 280, 100, 30)
    sample_empty_screen.add_widget(label_out_of_bounds)
    assert WidgetOutOfBounds.check(sample_empty_screen) is not None
