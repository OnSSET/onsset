# Pulls all the other functions together to make magic!
#
# Author: Christopher Arderne
# Date: 26 November 2016
# Python version: 3.5

import os
import pandas as pd
from pyonsset.constants import *
from pyonsset import prep, tables, elec

specs_path = 'db/specs.xlsx'
specs = pd.read_excel(specs_path, index_col=0)

countries = str(input('countries: ')).split()
countries = specs.index.tolist() if 'all' in countries else countries
wb_tier = int(input('wb tier: '))
diesel_high = True if 'y' in input('diesel high y/n: ') else False
diesel_tag = 'high' if diesel_high else 'low'
do_anything = True if 'y' in input('anything y/n: ') else False
do_prep = True if 'y' in input('prep y/n: ') else False
do_run = True if 'y' in input('run y/n: ') else False
combine = True if 'y' in input('combine y/n: ') else False

output_dir = 'db/run_12Nov'
try: os.makedirs(output_dir)
except FileExistsError: pass

if do_anything:
    for country in countries:
        # create country_specs here
        print(' --- {} --- {} --- {} --- '.format(country, wb_tier, diesel_tag))
        settlements_in_csv = 'db/base/{}.csv'.format(country)
        settlements_out_csv = os.path.join(output_dir, '{}_{}_{}.csv'.format(country, wb_tier, diesel_tag))
        summary_csv = os.path.join(output_dir, '{}_{}_{}_summary.csv'.format(country, wb_tier, diesel_tag))

        if os.path.isfile(settlements_in_csv):
            df = pd.read_csv(settlements_in_csv)
        else:
            df = pd.read_csv('db/settlements.csv')
            df = df.loc[df[SET_COUNTRY] == country]
            do_prep = True

        if do_prep:
            df = prep.condition(df)
            df = prep.grid_penalties(df)
            df = prep.wind(df)

            pop_actual = specs.loc[country, SPE_POP]
            pop_future = specs.loc[country, SPE_POP_FUTURE]
            urban = specs.loc[country, SPE_URBAN]
            urban_future = specs.loc[country, SPE_URBAN_FUTURE]
            urban_cutoff = specs.loc[country, SPE_URBAN_CUTOFF]

            elec = specs.loc[country, SPE_ELEC]
            pop_cutoff = specs.loc[country, SPE_POP_CUTOFF1]
            min_night_lights = specs.loc[country, SPE_MIN_NIGHT_LIGHTS]
            max_grid_dist = specs.loc[country, SPE_MAX_GRID_DIST]
            max_road_dist = specs.loc[country, SPE_MAX_ROAD_DIST]
            pop_tot = specs.loc[country, SPE_POP]
            pop_cutoff2 = specs.loc[country, SPE_POP_CUTOFF2]

            df, urban_cutoff, urban_modelled = prep.pop(df, pop_actual, pop_future, urban, urban_future, urban_cutoff)
            df, min_night_lights, max_grid_dist, max_road_dist, elec_modelled, pop_cutoff, pop_cutoff2 =\
                prep.elec_current(df, elec, pop_cutoff, min_night_lights, max_grid_dist, pop_tot, pop_cutoff2)

            specs.to_excel(specs_path)
            df.to_csv(settlements_in_csv, index=False)

        if do_run:
            diesel_price = specs[SPE_DIESEL_PRICE_HIGH][country] if diesel_high else specs[SPE_DIESEL_PRICE_LOW][country]
            grid_price = specs[SPE_GRID_PRICE][country]
            existing_grid_cost_ratio = specs[SPE_EXISTING_GRID_COST_RATIO][country]
            num_people_per_hh = float(specs[SPE_NUM_PEOPLE_PER_HH][country])
            transmission_losses = float(specs[SPE_GRID_LOSSES][country])
            grid_capacity_investment = float(specs[SPE_GRID_CAPACITY_INVESTMENT][country])
            max_dist = float(specs[SPE_MAX_GRID_EXTENSION_DIST][country])
            grid_base_to_peak = float(specs[SPE_BASE_TO_PEAK][country])
            wb_tiers_all = {1: 7.738, 2: 43.8, 3: 160.6, 4: 423.4, 5: 598.6}
            energy_per_hh = wb_tiers_all[wb_tier] * num_people_per_hh

            grid_lcoes = tables.get_grid_lcoe_table(energy_per_hh, max_dist, num_people_per_hh, transmission_losses, grid_base_to_peak,
                                                    grid_price, grid_capacity_investment)
            df = elec.techs_only(df, diesel_price, energy_per_hh, num_people_per_hh)
            df = elec.run_elec(df, grid_lcoes, grid_price, existing_grid_cost_ratio, max_dist)
            df = elec.results_columns(df, energy_per_hh, grid_base_to_peak, num_people_per_hh, diesel_price, grid_price,
                                      transmission_losses, grid_capacity_investment)
            elec.summaries(df, country).to_csv(summary_csv, header=True)

            df.to_csv(settlements_out_csv, index=False)

if combine:
    print('combining')
    df_base = pd.DataFrame()
    summaries = pd.DataFrame(columns=countries)

    for country in countries:
        print(country)
        df_add = pd.read_csv(os.path.join(output_dir, '{}_{}_{}.csv'.format(country, wb_tier, diesel_tag)))
        df_base = df_base.append(df_add, ignore_index=True)

        summaries[country] = pd.read_csv(os.path.join(output_dir, '{}_{}_{}_summary.csv'.format(country, wb_tier, diesel_tag)),
                                         squeeze=True, index_col=0)

    print('saving csv')
    df_base.to_csv(os.path.join(output_dir, '{}_{}.csv'.format(wb_tier, diesel_tag)), index=False)
    summaries.to_csv(os.path.join(output_dir, '{}_{}_summary.csv'.format(wb_tier, diesel_tag)))