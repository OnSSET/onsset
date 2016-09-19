# files and folders
FF_SPECS = 'db/specs.xlsx'
FF_SETTLEMENTS = 'db/settlements.csv'

# general
NUM_PEOPLE_DISTS = [5, 10]
LHV_DIESEL = 9.9445485  # (kWh/l) lower heating value
HOURS_PER_YEAR = 8760
PV_LOW = 1500  # kWh/m2/year
PV_MID = 2000
PV_HIGH = 2900  # kWh/m2/year
WIND_LOW = 0.2  # capacity factor
WIND_MID = 0.3  # capacity factor
WIND_HIGH = 0.4  # capacity factor
WIND_EXTRA_HIGH = 0.7  # capacity factor

# settlements file
SET_COUNTRY = 'Country'  # This cannot be changed, lots of code will break
SET_X = 'X'  # Coordinate in kilometres
SET_Y = 'Y'  # Coordinate in kilometres
SET_X_DEG = 'X_deg'
SET_Y_DEG = 'Y_deg'
SET_POP = 'Pop'  # Population in people per point (equally, people per km2)
SET_POP_CALIB = 'Pop2015Act'  # Calibrated population to reference year, same units
SET_POP_FUTURE = 'Pop2030'  # Project future population, same units
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
SET_SUBSTATION_DIST = 'SubstationDist'
SET_ELEVATION = 'Elevation'
SET_SLOPE = 'Slope'
SET_LAND_COVER = 'LandCover'
SET_SOLAR_RESTRICTION = 'SolarRestriction'
SET_ROAD_DIST_CLASSIFIED = 'RoadDistClassified'
SET_SUBSTATION_DIST_CLASSIFIED = 'SubstationDistClassified'
SET_ELEVATION_CLASSIFIED = 'ElevationClassified'
SET_SLOPE_CLASSIFIED = 'SlopeClassified'
SET_LAND_COVER_CLASSIFIED = 'LandCoverClassified'
SET_COMBINED_CLASSIFICATION = 'GridClassification'
SET_GRID_PENALTY = 'GridPenalty'
SET_URBAN = 'IsUrban'  # Whether the site is urban (0 or 1)
SET_ELEC_PREFIX = 'Elec'
START_YEAR = 2015
END_YEAR = 2030
SET_ELEC_CURRENT = SET_ELEC_PREFIX + str(START_YEAR)  # If the site is currently electrified (0 or 1)
SET_ELEC_FUTURE = SET_ELEC_PREFIX + str(END_YEAR)  # If the site has the potential to be 'easily' electrified in future

# results inserted into settlements file
RES_MIN_GRID_DIST = 'MinGridDist'
RES_LCOE_GRID = 'lcoe_grid'  # All lcoes in USD/kWh
RES_LCOE_SA_PV = 'lcoe_sa_pv'
RES_LCOE_SA_DIESEL = 'lcoe_sa_diesel'
RES_LCOE_MG_WIND = 'lcoe_mg_wind'
RES_LCOE_MG_DIESEL = 'lcoe_mg_diesel'
RES_LCOE_MG_PV = 'lcoe_mg_pv'
RES_LCOE_MG_HYDRO = 'lcoe_mg_hydro'
RES_MINIMUM_TECH = 'minimum_tech'  # The technology with lowest lcoe (excluding grid)
RES_MINIMUM_OVERALL = 'minimum_overall'
RES_MINIMUM_TECH_LCOE = 'minimum_tech_lcoe'  # The lcoe value
RES_MINIMUM_OVERALL_LCOE = 'minimum_overall_lcoe'
RES_MINIMUM_OVERALL_CODE = 'minimum_overall_code'
RES_MINIMUM_CATEGORY = 'minimum_category'  # The category with minimum lcoe (grid, minigrid or standalone)
RES_NEW_CAPACITY = 'NewCapacity'  # Capacity in kW
RES_NEW_CONNECTIONS = 'NewConnections'  # Number of new people with electricity connections
RES_INVESTMENT_COST = 'InvestmentCost'  # The investment cost in USD

# summary results
SUM_SPLIT_PREFIX = 'split_'
SUM_CAPACITY_PREFIX = 'capacity_'
SUM_INVESTMENT_PREFIX = 'investment_'

# specs file
SPE_COUNTRY = 'Country'
SPE_POP = 'Pop2015'  # The actual population in the base year
SPE_URBAN = 'UrbanRatio2015'  # The ratio of urban population (range 0 - 1) in base year
SPE_POP_FUTURE = 'Pop2030'
SPE_URBAN_FUTURE = 'UrbanRatio2030'
SPE_URBAN_MODELLED = 'UrbanRatioModelled'  # The urban ratio in the model after calibration (for comparison)
SPE_URBAN_CUTOFF = 'UrbanCutOff'  # The urban cutoff population calirated by the model, in people per km2
SPE_URBAN_GROWTH = 'UrbanGrowth'  # The urban growth rate as a simple multplier (urban pop future / urban pop present)
SPE_RURAL_GROWTH = 'RuralGrowth'  # Same as for urban
SPE_NUM_PEOPLE_PER_HH = 'NumPeoplePerHH'
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
SPE_MIN_NIGHT_LIGHTS = 'MinNightLights'
SPE_MAX_GRID_EXTENSION_DIST = 'MaxGridExtensionDist'
SPE_MAX_ROAD_DIST = 'MaxRoadDist'
SPE_POP_CUTOFF1 = 'PopCutOffRoundOne'
SPE_POP_CUTOFF2 = 'PopCutOffRoundTwo'

# tech lcoes
GRID = 'grid'
MG_HYDRO = 'mg_hydro'
MG_PV_LOW = 'mg_pv_low'
MG_PV_MID = 'mg_pv_mid'
MG_PV_HIGH = 'mg_pv_high'
MG_WIND_LOW = 'mg_wind_low'
MG_WIND_MID = 'mg_wind_mid'
MG_WIND_HIGH = 'mg_wind_high'
MG_WIND_EXTRA_HIGH = 'mg_wind_extra_high'
MG_DIESEL = 'mg_diesel'
SA_DIESEL = 'sa_diesel'
SA_PV_LOW = 'sa_pv_low'
SA_PV_MID = 'sa_pv_mid'
SA_PV_HIGH = 'sa_pv_high'
