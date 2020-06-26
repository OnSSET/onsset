import numpy as np
from math import ceil
import pandas as pd


def pv_diesel_hybrid(
        energy_per_hh,  # kWh/household/year as defined
        ghi,  # highest annual GHI value encountered in the GIS data
        travel_hours,  # highest value for travel hours encountered in the GIS data
        tier,
        start_year,
        end_year,
        pv_no=15,  # number of PV panel sizes simulated
        diesel_no=15,  # number of diesel generators simulated
        diesel_price=0.7,
        diesel_truck_consumption=33.7,
        diesel_truck_volume=15000,
        discount_rate=0.08
):
    n_chg = 0.92  # charge efficiency of battery
    n_dis = 0.92  # discharge efficiency of battery
    lpsp = 0.05  # maximum loss of load allowed over the year, in share of kWh
    battery_cost = 150  # battery capital capital cost, USD/kWh of storage capacity
    pv_cost = 2490  # PV panel capital cost, USD/kW peak power
    diesel_cost = 550  # diesel generator capital cost, USD/kW rated power
    pv_life = 20  # PV panel expected lifetime, years
    diesel_life = 15  # diesel generator expected lifetime, years
    pv_om = 0.015  # annual OM cost of PV panels
    diesel_om = 0.1  # annual OM cost of diesel generator
    k_t = 0.005  # temperature factor of PV panels

    ghi = pd.read_csv('Supplementary_files\Benin_data.csv', usecols=[3], skiprows=341882).as_matrix()
    temp = pd.read_csv('Supplementary_files\Benin_data.csv', usecols=[2], skiprows=341882).as_matrix()
    
    hour_numbers = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23) * 365
    lhv_diesel = 9.9445485
    dod_max = 0.8  # maximum depth of discharge of battery

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

    load_curve = np.array(load_curve) * energy_per_hh / 365

    def pv_diesel_capacities(pv_capacity, battery_size, diesel_capacity, pv_no, diesel_no):
        ren_limit = 0.25
        break_hour = 17
        dod = np.zeros(shape=(24, pv_no, diesel_no))
        battery_use = np.zeros(shape=(24, pv_no, diesel_no))  # Stores the amount of battery discharge during the day
        fuel_result = np.zeros(shape=(pv_no, diesel_no))
        battery_life = np.zeros(shape=(pv_no, diesel_no))
        soc = np.ones(shape=(pv_no, diesel_no)) * 0.5
        unmet_demand = np.zeros(shape=(pv_no, diesel_no))
        annual_diesel_gen = np.zeros(shape=(pv_no, diesel_no))
        dod_max = np.ones(shape=(pv_no, diesel_no)) * 0.8

        for i in range(8760):
            battery_use[hour_numbers[i], :, :] = 0.0002 * soc  # Battery self-discharge
            soc *= 0.9998
            t_cell = temp[i] + 0.0256 * ghi[i]  # PV cell temperature
            pv_gen = pv_capacity * 0.9 * ghi[i] / 1000 * (1 - k_t * (t_cell - 25))  # PV generation in the hour
            net_load = load_curve[hour_numbers[i]] - pv_gen  # remaining load not met by PV panels

            if battery_size > 0:
                net_load_charge = np.where(net_load <= 0, 1, 0)
                soc -= (n_chg * net_load / battery_size) * net_load_charge
                net_load = net_load - net_load * net_load_charge  # REVIEW, NEEDED?

            max_diesel = np.where(net_load + (1 - soc) * battery_size / n_chg > diesel_capacity, diesel_capacity,
                                  net_load + (1 - soc) * battery_size / n_chg > diesel_capacity)
            #  Maximum amount of diesel needed to supply load and charge battery, limited by rated diesel capacity

            # Below is the dispatch strategy for the diesel generator as described in word document
            if break_hour + 1 > hour_numbers[i] > 4:  # and net_load > soc * battery_size * n_dis:
                diesel_gen_1 = np.where((net_load > soc * battery_size * n_dis) & (net_load > diesel_capacity),
                                        diesel_capacity, 0)
                diesel_gen_2 = np.where(
                    (net_load > soc * battery_size * n_dis) & (net_load < 0.4 * diesel_capacity),
                    0.4 * diesel_capacity, 0)
                diesel_gen_3 = np.where((net_load > soc * battery_size * n_dis) & (net_load < diesel_capacity) & (
                        net_load > 0.4 * diesel_capacity), net_load, 0)
                diesel_gen = diesel_gen_1 + diesel_gen_2 + diesel_gen_3
            elif 23 > hour_numbers[i] > break_hour:
                diesel_gen = np.where(max_diesel > 0.40 * diesel_capacity, max_diesel, 0)
            else:
                diesel_gen_1 = np.where(
                    (n_dis * soc * battery_size < net_load) & (0.4 * diesel_capacity > max_diesel),
                    0.4 * diesel_capacity, 0)
                diesel_gen_2 = np.where(
                    (n_dis * soc * battery_size < net_load) & (0.4 * diesel_capacity < max_diesel),
                    max_diesel, 0)
                diesel_gen = diesel_gen_1 + diesel_gen_2

            diesel_usage = np.where(diesel_gen > 0, 1, 0)
            fuel_result += diesel_usage * diesel_capacity * 0.08145 + diesel_gen * 0.246
            annual_diesel_gen += diesel_gen

            battery_discharge = np.where(net_load - diesel_gen > 0, 1, 0)
            battery_charge = np.where(net_load - diesel_gen < 0, 1, 0)

            if battery_size > 0:
                # If diesel generator cannot meet load the battery is also used
                battery_sufficient = np.where(soc > (net_load - diesel_gen) / n_dis / battery_size, 1, 0)
                battery_insufficient = np.where(soc > (net_load - diesel_gen) / n_dis / battery_size, 0, 1)
                soc -= battery_discharge * battery_sufficient * (net_load - diesel_gen) / n_dis / battery_size
                battery_use[hour_numbers[i], :, :] += \
                    (net_load - diesel_gen) / n_dis / battery_size * battery_discharge * battery_sufficient

                # If battery and diesel generator cannot supply load there is unmet demand
                unmet_demand += \
                    (net_load - diesel_gen - soc * n_dis * battery_size) * battery_discharge * battery_insufficient
                battery_use[hour_numbers[i], :, :] += battery_discharge * battery_insufficient * soc
                soc -= battery_discharge * battery_insufficient * soc

                # If diesel generation is larger than load the excess energy is stored in battery
                soc += ((diesel_gen - net_load) * n_chg / battery_size) * battery_charge

            if battery_size == 0:  # If no battery and diesel generation < net load there is unmet demand
                unmet_demand += (net_load - diesel_gen) * battery_discharge

            # Battery state of charge cannot be > 1
            soc = np.minimum(soc, 1)

            dod[hour_numbers[i], :, :] = 1 - soc  # The depth of discharge in every hour of the day is stored
            if hour_numbers[i] == 23:  # The battery wear during the last day is calculated
                battery_used = np.where(dod.max(axis=0) > 0, 1, 0)
                battery_life += battery_use.sum(axis=0) / (
                        531.52764 * np.maximum(0.1, dod.max(axis=0) * dod_max) ** -1.12297) * battery_used

        condition = unmet_demand / energy_per_hh  # lpsp is calculated

        valid_solution = np.where((condition < lpsp) & (annual_diesel_gen <= (1 - ren_limit) * energy_per_hh), 1, 0)
        invalid_solution = np.where(valid_solution == 1, 0, 1)

        battery_life = np.round(1 / battery_life)

        diesel_capacity += 99 * invalid_solution - diesel_capacity * invalid_solution
        battery_life -= battery_life * invalid_solution - invalid_solution

        return pv_capacity, diesel_capacity, battery_size, fuel_result, battery_life

    ref = 3 * load_curve[19]

    battery_sizes = [0.5 * energy_per_hh / 365, energy_per_hh / 365, 2 * energy_per_hh / 365]
    ref_battery_size = np.zeros((len(battery_sizes), pv_no, diesel_no))
    ref_panel_size = np.zeros((len(battery_sizes), pv_no, diesel_no))
    ref_diesel_cap = np.zeros((len(battery_sizes), pv_no, diesel_no))
    ref_fuel_result = np.zeros((len(battery_sizes), pv_no, diesel_no))
    ref_battery_life = np.zeros((len(battery_sizes), pv_no, diesel_no))

    pv_caps = []
    diesel_caps = []
    diesel_extend = np.ones(pv_no)
    pv_extend = np.ones(diesel_no)

    for i in range(pv_no):
        pv_caps.append(ref * (pv_no - i) / pv_no)

    for j in range(diesel_no):
        diesel_caps.append(j * max(load_curve) / diesel_no)

    pv_caps = np.outer(np.array(pv_caps), pv_extend)
    diesel_caps = np.outer(diesel_extend, np.array(diesel_caps))

    # For the number of diesel, pv and battery capacities the lpsp, battery lifetime and fuel usage is calculated
    for k in range(len(battery_sizes)):
        a = pv_diesel_capacities(pv_caps, battery_sizes[k], diesel_caps, pv_no, diesel_no)
        ref_panel_size[k, :, :] = pv_caps
        ref_diesel_cap[k, :, :] = a[1]
        ref_battery_size[k, :, :] = a[2]
        ref_fuel_result[k, :, :] = a[3]
        ref_battery_life[k, :, :] = a[4]  # Battery life limited to maximum 20 years

    # Necessary information for calculation of LCOE is defined
    project_life = end_year - start_year
    diesel_cost = diesel_price + 2 * diesel_price * diesel_truck_consumption * travel_hours / diesel_truck_volume / lhv_diesel
    generation = np.ones(project_life) * energy_per_hh
    generation[0] = 0
    year = np.arange(project_life)
    discount_factor = (1 + discount_rate) ** year

    # For each combination of GHI and diesel price the least costly configuration is calculated by iterating through
    # the different configurations specified above

    for k in range(pv_no):
        pv_size = ref_panel_size * ghi.sum() / 1000 / (1000 + 50 * k)
        for l in range(diesel_no):
            for m in range(len(battery_sizes)):
                investments = np.zeros(project_life)
                salvage = np.zeros(project_life)
                fuel_costs = np.ones(project_life) * ref_fuel_result[m, k, l] * (
                        diesel_price + 0.01 * j)
                investments[0] = pv_size[m, k, l] * pv_cost + ref_diesel_cap[m, k, l] * diesel_cost
                salvage[-1] = ref_diesel_cap[m, k, l] * diesel_cost * (1 - project_life / diesel_life) + \
                              pv_size[m, k, l] * pv_cost * (1 - project_life / pv_life)
                om = np.ones(project_life) * (
                        pv_size[m, k, l] * pv_cost * pv_om + ref_diesel_cap[m, k, l] * diesel_cost * diesel_om)
                if pv_life < project_life:
                    investments[pv_life] = pv_size[m, k, l] * pv_cost
                if diesel_life < project_life:
                    investments[diesel_life] = ref_diesel_cap[m, k, l] * diesel_cost
                for n in range(project_life):
                    if year[n] % ref_battery_life[m, k, l] == 0:
                        investments[n] += ref_battery_size[m, k, l] * battery_cost / dod_max
                salvage[-1] += (1 - ((project_life % ref_battery_life[m, k, l]) / ref_battery_life[m, k, l])) \
                               * battery_cost * ref_battery_size[m, k, l] / dod_max + ref_diesel_cap[m, k, l] * \
                               diesel_cost * (1 - (project_life % diesel_life) / diesel_life) \
                               + pv_size[m, k, l] * pv_cost * (1 - (project_life % pv_life) / pv_life)
                discount_investments = (investments + fuel_costs - salvage + om) / discount_factor
                discount_generation = generation / discount_factor
                lcoe = np.sum(discount_investments) / np.sum(discount_generation)
                if lcoe < lcoe_table[i, j]:
                    lcoe_table[i, j] = lcoe
                    pv_table[i, j] = pv_size[m, k, l]
                    diesel_table[i, j] = ref_diesel_cap[m, k, l]
                    investment_table[i, j] = np.sum(discount_investments)
                    choice_table[i, j] = (l + 1) * 10 + (k + 1) * 10000 + m + 1
                    # first number is PV size, second is diesel, third is battery
    return lcoe_table, pv_table, diesel_table, investment_table, load_curve[19], choice_table


lcoe_table, pv_table, diesel_table, investment_table, load_curve, choice_table = pv_diesel_hybrid(100, 2000, 10, 2, 2020, 2030)

1+1

