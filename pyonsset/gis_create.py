import arcpy as ap

ap.env.workspace = r'C:\Users\adm.esa\Desktop\ONSSET\Africa_Onsset.gdb'
ap.env.overwriteOutput = True
ap.env.addOutputsToMap = False
ap.CheckOutExtension("Spatial")

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

ap.RasterToPoint_conversion(pop, settlements)

ap.sa.ExtractMultiValuesToPoints(settlements, [[admin_raster, 'CountryNum']])
ap.JoinField_management(settlements,'CountryNum',admin_raster,'Value','Country')
ap.DeleteField_management(settlements,'CountryNum')

ap.sa.ExtractMultiValuesToPoints(settlements, [[ghi, 'GHI']])
print('ghi')
ap.sa.ExtractMultiValuesToPoints(settlements, [[windcf, 'WindCF']])
print('wind')
ap.sa.ExtractMultiValuesToPoints(settlements, [[travel, 'TravelHours']])
print('travel')
ap.sa.ExtractMultiValuesToPoints(settlements, [[nightlights, 'NightLights']])
print('lights')


"""
Calculate the distance of every settlement from
a) the existing grid
b) existing grid or the planned grid
"""
# each point's distance from the existing grid
ap.Near_analysis(settlements, gridExisting)

# done this way (as opposed to AlterField) so that the field type can be specified
ap.AddField_management(settlements, 'GridDistCurrent', 'LONG')
ap.CalculateField_management(settlements, 'GridDistCurrent', '!NEAR_DIST!', 'PYTHON_9.3')
ap.DeleteField_management(settlements, 'NEAR_DIST; NEAR_FID')

# each point's distance from either grid
ap.Near_analysis(settlements, [gridExisting, gridPlanned])

# done this way (as opposed to AlterField) so that the field type can be specified
ap.AddField_management(settlements, 'GridDistPlan', 'LONG')
ap.CalculateField_management(settlements, 'GridDistPlan', '!NEAR_DIST!', 'PYTHON_9.3')
ap.DeleteField_management(settlements, 'NEAR_DIST; NEAR_FID; NEAR_FC')

print('done grid')

"""
Add roaddist
"""

# each point's distance from the existing grid
ap.Near_analysis(settlements, roads)

# done this way (as opposed to AlterField) so that the field type can be specified
ap.AddField_management(settlements, 'RoadDist', 'LONG')
ap.CalculateField_management(settlements, 'RoadDist', '!NEAR_DIST!', 'PYTHON_9.3')
ap.DeleteField_management(settlements, 'NEAR_DIST; NEAR_FID')

print('done roads')

"""
Add hydropower points to settlements
"""
# find the hydro point nearest each settlement (add the FID and distance to settlements)
ap.Near_analysis(settlements, hydro_points)
ap.AlterField_management(settlements, 'NEAR_DIST', 'HydropowerDist')

ap.JoinField_management(settlements, 'NEAR_FID', hydro_points,
                        ap.Describe(hydro_points).OIDFieldName, ['Hydropower'])

ap.DeleteField_management(settlements, 'NEAR_FID')

print('done hydro')