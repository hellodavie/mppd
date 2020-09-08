from pathlib import Path
from sys import executable
import pytest

pytest_plugins = "pytester"

SCRIPT_RELATIVE_PATH = "../mips.py"
SCRIPT_PATH = Path(__file__).parent / SCRIPT_RELATIVE_PATH


@pytest.fixture
def run_mips(testdir):
    def do_run(*args):
        args = [executable, SCRIPT_PATH] + list(args)
        return testdir.run(*args)

    return do_run


class Utils:
    @staticmethod
    def remove_whitespace(s):
        return s.translate(s.maketrans('', '', ' \n\t\r'))


@pytest.fixture
def util():
    return Utils
