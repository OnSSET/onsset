"""Columns in the specs file must match these exactly
"""
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
SPE_ELEC_URBAN = 'UrbanElecRatio'  # Actual electrification for urban areas
SPE_ELEC_RURAL = 'RuralElecRatio'  # Actual electrification for rural areas
SPE_MIN_NIGHT_LIGHTS = 'MinNightLights'
SPE_MAX_GRID_EXTENSION_DIST = 'MaxGridExtensionDist'
SPE_MAX_ROAD_DIST = 'MaxRoadDist'
SPE_POP_CUTOFF1 = 'PopCutOffRoundOne'
SPE_POP_CUTOFF2 = 'PopCutOffRoundTwo'
SPE_ELEC_LIMIT = "ElecLimit"
SPE_INVEST_LIMIT = "InvestmentLimit"
SPE_DIST_TO_TRANS = "DistToTrans"
SPE_COST_NON_SUPLIED_ENERGY = 'CNSE' # in USD cents of kWh
SPE_START_YEAR = "StartYear"
SPE_END_YEAR = "EndYear"
SPE_TIMESTEP = "TimeStep"

# =============================================================================
# CLIMATE DATA SHEET CONSTANTS
# =============================================================================
# These constants define column names for the 'ClimateData' sheet in specs file.
# The sheet should contain configuration parameters for climate risk calculations.

# Heatwave parameters
SPE_CLIM_HW_THRESHOLD = 'HeatwaveThresholdC'  # Temperature threshold for heatwave day (°C), default 32.0
SPE_CLIM_HW_DURATION = 'HeatwaveDurationDays'  # Minimum consecutive days for heatwave event, default 3
SPE_CLIM_HW_TEMP_COL = 'TemperatureColumnName'  # Column name in climate CSV for temperature, default 't2m_max_C'

# Heatwave intensity categories (3-day rolling mean thresholds)
SPE_CLIM_HW_CAT1_LOW = 'HeatwaveCat1Low'  # Lower bound for category 1, default 32.0
SPE_CLIM_HW_CAT1_HIGH = 'HeatwaveCat1High'  # Upper bound for category 1, default 35.0
SPE_CLIM_HW_CAT2_LOW = 'HeatwaveCat2Low'  # Lower bound for category 2, default 35.0
SPE_CLIM_HW_CAT2_HIGH = 'HeatwaveCat2High'  # Upper bound for category 2, default 38.0
SPE_CLIM_HW_CAT3_LOW = 'HeatwaveCat3Low'  # Lower bound for category 3, default 38.0
SPE_CLIM_HW_CAT3_HIGH = 'HeatwaveCat3High'  # Upper bound for category 3, default 42.0
SPE_CLIM_HW_CAT4_LOW = 'HeatwaveCat4Low'  # Lower bound for category 4 (extreme), default 42.0

# SPI (Standardized Precipitation Index) drought parameters
SPE_CLIM_SPI_SCALE = 'SPIScale'  # Accumulation period in months (e.g., 3 for SPI-3), default 3
SPE_CLIM_SPI_BASELINE_START = 'SPIBaselineStartYear'  # Start year for gamma distribution fitting, default 1950
SPE_CLIM_SPI_BASELINE_END = 'SPIBaselineEndYear'  # End year for gamma distribution fitting, default 2000
SPE_CLIM_SPI_PRECIP_COL = 'PrecipitationColumnName'  # Column name in climate CSV for precipitation, default 'tp_mm_month'

# SPI drought intensity thresholds
SPE_CLIM_SPI_DROUGHT_THRESHOLD = 'SPIDroughtThreshold'  # SPI value below which is drought, default -1.0
SPE_CLIM_SPI_MILD_THRESHOLD = 'SPIMildThreshold'  # Mild drought threshold, default -1.5
SPE_CLIM_SPI_MODERATE_THRESHOLD = 'SPIModerateThreshold'  # Moderate drought threshold, default -2.0
SPE_CLIM_SPI_SEVERE_THRESHOLD = 'SPISevereThreshold'  # Severe drought threshold, default -2.5

# Climate data common parameters
SPE_CLIM_LAT_COL = 'LatitudeColumnName'  # Column name for latitude, default 'latitude'
SPE_CLIM_LON_COL = 'LongitudeColumnName'  # Column name for longitude, default 'longitude'
SPE_CLIM_DATE_COL = 'DateColumnName'  # Column name for date/timestamp, default 'date'
SPE_CLIM_ADMIN3_ID_COL = 'Admin3IDColumn'  # Column in admin3 shapefile for ID, default 'GID_3'
SPE_CLIM_ADMIN3_NAME_COL = 'Admin3NameColumn'  # Column in admin3 shapefile for name, default 'NAME_3'

# Risk weighting
SPE_CLIM_HW_WEIGHT = 'HeatwaveRiskWeight'  # Weight for heatwave in compound risk, default 0.5
SPE_CLIM_DROUGHT_WEIGHT = 'DroughtRiskWeight'  # Weight for drought in compound risk, default 0.5
