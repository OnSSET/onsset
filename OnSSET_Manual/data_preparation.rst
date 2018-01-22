GIS data preparation
========================

GIS preparation
******************



Common Data types (models)
---------------------------

**Spatial Data:** Describe the absolute and relative location of geographic features.

    * Vectors

        - Arcs (Polylines): Line segments forming individual linear features
        - Polygons: Areas enclosed by arcs
        - Points: Single coordinate pairs

        .. image:: img/vector.png
            :width: 200px
            :height: 120px
            :align: center


    * Rasters

        - Grid-Cells: single column/row positions
        - Cell size: Resolution or else the accuracy of the data

        .. image:: img/raster.png
            :width: 200px
            :height: 120px
            :align: center

**Attribute data:** Describe characteristics of the spatial features. These characteristics can be quantitative and/or qualitative in nature. Attribute data is often referred to as tabular data.

OnSSET dataset preparation
---------------------------

There are five steps that need to be undertaken to process the GIS data so that it can be used for an OnSSET analysis.

**Step 1.** Secure that you have all the 16 datasets required as layers onto your map (the geographic coordinate systems should be WGS84).

**Step 2.** Project every single layer using the WGS 1984 World Mercator system.

**Step 3.** Create and populate a geo-database with all the layers needed and the correct naming convention.

**Step 4.** Use GIS functions and tools to assign a number of important attributes to every single settlement
(please note the spatial resolution at the starting point).

**Step 5.** Save the data to a csv file with naming conventions matching the Python code

There are two options to complete these steps. Either they are performed using a set of Python commands provided by KTH dESA
or they are performed manually in the GIS software.

Using the GIS Commands for processing file provided by KTH dESA.
-------------------------------------------------------------------

    **Example:**

.. code-block:: python

    import logging
    import arcpy
    logging.basicConfig(format='%(asctime)s\t\t%(message)s', level=logging.DEBUG)
    #
    # Here you should define the path of the geodatabase containing all the layers
    #
    path=r"C:\...\...\<geodatabase name>.gdb"
    path1=r"C:\Users\...\Assistingfolder"
    outpath = r"C:\...\OnSSET"
    #
    arcpy.env.workspace = path
    arcpy.env.overwriteOutput = True
    arcpy.env.addOutputsToMap = False
    arcpy.CheckOutExtension("Spatial")
    #
    # The variables needed
    #
    SET_COUNTRY = 'Country'  # This cannot be changed, lots of code will break
    SET_X = 'X'  # Coordinate in kilometres
    SET_Y = 'Y'  # Coordinate in kilometres
    SET_X_DEG = 'X_deg'  # Coordinates in degrees
    SET_Y_DEG = 'Y_deg'
    SET_POP = 'Pop'  # Population in people per point (equally, people per 100km2)
    SET_POP_CALIB = 'PopStartCalibrated'  # Calibrated population to reference year, same units
    SET_POP_FUTURE = 'PopFuture'  # Project future population, same units
    SET_GRID_DIST_CURRENT = 'GridDistCurrent'  # Distance in km from current grid
    SET_GRID_DIST_PLANNED = 'GridDistPlan'  # Distance in km from current and future grid
    SET_ROAD_DIST = 'RoadDist'  # Distance in km from road network
    SET_NIGHT_LIGHTS = 'NightLights'  # Intensity of night time lights (from NASA), range 0 - 63
    SET_TRAVEL_HOURS = 'TravelHours'  # Travel time to large city in hours
    SET_GHI = 'GHI'  # Global horizontal irradiance in kWh/m2/day
    SET_WINDVEL = 'WindVel'  # Wind velocity in m/s
    SET_WINDCF = 'WindCF'  # Wind capacity factor as percentage (range 0 - 1)
    SET_HYDRO = 'power'  # Hydropower potential in kW
    SET_HYDRO_DIST = 'HydropowerDist'  # Distance to hydropower site in km
    SET_HYDRO_FID = 'HydropowerFID'  # the unique tag for eah hydropower, to not over-utilise
    SET_SUBSTATION_DIST = 'SubstationDist'
    SET_ELEVATION = 'Elevation'  # in metres
    SET_SLOPE = 'Slope'  # in degrees
    SET_LAND_COVER = 'LandCover'
    SET_SOLAR_RESTRICTION = 'SolarRestriction'
    #
    # Here are the layers in the geodatabase. Make sure that the naming convection is the same as it appears on ArcGIS
    #
    pop = 'pop2015'  # Type: raster, Unit: people per 100km2, must be in resolution 10km x 10km
    ghi = 'ghi'  # Type: raster, Unit: kWh/m2/day
    windvel = 'windvel'  # Type: raster, Unit: capacity factor as a percentage (range 0 - 1)
    travel = 'traveltime'  # Type: raster, Unit: hours
    grid_existing = 'existing_grid'  # Type: shapefile (line)
    grid_planned = 'planned_grid'  # Type: shapefile (line)
    hydro_points = 'hydro_points'  # Type: shapefile (points), Unit: kW (field must be named Hydropower)
    admin_raster = 'admin_0'  # Type: raster, country names must conform to specs.xlsx file
    admin1_raster = 'admin_1'  # Type: raster, country names must conform to specs.xlsx file
    roads = 'completedroads'  # Type: shapefile (lines)
    nightlights = 'nightlights'  # Type: raster, Unit: (range 0 - 63)
    substations = 'allsubstations'
    elevation = 'elevation'
    slope = 'slope'
    land_cover = 'landcover'
    solar_restriction = 'solar_restrictions'
    settlements_fc = 'Afghanistan10km'  # Here you can select the name of the feature class that will aggregate all the results
    ##
    ## All the commands that are together (no gaps inbetween) can be executed together.
    ## Depending on computational cababilities more commands can be executed together.

    arcpy.RasterToPoint_conversion(pop, settlements_fc)
    arcpy.AlterField_management(settlements_fc, 'grid_code', SET_POP)

    arcpy.AddXY_management(settlements_fc)
    arcpy.AddField_management(settlements_fc, SET_X, 'FLOAT')
    arcpy.CalculateField_management(settlements_fc, SET_X, '!POINT_X! / 1000', 'PYTHON_9.3')
    arcpy.AddField_management(settlements_fc, SET_Y, 'FLOAT')
    arcpy.CalculateField_management(settlements_fc, SET_Y, '!POINT_Y! / 1000', 'PYTHON_9.3')
    arcpy.DeleteField_management(settlements_fc, 'POINT_X; POINT_Y')

    arcpy.sa.ExtractMultiValuesToPoints(settlements_fc, [[solar_restriction, SET_SOLAR_RESTRICTION]])

    arcpy.sa.ExtractMultiValuesToPoints(settlements_fc, [[travel, SET_TRAVEL_HOURS]])

    arcpy.sa.ExtractMultiValuesToPoints(settlements_fc, [[nightlights, SET_NIGHT_LIGHTS]])

    arcpy.sa.ExtractMultiValuesToPoints(settlements_fc, [[elevation, SET_ELEVATION]])

    arcpy.sa.ExtractMultiValuesToPoints(settlements_fc, [[slope, SET_SLOPE]])

    arcpy.sa.ExtractMultiValuesToPoints(settlements_fc, [[land_cover, SET_LAND_COVER]])

    arcpy.Near_analysis(settlements_fc, grid_existing)
    arcpy.AddField_management(settlements_fc, SET_GRID_DIST_CURRENT, 'FLOAT')
    arcpy.CalculateField_management(settlements_fc, SET_GRID_DIST_CURRENT, '!NEAR_DIST! / 1000', 'PYTHON_9.3')
    arcpy.DeleteField_management(settlements_fc, 'NEAR_DIST; NEAR_FID')

    arcpy.Near_analysis(settlements_fc, [grid_existing, grid_planned])
    arcpy.AddField_management(settlements_fc, SET_GRID_DIST_PLANNED, 'FLOAT')
    arcpy.CalculateField_management(settlements_fc, SET_GRID_DIST_PLANNED, '!NEAR_DIST! / 1000', 'PYTHON_9.3')
    arcpy.DeleteField_management(settlements_fc, 'NEAR_DIST; NEAR_FID; NEAR_FC')

    arcpy.Near_analysis(settlements_fc, substations)
    arcpy.AddField_management(settlements_fc, SET_SUBSTATION_DIST, 'FLOAT')
    arcpy.CalculateField_management(settlements_fc, SET_SUBSTATION_DIST, '!NEAR_DIST! / 1000', 'PYTHON_9.3')
    arcpy.DeleteField_management(settlements_fc, 'NEAR_DIST; NEAR_FID; NEAR_FC')

    arcpy.Near_analysis(settlements_fc, roads)
    arcpy.AddField_management(settlements_fc, SET_ROAD_DIST, 'FLOAT')
    arcpy.CalculateField_management(settlements_fc, SET_ROAD_DIST, '!NEAR_DIST! / 1000', 'PYTHON_9.3')
    arcpy.DeleteField_management(settlements_fc, 'NEAR_DIST; NEAR_FID')

    arcpy.Near_analysis(settlements_fc, hydro_points)
    arcpy.AddField_management(settlements_fc, SET_HYDRO_DIST, 'FLOAT')
    arcpy.CalculateField_management(settlements_fc, SET_HYDRO_DIST, '!NEAR_DIST! / 1000', 'PYTHON_9.3')
    arcpy.JoinField_management(settlements_fc, 'NEAR_FID', hydro_points,
    arcpy.Describe(hydro_points).OIDFieldName, [SET_HYDRO])
    arcpy.AlterField_management(settlements_fc, 'NEAR_FID', SET_HYDRO_FID, SET_HYDRO_FID)
    arcpy.DeleteField_management(settlements_fc, 'NEAR_DIST')

    # Here the process changes due to some peculiarities of the following datasets
    # path1=r"C:\Users\Dimitris\Desktop\OnSSET\AFG_GIS_10km\Assistingfolder" this is moved at the top
    path2=path1+"\Afghanistan"
    path3=path1+"\Afghanistan_Provinces"
    path4=path1+"\GlobalHI"
    path5=path1+"\WIND"

    arcpy.sa.ExtractValuesToPoints(settlements_fc,admin_raster,path2,"NONE", "ALL")
    arcpy.sa.ExtractValuesToPoints(settlements_fc,admin1_raster,path3,"NONE", "ALL")
    arcpy.sa.ExtractValuesToPoints(settlements_fc,ghi,path4,"INTERPOLATE","VALUE_ONLY")
    arcpy.sa.ExtractValuesToPoints(settlements_fc,windvel,path5,"INTERPOLATE","VALUE_ONLY")

    arcpy.env.workspace = path1
    in_features = ['WIND.shp', 'GlobalHI.shp', 'Afghanistan.shp', 'Afghanistan_Provinces.shp']
    out_location = path
    arcpy.FeatureClassToGeodatabase_conversion(in_features, out_location)

    arcpy.env.workspace = path

    arcpy.JoinField_management(settlements_fc,"pointid","WIND","pointid","RASTERVALU")

    arcpy.JoinField_management(settlements_fc,"pointid","GlobalHI","pointid","RASTERVALU")

    arcpy.JoinField_management(settlements_fc,"pointid","Afghanistan","pointid","CNTRY_NAME")

    arcpy.JoinField_management(settlements_fc,"pointid","Afghanistan_Provinces","pointid","Prov_Name")

    # outpath = r"C:\Users\Dimitris\Desktop\OnSSET" this is moved at the top
    arcpy.TableToTable_conversion(settlements_fc,outpath,"AfghanistanSett10k")



Manual GIS processing using ArcGIS
----------------------------------------

Projecting coordinate systems
++++++++++++++++++++++++++++++++++++++++++++++++

**Projection** is the systematic transformation of the latitude and longitude of a location into a pair of two dimensional coordinates or else the position of this location on a plane (flat) surface.
A projection is necessary every time a map is created and all map projections distort the surface in some fashion.

.. note::
    Ellipsoid, Datum & Geographic Coordinate System

    **Coordinate System:** Simply put, it is a way of describing a spatial property relative to a center.

    **Datum:** The center and orientation of the ellipsoid

    .. image:: img/crs1.png
        :width: 350px
        :height: 200px
        :align: center

    .. image:: img/crs2.png
        :width: 300
        :height: 150
        :align: center

Make sure you that you use **World Geodetic Datum 1984 (WGS84)** for all layers. Check by right-clicking on the layer in ArcGIS and select *Properties* then look at the *Source* tab. If this is not the case the datasets need to be projected to this coordinate System. This is done in 3 steps

* Open the Project tool in ArcMap (Data Management Tools --> Projections and Transformations --> Project or simply type project in the search bar).

* In the field that says *Input Dataset or Feature Class* select the dataset that you wish to project

* The next step is to select the *Output Coordinate System*. This can be done in two ways.

    1. If you already have a layer with the right coordinate system simply open up the layer folder and choose WGS 1984.

                .. figure:: img/fig11.jpg
                    :width: 300px
                    :height: 100px
                    :align: center

    2. If you do not have a layer with the right coordinate system open up the the following path: **Projected Coordinate Systems** --> **UTM** --> **WGS 1984** and choose an UTM Zone. The easiest way to find the UTM zone is to google it i.e. "Tanzania UTM zone". You can also use the following source: http://coordtrans.com/coordtrans/guide.asp?section=SupportedCountries (all countries are not available. For cases in which you have more than one UTM zone option chose one and be consistent.


**Slope**

The slope map is not downloaded as a dataset but rather generated from the elevation map. In order to create the slope map certain steps need to be followed.

1. In ArcMap open the slope tool (Spatial Analyst Tools --> Surface --> slope or simply type in the search bar).

2. You will be asked to specify the input file. For this use your elevation map. When the input file is chosen the box with the output file should automatically be filled in

3. Make sure that the output measurement is set to **degree**

4. The last step is to enter a value for the **Z-factor**. For this the following table can be used:

                           +----------+------------+
                           | Latitude | Z-factor   |
                           +----------+------------+
                           | 0        | 0.00000898 |
                           +----------+------------+
                           | 10       | 0.00000912 |
                           +----------+------------+
                           | 20       | 0.00000956 |
                           +----------+------------+
                           | 30       | 0.00001036 |
                           +----------+------------+
                           | 40       | 0.00001171 |
                           +----------+------------+
                           | 50       | 0.00001395 |
                           +----------+------------+
                           | 60       | 0.00001792 |
                           +----------+------------+
                           | 70       | 0.00002619 |
                           +----------+------------+
                           | 80       | 0.00005156 |
                           +----------+------------+

In which the latitude is the central latitude of the study area


Exporting the data from ArcGIS to .csv
***************************************

In order to be able to make the analysis all the data from ArcMap need to be transfered to an .csv file. This will
make it possible to run the analysis in Python. This might be a rather time consuming task depending on the
resolution of the study area. In order to transfer all the data to .csv files 6 steps need to be taken.

1. Create a raster basemap of the study area. The values in this map are not important. The only thing that you need to make sure is that you have the right resolution on it.

2. In ArcMap open the Sample tool (Spatial Analyst Tools --> Extraction --> Sample or simply type sample in the search bar)

3. In the field "Input raster" enter the dataset that you would like to sample (The dataset that you have to sample are described below ).

4. In the field "Input location raster or point feature" enter the dataset that you created in step 1

5. When these steps are completed you should end up with a table in ArcMap in order to get it to a csv file open the Table to Excel tool in ArcMap (Conversion tools --> Excel --> Table to Excel or simply type table to excel in the search bar).

6. Here you chose the input table as the table you recieved after finishing sample.

By following these steps you should be left with an excel file with X and Y coordinates as well as a value in every grid cell for the dataset that you have chosen to sample. When these steps are done you also need to put all of the excel files into one single file with every column having the names given by OnSSET's naming convention.

.. note::
    You can sample more than one dataset at a time. However this could lead to difficulties when creating the
    input file for OnSSET. It also requires a significant amount of computational capacity.

GIS country file
------------------------------
The table below shows all the parameters that should be sampled and put into the csv file representing the study area.

+--------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------+
| **Parameter**            | **Description**                                                                                                                                          |
+==========================+==========================================================================================================================================================+
| Country                  | Name of the country                                                                                                                                      |
+--------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------+
| Pop                      | Population in base year                                                                                                                                  |
+--------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------+
| X                        | Longitude                                                                                                                                                |
+--------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------+
| Y                        | Latitude                                                                                                                                                 |
+--------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------+
| GHI                      | Global Horizontal Irradiation (kWh/m2/year)                                                                                                              |
+--------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------+
| SolarRestriction         | Defines if an areas is restricted to solar PV deployment (1: restricted, 0: non restricted)                                                              |
+--------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------+
| WindVel                  | Wind speed (m/s)                                                                                                                                         |
+--------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------+
| TravelHours              | Distance to the nearest town (hours)                                                                                                                     |
+--------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------+
| NightLights              | Nighttime light intensity (0-63)                                                                                                                         |
+--------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------+
| Elevation                | Elevation from sea level (m)                                                                                                                             |
+--------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------+
| Slope                    | Ground surface slope gradient (degrees)                                                                                                                  |
+--------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------+
| LandCover                | Type of land cover as defined by the source data                                                                                                         |
+--------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------+
| GridDistCurrent          | Distance from the existing electricity grid network (km)                                                                                                 |
+--------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------+
| GridDistPlan             | Distance from the planned electricity grid network (km)                                                                                                  |
+--------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------+
| SubstationDist           | Distance from the existing sub-stations (km)                                                                                                             |
+--------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------+
| RoadDist                 | Distance from the existing and planned road network (km)                                                                                                 |
+--------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------+
| HydropowerDist           | Distance from identified hydropower potential (km)                                                                                                       |
+--------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------+
| Hydropower               | Closest hydropower technical potential identified                                                                                                        |
+--------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------+
| HydropowerFID            | ID of the nearest hydropower potential                                                                                                                   |
+--------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------+


.. note::
    It is very important that the columns in the csv-file are named exactly as they are namned in the **Parameter**-column in the table above.






































