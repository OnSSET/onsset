import os
from onsset.runner import scenario



def onsset():
    # 'Database_lower_ElecPopCalib.csv'
    # 'Database_new_1.csv'
    specs_path = os.path.join('onsset','Bolivia', 'specs_paper_new.xlsx')
    calibrated_csv_path = os.path.join('onsset', 'Bolivia', 'Database_new_3.csv')
    results_folder = os.path.join('onsset', 'Bolivia')
    summary_folder	= os.path.join('onsset', 'Bolivia')
    
    scenario(specs_path, calibrated_csv_path, results_folder, summary_folder)
    
