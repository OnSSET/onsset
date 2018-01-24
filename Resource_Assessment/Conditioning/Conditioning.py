
# coding: utf-8

# In[136]:

import numpy as np
import pandas as pd
import os

# Users input
input_file = "Madagascar_10kmSettlements"
country = "Madagascar"

# Read the csv into a pandas dataframe
df = pd.read_csv("{x}.csv".format(x=input_file))


# In[138]:

# Delete the pointid column
del df["pointid"]
del df["Unnamed: 0"]

# Rename all columns as appropriate
df.rename(columns={"Pop":"Pop", "X":"X", "Y":"Y", 
                   "SolarRestr":"SolarRestriction", 
                   "TravelHour":"TravelHours", 
                   "NightLight":"NightLights", 
                   "Elevation":"Elevation", 
                   "Slope":"Slope", 
                   "LandCover":"LandCover", 
                   "GridDistCu":"GridDistCurrent", 
                   "GridDistPl":"GridDistPlan", 
                   "Substation":"SubstationDist", 
                   "RoadDist":"RoadDist", 
                   "Hydropower":"HydropowerDist", 
                   "Hydropow_1":"Hydropower", 
                   "RASTERVALU":"WindVel", 
                   "RASTERVA_1":"GHI", 
                   "COUNTRY":"Country"}, inplace =True)

#Assure that everything is in the right format
df["Country"] = country
df["X"] = df["X"]*1000
df["Y"] = df["Y"]*1000
df["Pop"] = pd.to_numeric(df["Pop"], errors='coerce')
df["SolarRestriction"] = pd.to_numeric(df["SolarRestriction"], errors='coerce')
df["TravelHours"] = pd.to_numeric(df["TravelHours"], errors='coerce')
df["NightLights"] = pd.to_numeric(df["NightLights"], errors='coerce')
df["Elevation"] = pd.to_numeric(df["Elevation"], errors='coerce')
df["Slope"] = pd.to_numeric(df["Slope"], errors='coerce')
df["LandCover"] = pd.to_numeric(df["LandCover"], errors='coerce')
df["GridDistCurrent"] = pd.to_numeric(df["GridDistCurrent"], errors='coerce')
df["GridDistPlan"] = pd.to_numeric(df["GridDistPlan"], errors='coerce')
df["SubstationDist"] = pd.to_numeric(df["SubstationDist"], errors='coerce')
df["RoadDist"] = pd.to_numeric(df["RoadDist"], errors='coerce')
df["HydropowerDist"] = pd.to_numeric(df["HydropowerDist"], errors='coerce')
df["Hydropower"] = pd.to_numeric(df["Hydropower"], errors='coerce')

# Places with GHI=0 are given the average value over the country
df["GHI"] = pd.to_numeric(df["GHI"], errors='coerce')
df.loc[(df["GHI"] == 0), "GHI"] = df["GHI"].mean()

# Places with Wind Speed = -9999 are given the most frequent value in the country
df["WindVel"] = pd.to_numeric(df["WindVel"], errors='coerce')
df.loc[(df["WindVel"] == -9999), "WindVel"] = max(df['WindVel'].value_counts().idxmax(),0)

#Returning the conditioned csv
df.to_csv("{c}.csv".format(c=country), index=False)

