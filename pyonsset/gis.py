# Functions to create a settlements feature class, export it, and re-import a process csv
#
# Author: Christopher Arderne
# Date: 26 November 2016
# Python version: 2.7

from __future__ import absolute_import, division, print_function
import logging
import arcpy
import csv
from pyonsset.constants import *
import os
import errno

logging.basicConfig(format='%(asctime)s\t\t%(message)s', level=logging.DEBUG)


def create(gdb='C:/Users/adm.esa/Desktop/ONSSET/Africa_Onsset.gdb', settlements_fc='settlements'):
    """
    Create a new settlements layer from all the required layers.

    @param gdb: the ARcGIS geodatabase holding the layers
    @param settlements_fc: a name for the new settlements layer
    """

    logging.info('Starting function gis.create()')

    arcpy.env.workspace = gdb
    arcpy.env.overwriteOutput = True
    arcpy.env.addOutputsToMap = False
    arcpy.CheckOutExtension("Spatial")

    pop = 'pop2010'  # Type: raster, Unit: people per km2, must be in resolution 1km x 1km
    ghi = 'ghi'  # Type: raster, Unit: kWh/m2/day
    windvel = 'windvel'  # Type: raster, Unit: capacity factor as a percentage (range 0 - 1)
    travel = 'travelhours'  # Type: raster, Unit: hours
    grid_existing = 'grid_existing'  # Type: shapefile (line)
    grid_planned = 'grid_planned'  # Type: shapefile (line)
    hydro_points = 'hydropoints'  # Type: shapefile (points), Unit: kW (field must be named Hydropower)
    admin_raster = 'admin_raster'  # Type: raster, country names must conform to specs.xlsx file
    roads = 'roads'  # Type: shapefile (lines)
    nightlights = 'nightlights'  # Type: raster, Unit: (range 0 - 63)
    substations = 'substations'
    elevation = 'elevation'
    slope = 'slope'
    land_cover = 'landcover'
    solar_restriction = 'solar_restriction'

    # Starting point
    logging.info('Create settlements layer')
    arcpy.RasterToPoint_conversion(pop, settlements_fc)
    arcpy.AlterField_management(settlements_fc, 'grid_code', SET_POP, SET_POP)

    # Country names
    # Has to be done with a raster -- trying with a shapefile ran out of memory and crashed
    # Thus the names have to be added after with a Join
    logging.info('Add country names')
    country_num = 'CountryNum'
    arcpy.sa.ExtractMultiValuesToPoints(settlements_fc, [[admin_raster, country_num]])
    arcpy.JoinField_management(settlements_fc, country_num, admin_raster, 'Value', SET_COUNTRY)
    arcpy.DeleteField_management(settlements_fc, country_num)

    # Add X and Y values
    # They are converted from metres to kilometres in this process
    logging.info('Add X/Y values')
    arcpy.AddXY_management(settlements_fc)
    arcpy.AddField_management(settlements_fc, SET_X, 'FLOAT')
    arcpy.CalculateField_management(settlements_fc, SET_X, '!POINT_X! / 1000', 'PYTHON_9.3')
    arcpy.AddField_management(settlements_fc, SET_Y, 'FLOAT')
    arcpy.CalculateField_management(settlements_fc, SET_Y, '!POINT_Y! / 1000', 'PYTHON_9.3')
    arcpy.DeleteField_management(settlements_fc, 'POINT_X; POINT_Y')

    # Add GHI, WindCF, travel, nightlights
    logging.info('Add GHI')
    arcpy.sa.ExtractMultiValuesToPoints(settlements_fc, [[ghi, SET_GHI]])
    logging.info('Add Solar restriction')
    arcpy.sa.ExtractMultiValuesToPoints(settlements_fc, [[solar_restriction, SET_SOLAR_RESTRICTION]])
    logging.info('Add WindVel')
    arcpy.sa.ExtractMultiValuesToPoints(settlements_fc, [[windvel, SET_WINDVEL]])
    logging.info('Add Travel time')
    arcpy.sa.ExtractMultiValuesToPoints(settlements_fc, [[travel, SET_TRAVEL_HOURS]])
    logging.info('Add night lights')
    arcpy.sa.ExtractMultiValuesToPoints(settlements_fc, [[nightlights, SET_NIGHT_LIGHTS]])
    logging.info('Add elevation')
    arcpy.sa.ExtractMultiValuesToPoints(settlements_fc, [[elevation, SET_ELEVATION]])
    logging.info('Add slope')
    arcpy.sa.ExtractMultiValuesToPoints(settlements_fc, [[slope, SET_SLOPE]])
    logging.info('Add land cover')
    arcpy.sa.ExtractMultiValuesToPoints(settlements_fc, [[land_cover, SET_LAND_COVER]])

    # Each point's distance from the existing grid
    # Converted to kilometres
    logging.info('Add distance from existing grid')
    arcpy.Near_analysis(settlements_fc, grid_existing)
    arcpy.AddField_management(settlements_fc, SET_GRID_DIST_CURRENT, 'FLOAT')
    arcpy.CalculateField_management(settlements_fc, SET_GRID_DIST_CURRENT, '!NEAR_DIST! / 1000', 'PYTHON_9.3')
    arcpy.DeleteField_management(settlements_fc, 'NEAR_DIST; NEAR_FID')

    # Each point's distance from either grid
    # Converted to kilometres
    logging.info('Add distance from either grid')
    arcpy.Near_analysis(settlements_fc, [grid_existing, grid_planned])
    arcpy.AddField_management(settlements_fc, SET_GRID_DIST_PLANNED, 'FLOAT')
    arcpy.CalculateField_management(settlements_fc, SET_GRID_DIST_PLANNED, '!NEAR_DIST! / 1000', 'PYTHON_9.3')
    arcpy.DeleteField_management(settlements_fc, 'NEAR_DIST; NEAR_FID; NEAR_FC')

    # Each point's distance from substations
    # Converted to kilometres
    logging.info('Add distance from substations')
    arcpy.Near_analysis(settlements_fc, substations)
    arcpy.AddField_management(settlements_fc, SET_SUBSTATION_DIST, 'FLOAT')
    arcpy.CalculateField_management(settlements_fc, SET_SUBSTATION_DIST, '!NEAR_DIST! / 1000', 'PYTHON_9.3')
    arcpy.DeleteField_management(settlements_fc, 'NEAR_DIST; NEAR_FID; NEAR_FC')

    # Add roaddist
    # Converted to kilometres
    logging.info('Add road dist')
    arcpy.Near_analysis(settlements_fc, roads)
    arcpy.AddField_management(settlements_fc, SET_ROAD_DIST, 'FLOAT')
    arcpy.CalculateField_management(settlements_fc, SET_ROAD_DIST, '!NEAR_DIST! / 1000', 'PYTHON_9.3')
    arcpy.DeleteField_management(settlements_fc, 'NEAR_DIST; NEAR_FID')

    # Add hydropower points
    # The distance is converted to kilometres
    # Important that the hydropower field is named exactly matching SET_HYDRO
    logging.info('Add hydropower and hydropower distance')
    arcpy.Near_analysis(settlements_fc, hydro_points)
    arcpy.AddField_management(settlements_fc, SET_HYDRO_DIST, 'FLOAT')
    arcpy.CalculateField_management(settlements_fc, SET_HYDRO_DIST, '!NEAR_DIST! / 1000', 'PYTHON_9.3')
    arcpy.JoinField_management(settlements_fc, 'NEAR_FID', hydro_points,
                               arcpy.Describe(hydro_points).OIDFieldName, [SET_HYDRO])
    arcpy.DeleteField_management(settlements_fc, 'NEAR_DIST; NEAR_FID')
    logging.info('Completed function gis.create()')


def export_csv(gdb=r'C:\Users\adm.esa\Desktop\ONSSET\Onsset_Layers.gdb', settlements_fc='settlements', out_file='db/settlements.csv'):
    """
    Export a settlements feature class to a csv file that can be used by pandas.

    @param gdb: the ARcGIS geodatabase holding the layers
    @param settlements_fc: a name for the new settlements layer
    """

    logging.info('Starting function gis.export_csv()...')

    arcpy.env.workspace = gdb

    try:
        os.makedirs(os.path.dirname(out_file))
    except OSError as e:
        if e.errno == errno.EEXIST:
            print('Directory not created.')
        else:
            raise

    # Skips the first two elements (OBJECT_ID and Shape)
    field_list = [f.name for f in arcpy.ListFields(settlements_fc)[2:]]

    logging.info('Writing output...')
    with open(out_file, 'w') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=',', lineterminator='\n')
        csvwriter.writerow(field_list)

        with arcpy.da.SearchCursor(settlements_fc, field_list) as cursor:
            for row in cursor:
                csvwriter.writerow(row)

    logging.info('Completed function gis.export_csv()')


def import_csv(in_file, out_fc, gdb=r'C:\Users\adm.esa\Desktop\ONSSET\Onsset_Results_13Sep.gdb'):
    """
    Import the csv file designated by scenario, selection and diesel_high back into ArcGIS.
    The columns with locations in degrees (not metres!) must be labelled X and Y

    @param scenario: The scenario target in kWh/hh/year
    @param selection: The country or subset to import
    @param diesel_high: Whether to use the high diesel table
    @param gdb: The geodatabase where the result should be saved
    """

    logging.info('Starting function gis.import_csv()...')

    # Set up the ArcGIS environment options and create a new feature class
    arcpy.env.workspace = gdb
    arcpy.env.overwriteOutput = True
    arcpy.env.addOutputsToMap = False
    arcpy.CheckOutExtension("Spatial")

    # Open the csv file and copy the field names (first row)
    csvreader = csv.reader(open(in_file, 'r'), delimiter=',', lineterminator='\n')
    fields = next(csvreader)  # The first line in the csv file contains the field names

    # We only create the feature class once we've confirmed that the csv exists
    arcpy.CreateFeatureclass_management(arcpy.env.workspace, out_fc, "POINT")
    arcpy.DefineProjection_management(out_fc, arcpy.SpatialReference('WGS 1984'))

    # Add a sample row (to set the field types in ArcGIS)
    # For all the fields that are floatable, make the field a FLOAT, otherwise TEXT
    # If any element is blank (it equals '') then try the operation again with the next row, as '' isn't floatable
    field_types = []
    while True:
        sample_row = next(csvreader)
        field_types = []

        for i, f in enumerate(fields):
            if sample_row[i] == '':
                continue

            try:
                float(sample_row[i])
                field_type = 'FLOAT'
            except ValueError:
                field_type = 'TEXT'
            field_types.append(field_type)
            arcpy.AddField_management(out_fc, f, field_type)
        break

    # Reset the csvreader and skip the first row
    csvreader = csv.reader(open(in_file, 'r'), delimiter=',', lineterminator='\n')
    next(csvreader)
    # Add the X and Y fields so that ArcGIS recognises them as as the coordinates
    fields.append('SHAPE@X')
    fields.append('SHAPE@Y')

    # Insert the rows one at a time, converting to float or string as appropriate
    # The prev variable is just to know when a new country is starting to it can be reported
    prev = None
    with arcpy.da.InsertCursor(out_fc, fields) as cursor:
        for row in csvreader:
            rowf = []

            x, y = 0.0, 0.0
            for i, r in enumerate(row):
                if fields[i] == 'X':
                    x = float(r)
                    rowf.append(x)
                elif fields[i] == 'Y':
                    y = float(r)
                    rowf.append(y)

                elif field_types[i] == 'FLOAT':
                    try:
                        rowf.append(float(r))
                    except ValueError:
                        rowf.append(0.0)
                else:
                    rowf.append(str(r))

            rowf.append(x)
            rowf.append(y)
            cursor.insertRow(rowf)
            if rowf[2] != prev:
                logging.info('Doing {}'.format(rowf[2]))
            prev = rowf[2]

    logging.info('Completed function gis.import_csv()')


if __name__ == "__main__":
    print(0)
    #gdb = r'C:\Users\adm.esa\Desktop\ONSSET\output_12Nov.gdb'
    #in_f = r'C:\Users\adm.esa\Desktop\ONSSET\PyOnSSET\db\run_12Nov\_Africa_combined.csv'
    #fc = 'africa12nov'
    #import_csv(in_f, fc, gdb)

    #gdb = r'C:\Users\adm.esa\Documents\ArcGIS\Default.gdb'
    #in_featureclass = 'africa100km2_COUNTRIES'
    #out_csv = r'C:\Users\adm.esa\Desktop\ONSSET\PyOnSSET\db/africa100km2.csv'
    #export_csv(gdb, in_featureclass, out_csv)