#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 17 18:57:06 2020

@author: balderrama
"""

import pandas as pd
#%%
data = pd.read_csv('Bolivia/bo-1-0_0_0_0_0_0_summary.csv')  


Total_Population = data[:8]['2025'].sum()
new_conections = data[8:16]['2025'].sum()

#%%
data_2 = pd.read_csv('Bolivia/bo-1-0_0_0_0_0_0.csv')  


#%%

data_3 = pd.read_csv('Bolivia/Old_result.csv')  
