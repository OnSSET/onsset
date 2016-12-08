# Calculate the levelised cost for given technologies and parameters
#
# Author: Christopher Arderne
# Date: 26 November 2016
# Python version: 3.5

import logging
import numpy as np
import pandas as pd
from math import ceil, sqrt
from pyonsset.constants import *

logging.basicConfig(format='%(asctime)s\t\t%(message)s', level=logging.DEBUG)


def get_grid_lcoe_table(scenario, max_dist, num_people_per_hh, transmission_losses, base_to_peak_load_ratio,
                        grid_price, grid_capacity_investment, grid_vals):
    """
    Create the LCOES and capital costs for grid and each technology, as well as the number of people required to be
    grid-connected, for each set of parameters.

    @param df:
    @param country_specs:
    @param scenario:
    @param diesel_high
    """

    logging.info('Create grid lcoe tables')

    people_arr_direct = list(range(1000)) + list(range(1000,10000,10)) + list(range(10000,350000,1000))

    elec_dists = range(0, int(max_dist) + 1)

    # A pd.Panel for each of the main results
    grid_lcoes = pd.DataFrame(index=elec_dists, columns=people_arr_direct)

    for people in people_arr_direct:
        for additional_mv_line_length in elec_dists:
            grid_lcoes[people][additional_mv_line_length] = calc_lcoe(people=people,
                                                                      scenario=scenario,
                                                                      num_people_per_hh=num_people_per_hh,
                                                                      om_of_td_lines=grid_vals['om_of_td_lines'],
                                                                      distribution_losses=transmission_losses,
                                                                      connection_cost_per_hh=grid_vals['connection_cost_per_hh'],
                                                                      base_to_peak_load_ratio=base_to_peak_load_ratio,
                                                                      system_life=grid_vals['system_life'],
                                                                      additional_mv_line_length=additional_mv_line_length,
                                                                      grid_price=grid_price,
                                                                      grid=True,
                                                                      grid_capacity_investment=grid_capacity_investment,
                                                                      calc_cap_only=False)

    return grid_lcoes


def calc_lcoe(people, scenario, num_people_per_hh, om_of_td_lines, distribution_losses, connection_cost_per_hh,
              base_to_peak_load_ratio, system_life, mv_line_length=0, om_costs=0.0, capital_cost=0, capacity_factor=1.0,
              efficiency=1.0, diesel_price=0.0, additional_mv_line_length=0, grid_price=0.0, grid=False, diesel=False,
              standalone=False, grid_capacity_investment=0.0, calc_cap_only=False):

    # To prevent any div/0 error
    if people == 0:
        if calc_cap_only:
            return 0
        else:
            people = 0.00001

    grid_cell_area = 1  # This was 100, changed to 1 which creates different results but let's go with it

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

    consumption = people / num_people_per_hh * scenario  # kWh/year
    average_load = consumption * (1 + distribution_losses) / HOURS_PER_YEAR
    peak_load = average_load / base_to_peak_load_ratio

    no_mv_lines = peak_load / mv_line_capacity
    no_lv_lines = peak_load / lv_line_capacity
    lv_networks_lim_capacity = no_lv_lines / no_mv_lines
    lv_networks_lim_length = ((grid_cell_area / no_mv_lines) / (lv_line_max_length / sqrt(2))) ** 2
    actual_lv_lines = min([people / num_people_per_hh, max([lv_networks_lim_capacity, lv_networks_lim_length])])
    hh_per_lv_network = (people / num_people_per_hh) / (actual_lv_lines * no_mv_lines)
    lv_unit_length = sqrt(grid_cell_area / (people / num_people_per_hh)) * sqrt(2) / 2
    lv_lines_length_per_lv_network = 1.333 * hh_per_lv_network * lv_unit_length
    total_lv_lines_length = no_mv_lines * actual_lv_lines * lv_lines_length_per_lv_network
    line_reach = (grid_cell_area / no_mv_lines) / (2 * sqrt(grid_cell_area / no_lv_lines))
    total_length_of_lines = min([line_reach, mv_line_max_length]) * no_mv_lines
    additional_hv_lines = max(
        [0, round(sqrt(grid_cell_area) / (2 * min([line_reach, mv_line_max_length])) / 10, 3) - 1])
    hv_lines_total_length = (sqrt(grid_cell_area) / 2) * additional_hv_lines * sqrt(grid_cell_area)
    num_transformers = additional_hv_lines + no_mv_lines + (no_mv_lines * actual_lv_lines)
    generation_per_year = average_load * HOURS_PER_YEAR

    # The investment and O&M costs are different for grid and non-grid solutions
    if grid:
        td_investment_cost = hv_lines_total_length * hv_line_cost + \
                             total_length_of_lines * mv_line_cost + \
                             total_lv_lines_length * lv_line_cost + \
                             num_transformers * hv_lv_transformer_cost + \
                             (people / num_people_per_hh) * connection_cost_per_hh + \
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
                                                                people / num_people_per_hh) * connection_cost_per_hh
        td_om_cost = td_investment_cost * om_of_td_lines
        total_investment_cost = td_investment_cost + capital_investment
        total_om_cost = td_om_cost + (capital_cost * om_costs * installed_capacity)

    # The renewable solutions have no fuel cost
    if diesel:
        fuel_cost = diesel_price / LHV_DIESEL / efficiency
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
