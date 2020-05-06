import os
from runner import scenario


# 'Database_lower_ElecPopCalib.csv'
# 'Database_new_1.csv'
specs_path = os.path.join('Bolivia', 'specs_paper_new.xlsx')
calibrated_csv_path = os.path.join('Bolivia', 'Database_new_3.csv')
results_folder = os.path.join('Bolivia')
summary_folder	= os.path.join('Bolivia')

scenario(specs_path, calibrated_csv_path, results_folder, summary_folder)


# PopEndYear 1 !choose high or low population, 0 is for low population
# 'GridConnectionsLimitThousands'  9999999
# 'AutoIntensificationKM' 0
# 'NewGridGenerationCapacityAnnualLimitMW' 1000
# Change the name of column ElecPop to ElecPopCalib
# project_life = int(end_year - self.base_year + 1) in get_lcoe
# step = int(start_year - self.base_year) in get_lcoe
# if wind is equal to 0, the invesment in that row is nan, leading to a lot of problems in the summary.csv
# print(self.capacity_factor)  for   installed_capacity = peak_load / self.capacity_factor
#check the hydro =>A df with all hydro-power sites, to ensure that they aren't assigned more capacity than is available
# ask about the grid_cell_area effect on the calculations
# SET_ELEC_FINAL_CODE / SET_DISTRIBUTION_NETWORK 