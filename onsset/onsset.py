import logging
from math import exp, log, pi
from typing import Dict
import scipy.spatial

import numpy as np
import pandas as pd

logging.basicConfig(format='%(asctime)s\t\t%(message)s', level=logging.DEBUG)
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
SET_MIN_GRID_DIST = 'MinGridDist'
SET_LCOE_GRID = 'Grid'  # All LCOE's in USD/kWh
SET_LCOE_SA_PV = 'SA_PV'
SET_LCOE_SA_DIESEL = 'SA_Diesel'
SET_LCOE_MG_WIND = 'MG_Wind'
SET_LCOE_MG_DIESEL = 'MG_Diesel'
SET_LCOE_MG_PV = 'MG_PV'
SET_LCOE_MG_HYDRO = 'MG_Hydro'
SET_MIN_OFFGRID = 'Minimum_Tech_Off_grid'  # The technology with lowest lcoe (excluding grid)
SET_MIN_OVERALL = 'MinimumOverall'  # Same as above, but including grid
SET_MIN_OFFGRID_LCOE = 'Minimum_LCOE_Off_grid'  # The lcoe value for minimum tech
SET_MIN_OVERALL_LCOE = 'MinimumOverallLCOE'  # The lcoe value for overall minimum
SET_MIN_OVERALL_CODE = 'MinimumOverallCode'  # And a code from 1 - 7 to represent that option
SET_MIN_CATEGORY = 'MinimumCategory'  # The category with minimum lcoe (grid, minigrid or standalone)
SET_NEW_CAPACITY = 'NewCapacity'  # Capacity in kW
SET_INVESTMENT_COST = 'InvestmentCost'  # The investment cost in USD
SET_CONFLICT = "Conflict"
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
SET_WTFtier = "ResidentialDemandTier"
SET_TIER = 'Tier'
SET_INVEST_PER_CAPITA = "InvestmentCapita"
SET_CALIB_GRID_DIST = 'GridDistCalibElec'
SET_CAPITA_DEMAND = 'PerCapitaDemand'
SET_RESIDENTIAL_TIER = 'ResidentialDemandTier'
SET_MIN_TD_DIST = 'minTDdist'
SET_SA_DIESEL_FUEL = 'SADieselFuelCost'
SET_MG_DIESEL_FUEL = 'MGDieselFuelCost'

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
                 base_to_peak_load_ratio=0,
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
        self.mini_grid = mini_grid
        self.existing_grid_cost_ratio = existing_grid_cost_ratio
        self.grid_capacity_investment = grid_capacity_investment
        self.diesel_truck_consumption = diesel_truck_consumption
        self.diesel_truck_volume = diesel_truck_volume
        self.om_of_td_lines = om_of_td_lines

    @classmethod
    def set_default_values(cls, base_year, start_year, end_year, discount_rate, hv_line_type=69, hv_line_cost=53000,
                           mv_line_type=33, mv_line_amperage_limit=8.0, mv_line_cost=7000, lv_line_type=0.240,
                           lv_line_cost=4250, lv_line_max_length=0.5, service_transf_type=50, service_transf_cost=4250,
                           max_nodes_per_serv_trans=300, mv_lv_sub_station_type=400, mv_lv_sub_station_cost=10000,
                           mv_mv_sub_station_cost=10000, hv_lv_sub_station_type=1000, hv_lv_sub_station_cost=25000,
                           hv_mv_sub_station_cost=25000, power_factor=0.9, load_moment=9643):
        """Initialises the class with parameter values common to all Technologies
        """
        cls.base_year = base_year
        cls.start_year = start_year
        cls.end_year = end_year

        # RUN_PARAM: Here are the assumptions related to cost and physical properties of grid extension elements
        cls.discount_rate = discount_rate
        cls.hv_line_type = hv_line_type  # kV
        cls.hv_line_cost = hv_line_cost  # $/km for 69kV
        cls.mv_line_type = mv_line_type  # kV
        cls.mv_line_amperage_limit = mv_line_amperage_limit  # Ampere (A)
        cls.mv_line_cost = mv_line_cost  # $/km  for 11-33 kV
        cls.lv_line_type = lv_line_type  # kV
        cls.lv_line_cost = lv_line_cost  # $/km
        cls.lv_line_max_length = lv_line_max_length  # km
        cls.service_transf_type = service_transf_type  # kVa
        cls.service_transf_cost = service_transf_cost  # $/unit
        cls.max_nodes_per_serv_trans = max_nodes_per_serv_trans  # max number of nodes served by a service transformer
        cls.mv_lv_sub_station_type = mv_lv_sub_station_type  # kVa
        cls.mv_lv_sub_station_cost = mv_lv_sub_station_cost  # $/unit
        cls.mv_mv_sub_station_cost = mv_mv_sub_station_cost  # $/unit
        cls.hv_lv_sub_station_type = hv_lv_sub_station_type  # kVa
        cls.hv_lv_sub_station_cost = hv_lv_sub_station_cost  # $/unit
        cls.hv_mv_sub_station_cost = hv_mv_sub_station_cost  # $/unit
        cls.power_factor = power_factor
        cls.load_moment = load_moment  # for 50mm aluminum conductor under 5% voltage drop (kW m)

    def get_lcoe(self, energy_per_cell, people, num_people_per_hh, start_year, end_year, new_connections,
                 total_energy_per_cell, prev_code, grid_cell_area, additional_mv_line_length=0.0,
                 capacity_factor=0.9, grid_penalty_ratio=1, fuel_cost=0, elec_loop=0, productive_nodes=0,
                 additional_transformer=0, penalty=1, get_investment_cost=False):
        """Calculates the LCOE depending on the parameters. Optionally calculates the investment cost instead.

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
        get_investment_cost : bool

        Returns
        -------
        lcoe or discounted investment cost
        """

        if type(people) == int or type(people) == float or type(people) == np.float64:
            if people == 0:
                # If there are no people, the investment cost is zero.
                if get_investment_cost:
                    return 0
                # Otherwise we set the people low (prevent div/0 error) and continue.
                else:
                    people = 0.00001
        else:
            people = np.maximum(people, 0.00001)

        if type(energy_per_cell) == int or type(energy_per_cell) == float or type(energy_per_cell) == np.float64:
            if energy_per_cell == 0:
                # If there are no people, the investment cost is zero.
                if get_investment_cost:
                    return 0
                # Otherwise we set the people low (prevent div/0 error) and continue.
                else:
                    energy_per_cell = 0.000000000001
        else:
            energy_per_cell = np.maximum(energy_per_cell, 0.000000000001)

        grid_penalty_ratio = np.maximum(1, grid_penalty_ratio)

        generation_per_year, peak_load, td_investment_cost = self.td_network_cost(people,
                                                                                  new_connections,
                                                                                  prev_code,
                                                                                  total_energy_per_cell,
                                                                                  energy_per_cell,
                                                                                  num_people_per_hh,
                                                                                  grid_cell_area,
                                                                                  additional_mv_line_length,
                                                                                  additional_transformer,
                                                                                  productive_nodes,
                                                                                  elec_loop,
                                                                                  penalty)
        generation_per_year = pd.Series(generation_per_year)
        peak_load = pd.Series(peak_load)
        td_investment_cost = pd.Series(td_investment_cost)

        td_investment_cost = td_investment_cost * grid_penalty_ratio
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

        capital_investment = installed_capacity * cap_cost * penalty
        total_om_cost = td_om_cost + (cap_cost * penalty * self.om_costs * installed_capacity)
        total_investment_cost = td_investment_cost + capital_investment

        if self.grid_price > 0:
            fuel_cost = self.grid_price

        # Perform the time-value LCOE calculation
        project_life = end_year - self.base_year + 1
        reinvest_year = 0
        step = start_year - self.base_year
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

        discounted_investments = investments / discount_factor
        dicounted_grid_capacity_investments = grid_capacity_investments / discount_factor
        investment_cost = np.sum(discounted_investments, axis=1) + np.sum(dicounted_grid_capacity_investments, axis=1)
        discounted_costs = (investments + operation_and_maintenance + fuel - salvage) / discount_factor
        discounted_generation = el_gen / discount_factor
        lcoe = np.sum(discounted_costs, axis=1) / np.sum(discounted_generation, axis=1)
        lcoe = pd.DataFrame(lcoe[:, np.newaxis])
        investment_cost = pd.DataFrame(investment_cost[:, np.newaxis])

        if get_investment_cost:
            return investment_cost
        else:
            return lcoe, investment_cost

    def transmission_network(self, peak_load, additional_mv_line_length=0, additional_transformer=0,
                             mv_distribution=False):
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
        mv_distribution : bool
            True if distribution network in settlement contains MV lines

        Notes
        -----
        Based on: https://www.mdpi.com/1996-1073/12/7/1395
        """

        mv_km = 0
        hv_km = 0
        no_of_hv_mv_subs = 0
        no_of_mv_mv_subs = 0
        no_of_hv_lv_subs = 0
        no_of_mv_lv_subs = 0

        if not self.standalone:
            # Sizing HV/MV
            hv_to_mv_lines = self.hv_line_cost / self.mv_line_cost
            max_mv_load = self.mv_line_amperage_limit * self.mv_line_type * hv_to_mv_lines

            mv_amperage = self.mv_lv_sub_station_type / self.mv_line_type
            no_of_mv_lines = np.ceil(peak_load / (mv_amperage * self.mv_line_type))
            hv_amperage = self.hv_lv_sub_station_type / self.hv_line_type
            no_of_hv_lines = np.ceil(peak_load / (hv_amperage * self.hv_line_type))

            if additional_transformer > 0:
                mv_km = 0
                hv_km = additional_mv_line_length * no_of_hv_lines
            else:
                mv_km = np.where((peak_load <= max_mv_load) & (additional_mv_line_length < 50),
                                 additional_mv_line_length * no_of_mv_lines,
                                 0)

                hv_km = np.where((peak_load <= max_mv_load) & (additional_mv_line_length < 50),
                                 0,
                                 additional_mv_line_length * no_of_hv_lines)

            no_of_hv_mv_subs = np.where(mv_distribution & (hv_km > 0),
                                        np.ceil(peak_load / self.mv_lv_sub_station_type),
                                        0)
            no_of_mv_mv_subs = np.where(mv_distribution & (mv_km > 0),
                                        np.ceil(peak_load / self.mv_lv_sub_station_type),
                                        0)
            no_of_hv_lv_subs = np.where(mv_distribution,
                                        0,
                                        np.where(hv_km > 0, np.ceil(peak_load / self.hv_lv_sub_station_type), 0))
            if self.mini_grid:
                no_of_mv_lv_subs = np.where(mv_km > 0,
                                            np.ceil(peak_load / self.mv_lv_sub_station_type),
                                            0)
            else:
                no_of_mv_lv_subs = np.where(mv_distribution,
                                            np.where(hv_km == 0, np.where(
                                                mv_km == 0, np.ceil(peak_load / self.mv_lv_sub_station_type), 0), 0),
                                            np.ceil(peak_load / self.mv_lv_sub_station_type))

            no_of_hv_mv_subs += additional_transformer  # to connect the MV line to the HV grid

        return hv_km, mv_km, no_of_hv_mv_subs, no_of_mv_mv_subs, no_of_hv_lv_subs, no_of_mv_lv_subs

    def distribution_network(self, people, energy_per_cell, num_people_per_hh, grid_cell_area,
                             productive_nodes=0):
        """This method calculates the required components for the distribution network
        This includes potentially MV lines, LV lines and service transformers

        Arguments
        ---------
        people : float
            Number of people in settlement
        energy_per_cell : float
            Annual energy demand in settlement (kWh)
        num_people_per_hh : float
            Number of people per household in settlement
        grid_cell_area : float
            Area of settlement (km2)
        productive_nodes : int
            Additional connections (schools, health facilities, shops)

        Notes
        -----
        Based on: https://www.mdpi.com/1996-1073/12/7/1395
        """

        consumption = energy_per_cell  # kWh/year
        average_load = consumption / (1 - self.distribution_losses) / HOURS_PER_YEAR  # kW
        peak_load = average_load / self.base_to_peak_load_ratio  # kW

        if self.standalone:
            cluster_mv_lines_length = 0
            lv_km = 0
            no_of_service_transf = 0
            total_nodes = 0
        else:
            s_max = peak_load / self.power_factor
            max_transformer_area = pi * self.lv_line_max_length ** 2
            total_nodes = (people / num_people_per_hh) + productive_nodes

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
                        num_people_per_hh, grid_cell_area, additional_mv_line_length=0, additional_transformer=0,
                        productive_nodes=0, elec_loop=0, penalty=1):
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
            self.distribution_network(people, total_energy_per_cell, num_people_per_hh, grid_cell_area,
                                      productive_nodes)

        # Next calculate the network that is already there
        cluster_mv_lines_length_existing, cluster_lv_lines_length_existing, no_of_service_transf_existing, \
            generation_per_year_existing, peak_load_existing, total_nodes_existing = \
            self.distribution_network(np.maximum((people - new_connections), 1),
                                      (total_energy_per_cell - energy_per_cell),
                                      num_people_per_hh, grid_cell_area, productive_nodes)

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
        mv_distribution = np.where(mv_lines_distribution_length_additional > 0, True, False)

        # Then calculate the transmission network (HV or MV lines plus transformers) using the same methodology
        hv_lines_total_length_total, mv_lines_connection_length_total, no_of_hv_mv_substation_total, \
            no_of_mv_mv_substation_total, no_of_hv_lv_substation_total, no_of_mv_lv_substation_total = \
            self.transmission_network(peak_load_total, additional_mv_line_length, additional_transformer,
                                      mv_distribution=mv_distribution)

        hv_lines_total_length_existing, mv_lines_connection_length_existing, no_of_hv_mv_substation_existing, \
            no_of_mv_mv_substation_existing, no_of_hv_lv_substation_existing, no_of_mv_lv_substation_existing = \
            self.transmission_network(peak_load_existing, additional_mv_line_length, additional_transformer,
                                      mv_distribution=mv_distribution)

        hv_lines_total_length_additional = np.maximum(hv_lines_total_length_total - hv_lines_total_length_existing, 0)
        mv_lines_connection_length_additional = \
            np.maximum(mv_lines_connection_length_total - mv_lines_connection_length_existing, 0)
        no_of_hv_lv_substation_additional = \
            np.maximum(no_of_hv_lv_substation_total - no_of_hv_lv_substation_existing, 0)
        no_of_hv_mv_substation_additional = \
            np.maximum(no_of_hv_mv_substation_total - no_of_hv_mv_substation_existing, 0)
        no_of_mv_mv_substation_additional = \
            np.maximum(no_of_mv_mv_substation_total - no_of_mv_mv_substation_existing, 0)
        no_of_mv_lv_substation_additional = \
            np.maximum(no_of_mv_lv_substation_total - no_of_mv_lv_substation_existing, 0)

        # If no distribution network is present, perform the calculations only once
        mv_lines_distribution_length_new, total_lv_lines_length_new, num_transformers_new, generation_per_year_new, \
            peak_load_new, total_nodes_new = self.distribution_network(people, energy_per_cell, num_people_per_hh,
                                                                       grid_cell_area, productive_nodes)

        mv_distribution = np.where(mv_lines_distribution_length_new > 0, True, False)

        hv_lines_total_length_new, mv_lines_connection_length_new, no_of_hv_mv_substation_new, \
            no_of_mv_mv_substation_new, no_of_hv_lv_substation_new, no_of_mv_lv_substation_new = \
            self.transmission_network(peak_load_new, additional_mv_line_length, additional_transformer,
                                      mv_distribution=mv_distribution)

        mv_lines_distribution_length = np.where((people != new_connections) & ((prev_code < 2) | (prev_code > 3)),
                                                mv_lines_distribution_length_additional,
                                                mv_lines_distribution_length_new)
        hv_lines_total_length = np.where((people != new_connections) & ((prev_code < 2) | (prev_code > 3)),
                                         hv_lines_total_length_additional,
                                         hv_lines_total_length_new)
        mv_lines_connection_length = np.where((people != new_connections) & ((prev_code < 2) | (prev_code > 3)),
                                              mv_lines_connection_length_additional,
                                              mv_lines_connection_length_new)
        total_lv_lines_length = np.where((people != new_connections) & ((prev_code < 2) | (prev_code > 3)),
                                         total_lv_lines_length_additional,
                                         total_lv_lines_length_new)
        num_transformers = np.where((people != new_connections) & ((prev_code < 2) | (prev_code > 3)),
                                    num_transformers_additional,
                                    num_transformers_new)
        total_nodes = np.where((people != new_connections) & ((prev_code < 2) | (prev_code > 3)),
                               total_nodes_additional,
                               total_nodes_new)
        no_of_hv_lv_substation = np.where((people != new_connections) & ((prev_code < 2) | (prev_code > 3)),
                                          no_of_hv_lv_substation_additional,
                                          no_of_hv_lv_substation_new)
        no_of_hv_mv_substation = np.where((people != new_connections) & ((prev_code < 2) | (prev_code > 3)),
                                          no_of_hv_mv_substation_additional,
                                          no_of_hv_mv_substation_new)
        no_of_mv_mv_substation = np.where((people != new_connections) & ((prev_code < 2) | (prev_code > 3)),
                                          no_of_mv_mv_substation_additional,
                                          no_of_mv_mv_substation_new)
        no_of_mv_lv_substation = np.where((people != new_connections) & ((prev_code < 2) | (prev_code > 3)),
                                          no_of_mv_lv_substation_additional,
                                          no_of_mv_lv_substation_new)
        generation_per_year = np.where((people != new_connections) & ((prev_code < 2) | (prev_code > 3)),
                                       generation_per_year_additional,
                                       generation_per_year_new)
        peak_load = np.where((people != new_connections) & ((prev_code < 2) | (prev_code > 3)),
                             peak_load_additional,
                             peak_load_new)

        td_investment_cost = (hv_lines_total_length * self.hv_line_cost * (
                1 + self.existing_grid_cost_ratio * elec_loop) +
                              mv_lines_connection_length * self.mv_line_cost * (
                                      1 + self.existing_grid_cost_ratio * elec_loop) +
                              total_lv_lines_length * self.lv_line_cost +
                              mv_lines_distribution_length * self.mv_line_cost +
                              num_transformers * self.service_transf_cost +
                              total_nodes * self.connection_cost_per_hh +
                              no_of_hv_lv_substation * self.hv_lv_sub_station_cost +
                              no_of_hv_mv_substation * self.hv_mv_sub_station_cost +
                              no_of_mv_mv_substation * self.mv_mv_sub_station_cost +
                              no_of_mv_lv_substation * self.mv_lv_sub_station_cost) * penalty

        return generation_per_year, peak_load, td_investment_cost


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

    def condition_df(self):
        """
        Do any initial data conditioning that may be required.
        """

        logging.info('Ensure that columns that are supposed to be numeric are numeric')
        self.df[SET_NIGHT_LIGHTS] = pd.to_numeric(self.df[SET_NIGHT_LIGHTS], errors='coerce')
        self.df[SET_POP] = pd.to_numeric(self.df[SET_POP], errors='coerce')
        self.df[SET_GRID_CELL_AREA] = pd.to_numeric(self.df[SET_GRID_CELL_AREA], errors='coerce')
        self.df[SET_ELEC_POP] = pd.to_numeric(self.df[SET_ELEC_POP], errors='coerce')
        self.df[SET_GHI] = pd.to_numeric(self.df[SET_GHI], errors='coerce')
        self.df[SET_WINDVEL] = pd.to_numeric(self.df[SET_WINDVEL], errors='coerce')
        self.df[SET_TRAVEL_HOURS] = pd.to_numeric(self.df[SET_TRAVEL_HOURS], errors='coerce')
        self.df[SET_ELEVATION] = pd.to_numeric(self.df[SET_ELEVATION], errors='coerce')
        self.df[SET_SLOPE] = pd.to_numeric(self.df[SET_SLOPE], errors='coerce')
        self.df[SET_LAND_COVER] = pd.to_numeric(self.df[SET_LAND_COVER], errors='coerce')
        self.df[SET_SUBSTATION_DIST] = pd.to_numeric(self.df[SET_SUBSTATION_DIST], errors='coerce')
        self.df[SET_HV_DIST_CURRENT] = pd.to_numeric(self.df[SET_HV_DIST_CURRENT], errors='coerce')
        self.df[SET_HV_DIST_PLANNED] = pd.to_numeric(self.df[SET_HV_DIST_PLANNED], errors='coerce')
        self.df[SET_MV_DIST_CURRENT] = pd.to_numeric(self.df[SET_MV_DIST_CURRENT], errors='coerce')
        self.df[SET_MV_DIST_PLANNED] = pd.to_numeric(self.df[SET_MV_DIST_PLANNED], errors='coerce')
        self.df[SET_ROAD_DIST] = pd.to_numeric(self.df[SET_ROAD_DIST], errors='coerce')
        self.df[SET_X_DEG] = pd.to_numeric(self.df[SET_X_DEG], errors='coerce')
        self.df[SET_Y_DEG] = pd.to_numeric(self.df[SET_Y_DEG], errors='coerce')
        self.df[SET_DIST_TO_TRANS] = pd.to_numeric(self.df[SET_DIST_TO_TRANS], errors='coerce')
        self.df[SET_HYDRO_DIST] = pd.to_numeric(self.df[SET_HYDRO_DIST], errors='coerce')
        self.df[SET_HYDRO] = pd.to_numeric(self.df[SET_HYDRO], errors='coerce')
        self.df[SET_HYDRO_FID] = pd.to_numeric(self.df[SET_HYDRO_FID], errors='coerce')
        self.df[SET_URBAN] = pd.to_numeric(self.df[SET_URBAN], errors='coerce')
        self.df[SET_CAPITA_DEMAND] = pd.to_numeric(self.df[SET_CAPITA_DEMAND], errors='coerce')
        self.df[SET_AGRI_DEMAND] = pd.to_numeric(self.df[SET_AGRI_DEMAND], errors='coerce')
        self.df[SET_HEALTH_DEMAND] = pd.to_numeric(self.df[SET_HEALTH_DEMAND], errors='coerce')
        self.df[SET_EDU_DEMAND] = pd.to_numeric(self.df[SET_EDU_DEMAND], errors='coerce')
        self.df[SET_COMMERCIAL_DEMAND] = pd.to_numeric(self.df[SET_COMMERCIAL_DEMAND], errors='coerce')
        self.df[SET_ELEC_ORDER] = pd.to_numeric(self.df[SET_ELEC_ORDER], errors='coerce')
        self.df[SET_CONFLICT] = pd.to_numeric(self.df[SET_CONFLICT], errors='coerce')

        self.df.loc[self.df[SET_ELEC_POP] > self.df[SET_POP], SET_ELEC_POP] = self.df[SET_POP]

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
    def get_wind_cf(wind_velocity):
        """Calculate the wind capacity factor based on the average wind velocity.

        Parameters
        ----------
        wind_velocity : float
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

        if wind_velocity == 0:
            return 0
        elif wind_velocity < 0:
            raise ValueError('Wind velocity must be greater than 0')

        else:
            # Adjust for the correct hub height
            alpha = (0.37 - 0.088 * log(wind_velocity)) / (1 - 0.088 * log(zr / 10))
            u_z = wind_velocity * (z / zr) ** alpha

            # Rayleigh distribution and sum of series
            rayleigh = [(pi / 2) * (u / u_z ** 2) * exp((-pi / 4) * (u / u_z) ** 2) for u in u_arr]
            energy_produced = sum([mu * es * t * p * r for p, r in zip(p_curve, rayleigh)])

            return energy_produced / (p_rated * t)

    def calc_wind_cfs(self):
        logging.info('Calculate Wind CF')
        return self.df[SET_WINDVEL].apply(self.get_wind_cf)

    def prepare_wtf_tier_columns(self, num_people_per_hh_rural, num_people_per_hh_urban,
                                 tier_1, tier_2, tier_3, tier_4, tier_5):
        """ Prepares the five Residential Demand Tier Targets based customized for each country
        """
        # The MTF approach is given as per yearly household consumption
        # (BEYOND CONNECTIONS Energy Access Redefined, ESMAP, 2015).
        # Tiers in kWh/capita/year depends on the average ppl/hh which is different in every country

        logging.info('Populate ResidentialDemandTier columns')
        tier_num = [1, 2, 3, 4, 5]
        ppl_hh_average = (num_people_per_hh_urban + num_people_per_hh_rural) / 2
        tier_1 = tier_1 / ppl_hh_average  # 38.7 refers to kWh/household/year (mean value between Tier 1 and Tier 2)
        tier_2 = tier_2 / ppl_hh_average
        tier_3 = tier_3 / ppl_hh_average
        tier_4 = tier_4 / ppl_hh_average
        tier_5 = tier_5 / ppl_hh_average

        wb_tiers_all = {1: tier_1, 2: tier_2, 3: tier_3, 4: tier_4, 5: tier_5}

        for num in tier_num:
            self.df[SET_WTFtier + "{}".format(num)] = wb_tiers_all[num]

    def calibrate_current_pop_and_urban(self, pop_actual, urban_current):
        """
        The function calibrates population values and urban/rural split (as estimated from GIS layers) based
        on actual values provided by the user for the start year.
        """

        logging.info('Population calibration process')

        # First, calculate ratio between GIS retrieved and user provided population
        pop_ratio = pop_actual / self.df[SET_POP].sum()

        # Use above ratio to calibrate the population in a new column
        self.df[SET_POP_CALIB] = self.df.apply(lambda row: row[SET_POP] * pop_ratio, axis=1)
        pop_modelled = self.df[SET_POP_CALIB].sum()
        pop_diff = abs(pop_modelled - pop_actual)
        print('The calibrated population differs by {:.2f}. '
              'In case this is not acceptable please revise this part of the code'.format(pop_diff))

        # TODO Why do we apply the ratio to elec_pop? Shouldn't the calibration take place before defining elec_pop?
        self.df[SET_ELEC_POP_CALIB] = self.df[SET_ELEC_POP] * pop_ratio

        logging.info('Urban/rural calibration process')
        # TODO As indicated below, HRSL classifies in 0, 1 and 2; I don't get why if statement uses 3 here.
        if max(self.df[SET_URBAN]) == 3:  # THIS OPTION IS CURRENTLY DISABLED
            calibrate = True if 'n' in input(
                'Use urban definition from GIS layer <y/n> (n=model calibration):') else False
        else:
            calibrate = True
        # RUN_PARAM: This is where manual calibration of urban/rural population takes place.
        # The model uses 0, 1, 2 as GHS population layer does.
        # As of this version, urban are only self.dfs with value equal to 2
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

        return pop_modelled, urban_modelled

    def project_pop_and_urban(self, pop_modelled, pop_future_high, pop_future_low, urban_modelled,
                              urban_future, start_year, end_year, intermediate_year):
        """
        This function projects population and urban/rural ratio for the different years of the analysis
        """
        project_life = end_year - start_year

        # Project future population, with separate growth rates for urban and rural
        logging.info('Population projection process')

        # TODO this is a residual of the previous process;
        # shall we delete? Is there any scenario where we don't apply projections?
        calibrate = True

        if calibrate:
            urban_growth_high = (urban_future * pop_future_high) / (urban_modelled * pop_modelled)
            rural_growth_high = ((1 - urban_future) * pop_future_high) / ((1 - urban_modelled) * pop_modelled)

            yearly_urban_growth_rate_high = urban_growth_high ** (1 / project_life)
            yearly_rural_growth_rate_high = rural_growth_high ** (1 / project_life)

            urban_growth_low = (urban_future * pop_future_low) / (urban_modelled * pop_modelled)
            rural_growth_low = ((1 - urban_future) * pop_future_low) / ((1 - urban_modelled) * pop_modelled)

            yearly_urban_growth_rate_low = urban_growth_low ** (1 / project_life)
            yearly_rural_growth_rate_low = rural_growth_low ** (1 / project_life)
        else:
            urban_growth_high = pop_future_high / pop_modelled
            rural_growth_high = pop_future_high / pop_modelled

            yearly_urban_growth_rate_high = urban_growth_high ** (1 / project_life)
            yearly_rural_growth_rate_high = rural_growth_high ** (1 / project_life)

            urban_growth_low = pop_future_low / pop_modelled
            rural_growth_low = pop_future_low / pop_modelled

            yearly_urban_growth_rate_low = urban_growth_low ** (1 / project_life)
            yearly_rural_growth_rate_low = rural_growth_low ** (1 / project_life)

        # RUN_PARAM: Define here the years for which results should be provided in the output file.
        years_of_analysis = [intermediate_year, end_year]

        for year in years_of_analysis:
            self.df[SET_POP + "{}".format(year) + 'High'] = \
                self.df.apply(lambda row: row[SET_POP_CALIB] * (yearly_urban_growth_rate_high ** (year - start_year))
                              if row[SET_URBAN] > 1
                              else row[SET_POP_CALIB] * (yearly_rural_growth_rate_high ** (year - start_year)), axis=1)

            self.df[SET_POP + "{}".format(year) + 'Low'] = \
                self.df.apply(lambda row: row[SET_POP_CALIB] * (yearly_urban_growth_rate_low ** (year - start_year))
                              if row[SET_URBAN] > 1
                              else row[SET_POP_CALIB] * (yearly_rural_growth_rate_low ** (year - start_year)), axis=1)

        self.df[SET_POP + "{}".format(start_year)] = self.df.apply(lambda row: row[SET_POP_CALIB], axis=1)

    def elec_current_and_future(self, elec_actual, elec_actual_urban, elec_actual_rural, start_year,
                                min_night_lights=0, min_pop=50, max_transformer_dist=2, max_mv_dist=2, max_hv_dist=5):
        """
        Calibrate the current electrification status, and future 'pre-electrification' status
        """

        # REVIEW: The way this works now, for all urban or rural settlements that fit the conditioning.
        # The population SET_ELEC_POP is reduced by equal amount to match urban/rural national statistics respectively.
        # TODO We might need to update with off-grid electrified in future versions
        urban_pop = (self.df.loc[self.df[SET_URBAN] > 1, SET_POP_CALIB].sum())  # Calibrate current electrification
        rural_pop = (self.df.loc[self.df[SET_URBAN] <= 1, SET_POP_CALIB].sum())  # Calibrate current electrification
        total_pop = self.df[SET_POP_CALIB].sum()
        total_elec_ratio = elec_actual
        urban_elec_ratio = elec_actual_urban
        rural_elec_ratio = elec_actual_rural
        elec_modelled = 0
        factor = (total_pop * total_elec_ratio) / (urban_pop * urban_elec_ratio + rural_pop * rural_elec_ratio)
        urban_elec_ratio *= factor
        rural_elec_ratio *= factor
        self.df.loc[self.df[SET_NIGHT_LIGHTS] <= 0, [SET_ELEC_POP_CALIB]] = 0

        logging.info('Calibrate current electrification')
        self.df[SET_ELEC_CURRENT] = 0

        # This if function here skims through T&D columns to identify if any non 0 values exist;
        # Then it defines calibration method accordingly.
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
            dist_limit = max_hv_dist

        condition = 0

        while condition == 0:
            # Assign the 1 (electrified)/0 (un-electrified) values to each cell
            urban_electrified = urban_pop * urban_elec_ratio
            rural_electrified = rural_pop * rural_elec_ratio
            # RUN_PARAM: Calibration parameters if MV lines or transformer location is available
            if priority == 1:
                print(
                    'We have identified the existence of transformers or MV lines as input data; '
                    'therefore we proceed using those for the calibration')
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
                    pop_elec_2 = self.df.loc[(self.df[SET_ELEC_CURRENT] == 0) & (self.df[SET_POP_CALIB] > min_pop) &
                                             (self.df[SET_CALIB_GRID_DIST] < td_dist_2), SET_POP_CALIB].sum()
                    if i < 50:
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
                    'No transformers or MV lines were identified as input data; '
                    'therefore we proceed to the calibration with HV line info')
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
                while elec_actual - elec_modelled > 0.01:
                    pop_elec_2 = self.df.loc[(self.df[SET_ELEC_CURRENT] == 0) & (self.df[SET_POP_CALIB] > min_pop) &
                                             (self.df[SET_CALIB_GRID_DIST] < td_dist_2), SET_POP_CALIB].sum()
                    if i < 50:
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

            print('The modelled electrification rate differ by {0:.2f}. '
                  'Urban elec. rate differ by {1:.2f} and Rural elec. rate differ by {2:.2f}. \n'
                  'If this is not acceptable please revise this '
                  'part of the algorithm'.format(elec_modelled - elec_actual,
                                                 urban_elec_ratio - elec_actual_urban,
                                                 rural_elec_ratio - elec_actual_rural))
            condition = 1

        self.df[SET_ELEC_FINAL_CODE + "{}".format(start_year)] = \
            self.df.apply(lambda row: 1 if row[SET_ELEC_CURRENT] == 1 else 99, axis=1)

        return elec_modelled, rural_elec_ratio, urban_elec_ratio

    def pre_electrification(self, grid_price, year, time_step, end_year, grid_calc, grid_capacity_limit,
                            grid_connect_limit):

        """" ... """

        logging.info('Define the initial electrification status')
        grid_investment = np.zeros(len(self.df[SET_X_DEG]))
        prev_code = self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)].copy(deep=True)

        # Grid-electrified settlements
        electrified_loce, electrified_investment = self.get_grid_lcoe(0, 0, 0, year, time_step, end_year, grid_calc)
        electrified_investment = electrified_investment[0]
        grid_investment = np.where(self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 1,
                                   electrified_investment, grid_investment)

        self.df[SET_LCOE_GRID + "{}".format(year)] = 99
        self.df.loc[self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 1,
                    SET_LCOE_GRID + "{}".format(year)] = grid_price

        # Two restrictions may be imposed on the grid. The new grid generation capacity that can be added and the
        # number of new households that can be connected. The next step calculates how much of that will be used up due
        # to demand (population) growth in already electrified settlements
        consumption = sum(self.df.loc[prev_code == 1][SET_ENERGY_PER_CELL + "{}".format(year)])
        average_load = consumption / (1 - grid_calc.distribution_losses) / HOURS_PER_YEAR  # kW
        peak_load = average_load / grid_calc.base_to_peak_load_ratio  # kW
        grid_capacity_limit -= peak_load

        self.df['Densification_connections'] = self.df[SET_NEW_CONNECTIONS + "{}".format(year)] / self.df[
            SET_NUM_PEOPLE_PER_HH]
        grid_connect_limit -= sum(self.df.loc[prev_code == 1]['Densification_connections'])
        del self.df['Densification_connections']

        return pd.Series(grid_investment), grid_capacity_limit, grid_connect_limit

    def current_mv_line_dist(self):
        logging.info('Determine current MV line length')
        self.df[SET_MV_CONNECT_DIST] = 0
        self.df.loc[self.df[SET_ELEC_CURRENT] == 1, SET_MV_CONNECT_DIST] = self.df[SET_HV_DIST_CURRENT]
        self.df[SET_MIN_TD_DIST] = self.df[[SET_MV_DIST_PLANNED, SET_HV_DIST_PLANNED]].min(axis=1)

    def elec_extension(self, grid_calc, max_dist, year, start_year, end_year, time_step, grid_capacity_limit,
                       grid_connect_limit, new_investment, auto_intensification=0, prioritization=0):
        """
        Iterate through all electrified settlements and find which settlements can be economically connected to the grid
        Repeat with newly electrified settlements until no more are added
        """

        prio = int(prioritization)

        prev_code = self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)].copy(deep=True)
        if year - time_step == start_year:
            elecorder = self.df[SET_ELEC_ORDER].copy(deep=True)
        else:
            elecorder = self.df[SET_ELEC_ORDER + "{}".format(year - time_step)].copy(deep=True)
        grid_penalty_ratio = self.df[SET_GRID_PENALTY].copy(deep=True)
        min_code_lcoes = self.df[SET_MIN_OFFGRID_LCOE + "{}".format(year)].copy(deep=True)
        new_lcoes = self.df[SET_LCOE_GRID + "{}".format(year)].copy(deep=True)
        cell_path_real = self.df[SET_MV_CONNECT_DIST].copy(deep=True)
        cell_path_adjusted = list(np.zeros(len(prev_code)).tolist())
        mv_planned = self.df[SET_MV_DIST_PLANNED].copy(deep=True)

        # Start by identifying which settlements are grid-connected already
        electrified = np.where(prev_code == 1, 1, 0)

        # The grid may be forced to expand around existing MV lines if this option has been selected, regardless
        # off-grid alternatives are less costly. The following section implements that
        if (prio == 2) or (prio == 4):
            mv_dist_adjusted = np.nan_to_num(grid_penalty_ratio * mv_planned)

            intensification_lcoe, intensification_investment = \
                self.get_grid_lcoe(dist_adjusted=mv_dist_adjusted, elecorder=0, additional_transformer=0, year=year,
                                   time_step=time_step, end_year=end_year, grid_calc=grid_calc)
            intensification_lcoe = new_lcoes.copy(deep=True)
            intensification_lcoe.loc[(mv_planned < auto_intensification) & (prev_code != 1)] = 0.01
            intensification_lcoe = pd.DataFrame(intensification_lcoe)
            intensification_lcoe.columns = [0]

            grid_capacity_limit, grid_connect_limit, cell_path_real, cell_path_adjusted, elecorder, electrified, \
                new_lcoes, new_investment \
                = self.update_grid_extension_info(grid_lcoe=intensification_lcoe, dist=mv_planned,
                                                  dist_adjusted=mv_dist_adjusted, prev_dist=0, elecorder=elecorder,
                                                  new_elec_order=1, max_dist=max_dist, new_lcoes=new_lcoes,
                                                  grid_capacity_limit=grid_capacity_limit,
                                                  grid_connect_limit=grid_connect_limit, cell_path_real=cell_path_real,
                                                  cell_path_adjusted=cell_path_adjusted, electrified=electrified,
                                                  year=year, grid_calc=grid_calc,
                                                  grid_investment=intensification_investment,
                                                  new_investment=new_investment)

        # Find the unelectrified settlements where grid can be less costly than off-grid
        filter_lcoe, filter_investment = self.get_grid_lcoe(0, 0, 0, year, time_step, end_year, grid_calc)
        filter_lcoe = filter_lcoe[0]
        filter_lcoe.loc[electrified == 1] = 99
        unelectrified = np.where(filter_lcoe < min_code_lcoes)
        unelectrified = unelectrified[0].tolist()

        logging.info('Initially {} electrified'.format(sum(electrified)))

        # First round of extension from MV network
        mv_dist = pd.Series(self.df[SET_MV_DIST_PLANNED])
        mv_dist_adjusted = np.nan_to_num(grid_penalty_ratio * mv_dist)

        grid_lcoe, grid_investment = self.get_grid_lcoe(dist_adjusted=mv_dist_adjusted, elecorder=0,
                                                        additional_transformer=0, year=year, time_step=time_step,
                                                        end_year=end_year, grid_calc=grid_calc)

        grid_capacity_limit, grid_connect_limit, cell_path_real, cell_path_adjusted, elecorder, electrified, \
            new_lcoes, new_investment \
            = self.update_grid_extension_info(grid_lcoe=grid_lcoe, dist=mv_dist, dist_adjusted=mv_dist_adjusted,
                                              prev_dist=0, elecorder=elecorder, new_elec_order=1, max_dist=max_dist,
                                              new_lcoes=new_lcoes, grid_capacity_limit=grid_capacity_limit,
                                              grid_connect_limit=grid_connect_limit, cell_path_real=cell_path_real,
                                              cell_path_adjusted=cell_path_adjusted, electrified=electrified, year=year,
                                              grid_calc=grid_calc, grid_investment=grid_investment,
                                              new_investment=new_investment)

        #  Second round of extension from HV lines
        hv_dist = np.nan_to_num(self.df[SET_HV_DIST_PLANNED])
        hv_dist_adjusted = np.nan_to_num(hv_dist * grid_penalty_ratio)

        grid_lcoe, grid_investment = self.get_grid_lcoe(dist_adjusted=hv_dist_adjusted, elecorder=0,
                                                        additional_transformer=1, year=year, time_step=time_step,
                                                        end_year=end_year, grid_calc=grid_calc)

        grid_capacity_limit, grid_connect_limit, cell_path_real, cell_path_adjusted, elecorder, electrified, \
            new_lcoes, new_investment \
            = self.update_grid_extension_info(grid_lcoe=grid_lcoe, dist=hv_dist, dist_adjusted=hv_dist_adjusted,
                                              prev_dist=0, elecorder=elecorder, new_elec_order=1, max_dist=999999,
                                              new_lcoes=new_lcoes, grid_capacity_limit=grid_capacity_limit,
                                              grid_connect_limit=grid_connect_limit, cell_path_real=cell_path_real,
                                              cell_path_adjusted=cell_path_adjusted, electrified=electrified,
                                              year=year, grid_calc=grid_calc, grid_investment=grid_investment,
                                              new_investment=new_investment)

        # Third to last round of extension loops from electrified settlements. First considering all
        # electrified settlements up until this point, then from the newly electrified settlements in each round
        prev_electrified = np.zeros(len(prev_code))
        loops = 1
        while sum(electrified) > sum(prev_electrified):
            new_electrified = electrified - prev_electrified
            prev_electrified = electrified
            logging.info('Electrification loop {} with {} electrified'.format(loops, int(sum(new_electrified))))
            loops += 1

            if sum(new_electrified) > 1:
                # Calculating the distance and adjusted distance from each unelectrified settelement to the closest
                # electrified settlement, as well as the electrification order an total MV distance to that electrified
                # settlement
                nearest_dist_adjusted, nearest_elec_order, prev_dist, nearest_dist = \
                    self.closest_electrified_settlement(new_electrified, unelectrified, cell_path_real,
                                                        grid_penalty_ratio, elecorder)

                grid_lcoe, grid_investment = self.get_grid_lcoe(dist_adjusted=nearest_dist_adjusted,
                                                                elecorder=nearest_elec_order,
                                                                additional_transformer=0, year=year,
                                                                time_step=time_step,
                                                                end_year=end_year, grid_calc=grid_calc)

                grid_capacity_limit, grid_connect_limit, cell_path_real, cell_path_adjusted, elecorder, electrified, \
                    new_lcoes, new_investment = \
                    self.update_grid_extension_info(grid_lcoe=grid_lcoe, dist=nearest_dist,
                                                    dist_adjusted=nearest_dist_adjusted,
                                                    prev_dist=prev_dist, elecorder=elecorder,
                                                    new_elec_order=nearest_elec_order, max_dist=max_dist,
                                                    new_lcoes=new_lcoes, grid_capacity_limit=grid_capacity_limit,
                                                    grid_connect_limit=grid_connect_limit,
                                                    cell_path_real=cell_path_real,
                                                    cell_path_adjusted=cell_path_adjusted, electrified=electrified,
                                                    year=year, grid_calc=grid_calc, grid_investment=grid_investment,
                                                    new_investment=new_investment)

        return new_lcoes, cell_path_adjusted, elecorder, cell_path_real, pd.DataFrame(new_investment)

    def get_grid_lcoe(self, dist_adjusted, elecorder, additional_transformer, year, time_step, end_year, grid_calc):
        grid_lcoe, grid_investment = \
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
                               additional_transformer=additional_transformer)
        return grid_lcoe, grid_investment

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
                                   cell_path_adjusted, electrified, year, grid_calc, grid_investment, new_investment):

        min_code_lcoes = self.df[SET_MIN_OFFGRID_LCOE + "{}".format(year)].copy(deep=True)

        grid_lcoe = grid_lcoe[0]
        grid_investment = grid_investment[0]
        grid_lcoe.loc[electrified == 1] = 99
        grid_lcoe.loc[prev_dist + dist_adjusted > max_dist] = 99
        grid_lcoe.loc[grid_lcoe > new_lcoes] = 99
        consumption = self.df[SET_ENERGY_PER_CELL + "{}".format(year)]  # kWh/year
        average_load = consumption / (1 - grid_calc.distribution_losses) / HOURS_PER_YEAR  # kW
        peak_load = average_load / grid_calc.base_to_peak_load_ratio  # kW
        peak_load.loc[grid_lcoe >= min_code_lcoes] = 0
        peak_load_cum_sum = np.cumsum(peak_load)
        grid_lcoe.loc[peak_load_cum_sum > grid_capacity_limit] = 99
        new_grid_connections = self.df[SET_NEW_CONNECTIONS + "{}".format(year)] / self.df[SET_NUM_PEOPLE_PER_HH]
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

        return grid_capacity_limit, grid_connect_limit, cell_path_real, cell_path_adjusted, elecorder, \
            electrified, new_lcoes, new_investment

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

    def calculate_new_connections(self, year, time_step, start_year):
        """this method defines new connections for grid related purposes

        Arguments
        ---------
        year : int
        time_step : int
        start_year : int

        """

        logging.info('Calculate new connections')
        # Calculate new connections for grid related purposes
        # TODO - This was changed based on your "newly created" column SET_ELEC_POP.
        # Please review and check whether this creates any problem at your distribution_network function
        # using people/new connections and energy_per_settlement/total_energy_per_settlement

        if year - time_step == start_year:
            # Assign new connections to those that are already electrified to a certain percent
            self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] < 99),
                        SET_NEW_CONNECTIONS + "{}".format(year)] = \
                (self.df[SET_POP + "{}".format(year)] - self.df[SET_ELEC_POP_CALIB])
            # Assign new connections to those that are not currently electrified
            self.df.loc[self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 99,
                        SET_NEW_CONNECTIONS + "{}".format(year)] = self.df[SET_POP + "{}".format(year)]
            # Some conditioning to eliminate negative values if existing by mistake
            self.df.loc[self.df[SET_NEW_CONNECTIONS + "{}".format(year)] < 0,
                        SET_NEW_CONNECTIONS + "{}".format(year)] = 0
        else:
            # Assign new connections to settlements that are already electrified
            self.df.loc[self.df[SET_LIMIT + "{}".format(year - time_step)] == 1,
                        SET_NEW_CONNECTIONS + "{}".format(year)] = \
                (self.df[SET_POP + "{}".format(year)] - self.df[SET_POP + "{}".format(year - time_step)])

            # Assign new connections to settlements that were initially electrified,
            # but not prioritized during the time_step
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

    # RESIDENTIAL DEMAND STARTS
    def set_residential_demand(self, rural_tier, urban_tier, num_people_per_hh_rural,
                               num_people_per_hh_urban, productive_demand):
        """this method defines residential demand per tier level for each target year

        Arguments
        ---------
        rural_tier : int
        urban_tier : int
        num_people_per_hh_rural : float
        num_people_per_hh_urban : float
        productive_demand : int

        """

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

            # TODO: REVIEW, added Tier column
            tier_1 = 38.7  # 38.7 refers to kWh/household/year. It is the mean value between Tier 1 and Tier 2
            tier_2 = 219
            tier_3 = 803
            tier_4 = 2117

            self.df[SET_TIER] = 5
            self.df.loc[self.df[SET_CAPITA_DEMAND] * self.df[SET_NUM_PEOPLE_PER_HH] < tier_4, SET_TIER] = 4
            self.df.loc[self.df[SET_CAPITA_DEMAND] * self.df[SET_NUM_PEOPLE_PER_HH] < tier_3, SET_TIER] = 3
            self.df.loc[self.df[SET_CAPITA_DEMAND] * self.df[SET_NUM_PEOPLE_PER_HH] < tier_2, SET_TIER] = 2
            self.df.loc[self.df[SET_CAPITA_DEMAND] * self.df[SET_NUM_PEOPLE_PER_HH] < tier_1, SET_TIER] = 1

            # Add commercial demand
            # agri = True if 'y' in input('Include agricultural demand? <y/n> ') else False
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

    def calculate_total_demand_per_settlement(self, year):
        """this method calculates total demand for each settlement per year

        Arguments
        ---------
        year : int

        """

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

    def set_scenario_variables(self, year, num_people_per_hh_rural, num_people_per_hh_urban, time_step, start_year,
                               urban_tier, rural_tier, end_year_pop, productive_demand):
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

        if end_year_pop == 0:
            self.df[SET_POP + "{}".format(year)] = self.df[SET_POP + "{}".format(year) + 'Low']
        else:
            self.df[SET_POP + "{}".format(year)] = self.df[SET_POP + "{}".format(year) + 'High']

        self.calculate_new_connections(year, time_step, start_year)
        self.set_residential_demand(rural_tier, urban_tier, num_people_per_hh_rural, num_people_per_hh_urban,
                                    productive_demand)
        self.calculate_total_demand_per_settlement(year)

    def calculate_off_grid_lcoes(self, mg_hydro_calc, mg_wind_calc, mg_pv_calc, sa_pv_calc, mg_diesel_calc,
                                 sa_diesel_calc, year, end_year, time_step, diesel_techs=0):
        """
        Calculate the LCOEs for all off-grid technologies

        """

        logging.info('Calculate minigrid hydro LCOE')
        self.df[SET_LCOE_MG_HYDRO + "{}".format(year)], mg_hydro_investment = \
            mg_hydro_calc.get_lcoe(energy_per_cell=self.df[SET_ENERGY_PER_CELL + "{}".format(year)],
                                   start_year=year - time_step,
                                   end_year=end_year,
                                   people=self.df[SET_POP + "{}".format(year)],
                                   new_connections=self.df[SET_NEW_CONNECTIONS + "{}".format(year)],
                                   total_energy_per_cell=self.df[SET_TOTAL_ENERGY_PER_CELL],
                                   prev_code=self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)],
                                   num_people_per_hh=self.df[SET_NUM_PEOPLE_PER_HH],
                                   grid_cell_area=self.df[SET_GRID_CELL_AREA],
                                   additional_mv_line_length=self.df[SET_HYDRO_DIST])

        logging.info('Calculate minigrid PV LCOE')
        self.df[SET_LCOE_MG_PV + "{}".format(year)], mg_pv_investment = \
            mg_pv_calc.get_lcoe(energy_per_cell=self.df[SET_ENERGY_PER_CELL + "{}".format(year)],
                                start_year=year - time_step,
                                end_year=end_year,
                                people=self.df[SET_POP + "{}".format(year)],
                                new_connections=self.df[SET_NEW_CONNECTIONS + "{}".format(year)],
                                total_energy_per_cell=self.df[SET_TOTAL_ENERGY_PER_CELL],
                                prev_code=self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)],
                                num_people_per_hh=self.df[SET_NUM_PEOPLE_PER_HH],
                                grid_cell_area=self.df[SET_GRID_CELL_AREA],
                                capacity_factor=self.df[SET_GHI] / HOURS_PER_YEAR)
        self.df.loc[self.df[SET_GHI] <= 1000, SET_LCOE_MG_PV + "{}".format(year)] = 99

        logging.info('Calculate minigrid wind LCOE')
        self.df[SET_LCOE_MG_WIND + "{}".format(year)], mg_wind_investment = \
            mg_wind_calc.get_lcoe(energy_per_cell=self.df[SET_ENERGY_PER_CELL + "{}".format(year)],
                                  start_year=year - time_step,
                                  end_year=end_year,
                                  people=self.df[SET_POP + "{}".format(year)],
                                  new_connections=self.df[SET_NEW_CONNECTIONS + "{}".format(year)],
                                  total_energy_per_cell=self.df[SET_TOTAL_ENERGY_PER_CELL],
                                  prev_code=self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)],
                                  num_people_per_hh=self.df[SET_NUM_PEOPLE_PER_HH],
                                  grid_cell_area=self.df[SET_GRID_CELL_AREA],
                                  capacity_factor=self.df[SET_WINDCF])
        self.df.loc[self.df[SET_WINDCF] <= 0.1, SET_LCOE_MG_WIND + "{}".format(year)] = 99

        if diesel_techs == 0:
            self.df[SET_LCOE_MG_DIESEL + "{}".format(year)] = 99
            self.df[SET_LCOE_SA_DIESEL + "{}".format(year)] = 99
            sa_diesel_investment = mg_pv_investment * 0
            mg_diesel_investment = mg_pv_investment * 0
        else:
            logging.info('Calculate minigrid diesel LCOE')
            self.df[SET_LCOE_MG_DIESEL + "{}".format(year)], mg_diesel_investment = \
                mg_diesel_calc.get_lcoe(energy_per_cell=self.df[SET_ENERGY_PER_CELL + "{}".format(year)],
                                        start_year=year - time_step,
                                        end_year=end_year,
                                        people=self.df[SET_POP + "{}".format(year)],
                                        new_connections=self.df[SET_NEW_CONNECTIONS + "{}".format(year)],
                                        total_energy_per_cell=self.df[SET_TOTAL_ENERGY_PER_CELL],
                                        prev_code=self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)],
                                        num_people_per_hh=self.df[SET_NUM_PEOPLE_PER_HH],
                                        grid_cell_area=self.df[SET_GRID_CELL_AREA],
                                        fuel_cost=self.df[SET_MG_DIESEL_FUEL + "{}".format(year)],
                                        )

            logging.info('Calculate standalone diesel LCOE')
            self.df[SET_LCOE_SA_DIESEL + "{}".format(year)], sa_diesel_investment = \
                sa_diesel_calc.get_lcoe(energy_per_cell=self.df[SET_ENERGY_PER_CELL + "{}".format(year)],
                                        start_year=year - time_step,
                                        end_year=end_year,
                                        people=self.df[SET_POP + "{}".format(year)],
                                        new_connections=self.df[SET_NEW_CONNECTIONS + "{}".format(year)],
                                        total_energy_per_cell=self.df[SET_TOTAL_ENERGY_PER_CELL],
                                        prev_code=self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)],
                                        num_people_per_hh=self.df[SET_NUM_PEOPLE_PER_HH],
                                        grid_cell_area=self.df[SET_GRID_CELL_AREA],
                                        fuel_cost=self.df[SET_SA_DIESEL_FUEL + "{}".format(year)],
                                        )

        logging.info('Calculate standalone PV LCOE')
        self.df[SET_LCOE_SA_PV + "{}".format(year)], sa_pv_investment = \
            sa_pv_calc.get_lcoe(energy_per_cell=self.df[SET_ENERGY_PER_CELL + "{}".format(year)],
                                start_year=year - time_step,
                                end_year=end_year,
                                people=self.df[SET_POP + "{}".format(year)],
                                new_connections=self.df[SET_NEW_CONNECTIONS + "{}".format(year)],
                                total_energy_per_cell=self.df[SET_TOTAL_ENERGY_PER_CELL],
                                prev_code=self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)],
                                num_people_per_hh=self.df[SET_NUM_PEOPLE_PER_HH],
                                grid_cell_area=self.df[SET_GRID_CELL_AREA],
                                capacity_factor=self.df[SET_GHI] / HOURS_PER_YEAR)
        self.df.loc[self.df[SET_GHI] <= 1000, SET_LCOE_SA_PV + "{}".format(year)] = 99

        self.choose_minimum_off_grid_tech(year, mg_hydro_calc)

        return sa_diesel_investment, sa_pv_investment, mg_diesel_investment, mg_pv_investment, mg_wind_investment, \
            mg_hydro_investment

    def choose_minimum_off_grid_tech(self, year, mg_hydro_calc):
        """Choose minimum LCOE off-grid technology

        First step determines the off-grid technology with minimum LCOE
        Second step determnines the value (number) of the selected minimum off-grid technology

        Arguments
        ---------
        year : int
        mg_hydro_calc : dict
        """

        logging.info('Determine minimum technology (off-grid)')
        self.df[SET_MIN_OFFGRID + "{}".format(year)] = self.df[[SET_LCOE_SA_PV + "{}".format(year),
                                                                SET_LCOE_MG_WIND + "{}".format(year),
                                                                SET_LCOE_MG_PV + "{}".format(year),
                                                                SET_LCOE_MG_HYDRO + "{}".format(year),
                                                                SET_LCOE_MG_DIESEL + "{}".format(year),
                                                                SET_LCOE_SA_DIESEL + "{}".format(year)]].T.idxmin()

        # A df with all hydro-power sites, to ensure that they aren't assigned more capacity than is available
        hydro_used = 'HydropowerUsed'  # the amount of the hydro potential that has been assigned
        hydro_lcoe = self.df[SET_LCOE_MG_HYDRO + "{}".format(year)].copy()
        hydro_df = self.df[[SET_HYDRO_FID, SET_HYDRO]].drop_duplicates(subset=SET_HYDRO_FID)
        hydro_df[hydro_used] = 0
        hydro_df = hydro_df.set_index(SET_HYDRO_FID)
        max_hydro_dist = 5  # the max distance in km to consider hydropower viable
        additional_capacity = (
                (self.df[SET_ENERGY_PER_CELL + "{}".format(year)]) /
                (HOURS_PER_YEAR * mg_hydro_calc.capacity_factor * mg_hydro_calc.base_to_peak_load_ratio *
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

        self.df[SET_MIN_OFFGRID + "{}".format(year)] = self.df[[SET_LCOE_SA_PV + "{}".format(year),
                                                                SET_LCOE_MG_WIND + "{}".format(year),
                                                                SET_LCOE_MG_PV + "{}".format(year),
                                                                SET_LCOE_MG_HYDRO + "{}".format(year),
                                                                SET_LCOE_MG_DIESEL + "{}".format(year),
                                                                SET_LCOE_SA_DIESEL + "{}".format(year)]].T.idxmin()

        logging.info('Determine minimum tech LCOE')
        self.df[SET_MIN_OFFGRID_LCOE + "{}".format(year)] = self.df[[SET_LCOE_SA_PV + "{}".format(year),
                                                                     SET_LCOE_MG_WIND + "{}".format(year),
                                                                     SET_LCOE_MG_PV + "{}".format(year),
                                                                     SET_LCOE_MG_HYDRO + "{}".format(year),
                                                                     SET_LCOE_MG_DIESEL + "{}".format(year),
                                                                     SET_LCOE_SA_DIESEL + "{}".format(year)]].T.min()

        codes = {SET_LCOE_MG_HYDRO + "{}".format(year): 7,
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

    def results_columns(self, year, time_step, prio, auto_intensification):
        """Calculate the capacity and investment requirements for each settlement

        Once the grid extension algorithm has been run, determine the minimum overall option,
        and calculate the capacity and investment requirements for each settlement

        Arguments
        ---------
        year : int

        """

        # logging.info('Determine minimum overall')
        self.df[SET_MIN_OVERALL + "{}".format(year)] = self.df[[SET_LCOE_GRID + "{}".format(year),
                                                                SET_LCOE_SA_PV + "{}".format(year),
                                                                SET_LCOE_MG_WIND + "{}".format(year),
                                                                SET_LCOE_MG_PV + "{}".format(year),
                                                                SET_LCOE_MG_HYDRO + "{}".format(year),
                                                                SET_LCOE_MG_DIESEL + "{}".format(year),
                                                                SET_LCOE_SA_DIESEL + "{}".format(year)]].T.idxmin()

        self.df.loc[self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 1,
                    SET_MIN_OVERALL + "{}".format(year)] = 'Grid' + "{}".format(year)

        if (prio == 2) or (prio == 4):
            self.df.loc[(self.df[SET_MV_DIST_PLANNED] < auto_intensification) &
                        (self.df[SET_LCOE_GRID + "{}".format(year)] != 99),
                        SET_MIN_OVERALL + "{}".format(year)] = 'Grid' + "{}".format(year)

        # logging.info('Determine minimum overall LCOE')
        self.df[SET_MIN_OVERALL_LCOE + "{}".format(year)] = self.df[[SET_LCOE_GRID + "{}".format(year),
                                                                     SET_LCOE_SA_PV + "{}".format(year),
                                                                     SET_LCOE_MG_WIND + "{}".format(year),
                                                                     SET_LCOE_MG_PV + "{}".format(year),
                                                                     SET_LCOE_MG_HYDRO + "{}".format(year),
                                                                     SET_LCOE_MG_DIESEL + "{}".format(year),
                                                                     SET_LCOE_SA_DIESEL + "{}".format(year)]].T.min()

        self.df.loc[self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 1,
                    SET_MIN_OVERALL_LCOE + "{}".format(year)] = self.df[SET_LCOE_GRID + "{}".format(year)]

        if (prio == 2) or (prio == 4):
            self.df.loc[(self.df[SET_MV_DIST_PLANNED] < auto_intensification) &
                        (self.df[SET_LCOE_GRID + "{}".format(year)] != 99),
                        SET_MIN_OVERALL_LCOE + "{}".format(year)] = self.df[SET_LCOE_GRID + "{}".format(year)]

        # logging.info('Add technology codes')
        codes = {SET_LCOE_GRID + "{}".format(year): 1,
                 SET_LCOE_MG_HYDRO + "{}".format(year): 7,
                 SET_LCOE_MG_WIND + "{}".format(year): 6,
                 SET_LCOE_MG_PV + "{}".format(year): 5,
                 SET_LCOE_MG_DIESEL + "{}".format(year): 4,
                 SET_LCOE_SA_DIESEL + "{}".format(year): 2,
                 SET_LCOE_SA_PV + "{}".format(year): 3}

        for key in codes.keys():
            self.df.loc[self.df[SET_MIN_OVERALL + "{}".format(year)] == key,
                        SET_MIN_OVERALL_CODE + "{}".format(year)] = codes[key]

    def calculate_investments(self, sa_diesel_investment, sa_pv_investment, mg_diesel_investment, mg_pv_investment,
                              mg_wind_investment, mg_hydro_investment, grid_investment, year):

        logging.info('Calculate investment cost')

        self.df[SET_INVESTMENT_COST + "{}".format(year)] = 0

        grid = pd.DataFrame(np.where(self.df[SET_MIN_OVERALL_CODE + "{}".format(year)] == 1, 1, 0))
        sa_diesel = pd.DataFrame(np.where(self.df[SET_MIN_OVERALL_CODE + "{}".format(year)] == 2, 1, 0))
        sa_pv = pd.DataFrame(np.where(self.df[SET_MIN_OVERALL_CODE + "{}".format(year)] == 3, 1, 0))
        mg_diesel = pd.DataFrame(np.where(self.df[SET_MIN_OVERALL_CODE + "{}".format(year)] == 4, 1, 0))
        mg_pv = pd.DataFrame(np.where(self.df[SET_MIN_OVERALL_CODE + "{}".format(year)] == 5, 1, 0))
        mg_wind = pd.DataFrame(np.where(self.df[SET_MIN_OVERALL_CODE + "{}".format(year)] == 6, 1, 0))
        mg_hydro = pd.DataFrame(np.where(self.df[SET_MIN_OVERALL_CODE + "{}".format(year)] == 7, 1, 0))

        self.df[SET_INVESTMENT_COST + "{}".format(year)] = grid * grid_investment + sa_diesel * sa_diesel_investment + \
            sa_pv * sa_pv_investment + mg_diesel * mg_diesel_investment + mg_pv * mg_pv_investment + \
            mg_wind * mg_wind_investment + mg_hydro * mg_hydro_investment

    def apply_limitations(self, eleclimit, year, time_step, prioritization, auto_densification=0):

        logging.info('Determine electrification limits')
        choice = int(prioritization)
        self.df[SET_LIMIT + "{}".format(year)] = 0

        # Calculate the total population targeted to be electrified
        elec_target_pop = eleclimit * self.df[SET_POP + "{}".format(year)].sum()

        # Adding a column with investment/capita
        self.df[SET_INVEST_PER_CAPITA + "{}".format(year)] = \
            self.df[SET_INVESTMENT_COST + "{}".format(year)] / self.df[SET_NEW_CONNECTIONS + "{}".format(year)]

        if choice == 4:
            # Choose only already electrified settlements and settlements within intensification target range,
            # regardless of target electrification rate
            self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] < 99),
                        SET_LIMIT + "{}".format(year)] = 1
            self.df.loc[self.df[SET_MV_DIST_PLANNED] < auto_densification, SET_LIMIT + "{}".format(year)] = 1

        elif eleclimit == 1:
            # If electrification target rate is 100%, set all settlements to electrified
            self.df[SET_LIMIT + "{}".format(year)] = 1

        elif choice == 2:
            # Prioritize already electrified settlements, then intensification, then lowest investment per capita

            self.df['Intensification'] = np.where(self.df[SET_MV_DIST_PLANNED] < auto_densification, 1, 0)

            self.df.sort_values(by=[SET_ELEC_FINAL_CODE + "{}".format(year - time_step),
                                    'Intensification',
                                    SET_INVEST_PER_CAPITA + "{}".format(year)], inplace=True)

            cumulative_pop = self.df[SET_POP + "{}".format(year)].cumsum()

            self.df[SET_LIMIT + "{}".format(year)] = np.where(cumulative_pop < elec_target_pop, 1, 0)

            del self.df['Intensification']

            self.df.sort_index(inplace=True)

            # Ensure already electrified settlements remain electrified
            self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] < 99),
                        SET_LIMIT + "{}".format(year)] = 1

        elif choice == 5:
            # Prioritize already electrified settlements first, then lowest investment per capita
            self.df.sort_values(by=[SET_ELEC_FINAL_CODE + "{}".format(year - time_step),
                                    SET_INVEST_PER_CAPITA + "{}".format(year)], inplace=True)

            cumulative_pop = self.df[SET_POP + "{}".format(year)].cumsum()

            self.df[SET_LIMIT + "{}".format(year)] = np.where(cumulative_pop < elec_target_pop, 1, 0)

            self.df.sort_index(inplace=True)

            # Ensure already electrified settlements remain electrified
            self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] < 99),
                        SET_LIMIT + "{}".format(year)] = 1

        elecrate = self.df.loc[self.df[SET_LIMIT + "{}".format(year)] == 1,
                               SET_POP + "{}".format(year)].sum() / self.df[SET_POP + "{}".format(year)].sum()

        logging.info('Determine final electrification decision')
        self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] = self.df[SET_MIN_OVERALL_CODE + "{}".format(year)]
        self.df.loc[(self.df[SET_LIMIT + "{}".format(year)] == 0), SET_ELEC_FINAL_CODE + "{}".format(year)] = 99

        print("The electrification rate achieved in {} is {:.1f} %".format(year, elecrate * 100))

    def calculate_new_capacity(self, mg_hydro_calc, mg_wind_calc, mg_pv_calc, sa_pv_calc, mg_diesel_calc,
                               sa_diesel_calc, grid_calc, year):

        logging.info('Calculate new capacity')
        self.df.loc[self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 99, SET_NEW_CAPACITY + "{}".format(year)] = 0

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
