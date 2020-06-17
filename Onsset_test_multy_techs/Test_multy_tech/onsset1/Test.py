#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May  8 20:49:46 2020

@author: balderrama
"""

import pandas as pd

#%%
summary1 = pd.read_csv('Bolivia/summary_test_13.csv', index_col=0)  
summary2 = pd.read_csv('Bolivia/bo-1-0_0_0_0_0_0_summary.csv', index_col=0)

summary1 = summary1.drop(['1.Population_MG_Hybrid', '2.New_Connections_MG_Hybrid', 
                          '3.Capacity_MG_Hybrid','4.Investment_MG_Hybrid'],axis=0)


summary1 = summary1.reindex(summary2.index)



comparation_1 = summary1.equals(summary2)
print(comparation_1)
    
for i in summary2.columns:        
    
    comparation_2 = summary1[i].sum() == summary2[i].sum()        
    print(comparation_2)


#%%

data1 = pd.read_csv('Bolivia/Results_test_13.csv', index_col=0)  
data2 = pd.read_csv('Bolivia/bo-1-0_0_0_0_0_0.csv', index_col=0)  

codes = {7: 'MG_Hydro',
         6: 'MG_Wind',
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
     


key_words = ['SADieselFuelCost',	'MGDieselFuelCost',	'MG_Hydro',	'MG_Wind',	
                 'MG_PV', 'SA_PV',	'MG_Diesel',  'SA_Diesel', 
                 'Minimum_LCOE_Off_grid', 
                 'Grid', 'MinimumOverallLCOE', 'InvestmentCost', 'NewCapacity', 'FinalElecCode']
    

    
for i in year:
  for j in key_words:
            
            name = j + str(i)
            comparation_1 = data1[name] == data2[name]
            comparation_1 = pd.Series(comparation_1).all()
            print(comparation_1)
            if comparation_1 == False:
                print(name + ' 1')
            
            comparation_2 = data1[name].sum() == data2[name].sum()
            print(comparation_2)
            
            if comparation_2 == False:
                print(name + ' 2')
