import os
import sys

from setuptools import setup
from setuptools.command.test import test as TestCommand


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


class PyTest(TestCommand):
    user_options = [("pytest-args=", "a", "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest

        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


os.environ.setdefault("DEBUG", "true")
setup(
    name="topica",
    version="0.0.0",
    url="http://github.com/avengerpenguin/topica",
    license="GPL v3",
    author="Ross Fenning",
    author_email="github@rossfenning.co.uk",
    packages=["topica"],
    tests_require=["pytest"],
    cmdclass={"test": PyTest},
)
