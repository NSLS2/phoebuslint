import argparse
import logging
from pathlib import Path

from ._version import __version__
from .linter import PhoebusLinter

logger = logging.getLogger("phoebuslint")
logging.basicConfig(level=logging.INFO)


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
        nargs="+",
        help="Paths to .bob files or directories to lint recursively",
    )
    parser.add_argument(
        "-d", "--debug", action="store_true", help="Enable debug logging"
    )
    parser.add_argument(
        "-v", "--version", action="version", version=f"PhoebusLint {__version__}"
    )
    parser.add_argument("--fix", action="store_true", help="Enable automatic fixes for certain linting issues")

    args = parser.parse_args()

    if args.config and Path(args.config).is_file():
        with open(args.config) as f:
            config_content = f.read()
        linter = PhoebusLinter.from_yaml(config_content)
    else:
        linter = PhoebusLinter(enable_fixes=args.fix)

    print(f"PhoebusLint version: {__version__}")

    results = {}
    for path_str in args.paths:
        path = Path(path_str)
        if path.is_file() and path.suffix == ".bob":
            results.update(linter.lint_file(path))
        elif path.is_dir():
            results.update(linter.lint_directory(path))
        else:
            logger.warning(f"Skipping invalid path: {path}")

    linter.display_linting_report(results)
    if linter.did_linting_pass(results):
        exit(0)
    else:
        exit(1)


if __name__ == "__main__":
    main()
