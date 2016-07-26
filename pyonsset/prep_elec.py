import pandas as pd
import os

def run(settlements, specs):
    settlements_csv = os.path.join('Tables', settlements)
    country_specs_xlsx = os.path.join('Tables', specs)

    df = pd.read_csv(settlements_csv)
    country_specs = pd.read_excel(country_specs_xlsx, index_col = 0)
    countries = country_specs.index.values.tolist()

    for c in countries:
        # Calculate Elec2015
        count = 0
        target = country_specs.loc[c, 'ElecActual']
        pop_cutoff = country_specs.loc[c, 'PopCutOffRoundOne']
        min_night_lights = country_specs.loc[c, 'MinNightLights']
        max_grid_dist = country_specs.loc[c, 'MaxGridDist']
        max_road_dist = country_specs.loc[c, 'MaxRoadDist']
        pop_tot = country_specs.loc[c, 'Pop2015TotActual']

        prev_vals = []

        round_two = False
        pop_round_two = country_specs.loc[c, 'PopCutOffRoundTwo']
        grid_dist_round_two = country_specs.loc[c, 'GridRoundTwo']
        road_dist_round_two = country_specs.loc[c, 'RoadRoundTwo']



        while True:
            df.loc[df.Country == c, 'Elec2015'] = df.loc[df.Country == c].apply(lambda row:
                                                                   1
                                                                   if (row['NightLights'] > min_night_lights and
                                                                            (row['Pop2015Act'] > pop_cutoff or
                                                                            row['GridDistCurrent'] < max_grid_dist or
                                                                            row['RoadDist'] < max_road_dist))
                                                                        or
                                                                      (
                                                                        row['Pop2015Act'] > pop_round_two and
                                                                        (
                                                                            row['GridDistCurrent'] < grid_dist_round_two or
                                                                            row['RoadDist'] < road_dist_round_two
                                                                        )
                                                                      )
                                                                   else 0
                                                                   , axis=1)

            pop_elec = df.ix[df.Country == c][df.loc[df.Country == c]['Elec2015'] == 1]['Pop2015Act'].sum()
            calculated = pop_elec / pop_tot

            print("{}\telec: {}\tpop_cutoff: {}\tlights: {}\tgrid: {}\troad: {}\tpop round two: {}".format(c, calculated, pop_cutoff,
                                                                                                  min_night_lights,
                                                                                                  max_grid_dist,
                                                                                                  max_road_dist, pop_round_two))

            if calculated == 0: calculated = 0.01
            elif calculated == 1: calculated = 0.99

            if abs(calculated - target) < 0.005:
                print('satisfied')
                break
            elif not round_two:
                min_night_lights = sorted([5.0, min_night_lights - min_night_lights * 2 * (target-calculated)/target, 60.0])[1]
                max_grid_dist = sorted([5000.0, max_grid_dist + max_grid_dist * 2 * (target-calculated)/target, 150000.0])[1]
                max_road_dist = sorted([500.0, max_road_dist + max_road_dist * 2 * (target-calculated)/target, 50000.0])[1]
            elif calculated - target < 0:
                pop_round_two = sorted([0.01, pop_round_two - pop_round_two * (target-calculated)/target, 100000.0])[1]
            else:
                pop_cutoff = sorted([0.01, pop_cutoff - pop_cutoff * 0.5 * (target-calculated)/target, 10000.0])[1]

            constraints = str(pop_cutoff) + str(min_night_lights) + str(max_grid_dist) + str(max_road_dist) + str(pop_round_two)
            if constraints in prev_vals and not round_two:
                print('repeating myself, move to round two')
                prev_vals = []
                round_two = True
            elif constraints in prev_vals and round_two:
                print('repeating myself, all done')
                break
            else:
                prev_vals.append(constraints)

            if count >= 30 and not round_two:
                print('got to 30, move to round two')
                round_two = True
            elif count >= 60 and round_two:
                print('got to 60, all done')
                break

            count += 1

        country_specs.loc[c, 'MinNightLights'] = min_night_lights
        country_specs.loc[c, 'MaxGridDist'] = max_grid_dist
        country_specs.loc[c, 'MaxRoadDist'] = max_road_dist
        country_specs.loc[c, 'ElecModelled'] = calculated
        country_specs.loc[c, 'PopCutOffRoundTwo'] = pop_round_two
        country_specs.loc[c, 'PopCutOffRoundOne'] = pop_cutoff


    df.to_csv(settlements_csv,index=False)
    country_specs.to_excel(country_specs_xlsx)