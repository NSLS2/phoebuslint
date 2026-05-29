import argparse
import logging
from pathlib import Path

import yaml

from ._version import __version__
from . import rules  # noqa: F401 - import to register rule subclasses
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
        default=["."],
        help="Paths to .bob files or directories to lint recursively",
    )
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug logging.")
    parser.add_argument("-q", "--quiet", action="store_true", help="Enable quiet mode, only show warning and above log messages and linting report.")

    parser.add_argument(
        "-v", "--version", action="version", version=f"PhoebusLint {__version__}"
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Enable automatic fixes for certain linting issues",
    )
    parser.add_argument("-i", "--ignore-paths", nargs="+", help="List of paths to ignore during linting.")
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
        help="Filter linting rules by their codes."
    )

    args = parser.parse_args()
    if args.debug:
        logger.setLevel(logging.DEBUG)
    elif args.quiet:
        logger.setLevel(logging.WARNING)

    linter_config = {}

    if args.config and Path(args.config).is_file():
        with open(args.config) as f:
            config_content = f.read()
            linter_config.update(yaml.safe_load(config_content))

    if args.fix:
        linter_config["enable_fixes"] = True
    if args.ignore_paths:
        linter_config["ignore_paths"] = args.ignore_paths
    if args.fail_severity:
        linter_config["fail_severity"] = SeverityLevel[args.fail_severity]
    if args.filter:
        linter_config["disabled_rule_codes"] = [code for code in all_rule_codes if code not in args.filter]

    linter = PhoebusLinter(**linter_config)

    logger.info(f"PhoebusLint version: {__version__}")

    results = {}
    num_fixable = 0
    for path_str in args.paths:
        path = Path(path_str)
        if path.is_file() and path.suffix == ".bob":
            results, num_fixable = linter.lint_file(path, visited=results, num_fixable=num_fixable)
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
