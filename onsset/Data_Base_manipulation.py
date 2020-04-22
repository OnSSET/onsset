#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 14 21:34:50 2020

@author: balderrama
"""

import pandas as pd
#%%
data = pd.read_csv('Bolivia/Database_new.csv')  

#%%
data = pd.read_csv('Bolivia/Database_new_1.csv')  
#%%

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


print(test['Pop'].sum())
print(test['Pop2020'].sum())
print(test['Pop2025High'].sum())
print(test['Pop2030'].sum())
print(test['Pop2025High'].sum() - test['Pop2020'].sum())
print(test['Pop2030'].sum() - test['Pop2025High'].sum())

data['Pop2020High'] = test['Pop2020']
data['Pop2030High'] = test['Pop2030']

data.to_csv('Bolivia/Database_new_1.csv')

#%%

# Change the name of column Elecpop to ElecPopCalib
data['ElecPopCalib'] = data['ElecPop']
data.to_csv('Bolivia/Database_new_1.csv')
data = data.drop('ElecPop',axis=1)
data.to_csv('Bolivia/Database_new_1.csv')


#%%

# change the wind
data['WindVel'] = 5
data['WindCF'] = 0.3
data.to_csv('Bolivia/Database_new_1.csv')





















 