import os
import pandas as pd
import numpy as np
from scipy import interpolate
from pyonsset.constants import *

def run(scenario, diesel_high, settlements, specs):
    output_dir = 'Tables/scenario{}'.format(scenario)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    settlements_csv = os.path.join(output_dir, settlements + '.csv')

    if diesel_high:
        settlements_out_csv = os.path.join(output_dir, settlements+'-high.csv')
        summary_csv = os.path.join(output_dir, 'summary-high.csv')
    else:
        settlements_out_csv = os.path.join(output_dir, settlements+'-low.csv')
        summary_csv = os.path.join(output_dir, 'summary-low.csv')


    grid_lcoes_csv = os.path.join(output_dir, 'grid_lcoes.csv')
    grid_cap_csv = os.path.join(output_dir, 'grid_cap.csv')
    tech_lcoes_csv = os.path.join(output_dir, 'tech_lcoes.csv')
    tech_cap_csv = os.path.join(output_dir, 'tech_cap.csv')
    country_specs_xlsx = os.path.join('Tables', specs + '.xlsx')

    df = pd.read_csv(settlements_csv)
    grid_lcoes = pd.read_csv(grid_lcoes_csv, index_col=0).set_index('minor',drop=True,append=True,inplace=False).to_panel()
    grid_cap = pd.read_csv(grid_cap_csv, index_col=0).set_index('minor', drop=True, append=True,inplace=False).to_panel()
    tech_lcoes = pd.read_csv(tech_lcoes_csv, index_col=0).set_index('minor',drop=True,append=True,inplace=False).to_panel()
    tech_cap = pd.read_csv(tech_cap_csv, index_col=0).set_index('minor', drop=True, append=True,
                                                                    inplace=False).to_panel()
    country_specs = pd.read_excel(country_specs_xlsx, index_col=0)

    # Calculate LCOE for GRID
    df[RES_MIN_GRID_DIST] = df.apply(lambda row:(
                            np.ma.filled(np.ma.masked_equal(np.array([row[x] * ELEC_DISTANCES[i] for i,x in SET_ELEC_STEPS]),
                                               0, copy = False).min(),fill_value=99)
                            if row[SET_ELEC_CURRENT]==0
                            else 0
                            ),axis=1)

    x = grid_lcoes.items.values.astype(float).tolist()
    y = grid_lcoes.minor_axis.values.astype(float).tolist()
    def lcoe_grid(row):
        if row[RES_MIN_GRID_DIST] == 99: return 99
        elif row[RES_MIN_GRID_DIST] == 0: return country_specs[SPE_GRID_PRICE][row[SET_COUNTRY]]
        else: return interpolate.interp2d(x, y, grid_lcoes.major_xs(row[SET_COUNTRY]).as_matrix())(row[SET_POP_FUTURE]*100, row[RES_MIN_GRID_DIST])[0]
    df[RES_LCOE_GRID] = df.apply(lcoe_grid,axis=1)

    df[RES_LCOE_SA_PV] = df.apply(lambda row:(
                            -0.000181463450348082 * row['GHI'] + 0.7259
                            ),axis=1)

    x = tech_lcoes.items.values.astype(float).tolist()
    y = [0.2, 0.3, 0.4]
    df[RES_LCOE_MG_WIND] = df.apply(lambda row:(
                            interpolate.interp2d(x, y, tech_lcoes.major_xs(row[SET_COUNTRY]).loc[[MG_WIND_LOW, MG_WIND_MID, MG_WIND_HIGH]].as_matrix())(row[SET_POP_FUTURE] * 100, row[SET_WINDCF])[0]
                            if row[SET_WINDCF] > 0.2
                            else 99
                                ),axis=1)
    print('done mg_wind')

    x = tech_lcoes.items.values.astype(float).tolist()
    y = [0.0,2.0]
    df[RES_LCOE_MG_DIESEL] = df.apply(lambda row:(
        interpolate.interp2d(x, y, tech_lcoes.major_xs(row[SET_COUNTRY]).loc[[MG_DIESEL, MG_DIESEL]].as_matrix())(row[SET_POP_FUTURE] * 100, 1.0)[0] + 0.00256 * row[SET_TRAVEL_HOURS]
                            ),axis=1)

    x = tech_lcoes.items.values.astype(float).tolist()
    y = [1750.0, 2250.0]
    df[RES_LCOE_MG_PV] = df.apply(lambda row:(
        interpolate.interp2d(x, y, tech_lcoes.major_xs(row[SET_COUNTRY]).loc[[MG_PV_LOW, MG_PV_HIGH]].as_matrix())(row[SET_POP_FUTURE] * 100, row[SET_GHI])[0]
                            ),axis=1)

    x = tech_lcoes.items.values.astype(float).tolist()
    y = [0.0,2.0]
    df[RES_LCOE_MG_HYDRO] = df.apply(lambda row:(
        interpolate.interp2d(x, y, tech_lcoes.major_xs(row[SET_COUNTRY]).loc[[MG_HYDRO, MG_HYDRO]].as_matrix())(row[SET_POP_FUTURE] * 100, 1.0)[0]
                            if row[SET_HYDRO_DIST] < 5000
                            else 99
                            ),axis=1)

    # calculate the diesel cost based on the travel time and other variables
    # from Mentis2015: Pp = (Pd + 2*Pd*c*t/V)*(1/mu)*(1/LHVd) + Pom
    # diesel price Pd in (USD/l), time t in hours, output Pp in USD/kWh

    c = 12 # (l/h) truck consumption per hour
    V = 300 # (l) volume of truck
    mu = 0.286 # (kWhth/kWhel) gen efficiency
    LHVd = 9.9445485 # (kWh/l) lower heating value
    Pom = 0.01 # (USD/kWh) operation, maintenance and amortization
    if diesel_high: diesel_price = SPE_DIESEL_PRICE_HIGH
    else: diesel_price = SPE_DIESEL_PRICE_LOW

    df[RES_LCOE_SA_DIESEL] = df.apply(lambda row: (
        (country_specs[diesel_price][row[SET_COUNTRY]] +
         2 * country_specs[diesel_price][row[SET_COUNTRY]] *
         c * row[SET_TRAVEL_HOURS] / V) * (1 / mu) * (1 / LHVd) + Pom
    ), axis=1)


    df[RES_MINIMUM_TECH] = df[[RES_LCOE_GRID, RES_LCOE_SA_DIESEL, RES_LCOE_SA_PV, RES_LCOE_MG_WIND, RES_LCOE_MG_DIESEL, RES_LCOE_MG_PV, RES_LCOE_MG_HYDRO]].T.idxmin()

    df[RES_MINIMUM_LCOE] = df.apply(lambda row:(
                            row[row[RES_MINIMUM_TECH]]
                            ),axis=1)

    def minimum_category(row):
        if 'grid' in row[RES_MINIMUM_TECH]: return 'grid'
        elif 'mg' in row[RES_MINIMUM_TECH]: return 'mg'
        else: return 'sa'
    df['minimum_category'] = df.apply(minimum_category,axis=1)


    # check capacity formulae
    num_people_per_hh = 5
    def capacity(row):
        min_tech = row[RES_MINIMUM_TECH]
        if min_tech == RES_LCOE_SA_DIESEL: f = 1 * 0.5
        elif min_tech == RES_LCOE_SA_PV: f = 1 * row[SET_GHI]/(365 * 24)
        elif min_tech == RES_LCOE_MG_WIND: f = 0.75 * row[SET_WINDCF]/100
        elif min_tech == RES_LCOE_MG_DIESEL: f = 0.5 * 0.7
        elif min_tech == RES_LCOE_MG_PV: f = 0.9 * row[SET_GHI]/(365 * 24)
        elif min_tech == RES_LCOE_MG_HYDRO: f = 1 * 0.5
        elif min_tech == RES_LCOE_GRID: f = 1 # case for grid

        if min_tech == RES_LCOE_GRID: return 0 # 0 for grid
        else: return (row[SET_POP_FUTURE]*scenario/num_people_per_hh)/(8760*f)
    df[RES_NEW_CAPACITY] = df.apply(capacity,axis=1)

    # calculate new connections
    def new_connections(row):
        if row[SET_ELEC_CURRENT] == 1:
            return max([0, row[SET_POP_FUTURE] - row[SET_POP_CALIB]])
        else:
            return row[SET_POP_FUTURE]
    df[RES_NEW_CONNECTIONS] = df.apply(new_connections, axis=1)

    # calculate investment cost
    def investment(row):
        min_tech = row[RES_MINIMUM_TECH]
        if min_tech == RES_LCOE_SA_DIESEL:
            x = tech_cap.items.values.astype(float).tolist()
            y = [0.0, 2.0]
            z = tech_cap.major_xs(row[SET_COUNTRY]).loc[[SA_DIESEL_, SA_DIESEL_]].as_matrix()
            bilin = interpolate.interp2d(x, y, z)(row[SET_POP_FUTURE] * 100, 1.0)[0]
            return bilin * scenario * row[RES_NEW_CONNECTIONS] / num_people_per_hh
        elif min_tech == RES_LCOE_SA_PV:
            x = tech_cap.items.values.astype(float).tolist()
            y = [1750.0, 2500.0]
            z = tech_cap.major_xs(row[SET_COUNTRY]).loc[[SA_PV_LOW, SA_PV_HIGH]].as_matrix()
            bilin = interpolate.interp2d(x, y, z)(row[SET_POP_FUTURE] * 100, row[SET_GHI])[0]
            return bilin * scenario * row[RES_NEW_CONNECTIONS] / num_people_per_hh
        elif min_tech == RES_LCOE_MG_WIND:
            x = tech_cap.items.values.astype(float).tolist()
            y = [0.2, 0.3, 0.4]
            z = tech_cap.major_xs(row[SET_COUNTRY]).loc[[MG_WIND_LOW, MG_WIND_MID, MG_WIND_HIGH]].as_matrix()
            bilin = interpolate.interp2d(x, y, z)(row[SET_POP_FUTURE] * 100, row[SET_WINDCF])[0]
            return bilin * scenario * row[RES_NEW_CONNECTIONS] / num_people_per_hh
        elif min_tech == RES_LCOE_MG_DIESEL:
            x = tech_cap.items.values.astype(float).tolist()
            y = [0.0, 2.0]
            z = tech_cap.major_xs(row[SET_COUNTRY]).loc[[MG_DIESEL, MG_DIESEL]].as_matrix()
            bilin = interpolate.interp2d(x, y, z)(row[SET_POP_FUTURE] * 100, 1.0)[0]
            return bilin * scenario * row[RES_NEW_CONNECTIONS] / num_people_per_hh
        elif min_tech == RES_LCOE_MG_PV:
            x = tech_cap.items.values.astype(float).tolist()
            y = [1750.0, 2500.0]
            z = tech_cap.major_xs(row[SET_COUNTRY]).loc[[MG_PV_LOW, MG_PV_HIGH]].as_matrix()
            bilin = interpolate.interp2d(x, y, z)(row[SET_POP_FUTURE] * 100, row[SET_GHI])[0]
            return bilin * scenario * row[RES_NEW_CONNECTIONS] / num_people_per_hh
        elif min_tech == RES_LCOE_MG_HYDRO:
            x = tech_cap.items.values.astype(float).tolist()
            y = [0.0, 2.0]
            z = tech_cap.major_xs(row[SET_COUNTRY]).loc[[MG_HYDRO, MG_HYDRO]].as_matrix()
            bilin = interpolate.interp2d(x, y, z)(row[SET_POP_FUTURE] * 100, 1.0)[0]
            return bilin * scenario * row[RES_NEW_CONNECTIONS] / num_people_per_hh
        elif min_tech == RES_LCOE_GRID:
            x = grid_cap.items.values.astype(float).tolist()
            y = grid_cap.minor_axis.values.astype(float).tolist()
            z = grid_cap.major_xs(row[SET_COUNTRY]).as_matrix()
            bilin = interpolate.interp2d(x, y, z)(row[SET_POP_FUTURE]*100, row[RES_MIN_GRID_DIST])[0]
            return bilin * scenario * row[RES_NEW_CONNECTIONS] / num_people_per_hh
    df[RES_INVESTMENT_COST] = df.apply(investment, axis=1)

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
            summary.loc[c, 'split_' + t] = df.ix[df.Country == c][df.loc[df.Country == c]['minimum_tech'] == t]['Pop2015Act'].sum()/pop_tot
            summary.loc[c, 'capacity_' + t] = df.ix[df.Country == c][df.loc[df.Country == c]['minimum_tech'] == t]['NewCapacity'].sum()
            summary.loc[c, 'investment_' + t] = df.ix[df.Country == c][df.loc[df.Country == c]['minimum_tech'] == t]['InvestmentCost'].sum()

    summary.to_csv(summary_csv)