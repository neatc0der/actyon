#!/usr/bin/env python
import unittest


def run_tests() -> None:
    # use the default shared TestLoader instance
    test_loader = unittest.TestLoader()

    # use the basic test runner that outputs to sys.stderr
    test_runner = unittest.TextTestRunner()

    # automatically discover all tests in the current dir of the form test*.py
    # NOTE: only works for python 2.7 and later
    test_suite = test_loader.discover('tests')

    # run the test suite
    test_runner.run(test_suite)


if __name__ == '__main__':
    run_tests()
