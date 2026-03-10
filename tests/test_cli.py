import pytest
import subprocess
from phoebuslint._version import __version__

def test_cli_version():
    result = subprocess.run(["phoebuslint", "--version"], capture_output=True, text=True)
    assert result.returncode == 0
    assert result.stdout.strip() == f"PhoebusLint {__version__}"
