import os
from onssetmaster.runner import scenario



def onsset1():
    
    specs_path = os.path.join('onssetmaster', 'Bolivia', 'specs_paper_new.xlsx')
    calibrated_csv_path = os.path.join('onssetmaster', 'Bolivia', 'Database_new_2.csv')
    results_folder = os.path.join('onssetmaster', 'Bolivia')
    summary_folder	= os.path.join('onssetmaster', 'Bolivia')
    
    scenario(specs_path, calibrated_csv_path, results_folder, summary_folder)

# 'Database_lower_ElecPopCalib.csv'
# 'Database_new_1.csv'
#  PopEndYear 1 !choose high or low population, 0 is for low population
# 'GridConnectionsLimitThousands'  9999999
# 'AutoIntensificationKM' 0
# 'NewGridGenerationCapacityAnnualLimitMW' 1000
# Change the name of column ElecPop to ElecPopCalib
# project_life = int(end_year - self.base_year + 1) in get_lcoe
# step = int(start_year - self.base_year) in get_lcoe
# if wind is equal to 0, the invesment in that row is nan, leading to a lot of problems in the summary.csv
# print(self.capacity_factor)  for   installed_capacity = peak_load / self.capacity_factor
#check the hydro =>A df with all hydro-power sites, to ensure that they aren't assigned more capacity than is available

#data = pd.read_csv('Bolivia/Database_new_1.csv')  
#
#
#
#foo = np.where(data['FinalElecCode2012']==1,1,0)
#
#new_elec_pop = np.where(foo == 0,data['ElecPopCalib']*0,data['ElecPopCalib'])
#
#total_Un_Elec_pop = data['Pop2030High'].sum() - new_elec_pop.sum()
#total_Un_Elec_pop_initial =  data['Pop2030High'].sum() - data['ElecPopCalib'].sum()
    