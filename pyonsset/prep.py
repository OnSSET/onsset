# Functions for preparation that doesn't depend on scenario considerations
#
# Author: Christopher Arderne
# Date: 26 November 2016
# Python version: 3.5

import logging
from math import pi, exp, log
from pyproj import Proj
from pyonsset.constants import *

logging.basicConfig(format='%(asctime)s\t\t%(message)s', level=logging.DEBUG)


def condition(df):
    """
    Do any initial data conditioning that may be required.
    """

    logging.info('Replace null values with zero')
    df.fillna(0, inplace=True)

    logging.info('Sort by country, Y and X')
    df.sort_values(by=[SET_COUNTRY, SET_Y, SET_X], inplace=True)

    logging.info('Add columns with location in degrees')
    project = Proj('+proj=merc +lon_0=0 +k=1 +x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m +no_defs')

    def get_x(row):
        x, y = project(row[SET_X] * 1000, row[SET_Y] * 1000, inverse=True)
        return x

    def get_y(row):
        x, y = project(row[SET_X] * 1000, row[SET_Y] * 1000, inverse=True)
        return y

    df[SET_X_DEG] = df.apply(get_x, axis=1)
    df[SET_Y_DEG] = df.apply(get_y, axis=1)

    return df


def grid_penalties(df):
    """
    Do any initial data conditioning that may be required.
    """

    def classify_road_dist(row):
        road_dist = row[SET_ROAD_DIST]
        if road_dist <= 5: return 5
        elif road_dist <= 10: return 4
        elif road_dist <= 25: return 3
        elif road_dist <= 50: return 2
        else: return 1

    def classify_substation_dist(row):
        substation_dist = row[SET_SUBSTATION_DIST]
        if substation_dist <= 0.5: return 5
        elif substation_dist <= 1: return 4
        elif substation_dist <= 5: return 3
        elif substation_dist <= 10: return 2
        else: return 1

    def classify_land_cover(row):
        land_cover = row[SET_LAND_COVER]
        if land_cover == 0: return 1
        elif land_cover == 1: return 3
        elif land_cover == 2: return 4
        elif land_cover == 3: return 3
        elif land_cover == 4: return 4
        elif land_cover == 5: return 3
        elif land_cover == 6: return 2
        elif land_cover == 7: return 5
        elif land_cover == 8: return 2
        elif land_cover == 9: return 5
        elif land_cover == 10: return 5
        elif land_cover == 11: return 1
        elif land_cover == 12: return 3
        elif land_cover == 13: return 3
        elif land_cover == 14: return 5
        elif land_cover == 15: return 3
        elif land_cover == 16: return 5

    def classify_elevation(row):
        elevation = row[SET_ELEVATION]
        if elevation <= 500: return 5
        elif elevation <= 1000: return 4
        elif elevation <= 2000: return 3
        elif elevation <= 3000: return 2
        else: return 1

    def classify_slope(row):
        slope = row[SET_SLOPE]
        if slope <= 10: return 5
        elif slope <= 20: return 4
        elif slope <= 30: return 3
        elif slope <= 40: return 2
        else: return 1

    def set_penalty(row):
        classification = row[SET_COMBINED_CLASSIFICATION]
        return 1 + (exp(0.85 * abs(1 - classification)) - 1) / 100

        #if classification <= 2: return 1.00
        #elif classification <= 3: return 1.02
        #elif classification <= 4: return 1.05
        #else: return 1.10

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
    df[SET_COMBINED_CLASSIFICATION] = (0.05 * df[SET_ROAD_DIST_CLASSIFIED] +
                                       0.09 * df[SET_SUBSTATION_DIST_CLASSIFIED] +
                                       0.39 * df[SET_LAND_COVER_CLASSIFIED] +
                                       0.15 * df[SET_ELEVATION_CLASSIFIED] +
                                       0.32 * df[SET_SLOPE_CLASSIFIED])

    logging.info('Grid penalty')
    df[SET_GRID_PENALTY] = df.apply(set_penalty, axis=1)

    return df


def wind(df):
    """
    Calculate the wind capacity factor based on the average wind velocity.
    """

    mu = 0.97  # availability factor
    t = 8760
    p_rated = 600
    z = 55  # hub height
    zr = 80  # velocity measurement height
    es = 0.85  # losses in wind electricty
    u_arr = range(1, 26)
    p_curve = [0, 0, 0, 0, 30, 77, 135, 208, 287, 371, 450, 514, 558,
               582, 594, 598, 600, 600, 600, 600, 600, 600, 600, 600, 600]

    def get_wind_cf(row):
        u_zr = row[SET_WINDVEL]
        if u_zr == 0:
            return 0

        else:
            # Adjust for the correct hub height
            alpha = (0.37 - 0.088 * log(u_zr)) / (1 - 0.088 * log(zr / 10))
            u_z = u_zr * (z / zr) ** alpha

            # Rayleigh distribution and sum of series
            rayleigh = [(pi / 2) * (u / u_z ** 2) * exp((-pi / 4) * (u / u_z) ** 2) for u in u_arr]
            energy_produced = sum([mu * es * t * p * r for p, r in zip(p_curve, rayleigh)])

            return energy_produced/(p_rated * t)

    logging.info('Calculate Wind CF')
    df[SET_WINDCF] = df.apply(get_wind_cf, axis=1)

    return df


def pop(df, pop_actual, pop_future, urban, urban_future, urban_cutoff):
    """
    Calibrate the actual current population, the urban split and forecast the future population
    """

    # Calculate the ratio between the actual population and the total population from the GIS layer
    logging.info('Calibrate current population')
    pop_ratio = pop_actual/df[SET_POP].sum()

    # And use this ratio to calibrate the population in a new column
    df[SET_POP_CALIB] = df.apply(lambda row: row[SET_POP] * pop_ratio, axis=1)

    # Calculate the urban split, by calibrating the cutoff until the target ratio is achieved
    # Keep looping until it is satisfied or another break conditions is reached
    logging.info('Calibrate urban split')
    count = 0
    prev_vals = []  # Stores cutoff values that have already been tried to prevent getting stuck in a loop
    accuracy = 0.005
    max_iterations = 30
    while True:
        # Assign the 1 (urban)/0 (rural) values to each cell
        df[SET_URBAN] = df.apply(lambda row: 1 if row[SET_POP_CALIB] > urban_cutoff else 0, axis=1)

        # Get the calculated urban ratio, and limit it to within reasonable boundaries
        pop_urb = df.loc[df[SET_URBAN] == 1, SET_POP_CALIB].sum()
        urban_modelled = pop_urb / pop_actual

        if urban_modelled == 0:
            urban_modelled = 0.05
        elif urban_modelled == 1:
            urban_modelled = 0.999

        if abs(urban_modelled - urban) < accuracy:
            break
        else:
            urban_cutoff = sorted([0.005, urban_cutoff - urban_cutoff * 2 * (urban - urban_modelled) / urban, 10000.0])[1]

        if urban_cutoff in prev_vals:
            logging.info('NOT SATISFIED: repeating myself')
            break
        else:
            prev_vals.append(urban_cutoff)

        if count >= max_iterations:
            logging.info('NOT SATISFIED: got to {}'.format(max_iterations))
            break

        count += 1

    # Project future population, with separate growth rates for urban and rural
    logging.info('Project future population')

    urban_growth = (urban_future * pop_future) / (urban * pop)
    rural_growth = ((1 - urban_future) * pop_future) / ((1 - urban) * pop)

    df[SET_POP_FUTURE] = df.apply(lambda row: row[SET_POP_CALIB] * urban_growth
                                  if row[SET_URBAN] == 1
                                  else row[SET_POP_CALIB] * rural_growth,
                                  axis=1)



    return df, urban_cutoff, urban_modelled


def elec_current(df, elec, pop_cutoff, min_night_lights, max_grid_dist, pop_tot, pop_cutoff2):
    """
    Calibrate the current electrification status, and future 'pre-electrification' status
    """

    # Calibrate current electrification
    logging.info('Calibrate current electrification')
    is_round_two = False
    grid_cutoff2 = 10
    road_cutoff2 = 10
    count = 0
    prev_vals = []
    accuracy = 0.005
    max_iterations_one = 30
    max_iterations_two = 60

    while True:
        # Assign the 1 (electrified)/0 (un-electrified) values to each cell
        df[SET_ELEC_CURRENT] = df.apply(lambda row:
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
        pop_elec = df.loc[df[SET_ELEC_CURRENT] == 1, SET_POP_CALIB].sum()
        elec_modelled = pop_elec / pop_tot

        if elec_modelled == 0:
            elec_modelled = 0.01
        elif elec_modelled == 1:
            elec_modelled = 0.99

        if abs(elec_modelled - elec) < accuracy:
            break
        elif not is_round_two:
            min_night_lights = sorted([5, min_night_lights - min_night_lights * 2 * (elec - elec_modelled) / elec, 60])[1]
            max_grid_dist = sorted([5, max_grid_dist + max_grid_dist * 2 * (elec - elec_modelled) / elec, 150])[1]
            max_road_dist = sorted([0.5, max_road_dist + max_road_dist * 2 * (elec - elec_modelled) / elec, 50])[1]
        elif elec_modelled - elec < 0:
            pop_cutoff2 = sorted([0.01, pop_cutoff2 - pop_cutoff2 * (elec - elec_modelled) / elec, 100000])[1]
        elif elec_modelled - elec > 0:
            pop_cutoff = sorted([0.01, pop_cutoff - pop_cutoff * 0.5 * (elec - elec_modelled) / elec, 10000])[1]

        constraints = '{}{}{}{}{}'.format(pop_cutoff, min_night_lights, max_grid_dist, max_road_dist, pop_cutoff2)
        if constraints in prev_vals and not is_round_two:
            logging.info('Repeating myself, on to round two')
            prev_vals = []
            is_round_two = True
        elif constraints in prev_vals and is_round_two:
            logging.info('NOT SATISFIED: repeating myself')
            break
        else:
            prev_vals.append(constraints)

        if count >= max_iterations_one and not is_round_two:
            logging.info('Got to {}, on to round two'.format(max_iterations_one))
            is_round_two = True
        elif count >= max_iterations_two and is_round_two:
            logging.info('NOT SATISFIED: Got to {}'.format(max_iterations_two))
            break

        count += 1

    logging.info('Calculate new connections')
    df.loc[df[SET_ELEC_CURRENT] == 1, SET_NEW_CONNECTIONS] = df[SET_POP_FUTURE] - df[SET_POP_CALIB]
    df.loc[df[SET_ELEC_CURRENT] == 0, SET_NEW_CONNECTIONS] = df[SET_POP_FUTURE]
    df.loc[df[SET_NEW_CONNECTIONS] < 0, SET_NEW_CONNECTIONS] = 0

    return df, min_night_lights, max_grid_dist, max_road_dist, elec_modelled, pop_cutoff, pop_cutoff2
