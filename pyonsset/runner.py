# Pulls all the other functions together to make magic!
#
# Author: Christopher Arderne
# Date: 26 November 2016
# Python version: 3.5

import os
from pyonsset.onsset import *

os.chdir('..')
os.chdir('db')

specs_path = str(input('Enter the name of the specs file: '))
specs = pd.read_excel(specs_path, index_col=0)

countries = str(input('countries: ')).split()
countries = specs.index.tolist() if 'all' in countries else countries

choice = int(input('Enter 1 to split, 2 to prep, 3 to run a scenario: '))

if choice == 1:
    settlements_csv = str(input('Enter the name of the file containing all countries: '))
    base_dir = str(input('Enter the base file directory to save the split countries: '))

    print('\n --- Splitting --- \n')

    try: os.makedirs(base_dir)
    except FileExistsError: pass

    df = pd.read_csv(settlements_csv)

    for country in countries:
        print(country)
        df.loc[df[SET_COUNTRY] == country].to_csv(os.path.join(base_dir, '{}.csv'.format(country)), index=False)

elif choice == 2:
    base_dir = str(input('Enter the base file directory containing separated countries (files will be overwritten): '))
    print('\n --- Prepping --- \n')

    for country in countries:
        print(country)
        settlements_in_csv = os.path.join(base_dir, '{}.csv'.format(country))

        try:
            df = pd.read_csv(settlements_in_csv)
        except FileNotFoundError:
            print('You need to first split into a base directory!')
            raise

        df = condition_df(df)
        df = grid_penalties(df)
        df = calc_wind_cfs(df)

        pop_actual = specs.loc[country, SPE_POP]
        pop_future = specs.loc[country, SPE_POP_FUTURE]
        urban = specs.loc[country, SPE_URBAN]
        urban_future = specs.loc[country, SPE_URBAN_FUTURE]
        urban_cutoff = specs.loc[country, SPE_URBAN_CUTOFF]

        elec_actual = specs.loc[country, SPE_ELEC]
        pop_cutoff = specs.loc[country, SPE_POP_CUTOFF1]
        min_night_lights = specs.loc[country, SPE_MIN_NIGHT_LIGHTS]
        max_grid_dist = specs.loc[country, SPE_MAX_GRID_DIST]
        max_road_dist = specs.loc[country, SPE_MAX_ROAD_DIST]
        pop_tot = specs.loc[country, SPE_POP]
        pop_cutoff2 = specs.loc[country, SPE_POP_CUTOFF2]

        df, urban_cutoff, urban_modelled = calibrate_pop_and_urban(df, pop_actual, pop_future, urban, urban_future, urban_cutoff)
        df, min_night_lights, max_grid_dist, max_road_dist, elec_modelled, pop_cutoff, pop_cutoff2 = \
            elec_current_and_future(df, elec_actual, pop_cutoff, min_night_lights, max_grid_dist, max_road_dist, pop_tot,
                                    pop_cutoff2)

        specs.loc[country, SPE_MIN_NIGHT_LIGHTS] = min_night_lights
        specs.loc[country, SPE_MAX_GRID_DIST] = max_grid_dist
        specs.loc[country, SPE_MAX_ROAD_DIST] = max_road_dist
        specs.loc[country, SPE_ELEC_MODELLED] = elec_modelled
        specs.loc[country, SPE_POP_CUTOFF1] = pop_cutoff
        specs.loc[country, SPE_POP_CUTOFF2] = pop_cutoff2

        specs.to_excel(specs_path)
        df.to_csv(settlements_in_csv, index=False)

elif choice == 3:
    base_dir = str(input('Enter the base file directory containing separated and prepped countries: '))
    output_dir = str(input('Enter the output directory (can contain multiple runs): '))

    wb_tiers_all = {1: 7.738, 2: 43.8, 3: 160.6, 4: 423.4, 5: 598.6}
    wb_tier_urban = int(input('World Bank Tiers of Electricity Access\n'
                      '1: {} kWh/hh/year\n2: {} kWh/hh/year\n3: {} kWh/hh/year\n4: {} kWh/hh/year\n5: {} kWh/hh/year\n'
                      'Enter the tier number for urban: '.format(wb_tiers_all[1], wb_tiers_all[2], wb_tiers_all[3],
                                                                 wb_tiers_all[4], wb_tiers_all[5])))
    wb_tier_rural = int(input('World Bank Tiers of Electricity Access\n'
                              '1: {} kWh/hh/year\n2: {} kWh/hh/year\n3: {} kWh/hh/year\n4: {} kWh/hh/year\n5: {} kWh/hh/year\n'
                              'Enter the tier number for rural: '.format(wb_tiers_all[1], wb_tiers_all[2],
                                                                         wb_tiers_all[3],
                                                                         wb_tiers_all[4], wb_tiers_all[5])))

    diesel_high = True if 'y' in input('Use high diesel value? <y/n> ') else False
    diesel_tag = 'high' if diesel_high else 'low'
    do_combine = True if 'y' in input('Combine countries into a single file? <y/n> ') else False

    print('\n --- Running scenario --- \n')

    try: os.makedirs(output_dir)
    except FileExistsError: pass

    for country in countries:
        # create country_specs here
        print(' --- {} --- {} --- {} --- '.format(country, wb_tier_urban, diesel_tag))
        settlements_in_csv = os.path.join(base_dir, '{}.csv'.format(country))
        settlements_out_csv = os.path.join(output_dir, '{}_{}_{}.csv'.format(country, wb_tier_urban, diesel_tag))
        summary_csv = os.path.join(output_dir, '{}_{}_{}_summary.csv'.format(country, wb_tier_urban, diesel_tag))

        try:
            df = pd.read_csv(settlements_in_csv)
        except FileNotFoundError:
            print('You need to first split into a base directory and prep!')
            raise

        diesel_price = specs[SPE_DIESEL_PRICE_HIGH][country] if diesel_high else specs[SPE_DIESEL_PRICE_LOW][country]
        grid_price = specs[SPE_GRID_PRICE][country]
        existing_grid_cost_ratio = specs[SPE_EXISTING_GRID_COST_RATIO][country]
        num_people_per_hh = float(specs[SPE_NUM_PEOPLE_PER_HH][country])
        transmission_losses = float(specs[SPE_GRID_LOSSES][country])
        grid_capacity_investment = float(specs[SPE_GRID_CAPACITY_INVESTMENT][country])
        max_dist = float(specs[SPE_MAX_GRID_EXTENSION_DIST][country])
        grid_base_to_peak = float(specs[SPE_BASE_TO_PEAK][country])
        energy_per_hh_urban = wb_tiers_all[wb_tier_urban] * num_people_per_hh
        energy_per_hh_rural = wb_tiers_all[wb_tier_rural] * num_people_per_hh

        mg_hydro_vals = {'capacity_factor': 0.5, 'capital_cost': 5000, 'om_costs':0.02,
                         'base_to_peak_load_ratio': 1, 'system_life': 30}
        mg_pv_vals = {'capital_cost': 4300, 'om_costs': 0.015, 'base_to_peak_load_ratio': 0.9, 'system_life': 20}
        mg_wind_vals = {'capital_cost': 3000, 'om_costs': 0.02, 'base_to_peak_load_ratio': 0.75, 'system_life': 20}
        mg_diesel_vals = {'capacity_factor': 0.7, 'capital_cost': 721, 'om_costs': 0.1,
                          'base_to_peak_load_ratio': 0.5, 'system_life': 15, 'efficiency': 0.33}

        sa_pv_vals = {'capital_cost': 5500, 'om_costs': 0.012, 'base_to_peak_load_ratio': 0.9, 'system_life': 15}
        sa_diesel_vals = {'capacity_factor': 0.7, 'capital_cost': 938, 'om_costs': 0.1,
                          'base_to_peak_load_ratio': 0.5, 'system_life': 10, 'efficiency': 0.28}

        mg_vals = {'om_of_td_lines': 0.03, 'distribution_losses': 0.05, 'connection_cost_per_hh': 100}
        grid_vals = {'capacity_factor': 1, 'base_to_peak_load_ratio': grid_base_to_peak, 'om_of_td_lines': 0.03, 'connection_cost_per_hh': 125, 'system_life': 30}

        df = set_elec_targets(df, energy_per_hh_urban, energy_per_hh_rural)

        grid_lcoes_urban = get_grid_lcoe_table(energy_per_hh_urban, max_dist, num_people_per_hh, transmission_losses,
                                                grid_base_to_peak, grid_price, grid_capacity_investment, grid_vals)
        grid_lcoes_rural = get_grid_lcoe_table(energy_per_hh_rural, max_dist, num_people_per_hh, transmission_losses,
                                               grid_base_to_peak, grid_price, grid_capacity_investment, grid_vals)

        df = techs_only(df, diesel_price, (energy_per_hh_urban, energy_per_hh_rural), num_people_per_hh, mg_vals, mg_hydro_vals, mg_pv_vals,
                             mg_wind_vals, mg_diesel_vals, sa_pv_vals, sa_diesel_vals)
        df = run_elec(df, grid_lcoes_urban, grid_lcoes_rural, grid_price, existing_grid_cost_ratio, max_dist)
        df = results_columns(df, (energy_per_hh_urban, energy_per_hh_rural), grid_base_to_peak, num_people_per_hh, diesel_price, grid_price,
                                  transmission_losses, grid_capacity_investment, grid_vals, mg_vals, mg_hydro_vals,
                                  mg_pv_vals, mg_wind_vals, mg_diesel_vals, sa_pv_vals, sa_diesel_vals)
        calc_summaries(df, country).to_csv(summary_csv, header=True)

        df.to_csv(settlements_out_csv, index=False)

    if do_combine:
        print('\n --- Combining --- \n')
        df_base = pd.DataFrame()
        summaries = pd.DataFrame(columns=countries)

        for country in countries:
            print(country)
            df_add = pd.read_csv(os.path.join(output_dir, '{}_{}_{}.csv'.format(country, wb_tier_urban, diesel_tag)))
            df_base = df_base.append(df_add, ignore_index=True)

            summaries[country] = pd.read_csv(os.path.join(output_dir, '{}_{}_{}_summary.csv'.format(country, wb_tier_urban, diesel_tag)),
                                             squeeze=True, index_col=0)

        print('saving csv')
        df_base.to_csv(os.path.join(output_dir, '{}_{}.csv'.format(wb_tier_urban, diesel_tag)), index=False)
        summaries.to_csv(os.path.join(output_dir, '{}_{}_summary.csv'.format(wb_tier_urban, diesel_tag)))
