# Calculate the cost of the off-grid technologies, the grid extension potential, the lowest overall
# And then calculate the investment costs and create summaries
#
# Author: Christopher Arderne
# Date: 26 November 2016
# Python version: 3.5

import logging
import pandas as pd
import numpy as np
from collections import defaultdict
from math import sqrt

from pyonsset import tables
from pyonsset.constants import *

logging.basicConfig(format='%(asctime)s\t\t%(message)s', level=logging.DEBUG)

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


def pre_elec(df_country, grid):
    """

    @param df_country:
    @param grid:
    @return:
    """
    pop = df_country[SET_POP_FUTURE].tolist()
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

        grid_lcoe = grid[pop_index][int(grid_penalty_ratio[unelec] * dist_planned[unelec])]
        if grid_lcoe < min_tech_lcoes[unelec]:
            status[unelec] = 1

    return status


def elec_direct(df_country, grid, existing_grid_cost_ratio, max_dist):
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

        changes, new_lcoes, cell_path = compare_lcoes(electrified, new_lcoes, min_tech_lcoes,
                                                          cell_path, hash_table, grid, x, y, pop, grid_penalty_ratio,
                                                          max_dist, existing_grid_cost_ratio)

        electrified = changes[:]
        unelectrified = [x for x in unelectrified if x not in electrified]

    return new_lcoes, cell_path


def compare_lcoes(electrified, new_lcoes, min_tech_lcoes, cell_path, hash_table, grid,
                  x, y, pop, grid_penalty_ratio, max_dist, existing_grid_cost_ratio):
    """

    @param electrified:
    @param new_lcoes:
    @param min_tech_lcoes:
    @param cell_path:
    @param hash_table:
    @param grid:
    @param x:
    @param y:
    @param pop:
    @param grid_penalty_ratio:
    @param max_dist
    @param existing_grid_cost_ratio
    @return:
    """

    changes = []
    for elec in electrified:
        unelectrified_hashed = get_unelectrified_rows(hash_table, elec, x, y, max_dist)
        for unelec in unelectrified_hashed:
            prev_dist = cell_path[elec]
            dist = grid_penalty_ratio[unelec] * sqrt((x[elec] - x[unelec]) ** 2 + (y[elec] - y[unelec]) ** 2)
            if prev_dist + dist < max_dist:

                pop_index = pop[unelec]
                if pop_index < 1000: pop_index = int(pop_index)
                elif pop_index < 10000: pop_index = 10 * round(pop_index / 10)
                else: pop_index = 1000 * round(pop_index / 1000)

                grid_lcoe = grid[pop_index][int(dist + existing_grid_cost_ratio * prev_dist)]
                if grid_lcoe < min_tech_lcoes[unelec]:
                    if grid_lcoe < new_lcoes[unelec]:
                        new_lcoes[unelec] = grid_lcoe
                        cell_path[unelec] = dist + prev_dist
                        if unelec not in changes:
                            changes.append(unelec)
    return changes, new_lcoes, cell_path


def run_elec(df, grid_lcoes, grid_price, existing_grid_cost_ratio, max_dist):
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

    df.loc[df[SET_GRID_DIST_PLANNED] < 10, SET_ELEC_FUTURE] = pre_elec(df.loc[df[SET_GRID_DIST_PLANNED] < 10], grid_lcoes.to_dict())

    df[SET_LCOE_GRID] = 99
    df[SET_LCOE_GRID] = df.apply(lambda row: grid_price if row[SET_ELEC_FUTURE] == 1 else 99, axis=1)

    df[SET_LCOE_GRID], df[SET_MIN_GRID_DIST] = elec_direct(df, grid_lcoes.to_dict(),
                                                           existing_grid_cost_ratio, max_dist)

    return df


def techs_only(df, diesel_price, scenario, num_people_per_hh):
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
        lambda row: tables.get_mg_hydro_lcoe(row[SET_POP_FUTURE], scenario, num_people_per_hh, False, row[SET_HYDRO_DIST])
        if row[SET_HYDRO_DIST] < 5 else 99, axis=1)

    logging.info('Calculate minigrid PV LCOE')
    df[SET_LCOE_MG_PV] = df.apply(
        lambda row: tables.get_mg_pv_lcoe(row[SET_POP_FUTURE], scenario, num_people_per_hh, False, row[SET_GHI])
        if (row[SET_SOLAR_RESTRICTION] == 1 and row[SET_GHI] > 1000) else 99,
        axis=1)

    logging.info('Calculate minigrid wind LCOE')
    df[SET_LCOE_MG_WIND] = df.apply(
        lambda row: tables.get_mg_wind_lcoe(row[SET_POP_FUTURE], scenario, num_people_per_hh, False, row[SET_WINDCF])
        if row[SET_WINDCF] > 0.1 else 99
        , axis=1)

    logging.info('Calculate minigrid diesel LCOE')
    df[SET_LCOE_MG_DIESEL] = df.apply(
        lambda row:
        tables.get_mg_diesel_lcoe(row[SET_POP_FUTURE], scenario, num_people_per_hh, False, diesel_price) +
        (2 * diesel_price * consumption_mg_diesel * row[SET_TRAVEL_HOURS] / volume_mg_diesel) *
        (1 / mu_mg_diesel) * (1 / LHV_DIESEL),
        axis=1)

    logging.info('Calculate standalone diesel LCOE')
    df[SET_LCOE_SA_DIESEL] = df.apply(
        lambda row:
        (diesel_price + 2 * diesel_price * consumption_sa_diesel * row[SET_TRAVEL_HOURS] / volume_sa_diesel) *
        (1 / mu_sa_diesel) * (1 / LHV_DIESEL) + p_om_sa_diesel + tables.get_sa_diesel_lcoe(row[SET_POP_FUTURE], scenario, num_people_per_hh, False, diesel_price),
        axis=1)

    logging.info('Calculate standalone PV LCOE')
    df[SET_LCOE_SA_PV] = df.apply(
        lambda row: tables.get_sa_pv_lcoe(row[SET_POP_FUTURE], scenario, num_people_per_hh, False, row[SET_GHI])
        if row[SET_GHI] > 1000 else 99,
        axis=1)

    logging.info('Determine minimum technology (no grid)')
    df[SET_MINIMUM_TECH] = df[[SET_LCOE_SA_DIESEL, SET_LCOE_SA_PV, SET_LCOE_MG_WIND,
                               SET_LCOE_MG_DIESEL, SET_LCOE_MG_PV, SET_LCOE_MG_HYDRO]].T.idxmin()

    logging.info('Determine minimum tech LCOE')
    df[SET_MINIMUM_TECH_LCOE] = df.apply(lambda row: (row[row[SET_MINIMUM_TECH]]), axis=1)

    return df


def results_columns(df, scenario, grid_btp, num_people_per_hh, diesel_price, grid_price,
                    transmission_losses, grid_capacity_investment):
    """

    @param df:
    @param grid_cap:
    @param tech_cap:
    @param scenario:
    @param grid_btp
    @param num_people_per_hh
    @return:
    """

    def res_investment_cost(row):
        min_tech = row[SET_MINIMUM_OVERALL]
        if min_tech == SET_LCOE_SA_DIESEL:
            return tables.get_sa_diesel_lcoe(row[SET_NEW_CONNECTIONS], scenario, num_people_per_hh, True, diesel_price)
        elif min_tech == SET_LCOE_SA_PV:
            return tables.get_sa_pv_lcoe(row[SET_NEW_CONNECTIONS], scenario, num_people_per_hh, True, row[SET_GHI])
        elif min_tech == SET_LCOE_MG_WIND:
            return tables.get_mg_wind_lcoe(row[SET_NEW_CONNECTIONS], scenario, num_people_per_hh, True, row[SET_WINDCF])
        elif min_tech == SET_LCOE_MG_DIESEL:
            return tables.get_mg_diesel_lcoe(row[SET_NEW_CONNECTIONS], scenario, num_people_per_hh, True, diesel_price)
        elif min_tech == SET_LCOE_MG_PV:
            return tables.get_mg_pv_lcoe(row[SET_NEW_CONNECTIONS], scenario, num_people_per_hh, True, row[SET_GHI])
        elif min_tech == SET_LCOE_MG_HYDRO:
            return tables.get_mg_hydro_lcoe(row[SET_NEW_CONNECTIONS], scenario, num_people_per_hh, True, row[SET_HYDRO_DIST])
        elif min_tech == SET_LCOE_GRID:
            return tables.get_grid_lcoe(row[SET_NEW_CONNECTIONS], scenario, num_people_per_hh, True, transmission_losses,
                                 grid_btp, grid_price, grid_capacity_investment, row[SET_MIN_GRID_DIST])
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
    df[SET_MINIMUM_CATEGORY] = df[SET_MINIMUM_OVERALL].str.extract('(sa|mg|grid)', expand=False)

    logging.info('Calculate new capacity')
    grid_vals = {'cf': 1.0, 'btp': grid_btp}
    mg_hydro_vals = {'cf': 0.5, 'btp': 1.0}
    mg_pv_vals = {'btp': 0.9}
    mg_wind_vals = {'btp': 0.75}
    mg_diesel_vals = {'cf': 0.7, 'btp': 0.5}
    sa_diesel_vals = {'cf': 0.7, 'btp': 0.5}
    sa_pv_vals = {'btp': 0.9}

    df.loc[df[SET_MINIMUM_OVERALL] == SET_LCOE_GRID, SET_NEW_CAPACITY] = \
        (df[SET_NEW_CONNECTIONS] * scenario / num_people_per_hh) / (HOURS_PER_YEAR * grid_vals['cf'] * grid_vals['btp'])
    df.loc[df[SET_MINIMUM_OVERALL] == SET_LCOE_MG_HYDRO, SET_NEW_CAPACITY] = \
        (df[SET_NEW_CONNECTIONS] * scenario / num_people_per_hh) / (HOURS_PER_YEAR * mg_hydro_vals['cf'] * mg_hydro_vals['btp'])
    df.loc[df[SET_MINIMUM_OVERALL] == SET_LCOE_MG_PV, SET_NEW_CAPACITY] = \
        (df[SET_NEW_CONNECTIONS] * scenario / num_people_per_hh) / (HOURS_PER_YEAR * (df[SET_GHI] / HOURS_PER_YEAR) * mg_pv_vals['btp'])
    df.loc[df[SET_MINIMUM_OVERALL] == SET_LCOE_MG_WIND, SET_NEW_CAPACITY] = \
        (df[SET_NEW_CONNECTIONS] * scenario / num_people_per_hh) / (HOURS_PER_YEAR * df[SET_WINDCF] * mg_wind_vals['btp'])
    df.loc[df[SET_MINIMUM_OVERALL] == SET_LCOE_MG_DIESEL, SET_NEW_CAPACITY] = \
        (df[SET_NEW_CONNECTIONS] * scenario / num_people_per_hh) / (HOURS_PER_YEAR * mg_diesel_vals['cf'] * mg_diesel_vals['btp'])
    df.loc[df[SET_MINIMUM_OVERALL] == SET_LCOE_SA_DIESEL, SET_NEW_CAPACITY] = \
        (df[SET_NEW_CONNECTIONS] * scenario / num_people_per_hh) / (HOURS_PER_YEAR * sa_diesel_vals['cf'] * sa_diesel_vals['btp'])
    df.loc[df[SET_MINIMUM_OVERALL] == SET_LCOE_SA_PV, SET_NEW_CAPACITY] = \
        (df[SET_NEW_CONNECTIONS] * scenario / num_people_per_hh) / (HOURS_PER_YEAR * (df[SET_GHI] / HOURS_PER_YEAR) * sa_pv_vals['btp'])

    logging.info('Calculate investment cost')
    df[SET_INVESTMENT_COST] = df.apply(res_investment_cost, axis=1)

    return df


def summaries(df, country):
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
