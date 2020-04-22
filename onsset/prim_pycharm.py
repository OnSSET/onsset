# Drawing on https://github.com/Project-Platypus/PRIM for scenario discovery PRIM analysis

import prim
import pandas as pd
import matplotlib.pyplot as plt
import os

df = pd.DataFrame(columns = ["pop", "demand", "discount rate", "grid gen cost", "pv cost", "grid strategy", "distribution"])

country = 'lr'

population = [1]
pv_cost = [0, 1, 2, 3, 4]
grid_cost = [0, 1, 2, 3, 4]
discount_rate = [0, 1, 2, 3]
demand = [0]
grid_options = [0, 1, 2]
distribution = [0, 1, 2, 3, 4]

lcoe = []

for pop in population:
    for pv in pv_cost:
        for grid in grid_cost:
            for discount in discount_rate:
                for dem in demand:
                    for option in grid_options:
                        for dist in distribution:
                            df = df.append({"pop": pop, "demand": dem, "discount rate": discount, "grid gen cost": grid, "pv cost": pv, "grid strategy": option, "distribution": dist},
                                           ignore_index=True)
                            result_path = os.path.join('C:/Users/asahl/Box Sync/Scenario_discovery/Summaries/{}'.format(country),
                                                       '{}-1-{}_{}_{}_{}_{}_{}_{}_summary.csv'.format(country, pop, dem, discount, grid,
                                                                                                   pv, option, dist))
                            result = pd.read_csv(result_path)
                            lcoe.append(result['2030'].iloc[34])
                            # lcoe.append((result['2025'].iloc[35] * result['2025'].iloc[33] + result['2030'].iloc[35] *
                            #              result['2030'].iloc[33]) / (result['2025'].iloc[35] + result['2030'].iloc[33]))

lcoe = pd.Series(lcoe)
sorted_lcoe = pd.Series(sorted(lcoe))
sorted_lcoe.plot()

thres = lcoe.quantile(q=0.85)

p = prim.Prim(df, lcoe, threshold=thres, threshold_type=">")

box = p.find_box()
box.show_tradeoff()
plt.show()

a = 1 + 1