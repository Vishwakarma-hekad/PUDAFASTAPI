#digit_utils_buildings.py
from grepfunc import grep_iter
import copy
import re
import sys
import math
import ezdxf
import traceback
import pandas as pd
import numpy as np
from shapely.geometry import Point,Polygon,LineString
import shapely.wkt
from timeit import default_timer as timer
# from digit_base import printLog, LayerMaster
from digit_base import LayerMaster
from digit_domain import DxfPoly
from code_files.Buildings.travel_distance import Travelled_Distance
from code_files.Buildings.podium_setbacks import check_podium_setbacks,podium_regular_setbacks,check_redius_of_Arc
from code_files.Buildings.floor_wise_setbacks import check_floor_wise_setbacks
from code_files.Buildings.cellar_setbacks_util import check_cellar_setbacks,cellar_plinth_dist
from code_files.Buildings.septic_tank_util import dist_of_sept_tank
from code_files.Buildings.ramp_check_util import RampLENGTHandBuildingHeight
from code_files.Buildings.building_mortgage_util import get_building_mortgage_carpetarea
from code_files.Buildings.transfer_of_setbacks_util import transfer_setbacks
from code_files.Buildings.new_buildings_get_accessory_voids_by_buatype_util_v2 import check_resibua_and_commbua_tot_area
from code_files.Buildings.checkOverlappingLayers import check_For_layersOverlapping
from code_files.Buildings.Validation_layers_v2 import CommonValidationLayers
from code_files.Buildings.roomUtil2 import window_check
from code_files.Buildings.CommonFloorSetbacks_v2 import CommomFloorSetbacks
from code_files.Buildings.BalconyLengthAndWidth_util import BalconyLengthAndWidth
from code_files.Buildings.CheckWidthANDAreaForVentilationShaft import VentilationWidthANDArea
from code_files.Buildings.PlotLengthANDEntGateWidth import SegmentwisePlotLength_AND_EntGateWidth
from code_files.Buildings.SegmentWiseSetabcksForBuildings import CommonFloorSetbacksOFSegmentwise
from code_files.Buildings.WindowInRoomUtil import CheckWindowsINRoom
from code_files.Buildings.CommonBuildingsCode_forarc import AllBuildingsData
from code_files.Buildings.RoomVentilationInfo import RoomVentilationAreaDetail
from code_files.Buildings.CompounWallDetails import CompoundWallDetails
from code_files.Buildings.court_yard_Details import CourtYardDetails

from logging_config import get_current_logger
ALLOWED_EXTENSIONS=['.dwg', '.dxf','.DWG','.DXF']

#to get unquoted text from an array 
translation = {39: None}

def return_line_coeffs(p1, p2):
	a = p1[1] - p2[1]
	b = p2[0] - p1[0]
	c = (p1[0]*p2[1]) - (p2[0]*p1[1])
	return [a, b, c]

def return_line_list(cl_list):
	line_list = []
	for i in range(len(cl_list) - 1):
		line_list.append(return_line_coeffs(cl_list[i], cl_list[i+1]))
	return line_list

def distance_from_line(point, line):

	dist = (np.abs(line[0]*point[0] + line[1]*point[1] + line[2]))/(math.sqrt(line[0]**2 + line[1]**2))
	return dist

#polygon list , cl_list - centerlist points 
def getMinWidthByCenterLine(point_list, cl_list):
	line_list = return_line_list(cl_list)
	dist_dict = {}
	
	for i, point in enumerate(point_list):
		for j, line in enumerate(line_list):
			dist = distance_from_line(point, line)
			dist_dict[f'point_{point}_line_{line}_dist'] = dist
	min_distance_across_all_points = min(dist_dict.values())
	points_with_min_distance = [key for key in dist_dict if dist_dict[key] == min_distance_across_all_points]
	#     print('distance_dict:', dist_dict)
	get_current_logger().debug('The minimum width of the figure is :', min_distance_across_all_points)
	get_current_logger().debug('The Points with minimum width:', points_with_min_distance)
	
	return min_distance_across_all_points

#since 3/20/2022
distance_calc = lambda pt1, pt2: np.sqrt((pt1[0] - pt2[0])**2 + (pt1[1] - pt2[1])**2)

# helper #2 for getMinWidthIrregularObjects
#Function to return the minimum distance for each point
#since 3/20/2022
def min_distance_for_point(point, point_coordinates, point_dict):
	
	distance_list = []
	for secondary_point, secondary_point_coordinates in point_dict.items():
		if point != secondary_point:
			distance_list.append(distance_calc(point_coordinates, secondary_point_coordinates))

	min_distance = min(distance_list)
	return min_distance

#Main Function for getMinWidthIrregularObjects 
#depends on two helper functions (distance_calc and min_distance_for_point)
#since 3/20/2022
def getMinWidthIrregularObjects(objectPoly) -> int :
	
	# printLog('debug','starting getMinWidthIrregularObjects')
	# printLog('debug','input type ' + str(type(objectPoly)))
	if (objectPoly is None ):
		return -1

	childIndivlwpoly = shapely.wkt.loads(str(objectPoly)  )
	lpoints  = list(childIndivlwpoly.exterior.coords)
	

	point_dict = {}
	for i, point in enumerate(lpoints[:-1]):
		point_dict[f'point_{i+1}'] = point

	# printLog('debug','points as dict ' + str(point_dict))

	#Function to calculate distance between points
	distance_calc = lambda pt1, pt2: np.sqrt((pt1[0] - pt2[0])**2 + (pt1[1] - pt2[1])**2)

	#Dictionary to store point along with the minimum distance associated with it
	min_distance_dict = {}
	for point, point_coordinates in point_dict.items():

		min_distance = min_distance_for_point(point, point_coordinates, point_dict)
		min_distance_dict[point] = min_distance
		
	min_distance_across_all_points = min(min_distance_dict.values())
	points_with_min_distance = [key for key in min_distance_dict if min_distance_dict[key] == min_distance_across_all_points]

	#Output Statements
	# printLog('debug','The minimum width of the figure is :', min_distance_across_all_points)
	# printLog('debug','The Points with minimum width:', points_with_min_distance)
	# printLog('debug','Done getMinWidthIrregularObjects')
	return min_distance_across_all_points


def getPointsAsListFromString(inputValue:str):

	if (inputValue is None or len(inputValue) <= 0 ):
		return []
	translation={39:None}
	
	inputValue=inputValue[1:-1]  #ignore [ and  ]
	# printLog('debug','getPointsAsListFromString inputValue ', inputValue)
	myreturnlist=[]

	for item in inputValue.translate(translation).split(','):
		# printLog('debug','item ', item)
		tmpList = item.split(' ')
		mytmpList = list()
		for t in tmpList :
			t = t.strip()
			#skip blank values 
			if ( len(t)> 0 ) :
				mytmpList.append(float(t))
		myreturnlist.append(mytmpList)

		# printLog('debug',' item ', mytmpList )

	return myreturnlist

#Function helper for getInternalRoadWidth 
#Fix 4/27/2022
def split(start,end,seg):  # this function used for Spliting the lines

	x_delta=(end[0]-start[0])/float(seg)

	y_delta=(end[1]-start[1])/float(seg)

	points=[]

	for i in range(1,seg):

		pts=(start[0]+i*x_delta,start[1]+i*y_delta)

		points.append(pts)

	return [start]+points+[end]

def get_ghmc_setbacks(modelspace):#folder:str,filename:str):

	resultsList=[]

	returnValueDict=dict()

	if (modelspace is None):
	#if (folder is None or filename is None):

		return returnValueDict

	try:

		get_current_logger().info('starting get_ghmc_setbacks ')

		msp=modelspace

		proposed_text=msp.query("TEXT MTEXT[layer=='_ProposedWork']")

		proposed_polygon=msp.query("LWPOLYLINE[layer=='_ProposedWork']")

		margin_data=msp.query("*[layer=='_MarginLine']")

		org_mtext=msp.query('TEXT MTEXT[layer=="_OrganizedOpenSpace"]')

		org_polygon=msp.query('LWPOLYLINE[layer=="_OrganizedOpenSpace"]')

		#msp=read_dxf.modelspace()

		#proposed work text

		for prop_text in proposed_text:

			prop_text_attribs=prop_text.dxfattribs()

			insert_prop_text_pts=prop_text_attribs.get('insert')

			prop_text_name=prop_text_attribs.get('text') if prop_text.dxftype()=='TEXT' else prop_text.plain_text()

			np_insert_prop_text_pts=np.array([insert_prop_text_pts[0],insert_prop_text_pts[1]]).round(2)

			prop_text_point=Point(np_insert_prop_text_pts)

			#proposed work polygon

			for lwpolyline in proposed_polygon:

				prop_pts=[x[0:2] for x in lwpolyline.get_points()]

				np_prop_pts=np.array(prop_pts).round(2)

				prop_poly1=Polygon(np_prop_pts)

				# check propposed name in proposed polygon

				if prop_poly1.contains(prop_text_point)==True or prop_poly1.touches(prop_text_point)==True:

					refid=lwpolyline.dxf.handle

					front_data=[]

					rear_data=[]

					side1_data=[]

					side2_data=[]

					front_coordinate_data=[]

					rear_coordinate_data=[]

					side1_coordinate_data=[]

					side2_coordinate_data=[]

					for tpl in lwpolyline.virtual_entities():

						if tpl.dxftype()=='LINE':

							start_pts=tpl.dxf.start

							end_pts=tpl.dxf.end

							linex=[[start_pts[0],start_pts[1]],[end_pts[0],end_pts[1]]]

							np_linex=np.array(linex).round(2)

							min_np_linex=np_linex.min(axis=0)

							#split_prop_line=split(linex[0],linex[1],2)

							prop_line=LineString(np_linex)

							for entity in margin_data:

								lstf=[]

								lstr=[]

								lsts1=[]

								lsts2=[]

								if entity.dxftype()=='INSERT':

									for x in entity.virtual_entities():

										# read only line

										if x.dxftype()=='LINE':

											if x.dxf.color==1:

												v1=x.dxf.start

												va=[v1[0],v1[1]]

												v2=x.dxf.end

												vb=[v2[0],v2[1]]

												lst=np.array([va,vb])

												margin_linef=LineString(lst)

												lstf.append(round(prop_line.distance(margin_linef),1))

												front_coordinate_data.append([linex,lst])

											elif(x.dxf.color== 6):

												v1=x.dxf.start

												va=(v1[0],v1[1])

												v2=x.dxf.end

												vb=(v2[0],v2[1])

												lst=[va,vb]

												margin_liner=LineString(lst)

												lstr.append(round(prop_line.distance(margin_liner),1))

												rear_coordinate_data.append([linex,lst])

											elif(x.dxf.color==5):

												v1=x.dxf.start

												va=(v1[0],v1[1])

												v2=x.dxf.end

												vb=(v2[0],v2[1])

												lst=[va,vb]

												margin_lines1=LineString(lst)

												lsts1.append(round(prop_line.distance(margin_lines1),1))

												side1_coordinate_data.append([linex,lst])

											elif(x.dxf.color==104):

												v1=x.dxf.start

												va=(v1[0],v1[1])

												v2=x.dxf.end

												vb=(v2[0],v2[1])

												lst=[va,vb]

												margin_lines2=LineString(lst)

												lsts2.append(round(prop_line.distance(margin_lines2),1))

												side2_coordinate_data.append([linex,lst])

										# read only arc

										elif x.dxftype()=='ARC':

											if x.dxf.color==1:

												v1=x.start_point

												va=[v1[0],v1[1]]

												v2=x.end_point

												vb=[v2[0],v2[1]]

												lst=np.array([va,vb])

												margin_linef=LineString(lst)

												lstf.append(round(prop_line.distance(margin_linef),1))

												front_coordinate_data.append([linex,lst])

											elif(x.dxf.color== 6):

												v1=x.start_point

												va=(v1[0],v1[1])

												v2=x.end_point

												vb=(v2[0],v2[1])

												lst=[va,vb]

												margin_liner=LineString(lst)

												lstr.append(round(prop_line.distance(margin_liner),1))

												rear_coordinate_data.append([linex,lst])

											elif(x.dxf.color==5):

												v1=x.start_point

												va=(v1[0],v1[1])

												v2=x.end_point

												vb=(v2[0],v2[1])

												lst=[va,vb]

												margin_lines1=LineString(lst)

												lsts1.append(round(prop_line.distance(margin_lines1),1))

												side1_coordinate_data.append([linex,lst])

											elif(x.dxf.color==104):

												v1=x.start_point

												va=(v1[0],v1[1])

												v2=x.end_point

												vb=(v2[0],v2[1])

												lst=[va,vb]

												margin_lines2=LineString(lst)

												lsts2.append(round(prop_line.distance(margin_lines2),1))

												side2_coordinate_data.append([linex,lst])

								elif(entity.dxftype()=='LINE'):

									if entity.dxf.color == 1:

										v1 = entity.dxf.start

										va = [v1[0], v1[1]]

										v2 = entity.dxf.end

										vb = [v2[0], v2[1]]

										lst = np.array([va, vb])

										margin_linef = LineString(lst)

										lstf.append(round(prop_line.distance(margin_linef), 1))

										front_coordinate_data.append([linex, lst])

									elif (entity.dxf.color == 6):

										v1 = entity.dxf.start

										va = (v1[0], v1[1])

										v2 = entity.dxf.end

										vb = (v2[0], v2[1])

										lst = [va, vb]

										margin_liner = LineString(lst)

										lstr.append(round(prop_line.distance(margin_liner), 1))

										rear_coordinate_data.append([linex, lst])

									elif (entity.dxf.color == 5):

										v1 = entity.dxf.start

										va = (v1[0], v1[1])

										v2 = entity.dxf.end

										vb = (v2[0], v2[1])

										lst = [va, vb]

										margin_lines1 = LineString(lst)

										lsts1.append(round(prop_line.distance(margin_lines1), 1))

										side1_coordinate_data.append([linex, lst])

									elif (entity.dxf.color == 104 or entity.dxf.color == 3):

										v1 = entity.dxf.start

										va = (v1[0], v1[1])

										v2 = entity.dxf.end

										vb = (v2[0], v2[1])

										lst = [va, vb]

										margin_lines2 = LineString(lst)

										lsts2.append(round(prop_line.distance(margin_lines2), 1))

										side2_coordinate_data.append([linex, lst])

								elif(entity.dxftype()=='ARC'):

									if entity.dxf.color == 1:

										v1 = entity.start_point

										va = [v1[0], v1[1]]

										v2 = entity.end_point

										vb = [v2[0], v2[1]]

										lst = np.array([va, vb])

										margin_linef = LineString(lst)

										lstf.append(round(prop_line.distance(margin_linef), 1))

										front_coordinate_data.append([linex, lst])

									elif (entity.dxf.color == 6):

										v1 = entity.start_point

										va = (v1[0], v1[1])

										v2 = entity.end_point

										vb = (v2[0], v2[1])

										lst = [va, vb]

										margin_liner = LineString(lst)

										lstr.append(round(prop_line.distance(margin_liner), 1))

										rear_coordinate_data.append([linex, lst])

									elif (entity.dxf.color == 5):

										v1 = entity.start_point

										va = (v1[0], v1[1])

										v2 = entity.end_point

										vb = (v2[0], v2[1])

										lst = [va, vb]

										margin_lines1 = LineString(lst)

										lsts1.append(round(prop_line.distance(margin_lines1), 1))

										side1_coordinate_data.append([linex, lst])

									elif (entity.dxf.color == 104 or entity.dxf.color == 3):

										v1 = entity.start_point

										va = (v1[0], v1[1])

										v2 = entity.end_point

										vb = (v2[0], v2[1])

										lst = [va, vb]

										margin_lines2 = LineString(lst)

										lsts2.append(round(prop_line.distance(margin_lines2), 1))

										side2_coordinate_data.append([linex, lst])

								if lstf!=[]:

									front_data.append(min(lstf))

								if lstr!=[]:

									rear_data.append(min(lstr))

								if lsts1!=[]:

									side1_data.append(min(lsts1))

								if lsts2!=[]:

									side2_data.append(min(lsts2))

						elif tpl.dxftype() == 'ARC':

							start_pts = tpl.start_point

							end_pts = tpl.end_point

							linex = [[start_pts[0], start_pts[1]], [end_pts[0], end_pts[1]]]

							np_linex = np.array(linex).round(2)

							min_np_linex = np_linex.min(axis=0)

							# split_prop_line=split(linex[0],linex[1],2)

							prop_line = LineString(np_linex)

							for entity in margin_data:

								lstf = []

								lstr = []

								lsts1 = []

								lsts2 = []

								if entity.dxftype()=='INSERT':

									for x in entity.virtual_entities():

										# read only line

										if x.dxftype() == 'LINE':

											if x.dxf.color == 1:

												v1 = x.dxf.start

												va = [v1[0], v1[1]]

												v2 = x.dxf.end

												vb = [v2[0], v2[1]]

												lst = np.array([va, vb])

												margin_linef = LineString(lst)

												lstf.append(round(prop_line.distance(margin_linef), 1))

												front_coordinate_data.append([linex, lst])

											elif (x.dxf.color == 6):

												v1 = x.dxf.start

												va = (v1[0], v1[1])

												v2 = x.dxf.end

												vb = (v2[0], v2[1])

												lst = [va, vb]

												margin_liner = LineString(lst)

												lstr.append(round(prop_line.distance(margin_liner), 1))

												rear_coordinate_data.append([linex, lst])

											elif (x.dxf.color == 5):

												v1 = x.dxf.start

												va = (v1[0], v1[1])

												v2 = x.dxf.end

												vb = (v2[0], v2[1])

												lst = [va, vb]

												margin_lines1 = LineString(lst)

												lsts1.append(round(prop_line.distance(margin_lines1), 1))

												side1_coordinate_data.append([linex, lst])

											elif (x.dxf.color == 104 or x.dxf.color == 3):

												v1 = x.dxf.start

												va = (v1[0], v1[1])

												v2 = x.dxf.end

												vb = (v2[0], v2[1])

												lst = [va, vb]

												margin_lines2 = LineString(lst)

												lsts2.append(round(prop_line.distance(margin_lines2), 1))

												side2_coordinate_data.append([linex, lst])

										#read only arc

										elif x.dxftype() == 'ARC':

											if x.dxf.color == 1:

												v1 = x.start_point

												va = [v1[0], v1[1]]

												v2 = x.end_point

												vb = [v2[0], v2[1]]

												lst = np.array([va, vb])

												margin_linef = LineString(lst)

												lstf.append(round(prop_line.distance(margin_linef), 1))

												front_coordinate_data.append([linex, lst])

											elif (x.dxf.color == 6):

												v1 = x.start_point

												va = (v1[0], v1[1])

												v2 = x.end_point

												vb = (v2[0], v2[1])

												lst = [va, vb]

												margin_liner = LineString(lst)

												lstr.append(round(prop_line.distance(margin_liner), 1))

												rear_coordinate_data.append([linex, lst])

											elif (x.dxf.color == 5):

												v1 = x.start_point

												va = (v1[0], v1[1])

												v2 = x.end_point

												vb = (v2[0], v2[1])

												lst = [va, vb]

												margin_lines1 = LineString(lst)

												lsts1.append(round(prop_line.distance(margin_lines1), 1))

												side1_coordinate_data.append([linex, lst])

											elif (x.dxf.color == 104 or x.dxf.color == 3):

												v1 = x.start_point

												va = (v1[0], v1[1])

												v2 = x.end_point

												vb = (v2[0], v2[1])

												lst = [va, vb]

												margin_lines2 = LineString(lst)

												lsts2.append(round(prop_line.distance(margin_lines2), 1))

												side2_coordinate_data.append([linex, lst])

								elif entity.dxftype() == 'LINE':

									if entity.dxf.color == 1:

										v1 = entity.dxf.start

										va = [v1[0], v1[1]]

										v2 = entity.dxf.end

										vb = [v2[0], v2[1]]

										lst = np.array([va, vb])

										margin_linef = LineString(lst)

										lstf.append(round(prop_line.distance(margin_linef), 1))

										front_coordinate_data.append([linex, lst])

									elif (entity.dxf.color == 6):

										v1 = entity.dxf.start

										va = (v1[0], v1[1])

										v2 = entity.dxf.end

										vb = (v2[0], v2[1])

										lst = [va, vb]

										margin_liner = LineString(lst)

										lstr.append(round(prop_line.distance(margin_liner), 1))

										rear_coordinate_data.append([linex, lst])

									elif (entity.dxf.color == 5):

										v1 = entity.dxf.start

										va = (v1[0], v1[1])

										v2 = entity.dxf.end

										vb = (v2[0], v2[1])

										lst = [va, vb]

										margin_lines1 = LineString(lst)

										lsts1.append(round(prop_line.distance(margin_lines1), 1))

										side1_coordinate_data.append([linex, lst])

									elif (entity.dxf.color == 104 or entity.dxf.color == 3):

										v1 = entity.dxf.start

										va = (v1[0], v1[1])

										v2 = entity.dxf.end

										vb = (v2[0], v2[1])

										lst = [va, vb]

										margin_lines2 = LineString(lst)

										lsts2.append(round(prop_line.distance(margin_lines2), 1))

										side2_coordinate_data.append([linex, lst])

								elif entity.dxftype() == 'ARC':

									if entity.dxf.color == 1:

										v1 = entity.start_point

										va = [v1[0], v1[1]]

										v2 = entity.end_point

										vb = [v2[0], v2[1]]

										lst = np.array([va, vb])

										margin_linef = LineString(lst)

										lstf.append(round(prop_line.distance(margin_linef), 1))

										front_coordinate_data.append([linex, lst])

									elif (entity.dxf.color == 6):

										v1 = entity.start_point

										va = (v1[0], v1[1])

										v2 = entity.end_point

										vb = (v2[0], v2[1])

										lst = [va, vb]

										margin_liner = LineString(lst)

										lstr.append(round(prop_line.distance(margin_liner), 1))

										rear_coordinate_data.append([linex, lst])

									elif (entity.dxf.color == 5):

										v1 = entity.start_point

										va = (v1[0], v1[1])

										v2 = entity.end_point

										vb = (v2[0], v2[1])

										lst = [va, vb]

										margin_lines1 = LineString(lst)

										lsts1.append(round(prop_line.distance(margin_lines1), 1))

										side1_coordinate_data.append([linex, lst])

									elif (entity.dxf.color == 104 or entity.dxf.color == 3):

										v1 = entity.start_point

										va = (v1[0], v1[1])

										v2 = entity.end_point

										vb = (v2[0], v2[1])

										lst = [va, vb]

										margin_lines2 = LineString(lst)

										lsts2.append(round(prop_line.distance(margin_lines2), 1))

										side2_coordinate_data.append([linex, lst])

								if lstf != []:

									front_data.append(min(lstf))

								if lstr != []:

									rear_data.append(min(lstr))

								if lsts1 != []:

									side1_data.append(min(lsts1))

								if lsts2 != []:

									side2_data.append(min(lsts2))

					# for Front side  data

					fline_pts_value=[]

					fline_pts=[]

					for fdata in front_coordinate_data:

						f_prop_linex=LineString(fdata[0])

						f_margin_linex=LineString(fdata[1])

						#match minimum distance value proposed line to front line

						if round(f_prop_linex.distance(f_margin_linex),1)==min(front_data):

							# get match line of proposed line

							f_np_prop_linex=np.array(fdata[0]).round(2)

							# split this line

							prop_line_splitf=split(f_np_prop_linex[0],f_np_prop_linex[1],4)

							# remove first amd last point

							for prop_splitf_pts in prop_line_splitf[1:-1]:

								np_prop_splitf_pts=np.array(prop_splitf_pts).round(2)

								prop_splitf_point=Point(np_prop_splitf_pts)

								fline_pts_value.append(round(prop_splitf_point.distance(f_margin_linex),1))

								fline_pts.append(np_prop_splitf_pts)

					# for front side

					for fdata_x in front_coordinate_data:

						f_prop_linex_x=LineString(fdata_x[0])

						f_margin_linex_x=LineString(fdata_x[1])

						if round(f_prop_linex_x.distance(f_margin_linex_x),1)==min(front_data):

							np_prop_linex_x=np.array(fdata_x[0]).round(2)

							max_prop_linex_x=np_prop_linex_x.max(axis=0).round(2)

							min_prop_linex_x=np_prop_linex_x.min(axis=0).round(2)

							for x_fline_pts in fline_pts:

								np_x_fline_pts=np.array(x_fline_pts).round(2)

								x_fline_point=Point(np_x_fline_pts)

								#check point in this line or not

								if ((max_prop_linex_x[0]>=np_x_fline_pts[0] and min_prop_linex_x[0]<=np_x_fline_pts[0]) and (max_prop_linex_x[1]>=np_x_fline_pts[1] and min_prop_linex_x[1]<=np_x_fline_pts[1])):

									# match minmum distance of point to front line

									if round(x_fline_point.distance(f_margin_linex_x),1)==min(fline_pts_value):

										# y value is  equal

										if np_prop_linex_x[0,1]==np_prop_linex_x[1,1]:

										   # proposed work polygon convert into lines

											for x_f_prop_line in lwpolyline.virtual_entities():

												if x_f_prop_line.dxftype()=='LINE':

													x_f_prop_start_pts=[x_f_prop_line.dxf.start[0],x_f_prop_line.dxf.start[1]]

													x_f_prop_end_pts=[x_f_prop_line.dxf.end[0],x_f_prop_line.dxf.end[1]]

													x_prop_line=[x_f_prop_start_pts,x_f_prop_end_pts]

													np_x_prop_line=np.array(x_prop_line).round(2)

													#check this direction of all proposed line

													if np_x_prop_line[0,1]==np_prop_linex_x[0,1] and np_x_prop_line[1,1]==np_prop_linex_x[1,1]:

														x_prop_work_line=LineString(np_x_prop_line)

														min_np_x_prop_line=np_x_prop_line.min(axis=0)

														max_np_x_prop_line=np_x_prop_line.max(axis=0)

														# tot_lot polygon

														for organized_open_space_text in org_mtext:

															org_open_space=organized_open_space_text.dxf.text if organized_open_space_text.dxftype()=='TEXT' else organized_open_space_text.plain_text()

															if org_open_space=='Tot-lot' or org_open_space=='Tot lot':

																organized_attrib=organized_open_space_text.dxfattribs()

																tot_lot_pts=organized_attrib['insert']

																np_tot_lot_pts=np.array([tot_lot_pts[0],tot_lot_pts[1]]).round(2)

																tot_lot_coords=Point(np_tot_lot_pts)

																for organized_open_space_poly in org_polygon:

																	organized_open_space_poly_pts=[y[0:2] for y in organized_open_space_poly.get_points()]

																	np_organized_open_space_poly_pts=np.array(organized_open_space_poly_pts).round(2)

																	organized_space_poly=Polygon(np_organized_open_space_poly_pts)

																	for f_tot_lot_line in organized_open_space_poly.virtual_entities():

																		if f_tot_lot_line.dxftype()=='LINE':

																			start_f_tot_lot_line_pts=[f_tot_lot_line.dxf.start[0],f_tot_lot_line.dxf.start[1]]

																			end_f_tot_lot_line_pts=[f_tot_lot_line.dxf.end[0],f_tot_lot_line.dxf.end[1]]

																			np_f_tot_lot_line_pts=np.array([start_f_tot_lot_line_pts,end_f_tot_lot_line_pts]).round(2)

																			split_np_f_tot_lot_line_pts=split(np_f_tot_lot_line_pts[0],np_f_tot_lot_line_pts[1],4)

																			#check tot-lot text in polygon or not

																			if organized_space_poly.contains(tot_lot_coords)==True:

																				# tot-lot polygon convert into points

																				for f_tot_pts in split_np_f_tot_lot_line_pts:

																					np_f_tot_pts=np.array(f_tot_pts).round(2)

																					np_f_tot_point=Point(np_f_tot_pts)

																					#check propposed polygon to totlot polygon distance not 0

																					if round(prop_poly1.distance(organized_space_poly))!=0:

																						#tot-lot point in proposed line or not

																						if (min_np_x_prop_line[0]<=np_f_tot_pts[0] and  max_np_x_prop_line[0]>=np_f_tot_pts[0]) or (min_np_x_prop_line[1]<=np_f_tot_pts[1] and  max_np_x_prop_line[1]>=np_f_tot_pts[1]):

																							front_data.append(round(np_f_tot_point.distance(x_prop_work_line),2))

																							#check propposed polygon to totlot polygon distance is 0

																						elif(round(prop_poly1.distance(organized_space_poly))==0):

																							front_data.append(round(organized_space_poly.distance(f_margin_linex_x),2))

																		elif f_tot_lot_line.dxftype() == 'ARC':

																			start_f_tot_lot_line_pts = [
																				f_tot_lot_line.start_point[0],
																				f_tot_lot_line.start_point[1]]

																			end_f_tot_lot_line_pts = [
																				f_tot_lot_line.end_point[0],
																				f_tot_lot_line.end_point[1]]

																			np_f_tot_lot_line_pts = np.array(
																				[start_f_tot_lot_line_pts,
																				 end_f_tot_lot_line_pts]).round(2)

																			split_np_f_tot_lot_line_pts = split(
																				np_f_tot_lot_line_pts[0],
																				np_f_tot_lot_line_pts[1], 4)

																			# check tot-lot text in polygon or not

																			if organized_space_poly.contains(
																					tot_lot_coords) == True:

																				# tot-lot polygon convert into points

																				for f_tot_pts in split_np_f_tot_lot_line_pts:

																					np_f_tot_pts = np.array(
																						f_tot_pts).round(2)

																					np_f_tot_point = Point(np_f_tot_pts)

																					# check propposed polygon to totlot polygon distance not 0

																					if round(prop_poly1.distance(
																							organized_space_poly)) != 0:

																						# tot-lot point in proposed line or not

																						if (min_np_x_prop_line[0] <=
																							np_f_tot_pts[0] and
																							max_np_x_prop_line[0] >=
																							np_f_tot_pts[0]) or (
																								min_np_x_prop_line[1] <=
																								np_f_tot_pts[1] and
																								max_np_x_prop_line[1] >=
																								np_f_tot_pts[1]):

																							front_data.append(round(
																								np_f_tot_point.distance(
																									x_prop_work_line), 2))

																						# check propposed polygon to totlot polygon distance is 0

																						elif (round(prop_poly1.distance(
																								organized_space_poly)) == 0):

																							front_data.append(round(
																								organized_space_poly.distance(
																									f_margin_linex_x), 2))
														#This loop for front line to prop_work block

														for fprop_work_poly in proposed_polygon:

															fprop_poly_pts=[a[0:2] for a in fprop_work_poly.get_points()]

															np_fprop_poly_pts=np.array(fprop_poly_pts).round(2)

															fprop_poly=Polygon(np_fprop_poly_pts)

															 # proposed work polygon convert into points

															for f_prop_pts in np_fprop_poly_pts:

																np_f_prop_pts=np.array(f_prop_pts).round(2)

																np_f_prop_point=Point(np_f_prop_pts)

																# check proposed polygon to another proposed polygon not 0

																if round(prop_poly1.distance(fprop_poly))!=0:

																	#check proposed polygon point in proposed polygon line

																	if (min_np_x_prop_line[0]<=np_f_prop_pts[0] and  max_np_x_prop_line[0]>=np_f_prop_pts[0]) or (min_np_x_prop_line[1]<=np_f_prop_pts[1] and  max_np_x_prop_line[1]>=np_f_prop_pts[1]):

																		front_data.append(round(np_f_prop_point.distance(x_prop_work_line),2))

																	else:

																		for f_prop_line in fprop_work_poly.virtual_entities():

																			if f_prop_line.dxftype()=='LINE':

																				f_start_prop_pts=[f_prop_line.dxf.start[0],f_prop_line.dxf.start[1]]

																				f_end_prop_pts=[f_prop_line.dxf.end[0],f_prop_line.dxf.end[1]]

																				f_prop_line=[f_start_prop_pts,f_end_prop_pts]

																				np_f_prop_line=np.array(f_prop_line).round(2)

																				f_prop_linea=LineString(np_f_prop_line)

																				max_np_f_prop_line=np_f_prop_line.max(axis=0).round(2)

																				min_np_f_prop_line=np_f_prop_line.min(axis=0).round(2)

																				for f_prop_line_pts in np_prop_linex_x:

																					np_f_prop_line_pts=np.array(f_prop_line_pts).round(2)

																					f_prop_line_point=Point(np_f_prop_line_pts)

																					if (min_np_f_prop_line[0]<=np_f_prop_line_pts[0] and  max_np_f_prop_line[0]>=np_f_prop_line_pts[0]) or (min_np_f_prop_line[1]<=np_f_prop_line_pts[1] and  max_np_f_prop_line[1]>=np_f_prop_line_pts[1]):

																						front_data.append(round(f_prop_line_point.distance(f_prop_linea),2))

																			elif f_prop_line.dxftype() == 'ARC':

																				f_start_prop_pts = [
																					f_prop_line.start_point[0],
																					f_prop_line.start_point[1]]

																				f_end_prop_pts = [f_prop_line.end_point[0],
																								  f_prop_line.end_point[1]]

																				f_prop_line = [f_start_prop_pts,
																							   f_end_prop_pts]

																				np_f_prop_line = np.array(
																					f_prop_line).round(2)

																				f_prop_linea = LineString(np_f_prop_line)

																				max_np_f_prop_line = np_f_prop_line.max(
																					axis=0).round(2)

																				min_np_f_prop_line = np_f_prop_line.min(
																					axis=0).round(2)

																				for f_prop_line_pts in np_prop_linex_x:

																					np_f_prop_line_pts = np.array(
																						f_prop_line_pts).round(2)

																					f_prop_line_point = Point(
																						np_f_prop_line_pts)

																					if (min_np_f_prop_line[0] <=
																						np_f_prop_line_pts[0] and
																						max_np_f_prop_line[0] >=
																						np_f_prop_line_pts[0]) or (
																							min_np_f_prop_line[1] <=
																							np_f_prop_line_pts[1] and
																							max_np_f_prop_line[1] >=
																							np_f_prop_line_pts[1]):
																						front_data.append(round(
																							f_prop_line_point.distance(
																								f_prop_linea), 2))

												elif x_f_prop_line.dxftype() == 'ARC':

													x_f_prop_start_pts = [x_f_prop_line.start_point[0],
																		  x_f_prop_line.start_point[1]]

													x_f_prop_end_pts = [x_f_prop_line.end_point[0],
																		x_f_prop_line.end_point[1]]

													x_prop_line = [x_f_prop_start_pts, x_f_prop_end_pts]

													np_x_prop_line = np.array(x_prop_line).round(2)

													# check this direction of all proposed line

													if np_x_prop_line[0, 1] == np_prop_linex_x[0, 1] and np_x_prop_line[
														1, 1] == np_prop_linex_x[1, 1]:

														x_prop_work_line = LineString(np_x_prop_line)

														min_np_x_prop_line = np_x_prop_line.min(axis=0)

														max_np_x_prop_line = np_x_prop_line.max(axis=0)

														# tot_lot polygon

														for organized_open_space_text in org_mtext:

															org_open_space=organized_open_space_text.dxf.text if organized_open_space_text.dxftype()=='TEXT' else organized_open_space_text.plain_text()

															if org_open_space == 'Tot-lot' or org_open_space == 'Tot lot':

																organized_attrib = organized_open_space_text.dxfattribs()

																tot_lot_pts = organized_attrib['insert']

																np_tot_lot_pts = np.array(
																	[tot_lot_pts[0], tot_lot_pts[1]]).round(2)

																tot_lot_coords = Point(np_tot_lot_pts)

																for organized_open_space_poly in msp.query(
																		'LWPOLYLINE[layer=="_OrganizedOpenSpace"]'):

																	organized_open_space_poly_pts = [y[0:2] for y in
																									 organized_open_space_poly.get_points()]

																	np_organized_open_space_poly_pts = np.array(
																		organized_open_space_poly_pts).round(2)

																	organized_space_poly = Polygon(
																		np_organized_open_space_poly_pts)

																	for f_tot_lot_line in organized_open_space_poly.virtual_entities():

																		if f_tot_lot_line.dxftype() == 'LINE':

																			start_f_tot_lot_line_pts = [
																				f_tot_lot_line.dxf.start[0],
																				f_tot_lot_line.dxf.start[1]]

																			end_f_tot_lot_line_pts = [
																				f_tot_lot_line.dxf.end[0],
																				f_tot_lot_line.dxf.end[1]]

																			np_f_tot_lot_line_pts = np.array(
																				[start_f_tot_lot_line_pts,
																				 end_f_tot_lot_line_pts]).round(2)

																			split_np_f_tot_lot_line_pts = split(
																				np_f_tot_lot_line_pts[0],
																				np_f_tot_lot_line_pts[1], 4)

																			# check tot-lot text in polygon or not

																			if organized_space_poly.contains(
																					tot_lot_coords) == True:

																				# tot-lot polygon convert into points

																				for f_tot_pts in split_np_f_tot_lot_line_pts:

																					np_f_tot_pts = np.array(
																						f_tot_pts).round(2)

																					np_f_tot_point = Point(np_f_tot_pts)

																					# check propposed polygon to totlot polygon distance not 0

																					if round(prop_poly1.distance(
																							organized_space_poly)) != 0:

																						# tot-lot point in proposed line or not

																						if (min_np_x_prop_line[0] <=
																							np_f_tot_pts[0] and
																							max_np_x_prop_line[0] >=
																							np_f_tot_pts[0]) or (
																								min_np_x_prop_line[1] <=
																								np_f_tot_pts[1] and
																								max_np_x_prop_line[1] >=
																								np_f_tot_pts[1]):

																							front_data.append(round(
																								np_f_tot_point.distance(
																									x_prop_work_line),
																								2))

																						# check propposed polygon to totlot polygon distance is 0

																						elif (round(prop_poly1.distance(
																								organized_space_poly)) == 0):

																							front_data.append(round(
																								organized_space_poly.distance(
																									f_margin_linex_x),
																								2))
																		elif f_tot_lot_line.dxftype() == 'ARC':

																			start_f_tot_lot_line_pts = [
																				f_tot_lot_line.start_point[0],
																				f_tot_lot_line.start_point[1]]

																			end_f_tot_lot_line_pts = [
																				f_tot_lot_line.end_point[0],
																				f_tot_lot_line.end_point[1]]

																			np_f_tot_lot_line_pts = np.array(
																				[start_f_tot_lot_line_pts,
																				 end_f_tot_lot_line_pts]).round(2)

																			split_np_f_tot_lot_line_pts = split(
																				np_f_tot_lot_line_pts[0],
																				np_f_tot_lot_line_pts[1], 4)

																			# check tot-lot text in polygon or not

																			if organized_space_poly.contains(
																					tot_lot_coords) == True:

																				# tot-lot polygon convert into points

																				for f_tot_pts in split_np_f_tot_lot_line_pts:

																					np_f_tot_pts = np.array(
																						f_tot_pts).round(2)

																					np_f_tot_point = Point(np_f_tot_pts)

																					# check propposed polygon to totlot polygon distance not 0

																					if round(prop_poly1.distance(
																							organized_space_poly)) != 0:

																						# tot-lot point in proposed line or not

																						if (min_np_x_prop_line[0] <=
																							np_f_tot_pts[0] and
																							max_np_x_prop_line[0] >=
																							np_f_tot_pts[0]) or (
																								min_np_x_prop_line[1] <=
																								np_f_tot_pts[1] and
																								max_np_x_prop_line[1] >=
																								np_f_tot_pts[1]):

																							front_data.append(round(
																								np_f_tot_point.distance(
																									x_prop_work_line),
																								2))

																						# check propposed polygon to totlot polygon distance is 0

																						elif (round(prop_poly1.distance(
																								organized_space_poly)) == 0):

																							front_data.append(round(
																								organized_space_poly.distance(
																									f_margin_linex_x),
																								2))
														# This loop for front line to prop_work block

														for fprop_work_poly in msp.query(
																'LWPOLYLINE[layer=="_ProposedWork"]'):

															fprop_poly_pts = [a[0:2] for a in
																			  fprop_work_poly.get_points()]

															np_fprop_poly_pts = np.array(fprop_poly_pts).round(2)

															fprop_poly = Polygon(np_fprop_poly_pts)

															# proposed work polygon convert into points

															for f_prop_pts in np_fprop_poly_pts:

																np_f_prop_pts = np.array(f_prop_pts).round(2)

																np_f_prop_point = Point(np_f_prop_pts)

																# check proposed polygon to another proposed polygon not 0

																if round(prop_poly1.distance(fprop_poly)) != 0:

																	# check proposed polygon point in proposed polygon line

																	if (min_np_x_prop_line[0] <= np_f_prop_pts[0] and
																		max_np_x_prop_line[0] >= np_f_prop_pts[0]) or (
																			min_np_x_prop_line[1] <= np_f_prop_pts[
																		1] and max_np_x_prop_line[1] >= np_f_prop_pts[
																				1]):

																		front_data.append(round(
																			np_f_prop_point.distance(x_prop_work_line),
																			2))

																	else:

																		for f_prop_line in fprop_work_poly.virtual_entities():

																			if f_prop_line.dxftype() == 'LINE':

																				f_start_prop_pts = [
																					f_prop_line.dxf.start[0],
																					f_prop_line.dxf.start[1]]

																				f_end_prop_pts = [
																					f_prop_line.dxf.end[0],
																					f_prop_line.dxf.end[1]]

																				f_prop_line = [f_start_prop_pts,
																							   f_end_prop_pts]

																				np_f_prop_line = np.array(
																					f_prop_line).round(2)

																				f_prop_linea = LineString(
																					np_f_prop_line)

																				max_np_f_prop_line = np_f_prop_line.max(
																					axis=0).round(2)

																				min_np_f_prop_line = np_f_prop_line.min(
																					axis=0).round(2)

																				for f_prop_line_pts in np_prop_linex_x:

																					np_f_prop_line_pts = np.array(
																						f_prop_line_pts).round(2)

																					f_prop_line_point = Point(
																						np_f_prop_line_pts)

																					if (min_np_f_prop_line[0] <=
																						np_f_prop_line_pts[0] and
																						max_np_f_prop_line[0] >=
																						np_f_prop_line_pts[0]) or (
																							min_np_f_prop_line[1] <=
																							np_f_prop_line_pts[1] and
																							max_np_f_prop_line[1] >=
																							np_f_prop_line_pts[1]):
																						front_data.append(round(
																							f_prop_line_point.distance(
																								f_prop_linea), 2))
																			elif f_prop_line.dxftype() == 'ARC':

																				f_start_prop_pts = [
																					f_prop_line.start_point[0],
																					f_prop_line.start_point[1]]

																				f_end_prop_pts = [
																					f_prop_line.end_point[0],
																					f_prop_line.end_point[1]]

																				f_prop_line = [f_start_prop_pts,
																							   f_end_prop_pts]

																				np_f_prop_line = np.array(
																					f_prop_line).round(2)

																				f_prop_linea = LineString(
																					np_f_prop_line)

																				max_np_f_prop_line = np_f_prop_line.max(
																					axis=0).round(2)

																				min_np_f_prop_line = np_f_prop_line.min(
																					axis=0).round(2)

																				for f_prop_line_pts in np_prop_linex_x:

																					np_f_prop_line_pts = np.array(
																						f_prop_line_pts).round(2)

																					f_prop_line_point = Point(
																						np_f_prop_line_pts)

																					if (min_np_f_prop_line[0] <=
																						np_f_prop_line_pts[0] and
																						max_np_f_prop_line[0] >=
																						np_f_prop_line_pts[0]) or (
																							min_np_f_prop_line[1] <=
																							np_f_prop_line_pts[1] and
																							max_np_f_prop_line[1] >=
																							np_f_prop_line_pts[1]):
																						front_data.append(round(
																							f_prop_line_point.distance(
																								f_prop_linea), 2))
										#used for x axis value is equal

										elif(np_prop_linex_x[0,0]==np_prop_linex_x[1,0]):

											for x_f_prop_line in lwpolyline.virtual_entities():

												if x_f_prop_line.dxftype()=='LINE':

													x_f_prop_start_pts=[x_f_prop_line.dxf.start[0],x_f_prop_line.dxf.start[1]]

													x_f_prop_end_pts=[x_f_prop_line.dxf.end[0],x_f_prop_line.dxf.end[1]]

													x_prop_line=[x_f_prop_start_pts,x_f_prop_end_pts]

													np_x_prop_line=np.array(x_prop_line).round(2)

													if np_x_prop_line[0,0]==np_prop_linex_x[0,0] and np_x_prop_line[1,0]==np_prop_linex_x[1,0]:

														x_prop_work_line=LineString(np_x_prop_line)

														min_np_x_prop_line=np_x_prop_line.min(axis=0)

														max_np_x_prop_line=np_x_prop_line.max(axis=0)

														# tot lot data

														for organized_open_space_text in org_mtext:

															org_open_space = organized_open_space_text.dxf.text if organized_open_space_text.dxftype() == 'TEXT' else organized_open_space_text.plain_text()

															if org_open_space=='Tot-lot' or org_open_space=='Tot lot':

																organized_attrib=organized_open_space_text.dxfattribs()

																tot_lot_pts=organized_attrib['insert']

																np_tot_lot_pts=np.array([tot_lot_pts[0],tot_lot_pts[1]]).round(2)

																tot_lot_coords=Point(np_tot_lot_pts)

																for organized_open_space_poly in org_polygon:

																	organized_open_space_poly_pts=[y[0:2] for y in organized_open_space_poly.get_points()]

																	np_organized_open_space_poly_pts=np.array(organized_open_space_poly_pts).round(2)

																	organized_space_poly=Polygon(np_organized_open_space_poly_pts)

																	for f_tot_lot_line in organized_open_space_poly.virtual_entities():

																		if f_tot_lot_line.dxftype()=='LINE':

																			start_f_tot_lot_line_pts=[f_tot_lot_line.dxf.start[0],f_tot_lot_line.dxf.start[1]]

																			end_f_tot_lot_line_pts=[f_tot_lot_line.dxf.end[0],f_tot_lot_line.dxf.end[1]]

																			np_f_tot_lot_line_pts=np.array([start_f_tot_lot_line_pts,end_f_tot_lot_line_pts]).round(2)

																			split_np_f_tot_lot_line_pts=split(np_f_tot_lot_line_pts[0],np_f_tot_lot_line_pts[1],4)

																			if organized_space_poly.contains(tot_lot_coords)==True:

																				for f_tot_pts in split_np_f_tot_lot_line_pts:

																					np_f_tot_pts=np.array(f_tot_pts).round(2)

																					np_f_tot_point=Point(np_f_tot_pts)

																					if round(prop_poly1.distance(organized_space_poly))!=0:

																						if (min_np_x_prop_line[0]<=np_f_tot_pts[0] and  max_np_x_prop_line[0]>=np_f_tot_pts[0]) or (min_np_x_prop_line[1]<=np_f_tot_pts[1] and  max_np_x_prop_line[1]>=np_f_tot_pts[1]):

																							front_data.append(round(np_f_tot_point.distance(x_prop_work_line),2))

																					elif(round(prop_poly1.distance(organized_space_poly))==0):

																						front_data.append(round(organized_space_poly.distance(f_margin_linex_x),2))
																		elif f_tot_lot_line.dxftype() == 'ARC':

																			start_f_tot_lot_line_pts = [
																				f_tot_lot_line.start_point[0],
																				f_tot_lot_line.start_point[1]]

																			end_f_tot_lot_line_pts = [
																				f_tot_lot_line.end_point[0],
																				f_tot_lot_line.end_point[1]]

																			np_f_tot_lot_line_pts = np.array(
																				[start_f_tot_lot_line_pts,
																				 end_f_tot_lot_line_pts]).round(2)

																			split_np_f_tot_lot_line_pts = split(
																				np_f_tot_lot_line_pts[0],
																				np_f_tot_lot_line_pts[1], 4)

																			if organized_space_poly.contains(
																					tot_lot_coords) == True:

																				for f_tot_pts in split_np_f_tot_lot_line_pts:

																					np_f_tot_pts = np.array(
																						f_tot_pts).round(2)

																					np_f_tot_point = Point(np_f_tot_pts)

																					if round(prop_poly1.distance(
																							organized_space_poly)) != 0:

																						if (min_np_x_prop_line[0] <=
																							np_f_tot_pts[0] and
																							max_np_x_prop_line[0] >=
																							np_f_tot_pts[0]) or (
																								min_np_x_prop_line[1] <=
																								np_f_tot_pts[1] and
																								max_np_x_prop_line[1] >=
																								np_f_tot_pts[1]):
																							front_data.append(round(
																								np_f_tot_point.distance(
																									x_prop_work_line),
																								2))

																					elif (round(prop_poly1.distance(
																							organized_space_poly)) == 0):

																						front_data.append(round(
																							organized_space_poly.distance(
																								f_margin_linex_x), 2))
														#This loop for front line to prop_work block

														for fprop_work_poly in proposed_polygon:

															fprop_poly_pts=[a[0:2] for a in fprop_work_poly.get_points()]

															np_fprop_poly_pts=np.array(fprop_poly_pts).round(2)

															fprop_poly=Polygon(np_fprop_poly_pts)

															for f_prop_pts in np_fprop_poly_pts:

																np_f_prop_pts=np.array(f_prop_pts).round(2)

																np_f_prop_point=Point(np_f_prop_pts)

																if round(prop_poly1.distance(fprop_poly))!=0:

																	if (min_np_x_prop_line[0]<=np_f_prop_pts[0] and  max_np_x_prop_line[0]>=np_f_prop_pts[0]) or (min_np_x_prop_line[1]<=np_f_prop_pts[1] and  max_np_x_prop_line[1]>=np_f_prop_pts[1]):

																		front_data.append(round(np_f_prop_point.distance(x_prop_work_line),2))

																	else:

																		for f_prop_line in fprop_work_poly.virtual_entities():

																			f_start_prop_pts=[f_prop_line.dxf.start[0],f_prop_line.dxf.start[1]]

																			f_end_prop_pts=[f_prop_line.dxf.end[0],f_prop_line.dxf.end[1]]

																			f_prop_line=[f_start_prop_pts,f_end_prop_pts]

																			np_f_prop_line=np.array(f_prop_line).round(2)

																			f_prop_linea=LineString(np_f_prop_line)

																			max_np_f_prop_line=np_f_prop_line.max(axis=0).round(2)

																			min_np_f_prop_line=np_f_prop_line.min(axis=0).round(2)

																			for f_prop_line_pts in np_prop_linex_x:

																				np_f_prop_line_pts=np.array(f_prop_line_pts).round(2)

																				f_prop_line_point=Point(np_f_prop_line_pts)

																				if (min_np_f_prop_line[0]<=np_f_prop_line_pts[0] and  max_np_f_prop_line[0]>=np_f_prop_line_pts[0]) or (min_np_f_prop_line[1]<=np_f_prop_line_pts[1] and  max_np_f_prop_line[1]>=np_f_prop_line_pts[1]):

																					front_data.append(round(f_prop_line_point.distance(f_prop_linea),2))

												elif x_f_prop_line.dxftype() == 'ARC':

													x_f_prop_start_pts = [x_f_prop_line.start_point[0],
																		  x_f_prop_line.start_point[1]]

													x_f_prop_end_pts = [x_f_prop_line.end_point[0],
																		x_f_prop_line.end_point[1]]

													x_prop_line = [x_f_prop_start_pts, x_f_prop_end_pts]

													np_x_prop_line = np.array(x_prop_line).round(2)

													if np_x_prop_line[0, 0] == np_prop_linex_x[0, 0] and np_x_prop_line[
														1, 0] == np_prop_linex_x[1, 0]:

														x_prop_work_line = LineString(np_x_prop_line)

														min_np_x_prop_line = np_x_prop_line.min(axis=0)

														max_np_x_prop_line = np_x_prop_line.max(axis=0)

														# tot lot data

														for organized_open_space_text in org_mtext:

															org_open_space = organized_open_space_text.dxf.text if organized_open_space_text.dxftype() == 'TEXT' else organized_open_space_text.plain_text()

															if org_open_space == 'Tot-lot' or org_open_space == 'Tot lot':

																organized_attrib = organized_open_space_text.dxfattribs()

																tot_lot_pts = organized_attrib['insert']

																np_tot_lot_pts = np.array(
																	[tot_lot_pts[0], tot_lot_pts[1]]).round(2)

																tot_lot_coords = Point(np_tot_lot_pts)

																for organized_open_space_poly in org_polygon:

																	organized_open_space_poly_pts = [y[0:2] for y in
																									 organized_open_space_poly.get_points()]

																	np_organized_open_space_poly_pts = np.array(
																		organized_open_space_poly_pts).round(2)

																	organized_space_poly = Polygon(
																		np_organized_open_space_poly_pts)

																	for f_tot_lot_line in organized_open_space_poly.virtual_entities():

																		if f_tot_lot_line.dxftype() == 'LINE':

																			start_f_tot_lot_line_pts = [
																				f_tot_lot_line.dxf.start[0],
																				f_tot_lot_line.dxf.start[1]]

																			end_f_tot_lot_line_pts = [
																				f_tot_lot_line.dxf.end[0],
																				f_tot_lot_line.dxf.end[1]]

																			np_f_tot_lot_line_pts = np.array(
																				[start_f_tot_lot_line_pts,
																				 end_f_tot_lot_line_pts]).round(2)

																			split_np_f_tot_lot_line_pts = split(
																				np_f_tot_lot_line_pts[0],
																				np_f_tot_lot_line_pts[1], 4)

																			if organized_space_poly.contains(
																					tot_lot_coords) == True:

																				for f_tot_pts in split_np_f_tot_lot_line_pts:

																					np_f_tot_pts = np.array(
																						f_tot_pts).round(2)

																					np_f_tot_point = Point(np_f_tot_pts)

																					if round(prop_poly1.distance(
																							organized_space_poly)) != 0:

																						if (min_np_x_prop_line[0] <=
																							np_f_tot_pts[0] and
																							max_np_x_prop_line[0] >=
																							np_f_tot_pts[0]) or (
																								min_np_x_prop_line[1] <=
																								np_f_tot_pts[1] and
																								max_np_x_prop_line[1] >=
																								np_f_tot_pts[1]):
																							front_data.append(round(
																								np_f_tot_point.distance(
																									x_prop_work_line),
																								2))

																					elif (round(prop_poly1.distance(
																							organized_space_poly)) == 0):

																						front_data.append(round(
																							organized_space_poly.distance(
																								f_margin_linex_x), 2))

																		elif f_tot_lot_line.dxftype() == 'ARC':

																			start_f_tot_lot_line_pts = [
																				f_tot_lot_line.start_point[0],
																				f_tot_lot_line.start_point[1]]

																			end_f_tot_lot_line_pts = [
																				f_tot_lot_line.end_point[0],
																				f_tot_lot_line.end_point[1]]

																			np_f_tot_lot_line_pts = np.array(
																				[start_f_tot_lot_line_pts,
																				 end_f_tot_lot_line_pts]).round(2)

																			split_np_f_tot_lot_line_pts = split(
																				np_f_tot_lot_line_pts[0],
																				np_f_tot_lot_line_pts[1], 4)

																			if organized_space_poly.contains(
																					tot_lot_coords) == True:

																				for f_tot_pts in split_np_f_tot_lot_line_pts:

																					np_f_tot_pts = np.array(
																						f_tot_pts).round(2)

																					np_f_tot_point = Point(np_f_tot_pts)

																					if round(prop_poly1.distance(
																							organized_space_poly)) != 0:

																						if (min_np_x_prop_line[0] <=
																							np_f_tot_pts[0] and
																							max_np_x_prop_line[0] >=
																							np_f_tot_pts[0]) or (
																								min_np_x_prop_line[1] <=
																								np_f_tot_pts[1] and
																								max_np_x_prop_line[1] >=
																								np_f_tot_pts[1]):
																							front_data.append(round(
																								np_f_tot_point.distance(
																									x_prop_work_line),
																								2))

																					elif (round(prop_poly1.distance(
																							organized_space_poly)) == 0):

																						front_data.append(round(
																							organized_space_poly.distance(
																								f_margin_linex_x), 2))
														# This loop for front line to prop_work block

														for fprop_work_poly in proposed_polygon:

															fprop_poly_pts = [a[0:2] for a in
																			  fprop_work_poly.get_points()]

															np_fprop_poly_pts = np.array(fprop_poly_pts).round(2)

															fprop_poly = Polygon(np_fprop_poly_pts)

															for f_prop_pts in np_fprop_poly_pts:

																np_f_prop_pts = np.array(f_prop_pts).round(2)

																np_f_prop_point = Point(np_f_prop_pts)

																if round(prop_poly1.distance(fprop_poly)) != 0:

																	if (min_np_x_prop_line[0] <= np_f_prop_pts[0] and
																		max_np_x_prop_line[0] >= np_f_prop_pts[0]) or (
																			min_np_x_prop_line[1] <= np_f_prop_pts[
																		1] and max_np_x_prop_line[1] >= np_f_prop_pts[
																				1]):

																		front_data.append(round(
																			np_f_prop_point.distance(x_prop_work_line),
																			2))

																	else:

																		for f_prop_line in fprop_work_poly.virtual_entities():

																			if f_prop_line.dxftype()=='LINE':

																				f_start_prop_pts = [
																					f_prop_line.dxf.start[0],
																					f_prop_line.dxf.start[1]]

																				f_end_prop_pts = [f_prop_line.dxf.end[0],
																								  f_prop_line.dxf.end[1]]

																				f_prop_line = [f_start_prop_pts,
																							   f_end_prop_pts]

																				np_f_prop_line = np.array(
																					f_prop_line).round(2)

																				f_prop_linea = LineString(np_f_prop_line)

																				max_np_f_prop_line = np_f_prop_line.max(
																					axis=0).round(2)

																				min_np_f_prop_line = np_f_prop_line.min(
																					axis=0).round(2)

																				for f_prop_line_pts in np_prop_linex_x:

																					np_f_prop_line_pts = np.array(
																						f_prop_line_pts).round(2)

																					f_prop_line_point = Point(
																						np_f_prop_line_pts)

																					if (min_np_f_prop_line[0] <=
																						np_f_prop_line_pts[0] and
																						max_np_f_prop_line[0] >=
																						np_f_prop_line_pts[0]) or (
																							min_np_f_prop_line[1] <=
																							np_f_prop_line_pts[1] and
																							max_np_f_prop_line[1] >=
																							np_f_prop_line_pts[1]):
																						front_data.append(round(
																							f_prop_line_point.distance(
																								f_prop_linea), 2))
																			elif f_prop_line.dxftype() == 'ARC':

																				f_start_prop_pts = [
																					f_prop_line.start_point[0],
																					f_prop_line.start_point[1]]

																				f_end_prop_pts = [
																					f_prop_line.end_point[0],
																					f_prop_line.end_point[1]]

																				f_prop_line = [f_start_prop_pts,
																							   f_end_prop_pts]

																				np_f_prop_line = np.array(
																					f_prop_line).round(2)

																				f_prop_linea = LineString(
																					np_f_prop_line)

																				max_np_f_prop_line = np_f_prop_line.max(
																					axis=0).round(2)

																				min_np_f_prop_line = np_f_prop_line.min(
																					axis=0).round(2)

																				for f_prop_line_pts in np_prop_linex_x:

																					np_f_prop_line_pts = np.array(
																						f_prop_line_pts).round(2)

																					f_prop_line_point = Point(
																						np_f_prop_line_pts)

																					if (min_np_f_prop_line[0] <=
																						np_f_prop_line_pts[0] and
																						max_np_f_prop_line[0] >=
																						np_f_prop_line_pts[0]) or (
																							min_np_f_prop_line[1] <=
																							np_f_prop_line_pts[1] and
																							max_np_f_prop_line[1] >=
																							np_f_prop_line_pts[1]):
																						front_data.append(round(
																							f_prop_line_point.distance(
																								f_prop_linea), 2))
									# Does not equal x and y value

									else:

										#proposed work polygon

										for fprop_work_poly in proposed_polygon:

											fprop_poly_pts=[b[0:2] for b in fprop_work_poly.get_points()]

											np_fprop_poly_pts=np.array(fprop_poly_pts).round(2)

											fprop_poly=Polygon(np_fprop_poly_pts)

											for f_prop_pts in fprop_poly_pts:

												np_f_prop_pts=np.array(f_prop_pts).round(2)

												f_prop_point=Point(np_f_prop_pts)

												if round(prop_poly1.distance(fprop_poly))!=0:

													if (max_prop_linex_x[0]>=np_f_prop_pts[0] and min_prop_linex_x[0]<=np_f_prop_pts[0]) or (max_prop_linex_x[1]>=np_f_prop_pts[1] and min_prop_linex_x[1]<=np_f_prop_pts[1]):

														front_data.append(round(f_prop_point.distance(f_prop_linex_x),2))

													else:

														for f_lwpolygon in proposed_polygon:

															f_lwpolygon_pts=[p[0:2] for p in f_lwpolygon.get_points()]

															np_f_lwpolygon_pts=np.array(f_lwpolygon_pts).round(2)

															f_lwpolygon_poly=Polygon(np_f_lwpolygon_pts)

															for f_prop_line in f_lwpolygon.virtual_entities():

																if f_prop_line.dxftype()=='LINE':

																	f_prop_start_pts=[f_prop_line.dxf.start[0],f_prop_line.dxf.start[1]]

																	f_prop_end_pts=[f_prop_line.dxf.end[0],f_prop_line.dxf.end[1]]

																	f_prop_line_pts=[f_prop_start_pts,f_prop_end_pts]

																	np_f_prop_line_point=np.array(f_prop_line_pts).round(2)

																	f_prop_line_point=LineString(np_f_prop_line_point)

																	max_np_f_prop_line_point=np_f_prop_line_point.max(axis=0)

																	min_np_f_prop_line_point=np_f_prop_line_point.min(axis=0)

																	if round(f_lwpolygon_poly.distance(prop_poly1),1)!=0:

																		if (max_np_f_prop_line_point[0]>=np_x_fline_pts[0] and min_np_f_prop_line_point[0]<=np_x_fline_pts[0]) or (max_np_f_prop_line_point[1]>=np_x_fline_pts[1] and min_np_f_prop_line_point[1]<=np_x_fline_pts[1]):

																			front_data.append(round(x_fline_point.distance(f_prop_line_point),2))

																		else:

																			for x_f_lwpolygon_pts in np_f_lwpolygon_pts:

																				np_x_f_lwpolygon_pts=np.array(x_f_lwpolygon_pts).round(2)

																				x_f_lwpolygon_pts=Point(x_f_lwpolygon_pts)

																				if (max_prop_linex_x[0]>=np_x_f_lwpolygon_pts[0] and min_prop_linex_x[0]<=np_x_f_lwpolygon_pts[0]) or (max_prop_linex_x[1]>=np_x_f_lwpolygon_pts[1] and min_prop_linex_x[1]<=np_x_f_lwpolygon_pts[1]):

																					front_data.append(round(x_f_lwpolygon_pts.distance(f_prop_linex_x),2))

																elif f_prop_line.dxftype() == 'ARC':

																	f_prop_start_pts = [f_prop_line.start_point[0],
																						f_prop_line.start_point[1]]

																	f_prop_end_pts = [f_prop_line.end_point[0],
																					  f_prop_line.end_point[1]]

																	f_prop_line_pts = [f_prop_start_pts, f_prop_end_pts]

																	np_f_prop_line_point = np.array(
																		f_prop_line_pts).round(2)

																	f_prop_line_point = LineString(np_f_prop_line_point)

																	max_np_f_prop_line_point = np_f_prop_line_point.max(
																		axis=0)

																	min_np_f_prop_line_point = np_f_prop_line_point.min(
																		axis=0)

																	if round(f_lwpolygon_poly.distance(prop_poly1),
																			 1) != 0:

																		if (max_np_f_prop_line_point[0] >=
																			np_x_fline_pts[0] and
																			min_np_f_prop_line_point[0] <=
																			np_x_fline_pts[0]) or (
																				max_np_f_prop_line_point[1] >=
																				np_x_fline_pts[1] and
																				min_np_f_prop_line_point[1] <=
																				np_x_fline_pts[1]):

																			front_data.append(round(
																				x_fline_point.distance(
																					f_prop_line_point), 2))

																		else:

																			for x_f_lwpolygon_pts in np_f_lwpolygon_pts:

																				np_x_f_lwpolygon_pts = np.array(
																					x_f_lwpolygon_pts).round(2)

																				x_f_lwpolygon_pts = Point(
																					x_f_lwpolygon_pts)

																				if (max_prop_linex_x[0] >=
																					np_x_f_lwpolygon_pts[0] and
																					min_prop_linex_x[0] <=
																					np_x_f_lwpolygon_pts[0]) or (
																						max_prop_linex_x[1] >=
																						np_x_f_lwpolygon_pts[1] and
																						min_prop_linex_x[1] <=
																						np_x_f_lwpolygon_pts[1]):
																					front_data.append(round(
																						x_f_lwpolygon_pts.distance(
																							f_prop_linex_x), 2))
					rline_pts_value=[]

					rline_pts=[]

					for rdata in rear_coordinate_data:

						r_prop_linex=LineString(rdata[0])

						r_margin_linex=LineString(rdata[1])

						if round(r_prop_linex.distance(r_margin_linex),1)==min(rear_data):

							r_np_prop_linex=np.array(rdata[0]).round(2)

							prop_line_splitr=split(r_np_prop_linex[0],r_np_prop_linex[1],4)

							for prop_splitr_pts in prop_line_splitr[1:-1]:

								np_prop_splitr_pts=np.array(prop_splitr_pts).round(2)

								prop_splitr_point=Point(np_prop_splitr_pts)

								rline_pts_value.append(round(prop_splitr_point.distance(r_margin_linex),1))

								rline_pts.append(np_prop_splitr_pts)

					for rdata_x in rear_coordinate_data:

						r_prop_linex_y=LineString(rdata_x[0])

						r_margin_linex_y=LineString(rdata_x[1])

						if round(r_prop_linex_y.distance(r_margin_linex_y),1)==min(rear_data):

							np_prop_linex_y=np.array(rdata_x[0]).round(2)

							max_prop_linex_y=np_prop_linex_y.max(axis=0).round(2)

							min_prop_linex_y=np_prop_linex_y.min(axis=0).round(2)

							for y_rline_pts in rline_pts:

								np_y_rline_pts=np.array(y_rline_pts).round(2)

								y_rline_point=Point(np_y_rline_pts)

								if ((max_prop_linex_y[0]>=np_y_rline_pts[0] and min_prop_linex_y[0]<=np_y_rline_pts[0]) and (max_prop_linex_y[1]>=np_y_rline_pts[1] and min_prop_linex_y[1]<=np_y_rline_pts[1])):

									# check match value

									if round(y_rline_point.distance(r_margin_linex_y),1)==min(rline_pts_value):

										# used for y axis equal

										if np_prop_linex_y[0,1]==np_prop_linex_y[1,1]:

											for y_r_prop_line in lwpolyline.virtual_entities():

												if y_r_prop_line.dxftype()=='LINE':

													y_r_prop_start_pts=[y_r_prop_line.dxf.start[0],y_r_prop_line.dxf.start[1]]

													y_r_prop_end_pts=[y_r_prop_line.dxf.end[0],y_r_prop_line.dxf.end[1]]

													y_prop_line=[y_r_prop_start_pts,y_r_prop_end_pts]

													np_y_prop_line=np.array(y_prop_line).round(2)

													if np_y_prop_line[0,1]==np_prop_linex_y[0,1] and np_y_prop_line[1,1]==np_prop_linex_y[1,1]:

														y_prop_work_line=LineString(np_y_prop_line)

														min_np_y_prop_line=np_y_prop_line.min(axis=0)

														max_np_y_prop_line=np_y_prop_line.max(axis=0)

														for organized_open_space_text in org_mtext:

															org_open_space = organized_open_space_text.dxf.text if organized_open_space_text.dxftype() == 'TEXT' else organized_open_space_text.plain_text()

															if org_open_space=='Tot-lot' or org_open_space=='Tot lot':

																organized_attrib=organized_open_space_text.dxfattribs()

																tot_lot_pts=organized_attrib['insert']

																np_tot_lot_pts=np.array([tot_lot_pts[0],tot_lot_pts[1]]).round(2)

																tot_lot_coords=Point(np_tot_lot_pts)

																for organized_open_space_poly in org_polygon:

																	organized_open_space_poly_pts=[y[0:2] for y in organized_open_space_poly.get_points()]

																	np_organized_open_space_poly_pts=np.array(organized_open_space_poly_pts).round(2)

																	organized_space_poly=Polygon(np_organized_open_space_poly_pts)

																	for r_tot_lot_line in organized_open_space_poly.virtual_entities():

																		if r_tot_lot_line.dxftype()=='LINE':

																			start_r_tot_lot_line_pts=[r_tot_lot_line.dxf.start[0],r_tot_lot_line.dxf.start[1]]

																			end_r_tot_lot_line_pts=[r_tot_lot_line.dxf.end[0],r_tot_lot_line.dxf.end[1]]

																			np_r_tot_lot_line_pts=np.array([start_r_tot_lot_line_pts,end_r_tot_lot_line_pts]).round(2)

																			split_np_r_tot_lot_line_pts=split(np_r_tot_lot_line_pts[0],np_r_tot_lot_line_pts[1],4)

																			if organized_space_poly.contains(tot_lot_coords)==True:

																				for r_tot_pts in split_np_r_tot_lot_line_pts:

																					np_r_tot_pts=np.array(r_tot_pts).round(2)

																					np_r_tot_point=Point(np_r_tot_pts)

																					if round(prop_poly1.distance(organized_space_poly))!=0:

																						if (min_np_y_prop_line[0]<=np_r_tot_pts[0] and  max_np_y_prop_line[0]>=np_r_tot_pts[0]) or (min_np_y_prop_line[1]<=np_r_tot_pts[1] and  max_np_y_prop_line[1]>=np_r_tot_pts[1]):

																							rear_data.append(round(np_r_tot_point.distance(y_prop_work_line),2))

																						else:

																							#tot lot polygon convert lines

																							for r_tot_line in organized_open_space_poly.virtual_entities():

																								if r_tot_line.dxftype()=='LINE':

																									r_tot_start_pts=[r_tot_line.dxf.start[0],r_tot_line.dxf.start[1]]

																									r_tot_end_pts=[r_tot_line.dxf.end[0],r_tot_line.dxf.end[1]]

																									r_tot_line_pts=[r_tot_start_pts,r_tot_end_pts]

																									np_r_tot_line_pts=np.array(r_tot_line_pts).round(2)

																									max_np_r_tot_line_pts=np_r_tot_line_pts.max(axis=0)

																									min_np_r_tot_line_pts=np_r_tot_line_pts.min(axis=0)

																									r_tot_line_point=LineString(np_r_tot_line_pts)

																									# proposed work line convert into points

																									for r_prop_work_pts in np_y_prop_line:

																										np_r_prop_work_pts=np.array(r_prop_work_pts).round(2)

																										r_prop_work_point=Point(np_r_prop_work_pts)

																										#check condition tot_lot line incluide proposed work points or not

																										if (max_np_r_tot_line_pts[0]>=np_r_prop_work_pts[0] and min_np_r_tot_line_pts[0]<=np_r_prop_work_pts[0]) or (max_np_r_tot_line_pts[1]>=np_r_prop_work_pts[1] and min_np_r_tot_line_pts[1]<=np_r_prop_work_pts[1]):

																											rear_data.append(round(r_prop_work_point.distance(r_tot_line_point),2))
																								elif r_tot_line.dxftype() == 'ARC':

																									r_tot_start_pts = [
																										r_tot_line.start_point[
																											0],
																										r_tot_line.start_point[
																											1]]

																									r_tot_end_pts = [
																										r_tot_line.end_point[
																											0],
																										r_tot_line.end_point[
																											1]]

																									r_tot_line_pts = [
																										r_tot_start_pts,
																										r_tot_end_pts]

																									np_r_tot_line_pts = np.array(
																										r_tot_line_pts).round(
																										2)

																									max_np_r_tot_line_pts = np_r_tot_line_pts.max(
																										axis=0)

																									min_np_r_tot_line_pts = np_r_tot_line_pts.min(
																										axis=0)

																									r_tot_line_point = LineString(
																										np_r_tot_line_pts)

																									# proposed work line convert into points

																									for r_prop_work_pts in np_y_prop_line:

																										np_r_prop_work_pts = np.array(
																											r_prop_work_pts).round(
																											2)

																										r_prop_work_point = Point(
																											np_r_prop_work_pts)

																										# check condition tot_lot line incluide proposed work points or not

																										if (
																												max_np_r_tot_line_pts[
																													0] >=
																												np_r_prop_work_pts[
																													0] and
																												min_np_r_tot_line_pts[
																													0] <=
																												np_r_prop_work_pts[
																													0]) or (
																												max_np_r_tot_line_pts[
																													1] >=
																												np_r_prop_work_pts[
																													1] and
																												min_np_r_tot_line_pts[
																													1] <=
																												np_r_prop_work_pts[
																													1]):
																											rear_data.append(
																												round(
																													r_prop_work_point.distance(
																														r_tot_line_point),
																													2))
																					elif(round(prop_poly1.distance(organized_space_poly))==0):

																						rear_data.append(round(organized_space_poly.distance(r_margin_linex_y),2))
																		elif r_tot_lot_line.dxftype() == 'ARC':

																			start_r_tot_lot_line_pts = [
																				r_tot_lot_line.start_point[0],
																				r_tot_lot_line.start_point[1]]

																			end_r_tot_lot_line_pts = [
																				r_tot_lot_line.end_point[0],
																				r_tot_lot_line.end_point[1]]

																			np_r_tot_lot_line_pts = np.array(
																				[start_r_tot_lot_line_pts,
																				 end_r_tot_lot_line_pts]).round(2)

																			split_np_r_tot_lot_line_pts = split(
																				np_r_tot_lot_line_pts[0],
																				np_r_tot_lot_line_pts[1], 4)

																			if organized_space_poly.contains(
																					tot_lot_coords) == True:

																				for r_tot_pts in split_np_r_tot_lot_line_pts:

																					np_r_tot_pts = np.array(
																						r_tot_pts).round(2)

																					np_r_tot_point = Point(np_r_tot_pts)

																					if round(prop_poly1.distance(
																							organized_space_poly)) != 0:

																						if (min_np_y_prop_line[0] <=
																							np_r_tot_pts[0] and
																							max_np_y_prop_line[0] >=
																							np_r_tot_pts[0]) or (
																								min_np_y_prop_line[1] <=
																								np_r_tot_pts[1] and
																								max_np_y_prop_line[1] >=
																								np_r_tot_pts[1]):

																							rear_data.append(round(
																								np_r_tot_point.distance(
																									y_prop_work_line),
																								2))

																						else:

																							# tot lot polygon convert lines

																							for r_tot_line in organized_open_space_poly.virtual_entities():

																								if r_tot_line.dxftype() == 'LINE':

																									r_tot_start_pts = [
																										r_tot_line.dxf.start[
																											0],
																										r_tot_line.dxf.start[
																											1]]

																									r_tot_end_pts = [
																										r_tot_line.dxf.end[
																											0],
																										r_tot_line.dxf.end[
																											1]]

																									r_tot_line_pts = [
																										r_tot_start_pts,
																										r_tot_end_pts]

																									np_r_tot_line_pts = np.array(
																										r_tot_line_pts).round(
																										2)

																									max_np_r_tot_line_pts = np_r_tot_line_pts.max(
																										axis=0)

																									min_np_r_tot_line_pts = np_r_tot_line_pts.min(
																										axis=0)

																									r_tot_line_point = LineString(
																										np_r_tot_line_pts)

																									# proposed work line convert into points

																									for r_prop_work_pts in np_y_prop_line:

																										np_r_prop_work_pts = np.array(
																											r_prop_work_pts).round(
																											2)

																										r_prop_work_point = Point(
																											np_r_prop_work_pts)

																										# check condition tot_lot line incluide proposed work points or not

																										if (
																												max_np_r_tot_line_pts[
																													0] >=
																												np_r_prop_work_pts[
																													0] and
																												min_np_r_tot_line_pts[
																													0] <=
																												np_r_prop_work_pts[
																													0]) or (
																												max_np_r_tot_line_pts[
																													1] >=
																												np_r_prop_work_pts[
																													1] and
																												min_np_r_tot_line_pts[
																													1] <=
																												np_r_prop_work_pts[
																													1]):
																											rear_data.append(
																												round(
																													r_prop_work_point.distance(
																														r_tot_line_point),
																													2))
																								elif r_tot_line.dxftype() == 'ARC':

																									r_tot_start_pts = [
																										r_tot_line.start_point[
																											0],
																										r_tot_line.start_point[
																											1]]

																									r_tot_end_pts = [
																										r_tot_line.end_point[
																											0],
																										r_tot_line.end_point[
																											1]]

																									r_tot_line_pts = [
																										r_tot_start_pts,
																										r_tot_end_pts]

																									np_r_tot_line_pts = np.array(
																										r_tot_line_pts).round(
																										2)

																									max_np_r_tot_line_pts = np_r_tot_line_pts.max(
																										axis=0)

																									min_np_r_tot_line_pts = np_r_tot_line_pts.min(
																										axis=0)

																									r_tot_line_point = LineString(
																										np_r_tot_line_pts)

																									# proposed work line convert into points

																									for r_prop_work_pts in np_y_prop_line:

																										np_r_prop_work_pts = np.array(
																											r_prop_work_pts).round(
																											2)

																										r_prop_work_point = Point(
																											np_r_prop_work_pts)

																										# check condition tot_lot line incluide proposed work points or not

																										if (
																												max_np_r_tot_line_pts[
																													0] >=
																												np_r_prop_work_pts[
																													0] and
																												min_np_r_tot_line_pts[
																													0] <=
																												np_r_prop_work_pts[
																													0]) or (
																												max_np_r_tot_line_pts[
																													1] >=
																												np_r_prop_work_pts[
																													1] and
																												min_np_r_tot_line_pts[
																													1] <=
																												np_r_prop_work_pts[
																													1]):
																											rear_data.append(
																												round(
																													r_prop_work_point.distance(
																														r_tot_line_point),
																													2))
																					elif (round(prop_poly1.distance(
																							organized_space_poly)) == 0):

																						rear_data.append(round(
																							organized_space_poly.distance(
																								r_margin_linex_y), 2))

														#This loop for rear line to prop_work block

														for rprop_work_poly in proposed_polygon:

															rprop_poly_pts=[b[0:2] for b in rprop_work_poly.get_points()]

															np_rprop_poly_pts=np.array(rprop_poly_pts).round(2)

															rprop_poly=Polygon(np_rprop_poly_pts)

															for rprop_work_poly_line in rprop_work_poly.virtual_entities():

																if rprop_work_poly_line.dxftype()=='LINE':

																	start_rprop_work_poly_line_pts=[rprop_work_poly_line.dxf.start[0],rprop_work_poly_line.dxf.start[1]]

																	end_rprop_work_poly_line_pts=[rprop_work_poly_line.dxf.end[0],rprop_work_poly_line.dxf.end[1]]

																	np_rprop_work_poly_line=np.array([start_rprop_work_poly_line_pts,end_rprop_work_poly_line_pts]).round(2)

																	split_np_rprop_work_poly_line=split(np_rprop_work_poly_line[0],np_rprop_work_poly_line[1],4)

																	for r_prop_pts in split_np_rprop_work_poly_line:

																		np_r_prop_pts=np.array(r_prop_pts).round(2)

																		np_r_prop_point=Point(np_r_prop_pts)

																		if round(prop_poly1.distance(rprop_poly))!=0:

																			if (min_np_y_prop_line[0]<=np_r_prop_pts[0] and  max_np_y_prop_line[0]>=np_r_prop_pts[0]) or (min_np_y_prop_line[1]<=np_r_prop_pts[1] and  max_np_y_prop_line[1]>=np_r_prop_pts[1]):

																				rear_data.append(round(np_r_prop_point.distance(y_prop_work_line),2))

																elif rprop_work_poly_line.dxftype() == 'ARC':

																	start_rprop_work_poly_line_pts = [
																		rprop_work_poly_line.start_point[0],
																		rprop_work_poly_line.start_point[1]]

																	end_rprop_work_poly_line_pts = [
																		rprop_work_poly_line.end_point[0],
																		rprop_work_poly_line.end_point[1]]

																	np_rprop_work_poly_line = np.array(
																		[start_rprop_work_poly_line_pts,
																		 end_rprop_work_poly_line_pts]).round(2)

																	split_np_rprop_work_poly_line = split(
																		np_rprop_work_poly_line[0],
																		np_rprop_work_poly_line[1], 4)

																	for r_prop_pts in split_np_rprop_work_poly_line:

																		np_r_prop_pts = np.array(r_prop_pts).round(2)

																		np_r_prop_point = Point(np_r_prop_pts)

																		if round(prop_poly1.distance(rprop_poly)) != 0:

																			if (min_np_y_prop_line[0] <= np_r_prop_pts[
																				0] and max_np_y_prop_line[0] >=
																				np_r_prop_pts[0]) or (
																					min_np_y_prop_line[1] <=
																					np_r_prop_pts[1] and
																					max_np_y_prop_line[1] >=
																					np_r_prop_pts[1]):
																				rear_data.append(round(
																					np_r_prop_point.distance(
																						y_prop_work_line), 2))

												elif y_r_prop_line.dxftype() == 'ARC':

													y_r_prop_start_pts = [y_r_prop_line.start_point[0],
																		  y_r_prop_line.start_point[1]]

													y_r_prop_end_pts = [y_r_prop_line.end_point[0],
																		y_r_prop_line.end_point[1]]

													y_prop_line = [y_r_prop_start_pts, y_r_prop_end_pts]

													np_y_prop_line = np.array(y_prop_line).round(2)

													if np_y_prop_line[0, 1] == np_prop_linex_y[0, 1] and np_y_prop_line[
														1, 1] == np_prop_linex_y[1, 1]:

														y_prop_work_line = LineString(np_y_prop_line)

														min_np_y_prop_line = np_y_prop_line.min(axis=0)

														max_np_y_prop_line = np_y_prop_line.max(axis=0)

														for organized_open_space_text in org_mtext:

															org_open_space = organized_open_space_text.dxf.text if organized_open_space_text.dxftype() == 'TEXT' else organized_open_space_text.plain_text()

															if org_open_space=='Tot-lot' or org_open_space=='Tot lot':

																organized_attrib = organized_open_space_text.dxfattribs()

																tot_lot_pts = organized_attrib['insert']

																np_tot_lot_pts = np.array(
																	[tot_lot_pts[0], tot_lot_pts[1]]).round(2)

																tot_lot_coords = Point(np_tot_lot_pts)

																for organized_open_space_poly in org_polygon:

																	organized_open_space_poly_pts = [y[0:2] for y in
																									 organized_open_space_poly.get_points()]

																	np_organized_open_space_poly_pts = np.array(
																		organized_open_space_poly_pts).round(2)

																	organized_space_poly = Polygon(
																		np_organized_open_space_poly_pts)

																	for r_tot_lot_line in organized_open_space_poly.virtual_entities():

																		if r_tot_lot_line.dxftype()=='LINE':

																			start_r_tot_lot_line_pts = [
																				r_tot_lot_line.dxf.start[0],
																				r_tot_lot_line.dxf.start[1]]

																			end_r_tot_lot_line_pts = [
																				r_tot_lot_line.dxf.end[0],
																				r_tot_lot_line.dxf.end[1]]

																			np_r_tot_lot_line_pts = np.array(
																				[start_r_tot_lot_line_pts,
																				 end_r_tot_lot_line_pts]).round(2)

																			split_np_r_tot_lot_line_pts = split(
																				np_r_tot_lot_line_pts[0],
																				np_r_tot_lot_line_pts[1], 4)

																			if organized_space_poly.contains(
																					tot_lot_coords) == True:

																				for r_tot_pts in split_np_r_tot_lot_line_pts:

																					np_r_tot_pts = np.array(
																						r_tot_pts).round(2)

																					np_r_tot_point = Point(np_r_tot_pts)

																					if round(prop_poly1.distance(
																							organized_space_poly)) != 0:

																						if (min_np_y_prop_line[0] <=
																							np_r_tot_pts[0] and
																							max_np_y_prop_line[0] >=
																							np_r_tot_pts[0]) or (
																								min_np_y_prop_line[1] <=
																								np_r_tot_pts[1] and
																								max_np_y_prop_line[1] >=
																								np_r_tot_pts[1]):

																							rear_data.append(round(
																								np_r_tot_point.distance(
																									y_prop_work_line), 2))

																						else:

																							# tot lot polygon convert lines

																							for r_tot_line in organized_open_space_poly.virtual_entities():

																								if r_tot_line.dxftype()=='LINE':
																									r_tot_start_pts = [
																										r_tot_line.dxf.start[0],
																										r_tot_line.dxf.start[1]]

																									r_tot_end_pts = [
																										r_tot_line.dxf.end[0],
																										r_tot_line.dxf.end[1]]

																									r_tot_line_pts = [
																										r_tot_start_pts,
																										r_tot_end_pts]

																									np_r_tot_line_pts = np.array(
																										r_tot_line_pts).round(2)

																									max_np_r_tot_line_pts = np_r_tot_line_pts.max(
																										axis=0)

																									min_np_r_tot_line_pts = np_r_tot_line_pts.min(
																										axis=0)

																									r_tot_line_point = LineString(
																										np_r_tot_line_pts)

																									# proposed work line convert into points

																									for r_prop_work_pts in np_y_prop_line:

																										np_r_prop_work_pts = np.array(
																											r_prop_work_pts).round(
																											2)

																										r_prop_work_point = Point(
																											np_r_prop_work_pts)

																										# check condition tot_lot line incluide proposed work points or not

																										if (
																												max_np_r_tot_line_pts[
																													0] >=
																												np_r_prop_work_pts[
																													0] and
																												min_np_r_tot_line_pts[
																													0] <=
																												np_r_prop_work_pts[
																													0]) or (
																												max_np_r_tot_line_pts[
																													1] >=
																												np_r_prop_work_pts[
																													1] and
																												min_np_r_tot_line_pts[
																													1] <=
																												np_r_prop_work_pts[
																													1]):
																											rear_data.append(
																												round(
																													r_prop_work_point.distance(
																														r_tot_line_point),
																													2))
																								elif r_tot_line.dxftype()=='ARC':
																									r_tot_start_pts = [
																										r_tot_line.start_point[0],
																										r_tot_line.start_point[1]]

																									r_tot_end_pts = [
																										r_tot_line.end_point[0],
																										r_tot_line.end_point[1]]

																									r_tot_line_pts = [
																										r_tot_start_pts,
																										r_tot_end_pts]

																									np_r_tot_line_pts = np.array(
																										r_tot_line_pts).round(2)

																									max_np_r_tot_line_pts = np_r_tot_line_pts.max(
																										axis=0)

																									min_np_r_tot_line_pts = np_r_tot_line_pts.min(
																										axis=0)

																									r_tot_line_point = LineString(
																										np_r_tot_line_pts)

																									# proposed work line convert into points

																									for r_prop_work_pts in np_y_prop_line:

																										np_r_prop_work_pts = np.array(
																											r_prop_work_pts).round(
																											2)

																										r_prop_work_point = Point(
																											np_r_prop_work_pts)

																										# check condition tot_lot line incluide proposed work points or not

																										if (
																												max_np_r_tot_line_pts[
																													0] >=
																												np_r_prop_work_pts[
																													0] and
																												min_np_r_tot_line_pts[
																													0] <=
																												np_r_prop_work_pts[
																													0]) or (
																												max_np_r_tot_line_pts[
																													1] >=
																												np_r_prop_work_pts[
																													1] and
																												min_np_r_tot_line_pts[
																													1] <=
																												np_r_prop_work_pts[
																													1]):
																											rear_data.append(
																												round(
																													r_prop_work_point.distance(
																														r_tot_line_point),
																													2))
																					elif (round(prop_poly1.distance(
																							organized_space_poly)) == 0):

																						rear_data.append(round(
																							organized_space_poly.distance(
																								r_margin_linex_y), 2))

																		elif r_tot_lot_line.dxftype() == 'ARC':

																			start_r_tot_lot_line_pts = [
																				r_tot_lot_line.start_point[0],
																				r_tot_lot_line.start_point[1]]

																			end_r_tot_lot_line_pts = [
																				r_tot_lot_line.end_point[0],
																				r_tot_lot_line.end_point[1]]

																			np_r_tot_lot_line_pts = np.array(
																				[start_r_tot_lot_line_pts,
																				 end_r_tot_lot_line_pts]).round(2)

																			split_np_r_tot_lot_line_pts = split(
																				np_r_tot_lot_line_pts[0],
																				np_r_tot_lot_line_pts[1], 4)

																			if organized_space_poly.contains(
																					tot_lot_coords) == True:

																				for r_tot_pts in split_np_r_tot_lot_line_pts:

																					np_r_tot_pts = np.array(
																						r_tot_pts).round(2)

																					np_r_tot_point = Point(np_r_tot_pts)

																					if round(prop_poly1.distance(
																							organized_space_poly)) != 0:

																						if (min_np_y_prop_line[0] <=
																							np_r_tot_pts[0] and
																							max_np_y_prop_line[0] >=
																							np_r_tot_pts[0]) or (
																								min_np_y_prop_line[1] <=
																								np_r_tot_pts[1] and
																								max_np_y_prop_line[1] >=
																								np_r_tot_pts[1]):

																							rear_data.append(round(
																								np_r_tot_point.distance(
																									y_prop_work_line),
																								2))

																						else:

																							# tot lot polygon convert lines

																							for r_tot_line in organized_open_space_poly.virtual_entities():

																								if r_tot_line.dxftype()=='LINE':

																									r_tot_start_pts = [
																										r_tot_line.dxf.start[
																											0],
																										r_tot_line.dxf.start[
																											1]]

																									r_tot_end_pts = [
																										r_tot_line.dxf.end[
																											0],
																										r_tot_line.dxf.end[
																											1]]

																									r_tot_line_pts = [
																										r_tot_start_pts,
																										r_tot_end_pts]

																									np_r_tot_line_pts = np.array(
																										r_tot_line_pts).round(
																										2)

																									max_np_r_tot_line_pts = np_r_tot_line_pts.max(
																										axis=0)

																									min_np_r_tot_line_pts = np_r_tot_line_pts.min(
																										axis=0)

																									r_tot_line_point = LineString(
																										np_r_tot_line_pts)

																									# proposed work line convert into points

																									for r_prop_work_pts in np_y_prop_line:

																										np_r_prop_work_pts = np.array(
																											r_prop_work_pts).round(
																											2)

																										r_prop_work_point = Point(
																											np_r_prop_work_pts)

																										# check condition tot_lot line incluide proposed work points or not

																										if (
																												max_np_r_tot_line_pts[
																													0] >=
																												np_r_prop_work_pts[
																													0] and
																												min_np_r_tot_line_pts[
																													0] <=
																												np_r_prop_work_pts[
																													0]) or (
																												max_np_r_tot_line_pts[
																													1] >=
																												np_r_prop_work_pts[
																													1] and
																												min_np_r_tot_line_pts[
																													1] <=
																												np_r_prop_work_pts[
																													1]):
																											rear_data.append(
																												round(
																													r_prop_work_point.distance(
																														r_tot_line_point),
																													2))
																								elif r_tot_line.dxftype() == 'ARC':

																									r_tot_start_pts = [
																										r_tot_line.start_point[
																											0],
																										r_tot_line.start_point[
																											1]]

																									r_tot_end_pts = [
																										r_tot_line.end_point[
																											0],
																										r_tot_line.end_point[
																											1]]

																									r_tot_line_pts = [
																										r_tot_start_pts,
																										r_tot_end_pts]

																									np_r_tot_line_pts = np.array(
																										r_tot_line_pts).round(
																										2)

																									max_np_r_tot_line_pts = np_r_tot_line_pts.max(
																										axis=0)

																									min_np_r_tot_line_pts = np_r_tot_line_pts.min(
																										axis=0)

																									r_tot_line_point = LineString(
																										np_r_tot_line_pts)

																									# proposed work line convert into points

																									for r_prop_work_pts in np_y_prop_line:

																										np_r_prop_work_pts = np.array(
																											r_prop_work_pts).round(
																											2)

																										r_prop_work_point = Point(
																											np_r_prop_work_pts)

																										# check condition tot_lot line incluide proposed work points or not

																										if (
																												max_np_r_tot_line_pts[
																													0] >=
																												np_r_prop_work_pts[
																													0] and
																												min_np_r_tot_line_pts[
																													0] <=
																												np_r_prop_work_pts[
																													0]) or (
																												max_np_r_tot_line_pts[
																													1] >=
																												np_r_prop_work_pts[
																													1] and
																												min_np_r_tot_line_pts[
																													1] <=
																												np_r_prop_work_pts[
																													1]):
																											rear_data.append(
																												round(
																													r_prop_work_point.distance(
																														r_tot_line_point),
																													2))
																					elif (round(prop_poly1.distance(
																							organized_space_poly)) == 0):

																						rear_data.append(round(
																							organized_space_poly.distance(
																								r_margin_linex_y), 2))
														# This loop for rear line to prop_work block

														for rprop_work_poly in proposed_polygon:

															rprop_poly_pts = [b[0:2] for b in
																			  rprop_work_poly.get_points()]

															np_rprop_poly_pts = np.array(rprop_poly_pts).round(2)

															rprop_poly = Polygon(np_rprop_poly_pts)

															for rprop_work_poly_line in rprop_work_poly.virtual_entities():

																if rprop_work_poly_line.dxftype()=='LINE':

																	start_rprop_work_poly_line_pts = [
																		rprop_work_poly_line.dxf.start[0],
																		rprop_work_poly_line.dxf.start[1]]

																	end_rprop_work_poly_line_pts = [
																		rprop_work_poly_line.dxf.end[0],
																		rprop_work_poly_line.dxf.end[1]]

																	np_rprop_work_poly_line = np.array(
																		[start_rprop_work_poly_line_pts,
																		 end_rprop_work_poly_line_pts]).round(2)

																	split_np_rprop_work_poly_line = split(
																		np_rprop_work_poly_line[0],
																		np_rprop_work_poly_line[1], 4)

																	for r_prop_pts in split_np_rprop_work_poly_line:

																		np_r_prop_pts = np.array(r_prop_pts).round(2)

																		np_r_prop_point = Point(np_r_prop_pts)

																		if round(prop_poly1.distance(rprop_poly)) != 0:

																			if (min_np_y_prop_line[0] <= np_r_prop_pts[
																				0] and max_np_y_prop_line[0] >=
																				np_r_prop_pts[0]) or (
																					min_np_y_prop_line[1] <= np_r_prop_pts[
																				1] and max_np_y_prop_line[1] >=
																					np_r_prop_pts[1]):
																				rear_data.append(round(
																					np_r_prop_point.distance(
																						y_prop_work_line), 2))
																elif rprop_work_poly_line.dxftype() == 'ARC':

																	start_rprop_work_poly_line_pts = [
																		rprop_work_poly_line.start_point[0],
																		rprop_work_poly_line.start_point[1]]

																	end_rprop_work_poly_line_pts = [
																		rprop_work_poly_line.end_point[0],
																		rprop_work_poly_line.end_point[1]]

																	np_rprop_work_poly_line = np.array(
																		[start_rprop_work_poly_line_pts,
																		 end_rprop_work_poly_line_pts]).round(2)

																	split_np_rprop_work_poly_line = split(
																		np_rprop_work_poly_line[0],
																		np_rprop_work_poly_line[1], 4)

																	for r_prop_pts in split_np_rprop_work_poly_line:

																		np_r_prop_pts = np.array(r_prop_pts).round(2)

																		np_r_prop_point = Point(np_r_prop_pts)

																		if round(prop_poly1.distance(rprop_poly)) != 0:

																			if (min_np_y_prop_line[0] <= np_r_prop_pts[
																				0] and max_np_y_prop_line[0] >=
																				np_r_prop_pts[0]) or (
																					min_np_y_prop_line[1] <=
																					np_r_prop_pts[
																						1] and max_np_y_prop_line[1] >=
																					np_r_prop_pts[1]):
																				rear_data.append(round(
																					np_r_prop_point.distance(
																						y_prop_work_line), 2))
										#used for x axis equal data

										elif(np_prop_linex_y[0,0]==np_prop_linex_y[1,0]):

											for y_r_prop_line in lwpolyline.virtual_entities():

												if y_r_prop_line.dxftype()=='LINE':

													y_r_prop_start_pts=[y_r_prop_line.dxf.start[0],y_r_prop_line.dxf.start[1]]

													y_r_prop_end_pts=[y_r_prop_line.dxf.end[0],y_r_prop_line.dxf.end[1]]

													y_prop_line=[y_r_prop_start_pts,y_r_prop_end_pts]

													np_y_prop_line=np.array(y_prop_line).round(2)

													if np_y_prop_line[0,0]==np_prop_linex_y[0,0] and np_y_prop_line[1,0]==np_prop_linex_y[1,0]:

														y_prop_work_line=LineString(np_y_prop_line)

														min_np_y_prop_line=np_y_prop_line.min(axis=0)

														max_np_y_prop_line=np_y_prop_line.max(axis=0)

														for organized_open_space_text in org_mtext:

															org_open_space = organized_open_space_text.dxf.text if organized_open_space_text.dxftype() == 'TEXT' else organized_open_space_text.plain_text()

															if org_open_space=='Tot-lot' or org_open_space=='Tot lot':

																organized_attrib=organized_open_space_text.dxfattribs()

																tot_lot_pts=organized_attrib['insert']

																np_tot_lot_pts=np.array([tot_lot_pts[0],tot_lot_pts[1]]).round(2)

																tot_lot_coords=Point(np_tot_lot_pts)

																for organized_open_space_poly in org_polygon:

																	organized_open_space_poly_pts=[y[0:2] for y in organized_open_space_poly.get_points()]

																	np_organized_open_space_poly_pts=np.array(organized_open_space_poly_pts).round(2)

																	organized_space_poly=Polygon(np_organized_open_space_poly_pts)

																	if organized_space_poly.contains(tot_lot_coords)==True:

																		for r_tot_pts in np_organized_open_space_poly_pts:

																			np_r_tot_pts=np.array(r_tot_pts).round(2)

																			np_r_tot_point=Point(np_r_tot_pts)

																			if round(prop_poly1.distance(organized_space_poly))!=0:

																				if (min_np_y_prop_line[0]<=np_r_tot_pts[0] and  max_np_y_prop_line[0]>=np_r_tot_pts[0]) or (min_np_y_prop_line[1]<=np_r_tot_pts[1] and  max_np_y_prop_line[1]>=np_r_tot_pts[1]):

																					rear_data.append(round(np_r_tot_point.distance(y_prop_work_line),2))

																				else:

																					#tot lot polygon convert lines

																					for r_tot_line in organized_open_space_poly.virtual_entities():

																						if r_tot_line.dxftype()=='LINE':

																							r_tot_start_pts=[r_tot_line.dxf.start[0],r_tot_line.dxf.start[1]]

																							r_tot_end_pts=[r_tot_line.dxf.end[0],r_tot_line.dxf.end[1]]

																							r_tot_line_pts=[r_tot_start_pts,r_tot_end_pts]

																							np_r_tot_line_pts=np.array(r_tot_line_pts).round(2)

																							max_np_r_tot_line_pts=np_r_tot_line_pts.max(axis=0)

																							min_np_r_tot_line_pts=np_r_tot_line_pts.min(axis=0)

																							r_tot_line_point=LineString(np_r_tot_line_pts)

																							# proposed work line convert into points

																							for r_prop_work_pts in np_y_prop_line:

																								np_r_prop_work_pts=np.array(r_prop_work_pts).round(2)

																								r_prop_work_point=Point(np_r_prop_work_pts)

																								#check condition tot_lot line incluide proposed work points or not

																								if (max_np_r_tot_line_pts[0]>=np_r_prop_work_pts[0] and min_np_r_tot_line_pts[0]<=np_r_prop_work_pts[0]) or (max_np_r_tot_line_pts[1]>=np_r_prop_work_pts[1] and min_np_r_tot_line_pts[1]<=np_r_prop_work_pts[1]):

																									rear_data.append(round(r_prop_work_point.distance(r_tot_line_point),2))

																						elif r_tot_line.dxftype() == 'ARC':

																							r_tot_start_pts = [
																								r_tot_line.start_point[0],
																								r_tot_line.start_point[1]]

																							r_tot_end_pts = [
																								r_tot_line.end_point[0],
																								r_tot_line.end_point[1]]

																							r_tot_line_pts = [
																								r_tot_start_pts,
																								r_tot_end_pts]

																							np_r_tot_line_pts = np.array(
																								r_tot_line_pts).round(2)

																							max_np_r_tot_line_pts = np_r_tot_line_pts.max(
																								axis=0)

																							min_np_r_tot_line_pts = np_r_tot_line_pts.min(
																								axis=0)

																							r_tot_line_point = LineString(
																								np_r_tot_line_pts)

																							# proposed work line convert into points

																							for r_prop_work_pts in np_y_prop_line:

																								np_r_prop_work_pts = np.array(
																									r_prop_work_pts).round(
																									2)

																								r_prop_work_point = Point(
																									np_r_prop_work_pts)

																								# check condition tot_lot line incluide proposed work points or not

																								if (
																										max_np_r_tot_line_pts[
																											0] >=
																										np_r_prop_work_pts[
																											0] and
																										min_np_r_tot_line_pts[
																											0] <=
																										np_r_prop_work_pts[
																											0]) or (
																										max_np_r_tot_line_pts[
																											1] >=
																										np_r_prop_work_pts[
																											1] and
																										min_np_r_tot_line_pts[
																											1] <=
																										np_r_prop_work_pts[
																											1]):
																									rear_data.append(
																										round(
																											r_prop_work_point.distance(
																												r_tot_line_point),
																											2))
																			elif(round(prop_poly1.distance(organized_space_poly))==0):

																				rear_data.append(round(organized_space_poly.distance(r_margin_linex_y),2))

														#This loop for rear line to prop_work block

														for rprop_work_poly in proposed_polygon:

															rprop_poly_pts=[b[0:2] for b in rprop_work_poly.get_points()]

															np_rprop_poly_pts=np.array(rprop_poly_pts).round(2)

															rprop_poly=Polygon(np_rprop_poly_pts)

															for r_prop_pts in np_rprop_poly_pts:

																np_r_prop_pts=np.array(r_prop_pts).round(2)

																np_r_prop_point=Point(np_r_prop_pts)

																if round(prop_poly1.distance(rprop_poly))!=0:

																	if (min_np_y_prop_line[0]<=np_r_prop_pts[0] and  max_np_y_prop_line[0]>=np_r_prop_pts[0]) or (min_np_y_prop_line[1]<=np_r_prop_pts[1] and  max_np_y_prop_line[1]>=np_r_prop_pts[1]):

																		rear_data.append(round(np_r_prop_point.distance(y_prop_work_line),2))

																	else:

																		for r_prop_line in rprop_work_poly.virtual_entities():

																			r_start_prop_pts=[r_prop_line.dxf.start[0],r_prop_line.dxf.start[1]]

																			r_end_prop_pts=[r_prop_line.dxf.end[0],r_prop_line.dxf.end[1]]

																			r_prop_line=[r_start_prop_pts,r_end_prop_pts]

																			np_r_prop_line=np.array(r_prop_line).round(2)

																			r_prop_linea=LineString(np_r_prop_line)

																			max_np_r_prop_line=np_r_prop_line.max(axis=0).round(2)

																			min_np_r_prop_line=np_r_prop_line.min(axis=0).round(2)

																			for r_prop_line_pts in np_prop_linex_y:

																				np_r_prop_line_pts=np.array(r_prop_line_pts).round(2)

																				r_prop_line_point=Point(np_r_prop_line_pts)

																				if (min_np_r_prop_line[0]<=np_r_prop_line_pts[0] and  max_np_r_prop_line[0]>=np_r_prop_line_pts[0]) or (min_np_r_prop_line[1]<=np_r_prop_line_pts[1] and  max_np_r_prop_line[1]>=np_r_prop_line_pts[1]):

																					rear_data.append(round(r_prop_line_point.distance(r_prop_linea),2))

												elif y_r_prop_line.dxftype() == 'ARC':

													y_r_prop_start_pts = [y_r_prop_line.start_point[0],
																		  y_r_prop_line.start_point[1]]

													y_r_prop_end_pts = [y_r_prop_line.end_point[0],
																		y_r_prop_line.end_point[1]]

													y_prop_line = [y_r_prop_start_pts, y_r_prop_end_pts]

													np_y_prop_line = np.array(y_prop_line).round(2)

													if np_y_prop_line[0, 0] == np_prop_linex_y[0, 0] and np_y_prop_line[
														1, 0] == np_prop_linex_y[1, 0]:

														y_prop_work_line = LineString(np_y_prop_line)

														min_np_y_prop_line = np_y_prop_line.min(axis=0)

														max_np_y_prop_line = np_y_prop_line.max(axis=0)

														for organized_open_space_text in org_mtext:

															org_open_space = organized_open_space_text.dxf.text if organized_open_space_text.dxftype() == 'TEXT' else organized_open_space_text.plain_text()

															if org_open_space == 'Tot-lot' or org_open_space == 'Tot lot':

																organized_attrib = organized_open_space_text.dxfattribs()

																tot_lot_pts = organized_attrib['insert']

																np_tot_lot_pts = np.array(
																	[tot_lot_pts[0], tot_lot_pts[1]]).round(2)

																tot_lot_coords = Point(np_tot_lot_pts)

																for organized_open_space_poly in org_polygon:

																	organized_open_space_poly_pts = [y[0:2] for y in
																									 organized_open_space_poly.get_points()]

																	np_organized_open_space_poly_pts = np.array(
																		organized_open_space_poly_pts).round(2)

																	organized_space_poly = Polygon(
																		np_organized_open_space_poly_pts)

																	if organized_space_poly.contains(
																			tot_lot_coords) == True:

																		for r_tot_pts in np_organized_open_space_poly_pts:

																			np_r_tot_pts = np.array(r_tot_pts).round(2)

																			np_r_tot_point = Point(np_r_tot_pts)

																			if round(prop_poly1.distance(
																					organized_space_poly)) != 0:

																				if (min_np_y_prop_line[0] <=
																					np_r_tot_pts[0] and
																					max_np_y_prop_line[0] >=
																					np_r_tot_pts[0]) or (
																						min_np_y_prop_line[1] <=
																						np_r_tot_pts[1] and
																						max_np_y_prop_line[1] >=
																						np_r_tot_pts[1]):

																					rear_data.append(round(
																						np_r_tot_point.distance(
																							y_prop_work_line), 2))

																				else:

																					# tot lot polygon convert lines

																					for r_tot_line in organized_open_space_poly.virtual_entities():

																						if r_tot_line.dxftype() == 'LINE':

																							r_tot_start_pts = [
																								r_tot_line.dxf.start[0],
																								r_tot_line.dxf.start[1]]

																							r_tot_end_pts = [
																								r_tot_line.dxf.end[0],
																								r_tot_line.dxf.end[1]]

																							r_tot_line_pts = [
																								r_tot_start_pts,
																								r_tot_end_pts]

																							np_r_tot_line_pts = np.array(
																								r_tot_line_pts).round(2)

																							max_np_r_tot_line_pts = np_r_tot_line_pts.max(
																								axis=0)

																							min_np_r_tot_line_pts = np_r_tot_line_pts.min(
																								axis=0)

																							r_tot_line_point = LineString(
																								np_r_tot_line_pts)

																							# proposed work line convert into points

																							for r_prop_work_pts in np_y_prop_line:

																								np_r_prop_work_pts = np.array(
																									r_prop_work_pts).round(
																									2)

																								r_prop_work_point = Point(
																									np_r_prop_work_pts)

																								# check condition tot_lot line incluide proposed work points or not

																								if (
																										max_np_r_tot_line_pts[
																											0] >=
																										np_r_prop_work_pts[
																											0] and
																										min_np_r_tot_line_pts[
																											0] <=
																										np_r_prop_work_pts[
																											0]) or (
																										max_np_r_tot_line_pts[
																											1] >=
																										np_r_prop_work_pts[
																											1] and
																										min_np_r_tot_line_pts[
																											1] <=
																										np_r_prop_work_pts[
																											1]):
																									rear_data.append(
																										round(
																											r_prop_work_point.distance(
																												r_tot_line_point),
																											2))

																						elif r_tot_line.dxftype() == 'ARC':

																							r_tot_start_pts = [
																								r_tot_line.start_point[
																									0],
																								r_tot_line.start_point[
																									1]]

																							r_tot_end_pts = [
																								r_tot_line.end_point[0],
																								r_tot_line.end_point[1]]

																							r_tot_line_pts = [
																								r_tot_start_pts,
																								r_tot_end_pts]

																							np_r_tot_line_pts = np.array(
																								r_tot_line_pts).round(2)

																							max_np_r_tot_line_pts = np_r_tot_line_pts.max(
																								axis=0)

																							min_np_r_tot_line_pts = np_r_tot_line_pts.min(
																								axis=0)

																							r_tot_line_point = LineString(
																								np_r_tot_line_pts)

																							# proposed work line convert into points

																							for r_prop_work_pts in np_y_prop_line:

																								np_r_prop_work_pts = np.array(
																									r_prop_work_pts).round(
																									2)

																								r_prop_work_point = Point(
																									np_r_prop_work_pts)

																								# check condition tot_lot line incluide proposed work points or not

																								if (
																										max_np_r_tot_line_pts[
																											0] >=
																										np_r_prop_work_pts[
																											0] and
																										min_np_r_tot_line_pts[
																											0] <=
																										np_r_prop_work_pts[
																											0]) or (
																										max_np_r_tot_line_pts[
																											1] >=
																										np_r_prop_work_pts[
																											1] and
																										min_np_r_tot_line_pts[
																											1] <=
																										np_r_prop_work_pts[
																											1]):
																									rear_data.append(
																										round(
																											r_prop_work_point.distance(
																												r_tot_line_point),
																											2))
																			elif (round(prop_poly1.distance(
																					organized_space_poly)) == 0):

																				rear_data.append(round(
																					organized_space_poly.distance(
																						r_margin_linex_y), 2))

														# This loop for rear line to prop_work block

														for rprop_work_poly in proposed_polygon:

															rprop_poly_pts = [b[0:2] for b in
																			  rprop_work_poly.get_points()]

															np_rprop_poly_pts = np.array(rprop_poly_pts).round(2)

															rprop_poly = Polygon(np_rprop_poly_pts)

															for r_prop_pts in np_rprop_poly_pts:

																np_r_prop_pts = np.array(r_prop_pts).round(2)

																np_r_prop_point = Point(np_r_prop_pts)

																if round(prop_poly1.distance(rprop_poly)) != 0:

																	if (min_np_y_prop_line[0] <= np_r_prop_pts[0] and
																		max_np_y_prop_line[0] >= np_r_prop_pts[0]) or (
																			min_np_y_prop_line[1] <= np_r_prop_pts[
																		1] and max_np_y_prop_line[1] >= np_r_prop_pts[
																				1]):

																		rear_data.append(round(
																			np_r_prop_point.distance(y_prop_work_line),
																			2))

																	else:

																		for r_prop_line in rprop_work_poly.virtual_entities():

																			r_start_prop_pts = [
																				r_prop_line.dxf.start[0],
																				r_prop_line.dxf.start[1]]

																			r_end_prop_pts = [r_prop_line.dxf.end[0],
																							  r_prop_line.dxf.end[1]]

																			r_prop_line = [r_start_prop_pts,
																						   r_end_prop_pts]

																			np_r_prop_line = np.array(
																				r_prop_line).round(2)

																			r_prop_linea = LineString(np_r_prop_line)

																			max_np_r_prop_line = np_r_prop_line.max(
																				axis=0).round(2)

																			min_np_r_prop_line = np_r_prop_line.min(
																				axis=0).round(2)

																			for r_prop_line_pts in np_prop_linex_y:

																				np_r_prop_line_pts = np.array(
																					r_prop_line_pts).round(2)

																				r_prop_line_point = Point(
																					np_r_prop_line_pts)

																				if (min_np_r_prop_line[0] <=
																					np_r_prop_line_pts[0] and
																					max_np_r_prop_line[0] >=
																					np_r_prop_line_pts[0]) or (
																						min_np_r_prop_line[1] <=
																						np_r_prop_line_pts[1] and
																						max_np_r_prop_line[1] >=
																						np_r_prop_line_pts[1]):
																					rear_data.append(round(
																						r_prop_line_point.distance(
																							r_prop_linea), 2))
										# x and y does not equal

										else:

											for rprop_work_poly in proposed_polygon:

												rprop_poly_pts=[b[0:2] for b in rprop_work_poly.get_points()]

												np_rprop_poly_pts=np.array(rprop_poly_pts).round(2)

												rprop_poly=Polygon(np_rprop_poly_pts)

												for r_prop_pts in rprop_poly_pts:

													np_r_prop_pts=np.array(r_prop_pts).round(2)

													r_prop_point=Point(np_r_prop_pts)

													if round(prop_poly1.distance(rprop_poly))!=0:

														if (max_prop_linex_y[0]>=np_r_prop_pts[0] and min_prop_linex_y[0]<=np_r_prop_pts[0]) or (max_prop_linex_y[1]>=np_r_prop_pts[1] and min_prop_linex_y[1]<=np_r_prop_pts[1]):

															rear_data.append(round(r_prop_point.distance(r_prop_linex_y),2))

									else:

										for r_lwpolygon in proposed_polygon:

											r_lwpolygon_pts=[p[0:2] for p in r_lwpolygon.get_points()]

											np_r_lwpolygon_pts=np.array(r_lwpolygon_pts).round(2)

											r_lwpolygon_poly=Polygon(np_r_lwpolygon_pts)

											for r_prop_line in r_lwpolygon.virtual_entities():

												if r_prop_line.dxftype()=='LINE':

													r_prop_start_pts=[r_prop_line.dxf.start[0],r_prop_line.dxf.start[1]]

													r_prop_end_pts=[r_prop_line.dxf.end[0],r_prop_line.dxf.end[1]]

													r_prop_line_pts=[r_prop_start_pts,r_prop_end_pts]

													np_r_prop_line_point=np.array(r_prop_line_pts).round(2)

													r_prop_line_point=LineString(np_r_prop_line_point)

													max_np_r_prop_line_point=np_r_prop_line_point.max(axis=0)

													min_np_r_prop_line_point=np_r_prop_line_point.min(axis=0)

													if round(r_lwpolygon_poly.distance(prop_poly1),1)!=0:

														if (max_np_r_prop_line_point[0]>=np_y_rline_pts[0] and min_np_r_prop_line_point[0]<=np_y_rline_pts[0]) or (max_np_r_prop_line_point[1]>=np_y_rline_pts[1] and min_np_r_prop_line_point[1]<=np_y_rline_pts[1]):

															rear_data.append(round(y_rline_point.distance(r_prop_line_point),2))
												elif r_prop_line.dxftype() == 'ARC':

													r_prop_start_pts = [r_prop_line.start_point[0],
																		r_prop_line.start_point[1]]

													r_prop_end_pts = [r_prop_line.end_point[0], r_prop_line.end_point[1]]

													r_prop_line_pts = [r_prop_start_pts, r_prop_end_pts]

													np_r_prop_line_point = np.array(r_prop_line_pts).round(2)

													r_prop_line_point = LineString(np_r_prop_line_point)

													max_np_r_prop_line_point = np_r_prop_line_point.max(axis=0)

													min_np_r_prop_line_point = np_r_prop_line_point.min(axis=0)

													if round(r_lwpolygon_poly.distance(prop_poly1), 1) != 0:

														if (max_np_r_prop_line_point[0] >= np_y_rline_pts[0] and
															min_np_r_prop_line_point[0] <= np_y_rline_pts[0]) or (
																max_np_r_prop_line_point[1] >= np_y_rline_pts[1] and
																min_np_r_prop_line_point[1] <= np_y_rline_pts[1]):
															rear_data.append(
																round(y_rline_point.distance(r_prop_line_point), 2))
					s1line_pts_value=[]

					s1line_pts=[]

					for s1data in side1_coordinate_data:

						s1_prop_linex=LineString(s1data[0])

						s1_margin_linex=LineString(s1data[1])

						if round(s1_prop_linex.distance(s1_margin_linex),1)==min(side1_data):

							s1_np_prop_linex=np.array(s1data[0]).round(2)

							prop_line_splits1=split(s1_np_prop_linex[0],s1_np_prop_linex[1],4)

							for prop_splits1_pts in prop_line_splits1[1:-1]:

								np_prop_splits1_pts=np.array(prop_splits1_pts).round(2)

								prop_splits1_point=Point(np_prop_splits1_pts)

								s1line_pts_value.append(round(prop_splits1_point.distance(s1_margin_linex),1))

								s1line_pts.append(np_prop_splits1_pts)

					for s1data_x in side1_coordinate_data:

						s1_prop_linex_x1=LineString(s1data_x[0])

						s1_margin_linex_x1=LineString(s1data_x[1])

						# match minimum proposed line to side1 data

						if round(s1_prop_linex_x1.distance(s1_margin_linex_x1),1)==min(side1_data):

							np_prop_linex_x1=np.array(s1data_x[0]).round(2)

							max_prop_linex_x1=np_prop_linex_x1.max(axis=0).round(2)

							min_prop_linex_x1=np_prop_linex_x1.min(axis=0).round(2)

							for x1_s1line_pts in s1line_pts:

								np_x1_s1line_pts=np.array(x1_s1line_pts).round(2)

								x1_s1line_point=Point(np_x1_s1line_pts)

								#check point in proposed line or not

								if ((max_prop_linex_x1[0]>=np_x1_s1line_pts[0] and min_prop_linex_x1[0]<=np_x1_s1line_pts[0]) and (max_prop_linex_x1[1]>=np_x1_s1line_pts[1] and min_prop_linex_x1[1]<=np_x1_s1line_pts[1])):

									#match minimum proposed  point to side 1 line distance

									if round(x1_s1line_point.distance(s1_margin_linex_x1),1)==min(s1line_pts_value):

										# y value is  equal

										if np_prop_linex_x1[0,1]==np_prop_linex_x1[1,1]:

											#proposed polygon convert into lines

											for x1_s1_prop_line in lwpolyline.virtual_entities():

												if x1_s1_prop_line.dxftype()=='LINE':

													x1_s1_prop_start_pts=[x1_s1_prop_line.dxf.start[0],x1_s1_prop_line.dxf.start[1]]

													x1_s1_prop_end_pts=[x1_s1_prop_line.dxf.end[0],x1_s1_prop_line.dxf.end[1]]

													x1_prop_line=[x1_s1_prop_start_pts,x1_s1_prop_end_pts]

													np_x1_prop_line=np.array(x1_prop_line).round(2)

													# check y value same as line

													if np_x1_prop_line[0,1]==np_prop_linex_x1[0,1] and np_x1_prop_line[1,1]==np_prop_linex_x1[1,1]:

														x1_prop_work_line=LineString(np_x1_prop_line)

														min_np_x1_prop_line=np_x1_prop_line.min(axis=0)

														max_np_x1_prop_line=np_x1_prop_line.max(axis=0)

														# tot_lot data

														for organized_open_space_text in org_mtext:

															org_open_space = organized_open_space_text.dxf.text if organized_open_space_text.dxftype() == 'TEXT' else organized_open_space_text.plain_text()

															if org_open_space=='Tot-lot' or org_open_space=='Tot lot':

																organized_attrib=organized_open_space_text.dxfattribs()

																tot_lot_pts=organized_attrib['insert']

																np_tot_lot_pts=np.array([tot_lot_pts[0],tot_lot_pts[1]]).round(2)

																tot_lot_coords=Point(np_tot_lot_pts)

																for organized_open_space_poly in org_polygon:

																	organized_open_space_poly_pts=[y[0:2] for y in organized_open_space_poly.get_points()]

																	np_organized_open_space_poly_pts=np.array(organized_open_space_poly_pts).round(2)

																	organized_space_poly=Polygon(np_organized_open_space_poly_pts)

																	# check text data in totlot polygon

																	if organized_space_poly.contains(tot_lot_coords)==True:

																		# totlot polygon convert into points

																		for s1_tot_pts in np_organized_open_space_poly_pts:

																			np_s1_tot_pts=np.array(s1_tot_pts).round(2)

																			np_s1_tot_point=Point(np_s1_tot_pts)

																			# check proposed polygon to totlot polygon distance is not 0

																			if round(prop_poly1.distance(organized_space_poly))!=0:

																				#check totlot point in minimum proposed line or not

																				if (min_np_x1_prop_line[0]<=np_s1_tot_pts[0] and  max_np_x1_prop_line[0]>=np_s1_tot_pts[0]) or (min_np_x1_prop_line[1]<=np_s1_tot_pts[1] and  max_np_x1_prop_line[1]>=np_s1_tot_pts[1]):

																					side1_data.append(round(np_s1_tot_point.distance(x1_prop_work_line),2))

																				else:

																					#tot lot polygon convert lines

																					for s1_tot_line in organized_open_space_poly.virtual_entities():

																						if s1_tot_line.dxftype()=='LINE':

																							s1_tot_start_pts=[s1_tot_line.dxf.start[0],s1_tot_line.dxf.start[1]]

																							s1_tot_end_pts=[s1_tot_line.dxf.end[0],s1_tot_line.dxf.end[1]]

																							s1_tot_line_pts=[s1_tot_start_pts,s1_tot_end_pts]

																							np_s1_tot_line_pts=np.array(s1_tot_line_pts).round(2)

																							max_np_s1_tot_line_pts=np_s1_tot_line_pts.max(axis=0)

																							min_np_s1_tot_line_pts=np_s1_tot_line_pts.min(axis=0)

																							s1_tot_line_point=LineString(np_s1_tot_line_pts)

																							# proposed work line convert into points

																							for s1_prop_work_pts in np_x1_prop_line:

																								np_s1_prop_work_pts=np.array(s1_prop_work_pts).round(2)

																								s1_prop_work_point=Point(np_s1_prop_work_pts)

																								#check proposed work point in totlot line

																								if (max_np_s1_tot_line_pts[0]>=np_s1_prop_work_pts[0] and min_np_s1_tot_line_pts[0]<=np_s1_prop_work_pts[0]) or (max_np_s1_tot_line_pts[1]>=np_s1_prop_work_pts[1] and min_np_s1_tot_line_pts[1]<=np_s1_prop_work_pts[1]):

																									side1_data.append(round(s1_prop_work_point.distance(s1_tot_line_point),2))

																						elif s1_tot_line.dxftype() == 'ARC':

																							s1_tot_start_pts = [
																								s1_tot_line.start_point[
																									0],
																								s1_tot_line.start_point[
																									1]]

																							s1_tot_end_pts = [
																								s1_tot_line.end_point[0],
																								s1_tot_line.end_point[1]]

																							s1_tot_line_pts = [
																								s1_tot_start_pts,
																								s1_tot_end_pts]

																							np_s1_tot_line_pts = np.array(
																								s1_tot_line_pts).round(
																								2)

																							max_np_s1_tot_line_pts = np_s1_tot_line_pts.max(
																								axis=0)

																							min_np_s1_tot_line_pts = np_s1_tot_line_pts.min(
																								axis=0)

																							s1_tot_line_point = LineString(
																								np_s1_tot_line_pts)

																							# proposed work line convert into points

																							for s1_prop_work_pts in np_x1_prop_line:

																								np_s1_prop_work_pts = np.array(
																									s1_prop_work_pts).round(
																									2)

																								s1_prop_work_point = Point(
																									np_s1_prop_work_pts)

																								# check proposed work point in totlot line

																								if (
																										max_np_s1_tot_line_pts[
																											0] >=
																										np_s1_prop_work_pts[
																											0] and
																										min_np_s1_tot_line_pts[
																											0] <=
																										np_s1_prop_work_pts[
																											0]) or (
																										max_np_s1_tot_line_pts[
																											1] >=
																										np_s1_prop_work_pts[
																											1] and
																										min_np_s1_tot_line_pts[
																											1] <=
																										np_s1_prop_work_pts[
																											1]):
																									side1_data.append(
																										round(
																											s1_prop_work_point.distance(
																												s1_tot_line_point),
																											2))

																			#check totlot polygon and proposed polygon diatnce is 0

																			elif(round(prop_poly1.distance(organized_space_poly))==0):

																				side1_data.append(round(organized_space_poly.distance(s1_margin_linex_x1),2))

														#This loop for side1 line to prop_work block

														for s1prop_work_poly in proposed_polygon:

															s1prop_poly_pts=[c[0:2] for c in s1prop_work_poly.get_points()]

															np_s1prop_poly_pts=np.array(s1prop_poly_pts).round(2)

															s1prop_poly=Polygon(np_s1prop_poly_pts)

															for s1_prop_pts in np_s1prop_poly_pts:

																np_s1_prop_pts=np.array(s1_prop_pts).round(2)

																np_s1_prop_point=Point(np_s1_prop_pts)

																#proposed polygon to proposed polygon is not 0

																if round(prop_poly1.distance(s1prop_poly))!=0:

																	#proposed polygon point in minimum propposed line

																	if (min_np_x1_prop_line[0]<=np_s1_prop_pts[0] and  max_np_x1_prop_line[0]>=np_s1_prop_pts[0]) or (min_np_x1_prop_line[1]<=np_s1_prop_pts[1] and  max_np_x1_prop_line[1]>=np_s1_prop_pts[1]):

																		side1_data.append(round(np_s1_prop_point.distance(x1_prop_work_line),2))

																	else:

																		#propposed work polygon convert into line

																		for s1_prop_line in s1prop_work_poly.virtual_entities():

																			s1_start_prop_pts=[s1_prop_line.dxf.start[0],s1_prop_line.dxf.start[1]]

																			s1_end_prop_pts=[s1_prop_line.dxf.end[0],s1_prop_line.dxf.end[1]]

																			s1_prop_line=[s1_start_prop_pts,s1_end_prop_pts]

																			np_s1_prop_line=np.array(s1_prop_line).round(2)

																			s1_prop_linea=LineString(np_s1_prop_line)

																			max_np_s1_prop_line=np_s1_prop_line.max(axis=0).round(2)

																			min_np_s1_prop_line=np_s1_prop_line.min(axis=0).round(2)

																			# minimum proposed work line convert into points

																			for s1_prop_line_pts in np_prop_linex_x1:

																				np_s1_prop_line_pts=np.array(s1_prop_line_pts).round(2)

																				s1_prop_line_point=Point(np_s1_prop_line_pts)

																				# minimum proposed work line points in proposed work line

																				if (min_np_s1_prop_line[0]<=np_s1_prop_line_pts[0] and  max_np_s1_prop_line[0]>=np_s1_prop_line_pts[0]) or (min_np_s1_prop_line[1]<=np_s1_prop_line_pts[1] and  max_np_s1_prop_line[1]>=np_s1_prop_line_pts[1]):

																					side1_data.append(round(s1_prop_line_point.distance(s1_prop_linea),2))

												elif x1_s1_prop_line.dxftype() == 'ARC':

													x1_s1_prop_start_pts = [x1_s1_prop_line.start_point[0],
																			x1_s1_prop_line.start_point[1]]

													x1_s1_prop_end_pts = [x1_s1_prop_line.end_point[0],
																		  x1_s1_prop_line.end_point[1]]

													x1_prop_line = [x1_s1_prop_start_pts, x1_s1_prop_end_pts]

													np_x1_prop_line = np.array(x1_prop_line).round(2)

													# check y value same as line

													if np_x1_prop_line[0, 1] == np_prop_linex_x1[0, 1] and \
															np_x1_prop_line[1, 1] == np_prop_linex_x1[1, 1]:

														x1_prop_work_line = LineString(np_x1_prop_line)

														min_np_x1_prop_line = np_x1_prop_line.min(axis=0)

														max_np_x1_prop_line = np_x1_prop_line.max(axis=0)

														# tot_lot data

														for organized_open_space_text in org_mtext:

															org_open_space = organized_open_space_text.dxf.text if organized_open_space_text.dxftype() == 'TEXT' else organized_open_space_text.plain_text()

															if org_open_space == 'Tot-lot' or org_open_space == 'Tot lot':

																organized_attrib = organized_open_space_text.dxfattribs()

																tot_lot_pts = organized_attrib['insert']

																np_tot_lot_pts = np.array(
																	[tot_lot_pts[0], tot_lot_pts[1]]).round(2)

																tot_lot_coords = Point(np_tot_lot_pts)

																for organized_open_space_poly in org_polygon:

																	organized_open_space_poly_pts = [y[0:2] for y in
																									 organized_open_space_poly.get_points()]

																	np_organized_open_space_poly_pts = np.array(
																		organized_open_space_poly_pts).round(2)

																	organized_space_poly = Polygon(
																		np_organized_open_space_poly_pts)

																	# check text data in totlot polygon

																	if organized_space_poly.contains(
																			tot_lot_coords) == True:

																		# totlot polygon convert into points

																		for s1_tot_pts in np_organized_open_space_poly_pts:

																			np_s1_tot_pts = np.array(s1_tot_pts).round(
																				2)

																			np_s1_tot_point = Point(np_s1_tot_pts)

																			# check proposed polygon to totlot polygon distance is not 0

																			if round(prop_poly1.distance(
																					organized_space_poly)) != 0:

																				# check totlot point in minimum proposed line or not

																				if (min_np_x1_prop_line[0] <=
																					np_s1_tot_pts[0] and
																					max_np_x1_prop_line[0] >=
																					np_s1_tot_pts[0]) or (
																						min_np_x1_prop_line[1] <=
																						np_s1_tot_pts[1] and
																						max_np_x1_prop_line[1] >=
																						np_s1_tot_pts[1]):

																					side1_data.append(round(
																						np_s1_tot_point.distance(
																							x1_prop_work_line), 2))

																				else:

																					# tot lot polygon convert lines

																					for s1_tot_line in organized_open_space_poly.virtual_entities():

																						if s1_tot_line.dxftype() == 'LINE':

																							s1_tot_start_pts = [
																								s1_tot_line.dxf.start[
																									0],
																								s1_tot_line.dxf.start[
																									1]]

																							s1_tot_end_pts = [
																								s1_tot_line.dxf.end[0],
																								s1_tot_line.dxf.end[1]]

																							s1_tot_line_pts = [
																								s1_tot_start_pts,
																								s1_tot_end_pts]

																							np_s1_tot_line_pts = np.array(
																								s1_tot_line_pts).round(
																								2)

																							max_np_s1_tot_line_pts = np_s1_tot_line_pts.max(
																								axis=0)

																							min_np_s1_tot_line_pts = np_s1_tot_line_pts.min(
																								axis=0)

																							s1_tot_line_point = LineString(
																								np_s1_tot_line_pts)

																							# proposed work line convert into points

																							for s1_prop_work_pts in np_x1_prop_line:

																								np_s1_prop_work_pts = np.array(
																									s1_prop_work_pts).round(
																									2)

																								s1_prop_work_point = Point(
																									np_s1_prop_work_pts)

																								# check proposed work point in totlot line

																								if (
																										max_np_s1_tot_line_pts[
																											0] >=
																										np_s1_prop_work_pts[
																											0] and
																										min_np_s1_tot_line_pts[
																											0] <=
																										np_s1_prop_work_pts[
																											0]) or (
																										max_np_s1_tot_line_pts[
																											1] >=
																										np_s1_prop_work_pts[
																											1] and
																										min_np_s1_tot_line_pts[
																											1] <=
																										np_s1_prop_work_pts[
																											1]):
																									side1_data.append(
																										round(
																											s1_prop_work_point.distance(
																												s1_tot_line_point),
																											2))

																						elif s1_tot_line.dxftype() == 'ARC':

																							s1_tot_start_pts = [
																								s1_tot_line.start_point[
																									0],
																								s1_tot_line.start_point[
																									1]]

																							s1_tot_end_pts = [
																								s1_tot_line.end_point[
																									0],
																								s1_tot_line.end_point[
																									1]]

																							s1_tot_line_pts = [
																								s1_tot_start_pts,
																								s1_tot_end_pts]

																							np_s1_tot_line_pts = np.array(
																								s1_tot_line_pts).round(
																								2)

																							max_np_s1_tot_line_pts = np_s1_tot_line_pts.max(
																								axis=0)

																							min_np_s1_tot_line_pts = np_s1_tot_line_pts.min(
																								axis=0)

																							s1_tot_line_point = LineString(
																								np_s1_tot_line_pts)

																							# proposed work line convert into points

																							for s1_prop_work_pts in np_x1_prop_line:

																								np_s1_prop_work_pts = np.array(
																									s1_prop_work_pts).round(
																									2)

																								s1_prop_work_point = Point(
																									np_s1_prop_work_pts)

																								# check proposed work point in totlot line

																								if (
																										max_np_s1_tot_line_pts[
																											0] >=
																										np_s1_prop_work_pts[
																											0] and
																										min_np_s1_tot_line_pts[
																											0] <=
																										np_s1_prop_work_pts[
																											0]) or (
																										max_np_s1_tot_line_pts[
																											1] >=
																										np_s1_prop_work_pts[
																											1] and
																										min_np_s1_tot_line_pts[
																											1] <=
																										np_s1_prop_work_pts[
																											1]):
																									side1_data.append(
																										round(
																											s1_prop_work_point.distance(
																												s1_tot_line_point),
																											2))

																			# check totlot polygon and proposed polygon diatnce is 0

																			elif (round(prop_poly1.distance(
																					organized_space_poly)) == 0):

																				side1_data.append(round(
																					organized_space_poly.distance(
																						s1_margin_linex_x1), 2))

														# This loop for side1 line to prop_work block

														for s1prop_work_poly in proposed_polygon:

															s1prop_poly_pts = [c[0:2] for c in
																			   s1prop_work_poly.get_points()]

															np_s1prop_poly_pts = np.array(s1prop_poly_pts).round(2)

															s1prop_poly = Polygon(np_s1prop_poly_pts)

															for s1_prop_pts in np_s1prop_poly_pts:

																np_s1_prop_pts = np.array(s1_prop_pts).round(2)

																np_s1_prop_point = Point(np_s1_prop_pts)

																# proposed polygon to proposed polygon is not 0

																if round(prop_poly1.distance(s1prop_poly)) != 0:

																	# proposed polygon point in minimum propposed line

																	if (min_np_x1_prop_line[0] <= np_s1_prop_pts[0] and
																		max_np_x1_prop_line[0] >= np_s1_prop_pts[
																			0]) or (
																			min_np_x1_prop_line[1] <= np_s1_prop_pts[
																		1] and max_np_x1_prop_line[1] >= np_s1_prop_pts[
																				1]):

																		side1_data.append(round(
																			np_s1_prop_point.distance(
																				x1_prop_work_line), 2))

																	else:

																		# propposed work polygon convert into line

																		for s1_prop_line in s1prop_work_poly.virtual_entities():

																			if s1_prop_line.dxftype()=='LINE':

																				s1_start_prop_pts = [
																					s1_prop_line.dxf.start[0],
																					s1_prop_line.dxf.start[1]]

																				s1_end_prop_pts = [s1_prop_line.dxf.end[0],
																								   s1_prop_line.dxf.end[1]]

																				s1_prop_line = [s1_start_prop_pts,
																								s1_end_prop_pts]

																				np_s1_prop_line = np.array(
																					s1_prop_line).round(2)

																				s1_prop_linea = LineString(np_s1_prop_line)

																				max_np_s1_prop_line = np_s1_prop_line.max(
																					axis=0).round(2)

																				min_np_s1_prop_line = np_s1_prop_line.min(
																					axis=0).round(2)

																				# minimum proposed work line convert into points

																				for s1_prop_line_pts in np_prop_linex_x1:

																					np_s1_prop_line_pts = np.array(
																						s1_prop_line_pts).round(2)

																					s1_prop_line_point = Point(
																						np_s1_prop_line_pts)

																					# minimum proposed work line points in proposed work line

																					if (min_np_s1_prop_line[0] <=
																						np_s1_prop_line_pts[0] and
																						max_np_s1_prop_line[0] >=
																						np_s1_prop_line_pts[0]) or (
																							min_np_s1_prop_line[1] <=
																							np_s1_prop_line_pts[1] and
																							max_np_s1_prop_line[1] >=
																							np_s1_prop_line_pts[1]):
																						side1_data.append(round(
																							s1_prop_line_point.distance(
																								s1_prop_linea), 2))

																			elif s1_prop_line.dxftype() == 'ARC':

																				s1_start_prop_pts = [
																					s1_prop_line.start_point[0],
																					s1_prop_line.start_point[1]]

																				s1_end_prop_pts = [
																					s1_prop_line.end_point[0],
																					s1_prop_line.end_point[1]]

																				s1_prop_line = [s1_start_prop_pts,
																								s1_end_prop_pts]

																				np_s1_prop_line = np.array(
																					s1_prop_line).round(2)

																				s1_prop_linea = LineString(
																					np_s1_prop_line)

																				max_np_s1_prop_line = np_s1_prop_line.max(
																					axis=0).round(2)

																				min_np_s1_prop_line = np_s1_prop_line.min(
																					axis=0).round(2)

																				# minimum proposed work line convert into points

																				for s1_prop_line_pts in np_prop_linex_x1:

																					np_s1_prop_line_pts = np.array(
																						s1_prop_line_pts).round(2)

																					s1_prop_line_point = Point(
																						np_s1_prop_line_pts)

																					# minimum proposed work line points in proposed work line

																					if (min_np_s1_prop_line[0] <=
																						np_s1_prop_line_pts[0] and
																						max_np_s1_prop_line[0] >=
																						np_s1_prop_line_pts[0]) or (
																							min_np_s1_prop_line[1] <=
																							np_s1_prop_line_pts[1] and
																							max_np_s1_prop_line[1] >=
																							np_s1_prop_line_pts[1]):
																						side1_data.append(round(
																							s1_prop_line_point.distance(
																								s1_prop_linea), 2))
										#used for x axis equal data

										elif(np_prop_linex_x1[0,0]==np_prop_linex_x1[1,0]):

											for x1_s1_prop_line in lwpolyline.virtual_entities():

												if x1_s1_prop_line.dxftype()=='LINE':

													x1_s1_prop_start_pts=[x1_s1_prop_line.dxf.start[0],x1_s1_prop_line.dxf.start[1]]

													x1_s1_prop_end_pts=[x1_s1_prop_line.dxf.end[0],x1_s1_prop_line.dxf.end[1]]

													x1_prop_line=[x1_s1_prop_start_pts,x1_s1_prop_end_pts]

													np_x1_prop_line=np.array(x1_prop_line).round(2)

													if np_x1_prop_line[0,0]==np_prop_linex_x1[0,0] and np_x1_prop_line[1,0]==np_prop_linex_x1[1,0]:

														x1_prop_work_line=LineString(np_x1_prop_line)

														min_np_x1_prop_line=np_x1_prop_line.min(axis=0)

														max_np_x1_prop_line=np_x1_prop_line.max(axis=0)

														for organized_open_space_text in org_mtext:

															org_open_space = organized_open_space_text.dxf.text if organized_open_space_text.dxftype() == 'TEXT' else organized_open_space_text.plain_text()

															if org_open_space=='Tot-lot' or org_open_space=='Tot lot':

																organized_attrib=organized_open_space_text.dxfattribs()

																tot_lot_pts=organized_attrib['insert']

																np_tot_lot_pts=np.array([tot_lot_pts[0],tot_lot_pts[1]]).round(2)

																tot_lot_coords=Point(np_tot_lot_pts)

																for organized_open_space_poly in org_polygon:

																	organized_open_space_poly_pts=[y[0:2] for y in organized_open_space_poly.get_points()]

																	np_organized_open_space_poly_pts=np.array(organized_open_space_poly_pts).round(2)

																	organized_space_poly=Polygon(np_organized_open_space_poly_pts)

																	if organized_space_poly.contains(tot_lot_coords)==True:

																		for s1_tot_pts in np_organized_open_space_poly_pts:

																			np_s1_tot_pts=np.array(s1_tot_pts).round(2)

																			np_s1_tot_point=Point(np_s1_tot_pts)

																			if round(prop_poly1.distance(organized_space_poly))!=0:

																				if (min_np_x1_prop_line[0]<=np_s1_tot_pts[0] and  max_np_x1_prop_line[0]>=np_s1_tot_pts[0]) or (min_np_x1_prop_line[1]<=np_s1_tot_pts[1] and  max_np_x1_prop_line[1]>=np_s1_tot_pts[1]):

																					side1_data.append(round(np_s1_tot_point.distance(x1_prop_work_line),2))

																				else:

																					#tot lot polygon convert lines

																					for s1_tot_line in organized_open_space_poly.virtual_entities():

																						if s1_tot_line.dxftype()=='LINE':

																							s1_tot_start_pts=[s1_tot_line.dxf.start[0],s1_tot_line.dxf.start[1]]

																							s1_tot_end_pts=[s1_tot_line.dxf.end[0],s1_tot_line.dxf.end[1]]

																							s1_tot_line_pts=[s1_tot_start_pts,s1_tot_end_pts]

																							np_s1_tot_line_pts=np.array(s1_tot_line_pts).round(2)

																							max_np_s1_tot_line_pts=np_s1_tot_line_pts.max(axis=0)

																							min_np_s1_tot_line_pts=np_s1_tot_line_pts.min(axis=0)

																							s1_tot_line_point=LineString(np_s1_tot_line_pts)

																							# proposed work line convert into points

																							for s1_prop_work_pts in np_x1_prop_line:

																								np_s1_prop_work_pts=np.array(s1_prop_work_pts).round(2)

																								s1_prop_work_point=Point(np_s1_prop_work_pts)

																								#check condition tot_lot line incluide proposed work points or not

																								if (max_np_s1_tot_line_pts[0]>=np_s1_prop_work_pts[0] and min_np_s1_tot_line_pts[0]<=np_s1_prop_work_pts[0]) or (max_np_s1_tot_line_pts[1]>=np_s1_prop_work_pts[1] and min_np_s1_tot_line_pts[1]<=np_s1_prop_work_pts[1]):

																									side1_data.append(round(s1_prop_work_point.distance(s1_tot_line_point),2))
																						elif s1_tot_line.dxftype() == 'ARC':

																							s1_tot_start_pts = [
																								s1_tot_line.start_point[
																									0],
																								s1_tot_line.start_point[
																									1]]

																							s1_tot_end_pts = [
																								s1_tot_line.end_point[0],
																								s1_tot_line.end_point[1]]

																							s1_tot_line_pts = [
																								s1_tot_start_pts,
																								s1_tot_end_pts]

																							np_s1_tot_line_pts = np.array(
																								s1_tot_line_pts).round(
																								2)

																							max_np_s1_tot_line_pts = np_s1_tot_line_pts.max(
																								axis=0)

																							min_np_s1_tot_line_pts = np_s1_tot_line_pts.min(
																								axis=0)

																							s1_tot_line_point = LineString(
																								np_s1_tot_line_pts)

																							# proposed work line convert into points

																							for s1_prop_work_pts in np_x1_prop_line:

																								np_s1_prop_work_pts = np.array(
																									s1_prop_work_pts).round(
																									2)

																								s1_prop_work_point = Point(
																									np_s1_prop_work_pts)

																								# check condition tot_lot line incluide proposed work points or not

																								if (
																										max_np_s1_tot_line_pts[
																											0] >=
																										np_s1_prop_work_pts[
																											0] and
																										min_np_s1_tot_line_pts[
																											0] <=
																										np_s1_prop_work_pts[
																											0]) or (
																										max_np_s1_tot_line_pts[
																											1] >=
																										np_s1_prop_work_pts[
																											1] and
																										min_np_s1_tot_line_pts[
																											1] <=
																										np_s1_prop_work_pts[
																											1]):
																									side1_data.append(
																										round(
																											s1_prop_work_point.distance(
																												s1_tot_line_point),
																											2))

																			elif(round(prop_poly1.distance(organized_space_poly))==0):

																				side1_data.append(round(organized_space_poly.distance(s1_margin_linex_x1),2))

														#This loop for side1 line to prop_work block

														for s1prop_work_poly in proposed_polygon:

															s1prop_poly_pts=[c[0:2] for c in s1prop_work_poly.get_points()]

															np_s1prop_poly_pts=np.array(s1prop_poly_pts).round(2)

															s1prop_poly=Polygon(np_s1prop_poly_pts)

															for s1_prop_pts in np_s1prop_poly_pts:

																np_s1_prop_pts=np.array(s1_prop_pts).round(2)

																np_s1_prop_point=Point(np_s1_prop_pts)

																if round(prop_poly1.distance(s1prop_poly))!=0:

																	if (min_np_x1_prop_line[0]<=np_s1_prop_pts[0] and  max_np_x1_prop_line[0]>=np_s1_prop_pts[0]) or (min_np_x1_prop_line[1]<=np_s1_prop_pts[1] and  max_np_x1_prop_line[1]>=np_s1_prop_pts[1]):

																		side1_data.append(round(np_s1_prop_point.distance(x1_prop_work_line),2))

																	else:

																		for s1_prop_line in s1prop_work_poly.virtual_entities():

																			if s1_prop_line.dxftype()=='LINE':

																				s1_start_prop_pts=[s1_prop_line.dxf.start[0],s1_prop_line.dxf.start[1]]

																				s1_end_prop_pts=[s1_prop_line.dxf.end[0],s1_prop_line.dxf.end[1]]

																				s1_prop_line=[s1_start_prop_pts,s1_end_prop_pts]

																				np_s1_prop_line=np.array(s1_prop_line).round(2)

																				s1_prop_linea=LineString(np_s1_prop_line)

																				max_np_s1_prop_line=np_s1_prop_line.max(axis=0).round(2)

																				min_np_s1_prop_line=np_s1_prop_line.min(axis=0).round(2)

																				for s1_prop_line_pts in np_prop_linex_x1:

																					np_s1_prop_line_pts=np.array(s1_prop_line_pts).round(2)

																					s1_prop_line_point=Point(np_s1_prop_line_pts)

																					if (min_np_s1_prop_line[0]<=np_s1_prop_line_pts[0] and  max_np_s1_prop_line[0]>=np_s1_prop_line_pts[0]) or (min_np_s1_prop_line[1]<=np_s1_prop_line_pts[1] and  max_np_s1_prop_line[1]>=np_s1_prop_line_pts[1]):

																						side1_data.append(round(s1_prop_line_point.distance(s1_prop_linea),2))
																			elif s1_prop_line.dxftype() == 'ARC':

																				s1_start_prop_pts = [
																					s1_prop_line.start_point[0],
																					s1_prop_line.start_point[1]]

																				s1_end_prop_pts = [
																					s1_prop_line.end_point[0],
																					s1_prop_line.end_point[1]]

																				s1_prop_line = [s1_start_prop_pts,
																								s1_end_prop_pts]

																				np_s1_prop_line = np.array(
																					s1_prop_line).round(2)

																				s1_prop_linea = LineString(
																					np_s1_prop_line)

																				max_np_s1_prop_line = np_s1_prop_line.max(
																					axis=0).round(2)

																				min_np_s1_prop_line = np_s1_prop_line.min(
																					axis=0).round(2)

																				for s1_prop_line_pts in np_prop_linex_x1:

																					np_s1_prop_line_pts = np.array(
																						s1_prop_line_pts).round(2)

																					s1_prop_line_point = Point(
																						np_s1_prop_line_pts)

																					if (min_np_s1_prop_line[0] <=
																						np_s1_prop_line_pts[0] and
																						max_np_s1_prop_line[0] >=
																						np_s1_prop_line_pts[0]) or (
																							min_np_s1_prop_line[1] <=
																							np_s1_prop_line_pts[1] and
																							max_np_s1_prop_line[1] >=
																							np_s1_prop_line_pts[1]):
																						side1_data.append(round(
																							s1_prop_line_point.distance(
																								s1_prop_linea), 2))
					s2line_pts_value=[]

					s2line_pts=[]

					for s2data in side2_coordinate_data:

						s2_prop_linex=LineString(s2data[0])

						s2_margin_linex=LineString(s2data[1])

						if round(s2_prop_linex.distance(s2_margin_linex),1)==min(side2_data):

							s2_np_prop_linex=np.array(s2data[0]).round(2)

							prop_line_splits2=split(s2_np_prop_linex[0],s2_np_prop_linex[1],4)

							for prop_splits2_pts in prop_line_splits2[1:-1]:

								np_prop_splits2_pts=np.array(prop_splits2_pts).round(2)

								prop_splits2_point=Point(np_prop_splits2_pts)

								s2line_pts_value.append(round(prop_splits2_point.distance(s2_margin_linex),2))

								s2line_pts.append(np_prop_splits2_pts)

					for s2data_x in side2_coordinate_data:

						s2_prop_linex_y1=LineString(s2data_x[0])

						s2_margin_linex_y1=LineString(s2data_x[1])

						if round(s2_prop_linex_y1.distance(s2_margin_linex_y1),1)==min(side2_data):

							np_prop_linex_y1=np.array(s2data_x[0]).round(2)

							max_prop_linex_y1=np_prop_linex_y1.max(axis=0).round(2)

							min_prop_linex_y1=np_prop_linex_y1.min(axis=0).round(2)

							for y1_s2line_pts in s2line_pts:

								np_y1_s2line_pts=np.array(y1_s2line_pts).round(2)

								y1_s2line_point=Point(np_y1_s2line_pts)

								if ((max_prop_linex_y1[0]>=np_y1_s2line_pts[0] and min_prop_linex_y1[0]<=np_y1_s2line_pts[0]) and (max_prop_linex_y1[1]>=np_y1_s2line_pts[1] and min_prop_linex_y1[1]<=np_y1_s2line_pts[1]))==True:

									if round(y1_s2line_point.distance(s2_margin_linex_y1),2)==min(s2line_pts_value):

										# used for y axis equal

										if np_prop_linex_y1[0,1]==np_prop_linex_y1[1,1]:

											for y1_s2_prop_line in lwpolyline.virtual_entities():

												if y1_s2_prop_line.dxftype()=='LINE':

													y1_s2_prop_start_pts=[y1_s2_prop_line.dxf.start[0],y1_s2_prop_line.dxf.start[1]]

													y1_s2_prop_end_pts=[y1_s2_prop_line.dxf.end[0],y1_s2_prop_line.dxf.end[1]]

													y1_prop_line=[y1_s2_prop_start_pts,y1_s2_prop_end_pts]

													np_y1_prop_line=np.array(y1_prop_line).round(2)

													if np_y1_prop_line[0,1]==np_prop_linex_y1[0,1] and np_y1_prop_line[1,1]==np_prop_linex_y1[1,1]:

														y1_prop_work_line=LineString(np_y1_prop_line)

														min_np_y1_prop_line=np_y1_prop_line.min(axis=0)

														max_np_y1_prop_line=np_y1_prop_line.max(axis=0)

														for organized_open_space_text in org_mtext:

															org_open_space = organized_open_space_text.dxf.text if organized_open_space_text.dxftype() == 'TEXT' else organized_open_space_text.plain_text()

															if org_open_space=='Tot-lot' or org_open_space=='Tot lot':

																organized_attrib=organized_open_space_text.dxfattribs()

																tot_lot_pts=organized_attrib['insert']

																np_tot_lot_pts=np.array([tot_lot_pts[0],tot_lot_pts[1]]).round(2)

																tot_lot_coords=Point(np_tot_lot_pts)

																for organized_open_space_poly in org_polygon:

																	organized_open_space_poly_pts=[y[0:2] for y in organized_open_space_poly.get_points()]

																	np_organized_open_space_poly_pts=np.array(organized_open_space_poly_pts).round(2)

																	organized_space_poly=Polygon(np_organized_open_space_poly_pts)

																	if organized_space_poly.contains(tot_lot_coords)==True:

																		for s2_tot_pts in np_organized_open_space_poly_pts:

																			np_s2_tot_pts=np.array(s2_tot_pts).round(2)

																			np_s2_tot_point=Point(np_s2_tot_pts)

																			if round(prop_poly1.distance(organized_space_poly))!=0:

																				if (min_np_y1_prop_line[0]<=np_s2_tot_pts[0] and  max_np_y1_prop_line[0]>=np_s2_tot_pts[0]) or (min_np_y1_prop_line[1]<=np_s2_tot_pts[1] and  max_np_y1_prop_line[1]>=np_s2_tot_pts[1]):

																					side2_data.append(round(np_s2_tot_point.distance(y1_prop_work_line),2))

																				else:

																					#tot lot polygon convert lines

																					for s2_tot_line in organized_open_space_poly.virtual_entities():

																						if s2_tot_line.dxftype()=='LINE':

																							s2_tot_start_pts=[s2_tot_line.dxf.start[0],s2_tot_line.dxf.start[1]]

																							s2_tot_end_pts=[s2_tot_line.dxf.end[0],s2_tot_line.dxf.end[1]]

																							s2_tot_line_pts=[s2_tot_start_pts,s2_tot_end_pts]

																							np_s2_tot_line_pts=np.array(s2_tot_line_pts).round(2)

																							max_np_s2_tot_line_pts=np_s2_tot_line_pts.max(axis=0)

																							min_np_s2_tot_line_pts=np_s2_tot_line_pts.min(axis=0)

																							s2_tot_line_point=LineString(np_s2_tot_line_pts)

																							# proposed work line convert into points

																							for s2_prop_work_pts in np_y1_prop_line:

																								np_s2_prop_work_pts=np.array(s2_prop_work_pts).round(2)

																								s2_prop_work_point=Point(np_s2_prop_work_pts)

																								#check condition tot_lot line incluide proposed work points or not

																								if (max_np_s2_tot_line_pts[0]>=np_s2_prop_work_pts[0] and min_np_s2_tot_line_pts[0]<=np_s2_prop_work_pts[0]) or (max_np_s2_tot_line_pts[1]>=np_s2_prop_work_pts[1] and min_np_s2_tot_line_pts[1]<=np_s2_prop_work_pts[1]):

																									side2_data.append(round(s2_prop_work_point.distance(s2_tot_line_point),2))

																						elif s2_tot_line.dxftype() == 'ARC':

																							s2_tot_start_pts = [
																								s2_tot_line.start_point[
																									0],
																								s2_tot_line.start_point[
																									1]]

																							s2_tot_end_pts = [
																								s2_tot_line.end_point[0],
																								s2_tot_line.end_point[1]]

																							s2_tot_line_pts = [
																								s2_tot_start_pts,
																								s2_tot_end_pts]

																							np_s2_tot_line_pts = np.array(
																								s2_tot_line_pts).round(
																								2)

																							max_np_s2_tot_line_pts = np_s2_tot_line_pts.max(
																								axis=0)

																							min_np_s2_tot_line_pts = np_s2_tot_line_pts.min(
																								axis=0)

																							s2_tot_line_point = LineString(
																								np_s2_tot_line_pts)

																							# proposed work line convert into points

																							for s2_prop_work_pts in np_y1_prop_line:

																								np_s2_prop_work_pts = np.array(
																									s2_prop_work_pts).round(
																									2)

																								s2_prop_work_point = Point(
																									np_s2_prop_work_pts)

																								# check condition tot_lot line incluide proposed work points or not

																								if (
																										max_np_s2_tot_line_pts[
																											0] >=
																										np_s2_prop_work_pts[
																											0] and
																										min_np_s2_tot_line_pts[
																											0] <=
																										np_s2_prop_work_pts[
																											0]) or (
																										max_np_s2_tot_line_pts[
																											1] >=
																										np_s2_prop_work_pts[
																											1] and
																										min_np_s2_tot_line_pts[
																											1] <=
																										np_s2_prop_work_pts[
																											1]):
																									side2_data.append(
																										round(
																											s2_prop_work_point.distance(
																												s2_tot_line_point),
																											2))
																			elif(round(prop_poly1.distance(organized_space_poly))==0):

																				side2_data.append(round(organized_space_poly.distance(s2_margin_linex_y1),2))

														#This loop for side2 line to prop_work block

														for s2prop_work_poly in proposed_polygon:

															s2prop_poly_pts=[d[0:2] for d in s2prop_work_poly.get_points()]

															np_s2prop_poly_pts=np.array(s2prop_poly_pts).round(2)

															s2prop_poly=Polygon(np_s2prop_poly_pts)

															for s2_prop_pts in np_s2prop_poly_pts:

																np_s2_prop_pts=np.array(s2_prop_pts).round(2)

																np_s2_prop_point=Point(np_s2_prop_pts)

																if round(prop_poly1.distance(s2prop_poly))!=0:

																	if (min_np_y1_prop_line[0]<=np_s2_prop_pts[0] and  max_np_y1_prop_line[0]>=np_s2_prop_pts[0]) or (min_np_y1_prop_line[1]<=np_s2_prop_pts[1] and  max_np_y1_prop_line[1]>=np_s2_prop_pts[1]):

																		side2_data.append(round(np_s2_prop_point.distance(y1_prop_work_line),2))

																	else:

																		for s2_prop_line in s2prop_work_poly.virtual_entities():

																			if s2_prop_line.dxftype()=='LINE':

																				s2_start_prop_pts=[s2_prop_line.dxf.start[0],s2_prop_line.dxf.start[1]]

																				s2_end_prop_pts=[s2_prop_line.dxf.end[0],s2_prop_line.dxf.end[1]]

																				s2_prop_line=[s2_start_prop_pts,s2_end_prop_pts]

																				np_s2_prop_line=np.array(s2_prop_line).round(2)

																				s2_prop_linea=LineString(np_s2_prop_line)

																				max_np_s2_prop_line=np_s2_prop_line.max(axis=0).round(2)

																				min_np_s2_prop_line=np_s2_prop_line.min(axis=0).round(2)

																				for s2_prop_line_pts in np_prop_linex_y1:

																					np_s2_prop_line_pts=np.array(s2_prop_line_pts).round(2)

																					s2_prop_line_point=Point(np_s2_prop_line_pts)

																					if (min_np_s2_prop_line[0]<=np_s2_prop_line_pts[0] and  max_np_s2_prop_line[0]>=np_s2_prop_line_pts[0]) or (min_np_s2_prop_line[1]<=np_s2_prop_line_pts[1] and  max_np_s2_prop_line[1]>=np_s2_prop_line_pts[1]):

																						side2_data.append(round(s2_prop_line_point.distance(s2_prop_linea),2))

																			elif s2_prop_line.dxftype() == 'ARC':

																				s2_start_prop_pts = [
																					s2_prop_line.start_point[0],
																					s2_prop_line.start_point[1]]

																				s2_end_prop_pts = [
																					s2_prop_line.end_point[0],
																					s2_prop_line.end_point[1]]

																				s2_prop_line = [s2_start_prop_pts,
																								s2_end_prop_pts]

																				np_s2_prop_line = np.array(
																					s2_prop_line).round(2)

																				s2_prop_linea = LineString(
																					np_s2_prop_line)

																				max_np_s2_prop_line = np_s2_prop_line.max(
																					axis=0).round(2)

																				min_np_s2_prop_line = np_s2_prop_line.min(
																					axis=0).round(2)

																				for s2_prop_line_pts in np_prop_linex_y1:

																					np_s2_prop_line_pts = np.array(
																						s2_prop_line_pts).round(2)

																					s2_prop_line_point = Point(
																						np_s2_prop_line_pts)

																					if (min_np_s2_prop_line[0] <=
																						np_s2_prop_line_pts[0] and
																						max_np_s2_prop_line[0] >=
																						np_s2_prop_line_pts[0]) or (
																							min_np_s2_prop_line[1] <=
																							np_s2_prop_line_pts[1] and
																							max_np_s2_prop_line[1] >=
																							np_s2_prop_line_pts[1]):
																						side2_data.append(round(
																							s2_prop_line_point.distance(
																								s2_prop_linea), 2))
										#used for x axis equal data

										elif(np_prop_linex_y1[0,0]==np_prop_linex_y1[1,0]):

											for y1_s2_prop_line in lwpolyline.virtual_entities():

												if y1_s2_prop_line.dxftype()=='LINE':

													y1_s2_prop_start_pts=[y1_s2_prop_line.dxf.start[0],y1_s2_prop_line.dxf.start[1]]

													y1_s2_prop_end_pts=[y1_s2_prop_line.dxf.end[0],y1_s2_prop_line.dxf.end[1]]

													y1_prop_line=[y1_s2_prop_start_pts,y1_s2_prop_end_pts]

													np_y1_prop_line=np.array(y1_prop_line).round(2)

													if np_y1_prop_line[0,0]==np_prop_linex_y1[0,0] and np_y1_prop_line[1,0]==np_prop_linex_y1[1,0]:

														y1_prop_work_line=LineString(np_y1_prop_line)

														min_np_y1_prop_line=np_y1_prop_line.min(axis=0)

														max_np_y1_prop_line=np_y1_prop_line.max(axis=0)

														for organized_open_space_text in org_mtext:

															org_open_space = organized_open_space_text.dxf.text if organized_open_space_text.dxftype() == 'TEXT' else organized_open_space_text.plain_text()

															if org_open_space=='Tot-lot' or org_open_space=='Tot lot':

																organized_attrib=organized_open_space_text.dxfattribs()

																tot_lot_pts=organized_attrib['insert']

																np_tot_lot_pts=np.array([tot_lot_pts[0],tot_lot_pts[1]]).round(2)

																tot_lot_coords=Point(np_tot_lot_pts)

																for organized_open_space_poly in org_polygon:

																	organized_open_space_poly_pts=[y[0:2] for y in organized_open_space_poly.get_points()]

																	np_organized_open_space_poly_pts=np.array(organized_open_space_poly_pts).round(2)

																	organized_space_poly=Polygon(np_organized_open_space_poly_pts)

																	if organized_space_poly.contains(tot_lot_coords)==True:

																		for s2_tot_pts in np_organized_open_space_poly_pts:

																			np_s2_tot_pts=np.array(s2_tot_pts).round(2)

																			np_s2_tot_point=Point(np_s2_tot_pts)

																			if round(prop_poly1.distance(organized_space_poly))!=0:

																				if (min_np_y1_prop_line[0]<=np_s2_tot_pts[0] and  max_np_y1_prop_line[0]>=np_s2_tot_pts[0]) or (min_np_y1_prop_line[1]<=np_s2_tot_pts[1] and  max_np_y1_prop_line[1]>=np_s2_tot_pts[1]):

																					side2_data.append(round(np_s2_tot_point.distance(y1_prop_work_line),2))

																				else:

																					#tot lot polygon convert lines

																					for s2_tot_line in organized_open_space_poly.virtual_entities():

																						if s2_tot_line.dxftype()=='LINE':

																							s2_tot_start_pts=[s2_tot_line.dxf.start[0],s2_tot_line.dxf.start[1]]

																							s2_tot_end_pts=[s2_tot_line.dxf.end[0],s2_tot_line.dxf.end[1]]

																							s2_tot_line_pts=[s2_tot_start_pts,s2_tot_end_pts]

																							np_s2_tot_line_pts=np.array(s2_tot_line_pts).round(2)

																							max_np_s2_tot_line_pts=np_s2_tot_line_pts.max(axis=0)

																							min_np_s2_tot_line_pts=np_s2_tot_line_pts.min(axis=0)

																							s2_tot_line_point=LineString(np_s2_tot_line_pts)

																							# proposed work line convert into points

																							for s2_prop_work_pts in np_y1_prop_line:

																								np_s2_prop_work_pts=np.array(s2_prop_work_pts).round(2)

																								s2_prop_work_point=Point(np_s2_prop_work_pts)

																								#check condition tot_lot line incluide proposed work points or not

																								if (max_np_s2_tot_line_pts[0]>=np_s2_prop_work_pts[0] and min_np_s2_tot_line_pts[0]<=np_s2_prop_work_pts[0]) or (max_np_s2_tot_line_pts[1]>=np_s2_prop_work_pts[1] and min_np_s2_tot_line_pts[1]<=np_s2_prop_work_pts[1]):

																									side2_data.append(round(s2_prop_work_point.distance(s2_tot_line_point),2))

																						elif s2_tot_line.dxftype() == 'ARC':

																							s2_tot_start_pts = [
																								s2_tot_line.start_point[
																									0],
																								s2_tot_line.start_point[
																									1]]

																							s2_tot_end_pts = [
																								s2_tot_line.end_point[0],
																								s2_tot_line.end_point[1]]

																							s2_tot_line_pts = [
																								s2_tot_start_pts,
																								s2_tot_end_pts]

																							np_s2_tot_line_pts = np.array(
																								s2_tot_line_pts).round(
																								2)

																							max_np_s2_tot_line_pts = np_s2_tot_line_pts.max(
																								axis=0)

																							min_np_s2_tot_line_pts = np_s2_tot_line_pts.min(
																								axis=0)

																							s2_tot_line_point = LineString(
																								np_s2_tot_line_pts)

																							# proposed work line convert into points

																							for s2_prop_work_pts in np_y1_prop_line:

																								np_s2_prop_work_pts = np.array(
																									s2_prop_work_pts).round(
																									2)

																								s2_prop_work_point = Point(
																									np_s2_prop_work_pts)

																								# check condition tot_lot line incluide proposed work points or not

																								if (
																										max_np_s2_tot_line_pts[
																											0] >=
																										np_s2_prop_work_pts[
																											0] and
																										min_np_s2_tot_line_pts[
																											0] <=
																										np_s2_prop_work_pts[
																											0]) or (
																										max_np_s2_tot_line_pts[
																											1] >=
																										np_s2_prop_work_pts[
																											1] and
																										min_np_s2_tot_line_pts[
																											1] <=
																										np_s2_prop_work_pts[
																											1]):
																									side2_data.append(
																										round(
																											s2_prop_work_point.distance(
																												s2_tot_line_point),
																											2))
																			elif(round(prop_poly1.distance(organized_space_poly))==0):

																				side2_data.append(round(organized_space_poly.distance(s2_margin_linex_y1),2))

														#This loop for side2 line to prop_work block

														for s2prop_work_poly in proposed_polygon:

															s2prop_poly_pts=[d[0:2] for d in s2prop_work_poly.get_points()]

															np_s2prop_poly_pts=np.array(s2prop_poly_pts).round(2)

															s2prop_poly=Polygon(np_s2prop_poly_pts)

															for s2_prop_pts in np_s2prop_poly_pts:

																np_s2_prop_pts=np.array(s2_prop_pts).round(2)

																s2_prop_point=Point(np_s2_prop_pts)

																if round(prop_poly1.distance(s2prop_poly))!=0:

																	if (min_np_y1_prop_line[0]<=np_s2_prop_pts[0] and  max_np_y1_prop_line[0]>=np_s2_prop_pts[0]) or (min_np_y1_prop_line[1]<=np_s2_prop_pts[1] and  max_np_y1_prop_line[1]>=np_s2_prop_pts[1]):

																		side2_data.append(round(s2_prop_point.distance(y1_prop_work_line),2))

																	else:

																		for s2_prop_line in s2prop_work_poly.virtual_entities():

																			if s2_prop_line.dxftype()=='LINE':

																				s2_start_prop_pts=[s2_prop_line.dxf.start[0],s2_prop_line.dxf.start[1]]

																				s2_end_prop_pts=[s2_prop_line.dxf.end[0],s2_prop_line.dxf.end[1]]

																				s2_prop_line=[s2_start_prop_pts,s2_end_prop_pts]

																				np_s2_prop_line=np.array(s2_prop_line).round(2)

																				s2_prop_linea=LineString(np_s2_prop_line)

																				max_np_s2_prop_line=np_s2_prop_line.max(axis=0).round(2)

																				min_np_s2_prop_line=np_s2_prop_line.min(axis=0).round(2)

																				for s2_prop_line_pts in np_prop_linex_y1:

																					np_s2_prop_line_pts=np.array(s2_prop_line_pts).round(2)

																					s2_prop_line_point=Point(np_s2_prop_line_pts)

																					if (min_np_s2_prop_line[0]<=np_s2_prop_line_pts[0] and  max_np_s2_prop_line[0]>=np_s2_prop_line_pts[0]) or (min_np_s2_prop_line[1]<=np_s2_prop_line_pts[1] and  max_np_s2_prop_line[1]>=np_s2_prop_line_pts[1]):

																						side2_data.append(round(s2_prop_line_point.distance(s2_prop_linea),2))

																			elif s2_prop_line.dxftype() == 'ARC':

																				s2_start_prop_pts = [
																					s2_prop_line.start_point[0],
																					s2_prop_line.start_point[1]]

																				s2_end_prop_pts = [
																					s2_prop_line.end_point[0],
																					s2_prop_line.end_point[1]]

																				s2_prop_line = [s2_start_prop_pts,
																								s2_end_prop_pts]

																				np_s2_prop_line = np.array(
																					s2_prop_line).round(2)

																				s2_prop_linea = LineString(
																					np_s2_prop_line)

																				max_np_s2_prop_line = np_s2_prop_line.max(
																					axis=0).round(2)

																				min_np_s2_prop_line = np_s2_prop_line.min(
																					axis=0).round(2)

																				for s2_prop_line_pts in np_prop_linex_y1:

																					np_s2_prop_line_pts = np.array(
																						s2_prop_line_pts).round(2)

																					s2_prop_line_point = Point(
																						np_s2_prop_line_pts)

																					if (min_np_s2_prop_line[0] <=
																						np_s2_prop_line_pts[0] and
																						max_np_s2_prop_line[0] >=
																						np_s2_prop_line_pts[0]) or (
																							min_np_s2_prop_line[1] <=
																							np_s2_prop_line_pts[1] and
																							max_np_s2_prop_line[1] >=
																							np_s2_prop_line_pts[1]):
																						side2_data.append(round(
																							s2_prop_line_point.distance(
																								s2_prop_linea), 2))

												elif y1_s2_prop_line.dxftype() == 'ARC':

													y1_s2_prop_start_pts = [y1_s2_prop_line.start_point[0],
																			y1_s2_prop_line.start_point[1]]

													y1_s2_prop_end_pts = [y1_s2_prop_line.end_point[0],
																		  y1_s2_prop_line.end_point[1]]

													y1_prop_line = [y1_s2_prop_start_pts, y1_s2_prop_end_pts]

													np_y1_prop_line = np.array(y1_prop_line).round(2)

													if np_y1_prop_line[0, 0] == np_prop_linex_y1[0, 0] and \
															np_y1_prop_line[1, 0] == np_prop_linex_y1[1, 0]:

														y1_prop_work_line = LineString(np_y1_prop_line)

														min_np_y1_prop_line = np_y1_prop_line.min(axis=0)

														max_np_y1_prop_line = np_y1_prop_line.max(axis=0)

														for organized_open_space_text in org_mtext:

															org_open_space = organized_open_space_text.dxf.text if organized_open_space_text.dxftype() == 'TEXT' else organized_open_space_text.plain_text()

															if org_open_space == 'Tot-lot' or org_open_space == 'Tot lot':

																organized_attrib = organized_open_space_text.dxfattribs()

																tot_lot_pts = organized_attrib['insert']

																np_tot_lot_pts = np.array(
																	[tot_lot_pts[0], tot_lot_pts[1]]).round(2)

																tot_lot_coords = Point(np_tot_lot_pts)

																for organized_open_space_poly in org_polygon:

																	organized_open_space_poly_pts = [y[0:2] for y in
																									 organized_open_space_poly.get_points()]

																	np_organized_open_space_poly_pts = np.array(
																		organized_open_space_poly_pts).round(2)

																	organized_space_poly = Polygon(
																		np_organized_open_space_poly_pts)

																	if organized_space_poly.contains(
																			tot_lot_coords) == True:

																		for s2_tot_pts in np_organized_open_space_poly_pts:

																			np_s2_tot_pts = np.array(s2_tot_pts).round(
																				2)

																			np_s2_tot_point = Point(np_s2_tot_pts)

																			if round(prop_poly1.distance(
																					organized_space_poly)) != 0:

																				if (min_np_y1_prop_line[0] <=
																					np_s2_tot_pts[0] and
																					max_np_y1_prop_line[0] >=
																					np_s2_tot_pts[0]) or (
																						min_np_y1_prop_line[1] <=
																						np_s2_tot_pts[1] and
																						max_np_y1_prop_line[1] >=
																						np_s2_tot_pts[1]):

																					side2_data.append(round(
																						np_s2_tot_point.distance(
																							y1_prop_work_line), 2))

																				else:

																					# tot lot polygon convert lines

																					for s2_tot_line in organized_open_space_poly.virtual_entities():

																						if s2_tot_line.dxftype() == 'LINE':

																							s2_tot_start_pts = [
																								s2_tot_line.dxf.start[
																									0],
																								s2_tot_line.dxf.start[
																									1]]

																							s2_tot_end_pts = [
																								s2_tot_line.dxf.end[0],
																								s2_tot_line.dxf.end[1]]

																							s2_tot_line_pts = [
																								s2_tot_start_pts,
																								s2_tot_end_pts]

																							np_s2_tot_line_pts = np.array(
																								s2_tot_line_pts).round(
																								2)

																							max_np_s2_tot_line_pts = np_s2_tot_line_pts.max(
																								axis=0)

																							min_np_s2_tot_line_pts = np_s2_tot_line_pts.min(
																								axis=0)

																							s2_tot_line_point = LineString(
																								np_s2_tot_line_pts)

																							# proposed work line convert into points

																							for s2_prop_work_pts in np_y1_prop_line:

																								np_s2_prop_work_pts = np.array(
																									s2_prop_work_pts).round(
																									2)

																								s2_prop_work_point = Point(
																									np_s2_prop_work_pts)

																								# check condition tot_lot line incluide proposed work points or not

																								if (
																										max_np_s2_tot_line_pts[
																											0] >=
																										np_s2_prop_work_pts[
																											0] and
																										min_np_s2_tot_line_pts[
																											0] <=
																										np_s2_prop_work_pts[
																											0]) or (
																										max_np_s2_tot_line_pts[
																											1] >=
																										np_s2_prop_work_pts[
																											1] and
																										min_np_s2_tot_line_pts[
																											1] <=
																										np_s2_prop_work_pts[
																											1]):
																									side2_data.append(
																										round(
																											s2_prop_work_point.distance(
																												s2_tot_line_point),
																											2))

																						elif s2_tot_line.dxftype() == 'ARC':

																							s2_tot_start_pts = [
																								s2_tot_line.start_point[
																									0],
																								s2_tot_line.start_point[
																									1]]

																							s2_tot_end_pts = [
																								s2_tot_line.end_point[
																									0],
																								s2_tot_line.end_point[
																									1]]

																							s2_tot_line_pts = [
																								s2_tot_start_pts,
																								s2_tot_end_pts]

																							np_s2_tot_line_pts = np.array(
																								s2_tot_line_pts).round(
																								2)

																							max_np_s2_tot_line_pts = np_s2_tot_line_pts.max(
																								axis=0)

																							min_np_s2_tot_line_pts = np_s2_tot_line_pts.min(
																								axis=0)

																							s2_tot_line_point = LineString(
																								np_s2_tot_line_pts)

																							# proposed work line convert into points

																							for s2_prop_work_pts in np_y1_prop_line:

																								np_s2_prop_work_pts = np.array(
																									s2_prop_work_pts).round(
																									2)

																								s2_prop_work_point = Point(
																									np_s2_prop_work_pts)

																								# check condition tot_lot line incluide proposed work points or not

																								if (
																										max_np_s2_tot_line_pts[
																											0] >=
																										np_s2_prop_work_pts[
																											0] and
																										min_np_s2_tot_line_pts[
																											0] <=
																										np_s2_prop_work_pts[
																											0]) or (
																										max_np_s2_tot_line_pts[
																											1] >=
																										np_s2_prop_work_pts[
																											1] and
																										min_np_s2_tot_line_pts[
																											1] <=
																										np_s2_prop_work_pts[
																											1]):
																									side2_data.append(
																										round(
																											s2_prop_work_point.distance(
																												s2_tot_line_point),
																											2))
																			elif (round(prop_poly1.distance(
																					organized_space_poly)) == 0):

																				side2_data.append(round(
																					organized_space_poly.distance(
																						s2_margin_linex_y1), 2))

														# This loop for side2 line to prop_work block

														for s2prop_work_poly in proposed_polygon:

															s2prop_poly_pts = [d[0:2] for d in
																			   s2prop_work_poly.get_points()]

															np_s2prop_poly_pts = np.array(s2prop_poly_pts).round(2)

															s2prop_poly = Polygon(np_s2prop_poly_pts)

															for s2_prop_pts in np_s2prop_poly_pts:

																np_s2_prop_pts = np.array(s2_prop_pts).round(2)

																s2_prop_point = Point(np_s2_prop_pts)

																if round(prop_poly1.distance(s2prop_poly)) != 0:

																	if (min_np_y1_prop_line[0] <= np_s2_prop_pts[0] and
																		max_np_y1_prop_line[0] >= np_s2_prop_pts[
																			0]) or (
																			min_np_y1_prop_line[1] <= np_s2_prop_pts[
																		1] and max_np_y1_prop_line[1] >= np_s2_prop_pts[
																				1]):

																		side2_data.append(round(
																			s2_prop_point.distance(y1_prop_work_line),
																			2))

																	else:

																		for s2_prop_line in s2prop_work_poly.virtual_entities():

																			if s2_prop_line.dxftype()=='LINE':

																				s2_start_prop_pts = [
																					s2_prop_line.dxf.start[0],
																					s2_prop_line.dxf.start[1]]

																				s2_end_prop_pts = [s2_prop_line.dxf.end[0],
																								   s2_prop_line.dxf.end[1]]

																				s2_prop_line = [s2_start_prop_pts,
																								s2_end_prop_pts]

																				np_s2_prop_line = np.array(
																					s2_prop_line).round(2)

																				s2_prop_linea = LineString(np_s2_prop_line)

																				max_np_s2_prop_line = np_s2_prop_line.max(
																					axis=0).round(2)

																				min_np_s2_prop_line = np_s2_prop_line.min(
																					axis=0).round(2)

																				for s2_prop_line_pts in np_prop_linex_y1:

																					np_s2_prop_line_pts = np.array(
																						s2_prop_line_pts).round(2)

																					s2_prop_line_point = Point(
																						np_s2_prop_line_pts)

																					if (min_np_s2_prop_line[0] <=
																						np_s2_prop_line_pts[0] and
																						max_np_s2_prop_line[0] >=
																						np_s2_prop_line_pts[0]) or (
																							min_np_s2_prop_line[1] <=
																							np_s2_prop_line_pts[1] and
																							max_np_s2_prop_line[1] >=
																							np_s2_prop_line_pts[1]):
																						side2_data.append(round(
																							s2_prop_line_point.distance(
																								s2_prop_linea), 2))
																			elif s2_prop_line.dxftype() == 'ARC':

																				s2_start_prop_pts = [
																					s2_prop_line.start_point[0],
																					s2_prop_line.start_point[1]]

																				s2_end_prop_pts = [
																					s2_prop_line.end_point[0],
																					s2_prop_line.end_point[1]]

																				s2_prop_line = [s2_start_prop_pts,
																								s2_end_prop_pts]

																				np_s2_prop_line = np.array(
																					s2_prop_line).round(2)

																				s2_prop_linea = LineString(
																					np_s2_prop_line)

																				max_np_s2_prop_line = np_s2_prop_line.max(
																					axis=0).round(2)

																				min_np_s2_prop_line = np_s2_prop_line.min(
																					axis=0).round(2)

																				for s2_prop_line_pts in np_prop_linex_y1:

																					np_s2_prop_line_pts = np.array(
																						s2_prop_line_pts).round(2)

																					s2_prop_line_point = Point(
																						np_s2_prop_line_pts)

																					if (min_np_s2_prop_line[0] <=
																						np_s2_prop_line_pts[0] and
																						max_np_s2_prop_line[0] >=
																						np_s2_prop_line_pts[0]) or (
																							min_np_s2_prop_line[1] <=
																							np_s2_prop_line_pts[1] and
																							max_np_s2_prop_line[1] >=
																							np_s2_prop_line_pts[1]):
																						side2_data.append(round(
																							s2_prop_line_point.distance(
																								s2_prop_linea), 2))
					#info_data=[]

					tmpPropWorkDict=dict()

					tmpPropWorkDict['NAME']=prop_text_name

					if front_data is not None and len(front_data)>0:

						tmpPropWorkDict['FRONT']=min(front_data)

						#info_data.append(f'Front,{min(front_data)}')

					if rear_data is not None  and len(rear_data)>0:

						tmpPropWorkDict['REAR']=min(rear_data)

						#info_data.append(f'Rear,{min(rear_data)}')

					if side1_data is not None  and len(side1_data)>0:

						tmpPropWorkDict['SIDE1']=min(side1_data)

						#info_data.append(f'Side1,{min(side1_data)}')

					if side2_data is not None and len(side2_data)>0:

						tmpPropWorkDict['SIDE2']=min(side2_data)

						#info_data.append(f'Side2,{min(side2_data)}')

					#main_data=f'{name.dxf.text},{info_data}'

					#print ('refid ', refid)

					returnValueDict[refid]=tmpPropWorkDict

					#resultsList.append(main_data)

	except IndexError:

		get_current_logger().error('Didn"t have name of value')

		return returnValueDict

	except IOError:

		get_current_logger().error(f'Not a DXF file or a generic I/O error.')

		return returnValueDict

	except ezdxf.DXFStructureError:

		get_current_logger().error(f'Invalid or corrupted DXF file.')

		return returnValueDict

	return returnValueDict

def splitLines(start,end,seg):  # this function used for Spliting the lines

	x_delta=(end[0]-start[0])/float(seg)

	y_delta=(end[1]-start[1])/float(seg)

	points=[]

	for i in range(1,seg):

		pts=[start[0]+i*x_delta,start[1]+i*y_delta]

		points.append(pts)

	return [start]+points+[end]

def getSetBacksByMidPointsMarginLineNew(modelspace):

	resultsList=[]
	returnValueDict=dict()

	if (modelspace is None):

		return returnValueDict

	#dxf_path=os.path.join(folder,filename)
	#print('file is ', dxf_path)

	try:

		#read_dxf=ezdxf.readfile(dxf_path)

		#print('read file')

		msp=modelspace

		proposed_work_text=msp.query("TEXT MTEXT[layer=='_ProposedWork']")

		proposed_work_polygon=msp.query("LWPOLYLINE[layer=='_ProposedWork']")

		Margin_data=msp.query("*[layer=='_MarginLine']")

		org_mtext=msp.query('MTEXT[layer=="_OrganizedOpenSpace"]')

		org_polygon=msp.query('LWPOLYLINE[layer=="_OrganizedOpenSpace"]')

		for text in proposed_work_text:

			text_attribs=text.dxfattribs()

			text_name=text.dxf.text if text.dxftype()=='TEXT' else text.plain_text()

			text_insert_pts=text_attribs.get('insert')

			text_Point=Point([text_insert_pts[0],text_insert_pts[1]])

			for lwpolyline in proposed_work_polygon:

				prop_pts=[x[0:2] for x in lwpolyline.get_points()]

				np_prop_pts=np.array(prop_pts).round(2)

				prop_poly1=Polygon(np_prop_pts)

				if prop_poly1.contains(text_Point)==True or prop_poly1.touches(text_Point)==True or round(prop_poly1.distance(text_Point),1)==0.0:

					refid=lwpolyline.dxf.handle

					front_data=[]

					rear_data=[]

					side1_data=[]

					side2_data=[]

					front_coordinate_data=[]

					rear_coordinate_data=[]

					side1_coordinate_data=[]

					side2_coordinate_data=[]

					for tpl in lwpolyline.virtual_entities():

						#print (' tpl is ', type(tpl), ' object value  ', str(tpl))

						#LINE INPUT

						if tpl.dxftype()=='LINE':

							start_pts=tpl.dxf.start

							end_pts=tpl.dxf.end

							linex=[[start_pts[0],start_pts[1]],[end_pts[0],end_pts[1]]]

							np_linex=np.array(linex).round(2)

							min_np_linex=np_linex.min(axis=0)

							#split_prop_line=split(linex[0],linex[1],2)

							prop_line=LineString(np_linex)

							#Margin line distances to the proposedwork
							for entity in Margin_data:

								lstf=[]

								lstr=[]

								lsts1=[]

								lsts2=[]

								if entity.dxftype()=='INSERT':

									for x in entity.virtual_entities():

										if x.dxftype()=='LINE':

											if x.dxf.color==1:

												v1=x.dxf.start

												va=[v1[0],v1[1]]

												v2=x.dxf.end

												vb=[v2[0],v2[1]]

												lst=np.array([va,vb])

												margin_linef=LineString(lst)

												if round(prop_line.distance(margin_linef), 1)!=0.0:

													lstf.append(round(prop_line.distance(margin_linef),2))

													front_coordinate_data.append([linex,lst])

											elif(x.dxf.color== 6):

												v1=x.dxf.start

												va=(v1[0],v1[1])

												v2=x.dxf.end

												vb=(v2[0],v2[1])

												lst=[va,vb]

												margin_liner=LineString(lst)

												if round(prop_line.distance(margin_liner),1)!=0.0:

													lstr.append(round(prop_line.distance(margin_liner),2))

													rear_coordinate_data.append([linex,lst])

											elif(x.dxf.color==5):

												v1=x.dxf.start

												va=(v1[0],v1[1])

												v2=x.dxf.end

												vb=(v2[0],v2[1])

												lst=[va,vb]

												margin_lines1=LineString(lst)

												if round(prop_line.distance(margin_lines1),1)!=0.0:

													lsts1.append(round(prop_line.distance(margin_lines1),2))

													side1_coordinate_data.append([linex,lst])

											elif(x.dxf.color==104 or x.dxf.color==3 ):

												v1=x.dxf.start

												va=(v1[0],v1[1])

												v2=x.dxf.end

												vb=(v2[0],v2[1])

												lst=[va,vb]

												margin_lines2=LineString(lst)

												if round(prop_line.distance(margin_lines2),1)!=0.0:

													lsts2.append(round(prop_line.distance(margin_lines2),2))

													side2_coordinate_data.append([linex,lst])

										elif(x.dxftype()=='ARC'):

											if x.dxf.color==1:

												v1=x.start_point

												va=[v1[0],v1[1]]

												v2=x.end_point

												vb=[v2[0],v2[1]]

												lst=np.array([va,vb])

												margin_linef=LineString(lst)

												if round(prop_line.distance(margin_linef), 1)!=0.0:

													lstf.append(round(prop_line.distance(margin_linef),2))

													front_coordinate_data.append([linex,lst])

											elif(x.dxf.color== 6):

												v1=x.start_point

												va=(v1[0],v1[1])

												v2=x.end_point

												vb=(v2[0],v2[1])

												lst=[va,vb]

												margin_liner=LineString(lst)

												if round(prop_line.distance(margin_liner),1)!=0.0:

													lstr.append(round(prop_line.distance(margin_liner),2))

													rear_coordinate_data.append([linex,lst])

											elif(x.dxf.color==5):

												v1=x.start_point

												va=(v1[0],v1[1])

												v2=x.end_point

												vb=(v2[0],v2[1])

												lst=[va,vb]

												margin_lines1=LineString(lst)

												if round(prop_line.distance(margin_lines1), 1)!=0.0:

													lsts1.append(round(prop_line.distance(margin_lines1),2))

													side1_coordinate_data.append([linex,lst])

											elif(x.dxf.color==104 or x.dxf.color==3):

												v1=x.start_point

												va=(v1[0],v1[1])

												v2=x.end_point

												vb=(v2[0],v2[1])

												lst=[va,vb]

												margin_lines2=LineString(lst)

												if round(prop_line.distance(margin_lines2),1)!=0.0:

													lsts2.append(round(prop_line.distance(margin_lines2),2))

													side2_coordinate_data.append([linex,lst])

								elif(entity.dxftype()=='LINE'):

									if entity.dxf.color == 1:

										v1 = entity.dxf.start

										va = [v1[0], v1[1]]

										v2 = entity.dxf.end

										vb = [v2[0], v2[1]]

										lst = np.array([va, vb])

										margin_linef = LineString(lst)

										if round(prop_line.distance(margin_linef), 1)!=0.0:

											lstf.append(round(prop_line.distance(margin_linef), 2))

											front_coordinate_data.append([linex, lst])

									elif (entity.dxf.color == 6):

										v1 = entity.dxf.start

										va = (v1[0], v1[1])

										v2 = entity.dxf.end

										vb = (v2[0], v2[1])

										lst = [va, vb]

										margin_liner = LineString(lst)

										if round(prop_line.distance(margin_liner), 1)!=0.0:

											lstr.append(round(prop_line.distance(margin_liner), 2))

											rear_coordinate_data.append([linex, lst])

									elif (entity.dxf.color == 5):

										v1 = entity.dxf.start

										va = (v1[0], v1[1])

										v2 = entity.dxf.end

										vb = (v2[0], v2[1])

										lst = [va, vb]

										margin_lines1 = LineString(lst)

										if round(prop_line.distance(margin_lines1), 1)!=0.0:

											lsts1.append(round(prop_line.distance(margin_lines1), 2))

											side1_coordinate_data.append([linex, lst])

									elif (entity.dxf.color == 104 or entity.dxf.color ==3):

										v1 = entity.dxf.start

										va = (v1[0], v1[1])

										v2 = entity.dxf.end

										vb = (v2[0], v2[1])

										lst = [va, vb]

										margin_lines2 = LineString(lst)

										if round(prop_line.distance(margin_lines2), 1)!=0.0:

											lsts2.append(round(prop_line.distance(margin_lines2), 2))

											side2_coordinate_data.append([linex, lst])

								elif (entity.dxftype() =='ARC'):

									if entity.dxf.color == 1:

										v1 = entity.start_point

										va = [v1[0], v1[1]]

										v2 = entity.end_point

										vb = [v2[0], v2[1]]

										lst = np.array([va, vb])

										margin_linef = LineString(lst)

										if round(prop_line.distance(margin_linef), 1)!=0.0:

											lstf.append(round(prop_line.distance(margin_linef), 2))

											front_coordinate_data.append([linex, lst])

									elif (entity.dxf.color == 6):

										v1 = entity.start_point

										va = (v1[0], v1[1])

										v2 = entity.end_point

										vb = (v2[0], v2[1])

										lst = [va, vb]

										margin_liner = LineString(lst)

										if round(prop_line.distance(margin_liner), 1)!=0.0:

											lstr.append(round(prop_line.distance(margin_liner), 2))

											rear_coordinate_data.append([linex, lst])

									elif (entity.dxf.color == 5):

										v1 = entity.start_point

										va = (v1[0], v1[1])

										v2 = entity.end_point

										vb = (v2[0], v2[1])

										lst = [va, vb]

										margin_lines1 = LineString(lst)

										if round(prop_line.distance(margin_lines1), 1)!=0.0:

											lsts1.append(round(prop_line.distance(margin_lines1), 2))

											side1_coordinate_data.append([linex, lst])

									elif (entity.dxf.color == 104 or entity.dxf.color ==3):

										v1 = entity.start_point

										va = (v1[0], v1[1])

										v2 = entity.end_point

										vb = (v2[0], v2[1])

										lst = [va, vb]

										margin_lines2 = LineString(lst)

										if round(prop_line.distance(margin_lines2), 1)!=0.0:

											lsts2.append(round(prop_line.distance(margin_lines2), 2))

											side2_coordinate_data.append([linex, lst])



								if lstf!=[]:

									front_data.append(min(lstf))

								if lstr!=[]:

									rear_data.append(min(lstr))

								if lsts1!=[]:

									side1_data.append(min(lsts1))

								if lsts2!=[]:

									side2_data.append(min(lsts2))

						# ARC INPUT
						elif tpl.dxftype()=='ARC':

							start_pts = tpl.start_point

							end_pts = tpl.end_point

							arcx = [[start_pts[0], start_pts[1]], [end_pts[0], end_pts[1]]]

							np_arcx = np.array(arcx).round(2)

							prop_arc=LineString(np_arcx)
							# Margin line distances to the proposedwork

							for entity1 in Margin_data:

								lstf = []

								lstr = []

								lsts1 = []

								lsts2 = []

								if entity1.dxftype()=='INSERT':

									for x in entity1.virtual_entities():

										if x.dxftype()=='LINE':

											if x.dxf.color == 1:

												v1 = x.dxf.start

												va = [v1[0], v1[1]]

												v2 = x.dxf.end

												vb = [v2[0], v2[1]]

												lst = np.array([va, vb])

												margin_linef = LineString(lst)

												if round(prop_arc.distance(margin_linef), 1)!=0.0:

													lstf.append(round(prop_arc.distance(margin_linef), 2))

													front_coordinate_data.append([arcx, lst])

											elif (x.dxf.color == 6):

												v1 = x.dxf.start

												va = (v1[0], v1[1])

												v2 = x.dxf.end

												vb = (v2[0], v2[1])

												lst = [va, vb]

												margin_liner = LineString(lst)

												if round(prop_arc.distance(margin_liner), 1)!=0.0:

													lstr.append(round(prop_arc.distance(margin_liner), 2))

													rear_coordinate_data.append([arcx, lst])

											elif (x.dxf.color == 5):

												v1 = x.dxf.start

												va = (v1[0], v1[1])

												v2 = x.dxf.end

												vb = (v2[0], v2[1])

												lst = [va, vb]

												margin_lines1 = LineString(lst)

												if round(prop_arc.distance(margin_lines1), 1)!=0.0:

													lsts1.append(round(prop_arc.distance(margin_lines1), 2))

													side1_coordinate_data.append([arcx, lst])

											elif (x.dxf.color == 104 or x.dxf.color == 3):

												v1 = x.dxf.start

												va = (v1[0], v1[1])

												v2 = x.dxf.end

												vb = (v2[0], v2[1])

												lst = [va, vb]

												margin_lines2 = LineString(lst)

												if round(prop_arc.distance(margin_lines2), 1)!=0.0:

													lsts2.append(round(prop_arc.distance(margin_lines2), 2))

													side2_coordinate_data.append([arcx, lst])

										elif(x.dxftype()=='ARC'):

											if x.dxf.color == 1:

												v1 = x.start_point

												va = [v1[0], v1[1]]

												v2 = x.end_point

												vb = [v2[0], v2[1]]

												lst = np.array([va, vb])

												margin_linef = LineString(lst)

												if round(prop_arc.distance(margin_linef), 1)!=0.0:

													lstf.append(round(prop_arc.distance(margin_linef), 2))

													front_coordinate_data.append([arcx, lst])

											elif (x.dxf.color == 6):

												v1 = x.start_point

												va = (v1[0], v1[1])

												v2 = x.end_point

												vb = (v2[0], v2[1])

												lst = [va, vb]

												margin_liner = LineString(lst)

												if round(prop_arc.distance(margin_liner), 1)!=0.0:

													lstr.append(round(prop_arc.distance(margin_liner), 2))

													rear_coordinate_data.append([arcx, lst])

											elif (x.dxf.color == 5):

												v1 = x.start_point

												va = (v1[0], v1[1])

												v2 = x.end_point

												vb = (v2[0], v2[1])

												lst = [va, vb]

												margin_lines1 = LineString(lst)

												if round(prop_arc.distance(margin_lines1), 1)!=0.0:

													lsts1.append(round(prop_arc.distance(margin_lines1), 2))

													side1_coordinate_data.append([arcx, lst])

											elif (x.dxf.color == 104 or x.dxf.color == 3):

												v1 = x.start_point

												va = (v1[0], v1[1])

												v2 = x.end_point

												vb = (v2[0], v2[1])

												lst = [va, vb]

												margin_lines2 = LineString(lst)

												if round(prop_arc.distance(margin_lines2), 1)!=0.0:

													lsts2.append(round(prop_arc.distance(margin_lines2), 2))

													side2_coordinate_data.append([arcx, lst])

								elif(entity1.dxftype()=='LINE'):

									if entity1.dxf.color == 1:

										v1 = entity1.dxf.start

										va = [v1[0], v1[1]]

										v2 = entity1.dxf.end

										vb = [v2[0], v2[1]]

										lst = np.array([va, vb])

										margin_linef = LineString(lst)

										if round(prop_arc.distance(margin_linef), 1) != 0.0:

											lstf.append(round(prop_arc.distance(margin_linef), 2))

											front_coordinate_data.append([arcx, lst])

									elif (entity1.dxf.color == 6):

										v1 = entity1.dxf.start

										va = (v1[0], v1[1])

										v2 = entity1.dxf.end

										vb = (v2[0], v2[1])

										lst = [va, vb]

										margin_liner = LineString(lst)

										if round(prop_arc.distance(margin_liner), 1) != 0.0:

											lstr.append(round(prop_arc.distance(margin_liner), 2))

											rear_coordinate_data.append([arcx, lst])

									elif (entity1.dxf.color == 5):

										v1 = entity1.dxf.start

										va = (v1[0], v1[1])

										v2 = entity1.dxf.end

										vb = (v2[0], v2[1])

										lst = [va, vb]

										margin_lines1 = LineString(lst)

										if round(prop_arc.distance(margin_lines1), 1) != 0.0:

											lsts1.append(round(prop_arc.distance(margin_lines1), 2))

											side1_coordinate_data.append([arcx, lst])

									elif (entity1.dxf.color == 104 or entity1.dxf.color == 3):

										v1 = entity1.dxf.start

										va = (v1[0], v1[1])

										v2 = entity1.dxf.end

										vb = (v2[0], v2[1])

										lst = [va, vb]

										margin_lines2 = LineString(lst)

										if round(prop_arc.distance(margin_lines2), 1) != 0.0:

											lsts2.append(round(prop_arc.distance(margin_lines2), 2))

											side2_coordinate_data.append([arcx, lst])

								elif (entity1.dxftype() == 'ARC'):

									if entity1.dxf.color == 1:

										v1 = entity1.start_point

										va = [v1[0], v1[1]]

										v2 = entity1.end_point

										vb = [v2[0], v2[1]]

										lst = np.array([va, vb])

										margin_linef = LineString(lst)

										if round(prop_arc.distance(margin_linef), 1) != 0.0:

											lstf.append(round(prop_arc.distance(margin_linef), 2))

											front_coordinate_data.append([arcx, lst])

									elif (entity1.dxf.color == 6):

										v1 = entity1.start_point

										va = (v1[0], v1[1])

										v2 = entity1.end_point

										vb = (v2[0], v2[1])

										lst = [va, vb]

										margin_liner = LineString(lst)

										if round(prop_arc.distance(margin_liner), 1) != 0.0:

											lstr.append(round(prop_arc.distance(margin_liner), 2))

											rear_coordinate_data.append([arcx, lst])

									elif (entity1.dxf.color == 5):

										v1 = entity1.start_point

										va = (v1[0], v1[1])

										v2 = entity1.end_point

										vb = (v2[0], v2[1])

										lst = [va, vb]

										margin_lines1 = LineString(lst)

										if round(prop_arc.distance(margin_lines1), 1) != 0.0:

											lsts1.append(round(prop_arc.distance(margin_lines1), 2))

											side1_coordinate_data.append([arcx, lst])

									elif (entity1.dxf.color == 104 or entity1.dxf.color == 3):

										v1 = entity1.start_point

										va = (v1[0], v1[1])

										v2 = entity1.end_point

										vb = (v2[0], v2[1])

										lst = [va, vb]

										margin_lines2 = LineString(lst)

										if round(prop_arc.distance(margin_lines2), 1) != 0.0:

											lsts2.append(round(prop_arc.distance(margin_lines2), 2))

											side2_coordinate_data.append([arcx, lst])

								if lstf != []:

									front_data.append(min(lstf))

								if lstr != []:

									rear_data.append(min(lstr))

								if lsts1 != []:

									side1_data.append(min(lsts1))

								if lsts2 != []:

									side2_data.append(min(lsts2))

					fline_pts_value=[]

					fline_pts=[]
					#Front coords data

					for fdata in front_coordinate_data:

						f_prop_linex=LineString(fdata[0])

						f_margin_linex=LineString(fdata[1])

						if round(f_prop_linex.distance(f_margin_linex),2)==min(front_data):

							f_np_prop_linex=np.array(fdata[0]).round(2)

							prop_line_splitf=splitLines(f_np_prop_linex[0],f_np_prop_linex[1],4)

							for prop_splitf_pts in prop_line_splitf[1:-1]:

								np_prop_splitf_pts=np.array(prop_splitf_pts).round(2)

								prop_splitf_point=Point(np_prop_splitf_pts)

								fline_pts_value.append(round(prop_splitf_point.distance(f_margin_linex),2))

								fline_pts.append(np_prop_splitf_pts)

					for fdata_x in front_coordinate_data:

						f_prop_linex_x=LineString(fdata_x[0])

						f_margin_linex_x=LineString(fdata_x[1])

						if round(f_prop_linex_x.distance(f_margin_linex_x),2)==min(front_data):

							np_prop_linex_x=np.array(fdata_x[0]).round(2)

							max_prop_linex_x=np_prop_linex_x.max(axis=0).round(2)

							min_prop_linex_x=np_prop_linex_x.min(axis=0).round(2)

							for x_fline_pts in fline_pts:

								np_x_fline_pts=np.array(x_fline_pts).round(2)

								x_fline_point=Point(np_x_fline_pts)

								if ((max_prop_linex_x[0]>=np_x_fline_pts[0] and min_prop_linex_x[0]<=np_x_fline_pts[0]) and (max_prop_linex_x[1]>=np_x_fline_pts[1] and min_prop_linex_x[1]<=np_x_fline_pts[1]))==True:

									if round(x_fline_point.distance(f_margin_linex_x),2)==min(fline_pts_value):

										# used for y axis equal

										if np_prop_linex_x[0,1]==np_prop_linex_x[1,1]:

											for x_f_prop_line in lwpolyline.virtual_entities():

												if x_f_prop_line.dxftype()=='LINE':

													x_f_prop_start_pts=[x_f_prop_line.dxf.start[0],x_f_prop_line.dxf.start[1]]

													x_f_prop_end_pts=[x_f_prop_line.dxf.end[0],x_f_prop_line.dxf.end[1]]

													x_prop_line=[x_f_prop_start_pts,x_f_prop_end_pts]

													np_x_prop_line=np.array(x_prop_line).round(2)

													if np_x_prop_line[0,1]==np_prop_linex_x[0,1] and np_x_prop_line[1,1]==np_prop_linex_x[1,1]:

														x_prop_work_line=LineString(np_x_prop_line)

														min_np_x_prop_line=np_x_prop_line.min(axis=0)

														max_np_x_prop_line=np_x_prop_line.max(axis=0)

														for organized_open_space_text in org_mtext:

															if organized_open_space_text.text=='Tot-lot':

																organized_attrib=organized_open_space_text.dxfattribs()

																tot_lot_pts=organized_attrib['insert']

																np_tot_lot_pts=np.array([tot_lot_pts[0],tot_lot_pts[1]]).round(2)

																tot_lot_coords=Point(np_tot_lot_pts)

																for organized_open_space_poly in org_polygon:

																	organized_open_space_poly_pts=[y[0:2] for y in organized_open_space_poly.get_points()]

																	np_organized_open_space_poly_pts=np.array(organized_open_space_poly_pts).round(2)

																	organized_space_poly=Polygon(np_organized_open_space_poly_pts)

																	if organized_space_poly.contains(tot_lot_coords)==True:

																		for f_tot_pts in np_organized_open_space_poly_pts:

																			np_f_tot_pts=np.array(f_tot_pts).round(2)

																			np_f_tot_point=Point(np_f_tot_pts)

																			if round(prop_poly1.distance(organized_space_poly))!=0:

																				if (min_np_x_prop_line[0]<=np_f_tot_pts[0] and  max_np_x_prop_line[0]>=np_f_tot_pts[0]) or (min_np_x_prop_line[1]<=np_f_tot_pts[1] and  max_np_x_prop_line[1]>=np_f_tot_pts[1]):

																					front_data.append(round(np_f_tot_point.distance(x_prop_work_line),2))
												elif(x_f_prop_line.dxftype()=='ARC'):

													x_f_prop_start_pts = [x_f_prop_line.start_point[0],x_f_prop_line.start_point[1]]

													x_f_prop_end_pts = [x_f_prop_line.end_point[0],x_f_prop_line.end_point[1]]

													x_prop_line = [x_f_prop_start_pts, x_f_prop_end_pts]

													np_x_prop_line = np.array(x_prop_line).round(2)

													if np_x_prop_line[0, 1] == np_prop_linex_x[0, 1] and np_x_prop_line[1, 1] == np_prop_linex_x[1, 1]:

														x_prop_work_line = LineString(np_x_prop_line)

														min_np_x_prop_line = np_x_prop_line.min(axis=0)

														max_np_x_prop_line = np_x_prop_line.max(axis=0)

														for organized_open_space_text in org_mtext:

															if organized_open_space_text.text == 'Tot-lot':

																organized_attrib = organized_open_space_text.dxfattribs()

																tot_lot_pts = organized_attrib['insert']

																np_tot_lot_pts = np.array([tot_lot_pts[0], tot_lot_pts[1]]).round(2)

																tot_lot_coords = Point(np_tot_lot_pts)

																for organized_open_space_poly in org_polygon:

																	organized_open_space_poly_pts = [y[0:2] for y in organized_open_space_poly.get_points()]

																	np_organized_open_space_poly_pts = np.array(organized_open_space_poly_pts).round(2)

																	organized_space_poly = Polygon(np_organized_open_space_poly_pts)

																	if organized_space_poly.contains(tot_lot_coords) == True:

																		for f_tot_pts in np_organized_open_space_poly_pts:

																			np_f_tot_pts = np.array(f_tot_pts).round(2)

																			np_f_tot_point = Point(np_f_tot_pts)

																			if round(prop_poly1.distance(organized_space_poly)) != 0:

																				if (min_np_x_prop_line[0] <= np_f_tot_pts[0] and max_np_x_prop_line[0] >= np_f_tot_pts[0]) or ( min_np_x_prop_line[1] <= np_f_tot_pts[1] and max_np_x_prop_line[1] >= np_f_tot_pts[1]):

																					front_data.append(round(np_f_tot_point.distance(x_prop_work_line), 2))

										#used for x axis equal data

										elif(np_prop_linex_x[0,1]==np_prop_linex_x[1,1]):

											for x_f_prop_line in lwpolyline.virtual_entities():

												if x_f_prop_line.dxftype()=='LINE':

													x_f_prop_start_pts=[x_f_prop_line.dxf.start[0],x_f_prop_line.dxf.start[1]]

													x_f_prop_end_pts=[x_f_prop_line.dxf.end[0],x_f_prop_line.dxf.end[1]]

													x_prop_line=[x_f_prop_start_pts,x_f_prop_end_pts]

													np_x_prop_line=np.array(x_prop_line).round(2)

													if np_x_prop_line[0,0]==np_prop_linex_x[0,0] and np_x_prop_line[1,0]==np_prop_linex_x[1,0]:

														x_prop_work_line=LineString(np_x_prop_line)

														min_np_x_prop_line=np_x_prop_line.min(axis=0)

														max_np_x_prop_line=np_x_prop_line.max(axis=0)

														for organized_open_space_text in org_mtext:

															if organized_open_space_text.text=='Tot-lot':

																organized_attrib=organized_open_space_text.dxfattribs()

																tot_lot_pts=organized_attrib['insert']

																np_tot_lot_pts=np.array([tot_lot_pts[0],tot_lot_pts[1]]).round(2)

																tot_lot_coords=Point(np_tot_lot_pts)

																for organized_open_space_poly in org_polygon:

																	organized_open_space_poly_pts=[y[0:2] for y in organized_open_space_poly.get_points()]

																	np_organized_open_space_poly_pts=np.array(organized_open_space_poly_pts).round(2)

																	organized_space_poly=Polygon(np_organized_open_space_poly_pts)

																	if organized_space_poly.contains(tot_lot_coords)==True:

																		for f_tot_pts in np_organized_open_space_poly_pts:

																			np_f_tot_pts=np.array(f_tot_pts).round(2)

																			np_f_tot_point=Point(np_f_tot_pts)

																			if round(prop_poly1.distance(organized_space_poly))!=0:

																				if (min_np_x_prop_line[0]<=np_f_tot_pts[0] and  max_np_x_prop_line[0]>=np_f_tot_pts[0]) or (min_np_x_prop_line[1]<=np_f_tot_pts[1] and  max_np_x_prop_line[1]>=np_f_tot_pts[1]):

																					front_data.append(round(np_f_tot_point.distance(x_prop_work_line),2))

												elif(x_f_prop_line.dxftype()=='ARC'):

													x_f_prop_start_pts = [x_f_prop_line.dxf.start[0],x_f_prop_line.dxf.start[1]]

													x_f_prop_end_pts = [x_f_prop_line.dxf.end[0],x_f_prop_line.dxf.end[1]]

													x_prop_line = [x_f_prop_start_pts, x_f_prop_end_pts]

													np_x_prop_line = np.array(x_prop_line).round(2)

													if np_x_prop_line[0, 0] == np_prop_linex_x[0, 0] and np_x_prop_line[1, 0] == np_prop_linex_x[1, 0]:

														x_prop_work_line = LineString(np_x_prop_line)

														min_np_x_prop_line = np_x_prop_line.min(axis=0)

														max_np_x_prop_line = np_x_prop_line.max(axis=0)

														for organized_open_space_text in org_mtext:

															if organized_open_space_text.text == 'Tot-lot':

																organized_attrib = organized_open_space_text.dxfattribs()

																tot_lot_pts = organized_attrib['insert']

																np_tot_lot_pts = np.array([tot_lot_pts[0], tot_lot_pts[1]]).round(2)

																tot_lot_coords = Point(np_tot_lot_pts)

																for organized_open_space_poly in org_polygon:

																	organized_open_space_poly_pts = [y[0:2] for y in organized_open_space_poly.get_points()]

																	np_organized_open_space_poly_pts = np.array(organized_open_space_poly_pts).round(2)

																	organized_space_poly = Polygon(np_organized_open_space_poly_pts)

																	if organized_space_poly.contains(tot_lot_coords) == True:

																		for f_tot_pts in np_organized_open_space_poly_pts:

																			np_f_tot_pts = np.array(f_tot_pts).round(2)

																			np_f_tot_point = Point(np_f_tot_pts)

																			if round(prop_poly1.distance(organized_space_poly)) != 0:

																				if (min_np_x_prop_line[0] <= np_f_tot_pts[0] and max_np_x_prop_line[0] >= np_f_tot_pts[0]) or ( min_np_x_prop_line[1] <= np_f_tot_pts[1] and max_np_x_prop_line[1] >= np_f_tot_pts[1]):

																					front_data.append(round(np_f_tot_point.distance(x_prop_work_line), 2))


					rline_pts_value=[]

					rline_pts=[]

					for rdata in rear_coordinate_data:

						r_prop_linex=LineString(rdata[0])

						r_margin_linex=LineString(rdata[1])

						if round(r_prop_linex.distance(r_margin_linex),2)==min(rear_data):

							r_np_prop_linex=np.array(rdata[0]).round(2)

							prop_line_splitr=splitLines(r_np_prop_linex[0],r_np_prop_linex[1],4)

							for prop_splitr_pts in prop_line_splitr[1:-1]:

								np_prop_splitr_pts=np.array(prop_splitr_pts).round(2)

								prop_splitr_point=Point(np_prop_splitr_pts)

								rline_pts_value.append(round(prop_splitr_point.distance(r_margin_linex),2))

								rline_pts.append(np_prop_splitr_pts)

					for rdata_x in rear_coordinate_data:

						r_prop_linex_y=LineString(rdata_x[0])

						r_margin_linex_y=LineString(rdata_x[1])

						if round(r_prop_linex_y.distance(r_margin_linex_y),2)==min(rear_data):

							np_prop_linex_y=np.array(rdata_x[0]).round(2)

							max_prop_linex_y=np_prop_linex_y.max(axis=0).round(2)

							min_prop_linex_y=np_prop_linex_y.min(axis=0).round(2)

							for y_rline_pts in rline_pts:

								np_y_rline_pts=np.array(y_rline_pts).round(2)

								y_rline_point=Point(np_y_rline_pts)

								if ((max_prop_linex_y[0]>=np_y_rline_pts[0] and min_prop_linex_y[0]<=np_y_rline_pts[0]) and (max_prop_linex_y[1]>=np_y_rline_pts[1] and min_prop_linex_y[1]<=np_y_rline_pts[1]))==True:

									if round(y_rline_point.distance(r_margin_linex_y),2)==min(rline_pts_value):

										# used for y axis equal

										if np_prop_linex_y[0,1]==np_prop_linex_y[1,1]:

											for y_r_prop_line in lwpolyline.virtual_entities():

												if y_r_prop_line.dxftype()=='LINE':

													y_r_prop_start_pts=[y_r_prop_line.dxf.start[0],y_r_prop_line.dxf.start[1]]

													y_r_prop_end_pts=[y_r_prop_line.dxf.end[0],y_r_prop_line.dxf.end[1]]

													y_prop_line=[y_r_prop_start_pts,y_r_prop_end_pts]

													np_y_prop_line=np.array(y_prop_line).round(2)

													if np_y_prop_line[0,1]==np_prop_linex_y[0,1] and np_y_prop_line[1,1]==np_prop_linex_y[1,1]:

														y_prop_work_line=LineString(np_y_prop_line)

														min_np_y_prop_line=np_y_prop_line.min(axis=0)

														max_np_y_prop_line=np_y_prop_line.max(axis=0)

														for organized_open_space_text in org_mtext:

															if organized_open_space_text.text=='Tot-lot':

																organized_attrib=organized_open_space_text.dxfattribs()

																tot_lot_pts=organized_attrib['insert']

																np_tot_lot_pts=np.array([tot_lot_pts[0],tot_lot_pts[1]]).round(2)

																tot_lot_coords=Point(np_tot_lot_pts)

																for organized_open_space_poly in org_polygon:

																	organized_open_space_poly_pts=[y[0:2] for y in organized_open_space_poly.get_points()]

																	np_organized_open_space_poly_pts=np.array(organized_open_space_poly_pts).round(2)

																	organized_space_poly=Polygon(np_organized_open_space_poly_pts)

																	if organized_space_poly.contains(tot_lot_coords)==True:

																		for r_tot_pts in np_organized_open_space_poly_pts:

																			np_r_tot_pts=np.array(r_tot_pts).round(2)

																			np_r_tot_point=Point(np_r_tot_pts)

																			if round(prop_poly1.distance(organized_space_poly))!=0:

																				if (min_np_y_prop_line[0]<=np_r_tot_pts[0] and  max_np_y_prop_line[0]>=np_r_tot_pts[0]) or (min_np_y_prop_line[1]<=np_r_tot_pts[1] and  max_np_y_prop_line[1]>=np_r_tot_pts[1]):

																					rear_data.append(round(np_r_tot_point.distance(y_prop_work_line),2))
												elif(y_r_prop_line.dxftype()=='ARC'):

													y_r_prop_start_pts = [y_r_prop_line.start_point[0],y_r_prop_line.start_point[1]]

													y_r_prop_end_pts = [y_r_prop_line.end_point[0],y_r_prop_line.end_point[1]]

													y_prop_line = [y_r_prop_start_pts, y_r_prop_end_pts]

													np_y_prop_line = np.array(y_prop_line).round(2)

													if np_y_prop_line[0, 1] == np_prop_linex_y[0, 1] and np_y_prop_line[1, 1] == np_prop_linex_y[1, 1]:

														y_prop_work_line = LineString(np_y_prop_line)

														min_np_y_prop_line = np_y_prop_line.min(axis=0)

														max_np_y_prop_line = np_y_prop_line.max(axis=0)

														for organized_open_space_text in org_mtext:

															if organized_open_space_text.text == 'Tot-lot':

																organized_attrib = organized_open_space_text.dxfattribs()

																tot_lot_pts = organized_attrib['insert']

																np_tot_lot_pts = np.array([tot_lot_pts[0], tot_lot_pts[1]]).round(2)

																tot_lot_coords = Point(np_tot_lot_pts)

																for organized_open_space_poly in org_polygon:

																	organized_open_space_poly_pts = [y[0:2] for y in organized_open_space_poly.get_points()]

																	np_organized_open_space_poly_pts = np.array(organized_open_space_poly_pts).round(2)

																	organized_space_poly = Polygon(np_organized_open_space_poly_pts)

																	if organized_space_poly.contains(tot_lot_coords) == True:

																		for r_tot_pts in np_organized_open_space_poly_pts:

																			np_r_tot_pts = np.array(r_tot_pts).round(2)

																			np_r_tot_point = Point(np_r_tot_pts)

																			if round(prop_poly1.distance(organized_space_poly)) != 0:

																				if (min_np_y_prop_line[0] <=np_r_tot_pts[0] and max_np_y_prop_line[0] >=np_r_tot_pts[0]) or ( min_np_y_prop_line[1] <= np_r_tot_pts[1] and max_np_y_prop_line[1] >= np_r_tot_pts[1]):

																					rear_data.append(round(np_r_tot_point.distance(y_prop_work_line), 2))


										#used for x axis equal data

										elif(np_prop_linex_y[0,0]==np_prop_linex_y[1,0]):

											for y_r_prop_line in lwpolyline.virtual_entities():

												if y_r_prop_line.dxftype()=='LINE':

													y_r_prop_start_pts=[y_r_prop_line.dxf.start[0],y_r_prop_line.dxf.start[1]]

													y_r_prop_end_pts=[y_r_prop_line.dxf.end[0],y_r_prop_line.dxf.end[1]]

													y_prop_line=[y_r_prop_start_pts,y_r_prop_end_pts]

													np_y_prop_line=np.array(y_prop_line).round(2)

													if np_y_prop_line[0,0]==np_prop_linex_y[0,0] and np_y_prop_line[1,0]==np_prop_linex_y[1,0]:

														y_prop_work_line=LineString(np_y_prop_line)

														min_np_y_prop_line=np_y_prop_line.min(axis=0)

														max_np_y_prop_line=np_y_prop_line.max(axis=0)

														for organized_open_space_text in org_mtext:

															if organized_open_space_text.text=='Tot-lot':

																organized_attrib=organized_open_space_text.dxfattribs()

																tot_lot_pts=organized_attrib['insert']

																np_tot_lot_pts=np.array([tot_lot_pts[0],tot_lot_pts[1]]).round(2)

																tot_lot_coords=Point(np_tot_lot_pts)

																for organized_open_space_poly in org_polygon:

																	organized_open_space_poly_pts=[y[0:2] for y in organized_open_space_poly.get_points()]

																	np_organized_open_space_poly_pts=np.array(organized_open_space_poly_pts).round(2)

																	organized_space_poly=Polygon(np_organized_open_space_poly_pts)

																	if organized_space_poly.contains(tot_lot_coords)==True:

																		for r_tot_pts in np_organized_open_space_poly_pts:

																			np_r_tot_pts=np.array(r_tot_pts).round(2)
																			np_r_tot_point=Point(np_r_tot_pts)

																			if round(prop_poly1.distance(organized_space_poly))!=0:

																				if (min_np_y_prop_line[0]<=np_r_tot_pts[0] and  max_np_y_prop_line[0]>=np_r_tot_pts[0]) or (min_np_y_prop_line[1]<=np_r_tot_pts[1] and  max_np_y_prop_line[1]>=np_r_tot_pts[1]):

																					rear_data.append(round(np_r_tot_point.distance(y_prop_work_line),2))

												elif(y_r_prop_line.dxftype()=='ARC'):

													y_r_prop_start_pts = [y_r_prop_line.start_point[0],y_r_prop_line.start_point[1]]

													y_r_prop_end_pts = [y_r_prop_line.end_point[0],y_r_prop_line.end_point[1]]

													y_prop_line = [y_r_prop_start_pts, y_r_prop_end_pts]

													np_y_prop_line = np.array(y_prop_line).round(2)

													if np_y_prop_line[0, 0] == np_prop_linex_y[0, 0] and np_y_prop_line[1, 0] == np_prop_linex_y[1, 0]:

														y_prop_work_line = LineString(np_y_prop_line)

														min_np_y_prop_line = np_y_prop_line.min(axis=0)

														max_np_y_prop_line = np_y_prop_line.max(axis=0)

														for organized_open_space_text in org_mtext:

															if organized_open_space_text.text == 'Tot-lot':

																organized_attrib = organized_open_space_text.dxfattribs()

																tot_lot_pts = organized_attrib['insert']

																np_tot_lot_pts = np.array([tot_lot_pts[0], tot_lot_pts[1]]).round(2)

																tot_lot_coords = Point(np_tot_lot_pts)

																for organized_open_space_poly in org_polygon:

																	organized_open_space_poly_pts = [y[0:2] for y in organized_open_space_poly.get_points()]

																	np_organized_open_space_poly_pts = np.array(organized_open_space_poly_pts).round(2)

																	organized_space_poly = Polygon(np_organized_open_space_poly_pts)

																	if organized_space_poly.contains(tot_lot_coords) == True:

																		for r_tot_pts in np_organized_open_space_poly_pts:

																			np_r_tot_pts = np.array(r_tot_pts).round(2)

																			np_r_tot_point = Point(np_r_tot_pts)

																			if round(prop_poly1.distance(organized_space_poly)) != 0:

																				if (min_np_y_prop_line[0] <= np_r_tot_pts[0] and max_np_y_prop_line[0] >= np_r_tot_pts[0]) or ( min_np_y_prop_line[1] <= np_r_tot_pts[1] and max_np_y_prop_line[1] >= np_r_tot_pts[1]):

																					rear_data.append(round(np_r_tot_point.distance(y_prop_work_line), 2))


					s1line_pts_value=[]

					s1line_pts=[]

					for s1data in side1_coordinate_data:

						s1_prop_linex=LineString(s1data[0])

						s1_margin_linex=LineString(s1data[1])

						if round(s1_prop_linex.boundary.distance(s1_margin_linex),2)==min(side1_data):

							s1_np_prop_linex=np.array(s1data[0]).round(2)

							prop_line_splits1=splitLines(s1_np_prop_linex[0],s1_np_prop_linex[1],4)

							for prop_splits1_pts in prop_line_splits1[1:-1]:

								np_prop_splits1_pts=np.array(prop_splits1_pts).round(2)

								prop_splits1_point=Point(np_prop_splits1_pts)

								s1line_pts_value.append(round(prop_splits1_point.distance(s1_margin_linex),2))

								s1line_pts.append(np_prop_splits1_pts)

					for s1data_x in side1_coordinate_data:

						s1_prop_linex_x1=LineString(s1data_x[0])

						s1_margin_linex_x1=LineString(s1data_x[1])

						if round(s1_prop_linex_x1.distance(s1_margin_linex_x1),2)==min(side1_data):

							np_prop_linex_x1=np.array(s1data_x[0]).round(2)

							max_prop_linex_x1=np_prop_linex_x1.max(axis=0).round(2)

							min_prop_linex_x1=np_prop_linex_x1.min(axis=0).round(2)

							for x1_s1line_pts in s1line_pts:

								np_x1_s1line_pts=np.array(x1_s1line_pts).round(2)

								x1_s1line_point=Point(np_x1_s1line_pts)

								if ((max_prop_linex_x1[0]>=np_x1_s1line_pts[0] and min_prop_linex_x1[0]<=np_x1_s1line_pts[0]) and (max_prop_linex_x1[1]>=np_x1_s1line_pts[1] and min_prop_linex_x1[1]<=np_x1_s1line_pts[1]))==True:

									if round(x1_s1line_point.distance(s1_margin_linex_x1),2)==min(s1line_pts_value):

										# used for y axis equal

										if np_prop_linex_x1[0,1]==np_prop_linex_x1[1,1]:

											for x1_s1_prop_line in lwpolyline.virtual_entities():

												if x1_s1_prop_line.dxftype()=='LINE':

													x1_s1_prop_start_pts=[x1_s1_prop_line.dxf.start[0],x1_s1_prop_line.dxf.start[1]]

													x1_s1_prop_end_pts=[x1_s1_prop_line.dxf.end[0],x1_s1_prop_line.dxf.end[1]]

													x1_prop_line=[x1_s1_prop_start_pts,x1_s1_prop_end_pts]

													np_x1_prop_line=np.array(x1_prop_line).round(2)

													if np_x1_prop_line[0,1]==np_prop_linex_x1[0,1] and np_x1_prop_line[1,1]==np_prop_linex_x1[1,1]:

														x1_prop_work_line=LineString(np_x1_prop_line)

														min_np_x1_prop_line=np_x1_prop_line.min(axis=0)

														max_np_x1_prop_line=np_x1_prop_line.max(axis=0)

														for organized_open_space_text in org_mtext:

															if organized_open_space_text.text=='Tot-lot':

																organized_attrib=organized_open_space_text.dxfattribs()

																tot_lot_pts=organized_attrib['insert']

																np_tot_lot_pts=np.array([tot_lot_pts[0],tot_lot_pts[1]]).round(2)

																tot_lot_coords=Point(np_tot_lot_pts)

																for organized_open_space_poly in org_polygon:

																	organized_open_space_poly_pts=[y[0:2] for y in organized_open_space_poly.get_points()]

																	np_organized_open_space_poly_pts=np.array(organized_open_space_poly_pts).round(2)

																	organized_space_poly=Polygon(np_organized_open_space_poly_pts)

																	if organized_space_poly.contains(tot_lot_coords)==True:

																		for s1_tot_pts in np_organized_open_space_poly_pts:

																			np_s1_tot_pts=np.array(s1_tot_pts).round(2)

																			np_s1_tot_point=Point(np_s1_tot_pts)

																			if round(prop_poly1.distance(organized_space_poly))!=0:

																				if (min_np_x1_prop_line[0]<=np_s1_tot_pts[0] and  max_np_x1_prop_line[0]>=np_s1_tot_pts[0]) or (min_np_x1_prop_line[1]<=np_s1_tot_pts[1] and  max_np_x1_prop_line[1]>=np_s1_tot_pts[1]):

																					side1_data.append(round(np_s1_tot_point.distance(x1_prop_work_line),2))

												elif(x1_s1_prop_line.dxftype()=='ARC'):

													x1_s1_prop_start_pts = [x1_s1_prop_line.start_point[0],x1_s1_prop_line.start_point[1]]

													x1_s1_prop_end_pts = [x1_s1_prop_line.end_point[0],x1_s1_prop_line.end_point[1]]

													x1_prop_line = [x1_s1_prop_start_pts, x1_s1_prop_end_pts]

													np_x1_prop_line = np.array(x1_prop_line).round(2)

													if np_x1_prop_line[0, 1] == np_prop_linex_x1[0, 1] and np_x1_prop_line[1, 1] == np_prop_linex_x1[1, 1]:

														x1_prop_work_line = LineString(np_x1_prop_line)

														min_np_x1_prop_line = np_x1_prop_line.min(axis=0)

														max_np_x1_prop_line = np_x1_prop_line.max(axis=0)

														for organized_open_space_text in org_mtext:

															if organized_open_space_text.text == 'Tot-lot':

																organized_attrib = organized_open_space_text.dxfattribs()

																tot_lot_pts = organized_attrib['insert']

																np_tot_lot_pts = np.array([tot_lot_pts[0], tot_lot_pts[1]]).round(2)

																tot_lot_coords = Point(np_tot_lot_pts)

																for organized_open_space_poly in org_polygon:

																	organized_open_space_poly_pts = [y[0:2] for y in organized_open_space_poly.get_points()]

																	np_organized_open_space_poly_pts = np.array(organized_open_space_poly_pts).round(2)

																	organized_space_poly = Polygon(np_organized_open_space_poly_pts)

																	if organized_space_poly.contains(tot_lot_coords) == True:

																		for s1_tot_pts in np_organized_open_space_poly_pts:

																			np_s1_tot_pts = np.array(s1_tot_pts).round(2)

																			np_s1_tot_point = Point(np_s1_tot_pts)

																			if round(prop_poly1.distance(organized_space_poly)) != 0:

																				if (min_np_x1_prop_line[0] <= np_s1_tot_pts[0] and max_np_x1_prop_line[0] >= np_s1_tot_pts[0]) or ( min_np_x1_prop_line[1] <= np_s1_tot_pts[1] and max_np_x1_prop_line[1] >= np_s1_tot_pts[1]):

																					side1_data.append(round(np_s1_tot_point.distance(x1_prop_work_line), 2))
										#used for x axis equal data

										elif(np_prop_linex_x1[0,0]==np_prop_linex_x1[1,0]):

											for x1_s1_prop_line in lwpolyline.virtual_entities():

												if x1_s1_prop_line.dxftype()=='LINE':

													x1_s1_prop_start_pts=[x1_s1_prop_line.dxf.start[0],x1_s1_prop_line.dxf.start[1]]

													x1_s1_prop_end_pts=[x1_s1_prop_line.dxf.end[0],x1_s1_prop_line.dxf.end[1]]

													x1_prop_line=[x1_s1_prop_start_pts,x1_s1_prop_end_pts]

													np_x1_prop_line=np.array(x1_prop_line).round(2)

													if np_x1_prop_line[0,0]==np_prop_linex_x1[0,0] and np_x1_prop_line[1,0]==np_prop_linex_x1[1,0]:

														x1_prop_work_line=LineString(np_x1_prop_line)

														min_np_x1_prop_line=np_x1_prop_line.min(axis=0)

														max_np_x1_prop_line=np_x1_prop_line.max(axis=0)

														for organized_open_space_text in org_mtext:

															if organized_open_space_text.text=='Tot-lot':

																organized_attrib=organized_open_space_text.dxfattribs()

																tot_lot_pts=organized_attrib['insert']

																np_tot_lot_pts=np.array([tot_lot_pts[0],tot_lot_pts[1]]).round(2)

																tot_lot_coords=Point(np_tot_lot_pts)

																for organized_open_space_poly in org_polygon:

																	organized_open_space_poly_pts=[y[0:2] for y in organized_open_space_poly.get_points()]

																	np_organized_open_space_poly_pts=np.array(organized_open_space_poly_pts).round(2)

																	organized_space_poly=Polygon(np_organized_open_space_poly_pts)

																	if organized_space_poly.contains(tot_lot_coords)==True:

																		for s1_tot_pts in np_organized_open_space_poly_pts:

																			np_s1_tot_pts=np.array(s1_tot_pts).round(2)
																			np_s1_tot_point=Point(np_s1_tot_pts)

																			if round(prop_poly1.distance(organized_space_poly))!=0:

																				if (min_np_x1_prop_line[0]<=np_s1_tot_pts[0] and  max_np_x1_prop_line[0]>=np_s1_tot_pts[0]) or (min_np_x1_prop_line[1]<=np_s1_tot_pts[1] and  max_np_x1_prop_line[1]>=np_s1_tot_pts[1]):

																					side1_data.append(round(np_s1_tot_point.distance(x1_prop_work_line),2))

												elif(x1_s1_prop_line.dxftype()=='ARC'):

													x1_s1_prop_start_pts = [x1_s1_prop_line.start_point[0],x1_s1_prop_line.start_point[1]]

													x1_s1_prop_end_pts = [x1_s1_prop_line.end_point[0],x1_s1_prop_line.end_point[1]]

													x1_prop_line = [x1_s1_prop_start_pts, x1_s1_prop_end_pts]

													np_x1_prop_line = np.array(x1_prop_line).round(2)

													if np_x1_prop_line[0, 0] == np_prop_linex_x1[0, 0] and np_x1_prop_line[1, 0] == np_prop_linex_x1[1, 0]:

														x1_prop_work_line = LineString(np_x1_prop_line)

														min_np_x1_prop_line = np_x1_prop_line.min(axis=0)

														max_np_x1_prop_line = np_x1_prop_line.max(axis=0)

														for organized_open_space_text in org_mtext:

															if organized_open_space_text.text == 'Tot-lot':

																organized_attrib = organized_open_space_text.dxfattribs()

																tot_lot_pts = organized_attrib['insert']

																np_tot_lot_pts = np.array([tot_lot_pts[0], tot_lot_pts[1]]).round(2)

																tot_lot_coords = Point(np_tot_lot_pts)

																for organized_open_space_poly in org_polygon:

																	organized_open_space_poly_pts = [y[0:2] for y in organized_open_space_poly.get_points()]

																	np_organized_open_space_poly_pts = np.array(organized_open_space_poly_pts).round(2)

																	organized_space_poly = Polygon(np_organized_open_space_poly_pts)

																	if organized_space_poly.contains(tot_lot_coords) == True:

																		for s1_tot_pts in np_organized_open_space_poly_pts:

																			np_s1_tot_pts = np.array(s1_tot_pts).round(2)

																			np_s1_tot_point = Point(np_s1_tot_pts)

																			if round(prop_poly1.distance(organized_space_poly)) != 0:

																				if (min_np_x1_prop_line[0] <= np_s1_tot_pts[0] and max_np_x1_prop_line[0] >= np_s1_tot_pts[0]) or ( min_np_x1_prop_line[1] <= np_s1_tot_pts[1] and max_np_x1_prop_line[1] >= np_s1_tot_pts[1]):

																					side1_data.append(round(np_s1_tot_point.distance(x1_prop_work_line), 2))


					s2line_pts_value=[]

					s2line_pts=[]

					for s2data in side2_coordinate_data:

						s2_prop_linex=LineString(s2data[0])

						s2_margin_linex=LineString(s2data[1])

						if round(s2_prop_linex.distance(s2_margin_linex),2)==min(side2_data):

							s2_np_prop_linex=np.array(s2data[0]).round(2)

							prop_line_splits2=splitLines(s2_np_prop_linex[0],s2_np_prop_linex[1],4)

							for prop_splits2_pts in prop_line_splits2[1:-1]:

								np_prop_splits2_pts=np.array(prop_splits2_pts).round(2)

								prop_splits2_point=Point(np_prop_splits2_pts)

								s2line_pts_value.append(round(prop_splits2_point.distance(s2_margin_linex),2))

								s2line_pts.append(np_prop_splits2_pts)

					for s2data_x in side2_coordinate_data:

						s2_prop_linex_y1=LineString(s2data_x[0])

						s2_margin_linex_y1=LineString(s2data_x[1])

						if round(s2_prop_linex_y1.distance(s2_margin_linex_y1),2)==min(side2_data):

							np_prop_linex_y1=np.array(s2data_x[0]).round(2)

							max_prop_linex_y1=np_prop_linex_y1.max(axis=0).round(2)

							min_prop_linex_y1=np_prop_linex_y1.min(axis=0).round(2)

							for y1_s2line_pts in s2line_pts:

								np_y1_s2line_pts=np.array(y1_s2line_pts).round(2)

								y1_s2line_point=Point(np_y1_s2line_pts)

								if ((max_prop_linex_y1[0]>=np_y1_s2line_pts[0] and min_prop_linex_y1[0]<=np_y1_s2line_pts[0]) and (max_prop_linex_y1[1]>=np_y1_s2line_pts[1] and min_prop_linex_y1[1]<=np_y1_s2line_pts[1]))==True:

									if round(y1_s2line_point.distance(s2_margin_linex_y1),2)==min(s2line_pts_value):

										# used for y axis equal

										if np_prop_linex_y1[0,1]==np_prop_linex_y1[1,1]:

											for y1_s2_prop_line in lwpolyline.virtual_entities():

												if y1_s2_prop_line.dxftype()=='LINE':

													y1_s2_prop_start_pts=[y1_s2_prop_line.dxf.start[0],y1_s2_prop_line.dxf.start[1]]

													y1_s2_prop_end_pts=[y1_s2_prop_line.dxf.end[0],y1_s2_prop_line.dxf.end[1]]

													y1_prop_line=[y1_s2_prop_start_pts,y1_s2_prop_end_pts]

													np_y1_prop_line=np.array(y1_prop_line).round(2)

													if np_y1_prop_line[0,1]==np_prop_linex_y1[0,1] and np_y1_prop_line[1,1]==np_prop_linex_y1[1,1]:

														y1_prop_work_line=LineString(np_y1_prop_line)

														min_np_y1_prop_line=np_y1_prop_line.min(axis=0)

														max_np_y1_prop_line=np_y1_prop_line.max(axis=0)

														for organized_open_space_text in org_mtext:

															if organized_open_space_text.text=='Tot-lot':

																organized_attrib=organized_open_space_text.dxfattribs()

																tot_lot_pts=organized_attrib['insert']

																np_tot_lot_pts=np.array([tot_lot_pts[0],tot_lot_pts[1]]).round(2)

																tot_lot_coords=Point(np_tot_lot_pts)

																for organized_open_space_poly in org_polygon:

																	organized_open_space_poly_pts=[y[0:2] for y in organized_open_space_poly.get_points()]

																	np_organized_open_space_poly_pts=np.array(organized_open_space_poly_pts).round(2)

																	organized_space_poly=Polygon(np_organized_open_space_poly_pts)

																	if organized_space_poly.contains(tot_lot_coords)==True:

																		for s2_tot_pts in np_organized_open_space_poly_pts:

																			np_s2_tot_pts=np.array(s2_tot_pts).round(2)

																			np_s2_tot_point=Point(np_s2_tot_pts)

																			if round(prop_poly1.distance(organized_space_poly))!=0:

																				if (min_np_y1_prop_line[0]<=np_s2_tot_pts[0] and  max_np_y1_prop_line[0]>=np_s2_tot_pts[0]) or (min_np_y1_prop_line[1]<=np_s2_tot_pts[1] and  max_np_y1_prop_line[1]>=np_s2_tot_pts[1]):

																					side2_data.append(round(np_s2_tot_point.distance(y1_prop_work_line),2))

												elif y1_s2_prop_line.dxftype() == 'ARC':

													y1_s2_prop_start_pts = [y1_s2_prop_line.start_point[0],y1_s2_prop_line.start_point[1]]

													y1_s2_prop_end_pts = [y1_s2_prop_line.end_point[0],y1_s2_prop_line.end_point[1]]

													y1_prop_line = [y1_s2_prop_start_pts, y1_s2_prop_end_pts]

													np_y1_prop_line = np.array(y1_prop_line).round(2)

													if np_y1_prop_line[0, 1] == np_prop_linex_y1[0, 1] and np_y1_prop_line[1, 1] == np_prop_linex_y1[1, 1]:

														y1_prop_work_line = LineString(np_y1_prop_line)

														min_np_y1_prop_line = np_y1_prop_line.min(axis=0)

														max_np_y1_prop_line = np_y1_prop_line.max(axis=0)

														for organized_open_space_text in org_mtext:

															if organized_open_space_text.text == 'Tot-lot':

																organized_attrib = organized_open_space_text.dxfattribs()

																tot_lot_pts = organized_attrib['insert']

																np_tot_lot_pts = np.array([tot_lot_pts[0], tot_lot_pts[1]]).round(2)

																tot_lot_coords = Point(np_tot_lot_pts)

																for organized_open_space_poly in org_polygon:

																	organized_open_space_poly_pts = [y[0:2] for y in organized_open_space_poly.get_points()]

																	np_organized_open_space_poly_pts = np.array(organized_open_space_poly_pts).round(2)

																	organized_space_poly = Polygon(np_organized_open_space_poly_pts)

																	if organized_space_poly.contains(tot_lot_coords) == True:

																		for s2_tot_pts in np_organized_open_space_poly_pts:

																			np_s2_tot_pts = np.array(s2_tot_pts).round(2)

																			np_s2_tot_point = Point(np_s2_tot_pts)

																			if round(prop_poly1.distance(organized_space_poly)) != 0:

																				if (min_np_y1_prop_line[0] <=np_s2_tot_pts[0] and max_np_y1_prop_line[0] >=np_s2_tot_pts[0]) or (min_np_y1_prop_line[1] <=np_s2_tot_pts[1] and max_np_y1_prop_line[1] >=np_s2_tot_pts[1]):

																					side2_data.append(round(np_s2_tot_point.distance(y1_prop_work_line), 2))

										#used for x axis equal data

									elif(np_prop_linex_y1[0,0]==np_prop_linex_y1[1,0]):

											for y1_s2_prop_line in lwpolyline.virtual_entities():

												if y1_s2_prop_line.dxftype()=='LINE':

													y1_s2_prop_start_pts=[y1_s2_prop_line.dxf.start[0],y1_s2_prop_line.dxf.start[1]]

													y1_s2_prop_end_pts=[y1_s2_prop_line.dxf.end[0],y1_s2_prop_line.dxf.end[1]]

													y1_prop_line=[y1_s2_prop_start_pts,y1_s2_prop_end_pts]

													np_y1_prop_line=np.array(y1_prop_line).round(2)

													if np_y1_prop_line[0,0]==np_prop_linex_y1[0,0] and np_y1_prop_line[1,0]==np_prop_linex_y1[1,0]:

														y1_prop_work_line=LineString(np_y1_prop_line)

														min_np_y1_prop_line=np_y1_prop_line.min(axis=0)

														max_np_y1_prop_line=np_y1_prop_line.max(axis=0)

														for organized_open_space_text in org_mtext:

															if organized_open_space_text.text=='Tot-lot':

																organized_attrib=organized_open_space_text.dxfattribs()

																tot_lot_pts=organized_attrib['insert']

																np_tot_lot_pts=np.array([tot_lot_pts[0],tot_lot_pts[1]]).round(2)

																tot_lot_coords=Point(np_tot_lot_pts)

																for organized_open_space_poly in org_polygon:

																	organized_open_space_poly_pts=[y[0:2] for y in organized_open_space_poly.get_points()]

																	np_organized_open_space_poly_pts=np.array(organized_open_space_poly_pts).round(2)

																	organized_space_poly=Polygon(np_organized_open_space_poly_pts)

																	if organized_space_poly.contains(tot_lot_coords)==True:

																		for s2_tot_pts in np_organized_open_space_poly_pts:

																			np_s2_tot_pts=np.array(s2_tot_pts).round(2)

																			np_s2_tot_point=Point(np_s2_tot_pts)

																			if round(prop_poly1.distance(organized_space_poly))!=0:

																				if (min_np_y1_prop_line[0]<=np_s2_tot_pts[0] and  max_np_y1_prop_line[0]>=np_s2_tot_pts[0]) or (min_np_y1_prop_line[1]<=np_s2_tot_pts[1] and  max_np_y1_prop_line[1]>=np_s2_tot_pts[1]):

																					side2_data.append(round(np_s2_tot_point.distance(y1_prop_work_line),2))

												elif(y1_s2_prop_line.dxftype()=='ARC'):

													y1_s2_prop_start_pts = [y1_s2_prop_line.start_point[0],y1_s2_prop_line.start_point[1]]

													y1_s2_prop_end_pts = [y1_s2_prop_line.end_point[0],y1_s2_prop_line.end_point[1]]

													y1_prop_line = [y1_s2_prop_start_pts, y1_s2_prop_end_pts]

													np_y1_prop_line = np.array(y1_prop_line).round(2)

													if np_y1_prop_line[0, 0] == np_prop_linex_y1[0, 0] and np_y1_prop_line[1, 0] == np_prop_linex_y1[1, 0]:

														y1_prop_work_line = LineString(np_y1_prop_line)

														min_np_y1_prop_line = np_y1_prop_line.min(axis=0)

														max_np_y1_prop_line = np_y1_prop_line.max(axis=0)

														for organized_open_space_text in org_mtext:

															if organized_open_space_text.text == 'Tot-lot':

																organized_attrib = organized_open_space_text.dxfattribs()

																tot_lot_pts = organized_attrib['insert']

																np_tot_lot_pts = np.array([tot_lot_pts[0], tot_lot_pts[1]]).round(2)

																tot_lot_coords = Point(np_tot_lot_pts)

																for organized_open_space_poly in org_polygon:

																	organized_open_space_poly_pts = [y[0:2] for y in organized_open_space_poly.get_points()]

																	np_organized_open_space_poly_pts = np.array(organized_open_space_poly_pts).round(2)

																	organized_space_poly = Polygon(np_organized_open_space_poly_pts)

																	if organized_space_poly.contains(tot_lot_coords) == True:

																		for s2_tot_pts in np_organized_open_space_poly_pts:

																			np_s2_tot_pts = np.array(s2_tot_pts).round(2)

																			np_s2_tot_point = Point(np_s2_tot_pts)

																			if round(prop_poly1.distance(organized_space_poly)) != 0:

																				if (min_np_y1_prop_line[0] <=np_s2_tot_pts[0] and max_np_y1_prop_line[0] >=np_s2_tot_pts[0]) or (min_np_y1_prop_line[1] <=np_s2_tot_pts[1] and max_np_y1_prop_line[1] >=np_s2_tot_pts[1]):

																					side2_data.append(round(np_s2_tot_point.distance(y1_prop_work_line), 2))


					info_data=[]

					tmpPropWorkDict=dict()

					tmpPropWorkDict['NAME']=text_name

					if front_data is not None and len(front_data)>0:

						tmpPropWorkDict['FRONT']=min(front_data)

						#info_data.append(f'Front,{min(front_data)}')

					else:

						tmpPropWorkDict['FRONT']='-1'

					if rear_data is not None and len(rear_data)>0 :

						tmpPropWorkDict['REAR']=min(rear_data)

						#info_data.append(f'Rear,{min(rear_data)}')

					else:

						tmpPropWorkDict['REAR']='-1'

					if side1_data is not None and len(side1_data)>0 :

						tmpPropWorkDict['SIDE1']=min(side1_data)

						#info_data.append(f'Side1,{min(side1_data)}')

					else:

						tmpPropWorkDict['SIDE1']='-1'

					if side2_data is not None and len(side2_data)>0 :

						tmpPropWorkDict['SIDE2']=min(side2_data)

						#info_data.append(f'Side2,{min(side2_data)}')

					else:

						tmpPropWorkDict['SIDE2']='-1'

					#main_data=f'{name.dxf.text},{info_data}'
					# print ('refid ', refid)

					returnValueDict[refid]=tmpPropWorkDict
					# print ('returnValueDict ', returnValueDict)
					#resultsList.append(main_data)

	except IndexError as ieXp:
		get_current_logger().error(f'Didn"t have name of value'+str(ieXp))
		return returnValueDict

	except IOError as ioe:
		get_current_logger().error(f'Not a DXF file or a generic I/O error.'+str(ioe))
		return returnValueDict

	except ezdxf.DXFStructureError  as dError:
		get_current_logger().error(f'Invalid or corrupted DXF file.'+str(dError))
		return returnValueDict

	return returnValueDict

#02/12/23 Fix for green strip 

def Green_strip_width(msp):#(folder:str,filename:str):#

	returnValueDict={}

	resultsList=[]

	if (msp is None):#(folder is None or filename is None):#

		return returnValueDict

	#dxf_path=os.path.join(folder,filename)

	try:
		#read_dxf=ezdxf.readfile(dxf_path)

		#print('read file')

		#msp=read_dxf.modelspace()

		orgSpacePolyEntities=msp.query('LWPOLYLINE[layer=="_OrganizedOpenSpace"]')
		orgSpaceTextEntities= msp.query('MTEXT[layer=="_OrganizedOpenSpace"]')
		marginEntities=msp.query('INSERT[layer=="_MarginLine"]')

		for org_text in orgSpaceTextEntities:# msp.query('MTEXT[layer=="_OrganizedOpenSpace"]'):

			if org_text.text=='Tot-lot' or org_text.text=='Tot lot':

				org_text_attribs=org_text.dxfattribs()

				insert_org_text=org_text_attribs.get('insert')

				org_text_pts=[insert_org_text[0],insert_org_text[1]]

				np_org_text_pts=np.array(org_text_pts).round(1)

				org_text_point=Point(np_org_text_pts)

				for org_polygon in orgSpacePolyEntities:#msp.query('LWPOLYLINE[layer=="_OrganizedOpenSpace"]'):

					org_polygon_pts=[o[0:2] for o in org_polygon.get_points()]

					np_org_polygon_pts=np.array(org_polygon_pts).round(1)

					org_polygon_point=Polygon(np_org_polygon_pts)

					if org_polygon_point.contains(org_text_point)==True:

						tot_lot_data=[]

						for org_line in org_polygon.virtual_entities():

							if org_line.dxftype()=='LINE':

								org_line_start_pts=[org_line.dxf.start[0],org_line.dxf.start[1]]

								org_line_end_pts=[org_line.dxf.end[0],org_line.dxf.end[1]]

								org_line_pts=[org_line_start_pts,org_line_end_pts]

								np_org_line_pts=np.array(org_line_pts).round(1)

								max_np_org_line_pts=np_org_line_pts.max(axis=0)

								min_np_org_line_pts=np_org_line_pts.min(axis=0)

								org_line_point=LineString(np_org_line_pts)

								if round(org_line_point.length)>1:

									 #equal x value

									if np_org_line_pts[0,0]==np_org_line_pts[1,0]:

										x_data=[]

										for org_linea in org_polygon.virtual_entities():

											if org_linea.dxftype()=='LINE':

												org_linea_start_pts=[org_linea.dxf.start[0],org_linea.dxf.start[1]]

												org_linea_end_pts=[org_linea.dxf.end[0],org_linea.dxf.end[1]]

												org_linea_pts=[org_linea_start_pts,org_linea_end_pts]

												np_org_linea_pts=np.array(org_linea_pts).round(1)

												max_np_org_linea_pts=np_org_linea_pts.max(axis=0)

												min_np_org_linea_pts=np_org_linea_pts.min(axis=0)

												org_linea_point=LineString(np_org_linea_pts)

												if round(org_linea_point.length)>=1:

													if np_org_linea_pts[0,0]==np_org_linea_pts[1,0]:

														if round(org_line_point.distance(org_linea_point))!=0:

															if max_np_org_line_pts[1]>=max_np_org_linea_pts[1] and min_np_org_line_pts[1]<=min_np_org_linea_pts[1]:

																x_data.append(round(org_line_point.distance(org_linea_point),1))

															elif(max_np_org_linea_pts[1]>=max_np_org_line_pts[1] and min_np_org_linea_pts[1]<=min_np_org_line_pts[1]):

																x_data.append(round(org_linea_point.distance(org_line_point),1))


										if x_data !=[]:

											tot_lot_data.append(min(x_data))

									#equal y value

									elif(np_org_line_pts[0,1]==np_org_line_pts[1,1]):

										y_data=[]

										for org_lineb in org_polygon.virtual_entities():

											if org_lineb.dxftype()=='LINE':

												org_lineb_start_pts=[org_lineb.dxf.start[0],org_lineb.dxf.start[1]]

												org_lineb_end_pts=[org_lineb.dxf.end[0],org_lineb.dxf.end[1]]

												org_lineb_pts=[org_lineb_start_pts,org_lineb_end_pts]

												np_org_lineb_pts=np.array(org_lineb_pts).round(1)

												max_np_org_lineb_pts=np_org_lineb_pts.max(axis=0)

												min_np_org_lineb_pts=np_org_lineb_pts.min(axis=0)

												org_lineb_point=LineString(np_org_lineb_pts)

												if round(org_lineb_point.length)>=1:

													if np_org_lineb_pts[0,1]==np_org_lineb_pts[1,1]:

														if round(org_line_point.distance(org_lineb_point))!=0:

															if max_np_org_line_pts[0]>=max_np_org_lineb_pts[0] and min_np_org_line_pts[0]<=min_np_org_lineb_pts[0]:

																y_data.append(round(org_line_point.distance(org_lineb_point),1))

															elif(max_np_org_lineb_pts[0]>=max_np_org_line_pts[0] and min_np_org_lineb_pts[0]<=min_np_org_line_pts[0]):

																y_data.append(round(org_line_point.distance(org_lineb_point),1))

										if y_data!=[]:

											tot_lot_data.append(min(y_data))

									#Does not equal x amd y value

									else:

										z_data=[]

										for org_linec in org_polygon.virtual_entities():

											if org_linec.dxftype()=='LINE':

												org_linec_start_pts=[org_linec.dxf.start[0],org_linec.dxf.start[1]]

												org_linec_end_pts=[org_linec.dxf.end[0],org_linec.dxf.end[1]]

												org_linec_pts=[org_linec_start_pts,org_linec_end_pts]

												np_org_linec_pts=np.array(org_linec_pts).round(1)

												max_np_org_linec_pts=np_org_linec_pts.max(axis=0)

												min_np_org_linec_pts=np_org_linec_pts.min(axis=0)

												org_linec_point=LineString(np_org_linec_pts)

												if round(org_linec_point.length)>=1:

													if round(org_line_point.distance(org_linec_point))!=0:

															z_data.append(round(org_line_point.distance(org_linec_point),2))
										if z_data !=[]:

										   tot_lot_data.append(min(z_data))

						if tot_lot_data is not None :

							if (len(tot_lot_data) ==0):

								minValue=0

							else:

								minValue=min(tot_lot_data)

							#resultsList.append(f'{org_text.text},{min(tot_lot_data)}')
							returnValueDict[org_polygon.dxf.handle]=f'{org_text.text},{minValue}'

			#for Green Strip

			# check green strip in text

			if 'Green Strip' in org_text.text:

				org_text_attribs=org_text.dxfattribs()

				insert_org_text=org_text_attribs.get('insert')

				org_text_pts=[insert_org_text[0],insert_org_text[1]]

				np_org_text_pts=np.array(org_text_pts).round(1)

				org_text_point=Point(np_org_text_pts)

				for org_polygon in orgSpacePolyEntities:#msp.query('LWPOLYLINE[layer=="_OrganizedOpenSpace"]'):

					org_polygon_pts=[o[0:2] for o in org_polygon.get_points()]

					np_org_polygon_pts=np.array(org_polygon_pts).round(1)

					org_polygon_point=Polygon(np_org_polygon_pts)

					if org_polygon_point.contains(org_text_point)==True or org_polygon_point.touches(org_text_point)==True:

						green_strip_data=[]

						# For margin line

						for insert in marginEntities:#msp.query('INSERT[layer=="_MarginLine"]'):

							# convert into lines

							for m_line in insert.virtual_entities():

								if m_line.dxftype()=='LINE':

									m_line_start_pts=[m_line.dxf.start[0],m_line.dxf.start[1]]

									m_line_end_pts=[m_line.dxf.end[0],m_line.dxf.end[1]]

									m_line_pts=[m_line_start_pts,m_line_end_pts]

									np_m_line_pts=np.array(m_line_pts).round(1)

									m_line_point=LineString(np_m_line_pts)

									if org_polygon_point.touches(m_line_point)==True or round(org_polygon_point.distance(m_line_point),1)<=0.1:

										area_of_polygon=round(org_polygon_point.area,1)

										polygon_length=round(org_polygon_point.length/2,1)

										green_strip_data.append(float(round(area_of_polygon/polygon_length)))

						if len(green_strip_data)>0:

							returnValueDict[org_polygon.dxf.handle]=f'{org_text.text},{min(green_strip_data)}'

						else:

							get_current_logger().warning(f'Green Strip {org_polygon.dxf.handle} Does Not Touch to the Plot line')
	except IndexError:

		get_current_logger().error(f'Not Found Any Value.')

		return returnValueDict

	except IOError:

		get_current_logger().error(f'Not a DXF file or a generic I/O error.')
		return returnValueDict

	except ezdxf.DXFStructureError:

		get_current_logger().error(f'Invalid or corrupted DXF file.')
		return returnValueDict

	return returnValueDict


#Fix 7/28/2022 
# Walking Distance from Room to Stairs 
#from .travel_distance import * 

def get_travel_distance(modelspace):
	returnValueDict = dict()

	try :
		if (modelspace is not None):
			return Travelled_Distance(modelspace)
		else:
			get_current_logger().error('Error Invalid input required modelspace is None ' )
			return returnValueDict

	except Exception as excp:
		get_current_logger().exception('Error getting Travel Distance from room to stairs '+str(excp))
		
		return returnValueDict

#Fix 8/1/2022 
# Podium floors setbacks Dict of Dict values 
# 	3 types of objects are returned 
#   a) Podium Floor Setbacks  #Key PODIUM_SETBACKS_RESPONSE
#   b) Podium Building Level Setbacks #Key REGULAR_SETBACK_RESPONSE
#   c) Arc Radius (if defined) #Key, PODIUM_ARC_RADIUS_RESPONSE
# CODE = 0 when success, < 0 for failure cases.  
# Failure cases : -2 for invalid input.  -1 for exception while processing & ERROR with the text 
#      
def get_podium_setbacks(modelspace):
	returnValueDict = dict()
	
	try :

		podium_set_stage='Podium Floor Setbacks'
		if (modelspace is not None):
			
			response1=check_podium_setbacks(modelspace)

			# print ( ' ** (Podium Floor)  Completed \n Response ', response1 )
			
			podium_set_stage='Podium Building Regular Setbacks'
			response2=podium_regular_setbacks(modelspace)

			# print (  ' ** (Podium Building Regular )  Completed \n Response ', response2)
			
			podium_set_stage='Arc Radius'
			response3=check_redius_of_Arc(modelspace)
			# print (  ' ** (Arc Radius )  Completed \n Response ', response3 )
			
			returnValueDict['PODIUM_SETBACKS_RESPONSE']=response1

			returnValueDict['REGULAR_SETBACK_RESPONSE']=response2

			returnValueDict['PODIUM_ARC_RADIUS_RESPONSE']=response3
			returnValueDict['CODE']=0

		else:
			msg = 'Error Invalid input required modelspace is None '
			returnValueDict['ERROR']=msg
			returnValueDict['CODE']=-2
			return returnValueDict

	except Exception as excp:
		msg = 'Problem processing Podium Setbacks failed at Step # ' + podium_set_stage + ' due to # ' + str(excp)
		get_current_logger().exception(msg)
		returnValueDict['ERROR']=msg
		returnValueDict['CODE']=-1

	return returnValueDict


#Fix 8/8/2022 -replaced full implementation with new one 
# from .cellar_setbacks_util  import check_cellar_setbacks,cellar_plinth_dist
# CODE = 0 when success, < 0 for failure cases.  
# Failure cases : -2 for invalid input.  -1 for exception while processing & ERROR with the text 
#      
def get_cellar_setbacks_plinth(modelspace):
	returnValueDict = dict()
	
	try :

		cellar_set_stage='Cellar Setbacks '
		if (modelspace is not None):
			
			response1=check_cellar_setbacks(modelspace)

			# print (' *** ' + cellar_set_stage + ' Completed \n Response ', response1 )
			returnValueDict['CELLAR_SETBACKS_RESPONSE']=response1
			


			cellar_set_stage='Cellar PLINTH '

			response2=cellar_plinth_dist(modelspace)
			# print (' *** ' + cellar_set_stage + ' Completed \n Response ', response1 )
			
			
			returnValueDict['CELLAR_PLINTH_RESPONSE']=response2

			returnValueDict['CODE']=0

		else:
			msg = 'Error Invalid input required modelspace is None '
			returnValueDict['ERROR']=msg
			returnValueDict['CODE']=-2
			return returnValueDict

	except Exception as excp:
		msg = 'Problem processing # get_cellar_setbacks_plinth - ' + cellar_set_stage + ' due to # ' + str(excp)
		get_current_logger().exception(msg)
		returnValueDict['ERROR']=msg
		returnValueDict['CODE']=-1

	return returnValueDict

#Fix 7/29/2023 
# from .ramp_check_util import RampLENGTHandBuildingHeight
# CODE = 0 when success, < 0 for failure cases.  
# Failure cases : -2 for invalid input.  -1 for exception while processing & ERROR with the text 
#      
def get_ramp_info(modelspace):
	returnValueDict = dict()
	set_stage='Ramp Info'
	response1=dict()
	try :

		
		if (modelspace is not None):
			
			response1=RampLENGTHandBuildingHeight(modelspace)

			# print (' *** ' + set_stage + ' Completed \n Response ', response1 )
			
			returnValueDict['RAMP_INFO_RESPONSE']=response1

			returnValueDict['CODE']=0

		else:
			msg = 'Error Invalid input required modelspace is None '
			returnValueDict['ERROR']=msg
			returnValueDict['CODE']=-2
			return returnValueDict

	except Exception as excp:
		msg =  set_stage + '-Error Reason  ' + str(excp)
		get_current_logger().exception(msg)
		#Fix for Abrupt ending of the program May 25 2025
		returnValueDict['RAMP_INFO_RESPONSE']=response1
		returnValueDict['ERROR']=msg
		returnValueDict['CODE']=-1

	return returnValueDict


#Fix 8/8/2022 
# from .floor_wise_setbacks import check_floor_wise_setbacks
# CODE = 0 when success, < 0 for failure cases.  
# Failure cases : -2 for invalid input.  -1 for exception while processing & ERROR with the text 
#      
def get_floor_wise_setbacks(modelspace):
	returnValueDict = dict()
	
	try :

		floorwise_set_stage='Floor Wise Setbacks'
		if (modelspace is not None):
			
			response1=check_floor_wise_setbacks(modelspace)

			# print (' *** ' + floorwise_set_stage + ' Completed \n Response ', response1 )
			
			returnValueDict['FLOORWISE_SETBACKS_RESPONSE']=response1

			returnValueDict['CODE']=0

		else:
			msg = 'Error Invalid input required modelspace is None '
			returnValueDict['ERROR']=msg
			returnValueDict['CODE']=-2
			return returnValueDict

	except Exception as excp:
		msg = 'Problem processing # get_floor_wise_setbacks - ' + floorwise_set_stage + ' due to # ' + str(excp)
		get_current_logger().exception(msg)
		returnValueDict['ERROR']=msg
		returnValueDict['CODE']=-1

	return returnValueDict

#Fix 8/8/2022 
# 	from septic_tank_util import dist_of_sept_tank
# CODE = 0 when success, < 0 for failure cases.  
# Failure cases : -2 for invalid input.  -1 for exception while processing & ERROR with the text 
#      
def get_accessory_septic_sewage_transformer_distances(modelspace):
	returnValueDict = dict()
	
	try :

		floorwise_set_stage='Accessory Use - Septic Tank, Sweage and Distribution Transformer distances from Plot '
		if (modelspace is not None):
			
			response1=dist_of_sept_tank(modelspace)

			# print (' *** ' + floorwise_set_stage + ' Completed \n Response ', response1 )
			
			returnValueDict['ACCESSORYUSE_DISTANCE_FROM_PLOT_RESPONSE']=response1

			returnValueDict['CODE']=0

		else:
			msg = 'Error Invalid input required modelspace is None '
			returnValueDict['ERROR']=msg
			returnValueDict['CODE']=-2
			return returnValueDict

	except Exception as excp:
		msg = 'Problem processing # get_floor_wise_setbacks - ' + floorwise_set_stage + ' due to # ' + str(excp)
		get_current_logger().exception(msg)
		returnValueDict['ERROR']=msg
		returnValueDict['CODE']=-1

	return returnValueDict


#Fix 9/25/2022 
# 	from building_mortgage_util import get_building_mortgage_carpetarea

# CODE = 0 when success, < 0 for failure cases.  
# Failure cases : -2 for invalid input.  -1 for exception while processing & ERROR with the text 
#      
def get_Mortgaged_CarpetArea4Buildings(modelspace):
	returnValueDict = dict()
	msg_set_stage='Get Mortaged Carpet Area Units '
	
	try :

		
		if (modelspace is not None):
			
			response1=get_building_mortgage_carpetarea(modelspace)
			code=response1.get('code',-1)
			data=response1.get('data',[])
			error=response1.get('error','N/A')
			# print ('Building Mortgage return  Code and  Error text  ', str(code ), ' error #' , str(error) )
			if (code == 0 ):
				# print (' *** ' + msg_set_stage + ' Completed \n Response ', data )
				returnValueDict['MORTGAGED_CARPETAREA_LIST']=data
				returnValueDict['CODE']=0
			elif(code == -1 ):
				error='Blank response object  '
				data=list()
				data.append(error)

				# print (' *** ' + msg_set_stage + ' Completed \n Response ', data )
				returnValueDict['MORTGAGED_CARPETAREA_LIST']=data
				returnValueDict['CODE']=-1
				returnValueDict['ERROR']=data 

			elif(code ==  1):
				#error='Problem with data extraction  -  '
				data=list()
				data.append(error)

				# print (' *** ' + msg_set_stage + ' Completed \n Response ', data )
				returnValueDict['MORTGAGED_CARPETAREA_LIST']=[]
				returnValueDict['CODE']=code
				returnValueDict['ERROR']=data 
				
			elif(code == 99 ):
				
				data=list()
				data.append(error)

				# print (' *** ' + msg_set_stage + ' Completed \n Response ', data )
				returnValueDict['MORTGAGED_CARPETAREA_LIST']=data
				returnValueDict['CODE']=99

		else:
			msg = 'Error Invalid input required modelspace is None '
			returnValueDict['ERROR']=msg
			returnValueDict['CODE']=99
			return returnValueDict

	except Exception as excp:
		msg = 'Problem processing # get_Mortgaged_CarpetArea4Buildings- ' + msg_set_stage + ' due to # ' + str(excp)
		get_current_logger().exception(msg)
		returnValueDict['ERROR']=msg
		returnValueDict['CODE']=-1

	return returnValueDict

#Fix 11/9/2022 
# from .transfer_of_setbacks_util import transfer_setbacks
# CODE = 0 when success, < 0 for failure cases.  
# Failure cases : -2 for invalid input.  -1 for exception while processing & ERROR with the text 
#      
def get_transfer_of_setbacks(modelspace):
	returnValueDict = dict()
	
	try :

		msg_set_stage='Transfer Of Setbacks'
		if (modelspace is not None):
			
			response1=transfer_setbacks(modelspace)

			# print (' *** ' + msg_set_stage + ' Completed \n Response ', response1 )
			
			returnValueDict['TRANSFER_OF_SETBACKS_RESPONSE']=response1

			returnValueDict['CODE']=0

		else:
			msg = 'Error Invalid input required modelspace is None '
			returnValueDict['ERROR']=msg
			returnValueDict['CODE']=-2
			return returnValueDict

	except Exception as excp:
		msg = 'Problem processing # get_transfer_of_setbacks - ' + msg_set_stage + ' due to # ' + str(excp)
		get_current_logger().exception(msg)
		returnValueDict['ERROR']=msg
		returnValueDict['CODE']=-1

	return returnValueDict


#Fix 5/27/2023 - Merge two array of Dictionaries and returns a Pandas Dataframe 

def merge_netbua (inputArray1:[], inputArray2:[] , joinType:str="outer"):
	
	#ARRAY LIST of DICT 
	details_df= pd.DataFrame(inputArray1)
	floor_df =pd.DataFrame(inputArray2)

	floor_df.rename(columns={'FLOOR':'FLOOR_NAME'}, inplace=True)
	
	details_df['BLDG_NAME']=details_df['BLDG_NAME'].str.replace(' ', '') 
	
	merged_df = details_df.merge(floor_df, on=['BLDG_NAME', 'FLOOR_NAME'], how='outer' ) #'left')
	# print('Merged JSON for NETBUA Calc .... ')
	# print(merged_df)

	#merged_df.to_json('merged_netbua.json', orient='records')

	#merged_df.to_csv('merged_netbua.csv', index=False)
	return merged_df


#Fix 8/16/2023 - CommonFloorSetbacks -  
#from CommonFloorSetbacks import *
def commonfloor_setbacks (msp):
	returnValueDict = dict()
	
	try :

		msg_set_stage='GET CommonFloorSetbacks since 8/16/2023 '
		if (msp is not None):

			obj=CommomFloorSetbacks()
			response1 = obj.FloorSebacks(msp)
			
			
			# print('>>>>>>>>>>>>>>>>  Response  CommonFloorSetbacks since 8/16/2023  ', response1)
			#print (' *** ' + msg_set_stage + ' Completed \n Response ', response1 )
			if (len (response1) >0 ):
				codeValue=0
			else:
				codeValue=-3
			#codeValue = response1.get('code',-3)
			
			if (codeValue == 0 ):

				returnValueDict['DATA']=response1
				returnValueDict['CODE']=codeValue
			else:
				
				returnValueDict['ERROR']=response1.get('msg','N/A')
				returnValueDict['CODE']=codeValue
			
			return returnValueDict

	except Exception as excp:
		msg = 'Problem processing # get_transfer_of_setbacks - ' + msg_set_stage + ' due to # ' + str(excp)
		get_current_logger().exception(msg)
		returnValueDict['ERROR']=msg
		returnValueDict['CODE']=-1

	return returnValueDict


def get_area_by_bua_type_voids_accessory(modelspace):
	returnValueDict = dict()
	
	try :

		msg_set_stage='GET BUA BY TYPE - ACCESSORY VOIDS VENTISHAFT '
		if (modelspace is not None):
			
			response1=check_resibua_and_commbua_tot_area(modelspace)
			# print('>>>>>>>>>>>>>>>>  check_resibua_and_commbua_tot_area  ', response1)
			#print (' *** ' + msg_set_stage + ' Completed \n Response ', response1 )
			codeValue = response1.get('code',-3)
			if (codeValue == 0 ):

				returnValueDict['AREA_VOID_ACCESS_BYBUA_RESPONSE']=response1.get('data',[])
				returnValueDict['CODE']=codeValue
			else:
				
				returnValueDict['ERROR']=response1.get('msg','N/A')
				returnValueDict['CODE']=codeValue
			
			return returnValueDict

	except Exception as excp:
		msg = 'Problem processing # get_transfer_of_setbacks - ' + msg_set_stage + ' due to # ' + str(excp)
		get_current_logger().exception(msg)
		returnValueDict['ERROR']=msg
		returnValueDict['CODE']=-1

	return returnValueDict

def groundlevel_check_latest(msp):

	returnValueDict={}

	resultsList=[]

	if (msp is None):

		return returnValueDict

	#dxf_path=os.path.join(folder,filename)

	try:

		#read_dxf=ezdxf.readfile(dxf_path)

		#print('read file')

		#msp=read_dxf.modelspace()

		duplicateList=[]
		errorList=[]

		b_dict=dict()
		b_nameDict=dict()
		#Always read outside any for loop !!! 
		startTimer=timer()

		bldgTextLayerEntities=msp.query('TEXT[layer=="_BuildingName"]')
		bldgPolyLayerEntities=msp.query('LWPOLYLINE[layer=="_BuildingName"]')
		glPolyLayerEntities=msp.query('LWPOLYLINE[layer=="_GroundLevel"]')
		fisPolyLayerEntities=msp.query('LWPOLYLINE[layer=="_FloorInSection"]')
		fisTextLayerEntities=msp.query('TEXT[layer=="_FloorInSection"]')

		queryTimer=timer()
		for b_name in bldgTextLayerEntities:#msp.query('TEXT[layer=="_BuildingName"]'):

			b_name_txt=b_name.dxfattribs()
			b_handle=b_name_txt.get('handle','-')
			#print('name and handle for building ', b_name_txt, ' , ', b_handle)
			b_name_txt_pts=b_name_txt['insert']

			b_name_txt_coords=np.array([b_name_txt_pts[0],b_name_txt_pts[1]]).round(2)

			building_text_point=Point(b_name_txt_coords)

			for b_poly in bldgPolyLayerEntities:# msp.query('LWPOLYLINE[layer=="_BuildingName"]'):

				b_poly_pts=[p[0:2] for p in b_poly.get_points()]

				b_poly_coords=np.array(b_poly_pts).round(2)

				building_poly=Polygon(b_poly_coords)

				if building_poly.contains(building_text_point)==True:
					tmpBldgDict=dict()
					tmpBldgDict['poly']=building_poly
					tmpBldgDict['handle']=b_handle

					b_dict[b_name.dxf.text]=tmpBldgDict
					#b_nameDict[b_name.dxf.text]=b_handle


		for buildingName,buildingValues in b_dict.items():

			bldgPoly= buildingValues['poly']
			b_handle= buildingValues['handle']
			
			building_block_poly=Polygon(bldgPoly)

			block_value=[]

			for gl_line in glPolyLayerEntities:#msp.query('LWPOLYLINE[layer=="_GroundLevel"]'):
				gl_id=gl_line.dxf.handle
				try:
					

					gl_line_pts=[x[0:2] for x in gl_line.get_points()]

					gl_line_coords=LineString(np.array(gl_line_pts).round(2))

					for section_floor_name in fisTextLayerEntities:# msp.query('TEXT[layer=="_FloorInSection"]'):

						text_pts=section_floor_name.dxfattribs()
						floorText=text_pts['text'].strip()
						if floorText == 'TERRACE FLOOR':

							terrace_pts=text_pts['insert']

							terrace_text_pts=Point(np.array([terrace_pts[0],terrace_pts[1]]).round(2))

							for section_floor_poly in fisPolyLayerEntities:#msp.query('LWPOLYLINE[layer=="_FloorInSection"]'):

								poly_section_floor_pts=[x[0:2] for x in section_floor_poly.get_points()]

								poly_section_floor_coords=np.array(poly_section_floor_pts).round(2)

								section_poly=Polygon(poly_section_floor_coords)

								if section_poly.contains(terrace_text_pts)==True:

									if building_block_poly.contains(gl_line_coords)==True and building_block_poly.contains(section_poly)==True:
										gl_value_tmp=round(gl_line_coords.distance(section_poly),2)
										#block_value.append(f'{gl_id},{gl_height}')
										#duplicate buildings will be caught and reported as warnings
										if (returnValueDict.get(b_handle,0) == 0):
											returnValueDict[b_handle]=buildingName + '|' + gl_id + '|' + str(gl_value_tmp)
										else:
											duplicateList.append(f"Duplicate Building {buildingName}  with same Reference# {b_handle}")
				except:
					gl_msg='problem calculating building height for reference ' + str(gl_id) 
					# print (gl_msg)
					errorList.append(gl_msg)
					continue 

		if (len(duplicateList)> 0):
			returnValueDict['duplicateList']=duplicateList
		
		if (len(errorList)> 0):
			returnValueDict['errorList']=errorList

		endTimer=timer()
		# print('Total Time ', str(round(endTimer-startTimer,2)) , ' sec ')
		# print('Query Time ', str(round(queryTimer-startTimer,2)) , ' sec ')
		# print('Core Logic Time ', str(round(endTimer-queryTimer,2)) , ' sec ')

		return returnValueDict

	except IOError:

			 get_current_logger().error(f'Not a DXF file or a generic I/O error.')

			 return returnValueDict

	except ezdxf.DXFStructureError:

			 get_current_logger().error(f'Invalid or corrupted DXF file.')

			 return returnValueDict

def window_check_util(msp):

	returnValueDict={}
	resultsList=[]

	if (msp is None):
		return returnValueDict

	
	returnValueDict=dict()
	if (msp is None): 
		returnValueDict['CODE']=-1
		returnValueDict['ERROR']='Invalid Inputs. Valid Modelspace required but is None'

		return returnValueDict
	else:
		try :

			response1 = window_check(msp)
			returnValueDict['RESULTS']=response1
			returnValueDict['CODE']=0
		except  :
			# printLog('error','Unable to extract Room Ventilation '
			# 	)
			get_current_logger().error('Unable to extract Room Ventilation ')
			returnValueDict['CODE']=-2
			returnValueDict['ERROR']='Exception occurred while trying to run roomutil2 '

	return returnValueDict

def check_balcony_maindoor(modelspace):

	returnValueDict={}

	if (modelspace is None):

		return returnValueDict

	#dxf_path=os.path.join(folder,filename)

	try:

		#read_dxf = ezdxf.readfile(dxf_path)

		#print('read file')

		#msp = read_dxf.modelspace()

		group = modelspace.groupby(dxfattrib='layer')

		#print('group', len(group))
		#balconyEntities = group.get('_Balcony')
		#doorEntities = group.get('_Door')
		#stairCaseEntities = group.get('_StairCase')
		 

		#print('Balcony entity cnt ' ,  len(balconyEntities )  , ' \n door entity cnt ', len(doorEntities ), ' \n Stair Case entity cnt ', len(stairCaseEntities))
		

		#passageLayerItems = modelspace.query('*[layer =="_Passage"]')

		for layers, entities in group.items():

			if layers == '_Balcony':

				for entity1 in entities:

					balcony_id = entity1.dxf.handle

					if entity1.dxftype() == 'LWPOLYLINE':

						if len(entity1.get_points()) > 2:

							lstx = [p[0:2] for p in entity1.get_points()]

							polyx = Polygon(lstx)

							balcony_list = []

							for layers, entities in group.items():

								if layers == '_Door':

									dctx = {}

									door_name = list(filter(lambda n: n.dxftype() == 'TEXT' or n.dxftype() == 'MTEXT', entities))

									i = 0

									for entity2 in entities:

										if entity2.dxftype() == 'LWPOLYLINE':

											try:

												dctx[door_name[i]] = entity2

												i += 1

											except IndexError:
												pass

									door_list = []

									for key, values in dctx.items():

										k1 = key.dxf.text if key.dxftype() == 'TEXT' else key.text

										if k1 == 'MD' or k1 == 'M/D':

											md_list = [q[0:2] for q in values.get_points()]

											polyy = Polygon(md_list)

											if polyx.touches(polyy) == True or round(polyx.distance(polyy), 1) == 0.0:

												for layers, entities in group.items():

													if layers == '_StairCase':

														stair_list = []

														for entity3 in entities:

															if entity3.dxftype() == 'LWPOLYLINE':

																if len(entity3.get_points())>= 4:

																	lst3 = [z[0:2] for z in entity3.get_points()]

																	polyz = Polygon(lst3)

																	stair_list.append(round(polyy.distance(polyz), 2))

														if stair_list == []:

															stair_list.append(False)

														door_list.append(min(stair_list))

									if door_list == []:

										door_list.append(False)

									balcony_list.append(door_list)

						if balcony_list == []:

							balcony_list.append(False)

						returnValueDict[balcony_id]=balcony_list


	except IOError:

			get_current_logger().error(f'Not a DXF file or a generic I/O error.')
			return returnValueDict

	except ezdxf.DXFStructureError:
		get_current_logger().error(f'Invalid or corrupted DXF file.')
		return returnValueDict

	return returnValueDict

def window_in_passage_check(modelspace):

	returnValueDict={}

	resultsList=[]

	if (modelspace is None):

		return returnValueDict

	#dxf_path=os.path.join(folder,filename)

	try:

		#read_dxf=ezdxf.readfile(dxf_path)

		#print('read file')

		#msp=read_dxf.modelspace()

		group=modelspace.groupby(dxfattrib='layer')

		# print('group',len(group))

		#color=[]

		xa=[]
		for layers,entities in group.items():
			if layers=='_Passage':
				for entity1 in entities:
					if entity1.dxftype()=='LWPOLYLINE':
						if len(entity1.get_points())>=4:
							passage_id=entity1.dxf.handle
							lstx=[x[0:2] for x in entity1.get_points()]
							poly1=Polygon(lstx)
							passage_list=[]
							for layers,entities in group.items():
								if layers=='_Window':
									window_list=[]
									for entity2 in entities:

										if entity2.dxftype()=='LWPOLYLINE':
											if len(entity2.get_points())==4:
												lsty=[y[0:2] for y in entity2.get_points()]
												poly2=Polygon(lsty)
												if round(poly1.distance(poly2),2)==0.0:
													window_list.append(True)
												else:
													window_list.append(False)
									if True in window_list:
										passage_list.append(True)
									else:
										passage_list.append(False)
							if passage_list!=[]:
								passage_data=f'{passage_id},{passage_list}'
								resultsList.append(passage_data)
								returnValueDict[passage_id]=passage_list

	except IOError:

		get_current_logger().error(f'Not a DXF file or a generic I/O error.')
		return returnValueDict

	except ezdxf.DXFStructureError:

		get_current_logger().error(f'Invalid or corrupted DXF file.')
		return returnValueDict

	return returnValueDict

def convertListToStr(inputList:list, delimeter:str="|"):

	returnValue=""

	if (inputList is None or len(inputList) == 0  ):
		return returnValue

	for itr in inputList :
		returnValue += str(itr) + delimeter

	return returnValue

def door_to_staircase_distance(modelspace):

	returnValueDict={}

	resultsList=[]

	if (modelspace is None):#folder is None or filename is None

		return returnValueDict

	#dxf_path=os.path.join(folder,filename)

	try:

		#read_dxf = ezdxf.readfile(dxf_path)

		#print('read file')

		#msp = read_dxf.modelspace()
		passageLayerItems = modelspace.query('*[layer =="_Passage"]')
		doorLayerItems = modelspace.query('*[layer =="_Door"]')
		doorPolyItems = modelspace.query('LWPOLYLINE[layer =="_Door"]')
		stairPolyItems = modelspace.query('LWPOLYLINE[layer=="_StairCase"]')

		for entity1 in passageLayerItems:#modelspace.query('*[layer=="_Passage"]'):

			if entity1.dxftype() == 'LWPOLYLINE':

				if len(entity1.get_points()) >= 4:

					passage_id = entity1.dxf.handle

					lst1 = [x[0:2] for x in entity1.get_points()]

					poly1 = Polygon(lst1)

					dct1 = {}

					Door_name = []

					i = 0

					for entity2a in doorLayerItems:#modelspace.query('*[layer=="_Door"]'):

						if entity2a.dxftype() == 'TEXT' or entity2a.dxftype() == 'MTEXT':

							Door_name.append(entity2a)

					for entity2b in doorPolyItems:#modelspace.query('LWPOLYLINE[layer=="_Door"]'):

						if len(entity2b.get_points()) == 4:

							try:

								dct1[Door_name[i]] = entity2b
								i += 1
							except IndexError:

								pass

					door_list = []

					for key, value in dct1.items():

						k1 = key.dxf.text if key.dxftype() == 'TEXT' else key.text

						if k1 == 'M/D' or k1 == 'MD':

							lst2 = [y[0:2] for y in value.get_points()]

							poly2 = Polygon(lst2)

							if poly1.touches(poly2) == True or round(poly1.distance(poly2), 1) == 0.0:

								stair_list = []

								for entity3 in stairPolyItems:#modelspace.query('LWPOLYLINE[layer=="_StairCase"]'):

									if len(entity3.get_points()) >=4:

										lst3 = [z[0:2] for z in entity3.get_points()]

										poly3 = Polygon(lst3)

										stair_list.append(round(poly2.distance(poly3), 2))

								if stair_list != []:

									door_list.append(round(min(stair_list), 2))

								else:
									door_list.append('--')

					if door_list == []:

						door_list.append('--')

					returnValueDict[passage_id]=convertListToStr(door_list)

	except IOError:

		get_current_logger().error(f'Not a DXF file or a generic I/O error.')

		return returnValueDict

	except ezdxf.DXFStructureError:

		 get_current_logger().error(f'Invalid or corrupted DXF file.')

		 return returnValueDict

	return returnValueDict

def getPurposeDesc (purposecode:str  ):
	returnValue = 'N/A'
	if (purposecode is None):
		return returnValue
	else:
		pcodeMap=LayerMaster.PURPOSE_CODE_DESC_MAP.value
		return pcodeMap.get(purposecode,'N/A')

def getCategoryForParking(request_params:dict):
	#	#GHMC vs HMDA/Others 
	# Category 1 ['Multiplexes','Shopping Malls','ITES'] & Location = GHMC Parking : 60% else 50%  
	#

	# Category 2 ['Hotels', 'Restaurants', 'Lodges', 'Cinema halls', \
	#			  'Business buildings', 'Other Commercial buildings', 'Kalyana Mandapams', 'Offices','Non-Residential'] 
	#			 & Location = GHMC Parking : 40% else 30%  
	
	# Category 3 'Residential', 'Apartment Complexes', 'Hospitals', 'Institutional buildings', 'Industrial buildings', \
	#			'Schools', 'Colleges', 'Other Educational Buildings' & 'Godowns', 'Others']
	#			& Location = GHMC Parking : 30% else 20%  
	#category value to be passed 
	#location type to be passed GHMC, HMDA etc 
	category1_list= ['Multiplex','Shopping','Mall','ITES']
	category2_list= ['Hotel', 'Restaurant', 'Lodge', 'Cinema hall', \
					'Business building', 'Commercial', 'Kalyana Mandapam', 'Offices','Non-Residential'] 
	category3_list=['Residential', 'Apartment Complexes', 'Hospitals', 'Institutional', 'Industrial', \
				'Schools', 'Colleges', 'Educational' , 'Godown', 'Others']
	

	subuse=request_params.get('subuse','N/A')
	purposecode=request_params.get('purposecode','N/A')


	if (subuse in category1_list ) :
		return "CAT1"
	elif (subuse in category2_list ) :
		return "CAT2"
	elif (subuse in category3_list ) :
		return "CAT3"
	else :
		return "CAT3"

def getSetBacksByMidPoints(plotObj:Polygon, bldObj:Polygon):

	from shapely.geometry import Point, LinearRing
	from shapely.ops import nearest_points
	setBackDict= dict()

	poly = plotObj  #Polygon([(0, 0), (2,8), (14, 10), (6,1)])
	bld_ext = LinearRing(bldObj.exterior.coords)
	pol_ext = LinearRing(poly.exterior.coords)
	
	x1,y1,x2,y2 = bldObj.bounds
	# print("bldg bounds minxx:" + str(x1) + " maxx:" + str(x2) + " miny:" + str(y1) + " maxy:" + str(y2) )
	#convert to points array minx [00,maxx[1], miny[2],maxy[3]  
	midOfx = round((x1+x2)/2,2)
	midOfy = round((y1+y2)/2,2)
	# print ("Mid of x and y are " + str(midOfx)  + " , " + str(midOfy))

	points = [Point(midOfx, y1), Point(x2, midOfy), Point(midOfx,y2), Point(x1,midOfy)]
	# for p in points:
		# print("points :" + str(p.coords.xy) )

	for point in points:
		
		np = nearest_points(pol_ext, point)[0]
		distance=round(point.distance(np),2)
		# print("source " + str(point)   +  " to " + str(np) + " distance is " + str(distance )  )
		setBackDict[str(point)]=distance
	
	sorted_x = sorted(setBackDict.values(),reverse=True)
	newSBDict=dict()

	idx=0
	#@TODO: FIX by MARGIN LINE COLOR CODE FOR GETTING FRONT REAR
	if (len(sorted_x) == 4 ):
		newSBDict['proposed_front_setback']= sorted_x[idx]
		newSBDict['proposed_rear_setback']= sorted_x[idx+1]
		newSBDict['proposed_side1_setback']= sorted_x[idx+2]
		newSBDict['proposed_side2_setback']= sorted_x[idx+3]
		
		return newSBDict

	else:
		#just return unformatted results 
		setBackDict


""" 
check from a list of liftpoints if it is part of a terrace polygon and returns the height. 
this will be added to the floorsec item /lift 

"""
def checkLiftHeight(liftpoints:list, floorPoly:Polygon ):

	translation = {39: None} 
	
	for liftpoint in liftpoints:
	
		#liftpoint=['7744.982628334024 -322.096752772895', '7747.111091212717 -322.096752772895', '7747.111091212717 -324.6867527728961', '7744.982628334024 -324.6867527728961', '7744.982628334024 -322.096752772895']
		
		lpolyStr= str(liftpoint.get_points())[1:-1].translate(translation)
		
		liftPolyStr = 'POLYGON (('  + lpolyStr  + '))'

		liftPoly = shapely.wkt.loads( liftPolyStr )

		# floorInSectionPoly='POLYGON ((7738.124628334013 -323.6867527728961, 7764.179891212716 -323.6867527728961, 7764.179891212716 -324.6867527728961, 7738.124628334013 -324.6867527728961, 7738.124628334013 -323.6867527728961))'
		# floorPoly = shapely.wkt.loads( floorInSectionPoly )
		floorHasLift = floorPoly.intersects(liftPoly)
		if (floorHasLift):
			# print(" floor contains lift  " + str(floorHasLift) )
			
			# get minimum bounding box around polygon
			box = liftPoly.minimum_rotated_rectangle
			# get coordinates of polygon vertices
			x, y = box.exterior.coords.xy
			# get length of bounding box edges
			edge_length = (Point(x[0], y[0]).distance(Point(x[1], y[1])), Point(x[1], y[1]).distance(Point(x[2], y[2])))
			# get length of polygon as the longest edge of the bounding box
			length = round(max(edge_length),2)
			# get width of polygon as the shortest edge of the bounding box
			width = round(min(edge_length),2)

			# print("area " + str(box.area ))
			# print("width " + str(width ) )
			# print("height " + str(length) )
			return length
	#if no match return 0.0 
	return 0.0     




"""
Extracts the Total Building Height and Floor Heights from a given Dataframe 
 Total Building Height = PLINTH + STILT+ FLOOR 
 FLOOR HEIGHT = FLOOR Height 
 EXCLUSIONS: BASEMENT and LIFT MAN HEIGHT NOT INCLUDED 

"""
def getBuilding_Floor_Heights(pd_dataframe,projecttype:str=None):
	
	if (pd_dataframe is None):
		return None

	# print('input getBuilding_Floor_Heights', pd_dataframe)
	# Fix: Feb 19 2022 exclude STILT by default. Include for Height calculation for MSBR only 
	# or (excludeList is not None and len(excludeList)>0)
	#
	if (projecttype in "HIGHRISE_MSBR" ) :
		exclude=['BASEMENT', 'TERRACE']
	else:
		exclude=['BASEMENT', 'TERRACE', 'STILT']	
	
	#step 1. get floor height 
	subtype_df=pd_dataframe[['parent','subtype','height']]

	whitelist_heights=['FLOOR', 'PLINTH']

	#floorOnly_df=subtype_df[subtype_df['subtype'] == 'FLOOR']
	floorOnly_df=subtype_df[subtype_df['subtype'].isin(whitelist_heights)]
	# print("Only Floors ")
	floorSum=floorOnly_df.groupby(['parent']).agg(Floor_Height=pd.NamedAgg(column="height", aggfunc="sum"))
	# print(floorSum)
	
	#step 2. get building height 
	# print("Building Height except basement ")
	mask_basement_terrace=subtype_df['subtype'].isin(exclude)
	except_basement_df=subtype_df[~mask_basement_terrace]
	#except_basement_df=subtype_df[subtype_df['subtype'] != 'BASEMENT']

	bldgSum=except_basement_df.groupby(['parent']).agg(Building_Height=pd.NamedAgg(column="height", aggfunc="sum")) #{'height': 'sum'}) 
	# print(bldgSum)

	#3 merge the dataframes 
	# print('Final table ')
	mergeddf=pd.merge(floorSum,bldgSum,on='parent',how='inner')
	
	mergeddf.reindex()
	# print (mergeddf)
	return mergeddf


def enrichStairsData(df):

	# printLog('verbose',"dataframe ... input ")
	df.head()

	df = df.sort_values(by=['stairId', 'x1','y1','x2','y2'])

	stairscol=df[['stairId']]

	points_df=df[['x1','y1','x2','y2']]
	
	points_df["x1"]=pd.to_numeric(df["x1"], downcast="float")
	points_df["y1"]=pd.to_numeric(df["y1"], downcast="float")
	points_df["x2"]=pd.to_numeric(df["x2"], downcast="float")
	points_df["y2"]=pd.to_numeric(df["y2"], downcast="float")

	# print(points_df)
	#'stairId',
	diff_df=round(abs(points_df.diff()),2)
	# print("abs values")
	# print(diff_df)
	diff_df=pd.merge(stairscol,diff_df,left_index=True,right_index=True)

	#disabled tocsv #FIX 10/25/2023
	#diff_df.to_csv("vanilla_merge_diff_stairs.csv")

	#replace 0, .15 with higher number so they will not get picked in min function 
	
	#3/2/22 disabled 2 lines 
	diff_df=diff_df.replace(0, np.NaN)
	diff_df.loc[diff_df['x1'] > 1, 'x1'] = np.NaN
	diff_df.loc[diff_df['y1'] > 1, 'y1'] = np.NaN
	diff_df.loc[diff_df['x2'] > 1, 'x2'] = np.NaN
	diff_df.loc[diff_df['y2'] > 1, 'y2'] = np.NaN

	#diff_df=diff_df.replace(0.66,np.nan)
	#diff_df=diff_df.replace(0.15,0.67)
	# print("difference of between rows after replace 0.0 to .66")
	# print("after replace of values ")
	# print(diff_df)
	#disabled tocsv #FIX 10/25/2023
	#diff_df.to_csv("after_replace_vanilla_merge_diff_stairs.csv")

	diff_df=pd.merge(stairscol,diff_df,left_index=True,right_index=True)
	# print("after temp pd merge ")
	# print(diff_df)

	#disabled tocsv #FIX 10/25/2023
	#diff_df.to_csv("diff_vanilla_merge_diff_stairs.csv")
	min_df=diff_df.min(axis=1)
	
	#disabled tocsv #FIX 10/25/2023
	#min_df.to_csv("min_df_vanilla_merge_diff_stairs.csv")
	
	minAsDf=min_df.to_frame()
	minAsDf['min of x or y']=minAsDf[0]

	
	real_values= pd.merge(df,minAsDf,left_index=True, right_index=True )


	return real_values

def extractRiserTread(df,floorheight:float=2.99):


	df = df.drop(['color','lineId','x1','y1','x2','y2','flightwidth'], axis=1)
	df.set_index('stairId')
	stair_count = df.groupby('stairId').size()
	
	#3/2/2022 replaced data with df 
	riser_count = df.groupby('stairId').size()
	stair_avg = df.groupby('stairId').mean()

	stair_avg = stair_avg.drop(0, axis=1)

	total_df = pd.DataFrame()
	total_df = pd.concat([stair_count, riser_count, stair_avg], axis=1).reset_index()

	total_df = total_df.rename(columns={0:'total_count',1:'riser_count',
									'min of x or y': 'tread_width'})
	#Fix 06/29/2025 3FL Stairs issue 
	#adding original riser_count 
	total_df['raw_riser_count']=total_df['total_count'] +1

	total_df.loc[total_df['total_count']//total_df['riser_count']<2 , 'riser_count'] = total_df['total_count']//2


	total_df['riser_count'] = total_df['riser_count']

	# print("after adjusting riser cnt ")
	# print(total_df)

	total_df['no_of_flights'] = total_df.loc[:,'total_count']//total_df.loc[:,'riser_count']
	# print("no of fligts")
	# print(total_df['no_of_flights'])

	#12/30/2021 fix for riser count off by 1  -- removed +1 3/2/2022
	total_df['riser_count'] = total_df['riser_count']

	total_df['floor_height'] = floorheight
	# print(total_df)
	total_df['riser_height'] = total_df['floor_height']/total_df['riser_count']/total_df['no_of_flights']
	total_df['riser_height'] = total_df['riser_height'].round(2)

	return total_df


def cleanStairsData(df):

	#convert to numerics 
	df["color"]=pd.to_numeric(df["color"], downcast="float")
	df["x1"]=pd.to_numeric(df["x1"], downcast="float")
	df["y1"]=pd.to_numeric(df["y1"], downcast="float")
	df["x2"]=pd.to_numeric(df["x2"], downcast="float")
	df["y2"]=pd.to_numeric(df["y2"], downcast="float")
	
	before_cnt=df.groupby('stairId').size()
	
	df = df.sort_values(by=['stairId', 'x1','y1','x2','y2'])
	df.reindex()
	# print("columns ", df.columns)

	return df


"""
Input: 

Stair Case stairResult. output from extractSubPlot(mspdwg, layerToSearch, lineType,False,False) 
layerToSearch=LayerMaster.STAIRCASE.value 
lineType=LayerMaster.DWG_LWPOLYLINE.value]

Extracts the stair case details 
 a) Tread Width (step depth) 
 b) Riser Count (# of steps) 
 c) Riser Height (step height) 

Returns a dataframe by stair id 


"""

def getTimeDiff(startTimer,endTimer):
	try :
		# print('total time ', str(round(endTimer-startTimer,2)) , ' sec ')
		return str(round(endTimer-startTimer,2)) + ' sec'
	except Exception as excp:
		get_current_logger().error(f"problem extracting time difference from input values {startTimer},{endTimer} due to {excp}")
		return '-1'


# V1.0 
def processStairsDataNew(stairResult):
	if (stairResult is None ): 
		return None 

	uniqueClosedDict=dict()
	uniqueLinesDict=dict()

	#split closed and open lines
	for dxfP in stairResult:
		if (dxfP.isClosed()):
			# print("processing handle" + dxfP.handle)
			if (uniqueClosedDict.get(dxfP.handle,0) ==0):
				# print("\t added " + str(dxfP.to_dict()))
				uniqueClosedDict[str(dxfP.handle)]=dxfP
		else:
			if (uniqueLinesDict.get(dxfP.handle,0) ==0):
				uniqueLinesDict[dxfP.handle]=dxfP

	# printLog('debug',"closed Object count " , len(uniqueClosedDict))
	# printLog('debug',"open lines count " , len(uniqueLinesDict) )

	#create closed polygons 
	stairPolygonsDict=dict()
	# printLog('debug',"Stairs poly")
	for stairK,stairP in uniqueClosedDict.items():
			spoints = stairP.get_points()
			translation={39:None}
			spolyStr=str(spoints)[1:-1].translate(translation)

			stairPolyStr = 'POLYGON (('  + spolyStr  + '))'
			stairPoly = shapely.wkt.loads( stairPolyStr )
			stairPolyCoords = list(stairPoly.exterior.coords)
			stairPolyRcoords=re_round(stairPolyCoords,4)
			stairPolygonsDict[stairK]=Polygon(stairPolyRcoords)
			# print("adding polygon " + stairPolyStr )

	stairsDetailsDict=dict()  # key , value:  no of lines/treads, avg. distance between two lines, avg. width of line 
	#loop through each line and slot them 
	# printLog('debug',"lines ")
	for lineK,lineP in uniqueLinesDict.items():
		lpoints = lineP.get_points()
		lpolyStr=str(lpoints)[1:-1].translate(translation)
		# printLog('debug',"lpolyStr  " + str(lpolyStr))
		aspoints=lpolyStr.split(",")
		if (aspoints is None or len(aspoints) ==0 ):
			break 

		startPoint=aspoints[0]
		endPoint =aspoints[1]
		# print("start:" + startPoint)
		# printLog('debug',startPoint.strip().split(" ") )
		# print("end:" + endPoint)
		# printLog('debug',endPoint.strip().split(" ") )
		
		x1,y1=startPoint.strip().split(" ")
		x2,y2=endPoint.strip().split(" ")
		x1=str(round(float(x1),2))
		y1=str(round(float(y1),2))
		x2=str(round(float(x2),2))
		y2=str(round(float(y2),2))
		
		linePoly = 'LINESTRING ('  + lpolyStr  + ')'
		line = shapely.wkt.loads(linePoly)
		llength = str(round(line.length,2))
		# printLog('debug',lpolyStr + " with length >>>>"  )

		for stairK,stairP1 in stairPolygonsDict.items():
			if (stairP1.intersects(line) or line.touches(stairP1) ):
				# printLog('debug',"line #" + str(line)  + " belongs to #" + str(stairP1)  )
				if (int(lineP.getColor()) >=256 ):
					stairsDetailsDict[lineK]= stairK + "," + lineK + "," + str(lineP.getColor()) + "," + x1 + "," + y1 + "," + x2 + "," + y2 +  "," + llength 
	# printLog('debug',"stairsDetails \n" + str(stairsDetailsDict))

	listOfTuple=list()
	for value in stairsDetailsDict.values():
		record=value.split(',')
		listOfTuple.append(record)
	   

	df = pd.DataFrame(data=listOfTuple,columns=['stairId','lineId','color','x1','y1','x2','y2','flightwidth'])

	df= cleanStairsData(df)

	stairstempDf=enrichStairsData(df)


	# printLog('debug',"stairs enriched data \n ")
	# print(stairstempDf)

	stairsFinalDf=extractRiserTread(stairstempDf,2.99) 
	# printLog('debug',"stairs riser data ===> \n")
	# printLog('debug', stairsFinalDf)

	return stairsFinalDf  



"""
Since 11/20/2020 for Floor Height For a given Stair 
Function correlates the floor height from FloorInSection , FloorStairMapping and StairsIdFloorDict 
and returns a height for a given stairid

1) floorInSectionSortedDict: Sorted Dictionary, Floor names in FloorInSection have below naming convention :
	'E(PROPOSED)|STILT-3FLOOR'  :  3.14,
	'E(PROPOSED)|THIRDFLOOR':2.99,

2) FLOORS are expanded to the ordinal names when there is a TYPICAL FLOOR PLAN in the Building Report 
'E (PROPOSED)|STILT -3 FLOOR PLAN':'E(PROPOSED)|STILT-3FLOORPLAN',
'E (PROPOSED)|THIRD FLOOR PLAN':'E(PROPOSED)|TYPICAL-3,4,5,6,7,8FLOORPLAN',

3) Stairs in the Floor have different naming convention (example  TYPICAL - 3,4,..8 FLOOR PLAN )
	'43034E':'E(PROPOSED)|TYPICAL-3,4,5,6,7,8FLOORPLAN',
	'4646DBB8':'E(PROPOSED)|STILT-3FLOORPLAN',


Output will be 
	{
	"status" :string # OK or NOTOK One value is mandatory 
	"data" : dict, #{'43034E':2.99,'4646DBB8':3.14}   #when Status is OK else empty 
	"errormsg": list # ['xyz not found defaulted to 2.99'] #Based on data validation failures or Exceptions occur else empty  
	}
 
"""
def extractStairsHeightInfo(floorInSectionSortedDict:dict,floorAndStairFloorMapping:dict, stairsIdFloorDict:dict):

	if (floorInSectionSortedDict is None or len(floorInSectionSortedDict)==0 \
		or floorAndStairFloorMapping is None or len(floorAndStairFloorMapping)==0 \
		or stairsIdFloorDict is None or len(stairsIdFloorDict)==0 ):
		msg="Invalid inputs one or more items are Empty "
		# print(" " + msg )
		return {"status": "NOTOK", "data":{},"errormsg": [msg] }


	stairsHeightDict=dict()
	default_height_value=2.99
	errorList=[]
	try:    
		#step#1 get the Floor height mapped to the stair floor name 
		# printLog('debug',"inputs keys "+ str(floorInSectionSortedDict.keys()) )
		for skey,sval in floorAndStairFloorMapping.items():
			stair_clean_str=sval.replace(" ","")
			

			if (stair_clean_str not in stairsHeightDict):

				keyToFind=skey.replace(" ","").replace("PLAN","")
				nresult=floorInSectionSortedDict.get(keyToFind,"N/A")
				
				# printLog('verbose',"searched " + keyToFind+ "=" + str(nresult))
				#check result
				if (nresult !="N/A" and len(stair_clean_str)>0):
					stairsHeightDict[stair_clean_str]=nresult
				else:
					stairsHeightDict[stair_clean_str]=default_height_value
					notfound=""
					if (nresult != "N/A"):
						notfound += " Unable to find floor #" + keyToFind +  " using default value#" + str(default_height_value)
					if (len(stair_clean_str)==0 ):
						notfound+= " Invalid value for 2nd key# " + stair_clean_str
					# printLog('debug', notfound)
					errorList.append(notfound)

		#format stair floorname, height     
		# printLog('debug',"Floor Height Mapped to Stair's Floor Name ")
		
		if (len(stairsHeightDict)>0):

			#step#2 map the stair floor height with the stairId 
			#use items from stairsIdFloor to lookup in stairsHeightDict 
			stairIdDict=dict()
			for k,v in stairsIdFloorDict.items():
				kkey=k.replace(" ","")
				vkey=v.replace(" ","")
				#search in stairsHeightDict
				oresult=stairsHeightDict.get(vkey,"N/A")
				if (oresult != "N/A"):
					# printLog('debug',"found match for vkey # "+ str(vkey) + " value# "+ str(oresult))
					stairIdDict[kkey]=oresult
				else:
					# printLog('debug',"did not find match for vkey# " + str(kkey) + "using default value " + str(default_height_value)  )
					stairIdDict[kkey]=default_height_value


			# printLog('debug',"Floor Height Mapped to Stair ID ")
			# printLog('debug',str(stairIdDict))
			return {"status": "OK", "data":stairIdDict ,"errormsg": errorList }
			#step#3 apply the floor height in the stair riser df 
		else:
			msg="Unable to extract Height for stairs by Floor name as input size is:" + str(len(stairsHeightDict))
			# printLog('debug',msg)
			errorList.append(msg)

	except:
		
		# Get current system exception
		ex_type, ex_value, ex_traceback = sys.exc_info()
		
		msg="Problem extracting stairInfo due to:"  + str(ex_type.__name__)

		# Extract unformatter stack traces as tuples
		trace_back = traceback.extract_tb(ex_traceback)

		# Format stacktrace
		stack_trace = list()

		for trace in trace_back:
			stack_trace.append("File : %s , Line : %d, Func.Name : %s, Message : %s" % (trace[0], trace[1], trace[2], trace[3]))

		# print("Exception type : %s " % ex_type.__name__)
		# print("Exception message : %s" %ex_value)
		# print("Stack trace : %s" %stack_trace)

		# print(" " + msg )
		# print("Inputs:  ", str(search_floors) )

		return {"status": "OK", "data":{},"errormsg": [msg] }


"""
Extracts the no of floors, basement, stilt, plinth counts from a given building 
and returns the result  in a single column 

"""

def getBuildingInfo(pd_dataframe):

	if (pd_dataframe is None):
		return None
	# print('getBuildingInfo ::: input ')
	# print(pd_dataframe)
	#dont need terrace :) 
	mask_terrace=pd_dataframe['subtype'].isin(['TERRACE'])
	pd_dataframe=pd_dataframe[~mask_terrace]
	
	df_parent = pd_dataframe.groupby(['parent', 'subtype']).agg({'subtype': 'count'})
	df_parent = df_parent.unstack()
	df_parent = df_parent.replace(np.nan, 0)
	# print(df_parent)
	# df_parent.to_csv('output_file_2.csv')

	Summary_dict ={}
	for i, block in enumerate(df_parent.index):
		temp_dict = {}
		temp_str =  []
		result = ''
		for j, column in enumerate(df_parent.columns):
			if df_parent.iloc[i][j] != 0:
				temp_dict[column[1]] = df_parent.iloc[i][j]
				result += (str(df_parent.iloc[i][j]) +  '-' + column[1] + ' +')
				#print("index now i:j " + str(i) + " : " + str(j)  )

		Summary_dict[block] = result[:-1]
		 
	# print(Summary_dict)
	final_df = pd.DataFrame(list(Summary_dict.items()), columns=['Building', 'Remarks'])
	final_df.style.set_properties(**{'text-align': 'left'}).set_table_styles([ dict(selector='th', props=[('text-align', 'left')] ) ])
	# print(final_df)
	return final_df


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
		# print('reduce_round_error ')
		return type(li)(re_round(x, _prec) for x in li)


"""
Extracts digits between two delimeter strings 
ramp_text = '25.00 mt. long 3.14 mt. High 5.40 mt. Wide Vehicular Ramp'
startDelimeter is optional like if u know only end index 

"""
def extract_dimensions_fromtext(inputText:str, startDelimeter:None, endDelimeter:'h'):

	height_value = 0.0
	start_idx = 0

	# printLog("verbose", "extract_dimension from text :: InputText =" , inputText , "start/end delimeters" , startDelimeter, "/", endDelimeter)
	if (inputText is None or len(inputText) == 0 ): 
		# printLog('error', "Invalid inputs returning default value  ", height_value)
		get_current_logger().error(f"Invalid inputs returning default value  {height_value}")
		return height_value
	else:
		#any digit patterns 
		numeric_const_pattern = '[-+]? (?: (?: \d* \. \d+ ) | (?: \d+ \.? ) )(?: [Ee] [+-]? \d+ ) ?'
		rx = re.compile(numeric_const_pattern, re.VERBOSE)
		
		# check if u can find the start and end delimeters 
		if (startDelimeter is not None and len(startDelimeter) > 0  ):
			start_idx = inputText.find(startDelimeter)
		else: 
			start_idx = 0

		end_idx = inputText.find(endDelimeter)

		sub_text = inputText[start_idx:end_idx]

		# printLog('debug',"substring is " + sub_text)


		height_tmp = rx.findall(sub_text)
		# printLog('verbose',"dimension  is " + str(height_tmp) )
		if (len(height_tmp) > 0 ):
			#return the index[0] value 
			return height_tmp[0]
		else: 
			# printLog('error','Unable to extract height value from :: ' + inputText + ' - Returning default value ' + str(height_value))
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
def extract_road_width_fromtext(inputText:str):

	height_value = 0.0
	start_idx = 0

	# printLog("verbose", "extract_width :: InputText =" , inputText , "start/end delimeters")
	if (inputText is None or len(inputText) == 0 ): 
		# printLog('error', "Invalid inputs returning default value  ", height_value)
		get_current_logger().error(f"Invalid inputs returning default value  {height_value}")
		return height_value
	else:
		startDelim=None
		#case of neither - just get single value 
		noDelim=False

		inputText=inputText.upper()
		existingIndex= inputText.find('EXISTING')
		proposedIndex= inputText.find('PROPOSED')
		
		#set Start and End Delim 
		if (existingIndex > -1):
			startDelim='EXISTING'
			start_idx=existingIndex
		else:
			start_idx=0
		
		if (proposedIndex > -1):
			endDelim='PROPOSED'
			end_idx=proposedIndex
		else:
			#endDelim=''
			end_idx=len(inputText)


		if (existingIndex == -1 and proposedIndex == -1):
			noDelim=True 
			startDelim=0
			endDelim=len(inputText)


		#any digit patterns 
		numeric_const_pattern = '[-+]? (?: (?: \d* \. \d+ ) | (?: \d+ \.? ) )(?: [Ee] [+-]? \d+ ) ?'
		rx = re.compile(numeric_const_pattern, re.VERBOSE)
		
		sub_text = inputText[start_idx:end_idx]

		# printLog('verbose',"substring is " + sub_text)

		height_tmp = rx.findall(sub_text)
		# printLog('verbose',"dimension  is " + str(height_tmp) )
		if (len(height_tmp) > 0 ):
			#return the index[0] value 
			return height_tmp[0]
		else: 
			# printLog('error','Unable to extract height value from :: ' + inputText + ' - Returning default value ' + str(height_value))
			get_current_logger().error(f"Unable to extract height value from :: {inputText} - Returning default value {height_value}")
			return height_value


def extract_room_dimensions(roomName):
	# printLog('debug', ' Extract room dimensions from ' + str(roomName) )
	result=dict()
	
	if (roomName is None or len(roomName.strip()) <= 0):
		result['code']=99
		result['length']=-1
		result['width']=-1
		result['type']='N/A'
		result['msg']='Input required, is : '+ roomName
	else:
		
		lengthDelim='\\P'
		widthDelim='X'

		length_idx = roomName.rfind(lengthDelim)
		width_idx=roomName.rfind(widthDelim)

		if (length_idx != -1 and width_idx != -1 ):
			#success set return code 0 
			result['code']=0
			result['length']=roomName[length_idx+2:width_idx]
			result['width']=roomName[width_idx+1:]
			result['type']=roomName[:length_idx]
			result['msg']=''

		else:
			#unable to extract return failure
			result['code']=1
			result['length']=0
			result['width']=0
			result['type']='N/A'
			result['msg']='Unable to get dimensions'
	return result


""" 
function to calculate the gradient given a length and height 
"""
def calc_gradient(length:float, height:float):

	gradient = 0
	msg = " inputs length/height : " + str(length) + "/" + str(height)
	# printLog('debug',msg )
	if (length == 0 or height == 0 ): 
		# printLog('error', "calc_gradient " + msg + " In valid inputs returning default value " + str(gradient))
		get_current_logger().error(f"calc_gradient {msg} In valid inputs returning default value {gradient}")
		return gradient
	else : 
		#get slope_length 
		slope_length = math.sqrt(float(length) **2 + float(height) **2 )
		#gradient is ration of slope_length to the height 
		gradient = int (float(slope_length)/float(height))
		msg = "Calculated gradient is " + str(gradient) + " for " + msg 
		# printLog('debug',msg )
	return gradient


def getDistanceBetweenObjects(source:DxfPoly, target:DxfPoly):
	if (source is None or target is None ): 
		retValue=-99
	else: 
		retValue = round(source.distance(target),2)

	return retValue

def get_json4DictNormal(aspect:str, objListDict:dict):
	if (aspect is None):
		returnStr=" { "
	else:
		returnStr="{ \"" + aspect + "\" : " + " { "

	isFirst=True
	for k,v in objListDict.items(): 
		k = removeSpecialChars(k)
		v = removeSpecialChars(str(v))
		
		if isFirst:
			returnStr +=  " \"" + k + "\" : \"" + str(v) + "\" " 
			isFirst=False
		else :
			returnStr +=  ", " + " \"" + k + "\" : \"" + str(v) + "\" "
	returnStr += " } "
	if aspect is not None :
		returnStr += " } "
	return returnStr

"""
Remove Special chars from ACAD for JSON Single "\" or \\P}
"""
def removeSpecialChars(textStr ):
	
	if (textStr is None):
		return ''

	replaceSpaceStr=" "
	replaceBlankStr=""
	#for room names having special char in 2 words 
	
	if ("\\P" in textStr ) :
		textStr = textStr.replace("\\P",replaceSpaceStr)
	#for room name having special chars
	if ("\\ptz;" in textStr or "pxqc;"  in textStr or "\\q*;"  in textStr or "*;" in textStr or "T1.5;" in textStr or ";" in textStr) :
		textStr = textStr.replace("\\ptz;",replaceBlankStr).replace("\\pxqc;",replaceBlankStr).replace("\\pq*;",replaceBlankStr).replace("*;",replaceBlankStr).replace(
			"T1.5;",replaceBlankStr).replace(";",replaceBlankStr)
	#for road names having quotes single/double 
	if ("\'" in textStr or "\"" in textStr or "\\" in textStr):
		textStr = textStr.replace("\'",replaceBlankStr).replace("\"",replaceBlankStr).replace("\\",replaceBlankStr)
	
	return textStr
# """
# #05/01/2024 - Fix Clean new lines from JSON file before returning to api calls
#
#
# """
# def clean_jsonFile(json_file_in:str):
# 	import os.path , shutil
# 	# print("Starting clean_jsonFile")
# 	if (json_file_in is None):
# 		# print("Valid File required , Input value=", json_file_in)
#
#
# 	elif (os.path.isfile(json_file_in)==False) :
# 		print("Valid File required , Input value=", json_file_in  , " does file exists ? ", os.path.isfile(json_file_in) )
#
# 	else:
# 		print('Cleaning new lines from Input File : ', os.path.basename(json_file_in))
#
# 		json_file_out=json_file_in[0:-5]+"_tmp.json"
#
# 		try :
#
# 			with open(json_file_in,'r') as in_filestream, open(json_file_out, mode='w') as out_file :
# 				contents = in_filestream.read()
# 				out_file.write(contents.replace('\n','') )
# 				#out_file.write(re.sub('\\s$', '', contents, flags=re.MULTILINE))
#
# 			in_filestream.close()
# 			out_file.close()
#
# 			shutil.move(json_file_out, json_file_in)
# 			print( "File cleaned successfully " )
# 		except Exception as excp:
# 			print("Unable to remove new lines from the input file due to ", str(excp) )
# 	print("Completed clean_jsonFile")

"""
Returns a JSON String for a List of Dict (key,value ) pairs 

"""
def get_json4ListOfDictNormal(aspect:str, listInput : list ):
	returnStr="{ \"" + aspect + "\" : " + " [ "

	idx = 0 
	for listItem in listInput:
		isFirst=True
		for k,v in listItem.items(): 
			k = removeSpecialChars(k)
			v = removeSpecialChars(str(v))
			if isFirst:
				returnStr +=  " { \"" + k + "\" : \"" + str(v) + "\"  " 
				isFirst=False
			else :
				returnStr +=  ", " + " \"" + k + "\" : \"" + str(v) + "\"  "
		
		if (idx < len(listInput)-1) :
			returnStr += " } , "
		else:
			returnStr += " } "
		idx += 1
	returnStr += " ]  }"
	return returnStr


def get_json4String(aspect:str,value:str):

	if (aspect is not None and value is not None):
		returnStr="{ \"" + aspect + "\" : " + " [ " + value + " ]  } "
	else:
		returnStr="{}"
	return returnStr

def get_json4ListString(aspect:str,value:list):

	if (aspect is not None and value is not None):
		returnStr="{ \"" + aspect + "\" : " +  str(value).replace('\'', '\"') + "  } "
	else:
		returnStr="{}"
	return returnStr

'''
Extract Textual attributes from the DXF File 
'''
def grepFromFile(dxfFile,keywords:dict):
	import sys 
	infile = open(dxfFile, 'r')
	try :
		resultsDict = {} 
		for keywordIdx,label in keywords.items():
			# print("searching ... " + keywordIdx)
			search_result=[]
			for txtResult in grep_iter(infile, keywordIdx):
				if (txtResult not in search_result):
					if (":" in txtResult):
						startId = txtResult.find(":")
						covgNew = txtResult[startId+1:]
						search_result.append(covgNew)
					else:
						search_result.append(txtResult)
					
					# print("found match ", str(txtResult) )
					break
					
			resultsDict[keywordIdx] = search_result
			

		# print("Results: ", str(resultsDict))
		return resultsDict
	except: 
		e = sys.exc_info()[0]
		# print ('Error occured in function grepFromFile ', e )
		return {}

'''
TYPICAL - 3, 4, 5, 6, 7, 8 FLOOR PLAN 

'''
def determineFloorNumbers(nameOfFloor:str):
	from num2words import num2words
	retVal = []
	
	import re 
	#check if string has any digits otherwise just split the string 
	word2RemoveList=['|', 'TYPICAL','FLOOR', 'PLAN']
	# print("The original string is : " + nameOfFloor)

	if "|" in nameOfFloor:
		nameOfFloor=nameOfFloor[nameOfFloor.find("|"):].upper()
	#clean
	for word2Remove in word2RemoveList:
		nameOfFloor=nameOfFloor.replace(word2Remove,"")
	#translate
	if ("&" in nameOfFloor): 
		nameOfFloor = nameOfFloor.replace("&",',')

	typeOfString=checkString4AlphaDigits(nameOfFloor)  #ALPHA, DIGITS, ALPHANUM 
	# print("determined type of string as : " + typeOfString)

	if ("DIGITS" in typeOfString): #nameOfFloor is not None and hasDigits):

		# Convert String ranges to list 
		# Using sum() + list comprehension + enumerate() + split() 
		
		# print("The original string is : " + nameOfFloor) 
		#remove spaces and alphabhets
		nameOfFloor=re.sub(r'[a-z]|[A-Z]|\s|\t|\|', '', nameOfFloor)
		
		# print("After removing spaces/alphabhets string is now : " + nameOfFloor) 
		
		#extract the number ranges 
		nameOfFloor = re.sub("[^0123456789\,\-]","", nameOfFloor)
		
		if (nameOfFloor[0] == "-"):
			nameOfFloor = nameOfFloor[1:]


		if(nameOfFloor[0] == ","):
		  nameOfFloor=nameOfFloor[1:]

		res = sum( ( (list(range(*[int(b) + c  
				   for c, b in enumerate(a.split('-'))])) 
				   # if ('-' in a or ' ' in a ) else [int(a)]) for a in re.split(',|\s',nameOfFloor) ), [])
				   if '-' in a else [int(a)]) for a in nameOfFloor.split(',') ), [])  

		# printing result 
		# print("List after conversion from string : " + str(res)) 
		
		#convert them to ordinal words 1 First 2 secound 4 fourth etc ...
		wordResults=[]
		for numberOfFlr in res:
			wordResults.append(num2words(numberOfFlr,to='ordinal').upper())

		retVal = wordResults

	elif ("ALPHANUM" in typeOfString) :
		nameOfFloor=re.sub(r'|\s|\t|\|', '', nameOfFloor)
		# print ("after cleanup:" + nameOfFloor.strip())

		if (nameOfFloor[0] == "-"):
			nameOfFloor = nameOfFloor[1:]
		# print("The mixed word and number range is : " + nameOfFloor)

		wordResults=[]

		for tok in nameOfFloor.split(","):
			if (tok.isnumeric()):
				asword = num2words(tok,to='ordinal').upper()
				wordResults.append(asword) 
			else:
				wordResults.append(tok)
		retVal= wordResults

	elif ("ONLYTEXT" in typeOfString) : #(not hasDigits and (","  in nameOfFloor or "-"  in nameOfFloor) ) :
		""" some have a words itself """
		words2Remove=['FLOOR','PLAN','TYPICAL']

		# print("The original string is : " + nameOfFloor)
		for toRemove in words2Remove:
			nameOfFloor=nameOfFloor.replace(toRemove,"")

		#remove spaces
		nameOfFloor=re.sub(r'|\s|\t|\|', '', nameOfFloor)
		if ("&" in nameOfFloor): 
			nameOfFloor = nameOfFloor.replace("&",',')
		# print("After removing spaces string is now : " + nameOfFloor)
		
		if (nameOfFloor[0] == "-"):
			nameOfFloor = nameOfFloor[1:]
		# print("The word-number range is : " + nameOfFloor)

		# printing original string  
		# print("The string is :" + nameOfFloor)
		if(nameOfFloor[0] == ","):
		  nameOfFloor=nameOfFloor[1:]
		  # print("The final string is :" + nameOfFloor)
		
		wordResults=[]
		for nameStr in nameOfFloor.split(","):
			wordResults.append(nameStr)

		retVal = wordResults

	

	return retVal

"""
utility to check if string is only digits, only text or mix. used for splitting typical floor 
"""
def checkString4AlphaDigits(nameOfFloor:str):

	nameOfFloor=nameOfFloor.upper()
	word2RemoveList=['|', 'TYPICAL','FLOOR', 'PLAN']
	pIndex=nameOfFloor.find("|") 

	if pIndex > -1 :
		nameOfFloor=nameOfFloor[pIndex:].upper()

	for word2Remove in word2RemoveList:
		nameOfFloor=nameOfFloor.replace(word2Remove,"")

	nameOfFloor_Check=re.sub(r'|\s|\t|\,|\-|\*|', '', nameOfFloor) 
	
	isAlpha=nameOfFloor_Check.isalpha()  #check if string is only alpha a-z 
	isAlphaNum = nameOfFloor_Check.isalnum()  #check if string has digits and alpha 
	isDigits=nameOfFloor_Check.isnumeric()  #only digits 
	# print("check str",nameOfFloor_Check )
	# print ("  Alpha, isAlphaNum, has Digits ", isAlpha, isAlphaNum, isDigits)

	if (isDigits and isAlphaNum and not (isAlpha)):
		return "DIGITS"
	elif ((isAlpha and isAlphaNum) and not (isDigits)):
		return "ONLYTEXT"
	elif (isAlphaNum and not (isDigits and isAlpha)):
		return "ALPHANUM"
	else:
		# print("unknown, default to ALPHA ")
		return "ONLYTEXT"


'''
Deep copy of Typical Floors into individual floors 
'''
def splitTypicalFloors(floorObj):
	
	results= {}
	if (floorObj is not None ):

		#Check Typical in name and , 
		floorExpandedList = determineFloorNumbers(floorObj.fname)

		for newFlrName in floorExpandedList:
			tmpFlrObj = copy.deepcopy(floorObj)
			tmpName = newFlrName.strip()
			if ("FLOOR" in floorObj.fname): 
				tmpName += " FLOOR"
			if ("PLAN" in floorObj.fname ):
				tmpName += " PLAN"
			tmpFlrObj.name=tmpName
			results[floorObj.parent + "|" +  newFlrName.strip()  + " FLOOR PLAN"]= tmpFlrObj
		return results


def checkDeviationsInDrawing(msp):
	returnValueDict=dict()
	if (msp is None): 
		returnValueDict['CODE']=-1
		returnValueDict['ERROR']='Invalid Inputs. Valid Modelspace required but is None'

		return returnValueDict
	else:
		overlappingObject = check_For_layersOverlapping()
		response1 = overlappingObject.checkDeviations(msp)
	
		returnValueDict['RESULTS']=response1
		returnValueDict['CODE']=0
	return returnValueDict

#Validation_layers 
def checkCommonLayersInBuildings(msp):
	returnValueDict=dict()
	if (msp is None): 
		returnValueDict['CODE']=-1
		returnValueDict['ERROR']='Invalid Inputs. Valid Modelspace required but is None'

		return returnValueDict
	else:
		try :

			commonValidationObject = CommonValidationLayers()
			response1 = commonValidationObject.performLayerChecks(msp)
		
			returnValueDict['RESULTS']=response1
			returnValueDict['CODE']=0
		except Exception as excp:
			msg='Problem Validating Layer Checks checkCommonLayersInBuildings ' + str(excp) 
			
			# print('ERROR ', msg )
			returnValueDict['ERROR']=msg
			returnValueDict['CODE']=-1
	return returnValueDict


def getBalconyInfo(msp):
	returnValueDict=dict()
	if (msp is None): 
		returnValueDict['CODE']=-1
		returnValueDict['ERROR']='Invalid Inputs. Valid Modelspace required but is None'

		return returnValueDict
	else:
		try :
			obj=BalconyLengthAndWidth()

			response1 = obj.FindBalconyLengthAndWidth(msp)
	
			returnValueDict['RESULTS']=response1
			returnValueDict['CODE']=0
		except Exception as excp:
			msg='Problem Extracting Balcony Details from Dwg ' + str(excp) 
			
			# print('ERROR ', msg )
			returnValueDict['ERROR']=msg
			returnValueDict['CODE']=-1
	return returnValueDict 


def runCommonBuildingUtils(msp):
	returnValueDict=dict()
	# printLog('verbose','Starting runCommonBuildingUtils '  )

	if (msp is None): 
		returnValueDict['CODE']=-1
		returnValueDict['ERROR']='Invalid Inputs. Valid Modelspace required but is None'

		return returnValueDict
	else:
		utils_list=['SEGMENT_WISE_FLOOR_SETBACKS','PLOT_LINE_ENTRANCE_GATE', 'VENTILATION_SHAFT_DIMENSION','WINDOW_IN_ROOM_CHECKS']
		returnValueDict['SUPPORTED_BUILDING_UTILS']=utils_list
		errorsList=[]


		for utilname in utils_list:

			try :
				# printLog('verbose', 'Running ' , utilname )
				if (utilname == 'PLOT_LINE_ENTRANCE_GATE'):
					obj = SegmentwisePlotLength_AND_EntGateWidth()
					response1 =  [(dict(sorted(dct.items()))) for dct in obj.FindPlotLength_And_EntGateWidth(msp)]

				elif (utilname == 'VENTILATION_SHAFT_DIMENSION' ):

					obj = VentilationWidthANDArea()
					response1 = [(dict(sorted(dct.items()))) for dct in obj.FindVentilationWidthANDArea(msp)]

				elif (utilname == 'SEGMENT_WISE_FLOOR_SETBACKS'):
					obj = CommonFloorSetbacksOFSegmentwise()
					response1 = [(dict(sorted(dct.items()))) for dct in obj.FindSebacks(msp)]

				elif (utilname == 'WINDOW_IN_ROOM_CHECKS'):
					obj=CheckWindowsINRoom()
					##
					windowResponse=obj.CheckWindowInRoom(msp)
					response1= [dict(sorted(dct.items())) for dct in windowResponse.get('data',[])]

				else:
					response1=[]

				returnValueDict[utilname + '_RESULT']= response1
			
				
			except Exception as excp:

				msg='Problem Running ' + utilname + ' due to ' + str(excp) 
				errorsList.append(msg)
			
		if (len(errorsList) >0 )	:
			returnValueDict['ERROR']=errorsList
			returnValueDict['CODE']=-1
		else:
			returnValueDict['CODE']=0

		# printLog('verbose','Completed  runCommonBuildingUtils '  )

	return returnValueDict

def runCombinedBuildingUtility(msp,gatedCommunityFlag:str):
	returnValueDict=dict()
	errorsList=[]
	# printLog('verbose','Starting runCombinedBuildingUtility '  )

	if (msp is None or gatedCommunityFlag is None): 
		returnValueDict['CODE']=-1
		returnValueDict['ERROR']='Invalid Inputs. Valid Modelspace required but is None, gatedCommunityFlag is required'

		return returnValueDict
	else:
		try :

			AllbuildinsData=AllBuildingsData()

			response1=AllbuildinsData.GetAllBuildingsData(msp,gatedCommunityFlag)
			
			returnValueDict['COMBINED_BUILDING_UTIL_RESULTS']=response1

		except Exception as excp:
			msg='Problem Running  runCombinedBuildingUtility  due to ' + str(excp) 
			errorsList.append(msg)
			
		if (len(errorsList) >0 )	:
			returnValueDict['ERROR']=errorsList
			returnValueDict['CODE']=-1
		else:
			returnValueDict['CODE']=0

		# printLog('verbose','Completed  COMBINED_BUILDING_UTIL_RESULTS '  )

	return returnValueDict 

def executeDrawingActions(request_params:dict,folder:str,filename:str):
	returnValueDict=dict()
	
	# print(f'Drawing Actions Inputs - request params {request_params}, folder {folder} , filename {filename}  ')
	#  0:success -1:default -2: failed 
	invalidInput = -1 
	failedCode = -2 
	successCode = 0 

	response1 = dict()
	warnings=[]
	errors=[]

	#check layout from request_params 
	if (request_params is None or len(request_params) == 0  or folder is None or filename is None): 
		returnValueDict['code']=invalidInput
		errors.append('Invalid Inputs. Valid request_params, folder and filename required but are None')
		returnValueDict['errors']=errors 

		return returnValueDict
	
	else:
		actionType=request_params.get('actiontype','NA')
		layout=request_params.get('layout','NA')
		gatedCommunityRequest=request_params.get('isGatedCommunity','False')

		# print('Drawing Actions request layout =' , layout , ' actionType =' , actionType)
		allowedActionsDict= LayerMaster.DRAWING_ACTIONS_TYPE.value
		actionForLayout=allowedActionsDict.get(layout,[])

		isSupportedLayout=False
		isActionValidForLayout=False
		isGatedCommunityRequest=False  #10/08/2023 



		if (layout != "NA" and layout in allowedActionsDict.keys()) :
			isSupportedLayout=True

		
		if (len(actionForLayout)> 0 and actionType in actionForLayout ):
			isActionValidForLayout=True

		#10/08/2023 GatedCommunity Setbacks 
		if (gatedCommunityRequest == 'True' or 
				(gatedCommunityRequest == 'False' and actionType == 'GatedCommunitySetbacks') 
		   ):
			# print('setting isGatedCommunityRequest True')
			isGatedCommunityRequest=True

			# print(f'Flags checks isGatedCommunityRequest {isGatedCommunityRequest} \
			# isActionValidForLayout {isActionValidForLayout} \
			# isSupportedLayout {isSupportedLayout} ')

		if ( isSupportedLayout==False or isActionValidForLayout ==False ):
			returnValueDict['code']=invalidInput
			returnValueDict['errors']=['Invalid Inputs. Valid layout, actionType required. Given (layout,actionType) are ' \
						+ layout + ' , ' + actionType]

			return returnValueDict
		else:
		
			runDwgConversion=False
			try :
				

				msg=''
				actionExecuted=False
				if (layout == 'Building'):
					if (actionType == 'CreateLayersFromDwg'):
						# print('in building and createlayersfromdwg ')
						list_of_svg_files=[]
						# obj=BPCDrawingLayers()
						# response1 = obj.LoadLayers(folder,filename)
						# print(f' Response from AI  {response1} ')
						# runDwgConversion=True
						#
						# if (response1 is not None):
						# 	returnCode=response1.get('code',-2)
						# 	print(f' Response code {returnCode} ')
						# 	warnings=response1.get('warnings',[])
						#
						# 	if (returnCode < 0 ):
						# 		errors=response1.get('errors',[])
						# 		print(f' Response code {returnCode} Errors {errors} warnings {warnings} ')
						# 	elif (returnCode == 0):
						# 		print(f' Response code {returnCode}  warnings {warnings}  ')
						# 	else:
						# 		print(f' Response code {returnCode} Not mapped ')
						#
						#
						#
						# else:
						# 	returnCode=failedCode
						# 	print(f' Response code {returnCode} Empty Response  ')

					# elif (actionType == 'FirePlanScrutiny'):
					# 	print("Fire Action Starting ")
					# 	fireBuildingObj=FireBuildings()
					# 	##
					# 	response1=fireBuildingObj.CheckValidation(folder,filename)
					# 	#print('response of fire buildings is \n ',response1 )
					#
					# 	if (response1 is not None):
					# 		returnCode=response1.get('code',-2)
					# 		errors=response1.get('errors',[])
					# 		print(f'  Response code {returnCode} ')
					# 		if (returnCode < 0 ):
					#
					# 			print(f' Response code {returnCode} Errors {errors}   ')
					# 		elif (returnCode == 0):
					# 			actionExecuted=True
					#
					# 			print(f'Setting ActionExecuted =True Response code {returnCode}  Errors {errors}   ')
					# 		else:
					# 			print(f' Response code {returnCode} Not mapped ')
					#
					# 	else:
					# 		returnCode=failedCode
					# 		print(f' Response code {returnCode} Empty Response  ')
					#
					# 	print("Fire Action Completed ")
					#
					# elif (isGatedCommunityRequest == True ):
					# 	print('in building and GatedCommunitySetbacks ')
					# 	obj=GatedCommunitySetbacks()
					# 	response1 = obj.setbacks(folder,filename)
					# 	actionExecuted=True
					# 	if (len(response1)>0):
					# 		returnCode = successCode
					# 	else:
					# 		returnCode=failedCode
					# 		msg=f'GatedCommunitySetbacks - Empty Response with  returnCode {returnCode} '
					# 		print(msg)
					#
					# else:
					# 	msg= f'No Matching Action ** {actionType} ** for Layout # {layout} '
					# 	print(msg)
					# 	returnCode=failedCode

				# elif (layout == 'OpenLayout'):
				# 	if (actionType == 'CreateLayersFromDwg'):
				# 		obj=BPCDrawingLayersForOpenLayout()
				# 		response1 = obj.LoadLayers(folder,filename)
				# 		print(f' Response from AI  {response1} ')
				#
				# 		if (response1 is not None):
				# 			returnCode=response1.get('code',-2)
				# 			warnings=response1.get('warnings',[])
				# 			print(f' Response code {returnCode} ')
				# 			if (returnCode < 0 or returnCode == 1):
				# 				runDwgConversion=False
				# 				errors=response1.get('errors',[])
				# 				print(f' Response code {returnCode} Errors {errors} warnings {warnings} ')
				# 			elif (returnCode == 0):
				# 				runDwgConversion=True
				# 				returnCode=successCode
				# 				print(f' Response code {returnCode}  warnings {warnings}  ')
				# 			else:
				# 				runDwgConversion=False
				# 				print(f' Response code {returnCode} Not mapped ')
				#
				# 		else:
				# 			returnCode=failedCode
				# 			print(f' Response code {returnCode} Empty Response  ')
				#
				# 	else:
				# 		msg= f'No Matching Action ** {actionType} ** for Layout # {layout} '
				# 		print(msg)
				# 		returnCode=failedCode

				else:
					msg=f'UnSupported Action Type ** {actionType} ** for Layout # {layout} not implemented '
					# get_current_logger().error(msg)
					returnCode=failedCode


				# #checking post actionExecute commands
				# print ('#checking post actionExecute commands  ')
				# if (runDwgConversion==True):
				# 	print ('runDwgConversion True  ')
				# 	#DXFFILE_DIR='C:\\Users\\esiva\\AppData\\Local\\Programs\\Python\\Python38-32\\myscripts\\flask-tabler\\app\\base\\..\\..\\output\\'
				# 	DXFFILE_DIR=folder
				# 	inputFile=filename
				# 	DWGFILE_DIR=folder.replace("app\\base\\..\\..\\output\\","") + "testfiles\\drawings\\"
				# 	#DWGFILE_DIR='C:\\Users\\esiva\\AppData\\Local\\Programs\\Python\\Python38-32\\myscripts\\flask-tabler\\testfiles\\drawings\\'
				#
				# 	convertedDwgResponse=convertDXF2DWGUtil(DXFFILE_DIR, inputFile, DWGFILE_DIR)
				# 	newFileName= convertedDwgResponse.get('FileName','')
				#
				# 	returnCode=successCode
				# 	returnValueDict['code']=returnCode
				# 	returnValueDict['dwg_name']=newFileName
				# 	returnValueDict['results']=convertedDwgResponse
				# 	print(f' DWG Conversion new file # {newFileName} converted to dwg Successfully')
				#
				# elif (actionExecuted==True):
				# 	print(f' Action {actionType} executed for {layout} with returnCode {returnCode} ')
				#
				#
				# 	returnValueDict['code']=returnCode
				# 	returnValueDict['results']=response1
				#
				# 	#print(f' Response is \n {response1}')
				#
				#
				# else:
				# 	print('Else in checking post actions commands ' + msg)
				# 	returnValueDict['code']=returnCode
				# 	returnValueDict['dwg_name']=''
				# 	returnValueDict['results']=dict()
				#
				#
				# if len(msg) >0 :
				# 	errors.append(msg)
				#
				# returnValueDict['warnings']=warnings
				# returnValueDict['errors']=errors
			except Exception as excp:
				# print('Exception occured in executeDrawingActions ' + str(excp))
				ex_type, ex_value, ex_traceback = sys.exc_info()

				# Extract unformatter stack traces as tuples
				trace_back = traceback.extract_tb(ex_traceback)

				# Format stacktrace
				stack_trace = list()

				for trace in trace_back:
					errorDict=dict()
					fileName=trace[0]
					fileName=fileName.strip()
					stripFileName=fileName[fileName.rindex("\\")+1:-3]
					errorDict['File']=stripFileName
					errorDict['Line']=trace[1]
					errorDict['Func.Name']=trace[2]
					errorDict['Statement']=trace[3]
					stack_trace.append(errorDict)
					#stack_trace.append("File : %s , Line : %d, Func.Name : %s, Statement : %s" % (stripFileName, trace[1], trace[2], trace[3]))

				# print("Exception type : %s " % ex_type.__name__)
				# print("Exception message : %s" %ex_value)
				# print("Stack trace : %s" %stack_trace)

				msg='Problem Executing Drawing Actions  ' + str(excp) 
				returnValueDict['code']=failedCode
				returnValueDict['errors']=msg
				# print('ERROR encounted executeDrawingActions due to :::: ', msg )
				
	return returnValueDict


def mapCenterLinesWithinObjectList(passageOrRoadList: list) -> list:
	returnValue = []
	if (passageOrRoadList is None or len(passageOrRoadList) == 0):
		return returnValue

	centerLinesList = []

	# onlyClosedRoads
	closedRoadsList = []
	for internalRoadTmp in passageOrRoadList:
		# printLog('debug', " DXPoly is " + internalRoadTmp.handle, ' is closed ', internalRoadTmp.isClosed())
		if (internalRoadTmp.isClosed()):
			closedRoadsList.append(internalRoadTmp)
		else:
			centerLinesList.append(internalRoadTmp)

	# printLog('debug', "Center line list count ", len(centerLinesList))
	# printLog('debug', "Closed Roads list count ", len(closedRoadsList))
	roadWithCenterLineProcessedCheck = []
	roadWithCenterLineProcessedList = []
	for roadWithCentreLine in closedRoadsList:
		if (roadWithCentreLine.handle not in roadWithCenterLineProcessedCheck):
			roadWithCenterLineProcessedCheck.append(roadWithCentreLine.handle)
		else:
			continue

		# printLog('debug', 'processing ', roadWithCentreLine.handle, str(roadWithCentreLine.get_points()))
		for centerLine in centerLinesList:
			# printLog('debug', 'centreline  ', centerLine.handle, str(centerLine.get_points()))
			if (centerLine.isClosed() == False):
				xyP1 = centerLine.get_points()[0].split(" ")
				xyP2 = centerLine.get_points()[1].split(" ")
				# printLog('debug', 'centerLine points', centerLine.get_points())
				xyP_Str = xyP1[0], "-", xyP1[1]

				p1 = Point(float(xyP1[0]), float(xyP1[1]))
				p2 = Point(float(xyP2[0]), float(xyP2[1]))

				center_line = LineString([p1, p2])

				polyStr = str(roadWithCentreLine.get_points())[1:-1].translate(translation)
				# printLog('debug', "LineString String coordates ", str(center_line))
				# create a ploygon
				polyPoints = 'POLYGON ((' + polyStr + '))'

				lwpoly = shapely.wkt.loads(polyPoints)

				# printLog('debug', 'covers ', lwpoly.covers(center_line), \
				# 		 'within ', center_line.within(lwpoly), \
				# 		 'contains ', lwpoly.contains(center_line), \
				# 		 'intersects ', center_line.intersects(lwpoly))

				if (center_line.intersects(lwpoly)):
					# printLog('debug',
					# 		 'Found a match for ' + centerLine.handle + " with parent " + roadWithCentreLine.handle)
					clDict = dict()
					clDict['centerline'] = str(centerLine.get_points())
					roadWithCentreLine.setMiscProps(clDict)
					roadWithCenterLineProcessedList.append(roadWithCentreLine)

	return roadWithCenterLineProcessedList

def getPurposeCodeMap():
	return 	LayerMaster.PURPOSE_CODE_DESC_MAP.value

def getBuildingSubTypes():
	return 	LayerMaster.BUILDING_CATEGORY.value

def getROOMVentilationArea_info(msp):
	returnValueDict = dict()
	if (msp is None):
		returnValueDict['CODE'] = -1
		returnValueDict['ERROR'] = 'Invalid Inputs. Valid Modelspace required but is None'

		return returnValueDict
	else:
		try:
			obj = RoomVentilationAreaDetail(msp)

			response1 = obj.get_details()

			returnValueDict['RESULTS'] = response1
			returnValueDict['CODE'] = 0

		except Exception as excp:
			msg = 'Problem Extracting Room Ventilation Details' + str(excp)

			# print('ERROR ', msg )
			returnValueDict['ERROR'] = msg
			returnValueDict['CODE'] = -1
	return returnValueDict

def getCompoundWallDetails(msp):
	returnValueDict = dict()
	if (msp is None):
		returnValueDict['CODE'] = -1
		returnValueDict['ERROR'] = 'Invalid Inputs. Valid Modelspace required but is None'

		return returnValueDict
	else:
		try:
			obj = CompoundWallDetails(msp)

			response1 = obj.get_WCdetails()

			returnValueDict['RESULTS'] = response1
			returnValueDict['CODE'] = 0
		except Exception as excp:
			msg = 'Problem Extracting Compound Wall Details' + str(excp)

			# print('ERROR ', msg )
			returnValueDict['ERROR'] = msg
			returnValueDict['CODE'] = -1

	return returnValueDict


def getCourtYard_details(msp):

	returnValueDict = dict()
	if (msp is None):
		returnValueDict['CODE'] = -1
		returnValueDict['ERROR'] = 'Invalid Inputs. Valid Modelspace required but is None'

		return returnValueDict
	else:
		try:
			obj = CourtYardDetails(msp)

			response1 = obj.get_courtyard_details()

			returnValueDict['RESULTS'] = response1
			returnValueDict['CODE'] = 0
		except Exception as excp:
			msg = 'Problem Extracting Court Yard Details ' + str(excp)

			# print('ERROR ', msg )
			returnValueDict['ERROR'] = msg
			returnValueDict['CODE'] = -1

	return returnValueDict