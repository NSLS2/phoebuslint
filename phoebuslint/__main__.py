import argparse
from .config import PhoebusLintConfig
from .linter import PhoebusLinter
from pathlib import Path
from ._version import __version__
import logging

logger = logging.getLogger("phoebuslint")
logging.basicConfig(level=logging.INFO)

def main():
    parser = argparse.ArgumentParser(description="Phoebus operator interface screen linter")
    parser.add_argument(
        "-c", "--config", type=str, help="Path to PhoebusLint configuration file", default=None
    )
    parser.add_argument("paths", nargs="+", help="Paths to .bob files or directories to lint recursively")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("-v", "--version", action="version", version=f"PhoebusLint {__version__}")

    args = parser.parse_args()

    if args.config and Path(args.config).is_file():
        with open(args.config, "r") as f:
            config_content = f.read()
        config = PhoebusLintConfig.from_yaml(config_content)
    else:
        config = PhoebusLintConfig()
    
    linter = PhoebusLinter(config)

    for path_str in args.paths:
        path = Path(path_str)
        if path.is_file() and path.suffix == ".bob":
            linter.lint_file(path)
        elif path.is_dir():
            linter.lint_directory(path)
        else:
            logger.warning(f"Skipping invalid path: {path}")



if __name__ == "__main__":
    main()