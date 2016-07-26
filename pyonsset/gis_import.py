import csv
import arcpy as ap

######
# set the variables here!
# the geodatabase, the shapefile name, and the csv file input
#####
ap.env.workspace = r'C:\Users\adm.esa\Desktop\ONSSET\Africa_Onsset.gdb'
sets = 'sets673'
csvfile = r'C:\Users\adm.esa\Desktop\ONSSET\PyOnSSET\Tables\scenario673\settlements.csv'

ap.env.overwriteOutput = True
ap.env.addOutputsToMap = False
ap.CheckOutExtension("Spatial")


ap.CreateFeatureclass_management(ap.env.workspace, sets, "POINT")
csvreader = csv.reader(open(csvfile, 'r'), delimiter=',', lineterminator='\n')

fields = csvreader.next()
heads = fields[:]
fields[1] = 'SHAPE@XY'
del fields[2]
del heads[0]
del heads[0]
del heads[0]

ap.AddField_management(sets, fields[0], 'TEXT')
for h in heads:
    if h == 'minimum_tech' or h == 'minimum_category':
        ap.AddField_management(sets, h, 'TEXT')
    else:
        ap.AddField_management(sets, h, 'FLOAT')

prev = 'Baloo'
with ap.da.InsertCursor(sets, fields) as cursor:
    for row in csvreader:
        rowf = []

        rowf.append(row[0])
        rowf.append((float(row[1]), float(row[2])))

        for i,r in enumerate(row):
            if i >= 3 and i != 38 and i != 40:
                try:
                    rowf.append(float(r))
                except:
                    rowf.append(0)
            elif i == 38 or i == 40:
                rowf.append(str(r))

        cursor.insertRow(rowf)
        if rowf[0] != prev: print(rowf[0])
        prev = rowf[0]
