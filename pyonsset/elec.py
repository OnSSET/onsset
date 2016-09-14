"""
Contains the functions to calculate the electrification possibility for each cell, at a number of different distances
from the future grid.
"""

import logging
import pandas as pd
import numpy as np
from scipy.interpolate import RegularGridInterpolator, interp2d
from collections import defaultdict
from pyonsset.constants import *
from math import ceil, sqrt
import multiprocessing as mp

logging.basicConfig(format='%(asctime)s\t\t%(message)s', level=logging.DEBUG)


def separate_elec_status(elec_status):
    """
    Separate out the electrified and unelectrified states from list.

    @param elec_status: electricity status for each location
    @type elec_status: list of int
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


def elec_direct(df_country, grid, parallel=False):
    x = df_country[SET_X].tolist()
    y = df_country[SET_Y].tolist()
    pop = df_country[SET_POP_FUTURE].tolist()
    grid_penalty_ratio = df_country[SET_GRID_PENALTY].tolist()
    status = df_country[SET_ELEC_FUTURE].tolist()
    min_tech_lcoes = df_country[RES_MINIMUM_TECH_LCOE].tolist()
    new_lcoes = df_country[RES_LCOE_GRID].tolist()

    cell_path = np.zeros(len(status)).tolist()
    electrified, unelectrified = separate_elec_status(status)
    cpu_count = os.cpu_count()

    loops = 1
    while len(electrified) > 0:
        logging.info('Loop {} with {} electrified'.format(loops, len(electrified)))
        loops += 1
        hash_table = get_2d_hash_table(x, y, unelectrified, MAX_DIST)

        if parallel and len(electrified) > 2000:
            n = ceil(len(electrified) / cpu_count)
            a = [electrified[i:i + n] for i in range(0, len(electrified), n)]

            pool = mp.Pool(processes=cpu_count)
            results = [pool.apply_async(compare_lcoes,
                                        args=(i, new_lcoes, min_tech_lcoes, cell_path, dict(hash_table), grid,
                                              x, y, pop, grid_penalty_ratio)) for i in a]

            output = [p.get() for p in results]
            pool.close()
            pool.join()

            output_changes = [o[0] for o in output]
            output_new_lcoe = [o[1] for o in output]
            output_cell_path = [o[2] for o in output]

            changes = list(set([val for sublist in output_changes for val in sublist]))
            for c in changes:
                new_lcoes[c] = min([n[c] for n in output_new_lcoe])
                cell_path[c] = output_cell_path[[n[c] for n in output_new_lcoe].index(new_lcoes[c])][c]

        else:
            changes, new_lcoes, cell_path = compare_lcoes(electrified, new_lcoes, min_tech_lcoes,
                                                          cell_path, hash_table, grid, x, y, pop, grid_penalty_ratio)

        electrified = changes[:]
        unelectrified = [x for x in unelectrified if x not in electrified]

    return new_lcoes, cell_path


def compare_lcoes(electrified, new_lcoes, min_tech_lcoes, cell_path, hash_table, grid, x, y, pop, grid_penalty_ratio):
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
    @return:
    """
    _changes = []
    for elec in electrified:
        unelectrified_hashed = get_unelectrified_rows(hash_table, elec, x, y, MAX_DIST)
        for unelec in unelectrified_hashed:
            prev_dist = cell_path[elec]
            dist = grid_penalty_ratio[unelec] * sqrt((x[elec] - x[unelec]) ** 2 + (y[elec] - y[unelec]) ** 2)
            if prev_dist + dist < MAX_DIST:

                pop_index = pop[unelec]
                if pop_index < 1000:
                    pop_index = int(pop_index)
                elif pop_index < 10000:
                    pop_index = int(1000 + (pop_index - 1000)/10)
                else:
                    pop_index = int(1900 + (pop_index - 10000)/1000)

                grid_lcoe = grid[int(dist + EXISTING_GRID_COST_RATIO * prev_dist), pop_index]
                if grid_lcoe < min_tech_lcoes[unelec]:
                    if grid_lcoe < new_lcoes[unelec]:
                        new_lcoes[unelec] = grid_lcoe
                        cell_path[unelec] = dist + prev_dist
                        if unelec not in _changes:
                            _changes.append(unelec)
    return _changes, new_lcoes, cell_path


def run_elec(df, num_people, grid_lcoes, grid_price, parallel):
    """
    Run the electrification algorithm for the selected scenario and either one country or all.

    @param df
    @param num_people
    @param scenario
    @param specs
    @param countries
    @param parallel
    """

    # Calculate 2030 pre-electrification
    logging.info('Determine future pre-electrification status')
    df[SET_ELEC_FUTURE] = 0
    df[SET_ELEC_FUTURE] = df.apply(lambda row:
        1
        if row[SET_ELEC_CURRENT] == 1 or
        (row[SET_GRID_DIST_PLANNED] < NUM_PEOPLE_DISTS[0] and row[SET_POP_FUTURE] > num_people[NUM_PEOPLE_DISTS[0]]) or
           (row[SET_GRID_DIST_PLANNED] < NUM_PEOPLE_DISTS[1] and row[SET_POP_FUTURE] > num_people[NUM_PEOPLE_DISTS[1]])
        else 0,
                                                                                                   axis=1)

    df[RES_LCOE_GRID] = 99
    df[RES_LCOE_GRID] = df.apply(lambda row:
        grid_price
        if row[SET_ELEC_FUTURE] == 1
        else 99,
                                                                                            axis=1)

    df[RES_LCOE_GRID], df[RES_MIN_GRID_DIST] = elec_direct(
        df,
        grid_lcoes.as_matrix(),
        parallel)

    return df


def techs_only(df, tech_lcoes, diesel_price):
    """

    @param df:
    @param tech_lcoes:
    @param specs:
    @param diesel_high:
    @return:
    """


    x = tech_lcoes.columns.astype(float).tolist()

    # Prepare MG_HYDRO
    z_mg_hydro = tech_lcoes.loc[MG_HYDRO].as_matrix()

    # Prepare MG_PV
    y_pv = [PV_LOW, PV_MID, PV_HIGH]
    z = tech_lcoes.loc[[MG_PV_LOW, MG_PV_MID, MG_PV_HIGH]].as_matrix()
    interp_mg_pv =  interp2d(x, y_pv, z, bounds_error=False, fill_value=99)

    # Prepare MG_WIND
    y_wind = [WIND_LOW, WIND_MID, WIND_HIGH, WIND_EXTRA_HIGH]
    z_mg_wind = tech_lcoes.loc[[MG_WIND_LOW, MG_WIND_MID, MG_WIND_HIGH, MG_WIND_EXTRA_HIGH]].as_matrix()
    interp_mg_wind = interp2d(x, y_wind, z_mg_wind, bounds_error=False, fill_value=99)

    # Prepare MG_DIESEL
    # Pp = p_lcoe + (2*p_d*consumption*time/volume)*(1/mu)*(1/LHVd)
    z_mg_diesel = tech_lcoes.loc[MG_DIESEL].as_matrix()
    consumption_mg_diesel = 33.7
    volume_mg_diesel = 15000
    mu_mg_diesel = 0.3

    # Prepare SA_DIESEL
    # Pp = (p_d + 2*p_d*consumption*time/volume)*(1/mu)*(1/LHVd) + p_om + p_c
    p_c_sa_diesel = tech_lcoes.loc[SA_DIESEL][0]  # the value is not a function of population
    consumption_sa_diesel = 14  # (l/h) truck consumption per hour
    volume_sa_diesel = 300  # (l) volume of truck
    mu_sa_diesel = 0.3  # (kWhth/kWhel) gen efficiency
    p_om_sa_diesel = 0.01  # (USD/kWh) operation, maintenance and amortization

    # Prepare SA_PV
    z_sa_pv = [tech_lcoes.loc[SA_PV_LOW][0], tech_lcoes.loc[SA_PV_MID][0], tech_lcoes.loc[SA_PV_HIGH][0]]

    def res_lcoe_mg_hydro(row):
        if row[SET_HYDRO_DIST] < 5:
            return np.interp(row[SET_POP_FUTURE], x, z_mg_hydro)
        else:
            return 99

    def res_lcoe_mg_pv(row):
        if row[SET_SOLAR_RESTRICTION] == 0:
            return 99
        else:
            return interp_mg_pv(row[SET_POP_FUTURE], row[SET_GHI])[0]

    def res_lcoe_mg_wind(row):
        return interp_mg_wind(row[SET_POP_FUTURE], row[SET_WINDCF])[0]

    def res_lcoe_mg_diesel(row):
        p_lcoe = np.interp(row[SET_POP_FUTURE], x, z_mg_diesel)
        return p_lcoe + (2 * diesel_price * consumption_mg_diesel * row[SET_TRAVEL_HOURS] / volume_mg_diesel) * (1 / mu_mg_diesel) * (1 / LHV_DIESEL)

    def res_lcoe_sa_diesel(row):
        return (diesel_price + 2 * diesel_price * consumption_sa_diesel * row[SET_TRAVEL_HOURS] / volume_sa_diesel) * (1 / mu_sa_diesel) * (1 / LHV_DIESEL) + p_om_sa_diesel + p_c_sa_diesel

    def res_lcoe_sa_pv(row):
        return np.interp(row[SET_GHI], y_pv, z_sa_pv)

    logging.info('Calculate minigrid hydro LCOE')
    df[RES_LCOE_MG_HYDRO] = df.apply(res_lcoe_mg_hydro, axis=1)

    logging.info('Calculate minigrid PV LCOE')
    df[RES_LCOE_MG_PV] = df.apply(res_lcoe_mg_pv, axis=1)

    logging.info('Calculate minigrid wind LCOE')
    df[RES_LCOE_MG_WIND] = df.apply(res_lcoe_mg_wind, axis=1)

    logging.info('Calculate minigrid diesel LCOE')
    df[RES_LCOE_MG_DIESEL] = df.apply(res_lcoe_mg_diesel, axis=1)

    logging.info('Calculate standalone diesel LCOE')
    df[RES_LCOE_SA_DIESEL] = df.apply(res_lcoe_sa_diesel, axis=1)

    logging.info('Calculate standalone PV LCOE')
    df[RES_LCOE_SA_PV] = df.apply(res_lcoe_sa_pv, axis=1)

    logging.info('Determine minimum technology (no grid)')
    df[RES_MINIMUM_TECH] = df[[RES_LCOE_SA_DIESEL, RES_LCOE_SA_PV, RES_LCOE_MG_WIND,
                               RES_LCOE_MG_DIESEL, RES_LCOE_MG_PV, RES_LCOE_MG_HYDRO]].T.idxmin()

    logging.info('Determine minimum tech LCOE')
    df[RES_MINIMUM_TECH_LCOE] = df.apply(lambda row: (row[row[RES_MINIMUM_TECH]]), axis=1)

    return df


def results_columns(df, grid_cap, tech_cap, scenario, grid_btp):
    """

    @param df:
    @param specs:
    @param grid_cap:
    @param tech_cap:
    @param scenario:
    @return:
    """

    x_techs = tech_cap.columns.astype(float).tolist()

    y_pv = [PV_LOW, PV_MID, PV_HIGH]
    y_wind = [WIND_LOW, WIND_MID, WIND_HIGH, WIND_EXTRA_HIGH]

    # Prepare SA_DIESEL
    z_sa_diesel = tech_cap.loc[SA_DIESEL].as_matrix()

    # Prepare SA_PV
    z_sa_pv = tech_cap.loc[[SA_PV_LOW, SA_PV_MID, SA_PV_HIGH]].as_matrix()
    interp_sa_pv = interp2d(x_techs, y_pv, z_sa_pv)

    # Prepare MG_WIND
    z_mg_wind = tech_cap.loc[[MG_WIND_LOW, MG_WIND_MID, MG_WIND_HIGH, MG_WIND_EXTRA_HIGH]].as_matrix()
    interp_mg_wind = interp2d(x_techs,y_wind, z_mg_wind)

    # Prepare MG_DIESEL
    z_mg_diesel = tech_cap.loc[MG_DIESEL].as_matrix()

    # Prepare MG_PV
    z_mg_pv = tech_cap.loc[[MG_PV_LOW, MG_PV_MID, MG_PV_HIGH]].as_matrix()
    interp_mg_pv = interp2d(x_techs, y_pv, z_mg_pv)

    # Prepare MG_HYDRO
    z_mg_hydro = tech_cap.loc[MG_HYDRO].as_matrix()

    # Prepare GRID
    x_grid = grid_cap.columns.astype(float).tolist()
    y_grid = grid_cap.index.astype(float).tolist()
    z_grid = grid_cap.as_matrix()
    interp_grid = interp2d(x_grid, y_grid, z_grid)

    def res_investment_cost(row):
        min_tech = row[RES_MINIMUM_OVERALL]
        if min_tech == RES_LCOE_SA_DIESEL:
            return np.interp(row[RES_NEW_CONNECTIONS], x_techs, z_sa_diesel)
        elif min_tech == RES_LCOE_SA_PV:
            return interp_sa_pv(row[RES_NEW_CONNECTIONS], row[SET_GHI])[0]
        elif min_tech == RES_LCOE_MG_WIND:
            return interp_mg_wind(row[RES_NEW_CONNECTIONS], row[SET_WINDCF])[0]
        elif min_tech == RES_LCOE_MG_DIESEL:
            return np.interp(row[RES_NEW_CONNECTIONS], x_techs, z_mg_diesel)
        elif min_tech == RES_LCOE_MG_PV:
            return interp_mg_pv(row[RES_NEW_CONNECTIONS], row[SET_GHI])[0]
        elif min_tech == RES_LCOE_MG_HYDRO:
            return np.interp(row[RES_NEW_CONNECTIONS], x_techs, z_mg_hydro)
        elif min_tech == RES_LCOE_GRID:
            return interp_grid(row[RES_NEW_CONNECTIONS], row[RES_MIN_GRID_DIST])[0]
        else:
            raise ValueError('A technology has not been accounted for in res_investment_cost()')

    logging.info('Determine minimum overall')
    df[RES_MINIMUM_OVERALL] = df[[RES_LCOE_GRID, RES_LCOE_SA_DIESEL, RES_LCOE_SA_PV, RES_LCOE_MG_WIND,
                                  RES_LCOE_MG_DIESEL, RES_LCOE_MG_PV, RES_LCOE_MG_HYDRO]].T.idxmin()

    logging.info('Determine minimum overall LCOE')
    df[RES_MINIMUM_OVERALL_LCOE] = df.apply(lambda row: (row[row[RES_MINIMUM_OVERALL]]), axis=1)

    logging.info('Add technology codes')
    codes = {RES_LCOE_GRID: 1, RES_LCOE_MG_HYDRO: 7, RES_LCOE_MG_WIND: 6, RES_LCOE_MG_PV: 5,
             RES_LCOE_MG_DIESEL: 4, RES_LCOE_SA_DIESEL: 2, RES_LCOE_SA_PV: 3}
    df.loc[df[RES_MINIMUM_OVERALL] == RES_LCOE_GRID, RES_MINIMUM_OVERALL_CODE] = codes[RES_LCOE_GRID]
    df.loc[df[RES_MINIMUM_OVERALL] == RES_LCOE_MG_HYDRO, RES_MINIMUM_OVERALL_CODE] = codes[RES_LCOE_MG_HYDRO]
    df.loc[df[RES_MINIMUM_OVERALL] == RES_LCOE_SA_PV, RES_MINIMUM_OVERALL_CODE] = codes[RES_LCOE_SA_PV]
    df.loc[df[RES_MINIMUM_OVERALL] == RES_LCOE_MG_WIND, RES_MINIMUM_OVERALL_CODE] = codes[RES_LCOE_MG_WIND]
    df.loc[df[RES_MINIMUM_OVERALL] == RES_LCOE_MG_PV, RES_MINIMUM_OVERALL_CODE] = codes[RES_LCOE_MG_PV]
    df.loc[df[RES_MINIMUM_OVERALL] == RES_LCOE_MG_DIESEL, RES_MINIMUM_OVERALL_CODE] = codes[RES_LCOE_MG_DIESEL]
    df.loc[df[RES_MINIMUM_OVERALL] == RES_LCOE_SA_DIESEL, RES_MINIMUM_OVERALL_CODE] = codes[RES_LCOE_SA_DIESEL]

    logging.info('Determine minimum category')
    df[RES_MINIMUM_CATEGORY] = df[RES_MINIMUM_OVERALL].str.extract('(sa|mg|grid)', expand=False)

    logging.info('Calculate new connections')
    df.loc[df[SET_ELEC_CURRENT] == 1, RES_NEW_CONNECTIONS] = df[SET_POP_FUTURE] - df[SET_POP_CALIB]
    df.loc[df[SET_ELEC_CURRENT] == 0, RES_NEW_CONNECTIONS] = df[SET_POP_FUTURE]
    df.loc[df[RES_NEW_CONNECTIONS] < 0, RES_NEW_CONNECTIONS] = 0

    logging.info('Calculate new capacity')
    grid_vals = {'cf': 1.0, 'btp': grid_btp}
    mg_hydro_vals = {'cf': 0.5, 'btp': 1.0}
    mg_pv_vals = {'btp': 0.9}
    mg_wind_vals = {'btp': 0.75}
    mg_diesel_vals = {'cf': 0.7, 'btp': 0.5}
    sa_diesel_vals = {'cf': 0.7, 'btp': 0.5}
    sa_pv_vals = {'btp': 0.9}

    df.loc[df[RES_MINIMUM_OVERALL] == RES_LCOE_GRID, RES_NEW_CAPACITY] = (df[RES_NEW_CONNECTIONS]*scenario/NUM_PEOPLE_PER_HH)/(HOURS_PER_YEAR * grid_vals['cf'] * grid_vals['btp'])
    df.loc[df[RES_MINIMUM_OVERALL] == RES_LCOE_MG_HYDRO, RES_NEW_CAPACITY] = (df[RES_NEW_CONNECTIONS]*scenario/NUM_PEOPLE_PER_HH)/(HOURS_PER_YEAR * mg_hydro_vals['cf'] * mg_hydro_vals['btp'])
    df.loc[df[RES_MINIMUM_OVERALL] == RES_LCOE_MG_PV, RES_NEW_CAPACITY] = (df[RES_NEW_CONNECTIONS]*scenario/NUM_PEOPLE_PER_HH)/(HOURS_PER_YEAR * (df[SET_GHI]/HOURS_PER_YEAR) * mg_pv_vals['btp'])
    df.loc[df[RES_MINIMUM_OVERALL] == RES_LCOE_MG_WIND, RES_NEW_CAPACITY] = (df[RES_NEW_CONNECTIONS]*scenario/NUM_PEOPLE_PER_HH)/(HOURS_PER_YEAR * df[SET_WINDCF] * mg_wind_vals['btp'])
    df.loc[df[RES_MINIMUM_OVERALL] == RES_LCOE_MG_DIESEL, RES_NEW_CAPACITY] = (df[RES_NEW_CONNECTIONS]*scenario/NUM_PEOPLE_PER_HH)/(HOURS_PER_YEAR * mg_diesel_vals['cf'] * mg_diesel_vals['btp'])
    df.loc[df[RES_MINIMUM_OVERALL] == RES_LCOE_SA_DIESEL, RES_NEW_CAPACITY] = (df[RES_NEW_CONNECTIONS]*scenario/NUM_PEOPLE_PER_HH)/(HOURS_PER_YEAR * sa_diesel_vals['cf'] * sa_diesel_vals['btp'])
    df.loc[df[RES_MINIMUM_OVERALL] == RES_LCOE_SA_PV, RES_NEW_CAPACITY] = (df[RES_NEW_CONNECTIONS]*scenario/NUM_PEOPLE_PER_HH)/(HOURS_PER_YEAR * (df[SET_GHI]/HOURS_PER_YEAR) * sa_pv_vals['btp'])

    logging.info('Calculate investment cost')
    df[RES_INVESTMENT_COST] = df.apply(res_investment_cost, axis=1)

    return df


def summaries(df):
    """
    The next section calculates the summaries for technology split, consumption added and total investment cost

    @param df:
    @param specs:
    @param selection:
    """

    logging.info('Calculate summaries')
    cols = []
    techs = [RES_LCOE_GRID, RES_LCOE_SA_DIESEL, RES_LCOE_SA_PV, RES_LCOE_MG_WIND,
             RES_LCOE_MG_DIESEL, RES_LCOE_MG_PV, RES_LCOE_MG_HYDRO]
    cols.extend([SUM_SPLIT_PREFIX + t for t in techs])
    cols.extend([SUM_CAPACITY_PREFIX + t for t in techs])
    cols.extend([SUM_INVESTMENT_PREFIX + t for t in techs])
    summary = pd.Series(index=cols)

    new_connections = float(df[RES_NEW_CONNECTIONS].sum())
    for t in techs:
        summary.loc[SUM_SPLIT_PREFIX + t] = \
            df.loc[df[RES_MINIMUM_TECH] == t][RES_NEW_CONNECTIONS].sum() / new_connections
        summary.loc[SUM_CAPACITY_PREFIX + t] = \
            df.loc[df[RES_MINIMUM_TECH] == t][RES_NEW_CAPACITY].sum()
        summary.loc[SUM_INVESTMENT_PREFIX + t] = \
            df.loc[df[RES_MINIMUM_TECH] == t][RES_INVESTMENT_COST].sum()

    return summary


def main():
    scenario = 22  # int(input('Enter scenario value (int): '))
    diesel_high = True  # if 'H' in input('Enter L for low diesel, H for high diesel: ') else False
    parallel = False  # True if 'y' in input('parallel? ') else False

    diesel_tag = 'high' if diesel_high else 'low'

    specs = pd.read_excel(FF_SPECS, index_col=0)
    countries = specs.index.values.tolist()
    for country in countries:
        logging.info(' --- {} --- {} --- {} --- '.format(country, scenario, diesel_tag))

        output_dir = os.path.join('db/{}/{}'.format(country, scenario))
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        settlements_in_csv = 'db/{}/{}.csv'.format(country, country)
        settlements_out_csv = os.path.join(output_dir, '{}_{}_{}.csv'.format(country, scenario, diesel_tag))
        summary_csv = os.path.join(output_dir, '{}_{}_{}_summary.csv'.format(country, scenario, diesel_tag))

        lcoes_dir = os.path.join('db/{}/lcoes/{}'.format(country, scenario))
        grid_lcoes_csv = os.path.join(lcoes_dir, 'grid_lcoes_{}_{}.csv'.format(country, scenario))
        grid_cap_csv = os.path.join(lcoes_dir, 'grid_cap_{}_{}.csv'.format(country, scenario))
        tech_lcoes_csv = os.path.join(lcoes_dir, 'tech_lcoes_{}_{}.csv'.format(country, scenario))
        tech_cap_csv = os.path.join(lcoes_dir, 'tech_cap_{}_{}.csv'.format(country, scenario))
        num_people_csv = os.path.join(lcoes_dir, 'num_people_{}_{}.csv'.format(country, scenario))
        grid_lcoes = pd.read_csv(grid_lcoes_csv, index_col=0)
        grid_cap = pd.read_csv(grid_cap_csv, index_col=0)
        tech_lcoes = pd.read_csv(tech_lcoes_csv, index_col=0)
        tech_cap = pd.read_csv(tech_cap_csv, index_col=0)
        num_people = pd.read_csv(num_people_csv, index_col = 0, squeeze=True, header=None)

        df = pd.read_csv(settlements_in_csv)
        diesel_price = specs[SPE_DIESEL_PRICE_HIGH][country] if diesel_high else specs[SPE_DIESEL_PRICE_LOW][country]
        grid_price = specs[SPE_GRID_PRICE][country]

        df = techs_only(df, tech_lcoes, diesel_price)
        df = run_elec(df, num_people, grid_lcoes, grid_price, parallel)
        df = results_columns(df, grid_cap, tech_cap, scenario, specs[SPE_BASE_TO_PEAK][country])
        summaries(df).to_csv(summary_csv)

        logging.info('Saving to csv')
        df.to_csv(settlements_out_csv, index=False)

if __name__ == "__main__":
    os.chdir('..')
    print('Running as a script')
    main()
