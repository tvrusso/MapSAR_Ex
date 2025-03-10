#-------------------------------------------------------------------------------
# Name:        ProbabilityRegions (ProbRegions.py)
# Purpose: Copy Probability Regions over to Segments.
#
# Author:      Don Ferguson
#
# Created:     01/25/2012
# Copyright:   (c) Don Ferguson 2012
# Licence:
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  The GNU General Public License can be found at
#  <http://www.gnu.org/licenses/>.
#-------------------------------------------------------------------------------
#!/usr/bin/env python

# Import arcpy module
try:
    arcpy
except NameError:
    import arcpy
try:
    sys
except NameError:
    import sys
import string
from types import *
from arcpy import env
import IGT4SAR_AreaNameDomain

# Environment variables
wrkspc=arcpy.env.workspace
env.overwriteOutput = "True"
arcpy.env.extent = "MAXOF"
##arcpy.env.parallelProcessingFactor = "100%"

def getDataframe():
    """ get current mxd and dataframe returns mxd, frame"""
    try:
        mxd = arcpy.mapping.MapDocument('CURRENT');df = arcpy.mapping.ListDataFrames(mxd,"*")[0]

        return(mxd,df)

    except SystemExit as err:
            pass

def ProbabilityDomain(Probability_Regions):
    cProb=arcpy.GetCount_management(Probability_Regions)
    if int(cProb.getOutput(0)) > 0:
    # Process: Table To Domain (9)
        arcpy.AddMessage("update Probability Region Name domain")
        arcpy.TableToDomain_management(Probability_Regions, "Region_Name", "Region_Name", wrkspc, "Region_Name", "Region_Name", "REPLACE")
        try:
            arcpy.SortCodedValueDomain_management(wrkspc, "Region_Name", "DESCRIPTION", "ASCENDING")
        except:
            pass
    else:
        arcpy.AddMessage("No Probability Region information to update")

###########Main############
if __name__ == '__main__':
    mxd, df = getDataframe()

    ProbRegions = arcpy.GetParameterAsText(0)
    if ProbRegions == '#' or not ProbRegions:
        ProbRegions = "8 Segments_Group\Probability Regions" # provide a default value if unspecified

    fc2 = "Search_Segments"
    fc3 = ProbRegions

    ProbabilityDomain(ProbRegions)
    arcpy.CalculateField_management(fc3, "Area", "!shape.area@acres!", "PYTHON_9.3", "")

    POCList=[]
    rows = arcpy.SearchCursor(fc3)
    for row in rows:
        if type(row.getValue("POCaSsign")) is NoneType:
            RegName = row.getValue("Region_Name")
            arcpy.AddError("POC has not been assigned for Region: " + RegName + ".  Set POC Assign to '0' if you do not want to include in Probability calculations.")
            sys.exit()
        else:
            POCList.append(row.POCaSsign)

    POCTotal = sum(POCList)

    rows1 = arcpy.UpdateCursor(fc3)
    row1 = rows1.next()

    while row1:
        # you need to insert correct field names in your getvalue function
        RegionName = row1.Region_Name
        RegArea = row1.Area
        if POCTotal==0.0:
            POCTotal=1.0
        POCReg = row1.POCaSsign/POCTotal * 100.0
        row1.POA = POCReg
        row1.POAcum = POCReg
        if RegArea != 0.0:
            PdenReg = round(POCReg/RegArea,3)
        else:
            PdenReg = 0.0

        row1.Pden=PdenReg

        where2 = '"Region_Name" = ' + "'" + RegionName + "'"
        arcpy.AddMessage(where2)
        rows2 = arcpy.SearchCursor(fc2, where2)
        row2 = rows2.next()

        arcpy.SelectLayerByAttribute_management(fc3,"NEW_SELECTION",where2)

        if row2:
            arcpy.AddMessage(RegionName + " already exists as a Segment")
            row2 = rows2.next()

        else:
            arcpy.SelectLayerByAttribute_management(fc3,"NEW_SELECTION",where2)
            arcpy.Append_management(fc3, fc2, "NO_TEST", "", "")
            rows3 = arcpy.UpdateCursor(fc2,where2)
            for row3 in rows3:
                if RegionName == 'ROW':
                    row3.Area_Name = RegionName
                else:
                    row3.Area_Name = RegionName + "01"
                row3.Area_seg = RegArea
                row3.POA = POCReg
                row3.sPOC_Orig = POCReg
                row3.POC_Now = POCReg
                row3.Pden = PdenReg
                row3.Status = "Not Assigned"
                row3.Searched = 0
                row3.Display = 1
                row3.PODcum = 0
                row3.PODcumunrsp = 0
                rows3.updateRow(row3)
            del row3
            del rows3

        del where2
        del row2
        del rows2

        rows1.updateRow(row1)
        row1 = rows1.next()

    del rows1
    del row1
    arcpy.SelectLayerByAttribute_management(fc3,"CLEAR_SELECTION")

    arcpy.AddMessage("\nUpdate Area Name Domain\n")
    try:
        IGT4SAR_AreaNameDomain.AreaNamesUpdate(wrkspc)
    except:
        sys.exit("Did not update Search Area Names Domain")
        arcpy.AddWarning("Failed to update the Search Area Names Domain")


