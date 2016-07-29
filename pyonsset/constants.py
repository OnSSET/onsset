import os

# files and folders
FF_TABLES = 'tables'
FF_LCOES = os.path.join(FF_TABLES, 'lcoes')
FF_SPECS = os.path.join(FF_TABLES, 'specs.xlsx')
FF_SETTLEMENTS = os.path.join(FF_TABLES, 'settlements.csv')
def FF_GRID_LCOES(scenario):
    return os.path.join(FF_LCOES, str(scenario), 'grid_lcoes_{}.csv'.format(scenario))
def FF_GRID_CAP(scenario):
    return os.path.join(FF_LCOES, str(scenario), 'grid_cap_{}.csv'.format(scenario))
def FF_TECH_LCOES(scenario):
    return os.path.join(FF_LCOES, str(scenario), 'tech_lcoes_{}.csv'.format(scenario))
def FF_TECH_CAP(scenario):
    return os.path.join(FF_LCOES, str(scenario), 'tech_cap_{}.csv'.format(scenario))
def FF_NUM_PEOPLE(scenario):
    return os.path.join(FF_LCOES, str(scenario), 'num_people_{}.csv'.format(scenario))

# general
ELEC_DISTANCES = [5*x for x in range(1,11)]
MAX_GRID_EXTEND = ELEC_DISTANCES[-1]
NUM_PEOPLE_PER_HH = 5.0

# settlements file
SET_COUNTRY = 'Country' # give eplanation of each variable
SET_X = 'X'
SET_Y = 'Y'
SET_POP = 'Pop'
SET_POP_CALIB = 'Pop2015Act'
SET_POP_FUTURE = 'Pop2030'
SET_GRID_DIST_CURRENT = 'GridDistCurrent'
SET_GRID_DIST_PLANNED = 'GridDistPlan'
SET_ROAD_DIST = 'RoadDist'
SET_NIGHT_LIGHTS = 'NightLights'
SET_TRAVEL_HOURS = 'TravelHours'
SET_GHI = 'GHI'
SET_WINDCF = 'WindCF'
SET_HYDRO = 'Hydropower'
SET_HYDRO_DIST = 'HydropwoerDist'
SET_URBAN = 'IsUrban'
SET_ELEC_PREFIX = 'Elec'
SET_ELEC_CURRENT = SET_ELEC_PREFIX + '2015'
SET_ELEC_FUTURE = SET_ELEC_PREFIX + '2030'
SET_ELEC_STEPS = [SET_ELEC_PREFIX + str(x) for x in ELEC_DISTANCES]

# results inserted into settlements file
RES_MIN_GRID_DIST = 'MinGridDist'
RES_LCOE_GRID = 'lcoe_grid'
RES_LCOE_SA_PV = 'lcoe_sa_pv'
RES_LCOE_SA_DIESEL = 'lcoe_sa_diesel'
RES_LCOE_MG_WIND = 'lcoe_mg_wind'
RES_LCOE_MG_DIESEL = 'lcoe_mg_diesel'
RES_LCOE_MG_PV = 'lcoe_mg_pv'
RES_LCOE_MG_HYDRO = 'lcoe_mg_hydro'
RES_MINIMUM_TECH = 'minimum_tech'
RES_MINIMUM_LCOE = 'minimum_lcoe'
RES_MINIMUM_CATEGORY = 'minimum_category'
RES_NEW_CAPACITY = 'NewCapacity'
RES_NEW_CONNECTIONS = 'NewConnections'
RES_INVESTMENT_COST = 'InvestmentCost'

# specs file
SPE_COUNTRY = 'Country'
SPE_POP = 'Pop2015TotActual'
SPE_URBAN = 'UrbanRatio'
SPE_URBAN_MODELLED = 'UrbanRatioModelled'
SPE_URBAN_CUTOFF = 'UrbanCutOff'
SPE_URBAN_GROWTH = 'UrbanGrowth'
SPE_RURAL_GROWTH = 'RuralGrowth'
SPE_DIESEL_PRICE_LOW = 'DieselPriceLow'
SPE_DIESEL_PRICE_HIGH = 'DieselPriceHigh'
SPE_GRID_PRICE = 'GridPrice'
SPE_GRID_LOSSES = 'GridLosses'
SPE_BASE_TO_PEAK = 'BaseToPeak'
SPE_ELEC = 'ElecActual'
SPE_ELEC_MODELLED = 'ElecModelled'
SPE_MIN_NIGHT_LIGHTS = 'MinNightLights'
SPE_MAX_GRID_DIST = 'MaxGridDist'
SPE_MAX_ROAD_DIST = 'MaxRoadDist'
SPE_POP_CUTOFF1 = 'PopCutOffRoundOne'
SPE_POP_CUTOFF2 = 'PopCutOffRoundTwo'
SPE_GRID_CUTOFF2 = 'GridRoundTwo'
SPE_ROAD_CUTOFF2 = 'RoadRoundTwo'

# tech lcoes
MG_HYDRO = 'mg_hydro'
MG_PV_LOW = 'mg_pv1750'
MG_PV_HIGH = 'mg_pv2250'
MG_WIND_LOW = 'mg_wind0.2'
MG_WIND_MID = 'mg_wind0.3'
MG_WIND_HIGH = 'mg_wind0.4'
MG_DIESEL = 'mg_diesel'
SA_DIESEL_ = 'sa_diesel'
SA_PV_LOW = 'sa_pv1750'
SA_PV_HIGH = 'sa_pv2250'