# Runs the modules

import os
from onsset.runner import calibration, scenario
import filecmp

def test_regression():
    specs_path = os.path.join('test_data','dj-specs-test.xlsx')
    csv_path = os.path.join('test_data','dj-test.csv')
    calibrated_csv_path = os.path.join('test_data', 'dj-calibrated.csv')
    specs_path_calib = os.path.join('test_results', 'dj-specs-test-calib.xlsx')
    results_folder = 'test_results'
    summary_folder = 'test_results'

    calibration(specs_path, csv_path, specs_path_calib, calibrated_csv_path)

    scenario(specs_path_calib, calibrated_csv_path, results_folder, summary_folder)

    assert compare_csv()

def compare_csv():

    expected_summary_file = os.path.join('test_results', 'expected_summary.csv')
    summary = os.path.join('test_results', 'dj-1-1_1_1_1_0_0_summary.csv')
    return filecmp.cmp(expected_summary_file, summary)


