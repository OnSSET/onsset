"""
Contains the functions to set up all columns that aren't scenario-specific
"""

import logging
import pandas as pd
from math import pi, exp, log
from pyonsset.constants import *

logging.basicConfig(format='%(asctime)s\t\t%(message)s', level=logging.DEBUG)


def condition():
    """
    Do any initial data conditioning that may be required.
    """

    logging.info('Starting function prep.condition()')

    # Ensure that the base folder for all csv files exists
    if not os.path.exists(FF_TABLES):
        raise IOError('The main folder has not been set up')

    df = pd.read_csv(FF_SETTLEMENTS)

    logging.info('Replace null values with zero')
    df.fillna(0, inplace=True)

    # Sort the dataframe by country to make it prettier to use
    if df[SET_COUNTRY].iloc[0] != 'Angola':
        logging.info('Sort by country')
        df.sort_values('Country', inplace=True)

    logging.info('Saving to csv')
    df.to_csv(FF_SETTLEMENTS, index=False)

    logging.info('Completed function prep.condition()')


def grid_penalties():
    """
    Do any initial data conditioning that may be required.
    """

    logging.info('Starting function prep.grid_penalties()')

    # Ensure that the base folder for all csv files exists
    if not os.path.exists(FF_TABLES):
        raise IOError('The main folder has not been set up')

    df = pd.read_csv(FF_SETTLEMENTS)

    def classify_road_dist(row):
        road_dist = row[SET_ROAD_DIST]
        if road_dist <= 5: return 5
        elif 5 < road_dist <= 10: return 4
        elif 10 < road_dist <= 25: return 3
        elif 25 < road_dist <= 50: return 2
        elif road_dist > 50: return 1

    def classify_substation_dist(row):
        substation_dist = row[SET_SUBSTATION_DIST]
        if substation_dist <= 1: return 5
        elif 1 < substation_dist <= 5: return 4
        elif 5 < substation_dist <= 10: return 3
        elif 10 < substation_dist <= 50: return 2
        elif substation_dist > 50: return 1

    def classify_land_cover(row):
        land_cover = row[SET_LAND_COVER]
        if land_cover == 0: return 1
        elif land_cover == 1: return 3
        elif land_cover == 2: return 2
        elif land_cover == 3: return 3
        elif land_cover == 4: return 2
        elif land_cover == 5: return 3
        elif land_cover == 6: return 4
        elif land_cover == 7: return 5
        elif land_cover == 8: return 4
        elif land_cover == 9: return 5
        elif land_cover == 10: return 5
        elif land_cover == 11: return 1
        elif land_cover == 12: return 3
        elif land_cover == 13: return 3
        elif land_cover == 14: return 5
        elif land_cover == 15: return 3
        elif land_cover == 16: return 5

    def classify_elevation(row):
        elevation = row[SET_SUBSTATION_DIST]
        if elevation <= 500: return 5
        elif 500 < elevation <= 1000: return 4
        elif 1000 < elevation <= 2000: return 3
        elif 2000 < elevation <= 3000: return 2
        elif elevation > 3000: return 1

    def classify_slope(row):
        slope = row[SET_SUBSTATION_DIST]
        if slope <= 10: return 5
        elif 10 < slope <= 20: return 4
        elif 20 < slope <= 30: return 3
        elif 30 < slope <= 40: return 2
        elif slope > 40: return 1

    logging.info('Classify road dist')
    df[SET_ROAD_DIST_CLASSIFIED] = df.apply(classify_road_dist, axis=1)

    logging.info('Classify substation dist')
    df[SET_SUBSTATION_DIST_CLASSIFIED] = df.apply(classify_substation_dist, axis=1)

    logging.info('Classify land cover')
    df[SET_LAND_COVER_CLASSIFIED] = df.apply(classify_land_cover, axis=1)

    logging.info('Classify elevation')
    df[SET_ELEVATION_CLASSIFIED] = df.apply(classify_elevation, axis=1)

    logging.info('Classify slope')
    df[SET_SLOPE_CLASSIFIED] = df.apply(classify_slope, axis=1)

    logging.info('Combined classification')
    df[SET_COMBINED_CLASSIFICATION] = 0.05 * df[SET_ROAD_DIST_CLASSIFIED] + \
                                  0.09 * df[SET_SUBSTATION_DIST_CLASSIFIED] + \
                                  0.39 * df[SET_LAND_COVER_CLASSIFIED] + \
                                  0.15 * df[SET_ELEVATION_CLASSIFIED] + \
                                  0.32 * df[SET_SLOPE_CLASSIFIED]

    logging.info('Saving to csv')
    df.to_csv(FF_SETTLEMENTS, index=False)

    logging.info('Completed function prep.grid_penalties()')

def wind():
    """
    Calculate the wind capacity factor based on the average wind velocity.
    """

    logging.info('Starting function prep.wind()')

    # Ensure that the base folder for all csv files exists
    if not os.path.exists(FF_TABLES):
        raise IOError('The main folder has not been set up')

    df = pd.read_csv(FF_SETTLEMENTS)

    k = 2
    mu = 0.97
    T = 365.25 * 24
    Uarr = range(1, 26)
    Prated = 600
    hub_height = 45
    data_height = 80
    P = [0, 0, 25, 80, 130, 205, 290, 375, 450, 510, 555, 580,
         595, 597, 600, 600, 600, 600, 600, 600, 600, 600, 600, 600, 600]

    def power_law(u_zr, z, zr):
        return u_zr * (z / zr) ** ((0.37 - 0.088 * log(u_zr)) / (1 - 0.088 * log(zr / 10)))

    def get_wind_cf(row):
        u = row[SET_WINDVEL]
        if u == 0:
            return 0

        else:
            u_mean = power_law(u, hub_height, data_height)

            f = []
            for u in Uarr:
                f.append((pi / 2.0) * (u / u_mean ** 2) * exp((-pi / 4) * (u / u_mean) ** k))

            E = 0
            for i in range(len(Uarr)):
                E += mu * T * P[i] * f[i]

            return E / (Prated * T)

    df[SET_WINDCF] = df.apply(get_wind_cf, axis=1)

    logging.info('Saving to csv')
    df.to_csv(FF_SETTLEMENTS, index=False)

    logging.info('Completed function prep.wind()')


def pop():
    """
    Calibrate the actual current population, the urban split and forecast the future population
    """

    logging.info('Starting function prep.pop()')

    # Ensure that the base folder for all csv files exists
    if not os.path.exists(FF_TABLES):
        raise IOError('The main folder has not been set up')

    df = pd.read_csv(FF_SETTLEMENTS)
    specs = pd.read_excel(FF_SPECS, index_col=0)
    countries = specs.index.values.tolist()

    # Everything is done one country at a time (not so for all modules)
    for c in countries:
        logging.info(c)

        # Calculate the ratio between the actual population and the total population from the GIS layer
        logging.info(' - Calibrate current population')
        pop_actual = float(specs.loc[c, SPE_POP])
        pop_sum = df.loc[df[SET_COUNTRY] == c, SET_POP].sum()
        pop_ratio = pop_actual/pop_sum

        # And use this ratio to calibrate the population in a new column
        df.loc[df[SET_COUNTRY] == c, SET_POP_CALIB] = df.loc[df[SET_COUNTRY] == c].apply(lambda row:
            row[SET_POP] * pop_ratio,
            axis=1)

        # Calculate the urban split, by calibrating the cutoff until the target ratio is achieved
        # Keep looping until it is satisfied or another break conditions is reached
        logging.info(' - Calibrate urban split')
        target = specs.loc[c, SPE_URBAN]
        cutoff = specs.loc[c, SPE_URBAN_CUTOFF]  # Start with a cutoff value from specs
        calculated = 0
        count = 0
        prev_vals = []  # Stores cutoff values that have already been tried to prevent getting stuck in a loop
        accuracy = 0.005
        max_iterations = 30
        while True:
            # Assign the 1 (urban)/0 (rural) values to each cell
            df.loc[df[SET_COUNTRY] == c, SET_URBAN] = df.loc[df[SET_COUNTRY] == c].apply(lambda row:
                1
                if row[SET_POP_CALIB] > cutoff
                else 0,
                axis=1)

            # Get the calculated urban ratio, and limit it to within reasonable boundaries
            pop_urb = df.ix[df[SET_COUNTRY] == c][df.loc[df[SET_COUNTRY] == c][SET_URBAN] == 1][SET_POP_CALIB].sum()
            calculated = pop_urb / pop_actual

            if calculated == 0:
                calculated = 0.05
            elif calculated == 1:
                calculated = 0.999

            if abs(calculated - target) < accuracy:
                logging.info(' - Satisfied')
                break
            else:
                cutoff = sorted([0.005, cutoff - cutoff * 2 * (target-calculated)/target, 10000.0])[1]

            if cutoff in prev_vals:
                logging.info('NOT SATISFIED: repeating myself')
                break
            else:
                prev_vals.append(cutoff)

            if count >= max_iterations:
                logging.info('NOT SATISFIED: got to {}'.format(max_iterations))
                break

            count += 1

        # Save the calibrated cutoff and split so they can be compared
        specs.loc[c, SPE_URBAN_CUTOFF] = cutoff
        specs.loc[c, SPE_URBAN_MODELLED] = calculated

        # Project future population, with separate growth rates for urban and rural
        logging.info(' - Project future population')

        urban_growth = (specs.loc[c, SPE_URBAN_FUTURE] * specs.loc[c, SPE_POP_FUTURE]) / (
            specs.loc[c, SPE_URBAN] * specs.loc[c, SPE_POP])
        rural_growth = ((1 - specs.loc[c, SPE_URBAN_FUTURE]) * specs.loc[c, SPE_POP_FUTURE]) / (
            (1 - specs.loc[c, SPE_URBAN]) * specs.loc[c, SPE_POP])

        df.loc[df[SET_COUNTRY] == c, SET_POP_FUTURE] = df.loc[df[SET_COUNTRY] == c].apply(lambda row:
            row[SET_POP_CALIB] * urban_growth
            if row[SET_URBAN] == 1
            else row[SET_POP_CALIB] * rural_growth,
            axis=1)

    logging.info('Saving to csv')
    df.to_csv(FF_SETTLEMENTS, index=False)
    specs.to_excel(FF_SPECS)

    logging.info('Completed function prep.pop()')


def elec():
    """
    Calibrate the current electrification status, and future 'pre-electrification' status
    """

    logging.info('Starting function prep.elec()')

    # Ensure that the base folder for all csv files exists
    if not os.path.exists(FF_TABLES):
        raise IOError('The main folder has not been set up')

    df = pd.read_csv(FF_SETTLEMENTS)
    country_specs = pd.read_excel(FF_SPECS, index_col=0)
    countries = country_specs.index.values.tolist()

    for c in countries:
        logging.info(c)

        # Calibrate current electrification
        logging.info(' - Calibrating current electrification')
        target = country_specs.loc[c, SPE_ELEC]
        pop_cutoff = country_specs.loc[c, SPE_POP_CUTOFF1]
        min_night_lights = country_specs.loc[c, SPE_MIN_NIGHT_LIGHTS]
        max_grid_dist = country_specs.loc[c, SPE_MAX_GRID_DIST]
        max_road_dist = country_specs.loc[c, SPE_MAX_ROAD_DIST]
        pop_tot = country_specs.loc[c, SPE_POP]
        is_round_two = False
        pop_cutoff2 = country_specs.loc[c, SPE_POP_CUTOFF2]
        grid_cutoff2 = country_specs.loc[c, SPE_GRID_CUTOFF2]
        road_cutoff2 = country_specs.loc[c, SPE_ROAD_CUTOFF2]
        calculated = 0

        count = 0
        prev_vals = []
        accuracy = 0.005
        max_iterations_one = 30
        max_iterations_two = 60
        while True:
            # Assign the 1 (electrified)/0 (un-electrified) values to each cell
            df.loc[df[SET_COUNTRY] == c, SET_ELEC_CURRENT] = df.loc[df[SET_COUNTRY] == c].apply(lambda row:
                1
                if (row[SET_NIGHT_LIGHTS] > min_night_lights and
                    (row[SET_POP_CALIB] > pop_cutoff or
                    row[SET_GRID_DIST_CURRENT] < max_grid_dist or
                    row[SET_ROAD_DIST] < max_road_dist))
                or (row[SET_POP_CALIB] > pop_cutoff2 and
                    (row[SET_GRID_DIST_CURRENT] < grid_cutoff2 or
                    row[SET_ROAD_DIST] < road_cutoff2))
                else 0,
                axis=1)

            # Get the calculated electrified ratio, and limit it to within reasonable boundaries
            pop_elec = df.ix[df[SET_COUNTRY] == c][df.loc[df[SET_COUNTRY] == c][SET_ELEC_CURRENT] == 1][SET_POP_CALIB].sum()
            calculated = pop_elec / pop_tot

            if calculated == 0:
                calculated = 0.01
            elif calculated == 1:
                calculated = 0.99

            if abs(calculated - target) < accuracy:
                logging.info(' - Satisfied')
                break
            elif not is_round_two:
                min_night_lights = sorted([5, min_night_lights-min_night_lights*2*(target-calculated)/target, 60])[1]
                max_grid_dist = sorted([5, max_grid_dist + max_grid_dist * 2 * (target-calculated)/target, 150])[1]
                max_road_dist = sorted([0.5, max_road_dist + max_road_dist * 2 * (target-calculated)/target, 50])[1]
            elif calculated - target < 0:
                pop_cutoff2 = sorted([0.01, pop_cutoff2 - pop_cutoff2 * (target-calculated)/target, 100000])[1]
            elif calculated - target > 0:
                pop_cutoff = sorted([0.01, pop_cutoff - pop_cutoff * 0.5 * (target-calculated)/target, 10000])[1]

            constraints = '{}{}{}{}{}'.format(pop_cutoff, min_night_lights, max_grid_dist, max_road_dist, pop_cutoff2)
            if constraints in prev_vals and not is_round_two:
                logging.info(' - Repeating myself, on to round two')
                prev_vals = []
                is_round_two = True
            elif constraints in prev_vals and is_round_two:
                logging.info('NOT SATISFIED: repeating myself')
                break
            else:
                prev_vals.append(constraints)

            if count >= max_iterations_one and not is_round_two:
                logging.info(' - Got to {}, on to round two'.format(max_iterations_one))
                is_round_two = True
            elif count >= max_iterations_two and is_round_two:
                logging.info('NOT SATISFIED: Got to {}'.format(max_iterations_two))
                break

            count += 1

        country_specs.loc[c, SPE_MIN_NIGHT_LIGHTS] = min_night_lights
        country_specs.loc[c, SPE_MAX_GRID_DIST] = max_grid_dist
        country_specs.loc[c, SPE_MAX_ROAD_DIST] = max_road_dist
        country_specs.loc[c, SPE_ELEC_MODELLED] = calculated
        country_specs.loc[c, SPE_POP_CUTOFF1] = pop_cutoff
        country_specs.loc[c, SPE_POP_CUTOFF2] = pop_cutoff2
        # These two aren't included, as we want to give the algorithm a fresh start each time
        # country_specs.loc[c, SPE_GRID_CUTOFF2] = grid_dist_round_two
        # country_specs.loc[c, SPE_ROAD_CUTOFF2] = road_dist_round_two

    logging.info('Saving to csv')
    df.to_csv(FF_SETTLEMENTS, index=False)
    country_specs.to_excel(FF_SPECS)

    logging.info('Completed function prep.elec()')


if __name__ == "__main__":
    os.chdir('..')
    print('Running as a script')
    choice = int(input('(1) pop, (2) elec, (3) wind: '))
    if choice == 1:
        pop()
    elif choice == 2:
        elec()
    elif choice == 3:
        wind()