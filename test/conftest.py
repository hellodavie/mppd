from pathlib import Path
from sys import executable
import pytest

pytest_plugins = "pytester"

SCRIPT_RELATIVE_PATH = "../mips.py"
SCRIPT_PATH = Path(__file__).parent / SCRIPT_RELATIVE_PATH

import os

os.environ['COVERAGE_PROCESS_START'] = str(Path(__file__).parent / "../.coveragerc")
os.environ['COVERAGE_RCFILE'] = str(Path(__file__).parent / "../.coverage-out")


@pytest.fixture
def run_mips(testdir):
    def do_run(*args):
        args = [executable, SCRIPT_PATH] + list(args)
        return testdir.run(*args)

    return do_run
