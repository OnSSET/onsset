import os
import pandas as pd
import numpy as np
from scipy.interpolate import interp2d
from pyonsset.constants import *


def run(scenario, selection, diesel_high):
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
    grid_lcoes = pd.read_csv(grid_lcoes_csv, index_col=0).set_index('minor',drop=True,append=True,inplace=False).to_panel()
    grid_cap = pd.read_csv(grid_cap_csv, index_col=0).set_index('minor', drop=True, append=True,inplace=False).to_panel()
    tech_lcoes = pd.read_csv(tech_lcoes_csv, index_col=0).set_index('minor',drop=True,append=True,inplace=False).to_panel()
    tech_cap = pd.read_csv(tech_cap_csv, index_col=0).set_index('minor', drop=True, append=True,inplace=False).to_panel()
    country_specs = pd.read_excel(FF_SPECS, index_col=0)

    def func_RES_MIN_GRID_DIST(row):
        if row[SET_ELEC_CURRENT] == 0:
            return np.ma.filled(np.ma.masked_equal(np.array([row[x] * ELEC_DISTANCES[i] for i,x in enumerate(SET_ELEC_STEPS)]),0, copy=False).min(),fill_value=99)
        else:
            return 0

    def func_RES_LCOE_GRID(row):
        x = grid_lcoes.items.values.astype(float).tolist()
        y = grid_lcoes.minor_axis.values.astype(float).tolist()
        if row[RES_MIN_GRID_DIST] == 99:
            return 99
        elif row[RES_MIN_GRID_DIST] == 0:
            return country_specs[SPE_GRID_PRICE][row[SET_COUNTRY]]
        else:
            return interp2d(x, y, grid_lcoes.major_xs(row[SET_COUNTRY]).as_matrix())(row[SET_POP_FUTURE], row[RES_MIN_GRID_DIST])[0]

    def func_RES_LCOE_SA_PV(row):
        return -0.000181463450348082 * row['GHI'] + 0.7259

    def func_RES_LCOE_MG_WIND(row):
        x = tech_lcoes.items.values.astype(float).tolist()
        y = [0.2, 0.3, 0.4]
        if row[SET_WINDCF] > 0.2:
            return interp2d(x, y, tech_lcoes.major_xs(row[SET_COUNTRY]).loc[[MG_WIND_LOW, MG_WIND_MID, MG_WIND_HIGH]].as_matrix())(row[SET_POP_FUTURE], row[SET_WINDCF])[0]
        else:
            return 99

    def func_RES_LCOE_MG_DIESEL(row):
        x = tech_lcoes.items.values.astype(float).tolist()
        y = [0.0, 2.0]
        return interp2d(x, y, tech_lcoes.major_xs(row[SET_COUNTRY]).loc[[MG_DIESEL, MG_DIESEL]].as_matrix())(row[SET_POP_FUTURE], 1.0)[0] + 0.00256 * row[SET_TRAVEL_HOURS]

    def func_RES_LCOE_MG_PV(row):
        x = tech_lcoes.items.values.astype(float).tolist()
        y = [1750.0, 2250.0]
        return interp2d(x, y, tech_lcoes.major_xs(row[SET_COUNTRY]).loc[[MG_PV_LOW, MG_PV_HIGH]].as_matrix())(row[SET_POP_FUTURE], row[SET_GHI])[0]

    def func_RES_LCOE_MG_HYDRO(row):
        if row[SET_HYDRO_DIST] < 5:
            x = tech_lcoes.items.values.astype(float).tolist()
            y = [0.0,2.0]
            return interp2d(x, y, tech_lcoes.major_xs(row[SET_COUNTRY]).loc[[MG_HYDRO, MG_HYDRO]].as_matrix())(row[SET_POP_FUTURE],1.0)[0]
        else:
            return 99

    def func_RES_LCOE_SA_DIESEL(row):
        # calculate the diesel cost based on the travel time and other variables
        # from Mentis2015: Pp = (Pd + 2*Pd*c*t/V)*(1/mu)*(1/LHVd) + Pom
        # diesel price Pd in (USD/l), time t in hours, output Pp in USD/kWh

        c = 12 # (l/h) truck consumption per hour
        V = 300 # (l) volume of truck
        mu = 0.286 # (kWhth/kWhel) gen efficiency
        LHVd = 9.9445485 # (kWh/l) lower heating value
        Pom = 0.01 # (USD/kWh) operation, maintenance and amortization
        if diesel_high:
            diesel_price = SPE_DIESEL_PRICE_HIGH
        else:
            diesel_price = SPE_DIESEL_PRICE_LOW

        return (country_specs[diesel_price][row[SET_COUNTRY]] + 2 * country_specs[diesel_price][row[SET_COUNTRY]] * c * row[SET_TRAVEL_HOURS] / V) * (1 / mu) * (1 / LHVd) + Pom

    def func_RES_MINIMUM_CATEGORY(row):
        if 'grid' in row[RES_MINIMUM_TECH]:
            return 'grid'
        elif 'mg' in row[RES_MINIMUM_TECH]:
            return 'mg'
        else:
            return 'sa'

    def func_RES_NEW_CAPACITY(row):
        min_tech = row[RES_MINIMUM_TECH]
        if min_tech == RES_LCOE_SA_DIESEL: f = 1 * 0.5
        elif min_tech == RES_LCOE_SA_PV: f = 1 * row[SET_GHI]/(365 * 24)
        elif min_tech == RES_LCOE_MG_WIND: f = 0.75 * row[SET_WINDCF]/100
        elif min_tech == RES_LCOE_MG_DIESEL: f = 0.5 * 0.7
        elif min_tech == RES_LCOE_MG_PV: f = 0.9 * row[SET_GHI]/(365 * 24)
        elif min_tech == RES_LCOE_MG_HYDRO: f = 1 * 0.5
        elif min_tech == RES_LCOE_GRID: f = 1 # case for grid

        if min_tech == RES_LCOE_GRID: return 0 # 0 for grid
        else: return (row[SET_POP_FUTURE]*scenario/NUM_PEOPLE_PER_HH)/(8760*f)

    def func_RES_NEW_CONNECTIONS(row):
        if row[SET_ELEC_CURRENT] == 1:
            return max([0, row[SET_POP_FUTURE] - row[SET_POP_CALIB]])
        else:
            return row[SET_POP_FUTURE]

    def func_RES_INVESTMENT_COST(row):
        min_tech = row[RES_MINIMUM_TECH]
        if min_tech == RES_LCOE_SA_DIESEL:
            x = tech_cap.items.values.astype(float).tolist()
            y = [0.0, 2.0]
            z = tech_cap.major_xs(row[SET_COUNTRY]).loc[[SA_DIESEL_, SA_DIESEL_]].as_matrix()
            bilin = interp2d(x, y, z)(row[SET_POP_FUTURE], 1.0)[0]
        elif min_tech == RES_LCOE_SA_PV:
            x = tech_cap.items.values.astype(float).tolist()
            y = [1750.0, 2500.0]
            z = tech_cap.major_xs(row[SET_COUNTRY]).loc[[SA_PV_LOW, SA_PV_HIGH]].as_matrix()
            bilin = interp2d(x, y, z)(row[SET_POP_FUTURE], row[SET_GHI])[0]
        elif min_tech == RES_LCOE_MG_WIND:
            x = tech_cap.items.values.astype(float).tolist()
            y = [0.2, 0.3, 0.4]
            z = tech_cap.major_xs(row[SET_COUNTRY]).loc[[MG_WIND_LOW, MG_WIND_MID, MG_WIND_HIGH]].as_matrix()
            bilin = interp2d(x, y, z)(row[SET_POP_FUTURE], row[SET_WINDCF])[0]
        elif min_tech == RES_LCOE_MG_DIESEL:
            x = tech_cap.items.values.astype(float).tolist()
            y = [0.0, 2.0]
            z = tech_cap.major_xs(row[SET_COUNTRY]).loc[[MG_DIESEL, MG_DIESEL]].as_matrix()
            bilin = interp2d(x, y, z)(row[SET_POP_FUTURE], 1.0)[0]
        elif min_tech == RES_LCOE_MG_PV:
            x = tech_cap.items.values.astype(float).tolist()
            y = [1750.0, 2500.0]
            z = tech_cap.major_xs(row[SET_COUNTRY]).loc[[MG_PV_LOW, MG_PV_HIGH]].as_matrix()
            bilin = interp2d(x, y, z)(row[SET_POP_FUTURE], row[SET_GHI])[0]
        elif min_tech == RES_LCOE_MG_HYDRO:
            x = tech_cap.items.values.astype(float).tolist()
            y = [0.0, 2.0]
            z = tech_cap.major_xs(row[SET_COUNTRY]).loc[[MG_HYDRO, MG_HYDRO]].as_matrix()
            bilin = interp2d(x, y, z)(row[SET_POP_FUTURE], 1.0)[0]
        elif min_tech == RES_LCOE_GRID:
            x = grid_cap.items.values.astype(float).tolist()
            y = grid_cap.minor_axis.values.astype(float).tolist()
            z = grid_cap.major_xs(row[SET_COUNTRY]).as_matrix()
            bilin = interp2d(x, y, z)(row[SET_POP_FUTURE], row[RES_MIN_GRID_DIST])[0]
        return bilin * scenario * row[RES_NEW_CONNECTIONS] / NUM_PEOPLE_PER_HH

    df[RES_MIN_GRID_DIST] = df.apply(func_RES_MIN_GRID_DIST, axis=1)
    df[RES_LCOE_GRID] = df.apply(func_RES_LCOE_GRID, axis=1)
    df[RES_LCOE_SA_PV] = df.apply(func_RES_LCOE_SA_PV, axis=1)
    df[RES_LCOE_MG_WIND] = df.apply(func_RES_LCOE_MG_WIND, axis=1)
    df[RES_LCOE_MG_DIESEL] = df.apply(func_RES_LCOE_MG_DIESEL, axis=1)
    df[RES_LCOE_MG_PV] = df.apply(func_RES_LCOE_MG_PV,axis=1)
    df[RES_LCOE_MG_HYDRO] = df.apply(func_RES_LCOE_MG_HYDRO,axis=1)
    df[RES_LCOE_SA_DIESEL] = df.apply(func_RES_LCOE_SA_DIESEL, axis=1)
    df[RES_MINIMUM_TECH] = df[[RES_LCOE_GRID, RES_LCOE_SA_DIESEL, RES_LCOE_SA_PV, RES_LCOE_MG_WIND, RES_LCOE_MG_DIESEL, RES_LCOE_MG_PV, RES_LCOE_MG_HYDRO]].T.idxmin()
    df[RES_MINIMUM_LCOE] = df.apply(lambda row:(row[row[RES_MINIMUM_TECH]]),axis=1)
    df[RES_MINIMUM_CATEGORY] = df.apply(func_RES_MINIMUM_CATEGORY, axis=1)
    df[RES_NEW_CAPACITY] = df.apply(func_RES_NEW_CAPACITY,axis=1)
    df[RES_NEW_CONNECTIONS] = df.apply(func_RES_NEW_CONNECTIONS, axis=1)
    df[RES_INVESTMENT_COST] = df.apply(func_RES_INVESTMENT_COST, axis=1)
    df.to_csv(settlements_out_csv,index=False)

    countries = country_specs.index.values.tolist()
    cols = []
    techs = [RES_LCOE_GRID, RES_LCOE_SA_DIESEL, RES_LCOE_SA_PV, RES_LCOE_MG_WIND, RES_LCOE_MG_DIESEL, RES_LCOE_MG_PV, RES_LCOE_MG_HYDRO]
    for t in techs: cols.append('split_' + t)
    for t in techs: cols.append('capacity_' + t)
    for t in techs: cols.append('investment_' + t)

    summary = pd.DataFrame(index=countries, columns=cols)

    for c in countries:
        pop_tot = float(country_specs.loc[c, SPE_POP])
        for t in techs:
            summary.loc[c, 'split_' + t] = df.ix[df.Country == c][df.loc[df.Country == c]['minimum_tech'] == t][SET_POP_CALIB].sum()/pop_tot
            summary.loc[c, 'capacity_' + t] = df.ix[df.Country == c][df.loc[df.Country == c]['minimum_tech'] == t][RES_NEW_CAPACITY].sum()
            summary.loc[c, 'investment_' + t] = df.ix[df.Country == c][df.loc[df.Country == c]['minimum_tech'] == t][RES_INVESTMENT_COST].sum()

    summary.to_csv(summary_csv)