"""Profile a run of OnSSET using the test datasets

Note, requires that KCacheGrind, or QCacheGrind is installed, along with
the Python script ``pyprof2calltree`` which can be acquired using ``pip``.
"""
import cProfile
import filecmp
import os
from tempfile import TemporaryDirectory

from onsset.runner import calibration, scenario
from pyprof2calltree import convert, visualize


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
    actual = filecmp.cmp(actual, expected)

    return summary, actual


def profile_code():

    pr = cProfile.Profile()
    pr.enable()

    with TemporaryDirectory() as tmpdir:
        run_analysis(tmpdir)

    pr.disable()

    visualize(pr.getstats())                            # run kcachegrind
    convert(pr.getstats(), 'profiling_results.kgrind')  # save for later

    assert 0


if __name__ == '__main__':
    profile_code()
