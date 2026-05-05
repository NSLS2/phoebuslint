from xml.etree import ElementTree as ET

from phoebusgen.v4 import Screen
from phoebusgen.v4.widgets import Label
from phoebuslint.rules import (
    DefaultTitleSet,
    EmptyScreen,
    ExtraTagsInDisplay,
    ScreenHeightOrWidthZeroOrNegative,
    TitleEmptyOrNotSet,
    TopLevelTagNotDisplay,
)


def test_root_tag_not_display(sample_empty_screen: Screen):
    sample_empty_screen.root.tag = "notDisplay"

    violations = TopLevelTagNotDisplay.check(sample_empty_screen)
    assert len(violations) == 1
    assert violations[0].rule_code == TopLevelTagNotDisplay.rule_code
    assert violations[0].details.startswith("Root tag is not <display>.")


def test_extra_tags_in_display_rule(sample_empty_screen: Screen):
    ET.SubElement(sample_empty_screen.root, "unexpectedTag")

    violations = ExtraTagsInDisplay.check(sample_empty_screen)
    assert len(violations) == 1
    assert violations[0].rule_code == ExtraTagsInDisplay.rule_code
    assert violations[0].details.startswith("Unexpected tag found in <display>.")


def test_title_empty_or_not_set(sample_empty_screen: Screen):
    if sample_empty_screen.name.strip() == "":
        assert len(TitleEmptyOrNotSet.check(sample_empty_screen)) > 0

    sample_empty_screen.name = "Main Screen"
    assert len(TitleEmptyOrNotSet.check(sample_empty_screen)) == 0


def test_default_title_set_rule(sample_empty_screen: Screen):
    if sample_empty_screen.name == "Display":
        assert len(DefaultTitleSet.check(sample_empty_screen)) > 0

    sample_empty_screen.name = "Control Panel"
    assert len(DefaultTitleSet.check(sample_empty_screen)) == 0


def test_empty_screen_rule(sample_empty_screen: Screen):
    violations = EmptyScreen.check(sample_empty_screen)
    assert len(violations) == 1
    assert violations[0].rule_code == EmptyScreen.rule_code
    assert violations[0].details == "Screen is empty (has no widgets)."

    sample_empty_screen.add_widget(Label("label1", "test", 0, 0, 100, 30))
    assert len(EmptyScreen.check(sample_empty_screen)) == 0


def test_screen_height_or_width_zero_or_negative(sample_empty_screen: Screen):

    sample_empty_screen.width = 0
    violations = ScreenHeightOrWidthZeroOrNegative.check(sample_empty_screen)
    assert len(violations) == 1
    assert violations[0].rule_code == ScreenHeightOrWidthZeroOrNegative.rule_code
    assert "width" in violations[0].details

    sample_empty_screen.width = 800
    sample_empty_screen.height = -100
    violations = ScreenHeightOrWidthZeroOrNegative.check(sample_empty_screen)
    assert len(violations) == 1
    assert violations[0].rule_code == ScreenHeightOrWidthZeroOrNegative.rule_code
    assert "height" in violations[0].details

    sample_empty_screen.height = 600
    assert len(ScreenHeightOrWidthZeroOrNegative.check(sample_empty_screen)) == 0
