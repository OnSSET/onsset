import os
import arcpy
import csv
from pyonsset.constants import *

def create():
    arcpy.env.workspace = r'C:\Users\adm.esa\Desktop\ONSSET\Africa_Onsset.gdb'
    arcpy.env.overwriteOutput = True
    arcpy.env.addOutputsToMap = False
    arcpy.CheckOutExtension("Spatial")

    settlements = 'settlements_1km2'
    pop = 'pop2010_clipped'
    ghi = 'ghi' # per day values
    windcf = 'windcf'
    travel = 'travelhours' # time in minutes
    gridExisting = 'grid_existing'
    gridPlanned = 'grid_planned'
    hydro_points = 'hydropoints' # with Hydropower field in MW
    admin_raster = 'admin_raster'
    roads = 'roads'
    nightlights = 'nightlights'

    #starting point
    arcpy.RasterToPoint_conversion(pop, settlements)

    #country names
    arcpy.sa.ExtractMultiValuesToPoints(settlements, [[admin_raster, 'CountryNum']])
    arcpy.JoinField_management(settlements, 'CountryNum', admin_raster, 'Value', SET_COUNTRY)
    arcpy.DeleteField_management(settlements, 'CountryNum')

    # add X and Y values in km
    arcpy.AddXY_management(settlements)
    arcpy.AddField_management(settlements, SET_X, 'FLOAT')
    arcpy.CalculateField_management(settlements, SET_X, '!POINT_X! / 1000', 'PYTHON_9.3')
    arcpy.AddField_management(settlements, SET_Y, 'FLOAT')
    arcpy.CalculateField_management(settlements, SET_Y, '!POINT_Y! / 1000', 'PYTHON_9.3')
    arcpy.DeleteField_management(settlements, 'POINT_X; POINT_Y')

    # ghi, windcf, travel, nightlights
    arcpy.sa.ExtractMultiValuesToPoints(settlements, [[ghi, SET_GHI]])
    arcpy.sa.ExtractMultiValuesToPoints(settlements, [[windcf, SET_WINDCF]])
    arcpy.sa.ExtractMultiValuesToPoints(settlements, [[travel, SET_TRAVEL_HOURS]])
    arcpy.sa.ExtractMultiValuesToPoints(settlements, [[nightlights, SET_NIGHT_LIGHTS]])

    # each point's distance from the existing grid
    arcpy.Near_analysis(settlements, gridExisting)
    arcpy.AddField_management(settlements, SET_GRID_DIST_CURRENT, 'FLOAT')
    arcpy.CalculateField_management(settlements, SET_GRID_DIST_CURRENT, '!NEAR_DIST! / 1000', 'PYTHON_9.3')
    arcpy.DeleteField_management(settlements, 'NEAR_DIST; NEAR_FID')

    # each point's distance from either grid
    arcpy.Near_analysis(settlements, [gridExisting, gridPlanned])
    arcpy.AddField_management(settlements, SET_GRID_DIST_PLANNED, 'FLOAT')
    arcpy.CalculateField_management(settlements, SET_GRID_DIST_PLANNED, '!NEAR_DIST! / 1000', 'PYTHON_9.3')
    arcpy.DeleteField_management(settlements, 'NEAR_DIST; NEAR_FID; NEAR_FC')

    # Add roaddist
    arcpy.Near_analysis(settlements, roads)
    arcpy.AddField_management(settlements, SET_ROAD_DIST, 'FLOAT')
    arcpy.CalculateField_management(settlements, SET_ROAD_DIST, '!NEAR_DIST! / 1000', 'PYTHON_9.3')
    arcpy.DeleteField_management(settlements, 'NEAR_DIST; NEAR_FID')

    # Add hydropower points to settlements
    arcpy.Near_analysis(settlements, hydro_points)
    arcpy.AddField_management(settlements, SET_HYDRO_DIST, 'FLOAT')
    arcpy.CalculateField_management(settlements, SET_HYDRO_DIST, '!NEAR_DIST! / 1000', 'PYTHON_9.3')
    arcpy.JoinField_management(settlements, 'NEAR_FID', hydro_points,arcpy.Describe(hydro_points).OIDFieldName, [SET_HYDRO])
    arcpy.DeleteField_management(settlements, 'NEAR_DIST; NEAR_FID')

def export_csv(settlements):
    settlements = r'C:/Users/adm.esa/Desktop/ONSSET/Africa_Onsset.gdb/settlements_1km2'
    settlements_csv = os.path.join('Tables', settlements + '.csv')

    field_list = [SET_COUNTRY, SET_X, SET_Y, SET_POP, SET_GRID_DIST_CURRENT,
                  SET_GRID_DIST_PLANNED, SET_ROAD_DIST, SET_NIGHT_LIGHTS, SET_TRAVEL_HOURS,
                  SET_GHI, SET_WINDCF, SET_HYDRO, SET_HYDRO_DIST]

    with open(settlements_csv, 'w') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=',', lineterminator='\n')
        csvwriter.writerow(field_list)

        with arcpy.da.SearchCursor(settlements, field_list) as cursor:
            for row in cursor:
                csvwriter.writerow(row)

def import_csv(scenario, diesel_high, settlements, gdb, shapefile):
    output_dir = r'C:\Users\arderne\Work\Onsset\PyOnSSET\Tables\scenario{}'.format(scenario)
    if diesel_high:
        settlements_csv = os.path.join(output_dir, settlements + '-high.csv')
    else:
        settlements_csv = os.path.join(output_dir, settlements + '-low.csv')

    arcpy.env.workspace = gdb
    arcpy.env.overwriteOutput = True
    arcpy.env.addOutputsToMap = False
    arcpy.CheckOutExtension("Spatial")

    arcpy.CreateFeatureclass_management(arcpy.env.workspace, shapefile, "POINT")
    csvreader = csv.reader(open(settlements_csv, 'r'), delimiter=',', lineterminator='\n')

    fields = next(csvreader)
    heads = fields[:]
    fields[1] = 'SHAPE@X'
    fields[2] = 'SHAPE@Y'
    first_row = next(csvreader)
    csvreader = csv.reader(open(settlements_csv, 'r'), delimiter=',', lineterminator='\n')
    next(csvreader)

    types = []
    for i, h in enumerate(heads):
        try:
            float(first_row[i])
            type = 'FLOAT'
        except ValueError:
            type = 'TEXT'
        types.append(type)
        arcpy.AddField_management(shapefile, h, type)

    prev = None
    with arcpy.da.InsertCursor(shapefile, fields) as cursor:
        for row in csvreader:
            rowf = []

            for i, r in enumerate(row):
                if types[i] == 'FLOAT':
                    try:
                        rowf.append(float(r))
                    except:
                        rowf.append(0.0)
                else:
                    rowf.append(str(r))

            cursor.insertRow(rowf)
            if rowf[0] != prev: print(rowf[0])
            prev = rowf[0]