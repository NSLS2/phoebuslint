import argparse
import logging
from pathlib import Path
from typing import Any

import yaml

from . import rules  # noqa: F401 - import to register rule subclasses
from ._version import __version__
from .linter import PhoebusLinter, SeverityLevel, get_all_rule_codes
from .log import logger


def main():
    parser = argparse.ArgumentParser(
        description="Phoebus operator interface screen linter"
    )
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        help="Path to PhoebusLint configuration file",
        default=None,
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=None,
        help="Paths to .bob files or directories to lint recursively",
    )
    parser.add_argument(
        "-d", "--debug", action="store_true", help="Enable debug logging."
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Enable quiet mode, only show warning and above logs and linting report.",
    )

    parser.add_argument(
        "-v", "--version", action="version", version=f"PhoebusLint {__version__}"
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Enable automatic fixes for certain linting issues",
    )
    parser.add_argument(
        "--unsafe-fixes",
        action="store_true",
        help="Enable unsafe automatic fixes that may introduce breaking changes",
    )
    parser.add_argument(
        "-i",
        "--ignore-paths",
        nargs="+",
        help="List of paths to ignore during linting.",
    )
    parser.add_argument(
        "--fail-severity",
        type=str,
        choices=["INFO", "WARNING", "ERROR"],
        help="Set the fail severity level",
        default="WARNING",
    )
    all_rule_codes = get_all_rule_codes()
    parser.add_argument(
        "--filter",
        type=str,
        nargs="+",
        choices=["S101"] + all_rule_codes,
        metavar="RULE_CODE",
        help="Filter linting rules by their codes.",
    )
    parser.add_argument(
        "--filter-out",
        type=str,
        nargs="+",
        choices=["S101"] + all_rule_codes,
        metavar="RULE_CODE",
        help="Disable the linting rules with the given codes.",
    )
    parser.add_argument(
        "--show-counts",
        action="store_true",
        help="Show counts of each rule violation.",
    )
    parser.add_argument(
        "--show-rules",
        action="store_true",
        help="Print all enabled rules with descriptions, then lint if paths given.",
    )

    args = parser.parse_args()
    if args.debug:
        logger.setLevel(logging.DEBUG)
    elif args.quiet:
        logger.setLevel(logging.WARNING)

    linter_config: dict[str, Any] = {}

    if args.config and Path(args.config).is_file():
        with open(args.config) as f:
            config_content = f.read()
            linter_config.update(yaml.safe_load(config_content))

    if args.fix:
        linter_config["enable_fixes"] = True
    if args.unsafe_fixes:
        linter_config["enable_fixes"] = True
        linter_config["enable_unsafe_fixes"] = True
    if args.ignore_paths:
        linter_config["ignore_paths"] = args.ignore_paths
    if args.fail_severity:
        linter_config["fail_severity"] = SeverityLevel[args.fail_severity]
    if args.filter:
        linter_config["disabled_rule_codes"] = [
            code for code in all_rule_codes if code not in args.filter
        ]
    if args.filter_out:
        disabled = set(linter_config.get("disabled_rule_codes", []))
        disabled.update(args.filter_out)
        linter_config["disabled_rule_codes"] = list(disabled)
    if args.show_counts:
        linter_config["show_counts"] = True

    linter = PhoebusLinter(**linter_config)

    logger.info(f"PhoebusLint version: {__version__}")

    if args.show_rules:
        linter.display_rules()
        if not args.paths:
            exit(0)

    # Build the bob file tree from cwd for path resolution
    linter.build_bob_file_tree(Path.cwd())

    results = {}
    num_fixable = 0
    for path_str in args.paths or ["."]:
        path = Path(path_str)
        if path.is_file() and path.suffix == ".bob":
            results, num_fixable = linter.lint_file(
                path, visited=results, num_fixable=num_fixable
            )
        elif path.is_dir():
            results, num_fixable = linter.lint_directory(path)
        else:
            logger.warning(f"Skipping invalid path: {path}")

    linter.display_linting_report(results, num_fixable)
    if linter.did_linting_pass(results):
        exit(0)
    else:
        exit(1)


if __name__ == "__main__":
    main()
