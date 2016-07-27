import os
import pandas as pd
import numpy as np
from collections import defaultdict
from pyonsset.constants import *

def separateElecStatus(elec_status):
    """
    Separate out the electrified and unelectrified states from list

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


def get2DHashTable(gis_data, unelectrified, distance_limit):
    """
    Generates the 2D Hash Table with the unelectrified locations hashed
    into the table for easy O(1) access.

    TODO params and return docstring
    """
    hash_table = defaultdict(lambda: defaultdict(list))
    for unelec_row in unelectrified:
        hash_x = int(gis_data[unelec_row][0] / distance_limit)
        hash_y = int(gis_data[unelec_row][1] / distance_limit)
        hash_table[hash_x][hash_y].append(unelec_row)
    return hash_table


def getUnelectrifiedRows(hash_table, elec_row, gis_data, distance_limit):
    """
    Returns all the unelectrified locations close to the electrified location
    based on the distance boundary limit specified by asking the 2D hash table.

    TODO params and return docstring
    """
    unelec_list = []
    hash_x = int(gis_data[elec_row][0] / distance_limit)
    hash_y = int(gis_data[elec_row][1] / distance_limit)

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


def runAlgorithm(df_country, distance, num_people):
    gis_data = df_country[['X', 'Y', 'Pop2030']].values.tolist()
    elec_status = df_country['Elec2030'].tolist()
    cell_path = np.zeros((len(elec_status),2))

    df_elec = pd.DataFrame(index=df_country.index.values)

    for distance_limit, population_limit in zip(distance, num_people):
        print('doing column {}'.format(distance_limit))
        counter = 0
        electrified, unelectrified = separateElecStatus(elec_status)

        hash_table = get2DHashTable(gis_data, unelectrified, distance_limit)
        # print str(hash_table) # TO DEBUG

        elec_changes = []
        counter2 = 2

        while counter2 >= 1:
            counter2 = 0
            # Iteration based on number of electrified
            # cells at this stage of the calculation.
            for elec_row in electrified:

                unelec_rows = getUnelectrifiedRows(hash_table, elec_row, gis_data, distance_limit)

                for unelec_row in unelec_rows:
                    # km of line build prior + line km building
                    existing_grid = cell_path[elec_row][0] + cell_path[elec_row][1]
                    # Check if really unelectrified
                    el = elec_status[unelec_row] == 0
                    dx = abs(gis_data[elec_row][0] - gis_data[unelec_row][0]) < distance_limit
                    dy = abs(gis_data[elec_row][1] - gis_data[unelec_row][1]) < distance_limit
                    not_same_point = dx > 0 or dy > 0
                    pop = gis_data[unelec_row][2] > population_limit + distance_limit * (
                    15.702 * (existing_grid + 7006) / 1000 - 110) / 4400
                    ok_to_extend = existing_grid < 50000

                    if el and dx and dy and not_same_point and pop and ok_to_extend:
                        if unelec_row not in elec_changes:
                            counter2 += 1
                            elec_changes.append(unelec_row)
                            elec_status[unelec_row] = 1
                            cell_path[unelec_row] = [existing_grid, distance_limit]

            if counter2 != 0:
                electrified = [item for item in elec_changes]
                elec_changes = []
            counter += 1
            # end while loop

        df_elec['Elec'+str(distance_limit)] = elec_status

    return df_elec

def run(scenario, settlements):
    output_dir = 'Tables/scenario{}'.format(scenario)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    settlements_csv = os.path.join('Tables', settlements + '.csv')
    num_people_csv = os.path.join(output_dir, 'num_people.csv')
    settlements_out_csv = os.path.join(output_dir, settlements)

    df = pd.read_csv(settlements_csv)
    num_people = pd.read_csv(num_people_csv, index_col=0)

    df['Elec2030'] = 0
    for col in SET_ELEC_STEPS: df[col] = 0
    countries = num_people.columns.values.tolist()

    for c in countries:
        df.loc[df.Country == c, SET_ELEC_FUTURE] = df.loc[df.Country == c].apply(lambda row:
                                                                           1
                                                                           if row[SET_ELEC_CURRENT] == 1 or
                                                                                (row[SET_GRID_DIST_PLANNED] < 5000 and row[SET_POP_FUTURE] > num_people[c].loc[5]) or
                                                                                (row[SET_GRID_DIST_PLANNED] < 10000 and row[SET_POP_FUTURE] > num_people[c].loc[10])
                                                                           else 0
                                                                           , axis=1)

        print('start {}'.format(c))
        df.loc[df.Country == c,SET_ELEC_STEPS] = runAlgorithm(
                        df.loc[df.Country == c,[SET_X, SET_Y, SET_POP_FUTURE, SET_ELEC_FUTURE]],
            ELEC_DISTANCES,
                        num_people[c].values.astype(int).tolist())


    df.to_csv(settlements_out_csv,index=False)