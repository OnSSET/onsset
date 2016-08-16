import os

# files and folders
FF_TABLES = 'db'
FF_LCOES = os.path.join(FF_TABLES, 'lcoes')
FF_SPECS = os.path.join(FF_TABLES, 'specs.xlsx')
FF_SETTLEMENTS = os.path.join(FF_TABLES, 'settlements.csv')
FF_GRID_LCOES = lambda x: os.path.join(FF_LCOES, str(x), 'grid_lcoes_{}.csv'.format(x))
FF_GRID_CAP = lambda x: os.path.join(FF_LCOES, str(x), 'grid_cap_{}.csv'.format(x))
FF_TECH_LCOES = lambda x: os.path.join(FF_LCOES, str(x), 'tech_lcoes_{}.csv'.format(x))
FF_TECH_CAP = lambda x: os.path.join(FF_LCOES, str(x), 'tech_cap_{}.csv'.format(x))
FF_NUM_PEOPLE = lambda x: os.path.join(FF_LCOES, str(x), 'num_people_{}.csv'.format(x))

# general
ELEC_DISTS = list(range(1, 10)) + list(range(10, 20, 2)) + list(range(20,51,5))  # distances in km to test elec
MAX_GRID_EXTEND = ELEC_DISTS[-1]  # in km, never extend the grid further than this
NUM_PEOPLE_PER_HH = 5
LHV_DIESEL = 9.9445485  # (kWh/l) lower heating value
HOURS_PER_YEAR = 8760
EXISTING_GRID_COST_RATIO = 0.1 # factor to multiply by existing grid length when calculating elec status
PV_LOW = 1500  # kWh/m2/year
PV_HIGH = 2500  # kWh/m2/year
WIND_LOW = 0.2  # capacity factor
WIND_MID = 0.3  # capacity factor
WIND_HIGH = 0.4  # capacity factor

# settlements file
SET_COUNTRY = 'Country'  # This cannot be changed, lots of code will break
SET_X = 'X'  # Coordinate in kilometres
SET_Y = 'Y'  # Coordinate in kilometres
SET_POP = 'Pop'  # Population in people per point (equally, people per km2)
SET_POP_CALIB = 'Pop2015Act'  # Calibrated population to reference year, same units
SET_POP_FUTURE = 'Pop2030'  # Project future population, same units
SET_GRID_DIST_CURRENT = 'GridDistCurrent'  # Distance in km from current grid
SET_GRID_DIST_PLANNED = 'GridDistPlan'  # Distance in km from current and future grid
SET_ROAD_DIST = 'RoadDist'  # Distance in km from road network
SET_NIGHT_LIGHTS = 'NightLights'  # Intensity of night time lights (from NASA), range 0 - 63
SET_TRAVEL_HOURS = 'TravelHours'  # Travel time to large city in hours
SET_GHI = 'GHI'  # Global horizontal irradiance in kWh/m2/day
SET_WINDCF = 'WindCF'  # Wind capacity factor as percentage (range 0 - 1)
SET_HYDRO = 'Hydropower'  # Hydropower potential in kW
SET_HYDRO_DIST = 'HydropowerDist'  # Distance to hydropower site in km
SET_URBAN = 'IsUrban'  # Whether the site is urban (0 or 1)
SET_ELEC_PREFIX = 'Elec'
START_YEAR = 2015
END_YEAR = 2030
SET_ELEC_CURRENT = SET_ELEC_PREFIX + str(START_YEAR)  # If the site is currently electrified (0 or 1)
SET_ELEC_FUTURE = SET_ELEC_PREFIX + str(END_YEAR)  # If the site has the potential to be 'easily' electrified in future
SET_ELEC_STEPS = [SET_ELEC_PREFIX + str(x) for x in ELEC_DISTS]  # Electrification potential at each distance

# results inserted into settlements file
RES_MIN_GRID_DIST = 'MinGridDist'  # The minimum distance to an electrified cell
RES_LCOE_GRID = 'lcoe_grid'  # All lcoes in USD/kWh
RES_LCOE_SA_PV = 'lcoe_sa_pv'
RES_LCOE_SA_DIESEL = 'lcoe_sa_diesel'
RES_LCOE_MG_WIND = 'lcoe_mg_wind'
RES_LCOE_MG_DIESEL = 'lcoe_mg_diesel'
RES_LCOE_MG_PV = 'lcoe_mg_pv'
RES_LCOE_MG_HYDRO = 'lcoe_mg_hydro'
RES_MINIMUM_TECH = 'minimum_tech'  # The technology with lowest lcoe
RES_MINIMUM_LCOE = 'minimum_lcoe'  # The lcoe value
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
SPE_DIESEL_PRICE_LOW = 'DieselPriceLow'  # Diesel price in USD/litre
SPE_DIESEL_PRICE_HIGH = 'DieselPriceHigh'  # Same, with a high forecast scenario
SPE_GRID_PRICE = 'GridPrice'  # Grid price of electricity in USD/kWh
SPE_GRID_LOSSES = 'GridLosses'  # As a ratio (0 - 1)
SPE_BASE_TO_PEAK = 'BaseToPeak'  # As a ratio (0 - 1)
SPE_ELEC = 'ElecActual'  # Actual current percentage electrified population (0 - 1)
SPE_ELEC_MODELLED = 'ElecModelled'  # The modelled version after calibration (for comparison)
SPE_MIN_NIGHT_LIGHTS = 'MinNightLights'
SPE_MAX_GRID_DIST = 'MaxGridDist'
SPE_MAX_ROAD_DIST = 'MaxRoadDist'
SPE_POP_CUTOFF1 = 'PopCutOffRoundOne'
SPE_POP_CUTOFF2 = 'PopCutOffRoundTwo'
SPE_GRID_CUTOFF2 = 'GridRoundTwo'
SPE_ROAD_CUTOFF2 = 'RoadRoundTwo'

# tech lcoes
GRID = 'grid'
MG_HYDRO = 'mg_hydro'
MG_PV_LOW = 'mg_pv_low'
MG_PV_HIGH = 'mg_pv_high'
MG_WIND_LOW = 'mg_wind_low'
MG_WIND_MID = 'mg_wind_mid'
MG_WIND_HIGH = 'mg_wind_high'
MG_DIESEL = 'mg_diesel'
SA_DIESEL = 'sa_diesel'
SA_PV_LOW = 'sa_pv_low'
SA_PV_HIGH = 'sa_pv_high'
