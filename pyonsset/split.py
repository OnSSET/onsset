"""
Contains the final section to calculate and compare the LCOEs for each cell.
"""

import logging
import pandas as pd
import numpy as np
from scipy.interpolate import interp2d
from pyonsset.constants import *

logging.basicConfig(format='%(asctime)s\t\t%(message)s', level=logging.DEBUG)


def run(scenario, selection='all', diesel_high=False):
    """
    Calculate LCOEs for each cell and compare.

    @param scenario: kWh/hh/yeaer
    @param selection: specific country or all
    @param diesel_high: True/False
    """

    logging.info('Starting function split.run()')

    output_dir = os.path.join(FF_TABLES, selection, str(scenario))
    if not os.path.exists(output_dir):
        raise IOError('The scenario has not been set up')

    if not os.path.exists(os.path.join(FF_LCOES, str(scenario))):
        raise IOError('The scenario has not been set up')

    settlements_in_csv = os.path.join(output_dir, '{}_{}.csv'.format(selection, scenario))
    if diesel_high:
        settlements_out_csv = os.path.join(output_dir, '{}_{}_high.csv'.format(selection, scenario))
        summary_csv = os.path.join(output_dir, '{}_{}_high_summary.csv'.format(selection, scenario))
    else:
        settlements_out_csv = os.path.join(output_dir, '{}_{}_low.csv'.format(selection, scenario))
        summary_csv = os.path.join(output_dir, '{}_{}_low_summary.csv'.format(selection, scenario))

    grid_lcoes_csv = FF_GRID_LCOES(scenario)
    grid_cap_csv = FF_GRID_CAP(scenario)
    tech_lcoes_csv = FF_TECH_LCOES(scenario)
    tech_cap_csv = FF_TECH_CAP(scenario)

    df = pd.read_csv(settlements_in_csv)
    grid_lcoes = pd.read_csv(grid_lcoes_csv, index_col=0).set_index('minor', drop=True, append=True).to_panel()
    grid_cap = pd.read_csv(grid_cap_csv, index_col=0).set_index('minor', drop=True, append=True).to_panel()
    tech_lcoes = pd.read_csv(tech_lcoes_csv, index_col=0).set_index('minor', drop=True, append=True).to_panel()
    tech_cap = pd.read_csv(tech_cap_csv, index_col=0).set_index('minor', drop=True, append=True).to_panel()
    specs = pd.read_excel(FF_SPECS, index_col=0)

    # Each of these functions for a specific column of results
    # The columns are used in df.apply() calls underneath
    # To add a new column, it needs a new function, as well as the df.apply() call beneath

    def res_min_grid_dist(row):
        if row[SET_ELEC_CURRENT] == 0:
            return np.ma.filled(np.ma.masked_equal(np.array(
                [row[x] * ELEC_DISTS[i] for i, x in enumerate(SET_ELEC_STEPS)]), 0, copy=False).min(), fill_value=99)
        else:
            return 0

    def res_lcoe_grid(row):
        if row[RES_MIN_GRID_DIST] == 99:
            return 99
        elif row[RES_MIN_GRID_DIST] == 0:
            return specs[SPE_GRID_PRICE][row[SET_COUNTRY]]
        else:
            x = grid_lcoes.items.values.astype(float).tolist()
            y = grid_lcoes.minor_axis.values.astype(float).tolist()
            z = grid_lcoes.major_xs(row[SET_COUNTRY]).as_matrix()
            return interp2d(x, y, z)(row[SET_POP_FUTURE], row[RES_MIN_GRID_DIST])[0]

    def res_lcoe_mg_hydro(row):
        if row[SET_HYDRO_DIST] < 5:
            x = tech_lcoes.items.values.astype(float).tolist()
            y = [0.0, 2.0]
            z = tech_lcoes.major_xs(row[SET_COUNTRY]).loc[[MG_HYDRO, MG_HYDRO]].as_matrix()
            return interp2d(x, y, z)(row[SET_POP_FUTURE], 1.0)[0]
        else:
            return 99

    def res_lcoe_mg_pv(row):
        x = tech_lcoes.items.values.astype(float).tolist()
        y = [PV_LOW, PV_HIGH]
        z = tech_lcoes.major_xs(row[SET_COUNTRY]).loc[[MG_PV_LOW, MG_PV_HIGH]].as_matrix()
        return interp2d(x, y, z)(row[SET_POP_FUTURE], row[SET_GHI])[0]

    def res_lcoe_mg_wind(row):
        if row[SET_WINDCF] >= 0.2:
            x = tech_lcoes.items.values.astype(float).tolist()
            y = [WIND_LOW, WIND_MID, WIND_HIGH]
            z = tech_lcoes.major_xs(row[SET_COUNTRY]).loc[[MG_WIND_LOW, MG_WIND_MID, MG_WIND_HIGH]].as_matrix()
            return interp2d(x, y, z)(row[SET_POP_FUTURE], row[SET_WINDCF])[0]
        else:
            return 99

    def res_lcoe_mg_diesel(row):
        # Pp = p_lcoe + (2*p_d*consumption*time/volume)*(1/mu)*(1/LHVd)

        x = tech_lcoes.items.values.astype(float).tolist()
        y = [0.0, 2.0]
        z = tech_lcoes.major_xs(row[SET_COUNTRY]).loc[[MG_DIESEL, MG_DIESEL]].as_matrix()
        p_lcoe = interp2d(x, y, z)(row[SET_POP_FUTURE], 1.0)[0]

        consumption = 33.7
        volume = 15000
        time = row[SET_TRAVEL_HOURS]
        mu = 0.3

        if diesel_high:
            p_d = specs[SPE_DIESEL_PRICE_HIGH][row[SET_COUNTRY]]
        else:
            p_d = specs[SPE_DIESEL_PRICE_LOW][row[SET_COUNTRY]]

        return p_lcoe + (2 * p_d * consumption * time / volume) * (1/mu) * (1/LHV_DIESEL)

    def res_lcoe_sa_diesel(row):
        # calculate the diesel cost based on the travel time and other variables
        # from Mentis2015: Pp = (p_d + 2*p_d*consumption*time/volume)*(1/mu)*(1/LHVd) + p_om + p_c
        # output Pp in USD/kWh

        x = tech_cap.items.values.astype(float).tolist()
        y = [0.0, 2.0]
        z = tech_cap.major_xs(row[SET_COUNTRY]).loc[[SA_DIESEL, SA_DIESEL]].as_matrix()
        p_c = interp2d(x, y, z)(row[SET_POP_FUTURE], 1.0)[0]  # capital cost in USD/kWh

        consumption = 14  # (l/h) truck consumption per hour
        time = row[SET_TRAVEL_HOURS]  # time in hours
        volume = 300  # (l) volume of truck
        mu = 0.3  # (kWhth/kWhel) gen efficiency
        p_om = 0.01  # (USD/kWh) operation, maintenance and amortization
        # diesel price p_d in (USD/l)
        if diesel_high:
            p_d = specs[SPE_DIESEL_PRICE_HIGH][row[SET_COUNTRY]]
        else:
            p_d = specs[SPE_DIESEL_PRICE_LOW][row[SET_COUNTRY]]

        return (p_d + 2 * p_d * consumption * time / volume) * (1 / mu) * (1 / LHV_DIESEL) + p_om + p_c

    def res_lcoe_sa_pv(row):
        x1 = PV_LOW
        x2 = PV_HIGH
        y1 = tech_lcoes.major_xs(row[SET_COUNTRY]).loc[SA_PV_LOW].iloc[0]
        y2 = tech_lcoes.major_xs(row[SET_COUNTRY]).loc[SA_PV_HIGH].iloc[0]

        gradient = (y2 - y1) / (x2 - x1)
        intercept = y2 - gradient * x2

        return gradient * row['GHI'] + intercept

    def res_minimum_category(row):
        if 'grid' in row[RES_MINIMUM_TECH]:
            return 'grid'
        elif 'mg' in row[RES_MINIMUM_TECH]:
            return 'mg'
        else:
            return 'sa'

    def res_new_connections(row):
        if row[SET_ELEC_CURRENT] == 1:
            return max([0, row[SET_POP_FUTURE] - row[SET_POP_CALIB]])
        else:
            return row[SET_POP_FUTURE]

    def res_new_capacity(row):
        min_tech = row[RES_MINIMUM_TECH]
        if min_tech == RES_LCOE_SA_DIESEL:
            cf = 1 * 0.5
        elif min_tech == RES_LCOE_SA_PV:
            cf = 1 * row[SET_GHI]/HOURS_PER_YEAR
        elif min_tech == RES_LCOE_MG_WIND:
            cf = 0.75 * row[SET_WINDCF]
        elif min_tech == RES_LCOE_MG_DIESEL:
            cf = 0.5 * 0.7
        elif min_tech == RES_LCOE_MG_PV:
            cf = 0.9 * row[SET_GHI]/HOURS_PER_YEAR
        elif min_tech == RES_LCOE_MG_HYDRO:
            cf = 1 * 0.5
        elif min_tech == RES_LCOE_GRID:
            cf = 1 * specs[SPE_BASE_TO_PEAK][row[SET_COUNTRY]]
        else:
            raise ValueError('A technology has not been accounted for in res_new_capacity()')

        return (row[RES_NEW_CONNECTIONS]*scenario/NUM_PEOPLE_PER_HH)/(HOURS_PER_YEAR*cf)

    def res_investment_cost(row):
        min_tech = row[RES_MINIMUM_TECH]
        if min_tech == RES_LCOE_SA_DIESEL:
            x = tech_cap.items.values.astype(float).tolist()
            y = [0.0, 2.0]
            y_var = 1.0
            z = tech_cap.major_xs(row[SET_COUNTRY]).loc[[SA_DIESEL, SA_DIESEL]].as_matrix()
        elif min_tech == RES_LCOE_SA_PV:
            x = tech_cap.items.values.astype(float).tolist()
            y = [PV_LOW, PV_HIGH]
            y_var = row[SET_GHI]
            z = tech_cap.major_xs(row[SET_COUNTRY]).loc[[SA_PV_LOW, SA_PV_HIGH]].as_matrix()
        elif min_tech == RES_LCOE_MG_WIND:
            x = tech_cap.items.values.astype(float).tolist()
            y = [WIND_LOW, WIND_MID, WIND_HIGH]
            y_var = row[SET_WINDCF]
            z = tech_cap.major_xs(row[SET_COUNTRY]).loc[[MG_WIND_LOW, MG_WIND_MID, MG_WIND_HIGH]].as_matrix()
        elif min_tech == RES_LCOE_MG_DIESEL:
            x = tech_cap.items.values.astype(float).tolist()
            y = [0.0, 2.0]
            y_var = 1.0
            z = tech_cap.major_xs(row[SET_COUNTRY]).loc[[MG_DIESEL, MG_DIESEL]].as_matrix()
        elif min_tech == RES_LCOE_MG_PV:
            x = tech_cap.items.values.astype(float).tolist()
            y = [PV_LOW, PV_HIGH]
            y_var = row[SET_GHI]
            z = tech_cap.major_xs(row[SET_COUNTRY]).loc[[MG_PV_LOW, MG_PV_HIGH]].as_matrix()
        elif min_tech == RES_LCOE_MG_HYDRO:
            x = tech_cap.items.values.astype(float).tolist()
            y = [0.0, 2.0]
            y_var = 1.0
            z = tech_cap.major_xs(row[SET_COUNTRY]).loc[[MG_HYDRO, MG_HYDRO]].as_matrix()
        elif min_tech == RES_LCOE_GRID:
            x = grid_cap.items.values.astype(float).tolist()
            y = grid_cap.minor_axis.values.astype(float).tolist()
            y_var = row[RES_MIN_GRID_DIST]
            z = grid_cap.major_xs(row[SET_COUNTRY]).as_matrix()
        else:
            raise ValueError('A technology has not been accounted for in res_investment_cost()')

        # TODO is it correct to multiply by number of years (15)?
        return interp2d(x, y, z)(row[SET_POP_FUTURE], y_var)[0]*(
            scenario*row[RES_NEW_CONNECTIONS]/NUM_PEOPLE_PER_HH)*(END_YEAR-START_YEAR)

    # Here the functions defined above are actually applied.
    logging.info('Calculate minimum grid distance')
    df[RES_MIN_GRID_DIST] = df.apply(res_min_grid_dist, axis=1)

    logging.info('Calculate grid LCOE')
    df[RES_LCOE_GRID] = df.apply(res_lcoe_grid, axis=1)

    logging.info('Calculated minigrid hydro LCOE')
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

    logging.info('Determine minimum technology')
    df[RES_MINIMUM_TECH] = df[[RES_LCOE_GRID, RES_LCOE_SA_DIESEL, RES_LCOE_SA_PV, RES_LCOE_MG_WIND,
                               RES_LCOE_MG_DIESEL, RES_LCOE_MG_PV, RES_LCOE_MG_HYDRO]].T.idxmin()

    logging.info('Determine minimum LCOE')
    df[RES_MINIMUM_LCOE] = df.apply(lambda row: (row[row[RES_MINIMUM_TECH]]), axis=1)

    logging.info('Determine minimum category')
    df[RES_MINIMUM_CATEGORY] = df.apply(res_minimum_category, axis=1)

    logging.info('Calculate new connections')
    df[RES_NEW_CONNECTIONS] = df.apply(res_new_connections, axis=1)

    logging.info('Calcualte new consumption')
    df[RES_NEW_CAPACITY] = df.apply(res_new_capacity, axis=1)

    logging.info('Calculate investment cost')
    df[RES_INVESTMENT_COST] = df.apply(res_investment_cost, axis=1)

    logging.info('Saving to csv')
    df.to_csv(settlements_out_csv, index=False)

    # The next section calculates the summaries for technology split, consumption added and total investment cost
    logging.info('Calculate summaries')
    countries = specs.index.values.tolist()
    cols = []
    techs = [RES_LCOE_GRID, RES_LCOE_SA_DIESEL, RES_LCOE_SA_PV, RES_LCOE_MG_WIND,
             RES_LCOE_MG_DIESEL, RES_LCOE_MG_PV, RES_LCOE_MG_HYDRO]
    cols.extend([SUM_SPLIT_PREFIX + t for t in techs])
    cols.extend([SUM_CAPACITY_PREFIX + t for t in techs])
    cols.extend([SUM_INVESTMENT_PREFIX + t for t in techs])
    summary = pd.DataFrame(index=countries, columns=cols)

    for c in countries:
        pop_tot = float(specs.loc[c, SPE_POP])
        for t in techs:
            summary.loc[c, SUM_SPLIT_PREFIX + t] = \
                df.ix[df.Country == c][df.loc[df.Country == c][RES_MINIMUM_TECH] == t][SET_POP_CALIB].sum()/pop_tot
            summary.loc[c, SUM_CAPACITY_PREFIX + t] = \
                df.ix[df.Country == c][df.loc[df.Country == c][RES_MINIMUM_TECH] == t][RES_NEW_CAPACITY].sum()
            summary.loc[c, SUM_INVESTMENT_PREFIX + t] = \
                df.ix[df.Country == c][df.loc[df.Country == c][RES_MINIMUM_TECH] == t][RES_INVESTMENT_COST].sum()

    summary.to_csv(summary_csv)

    logging.info('Completed function split.run()')


if __name__ == "__main__":
    os.chdir('..')
    print('Running as a script')
    scenario = int(input('Enter scenario value (int): '))
    selection = input('Enter country selection or "all": ')
    diesel_high = input('Enter L for low diesel, H for high diesel: ')
    diesel_high = diesel_high in 'H'
    run(scenario, selection, diesel_high)
