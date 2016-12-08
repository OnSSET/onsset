# Author: Christopher Arderne
# Date: 26 November 2016
# Python version: 3.5


import logging
import pandas as pd
from math import pi, exp, log, ceil, sqrt
from pyproj import Proj
import numpy as np
from collections import defaultdict


logging.basicConfig(format='%(asctime)s\t\t%(message)s', level=logging.DEBUG)


# general
LHV_DIESEL = 9.9445485  # (kWh/l) lower heating value
HOURS_PER_YEAR = 8760
START_YEAR = 2015
END_YEAR = 2030

# settlements file
SET_COUNTRY = 'Country'  # This cannot be changed, lots of code will break
SET_X = 'X'  # Coordinate in kilometres
SET_Y = 'Y'  # Coordinate in kilometres
SET_X_DEG = 'X_deg'
SET_Y_DEG = 'Y_deg'
SET_POP = 'Pop'  # Population in people per point (equally, people per km2)
SET_POP_CALIB = 'PopStartCalibrated'  # Calibrated population to reference year, same units
SET_POP_FUTURE = 'PopFuture'  # Project future population, same units
SET_GRID_DIST_CURRENT = 'GridDistCurrent'  # Distance in km from current grid
SET_GRID_DIST_PLANNED = 'GridDistPlan'  # Distance in km from current and future grid
SET_ROAD_DIST = 'RoadDist'  # Distance in km from road network
SET_NIGHT_LIGHTS = 'NightLights'  # Intensity of night time lights (from NASA), range 0 - 63
SET_TRAVEL_HOURS = 'TravelHours'  # Travel time to large city in hours
SET_GHI = 'GHI'  # Global horizontal irradiance in kWh/m2/day
SET_WINDVEL = 'WindVel'  # Wind velocity in m/s
SET_WINDCF = 'WindCF'  # Wind capacity factor as percentage (range 0 - 1)
SET_HYDRO = 'Hydropower'  # Hydropower potential in kW
SET_HYDRO_DIST = 'HydropowerDist'  # Distance to hydropower site in km
SET_SUBSTATION_DIST = 'SubstationDist'
SET_ELEVATION = 'Elevation'
SET_SLOPE = 'Slope'
SET_LAND_COVER = 'LandCover'
SET_SOLAR_RESTRICTION = 'SolarRestriction'
SET_ROAD_DIST_CLASSIFIED = 'RoadDistClassified'
SET_SUBSTATION_DIST_CLASSIFIED = 'SubstationDistClassified'
SET_ELEVATION_CLASSIFIED = 'ElevationClassified'
SET_SLOPE_CLASSIFIED = 'SlopeClassified'
SET_LAND_COVER_CLASSIFIED = 'LandCoverClassified'
SET_COMBINED_CLASSIFICATION = 'GridClassification'
SET_GRID_PENALTY = 'GridPenalty'
SET_URBAN = 'IsUrban'  # Whether the site is urban (0 or 1)
SET_ELEC_TARGET = 'ElecTarget'
SET_ELEC_PREFIX = 'Elec'
SET_ELEC_CURRENT = 'ElecStart'  # If the site is currently electrified (0 or 1)
SET_ELEC_FUTURE = 'ElecFuture'  # If the site has the potential to be 'easily' electrified in future
SET_NEW_CONNECTIONS = 'NewConnections'  # Number of new people with electricity connections
SET_MIN_GRID_DIST = 'MinGridDist'
SET_LCOE_GRID = 'Grid'  # All lcoes in USD/kWh
SET_LCOE_SA_PV = 'SA_PV'
SET_LCOE_SA_DIESEL = 'SA_Diesel'
SET_LCOE_MG_WIND = 'MG_Wind'
SET_LCOE_MG_DIESEL = 'MG_Diesel'
SET_LCOE_MG_PV = 'MG_PV'
SET_LCOE_MG_HYDRO = 'MG_Hydro'
SET_MINIMUM_TECH = 'MinimumTech'  # The technology with lowest lcoe (excluding grid)
SET_MINIMUM_OVERALL = 'MinimumOverall'  # Same as above, but including grid
SET_MINIMUM_TECH_LCOE = 'MinimumTechLCOE'  # The lcoe value for minimum tech
SET_MINIMUM_OVERALL_LCOE = 'MinimumOverallLCOE'  # The lcoe value for overall minimum
SET_MINIMUM_OVERALL_CODE = 'MinimumOverallCode'  # And a code from 1 - 7 to represent that option
SET_MINIMUM_CATEGORY = 'MinimumCategory'  # The category with minimum lcoe (grid, minigrid or standalone)
SET_NEW_CAPACITY = 'NewCapacity'  # Capacity in kW
SET_INVESTMENT_COST = 'InvestmentCost'  # The investment cost in USD

# summary results
SUM_POPULATION_PREFIX = 'population_'
SUM_NEW_CONNECTIONS_PREFIX = 'new_connections_'
SUM_CAPACITY_PREFIX = 'capacity_'
SUM_INVESTMENT_PREFIX = 'investment_'

# specs file
SPE_COUNTRY = 'Country'
SPE_POP = 'Pop2015'  # The actual population in the base year
SPE_URBAN = 'UrbanRatio2015'  # The ratio of urban population (range 0 - 1) in base year
SPE_POP_FUTURE = 'Pop2030'
SPE_URBAN_FUTURE = 'UrbanRatio2030'
SPE_URBAN_MODELLED = 'UrbanRatioModelled'  # The urban ratio in the model after calibration (for comparison)
SPE_URBAN_CUTOFF = 'UrbanCutOff'  # The urban cutoff population calirated by the model, in people per km2
SPE_URBAN_GROWTH = 'UrbanGrowth'  # The urban growth rate as a simple multplier (urban pop future / urban pop present)
SPE_RURAL_GROWTH = 'RuralGrowth'  # Same as for urban
SPE_NUM_PEOPLE_PER_HH = 'NumPeoplePerHH'
SPE_DIESEL_PRICE_LOW = 'DieselPriceLow'  # Diesel price in USD/litre
SPE_DIESEL_PRICE_HIGH = 'DieselPriceHigh'  # Same, with a high forecast var
SPE_GRID_PRICE = 'GridPrice'  # Grid price of electricity in USD/kWh
SPE_GRID_CAPACITY_INVESTMENT = 'GridCapacityInvestmentCost'  # grid capacity investments costs from TEMBA USD/kW
SPE_GRID_LOSSES = 'GridLosses'  # As a ratio (0 - 1)
SPE_BASE_TO_PEAK = 'BaseToPeak'  # As a ratio (0 - 1)
SPE_EXISTING_GRID_COST_RATIO = 'ExistingGridCostRatio'
SPE_MAX_GRID_DIST = 'MaxGridDist'
SPE_ELEC = 'ElecActual'  # Actual current percentage electrified population (0 - 1)
SPE_ELEC_MODELLED = 'ElecModelled'  # The modelled version after calibration (for comparison)
SPE_MIN_NIGHT_LIGHTS = 'MinNightLights'
SPE_MAX_GRID_EXTENSION_DIST = 'MaxGridExtensionDist'
SPE_MAX_ROAD_DIST = 'MaxRoadDist'
SPE_POP_CUTOFF1 = 'PopCutOffRoundOne'
SPE_POP_CUTOFF2 = 'PopCutOffRoundTwo'


def condition_df(df):
    """
    Do any initial data conditioning that may be required.
    """

    logging.info('Ensure that columns that are supposed to be numeric are numeric')
    df[SET_GHI] = pd.to_numeric(df[SET_GHI], errors='coerce')
    df[SET_WINDVEL] = pd.to_numeric(df[SET_WINDVEL], errors='coerce')
    df[SET_NIGHT_LIGHTS] = pd.to_numeric(df[SET_NIGHT_LIGHTS], errors='coerce')
    df[SET_ELEVATION] = pd.to_numeric(df[SET_ELEVATION], errors='coerce')
    df[SET_SLOPE] = pd.to_numeric(df[SET_SLOPE], errors='coerce')
    df[SET_LAND_COVER] = pd.to_numeric(df[SET_LAND_COVER], errors='coerce')
    df[SET_GRID_DIST_CURRENT] = pd.to_numeric(df[SET_GRID_DIST_CURRENT], errors='coerce')
    df[SET_GRID_DIST_PLANNED] = pd.to_numeric(df[SET_GRID_DIST_PLANNED], errors='coerce')
    df[SET_SUBSTATION_DIST] = pd.to_numeric(df[SET_SUBSTATION_DIST], errors='coerce')
    df[SET_ROAD_DIST] = pd.to_numeric(df[SET_ROAD_DIST], errors='coerce')
    df[SET_HYDRO_DIST] = pd.to_numeric(df[SET_HYDRO_DIST], errors='coerce')
    df[SET_HYDRO] = pd.to_numeric(df[SET_HYDRO], errors='coerce')
    df[SET_SOLAR_RESTRICTION] = pd.to_numeric(df[SET_SOLAR_RESTRICTION], errors='coerce')

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


def calc_wind_cfs(df):
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


def calibrate_pop_and_urban(df, pop_actual, pop_future, urban, urban_future, urban_cutoff):
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

    urban_growth = (urban_future * pop_future) / (urban * pop_actual)
    rural_growth = ((1 - urban_future) * pop_future) / ((1 - urban) * pop_actual)

    df[SET_POP_FUTURE] = df.apply(lambda row: row[SET_POP_CALIB] * urban_growth
                                  if row[SET_URBAN] == 1
                                  else row[SET_POP_CALIB] * rural_growth,
                                  axis=1)



    return df, urban_cutoff, urban_modelled


def elec_current_and_future(df, elec_actual, pop_cutoff, min_night_lights, max_grid_dist, max_road_dist, pop_tot, pop_cutoff2):
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

        if abs(elec_modelled - elec_actual) < accuracy:
            break
        elif not is_round_two:
            min_night_lights = sorted([5, min_night_lights - min_night_lights * 2 * (elec_actual - elec_modelled) / elec_actual, 60])[1]
            max_grid_dist = sorted([5, max_grid_dist + max_grid_dist * 2 * (elec_actual - elec_modelled) / elec_actual, 150])[1]
            max_road_dist = sorted([0.5, max_road_dist + max_road_dist * 2 * (elec_actual - elec_modelled) / elec_actual, 50])[1]
        elif elec_modelled - elec_actual < 0:
            pop_cutoff2 = sorted([0.01, pop_cutoff2 - pop_cutoff2 * (elec_actual - elec_modelled) / elec_actual, 100000])[1]
        elif elec_modelled - elec_actual > 0:
            pop_cutoff = sorted([0.01, pop_cutoff - pop_cutoff * 0.5 * (elec_actual - elec_modelled) / elec_actual, 10000])[1]

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


def get_grid_lcoe_table(scenario, max_dist, num_people_per_hh, transmission_losses, base_to_peak_load_ratio,
                        grid_price, grid_capacity_investment, grid_vals):
    """
    Create the LCOES and capital costs for grid and each technology, as well as the number of people required to be
    grid-connected, for each set of parameters.

    @param df:
    @param country_specs:
    @param scenario:
    @param diesel_high
    """

    logging.info('Create grid lcoe tables')

    people_arr_direct = list(range(1000)) + list(range(1000,10000,10)) + list(range(10000,350000,1000))
    elec_dists = range(0, int(max_dist) + 20)
    grid_lcoes = pd.DataFrame(index=elec_dists, columns=people_arr_direct)

    for people in people_arr_direct:
        for additional_mv_line_length in elec_dists:
            grid_lcoes[people][additional_mv_line_length] = calc_lcoe(people=people,
                                                                      scenario=scenario,
                                                                      num_people_per_hh=num_people_per_hh,
                                                                      om_of_td_lines=grid_vals['om_of_td_lines'],
                                                                      distribution_losses=transmission_losses,
                                                                      connection_cost_per_hh=grid_vals['connection_cost_per_hh'],
                                                                      base_to_peak_load_ratio=base_to_peak_load_ratio,
                                                                      system_life=grid_vals['system_life'],
                                                                      additional_mv_line_length=additional_mv_line_length,
                                                                      grid_price=grid_price,
                                                                      grid=True,
                                                                      grid_capacity_investment=grid_capacity_investment,
                                                                      calc_cap_only=False)

    return grid_lcoes


def calc_lcoe(people, scenario, num_people_per_hh, om_of_td_lines, distribution_losses, connection_cost_per_hh,
              base_to_peak_load_ratio, system_life, mv_line_length=0, om_costs=0.0, capital_cost=0, capacity_factor=1.0,
              efficiency=1.0, diesel_price=0.0, additional_mv_line_length=0, grid_price=0.0, grid=False, diesel=False,
              standalone=False, grid_capacity_investment=0.0, calc_cap_only=False):

    # To prevent any div/0 error
    if people == 0:
        if calc_cap_only:
            return 0
        else:
            people = 0.00001

    grid_cell_area = 1  # This was 100, changed to 1 which creates different results but let's go with it

    mv_line_cost = 9000  # USD/km
    lv_line_cost = 5000  # USD/km
    discount_rate = 0.08  # percent
    mv_line_capacity = 50  # kW/line
    lv_line_capacity = 10  # kW/line
    lv_line_max_length = 30  # km
    hv_line_cost = 53000  # USD/km
    mv_line_max_length = 50  # km
    hv_lv_transformer_cost = 5000  # USD/unit
    mv_increase_rate = 0.1  # percentage

    consumption = people / num_people_per_hh * scenario  # kWh/year
    average_load = consumption * (1 + distribution_losses) / HOURS_PER_YEAR
    peak_load = average_load / base_to_peak_load_ratio

    no_mv_lines = peak_load / mv_line_capacity
    no_lv_lines = peak_load / lv_line_capacity
    lv_networks_lim_capacity = no_lv_lines / no_mv_lines
    lv_networks_lim_length = ((grid_cell_area / no_mv_lines) / (lv_line_max_length / sqrt(2))) ** 2
    actual_lv_lines = min([people / num_people_per_hh, max([lv_networks_lim_capacity, lv_networks_lim_length])])
    hh_per_lv_network = (people / num_people_per_hh) / (actual_lv_lines * no_mv_lines)
    lv_unit_length = sqrt(grid_cell_area / (people / num_people_per_hh)) * sqrt(2) / 2
    lv_lines_length_per_lv_network = 1.333 * hh_per_lv_network * lv_unit_length
    total_lv_lines_length = no_mv_lines * actual_lv_lines * lv_lines_length_per_lv_network
    line_reach = (grid_cell_area / no_mv_lines) / (2 * sqrt(grid_cell_area / no_lv_lines))
    total_length_of_lines = min([line_reach, mv_line_max_length]) * no_mv_lines
    additional_hv_lines = max(
        [0, round(sqrt(grid_cell_area) / (2 * min([line_reach, mv_line_max_length])) / 10, 3) - 1])
    hv_lines_total_length = (sqrt(grid_cell_area) / 2) * additional_hv_lines * sqrt(grid_cell_area)
    num_transformers = additional_hv_lines + no_mv_lines + (no_mv_lines * actual_lv_lines)
    generation_per_year = average_load * HOURS_PER_YEAR

    # The investment and O&M costs are different for grid and non-grid solutions
    if grid:
        td_investment_cost = hv_lines_total_length * hv_line_cost + \
                             total_length_of_lines * mv_line_cost + \
                             total_lv_lines_length * lv_line_cost + \
                             num_transformers * hv_lv_transformer_cost + \
                             (people / num_people_per_hh) * connection_cost_per_hh + \
                             additional_mv_line_length * (
                                 mv_line_cost * (1 + mv_increase_rate) ** ((additional_mv_line_length / 5) - 1))
        td_om_cost = td_investment_cost * om_of_td_lines
        total_investment_cost = td_investment_cost
        total_om_cost = td_om_cost

    else:
        total_lv_lines_length *= 0 if standalone else 0.75
        mv_total_line_cost = mv_line_cost * mv_line_length
        lv_total_line_cost = lv_line_cost * total_lv_lines_length
        installed_capacity = peak_load / capacity_factor
        capital_investment = installed_capacity * capital_cost
        td_investment_cost = mv_total_line_cost + lv_total_line_cost + (
                                                                people / num_people_per_hh) * connection_cost_per_hh
        td_om_cost = td_investment_cost * om_of_td_lines
        total_investment_cost = td_investment_cost + capital_investment
        total_om_cost = td_om_cost + (capital_cost * om_costs * installed_capacity)

    # The renewable solutions have no fuel cost
    if diesel:
        fuel_cost = diesel_price / LHV_DIESEL / efficiency
    elif grid:
        fuel_cost = grid_price
    else:
        fuel_cost = 0

    # Perform the time value LCOE calculation

    project_life = END_YEAR - START_YEAR
    reinvest_year = 0
    if system_life < project_life:
        reinvest_year = system_life

    year = np.arange(project_life)
    el_gen = generation_per_year * np.ones(project_life)
    el_gen[0] = 0
    discount_factor = (1 + discount_rate) ** year
    investments = np.zeros(project_life)
    investments[0] = total_investment_cost
    if reinvest_year:
        investments[reinvest_year] = total_investment_cost

    salvage = np.zeros(project_life)
    used_life = project_life
    if reinvest_year:
        used_life = project_life - system_life  # so salvage will come from the remaining life after the re-investment
    salvage[-1] = total_investment_cost * (1 - used_life / system_life)

    operation_and_maintenance = total_om_cost * np.ones(project_life)
    operation_and_maintenance[0] = 0
    fuel = el_gen * fuel_cost
    fuel[0] = 0

    # So we also return the total investment cost for this number of people
    if calc_cap_only:
        discounted_investments = investments / discount_factor
        return np.sum(discounted_investments) + grid_capacity_investment * peak_load
    else:
        discounted_costs = (investments + operation_and_maintenance + fuel - salvage) / discount_factor
        discounted_generation = el_gen / discount_factor
        return np.sum(discounted_costs) / np.sum(discounted_generation)


def separate_elec_status(elec_status):
    """
    Separate out the electrified and unelectrified states from list.

    @param elec_status: electricity status for each location
    """

    electrified = []
    unelectrified = []

    for i, status in enumerate(elec_status):
        if status:
            electrified.append(i)
        else:
            unelectrified.append(i)
    return electrified, unelectrified


def get_2d_hash_table(x, y, unelectrified, distance_limit):
    """
    Generates the 2D Hash Table with the unelectrified locations hashed into the table for easy O(1) access.

    @param x
    @param y
    @param unelectrified
    @param distance_limit: the current distance from grid value being used
    @return:
    """

    hash_table = defaultdict(lambda: defaultdict(list))
    for unelec_row in unelectrified:
        hash_x = int(x[unelec_row] / distance_limit)
        hash_y = int(y[unelec_row] / distance_limit)
        hash_table[hash_x][hash_y].append(unelec_row)
    return hash_table


def get_unelectrified_rows(hash_table, elec_row, x, y, distance_limit):
    """
    Returns all the unelectrified locations close to the electrified location
    based on the distance boundary limit specified by asking the 2D hash table.

    @param hash_table: the hash table created by get_2d_hash_table()
    @param elec_row: the current row being worked on
    @param x: list of X- and Y-values for each cell
    @param y
    @param distance_limit: the current distance from grid value being used
    @return:
    """

    unelec_list = []
    hash_x = int(x[elec_row] / distance_limit)
    hash_y = int(y[elec_row] / distance_limit)

    unelec_list.extend(hash_table.get(hash_x, {}).get(hash_y, []))
    unelec_list.extend(hash_table.get(hash_x, {}).get(hash_y - 1, []))
    unelec_list.extend(hash_table.get(hash_x, {}).get(hash_y + 1, []))

    unelec_list.extend(hash_table.get(hash_x + 1, {}).get(hash_y, []))
    unelec_list.extend(hash_table.get(hash_x + 1, {}).get(hash_y - 1, []))
    unelec_list.extend(hash_table.get(hash_x + 1, {}).get(hash_y + 1, []))

    unelec_list.extend(hash_table.get(hash_x - 1, {}).get(hash_y, []))
    unelec_list.extend(hash_table.get(hash_x - 1, {}).get(hash_y - 1, []))
    unelec_list.extend(hash_table.get(hash_x - 1, {}).get(hash_y + 1, []))

    return unelec_list


def pre_elec(df_country, grid_lcoes_urban, grid_lcoes_rural):
    """

    @param df_country:
    @param grid:
    @return:
    """
    pop = df_country[SET_POP_FUTURE].tolist()
    urban = df_country[SET_URBAN].tolist()
    grid_penalty_ratio = df_country[SET_GRID_PENALTY].tolist()
    status = df_country[SET_ELEC_CURRENT].tolist()
    min_tech_lcoes = df_country[SET_MINIMUM_TECH_LCOE].tolist()
    dist_planned = df_country[SET_GRID_DIST_PLANNED].tolist()

    electrified, unelectrified = separate_elec_status(status)

    for unelec in unelectrified:

        pop_index = pop[unelec]
        if pop_index < 1000: pop_index = int(pop_index)
        elif pop_index < 10000: pop_index = 10 * round(pop_index / 10)
        else: pop_index = 1000 * round(pop_index / 1000)

        if urban[unelec]:
            grid_lcoe = grid_lcoes_urban[pop_index][int(grid_penalty_ratio[unelec] * dist_planned[unelec])]
        else:
            grid_lcoe = grid_lcoes_rural[pop_index][int(grid_penalty_ratio[unelec] * dist_planned[unelec])]

        if grid_lcoe < min_tech_lcoes[unelec]:
            status[unelec] = 1

    return status


def elec_direct(df_country, grid_lcoes_urban, grid_lcoes_rural, existing_grid_cost_ratio, max_dist):
    """

    @param df_country:
    @param grid:
    @param existing_grid_cost_ratio:
    @param max_dist:
    @param parallel:
    @return:
    """
    x = df_country[SET_X].tolist()
    y = df_country[SET_Y].tolist()
    pop = df_country[SET_POP_FUTURE].tolist()
    urban = df_country[SET_URBAN].tolist()
    grid_penalty_ratio = df_country[SET_GRID_PENALTY].tolist()
    status = df_country[SET_ELEC_FUTURE].tolist()
    min_tech_lcoes = df_country[SET_MINIMUM_TECH_LCOE].tolist()
    new_lcoes = df_country[SET_LCOE_GRID].tolist()

    cell_path = np.zeros(len(status)).tolist()
    electrified, unelectrified = separate_elec_status(status)

    loops = 1
    while len(electrified) > 0:
        logging.info('Electrification loop {} with {} electrified'.format(loops, len(electrified)))
        loops += 1
        hash_table = get_2d_hash_table(x, y, unelectrified, max_dist)

        changes = []
        for elec in electrified:
            unelectrified_hashed = get_unelectrified_rows(hash_table, elec, x, y, max_dist)
            for unelec in unelectrified_hashed:
                prev_dist = cell_path[elec]
                dist = sqrt((x[elec] - x[unelec]) ** 2 + (y[elec] - y[unelec]) ** 2)
                if prev_dist + dist < max_dist:

                    pop_index = pop[unelec]
                    if pop_index < 1000:
                        pop_index = int(pop_index)
                    elif pop_index < 10000:
                        pop_index = 10 * round(pop_index / 10)
                    else:
                        pop_index = 1000 * round(pop_index / 1000)

                    if urban[unelec]:
                        grid_lcoe = grid_lcoes_urban[pop_index][int(grid_penalty_ratio[unelec]*(dist + existing_grid_cost_ratio * prev_dist))]
                    else:
                        grid_lcoe = grid_lcoes_rural[pop_index][int(grid_penalty_ratio[unelec] * (dist + existing_grid_cost_ratio * prev_dist))]


                    if grid_lcoe < min_tech_lcoes[unelec]:
                        if grid_lcoe < new_lcoes[unelec]:
                            new_lcoes[unelec] = grid_lcoe
                            cell_path[unelec] = dist + prev_dist
                            # TODO should add fake distance! (what about places electrified with preelec?
                            if unelec not in changes:
                                changes.append(unelec)

        electrified = changes[:]
        unelectrified = [x for x in unelectrified if x not in electrified]

    return new_lcoes, cell_path


def run_elec(df, grid_lcoes_urban, grid_lcoes_rural, grid_price, existing_grid_cost_ratio, max_dist):
    """
    Run the electrification algorithm for the selected scenario and either one country or all.

    @param df
    @param grid_lcoes
    @param grid_price
    @param existing_grid_cost_ratio
    """

    # Calculate 2030 pre-electrification
    logging.info('Determine future pre-electrification status')
    df[SET_ELEC_FUTURE] = df.apply(lambda row: 1 if row[SET_ELEC_CURRENT] == 1 else 0, axis=1)

    pre_elec_dist = 10
    df.loc[df[SET_GRID_DIST_PLANNED] < pre_elec_dist, SET_ELEC_FUTURE] = pre_elec(df.loc[df[SET_GRID_DIST_PLANNED] < pre_elec_dist], grid_lcoes_urban.to_dict(), grid_lcoes_rural.to_dict())

    df[SET_LCOE_GRID] = 99
    df[SET_LCOE_GRID] = df.apply(lambda row: grid_price if row[SET_ELEC_FUTURE] == 1 else 99, axis=1)

    df[SET_LCOE_GRID], df[SET_MIN_GRID_DIST] = elec_direct(df, grid_lcoes_urban.to_dict(), grid_lcoes_rural.to_dict(),
                                                           existing_grid_cost_ratio, max_dist)

    return df


def set_elec_targets(df, scenario_urban, scenario_rural):
    logging.info('Setting electrification targets')
    df.loc[df[SET_URBAN] == 1, SET_ELEC_TARGET] = scenario_urban
    df.loc[df[SET_URBAN] == 0, SET_ELEC_TARGET] = scenario_rural

    return df


def techs_only(df, diesel_price, scenarios, num_people_per_hh, mg_vals, mg_hydro_vals, mg_pv_vals, mg_wind_vals, mg_diesel_vals,
               sa_pv_vals, sa_diesel_vals):
    """

    @param df:
    @param tech_lcoes:
    @param diesel_price:
    @return:
    """

    # Prepare MG_DIESEL
    # Pp = p_lcoe + (2*p_d*consumption*time/volume)*(1/mu)*(1/LHVd)
    consumption_mg_diesel = 33.7
    volume_mg_diesel = 15000
    mu_mg_diesel = 0.3

    # Prepare SA_DIESEL
    # Pp = (p_d + 2*p_d*consumption*time/volume)*(1/mu)*(1/LHVd) + p_om + p_c
    consumption_sa_diesel = 14  # (l/h) truck consumption per hour
    volume_sa_diesel = 300  # (l) volume of truck
    mu_sa_diesel = 0.3  # (kWhth/kWhel) gen efficiency
    p_om_sa_diesel = 0.01  # (USD/kWh) operation, maintenance and amortization

    #TODO Limit hydropower
    #TODO differentiate urban/rural for target, household size...
    logging.info('Calculate minigrid hydro LCOE')
    df[SET_LCOE_MG_HYDRO] = df.apply(
        lambda row: calc_lcoe(people=row[SET_POP_FUTURE],
                                     scenario=scenarios[0] if row[SET_URBAN] else scenarios[1],
                                     num_people_per_hh=num_people_per_hh,
                                     om_of_td_lines=mg_vals['om_of_td_lines'],
                                     capacity_factor=mg_hydro_vals['capacity_factor'],
                                     distribution_losses=mg_vals['distribution_losses'],
                                     connection_cost_per_hh=mg_vals['connection_cost_per_hh'],
                                     capital_cost=mg_hydro_vals['capital_cost'],
                                     om_costs=mg_hydro_vals['om_costs'],
                                     base_to_peak_load_ratio=mg_hydro_vals['base_to_peak_load_ratio'],
                                     system_life=mg_hydro_vals['system_life'],
                                     mv_line_length=row[SET_HYDRO_DIST],
                                     calc_cap_only=False)
        if row[SET_HYDRO_DIST] < 5 else 99, axis=1)

    logging.info('Calculate minigrid PV LCOE')
    df[SET_LCOE_MG_PV] = df.apply(
        lambda row: calc_lcoe(people=row[SET_POP_FUTURE],
                                     scenario=scenarios[0] if row[SET_URBAN] else scenarios[1],
                                     num_people_per_hh=num_people_per_hh,
                                     om_of_td_lines=mg_vals['om_of_td_lines'],
                                     capacity_factor=row[SET_GHI] / HOURS_PER_YEAR,
                                     distribution_losses=mg_vals['distribution_losses'],
                                     connection_cost_per_hh=mg_vals['connection_cost_per_hh'],
                                     capital_cost=mg_pv_vals['capital_cost'],
                                     om_costs=mg_pv_vals['om_costs'],
                                     base_to_peak_load_ratio=mg_pv_vals['base_to_peak_load_ratio'],
                                     system_life=mg_pv_vals['system_life'],
                                     calc_cap_only=False)
        if (row[SET_SOLAR_RESTRICTION] == 1 and row[SET_GHI] > 1000) else 99,
        axis=1)

    logging.info('Calculate minigrid wind LCOE')
    df[SET_LCOE_MG_WIND] = df.apply(
        lambda row: calc_lcoe(people=row[SET_POP_FUTURE],
                                     scenario=scenarios[0] if row[SET_URBAN] else scenarios[1],
                                     num_people_per_hh=num_people_per_hh,
                                     om_of_td_lines=mg_vals['om_of_td_lines'],
                                     capacity_factor=row[SET_WINDCF],
                                     distribution_losses=mg_vals['distribution_losses'],
                                     connection_cost_per_hh=mg_vals['connection_cost_per_hh'],
                                     capital_cost=mg_wind_vals['capital_cost'],
                                     om_costs=mg_wind_vals['om_costs'],
                                     base_to_peak_load_ratio=mg_wind_vals['base_to_peak_load_ratio'],
                                     system_life=mg_wind_vals['system_life'],
                                     calc_cap_only=False)
        if row[SET_WINDCF] > 0.1 else 99,
        axis=1)

    logging.info('Calculate minigrid diesel LCOE')
    df[SET_LCOE_MG_DIESEL] = df.apply(
        lambda row:
        calc_lcoe(people=row[SET_POP_FUTURE],
                         scenario=scenarios[0] if row[SET_URBAN] else scenarios[1],
                         num_people_per_hh=num_people_per_hh,
                         om_of_td_lines=mg_vals['om_of_td_lines'],
                         capacity_factor=mg_diesel_vals['capacity_factor'],
                         distribution_losses=mg_vals['distribution_losses'],
                         connection_cost_per_hh=mg_vals['connection_cost_per_hh'],
                         capital_cost=mg_diesel_vals['capital_cost'],
                         om_costs=mg_diesel_vals['om_costs'],
                         base_to_peak_load_ratio=mg_diesel_vals['base_to_peak_load_ratio'],
                         system_life=mg_diesel_vals['system_life'],
                         efficiency=mg_diesel_vals['efficiency'],
                         diesel_price=diesel_price,
                         diesel=True,
                         calc_cap_only=False) +
        (2 * diesel_price * consumption_mg_diesel * row[SET_TRAVEL_HOURS] / volume_mg_diesel) *
        (1 / mu_mg_diesel) * (1 / LHV_DIESEL),
        axis=1)

    logging.info('Calculate standalone diesel LCOE')
    df[SET_LCOE_SA_DIESEL] = df.apply(
        lambda row:
        (diesel_price + 2 * diesel_price * consumption_sa_diesel * row[SET_TRAVEL_HOURS] / volume_sa_diesel) *
        (1 / mu_sa_diesel) * (1 / LHV_DIESEL) + p_om_sa_diesel + calc_lcoe(people=row[SET_POP_FUTURE],
                                                                                  scenario=scenarios[0] if row[SET_URBAN] else scenarios[1],
                                                                                  num_people_per_hh=num_people_per_hh,
                                                                                  om_of_td_lines=0,
                                                                                  capacity_factor=sa_diesel_vals['capacity_factor'],
                                                                                  distribution_losses=0,
                                                                                  connection_cost_per_hh=0,
                                                                                  capital_cost=sa_diesel_vals['capital_cost'],
                                                                                  om_costs=sa_diesel_vals['om_costs'],
                                                                                  base_to_peak_load_ratio=sa_diesel_vals['base_to_peak_load_ratio'],
                                                                                  system_life=sa_diesel_vals['system_life'],
                                                                                  efficiency=sa_diesel_vals['efficiency'],
                                                                                  diesel_price=diesel_price,
                                                                                  diesel=True,
                                                                                  standalone=True,
                                                                                  calc_cap_only=False),
        axis=1)

    logging.info('Calculate standalone PV LCOE')
    df[SET_LCOE_SA_PV] = df.apply(
        lambda row: calc_lcoe(people=row[SET_POP_FUTURE],
                                     scenario=scenarios[0] if row[SET_URBAN] else scenarios[1],
                                     num_people_per_hh=num_people_per_hh,
                                     om_of_td_lines=0,
                                     capacity_factor=row[SET_GHI]/HOURS_PER_YEAR,
                                     distribution_losses=0,
                                     connection_cost_per_hh=0,
                                     capital_cost=sa_pv_vals['capital_cost'],
                                     om_costs=sa_pv_vals['om_costs'],
                                     base_to_peak_load_ratio=sa_pv_vals['base_to_peak_load_ratio'],
                                     system_life=sa_pv_vals['system_life'],
                                     standalone=True,
                                     calc_cap_only=False)
        if row[SET_GHI] > 1000 else 99,
        axis=1)

    logging.info('Determine minimum technology (no grid)')
    df[SET_MINIMUM_TECH] = df[[SET_LCOE_SA_DIESEL, SET_LCOE_SA_PV, SET_LCOE_MG_WIND,
                               SET_LCOE_MG_DIESEL, SET_LCOE_MG_PV, SET_LCOE_MG_HYDRO]].T.idxmin()

    logging.info('Determine minimum tech LCOE')
    df[SET_MINIMUM_TECH_LCOE] = df.apply(lambda row: (row[row[SET_MINIMUM_TECH]]), axis=1)

    return df


def results_columns(df, scenarios, grid_btp, num_people_per_hh, diesel_price, grid_price,
                    transmission_losses, grid_capacity_investment, grid_vals, mg_vals, mg_hydro_vals,
                    mg_pv_vals, mg_wind_vals, mg_diesel_vals, sa_pv_vals, sa_diesel_vals):

    def res_investment_cost(row):
        min_tech = row[SET_MINIMUM_OVERALL]
        if min_tech == SET_LCOE_SA_DIESEL:
            return calc_lcoe(people=row[SET_NEW_CONNECTIONS],
                                    scenario=scenarios[0] if row[SET_URBAN] else scenarios[1],
                                    num_people_per_hh=num_people_per_hh,
                                    om_of_td_lines=0,
                                    capacity_factor=sa_diesel_vals['capacity_factor'],
                                    distribution_losses=0,
                                    connection_cost_per_hh=0,
                                    capital_cost=sa_diesel_vals['capital_cost'],
                                    om_costs=sa_diesel_vals['om_costs'],
                                    base_to_peak_load_ratio=sa_diesel_vals['base_to_peak_load_ratio'],
                                    system_life=sa_diesel_vals['system_life'],
                                    efficiency=sa_diesel_vals['efficiency'],
                                    diesel_price=diesel_price,
                                    diesel=True,
                                    standalone=True,
                                    calc_cap_only=True)
        elif min_tech == SET_LCOE_SA_PV:
            return calc_lcoe(people=row[SET_NEW_CONNECTIONS],
                                    scenario=scenarios[0] if row[SET_URBAN] else scenarios[1],
                                    num_people_per_hh=num_people_per_hh,
                                    om_of_td_lines=0,
                                    capacity_factor=row[SET_GHI]/HOURS_PER_YEAR,
                                    distribution_losses=0,
                                    connection_cost_per_hh=0,
                                    capital_cost=sa_pv_vals['capital_cost'],
                                    om_costs=sa_pv_vals['om_costs'],
                                    base_to_peak_load_ratio=sa_pv_vals['base_to_peak_load_ratio'],
                                    system_life=sa_pv_vals['system_life'],
                                    standalone=True,
                                    calc_cap_only=True)
        elif min_tech == SET_LCOE_MG_WIND:
            return calc_lcoe(people=row[SET_NEW_CONNECTIONS],
                                    scenario=scenarios[0] if row[SET_URBAN] else scenarios[1],
                                    num_people_per_hh=num_people_per_hh,
                                    om_of_td_lines=mg_vals['om_of_td_lines'],
                                    capacity_factor=row[SET_WINDCF],
                                    distribution_losses=mg_vals['distribution_losses'],
                                    connection_cost_per_hh=mg_vals['connection_cost_per_hh'],
                                    capital_cost=mg_wind_vals['capital_cost'],
                                    om_costs=mg_wind_vals['om_costs'],
                                    base_to_peak_load_ratio=mg_wind_vals['base_to_peak_load_ratio'],
                                    system_life=mg_wind_vals['system_life'],
                                    calc_cap_only=True)
        elif min_tech == SET_LCOE_MG_DIESEL:
            return calc_lcoe(people=row[SET_NEW_CONNECTIONS],
                                    scenario=scenarios[0] if row[SET_URBAN] else scenarios[1],
                                    num_people_per_hh=num_people_per_hh,
                                    om_of_td_lines=mg_vals['om_of_td_lines'],
                                    capacity_factor=mg_diesel_vals['capacity_factor'],
                                    distribution_losses=mg_vals['distribution_losses'],
                                    connection_cost_per_hh=mg_vals['connection_cost_per_hh'],
                                    capital_cost=mg_diesel_vals['capital_cost'],
                                    om_costs=mg_diesel_vals['om_costs'],
                                    base_to_peak_load_ratio=mg_diesel_vals['base_to_peak_load_ratio'],
                                    system_life=mg_diesel_vals['system_life'],
                                    efficiency=mg_diesel_vals['efficiency'],
                                    diesel_price=diesel_price,
                                    diesel=True,
                                    calc_cap_only=True)
        elif min_tech == SET_LCOE_MG_PV:
            return calc_lcoe(people=row[SET_NEW_CONNECTIONS],
                                    scenario=scenarios[0] if row[SET_URBAN] else scenarios[1],
                                    num_people_per_hh=num_people_per_hh,
                                    om_of_td_lines=mg_vals['om_of_td_lines'],
                                    capacity_factor=row[SET_GHI] / HOURS_PER_YEAR,
                                    distribution_losses=mg_vals['distribution_losses'],
                                    connection_cost_per_hh=mg_vals['connection_cost_per_hh'],
                                    capital_cost=mg_pv_vals['capital_cost'],
                                    om_costs=mg_pv_vals['om_costs'],
                                    base_to_peak_load_ratio=mg_pv_vals['base_to_peak_load_ratio'],
                                    system_life=mg_pv_vals['system_life'],
                                    calc_cap_only=True)
        elif min_tech == SET_LCOE_MG_HYDRO:
            return calc_lcoe(people=row[SET_NEW_CONNECTIONS],
                                    scenario=scenarios[0] if row[SET_URBAN] else scenarios[1],
                                    num_people_per_hh=num_people_per_hh,
                                    om_of_td_lines=mg_vals['om_of_td_lines'],
                                    capacity_factor=mg_hydro_vals['capacity_factor'],
                                    distribution_losses=mg_vals['distribution_losses'],
                                    connection_cost_per_hh=mg_vals['connection_cost_per_hh'],
                                    capital_cost=mg_hydro_vals['capital_cost'],
                                    om_costs=mg_hydro_vals['om_costs'],
                                    base_to_peak_load_ratio=mg_hydro_vals['base_to_peak_load_ratio'],
                                    system_life=mg_hydro_vals['system_life'],
                                    mv_line_length=row[SET_HYDRO_DIST],
                                    calc_cap_only=True)
        elif min_tech == SET_LCOE_GRID:
            return calc_lcoe(people=row[SET_NEW_CONNECTIONS],
                                    scenario=scenarios[0] if row[SET_URBAN] else scenarios[1],
                                    num_people_per_hh=num_people_per_hh,
                                    om_of_td_lines=grid_vals['om_of_td_lines'],
                                    distribution_losses=transmission_losses,
                                    connection_cost_per_hh=grid_vals['connection_cost_per_hh'],
                                    base_to_peak_load_ratio=grid_btp,
                                    system_life=grid_vals['system_life'],
                                    additional_mv_line_length=row[SET_MIN_GRID_DIST],
                                    grid_price=grid_price,
                                    grid=True,
                                    grid_capacity_investment=grid_capacity_investment,
                                    calc_cap_only=True)
        else:
            raise ValueError('A technology has not been accounted for in res_investment_cost()')

    logging.info('Determine minimum overall')
    df[SET_MINIMUM_OVERALL] = df[[SET_LCOE_GRID, SET_LCOE_SA_DIESEL, SET_LCOE_SA_PV, SET_LCOE_MG_WIND,
                                  SET_LCOE_MG_DIESEL, SET_LCOE_MG_PV, SET_LCOE_MG_HYDRO]].T.idxmin()

    logging.info('Determine minimum overall LCOE')
    df[SET_MINIMUM_OVERALL_LCOE] = df.apply(lambda row: (row[row[SET_MINIMUM_OVERALL]]), axis=1)

    logging.info('Add technology codes')
    codes = {SET_LCOE_GRID: 1, SET_LCOE_MG_HYDRO: 7, SET_LCOE_MG_WIND: 6, SET_LCOE_MG_PV: 5,
             SET_LCOE_MG_DIESEL: 4, SET_LCOE_SA_DIESEL: 2, SET_LCOE_SA_PV: 3}
    df.loc[df[SET_MINIMUM_OVERALL] == SET_LCOE_GRID, SET_MINIMUM_OVERALL_CODE] = codes[SET_LCOE_GRID]
    df.loc[df[SET_MINIMUM_OVERALL] == SET_LCOE_MG_HYDRO, SET_MINIMUM_OVERALL_CODE] = codes[SET_LCOE_MG_HYDRO]
    df.loc[df[SET_MINIMUM_OVERALL] == SET_LCOE_SA_PV, SET_MINIMUM_OVERALL_CODE] = codes[SET_LCOE_SA_PV]
    df.loc[df[SET_MINIMUM_OVERALL] == SET_LCOE_MG_WIND, SET_MINIMUM_OVERALL_CODE] = codes[SET_LCOE_MG_WIND]
    df.loc[df[SET_MINIMUM_OVERALL] == SET_LCOE_MG_PV, SET_MINIMUM_OVERALL_CODE] = codes[SET_LCOE_MG_PV]
    df.loc[df[SET_MINIMUM_OVERALL] == SET_LCOE_MG_DIESEL, SET_MINIMUM_OVERALL_CODE] = codes[SET_LCOE_MG_DIESEL]
    df.loc[df[SET_MINIMUM_OVERALL] == SET_LCOE_SA_DIESEL, SET_MINIMUM_OVERALL_CODE] = codes[SET_LCOE_SA_DIESEL]

    logging.info('Determine minimum category')
    df[SET_MINIMUM_CATEGORY] = df[SET_MINIMUM_OVERALL].str.extract('(SA|MG|Grid)', expand=False)

    logging.info('Calculate new capacity')
    df.loc[df[SET_MINIMUM_OVERALL] == SET_LCOE_GRID, SET_NEW_CAPACITY] = \
        (df[SET_NEW_CONNECTIONS] * df[SET_ELEC_TARGET] / num_people_per_hh) / (HOURS_PER_YEAR * grid_vals['capacity_factor'] * grid_vals['base_to_peak_load_ratio'])
    df.loc[df[SET_MINIMUM_OVERALL] == SET_LCOE_MG_HYDRO, SET_NEW_CAPACITY] = \
        (df[SET_NEW_CONNECTIONS] * df[SET_ELEC_TARGET] / num_people_per_hh) / (HOURS_PER_YEAR * mg_hydro_vals['capacity_factor'] * mg_hydro_vals['base_to_peak_load_ratio'])
    df.loc[df[SET_MINIMUM_OVERALL] == SET_LCOE_MG_PV, SET_NEW_CAPACITY] = \
        (df[SET_NEW_CONNECTIONS] * df[SET_ELEC_TARGET] / num_people_per_hh) / (HOURS_PER_YEAR * (df[SET_GHI] / HOURS_PER_YEAR) * mg_pv_vals['base_to_peak_load_ratio'])
    df.loc[df[SET_MINIMUM_OVERALL] == SET_LCOE_MG_WIND, SET_NEW_CAPACITY] = \
        (df[SET_NEW_CONNECTIONS] * df[SET_ELEC_TARGET] / num_people_per_hh) / (HOURS_PER_YEAR * df[SET_WINDCF] * mg_wind_vals['base_to_peak_load_ratio'])
    df.loc[df[SET_MINIMUM_OVERALL] == SET_LCOE_MG_DIESEL, SET_NEW_CAPACITY] = \
        (df[SET_NEW_CONNECTIONS] * df[SET_ELEC_TARGET] / num_people_per_hh) / (HOURS_PER_YEAR * mg_diesel_vals['capacity_factor'] * mg_diesel_vals['base_to_peak_load_ratio'])
    df.loc[df[SET_MINIMUM_OVERALL] == SET_LCOE_SA_DIESEL, SET_NEW_CAPACITY] = \
        (df[SET_NEW_CONNECTIONS] * df[SET_ELEC_TARGET] / num_people_per_hh) / (HOURS_PER_YEAR * sa_diesel_vals['capacity_factor'] * sa_diesel_vals['base_to_peak_load_ratio'])
    df.loc[df[SET_MINIMUM_OVERALL] == SET_LCOE_SA_PV, SET_NEW_CAPACITY] = \
        (df[SET_NEW_CONNECTIONS] * df[SET_ELEC_TARGET] / num_people_per_hh) / (HOURS_PER_YEAR * (df[SET_GHI] / HOURS_PER_YEAR) * sa_pv_vals['base_to_peak_load_ratio'])

    logging.info('Calculate investment cost')
    df[SET_INVESTMENT_COST] = df.apply(res_investment_cost, axis=1)

    return df


def calc_summaries(df, country):
    """
    The next section calculates the summaries for technology split, consumption added and total investment cost

    @param df:
    @param country
    """

    logging.info('Calculate summaries')
    rows = []
    techs = [SET_LCOE_GRID, SET_LCOE_SA_DIESEL, SET_LCOE_SA_PV, SET_LCOE_MG_WIND,
             SET_LCOE_MG_DIESEL, SET_LCOE_MG_PV, SET_LCOE_MG_HYDRO]
    rows.extend([SUM_POPULATION_PREFIX + t for t in techs])
    rows.extend([SUM_NEW_CONNECTIONS_PREFIX + t for t in techs])
    rows.extend([SUM_CAPACITY_PREFIX + t for t in techs])
    rows.extend([SUM_INVESTMENT_PREFIX + t for t in techs])
    summary = pd.Series(index=rows, name=country)

    for t in techs:
        summary.loc[SUM_POPULATION_PREFIX + t] = df.loc[df[SET_MINIMUM_OVERALL] == t, SET_POP_FUTURE].sum()
        summary.loc[SUM_NEW_CONNECTIONS_PREFIX + t] = df.loc[df[SET_MINIMUM_OVERALL] == t, SET_NEW_CONNECTIONS].sum()
        summary.loc[SUM_CAPACITY_PREFIX + t] = df.loc[df[SET_MINIMUM_OVERALL] == t, SET_NEW_CAPACITY].sum()
        summary.loc[SUM_INVESTMENT_PREFIX + t] = df.loc[df[SET_MINIMUM_OVERALL] == t, SET_INVESTMENT_COST].sum()

    return summary
