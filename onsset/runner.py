# Defines the modules

import logging
import os
import numpy as np

import pandas as pd
from onsset import (SET_ELEC_ORDER, SET_LCOE_GRID, SET_MIN_GRID_DIST, SET_GRID_PENALTY,
                    SET_MV_CONNECT_DIST, SET_WINDCF, SettlementProcessor, Technology, SET_MIN_OVERALL_CODE,
                    SET_POP, SET_NEW_CAPACITY, SET_ELEC_FINAL_CODE, SET_NEW_CONNECTIONS, SET_INVESTMENT_COST)

try:
    from onsset.specs import (SPE_COUNTRY, SPE_ELEC, SPE_ELEC_MODELLED,
                              SPE_ELEC_RURAL, SPE_ELEC_URBAN, SPE_END_YEAR,
                              SPE_GRID_CAPACITY_INVESTMENT, SPE_GRID_LOSSES,
                              SPE_MAX_GRID_EXTENSION_DIST,
                              SPE_NUM_PEOPLE_PER_HH_RURAL,
                              SPE_NUM_PEOPLE_PER_HH_URBAN, SPE_POP, SPE_POP_FUTURE,
                              SPE_START_YEAR, SPE_URBAN, SPE_URBAN_FUTURE,
                              SPE_URBAN_MODELLED)
except ImportError:
    from specs import (SPE_COUNTRY, SPE_ELEC, SPE_ELEC_MODELLED,
                       SPE_ELEC_RURAL, SPE_ELEC_URBAN, SPE_END_YEAR,
                       SPE_GRID_CAPACITY_INVESTMENT, SPE_GRID_LOSSES,
                       SPE_MAX_GRID_EXTENSION_DIST,
                       SPE_NUM_PEOPLE_PER_HH_RURAL,
                       SPE_NUM_PEOPLE_PER_HH_URBAN, SPE_POP, SPE_POP_FUTURE,
                       SPE_START_YEAR, SPE_URBAN, SPE_URBAN_FUTURE,
                       SPE_URBAN_MODELLED)
from openpyxl import load_workbook

logging.basicConfig(format='%(asctime)s\t\t%(message)s', level=logging.DEBUG)


def calibration(specs_path, csv_path, specs_path_calib, calibrated_csv_path):
    """

    Arguments
    ---------
    specs_path
    csv_path
    specs_path_calib
    calibrated_csv_path
    """
    specs_data = pd.read_excel(specs_path, sheet_name='SpecsData')
    settlements_in_csv = csv_path
    settlements_out_csv = calibrated_csv_path

    onsseter = SettlementProcessor(settlements_in_csv)

    num_people_per_hh_rural = float(specs_data.iloc[0][SPE_NUM_PEOPLE_PER_HH_RURAL])
    num_people_per_hh_urban = float(specs_data.iloc[0][SPE_NUM_PEOPLE_PER_HH_URBAN])

    # RUN_PARAM: these are the annual household electricity targets
    tier_1 = 38.7  # 38.7 refers to kWh/household/year. It is the mean value between Tier 1 and Tier 2
    tier_2 = 219
    tier_3 = 803
    tier_4 = 2117
    tier_5 = 2993

    onsseter.prepare_wtf_tier_columns(num_people_per_hh_rural, num_people_per_hh_urban,
                                      tier_1, tier_2, tier_3, tier_4, tier_5)
    onsseter.condition_df()
    onsseter.df[SET_GRID_PENALTY] = onsseter.grid_penalties(onsseter.df)

    onsseter.df[SET_WINDCF] = onsseter.calc_wind_cfs()

    pop_actual = specs_data.loc[0, SPE_POP]
    pop_future = specs_data.loc[0, SPE_POP_FUTURE]
    urban_current = specs_data.loc[0, SPE_URBAN]
    urban_future = specs_data.loc[0, SPE_URBAN_FUTURE]
    start_year = int(specs_data.loc[0, SPE_START_YEAR])
    end_year = int(specs_data.loc[0, SPE_END_YEAR])

    intermediate_year = 2025
    elec_actual = specs_data.loc[0, SPE_ELEC]
    elec_actual_urban = specs_data.loc[0, SPE_ELEC_URBAN]
    elec_actual_rural = specs_data.loc[0, SPE_ELEC_RURAL]

    pop_modelled, urban_modelled = onsseter.calibrate_current_pop_and_urban(pop_actual, urban_current)



    elec_modelled, rural_elec_ratio, urban_elec_ratio = \
        onsseter.elec_current_and_future(elec_actual, elec_actual_urban, elec_actual_rural, start_year)

    # In case there are limitations in the way grid expansion is moving in a country, 
    # this can be reflected through gridspeed.
    # In this case the parameter is set to a very high value therefore is not taken into account.

    specs_data.loc[0, SPE_URBAN_MODELLED] = urban_modelled
    specs_data.loc[0, SPE_ELEC_MODELLED] = elec_modelled
    specs_data.loc[0, 'rural_elec_ratio_modelled'] = rural_elec_ratio
    specs_data.loc[0, 'urban_elec_ratio_modelled'] = urban_elec_ratio

    book = load_workbook(specs_path)
    writer = pd.ExcelWriter(specs_path_calib, engine='openpyxl')
    writer.book = book
    # RUN_PARAM: Here the calibrated "specs" data are copied to a new tab called "SpecsDataCalib". 
    # This is what will later on be used to feed the model
    specs_data.to_excel(writer, sheet_name='SpecsDataCalib', index=False)
    writer.save()
    writer.close()

    logging.info('Calibration finished. Results are transferred to the csv file')
    onsseter.df.to_csv(settlements_out_csv, index=False)


def scenario(specs_path, calibrated_csv_path, results_folder, summary_folder):
    """

    Arguments
    ---------
    specs_path : str
    calibrated_csv_path : str
    results_folder : str
    summary_folder : str

    """

    scenario_info = pd.read_excel(specs_path, sheet_name='ScenarioInfo')
    scenarios = scenario_info['Scenario']
    scenario_parameters = pd.read_excel(specs_path, sheet_name='ScenarioParameters')
    specs_data = pd.read_excel(specs_path, sheet_name='SpecsDataCalib')
    print(specs_data.loc[0, SPE_COUNTRY])

    for scenario in scenarios:
        print('Scenario: ' + str(scenario + 1))
        country_id = specs_data.iloc[0]['CountryCode']

        # Population lever
        pop_index = scenario_info.iloc[scenario]['PopIndex']

        pop_future = scenario_parameters.iloc[pop_index]['Population2030']
        urban_future = scenario_parameters.iloc[pop_index]['UrbanRatio2030']

        #  Discount rate lever
        disscount_index = scenario_info.iloc[scenario]['DiscountIndex']
        disc_rate = scenario_parameters.iloc[disscount_index]['DiscRate']

        # Electrification rate target lever
        electification_rate_index = scenario_info.iloc[scenario]['Electrification_rate']

        electrification_rate_2030 = scenario_parameters.iloc[electification_rate_index]['ElecRate2030']
        electrification_rate_2025 = scenario_parameters.iloc[electification_rate_index]['ElecRate2025']

        # Productive uses lever
        productive_index = scenario_info.iloc[scenario]['Productive_uses_demand']
        productive_demand = scenario_parameters.iloc[productive_index]['ProductiveDemand']

        #  Demand lever
        tier_index = scenario_info.iloc[scenario]['Target_electricity_consumption_level']
        rural_tier = int(scenario_parameters.iloc[tier_index]['RuralTargetTier'])
        urban_tier = int(scenario_parameters.iloc[tier_index]['UrbanTargetTier'])

        # PV system cost
        pv_index = scenario_info.iloc[scenario]['PV_cost_adjust']
        pv_capital_cost_adjust = float(scenario_parameters.iloc[pv_index]['PV_Cost_adjust'])

        settlements_in_csv = calibrated_csv_path
        settlements_out_csv = os.path.join(results_folder,
                                           '{}-{}_{}_{}_{}_{}_{}.csv'.format(country_id, tier_index, productive_index,
                                                                               pv_index, disscount_index, electification_rate_index, pop_index))
        summary_csv = os.path.join(summary_folder,
                                   '{}-{}_{}_{}_{}_{}_{}_summary.csv'.format(country_id, tier_index, productive_index,
                                                                               pv_index, disscount_index, electification_rate_index, pop_index))

        onsseter = SettlementProcessor(settlements_in_csv)

        start_year = specs_data.iloc[0][SPE_START_YEAR]
        intermediate_year = specs_data.iloc[0]['Intermediate_year']
        end_year = specs_data.iloc[0][SPE_END_YEAR]

        num_people_per_hh_rural = float(specs_data.iloc[0][SPE_NUM_PEOPLE_PER_HH_RURAL])
        num_people_per_hh_urban = float(specs_data.iloc[0][SPE_NUM_PEOPLE_PER_HH_URBAN])
        max_grid_extension_dist = 50

        intermediate_electrification_target = electrification_rate_2025
        end_year_electrification_rate_target = electrification_rate_2030

        # West grid specifications
        auto_intensification_ouest = 0
        annual_new_grid_connections_limit_ouest = {intermediate_year: 999999999,
                                                   end_year: 999999999}
        annual_grid_cap_gen_limit_ouest = {intermediate_year: 999999999,
                                           end_year: 999999999}
        grid_generation_cost_ouest = 0.03
        grid_power_plants_capital_cost_ouest = 2000
        grid_losses_ouest = 0.08

        # South grid specifications
        auto_intensification_sud = 0
        annual_new_grid_connections_limit_sud = {intermediate_year: 999999999,
                                                 end_year: 999999999}
        annual_grid_cap_gen_limit_sud = {intermediate_year: 999999999,
                                         end_year: 999999999}
        grid_generation_cost_sud = 0.06
        grid_generation_cost_sud = 0.06
        grid_power_plants_capital_cost_sud = 2000
        grid_losses_sud = 0.08

        # East grid specifications
        auto_intensification_est = 0
        annual_new_grid_connections_limit_est = {intermediate_year: 999999999,
                                                 end_year: 999999999}
        annual_grid_cap_gen_limit_est = {intermediate_year: 999999999,
                                         end_year: 999999999}
        grid_generation_cost_est = 0.08
        grid_power_plants_capital_cost_est = 2000
        grid_losses_est = 0.08

        # RUN_PARAM: Fill in general and technology specific parameters (e.g. discount rate, losses etc.)
        Technology.set_default_values(base_year=start_year,
                                      start_year=start_year,
                                      end_year=end_year,
                                      discount_rate=disc_rate)

        grid_calc_ouest = Technology(om_of_td_lines=0.1,
                                     distribution_losses=grid_losses_ouest,
                                     connection_cost_per_hh=150,
                                     base_to_peak_load_ratio=0.8,
                                     capacity_factor=1,
                                     tech_life=30,
                                     grid_capacity_investment=grid_power_plants_capital_cost_ouest,
                                     grid_price=grid_generation_cost_ouest)

        grid_calc_sud = Technology(om_of_td_lines=0.1,
                                   distribution_losses=grid_losses_sud,
                                   connection_cost_per_hh=150,
                                   base_to_peak_load_ratio=0.8,
                                   capacity_factor=1,
                                   tech_life=30,
                                   grid_capacity_investment=grid_power_plants_capital_cost_sud,
                                   grid_price=grid_generation_cost_sud)

        grid_calc_est = Technology(om_of_td_lines=0.1,
                                   distribution_losses=grid_losses_est,
                                   connection_cost_per_hh=150,
                                   base_to_peak_load_ratio=0.8,
                                   capacity_factor=1,
                                   tech_life=30,
                                   grid_capacity_investment=grid_power_plants_capital_cost_est,
                                   grid_price=grid_generation_cost_est)

        mg_hydro_calc = Technology(om_of_td_lines=0.02,
                                   distribution_losses=0.05,
                                   connection_cost_per_hh=92,
                                   base_to_peak_load_ratio=0.85,
                                   capacity_factor=0.5,
                                   tech_life=35,
                                   capital_cost={float("inf"): 5000},
                                   om_costs=0.03,
                                   mini_grid=True)

        mg_wind_calc = Technology(om_of_td_lines=0.02,
                                  distribution_losses=0.05,
                                  connection_cost_per_hh=92,
                                  base_to_peak_load_ratio=0.85,
                                  capital_cost={float("inf"): 3750},
                                  om_costs=0.02,
                                  tech_life=20,
                                  mini_grid=True)

        mg_pv_calc = Technology(om_of_td_lines=0.02,
                                distribution_losses=0.05,
                                connection_cost_per_hh=92,
                                base_to_peak_load_ratio=0.85,
                                tech_life=25,
                                om_costs=0.015,
                                capital_cost={float("inf"): 6327 * pv_capital_cost_adjust},
                                mini_grid=True)

        sa_pv_calc = Technology(base_to_peak_load_ratio=0.9,
                                tech_life=25,
                                om_costs=0.02,
                                capital_cost={float("inf"): 6950 * pv_capital_cost_adjust,
                                              1: 4470 * pv_capital_cost_adjust,
                                              0.100: 6380 * pv_capital_cost_adjust,
                                              0.050: 8780 * pv_capital_cost_adjust,
                                              0.020: 9620 * pv_capital_cost_adjust
                                              },
                                standalone=True)

        mg_diesel_calc = Technology(om_of_td_lines=0.02,
                                    distribution_losses=0.05,
                                    connection_cost_per_hh=92,
                                    base_to_peak_load_ratio=0.85,
                                    capacity_factor=0.7,
                                    tech_life=20,
                                    om_costs=0.1,
                                    capital_cost={float("inf"): 672},
                                    mini_grid=True)

        sa_diesel_calc = Technology(base_to_peak_load_ratio=0.9,
                                    capacity_factor=0.5,
                                    tech_life=20,
                                    om_costs=0.1,
                                    capital_cost={float("inf"): 814},
                                    standalone=True)

        sa_diesel_cost = {'diesel_price': 0.8,
                          'efficiency': 0.28,
                          'diesel_truck_consumption': 14,
                          'diesel_truck_volume': 300}

        mg_diesel_cost = {'diesel_price': 0.8,
                          'efficiency': 0.33,
                          'diesel_truck_consumption': 33.7,
                          'diesel_truck_volume': 15000}

        onsseter.df.loc[onsseter.df['Region'] == 'Haut-Katanga', 'ClosestGrid'] = 'Sud'
        onsseter.df.loc[onsseter.df['Region'] == 'Haut-Lomami', 'ClosestGrid'] = 'Sud'
        onsseter.df.loc[onsseter.df['Region'] == 'Lualaba', 'ClosestGrid'] = 'Sud'
        onsseter.df.loc[onsseter.df['Region'] == 'Tanganyika', 'ClosestGrid'] = 'Sud'
        onsseter.df.loc[onsseter.df['Region'] == 'Kasaï-Central', 'ClosestGrid'] = 'Sud'
        onsseter.df.loc[onsseter.df['Region'] == 'Lomami', 'ClosestGrid'] = 'Sud'

        onsseter.df.loc[onsseter.df['Region'] == 'Kongo-Central', 'ClosestGrid'] = 'Ouest'
        onsseter.df.loc[onsseter.df['Region'] == 'Kinshasa', 'ClosestGrid'] = 'Ouest'
        onsseter.df.loc[onsseter.df['Region'] == 'Kwango', 'ClosestGrid'] = 'Ouest'
        onsseter.df.loc[onsseter.df['Region'] == 'Kasaï', 'ClosestGrid'] = 'Ouest'
        onsseter.df.loc[onsseter.df['Region'] == 'Kwilu', 'ClosestGrid'] = 'Ouest'
        onsseter.df.loc[onsseter.df['Region'] == 'Maï-Ndombe', 'ClosestGrid'] = 'Ouest'
        onsseter.df.loc[onsseter.df['Region'] == 'Tshuapa', 'ClosestGrid'] = 'Ouest'
        onsseter.df.loc[onsseter.df['Region'] == 'Équateur', 'ClosestGrid'] = 'Ouest'
        onsseter.df.loc[onsseter.df['Region'] == 'Mongala', 'ClosestGrid'] = 'Ouest'
        onsseter.df.loc[onsseter.df['Region'] == 'Sud-Ubangi', 'ClosestGrid'] = 'Ouest'
        onsseter.df.loc[onsseter.df['Region'] == 'Nord-Ubangi', 'ClosestGrid'] = 'Ouest'

        onsseter.df.loc[onsseter.df['Region'] == 'Sud-Kivu', 'ClosestGrid'] = 'Est'
        onsseter.df.loc[onsseter.df['Region'] == 'Nord-Kivu', 'ClosestGrid'] = 'Est'
        onsseter.df.loc[onsseter.df['Region'] == 'Maniema', 'ClosestGrid'] = 'Est'
        onsseter.df.loc[onsseter.df['Region'] == 'Sankuru', 'ClosestGrid'] = 'Est'
        onsseter.df.loc[onsseter.df['Region'] == 'Tshopo', 'ClosestGrid'] = 'Est'
        onsseter.df.loc[onsseter.df['Region'] == 'Ituri', 'ClosestGrid'] = 'Est'
        onsseter.df.loc[onsseter.df['Region'] == 'Bas-Uélé', 'ClosestGrid'] = 'Est'
        onsseter.df.loc[onsseter.df['Region'] == 'Haut-Uélé', 'ClosestGrid'] = 'Est'

        prioritization = 2

        # RUN_PARAM: One shall define here the years of analysis (excluding start year),
        # together with access targets per interval and timestep duration
        yearsofanalysis = [intermediate_year, end_year]
        eleclimits = {intermediate_year: intermediate_electrification_target,
                      end_year: end_year_electrification_rate_target}
        time_steps = {intermediate_year: intermediate_year - start_year, end_year: end_year - intermediate_year}

        onsseter.current_mv_line_dist()

        onsseter.project_pop_and_urban(pop_future, urban_future, start_year, end_year, intermediate_year)

        for year in yearsofanalysis:
            eleclimit = eleclimits[year]
            time_step = time_steps[year]

            grid_cap_gen_limit_ouest = time_step * annual_grid_cap_gen_limit_ouest[year] * 1000
            grid_connect_limit_ouest = time_step * annual_new_grid_connections_limit_ouest[year] * 1000

            grid_cap_gen_limit_sud = time_step * annual_grid_cap_gen_limit_sud[year] * 1000
            grid_connect_limit_sud = time_step * annual_new_grid_connections_limit_sud[year] * 1000

            grid_cap_gen_limit_est = time_step * annual_grid_cap_gen_limit_est[year] * 1000
            grid_connect_limit_est = time_step * annual_new_grid_connections_limit_est[year] * 1000

            onsseter.set_scenario_variables(year, num_people_per_hh_rural, num_people_per_hh_urban, time_step,
                                            start_year, urban_tier, rural_tier, 1, productive_demand)

            onsseter.diesel_cost_columns(sa_diesel_cost, mg_diesel_cost, year)

            sa_diesel_investment, sa_pv_investment, mg_diesel_investment, mg_pv_investment, mg_wind_investment, \
                mg_hydro_investment = onsseter.calculate_off_grid_lcoes(mg_hydro_calc, mg_wind_calc, mg_pv_calc,
                                                                        sa_pv_calc, mg_diesel_calc,
                                                                        sa_diesel_calc, year, end_year, time_step)

            grid_investment = np.zeros(len(onsseter.df['X_deg']))
            onsseter.df[SET_LCOE_GRID + "{}".format(year)] = 99

            grid_investment, grid_cap_gen_limit_ouest, grid_connect_limit_ouest = \
                onsseter.pre_electrification(grid_generation_cost_ouest, year, time_step, end_year, grid_calc_ouest,
                                             grid_cap_gen_limit_ouest, grid_connect_limit_ouest, grid_investment)

            grid_investment, grid_cap_gen_limit_sud, grid_connect_limit_sud = \
                onsseter.pre_electrification(grid_generation_cost_sud, year, time_step, end_year, grid_calc_sud,
                                             grid_cap_gen_limit_sud, grid_connect_limit_sud, grid_investment)

            grid_investment, grid_cap_gen_limit_est, grid_connect_limit_est = \
                onsseter.pre_electrification(grid_generation_cost_est, year, time_step, end_year, grid_calc_est,
                                             grid_cap_gen_limit_est, grid_connect_limit_est, grid_investment)

            onsseter.df[SET_LCOE_GRID + "{}".format(year)], onsseter.df[SET_MIN_GRID_DIST + "{}".format(year)], \
            onsseter.df[SET_ELEC_ORDER + "{}".format(year)], onsseter.df[SET_MV_CONNECT_DIST], grid_investment = \
                onsseter.elec_extension(grid_calc_ouest,
                                        max_grid_extension_dist,
                                        year,
                                        start_year,
                                        end_year,
                                        time_step,
                                        grid_cap_gen_limit_ouest,
                                        grid_connect_limit_ouest,
                                        auto_intensification=auto_intensification_ouest,
                                        prioritization=prioritization,
                                        new_investment=grid_investment,
                                        grid_name='Ouest')

            grid_investment = grid_investment[0]

            onsseter.df[SET_LCOE_GRID + "{}".format(year)], onsseter.df[SET_MIN_GRID_DIST + "{}".format(year)], \
            onsseter.df[SET_ELEC_ORDER + "{}".format(year)], onsseter.df[SET_MV_CONNECT_DIST], grid_investment = \
                onsseter.elec_extension(grid_calc_sud,
                                        max_grid_extension_dist,
                                        year,
                                        start_year,
                                        end_year,
                                        time_step,
                                        grid_cap_gen_limit_sud,
                                        grid_connect_limit_sud,
                                        auto_intensification=auto_intensification_sud,
                                        prioritization=prioritization,
                                        new_investment=grid_investment,
                                        grid_name='Sud')

            grid_investment = grid_investment[0]

            onsseter.df[SET_LCOE_GRID + "{}".format(year)], onsseter.df[SET_MIN_GRID_DIST + "{}".format(year)], \
            onsseter.df[SET_ELEC_ORDER + "{}".format(year)], onsseter.df[SET_MV_CONNECT_DIST], grid_investment = \
                onsseter.elec_extension(grid_calc_est,
                                        max_grid_extension_dist,
                                        year,
                                        start_year,
                                        end_year,
                                        time_step,
                                        grid_cap_gen_limit_est,
                                        grid_connect_limit_est,
                                        auto_intensification=auto_intensification_est,
                                        prioritization=prioritization,
                                        new_investment=grid_investment,
                                        grid_name='Est')

            onsseter.results_columns(year, time_step, prioritization, auto_intensification_ouest,
                                     auto_intensification_sud, auto_intensification_est)

            onsseter.calculate_investments(sa_diesel_investment, sa_pv_investment, mg_diesel_investment,
                                           mg_pv_investment, mg_wind_investment,
                                           mg_hydro_investment, grid_investment, year)

            onsseter.apply_limitations(eleclimit, year, time_step, prioritization, auto_intensification_ouest,
                                       auto_intensification_sud, auto_intensification_est)

            onsseter.calculate_new_capacity(mg_hydro_calc, mg_wind_calc, mg_pv_calc, sa_pv_calc, mg_diesel_calc,
                                            sa_diesel_calc, grid_calc_ouest, grid_calc_sud, grid_calc_est, year)

        for i in range(len(onsseter.df.columns)):
            if onsseter.df.iloc[:, i].dtype == 'float64':
                onsseter.df.iloc[:, i] = pd.to_numeric(onsseter.df.iloc[:, i], downcast='float')
            elif onsseter.df.iloc[:, i].dtype == 'int64':
                onsseter.df.iloc[:, i] = pd.to_numeric(onsseter.df.iloc[:, i], downcast='signed')


        onsseter.df.to_csv(settlements_out_csv, index=False)

        elements = []
        for year in yearsofanalysis:
            elements.append("Population{}".format(year))
            elements.append("NewConnections{}".format(year))
            elements.append("Capacity{}".format(year))
            elements.append("Investment{}".format(year))

        techs = ["Grid", "SA_Diesel", "SA_PV", "MG_Diesel", "MG_PV", "MG_Wind", "MG_Hydro"]

        sumtechs = []
        for year in yearsofanalysis:
            sumtechs.extend(["Population{}".format(year) + t for t in techs])
            sumtechs.extend(["NewConnections{}".format(year) + t for t in techs])
            sumtechs.extend(["Capacity{}".format(year) + t for t in techs])
            sumtechs.extend(["Investment{}".format(year) + t for t in techs])

        summary = pd.Series(index=sumtechs, name='country')

        for year in yearsofanalysis:
            code = 1
            for t in techs:
                summary.loc["Population{}".format(year) + t] = onsseter.df.loc[
                    (onsseter.df[SET_MIN_OVERALL_CODE + '{}'.format(year)] == code) & (
                                onsseter.df[SET_ELEC_FINAL_CODE + '{}'.format(year)] < 99), SET_POP + '{}'.format(
                        year)].sum()
                summary.loc["NewConnections{}".format(year) + t] = onsseter.df.loc[
                    (onsseter.df[SET_MIN_OVERALL_CODE + '{}'.format(year)] == code) & (onsseter.df[
                                                                                           SET_ELEC_FINAL_CODE + '{}'.format(
                                                                                               year)] < 99), SET_NEW_CONNECTIONS + '{}'.format(
                        year)].sum()
                summary.loc["Capacity{}".format(year) + t] = onsseter.df.loc[(onsseter.df[
                                                                                  SET_MIN_OVERALL_CODE + '{}'.format(
                                                                                      year)] == code) & (onsseter.df[
                                                                                                             SET_ELEC_FINAL_CODE + '{}'.format(
                                                                                                                 year)] < 99), SET_NEW_CAPACITY + '{}'.format(
                    year)].sum() / 1000
                summary.loc["Investment{}".format(year) + t] = onsseter.df.loc[
                    (onsseter.df[SET_MIN_OVERALL_CODE + '{}'.format(year)] == code) & (onsseter.df[
                                                                                           SET_ELEC_FINAL_CODE + '{}'.format(
                                                                                               year)] < 99), SET_INVESTMENT_COST + '{}'.format(
                        year)].sum()
                code += 1

        index = techs + ['Total']
        columns = []
        for year in yearsofanalysis:
            columns.append("Population{}".format(year))
            columns.append("NewConnections{}".format(year))
            columns.append("Capacity{} (MW)".format(year))
            columns.append("Investment{} (million USD)".format(year))

        summary_table = pd.DataFrame(index=index, columns=columns)

        summary_table[columns[0]] = summary.iloc[0:7].astype(int).tolist() + [int(summary.iloc[0:7].sum())]
        summary_table[columns[1]] = summary.iloc[7:14].astype(int).tolist() + [int(summary.iloc[7:14].sum())]
        summary_table[columns[2]] = summary.iloc[14:21].astype(int).tolist() + [int(summary.iloc[14:21].sum())]
        summary_table[columns[3]] = [round(x / 1e4) / 1e2 for x in summary.iloc[21:28].astype(float).tolist()] + [
            round(summary.iloc[21:28].sum() / 1e4) / 1e2]
        summary_table[columns[4]] = summary.iloc[28:35].astype(int).tolist() + [int(summary.iloc[28:35].sum())]
        summary_table[columns[5]] = summary.iloc[35:42].astype(int).tolist() + [int(summary.iloc[35:42].sum())]
        summary_table[columns[6]] = summary.iloc[42:49].astype(int).tolist() + [int(summary.iloc[42:49].sum())]
        summary_table[columns[7]] = [round(x / 1e4) / 1e2 for x in summary.iloc[49:56].astype(float).tolist()] + [
            round(summary.iloc[49:56].sum() / 1e4) / 1e2]

        summary_table.to_csv(summary_csv, index=True)

        regions = onsseter.df['Region'].unique()

        for region in regions:

            elements = []
            for year in yearsofanalysis:
                elements.append("Population{}".format(year))
                elements.append("NewConnections{}".format(year))
                elements.append("Capacity{}".format(year))
                elements.append("Investment{}".format(year))

            techs = ["Grid", "SA_Diesel", "SA_PV", "MG_Diesel", "MG_PV", "MG_Wind", "MG_Hydro"]

            sumtechs = []
            for year in yearsofanalysis:
                sumtechs.extend(["Population{}".format(year) + t for t in techs])
                sumtechs.extend(["NewConnections{}".format(year) + t for t in techs])
                sumtechs.extend(["Capacity{}".format(year) + t for t in techs])
                sumtechs.extend(["Investment{}".format(year) + t for t in techs])

            summary = pd.Series(index=sumtechs, name='country')

            for year in yearsofanalysis:
                code = 1
                for t in techs:
                    summary.loc["Population{}".format(year) + t] = onsseter.df.loc[
                        (onsseter.df[SET_MIN_OVERALL_CODE + '{}'.format(year)] == code) & (
                                    onsseter.df[SET_ELEC_FINAL_CODE + '{}'.format(year)] < 99) & (
                                    onsseter.df['Region'] == region), SET_POP + '{}'.format(year)].sum()
                    summary.loc["NewConnections{}".format(year) + t] = onsseter.df.loc[
                        (onsseter.df[SET_MIN_OVERALL_CODE + '{}'.format(year)] == code) & (
                                    onsseter.df[SET_ELEC_FINAL_CODE + '{}'.format(year)] < 99) & (
                                    onsseter.df['Region'] == region), SET_NEW_CONNECTIONS + '{}'.format(year)].sum()
                    summary.loc["Capacity{}".format(year) + t] = onsseter.df.loc[(onsseter.df[
                                                                                      SET_MIN_OVERALL_CODE + '{}'.format(
                                                                                          year)] == code) & (
                                                                                             onsseter.df[
                                                                                                 SET_ELEC_FINAL_CODE + '{}'.format(
                                                                                                     year)] < 99) & (
                                                                                             onsseter.df[
                                                                                                 'Region'] == region), SET_NEW_CAPACITY + '{}'.format(
                        year)].sum() / 1000
                    summary.loc["Investment{}".format(year) + t] = onsseter.df.loc[
                        (onsseter.df[SET_MIN_OVERALL_CODE + '{}'.format(year)] == code) & (
                                    onsseter.df[SET_ELEC_FINAL_CODE + '{}'.format(year)] < 99) & (
                                    onsseter.df['Region'] == region), SET_INVESTMENT_COST + '{}'.format(year)].sum()
                    code += 1

            index = techs + ['Total']
            columns = []
            for year in yearsofanalysis:
                columns.append("Population{}".format(year))
                columns.append("NewConnections{}".format(year))
                columns.append("Capacity{} (MW)".format(year))
                columns.append("Investment{} (million USD)".format(year))

            summary_table = pd.DataFrame(index=index, columns=columns)

            summary_table[columns[0]] = summary.iloc[0:7].astype(int).tolist() + [int(summary.iloc[0:7].sum())]
            summary_table[columns[1]] = summary.iloc[7:14].astype(int).tolist() + [int(summary.iloc[7:14].sum())]
            summary_table[columns[2]] = summary.iloc[14:21].astype(int).tolist() + [int(summary.iloc[14:21].sum())]
            summary_table[columns[3]] = [round(x / 1e4) / 1e2 for x in summary.iloc[21:28].astype(float).tolist()] + [
                round(summary.iloc[21:28].sum() / 1e4) / 1e2]
            summary_table[columns[4]] = summary.iloc[28:35].astype(int).tolist() + [int(summary.iloc[28:35].sum())]
            summary_table[columns[5]] = summary.iloc[35:42].astype(int).tolist() + [int(summary.iloc[35:42].sum())]
            summary_table[columns[6]] = summary.iloc[42:49].astype(int).tolist() + [int(summary.iloc[42:49].sum())]
            summary_table[columns[7]] = [round(x / 1e4) / 1e2 for x in summary.iloc[49:56].astype(float).tolist()] + [
                round(summary.iloc[49:56].sum() / 1e4) / 1e2]

            summary_csv = os.path.join(summary_folder,
                                       '{}-{}-{}_{}_{}_summary.csv'.format(country_id, region, tier_index, productive_index,
                                                                          pv_index))
            summary_table.to_csv(summary_csv, index=True)

        logging.info('Finished')
