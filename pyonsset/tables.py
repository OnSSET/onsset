"""
Contains functions to calculate LCOEs and number of people required for grid.
"""

import logging
import numpy as np
import pandas as pd
from math import ceil, sqrt
from pyonsset.constants import *

logging.basicConfig(format='%(asctime)s\t\t%(message)s', level=logging.DEBUG)


def make_tables(country, scenario):
    """
    Create the LCOES and capital costs for grid and each technology, as well as the number of people required to be
    grid-connected, for each set of parameters.

    @param country:
    @param scenario: the scenario value in kWh/hh/year
    """

    logging.info('Making tables: {} for scenario {}'.format(country, scenario))

    lcoes_dir = os.path.join('db/{}/lcoes/{}'.format(country, scenario))
    if not os.path.exists(lcoes_dir):
        os.makedirs(lcoes_dir)
    grid_lcoes_csv = os.path.join(lcoes_dir, 'grid_lcoes_{}_{}.csv'.format(country, scenario))
    grid_cap_csv = os.path.join(lcoes_dir, 'grid_cap_{}_{}.csv'.format(country, scenario))
    tech_lcoes_csv = os.path.join(lcoes_dir, 'tech_lcoes_{}_{}.csv'.format(country, scenario))
    tech_cap_csv = os.path.join(lcoes_dir, 'tech_cap_{}_{}.csv'.format(country, scenario))
    num_people_csv = os.path.join(lcoes_dir, 'num_people_{}_{}.csv'.format(country, scenario))

    # Import country specific values from Excel
    specs = pd.read_excel(FF_SPECS, index_col=0)

    # From 0 to 340 000 people per km2 (must be checked if max pop changes)
    people_arr = list(range(10)) + list(range(10, 1000, 10)) + list(range(1000, 10000, 100)) + \
                 list(range(10000, 350000, 10000))
    people_arr_direct = list(range(1000)) + list(range(1000,10000,10)) + list(range(10000,350000,1000))

    # Techs must be modified if any new technologies are added
    techs = [MG_HYDRO, MG_PV_LOW, MG_PV_MID, MG_PV_HIGH, MG_WIND_LOW, MG_WIND_MID,
             MG_WIND_HIGH, MG_WIND_EXTRA_HIGH, MG_DIESEL, SA_DIESEL, SA_PV_LOW, SA_PV_MID, SA_PV_HIGH]

    # A pd.Panel for each of the main results
    grid_lcoes = pd.DataFrame(index=ELEC_DISTS, columns=people_arr_direct)
    grid_cap = pd.DataFrame(index=ELEC_DISTS, columns=people_arr)
    tech_lcoes = pd.DataFrame(index=techs, columns=people_arr)
    tech_cap = pd.DataFrame(index=techs, columns=people_arr)
    num_people_for_grid = pd.Series(1e9 * np.ones(len(NUM_PEOPLE_DISTS)), index=NUM_PEOPLE_DISTS)

    country_specs = specs.loc[country]

    transmission_losses = float(country_specs[SPE_GRID_LOSSES])
    base_to_peak_load_ratio = float(country_specs[SPE_BASE_TO_PEAK])
    grid_price = float(country_specs[SPE_GRID_PRICE])
    diesel_price = float(country_specs[SPE_DIESEL_PRICE_LOW]) / LHV_DIESEL  # to convert from USD/L to USD/kWh
    grid_capacity_investment = float(country_specs[SPE_GRID_CAPACITY_INVESTMENT])

    for people in people_arr_direct:
        grid_lcoes[people] = get_grid_lcoes(people, scenario, False, transmission_losses,
                                                          base_to_peak_load_ratio, grid_price,
                                                          grid_capacity_investment)

    for people in people_arr:
        lcoes = get_tech_lcoes(people, scenario, False, diesel_price)
        tech_lcoes[people][MG_HYDRO] = lcoes[MG_HYDRO]
        tech_lcoes[people][MG_PV_LOW] = lcoes[MG_PV_LOW]
        tech_lcoes[people][MG_PV_MID] = lcoes[MG_PV_MID]
        tech_lcoes[people][MG_PV_HIGH] = lcoes[MG_PV_HIGH]
        tech_lcoes[people][MG_WIND_LOW] = lcoes[MG_WIND_LOW]
        tech_lcoes[people][MG_WIND_MID] = lcoes[MG_WIND_MID]
        tech_lcoes[people][MG_WIND_HIGH] = lcoes[MG_WIND_HIGH]
        tech_lcoes[people][MG_WIND_EXTRA_HIGH] = lcoes[MG_WIND_EXTRA_HIGH]
        tech_lcoes[people][MG_DIESEL] = lcoes[MG_DIESEL]
        tech_lcoes[people][SA_DIESEL] = lcoes[SA_DIESEL]
        tech_lcoes[people][SA_PV_LOW] = lcoes[SA_PV_LOW]
        tech_lcoes[people][SA_PV_MID] = lcoes[SA_PV_MID]
        tech_lcoes[people][SA_PV_HIGH] = lcoes[SA_PV_HIGH]

        # Then calculate only the capital costs, and insert the values
        grid_cap[people] = get_grid_lcoes(people, scenario, True, transmission_losses,
                                                        base_to_peak_load_ratio, grid_price,
                                                        grid_capacity_investment)

        caps = get_tech_lcoes(people, scenario, True, diesel_price)
        tech_cap[people][MG_HYDRO] = caps[MG_HYDRO]
        tech_cap[people][MG_PV_LOW] = caps[MG_PV_LOW]
        tech_cap[people][MG_PV_MID] = caps[MG_PV_MID]
        tech_cap[people][MG_PV_HIGH] = caps[MG_PV_HIGH]
        tech_cap[people][MG_WIND_LOW] = caps[MG_WIND_LOW]
        tech_cap[people][MG_WIND_MID] = caps[MG_WIND_MID]
        tech_cap[people][MG_WIND_HIGH] = caps[MG_WIND_HIGH]
        tech_cap[people][MG_WIND_EXTRA_HIGH] = caps[MG_WIND_EXTRA_HIGH]
        tech_cap[people][MG_DIESEL] = caps[MG_DIESEL]
        tech_cap[people][SA_DIESEL] = caps[SA_DIESEL]
        tech_cap[people][SA_PV_LOW] = caps[SA_PV_LOW]
        tech_cap[people][SA_PV_MID] = caps[SA_PV_MID]
        tech_cap[people][SA_PV_HIGH] = caps[SA_PV_HIGH]

    # The following section calculates the number of people required before grid-connecting is feasible
    # Dependent on country and distance from existing grid
    # The dataframe is initialised with very high default values
    # Loop through every combination of variables and see at what point (number of people) the grid becomes the
    # most economical option.
    ghi = country_specs[SPE_AVE_GHI]
    wind_cf = country_specs[SPE_AVE_WINDCF]
    travel_hours = country_specs[SPE_AVE_TRAVEL_HOURS]

    for additional_mv_line_length in NUM_PEOPLE_DISTS:
        for people in people_arr:
            #if people > people_arr_direct[-1]:
            #    break

            lcoes = tech_lcoes[people]

            cost_mg_diesel = lcoes[MG_DIESEL] + (2 * country_specs[SPE_DIESEL_PRICE_HIGH] * 33.7 * travel_hours /
                                                 15000) * (1 / 0.3) * (1 / LHV_DIESEL)

            cost_mg_pv = np.interp(ghi, [PV_LOW, PV_MID, PV_HIGH],
                                   [lcoes[MG_PV_LOW], lcoes[MG_PV_MID], lcoes[MG_PV_HIGH]])
            cost_sa_pv = np.interp(ghi, [PV_LOW, PV_MID, PV_HIGH],
                                   [lcoes[SA_PV_LOW], lcoes[SA_PV_MID], lcoes[SA_PV_HIGH]])
            cost_mg_wind = np.interp(wind_cf, [WIND_LOW, WIND_MID, WIND_HIGH, WIND_EXTRA_HIGH],
                                     [lcoes[MG_WIND_LOW], lcoes[MG_WIND_MID],
                                      lcoes[MG_WIND_HIGH], lcoes[MG_WIND_EXTRA_HIGH]])

            min_lcoe_techs = min(cost_mg_pv, cost_sa_pv, cost_mg_wind, cost_mg_diesel)

            if grid_lcoes[people][additional_mv_line_length] < min_lcoe_techs:
                num_people_for_grid[additional_mv_line_length] = people
                break

    grid_lcoes.to_csv(grid_lcoes_csv)
    grid_cap.to_csv(grid_cap_csv)
    tech_lcoes.to_csv(tech_lcoes_csv)
    tech_cap.to_csv(tech_cap_csv)
    num_people_for_grid.to_csv(num_people_csv)


def get_grid_lcoes(people, scenario, calc_cap_only, transmission_losses,
                   base_to_peak_load_ratio, grid_price, grid_capacity_investment):
    """
    @param people: the number of people for this iteration
    @param scenario: the scenario, kWh/hh/year
    @param calc_cap_only: # whether to calculate capital cost only, or include full LCOE
    @param transmission_losses
    @param base_to_peak_load_ratio
    @param grid_price
    @param grid_capacity_investment
    @return: a dictionary containing the LCOE for each technology pathway
    """

    # Each technology gets a call to calc_lcoe() with the relevant parameters
    # The grid calculation is a list comprehension including lcoes for each value in ELEC_DISTS
    return [calc_lcoe(people=people,
                      scenario=scenario,
                      om_of_td_lines=0.03,
                      distribution_losses=transmission_losses,
                      connection_cost_per_hh=125,
                      base_to_peak_load_ratio=base_to_peak_load_ratio,
                      system_life=30,
                      additional_mv_line_length=additional_mv_line_length,
                      grid_price=grid_price,
                      grid=True,
                      grid_capacity_investment=grid_capacity_investment,
                      calc_cap_only=calc_cap_only)
            for additional_mv_line_length in ELEC_DISTS]


def get_tech_lcoes(people, scenario, calc_cap_only, diesel_price):
    """

    @param people: the number of people for this iteration
    @param scenario: the scenario, kWh/hh/year
    @param calc_cap_only: # whether to calculate capital cost only, or include full LCOE
    @param diesel_price
    @return: a dictionary containing the LCOE for each technology pathway
    """

    lcoes = {}

    lcoes[MG_HYDRO] = calc_lcoe(people=people,
                                scenario=scenario,
                                om_of_td_lines=0.03,
                                capacity_factor=0.5,
                                distribution_losses=0.05,
                                connection_cost_per_hh=100,
                                capital_cost=5000,
                                om_costs=0.02,
                                base_to_peak_load_ratio=1,
                                system_life=30,
                                mv_line_length=5,
                                calc_cap_only=calc_cap_only)

    lcoes[MG_PV_LOW], lcoes[MG_PV_MID], lcoes[MG_PV_HIGH] = [calc_lcoe(people=people,
                                                                       scenario=scenario,
                                                                       om_of_td_lines=0.03,
                                                                       capacity_factor=ghi / HOURS_PER_YEAR,
                                                                       distribution_losses=0.05,
                                                                       connection_cost_per_hh=100,
                                                                       capital_cost=4300,
                                                                       om_costs=0.0015,
                                                                       base_to_peak_load_ratio=0.9,
                                                                       system_life=20,
                                                                       calc_cap_only=calc_cap_only)
                                                             for ghi in [PV_LOW, PV_MID, PV_HIGH]]

    lcoes[MG_WIND_LOW], lcoes[MG_WIND_MID], lcoes[MG_WIND_HIGH], lcoes[MG_WIND_EXTRA_HIGH] = [calc_lcoe(
                                  people=people,
                                  scenario=scenario,
                                  om_of_td_lines=0.03,
                                  capacity_factor=cf,
                                  distribution_losses=0.05,
                                  connection_cost_per_hh=100,
                                  capital_cost=3000,
                                  om_costs=0.02,
                                  base_to_peak_load_ratio=0.75,
                                  system_life=20,
                                  calc_cap_only=calc_cap_only)
                                  for cf in [WIND_LOW, WIND_MID, WIND_HIGH, WIND_EXTRA_HIGH]]

    lcoes[MG_DIESEL] = calc_lcoe(people=people,
                                 scenario=scenario,
                                 om_of_td_lines=0.03,
                                 capacity_factor=0.7,
                                 distribution_losses=0.05,
                                 connection_cost_per_hh=100,
                                 capital_cost=721,
                                 om_costs=0.1,
                                 base_to_peak_load_ratio=0.5,
                                 system_life=15,
                                 efficiency=0.33,
                                 diesel_price=diesel_price,
                                 diesel=True,
                                 calc_cap_only=calc_cap_only)

    lcoes[SA_DIESEL] = calc_lcoe(people=people,
                                 scenario=scenario,
                                 om_of_td_lines=0,
                                 capacity_factor=0.7,
                                 distribution_losses=0,
                                 connection_cost_per_hh=100,
                                 capital_cost=938,
                                 om_costs=0.1,
                                 base_to_peak_load_ratio=0.5,
                                 system_life=10,
                                 efficiency=0.28,
                                 diesel_price=diesel_price,
                                 diesel=True,
                                 standalone=True,
                                 calc_cap_only=calc_cap_only)

    lcoes[SA_PV_LOW], lcoes[SA_PV_MID], lcoes[SA_PV_HIGH] = [calc_lcoe(
                                  people=people,
                                  scenario=scenario,
                                  om_of_td_lines=0,
                                  capacity_factor=ghi / HOURS_PER_YEAR,
                                  distribution_losses=0,
                                  connection_cost_per_hh=100,
                                  capital_cost=5500,
                                  om_costs=0.0012,
                                  base_to_peak_load_ratio=0.9,
                                  system_life=15,
                                  standalone=True,
                                  calc_cap_only=calc_cap_only)
                                  for ghi in [PV_LOW, PV_MID, PV_HIGH]]

    return lcoes


def calc_lcoe(people, scenario, om_of_td_lines, distribution_losses, connection_cost_per_hh,
              base_to_peak_load_ratio, system_life, mv_line_length=0, om_costs=0.0, capital_cost=0, capacity_factor=1.0,
              efficiency=1.0, diesel_price=0.0, additional_mv_line_length=0, grid_price=0.0, grid=False, diesel=False,
              standalone=False, grid_capacity_investment=0.0, calc_cap_only=False):
    """
    Calculate the LCOE for a single technology with a single people/distance pair.

    @param people: the number of people
    @param scenario: the scenario value, in kWh/hh/year
    @param om_of_td_lines: the O&M cost of TD lines as a percentage of investment cost
    @param distribution_losses: as a percentage
    @param connection_cost_per_hh: USD, cost to connect a household to a specific technology
    @param base_to_peak_load_ratio: as a percentage
    @param system_life: in years
    @param mv_line_length: the MV line length in km needed to connect minigrid technologies
    @param om_costs: O&M costs of a technology as a percentage of capital cost (non-grid only)
    @param capital_cost: USD/kW (non-grid only)
    @param capacity_factor: percentage (non-grid only)
    @param efficiency: percentage (diesel only)
    @param diesel_price: USD/kWh (diesel only)
    @param additional_mv_line_length: the additional MV line length in km, from ELEC_DISTS (grid only)
    @param grid_price: USD/kWh (grid only)
    @param grid: True/False flag for grid
    @param diesel: True/False flag for diesel
    @param standalone: True/False flag for standalone
    @param grid_capacity_investment: grid capacity investment costs (grid only) USD/kW
    @param calc_cap_only: True/False flag for calculating only capital cost
    @return: The LCOE values with the given parameters, or the capital cost as a function of num people
    """

    # To prevent any div/0 error
    if people == 0:
        people = 0.00001

    grid_cell_area = 1  # This was 100, changed to 1 which creates different results but let's go with it
    people *= grid_cell_area  # To adjust for incorrect grid size above

    mv_line_cost = 9000  # USD/km
    lv_line_cost = 5000  # USD/km
    discount_rate = 0.08  # percent
    mv_line_capacity = 50  # kW/line
    lv_line_capacity = 10  # kW/line
    lv_line_max_length = 30  # km
    hv_line_cost = 53000  # USD/km
    mv_line_max_length = 50  # km
    hv_lv_transformer_cost = 5000  # USD/unit
    mv_increase_rate = 0.1  # percentage

    consumption = people / NUM_PEOPLE_PER_HH * scenario  # kWh/year
    average_load = consumption * (1 + distribution_losses) / HOURS_PER_YEAR
    peak_load = average_load / base_to_peak_load_ratio

    no_mv_lines = ceil(peak_load / mv_line_capacity)
    no_lv_lines = ceil(peak_load / lv_line_capacity)
    lv_networks_lim_capacity = no_lv_lines / no_mv_lines
    lv_networks_lim_length = ((grid_cell_area / no_mv_lines) / (lv_line_max_length / sqrt(2))) ** 2
    actual_lv_lines = ceil(min([people / NUM_PEOPLE_PER_HH, max([lv_networks_lim_capacity, lv_networks_lim_length])]))
    hh_per_lv_network = (people / NUM_PEOPLE_PER_HH) / (actual_lv_lines * no_mv_lines)
    lv_unit_length = sqrt(grid_cell_area / (people / NUM_PEOPLE_PER_HH)) * sqrt(2) / 2
    lv_lines_length_per_lv_network = 1.333 * hh_per_lv_network * lv_unit_length
    total_lv_lines_length = no_mv_lines * actual_lv_lines * lv_lines_length_per_lv_network
    line_reach = (grid_cell_area / no_mv_lines) / (2 * sqrt(grid_cell_area / no_lv_lines))
    total_length_of_lines = min([line_reach, mv_line_max_length]) * no_mv_lines
    additional_hv_lines = max(
        [0, round(sqrt(grid_cell_area) / (2 * min([line_reach, mv_line_max_length])) / 10, 3) - 1])
    hv_lines_total_length = (sqrt(grid_cell_area) / 2) * additional_hv_lines * sqrt(grid_cell_area)
    num_transformers = ceil(additional_hv_lines + no_mv_lines + (no_mv_lines * actual_lv_lines))
    generation_per_year = average_load * HOURS_PER_YEAR

    # The investment and O&M costs are different for grid and non-grid solutions
    if grid:
        td_investment_cost = hv_lines_total_length * hv_line_cost + \
                             total_length_of_lines * mv_line_cost + \
                             total_lv_lines_length * lv_line_cost + \
                             num_transformers * hv_lv_transformer_cost + \
                             (people / NUM_PEOPLE_PER_HH) * connection_cost_per_hh + \
                             additional_mv_line_length * (
                                 mv_line_cost * (1 + mv_increase_rate) ** ((additional_mv_line_length / 5) - 1))
        td_om_cost = td_investment_cost * om_of_td_lines
        total_investment_cost = td_investment_cost
        total_om_cost = td_om_cost

    else:
        total_lv_lines_length *= 0 if standalone else 0.75
        mv_total_line_cost = mv_line_cost * mv_line_length
        lv_total_line_cost = lv_line_cost * total_lv_lines_length
        installed_capacity = peak_load / capacity_factor
        capital_investment = installed_capacity * capital_cost
        td_investment_cost = mv_total_line_cost + lv_total_line_cost + (
                             people / NUM_PEOPLE_PER_HH) * connection_cost_per_hh
        td_om_cost = td_investment_cost * om_of_td_lines
        total_investment_cost = td_investment_cost + capital_investment
        total_om_cost = td_om_cost + (capital_cost * om_costs * installed_capacity)

    # The renewable solutions have no fuel cost
    if diesel:
        fuel_cost = diesel_price / efficiency
    elif grid:
        fuel_cost = grid_price
    else:
        fuel_cost = 0

    # Perform the time value LCOE calculation

    project_life = END_YEAR - START_YEAR
    reinvest_year = 0
    if system_life < project_life:
        reinvest_year = system_life

    year = np.arange(project_life)
    el_gen = generation_per_year * np.ones(project_life)
    el_gen[0] = 0
    discount_factor = (1 + discount_rate) ** year
    investments = np.zeros(project_life)
    investments[0] = total_investment_cost
    if reinvest_year:
        investments[reinvest_year] = total_investment_cost

    salvage = np.zeros(project_life)
    used_life = project_life
    if reinvest_year:
        used_life = project_life - system_life  # so salvage will come from the remaining life after the re-investment
    salvage[-1] = total_investment_cost * (1 - used_life / system_life)

    operation_and_maintenance = total_om_cost * np.ones(project_life)
    operation_and_maintenance[0] = 0
    fuel = el_gen * fuel_cost
    fuel[0] = 0

    # So we also return the total investment cost for this number of people
    if calc_cap_only:
        discounted_investments = investments / discount_factor
        return np.sum(discounted_investments) + grid_capacity_investment * peak_load
    else:
        discounted_costs = (investments + operation_and_maintenance + fuel - salvage) / discount_factor
        discounted_generation = el_gen / discount_factor
        return np.sum(discounted_costs) / np.sum(discounted_generation)


def main():
    countries = specs = pd.read_excel(FF_SPECS, index_col=0).index.values.tolist()
    scenarios = [22, 224, 695, 1800, 2195]

    for c in countries:
        for s in scenarios:
            make_tables(c, s)

if __name__ == "__main__":
    os.chdir('..')
    print('Running as a script')
    main()
