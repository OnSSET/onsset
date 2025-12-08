import logging
import time
from math import log, pi
from typing import Dict
import scipy.spatial
from scipy.optimize import differential_evolution, Bounds

try:
    from hybrids import *
except:
    from onsset.hybrids import *

try:
    from hybrids_wind import *
except:
    from onsset.hybrids_wind import *

import geojson
from shapely.geometry import shape, Point
import geopandas as gpd
import numpy as np
import pandas as pd
from numba import njit
import shapely.geometry
import geojson

logging.basicConfig(format='%(asctime)s\t\t%(message)s', level=logging.ERROR)
logger = logging.getLogger(__name__)

# Columns in settlements file must match these exactly
SET_COUNTRY = 'Country'  # This cannot be changed, lots of code will break
SET_X_DEG = 'X_deg'  # Coordinates in degrees
SET_Y_DEG = 'Y_deg'
SET_POP = 'Pop'  # Population in people per point (equally, people per km2)
SET_POP_CALIB = 'PopStartYear'  # Calibrated population to reference year, same units
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
SET_road_dist_classified = 'RoadDistClassified'
SET_substation_dist_classified = 'SubstationDistClassified'
SET_elevation_classified = 'ElevationClassified'
SET_slope_classified = 'SlopeClassified'
SET_land_cover_classified = 'LandCoverClassified'
SET_combined_classification = 'GridClassification'
SET_GRID_PENALTY = 'GridPenalty'
SET_URBAN = 'IsUrban'  # Whether the site is urban (0 or 1)
SET_ENERGY_PER_CELL = 'EnergyPerSettlement'
SET_NUM_PEOPLE_PER_HH = 'NumPeoplePerHH'
SET_ELEC_CURRENT = 'ElecStart'  # If the site is currently electrified (0 or 1)
SET_NEW_CONNECTIONS = 'NewConnections'  # Number of new people with electricity connections
SET_MIN_GRID_DIST = 'NewGridExtensionDist'
SET_LCOE_GRID = 'Grid'  # All LCOE's in USD/kWh
SET_LCOE_SA_PV = 'SA_PV'
SET_LCOE_SA_DIESEL = 'SA_Diesel'
SET_LCOE_MG_WIND = 'MG_Wind'
SET_LCOE_MG_DIESEL = 'MG_Diesel'
SET_LCOE_MG_PV = 'MG_PV'
SET_LCOE_MG_HYDRO = 'MG_Hydro'
SET_LCOE_MG_PV_HYBRID = 'MG_PVHybrid'
SET_MIN_OFFGRID = 'Minimum_Tech_Off_grid'  # The technology with lowest lcoe (excluding grid)
SET_MIN_OVERALL = 'MinimumOverall'  # Same as above, but including grid
SET_MIN_OFFGRID_LCOE = 'Minimum_LCOE_Off_grid'  # The lcoe value for minimum tech
SET_MIN_OVERALL_LCOE = 'MinimumOverallLCOE'  # The lcoe value for overall minimum
SET_MIN_OVERALL_CODE = 'MinimumOverallCode'  # And a code from 1 - 7 to represent that option
SET_MIN_CATEGORY = 'MinimumCategory'  # The category with minimum lcoe (grid, minigrid or standalone)
SET_NEW_CAPACITY = 'NewCapacity'  # Capacity in kW
SET_INVESTMENT_COST = 'InvestmentCost'  # The investment cost in USD
SET_ELEC_ORDER = "ElectrificationOrder"
SET_LIMIT = "ElecStatusIn"
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
SET_MTFtier = "ResidentialDemandTier"
SET_TIER = 'Tier'
SET_INVEST_PER_CONNECTION = "InvestmentPerConnection"
SET_CALIB_GRID_DIST = 'GridDistCalibElec'
SET_HH_DEMAND = 'PerHouseholdDemand'
SET_RESIDENTIAL_TIER = 'ResidentialDemandTier'
SET_MIN_TD_DIST = 'minTDdist'
SET_SA_DIESEL_FUEL = 'SADieselFuelCost'
SET_MG_DIESEL_FUEL = 'MGDieselFuelCost'
SET_MG_DIST = 'MGDist'
SET_GRID_RELIABILITY = 'GridReliability'  # To Calculate grid reliability
SET_UNMET_DEMAND = 'UnmetDemand'  # To Calculate grid reliability
SET_BACKUP_CAP = "BackupCap"
SET_BACKUP_LCOE = "BackUpLCOE"
SET_AVERAGE_TO_PEAK = "AverageToPeakLoadRatio"

# General
LHV_DIESEL = 9.9445485  # (kWh/l) lower heating value
HOURS_PER_YEAR = 8760


class Technology:
    """
    Used to define the parameters for each electricity access technology, and to calculate the LCOE depending on
    input parameters.
    """

    def __init__(self,
                 tech_life=0,  # in years
                 distribution_losses=0,  # percentage
                 connection_cost_per_hh=0,  # USD/hh
                 om_costs=0.0,  # OM costs as percentage of capital costs
                 capital_cost={float("inf"): 0},  # USD/kW
                 capacity_factor=0.9,  # percentage
                 grid_penalty_ratio=1,  # multiplier
                 efficiency=1.0,  # percentage
                 diesel_price=0.0,  # USD/litre
                 grid_price=0.0,  # USD/kWh for grid electricity
                 standalone=False,
                 mini_grid=False,
                 existing_grid_cost_ratio=0.,  # percentage
                 grid_capacity_investment=0.0,  # USD/kW for on-grid capacity investments (excluding grid itself)
                 diesel_truck_consumption=0,  # litres/hour
                 diesel_truck_volume=0,  # litres
                 om_of_td_lines=0,
                 hybrid=False,
                 hybrid_investment=0,
                 hybrid_capacity=0,
                 hybrid_fuel=0,
                 discount_rate=0.08,
                 cnse=0,
                 mv_line_type=33,
                 mv_line_amperage_limit=8.0,
                 mv_line_cost=7000,
                 mv_line_max_length=50,
                 lv_line_type=0.240,
                 lv_line_cost=4250,
                 lv_line_max_length=0.5,
                 service_transf_type=50,
                 service_transf_cost=4250,
                 max_nodes_per_serv_trans=300,
                 mv_lv_sub_station_type=400,
                 mv_lv_sub_station_cost=10000,
                 base_to_peak_load_ratio=1
                 ):  # percentage

        self.distribution_losses = distribution_losses
        self.base_to_peak_load_ratio = base_to_peak_load_ratio
        self.connection_cost_per_hh = connection_cost_per_hh
        self.tech_life = tech_life
        self.om_costs = om_costs
        self.capital_cost = capital_cost
        self.capacity_factor = capacity_factor
        self.grid_penalty_ratio = grid_penalty_ratio
        self.efficiency = efficiency
        self.diesel_price = diesel_price
        self.grid_price = grid_price
        self.standalone = standalone
        self.mini_grid = mini_grid
        self.existing_grid_cost_ratio = existing_grid_cost_ratio
        self.grid_capacity_investment = grid_capacity_investment
        self.diesel_truck_consumption = diesel_truck_consumption
        self.diesel_truck_volume = diesel_truck_volume
        self.om_of_td_lines = om_of_td_lines
        self.hybrid = hybrid
        self.hybrid_investment = hybrid_investment
        self.hybrid_capacity = hybrid_capacity
        self.hybrid_fuel = hybrid_fuel
        self.discount_rate = discount_rate
        self.cnse=cnse  # cost of non served energy to include penalty in grid lcoe for low reliability grid
        self.mv_line_type = mv_line_type  # kV
        self.mv_line_amperage_limit = mv_line_amperage_limit  # Ampere (A)
        self.mv_line_cost = mv_line_cost  # $/km  for 11-33 kV
        self.mv_line_max_length = mv_line_max_length
        self.lv_line_type = lv_line_type  # kV
        self.lv_line_cost = lv_line_cost  # $/km
        self.lv_line_max_length = lv_line_max_length  # km
        self.service_transf_type = service_transf_type  # kVa
        self.service_transf_cost = service_transf_cost  # $/unit
        self.max_nodes_per_serv_trans = max_nodes_per_serv_trans  # max number of nodes served by a service transformer
        self.mv_lv_sub_station_type = mv_lv_sub_station_type  # kVa
        self.mv_lv_sub_station_cost = mv_lv_sub_station_cost  # $/unit

    @classmethod
    def set_default_values(cls, base_year, start_year, end_year, hv_line_type=69, hv_line_cost=53000,
                           hv_mv_sub_station_cost=25000, hv_mv_substation_type=10000, power_factor=0.9, load_moment=9643):
        """Initialises the class with parameter values common to all Technologies
        """
        cls.base_year = base_year
        cls.start_year = start_year
        cls.end_year = end_year

        # RUN_PARAM: Here are the assumptions related to cost and physical properties of grid extension elements
        #cls.discount_rate = discount_rate
        cls.hv_line_type = hv_line_type  # kV
        cls.hv_line_cost = hv_line_cost  # $/km for 69kV
        cls.hv_mv_substation_type = hv_mv_substation_type  # kVA
        cls.hv_mv_sub_station_cost = hv_mv_sub_station_cost  # $/unit
        cls.power_factor = power_factor
        cls.load_moment = load_moment  # for 50mm aluminum conductor under 5% voltage drop (kW m)

    def get_lcoe(self, energy_per_cell, people, num_people_per_hh, start_year, end_year, new_connections,
                 total_energy_per_cell, prev_code, grid_cell_area, base_to_peak_load_ratio, sa_diesel_calc={}, unmet_demand=0, additional_mv_line_length=0.0,
                 capacity_factor=0.9, grid_penalty_ratio=1, fuel_cost=0, elec_loop=0,
                 productive_nodes=0,  additional_transformer=0, penalty=1, get_max_dist=False, fuel_cost_settlement=0,
                 grid_reliability_option='None'):
        """Calculates the LCOE depending on the parameters.

        Parameters
        ----------
        people : float or pandas.Series
            Number of people in settlement
        new_connections : float or pandas.Series
            Number of new people in settlement to connect
        prev_code : int or pandas.Series
            Code representation of previous supply technology in settlement
        total_energy_per_cell : float or pandas.Series
            Total annual energy demand in cell, including already met demand
        energy_per_cell : float or pandas.Series
            Annual energy demand in cell, excluding already met demand
        num_people_per_hh : float or pandas.Series
            Number of people per household in settlement
        grid_cell_area : float or pandas.Series
            Area of settlement (km2)
        additional_mv_line_length : float or pandas.Series
            Distance to connect the settlement
        additional_transformer : int
            If a transformer is needed on other end to connect to HV line
        productive_nodes : int or pandas.Series
            Additional connections (schools, health facilities, shops)
        elec_loop : int or pandas.Series
            Round of extension in grid extension algorithm
        penalty : float or pandas.Series
            Cost penalty factor for T&D network, e.g. https://www.mdpi.com/2071-1050/12/3/777
        start_year : int
        end_year : int
        capacity_factor : float or pandas.Series
        grid_penalty_ratio : float or pandas.Series
        fuel_cost : float or pandas.Series

        Returns
        -------
        lcoe or discounted investment cost
        """

        if type(people) == int or type(people) == float or type(people) == np.float64:
            if people == 0:
                # If there are no people, set the people low (prevent div/0 error) and continue.
                people = 0.00001
        else:
            people = np.maximum(people, 0.00001)

        if type(energy_per_cell) == int or type(energy_per_cell) == float or type(energy_per_cell) == np.float64:
            if energy_per_cell == 0:
                # If there is no demand, set the demand low (prevent div/0 error) and continue.
                energy_per_cell = 0.000000000001
        else:
            energy_per_cell = np.maximum(energy_per_cell, 0.000000000001)

        grid_penalty_ratio = 1

        generation_per_year, peak_load, td_investment_cost, hv, mv, lv, service_transf, connection = \
            self.td_network_cost(people,
                                 new_connections,
                                 prev_code,
                                 total_energy_per_cell,
                                 energy_per_cell,
                                 num_people_per_hh,
                                 grid_cell_area,
                                 base_to_peak_load_ratio,
                                 additional_mv_line_length,
                                 additional_transformer,
                                 productive_nodes,
                                 elec_loop,
                                 penalty
                                 )

        generation_per_year = pd.Series(generation_per_year)
        peak_load = pd.Series(peak_load)
        td_investment_cost = pd.Series(td_investment_cost)

        td_investment_cost = td_investment_cost # * grid_penalty_ratio
        td_om_cost = td_investment_cost * self.om_of_td_lines * penalty
        installed_capacity = peak_load / capacity_factor

        cap_cost = td_investment_cost * 0
        cost_dict_list = self.capital_cost.keys()
        cost_dict_list = sorted(cost_dict_list)
        for key in cost_dict_list:
            if self.standalone:
                cap_cost.loc[((installed_capacity / (people / num_people_per_hh)) < key) & (cap_cost == 0)] = \
                    self.capital_cost[key]
            else:
                cap_cost.loc[(installed_capacity < key) & (cap_cost == 0)] = self.capital_cost[key]

        capital_investment = installed_capacity * cap_cost  # * penalty
        total_om_cost = td_om_cost + (cap_cost * penalty * self.om_costs * installed_capacity)
        total_investment_cost = td_investment_cost + capital_investment

        if self.grid_price > 0:
            fuel_cost = self.grid_price

        # Perform the time-value LCOE calculation
        project_life = end_year - start_year + 1
        reinvest_year = 0
        step = 0
        # If the technology life is less than the project life, we will have to invest twice to buy it again
        if self.tech_life + step < project_life:
            reinvest_year = self.tech_life + step

        year = np.arange(project_life)
        el_gen = np.outer(np.asarray(generation_per_year), np.ones(project_life))
        for s in range(step):
            el_gen[:, s] = 0
        discount_factor = (1 + self.discount_rate) ** year
        investments = np.zeros(project_life)
        investments[step] = 1
        # Calculate the year of re-investment if tech_life is smaller than project life
        if reinvest_year:
            investments[reinvest_year] = 1
        investments = np.outer(total_investment_cost, investments)

        grid_capacity_investments = np.zeros(project_life)
        grid_capacity_investments[step] = 1
        # Calculate the year of re-investment if tech_life is smaller than project life
        if reinvest_year:
            grid_capacity_investments[reinvest_year] = 1
        grid_capacity_investments = np.outer(peak_load * self.grid_capacity_investment, grid_capacity_investments)

        # Calculate salvage value if tech_life is bigger than project life
        salvage = np.zeros(project_life)
        if reinvest_year > 0:
            used_life = (project_life - step) - self.tech_life
        else:
            used_life = project_life - step - 1
        salvage[-1] = 1
        salvage = np.outer(total_investment_cost * (1 - used_life / self.tech_life), salvage)

        operation_and_maintenance = np.ones(project_life)
        for s in range(step):
            operation_and_maintenance[s] = 0
        operation_and_maintenance = np.outer(total_om_cost, operation_and_maintenance)
        fuel = np.outer(np.asarray(generation_per_year), np.zeros(project_life))
        for p in range(project_life):
            fuel[:, p] = el_gen[:, p] * fuel_cost

        if grid_reliability_option == 'DieselBackup':
            total_costs_reliability, discounted_costs_backup, backup_capacity = \
                sa_diesel_calc.get_lcoe_backup(project_life, step, new_connections, num_people_per_hh, energy_per_cell,
                                               unmet_demand, fuel_cost_settlement, base_to_peak_load_ratio)
        elif grid_reliability_option == 'CNSE':
            discounted_costs_backup = np.outer(unmet_demand, 0)
            total_costs_reliability = np.outer(unmet_demand, self.cnse)
            backup_capacity = 0
        else: # if grid_reliability_option == 'None'
            discounted_costs_backup = np.outer(unmet_demand, 0)
            total_costs_reliability = np.outer(unmet_demand, 0)
            backup_capacity = 0

        discounted_investments = investments / discount_factor
        discounted_grid_capacity_investments = grid_capacity_investments / discount_factor

        investment_cost = (np.sum(investments, axis=1) + np.sum(grid_capacity_investments, axis=1) + np.sum(discounted_costs_backup, axis=1))
        discounted_investment_cost = (np.sum(discounted_investments, axis=1) + np.sum(discounted_grid_capacity_investments, axis=1) + np.sum(discounted_costs_backup, axis=1))
        discounted_costs = (investments + operation_and_maintenance + fuel - salvage + total_costs_reliability) / discount_factor
        #investment_cost = np.sum(discounted_investments, axis=1) + np.sum(discounted_grid_capacity_investments, axis=1)
        #discounted_costs = (investments + operation_and_maintenance + fuel - salvage) / discount_factor
        discounted_generation = el_gen / discount_factor
        lcoe = np.sum(discounted_costs, axis=1) / np.sum(discounted_generation, axis=1)
        # lcoe = pd.DataFrame(lcoe[:, np.newaxis])
        # investment_cost = pd.DataFrame(investment_cost[:, np.newaxis])
        # installed_capacity = pd.DataFrame(installed_capacity[:, np.newaxis])

        lcoe = pd.DataFrame(lcoe)
        investment_cost = pd.DataFrame(investment_cost)
        discounted_investment_cost = pd.DataFrame(discounted_investment_cost)
        installed_capacity = pd.DataFrame(installed_capacity + backup_capacity)

        #if self.hybrid:
        #    print('Hybrid: ', lcoe, lcoe + pd.DataFrame(self.hybrid_fuel))
        #if get_max_dist:
        #    print('Grid: ', lcoe)

        if get_max_dist:
            return lcoe, investment_cost, installed_capacity, peak_load
        elif self.hybrid:
            hybrid_capacity = pd.DataFrame(self.hybrid_capacity)
            return lcoe + pd.DataFrame(self.hybrid_fuel), pd.DataFrame(investment_cost[0] + self.hybrid_investment), hybrid_capacity
        else:
            return lcoe, investment_cost, installed_capacity

    def get_lcoe_backup(self, project_life, step, people, num_people_per_hh, demand, unmet_demand, fuel_cost_settlement,
                        base_to_peak_load_ratio):

        if type(unmet_demand) == int or type(unmet_demand) == float or type(unmet_demand) == np.float64:
            if unmet_demand == 0:
                # If there is no demand, set the demand low (prevent div/0 error) and continue.
                unmet_demand = 0.000000000001
        else:
            unmet_demand = np.maximum(unmet_demand, 0.000000000001)

        reinvest_year = 0

        cap_cost = unmet_demand * 0
        cost_dict_list = self.capital_cost.keys()
        cost_dict_list = sorted(cost_dict_list)

        # Sizing diesel generator
        installed_capacity_diesel_genset = demand / self.capacity_factor / HOURS_PER_YEAR / base_to_peak_load_ratio

        for key in cost_dict_list:
            if self.standalone:
                cap_cost.loc[((installed_capacity_diesel_genset / (people / num_people_per_hh)) < key) & (cap_cost == 0)] = \
                    self.capital_cost[key]
            else:
                cap_cost.loc[(installed_capacity_diesel_genset < key) & (cap_cost == 0)] = self.capital_cost[key]

        # If the technology life is less than the project life, we will have to invest twice to buy it again
        if self.tech_life + step < project_life:
            reinvest_year = self.tech_life + step

        year = np.arange(project_life)
        discount_factor = (1 + self.discount_rate) ** year

        capital_cost_diesel_genset = np.zeros(project_life)
        capital_cost_diesel_genset[0] = 1
        total_investment_cost = installed_capacity_diesel_genset * cap_cost

        # Calculate the year of re-investment if tech_life is smaller than project life
        if reinvest_year:
            capital_cost_diesel_genset[reinvest_year] = 1
        capital_cost_diesel_genset = np.outer(total_investment_cost, capital_cost_diesel_genset)

        # Diesel usage and O&M
        diesel_gen_set_generation = unmet_demand / self.efficiency  # kWh
        fuel_gen_set = diesel_gen_set_generation * fuel_cost_settlement  # kWh * USD/kWh
        life_time_diesel = np.ones(project_life)

        total_om_cost_diesel = np.outer(
            installed_capacity_diesel_genset * self.om_costs * cap_cost, life_time_diesel)

        fuel_gen_set = np.outer(fuel_gen_set, life_time_diesel)

        if reinvest_year > 0:
            used_life = (project_life - step) - self.tech_life
        else:
            used_life = project_life - step - 1

        salvage_diesel_genset = np.zeros(project_life)
        salvage_diesel_genset[-1] = 1
        salvage_diesel_genset = np.outer(installed_capacity_diesel_genset * cap_cost * (
                    1 - used_life / self.tech_life), salvage_diesel_genset)

        total_diesel_genset = capital_cost_diesel_genset + fuel_gen_set + total_om_cost_diesel - salvage_diesel_genset

        discounted_total_diesel_genset = capital_cost_diesel_genset / discount_factor

        return total_diesel_genset, discounted_total_diesel_genset, installed_capacity_diesel_genset

    def transmission_network(self, peak_load, additional_mv_line_length=0, additional_transformer=0):
        """This method calculates the required components for connecting the settlement
        Settlements can be connected to grid or a hydropower source
        This includes potentially HV lines, MV lines and substations

        Arguments
        ---------
        peak_load : float
            Peak load in the settlement (kW)
        additional_mv_line_length : float
            Distance to connect the settlement
        additional_transformer : int
            If a transformer is needed on other end to connect to HV line

        Notes
        -----
        Based on: https://www.mdpi.com/1996-1073/12/7/1395
        """

        mv_km = 0
        hv_km = 0
        no_of_hv_mv_subs = 0
        no_of_mv_lv_subs = 0

        if not self.standalone:
            # Sizing HV/MV
            hv_to_mv_lines = self.hv_line_cost / self.mv_line_cost
            max_mv_load = self.mv_line_amperage_limit * self.mv_line_type * hv_to_mv_lines

            mv_amperage = self.service_transf_type / self.mv_line_type # ToDo check
            no_of_mv_lines = np.ceil(peak_load / (mv_amperage * self.mv_line_type))
            hv_amperage = self.hv_mv_substation_type / self.hv_line_type
            no_of_hv_lines = np.ceil(peak_load / (hv_amperage * self.hv_line_type))

            mv_km = np.where((peak_load <= max_mv_load) & (additional_mv_line_length < self.mv_line_max_length),
                             additional_mv_line_length * no_of_mv_lines,
                             0)

            hv_km = np.where((peak_load <= max_mv_load) & (additional_mv_line_length < self.mv_line_max_length),
                             0,
                             additional_mv_line_length * no_of_hv_lines)

            if additional_transformer:
                no_of_hv_mv_subs = np.ceil(peak_load / self.hv_mv_substation_type)  # ToDo if hv_km

        return hv_km, mv_km, no_of_hv_mv_subs, no_of_mv_lv_subs

    def distribution_network(self, connections, energy_per_cell, grid_cell_area, base_to_peak_load_ratio,
                             productive_nodes=0):
        """This method calculates the required components for the distribution network
        This includes potentially MV lines, LV lines and service transformers

        Arguments
        ---------
        connections : pd.Series
            Number of people in settlement
        energy_per_cell : pd.Series
            Annual energy demand in settlement (kWh)
        grid_cell_area : pd.Series
            Area of settlement (km2)
        productive_nodes : int
            Additional connections (schools, health facilities, shops)

        Notes
        -----
        Based on: https://www.mdpi.com/1996-1073/12/7/1395
        """

        consumption = energy_per_cell  # kWh/year
        average_load = consumption / (1 - self.distribution_losses) / HOURS_PER_YEAR  # kW
        peak_load = average_load / base_to_peak_load_ratio  # kW

        if self.standalone:
            cluster_mv_lines_length = 0
            lv_km = 0
            no_of_service_transf = 0
            total_nodes = 0
        else:
            s_max = peak_load / self.power_factor
            max_transformer_area = pi * self.lv_line_max_length ** 2
            total_nodes = connections + productive_nodes

            no_of_service_transf = np.ceil(
                np.maximum(s_max / self.service_transf_type, np.maximum(total_nodes / self.max_nodes_per_serv_trans,
                                                                        grid_cell_area / max_transformer_area)))

            transformer_radius = ((grid_cell_area / no_of_service_transf) / pi) ** 0.5
            transformer_load = peak_load / no_of_service_transf
            cluster_radius = (grid_cell_area / pi) ** 0.5

            # Sizing lv lines in settlement
            cluster_lv_lines_length = np.where(2 / 3 * cluster_radius * transformer_load * 1000 < self.load_moment,
                                               2 / 3 * cluster_radius * no_of_service_transf,
                                               0)

            cluster_mv_lines_length = np.where(2 / 3 * cluster_radius * transformer_load * 1000 >= self.load_moment,
                                               2 * transformer_radius * no_of_service_transf,
                                               0)

            hh_area = grid_cell_area / total_nodes
            hh_diameter = 2 * ((hh_area / pi) ** 0.5)

            transformer_lv_lines_length = hh_diameter * total_nodes

            lv_km = cluster_lv_lines_length + transformer_lv_lines_length

        return cluster_mv_lines_length, lv_km, no_of_service_transf, consumption, peak_load, total_nodes

    def td_network_cost(self, people, new_connections, prev_code, total_energy_per_cell, energy_per_cell,
                        num_people_per_hh, grid_cell_area, base_to_peak_load_ratio, additional_mv_line_length=0,
                        additional_transformer=0, productive_nodes=0, elec_loop=0, penalty=1):
        """Calculates all the transmission and distribution network components

        Parameters
        ----------
        people : float
            Number of people in settlement
        new_connections : float
            Number of new people in settlement to connect
        prev_code : int
            Code representation of previous supply technology in settlement
        total_energy_per_cell : float
            Total annual energy demand in cell, including already met demand
        energy_per_cell : float
            Annual energy demand in cell, excluding already met demand
        num_people_per_hh : float
            Number of people per household in settlement
        grid_cell_area : float
            Area of settlement (km2)
        additional_mv_line_length : float
            Distance to connect the settlement
        additional_transformer : int
            If a transformer is needed on other end to connect to HV line
        productive_nodes : int
            Additional connections (schools, health facilities, shops)
        elec_loop : int
            Round of extension in grid extension algorithm
        penalty : float
            Cost penalty factor for T&D network, e.g. https://www.mdpi.com/2071-1050/12/3/777
        """

        # Start by calculating the distribution network required to meet all of the demand
        cluster_mv_lines_length_total, cluster_lv_lines_length_total, no_of_service_transf_total, \
            generation_per_year_total, peak_load_total, total_nodes_total = \
            self.distribution_network(round(people / num_people_per_hh), total_energy_per_cell, grid_cell_area,
                                      base_to_peak_load_ratio, productive_nodes)

        # Next calculate the network that is already there
        cluster_mv_lines_length_existing, cluster_lv_lines_length_existing, no_of_service_transf_existing, \
            generation_per_year_existing, peak_load_existing, total_nodes_existing = \
            self.distribution_network(np.maximum((round(people / num_people_per_hh) - new_connections), 1),
                                      (total_energy_per_cell - energy_per_cell), grid_cell_area,
                                      base_to_peak_load_ratio, productive_nodes)

        # Then calculate the difference between the two
        mv_lines_distribution_length_additional = \
            np.maximum(cluster_lv_lines_length_total - cluster_lv_lines_length_existing, 0)
        total_lv_lines_length_additional = \
            np.maximum(cluster_lv_lines_length_total - cluster_lv_lines_length_existing, 0)
        num_transformers_additional = np.maximum(no_of_service_transf_total - no_of_service_transf_existing, 0)
        generation_per_year_additional = np.maximum(generation_per_year_total - generation_per_year_existing, 0)
        peak_load_additional = np.maximum(peak_load_total - peak_load_existing, 0)
        total_nodes_additional = np.maximum(total_nodes_total - total_nodes_existing, 0)

        # Examine if there are any MV lines in the distribution network, used to determine transformer type
        mv_distribution = np.where(mv_lines_distribution_length_additional > 0, True, False)  # ToDo check if needed

        # Then calculate the transmission network (HV or MV lines plus transformers) using the same methodology
        hv_lines_total_length_total, mv_lines_connection_length_total, no_of_hv_mv_substation_total, \
            no_of_mv_lv_substation_total = \
            self.transmission_network(peak_load_total, additional_mv_line_length, additional_transformer)

        hv_lines_total_length_existing, mv_lines_connection_length_existing, no_of_hv_mv_substation_existing, \
            no_of_mv_lv_substation_existing = \
            self.transmission_network(peak_load_existing, additional_mv_line_length, additional_transformer)

        hv_lines_total_length_additional = np.maximum(hv_lines_total_length_total - hv_lines_total_length_existing, 0)
        mv_lines_connection_length_additional = \
            np.maximum(mv_lines_connection_length_total - mv_lines_connection_length_existing, 0)
        no_of_hv_mv_substation_additional = \
            np.maximum(no_of_hv_mv_substation_total - no_of_hv_mv_substation_existing, 0)
        no_of_mv_lv_substation_additional = \
            np.maximum(no_of_mv_lv_substation_total - no_of_mv_lv_substation_existing, 0)

        # If no distribution network is present, perform the calculations only once
        mv_lines_distribution_length_new, total_lv_lines_length_new, num_transformers_new, generation_per_year_new, \
            peak_load_new, total_nodes_new = self.distribution_network(round(people / num_people_per_hh),
                                                                       energy_per_cell, grid_cell_area,
                                                                       base_to_peak_load_ratio, productive_nodes)
        # ToDo this can be removed

        mv_distribution = np.where(mv_lines_distribution_length_new > 0, True, False)

        hv_lines_total_length_new, mv_lines_connection_length_new, no_of_hv_mv_substation_new, \
            no_of_mv_lv_substation_new, = \
            self.transmission_network(peak_load_new, additional_mv_line_length, additional_transformer)

        mv_lines_distribution_length = np.where((prev_code != 3) & (prev_code != 99),
                                                mv_lines_distribution_length_additional,
                                                mv_lines_distribution_length_new)

        hv_lines_total_length = np.where((prev_code < 3),
                                         hv_lines_total_length_additional,
                                         hv_lines_total_length_new)

        mv_lines_connection_length = np.where((prev_code < 3),
                                              mv_lines_connection_length_additional,
                                              mv_lines_connection_length_new)

        total_lv_lines_length = np.where((prev_code != 3) & (prev_code != 99),
                                         total_lv_lines_length_additional,
                                         total_lv_lines_length_new)

        num_transformers = np.where((prev_code != 3) & (prev_code != 99),
                                    num_transformers_additional,
                                    num_transformers_new)

        total_nodes = np.where((prev_code != 3) & (prev_code != 99),
                               total_nodes_additional,
                               total_nodes_new)

        no_of_hv_mv_substation = np.where((prev_code != 3) & (prev_code != 99),
                                          no_of_hv_mv_substation_additional,
                                          no_of_hv_mv_substation_new)

        no_of_mv_lv_substation = np.where((prev_code != 3) & (prev_code != 99),
                                          no_of_mv_lv_substation_additional,
                                          no_of_mv_lv_substation_new)

        generation_per_year = np.where((prev_code != 3) & (prev_code != 99),
                                       generation_per_year_additional,
                                       generation_per_year_new)

        peak_load = np.where(prev_code != 99,
                             peak_load_additional,
                             peak_load_new)

        if self.mini_grid:
            power_house = np.where((prev_code != 5) & (prev_code != 6) & (prev_code != 7),
                                    20000,
                                    0)
        else:
            power_house = 0

        td_investment_cost = (hv_lines_total_length * self.hv_line_cost +
                              mv_lines_connection_length * self.mv_line_cost +
                              total_lv_lines_length * self.lv_line_cost +
                              mv_lines_distribution_length * self.mv_line_cost +
                              num_transformers * self.service_transf_cost +
                              total_nodes * self.connection_cost_per_hh +
                              no_of_hv_mv_substation * self.hv_mv_sub_station_cost) + power_house

        return generation_per_year, peak_load, td_investment_cost, hv_lines_total_length * self.hv_line_cost, \
            mv_lines_distribution_length * self.mv_line_cost, total_lv_lines_length * self.lv_line_cost,\
            num_transformers * self.service_transf_cost, total_nodes * self.connection_cost_per_hh


class SettlementProcessor:
    """
    Processes the DataFrame and adds all the columns to determine the cheapest option and the final costs and summaries
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

    @staticmethod
    def _diesel_fuel_cost_calculator(diesel_price: float,
                                     diesel_truck_consumption: float,
                                     diesel_truck_volume: float,
                                     traveltime: np.ndarray,
                                     efficiency: float):
        """We apply the Szabo formula to calculate the transport cost for the diesel

        Formulae is::

            p = (p_d + 2*p_d*consumption*time/volume)*(1/mu)*(1/LHVd)

        Arguments
        ---------
        diesel_price: float
        diesel_truck_consumption: float
        diesel_truck_volume: float
        traveltime: numpy.ndarray
        efficiency: float

        Returns
        -------
        numpy.ndarray
        """
        return (diesel_price + 2 * diesel_price * diesel_truck_consumption *
                traveltime / diesel_truck_volume) / LHV_DIESEL / efficiency

    def compute_diesel_cost(self,
                            dataframe: pd.DataFrame,
                            sa_diesel_cost: Dict,
                            mg_diesel_cost: Dict,
                            year: int):
        """Calculate diesel fuel cost

        Arguments
        ---------
        dataframe: pandas.DataFrame
        sa_diesel_cost: Dict
        mg_diesel_cost: Dict
        year: int

        Returns
        -------
        pandas.DataFrame
        """
        df = dataframe.copy(deep=True)
        travel_time = df[SET_TRAVEL_HOURS].values

        df[SET_SA_DIESEL_FUEL + "{}".format(year)] = self._diesel_fuel_cost_calculator(
            diesel_price=sa_diesel_cost['diesel_price'],
            diesel_truck_volume=sa_diesel_cost['diesel_truck_volume'],
            diesel_truck_consumption=sa_diesel_cost['diesel_truck_consumption'],
            efficiency=sa_diesel_cost['efficiency'],
            traveltime=travel_time)

        df[SET_MG_DIESEL_FUEL + "{}".format(year)] = self._diesel_fuel_cost_calculator(
            diesel_price=mg_diesel_cost['diesel_price'],
            diesel_truck_volume=mg_diesel_cost['diesel_truck_volume'],
            diesel_truck_consumption=mg_diesel_cost['diesel_truck_consumption'],
            efficiency=mg_diesel_cost['efficiency'],
            traveltime=travel_time)

        return df.drop(columns=SET_TRAVEL_HOURS)

    def diesel_cost_columns(self, sa_diesel_cost: Dict[str, float],
                            mg_diesel_cost: Dict[str, float], year: int):
        """Calculate diesel fuel cost based on TravelHours column

        Arguments
        ---------
        sa_diesel_cost: Dict
        mg_diesel_cost: Dict
        year: int

        Returns
        -------
        """
        diesel_cost = self.compute_diesel_cost(self.df[[SET_TRAVEL_HOURS]],
                                               sa_diesel_cost, mg_diesel_cost, year)

        self.df = self.df.join(diesel_cost)

    def conditioning(self):

        columns = ['GridCellArea', 'Country', 'ElecPop', 'IsUrban', 'NightLights', 'Pop', 'id',
                   'GHI', 'TravelHours', 'WindVel', 'ResidentialDemandTierCustom',
                   'CurrentHVLineDist',
                   'Admin_1', 'SubstationDist',
                   'PlannedHVLineDist', 'PlannedMVLineDist', 'CurrentMVLineDist', 'TransformerDist', 'Hydropower',
                   'HydropowerDist', 'HydropowerFID', 'HealthDemand', 'EducationDemand',
                   'AgriDemand',
                   'CommercialDemand', 'RoadDist', 'MGDist', 'X_deg', 'Y_deg']

        self.df['ElectrificationOrder'] = 0
        self.df['PerHouseholdDemand'] = 0

        for c in columns:
            if c in self.df.columns:
                if self.df[c].isnull().values.any():
                    if c in ['LandCover', 'Country', 'ResidentialDemandTierCustom', 'ResidentialDemandTierCustomUrban',
                             'ResidentialDemandTierCustomRural', 'ResidentialDemandTier1',
                             'ResidentialDemandTier2',
                             'ResidentialDemandTier3', 'ResidentialDemandTier4', 'ResidentialDemandTier5']:
                        self.df[c].fillna(self.df[c].mode()[0], inplace=True)
                        print(c + " contains null values. Filling with most common")

                    elif c in ['GHI', 'TravelTime', 'WindVel', 'TravelHours']:
                        self.df[c].fillna(self.df[c].mean(), inplace=True)
                        print(c + " contains null values. Filling with mean")

                    elif c in ['NightLights', 'ElecPop', 'IsUrban', 'Elevation', 'Slope', 'Hydropower', 'HealthDemand',
                               'EducationDemand', 'AgriDemand', 'CommercialDemand', 'Conflict', 'ElectrificationOrder',
                               'RoadDist']:
                        self.df[c].fillna(0, inplace=True)
                        print(c + " contains null values. Filling with 0")

                    elif c in ['HydropowerDist', 'HydropowerFID']:
                        self.df[c].fillna(9999, inplace=True)
                        print(c + " contains null values. Filling with 9999")

                    elif c in ['GridCellArea', 'Pop', 'id', 'Admin_1', 'PlannedHVLineDist', 'SubstationDist',
                               'PlannedMVLineDist', 'CurrentMVLineDist', 'TransformerDist', 'X_deg', 'Y_deg']:
                        print(c + " contains null values. Check the input file!")

            else:
                if c in ['PlannedHVLineDist', 'SubstationDist', 'PlannedMVLineDist', 'CurrentMVLineDist',
                         'TransformerDist', 'HydropowerDist', 'HydropowerFID']:
                    print(c + ' is missing from the csv file. Filling with 9999 values')
                    self.df[c] = 9999
                else:
                    print(c + ' is missing from the csv file. Filling with 0 values')
                    self.df[c] = 0

    def condition_df(self):
        """
        Do any initial data conditioning that may be required.
        """

        logging.info('Ensure that columns that are supposed to be numeric are numeric')

        columns = [SET_NIGHT_LIGHTS, SET_POP, SET_GRID_CELL_AREA, SET_ELEC_POP, SET_GHI, SET_WINDVEL, SET_TRAVEL_HOURS,
                   SET_SUBSTATION_DIST, SET_HV_DIST_CURRENT,
                   SET_HV_DIST_PLANNED, SET_MV_DIST_CURRENT, SET_MV_DIST_PLANNED, SET_ROAD_DIST, SET_X_DEG, SET_Y_DEG,
                   SET_DIST_TO_TRANS, SET_HYDRO_DIST, SET_HYDRO, SET_HYDRO_FID, SET_URBAN,
                   SET_AGRI_DEMAND, SET_HEALTH_DEMAND, SET_EDU_DEMAND, SET_COMMERCIAL_DEMAND,
                   'ResidentialDemandTierCustom', 'ResidentialDemandTier1', 'ResidentialDemandTier2',
                   'ResidentialDemandTier3', 'ResidentialDemandTier4', 'ResidentialDemandTier5']  # SET_ELEC_ORDER

        for column in columns:
            self.df[column] = pd.to_numeric(self.df[column], errors='coerce')

        logging.info('Replace null values with zero')
        self.df.fillna(0, inplace=True)

        logging.info('Sort by country, Y and X')
        self.df.sort_values(by=[SET_Y_DEG, SET_X_DEG], inplace=True)

    @staticmethod
    def classify_road_distance(road_distance):
        """Classify the road distance according to bins and labels

        Arguments
        ---------
        road_distance : list
        """
        # Define bins
        road_distance_bins = [0, 5, 10, 25, 50, float("inf")]
        # Define classifiers
        road_distance_labels = [5, 4, 3, 2, 1]

        return pd.cut(road_distance, road_distance_bins, labels=road_distance_labels, include_lowest=True).astype(float)

    @staticmethod
    def classify_substation_distance(substation_distance):
        """Classify the substation distance according to bins and labels

        Arguments
        ---------
        substation_distance : list
        """
        # Define bins
        substation_distance_bins = [0, 0.5, 1, 5, 10, float("inf")]
        # Define classifiers
        substation_distance_labels = [5, 4, 3, 2, 1]

        return pd.cut(substation_distance, substation_distance_bins, labels=substation_distance_labels).astype(float)

    @staticmethod
    def classify_elevation(elevation):
        """Classify the elevation distance according to bins and labels

        Arguments
        ---------
        elevation : list
        """

        # Define bins
        elevation_bins = [float("-inf"), 500, 1000, 2000, 3000, float("inf")]
        # Define classifiers
        elevation_labels = [5, 4, 3, 2, 1]

        return pd.cut(elevation, elevation_bins, labels=elevation_labels).astype(float)

    @staticmethod
    def classify_slope(slope):
        """Classify the slope according to bins and labels

        Arguments
        ---------
        slope : list
        """

        # Define bins
        slope_bins = [0, 10, 20, 30, 40, float("inf")]
        # Define classifiers
        slope_labels = [5, 4, 3, 2, 1]

        return pd.cut(slope, slope_bins, labels=slope_labels, include_lowest=True).astype(float)

    @staticmethod
    def classify_land_cover(column):
        """this is a different method employed to classify land cover and create new columns with the classification

        Arguments
        ---------
        column : series

        Notes
        -----
        0, 11 = 1
        6, 8 = 2
        1, 3, 5, 12, 13, 15 = 3
        2, 4 = 4
        7, 9, 10, 14, 16 = 5
        """

        land_cover_labels = [1, 3, 4, 3, 4, 3, 2, 5, 2, 5, 5, 1, 3, 3, 5, 3, 5]
        return column.apply(lambda x: land_cover_labels[int(x)])

    def grid_penalties(self, data_frame):

        """this method calculates the grid penalties in each settlement

        First step classifies the parameters and creates new columns with classification

        Second step adds the grid penalty to increase grid cost in areas that higher road distance, higher substation
        distance, unsuitable land cover, high slope angle or high elevation

        """

        logging.info('Classify road dist')
        road_dist_classified = self.classify_road_distance(data_frame[SET_ROAD_DIST])

        logging.info('Classify substation dist')
        substation_dist_classified = self.classify_substation_distance(data_frame[SET_SUBSTATION_DIST])

        logging.info('Classify elevation')
        elevation_classified = self.classify_elevation(data_frame[SET_ELEVATION])

        logging.info('Classify slope')
        slope_classified = self.classify_slope(data_frame[SET_SLOPE])

        logging.info('Classify land cover')
        land_cover_classified = self.classify_land_cover(data_frame[SET_LAND_COVER])

        logging.info('Combined classification')
        combined_classification = (0.15 * road_dist_classified +
                                   0.20 * substation_dist_classified +
                                   0.15 * elevation_classified +
                                   0.30 * slope_classified +
                                   0.20 * land_cover_classified)

        logging.info('Grid penalty')
        """this calculates the penalty from the results obtained from the combined classifications"""
        classification = combined_classification.astype(float)

        c = 1 + (np.exp(.85 * np.abs(1 - classification)) - 1) / 100

        return c

    @staticmethod
    def calc_wind_cfs(wind_vel):
        logging.info('Calculate Wind CF')

        mu = 0.97  # availability factor
        t = 8760
        p_rated = 600
        z = 55  # hub height
        zr = 80  # velocity measurement height
        es = 0.85  # losses in wind electricity
        u_arr = range(1, 26)
        p_curve = [0, 0, 0, 0, 30, 77, 135, 208, 287, 371, 450, 514, 558,
                   582, 594, 598, 600, 600, 600, 600, 600, 600, 600, 600, 600]

        wind_speed = np.where(wind_vel > 0, wind_vel, 99)

        # Adjust for the correct hub height
        alpha = (0.37 - 0.088 * np.log(wind_speed)) / (1 - 0.088 * log(zr / 10))
        u_z = wind_speed * (z / zr) ** alpha

        # Rayleigh distribution and sum of series
        rayleigh = [(pi / 2) * (u / u_z ** 2) * np.exp((-pi / 4) * (u / u_z) ** 2) for u in u_arr]
        energy_produced = sum([mu * es * t * p * r for p, r in zip(p_curve, rayleigh)])

        cf = np.where(wind_vel > 0, energy_produced / (p_rated * t), 0)
        return cf

    def prepare_wtf_tier_columns(self, tier_1, tier_2, tier_3, tier_4, tier_5):
        """ Prepares the five Residential Demand Tier Targets based customized for each country
        """
        # The MTF approach is given as per yearly household consumption
        # (BEYOND CONNECTIONS Energy Access Redefined, ESMAP, 2015).
        # Tiers in kWh/household/year

        logging.info('Populate ResidentialDemandTier columns')
        tier_num = [1, 2, 3, 4, 5]

        wb_tiers_all = {1: tier_1, 2: tier_2, 3: tier_3, 4: tier_4, 5: tier_5}

        for num in tier_num:
            self.df[SET_MTFtier + "{}".format(num)] = wb_tiers_all[num]

    def calibrate_current_pop_and_urban(self, pop_actual, urban_current):
        """
        The function calibrates population values and urban/rural split (as estimated from GIS layers) based
        on actual values provided by the user for the start year.
        """

        logging.info('Population calibration process')

        # First, calculate ratio between GIS retrieved and user provided population
        pop_ratio = pop_actual / self.df[SET_POP].sum()

        # Use above ratio to calibrate the population in a new column
        self.df[SET_POP_CALIB] = self.df[SET_POP] * pop_ratio
        pop_modelled = self.df[SET_POP_CALIB].sum()

        self.df[SET_ELEC_POP_CALIB] = self.df[SET_ELEC_POP] * pop_ratio

        logging.info('Urban/rural calibration process')
        # RUN_PARAM: This is where manual calibration of urban/rural population takes place.
        # The model uses 0, 1, 2 as follows; 0 = rural, 1 = peri-urban, 2 = urban.
        # The calibration build into the model only classifies into urban/rural

        self.df.sort_values(by=[SET_POP_CALIB], inplace=True, ascending=False)
        cumulative_urban_pop = self.df[SET_POP_CALIB].cumsum()
        self.df[SET_URBAN] = np.where(cumulative_urban_pop < (urban_current * self.df[SET_POP_CALIB].sum()), 2, 0)
        self.df.sort_index(inplace=True)

        # Get the calculated urban ratio and compare to the actual ratio
        pop_urb = self.df.loc[self.df[SET_URBAN] > 1, SET_POP_CALIB].sum()
        urban_modelled = pop_urb / pop_actual

        if abs(urban_modelled - urban_current) > 0.01:
            print('The modelled urban ratio is {:.2f}. '
                  'In case this is not acceptable please revise this part of the code'.format(urban_modelled))

        return pop_modelled, urban_modelled

    def project_pop_and_urban(self, pop_future, urban_future, start_year, years_of_analysis):
        """
        This function projects population and urban/rural ratio for the different years of the analysis
        """
        project_life = years_of_analysis[-1] - start_year

        # Project future population, with separate growth rates for urban and rural
        logging.info('Population projection process')
        start_year_pop = self.df[SET_POP_CALIB].sum()
        start_year_urban_ratio = self.df.loc[self.df[SET_URBAN] > 1, SET_POP_CALIB].sum() / start_year_pop

        urban_growth = (urban_future * pop_future) / (start_year_urban_ratio * start_year_pop)
        rural_growth = ((1 - urban_future) * pop_future) / ((1 - start_year_urban_ratio) * start_year_pop)

        yearly_urban_growth_rate = urban_growth ** (1 / project_life)
        yearly_rural_growth_rate = rural_growth ** (1 / project_life)

        for year in years_of_analysis:
            self.df.loc[self.df[SET_URBAN] > 1, SET_POP + "{}".format(year)] = self.df[SET_POP_CALIB] * (yearly_urban_growth_rate ** (year - start_year))
            self.df.loc[self.df[SET_URBAN] == 0, SET_POP + "{}".format(year)] = self.df[SET_POP_CALIB] * (yearly_rural_growth_rate ** (year - start_year))

            # self.df[SET_POP + "{}".format(year)] = \
            #     self.df.apply(lambda row: row[SET_POP_CALIB] * (yearly_urban_growth_rate ** (year - start_year))
            #     if row[SET_URBAN] > 1
            #     else row[SET_POP_CALIB] * (yearly_rural_growth_rate ** (year - start_year)), axis=1)

        self.df[SET_POP + "{}".format(start_year)] = self.df[SET_POP_CALIB]

    def calibrate_grid_elec_current(self, grid_elec_current, grid_elec_current_urban, grid_elec_current_rural,
                                    start_year, min_night_lights=0.05, min_pop=100, max_transformer_dist=2, max_mv_dist=3,
                                    max_hv_dist=5, buffer=False):
        """
        Calibrate the current electrification status
        """

        self.df[SET_ELEC_POP_CALIB] = self.df[SET_ELEC_POP] * (self.df[SET_POP_CALIB].sum() / self.df[SET_POP].sum())

        urban_pop = (self.df.loc[self.df[SET_URBAN] > 1, SET_POP_CALIB].sum())  # Total start year urban population
        rural_pop = (self.df.loc[self.df[SET_URBAN] <= 1, SET_POP_CALIB].sum())  # Total start year rural population
        total_pop = self.df[SET_POP_CALIB].sum()  # Total start year population

        factor = (total_pop * grid_elec_current) / (
                urban_pop * grid_elec_current_urban + rural_pop * grid_elec_current_rural)
        grid_elec_current_urban *= factor
        grid_elec_current_rural *= factor

        urban_electrified = urban_pop * grid_elec_current_urban  # Total start year electrified urban population
        rural_electrified = rural_pop * grid_elec_current_rural  # Total start year electrified rural population
        total_electrified = urban_electrified + rural_electrified

        # Ensure initially considered electrified population in settlement !> calibrated pop in settlement
        self.df.loc[self.df[SET_ELEC_POP] > self.df[SET_POP_CALIB], SET_ELEC_POP] = self.df[SET_POP]

        # REVIEW: The way this works now, for all urban or rural settlements that fit the conditioning.
        # The population SET_ELEC_POP is reduced by equal amount to match urban/rural national statistics respectively.

        elec_modelled = 0
        self.df.loc[self.df[SET_NIGHT_LIGHTS] <= 0, [SET_ELEC_POP_CALIB]] = 0

        logging.info('Calibrate current electrification')
        self.df[SET_ELEC_CURRENT] = 0  # 0 = unelectrified, 1 = electrified. Initially all settlements set to 0

        # This if function here skims through T&D columns in csv to identify which GIS grid distance information exists;
        # Then it defines calibration method accordingly.
        if min(self.df[SET_DIST_TO_TRANS]) < 9999:
            self.df[SET_CALIB_GRID_DIST] = self.df[SET_DIST_TO_TRANS]
            priority = 1
            dist_limit = max_transformer_dist
            print('Calibrating using distribution transformers')
        elif min(self.df[SET_MV_DIST_CURRENT]) < 9999:
            self.df[SET_CALIB_GRID_DIST] = self.df[SET_MV_DIST_CURRENT]
            priority = 1
            dist_limit = max_mv_dist
            print('Calibrating using MV lines')
        else:
            self.df[SET_CALIB_GRID_DIST] = self.df[SET_HV_DIST_CURRENT]
            priority = 2
            dist_limit = max_hv_dist
            print('Calibrating using HV lines')

        condition = 0

        urban_elec_ratio = grid_elec_current_urban
        rural_elec_ratio = grid_elec_current_rural

        while condition == 0:
            # Assign the 1 (electrified)/0 (un-electrified) values to each cell
            urban_electrified = urban_pop * urban_elec_ratio
            rural_electrified = rural_pop * rural_elec_ratio
            # RUN_PARAM: Calibration parameters if MV lines or transformer location is available
            if priority == 1:
                # print(
                #    'We have identified the existence of transformers or MV lines as input data; '
                #   'therefore we proceed using those for the calibration')
                self.df.loc[
                    (self.df[SET_CALIB_GRID_DIST] < dist_limit) & (self.df[SET_NIGHT_LIGHTS] > min_night_lights) & (
                            self.df[SET_POP_CALIB] > min_pop), SET_ELEC_CURRENT] = 1
                self.df.loc[(self.df[SET_ELEC_CURRENT] == 1) & (self.df[SET_ELEC_POP_CALIB] == 0), SET_ELEC_POP_CALIB] = \
                    self.df[SET_POP_CALIB]

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
                    while urban_elec_factor <= 1:
                        if i < 50:
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
                    while rural_elec_factor <= 1:
                        if i < 50:
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

                i = 0
                while elec_modelled < grid_elec_current:
                    if i < 21:
                        self.df.loc[self.df[SET_ELEC_CURRENT] == 1, SET_ELEC_POP_CALIB] += 0.05 * self.df[
                            SET_ELEC_POP_CALIB]  # ToDo improve
                        self.df[SET_ELEC_POP_CALIB] = np.minimum(self.df[SET_ELEC_POP_CALIB], self.df[SET_POP_CALIB])
                        pop_elec = self.df.loc[self.df[SET_ELEC_CURRENT] == 1, SET_ELEC_POP_CALIB].sum()
                        elec_modelled = pop_elec / total_pop
                        i += 1
                    else:
                        break

                # Additional calibration step for pop not meeting original steps, if prev elec pop is too small
                i = 0
                td_dist_2 = 0.1
                if buffer:
                    if grid_elec_current - elec_modelled > 0.01:
                        # print(elec_modelled - grid_elec_current)
                        print('Additional step')  # ToDo improve
                    while grid_elec_current - elec_modelled > 0.01:
                        pop_elec_2 = self.df.loc[(self.df[SET_ELEC_CURRENT] == 0) & (self.df[SET_POP_CALIB] > min_pop) &
                                                 (self.df[SET_CALIB_GRID_DIST] < td_dist_2), SET_POP_CALIB].sum()
                        if i < 50:
                            if (pop_elec + pop_elec_2) / total_pop > grid_elec_current:
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

                if elec_modelled > grid_elec_current:
                    self.df[SET_ELEC_POP_CALIB] *= grid_elec_current / elec_modelled
                pop_elec = self.df.loc[self.df[SET_ELEC_CURRENT] == 1, SET_ELEC_POP_CALIB].sum()
                elec_modelled = pop_elec / total_pop

            # RUN_PARAM: Calibration parameters if only HV lines are available
            else:
                # print(
                #    'No transformers or MV lines were identified as input data; '
                #    'therefore we proceed to the calibration with HV line info')
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
                    pass
                if rural_elec_factor > 1:
                    self.df.loc[(self.df[SET_ELEC_CURRENT] == 1) & (self.df[SET_URBAN] <= 1), SET_ELEC_POP_CALIB] *= (
                            1 / rural_elec_factor)
                else:
                    pass

                pop_elec = self.df.loc[self.df[SET_ELEC_CURRENT] == 1, SET_ELEC_POP_CALIB].sum()
                elec_modelled = pop_elec / total_pop

                # REVIEW. Added new calibration step for pop not meeting original steps, if prev elec pop is too small
                i = 0
                td_dist_2 = 0.1
                while grid_elec_current - elec_modelled > 0.01:
                    pop_elec_2 = self.df.loc[(self.df[SET_ELEC_CURRENT] == 0) & (self.df[SET_POP_CALIB] > min_pop) &
                                             (self.df[SET_CALIB_GRID_DIST] < td_dist_2), SET_POP_CALIB].sum()
                    if i < 50:
                        if (pop_elec + pop_elec_2) / total_pop > grid_elec_current:
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

                if elec_modelled > grid_elec_current:
                    self.df[SET_ELEC_POP_CALIB] *= grid_elec_current / elec_modelled
                pop_elec = self.df.loc[self.df[SET_ELEC_CURRENT] == 1, SET_ELEC_POP_CALIB].sum()
                elec_modelled = pop_elec / total_pop

            urban_elec_ratio = self.df.loc[(self.df[SET_ELEC_CURRENT] == 1) & (
                    self.df[SET_URBAN] > 1), SET_ELEC_POP_CALIB].sum() / urban_pop
            rural_elec_ratio = self.df.loc[(self.df[SET_ELEC_CURRENT] == 1) & (
                    self.df[SET_URBAN] <= 1), SET_ELEC_POP_CALIB].sum() / rural_pop

            print('The national modelled grid electrification rate is {}.'.format(round(elec_modelled, 2)))
            print('The modelled urban grid elec. rate is {}.'.format(round(urban_elec_ratio, 2)))
            print('The modelled rural grid elec. rate is {}'.format(round(rural_elec_ratio, 2)))
            condition = 1

        self.df[SET_ELEC_FINAL_CODE + "{}".format(start_year)] = \
            self.df.apply(lambda row: 1 if row[SET_ELEC_CURRENT] == 1 else 99, axis=1)

        self.df.loc[self.df[SET_ELEC_FINAL_CODE + "{}".format(start_year)] == 99, SET_ELEC_POP_CALIB] = 0
        self.df[SET_ELEC_POP + "{}".format(start_year)] = self.df[SET_ELEC_POP_CALIB]

        return elec_modelled, rural_elec_modelled, urban_elec_modelled, dist_limit, \
            min_night_lights, min_pop, buffer, td_dist_2

    def mg_elec_current(self,
                        start_year,
                        mg_dist=1, # Distance from existing mini-grids to consider settlements connected to the mini-grid
                        mg_ntl=-1, # Night-time light threshold to consider a settlement mini-grid electrified, in combination with mg_dist. -1 means NTL is not required, 0 means all settlements with NTL within dist is electrified, and any higher value means a higher cut-off threshold
                        min_pop=400  ### Settlement population above which we can assume that it could be electrified
                        ):

        self.df.loc[
            (self.df[SET_ELEC_FINAL_CODE + '{}'.format(start_year)] != 1) & (self.df[SET_NIGHT_LIGHTS] > mg_ntl) &
            (self.df[SET_MG_DIST] < mg_dist) & (self.df[SET_POP_CALIB] > min_pop), SET_ELEC_CURRENT] = 1

        self.df.loc[
            (self.df[SET_ELEC_FINAL_CODE + '{}'.format(start_year)] != 1) & (self.df[SET_NIGHT_LIGHTS] > mg_ntl) &
            (self.df[SET_MG_DIST] < mg_dist) & (self.df[SET_POP_CALIB] > min_pop), SET_ELEC_FINAL_CODE + '{}'.format(
                start_year)] = 5

        self.df.loc[
            (self.df[SET_ELEC_FINAL_CODE + '{}'.format(start_year)] != 1) & (self.df[SET_NIGHT_LIGHTS] > mg_ntl) &
            (self.df[SET_MG_DIST] < mg_dist) & (self.df[SET_POP_CALIB] > min_pop), SET_ELEC_POP_CALIB] = self.df[
            SET_POP_CALIB]

        self.df[SET_ELEC_POP + '{}'.format(start_year)] = self.df[SET_ELEC_POP_CALIB]

        mg_pop = self.df.loc[self.df[SET_ELEC_FINAL_CODE + '{}'.format(start_year)] == 5, SET_ELEC_POP_CALIB].sum() / \
                 self.df[SET_POP_CALIB].sum()

        print('The national modelled mini-grid electrification rate is {}'.format(round(mg_pop, 3)))

        return mg_pop

    def current_mv_line_dist(self):
        logging.info('Determine current MV line length')
        self.df[SET_MV_CONNECT_DIST] = 0.
        self.df.loc[self.df[SET_ELEC_CURRENT] == 1, SET_MV_CONNECT_DIST] = self.df[SET_HV_DIST_CURRENT]
        self.df[SET_MIN_TD_DIST] = self.df[[SET_MV_DIST_PLANNED, SET_HV_DIST_PLANNED]].min(axis=1)

    def pre_electrification(self, grid_price, year, time_step, end_year, grid_calc, sa_diesel_calc,
                            grid_reliability_option, grid_capacity_limit, grid_connect_limit):

        """" ... """

        logging.info('Define the initial electrification status')
        grid_investment = np.zeros(len(self.df[SET_X_DEG]))
        grid_capacity = np.zeros(len(self.df[SET_X_DEG]))
        prev_code = self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)].copy(deep=True)

        # Grid-electrified settlements
        electrified_loce, electrified_investment, electrified_capacity = self.get_grid_lcoe(0, 0, 0, year, time_step,
                                                                                            end_year, grid_calc,
                                                                                            sa_diesel_calc,
                                                                                            grid_reliability_option)
        electrified_investment = electrified_investment[0]
        electrified_capacity = electrified_capacity[0]
        grid_investment = np.where(self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 1,
                                   electrified_investment, grid_investment)
        grid_capacity = np.where(self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 1,
                                 electrified_capacity, grid_capacity)

        self.df[SET_LCOE_GRID + "{}".format(year)] = 99.
        self.df.loc[self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 1,
                    SET_LCOE_GRID + "{}".format(year)] = grid_price


        # Two restrictions may be imposed on the grid. The new grid generation capacity that can be added and the
        # number of new households that can be connected. The next step calculates how much of that will be used up due
        # to demand (population) growth in already electrified settlements

        grid_capacity_limit -= grid_capacity.sum()

        self.df['Densification_connections'] = self.df[SET_NEW_CONNECTIONS + "{}".format(year)] # / self.df[SET_NUM_PEOPLE_PER_HH]
        grid_connect_limit -= sum(self.df.loc[prev_code == 1]['Densification_connections'])
        del self.df['Densification_connections']

        return pd.Series(grid_investment), pd.Series(grid_capacity), grid_capacity_limit, grid_connect_limit

    def max_extension_dist(self, year, time_step, end_year, start_year, grid_calc, sa_diesel_calc,
                           grid_reliability_option, max_intensification_cost=0, auto_intensification=0):

        # Calculate max extension for each settlement to be connected to the grid at
        # a lower cost than least-cost off-grid alternative

        filter_lcoe, filter_investment, filter_capacity, peak_load = \
            self.get_grid_lcoe(0, 0, 0, year, time_step, end_year, grid_calc, sa_diesel_calc,
                               grid_reliability_option, get_max_dist=True)

        filter_lcoe_1, filter_investment_1, filter_capacity_1, peak_load_1 = \
            self.get_grid_lcoe(1, 0, 0, year, time_step, end_year, grid_calc, sa_diesel_calc,
                               grid_reliability_option, get_max_dist=True)

        self.df['NoExtensionInvestment{}'.format(year)] = filter_investment[0]
        self.df['FilterLCOE' + "{}".format(year)] = filter_lcoe[0]

        self.df['NoExtensionInvestment{}_1'.format(year)] = filter_investment_1[0]
        self.df['FilterLCOE' + "{}_1".format(year)] = filter_lcoe_1[0]

        project_life = end_year - start_year + 1

        years = np.arange(project_life)
        step = (year - time_step) - start_year
        generation_per_year = self.df[SET_ENERGY_PER_CELL + '{}'.format(year)]

        el_gen = np.outer(np.asarray(generation_per_year), np.ones(project_life))
        for s in range(step):
            el_gen[:, s] = 0

        discount_factor = (1 + grid_calc.discount_rate) ** years

        hv_to_mv_lines = grid_calc.hv_line_cost / grid_calc.mv_line_cost
        max_mv_load = grid_calc.mv_line_amperage_limit * grid_calc.mv_line_type * hv_to_mv_lines
        mv_amperage = grid_calc.service_transf_type / grid_calc.mv_line_type
        no_of_mv_lines = np.ceil(peak_load / (mv_amperage * grid_calc.mv_line_type))
        hv_amperage = grid_calc.hv_mv_substation_type / grid_calc.hv_line_type
        no_of_hv_lines = np.ceil(peak_load / (hv_amperage * grid_calc.hv_line_type))

        mv_lines = np.where((peak_load <= max_mv_load), no_of_mv_lines, 0)
        hv_lines = np.where((peak_load <= max_mv_load), 0, no_of_hv_lines)
        mv_cost_per_km = mv_lines * grid_calc.mv_line_cost
        hv_cost_per_km = hv_lines * grid_calc.hv_line_cost
        cost_per_km = mv_cost_per_km + hv_cost_per_km

        reinvest_year = 0
        if grid_calc.tech_life + step < project_life:
            reinvest_year = grid_calc.tech_life + step

        if reinvest_year > 0:
            used_life = (project_life - step) - grid_calc.tech_life
        else:
            used_life = project_life - step - 1

        salvage = (1 - used_life / grid_calc.tech_life) * cost_per_km / discount_factor[-1]

        cost_per_km -= salvage

        marginal_lcoe = filter_lcoe_1[0] - filter_lcoe[0]

        self.df['MaxDist' + '{}'.format(year)] = (self.df['Minimum_LCOE_Off_grid{}'.format(year)] - filter_lcoe[0]) / marginal_lcoe

        self.df['GridCapacityRequired'] = peak_load / grid_calc.capacity_factor
        self.df['GridCapacityRequired' + '{}'.format(year)] = peak_load / grid_calc.capacity_factor

        self.df['MaxIntensificationDist'] = np.where((self.df[SET_NEW_CONNECTIONS + "{}".format(year)] > 0) & (self.df[SET_MV_DIST_PLANNED] < auto_intensification),  #
                                                     (max_intensification_cost * self.df[SET_NEW_CONNECTIONS + "{}".format(year)] - filter_investment[0]) / cost_per_km,
                                                     -1)

        self.df['MaxDist' + '{}'.format(year)] = np.maximum(self.df['MaxIntensificationDist'], self.df['MaxDist' + '{}'.format(year)])


    @staticmethod
    def start_extension_points(mv_lines_path, index_parts=True):
        # Function to interpolate points along a LineString

        data = gpd.read_file(mv_lines_path)
        data = data.to_crs(3395)

        def interpolate_points(line, distance):
            num_vertices = int(line.length / distance) + 1
            points = [line.interpolate(i * distance) for i in range(num_vertices)]
            return points

        # Function to convert a coordinate to Point geometry
        def coords_to_points(coords):
            return [Point(coord) for coord in coords]

        # Define the target distance for interpolation (500 meters)
        distance = 500  # in meters

        # Define lists to collect all x and y coordinates
        x_coords = []
        y_coords = []

        # Iterate through features in the GeoJSON
        try:
            for line in data['geometry'].explode(index_parts=index_parts):
                #if geom.geom_type == 'MultiLineString':
                #    for line in geom:
                        # Add original vertices
                        for point in coords_to_points(line.coords):
                            x_coords.append(point.x)
                            y_coords.append(point.y)

                        # Interpolate points if the line is longer than 750 meters
                        if line.length > 750:
                            for point in interpolate_points(line, distance):
                                x_coords.append(point.x)
                                y_coords.append(point.y)
        except TypeError:
            for line in data['geometry'].explode():
                #if geom.geom_type == 'MultiLineString':
                #    for line in geom:
                        # Add original vertices
                        for point in coords_to_points(line.coords):
                            x_coords.append(point.x)
                            y_coords.append(point.y)

                        # Interpolate points if the line is longer than 750 meters
                        if line.length > 750:
                            for point in interpolate_points(line, distance):
                                x_coords.append(point.x)
                                y_coords.append(point.y)

        # Convert lists to numpy arrays
        x_array = np.array(x_coords)
        y_array = np.array(y_coords)

        return x_array, y_array

    @staticmethod
    @njit
    def extension_dist_and_check(unelectrified,
                                 x_coordinates,
                                 y_coordinates,
                                 x_unelectrified,
                                 y_unelectrified,
                                 max_dist,
                                 new_connections,
                                 grid_connect_limit,
                                 new_capacity,
                                 new_capacity_limit,
                                 x_coordinates_iteration,
                                 y_coordinates_iteration,
                                 ):
        newly_electrified = []
        newly_electrified_dist = []
        new_mv_line_coords = []

        new_x_coords = []
        new_y_coords = []

        for i in range(len(unelectrified)):

            if (grid_connect_limit <= 0) | (new_capacity_limit <= 0):
                break

            id = unelectrified[i]
            x = x_unelectrified[i]
            y = y_unelectrified[i]

            dist = np.sqrt((x_coordinates_iteration - x) ** 2 + (y_coordinates_iteration - y) ** 2)
            min_dist = min(dist) / 1000
            min_index = np.argmin(dist)

            if min_dist < max_dist[i]:
                newly_electrified.append(id)
                x_coordinates = np.append(x_coordinates, x)
                y_coordinates = np.append(y_coordinates, y)

                x_coordinates_iteration = np.append(x_coordinates_iteration, x)
                y_coordinates_iteration = np.append(y_coordinates_iteration, y)

                new_x_coords.append(x)
                new_y_coords.append(y)

                newly_electrified_dist.append(min_dist)
                new_mv_line_coords.append((x, y, x_coordinates_iteration[min_index], y_coordinates_iteration[min_index]))

                grid_connect_limit -= new_connections[i]
                new_capacity_limit -= new_capacity[i]

                if min_dist > 0.75:
                    # Calculate the number of intermediate points
                    number_of_points = int(min_dist / 0.5)

                    # Generate the intermediate points
                    for i in range(1, number_of_points + 1):
                        x_i = x + i * (x_coordinates_iteration[min_index] - x) / (number_of_points + 1)
                        y_i = y + i * (y_coordinates_iteration[min_index] - y) / (number_of_points + 1)
                        x_coordinates = np.append(x_coordinates, x_i)
                        y_coordinates = np.append(y_coordinates, y_i)

                        x_coordinates_iteration = np.append(x_coordinates_iteration, x_i)
                        y_coordinates_iteration = np.append(y_coordinates_iteration, y_i)

                        new_x_coords.append(x_i)
                        new_y_coords.append(y_i)

            else:
                pass

        new_x_coords = np.array(new_x_coords)
        new_y_coords = np.array(new_y_coords)

        return newly_electrified, newly_electrified_dist, new_mv_line_coords, \
            x_coordinates, y_coordinates, grid_connect_limit, new_capacity_limit, new_x_coords, new_y_coords

    def add_xy_3395(self):
        # Earth's radius in meters (WGS 84)
        R = 6378137.0
        # Flattening factor of the Earth
        f = 1 / 298.257223563
        # Scale factor for EPSG:3395
        k0 = 1.0

        # Conversion constants for EPSG:3395
        def deg_to_rad(degrees):
            return degrees * (np.pi / 180.0)

        def lon_to_x(lon):
            return R * deg_to_rad(lon)

        def lat_to_y(lat):
            lat_rad = deg_to_rad(lat)
            e = np.sqrt(f * (2 - f))  # Eccentricity
            sin_lat = np.sin(lat_rad)
            return R * np.log(np.tan(np.pi / 4 + lat_rad / 2) * ((1 - e * sin_lat) / (1 + e * sin_lat)) ** (e / 2))

        self.df['X'] = lon_to_x(self.df[SET_X_DEG])
        self.df['Y'] = lat_to_y(self.df[SET_Y_DEG])

    def elec_extension_numba(self, grid_calc, sa_diesel_calc, grid_reliability_option, max_dist, year,
                             end_year, time_step, grid_capacity_limit, grid_connect_limit, x_coordinates, y_coordinates,
                             mg_interconnection=False):

        print(time.ctime(), 'Calculate grid extension for year {}'.format(year))

        self.df['NearRoads'] = np.where(self.df[SET_ROAD_DIST] < 0.5, 0, 1)

        # Re-sort df to start extending MV lines along (close to) road network
        self.df.sort_values(by=['NearRoads', SET_MV_DIST_CURRENT], inplace=True)
        del self.df['NearRoads']

        # Ensure MV lines are not extended further than their maximum distance
        self.df.loc[self.df[SET_MV_DIST_PLANNED] > max_dist, 'MaxDist' + "{}".format(year)] = -1

        new_electrified = []
        new_dists = []
        new_lines = []

        iterate = True
        i = 0

        new_x_coords = x_coordinates.copy()
        new_y_coords = y_coordinates.copy()

        while iterate:

            if mg_interconnection == 1:
                unelectrified = self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] >= 3) &
                                            (self.df['MaxDist' + "{}".format(year)] >= 0) &
                                            (self.df['PreSelection' + "{}".format(year)] == 1) &
                                            (self.df[SET_HV_DIST_PLANNED] < max_dist)].index.tolist()
            else:
                unelectrified = self.df.loc[((self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 3) | (self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 99)) &
                                            (self.df['MaxDist' + "{}".format(year)] >= 0) &
                                            (self.df['PreSelection' + "{}".format(year)] == 1) &
                                            (self.df[SET_HV_DIST_PLANNED] < max_dist)].index.tolist()

            unelectrified = [x for x in unelectrified if x not in new_electrified]

            if len(unelectrified) > 0:
                newly_electrified, newly_electrified_dists, new_mv_line_coords, \
                     x_coordinates, y_coordinates, grid_connect_limit, grid_capacity_limit, new_x_coords, new_y_coords = \
                     self.extension_dist_and_check(unelectrified,
                                                   x_coordinates,
                                                   y_coordinates,
                                                   np.array(self.df.loc[unelectrified]['X']),
                                                   np.array(self.df.loc[unelectrified]['Y']),
                                                   np.array(self.df.loc[unelectrified]['MaxDist' + "{}".format(year)]),
                                                   np.array(self.df.loc[unelectrified][SET_NEW_CONNECTIONS + "{}".format(year)]),
                                                   grid_connect_limit,
                                                   np.array(self.df.loc[unelectrified]['GridCapacityRequired' + '{}'.format(year)]),
                                                   grid_capacity_limit,
                                                   new_x_coords,
                                                   new_y_coords
                                                   )

                new_lines += new_mv_line_coords
                new_electrified += newly_electrified
                new_dists += newly_electrified_dists

                if len(newly_electrified) > 0:
                    print(len(newly_electrified), ' new settlements connected to the grid', time.ctime())

                new_lines += new_mv_line_coords
                new_electrified += newly_electrified
                new_dists += newly_electrified_dists

            else:
                newly_electrified = []

            i += 1
            if len(newly_electrified) == 0:
                iterate = False
            if len(unelectrified) == 0:
                iterate = False

            if grid_connect_limit <= 0:
                iterate = False

        features = []

        for coord in new_lines:
            x_start, y_start, x_end, y_end = coord
            line = shapely.geometry.LineString([(x_start, y_start), (x_end, y_end)])
            feature = geojson.Feature(geometry=line, properties={})
            features.append(feature)

        self.df['NewDist'] = 0.
        self.df.loc[new_electrified, 'NewDist'] = new_dists

        self.df.sort_index(inplace=True)

        grid_lcoe, grid_investment, grid_capacity = \
            self.get_grid_lcoe(self.df['NewDist'], 0, 0, year, time_step, end_year, grid_calc, sa_diesel_calc,
                               grid_reliability_option)

        grid_lcoe = np.where((self.df['NewDist'] == 0) & (self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] > 2), 99, grid_lcoe[0])
        grid_investment = np.where((self.df['NewDist'] == 0) & (self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] > 2), 0, grid_investment[0])
        grid_capacity = np.where((self.df['NewDist'] == 0) & (self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] > 2), 0, grid_capacity[0])

        # Create a FeatureCollection
        feature_collection = geojson.FeatureCollection(features)

        self.df.sort_index(inplace=True)

        # print('Finishing', time.ctime())

        return grid_lcoe, self.df['NewDist'], pd.DataFrame(grid_investment), pd.DataFrame(grid_capacity), \
            x_coordinates, y_coordinates, feature_collection

    def get_grid_lcoe(self, dist_adjusted, elecorder, additional_transformer, year, time_step, end_year, grid_calc,
                      sa_diesel_calc, grid_reliability_option, get_max_dist=False):
        grid = \
            grid_calc.get_lcoe(energy_per_cell=self.df[SET_ENERGY_PER_CELL + "{}".format(year)],
                               start_year=year - time_step,
                               end_year=end_year,
                               people=self.df[SET_POP + "{}".format(year)],
                               new_connections=self.df[SET_NEW_CONNECTIONS + "{}".format(year)],
                               total_energy_per_cell=self.df[SET_TOTAL_ENERGY_PER_CELL],
                               prev_code=self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)],
                               num_people_per_hh=self.df[SET_NUM_PEOPLE_PER_HH],
                               grid_cell_area=self.df[SET_GRID_CELL_AREA],
                               additional_mv_line_length=dist_adjusted,
                               elec_loop=elecorder,
                               additional_transformer=additional_transformer,
                               capacity_factor=grid_calc.capacity_factor,
                               get_max_dist=get_max_dist,
                               unmet_demand=self.df[SET_UNMET_DEMAND + "{}".format(year)],
                               fuel_cost_settlement=self.df[SET_MG_DIESEL_FUEL + "{}".format(year)],
                               sa_diesel_calc=sa_diesel_calc,
                               grid_reliability_option=grid_reliability_option,
                               base_to_peak_load_ratio=self.df[SET_AVERAGE_TO_PEAK]
                               )

        if get_max_dist:
            return grid[0], grid[1], grid[2], grid[3]
        else:
            return grid[0], grid[1], grid[2]

    def closest_electrified_settlement(self, new_electrified, unelectrified, cell_path_real, grid_penalty_ratio,
                                       elecorder):

        x = self.df[SET_X_DEG].copy(deep=True)
        y = self.df[SET_Y_DEG].copy(deep=True)

        # Identifies the electrified settlements from which to extend the network
        extension_nodes = np.where(new_electrified == 1)
        extension_nodes = extension_nodes[0].tolist()
        # Creates an array of x, y coordinates of the electrified settlements
        elec_nodes2 = np.transpose(np.array([x.loc[extension_nodes], y.loc[extension_nodes]]))

        closest_elec_node = np.zeros(len(x), dtype=int)
        nearest_dist = np.zeros(len(x))
        nearest_elec_order = np.zeros(len(x), dtype=int)
        prev_dist = np.zeros(len(x))

        # Create an array of x-, y-coordinates of the (filtered) unelectrified settlements
        unelectrified = np.setdiff1d(unelectrified, extension_nodes).tolist()
        x_unelec = x.loc[unelectrified]
        y_unelec = y.loc[unelectrified]
        unelec_nodes = pd.DataFrame(np.transpose(np.array([x_unelec, y_unelec])))

        # Calculate for each unelectrified settlement which is the closest electrified settlement
        closest_node = self.do_kdtree(elec_nodes2, unelec_nodes)

        # For each unelectrified settlement, find the electrifiecation order, distance to closest electrified
        # settlement, distance including grid penalty, and total mv length up until the electrrfied settlement
        j = 0
        for unelec in unelectrified:
            closest_elec_node[unelec] = closest_node[j]
            j += 1
        extension_nodes = np.array(extension_nodes)
        x_closest_elec = x.loc[extension_nodes[closest_elec_node[unelectrified]]]
        x_closest_elec.index = x_unelec.index
        y_closest_elec = y.loc[extension_nodes[closest_elec_node[unelectrified]]]
        y_closest_elec.index = y_unelec.index
        dist = self.haversine_vector(x_closest_elec, y_closest_elec, x_unelec, y_unelec)
        nearest_dist[unelectrified] = dist[unelectrified]
        nearest_dist_adjusted = np.nan_to_num(nearest_dist * grid_penalty_ratio)
        nearest_elec_order[unelectrified] = elecorder[extension_nodes[
            closest_elec_node[unelectrified]]] + 1
        prev_dist[unelectrified] = cell_path_real[
            extension_nodes[closest_elec_node[unelectrified]]]

        return nearest_dist_adjusted, nearest_elec_order, prev_dist, nearest_dist

    def update_grid_extension_info(self, grid_lcoe, dist, dist_adjusted, prev_dist, elecorder, new_elec_order,
                                   max_dist, new_lcoes, grid_capacity_limit, grid_connect_limit, cell_path_real,
                                   cell_path_adjusted, electrified, year, grid_calc, grid_investment, new_investment,
                                   grid_capacity, new_capacity, base_to_peak_load_ratio, threshold=999999999):

        min_code_lcoes = self.df[SET_MIN_OFFGRID_LCOE + "{}".format(year)].copy(deep=True)

        grid_lcoe = grid_lcoe[0]
        grid_investment = grid_investment[0]
        grid_capacity = grid_capacity[0]
        grid_lcoe.loc[electrified == 1] = 99
        grid_lcoe.loc[prev_dist + dist_adjusted > max_dist] = 99
        grid_lcoe.loc[grid_lcoe > new_lcoes] = 99

        grid_lcoe.loc[grid_investment / self.df[SET_NEW_CONNECTIONS + "{}".format(year)] > threshold] = 99

        consumption = self.df[SET_ENERGY_PER_CELL + "{}".format(year)]  # kWh/year
        average_load = consumption / (1 - grid_calc.distribution_losses) / HOURS_PER_YEAR  # kW
        peak_load = average_load / base_to_peak_load_ratio  # kW
        peak_load.loc[grid_lcoe >= min_code_lcoes] = 0
        peak_load_cum_sum = np.cumsum(peak_load)
        grid_lcoe.loc[peak_load_cum_sum > grid_capacity_limit] = 99
        new_grid_connections = self.df[SET_NEW_CONNECTIONS + "{}".format(year)].copy()
        new_grid_connections.loc[grid_lcoe >= min_code_lcoes] = 0
        new_grid_connections_cum_sum = np.cumsum(new_grid_connections)
        grid_lcoe.loc[new_grid_connections_cum_sum > grid_connect_limit] = 99

        # Update limiting values
        grid_capacity_limit -= peak_load.loc[grid_lcoe < min_code_lcoes].sum()
        grid_connect_limit -= new_grid_connections.loc[grid_lcoe < min_code_lcoes].sum()

        # Update values for settlements that meet conditions
        cell_path_real = np.where(grid_lcoe < min_code_lcoes, prev_dist + dist, cell_path_real)
        cell_path_adjusted = np.where(grid_lcoe < min_code_lcoes, dist_adjusted, cell_path_adjusted)
        elecorder = np.where(grid_lcoe < min_code_lcoes, new_elec_order, elecorder)
        electrified = np.where(grid_lcoe < min_code_lcoes, 1, electrified)
        new_lcoes = np.where(grid_lcoe < min_code_lcoes, grid_lcoe, new_lcoes)
        new_investment = np.where(grid_lcoe < min_code_lcoes, grid_investment, new_investment)
        new_capacity = np.where(grid_lcoe < min_code_lcoes, grid_capacity, new_capacity)

        return grid_capacity_limit, grid_connect_limit, cell_path_real, cell_path_adjusted, elecorder, \
            electrified, new_lcoes, new_investment, new_capacity

    @staticmethod
    def haversine_vector(lon1, lat1, lon2, lat2):
        """Calculate the great circle distance between two points
        on the earth (specified in decimal degrees)
        """
        # convert decimal degrees to radians
        lon1, lat1, lon2, lat2 = map(np.deg2rad, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
        c = 2 * np.arcsin(np.sqrt(a))
        r = 6371  # Radius of earth in kilometers. Use 3956 for miles
        return c * r

    @staticmethod
    def do_kdtree(combined_x_y_arrays, points):
        mytree = scipy.spatial.cKDTree(combined_x_y_arrays)
        dist, indexes = mytree.query(points)
        return indexes

    def calculate_new_connections(self, year, time_step, num_people_per_hh_rural, num_people_per_hh_urban):
        """this method defines number of new connections in each settlement each year

        Arguments
        ---------
        year : int
        time_step : int
        start_year : int
        num_people_per_hh_rural : float
        num_people_per_hh_urban : float

        """

        # RUN_PARAM: This shall be changed if different urban/rural categorization is decided
        # Create new columns assigning number of people per household as per Urban/Rural type

        self.df.loc[self.df[SET_URBAN] == 2, SET_NUM_PEOPLE_PER_HH] = num_people_per_hh_urban
        self.df.loc[self.df[SET_URBAN] == 0, SET_NUM_PEOPLE_PER_HH] = num_people_per_hh_rural
        

        logging.info('Calculate new connections')
        # Calculate new connections
        self.df[SET_NEW_CONNECTIONS + "{}".format(year)] = \
            np.round(self.df[SET_POP + "{}".format(year)] / self.df[SET_NUM_PEOPLE_PER_HH] -
                     self.df[SET_ELEC_POP + "{}".format(year - time_step)] / self.df[SET_NUM_PEOPLE_PER_HH])

        # Some conditioning to eliminate negative values if existing by mistake
        self.df.loc[self.df[SET_NEW_CONNECTIONS + "{}".format(year)] < 0, SET_NEW_CONNECTIONS + "{}".format(year)] = 0

    def set_residential_demand(self, urban_tier, rural_tier_large, rural_tier_small, rural_cutoff, tiers, year):
        """this method defines residential demand per tier level for each target year

        Arguments
        ---------
        rural_tier : int
        urban_tier : int
        num_people_per_hh_rural : float
        num_people_per_hh_urban : float
        """

        logging.info('Setting electrification demand as per target per year')

        if max(self.df[SET_HH_DEMAND]) == 0:

            self.df[SET_HH_DEMAND] = 0.

            # Define residential demand
            if int(urban_tier) == 6:
                self.df.loc[self.df[SET_URBAN] > 0, SET_HH_DEMAND] = self.df[SET_RESIDENTIAL_TIER + 'Custom'] * self.df[SET_NUM_PEOPLE_PER_HH]
            else:
                self.df.loc[self.df[SET_URBAN] > 0, SET_HH_DEMAND] = tiers[urban_tier]

            if int(rural_tier_large) == 6:
                self.df.loc[(self.df[SET_POP + "{}".format(year)] / self.df[SET_NUM_PEOPLE_PER_HH] >= rural_cutoff) & (self.df[SET_URBAN] == 0),
                            SET_HH_DEMAND] = self.df[SET_RESIDENTIAL_TIER + 'Custom'] * self.df[SET_NUM_PEOPLE_PER_HH]
            else:
                self.df.loc[(self.df[SET_POP + "{}".format(year)] / self.df[SET_NUM_PEOPLE_PER_HH] >= rural_cutoff) & (self.df[SET_URBAN] == 0),
                            SET_HH_DEMAND] = tiers[rural_tier_large]

            if int(rural_tier_small) == 6:
                self.df.loc[(self.df[SET_POP + "{}".format(year)] / self.df[SET_NUM_PEOPLE_PER_HH] < rural_cutoff) & (self.df[SET_URBAN] == 0),
                            SET_HH_DEMAND] = self.df[SET_RESIDENTIAL_TIER + 'Custom'] * self.df[SET_NUM_PEOPLE_PER_HH]
            else:
                self.df.loc[(self.df[SET_POP + "{}".format(year)] / self.df[SET_NUM_PEOPLE_PER_HH] < rural_cutoff) & (self.df[SET_URBAN] == 0),
                            SET_HH_DEMAND] = tiers[rural_tier_small]

        self.df[SET_TIER] = 5
        self.df.loc[self.df[SET_HH_DEMAND] < tiers[5], SET_TIER] = 4
        self.df.loc[self.df[SET_HH_DEMAND] < tiers[4], SET_TIER] = 3
        self.df.loc[self.df[SET_HH_DEMAND] < tiers[3], SET_TIER] = 2
        self.df.loc[self.df[SET_HH_DEMAND] < tiers[2], SET_TIER] = 1

        self.df[SET_AVERAGE_TO_PEAK] = 0.8
        self.df.loc[self.df[SET_TIER] == 1, SET_AVERAGE_TO_PEAK] = 0.3
        self.df.loc[self.df[SET_TIER] == 2, SET_AVERAGE_TO_PEAK] = 0.4
        self.df.loc[self.df[SET_TIER] == 3, SET_AVERAGE_TO_PEAK] = 0.5
        self.df.loc[self.df[SET_TIER] == 4, SET_AVERAGE_TO_PEAK] = 0.5
        self.df.loc[self.df[SET_TIER] == 5, SET_AVERAGE_TO_PEAK] = 0.5

    def calculate_total_demand_per_settlement(self, year, time_step):
        """this method calculates total demand for each settlement per year

        Arguments
        ---------
        year : int

        """

        produse = self.df[SET_AGRI_DEMAND] + self.df[SET_COMMERCIAL_DEMAND] + self.df[SET_HEALTH_DEMAND] + self.df[
            SET_EDU_DEMAND]

        self.df.loc[self.df[SET_URBAN] == 0, SET_ENERGY_PER_CELL + "{}".format(year)] = \
            self.df[SET_HH_DEMAND] * self.df[SET_NEW_CONNECTIONS + "{}".format(year)]
        self.df.loc[self.df[SET_URBAN] == 1, SET_ENERGY_PER_CELL + "{}".format(year)] = \
            self.df[SET_HH_DEMAND] * self.df[SET_NEW_CONNECTIONS + "{}".format(year)]
        self.df.loc[self.df[SET_URBAN] == 2, SET_ENERGY_PER_CELL + "{}".format(year)] = \
            self.df[SET_HH_DEMAND] * self.df[SET_NEW_CONNECTIONS + "{}".format(year)]

        self.df.loc[(self.df[SET_URBAN] == 0) & (self.df[SET_ELEC_FINAL_CODE + "{}".format(
            year - time_step)] == 99), SET_ENERGY_PER_CELL + "{}".format(year)] = \
            self.df[SET_HH_DEMAND] * self.df[SET_NEW_CONNECTIONS + "{}".format(year)] + produse
        self.df.loc[(self.df[SET_URBAN] == 1) & (self.df[SET_ELEC_FINAL_CODE + "{}".format(
            year - time_step)] == 99), SET_ENERGY_PER_CELL + "{}".format(year)] = \
            self.df[SET_HH_DEMAND] * self.df[SET_NEW_CONNECTIONS + "{}".format(year)] + produse
        self.df.loc[(self.df[SET_URBAN] == 2) & (self.df[SET_ELEC_FINAL_CODE + "{}".format(
            year - time_step)] == 99), SET_ENERGY_PER_CELL + "{}".format(year)] = \
            self.df[SET_HH_DEMAND] * self.df[SET_NEW_CONNECTIONS + "{}".format(year)] + produse

        self.df.loc[self.df[SET_URBAN] == 0, SET_TOTAL_ENERGY_PER_CELL] = \
            self.df[SET_HH_DEMAND] * np.round(self.df[SET_POP + "{}".format(year)] / self.df[SET_NUM_PEOPLE_PER_HH]) + produse
        self.df.loc[self.df[SET_URBAN] == 1, SET_TOTAL_ENERGY_PER_CELL] = \
            self.df[SET_HH_DEMAND] * np.round(self.df[SET_POP + "{}".format(year)] / self.df[SET_NUM_PEOPLE_PER_HH]) + produse
        self.df.loc[self.df[SET_URBAN] == 2, SET_TOTAL_ENERGY_PER_CELL] = \
            self.df[SET_HH_DEMAND] * np.round(self.df[SET_POP + "{}".format(year)] / self.df[SET_NUM_PEOPLE_PER_HH]) + produse

    def calculate_demand(self, year, num_people_per_hh_rural, num_people_per_hh_urban,
                         time_step, urban_tier, rural_tier_large, rural_tier_small, rural_cutoff,
                         tiers):
        """
        this method determines some basic parameters required in LCOE calculation
        it sets the basic scenario parameters that differ based on urban/rural so that they are in the table and
        can be read directly to calculate LCOEs

        Arguments
        ---------
        year : int
        num_people_per_hh_rural : float
        num_people_per_hh_urban : float
        time_step : int
        start_year: int
        urban_tier : int
        rural_tier : int
        end_year_pop : int
        productive_demand : int

        """

        self.calculate_new_connections(year, time_step, num_people_per_hh_rural, num_people_per_hh_urban)
        self.set_residential_demand(urban_tier, rural_tier_large, rural_tier_small, rural_cutoff,
                               tiers, year)
        self.calculate_total_demand_per_settlement(year, time_step)

    def calculate_unmet_demand(self, year, reliability=1):
        if SET_GRID_RELIABILITY in self.df:
            self.df[SET_UNMET_DEMAND + "{}".format(year)] = \
                self.df[SET_ENERGY_PER_CELL + "{}".format(year)] * (1 - self.df[SET_GRID_RELIABILITY])
        else:
            self.df[SET_UNMET_DEMAND + "{}".format(year)] = \
                self.df[SET_ENERGY_PER_CELL + "{}".format(year)] * (1 - reliability)

    @staticmethod
    def optimize_mini_grid(ghi_curve, temp, energy, tier, diesel_price, start_year, end_year,
                           year, time_step, mg_pv_hybrid_specs):

        load_curve = calc_load_curve(tier, energy)

        def optimizer_de(diesel_price,
                         hourly_ghi,
                         hourly_temp,
                         load_curve,
                         diesel_cost=mg_pv_hybrid_specs['diesel_cost'],
                         discount_rate=mg_pv_hybrid_specs['discount_rate'],
                         n_chg=mg_pv_hybrid_specs['n_chg'],
                         n_dis=mg_pv_hybrid_specs['n_dis'],
                         battery_cost=mg_pv_hybrid_specs['battery_cost'],
                         pv_cost=mg_pv_hybrid_specs['pv_cost'],
                         charge_controller=mg_pv_hybrid_specs['charge_controller'],
                         pv_inverter=mg_pv_hybrid_specs['pv_inverter'],
                         pv_life=mg_pv_hybrid_specs['pv_life'],
                         diesel_life=mg_pv_hybrid_specs['diesel_life'],
                         pv_om=mg_pv_hybrid_specs['pv_om'],
                         diesel_om=mg_pv_hybrid_specs['diesel_om'],
                         battery_inverter_cost=mg_pv_hybrid_specs['battery_inverter_cost'],
                         battery_inverter_life=mg_pv_hybrid_specs['battery_inverter_life'],
                         dod_max=mg_pv_hybrid_specs['dod_max'],
                         inv_eff=mg_pv_hybrid_specs['inv_eff'],
                         lpsp_max=mg_pv_hybrid_specs['lpsp_max'],
                         diesel_limit=mg_pv_hybrid_specs['diesel_limit'],
                         full_life_cycles=mg_pv_hybrid_specs['full_life_cycles'],
                         start_year=year - time_step,
                         end_year=end_year,
                         ):

            demand = load_curve.sum()

            # The following lines defines the solution space for the Particle Swarm Optimization (PSO) algorithm
            battery_bounds = [0, 5 * demand / 365]
            pv_bounds = [0, 5 * max(load_curve)]
            diesel_bounds = [0, max(load_curve)]
            if diesel_limit == 0:
                diesel_bounds = [0, 0]

            min_bounds = np.array([pv_bounds[0], battery_bounds[0], diesel_bounds[0]])
            max_bounds = np.array([pv_bounds[1], battery_bounds[1], diesel_bounds[1]])
            bounds = Bounds(min_bounds, max_bounds)

            #  This creates a series of the hour numbers (0-24) for one year
            hour_numbers = np.empty(8760)
            for i in prange(365):
                for j in prange(24):
                    hour_numbers[i * 24 + j] = j

            def opt_func(X):
                lcoe = find_least_cost_option(X, hourly_temp, hourly_ghi, hour_numbers,
                                              load_curve, inv_eff, n_dis, n_chg, dod_max,
                                              diesel_price, end_year, start_year, pv_cost, charge_controller,
                                              pv_inverter, pv_om,
                                              diesel_cost, diesel_om, battery_inverter_life, battery_inverter_cost,
                                              diesel_life, pv_life,
                                              battery_cost, discount_rate, lpsp_max, diesel_limit,
                                              full_life_cycles)[0]

                return lcoe

            ret = differential_evolution(opt_func, bounds, popsize=15,
                                         init='latinhypercube')  # init='halton' on newer env

            X = [ret.x[0], ret.x[1], ret.x[2]]

            result = find_least_cost_option(X, hourly_temp, hourly_ghi, hour_numbers,
                                            load_curve, inv_eff, n_dis, n_chg, dod_max,
                                            diesel_price, end_year, start_year, pv_cost, charge_controller,
                                            pv_inverter, pv_om,
                                            diesel_cost, diesel_om, battery_inverter_life, battery_inverter_cost,
                                            diesel_life, pv_life,
                                            battery_cost, discount_rate, lpsp_max, diesel_limit,
                                            full_life_cycles)

            return result

        result = optimizer_de(diesel_price=diesel_price,
                              hourly_ghi=ghi_curve,
                              hourly_temp=temp,
                              load_curve=load_curve,
                              start_year=start_year,
                              end_year=end_year,
                              )

        return result[0], result[3], result[8] + result[9], result[4]

    def pv_hybrids_lcoe(self, year, time_step, end_year, mg_pv_hybrid_specs, pv_folder_path=r'../test_data'):
        #logging.info('Starting hybrid gen lcoe')
        print(time.ctime(), 'Starting PV-hybrid LCOE calculation for year {}'.format(year))

        self.df['PVHybridGenLCOE' + "{}".format(year)] = 0.

        pv_path = pv_folder_path
        # os.path.join(pv_folder_path, 'sl-2-pv.csv') # ToDo, should use multiple PV files
        ghi_curve, temp = read_environmental_data(pv_path)

        self.df['PotentialMG'] = np.where(((self.df[SET_POP + "{}".format(year)] > mg_pv_hybrid_specs['min_mg_connections'])
                                          & (self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] != 1) &
                                          (self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] != 2)) |
                                          (self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 5), 1, 0)

        gen_lcoe, inv, cap, fuel_cost = zip(
            *self.df.apply(lambda row: self.optimize_mini_grid(ghi_curve * ((ghi_curve.sum() / 1000) / row[SET_GHI]),
                                                               temp,
                                                               row[SET_ENERGY_PER_CELL + '{}'.format(year)],
                                                               row[SET_TIER],
                                                               row[SET_MG_DIESEL_FUEL + '{}'.format(year)],
                                                               year - time_step,
                                                               end_year,
                                                               year,
                                                               time_step,
                                                               mg_pv_hybrid_specs)
            if row['PotentialMG'] == 1
            else [99, 0, 0, 0],
                           axis=1))

        del self.df['PotentialMG']

        hybrid_lcoe = pd.Series(gen_lcoe)
        hybrid_capacity = pd.Series(cap)
        hybrid_investment = pd.Series(inv)
        fuel_cost = pd.Series(fuel_cost)
        emission_factor = fuel_cost / self.df[
            SET_MG_DIESEL_FUEL + '{}'.format(year)] * 256.9131097 * 9.9445485  # ToDo check emission factor
        self.df['PVHybridEmissionFactor' + "{}".format(year)] = emission_factor
        self.df['PVHybridGenLCOE' + "{}".format(year)] += hybrid_lcoe

        return hybrid_lcoe, hybrid_capacity, hybrid_investment

    def pv_hybrids_lcoe_lookuptable(self, year, time_step, end_year, mg_pv_hybrid_specs, pv_path=r'../test_data'):
        logging.info('Starting hybrid gen lcoe')
        # lats = sorted(self.df['Y_deg'].round().unique())
        # longs = sorted(self.df['X_deg'].round().unique())

        self.df['PVHybridGenLCOE' + "{}".format(year)] = 0.

        ghi_curve, temp = read_environmental_data(pv_path)

        ghi_min = round(min(self.df[SET_GHI]), -2)
        ghi_max = round(max(self.df[SET_GHI]), -2)
        diesel_min = round(min(self.df[SET_MG_DIESEL_FUEL + "{}".format(year)]), 1)
        diesel_max = round(max(self.df[SET_MG_DIESEL_FUEL + "{}".format(year)]), 1)
        ghi_range = np.round(np.arange(ghi_min, ghi_max + 100, 100), -2)
        diesel_range = np.round(np.arange(diesel_min, diesel_max + 0.1, 0.1), 1)

        tiers = [1, 2, 3, 4, 5]

        pv_hybrids_lcoe = {}
        pv_hybrid_investment = {}
        pv_hybrid_capacity = {}
        pv_hybrid_fuel_cost = {}

        for t in tiers:
            for g in ghi_range:
                for d in diesel_range:
                    gen_lcoe, inv, cap, fuel_cost = \
                        self.optimize_mini_grid(ghi_curve * g * 1000 / ghi_curve.sum(), #((ghi_curve.sum() / 1000) / g),
                                                temp,
                                                10000,
                                                t,
                                                d,
                                                year - time_step,
                                                end_year,
                                                year,
                                                time_step,
                                                mg_pv_hybrid_specs)

                    pv_hybrids_lcoe[t, g, d] = gen_lcoe
                    pv_hybrid_investment[t, g, d] = inv
                    pv_hybrid_capacity[t, g, d] = cap
                    pv_hybrid_fuel_cost[t, g, d] = fuel_cost

        def local_hybrid(ghi, diesel, tier, energy):
            ghi = round(ghi, -2)
            diesel = round(diesel, 1)

            hybrid_lcoe = pv_hybrids_lcoe[tier, ghi, diesel]
            hybrid_investment = pv_hybrid_investment[tier, ghi, diesel] #* (energy / 10000)
            hybrid_capacity = pv_hybrid_capacity[tier, ghi, diesel] #* (energy / 10000)
            hybrid_fuel_cost = pv_hybrid_fuel_cost[tier, ghi, diesel] #* (energy / 10000)

            return hybrid_lcoe, hybrid_investment, hybrid_capacity, hybrid_fuel_cost

        self.df['PotentialMG'] = np.where(
            ((self.df[SET_POP + "{}".format(year)] > mg_pv_hybrid_specs['min_mg_connections'])
             & (self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] != 1) &
             (self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] != 10)) |
            (self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 5), 1, 0)

        hybrid_series = self.df.apply(
            lambda row: local_hybrid(row[SET_GHI], row[SET_MG_DIESEL_FUEL + "{}".format(year)],
                                     row[SET_TIER], row[SET_ENERGY_PER_CELL + "{}".format(year)])
            if row['PotentialMG'] == 1
            else [99, 0, 0, 0],
            axis=1,
            result_type='expand')

        del self.df['PotentialMG']

        hybrid_lcoe = pd.Series(hybrid_series[0])
        hybrid_capacity = pd.Series(hybrid_series[2] * (self.df[SET_ENERGY_PER_CELL + "{}".format(year)] / 10000))
        hybrid_investment = pd.Series(hybrid_series[1] * (self.df[SET_ENERGY_PER_CELL + "{}".format(year)] / 10000))
        fuel_cost = pd.Series(hybrid_series[3] * (self.df[SET_ENERGY_PER_CELL + "{}".format(year)] / 10000))
        emission_factor = fuel_cost / self.df[
            SET_MG_DIESEL_FUEL + '{}'.format(year)] * 256.9131097 * 9.9445485  # ToDo check emission factor
        self.df['PVHybridEmissionFactor' + "{}".format(year)] = emission_factor
        self.df['PVHybridGenLCOE' + "{}".format(year)] += hybrid_lcoe

        return hybrid_lcoe, hybrid_capacity, hybrid_investment, pv_hybrid_investment

    @staticmethod
    def optimize_wind_mini_grid(wind_curve, energy, tier, diesel_price, start_year, end_year,
                                year, time_step, mg_wind_hybrid_specs):

        load_curve = calc_load_curve(tier, energy)

        def optimizer_wind_de(diesel_price,
                             hourly_wind,
                             load_curve,
                             diesel_cost=mg_wind_hybrid_specs['diesel_cost'],
                             discount_rate=mg_wind_hybrid_specs['discount_rate'],
                             n_chg=mg_wind_hybrid_specs['n_chg'],
                             n_dis=mg_wind_hybrid_specs['n_dis'],
                             battery_cost=mg_wind_hybrid_specs['battery_cost'],
                             wind_cost=mg_wind_hybrid_specs['wind_cost'],
                             charge_controller=mg_wind_hybrid_specs['charge_controller'],
                             wind_life=mg_wind_hybrid_specs['wind_life'],
                             diesel_life=mg_wind_hybrid_specs['diesel_life'],
                             wind_om=mg_wind_hybrid_specs['wind_om'],
                             diesel_om=mg_wind_hybrid_specs['diesel_om'],
                             battery_inverter_cost=mg_wind_hybrid_specs['battery_inverter_cost'],
                             battery_inverter_life=mg_wind_hybrid_specs['battery_inverter_life'],
                             dod_max=mg_wind_hybrid_specs['dod_max'],
                             inv_eff=mg_wind_hybrid_specs['inv_eff'],
                             lpsp_max=mg_wind_hybrid_specs['lpsp_max'],
                             diesel_limit=mg_wind_hybrid_specs['diesel_limit'],
                             full_life_cycles=mg_wind_hybrid_specs['full_life_cycles'],
                             start_year=year - time_step,
                             end_year=end_year,
                             ):

            demand = load_curve.sum()

            # The following lines defines the solution space for the Particle Swarm Optimization (PSO) algorithm
            battery_bounds = [0, 5 * demand / 365]
            wind_bounds = [0, 10 * max(load_curve)]
            diesel_bounds = [0.5, max(load_curve)]

            min_bounds = np.array([wind_bounds[0], battery_bounds[0], diesel_bounds[0]])
            max_bounds = np.array([wind_bounds[1], battery_bounds[1], diesel_bounds[1]])
            bounds = Bounds(min_bounds, max_bounds)

            #  This creates a series of the hour numbers (0-24) for one year
            hour_numbers = np.empty(8760)
            for i in prange(365):
                for j in prange(24):
                    hour_numbers[i * 24 + j] = j

            # def opt_func(X):
            #     lcoe = find_least_cost_option_wind(X, hourly_wind, hour_numbers, load_curve, inv_eff, n_dis, n_chg,
            #                                        dod_max, diesel_price, end_year, start_year, wind_cost,
            #                                        charge_controller, wind_om, diesel_cost, diesel_om,
            #                                        battery_inverter_life, battery_inverter_cost, diesel_life,
            #                                        wind_life, battery_cost, discount_rate, lpsp_max, diesel_limit,
            #                                        full_life_cycles)[0]
            #
            #     return lcoe
            #
            # ret = differential_evolution(opt_func, bounds, popsize=15,
            #                              init='latinhypercube')  # init='halton' on newer env
            #
            # X = [ret.x[0], ret.x[1], ret.x[2]]

            X = [(wind_bounds[0] + wind_bounds[1])/2, (battery_bounds[0] + battery_bounds[1])/2, (diesel_bounds[0] + diesel_bounds[1])/2]

            result = find_least_cost_option_wind(X, hourly_wind, hour_numbers, load_curve, inv_eff, n_dis, n_chg,
                                                 dod_max, diesel_price, end_year, start_year, wind_cost,
                                                 charge_controller, wind_om, diesel_cost, diesel_om,
                                                 battery_inverter_life, battery_inverter_cost, diesel_life, wind_life,
                                                 battery_cost, discount_rate, lpsp_max, diesel_limit, full_life_cycles)

            return result

        result = optimizer_wind_de(diesel_price=diesel_price,
                                   hourly_wind=wind_curve,
                                   load_curve=load_curve,
                                   start_year=start_year,
                                   end_year=end_year,
                                   )

        return result[0], result[3], result[8] + result[9], result[4]

    def wind_hybrids_lcoe(self, year, time_step, end_year, mg_wind_hybrid_specs, wind_folder_path=r'../test_data'):
        #logging.info('Starting hybrid gen lcoe')
        print(time.ctime(), 'Starting Wind-hybrid LCOE calculation for year {}'.format(year))

        self.df['windHybridGenLCOE' + "{}".format(year)] = 0.

        wind_path = wind_folder_path
        # os.path.join(wind_folder_path, 'sl-2-wind.csv') # ToDo, should use multiple wind files
        wind_curve = read_wind_environmental_data(wind_path)

        self.df['PotentialMG'] = np.where(((self.df[SET_POP + "{}".format(year)] > mg_wind_hybrid_specs['min_mg_connections'])
                                          & (self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] != 1) &
                                          (self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] != 10)) |
                                          (self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 5), 1, 0)

        gen_lcoe, inv, cap, fuel_cost = zip(
            *self.df.apply(lambda row: self.optimize_mini_grid_wind(wind_curve * row[SET_WINDVEL] / np.average(wind_curve),
                                                                    row[SET_ENERGY_PER_CELL + '{}'.format(year)],
                                                                    row[SET_TIER],
                                                                    row[SET_MG_DIESEL_FUEL + '{}'.format(year)],
                                                                    year - time_step,
                                                                    end_year,
                                                                    year,
                                                                    time_step,
                                                                    mg_wind_hybrid_specs)
            if row['PotentialMG'] == 1
            else [99, 0, 0, 0],
                           axis=1))

        del self.df['PotentialMG']

        hybrid_lcoe = pd.Series(gen_lcoe)
        hybrid_capacity = pd.Series(cap)
        hybrid_investment = pd.Series(inv)
        fuel_cost = pd.Series(fuel_cost)
        emission_factor = fuel_cost / self.df[
            SET_MG_DIESEL_FUEL + '{}'.format(year)] * 256.9131097 * 9.9445485  # ToDo check emission factor
        self.df['windHybridEmissionFactor' + "{}".format(year)] = emission_factor
        self.df['windHybridGenLCOE' + "{}".format(year)] += hybrid_lcoe

        return hybrid_lcoe, hybrid_capacity, hybrid_investment

    def wind_hybrids_lcoe_lookuptable(self, year, time_step, end_year, mg_wind_hybrid_specs, wind_path=r'../test_data'):
        logging.info('Starting wind hybrid gen lcoe')
        # lats = sorted(self.df['Y_deg'].round().unique())
        # longs = sorted(self.df['X_deg'].round().unique())

        self.df['windHybridGenLCOE' + "{}".format(year)] = 0.

        wind_curve = read_wind_environmental_data(wind_path)

        wind_min = round(min(self.df[SET_WINDVEL]))
        wind_max = round(max(self.df[SET_WINDVEL]))
        diesel_min = round(min(self.df[SET_MG_DIESEL_FUEL + "{}".format(year)]), 1)
        diesel_max = round(max(self.df[SET_MG_DIESEL_FUEL + "{}".format(year)]), 1)
        wind_range = np.round(np.arange(wind_min, wind_max + 1))
        diesel_range = np.round(np.arange(diesel_min, diesel_max + 0.1, 0.1), 1)

        tiers = [1, 2, 3, 4, 5]

        wind_hybrids_lcoe = {}
        wind_hybrid_investment = {}
        wind_hybrid_capacity = {}
        wind_hybrid_fuel_cost = {}

        for t in tiers:
            for g in wind_range:
                for d in diesel_range:
                    gen_lcoe, inv, cap, fuel_cost = \
                        self.optimize_wind_mini_grid(wind_curve * g / np.average(wind_curve),
                                                     10000,
                                                     t,
                                                     d,
                                                     year - time_step,
                                                     end_year,
                                                     year,
                                                     time_step,
                                                     mg_wind_hybrid_specs)

                    wind_hybrids_lcoe[t, g, d] = gen_lcoe
                    wind_hybrid_investment[t, g, d] = inv
                    wind_hybrid_capacity[t, g, d] = cap
                    wind_hybrid_fuel_cost[t, g, d] = fuel_cost

        def local_hybrid(wind, diesel, tier, energy):
            wind = round(wind)
            diesel = round(diesel, 1)

            hybrid_lcoe = wind_hybrids_lcoe[tier, wind, diesel]
            hybrid_investment = wind_hybrid_investment[tier, wind, diesel] #* (energy / 10000)
            hybrid_capacity = wind_hybrid_capacity[tier, wind, diesel] #* (energy / 10000)
            hybrid_fuel_cost = wind_hybrid_fuel_cost[tier, wind, diesel] #* (energy / 10000)

            return hybrid_lcoe, hybrid_investment, hybrid_capacity, hybrid_fuel_cost

        self.df['PotentialMG'] = np.where(
            ((self.df[SET_POP + "{}".format(year)] > mg_wind_hybrid_specs['min_mg_connections'])
             & (self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] != 1) &
             (self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] != 2)) |
            (self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 5), 1, 0)

        hybrid_series = self.df.apply(
            lambda row: local_hybrid(row[SET_WINDVEL], row[SET_MG_DIESEL_FUEL + "{}".format(year)],
                                     row[SET_TIER], row[SET_ENERGY_PER_CELL + "{}".format(year)])
            if row['PotentialMG'] == 1
            else [99, 0, 0, 0],
            axis=1,
            result_type='expand')

        del self.df['PotentialMG']

        hybrid_lcoe = pd.Series(hybrid_series[0])
        hybrid_capacity = pd.Series(hybrid_series[2] * (self.df[SET_ENERGY_PER_CELL + "{}".format(year)] / 10000))
        hybrid_investment = pd.Series(hybrid_series[1] * (self.df[SET_ENERGY_PER_CELL + "{}".format(year)] / 10000))
        fuel_cost = pd.Series(hybrid_series[3] * (self.df[SET_ENERGY_PER_CELL + "{}".format(year)] / 10000))
        emission_factor = fuel_cost / self.df[
            SET_MG_DIESEL_FUEL + '{}'.format(year)] * 256.9131097 * 9.9445485  # ToDo check emission factor
        self.df['windHybridEmissionFactor' + "{}".format(year)] = emission_factor
        self.df['windHybridGenLCOE' + "{}".format(year)] += hybrid_lcoe

        return hybrid_lcoe, hybrid_capacity, hybrid_investment, wind_hybrid_investment

    def calculate_off_grid_lcoes(self, mg_hydro_calc, mg_wind_hybrid_calc, sa_pv_calc,  mg_pv_hybrid_calc, year, end_year, time_step, techs, tech_codes,
                                 min_mg_size=0, mg_min_grid_dist=0):
        """
        Calculate the LCOEs for all off-grid technologies
        """

        print(time.ctime(), 'Starting off-grid LCOE calculation for year {}'.format(year))

        logging.info('Calculate minigrid hydro LCOE')
        self.df[SET_LCOE_MG_HYDRO + "{}".format(year)], mg_hydro_investment, mg_hydro_capacity = \
            mg_hydro_calc.get_lcoe(energy_per_cell=self.df[SET_ENERGY_PER_CELL + "{}".format(year)],
                                   start_year=year - time_step,
                                   end_year=end_year,
                                   people=self.df[SET_POP + "{}".format(year)],
                                   new_connections=self.df[SET_NEW_CONNECTIONS + "{}".format(year)],
                                   total_energy_per_cell=self.df[SET_TOTAL_ENERGY_PER_CELL],
                                   prev_code=self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)],
                                   num_people_per_hh=self.df[SET_NUM_PEOPLE_PER_HH],
                                   grid_cell_area=self.df[SET_GRID_CELL_AREA],
                                   additional_mv_line_length=self.df[SET_HYDRO_DIST],
                                   capacity_factor=mg_hydro_calc.capacity_factor,
                                   base_to_peak_load_ratio=self.df[SET_AVERAGE_TO_PEAK]
                                   )

        self.df.loc[(self.df[SET_POP + "{}".format(year)] / self.df[SET_NUM_PEOPLE_PER_HH]) < min_mg_size, SET_LCOE_MG_HYDRO + "{}".format(year)] = 99
        self.df.loc[self.df[SET_MV_DIST_CURRENT] < mg_min_grid_dist, SET_LCOE_MG_HYDRO + "{}".format(year)] = 99

        logging.info('Calculate minigrid PV Hybrid LCOE')
        self.df[SET_LCOE_MG_PV_HYBRID + "{}".format(year)], mg_pv_hybrid_investment, mg_pv_hybrid_capacity = \
            mg_pv_hybrid_calc.get_lcoe(energy_per_cell=self.df[SET_ENERGY_PER_CELL + "{}".format(year)],
                                       start_year=year - time_step,
                                       end_year=end_year,
                                       people=self.df[SET_POP + "{}".format(year)],
                                       new_connections=self.df[SET_NEW_CONNECTIONS + "{}".format(year)],
                                       total_energy_per_cell=self.df[SET_TOTAL_ENERGY_PER_CELL],
                                       prev_code=self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)],
                                       num_people_per_hh=self.df[SET_NUM_PEOPLE_PER_HH],
                                       grid_cell_area=self.df[SET_GRID_CELL_AREA],
                                       capacity_factor=self.df[SET_GHI] / HOURS_PER_YEAR,
                                       base_to_peak_load_ratio=self.df[SET_AVERAGE_TO_PEAK]
                                       )

        self.df.loc[self.df[SET_LCOE_MG_PV_HYBRID + "{}".format(year)] > 99, SET_LCOE_MG_PV_HYBRID + "{}".format(year)] = 99

        self.df.loc[(self.df[SET_POP + "{}".format(year)] / self.df[SET_NUM_PEOPLE_PER_HH]) < min_mg_size, SET_LCOE_MG_PV_HYBRID + "{}".format(year)] = 99
        self.df.loc[self.df[SET_MV_DIST_CURRENT] < mg_min_grid_dist, SET_LCOE_MG_PV_HYBRID + "{}".format(year)] = 99

        self.df.loc[self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 5, SET_LCOE_MG_PV_HYBRID + "{}".format(year)] = 0.01 # ToDo ensure remain mg

        logging.info('Calculate minigrid Wind Hybrid LCOE')
        self.df[SET_LCOE_MG_WIND + "{}".format(year)], mg_wind_investment, mg_wind_capacity = \
            mg_wind_hybrid_calc.get_lcoe(energy_per_cell=self.df[SET_ENERGY_PER_CELL + "{}".format(year)],
                                         start_year=year - time_step,
                                         end_year=end_year,
                                         people=self.df[SET_POP + "{}".format(year)],
                                         new_connections=self.df[SET_NEW_CONNECTIONS + "{}".format(year)],
                                         total_energy_per_cell=self.df[SET_TOTAL_ENERGY_PER_CELL],
                                         prev_code=self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)],
                                         num_people_per_hh=self.df[SET_NUM_PEOPLE_PER_HH],
                                         grid_cell_area=self.df[SET_GRID_CELL_AREA],
                                         capacity_factor=self.df[SET_WINDCF],
                                         base_to_peak_load_ratio=self.df[SET_AVERAGE_TO_PEAK])
        self.df.loc[self.df[SET_LCOE_MG_WIND + "{}".format(year)] > 99, SET_LCOE_MG_WIND + "{}".format(year)] = 99

        self.df.loc[(self.df[SET_POP + "{}".format(year)] / self.df[SET_NUM_PEOPLE_PER_HH]) < min_mg_size, SET_LCOE_MG_WIND + "{}".format(year)] = 99
        self.df.loc[self.df[SET_MV_DIST_CURRENT] < mg_min_grid_dist, SET_LCOE_MG_WIND + "{}".format(year)] = 99

        logging.info('Calculate standalone PV LCOE')
        self.df[SET_LCOE_SA_PV + "{}".format(year)], sa_pv_investment, sa_pv_capacity = \
            sa_pv_calc.get_lcoe(energy_per_cell=self.df[SET_ENERGY_PER_CELL + "{}".format(year)],
                                start_year=year - time_step,
                                end_year=end_year,
                                people=self.df[SET_POP + "{}".format(year)],
                                new_connections=self.df[SET_NEW_CONNECTIONS + "{}".format(year)],
                                total_energy_per_cell=self.df[SET_TOTAL_ENERGY_PER_CELL],
                                prev_code=self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)],
                                num_people_per_hh=self.df[SET_NUM_PEOPLE_PER_HH],
                                grid_cell_area=self.df[SET_GRID_CELL_AREA],
                                capacity_factor=self.df[SET_GHI] / HOURS_PER_YEAR,
                                base_to_peak_load_ratio=sa_pv_calc.base_to_peak_load_ratio)

        self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] != 3) &
                    (self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] != 99),
                    SET_LCOE_SA_PV + "{}".format(year)] = 99

        self.choose_minimum_off_grid_tech(year, mg_hydro_calc, techs, tech_codes, sa_pv_investment,
                                          mg_pv_hybrid_investment, mg_wind_investment, mg_hydro_investment)

        return sa_pv_investment, sa_pv_capacity, mg_pv_hybrid_investment, mg_pv_hybrid_capacity, mg_wind_investment, \
            mg_wind_capacity, mg_hydro_investment, mg_hydro_capacity

    def choose_minimum_off_grid_tech(self, year, mg_hydro_calc, techs, tech_codes, sa_pv_investment,
                                     mg_pv_hybrid_investment, mg_wind_investment, mg_hydro_investment):
        """Choose minimum LCOE off-grid technology

        First step determines the off-grid technology with minimum LCOE
        Second step determines the value (number) of the selected minimum off-grid technology

        Arguments
        ---------
        year : int
        mg_hydro_calc : dict
        """
        off_grid_techs = techs.copy()
        del off_grid_techs[0]
        # del off_grid_techs[0]
        off_grid_techs = [x + str(year) for x in off_grid_techs]

        off_grid_tech_codes = tech_codes.copy()
        del off_grid_tech_codes[0]
        # del off_grid_tech_codes[0]

        logging.info('Determine minimum technology (off-grid)')
        self.df[SET_MIN_OFFGRID + "{}".format(year)] = self.df[off_grid_techs].T.idxmin()

        logging.info('Ensure hydro-power is not over-utilized')
        self.limit_hydro_usage(mg_hydro_calc, year)

        self.df[SET_MIN_OFFGRID + "{}".format(year)] = self.df[off_grid_techs].T.idxmin()

        logging.info('Determine minimum off-grid tech LCOE')
        self.df[SET_MIN_OFFGRID_LCOE + "{}".format(year)] = self.df[off_grid_techs].T.min()

        # Add code numbers reflecting minimum off-grid technology code
        for i in range(len(off_grid_techs)):
            self.df.loc[self.df[SET_MIN_OFFGRID + "{}".format(year)] == off_grid_techs[i],
                        SET_MIN_OFFGRID_CODE + "{}".format(year)] = off_grid_tech_codes[i]

        sa_diesel = pd.DataFrame(np.where(self.df[SET_MIN_OFFGRID_CODE + "{}".format(year)] == 2, 1, 0))
        sa_pv = pd.DataFrame(np.where(self.df[SET_MIN_OFFGRID_CODE + "{}".format(year)] == 3, 1, 0))
        mg_diesel = pd.DataFrame(np.where(self.df[SET_MIN_OFFGRID_CODE + "{}".format(year)] == 4, 1, 0))
        mg_pv_hybrid = pd.DataFrame(np.where(self.df[SET_MIN_OFFGRID_CODE + "{}".format(year)] == 5, 1, 0))
        mg_wind = pd.DataFrame(np.where(self.df[SET_MIN_OFFGRID_CODE + "{}".format(year)] == 6, 1, 0))
        mg_hydro = pd.DataFrame(np.where(self.df[SET_MIN_OFFGRID_CODE + "{}".format(year)] == 7, 1, 0))

        sa_pv_investment.fillna(0, inplace=True)
        mg_pv_hybrid_investment.fillna(0, inplace=True)
        mg_wind_investment.fillna(0, inplace=True)
        mg_hydro_investment.fillna(0, inplace=True)

        logging.info('Calculate investment cost')
        print(time.ctime(), 'Calculating off-grid investment cost for year {}'.format(year))

        self.df['OffGridInvestmentCost' + "{}".format(year)] = 0.
        self.df['OffGridInvestmentCost' + "{}".format(year)] = sa_pv * sa_pv_investment + \
                                                           mg_pv_hybrid * mg_pv_hybrid_investment + \
                                                           mg_wind * mg_wind_investment + mg_hydro * mg_hydro_investment

    def limit_hydro_usage(self, mg_hydro_calc, year):
        # A df with all hydro-power sites, to ensure that they aren't assigned more capacity than is available
        hydro_used = 'HydropowerUsed'  # the amount of the hydro potential that has been assigned
        hydro_lcoe = self.df[SET_LCOE_MG_HYDRO + "{}".format(year)].copy()
        hydro_df = self.df[[SET_HYDRO_FID, SET_HYDRO]].drop_duplicates(subset=SET_HYDRO_FID)
        hydro_df[hydro_used] = 0
        hydro_df = hydro_df.set_index(SET_HYDRO_FID)
        max_hydro_dist = 5  # the max distance in km to consider hydropower viable
        additional_capacity = (
                (self.df[SET_ENERGY_PER_CELL + "{}".format(year)]) /
                (HOURS_PER_YEAR * mg_hydro_calc.capacity_factor * self.df[SET_AVERAGE_TO_PEAK] *
                 (1 - mg_hydro_calc.distribution_losses)))

        for index, row in hydro_df.iterrows():
            hydro_usage = additional_capacity.loc[(self.df[SET_HYDRO_FID] == index) &
                                                  (self.df[SET_HYDRO_DIST] < max_hydro_dist)].sum()
            if hydro_usage > hydro_df[SET_HYDRO][index]:
                hydro_usage_cumsum = additional_capacity.loc[(self.df[SET_HYDRO_FID] == index) &
                                                             (self.df[SET_HYDRO_DIST] < max_hydro_dist)].cumsum()
                hydro_usage = hydro_usage_cumsum.loc[hydro_usage_cumsum > hydro_df[SET_HYDRO][index]]
                hydro_lcoe[hydro_usage.index] = 99

        self.df[SET_LCOE_MG_HYDRO + "{}".format(year)] = hydro_lcoe

        self.df.loc[self.df[SET_HYDRO_DIST] > max_hydro_dist, SET_LCOE_MG_HYDRO + "{}".format(year)] = 99

    def results_columns(self, techs, tech_codes, year, time_step, auto_intensification, mg_interconnection=False):
        """Calculate the capacity and investment requirements for each settlement

        Once the grid extension algorithm has been run, determine the minimum overall option,
        and calculate the capacity and investment requirements for each settlement

        Arguments
        ---------
        year : int

        """

        all_techs = [x + str(year) for x in techs]

        logging.info('Determine minimum overall tech')
        self.df[SET_MIN_OVERALL + "{}".format(year)] = self.df[all_techs].T.idxmin()

        # Ensure what is grid-connected in previous time-step remains grid-connected
        self.df.loc[self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] < 3,
                    SET_MIN_OVERALL + "{}".format(year)] = 'Grid' + "{}".format(year)

        self.df.loc[self.df[SET_LCOE_GRID + "{}".format(year)] < 99, SET_MIN_OVERALL + "{}".format(year)] = 'Grid' + "{}".format(year)

        # If mini-grids are not allowed to be interconnected, ensure they remain mini-grids
        if not mg_interconnection:
            self.df.loc[self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 7,
                        SET_MIN_OVERALL + "{}".format(year)] = SET_LCOE_MG_HYDRO + "{}".format(year)
            self.df.loc[self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 5,
                        SET_MIN_OVERALL + "{}".format(year)] = SET_LCOE_MG_PV_HYBRID + "{}".format(year)
            self.df.loc[self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 6,
                        SET_MIN_OVERALL + "{}".format(year)] = SET_LCOE_MG_WIND + "{}".format(year)

        # Ensure settlements within intensification distance are grid-connected
        self.df.loc[(self.df[SET_MV_DIST_PLANNED] < auto_intensification) &
                    (self.df[SET_LCOE_GRID + "{}".format(year)] != 99),
                    SET_MIN_OVERALL + "{}".format(year)] = 'Grid' + "{}".format(year)

        logging.info('Determine minimum overall LCOE')
        self.df[SET_MIN_OVERALL_LCOE + "{}".format(year)] = self.df[all_techs].T.min()

        for i in range(len(techs)):
            self.df.loc[self.df[SET_MIN_OVERALL + "{}".format(year)] == all_techs[i],
                        SET_MIN_OVERALL_CODE + "{}".format(year)] = tech_codes[i]

    def calculate_investments_and_capacity(self, sa_pv_investment, sa_pv_capacity, mg_pv_hybrid_investment,
                                           mg_pv_hybrid_capacity, mg_wind_investment, mg_wind_capacity,
                                           mg_hydro_investment, mg_hydro_capacity, grid_investment, grid_capacity,
                                           year):

        grid = pd.DataFrame(np.where(self.df[SET_MIN_OVERALL_CODE + "{}".format(year)] == 1, 1, 0))
        sa_diesel = pd.DataFrame(np.where(self.df[SET_MIN_OVERALL_CODE + "{}".format(year)] == 2, 1, 0))
        sa_pv = pd.DataFrame(np.where(self.df[SET_MIN_OVERALL_CODE + "{}".format(year)] == 3, 1, 0))
        mg_diesel = pd.DataFrame(np.where(self.df[SET_MIN_OVERALL_CODE + "{}".format(year)] == 4, 1, 0))
        # mg_pv = pd.DataFrame(np.where(self.df[SET_MIN_OVERALL_CODE + "{}".format(year)] == 5, 1, 0))
        mg_pv_hybrid = pd.DataFrame(np.where(self.df[SET_MIN_OVERALL_CODE + "{}".format(year)] == 5, 1, 0))
        mg_wind = pd.DataFrame(np.where(self.df[SET_MIN_OVERALL_CODE + "{}".format(year)] == 6, 1, 0))
        mg_hydro = pd.DataFrame(np.where(self.df[SET_MIN_OVERALL_CODE + "{}".format(year)] == 7, 1, 0))

        sa_pv_investment.fillna(0, inplace=True)
        mg_pv_hybrid_investment.fillna(0, inplace=True)
        mg_wind_investment.fillna(0, inplace=True)
        mg_hydro_investment.fillna(0, inplace=True)
        grid_investment.fillna(0, inplace=True)

        sa_pv_investment.replace([np.inf, -np.inf], 0, inplace=True)
        mg_pv_hybrid_investment.replace([np.inf, -np.inf], 0, inplace=True)
        mg_wind_investment.replace([np.inf, -np.inf], 0, inplace=True)
        mg_hydro_investment.replace([np.inf, -np.inf], 0, inplace=True)
        grid_investment.replace([np.inf, -np.inf], 0, inplace=True)

        logging.info('Calculate investment cost')

        self.df[SET_INVESTMENT_COST + "{}".format(year)] = 0

        self.df[SET_INVESTMENT_COST + "{}".format(year)] = grid * grid_investment + \
                                                           sa_pv * sa_pv_investment + \
                                                           mg_pv_hybrid * mg_pv_hybrid_investment + \
                                                           mg_wind * mg_wind_investment + mg_hydro * mg_hydro_investment

        logging.info('Calculate new capacity')

        sa_pv_capacity.fillna(0, inplace=True)
        mg_pv_hybrid_capacity.fillna(0, inplace=True)
        mg_wind_capacity.fillna(0, inplace=True)
        mg_hydro_capacity.fillna(0, inplace=True)
        grid_capacity.fillna(0, inplace=True)

        sa_pv_capacity.replace([np.inf, -np.inf], 0, inplace=True)
        mg_pv_hybrid_capacity.replace([np.inf, -np.inf], 0, inplace=True)
        mg_wind_capacity.replace([np.inf, -np.inf], 0, inplace=True)
        mg_hydro_capacity.replace([np.inf, -np.inf], 0, inplace=True)
        grid_capacity.replace([np.inf, -np.inf], 0, inplace=True)

        self.df[SET_NEW_CAPACITY + "{}".format(year)] = 0

        self.df[SET_NEW_CAPACITY + "{}".format(year)] = grid * grid_capacity + sa_pv * sa_pv_capacity + \
                                                        mg_pv_hybrid * mg_pv_hybrid_capacity + \
                                                        mg_wind * mg_wind_capacity + mg_hydro * mg_hydro_capacity
    def pre_selection(self, eleclimit, year, time_step, auto_densification=0, prio_choice=5):

        self.df['PreSelection' + "{}".format(year)] = 0

        # Calculate the total population targeted to be electrified
        elec_target_pop = eleclimit * self.df[SET_POP + "{}".format(year)].sum()

        # Adding a column with investment/connection
        self.df[SET_INVEST_PER_CONNECTION + "{}".format(year)] = \
            self.df['OffGridInvestmentCost' + "{}".format(year)] / self.df[SET_NEW_CONNECTIONS + "{}".format(year)]

        if eleclimit == 1:
            # If electrification target rate is 100%, set all settlements to electrified
            self.df['PreSelection' + "{}".format(year)] = 1
            elecrate = 1

        else:

            self.df['Intensification'] = np.where((self.df[SET_MV_DIST_PLANNED] < auto_densification) & (self.df['MaxDist' + '{}'.format(year)] >= 0), 0, 1)

            if prio_choice == 5:
                self.df.sort_values(by=[SET_ELEC_FINAL_CODE + "{}".format(year - time_step),
                                        SET_POP + "{}".format(year)], inplace=True)

            elif prio_choice == 4:

                self.df.sort_values(by=[SET_ELEC_FINAL_CODE + "{}".format(year - time_step),
                                        'Intensification',
                                        SET_INVEST_PER_CONNECTION + "{}".format(year)], inplace=True)
            elif prio_choice == 3:

                self.df['SetSize'] = self.df[SET_POP] * -1

                self.df.sort_values(by=[SET_ELEC_FINAL_CODE + "{}".format(year - time_step),
                                        'Intensification',
                                        'SetSize'], inplace=True)

                del self.df['SetSize']

            elif prio_choice == 2:
                self.df.sort_values(by=[SET_ELEC_FINAL_CODE + "{}".format(year - time_step),
                                        'Intensification',
                                        SET_TRAVEL_HOURS], inplace=True)
            elif prio_choice == 1:
                self.df.sort_values(by=[SET_ELEC_FINAL_CODE + "{}".format(year - time_step),
                                        'Intensification',
                                        SET_ROAD_DIST], inplace=True)

            self.df['Elec_POP'] = self.df[SET_ELEC_POP + "{}".format(year - time_step)] + self.df[
                SET_NEW_CONNECTIONS + "{}".format(year)] * self.df[SET_NUM_PEOPLE_PER_HH]
            cumulative_pop = self.df['Elec_POP'].cumsum()
            cumulative_pop = self.df[SET_POP + "{}".format(year)].cumsum()

            self.df['PreSelection' + "{}".format(year)] = np.where(cumulative_pop < elec_target_pop, 1, 0)

            del self.df['Intensification']


            self.df.sort_index(inplace=True)

            # Ensure already electrified settlements remain electrified
            self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] < 99),
                        'PreSelection' + "{}".format(year)] = 1

            elecrate = self.df.loc[self.df['PreSelection' + "{}".format(year)] == 1, 'Elec_POP'].sum() / \
                self.df[SET_POP + "{}".format(year)].sum()

            del self.df['Elec_POP']

        del self.df[SET_INVEST_PER_CONNECTION + "{}".format(year)]

    def apply_limitations(self, eleclimit, year, time_step, auto_densification=0):

        logging.info('Determine electrification limits')
        self.df[SET_LIMIT + "{}".format(year)] = 0

        # Calculate the total population targeted to be electrified
        elec_target_pop = eleclimit * self.df[SET_POP + "{}".format(year)].sum()

        # Adding a column with investment/connection
        self.df[SET_INVEST_PER_CONNECTION + "{}".format(year)] = \
            self.df[SET_INVESTMENT_COST + "{}".format(year)] / self.df[SET_NEW_CONNECTIONS + "{}".format(year)]

        if eleclimit == 1:
            # If electrification target rate is 100%, set all settlements to electrified
            self.df[SET_LIMIT + "{}".format(year)] = 1
            elecrate = 1

        else:
            # Prioritize already electrified settlements, then intensification, then lowest investment per connection

            # self.df['Intensification'] = np.where(self.df[SET_MV_DIST_PLANNED] < auto_densification, 1, 0)

            self.df.sort_values(by=['PreSelection' + "{}".format(year)], inplace=True, ascending=False)

            self.df['Elec_POP'] = self.df[SET_ELEC_POP + "{}".format(year - time_step)] + self.df[
                SET_NEW_CONNECTIONS + "{}".format(year)] * self.df[SET_NUM_PEOPLE_PER_HH]
            cumulative_pop = self.df['Elec_POP'].cumsum() # ToDo check if works correctly
            cumulative_pop = self.df[SET_POP + "{}".format(year)].cumsum()

            self.df[SET_LIMIT + "{}".format(year)] = np.where(cumulative_pop < elec_target_pop, 1, 0)

            # del self.df['Intensification']

            self.df.sort_index(inplace=True)

            # Ensure already electrified settlements remain electrified
            self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] < 99),
                        SET_LIMIT + "{}".format(year)] = 1

            elecrate = self.df.loc[self.df[SET_LIMIT + "{}".format(year)] == 1, SET_POP + "{}".format(year)].sum() / \
                self.df[SET_POP + "{}".format(year)].sum()

        logging.info('Determine final electrification decision')
        self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] = self.df[SET_MIN_OVERALL_CODE + "{}".format(year)]
        self.df.loc[(self.df[SET_LIMIT + "{}".format(year)] == 0), SET_ELEC_FINAL_CODE + "{}".format(year)] = 99
        self.df.loc[(self.df[SET_LIMIT + "{}".format(year)] == 0), SET_INVESTMENT_COST + "{}".format(year)] = 0
        self.df.loc[(self.df[SET_LIMIT + "{}".format(year)] == 0), SET_NEW_CAPACITY + "{}".format(year)] = 0
        self.df.loc[(self.df[SET_MIN_OVERALL_CODE + "{}".format(year)] == 1) & (
                    self.df[SET_LIMIT + "{}".format(year)] == 0), SET_ELEC_ORDER] = 0
        self.df.loc[(self.df[SET_MIN_OVERALL_CODE + "{}".format(year)] == 1) & (
                    self.df[SET_LIMIT + "{}".format(year)] == 0), SET_MIN_GRID_DIST + "{}".format(year)] = 0
        self.df.loc[(self.df[SET_MIN_OVERALL_CODE + "{}".format(year)] == 1) & (
                    self.df[SET_LIMIT + "{}".format(year)] == 0), SET_MV_CONNECT_DIST] = 0

        if eleclimit == 1:
            self.df[SET_ELEC_POP + "{}".format(year)] = self.df[SET_POP + "{}".format(year)]
        else:
            self.df[SET_ELEC_POP + "{}".format(year)] = 0.
            self.df.loc[self.df[SET_LIMIT + "{}".format(year)] == 1, SET_ELEC_POP + "{}".format(year)] = self.df[
                'Elec_POP']
            del self.df['Elec_POP']

        self.df['Technology{}'.format(year)] = 'Unelectrified'
        self.df.loc[self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 1, 'Technology{}'.format(year)] = 'Existing grid'
        self.df.loc[self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 2, 'Technology{}'.format(year)] = 'Grid extension'
        self.df.loc[self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 3, 'Technology{}'.format(year)] = 'SHS'
        self.df.loc[self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 5, 'Technology{}'.format(year)] = 'PV Hybrid Mini-Grid'
        self.df.loc[self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 6, 'Technology{}'.format(year)] = 'Wind Hybrid Mini-Grid'
        self.df.loc[self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 7, 'Technology{}'.format(year)] = 'Hydro Mini-Grid'

        print("The electrification rate achieved in {} is {:.1f} %".format(year, elecrate * 100))

    def check_grid_limitations(self, grid_connect_limit, grid_cap_limit, year, time_step, final=False):

        # ToDo is there a need to check also total elec_limit with densification???

        new_grid_conn = self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] <= 2), SET_NEW_CONNECTIONS + "{}".format(year)].sum()

        new_grid_cap = self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] <= 2), SET_NEW_CAPACITY + "{}".format(year)].sum()

        connect_factor = grid_connect_limit / new_grid_conn
        cap_factor = grid_cap_limit / new_grid_cap

        factor = min(connect_factor, cap_factor)

        if factor < 1:
            if final:
                if connect_factor < 1:
                    print('Maximum number of grid connections were not enough to meet densification demand, results have more grid connections than the limit')
                if cap_factor < 1:
                    print('Maximum new grid generation capacity was not enough to meet densification demand, results have more grid capacity than the limit')
            if not final:
                self.df.loc[self.df[SET_MIN_OVERALL + "{}".format(year)] == SET_LCOE_GRID + "{}".format(year), SET_NEW_CONNECTIONS + "{}".format(year)] *= factor
                self.df.loc[self.df[SET_MIN_OVERALL + "{}".format(year)] == SET_LCOE_GRID + "{}".format(year), SET_NEW_CAPACITY + "{}".format(year)] *= factor
                self.df.loc[self.df[SET_MIN_OVERALL + "{}".format(year)] == SET_LCOE_GRID + "{}".format(year), SET_INVESTMENT_COST + "{}".format(year)] *= factor

            self.df.loc[self.df[SET_MIN_OVERALL + "{}".format(year)] == 1, SET_ELEC_POP + "{}".format(year)] = \
                self.df[SET_POP + "{}".format(year - time_step)] + self.df[SET_NEW_CONNECTIONS + "{}".format(year)]

    def calc_summaries(self, df_summary, sumtechs, tech_codes, year, base_year):

        """The next section calculates the summaries for technology split,
        capacity added and total investment cost"""

        logging.info('Calculate summaries')

        i = 0

        summaries = [SET_ELEC_POP, SET_NEW_CONNECTIONS, SET_NEW_CAPACITY, SET_INVESTMENT_COST, 'AnnualEmissions']

        # Population Summaries
        for s in summaries:
            for t in tech_codes:
                df_summary.loc[sumtechs[i], year] = sum(
                    self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == t) &
                                (self.df[SET_LIMIT + "{}".format(year)] == 1)]
                    [s + "{}".format(year)])
                i += 1

        self.df.loc[(self.df[SET_ELEC_FINAL_CODE + '{}'.format(year)] == 1) &
                    (self.df[SET_ELEC_FINAL_CODE + '{}'.format(base_year)] != 1),
                    SET_ELEC_FINAL_CODE + '{}'.format(year)] = 2

    def calculate_emission(self, grid_factor, year, time_step, start_year):
        self.df['AnnualEmissions' + "{}".format(year)] = 0.

        self.df.loc[self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] < 3, 'AnnualEmissions' + "{}".format(year)] = \
            self.df[SET_ENERGY_PER_CELL + "{}".format(year)] * grid_factor / 1000
        # self.df.loc[self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 5, 'AnnualEmissions' + "{}".format(year)] = \
        # self.df[SET_ENERGY_PER_CELL + "{}".format(year)] * self.df['PVHybridEmissionFactor' + "{}".format(year)] / 1000

        self.df.loc[self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 5, 'AnnualEmissions' + "{}".format(year)] = \
            self.df['PVHybridEmissionFactor' + "{}".format(year)] / 1000
        # self.df.loc[self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 9, 'AnnualEmissions' + "{}".format(year)] = \
        # self.df[SET_ENERGY_PER_CELL + "{}".format(year)] * self.df['WindHybridEmissionFactor' + "{}".format(year)] / 1000

        if year - time_step != start_year:
            self.df['AnnualEmissionsTotal'] = self.df['AnnualEmissions' + "{}".format(year)] + self.df[
                'AnnualEmissions' + "{}".format(year - time_step)]
