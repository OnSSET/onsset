import logging
import numpy as np
import pandas as pd
from math import ceil, sqrt
from .constants import *

logging.basicConfig(format='%(asctime)s\t\t%(message)s', level=logging.DEBUG)


def get_grid_lcoe_table(country_specs, scenario):
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

    elec_dists = range(0, int(country_specs[SPE_MAX_GRID_EXTENSION_DIST]) + 1)

    # A pd.Panel for each of the main results
    grid_lcoes = pd.DataFrame(index=elec_dists, columns=people_arr_direct)

    num_people_per_hh = float(country_specs[SPE_NUM_PEOPLE_PER_HH])
    transmission_losses = float(country_specs[SPE_GRID_LOSSES])
    base_to_peak_load_ratio = float(country_specs[SPE_BASE_TO_PEAK])
    grid_price = float(country_specs[SPE_GRID_PRICE])
    grid_capacity_investment = float(country_specs[SPE_GRID_CAPACITY_INVESTMENT])

    for people in people_arr_direct:
        for additional_mv_line_length in elec_dists:
            grid_lcoes[people][additional_mv_line_length] = get_grid_lcoe(people, scenario, num_people_per_hh, False, transmission_losses,
                                                          base_to_peak_load_ratio, grid_price,
                                                          grid_capacity_investment, additional_mv_line_length)

    return grid_lcoes


def get_grid_lcoe(people, scenario, num_people_per_hh, calc_cap_only, transmission_losses,
                   base_to_peak_load_ratio, grid_price, grid_capacity_investment, additional_mv_line_length):
    """
    @param people: the number of people for this iteration
    @param scenario: the scenario, kWh/hh/year
    @param num_people_per_hh
    @param calc_cap_only: # whether to calculate capital cost only, or include full LCOE
    @param transmission_losses
    @param base_to_peak_load_ratio
    @param grid_price
    @param grid_capacity_investment
    @param elec_dists
    @return: a dictionary containing the LCOE for each technology pathway
    """

    # Each technology gets a call to calc_lcoe() with the relevant parameters
    # The grid calculation is a list comprehension including lcoes for each value in ELEC_DISTS
    return calc_lcoe(people=people,
                      scenario=scenario,
                      num_people_per_hh=num_people_per_hh,
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


def get_mg_hydro_lcoe(people, scenario, num_people_per_hh, calc_cap_only, mv_line_length):
    return calc_lcoe(people=people,
                                scenario=scenario,
                                num_people_per_hh=num_people_per_hh,
                                om_of_td_lines=0.03,
                                capacity_factor=0.5,
                                distribution_losses=0.05,
                                connection_cost_per_hh=100,
                                capital_cost=5000,
                                om_costs=0.02,
                                base_to_peak_load_ratio=1,
                                system_life=30,
                                mv_line_length=mv_line_length,
                                calc_cap_only=calc_cap_only)

def get_mg_pv_lcoe(people, scenario, num_people_per_hh, calc_cap_only, ghi):
    return calc_lcoe(people=people,
                           scenario=scenario,
                           num_people_per_hh=num_people_per_hh,
                           om_of_td_lines=0.03,
                           capacity_factor=ghi / HOURS_PER_YEAR,
                           distribution_losses=0.05,
                           connection_cost_per_hh=100,
                           capital_cost=4300,
                           om_costs=0.0015,
                           base_to_peak_load_ratio=0.9,
                           system_life=20,
                           calc_cap_only=calc_cap_only)

def get_mg_wind_lcoe(people, scenario, num_people_per_hh, calc_cap_only, wind_cf):
    return calc_lcoe(
                                  people=people,
                                  scenario=scenario,
                                  num_people_per_hh=num_people_per_hh,
                                  om_of_td_lines=0.03,
                                  capacity_factor=wind_cf,
                                  distribution_losses=0.05,
                                  connection_cost_per_hh=100,
                                  capital_cost=3000,
                                  om_costs=0.02,
                                  base_to_peak_load_ratio=0.75,
                                  system_life=20,
                                  calc_cap_only=calc_cap_only)

def get_mg_diesel_lcoe(people, scenario, num_people_per_hh, calc_cap_only, diesel_price):
    return calc_lcoe(people=people,
                                 scenario=scenario,
                                 num_people_per_hh=num_people_per_hh,
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

def get_sa_diesel_lcoe(people, scenario, num_people_per_hh, calc_cap_only, diesel_price):
    return calc_lcoe(people=people,
                                 scenario=scenario,
                                 num_people_per_hh=num_people_per_hh,
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

def get_sa_pv_lcoe(people, scenario, num_people_per_hh, calc_cap_only, ghi):
    return calc_lcoe(
                                  people=people,
                                  scenario=scenario,
                                  num_people_per_hh=num_people_per_hh,
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


def calc_lcoe(people, scenario, num_people_per_hh, om_of_td_lines, distribution_losses, connection_cost_per_hh,
              base_to_peak_load_ratio, system_life, mv_line_length=0, om_costs=0.0, capital_cost=0, capacity_factor=1.0,
              efficiency=1.0, diesel_price=0.0, additional_mv_line_length=0, grid_price=0.0, grid=False, diesel=False,
              standalone=False, grid_capacity_investment=0.0, calc_cap_only=False):
    """
    Calculate the LCOE for a single technology with a single people/distance pair.

    @param people: the number of people
    @param scenario: the scenario value, in kWh/hh/year
    @param num_people_per_hh
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

    consumption = people / num_people_per_hh * scenario  # kWh/year
    average_load = consumption * (1 + distribution_losses) / HOURS_PER_YEAR
    peak_load = average_load / base_to_peak_load_ratio

    no_mv_lines = ceil(peak_load / mv_line_capacity)
    no_lv_lines = ceil(peak_load / lv_line_capacity)
    lv_networks_lim_capacity = no_lv_lines / no_mv_lines
    lv_networks_lim_length = ((grid_cell_area / no_mv_lines) / (lv_line_max_length / sqrt(2))) ** 2
    actual_lv_lines = ceil(min([people / num_people_per_hh, max([lv_networks_lim_capacity, lv_networks_lim_length])]))
    hh_per_lv_network = (people / num_people_per_hh) / (actual_lv_lines * no_mv_lines)
    lv_unit_length = sqrt(grid_cell_area / (people / num_people_per_hh)) * sqrt(2) / 2
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
