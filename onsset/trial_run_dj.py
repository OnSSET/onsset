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
# choice = int(input('Enter 1 to prepare/calibrate the GIS input file, 2 to run scenario(s): '))


if choice == 1:
    messagebox.showinfo('OnSSET', 'Open the specs file')
    specs_path = filedialog.askopenfilename()
    specs = pd.read_excel(specs_path, index_col=0)

    messagebox.showinfo('OnSSET', 'Open the file containing separated countries')
    csv_path = filedialog.askopenfilename()

    messagebox.showinfo('OnSSET', 'Browse to result folder and name the calibrated file')
    calibrated_csv_path = filedialog.asksaveasfilename()
    calibrated_csv_path = calibrated_csv_path + '.csv'

    messagebox.showinfo('OnSSET', 'Browse to result folder and name the calibrated specs file')
    specs_path_calib = filedialog.asksaveasfilename()
    specs_path_calib = specs_path_calib + '.xlsx'

    calibration(specs_path, csv_path, specs_path_calib, calibrated_csv_path)

elif choice == 2:
    specs_path = r'C:\GitHub\OnSSET\Results\dj-calib-specs.xlsx'
    calibrated_csv_path = r'C:\GitHub\OnSSET\Results\dj-calib.csv'
    results_folder = r'C:\GitHub\OnSSET\Results'
    summary_folder = r'C:\GitHub\OnSSET\Results'

    scenario(specs_path, calibrated_csv_path, results_folder, summary_folder)
