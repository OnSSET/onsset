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

    try:
        os.makedirs(base_dir)
    except FileExistsError:
        pass

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

        onsseter = SettlementProcessor(settlements_in_csv)

        onsseter.condition_df()
        onsseter.grid_penalties()
        onsseter.calc_wind_cfs()

        pop_actual = specs.loc[country, SPE_POP]
        pop_future = specs.loc[country, SPE_POP_FUTURE]
        urban_current = specs.loc[country, SPE_URBAN]
        urban_future = specs.loc[country, SPE_URBAN_FUTURE]
        urban_cutoff = specs.loc[country, SPE_URBAN_CUTOFF]

        elec_actual = specs.loc[country, SPE_ELEC]
        pop_cutoff = specs.loc[country, SPE_POP_CUTOFF1]
        min_night_lights = specs.loc[country, SPE_MIN_NIGHT_LIGHTS]
        max_grid_dist = specs.loc[country, SPE_MAX_GRID_DIST]
        max_road_dist = specs.loc[country, SPE_MAX_ROAD_DIST]
        pop_tot = specs.loc[country, SPE_POP]
        pop_cutoff2 = specs.loc[country, SPE_POP_CUTOFF2]

        urban_cutoff, urban_modelled = onsseter.calibrate_pop_and_urban(pop_actual, pop_future, urban_current,
                                                                        urban_future, urban_cutoff)
        min_night_lights, max_grid_dist, max_road_dist, elec_modelled, pop_cutoff, pop_cutoff2 = \
            onsseter.elec_current_and_future(elec_actual, pop_cutoff, min_night_lights,
                                             max_grid_dist, max_road_dist, pop_tot, pop_cutoff2)

        specs.loc[country, SPE_MIN_NIGHT_LIGHTS] = min_night_lights
        specs.loc[country, SPE_MAX_GRID_DIST] = max_grid_dist
        specs.loc[country, SPE_MAX_ROAD_DIST] = max_road_dist
        specs.loc[country, SPE_ELEC_MODELLED] = elec_modelled
        specs.loc[country, SPE_POP_CUTOFF1] = pop_cutoff
        specs.loc[country, SPE_POP_CUTOFF2] = pop_cutoff2

        specs.to_excel(specs_path)
        onsseter.df.to_csv(settlements_in_csv, index=False)

elif choice == 3:
    base_dir = str(input('Enter the base file directory containing separated and prepped countries: '))
    output_dir = str(input('Enter the output directory (can contain multiple runs): '))

    wb_tiers_all = {1: 7.738, 2: 43.8, 3: 160.6, 4: 423.4, 5: 598.6}
    wb_tier_urban = int(input("""\nWorld Bank Tiers of Electricity Access\n
                              1: {} kWh/person/year\n
                              2: {} kWh/person/year\n
                              3: {} kWh/person/year\n
                              4: {} kWh/person/year\n
                              5: {} kWh/person/year\n
                              Enter the tier number for urban: """.format(wb_tiers_all[1], wb_tiers_all[2],
                                                                          wb_tiers_all[3], wb_tiers_all[4],
                                                                          wb_tiers_all[5])))
    wb_tier_rural = int(input("""\nWorld Bank Tiers of Electricity Access\n
                              1: {} kWh/person/year\n
                              2: {} kWh/person/year\n
                              3: {} kWh/person/year\n
                              4: {} kWh/person/year\n
                              5: {} kWh/person/year\n
                              Enter the tier number for rural: """.format(wb_tiers_all[1], wb_tiers_all[2],
                                                                          wb_tiers_all[3], wb_tiers_all[4],
                                                                          wb_tiers_all[5])))

    diesel_high = True if 'y' in input('Use high diesel value? <y/n> ') else False
    diesel_tag = 'high' if diesel_high else 'low'
    do_combine = True if 'y' in input('Combine countries into a single file? <y/n> ') else False

    print('\n --- Running scenario --- \n')

    try:
        os.makedirs(output_dir)
    except FileExistsError:
        pass

    for country in countries:
        # create country_specs here
        print(' --- {} --- {} --- {} --- '.format(country, wb_tier_urban, diesel_tag))
        settlements_in_csv = os.path.join(base_dir, '{}.csv'.format(country))
        settlements_out_csv = os.path.join(output_dir, '{}_{}_{}.csv'.format(country, wb_tier_urban, diesel_tag))
        summary_csv = os.path.join(output_dir, '{}_{}_{}_summary.csv'.format(country, wb_tier_urban, diesel_tag))

        onsseter = SettlementProcessor(settlements_in_csv)

        diesel_price = specs[SPE_DIESEL_PRICE_HIGH][country] if diesel_high else specs[SPE_DIESEL_PRICE_LOW][country]
        grid_price = specs[SPE_GRID_PRICE][country]
        existing_grid_cost_ratio = specs[SPE_EXISTING_GRID_COST_RATIO][country]
        num_people_per_hh_rural = float(specs[SPE_NUM_PEOPLE_PER_HH_RURAL][country])
        num_people_per_hh_urban = float(specs[SPE_NUM_PEOPLE_PER_HH_URBAN][country])
        max_grid_extension_dist = float(specs[SPE_MAX_GRID_EXTENSION_DIST][country])
        energy_per_hh_rural = wb_tiers_all[wb_tier_rural] * num_people_per_hh_rural
        energy_per_hh_urban = wb_tiers_all[wb_tier_urban] * num_people_per_hh_urban

        grid_calc = Technology(om_of_td_lines=0.03,
                               distribution_losses=float(specs[SPE_GRID_LOSSES][country]),
                               connection_cost_per_hh=125,
                               base_to_peak_load_ratio=float(specs[SPE_BASE_TO_PEAK][country]),
                               capacity_factor=1,
                               tech_life=30,
                               grid_capacity_investment=float(specs[SPE_GRID_CAPACITY_INVESTMENT][country]),
                               grid_price=grid_price)

        mg_hydro_calc = Technology(om_of_td_lines=0.03,
                                   distribution_losses=0.05,
                                   connection_cost_per_hh=100,
                                   base_to_peak_load_ratio=1,
                                   capacity_factor=0.5,
                                   tech_life=30,
                                   capital_cost=5000,
                                   om_costs=0.02)

        mg_wind_calc = Technology(om_of_td_lines=0.03,
                                  distribution_losses=0.05,
                                  connection_cost_per_hh=100,
                                  base_to_peak_load_ratio=0.75,
                                  capital_cost=3000,
                                  om_costs=0.02,
                                  tech_life=20)

        mg_pv_calc = Technology(om_of_td_lines=0.03,
                                distribution_losses=0.05,
                                connection_cost_per_hh=100,
                                base_to_peak_load_ratio=0.9,
                                tech_life=20,
                                om_costs=0.015,
                                capital_cost=4300)

        sa_pv_calc = Technology(base_to_peak_load_ratio=0.9,
                                tech_life=15,
                                om_costs=0.012,
                                capital_cost=5500,
                                standalone=True)

        mg_diesel_calc = Technology(om_of_td_lines=0.03,
                                    distribution_losses=0.05,
                                    connection_cost_per_hh=100,
                                    base_to_peak_load_ratio=0.5,
                                    capacity_factor=0.7,
                                    tech_life=15,
                                    om_costs=0.1,
                                    efficiency=0.33,
                                    capital_cost=721,
                                    diesel_price=diesel_price,
                                    diesel_truck_consumption=33.7,
                                    diesel_truck_volume=15000)

        sa_diesel_calc = Technology(base_to_peak_load_ratio=0.5,
                                    capacity_factor=0.7,
                                    tech_life=10,
                                    om_costs=0.1,
                                    capital_cost=938,
                                    diesel_price=diesel_price,
                                    standalone=True,
                                    efficiency=0.28,
                                    diesel_truck_consumption=14,
                                    diesel_truck_volume=300)

        onsseter.set_scenario_variables(energy_per_hh_rural, energy_per_hh_urban,
                                        num_people_per_hh_rural, num_people_per_hh_urban)

        grid_lcoes_rural = grid_calc.get_grid_table(energy_per_hh_rural, num_people_per_hh_rural,
                                                    max_grid_extension_dist)
        grid_lcoes_urban = grid_calc.get_grid_table(energy_per_hh_urban, num_people_per_hh_urban,
                                                    max_grid_extension_dist)

        onsseter.calculate_off_grid_lcoes(mg_hydro_calc, mg_wind_calc, mg_pv_calc,
                                          sa_pv_calc, mg_diesel_calc, sa_diesel_calc)
        onsseter.run_elec(grid_lcoes_rural, grid_lcoes_urban, grid_price,
                          existing_grid_cost_ratio, max_grid_extension_dist)
        onsseter.results_columns(mg_hydro_calc, mg_wind_calc, mg_pv_calc, sa_pv_calc,
                                 mg_diesel_calc, sa_diesel_calc, grid_calc)

        summary = onsseter.calc_summaries()
        summary.name = country
        summary.to_csv(summary_csv, header=True)

        onsseter.df.to_csv(settlements_out_csv, index=False)

    if do_combine:
        print('\n --- Combining --- \n')
        df_base = pd.DataFrame()
        summaries = pd.DataFrame(columns=countries)

        for country in countries:
            print(country)
            df_add = pd.read_csv(os.path.join(output_dir, '{}_{}_{}.csv'.format(country, wb_tier_urban, diesel_tag)))
            df_base = df_base.append(df_add, ignore_index=True)

            summaries[country] = pd.read_csv(os.path.join(output_dir, '{}_{}_{}_summary.csv'.format(country,
                                                                                                    wb_tier_urban,
                                                                                                    diesel_tag)),
                                             squeeze=True, index_col=0)

        print('saving csv')
        df_base.to_csv(os.path.join(output_dir, '{}_{}.csv'.format(wb_tier_urban, diesel_tag)), index=False)
        summaries.to_csv(os.path.join(output_dir, '{}_{}_summary.csv'.format(wb_tier_urban, diesel_tag)))
