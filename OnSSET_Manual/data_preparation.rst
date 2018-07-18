GIS data preparation
========================

Once all necessary layers have been succesfully acquired, the user would need to prepare the datasets for their input into the OnSSET model. This requires the creation of a .csv file. There are five steps that need to be undertaken to process the GIS data so that it can be used for an OnSSET analysis.

**Step 1. Proper data types and coordinate system** 
---------------------------------------------------

In this first step the user would need to secure that you have all the datasets have been properly overlayed within a GIS environment. It is common that layers in this stage are un-projected and at their initial geographic co-ordinate system (e.g. WGS84).

**Step 2. Layer projection** 
---------------------------------------------------

In this step the user would need to determine the projection system he/she wish to use. Projection systems always distort the datasets and the system chosen should be one that minimizes this distortion. There is no need to manually project the datasets yourself it is however good to have an idea of which system to use before starting to work with the datasets.
Here follows a few important key aspects.

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
        :align: 

Before starting the analysis make sure that all datasets have the same coordiante system (preferably **World Geodetic Datum 1984 (WGS84)**) You can check the coordinate system of your layers by importing them into QGIS and then right-clickin on them and open the **Properties** window. In the Properties window go to the **Information** tab, here the coordinate system used is listed under *CRS* for both raster and vector datasets. 


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

Before starting the analysis make sure that all datasets have the same coordiante system (preferably **World Geodetic Datum 1984 (WGS84)**) You can check the coordinate system of your layers by importing them into QGIS and then right-clickin on them and open the **Properties** window. In the Properties window go to the **Information** tab, here the coordinate system used is listed under *CRS* for both raster and vector datasets. 

**Step 3. Import all the layers into QGIS** 
---------------------------------------------------

When all of the datasets are gathered and the user has made sure that the datasets are all in the same coordinate system import them into QGIS 

**Step 4. Inform the Settlements' layer** 
---------------------------------------------------

Once the previous steps are finished, we can combine all layers together into a single table. The principle is simple. We will use the population layer in order to create a base table. Every row in this table represents a grid cell. Then, we will adhere one by one all the layers into this table so that every row (grid cell) acquires its specific characteristics based on its location. One can perform the process manually by identifying the tools in the GIS environment of his preference. 

In order to facilitate the process KTH dESA has prepared a batch of python commands that can directly be ran directly in the QGIS script runner. Here follows an example of these commands. **Note!** These commands have been developed for python version 3 and work properly in the QGIS environment as long as it is QGIS version 3.0 or newer. In case the user chooses a different GIS environment (e.g. Grass, ArcGIS etc.) these commands might need modifications.


    **Example:**

.. code-block:: python

    # Import the following packages in order to run code
    import sys
    import os
    from qgis.core import *
    from PyQt5.QtGui import *
    from processing.core.Processing import Processing
    Processing.initialize()
    import processing


    ### Things that need to be changed
    # This is the workspace with all the datasets that you wish to use should be here in corresponding sub-folders.
    # The workspace has to include the subfolders with all of the 16 layers
    workspace = r'C:\OSGeo4W64\Lesotho'

    #This is the epsg code of the coordinate system that you wish to project your datasets TO
    projCord = "EPSG:3395"

    #The name of the settlement that you are analysing this will be name of your output csv file
    settlements_fc = 'Lesotho'

    #The name of the column including your hydropower potential in either kW, MW or W (This is important to specify for
    #the hydrolayer later on in hte code.
    hydropowerField = "power"

    #We will create two additional folders in every run calling them Assist and Assist2 these folders are used in order for
    #the code to run more smoothly.
    if not os.path.exists(workspace + r"/Assist"):
         os.makedirs(workspace + r"/Assist")

    if not os.path.exists(workspace + r"/Assist2"):
         os.makedirs(workspace + r"/Assist2")

    assistingFolder = workspace + r"/Assist"
    assistingFolder2 = workspace + r"/Assist2"

    # The naming of all the datasets, make sure that the datasets are named as they are named here
    pop = 'pop2015'
    ghi = 'ghi'
    windvel = 'windvel'
    travel = 'traveltime'
    grid_existing = 'existing_grid'
    grid_planned = 'planned_grid'
    hydro_points = 'hydro_points'
    admin = 'admin_0'
    roads = 'roads'
    nightlight = 'nightlights'
    substations = 'substations'
    elevation = 'elevation'
    slope = 'slope'
    land_cover = 'landcover'
    solar_restriction = 'solar_restrictions'


    # Import admin polygon
    # We import it in order to clip the population dataset (in case the population dataset is global)
    admin = workspace + r'/Admin/' + admin + '.shp'

    # Creata a "extent" layer, this will be used to clip all the other datasets in the analysis, this way we will not have null values.
    ext = QgsVectorLayer(admin,'','ogr').extent()

    xmin = ext.xMinimum()-1
    xmax = ext.xMaximum()+1
    ymin = ext.yMinimum()-1
    ymax = ext.yMaximum()+1

    # Createas a coords string. This is important for some of the calculations below
    coords = '{},{},{},{}'.format(xmin, xmax, ymin, ymax)

    # Clip population map with admin and create point layer
    pop_data = workspace + r"/Population_2015/"+ pop + ".tif"
    processing.run("gdal:cliprasterbymasklayer", {'INPUT':pop_data,'MASK':admin,'NODATA':None,'ALPHA_BAND':False,'CROP_TO_CUTLINE':True,'KEEP_RESOLUTION':True,'OPTIONS':'','DATA_TYPE':5,'OUTPUT':workspace + r'/Population_2015/' + pop + settlements_fc[0:3] +'.tif'})
    processing.run("saga:rastervaluestopoints", {'GRIDS':[workspace + r'/Population_2015/' + pop + settlements_fc[0:3] +'.tif'],'POLYGONS':None,'NODATA        ':True,'TYPE':0,'SHAPES': workspace + r'/Population_2015/Pop.shp'})

    # Projecting the population points
    processing.run("native:reprojectlayer", {'INPUT':workspace + r'/Population_2015/Pop.shp','TARGET_CRS':projCord,'OUTPUT':workspace + r'/Population_2015/' + pop + '.shp'})
    Pop = QgsVectorLayer(workspace + r'/Population_2015/' + pop + '.shp','','ogr')

    # Identify the field showing the population
    field_ids = []
    fieldnames = set(['pop2015'+ settlements_fc[0:3]])
    for field in Pop.fields():
        if field.name() not in fieldnames:
          field_ids.append(Pop.fields().indexFromName(field.name()))

    # Remove all the fields that are not the population field identified above
    Pop.dataProvider().deleteAttributes(field_ids)
    Pop.updateFields()

    # Raster datasets
    # Create elevation and slope maps.
    # 1. Clip the elevation map with the extent layer.
    # 2. Create a terrain slope map with the elevation layer
    # 3. Reprojects the slope and elevation maps to the coordinates specified above
    # 4. Interpolates the elevation and slope maps in order to avoid null values
    processing.run("gdal:cliprasterbyextent", {'INPUT':workspace + r'/DEM/' + elevation + '.tif','PROJWIN':coords,'NODATA':None,'OPTIONS':'','DATA_TYPE':5,'OUTPUT':workspace + r'/DEM/' + elevation + settlements_fc[0:3] +'.tif'})
    processing.run("gdal:slope", {'INPUT':workspace + r'/DEM/' + elevation + settlements_fc[0:3] +'.tif','BAND':1,'SCALE':111120,'AS_PERCENT':False,'COMPUTE_EDGES':False,'ZEVENBERGEN':False,'OPTIONS':'','OUTPUT':workspace + r"/Slope/" + slope + settlements_fc[0:3] + ".tif"})
    processing.run("gdal:warpreproject", {'INPUT':workspace + r"/Slope/" + slope + settlements_fc[0:3] + ".tif",'SOURCE_CRS':None,'TARGET_CRS':projCord,'NODATA':0,'TARGET_RESOLUTION':0,'OPTIONS':'','RESAMPLING':0,'DATA_TYPE':5,'TARGET_EXTENT':None,'TARGET_EXTENT_CRS':None,'MULTITHREADING':False,'OUTPUT':workspace + r'/Slope/' + slope + settlements_fc[0:3] +'_Proj.tif'})
    processing.run("gdal:warpreproject", {'INPUT':workspace + r'/DEM/' + elevation + settlements_fc[0:3] +'.tif','SOURCE_CRS':None,'TARGET_CRS':projCord,'NODATA':0,'TARGET_RESOLUTION':0,'OPTIONS':'','RESAMPLING':0,'DATA_TYPE':5,'TARGET_EXTENT':None,'TARGET_EXTENT_CRS':None,'MULTITHREADING':False,'OUTPUT':workspace + r'/DEM/' + elevation + settlements_fc[0:3] +'_Proj.tif'})
    processing.run("gdal:fillnodata", {'INPUT':workspace + r'/Slope/' + slope + settlements_fc[0:3] +'_Proj.tif','BAND':1,'DISTANCE':10,'ITERATIONS':0,'NO_MASK':False,'MASK_LAYER':None,'OUTPUT':assistingFolder2 +r'/' + slope + ".tif"})
    processing.run("gdal:fillnodata", {'INPUT':workspace + r'/DEM/' + elevation + settlements_fc[0:3] +'_Proj.tif','BAND':1,'DISTANCE':10,'ITERATIONS':0,'NO_MASK':False,'MASK_LAYER':None,'OUTPUT':assistingFolder2 +r'/' + elevation + ".tif"})

    # GHI
    # 1. Clip the ghi map with the extent layer.
    # 2. Reprojects the ghi map to the coordinates specified above
    # 3. Interpolates the ghi map in order to avoid null values
    processing.run("gdal:cliprasterbyextent", {'INPUT':workspace + r'/Solar/' + ghi + '.tif','PROJWIN':coords,'NODATA':None,'OPTIONS':'','DATA_TYPE':5,'OUTPUT':workspace + r'/Solar/' + ghi + settlements_fc[0:3] +'.tif'})
    processing.run("gdal:warpreproject", {'INPUT':workspace + r'/Solar/' + ghi + settlements_fc[0:3] +'.tif','SOURCE_CRS':None,'TARGET_CRS':projCord,'NODATA':0,'TARGET_RESOLUTION':0,'OPTIONS':'','RESAMPLING':0,'DATA_TYPE':5,'TARGET_EXTENT':None,'TARGET_EXTENT_CRS':None,'MULTITHREADING':False,'OUTPUT':workspace + r'/Solar/' + ghi + settlements_fc[0:3] +'_Proj.tif'})
    processing.run("gdal:fillnodata", {'INPUT':workspace + r'/Solar/' + ghi + settlements_fc[0:3] +'_Proj.tif','BAND':1,'DISTANCE':10,'ITERATIONS':0,'NO_MASK':False,'MASK_LAYER':None,'OUTPUT':assistingFolder2 +r'/' + ghi + ".tif"})

    # Traveltime
    # 1. Clip the traveltime map with the extent layer.
    # 2. Reprojects the traveltime map to the coordinates specified above
    # 3. Interpolates the traveltime map in order to avoid null values
    processing.run("gdal:cliprasterbyextent", {'INPUT':workspace + r'/Travel_time/' + travel + '.tif','PROJWIN':coords,'NODATA':None,'OPTIONS':'','DATA_TYPE':5,'OUTPUT':workspace + r'/Travel_time/' + travel + settlements_fc[0:3] +'.tif'})
    processing.run("gdal:warpreproject", {'INPUT':workspace + r'/Travel_time/' + travel + settlements_fc[0:3] +'.tif','SOURCE_CRS':None,'TARGET_CRS':projCord,'NODATA':0,'TARGET_RESOLUTION':0,'OPTIONS':'','RESAMPLING':0,'DATA_TYPE':5,'TARGET_EXTENT':None,'TARGET_EXTENT_CRS':None,'MULTITHREADING':False,'OUTPUT':workspace + r'/Travel_time/' + travel + settlements_fc[0:3] +'_Proj.tif'})
    processing.run("gdal:fillnodata", {'INPUT':workspace + r'/Travel_time/' + travel + settlements_fc[0:3] +'_Proj.tif','BAND':1,'DISTANCE':10,'ITERATIONS':0,'NO_MASK':False,'MASK_LAYER':None,'OUTPUT':assistingFolder2 +r'/' + travel + ".tif"})

    # Wind
    # 1. Clip the wind velocity map with the extent layer.
    # 2. Reprojects the wind velocity map to the coordinates specified above
    # 3. Interpolates the wind velocity map in order to avoid null values
    processing.run("gdal:cliprasterbyextent", {'INPUT':workspace + r'/Wind/' + windvel + '.tif','PROJWIN':coords,'NODATA':None,'OPTIONS':'','DATA_TYPE':5,'OUTPUT':workspace + r'/Wind/' + windvel + settlements_fc[0:3] +'.tif'})
    processing.run("gdal:warpreproject", {'INPUT':workspace + r'/Wind/' + windvel + settlements_fc[0:3] +'.tif','SOURCE_CRS':None,'TARGET_CRS':projCord,'NODATA':0,'TARGET_RESOLUTION':0,'OPTIONS':'','RESAMPLING':0,'DATA_TYPE':5,'TARGET_EXTENT':None,'TARGET_EXTENT_CRS':None,'MULTITHREADING':False,'OUTPUT':workspace + r'/Wind/' + windvel + settlements_fc[0:3] +'_Proj.tif'})
    processing.run("gdal:fillnodata", {'INPUT':workspace + r'/Wind/' + windvel + settlements_fc[0:3] +'_Proj.tif','BAND':1,'DISTANCE':10,'ITERATIONS':0,'NO_MASK':False,'MASK_LAYER':None,'OUTPUT':assistingFolder2 + r'/' + windvel + ".tif"})

    # Solar restriction
    # 1. Clip the solar restriction map with the extent layer.
    # 2. Reprojects the solar restriction map to the coordinates specified above
    # This dataset is not interpolated as it is  discrete
    processing.run("gdal:cliprasterbyextent", {'INPUT':workspace + r'/Solar_Restrictions/' + solar_restriction + '.tif','PROJWIN':coords,'NODATA':None,'OPTIONS':'','DATA_TYPE':5,'OUTPUT':workspace + r'/Solar_restrictions/' + solar_restriction + settlements_fc[0:3] +'.tif'})
    processing.run("gdal:warpreproject", {'INPUT':workspace + r'/Solar_restrictions/' + solar_restriction + settlements_fc[0:3] +'.tif','SOURCE_CRS':None,'TARGET_CRS':projCord,'NODATA':0,'TARGET_RESOLUTION':0,'OPTIONS':'','RESAMPLING':0,'DATA_TYPE':5,'TARGET_EXTENT':None,'TARGET_EXTENT_CRS':None,'MULTITHREADING':False,'OUTPUT':assistingFolder2 + r'/' + solar_restriction + '_Proj.tif'})

    # Landcover
    # 1. Clip the landcover map with the extent layer.
    # 2. Reprojects the landcover map to the coordinates specified above
    # This dataset is not interpolated as it is discrete
    processing.run("gdal:cliprasterbyextent", {'INPUT':workspace + r'/Land_Cover/' + land_cover + '.tif','PROJWIN':coords,'NODATA':None,'OPTIONS':'','DATA_TYPE':5,'OUTPUT':workspace + r'/Land_Cover/' + land_cover + settlements_fc[0:3] +'.tif'})
    processing.run("gdal:warpreproject", {'INPUT':workspace + r'/Land_Cover/' + land_cover + settlements_fc[0:3] +'.tif','SOURCE_CRS':None,'TARGET_CRS':projCord,'NODATA':0,'TARGET_RESOLUTION':0,'OPTIONS':'','RESAMPLING':0,'DATA_TYPE':5,'TARGET_EXTENT':None,'TARGET_EXTENT_CRS':None,'MULTITHREADING':False,'OUTPUT':assistingFolder2 +r'/'+ land_cover + settlements_fc[0:3] +'_Proj.tif'})

    # Nighttimelights
    # 1. Clip the landcover map with the extent layer.
    # 2. Reprojects the landcover map to the coordinates specified above
    # This dataset is not interpolated as it is discrete
    processing.run("gdal:cliprasterbyextent", {'INPUT':workspace + r'/Night_Time_Lights/' + nightlight + '.tif','PROJWIN':coords,'NODATA':None,'OPTIONS':'','DATA_TYPE':5,'OUTPUT':workspace + r'/Night_Time_Lights/' + nightlight + settlements_fc[0:3] +'.tif'})
    processing.run("gdal:warpreproject", {'INPUT':workspace + r'/Night_Time_Lights/' + nightlight + settlements_fc[0:3] +'.tif','SOURCE_CRS':None,'TARGET_CRS':projCord,'NODATA':0,'TARGET_RESOLUTION':0,'OPTIONS':'','RESAMPLING':0,'DATA_TYPE':5,'TARGET_EXTENT':None,'TARGET_EXTENT_CRS':None,'MULTITHREADING':False,'OUTPUT':assistingFolder2 +r'/'+ nightlight + settlements_fc[0:3] +'_Proj.tif'})

    # Define all the rastermaps that have been generated this far
    elevation = QgsRasterLayer(assistingFolder2 + r'/' + elevation + ".tif",'elevation')
    slope = QgsRasterLayer(assistingFolder2 +r'/'+ slope + ".tif",'slope')
    solar = QgsRasterLayer(assistingFolder2 +r'/'+ ghi + ".tif",'solar')
    traveltime = QgsRasterLayer(assistingFolder2 +r'/'+ travel + ".tif", 'traveltime')
    windvel = QgsRasterLayer(assistingFolder2 +r'/'+ windvel + ".tif",'windvel')
    solar_restrictions = QgsRasterLayer(assistingFolder2 +r'/'+ solar_restriction + '_Proj.tif','solar_restrictions')
    landcover = QgsRasterLayer(assistingFolder2 + r'/'+ land_cover + settlements_fc[0:3] +'_Proj.tif','landcover')
    nightlights = QgsRasterLayer(assistingFolder2 +r'/'+ nightlight + settlements_fc[0:3] +'_Proj.tif','nightlights')

    # Add the rastervalues to points adds all the raster values to the population point layer based on coordinates
    processing.run("saga:addrastervaluestopoints", {'SHAPES':Pop,'GRIDS':[elevation, landcover, nightlights, slope, solar,solar_restrictions, traveltime, windvel],'RESAMPLING':0,'RESULT':assistingFolder2 + r"/SettlementsPlaceholder_withoutID.shp"})
    processing.run("qgis:fieldcalculator", {'INPUT':assistingFolder2 + r"/SettlementsPlaceholder_withoutID.shp",'FIELD_NAME':'AUTO','FIELD_TYPE':0,'FIELD_LENGTH':10,'FIELD_PRECISION':3,'NEW_FIELD':True,'FORMULA':' @row_number ','OUTPUT':assistingFolder + r"/SettlementsPlaceholder.shp"})

    # Define layer created above
    settlement = QgsVectorLayer(assistingFolder + r"/SettlementsPlaceholder.shp","","ogr")

    # Vector datasets
    # substations
    # 1. Create a column with the name AUTO this is needed in order for all vector files to have at least one column in common
    # 2. Clips and removes all vectors outside the admin raster
    # 3. Reprojects the vector layer
    # 4. Calculates the distance to nearest vector element for all the cells in the population layer (we need the name of a column and we use the ENUM_ID
    processing.run("qgis:fieldcalculator", {'INPUT':workspace + r'/Substations/' + substations + '.shp','FIELD_NAME':'AUTO','FIELD_TYPE':0,'FIELD_LENGTH':10,'FIELD_PRECISION':3,'NEW_FIELD':True,'FORMULA':' @row_number ','OUTPUT':workspace + r'/Substations/' + substations + '_with_ID.shp'})
    processing.run("native:clip", {'INPUT':workspace + r'/Substations/' + substations + '_with_ID.shp','OVERLAY':admin,'OUTPUT':workspace + r'/Substations/' + substations + settlements_fc[0:3] +'.shp'})
    processing.run("native:reprojectlayer", {'INPUT':workspace + r'/Substations/' + substations + settlements_fc[0:3] +'.shp','TARGET_CRS':projCord,'OUTPUT':workspace + r'/Substations/' + substations + settlements_fc[0:3] +'_Proj.shp'})
    processing.run("qgis:distancetonearesthubpoints", {'INPUT':Pop,'HUBS':workspace + r'/Substations/' + substations + settlements_fc[0:3] +'_Proj.shp','FIELD':'AUTO','UNIT':0,'OUTPUT':assistingFolder2 + r"\Substationsdist_NO_ID.shp"})
    processing.run("qgis:fieldcalculator", {'INPUT':assistingFolder2 + r"\Substationsdist_NO_ID.shp",'FIELD_NAME':'AUTO','FIELD_TYPE':0,'FIELD_LENGTH':10,'FIELD_PRECISION':3,'NEW_FIELD':True,'FORMULA':' @row_number ','OUTPUT':workspace + r"\Substations\Substationsdist.shp"})
    substationsdist = QgsVectorLayer(workspace + r"\Substations\Substationsdist.shp","","ogr")

    # Identify the field showing the substationdist
    field_ids = []
    fieldnames = set(['HubDist', 'AUTO'])
    for field in substationsdist.fields():
        if field.name() not in fieldnames:
          field_ids.append(substationsdist.fields().indexFromName(field.name()))

    # Remove all the columns that are not substationdist
    substationsdist.dataProvider().deleteAttributes(field_ids)
    substationsdist.updateFields()

    # rename the hubdist field to SubstationDist
    for field in substationsdist.fields():
        if field.name() == 'HubDist':
            with edit(substationsdist):
                idx = substationsdist.fields().indexFromName(field.name())
                substationsdist.renameAttribute(idx, 'SubstationDist')

    #Hydropower
    # 1. Create a column with the name AUTO this is needed in order for all vector files to have at least one column in common
    # 2. Clips and removes all vectors outside the admin raster
    # 3. Reprojects the vector layer
    # 4. Calculates the distance to nearest vector element for all the cells in the population layer (we need the name of a column and we use the ENUM_ID
    processing.run("qgis:fieldcalculator", {'INPUT':workspace + r'/Hydropower/' + hydro_points + '.shp','FIELD_NAME':'AUTO','FIELD_TYPE':0,'FIELD_LENGTH':10,'FIELD_PRECISION':3,'NEW_FIELD':True,'FORMULA':' @row_number ','OUTPUT':workspace + r'/Hydropower/' + hydro_points + '_with_ID.shp'})
    processing.run("native:clip", {'INPUT':workspace + r'/Hydropower/' + hydro_points + '_with_ID.shp','OVERLAY':admin,'OUTPUT':workspace + r'/Hydropower/' + hydro_points + settlements_fc[0:3] +'.shp'})
    processing.run("native:reprojectlayer", {'INPUT':workspace + r'/Hydropower/' + hydro_points + settlements_fc[0:3] +'.shp','TARGET_CRS':projCord,'OUTPUT':workspace + r'/Hydropower/' + hydro_points + settlements_fc[0:3] +'_Proj.shp'})
    processing.run("qgis:distancetonearesthubpoints", {'INPUT':Pop,'HUBS':workspace + r'/Hydropower/' + hydro_points + settlements_fc[0:3] +'_Proj.shp','FIELD':'AUTO','UNIT':0,'OUTPUT':assistingFolder2 + r"\HydroFID_NO_ID.shp"})
    processing.run("qgis:distancetonearesthubpoints", {'INPUT':Pop,'HUBS':workspace + r'/Hydropower/' + hydro_points + settlements_fc[0:3] +'_Proj.shp','FIELD':hydropowerField,'UNIT':0,'OUTPUT': assistingFolder2 + r"\Hydropower_NO_ID.shp"})
    processing.run("qgis:fieldcalculator", {'INPUT':assistingFolder2 + r"\HydroFID_NO_ID.shp",'FIELD_NAME':'AUTO','FIELD_TYPE':0,'FIELD_LENGTH':10,'FIELD_PRECISION':3,'NEW_FIELD':True,'FORMULA':' @row_number ','OUTPUT':workspace + r"\Hydropower\hydrofid.shp"})
    processing.run("qgis:fieldcalculator", {'INPUT':assistingFolder2 + r"\Hydropower_NO_ID.shp",'FIELD_NAME':'AUTO','FIELD_TYPE':0,'FIELD_LENGTH':10,'FIELD_PRECISION':3,'NEW_FIELD':True,'FORMULA':' @row_number ','OUTPUT':workspace +r"\Hydropower\power.shp"})
    power = QgsVectorLayer(workspace +r"\Hydropower\power.shp","","ogr")
    hydrofid = QgsVectorLayer(workspace + r"\Hydropower\hydrofid.shp","","ogr")

    #Identify the field showing the hydropower
    field_ids = []
    fieldnames = set(['HubName', 'AUTO'])
    for field in power.fields():
        if field.name() not in fieldnames:
          field_ids.append(power.fields().indexFromName(field.name()))

    power.dataProvider().deleteAttributes(field_ids)
    power.updateFields()

    #Change fieldname to Hydropower
    for field in power.fields():
        if field.name() == 'HubName':
            with edit(power):
                idx =power.fields().indexFromName(field.name())
                power.renameAttribute(idx, 'Hydropower')

    #remove unecassary columns for hydrodist and hydrofid
    field_ids = []
    fieldnames = set(['HubName', 'HubDist', 'AUTO'])
    for field in hydrofid.fields():
        if field.name() not in fieldnames:
          field_ids.append(hydrofid.fields().indexFromName(field.name()))

    hydrofid.dataProvider().deleteAttributes(field_ids)
    hydrofid.updateFields()

    #Change fieldname to something appropriate for hydrodist and hydrofid
    for field in hydrofid.fields():
        if field.name() == 'HubName':
            with edit(hydrofid):
                idx = hydrofid.fields().indexFromName(field.name())
                hydrofid.renameAttribute(idx, 'HydropowerFID')
        elif field.name() == 'HubDist':
            with edit(hydrofid):
                idx =hydrofid.fields().indexFromName(field.name())
                hydrofid.renameAttribute(idx, 'HydropowerDist')

    # Existing transmission lines
    # 1. Clips and removes all vectors outside the admin raster
    # 2. Creates a point layer from the lines. Each point has a distance of 100 meters to the closes point
    # 3. Create a column with the name AUTO this is needed in order for all vector files to have at least one column in common
    # 4. Reprojects the vector layer
    # 5. Calculates the distance to nearest vector element for all the cells in the population layer (we need the name of a column and  we use the AUTO
    processing.run("native:clip", {'INPUT':workspace + r'/Transmission_Network/' + grid_existing + '.shp','OVERLAY':admin,'OUTPUT':workspace + r'/Transmission_Network/' + grid_existing + settlements_fc[0:3] +'.shp'})
    processing.run("saga:convertlinestopoints", {'LINES':workspace + r'/Transmission_Network/' + grid_existing + settlements_fc[0:3] +'.shp','ADD         ':True,'DIST':0.000833333333,'POINTS':workspace + r'/Transmission_Network/' + grid_existing + settlements_fc[0:3] +'Point.shp'})
    processing.run("qgis:fieldcalculator", {'INPUT':workspace + r'/Transmission_Network/' + grid_existing + settlements_fc[0:3] +'Point.shp','FIELD_NAME':'AUTO','FIELD_TYPE':0,'FIELD_LENGTH':10,'FIELD_PRECISION':3,'NEW_FIELD':True,'FORMULA':' @row_number ','OUTPUT':workspace + r'/Transmission_Network/' + grid_existing + 'Point_ID.shp'})
    processing.run("native:reprojectlayer", {'INPUT':workspace + r'/Transmission_Network/' + grid_existing + 'Point_ID.shp','TARGET_CRS':projCord,'OUTPUT':workspace + r'/Transmission_Network/' + grid_existing + 'Point_ID_Proj.shp'})
    processing.run("qgis:distancetonearesthubpoints", {'INPUT':Pop,'HUBS':workspace + r'/Transmission_Network/' + grid_existing + 'Point_ID_Proj.shp','FIELD':'AUTO','UNIT':0,'OUTPUT': assistingFolder2 +r"/griddistcurrent_NO_ID.shp"})
    processing.run("qgis:fieldcalculator", {'INPUT':assistingFolder2 +r"/griddistcurrent_NO_ID.shp",'FIELD_NAME':'AUTO','FIELD_TYPE':0,'FIELD_LENGTH':10,'FIELD_PRECISION':3,'NEW_FIELD':True,'FORMULA':' @row_number ','OUTPUT':workspace + r"\Transmission_Network\griddistcurrent.shp"})
    griddistcurrent = QgsVectorLayer(workspace + r"\Transmission_Network\griddistcurrent.shp","","ogr")

    # Identify the field showing the griddist
    field_ids = []
    fieldnames = set(['HubDist', 'AUTO'])
    for field in griddistcurrent.fields():
        if field.name() not in fieldnames:
          field_ids.append(griddistcurrent.fields().indexFromName(field.name()))

    griddistcurrent.dataProvider().deleteAttributes(field_ids)
    griddistcurrent.updateFields()

    #Change fieldname to griddistcurrent
    for field in griddistcurrent.fields():
        if field.name() == 'HubDist':
            with edit(griddistcurrent):
                idx = griddistcurrent.fields().indexFromName(field.name())
                griddistcurrent.renameAttribute(idx, 'GridDistCurrent')

    #Planned Grid
    # 1. Merge current and planned grid
    # 2. Clips and removes all vectors outside the admin raster
    # 3. Creates a point layer from the lines. Each point has a distance of 100 meters to the closes point
    # 4. Create a column with the name AUTO this is needed in order for all vector files to have at least one column in common
    # 5. Reprojects the vector layer
    # 6. Calculates the distance to nearest vector element for all the cells in the population layer (we need the name of a column and we use the AUTO
    processing.run("native:mergevectorlayers", {'LAYERS':[workspace + r'/Transmission_Network/' + grid_planned + '.shp',workspace + r'/Transmission_Network/' + grid_existing + settlements_fc[0:3] +'.shp'],'CRS':None,'OUTPUT':workspace + r'/Transmission_Network/' + grid_planned + '_Merged.shp'})
    processing.run("native:clip", {'INPUT':workspace + r'/Transmission_Network/' + grid_planned + '_Merged.shp','OVERLAY':admin,'OUTPUT':workspace + r'/Transmission_Network/' + grid_planned + settlements_fc[0:3] +'.shp'})
    processing.run("saga:convertlinestopoints", {'LINES':workspace + r'/Transmission_Network/' + grid_planned + settlements_fc[0:3] +'.shp','ADD         ':True,'DIST':0.000833333333,'POINTS':workspace + r'/Transmission_Network/' + grid_planned + settlements_fc[0:3] +'Point.shp'})
    processing.run("qgis:fieldcalculator", {'INPUT':workspace + r'/Transmission_Network/' + grid_planned + settlements_fc[0:3] +'Point.shp','FIELD_NAME':'AUTO','FIELD_TYPE':0,'FIELD_LENGTH':10,'FIELD_PRECISION':3,'NEW_FIELD':True,'FORMULA':' @row_number ','OUTPUT':workspace + r'/Transmission_Network/' + grid_planned + 'Point_ID.shp'})
    processing.run("native:reprojectlayer", {'INPUT':workspace + r'/Transmission_Network/' + grid_planned + 'Point_ID.shp','TARGET_CRS':projCord,'OUTPUT':workspace + r'/Transmission_Network/' + grid_planned + 'Point_ID_Proj.shp'})
    processing.run("qgis:distancetonearesthubpoints", {'INPUT':Pop,'HUBS':workspace + r'/Transmission_Network/' + grid_planned + 'Point_ID_Proj.shp','FIELD':'AUTO','UNIT':0,'OUTPUT':assistingFolder2 + r"\griddistplanned_NO_ID.shp"})
    processing.run("qgis:fieldcalculator", {'INPUT':assistingFolder2 + r"\griddistplanned_NO_ID.shp",'FIELD_NAME':'AUTO','FIELD_TYPE':0,'FIELD_LENGTH':10,'FIELD_PRECISION':3,'NEW_FIELD':True,'FORMULA':' @row_number ','OUTPUT':workspace + r"\Transmission_Network\griddistplanned.shp"})
    griddistplanned = QgsVectorLayer(workspace + r"\Transmission_Network\griddistplanned.shp","", "ogr")

    # Identify the field showing the griddist
    field_ids = []
    fieldnames = set(['HubDist','AUTO'])
    for field in griddistplanned.fields():
        if field.name() not in fieldnames:
          field_ids.append(griddistplanned.fields().indexFromName(field.name()))

    griddistplanned.dataProvider().deleteAttributes(field_ids)
    griddistplanned.updateFields()

    #Change fieldname to griddistplanned
    for field in griddistplanned.fields():
        if field.name() == 'HubDist':
            with edit(griddistplanned):
                idx = griddistplanned.fields().indexFromName(field.name())
                griddistplanned.renameAttribute(idx, 'GridDistPlanned')


    # Roads
    # 1. Clips and removes all vectors outside the admin raster
    # 2. Creates a point layer from the lines. Each point has a distance of 100 meters to the closes point
    # 3. Create a column with the name AUTO this is needed in order for all vector files to have at least one column in common
    # 4. Reprojects the vector layer
    # 5. Calculates the distance to nearest vector element for all the cells in the population layer (we need the name of a column and we use the AUTO
    processing.run("native:clip", {'INPUT':workspace + r'/Roads/' + roads + '.shp','OVERLAY':admin,'OUTPUT':workspace + r'/Roads/' + roads + settlements_fc[0:3] +'.shp'})
    processing.run("saga:convertlinestopoints", {'LINES':workspace + r'/Roads/' + roads + settlements_fc[0:3] +'.shp','ADD         ':True,'DIST':0.000833333333,'POINTS':workspace + r'/Roads/' + roads + settlements_fc[0:3] +'Point.shp'})
    processing.run("qgis:fieldcalculator", {'INPUT':workspace + r'/Roads/' + roads + settlements_fc[0:3] +'Point.shp','FIELD_NAME':'AUTO','FIELD_TYPE':0,'FIELD_LENGTH':10,'FIELD_PRECISION':3,'NEW_FIELD':True,'FORMULA':' @row_number ','OUTPUT':workspace + r'/Roads/' + roads + '_with_ID.shp'})
    processing.run("native:reprojectlayer", {'INPUT':workspace + r'/Roads/' + roads + '_with_ID.shp','TARGET_CRS':projCord,'OUTPUT':workspace + r'/Roads/' + roads + 'Point_ID_Proj.shp'})
    processing.run("qgis:distancetonearesthubpoints", {'INPUT':Pop,'HUBS':workspace + r'/Roads/' + roads + 'Point_ID_Proj.shp','FIELD':'AUTO','UNIT':0,'OUTPUT':assistingFolder2 + r"\roaddist_NO_ID.shp"})
    processing.run("qgis:fieldcalculator", {'INPUT':assistingFolder2 + r"\roaddist_NO_ID.shp",'FIELD_NAME':'AUTO','FIELD_TYPE':0,'FIELD_LENGTH':10,'FIELD_PRECISION':3,'NEW_FIELD':True,'FORMULA':' @row_number ','OUTPUT':workspace + r"\Roads\roaddist.shp"})
    roaddist = QgsVectorLayer(workspace + r"\Roads\roaddist.shp", "", "ogr")

    # Identify the field showing the roaddist
    field_ids = []
    fieldnames = set(['HubDist', 'AUTO'])
    for field in roaddist.fields():
        if field.name() not in fieldnames:
          field_ids.append(roaddist.fields().indexFromName(field.name()))

    roaddist.dataProvider().deleteAttributes(field_ids)
    roaddist.updateFields()

    #Change fieldname to something RoadDist
    for field in roaddist.fields():
        if field.name() == 'HubDist':
            with edit(roaddist):
                idx = roaddist.fields().indexFromName(field.name())
                roaddist.renameAttribute(idx, 'RoadDist')

    # We add every vector to the settlemnt file created above one vector at a time using the coordinates as identifier
    iter1=processing.run("native:joinattributestable", {'INPUT': settlement,'FIELD':'AUTO','INPUT_2':substationsdist,'FIELD_2':'AUTO','FIELDS_TO_COPY':[],'METHOD':1,'DISCARD_NONMATCHING':False,'PREFIX':'','OUTPUT':assistingFolder + r"\iter1.shp"})
    iter2=processing.run("native:joinattributestable", {'INPUT': assistingFolder + r"\iter1.shp",'FIELD':'AUTO','INPUT_2':roaddist,'FIELD_2':'AUTO','FIELDS_TO_COPY':[],'METHOD':1,'DISCARD_NONMATCHING':False,'PREFIX':'','OUTPUT':assistingFolder + r"\iter2.shp"})
    iter3=processing.run("native:joinattributestable", {'INPUT': assistingFolder + r"\iter2.shp",'FIELD':'AUTO','INPUT_2':griddistcurrent,'FIELD_2':'AUTO','FIELDS_TO_COPY':[],'METHOD':1,'DISCARD_NONMATCHING':False,'PREFIX':'','OUTPUT':assistingFolder + r"\iter3.shp"})
    iter4=processing.run("native:joinattributestable", {'INPUT': assistingFolder + r"\iter3.shp",'FIELD':'AUTO','INPUT_2':griddistplanned,'FIELD_2':'AUTO','FIELDS_TO_COPY':[],'METHOD':1,'DISCARD_NONMATCHING':False,'PREFIX':'','OUTPUT':assistingFolder + r"\iter4.shp"})
    iter5=processing.run("native:joinattributestable", {'INPUT': assistingFolder + r"\iter4.shp",'FIELD':'AUTO','INPUT_2':power,'FIELD_2':'AUTO','FIELDS_TO_COPY':[],'METHOD':1,'DISCARD_NONMATCHING':False,'PREFIX':'','OUTPUT':assistingFolder + r"\iter5.shp"})
    iter6=processing.run("native:joinattributestable", {'INPUT': assistingFolder + r"\iter5.shp",'FIELD':'AUTO','INPUT_2':hydrofid,'FIELD_2':'AUTO','FIELDS_TO_COPY':[],'METHOD':1,'DISCARD_NONMATCHING':False,'PREFIX':'','OUTPUT':assistingFolder + r"\iter6.shp"})

    # Add coordinates to the settlementfile
    processing.run("saga:addcoordinatestopoints", {'INPUT':assistingFolder + r"\iter6.shp",'OUTPUT':assistingFolder +r'/' + settlements_fc + '.shp'})
    settlements = QgsVectorLayer(assistingFolder + r'/' + settlements_fc + '.shp',"","ogr")

    # Identify all the fileds that we are interested in
    field_ids = []
    fieldnames = set(['X','Y','pop2015' + settlements_fc[0:3],'elevation','landcover','nightlight','slope','solar','solarrestr','traveltime','windvel','Substation','RoadDist','GridDistCu','GridDistPl','Hydropower','Hydropow_1','Hydropow_2'])
    for field in settlements.fields():
         if field.name() not in fieldnames:
           field_ids.append(settlements.fields().indexFromName(field.name()))

    # Remove all others
    settlements.dataProvider().deleteAttributes(field_ids)
    settlements.updateFields()

    # Save as a csv file
    settlements.setName(settlements_fc)
    QgsVectorFileWriter.writeAsVectorFormat(settlements, workspace + r"/" + settlements_fc + ".csv", "utf-8", settlements.crs(), "CSV")


.. note::

   A fully updated version of this code is available `here <https://github.com/KTH-dESA/PyOnSSET/tree/master/Resource_Assessment/Python_Commands_For_Processing_GIS_Data>`_.
   

.. note::
    In order to run the code in QGIS certain things need to be set up properly. In the following steps these things will be described. **NOTE** it is possible to set things up differently, but if this is done then the code will most likely need changes as well. 
    
    **1. Setting up the workspace**
    When all of the datasets have been generated and projected to a common projection system they need to be saved in appropriate folders before running the code. The image below shows an image of the workspace necessary for the analysis, these folders need to be set up accordingly and filled in with the corresponding datasets. 
    
    .. image:: img/Workspace.png
        :width: 300
        :height: 200
        :align: center
    
    To run a basic OnSSET analysis you will need 14 datasets. These 14 datasets should be saved in their corresponding folder. Two of the datasets (planned and existing transmission lines) should both be saved in the transmission network folder. The slope map will be generated in the code using the elevation map and therefore there is no need to download it. The datasets needed are: 
   
    .. image:: img/DatasetNames.png
        :width: 300
        :height: 200
        :align: center
        
    **Please make sure that the datasets are named exactly as they are in the column named “Data” and that the folders are named as in the column “Corresponding Folder”**.
   
   **2. Additional concerns**
       *1.*	In line 14 make sure that the link to the workspace is correct (remember: the workspace is where the folders with the                   datasets are located). Make sure the path does not include any special characters or spaces as this could potentially                   cause errors.
                .. image:: img/Line14.png
                    :width: 300
                    :height: 200
                    :align: center
       *2.*  In line 17 make sure that you enter the coordinate system that you want to project your datasets to. The datasets used                   in the analysis are often in a default coordinate system (e.g. WGS 84) if you wish to change that you can enter the EPSG               code of your target coordinate system (remember to include the “EPSG” part if that is included in the code).
               .. image:: img/Line17.png
                    :width: 300
                    :height: 200
                    :align: center
       *3.*  In line 20 put settlements_fc equal to your study area. Whatever you put here will be the name of your output file from                 the code.
                .. image:: img/Line20.png
                    :width: 300
                    :height: 200
                    :align: center
       
       *4.*  In line 24 you might have to change the column name. In order to determine the amount of hydropower in all the                           potential points QGIS needs to know the name of the column in which the hydropower potential is given (open the attribute               table of your dataset and write down the name of the column that contains the potential outputs).
                .. image:: img/Line24.png
                    :width: 300
                    :height: 200
                    :align: center
                    
    **3. Running the code**
    
    1.	Open QGIS 
    2.	Open the python console 
         .. image:: img/step2.png
              :width: 300
              :height: 200
              :align: center
                    
    3.	This will open up the python console in QGIS. In here you can write commands and run different tools included in QGIS.
    
          .. image:: img/step3.png
              :width: 300
              :height: 200
              :align: center
 
    4.	By clicking on “Show editor” (marked in red in the image below). You will open up the editor window of the python version           following with your installation of QGIS. 
 
         .. image:: img/step4.png
              :width: 300
              :height: 200
              :align: center
    5.	In the editor you can write and run your own python scripts. In order to run the extraction code copy and paste it into this        window.
            
         .. image:: img/step5.png
              :width: 300
              :height: 200
              :align: center

    6.	When the code is pasted in you can finally run the code. Do so by clicking on the blue play button at the top of the screen.
        
         .. image:: img/step6.png
              :width: 300
              :height: 200
              :align: center

    7.	After running the code you will see that two new folders have been added to your workspace; Assist and Assist2. In the Assist       folder there will be a csv with the same name as you specified in settlements_fc. This file includes some empty rows and hence it       still needs conditioning in order to work with OnSSET. 
 
         .. image:: img/step7a.png
              :width: 300
              :height: 200
              :align: center
              
         .. image:: img/step7b.PNG
              :width: 300
              :height: 200
              :align: center

**Step 5. Conditioning** 
---------------------------------------------------
If you after the previous step open the CSV file you will see that some of the columns have names that do not make sense. Additionally three of the columns; nighttime lights, solar restrictions and landcover; all have empty rows. These empty rows are supposed to have the value zero. This problems can be dealt manually, but to facilitate the process KTH-dESA has developed a python code named **Conditioning** that automates the process.
This code is avaiable `here <https://github.com/KTH-dESA/PyOnSSET/tree/master/Resource_Assessment/Conditioning>`_. 

.. note::
    Depending on the name of the datasets that you use the renaming part might have to be altered. Also make sure that the code is tailored towards your study i.e. make sure that the settlement layer has the right name and that the workspace variable is pointing to the right directory etc. 


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
