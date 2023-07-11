"""Provides a GUI for the user to choose input files

This file runs either the calibration or scenario modules in the runner file,
and asks the user to browse to the necessary input files
"""

import pandas as pd
from runner import calibration, scenario

# messagebox.showinfo('OnSSET', 'Open the specs file')
specs_path = '../test/test_data/dj-specs-test.xlsx'

specs = pd.read_excel(specs_path, index_col=0)

# messagebox.showinfo('OnSSET', 'Open the file containing separated countries')
csv_path = '../test/test_data/dj-test.csv'

calibrated_csv_path = '../test/test_data/dj-test-calibrated.csv'
specs_path_calib = '../test/test_data/dj-specs-test-calibrated.xlsx'

calibration(specs_path, csv_path, specs_path_calib, calibrated_csv_path)

# Run scenarios
calibrated_csv_path = '../test/test_data/dj-test-calibrated.csv'
calibrated_specs_path = '../test/test_data/dj-specs-test-calibrated.xlsx'

results_folder = '../test/test_data'
summary_folder = '../test/test_data'
gis_cost_path = r'C:\Users\asahl\OneDrive - KTH\box_files\PhD\Paper 4 DRC\runs\dj_final_cost.tif'
power_cost_path = r'C:\Users\asahl\OneDrive - KTH\box_files\PhD\Paper 4 DRC\runs\dj_power_cost.tif'

scenario(calibrated_specs_path, calibrated_csv_path, results_folder, summary_folder, gis_cost_path,
         power_cost_path, save_shapefiles=True, gis_grid_extension=True)
