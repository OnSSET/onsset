GIS data preparation
========================

Once all 16 layers have been succesfully acquired, the user would need to prepare the datasets for their input into the OnSSET model. This requires the creation of a .csv file. There are five steps that need to be undertaken to process the GIS data so that it can be used for an OnSSET analysis.

**Step 1. Proper data types and coordinate system** 
---------------------------------------------------

In this first step the user would need to secure that you have all the 16 datasets have been properly overlayed within a GIS environment. IT is common that layers in this stage are un-projected and at their initial geographic co-ordinate system (e.g. WGS84).

**Step 2. Layer projection** 
---------------------------------------------------

In this step the user would need to project every single layer using the projection system that is suitable for your study area (e.g. WGS 1984 World Mercator). Here follow few important kew aspects.

**Projection** is the systematic transformation of the latitude and longitude of a location into a pair of two dimensional coordinates or else the position of this location on a plane (flat) surface. A projection is necessary every time a map is created and all map projections distort the surface in some fashion.

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

**Step 3. Create and populate a geo-database** 
---------------------------------------------------

The used will not need to create and generate a geo-database containing all the projected layers of the analysis under the proper naming convention. Further documentation on the process is available `here <https://github.com/KTH-dESA/PyOnSSET/tree/master/Resource_Assessment/Prepare_The_Geodatabase>`_.


**Step 4. Inform the Settlements' layer** 
---------------------------------------------------

Once the geo-database is filled in with all the layers, we can make use of it in order to combine all layers together into a single table. The principle is simple. We will use the population layer in order to create a base table. Every row in this table represents a grid cell. The, we will adhere one by one all the layers into this table so that every row (grid cell) acquires its specific characteristics based on its location. One can perform the process manually by identifying the tools in the GIS environment of his preference. 

In order to facilitate the process KTH dESA has prepared a batch of python commands that can directly be ran by the user using the python command window. Here follows an example of these commands. **Note!** These commands have been developed for python version 2 and work properly in the ArcGIS environment. In case the user chooses a different GIS environment (e.g. Grass, Qgis etc.) these commands might need slight modification. 

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

.. note::

   A fully updated version of this code is available `here <https://github.com/KTH-dESA/PyOnSSET/tree/master/Resource_Assessment/Python_Commands_For_Processing_GIS_Data>`_. 


**Step 5. Preparing the .csv file** 
---------------------------------------------------

Once the process finishes, the settlements file is almost ready. The settlements layer contains the population points throughout the country’s territory along with 16 attributes that are useful for conducting the electrification analysis with OnSSET. In order to continue with the electrification model, this layer needs to be extracted from GIS to a .csv file. Here are two options of how this action can be performed. 

1.	Use the **DBF_TO_CSV tool** which has been developed for this exact reason by KTH dESA. The tool is available `here <https://github.com/KTH-dESA/PyOnSSET/tree/master/Resource_Assessment/DBF_to_CSV>`_.

2.	The settlements file is a shapefile. That is, a dbf file is always existing in the same directory. This dbf file contains the trivial information of the settlements file and can be opened via Excel. Then one can use excel to save the file as csv.

By following these steps you should be left with a .csv file with X and Y coordinates as well as a value in every grid cell for the dataset that you have chosen to sample. When these steps are done you also need to put all of the excel files into one single file with every column having the names given by OnSSET's naming convention. Find a python code performing this in a quick and easy manner `here <https://github.com/KTH-dESA/PyOnSSET/tree/master/Resource_Assessment/Conditioning>`_. 

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
