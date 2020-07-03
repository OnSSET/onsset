import os
from runner import scenario



    # 'Database_lower_ElecPopCalib.csv'
    # 'Database_new_1.csv'
specs_path = os.path.join('Bolivia', 'specs_paper_new.xlsx')
calibrated_csv_path = os.path.join('Bolivia', 'Database_new_3.csv')
results_folder = os.path.join('Bolivia')
summary_folder	= os.path.join('Bolivia')
  
scenario(specs_path, calibrated_csv_path, results_folder, summary_folder)
    
