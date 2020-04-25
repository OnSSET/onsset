#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 14 21:34:50 2020

@author: balderrama
"""

import pandas as pd
from random import shuffle

#%%
data = pd.read_csv('Bolivia/Database_new.csv')  

# creation of population for the years 2020 and 2030
test = pd.DataFrame()
test['Slopes'] = data['Pop2025High']/data['Pop']
b = (data['Pop2025High'] - data['Pop'])/(2025 - 2012)
test['Interceptors'] =  data['Pop2025High'] - b*2025
test['Pop2025High'] = data['Pop2025High']
test['Pop2025Test'] = test['Interceptors'] + b*2025
test['Pop'] = data['Pop']
test['PopTest'] = test['Interceptors'] + b*2012
test['Pop2020'] = test['Interceptors'] + b*2020
test['Pop2030'] = test['Interceptors'] + b*2030

#print(test['Pop'].sum())
#print(test['Pop2020'].sum())
#print(test['Pop2025High'].sum())
#print(test['Pop2030'].sum())
#print(test['Pop2025High'].sum() - test['Pop2020'].sum())
#print(test['Pop2030'].sum() - test['Pop2025High'].sum())

data['Pop2020High'] = test['Pop2020']
data['Pop2030High'] = test['Pop2030']


# Change the name of column Elecpop to ElecPopCalib
data['ElecPopCalib'] = data['ElecPop']
data.to_csv('Bolivia/Database_new_1.csv')
data = data.drop('ElecPop',axis=1)

# change the wind
data['WindVel'] = 5
data['WindCF'] = 0.3

# Change small mistakes in elecstart 2012

data.loc[7797,  'ElecStart'] = 0
data.loc[9620,  'ElecStart'] = 0
data.loc[13070, 'ElecStart'] = 0

data.to_csv('Bolivia/Database_new_1.csv')

#%%

# analize the ElecStart/ not done yet

data = pd.read_csv('Bolivia/Database_new_1.csv')  


test = pd.DataFrame()

test['Pop'] = data['Pop']
test['ElecPopCalib'] = data['ElecPopCalib']
test['ElecStart'] =  data['ElecStart']
test['FinalElecCode2012'] = data['FinalElecCode2012']







#%%
# Create a new data set with lower electricity penetration

data = pd.read_csv('Bolivia/Database_new_1.csv')  

size  = len(data)
zeros = int(round(size*0.3,0))
ones  = int(round(size*0.7,0)) 

Modificator = [0] * zeros + [1] * ones

shuffle(Modificator)

data['ElecPopCalib'] = data['ElecPopCalib']*Modificator

data.to_csv('Bolivia/Database_lower_ElecPopCalib.csv')










 