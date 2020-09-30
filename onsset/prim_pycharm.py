# Drawing on https://github.com/Project-Platypus/PRIM for scenario discovery PRIM analysis

import prim
import pandas as pd
import matplotlib.pyplot as plt
import os

df = pd.DataFrame(columns = ["grid_cap", "demand", "discount rate", "grid gen cost", "pv cost", "grid strategy", "mini grid compatability"])

country = 'bf'

population = [0, 1, 2]  # grid cap
pv_cost = [1, 2, 3]  # [0, 1, 2, 3, 4] # pv cost ToDo
grid_cost = [1, 2, 3]  # [0, 1, 2, 3, 4] # grid gen cost
discount_rate = [0, 1, 2]  # [0, 1, 2] # discount rate
demand = [0, 1]  # [0, 1] # demand
grid_options = [0]  # [0, 1, 2, 3] Grid strategy
distribution = [0, 1, 2]  # mini grid compatability

lcoe = []
investment = []
grid_pop = []
mg_pop = []

for pop in population:
    for pv in pv_cost:
        for grid in grid_cost:
            for discount in discount_rate:
                for dem in demand:
                    for option in grid_options:
                        for dist in distribution:
                            lcoe_type = 35  # 34 = population weighted, 35 = energy weighted

                            df = df.append({"grid_cap": pop, "demand": dem, "discount rate": discount, "grid gen cost": grid, "pv cost": pv, "grid strategy": option, "mini grid compatability": dist},
                                           ignore_index=True)
                            result_path = os.path.join('C:/Users/asahl/Documents/Scenario_discovery/{}'.format(country),
                                                       '{}-1-{}_{}_{}_{}_{}_{}_{}_summary.csv'.format(country, pop, dem, discount, grid,
                                                                                                   pv, option, dist))
                            result = pd.read_csv(result_path)
                            # lcoe.append(result['2030'].iloc[34])
                            lcoe.append((result['2025'].iloc[lcoe_type] * result['2025'].iloc[lcoe_type-2] + result['2030'].iloc[lcoe_type] *
                                         result['2030'].iloc[lcoe_type-2]) / (result['2025'].iloc[lcoe_type-2] + result['2030'].iloc[lcoe_type-2]))
                            investment.append(result['2025'].iloc[24] + result['2025'].iloc[25] + result['2025'].iloc[26]
                                              + result['2025'].iloc[27] + result['2025'].iloc[28] + result['2025'].iloc[29]
                                              + result['2025'].iloc[30] + result['2025'].iloc[31] + result['2030'].iloc[24] +
                                              result['2030'].iloc[25] + result['2030'].iloc[26]
                                              + result['2030'].iloc[27] + result['2030'].iloc[28] + result['2030'].iloc[29]
                                              + result['2030'].iloc[30] + result['2030'].iloc[31])
                            grid_pop.append(result['2030'].iloc[0])
                            mg_pop.append(result['2030'].iloc[4] + result['2030'].iloc[5] + result['2030'].iloc[6] +
                                          result['2030'].iloc[7])

lcoe = pd.Series(lcoe)  # ToDo
sorted_lcoe = pd.Series(sorted(lcoe)) # /1000000

# lcoe_out = pd.DataFrame(lcoe)
# scenario_name = 'larger_settlements.csv'
# scenario_name_2 = 'larger_settlements_df.csv'
# path_out = os.path.join(r'C:\Users\asahl\Box Sync\PhD\Paper 1 Scenario Discovery\Figures', scenario_name)
# path_2_out = os.path.join(r'C:\Users\asahl\Box Sync\PhD\Paper 1 Scenario Discovery\Figures', scenario_name_2)
# lcoe_out.to_csv(path_out)
# df.to_csv(path_2_out)

sorted_lcoe.plot()

thres = lcoe.quantile(q=0.1)
# thres = 0.265

p = prim.Prim(df, lcoe, threshold=thres, threshold_type="<")

box = p.find_box()
box.show_tradeoff()
plt.show()

a = 1 + 1
