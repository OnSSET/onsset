# Author: KTH dESA Last modified by Andreas Sahlberg
# Date: 05 June 2019
# Python version: 3.5

import os
import logging
import pandas as pd
from math import ceil, pi, exp, log, sqrt, radians, cos, sin, asin
# from pyproj import Proj
import numpy as np
from collections import defaultdict

# from IPython.display import Markdown

logging.basicConfig(format='%(asctime)s\t\t%(message)s', level=logging.DEBUG)

# General
LHV_DIESEL = 9.9445485  # (kWh/l) lower heating value
HOURS_PER_YEAR = 8760

# Columns in settlements file must match these exactly
SET_COUNTRY = 'Country'  # This cannot be changed, lots of code will break
SET_X = 'X'  # Coordinate in kilometres
SET_Y = 'Y'  # Coordinate in kilometres
SET_X_DEG = 'X_deg'  # Coordinates in degrees
SET_Y_DEG = 'Y_deg'
SET_POP = 'Pop'  # Population in people per point (equally, people per km2)
SET_POP_CALIB = 'PopStartYear'  # Calibrated population to reference year, same units
SET_POP_FUTURE = 'PopEndYear'  # Project future population, same units
SET_GRID_DIST_CURRENT = 'GridDistCurrent'  # Distance in km from current grid
SET_GRID_DIST_PLANNED = 'GridDistPlan'  # Distance in km from current and future grid
SET_ROAD_DIST = 'RoadDist'  # Distance in km from road network
SET_NIGHT_LIGHTS = 'NightLights'  # Intensity of night time lights (from NASA), range 0 - 63
SET_TRAVEL_HOURS = 'TravelHours'  # Travel time to large city in hours
SET_GHI = 'GHI'  # Global horizontal irradiance in kWh/m2/day
SET_WINDVEL = 'WindVel'  # Wind velocity in m/s
SET_WINDCF = 'WindCF'  # Wind capacity factor as percentage (range 0 - 1)
SET_HYDRO = 'Hydropower'  # Hydropower potential in kW
SET_HYDRO_DIST = 'HydropowerDist'  # Distance to hydropower site in km
SET_HYDRO_FID = 'HydropowerFID'  # the unique tag for eah hydropower, to not over-utilise
SET_SUBSTATION_DIST = 'SubstationDist'
SET_ELEVATION = 'Elevation'  # in metres
SET_SLOPE = 'Slope'  # in degrees
SET_LAND_COVER = 'LandCover'
SET_ROAD_DIST_CLASSIFIED = 'RoadDistClassified'
SET_SUBSTATION_DIST_CLASSIFIED = 'SubstationDistClassified'
SET_ELEVATION_CLASSIFIED = 'ElevationClassified'
SET_SLOPE_CLASSIFIED = 'SlopeClassified'
SET_LAND_COVER_CLASSIFIED = 'LandCoverClassified'
SET_COMBINED_CLASSIFICATION = 'GridClassification'
SET_GRID_PENALTY = 'GridPenalty'
SET_URBAN = 'IsUrban'  # Whether the site is urban (0 or 1)
SET_ENERGY_PER_CELL = 'EnergyPerSettlement'
SET_NUM_PEOPLE_PER_HH = 'NumPeoplePerHH'
SET_ELEC_CURRENT = 'ElecStart'  # If the site is currently electrified (0 or 1)
SET_ELEC_FUTURE = 'Elec_Status'  # If the site has the potential to be 'easily' electrified in future
SET_ELEC_FUTURE_GRID = "Elec_Initial_Status_Grid"
SET_ELEC_FUTURE_OFFGRID = "Elec_Init_Status_Offgrid"
SET_ELEC_FUTURE_ACTUAL = "Actual_Elec_Status_"
SET_ELEC_FINAL_GRID = "GridElecIn"
SET_ELEC_FINAL_OFFGRID = "OffGridElecIn"
SET_NEW_CONNECTIONS = 'NewConnections'  # Number of new people with electricity connections
SET_MIN_GRID_DIST = 'MinGridDist'
SET_LCOE_GRID = 'Grid'  # All lcoes in USD/kWh
SET_LCOE_SA_PV = 'SA_PV'
SET_LCOE_SA_DIESEL = 'SA_Diesel'
SET_LCOE_MG_WIND = 'MG_Wind'
SET_LCOE_MG_DIESEL = 'MG_Diesel'
SET_LCOE_MG_PV = 'MG_PV'
SET_LCOE_MG_HYDRO = 'MG_Hydro'
SET_LCOE_MG_HYBRID = 'MG_Hybrid'
SET_GRID_LCOE_Round1 = "Grid_lcoe_PreElec"
SET_MIN_OFFGRID = 'Minimum_Tech_Off_grid'  # The technology with lowest lcoe (excluding grid)
SET_MIN_OVERALL = 'MinimumOverall'  # Same as above, but including grid
SET_MIN_OFFGRID_LCOE = 'Minimum_LCOE_Off_grid'  # The lcoe value for minimum tech
SET_MIN_OVERALL_LCOE = 'MinimumOverallLCOE'  # The lcoe value for overall minimum
SET_MIN_OVERALL_CODE = 'MinimumOverallCode'  # And a code from 1 - 7 to represent that option
SET_MIN_CATEGORY = 'MinimumCategory'  # The category with minimum lcoe (grid, minigrid or standalone)
SET_NEW_CAPACITY = 'NewCapacity'  # Capacity in kW
SET_INVESTMENT_COST = 'InvestmentCost'  # The investment cost in USD
SET_INVESTMENT_COST_OFFGRID = "InvestmentOffGrid"
SET_CONFLICT = "Conflict"
SET_ELEC_ORDER = "ElectrificationOrder"
SET_DYNAMIC_ORDER = "Electrification_Wave"
SET_LIMIT = "ElecStatusIn"
SET_GRID_REACH_YEAR = "GridReachYear"
SET_MIN_OFFGRID_CODE = "Off_Grid_Code"
SET_ELEC_FINAL_CODE = "FinalElecCode"
SET_DIST_TO_TRANS = "TransformerDist"
SET_TOTAL_ENERGY_PER_CELL = "TotalEnergyPerCell"  # all previous + current timestep
SET_RESIDENTIAL_DEMAND = "ResidentialDemand"
SET_AGRI_DEMAND = 'AgriDemand'
SET_HEALTH_DEMAND = 'HealthDemand'
SET_EDU_DEMAND = 'EducationDemand'
SET_COMMERCIAL_DEMAND = 'CommercialDemand'
SET_GRID_CELL_AREA = 'GridCellArea'
SET_MV_CONNECT_DIST = 'MVConnectDist'
SET_HV_DIST_CURRENT = 'CurrentHVLineDist'
SET_HV_DIST_PLANNED = 'PlannedHVLineDist'
SET_MV_DIST_CURRENT = 'CurrentMVLineDist'
SET_MV_DIST_PLANNED = 'PlannedMVLineDist'
SET_ELEC_POP = 'ElecPop'
SET_ELEC_POP_CALIB = 'ElecPopCalib'
SET_WTFtier = "ResidentialDemandTier"
SET_TIER = 'Tier'
SET_INVEST_PER_CAPITA = "InvestmentCapita"
SET_CAP_MG_HYBRID = "Capacity_Hybrid"
SET_CALIB_GRID_DIST = 'GridDistCalibElec'
SET_CAPITA_DEMAND = 'PerCapitaDemand'
SET_RESIDENTIAL_TIER = 'ResidentialDemandTier'
SET_NTL_BIN = 'NTLBin'
SET_MIN_TD_DIST = 'minTDdist'

# Columns in the specs file must match these exactly
SPE_COUNTRY = 'Country'
SPE_POP = 'PopStartYear'  # The actual population in the base year
SPE_URBAN = 'UrbanRatioStartYear'  # The ratio of urban population (range 0 - 1) in base year
SPE_POP_FUTURE = 'PopEndYear'
SPE_URBAN_FUTURE = 'UrbanRatioEndYear'
SPE_URBAN_MODELLED = 'UrbanRatioModelled'  # The urban ratio in the model after calibration (for comparison)
SPE_URBAN_CUTOFF = 'UrbanCutOff'  # The urban cutoff population calirated by the model, in people per km2
SPE_URBAN_GROWTH = 'UrbanGrowth'  # The urban growth rate as a simple multplier (urban pop future / urban pop present)
SPE_RURAL_GROWTH = 'RuralGrowth'  # Same as for urban
SPE_NUM_PEOPLE_PER_HH_RURAL = 'NumPeoplePerHHRural'
SPE_NUM_PEOPLE_PER_HH_URBAN = 'NumPeoplePerHHUrban'
SPE_DIESEL_PRICE_LOW = 'DieselPriceLow'  # Diesel price in USD/litre
SPE_DIESEL_PRICE_HIGH = 'DieselPriceHigh'  # Same, with a high forecast var
SPE_GRID_PRICE = 'GridPrice'  # Grid price of electricity in USD/kWh
SPE_GRID_CAPACITY_INVESTMENT = 'GridCapacityInvestmentCost'  # grid capacity investments costs from TEMBA USD/kW
SPE_GRID_LOSSES = 'GridLosses'  # As a ratio (0 - 1)
SPE_BASE_TO_PEAK = 'BaseToPeak'  # As a ratio (0 - 1)
SPE_EXISTING_GRID_COST_RATIO = 'ExistingGridCostRatio'
SPE_MAX_GRID_DIST = 'MaxGridDist'
SPE_ELEC = 'ElecActual'  # Actual current percentage electrified population (0 - 1)
SPE_ELEC_MODELLED = 'ElecModelled'  # The modelled version after calibration (for comparison)
SPE_ELEC_URBAN = 'Urban_elec_ratio'  # Actual electrification for urban areas
SPE_ELEC_RURAL = 'Rural_elec_ratio'  # Actual electrification for rural areas
SPE_MIN_NIGHT_LIGHTS = 'MinNightLights'
SPE_MAX_GRID_EXTENSION_DIST = 'MaxGridExtensionDist'
SPE_MAX_ROAD_DIST = 'MaxRoadDist'
SPE_POP_CUTOFF1 = 'PopCutOffRoundOne'
SPE_POP_CUTOFF2 = 'PopCutOffRoundTwo'
SPE_ELEC_LIMIT = "ElecLimit"
SPE_INVEST_LIMIT = "InvestmentLimit"
SPE_DIST_TO_TRANS = "DistToTrans"

SPE_START_YEAR = "StartYear"
SPE_END_YEAR = "EndYEar"
SPE_TIMESTEP = "TimeStep"


class Technology:
    """
    Used to define the parameters for each electricity access technology, and to calculate the LCOE depending on
    input parameters.
    """

    def __init__(self,
                 tech_life,  # in years
                 base_to_peak_load_ratio,
                 distribution_losses=0,  # percentage
                 connection_cost_per_hh=0,  # USD/hh
                 om_costs=0.0,  # OM costs as percentage of capital costs
                 capital_cost=0,  # USD/kW
                 capacity_factor=0.9,  # percentage
                 grid_penalty_ratio=1,  # multiplier
                 efficiency=1.0,  # percentage
                 diesel_price=0.0,  # USD/litre
                 grid_price=0.0,  # USD/kWh for grid electricity
                 standalone=False,
                 existing_grid_cost_ratio=0.1,  # percentage
                 grid_capacity_investment=0.0,  # USD/kW for on-grid capacity investments (excluding grid itself)
                 diesel_truck_consumption=0,  # litres/hour
                 diesel_truck_volume=0,  # litres
                 om_of_td_lines=0):  # percentage

        self.distribution_losses = distribution_losses
        self.connection_cost_per_hh = connection_cost_per_hh
        self.base_to_peak_load_ratio = base_to_peak_load_ratio
        self.tech_life = tech_life
        self.om_costs = om_costs
        self.capital_cost = capital_cost
        self.capacity_factor = capacity_factor
        self.grid_penalty_ratio = grid_penalty_ratio
        self.efficiency = efficiency
        self.diesel_price = diesel_price
        self.grid_price = grid_price
        self.standalone = standalone
        self.existing_grid_cost_ratio = existing_grid_cost_ratio
        self.grid_capacity_investment = grid_capacity_investment
        self.diesel_truck_consumption = diesel_truck_consumption
        self.diesel_truck_volume = diesel_truck_volume
        self.om_of_td_lines = om_of_td_lines

    @classmethod
    def set_default_values(cls, base_year, start_year, end_year, discount_rate, HV_line_type=69, HV_line_cost=53000,
                           MV_line_type=33, MV_line_amperage_limit=8.0, MV_line_cost=7000, LV_line_type=0.240,
                           LV_line_cost=4250, LV_line_max_length=0.5, service_Transf_type=50, service_Transf_cost=4250,
                           max_nodes_per_serv_trans=300, MV_LV_sub_station_type=400, MV_LV_sub_station_cost=10000,
                           MV_MV_sub_station_cost=10000, HV_LV_sub_station_type=1000, HV_LV_sub_station_cost=25000,
                           HV_MV_sub_station_cost=25000, power_factor=0.9, load_moment=9643):
        cls.base_year = base_year
        cls.start_year = start_year
        cls.end_year = end_year

        # RUN_PARAM: Here are the assumptions related to cost and physical properties of grid extension elements
        # REVIEW - A final revision is needed before publishing
        cls.discount_rate = discount_rate
        cls.HV_line_type = HV_line_type  # kV
        cls.HV_line_cost = HV_line_cost  # $/km for 69kV
        cls.MV_line_type = MV_line_type  # kV
        cls.MV_line_amperage_limit = MV_line_amperage_limit  # Ampere (A)
        cls.MV_line_cost = MV_line_cost  # $/km  for 11-33 kV
        cls.LV_line_type = LV_line_type  # kV
        cls.LV_line_cost = LV_line_cost  # $/km
        cls.LV_line_max_length = LV_line_max_length  # km
        cls.service_Transf_type = service_Transf_type  # kVa
        cls.service_Transf_cost = service_Transf_cost  # $/unit
        cls.max_nodes_per_serv_trans = max_nodes_per_serv_trans  # maximum number of nodes served by each service transformer
        cls.MV_LV_sub_station_type = MV_LV_sub_station_type  # kVa
        cls.MV_LV_sub_station_cost = MV_LV_sub_station_cost  # $/unit
        cls.MV_MV_sub_station_cost = MV_MV_sub_station_cost  # $/unit
        cls.HV_LV_sub_station_type = HV_LV_sub_station_type  # kVa
        cls.HV_LV_sub_station_cost = HV_LV_sub_station_cost  # $/unit
        cls.HV_MV_sub_station_cost = HV_MV_sub_station_cost  # $/unit
        cls.power_factor = power_factor
        cls.load_moment = load_moment  # for 50mm aluminum conductor under 5% voltage drop (kW m)
        # simultaneous_usage = 0.06         # Not used eventually - maybe in an updated version

    def pv_diesel_hybrid(self, energy_per_hh,  # kWh/household/year as defined
                         max_ghi,  # highest annual GHI value encountered in the GIS data
                         max_travel_hours,  # highest value for travel hours encountered in the GIS data
                         tier,
                         start_year,
                         end_year,
                         pv_no=15,  # number of PV panel sizes simulated
                         diesel_no=15,  # number of diesel generators simulated
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
        if tier == 1:
            pass
            # logging.info('Preparing mg pv-diesel hybrid reference table')
        # ghi = pd.read_csv('Supplementary_files\GHI_hourly.csv', usecols=[4], sep=';', skiprows=21).as_matrix()
        ghi = np.ones(8760)
        ghi = ghi[:8760]
        # hourly GHI values downloaded from SoDa for one location in the country
        # temp = pd.read_csv('Supplementary_files\Temperature_hourly.csv', usecols=[4], sep=';', skiprows=21).as_matrix()
        temp = np.ones(8760)
        # hourly temperature values downloaded from SoDa for one location in the country
        hour_numbers = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23) * 365
        LHV_DIESEL = 9.9445485
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
            pv_length = len(pv_capacity)
            ren_limit = 0.25
            ren_limit_2 = 0.75
            break_hour = 17
            dod = np.zeros(shape=(24, pv_no, diesel_no))
            battery_use = np.zeros(
                shape=(24, pv_no, diesel_no))  # Stores the amount of battery discharge during the day
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
                pv_gen = pv_capacity * 0.9 * ghi[i] / 1000 * (1 - k_t * (t_cell - 298.15))  # PV generation in the hour
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
                    battery_use[hour_numbers[i], :, :] += (
                                                                  net_load - diesel_gen) / n_dis / battery_size * battery_discharge * battery_sufficient

                    # If battery and diesel generator cannot supply load there is unmet demand
                    unmet_demand += (
                                            net_load - diesel_gen - soc * n_dis * battery_size) * battery_discharge * battery_insufficient
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

            valid_solution = np.where((condition < lpsp) & (annual_diesel_gen <= (1 - ren_limit) * energy_per_hh) & (
                    annual_diesel_gen >= (1 - ren_limit_2) * energy_per_hh), 1, 0)
            invalid_solution = np.where(valid_solution == 1, 0, 1)

            battery_life = np.round(1 / battery_life)

            diesel_capacity += 99 * invalid_solution - diesel_capacity * invalid_solution
            battery_life -= battery_life * invalid_solution - invalid_solution

            return pv_capacity, diesel_capacity, battery_size, fuel_result, battery_life

        ref = 3 * load_curve[19]

        battery_sizes = [0, 0.5 * energy_per_hh / 365, energy_per_hh / 365, 2 * energy_per_hh / 365]
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
        ghi_steps = int(
            ceil((max_ghi - 1000) / 50) + 1)  # GHI values rounded to nearest 50 are used for reference matrix
        diesel_cost_max = 2 * self.diesel_price * self.diesel_truck_consumption * max_travel_hours / self.diesel_truck_volume / LHV_DIESEL
        diesel_steps = int(
            ceil(diesel_cost_max * 100) + 1)  # Diesel values rounded to 0.01 USD used for reference matrix
        generation = np.ones(project_life) * energy_per_hh
        generation[0] = 0
        year = np.arange(project_life)
        discount_factor = (1 + self.discount_rate) ** year
        investment_table = np.zeros((ghi_steps, diesel_steps))  # Stores least-cost configuration investments
        pv_table = np.zeros((ghi_steps, diesel_steps))  # Stores PV size for least-cost configuraton
        diesel_table = np.zeros((ghi_steps, diesel_steps))  # Stores diesel capacity for least-cost configuration
        lcoe_table = np.ones((ghi_steps, diesel_steps)) * 99  # Stores LCOE for least-cost configuration
        choice_table = np.zeros((ghi_steps, diesel_steps))

        # For each combination of GHI and diesel price the least costly configuration is calculated by iterating through
        # the different configurations specified above
        for i in range(ghi_steps):
            pv_size = ref_panel_size * ghi.sum() / 1000 / (1000 + 50 * i)
            for j in range(diesel_steps):
                for k in range(pv_no):
                    for l in range(diesel_no):
                        for m in range(len(battery_sizes)):
                            investments = np.zeros(project_life)
                            salvage = np.zeros(project_life)
                            fuel_costs = np.ones(project_life) * ref_fuel_result[m, k, l] * (
                                    self.diesel_price + 0.01 * j)
                            investments[0] = pv_size[m, k, l] * pv_cost + ref_diesel_cap[m, k, l] * diesel_cost
                            salvage[-1] = ref_diesel_cap[m, k, l] * diesel_cost * (1 - project_life / diesel_life) + \
                                          pv_size[m, k, l] * pv_cost * (1 - project_life / pv_life)
                            om = np.ones(project_life) * (
                                    pv_size[m, k, l] * pv_cost * pv_om + ref_diesel_cap[
                                m, k, l] * diesel_cost * diesel_om)
                            if pv_life < project_life:
                                investments[pv_life] = pv_size[m, k, l] * pv_cost
                            if diesel_life < project_life:
                                investments[diesel_life] = ref_diesel_cap[m, k, l] * diesel_cost
                            for n in range(project_life):
                                if year[n] % ref_battery_life[m, k, l] == 0:
                                    investments[n] += ref_battery_size[m, k, l] * battery_cost / dod_max
                            salvage[-1] += (1 - (
                                    (project_life % ref_battery_life[m, k, l]) / ref_battery_life[m, k, l])) * \
                                           battery_cost * ref_battery_size[m, k, l] / dod_max + ref_diesel_cap[
                                               m, k, l] * \
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

    def get_lcoe(self, energy_per_cell, people, num_people_per_hh, start_year, end_year, new_connections,
                 total_energy_per_cell, prev_code, grid_cell_area, conf_status=0, additional_mv_line_length=0,
                 capacity_factor=0,
                 grid_penalty_ratio=1, mv_line_length=0, travel_hours=0, elec_loop=0, productive_nodes=0,
                 additional_transformer=0, ghi=0, urban=0,
                 hybrid_1=0, hybrid_2=0, hybrid_3=0, hybrid_4=0, hybrid_5=0, tier=0,
                 get_investment_cost=False,
                 get_investment_cost_lv=False, get_investment_cost_mv=False, get_investment_cost_hv=False,
                 get_investment_cost_transformer=False, get_investment_cost_connection=False, mg_hybrid=False,
                 get_capacity=False):
        """
        Calculates the LCOE depending on the parameters. Optionally calculates the investment cost instead.

        The only required parameters are energy_per_cell, people and num_people_per_hh
        additional_mv_line_length required for grid
        capacity_factor required for PV and wind
        mv_line_length required for hydro
        travel_hours required for diesel
        """

        if people == 0:
            # If there are no people, the investment cost is zero.
            if get_investment_cost:
                return 0
            # Otherwise we set the people low (prevent div/0 error) and continue.
            else:
                people = 0.00001

        if energy_per_cell == 0:
            # If there is no demand, the investment cost is zero.
            if get_investment_cost:
                return 0
            # Otherwise we set the people low (prevent div/0 error) and continue.
            else:
                energy_per_cell = 0.000000000001

        if grid_cell_area <= 0:
            grid_cell_area = 0.001

        if grid_penalty_ratio == 0:
            grid_penalty_ratio = self.grid_penalty_ratio

        # If a new capacity factor isn't given, use the class capacity factor (for hydro, diesel etc)
        if capacity_factor == 0:
            capacity_factor = self.capacity_factor

        if mg_hybrid:
            if tier == 1:
                hybrid = hybrid_1
            elif tier == 2:
                hybrid = hybrid_2
            elif tier == 3:
                hybrid = hybrid_3
            elif tier == 4:
                hybrid = hybrid_4
            else:
                hybrid = hybrid_5

        def distribution_network(people, energy_per_cell):
            if energy_per_cell <= 0:
                energy_per_cell = 0.0001
            try:
                int(energy_per_cell)
            except ValueError:
                energy_per_cell = 0.0001

            if people <= 0:
                people = 0.0001

            consumption = energy_per_cell  # kWh/year
            average_load = consumption / (1 - self.distribution_losses) / HOURS_PER_YEAR  # kW

            # REVIEW
            if mg_hybrid:
                # peak_load = average_load / self.base_to_peak_load_ratio  # kW
                # peak_load = hybrid[4] * consumption
                peak_load = people / num_people_per_hh * hybrid[4] * (1 + self.distribution_losses)
            else:
                peak_load = average_load / self.base_to_peak_load_ratio  # kW

            try:
                int(peak_load)
            except ValueError:
                peak_load = 1

            # Sizing HV/MV
            HV_to_MV_lines = self.HV_line_cost / self.MV_line_cost
            max_MV_load = self.MV_line_amperage_limit * self.MV_line_type * HV_to_MV_lines

            MV_km = 0
            HV_km = 0
            if peak_load <= max_MV_load and additional_mv_line_length < 50 and self.grid_price > 0:
                MV_amperage = self.MV_LV_sub_station_type / self.MV_line_type
                No_of_MV_lines = ceil(peak_load / (MV_amperage * self.MV_line_type))
                MV_km = additional_mv_line_length * No_of_MV_lines
            elif self.grid_price > 0:
                HV_amperage = self.HV_LV_sub_station_type / self.HV_line_type
                No_of_HV_lines = ceil(peak_load / (HV_amperage * self.HV_line_type))
                HV_km = additional_mv_line_length * No_of_HV_lines

            Smax = peak_load / self.power_factor
            max_tranformer_area = pi * self.LV_line_max_length ** 2
            total_nodes = (people / num_people_per_hh) + productive_nodes

            try:
                no_of_service_transf = ceil(
                    max(Smax / self.service_Transf_type, total_nodes / self.max_nodes_per_serv_trans,
                        grid_cell_area / max_tranformer_area))
            except ValueError:
                no_of_service_transf = 1
            transformer_radius = ((grid_cell_area / no_of_service_transf) / pi) ** 0.5
            transformer_nodes = total_nodes / no_of_service_transf
            transformer_load = peak_load / no_of_service_transf
            cluster_radius = (grid_cell_area / pi) ** 0.5

            # Sizing LV lines in settlement
            if 2 / 3 * cluster_radius * transformer_load * 1000 < self.load_moment:
                cluster_lv_lines_length = 2 / 3 * cluster_radius * no_of_service_transf
                cluster_mv_lines_length = 0
            else:
                cluster_lv_lines_length = 0
                # cluster_mv_lines_length = 2 / 3 * cluster_radius * no_of_service_transf
                cluster_mv_lines_length = 2 * transformer_radius * no_of_service_transf

            hh_area = grid_cell_area / total_nodes
            hh_diameter = 2 * ((hh_area / pi) ** 0.5)

            transformer_lv_lines_length = hh_diameter * total_nodes
            No_of_HV_MV_subs = 0
            No_of_MV_MV_subs = 0
            No_of_HV_LV_subs = 0
            No_of_MV_LV_subs = 0
            No_of_HV_MV_subs += additional_transformer  # to connect the MV line to the HV grid

            if cluster_mv_lines_length > 0 and HV_km > 0:
                No_of_HV_MV_subs = ceil(peak_load / self.HV_LV_sub_station_type)  # 1
            elif cluster_mv_lines_length > 0 and MV_km > 0:
                No_of_MV_MV_subs = ceil(peak_load / self.MV_LV_sub_station_type)  # 1
            elif cluster_lv_lines_length > 0 and HV_km > 0:
                No_of_HV_LV_subs = ceil(peak_load / self.HV_LV_sub_station_type)  # 1
            else:
                No_of_MV_LV_subs = ceil(peak_load / self.MV_LV_sub_station_type)  # 1

            LV_km = cluster_lv_lines_length + transformer_lv_lines_length
            # MV_km += cluster_mv_lines_length  ### REVIEW

            return HV_km, MV_km, cluster_mv_lines_length, LV_km, no_of_service_transf, \
                   No_of_HV_MV_subs, No_of_MV_MV_subs, No_of_HV_LV_subs, No_of_MV_LV_subs, \
                   consumption, peak_load, total_nodes

        if people != new_connections and (prev_code == 1 or prev_code == 4 or prev_code == 5 or
                                          prev_code == 6 or prev_code == 7 or prev_code == 8):
            HV_km1, MV_km1, cluster_mv_lines_length1, cluster_lv_lines_length1, no_of_service_transf1, \
            No_of_HV_MV_subs1, No_of_MV_MV_subs1, No_of_HV_LV_subs1, No_of_MV_LV_subs1, \
            generation_per_year1, peak_load1, total_nodes1 = distribution_network(people, total_energy_per_cell)

            HV_km2, MV_km2, cluster_mv_lines_length2, cluster_lv_lines_length2, no_of_service_transf2, \
            No_of_HV_MV_subs2, No_of_MV_MV_subs2, No_of_HV_LV_subs2, No_of_MV_LV_subs2, \
            generation_per_year2, peak_load2, total_nodes2 = \
                distribution_network(people=(people - new_connections),
                                     energy_per_cell=(total_energy_per_cell - energy_per_cell))
            hv_lines_total_length = max(HV_km1 - HV_km2, 0)
            mv_lines_connection_length = max(MV_km1 - MV_km2, 0)
            mv_lines_distribution_length = max(cluster_lv_lines_length1 - cluster_lv_lines_length2, 0)
            total_lv_lines_length = max(cluster_lv_lines_length1 - cluster_lv_lines_length2, 0)
            num_transformers = max(no_of_service_transf1 - no_of_service_transf2, 0)
            generation_per_year = max(generation_per_year1 - generation_per_year2, 0)
            peak_load = max(peak_load1 - peak_load2, 0)
            No_of_HV_LV_substation = max(No_of_HV_LV_subs1 - No_of_HV_LV_subs2, 0)
            No_of_HV_MV_substation = max(No_of_HV_MV_subs1 - No_of_HV_MV_subs2, 0)
            No_of_MV_MV_substation = max(No_of_MV_MV_subs1 - No_of_MV_MV_subs2, 0)
            No_of_MV_LV_substation = max(No_of_MV_LV_subs1 - No_of_MV_LV_subs2, 0)
            total_nodes = max(total_nodes1 - total_nodes2, 0)
        else:
            hv_lines_total_length, mv_lines_connection_length, mv_lines_distribution_length, total_lv_lines_length, num_transformers, \
            No_of_HV_MV_substation, No_of_MV_MV_substation, No_of_HV_LV_substation, No_of_MV_LV_substation, \
            generation_per_year, peak_load, total_nodes = distribution_network(people, energy_per_cell)

        try:
            int(conf_status)
        except ValueError:
            conf_status = 0
        conf_grid_pen = {0: 1, 1: 1.1, 2: 1.25, 3: 1.5, 4: 2}
        # The investment and O&M costs are different for grid and non-grid solutions
        if self.grid_price > 0:
            td_investment_cost = (hv_lines_total_length * self.HV_line_cost * (
                    1 + self.existing_grid_cost_ratio * elec_loop) +
                                  mv_lines_connection_length * self.MV_line_cost * (
                                          1 + self.existing_grid_cost_ratio * elec_loop) +
                                  total_lv_lines_length * self.LV_line_cost +
                                  mv_lines_distribution_length * self.MV_line_cost +
                                  num_transformers * self.service_Transf_cost +
                                  total_nodes * self.connection_cost_per_hh +
                                  No_of_HV_LV_substation * self.HV_LV_sub_station_cost +
                                  No_of_HV_MV_substation * self.HV_MV_sub_station_cost +
                                  No_of_MV_MV_substation * self.MV_MV_sub_station_cost +
                                  No_of_MV_LV_substation * self.MV_LV_sub_station_cost) * conf_grid_pen[conf_status]
            td_investment_cost = td_investment_cost * grid_penalty_ratio
            td_om_cost = td_investment_cost * self.om_of_td_lines

            total_investment_cost = td_investment_cost
            total_om_cost = td_om_cost
            fuel_cost = self.grid_price  # / (1 - self.distribution_losses) REVIEW
        else:
            # TODO: Possibly add substation here for mini-grids
            conflict_sa_pen = {0: 1, 1: 1.03, 2: 1.07, 3: 1.125, 4: 1.25}
            conflict_mg_pen = {0: 1, 1: 1.05, 2: 1.125, 3: 1.25, 4: 1.5}
            total_lv_lines_length *= 0 if self.standalone else 1
            mv_lines_distribution_length *= 0 if self.standalone else 1
            mv_total_line_cost = self.MV_line_cost * mv_lines_distribution_length * conflict_mg_pen[conf_status]
            lv_total_line_cost = self.LV_line_cost * total_lv_lines_length * conflict_mg_pen[conf_status]
            service_transformer_total_cost = 0 if self.standalone else num_transformers * self.service_Transf_cost * \
                                                                       conflict_mg_pen[conf_status]
            installed_capacity = peak_load / capacity_factor
            td_investment_cost = mv_total_line_cost + lv_total_line_cost + total_nodes * self.connection_cost_per_hh + service_transformer_total_cost
            td_om_cost = td_investment_cost * self.om_of_td_lines * conflict_sa_pen[conf_status] if self.standalone \
                else td_investment_cost * self.om_of_td_lines * conflict_mg_pen[conf_status]

            if self.standalone and self.diesel_price == 0:
                if installed_capacity / (people / num_people_per_hh) < 0.020:
                    capital_investment = installed_capacity * self.capital_cost[0.020] * conflict_sa_pen[conf_status]
                    total_om_cost = td_om_cost + (self.capital_cost[0.020] * self.om_costs * conflict_sa_pen[
                        conf_status] * installed_capacity)
                elif installed_capacity / (people / num_people_per_hh) < 0.050:
                    capital_investment = installed_capacity * self.capital_cost[0.050] * conflict_sa_pen[conf_status]
                    total_om_cost = td_om_cost + (self.capital_cost[0.050] * self.om_costs * conflict_sa_pen[
                        conf_status] * installed_capacity)
                elif installed_capacity / (people / num_people_per_hh) < 0.100:
                    capital_investment = installed_capacity * self.capital_cost[0.100] * conflict_sa_pen[conf_status]
                    total_om_cost = td_om_cost + (self.capital_cost[0.100] * self.om_costs * conflict_sa_pen[
                        conf_status] * installed_capacity)
                elif installed_capacity / (people / num_people_per_hh) < 1:
                    capital_investment = installed_capacity * self.capital_cost[1] * conflict_sa_pen[conf_status]
                    total_om_cost = td_om_cost + (self.capital_cost[1] * self.om_costs * conflict_sa_pen[
                        conf_status] * installed_capacity)
                else:
                    capital_investment = installed_capacity * self.capital_cost[5] * conflict_sa_pen[conf_status]
                    total_om_cost = td_om_cost + (self.capital_cost[5] * self.om_costs * conflict_sa_pen[
                        conf_status] * installed_capacity)
            elif mg_hybrid:
                diesel_lookup = int(round(2 * self.diesel_price * self.diesel_truck_consumption *
                                          travel_hours / self.diesel_truck_volume / LHV_DIESEL * 100))
                renewable_lookup = int(round((ghi - 1000) / 50))

                ref_table = hybrid[0]
                ref_investments = hybrid[3]
                ref_capacity = hybrid[1] + hybrid[2]

                add_lcoe = ref_table[renewable_lookup, diesel_lookup]
                add_investments = ref_investments[renewable_lookup, diesel_lookup] * energy_per_cell
                add_capacity = ref_capacity[renewable_lookup, diesel_lookup] * energy_per_cell

                capital_investment = installed_capacity * self.capital_cost * conflict_sa_pen[conf_status]
                total_om_cost = td_om_cost  # + (add_investments * self.om_costs)  # * installed_capacity)
            else:
                capital_investment = installed_capacity * self.capital_cost * conflict_sa_pen[
                    conf_status] if self.standalone \
                    else installed_capacity * self.capital_cost * conflict_mg_pen[conf_status]
                total_om_cost = td_om_cost + (self.capital_cost * conflict_sa_pen[conf_status] * self.om_costs *
                                              installed_capacity) if self.standalone \
                    else td_om_cost + (
                        self.capital_cost * conflict_mg_pen[conf_status] * self.om_costs * installed_capacity)
            total_investment_cost = td_investment_cost + capital_investment

            # If a diesel price has been passed, the technology is diesel
            # And we apply the Szabo formula to calculate the transport cost for the diesel
            # p = (p_d + 2*p_d*consumption*time/volume)*(1/mu)*(1/LHVd)
            # Otherwise it's hydro/wind etc with no fuel cost
            conf_diesel_pen = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5}

            if self.diesel_price > 0:
                fuel_cost = (self.diesel_price + 2 * self.diesel_price * self.diesel_truck_consumption * (
                        travel_hours * conf_diesel_pen[conf_status]) /
                             self.diesel_truck_volume) / LHV_DIESEL / self.efficiency
            else:
                fuel_cost = 0

        # Perform the time-value LCOE calculation
        project_life = end_year - self.base_year + 1
        reinvest_year = 0
        step = start_year - self.base_year
        # If the technology life is less than the project life, we will have to invest twice to buy it again
        if self.tech_life + step < project_life:
            reinvest_year = self.tech_life + step

        year = np.arange(project_life)
        el_gen = generation_per_year * np.ones(project_life)
        el_gen[0:step] = 0
        discount_factor = (1 + self.discount_rate) ** year
        investments = np.zeros(project_life)
        investments[step] = total_investment_cost

        # Calculate the year of re-investment if tech_life is smaller than project life
        if reinvest_year:
            investments[reinvest_year] = total_investment_cost

        # Calculate salvage value if tech_life is bigger than project life
        salvage = np.zeros(project_life)
        if reinvest_year > 0:
            used_life = (project_life - step) - self.tech_life
        else:
            used_life = project_life - step - 1
        salvage[-1] = total_investment_cost * (1 - used_life / self.tech_life)
        operation_and_maintenance = total_om_cost * np.ones(project_life)
        operation_and_maintenance[0:step] = 0
        fuel = el_gen * fuel_cost
        fuel[0:step] = 0

        # So we also return the total investment cost for this number of people
        if get_investment_cost:
            discounted_investments = investments / discount_factor
            if mg_hybrid:
                return add_investments + np.sum(discounted_investments)
            else:
                return np.sum(discounted_investments) + self.grid_capacity_investment * peak_load / discount_factor[step]
        elif get_investment_cost_lv:
            return total_lv_lines_length * (self.LV_line_cost * conf_grid_pen[conf_status])
        elif get_investment_cost_mv:
            return (mv_lines_connection_length * self.MV_line_cost * (1 + self.existing_grid_cost_ratio * elec_loop) +
                    mv_lines_distribution_length * self.MV_line_cost) * conf_grid_pen[conf_status]
        elif get_investment_cost_hv:
            return hv_lines_total_length * (self.HV_line_cost * conf_grid_pen[conf_status]) * \
                   (1 + self.existing_grid_cost_ratio * elec_loop)
        elif get_investment_cost_transformer:
            return (No_of_HV_LV_substation * self.HV_LV_sub_station_cost +
                    No_of_HV_MV_substation * self.HV_MV_sub_station_cost +
                    No_of_MV_MV_substation * self.MV_MV_sub_station_cost +
                    No_of_MV_LV_substation * self.MV_LV_sub_station_cost) * conf_grid_pen[conf_status]
        elif get_investment_cost_connection:
            return total_nodes * self.connection_cost_per_hh
        elif get_capacity:
            return add_capacity
        else:
            discounted_costs = (investments + operation_and_maintenance + fuel - salvage) / discount_factor
            discounted_generation = el_gen / discount_factor
            if mg_hybrid:
                return (np.sum(discounted_costs) / np.sum(discounted_generation) + add_lcoe)
            else:
                return np.sum(discounted_costs) / np.sum(discounted_generation)


class SettlementProcessor:
    """
    Processes the dataframe and adds all the columns to determine the cheapest option and the final costs and summaries
    """
    def __init__(self, path):
        try:
            self.df = pd.read_csv(path)
        except FileNotFoundError:
            print("Please make sure that the country name you provided and the .csv file, both have the same name")
            raise

        try:
            self.df[SET_GHI]
        except KeyError:
            self.df = pd.read_csv(path, sep=';')
            try:
                self.df[SET_GHI]
            except ValueError:
                print('Column "GHI" not found, check column names in calibrated csv-file')
                raise

    def condition_df(self):
        """
        Do any initial data conditioning that may be required.
        """

        logging.info('Ensure that columns that are supposed to be numeric are numeric')
        self.df[SET_GHI] = pd.to_numeric(self.df[SET_GHI], errors='coerce')
        self.df[SET_WINDVEL] = pd.to_numeric(self.df[SET_WINDVEL], errors='coerce')
        self.df[SET_NIGHT_LIGHTS] = pd.to_numeric(self.df[SET_NIGHT_LIGHTS], errors='coerce')
        self.df[SET_ELEVATION] = pd.to_numeric(self.df[SET_ELEVATION], errors='coerce')
        self.df[SET_SLOPE] = pd.to_numeric(self.df[SET_SLOPE], errors='coerce')
        self.df[SET_LAND_COVER] = pd.to_numeric(self.df[SET_LAND_COVER], errors='coerce')
        self.df[SET_SUBSTATION_DIST] = pd.to_numeric(self.df[SET_SUBSTATION_DIST], errors='coerce')
        self.df[SET_ROAD_DIST] = pd.to_numeric(self.df[SET_ROAD_DIST], errors='coerce')
        self.df[SET_HYDRO_DIST] = pd.to_numeric(self.df[SET_HYDRO_DIST], errors='coerce')
        self.df[SET_HYDRO] = pd.to_numeric(self.df[SET_HYDRO], errors='coerce')
        self.df[SET_ELEC_POP] = pd.to_numeric(self.df[SET_ELEC_POP], errors='coerce')
        self.df.loc[self.df[SET_ELEC_POP] > self.df[SET_POP], SET_ELEC_POP] = self.df[SET_POP]

        logging.info('Adding column "ElectrificationOrder"')
        self.df[SET_ELEC_ORDER] = 0

        logging.info('Replace null values with zero')
        self.df.fillna(0, inplace=True)

        logging.info('Sort by country, Y and X')
        self.df.sort_values(by=[SET_Y_DEG, SET_X_DEG], inplace=True)

    def grid_penalties(self):
        """
        Add a grid penalty factor to increase the grid cost in areas that higher road distance, higher substation
        distance, unsuitable land cover, high slope angle or high elevation
        """

        def classify_road_dist(row):
            road_dist = row[SET_ROAD_DIST]
            if road_dist <= 5:
                return 5
            elif road_dist <= 10:
                return 4
            elif road_dist <= 25:
                return 3
            elif road_dist <= 50:
                return 2
            else:
                return 1

        def classify_substation_dist(row):
            substation_dist = row[SET_SUBSTATION_DIST]
            if substation_dist <= 0.5:
                return 5
            elif substation_dist <= 1:
                return 4
            elif substation_dist <= 5:
                return 3
            elif substation_dist <= 10:
                return 2
            else:
                return 1

        def classify_land_cover(row):
            land_cover = row[SET_LAND_COVER]
            if land_cover == 0:
                return 1
            elif land_cover == 1:
                return 3
            elif land_cover == 2:
                return 4
            elif land_cover == 3:
                return 3
            elif land_cover == 4:
                return 4
            elif land_cover == 5:
                return 3
            elif land_cover == 6:
                return 2
            elif land_cover == 7:
                return 5
            elif land_cover == 8:
                return 2
            elif land_cover == 9:
                return 5
            elif land_cover == 10:
                return 5
            elif land_cover == 11:
                return 1
            elif land_cover == 12:
                return 3
            elif land_cover == 13:
                return 3
            elif land_cover == 14:
                return 5
            elif land_cover == 15:
                return 3
            elif land_cover == 16:
                return 5

        def classify_elevation(row):
            elevation = row[SET_ELEVATION]
            if elevation <= 500:
                return 5
            elif elevation <= 1000:
                return 4
            elif elevation <= 2000:
                return 3
            elif elevation <= 3000:
                return 2
            else:
                return 1

        def classify_slope(row):
            slope = row[SET_SLOPE]
            if slope <= 10:
                return 5
            elif slope <= 20:
                return 4
            elif slope <= 30:
                return 3
            elif slope <= 40:
                return 2
            else:
                return 1

        def set_penalty(row):
            classification = row[SET_COMBINED_CLASSIFICATION]
            return 1 + (exp(0.85 * abs(1 - classification)) - 1) / 100

        logging.info('Classify road dist')
        self.df[SET_ROAD_DIST_CLASSIFIED] = self.df.apply(classify_road_dist, axis=1)

        logging.info('Classify substation dist')
        self.df[SET_SUBSTATION_DIST_CLASSIFIED] = self.df.apply(classify_substation_dist, axis=1)

        logging.info('Classify land cover')
        self.df[SET_LAND_COVER_CLASSIFIED] = self.df.apply(classify_land_cover, axis=1)

        logging.info('Classify elevation')
        self.df[SET_ELEVATION_CLASSIFIED] = self.df.apply(classify_elevation, axis=1)

        logging.info('Classify slope')
        self.df[SET_SLOPE_CLASSIFIED] = self.df.apply(classify_slope, axis=1)

        logging.info('Combined classification')
        self.df[SET_COMBINED_CLASSIFICATION] = (0.15 * self.df[SET_ROAD_DIST_CLASSIFIED] +
                                                0.20 * self.df[SET_SUBSTATION_DIST_CLASSIFIED] +
                                                0.20 * self.df[SET_LAND_COVER_CLASSIFIED] +
                                                0.15 * self.df[SET_ELEVATION_CLASSIFIED] +
                                                0.30 * self.df[SET_SLOPE_CLASSIFIED])

        logging.info('Grid penalty')
        self.df[SET_GRID_PENALTY] = self.df.apply(set_penalty, axis=1)

    def calc_wind_cfs(self):
        """
        Calculate the wind capacity factor based on the average wind velocity.
        """

        mu = 0.97  # availability factor
        t = 8760
        p_rated = 600
        z = 55  # hub height
        zr = 80  # velocity measurement height
        es = 0.85  # losses in wind electricity
        u_arr = range(1, 26)
        p_curve = [0, 0, 0, 0, 30, 77, 135, 208, 287, 371, 450, 514, 558,
                   582, 594, 598, 600, 600, 600, 600, 600, 600, 600, 600, 600]

        def get_wind_cf(row):
            u_zr = row[SET_WINDVEL]
            if u_zr == 0:
                return 0

            else:
                # Adjust for the correct hub height
                alpha = (0.37 - 0.088 * log(u_zr)) / (1 - 0.088 * log(zr / 10))
                u_z = u_zr * (z / zr) ** alpha

                # Rayleigh distribution and sum of series
                rayleigh = [(pi / 2) * (u / u_z ** 2) * exp((-pi / 4) * (u / u_z) ** 2) for u in u_arr]
                energy_produced = sum([mu * es * t * p * r for p, r in zip(p_curve, rayleigh)])

                return energy_produced / (p_rated * t)

        logging.info('Calculate Wind CF')
        self.df[SET_WINDCF] = self.df.apply(get_wind_cf, axis=1)

    def prepare_wtf_tier_columns(self, num_people_per_hh_rural, num_people_per_hh_urban,
                                 tier_1, tier_2, tier_3, tier_4, tier_5):
        """ Prepares the five Residential Demand Tier Targets based customized for each country
        """
        # The MTF approach is given as per yearly household consumption (BEYOND CONNECTIONS Energy Access Redefined, ESMAP, 2015). Tiers in kWh/capita/year depends on the average ppl/hh which is different in every country
        logging.info('Populate ResidentialDemandTier columns')
        tier_num = [1, 2, 3, 4, 5]
        ppl_hh_average = (num_people_per_hh_urban + num_people_per_hh_rural) / 2
        tier_1 = tier_1 / ppl_hh_average  # 38.7 refers to kWh/household/year. It is the mean value between Tier 1 and Tier 2
        tier_2 = tier_2 / ppl_hh_average
        tier_3 = tier_3 / ppl_hh_average
        tier_4 = tier_4 / ppl_hh_average
        tier_5 = tier_5 / ppl_hh_average

        wb_tiers_all = {1: tier_1, 2: tier_2, 3: tier_3, 4: tier_4, 5: tier_5}

        for num in tier_num:
            self.df[SET_WTFtier + "{}".format(num)] = wb_tiers_all[num]

    def calibrate_pop_and_urban(self, pop_actual, pop_future_high, pop_future_low, urban_current, urban_future,
                                start_year, end_year, intermediate_year):
        """
        Calibrate the actual current population, the urban split and forecast the future population
        """

        logging.info('Calibrate current population')
        project_life = end_year - start_year
        # Calculate the ratio between the actual population and the total population from the GIS layer
        pop_ratio = pop_actual / self.df[SET_POP].sum()
        # And use this ratio to calibrate the population in a new column
        self.df[SET_POP_CALIB] = self.df.apply(lambda row: row[SET_POP] * pop_ratio, axis=1)
        self.df[SET_ELEC_POP_CALIB] = self.df[SET_ELEC_POP] * pop_ratio
        if max(self.df[SET_URBAN]) == 3:  # THIS OPTION IS CURRENTLY DISABLED
            calibrate = True if 'n' in input(
                'Use urban definition from GIS layer <y/n> (n=model calibration):') else False
        else:
            calibrate = True
        # RUN_PARAM: This is where manual calibration of urban/rural population takes place.
        # The model uses 0, 1, 2 as GHS population layer does.
        # As of this version, urban are only rows with value equal to 2
        if calibrate:
            urban_modelled = 2
            factor = 1
            while abs(urban_modelled - urban_current) > 0.01:
                self.df[SET_URBAN] = 0
                self.df.loc[(self.df[SET_POP_CALIB] > 5000 * factor) & (
                        self.df[SET_POP_CALIB] / self.df[SET_GRID_CELL_AREA] > 350 * factor), SET_URBAN] = 1
                self.df.loc[(self.df[SET_POP_CALIB] > 50000 * factor) & (
                        self.df[SET_POP_CALIB] / self.df[SET_GRID_CELL_AREA] > 1500 * factor), SET_URBAN] = 2
                pop_urb = self.df.loc[self.df[SET_URBAN] > 1, SET_POP_CALIB].sum()
                urban_modelled = pop_urb / pop_actual
                if urban_modelled > urban_current:
                    factor *= 1.1
                else:
                    factor *= 0.9

        # Get the calculated urban ratio, and limit it to within reasonable boundaries
        pop_urb = self.df.loc[self.df[SET_URBAN] > 1, SET_POP_CALIB].sum()
        urban_modelled = pop_urb / pop_actual

        if abs(urban_modelled - urban_current) > 0.01:
            print('The modelled urban ratio is {:.2f}. '
                  'In case this is not acceptable please revise this part of the code'.format(urban_modelled))

        # Project future population, with separate growth rates for urban and rural
        logging.info('Project future population')

        if calibrate:
            urban_growth_high = (urban_future * pop_future_high) / (urban_modelled * pop_actual)
            rural_growth_high = ((1 - urban_future) * pop_future_high) / ((1 - urban_modelled) * pop_actual)

            yearly_urban_growth_rate_high = urban_growth_high ** (1 / project_life)
            yearly_rural_growth_rate_high = rural_growth_high ** (1 / project_life)

            urban_growth_low = (urban_future * pop_future_low) / (urban_modelled * pop_actual)
            rural_growth_low = ((1 - urban_future) * pop_future_low) / ((1 - urban_modelled) * pop_actual)

            yearly_urban_growth_rate_low = urban_growth_low ** (1 / project_life)
            yearly_rural_growth_rate_low = rural_growth_low ** (1 / project_life)
        else:
            urban_growth_high = pop_future_high / pop_actual
            rural_growth_high = pop_future_high / pop_actual

            yearly_urban_growth_rate_high = urban_growth_high ** (1 / project_life)
            yearly_rural_growth_rate_high = rural_growth_high ** (1 / project_life)

            urban_growth_low = pop_future_low / pop_actual
            rural_growth_low = pop_future_low / pop_actual

            yearly_urban_growth_rate_low = urban_growth_low ** (1 / project_life)
            yearly_rural_growth_rate_low = rural_growth_low ** (1 / project_life)

        # RUN_PARAM: Define here the years for which results should be provided in the output file.
        yearsofanalysis = [intermediate_year, end_year]

        for year in yearsofanalysis:
            self.df[SET_POP + "{}".format(year) + 'High'] = self.df.apply(lambda row: row[SET_POP_CALIB] *
                                                                                      (yearly_urban_growth_rate_high **
                                                                                       (year - start_year))
            if row[SET_URBAN] > 1
            else row[SET_POP_CALIB] *
                 (yearly_rural_growth_rate_high ** (year - start_year)), axis=1)

            self.df[SET_POP + "{}".format(year) + 'Low'] = self.df.apply(lambda row: row[SET_POP_CALIB] *
                                                                                     (yearly_urban_growth_rate_low **
                                                                                      (year - start_year))
            if row[SET_URBAN] > 1
            else row[SET_POP_CALIB] *
                 (yearly_rural_growth_rate_low ** (year - start_year)), axis=1)

        self.df[SET_POP + "{}".format(start_year)] = self.df.apply(lambda row: row[SET_POP_CALIB], axis=1)

        return urban_modelled

    def elec_current_and_future(self, elec_actual, elec_actual_urban, elec_actual_rural, pop_tot, start_year,
                                min_night_lights=0, min_pop=50, max_transformer_dist=2, max_mv_dist=2, max_hv_dist=5):
        """
        Calibrate the current electrification status, and future 'pre-electrification' status
        """

        # REVIEW: The way this works now, for all urban or rural settlements that fit the conditioning, the population SET_ELEC_POP is reduced by equal amount so that we match urban/rural national statistics respectively.
        # TODO We might need to update with off-grid electrified in future versions
        urban_pop = (self.df.loc[self.df[SET_URBAN] > 1, SET_POP_CALIB].sum())  # Calibrate current electrification
        rural_pop = (self.df.loc[self.df[SET_URBAN] <= 1, SET_POP_CALIB].sum())  # Calibrate current electrification
        total_pop = self.df[SET_POP_CALIB].sum()
        total_elec_ratio = elec_actual
        urban_elec_ratio = elec_actual_urban
        rural_elec_ratio = elec_actual_rural
        factor = (total_pop * total_elec_ratio) / (urban_pop * urban_elec_ratio + rural_pop * rural_elec_ratio)
        urban_elec_ratio *= factor
        rural_elec_ratio *= factor
        self.df.loc[self.df[SET_NIGHT_LIGHTS] <= 0, [SET_ELEC_POP_CALIB]] = 0

        logging.info('Calibrate current electrification')
        self.df[SET_ELEC_CURRENT] = 0

        # This if function here skims through T&D columns to identify if any non 0 values exist; Then it defines priority accordingly.
        if max(self.df[SET_DIST_TO_TRANS]) > 0:
            self.df[SET_CALIB_GRID_DIST] = self.df[SET_DIST_TO_TRANS]
            priority = 1
            dist_limit = max_transformer_dist
        elif max(self.df[SET_MV_DIST_CURRENT]) > 0:
            self.df[SET_CALIB_GRID_DIST] = self.df[SET_MV_DIST_CURRENT]
            priority = 1
            dist_limit = max_mv_dist
        else:
            self.df[SET_CALIB_GRID_DIST] = self.df[SET_HV_DIST_CURRENT]
            priority = 2

        condition = 0

        while condition == 0:
            # Assign the 1 (electrified)/0 (un-electrified) values to each cell
            urban_electrified = urban_pop * urban_elec_ratio
            rural_electrified = rural_pop * rural_elec_ratio
            # RUN_PARAM: Calibration parameters if MV lines or transformer location is available
            if priority == 1:
                print(
                    'We have identified the existence of transformers or MV lines as input data; therefore we proceed using those for the calibration')
                self.df.loc[
                    (self.df[SET_CALIB_GRID_DIST] < dist_limit) & (self.df[SET_NIGHT_LIGHTS] > min_night_lights) & (
                            self.df[SET_POP_CALIB] > min_pop), SET_ELEC_CURRENT] = 1
                urban_elec_modelled = self.df.loc[
                    (self.df[SET_ELEC_CURRENT] == 1) & (self.df[SET_URBAN] > 1), SET_ELEC_POP_CALIB].sum()
                rural_elec_modelled = self.df.loc[
                    (self.df[SET_ELEC_CURRENT] == 1) & (self.df[SET_URBAN] <= 1), SET_ELEC_POP_CALIB].sum()
                urban_elec_factor = urban_elec_modelled / urban_electrified
                rural_elec_factor = rural_elec_modelled / rural_electrified
                if urban_elec_factor > 1:
                    self.df.loc[(self.df[SET_ELEC_CURRENT] == 1) & (self.df[SET_URBAN] > 1), SET_ELEC_POP_CALIB] *= (
                            1 / urban_elec_factor)
                else:
                    i = 0
                    print(
                        "The urban settlements identified as electrified are lower than in statistics; Please re-adjust the calibration conditions")
                    while urban_elec_factor <= 1:
                        if i < 10:
                            self.df.loc[
                                (self.df[SET_ELEC_CURRENT] == 1) & (self.df[SET_URBAN] == 2), SET_ELEC_POP_CALIB] *= 1.1
                            self.df[SET_ELEC_POP_CALIB] = np.minimum(self.df[SET_ELEC_POP_CALIB],
                                                                     self.df[SET_POP_CALIB])
                            urban_elec_modelled = self.df.loc[
                                (self.df[SET_ELEC_CURRENT] == 1) & (self.df[SET_URBAN] == 2), SET_ELEC_POP_CALIB].sum()
                            urban_elec_factor = urban_elec_modelled / urban_electrified
                            i += 1
                        else:
                            break

                if rural_elec_factor > 1:
                    self.df.loc[(self.df[SET_ELEC_CURRENT] == 1) & (self.df[SET_URBAN] <= 1), SET_ELEC_POP_CALIB] *= (
                            1 / rural_elec_factor)
                else:
                    i = 0
                    print(
                        "The rural settlements identified as electrified are lower than in statistics; Please re-adjust the calibration conditions")
                    while rural_elec_factor <= 1:
                        if i < 10:
                            self.df.loc[
                                (self.df[SET_ELEC_CURRENT] == 1) & (self.df[SET_URBAN] < 2), SET_ELEC_POP_CALIB] *= 1.1
                            self.df[SET_ELEC_POP_CALIB] = np.minimum(self.df[SET_ELEC_POP_CALIB],
                                                                     self.df[SET_POP_CALIB])
                            rural_elec_modelled = self.df.loc[
                                (self.df[SET_ELEC_CURRENT] == 1) & (self.df[SET_URBAN] < 2), SET_ELEC_POP_CALIB].sum()
                            rural_elec_factor = rural_elec_modelled / rural_electrified
                            i += 1
                        else:
                            break

                pop_elec = self.df.loc[self.df[SET_ELEC_CURRENT] == 1, SET_ELEC_POP_CALIB].sum()
                elec_modelled = pop_elec / total_pop

                # REVIEW. Added new calibration step for pop not meeting original steps, if prev elec pop is too small
                i = 0
                td_dist_2 = 0.1
                while elec_actual - elec_modelled > 0.01:
                    if i < 50:
                        pop_elec_2 = self.df.loc[(self.df[SET_ELEC_CURRENT] == 0) & (self.df[SET_POP_CALIB] > min_pop) &
                                                 (self.df[SET_CALIB_GRID_DIST] < td_dist_2), SET_POP_CALIB].sum()
                        if (pop_elec + pop_elec_2) / total_pop > elec_actual:
                            elec_modelled = (pop_elec + pop_elec_2) / total_pop
                            self.df.loc[(self.df[SET_ELEC_CURRENT] == 0) & (self.df[SET_POP_CALIB] > min_pop) &
                                        (self.df[SET_CALIB_GRID_DIST] < td_dist_2), SET_ELEC_POP_CALIB] = self.df[
                                SET_POP_CALIB]
                            self.df.loc[(self.df[SET_ELEC_CURRENT] == 0) & (self.df[SET_POP_CALIB] > min_pop) &
                                        (self.df[SET_CALIB_GRID_DIST] < td_dist_2), SET_ELEC_CURRENT] = 1
                        else:
                            i += 1
                            td_dist_2 += 0.1
                    else:
                        self.df.loc[(self.df[SET_ELEC_CURRENT] == 0) & (self.df[SET_POP_CALIB] > min_pop) &
                                    (self.df[SET_CALIB_GRID_DIST] < td_dist_2), SET_ELEC_POP_CALIB] = self.df[
                            SET_POP_CALIB]
                        self.df.loc[(self.df[SET_ELEC_CURRENT] == 0) & (self.df[SET_POP_CALIB] > min_pop) &
                                    (self.df[SET_CALIB_GRID_DIST] < td_dist_2), SET_ELEC_CURRENT] = 1
                        elec_modelled = (pop_elec + pop_elec_2) / total_pop
                        break

                if elec_modelled > elec_actual:
                    self.df[SET_ELEC_POP_CALIB] *= elec_actual / elec_modelled
                pop_elec = self.df.loc[self.df[SET_ELEC_CURRENT] == 1, SET_ELEC_POP_CALIB].sum()
                elec_modelled = pop_elec / total_pop

            # RUN_PARAM: Calibration parameters if only HV lines are available
            else:
                print(
                    'No transformers or MV lines were identified as input data; therefore we proceed to the calibration with HV line info')
                self.df.loc[
                    (self.df[SET_CALIB_GRID_DIST] < max_hv_dist) & (self.df[SET_NIGHT_LIGHTS] > min_night_lights) & (
                            self.df[SET_POP_CALIB] > min_pop), SET_ELEC_CURRENT] = 1

                urban_elec_modelled = self.df.loc[
                    (self.df[SET_ELEC_CURRENT] == 1) & (self.df[SET_URBAN] > 1), SET_ELEC_POP_CALIB].sum()
                rural_elec_modelled = self.df.loc[
                    (self.df[SET_ELEC_CURRENT] == 1) & (self.df[SET_URBAN] <= 1), SET_ELEC_POP_CALIB].sum()
                urban_elec_factor = urban_elec_modelled / urban_electrified
                rural_elec_factor = rural_elec_modelled / rural_electrified

                if urban_elec_factor > 1:
                    self.df.loc[(self.df[SET_ELEC_CURRENT] == 1) & (self.df[SET_URBAN] > 1), SET_ELEC_POP_CALIB] *= (
                            1 / urban_elec_factor)
                else:
                    print(
                        "The urban settlements identified as electrified are lower than in statistics; Please re-adjust the calibration conditions")

                if rural_elec_factor > 1:
                    self.df.loc[(self.df[SET_ELEC_CURRENT] == 1) & (self.df[SET_URBAN] <= 1), SET_ELEC_POP_CALIB] *= (
                            1 / rural_elec_factor)
                else:
                    print(
                        "The rural settlements identified as electrified are lower than in statistics; Please re-adjust the calibration conditions")

                pop_elec = self.df.loc[self.df[SET_ELEC_CURRENT] == 1, SET_ELEC_POP_CALIB].sum()
                elec_modelled = pop_elec / total_pop

                # REVIEW. Added new calibration step for pop not meeting original steps, if prev elec pop is too small
                i = 0
                td_dist_2 = 0.1
                while elec_actual - elec_modelled > 0.01:
                    if i < 50:
                        pop_elec_2 = self.df.loc[(self.df[SET_ELEC_CURRENT] == 0) & (self.df[SET_POP_CALIB] > min_pop) &
                                                 (self.df[SET_CALIB_GRID_DIST] < td_dist_2), SET_POP_CALIB].sum()
                        if (pop_elec + pop_elec_2) / total_pop > elec_actual:
                            elec_modelled = (pop_elec + pop_elec_2) / total_pop
                            self.df.loc[(self.df[SET_ELEC_CURRENT] == 0) & (self.df[SET_POP_CALIB] > min_pop) &
                                        (self.df[SET_CALIB_GRID_DIST] < td_dist_2), SET_ELEC_POP_CALIB] = self.df[
                                SET_POP_CALIB]
                            self.df.loc[(self.df[SET_ELEC_CURRENT] == 0) & (self.df[SET_POP_CALIB] > min_pop) &
                                        (self.df[SET_CALIB_GRID_DIST] < td_dist_2), SET_ELEC_CURRENT] = 1
                        else:
                            i += 1
                            td_dist_2 += 0.1
                    else:
                        self.df.loc[(self.df[SET_ELEC_CURRENT] == 0) & (self.df[SET_POP_CALIB] > min_pop) &
                                    (self.df[SET_CALIB_GRID_DIST] < td_dist_2), SET_ELEC_POP_CALIB] = self.df[
                            SET_POP_CALIB]
                        self.df.loc[(self.df[SET_ELEC_CURRENT] == 0) & (self.df[SET_POP_CALIB] > min_pop) &
                                    (self.df[SET_CALIB_GRID_DIST] < td_dist_2), SET_ELEC_CURRENT] = 1
                        elec_modelled = (pop_elec + pop_elec_2) / total_pop
                        break

                if elec_modelled > elec_actual:
                    self.df[SET_ELEC_POP_CALIB] *= elec_actual / elec_modelled
                pop_elec = self.df.loc[self.df[SET_ELEC_CURRENT] == 1, SET_ELEC_POP_CALIB].sum()
                elec_modelled = pop_elec / total_pop

            urban_elec_ratio = self.df.loc[(self.df[SET_ELEC_CURRENT] == 1) & (
                    self.df[SET_URBAN] > 1), SET_ELEC_POP_CALIB].sum() / urban_pop
            rural_elec_ratio = self.df.loc[(self.df[SET_ELEC_CURRENT] == 1) & (
                    self.df[SET_URBAN] <= 1), SET_ELEC_POP_CALIB].sum() / rural_pop

            print('The modelled electrification rate achieved is {0:.2f}.'
                  'Urban elec. rate is {1:.2f} and Rural elec. rate is {2:.2f}. \n'
                  'If this is not acceptable please revise this part of the algorithm'.format(elec_modelled-elec_actual,
                                                                                              urban_elec_ratio-elec_actual_urban,
                                                                                              rural_elec_ratio-elec_actual_rural))
            condition = 1

        self.df[SET_ELEC_FUTURE_GRID + "{}".format(start_year)] = \
            self.df.apply(lambda row: 1 if row[SET_ELEC_CURRENT] == 1 else 0, axis=1)
        self.df[SET_ELEC_FUTURE_OFFGRID + "{}".format(start_year)] = self.df.apply(lambda row: 0, axis=1)
        self.df[SET_ELEC_FUTURE_ACTUAL + "{}".format(start_year)] = \
            self.df.apply(lambda row: 1 if row[SET_ELEC_FUTURE_GRID + "{}".format(start_year)] == 1 or
                                           row[SET_ELEC_FUTURE_OFFGRID + "{}".format(start_year)] == 1 else 0, axis=1)
        self.df[SET_ELEC_FINAL_CODE + "{}".format(start_year)] = \
            self.df.apply(lambda row: 1 if row[SET_ELEC_CURRENT] == 1 else 99, axis=1)

        return elec_modelled, rural_elec_ratio, urban_elec_ratio

    @staticmethod
    def separate_elec_status(elec_status):
        """
        Separate out the electrified and unelectrified states from list.
        """

        electrified = []
        unelectrified = []

        for i, status in enumerate(elec_status):
            if status:
                electrified.append(i)
            else:
                unelectrified.append(i)
        return electrified, unelectrified

    @staticmethod
    def get_2d_hash_table(x, y, unelectrified, distance_limit):
        """
        Generates the 2D Hash Table with the unelectrified locations hashed into the table for easy O(1) access.
        """

        hash_table = defaultdict(lambda: defaultdict(list))
        for unelec_row in unelectrified:
            hash_x = int(x[unelec_row] / distance_limit)
            hash_y = int(y[unelec_row] / distance_limit)
            hash_table[hash_x][hash_y].append(unelec_row)
        return hash_table

    @staticmethod
    def get_unelectrified_rows(hash_table, elec_row, x, y, distance_limit):
        """
        Returns all the unelectrified locations close to the electrified location
        based on the distance boundary limit specified by asking the 2D hash table.
        """

        unelec_list = []
        hash_x = int(x[elec_row] / distance_limit)
        hash_y = int(y[elec_row] / distance_limit)

        unelec_list.extend(hash_table.get(hash_x, {}).get(hash_y, []))
        unelec_list.extend(hash_table.get(hash_x, {}).get(hash_y - 1, []))
        unelec_list.extend(hash_table.get(hash_x, {}).get(hash_y + 1, []))

        unelec_list.extend(hash_table.get(hash_x + 1, {}).get(hash_y, []))
        unelec_list.extend(hash_table.get(hash_x + 1, {}).get(hash_y - 1, []))
        unelec_list.extend(hash_table.get(hash_x + 1, {}).get(hash_y + 1, []))

        unelec_list.extend(hash_table.get(hash_x - 1, {}).get(hash_y, []))
        unelec_list.extend(hash_table.get(hash_x - 1, {}).get(hash_y - 1, []))
        unelec_list.extend(hash_table.get(hash_x - 1, {}).get(hash_y + 1, []))

        return unelec_list

    def pre_electrification(self, grid_calc, grid_price, year, time_step, start_year):

        """" ... """

        logging.info('Define the initial electrification status')

        # Update electrification status based on already existing
        if (year - time_step) == start_year:
            self.df[SET_ELEC_FUTURE_GRID + "{}".format(year)] = 0
            self.df.loc[
                self.df[SET_ELEC_FUTURE_GRID + "{}".format(year - time_step)] == 1, SET_ELEC_FUTURE_GRID + "{}".format(
                    year)] = 1
        else:
            self.df[SET_ELEC_FUTURE_GRID + "{}".format(year)] = 0
            self.df.loc[
                self.df[SET_ELEC_FUTURE_GRID + "{}".format(year - time_step)] == 1, SET_ELEC_FUTURE_GRID + "{}".format(
                    year)] = 1
            self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 1) & (
                    self.df[SET_LIMIT + "{}".format(year - time_step)] == 1), SET_ELEC_FUTURE_GRID + "{}".format(
                year)] = 1

        if (year - time_step) == start_year:
            self.df[SET_ELEC_FUTURE_OFFGRID + "{}".format(year)] = 0
            self.df.loc[self.df[SET_ELEC_FUTURE_OFFGRID + "{}".format(
                year - time_step)] == 1, SET_ELEC_FUTURE_OFFGRID + "{}".format(year)] = 1
        else:
            self.df[SET_ELEC_FUTURE_OFFGRID + "{}".format(year)] = 0
            self.df.loc[(self.df[SET_ELEC_FUTURE_OFFGRID + "{}".format(year - time_step)] == 1) &
                        (self.df[SET_ELEC_FUTURE_GRID + "{}".format(year - time_step)] != 1),
                        SET_ELEC_FUTURE_OFFGRID + "{}".format(year)] = 1
            self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] != 1) & (
                    self.df[SET_LIMIT + "{}".format(year - time_step)] == 1), SET_ELEC_FUTURE_OFFGRID + "{}".format(
                year)] = 1

        if (year - time_step) == start_year:
            self.df[SET_ELEC_FUTURE_ACTUAL + "{}".format(year)] = 0
            self.df.loc[self.df[SET_ELEC_FUTURE_ACTUAL + "{}".format(
                year - time_step)] == 1, SET_ELEC_FUTURE_ACTUAL + "{}".format(year)] = 1
        else:
            self.df[SET_ELEC_FUTURE_ACTUAL + "{}".format(year)] = 0
            self.df.loc[self.df[SET_ELEC_FUTURE_ACTUAL + "{}".format(
                year - time_step)] == 1, SET_ELEC_FUTURE_ACTUAL + "{}".format(year)] = 1
            self.df.loc[self.df[SET_ELEC_FUTURE_GRID + "{}".format(
                year - time_step)] == 1, SET_ELEC_FUTURE_ACTUAL + "{}".format(year)] = 1
            self.df.loc[self.df[SET_ELEC_FUTURE_OFFGRID + "{}".format(
                year - time_step)] == 1, SET_ELEC_FUTURE_ACTUAL + "{}".format(year)] = 1

        self.df[SET_LCOE_GRID + "{}".format(year)] = 99
        self.df.loc[
            self.df[SET_ELEC_FUTURE_GRID + "{}".format(year)] == 1, SET_LCOE_GRID + "{}".format(year)] = grid_price

    def current_mv_line_dist(self):
        logging.info('Determine current MV line length')
        self.df[SET_MV_CONNECT_DIST] = 0
        self.df.loc[self.df[SET_ELEC_CURRENT] == 1, SET_MV_CONNECT_DIST] = self.df[SET_HV_DIST_CURRENT]
        self.df[SET_MIN_TD_DIST] = self.df[[SET_MV_DIST_PLANNED, SET_HV_DIST_PLANNED]].min(axis=1)

    def elec_extension(self, grid_calc, max_dist, year, start_year, end_year, timestep, grid_cap_gen_limit,
                       grid_connect_limit, auto_intensification=0, prioritization=0):
        """
        Iterate through all electrified settlements and find which settlements can be economically connected to the grid
        Repeat with newly electrified settlements until no more are added
        """
        prio = int(prioritization)
        new_grid_capacity = 0
        grid_capacity_limit = grid_cap_gen_limit
        x = (self.df[SET_X_DEG]).tolist()
        y = (self.df[SET_Y_DEG]).tolist()
        pop = self.df[SET_POP + "{}".format(year)].tolist()
        confl = self.df[SET_CONFLICT].tolist()
        travl = self.df[SET_TRAVEL_HOURS].tolist()
        enerperhh = self.df[SET_ENERGY_PER_CELL + "{}".format(year)]
        nupppphh = self.df[SET_NUM_PEOPLE_PER_HH]
        grid_cell_area = self.df[SET_GRID_CELL_AREA]
        prev_code = self.df[SET_ELEC_FINAL_CODE + "{}".format(year - timestep)]
        new_connections = self.df[SET_NEW_CONNECTIONS + "{}".format(year)]
        total_energy_per_cell = self.df[SET_TOTAL_ENERGY_PER_CELL]
        if year - timestep == start_year:
            elecorder = self.df[SET_ELEC_ORDER].tolist()
        else:
            elecorder = self.df[SET_ELEC_ORDER + "{}".format(year - timestep)].tolist()
        grid_penalty_ratio = self.df[SET_GRID_PENALTY].tolist()
        status = self.df[SET_ELEC_FUTURE_GRID + "{}".format(year)].tolist()
        min_code_lcoes = self.df[SET_MIN_OFFGRID_LCOE + "{}".format(year)].tolist()
        new_lcoes = self.df[SET_LCOE_GRID + "{}".format(year)].tolist()
        grid_reach = self.df[SET_GRID_REACH_YEAR].tolist()
        cell_path_real = self.df[SET_MV_CONNECT_DIST].tolist()
        planned_hv_dist = self.df[SET_HV_DIST_PLANNED].tolist()  # If connecting from anywhere on the HV line
        planned_mv_dist = self.df[SET_MV_DIST_PLANNED].tolist()  # If connecting from anywhere on the HV line
        self.df['new_connections_household'] = self.df[SET_NEW_CONNECTIONS + "{}".format(year)] / self.df[
            SET_NUM_PEOPLE_PER_HH]

        urban_initially_electrified = sum(self.df.loc[
                                              (self.df[SET_ELEC_FUTURE_GRID + "{}".format(year - timestep)] == 1) & (
                                                      self.df[SET_URBAN] == 2)][
                                              SET_ENERGY_PER_CELL + "{}".format(year)])
        rural_initially_electrified = sum(self.df.loc[
                                              (self.df[SET_ELEC_FUTURE_GRID + "{}".format(year - timestep)] == 1) & (
                                                      self.df[SET_URBAN] < 2)][
                                              SET_ENERGY_PER_CELL + "{}".format(year)])
        densification_connections = sum(
            self.df.loc[self.df[SET_ELEC_FUTURE_GRID + "{}".format(year - timestep)] == 1]['new_connections_household'])
        consumption = rural_initially_electrified + urban_initially_electrified
        average_load = consumption / (1 - grid_calc.distribution_losses) / HOURS_PER_YEAR  # kW
        peak_load = average_load / grid_calc.base_to_peak_load_ratio  # kW
        grid_capacity_limit -= peak_load
        grid_connect_limit -= densification_connections

        cell_path_adjusted = list(np.zeros(len(status)).tolist())
        electrified, unelectrified = self.separate_elec_status(status)

        if (prio == 2) or (prio == 4):
            changes = []
            for unelec in unelectrified:
                try:
                    if planned_mv_dist[unelec] < auto_intensification:
                        consumption = enerperhh[unelec]  # kWh/year
                        average_load = consumption / (1 - grid_calc.distribution_losses) / HOURS_PER_YEAR  # kW
                        peak_load = average_load / grid_calc.base_to_peak_load_ratio  # kW
                        dist = planned_mv_dist[unelec]
                        dist_adjusted = grid_penalty_ratio[unelec] * dist

                        grid_lcoe = 0.001

                        new_lcoes[unelec] = grid_lcoe
                        cell_path_real[unelec] = dist
                        cell_path_adjusted[unelec] = dist_adjusted
                        new_grid_capacity += peak_load
                        grid_connect_limit -= new_connections[unelec] / nupppphh[unelec]
                        elecorder[unelec] = 0
                        changes.append(unelec)
                except KeyError:
                    pass

            electrified.extend(changes[:])
            unelectrified = set(unelectrified).difference(electrified)

        filtered_unelectrified = []
        for unelec in unelectrified:
            try:
                grid_lcoe = grid_calc.get_lcoe(energy_per_cell=enerperhh[unelec],
                                               start_year=year - timestep,
                                               end_year=end_year,
                                               people=pop[unelec],
                                               new_connections=new_connections[unelec],
                                               total_energy_per_cell=total_energy_per_cell[unelec],
                                               prev_code=prev_code[unelec],
                                               num_people_per_hh=nupppphh[unelec],
                                               grid_cell_area=grid_cell_area[unelec],
                                               conf_status=confl[unelec],
                                               travel_hours=travl[unelec],
                                               additional_mv_line_length=0,
                                               elec_loop=0)
                if grid_lcoe < min_code_lcoes[unelec]:
                    filtered_unelectrified.append(unelec)
            except KeyError:
                pass
        unelectrified = filtered_unelectrified

        close = []
        elec_nodes2 = []
        changes = []
        for elec in electrified:
            elec_nodes2.append((x[elec], y[elec]))

        def haversine(lon1, lat1, lon2, lat2):
            """
            Calculate the great circle distance between two points
            on the earth (specified in decimal degrees)
            """
            # convert decimal degrees to radians
            lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

            # haversine formula
            dlon = lon2 - lon1
            dlat = lat2 - lat1
            a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
            c = 2 * asin(sqrt(a))
            r = 6371  # Radius of earth in kilometers. Use 3956 for miles
            return c * r

        def closest_elec(unelec_node, elec_nodes):
            deltas = elec_nodes - unelec_node
            dist_2 = np.einsum('ij,ij->i', deltas, deltas)
            min_dist = np.argmin(dist_2)
            return min_dist

        logging.info('Initially {} electrified'.format(len(electrified)))
        loops = 1

        # First round of extension from MV network
        for unelec in unelectrified:
            if year >= grid_reach[unelec]:
                consumption = enerperhh[unelec]  # kWh/year
                average_load = consumption / (1 - grid_calc.distribution_losses) / HOURS_PER_YEAR  # kW
                peak_load = average_load / grid_calc.base_to_peak_load_ratio  # kW
                dist = planned_mv_dist[unelec]
                dist_adjusted = grid_penalty_ratio[unelec] * dist
                if dist_adjusted <= max_dist:
                    grid_lcoe = grid_calc.get_lcoe(energy_per_cell=enerperhh[unelec],
                                                   start_year=year - timestep,
                                                   end_year=end_year,
                                                   people=pop[unelec],
                                                   new_connections=new_connections[unelec],
                                                   total_energy_per_cell=total_energy_per_cell[unelec],
                                                   prev_code=prev_code[unelec],
                                                   num_people_per_hh=nupppphh[unelec],
                                                   grid_cell_area=grid_cell_area[unelec],
                                                   conf_status=confl[unelec],
                                                   travel_hours=travl[unelec],
                                                   additional_mv_line_length=dist_adjusted,
                                                   elec_loop=0)

                    if grid_lcoe < min_code_lcoes[unelec]:
                        if (grid_lcoe < new_lcoes[unelec]) and (new_grid_capacity + peak_load < grid_capacity_limit) \
                                and (new_connections[unelec] / nupppphh[unelec] < grid_connect_limit):
                            new_lcoes[unelec] = grid_lcoe
                            cell_path_real[unelec] = dist
                            cell_path_adjusted[unelec] = dist_adjusted
                            new_grid_capacity += peak_load
                            grid_connect_limit -= new_connections[unelec] / nupppphh[unelec]
                            elecorder[unelec] = 1
                            if unelec not in changes:
                                changes.append(unelec)
                        else:
                            close.append(unelec)
                    else:
                        close.append(unelec)
                else:
                    close.append(unelec)
        electrified = changes[:]
        unelectrified = close

        #  Extension from HV lines
        for unelec in unelectrified:
            if year >= grid_reach[unelec]:
                consumption = enerperhh[unelec]  # kWh/year
                average_load = consumption / (1 - grid_calc.distribution_losses) / HOURS_PER_YEAR  # kW
                peak_load = average_load / grid_calc.base_to_peak_load_ratio  # kW
                dist = planned_hv_dist[unelec]
                dist_adjusted = grid_penalty_ratio[unelec] * dist
                if dist <= max_dist:
                    elec_loop_value = 0
                    grid_lcoe = grid_calc.get_lcoe(energy_per_cell=enerperhh[unelec],
                                                   start_year=year - timestep,
                                                   end_year=end_year,
                                                   people=pop[unelec],
                                                   new_connections=new_connections[unelec],
                                                   total_energy_per_cell=total_energy_per_cell[unelec],
                                                   prev_code=prev_code[unelec],
                                                   num_people_per_hh=nupppphh[unelec],
                                                   grid_cell_area=grid_cell_area[unelec],
                                                   conf_status=confl[unelec],
                                                   travel_hours=travl[unelec],
                                                   additional_mv_line_length=dist_adjusted,
                                                   elec_loop=elec_loop_value,
                                                   additional_transformer=1)
                    if (grid_lcoe < min_code_lcoes[unelec]) and (new_grid_capacity + peak_load < grid_capacity_limit) \
                            and (new_connections[unelec] / nupppphh[unelec] < grid_connect_limit):
                        new_lcoes[unelec] = grid_lcoe
                        status[unelec] = 1
                        cell_path_real[unelec] = dist
                        cell_path_adjusted[unelec] = dist_adjusted
                        new_grid_capacity += peak_load
                        grid_connect_limit -= new_connections[unelec] / nupppphh[unelec]
                        elecorder[unelec] = 1
                        if unelec not in changes:
                            changes.append(unelec)
        electrified = changes[:]
        unelectrified = set(unelectrified).difference(electrified)

        #  Second to last round of extension loops from existing and new lines, including newly connected settlements
        while len(electrified) > 0:
            logging.info('Electrification loop {} with {} electrified'.format(loops, len(electrified)))
            loops += 1
            hash_table = self.get_2d_hash_table(x, y, electrified, max_dist)
            elec_nodes2 = []
            for elec in electrified:
                elec_nodes2.append((x[elec], y[elec]))
            elec_nodes2 = np.asarray(elec_nodes2)
            changes = []
            if len(elec_nodes2) > 0:
                for unelec in unelectrified:
                    if year >= grid_reach[unelec]:
                        consumption = enerperhh[unelec]  # kWh/year
                        average_load = consumption / (1 - grid_calc.distribution_losses) / HOURS_PER_YEAR  # kW
                        peak_load = average_load / grid_calc.base_to_peak_load_ratio  # kW

                        node = (x[unelec], y[unelec])
                        closest_elec_node = closest_elec(node, elec_nodes2)
                        dist = haversine(x[electrified[closest_elec_node]], y[electrified[closest_elec_node]],
                                         x[unelec], y[unelec])
                        dist_adjusted = grid_penalty_ratio[unelec] * dist
                        prev_dist = cell_path_real[electrified[closest_elec_node]]
                        if dist + prev_dist < max_dist:
                            grid_lcoe = grid_calc.get_lcoe(energy_per_cell=enerperhh[unelec],
                                                           start_year=year - timestep,
                                                           end_year=end_year,
                                                           people=pop[unelec],
                                                           new_connections=new_connections[unelec],
                                                           total_energy_per_cell=total_energy_per_cell[unelec],
                                                           prev_code=prev_code[unelec],
                                                           num_people_per_hh=nupppphh[unelec],
                                                           grid_cell_area=grid_cell_area[unelec],
                                                           conf_status=confl[unelec],
                                                           travel_hours=travl[unelec],
                                                           additional_mv_line_length=dist_adjusted,
                                                           elec_loop=elecorder[electrified[closest_elec_node]] + 1)
                            if grid_lcoe < min_code_lcoes[unelec]:
                                if (grid_lcoe < new_lcoes[unelec]) and \
                                        (new_grid_capacity + peak_load < grid_capacity_limit) \
                                        and (new_connections[unelec] / nupppphh[unelec] < grid_connect_limit):
                                    new_lcoes[unelec] = grid_lcoe
                                    cell_path_real[unelec] = dist + cell_path_real[electrified[closest_elec_node]]
                                    cell_path_adjusted[unelec] = dist_adjusted
                                    elecorder[unelec] = elecorder[electrified[closest_elec_node]] + 1
                                    new_grid_capacity += peak_load
                                    grid_connect_limit -= new_connections[unelec] / nupppphh[unelec]
                                    if unelec not in changes:
                                        changes.append(unelec)
                        elif new_grid_capacity + peak_load < grid_capacity_limit and 1 > 2:
                            electrified_hashed = self.get_unelectrified_rows(hash_table, unelec, x, y, max_dist)
                            grid_capacity_addition_loop = 0
                            for elec in electrified_hashed:
                                prev_dist = cell_path_real[elec]
                                dist = haversine(x[elec], y[elec], x[unelec], y[unelec])
                                dist_adjusted = grid_penalty_ratio[unelec] * dist
                                if prev_dist + dist < max_dist:
                                    grid_lcoe = grid_calc.get_lcoe(energy_per_cell=enerperhh[unelec],
                                                                   start_year=year - timestep,
                                                                   end_year=end_year,
                                                                   people=pop[unelec],
                                                                   new_connections=new_connections[unelec],
                                                                   total_energy_per_cell=total_energy_per_cell[
                                                                       unelec],
                                                                   prev_code=prev_code[unelec],
                                                                   num_people_per_hh=nupppphh[unelec],
                                                                   grid_cell_area=grid_cell_area[unelec],
                                                                   conf_status=confl[unelec],
                                                                   travel_hours=travl[unelec],
                                                                   additional_mv_line_length=dist_adjusted,
                                                                   elec_loop=elecorder[elec] + 1)
                                    if grid_lcoe < min_code_lcoes[unelec] and \
                                            (new_grid_capacity + peak_load < grid_capacity_limit) \
                                            and (new_connections[unelec] / nupppphh[unelec] < grid_connect_limit):
                                        if grid_lcoe < new_lcoes[unelec]:
                                            new_lcoes[unelec] = grid_lcoe
                                            cell_path_real[unelec] = dist + cell_path_real[elec]
                                            cell_path_adjusted[unelec] = dist_adjusted
                                            elecorder[unelec] = elecorder[elec] + 1
                                            if grid_capacity_addition_loop == 0:
                                                new_grid_capacity += peak_load
                                                grid_connect_limit -= new_connections[unelec] / nupppphh[unelec]
                                                grid_capacity_addition_loop += 1
                                            if unelec not in changes:
                                                changes.append(unelec)
            electrified = changes[:]
            unelectrified = set(unelectrified).difference(electrified)

        return new_lcoes, cell_path_adjusted, elecorder, cell_path_real

    #Runs the grid extension algorithm
    def set_scenario_variables(self, year, num_people_per_hh_rural, num_people_per_hh_urban, time_step, start_year,
                               urban_elec_ratio, rural_elec_ratio, urban_tier, rural_tier, end_year_pop,
                               productive_demand):
        """
        Set the basic scenario parameters that differ based on urban/rural
        So that they are in the table and can be read directly to calculate LCOEs
        """

        if end_year_pop == 0:
            self.df[SET_POP + "{}".format(year)] = self.df[SET_POP + "{}".format(year) + 'Low']
        else:
            self.df[SET_POP + "{}".format(year)] = self.df[SET_POP + "{}".format(year) + 'High']

        logging.info('Calculate new connections')
        # Calculate new connections for grid related purposes
        # REVIEW - This was changed based on your "newly created" column SET_ELEC_POP. Please review and check whether this creates any problem at your distribution_network function using people/new connections and energy_per_settlement/total_energy_per_settlement

        if year - time_step == start_year:
            # Assign new connections to those that are already electrified to a certain percent
            self.df.loc[(self.df[SET_ELEC_FUTURE_ACTUAL + "{}".format(
                year - time_step)] == 1), SET_NEW_CONNECTIONS + "{}".format(year)] = \
                (self.df[SET_POP + "{}".format(year)] - self.df[SET_ELEC_POP_CALIB])
            # Assign new connections to those that are not currently electrified
            self.df.loc[self.df[SET_ELEC_FUTURE_ACTUAL + "{}".format(year - time_step)] == 0,
                        SET_NEW_CONNECTIONS + "{}".format(year)] = self.df[SET_POP + "{}".format(year)]
            # Some conditioning to eliminate negative values if existing by mistake
            self.df.loc[self.df[SET_NEW_CONNECTIONS + "{}".format(year)] < 0,
                        SET_NEW_CONNECTIONS + "{}".format(year)] = 0
        else:
            # Assign new connections to settlements that are already electrified
            self.df.loc[self.df[SET_LIMIT + "{}".format(year - time_step)] == 1,
                        SET_NEW_CONNECTIONS + "{}".format(year)] = \
                (self.df[SET_POP + "{}".format(year)] - self.df[SET_POP + "{}".format(year - time_step)])

            # Assign new connections to settlements that were initially electrified but not prioritized during the timestep
            self.df.loc[(self.df[SET_LIMIT + "{}".format(year - time_step)] == 0) &
                        (self.df[SET_ELEC_CURRENT] == 1),
                        SET_NEW_CONNECTIONS + "{}".format(year)] = self.df[SET_POP + "{}".format(year)] - self.df[
                SET_ELEC_POP_CALIB]

            # Assing new connections to settlements that have not been electrified
            self.df.loc[(self.df[SET_LIMIT + "{}".format(year - time_step)] == 0) & (
                    self.df[SET_ELEC_CURRENT] == 0),
                        SET_NEW_CONNECTIONS + "{}".format(year)] = self.df[SET_POP + "{}".format(year)]

            # Some conditioning to eliminate negative values if existing by mistake
            self.df.loc[
                self.df[SET_NEW_CONNECTIONS + "{}".format(year)] < 0, SET_NEW_CONNECTIONS + "{}".format(year)] = 0

        logging.info('Setting electrification demand as per target per year')

        if max(self.df[SET_CAPITA_DEMAND]) == 0:
            # RUN_PARAM: This shall be changed if different urban/rural categorization is decided
            wb_tier_rural = int(rural_tier)
            wb_tier_urban_clusters = int(rural_tier)
            wb_tier_urban_centers = int(urban_tier)

            if wb_tier_urban_centers == 6:
                wb_tier_urban_centers = 'Custom'
            if wb_tier_urban_clusters == 6:
                wb_tier_urban_clusters = 'Custom'
            if wb_tier_rural == 6:
                wb_tier_rural = 'Custom'

            self.df[SET_CAPITA_DEMAND] = 0

            # RUN_PARAM: This shall be changed if different urban/rural categorization is decided
            # Create new columns assigning number of people per household as per Urban/Rural type
            self.df.loc[self.df[SET_URBAN] == 0, SET_NUM_PEOPLE_PER_HH] = num_people_per_hh_rural
            self.df.loc[self.df[SET_URBAN] == 1, SET_NUM_PEOPLE_PER_HH] = num_people_per_hh_rural
            self.df.loc[self.df[SET_URBAN] == 2, SET_NUM_PEOPLE_PER_HH] = num_people_per_hh_urban

            # Define per capita residential demand
            self.df.loc[self.df[SET_URBAN] == 0, SET_CAPITA_DEMAND] = self.df[
                SET_RESIDENTIAL_TIER + str(wb_tier_rural)]
            self.df.loc[self.df[SET_URBAN] == 1, SET_CAPITA_DEMAND] = self.df[
                SET_RESIDENTIAL_TIER + str(wb_tier_urban_clusters)]
            self.df.loc[self.df[SET_URBAN] == 2, SET_CAPITA_DEMAND] = self.df[
                SET_RESIDENTIAL_TIER + str(wb_tier_urban_centers)]

            # REVIEW, added Tier column
            tier_1 = 38.7  # 38.7 refers to kWh/household/year. It is the mean value between Tier 1 and Tier 2
            tier_2 = 219
            tier_3 = 803
            tier_4 = 2117
            tier_5 = 2993

            self.df[SET_TIER] = 5
            self.df.loc[self.df[SET_CAPITA_DEMAND] * self.df[SET_NUM_PEOPLE_PER_HH] < tier_4, SET_TIER] = 4
            self.df.loc[self.df[SET_CAPITA_DEMAND] * self.df[SET_NUM_PEOPLE_PER_HH] < tier_3, SET_TIER] = 3
            self.df.loc[self.df[SET_CAPITA_DEMAND] * self.df[SET_NUM_PEOPLE_PER_HH] < tier_2, SET_TIER] = 2
            self.df.loc[self.df[SET_CAPITA_DEMAND] * self.df[SET_NUM_PEOPLE_PER_HH] < tier_1, SET_TIER] = 1

            # Add commercial demand
            # agri = True if 'y' in input('Include agrcultural demand? <y/n> ') else False
            # if agri:
            if int(productive_demand) == 1:
                self.df[SET_CAPITA_DEMAND] += self.df[SET_AGRI_DEMAND]

            # commercial = True if 'y' in input('Include commercial demand? <y/n> ') else False
            # if commercial:
            if int(productive_demand) == 1:
                self.df[SET_CAPITA_DEMAND] += self.df[SET_COMMERCIAL_DEMAND]

            # health = True if 'y' in input('Include health demand? <y/n> ') else False
            # if health:
            if int(productive_demand) == 1:
                self.df[SET_CAPITA_DEMAND] += self.df[SET_HEALTH_DEMAND]

            # edu = True if 'y' in input('Include educational demand? <y/n> ') else False
            # if edu:
            if int(productive_demand) == 1:
                self.df[SET_CAPITA_DEMAND] += self.df[SET_EDU_DEMAND]

        self.df.loc[self.df[SET_URBAN] == 0, SET_ENERGY_PER_CELL + "{}".format(year)] = \
            self.df[SET_CAPITA_DEMAND] * self.df[SET_NEW_CONNECTIONS + "{}".format(year)]
        self.df.loc[self.df[SET_URBAN] == 1, SET_ENERGY_PER_CELL + "{}".format(year)] = \
            self.df[SET_CAPITA_DEMAND] * self.df[SET_NEW_CONNECTIONS + "{}".format(year)]
        self.df.loc[self.df[SET_URBAN] == 2, SET_ENERGY_PER_CELL + "{}".format(year)] = \
            self.df[SET_CAPITA_DEMAND] * self.df[SET_NEW_CONNECTIONS + "{}".format(year)]

        # if year - time_step == start_year:
        self.df.loc[self.df[SET_URBAN] == 0, SET_TOTAL_ENERGY_PER_CELL] = \
            self.df[SET_CAPITA_DEMAND] * self.df[SET_POP + "{}".format(year)]
        self.df.loc[self.df[SET_URBAN] == 1, SET_TOTAL_ENERGY_PER_CELL] = \
            self.df[SET_CAPITA_DEMAND] * self.df[SET_POP + "{}".format(year)]
        self.df.loc[self.df[SET_URBAN] == 2, SET_TOTAL_ENERGY_PER_CELL] = \
            self.df[SET_CAPITA_DEMAND] * self.df[SET_POP + "{}".format(year)]

    def grid_reach_estimate(self, start_year, gridspeed):
        """ Estimates the year of grid arrival based on geospatial characteristics
        and grid expansion speed in km/year"""

        # logging.info('Estimate year of grid reach')
        # self.df[SET_GRID_REACH_YEAR] = 0
        # self.df.loc[self.df[SET_ELEC_FUTURE_GRID + "{}".format(start_year)] == 0, SET_GRID_REACH_YEAR] = \
        #     self.df[SET_HV_DIST_PLANNED] * self.df[SET_GRID_PENALTY] / gridspeed

        self.df[SET_GRID_REACH_YEAR] = \
            self.df.apply(lambda row: int(start_year +
                                          row[SET_HV_DIST_PLANNED] * row[SET_COMBINED_CLASSIFICATION] / gridspeed)
            if row[SET_ELEC_FUTURE_GRID + "{}".format(start_year)] == 0
            else start_year,
                          axis=1)

    def calculate_off_grid_lcoes(self, mg_hydro_calc, mg_wind_calc, mg_pv_calc,
                                 sa_pv_calc, mg_diesel_calc, sa_diesel_calc, hybrid_1, hybrid_2, hybrid_3, hybrid_4,
                                 hybrid_5,
                                 year, start_year, end_year, timestep, diesel_techs=0):
        """
        Calcuate the LCOEs for all off-grid technologies, and calculate the minimum, so that the electrification
        algorithm knows where the bar is before it becomes economical to electrify
        """

        # A df with all hydropower sites, to ensure that they aren't assigned more capacity than is available
        hydro_used = 'HydropowerUsed'  # the amount of the hydro potential that has been assigned
        hydro_df = self.df[[SET_HYDRO_FID, SET_HYDRO]].drop_duplicates(subset=SET_HYDRO_FID)
        hydro_df[hydro_used] = 0
        hydro_df = hydro_df.set_index(SET_HYDRO_FID)

        max_hydro_dist = 5  # the max distance in km to consider hydropower viable

        def hydro_lcoe(row):
            if row[SET_HYDRO_DIST] < max_hydro_dist:
                # calculate the capacity that would be added by the settlement
                additional_capacity = ((row[SET_NEW_CONNECTIONS + "{}".format(year)] *
                                        row[SET_ENERGY_PER_CELL + "{}".format(year)]) /
                                       (HOURS_PER_YEAR * mg_hydro_calc.capacity_factor *
                                        mg_hydro_calc.base_to_peak_load_ratio))

                # and add it to the tracking df
                hydro_df.loc[row[SET_HYDRO_FID], hydro_used] += additional_capacity

                # if it exceeds the available capacity, it's not an option
                if hydro_df.loc[row[SET_HYDRO_FID], hydro_used] > hydro_df.loc[row[SET_HYDRO_FID], SET_HYDRO]:
                    return 99

                else:
                    return mg_hydro_calc.get_lcoe(energy_per_cell=row[SET_ENERGY_PER_CELL + "{}".format(year)],
                                                  start_year=year - timestep,
                                                  end_year=end_year,
                                                  people=row[SET_POP + "{}".format(year)],
                                                  new_connections=row[SET_NEW_CONNECTIONS + "{}".format(year)],
                                                  total_energy_per_cell=row[SET_TOTAL_ENERGY_PER_CELL],
                                                  prev_code=row[SET_ELEC_FINAL_CODE + "{}".format(year - timestep)],
                                                  num_people_per_hh=row[SET_NUM_PEOPLE_PER_HH],
                                                  grid_cell_area=row[SET_GRID_CELL_AREA],
                                                  conf_status=row[SET_CONFLICT],
                                                  mv_line_length=row[SET_HYDRO_DIST])
            else:
                return 99

        logging.info('Calculate minigrid hydro LCOE')
        self.df[SET_LCOE_MG_HYDRO + "{}".format(year)] = self.df.apply(hydro_lcoe, axis=1)

        num_hydro_limited = hydro_df.loc[hydro_df[hydro_used] > hydro_df[SET_HYDRO]][SET_HYDRO].count()
        logging.info('{} potential hydropower sites were utilised to maximum capacity'.format(num_hydro_limited))

        logging.info('Calculate minigrid PV LCOE')
        self.df[SET_LCOE_MG_PV + "{}".format(year)] = self.df.apply(
            lambda row: mg_pv_calc.get_lcoe(energy_per_cell=row[SET_ENERGY_PER_CELL + "{}".format(year)],
                                            start_year=year - timestep,
                                            end_year=end_year,
                                            people=row[SET_POP + "{}".format(year)],
                                            new_connections=row[SET_NEW_CONNECTIONS + "{}".format(year)],
                                            total_energy_per_cell=row[SET_TOTAL_ENERGY_PER_CELL],
                                            prev_code=row[SET_ELEC_FINAL_CODE + "{}".format(year - timestep)],
                                            num_people_per_hh=row[SET_NUM_PEOPLE_PER_HH],
                                            grid_cell_area=row[SET_GRID_CELL_AREA],
                                            conf_status=row[SET_CONFLICT],
                                            capacity_factor=row[SET_GHI] / HOURS_PER_YEAR)
            if row[SET_GHI] > 1000
            else 99, axis=1)

        logging.info('Calculate minigrid wind LCOE')
        self.df[SET_LCOE_MG_WIND + "{}".format(year)] = self.df.apply(
            lambda row: mg_wind_calc.get_lcoe(energy_per_cell=row[SET_ENERGY_PER_CELL + "{}".format(year)],
                                              start_year=year - timestep,
                                              end_year=end_year,
                                              people=row[SET_POP + "{}".format(year)],
                                              new_connections=row[SET_NEW_CONNECTIONS + "{}".format(year)],
                                              total_energy_per_cell=row[SET_TOTAL_ENERGY_PER_CELL],
                                              prev_code=row[SET_ELEC_FINAL_CODE + "{}".format(year - timestep)],
                                              num_people_per_hh=row[SET_NUM_PEOPLE_PER_HH],
                                              grid_cell_area=row[SET_GRID_CELL_AREA],
                                              conf_status=row[SET_CONFLICT],
                                              capacity_factor=row[SET_WINDCF])
            if row[SET_WINDCF] > 0.1 else 99,
            axis=1)

        if diesel_techs == 0:
            self.df[SET_LCOE_MG_DIESEL + "{}".format(year)] = 99
            self.df[SET_LCOE_SA_DIESEL + "{}".format(year)] = 99
        else:
            logging.info('Calculate minigrid diesel LCOE')
            self.df[SET_LCOE_MG_DIESEL + "{}".format(year)] = self.df.apply(
                lambda row: mg_diesel_calc.get_lcoe(energy_per_cell=row[SET_ENERGY_PER_CELL + "{}".format(year)],
                                                    start_year=year - timestep,
                                                    end_year=end_year,
                                                    people=row[SET_POP + "{}".format(year)],
                                                    new_connections=row[SET_NEW_CONNECTIONS + "{}".format(year)],
                                                    total_energy_per_cell=row[SET_TOTAL_ENERGY_PER_CELL],
                                                    prev_code=row[SET_ELEC_FINAL_CODE + "{}".format(year - timestep)],
                                                    num_people_per_hh=row[SET_NUM_PEOPLE_PER_HH],
                                                    grid_cell_area=row[SET_GRID_CELL_AREA],
                                                    conf_status=row[SET_CONFLICT],
                                                    travel_hours=row[SET_TRAVEL_HOURS]), axis=1)

            logging.info('Calculate standalone diesel LCOE')
            self.df[SET_LCOE_SA_DIESEL + "{}".format(year)] = self.df.apply(
                lambda row: sa_diesel_calc.get_lcoe(energy_per_cell=row[SET_ENERGY_PER_CELL + "{}".format(year)],
                                                    start_year=year - timestep,
                                                    end_year=end_year,
                                                    people=row[SET_POP + "{}".format(year)],
                                                    new_connections=row[SET_NEW_CONNECTIONS + "{}".format(year)],
                                                    total_energy_per_cell=row[SET_TOTAL_ENERGY_PER_CELL],
                                                    prev_code=row[SET_ELEC_FINAL_CODE + "{}".format(year - timestep)],
                                                    num_people_per_hh=row[SET_NUM_PEOPLE_PER_HH],
                                                    grid_cell_area=row[SET_GRID_CELL_AREA],
                                                    conf_status=row[SET_CONFLICT],
                                                    travel_hours=row[SET_TRAVEL_HOURS]), axis=1)

        logging.info('Calculate standalone PV LCOE')
        self.df[SET_LCOE_SA_PV + "{}".format(year)] = self.df.apply(
            lambda row: sa_pv_calc.get_lcoe(energy_per_cell=row[SET_ENERGY_PER_CELL + "{}".format(year)],
                                            start_year=year - timestep,
                                            end_year=end_year,
                                            people=row[SET_POP + "{}".format(year)],
                                            new_connections=row[SET_NEW_CONNECTIONS + "{}".format(year)],
                                            total_energy_per_cell=row[SET_TOTAL_ENERGY_PER_CELL],
                                            prev_code=row[SET_ELEC_FINAL_CODE + "{}".format(year - timestep)],
                                            num_people_per_hh=row[SET_NUM_PEOPLE_PER_HH],
                                            grid_cell_area=row[SET_GRID_CELL_AREA],
                                            conf_status=row[SET_CONFLICT],
                                            capacity_factor=row[SET_GHI] / HOURS_PER_YEAR) if row[SET_GHI] > 1000
            else 99,
            axis=1)

        # logging.info('Calculate PV diesel hybrid LCOE')
        # self.df[SET_LCOE_MG_HYBRID + "{}".format(year)] = self.df.apply(
        #     lambda row: pv_diesel_hyb.get_lcoe(energy_per_cell=row[SET_ENERGY_PER_CELL + "{}".format(year)],
        #                                        total_energy_per_cell=row[SET_TOTAL_ENERGY_PER_CELL],
        #                                        prev_code=row[SET_ELEC_FINAL_CODE + "{}".format(year - timestep)],
        #                                        conf_status=row[SET_CONFLICT],
        #                                        start_year=year - timestep,
        #                                        end_year=end_year,
        #                                        people=row[SET_POP + "{}".format(year)],
        #                                        new_connections=row[SET_NEW_CONNECTIONS + "{}".format(year)],
        #                                        num_people_per_hh=row[SET_NUM_PEOPLE_PER_HH],
        #                                        travel_hours=row[SET_TRAVEL_HOURS],
        #                                        ghi=row[SET_GHI],
        #                                        urban=row[SET_URBAN],
        #                                        hybrid_1=hybrid_1,
        #                                        hybrid_2=hybrid_2,
        #                                        hybrid_3=hybrid_3,
        #                                        hybrid_4=hybrid_4,
        #                                        hybrid_5=hybrid_5,
        #                                        tier=row[SET_TIER],
        #                                        grid_cell_area=row[SET_GRID_CELL_AREA],
        #                                        mg_hybrid=True,
        #                                        )
        #     if row[SET_GHI] > 1000 else 99,
        #     axis=1)

        logging.info('Determine minimum technology (off-grid)')
        # self.df[SET_MIN_OFFGRID + "{}".format(year)] = self.df[[SET_LCOE_SA_DIESEL + "{}".format(year),
        #                                                         SET_LCOE_SA_PV + "{}".format(year),
        #                                                         SET_LCOE_MG_WIND + "{}".format(year),
        #                                                         SET_LCOE_MG_DIESEL + "{}".format(year),
        #                                                         SET_LCOE_MG_PV + "{}".format(year),
        #                                                         SET_LCOE_MG_HYDRO + "{}".format(year),
        #                                                         SET_LCOE_MG_HYBRID + "{}".format(year)]].T.idxmin()

        self.df[SET_MIN_OFFGRID + "{}".format(year)] = self.df[[SET_LCOE_SA_PV + "{}".format(year),
                                                                SET_LCOE_MG_WIND + "{}".format(year),
                                                                SET_LCOE_MG_PV + "{}".format(year),
                                                                SET_LCOE_MG_HYDRO + "{}".format(year),
                                                                SET_LCOE_MG_DIESEL + "{}".format(year),
                                                                SET_LCOE_SA_DIESEL + "{}".format(year)]].T.idxmin()

        logging.info('Determine minimum tech LCOE')
        # self.df[SET_MIN_OFFGRID_LCOE + "{}".format(year)] = \
        #     self.df.apply(lambda row: (row[row[SET_MIN_OFFGRID + "{}".format(year)]]), axis=1)
        # self.df[SET_MIN_OFFGRID_LCOE + "{}".format(year)] = self.df[[SET_LCOE_SA_DIESEL + "{}".format(year),
        #                                                              SET_LCOE_SA_PV + "{}".format(year),
        #                                                              SET_LCOE_MG_DIESEL + "{}".format(year),
        #                                                              SET_LCOE_MG_WIND + "{}".format(year),
        #                                                              SET_LCOE_MG_PV + "{}".format(year),
        #                                                              SET_LCOE_MG_HYDRO + "{}".format(year),
        #                                                              SET_LCOE_MG_HYBRID + "{}".format(year)]].T.min()

        self.df[SET_MIN_OFFGRID_LCOE + "{}".format(year)] = self.df[[SET_LCOE_SA_PV + "{}".format(year),
                                                                     SET_LCOE_MG_WIND + "{}".format(year),
                                                                     SET_LCOE_MG_PV + "{}".format(year),
                                                                     SET_LCOE_MG_HYDRO + "{}".format(year),
                                                                     SET_LCOE_MG_DIESEL + "{}".format(year),
                                                                     SET_LCOE_SA_DIESEL + "{}".format(year)]].T.min()

        codes = {SET_LCOE_MG_HYBRID + "{}".format(year): 8,
                 SET_LCOE_MG_HYDRO + "{}".format(year): 7,
                 SET_LCOE_MG_WIND + "{}".format(year): 6,
                 SET_LCOE_MG_PV + "{}".format(year): 5,
                 SET_LCOE_MG_DIESEL + "{}".format(year): 4,
                 SET_LCOE_SA_DIESEL + "{}".format(year): 2,
                 SET_LCOE_SA_PV + "{}".format(year): 3}

        self.df.loc[self.df[SET_MIN_OFFGRID + "{}".format(year)] == SET_LCOE_MG_HYDRO + "{}".format(
            year), SET_MIN_OFFGRID_CODE + "{}".format(year)] = codes[SET_LCOE_MG_HYDRO + "{}".format(year)]
        self.df.loc[self.df[SET_MIN_OFFGRID + "{}".format(year)] == SET_LCOE_SA_PV + "{}".format(
            year), SET_MIN_OFFGRID_CODE + "{}".format(year)] = codes[SET_LCOE_SA_PV + "{}".format(year)]
        self.df.loc[self.df[SET_MIN_OFFGRID + "{}".format(year)] == SET_LCOE_MG_WIND + "{}".format(
            year), SET_MIN_OFFGRID_CODE + "{}".format(year)] = codes[SET_LCOE_MG_WIND + "{}".format(year)]
        self.df.loc[self.df[SET_MIN_OFFGRID + "{}".format(year)] == SET_LCOE_MG_PV + "{}".format(
            year), SET_MIN_OFFGRID_CODE + "{}".format(year)] = codes[SET_LCOE_MG_PV + "{}".format(year)]
        self.df.loc[self.df[SET_MIN_OFFGRID + "{}".format(year)] == SET_LCOE_MG_DIESEL + "{}".format(
            year), SET_MIN_OFFGRID_CODE + "{}".format(year)] = codes[SET_LCOE_MG_DIESEL + "{}".format(year)]
        self.df.loc[self.df[SET_MIN_OFFGRID + "{}".format(year)] == SET_LCOE_SA_DIESEL + "{}".format(
            year), SET_MIN_OFFGRID_CODE + "{}".format(year)] = codes[SET_LCOE_SA_DIESEL + "{}".format(year)]
        self.df.loc[self.df[SET_MIN_OFFGRID + "{}".format(year)] == SET_LCOE_MG_HYBRID + "{}".format(
            year), SET_MIN_OFFGRID_CODE + "{}".format(year)] = codes[SET_LCOE_MG_HYBRID + "{}".format(year)]

    def results_columns(self, mg_hydro_calc, mg_wind_calc, mg_pv_calc, sa_pv_calc, mg_diesel_calc,
                        sa_diesel_calc, grid_calc, hybrid_1, hybrid_2, hybrid_3, hybrid_4, hybrid_5, year):
        """
        Once the grid extension algorithm has been run, determine the minimum overall option, and calculate the
        capacity and investment requirements for each settlement
        """

        logging.info('Determine minimum overall')
        self.df[SET_MIN_OVERALL + "{}".format(year)] = self.df[[SET_LCOE_GRID + "{}".format(year),
                                                                SET_LCOE_SA_PV + "{}".format(year),
                                                                SET_LCOE_MG_WIND + "{}".format(year),
                                                                SET_LCOE_MG_PV + "{}".format(year),
                                                                SET_LCOE_MG_HYDRO + "{}".format(year),
                                                                SET_LCOE_MG_DIESEL + "{}".format(year),
                                                                SET_LCOE_SA_DIESEL + "{}".format(year)]].T.idxmin()

        logging.info('Determine minimum overall LCOE')
        self.df[SET_MIN_OVERALL_LCOE + "{}".format(year)] = self.df[[SET_LCOE_GRID + "{}".format(year),
                                                                     SET_LCOE_SA_PV + "{}".format(year),
                                                                     SET_LCOE_MG_WIND + "{}".format(year),
                                                                     SET_LCOE_MG_PV + "{}".format(year),
                                                                     SET_LCOE_MG_HYDRO + "{}".format(year),
                                                                     SET_LCOE_MG_DIESEL + "{}".format(year),
                                                                     SET_LCOE_SA_DIESEL + "{}".format(year)]].T.min()

        logging.info('Add technology codes')
        codes = {SET_LCOE_GRID + "{}".format(year): 1,
                 SET_LCOE_MG_HYBRID + "{}".format(year): 8,
                 SET_LCOE_MG_HYDRO + "{}".format(year): 7,
                 SET_LCOE_MG_WIND + "{}".format(year): 6,
                 SET_LCOE_MG_PV + "{}".format(year): 5,
                 SET_LCOE_MG_DIESEL + "{}".format(year): 4,
                 SET_LCOE_SA_DIESEL + "{}".format(year): 2,
                 SET_LCOE_SA_PV + "{}".format(year): 3}

        self.df.loc[self.df[SET_MIN_OVERALL + "{}".format(year)] == SET_LCOE_GRID + "{}".format(year),
                    SET_MIN_OVERALL_CODE + "{}".format(year)] = codes[SET_LCOE_GRID + "{}".format(year)]
        self.df.loc[self.df[SET_MIN_OVERALL + "{}".format(year)] == SET_LCOE_MG_HYDRO + "{}".format(year),
                    SET_MIN_OVERALL_CODE + "{}".format(year)] = codes[SET_LCOE_MG_HYDRO + "{}".format(year)]
        self.df.loc[self.df[SET_MIN_OVERALL + "{}".format(year)] == SET_LCOE_SA_PV + "{}".format(year),
                    SET_MIN_OVERALL_CODE + "{}".format(year)] = codes[SET_LCOE_SA_PV + "{}".format(year)]
        self.df.loc[self.df[SET_MIN_OVERALL + "{}".format(year)] == SET_LCOE_MG_WIND + "{}".format(year),
                    SET_MIN_OVERALL_CODE + "{}".format(year)] = codes[SET_LCOE_MG_WIND + "{}".format(year)]
        self.df.loc[self.df[SET_MIN_OVERALL + "{}".format(year)] == SET_LCOE_MG_PV + "{}".format(year),
                    SET_MIN_OVERALL_CODE + "{}".format(year)] = codes[SET_LCOE_MG_PV + "{}".format(year)]
        self.df.loc[self.df[SET_MIN_OVERALL + "{}".format(year)] == SET_LCOE_MG_DIESEL + "{}".format(year),
                    SET_MIN_OVERALL_CODE + "{}".format(year)] = codes[SET_LCOE_MG_DIESEL + "{}".format(year)]
        self.df.loc[self.df[SET_MIN_OVERALL + "{}".format(year)] == SET_LCOE_SA_DIESEL + "{}".format(year),
                    SET_MIN_OVERALL_CODE + "{}".format(year)] = codes[SET_LCOE_SA_DIESEL + "{}".format(year)]
        self.df.loc[self.df[SET_MIN_OVERALL + "{}".format(year)] == SET_LCOE_MG_HYBRID + "{}".format(
            year), SET_MIN_OVERALL_CODE + "{}".format(year)] = codes[SET_LCOE_MG_HYBRID + "{}".format(year)]

    def calculate_investments(self, mg_hydro_calc, mg_wind_calc, mg_pv_calc, sa_pv_calc, mg_diesel_calc,
                              sa_diesel_calc, grid_calc, hybrid_1, hybrid_2, hybrid_3, hybrid_4, hybrid_5, year,
                              end_year, timestep):
        def res_investment_cost(row):
            min_code = row[SET_MIN_OVERALL_CODE + "{}".format(year)]

            if min_code == 2:
                return sa_diesel_calc.get_lcoe(energy_per_cell=row[SET_ENERGY_PER_CELL + "{}".format(year)],
                                               start_year=year - timestep,
                                               end_year=end_year,
                                               people=row[SET_POP + "{}".format(year)],
                                               new_connections=row[SET_NEW_CONNECTIONS + "{}".format(year)],
                                               total_energy_per_cell=row[SET_TOTAL_ENERGY_PER_CELL],
                                               prev_code=row[SET_ELEC_FINAL_CODE + "{}".format(year - timestep)],
                                               num_people_per_hh=row[SET_NUM_PEOPLE_PER_HH],
                                               grid_cell_area=row[SET_GRID_CELL_AREA],
                                               travel_hours=row[SET_TRAVEL_HOURS],
                                               conf_status=row[SET_CONFLICT],
                                               get_investment_cost=True)

            elif min_code == 3:
                return sa_pv_calc.get_lcoe(energy_per_cell=row[SET_ENERGY_PER_CELL + "{}".format(year)],
                                           start_year=year - timestep,
                                           end_year=end_year,
                                           people=row[SET_POP + "{}".format(year)],
                                           new_connections=row[SET_NEW_CONNECTIONS + "{}".format(year)],
                                           total_energy_per_cell=row[SET_TOTAL_ENERGY_PER_CELL],
                                           prev_code=row[SET_ELEC_FINAL_CODE + "{}".format(year - timestep)],
                                           num_people_per_hh=row[SET_NUM_PEOPLE_PER_HH],
                                           grid_cell_area=row[SET_GRID_CELL_AREA],
                                           capacity_factor=row[SET_GHI] / HOURS_PER_YEAR,
                                           conf_status=row[SET_CONFLICT],
                                           get_investment_cost=True)

            elif min_code == 6:
                return mg_wind_calc.get_lcoe(energy_per_cell=row[SET_ENERGY_PER_CELL + "{}".format(year)],
                                             start_year=year - timestep,
                                             end_year=end_year,
                                             people=row[SET_POP + "{}".format(year)],
                                             new_connections=row[SET_NEW_CONNECTIONS + "{}".format(year)],
                                             total_energy_per_cell=row[SET_TOTAL_ENERGY_PER_CELL],
                                             prev_code=row[SET_ELEC_FINAL_CODE + "{}".format(year - timestep)],
                                             num_people_per_hh=row[SET_NUM_PEOPLE_PER_HH],
                                             grid_cell_area=row[SET_GRID_CELL_AREA],
                                             capacity_factor=row[SET_WINDCF],
                                             conf_status=row[SET_CONFLICT],
                                             get_investment_cost=True)

            elif min_code == 4:
                return mg_diesel_calc.get_lcoe(energy_per_cell=row[SET_ENERGY_PER_CELL + "{}".format(year)],
                                               start_year=year - timestep,
                                               end_year=end_year,
                                               people=row[SET_POP + "{}".format(year)],
                                               new_connections=row[SET_NEW_CONNECTIONS + "{}".format(year)],
                                               total_energy_per_cell=row[SET_TOTAL_ENERGY_PER_CELL],
                                               prev_code=row[SET_ELEC_FINAL_CODE + "{}".format(year - timestep)],
                                               num_people_per_hh=row[SET_NUM_PEOPLE_PER_HH],
                                               grid_cell_area=row[SET_GRID_CELL_AREA],
                                               travel_hours=row[SET_TRAVEL_HOURS],
                                               conf_status=row[SET_CONFLICT],
                                               get_investment_cost=True)

            elif min_code == 5:
                return mg_pv_calc.get_lcoe(energy_per_cell=row[SET_ENERGY_PER_CELL + "{}".format(year)],
                                           start_year=year - timestep,
                                           end_year=end_year,
                                           people=row[SET_POP + "{}".format(year)],
                                           new_connections=row[SET_NEW_CONNECTIONS + "{}".format(year)],
                                           total_energy_per_cell=row[SET_TOTAL_ENERGY_PER_CELL],
                                           prev_code=row[SET_ELEC_FINAL_CODE + "{}".format(year - timestep)],
                                           num_people_per_hh=row[SET_NUM_PEOPLE_PER_HH],
                                           grid_cell_area=row[SET_GRID_CELL_AREA],
                                           capacity_factor=row[SET_GHI] / HOURS_PER_YEAR,
                                           conf_status=row[SET_CONFLICT],
                                           get_investment_cost=True)

            elif min_code == 7:
                return mg_hydro_calc.get_lcoe(energy_per_cell=row[SET_ENERGY_PER_CELL + "{}".format(year)],
                                              start_year=year - timestep,
                                              end_year=end_year,
                                              people=row[SET_POP + "{}".format(year)],
                                              new_connections=row[SET_NEW_CONNECTIONS + "{}".format(year)],
                                              total_energy_per_cell=row[SET_TOTAL_ENERGY_PER_CELL],
                                              prev_code=row[SET_ELEC_FINAL_CODE + "{}".format(year - timestep)],
                                              num_people_per_hh=row[SET_NUM_PEOPLE_PER_HH],
                                              grid_cell_area=row[SET_GRID_CELL_AREA],
                                              conf_status=row[SET_CONFLICT],
                                              mv_line_length=row[SET_HYDRO_DIST],
                                              get_investment_cost=True)

            elif min_code == 1:
                return grid_calc.get_lcoe(energy_per_cell=row[SET_ENERGY_PER_CELL + "{}".format(year)],
                                          start_year=year - timestep,
                                          end_year=end_year,
                                          people=row[SET_POP + "{}".format(year)],
                                          new_connections=row[SET_NEW_CONNECTIONS + "{}".format(year)],
                                          total_energy_per_cell=row[SET_TOTAL_ENERGY_PER_CELL],
                                          prev_code=row[SET_ELEC_FINAL_CODE + "{}".format(year - timestep)],
                                          num_people_per_hh=row[SET_NUM_PEOPLE_PER_HH],
                                          grid_cell_area=row[SET_GRID_CELL_AREA],
                                          conf_status=row[SET_CONFLICT],
                                          additional_mv_line_length=row[SET_MIN_GRID_DIST + "{}".format(year)],
                                          elec_loop=row[SET_ELEC_ORDER + "{}".format(year)],
                                          get_investment_cost=True)
            elif min_code == 8:
                pass
                # return pv_diesel_hyb.get_lcoe(energy_per_cell=row[SET_ENERGY_PER_CELL + "{}".format(year)],
                #                               total_energy_per_cell=row[SET_TOTAL_ENERGY_PER_CELL],
                #                               prev_code=row[SET_ELEC_FINAL_CODE + "{}".format(year - timestep)],
                #                               conf_status=row[SET_CONFLICT],
                #                               start_year=year - timestep,
                #                               end_year=end_year,
                #                               people=row[SET_POP + "{}".format(year)],
                #                               new_connections=row[SET_NEW_CONNECTIONS + "{}".format(year)],
                #                               num_people_per_hh=row[SET_NUM_PEOPLE_PER_HH],
                #                               travel_hours=row[SET_TRAVEL_HOURS],
                #                               ghi=row[SET_GHI],
                #                               urban=row[SET_URBAN],
                #                               hybrid_1=hybrid_1,
                #                               hybrid_2=hybrid_2,
                #                               hybrid_3=hybrid_3,
                #                               hybrid_4=hybrid_4,
                #                               hybrid_5=hybrid_5,
                #                               tier=row[SET_TIER],
                #                               grid_cell_area=row[SET_GRID_CELL_AREA],
                #                               mg_hybrid=True,
                #                               get_investment_cost=True)
            else:
                return 0

        logging.info('Calculate investment cost')
        self.df[SET_INVESTMENT_COST + "{}".format(year)] = self.df.apply(res_investment_cost, axis=1)

    def apply_limitations(self, eleclimit, year, timestep, prioritization, auto_densification=0):

        logging.info('Determine electrification limits')
        choice = int(prioritization)
        elec_limit_origin = eleclimit
        if (eleclimit == 1) & (choice != 4):
            self.df[SET_LIMIT + "{}".format(year)] = 1
            self.df[SET_INVEST_PER_CAPITA + "{}".format(year)] = self.df[SET_INVESTMENT_COST + "{}".format(year)] / \
                                                                 self.df[SET_NEW_CONNECTIONS + "{}".format(year)]
            elecrate = 1
        else:

            self.df[SET_LIMIT + "{}".format(year)] = 0

            # RUN_PARAM: Here one can modify the prioritization algorithm - Currently only the first option is reviewed and ready to be used
            if choice == 1:  # Prioritize grid densification first, then lowest investment per capita
                elecrate = 0
                min_investment = 0
                min_dist_to_cities = 50
                iter_limit_1 = 0
                iter_limit_2 = 0
                iter_limit_3 = 0
                iter_limit_4 = 0
                self.df[SET_INVEST_PER_CAPITA + "{}".format(year)] = self.df[SET_INVESTMENT_COST + "{}".format(year)] / \
                                                                     self.df[SET_NEW_CONNECTIONS + "{}".format(year)]
                step_size = self.df[SET_INVEST_PER_CAPITA + "{}".format(year)].quantile(q=0.95) / 100
                if sum(self.df[self.df[SET_ELEC_FUTURE_GRID + "{}".format(year - timestep)] == 1][
                           SET_POP + "{}".format(year)]) / \
                        self.df[SET_POP + "{}".format(year)].sum() < eleclimit:
                    eleclimit -= sum(self.df[self.df[SET_ELEC_FUTURE_GRID + "{}".format(year - timestep)] == 1][
                                         SET_POP + "{}".format(year)]) / \
                                 self.df[SET_POP + "{}".format(year)].sum()

                    while abs(elecrate - eleclimit) > 0.01:
                        elecrate = sum(self.df[(self.df[SET_INVEST_PER_CAPITA + "{}".format(year)] < min_investment) &
                                               (self.df[SET_ELEC_FUTURE_GRID + "{}".format(year - timestep)] == 0) &
                                               (self.df[SET_TRAVEL_HOURS] < min_dist_to_cities)][
                                           SET_POP + "{}".format(year)]) / \
                                   self.df[SET_POP + "{}".format(year)].sum()
                        if (eleclimit - elecrate > 0.01) and (iter_limit_3 < 100):
                            min_investment += step_size
                            iter_limit_3 += 1
                        elif ((elecrate - eleclimit) > 0.01) and (iter_limit_4 < 20):
                            min_investment -= 0.05 * step_size
                            iter_limit_4 += 1
                        else:
                            break

                    # Updating (using the SET_LIMIT function) what is electrified in the year and what is not
                    self.df.loc[
                        (self.df[SET_ELEC_FUTURE_GRID + "{}".format(year - timestep)] == 1), SET_LIMIT + "{}".format(
                            year)] = 1

                    self.df.loc[(self.df[SET_INVEST_PER_CAPITA + "{}".format(year)] <= min_investment) &
                                (self.df[SET_ELEC_FUTURE_GRID + "{}".format(year - timestep)] == 0) &
                                (self.df[SET_TRAVEL_HOURS] <= min_dist_to_cities), SET_LIMIT + "{}".format(year)] = 1

                    self.df.loc[(self.df[SET_INVEST_PER_CAPITA + "{}".format(year)] <= min_investment) &
                                (self.df[SET_ELEC_FUTURE_GRID + "{}".format(year - timestep)] == 0) &
                                (self.df[SET_TRAVEL_HOURS] > min_dist_to_cities), SET_LIMIT + "{}".format(year)] = 0

                    self.df.loc[(self.df[SET_INVEST_PER_CAPITA + "{}".format(year)] > min_investment) &
                                (self.df[SET_ELEC_FUTURE_GRID + "{}".format(
                                    year - timestep)] == 0), SET_LIMIT + "{}".format(year)] = 0

                    elecrate = self.df.loc[
                                   self.df[SET_LIMIT + "{}".format(year)] == 1, SET_POP + "{}".format(year)].sum() / \
                               self.df[SET_POP + "{}".format(year)].sum()
                else:
                    print(
                        "The electrification target set is quite low and has been reached by grid densification in already electrified areas")
                    self.df.loc[
                        (self.df[SET_ELEC_FUTURE_GRID + "{}".format(year - timestep)] == 1), SET_LIMIT + "{}".format(
                            year)] = 1
                    self.df.loc[
                        (self.df[SET_ELEC_FUTURE_GRID + "{}".format(year - timestep)] == 0), SET_LIMIT + "{}".format(
                            year)] = 0

                    elecrate = self.df.loc[
                                   self.df[SET_LIMIT + "{}".format(year)] == 1, SET_POP + "{}".format(year)].sum() / \
                               self.df[SET_POP + "{}".format(year)].sum()

            elif choice == 2:  # Prioritize grid densification/intensification (1 or 2 km).
                # Then lowest investment per capita
                self.df[SET_LIMIT + "{}".format(year)] = 0
                elecrate = 0
                min_investment = 0
                extension = 0
                iter_limit_4 = 0
                iter_limit_5 = 0
                self.df[SET_INVEST_PER_CAPITA + "{}".format(year)] = self.df[SET_INVESTMENT_COST + "{}".format(year)] / \
                                                                     self.df[SET_NEW_CONNECTIONS + "{}".format(year)]
                step_size = self.df[SET_INVEST_PER_CAPITA + "{}".format(year)].quantile(q=0.95) / 100
                densification_pop = sum(self.df[self.df[SET_ELEC_FUTURE_GRID + "{}".format(year - timestep)] == 1][
                                            SET_POP + "{}".format(year)])
                intensification_pop = sum(self.df[(self.df[SET_ELEC_FUTURE_GRID + "{}".format(year - timestep)] == 0) &
                                                  (self.df[SET_MV_DIST_PLANNED] < auto_densification)][
                                              SET_POP + "{}".format(year)])

                if (densification_pop + intensification_pop) / self.df[SET_POP + "{}".format(year)].sum() < eleclimit:
                    eleclimit -= densification_pop / self.df[SET_POP + "{}".format(year)].sum()
                    eleclimit -= intensification_pop / self.df[SET_POP + "{}".format(year)].sum()

                    while abs(elecrate - eleclimit) > 0.01:
                        extension = 1

                        elecrate = sum(
                            self.df[(self.df[SET_INVEST_PER_CAPITA + "{}".format(year)] < min_investment) &
                                    (self.df[SET_ELEC_FUTURE_GRID + "{}".format(year - timestep)] == 0) &
                                    (self.df[SET_MV_DIST_PLANNED] >= auto_densification)][
                                SET_POP + "{}".format(year)]) / \
                                   self.df[SET_POP + "{}".format(year)].sum()
                        if (eleclimit - elecrate > 0.01) and (iter_limit_4 < 100):
                            min_investment += step_size
                            iter_limit_4 += 1
                        elif ((elecrate - eleclimit) > 0.01) and (iter_limit_5 < 50):
                            min_investment -= 0.02 * step_size
                            iter_limit_5 += 1
                            iter_limit_4 = 100
                        else:
                            break

                    # Updating (using the SET_LIMIT function) what is electrified in the year and what is not
                    self.df.loc[(self.df[SET_ELEC_FUTURE_GRID + "{}".format(year - timestep)] == 1),
                                SET_LIMIT + "{}".format(year)] = 1

                    self.df.loc[self.df[SET_MV_DIST_PLANNED] < auto_densification, SET_LIMIT + "{}".format(year)] = 1

                    if extension == 1:
                        self.df.loc[(self.df[SET_INVEST_PER_CAPITA + "{}".format(year)] <= min_investment),
                                    SET_LIMIT + "{}".format(year)] = 1

                else:
                    print("The electrification target set is quite low,"
                          " and has been reached by grid densification/intensification")
                    self.df.loc[(self.df[SET_ELEC_FUTURE_GRID + "{}".format(year - timestep)] == 1),
                                SET_LIMIT + "{}".format(year)] = 1
                    self.df.loc[(self.df[SET_MV_DIST_PLANNED] < auto_densification), SET_LIMIT + "{}".format(year)] = 1

                elecrate = self.df.loc[self.df[SET_LIMIT + "{}".format(year)] == 1,
                                       SET_POP + "{}".format(year)].sum() / self.df[SET_POP + "{}".format(year)].sum()

            elif choice == 3:
                # Prioritize grid densification first. Then lowest investment per capita in areas close to cities.
                elecrate = 0
                min_investment = 0
                min_dist_to_cities = 1
                iter_limit_1 = 0
                iter_limit_2 = 0
                iter_limit_3 = 0

                self.df[SET_INVEST_PER_CAPITA + "{}".format(year)] = \
                    self.df[SET_INVESTMENT_COST + "{}".format(year)] / self.df[SET_NEW_CONNECTIONS + "{}".format(year)]
                step_size = self.df[SET_INVEST_PER_CAPITA + "{}".format(year)].quantile(q=0.95) / 100
                if sum(self.df[self.df[SET_ELEC_FUTURE_GRID + "{}".format(year - timestep)] == 1][
                           SET_POP + "{}".format(year)]) / \
                        self.df[SET_POP + "{}".format(year)].sum() < eleclimit:
                    eleclimit -= sum(self.df[self.df[SET_ELEC_FUTURE_GRID + "{}".format(year - timestep)] == 1][
                                         SET_POP + "{}".format(year)]) / \
                                 self.df[SET_POP + "{}".format(year)].sum()

                    while abs(elecrate - eleclimit) > 0.01:
                        elecrate = sum(self.df[(self.df[SET_INVEST_PER_CAPITA + "{}".format(year)] < min_investment) &
                                               (self.df[SET_ELEC_FUTURE_GRID + "{}".format(year - timestep)] == 0) &
                                               (self.df[SET_TRAVEL_HOURS] < min_dist_to_cities)][
                                           SET_POP + "{}".format(year)]) / \
                                   self.df[SET_POP + "{}".format(year)].sum()
                        if eleclimit - elecrate > 0.02 and iter_limit_3 < 100:
                            min_investment += step_size
                            iter_limit_3 += 1
                        elif (eleclimit - elecrate > 0.01) and (iter_limit_1 < 5):
                            min_dist_to_cities += 0.5
                            iter_limit_1 += 1
                            iter_limit_3 = 0
                            min_investment = 0
                        elif ((eleclimit - elecrate) < -0.01) and (iter_limit_2 < 100):
                            min_investment -= step_size / 20
                            iter_limit_2 += 1
                        else:
                            break

                    # Updating (using the SET_LIMIT function) what is electrified in the year and what is not
                    self.df.loc[
                        (self.df[SET_ELEC_FUTURE_GRID + "{}".format(year - timestep)] == 1), SET_LIMIT + "{}".format(
                            year)] = 1

                    self.df.loc[(self.df[SET_INVEST_PER_CAPITA + "{}".format(year)] <= min_investment) &
                                (self.df[SET_ELEC_FUTURE_GRID + "{}".format(year - timestep)] == 0) &
                                (self.df[SET_TRAVEL_HOURS] <= min_dist_to_cities), SET_LIMIT + "{}".format(year)] = 1

                    self.df.loc[(self.df[SET_INVEST_PER_CAPITA + "{}".format(year)] <= min_investment) &
                                (self.df[SET_ELEC_FUTURE_GRID + "{}".format(year - timestep)] == 0) &
                                (self.df[SET_TRAVEL_HOURS] > min_dist_to_cities), SET_LIMIT + "{}".format(year)] = 0

                    self.df.loc[(self.df[SET_INVEST_PER_CAPITA + "{}".format(year)] > min_investment) &
                                (self.df[SET_ELEC_FUTURE_GRID + "{}".format(
                                    year - timestep)] == 0), SET_LIMIT + "{}".format(year)] = 0

                else:
                    print("The electrification target set is quite low,"
                          " and has been reached by grid densification in already electrified areas")
                    self.df.loc[(self.df[SET_ELEC_FUTURE_GRID + "{}".format(year - timestep)] == 1),
                                SET_LIMIT + "{}".format(year)] = 1
                    self.df.loc[(self.df[SET_ELEC_FUTURE_GRID + "{}".format(year - timestep)] == 0),
                                SET_LIMIT + "{}".format(year)] = 0

                elecrate = self.df.loc[self.df[SET_LIMIT + "{}".format(year)] == 1,
                                       SET_POP + "{}".format(year)].sum() / self.df[SET_POP + "{}".format(year)].sum()

            elif choice == 4:
                self.df[SET_LIMIT + "{}".format(year)] = 0

                self.df.loc[(self.df[SET_ELEC_FUTURE_GRID + "{}".format(year - timestep)] == 1),SET_LIMIT + "{}".format(year)] = 1
                self.df.loc[self.df[SET_MV_DIST_PLANNED] < auto_densification, SET_LIMIT + "{}".format(year)] = 1
                elecrate = self.df.loc[self.df[SET_LIMIT + "{}".format(year)] == 1,
                                       SET_POP + "{}".format(year)].sum() / self.df[SET_POP + "{}".format(year)].sum()

            elif choice == 5:  # Prioritize grid densification first, then lowest investment per capita combined with travel time
                elecrate = 0
                min_investment = 0
                min_dist_to_cities = max(self.df[SET_TRAVEL_HOURS])
                iter_limit_1 = 0
                iter_limit_2 = 0
                iter_limit_3 = 0
                iter_limit_4 = 0
                self.df[SET_INVEST_PER_CAPITA + "{}".format(year)] = self.df[SET_INVESTMENT_COST + "{}".format(year)] / \
                                                                     self.df[SET_NEW_CONNECTIONS + "{}".format(year)]
                step_size = self.df[SET_INVEST_PER_CAPITA + "{}".format(year)].quantile(q=0.95) / 20
                travel_time_step = self.df[SET_TRAVEL_HOURS].quantile(q=1) / 100
                if sum(self.df[self.df[SET_ELEC_FUTURE_GRID + "{}".format(year - timestep)] == 1][
                           SET_POP + "{}".format(year)]) / \
                        self.df[SET_POP + "{}".format(year)].sum() < eleclimit:
                    eleclimit -= sum(self.df[self.df[SET_ELEC_FUTURE_GRID + "{}".format(year - timestep)] == 1][
                                         SET_POP + "{}".format(year)]) / \
                                 self.df[SET_POP + "{}".format(year)].sum()

                    while abs(elecrate - eleclimit) > 0.01:
                        elecrate = sum(self.df[(self.df[SET_INVEST_PER_CAPITA + "{}".format(year)] < min_investment) &
                                               (self.df[SET_ELEC_FUTURE_GRID + "{}".format(year - timestep)] == 0) &
                                               (self.df[SET_TRAVEL_HOURS] < min_dist_to_cities)][
                                           SET_POP + "{}".format(year)]) / \
                                   self.df[SET_POP + "{}".format(year)].sum()
                        if (eleclimit - elecrate > 0.01) and (iter_limit_3 < 20):
                            min_investment += step_size
                            iter_limit_3 += 1
                        elif ((elecrate - eleclimit) > 0.01) and (iter_limit_4 < 100):
                            min_dist_to_cities -= travel_time_step
                            iter_limit_4 += 1
                        else:
                            break

                    # Updating (using the SET_LIMIT function) what is electrified in the year and what is not
                    self.df.loc[
                        (self.df[SET_ELEC_FUTURE_GRID + "{}".format(year - timestep)] == 1), SET_LIMIT + "{}".format(
                            year)] = 1

                    self.df.loc[(self.df[SET_INVEST_PER_CAPITA + "{}".format(year)] <= min_investment) &
                                (self.df[SET_ELEC_FUTURE_GRID + "{}".format(year - timestep)] == 0) &
                                (self.df[SET_TRAVEL_HOURS] <= min_dist_to_cities), SET_LIMIT + "{}".format(year)] = 1

                    self.df.loc[(self.df[SET_INVEST_PER_CAPITA + "{}".format(year)] <= min_investment) &
                                (self.df[SET_ELEC_FUTURE_GRID + "{}".format(year - timestep)] == 0) &
                                (self.df[SET_TRAVEL_HOURS] > min_dist_to_cities), SET_LIMIT + "{}".format(year)] = 0

                    self.df.loc[(self.df[SET_INVEST_PER_CAPITA + "{}".format(year)] > min_investment) &
                                (self.df[SET_ELEC_FUTURE_GRID + "{}".format(
                                    year - timestep)] == 0), SET_LIMIT + "{}".format(year)] = 0

                    elecrate = self.df.loc[
                                   self.df[SET_LIMIT + "{}".format(year)] == 1, SET_POP + "{}".format(year)].sum() / \
                               self.df[SET_POP + "{}".format(year)].sum()
                else:
                    print(
                        "The electrification target set is quite low and has been reached by grid densification in already electrified areas")
                    self.df.loc[
                        (self.df[SET_ELEC_FUTURE_GRID + "{}".format(year - timestep)] == 1), SET_LIMIT + "{}".format(
                            year)] = 1
                    self.df.loc[
                        (self.df[SET_ELEC_FUTURE_GRID + "{}".format(year - timestep)] == 0), SET_LIMIT + "{}".format(
                            year)] = 0

                    elecrate = self.df.loc[
                                   self.df[SET_LIMIT + "{}".format(year)] == 1, SET_POP + "{}".format(year)].sum() / \
                               self.df[SET_POP + "{}".format(year)].sum()


            # TODO The algorithm needs to be updated
            # Review is required
            elif choice == 99:
                elecrate = 0
                min_investment = 0
                self.df[SET_INVEST_PER_CAPITA + "{}".format(year)] = self.df[SET_INVESTMENT_COST + "{}".format(year)] / \
                                                                     self.df[SET_NEW_CONNECTIONS + "{}".format(year)]
                while elecrate < eleclimit:
                    elecrate = sum(self.df[self.df[SET_INVEST_PER_CAPITA + "{}".format(year)] < min_investment][
                                       SET_POP + "{}".format(year)]) / self.df[SET_POP + "{}".format(year)].sum()
                    if elecrate < 0.999 * eleclimit:
                        min_investment += 1
                    else:
                        break
                self.df.loc[
                    self.df[SET_INVEST_PER_CAPITA + "{}".format(year)] <= min_investment, SET_LIMIT + "{}".format(
                        year)] = 1
                self.df.loc[
                    self.df[SET_INVEST_PER_CAPITA + "{}".format(year)] > min_investment, SET_LIMIT + "{}".format(
                        year)] = 0

            # TODO The algorithm needs to be updated
            # Review is required
            elif choice == 99:  # Prioritize lowest LCOE (Not tested)
                elecrate = 1
                min_lcoe = 0
                while elecrate >= eleclimit:
                    elecrate = sum(self.df[self.df[SET_MIN_OVERALL_LCOE + "{}".format(year)] < min_lcoe][
                                       SET_POP + "{}".format(year)]) / self.df[SET_POP + "{}".format(year)].sum()
                    if elecrate > 1.001 * eleclimit:
                        min_lcoe += 0.001
                    else:
                        break
                self.df.loc[
                    self.df[SET_MIN_OVERALL_LCOE + "{}".format(year)] <= min_lcoe, SET_LIMIT + "{}".format(year)] = 1
                self.df.loc[
                    self.df[SET_MIN_OVERALL_LCOE + "{}".format(year)] > min_lcoe, SET_LIMIT + "{}".format(year)] = 0

        print("The electrification rate achieved in {} is {:.1f} %".format(year, (elecrate - elec_limit_origin)*100))

    def final_decision(self, mg_hydro_calc, mg_wind_calc, mg_pv_calc, sa_pv_calc, mg_diesel_calc,
                       sa_diesel_calc, grid_calc, hybrid_1, hybrid_2, hybrid_3, hybrid_4, hybrid_5, year, end_year,
                       timestep):
        """" ... """

        logging.info('Determine final electrification decision')

        # Defining what is electrified in a given year by the grid after prioritization process has finished
        self.df[SET_ELEC_FINAL_GRID + "{}".format(year)] = 0
        self.df.loc[
            (self.df[SET_ELEC_FUTURE_GRID + "{}".format(year)] == 1), SET_ELEC_FINAL_GRID + "{}".format(year)] = 1
        self.df.loc[
            (self.df[SET_LIMIT + "{}".format(year)] == 1) & (self.df[SET_MIN_OVERALL_CODE + "{}".format(year)] == 1) & (
                    self.df[SET_GRID_REACH_YEAR] <= year), SET_ELEC_FINAL_GRID + "{}".format(year)] = 1
        # Define what is electrified in a given year by off-grid after prioritization process has finished
        self.df[SET_ELEC_FINAL_OFFGRID + "{}".format(year)] = 0
        self.df.loc[(self.df[SET_ELEC_FUTURE_OFFGRID + "{}".format(year)] == 1) & (
                self.df[SET_MIN_OVERALL_CODE + "{}".format(year)] != 1), SET_ELEC_FINAL_OFFGRID + "{}".format(
            year)] = 1
        self.df.loc[(self.df[SET_LIMIT + "{}".format(year)] == 1) & (
                self.df[SET_ELEC_FINAL_GRID + "{}".format(year)] == 0), SET_ELEC_FINAL_OFFGRID + "{}".format(
            year)] = 1
        self.df.loc[
            (self.df[SET_LIMIT + "{}".format(year)] == 1) & (self.df[SET_MIN_OVERALL_CODE + "{}".format(year)] == 0) & (
                    self.df[SET_GRID_REACH_YEAR] > year), SET_ELEC_FINAL_OFFGRID + "{}".format(year)] = 1

        #
        self.df.loc[
            (self.df[SET_LIMIT + "{}".format(year)] == 1) & (self.df[SET_ELEC_FINAL_GRID + "{}".format(year)] == 1),
            SET_ELEC_FINAL_CODE + "{}".format(year)] = 1

        self.df.loc[
            (self.df[SET_LIMIT + "{}".format(year)] == 1) & (self.df[SET_ELEC_FINAL_OFFGRID + "{}".format(year)] == 1),
            SET_ELEC_FINAL_CODE + "{}".format(year)] = self.df[SET_MIN_OFFGRID_CODE + "{}".format(year)]

        self.df.loc[(self.df[SET_LIMIT + "{}".format(year)] == 0),
                    SET_ELEC_FINAL_CODE + "{}".format(year)] = 99

        logging.info('Calculate new capacity')

        # self.df[SET_NEW_CAPACITY + "{}".format(year)] = self.df.apply(
        #     lambda row: pv_diesel_hyb.get_lcoe(energy_per_cell=row[SET_ENERGY_PER_CELL + "{}".format(year)],
        #                                        total_energy_per_cell=row[SET_TOTAL_ENERGY_PER_CELL],
        #                                        prev_code=row[SET_ELEC_FINAL_CODE + "{}".format(year - timestep)],
        #                                        conf_status=row[SET_CONFLICT],
        #                                        start_year=year - timestep,
        #                                        end_year=end_year,
        #                                        people=row[SET_POP + "{}".format(year)],
        #                                        new_connections=row[SET_NEW_CONNECTIONS + "{}".format(year)],
        #                                        num_people_per_hh=row[SET_NUM_PEOPLE_PER_HH],
        #                                        travel_hours=row[SET_TRAVEL_HOURS],
        #                                        ghi=row[SET_GHI],
        #                                        urban=row[SET_URBAN],
        #                                        hybrid_1=hybrid_1,
        #                                        hybrid_2=hybrid_2,
        #                                        hybrid_3=hybrid_3,
        #                                        hybrid_4=hybrid_4,
        #                                        hybrid_5=hybrid_5,
        #                                        tier=row[SET_TIER],
        #                                        grid_cell_area=row[SET_GRID_CELL_AREA],
        #                                        mg_hybrid=True,
        #                                        get_capacity=True
        #                                        )
        #     if row[SET_ELEC_FINAL_CODE + "{}".format(year)] == 8 else 0,
        #     axis=1)

        self.df.loc[self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 1, SET_NEW_CAPACITY + "{}".format(year)] = (
                (self.df[SET_ENERGY_PER_CELL + "{}".format(year)]) /
                (HOURS_PER_YEAR * grid_calc.capacity_factor * grid_calc.base_to_peak_load_ratio *
                 (1 - grid_calc.distribution_losses)))

        self.df.loc[self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 7, SET_NEW_CAPACITY + "{}".format(year)] = (
                (self.df[SET_ENERGY_PER_CELL + "{}".format(year)]) /
                (HOURS_PER_YEAR * mg_hydro_calc.capacity_factor * mg_hydro_calc.base_to_peak_load_ratio *
                 (1 - mg_hydro_calc.distribution_losses)))

        self.df.loc[self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 5, SET_NEW_CAPACITY + "{}".format(year)] = (
                (self.df[SET_ENERGY_PER_CELL + "{}".format(year)]) /
                (HOURS_PER_YEAR * (self.df[SET_GHI] / HOURS_PER_YEAR) * mg_pv_calc.base_to_peak_load_ratio *
                 (1 - mg_pv_calc.distribution_losses)))

        self.df.loc[self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 6, SET_NEW_CAPACITY + "{}".format(year)] = (
                (self.df[SET_ENERGY_PER_CELL + "{}".format(year)]) /
                (HOURS_PER_YEAR * self.df[SET_WINDCF] * mg_wind_calc.base_to_peak_load_ratio *
                 (1 - mg_wind_calc.distribution_losses)))

        self.df.loc[self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 4, SET_NEW_CAPACITY + "{}".format(year)] = (
                (self.df[SET_ENERGY_PER_CELL + "{}".format(year)]) /
                (HOURS_PER_YEAR * mg_diesel_calc.capacity_factor * mg_diesel_calc.base_to_peak_load_ratio *
                 (1 - mg_diesel_calc.distribution_losses)))

        self.df.loc[self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 2, SET_NEW_CAPACITY + "{}".format(year)] = (
                (self.df[SET_ENERGY_PER_CELL + "{}".format(year)]) /
                (HOURS_PER_YEAR * sa_diesel_calc.capacity_factor * sa_diesel_calc.base_to_peak_load_ratio *
                 (1 - sa_diesel_calc.distribution_losses)))

        self.df.loc[self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 3, SET_NEW_CAPACITY + "{}".format(year)] = (
                (self.df[SET_ENERGY_PER_CELL + "{}".format(year)]) /
                (HOURS_PER_YEAR * (self.df[SET_GHI] / HOURS_PER_YEAR) * sa_pv_calc.base_to_peak_load_ratio *
                 (1 - sa_pv_calc.distribution_losses)))

        self.df.loc[self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 99, SET_NEW_CAPACITY + "{}".format(year)] = 0

        def res_investment_cost(row):
            min_code = row[SET_ELEC_FINAL_CODE + "{}".format(year)]

            if min_code == 2:
                return sa_diesel_calc.get_lcoe(energy_per_cell=row[SET_ENERGY_PER_CELL + "{}".format(year)],
                                               start_year=year - timestep,
                                               end_year=end_year,
                                               people=row[SET_POP + "{}".format(year)],
                                               new_connections=row[SET_NEW_CONNECTIONS + "{}".format(year)],
                                               total_energy_per_cell=row[SET_TOTAL_ENERGY_PER_CELL],
                                               prev_code=row[SET_ELEC_FINAL_CODE + "{}".format(year - timestep)],
                                               num_people_per_hh=row[SET_NUM_PEOPLE_PER_HH],
                                               grid_cell_area=row[SET_GRID_CELL_AREA],
                                               travel_hours=row[SET_TRAVEL_HOURS],
                                               conf_status=row[SET_CONFLICT],
                                               get_investment_cost=True)

            elif min_code == 3:
                return sa_pv_calc.get_lcoe(energy_per_cell=row[SET_ENERGY_PER_CELL + "{}".format(year)],
                                           start_year=year - timestep,
                                           end_year=end_year,
                                           people=row[SET_POP + "{}".format(year)],
                                           new_connections=row[SET_NEW_CONNECTIONS + "{}".format(year)],
                                           total_energy_per_cell=row[SET_TOTAL_ENERGY_PER_CELL],
                                           prev_code=row[SET_ELEC_FINAL_CODE + "{}".format(year - timestep)],
                                           num_people_per_hh=row[SET_NUM_PEOPLE_PER_HH],
                                           grid_cell_area=row[SET_GRID_CELL_AREA],
                                           capacity_factor=row[SET_GHI] / HOURS_PER_YEAR,
                                           conf_status=row[SET_CONFLICT],
                                           get_investment_cost=True)

            elif min_code == 6:
                return mg_wind_calc.get_lcoe(energy_per_cell=row[SET_ENERGY_PER_CELL + "{}".format(year)],
                                             start_year=year - timestep,
                                             end_year=end_year,
                                             people=row[SET_POP + "{}".format(year)],
                                             new_connections=row[SET_NEW_CONNECTIONS + "{}".format(year)],
                                             total_energy_per_cell=row[SET_TOTAL_ENERGY_PER_CELL],
                                             prev_code=row[SET_ELEC_FINAL_CODE + "{}".format(year - timestep)],
                                             num_people_per_hh=row[SET_NUM_PEOPLE_PER_HH],
                                             grid_cell_area=row[SET_GRID_CELL_AREA],
                                             capacity_factor=row[SET_WINDCF],
                                             conf_status=row[SET_CONFLICT],
                                             get_investment_cost=True)

            elif min_code == 4:
                return mg_diesel_calc.get_lcoe(energy_per_cell=row[SET_ENERGY_PER_CELL + "{}".format(year)],
                                               start_year=year - timestep,
                                               end_year=end_year,
                                               people=row[SET_POP + "{}".format(year)],
                                               new_connections=row[SET_NEW_CONNECTIONS + "{}".format(year)],
                                               total_energy_per_cell=row[SET_TOTAL_ENERGY_PER_CELL],
                                               prev_code=row[SET_ELEC_FINAL_CODE + "{}".format(year - timestep)],
                                               num_people_per_hh=row[SET_NUM_PEOPLE_PER_HH],
                                               grid_cell_area=row[SET_GRID_CELL_AREA],
                                               travel_hours=row[SET_TRAVEL_HOURS],
                                               conf_status=row[SET_CONFLICT],
                                               get_investment_cost=True)

            elif min_code == 5:
                return mg_pv_calc.get_lcoe(energy_per_cell=row[SET_ENERGY_PER_CELL + "{}".format(year)],
                                           start_year=year - timestep,
                                           end_year=end_year,
                                           people=row[SET_POP + "{}".format(year)],
                                           new_connections=row[SET_NEW_CONNECTIONS + "{}".format(year)],
                                           total_energy_per_cell=row[SET_TOTAL_ENERGY_PER_CELL],
                                           prev_code=row[SET_ELEC_FINAL_CODE + "{}".format(year - timestep)],
                                           num_people_per_hh=row[SET_NUM_PEOPLE_PER_HH],
                                           grid_cell_area=row[SET_GRID_CELL_AREA],
                                           capacity_factor=row[SET_GHI] / HOURS_PER_YEAR,
                                           conf_status=row[SET_CONFLICT],
                                           get_investment_cost=True)

            elif min_code == 7:
                return mg_hydro_calc.get_lcoe(energy_per_cell=row[SET_ENERGY_PER_CELL + "{}".format(year)],
                                              start_year=year - timestep,
                                              end_year=end_year,
                                              people=row[SET_POP + "{}".format(year)],
                                              new_connections=row[SET_NEW_CONNECTIONS + "{}".format(year)],
                                              total_energy_per_cell=row[SET_TOTAL_ENERGY_PER_CELL],
                                              prev_code=row[SET_ELEC_FINAL_CODE + "{}".format(year - timestep)],
                                              num_people_per_hh=row[SET_NUM_PEOPLE_PER_HH],
                                              grid_cell_area=row[SET_GRID_CELL_AREA],
                                              conf_status=row[SET_CONFLICT],
                                              mv_line_length=row[SET_HYDRO_DIST],
                                              get_investment_cost=True)

            elif min_code == 1:
                return grid_calc.get_lcoe(energy_per_cell=row[SET_ENERGY_PER_CELL + "{}".format(year)],
                                          start_year=year - timestep,
                                          end_year=end_year,
                                          people=row[SET_POP + "{}".format(year)],
                                          new_connections=row[SET_NEW_CONNECTIONS + "{}".format(year)],
                                          total_energy_per_cell=row[SET_TOTAL_ENERGY_PER_CELL],
                                          prev_code=row[SET_ELEC_FINAL_CODE + "{}".format(year - timestep)],
                                          num_people_per_hh=row[SET_NUM_PEOPLE_PER_HH],
                                          grid_cell_area=row[SET_GRID_CELL_AREA],
                                          conf_status=row[SET_CONFLICT],
                                          additional_mv_line_length=row[SET_MIN_GRID_DIST + "{}".format(year)],
                                          elec_loop=row[SET_ELEC_ORDER + "{}".format(year)],
                                          get_investment_cost=True)
            else:
                return 0

            logging.info('Calculate investment cost')
            self.df[SET_INVESTMENT_COST + "{}".format(year)] = self.df.apply(res_investment_cost, axis=1)

        def res_investment_cost_lv(row):
            min_code = row[SET_ELEC_FINAL_CODE + "{}".format(year)]
            if min_code == 1:
                return grid_calc.get_lcoe(energy_per_cell=row[SET_ENERGY_PER_CELL + "{}".format(year)],
                                          start_year=year - timestep,
                                          end_year=end_year,
                                          people=row[SET_POP + "{}".format(year)],
                                          new_connections=row[SET_NEW_CONNECTIONS + "{}".format(year)],
                                          total_energy_per_cell=row[SET_TOTAL_ENERGY_PER_CELL],
                                          prev_code=row[SET_ELEC_FINAL_CODE + "{}".format(year - timestep)],
                                          num_people_per_hh=row[SET_NUM_PEOPLE_PER_HH],
                                          grid_cell_area=row[SET_GRID_CELL_AREA],
                                          conf_status=row[SET_CONFLICT],
                                          additional_mv_line_length=row[SET_MIN_GRID_DIST + "{}".format(year)],
                                          elec_loop=row[SET_ELEC_ORDER + "{}".format(year)],
                                          get_investment_cost_lv=True)
            else:
                return 0

        # logging.info('Calculate LV investment cost')
        # self.df['InvestmentCostLV' + "{}".format(year)] = self.df.apply(res_investment_cost_lv, axis=1)

        def res_investment_cost_mv(row):
            min_code = row[SET_ELEC_FINAL_CODE + "{}".format(year)]
            if min_code == 1:
                return grid_calc.get_lcoe(energy_per_cell=row[SET_ENERGY_PER_CELL + "{}".format(year)],
                                          start_year=year - timestep,
                                          end_year=end_year,
                                          people=row[SET_POP + "{}".format(year)],
                                          new_connections=row[SET_NEW_CONNECTIONS + "{}".format(year)],
                                          total_energy_per_cell=row[SET_TOTAL_ENERGY_PER_CELL],
                                          prev_code=row[SET_ELEC_FINAL_CODE + "{}".format(year - timestep)],
                                          num_people_per_hh=row[SET_NUM_PEOPLE_PER_HH],
                                          grid_cell_area=row[SET_GRID_CELL_AREA],
                                          conf_status=row[SET_CONFLICT],
                                          additional_mv_line_length=row[SET_MIN_GRID_DIST + "{}".format(year)],
                                          elec_loop=row[SET_ELEC_ORDER + "{}".format(year)],
                                          get_investment_cost_mv=True)
            else:
                return 0

        # logging.info('Calculate MV investment cost')
        # self.df['InvestmentCostMV' + "{}".format(year)] = self.df.apply(res_investment_cost_mv, axis=1)

        def res_investment_cost_hv(row):
            min_code = row[SET_ELEC_FINAL_CODE + "{}".format(year)]
            if min_code == 1:
                return grid_calc.get_lcoe(energy_per_cell=row[SET_ENERGY_PER_CELL + "{}".format(year)],
                                          start_year=year - timestep,
                                          end_year=end_year,
                                          people=row[SET_POP + "{}".format(year)],
                                          new_connections=row[SET_NEW_CONNECTIONS + "{}".format(year)],
                                          total_energy_per_cell=row[SET_TOTAL_ENERGY_PER_CELL],
                                          prev_code=row[SET_ELEC_FINAL_CODE + "{}".format(year - timestep)],
                                          num_people_per_hh=row[SET_NUM_PEOPLE_PER_HH],
                                          grid_cell_area=row[SET_GRID_CELL_AREA],
                                          conf_status=row[SET_CONFLICT],
                                          additional_mv_line_length=row[SET_MIN_GRID_DIST + "{}".format(year)],
                                          elec_loop=row[SET_ELEC_ORDER + "{}".format(year)],
                                          get_investment_cost_hv=True)
            else:
                return 0

        # logging.info('Calculate HV investment cost')
        # self.df['InvestmentCostHV' + "{}".format(year)] = self.df.apply(res_investment_cost_hv, axis=1)

        def res_investment_cost_transformer(row):
            min_code = row[SET_ELEC_FINAL_CODE + "{}".format(year)]
            if min_code == 1:
                return grid_calc.get_lcoe(energy_per_cell=row[SET_ENERGY_PER_CELL + "{}".format(year)],
                                          start_year=year - timestep,
                                          end_year=end_year,
                                          people=row[SET_POP + "{}".format(year)],
                                          new_connections=row[SET_NEW_CONNECTIONS + "{}".format(year)],
                                          total_energy_per_cell=row[SET_TOTAL_ENERGY_PER_CELL],
                                          prev_code=row[SET_ELEC_FINAL_CODE + "{}".format(year - timestep)],
                                          num_people_per_hh=row[SET_NUM_PEOPLE_PER_HH],
                                          grid_cell_area=row[SET_GRID_CELL_AREA],
                                          conf_status=row[SET_CONFLICT],
                                          additional_mv_line_length=row[SET_MIN_GRID_DIST + "{}".format(year)],
                                          elec_loop=row[SET_ELEC_ORDER + "{}".format(year)],
                                          get_investment_cost_transformer=True)
            else:
                return 0

        # logging.info('Calculate transformer investment cost')
        # self.df['InvestmentCostTransformer' + "{}".format(year)] = self.df.apply(res_investment_cost_transformer, axis=1)

        def res_investment_cost_connection(row):
            min_code = row[SET_ELEC_FINAL_CODE + "{}".format(year)]
            if min_code == 1:
                return grid_calc.get_lcoe(energy_per_cell=row[SET_ENERGY_PER_CELL + "{}".format(year)],
                                          start_year=year - timestep,
                                          end_year=end_year,
                                          people=row[SET_POP + "{}".format(year)],
                                          new_connections=row[SET_NEW_CONNECTIONS + "{}".format(year)],
                                          total_energy_per_cell=row[SET_TOTAL_ENERGY_PER_CELL],
                                          prev_code=row[SET_ELEC_FINAL_CODE + "{}".format(year - timestep)],
                                          num_people_per_hh=row[SET_NUM_PEOPLE_PER_HH],
                                          grid_cell_area=row[SET_GRID_CELL_AREA],
                                          conf_status=row[SET_CONFLICT],
                                          additional_mv_line_length=row[SET_MIN_GRID_DIST + "{}".format(year)],
                                          elec_loop=row[SET_ELEC_ORDER + "{}".format(year)],
                                          get_investment_cost_connection=True)
            else:
                return 0

        # logging.info('Calculate connection investment cost')
        #  self.df['InvestmentCostConnection' + "{}".format(year)] = self.df.apply(res_investment_cost_connection, axis=1)

        def infrastructure_cost(row):
            if row[SET_NEW_CONNECTIONS + "{}".format(year)] > 0 and row[SET_ELEC_FINAL_CODE + "{}".format(year)] == 1:
                return (row['InvestmentCostLV' + "{}".format(year)]
                        + row['InvestmentCostMV' + "{}".format(year)] + row['InvestmentCostHV' + "{}".format(year)]
                        + row['InvestmentCostTransformer' + "{}".format(year)] +
                        row['InvestmentCostConnection' + "{}".format(year)]) / (
                               row[SET_NEW_CONNECTIONS + "{}".format(year)] / row[SET_NUM_PEOPLE_PER_HH])
            else:
                return 0

        # logging.info('Calculating average infrastructure cost for grid connection')
        # self.df['InfrastructureCapitaCost' + "{}".format(year)] = self.df.apply(infrastructure_cost, axis=1)

    def calc_summaries(self, df_summary, sumtechs, year):

        """The next section calculates the summaries for technology split,
        consumption added and total investment cost"""

        logging.info('Calculate summaries')

        # Population Summaries
        df_summary[year][sumtechs[0]] = sum(self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 1) &
                                                        (self.df[SET_LIMIT + "{}".format(year)] == 1)]
                                            [SET_POP + "{}".format(year)])

        df_summary[year][sumtechs[1]] = sum(self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 2) &
                                                        (self.df[SET_LIMIT + "{}".format(year)] == 1)]
                                            [SET_POP + "{}".format(year)])

        df_summary[year][sumtechs[2]] = sum(self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 3) &
                                                        (self.df[SET_LIMIT + "{}".format(year)] == 1) & (
                                                                self.df[SET_POP + "{}".format(year)] > 0)]
                                            [SET_POP + "{}".format(year)])

        df_summary[year][sumtechs[3]] = sum(self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 4) &
                                                        (self.df[SET_LIMIT + "{}".format(year)] == 1)]
                                            [SET_POP + "{}".format(year)])

        df_summary[year][sumtechs[4]] = sum(self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 5) &
                                                        (self.df[SET_LIMIT + "{}".format(year)] == 1)]
                                            [SET_POP + "{}".format(year)])

        df_summary[year][sumtechs[5]] = sum(self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 6) &
                                                        (self.df[SET_LIMIT + "{}".format(year)] == 1)]
                                            [SET_POP + "{}".format(year)])

        df_summary[year][sumtechs[6]] = sum(self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 7) &
                                                        (self.df[SET_LIMIT + "{}".format(year)] == 1)]
                                            [SET_POP + "{}".format(year)])

        df_summary[year][sumtechs[7]] = sum(self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 8) &
                                                        (self.df[SET_LIMIT + "{}".format(year)] == 1)]
                                            [SET_POP + "{}".format(year)])

        # New_Connection Summaries
        df_summary[year][sumtechs[8]] = sum(self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 1) &
                                                        (self.df[SET_LIMIT + "{}".format(year)] == 1)]
                                            [SET_NEW_CONNECTIONS + "{}".format(year)])

        df_summary[year][sumtechs[9]] = sum(self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 2) &
                                                        (self.df[SET_LIMIT + "{}".format(year)] == 1)]
                                            [SET_NEW_CONNECTIONS + "{}".format(year)])

        df_summary[year][sumtechs[10]] = sum(self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 3) &
                                                         (self.df[SET_LIMIT + "{}".format(year)] == 1) & (
                                                                 self.df[SET_POP + "{}".format(year)] > 0)]
                                             [SET_NEW_CONNECTIONS + "{}".format(year)])

        df_summary[year][sumtechs[11]] = sum(self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 4) &
                                                         (self.df[SET_LIMIT + "{}".format(year)] == 1)]
                                             [SET_NEW_CONNECTIONS + "{}".format(year)])

        df_summary[year][sumtechs[12]] = sum(self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 5) &
                                                         (self.df[SET_LIMIT + "{}".format(year)] == 1)]
                                             [SET_NEW_CONNECTIONS + "{}".format(year)])

        df_summary[year][sumtechs[13]] = sum(self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 6) &
                                                         (self.df[SET_LIMIT + "{}".format(year)] == 1)]
                                             [SET_NEW_CONNECTIONS + "{}".format(year)])

        df_summary[year][sumtechs[14]] = sum(self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 7) &
                                                         (self.df[SET_LIMIT + "{}".format(year)] == 1)]
                                             [SET_NEW_CONNECTIONS + "{}".format(year)])

        df_summary[year][sumtechs[15]] = sum(self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 8) &
                                                         (self.df[SET_LIMIT + "{}".format(year)] == 1)]
                                             [SET_NEW_CONNECTIONS + "{}".format(year)])

        # Capacity Summaries
        df_summary[year][sumtechs[16]] = sum(self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 1) &
                                                         (self.df[SET_LIMIT + "{}".format(year)] == 1)]
                                             [SET_NEW_CAPACITY + "{}".format(year)])

        df_summary[year][sumtechs[17]] = sum(self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 2) &
                                                         (self.df[SET_LIMIT + "{}".format(year)] == 1)]
                                             [SET_NEW_CAPACITY + "{}".format(year)])

        df_summary[year][sumtechs[18]] = sum(self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 3) &
                                                         (self.df[SET_LIMIT + "{}".format(year)] == 1) & (
                                                                 self.df[SET_POP + "{}".format(year)] > 0)]
                                             [SET_NEW_CAPACITY + "{}".format(year)])

        df_summary[year][sumtechs[19]] = sum(self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 4) &
                                                         (self.df[SET_LIMIT + "{}".format(year)] == 1)]
                                             [SET_NEW_CAPACITY + "{}".format(year)])

        df_summary[year][sumtechs[20]] = sum(self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 5) &
                                                         (self.df[SET_LIMIT + "{}".format(year)] == 1)]
                                             [SET_NEW_CAPACITY + "{}".format(year)])

        df_summary[year][sumtechs[21]] = sum(self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 6) &
                                                         (self.df[SET_LIMIT + "{}".format(year)] == 1)]
                                             [SET_NEW_CAPACITY + "{}".format(year)])

        df_summary[year][sumtechs[22]] = sum(self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 7) &
                                                         (self.df[SET_LIMIT + "{}".format(year)] == 1)]
                                             [SET_NEW_CAPACITY + "{}".format(year)])

        df_summary[year][sumtechs[23]] = sum(self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 8) &
                                                         (self.df[SET_LIMIT + "{}".format(year)] == 1)]
                                             [SET_NEW_CAPACITY + "{}".format(year)])

        # Investment Summaries
        df_summary[year][sumtechs[24]] = sum(self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 1) &
                                                         (self.df[SET_LIMIT + "{}".format(year)] == 1)]
                                             [SET_INVESTMENT_COST + "{}".format(year)])

        df_summary[year][sumtechs[25]] = sum(self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 2) &
                                                         (self.df[SET_LIMIT + "{}".format(year)] == 1)]
                                             [SET_INVESTMENT_COST + "{}".format(year)])

        df_summary[year][sumtechs[26]] = sum(self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 3) &
                                                         (self.df[SET_LIMIT + "{}".format(year)] == 1) & (
                                                                 self.df[SET_POP + "{}".format(year)] > 0)]
                                             [SET_INVESTMENT_COST + "{}".format(year)])

        df_summary[year][sumtechs[27]] = sum(self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 4) &
                                                         (self.df[SET_LIMIT + "{}".format(year)] == 1)]
                                             [SET_INVESTMENT_COST + "{}".format(year)])

        df_summary[year][sumtechs[28]] = sum(self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 5) &
                                                         (self.df[SET_LIMIT + "{}".format(year)] == 1)]
                                             [SET_INVESTMENT_COST + "{}".format(year)])

        df_summary[year][sumtechs[29]] = sum(self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 6) &
                                                         (self.df[SET_LIMIT + "{}".format(year)] == 1)]
                                             [SET_INVESTMENT_COST + "{}".format(year)])

        df_summary[year][sumtechs[30]] = sum(self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 7) &
                                                         (self.df[SET_LIMIT + "{}".format(year)] == 1)]
                                             [SET_INVESTMENT_COST + "{}".format(year)])

        df_summary[year][sumtechs[31]] = sum(self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 8) &
                                                         (self.df[SET_LIMIT + "{}".format(year)] == 1)]
                                             [SET_INVESTMENT_COST + "{}".format(year)])

        df_summary[year][sumtechs[32]] = min(self.df[SET_POP + "{}".format(year)])
        df_summary[year][sumtechs[33]] = max(self.df[SET_POP + "{}".format(year)])
        df_summary[year][sumtechs[34]] = min(self.df[SET_GRID_CELL_AREA])
        df_summary[year][sumtechs[35]] = max(self.df[SET_GRID_CELL_AREA])
        df_summary[year][sumtechs[36]] = min(self.df['CurrentMVLineDist'])
        df_summary[year][sumtechs[37]] = max(self.df['CurrentMVLineDist'])
        df_summary[year][sumtechs[38]] = min(self.df[SET_ROAD_DIST])
        df_summary[year][sumtechs[39]] = max(self.df[SET_ROAD_DIST])
        df_summary[year][sumtechs[40]] = min(
            (self.df[SET_INVESTMENT_COST + "{}".format(year)]) / (self.df[SET_NEW_CONNECTIONS + "{}".format(year)]))
        df_summary[year][sumtechs[41]] = max(
            (self.df[SET_INVESTMENT_COST + "{}".format(year)]) / (self.df[SET_NEW_CONNECTIONS + "{}".format(year)]))
