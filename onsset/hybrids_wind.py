import numpy as np
import pandas as pd
import numba
from numba import prange
import requests
import os
import json
import time
from io import StringIO


@numba.njit
def find_least_cost_option_wind(configuration, wind_curve, hour_numbers, load_curve, inv_eff, n_dis,
                                n_chg, dod_max, diesel_price, end_year, start_year, wind_cost, charge_controller,
                                wind_om, diesel_cost, diesel_om, battery_inverter_life, battery_inverter_cost,
                                diesel_life, wind_life, battery_cost, discount_rate, lpsp_max, diesel_limit,
                                full_life_cycles):

    wind = float(configuration[0])
    battery = float(configuration[1])
    usable_battery = battery * dod_max  # ensure the battery never goes below max depth of discharge
    diesel = float(configuration[2])

    annual_demand = load_curve.sum()

    # First the PV generation and net load (load - pv generation) is calculated for each hour of the year
    net_load, wind_gen = wind_generation(wind_curve, wind, load_curve, inv_eff)

    # For each hour of the year, diesel generation, battery charge/discharge and performance variables are calculated.
    diesel_generation_share, battery_life, unmet_demand_share, annual_fuel_consumption, \
        excess_gen_share, battery_soc_curve, diesel_gen_curve = \
        year_simulation_wind(battery_size=usable_battery, diesel_capacity=diesel, net_load=net_load,
                             hour_numbers=hour_numbers, inv_eff=inv_eff, n_dis=n_dis, n_chg=n_chg,
                             annual_demand=annual_demand, full_life_cycles=full_life_cycles, dod_max=dod_max)

    # If the system could meet the demand in a satisfactory manner (i.e. with high enough reliability and low enough
    # share of the generation coming from the diesel generator), then the LCOE is calculated. Else 99 is returned.
    if (battery_life == 0) or (unmet_demand_share > lpsp_max) or (diesel_generation_share > diesel_limit):
        lcoe = 99
        investment = 0
        fuel_cost = 0
        om_cost = 0
        npc = 0
    else:
        lcoe, investment, battery_investment, fuel_cost, \
            om_cost, npc = calculate_hybrid_lcoe_wind(diesel_price=diesel_price,
                                                     end_year=end_year,
                                                     start_year=start_year,
                                                     annual_demand=annual_demand,
                                                     fuel_usage=annual_fuel_consumption,
                                                     wind_size=wind,
                                                     wind_cost=wind_cost,
                                                     charge_controller=charge_controller,
                                                     wind_om=wind_om,
                                                     diesel_capacity=diesel,
                                                     diesel_cost=diesel_cost,
                                                     diesel_om=diesel_om,
                                                     battery_inverter_cost=battery_inverter_cost,
                                                     battery_inverter_life=battery_inverter_life,
                                                     load_curve=load_curve,
                                                     diesel_life=diesel_life,
                                                     wind_life=wind_life,
                                                     battery_life=battery_life,
                                                     battery_size=battery,
                                                     battery_cost=battery_cost,
                                                     discount_rate=discount_rate)

    return lcoe, unmet_demand_share, diesel_generation_share, investment, fuel_cost, om_cost, battery, battery_life, wind, diesel, npc

@numba.njit
def wind_generation(wind_curve, wind, load, inv_eff):
    # Calculation of Wind gen and net load
    p_rated = 600
    p_curve = [0, 0, 0, 0, 30, 77, 135, 208, 287, 371, 450, 514, 558,
               582, 594, 598, 600, 600, 600, 600, 600, 600, 600, 600, 600]
    wind_power = np.round(wind_curve)
    for i in prange(len(p_curve)):
        wind_power = np.where(wind_power == i, p_curve[i], wind_power)
    #wind_power = wind_curve
    wind_gen = wind_power * wind / p_rated
    net_load = load - wind_gen
    return net_load, wind_gen

@numba.njit
def year_simulation_wind(battery_size, diesel_capacity, net_load, hour_numbers, inv_eff, n_dis, n_chg,
                    annual_demand, full_life_cycles, dod_max):
    soc = 0.5  # Initial SOC of battery

    # Variables for tracking annual performance information
    annual_unmet_demand = 0
    annual_excess_gen = 0
    annual_diesel_gen = 0
    annual_battery_use = 0
    annual_fuel_consumption = 0

    # Arrays for tracking hourly values throughout the year (for plotting purposes)
    diesel_gen_curve = []
    battery_soc_curve = []

    net_load = net_load[0]

    # Run the simulation for each hour during one year
    for hour in hour_numbers:
        load = net_load[int(hour)]

        diesel_gen, annual_fuel_consumption, annual_diesel_gen, annual_battery_use, soc, annual_unmet_demand, \
            annual_excess_gen = hour_simulation_wind(hour, soc, load, diesel_capacity, annual_fuel_consumption,
                                                annual_diesel_gen,
                                                inv_eff, n_dis, n_chg, battery_size, annual_battery_use,
                                                annual_unmet_demand,
                                                annual_excess_gen)

        # Update plotting arrays
        diesel_gen_curve.append(diesel_gen)
        battery_soc_curve.append(soc)

    # When a full year has been simulated, calculate battery life and performance metrics
    if (battery_size > 0) & (annual_battery_use > 0):
        battery_life = min(round(full_life_cycles / (annual_battery_use)), 20)  # ToDo should dod_max be included here?
    else:
        battery_life = 20

    unmet_demand_share = annual_unmet_demand / annual_demand  # LPSP is calculated
    excess_gen_share = annual_excess_gen / annual_demand
    diesel_generation_share = annual_diesel_gen / annual_demand

    return diesel_generation_share, battery_life, unmet_demand_share, annual_fuel_consumption, \
        excess_gen_share, battery_soc_curve, diesel_gen_curve


@numba.njit
def hour_simulation_wind(hour, soc, net_load, diesel_capacity, annual_fuel_consumption, annual_diesel_gen, inv_eff, n_dis,
                    n_chg, battery_size, annual_battery_use, annual_unmet_demand, annual_excess_gen):
    # First the battery self-discharge is calculated (default rate set to 0.02% of the state-of-charge - SOC - per hour)
    battery_use = 0.0002 * soc
    soc - 0.0002 * soc

    battery_dispatchable = soc * battery_size * n_dis * inv_eff  # Max load that can be met by the battery until empty
    battery_chargeable = (1 - soc) * battery_size / n_chg / inv_eff  # Max energy that can be used to charge the battery until full

    # Below is the dispatch strategy for the diesel generator and battery

    if 4 < hour <= 17:
        # During the morning and day, the batteries are dispatched primarily.
        # The diesel generator, if needed, is run at the lowest possible capacity
        # (it is assumed that the diesel generator should never run below 40% of rated capacity)

        # Minimum diesel capacity to cover the net load after batteries.
        # Diesel generator limited by lowest possible capacity (40%) and rated capacity

        if net_load < battery_dispatchable:  # If load can be met by batteries, diesel generator is not used
            diesel_gen = 0
        else:  # If batteries are insufficient, diesel generator is used
            diesel_gen = min(max(net_load - battery_dispatchable, 0.4 * diesel_capacity), diesel_capacity)

    elif 17 < hour <= 23:
        # During the evening, the diesel generator is dispatched primarily.
        # During this time, diesel generator seeks to meet load and charge batteries for the night if possible.
        # Batteries are dispatched if diesel generation is insufficient.

        # Maximum amount of diesel needed to supply load and charge battery
        # Diesel generator limited by lowest possible capacity (40%) and rated capacity
        max_diesel = max(min(net_load + battery_chargeable, diesel_capacity), 0.4 * diesel_capacity)

        if net_load > 0:  # If there is net load after PV generation, diesel generator is used
            diesel_gen = max_diesel
        else:  # Else if there is no remaining load, diesel generator is not used
            diesel_gen = 0

    else:
        # During night, batteries are dispatched primarily. If batteries are insufficient, the diesel generator is used
        # at highest capacity required to meet load and charge batteries in order to minimize operating hours at night

        # Maximum amount of diesel needed to supply load and charge battery
        # Diesel generator limited by lowest possible capacity (40%) and rated capacity

        if net_load < battery_dispatchable:  # If load can be met by batteries, diesel generator is not used
            diesel_gen = 0
        else:  # If batteries are insufficient, diesel generator is used
            diesel_gen = max(min(net_load + battery_chargeable, diesel_capacity), 0.4 * diesel_capacity)

    if diesel_gen > 0:  # If the diesel generator was used, the amount of diesel generation and fuel used is stored
        annual_fuel_consumption += diesel_capacity * 0.08145 + diesel_gen * 0.246
        annual_diesel_gen += diesel_gen

    net_load -= diesel_gen  # Remaining load after diesel generation, used for subsequent battery calculations etc.

    soc_prev = soc  # Store the battery SOC before the hour in a variable to ensure battery is not over-used

    if (net_load > 0) & (battery_size > 0):
        if diesel_gen > 0:
            # If diesel generation is used, but is smaller than load, battery is discharged
            soc -= net_load / n_dis / inv_eff / battery_size
        elif diesel_gen == 0:
            # If net load is positive and no diesel is used, battery is discharged
            soc -= net_load / n_dis / inv_eff / battery_size
    elif (net_load < 0) & (battery_size > 0):
        if diesel_gen > 0:
            # If diesel generation is used, and is larger than load, battery is charged
            soc -= net_load * n_chg * inv_eff / battery_size
        if diesel_gen == 0:
            # If net load is negative, and no diesel has been used, excess PV gen is used to charge battery
            soc -= net_load * n_chg / battery_size

    # Store how much battery energy (measured in SOC) was discharged (if used).
    # No more than the previous SOC can be used
    if (net_load > 0) & (battery_size > 0):
        battery_use += min(net_load / n_dis / battery_size, soc_prev)

    annual_battery_use += battery_use

    # Calculate if there was any unmet demand or excess energy generation during the hour

    if battery_size > 0:
        if soc < 0:
            # If State of charge is negative, that means there's demand that could not be met.
            # If so, the annual unmet demand variable is updated and the SOC is reset to empty (0)
            annual_unmet_demand -= soc / n_dis * battery_size
            soc = 0

        if soc > 1:
            # If State of Charge is larger than 1, that means there was excess PV/diesel generation
            # If so, the annual excess generation variable is updated and the SOC is set to full (1)
            annual_excess_gen += (soc - 1) / n_chg * battery_size
            soc = 1
    else:  # This part handles the same case, if no battery is included in the system
        if net_load > 0:
            annual_unmet_demand += net_load
        if net_load < 0:
            annual_excess_gen -= net_load

    return diesel_gen, annual_fuel_consumption, annual_diesel_gen, annual_battery_use, \
        soc, annual_unmet_demand, annual_excess_gen


@numba.njit
def calculate_hybrid_lcoe_wind(diesel_price, end_year, start_year, annual_demand,
                          fuel_usage, wind_size, wind_cost, wind_life, wind_om, charge_controller,
                          diesel_capacity, diesel_cost, diesel_om, diesel_life,
                          battery_size, battery_cost, battery_life, battery_inverter_cost, battery_inverter_life,
                          load_curve, discount_rate):

    # Necessary information for calculation of LCOE is defined
    project_life = end_year - start_year  # Calculate project lifetime
    generation = np.ones(project_life) * annual_demand  # array of annual demand
    generation[0] = 0  # In first year, there is assumed to be no generation

    # Calculate LCOE
    sum_el_gen = 0
    investment = 0
    sum_costs = 0
    total_battery_investment = 0
    total_fuel_cost = 0
    total_om_cost = 0
    npc = 0

    # Iterate over each year in the project life and account for the costs that incur
    # This includes investment, OM, fuel, and reinvestment in any year a technology lifetime expires
    for year in prange(project_life + 1):
        salvage = 0
        inverter_investment = 0
        diesel_investment = 0
        wind_investment = 0
        battery_investment = 0

        fuel_costs = fuel_usage * diesel_price
        om_costs = (wind_size * (wind_cost + charge_controller) * wind_om + diesel_capacity * diesel_cost * diesel_om)

        total_fuel_cost += fuel_costs / (1 + discount_rate) ** year
        total_om_cost += om_costs / (1 + discount_rate) ** year

        # Here we check if there is need for investment/reinvestment
        if year % battery_inverter_life == 0:
            inverter_investment = max(load_curve) * battery_inverter_cost  # Battery inverter, sized based on the peak demand in the year
        if year % diesel_life == 0:
            diesel_investment = diesel_capacity * diesel_cost
        if year % wind_life == 0:
            wind_investment = wind_size * wind_cost
        if year % battery_life == 0:
            battery_investment = battery_size * battery_cost

        # In the final year, the salvage value of all components is calculated based on remaining life
        if year == project_life:
            salvage = (1 - (project_life % battery_life) / battery_life) * battery_cost * battery_size + \
                      (1 - (project_life % diesel_life) / diesel_life) * diesel_capacity * diesel_cost + \
                      (1 - (project_life % wind_life) / wind_life) * wind_size * wind_cost + \
                      (1 - (project_life % battery_inverter_life) / battery_inverter_life) * max(
                load_curve) * battery_inverter_cost

            total_battery_investment -= (1 - (
                    project_life % battery_life) / battery_life) * battery_cost * battery_size

        investment += diesel_investment + wind_investment + battery_investment + inverter_investment - salvage
        total_battery_investment += battery_investment

        sum_costs += (fuel_costs + om_costs + battery_investment + diesel_investment + wind_investment +
                      inverter_investment - salvage) / ((1 + discount_rate) ** year)

        npc += (fuel_costs + om_costs + battery_investment + diesel_investment + wind_investment +
                inverter_investment) / ((1 + discount_rate) ** year)

        if year > 0:
            sum_el_gen += annual_demand / ((1 + discount_rate) ** year)

    return sum_costs / sum_el_gen, investment, total_battery_investment, total_fuel_cost, total_om_cost, npc


@numba.njit
def calc_load_curve_wind(tier, annual_demand):
    # the values below define the load curve for the five tiers. The values reflect the share of the daily demand
    # expected in each hour of the day (sum of all values for one tier = 1)
    tier5_load_curve = [0.021008403, 0.021008403, 0.021008403, 0.021008403, 0.027310924, 0.037815126,
                        0.042016807, 0.042016807, 0.042016807, 0.042016807, 0.042016807, 0.042016807,
                        0.042016807, 0.042016807, 0.042016807, 0.042016807, 0.046218487, 0.050420168,
                        0.067226891, 0.084033613, 0.073529412, 0.052521008, 0.033613445, 0.023109244]
    tier4_load_curve = [0.017167382, 0.017167382, 0.017167382, 0.017167382, 0.025751073, 0.038626609,
                        0.042918455, 0.042918455, 0.042918455, 0.042918455, 0.042918455, 0.042918455,
                        0.042918455, 0.042918455, 0.042918455, 0.042918455, 0.0472103, 0.051502146,
                        0.068669528, 0.08583691, 0.075107296, 0.053648069, 0.034334764, 0.021459227]
    tier3_load_curve = [0.013297872, 0.013297872, 0.013297872, 0.013297872, 0.019060284, 0.034574468,
                        0.044326241, 0.044326241, 0.044326241, 0.044326241, 0.044326241, 0.044326241,
                        0.044326241, 0.044326241, 0.044326241, 0.044326241, 0.048758865, 0.053191489,
                        0.070921986, 0.088652482, 0.077570922, 0.055407801, 0.035460993, 0.019946809]
    tier2_load_curve = [0.010224949, 0.010224949, 0.010224949, 0.010224949, 0.019427403, 0.034764826,
                        0.040899796, 0.040899796, 0.040899796, 0.040899796, 0.040899796, 0.040899796,
                        0.040899796, 0.040899796, 0.040899796, 0.040899796, 0.04601227, 0.056237219,
                        0.081799591, 0.102249489, 0.089468303, 0.06390593, 0.038343558, 0.017893661]
    tier1_load_curve = [0, 0, 0, 0, 0.012578616, 0.031446541, 0.037735849, 0.037735849, 0.037735849,
                        0.037735849, 0.037735849, 0.037735849, 0.037735849, 0.037735849, 0.037735849,
                        0.037735849, 0.044025157, 0.062893082, 0.100628931, 0.125786164, 0.110062893,
                        0.078616352, 0.044025157, 0.012578616]

    if tier == 1:
        load_curve = tier1_load_curve * 365
    elif tier == 2:
        load_curve = tier2_load_curve * 365
    elif tier == 3:
        load_curve = tier3_load_curve * 365
    elif tier == 4:
        load_curve = tier4_load_curve * 365
    else:
        load_curve = tier5_load_curve * 365

    return np.array(load_curve) * annual_demand / 365


# def get_pv_data(latitude, longitude, token, output_folder): # ToDo
#     # This function can be used to retrieve solar resource data from https://renewables.ninja
#     api_base = 'https://www.renewables.ninja/api/'
#     s = requests.session()
#     # Send token header with each request
#     s.headers = {'Authorization': 'Token ' + token}
#
#     out_path = os.path.join(output_folder, 'pv_data_lat_{}_long_{}.csv'.format(latitude, longitude))
#
#     url = api_base + 'data/pv'
#
#     args = {
#         'lat': latitude,
#         'lon': longitude,
#         'date_from': '2020-01-01',
#         'date_to': '2020-12-31',
#         'dataset': 'merra2',
#         'capacity': 1.0,
#         'system_loss': 0.1,
#         'tracking': 0,
#         'tilt': 35,
#         'azim': 180,
#         'format': 'json',
#         'local_time': True,
#         'raw': True
#     }
#
#     if token != '':
#
#         try:
#             r = s.get(url, params=args)
#
#             # Parse JSON to get a pandas.DataFrame of data and dict of metadata
#             parsed_response = json.loads(r.text)
#
#         except json.decoder.JSONDecodeError:
#             print('API maximum hourly requests reached, waiting one hour', time.ctime())
#             time.sleep(3700)
#             print('Wait over, resuming API requests', time.ctime())
#             r = s.get(url, params=args)
#
#             # Parse JSON to get a pandas.DataFrame of data and dict of metadata
#             parsed_response = json.loads(r.text)
#
#         data = pd.read_json(StringIO(json.dumps(parsed_response['data'])), orient='index')
#
#         df_out = pd.DataFrame(columns=['time', 'ghi', 'temp'])
#         df_out['ghi'] = (data['irradiance_direct'] + data['irradiance_diffuse']) * 1000
#         df_out['temp'] = data['temperature']
#         df_out['time'] = data['local_time']
#
#         df_out.to_csv(out_path, index=False)
#     else:
#         print('No token provided')


def read_wind_environmental_data(wind_path, skiprows=3, wind_col=3):
    """
        This method reads the wind resource (m/s) for each hour during one year from a csv-file.
        The skiprows and skipcolumns define which rows and columns the data should be read from.
    """
    try:
        wind_curve = pd.read_csv(wind_path, usecols=[wind_col], skiprows=skiprows).values
        return wind_curve
    except:
        print('Could not read data, try changing which columns and rows ro read')

