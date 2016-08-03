"""
Contains the functions to set up all columns that aren't scenario-specific
"""

import logging
import pandas as pd
from pyonsset.constants import *

logging.basicConfig(format='%(asctime)s\t\t%(message)s', level=logging.DEBUG)


def pop():
    """
    Calibrate the actual current population, the urban split and forecast the future population
    """

    logging.info('Starting function prep.pop()')

    # Ensure that the base folder for all csv files exists
    if not os.path.exists(FF_TABLES):
        raise IOError('The main folder has not been set up')

    df = pd.read_csv(FF_SETTLEMENTS)
    specs = pd.read_excel(FF_SPECS, index_col = 0)
    countries = specs.index.values.tolist()

    # Everything is done one country at a time (not so for all modules)
    for c in countries:
        logging.info(c)

        # Calculate the ratio between the actual population and the total population from the GIS layer
        logging.info('Calibrate current population')
        pop_actual = float(specs.loc[c, SPE_POP])
        pop_sum = df.loc[df.Country == c, SET_POP].sum()
        pop_ratio = pop_actual/pop_sum

        # And use this ratio to calibrate the population in a new column
        df.loc[df.Country == c, SET_POP_CALIB] = df.loc[df.Country == c].apply(lambda row:
            row[SET_POP] * pop_ratio,
            axis=1)

        # Calculate the urban split, by calibrating the cutoff until the target ratio is achieved
        # Keep looping until it is satisfied or another break conditions is reached
        logging.info('Calibrate urban split')
        target = specs.loc[c, SPE_URBAN]
        cutoff = specs.loc[c, SPE_URBAN_CUTOFF] # Start with a cutoff value from specs
        calculated = 0
        count = 0
        prev_vals = [] # Stores cutoff values that have already been tried to prevent getting stuck in a loop
        accuracy = 0.005
        max_iterations = 30
        while True:
            # Assign the 1 (urban)/0 (rural) values to each cell
            df.loc[df.Country == c, SET_URBAN] = df.loc[df.Country == c].apply(lambda row:
                1
                if row[SET_POP_CALIB] > cutoff
                else 0,
                axis=1)

            # Get the calculated urban ratio, and limit it to within reasonable boundaries
            pop_urb = df.ix[df.Country == c][df.loc[df.Country == c][SET_URBAN] == 1][SET_POP_CALIB].sum()
            calculated = pop_urb / pop_actual
            if calculated == 0:
                calculated = 0.05
            elif calculated == 1:
                calculated = 0.999

            if abs(calculated - target) < accuracy:
                logging.info('Satisfied')
                break
            else:
                cutoff = sorted([0.005, cutoff - cutoff * 2 *(target-calculated)/target, 10000.0])[1]

            if cutoff in prev_vals:
                logging.info('Repeating myself, break')
                break
            else:
                prev_vals.append(cutoff)

            if count >= max_iterations:
                logging.info('Got to {}, break'.format(max_iterations))
                break

            count += 1

        # Save the calibrated cutoff and split so they can be compared
        specs.loc[c, SPE_URBAN_CUTOFF] = cutoff
        specs.loc[c, SPE_URBAN_MODELLED] = calculated

        # Project future population, with separate growth rates for urban and rural
        logging.info('Project future population')
        urban_growth = specs.loc[c, SPE_URBAN_GROWTH]
        rural_growth = specs.loc[c, SPE_RURAL_GROWTH]

        df.loc[df.Country == c, SET_POP_FUTURE] = df.loc[df.Country == c].apply(lambda row:
            row[SET_POP_CALIB] * urban_growth
            if row[SET_URBAN] == 1
            else row[SET_POP_CALIB] * rural_growth,
            axis=1)

    df.to_csv(FF_SETTLEMENTS, index=False)
    specs.to_excel(FF_SPECS)

    logging.info('Completed function prep.pop()')


def elec():
    """
    Calibrate the current electrification status, and future 'pre-electrification' status
    """

    logging.info('Starting function prep.pop()')

    # Ensure that the base folder for all csv files exists
    if not os.path.exists(FF_TABLES):
        raise IOError('The main folder has not been set up')

    df = pd.read_csv(FF_SETTLEMENTS)
    country_specs = pd.read_excel(FF_SPECS, index_col = 0)
    countries = country_specs.index.values.tolist()

    for c in countries:
        logging.info(c)

        # Calibrate current electrification
        logging.info('Calibrating current electrification')
        target = country_specs.loc[c, SPE_ELEC]
        pop_cutoff = country_specs.loc[c, SPE_POP_CUTOFF1]
        min_night_lights = country_specs.loc[c, SPE_MIN_NIGHT_LIGHTS]
        max_grid_dist = country_specs.loc[c, SPE_MAX_GRID_DIST]
        max_road_dist = country_specs.loc[c, SPE_MAX_ROAD_DIST]
        pop_tot = country_specs.loc[c, SPE_POP]
        is_round_two = False
        pop_cutoff_round_two = country_specs.loc[c, SPE_POP_CUTOFF2]
        grid_dist_round_two = country_specs.loc[c, SPE_GRID_CUTOFF2]
        road_dist_round_two = country_specs.loc[c, SPE_ROAD_CUTOFF2]
        calculated = 0

        count = 0
        prev_vals = []
        accuracy = 0.005
        max_iterations_one = 30
        max_iterations_two = 30
        while True:
            # Assign the 1 (electrified)/0 (un-electrified) values to each cell
            df.loc[df.Country == c, SET_ELEC_CURRENT] = df.loc[df.Country == c].apply(lambda row:
                1
                if (row[SET_NIGHT_LIGHTS] > min_night_lights and
                    (row[SET_POP_CALIB] > pop_cutoff or
                    row[SET_GRID_DIST_CURRENT] < max_grid_dist or
                    row[SET_ROAD_DIST] < max_road_dist))
                or (row[SET_POP_CALIB] > pop_cutoff_round_two and
                    (row[SET_GRID_DIST_CURRENT] < grid_dist_round_two or
                    row[SET_ROAD_DIST] < road_dist_round_two))
            else 0,
            axis=1)

            # Get the calculated electrified ratio, and limit it to within reasonable boundaries
            pop_elec = df.ix[df.Country == c][df.loc[df.Country == c][SET_ELEC_CURRENT] == 1][SET_POP_CALIB].sum()
            calculated = pop_elec / pop_tot
            if calculated == 0:
                calculated = 0.01
            elif calculated == 1:
                calculated = 0.99

            if abs(calculated - target) < accuracy:
                logging.info('Satisfied')
                break
            elif not is_round_two:
                min_night_lights = sorted([5.0, min_night_lights - min_night_lights * 2 * (target-calculated)/target, 60.0])[1]
                max_grid_dist = sorted([5.0, max_grid_dist + max_grid_dist * 2 * (target-calculated)/target, 150.0])[1]
                max_road_dist = sorted([0.5, max_road_dist + max_road_dist * 2 * (target-calculated)/target, 50.0])[1]
            elif calculated - target < 0:
                pop_cutoff_round_two = sorted([0.01, pop_cutoff_round_two - pop_cutoff_round_two * (target-calculated)/target, 100000.0])[1]
            elif calculated - target > 0:
                pop_cutoff = sorted([0.01, pop_cutoff - pop_cutoff * 0.5 * (target-calculated)/target, 10000.0])[1]

            constraints = str(pop_cutoff) + str(min_night_lights) + str(max_grid_dist) + str(max_road_dist) + str(pop_cutoff_round_two)
            if constraints in prev_vals and not is_round_two:
                logging.info('Repeating myself, on to round two')
                prev_vals = []
                is_round_two = True
            elif constraints in prev_vals and is_round_two:
                logging.info('Repeating myself, break')
                break
            else:
                prev_vals.append(constraints)

            if count >= max_iterations_one and not is_round_two:
                logging.info('Got to {}, on to round two'.format(max_iterations_one))
                is_round_two = True
            elif count >= max_iterations_two and is_round_two:
                logging.info('Got to {}, break'.format(max_iterations_two))
                break

            count += 1

        country_specs.loc[c, SPE_MIN_NIGHT_LIGHTS] = min_night_lights
        country_specs.loc[c, SPE_MAX_GRID_DIST] = max_grid_dist
        country_specs.loc[c, SPE_MAX_ROAD_DIST] = max_road_dist
        country_specs.loc[c, SPE_ELEC_MODELLED] = calculated
        country_specs.loc[c, SPE_POP_CUTOFF1] = pop_cutoff
        country_specs.loc[c, SPE_POP_CUTOFF2] = pop_cutoff_round_two
        # These two aren't included, as we want to give the algorithm a fresh start each time
        # country_specs.loc[c, SPE_GRID_CUTOFF2] = grid_dist_round_two
        # country_specs.loc[c, SPE_ROAD_CUTOFF2] = road_dist_round_two

    logging.info('Saving to csv')
    df.to_csv(FF_SETTLEMENTS, index=False)
    country_specs.to_excel(FF_SPECS)

    logging.info('Completed function prep.elec()')
