from math import ceil, sqrt
import numpy as np
import pandas as pd
from pyonsset.constants import *


def calc_tech_lcoe(people,
                   num_people_per_hh,
                   target_energy_access_level,
                   discount_rate,
                   total_lv_lines_length,
                   mv_line_cost,
                   lv_line_cost,
                   om_of_td_lines,
                   capacity_factor,
                   distribution_losses,
                   connection_cost_per_hh,
                   capital_cost, om_costs,
                   base_to_peak_load_ratio,
                   system_life,
                   mv_line_length,
                   diesel=False,
                   efficiency=1.0,
                   fuel_cost=0.0):

    consumption = people / num_people_per_hh * target_energy_access_level
    average_load = consumption * (1 + distribution_losses) / 8760
    peak_load = average_load / base_to_peak_load_ratio
    lv_line_length = total_lv_lines_length * 0.75
    mv_total_line_cost = mv_line_cost * mv_line_length
    lv_total_line_cost = lv_line_cost * lv_line_length
    td_investment_cost = mv_total_line_cost + lv_total_line_cost + (people / num_people_per_hh) * connection_cost_per_hh
    td_om_cost = td_investment_cost * om_of_td_lines
    installed_capacity = peak_load / capacity_factor
    capital_investment = installed_capacity * capital_cost
    total_investment_cost = td_investment_cost + capital_investment
    generation_per_year = average_load * 8760 / 1000

    if diesel: ft = fuel_cost / efficiency
    else: ft = 0

    return time_value_lcoe(discount_rate,
                           system_life,
                           generation_per_year,
                           total_investment_cost,
                           td_om_cost + (capital_cost * om_costs * installed_capacity),
                           ft)


def time_value_lcoe(dr, life, gen, it, mt, ft):
    year = np.arange(0, life+1)
    el_gen = gen * np.ones(life+1)
    el_gen[0] = 0
    discount_factor = (1 + dr) ** year
    It = np.zeros(life+1)
    It[0] = it
    Mt = mt * np.ones(life+1)
    Mt[0] = 0
    Ft = el_gen * ft
    Ft[0] = 0
    Upper = (It + Mt + Ft) / discount_factor
    Lower = el_gen / discount_factor
    return np.sum(Upper) / np.sum(Lower) / 1000


def make_tables(scenario):
    output_dir = os.path.join(FF_LCOES, str(scenario))
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Import country specific values from Excel
    grid_lcoes_csv = FF_GRID_LCOES(scenario)
    grid_cap_csv = FF_GRID_CAP(scenario)
    tech_lcoes_csv = FF_TECH_LCOES(scenario)
    tech_cap_csv = FF_TECH_CAP(scenario)
    num_people_csv = FF_NUM_PEOPLE(scenario)

    country_specs = pd.read_excel(FF_SPECS)[[SPE_COUNTRY, SPE_GRID_PRICE, SPE_GRID_LOSSES, SPE_BASE_TO_PEAK, SPE_DIESEL_PRICE_LOW]]

    people_arr = [10*x for x in range(1,401)]
    techs = [MG_HYDRO, MG_PV_LOW, MG_PV_HIGH, MG_WIND_LOW, MG_WIND_MID, MG_WIND_HIGH, MG_DIESEL, SA_DIESEL_, SA_PV_LOW, SA_PV_HIGH]

    grid_lcoes = pd.Panel(np.zeros([len(country_specs), len(ELEC_DISTANCES), len(people_arr)]),
                          items=country_specs[SPE_COUNTRY].values, major_axis=ELEC_DISTANCES,
                          minor_axis=people_arr)

    grid_cap = pd.Panel(np.zeros([len(country_specs), len(ELEC_DISTANCES), len(people_arr)]),
                          items=country_specs[SPE_COUNTRY].values, major_axis=ELEC_DISTANCES,
                          minor_axis=people_arr)

    tech_lcoes = pd.Panel(np.zeros([len(country_specs), len(techs), len(people_arr)]),
                      items=country_specs[SPE_COUNTRY].values, major_axis=techs,
                      minor_axis=people_arr)

    tech_cap = pd.Panel(np.zeros([len(country_specs), len(techs), len(people_arr)]),
                          items=country_specs[SPE_COUNTRY].values, major_axis=techs,
                          minor_axis=people_arr)

    target_energy_access_level = scenario
    grid_cell_area = 100.0 # legacy

    calc_lcoe = True # alternative being calculate caponly

    while True:
        for index, country in country_specs.iterrows():
            country_name = country[SPE_COUNTRY]

            for people in people_arr:
                people *= 100 # to adjust for incorrect grid size

                # Grid
                hv_line_cost = 53000.0
                mv_increase_rate = 0.1
                mv_line_cost = 9000.0
                mv_line_capacity = 50.0
                mv_line_max_length = 50.0
                lv_line_cost = 5000.0
                lv_line_capacity = 10.0
                lv_line_max_length = 30.0
                connection_cost_per_hh = 125.0
                hv_lv_transformer_cost = 5000.0
                discount_rate = 0.08
                system_life = 30

                transmission_losses = float(country[SPE_GRID_LOSSES])
                base_to_peak_load_ratio = float(country[SPE_BASE_TO_PEAK])

                if calc_lcoe:
                    om_of_td_lines = 0.03
                    lcoe_grid = float(country[SPE_GRID_PRICE])
                    diesel_price = float(country[SPE_DIESEL_PRICE_LOW])
                else:
                    om_of_td_lines = 0.0
                    lcoe_grid = 0.0
                    diesel_price = 0.0

                # load estimation
                consumption = people / NUM_PEOPLE_PER_HH * target_energy_access_level
                average_load = consumption * (1+transmission_losses) / 8760
                peak_load = average_load / base_to_peak_load_ratio

                # transmission calculation
                no_mv_lines = ceil(peak_load / mv_line_capacity)
                no_lv_lines = ceil(peak_load / lv_line_capacity)
                lv_network_capacity = no_lv_lines / no_mv_lines
                lv_network_length = ((grid_cell_area/no_mv_lines)/(lv_line_max_length/sqrt(2)))**2
                actual_lv_lines = ceil(min([people/NUM_PEOPLE_PER_HH, max([lv_network_capacity, lv_network_length])]))
                hh_per_lv_network = (people/NUM_PEOPLE_PER_HH)/(actual_lv_lines*no_mv_lines)
                lv_unit_length = sqrt(grid_cell_area/(people/NUM_PEOPLE_PER_HH))*sqrt(2)/2
                lv_lines_length_per_lv_network = 1.333 * hh_per_lv_network * lv_unit_length
                total_lv_lines_length = no_mv_lines * actual_lv_lines * lv_lines_length_per_lv_network
                line_reach = (grid_cell_area/no_mv_lines)/(2*sqrt(grid_cell_area/no_lv_lines))
                total_length_of_lines = min([line_reach, mv_line_max_length])*no_mv_lines
                additional_hv_lines = max([0,round(sqrt(grid_cell_area)/(2*min([line_reach, mv_line_max_length]))/10,3)-1])
                hv_lines_total_length = (sqrt(grid_cell_area)/2)*additional_hv_lines*sqrt(grid_cell_area)
                num_transformers = ceil(additional_hv_lines+no_mv_lines+(no_mv_lines*actual_lv_lines))

                lcoe_grid_list = []
                for additional_mv_line_length in ELEC_DISTANCES:
                    td_investment_cost =    hv_lines_total_length*hv_line_cost + \
                                            total_length_of_lines*mv_line_cost + \
                                            total_lv_lines_length*lv_line_cost + \
                                            num_transformers*hv_lv_transformer_cost + \
                                            (people/NUM_PEOPLE_PER_HH)*connection_cost_per_hh + \
                                            additional_mv_line_length*(mv_line_cost*(1+mv_increase_rate)**((additional_mv_line_length/5)-1))
                    td_om_cost = td_investment_cost*om_of_td_lines

                    lcoe = time_value_lcoe(discount_rate,
                                           system_life,
                                           consumption*(1+transmission_losses)/1000,
                                           td_investment_cost,
                                           td_om_cost,
                                           lcoe_grid * 1000)
                    lcoe_grid_list.append(lcoe)

                # mg_hydro
                if calc_lcoe: om_costs = 0.02
                else: om_costs = 0.0
                lcoe_mg_hydro = calc_tech_lcoe(people,
                                      NUM_PEOPLE_PER_HH,
                                      target_energy_access_level,
                                      discount_rate,
                                      total_lv_lines_length,
                                      mv_line_cost,
                                      lv_line_cost,
                                      om_of_td_lines,
                                      capacity_factor = 0.5,
                                      distribution_losses = 0.05,
                                      connection_cost_per_hh = 100.0,
                                      capital_cost = 5000.0,
                                      om_costs = om_costs,
                                      base_to_peak_load_ratio = 1.0,
                                      system_life = 30,
                                      mv_line_length = 5)

                # mg_pv1750
                irradiation = 1750.0
                if calc_lcoe: om_costs = 0.02
                else: om_costs = 0.0
                lcoe_mg_pv1750 = calc_tech_lcoe(people,
                                      NUM_PEOPLE_PER_HH,
                                      target_energy_access_level,
                                      discount_rate,
                                      total_lv_lines_length,
                                      mv_line_cost,
                                      lv_line_cost,
                                      om_of_td_lines,
                                      capacity_factor = irradiation / 8760,
                                      distribution_losses=0.05,
                                      connection_cost_per_hh=100.0,
                                      capital_cost = 4300.0,
                                      om_costs = om_costs,
                                      base_to_peak_load_ratio = 0.9,
                                      system_life = 20,
                                      mv_line_length = 0)

                # mg_pv2250
                irradiation = 2250.0
                if calc_lcoe: om_costs = 0.02
                else: om_costs = 0.0
                lcoe_mg_pv2250 = calc_tech_lcoe(people,
                                      NUM_PEOPLE_PER_HH,
                                      target_energy_access_level,
                                      discount_rate,
                                      total_lv_lines_length,
                                      mv_line_cost,
                                      lv_line_cost,
                                      om_of_td_lines,
                                      capacity_factor=irradiation / 8760,
                                      distribution_losses=0.05,
                                      connection_cost_per_hh=100.0,
                                      capital_cost=4300.0,
                                      om_costs=om_costs,
                                      base_to_peak_load_ratio=0.9,
                                      system_life=20,
                                      mv_line_length=0)

                # mg_wind0.2
                if calc_lcoe: om_costs = 0.02
                else: om_costs = 0.0
                lcoe_mg_wind02 = calc_tech_lcoe(people,
                                      NUM_PEOPLE_PER_HH,
                                      target_energy_access_level,
                                      discount_rate,
                                      total_lv_lines_length,
                                      mv_line_cost,
                                      lv_line_cost,
                                      om_of_td_lines,
                                      capacity_factor=0.2,
                                      distribution_losses=0.05,
                                      connection_cost_per_hh=100.0,
                                      capital_cost=3000.0,
                                      om_costs=om_costs,
                                      base_to_peak_load_ratio=0.75,
                                      system_life=20,
                                      mv_line_length=0)

                # mg_wind0.3
                if calc_lcoe: om_costs = 0.02
                else: om_costs = 0.0
                lcoe_mg_wind03 = calc_tech_lcoe(people,
                                      NUM_PEOPLE_PER_HH,
                                      target_energy_access_level,
                                      discount_rate,
                                      total_lv_lines_length,
                                      mv_line_cost,
                                      lv_line_cost,
                                      om_of_td_lines,
                                      capacity_factor=0.3,
                                      distribution_losses=0.05,
                                      connection_cost_per_hh=100.0,
                                      capital_cost=3000.0,
                                      om_costs=om_costs,
                                      base_to_peak_load_ratio=0.75,
                                      system_life=20,
                                      mv_line_length=0)

                # mg_wind0.4
                if calc_lcoe: om_costs = 0.02
                else: om_costs = 0.0
                lcoe_mg_wind04 = calc_tech_lcoe(people,
                                      NUM_PEOPLE_PER_HH,
                                      target_energy_access_level,
                                      discount_rate,
                                      total_lv_lines_length,
                                      mv_line_cost,
                                      lv_line_cost,
                                      om_of_td_lines,
                                      capacity_factor=0.4,
                                      distribution_losses=0.05,
                                      connection_cost_per_hh=100.0,
                                      capital_cost=3000.0,
                                      om_costs=om_costs,
                                      base_to_peak_load_ratio=0.75,
                                      system_life=20,
                                      mv_line_length=0)

                # mg_diesel
                if calc_lcoe: om_costs = 0.1
                else: om_costs = 0.0
                lcoe_mg_diesel = calc_tech_lcoe(people,
                                      NUM_PEOPLE_PER_HH,
                                      target_energy_access_level,
                                      discount_rate,
                                      total_lv_lines_length,
                                      mv_line_cost,
                                      lv_line_cost,
                                      om_of_td_lines,
                                      capacity_factor=0.7,
                                      distribution_losses=0.05,
                                      connection_cost_per_hh=100.0,
                                      capital_cost=721.0,
                                      om_costs=om_costs,
                                      base_to_peak_load_ratio=0.5,
                                      system_life=15,
                                      mv_line_length=0,
                                      diesel=True,
                                      efficiency=0.33,
                                      fuel_cost=diesel_price/10*1000)

                # sa_diesel
                if calc_lcoe: om_costs = 0.1
                else: om_costs = 0.0
                lcoe_sa_diesel = calc_tech_lcoe(people,
                                                NUM_PEOPLE_PER_HH,
                                                target_energy_access_level,
                                                discount_rate,
                                                0,
                                                0,
                                                0,
                                                0,
                                                capacity_factor=0.7,
                                                distribution_losses=0.0,
                                                connection_cost_per_hh=100.0,
                                                capital_cost=721.0,
                                                om_costs=om_costs,
                                                base_to_peak_load_ratio=0.5,
                                                system_life=15,
                                                mv_line_length=0,
                                                diesel=True,
                                                efficiency=0.33,
                                                fuel_cost=diesel_price / 10 * 1000)

                # sa_pv1750
                irradiation = 1750.0
                if calc_lcoe: om_costs = 0.02
                else: om_costs = 0.0
                lcoe_sa_pv1750 = calc_tech_lcoe(people,
                                      NUM_PEOPLE_PER_HH,
                                      target_energy_access_level,
                                      discount_rate,
                                      0,
                                      0,
                                      0,
                                      0,
                                      capacity_factor = irradiation / 8760,
                                      distribution_losses=0.0,
                                      connection_cost_per_hh=100.0,
                                      capital_cost = 4300.0,
                                      om_costs = om_costs,
                                      base_to_peak_load_ratio = 0.9,
                                      system_life = 20,
                                      mv_line_length = 0)

                # sa_pv2250
                irradiation = 2250.0
                if calc_lcoe: om_costs = 0.02
                else: om_costs = 0.0
                lcoe_sa_pv2250 = calc_tech_lcoe(people,
                                      NUM_PEOPLE_PER_HH,
                                      target_energy_access_level,
                                      discount_rate,
                                      0,
                                      0,
                                      0,
                                      0,
                                      capacity_factor=irradiation / 8760,
                                      distribution_losses=0.0,
                                      connection_cost_per_hh=100.0,
                                      capital_cost=4300.0,
                                      om_costs=om_costs,
                                      base_to_peak_load_ratio=0.9,
                                      system_life=20,
                                      mv_line_length=0)

                people /= 100 # reset people to original value
                if calc_lcoe:
                    grid_lcoes[country_name][people] = lcoe_grid_list
                    tech_lcoes[country_name][people][techs[0]] = lcoe_mg_hydro
                    tech_lcoes[country_name][people][techs[1]] = lcoe_mg_pv1750
                    tech_lcoes[country_name][people][techs[2]] = lcoe_mg_pv2250
                    tech_lcoes[country_name][people][techs[3]] = lcoe_mg_wind02
                    tech_lcoes[country_name][people][techs[4]] = lcoe_mg_wind03
                    tech_lcoes[country_name][people][techs[5]] = lcoe_mg_wind04
                    tech_lcoes[country_name][people][techs[6]] = lcoe_mg_diesel
                    tech_lcoes[country_name][people][techs[7]] = lcoe_sa_diesel
                    tech_lcoes[country_name][people][techs[8]] = lcoe_sa_pv1750
                    tech_lcoes[country_name][people][techs[9]] = lcoe_sa_pv2250
                else:
                    grid_cap[country_name][people] = lcoe_grid_list
                    tech_cap[country_name][people][techs[0]] = lcoe_mg_hydro
                    tech_cap[country_name][people][techs[1]] = lcoe_mg_pv1750
                    tech_cap[country_name][people][techs[2]] = lcoe_mg_pv2250
                    tech_cap[country_name][people][techs[3]] = lcoe_mg_wind02
                    tech_cap[country_name][people][techs[4]] = lcoe_mg_wind03
                    tech_cap[country_name][people][techs[5]] = lcoe_mg_wind04
                    tech_cap[country_name][people][techs[6]] = lcoe_mg_diesel
                    tech_cap[country_name][people][techs[7]] = lcoe_sa_diesel
                    tech_cap[country_name][people][techs[8]] = lcoe_sa_pv1750
                    tech_cap[country_name][people][techs[9]] = lcoe_sa_pv2250

        if calc_lcoe:
            calc_lcoe = False
        else:
            break

    grid_lcoes.transpose(2, 0, 1).to_frame().to_csv(grid_lcoes_csv)
    grid_cap.transpose(2, 0, 1).to_frame().to_csv(grid_cap_csv)
    tech_lcoes.transpose(2, 0, 1).to_frame().to_csv(tech_lcoes_csv)
    tech_cap.transpose(2, 0, 1).to_frame().to_csv(tech_cap_csv)

    ##### Calculate num people triggers
    num_people_for_grid = pd.DataFrame(1e9 * np.ones([len(ELEC_DISTANCES),len(country_specs)]),
                                      index=ELEC_DISTANCES,
                                      columns=country_specs[SPE_COUNTRY].values)

    for country in grid_lcoes:
        for additional_mv_line_length in ELEC_DISTANCES:
            for people in people_arr:
                lcoes = tech_lcoes[country][people]
                min_lcoe_techs = min(lcoes[MG_DIESEL], lcoes[MG_WIND_MID],
                                    (lcoes[SA_PV_LOW]+lcoes[SA_PV_HIGH])/2,
                                     lcoes[MG_HYDRO])

                if grid_lcoes[country][people][additional_mv_line_length] < min_lcoe_techs:
                    num_people_for_grid[country][additional_mv_line_length] = people
                    break

    num_people_for_grid.to_csv(num_people_csv)