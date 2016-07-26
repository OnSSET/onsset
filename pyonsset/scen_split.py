import os
import pandas as pd
import numpy as np
from scipy import interpolate

def run(scenario, diesel_high, settlements, specs):
    output_dir = 'Tables/scenario{}'.format(scenario)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    settlements_csv = os.path.join(output_dir, settlements)

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
    country_specs_xlsx = os.path.join('Tables', specs)

    df = pd.read_csv(settlements_csv)
    grid_lcoes = pd.read_csv(grid_lcoes_csv, index_col=0).set_index('minor',drop=True,append=True,inplace=False).to_panel()
    grid_cap = pd.read_csv(grid_cap_csv, index_col=0).set_index('minor', drop=True, append=True,inplace=False).to_panel()
    tech_lcoes = pd.read_csv(tech_lcoes_csv, index_col=0).set_index('minor',drop=True,append=True,inplace=False).to_panel()
    tech_cap = pd.read_csv(tech_cap_csv, index_col=0).set_index('minor', drop=True, append=True,
                                                                    inplace=False).to_panel()
    country_specs = pd.read_excel(country_specs_xlsx, index_col=0)

    # Calculate LCOE for GRID
    df['MinGridDist'] = df.apply(lambda row:(
                            np.ma.filled(np.ma.masked_equal(np.array([row['Elec5000'] * 5000, row['Elec10000'] * 10000,
                                                         row['Elec15000'] * 15000, row['Elec20000'] * 20000,
                                                         row['Elec25000'] * 25000, row['Elec30000'] * 30000,
                                                         row['Elec35000'] * 35000, row['Elec40000'] * 40000,
                                                         row['Elec45000'] * 45000, row['Elec50000'] * 50000]),
                                               0, copy = False).min(),fill_value=99)
                            if row['Elec2015']==0
                            else 0
                            ),axis=1)
    print('done mingriddist')

    x = grid_lcoes.items.values.astype(float).tolist()
    y = grid_lcoes.minor_axis.values.astype(float).tolist()
    def lcoe_grid(row):
        if row['MinGridDist'] == 99: return 99
        elif row['MinGridDist'] == 0: return country_specs['GridPrice'][row['Country']]
        else: return interpolate.interp2d(x, y, grid_lcoes.major_xs(row['Country']).as_matrix())(row['Pop2030']*100, row['MinGridDist'])[0]
    df['lcoe_grid'] = df.apply(lcoe_grid,axis=1)
    print('done grid')

    df['lcoe_sa_pv'] = df.apply(lambda row:(
                            -0.000181463450348082 * row['GHI'] + 0.7259
                            ),axis=1)
    print('done sa_pv')

    x = tech_lcoes.items.values.astype(float).tolist()
    y = [0.2, 0.3, 0.4]
    df['lcoe_mg_wind'] = df.apply(lambda row:(
                            interpolate.interp2d(x, y, tech_lcoes.major_xs(row['Country']).loc[['mg_wind0.2', 'mg_wind0.3', 'mg_wind0.4']].as_matrix())(row['Pop2030'] * 100, row['WindCF'])[0]
                            if row['WindCF'] > 0.2
                            else 99
                                ),axis=1)
    print('done mg_wind')

    x = tech_lcoes.items.values.astype(float).tolist()
    y = [0.0,2.0]
    df['lcoe_mg_diesel'] = df.apply(lambda row:(
        interpolate.interp2d(x, y, tech_lcoes.major_xs(row['Country']).loc[['mg_diesel', 'mg_diesel']].as_matrix())(row['Pop2030'] * 100, 1.0)[0] + 0.00256 * row['TravelHours']
                            ),axis=1)
    print('done_mg_diesel')

    x = tech_lcoes.items.values.astype(float).tolist()
    y = [1750.0, 2500.0]
    df['lcoe_mg_pv'] = df.apply(lambda row:(
        interpolate.interp2d(x, y, tech_lcoes.major_xs(row['Country']).loc[['mg_pv1750', 'mg_pv2500']].as_matrix())(row['Pop2030'] * 100, row['GHI'])[0]
                            ),axis=1)
    print('done mg_pv')

    x = tech_lcoes.items.values.astype(float).tolist()
    y = [0.0,2.0]
    df['lcoe_mg_hydro'] = df.apply(lambda row:(
        interpolate.interp2d(x, y, tech_lcoes.major_xs(row['Country']).loc[['mg_hydro', 'mg_hydro']].as_matrix())(row['Pop2030'] * 100, 1.0)[0]
                            if row['HydropowerDist'] < 5000
                            else 99
                            ),axis=1)
    print('done mg_hydro')

    # calculate the diesel cost based on the travel time and other variables
    # from Mentis2015: Pp = (Pd + 2*Pd*c*t/V)*(1/mu)*(1/LHVd) + Pom
    # diesel price Pd in (USD/l), time t in hours, output Pp in USD/kWh

    c = 12 # (l/h) truck consumption per hour
    V = 300 # (l) volume of truck
    mu = 0.286 # (kWhth/kWhel) gen efficiency
    LHVd = 9.9445485 # (kWh/l) lower heating value
    Pom = 0.01 # (USD/kWh) operation, maintenance and amortization
    if diesel_high: diesel_price = 'DieselPriceHigh'
    else: diesel_price = 'DieselPriceLow'

    df['lcoe_sa_diesel'] = df.apply(lambda row: (
        (country_specs[diesel_price][row['Country']] +
         2 * country_specs[diesel_price][row['Country']] *
         c * row['TravelHours'] / V) * (1 / mu) * (1 / LHVd) + Pom
    ), axis=1)


    df['minimum_tech'] = df[['lcoe_grid', 'lcoe_sa_diesel', 'lcoe_sa_pv', 'lcoe_mg_wind', 'lcoe_mg_diesel', 'lcoe_mg_pv', 'lcoe_mg_hydro']].T.idxmin()

    df['minimum_lcoe'] = df.apply(lambda row:(
                            row[row['minimum_tech']]
                            ),axis=1)

    def minimum_category(row):
        if 'grid' in row['minimum_tech']: return 'grid'
        elif 'mg' in row['minimum_tech']: return 'mg'
        else: return 'sa'
    df['minimum_category'] = df.apply(minimum_category,axis=1)


    # check capacity formulae
    num_people_per_hh = 5
    def capacity(row):
        min_tech = row['minimum_tech']
        if min_tech == 'lcoe_sa_diesel': f = 1 * 0.5
        elif min_tech == 'lcoe_sa_pv': f = 1 * row['GHI']/(365 * 24)
        elif min_tech == 'lcoe_mg_wind': f = 0.75 * row['WindCF']/100
        elif min_tech == 'lcoe_mg_diesel': f = 0.5 * 0.7
        elif min_tech == 'lcoe_mg_pv': f = 0.9 * row['GHI']/(365 * 24)
        elif min_tech == 'lcoe_mg_hydro': f = 1 * 0.5
        elif min_tech == 'lcoe_grid': f = 1 # case for grid

        if min_tech == 'lcoe_grid': return 0 # 0 for grid
        else: return (row['Pop2030']*scenario/num_people_per_hh)/(8760*f)
    df['NewCapacity'] = df.apply(capacity,axis=1)

    # calculate new connections
    def new_connections(row):
        if row['Elec2015'] == 1:
            return max([0, row['Pop2030'] - row['Pop2015Act']])
        else:
            return row['Pop2030']
    df['NewConnections'] = df.apply(new_connections, axis=1)

    # calculate investment cost
    def investment(row):
        min_tech = row['minimum_tech']
        if min_tech == 'lcoe_sa_diesel':
            return 9999 * scenario * row['NewConnections'] / num_people_per_hh
        elif min_tech == 'lcoe_sa_pv':
            return 9999 * scenario * row['NewConnections'] / num_people_per_hh
        elif min_tech == 'lcoe_mg_wind':
            x = tech_cap.items.values.astype(float).tolist()
            y = [0.2, 0.3, 0.4]
            z = tech_cap.major_xs(row['Country']).loc[['mg_wind0.2', 'mg_wind0.3', 'mg_wind0.4']].as_matrix()
            bilin = interpolate.interp2d(x, y, z)(row['Pop2030'] * 100, row['WindCF'])[0]
            return bilin * scenario * row['NewConnections'] / num_people_per_hh
        elif min_tech == 'lcoe_mg_diesel':
            x = tech_cap.items.values.astype(float).tolist()
            y = [0.0, 2.0]
            z = tech_cap.major_xs(row['Country']).loc[['mg_diesel', 'mg_diesel']].as_matrix()
            bilin = interpolate.interp2d(x, y, z)(row['Pop2030'] * 100, 1.0)[0]
            return bilin * scenario * row['NewConnections'] / num_people_per_hh
        elif min_tech == 'lcoe_mg_pv':
            x = tech_cap.items.values.astype(float).tolist()
            y = [1750.0, 2500.0]
            z = tech_cap.major_xs(row['Country']).loc[['mg_pv1750', 'mg_pv2500']].as_matrix()
            bilin = interpolate.interp2d(x, y, z)(row['Pop2030'] * 100, row['GHI'])[0]
            return bilin * scenario * row['NewConnections'] / num_people_per_hh
        elif min_tech == 'lcoe_mg_hydro':
            x = tech_cap.items.values.astype(float).tolist()
            y = [0.0, 2.0]
            z = tech_cap.major_xs(row['Country']).loc[['mg_hydro', 'mg_hydro']].as_matrix()
            bilin = interpolate.interp2d(x, y, z)(row['Pop2030'] * 100, 1.0)[0]
            return bilin * scenario * row['NewConnections'] / num_people_per_hh
        elif min_tech == 'lcoe_grid':
            x = grid_cap.items.values.astype(float).tolist()
            y = grid_cap.minor_axis.values.astype(float).tolist()
            z = grid_cap.major_xs(row['Country']).as_matrix()
            bilin = interpolate.interp2d(x, y, z)(row['Pop2030']*100, row['MinGridDist'])[0]
            return bilin * scenario * row['NewConnections'] / num_people_per_hh
    df['InvestmentCost'] = df.apply(investment, axis=1)
    print('done minimums and investments')

    df.to_csv(settlements_out_csv,index=False)

    countries = country_specs.index.values.tolist()
    cols = []
    techs = ['lcoe_grid', 'lcoe_sa_diesel', 'lcoe_sa_pv', 'lcoe_mg_wind', 'lcoe_mg_diesel', 'lcoe_mg_pv', 'lcoe_mg_hydro']
    for t in techs: cols.append('split_' + t)
    for t in techs: cols.append('capacity_' + t)
    for t in techs: cols.append('investment_' + t)

    summary = pd.DataFrame(index=countries, columns=cols)

    for c in countries:
        pop_tot = float(country_specs.loc[c, 'Pop2015TotActual'])
        for t in techs:
            summary.loc[c, 'split_' + t] = df.ix[df.Country == c][df.loc[df.Country == c]['minimum_tech'] == t]['Pop2015Act'].sum()/pop_tot
            summary.loc[c, 'capacity_' + t] = df.ix[df.Country == c][df.loc[df.Country == c]['minimum_tech'] == t]['NewCapacity'].sum()
            summary.loc[c, 'investment_' + t] = df.ix[df.Country == c][df.loc[df.Country == c]['minimum_tech'] == t]['InvestmentCost'].sum()

    summary.to_csv(summary_csv)