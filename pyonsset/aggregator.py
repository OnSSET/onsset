# Aggregate 1km2 results into a lower resolution fo easier display
#
# Author: Christopher Arderne
# Date: 26 November 2016
# Python version: 3.5

from math import copysign
from pyonsset.onsset import *

in_file = 'db/Rwanda/1800/Rwanda_1800_high.csv'
out_file = 'db/rwanda_agg.csv'
new_cell_size = 10

df = pd.read_csv(in_file)
df_agg = pd.DataFrame(columns=[SET_X, SET_Y, SET_POP_FUTURE, SET_NEW_CONNECTIONS, 'WeightedLCOE', SET_INVESTMENT_COST,
                               SET_LCOE_GRID, SET_LCOE_MG_HYDRO, SET_LCOE_MG_WIND, SET_LCOE_MG_DIESEL, SET_LCOE_MG_PV,
                               SET_LCOE_SA_DIESEL, SET_LCOE_SA_PV])

hash_table = defaultdict(lambda: defaultdict(list))
for index, row in df.iterrows():
    hash_x = int(row[SET_X] / 10)
    hash_y = int(row[SET_Y] / 10)
    hash_table[hash_x][hash_y].append(index)

for x,row in hash_table.items():
    for y,df_index in row.items():
        new_row = pd.Series()
        new_row[SET_POP_FUTURE] = df.iloc[df_index][SET_POP_FUTURE].sum()
        new_row[SET_NEW_CONNECTIONS] = df.iloc[df_index][SET_NEW_CONNECTIONS].sum()
        new_row[SET_INVESTMENT_COST] = df.iloc[df_index][SET_INVESTMENT_COST].sum()

        new_row[SET_X] = x*new_cell_size + copysign(0.45*new_cell_size, x)
        new_row[SET_Y] = y*new_cell_size + copysign(0.45*new_cell_size, y)

        new_row[SET_LCOE_GRID] = df.iloc[df_index].loc[df[SET_MINIMUM_TECH] == SET_LCOE_GRID][SET_NEW_CONNECTIONS].sum() / new_row['NewConnections']
        new_row[SET_LCOE_MG_HYDRO] = df.iloc[df_index].loc[df[SET_MINIMUM_TECH] == SET_LCOE_MG_HYDRO][SET_NEW_CONNECTIONS].sum() / new_row['NewConnections']
        new_row[SET_LCOE_MG_WIND] = df.iloc[df_index].loc[df[SET_MINIMUM_TECH] == SET_LCOE_MG_WIND][SET_NEW_CONNECTIONS].sum() / new_row['NewConnections']
        new_row[SET_LCOE_MG_DIESEL] = df.iloc[df_index].loc[df[SET_MINIMUM_TECH] == SET_LCOE_MG_DIESEL][SET_NEW_CONNECTIONS].sum() / new_row['NewConnections']
        new_row[SET_LCOE_MG_PV] = df.iloc[df_index].loc[df[SET_MINIMUM_TECH] == SET_LCOE_MG_PV][SET_NEW_CONNECTIONS].sum() / new_row['NewConnections']
        new_row[SET_LCOE_SA_DIESEL] = df.iloc[df_index].loc[df[SET_MINIMUM_TECH] == SET_LCOE_SA_DIESEL][SET_NEW_CONNECTIONS].sum() / new_row['NewConnections']
        new_row[SET_LCOE_SA_PV] = df.iloc[df_index].loc[df[SET_MINIMUM_TECH] == SET_LCOE_SA_PV][SET_NEW_CONNECTIONS].sum() / new_row['NewConnections']

        weighted_sum_lcoes = 0
        for i in df_index:
            weighted_sum_lcoes += df.iloc[i][SET_NEW_CONNECTIONS] * df.iloc[i][SET_MINIMUM_TECH_LCOE]
        new_row['WeightedLCOE'] = weighted_sum_lcoes / new_row[SET_NEW_CONNECTIONS]

        df_agg = df_agg.append(new_row, ignore_index=True)

df_agg.to_csv(out_file, index=False)
