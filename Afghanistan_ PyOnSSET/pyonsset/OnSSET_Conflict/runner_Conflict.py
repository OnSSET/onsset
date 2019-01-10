# Pulls all the other functions together to make magic!
#
# Author: KTH dESA Last modified by Alexandros Korkovelos
# Date: 26 November 2018
# Python version: 3.7

import os
from onsset import *
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox

root = tk.Tk()
root.withdraw()
root.attributes("-topmost", True)

messagebox.showinfo('OnSSET', 'Open the specs file')
specs_path = filedialog.askopenfilename()

specs = pd.read_excel(specs_path, index_col=0)

countries = str(input('countries: ')).split()
countries = specs.index.tolist() if 'all' in countries else countries

choice = int(input('Enter 1 to split, 2 to prepare the inputs, 3 to run a scenario: '))

if choice == 1:
    messagebox.showinfo('OnSSET', 'Open the csv file with GIS data')
    settlements_csv = filedialog.askopenfilename()
    messagebox.showinfo('OnSSET', 'Select the folder to save split countries')
    base_dir = filedialog.asksaveasfilename()

    print('\n --- Splitting --- \n')

    df = pd.read_csv(settlements_csv)

    for country in countries:
        print(country)
        df.loc[df[SET_COUNTRY] == country].to_csv(base_dir + '.csv', index=False)

elif choice == 2:
    messagebox.showinfo('OnSSET', 'Open the file containing separated countries')
    base_dir = filedialog.askopenfilename()
    messagebox.showinfo('OnSSET', 'Browse to result folder and name the calibrated file')
    output_dir = filedialog.asksaveasfilename()

    print('\n --- Prepping --- \n')

    for country in countries:
        print(country)
        settlements_in_csv = base_dir # os.path.join(base_dir, '{}.csv'.format(country))
        settlements_out_csv = output_dir + '.csv' # os.path.join(output_dir, '{}.csv'.format(country))

        onsseter = SettlementProcessor(settlements_in_csv)

        onsseter.condition_df(country)
        onsseter.grid_penalties()
        onsseter.calc_wind_cfs()

        pop_actual = specs.loc[country, SPE_POP]
        pop_future = specs.loc[country, SPE_POP_FUTURE]
        urban_current = specs.loc[country, SPE_URBAN]
        urban_future = specs.loc[country, SPE_URBAN_FUTURE]
        urban_cutoff = specs.loc[country, SPE_URBAN_CUTOFF]
        start_year = int(specs.loc[country, SPE_START_YEAR])
        end_year = int(specs.loc[country, SPE_END_YEAR])
        time_step = int(specs.loc[country, SPE_TIMESTEP])

        elec_actual = specs.loc[country, SPE_ELEC]
        pop_cutoff = specs.loc[country, SPE_POP_CUTOFF1]
        min_night_lights = specs.loc[country, SPE_MIN_NIGHT_LIGHTS]
        max_grid_dist = specs.loc[country, SPE_MAX_GRID_DIST]
        max_road_dist = specs.loc[country, SPE_MAX_ROAD_DIST]
        pop_tot = specs.loc[country, SPE_POP]
        pop_cutoff2 = specs.loc[country, SPE_POP_CUTOFF2]
        dist_to_trans = specs.loc[country, SPE_DIST_TO_TRANS]

        urban_cutoff, urban_modelled = onsseter.calibrate_pop_and_urban(pop_actual, pop_future, urban_current,
                                                                        urban_future, urban_cutoff, start_year, end_year, time_step)

        min_night_lights, dist_to_trans, max_grid_dist, max_road_dist, elec_modelled, pop_cutoff, pop_cutoff2, rural_elec_ratio, urban_elec_ratio = \
            onsseter.elec_current_and_future(elec_actual, pop_cutoff, dist_to_trans, min_night_lights, max_grid_dist,
                                             max_road_dist, pop_tot, pop_cutoff2, start_year)

        onsseter.grid_reach_estimate(start_year, gridspeed=9999)

        specs.loc[country, SPE_URBAN_MODELLED] = urban_modelled
        specs.loc[country, SPE_URBAN_CUTOFF] = urban_cutoff
        specs.loc[country, SPE_MIN_NIGHT_LIGHTS] = min_night_lights
        specs.loc[country, SPE_MAX_GRID_DIST] = max_grid_dist
        specs.loc[country, SPE_MAX_ROAD_DIST] = max_road_dist
        specs.loc[country, SPE_ELEC_MODELLED] = elec_modelled
        specs.loc[country, SPE_POP_CUTOFF1] = pop_cutoff
        specs.loc[country, SPE_POP_CUTOFF2] = pop_cutoff2
        specs.loc[country, 'rural_elec_ratio'] = rural_elec_ratio
        specs.loc[country, 'urban_elec_ratio'] = urban_elec_ratio


        try:
            specs.to_excel(specs_path)
        except ValueError:
            specs.to_excel(specs_path + '.xlsx')

        onsseter.df.to_csv(settlements_out_csv, index=False)

elif choice == 3:

    # wb_tiers_all = {1: 7.738, 2: 43.8, 3: 160.6, 4: 423.4, 5: 598.6}
    # print("""\nWorld Bank Tiers of Electricity Access
    #       1: {} kWh/person/year
    #       2: {} kWh/person/year
    #       3: {} kWh/person/year
    #       4: {} kWh/person/year
    #       5: {} kWh/person/year""".format(wb_tiers_all[1], wb_tiers_all[2], wb_tiers_all[3],
    #                                       wb_tiers_all[4], wb_tiers_all[5]))
    # wb_tier_urban = int(input('Enter the tier number for urban: '))
    # wb_tier_rural = int(input('Enter the tier number for rural: '))

    diesel_high = True if 'y' in input('Use high diesel value? <y/n> ') else False
    diesel_tag = 'high' if diesel_high else 'low'
    #do_combine = True if 'y' in input('Combine countries into a single file? <y/n> ') else False

    messagebox.showinfo('OnSSET', 'Open the csv file with calibrated GIS data')
    base_dir = filedialog.askopenfilename()
    messagebox.showinfo('OnSSET', 'Browse to result folder and name the scenario to save outputs')
    output_dir = filedialog.asksaveasfilename()

    print('\n --- Running scenario --- \n')

    for country in countries:
        # create country_specs here
        print(' --- {} --- {} --- '.format(country, diesel_tag))
        settlements_in_csv = base_dir # os.path.join(base_dir, '{}.csv'.format(country))
        settlements_out_csv = output_dir + '.csv' # os.path.join(output_dir, '{}_{}_{}.csv'.format(country, wb_tier_urban, diesel_tag))
        summary_csv = output_dir + 'summary.csv'

        onsseter = SettlementProcessor(settlements_in_csv)

        start_year = specs[SPE_START_YEAR][country]
        end_year = specs[SPE_END_YEAR][country]
        time_step = specs[SPE_TIMESTEP][country]

        diesel_price = specs[SPE_DIESEL_PRICE_HIGH][country] if diesel_high else specs[SPE_DIESEL_PRICE_LOW][country]
        grid_price = specs[SPE_GRID_PRICE][country]
        existing_grid_cost_ratio = specs[SPE_EXISTING_GRID_COST_RATIO][country]
        num_people_per_hh_rural = float(specs[SPE_NUM_PEOPLE_PER_HH_RURAL][country])
        num_people_per_hh_urban = float(specs[SPE_NUM_PEOPLE_PER_HH_URBAN][country])
        max_grid_extension_dist = float(specs[SPE_MAX_GRID_EXTENSION_DIST][country])
        urban_elec_ratio = float(specs['rural_elec_ratio'][country])
        rural_elec_ratio = float(specs['urban_elec_ratio'][country])
        # energy_per_pp_rural = wb_tiers_all[wb_tier_rural]
        # energy_per_pp_urban = wb_tiers_all[wb_tier_urban]
        mg_pv_cap_cost = specs.loc[country, SPE_CAP_COST_MG_PV]
        grid_cap_gen_limit = specs.loc[country, 'NewGridGenerationCapacityTimestepLimit']
        #eleclimit = specs[SPE_ELEC_LIMIT][country]
        #investlimit = specs[SPE_INVEST_LIMIT][country]

        #step_year = start_year + time_step


        Technology.set_default_values(base_year=start_year,
                                      start_year=start_year,
                                      end_year=end_year,
                                      discount_rate=0.12,
                                      # grid_cell_area=1,
                                      mv_line_cost=9000,
                                      lv_line_cost=5000,
                                      mv_line_capacity=50,
                                      lv_line_capacity=10,
                                      lv_line_max_length=30,
                                      hv_line_cost=120000,
                                      mv_line_max_length=50,
                                      hv_lv_transformer_cost=3500,
                                      mv_increase_rate=0.1)

        grid_calc = Technology(om_of_td_lines=0.03,
                               distribution_losses=float(specs[SPE_GRID_LOSSES][country]),
                               connection_cost_per_hh=122,
                               base_to_peak_load_ratio=float(specs[SPE_BASE_TO_PEAK][country]),
                               capacity_factor=1,
                               tech_life=30,
                               grid_capacity_investment=float(specs[SPE_GRID_CAPACITY_INVESTMENT][country]),
                               grid_penalty_ratio=1,
                               grid_price=grid_price)

        mg_hydro_calc = Technology(om_of_td_lines=0.03,
                                   distribution_losses=0.05,
                                   connection_cost_per_hh=100,
                                   base_to_peak_load_ratio=1,
                                   capacity_factor=0.5,
                                   tech_life=30,
                                   capital_cost=2500,
                                   om_costs=0.02)

        mg_wind_calc = Technology(om_of_td_lines=0.03,
                                  distribution_losses=0.05,
                                  connection_cost_per_hh=100,
                                  base_to_peak_load_ratio=0.9,
                                  capital_cost=2300,
                                  om_costs=0.035,
                                  tech_life=20)

        mg_pv_calc = Technology(om_of_td_lines=0.03,
                                distribution_losses=0.05,
                                connection_cost_per_hh=100,
                                base_to_peak_load_ratio=0.9,
                                tech_life=20,
                                om_costs=0.018,
                                capital_cost=mg_pv_cap_cost)

        sa_pv_calc = Technology(base_to_peak_load_ratio=0.9,
                                tech_life=15,
                                om_costs=0.018,
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
                                    capital_cost=1200,
                                    diesel_price=diesel_price,
                                    diesel_truck_consumption=33.7,
                                    diesel_truck_volume=15000)

        sa_diesel_calc = Technology(base_to_peak_load_ratio=0.5,
                                    capacity_factor=0.7,
                                    tech_life=10,
                                    om_costs=0.1,
                                    capital_cost=2000,
                                    diesel_price=diesel_price,
                                    standalone=True,
                                    efficiency=0.28,
                                    diesel_truck_consumption=14,
                                    diesel_truck_volume=300)

        # Used to identify the steps and include them in the results

        # ### FIRST RUN - NO TIMESTEP
        #
        #
        # time_step = 12
        # year = 2030
        # eleclimits = {2030: 1}
        #
        # # eleclimit = float(input('Provide the targeted electrification rate in {}:'.format(year)))
        # eleclimit = eleclimits[year]
        # # investlimit = int(input('Provide the targeted investment limit (in USD) for the year {}:'.format(year)))
        #
        # onsseter.set_scenario_variables(year, num_people_per_hh_rural, num_people_per_hh_urban, time_step, start_year,
        #                                 urban_elec_ratio, rural_elec_ratio)
        #
        #
        # onsseter.calculate_off_grid_lcoes(mg_hydro_calc, mg_wind_calc, mg_pv_calc, sa_pv_calc, mg_diesel_calc,
        #                                   sa_diesel_calc, year, start_year, end_year, time_step)
        #
        # onsseter.pre_electrification(grid_calc, grid_price, year, time_step, start_year)
        #
        # onsseter.run_elec(grid_calc, max_grid_extension_dist, year, start_year, end_year, time_step, grid_cap_gen_limit)
        #
        # onsseter.results_columns(mg_hydro_calc, mg_wind_calc, mg_pv_calc, sa_pv_calc, mg_diesel_calc, sa_diesel_calc,
        #                          grid_calc, year)
        #
        # onsseter.calculate_investments(mg_hydro_calc, mg_wind_calc, mg_pv_calc, sa_pv_calc, mg_diesel_calc,
        #                sa_diesel_calc, grid_calc, year, end_year, time_step)
        #
        # onsseter.apply_limitations(eleclimit, year, time_step)
        #
        # onsseter.final_decision(mg_hydro_calc, mg_wind_calc, mg_pv_calc, sa_pv_calc, mg_diesel_calc, sa_diesel_calc,
        #                         grid_calc, year, end_year, time_step)
        #
        # onsseter.delete_redundant_columns(year)
        #
        # ### END OF FIRST RUN

        # yearsofanalysis = list(range((start_year + time_step), end_year + 1, time_step))
        yearsofanalysis = [2030]
        eleclimits = {2030: 1}
        time_steps = {2030: 15}

        # This is used in the calculation of summaries at the end

        elements = ["1.Population", "2.New_Connections", "3.Capacity", "4.Investment"]
        techs = ["Grid", "SA_Diesel", "SA_PV", "MG_Diesel", "MG_PV", "MG_Wind", "MG_Hydro"]

        sumtechs = []

        for element in elements:
            for tech in techs:
                sumtechs.append(element + "_" + tech)

        total_rows = len(sumtechs)

        df_summary = pd.DataFrame(columns=yearsofanalysis)

        for row in range(0, total_rows):
            df_summary.loc[sumtechs[row]] = "Nan"

        ## If one wants time steps please un-comment below section within triple dashes
        ###


        # The runner beggins here..

        for year in yearsofanalysis:

            #eleclimit = float(input('Provide the targeted electrification rate in {}:'.format(year)))
            eleclimit = eleclimits[year]
            time_step = time_steps[year]
            #investlimit = int(input('Provide the targeted investment limit (in USD) for the year {}:'.format(year)))

            onsseter.set_scenario_variables(year, num_people_per_hh_rural, num_people_per_hh_urban, time_step,
                                            start_year, urban_elec_ratio, rural_elec_ratio)

            onsseter.calculate_off_grid_lcoes(mg_hydro_calc, mg_wind_calc, mg_pv_calc, sa_pv_calc, mg_diesel_calc, sa_diesel_calc, year, start_year, end_year, time_step)

            onsseter.pre_electrification(grid_calc, grid_price, year, time_step, start_year)

            onsseter.run_elec(grid_calc, max_grid_extension_dist, year, start_year, end_year, time_step, grid_cap_gen_limit)

            # if year == end_year:
            #     onsseter.calculategridyears(start_year, year, gridspeed=10)
            # else:
            #     pass

            onsseter.results_columns(mg_hydro_calc, mg_wind_calc, mg_pv_calc, sa_pv_calc, mg_diesel_calc, sa_diesel_calc, grid_calc, year)

            onsseter.calculate_investments(mg_hydro_calc, mg_wind_calc, mg_pv_calc, sa_pv_calc, mg_diesel_calc,
                                           sa_diesel_calc, grid_calc, year, end_year, time_step)

            onsseter.apply_limitations(eleclimit, year, time_step)

            onsseter.final_decision(mg_hydro_calc, mg_wind_calc, mg_pv_calc, sa_pv_calc, mg_diesel_calc, sa_diesel_calc, grid_calc, year, end_year, time_step)

            onsseter.calc_summaries(df_summary, sumtechs, year)

        ### Time step ends here

    df_summary.to_csv(summary_csv, index=sumtechs)
    onsseter.df.to_csv(settlements_out_csv, index=False)

    # if do_combine:
    #     print('\n --- Combining --- \n')
    #     df_base = pd.DataFrame()
    #     summaries = pd.DataFrame(columns=countries)
    #
    #     for country in countries:
    #         print(country)
    #         df_add = pd.read_csv(os.path.join(output_dir, '{}_{}_{}.csv'.format(country, wb_tier_urban, diesel_tag)))
    #         df_base = df_base.append(df_add, ignore_index=True)
    #
    #         summaries[country] = pd.read_csv(os.path.join(output_dir, '{}_{}_{}_summary.csv'.format(country,
    #                                                                                                 wb_tier_urban,
    #                                                                                                 diesel_tag)),
    #                                          squeeze=True, index_col=0)
    #
    #     print('saving csv')
    #     df_base.to_csv(os.path.join(output_dir, '{}_{}.csv'.format(wb_tier_urban, diesel_tag)), index=False)
    #     summaries.to_csv(os.path.join(output_dir, '{}_{}_summary.csv'.format(wb_tier_urban, diesel_tag)))
