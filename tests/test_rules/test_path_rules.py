from phoebusgen.v4 import Screen
from phoebuslint.linter import PhoebusLinter
from phoebuslint.rules.paths import (
    DisplayFileIsOpiFile,
    DisplayFilePathDoesNotExist,
    DisplayFilePathNotBobOrOpiFile,
    DisplayFilePathNotSet,
)


def _navtabs_source(*files: str) -> str:
    tabs = "".join(
        f"      <tab><name>Tab{i}</name><file>{f}</file></tab>\n"
        for i, f in enumerate(files)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<display version="2.0.0">\n'
        "  <name>Source</name>\n"
        "  <width>800</width>\n"
        "  <height>600</height>\n"
        '  <widget type="navtabs" version="2.0.0">\n'
        "    <name>Navigation Tabs</name>\n"
        "    <x>0</x><y>0</y><width>400</width><height>300</height>\n"
        "    <tabs>\n"
        f"{tabs}"
        "    </tabs>\n"
        "  </widget>\n"
        "</display>\n"
    )


def _navtabs_source_no_file() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<display version="2.0.0">\n'
        "  <name>Source</name>\n"
        "  <width>800</width>\n"
        "  <height>600</height>\n"
        '  <widget type="navtabs" version="2.0.0">\n'
        "    <name>Navigation Tabs</name>\n"
        "    <x>0</x><y>0</y><width>400</width><height>300</height>\n"
        "    <tabs>\n"
        "      <tab><name>Tab0</name></tab>\n"
        "    </tabs>\n"
        "  </widget>\n"
        "</display>\n"
    )


def _template_instance_source(file: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<display version="2.0.0">\n'
        "  <name>Source</name>\n"
        '  <widget type="template" version="2.0.0">\n'
        "    <name>Template Instance</name>\n"
        f"    <file>{file}</file>\n"
        "  </widget>\n"
        "</display>\n"
    )


def test_navtabs_path_does_not_exist_flags_missing(tmp_path):
    """NavigationTabs tabs pointing to missing files are flagged."""
    (tmp_path / "real.bob").write_text("")
    source_bob = tmp_path / "source.bob"
    source_bob.write_text(_navtabs_source("real.bob", "missing.bob"))
    screen = Screen(f_name=str(source_bob))

    violations = DisplayFilePathDoesNotExist.check(screen)
    assert len(violations) == 1
    assert "missing.bob" in violations[0].details


def test_navtabs_path_fixable_only_with_match(tmp_path):
    """A missing NavigationTabs tab path is repointed to its closest match."""
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "panel.bob").write_text("")
    source_bob = tmp_path / "source.bob"
    source_bob.write_text(_navtabs_source("panel.bob"))

    linter = PhoebusLinter()
    linter.build_bob_file_tree(tmp_path)
    screen = Screen(f_name=str(source_bob))

    violations = DisplayFilePathDoesNotExist.check(screen)
    assert len(violations) == 1
    assert violations[0].fixable is True
    assert DisplayFilePathDoesNotExist.fix(violations[0]) is True
    assert len(DisplayFilePathDoesNotExist.check(screen)) == 0


def test_navtabs_not_bob_or_opi_flags_wrong_suffix(tmp_path):
    """A NavigationTabs tab pointing to a non-bob/opi file is flagged."""
    source_bob = tmp_path / "source.bob"
    source_bob.write_text(_navtabs_source("notes.txt"))
    screen = Screen(f_name=str(source_bob))

    violations = DisplayFilePathNotBobOrOpiFile.check(screen)
    assert len(violations) == 1
    assert "notes.txt" in violations[0].details


def test_navtabs_no_file_path_set_flagged(tmp_path):
    """A NavigationTabs tab with no file element is flagged."""
    source_bob = tmp_path / "source.bob"
    source_bob.write_text(_navtabs_source_no_file())
    screen = Screen(f_name=str(source_bob))

    violations = DisplayFilePathNotSet.check(screen)
    assert len(violations) == 1


def test_navtabs_opi_file_flagged_and_fixable(tmp_path):
    """A NavigationTabs tab pointing to an .opi file is flagged and fixable."""
    (tmp_path / "panel.opi").write_text("")
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "panel.bob").write_text("")
    source_bob = tmp_path / "source.bob"
    source_bob.write_text(_navtabs_source("panel.opi"))

    linter = PhoebusLinter()
    linter.build_bob_file_tree(tmp_path)
    screen = Screen(f_name=str(source_bob))

    violations = DisplayFileIsOpiFile.check(screen)
    assert len(violations) == 1
    assert "panel.opi" in violations[0].details
    assert violations[0].fixable is True
    assert DisplayFileIsOpiFile.fix(violations[0]) is True
    assert len(DisplayFileIsOpiFile.check(screen)) == 0


def test_navtabs_valid_paths_not_flagged(tmp_path):
    """Existing .bob/.opi tab paths produce no missing/unset violation."""
    (tmp_path / "a.bob").write_text("")
    (tmp_path / "b.opi").write_text("")
    source_bob = tmp_path / "source.bob"
    source_bob.write_text(_navtabs_source("a.bob", "b.opi"))
    screen = Screen(f_name=str(source_bob))

    assert len(DisplayFilePathDoesNotExist.check(screen)) == 0
    assert len(DisplayFilePathNotBobOrOpiFile.check(screen)) == 0
    assert len(DisplayFilePathNotSet.check(screen)) == 0


def test_template_instance_no_file_path_set(tmp_path):
    """A TemplateInstance with no file element is flagged."""
    source_bob = tmp_path / "source.bob"
    source_bob.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<display version="2.0.0">\n'
        "  <name>Source</name>\n"
        '  <widget type="template" version="2.0.0">\n'
        "    <name>Template Instance</name>\n"
        "  </widget>\n"
        "</display>\n"
    )
    screen = Screen(f_name=str(source_bob))

    violations = DisplayFilePathNotSet.check(screen)
    assert len(violations) == 1


def test_template_instance_path_does_not_exist(tmp_path):
    """A TemplateInstance pointing to a missing file is flagged and fixable."""
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "template.bob").write_text("")
    source_bob = tmp_path / "source.bob"
    source_bob.write_text(_template_instance_source("template.bob"))

    linter = PhoebusLinter()
    linter.build_bob_file_tree(tmp_path)
    screen = Screen(f_name=str(source_bob))

    violations = DisplayFilePathDoesNotExist.check(screen)
    assert len(violations) == 1
    assert violations[0].fixable is True
    assert DisplayFilePathDoesNotExist.fix(violations[0]) is True
    assert len(DisplayFilePathDoesNotExist.check(screen)) == 0


def test_template_instance_path_is_opi_file(tmp_path):
    """A TemplateInstance pointing to an .opi file is flagged."""
    (tmp_path / "template.opi").write_text("")
    source_bob = tmp_path / "source.bob"
    source_bob.write_text(_template_instance_source("template.opi"))
    screen = Screen(f_name=str(source_bob))

    violations = DisplayFileIsOpiFile.check(screen)
    assert len(violations) == 1
    assert "template.opi" in violations[0].details


def test_template_instance_opi_fixable_with_matching_bob(tmp_path):
    """An .opi TemplateInstance path is repointed to a same-named .bob in the tree."""
    (tmp_path / "template.opi").write_text("")
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "template.bob").write_text("")
    source_bob = tmp_path / "source.bob"
    source_bob.write_text(_template_instance_source("template.opi"))

    linter = PhoebusLinter()
    linter.build_bob_file_tree(tmp_path)
    screen = Screen(f_name=str(source_bob))

    violations = DisplayFileIsOpiFile.check(screen)
    assert len(violations) == 1
    assert violations[0].fixable is True
    assert DisplayFileIsOpiFile.fix(violations[0]) is True
    assert len(DisplayFileIsOpiFile.check(screen)) == 0


def test_template_instance_opi_not_fixable_without_matching_bob(tmp_path):
    """An .opi TemplateInstance path is not fixable when no .bob match exists."""
    (tmp_path / "template.opi").write_text("")
    source_bob = tmp_path / "source.bob"
    source_bob.write_text(_template_instance_source("template.opi"))

    linter = PhoebusLinter()
    linter.build_bob_file_tree(tmp_path)
    screen = Screen(f_name=str(source_bob))

    violations = DisplayFileIsOpiFile.check(screen)
    assert len(violations) == 1
    assert violations[0].fixable is False
