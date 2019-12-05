"""Performs a regression test of the OnSSET modules

Notes
-----

Run ``python test/test_runner.py`` to update the test files,
if an intended modification is made to the codebase which
changes the contents of the output files.

"""

import filecmp
import os
from shutil import copyfile
from tempfile import TemporaryDirectory

from onsset.runner import calibration, scenario


def run_analysis(tmpdir):
    """

    Arguments
    ---------
    tmpdir : str
        Temporary directory to use for the calculated files

    Returns
    -------
    tuple
        Returns a tuple of bool for whether the summary or full files match

    """

    specs_path = os.path.join('test', 'test_data', 'dj-specs-test.xlsx')
    csv_path = os.path.join('test', 'test_data', 'dj-test.csv')
    calibrated_csv_path = os.path.join(tmpdir, 'dj-calibrated.csv')
    specs_path_calib = os.path.join(tmpdir, 'dj-specs-test-calib.xlsx')

    calibration(specs_path, csv_path, specs_path_calib, calibrated_csv_path)

    scenario(specs_path_calib, calibrated_csv_path, tmpdir, tmpdir)

    actual = os.path.join(tmpdir, 'dj-1-1_1_1_1_0_0_summary.csv')
    expected = os.path.join('test', 'test_results', 'expected_summary.csv')
    summary = filecmp.cmp(actual, expected)

    actual = os.path.join(tmpdir, 'dj-1-1_1_1_1_0_0.csv')
    expected = os.path.join('test', 'test_results', 'expected_full.csv')
    full = filecmp.cmp(actual, expected)
    return summary, full


def test_regression_summary():
    """A regression test to track changes to the summary results of OnSSET

    """

    with TemporaryDirectory() as tmpdir:
        summary, full = run_analysis(tmpdir)

    assert summary
    assert full


def update_test_file():
    """A utility function to produce a new test file if intended changes are made
    """
    tmpdir = '.'

    summary, actual = run_analysis(tmpdir)

    actual = os.path.join(tmpdir, 'dj-1-1_1_1_1_0_0_summary.csv')
    expected = os.path.join('test', 'test_results', 'expected_summary.csv')
    if not summary:
        copyfile(actual, expected)

    actual = os.path.join(tmpdir, 'dj-1-1_1_1_1_0_0.csv')
    expected = os.path.join('test', 'test_results', 'expected_full.csv')
    if not actual:
        copyfile(actual, expected)


if __name__ == '__main__':

    update_test_file()
