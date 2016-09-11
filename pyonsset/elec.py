"""
Contains the functions to calculate the electrification possibility for each cell, at a number of different distances
from the future grid.
"""

import logging
import pandas as pd
import numpy as np
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

    @param gis_data: list of X- and Y-values for each cell
    @param unelectrified: list of unelectrified cells
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
    @param gis_data: list of X- and Y-values for each cell
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


def elec_single_country(df_country, num_people):
    """

    @param df_country: pandas.DataFrame containing all rows for a single country
    @param distance: list of distances to use
    @param num_people: list of corresponding population cutoffs to use
    @return:
    """
    x = df_country[SET_X].values.tolist()
    y = df_country[SET_Y].values.tolist()
    pop = df_country[SET_POP_FUTURE].values.tolist()
    status = df_country[SET_ELEC_FUTURE].tolist()
    grid_penalty_ratio = (1 + 0.1/df_country[SET_COMBINED_CLASSIFICATION].as_matrix()**2).tolist()
    cell_path = np.zeros(len(status))

    df_elec = pd.DataFrame(index=df_country.index.values)

    # We skip the first element in ELEC_DISTS to avoid dividing by zero
    for distance_limit, population_limit in zip(ELEC_DISTS[1:], num_people):
        logging.info(' - Column {}'.format(distance_limit))
        electrified, unelectrified = separate_elec_status(status)

        hash_table = get_2d_hash_table(x, y, unelectrified, distance_limit)

        while len(electrified) > 0:
            changes = []
            # Iteration based on number of electrified cells at this stage of the calculation.
            for elec in electrified:

                unelectrified_hashed = get_unelectrified_rows(hash_table, elec, x, y, distance_limit)
                for unelec in unelectrified_hashed:
                    existing_grid = cell_path[elec]

                    # We go 1km - 50km so further sets can be electrified by closer ones, but not vice versa
                    # But if we fix this, then it might prefer to just electrify everything in 1km steps, as it
                    # then pays only 10% for previous steps

                    if grid_penalty_ratio[unelec]*((abs(x[elec] - x[unelec])) + EXISTING_GRID_COST_RATIO * existing_grid < distance_limit and
                            grid_penalty_ratio[unelec]*(abs(y[elec] - y[unelec])) + EXISTING_GRID_COST_RATIO * existing_grid < distance_limit):
                        if pop[unelec] > population_limit and existing_grid < MAX_GRID_EXTEND:
                            if status[unelec] == 0:
                                changes.append(unelec)
                                status[unelec] = 1
                                cell_path[unelec] = existing_grid + distance_limit

            electrified = changes[:]

        df_elec[SET_ELEC_PREFIX + str(distance_limit)] = status

    return df_elec


def elec_direct(df_country, grid, parallel=False):
    x = df_country[SET_X].values.tolist()
    y = df_country[SET_Y].values.tolist()
    pop = df_country[SET_POP_FUTURE].values.tolist()
    grid_penalty_ratio = (1 + 0.1 / df_country[SET_COMBINED_CLASSIFICATION].as_matrix() ** 2).tolist()
    status = df_country[SET_ELEC_FUTURE].tolist()
    min_tech_lcoes = df_country[RES_MINIMUM_TECH_LCOE].tolist()
    new_lcoes = df_country[RES_LCOE_GRID].tolist()

    max_dist = 50
    cell_path = np.zeros(len(status))
    electrified, unelectrified = separate_elec_status(status)
    cpu_count = 9  # os.cpu_count()

    loops = 1
    while len(electrified) > 0:
        logging.info('Loop {} with {} electrified'.format(loops, len(electrified)))
        loops += 1
        hash_table = get_2d_hash_table(x, y, unelectrified, max_dist)

        if parallel and len(electrified) > 2000:
            n = ceil(len(electrified) / cpu_count)
            a = [electrified[i:i + n] for i in range(0, len(electrified), n)]

            pool = mp.Pool(processes=cpu_count)
            results = [pool.apply_async(compare_lcoes,
                                        args=(i, new_lcoes, min_tech_lcoes, cell_path, dict(hash_table), grid, max_dist,
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
            changes, new_lcoes, cell_path = compare_lcoes(electrified, new_lcoes, min_tech_lcoes, cell_path, hash_table, grid, max_dist, x, y, pop, grid_penalty_ratio)

        electrified = changes[:]
        unelectrified = [x for x in unelectrified if x not in electrified]

    return new_lcoes


def compare_lcoes(_electrified, _new_lcoes, _min_tech_lcoes, _cell_path, _hash_table, _grid, _max_dist, _x, _y, _pop, _grid_penalty_ratio):
    _changes = []
    for elec in _electrified:
        unelectrified_hashed = get_unelectrified_rows(_hash_table, elec, _x, _y, _max_dist)
        for unelec in unelectrified_hashed:
            #if not _new_lcoes[unelec] != 99:
            prev_dist = _cell_path[elec]
            dist = _grid_penalty_ratio[unelec] * sqrt((_x[elec] - _x[unelec]) ** 2 + (_y[elec] - _y[unelec]) ** 2)
            if prev_dist + dist < _max_dist:
                grid_lcoe = _grid[int(dist + EXISTING_GRID_COST_RATIO * prev_dist), int(_pop[unelec])]
                if grid_lcoe < _min_tech_lcoes[unelec]:
                    if grid_lcoe < _new_lcoes[unelec]:
                        _new_lcoes[unelec] = grid_lcoe
                        _cell_path[unelec] = dist + prev_dist
                        if unelec not in _changes:
                            _changes.append(unelec)
    return _changes, _new_lcoes, _cell_path


def run_elec(df, num_people, grid_lcoes_big, specs, countries, direct, parallel):
    """
    Run the electrification algorithm for the selected scenario and either one country or all.

    @param scenario: kW/hh/year
    @param selection: (optional) a specific country or leave blank for all
    """

    logging.info('Starting function elec.run_elec()')

    # Initialise the new columns
    df[SET_ELEC_FUTURE] = 0
    if not direct:
        for col in SET_ELEC_STEPS:
            df[col] = 0

    for c in countries:
        logging.info('Electrify {}'.format(c))

        # Calcualte 2030 pre-electrification
        logging.info('Determine future pre-electrification status')
        df.loc[df[SET_COUNTRY] == c, SET_ELEC_FUTURE] = df.loc[df[SET_COUNTRY] == c].apply(lambda row:
            1
            if row[SET_ELEC_CURRENT] == 1 or
            # TODO This 4 and 9 is very specific
            (row[SET_GRID_DIST_PLANNED] < ELEC_DISTS[4] and row[SET_POP_FUTURE] > num_people[c].loc[ELEC_DISTS[4]]) or
            (row[SET_GRID_DIST_PLANNED] < ELEC_DISTS[9] and row[SET_POP_FUTURE] > num_people[c].loc[ELEC_DISTS[9]])
            else 0,
            axis=1)

        if direct:
            df[RES_LCOE_GRID] = 99
            df.loc[df[SET_COUNTRY] == c, RES_LCOE_GRID] = df.loc[df.Country == c].apply(lambda row:
                specs[SPE_GRID_PRICE][c]
                if row[SET_ELEC_FUTURE] == 1
                else 99,
                axis=1)

            df.loc[df[SET_COUNTRY] == c, RES_LCOE_GRID] = elec_direct(
                df.loc[df[SET_COUNTRY] == c],
                grid_lcoes_big.major_xs(c).as_matrix(),
                parallel)
        else:
            logging.info('Analyse electrification columns')
            df.loc[df[SET_COUNTRY] == c, SET_ELEC_STEPS] = elec_single_country(
                df.loc[df[SET_COUNTRY] == c],
                num_people[c].values.astype(int).tolist())

    logging.info('Completed function elec.run_elec()')
    return df


def main():
    scenario = int(input('Enter scenario value (int): '))
    selection = input('Enter country selection or "all": ')
    direct = True if 'y' in input('direct? ') else False
    parallel = True if 'y' in input('parallel? ') else False
    diesel_high = True if 'H' in input('Enter L for low diesel, H for high diesel: ') else False

    output_dir = os.path.join(FF_TABLES, selection, str(scenario))
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    settlements_in_csv = os.path.join(output_dir, '{}_{}_direct.csv'.format(selection, scenario))
    settlements_out_csv = os.path.join(output_dir, '{}_{}_parallel2.csv'.format(selection, scenario))
    df = pd.read_csv(settlements_in_csv)

    num_people_csv = FF_NUM_PEOPLE(scenario)
    grid_lcoes_big_csv = FF_GRID_LCOES_BIG(scenario)
    tech_lcoes_csv = FF_TECH_LCOES(scenario)
    if not os.path.isfile(num_people_csv):
        raise IOError('The scenario LCOE tables have not been set up')

    num_people = pd.read_csv(num_people_csv, index_col=0)
    grid_lcoes_big = pd.read_csv(grid_lcoes_big_csv, index_col=0).set_index('minor', drop=True, append=True).to_panel()
    tech_lcoes = pd.read_csv(tech_lcoes_csv, index_col=0).set_index('minor', drop=True, append=True).to_panel()
    specs = pd.read_excel(FF_SPECS, index_col=0)

    # Limit the scope to the specific country if requested
    countries = num_people.columns.values.tolist()
    if selection != 'all':
        if selection in countries:
            countries = [selection]
            df = df.loc[df[SET_COUNTRY] == selection]
        else:
            raise KeyError('The selected country doesnt exist')

    if direct:
        from pyonsset import split
        #df = split.techs_only(df, tech_lcoes, specs, diesel_high)
        #df.to_csv(settlements_out_csv, index=False)

    df = run_elec(df, num_people, grid_lcoes_big, specs, countries, direct, parallel)

    logging.info('Saving to csv')
    df.to_csv(settlements_out_csv, index=False)

if __name__ == "__main__":
    os.chdir('..')
    print('Running as a script')
    main()