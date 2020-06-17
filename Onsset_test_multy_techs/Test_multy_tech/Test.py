#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May  8 20:49:46 2020

@author: balderrama
"""

from onsset.Bolivia_runner import onsset
from onsset1.Bolivia_runner import onsset1
from onsset2.Bolivia_runner import onsset2
import pandas as pd


''' 

copy from onsset, the first has the values of two technologies and the other two
has one tech separate

two mistakes were fix, in the line that put all the values with WindCF less than 0.1 to 99 of LCOE 
and the line were the hydro power available is detected.

both had variable names SET_tech and were change to tech.name

'''


onsset()
onsset1()
onsset2()


year = [2020,2030]
#%%

data = pd.read_csv('onsset/Bolivia/bo-1-0_0_0_0_0_0.csv', index_col=0)  
data1 = pd.read_csv('onsset1/Bolivia/bo-1-0_0_0_0_0_0.csv', index_col=0)  


key_words = ['SADieselFuelCost',	'MGDieselFuelCost',	'MG_Hydro',	'MG_Wind',	
                 'MG_PV', 'SA_PV',	'MG_Diesel',  'SA_Diesel']
    

    
for i in year:
  for j in key_words:
            
            name = j + str(i)
            comparation_1 = data[name] == data1[name]
            comparation_1 = pd.Series(comparation_1).all()
            print(comparation_1)
            if comparation_1 == False:
                print(name + ' 1')
            
            comparation_2 = data[name].sum() == data1[name].sum()
            print(comparation_2)
            
            if comparation_2 == False:
                print(name + ' 2')
                
#%%
data2 = pd.read_csv('onsset2/Bolivia/bo-1-0_0_0_0_0_0.csv', index_col=0)  


key_words = ['SADieselFuelCost',	'MGDieselFuelCost',	'MG_Hydro1',	'MG_Wind1',	
                 'MG_PV1', 'SA_PV1',	'MG_Diesel1',  'SA_Diesel1']
for i in year:
  for j in key_words:
            
            name = j + str(i)
            comparation_1 = data[name] == data2[name]
            comparation_1 = pd.Series(comparation_1).all()
            print(comparation_1)
            if comparation_1 == False:
                print(name + ' 1')
            
            comparation_2 = data[name].sum() == data2[name].sum()
            print(comparation_2)
            
            if comparation_2 == False:
                print(name + ' 2')


              