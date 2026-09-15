from collections.abc import Iterator, Sequence
from statistics import median

from phoebusgen.v4 import Screen
from phoebusgen.v4.widgets import (
    ActionButton,
    ByteMonitor,
    CheckBox,
    ComboBox,
    Group,
    HasWidgets,
    LED,
    Label,
    Spinner,
    Tabs,
    TextEntry,
    TextUpdate,
    Widget,
)

from ..linter import (
    RuleViolation,
    SeverityLevel,
    UnsafeFixableLintRule,
)

# Two widgets are considered aligned on an axis when their positions differ by
# no more than this many pixels.
_ALIGNMENT_TOLERANCE = 15
# Maximum edge-to-edge distance for a label/control (or setpoint/readback) pair
# to be considered associated with one another.
_MAX_ASSOCIATION_GAP = 50
# Aligned widgets must be separated by at least this many pixels so they neither
# overlap nor crowd one another.
_MIN_WIDGET_GAP = 5
# A vertical byte monitor must have at least this many labels beside it before
# they are treated as per-bit labels.
_BYTE_MONITOR_MIN_LABELS = 2
# Column widgets should be separated by no more than this vertical gap.
_MAX_COLUMN_SPACING = 25
# A column must contain at least this many widgets to be considered one.
_COLUMN_MIN_WIDGETS = 3
# Widgets whose centers fall within this distance of a shared vertical line are
# treated as one column.
_COLUMN_CENTER_TOLERANCE = 10
# Widgets in a shared column but separated by a larger gap are treated as
# belonging to distinct columns rather than one poorly-spaced column.
_COLUMN_DETECTION_MAX_GAP = 60
# Differences at or below this are treated as "already aligned/uniform".
_EXACT_TOLERANCE = 2

# Control widgets that a descriptive label is expected to annotate.
_CONTROL_TYPES = (TextUpdate, TextEntry, LED, ActionButton, ComboBox, Spinner, CheckBox)
# Widget types that commonly form aligned columns.
_COLUMN_TYPES = (Label, TextUpdate, TextEntry, LED, ActionButton, ComboBox, Spinner)


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------
def _h_center(widget: Widget) -> float:
    return widget.x + widget.width / 2


def _v_center(widget: Widget) -> float:
    return widget.y + widget.height / 2


def _edge_gap(a: Widget, b: Widget) -> float:
    """Shortest distance between the bounding boxes of two widgets."""
    dx = max(b.x - (a.x + a.width), a.x - (b.x + b.width), 0)
    dy = max(b.y - (a.y + a.height), a.y - (b.y + b.height), 0)
    return (dx**2 + dy**2) ** 0.5


def _shares_horizontal_line(a: Widget, b: Widget) -> bool:
    """True when a single horizontal line can pass through both widgets."""
    return a.y <= b.y + b.height and b.y <= a.y + a.height


def _rows_aligned(a: Widget, b: Widget) -> bool:
    """True when two widgets' vertical centers align within tolerance."""
    return abs(_v_center(a) - _v_center(b)) <= _ALIGNMENT_TOLERANCE


def _iter_sibling_groups(container: HasWidgets) -> Iterator[list[Widget]]:
    """Yield the direct children of the screen and of every nested container.

    Each yielded list shares a single coordinate space (the screen, a group, or
    a tab), so widgets can be compared for alignment and spacing meaningfully.
    """
    children = list(container.get_widgets())
    if children:
        yield children
    for widget in children:
        if isinstance(widget, HasWidgets):
            yield from _iter_sibling_groups(widget)
        elif isinstance(widget, Tabs):
            for tab in widget.tabs:
                yield from _iter_sibling_groups(tab)


def _nearest_partner(primary: Widget, partners: list[Widget]) -> Widget | None:
    """Closest partner sharing a horizontal line with ``primary``."""
    best: Widget | None = None
    best_gap: float | None = None
    for partner in partners:
        if not _shares_horizontal_line(primary, partner):
            continue
        gap = _edge_gap(primary, partner)
        if gap <= _MAX_ASSOCIATION_GAP and (best_gap is None or gap < best_gap):
            best, best_gap = partner, gap
    return best


def _align_partner(primary: Widget, partner: Widget) -> bool:
    """Align ``partner``'s row to ``primary`` and keep a minimum gap between them."""
    changed = False
    # Partners share a horizontal line, so align their rows (vertical centers).
    new_y = round(_v_center(primary) - partner.height / 2)
    if partner.y != new_y:
        partner.y = new_y
        changed = True
    # Keep at least the minimum gap on the horizontal axis.
    if _h_center(partner) >= _h_center(primary):
        min_x = primary.x + primary.width + _MIN_WIDGET_GAP
        if partner.x < min_x:
            partner.x = min_x
            changed = True
    else:
        max_right = primary.x - _MIN_WIDGET_GAP
        if partner.x + partner.width > max_right:
            partner.x = max_right - partner.width
            changed = True
    return changed


def _check_pair_alignment(
    rule: type[UnsafeFixableLintRule],
    screen: Screen,
    primary_types: tuple[type[Widget], ...],
    partner_types: tuple[type[Widget], ...],
) -> list[RuleViolation]:
    """Flag primary widgets that are not aligned with their nearest partner."""
    violations = []
    for group in _iter_sibling_groups(screen):
        partners = [w for w in group if isinstance(w, partner_types)]
        if not partners:
            continue
        for primary in group:
            if not isinstance(primary, primary_types):
                continue
            candidates = [p for p in partners if p is not primary]
            partner = _nearest_partner(primary, candidates)
            if partner is None:
                continue
            if _rows_aligned(primary, partner) and (
                _edge_gap(primary, partner) >= _MIN_WIDGET_GAP
            ):
                continue
            violations.append(
                rule.rule_violation_factory(
                    screen=screen,
                    widget=primary,
                    details=rule.description
                    + f" (Widget: {primary.name}, Partner: {partner.name})",
                    fixable=True,
                )
            )
    return violations


def _fix_pair_alignment(
    violation: RuleViolation, partner_types: tuple[type[Widget], ...]
) -> bool:
    """Nudge the violation widget's nearest partner into alignment with it."""
    widget = violation.widget
    if widget is None:
        return False
    screen = violation.screen
    for group in _iter_sibling_groups(screen):
        if not any(w.root is widget.root for w in group):
            continue
        candidates = [
            w
            for w in group
            if isinstance(w, partner_types) and w.root is not widget.root
        ]
        partner = _nearest_partner(widget, candidates)
        if partner is None:
            return False
        return _align_partner(widget, partner)
    return False


class LabelControlMisaligned(UnsafeFixableLintRule):
    """A label is not aligned with the control widget it appears to annotate."""

    rule_code = "W121"
    rule_severity = SeverityLevel.WARNING
    description = "Label is not aligned with its associated control widget."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        return _check_pair_alignment(cls, screen, (Label,), _CONTROL_TYPES)

    @classmethod
    def fix(cls, violation: RuleViolation) -> bool:
        return _fix_pair_alignment(violation, _CONTROL_TYPES)


class SetpointReadbackMisaligned(UnsafeFixableLintRule):
    """A setpoint widget is not aligned with its associated readback widget."""

    rule_code = "W122"
    rule_severity = SeverityLevel.WARNING
    description = "Setpoint widget is not aligned with its associated readback."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        return _check_pair_alignment(
            cls, screen, (TextEntry, ComboBox), (TextUpdate,)
        )

    @classmethod
    def fix(cls, violation: RuleViolation) -> bool:
        return _fix_pair_alignment(violation, (TextUpdate,))


# ---------------------------------------------------------------------------
# Vertical byte monitor labels
# ---------------------------------------------------------------------------
def _iter_positioned(
    container: HasWidgets, offset_x: int = 0, offset_y: int = 0
) -> Iterator[tuple[Widget, int, int]]:
    """Yield ``(widget, offset_x, offset_y)`` for every widget in the tree.

    ``offset`` is the absolute position of the widget's coordinate space, so the
    widget's absolute position is ``offset + widget.x/y``. Groups shift their
    children; other containers share their parent's coordinate space.
    """
    for widget in container.get_widgets():
        yield widget, offset_x, offset_y
        if isinstance(widget, Group):
            yield from _iter_positioned(
                widget, offset_x + widget.x, offset_y + widget.y
            )
        elif isinstance(widget, HasWidgets):
            yield from _iter_positioned(widget, offset_x, offset_y)
        elif isinstance(widget, Tabs):
            for tab in widget.tabs:
                yield from _iter_positioned(tab, offset_x, offset_y)


def _byte_label_tolerance(segment: float) -> float:
    """Alignment tolerance for a bit label, scaled to the bit segment height."""
    return max(2.0, min(_ALIGNMENT_TOLERANCE, segment * 0.25))


# A resolved bit label: the widget, the absolute position of its coordinate
# space, the monitor's absolute left edge and width, the target bit-centre y,
# and the alignment tolerance.
_BytePlan = dict[object, tuple[Widget, int, int, int, int, float, float]]


def _byte_label_plan(screen: Screen) -> _BytePlan:
    """Match each bit label to its bit centre using absolute coordinates.

    A vertical byte monitor and its labels frequently live in different groups,
    so matching is done in absolute space. Only labels that can be confidently
    paired one-to-one with a monitor's bits (same count, ordered top to bottom)
    are included, which avoids collapsing several labels onto one bit.
    """
    positioned = list(_iter_positioned(screen))
    monitors = [
        (w, ox, oy)
        for w, ox, oy in positioned
        if isinstance(w, ByteMonitor) and not w.horizontal and w.num_bits > 0
    ]
    labels = [(w, ox, oy) for w, ox, oy in positioned if isinstance(w, Label)]
    monitor_boxes = [
        (mox + mon.x, moy + mon.y, mon.width, mon.height)
        for mon, mox, moy in monitors
    ]

    # Assign each label to the single nearest monitor beside it, so labels
    # squeezed between two columns are not claimed by both.
    buckets: dict[int, list[tuple[Widget, int, int, float]]] = {}
    for label, lox, loy in labels:
        lx, ly = lox + label.x, loy + label.y
        center_y = ly + label.height / 2
        best: int | None = None
        best_gap: float | None = None
        for i, (mx, my, mw, mh) in enumerate(monitor_boxes):
            if not (my - _ALIGNMENT_TOLERANCE <= center_y <= my + mh + _ALIGNMENT_TOLERANCE):
                continue
            beside = (
                lx + label.width <= mx + _EXACT_TOLERANCE
                or lx >= mx + mw - _EXACT_TOLERANCE
            )
            gap = max(lx - (mx + mw), mx - (lx + label.width), 0)
            if beside and gap <= _MAX_ASSOCIATION_GAP and (
                best_gap is None or gap < best_gap
            ):
                best, best_gap = i, gap
        if best is not None:
            buckets.setdefault(best, []).append((label, lox, loy, center_y))

    plan: _BytePlan = {}
    for i, associated in buckets.items():
        monitor = monitors[i][0]
        mx, my, mw, mh = monitor_boxes[i]
        nbits = monitor.num_bits
        if len(associated) < _BYTE_MONITOR_MIN_LABELS or len(associated) != nbits:
            continue
        segment = mh / nbits
        centers = [my + (b + 0.5) * segment for b in range(nbits)]
        tolerance = _byte_label_tolerance(segment)
        associated.sort(key=lambda item: item[3])
        for (label, lox, loy, _cy), center in zip(associated, centers):
            plan[label.root] = (label, lox, loy, mx, mw, center, tolerance)
    return plan


def _apply_byte_label(
    label: Widget,
    offset_x: int,
    offset_y: int,
    monitor_x: int,
    monitor_width: int,
    center: float,
) -> bool:
    """Align a label to its bit centre and keep a minimum gap from the monitor."""
    changed = False
    new_y = round(center - label.height / 2) - offset_y
    if label.y != new_y:
        label.y = new_y
        changed = True
    abs_x = offset_x + label.x
    monitor_right = monitor_x + monitor_width
    if abs_x + label.width / 2 >= monitor_x + monitor_width / 2:
        # Label sits to the right of the monitor.
        min_abs_x = monitor_right + _MIN_WIDGET_GAP
        if abs_x < min_abs_x:
            label.x = min_abs_x - offset_x
            changed = True
    else:
        # Label sits to the left of the monitor.
        max_abs_right = monitor_x - _MIN_WIDGET_GAP
        if abs_x + label.width > max_abs_right:
            label.x = max_abs_right - label.width - offset_x
            changed = True
    return changed


class ByteMonitorLabelsMisaligned(UnsafeFixableLintRule):
    """Labels beside a vertical byte monitor are not aligned with their bits."""

    rule_code = "W124"
    rule_severity = SeverityLevel.WARNING
    description = "Byte monitor label is not aligned with its associated bit."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        violations = []
        for label, lox, loy, mx, mw, center, tolerance in _byte_label_plan(
            screen
        ).values():
            center_y = loy + label.y + label.height / 2
            abs_x = lox + label.x
            gap = max(abs_x - (mx + mw), mx - (abs_x + label.width), 0)
            aligned = abs(center_y - center) <= tolerance
            spaced = gap >= _MIN_WIDGET_GAP
            if aligned and spaced:
                continue
            violations.append(
                cls.rule_violation_factory(
                    screen=screen,
                    widget=label,
                    details=cls.description + f" (Label: {label.name})",
                    fixable=True,
                )
            )
        return violations

    @classmethod
    def fix(cls, violation: RuleViolation) -> bool:
        widget = violation.widget
        if widget is None:
            return False
        entry = _byte_label_plan(violation.screen).get(widget.root)
        if entry is None:
            return False
        label, lox, loy, mx, mw, center, _tolerance = entry
        return _apply_byte_label(label, lox, loy, mx, mw, center)


# ---------------------------------------------------------------------------
# Column consistency
# ---------------------------------------------------------------------------
def _mode(values: list[int], prefer_max: bool = False) -> int:
    """Most common value, breaking ties towards the max or the min."""
    counts: dict[int, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    top = max(counts.values())
    tied = [value for value, count in counts.items() if count == top]
    return max(tied) if prefer_max else min(tied)


def _cluster_by_center(widgets: Sequence[Widget]) -> list[list[Widget]]:
    """Group widgets whose centers fall within the column center tolerance.

    Each cluster shares a vertical line (the first widget's center) that stays
    within ``_COLUMN_CENTER_TOLERANCE`` of every member's center.
    """
    clusters: list[list[Widget]] = []
    for widget in sorted(widgets, key=_h_center):
        for cluster in clusters:
            if abs(_h_center(widget) - _h_center(cluster[0])) <= _COLUMN_CENTER_TOLERANCE:
                cluster.append(widget)
                break
        else:
            clusters.append([widget])
    return clusters


def _columns_in_group(group: list[Widget]) -> list[list[Widget]]:
    """Detect vertically-stacked columns of similar widgets within a group."""
    candidates = [w for w in group if isinstance(w, _COLUMN_TYPES)]
    columns: list[list[Widget]] = []
    for cluster in _cluster_by_center(candidates):
        run: list[Widget] = []
        for widget in sorted(cluster, key=lambda w: w.y):
            if run:
                gap = widget.y - (run[-1].y + run[-1].height)
                if gap > _COLUMN_DETECTION_MAX_GAP:
                    if len(run) >= _COLUMN_MIN_WIDGETS:
                        columns.append(run)
                    run = []
            run.append(widget)
        if len(run) >= _COLUMN_MIN_WIDGETS:
            columns.append(run)
    return columns


def _column_issues(column: list[Widget]) -> list[str]:
    """Return a list of layout problems found in a detected column."""
    issues = []
    centers = [_h_center(w) for w in column]
    if max(centers) - min(centers) > _EXACT_TOLERANCE:
        issues.append("widget centers are not aligned to a vertical line")

    by_type: dict[type, list[Widget]] = {}
    for widget in column:
        by_type.setdefault(type(widget), []).append(widget)
    for widgets in by_type.values():
        if len(widgets) < 2:
            continue
        widths = [w.width for w in widgets]
        heights = [w.height for w in widgets]
        if max(widths) - min(widths) > _EXACT_TOLERANCE:
            issues.append("same-type widgets have differing widths")
        if max(heights) - min(heights) > _EXACT_TOLERANCE:
            issues.append("same-type widgets have differing heights")

    gaps = [
        column[i + 1].y - (column[i].y + column[i].height)
        for i in range(len(column) - 1)
    ]
    if gaps and max(gaps) - min(gaps) > _EXACT_TOLERANCE:
        issues.append("widgets are not evenly spaced")
    if gaps and min(gaps) < _MIN_WIDGET_GAP:
        issues.append(f"widgets overlap or are closer than {_MIN_WIDGET_GAP}px")
    if gaps and max(gaps) > _MAX_COLUMN_SPACING:
        issues.append(f"vertical spacing exceeds {_MAX_COLUMN_SPACING}px")
    return issues


def _normalize_column(column: list[Widget]) -> bool:
    """Align a column's centers, dimensions per type and vertical spacing."""
    changed = False
    ordered = sorted(column, key=lambda w: w.y)

    by_type: dict[type, list[Widget]] = {}
    for widget in ordered:
        by_type.setdefault(type(widget), []).append(widget)
    for widgets in by_type.values():
        if len(widgets) < 2:
            continue
        target_width = _mode([w.width for w in widgets], prefer_max=True)
        target_height = _mode([w.height for w in widgets], prefer_max=True)
        for widget in widgets:
            if widget.width != target_width:
                widget.width = target_width
                changed = True
            if widget.height != target_height:
                widget.height = target_height
                changed = True

    common_center = _mode([round(_h_center(w)) for w in ordered])
    for widget in ordered:
        new_x = round(common_center - widget.width / 2)
        if widget.x != new_x:
            widget.x = new_x
            changed = True

    gaps = [
        ordered[i + 1].y - (ordered[i].y + ordered[i].height)
        for i in range(len(ordered) - 1)
    ]
    valid_gaps = [gap for gap in gaps if gap >= 0]
    target_gap = round(median(valid_gaps)) if valid_gaps else _MAX_COLUMN_SPACING
    target_gap = max(_MIN_WIDGET_GAP, min(target_gap, _MAX_COLUMN_SPACING))
    for previous, widget in zip(ordered, ordered[1:]):
        new_y = previous.y + previous.height + target_gap
        if widget.y != new_y:
            widget.y = new_y
            changed = True
    return changed


class InconsistentColumnLayout(UnsafeFixableLintRule):
    """Similar widgets stacked in a column are misaligned, mis-sized or unevenly spaced."""

    rule_code = "W123"
    rule_severity = SeverityLevel.WARNING
    description = "Widgets in a column are not consistently laid out."

    @classmethod
    def check(cls, screen: Screen) -> list[RuleViolation]:
        violations = []
        for group in _iter_sibling_groups(screen):
            for column in _columns_in_group(group):
                issues = _column_issues(column)
                if not issues:
                    continue
                violations.append(
                    cls.rule_violation_factory(
                        screen=screen,
                        widget=column[0],
                        details=cls.description + f" ({'; '.join(issues)})",
                        fixable=True,
                    )
                )
        return violations

    @classmethod
    def fix(cls, violation: RuleViolation) -> bool:
        widget = violation.widget
        if widget is None:
            return False
        screen = violation.screen
        for group in _iter_sibling_groups(screen):
            for column in _columns_in_group(group):
                if any(w.root is widget.root for w in column):
                    return _normalize_column(column)
        return False
