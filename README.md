# PhoebusLint

A linter for [CS-Studio Phoebus](https://github.com/ControlSystemStudio/phoebus) operator interface display files (`.bob`).

PhoebusLint analyzes Phoebus display screens for common issues such as broken file paths, widgets out of bounds, undefined macros in screen transitions, and more.

## Installation

```bash
pip install phoebuslint
```

Or install from source:

```bash
git clone https://github.com/jwlodek/phoebuslint.git
cd phoebuslint
pip install -e .
```

## Usage

Lint all `.bob` files in the current directory recursively:

```bash
phoebuslint
```

Lint specific files or directories:

```bash
phoebuslint path/to/screen.bob path/to/directory/
```

### Options

| Option | Description |
|--------|-------------|
| `-c`, `--config` | Path to a YAML configuration file |
| `-d`, `--debug` | Enable debug logging |
| `-q`, `--quiet` | Quiet mode — only show warnings and above |
| `--fix` | Automatically fix certain linting issues |
| `-i`, `--ignore-paths` | Paths to ignore during linting |
| `--fail-severity` | Set minimum severity to fail (`INFO`, `WARNING`, `ERROR`). Default: `WARNING` |
| `--filter` | Only run specific rules by code |
| `--show-counts` | Show how many issues were found for each error code |
| `-v`, `--version` | Show version |

### Examples

Run only specific rules:

```bash
phoebuslint --filter W101 S106
```

Auto-fix fixable issues:

```bash
phoebuslint --fix path/to/screens/
```

Ignore certain directories:

```bash
phoebuslint -i build/ archive/ .
```

## Rules

### Screen Rules (`S1xx`)

| Code | Rule | Severity | Fixable |
|------|------|----------|---------|
| S102 | Missing top-level `<display>` tag | CRITICAL | No |
| S103 | Root tag is not `<display>` | CRITICAL | No |
| S104 | Unexpected tag found in `<display>` | WARNING | No |
| S105 | Screen has empty or unset title | WARNING | No |
| S106 | Screen has default title ("Display") | WARNING | Yes (renames to filename) |
| S107 | Screen is empty (no widgets) | WARNING | Yes (deletes the file) |
| S108 | Screen has zero or negative height/width | WARNING | No |

### Widget Rules (`W1xx`)

| Code | Rule | Severity | Fixable |
|------|------|----------|---------|
| W101 | Widget has zero or negative height/width | WARNING | No |
| W102 | Widget is out of screen bounds | WARNING | No |
| W103 | ActionButton has no actions defined | WARNING | No |
| W104 | Label has empty text | WARNING | No |
| W105 | Label has excessively long text | WARNING | No |
| W106 | TextUpdate widget with no defined PV | WARNING | No |
| W119 | Label/TextUpdate font size too large for widget height | WARNING | Yes |
| W121 | Label is not aligned with, or is too close to, its associated control widget (only widgets a horizontal line passes through are paired) | WARNING | Yes (unsafe, aligns rows and keeps a 5px gap) |
| W122 | Setpoint widget is not aligned with, or is too close to, its associated readback (only widgets a horizontal line passes through are paired) | WARNING | Yes (unsafe, aligns rows and keeps a 5px gap) |
| W123 | Widgets in a column (centers within 10px of a shared vertical line) are not consistently laid out | WARNING | Yes (unsafe, aligns centers, sizes and spacing with a 5px minimum gap) |
| W124 | Label beside a vertical byte monitor is not aligned with its bit | WARNING | Yes (unsafe, aligns label to its bit and keeps a 5px gap) |

### Macro Rules (`M1xx`)

| Code | Rule | Severity | Fixable |
|------|------|----------|---------|
| M101 | Screen transition leads to undefined macros in target | ERROR | No |

### Graphics Rules (`G1xx`)

| Code | Rule | Severity | Fixable |
|------|------|----------|---------|
| G101 | Transparent graphic has zero line width | WARNING | Yes (sets line width to 1) |

### Path Rules (`P1xx`)

| Code | Rule | Severity | Fixable |
|------|------|----------|---------|
| P101 | Display file reference has no file path set | ERROR | No |
| P102 | Display file reference path does not exist | ERROR | Yes (unsafe, repoints to closest match) |
| P103 | Display file reference is neither a bob nor an opi file | WARNING | No |
| P104 | Display file reference points to an OPI file | WARNING | Yes (unsafe, repoints to same-named .bob) |
| P105 | OpenFileAction path does not exist | WARNING | Yes (unsafe, repoints to closest match) |
| P106 | OpenWebpageAction has an invalid URL | WARNING | No |
| P107 | Script file path does not exist | WARNING | No |

### Action Button Rules (`AB1xx`)

| Code | Rule | Severity | Fixable |
|------|------|----------|---------|
| AB101 | ActionButton has no actions defined | WARNING | Yes (removes the widget) |
| AB102 | ActionButton has more than 15 actions | WARNING | No |

## Configuration

PhoebusLint can be configured via a YAML file passed with the `--config` flag:

```yaml
enable_fixes: true
ignore_paths:
  - build/
  - archive/
fail_severity: WARNING
disabled_rule_codes:
  - W102
  - W105
```

## Development

[uv](https://docs.astral.sh/uv/) is recommended for development:

```bash
uv sync
```

Or with pip:

```bash
pip install -e .[dev]
```

Run tests:

```bash
uv run pytest
```

## Requirements

- Python >= 3.11
- [phoebusgen](https://github.com/jwlodek/phoebusgen) v4

## Author

Jakub Wlodek (jwlodek@bnl.gov)
