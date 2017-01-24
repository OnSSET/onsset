# Horizontally combine results files for different scenarios into one huge csv file
# Additional section at the bottom to pick out some extra countries of choice
#
# Author: Christopher Arderne
# Date: 26 November 2016
# Python version: 3.5

import pandas as pd
import os
from pyonsset.onsset import *

os.chdir('..')
os.chdir('db')

scenarios = [1, 2, 3, 4, 5]
diesel = ['low', 'high']
output_dir = 'run_18Dec'
output_africa = 'africa_combined.csv'
output_wb_selection = 'nzt.csv'
country_codes_wb_selection = {'Nigeria': 566, 'Tanzania': 834, 'Zambia': 894}

scenario_codes = {'1low': 'L1', '2low': 'L2', '3low': 'L3', '4low': 'L4', '5low': 'L5',
                  '1high': 'N1', '2high': 'N2', '3high': 'N3', '4high': 'N4', '5high': 'N5'}

cols = ['X', 'Y', 'CountryCode', 'Population', 'Newconnections', 'GridDistCu', 'GridDistPl', 'RoadDist', 'GHI',
        'WindCF', 'Hydropower', 'loce_sa_diesel_low', 'loce_sa_diesel_high', 'HydropowerDist', 'IsUrban',
        'L1', 'L2', 'L3', 'L4', 'L5', 'N1', 'N2', 'N3', 'N4', 'N5',
        'LCOEL1', 'LCOEL2', 'LCOEL3', 'LCOEL4', 'LCOEL5', 'LCOEN1', 'LCOEN2', 'LCOEN3', 'LCOEN4', 'LCOEN5',
        'NewCapacityL1', 'NewCapacityL2', 'NewCapacityL3', 'NewCapacityL4', 'NewCapacityL5',
        'NewCapacityN1', 'NewCapacityN2', 'NewCapacityN3', 'NewCapacityN4', 'NewCapacityN5',
        'InvestmentL1', 'InvestmentL2', 'InvestmentL3', 'InvestmentL4', 'InvestmentL5',
        'InvestmentN1', 'InvestmentN2', 'InvestmentN3', 'InvestmentN4', 'InvestmentN5']
df = pd.DataFrame(columns=cols)

for diesel_tag in diesel:
    for scenario in scenarios:
        print(diesel_tag, scenario)
        df_add = pd.read_csv(os.path.join(output_dir, '{}_{}.csv'.format(scenario, diesel_tag)))
        if scenario == 1 and diesel_tag in 'low':
            df['X'] = df_add[SET_X_DEG]
            df['Y'] = df_add[SET_Y_DEG]
            df['CountryCode'] = df_add[SET_COUNTRY]
            df['Population'] = df_add[SET_POP_FUTURE]
            df['Newconnections'] = df_add[SET_NEW_CONNECTIONS]
            df['GridDistCu'] = df_add[SET_GRID_DIST_CURRENT]
            df['GridDistPl'] = df_add[SET_GRID_DIST_PLANNED]
            df['RoadDist'] = df_add[SET_ROAD_DIST]
            df['GHI'] = df_add[SET_GHI]
            df['WindCF'] = df_add[SET_WINDCF]
            df['Hydropower'] = df_add[SET_HYDRO] * 1000  # convert to Watts
            df['loce_sa_diesel_low'] = df_add[SET_LCOE_SA_DIESEL]
            df['HydropowerDist'] = df_add[SET_HYDRO_DIST]
            df['IsUrban'] = df_add[SET_URBAN]
        elif scenario == 1 and diesel_tag in 'high':
            df['loce_sa_diesel_high'] = df_add[SET_LCOE_SA_DIESEL]

        new1 = scenario_codes['{}{}'.format(scenario, diesel_tag)]
        new2 = 'LCOE{}'.format(new1)
        new3 = 'NewCapacity{}'.format(new1)
        new4 = 'Investment{}'.format(new1)

        df[new1] = df_add[SET_MIN_OVERALL_CODE]
        df[new2] = df_add[SET_MIN_OVERALL_LCOE]
        df[new3] = df_add[SET_NEW_CAPACITY] * 1000  # convert to Watts
        df[new4] = df_add[SET_INVESTMENT_COST]

round_to_int = {'Population': 0, 'NewConnections': 0, 'NewCapacityL1': 0, 'NewCapacityL2': 0, 'NewCapacityL3': 0,
      'NewCapacityL4': 0, 'NewCapacityL5': 0, 'NewCapacityN1': 0, 'NewCapacityN2': 0, 'NewCapacityN3': 0,
      'NewCapacityN4': 0, 'NewCapacityN5': 0, 'InvestmentL1': 0, 'InvestmentL2': 0, 'InvestmentL3': 0,
      'InvestmentL4': 0, 'InvestmentL5': 0, 'InvestmentN1': 0, 'InvestmentN2': 0,
      'InvestmentN3': 0, 'InvestmentN4': 0, 'InvestmentN5': 0}
df = df.round(decimals=round_to_int)

df.to_csv(os.path.join(output_dir, output_africa), index=False)

df_nzt = pd.DataFrame(columns=df.columns.tolist())
for country in country_codes_wb_selection.keys():
    df_nzt.append(df.loc[df['CountryCode'] == country])
    df_nzt.loc[df['CountryCode'] == country, 'CountryCode'] = country_codes_wb_selection[country]

round_to_int = {'CountryCode': 0}
df_nzt = df_nzt.round(decimals=round_to_int)
df_nzt.to_csv(os.path.join(output_dir, output_wb_selection), index=False)
