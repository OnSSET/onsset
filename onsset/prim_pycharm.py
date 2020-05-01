# Drawing on https://github.com/Project-Platypus/PRIM for scenario discovery PRIM analysis

import prim
import pandas as pd
import matplotlib.pyplot as plt
import os

df = pd.DataFrame(columns = ["grid_cap", "demand", "discount rate", "grid gen cost", "pv cost", "grid strategy", "distribution"])

country = 'bf'

population = [0, 1, 2, 3]
pv_cost = [1, 2, 3]
grid_cost = [1, 2, 3]
discount_rate = [0, 1, 2]
demand = [1]
grid_options = [0]
distribution = [2]

lcoe = []

for pop in population:
    for pv in pv_cost:
        for grid in grid_cost:
            for discount in discount_rate:
                for dem in demand:
                    for option in grid_options:
                        for dist in distribution:
                            lcoe_type = 35  # 34 = population weighted, 35 = energy weighted

                            df = df.append({"grid_cap": pop, "demand": dem, "discount rate": discount, "grid gen cost": grid, "pv cost": pv, "grid strategy": option, "distribution": dist},
                                           ignore_index=True)
                            result_path = os.path.join('C:/Users/asahl/Documents/Scenario_discovery/{}'.format(country),
                                                       '{}-1-{}_{}_{}_{}_{}_{}_{}_summary.csv'.format(country, pop, dem, discount, grid,
                                                                                                   pv, option, dist))
                            result = pd.read_csv(result_path)
                            # lcoe.append(result['2030'].iloc[34])
                            lcoe.append((result['2025'].iloc[lcoe_type] * result['2025'].iloc[lcoe_type-2] + result['2030'].iloc[lcoe_type] *
                                         result['2030'].iloc[lcoe_type-2]) / (result['2025'].iloc[lcoe_type-2] + result['2030'].iloc[lcoe_type-2]))

lcoe = pd.Series(lcoe)
sorted_lcoe = pd.Series(sorted(lcoe))
sorted_lcoe.plot()

thres = lcoe.quantile(q=0.15)

p = prim.Prim(df, lcoe, threshold=thres, threshold_type="<")

box = p.find_box()
box.show_tradeoff()
plt.show()

a = 1 + 1
