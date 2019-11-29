"""Performs a regression test of the OnSSET modules

Notes
-----

Run ``python test/test_runner.py`` to update the test files,
if an intended modification is made to the codebase which
changes the contents of the output files.

"""

import os
from shutil import copyfile
from onsset.runner import calibration, scenario
import filecmp
from tempfile import TemporaryDirectory


def test_regression_summary():
    """A regression test to track changes to the summary results of OnSSET

    """
    specs_path = os.path.join('test', 'test_data', 'dj-specs-test.xlsx')
    csv_path = os.path.join('test', 'test_data', 'dj-test.csv')

    with TemporaryDirectory() as tmpdir:

        calibrated_csv_path = os.path.join(tmpdir, 'dj-calibrated.csv')
        specs_path_calib = os.path.join(tmpdir, 'dj-specs-test-calib.xlsx')
        results_folder = tmpdir
        summary_folder = tmpdir

        calibration(specs_path, csv_path, specs_path_calib, calibrated_csv_path)

        scenario(specs_path_calib, calibrated_csv_path, results_folder, summary_folder)

        actual = os.path.join(results_folder, 'dj-1-1_1_1_1_0_0_summary.csv')
        expected = os.path.join('test', 'test_results', 'expected_summary.csv')
        assert filecmp.cmp(actual, expected)

        actual = os.path.join(results_folder, 'dj-1-1_1_1_1_0_0.csv')
        expected = os.path.join('test', 'test_results', 'expected_full.csv')
        assert filecmp.cmp(actual, expected)


def update_test_file():
    """A utility function to produce a new test file if intended changes are made
    """
    specs_path = os.path.join('test', 'test_data', 'dj-specs-test.xlsx')
    csv_path = os.path.join('test', 'test_data', 'dj-test.csv')

    tmpdir = '.'

    calibrated_csv_path = os.path.join(tmpdir, 'dj-calibrated.csv')
    specs_path_calib = os.path.join(tmpdir, 'dj-specs-test-calib.xlsx')
    results_folder = tmpdir
    summary_folder = tmpdir

    calibration(specs_path, csv_path, specs_path_calib, calibrated_csv_path)

    scenario(specs_path_calib, calibrated_csv_path, results_folder, summary_folder)

    actual = os.path.join(results_folder, 'dj-1-1_1_1_1_0_0_summary.csv')
    expected = os.path.join('test', 'test_results', 'expected_summary.csv')
    if not filecmp.cmp(actual, expected):
        copyfile(actual, expected)

    actual = os.path.join(results_folder, 'dj-1-1_1_1_1_0_0.csv')
    expected = os.path.join('test', 'test_results', 'expected_full.csv')
    if not filecmp.cmp(actual, expected):
        copyfile(actual, expected)

if __name__ == '__main__':

    update_test_file()