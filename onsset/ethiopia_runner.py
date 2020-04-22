import os
from runner import calibration, scenario

specs_path = os.path.join('test', 'test_data', 'dj-specs-test.xlsx')
csv_path = os.path.join('test', 'test_data', 'dj-test.csv')
result_path = os.path.join('test', 'test_data')


scenario(specs_path, csv_path, result_path, result_path)

