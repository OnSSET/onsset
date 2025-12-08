# Defines the modules

import logging
import os
import time
import geopandas as gpd
import numpy as np
import re
import geojson
import pandas as pd
from onsset import (SET_ELEC_ORDER, SET_LCOE_GRID, SET_MIN_GRID_DIST, SET_GRID_PENALTY,
                    SET_MV_CONNECT_DIST, SET_WINDVEL, SET_WINDCF, SET_X_DEG, SET_Y_DEG,
                    SettlementProcessor, Technology)

try:
    from onsset.specs import (SPE_COUNTRY, SPE_ELEC, SPE_ELEC_MODELLED,
                              SPE_ELEC_RURAL, SPE_ELEC_URBAN, SPE_END_YEAR,
                              SPE_GRID_CAPACITY_INVESTMENT, SPE_GRID_LOSSES,
                              SPE_MAX_GRID_EXTENSION_DIST,
                              SPE_NUM_PEOPLE_PER_HH_RURAL,
                              SPE_NUM_PEOPLE_PER_HH_URBAN, SPE_POP, SPE_POP_FUTURE,
                              SPE_START_YEAR, SPE_URBAN, SPE_URBAN_FUTURE,
                              SPE_URBAN_MODELLED, SPE_COST_NON_SUPLIED_ENERGY)
except ImportError:
    from specs import (SPE_COUNTRY, SPE_ELEC, SPE_ELEC_MODELLED,
                       SPE_ELEC_RURAL, SPE_ELEC_URBAN, SPE_END_YEAR,
                       SPE_GRID_CAPACITY_INVESTMENT, SPE_GRID_LOSSES,
                       SPE_MAX_GRID_EXTENSION_DIST,
                       SPE_NUM_PEOPLE_PER_HH_RURAL,
                       SPE_NUM_PEOPLE_PER_HH_URBAN, SPE_POP, SPE_POP_FUTURE,
                       SPE_START_YEAR, SPE_URBAN, SPE_URBAN_FUTURE,
                       SPE_URBAN_MODELLED, SPE_COST_NON_SUPLIED_ENERGY)
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

    sheets_dict = pd.read_excel(specs_path, sheet_name=None)
    specs_data = pd.read_excel(specs_path, sheet_name='SpecsData')
    settlements_in_csv = csv_path
    settlements_out_csv = calibrated_csv_path

    onsseter = SettlementProcessor(settlements_in_csv)

    onsseter.condition_df()
    onsseter.df[SET_GRID_PENALTY] = 1  # onsseter.grid_penalties(onsseter.df)

    onsseter.df[SET_WINDCF] = onsseter.calc_wind_cfs(onsseter.df[SET_WINDVEL])

    pop_actual = specs_data.loc[0, SPE_POP]
    urban_current = specs_data.loc[0, SPE_URBAN]
    start_year = int(specs_data.loc[0, SPE_START_YEAR])
    elec_actual = specs_data.loc[0, SPE_ELEC]
    elec_actual_urban = specs_data.loc[0, SPE_ELEC_URBAN]
    elec_actual_rural = specs_data.loc[0, SPE_ELEC_RURAL]

    pop_modelled, urban_modelled = onsseter.calibrate_current_pop_and_urban(pop_actual, urban_current)

    specs_data.loc[0, SPE_URBAN_MODELLED] = urban_modelled

    elec_calibration_results = onsseter.calibrate_grid_elec_current(elec_actual, elec_actual_urban, elec_actual_rural,
                                                                    start_year, buffer=False)

    mg_pop_calib = onsseter.mg_elec_current(start_year)

    specs_data.loc[0, SPE_ELEC_MODELLED] = elec_calibration_results[0]
    specs_data.loc[0, 'rural_elec_ratio_modelled'] = elec_calibration_results[1]
    specs_data.loc[0, 'urban_elec_ratio_modelled'] = elec_calibration_results[2]
    specs_data['grid_distance_used'] = elec_calibration_results[3]
    specs_data['ntl_limit'] = elec_calibration_results[4]
    specs_data['pop_limit'] = elec_calibration_results[5]
    specs_data['Buffer_used'] = elec_calibration_results[6]
    specs_data['buffer_distance'] = elec_calibration_results[7]
    specs_data['mg_pop_electrified'] = mg_pop_calib

    if SPE_COST_NON_SUPLIED_ENERGY in specs_data.columns:
        specs_data[SPE_COST_NON_SUPLIED_ENERGY]= specs_data.loc[0, SPE_COST_NON_SUPLIED_ENERGY] if not pd.isna(specs_data.loc[0, SPE_COST_NON_SUPLIED_ENERGY]) else 0
    else:
        specs_data[SPE_COST_NON_SUPLIED_ENERGY] = 0

    book = load_workbook(specs_path)
    with pd.ExcelWriter(specs_path_calib, engine='openpyxl') as writer:
        #writer = pd.ExcelWriter(specs_path_calib, engine='openpyxl')
        #writer.workbook = book
        for sheet_name, df in sheets_dict.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)

            # RUN_PARAM: Here the calibrated "specs" data are copied to a new tab called "SpecsDataCalib".
            # This is what will later on be used to feed the model
        specs_data.to_excel(writer, sheet_name='SpecsDataCalib', index=False)
    #writer.save()
    #writer.close()

    logging.info('Calibration finished. Results are transferred to the csv file')
    onsseter.df.to_csv(settlements_out_csv, index=False)


def scenario(specs_path, calibrated_csv_path, results_folder, summary_folder, pv_path, wind_path, mv_path):
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
    specs_data = pd.read_excel(specs_path, sheet_name='SpecsDataCalib', index_col=0)
    print(specs_data.iloc[0][SPE_COUNTRY])

    for scenario in scenarios:
        print('Scenario: ' + str(scenario + 1))

        onsseter = SettlementProcessor(calibrated_csv_path)

        x_mv_exist, y_mv_exist = onsseter.start_extension_points(mv_path)
        x_coordinates = x_mv_exist
        y_coordinates = y_mv_exist

        col_name = max(
            [c for c in onsseter.df.columns if c.startswith("FinalElecCode")],
            key=lambda x: int(re.search(r"\d{4}$", x).group())
        )

        yearsofanalysis = specs_data.index.tolist()
        base_year = specs_data.iloc[0][SPE_START_YEAR]
        end_year = yearsofanalysis[-1]

        onsseter.add_xy_3395()

        country_id = specs_data.iloc[0]['CountryCode']

        pop_future = specs_data.iloc[0][SPE_POP_FUTURE]
        urban_future = specs_data.iloc[0][SPE_URBAN_FUTURE]

        tier_index = scenario_info.iloc[scenario]['Target_electricity_consumption_level']
        grid_index = scenario_info.iloc[scenario]['Grid_electricity_generation_cost']
        productive_index = scenario_info.iloc[scenario]['Productive_uses_demand']
        prio_index = scenario_info.iloc[scenario]['Prioritization_algorithm']

        rural_tier_small = scenario_parameters.iloc[tier_index]['RuralTargetTierSmall']
        rural_tier_large = scenario_parameters.iloc[tier_index]['RuralTargetTierLarge']
        rural_cutoff = scenario_parameters.iloc[tier_index]['RuralCutoffSize']
        urban_tier = scenario_parameters.iloc[tier_index]['UrbanTargetTier']
        grid_price = scenario_parameters.iloc[grid_index]['GridGenerationCost']
        prioritization = scenario_parameters.iloc[prio_index]['PrioritizationAlgorithm']
        auto_intensification = scenario_parameters.iloc[prio_index]['AutoIntensificationKM']
        max_auto_intensification_cost = scenario_parameters.iloc[prio_index]['MaxIntensificationCost']  # Max household connection cost for forced grid intensification
        grid_capacity_investment = specs_data['GridCapacityInvestmentCost']
        annual_grid_cap_gen_limit = scenario_parameters.iloc[grid_index]['NewGridGenerationCapacityAnnualLimitMW'] * 1000
        annual_new_grid_connections_limit = scenario_parameters.iloc[grid_index]['GridConnectionsLimitThousands'] * 1000

        carbon_cost = 0
        grid_emission_factor = 0

        settlements_out_csv = os.path.join(results_folder,
                                           '{}-1-{}_{}_{}.csv'.format(country_id, tier_index, grid_index, prio_index))
        summary_csv = os.path.join(summary_folder,
                                   '{}-1-{}_{}_{}_summary.csv'.format(country_id, tier_index, grid_index, prio_index))

        elements = ["1.Population", "2.New_Connections", "3.Capacity", "4.Investment", "5.AnnualEmissions"]

        techs = ["Grid", "SA_PV", "MG_PVHybrid", "MG_Wind", "MG_Hydro"]
        tech_codes = [1, 3, 5, 6, 7]

        sumtechs = []
        for element in elements:
            for tech in techs:
                sumtechs.append(element + "_" + tech)
        total_rows = len(sumtechs)
        df_summary = pd.DataFrame(columns=yearsofanalysis)
        for row in range(0, total_rows):
            df_summary.loc[sumtechs[row]] = "Nan"

        onsseter.current_mv_line_dist()

        onsseter.project_pop_and_urban(pop_future, urban_future, base_year, yearsofanalysis)

        # RUN_PARAM: these are the annual household electricity targets
        tier_1 = 38.7  # 38.7 refers to kWh/household/year. It is the mean value between Tier 1 and Tier 2
        tier_2 = 219
        tier_3 = 803
        tier_4 = 2117
        tier_5 = 3000

        tiers = {1: tier_1, 2: tier_2, 3: tier_3, 4: tier_4, 5: tier_5}

        onsseter.prepare_wtf_tier_columns(tier_1, tier_2, tier_3, tier_4, tier_5)

        # Carbon cost represents the cost in USD/tonCO2eq, which is converted and added to the diesel price
        diesel_price = float(scenario_parameters.iloc[0]['DieselPrice'] + (carbon_cost / 1000000) * 256.9131097 * 9.9445485)

        grid_discount_rate = 0.08
        mg_discount_rate = 0.08
        sa_discount_rate = 0.08

        mg_interconnection = True  # True if mini-grids are allowed to be integrated into the grid, else False
        hybrid_lookup_table = True
        min_mg_size = 100  # minimum number of households in settlement for mini-grids to be considered as an option

        grid_reliability_option = 'None'  # Options: 'None', 'CNSE', 'DieselBackup'
        # 'None' = No cost of unreliable grid considered
        # 'CNSE' = Cost of Non-Served Energy for grid unreliability included in grid LCOE
        # 'DieselBackup' = Diesel backup generators considered for grid reliability, included in LCOE, Investment
        cnse = 0.0 # Cost of Non-Served Energy in USD/kWh for grid unreliability, only used if grid_reliability_option = 'CNSE'

        new_lines_geojson = {}

        time_steps = {}
        for i in range(len(yearsofanalysis)):
            if i == 0:
                time_steps[yearsofanalysis[i]] = yearsofanalysis[i] - base_year
            else:
                time_steps[yearsofanalysis[i]] = yearsofanalysis[i] - yearsofanalysis[i - 1]

        for year in yearsofanalysis:

            time_step = time_steps[year]
            start_year = year - time_step

            # RUN_PARAM: Fill in general and technology specific parameters (e.g. discount rate, losses etc.)
            Technology.set_default_values(base_year=start_year,
                                          start_year=start_year,
                                          end_year=end_year,
                                          hv_line_type=69, # kV
                                          hv_line_cost=53000, # USD/km
                                          hv_mv_sub_station_cost=25000, # USD/unit
                                          hv_mv_substation_type=10000, # kVA
                                          )

            grid_calc = Technology(om_of_td_lines=0.02,
                                   distribution_losses=float(specs_data.iloc[0][SPE_GRID_LOSSES]),
                                   connection_cost_per_hh=125,
                                   base_to_peak_load_ratio=0.8,
                                   capacity_factor=1,
                                   tech_life=30,
                                   grid_capacity_investment=grid_capacity_investment,
                                   grid_penalty_ratio=1,
                                   grid_price=grid_price,
                                   discount_rate=grid_discount_rate,
                                   mv_line_type=33,
                                   mv_line_amperage_limit=275,
                                   mv_line_cost=25000,
                                   lv_line_type=0.24,
                                   lv_line_cost=15000,
                                   lv_line_max_length=1,
                                   service_transf_type=75,
                                   service_transf_cost=9000,
                                   max_nodes_per_serv_trans=95,
                                   cnse=cnse)

            mg_hydro_calc = Technology(om_of_td_lines=0.02,
                                       distribution_losses=0.05,
                                       connection_cost_per_hh=100,
                                       base_to_peak_load_ratio=0.85,
                                       capacity_factor=0.5,
                                       tech_life=30,
                                       capital_cost={float("inf"): 3000},
                                       om_costs=0.03,
                                       discount_rate=mg_discount_rate,
                                       mv_line_type=33,
                                       mv_line_amperage_limit=275,
                                       mv_line_cost=25000,
                                       lv_line_type=0.24,
                                       lv_line_cost=15000,
                                       lv_line_max_length=1,
                                       service_transf_type=75,
                                       service_transf_cost=9000,
                                       max_nodes_per_serv_trans=95,
                                       mini_grid=True,
                                       )

            sa_pv_calc = Technology(base_to_peak_load_ratio=0.9,
                                    tech_life=5,
                                    om_costs=0.02,
                                    capital_cost={float("inf"): 6950,
                                                  1: 4470,
                                                  0.100: 6380,
                                                  0.050: 8780,
                                                  0.020: 9620,
                                                  },
                                    standalone=True,
                                    discount_rate=sa_discount_rate)

            mg_pv_hybrid_calc = Technology(om_of_td_lines=0.02,
                                           distribution_losses=0.05,
                                           connection_cost_per_hh=100,
                                           capacity_factor=0.5,
                                           tech_life=20,
                                           discount_rate=mg_discount_rate,
                                           mv_line_type=33,
                                           mv_line_amperage_limit=275,
                                           mv_line_cost=25000,
                                           lv_line_type=0.24,
                                           lv_line_cost=15000,
                                           lv_line_max_length=1,
                                           service_transf_type=75,
                                           service_transf_cost=9000,
                                           max_nodes_per_serv_trans=95,
                                           mini_grid=True,
                                           hybrid=True)

            mg_wind_hybrid_calc = Technology(om_of_td_lines=0.02,
                                             distribution_losses=0.05,
                                             connection_cost_per_hh=100,
                                             capacity_factor=0.5,
                                             tech_life=20,
                                             discount_rate=mg_discount_rate,
                                             mv_line_type=33,
                                             mv_line_amperage_limit=275,
                                             mv_line_cost=25000,
                                             lv_line_type=0.24,
                                             lv_line_cost=15000,
                                             lv_line_max_length=1,
                                             service_transf_type=75,
                                             service_transf_cost=9000,
                                             max_nodes_per_serv_trans=95,
                                             mini_grid=True,
                                             hybrid=True,
                                             )

            mg_pv_hybrid_params = {
                'min_mg_connections': min_mg_size,  # minimum number of households in settlement for mini-grids to be considered as an option
                'diesel_cost': 500,  # diesel generator capital cost, USD/kW rated power
                'discount_rate': mg_discount_rate,
                'n_chg': 0.92,  # charge efficiency of battery
                'n_dis': 0.92,  # discharge efficiency of battery
                'battery_cost': 300,  # battery capital cost, USD/kWh of storage capacity
                'pv_cost': 1400,  # PV panel capital cost, USD/kW peak power
                'charge_controller': 0,  # PV charge controller cost, USD/kW peak power, set to 0 if already included in pv_cost
                'pv_inverter': 0,  # PV inverter cost, USD/kW peak power, set to 0 if already included in pv_cost
                'pv_life': 25,  # PV panel expected lifetime, years
                'diesel_life': 10,  # diesel generator expected lifetime, years
                'pv_om': 0.015,  # annual OM cost of PV panels
                'diesel_om': 0.1,  # annual OM cost of diesel generator
                'battery_inverter_cost': 150,
                'battery_inverter_life': 10,
                'dod_max': 0.8,  # maximum depth of discharge of battery
                'inv_eff': 0.93,  # inverter_efficiency
                'lpsp_max': 0.02,  # maximum loss of load allowed over the year, in share of kWh
                'diesel_limit': 0.5,  # Max annual share of mini-grid generation from diesel gen-set
                'full_life_cycles': 4000  # Equivalent full life-cycles of battery until replacement
            }

            mg_wind_hybrid_params = {
                'min_mg_connections': min_mg_size,  # minimum number of households in settlement for mini-grids to be considered as an option
                'diesel_cost': 500,  # diesel generator capital cost, USD/kW rated power
                'discount_rate': mg_discount_rate,
                'n_chg': 0.92,  # charge efficiency of battery
                'n_dis': 0.92,  # discharge efficiency of battery
                'battery_cost': 300,  # battery capital cost, USD/kWh of storage capacity
                'wind_cost': 1400,  # Wind turbine capital cost, USD/kW peak power
                'charge_controller': 0,  # PV charge controller cost, USD/kW peak power, set to 0 if already included in pv_cost
                'wind_life': 25,  # Wind turbine expected lifetime, years
                'diesel_life': 10,  # diesel generator expected lifetime, years
                'wind_om': 0.015,  # annual OM cost of wind turbine
                'diesel_om': 0.1,  # annual OM cost of diesel generator
                'battery_inverter_cost': 150,
                'battery_inverter_life': 10,
                'dod_max': 0.8,  # maximum depth of discharge of battery
                'inv_eff': 0.93,  # inverter_efficiency
                'lpsp_max': 0.02,  # maximum loss of load allowed over the year, in share of kWh
                'diesel_limit': 0.7,  # Max annual share of mini-grid generation from diesel gen-set
                'full_life_cycles': 4000  # Equivalent full life-cycles of battery until replacement
            }

            # Used to model LCOE for non-served-energy
            sa_diesel_calc = Technology(base_to_peak_load_ratio=0.85,  # Deducted from curves
                                        capacity_factor=0.5,
                                        tech_life=10,
                                        om_costs=0.1,
                                        capital_cost={float("inf"): 928},
                                        efficiency=0.28,
                                        discount_rate=grid_discount_rate,
                                        standalone=True)

            sa_diesel_cost = {'diesel_price': diesel_price,
                              'efficiency': 0.28,
                              'diesel_truck_consumption': 14,
                              'diesel_truck_volume': 300}

            mg_diesel_cost = {'diesel_price': diesel_price,
                              'efficiency': 0.33,
                              'diesel_truck_consumption': 33.7,
                              'diesel_truck_volume': 15000}

            eleclimit = specs_data.loc[year]['ElecTarget']
            grid_cap_gen_limit = annual_grid_cap_gen_limit * time_step
            new_grid_connect_limit = annual_new_grid_connections_limit * time_step

            num_people_per_hh_rural = float(specs_data.loc[year][SPE_NUM_PEOPLE_PER_HH_RURAL])
            num_people_per_hh_urban = float(specs_data.loc[year][SPE_NUM_PEOPLE_PER_HH_URBAN])
            max_grid_extension_dist = float(specs_data.loc[year][SPE_MAX_GRID_EXTENSION_DIST])

            onsseter.calculate_demand(year, num_people_per_hh_rural, num_people_per_hh_urban, time_step,
                                      urban_tier, rural_tier_large, rural_tier_small, rural_cutoff, tiers)

            onsseter.calculate_unmet_demand(year, reliability=0.963)

            onsseter.diesel_cost_columns(sa_diesel_cost, mg_diesel_cost, year)

            if hybrid_lookup_table:
                hybrid_lcoe, hybrid_capacity, hybrid_investment, check = \
                    onsseter.pv_hybrids_lcoe_lookuptable(year, time_step, end_year,
                                                         mg_pv_hybrid_params, pv_path=pv_path)
                mg_pv_hybrid_calc.hybrid_fuel = hybrid_lcoe
                mg_pv_hybrid_calc.hybrid_investment = hybrid_investment
                mg_pv_hybrid_calc.hybrid_capacity = hybrid_capacity

                wind_hybrid_lcoe, wind_hybrid_capacity, wind_hybrid_investment, wind_check = \
                    onsseter.wind_hybrids_lcoe_lookuptable(year, time_step, end_year, mg_wind_hybrid_params,
                                                           wind_path=wind_path)
                wind_hybrid_investment.fillna(0, inplace=True)
                wind_hybrid_capacity.fillna(0, inplace=True)

                mg_wind_hybrid_calc.hybrid_fuel = wind_hybrid_lcoe
                mg_wind_hybrid_calc.hybrid_investment = wind_hybrid_capacity
                mg_wind_hybrid_calc.hybrid_capacity = wind_hybrid_investment
            else:
                hybrid_lcoe, hybrid_capacity, hybrid_investment = \
                    onsseter.pv_hybrids_lcoe(year, time_step, end_year,
                                             mg_pv_hybrid_params, pv_folder_path=pv_path)



            sa_pv_investment, sa_pv_capacity, mg_pv_hybrid_investment, mg_pv_hybrid_capacity, \
            mg_wind_investment, mg_wind_capacity, mg_hydro_investment, mg_hydro_capacity = onsseter.calculate_off_grid_lcoes(mg_hydro_calc, mg_wind_hybrid_calc,
                                                                                       sa_pv_calc,
                                                                                       mg_pv_hybrid_calc,
                                                                                       year, end_year, time_step,
                                                                                       techs, tech_codes, min_mg_size, 0)

            grid_investment, grid_capacity, grid_cap_gen_limit, grid_connect_limit = \
                onsseter.pre_electrification(grid_price, year, time_step, end_year, grid_calc, sa_diesel_calc,
                                             grid_reliability_option, grid_cap_gen_limit,
                                             new_grid_connect_limit)

            onsseter.max_extension_dist(year, time_step, end_year, start_year, grid_calc, sa_diesel_calc,
                                        grid_reliability_option, max_auto_intensification_cost, auto_intensification)

            onsseter.pre_selection(eleclimit, year, time_step, 2, auto_intensification)

            onsseter.df[SET_LCOE_GRID + "{}".format(year)], onsseter.df[SET_MIN_GRID_DIST + "{}".format(year)], \
                grid_investment, grid_capacity, x_coordinates, y_coordinates, new_lines_geojson[year] = \
                onsseter.elec_extension_numba(grid_calc,
                                              sa_diesel_calc,
                                              grid_reliability_option,
                                              max_grid_extension_dist,
                                              year,
                                              start_year,
                                              end_year,
                                              time_step,
                                              grid_cap_gen_limit,
                                              grid_connect_limit,
                                              x_coordinates,
                                              y_coordinates,
                                              mg_interconnection=False,
                                              )

            onsseter.results_columns(techs, tech_codes, year, time_step, prioritization, auto_intensification,
                                     mg_interconnection)

            onsseter.calculate_investments_and_capacity(sa_pv_investment, sa_pv_capacity,
                                                mg_pv_hybrid_investment, mg_pv_hybrid_capacity, mg_wind_investment,
                                                mg_wind_capacity, mg_hydro_investment, mg_hydro_capacity,
                                                grid_investment, grid_capacity, year)

            if year == yearsofanalysis[-1]:
                final_step = True
            else:
                final_step = False

            onsseter.check_grid_limitations(new_grid_connect_limit, annual_grid_cap_gen_limit, year, time_step, final_step)

            onsseter.apply_limitations(eleclimit, year, time_step, 2, auto_intensification)

            onsseter.calculate_emission(grid_factor=grid_emission_factor, year=year,
                                        time_step=time_step, start_year=start_year)

            onsseter.calc_summaries(df_summary, sumtechs, tech_codes, year, base_year)

            # Save to a GeoJSON file
            with open(os.path.join(results_folder, 'new_mv_lines_{}_{}.geojson'.format(scenario, year)), 'w') as f: # ToDo
                geojson.dump(new_lines_geojson[year], f)
            gdf = gpd.read_file(os.path.join(results_folder, 'new_mv_lines_{}_{}.geojson'.format(scenario, year)))
            gdf = gdf.set_crs(3395, allow_override=True)
            gdf = gdf.to_crs(4326)
            gdf.to_file(os.path.join(results_folder, 'new_mv_lines_{}_{}.geojson'.format(scenario, year)))

        for i in range(len(onsseter.df.columns)):
            if onsseter.df.iloc[:, i].dtype == 'float64':
                onsseter.df.iloc[:, i] = pd.to_numeric(onsseter.df.iloc[:, i], downcast='float')
            elif onsseter.df.iloc[:, i].dtype == 'int64':
                onsseter.df.iloc[:, i] = pd.to_numeric(onsseter.df.iloc[:, i], downcast='signed')

        df_summary.to_csv(summary_csv, index=sumtechs)
        onsseter.df.to_csv(settlements_out_csv, index=False)

        logging.info('Finished')
