"""Provides a GUI for the user to choose input files

This file runs either the calibration or scenario modules in the runner file,
and asks the user to browse to the necessary input files
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
from runner import calibration, scenario

root = tk.Tk()
root.withdraw()
root.attributes("-topmost", True)

choice = 2
specs_path = r'C:\Users\asahl\Box Sync\EGI Energy Systems\06 Projects\2020-05 WB Benin\Work\Least-cost model\Hybrid systems\Data\bj-1-specs.xlsx'

specs = pd.read_excel(specs_path, index_col=0)

calibrated_csv_path = r'C:\Users\asahl\Box Sync\EGI Energy Systems\06 Projects\2020-05 WB Benin\Work\Least-cost model\Hybrid systems\Data\bj-1-country-inputs.csv'

results_folder = r'C:\Users\asahl\Box Sync\EGI Energy Systems\06 Projects\2020-05 WB Benin\Work\Least-cost model\Hybrid systems\Data\Hybrid test results'
summary_folder = r'C:\Users\asahl\Box Sync\EGI Energy Systems\06 Projects\2020-05 WB Benin\Work\Least-cost model\Hybrid systems\Data\Hybrid test results'

scenario(specs_path, calibrated_csv_path, results_folder, summary_folder)
