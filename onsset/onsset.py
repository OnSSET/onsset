import logging
from math import asin, ceil, cos, exp, log, pi, radians, sin, sqrt

import numpy as np
import pandas as pd

logging.basicConfig(format='%(asctime)s\t\t%(message)s', level=logging.DEBUG)

# Columns in settlements file must match these exactly
SET_COUNTRY = 'Country'  # This cannot be changed, lots of code will break
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
SET_ELEC_FINAL_CODE = "Elec_Initial_Status_Grid"
SET_ELEC_FUTURE_OFFGRID = "Elec_Init_Status_Offgrid"
SET_ELEC_FUTURE_ACTUAL = "Actual_Elec_Status_"
SET_ELEC_FINAL_CODE = "GridElecIn"
SET_ELEC_FINAL_OFFGRID = "OffGridElecIn"
SET_NEW_CONNECTIONS = 'NewConnections'  # Number of new people with electricity connections
SET_MIN_GRID_DIST = 'MinGridDist'
SET_LCOE_GRID = 'Grid'  # All LCOE's in USD/kWh
SET_LCOE_SA_PV = 'SA_PV'
SET_LCOE_SA_DIESEL = 'SA_Diesel'
SET_LCOE_MG_WIND = 'MG_Wind'
SET_LCOE_MG_DIESEL = 'MG_Diesel'
SET_LCOE_MG_PV = 'MG_PV'
SET_LCOE_MG_HYDRO = 'MG_Hydro'
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
SET_NTL_BIN = 'NTLBin'
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
        # REVIEW - A final revision is needed before publishing
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
                 total_energy_per_cell, prev_code, grid_cell_area, conf_status=0, additional_mv_line_length=0,
                 capacity_factor=0, grid_penalty_ratio=1, fuel_cost=0, elec_loop=0, productive_nodes=0,
                 additional_transformer=0, get_investment_cost=False, get_investment_cost_lv=False,
                 get_investment_cost_mv=False, get_investment_cost_hv=False, get_investment_cost_transformer=False,
                 get_investment_cost_connection=False):
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

        if grid_penalty_ratio == 0:
            grid_penalty_ratio = self.grid_penalty_ratio

        # If a new capacity factor isn't given, use the class capacity factor (for hydro, diesel etc)
        if capacity_factor == 0:
            capacity_factor = self.capacity_factor

        hv_lines_total_length, mv_lines_connection_length, mv_lines_distribution_length, total_lv_lines_length, \
            num_transformers, no_of_hv_mv_substation, no_of_mv_mv_substation, no_of_hv_lv_substation, \
            no_of_mv_lv_substation, generation_per_year, peak_load, total_nodes = \
            self.td_network_cost(people, new_connections, prev_code, total_energy_per_cell, energy_per_cell,
                                 num_people_per_hh, grid_cell_area, additional_mv_line_length, additional_transformer)

        try:
            int(conf_status)
        except ValueError:
            conf_status = 0
        conf_grid_pen = {0: 1, 1: 1.1, 2: 1.25, 3: 1.5, 4: 2}
        # The investment and O&M costs are different for grid and non-grid solutions
        if self.grid_price > 0:
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
                                  no_of_mv_lv_substation * self.mv_lv_sub_station_cost) * conf_grid_pen[conf_status]
            td_investment_cost = td_investment_cost * grid_penalty_ratio
            td_om_cost = td_investment_cost * self.om_of_td_lines

            total_investment_cost = td_investment_cost
            total_om_cost = td_om_cost
            fuel_cost = self.grid_price  # TODO / (1 - self.distribution_losses) REVIEW
        else:
            # TODO: Possibly add substation here for mini-grids
            conflict_sa_pen = {0: 1, 1: 1.03, 2: 1.07, 3: 1.125, 4: 1.25}
            conflict_mg_pen = {0: 1, 1: 1.05, 2: 1.125, 3: 1.25, 4: 1.5}
            total_lv_lines_length *= 0 if self.standalone else 1
            mv_lines_distribution_length *= 0 if self.standalone else 1
            mv_total_line_cost = self.mv_line_cost * mv_lines_distribution_length * conflict_mg_pen[conf_status]
            lv_total_line_cost = self.lv_line_cost * total_lv_lines_length * conflict_mg_pen[conf_status]
            service_transformer_total_cost = 0 if self.standalone else num_transformers * self.service_transf_cost * \
                conflict_mg_pen[conf_status]
            installed_capacity = peak_load / capacity_factor
            td_investment_cost = mv_total_line_cost + lv_total_line_cost + total_nodes * self.connection_cost_per_hh + \
                service_transformer_total_cost
            td_om_cost = td_investment_cost * self.om_of_td_lines * conflict_sa_pen[conf_status] if self.standalone \
                else td_investment_cost * self.om_of_td_lines * conflict_mg_pen[conf_status]

            cap_cost = 0
            for key in self.capital_cost:
                if self.standalone and installed_capacity / (people / num_people_per_hh) < key:
                    cap_cost = self.capital_cost[key]
                    break
                elif installed_capacity < key:
                    cap_cost = self.capital_cost[key]
                    break

            if self.standalone:
                capital_investment = installed_capacity * cap_cost * conflict_sa_pen[conf_status]
                total_om_cost = cap_cost * self.om_costs * conflict_sa_pen[conf_status] * installed_capacity
            else:
                capital_investment = installed_capacity * cap_cost * conflict_mg_pen[conf_status]
                total_om_cost = td_om_cost + (cap_cost * conflict_mg_pen[conf_status] *
                                              self.om_costs * installed_capacity)
            total_investment_cost = td_investment_cost + capital_investment

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
            return np.sum(discounted_investments) + self.grid_capacity_investment * peak_load / discount_factor[step]
        elif get_investment_cost_lv:
            return total_lv_lines_length * (self.lv_line_cost * conf_grid_pen[conf_status])
        elif get_investment_cost_mv:
            return (mv_lines_connection_length * self.mv_line_cost * (1 + self.existing_grid_cost_ratio * elec_loop) +
                    mv_lines_distribution_length * self.mv_line_cost) * conf_grid_pen[conf_status]
        elif get_investment_cost_hv:
            return hv_lines_total_length * (self.hv_line_cost * conf_grid_pen[conf_status]) * \
                   (1 + self.existing_grid_cost_ratio * elec_loop)
        elif get_investment_cost_transformer:
            return (no_of_hv_lv_substation * self.hv_lv_sub_station_cost +
                    no_of_hv_mv_substation * self.hv_mv_sub_station_cost +
                    no_of_mv_mv_substation * self.mv_mv_sub_station_cost +
                    no_of_mv_lv_substation * self.mv_lv_sub_station_cost) * conf_grid_pen[conf_status]
        elif get_investment_cost_connection:
            return total_nodes * self.connection_cost_per_hh
        else:
            discounted_costs = (investments + operation_and_maintenance + fuel - salvage) / discount_factor
            discounted_generation = el_gen / discount_factor
            return np.sum(discounted_costs) / np.sum(discounted_generation)

    def transmission_network(self, peak_load, additional_mv_line_length=0, additional_transformer=0,
                             mv_distribution=False):
        """This method calculates the required components for connecting the settlement
        Settlements can be connected to grid or a hydropower source
        This includes potentially HV lines, MV lines and substations

        Arguments
        ---------
        peak_load : float
            Peak load in the settlement (kW)
        additional_mv_line_length
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

            if peak_load <= max_mv_load and additional_mv_line_length < 50:
                mv_amperage = self.mv_lv_sub_station_type / self.mv_line_type
                no_of_mv_lines = ceil(peak_load / (mv_amperage * self.mv_line_type))
                mv_km = additional_mv_line_length * no_of_mv_lines
            else:
                hv_amperage = self.hv_lv_sub_station_type / self.hv_line_type
                no_of_hv_lines = ceil(peak_load / (hv_amperage * self.hv_line_type))
                hv_km = additional_mv_line_length * no_of_hv_lines

            if mv_distribution and hv_km > 0:
                no_of_hv_mv_subs = ceil(peak_load / self.hv_lv_sub_station_type)
            elif mv_distribution and mv_km > 0:
                no_of_mv_mv_subs = ceil(peak_load / self.mv_lv_sub_station_type)
            elif hv_km > 0:
                no_of_hv_lv_subs = ceil(peak_load / self.hv_lv_sub_station_type)
            else:
                no_of_mv_lv_subs = ceil(peak_load / self.mv_lv_sub_station_type)

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

            try:
                no_of_service_transf = ceil(
                    max(s_max / self.service_transf_type, total_nodes / self.max_nodes_per_serv_trans,
                        grid_cell_area / max_transformer_area))
            except ValueError:  # TODO Review if this is needed
                no_of_service_transf = 1
            transformer_radius = ((grid_cell_area / no_of_service_transf) / pi) ** 0.5
            transformer_load = peak_load / no_of_service_transf
            cluster_radius = (grid_cell_area / pi) ** 0.5

            # Sizing lv lines in settlement
            if 2 / 3 * cluster_radius * transformer_load * 1000 < self.load_moment:
                cluster_lv_lines_length = 2 / 3 * cluster_radius * no_of_service_transf
                cluster_mv_lines_length = 0
            else:
                cluster_lv_lines_length = 0
                cluster_mv_lines_length = 2 * transformer_radius * no_of_service_transf

            hh_area = grid_cell_area / total_nodes
            hh_diameter = 2 * ((hh_area / pi) ** 0.5)

            transformer_lv_lines_length = hh_diameter * total_nodes

            lv_km = cluster_lv_lines_length + transformer_lv_lines_length

        return cluster_mv_lines_length, lv_km, no_of_service_transf, consumption, peak_load, total_nodes

    def td_network_cost(self, people, new_connections, prev_code, total_energy_per_cell, energy_per_cell,
                        num_people_per_hh, grid_cell_area, additional_mv_line_length=0, additional_transformer=0,
                        productive_nodes=0):
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
        additional_mv_line_length
            Distance to connect the settlement
        additional_transformer : int
            If a transformer is needed on other end to connect to HV line
        productive_nodes : int
            Additional connections (schools, health facilities, shops)
        """

        if people != new_connections and (prev_code < 2 or prev_code > 3):
            # If there is already a distribution network in the settlement, all calculations are mad twice.
            # First the network required to meet the full demand is calculated, then the existing network is calc.
            # The additional network components required is the difference between the two

            # Start by calculating the distribution network required to meet all of the demand
            cluster_mv_lines_length1, cluster_lv_lines_length1, no_of_service_transf1, \
                generation_per_year1, peak_load1, total_nodes1 = \
                self.distribution_network(people, total_energy_per_cell, num_people_per_hh, grid_cell_area,
                                          productive_nodes)

            # Next calculate the network that is already there
            cluster_mv_lines_length2, cluster_lv_lines_length2, no_of_service_transf2, \
                generation_per_year2, peak_load2, total_nodes2 = \
                self.distribution_network((people - new_connections), (total_energy_per_cell - energy_per_cell),
                                          num_people_per_hh, grid_cell_area, productive_nodes)

            # Then calculate the difference between the two
            mv_lines_distribution_length = max(cluster_lv_lines_length1 - cluster_lv_lines_length2, 0)
            total_lv_lines_length = max(cluster_lv_lines_length1 - cluster_lv_lines_length2, 0)
            num_transformers = max(no_of_service_transf1 - no_of_service_transf2, 0)
            generation_per_year = max(generation_per_year1 - generation_per_year2, 0)
            peak_load = max(peak_load1 - peak_load2, 0)
            total_nodes = max(total_nodes1 - total_nodes2, 0)

            # Examine if there are any MV lines in the distribution network, used to determine transformer type
            if mv_lines_distribution_length > 0:
                mv_distribution = True
            else:
                mv_distribution = False

            # Then calculate the transmission network (HV or MV lines plus transformers) using the same methodology
            hv_lines_total_length1, mv_lines_connection_length1, no_of_hv_mv_substation1, no_of_mv_mv_substation1, \
                no_of_hv_lv_substation1, no_of_mv_lv_substation1 = \
                self.transmission_network(peak_load1, additional_mv_line_length, additional_transformer,
                                          mv_distribution=mv_distribution)

            hv_lines_total_length2, mv_lines_connection_length2, no_of_hv_mv_substation2, no_of_mv_mv_substation2, \
                no_of_hv_lv_substation2, no_of_mv_lv_substation2 = \
                self.transmission_network(peak_load2, additional_mv_line_length, additional_transformer,
                                          mv_distribution=mv_distribution)

            hv_lines_total_length = max(hv_lines_total_length1 - hv_lines_total_length2, 0)
            mv_lines_connection_length = max(mv_lines_connection_length1 - mv_lines_connection_length2, 0)
            no_of_hv_lv_substation = max(no_of_hv_lv_substation1 - no_of_hv_lv_substation2, 0)
            no_of_hv_mv_substation = max(no_of_hv_mv_substation1 - no_of_hv_mv_substation2, 0)
            no_of_mv_mv_substation = max(no_of_mv_mv_substation1 - no_of_mv_mv_substation2, 0)
            no_of_mv_lv_substation = max(no_of_mv_lv_substation1 - no_of_mv_lv_substation2, 0)

        else:
            # If no distribution network is present, perform the calculations only once
            mv_lines_distribution_length, total_lv_lines_length, num_transformers, generation_per_year, peak_load, \
                total_nodes = self.distribution_network(people, energy_per_cell, num_people_per_hh, grid_cell_area,
                                                        productive_nodes)

            if mv_lines_distribution_length > 0:
                mv_distribution = True
            else:
                mv_distribution = False

            hv_lines_total_length, mv_lines_connection_length, no_of_hv_mv_substation, no_of_mv_mv_substation, \
                no_of_hv_lv_substation, no_of_mv_lv_substation = \
                self.transmission_network(peak_load, additional_mv_line_length, additional_transformer,
                                          mv_distribution=mv_distribution)

        return hv_lines_total_length, mv_lines_connection_length, mv_lines_distribution_length, total_lv_lines_length, \
            num_transformers, no_of_hv_mv_substation, no_of_mv_mv_substation, no_of_hv_lv_substation, \
            no_of_mv_lv_substation, generation_per_year, peak_load, total_nodes


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

    def diesel_cost_columns(self, sa_diesel_cost, mg_diesel_cost, year):

        def diesel_fuel_cost_calculator(diesel_price, diesel_truck_consumption, diesel_truck_volume,
                                        traveltime, efficiency):
            # We apply the Szabo formula to calculate the transport cost for the diesel
            # p = (p_d + 2*p_d*consumption*time/volume)*(1/mu)*(1/LHVd)

            return (diesel_price + 2 * diesel_price * diesel_truck_consumption *
                    traveltime) / diesel_truck_volume / LHV_DIESEL / efficiency

        self.df[SET_SA_DIESEL_FUEL + "{}".format(year)] = self.df.apply(
            lambda row: diesel_fuel_cost_calculator(diesel_price=sa_diesel_cost['diesel_price'],
                                                    diesel_truck_volume=sa_diesel_cost['diesel_truck_volume'],
                                                    diesel_truck_consumption=sa_diesel_cost['diesel_truck_consumption'],
                                                    efficiency=sa_diesel_cost['efficiency'],
                                                    traveltime=row[SET_TRAVEL_HOURS]
                                                    ), axis=1)

        self.df[SET_MG_DIESEL_FUEL + "{}".format(year)] = self.df.apply(
            lambda row: diesel_fuel_cost_calculator(diesel_price=mg_diesel_cost['diesel_price'],
                                                    diesel_truck_volume=mg_diesel_cost['diesel_truck_volume'],
                                                    diesel_truck_consumption=mg_diesel_cost['diesel_truck_consumption'],
                                                    efficiency=mg_diesel_cost['efficiency'],
                                                    traveltime=row[SET_TRAVEL_HOURS]
                                                    ), axis=1)

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

    def classify_road_distance(self, road_distance):
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

    def classify_substation_distance(self, substation_distance):
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

    def classify_elevation(self, elevation):
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

    def classify_slope(self, slope):
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

    def classify_land_cover(self, column):
        """this is a different method employed to classify land cover and create new columns with the classification

        Arguments
        ---------
        column : series

        Notes
        -----
        0,11 =1,
        6, 8 = 2
        1, 3, 5, 12 ,13,15,=3,
        2,4=4,
        7,9,10,14,16=5
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
        ROAD_DIST_CLASSIFIED = self.classify_road_distance(data_frame[SET_ROAD_DIST])

        logging.info('Classify substation dist')
        SUBSTATION_DIST_CLASSIFIED = self.classify_substation_distance(data_frame[SET_SUBSTATION_DIST])

        logging.info('Classify elevation')
        ELEVATION_CLASSIFIED = self.classify_elevation(data_frame[SET_ELEVATION])

        logging.info('Classify slope')
        SLOPE_CLASSIFIED = self.classify_slope(data_frame[SET_SLOPE])

        logging.info('Classify land cover')
        LAND_COVER_CLASSIFIED = self.classify_land_cover(data_frame[SET_LAND_COVER])

        logging.info('Combined classification')
        COMBINED_CLASSIFICATION = (0.15 * ROAD_DIST_CLASSIFIED +
                                   0.20 * SUBSTATION_DIST_CLASSIFIED +
                                   0.15 * ELEVATION_CLASSIFIED +
                                   0.30 * SLOPE_CLASSIFIED +
                                   0.20 * LAND_COVER_CLASSIFIED)

        logging.info('Grid penalty')
        """this calculates the penalty from the results obtained from the combined classifications"""
        classification = COMBINED_CLASSIFICATION.astype(float)

        c = 1 + (np.exp(.85 * np.abs(1 - classification)) - 1) / 100

        return c

    def calc_wind_cfs(self):
        """Calculate the wind capacity factor based on the average wind velocity.

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

        print(pop_actual, pop_modelled)

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
                    print(
                        "The urban settlements identified as electrified are lower than in statistics; "
                        "Please re-adjust the calibration conditions")
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
                        "The rural settlements identified as electrified are lower than in statistics; "
                        "Please re-adjust the calibration conditions")
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
                    print(
                        "The urban settlements identified as electrified are lower than in statistics; "
                        "Please re-adjust the calibration conditions")

                if rural_elec_factor > 1:
                    self.df.loc[(self.df[SET_ELEC_CURRENT] == 1) & (self.df[SET_URBAN] <= 1), SET_ELEC_POP_CALIB] *= (
                            1 / rural_elec_factor)
                else:
                    print(
                        "The rural settlements identified as electrified are lower than in statistics; "
                        "Please re-adjust the calibration conditions")

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

            print('The modelled electrification rate achieved is {0:.2f}.'
                  'Urban elec. rate is {1:.2f} and Rural elec. rate is {2:.2f}. \n'
                  'If this is not acceptable please revise this '
                  'part of the algorithm'.format(elec_modelled - elec_actual,
                                                 urban_elec_ratio - elec_actual_urban,
                                                 rural_elec_ratio - elec_actual_rural))
            condition = 1

        self.df[SET_ELEC_FINAL_CODE + "{}".format(start_year)] = \
            self.df.apply(lambda row: 1 if row[SET_ELEC_CURRENT] == 1 else 0, axis=1)
        self.df[SET_ELEC_FUTURE_OFFGRID + "{}".format(start_year)] = self.df.apply(lambda row: 0, axis=1)
        self.df[SET_ELEC_FUTURE_ACTUAL + "{}".format(start_year)] = \
            self.df.apply(lambda row: 1 if row[SET_ELEC_FINAL_CODE + "{}".format(start_year)] == 1 or
                          row[SET_ELEC_FUTURE_OFFGRID + "{}".format(start_year)] == 1 else 0, axis=1)
        self.df[SET_ELEC_FINAL_CODE + "{}".format(start_year)] = \
            self.df.apply(lambda row: 1 if row[SET_ELEC_CURRENT] == 1 else 99, axis=1)

        return elec_modelled, rural_elec_ratio, urban_elec_ratio

    def pre_electrification(self, grid_price, year, time_step, start_year):

        """" ... """

        logging.info('Define the initial electrification status')

        # Update electrification status based on already existing
        if (year - time_step) == start_year:
            self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] = 0
            self.df.loc[
                self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 1, SET_ELEC_FINAL_CODE + "{}".format(
                    year)] = 1
        else:
            self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] = 0
            self.df.loc[
                self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 1, SET_ELEC_FINAL_CODE + "{}".format(
                    year)] = 1
            self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 1) & (
                    self.df[SET_LIMIT + "{}".format(year - time_step)] == 1), SET_ELEC_FINAL_CODE + "{}".format(
                year)] = 1

        if (year - time_step) == start_year:
            self.df[SET_ELEC_FUTURE_OFFGRID + "{}".format(year)] = 0
            self.df.loc[self.df[SET_ELEC_FUTURE_OFFGRID + "{}".format(
                year - time_step)] == 1, SET_ELEC_FUTURE_OFFGRID + "{}".format(year)] = 1
        else:
            self.df[SET_ELEC_FUTURE_OFFGRID + "{}".format(year)] = 0
            self.df.loc[(self.df[SET_ELEC_FUTURE_OFFGRID + "{}".format(year - time_step)] == 1) &
                        (self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] != 1),
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
            self.df.loc[self.df[SET_ELEC_FINAL_CODE + "{}".format(
                year - time_step)] == 1, SET_ELEC_FUTURE_ACTUAL + "{}".format(year)] = 1
            self.df.loc[self.df[SET_ELEC_FUTURE_OFFGRID + "{}".format(
                year - time_step)] == 1, SET_ELEC_FUTURE_ACTUAL + "{}".format(year)] = 1

        self.df[SET_LCOE_GRID + "{}".format(year)] = 99
        self.df.loc[
            self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 1, SET_LCOE_GRID + "{}".format(year)] = grid_price

    def current_mv_line_dist(self):
        logging.info('Determine current MV line length')
        self.df[SET_MV_CONNECT_DIST] = 0
        self.df.loc[self.df[SET_ELEC_CURRENT] == 1, SET_MV_CONNECT_DIST] = self.df[SET_HV_DIST_CURRENT]
        self.df[SET_MIN_TD_DIST] = self.df[[SET_MV_DIST_PLANNED, SET_HV_DIST_PLANNED]].min(axis=1)

    def elec_extension(self, grid_calc, max_dist, year, start_year, end_year, time_step, grid_cap_gen_limit,
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
        enerperhh = self.df[SET_ENERGY_PER_CELL + "{}".format(year)]
        nupppphh = self.df[SET_NUM_PEOPLE_PER_HH]
        grid_cell_area = self.df[SET_GRID_CELL_AREA]
        prev_code = self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)]
        new_connections = self.df[SET_NEW_CONNECTIONS + "{}".format(year)]
        total_energy_per_cell = self.df[SET_TOTAL_ENERGY_PER_CELL]
        if year - time_step == start_year:
            elecorder = self.df[SET_ELEC_ORDER].tolist()
        else:
            elecorder = self.df[SET_ELEC_ORDER + "{}".format(year - time_step)].tolist()
        grid_penalty_ratio = self.df[SET_GRID_PENALTY].tolist()
        status = self.df[SET_ELEC_FINAL_CODE + "{}".format(year)].tolist()
        min_code_lcoes = self.df[SET_MIN_OFFGRID_LCOE + "{}".format(year)].tolist()
        new_lcoes = self.df[SET_LCOE_GRID + "{}".format(year)].tolist()
        cell_path_real = self.df[SET_MV_CONNECT_DIST].tolist()
        planned_hv_dist = self.df[SET_HV_DIST_PLANNED].tolist()  # If connecting from anywhere on the HV line
        planned_mv_dist = self.df[SET_MV_DIST_PLANNED].tolist()  # If connecting from anywhere on the HV line
        self.df['new_connections_household'] = self.df[SET_NEW_CONNECTIONS + "{}".format(year)] / self.df[
            SET_NUM_PEOPLE_PER_HH]

        urban_initially_electrified = sum(self.df.loc[
                                              (self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 1) & (
                                                      self.df[SET_URBAN] == 2)][
                                              SET_ENERGY_PER_CELL + "{}".format(year)])
        rural_initially_electrified = sum(self.df.loc[
                                              (self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 1) & (
                                                      self.df[SET_URBAN] < 2)][
                                              SET_ENERGY_PER_CELL + "{}".format(year)])
        densification_connections = sum(
            self.df.loc[self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 1]['new_connections_household'])
        consumption = rural_initially_electrified + urban_initially_electrified
        average_load = consumption / (1 - grid_calc.distribution_losses) / HOURS_PER_YEAR  # kW
        peak_load = average_load / grid_calc.base_to_peak_load_ratio  # kW
        grid_capacity_limit -= peak_load
        grid_connect_limit -= densification_connections

        cell_path_adjusted = list(np.zeros(len(status)).tolist())

        electrified = self.df[SET_ELEC_FINAL_CODE + "{}".format(year)].loc[
            self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 1].index.values.tolist()
        unelectrified = self.df[SET_ELEC_FINAL_CODE + "{}".format(year)].loc[
            self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 0].index.values.tolist()

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
                                               start_year=year - time_step,
                                               end_year=end_year,
                                               people=pop[unelec],
                                               new_connections=new_connections[unelec],
                                               total_energy_per_cell=total_energy_per_cell[unelec],
                                               prev_code=prev_code[unelec],
                                               num_people_per_hh=nupppphh[unelec],
                                               grid_cell_area=grid_cell_area[unelec],
                                               conf_status=confl[unelec],
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
            consumption = enerperhh[unelec]  # kWh/year
            average_load = consumption / (1 - grid_calc.distribution_losses) / HOURS_PER_YEAR  # kW
            peak_load = average_load / grid_calc.base_to_peak_load_ratio  # kW
            dist = planned_mv_dist[unelec]
            dist_adjusted = grid_penalty_ratio[unelec] * dist
            if dist_adjusted <= max_dist:
                grid_lcoe = grid_calc.get_lcoe(energy_per_cell=enerperhh[unelec],
                                               start_year=year - time_step,
                                               end_year=end_year,
                                               people=pop[unelec],
                                               new_connections=new_connections[unelec],
                                               total_energy_per_cell=total_energy_per_cell[unelec],
                                               prev_code=prev_code[unelec],
                                               num_people_per_hh=nupppphh[unelec],
                                               grid_cell_area=grid_cell_area[unelec],
                                               conf_status=confl[unelec],
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
            else:
                close.append(unelec)
        electrified = changes[:]
        unelectrified = close

        #  Extension from HV lines
        for unelec in unelectrified:
            consumption = enerperhh[unelec]  # kWh/year
            average_load = consumption / (1 - grid_calc.distribution_losses) / HOURS_PER_YEAR  # kW
            peak_load = average_load / grid_calc.base_to_peak_load_ratio  # kW
            dist = planned_hv_dist[unelec]
            dist_adjusted = grid_penalty_ratio[unelec] * dist
            if dist <= max_dist:
                elec_loop_value = 0
                grid_lcoe = grid_calc.get_lcoe(energy_per_cell=enerperhh[unelec],
                                               start_year=year - time_step,
                                               end_year=end_year,
                                               people=pop[unelec],
                                               new_connections=new_connections[unelec],
                                               total_energy_per_cell=total_energy_per_cell[unelec],
                                               prev_code=prev_code[unelec],
                                               num_people_per_hh=nupppphh[unelec],
                                               grid_cell_area=grid_cell_area[unelec],
                                               conf_status=confl[unelec],
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
            elec_nodes2 = []
            for elec in electrified:
                elec_nodes2.append((x[elec], y[elec]))
            elec_nodes2 = np.asarray(elec_nodes2)
            changes = []
            if len(elec_nodes2) > 0:
                for unelec in unelectrified:
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
                                                       start_year=year - time_step,
                                                       end_year=end_year,
                                                       people=pop[unelec],
                                                       new_connections=new_connections[unelec],
                                                       total_energy_per_cell=total_energy_per_cell[unelec],
                                                       prev_code=prev_code[unelec],
                                                       num_people_per_hh=nupppphh[unelec],
                                                       grid_cell_area=grid_cell_area[unelec],
                                                       conf_status=confl[unelec],
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
            electrified = changes[:]
            unelectrified = set(unelectrified).difference(electrified)

        return new_lcoes, cell_path_adjusted, elecorder, cell_path_real

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
        Calculate the LCOEs for all off-grid technologies, and calculate the minimum, so that the electrification
        algorithm knows where the bar is before it becomes economical to electrify

        """

        # A df with all hydro-power sites, to ensure that they aren't assigned more capacity than is available
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
                                                  start_year=year - time_step,
                                                  end_year=end_year,
                                                  people=row[SET_POP + "{}".format(year)],
                                                  new_connections=row[SET_NEW_CONNECTIONS + "{}".format(year)],
                                                  total_energy_per_cell=row[SET_TOTAL_ENERGY_PER_CELL],
                                                  prev_code=row[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)],
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
                                            start_year=year - time_step,
                                            end_year=end_year,
                                            people=row[SET_POP + "{}".format(year)],
                                            new_connections=row[SET_NEW_CONNECTIONS + "{}".format(year)],
                                            total_energy_per_cell=row[SET_TOTAL_ENERGY_PER_CELL],
                                            prev_code=row[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)],
                                            num_people_per_hh=row[SET_NUM_PEOPLE_PER_HH],
                                            grid_cell_area=row[SET_GRID_CELL_AREA],
                                            conf_status=row[SET_CONFLICT],
                                            capacity_factor=row[SET_GHI] / HOURS_PER_YEAR)
            if row[SET_GHI] > 1000
            else 99, axis=1)

        logging.info('Calculate minigrid wind LCOE')
        self.df[SET_LCOE_MG_WIND + "{}".format(year)] = self.df.apply(
            lambda row: mg_wind_calc.get_lcoe(energy_per_cell=row[SET_ENERGY_PER_CELL + "{}".format(year)],
                                              start_year=year - time_step,
                                              end_year=end_year,
                                              people=row[SET_POP + "{}".format(year)],
                                              new_connections=row[SET_NEW_CONNECTIONS + "{}".format(year)],
                                              total_energy_per_cell=row[SET_TOTAL_ENERGY_PER_CELL],
                                              prev_code=row[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)],
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
                                                    start_year=year - time_step,
                                                    end_year=end_year,
                                                    people=row[SET_POP + "{}".format(year)],
                                                    new_connections=row[SET_NEW_CONNECTIONS + "{}".format(year)],
                                                    total_energy_per_cell=row[SET_TOTAL_ENERGY_PER_CELL],
                                                    prev_code=row[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)],
                                                    num_people_per_hh=row[SET_NUM_PEOPLE_PER_HH],
                                                    grid_cell_area=row[SET_GRID_CELL_AREA],
                                                    conf_status=row[SET_CONFLICT],
                                                    fuel_cost=row[SET_MG_DIESEL_FUEL + "{}".format(year)],
                                                    ), axis=1)

            logging.info('Calculate standalone diesel LCOE')
            self.df[SET_LCOE_SA_DIESEL + "{}".format(year)] = self.df.apply(
                lambda row: sa_diesel_calc.get_lcoe(energy_per_cell=row[SET_ENERGY_PER_CELL + "{}".format(year)],
                                                    start_year=year - time_step,
                                                    end_year=end_year,
                                                    people=row[SET_POP + "{}".format(year)],
                                                    new_connections=row[SET_NEW_CONNECTIONS + "{}".format(year)],
                                                    total_energy_per_cell=row[SET_TOTAL_ENERGY_PER_CELL],
                                                    prev_code=row[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)],
                                                    num_people_per_hh=row[SET_NUM_PEOPLE_PER_HH],
                                                    grid_cell_area=row[SET_GRID_CELL_AREA],
                                                    conf_status=row[SET_CONFLICT],
                                                    fuel_cost=row[SET_SA_DIESEL_FUEL + "{}".format(year)],
                                                    ), axis=1)

        logging.info('Calculate standalone PV LCOE')
        self.df[SET_LCOE_SA_PV + "{}".format(year)] = self.df.apply(
            lambda row: sa_pv_calc.get_lcoe(energy_per_cell=row[SET_ENERGY_PER_CELL + "{}".format(year)],
                                            start_year=year - time_step,
                                            end_year=end_year,
                                            people=row[SET_POP + "{}".format(year)],
                                            new_connections=row[SET_NEW_CONNECTIONS + "{}".format(year)],
                                            total_energy_per_cell=row[SET_TOTAL_ENERGY_PER_CELL],
                                            prev_code=row[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)],
                                            num_people_per_hh=row[SET_NUM_PEOPLE_PER_HH],
                                            grid_cell_area=row[SET_GRID_CELL_AREA],
                                            conf_status=row[SET_CONFLICT],
                                            capacity_factor=row[SET_GHI] / HOURS_PER_YEAR) if row[SET_GHI] > 1000
            else 99,
            axis=1)
        self.choose_minimum_off_grid_tech(year)

    def choose_minimum_off_grid_tech(self, year):
        """Choose minimum LCOE off-grid technology

        First step determines the off-grid technology with minimum LCOE
        Second step determnines the value (number) of the selected minimum off-grid technology

        Arguments
        ---------
        year : int
        """

        logging.info('Determine minimum technology (off-grid)')
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

    def results_columns(self, year):
        """Calculate the capacity and investment requirements for each settlement

        Once the grid extension algorithm has been run, determine the minimum overall option,
        and calculate the capacity and investment requirements for each settlement

        Arguments
        ---------
        year : int

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
                 SET_LCOE_MG_HYDRO + "{}".format(year): 7,
                 SET_LCOE_MG_WIND + "{}".format(year): 6,
                 SET_LCOE_MG_PV + "{}".format(year): 5,
                 SET_LCOE_MG_DIESEL + "{}".format(year): 4,
                 SET_LCOE_SA_DIESEL + "{}".format(year): 2,
                 SET_LCOE_SA_PV + "{}".format(year): 3}

        for key in codes.keys():
            self.df.loc[self.df[SET_MIN_OVERALL + "{}".format(year)] == key,
                        SET_MIN_OVERALL_CODE + "{}".format(year)] = codes[key]

    def calculate_investments(self, mg_hydro_calc, mg_wind_calc, mg_pv_calc, sa_pv_calc, mg_diesel_calc,
                              sa_diesel_calc, grid_calc, year,
                              end_year, time_step):
        def res_investment_cost(row):
            min_code = row[SET_MIN_OVERALL_CODE + "{}".format(year)]

            if min_code == 2:
                return sa_diesel_calc.get_lcoe(energy_per_cell=row[SET_ENERGY_PER_CELL + "{}".format(year)],
                                               start_year=year - time_step,
                                               end_year=end_year,
                                               people=row[SET_POP + "{}".format(year)],
                                               new_connections=row[SET_NEW_CONNECTIONS + "{}".format(year)],
                                               total_energy_per_cell=row[SET_TOTAL_ENERGY_PER_CELL],
                                               prev_code=row[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)],
                                               num_people_per_hh=row[SET_NUM_PEOPLE_PER_HH],
                                               grid_cell_area=row[SET_GRID_CELL_AREA],
                                               conf_status=row[SET_CONFLICT],
                                               fuel_cost=row[SET_SA_DIESEL_FUEL + "{}".format(year)],
                                               get_investment_cost=True)

            elif min_code == 3:
                return sa_pv_calc.get_lcoe(energy_per_cell=row[SET_ENERGY_PER_CELL + "{}".format(year)],
                                           start_year=year - time_step,
                                           end_year=end_year,
                                           people=row[SET_POP + "{}".format(year)],
                                           new_connections=row[SET_NEW_CONNECTIONS + "{}".format(year)],
                                           total_energy_per_cell=row[SET_TOTAL_ENERGY_PER_CELL],
                                           prev_code=row[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)],
                                           num_people_per_hh=row[SET_NUM_PEOPLE_PER_HH],
                                           grid_cell_area=row[SET_GRID_CELL_AREA],
                                           capacity_factor=row[SET_GHI] / HOURS_PER_YEAR,
                                           conf_status=row[SET_CONFLICT],
                                           get_investment_cost=True)

            elif min_code == 6:
                return mg_wind_calc.get_lcoe(energy_per_cell=row[SET_ENERGY_PER_CELL + "{}".format(year)],
                                             start_year=year - time_step,
                                             end_year=end_year,
                                             people=row[SET_POP + "{}".format(year)],
                                             new_connections=row[SET_NEW_CONNECTIONS + "{}".format(year)],
                                             total_energy_per_cell=row[SET_TOTAL_ENERGY_PER_CELL],
                                             prev_code=row[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)],
                                             num_people_per_hh=row[SET_NUM_PEOPLE_PER_HH],
                                             grid_cell_area=row[SET_GRID_CELL_AREA],
                                             capacity_factor=row[SET_WINDCF],
                                             conf_status=row[SET_CONFLICT],
                                             get_investment_cost=True)

            elif min_code == 4:
                return mg_diesel_calc.get_lcoe(energy_per_cell=row[SET_ENERGY_PER_CELL + "{}".format(year)],
                                               start_year=year - time_step,
                                               end_year=end_year,
                                               people=row[SET_POP + "{}".format(year)],
                                               new_connections=row[SET_NEW_CONNECTIONS + "{}".format(year)],
                                               total_energy_per_cell=row[SET_TOTAL_ENERGY_PER_CELL],
                                               prev_code=row[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)],
                                               num_people_per_hh=row[SET_NUM_PEOPLE_PER_HH],
                                               grid_cell_area=row[SET_GRID_CELL_AREA],
                                               conf_status=row[SET_CONFLICT],
                                               fuel_cost=row[SET_MG_DIESEL_FUEL + "{}".format(year)],
                                               get_investment_cost=True)

            elif min_code == 5:
                return mg_pv_calc.get_lcoe(energy_per_cell=row[SET_ENERGY_PER_CELL + "{}".format(year)],
                                           start_year=year - time_step,
                                           end_year=end_year,
                                           people=row[SET_POP + "{}".format(year)],
                                           new_connections=row[SET_NEW_CONNECTIONS + "{}".format(year)],
                                           total_energy_per_cell=row[SET_TOTAL_ENERGY_PER_CELL],
                                           prev_code=row[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)],
                                           num_people_per_hh=row[SET_NUM_PEOPLE_PER_HH],
                                           grid_cell_area=row[SET_GRID_CELL_AREA],
                                           capacity_factor=row[SET_GHI] / HOURS_PER_YEAR,
                                           conf_status=row[SET_CONFLICT],
                                           get_investment_cost=True)

            elif min_code == 7:
                return mg_hydro_calc.get_lcoe(energy_per_cell=row[SET_ENERGY_PER_CELL + "{}".format(year)],
                                              start_year=year - time_step,
                                              end_year=end_year,
                                              people=row[SET_POP + "{}".format(year)],
                                              new_connections=row[SET_NEW_CONNECTIONS + "{}".format(year)],
                                              total_energy_per_cell=row[SET_TOTAL_ENERGY_PER_CELL],
                                              prev_code=row[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)],
                                              num_people_per_hh=row[SET_NUM_PEOPLE_PER_HH],
                                              grid_cell_area=row[SET_GRID_CELL_AREA],
                                              conf_status=row[SET_CONFLICT],
                                              mv_line_length=row[SET_HYDRO_DIST],
                                              get_investment_cost=True)

            elif min_code == 1:
                return grid_calc.get_lcoe(energy_per_cell=row[SET_ENERGY_PER_CELL + "{}".format(year)],
                                          start_year=year - time_step,
                                          end_year=end_year,
                                          people=row[SET_POP + "{}".format(year)],
                                          new_connections=row[SET_NEW_CONNECTIONS + "{}".format(year)],
                                          total_energy_per_cell=row[SET_TOTAL_ENERGY_PER_CELL],
                                          prev_code=row[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)],
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

    def apply_limitations(self, eleclimit, year, time_step, prioritization, auto_densification=0):

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

            # RUN_PARAM: Here one can modify the prioritization algorithm.
            # Currently only the first option is reviewed and ready to be used
            if choice == 1:  # Prioritize grid densification first, then lowest investment per capita
                elecrate = 0
                min_investment = 0
                min_dist_to_cities = 50
                iter_limit_3 = 0
                iter_limit_4 = 0
                self.df[SET_INVEST_PER_CAPITA + "{}".format(year)] = \
                    self.df[SET_INVESTMENT_COST + "{}".format(year)] / self.df[SET_NEW_CONNECTIONS + "{}".format(year)]
                step_size = self.df[SET_INVEST_PER_CAPITA + "{}".format(year)].quantile(q=0.95) / 100
                if sum(self.df[self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 1][
                           SET_POP + "{}".format(year)]) / \
                        self.df[SET_POP + "{}".format(year)].sum() < eleclimit:
                    eleclimit -= sum(self.df[self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 1][
                                         SET_POP + "{}".format(year)]) / self.df[SET_POP + "{}".format(year)].sum()

                    while abs(elecrate - eleclimit) > 0.01:
                        elecrate = sum(self.df[(self.df[SET_INVEST_PER_CAPITA + "{}".format(year)] < min_investment) &
                                               (self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 0) &
                                               (self.df[SET_TRAVEL_HOURS] < min_dist_to_cities)][
                                           SET_POP + "{}".format(year)]) / self.df[SET_POP + "{}".format(year)].sum()
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
                        (self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 1), SET_LIMIT + "{}".format(
                            year)] = 1

                    self.df.loc[(self.df[SET_INVEST_PER_CAPITA + "{}".format(year)] <= min_investment) &
                                (self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 0) &
                                (self.df[SET_TRAVEL_HOURS] <= min_dist_to_cities), SET_LIMIT + "{}".format(year)] = 1

                    self.df.loc[(self.df[SET_INVEST_PER_CAPITA + "{}".format(year)] <= min_investment) &
                                (self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 0) &
                                (self.df[SET_TRAVEL_HOURS] > min_dist_to_cities), SET_LIMIT + "{}".format(year)] = 0

                    self.df.loc[(self.df[SET_INVEST_PER_CAPITA + "{}".format(year)] > min_investment) &
                                (self.df[SET_ELEC_FINAL_CODE + "{}".format(
                                    year - time_step)] == 0), SET_LIMIT + "{}".format(year)] = 0

                    elecrate = self.df.loc[
                                   self.df[SET_LIMIT + "{}".format(year)] == 1, SET_POP + "{}".format(year)].sum() / \
                        self.df[SET_POP + "{}".format(year)].sum()
                else:
                    print(
                        "The electrification target set is quite low and has been reached by "
                        "grid densification in already electrified areas")
                    self.df.loc[
                        (self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 1), SET_LIMIT + "{}".format(
                            year)] = 1
                    self.df.loc[
                        (self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 0), SET_LIMIT + "{}".format(
                            year)] = 0

                    elecrate = self.df.loc[
                                   self.df[SET_LIMIT + "{}".format(year)] == 1, SET_POP + "{}".format(year)].sum() / \
                        self.df[SET_POP + "{}".format(year)].sum()

            elif choice == 2:
                # Prioritize grid densification/intensification (1 or 2 km). Then lowest investment per capita
                self.df[SET_LIMIT + "{}".format(year)] = 0
                elecrate = 0
                min_investment = 0
                extension = 0
                iter_limit_4 = 0
                iter_limit_5 = 0
                self.df[SET_INVEST_PER_CAPITA + "{}".format(year)] = \
                    self.df[SET_INVESTMENT_COST + "{}".format(year)] / self.df[SET_NEW_CONNECTIONS + "{}".format(year)]
                step_size = self.df[SET_INVEST_PER_CAPITA + "{}".format(year)].quantile(q=0.95) / 100
                densification_pop = sum(self.df[self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 1][
                                            SET_POP + "{}".format(year)])
                intensification_pop = sum(self.df[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 0) &
                                                  (self.df[SET_MV_DIST_PLANNED] < auto_densification)][
                                              SET_POP + "{}".format(year)])

                if (densification_pop + intensification_pop) / self.df[SET_POP + "{}".format(year)].sum() < eleclimit:
                    eleclimit -= densification_pop / self.df[SET_POP + "{}".format(year)].sum()
                    eleclimit -= intensification_pop / self.df[SET_POP + "{}".format(year)].sum()

                    while abs(elecrate - eleclimit) > 0.01:
                        extension = 1

                        elecrate = sum(
                            self.df[(self.df[SET_INVEST_PER_CAPITA + "{}".format(year)] < min_investment) &
                                    (self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 0) &
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
                    self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 1),
                                SET_LIMIT + "{}".format(year)] = 1

                    self.df.loc[self.df[SET_MV_DIST_PLANNED] < auto_densification, SET_LIMIT + "{}".format(year)] = 1

                    if extension == 1:
                        self.df.loc[(self.df[SET_INVEST_PER_CAPITA + "{}".format(year)] <= min_investment),
                                    SET_LIMIT + "{}".format(year)] = 1

                else:
                    print("The electrification target set is quite low,"
                          " and has been reached by grid densification/intensification")
                    self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 1),
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
                if sum(self.df[self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 1][
                           SET_POP + "{}".format(year)]) / \
                        self.df[SET_POP + "{}".format(year)].sum() < eleclimit:
                    eleclimit -= sum(self.df[self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 1][
                                         SET_POP + "{}".format(year)]) / \
                                 self.df[SET_POP + "{}".format(year)].sum()

                    while abs(elecrate - eleclimit) > 0.01:
                        elecrate = sum(self.df[(self.df[SET_INVEST_PER_CAPITA + "{}".format(year)] < min_investment) &
                                               (self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 0) &
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
                        (self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 1), SET_LIMIT + "{}".format(
                            year)] = 1

                    self.df.loc[(self.df[SET_INVEST_PER_CAPITA + "{}".format(year)] <= min_investment) &
                                (self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 0) &
                                (self.df[SET_TRAVEL_HOURS] <= min_dist_to_cities), SET_LIMIT + "{}".format(year)] = 1

                    self.df.loc[(self.df[SET_INVEST_PER_CAPITA + "{}".format(year)] <= min_investment) &
                                (self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 0) &
                                (self.df[SET_TRAVEL_HOURS] > min_dist_to_cities), SET_LIMIT + "{}".format(year)] = 0

                    self.df.loc[(self.df[SET_INVEST_PER_CAPITA + "{}".format(year)] > min_investment) &
                                (self.df[SET_ELEC_FINAL_CODE + "{}".format(
                                    year - time_step)] == 0), SET_LIMIT + "{}".format(year)] = 0

                else:
                    print("The electrification target set is quite low,"
                          " and has been reached by grid densification in already electrified areas")
                    self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 1),
                                SET_LIMIT + "{}".format(year)] = 1
                    self.df.loc[(self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 0),
                                SET_LIMIT + "{}".format(year)] = 0

                elecrate = self.df.loc[self.df[SET_LIMIT + "{}".format(year)] == 1,
                                       SET_POP + "{}".format(year)].sum() / self.df[SET_POP + "{}".format(year)].sum()

            elif choice == 4:
                self.df[SET_LIMIT + "{}".format(year)] = 0

                self.df.loc[
                    (self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 1), SET_LIMIT + "{}".format(
                        year)] = 1
                self.df.loc[self.df[SET_MV_DIST_PLANNED] < auto_densification, SET_LIMIT + "{}".format(year)] = 1
                elecrate = self.df.loc[self.df[SET_LIMIT + "{}".format(year)] == 1,
                                       SET_POP + "{}".format(year)].sum() / self.df[SET_POP + "{}".format(year)].sum()

            elif choice == 5:
                # Prioritize grid densification first, then lowest investment per capita combined with travel time
                elecrate = 0
                min_investment = 0
                min_dist_to_cities = max(self.df[SET_TRAVEL_HOURS])

                iter_limit_3 = 0
                iter_limit_4 = 0
                self.df[SET_INVEST_PER_CAPITA + "{}".format(year)] = \
                    self.df[SET_INVESTMENT_COST + "{}".format(year)] / self.df[SET_NEW_CONNECTIONS + "{}".format(year)]
                step_size = self.df[SET_INVEST_PER_CAPITA + "{}".format(year)].quantile(q=0.95) / 20
                travel_time_step = self.df[SET_TRAVEL_HOURS].quantile(q=1) / 100
                if sum(self.df[self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 1][
                           SET_POP + "{}".format(year)]) / \
                        self.df[SET_POP + "{}".format(year)].sum() < eleclimit:
                    eleclimit -= sum(self.df[self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 1][
                                         SET_POP + "{}".format(year)]) / \
                                 self.df[SET_POP + "{}".format(year)].sum()

                    while abs(elecrate - eleclimit) > 0.01:
                        elecrate = sum(self.df[(self.df[SET_INVEST_PER_CAPITA + "{}".format(year)] < min_investment) &
                                               (self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 0) &
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
                        (self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 1), SET_LIMIT + "{}".format(
                            year)] = 1

                    self.df.loc[(self.df[SET_INVEST_PER_CAPITA + "{}".format(year)] <= min_investment) &
                                (self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 0) &
                                (self.df[SET_TRAVEL_HOURS] <= min_dist_to_cities), SET_LIMIT + "{}".format(year)] = 1

                    self.df.loc[(self.df[SET_INVEST_PER_CAPITA + "{}".format(year)] <= min_investment) &
                                (self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 0) &
                                (self.df[SET_TRAVEL_HOURS] > min_dist_to_cities), SET_LIMIT + "{}".format(year)] = 0

                    self.df.loc[(self.df[SET_INVEST_PER_CAPITA + "{}".format(year)] > min_investment) &
                                (self.df[SET_ELEC_FINAL_CODE + "{}".format(
                                    year - time_step)] == 0), SET_LIMIT + "{}".format(year)] = 0

                    elecrate = self.df.loc[
                                   self.df[SET_LIMIT + "{}".format(year)] == 1, SET_POP + "{}".format(year)].sum() / \
                        self.df[SET_POP + "{}".format(year)].sum()
                else:
                    print(
                        "The electrification target set is quite low and has been reached by "
                        "grid densification in already electrified areas")
                    self.df.loc[
                        (self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 1), SET_LIMIT + "{}".format(
                            year)] = 1
                    self.df.loc[
                        (self.df[SET_ELEC_FINAL_CODE + "{}".format(year - time_step)] == 0), SET_LIMIT + "{}".format(
                            year)] = 0

                    elecrate = self.df.loc[
                                   self.df[SET_LIMIT + "{}".format(year)] == 1, SET_POP + "{}".format(year)].sum() / \
                        self.df[SET_POP + "{}".format(year)].sum()

        print("The electrification rate achieved in {} is {:.1f} %".format(year, (elecrate - elec_limit_origin) * 100))

    def final_decision(self, year):
        """" ... """

        logging.info('Determine final electrification decision')

        # Defining what is electrified in a given year by the grid after prioritization process has finished
        self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] = 0
        self.df.loc[
            (self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 1), SET_ELEC_FINAL_CODE + "{}".format(year)] = 1
        self.df.loc[
            (self.df[SET_LIMIT + "{}".format(year)] == 1) & (
                        self.df[SET_MIN_OVERALL_CODE + "{}".format(year)] == 1), SET_ELEC_FINAL_CODE + "{}".format(
                year)] = 1
        # Define what is electrified in a given year by off-grid after prioritization process has finished
        self.df[SET_ELEC_FINAL_OFFGRID + "{}".format(year)] = 0
        self.df.loc[(self.df[SET_ELEC_FUTURE_OFFGRID + "{}".format(year)] == 1) & (
                self.df[SET_MIN_OVERALL_CODE + "{}".format(year)] != 1), SET_ELEC_FINAL_OFFGRID + "{}".format(
            year)] = 1
        self.df.loc[(self.df[SET_LIMIT + "{}".format(year)] == 1) & (
                self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 0), SET_ELEC_FINAL_OFFGRID + "{}".format(
            year)] = 1
        self.df.loc[
            (self.df[SET_LIMIT + "{}".format(year)] == 1) & (
                        self.df[SET_MIN_OVERALL_CODE + "{}".format(year)] == 0), SET_ELEC_FINAL_OFFGRID + "{}".format(
                year)] = 1

        #
        self.df.loc[
            (self.df[SET_LIMIT + "{}".format(year)] == 1) & (self.df[SET_ELEC_FINAL_CODE + "{}".format(year)] == 1),
            SET_ELEC_FINAL_CODE + "{}".format(year)] = 1

        self.df.loc[
            (self.df[SET_LIMIT + "{}".format(year)] == 1) & (self.df[SET_ELEC_FINAL_OFFGRID + "{}".format(year)] == 1),
            SET_ELEC_FINAL_CODE + "{}".format(year)] = self.df[SET_MIN_OFFGRID_CODE + "{}".format(year)]

        self.df.loc[(self.df[SET_LIMIT + "{}".format(year)] == 0),
                    SET_ELEC_FINAL_CODE + "{}".format(year)] = 99

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
