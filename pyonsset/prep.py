import pandas as pd
import os
from pyonsset.constants import *

def pop(settlements, specs):
    settlements_csv = os.path.join('Tables', settlements + '.csv')
    country_specs_xlsx = os.path.join('Tables', specs + '.xlsx')

    df = pd.read_csv(settlements_csv)
    country_specs = pd.read_excel(country_specs_xlsx, index_col = 0)

    countries = country_specs.index.values.tolist()

    for c in countries:
        # Calibrate actual population
        pop_tot = float(country_specs.loc[c, SPE_POP])
        pop_sum = df.loc[df.Country == c, SET_POP].sum()
        pop_ratio = pop_tot/pop_sum

        df.loc[df.Country == c, SET_POP_CALIB] = df.loc[df.Country == c].apply(lambda row:
                                                                           row[SET_POP] * pop_ratio
                                                                           , axis=1)

        # Urban split, calibrate to actual value
        count = 0
        target = country_specs.loc[c, SPE_URBAN]
        cutoff = country_specs.loc[c, SPE_URBAN_CUTOFF]
        prev_vals = []

        while True:
            df.loc[df.Country == c, SET_URBAN] = df.loc[df.Country == c].apply(lambda row:
                                                                  1
                                                                  if row[SET_POP_CALIB] > cutoff
                                                                  else 0
                                                                  , axis=1)

            pop_urb = df.ix[df.Country == c][df.loc[df.Country == c][SET_URBAN] == 1][SET_POP_CALIB].sum()
            calculated = pop_urb / pop_tot

            print("{}\t\turban: {}\t\tcutoff: {}".format(c, calculated, cutoff))

            if calculated == 0: calculated = 0.05
            elif calculated == 1: calculated = 0.999

            if abs(calculated - target) < 0.005:
                print('satisfied')
                break
            else: cutoff = sorted([0.005, cutoff - cutoff * 2 *(target-calculated)/target, 10000.0])[1]

            if cutoff in prev_vals:
                print('repeating myself')
                break
            else: prev_vals.append(cutoff)

            if count >= 30:
                print('got to 30')
                break

            count += 1

        country_specs.loc[c, SPE_URBAN_CUTOFF] = cutoff
        country_specs.loc[c, SPE_URBAN_MODELLED] = calculated

        print("{} done urban split".format(c))

        # Project 2030 population
        urban_growth = country_specs.loc[c, SPE_URBAN_GROWTH]
        rural_growth = country_specs.loc[c, SPE_RURAL_GROWTH]

        df.loc[df.Country == c, SET_POP_FUTURE] = df.loc[df.Country == c].apply(lambda row:
                                                                           row[SET_POP_CALIB] * urban_growth
                                                                           if row[SET_URBAN] == 1
                                                                           else row[SET_POP_CALIB] * rural_growth
                                                                           , axis=1)


    df.to_csv(settlements_csv,index=False)
    country_specs.to_excel(country_specs_xlsx)

def elec(settlements, specs):
    settlements_csv = os.path.join('Tables', settlements + '.csv')
    country_specs_xlsx = os.path.join('Tables', specs + '.xlsx')

    df = pd.read_csv(settlements_csv)
    country_specs = pd.read_excel(country_specs_xlsx, index_col = 0)
    countries = country_specs.index.values.tolist()

    for c in countries:
        # Calculate Elec2015
        count = 0
        target = country_specs.loc[c, SPE_ELEC]
        pop_cutoff = country_specs.loc[c, SPE_POP_CUTOFF1]
        min_night_lights = country_specs.loc[c, SPE_MIN_NIGHT_LIGHTS]
        max_grid_dist = country_specs.loc[c, SPE_MAX_GRID_DIST]
        max_road_dist = country_specs.loc[c, SPE_MAX_ROAD_DIST]
        pop_tot = country_specs.loc[c, SPE_POP]

        prev_vals = []

        round_two = False
        pop_round_two = country_specs.loc[c, SPE_POP_CUTOFF2]
        grid_dist_round_two = country_specs.loc[c, SPE_GRID_CUTOFF2]
        road_dist_round_two = country_specs.loc[c, SPE_ROAD_CUTOFF2]



        while True:
            df.loc[df.Country == c, SET_ELEC_CURRENT] = df.loc[df.Country == c].apply(lambda row:
                                                                   1
                                                                   if (row[SET_NIGHT_LIGHTS] > min_night_lights and
                                                                            (row[SET_POP_CALIB] > pop_cutoff or
                                                                            row[SET_GRID_DIST_CURRENT] < max_grid_dist or
                                                                            row[SET_ROAD_DIST] < max_road_dist))
                                                                        or
                                                                      (
                                                                        row[SET_POP_CALIB] > pop_round_two and
                                                                        (
                                                                            row[SET_GRID_DIST_CURRENT] < grid_dist_round_two or
                                                                            row[SET_ROAD_DIST] < road_dist_round_two
                                                                        )
                                                                      )
                                                                   else 0
                                                                   , axis=1)

            pop_elec = df.ix[df.Country == c][df.loc[df.Country == c][SET_ELEC_CURRENT] == 1][SET_POP_CALIB].sum()
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

        country_specs.loc[c, SPE_MIN_NIGHT_LIGHTS] = min_night_lights
        country_specs.loc[c, SPE_MAX_GRID_DIST] = max_grid_dist
        country_specs.loc[c, SPE_MAX_ROAD_DIST] = max_road_dist
        country_specs.loc[c, SPE_ELEC_MODELLED] = calculated
        country_specs.loc[c, SPE_POP_CUTOFF2] = pop_round_two
        country_specs.loc[c, SPE_POP_CUTOFF1] = pop_cutoff


    df.to_csv(settlements_csv,index=False)
    country_specs.to_excel(country_specs_xlsx)