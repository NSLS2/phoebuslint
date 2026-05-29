import pytest
from phoebuslint.linter import NavigationStep, ScreenNavigationDAG
from pathlib import Path
from phoebusgen.v4 import Screen

@pytest.fixture
def nav_step_factory(tmp_path):
    def _factory(from_screen: str | Path, to_screen: str | Path, macros: dict[str, str] | None = None) -> NavigationStep:
        return NavigationStep(
            from_screen=tmp_path / from_screen,
            to_screen=tmp_path / to_screen,
            macros=macros or {},
        )
    return _factory


def test_navigation_step_equality(nav_step_factory):
    step1 = nav_step_factory("screen1.bob", "screen2.bob", {"MACRO1": "value1"})
    step2 = nav_step_factory("screen1.bob", "screen2.bob", {"MACRO1": "value1"})
    step3 = nav_step_factory("screen1.bob", "screen2.bob", {"MACRO1": "value2"})
    step4 = nav_step_factory("screen1.bob", "screen3.bob", {"MACRO1": "value1"})

    assert step1 == step2, "Steps with same from_screen, to_screen, and macros should be equal"
    assert step1 != step3, "Steps with different macros should not be equal"
    assert step1 != step4, "Steps with different to_screen should not be equal"


def test_screen_nav_dag_from_empty_screen(sample_empty_screen):
    # This test assumes that the sample_empty_screen has no linked screens
    dag = ScreenNavigationDAG.from_screen(sample_empty_screen)
    assert isinstance(dag, ScreenNavigationDAG), "Should return a ScreenNavigationDAG instance"
    assert len(dag.graph) == 0, "Empty screen should have no navigation edges"



def test_screen_nav_dag_with_linked_screens():
    dag = ScreenNavigationDAG.from_screen(Screen(f_name="examples/Example_TOP1.bob"))
    assert isinstance(dag, ScreenNavigationDAG), "Should return a ScreenNavigationDAG instance"
    assert len(dag.graph) > 0, "Should have navigation edges for linked screens"
    assert dag.graph.get(Path("examples/Example_TOP1.bob")) is not None, "Graph should contain the root screen"
    assert dag.graph.get(Path("examples/Example_TOP1.bob")) == [NavigationStep(from_screen=Path("examples/Example_TOP1.bob"), to_screen=Path("examples/Nested/Nested1.bob"), macros={"A": "1", "B": "2"})], "Graph should contain the correct navigation step from TOP1 to Nested1"