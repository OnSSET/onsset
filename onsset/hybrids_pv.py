import numpy as np
import logging
import pandas as pd
import os
import numba

logging.basicConfig(format='%(asctime)s\t\t%(message)s', level=logging.ERROR)


def read_environmental_data(path):
    # ghi_curve = pd.read_csv(path, usecols=[3], skiprows=341882)
    # temp = pd.read_csv(path, usecols=[2], skiprows=341882)

    ghi_curve = pd.read_csv(path, skiprows=341882)
    temp = pd.read_csv(path, skiprows=341882)

    ghi_curve = ghi_curve.iloc[:, 3].values
    temp = temp.iloc[:, 2].values

    # ghi_curve = pd.read_csv(path, usecols=[3], skiprows=3).values * 1000
    # temp = pd.read_csv(path, usecols=[5], skiprows=3).values
    return ghi_curve, temp


@numba.njit
def self_discharge(battery_use, soc):
    # Battery self-discharge (0.02% per hour)
    return battery_use + 0.0002 * soc, soc - 0.0002 * soc


@numba.njit
def pv_generation(temp, ghi, pv_capacity, load, inv_eff):
    # Calculation of PV gen and net load
    k_t = 0.005  # temperature factor of PV panels
    t_cell = temp + 0.0256 * ghi  # PV cell temperature
    pv_gen = pv_capacity * 0.9 * ghi / 1000 * (1 - k_t * (t_cell - 25))  # PV generation in the hour
    net_load = load - pv_gen * inv_eff  # remaining load not met by PV panels
    return net_load


@numba.njit
def diesel_dispatch(hour, net_load, diesel_capacity, fuel_result, annual_diesel_gen, soc, inv_eff, n_dis, n_chg, battery_size):
    # Below is the dispatch strategy for the diesel generator as described in word document

    battery_dispatchable = soc * battery_size * n_dis * inv_eff
    battery_chargeable = (1 - soc) * battery_size / n_chg / inv_eff

    if 4 < hour <= 17:
        # During the morning and day, the batteries are dispatched primarily.
        # The diesel generator, if needed, is run at the lowest possible capacity

        # Minimum diesel capacity to cover the net load after batteries.
        # Diesel generator limited by lowest possible capacity (40%) and rated capacity
        min_diesel = min(max(net_load - battery_dispatchable, 0.4 * diesel_capacity), diesel_capacity)

        if net_load > battery_dispatchable:
            diesel_gen = min_diesel
        else:
            diesel_gen = 0

    elif 17 > hour > 23:
        # During the evening, the diesel generator is dispatched primarily, at max_diesel.
        # Batteries are dispatched if diesel generation is insufficient.

        #  Maximum amount of diesel needed to supply load and charge battery
        # Diesel genrator limited by lowest possible capacity (40%) and rated capacity
        max_diesel = max(min(net_load + battery_chargeable, diesel_capacity), 0.4 * diesel_capacity)

        if net_load > 0:
            diesel_gen = max_diesel
        else:
            diesel_gen = 0

    else:
        # During night, batteries are dispatched primarily.
        # The diesel generator is used at max_diesel if load is larger than battery capacity

        #  Maximum amount of diesel needed to supply load and charge battery
        # Diesel genrator limited by lowest possible capacity (40%) and rated capacity
        max_diesel = max(min(net_load + battery_chargeable, diesel_capacity), 0.4 * diesel_capacity)

        if net_load > battery_dispatchable:
            diesel_gen = max_diesel
        else:
            diesel_gen = 0

    if diesel_gen > 0:
        fuel_result = fuel_result + diesel_capacity * 0.08145 + diesel_gen * 0.246
    else:
        fuel_result = 0

    # annual_diesel_gen = annual_diesel_gen + diesel_gen

    # Reamining load after diesel generator
    # net_load = net_load - diesel_gen

    return fuel_result, annual_diesel_gen + diesel_gen, diesel_gen, net_load - diesel_gen


@numba.njit
def soc_and_battery_usage(net_load, diesel_gen, n_dis, inv_eff, battery_size, n_chg, battery_use, soc, hour, dod):

    if net_load > 0:
        if diesel_gen > 0:
            # If diesel generation is used, but is smaller than load, battery is discharged
            soc = soc - net_load / n_dis / inv_eff / battery_size
        elif diesel_gen == 0:
            # If net load is positive and no diesel is used, battery is discharged
            soc = soc - net_load / n_dis / battery_size
    elif net_load < 0:
        if diesel_gen > 0:
            # If diesel generation is used, and is larger than load, battery is charged
            soc = soc - net_load * n_chg * inv_eff / battery_size
        if diesel_gen == 0:
            # If net load is negative, and no diesel has been used, excess PV gen is used to charge battery
            soc = soc - net_load * n_chg / battery_size

    # The amount of battery discharge in the hour is stored (measured in State Of Charge)
    if hour == 0:
        battery_use = 0
        dod = 0

    if net_load > 0:
        battery_use = battery_use + min(net_load / n_dis / battery_size, soc)
    else:
        battery_use = battery_use + min(0, soc)  # Unneccessary?

    return battery_use, soc, dod


@numba.njit
def unmet_demand_and_excess_gen(unmet_demand, soc, n_dis, battery_size, n_chg, excess_gen, dod,
                                hour, battery_life, dod_max, battery_use):

    if soc < 0:
        # If State of charge is negative, that means there's demand that could not be met.
        unmet_demand = unmet_demand - soc / n_dis * battery_size
        soc = 0

    if soc > 1:
        # If State of Charge is larger than 1, that means there was excess PV/diesel generation
        excess_gen = excess_gen + (soc - 1) / n_chg * battery_size
        soc = 1

    # If he depth of discharge in the hour is lower than...
    if 1 - soc > dod:
        dod = 1 - soc

    if hour == 23:  # The battery wear during the last day is calculated
        battery_life = battery_life + battery_use / (531.52764 * max(0.1, dod * dod_max) ** -1.12297)

    return unmet_demand, soc, excess_gen, dod,  battery_life


def pv_diesel_hybrid(
        energy_per_hh,  # kWh/household/year as defined
        ghi,
        ghi_curve,
        temp,
        tier,
        start_year,
        end_year,
        diesel_price,
        diesel_cost=261,  # diesel generator capital cost, USD/kW rated power
        pv_no=15,  # number of PV panel sizes simulated
        diesel_no=15,  # number of diesel generators simulated
        discount_rate=0.08
):
    n_chg = 0.92  # charge efficiency of battery
    n_dis = 0.92  # discharge efficiency of battery
    lpsp_max = 0.10  # maximum loss of load allowed over the year, in share of kWh
    battery_cost = 139  # battery capital capital cost, USD/kWh of storage capacity
    pv_cost = 503  # PV panel capital cost, USD/kW peak power
    pv_life = 25  # PV panel expected lifetime, years
    diesel_life = 10  # diesel generator expected lifetime, years
    pv_om = 0.015  # annual OM cost of PV panels
    diesel_om = 0.1  # annual OM cost of diesel generator
    inverter_cost = 80
    inverter_life = 10
    inv_eff = 0.92  # inverter_efficiency
    charge_controller = 142

    ghi = ghi_curve * ghi * 1000 / ghi_curve.sum()
    hour_numbers = np.array(
        (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23) * 365)
    dod_max = 0.8  # maximum depth of discharge of battery

    def load_curve(tier, energy_per_hh):
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

        return np.array(load_curve) * energy_per_hh / 365

    load_curve = load_curve(tier, energy_per_hh)

    @numba.njit
    def hourly_optimization(battery_size, diesel_capacity, net_load):
        fuel_result = 0
        battery_life = 0
        soc = 0.5
        unmet_demand = 0
        excess_gen = 0
        annual_diesel_gen = 0
        dod = 0
        battery_use = 0

        for hour in hour_numbers:

            load = net_load[hour]

            battery_use, soc = self_discharge(battery_use, soc)

            fuel_result, annual_diesel_gen, diesel_gen, load = diesel_dispatch(hour, load, diesel_capacity, fuel_result, annual_diesel_gen, soc, inv_eff, n_dis, n_chg, battery_size)

            battery_use, soc, dod = soc_and_battery_usage(load, diesel_gen, n_dis, inv_eff, battery_size, n_chg,
                                                     battery_use, soc, hour, dod)

            unmet_demand, soc, excess_gen, dod, battery_life = unmet_demand_and_excess_gen(unmet_demand, soc, n_dis,
                                                                                           battery_size, n_chg,
                                                                                           excess_gen, dod, hour,
                                                                                           battery_life, dod_max,
                                                                                           battery_use)

        condition = unmet_demand / energy_per_hh  # LPSP is calculated
        excess_gen = excess_gen / energy_per_hh
        battery_life = round(1 / battery_life)
        diesel_share = annual_diesel_gen / energy_per_hh

        return diesel_share, battery_life, condition, fuel_result, excess_gen

    # This section creates the range of PV capacities, diesel capacities and battery sizes to be simulated
    ref = 5 * load_curve[19]

    def diesel_range(x, max_steps):
        if x < 1000:
            return [1000]
        else:
            step = ceil(x / max_steps / 1000) * 1000
            return list(range(0, x + step, step))

    battery_sizes = [0.5 * energy_per_hh / 365, energy_per_hh / 365, 2 * energy_per_hh / 365]
    pv_caps = []
    for i in range(pv_no):
        pv_caps.append(ref * (pv_no - i) / pv_no)
    diesel_caps = diesel_range(max(load_curve), diesel_no)
    diesel_no = len(diesel_caps)

    diesel_extend = np.ones(pv_no)
    pv_extend = np.ones(len(diesel_caps))
    pv_extend = np.outer(np.array(pv_caps), pv_extend)
    diesel_extend = np.outer(diesel_extend, np.array(diesel_caps))

    # This section creates 2d-arrays to store information on PV capacities, diesel capacities, battery sizes,
    # fuel usage, battery life and LPSP

    battery_size = np.ones((len(battery_sizes), pv_no, diesel_no))
    pv_panel_size = np.zeros((len(battery_sizes), pv_no, diesel_no))
    diesel_capacity = np.zeros((len(battery_sizes), pv_no, diesel_no))

    for j in range(len(battery_sizes)):
        battery_size[j, :, :] *= battery_sizes[j]
        pv_panel_size[j, :, :] = pv_extend
        diesel_capacity[j, :, :] = diesel_extend

    battery_no = len(battery_sizes)
    battery_sizes = np.array(battery_sizes)

    diesel_share = np.zeros(shape=(battery_no, pv_no, diesel_no))
    battery_life = np.zeros(shape=(battery_no, pv_no, diesel_no))
    lpsp = np.zeros(shape=(battery_no, pv_no, diesel_no))
    fuel_usage = np.zeros(shape=(battery_no, pv_no, diesel_no))
    excess_gen = np.zeros(shape=(battery_no, pv_no, diesel_no))

    for pv in range(pv_no):
        pv_size = pv_caps[pv]
        net_load = pv_generation(temp, ghi, pv_size, load_curve, inv_eff)
        for battery in range(battery_no):
            battery_capacity = battery_sizes[battery]
            for diesel in range(diesel_no):
                diesel_size = diesel_caps[diesel]

                # For the number of diesel, pv and battery capacities the lpsp, battery lifetime, fuel usage and LPSP is calculated
                diesel_share[battery, pv, diesel], battery_life[battery, pv, diesel], lpsp[battery, pv, diesel], \
                fuel_usage[battery, pv, diesel], excess_gen[battery, pv, diesel] = \
                    hourly_optimization(battery_capacity, diesel_size, net_load)

    battery_life = np.minimum(20, battery_life)

    def calculate_hybrid_lcoe(diesel_price):
        # Necessary information for calculation of LCOE is defined
        project_life = end_year - start_year
        generation = np.ones(project_life) * energy_per_hh
        generation[0] = 0

        # Calculate LCOE
        sum_costs = np.zeros((len(battery_sizes), pv_no, diesel_no))
        sum_el_gen = np.zeros((len(battery_sizes), pv_no, diesel_no))
        investment = np.zeros((len(battery_sizes), pv_no, diesel_no))

        for year in range(project_life + 1):
            salvage = np.zeros((len(battery_sizes), pv_no, diesel_no))

            fuel_costs = fuel_usage * diesel_price
            om_costs = (pv_panel_size * (
                        pv_cost + charge_controller) * pv_om + diesel_capacity * diesel_cost * diesel_om)

            inverter_investment = np.where(year % inverter_life == 0, max(load_curve) * inverter_cost, 0)
            diesel_investment = np.where(year % diesel_life == 0, diesel_capacity * diesel_cost, 0)
            pv_investment = np.where(year % pv_life == 0, pv_panel_size * (pv_cost + charge_controller), 0)
            battery_investment = np.where(year % battery_life == 0, battery_size * battery_cost / dod_max,
                                          0)  # TODO Include dod_max here?

            if year == project_life:
                salvage = (1 - (project_life % battery_life) / battery_life) * battery_cost * battery_size / dod_max + \
                          (1 - (project_life % diesel_life) / diesel_life) * diesel_capacity * diesel_cost + \
                          (1 - (project_life % pv_life) / pv_life) * pv_panel_size * (pv_cost + charge_controller) + \
                          (1 - (project_life % inverter_life) / inverter_life) * max(load_curve) * inverter_cost

            investment += diesel_investment + pv_investment + battery_investment + inverter_investment - salvage

            sum_costs += (fuel_costs + om_costs + battery_investment + diesel_investment + pv_investment - salvage) / (
                        (1 + discount_rate) ** year)

            if year > 0:
                sum_el_gen += energy_per_hh / ((1 + discount_rate) ** year)

        return sum_costs / sum_el_gen, investment

    diesel_limit = 0.5

    min_lcoe_range = []
    investment_range = []
    capacity_range = []
    ren_share_range = []

    lcoe, investment = calculate_hybrid_lcoe(diesel_price)
    lcoe = np.where(lpsp > lpsp_max, 99, lcoe)
    lcoe = np.where(diesel_share > diesel_limit, 99, lcoe)

    min_lcoe = np.min(lcoe)
    min_lcoe_combination = np.unravel_index(np.argmin(lcoe, axis=None), lcoe.shape)
    ren_share = 1 - diesel_share[min_lcoe_combination]
    capacity = pv_panel_size[min_lcoe_combination] + diesel_capacity[min_lcoe_combination]
    ren_capacity = pv_panel_size[min_lcoe_combination] / capacity
    # excess_gen = excess_gen[min_lcoe_combination]

    min_lcoe_range.append(min_lcoe)
    investment_range.append(investment[min_lcoe_combination])
    capacity_range.append(capacity)
    ren_share_range.append(ren_share)

    return min_lcoe_range, investment_range, capacity_range, ren_share_range  # , ren_capacity, excess_gen
