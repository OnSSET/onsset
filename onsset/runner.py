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
    urban_current = specs_data.loc[0, SPE_URBAN]
    start_year = int(specs_data.loc[0, SPE_START_YEAR])

    elec_actual = specs_data.loc[0, SPE_ELEC]
    elec_actual_urban = specs_data.loc[0, SPE_ELEC_URBAN]
    elec_actual_rural = specs_data.loc[0, SPE_ELEC_RURAL]

    pop_modelled, urban_modelled = onsseter.calibrate_current_pop_and_urban(pop_actual, urban_current)

    elec_modelled, rural_elec_ratio, urban_elec_ratio = \
        onsseter.elec_current_and_future(elec_actual, elec_actual_urban, elec_actual_rural, start_year)

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

        # Electrification rate target lever
        electification_rate_index = scenario_info.iloc[scenario]['ElecRateIndex']
        electrification_rate_2030 = scenario_parameters.iloc[electification_rate_index]['ElecRate2030']
        electrification_rate_2025 = scenario_parameters.iloc[electification_rate_index]['ElecRate2025']

        #  Household demand lever
        household_dem_index = scenario_info.iloc[scenario]['ResidentialDemand']
        rural_tier = int(scenario_parameters.iloc[household_dem_index]['RuralTargetTier'])
        urban_tier = int(scenario_parameters.iloc[household_dem_index]['UrbanTargetTier'])

        # Social and productive demand lever (Health and education)
        social_productive_dem_index = scenario_info.iloc[scenario]['SocialProductiveDem']
        social_productive_demand = scenario_parameters.iloc[social_productive_dem_index]['SocialProductiveDemand']

        # Industrial demand lever
        ind_dem_index = scenario_info.iloc[scenario]['IndustrialDem']
        industrial_demand = scenario_parameters.iloc[ind_dem_index]['IndustrialDemand']

        # PV system cost
        pv_index = scenario_info.iloc[scenario]['PVIndex']
        pv_capital_cost_adjust = float(scenario_parameters.iloc[pv_index]['PV_Cost_adjust'])

        #  Discount rate lever
        disscount_index = scenario_info.iloc[scenario]['DiscountIndex']
        disc_rate = scenario_parameters.iloc[disscount_index]['DiscRate']

        scenario_name = '{}_{}_{}_{}_{}_{}'.format(pop_index, electification_rate_index, household_dem_index,
                                                   social_productive_dem_index, ind_dem_index, pv_index)

        settlements_in_csv = calibrated_csv_path
        onsseter = SettlementProcessor(settlements_in_csv)

        onsseter.df['HealthDemand'] = 0
        onsseter.df['EducationDemand'] = 0
        onsseter.df['AgriDemand'] = 0
        onsseter.df['CommercialDemand'] = 0
        onsseter.df['HeavyIndustryDemand'] = 0

        if social_productive_demand == 1:
            onsseter.df['HealthDemand'] = onsseter.df['health_dem_low']
            onsseter.df['EducationDemand'] = onsseter.df['edu_dem_low']
            onsseter.df['AgriDemand'] = onsseter.df['agri_dem_low']
            onsseter.df['CommercialDemand'] = onsseter.df['prod_dem_low']
        elif social_productive_demand == 2:
            onsseter.df['HealthDemand'] = onsseter.df['health_dem_mid']
            onsseter.df['EducationDemand'] = onsseter.df['edu_dem_mid']
            onsseter.df['AgriDemand'] = onsseter.df['agri_dem_mid']
            onsseter.df['CommercialDemand'] = onsseter.df['prod_dem_mid']
        elif social_productive_demand == 3:
            onsseter.df['HealthDemand'] = onsseter.df['health_dem_high']
            onsseter.df['EducationDemand'] = onsseter.df['edu_dem_high']
            onsseter.df['AgriDemand'] = onsseter.df['agri_dem_high']
            onsseter.df['CommercialDemand'] = onsseter.df['prod_dem_high']

        if industrial_demand == 1:
            onsseter.df['HeavyIndustryDemand'] = onsseter.df['ind_dem_low']
        elif industrial_demand == 2:
                onsseter.df['HeavyIndustryDemand'] = onsseter.df['ind_dem_mid']
        elif industrial_demand == 3:
                onsseter.df['HeavyIndustryDemand'] = onsseter.df['ind_dem_high']

        if rural_tier == 6:
            onsseter.df['ResidentialDemandTierCustom'] = onsseter.df['hh_dem_low']
        elif rural_tier == 7:
            onsseter.df['ResidentialDemandTierCustom'] = onsseter.df['hh_dem_mid']
        elif rural_tier == 8:
            onsseter.df['ResidentialDemandTierCustom'] = onsseter.df['hh_dem_high']

        onsseter.df.drop(['hh_dem_low', 'hh_dem_mid', 'hh_dem_high', 'health_dem_low', 'health_dem_mid',
                          'health_dem_high', 'edu_dem_low', 'edu_dem_mid', 'edu_dem_high', 'agri_dem_low',
                          'agri_dem_mid', 'agri_dem_high', 'prod_dem_low', 'prod_dem_mid', 'prod_dem_high',
                          'ind_dem_low', 'ind_dem_mid', 'ind_dem_high'], axis=1, inplace=True)

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
        onsseter.df.loc[onsseter.df['Region'] == 'Tanganyka', 'ClosestGrid'] = 'Sud'
        onsseter.df.loc[onsseter.df['Region'] == 'Kasai-Central', 'ClosestGrid'] = 'Sud'
        onsseter.df.loc[onsseter.df['Region'] == 'Lomami', 'ClosestGrid'] = 'Sud'
        onsseter.df.loc[onsseter.df['Region'] == 'Kasai-Oriental', 'ClosestGrid'] = 'Sud'

        onsseter.df.loc[onsseter.df['Region'] == 'Kongo Central', 'ClosestGrid'] = 'Ouest'
        onsseter.df.loc[onsseter.df['Region'] == 'Kinshasa', 'ClosestGrid'] = 'Ouest'
        onsseter.df.loc[onsseter.df['Region'] == 'Kwango', 'ClosestGrid'] = 'Ouest'
        onsseter.df.loc[onsseter.df['Region'] == 'Kasai', 'ClosestGrid'] = 'Ouest'
        onsseter.df.loc[onsseter.df['Region'] == 'Kwilu', 'ClosestGrid'] = 'Ouest'
        onsseter.df.loc[onsseter.df['Region'] == 'Mai-Ndombe', 'ClosestGrid'] = 'Ouest'
        onsseter.df.loc[onsseter.df['Region'] == 'Tshuapa', 'ClosestGrid'] = 'Ouest'
        onsseter.df.loc[onsseter.df['Region'] == 'Equateur', 'ClosestGrid'] = 'Ouest'
        onsseter.df.loc[onsseter.df['Region'] == 'Mongala', 'ClosestGrid'] = 'Ouest'
        onsseter.df.loc[onsseter.df['Region'] == 'Sud-Ubangi', 'ClosestGrid'] = 'Ouest'
        onsseter.df.loc[onsseter.df['Region'] == 'Nord-Ubangi', 'ClosestGrid'] = 'Ouest'

        onsseter.df.loc[onsseter.df['Region'] == 'Sud-Kivu', 'ClosestGrid'] = 'Est'
        onsseter.df.loc[onsseter.df['Region'] == 'Nord-Kivu', 'ClosestGrid'] = 'Est'
        onsseter.df.loc[onsseter.df['Region'] == 'Maniema', 'ClosestGrid'] = 'Est'
        onsseter.df.loc[onsseter.df['Region'] == 'Sankuru', 'ClosestGrid'] = 'Est'
        onsseter.df.loc[onsseter.df['Region'] == 'Tshopo', 'ClosestGrid'] = 'Est'
        onsseter.df.loc[onsseter.df['Region'] == 'Ituri', 'ClosestGrid'] = 'Est'
        onsseter.df.loc[onsseter.df['Region'] == 'Bas-Uele', 'ClosestGrid'] = 'Est'
        onsseter.df.loc[onsseter.df['Region'] == 'Haut-Uele', 'ClosestGrid'] = 'Est'

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
                                            start_year, urban_tier, rural_tier, 1)

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

            onsseter.update_results_columns(year)

        for i in range(len(onsseter.df.columns)):
            if onsseter.df.iloc[:, i].dtype == 'float64':
                onsseter.df.iloc[:, i] = pd.to_numeric(onsseter.df.iloc[:, i], downcast='float')
            elif onsseter.df.iloc[:, i].dtype == 'int64':
                onsseter.df.iloc[:, i] = pd.to_numeric(onsseter.df.iloc[:, i], downcast='signed')

        ### In the two variable below you can choose which summaries to include

        short_results = True  # If True, only selected columns included in the results. If False, all columns included in results
        regional_summaries = True  # If True, regional summaries are computed and saved. If False, only national summaries included

        ###

        if regional_summaries:
            settlements_out_dir = os.path.join(results_folder, scenario_name)
            summaries_out_dir = os.path.join(summary_folder, scenario_name)

            if not os.path.exists(settlements_out_dir):
                os.makedirs(settlements_out_dir)

            if not os.path.exists(summaries_out_dir):
                os.makedirs(summaries_out_dir)
        else:
            settlements_out_dir = results_folder
            summaries_out_dir = summary_folder

        settlements_out_csv = os.path.join(settlements_out_dir, '{}-{}.csv'.format(country_id, scenario_name))
        summary_csv = os.path.join(summaries_out_dir, '{}-{}_summary.csv'.format(country_id, scenario_name))

        if short_results:
            df_short = onsseter.df[['id', 'X_deg', 'Y_deg', 'Region', 'PopStartYear', 'ElecPopCalib', 'Pop2025',
                                    'FinalElecCode2025', 'NewConnections2025', 'NewCapacity2025', 'InvestmentCost2025',
                                    'NewDemand2025', 'TotalDemand2025', 'Pop2030', 'FinalElecCode2030',
                                    'NewConnections2030', 'NewCapacity2030', 'InvestmentCost2030', 'NewDemand2030',
                                    'TotalDemand2030']]
            df_short.to_csv(settlements_out_csv, index=False)
        else:
            onsseter.df.to_csv(settlements_out_csv, index=False)

        summary_table = onsseter.calc_drc_summaries(yearsofanalysis)

        summary_table.to_csv(summary_csv, index=True)

        if regional_summaries:
            regions = onsseter.df['Region'].unique()
            for region in regions:

                summary_table = onsseter.calc_drc_summaries(yearsofanalysis, region)

                # This line must also be updated if you change the levers and want regional summaries
                summary_csv = os.path.join(summaries_out_dir, '{}-{}_summary.csv'.format(region, scenario_name))

                # Enable or disable the line below to include/exclude regional summaries
                summary_table.to_csv(summary_csv, index=True)

        logging.info('Finished')
