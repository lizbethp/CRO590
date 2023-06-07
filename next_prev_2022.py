# Author: Lizbeth Plaza Torres (lizbethp@iastate.edu)
# Date: 12/7/2022
# Version: Python 3.9.11
# Purpose: This script defines a tool that will only work with a Digital Acre
# shapefile. The tool will flag all plants next to the skip bowl and numerate them.
# At this point the data should contain all plants in the field and
# should NOT contain any plants that were not in the field. Additionally,
# the shapefile should have the field location attribute (Plots/Rep, Row, Zone,
# Plant Number and MASTER/CORE ID).

#import modules
import arcpy
import time
import sys
import numpy as np
import pandas as pd
import os


#from mypackage.my_functions import *

#======= Function 1 ========#
# Returns the unique values of a list
# Inputs: list
def unique(list1):
    #import numpy as np
    x = np.array(list1)
    return list(np.unique(x))

#======= Function 2 ========#
# Converts fc table into dataframe
# Inputs: fc (feature class), fields (desired fields, list format)
# col_names (how you want to call the col on the dataframe, list
# format and same order as fields) - ALL REQUIERD
def fc_to_df(fc, fields, col_names):
    data = []
    with arcpy.da.SearchCursor(fc, fields) as cursor:
        for row in cursor:
            dict_temp = {}
            
            for i in range(len(fields)):
                dict_temp.update({col_names[i]:row[i]})
                
            data.append(dict_temp)
            
    return(pd.DataFrame(data))

# set up inputs
input_fc = arcpy.GetParameterAsText(0)
##plot = arcpy.GetParameterAsText(1)
##row = arcpy.GetParameterAsText(2)
##zone = arcpy.GetParameterAsText(3)
##plantn = arcpy.GetParameterAsText(4)
##coreID = arcpy.GetParameterAsText(5)




start = time.perf_counter()
#========== Next and Previos Distance ===========#
prev_dist_dict = {}
next_dist_dict = {}
arcpy.env.workspace = "memory"

arcpy.AddMessage('Calculating next and previos distance.')
# Generates near table for input_fc
neart = arcpy.analysis.GenerateNearTable(input_fc, input_fc, 'test', angle = 'ANGLE', closest = 'ALL', closest_count = 10)
near_field = [nfield.name for nfield in arcpy.ListFields(neart)]

# Setting up progressor 
plants = int(arcpy.GetCount_management(input_fc).getOutput(0))
i = 0
arcpy.SetProgressor('step', 'Calculating previos and next distand of plants...', 0, plants, 1)

# List of all oid values of input_fc
oid_values = [i[0] for i in arcpy.da.SearchCursor(input_fc, arcpy.Describe(input_fc).OIDFieldName)]

for oid in oid_values:
    # Updating progresson position 
    arcpy.SetProgressorLabel('Plant #' + str(i) + ' out of ' + str(plants))
    arcpy.SetProgressorPosition()
    #(NEAR_ANGLE > -190 And NEAR_ANGLE < -170) Or (NEAR_ANGLE > 170 And NEAR_ANGLE < 180)
    #where_clause1 = "{ANGLE} > {a1} And {ANGLE} < {a2} And {in_id} = {fc_oid}".format(ANGLE = near_field[5], 
                                                                      #a1 = -190, a2 = -170, in_id = near_field[1], fc_oid = oid)
    where_clause1 = "(({ANGLE} >= -180 And {ANGLE} < -150) Or ({ANGLE} > 150 And {ANGLE} <= 180)) And {in_id} = {fc_oid}".format(ANGLE = near_field[5], in_id = near_field[1], fc_oid = oid)
    all_dist_prev = [i[3] for i in arcpy.da.SearchCursor(neart,near_field, where_clause1)]
    try:
        prev_dist = min(all_dist_prev)
        prev_id = oid
    except:
        pass
    
    where_clause2 = "{ANGLE} > {a1} And {ANGLE} < {a2} And {in_id} = {fc_oid}".format(ANGLE = near_field[5], 
                                                                      a1 = -30, a2 = 30, in_id = near_field[1], fc_oid = oid)
    all_dist_next = [i[3] for i in arcpy.da.SearchCursor(neart,near_field, where_clause2)]
    try:
        next_dist = min(all_dist_next)
        next_id = oid
    except:
        pass

    # advance progresssor
    i += 1
        
    try:    
        prev_dist_dict[prev_id] = prev_dist
    except:
        pass
    try:
        next_dist_dict[next_id] = next_dist
    except:
        pass

arcpy.AddMessage('Adding prevdist and nextdist fields.')
arcpy.management.AddField(input_fc, "prevdist", "DOUBLE", field_alias="prev_dist", field_is_nullable="NULLABLE")
arcpy.management.AddField(input_fc, "nextdist", "DOUBLE", field_alias="next_dist", field_is_nullable="NULLABLE")

arcpy.AddMessage('Updating prevdist and nextdist fields.')
with arcpy.da.UpdateCursor(input_fc, [arcpy.Describe(input_fc).OIDFieldName, 'prevdist', 'nextdist']) as cursor:
    for row in cursor:
        try:
            row[1] = prev_dist_dict[row[0]]
            row[2] = next_dist_dict[row[0]]
            cursor.updateRow(row)
        except KeyError:
            try:
                row[1] = prev_dist_dict[row[0]]
                cursor.updateRow(row)
            except KeyError:
                try:
                    row[2] = next_dist_dict[row[0]]
                    cursor.updateRow(row)
                except:
                    pass
                
end = time.perf_counter()
arcpy.AddMessage(f'Execution took: {end-start} seconds')
