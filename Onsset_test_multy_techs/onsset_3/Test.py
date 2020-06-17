#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May  8 20:49:46 2020

@author: balderrama
"""

from onsset.Bolivia_runner import onsset
from onssetmaster.Bolivia_runner import onsset1

import pandas as pd


''' 

copy from onsset 2, comparison with onssset master lower price for wind and hydro
different names

'''


onsset()
onsset1()


year = [2020,2030]
#%%
summary = pd.read_csv('onsset/Bolivia/bo-1-0_0_0_0_0_0_summary.csv', index_col=0)  
summary1 = pd.read_csv('onssetmaster/Bolivia/bo-1-0_0_0_0_0_0_summary.csv', index_col=0)

summary1 = summary1.rename(index={'1.Population_MG_Wind' : '1.Population_MG_Wind1'})
summary1 = summary1.rename(index={'1.Population_MG_Hydro': '1.Population_MG_Hydro1'})

summary1 = summary1.rename(index={'2.New_Connections_MG_Wind' : '2.New_Connections_MG_Wind1'})
summary1 = summary1.rename(index={'2.New_Connections_MG_Hydro': '2.New_Connections_MG_Hydro1'})

summary1 = summary1.rename(index={'3.Capacity_MG_Wind' : '3.Capacity_MG_Wind1'})
summary1 = summary1.rename(index={'3.Capacity_MG_Hydro': '3.Capacity_MG_Hydro1'})

summary1 = summary1.rename(index={'4.Investment_MG_Wind' : '4.Investment_MG_Wind1'})
summary1 = summary1.rename(index={'4.Investment_MG_Hydro': '4.Investment_MG_Hydro1'})

summary1 = summary1.drop(['1.Population_MG_Hybrid', '2.New_Connections_MG_Hybrid', 
                          '3.Capacity_MG_Hybrid','4.Investment_MG_Hybrid'],axis=0)


summary1 = summary1.reindex(summary.index)



comparation_1 = summary1.equals(summary)
print(comparation_1)
    
for i in summary.columns:        
    
    comparation_2 = summary1[i].sum() == summary[i].sum()        
    print(comparation_2)



#%%

data = pd.read_csv('onsset/Bolivia/bo-1-0_0_0_0_0_0.csv', index_col=0)  
data1 = pd.read_csv('onssetmaster/Bolivia/bo-1-0_0_0_0_0_0.csv', index_col=0)  


data1 = data1.rename(columns={'MG_Hydro2020': 'MG_Hydro12020'})
data1 = data1.rename(columns={'MG_Wind2020': 'MG_Wind12020'})
data1 = data1.rename(columns={'MG_Hydro2030': 'MG_Hydro12030'})
data1 = data1.rename(columns={'MG_Wind2030': 'MG_Wind12030'})

codes = {7: 'MG_Hydro1',
         6: 'MG_Wind1',
         5: 'MG_PV',
         4:'MG_Diesel',
         3:'SA_PV',
         2:'SA_Diesel',
         1:'Grid',
         99:'Non'}

year = [2020,2030]

for j in year:
    for i in data1.index:
        name1 = 'FinalElecCode' + str(j)
        
        code1 = data1[name1][i]
        if code1 == 99:
            data1.loc[i,name1] = codes[code1]
        else:
            data1.loc[i,name1] = codes[code1] + str(j)
     


key_words = ['SADieselFuelCost',	'MGDieselFuelCost',	'MG_Hydro1',	'MG_Wind1',	
                 'MG_PV', 'SA_PV',	'MG_Diesel',  'SA_Diesel', 
                 'Minimum_LCOE_Off_grid', 
                 'Grid', 'MinimumOverallLCOE', 'InvestmentCost', 'NewCapacity', 'FinalElecCode']
    

    
for i in year:
  for j in key_words:
            
            name = j + str(i)
            comparation_1 = data1[name] == data[name]
            comparation_1 = pd.Series(comparation_1).all()
            print(comparation_1)
            if comparation_1 == False:
                print(name + ' 1')
            