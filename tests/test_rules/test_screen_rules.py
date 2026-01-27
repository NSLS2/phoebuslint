from phoebusgen import Screen
from phoebusgen.widgets import Label
from phoebuslint.rules import EmptyScreen, TitleEmptyOrNotSet, DefaultTitleSet, ExtraTagsInDisplay, TopLevelTagNotDisplay
import pytest
from xml.etree import ElementTree as ET
import os



def test_root_tag_not_display(sample_empty_screen: Screen):

    sample_empty_screen.root.tag = "notDisplay"

    violations = TopLevelTagNotDisplay.check(sample_empty_screen)
    assert violations is not None
    assert len(violations) == 1
    assert violations[0].rule_code == TopLevelTagNotDisplay.rule_code
    assert violations[0].details.startswith("Root tag is not <display>.")

def test_extra_tags_in_display_rule(sample_empty_screen: Screen):
    ET.SubElement(sample_empty_screen.root, "unexpectedTag")
    
    violations = ExtraTagsInDisplay.check(sample_empty_screen)
    assert violations is not None
    assert len(violations) == 1
    assert violations[0].rule_code == ExtraTagsInDisplay.rule_code
    assert violations[0].details.startswith("Unexpected tag found in <display>.")


def test_empty_screen_rule(sample_empty_screen: Screen):
    violations = EmptyScreen.check(sample_empty_screen)
    assert violations is not None
    assert len(violations) == 1
    assert violations[0].rule_code == EmptyScreen.rule_code
    assert violations[0].details == "Screen is empty (has no widgets)."

    sample_empty_screen.add_widget(Label("label1", "test", 0, 0, 100, 30))
    assert EmptyScreen.check(sample_empty_screen) is None

def test_title_empty_or_not_set(sample_empty_screen: Screen):
    if sample_empty_screen.name.strip() == "":
        assert TitleEmptyOrNotSet.check(sample_empty_screen) is not None

    sample_empty_screen.name = "Main Screen"
    assert TitleEmptyOrNotSet.check(sample_empty_screen) is None

def test_default_title_set_rule(sample_empty_screen: Screen):
    if sample_empty_screen.name == "Display":
        assert DefaultTitleSet.check(sample_empty_screen) is not None

    sample_empty_screen.name = "Control Panel"
    assert DefaultTitleSet.check(sample_empty_screen) is None

