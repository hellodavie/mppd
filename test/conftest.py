import pytest

pytest_plugins = "pytester"


class Utils:
    @staticmethod
    def remove_whitespace(s):
        return s.translate(s.maketrans('', '', ' \n\t\r'))


@pytest.fixture
def util():
    return Utils
