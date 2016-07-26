import csv
import arcpy as ap

settlements = r'C:/Users/adm.esa/Desktop/ONSSET/Africa_Onsset.gdb/settlements_1km2'
settlements_csv = r'Tables/settlements.csv'

field_list = ['Country', 'SHAPE@X', 'SHAPE@Y', 'Pop','GridDistCurrent',
              'GridDistPlan', 'RoadDist', 'NightLights', 'TravelHours',
              'GHI', 'WindCF', 'Hydropower', 'HydropowerDist']

header_list = ['Country', 'X', 'Y', 'Pop','GridDistCurrent',
              'GridDistPlan', 'RoadDist', 'NightLights', 'TravelHours',
              'GHI', 'WindCF', 'Hydropower', 'HydropowerDist']

with open(settlements_csv, 'w') as csvfile:
    csvwriter = csv.writer(csvfile, delimiter=',', lineterminator='\n')
    csvwriter.writerow(header_list)

    with ap.da.SearchCursor(settlements, field_list) as cursor:
        for row in cursor:
            csvwriter.writerow(row)