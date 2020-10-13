import numpy as np
from math import ceil
import pandas as pd

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

def result_arrays(pv_no, diesel_no):

    dod = np.zeros(shape=(24, pv_no, diesel_no))
    battery_use = np.zeros(shape=(24, pv_no, diesel_no))  # Stores the amount of battery discharge during the day
    fuel_result = np.zeros(shape=(pv_no, diesel_no))
    battery_life = np.zeros(shape=(pv_no, diesel_no))
    soc = np.ones(shape=(pv_no, diesel_no)) * 0.5
    unmet_demand = np.zeros(shape=(pv_no, diesel_no))
    annual_diesel_gen = np.zeros(shape=(pv_no, diesel_no))
    return dod, battery_use, fuel_result, battery_life, soc, unmet_demand, annual_diesel_gen


def hourly_load(tier, energy_per_hh):
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

def pv_net_load(ghi, temp, load, pv_capacity, k_t=0.005):
    ### Calculates the net load (load minus pv generation in every hour

    t_cell = temp + 0.0256 * ghi  # PV cell temperature
    pv_gen = pv_capacity * 0.9 * ghi / 1000 * (1 - k_t * (t_cell - 25))  # PV generation in the hour
    return load - pv_gen[0]  # remaining load not met by PV panels

def battery_and_diesel(battery_size, diesel_capacity, net_load, soc):
    net_load_charge = np.where(net_load <= 0, 1, 0)
    soc -= (n_chg * net_load / battery_size) * net_load_charge
    net_load = net_load - net_load * net_load_charge

###  IMPLEMENTATION

dod, battery_use, fuel_result, battery_life, soc, unmet_demand, annual_diesel_gen = result_arrays(5, 5)
test_load = hourly_load(1, 100)
test_net_load = pv_net_load(ghi, temp, test_load, 1)
1+1
