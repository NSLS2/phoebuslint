import pytest
from phoebusgen.v4 import Screen
from phoebuslint.linter import get_all_rules


@pytest.fixture
def all_rule_classes():
    """Fixture to get all LintRule subclasses."""
    return set(get_all_rules())


@pytest.fixture
def sample_empty_screen(tmp_path) -> Screen:
    screen = Screen(f_name=str(tmp_path / "test_screen.bob"))
    screen.width = 800
    screen.height = 600
    return screen


@pytest.fixture
def screen_given_xml_factory(tmp_path):
    def _factory(xml_content: str) -> Screen:
        bob_file = tmp_path / "test_screen.bob"
        with open(bob_file, "w") as f:
            f.write(xml_content)
        return Screen(f_name=str(bob_file))

    return _factory
