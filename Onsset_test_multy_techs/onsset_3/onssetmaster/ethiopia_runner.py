import os
from runner import calibration, scenario

specs_path = os.path.join('test', 'test_data', 'et-1-specs.xlsx')
csv_path = os.path.join('test', 'test_data', 'et-1-country-inputs.csv')
result_path = os.path.join('test', 'test_data')

scenario(specs_path, csv_path, result_path, result_path)

