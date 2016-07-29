import os
import arcpy
import csv
from pyonsset.constants import *

def create(gdb, settlements_fc):
    arcpy.env.workspace = gdb
    arcpy.env.overwriteOutput = True
    arcpy.env.addOutputsToMap = False
    arcpy.CheckOutExtension("Spatial")

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
    arcpy.RasterToPoint_conversion(pop, settlements_fc)

    #country names
    arcpy.sa.ExtractMultiValuesToPoints(settlements_fc, [[admin_raster, 'CountryNum']])
    arcpy.JoinField_management(settlements_fc, 'CountryNum', admin_raster, 'Value', SET_COUNTRY)
    arcpy.DeleteField_management(settlements_fc, 'CountryNum')

    # add X and Y values in km
    arcpy.AddXY_management(settlements_fc)
    arcpy.AddField_management(settlements_fc, SET_X, 'FLOAT')
    arcpy.CalculateField_management(settlements_fc, SET_X, '!POINT_X! / 1000', 'PYTHON_9.3')
    arcpy.AddField_management(settlements_fc, SET_Y, 'FLOAT')
    arcpy.CalculateField_management(settlements_fc, SET_Y, '!POINT_Y! / 1000', 'PYTHON_9.3')
    arcpy.DeleteField_management(settlements_fc, 'POINT_X; POINT_Y')

    # ghi, windcf, travel, nightlights
    arcpy.sa.ExtractMultiValuesToPoints(settlements_fc, [[ghi, SET_GHI]])
    arcpy.sa.ExtractMultiValuesToPoints(settlements_fc, [[windcf, SET_WINDCF]])
    arcpy.sa.ExtractMultiValuesToPoints(settlements_fc, [[travel, SET_TRAVEL_HOURS]])
    arcpy.sa.ExtractMultiValuesToPoints(settlements_fc, [[nightlights, SET_NIGHT_LIGHTS]])

    # each point's distance from the existing grid
    arcpy.Near_analysis(settlements_fc, gridExisting)
    arcpy.AddField_management(settlements_fc, SET_GRID_DIST_CURRENT, 'FLOAT')
    arcpy.CalculateField_management(settlements_fc, SET_GRID_DIST_CURRENT, '!NEAR_DIST! / 1000', 'PYTHON_9.3')
    arcpy.DeleteField_management(settlements_fc, 'NEAR_DIST; NEAR_FID')

    # each point's distance from either grid
    arcpy.Near_analysis(settlements_fc, [gridExisting, gridPlanned])
    arcpy.AddField_management(settlements_fc, SET_GRID_DIST_PLANNED, 'FLOAT')
    arcpy.CalculateField_management(settlements_fc, SET_GRID_DIST_PLANNED, '!NEAR_DIST! / 1000', 'PYTHON_9.3')
    arcpy.DeleteField_management(settlements_fc, 'NEAR_DIST; NEAR_FID; NEAR_FC')

    # Add roaddist
    arcpy.Near_analysis(settlements_fc, roads)
    arcpy.AddField_management(settlements_fc, SET_ROAD_DIST, 'FLOAT')
    arcpy.CalculateField_management(settlements_fc, SET_ROAD_DIST, '!NEAR_DIST! / 1000', 'PYTHON_9.3')
    arcpy.DeleteField_management(settlements_fc, 'NEAR_DIST; NEAR_FID')

    # Add hydropower points
    arcpy.Near_analysis(settlements_fc, hydro_points)
    arcpy.AddField_management(settlements_fc, SET_HYDRO_DIST, 'FLOAT')
    arcpy.CalculateField_management(settlements_fc, SET_HYDRO_DIST, '!NEAR_DIST! / 1000', 'PYTHON_9.3')
    arcpy.JoinField_management(settlements_fc, 'NEAR_FID', hydro_points,arcpy.Describe(hydro_points).OIDFieldName, [SET_HYDRO])
    arcpy.DeleteField_management(settlements_fc, 'NEAR_DIST; NEAR_FID')

def export_csv(gdb, settlements_fc, settlements):
    arcpy.env.workspace = gdb
    settlements_csv = os.path.join('Tables', settlements + '.csv')

    field_list = [SET_COUNTRY, SET_X, SET_Y, SET_POP, SET_GRID_DIST_CURRENT,
                  SET_GRID_DIST_PLANNED, SET_ROAD_DIST, SET_NIGHT_LIGHTS, SET_TRAVEL_HOURS,
                  SET_GHI, SET_WINDCF, SET_HYDRO, SET_HYDRO_DIST]

    with open(settlements_csv, 'w') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=',', lineterminator='\n')
        csvwriter.writerow(field_list)

        with arcpy.da.SearchCursor(settlements_fc, field_list) as cursor:
            for row in cursor:
                csvwriter.writerow(row)

def import_csv(scenario, diesel_high, settlements, gdb, settlements_fc):
    output_dir = r'C:\Users\arderne\Work\Onsset\PyOnSSET\Tables\scenario{}'.format(scenario)
    if diesel_high:
        settlements_csv = os.path.join(output_dir, settlements + '-high.csv')
    else:
        settlements_csv = os.path.join(output_dir, settlements + '-low.csv')

    arcpy.env.workspace = gdb
    arcpy.env.overwriteOutput = True
    arcpy.env.addOutputsToMap = False
    arcpy.CheckOutExtension("Spatial")

    arcpy.CreateFeatureclass_management(arcpy.env.workspace, settlements_fc, "POINT")
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
        arcpy.AddField_management(settlements_fc, h, type)

    prev = None
    with arcpy.da.InsertCursor(settlements_fc, fields) as cursor:
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