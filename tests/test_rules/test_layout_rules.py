from phoebusgen.v4 import Screen
from phoebusgen.v4.widgets import (
    ByteMonitor,
    Group,
    Label,
    Tab,
    Tabs,
    TextEntry,
    TextUpdate,
)

from phoebuslint.rules.layout import (
    ByteMonitorLabelsMisaligned,
    InconsistentColumnLayout,
    LabelControlMisaligned,
    SetpointReadbackMisaligned,
)


def _screen(tmp_path) -> Screen:
    screen = Screen(f_name=str(tmp_path / "screen.bob"))
    screen.width = 800
    screen.height = 600
    return screen


def _group_with(*widgets) -> Group:
    group = Group("group", 0, 0, 400, 400)
    for widget in widgets:
        group.add_widget(widget)
    return group


def _tabs_with(*widgets) -> Tabs:
    tabs = Tabs("tabs", 0, 0, 400, 400)
    tab = Tab("Tab1")
    for widget in widgets:
        tab.add_widget(widget)
    tabs.tabs = [tab]
    return tabs


# ---------------------------------------------------------------------------
# LabelControlMisaligned (W121)
# ---------------------------------------------------------------------------
def test_label_control_aligned_same_row_not_flagged(tmp_path):
    screen = _screen(tmp_path)
    screen.add_widget(Label("l", "Name", 10, 100, 50, 20))
    screen.add_widget(TextUpdate("t", "pv", 70, 100, 80, 20))
    assert LabelControlMisaligned.check(screen) == []


def test_label_control_aligned_same_column_not_flagged(tmp_path):
    screen = _screen(tmp_path)
    screen.add_widget(Label("l", "Name", 10, 100, 60, 20))
    screen.add_widget(TextUpdate("t", "pv", 10, 130, 60, 20))
    assert LabelControlMisaligned.check(screen) == []


def test_label_control_misaligned_flagged_and_fixable(tmp_path):
    screen = _screen(tmp_path)
    screen.add_widget(Label("l", "Name", 10, 100, 50, 40))
    control = TextUpdate("t", "pv", 70, 120, 80, 40)
    screen.add_widget(control)

    violations = LabelControlMisaligned.check(screen)
    assert len(violations) == 1
    assert violations[0].fixable is True

    assert LabelControlMisaligned.fix(violations[0]) is True
    assert control.y == 100
    assert LabelControlMisaligned.check(screen) == []


def test_label_control_misaligned_within_group(tmp_path):
    screen = _screen(tmp_path)
    screen.add_widget(
        _group_with(
            Label("l", "Name", 10, 100, 50, 40),
            TextUpdate("t", "pv", 70, 120, 80, 40),
        )
    )
    violations = LabelControlMisaligned.check(screen)
    assert len(violations) == 1


def test_label_control_misaligned_within_tab(tmp_path):
    screen = _screen(tmp_path)
    screen.add_widget(
        _tabs_with(
            Label("l", "Name", 10, 100, 50, 40),
            TextUpdate("t", "pv", 70, 120, 80, 40),
        )
    )
    violations = LabelControlMisaligned.check(screen)
    assert len(violations) == 1


def test_label_with_no_nearby_control_not_flagged(tmp_path):
    screen = _screen(tmp_path)
    screen.add_widget(Label("l", "Name", 10, 100, 50, 20))
    screen.add_widget(TextUpdate("t", "pv", 400, 400, 80, 20))
    assert LabelControlMisaligned.check(screen) == []


def test_label_control_not_sharing_horizontal_line_not_flagged(tmp_path):
    screen = _screen(tmp_path)
    screen.add_widget(Label("l", "Name", 10, 100, 50, 20))
    # Directly below, so no horizontal line passes through both.
    screen.add_widget(TextUpdate("t", "pv", 70, 140, 80, 20))
    assert LabelControlMisaligned.check(screen) == []


# ---------------------------------------------------------------------------
# SetpointReadbackMisaligned (W122)
# ---------------------------------------------------------------------------
def test_setpoint_readback_aligned_not_flagged(tmp_path):
    screen = _screen(tmp_path)
    screen.add_widget(TextEntry("sp", "pv", 10, 100, 60, 20))
    screen.add_widget(TextUpdate("rb", "pv", 80, 100, 60, 20))
    assert SetpointReadbackMisaligned.check(screen) == []


def test_setpoint_readback_misaligned_flagged_and_fixable(tmp_path):
    screen = _screen(tmp_path)
    screen.add_widget(TextEntry("sp", "pv", 10, 100, 60, 40))
    readback = TextUpdate("rb", "pv", 80, 120, 60, 40)
    screen.add_widget(readback)

    violations = SetpointReadbackMisaligned.check(screen)
    assert len(violations) == 1
    assert violations[0].fixable is True

    assert SetpointReadbackMisaligned.fix(violations[0]) is True
    assert readback.y == 100
    assert SetpointReadbackMisaligned.check(screen) == []


def test_setpoint_readback_misaligned_within_group(tmp_path):
    screen = _screen(tmp_path)
    screen.add_widget(
        _group_with(
            TextEntry("sp", "pv", 10, 100, 60, 40),
            TextUpdate("rb", "pv", 80, 120, 60, 40),
        )
    )
    assert len(SetpointReadbackMisaligned.check(screen)) == 1


# ---------------------------------------------------------------------------
# InconsistentColumnLayout (W123)
# ---------------------------------------------------------------------------
def test_consistent_column_not_flagged(tmp_path):
    screen = _screen(tmp_path)
    for i in range(3):
        screen.add_widget(TextUpdate(f"t{i}", "pv", 10, 10 + i * 30, 60, 20))
    assert InconsistentColumnLayout.check(screen) == []


def test_two_widgets_not_treated_as_column(tmp_path):
    screen = _screen(tmp_path)
    screen.add_widget(TextUpdate("t0", "pv", 10, 10, 60, 20))
    screen.add_widget(TextUpdate("t1", "pv", 30, 40, 60, 20))
    assert InconsistentColumnLayout.check(screen) == []


def test_widgets_with_spread_centers_not_a_column(tmp_path):
    screen = _screen(tmp_path)
    # Centers at 40, 55, 70: no vertical line is within 10px of all of them.
    screen.add_widget(TextUpdate("t0", "pv", 10, 10, 60, 20))
    screen.add_widget(TextUpdate("t1", "pv", 25, 40, 60, 20))
    screen.add_widget(TextUpdate("t2", "pv", 40, 70, 60, 20))
    assert InconsistentColumnLayout.check(screen) == []


def test_column_misaligned_centers_flagged_and_fixed(tmp_path):
    screen = _screen(tmp_path)
    widgets = [
        TextUpdate("t0", "pv", 10, 10, 60, 20),
        TextUpdate("t1", "pv", 20, 40, 60, 20),
        TextUpdate("t2", "pv", 10, 70, 60, 20),
    ]
    for widget in widgets:
        screen.add_widget(widget)

    violations = InconsistentColumnLayout.check(screen)
    assert len(violations) == 1
    assert violations[0].fixable is True

    assert InconsistentColumnLayout.fix(violations[0]) is True
    assert {w.x for w in widgets} == {10}
    assert InconsistentColumnLayout.check(screen) == []


def test_column_uneven_spacing_flagged_and_fixed(tmp_path):
    screen = _screen(tmp_path)
    widgets = [
        TextUpdate("t0", "pv", 10, 10, 60, 20),
        TextUpdate("t1", "pv", 10, 45, 60, 20),
        TextUpdate("t2", "pv", 10, 70, 60, 20),
    ]
    for widget in widgets:
        screen.add_widget(widget)

    violations = InconsistentColumnLayout.check(screen)
    assert len(violations) == 1
    assert InconsistentColumnLayout.fix(violations[0]) is True
    assert InconsistentColumnLayout.check(screen) == []


def test_column_differing_sizes_flagged_and_fixed(tmp_path):
    screen = _screen(tmp_path)
    widgets = [
        TextUpdate("t0", "pv", 10, 10, 60, 20),
        TextUpdate("t1", "pv", 10, 40, 80, 20),
        TextUpdate("t2", "pv", 10, 70, 60, 20),
    ]
    for widget in widgets:
        screen.add_widget(widget)

    violations = InconsistentColumnLayout.check(screen)
    assert len(violations) == 1
    assert InconsistentColumnLayout.fix(violations[0]) is True
    assert {w.width for w in widgets} == {60}
    assert InconsistentColumnLayout.check(screen) == []


def test_column_spacing_exceeds_maximum_flagged_and_fixed(tmp_path):
    screen = _screen(tmp_path)
    widgets = [
        TextUpdate("t0", "pv", 10, 10, 60, 20),
        TextUpdate("t1", "pv", 10, 70, 60, 20),
        TextUpdate("t2", "pv", 10, 130, 60, 20),
    ]
    for widget in widgets:
        screen.add_widget(widget)

    violations = InconsistentColumnLayout.check(screen)
    assert len(violations) == 1
    assert InconsistentColumnLayout.fix(violations[0]) is True
    assert InconsistentColumnLayout.check(screen) == []


def test_column_inconsistent_within_group(tmp_path):
    screen = _screen(tmp_path)
    screen.add_widget(
        _group_with(
            TextUpdate("t0", "pv", 10, 10, 60, 20),
            TextUpdate("t1", "pv", 20, 40, 60, 20),
            TextUpdate("t2", "pv", 10, 70, 60, 20),
        )
    )
    assert len(InconsistentColumnLayout.check(screen)) == 1


def _vertical_monitor(name="bm", x=10, y=0, width=20, height=200, num_bits=4):
    monitor = ByteMonitor(name, "pv", x, y, width, height)
    monitor.horizontal = False
    monitor.num_bits = num_bits
    return monitor


# ---------------------------------------------------------------------------
# ByteMonitorLabelsMisaligned (W124)
# ---------------------------------------------------------------------------
def test_byte_monitor_labels_aligned_not_flagged(tmp_path):
    screen = _screen(tmp_path)
    screen.add_widget(_vertical_monitor())
    # Segments of 50px; bit centres at 25, 75, 125, 175.
    for i, center in enumerate((25, 75, 125, 175)):
        screen.add_widget(Label(f"l{i}", "bit", 40, center - 10, 40, 20))
    assert ByteMonitorLabelsMisaligned.check(screen) == []


def test_byte_monitor_label_misaligned_flagged_and_fixable(tmp_path):
    screen = _screen(tmp_path)
    screen.add_widget(_vertical_monitor())
    screen.add_widget(Label("l0", "bit", 40, 15, 40, 20))
    screen.add_widget(Label("l1", "bit", 40, 65, 40, 20))
    screen.add_widget(Label("l2", "bit", 40, 115, 40, 20))
    stray = Label("l3", "bit", 40, 40, 40, 20)  # nearest centre 25, off by 25
    screen.add_widget(stray)

    violations = ByteMonitorLabelsMisaligned.check(screen)
    assert len(violations) == 1
    assert violations[0].fixable is True

    assert ByteMonitorLabelsMisaligned.fix(violations[0]) is True
    assert stray.y == 15
    assert ByteMonitorLabelsMisaligned.check(screen) == []


def test_horizontal_byte_monitor_labels_not_flagged(tmp_path):
    screen = _screen(tmp_path)
    monitor = ByteMonitor("bm", "pv", 10, 0, 200, 20)
    monitor.horizontal = True
    monitor.num_bits = 4
    screen.add_widget(monitor)
    screen.add_widget(Label("l0", "bit", 40, 40, 40, 20))
    screen.add_widget(Label("l1", "bit", 40, 90, 40, 20))
    assert ByteMonitorLabelsMisaligned.check(screen) == []


def test_byte_monitor_single_label_not_flagged(tmp_path):
    screen = _screen(tmp_path)
    screen.add_widget(_vertical_monitor())
    screen.add_widget(Label("l0", "bit", 40, 40, 40, 20))
    assert ByteMonitorLabelsMisaligned.check(screen) == []


def test_byte_monitor_label_too_close_flagged_and_fixed(tmp_path):
    screen = _screen(tmp_path)
    screen.add_widget(_vertical_monitor(height=100, num_bits=2))
    # Aligned to centres 25 and 75, but only 1px from the monitor's edge.
    near_top = Label("l0", "bit", 31, 15, 40, 20)
    near_bottom = Label("l1", "bit", 31, 65, 40, 20)
    screen.add_widget(near_top)
    screen.add_widget(near_bottom)

    violations = ByteMonitorLabelsMisaligned.check(screen)
    assert len(violations) == 2

    for violation in violations:
        assert ByteMonitorLabelsMisaligned.fix(violation) is True
    assert near_top.x == 35
    assert near_bottom.x == 35
    assert ByteMonitorLabelsMisaligned.check(screen) == []


def test_byte_monitor_labels_misaligned_within_group(tmp_path):
    screen = _screen(tmp_path)
    screen.add_widget(
        _group_with(
            _vertical_monitor(height=100, num_bits=2),
            Label("l0", "bit", 40, 15, 40, 20),
            Label("l1", "bit", 40, 40, 40, 20),
        )
    )
    assert len(ByteMonitorLabelsMisaligned.check(screen)) == 1


# ---------------------------------------------------------------------------
# Minimum 5px gap between aligned widgets
# ---------------------------------------------------------------------------
def test_label_control_too_close_flagged_and_separated(tmp_path):
    screen = _screen(tmp_path)
    screen.add_widget(Label("l", "Name", 10, 100, 50, 20))
    control = TextUpdate("t", "pv", 62, 100, 80, 20)  # aligned but 2px gap
    screen.add_widget(control)

    violations = LabelControlMisaligned.check(screen)
    assert len(violations) == 1

    assert LabelControlMisaligned.fix(violations[0]) is True
    assert control.x == 65
    assert LabelControlMisaligned.check(screen) == []


def test_setpoint_readback_too_close_flagged_and_separated(tmp_path):
    screen = _screen(tmp_path)
    screen.add_widget(TextEntry("sp", "pv", 10, 100, 60, 20))
    readback = TextUpdate("rb", "pv", 72, 100, 60, 20)  # aligned but 2px gap
    screen.add_widget(readback)

    violations = SetpointReadbackMisaligned.check(screen)
    assert len(violations) == 1

    assert SetpointReadbackMisaligned.fix(violations[0]) is True
    assert readback.x == 75
    assert SetpointReadbackMisaligned.check(screen) == []
