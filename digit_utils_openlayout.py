from shapely.geometry import Polygon,Point
import shapely
# from digit_domain import printLog
import re

from code_files.OpenLayouts.check_subplot_in_mortgage import get_mortgaged_subplots
from code_files.OpenLayouts.check_bufferzone import DXF_File_Data
from code_files.OpenLayouts.WidthOfMainRoadANDInternalRoadWhenTouch import MainRoadInternalRoadWidth
from code_files.OpenLayouts.ValidationLayersForOpenLayout import ValidationLayersForOpenLayout
from code_files.OpenLayouts.Validation_For_Utility_And_SocialInfrastructure import CheckUtilityAndSocialInfrastructure
from code_files.OpenLayouts.OpenLayouts_Facility_Area_Util import Facilities_With_InternalRoad
from logging_config import get_current_logger
#Function helper for getInternalRoadWidth

def re_round(li, _prec=1):
	try:
		return round(li, _prec)
	except TypeError:
		return type(li)(re_round(x, _prec) for x in li)

def reduce_round(li, _prec=1,deduct=0):
	try:
		#print('before li ', str(li))
		newList=[]

		for point_li in li:
			#print('point is ', point_li)
			x,y=point_li
			if (x > 0):
				x = round(x-deduct)
			else :
				x = x + deduct
			x = round(x,_prec)

			if (y>0) :
				y = round(y-deduct)
			else:
				y=y+deduct
			y = round(y,_prec)
			newList.append((x,y))
		#print('After reduction newList ', newList)
		#lireduced = round(newList, _prec)
		return newList
		#return round(newList, _prec)
	except TypeError:
		print('reduce_round_error ')
		return type(li)(re_round(x, _prec) for x in li)

#Fix 4/27/2022
def split(start,end,seg):  # this function used for Spliting the lines

	x_delta=(end[0]-start[0])/float(seg)

	y_delta=(end[1]-start[1])/float(seg)

	points=[]

	for i in range(1,seg):

		pts=(start[0]+i*x_delta,start[1]+i*y_delta)

		points.append(pts)

	return [start]+points+[end]


"""
Extracts digits between two delimeter strings 
ramp_text = '25.00 mt. long 3.14 mt. High 5.40 mt. Wide Vehicular Ramp'
startDelimeter is optional like if u know only end index 

"""


def extract_dimensions_fromtext(inputText: str, startDelimeter: None, endDelimeter: 'h'):
    height_value = 0.0
    start_idx = 0

    # printLog("verbose", "extract_dimension from text :: InputText =", inputText, "start/end delimeters", startDelimeter,
    #          "/", endDelimeter)
    if (inputText is None or len(inputText) == 0):
        get_current_logger().error(f"Invalid inputs returning default value  {height_value}")
        return height_value
    else:
        # any digit patterns
        numeric_const_pattern = '[-+]? (?: (?: \d* \. \d+ ) | (?: \d+ \.? ) )(?: [Ee] [+-]? \d+ ) ?'
        rx = re.compile(numeric_const_pattern, re.VERBOSE)

        # check if u can find the start and end delimeters
        if (startDelimeter is not None and len(startDelimeter) > 0):
            start_idx = inputText.find(startDelimeter)
        else:
            start_idx = 0

        end_idx = inputText.find(endDelimeter)

        sub_text = inputText[start_idx:end_idx]

        # printLog('debug', "substring is " + sub_text)

        height_tmp = rx.findall(sub_text)
        # printLog('verbose', "dimension  is " + str(height_tmp))
        if (len(height_tmp) > 0):
            # return the index[0] value
            return height_tmp[0]
        else:
            # printLog('error',
            #          'Unable to extract height value from :: ' + inputText + ' - Returning default value ' + str(
            #              height_value))

            get_current_logger().error(f"Unable to extract height value from :: {inputText} - Returning default value {height_value}")
            return height_value


"""
Extracts digits between two delimeter strings 
ramp_text = '25.00 mt. long 3.14 mt. High 5.40 mt. Wide Vehicular Ramp'
startDelimeter is optional like if u know only end index 

#

#18.00MT WIDE MAINROAD
#9.14m WIDE PROPOSED ROAD
#RoadNames
# a. IF EXSITNG MENTIONED?
#
'''
is proposed mentioned : get always proposed if present 
is existing mentioned : after existing 
if neither are mentioned :  just get the number 

'''
###



"""


def extract_road_width_fromtext(inputText: str):
    height_value = 0.0
    start_idx = 0

    # printLog("verbose", "extract_width :: InputText =", inputText, "start/end delimeters")
    if (inputText is None or len(inputText) == 0):
        # printLog('error', "Invalid inputs returning default value  ", height_value)
        get_current_logger().error(f"Invalid inputs returning default value  {height_value}")
        return height_value
    else:
        startDelim = None
        # case of neither - just get single value
        noDelim = False

        inputText = inputText.upper()
        existingIndex = inputText.find('EXISTING')
        proposedIndex = inputText.find('PROPOSED')

        # set Start and End Delim
        if (existingIndex > -1):
            startDelim = 'EXISTING'
            start_idx = existingIndex
        else:
            start_idx = 0

        if (proposedIndex > -1):
            endDelim = 'PROPOSED'
            end_idx = proposedIndex
        else:
            # endDelim=''
            end_idx = len(inputText)

        if (existingIndex == -1 and proposedIndex == -1):
            noDelim = True
            startDelim = 0
            endDelim = len(inputText)

        # any digit patterns
        numeric_const_pattern = '[-+]? (?: (?: \d* \. \d+ ) | (?: \d+ \.? ) )(?: [Ee] [+-]? \d+ ) ?'
        rx = re.compile(numeric_const_pattern, re.VERBOSE)

        sub_text = inputText[start_idx:end_idx]

        # printLog('verbose', "substring is " + sub_text)

        height_tmp = rx.findall(sub_text)
        # printLog('verbose', "dimension  is " + str(height_tmp))
        if (len(height_tmp) > 0):
            # return the index[0] value
            return height_tmp[0]
        else:
            # printLog('error',
            #          'Unable to extract height value from :: ' + inputText + ' - Returning default value ' + str(
            #              height_value))

            get_current_logger().error(f"Unable to extract height value from :: {inputText} - Returning default value {height_value}")
            return height_value

def getInternalRoadWidth(layerName:str,msp):#folder:str,filename:str):

	returnValueDict=dict()
	if (layerName is None or layerName not in ['_InternalRoad', '_GridRoad'] or msp is None):#folder is None or filename is None):
		print('Invalid inputs - need valid layerName (InternalRoad or GridRoad) and modelspace object. LayerName# ', layerName, ' modelspace #',msp )
		return returnValueDict

	#dxf_path=os.path.join(folder,filename)

	#read_dxf=ezdxf.readfile(dxf_path)
	#print('read file ')
	#msp=read_dxf.modelspace()

	group=msp.groupby(dxfattrib='layer')
	print('group ', len(group))
	lst1=[]
	for layer,entities in group.items():
		if '_InternalRoad'==layer:
			lst1=[]
			for entity in entities:
				if entity.dxftype()=='TEXT' or entity.dxftype() == 'MTEXT':
					if (entity.dxftype() == 'TEXT'):
						name=entity.dxf.text
					else:
						name =entity.text

					specialChar=name.find(';')
					#print('special char '  , specialChar)
					if (specialChar > -1 ):
						name=name[specialChar+1:]
						#print('special char is removed  now ', name)
						#check if it has } tag
						endTag=name.find('}')
						if (endTag > -1):
							#print('end tag removed string  is now ', name)
							name=name[:endTag]

					lst1.append(name)
			print(f'No of Road name={len(lst1)} \t\t Names {lst1}')
			lst2=[]
			for entity1 in entities:
				if (entity1.dxftype()=='LWPOLYLINE') and (len(entity1.get_points())==2 or len(entity1.get_points())==3):
					pts=entity1.get_points()
					xy=split(pts[0],pts[1],10)
					lsta=[]
					for pt in xy[3:-3]:
						lsta.append(pt)
					lst2.append(lsta)
			lst4=[]
			lst3=[]
			for entity2 in entities:
				 if entity2.dxftype()=='LWPOLYLINE' and len(entity2.get_points())>=4:
					 ptlw=entity2.get_points()
					 lst4.append(entity2.dxf.handle)
					 lstb=[]
					 for pts2 in ptlw:
						 lstb.append(pts2[0:2])
					 lst3.append(lstb)
			print(f'No of polygons={len(lst3)}, No of Handles ={len(lst4)}')
			x=0
			for i in lst3:
				poly=Polygon(i)
				lstc2=[]
				for dt in lst2:
					points=Point(dt)
					lstc2.append(poly.exterior.distance(points))
				print(f'width==={round(min(lstc2)*2,2)}\t\t id==={lst4[x]}')
				returnValueDict[lst4[x]]= [lst1[x],  round(min(lstc2)*2,2)]

				x = x+1
				print('-------------------------------------------')

	return returnValueDict


def extractMaxRoadWidthFromDict(splayRoadDict: dict):
    retVal = dict()

    if (splayRoadDict is None or len(splayRoadDict) == 0):
        retVal['errorCode'] = 99
        retVal['msg'] = 'Invalid inputs splayRoadDict is None or no items value=' + str(splayRoadDict)

    else:

        retVal['errorCode'] = 0
        sizeOfDict = len(splayRoadDict)
        roadOneTxt = 'N/A'
        roadTwoTxt = 'N/A'

        if (sizeOfDict == 2):
            for i, (k, v) in enumerate(splayRoadDict.items()):
                # print(i, k)
                if (i == 0):
                    roadOneTxt = splayRoadDict.get(k, 'N/A')
                if (i == 1):
                    roadTwoTxt = splayRoadDict.get(k, 'N/A')
            # extract Road Width
            if (roadOneTxt == 'N/A' or roadTwoTxt == 'N/A'):
                retVal['errorCode'] = 99
                retVal['msg'] = 'Require keys with 2 indices and are not visible '

            else:
                try:
                    roadOne = float(extract_dimensions_fromtext(roadOneTxt, None, 'W'))
                    roadTwo = float(extract_dimensions_fromtext(roadTwoTxt, None, 'W'))
                    # print("road one and two are : " + str(roadOne) + " , " + str(roadTwo))

                    if (roadOne == roadTwo):
                        # return either one
                        # print("Road one and two are same ")
                        retVal['msg'] = roadOneTxt
                    elif (roadOne > roadTwo):
                        # return roadOne
                        # print("Road one is more  ")
                        retVal['msg'] = roadOneTxt
                    else:
                        # return roadTwo
                        # print("Road two is more  ")
                        retVal['msg'] = roadTwoTxt
                except:
                    # printLog('error',
                    #          'Error occurred in extracting splay max abutting road. input = ' + str(splayRoadDict))

                    get_current_logger().error(f"Error occurred in extracting splay max abutting road. input = {splayRoadDict}")

                    retVal['errorCode'] = -1
                    retVal['msg'] = 'Unable to extract the abutting road text from input=' + str(splayRoadDict)
        elif (sizeOfDict == 1):
            # print("returning same " )
            retVal['msg'] = str(splayRoadDict.values())
        else:
            # print("return the same ")
            retVal['msg'] = str(splayRoadDict.values())

    return retVal


def extract_room_dimensions(roomName):
    # printLog('debug', ' Extract room dimensions from ' + str(roomName))
    result = dict()

    if (roomName is None or len(roomName.strip()) <= 0):
        result['code'] = 99
        result['length'] = -1
        result['width'] = -1
        result['type'] = 'N/A'
        result['msg'] = 'Input required, is : ' + roomName
    else:

        lengthDelim = '\\P'
        widthDelim = 'X'

        length_idx = roomName.rfind(lengthDelim)
        width_idx = roomName.rfind(widthDelim)

        if (length_idx != -1 and width_idx != -1):
            # success set return code 0
            result['code'] = 0
            result['length'] = roomName[length_idx + 2:width_idx]
            result['width'] = roomName[width_idx + 1:]
            result['type'] = roomName[:length_idx]
            result['msg'] = ''

        else:
            # unable to extract return failure
            result['code'] = 1
            result['length'] = 0
            result['width'] = 0
            result['type'] = 'N/A'
            result['msg'] = 'Unable to get dimensions'
    return result


# Fix 9/25/2022
# 	from check_subplot_in_mortgage import get_mortgaged_subplots
# CODE = 0 when success, > 0 for failure cases.
# Failure cases : 99 for invalid input.  99 for exception while processing & ERROR with the text
#
def get_mortgagedSubplots4OpenLayout(modelspace):
    returnValueDict = dict()
    msg_set_stage = 'Get Mortaged SubPlots '
    response1 = dict()
    try:

        if (modelspace is not None):

            response1 = get_mortgaged_subplots(modelspace)
            # printLog('verbose', ' *** ' + msg_set_stage + ' Completed \n Response ', response1)
            code = response1.get('code', -1)
            data = response1.get('data', 'N/A')
            error = response1.get('error', 'N/A')
            if (code == 0):
                print(' *** ' + msg_set_stage + ' Completed \n Response ', data)
                returnValueDict['MORTGAGED_SUBPLOTS_LIST'] = data
                returnValueDict['CODE'] = 0
            elif (code == -1):
                error = 'Problem extracting response '
                data = list()
                data.append(error)

                print(' *** ' + msg_set_stage + ' Completed \n Response ', data)
                returnValueDict['MORTGAGED_SUBPLOTS_LIST'] = data
                returnValueDict['CODE'] = -1
            elif (code == 99):

                data = list()
                data.append(error)

                print(' *** ' + msg_set_stage + ' Completed \n Response ', data)
                returnValueDict['MORTGAGED_SUBPLOTS_LIST'] = data
                returnValueDict['CODE'] = 99

        else:
            msg = 'Error Invalid input required modelspace is None '
            returnValueDict['ERROR'] = msg
            returnValueDict['CODE'] = 99
            return returnValueDict

    except Exception as excp:
        msg = 'Problem processing # get_mortgagedSubplots4OpenLayout- ' + msg_set_stage + ' due to # ' + str(excp)
        print(msg)
        returnValueDict['ERROR'] = msg
        returnValueDict['CODE'] = -1

    return returnValueDict


def checkBufferZoneWaterBodiesLocationWithPlot(msp):
    print('Starting checkBufferZoneWaterBodiesLocationWithPlot ')
    returnValueDict = dict()

    if (msp is None):
        returnValueDict['CODE'] = -1
        returnValueDict['ERROR'] = 'Invalid Inputs. Valid Modelspace required but is None'

        return returnValueDict
    else:
        try:
            Data_Extractor = DXF_File_Data()
            response1 = Data_Extractor.Read_File_Data_DXF_File(msp)

            returnCode = response1.get('code', 100)

            returnValueDict['CODE'] = returnCode

            if (returnCode == 0):
                returnValueDict['RESULTS'] = response1.get('data', [])
            else:
                returnValueDict['ERROR'] = response1.get('error', 'Unknown Error')

        except Exception as excp:
            msg = 'Problem check BufferZone/Waterbodies Location With Plot ' + str(excp)

            print('ERROR >>>>  ', msg)
            returnValueDict['ERROR'] = msg
            returnValueDict['CODE'] = -1

    print('Response  checkBufferZoneWaterBodiesLocationWithPlot  ', returnValueDict)

    print('Completed checkBufferZoneWaterBodiesLocationWithPlot  ')

    return returnValueDict


# from .WidthOfMainRoadANDInternalRoadWhenTouch import *
# Fix 01/16/2024 - Open Layout - Main and Internal Perpendicular Road < 18 m bypass
def checkMainAndInternalRoadWidthsInOpenLayout(msp):
    print('Starting checkMainAndInternalRoadWidthsInOpenLayout ')
    returnValueDict = dict()

    if (msp is None):
        returnValueDict['CODE'] = -1
        returnValueDict['ERROR'] = 'Invalid Inputs. Valid Modelspace required but is None'

        return returnValueDict
    else:
        try:
            mainInternalRoadObj = MainRoadInternalRoadWidth()

            response1 = mainInternalRoadObj.CalculateWidth(msp)

            returnCode = response1.get('code', 100)

            returnValueDict['CODE'] = returnCode

            if (returnCode == 0):
                returnValueDict['RESULTS'] = response1.get('data', [])
            else:
                returnValueDict['ERROR'] = response1.get('errors', 'Unknown Error')

        except Exception as excp:
            msg = 'Problem check MainAndInternal RoadWidthsInOpenLayout ' + str(excp)

            print('ERROR >>>>  ', msg)
            returnValueDict['ERROR'] = msg
            returnValueDict['CODE'] = -1

    print('Response  checkMainAndInternalRoadWidthsInOpenLayout  ', returnValueDict)

    print('Completed checkMainAndInternalRoadWidthsInOpenLayout  ')

    return returnValueDict


# Function to check if one object is part of a given list of objects
# example splay within plot,  regular plot is in mortgaged plots

# since 6/28/2022   with childIndivObj as polygon itself
def isChildFullyWithinParentObjectPlain(childType: str, parentType: str, childIndivObj, parentInvdivObjList: list):
    # printLog('debug',
    #          'isChildFullyWithinParentObjectPlain -- Starting , Child Type: ' + childType + ' Parent Type: ' + parentType)

    result = dict()

    if (childType is None or parentType is None or childIndivObj is None or parentInvdivObjList is None or len(
            parentInvdivObjList) == 0):

        # printLog('error', 'Invalid inputs to proceed to check child is within parent ')
        get_current_logger().error('Invalid inputs to proceed to check child is within parent ')
        result = {'iswithin': False, 'childType': childType, 'parentType': parentType, 'parentName': 'NA',
                  'parentObj': None}
        return result
    else:

        # printLog('debug', 'Inputs to proceed to check child is within parent ')
        # printLog('debug', 'Starting Child Type: ' + str(childType) + ' polygon ' + str(childIndivObj))

        for parentObj in parentInvdivObjList:
            # printLog('debug',
            #          ' Parent Type: ' + str(parentType) + ' Handle : ' + str(parentObj.handle) + ' Name: ' + str(
            #              parentObj.name) + ' polygon ' + str(parentObj.polygon))
            parentlwpoly = shapely.wkt.loads(str(parentObj.polygon))

            parentlwpoly_re_points = reduce_round(list(parentlwpoly.exterior.coords), 2, 0.10)
            parentlwpoly = Polygon(parentlwpoly_re_points)

            # childIndivlwpoly_re = shapely.wkt.loads(str(childIndivObj)  )

            # childIndivlwpoly_re_points= reduce_round(list(childIndivObj.exterior.coords),0,.10)

            # childIndivlwpoly_re= Polygon(childIndivlwpoly_re_points)

            # or parentlwpoly.overlaps(childIndivlwpoly)
            # printLog('debug', 'child overlaps parent ? ', childIndivObj.overlaps(parentlwpoly),
            #          'child contains parent ? ', \
            #          childIndivObj.contains(parentlwpoly), ' child within parent? ', childIndivObj.within(parentlwpoly),
            #          ' parent overlaps child ?', \
            #          parentlwpoly.overlaps(childIndivObj) \
            #          , ' parent contains child ?', parentlwpoly.contains(childIndivObj), ' parent intersects child ?',
            #          parentlwpoly.intersects(childIndivObj))
            if (childIndivObj.contains(parentlwpoly)):  # or parentlwpoly.overlaps(childIndivlwpoly)) :
                # printLog('debug', 'Child is within Parent Type: ' + str(parentType) + ' Name: ' + str(parentObj.name))
                # print('')
                result = {'iswithin': True, 'childType': childType, 'parentType': parentType,
                          'parentName': str(parentObj.name), 'parentObj': parentObj}
                # break
                return result

    # printLog('debug',
    #          'isChildFullyWithinParentObjectPlain -- Ending , Child Type: ' + childType + ' Parent Type: ' + parentType + ' Result :: ' + str(
    #              result))
    return result


# Function to check if one object is part of a given list of objects
# example splay within plot,  regular plot is in mortgaged plots
# since 3/12/2022
def isChildFullyWithinParentObject(childType: str, parentType: str, childIndivObj, parentInvdivObjList: list):
    # printLog('debug',
    #          'isChildFullyWithinParentObject -- Starting , Child Type: ' + childType + ' Parent Type: ' + parentType)

    result = dict()

    if (childType is None or parentType is None or childIndivObj is None or parentInvdivObjList is None or len(
            parentInvdivObjList) == 0):

        # printLog('error', 'Invalid inputs to proceed to check child is within parent ')
        get_current_logger().error('Invalid inputs to proceed to check child is within parent ')
        result = {'iswithin': False, 'childType': childType, 'parentType': parentType, 'parentName': 'NA',
                  'parentObj': None}
        return result
    else:

        # printLog('debug', 'Inputs to proceed to check child is within parent ')
        # printLog('debug',
        #          'Starting Child Type: ' + str(childType) + ' Handle : ' + str(childIndivObj.handle) + ' Name: ' + str(
        #              childIndivObj.name) + ' polygon ' + str(childIndivObj.polygon))

        for parentObj in parentInvdivObjList:
            # printLog('debug',
            #          ' Parent Type: ' + str(parentType) + ' Handle : ' + str(parentObj.handle) + ' Name: ' + str(
            #              parentObj.name) + ' polygon ' + str(parentObj.polygon))
            parentlwpoly = shapely.wkt.loads(str(parentObj.polygon))

            parentlwpoly_re_points = reduce_round(list(parentlwpoly.exterior.coords), 2, 0.10)
            parentlwpoly = Polygon(parentlwpoly_re_points)

            childIndivlwpoly = shapely.wkt.loads(str(childIndivObj.polygon))

            childIndivlwpoly_re_points = reduce_round(list(childIndivlwpoly.exterior.coords), 0, .10)

            childIndivlwpoly_re = Polygon(childIndivlwpoly_re_points)

            # or parentlwpoly.overlaps(childIndivlwpoly)
            # printLog('debug', ' child within parent? ', childIndivlwpoly_re.within(parentlwpoly),
            #          ' parent overlaps child ?', parentlwpoly.overlaps(childIndivlwpoly_re) \
            #          , ' parent contains child ?', parentlwpoly.contains(childIndivlwpoly_re),
            #          ' parent intersects child ?', parentlwpoly.intersects(childIndivlwpoly_re))
            if (childIndivlwpoly_re.within(parentlwpoly)):  # or parentlwpoly.overlaps(childIndivlwpoly)) :
                # printLog('debug', 'Child is within Parent Type: ' + str(parentType) + ' Name: ' + str(parentObj.name))
                # print('')
                result = {'iswithin': True, 'childType': childType, 'parentType': parentType,
                          'parentName': str(parentObj.name), 'parentObj': parentObj}
                # break
                return result

    # printLog('debug',
    #          'isChildFullyWithinParentObject -- Ending , Child Type: ' + childType + ' Parent Type: ' + parentType + ' Result :: ' + str(
    #              result))
    return result


# Function to check if one object is part of a given list of objects
# example splay within plot,  regular plot is in mortgaged plots
# since 3/12/2022
def isChildWithinParentObject(childType: str, parentType: str, childIndivObj, parentInvdivObjList: list):
    # printLog('debug',
    #          'isChildWithinParentObject -- Starting , Child Type: ' + childType + ' Parent Type: ' + parentType)

    result = dict()

    if (childType is None or parentType is None or childIndivObj is None or parentInvdivObjList is None or len(
            parentInvdivObjList) == 0):

        # printLog('error', 'Invalid inputs to proceed to check child is within parent ')
        get_current_logger().error('Invalid inputs to proceed to check child is within parent ')
        result = {'iswithin': False, 'childType': childType, 'parentType': parentType, 'parentName': 'NA',
                  'parentObj': None}
        return result
    else:

        # printLog('debug', 'Inputs to proceed to check child is within parent ')
        # printLog('debug', 'Starting Child Type: ' + str(childType) + ' Name: ' + str(childIndivObj.name))

        for parentObj in parentInvdivObjList:

            parentlwpoly = shapely.wkt.loads(str(parentObj.polygon))

            childIndivlwpoly = shapely.wkt.loads(str(childIndivObj.polygon))
            # or parentlwpoly.overlaps(childIndivlwpoly)
            if (childIndivlwpoly.within(parentlwpoly) or parentlwpoly.overlaps(childIndivlwpoly)):
                # printLog('debug', 'Child is within Parent Type: ' + str(parentType) + ' Name: ' + str(parentObj.name))
                # print('')
                result = {'iswithin': True, 'childType': childType, 'parentType': parentType,
                          'parentName': str(parentObj.name), 'parentObj': parentObj}
                break
            # return result

    # printLog('debug',
    #          'isChildWithinParentObject -- Ending , Child Type: ' + childType + ' Parent Type: ' + parentType + ' Result :: ' + str(
    #              result))
    return result


# Validation_layers OpenLayout 08/20/2023
# from .ValidationLayersForOpenLayout
def checkCommonLayersInOpenLayout(msp):
    returnValueDict = dict()
    if (msp is None):
        returnValueDict['CODE'] = -1
        returnValueDict['ERROR'] = 'Invalid Inputs. Valid Modelspace required but is None'

        return returnValueDict
    else:
        try:
            obj = ValidationLayersForOpenLayout()

            response1 = obj.ValLayersOpenLayout(msp)

            returnValueDict['RESULTS'] = "["+",".join(response1)+"]"
            returnValueDict['CODE'] = "0"
        except Exception as excp:
            msg = 'Problem Validating Layer Checks checkCommonLayersInOpenLayout ' + str(excp)

            print('ERROR ', msg)
            returnValueDict['ERROR'] = msg
            returnValueDict['CODE'] = -1
    return returnValueDict


# OpenLayout Additional Validation Checks Amenities  02/26/2024
# from Validation_For_Utility_And_SocialInfrastructure import *
def checkAmentiesSocialInfra_OpenLayouts(msp):
    returnValueDict = dict()
    print('checkAmentiesSocialInfra_OpenLayouts ', ' Starting...')
    if (msp is None):
        returnValueDict['CODE'] = -1
        returnValueDict['ERROR'] = 'Invalid Inputs. Valid Modelspace required but is None'

        return returnValueDict
    else:
        try:

            utilSocialInfra = CheckUtilityAndSocialInfrastructure()
            ##
            response1 = utilSocialInfra.CheckSocialInfoValidation(msp)
            respCode = response1.get('CODE', 100)
            returnValueDict['CODE'] = str(respCode)
            if (respCode != 100):
                returnValueDict['RESULTS'] = response1.get('RESULTS', [])

        except Exception as excp:
            print('checkAmentiesSocialInfra_OpenLayouts ', ' Exception Encountered...')
            msg = 'Problem Validating checkAmentiesSocialInfra_OpenLayouts ' + str(excp)

            print('ERROR ', msg)
            returnValueDict['ERROR'] = msg
            returnValueDict['CODE'] = -1

    print('checkAmentiesSocialInfra_OpenLayouts ', ' Completed.')
    return returnValueDict


# OpenLayout Additional Validation Checks Amenities  02/26/2024
# from OpenLayouts_Facility_Area_Util
def checkFacilities_OpenLayouts(msp):
    returnValueDict = dict()
    errors = []
    print('checkFacilities_OpenLayouts ', ' Starting...')
    if (msp is None):
        returnValueDict['CODE'] = -1
        errors.append('Invalid Inputs. Valid Modelspace required but is None')
        returnValueDict['ERROR'] = errors

        return returnValueDict
    else:
        try:

            facilityAreaInfra = Facilities_With_InternalRoad()
            ##
            response1 = facilityAreaInfra.CheckFacilityValidation(msp)
            respCode = response1.get('CODE', 100)
            returnValueDict['CODE'] = str(respCode)
            if (respCode != 100):
                returnValueDict['RESULTS'] = response1.get('RESULTS', [])
                returnValueDict['ERROR'] = response1.get('ERROR', [])


        except Exception as excp:
            print('checkFacilities_OpenLayouts ', ' Exception Encountered...')
            msg = 'Problem Validating checkFacilities_OpenLayouts ' + str(excp)
            errors.append(msg)
            print('ERROR ', msg)
            returnValueDict['ERROR'] = errors
            returnValueDict['CODE'] = -1

    print('checkFacilities_OpenLayouts ', ' Completed.')
    return returnValueDict