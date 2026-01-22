from phoebusgen import Screen
from phoebusgen.widgets import Label
from phoebuslint.rules.screen import EmptyScreen, TitleEmptyOrNotSet, DefaultTitleSet, WidgetOutOfBounds
import pytest
import os

pytestmark = pytest.mark.parametrize("sample_empty_screen", [Screen(), Screen(f_name=f"{__file__}/../screen_test_cases/empty_screen_default_name.bob")])

def test_empty_screen_rule(sample_empty_screen: Screen):
    assert EmptyScreen.check(sample_empty_screen) is True

    sample_empty_screen.add_widget(Label("label1", "test", 0, 0, 100, 30))
    assert EmptyScreen.check(sample_empty_screen) is False

def test_title_empty_or_not_set(sample_empty_screen: Screen):
    if sample_empty_screen.name.strip() == "":
        assert TitleEmptyOrNotSet.check(sample_empty_screen) is True

    sample_empty_screen.name = "Main Screen"
    assert TitleEmptyOrNotSet.check(sample_empty_screen) is False

def test_default_title_set_rule(sample_empty_screen: Screen):
    if sample_empty_screen.name == "Display":
        assert DefaultTitleSet.check(sample_empty_screen) is True

    sample_empty_screen.name = "Control Panel"
    assert DefaultTitleSet.check(sample_empty_screen) is False

def test_widget_out_of_bounds_rule(sample_empty_screen: Screen):
    sample_empty_screen.width = 400
    sample_empty_screen.height = 300

    label_in_bounds = Label("label1", "In Bounds", 50, 50, 100, 30)
    sample_empty_screen.add_widget(label_in_bounds)
    assert WidgetOutOfBounds.check(sample_empty_screen) is False

    label_out_of_bounds = Label("label2", "Out of Bounds", 350, 280, 100, 30)
    sample_empty_screen.add_widget(label_out_of_bounds)
    assert WidgetOutOfBounds.check(sample_empty_screen) is True
