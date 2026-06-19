from digit_domain import BldgBaseObj,BuildingName,Floor,IndivSubPlot
from logging_config import get_current_logger
from digit_utils_buildings import (LayerMaster,getPurposeDesc,executeDrawingActions,checkDeviationsInDrawing,
                                   runCombinedBuildingUtility,get_cellar_setbacks_plinth,get_podium_setbacks,get_ghmc_setbacks,
                                   getSetBacksByMidPointsMarginLineNew,get_transfer_of_setbacks,get_area_by_bua_type_voids_accessory,
                                   get_Mortgaged_CarpetArea4Buildings,get_floor_wise_setbacks,Green_strip_width,get_accessory_septic_sewage_transformer_distances,
                                   splitTypicalFloors,getMinWidthIrregularObjects,getBuildingInfo,re_round,getCategoryForParking,getBuilding_Floor_Heights,
                                   groundlevel_check_latest,determineFloorNumbers,merge_netbua,checkLiftHeight,getDistanceBetweenObjects,removeSpecialChars,
                                   extract_dimensions_fromtext,getSetBacksByMidPoints,commonfloor_setbacks,window_in_passage_check,get_ramp_info,
                                   calc_gradient,window_check_util,check_balcony_maindoor,runCommonBuildingUtils,getBalconyInfo,door_to_staircase_distance,
                                   getROOMVentilationArea_info,get_travel_distance,DxfPoly,mapCenterLinesWithinObjectList,getPointsAsListFromString,
                                   getMinWidthByCenterLine,grepFromFile,getCompoundWallDetails,getCourtYard_details)

from digit_utils_openlayout import extractMaxRoadWidthFromDict
from AnalyzeDrawingUtil import analyzeDrawingMsp
from digit_rules_v1 import callrule
import datetime
import time
import ezdxf
import pandas as pd
import numpy as np
from shapely.geometry import Point,LineString,Polygon
import shapely
import math
import re
import sys
import os
import traceback
from datetime import datetime
from ezdxf.entities.mtext import plain_mtext

SUCCESS_CODE=0
FAIL_CODE=99
TEXT_ELEMENTS_FROM_DWG ={"Proposed Coverage" : ""}  #disabled others
translation = {39: None}
MANDATORY_LAYERS_FOR_PLAN_TYPE= {
'Open_Layout' : ['_Plot', '_IndivSubPlot',  '_OrganizedOpenSpace',  '_InternalRoad'],
# 'OpenVillas_Layout':['_Plot', '_OrganizedOpenSpace', '_Floor', '_CarpetArea','_NetPlot', '_MarginLine','_FloorInSection' ,'_Room','_BuildingName','_Window','_Door'],
'Building_Layout' : ['_Floor', '_CarpetArea', '_OrganizedOpenSpace','_NetPlot', '_MarginLine','_FloorInSection' ,'_Room','_BuildingName','_Window','_Door']
 }

def extractAbuttingRoadForSplay(plot_poly, road_list):
    abuttingDict = dict()

    if (plot_poly is None or road_list is None):
        return abuttingDict

    get_current_logger().debug(f' splay plot poly {plot_poly}   with master road list  {road_list}')
    plot_coords = list(plot_poly.exterior.coords)
    rLen = len(plot_coords)
    rPos = 0

    plotList = re_round(plot_coords, 1)
    plotObj = Polygon(plotList)
    plot_org = Polygon(plot_coords)
    # loop each plot vertex
    for plotVertex in plotList:
        # print("processing rPos ", str(rPos))
        if (rPos == (rLen - 1)):
            rTarget = 0
        else:
            rTarget = rPos + 1
        # print ("rPos " , str(plotList[rPos]) )
        # print ("rTarget " , str(plotList[rTarget]) )

        line = LineString([Point(plotList[rPos]), Point(plotList[rTarget])])
        lineOrg = LineString([Point(plot_coords[rPos]), Point(plot_coords[rTarget])])

        get_current_logger().debug(f'Splay line segment #  {line}')
        roadIndx = 0
        for road in road_list:

            road_coords = list(road.polygon.exterior.coords)
            get_current_logger().debug(f' road name # {road.name} handle # {road.handle}')
            # as dimensions are in metres, need to round points to precision of 1 to find the plots matching.

            roadObj = re_round(road_coords, 1)
            road_Org = Polygon(road_coords)
            roadPoly = Polygon(roadObj)
            # get minimum bounding box around polygon
            box = road_Org.minimum_rotated_rectangle
            # get coordinates of polygon vertices
            x, y = box.exterior.coords.xy
            # get length of bounding box edges
            edge_length = (Point(x[0], y[0]).distance(Point(x[1], y[1])), Point(x[1], y[1]).distance(Point(x[2], y[2])))
            # get length of polygon as the longest edge of the bounding box
            length = round(max(edge_length), 2)
            # get width of polygon as the shortest edge of the bounding box
            width = round(min(edge_length), 2)

            # printLog('verbose',"processing road ", str(roadPoly))
            get_current_logger().debug(f'line intersects roadPoly  {line.intersects(roadPoly)}  road covers line {roadPoly.covers(line)}  line touches road  {line.touches(roadPoly)}')

            # as dimensions are in metres, need to round points to precision of 1 to find the roads matching.

            # printLog('debug',  " Abutting road name:>>  " , road.name )
            # check if road name is ROAD WIDENING then pick the por.width value

            # printLog('verbose','Road Wideninig - overriding with mainroad width ' , road.width )

            if (line.intersects(roadPoly) == True or roadPoly.covers(line) == True or line.touches(roadPoly) == True):
                # printLog('verbose','roadindx is ', roadIndx)

                if 'WIDENING' in road.name.upper():
                    width = float(road.width)
                    roadStr = "".join([str(width), " ", str(road.name).replace("|", '-'), "|", str(lineOrg.length)])
                else:
                    roadStr = "".join([str(road.name).replace("|", '-'), "|", str(lineOrg.length)])

                abuttingValue = abuttingDict.get(str(roadIndx), 0)
                get_current_logger().debug(f'ABUTTING VALUE CHECK **********  {abuttingValue}')
                if (abuttingValue != 0):
                    # check if the value is more than current - use max always
                    pipeIdx = abuttingValue.find('|')
                    if (pipeIdx > -1):
                        rdWidth = float(abuttingValue[pipeIdx + 1:])
                        if (lineOrg.length > rdWidth):
                            # add else skip
                            abuttingDict[str(roadIndx)] = roadStr

                else:
                    abuttingDict[str(roadIndx)] = roadStr


            else:
                get_current_logger().info('No Match Abutting road name:>> ')
            # Fix 6/29/2022 splay issue not detecting the road
            roadIndx = roadIndx + 1

        rPos = rPos + 1

    # fix for finding max abutting road for splay plots - 3/13/2022
    get_current_logger().debug(f'Abutting Roadnames dict =>>>>>>>  {abuttingDict}')
    responseDict = extractMaxRoadWidthFromDict(abuttingDict)

    if (responseDict is None or responseDict.get('errorCode') == 99 or responseDict.get('errorCode') == -1):

        get_current_logger().error(f'problem finding max abutting road for splay  {responseDict}')
        return abuttingDict
    else:
        newResponse = dict()
        newResponse['0'] = responseDict.get('msg')
        return newResponse

def extractAbuttingRoadForIndivPlot(layerName: str, handle: str, plot_poly, road_list):
    # to be used for debugging
    printVerbose = False
    debugHandleList = []  # ['8','19','P-29', 'P-28','P-147','P-161']
    if (handle is not None and handle in debugHandleList):
        printVerbose = True

    abuttingDict = dict()
    onlyCoversDict = dict()
    onlyIntersectsDict = dict()

    if (plot_poly is None or road_list is None):
        return abuttingDict

    get_current_logger().debug(f'layerName : {layerName} ,  handle : {handle} , plot : {plot_poly} , road list : {road_list}')

    roadIndx = 0

    for road in road_list:
        road_coords = list(road.polygon.exterior.coords)
        # if (handle in ['P-29', 'P-28','P-147','P-161']):
        # 	printLog('verbose', ' road coords ', str(road_coords) )
        get_current_logger().debug(f'road coords : {road_coords}')
        # as dimensions are in metres, need to round points to precision of 1 to find the plots matching.

        roadObj = re_round(road_coords, 1)
        road_Org = Polygon(road_coords)
        roadPoly = Polygon(roadObj)
        # get minimum bounding box around polygon
        box = road_Org.minimum_rotated_rectangle
        # get coordinates of polygon vertices
        x, y = box.exterior.coords.xy
        # get length of bounding box edges
        edge_length = (Point(x[0], y[0]).distance(Point(x[1], y[1])), Point(x[1], y[1]).distance(Point(x[2], y[2])))
        # get length of polygon as the longest edge of the bounding box
        length = round(max(edge_length), 2)
        # get width of polygon as the shortest edge of the bounding box
        width = round(min(edge_length), 2)

        # if (printVerbose):
        #     printLog('debug', "processing road ", str(roadPoly))
        get_current_logger().debug(f'processing road  {roadPoly}')


        rPos = 0
        plot_coords = list(plot_poly.exterior.coords)
        rLen = len(plot_coords)
        # as dimensions are in metres, need to round points to precision of 1 to find the roads matching.

        plotList = re_round(plot_coords, 1)
        plotObj = Polygon(plotList)
        plot_org = Polygon(plot_coords)
        # loop each plot vertex
        for plotVertex in plotList:
            # print("processing rPos ", str(rPos))
            if (rPos == (rLen - 1)):
                rTarget = 0
            else:
                rTarget = rPos + 1


            line = LineString([Point(plotList[rPos]), Point(plotList[rTarget])])
            lineOrg = LineString([Point(plot_coords[rPos]), Point(plot_coords[rTarget])])


            coversValue = roadPoly.covers(line)
            intersectsValue = line.intersects(roadPoly)

            if (roadPoly.covers(line) and lineOrg.length > 5):

                roadStr = "".join([str(road.name).replace("|", '-'), "|", str(lineOrg.length)])
                onlyCoversDict[str(roadIndx)] = roadStr


            elif (line.intersects(roadPoly) and lineOrg.length > 5):
                roadStr = "".join([str(road.name).replace("|", '-'), "|", str(lineOrg.length)])
                onlyIntersectsDict[str(roadIndx)] = roadStr

            roadIndx = roadIndx + 1

            rPos = rPos + 1

    if (len(onlyCoversDict) > 0):
        get_current_logger().debug(f'onlycoversDict  {onlyCoversDict}')
        abuttingDict.update(onlyCoversDict)

    if (len(onlyCoversDict) == 0 and len(onlyIntersectsDict) > 0):
        get_current_logger().debug(f'onlyIntersectsDict  {onlyIntersectsDict}')
        abuttingDict.update(onlyIntersectsDict)

    return abuttingDict

def checkGreenStripAroundCWall(plot_poly, cwall_list):
    abuttingList = []

    greenStripPoly = plot_poly.getPolygonObj()

    for cwallObj in cwall_list:
        cwall = cwallObj.getPolygonObj()
        get_current_logger().debug(f"Checking Green Strip around cwall {str(greenStripPoly)}")
        get_current_logger().info(f"Green Strip obj {str(greenStripPoly)}")
        green_coords = list(greenStripPoly.exterior.coords)

        greenStripPolyRe = re_round(green_coords, 0)

        rLen = len(greenStripPolyRe)

        cwall_x, cwall_y = cwall.coords.xy

        call_re = []
        for i, cx in enumerate(cwall_x):
            call_re.append(Point((round(cx, 0)), round(cwall_y[i], 0)))

        call_re_Ls = LineString(call_re)
        cwall_rx_re, cwall_ry_re = call_re_Ls.coords.xy
        get_current_logger().info("cwall re-rounded list ")

        # loop each plot vertex
        for rPos, plotVertex in enumerate(greenStripPolyRe):
            get_current_logger().info(f"processing  rPos {rPos}, plot {plotVertex}")
            if (rPos == (rLen - 1)):
                rTarget = 0
            else:
                rTarget = rPos + 1
            # print ("rPos " , str(greenStripPolyRe[rPos]) )
            # print ("rTarget " , str(greenStripPolyRe[rTarget]) )

            gsline = LineString([Point(greenStripPolyRe[rPos]), Point(greenStripPolyRe[rTarget])])
            gslineOrg = LineString([Point(green_coords[rPos]), Point(green_coords[rTarget])])

            get_current_logger().info(f"greenstrip line segment {gsline}")
            for i, road_ls in enumerate(cwall_rx_re):
                start_point = Point(cwall_rx_re[i], cwall_ry_re[i])

                if (i == len(cwall_rx_re) - 1):
                    end_point = Point(cwall_rx_re[0], cwall_ry_re[0])
                else:
                    end_point = Point(cwall_rx_re[i + 1], cwall_ry_re[i + 1])

                cwall_ls = LineString([start_point, end_point])
                gsaroundCwal = gsline.intersects(cwall_ls)
                if (gsaroundCwal == True):
                    get_current_logger().debug(f"cwall line segment {list(cwall_ls.coords)} length : {cwall_ls.length}road_ls {road_ls}")

                    gsStr = "gs-".join([str(round(gslineOrg.length, 2))])

                    abuttingList.append(
                        {"gs_name": plot_poly.name + ("-") + plot_poly.handle, "cwall_name": cwallObj.name,
                         "cwall": str(round(cwall_ls.length, 2)), "gs": str(round(gslineOrg.length, 2))})

                    get_current_logger().debug(f"green Strip #  with length {gsStr} abutting cwall :  {cwallObj.name} length {cwall_ls.length}")

                    break

                rPos = rPos + 1
    return abuttingList

def analyzeDrawing(msp):
	returnValueDict=dict()
	if (msp is None):
		returnValueDict['CODE']=-1
		returnValueDict['ERROR']='Invalid Inputs. Valid Modelspace required but is None'

		return returnValueDict
	else:

		returnValueDict=analyzeDrawingMsp(msp)
		returnValueDict['CODE']=0
	return returnValueDict

def extractSubPlot(msp, layerToSearch, objectType, onlyClosed=None, onlyOpen=None):
    """ Returns a List of LWPolygons which are closed inside a given layer """
    retList = []

    # checktype -
    if (type(layerToSearch) == list and len(layerToSearch) > 0):
        layerTmp = ''
        isFirst = True
        for layer in layerToSearch:
            if (isFirst):
                layerTmp += 'layer==\"' + layer + '\" | layer==\"' + layer + ' @ 1\"'
                isFirst = False
            else:
                layerTmp += '| layer==\"' + layer + '\" | layer==\"' + layer + ' @ 1\"'
        qry_str = objectType + '[' + layerTmp + ']i'

    #

    elif (type(layerToSearch) == str):
        qry_str = objectType + '[layer==\"' + layerToSearch + '\" | layer==\"' + layerToSearch + ' @ 1\"]i'

    else:
        get_current_logger().debug(f'Invalid layerToSearch - str or list with valid values is required but value is = {layerToSearch}')
        return retList

    get_current_logger().debug('**** QRY STR ' + qry_str)
    # qry_splots = msp.query('LWPOLYLINE [layer=="_IndivSubPlot"]')
    qry_splots = msp.query(qry_str)
    # is_LayerOn = dwg.layers.get(layerToSearch)

    get_current_logger().debug('verbose',
             '\t Search in layer:' + str(layerToSearch) + ' for objectype: ' + objectType + ' found count # ',
             len(qry_splots))

    # Coordinate.default_order = 'xy'

    if (len(qry_splots) == 0):
        return retList

    for entity in qry_splots:
        # print('entity type ', )
        if (layerToSearch not in [LayerMaster.MARGINLINE.value,
                                  LayerMaster.INTERNALROAD.value] and onlyClosed == True and (entity.closed) == 0):
            # printLog('debug', 'onlyClosed is True, ignoring non closed entities from layer ')
            continue
        if (layerToSearch not in [LayerMaster.MARGINLINE.value,
                                  LayerMaster.INTERNALROAD.value] and onlyOpen == True and (entity.closed) == 1):
            # printLog('debug', 'onlyOpen is True, ignoring non closed entities from layer ')
            continue

        splayAbornmalDict = {}
        splayAbnormalHandleList = []

        # BLOCK REFERENCE
        if entity.dxftype() == 'INSERT':
            # printLog('debug', 'Entity ' + entity.dxf.handle)

            polyObj = DxfPoly(layerToSearch, entity.dxftype(), entity.dxf.handle)

            for venty in entity.virtual_entities():

                # printLog('debug', "virtual entity type: " + venty.dxftype() + " color:" + str(venty.dxf.color))
                # Capture the linesegements for Magin
                if (venty.dxftype() == 'LINE'):

                    # printLog('debug', 'segment ' + str(venty.dxf.start) + " to : " + str(venty.dxf.end))
                    segLength = round(ezdxf.math.ConstructionLine(venty.dxf.start, venty.dxf.end).length(), 1)

                    # printLog('debug', 'segment length ' + str(segLength))
                    # MARGINLINE
                    if (layerToSearch == LayerMaster.MARGINLINE.value):
                        polyObj.add_Setback(venty.dxf.color, venty.dxf.start, venty.dxf.end, segLength)

            retList.append(polyObj)

        elif entity.dxftype() == LayerMaster.DWG_LWPOLYLINE.value:
            # printLog('debug', 'Entity ' + entity.dxf.handle + " is closed: " + str(entity.closed))

            polyObj = DxfPoly(layerToSearch, entity.dxftype(), entity.dxf.handle)
            polyObj.setIsClosed(entity.closed)

            for i, point in enumerate(entity.get_points()):
                if entity.closed == 1 and i == 0:
                    startPoint = point
                    rawpoints = entity.get_points()
                    polyObj.set_rawpoints(rawpoints)

                # pos 0=x, 1=y, 2=start width, 3=end width, 4=bulge (for arc )
                xypoint = str(point[0]) + " " + str(point[1])
                # xypoint = Point ( (round(point[0], 2)) ,  (round(point[1], 2)) )

                polyObj.add_2dpoint(xypoint)

                # printLog ('debug','\t\t(' + str(xypoint) +')' )

                if entity.closed == 1 and i + 1 == entity.__len__():
                    # pos 0=x, 1=y, 2=start width, 3=end width, 4=bulge (for arc )
                    xypoint = str(startPoint[0]) + " " + str(startPoint[1])
                    polyObj.add_2dpoint(xypoint)

            for venty in entity.virtual_entities():

                # printLog('debug', "virtual entity type: " + venty.dxftype()
                #          + " color:" + str(venty.dxf.color) + " venty " + str(venty))
                # printLog('debug', str(venty.graphic_properties()))
                # for stairs
                polyObj.setColor(venty.dxf.color)
                # capture the steps
                if (venty.dxftype() == 'LINE'):
                    # printLog('verbose', 'segment ' + str(venty.dxf.start) + " to : " + str(venty.dxf.end) )
                    segLength = round(ezdxf.math.ConstructionLine(venty.dxf.start, venty.dxf.end).length(), 1)

                    # printLog('debug', 'segment length ' + str(segLength))
                    if (layerToSearch == LayerMaster.SPLAY.value):
                        polyObj.add_sideLenghts(segLength)

                if (venty.dxftype() == 'ARC'):

                    bulgeList = list(zip(*entity.get_points('xyb')))[2]
                    nonZeroBulge = [i for i in bulgeList if (i != 0.0)]
                    # printLog('debug', ' nonZeroBulge list  ' + str(nonZeroBulge))
                    # printLog('debug', "nonZeroBulge via listzip @0 " + str(nonZeroBulge[0]))

                    # FIX - 3/20/2022 to skip adding abnormal radius for splay
                    if (len(nonZeroBulge) > 0):

                        p1 = venty.start_point
                        p2 = venty.end_point

                        distanceP1P2 = math.sqrt(((p1[0] - p2[0]) ** 2) + ((p1[1] - p2[1]) ** 2))

                        if (layerToSearch == LayerMaster.SPLAY.value):

                            polyObj.set_bulge_radius_angle_chordlen(nonZeroBulge[0], venty.dxf.radius,
                                                                    venty.dxf.start_angle, (distanceP1P2 / 2))
                        else:
                            # pass chord len which is half of distanceP1P2
                            polyObj.set_bulge_radius_angle_chordlen(nonZeroBulge[0], venty.dxf.radius,
                                                                    venty.dxf.start_angle, (distanceP1P2 / 2))

                    else:

                        get_current_logger().warning('not handled for ' + venty.dxftype() == 'ARC')

                retList.append(polyObj)

        if entity.dxftype() == 'TEXT' or entity.dxftype() == 'MTEXT':
            text_str = ""
            if (entity.dxftype() == 'TEXT'):
                text_str = entity.dxf.text


            else:
                text_str = entity.text

            # check for special chars and clean them
            specialChar = text_str.find(';')

            if (specialChar > -1):
                text_str = text_str[specialChar + 1:]

                # check if it has } tag
                endTag = text_str.find('}')
                if (endTag > -1):

                    text_str = text_str[:endTag]

            pointObj = DxfPoly(layerToSearch, entity.dxftype(), text_str)
            pointObj.setIsClosed(1)

            xypoint = str(entity.dxf.insert.x) + " " + str(entity.dxf.insert.y)
            pointObj.add_2dpoint(xypoint)
            retList.append(pointObj)

    return retList

def populateBldgListObj(masterFloorDict, masterBuildingDict, layerName, parent: None, subtype: None, dxfOfObjs,
                        dxfOfObjNames, objectTDict, updateMasterFloor: bool = True, ignoreClosedFlag: bool = False):

    parentList = [LayerMaster.EXISTINGSTRUCTURE.value, \
                  LayerMaster.PROPOSEDWORK.value, LayerMaster.COMPOUNDWALL.value]

    debugLayerList = [
        'dummy']  # ,LayerMaster.ROOM.value LayerMaster.FLOORINSECTION.value, LayerMaster.PARKING.value LayerMaster.MORTGAGEAREA.value
    if (layerName in debugLayerList):
        debugLevel = 'verbose'

    get_current_logger().debug(f"populateBldgListObj starting  for layer : {layerName}")

    if (layerName is None or dxfOfObjs is None or dxfOfObjNames is None or (
            layerName in parentList and parent is None)):
        error_msg = "One or more required inputs for the method are empty, returning error response. "

        get_current_logger().error(" populateBldgListObj :: " + error_msg)
        return {"result": "error", "msg": error_msg}

    get_current_logger().info(" DXFPoly Obj List len: " + str(len(dxfOfObjs)))
    get_current_logger().info(" DXFPoly Obj Names List len : " + str(len(dxfOfObjNames)))

    # iterate
    inflightObjectTDict = dict()

    flooridx = 1
    for objToProcess in dxfOfObjs:
        if (objToProcess.handle not in inflightObjectTDict):
            inflightObjectTDict[objToProcess.handle] = objToProcess
        else:
            continue

        get_current_logger().debug("processsing handle # " + str(objToProcess.handle) + " points : " + str(
            objToProcess.get_points()) + " isclosed : " + str(objToProcess.isClosed()))

        for ptId in dxfOfObjNames:
            get_current_logger().debug("point ID " + str(ptId.handle))
            xyP = ptId.get_points()[0].split(" ")
            # need this for splay layer for uniqueness of point. you can have multiple splays in a plot
            xyP_Str = xyP[0], "-", xyP[1]
            # @TO DO : Fix bulge for arc
            # bulge = xyP[4]
            pt = Point(round(float(xyP[0]), 2), round(float(xyP[1]), 2))

            get_current_logger().debug('checking point ::: ' + str(xyP_Str))
            if ignoreClosedFlag == False and objToProcess.isClosed() == False:
                get_current_logger().debug('Ignore Close Flag is False and polyline not closed .. breaking loop')
                break

            # Check if ignoreClosedFlag is True applicable for high tension lines which are open not closed polygon
            if (ignoreClosedFlag and objToProcess.isClosed() == False):
                get_current_logger().debug("ignoreClosedFlag is True ")
                # for high tension lines - open line string
                from shapely.geometry import LineString
                polyStr = str(objToProcess.get_points())[0:].translate(translation).strip()
                polyStr = re.sub('[\[\]]', '', polyStr)
                # print  ('debug', "Line String coordinates " , polyStr)

                points = []
                for pointLine in polyStr.split(","):
                    x, y = pointLine.strip().split(" ")
                    # print (" x y are " , x , "," , y )
                    points.append(Point(float(x), float(y)))

                lwpoly = LineString(points)

                if (LayerMaster.COMPOUNDWALL.value in layerName):
                    get_current_logger().debug(" If condition COMPOUNDWALL layer  ")
                    height = extract_dimensions_fromtext(ptId.handle, None, 'h')
                    p5 = BldgBaseObj(ptId.handle, None, ptId.handle, layerName, lwpoly, lwpoly.length, 0, height, 0,
                                     str(objToProcess.handle))
                    objectTDict[ptId.handle + "-" + str(lwpoly.length)] = p5
                    flooridx += 1
                    continue

                if (LayerMaster.ELECTRICLINE.value in layerName):
                    get_current_logger().debug("If condition ELECTRICLINE layer  ")
                    normalized_dist = lwpoly.project(pt, normalized=True)
                    if (normalized_dist < 1):
                        pointToPoly = True
                    else:
                        pointToPoly = False

                    p5 = BldgBaseObj(ptId.handle, None, ptId.handle, layerName, lwpoly, lwpoly.length, 0, 0, 0,
                                     str(objToProcess.handle))
                    objectTDict[ptId.handle + str(xyP_Str)] = p5
                    flooridx += 1
                    continue

            else:
                get_current_logger().debug("In else : ignoreClosedFlag is False")
                # create polygon
                polyStr = str(objToProcess.get_points())[1:-1].translate(translation)
                polyPoints = 'POLYGON ((' + polyStr + '))'
                lwpoly = shapely.wkt.loads(polyPoints)
                # door or window will touches not be within
                if (layerName in [LayerMaster.DOOR.value, LayerMaster.WINDOW.value]):
                    pointToPoly = lwpoly.intersects(pt)
                    get_current_logger().debug(f'checks intersects {pt.intersects(lwpoly)}')

                    get_current_logger().debug(f'checks touches {pt.touches(lwpoly)}')
                    get_current_logger().debug(f'checks overlaps {lwpoly.overlaps(pt)}')
                elif (layerName in [LayerMaster.VENTILATIONSHAFT.value, LayerMaster.SLABCUTOUTVOID.value]):
                    pointToPoly = True
                else:
                    pointToPoly = lwpoly.contains(pt)
                    get_current_logger().debug("Else block contains " + str(pointToPoly))

                get_current_logger().debug("pointToPoly is " + str(pointToPoly))

                # process normal flow i.e. ignoreClosedFlag=False (Default)
                if (pointToPoly == True):
                    get_current_logger().debug("In If condition as pointToPoly is True")

                    box = lwpoly.minimum_rotated_rectangle
                    # get coordinates of polygon vertices
                    x, y = box.exterior.coords.xy
                    # get length of bounding box edges
                    edge_length = (
                    Point(x[0], y[0]).distance(Point(x[1], y[1])), Point(x[1], y[1]).distance(Point(x[2], y[2])))
                    # get length of polygon as the longest edge of the bounding box
                    length = max(edge_length)
                    # get width of polygon as the shortest edge of the bounding box
                    width = min(edge_length)

                    # get_current_logger().debug('debug', "Matched point : "  +  str(xyP_Str) + " with Plot: " , ptId.handle , " area: " , lwpoly.area, ", length: ", length,  ", width: ",  width ," , coordinates :", str(lwpoly))
                    height = width if layerName == LayerMaster.FLOORINSECTION.value else 0.0
                    # reset width
                    if layerName == LayerMaster.FLOORINSECTION.value:
                        width = 0.0

                    area_polygon = lwpoly.area if (ignoreClosedFlag == False) else 0
                    get_current_logger().debug(' area before ' + str(area_polygon))
                    # eshwar - commented - may not be applicable  for building plans 9/24/2020
                    # if arc reduce segment area from polygon
                    if (objToProcess.hasBulge == True and layerName == LayerMaster.RAMP.value):
                        seg_area = objToProcess.get_segment()
                        bounding_box2d = ezdxf.math.BoundingBox2d(
                            [xy[0:2] for xy in list(objToProcess.get_rawpoints())])

                        get_current_logger().debug("box dimensions " + str(bounding_box2d.size))
                        width, length = bounding_box2d.size
                        get_current_logger().debug(f"width and length dimensions {round(width, 2)} : {round(length, 2)}")

                        if (seg_area < 0):
                            area_polygon = area_polygon + seg_area
                        else:
                            area_polygon = area_polygon - seg_area

                        get_current_logger().debug('segment area ' + str(seg_area) + ' net area (minus curved/splay ) is now ' + str(
                                     area_polygon))

                    if (layerName == LayerMaster.BUILDINGNAME.value) and ptId.handle not in objectTDict:
                        get_current_logger().debug(' In Building ' + ptId.handle)
                        # flayer, fname, type, fcoords, fpolygon, flength, fwidth, farea
                        #  	area of floor has not meaning - set to 0.0 here. area_polygon
                        p4 = BuildingName(ptId.handle, layerName, lwpoly)
                        masterBuildingDict[ptId.handle] = p4
                        objectTDict[ptId.handle] = p4

                    elif (parent is not None and layerName in parentList):
                        parentName = ""
                        get_current_logger().debug("Parent is Not None and layer =" + layerName + "In parentList Check " + str(
                                     parentList))
                        # and ptId.handle not in objectTDict
                        for pname, bldObj in parent.items():
                            if (bldObj.polygon.contains(lwpoly)):
                                get_current_logger().debug("Obj belongs to " + pname)
                                p5 = BldgBaseObj(pname, ptId.handle, ptId.handle, layerName, lwpoly, length, width,
                                                 height, area_polygon, str(objToProcess.handle))
                                p5.set_DXFPoly(objToProcess)

                                objectTDict[ptId.handle + str(xyP_Str)] = p5


                    elif (parent is None and layerName == LayerMaster.FLOOR.value) and ptId.handle not in objectTDict:
                        get_current_logger().debug(' In Floor ' + ptId.handle)
                        buildingName = ""
                        for bldname, bldObj in masterBuildingDict.items():
                            if (bldObj.polygon.contains(lwpoly)):
                                get_current_logger().debug(f"floor belongs to {bldname}")
                                buildingName = bldname

                        # check which building the floor maps to
                        floorName = buildingName + "|" + ptId.handle
                        # flayer, fname, type, fcoords, fpolygon, flength, fwidth, farea
                        #  	area of floor has not meaning - set to 0.0 here. area_polygon
                        p6 = Floor(layerName, floorName, buildingName, polyStr, lwpoly, length, width, 0.0)
                        masterFloorDict[floorName] = p6
                        objectTDict[floorName] = p6



                    elif (
                            parent is None and layerName != LayerMaster.FLOOR.value) and objToProcess.handle not in objectTDict:
                        get_current_logger().debug(' In Layer: ' + layerName + ' , Non Floor Type  ' + objToProcess.handle + " floors  cnt " + str(
                                     len(masterFloorDict)))

                        # loop through each floor object list and see where this object below
                        if updateMasterFloor == False:
                            parentName = ""
                            if (layerName == LayerMaster.FLOORINSECTION.value):
                                for bldname, bldObj in masterBuildingDict.items():
                                    if (bldObj.polygon.contains(lwpoly)):
                                        get_current_logger().debug(f"floor In Section belongs to {bldname}")
                                        parentName = bldname

                            p5 = BldgBaseObj(parentName, ptId.handle, ptId.handle, layerName, lwpoly, length, width,
                                             height, area_polygon, str(objToProcess.handle))
                            p5.set_DXFPoly(objToProcess)
                            objectTDict[ptId.handle + str(flooridx)] = p5
                            flooridx += 1
                            # if match found exit the loop without checking other points
                            break  # if you can find the first floor obj , it will not be part of two floors.


                        elif (updateMasterFloor == True):  # and masterFloorDict != None and len(masterFloorDict) > 0

                            for flrId, floorObj in masterFloorDict.items():
                                get_current_logger().debug(f'checking floor# {flrId}')
                                # for types  ROOM which are under CarpetArea
                                if (layerName == LayerMaster.ROOM.value):
                                    get_current_logger().debug('Room type ')

                                    for dwellUnit in floorObj.dwelUnits:
                                        # check which unit the room is part of
                                        if (dwellUnit.polygon.contains(lwpoly)):
                                            get_current_logger().debug('debug', '  room belongs to ' + flrId + "|" + dwellUnit.name)
                                            # flrId
                                            parentName = flrId + "|" + dwellUnit.name

                                            p5 = BldgBaseObj(parentName, None, ptId.handle, layerName, lwpoly, length,
                                                             width, height, area_polygon, str(objToProcess.handle))

                                            floorObj.add_tofloor(layerName, p5)

                                            # replace the Floor Obj with updatedFloor Obj
                                            masterFloorDict[flrId] = floorObj
                                            # flooridx = flooridx + 1
                                            objectTDict[objToProcess.handle] = p5

                                            # if match found exit the loop without checking other points
                                            break  # if you can find the first floor obj , it will not be part of two floors.

                                        else:
                                            continue  # go over next dwellunit in the floor

                                elif (layerName == LayerMaster.DOOR.value or layerName == LayerMaster.WINDOW.value):
                                    get_current_logger().debug( 'DOOR /WINDOW  type ')

                                    for roomUnit in floorObj.roomUnits:
                                        # check which unit the room is part of
                                        if (roomUnit.polygon.touches(lwpoly)):
                                            get_current_logger().debug('  door/win intersects to ' + flrId + "|" + roomUnit.name)
                                            # flrId
                                            parentName = flrId + "|" + roomUnit.name

                                            p5 = BldgBaseObj(parentName, None, ptId.handle, layerName, lwpoly, length,
                                                             width, height, area_polygon, str(objToProcess.handle))

                                            floorObj.add_tofloor(layerName, p5)

                                            # replace the Floor Obj with updatedFloor Obj
                                            masterFloorDict[flrId] = floorObj
                                            # flooridx = flooridx + 1
                                            objectTDict[objToProcess.handle] = p5
                                        else:
                                            continue  # go over next dwellunit in the floor

                                else:  # non room type tag at floor level

                                    # check which floor this object belongs to
                                    fpolygon = floorObj.fpolygon

                                    if (fpolygon.contains(lwpoly)):
                                        get_current_logger().debug(" Object " + ptId.handle + " is with in floor  " + floorObj.fname)
                                        ramp_length = 0.0
                                        ramp_height = 0.0
                                        ramp_width = 0.0
                                        gradientVal = 0.0
                                        # if layer is Ramp set gradient/slope from the MTEXT Value for RAMP
                                        if (layerName == LayerMaster.RAMP.value):
                                            ramp_length = extract_dimensions_fromtext(ptId.handle.upper(), None, 'LONG')
                                            ramp_height = extract_dimensions_fromtext(ptId.handle.upper(), 'LONG', 'H')
                                            ramp_width = extract_dimensions_fromtext(ptId.handle.upper(), 'H', 'W')

                                            gradientVal = calc_gradient(ramp_length, ramp_height)

                                            area_polygon = str(float(ramp_width) * float(ramp_length))
                                            get_current_logger().debug(f'gradientVal {gradientVal} type {type(gradientVal)}')
                                        #

                                        # override passage width (min.) from the MTEXT Value
                                        if (layerName == LayerMaster.PASSAGE.value):
                                            width = float(extract_dimensions_fromtext(ptId.handle.upper(), None, 'W'))
                                            get_current_logger().debug(f"Width for passage is {width}")

                                        get_current_logger().debug(' before bldBaseObj ')
                                        p5 = BldgBaseObj(flrId, None, ptId.handle, layerName, lwpoly, length, width,
                                                         height, area_polygon, str(objToProcess.handle))
                                        get_current_logger().debug(' after bldBaseObj')
                                        if (gradientVal > 0):
                                            get_current_logger().debug(' in if check >0')
                                            p5.set_gradient(gradientVal)

                                        floorObj.add_tofloor(layerName, p5)

                                        # replace the Floor Obj with updatedFloor Obj
                                        masterFloorDict[flrId] = floorObj
                                        # flooridx = flooridx + 1
                                        objectTDict[objToProcess.handle] = p5

                                        # if match found exit the loop without checking other points
                                        break  # if you can find the first floor obj , it will not be part of two floors.
                        else:
                            get_current_logger().debug("populateBldgListObj:  In else condition updateMasterFloor = True ")

                    else:
                        get_current_logger().debug("populateBldgListObj : layerName and condition not supported " + layerName + " ObjToProc in Dict  " + str(
                                     objToProcess.handle not in objectTDict))
                else:
                    get_current_logger().debug("populateBldgListObj :  else block pointToPoly ")

    inflightObjectTDict = ''

    get_current_logger().debug("populateBldgListObj completed for : " + layerName)

    return {"result": "OK", "data": objectTDict, "MASTERFLOORDICTKEY": masterFloorDict,
            "MASTERBUILDINGDICTKEY": masterBuildingDict}  # OK

def populateIndivPolyListObj(layerName, subPlots, pltNames, plotList, plotDict, internalRoadList: None):
    if (layerName is None or subPlots is None or pltNames is None or plotList is None):
        error_msg = "One or more of required inputs are None. Returning error response for " + layerName

        get_current_logger().error("populateIndivPolyListObj :: " + error_msg)

        return {"result": "error", "msg": error_msg}

    get_current_logger().info("subplots len " + str(len(subPlots)))
    get_current_logger().info("pltNames len " + str(len(pltNames)))
    # iterate through subPlots
    processedPlotDict = dict()
    matchedPlotDict = dict()

    for plotObj in subPlots:

        get_current_logger().debug("Processsing handle # " + str(plotObj.handle) + " points : " + str(
            plotObj.get_points()) + " isclosed : " + str(plotObj.isClosed()))

        if (plotObj.handle not in processedPlotDict):
            processedPlotDict[plotObj.handle] = plotObj.handle
        else:
            continue

        for ptId in pltNames:

            get_current_logger().debug("point ID " + str(ptId.handle))
            xyP = ptId.get_points()[0].split(" ")
            # need this for splay layer for uniqueness of point. you can have multiple splays in a plot
            xyP_Str = xyP[0], "-", xyP[1]

            pt = Point(round(float(xyP[0]), 2), round(float(xyP[1]), 2))
            get_current_logger().debug(" point ID " + str(ptId.handle) + '  point ::: ' + str(xyP_Str))

            if plotObj.isClosed() == False:
                get_current_logger().info('polyline not closed object breaking loop')
                break

            polyStr = str(plotObj.get_points())[1:-1].translate(translation)
            get_current_logger().debug(f"Polygon String coordates {polyStr}")
            # create a ploygon
            polyPoints = 'POLYGON ((' + polyStr + '))'

            lwpoly = shapely.wkt.loads(polyPoints)
            processedPlotDict[plotObj.handle] = round(lwpoly.area, 2)

            # or pt.distance(lwpoly) < 0.5
            if (lwpoly.contains(pt) or pt.touches(lwpoly) or pt.intersects(lwpoly)):
                get_current_logger().debug( 'matched ' + ptId.handle + " (x,y) " + str(
                    xyP) + " polyObj#  handle : " + plotObj.handle + " points: " + str(plotObj.get_points()))
                matchedPlotDict[plotObj.handle] = ptId.handle
                # foundMatch = True
                # get minimum bounding box around polygon
                box = lwpoly.minimum_rotated_rectangle
                # get coordinates of polygon vertices
                x, y = box.exterior.coords.xy
                # get length of bounding box edges
                edge_length = (
                Point(x[0], y[0]).distance(Point(x[1], y[1])), Point(x[1], y[1]).distance(Point(x[2], y[2])))
                # get length of polygon as the longest edge of the bounding box
                length = max(edge_length)
                # get width of polygon as the shortest edge of the bounding box
                width = min(edge_length)

                area_polygon = lwpoly.area
                get_current_logger().debug( ' area before ' + str(area_polygon))

                # if arc reduce segment area from polygon
                if (plotObj.hasBulge == True or plotObj.splayOverride == True):
                    seg_area = plotObj.get_segment()
                    get_current_logger().debug(f"bbox xyseb rawpoints {plotObj.get_rawpoints()} 2d on;y {plotObj.get_points()}")

                    # print("as 2d str ", str(plotObj.get_points())[1:-1].translate(translation))
                    bounding_box2d = ezdxf.math.BoundingBox2d([xy[0:2] for xy in list(plotObj.get_rawpoints())])
                    get_current_logger().debug(f"bounding_box2d  {bounding_box2d}")

                    sizeOfSideLen = len(plotObj.get_sideLengths())
                    get_current_logger().debug(f"splay override? {plotObj.splayOverride} size of sideLengths : {sizeOfSideLen}")
                    # if splay overide was done then use those for width/length else default bounding box method
                    if (plotObj.splayOverride == True and sizeOfSideLen == 2):
                        sideLengths = plotObj.get_sideLengths()
                        get_current_logger().debug("using splay override dimensions " + str(sideLengths))
                        length = sideLengths[0]
                        width = sideLengths[1]

                    else:
                        get_current_logger().debug("box dimensions " + str(bounding_box2d.size))
                        width, length = bounding_box2d.size
                        get_current_logger().debug(f"handle# {plotObj.handle} width and length dimensions {round(width, 2)}: {round(length, 2)}")

                    get_current_logger().debug(f" handle# {plotObj.handle} area_polygon area {area_polygon}")
                    if (seg_area < 0):
                        area_polygon = area_polygon + seg_area
                    else:
                        if (seg_area > 10 or seg_area > area_polygon):
                            area_polygon = round(float(area_polygon) * .3, 2)
                            get_current_logger().error('Possible Invalid SPLAY area_polygon area ' + str(area_polygon))
                        else:
                            area_polygon = area_polygon - seg_area

                    get_current_logger().debug('segment area ' + str(seg_area) + ' splay area is now ' + str(area_polygon))

                # whitelisted items to add -
                whiteListLayersToAdd = [LayerMaster.SURRENDERTOAUTH.value, LayerMaster.LEFTOVEROWNERSLAND.value,
                                        LayerMaster.SPLAY.value, \
                                        LayerMaster.WATERBODIES.value, LayerMaster.NALAROAD.value,
                                        LayerMaster.BUFFERZONE.value, \
                                        LayerMaster.MORTGAGEAREA.value, LayerMaster.SOCIALINFRA.value,
                                        LayerMaster.ORGOPENSPACE.value, \
                                        LayerMaster.ACCESSORYUSE.value, LayerMaster.MAINROAD.value,
                                        LayerMaster.INTERNALROAD.value, LayerMaster.GRIDROAD.value, \
                                        LayerMaster.ROADWIDENING.value, LayerMaster.MARGINLINE.value,
                                        LayerMaster.CYCLETRACK.value, \
                                        LayerMaster.UTILITY_MISC.value, LayerMaster.RESERVEDAREA.value,
                                        LayerMaster.PARKING.value, \
                                        LayerMaster.TRANSFER_OF_SETBACKS.value, LayerMaster.BUA_BEFORE_CONCESSION.value]

                # if (layerName == LayerMaster.SURRENDERTOAUTH.value or layerName == LayerMaster.LEFTOVEROWNERSLAND.value or  layerName == LayerMaster.WATERBODIES.value or layerName == LayerMaster.NALAROAD.value or  layerName == LayerMaster.BUFFERZONE.value or  layerName == LayerMaster.MORTGAGEAREA.value or  layerName == LayerMaster.SOCIALINFRA.value or  layerName == LayerMaster.ORGOPENSPACE.value or layerName == LayerMaster.ACCESSORYUSE.value or  layerName == "_Splay" or layerName == "_MainRoad" or layerName == "_InternalRoad" or layerName == "_RoadWidening") and plotObj.handle not in plotDict:

                if (layerName in whiteListLayersToAdd and plotObj.handle not in plotDict):
                    p6 = IndivSubPlot(ptId.handle, layerName, lwpoly, length, width, area_polygon, plotObj.handle)
                    # need this to check splay dimensions based on the road width -
                    if (layerName == "_Splay"):
                        bbox = lwpoly.bounds
                        splayPoly = shapely.geometry.box(*bbox, ccw=True)
                        get_current_logger().debug(f"SPLAY handle# {ptId.handle}")
                        abuttingroad_frontage = extractAbuttingRoadForSplay(splayPoly, internalRoadList)
                        get_current_logger().info(f"SPLAY abutting ******* {abuttingroad_frontage}")
                        p6.add_frontage_abuttingroad(abuttingroad_frontage)

                    plotList.append(p6)
                    plotDict[plotObj.handle] = p6

                    # if match found exit the loop without checking other points
                    break


                elif (layerName == "_IndivSubPlot") and ptId.handle not in plotDict:
                    abuttingroad_frontage = extractAbuttingRoadForIndivPlot(layerName, ptId.handle, lwpoly,
                                                                            internalRoadList)
                    if (ptId.handle in ['ABC']):  # '05','04','8', '33','P-147','P-161']):
                        get_current_logger().debug(" Handle# " + str(ptId.handle) + " area# " + str(
                            area_polygon) + " abutting frontage value# " + str(abuttingroad_frontage))
                    actualWidth = getMinWidthIrregularObjects(lwpoly)
                    get_current_logger().debug(f'plot# {ptId.handle} Actual vs BOundedBox Width {actualWidth}')
                    p6 = IndivSubPlot(ptId.handle, layerName, lwpoly, length, width, area_polygon, plotObj.handle)
                    p6.add_frontage_abuttingroad(abuttingroad_frontage)
                    plotList.append(p6)
                    plotDict[ptId.handle] = p6
                    # if match found exit the loop without checking other points
                    break

    warnings = []

    for key in processedPlotDict.keys():
        if not key in matchedPlotDict:
            msg = 'Type ' + layerName + ' UnMatched DWG Ref Handle # ' + str(key) \
                  + ' area = ' + str(processedPlotDict.get(key, '')) + '. '
            get_current_logger().error(msg)

    return {"result": "OK", "data_dict": plotDict, "data_list": plotList, "warnings": warnings}

def process_slabcutoutvoid(
        masterFloorDict,
        masterBuildingDict,
        layerName,
        parent,
        subtype,
        dxfOfObjs,
        dxfOfObjNames,   # kept for compatibility (not used)
        objectTDict,
        updateMasterFloor=True,
        ignoreClosedFlag=False):

    get_current_logger().info(f"process_slabcutoutvoid starting for layer : {layerName}")

    inflightObjectTDict = {}
    flooridx = 1

    for objToProcess in dxfOfObjs:

        # avoid duplicate processing
        if objToProcess.handle in inflightObjectTDict:
            continue
        inflightObjectTDict[objToProcess.handle] = objToProcess

        get_current_logger().info(f"processing handle # {objToProcess.handle}")

        if not ignoreClosedFlag and not objToProcess.isClosed():
            continue

        polyStr = str(objToProcess.get_points())[1:-1].translate(translation)
        polyPoints = 'POLYGON ((' + polyStr + '))'

        try:
            lwpoly = shapely.wkt.loads(polyPoints)
        except Exception as e:
            get_current_logger().error(f"Invalid polygon for handle {objToProcess.handle}: {e}")
            continue

        pointToPoly = True

        if not pointToPoly:
            continue

        box = lwpoly.minimum_rotated_rectangle
        x, y = box.exterior.coords.xy

        edge_length = (
            Point(x[0], y[0]).distance(Point(x[1], y[1])),
            Point(x[1], y[1]).distance(Point(x[2], y[2]))
        )

        length = max(edge_length)
        width = min(edge_length)

        height = width if layerName == LayerMaster.FLOORINSECTION.value else 0.0

        if layerName == LayerMaster.FLOORINSECTION.value:
            width = 0.0

        area_polygon = lwpoly.area if not ignoreClosedFlag else 0

        elif_condition = (
            parent is None and layerName != LayerMaster.FLOOR.value
        )

        if elif_condition and objToProcess.handle not in objectTDict:

            if not updateMasterFloor:

                parentName = ""

                if layerName == LayerMaster.FLOORINSECTION.value:
                    for bldname, bldObj in masterBuildingDict.items():
                        if bldObj.polygon.contains(lwpoly):
                            parentName = bldname
                            break

                p5 = BldgBaseObj(
                    parentName,
                    objToProcess.handle,
                    objToProcess.handle,
                    layerName,
                    lwpoly,
                    length,
                    width,
                    height,
                    area_polygon,
                    str(objToProcess.handle)
                )

                p5.set_DXFPoly(objToProcess)
                objectTDict[objToProcess.handle + str(flooridx)] = p5
                flooridx += 1

            else:
                for flrId, floorObj in masterFloorDict.items():

                    fpolygon = floorObj.fpolygon

                    if fpolygon.contains(lwpoly):

                        p5 = BldgBaseObj(
                            flrId,
                            None,
                            objToProcess.handle,
                            layerName,
                            lwpoly,
                            length,
                            width,
                            height,
                            area_polygon,
                            str(objToProcess.handle)
                        )

                        floorObj.add_tofloor(layerName, p5)
                        masterFloorDict[flrId] = floorObj
                        objectTDict[objToProcess.handle] = p5

                        break  # same behavior as original

        else:
            get_current_logger().info("SLABCUTOUTVOID: condition not supported")

    inflightObjectTDict.clear()

    get_current_logger().info("process_slabcutoutvoid completed")

    return {
        "result": "OK",
        "data": objectTDict,
        "MASTERFLOORDICTKEY": masterFloorDict,
        "MASTERBUILDINGDICTKEY": masterBuildingDict
    }

# def populateBldgPolyListObj(masterFloorDict, layerName, dxfOfObjs, objectTDict, updateMasterFloor: True, parent: None):
#
#     parentList = [LayerMaster.AREATABLE.value \
#         , LayerMaster.ORGOPENSPACE.value]
#     debugLevel = 'debug'
#
#     if (layerName in ['_ResiBUAOutline']):
#         debugLevel = 'verbose'
#
#     if (layerName is None or dxfOfObjs is None):
#         error_msg = "One or more required inputs for the method are empty, returning error response "
#         get_current_logger().error(" populateBldgPolyListObj  :: " + error_msg)
#         return {"result": "error", "msg": error_msg}
#
#     skippedList = []
#
#     # iterate through subPlots
#     processedObjectTDict = dict()
#     for plotObj in dxfOfObjs:
#         if (plotObj.handle not in processedObjectTDict):
#             processedObjectTDict[plotObj.handle] = plotObj.handle
#         else:
#             continue
#
#         if not plotObj.isClosed() or len(plotObj.get_points())<3:
#             continue
#
#         get_current_logger().debug(f"Layer {layerName} processsing : {plotObj.handle} points {plotObj.get_points()} updateMasterFloor Flag : {updateMasterFloor}")
#
#         polyStr = str(plotObj.get_points())[1:-1].translate(translation)
#         get_current_logger().debug(f"polyStr Polygon = {polyStr}")
#         polyPoints = 'POLYGON ((' + polyStr + '))'
#         get_current_logger().debug(polyPoints)
#         lwpoly = None
#         try:
#             lwpoly = shapely.wkt.loads(polyPoints)
#             # get minimum bounding box around polygon
#             box = lwpoly.minimum_rotated_rectangle
#             get_current_logger().debug(f"box type {type(box)}")
#             server_logger.debug(debugLevel, " value " + str(box))
#         except:
#             ex_type, ex_value, ex_traceback = sys.exc_info()
#
#             s_msg = "Problem processing Layer -" + layerName + "  DXF handle -" + plotObj.handle + " Skipping record due to " + str(
#                 ex_value)
#
#             skippedList.append(s_msg)
#
#             break
#
#         # print( '\t matched ' + ptId.handle + " (x,y) " + str(xyP) + " polyObj#  handle : "  + plotObj.handle + " points: "  +  str(plotObj.get_points()) )
#
#         # get coordinates of polygon vertices
#         x, y = box.exterior.coords.xy
#
#         # get length of bounding box edges
#         edge_length = (Point(x[0], y[0]).distance(Point(x[1], y[1])), Point(x[1], y[1]).distance(Point(x[2], y[2])))
#         # get length of polygon as the longest edge of the bounding box
#         length = max(edge_length)
#         # get width of polygon as the shortest edge of the bounding box
#         width = min(edge_length)
#         height = width if layerName == LayerMaster.FLOORINSECTION.value else 0.0
#         # reset width
#         if layerName == LayerMaster.FLOORINSECTION.value:
#             width = 0.0
#
#         server_logger.debug(f"Plot: {plotObj.handle} area: {lwpoly.area} length: {length} height:{height} width: {width} coordinates :{lwpoly}")
#
#         # loop through each object list and see where this object belongs
#         if (layerName not in parentList and updateMasterFloor == True and masterFloorDict != None and len(
#                 masterFloorDict) > 0):
#             for flrId, floorObj in masterFloorDict.items():
#                 server_logger.debug('checking floor# ', flrId)
#                 # check which floor this object belongs to
#                 fpolygon = floorObj.fpolygon
#                 if (fpolygon.contains(lwpoly)):
#                     server_logger.debug(" Object " + plotObj.handle + " is with in floor  " + floorObj.fname)
#
#                     p5 = BldgBaseObj(flrId, None, plotObj.handle, layerName, lwpoly, length, width, height, lwpoly.area,
#                                      plotObj.handle)
#                     floorObj.add_tofloor(layerName, p5)
#
#                     # replace the Floor Obj with updatedFloor Obj
#                     masterFloorDict[flrId] = floorObj
#                     # flooridx = flooridx + 1
#                     if plotObj.handle not in objectTDict:
#                         objectTDict[plotObj.handle] = p5
#                     # if match found exit the loop without checking other points
#                     break  # if you can find the first floor obj , it will not be part of two floors.
#         elif (layerName not in parentList and updateMasterFloor == False):
#
#             p5 = BldgBaseObj(plotObj.handle, None, plotObj.handle, layerName, lwpoly, length, width, height,
#                              lwpoly.area, plotObj.handle)
#             if plotObj.handle not in objectTDict:
#                 objectTDict[plotObj.handle] = p5
#                 # if match found exit the loop without checking other points
#                 break  # if you can find the first floor obj , it will not be part of two floors.
#
#         elif (parent is not None and layerName in parentList and plotObj.handle not in objectTDict):
#             # Main table logic goes here
#             # check if current lwpoly is part of the parent and map it in layername
#             parentName = ""
#             for parentKey, parentValue in parent.items():
#                 if (parentValue.polygon.contains(lwpoly)):
#                     server_logger.error("Object is part of the Parent " + parentValue.name)
#                     parentName = parentKey + "|" + plotObj.handle
#                     p5 = BldgBaseObj(parentName, None, plotObj.handle, layerName, lwpoly, length, width, height,
#                                      lwpoly.area, plotObj.handle)
#                     objectTDict[plotObj.handle] = p5
#
#                     break  # single object can belong to 1 parent
#         else:
#             server_logger.warning("Unhandled condition ")
#     processedObjectTDict = ''
#     if (len(skippedList) == 0):
#         resultStatus = "OK"
#         return {"result": resultStatus, "data": objectTDict, "masterFloorDict": masterFloorDict}
#
#     else:
#         resultStatus = "warning"
#         return {"result": resultStatus, "data": objectTDict, "masterFloorDict": masterFloorDict,
#                 "msg": str(skippedList)}

def populateBldgPolyListObj(masterFloorDict, layerName, dxfOfObjs,
                            objectTDict, updateMasterFloor=True, parent=None):

    parentList = [
        LayerMaster.AREATABLE.value,
        LayerMaster.ORGOPENSPACE.value
    ]

    debugLevel = 'debug'

    if layerName in ['_ResiBUAOutline']:
        debugLevel = 'verbose'

    if layerName is None or dxfOfObjs is None:
        error_msg = "One or more required inputs for the method are empty"
        get_current_logger().error("populateBldgPolyListObj :: " + error_msg)

        return {
            "result": "error",
            "msg": error_msg
        }

    skippedList = []
    processedObjectTDict = {}

    for plotObj in dxfOfObjs:

        try:

            # Skip duplicate handles
            if plotObj.handle in processedObjectTDict:
                continue

            processedObjectTDict[plotObj.handle] = plotObj.handle

            # Validate polygon
            if not plotObj.isClosed():
                get_current_logger().warning(
                    f"Skipping open polygon : {plotObj.handle}"
                )
                continue

            points = plotObj.get_points()

            if points is None or len(points) < 3:
                get_current_logger().warning(
                    f"Skipping invalid polygon (<3 points) : {plotObj.handle}"
                )
                continue

            get_current_logger().debug(
                f"Layer {layerName} processing : "
                f"{plotObj.handle} "
                f"points {points} "
                f"updateMasterFloor Flag : {updateMasterFloor}"
            )

            polyStr = str(points)[1:-1].translate(translation)

            get_current_logger().debug(f"polyStr Polygon = {polyStr}")

            polyPoints = f'POLYGON (({polyStr}))'

            get_current_logger().debug(polyPoints)

            # Create polygon
            lwpoly = shapely.wkt.loads(polyPoints)

            # Validate shapely polygon
            if lwpoly is None:
                skippedList.append(
                    f"Unable to create polygon for {plotObj.handle}"
                )
                continue

            if lwpoly.is_empty:
                skippedList.append(
                    f"Empty polygon for {plotObj.handle}"
                )
                continue

            if not lwpoly.is_valid:
                get_current_logger().warning(
                    f"Invalid polygon detected : {plotObj.handle}"
                )

                # try fixing polygon
                lwpoly = lwpoly.buffer(0)

                if not lwpoly.is_valid:
                    skippedList.append(
                        f"Invalid polygon for {plotObj.handle}"
                    )
                    continue

            if lwpoly.area <= 0:
                skippedList.append(
                    f"Zero area polygon for {plotObj.handle}"
                )
                continue

            # Get minimum rotated rectangle
            box = lwpoly.minimum_rotated_rectangle

            get_current_logger().debug(f"box type {type(box)}")
            get_current_logger().debug(f"{debugLevel} value {box}")

            # Handle LineString issue safely
            if box.geom_type == "Polygon":

                x, y = box.exterior.coords.xy

                if len(x) < 3 or len(y) < 3:
                    skippedList.append(
                        f"Invalid rectangle coordinates for {plotObj.handle}"
                    )
                    continue

                edge_length = (
                    Point(x[0], y[0]).distance(Point(x[1], y[1])),
                    Point(x[1], y[1]).distance(Point(x[2], y[2]))
                )

                length = max(edge_length)
                width = min(edge_length)

            elif box.geom_type == "LineString":

                get_current_logger().warning(
                    f"minimum_rotated_rectangle returned "
                    f"LineString for {plotObj.handle}"
                )

                coords = list(box.coords)

                if len(coords) < 2:
                    skippedList.append(
                        f"Invalid LineString for {plotObj.handle}"
                    )
                    continue

                length = Point(coords[0]).distance(Point(coords[-1]))
                width = 0.0

            else:

                skippedList.append(
                    f"Unsupported geometry type "
                    f"{box.geom_type} for {plotObj.handle}"
                )

                continue

            height = (
                width
                if layerName == LayerMaster.FLOORINSECTION.value
                else 0.0
            )

            if layerName == LayerMaster.FLOORINSECTION.value:
                width = 0.0

            get_current_logger().debug(
                f"Plot: {plotObj.handle} "
                f"area: {lwpoly.area} "
                f"length: {length} "
                f"height:{height} "
                f"width: {width} "
                f"coordinates :{lwpoly}"
            )

            # =========================================================
            # FLOOR MAPPING
            # =========================================================

            if (
                layerName not in parentList
                and updateMasterFloor is True
                and masterFloorDict is not None
                and len(masterFloorDict) > 0
            ):

                for flrId, floorObj in masterFloorDict.items():

                    get_current_logger().debug(f'checking floor# {flrId}')

                    fpolygon = floorObj.fpolygon

                    if fpolygon.contains(lwpoly):

                        get_current_logger().debug(
                            f"Object {plotObj.handle} "
                            f"is within floor {floorObj.fname}"
                        )

                        p5 = BldgBaseObj(
                            flrId,
                            None,
                            plotObj.handle,
                            layerName,
                            lwpoly,
                            length,
                            width,
                            height,
                            lwpoly.area,
                            plotObj.handle
                        )

                        floorObj.add_tofloor(layerName, p5)

                        masterFloorDict[flrId] = floorObj

                        if plotObj.handle not in objectTDict:
                            objectTDict[plotObj.handle] = p5

                        break

            # =========================================================
            # NORMAL OBJECT
            # =========================================================

            elif (
                layerName not in parentList
                and updateMasterFloor is False
            ):

                p5 = BldgBaseObj(
                    plotObj.handle,
                    None,
                    plotObj.handle,
                    layerName,
                    lwpoly,
                    length,
                    width,
                    height,
                    lwpoly.area,
                    plotObj.handle
                )

                if plotObj.handle not in objectTDict:
                    objectTDict[plotObj.handle] = p5

            # =========================================================
            # PARENT OBJECT MAPPING
            # =========================================================

            elif (
                parent is not None
                and layerName in parentList
                and plotObj.handle not in objectTDict
            ):

                for parentKey, parentValue in parent.items():

                    if parentValue.polygon.contains(lwpoly):

                        get_current_logger().debug(
                            f"Object is part of Parent "
                            f"{parentValue.name}"
                        )

                        parentName = f"{parentKey}|{plotObj.handle}"

                        p5 = BldgBaseObj(
                            parentName,
                            None,
                            plotObj.handle,
                            layerName,
                            lwpoly,
                            length,
                            width,
                            height,
                            lwpoly.area,
                            plotObj.handle
                        )

                        objectTDict[plotObj.handle] = p5

                        break

            else:
                get_current_logger().warning(
                    f"Unhandled condition for {plotObj.handle}"
                )

        except Exception as ex:

            ex_type, ex_value, ex_traceback = sys.exc_info()

            s_msg = (
                f"Problem processing Layer - {layerName} "
                f"DXF handle - {plotObj.handle} "
                f"Skipping record due to {str(ex_value)}"
            )

            get_current_logger().exception(s_msg)

            skippedList.append(s_msg)

            continue

    processedObjectTDict = ''

    if len(skippedList) == 0:

        return {
            "result": "OK",
            "data": objectTDict,
            "masterFloorDict": masterFloorDict
        }

    return {
        "result": "warning",
        "data": objectTDict,
        "masterFloorDict": masterFloorDict,
        "msg": str(skippedList)
    }

def clean_text_mtext_label(text_label:str):

    text=plain_mtext(text_label)
    text=text.strip().replace("\n"," ")
    return text

class ObjectByType:
    def __init__(self, layerName):
        self.type = layerName
        self.baseList = []
        self.baseUnitNames = []
        self.baseUnitDict = dict()
        self.baseUnitFinalList = []  # used for open layout

    def getBaseList(self):
        return self.baseList

    def setBaseList(self, baseList):
        self.baseList = baseList

    def getBaseUnitNames(self):
        return self.baseList

    def setBaseUnitNames(self, baseUnitNames):
        self.baseUnitNames = baseUnitNames

    def getBaseUnitDict(self):
        return self.baseUnitDict

    def setBaseUnitDict(self, baseUnitDict):
        self.baseUnitDict = baseUnitDict

    def setBaseUnitFinalList(self, baseUnitFinalList):
        self.baseUnitFinalList = baseUnitFinalList

    def getBaseUnitFinalList(self):
        return self.baseUnitFinalList

    # to add the datetime stamp in regular print statements

class GenReportData:

    def __init__(self,req_id,combinedObjects,file_name,dxf_dir,status_dict:dict,requesttimeobj,isComboRequest: bool = False,):
        self.req_id= req_id
        self.combinedObjects=combinedObjects
        self.filename=file_name
        self.isComboRequest=isComboRequest
        self.gen_report_resp = dict()
        self.reportExtractor = []
        self.request_params=self.combinedObjects.get('request_params', {})

        self.gatedCommunityFlag = self.request_params.get('isGatedCommunity', False)
        self.runOnlyCombinedUtil = self.request_params.get('runOnlyCombinedUtil', False)

        self.gatedCommunityFlag = "True" if str(self.gatedCommunityFlag).lower() == "true" else "False"
        self.runOnlyCombinedUtil = "True" if str(self.runOnlyCombinedUtil).lower() == "true" else "False"

        self.masterFloorDict= self.combinedObjects["MASTERFLOORDICTKEY"] if self.combinedObjects.get("MASTERFLOORDICTKEY",
                                                                                   0) != 0 else {}

        self.dxf_dir=dxf_dir
        self.modelspace_dwg = self.combinedObjects.get('modelspace', {})
        self.totalNalaArea=0.0
        self.warnings=[]
        self.errors=[]
        self.subtype=self.request_params.get('subtype', 'N/A')

        self.purposecode = self.request_params.get('purposecode', 'N/A')
        self.authority = self.request_params.get('authority', '-')
        self.location = self.request_params.get('location', '-')
        self.subuse = self.request_params.get('subuse', '-')

        self.plan_text_elementsDict = self.combinedObjects.get('PLAN_TEXT_ELEMENTS', 0)
        self.coverageAreaPercentDict = self.combinedObjects.get(LayerMaster.AREATABLE.value, 0)

        self.coverageAreaPercent = self.coverageAreaPercentDict.get('COVERAGE_AREA_PERCENT', 0)
        self.existingCoverageArea=0.0
        self.totalNetplotArea=0.0
        self.totalTotArea = 0.0
        self.totalParkingArea=0.0
        self.totalProposedBUAArea=0.0
        self.stackParkingArea=0.0
        self.totalMortgageArea=0.0

        self.totalBUAArea=0.0
        self.totalAccessoryUseArea=0.0
        self.totalVentilationArea=0.0
        self.totalSlabCutoutArea=0.0
        self.totalBalconyArea=0.0
        self.totalRampArea=0.0
        self.totalStairArea=0.0
        self.totalLiftArea=0.0
        self.totalProposedBUAArea=0.0
        self.totalNetBUAArea=0.0
        self.totalDwellUnitNo=0
        self.totalParkingArea=0.0
        self.totalStackParkingArea=0.0

        self.bldg_heights_dict=dict()
        self.jsAccessAreaBuaTypeInfo=[]
        self.setBacksDictConsolidated=dict()
        self.podiumSetBacksDictConsolidated=dict()
        self.abuttingRoadPropRequiredDict = dict()

        self.status_dict=status_dict
        self.progress= 0

        self.main2min_progress = 40
        self.main2max_progress = 80
        self.requesttimeobj=requesttimeobj
        self.pipeline_start_time= time.time()


    def get_summary_details(self):

        request_params = self.combinedObjects.get('request_params', {})

        purposecode = request_params.get('purposecode', 'N/A')

        purposedesc = getPurposeDesc(purposecode)
        request_params['purposedesc'] = purposedesc  # update the desc in request params for reporting here

        report_dwg_warnings = self.combinedObjects.get('DWG_WARNINGS', [])

        get_current_logger().info(
            f'current dwg warnings count # {str(len(report_dwg_warnings))} errors:{str(report_dwg_warnings)}')

        get_current_logger().info(f"REPORT GENERATION for {self.filename}")
        dateTimeObj = datetime.now()
        timestampStr = dateTimeObj.strftime("%d-%b-%Y (%H:%M:%S.%f)")

        js_requestParamsSummary = request_params
        js_requestParamsSummary['ReportGeneratedDateTime'] = timestampStr

        # # drawing problems #Jan 24 2021 release
        # drawingWarnings = self.combinedObjects.get("DRAWING_ERRORS", "N/A")
        # if (drawingWarnings != "N/A"):
        #     js_requestParamsSummary["DrawingWarnings"] = drawingWarnings

        self.reportExtractor.append({"REQUEST_SUMMARY": js_requestParamsSummary})

    def get_project_details(self):

        plan_text_elementsDict = self.combinedObjects.get('PLAN_TEXT_ELEMENTS', 0)

        textElementsForJSON = dict()
        textElementsForJSON['Proposed_Use'] = plan_text_elementsDict.get('Proposed Use', ['N/A'])[0]
        textElementsForJSON['Proposed_Activity'] = plan_text_elementsDict.get('Proposed Activity', ['N/A'])[0]
        textElementsForJSON['Near_Religious_Structure'] = plan_text_elementsDict.get('Religious Structure', ['N/A'])[0]
        textElementsForJSON['Application_Type'] = plan_text_elementsDict.get('Application Type', ['N/A'])[0]
        textElementsForJSON['Project_Type'] = plan_text_elementsDict.get('Project Type', ['N/A'])[0]
        textElementsForJSON['Land_Use'] = plan_text_elementsDict.get('Land Use', ['N/A'])[0]
        textElementsForJSON['Land_SubUse_Zone'] = plan_text_elementsDict.get('Land Sub Use Zone', ['N/A'])[0]
        textElementsForJSON['Nature_of_Development'] = plan_text_elementsDict.get('Nature of Development', ['N/A'])[0]

        self.reportExtractor.append({"Project_Summary": dict(sorted(textElementsForJSON.items()))})

    def get_gatedcommunity_setbacks(self):

        if (self.gatedCommunityFlag == 'True' or self.gatedCommunityFlag == True):

            gatedCommunityResponse = executeDrawingActions(self.request_params, self.dxf_dir, self.filename)

            gatedCommunityResponseListDirect = gatedCommunityResponse.get('results', [])

            self.reportExtractor.append({"GATED_COMMUNITY_SETBACKS": gatedCommunityResponseListDirect})

    def get_deviation_details(self):

        deviationsInDrawingResponseDict = dict()
        if self.runOnlyCombinedUtil == "True":
            get_current_logger().info(f'Bypassed Due to runOnlyCombinedUtil In Drawing {self.runOnlyCombinedUtil}')
        else:
            deviationsInDrawingResponseDict = checkDeviationsInDrawing(self.modelspace_dwg)

        self.reportExtractor.append({"DRAWING_DEVIATIONS": deviationsInDrawingResponseDict})

    def get_combine_utils_details(self):

        combinedBuildingUtilityResult = dict()

        if self.runOnlyCombinedUtil == "True":

            combinedBuildingUtilityResponse = runCombinedBuildingUtility(self.modelspace_dwg, self.gatedCommunityFlag)

            combinedBuildingReturnCode = combinedBuildingUtilityResponse.get('CODE', 100)


            if (combinedBuildingReturnCode == 0):
                combinedBuildingUtilityResult = combinedBuildingUtilityResponse.get(
                    'COMBINED_BUILDING_UTIL_RESULTS', {})

            else:
                combinedBuildingUtilErrors = combinedBuildingUtilityResponse.get('ERROR', [])

                combinedBuildingUtilityResult = {"COMBINED_BUILDING_UTIL_RESULTS", str(combinedBuildingUtilErrors)}

            get_current_logger().info('Completed  RunOnlyCombinedBuildingUtils  ')
        else:
            get_current_logger().info('Not Calling RunOnlyCombinedBuildingUtils ')
            get_current_logger().info('Completed  RunOnlyCombinedBuildingUtils ')

        dictObjectList = ['BALCONY_LENGTH_WIDTH', "STAIR_CASE_DETAILS", 'STAIRCASE_DATA',
                          # 'BLDG_FLOORWISE_ACC_VOID_AREA_BY_BUA_TYPE',
                          # 'CELLAR_PLINTH_FOR_SETBACKS',
                          'COMMONFLOOR_SETBACKS_FOR_PLOT', 'PLOT_LINE_ENTRANCE_GATE_RESULT',
                          'WINDOW_IN_ROOM_CHECKS_RESULT', 'RAMPLENGTH_BUILDINGHEIGHT',
                          'ACCESSORY_USE_AREA_IN_PARKING',
                          'MORTGAGE_FLOOR_SUMMARY_NEW', 'SEPTIC_TANK_DIST',
                          'PODIUM_REGULAR_SETBACKS', 'PODIUM_ARC_RADIUS', 'CELLAR_SETBACKS_FOR_BUILDING',
                          'VENTILATION_WIDTH_AREA',
                          'TRANSFER_OF_SETBACKS', 'PODIUM_SETBACKS', 'SEGMENT_WISE_FLOOR_SETBACKS_RESULT',
                          'GATED_COMMUNITY_DEDUCTIONS', 'MULTIPLE_OCCUPANCY_BUA',
                          'BUILDING_FLOOR_TOTAL_HEIGHT_SUMMARY', 'PARKING_SLOT_DETAILS', 'PLOT_DETAILS',
                          'ARCH_PROJECTION_DATA']

        stringObjectList = ['DRAWING_COMMONLAYER_VALIDATIONS', 'DRAWING_DEVIATIONS']


        for commonKeyName, commonKeyValue in combinedBuildingUtilityResult.items():

            if commonKeyName in dictObjectList:

                self.reportExtractor.append({"COMBINED_BUILDING_UTILITY_RESULT_" + commonKeyName: commonKeyValue})

            elif commonKeyName in stringObjectList:

                self.reportExtractor.append({"COMBINED_BUILDING_UTILITY_RESULT_" + commonKeyName: commonKeyValue})

            else:
                get_current_logger().warning(f'Found unknown Key  {commonKeyName}')

    def get_cellarsetbackAndPlinth_details(self):
        cellarSetbacksAndPlinthResponse = dict()

        if self.runOnlyCombinedUtil == "True":
            get_current_logger().info(f'Bypassed Due to runOnlyCombinedUtil In Drawing {self.runOnlyCombinedUtil}')
        else:
            cellarSetbacksAndPlinthResponse = get_cellar_setbacks_plinth(self.modelspace_dwg)


        cellarSetbacksDictDirect = cellarSetbacksAndPlinthResponse.get('CELLAR_SETBACKS_RESPONSE', {})

        cellarPlinthListDirect = cellarSetbacksAndPlinthResponse.get('CELLAR_PLINTH_RESPONSE', {})

        self.reportExtractor.append(
            {"CELLAR_PLINTH_FOR_SETBACKS": [dict(sorted(dct.items())) for dct in cellarPlinthListDirect]})

        js_cellarSetbacksList = []

        for cellarId, cellarObj in cellarSetbacksDictDirect.items():
            js_cellar_setBacksPlot = dict()
            bldg_name = removeSpecialChars(cellarObj.get('BLDG_NAME', 'N/A'))
            cellarfloor_name = removeSpecialChars(cellarObj.get('NAME', 'N/A'))
            cellar_Id = removeSpecialChars(cellarId)
            js_cellar_setBacksPlot['BUILDING_NAME'] = bldg_name
            js_cellar_setBacksPlot['NAME'] = cellarfloor_name
            js_cellar_setBacksPlot['REFERENCE_ID'] = cellar_Id
            js_cellar_setBacksPlot['PROPOSED_FRONT_SETBACK'] = cellarObj.get('FRONT', 'N/A')
            js_cellar_setBacksPlot['REQUIRED_FRONT_SETBACK'] = '-'
            js_cellar_setBacksPlot['PROPOSED_REAR_SETBACK'] = cellarObj.get('REAR', 'N/A')
            js_cellar_setBacksPlot['REQUIRED_REAR_SETBACK'] = '-'
            js_cellar_setBacksPlot['PROPOSED_SIDE1_SETBACK'] = cellarObj.get('SIDE1', 'N/A')
            js_cellar_setBacksPlot['REQUIRED_SIDE1_SETBACK'] = '-'
            js_cellar_setBacksPlot['PROPOSED_SIDE2_SETBACK'] = cellarObj.get('SIDE2', 'N/A')
            js_cellar_setBacksPlot['REQUIRED_SIDE2_SETBACK'] = '-'
            js_cellar_setBacksPlot['STATUS'] = 'OK'
            # js_cellar_setBacksPlot['APPLICABLE_RULE']=''

            js_cellarSetbacksList.append(js_cellar_setBacksPlot)

        self.reportExtractor.append(
            {"CELLAR_SETBACKS_FOR_BUILDING": [dict(sorted(dct.items())) for dct in js_cellarSetbacksList]})

    def get_podium_setbacks_details(self):

        if self.runOnlyCombinedUtil == "True":
            get_current_logger().info(f'Bypassed Due to runOnlyCombinedUtil In Drawing {self.runOnlyCombinedUtil}')
        else:
            podium_setbacks_results = get_podium_setbacks(self.modelspace_dwg)

            podium_setbacks_results.get('REGULAR_SETBACK_RESPONSE', {})

            podium_setbacks_results.get('PODIUM_SETBACKS_RESPONSE', {})

    def get_ghmc_setbacks_details(self):

        if self.runOnlyCombinedUtil == "True":
            get_current_logger().info(f'Bypassed Due to runOnlyCombinedUtil In Drawing {self.runOnlyCombinedUtil}')
        else:
            setBacksDictConsolidated = get_ghmc_setbacks(self.modelspace_dwg)

    def get_regular_setbacks_details(self):

        if self.runOnlyCombinedUtil == "True":
            get_current_logger().info(f'Bypassed Due to runOnlyCombinedUtil In Drawing {self.runOnlyCombinedUtil}')
        else:
            setBacksDictConsolidated = getSetBacksByMidPointsMarginLineNew(self.modelspace_dwg)

    def get_transferofsetbacks_details(self):
        transferOfSetbacksResponse = dict()

        if self.runOnlyCombinedUtil == "True":
            get_current_logger().info(f'Bypassed Due to runOnlyCombinedUtil In Drawing {self.runOnlyCombinedUtil}')
        else:
            transferOfSetbacksResponse = get_transfer_of_setbacks(self.modelspace_dwg)


        if (transferOfSetbacksResponse is not None):
            transferOfSetbacksListDirect = transferOfSetbacksResponse.get('TRANSFER_OF_SETBACKS_RESPONSE', {})
        else:
            transferOfSetbacksListDirect = dict()

        js_transferOfSetbacksPlotList = []

        for transferSbObj in transferOfSetbacksListDirect:

            for bldgName, sbList in transferSbObj.items():
                # each transfer details
                for sbObject in sbList:
                    js_transferOfSetbacks = dict()
                    js_transferOfSetbacks['BLDG_NAME'] = "\"" + str(bldgName) + "\""
                    js_transferOfSetbacks['POSITION'] = str(sbObject.get('POSITION', '-'))
                    js_transferOfSetbacks['TRANSFER_SETBACK_TYPE'] = str(sbObject.get('TRANSFER_SETBACK_TYPE', '-'))
                    js_transferOfSetbacks['TRANSFER_AREA'] = str(sbObject.get('AREA', '-'))
                    js_transferOfSetbacks['MIN_WIDTH'] = str(sbObject.get('MIN_WIDTH', '-'))
                    js_transferOfSetbacks['MAX_WIDTH'] = str(sbObject.get('MAX_WIDTH', '-'))
                    js_transferOfSetbacksPlotList.append(js_transferOfSetbacks)

        self.reportExtractor.append({"TRANSFER_OF_SETBACKS": js_transferOfSetbacksPlotList})

    def get_bua_area_details(self):

        accessoryAreaByBUAResponse = get_area_by_bua_type_voids_accessory(self.modelspace_dwg)

        if (accessoryAreaByBUAResponse is not None):
            accessoryAreaByBUAListDirect = accessoryAreaByBUAResponse.get('AREA_VOID_ACCESS_BYBUA_RESPONSE', [])
        else:
            accessoryAreaByBUAListDirect = []

        for areabyBuaTypeObj in accessoryAreaByBUAListDirect:
            consolidatedBuaAreaTmp = dict()
            consolidatedBuaAreaTmp['BLDG_REFID'] = areabyBuaTypeObj.get("BLDG_REFID", "N/A")
            consolidatedBuaAreaTmp['BLDG_NAME'] = areabyBuaTypeObj.get("BLDG_NAME", "N/A")
            consolidatedBuaAreaTmp['FLOOR_REFID'] = areabyBuaTypeObj.get("FLOOR_REFID", "N/A")
            consolidatedBuaAreaTmp['FLOOR'] = str(areabyBuaTypeObj.get("FLOOR", "N/A")).replace(",", "-")
            consolidatedBuaAreaTmp['RESIBUA_ACCESSORY'] = areabyBuaTypeObj.get("RESIBUA_ACCESSORY", "N/A")
            consolidatedBuaAreaTmp['RESIBUA_BALCONY'] = areabyBuaTypeObj.get("RESIBUA_BALCONY", "N/A")
            consolidatedBuaAreaTmp['RESIBUA_VENTILATION_SHAFT'] = areabyBuaTypeObj.get("RESIBUA_VENTILATION_SHAFT",
                                                                                       "N/A")
            consolidatedBuaAreaTmp['RESIBUA_SLAB_CUTOUT_VOID'] = areabyBuaTypeObj.get("RESIBUA_SLAB_CUTOUT_VOID",
                                                                                      "N/A")
            consolidatedBuaAreaTmp['RESIBUA_REFUSE_AREA'] = areabyBuaTypeObj.get("RESIBUA_REFUSE_AREA", "N/A")

            consolidatedBuaAreaTmp['RESIBUA_LIFT_AREA'] = areabyBuaTypeObj.get("RESIBUA_LIFT_AREA", "N/A")
            consolidatedBuaAreaTmp['RESIBUA_STAIRCASE_AREA'] = areabyBuaTypeObj.get("RESIBUA_STAIRCASE_AREA", "N/A")

            consolidatedBuaAreaTmp['RESIBUA_OCCUPANCY_TYPE'] = areabyBuaTypeObj.get("RESIBUA_OCCUPANCY_TYPE", "N/A")

            consolidatedBuaAreaTmp['COMMBUA_ACCESSORY'] = areabyBuaTypeObj.get("COMMBUA_ACCESSORY", "N/A")
            consolidatedBuaAreaTmp['COMMBUA_BALCONY'] = areabyBuaTypeObj.get("COMMBUA_BALCONY", "N/A")
            consolidatedBuaAreaTmp['COMMBUA_VENTILATION_SHAFT'] = areabyBuaTypeObj.get("COMMBUA_VENTILATION_SHAFT",
                                                                                       "N/A")
            consolidatedBuaAreaTmp['COMMBUA_SLAB_CUTOUT_VOID'] = areabyBuaTypeObj.get("COMMBUA_SLAB_CUTOUT_VOID",
                                                                                      "N/A")
            consolidatedBuaAreaTmp['COMMBUA_REFUSE_AREA'] = areabyBuaTypeObj.get("COMMBUA_REFUSE_AREA", "N/A")

            consolidatedBuaAreaTmp['COMMBUA_OCCUPANCY_TYPE'] = areabyBuaTypeObj.get("COMMBUA_OCCUPANCY_TYPE", "N/A")

            consolidatedBuaAreaTmp['INDBUA_ACCESSORY'] = areabyBuaTypeObj.get("INDBUA_ACCESSORY", "N/A")
            consolidatedBuaAreaTmp['INDBUA_BALCONY'] = areabyBuaTypeObj.get("INDBUA_BALCONY", "N/A")
            consolidatedBuaAreaTmp['INDBUA_VENTILATION_SHAFT'] = areabyBuaTypeObj.get("INDBUA_VENTILATION_SHAFT",
                                                                                      "N/A")
            consolidatedBuaAreaTmp['INDBUA_SLAB_CUTOUT_VOID'] = areabyBuaTypeObj.get("INDBUA_SLAB_CUTOUT_VOID",
                                                                                     "N/A")
            consolidatedBuaAreaTmp['INDBUA_REFUSE_AREA'] = areabyBuaTypeObj.get("INDBUA_REFUSE_AREA", "N/A")

            consolidatedBuaAreaTmp['INDBUA_OCCUPANCY_TYPE'] = areabyBuaTypeObj.get("INDBUA_OCCUPANCY_TYPE", "N/A")

            consolidatedBuaAreaTmp['SPECIAL_USEBUA_ACCESSORY'] = areabyBuaTypeObj.get("SPECIAL_USEBUA_ACCESSORY",
                                                                                      "N/A")
            consolidatedBuaAreaTmp['SPECIAL_USEBUA_BALCONY'] = areabyBuaTypeObj.get("SPECIAL_USEBUA_BALCONY", "N/A")
            consolidatedBuaAreaTmp['SPECIAL_USEBUA_VENTILATION_SHAFT'] = areabyBuaTypeObj.get(
                "SPECIAL_USEBUA_VENTILATION_SHAFT", "N/A")
            consolidatedBuaAreaTmp['SPECIAL_USEBUA_SLAB_CUTOUT_VOID'] = areabyBuaTypeObj.get(
                "SPECIAL_USEBUA_SLAB_CUTOUT_VOID", "N/A")
            consolidatedBuaAreaTmp['SPECIAL_USEBUA_REFUSE_AREA'] = areabyBuaTypeObj.get(
                "SPECIAL_USEBUA_REFUSE_AREA",
                "N/A")

            consolidatedBuaAreaTmp['SPECIAL_USEBUA_OCCUPANCY_TYPE'] = areabyBuaTypeObj.get(
                "SPECIAL_USEBUA_OCCUPANCY_TYPE", "N/A")

            self.jsAccessAreaBuaTypeInfo.append(consolidatedBuaAreaTmp)

        self.reportExtractor.append({"BLDG_FLOORWISE_ACC_VOID_AREA_BY_BUA_TYPE": [dict(sorted(dct.items())) for dct in
                                                                             self.jsAccessAreaBuaTypeInfo]})

    def get_netbuiltup_area_new(self):

        flNamesDictNew = dict()
        removeList = []
        floorNameMapping = dict()

        for floorFinal, flObj in self.masterFloorDict.items():

            if (flObj.subtype == LayerMaster.TYPICAL_FLOOR.value):
                get_current_logger().debug('Typical floor - to be split ' + floorFinal)
                flNamesTmp = splitTypicalFloors(flObj)

                for floorName in flNamesTmp:

                    floorNameMapping[floorName.replace(' ', '')] = flObj.fname.replace(' ', '')

                if (flNamesTmp is not None or len(flNamesTmp) > 0):

                    get_current_logger().debug('Pop from master  ' + str(floorFinal))
                    removeList.append(floorFinal)
                    get_current_logger().debug('Typical floor - After pop count  ' + str(len(self.masterFloorDict)))

                flNamesDictNew.update(flNamesTmp)
            else:

                floorNameMapping[flObj.fname.replace(' ', '')] = flObj.fname.replace(' ', '')

        for itemToDel in removeList:
            self.masterFloorDict.pop(itemToDel)
        # update the expanded floors for typical
        self.masterFloorDict.update(flNamesDictNew)

        total_bua_building_list = []
        for masterFlrItem, floorObj in self.masterFloorDict.items():

            tmpFloorDict = floorObj.get_dict()

            tmpFloorRec = dict()
            justBuilding = masterFlrItem
            if ("|" in justBuilding):
                startIdx = justBuilding.find('|')
                justBuilding = justBuilding[:startIdx]

            tmpFloorRec['Building'] = justBuilding
            tmpFloorRec['BUAArea'] = round(float(tmpFloorDict.get('BuiltUpArea', 0)), 2)
            tmpFloorRec['AccessoryUseArea'] = round(float(tmpFloorDict.get('AccessoryUseArea', 0)), 2)
            tmpFloorRec['RampArea'] = round(float(tmpFloorDict.get('RampArea', 0)), 2)
            tmpFloorRec['StairArea'] = round(float(tmpFloorDict.get('StairArea', 0)), 2)
            tmpFloorRec['LiftArea'] = round(float(tmpFloorDict.get('LiftArea', 0)), 2)
            tmpFloorRec['ProposedBUAArea'] = round(float(tmpFloorDict.get('ProposedNetBUA', 0)), 2)
            tmpFloorRec['NetBUAArea'] = float(tmpFloorDict.get('TotalNetBUA', 0))
            tmpFloorRec['DwellUnitNo'] = float(tmpFloorDict.get('DwellUnits', 0))
            tmpFloorRec['ParkingArea'] = float(tmpFloorDict.get('ParkingFloorArea', 0))
            tmpFloorRec['TotalStackParkingArea'] = float(tmpFloorDict.get('TotalStackParkingArea', 0))
            tmpFloorRec['ResidentialArea'] = float(tmpFloorDict.get('ResidentialArea', 0))
            tmpFloorRec['CommercialArea'] = float(tmpFloorDict.get('CommercialArea', 0))
            tmpFloorRec['IndustrialArea'] = float(tmpFloorDict.get('IndustrialArea', 0))
            tmpFloorRec['SpecialArea'] = float(tmpFloorDict.get('SpecialArea', 0))
            tmpFloorRec['VentiShaftArea'] = float(tmpFloorDict.get('VentiShaftArea', 0))
            tmpFloorRec['SlabCutoutArea'] = float(tmpFloorDict.get('SlabCutoutArea', 0))
            tmpFloorRec['BalconyArea'] = float(tmpFloorDict.get('BalconyArea', 0))

            tmpFloorRec['ExcludedAccessoryArea'] = float(tmpFloorDict.get('ExcludedAccessoryArea', 0))

            get_current_logger().debug(f"floor_rec:{tmpFloorRec}")
            total_bua_building_list.append(tmpFloorRec)

        # BUA BY BUILDING

        pd.set_option("display.max_rows", None, "display.max_columns", None)
        buaTypeColumns = ['Building', 'ResidentialArea', 'CommercialArea', 'IndustrialArea', 'SpecialArea' \
            , 'BUAArea', 'AccessoryUseArea', 'VentiShaftArea', 'SlabCutoutArea', 'RampArea', 'BalconyArea', 'StairArea',
                          'LiftArea', 'ProposedBUAArea', 'NetBUAArea', 'DwellUnitNo', 'ParkingArea',
                          'TotalStackParkingArea', 'ExcludedAccessoryArea']
        buaByType_df = pd.DataFrame.from_records(total_bua_building_list, columns=buaTypeColumns)
        tmpBua = buaByType_df.groupby('Building').sum()

        tmpBua = tmpBua.round(2)
        tmp_dict = tmpBua.to_dict(orient='index')

        json_tmpBuaByBuilding = {
            building: dict(sorted(values.items()))
            for building, values in sorted(tmp_dict.items())
        }

        self.reportExtractor.append({"NET_BUILT_UP_AREA_SUMMARY_NEW": [dict(sorted(json_tmpBuaByBuilding.items()))]})

    def get_nala_area_details(self):
        nalaRoadList = self.combinedObjects.get(
            LayerMaster.NALAROAD.value).getBaseUnitFinalList() if self.combinedObjects.get(LayerMaster.NALAROAD.value,
                                                                                      0) != 0 else []
        for nalaObj in nalaRoadList:
            self.totalNalaArea += float(nalaObj.area)

    def get_mortgagecarpetarea_details(self):

        mortgagedCarpetAreaUnitsListDirect=[]
        if self.runOnlyCombinedUtil == "True":
            get_current_logger().info(f'Bypassed Due to runOnlyCombinedUtil In Drawing {self.runOnlyCombinedUtil}')
        else:
            mortgagedCarpetAreaUnitsResponse = get_Mortgaged_CarpetArea4Buildings(self.modelspace_dwg)
            mcauCode = mortgagedCarpetAreaUnitsResponse.get('CODE', -1)

            if (mcauCode == 0):
                mortgagedCarpetAreaUnitsListDirect = mortgagedCarpetAreaUnitsResponse.get(
                    'MORTGAGED_CARPETAREA_LIST', [])
            else:
                error = mortgagedCarpetAreaUnitsResponse.get('ERROR', 'N/A')

        # detail rec
        jsxMtgFloorInfo = []

        for mtgFloorObj in mortgagedCarpetAreaUnitsListDirect:
            jsxMtgFloorInfo.append(mtgFloorObj)

        self.reportExtractor.append(
            {"MORTGAGE_FLOOR_SUMMARY_NEW": [dict(sorted(dct.items())) for dct in jsxMtgFloorInfo]})

    def get_floorwisesetabcks_details(self):

        floorSetbacksListDirect=dict()
        if self.runOnlyCombinedUtil == "True":
            get_current_logger().info(f'Bypassed Due to runOnlyCombinedUtil In Drawing {self.runOnlyCombinedUtil}')
        else:

            floorSetbacksResponse = get_floor_wise_setbacks(self.modelspace_dwg)

            if (floorSetbacksResponse is not None):
                floorSetbacksListDirect = floorSetbacksResponse.get('FLOORWISE_SETBACKS_RESPONSE', {})
            else:
                floorSetbacksListDirect = dict()

        self.reportExtractor.append({"FLOORWISE_SETBACKS": [dict(sorted(dct.items())) for dct in floorSetbacksListDirect]})

    def get_septictank_details(self):

        accessory_use_dist_reponse = get_accessory_septic_sewage_transformer_distances(self.modelspace_dwg)

        if (accessory_use_dist_reponse is not None):
            access_distances_DictDirect = accessory_use_dist_reponse.get('ACCESSORYUSE_DISTANCE_FROM_PLOT_RESPONSE', {})
        else:
            access_distances_DictDirect = dict()

        js_accessoryUseSpecificList = []

        for accUseKey, accUseResponse in access_distances_DictDirect.items():
            accTempDict = dict()
            statusValue_accessory = 'OK'
            get_current_logger().debug(f' response -  {accUseResponse}')
            direction, distanceFromPlot = accUseResponse
            accTempDict['ACCESSORY_NAME'] = accUseKey
            accTempDict['ACCESSORY_LOCATION'] = direction
            accTempDict['DISTANCE_FROM_PLOT'] = str(distanceFromPlot)
            accTempDict['STATUS'] = statusValue_accessory

            js_accessoryUseSpecificList.append(accTempDict)

        self.reportExtractor.append(
            {"ACCESSORY_USE_SPECIFIC_CHECKS": [dict(sorted(dct.items())) for dct in js_accessoryUseSpecificList]})

    def get_accessoryParking_details(self):

        accessoryUseAreaInParkingListDirect=[]

        self.reportExtractor.append({"ACCESSORY_USE_AREA_IN_PARKING": accessoryUseAreaInParkingListDirect})

    def get_plinthArea_details(self):

        existingPlinthAreaList = self.combinedObjects.get(
            LayerMaster.EXISTING_PLINTH_AREA.value).getBaseUnitFinalList() if self.combinedObjects.get(
            LayerMaster.EXISTING_PLINTH_AREA.value, 0) != 0 else []

        proposedPlinthAreaList = self.combinedObjects.get(
            LayerMaster.PROPOSED_PLINTH_AREA.value).getBaseUnitFinalList() if self.combinedObjects.get(
            LayerMaster.PROPOSED_PLINTH_AREA.value, 0) != 0 else []

        if (existingPlinthAreaList is not None and len(existingPlinthAreaList) > 0):
            existingPlinthAreaTotal = round(
                sum(float(existingPlinthObj.area) for existingPlinthObj in existingPlinthAreaList), 2)
        else:
            existingPlinthAreaTotal = 0.0

        if (proposedPlinthAreaList is not None and len(proposedPlinthAreaList) > 0):
            proposedPlinthAreaTotal = round(
                sum(float(propsedPlinthObj.area) for propsedPlinthObj in proposedPlinthAreaList), 2)
        else:
            proposedPlinthAreaTotal = 0.0

        plinthAreaDict = dict()
        plinthAreaDict['EXISTING_PLINTH_AREA'] = str(existingPlinthAreaTotal)
        plinthAreaDict['PROPOSED_PLINTH_AREA'] = str(proposedPlinthAreaTotal)

        self.reportExtractor.append({"PLINTH_SUMMARY": dict(sorted(plinthAreaDict.items()))})

    def get_area_summary_details(self):

        calculatedObjectsDict = dict()

        totalLeftoverOwnersLandArea = 0.0

        plotUnitDict = self.combinedObjects.get(LayerMaster.PLOT.value).getBaseUnitDict() if self.combinedObjects.get(
            LayerMaster.PLOT.value, 0) != 0 else {}
        splayPlotList = self.combinedObjects.get(LayerMaster.SPLAY.value).getBaseUnitFinalList() if self.combinedObjects.get(
            LayerMaster.SPLAY.value, 0) != 0 else []

        roadWideningDict = self.combinedObjects.get(LayerMaster.ROADWIDENING.value).getBaseUnitDict() if self.combinedObjects.get(
            LayerMaster.ROADWIDENING.value, 0) != 0 else {}
        netPlotDict = self.combinedObjects.get(LayerMaster.NETPLOT.value).getBaseUnitDict() if self.combinedObjects.get(
            LayerMaster.NETPLOT.value, 0) != 0 else {}
        proposedWorkDict = self.combinedObjects.get(LayerMaster.PROPOSEDWORK.value).getBaseUnitDict() if self.combinedObjects.get(
            LayerMaster.PROPOSEDWORK.value, 0) != 0 else {}

        existingStructDict = self.combinedObjects.get(
            LayerMaster.EXISTINGSTRUCTURE.value).getBaseUnitDict() if self.combinedObjects.get(
            LayerMaster.EXISTINGSTRUCTURE.value, 0) != 0 else {}

        leftoverOwnersLandList = self.combinedObjects.get(
            LayerMaster.LEFTOVEROWNERSLAND.value).getBaseUnitFinalList() if self.combinedObjects.get(
            LayerMaster.LEFTOVEROWNERSLAND.value, 0) != 0 else []

        grossPlotArea = sum(float(mnPlot.area) for mnPlot in plotUnitDict.values())

        totalSplayArea = round(sum(float(splayObj.area) for splayObj in splayPlotList), 2)

        totalRoadwideningArea = sum(float(rwPlot.area) for rwPlot in roadWideningDict.values())

        self.totalNetplotArea = round(sum(float(netPlot.area) for netPlot in netPlotDict.values()), 2)

        # FIX: Feb 27 to exclude splay from GHMC and DTCP Layouts
        if (totalSplayArea > 0 and self.authority in ['GHMC', 'DTCP']):
            self.totalNetplotArea = self.totalNetplotArea - totalSplayArea

        if (self.totalNalaArea > 0):

            self.totalNetplotArea = round((self.totalNetplotArea - self.totalNalaArea), 2)

        calculatedObjectsDict["GROSS_PLOT_AREA"] = str(grossPlotArea)
        calculatedObjectsDict["NALA_AREA"] = str(self.totalNalaArea)
        calculatedObjectsDict["SPLAY_AREA"] = str(totalSplayArea)
        calculatedObjectsDict["TOTAL_ROAD_WIDENING_AREA"] = str(round(totalRoadwideningArea, 2))
        calculatedObjectsDict["TOTAL_NETPLOT_AREA"] = str(round(self.totalNetplotArea, 2))

        # AREA TABLE CHECKS
        if (self.coverageAreaPercent == 0.0):

            tempProposedArea = 0.0
            for propworkObj in proposedWorkDict.values():
                tempProposedArea += propworkObj.area
            if (tempProposedArea > 0.0):
                coverageAreaValue = tempProposedArea
                self.coverageAreaPercent = round((float(coverageAreaValue) / float(self.totalNetplotArea)) * 100, 2)
            else:
                coverageAreaValue = 0.0

        else:

            coverageAreaValue = round((float(self.coverageAreaPercent) * float(self.totalNetplotArea)) / 100, 2)

        #
        demolishArea = 0.0
        if (existingStructDict.values() is not None and coverageAreaValue > 0):
            self.existingCoverageArea = sum(exPlot.area for exPlot in existingStructDict.values())

            demolishArea = sum(v.area for k, v in existingStructDict.items() if "demolish" in k.lower())

            existingCoveragePercent = round((float(self.existingCoverageArea) / float(self.totalNetplotArea) * 100), 2)
        else:
            self.existingCoverageArea = 0.0
            existingCoveragePercent = 0.0

        for leftoverOwnerLandObj in leftoverOwnersLandList:
            totalLeftoverOwnersLandArea += float(leftoverOwnerLandObj.area)

        calculatedObjectsDict["EXISTING_COVERAGE_AREA"] = str(self.existingCoverageArea)
        calculatedObjectsDict["EXISTING_COVERAGE_AREA_PERCENTAGE"] = str(existingCoveragePercent)
        calculatedObjectsDict["PROPOSED_COVERAGE_AREA"] = str(coverageAreaValue)
        calculatedObjectsDict["PROPOSED_COVERAGE_AREA_PERCENTAGE"] = str(self.coverageAreaPercent)

        calculatedObjectsDict['LEFTOVEROWNERSLAND_AREA'] = str(round(totalLeftoverOwnersLandArea, 2))

        vacantplotArea = float(self.totalNetplotArea) + float(demolishArea) - (
                float(coverageAreaValue) + float(self.existingCoverageArea))

        calculatedObjectsDict["VACANT_PLOT_AREA"] = str(round(vacantplotArea, 2))

        flNamesDictNew = dict()
        removeList = []
        floorNameMapping = dict()

        for floorFinal, flObj in self.masterFloorDict.items():

            if (flObj.subtype == LayerMaster.TYPICAL_FLOOR.value):

                flNamesTmp = splitTypicalFloors(flObj)

                for floorName in flNamesTmp:

                    floorNameMapping[floorName.replace(' ', '')] = flObj.fname.replace(' ', '')

                if (flNamesTmp is not None or len(flNamesTmp) > 0):

                    removeList.append(floorFinal)

                flNamesDictNew.update(flNamesTmp)
            else:

                floorNameMapping[flObj.fname.replace(' ', '')] = flObj.fname.replace(' ', '')

        # delete from master list for typical
        for itemToDel in removeList:
            self.masterFloorDict.pop(itemToDel)
        # update the expanded floors for typical
        self.masterFloorDict.update(flNamesDictNew)

        totalBUAArea = 0.0
        totalAccessoryUseArea = 0.0
        totalRampArea = 0.0
        totalStairArea = 0.0
        totalLiftArea = 0.0
        totalNetBUAArea = 0.0
        totalDwellUnitNo = 0.0
        totalResidentialArea = 0.0
        totalCommercialArea = 0.0
        totalIndustrialArea = 0.0
        totalSpecialArea = 0.0
        totalVentilationArea = 0.0
        totalSlabCutoutArea = 0.0
        totalBalconyArea = 0.0
        totalExcludedArea = 0.0

        total_bua_building_list = []
        for masterFlrItem, floorObj in self.masterFloorDict.items():
            # get the dict object
            tmpFloorDict = floorObj.get_dict()

            totalBUAArea += float(tmpFloorDict.get('BuiltUpArea', 0))

            totalAccessoryUseArea += float(tmpFloorDict.get('AccessoryUseArea', 0))
            totalRampArea += float(tmpFloorDict.get('RampArea', 0))

            totalStairArea += float(tmpFloorDict.get('StairArea', 0))
            totalLiftArea += float(tmpFloorDict.get('LiftArea', 0))
            self.totalProposedBUAArea += float(tmpFloorDict.get('ProposedNetBUA', 0))
            totalNetBUAArea += float(tmpFloorDict.get('TotalNetBUA', 0))
            totalDwellUnitNo += float(tmpFloorDict.get('DwellUnits', 0))
            self.totalParkingArea += float(tmpFloorDict.get('ParkingFloorArea', 0))
            self.totalStackParkingArea += float(tmpFloorDict.get('TotalStackParkingArea', 0))

            totalResidentialArea += float(tmpFloorDict.get('ResidentialArea', 0))
            totalCommercialArea += float(tmpFloorDict.get('CommercialArea', 0))
            totalIndustrialArea += float(tmpFloorDict.get('IndustrialArea', 0))
            totalSpecialArea += float(tmpFloorDict.get('SpecialArea', 0))
            totalVentilationArea += float(tmpFloorDict.get('VentiShaftArea', 0))
            totalSlabCutoutArea += float(tmpFloorDict.get('SlabCutoutArea', 0))
            totalBalconyArea += float(tmpFloorDict.get('BalconyArea', 0))
            totalExcludedArea += float(tmpFloorDict.get('ExcludedAccessoryArea', 0))

            tmpFloorRec = dict()
            justBuilding = masterFlrItem
            if ("|" in justBuilding):
                startIdx = justBuilding.find('|')
                justBuilding = justBuilding[:startIdx]

            tmpFloorRec['Building'] = justBuilding
            tmpFloorRec['BUAArea'] = round(float(tmpFloorDict.get('BuiltUpArea', 0)), 2)
            tmpFloorRec['AccessoryUseArea'] = round(float(tmpFloorDict.get('AccessoryUseArea', 0)), 2)
            tmpFloorRec['RampArea'] = round(float(tmpFloorDict.get('RampArea', 0)), 2)
            tmpFloorRec['StairArea'] = round(float(tmpFloorDict.get('StairArea', 0)), 2)
            tmpFloorRec['LiftArea'] = round(float(tmpFloorDict.get('LiftArea', 0)), 2)
            tmpFloorRec['ProposedBUAArea'] = round(float(tmpFloorDict.get('ProposedNetBUA', 0)), 2)
            tmpFloorRec['NetBUAArea'] = float(tmpFloorDict.get('TotalNetBUA', 0))
            tmpFloorRec['DwellUnitNo'] = float(tmpFloorDict.get('DwellUnits', 0))
            tmpFloorRec['ParkingArea'] = float(tmpFloorDict.get('ParkingFloorArea', 0))
            tmpFloorRec['TotalStackParkingArea'] = float(tmpFloorDict.get('TotalStackParkingArea', 0))
            tmpFloorRec['ResidentialArea'] = float(tmpFloorDict.get('ResidentialArea', 0))
            tmpFloorRec['CommercialArea'] = float(tmpFloorDict.get('CommercialArea', 0))
            tmpFloorRec['IndustrialArea'] = float(tmpFloorDict.get('IndustrialArea', 0))
            tmpFloorRec['SpecialArea'] = float(tmpFloorDict.get('SpecialArea', 0))
            tmpFloorRec['VentiShaftArea'] = float(tmpFloorDict.get('VentiShaftArea', 0))
            tmpFloorRec['SlabCutoutArea'] = float(tmpFloorDict.get('SlabCutoutArea', 0))
            tmpFloorRec['BalconyArea'] = float(tmpFloorDict.get('BalconyArea', 0))

            tmpFloorRec['ExcludedAccessoryArea'] = float(tmpFloorDict.get('ExcludedAccessoryArea', 0))

            get_current_logger().debug(f"floor_rec:{tmpFloorRec}")
            total_bua_building_list.append(tmpFloorRec)
        totalFloorsArea = (float(totalBUAArea) - float(self.totalParkingArea))

        calculatedObjectsDict["TOTAL_PROPOSED_BUA_WITHOUT_PARKING"] = str(round(totalFloorsArea, 2))
        calculatedObjectsDict["TOTAL_PROPOSED_BUA_WITH_PARKING"] = str(round(totalBUAArea, 2))

        self.reportExtractor.append({"AreaSummary": dict(sorted(calculatedObjectsDict.items()))})

    def get_propwork_dim_details(self):

        proposedWorkDict = self.combinedObjects.get(
            LayerMaster.PROPOSEDWORK.value).getBaseUnitDict() if self.combinedObjects.get(
            LayerMaster.PROPOSEDWORK.value, 0) != 0 else {}

        for bldobj in proposedWorkDict.values():

            self.reportExtractor.append({"ProposedWorkDimensions": dict(sorted(bldobj.to_dict().items()))})

    def get_netplot_dim_details(self):

        netPlotDict = self.combinedObjects.get(LayerMaster.NETPLOT.value).getBaseUnitDict() if self.combinedObjects.get(
            LayerMaster.NETPLOT.value, 0) != 0 else {}

        for npobj in netPlotDict.values():
            self.reportExtractor.append({"NetPlotDimensions": dict(sorted(npobj.to_dict().items()))})

    def get_existingsturcture_details(self):

        existingStructDict = self.combinedObjects.get(
            LayerMaster.EXISTINGSTRUCTURE.value).getBaseUnitDict() if self.combinedObjects.get(
            LayerMaster.EXISTINGSTRUCTURE.value, 0) != 0 else {}

        js_existingStruct = dict()

        if (self.existingCoverageArea > 0):

            idx = 1
            for exiKey, exiObj in existingStructDict.items():
                js_existingStruct[str(idx) + "-" + exiObj.name] = str(exiObj.area)
                idx += 1

            self.reportExtractor.append({"EXISTING_STRUCTURE": js_existingStruct})

    def get_tot_summary_details(self):

        totUnitsDict = self.combinedObjects.get(LayerMaster.ORGOPENSPACE.value).getBaseUnitDict() if self.combinedObjects.get(
            LayerMaster.ORGOPENSPACE.value, 0) != 0 else {}

        orgOpenspaceDict = dict()
        orgOpenspaceDict['subtype'] = self.subtype
        orgOpenspaceDict['proposed_site_area'] = round(self.totalNetplotArea, 2)
        orgOpenspaceDict['proposed_tot_factor'] = 9
        orgOpenspaceDict['proposed_tot_width'] = 2
        orgOpenspaceDict['proposed_tot_area'] = 15
        orgOpenspaceDict['proposed_greenstrip_width'] = 0

        orgOpenspaceRuleResult = callrule('ts-org-openspace', orgOpenspaceDict)

        get_current_logger().debug("orgOpenspaceDict response " + str(orgOpenspaceRuleResult))
        orgOpenspaceResult = orgOpenspaceRuleResult["result"]
        get_current_logger().debug(" orgOpenspaceDict rule result " + str(orgOpenspaceResult))

        TOT_MIN_PERCENT = orgOpenspaceResult.get('required_tot_factor', 10)

        orgOpenspace_rule = orgOpenspaceResult.get('zrule', 'N/A')

        TOT_MIN_TOTAL_REQUIRED_AREA = round((float(TOT_MIN_PERCENT) * float(self.totalNetplotArea)) / 100, 2)

        # iterate the list
        for totItem, totObj in totUnitsDict.items():

            if ("TOT" in totItem.upper() or 'LINE BUFFER' in totItem.upper() or 'HIGH-TENSION' in totItem.upper()):
                self.totalTotArea += totObj.area

        if self.totalTotArea >= TOT_MIN_TOTAL_REQUIRED_AREA:
            statusValue = "OK"
        else:
            statusValue = "NOT OK"

        js_totSummary = dict()
        js_totSummary['ORG_OPEN_SPACE_MIN_TOTAL_REQUIRED_AREA'] = str(TOT_MIN_TOTAL_REQUIRED_AREA)
        js_totSummary['ORG_OPEN_SPACE_PROPOSED_AREA'] = str(self.totalTotArea)
        js_totSummary['STATUS'] = statusValue
        js_totSummary['APPLICABLE_RULE'] = orgOpenspace_rule
        self.reportExtractor.append({"TOT_SUMMARY": dict(sorted(js_totSummary.items()))})

    def get_tot_details(self):

        orgOpenspaceDict = dict()
        orgOpenspaceDict['subtype'] = self.subtype
        orgOpenspaceDict['proposed_site_area'] = round(self.totalNetplotArea, 2)
        orgOpenspaceDict['proposed_tot_factor'] = 9
        orgOpenspaceDict['proposed_tot_width'] = 2
        orgOpenspaceDict['proposed_tot_area'] = 15
        orgOpenspaceDict['proposed_greenstrip_width'] = 0

        orgOpenspaceRuleResult = callrule('ts-org-openspace', orgOpenspaceDict)
        orgOpenspaceResult = orgOpenspaceRuleResult["result"]

        TOTPLOT_MIN_REQUIRED_WIDTH = orgOpenspaceResult.get('required_tot_width', 3)
        TOTPLOT_MIN_REQUIRED_AREA = orgOpenspaceResult.get('required_tot_area', 15)
        GREEN_STRIP_MIN_REQUIRED_WIDTH = orgOpenspaceResult.get('required_greenstrip_width', 1)
        GREEN_STRIP_MIN_REQUIRED_AREA = 0.0

        totUnitsDict = self.combinedObjects.get(
            LayerMaster.ORGOPENSPACE.value).getBaseUnitDict() if self.combinedObjects.get(
            LayerMaster.ORGOPENSPACE.value, 0) != 0 else {}

        green_tot_widthDirectDict=Green_strip_width(self.modelspace_dwg)

        js_totList = []

        # detail
        for totItem, totObj in totUnitsDict.items():
            isHeightTensionBuffer = False
            if ('LINE BUFFER' in totItem.upper() or 'HIGH-TENSION' in totItem.upper()):
                isHeightTensionBuffer = True

            js_totDetail = dict()
            js_totDetail['HANDLE'] = str(totObj.handle)

            tmpTotTxt = str(green_tot_widthDirectDict.get(totObj.handle, ''))

            # Fix accessory width 5/8/2022 viswa method - default
            if (tmpTotTxt is not None and len(tmpTotTxt) > 0):
                nametmp, widthtmp = tmpTotTxt.split(',')

                if ("green" in totObj.name.lower()):  # nametmp.lower()):
                    js_totDetail['TYPE'] = 'GREEN STRIP'
                    min_width_to_check = GREEN_STRIP_MIN_REQUIRED_WIDTH
                    min_area_to_check = GREEN_STRIP_MIN_REQUIRED_AREA

                    width = float(widthtmp)

                else:
                    js_totDetail['TYPE'] = 'TOT'
                    if (isHeightTensionBuffer):
                        min_width_to_check = 0
                    else:
                        min_width_to_check = TOTPLOT_MIN_REQUIRED_WIDTH
                    min_area_to_check = TOTPLOT_MIN_REQUIRED_AREA
                    width = float(widthtmp)

                    if (float(widthtmp) < min_width_to_check and float(widthtmp) < float(totObj.width)):
                        # swap using totOjb.width
                        width = float(totObj.width)

                if (totObj.area >= min_area_to_check and width >= min_width_to_check):
                    statusValue = "OK"

                else:
                    statusValue = "Not OK"
            else:  # existing in case we dont get results
                get_current_logger().debug('ORGANIZED OPEN SPACE didnt get results from  green_tot_widthDirectDict ')

                if ("green" in totItem.lower()):
                    js_totDetail['TYPE'] = 'GREEN STRIP'
                    min_width_to_check = GREEN_STRIP_MIN_REQUIRED_WIDTH
                    min_area_to_check = GREEN_STRIP_MIN_REQUIRED_AREA

                    width = round(getMinWidthIrregularObjects(totObj.polygon), 1)

                else:
                    js_totDetail['TYPE'] = 'TOT'
                    if (isHeightTensionBuffer):
                        min_width_to_check = 0
                    else:
                        min_width_to_check = TOTPLOT_MIN_REQUIRED_WIDTH

                    min_area_to_check = TOTPLOT_MIN_REQUIRED_AREA
                    width = totObj.width

                if (totObj.area >= min_area_to_check and width >= min_width_to_check):
                    statusValue = "OK"

                else:
                    statusValue = "Not OK"

            js_totDetail['NAME'] = totObj.name.replace("\\", "")
            js_totDetail['TOTPLOT_MIN_REQUIRED_AREA'] = str(min_area_to_check)
            js_totDetail['AREA'] = str(totObj.area)
            js_totDetail['TOTPLOT_MIN_REQUIRED_WIDTH'] = str(min_width_to_check)
            js_totDetail['WIDTH'] = str(width)
            js_totDetail['STATUS'] = statusValue
            js_totList.append(js_totDetail)

        self.reportExtractor.append({"TOT_DETAILS": [dict(sorted(dct.items())) for dct in js_totList]})

    def get_greenstripCwall_details(self):

        orgOpenspaceDict = dict()
        orgOpenspaceDict['subtype'] = self.subtype
        orgOpenspaceDict['proposed_site_area'] = round(self.totalNetplotArea, 2)
        orgOpenspaceDict['proposed_tot_factor'] = 9
        orgOpenspaceDict['proposed_tot_width'] = 2
        orgOpenspaceDict['proposed_tot_area'] = 15
        orgOpenspaceDict['proposed_greenstrip_width'] = 0

        orgOpenspaceRuleResult = callrule('ts-org-openspace', orgOpenspaceDict)

        orgOpenspaceResult = orgOpenspaceRuleResult["result"]

        GREEN_STRIP_MIN_REQUIRED_WIDTH = orgOpenspaceResult.get('required_greenstrip_width', 1)


        compoundWallDict = self.combinedObjects.get(LayerMaster.COMPOUNDWALL.value).getBaseUnitDict() if self.combinedObjects.get(
            LayerMaster.COMPOUNDWALL.value, 0) != 0 else {}

        totUnitsDict = self.combinedObjects.get(LayerMaster.ORGOPENSPACE.value).getBaseUnitDict() if self.combinedObjects.get(
            LayerMaster.ORGOPENSPACE.value, 0) != 0 else {}

        green_tot_widthDirectDict = Green_strip_width(self.modelspace_dwg)

        js_gsList = []
        default_CWAllName = ""
        for totItem, totObj in totUnitsDict.items():
            if ("green" in totItem.lower()):
                js_gsDetail = dict()
                js_gsDetail['HANDLE'] = str(totObj.handle)
                abuttingGs = checkGreenStripAroundCWall(totObj, compoundWallDict.values())

                tmpTotTxt = green_tot_widthDirectDict.get(totObj.handle, None)
                if (tmpTotTxt is not None and len(tmpTotTxt) > 0):
                    nametmp, widthtmp = tmpTotTxt.split(',')
                    width = float(widthtmp)

                else:
                    width = round(getMinWidthIrregularObjects(totObj.polygon), 1)

                abutting = ""
                for gsObj in abuttingGs:
                    abutting = str(gsObj.get('cwall_name', 'N/A'))
                    if (len(default_CWAllName) > 0):
                        gsname = str(gsObj.get('gs_name', 'N/A'))
                        get_current_logger().debug("GS :" + gsname + " abutting cwall : " + abutting)
                        break  # just need first record

                min_width_to_check = GREEN_STRIP_MIN_REQUIRED_WIDTH
                if (width >= min_width_to_check or len(abuttingGs) > 0):
                    statusValue = "OK"

                else:
                    statusValue = "Not OK"

                # write to json
                js_gsDetail['NAME'] = str(totObj.name.replace("\\", ""))
                js_gsDetail['GREENSTRIP_MIN_REQUIRED_WIDTH'] = str(GREEN_STRIP_MIN_REQUIRED_WIDTH)
                js_gsDetail['PROPOSED_WIDTH'] = str(width)
                js_gsDetail['CWALL_DESC'] = abutting
                js_gsDetail['STATUS'] = statusValue

                js_gsList.append(js_gsDetail)
        self.reportExtractor.append({"GREEN_STRIP_CWALL_DETAILS": [dict(sorted(dct.items())) for dct in js_gsList]})

    def get_building_summary_dertals(self):

        floorInSectionDict = self.combinedObjects.get(
            LayerMaster.FLOORINSECTION.value).getBaseUnitDict() if self.combinedObjects.get(LayerMaster.FLOORINSECTION.value,
                                                                                       0) != 0 else {}

        plan_text_elementsDict=self.plan_text_elementsDict

        if (len(floorInSectionDict.values()) > 0):
            df = None
        else:
            df = pd.DataFrame.from_records([fs.get_dict() for fs in floorInSectionDict.values()])
        BLDG_NAMES = []
        if (df is not None and df.empty == False):

            bldg_infodf = getBuildingInfo(df)
            bldg_infodf.insert(1, 'Building Use', plan_text_elementsDict.get('Proposed Use', ['N/A'])[0])
            bldg_infodf.insert(2, 'Building SubUse', plan_text_elementsDict.get('Proposed Activity', ['N/A'])[0])
            bldg_infodf.insert(3, 'Building Type', plan_text_elementsDict.get('Project Type', ['N/A'])[0])

            json_bldg_infoStr = bldg_infodf.to_dict()

            self.reportExtractor.append({"BUILDING_SUMMARY": [json_bldg_infoStr.items()]})
        else:

            json_bldg_infoStr = {}

            self.reportExtractor.append({"BUILDING_SUMMARY": [json_bldg_infoStr]})

    def get_floorinsection_details(self):

        parkingUnitsDict = self.combinedObjects.get(LayerMaster.PARKING.value).getBaseUnitDict() if self.combinedObjects.get(
            LayerMaster.PARKING.value, 0) != 0 else {}


        parking_category = getCategoryForParking(self.request_params)

        parkingChecksDict = dict()
        parkingChecksDict['subtype'] = self.subtype
        parkingChecksDict['proposed_site_area'] = round(self.totalNetplotArea, 2)
        parkingChecksDict['proposed_parking_factor'] = 1
        parkingChecksDict['proposed_visitor_parking_factor'] = 0
        parkingChecksDict['location'] = self.location
        parkingChecksDict['subuse'] = self.subuse
        parkingChecksDict['parking_category'] = parking_category
        parkingChecksDict['request_params'] = self.combinedObjects.get(LayerMaster.REQUEST_PARAMS.value)

        parkingChecksRuleResult = callrule('ts-parking', parkingChecksDict)

        parkingChecksResult = parkingChecksRuleResult["result"]

        PARKING_MIN_REQUIRED_AREA_PERCENT = parkingChecksResult.get('required_parking_factor', 30)
        PARKING_VISITORS_PERCENT = parkingChecksResult.get('required_visitor_parking_factor', 10)

        totalCustomerParkingArea = 0.0
        customerParkCount = 0
        totalVisitorParkingArea = 0.0
        visitorParkCount = 0
        totalOutsideParkingArea = 0.0
        outsideParkCount = 0
        outsideParkingList = []
        stackParkingArea = 0.0

        for parkingObjItem, parkingObj in parkingUnitsDict.items():
            pkName = parkingObj.name.upper()
            pkArea = parkingObj.area

            parkingFloorObj = self.masterFloorDict.get(parkingObj.parent, 0)
            if (parkingFloorObj != 0):

                if (pkArea == parkingFloorObj.maxParkingarea):
                    get_current_logger().error(f"Parking areas matches with floor bua area .. "
                                        f"(skipping parkArea , floorParkingArea) {(pkArea, parkingFloorObj.maxParkingarea)}")
                    continue  # skip
                else:

                    # check if parking is stack then add
                    if ("-1,2(MECH.)" in pkName.upper() or "STACK" in pkName.upper()):
                        self.stackParkingArea += pkArea  # add only the delta

                    if ("VISITOR" in pkName):

                        totalVisitorParkingArea = totalVisitorParkingArea + pkArea
                        visitorParkCount = visitorParkCount + 1
                    else:

                        totalCustomerParkingArea = totalCustomerParkingArea + pkArea
                        customerParkCount = customerParkCount + 1

            else:

                get_current_logger().debug("outside of floor area adding " + pkName + " = " + str(pkArea))
                outsideParkingList.append(parkingObj)

        # check outside parking
        for outrParking in outsideParkingList:
            outrPoly = shapely.wkt.loads(str(outrParking.polygon))
            for innerParking in outsideParkingList:
                innerPoly = shapely.wkt.loads(str(innerParking.polygon))
                if (outrParking.handle != innerParking.handle):  # outrParking.area >= innerParking.area ):

                    # check if innerParking is within the outrParking
                    if (innerPoly.within(outrPoly) and "VISITOR" in innerParking.name.upper()):

                        totalVisitorParkingArea = totalVisitorParkingArea + float(innerParking.area)
                        visitorParkCount = visitorParkCount + 1
                    else:

                        totalOutsideParkingArea = totalOutsideParkingArea + float(innerParking.area)
                        outsideParkCount = outsideParkCount + 1

        totalParkingAreaSection = totalOutsideParkingArea + self.totalParkingArea + stackParkingArea

        TOTAL_PARKING_AREA_REQUIRED = round((PARKING_MIN_REQUIRED_AREA_PERCENT * self.totalProposedBUAArea / 100), 2)

        BLDG_NAMES=[]

        if (totalParkingAreaSection >= TOTAL_PARKING_AREA_REQUIRED and \
                totalVisitorParkingArea >= round((PARKING_VISITORS_PERCENT * (TOTAL_PARKING_AREA_REQUIRED) / 100), 2)):
            statusValue = "OK"
        else:
            statusValue = "NOT OK"


        # @TODO default to first building - need to add if u have more than 1 bldg
        # Building Name is used in other parts of reports
        if (len(BLDG_NAMES) > 0):
            BLDG_NAME = BLDG_NAMES[0]
        else:
            BLDG_NAME = 'N/A'

        plinthHeight = 0.0
        floorHeight = 0.0
        stiltHeight = 0.0
        liftHeight = 0.0
        cellarHeight = 0.0
        terraceHeight = 0.0

        isStilt = False
        isTerrace = False
        isFloor = False
        isCellar = False
        isPlinth = False
        js_flrInSecDetailList = []
        bldg_heights_dict = dict()
        jsBuildingFloorDict = dict()
        flrInSectHeightDict = dict()

        floorInSectionDict = self.combinedObjects.get(
            LayerMaster.FLOORINSECTION.value).getBaseUnitDict() if self.combinedObjects.get(LayerMaster.FLOORINSECTION.value,
                                                                                       0) != 0 else {}

        for flrSecItem, flrSecObj in floorInSectionDict.items():
            js_flrInSecDetail = dict()
            # print("FLR SEC ITEM ", flrSecItem)
            if ("TERRACE" in flrSecItem):
                isTerrace = True  # continue
                continue
            # check floor type

            if ("STILT" in flrSecItem):
                if (stackParkingArea > 0):
                    requiredHeight = 4.5
                else:
                    requiredHeight = 2.50
                isStilt = True
            elif ("CELLAR" in flrSecItem or "BASEMENT" in flrSecItem):
                requiredHeight = 2.40
                isCellar = True
            elif ("PLINTH" in flrSecItem):
                requiredHeight = 0.45
                isPlinth = True
            else:
                requiredHeight = 2.75
                isFloor = True

            if (flrSecObj.height >= requiredHeight):
                statusValue = "OK"
            else:
                statusValue = "Not OK"
#
            tmpDxfPoly = flrSecObj.get_DXFPoly()
            isTDR = "-"
            if (tmpDxfPoly != None):
                colorTmp = tmpDxfPoly.getColor()
                if (int(colorTmp) == 240):
                    isTDR = "Yes"
                    get_current_logger().debug(f"isTDR True - as DXF Poly is color is: {colorTmp}")

            if (isFloor):
                floorHeight += flrSecObj.height
                liftHeight += flrSecObj.height

                bldg_heights_dict[flrSecObj.parent + '|FLOOR'] = floorHeight
                bldg_heights_dict[flrSecObj.parent + '|LIFT'] = liftHeight
            elif (isStilt):
                stiltHeight += flrSecObj.height

                bldg_heights_dict[flrSecObj.parent + '|STILT'] = stiltHeight
            elif (isCellar):
                cellarHeight += flrSecObj.height

                bldg_heights_dict[flrSecObj.parent + '|CELLAR'] = cellarHeight
            elif (isTerrace):
                terraceHeight += flrSecObj.height
                bldg_heights_dict[flrSecObj.parent + '|TERRACE'] = terraceHeight
            elif (isPlinth):
                plinthHeight += flrSecObj.height
                bldg_heights_dict[flrSecObj.parent + '|PLINTH'] = plinthHeight

            if (jsBuildingFloorDict.get(flrSecObj.parent, 0) == 0):
                if (isFloor or isStilt or isCellar or isTerrace):
                    jsBuildingFloorDict[flrSecObj.parent] = 1
            else:
                if (isFloor or isStilt or isCellar or isTerrace):
                    no_of_floors = jsBuildingFloorDict.get(flrSecObj.parent)
                    no_of_floors += 1
                    jsBuildingFloorDict[flrSecObj.parent] = no_of_floors

            flrInSectHeightDict[flrSecObj.parent.strip() + "-" + flrSecObj.name.strip()] = flrSecObj.height

            js_flrInSecDetail['BLDG_NAME'] = flrSecObj.parent
            js_flrInSecDetail['FLOOR_NAME'] = flrSecObj.name
            js_flrInSecDetail['BLDG_FLOOR_KEY'] = flrSecObj.parent.strip() + "-" + flrSecObj.name.strip()
            js_flrInSecDetail['REQUIRED_FLOOR_HEIGHT'] = str(requiredHeight)
            js_flrInSecDetail['PERMSSIBLE_FLOOR_HEIGHT'] = ''
            js_flrInSecDetail['PROPOSED_FLOOR_HEIGHT'] = str(flrSecObj.height)
            js_flrInSecDetail['TDR_FLOOR'] = isTDR
            js_flrInSecDetail['STATUS'] = statusValue
            js_flrInSecDetailList.append(js_flrInSecDetail)

        self.reportExtractor.append({"FLOORINSECTION_DETAIL": [dict(sorted(dct.items())) for dct in js_flrInSecDetailList]})

    def get_buildingheight_details(self):
        plinthHeight = 0.0
        floorHeight = 0.0
        stiltHeight = 0.0
        liftHeight = 0.0
        cellarHeight = 0.0
        terraceHeight = 0.0

        isStilt = False
        isTerrace = False
        isFloor = False
        isCellar = False
        isPlinth = False

        bldg_heights_dict = dict()
        NO_OF_FLOORS = 0
        jsBuildingFloorDict = dict()

        get_current_logger().info("NO_OF_FLOORS  \n " + str(NO_OF_FLOORS))

        flrInSectHeightDict = dict()

        floorInSectionDict = self.combinedObjects.get(
            LayerMaster.FLOORINSECTION.value).getBaseUnitDict() if self.combinedObjects.get(
            LayerMaster.FLOORINSECTION.value,
            0) != 0 else {}

        for flrSecItem, flrSecObj in floorInSectionDict.items():

            # print("FLR SEC ITEM ", flrSecItem)
            if ("TERRACE" in flrSecItem):
                isTerrace = True  # continue
                continue

            if ("STILT" in flrSecItem):
                if (self.stackParkingArea > 0):
                    requiredHeight = 4.5
                else:
                    requiredHeight = 2.50
                isStilt = True
            elif ("CELLAR" in flrSecItem or "BASEMENT" in flrSecItem):
                requiredHeight = 2.40
                isCellar = True
            elif ("PLINTH" in flrSecItem):
                requiredHeight = 0.45
                isPlinth = True
            else:
                requiredHeight = 2.75
                isFloor = True

            if (flrSecObj.height >= requiredHeight):
                statusValue = "OK"
            else:
                statusValue = "Not OK"

            tmpDxfPoly = flrSecObj.get_DXFPoly()
            isTDR = "-"
            if (tmpDxfPoly != None):
                colorTmp = tmpDxfPoly.getColor()
                if (int(colorTmp) == 240):
                    isTDR = "Yes"
                    get_current_logger().debug(f"isTDR True - as DXF Poly is color is: {colorTmp}")

            if (isFloor):
                floorHeight += flrSecObj.height
                liftHeight += flrSecObj.height

                bldg_heights_dict[flrSecObj.parent + '|FLOOR'] = floorHeight
                bldg_heights_dict[flrSecObj.parent + '|LIFT'] = liftHeight
            elif (isStilt):
                stiltHeight += flrSecObj.height

                bldg_heights_dict[flrSecObj.parent + '|STILT'] = stiltHeight
            elif (isCellar):
                cellarHeight += flrSecObj.height

                bldg_heights_dict[flrSecObj.parent + '|CELLAR'] = cellarHeight
            elif (isTerrace):
                terraceHeight += flrSecObj.height
                bldg_heights_dict[flrSecObj.parent + '|TERRACE'] = terraceHeight
            elif (isPlinth):
                plinthHeight += flrSecObj.height
                bldg_heights_dict[flrSecObj.parent + '|PLINTH'] = plinthHeight

            if (jsBuildingFloorDict.get(flrSecObj.parent, 0) == 0):
                if (isFloor or isStilt or isCellar or isTerrace):
                    jsBuildingFloorDict[flrSecObj.parent] = 1
            else:
                if (isFloor or isStilt or isCellar or isTerrace):
                    no_of_floors = jsBuildingFloorDict.get(flrSecObj.parent)
                    no_of_floors += 1
                    jsBuildingFloorDict[flrSecObj.parent] = no_of_floors

            flrInSectHeightDict[flrSecObj.parent.strip() + "-" + flrSecObj.name.strip()] = flrSecObj.height


        bldg_heights_calc = dict()
        for bldg_key, bldg_value in bldg_heights_dict.items():
            bldg_name_idx = bldg_key.find('|')
            bldg_name = bldg_key[0:bldg_name_idx]
            valueToadd = 0.0

            if ("|FLOOR" in bldg_key):
                valueToadd = bldg_heights_dict[flrSecObj.parent + '|FLOOR']

            elif ("|PLINTH" in bldg_key and flrSecObj.parent + '|PLINTH' in bldg_heights_dict):
                valueToadd = bldg_heights_dict[flrSecObj.parent + '|PLINTH']

            elif ("|STILT" in bldg_key and flrSecObj.parent + '|STILT' in bldg_heights_dict):
                valueToadd = bldg_heights_dict[flrSecObj.parent + '|STILT']

            else:
                continue

            if (valueToadd > 0):
                if (bldg_heights_calc.get(bldg_name, 0) == 0):
                    # create
                    bldg_heights_calc[bldg_name] = valueToadd
                else:
                    # add up to height
                    bldg_heights_calc[bldg_name] = float(bldg_heights_calc[bldg_name]) + float(valueToadd)

        pd.set_option("display.max_rows", None, "display.max_columns", None)
        floorInSection_df = pd.DataFrame.from_records([fs.get_dict() for fs in floorInSectionDict.values()])

        bldg_floor_resultdf = getBuilding_Floor_Heights(floorInSection_df, self.subtype)
        bldg_floor_resultdf.insert(0, 'Height_Mt._Permissible', '-')

        get_current_logger().debug(bldg_floor_resultdf)
        floor_height_col = bldg_floor_resultdf['Floor_Height']
        max_building_height = round(floor_height_col.max(), 2)
        get_current_logger().debug(f"MAX BUILDING HEIGHT :{max_building_height}")
        json_bldg_floor_result = bldg_floor_resultdf.to_dict()

        self.reportExtractor.append({"BUILDING_FLOOR_TOTAL_HEIGHT_SUMMARY": dict(sorted(json_bldg_floor_result.items()))})

    def get_groundleve_details(self):

        buildingGroundLevelDict = groundlevel_check_latest(self.modelspace_dwg)
        buildingGroundLevelByNameDict = dict()
        js_buildingGLList = []
        js_duplicateGLList = []

        for building_ReferenceId, values in buildingGroundLevelDict.items():
            if ('duplicateList' in building_ReferenceId):
                js_duplicateGLList.append(values)

            else:

                buildingName, sectionReference, gl_height = values.split('|')

                glDict = dict()
                glDict['BUILDING_NAME'] = buildingName
                glDict['BUILDING_REFERENCE_ID'] = building_ReferenceId
                glDict['SECTION_REFERENCE_ID'] = sectionReference
                glDict['GROUNDLEVEL_HEIGHT'] = str(gl_height)
                js_buildingGLList.append(glDict)

                buildingGroundLevelByNameDict[buildingName] = str(gl_height)

        self.reportExtractor.append({"BUILDING_GROUND_LEVEL_NEW": [dict(sorted(dct.items())) for dct in js_buildingGLList]})

    def get_mortgagearea_summary_details(self):

        floorInSectionDict = self.combinedObjects.get(
            LayerMaster.FLOORINSECTION.value).getBaseUnitDict() if self.combinedObjects.get(LayerMaster.FLOORINSECTION.value,
                                                                                       0) != 0 else {}

        pd.set_option("display.max_rows", None, "display.max_columns", None)
        floorInSection_df = pd.DataFrame.from_records([fs.get_dict() for fs in floorInSectionDict.values()])

        bldg_floor_resultdf = getBuilding_Floor_Heights(floorInSection_df, self.subtype)
        bldg_floor_resultdf.insert(0, 'Height_Mt._Permissible', '-')

        bldg_floor_resultdf = getBuilding_Floor_Heights(floorInSection_df, self.subtype)
        bldg_floor_resultdf.insert(0, 'Height_Mt._Permissible', '-')

        get_current_logger().debug(bldg_floor_resultdf)
        floor_height_col = bldg_floor_resultdf['Floor_Height']
        max_building_height = round(floor_height_col.max(), 2)
        get_current_logger().debug(f"MAX BUILDING HEIGHT :{max_building_height}")

        # Mortage
        MIN_MORTAGE_PERCENT_REQUIRED = 10.0

        if (self.totalProposedBUAArea > 0):
            proposed_mortageFactor = round(self.totalMortgageArea / self.totalProposedBUAArea * 100, 2)
        else:
            proposed_mortageFactor = 0.0

        mtgruleResult = callrule('ts-mortgage',
                                 {'plan_type': 'Building_Layout', 'plot_area': round(self.totalNetplotArea, 2),
                                  'building_height': round(max_building_height, 1),
                                  'proposed_mortgage_factor': proposed_mortageFactor})

        mortgageResult = mtgruleResult["result"]

        required_mortageFactor = mortgageResult.get('required_mortgage_factor',
                                                    MIN_MORTAGE_PERCENT_REQUIRED)
        mortage_status = mortgageResult.get('status', 'NOT OK')
        mortgageRule = mortgageResult.get('zrule', 'N/A')

        REQUIRED_MORTAGE_AREA = round(required_mortageFactor * self.totalProposedBUAArea / 100, 2)

        js_mtgSummary = dict()
        js_mtgSummary['MIN_MORTAGE_PERCENT_REQUIRED'] = str(required_mortageFactor)
        js_mtgSummary['REQUIRED_MORTAGE_AREA'] = str(REQUIRED_MORTAGE_AREA)
        js_mtgSummary['PROPOSED_MORTAGE_AREA'] = str(round(self.totalMortgageArea, 2))
        js_mtgSummary['STATUS'] = mortage_status
        js_mtgSummary['APPLICABLE_RULE'] = mortgageRule  # #escape with double quotes for json

        self.reportExtractor.append({"MORTGAGE_SUMMARY": dict(sorted(js_mtgSummary.items()))})

    def get_mortgagefloor_summary_details(self):

        mortgagedUnitsDict = self.combinedObjects.get(
            LayerMaster.MORTGAGEAREA.value).getBaseUnitDict() if self.combinedObjects.get(LayerMaster.MORTGAGEAREA.value,
                                                                                     0) != 0 else {}

        mortgageMultiplier = 1

        mortgagedFloorsText = []
        mtgIdx = 1
        for mtgItem, mtgObj in mortgagedUnitsDict.items():

            istypicalFloor = False
            if (LayerMaster.TYPICAL_FLOOR.value in mtgObj.parent):
                typFloorCnt = determineFloorNumbers(mtgObj.parent)
                istypicalFloor = True
                mortgageMultiplier = len(typFloorCnt)
                netmtgArea = mtgObj.area * mortgageMultiplier
            else:
                netmtgArea = mtgObj.area * mortgageMultiplier
            #

            mortageFloorAllowedStatus = "OK"

            mortgagedFloorsText.append(
                [mtgIdx, mtgObj.name + " " + mtgObj.parent.replace("|", " "), mortageFloorAllowedStatus])

            self.totalMortgageArea += netmtgArea

        jsMtgFloorInfo = []

        for mtgFloor in mortgagedFloorsText:
            tmpMtgObj = dict()
            tmpMtgObj['Sno'] = str(mtgFloor[0])
            tmpMtgObj['Floor_Name'] = mtgFloor[1]
            tmpMtgObj['Status'] = mtgFloor[2]
            jsMtgFloorInfo.append(tmpMtgObj)

        self.reportExtractor.append({"MORTGAGE_FLOOR_SUMMARY": [dict(sorted(dct.items())) for dct in jsMtgFloorInfo]})

    def get_netbuiltup_area_detail(self):

        js_netBUASummary = dict()

        js_netBUASummary['BLDG_NAME'] = ""
        js_netBUASummary['TOTAL_BUILT_UP_AREA'] = str(round(self.totalBUAArea, 2))
        js_netBUASummary['TOTAL_ACCESSORY_USE_AREA'] = str(round(self.totalAccessoryUseArea, 2))
        js_netBUASummary['TOTAL_VENTILATION_AREA'] = str(round(self.totalVentilationArea, 2))
        js_netBUASummary['TOTAL_SLABCUTOUT_AREA'] = str(round(self.totalSlabCutoutArea, 2))
        js_netBUASummary['TOTAL_BALCONY_AREA'] = str(round(self.totalBalconyArea, 2))
        js_netBUASummary['TOTAL_RAMP_AREA'] = str(self.totalRampArea)
        js_netBUASummary['TOTAL_STAIR_AREA'] = str(self.totalStairArea)
        js_netBUASummary['TOTAL_LIFT_AREA'] = str(round(self.totalLiftArea, 2))
        js_netBUASummary['TOTAL_PROPOSED_BUA'] = str(round(self.totalProposedBUAArea))
        js_netBUASummary['TOTAL_NET_BUA'] = str(round(self.totalNetBUAArea, 2))
        js_netBUASummary['DWELLING_UNIT_NOS'] = str(self.totalDwellUnitNo)
        js_netBUASummary['PARKING_FLOOR_AREA'] = str(round(self.totalParkingArea, 2))
        js_netBUASummary['STACK_PARKING_AREA'] = str(round(self.totalStackParkingArea, 2))

        DETAIL_LIFT_STAIRCASE_TEXT = ""

        js_netBUADetailList = []
        js_liftStairsList = []
        js_cellarDimensionList = []

        for masterFlrItem, floorObj in self.masterFloorDict.items():
            js_netBUADetail = dict()
            js_liftStairs = dict()
            # get the dict object
            tmpFloorDict = floorObj.get_dict()
            stripBuilding = masterFlrItem
            if ("|" in stripBuilding):
                startIdx = stripBuilding.find('|')
                stripBuilding = stripBuilding[startIdx + 1:]

            js_netBUADetail['BLDG_NAME'] = str(tmpFloorDict.get('Building', 0))
            js_netBUADetail['FLOOR_NAME'] = stripBuilding
            js_netBUADetail['RESIDENTIAL_BUA'] = str(tmpFloorDict.get('ResidentialArea', '-'))
            js_netBUADetail['COMMERCIAL_BUA'] = str(tmpFloorDict.get('CommercialArea', '-'))
            js_netBUADetail['INDUSTRIAL_BUA'] = str(tmpFloorDict.get('IndustrialArea', '-'))
            js_netBUADetail['SPECIAL_BUA'] = str(tmpFloorDict.get('SpecialArea', '-'))

            js_netBUADetail['TOTAL_BUILT_UP_AREA'] = str(round(tmpFloorDict.get('BuiltUpArea', 0), 2))
            js_netBUADetail['TOTAL_ACCESSORY_USE_AREA'] = str(round(tmpFloorDict.get('AccessoryUseArea', 0), 2))
            js_netBUADetail['TOTAL_VENTILATION_AREA'] = str(round(tmpFloorDict.get('VentiShaftArea', 0), 2))
            js_netBUADetail['TOTAL_SLABCUTOUT_AREA'] = str(round(tmpFloorDict.get('SlabCutoutArea', 0), 2))
            js_netBUADetail['TOTAL_RAMP_AREA'] = str(round(tmpFloorDict.get('RampArea', 0), 2))
            js_netBUADetail['TOTAL_STAIR_AREA'] = str(round(tmpFloorDict.get('StairArea', 0), 2))
            js_netBUADetail['TOTAL_BALCONY_AREA'] = tmpFloorDict.get('BalconyArea', 0)
            js_netBUADetail['TOTAL_LIFT_AREA'] = str(tmpFloorDict.get('LiftArea', 0))
            js_netBUADetail['TOTAL_PROPOSED_BUA'] = str(tmpFloorDict.get('ProposedNetBUA', 0))
            js_netBUADetail['TOTAL_NET_BUA'] = str(tmpFloorDict.get('TotalNetBUA', 0))
            js_netBUADetail['DWELLING_UNIT_NOS'] = tmpFloorDict.get('DwellUnits', 0)
            js_netBUADetail['PARKING_FLOOR_AREA'] = str(tmpFloorDict.get('ParkingFloorArea', 0))
            js_netBUADetail['NO_OF_STACK_PARKING'] = str(tmpFloorDict.get('NoOfStacks', 0))
            js_netBUADetail['STACK_PARKING_FACTOR'] = str(tmpFloorDict.get('StackFactor', 0))
            js_netBUADetail['TOTAL_STACK_PARKING_AREA'] = str(round(tmpFloorDict.get('TotalStackParkingArea', 0), 2))
            js_netBUADetail['EXCLUDED_ACCESSORY_AREA'] = tmpFloorDict.get('ExcludedAccessoryArea', 0)

            js_netBUADetailList.append(js_netBUADetail)

            DETAIL_LIFT_STAIRCASE_TEXT += str(tmpFloorDict.get('Building', 0)) + ',' + stripBuilding + ',' + str(
                tmpFloorDict.get('NoOfStairs', 0)) + ',' + str(tmpFloorDict.get('NoOfLifts', 0)) + "\n"

            js_liftStairs['BLDG_NAME'] = str(tmpFloorDict.get('Building', 0))
            js_liftStairs['FLOOR_NAME'] = stripBuilding
            js_liftStairs['FLOOR_TYPE'] = str(tmpFloorDict.get('Layer', '-'))
            js_liftStairs['NO_OF_STAIRS'] = str(tmpFloorDict.get('NoOfStairs', 0))
            js_liftStairs['NO_OF_LIFTS'] = str(tmpFloorDict.get('NoOfLifts', 0))
            js_liftStairs['FLOOR_AREA'] = str(round(tmpFloorDict.get('BuiltUpArea', 0), 2))

            js_liftStairsList.append(js_liftStairs)

            # add cellar dimensions
            if stripBuilding is not None and LayerMaster.CELLAR_FLOOR.value in stripBuilding.upper():
                cellarDimensionDict = floorObj.get_dimensions()
                cellarDimensionDict['Building_FName'] = masterFlrItem
                js_cellarDimensionList.append(cellarDimensionDict)

        # NETBUARULE
        js_BUARulesList = []

        netBUARuleDict = dict()
        netBUARuleDict['BUA_CALCULATIONS'] = '1. BUA= Sum of xxxBUAOutline (_ResiBUAOutline) + Balcony Area  ' + \
                                             ' 2. In Cellar Add Watchman and Toilet accessory use. Watchman upto 25 sq.mt. can be added ' + \
                                             '3. No Other Accessory use space added in CELLAR OR ANY FLOOR ' + \
                                             '4. STAIRS AND LIFT Area added to NET BUA for CELLAR. Other Floors not added. '

        js_BUARulesList.append(netBUARuleDict)

        mergedPD = None
        json_netbuadetails = []

        try:

            mergedPD = merge_netbua(js_netBUADetailList, self.jsAccessAreaBuaTypeInfo)

            mergedPD = mergedPD.round(2)  # round first
            mergedPD = mergedPD.replace({np.nan: "N/A"})  # then replace

            json_netbuadetails = mergedPD.to_dict(orient="records")

        except:
            get_current_logger().warning('unable to merge the netbua ')
            pass

        self.reportExtractor.append(
            {"NET_BUILT_UP_AREA_DETAILS_NEW": [dict(sorted(dct.items())) for dct in json_netbuadetails]})

        # reportExtractor.append({"NET_BUILT_UP_AREA_DETAILS": [dict(sorted(dct.items())) for dct in js_netBUADetailList]})
        self.reportExtractor.append({"NET_BUILT_UP_AREA_DETAILS": []})

        self.reportExtractor.append({"NET_BUA_RULES_INFO": js_BUARulesList})

        self.reportExtractor.append({"LIFT_STAIRS_INFO": [dict(sorted(dct.items())) for dct in js_liftStairsList]})

    def get_cellar_dim_details(self):

        js_finalCellarDimensionList=[]
        js_cellarDimensionList=[]

        for masterFlrItem, floorObj in self.masterFloorDict.items():

            stripBuilding = masterFlrItem
            if ("|" in stripBuilding):
                startIdx = stripBuilding.find('|')
                stripBuilding = stripBuilding[startIdx + 1:]

            if stripBuilding is not None and LayerMaster.CELLAR_FLOOR.value in stripBuilding.upper():
                cellarDimensionDict = floorObj.get_dimensions()
                cellarDimensionDict['Building_FName'] = masterFlrItem
                js_cellarDimensionList.append(cellarDimensionDict)

        for cellarObj in js_cellarDimensionList:
            cellarTmpDict = dict()
            cellarTmpDict['Name'] = cellarObj.get('Name', 'NA')
            cellarTmpDict['Building'] = cellarObj.get('Building', 'NA')
            pkList = cellarObj.get('ParkingUnits', [])

            parkingUnitsDictTemp = dict()
            tmpIdx = 0

            try:

                for pkUnit in pkList:
                    parkingUnitsDictTemp[tmpIdx] = pkUnit.area
                    tmpIdx = tmpIdx + 1

                idx, max_value = max(parkingUnitsDictTemp.items(), key=lambda x: x[1])

                cellarTmpDict['Length'] = str(pkList[idx].length)
                cellarTmpDict['Width'] = str(pkList[idx].width)
                cellarTmpDict['Area'] = str(pkList[idx].area)

                get_current_logger().debug('Cellar PARKING FLOOR DIMENSION for ' + str(cellarTmpDict))

                js_finalCellarDimensionList.append(cellarTmpDict)
            except Exception:
                continue

        self.reportExtractor.append({"CellarDimensions": [dict(sorted(dct.items())) for dct in js_finalCellarDimensionList]})

    def get_lift_info_details(self):

        js_liftStairsList = []

        for masterFlrItem, floorObj in self.masterFloorDict.items():
            js_liftStairs = dict()
            tmpFloorDict = floorObj.get_dict()
            stripBuilding = masterFlrItem
            if ("|" in stripBuilding):
                startIdx = stripBuilding.find('|')
                stripBuilding = stripBuilding[startIdx + 1:]


            js_liftStairs['BLDG_NAME'] = str(tmpFloorDict.get('Building', 0))
            js_liftStairs['FLOOR_NAME'] = stripBuilding
            js_liftStairs['FLOOR_TYPE'] = str(tmpFloorDict.get('Layer', '-'))
            js_liftStairs['NO_OF_STAIRS'] = str(tmpFloorDict.get('NoOfStairs', 0))
            js_liftStairs['NO_OF_LIFTS'] = str(tmpFloorDict.get('NoOfLifts', 0))
            js_liftStairs['FLOOR_AREA'] = str(round(tmpFloorDict.get('BuiltUpArea', 0), 2))
            js_liftStairsList.append(js_liftStairs)

        buildingGroundLevelDict = groundlevel_check_latest(self.modelspace_dwg)
        buildingGroundLevelByNameDict = dict()
        js_buildingGLList = []
        js_duplicateGLList = []

        for building_ReferenceId, values in buildingGroundLevelDict.items():
            if ('duplicateList' in building_ReferenceId):
                js_duplicateGLList.append(values)

            else:

                get_current_logger().debug(f'values for Building {building_ReferenceId}, gl resp , {values}')
                buildingName, sectionReference, gl_height = values.split('|')

                glDict = dict()
                glDict['BUILDING_NAME'] = buildingName
                glDict['BUILDING_REFERENCE_ID'] = building_ReferenceId
                glDict['SECTION_REFERENCE_ID'] = sectionReference
                glDict['GROUNDLEVEL_HEIGHT'] = str(gl_height)
                js_buildingGLList.append(glDict)

                buildingGroundLevelByNameDict[buildingName] = str(gl_height)

        plinthHeight = 0.0
        floorHeight = 0.0
        stiltHeight = 0.0
        liftHeight = 0.0
        cellarHeight = 0.0
        terraceHeight = 0.0

        isStilt = False
        isTerrace = False
        isFloor = False
        isCellar = False
        isPlinth = False

        bldg_heights_dict = dict()
        NO_OF_FLOORS = 0
        jsBuildingFloorDict = dict()

        floorInSectionDict = self.combinedObjects.get(
            LayerMaster.FLOORINSECTION.value).getBaseUnitDict() if self.combinedObjects.get(
            LayerMaster.FLOORINSECTION.value,
            0) != 0 else {}

        for flrSecItem, flrSecObj in floorInSectionDict.items():

            # print("FLR SEC ITEM ", flrSecItem)
            if ("TERRACE" in flrSecItem):
                isTerrace = True  # continue
                continue
            # check floor type

            if ("STILT" in flrSecItem):
                if (self.stackParkingArea > 0):
                    requiredHeight = 4.5
                else:
                    requiredHeight = 2.50
                isStilt = True
            elif ("CELLAR" in flrSecItem or "BASEMENT" in flrSecItem):
                requiredHeight = 2.40
                isCellar = True
            elif ("PLINTH" in flrSecItem):
                requiredHeight = 0.45
                isPlinth = True
            else:
                requiredHeight = 2.75
                isFloor = True

            if (flrSecObj.height >= requiredHeight):
                statusValue = "OK"
            else:
                statusValue = "Not OK"

            tmpDxfPoly = flrSecObj.get_DXFPoly()
            isTDR = "-"
            if (tmpDxfPoly != None):
                colorTmp = tmpDxfPoly.getColor()
                if (int(colorTmp) == 240):
                    isTDR = "Yes"
                    get_current_logger().debug(f"isTDR True - as DXF Poly is color is: {colorTmp}")

            if (isFloor):
                floorHeight += flrSecObj.height
                liftHeight += flrSecObj.height

                bldg_heights_dict[flrSecObj.parent + '|FLOOR'] = floorHeight
                bldg_heights_dict[flrSecObj.parent + '|LIFT'] = liftHeight
            elif (isStilt):
                stiltHeight += flrSecObj.height

                bldg_heights_dict[flrSecObj.parent + '|STILT'] = stiltHeight
            elif (isCellar):
                cellarHeight += flrSecObj.height

                bldg_heights_dict[flrSecObj.parent + '|CELLAR'] = cellarHeight
            elif (isTerrace):
                terraceHeight += flrSecObj.height
                bldg_heights_dict[flrSecObj.parent + '|TERRACE'] = terraceHeight
            elif (isPlinth):
                plinthHeight += flrSecObj.height
                bldg_heights_dict[flrSecObj.parent + '|PLINTH'] = plinthHeight

            if (jsBuildingFloorDict.get(flrSecObj.parent, 0) == 0):
                if (isFloor or isStilt or isCellar or isTerrace):
                    jsBuildingFloorDict[flrSecObj.parent] = 1
            else:
                if (isFloor or isStilt or isCellar or isTerrace):
                    no_of_floors = jsBuildingFloorDict.get(flrSecObj.parent)
                    no_of_floors += 1
                    jsBuildingFloorDict[flrSecObj.parent] = no_of_floors

        js_liftHeightDict = dict()

        liftUnitsList = self.combinedObjects.get(LayerMaster.LIFT.value).getBaseList() if self.combinedObjects.get(
            LayerMaster.LIFT.value, 0) != 0 else []

        for flrSecItem, flrSecObj in floorInSectionDict.items():

            if ("TERRACE" in flrSecItem):
                liftHeight = checkLiftHeight(liftUnitsList, flrSecObj.getPolygonObj())

                get_current_logger().debug(f"LIFT in TERRACE ? ', {flrSecItem}, terrace height ,{flrSecObj.height}")

                get_current_logger().debug(f"Lift height " + str(liftHeight))

                if (liftHeight > 0):

                    valueToAdd = float(buildingGroundLevelByNameDict.get(flrSecObj.parent, 0.0))

                    updatedLiftHeight = round(liftHeight + flrSecObj.height + valueToAdd, 2)
                    get_current_logger().debug(f"Building : {flrSecObj.parent} Total Lift is :{updatedLiftHeight}"
                                        f" Sum of (terrace height , bldg gl height , lift headroom height) values:,{(flrSecObj.height, valueToAdd, liftHeight)}")

                else:
                    updatedLiftHeight = liftHeight

                js_liftHeightDict[flrSecObj.parent] = str(updatedLiftHeight)

                js_liftHeightDict["Remarks"] = "Sum of (Building GL height and up to top of lift headroom height) "

        self.reportExtractor.append({"LIFT_HEIGHT": dict(sorted(js_liftHeightDict.items()))})

        tmp_building_height_dict = dict()
        for bldObject in js_buildingGLList:

            bldTmpName = bldObject.get('BUILDING_NAME', 'NA')

            bldHeightValue = bldObject.get('GROUNDLEVEL_HEIGHT', 0)

            tmp_building_height_dict[bldTmpName] = bldHeightValue

        get_current_logger().debug('Building Height Dict is ' + str(tmp_building_height_dict))

        MIN_STAIRCASE_COUNT = 1

        js_liftStairsListUpdated = []
        isErrorForStairChecks = False
        buildListProcessed = []
        for stairChecks in js_liftStairsList:
            #
            buildingName = stairChecks.get('BLDG_NAME', 0)

            if (buildingName not in buildListProcessed):
                buildListProcessed.append(buildingName)

            buildingHeight = tmp_building_height_dict.get(buildingName, 0)

            stairChecks['BLDG_HEIGHT'] = str(buildingHeight)

            floorName = stairChecks.get('FLOOR_NAME', 0)
            floorArea = stairChecks.get('FLOOR_AREA', 0)

            noStairCnt = stairChecks.get('NO_OF_STAIRS', 0)
            rule_head_stairschecks = ''
            NO_OF_FLOORS = jsBuildingFloorDict.get(buildingName, 0)

            if (float(buildingHeight) > 0 and float(floorArea) >= 0 and 'TERRACE' not in floorName.upper()):
                # check if floorArea>500 or height > 15 m or if purposecode is S-1, S-3 9m if S-4>300
                if (NO_OF_FLOORS == 2):
                    MIN_STAIRCASE_COUNT = 0
                    rule_head_stairschecks = "For Buildings having ONLY GROUND FLOOR Stair Cases is Optional  "

                elif (self.purposecode in ['S-1', 'S-3'] and float(buildingHeight) >= 9):
                    MIN_STAIRCASE_COUNT = 2
                    rule_head_stairschecks = "For Educational and Institutional Buildings having a Height > 9 mt. No. of required Stair cases = " + str(
                        MIN_STAIRCASE_COUNT)

                elif (self.purposecode in ['S-4'] and float(floorArea) >= 300):
                    MIN_STAIRCASE_COUNT = 2
                    rule_head_stairschecks = "For Assembly Buildings having a Floor area > 300 sq. m. No. of required Stair cases = " + str(
                        MIN_STAIRCASE_COUNT)

                elif (float(floorArea) >= 750 or float(buildingHeight) >= 15):
                    MIN_STAIRCASE_COUNT = 2
                    rule_head_stairschecks = "For Buildings having a Floor area > 750 sq. m or Height >=15 mt. No. of required Stair cases = " + str(
                        MIN_STAIRCASE_COUNT)

                elif (float(floorArea) < 750 or float(buildingHeight) < 15):
                    MIN_STAIRCASE_COUNT = 1
                    rule_head_stairschecks = "For Buildings having a Floor area < 750 sq. m or Height <15 mt. No. of required Stair cases = " + str(
                        MIN_STAIRCASE_COUNT)

                else:
                    rule_head_stairschecks = "Unable to determine No. Of Stairs. Status is NOT OK Default No. of required Stair cases = " + str(
                        MIN_STAIRCASE_COUNT)
                    isErrorForStairChecks = True

            stairChecks['NO_OF_STAIRS_REQUIRED'] = str(MIN_STAIRCASE_COUNT)
            if (float(noStairCnt) >= MIN_STAIRCASE_COUNT and not isErrorForStairChecks):
                statusValue = "OK"
            else:
                # bypass for TERRACE
                if ('TERRACE' in floorName.upper()):
                    statusValue = "OK"
                else:
                    statusValue = "Not OK"

            stairChecks['STATUS'] = statusValue
            stairChecks['APPLICABLE_RULE'] = rule_head_stairschecks

            js_liftStairsListUpdated.append(stairChecks)

        self.reportExtractor.append(
            {"LIFT_STAIRS_INFO_NEW": [dict(sorted(dct.items())) for dct in js_liftStairsListUpdated]})

    def get_bldg2bldgdist_details(self):

        proposedWorkDict = self.combinedObjects.get(LayerMaster.PROPOSEDWORK.value).getBaseUnitDict() if self.combinedObjects.get(
            LayerMaster.PROPOSEDWORK.value, 0) != 0 else {}

        existingStructDict = self.combinedObjects.get(
        LayerMaster.EXISTINGSTRUCTURE.value).getBaseUnitDict() if self.combinedObjects.get(
        LayerMaster.EXISTINGSTRUCTURE.value, 0) != 0 else {}

        if (self.purposecode == 'A-2a'):  # VILLAS_ROWHOUSING
            MIN_DIST_REQUIRED_BLDG_TO_BLDG = 2.0
        else:
            MIN_DIST_REQUIRED_BLDG_TO_BLDG = 6.0

        js_bld_to_bld_distList = []

        masterBuildings_Exist_New = dict()
        checkForDuplicateDistances = dict()
        masterBuildings_Exist_New.update(proposedWorkDict)
        masterBuildings_Exist_New.update(existingStructDict)
        for sourceBlgKey, sourceBlgValue in masterBuildings_Exist_New.items():

            for targetName, targetObj in masterBuildings_Exist_New.items():
                if (sourceBlgKey != targetName):
                    routeName = sourceBlgKey + "-" + targetName
                    reverseRoute = targetName + "-" + sourceBlgKey
                    bldgProcessed = checkForDuplicateDistances.get(routeName, "NA")

                    if (bldgProcessed != "NA" or bldgProcessed == targetName):
                        continue
                    else:
                        # store both routes for given 2 buildings. distance will be same
                        checkForDuplicateDistances[routeName] = targetName
                        checkForDuplicateDistances[reverseRoute] = sourceBlgKey

                    js_bld_to_bld_dist = dict()
                    distVal = getDistanceBetweenObjects(sourceBlgValue.polygon, targetObj.polygon)
                    if ("demolish" in targetName.lower()):
                        continue

                    if (distVal != -99 and distVal >= MIN_DIST_REQUIRED_BLDG_TO_BLDG):
                        statusValue = "OK"
                    else:
                        if (distVal == -99):
                            distVal = "UnKnown"

                            get_current_logger().error(
                                f"Unable to get distance between source and target {sourceBlgKey} / {targetName}")

                        statusValue = "Not OK"
                    # detail
                    js_bld_to_bld_dist['FROM_BUILDING'] = removeSpecialChars(sourceBlgValue.name)
                    js_bld_to_bld_dist['TO_BUILDING'] = removeSpecialChars(targetObj.name)
                    js_bld_to_bld_dist['REQUIRED_MIN_DISTANCE'] = str(MIN_DIST_REQUIRED_BLDG_TO_BLDG)
                    js_bld_to_bld_dist['PROPOSED_DISTANCE'] = str(distVal)
                    js_bld_to_bld_dist['STATUS'] = statusValue
                    js_bld_to_bld_distList.append(js_bld_to_bld_dist)

        self.reportExtractor.append(
            {"BUILDING_TO_BUILDING_DISTANCES": [dict(sorted(dct.items())) for dct in js_bld_to_bld_distList]})

    def get_acce2plot_setback_details(self):

        INTERNALROAD_MIN_REQUIRED_WIDTH = 9.00
        MIN_DIST_REQUIRED_ACCESSORY_TO_PLOT = 1.0

        js_mainRoadInfoList = []
        mainRoadWidthList = []
        total_road_area = 0.0

        mainRoadList = self.combinedObjects.get(LayerMaster.MAINROAD.value).getBaseUnitFinalList() if self.combinedObjects.get(
            LayerMaster.MAINROAD.value, 0) != 0 else []

        plotUnitDict = self.combinedObjects.get(LayerMaster.PLOT.value).getBaseUnitDict() if self.combinedObjects.get(
            LayerMaster.PLOT.value, 0) != 0 else {}

        accessoryUnitsDict = self.combinedObjects.get(
            LayerMaster.ACCESSORYUSE.value).getBaseUnitDict() if self.combinedObjects.get(LayerMaster.ACCESSORYUSE.value,
                                                                                     0) != 0 else {}

        for por in mainRoadList:
            js_mainRoadInfo = dict()
            total_road_area += por.area
            startDelim = None
            existing_startDelim = ''

            if (por.name.upper().find('EXISTING') > -1):
                existing_widthOfRoad = float(
                    extract_dimensions_fromtext(str(por.name), existing_startDelim, "EXISTING"))
            else:
                existing_widthOfRoad = 'N/A'

            # proposed width delim
            if (por.name.upper().find('EXISTING') > -1):
                startDelim = 'EXISTING'

            widthOfRoad = float(extract_dimensions_fromtext(str(por.name), startDelim, "PROPOSED"))
            mainRoadWidthList.append(widthOfRoad)

            statusValue = "Not OK"
            if (widthOfRoad >= INTERNALROAD_MIN_REQUIRED_WIDTH):
                statusValue = "OK"

            js_mainRoadInfo['ROAD_NAME'] = removeSpecialChars(por.name)
            js_mainRoadInfo['ROAD_LENGTH'] = str(por.length)
            js_mainRoadInfo['INTERNALROAD_MIN_REQUIRED_WIDTH'] = str(INTERNALROAD_MIN_REQUIRED_WIDTH)
            js_mainRoadInfo['ROAD_WIDTH'] = str(widthOfRoad)
            js_mainRoadInfo['EXISTING_ROAD_WIDTH'] = str(existing_widthOfRoad)
            js_mainRoadInfo['ROAD_AREA'] = str(por.area)
            js_mainRoadInfo['STATUS'] = statusValue
            js_mainRoadInfoList.append(js_mainRoadInfo)

        js_setBacksAccessoryPlotList = []

        for sourceBlgKey, sourceBlgValue in plotUnitDict.items():

            # detail
            for targetName, targetObj in accessoryUnitsDict.items():
                accNameUpper = targetName.upper()
                if ('GATE' in accNameUpper):
                    continue

                js_setBacksPhysical = dict()

                distVal = getSetBacksByMidPoints(sourceBlgValue.polygon, targetObj.polygon)

                if (distVal != None and len(distVal) > 0):
                    distanceMinValue = min(distVal.values())
                    if (distanceMinValue >= MIN_DIST_REQUIRED_ACCESSORY_TO_PLOT):
                        statusValue = "OK"
                    else:
                        statusValue = "Not OK"

                else:
                    distanceMinValue = 'N/A'
                    if (distVal == -99):
                        get_current_logger().error(
                            f"Unable to get distance between source and target {sourceBlgKey} / {targetName}")
                    statusValue = "Not OK"

                cleanSourceName = removeSpecialChars(sourceBlgValue.name)
                cleanTargetName = removeSpecialChars(targetObj.name)
                js_setBacksPhysical['FROM'] = cleanSourceName
                js_setBacksPhysical['TO'] = cleanTargetName
                js_setBacksPhysical['REQUIRED_MIN_DISTANCE'] = str(MIN_DIST_REQUIRED_ACCESSORY_TO_PLOT)
                js_setBacksPhysical['PROPOSED_DISTANCE'] = str(distanceMinValue)
                js_setBacksPhysical['STATUS'] = statusValue
                js_setBacksAccessoryPlotList.append(js_setBacksPhysical)

        self.reportExtractor.append(
            {"SETBACKS_FOR_ACCESSORY2PLOT": [dict(sorted(dct.items())) for dct in js_setBacksAccessoryPlotList]})

    def get_indivsubplot_setbacks_details(self):

        mainRoadWidthList = []

        pop_msg_area = LayerMaster.MAINROAD.value
        mainRoadObjInst = ObjectByType(pop_msg_area)
        mainRoadList = mainRoadObjInst.getBaseUnitFinalList()

        floorInSectionDict = self.combinedObjects.get(
            LayerMaster.FLOORINSECTION.value).getBaseUnitDict() if self.combinedObjects.get(LayerMaster.FLOORINSECTION.value,
                                                                                       0) != 0 else {}

        pd.set_option("display.max_rows", None, "display.max_columns", None)
        floorInSection_df = pd.DataFrame.from_records([fs.get_dict() for fs in floorInSectionDict.values()])
        bldg_floor_resultdf = getBuilding_Floor_Heights(floorInSection_df, self.subtype)
        bldg_floor_resultdf.insert(0, 'Height_Mt._Permissible', '-')

        get_current_logger().debug(bldg_floor_resultdf)
        floor_height_col = bldg_floor_resultdf['Floor_Height']
        max_building_height = round(floor_height_col.max(), 2)
        get_current_logger().debug(f"MAX BUILDING HEIGHT :{max_building_height}")

        for por in mainRoadList:

            startDelim = None

            if (por.name.upper().find('EXISTING') > -1):
                startDelim = 'EXISTING'

            widthOfRoad = float(extract_dimensions_fromtext(str(por.name), startDelim, "PROPOSED"))
            mainRoadWidthList.append(widthOfRoad)

        if (len(mainRoadWidthList) > 0):
            MAX_MAIN_ROAD_WIDTH = max(mainRoadWidthList)
        else:
            MAX_MAIN_ROAD_WIDTH = 0.0

        js_setBacksVillasPlotList = []

        indivPlotDict = self.combinedObjects.get(LayerMaster.OPENLAYOUT.value).getBaseUnitDict() if self.combinedObjects.get(
            LayerMaster.OPENLAYOUT.value, 0) != 0 else {}

        proposedWorkDict = self.combinedObjects.get(LayerMaster.PROPOSEDWORK.value).getBaseUnitDict() if self.combinedObjects.get(
            LayerMaster.PROPOSEDWORK.value, 0) != 0 else {}

        for sourceBlgKey, sourceBlgValue in indivPlotDict.items():

            for targetName, targetObj in proposedWorkDict.items():

                if (targetObj.polygon.within(sourceBlgValue.polygon)):

                    js_setBacksIndivPlot = dict()

                    setBacksDict = getSetBacksByMidPoints(sourceBlgValue.polygon, targetObj.polygon)
                    setBacksDict['subtype'] = self.subtype
                    setBacksDict['proposed_site_area'] = round(sourceBlgValue.area, 2)
                    setBacksDict['proposed_bldg_height'] = str(max_building_height)
                    setBacksDict['proposed_abutting_road_width'] = MAX_MAIN_ROAD_WIDTH

                    setbacksRuleResult = callrule('ts-setbacks', setBacksDict)

                    setbacksResult = setbacksRuleResult["result"]

                    setback_rule = setbacksResult.get('zrule', 'N/A')

                    prop_abutting_roadwidth = setbacksResult.get('proposed_abutting_road_width', 'N/A')
                    req_abutting_roadwidth = setbacksResult.get('required_abutting_road_width', 'N/A')

                    prop_front_setback = setbacksResult.get('proposed_front_setback', 'N/A')
                    req_front_setback = setbacksResult.get('required_front_setback', 'N/A')

                    prop_rear_setback = setbacksResult.get('proposed_rear_setback', 'N/A')
                    req_rear_setback = setbacksResult.get('required_rear_setback', 'N/A')

                    prop_side1_setback = setbacksResult.get('proposed_side1_setback', 'N/A')
                    req_side1_setback = setbacksResult.get('required_side1_setback', 'N/A')

                    prop_side2_setback = setbacksResult.get('proposed_side2_setback', 'N/A')
                    req_side2_setback = setbacksResult.get('required_side2_setback', 'N/A')

                    setbacks_status = setbacksResult.get('status', 'NOT OK')

                    js_setBacksIndivPlot['FROM'] = removeSpecialChars(sourceBlgValue.name)
                    js_setBacksIndivPlot['TO'] = removeSpecialChars(targetObj.name)
                    js_setBacksIndivPlot['PROPOSED_ABUTTING_ROAD_WIDTH'] = str(prop_abutting_roadwidth)
                    js_setBacksIndivPlot['REQUIRED_ABUTTING_ROAD_WIDTH'] = str(req_abutting_roadwidth)
                    js_setBacksIndivPlot['PROPOSED_FRONT_SETBACK'] = prop_front_setback
                    js_setBacksIndivPlot['REQUIRED_FRONT_SETBACK'] = req_front_setback
                    js_setBacksIndivPlot['PROPOSED_REAR_SETBACK'] = prop_rear_setback
                    js_setBacksIndivPlot['REQUIRED_REAR_SETBACK'] = req_rear_setback
                    js_setBacksIndivPlot['PROPOSED_SIDE1_SETBACK'] = prop_side1_setback
                    js_setBacksIndivPlot['REQUIRED_SIDE1_SETBACK'] = req_side1_setback
                    js_setBacksIndivPlot['PROPOSED_SIDE2_SETBACK'] = prop_side2_setback
                    js_setBacksIndivPlot['REQUIRED_SIDE2_SETBACK'] = req_side2_setback
                    js_setBacksIndivPlot['STATUS'] = setbacks_status
                    js_setBacksIndivPlot['APPLICABLE_RULE'] = setback_rule

                    js_setBacksVillasPlotList.append(js_setBacksIndivPlot)

    def get_setbackForPlot_details(self):

        if self.runOnlyCombinedUtil == "True":
            get_current_logger().info(f'Bypassed Due to runOnlyCombinedUtil In Drawing {self.runOnlyCombinedUtil}')

        else:

            js_setBacksPlotList1 = []

            pop_msg_area = LayerMaster.MAINROAD.value
            mainRoadObjInst = ObjectByType(pop_msg_area)
            mainRoadList = mainRoadObjInst.getBaseUnitFinalList()

            floorInSectionDict = self.combinedObjects.get(
                LayerMaster.FLOORINSECTION.value).getBaseUnitDict() if self.combinedObjects.get(
                LayerMaster.FLOORINSECTION.value,
                0) != 0 else {}

            pd.set_option("display.max_rows", None, "display.max_columns", None)
            floorInSection_df = pd.DataFrame.from_records([fs.get_dict() for fs in floorInSectionDict.values()])
            bldg_floor_resultdf = getBuilding_Floor_Heights(floorInSection_df, self.subtype)
            bldg_floor_resultdf.insert(0, 'Height_Mt._Permissible', '-')

            floor_height_col = bldg_floor_resultdf['Floor_Height']
            max_building_height = round(floor_height_col.max(), 2)
            get_current_logger().debug(f"MAX BUILDING HEIGHT :{max_building_height}")

            mainRoadWidthList=[]
            for por in mainRoadList:
                startDelim = None
                # proposed width delim
                if (por.name.upper().find('EXISTING') > -1):
                    startDelim = 'EXISTING'

                widthOfRoad = float(extract_dimensions_fromtext(str(por.name), startDelim, "PROPOSED"))
                mainRoadWidthList.append(widthOfRoad)

            if (len(mainRoadWidthList) > 0):
                MAX_MAIN_ROAD_WIDTH = max(mainRoadWidthList)
            else:
                MAX_MAIN_ROAD_WIDTH = 0.0

            proposedWorkDict = self.combinedObjects.get(LayerMaster.PROPOSEDWORK.value).getBaseUnitDict() if self.combinedObjects.get(
                LayerMaster.PROPOSEDWORK.value, 0) != 0 else {}

            for targetName, targetObj in proposedWorkDict.items():
                js_setBacksPlot = dict()

                sbOption3 = self.setBacksDictConsolidated.get(targetObj.handle, {})

                setBacksDict = dict()

                setBacksDict['proposed_front_setback'] = sbOption3.get('FRONT', 0)
                setBacksDict['proposed_rear_setback'] = sbOption3.get('REAR', 0)
                setBacksDict['proposed_side1_setback'] = sbOption3.get('SIDE1', 0)
                setBacksDict['proposed_side2_setback'] = sbOption3.get('SIDE2', 0)

                setBacksDict['subtype'] = self.subtype
                setBacksDict['proposed_site_area'] = round(self.totalNetplotArea, 2)
                setBacksDict['proposed_bldg_height'] = max_building_height
                setBacksDict['proposed_abutting_road_width'] = MAX_MAIN_ROAD_WIDTH

                setbacksRuleResult = callrule('ts-setbacks', setBacksDict)
                setbacksResult = setbacksRuleResult["result"]
                setback_rule = setbacksResult.get('zrule', 'N/A')

                prop_abutting_roadwidth = setbacksResult.get('proposed_abutting_road_width', 'N/A')
                req_abutting_roadwidth = setbacksResult.get('required_abutting_road_width', 'N/A')

                prop_front_setback = setbacksResult.get('proposed_front_setback', 'N/A')
                req_front_setback = setbacksResult.get('required_front_setback', 'N/A')

                prop_rear_setback = setbacksResult.get('proposed_rear_setback', 'N/A')
                req_rear_setback = setbacksResult.get('required_rear_setback', 'N/A')

                prop_side1_setback = setbacksResult.get('proposed_side1_setback', 'N/A')
                req_side1_setback = setbacksResult.get('required_side1_setback', 'N/A')

                prop_side2_setback = setbacksResult.get('proposed_side2_setback', 'N/A')
                req_side2_setback = setbacksResult.get('required_side2_setback', 'N/A')

                setbacks_status = setbacksResult.get('status', 'NOT OK')

                js_setBacksPlot['FROM'] = removeSpecialChars('Margin Plot')
                js_setBacksPlot['TO'] = removeSpecialChars(targetObj.name)
                js_setBacksPlot['PROPOSED_ABUTTING_ROAD_WIDTH'] = str(prop_abutting_roadwidth)
                js_setBacksPlot['REQUIRED_ABUTTING_ROAD_WIDTH'] = str(req_abutting_roadwidth)
                js_setBacksPlot['PROPOSED_FRONT_SETBACK'] = str(prop_front_setback)
                js_setBacksPlot['REQUIRED_FRONT_SETBACK'] = str(req_front_setback)
                js_setBacksPlot['PROPOSED_REAR_SETBACK'] = str(prop_rear_setback)
                js_setBacksPlot['REQUIRED_REAR_SETBACK'] = str(req_rear_setback)
                js_setBacksPlot['PROPOSED_SIDE1_SETBACK'] = str(prop_side1_setback)
                js_setBacksPlot['REQUIRED_SIDE1_SETBACK'] = str(req_side1_setback)
                js_setBacksPlot['PROPOSED_SIDE2_SETBACK'] = str(prop_side2_setback)
                js_setBacksPlot['REQUIRED_SIDE2_SETBACK'] = str(req_side2_setback)
                js_setBacksPlot['STATUS'] = setbacks_status
                js_setBacksPlot['APPLICABLE_RULE'] = setback_rule

                js_setBacksPlotList1.append(js_setBacksPlot)

            self.reportExtractor.append(
                {"SETBACKS_FOR_PLOT": [dict(sorted(dct.items())) for dct in js_setBacksPlotList1]})

    def get_podiumsetbacksForPlot_details(self):

        pop_msg_area = LayerMaster.MAINROAD.value
        mainRoadObjInst = ObjectByType(pop_msg_area)
        mainRoadList = mainRoadObjInst.getBaseUnitFinalList()

        floorInSectionDict = self.combinedObjects.get(
            LayerMaster.FLOORINSECTION.value).getBaseUnitDict() if self.combinedObjects.get(
            LayerMaster.FLOORINSECTION.value,
            0) != 0 else {}

        pd.set_option("display.max_rows", None, "display.max_columns", None)
        floorInSection_df = pd.DataFrame.from_records([fs.get_dict() for fs in floorInSectionDict.values()])
        bldg_floor_resultdf = getBuilding_Floor_Heights(floorInSection_df, self.subtype)
        bldg_floor_resultdf.insert(0, 'Height_Mt._Permissible', '-')

        floor_height_col = bldg_floor_resultdf['Floor_Height']
        max_building_height = round(floor_height_col.max(), 2)
        get_current_logger().debug(f"MAX BUILDING HEIGHT :{max_building_height}")

        mainRoadWidthList = []
        for por in mainRoadList:

            startDelim = None

            # proposed width delim
            if (por.name.upper().find('EXISTING') > -1):
                startDelim = 'EXISTING'

            widthOfRoad = float(extract_dimensions_fromtext(str(por.name), startDelim, "PROPOSED"))
            mainRoadWidthList.append(widthOfRoad)

        if (len(mainRoadWidthList) > 0):
            MAX_MAIN_ROAD_WIDTH = max(mainRoadWidthList)
        else:
            MAX_MAIN_ROAD_WIDTH = 0.0

        js_setBacksPlotList1 = []

        marginPlotList = self.combinedObjects.get(LayerMaster.MARGINLINE.value).getBaseList() if self.combinedObjects.get(
            LayerMaster.MARGINLINE.value, 0) != 0 else []

        for sourceBlgValue in marginPlotList:

            for targetName, targetObj in self.podiumSetBacksDictConsolidated.items():

                for podiumBldg, podiumBldgObjLst in targetObj.items():

                    for podiumFloorObj in podiumBldgObjLst:

                        floorName = podiumBldg + " - " + podiumFloorObj.get('NAME', 'N/A')
                        setBacksDict = dict()

                        setBacksDict['proposed_front_setback'] = podiumFloorObj.get('FRONT', 0)
                        setBacksDict['proposed_rear_setback'] = podiumFloorObj.get('REAR', 0)
                        setBacksDict['proposed_side1_setback'] = podiumFloorObj.get('SIDE1', 0)
                        setBacksDict['proposed_side2_setback'] = podiumFloorObj.get('SIDE2', 0)

                        setBacksDict['subtype'] = self.subtype
                        setBacksDict['proposed_site_area'] = round(self.totalNetplotArea, 2)
                        setBacksDict['proposed_bldg_height'] = max_building_height
                        setBacksDict['proposed_abutting_road_width'] = MAX_MAIN_ROAD_WIDTH
                        setBacksDict['purposecode'] = self.purposecode

                        setbacksRuleResult = callrule('ts-setbacks', setBacksDict)

                        setbacksResult = setbacksRuleResult["result"]

                        setback_rule = setbacksResult.get('zrule', 'N/A')

                        prop_abutting_roadwidth = setbacksResult.get('proposed_abutting_road_width', 'N/A')
                        req_abutting_roadwidth = setbacksResult.get('required_abutting_road_width', 'N/A')

                        prop_front_setback = setbacksResult.get('proposed_front_setback', 'N/A')
                        req_front_setback = setbacksResult.get('required_front_setback', 'N/A')

                        prop_rear_setback = setbacksResult.get('proposed_rear_setback', 'N/A')
                        req_rear_setback = setbacksResult.get('required_rear_setback', 'N/A')

                        prop_side1_setback = setbacksResult.get('proposed_side1_setback', 'N/A')
                        req_side1_setback = setbacksResult.get('required_side1_setback', 'N/A')

                        prop_side2_setback = setbacksResult.get('proposed_side2_setback', 'N/A')
                        req_side2_setback = setbacksResult.get('required_side2_setback', 'N/A')

                        setbacks_status = setbacksResult.get('status', 'NOT OK')

                        js_setBacksPlot = dict()
                        js_setBacksPlot['FROM'] = removeSpecialChars('Margin Plot')
                        js_setBacksPlot['TO'] = removeSpecialChars(floorName)
                        js_setBacksPlot['PROPOSED_ABUTTING_ROAD_WIDTH'] = str(prop_abutting_roadwidth)
                        js_setBacksPlot['REQUIRED_ABUTTING_ROAD_WIDTH'] = str(req_abutting_roadwidth)
                        js_setBacksPlot['PROPOSED_FRONT_SETBACK'] = prop_front_setback
                        js_setBacksPlot['REQUIRED_FRONT_SETBACK'] = req_front_setback
                        js_setBacksPlot['PROPOSED_REAR_SETBACK'] = prop_rear_setback
                        js_setBacksPlot['REQUIRED_REAR_SETBACK'] = req_rear_setback
                        js_setBacksPlot['PROPOSED_SIDE1_SETBACK'] = prop_side1_setback
                        js_setBacksPlot['REQUIRED_SIDE1_SETBACK'] = req_side1_setback
                        js_setBacksPlot['PROPOSED_SIDE2_SETBACK'] = prop_side2_setback
                        js_setBacksPlot['REQUIRED_SIDE2_SETBACK'] = req_side2_setback
                        js_setBacksPlot['STATUS'] = setbacks_status
                        js_setBacksPlot['APPLICABLE_RULE'] = setback_rule

                        js_setBacksPlotList1.append(js_setBacksPlot)

        self.reportExtractor.append({"PODIUM_SETBACKS_FOR_PLOT": js_setBacksPlotList1})

    def get_commonfloor_setbacks_details(self):
        commonFloorSetbacksList = None

        try:

            if self.runOnlyCombinedUtil == "True":
                get_current_logger().debug(
                    f'+++++++++++++  Bypassed Due to runOnlyCombinedUtil In Drawing  {self.runOnlyCombinedUtil}')
            else:
                commonFloorSetbacksDictResponse = commonfloor_setbacks(self.modelspace_dwg)

                if (commonFloorSetbacksDictResponse is not None and commonFloorSetbacksDictResponse.get('CODE',
                                                                                                        1) == 0):
                    commonFloorSetbacksList = commonFloorSetbacksDictResponse.get('DATA', [])
                else:
                    get_current_logger().debug(
                        f'+++++++++++++  WARNING - commonfloor_setbacks - No Valid Response - setting to blank  {commonFloorSetbacksDictResponse}')
                    commonFloorSetbacksList = []

        except ezdxf.lldxf.const.DXFAttributeError as attrMsg:
            commonFloorSetbacksList = []

            msg = f'Problem Running Common Floor Setbacks - DXF Attribute Error filename {self.filename} due to {attrMsg}'
            get_current_logger().error(msg)

        js_commonFloorSetbacksList = []

        # Add Blank if no valid response received
        if (commonFloorSetbacksList is not None and len(commonFloorSetbacksList) > 0):

            for commonFloorSetback in commonFloorSetbacksList:

                bldKey = commonFloorSetback.get('NAME', '')

                if (bldKey != ''):
                    abuttingRoadsPropRequiredDict = self.abuttingRoadPropRequiredDict.get(bldKey, dict())

                    commonFloorSetback.update(abuttingRoadsPropRequiredDict)

                js_commonFloorSetbacksList.append(commonFloorSetback)

            self.reportExtractor.append(
                {"COMMONFLOOR_SETBACKS_FOR_PLOT": [dict(sorted(dct.items())) for dct in js_commonFloorSetbacksList]})
        else:

            self.reportExtractor.append({"COMMONFLOOR_SETBACKS_FOR_PLOT": []})

    def get_transfersetbacks_details(self):

        transferOfSetbacksResponse = dict()

        if self.runOnlyCombinedUtil == "True":
            get_current_logger().info(f'Bypassed Due to runOnlyCombinedUtil In Drawing {self.runOnlyCombinedUtil}')
        else:
            transferOfSetbacksResponse = get_transfer_of_setbacks(self.modelspace_dwg)

        if (transferOfSetbacksResponse is not None):
            transferOfSetbacksListDirect = transferOfSetbacksResponse.get('TRANSFER_OF_SETBACKS_RESPONSE', {})
        else:
            transferOfSetbacksListDirect = dict()

        js_transferOfSetbacksPlotList = []

        for transferSbObj in transferOfSetbacksListDirect:

            for bldgName, sbList in transferSbObj.items():
                # each transfer details
                for sbObject in sbList:
                    js_transferOfSetbacks = dict()
                    js_transferOfSetbacks['BLDG_NAME'] = "\"" + str(bldgName) + "\""
                    js_transferOfSetbacks['POSITION'] = str(sbObject.get('POSITION', '-'))
                    js_transferOfSetbacks['TRANSFER_SETBACK_TYPE'] = str(sbObject.get('TRANSFER_SETBACK_TYPE', '-'))
                    js_transferOfSetbacks['TRANSFER_AREA'] = str(sbObject.get('AREA', '-'))
                    js_transferOfSetbacks['MIN_WIDTH'] = str(sbObject.get('MIN_WIDTH', '-'))
                    js_transferOfSetbacks['MAX_WIDTH'] = str(sbObject.get('MAX_WIDTH', '-'))
                    js_transferOfSetbacksPlotList.append(js_transferOfSetbacks)

        self.reportExtractor.append({"TRANSFER_OF_SETBACKS": js_transferOfSetbacksPlotList})

    def get_windowspassage_details(self):
        passageUnitsDict = self.combinedObjects.get(LayerMaster.PASSAGE.value).getBaseUnitDict() if self.combinedObjects.get(
            LayerMaster.PASSAGE.value, 0) != 0 else {}

        passageDictDirect = self.combinedObjects.get('PASSAGE_WIDTHS', dict())

        windowInPassageDirectDict = dict()
        try:
            if (self.purposecode not in ['A-2a']):

                if self.runOnlyCombinedUtil == "True":
                    get_current_logger().debug(
                        f'+++++++++++++  Bypassed Due to runOnlyCombinedUtil In Drawing  {self.runOnlyCombinedUtil}')
                else:
                    windowInPassageDirectDict = window_in_passage_check(self.modelspace_dwg)
                    get_current_logger().debug(f'window in passage checks  {windowInPassageDirectDict}')

        except Exception as ex:
            get_current_logger().error(f'Problem processing window_in_passage_check due to  {ex}')

        # PASSAGES
        PASSAGES_MIN_REQUIRED_WIDTH = 1.5
        passageParams = dict()
        passageParams['purpose_code'] = self.purposecode
        passageParams['proposed_passage_width'] = 1
        passageParams['plan_type'] = 'Building_Layout'
        passageParams['authority'] = self.request_params.get('authority', 'HMDA')
        passageRuleResult = callrule('ts-passage', passageParams)

        defaultPassageValues = dict()
        defaultPassageValues['required_passage_width'] = PASSAGES_MIN_REQUIRED_WIDTH
        defaultPassageValues['status'] = 'NOT OK'
        defaultPassageValues['zrule'] = 'N/A'
        passageResult = passageRuleResult.get("result", defaultPassageValues)

        requiredPassageWidth = passageResult.get('required_passage_width_min', PASSAGES_MIN_REQUIRED_WIDTH)
        passageRuleDesc = passageResult.get('zrule', 'N/A')

        js_setPassagesList = []
        for psgItem, psgObj in passageUnitsDict.items():
            js_setPassages = dict()

            widthOfPassageCheck = passageDictDirect.get(psgObj.handle, 0)
            windowExists = False
            windowResultList = windowInPassageDirectDict.get(psgObj.handle, [])
            if (len(windowResultList) > 0):
                windowExists = windowResultList[0]

            if (widthOfPassageCheck is None):
                widthtoUse = round(float(psgObj.width),
                                   2)  # round(float(getMinWidthIrregularObjects(por.polygon) ),2)
                get_current_logger().warning(f'Passage Handle #  {psgObj.handle}  Unable to get from direct method')
            else:
                widthtoUse = round(float(widthOfPassageCheck), 2)

            get_current_logger().debug(
                f'Passage Handle # {psgObj.handle}, Width Calc ====> {widthtoUse}, Window exists {windowExists}'
            )

            if (widthtoUse >= float(requiredPassageWidth) and windowExists == False):
                statusValue = "OK"
            else:
                statusValue = "Not OK"
            flrName = str(psgObj.parent.replace('|', '-'))

            js_setPassages['FLOOR_NAME'] = flrName
            js_setPassages['PASSAGE_NAME'] = str(psgObj.name)
            js_setPassages['REQUIRED_MIN_WIDTH'] = str(requiredPassageWidth)
            js_setPassages['PROPOSED_PASSAGE_WIDTH'] = str(widthtoUse)
            js_setPassages['PROPOSED_PASSAGE_LENGTH'] = str(psgObj.length)
            js_setPassages['WINDOW_IN_PASSAGE'] = str(windowExists)
            js_setPassages['STATUS'] = statusValue
            js_setPassages['APPLICABLE_RULE'] = passageRuleDesc
            js_setPassagesList.append(js_setPassages)

        self.reportExtractor.append({"PASSAGE_DETAILS": [dict(sorted(dct.items())) for dct in js_setPassagesList]})

    def get_parking_details(self):

        parking_category = getCategoryForParking(self.request_params)
        parkingUnitsDict = self.combinedObjects.get(LayerMaster.PARKING.value).getBaseUnitDict() if self.combinedObjects.get(
            LayerMaster.PARKING.value, 0) != 0 else {}
        parkingChecksDict = dict()
        parkingChecksDict['subtype'] = self.subtype
        parkingChecksDict['proposed_site_area'] = round(self.totalNetplotArea, 2)
        parkingChecksDict['proposed_parking_factor'] = 1
        parkingChecksDict['proposed_visitor_parking_factor'] = 0
        parkingChecksDict['location'] = self.location
        parkingChecksDict['subuse'] = self.subuse
        parkingChecksDict['parking_category'] = parking_category
        parkingChecksDict['request_params'] = self.combinedObjects.get(LayerMaster.REQUEST_PARAMS.value)

        parkingChecksRuleResult = callrule('ts-parking', parkingChecksDict)

        parkingChecksResult = parkingChecksRuleResult["result"]

        PARKING_MIN_REQUIRED_AREA_PERCENT = parkingChecksResult.get('required_parking_factor', 30)
        PARKING_VISITORS_PERCENT = parkingChecksResult.get('required_visitor_parking_factor', 10)
        PARKING_RULE = parkingChecksResult.get('zrule', 'N/A')

        # detail
        totalCustomerParkingArea = 0.0
        customerParkCount = 0
        totalVisitorParkingArea = 0.0
        visitorParkCount = 0
        totalOutsideParkingArea = 0.0
        outsideParkCount = 0

        outsideParkingList = []

        for parkingObjItem, parkingObj in parkingUnitsDict.items():
            pkName = parkingObj.name.upper()
            pkArea = parkingObj.area

            parkingFloorObj = self.masterFloorDict.get(parkingObj.parent, 0)
            if (parkingFloorObj != 0):

                if (pkArea == parkingFloorObj.maxParkingarea):
                    get_current_logger().error(f"Parking areas matches with floor bua area .. "
                                        f"(skipping parkArea , floorParkingArea) {(pkArea, parkingFloorObj.maxParkingarea)}")
                    continue  # skip
                else:

                    # check if parking is stack then add
                    if ("-1,2(MECH.)" in pkName.upper() or "STACK" in pkName.upper()):
                        self.stackParkingArea += pkArea  # add only the delta

                    if ("VISITOR" in pkName):

                        totalVisitorParkingArea = totalVisitorParkingArea + pkArea
                        visitorParkCount = visitorParkCount + 1

                    else:

                        totalCustomerParkingArea = totalCustomerParkingArea + pkArea
                        customerParkCount = customerParkCount + 1

            else:

                outsideParkingList.append(parkingObj)

        for outrParking in outsideParkingList:
            outrPoly = shapely.wkt.loads(str(outrParking.polygon))

            for innerParking in outsideParkingList:
                innerPoly = shapely.wkt.loads(str(innerParking.polygon))
                if (outrParking.handle != innerParking.handle):  # outrParking.area >= innerParking.area ):

                    # check if innerParking is within the outrParking
                    if (innerPoly.within(outrPoly) and "VISITOR" in innerParking.name.upper()):

                        totalVisitorParkingArea = totalVisitorParkingArea + float(innerParking.area)
                        visitorParkCount = visitorParkCount + 1
                    else:
                        totalOutsideParkingArea = totalOutsideParkingArea + float(innerParking.area)
                        outsideParkCount = outsideParkCount + 1

        totalParkingAreaSection = totalOutsideParkingArea + self.totalParkingArea + self.stackParkingArea


        TOTAL_PARKING_AREA_REQUIRED = round((PARKING_MIN_REQUIRED_AREA_PERCENT * self.totalProposedBUAArea / 100), 2)

        if (totalParkingAreaSection >= TOTAL_PARKING_AREA_REQUIRED and totalVisitorParkingArea >= round((PARKING_VISITORS_PERCENT * (TOTAL_PARKING_AREA_REQUIRED) / 100), 2)):
            statusValue = "OK"
        else:
            statusValue = "NOT OK"

        js_parkingInfo = dict()

        js_parkingInfo['PARKING_MIN_REQUIRED_AREA_PERCENT'] = str(PARKING_MIN_REQUIRED_AREA_PERCENT)
        js_parkingInfo['TOTAL_PARKING_AREA_REQUIRED'] = str(round(TOTAL_PARKING_AREA_REQUIRED, 2))
        js_parkingInfo['TOTAL_PARKING_AREA_PROPOSED'] = str(round(totalParkingAreaSection, 2))
        js_parkingInfo['TOTAL_STACK_PARKING_AREA'] = str(round(self.totalStackParkingArea, 2))
        js_parkingInfo['TOTAL_INSIDE_PARKING_AREA'] = str(round(self.totalParkingArea, 2))
        js_parkingInfo['TOTAL_OUTSIDE_PARKING_AREA'] = str(round(totalOutsideParkingArea, 2))
        js_parkingInfo['CUSTOMER_PARKING_SLOTS'] = str(customerParkCount)
        js_parkingInfo['CUSTOMER_PARKING_AREA'] = str(totalCustomerParkingArea)
        js_parkingInfo['VISITOR_PARKING_SLOTS'] = str(visitorParkCount)
        js_parkingInfo['VISITOR_PARKING_AREA'] = str(round(totalVisitorParkingArea, 2))
        js_parkingInfo['STATUS'] = statusValue
        remarks = ' TOTAL PARKING PROPOSED is SUM of TOTAL_INSIDE_PARKING_AREA, TOTAL_OUTSIDE_PARKING_AREA, TOTAL_STACK_PARKING_AREA '

        js_parkingInfo['APPLICABLE_RULE'] = PARKING_RULE + remarks

        self.reportExtractor.append({"PARKING_SUMMARY": dict(sorted(js_parkingInfo.items()))})

    def get_ramp_details(self):

        plinthHeight = 0.0
        floorHeight = 0.0
        stiltHeight = 0.0
        liftHeight = 0.0
        cellarHeight = 0.0
        terraceHeight = 0.0

        isStilt = False
        isTerrace = False
        isFloor = False
        isCellar = False
        isPlinth = False

        bldg_heights_dict = dict()
        NO_OF_FLOORS = 0
        jsBuildingFloorDict = dict()

        flrInSectHeightDict = dict()

        floorInSectionDict = self.combinedObjects.get(
            LayerMaster.FLOORINSECTION.value).getBaseUnitDict() if self.combinedObjects.get(LayerMaster.FLOORINSECTION.value,
                                                                                       0) != 0 else {}

        for flrSecItem, flrSecObj in floorInSectionDict.items():

            # print("FLR SEC ITEM ", flrSecItem)
            if ("TERRACE" in flrSecItem):
                isTerrace = True  # continue
                continue

            if ("STILT" in flrSecItem):
                if (self.stackParkingArea > 0):
                    requiredHeight = 4.5
                else:
                    requiredHeight = 2.50
                isStilt = True
            elif ("CELLAR" in flrSecItem or "BASEMENT" in flrSecItem):
                requiredHeight = 2.40
                isCellar = True
            elif ("PLINTH" in flrSecItem):
                requiredHeight = 0.45
                isPlinth = True
            else:
                requiredHeight = 2.75
                isFloor = True

            if (flrSecObj.height >= requiredHeight):
                statusValue = "OK"
            else:
                statusValue = "Not OK"

            tmpDxfPoly = flrSecObj.get_DXFPoly()
            isTDR = "-"
            if (tmpDxfPoly != None):
                colorTmp = tmpDxfPoly.getColor()
                if (int(colorTmp) == 240):
                    isTDR = "Yes"
                    get_current_logger().debug(f"isTDR True - as DXF Poly is color is: {colorTmp}")

            if (isFloor):
                floorHeight += flrSecObj.height
                liftHeight += flrSecObj.height

                bldg_heights_dict[flrSecObj.parent + '|FLOOR'] = floorHeight
                bldg_heights_dict[flrSecObj.parent + '|LIFT'] = liftHeight
            elif (isStilt):
                stiltHeight += flrSecObj.height

                bldg_heights_dict[flrSecObj.parent + '|STILT'] = stiltHeight
            elif (isCellar):
                cellarHeight += flrSecObj.height

                bldg_heights_dict[flrSecObj.parent + '|CELLAR'] = cellarHeight
            elif (isTerrace):
                terraceHeight += flrSecObj.height
                bldg_heights_dict[flrSecObj.parent + '|TERRACE'] = terraceHeight
            elif (isPlinth):
                plinthHeight += flrSecObj.height
                bldg_heights_dict[flrSecObj.parent + '|PLINTH'] = plinthHeight

            if (jsBuildingFloorDict.get(flrSecObj.parent, 0) == 0):
                if (isFloor or isStilt or isCellar or isTerrace):
                    jsBuildingFloorDict[flrSecObj.parent] = 1
            else:
                if (isFloor or isStilt or isCellar or isTerrace):
                    no_of_floors = jsBuildingFloorDict.get(flrSecObj.parent)
                    no_of_floors += 1
                    jsBuildingFloorDict[flrSecObj.parent] = no_of_floors

            flrInSectHeightDict[flrSecObj.parent.strip() + "-" + flrSecObj.name.strip()] = flrSecObj.height

        rampUnitsDict = self.combinedObjects.get(LayerMaster.RAMP.value).getBaseUnitDict() if self.combinedObjects.get(
            LayerMaster.RAMP.value, 0) != 0 else {}

        # RAMP CHECKS
        RAMP_MIN_REQUIRED_WIDTH = 5.40
        RAMP_MIN_SLOPE_VEH_REQUIRED = 8  # slope /gradient value will be shown as "1: 08 "  i.e. for 1 mt riser , need 8 mt. length/run
        RAMP_MIN_SLOPE_PED_REQUIRED = 1


        js_rampInfoList = []
        rampGradientValue = 0.0
        lengthToUse = 0.0
        rampInfoNewDirect = get_ramp_info(self.modelspace_dwg)
        gotRampInfo = False

        if (rampInfoNewDirect != None and rampInfoNewDirect.get('CODE', -2) == 0):

            rampInfoResponse = rampInfoNewDirect.get('RAMP_INFO_RESPONSE', 0)
            if (rampInfoResponse != 0 and len(rampInfoResponse) > 0):
                gotRampInfo = True

            # BLDG_FLOOR_KEY
            get_current_logger().debug(f'Length of RAMPINFORESPONSE  {len(rampInfoResponse)}')

            get_current_logger().debug(f'Floor In Section Height by Building  {flrInSectHeightDict} ')

            for rampItem, rampObj in rampUnitsDict.items():

                if ("Pedestrian" in rampObj.name):
                    RAMP_MIN_SLOPE_TO_CHECK = RAMP_MIN_SLOPE_PED_REQUIRED
                else:
                    RAMP_MIN_SLOPE_TO_CHECK = RAMP_MIN_SLOPE_VEH_REQUIRED

                js_rampInfo = dict()

                # check Gradient
                if (gotRampInfo):

                    rampTmpDict = rampInfoResponse.get(rampObj.handle, '')
                    if (rampTmpDict is not None and len(rampTmpDict) > 0):
                        lengthToUse = rampTmpDict.get('RAMP_LENGTH', 0.0)
                        widthtoUse = rampTmpDict.get('RAMP_WIDTH', 0.0)
                        rampKey = rampTmpDict.get('BLDG_FLOOR_KEY', 'N/A')

                        floorHeight = flrInSectHeightDict.get(rampKey, 0)

                        if (floorHeight == 0):
                            rampKey = rampKey.replace('PLAN', '').strip()
                            floorHeight = flrInSectHeightDict.get(rampKey, 0)

                        rampGradientValue = calc_gradient(lengthToUse, floorHeight)
                else:
                    rampGradientValue = rampObj.gradient
                    widthtoUse = rampObj.width
                    lengthToUse = 0.0
                if (widthtoUse >= RAMP_MIN_REQUIRED_WIDTH and rampGradientValue >= RAMP_MIN_SLOPE_TO_CHECK):
                    statusValue = "OK"
                else:
                    statusValue = "Not OK"

                bldg_floor = str(rampObj.parent.replace('|', '-'))

                js_rampInfo['BUILDNG_FLOOR'] = bldg_floor
                js_rampInfo['RAMP_NAME'] = str(rampObj.name)
                js_rampInfo['RAMP_DWG_REFERENCE'] = str(rampObj.handle)
                js_rampInfo['REQUIRED_MIN_WIDTH'] = str(RAMP_MIN_REQUIRED_WIDTH)
                js_rampInfo['PROPOSED_WIDTH'] = str(widthtoUse)
                js_rampInfo['PROPOSED_LENGTH'] = str(lengthToUse)
                js_rampInfo['PROPOSED_FLOOR_HEIGHT'] = str(floorHeight)
                js_rampInfo['PROPOSED_GRADIENT_VALUE'] = str(rampGradientValue)

                js_rampInfo['PERMISSIBLE_SLOPE_RATIO'] = "1: " + str(RAMP_MIN_SLOPE_TO_CHECK)
                js_rampInfo['PROPOSED_SLOPE_RATIO'] = "1: " + str(rampGradientValue)
                js_rampInfo['STATUS'] = statusValue
                js_rampInfoList.append(js_rampInfo)

            self.reportExtractor.append({"RAMP_INFORMATION": [dict(sorted(dct.items())) for dct in js_rampInfoList]})

        else:
            get_current_logger().info("Problem extracting RAMP Info - please check the Drawing")

            if (rampInfoNewDirect != None):
                get_current_logger().info(
                    f"ramp check CODE {rampInfoNewDirect.get('CODE', -2)}"
                )
                if (rampInfoNewDirect.get('CODE', -2) == -1):
                    get_current_logger().info("ramp check CODE ")
                    errorToAdd = rampInfoNewDirect.get('ERROR', "N/A")
                    self.warnings.append(errorToAdd)
                    self.reportExtractor.append({"RAMP_INFORMATION": []})

    def get_room_dimentions(self):

        roomDimensionsDirectDict = None
        roomVentilationResponseDict = dict()

        roomDimensionsDirectDict = window_check_util(self.modelspace_dwg)

        if (roomDimensionsDirectDict is not None and roomDimensionsDirectDict.get('RESULTS', 0) != 0):
            roomVentilationResponseDict = roomDimensionsDirectDict.get('RESULTS')

        balconyMainDoorDirectDict = dict()
        try:
            if (self.purposecode not in ['A-2a']):

                if self.runOnlyCombinedUtil == "True":

                    get_current_logger().debug(
                        f'+++++++++++++  Bypassed Due to runOnlyCombinedUtil In Drawing {self.runOnlyCombinedUtil}')
                else:
                    balconyMainDoorDirectDict = check_balcony_maindoor(self.modelspace_dwg)

            else:
                get_current_logger().warning('WARNING - PURPOSECODE A-2a not caling balcony_maindoor')

        except Exception as ex:

            get_current_logger().error(f'Problem processing check_balcony_maindoor due to  {ex}')

        commonBuildingUtilsResponse = dict()
        listOfUtils = list()

        try:

            commonBuildingUtilsResponse = runCommonBuildingUtils(self.modelspace_dwg)
            listOfUtils = commonBuildingUtilsResponse.get('SUPPORTED_BUILDING_UTILS')

            for utilname in listOfUtils:
                get_current_logger().info(f' utility : {utilname}')
                key = utilname + '_RESULT'

                self.reportExtractor.append({key: commonBuildingUtilsResponse.get(key, [])})

        except Exception as ex:
            get_current_logger().error(f'Problem processing due to {ex}')

    def get_balcony_dimention_details(self):

        balconyInfoDirectDict = dict()

        try:
            if (self.purposecode not in ['A-2a']):
                balconyInfoDirectDict = getBalconyInfo(self.modelspace_dwg)

            else:
                get_current_logger().warning('WARNING - PURPOSECODE A-2a not caling balcony_maindoor')
        except Exception as ex:
            get_current_logger().error(f'Problem processing due to  {ex}')

        # problem getting balcony

        # build the response for Balcony
        js_balconyDimensionsInfoList = []

        if (balconyInfoDirectDict is not None and len(balconyInfoDirectDict) > 0):
            # check the return code
            balconyResponseCode = balconyInfoDirectDict.get('CODE', -2)
            if (balconyResponseCode < 0):
                # problem extract the msg
                errMsg = balconyInfoDirectDict.get('ERROR', 'N/A')
            else:
                # extract the RESULTS
                balconyDataList = balconyInfoDirectDict.get('RESULTS', [])

                for balconyInfo in balconyDataList:
                    # Dict
                    balconyDimDict = dict()
                    balconyDimDict['BLDG_REF'] = balconyInfo.get('BLDG_REF', 'N/A')
                    balconyDimDict['BLDG_NAME'] = balconyInfo.get('BLDG_NAME', 'N/A')
                    balconyDimDict['FLOOR_REF'] = balconyInfo.get('FLOOR_REF', 'N/A')
                    balconyDimDict['FLOOR_NAME'] = balconyInfo.get('FLOOR_NAME', 'N/A')
                    balconyDimDict['BALCONY_REF'] = balconyInfo.get('BALCONY_REF', 'N/A')
                    balconyDimDict['BALCONY_LENGTH'] = balconyInfo.get('BALCONY_LENGTH', 'N/A')
                    balconyDimDict['BALCONY_WIDTH'] = balconyInfo.get('BALCONY_WIDTH', 'N/A')

                    js_balconyDimensionsInfoList.append(balconyInfo)

                self.reportExtractor.append({"BALCONY_DIMENSIONS_CHECKS": js_balconyDimensionsInfoList})

    def get_doorStairPassageDistance_details(self):

        doorToStaircaseDistDirectDict = door_to_staircase_distance(self.modelspace_dwg)
        js_doorToStairList = []

        for dkey, distancesStr in doorToStaircaseDistDirectDict.items():
            js_doorDistInfo = dict()
            js_doorDistInfo['PASSAGE_ID'] = dkey
            js_doorDistInfo['DOOR_STAIR_DISTANCES'] = distancesStr
            js_doorToStairList.append(js_doorDistInfo)

        self.reportExtractor.append(
            {"DOOR_STAIR_PASSAGE_DISTANCES": [dict(sorted(dct.items())) for dct in js_doorToStairList]})

    def get_roomventilation_details(self):

        roomDimensionsDirectDict = None
        roomVentilationResponseDict = dict()

        roomDimensionsDirectDict = window_check_util(self.modelspace_dwg)

        if (roomDimensionsDirectDict is not None and roomDimensionsDirectDict.get('RESULTS', 0) != 0):
            roomVentilationResponseDict = roomDimensionsDirectDict.get('RESULTS')

        js_roomVentiInfoList = []

        if (roomVentilationResponseDict is not None):

            for roomItem, ventiDetail in roomVentilationResponseDict.items():

                if type(ventiDetail) == str:
                    details = ventiDetail.split(",")
                    if (len(details) > 0):
                        js_roomVentiInfo = dict()
                        js_roomVentiInfo['ROOM_DWG_REFERENCE'] = str(roomItem)
                        js_roomVentiInfo['ROOM_NAME'] = str(clean_text_mtext_label(details[0]))
                        js_roomVentiInfo['VENTILATION_TYPE'] = str(details[1])
                        js_roomVentiInfo['VENTILATION_AREA'] = str(details[2])
                        js_roomVentiInfoList.append(js_roomVentiInfo)

            self.reportExtractor.append(
                {"ROOM_VENTILATION_INFORMATION": [dict(sorted(dct.items())) for dct in js_roomVentiInfoList]})

    def get_room_information_details(self):
        # # detail
        js_roomInfoList = []

        final_res = getROOMVentilationArea_info(self.modelspace_dwg)

        if final_res["CODE"] == 0:

            js_roomInfoList = final_res.get("RESULTS", [])
        else:

            js_roomErrorList = final_res.get("ERROR", [])

            get_current_logger().warning(js_roomErrorList)

        self.reportExtractor.append({"ROOM_INFORMATION": [dict(sorted(dct.items())) for dct in js_roomInfoList]})

    def get_balcony_information_details(self):

        balconyMainDoorDirectDict = dict()
        try:
            if (self.purposecode not in ['A-2a']):

                if self.runOnlyCombinedUtil == "True":

                    get_current_logger().debug(
                        f'+++++++++++++  Bypassed Due to runOnlyCombinedUtil In Drawing {self.runOnlyCombinedUtil}')
                else:
                    balconyMainDoorDirectDict = check_balcony_maindoor(self.modelspace_dwg)

            else:
                get_current_logger().warning('PURPOSECODE A-2a not caling balcony_maindoor')

        except Exception as ex:

            get_current_logger().error(f'Problem processing check_balcony_maindoor due to  {ex}')

        BALCONY_MIN_REQUIRED_WIDTH = 0.0
        BALCONY_MIN_REQUIRED_LENGTH = 0.0

        js_balconyInfoList = []

        balconyUnitsDict = self.combinedObjects.get(LayerMaster.BALCONY.value).getBaseUnitDict() if self.combinedObjects.get(
            LayerMaster.BALCONY.value, 0) != 0 else {}

        for balconyItem, balconyObj in balconyUnitsDict.items():

            js_balconyInfo = dict()
            mainDoorList = balconyMainDoorDirectDict.get(balconyObj.handle, '-')
            mddoorInPassage = False
            for checkDoor in mainDoorList:
                for hasDoor in checkDoor:
                    js_balconyInfo['MAIN_DOOR_EXISTS'] = str(hasDoor).capitalize()
                    if (hasDoor == True):
                        mddoorInPassage = True
                        statusValue = "Not OK"

            statusValue = "OK"

            bldg_floor = str(balconyObj.parent.replace('|', '-'))

            js_balconyInfo['BUILDNG_FLOOR'] = bldg_floor
            js_balconyInfo['BALCONY_NAME'] = str(balconyObj.name)
            js_balconyInfo['BALCONY_DWG_REFERENCE'] = str(balconyObj.handle)
            js_balconyInfo['BALCONY_AREA'] = str(balconyObj.area)
            js_balconyInfo['BALCONY_MIN_REQUIRED_LENGTH'] = str(BALCONY_MIN_REQUIRED_LENGTH)
            js_balconyInfo['PROPOSED_LENGTH'] = str(balconyObj.length)
            js_balconyInfo['BALCONY_MIN_REQUIRED_WIDTH'] = str(BALCONY_MIN_REQUIRED_WIDTH)
            js_balconyInfo['PROPOSED_WIDTH'] = str(balconyObj.width)
            js_balconyInfo['STATUS'] = statusValue
            js_balconyInfoList.append(js_balconyInfo)

        self.reportExtractor.append({"BALCONY_INFORMATION": [dict(sorted(dct.items())) for dct in js_balconyInfoList]})

    def get_splay_details(self):

        INTERNALROAD_MIN_REQUIRED_WIDTH = 9.00

        mainRoadList = self.combinedObjects.get(LayerMaster.MAINROAD.value).getBaseUnitFinalList() if self.combinedObjects.get(
        LayerMaster.MAINROAD.value, 0) != 0 else []

        radius_by_handle = {
            pt.handle: pt.radius
            for pt in extractSubPlot(
                self.modelspace_dwg, LayerMaster.MAINROAD.value, "LWPOLYLINE", True
            )
        }

        main_road_detail = ""
        # detail
        js_mainRoadInfoList = []
        mainRoadWidthList = []
        total_road_area = 0.0

        for por in mainRoadList:

            js_mainRoadInfo = dict()
            total_road_area += por.area
            startDelim = None
            existing_startDelim = ''

            #
            if (por.name.upper().find('EXISTING') > -1):
                existing_widthOfRoad = float(
                    extract_dimensions_fromtext(str(por.name), existing_startDelim, "EXISTING"))
            else:
                existing_widthOfRoad = 'N/A'

            # proposed width delim
            if (por.name.upper().find('EXISTING') > -1):
                startDelim = 'EXISTING'

            widthOfRoad = float(extract_dimensions_fromtext(str(por.name), startDelim, "PROPOSED"))
            mainRoadWidthList.append(widthOfRoad)
            statusValue = "Not OK"
            if (widthOfRoad >= INTERNALROAD_MIN_REQUIRED_WIDTH):
                statusValue = "OK"
            #
            main_road_detail += str(por.name) + ",-," + str(por.length) + "," + str(
                INTERNALROAD_MIN_REQUIRED_WIDTH) + ", " + \
                                str(widthOfRoad) + "," + str(existing_widthOfRoad) + ", " + str(
                por.area) + ", " + statusValue + "\n"

            js_mainRoadInfo['ROAD_NAME'] = removeSpecialChars(por.name)
            js_mainRoadInfo['ROAD_LENGTH'] = str(por.length)
            js_mainRoadInfo['INTERNALROAD_MIN_REQUIRED_WIDTH'] = str(INTERNALROAD_MIN_REQUIRED_WIDTH)
            js_mainRoadInfo['ROAD_WIDTH'] = str(widthOfRoad)
            js_mainRoadInfo['EXISTING_ROAD_WIDTH'] = str(existing_widthOfRoad)
            js_mainRoadInfo['ROAD_AREA'] = str(por.area)
            js_mainRoadInfo['ROAD_RADIUS'] = str(round(radius_by_handle.get(por.handle, 0.0),2))
            js_mainRoadInfo['STATUS'] = statusValue
            js_mainRoadInfoList.append(js_mainRoadInfo)


        splayPlotList = self.combinedObjects.get(LayerMaster.SPLAY.value).getBaseUnitFinalList() if self.combinedObjects.get(
            LayerMaster.SPLAY.value, 0) != 0 else []

        reservedRoadList = self.combinedObjects.get(
            LayerMaster.ROADWIDENING.value).getBaseUnitFinalList() if self.combinedObjects.get(
            LayerMaster.ROADWIDENING.value, 0) != 0 else []

        internalRoadList = self.combinedObjects.get(
            LayerMaster.INTERNALROAD.value).getBaseUnitFinalList() if self.combinedObjects.get(
            LayerMaster.INTERNALROAD.value, 0) != 0 else []

        totalSplayArea = round(sum(float(splayObj.area) for splayObj in splayPlotList), 2)

        js_splayInfoList = []


        detail_splay = ""
        widthOfRoad = 0
        splay_req_length = 4.5
        splay_req_width = 4.5
        splay_status = "Not OK"
        splay_rule = ""

        for por in splayPlotList:
            js_splayInfo = dict()

            if (por.frontageList is not None and len(por.frontageList) > 0):

                checkMaxFrontag = max(por.frontageList)
                frontage_index = por.frontageList.index(checkMaxFrontag)

                abutting_value = por.abuttingRoadList[frontage_index]
                widthOfRoad = float(extract_dimensions_fromtext(str(abutting_value), None, "M"))

                get_current_logger().debug(f' widthOfRoad  {widthOfRoad}')

                if (widthOfRoad == 0 or "WIDENING" in por.name.upper()):

                    for rl in reservedRoadList:
                        widthOfRoad = rl.width

                ruleResult = callrule('ts-splay', {'roadwidth': widthOfRoad, 'length': por.length, 'width': por.width})
                splayResult = ruleResult["result"]
                get_current_logger().debug(f'rule result  {splayResult}')
                splay_req_length = splayResult['required_length']
                splay_req_width = splayResult['required_width']
                splay_status = splayResult.get('status', 'N/A')
                splay_rule = splayResult.get('zrule', 'N/A')

            totalSplayArea = totalSplayArea + (por.area)

            js_splayInfo['SPLAY_NAME'] = str(por.name)
            js_splayInfo['REFERENCE_ID'] = str(por.handle)

            js_splayInfo['ABUTTING_ROAD_WIDTH'] = str(widthOfRoad)
            js_splayInfo['SPLAY_AREA'] = str(round((por.area), 2))
            js_splayInfo['REQUIRED_MIN_LENGTH'] = str(splay_req_length)
            js_splayInfo['PROPOSED_LENGTH'] = str(por.length)
            js_splayInfo['REQUIRED_MIN_WIDTH'] = str(splay_req_width)
            js_splayInfo['PROPOSED_WIDTH'] = str(por.width)
            js_splayInfo['STATUS'] = str(splay_status)
            js_splayInfoList.append(js_splayInfo)

            detail_splay = detail_splay + " ".join([str(por.name), ",", str(por.handle), ",", \
                                                    str(widthOfRoad), ",", str(round((por.area), 2)), ",", \
                                                    str(splay_req_length), ",", str(por.length), ",", \
                                                    str(splay_req_width), ",", str(por.width), ",", splay_status \
                                                       , "\n"])

        js_splaySummary = dict()

        js_splaySummary['TOTAL_NO_SPLAY_PLOTS'] = str(len(splayPlotList))
        js_splaySummary['TOTAL_SPLAY_AREA'] = str(round(totalSplayArea, 2))
        js_splaySummary['APPLICABLE_RULE'] = splay_rule

        js_internalRoadInfoList = []
        total_road_area = 0.0

        processing_step_name = 'PROPOSED INTERNAL ROAD CHECKS '

        for por in internalRoadList:
            js_internalRoadInfo = dict()
            total_road_area += por.area
            try:
                # disabled on 4/25
                widthOfRoadCheck = -1  # internalRoadDictDirect.get(por.handle,0)

                if (widthOfRoadCheck is None or widthOfRoadCheck <= 0):
                    widthOfRoad = por.width  # round(float(getMinWidthIrregularObjects(por.polygon) ),2)
                else:
                    widthOfRoad = widthOfRoadCheck

            except:

                get_current_logger().error(
                    f' Unable to extract getMindWidthIrregularObjects  of road setting to -1  Step#  {processing_step_name}')
                widthOfRoad = -1

                if (widthOfRoad <= 0.0):
                    widthOfRoad = por.width

            statusValue = "Not OK"
            if (widthOfRoad >= INTERNALROAD_MIN_REQUIRED_WIDTH):
                statusValue = "OK"

            js_internalRoadInfo['ROAD_NAME'] = removeSpecialChars(por.name)
            js_internalRoadInfo['ROAD_LENGTH'] = str(por.length)
            js_internalRoadInfo['INTERNALROAD_MIN_REQUIRED_WIDTH'] = str(INTERNALROAD_MIN_REQUIRED_WIDTH)
            js_internalRoadInfo['ROAD_WIDTH'] = str(widthOfRoad)
            js_internalRoadInfo['ROAD_AREA'] = str(por.area)
            js_internalRoadInfo['STATUS'] = statusValue
            js_internalRoadInfoList.append(js_internalRoadInfo)

        self.reportExtractor.append({"SPLAY_DETAILS": [dict(sorted(dct.items())) for dct in js_splayInfoList]})
        self.reportExtractor.append({"MAIN_ROADS_DETAILS": [dict(sorted(dct.items())) for dct in js_mainRoadInfoList]})

        self.reportExtractor.append(
            {"INTERNAL_ROADS_DETAILS ": [dict(sorted(dct.items())) for dct in js_internalRoadInfoList]})

    def get_accessorylist_details(self):

        accessoryUnitsDict = self.combinedObjects.get(
            LayerMaster.ACCESSORYUSE.value).getBaseUnitDict() if self.combinedObjects.get(LayerMaster.ACCESSORYUSE.value,
                                                                                     0) != 0 else {}

        js_accessoryUseList = []

        for accUseItem, accUseObj in accessoryUnitsDict.items():
            js_accessoryUse = dict()
            # js_accessoryUse['ACCESSORY_NAME'] = accUseObj.name.replace("\\P", " ")
            plain_label=clean_text_mtext_label(accUseObj.name)

            js_accessoryUse['ACCESSORY_NAME'] = plain_label
            if "parapet wall" in accUseObj.name.lower():
                js_accessoryUse['ACCESSORY_AREA'] = extract_dimensions_fromtext(accUseObj.name,None,'h')
            else:
                js_accessoryUse['ACCESSORY_AREA'] = str(accUseObj.area)

            js_accessoryUse['ACCESSORY_WIDTH'] = str(accUseObj.width)
            js_accessoryUseList.append(js_accessoryUse)


        self.reportExtractor.append({"ACCESSORY_LIST": [dict(sorted(dct.items())) for dct in js_accessoryUseList]})

    def get_courtyard_details(self):

        # CourtYardUnitsDict = self.combinedObjects.get(
        #     LayerMaster.COURTYARD.value).getBaseUnitDict() if self.combinedObjects.get(
        #     LayerMaster.COURTYARD.value,
        #     0) != 0 else {}

        # js_accessoryUseList = []
        #
        # for accUseItem, accUseObj in CourtYardUnitsDict.items():
        #     js_accessoryUse = dict()
        #     plain_label = clean_text_mtext_label(accUseObj.name)
        #     js_accessoryUse['COURTYARD_NAME'] = plain_label
        #     js_accessoryUse['COURTYARD_LENGTH'] = str(accUseObj.length)
        #     js_accessoryUse['COURTYARD_WIDTH'] = str(accUseObj.width)
        #     js_accessoryUse['COURTYARD_AREA'] = str(accUseObj.area)
        #     js_accessoryUseList.append(js_accessoryUse)

        lst_courtyard_data=[]

        result=getCourtYard_details(self.modelspace_dwg)

        if result.get("CODE")==0:
            lst_courtyard_data=result.get("RESULTS",[])
            get_current_logger().info(lst_courtyard_data)
        else:
            get_current_logger().error(result.get("ERROR",[]))

        self.reportExtractor.append({"COURTYARD_DETAILS": [dict(sorted(dct.items())) for dct in lst_courtyard_data]})

    def get_acceUsecheck_details(self):

        distribution_transformers_cnt = 0.0
        solar_heater_cnt = 0.0
        waste_water_cnt = 0.0
        septic_tank_cnt = 0.0
        flushing_system=0.0
        solar_photo_volatic=0.0
        accessory_proposed_dict = dict()

        accessoryUnitsDict = self.combinedObjects.get(
            LayerMaster.ACCESSORYUSE.value).getBaseUnitDict() if self.combinedObjects.get(LayerMaster.ACCESSORYUSE.value,
                                                                                     0) != 0 else {}

        for accUseItem, accUseObj in accessoryUnitsDict.items():

            if ("transformer" in accUseObj.name.lower()):
                distribution_transformers_cnt += 1
                accessory_proposed_dict['Distribution Transformers'] = distribution_transformers_cnt

            elif ("solar water heating" in accUseObj.name.lower()):
                solar_heater_cnt += 1
                accessory_proposed_dict['Solar Water Heater System'] = solar_heater_cnt

            elif ("waste" in accUseObj.name.lower()):
                waste_water_cnt += 1
                accessory_proposed_dict['Waste Water Recyling'] = waste_water_cnt

            elif ("septic" in accUseObj.name.lower()):
                septic_tank_cnt += 1
                accessory_proposed_dict['Septic Tank'] = septic_tank_cnt

            elif("flushing" in accUseObj.name.lower()):
                flushing_system+=1
                accessory_proposed_dict['Flushing System'] = flushing_system

            elif("solar photo" in accUseObj.name.lower()):
                solar_photo_volatic+=1
                accessory_proposed_dict['Solar Photo Volatic'] = solar_photo_volatic

        ACCESSORY_DICT_CHECKS = {'Distribution Transformers': 1,
                                 'Solar Water Heater System': 1,
                                 'Waste Water Recyling': 1,
                                 'Septic Tank': 1,
                                 'Flushing System':1,
                                 'Solar Photo Volatic':1,
                                 "Parapet Wall":1
                                 }

        js_accessoryUseChecksInfoList = []
        # @TODO: need to swap with a final list based on type of plan. TBD
        for acc_name, proposedValue in accessory_proposed_dict.items():

            # get the required cnt for type
            min_required_cnt_for_type = ACCESSORY_DICT_CHECKS.get(acc_name, 1)

            if (proposedValue >= min_required_cnt_for_type):
                statusValue = "OK"
            else:
                statusValue = "NOT OK"

            js_accessoryUseChecksInfo = dict()
            plain_label = clean_text_mtext_label(acc_name)
            js_accessoryUseChecksInfo['ACCESSORY_NAME'] = plain_label
            js_accessoryUseChecksInfo['MIN_REQUIRED_COUNT'] = str(min_required_cnt_for_type)
            js_accessoryUseChecksInfo['PROPOSED_COUNT'] = str(proposedValue)
            js_accessoryUseChecksInfo['STATUS'] = statusValue
            js_accessoryUseChecksInfoList.append(js_accessoryUseChecksInfo)

        self.reportExtractor.append(
            {"ACCESSORY_USE_CHECKS": [dict(sorted(dct.items())) for dct in js_accessoryUseChecksInfoList]})

    def get_acceUsespecific_details(self):

        js_accessoryUseSpecificList = []

        accessory_use_dist_reponse = get_accessory_septic_sewage_transformer_distances(self.modelspace_dwg)

        if (accessory_use_dist_reponse is not None):
            access_distances_DictDirect = accessory_use_dist_reponse.get('ACCESSORYUSE_DISTANCE_FROM_PLOT_RESPONSE', {})
        else:
            access_distances_DictDirect = dict()

        for accUseKey, accUseResponse in access_distances_DictDirect.items():
            accTempDict = dict()
            statusValue_accessory = 'OK'
            get_current_logger().debug(f' response -  {accUseResponse}')
            direction, distanceFromPlot = accUseResponse
            accTempDict['ACCESSORY_NAME'] = accUseKey
            accTempDict['ACCESSORY_LOCATION'] = direction
            accTempDict['DISTANCE_FROM_PLOT'] = str(distanceFromPlot)
            accTempDict['STATUS'] = statusValue_accessory

            js_accessoryUseSpecificList.append(accTempDict)

        self.reportExtractor.append(
            {"ACCESSORY_USE_SPECIFIC_CHECKS": [dict(sorted(dct.items())) for dct in js_accessoryUseSpecificList]})

    def get_stairCasewalking_details(self):

        try:
            stairDistanceDictResponse = get_travel_distance(self.modelspace_dwg)
        except Exception as stairExcp:
            get_current_logger().error(f'Problem extracting stair distances for Request# {stairExcp}')

        STAIRCASE_DISTANCE_THRESHOLD_MAX_VALUE = 30
        js_stairsWalkingDistanceList = []
        for stairBuildingKey, buildObject in stairDistanceDictResponse.items():
            #
            refId = stairBuildingKey

            for bldNameKey, bldDetailsObj in buildObject.items():

                for floorKey, floorDictObj in bldDetailsObj.items():

                    for floorName in floorDictObj:

                        floordistList = floorDictObj[floorName]

                        if (len(floordistList) > 0):
                            minValueProposed = min(floordistList)
                            maxValueProposed = max(floordistList)
                            if (float(minValueProposed) < float(STAIRCASE_DISTANCE_THRESHOLD_MAX_VALUE) and float(
                                    maxValueProposed) < float(STAIRCASE_DISTANCE_THRESHOLD_MAX_VALUE)):
                                statusValue = "OK"
                            else:
                                statusValue = "Not OK"
                        else:
                            minValueProposed = 0.0
                            maxValueProposed = 0.0
                            statusValue = "Not OK (Not able to extract distances. Possible Drafting issue)"
                        js_stairsWalkingDistDict = dict()
                        js_stairsWalkingDistDict['BUILDING_NAME'] = str(bldNameKey)
                        js_stairsWalkingDistDict['REFERENCE_ID'] = str(refId)
                        js_stairsWalkingDistDict['FLOOR_NAME'] = str(floorName)
                        js_stairsWalkingDistDict['PERMISSIBLE_MAX_STAIR_WALK_DISTANCE'] = str(
                            STAIRCASE_DISTANCE_THRESHOLD_MAX_VALUE)
                        js_stairsWalkingDistDict['PROPOSED_MIN_STAIR_WALK_DISTANCE'] = str(minValueProposed)
                        js_stairsWalkingDistDict['PROPOSED_MAX_STAIR_WALK_DISTANCE'] = str(maxValueProposed)
                        js_stairsWalkingDistDict['STATUS'] = str(statusValue)
                        js_stairsWalkingDistanceList.append(js_stairsWalkingDistDict)

        self.reportExtractor.append(
            {"STAIRS_WALKING_DISTANCE_CHECKS": [dict(sorted(dct.items())) for dct in js_stairsWalkingDistanceList]})

    def get_buaBeforeCondetails(self):

        buaBeforeConPlotList = self.combinedObjects.get(
            LayerMaster.BUA_BEFORE_CONCESSION.value).getBaseUnitFinalList() if self.combinedObjects.get(
            LayerMaster.BUA_BEFORE_CONCESSION.value, 0) != 0 else []

        js_buaBeforeConPlotList = []
        for sno, buaBeforeObj in enumerate(buaBeforeConPlotList):
            js_buaBeforeConInfo = dict()
            js_buaBeforeConInfo['SNO'] = str(sno + 1)
            js_buaBeforeConInfo['BUA_BEFORE_CONCESSION_NAME'] = str(buaBeforeObj.name)

            js_buaBeforeConInfo['BUA_BEFORE_CONCESSION_AREA'] = str(round(buaBeforeObj.area, 2))
            js_buaBeforeConPlotList.append(js_buaBeforeConInfo)

        self.reportExtractor.append({"BUA_BEFORE_CONCESSION": js_buaBeforeConPlotList})

    def get_compoundwallcheck_details(self):

        # compoundWallDict = self.combinedObjects.get(LayerMaster.COMPOUNDWALL.value).getBaseUnitDict() if self.combinedObjects.get(
        #     LayerMaster.COMPOUNDWALL.value, 0) != 0 else {}
        #
        # js_compoundWallInfoList = []
        # grill_height=[cWallObj.height for cWallObj in  compoundWallDict.values() if "grill" in cWallObj.name.lower()]
        #
        # for cWallItem, cWallObj in compoundWallDict.items():
        #
        #     if "wall" in cWallObj.name.lower():
        #         js_compoundWallInfo = dict()
        #         js_compoundWallInfo['COMPOUND_WALL_NAME'] = cWallObj.name
        #         js_compoundWallInfo['C_WALL_HEIGHT'] = str(cWallObj.height)
        #         js_compoundWallInfo['C_WALL_LENGTH'] = str(cWallObj.length)
        #         js_compoundWallInfo['GRILL_HEIGHT'] = str(min(grill_height)) if len(grill_height)>0 else "0.0"
        #
        #         js_compoundWallInfoList.append(js_compoundWallInfo)
        js_compoundWallInfoList=[]
        js_compoundWallInfoRes= getCompoundWallDetails(self.modelspace_dwg)
        if js_compoundWallInfoRes.get("CODE")==0:
            js_compoundWallInfoList=js_compoundWallInfoRes.get("RESULTS",[])
            get_current_logger().info("Compound Wall Details:%s",js_compoundWallInfoList)
        else:
            get_current_logger().error("Problem Processing Compound Wall Details %s",js_compoundWallInfoRes.get("Errors"))

        self.reportExtractor.append({"COMPOUND_WALL_CHECKS": [dict(sorted(dct.items())) for dct in js_compoundWallInfoList]})

    # def get_combineutility_details(self):
    #
    #     get_current_logger().info(
    #         f' Checking Flag  RunOnlyCombinedBuildingUtils runOnlyCombinedUtil Flag is :: {self.runOnlyCombinedUtil}')
    #     combinedBuildingUtilityResult = dict()
    #
    #     if self.runOnlyCombinedUtil == "True":
    #         server_logger.info('Calling  RunOnlyCombinedBuildingUtils ')
    #         combinedBuildingUtilityResponse = runCombinedBuildingUtility(self.modelspace_dwg, self.gatedCommunityFlag)
    #
    #         combinedBuildingReturnCode = combinedBuildingUtilityResponse.get('CODE', 100)
    #         server_logger.info(f"combinedBuildingReturnCode {combinedBuildingReturnCode}")
    #
    #         if (combinedBuildingReturnCode == 0):
    #             combinedBuildingUtilityResult = combinedBuildingUtilityResponse.get(
    #                 'COMBINED_BUILDING_UTIL_RESULTS', {})
    #
    #         else:
    #             combinedBuildingUtilErrors = combinedBuildingUtilityResponse.get('ERROR', [])
    #
    #             combinedBuildingUtilityResult = {"COMBINED_BUILDING_UTIL_RESULTS", str(combinedBuildingUtilErrors)}
    #
    #         server_logger.info('Completed  RunOnlyCombinedBuildingUtils  ')
    #     else:
    #         server_logger.info('Not Calling RunOnlyCombinedBuildingUtils ')
    #         server_logger.info('Completed  RunOnlyCombinedBuildingUtils ')
    #
    #
    #     if self.runOnlyCombinedUtil == "True":
    #
    #         dictObjectList = ['BALCONY_LENGTH_WIDTH', "STAIR_CASE_DETAILS", 'STAIRCASE_DATA',
    #                           # 'BLDG_FLOORWISE_ACC_VOID_AREA_BY_BUA_TYPE',
    #                           # 'CELLAR_PLINTH_FOR_SETBACKS',
    #                           'COMMONFLOOR_SETBACKS_FOR_PLOT', 'PLOT_LINE_ENTRANCE_GATE_RESULT',
    #                           'WINDOW_IN_ROOM_CHECKS_RESULT', 'RAMPLENGTH_BUILDINGHEIGHT',
    #                           'ACCESSORY_USE_AREA_IN_PARKING',
    #                           'MORTGAGE_FLOOR_SUMMARY_NEW', 'SEPTIC_TANK_DIST',
    #                           'PODIUM_REGULAR_SETBACKS', 'PODIUM_ARC_RADIUS', 'CELLAR_SETBACKS_FOR_BUILDING',
    #                           'VENTILATION_WIDTH_AREA',
    #                           'TRANSFER_OF_SETBACKS', 'PODIUM_SETBACKS', 'SEGMENT_WISE_FLOOR_SETBACKS_RESULT',
    #                           'GATED_COMMUNITY_DEDUCTIONS', 'MULTIPLE_OCCUPANCY_BUA',
    #                           'BUILDING_FLOOR_TOTAL_HEIGHT_SUMMARY', 'PARKING_SLOT_DETAILS', 'PLOT_DETAILS',
    #                           'ARCH_PROJECTION_DATA']
    #
    #         stringObjectList = ['DRAWING_COMMONLAYER_VALIDATIONS', 'DRAWING_DEVIATIONS']
    #
    #         #
    #         server_logger.info(
    #             "++++++++++++++++++++++++++++ Building Custom Response +++++++++++++++++++++++++++++++++++++")
    #         for commonKeyName, commonKeyValue in combinedBuildingUtilityResult.items():
    #             server_logger.debug(
    #                 f'Building Custom Response processing commonKeyName  {commonKeyName}  type  {type(commonKeyValue)}')
    #
    #             if commonKeyName in dictObjectList:
    #
    #                 self.reportExtractor.append({"COMBINED_BUILDING_UTILITY_RESULT_" + commonKeyName: commonKeyValue})
    #
    #             elif commonKeyName in stringObjectList:
    #                 server_logger.debug(f'Response type is List of String : {commonKeyName}  to be implemented ')
    #
    #                 self.reportExtractor.append({"COMBINED_BUILDING_UTILITY_RESULT_" + commonKeyName: commonKeyValue})
    #
    #             else:
    #                 server_logger.debug(f'Found unknown Key  {commonKeyName}')
    #         #
    #         server_logger.info(
    #             "++++++++++++++++++++++++++++ Building Custom Response Completed +++++++++++++++++++++++++++++++++++++")
    #
    #     else:
    #
    #         self.reportExtractor.append({"COMBINED_BUILDING_UTILITY_RESULT": {}})

    def get_CommonLayerValidation_details(self):

        checkCommonLayersInDrawingResponseDict = dict()
        # server_logger.info('Calling CommonValidationLayer checks In Drawing ')
        # if runOnlyCombinedUtil == "True":
        #     server_logger.info(f'Bypassed Due to runOnlyCombinedUtil In Drawing {runOnlyCombinedUtil}')
        # else:
        #     # checkCommonLayersInDrawingResponseDict = checkCommonLayersInBuildings(modelspace_dwg)
        # server_logger.info('Completed  CommonValidationLayer checks In Drawing ')

        self.reportExtractor.append({"DRAWING_COMMONLAYER_VALIDATIONS": checkCommonLayersInDrawingResponseDict})

    def get_drawingLayers_details(self):

        self.reportExtractor.append({"DRAWING_LAYERS": dict(sorted(self.combinedObjects['dwg_layers'].items()))})


    # def execute_step(self, step_no,total_step, step_name, step_function):
    #
    #     try:
    #         start_time = time.time()
    #
    #         server_logger.info("=" * 80)
    #         server_logger.info(f"Step{step_no}/{total_step} STARTED : {step_name}")
    #         server_logger.info("=" * 80)
    #
    #         processing_steps_dict = dict()
    #         processing_steps_dict["CurrentStep"] = f"{step_name} Processing ..."
    #         processing_steps_dict["Progress"] = self.progress
    #         processing_steps_dict["Steps"] = f"{step_no}/{total_step}"
    #
    #         self.status_dict["Step_data"] = processing_steps_dict
    #         send_status(self.req_id, self.status_dict,self.requesttimeobj)
    #
    #         time.sleep(1)
    #
    #         step_function()
    #
    #         self.progress = int(
    #             (step_no / total_step) * 100
    #         )
    #
    #         main_completed_progress = (
    #                 self.main2min_progress +
    #                 int(
    #                     (step_no / total_step)
    #                     * (
    #                             self.main2max_progress
    #                             - self.main2min_progress
    #                     )
    #                 )
    #         )
    #
    #         elapsed = round(time.time() - start_time, 2)
    #         completed_steps_dict = dict()
    #         completed_steps_dict["Steps"] = f"{step_no}/{total_step}"
    #         completed_steps_dict["CurrentStep"] = f"{step_name} Completed."
    #         completed_steps_dict["TotalTime"] = f"{elapsed} sec"
    #         completed_steps_dict["Progress"] = self.progress
    #
    #         self.status_dict["Step_data"] = completed_steps_dict
    #         self.status_dict["Progress"] = main_completed_progress
    #
    #         send_status(self.req_id, self.status_dict,self.requesttimeobj)
    #         server_logger.info(
    #             f"Step{step_no}/{total_step} COMPLETED : {step_name} | Time Taken : {elapsed} sec"
    #         )
    #         time.sleep(0.5)
    #
    #     except Exception as e:
    #
    #         elapsed = round(time.time() - start_time, 2)
    #
    #         error_msg = {
    #             "step": step_no,
    #             "step_name": step_name,
    #             "error": str(e),
    #             "time_taken": elapsed
    #         }
    #
    #         self.errors.append(error_msg)
    #
    #         server_logger.info("=" * 80)
    #         server_logger.info(f"{step_no} FAILED : {step_name}")
    #         server_logger.info(f"ERROR : {str(e)}")
    #         server_logger.info(traceback.format_exc())
    #         server_logger.info("=" * 80)
    #
    #         self.status_dict["Status"] = "Failed"
    #         self.status_dict["Progress"] = main_completed_progress
    #         failed_steps_dict=dict()
    #         failed_steps_dict["CurrentStep"] = f"{step_name} Processing ..."
    #         failed_steps_dict["Progress"] = self.progress
    #         failed_steps_dict["Steps"] = f"{step_no}/{total_step}"
    #         self.status_dict["Step_data"] = failed_steps_dict

    def execute_step(
            self,
            step_no,
            total_step,
            step_name,
            step_function
    ):

        try:

            start_time = time.time()

            get_current_logger().info("=" * 80)
            get_current_logger().info(
                f"Step{step_no}/{total_step} STARTED : {step_name}"
            )
            get_current_logger().info("=" * 80)

            # -----------------------------------
            # PROCESSING STATUS
            # -----------------------------------

            processing_steps_dict = dict()

            processing_steps_dict["CurrentStep"] = (
                f"{step_name} Processing ..."
            )

            processing_steps_dict["Progress"] = (
                self.progress
            )

            processing_steps_dict["Steps"] = (
                f"{step_no}/{total_step}"
            )

            processing_steps_dict["TotalTime"] = (
                "0.0 sec"
            )

            self.status_dict["Status"] = (
                "Processing ..."
            )

            self.status_dict["Step_data"] = (
                processing_steps_dict
            )

            # send_status(
            #     self.req_id,
            #     self.status_dict,
            #     self.requesttimeobj
            # )

            # IMPORTANT
            # Gives frontend/browser render time
            # time.sleep(1)

            # -----------------------------------
            # EXECUTE STEP FUNCTION
            # -----------------------------------

            step_function()

            # -----------------------------------
            # PROGRESS CALCULATION
            # -----------------------------------

            self.progress = int(
                (step_no / total_step) * 100
            )

            main_completed_progress = (
                    self.main2min_progress +
                    int(
                        (step_no / total_step)
                        * (
                                self.main2max_progress
                                - self.main2min_progress
                        )
                    )
            )

            elapsed = round(
                time.time() - start_time,
                2
            )

            # -----------------------------------
            # COMPLETED STATUS
            # -----------------------------------

            completed_steps_dict = dict()

            completed_steps_dict["CurrentStep"] = (
                f"{step_name} Completed."
            )

            completed_steps_dict["Steps"] = (
                f"{step_no}/{total_step}"
            )

            completed_steps_dict["TotalTime"] = (
                f"{elapsed} sec"
            )

            completed_steps_dict["Progress"] = (
                self.progress
            )

            self.status_dict["Status"] = (
                "Processing ..."
            )

            self.status_dict["Step_data"] = (
                completed_steps_dict
            )

            self.status_dict["Progress"] = (
                main_completed_progress
            )

            # send_status(
            #     self.req_id,
            #     self.status_dict,
            #     self.requesttimeobj
            # )

            get_current_logger().info(
                f"Step{step_no}/{total_step} "
                f"COMPLETED : {step_name} "
                f"| Time Taken : {elapsed} sec"
            )

            # time.sleep(0.5)

        except Exception as e:

            elapsed = round(
                time.time() - start_time,
                2
            )

            error_msg = {
                "step": step_no,
                "step_name": step_name,
                "error": str(e),
                "time_taken": elapsed
            }

            self.errors.append(error_msg)

            get_current_logger().info("=" * 80)
            get_current_logger().info(
                f"{step_no} FAILED : {step_name}"
            )
            get_current_logger().info(
                f"ERROR : {str(e)}"
            )
            get_current_logger().info(
                traceback.format_exc()
            )
            get_current_logger().info("=" * 80)

            # -----------------------------------
            # FAILED STATUS
            # -----------------------------------

            failed_steps_dict = dict()

            failed_steps_dict["CurrentStep"] = (
                f"{step_name} Failed."
            )

            failed_steps_dict["Progress"] = (
                self.progress
            )

            failed_steps_dict["Steps"] = (
                f"{step_no}/{total_step}"
            )

            failed_steps_dict["TotalTime"] = (
                f"{elapsed} sec"
            )

            self.status_dict["Status"] = (
                "Failed"
            )

            self.status_dict["Progress"] = (
                self.progress
            )

            self.status_dict["Step_data"] = (
                failed_steps_dict
            )

            self.status_dict["Error"] = (
                    "Problem Generating Report Data")

            # send_status(
            #     self.req_id,
            #     self.status_dict,
            #     self.requesttimeobj
            # )

            raise

    def getReport_details(self):

        get_current_logger().info(f"Processing Generating Report {self.filename} of That Building.")
        if (self.filename is None or self.combinedObjects is None):
            get_current_logger().info(f"Invalid Input. Require a file name")
            self.gen_report_resp['responseCode'] = FAIL_CODE
            self.gen_report_resp['error_category'] = "MISSING LAYERS "
            self.gen_report_resp['errors'] = "Invalid Input. Require a file name"
            self.gen_report_resp['planType'] = 'Building'
            self.gen_report_resp['dwgExtract'] = []
            return self.gen_report_resp

        get_current_logger().info(f"inputs keys {str(self.combinedObjects.keys())}")

        steps=[
            ("Nala Area Details", self.get_nala_area_details),
            ("Request Summary",self.get_summary_details),
            ("Project Summary",self.get_project_details),
            ("ProposedWork Dimentions", self.get_propwork_dim_details),
            ("NetPlot Dimentions", self.get_netplot_dim_details),
            ("Area Summary Details", self.get_area_summary_details),
            ("Existing Structure Details", self.get_existingsturcture_details),
            ("Tot Summary Details", self.get_tot_summary_details),
            ("Plinth Area Details", self.get_plinthArea_details),
            ("Tot Details", self.get_tot_details),
            ("Green Strip Wall Details", self.get_greenstripCwall_details),
            ("Building Summary Details", self.get_building_summary_dertals),
            ("FloorInSection Details", self.get_floorinsection_details),
            ("Building Height Details", self.get_buildingheight_details),
            ("GroundLevel Details", self.get_groundleve_details),
            ("Mortgage Floor Summary Details", self.get_mortgagefloor_summary_details),
            ("Mortgage Area Summary Details", self.get_mortgagearea_summary_details),
            ("Mortgage Carpet Area Details", self.get_mortgagecarpetarea_details),
            ("BuiltUp Area Details", self.get_bua_area_details),
            ("Net BuiltUp Area News Details", self.get_netbuiltup_area_new),
            ("Net BuiltUp Area Details", self.get_netbuiltup_area_detail),
            ("Cellar Dimention Details", self.get_cellar_dim_details),
            ("Lift Details", self.get_lift_info_details),
            ("Building to Building Distance Details", self.get_bldg2bldgdist_details),
            ("Accessory Plot Setbacks Details", self.get_acce2plot_setback_details),
            ("Common Floor Setbacks Details", self.get_commonfloor_setbacks_details),
            ("Transfer Of Setabcks Details", self.get_transfersetbacks_details),
            ("Floor Wise Setbacks", self.get_floorwisesetabcks_details),
            ("Cellar Setbacks/Plinth Details", self.get_cellarsetbackAndPlinth_details),
            ("Window Passage Details", self.get_windowspassage_details),
            ("Parking Details", self.get_parking_details),
            ("Ramp Details", self.get_ramp_details),
            ("Gated Community Setbacks",self.get_gatedcommunity_setbacks),
        ]

        if (self.purposecode in ['S-6']):

            steps.append(("Podium Setbacks",self.get_podium_setbacks_details))
        else:

            if (self.authority is not None and self.authority.upper() in ['GHMC'] and self.purposecode not in ['A-2a']):

                steps.append(("GHMC Setbacks",self.get_ghmc_setbacks_details))
            else:

                steps.append(("Regular Setbacks", self.get_regular_setbacks_details))


        steps.append(("Room Dimentions", self.get_room_dimentions))

        steps.append(("Balcony Dimentions Details", self.get_balcony_dimention_details))

        steps.append(("DOOR TO STAIRCASE/PASSAGES DISTANCES", self.get_doorStairPassageDistance_details))

        steps.append(("Room Ventilation Details", self.get_roomventilation_details))

        steps.append(("Room Information Details", self.get_room_information_details))

        steps.append(("Balcony Information Details", self.get_balcony_information_details))

        steps.append(("Splay Details", self.get_splay_details))

        steps.append(("Accessory List Details", self.get_accessorylist_details))

        steps.append(("Accessory Use Check Details", self.get_acceUsecheck_details))

        steps.append(("Accessory Use Specific Details", self.get_acceUsespecific_details))

        steps.append(("Accessory Area In Parking", self.get_accessoryParking_details))

        steps.append(("Court Yard Details", self.get_courtyard_details))

        steps.append(("StairCase Walking Details", self.get_stairCasewalking_details))

        steps.append(("BUA Concession Details", self.get_buaBeforeCondetails))

        steps.append(("Compound Wall Details", self.get_compoundwallcheck_details))

        if (self.purposecode == 'A-2a' and (self.runOnlyCombinedUtil == False or self.runOnlyCombinedUtil == 'False')):
            steps.append(("Indiv Subplot Details",self.get_indivsubplot_setbacks_details))
        else:
            steps.append(("Setbacks For Plot Details",self.get_setbackForPlot_details))

        if (self.purposecode == 'S-6' and (self.runOnlyCombinedUtil == False or self.runOnlyCombinedUtil == 'False')):

            steps.append(("Podium Setbacks For Plot Details",self.get_podiumsetbacksForPlot_details))

        steps.append(("Combined Utility Details",self.get_combine_utils_details))

        steps.append(("Drawing Validation Layers",self.get_CommonLayerValidation_details))

        steps.append(("Deviation Details",self.get_deviation_details),)

        steps.append(("Drawing Layers Details",self.get_drawingLayers_details))

        total_steps = len(steps)

        get_current_logger().info("=" * 100)
        get_current_logger().info("BUILDING PROCESS STARTED")
        get_current_logger().info("=" * 100)

        for index, (step_name, step_function) in enumerate(steps, start=1):
            self.execute_step(
                index,
                total_steps,
                step_name,
                step_function
            )

        self.reportExtractor.append({"DRAWING_WARNINGS": self.warnings})

        self.gen_report_resp["responseCode"] = SUCCESS_CODE
        self.gen_report_resp["dwgExtract"] = self.reportExtractor

        return self.gen_report_resp


class ProcessBuilding:

    def __init__(self,dxf_file,request_id,file_name,dxf_dir,layerDict,layerTypeDict,dwg_dir,request_params,status_dict:dict,requesttimeobj):
        self.dxf_file = dxf_file
        self.modelspace = dxf_file.modelspace()
        self.request_id = request_id
        self.file_name = file_name
        self.dxf_dir= dxf_dir
        self.request_params= request_params

        self.gatedCommunityFlag = request_params.get('isGatedCommunity', False)
        self.runOnlyCombinedUtil = request_params.get('runOnlyCombinedUtil', False)
        self.responsedict=dict()
        self.masterFloorDict = dict()
        self.masterBuildingDict = dict()
        self.combinedObjects = dict()
        self.textElementsResultsDict=dict()
        self.errors=[]
        self.warnings=[]
        self.coverageAreaPercent = 0.0
        self.resiObjList=[]
        self.mainRoadList=[]
        self.internalRoadList=[]
        self.dwg_dir=dwg_dir
        self.layerDict=layerDict
        self.layerTypeDict=layerTypeDict
        self.status_dict=status_dict
        self.progress = 0
        self.main1min_progress = 20
        self.main1max_progress = 40
        self.pipeline_start_time = time.time()
        self.requesttimeobj=requesttimeobj

    def analyzeAndextact(self):

        for layer in self.dxf_file.layers:
            self.layerDict[layer.dxf.name] = str(layer.is_on())

    def check_required_layers(self):
        layers_check = []

        for opLay in MANDATORY_LAYERS_FOR_PLAN_TYPE['Building_Layout']:

            if (opLay not in self.layerDict):
                layers_check.append(
                    "Layer " + opLay + " is required but is not found. Layer names are case sensitive.")

            elif (self.layerDict.get(opLay, 'False') == 'False'):

                layers_check.append(
                    " Layer " + opLay + " should be Visible but is " + self.layerDict.get(opLay, 'False'))

        return layers_check

    def get_building_details(self):

        pop_msg_area = LayerMaster.BUILDINGNAME.value  #
        pop_msg_refid = "2.0"

        # refactor-1
        buildingObjInst = ObjectByType(pop_msg_area)
        buildingUnitsDict = buildingObjInst.getBaseUnitDict()

        buildingUnits = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, True, False)

        buildingUnitNames = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)

        # refactor-2
        buildingObjInst.setBaseList(buildingUnits)
        buildingObjInst.setBaseUnitNames(buildingUnitNames)

        pop_dict_msg = populateBldgListObj(self.masterFloorDict, self.masterBuildingDict, pop_msg_area, None, None,
                                           buildingUnits,
                                           buildingUnitNames, buildingUnitsDict, True)

        resultCode = pop_dict_msg.get("result")
        if pop_dict_msg == None or resultCode == "error":
            get_current_logger().error(
                f"{pop_msg_refid} + Error processing [ {pop_msg_area} ] Area Section Return is {pop_dict_msg}")

        else:
            if (resultCode == "OK"):

                resiObjList = pop_dict_msg.get("data")

                # # refactor-3
                masterFloorTemp = pop_dict_msg.get("MASTERFLOORDICTKEY", None)

                buildingObjInst.setBaseUnitDict(resiObjList)

                # add to swap masterfloor/bldgDict
                self.masterFloorDict = masterFloorTemp if (masterFloorTemp is not None) else self.masterFloorDict

                self.combinedObjects[pop_msg_area] = buildingObjInst

    def get_floor_details(self):
        ### FLOORS
        pop_msg_area = LayerMaster.FLOOR.value  # "_Floor"
        pop_msg_refid = "2.1"

        # refactor-1
        flrObjInst = ObjectByType(pop_msg_area)
        floorsDict = flrObjInst.getBaseUnitDict()

        floorsList = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, True, False)

        floorsUnitNames = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)

        # refactor-2
        flrObjInst.setBaseList(floorsList)
        flrObjInst.setBaseUnitNames(floorsUnitNames)

        pop_dict_msg = populateBldgListObj(self.masterFloorDict, self.masterBuildingDict, pop_msg_area, None, None,
                                           floorsList,
                                           floorsUnitNames, floorsDict, True)

        resultCode = pop_dict_msg.get("result")
        if pop_dict_msg == None or resultCode == "error":
            get_current_logger().error(
                f"{pop_msg_refid} Error processing [ {pop_msg_area} ] Area Section Return is {pop_dict_msg}")
        else:
            if (resultCode == "OK"):

                resiObjList = pop_dict_msg.get("data")

                # refactor-3
                masterFloorTemp = pop_dict_msg.get("MASTERFLOORDICTKEY", None)
                masterBldgTemp = pop_dict_msg.get("MASTERBUILDINGDICTKEY", None)
                flrObjInst.setBaseUnitDict(resiObjList)

                # add to swap masterfloor/bldgDict
                self.masterFloorDict = masterFloorTemp if (masterFloorTemp is not None) else self.masterFloorDict
                self.masterBuildingDict = masterBldgTemp if (masterBldgTemp is not None) else self.masterBuildingDict
                # combined objects
                self.combinedObjects[pop_msg_area] = flrObjInst

    def get_carpetarea_details(self):
        ## CARPET AREA
        pop_msg_area = LayerMaster.CARPETAREA.value  #
        pop_msg_refid = "2.2"

        # refactor-1
        carptObjInst = ObjectByType(pop_msg_area)
        dwellUnitsDict = carptObjInst.getBaseUnitDict()

        dwellUnits = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, True, False)

        dwellUnitNames = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)

        # refactor-2
        carptObjInst.setBaseList(dwellUnits)
        carptObjInst.setBaseUnitNames(dwellUnitNames)

        pop_dict_msg = populateBldgListObj(self.masterFloorDict, self.masterBuildingDict, pop_msg_area, None, None,
                                           dwellUnits,
                                           dwellUnitNames, dwellUnitsDict, True)

        resultCode = pop_dict_msg.get("result")
        if pop_dict_msg == None or resultCode == "error":
            get_current_logger().error(
                f"{pop_msg_refid} Error processing [ {pop_msg_area} ] Area Section Return is {pop_dict_msg}")
        else:
            if (resultCode == "OK"):

                resiObjList = pop_dict_msg.get("data")

                # refactor-3
                masterFloorTemp = pop_dict_msg.get("MASTERFLOORDICTKEY", None)
                masterBldgTemp = pop_dict_msg.get("MASTERBUILDINGDICTKEY", None)
                carptObjInst.setBaseUnitDict(resiObjList)

                # add to swap masterfloor/bldgDict
                self.masterFloorDict = masterFloorTemp if (masterFloorTemp is not None) else self.masterFloorDict
                self.masterBuildingDict = masterBldgTemp if (masterBldgTemp is not None) else self.masterBuildingDict

                self.combinedObjects[pop_msg_area] = carptObjInst

    def get_room_details(self):
        pop_msg_area = LayerMaster.ROOM.value  #
        pop_msg_refid = "2.2.1"

        # refactor-1
        roomObjInst = ObjectByType(pop_msg_area)
        roomUnitsDict = roomObjInst.getBaseUnitDict()

        roomUnits = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, True, False)

        roomUnitNames = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)

        # refactor-2
        roomObjInst.setBaseList(roomUnits)
        roomObjInst.setBaseUnitNames(roomUnitNames)

        if (len(roomUnits) < 2000):
            pop_dict_msg = populateBldgListObj(self.masterFloorDict, self.masterBuildingDict, pop_msg_area, None, None,
                                               roomUnits,
                                               roomUnitNames, roomUnitsDict, True)


            resultCode = "error"

            if pop_dict_msg != None:
                resultCode = pop_dict_msg.get("result", "error")

            if pop_dict_msg == None or resultCode == "error":
                get_current_logger().error(
                    f"{pop_msg_refid} Error processing [ {pop_msg_area} ] Area Section Return is {pop_dict_msg}")
            else:
                if (resultCode == "OK"):
                    get_current_logger().info(f"{pop_msg_refid} Section [ {pop_msg_area} ] Area : Completed ")

                    resiObjList = pop_dict_msg.get("data")

                    # refactor-3
                    masterFloorTemp = pop_dict_msg.get("MASTERFLOORDICTKEY", None)
                    masterBldgTemp = pop_dict_msg.get("MASTERBUILDINGDICTKEY", None)
                    roomObjInst.setBaseUnitDict(resiObjList)

                    # add to swap masterfloor/bldgDict
                    self.masterFloorDict = masterFloorTemp if (masterFloorTemp is not None) else self.masterFloorDict
                    self.masterBuildingDict = masterBldgTemp if (masterBldgTemp is not None) else self.masterBuildingDict
                    # combined objects
                    self.combinedObjects[pop_msg_area] = roomObjInst

        else:
            get_current_logger().warning(
                f"{pop_msg_refid} Section [ {pop_msg_area} ] Area : Skipped  due to count > threshold of 2000 ")

    def get_mortgagearea_details(self):

        pop_msg_area = LayerMaster.MORTGAGEAREA.value  #
        pop_msg_refid = "2.3"

        # refactor-1
        mortgObjInst = ObjectByType(pop_msg_area)
        mortgagedUnitsDict = mortgObjInst.getBaseUnitDict()

        mortgagedUnits = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, True, False)

        mortgagedUnitNames = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)

        # refactor-2
        mortgObjInst.setBaseList(mortgagedUnits)
        mortgObjInst.setBaseUnitNames(mortgagedUnitNames)

        pop_dict_msg = populateBldgListObj(self.masterFloorDict, self.masterBuildingDict, pop_msg_area, None, None,
                                           mortgagedUnits,
                                           mortgagedUnitNames, mortgagedUnitsDict, True)

        resultCode = pop_dict_msg.get("result")
        if pop_dict_msg == None or resultCode == "error":
            get_current_logger().error(
                f"{pop_msg_refid} Error processing [ {pop_msg_area} ] Area Section Return is {pop_dict_msg}")

        else:
            if (resultCode == "OK"):

                resiObjList = pop_dict_msg.get("data")
                # refactor-3
                masterFloorTemp = pop_dict_msg.get("MASTERFLOORDICTKEY", None)
                masterBldgTemp = pop_dict_msg.get("MASTERBUILDINGDICTKEY", None)
                mortgObjInst.setBaseUnitDict(resiObjList)

                # add to swap masterfloor/bldgDict
                self.masterFloorDict = masterFloorTemp if (masterFloorTemp is not None) else self.masterFloorDict
                self.masterBuildingDict = masterBldgTemp if (masterBldgTemp is not None) else self.masterBuildingDict
                # combined objects
                self.combinedObjects[pop_msg_area] = mortgObjInst

    def get_accessoryUsedetails(self):

        ## ACCESSORYUSE AREA - Deductions
        pop_msg_area = LayerMaster.ACCESSORYUSE.value

        pop_msg_refid = "2.3a"

        # refactor-1
        accessoryObjInst = ObjectByType(pop_msg_area)
        accessoryUnitsDict = accessoryObjInst.getBaseUnitDict()

        accessoryUnits = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, True, False)

        accessoryUnitNames = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)

        # refactor-2
        accessoryObjInst.setBaseList(accessoryUnits)
        accessoryObjInst.setBaseUnitNames(accessoryUnitNames)

        pop_dict_msg = populateBldgListObj(self.masterFloorDict, self.masterBuildingDict, pop_msg_area, None, None,
                                           accessoryUnits,
                                           accessoryUnitNames, accessoryUnitsDict, True, False)

        resultCode = pop_dict_msg.get("result")
        if pop_dict_msg == None or resultCode == "error":
            get_current_logger().error(
                f"{pop_msg_refid} Error processing [ {pop_msg_area} ] Area Section Return is {pop_dict_msg}")
        else:
            if (resultCode == "OK"):

                pop_dict_msg = populateBldgListObj(self.masterFloorDict, self.masterBuildingDict, pop_msg_area, None, None,
                                                   accessoryUnits, accessoryUnitNames, accessoryUnitsDict, False,
                                                   False)

                resiObjList = pop_dict_msg.get("data")

                # refactor-3
                masterFloorTemp = pop_dict_msg.get("MASTERFLOORDICTKEY", None)
                masterBldgTemp = pop_dict_msg.get("MASTERBUILDINGDICTKEY", None)
                accessoryObjInst.setBaseUnitDict(resiObjList)

                # add to swap masterfloor/bldgDict
                self.masterFloorDict = masterFloorTemp if (masterFloorTemp is not None) else self.masterFloorDict
                self.masterBuildingDict = masterBldgTemp if (masterBldgTemp is not None) else self.masterBuildingDict
                # combined objects
                self.combinedObjects[pop_msg_area] = accessoryObjInst

    # def get_courtyard_details(self):
    #
    #     ## COURTYARD Layer
    #     pop_msg_area = LayerMaster.COURTYARD.value
    #
    #     # refactor-1
    #     courtyardObjInst = ObjectByType(pop_msg_area)
    #     courtyardUnitsDict = courtyardObjInst.getBaseUnitDict()
    #
    #     courtyardUnits = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, True, False)
    #
    #     courtyardUnitNames = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)
    #
    #     # refactor-2
    #     courtyardObjInst.setBaseList(courtyardUnits)
    #     courtyardObjInst.setBaseUnitNames(courtyardUnitNames)
    #
    #     pop_dict_msg = populateBldgListObj(self.masterFloorDict, self.masterBuildingDict, pop_msg_area, None, None,
    #                                        courtyardUnits,
    #                                        courtyardUnitNames, courtyardUnitsDict, True, False)
    #
    #     resultCode = pop_dict_msg.get("result")
    #     if pop_dict_msg == None or resultCode == "error":
    #         get_current_logger().error(
    #             f"Error processing [ {pop_msg_area} ] Area Section Return is {pop_dict_msg}")
    #     else:
    #         if (resultCode == "OK"):
    #             pop_dict_msg = populateBldgListObj(self.masterFloorDict, self.masterBuildingDict, pop_msg_area, None,
    #                                                None,
    #                                                courtyardUnits, courtyardUnitNames, courtyardUnitsDict, False,
    #                                                False)
    #
    #             resiObjList = pop_dict_msg.get("data")
    #
    #             # refactor-3
    #             masterFloorTemp = pop_dict_msg.get("MASTERFLOORDICTKEY", None)
    #             masterBldgTemp = pop_dict_msg.get("MASTERBUILDINGDICTKEY", None)
    #             courtyardObjInst.setBaseUnitDict(resiObjList)
    #
    #             # add to swap masterfloor/bldgDict
    #             self.masterFloorDict = masterFloorTemp if (masterFloorTemp is not None) else self.masterFloorDict
    #             self.masterBuildingDict = masterBldgTemp if (masterBldgTemp is not None) else self.masterBuildingDict
    #             # combined objects
    #             self.combinedObjects[pop_msg_area] = courtyardObjInst

    def get_ventiShaft_details(self):
        ##VENTILATIONSHAFT
        pop_msg_area = LayerMaster.VENTILATIONSHAFT.value
        pop_msg_refid = "2.3b"
        # refactor-1
        ventilationObjInst = ObjectByType(pop_msg_area)
        ventilationUnitsDict = ventilationObjInst.getBaseUnitDict()

        ventilationUnits = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, True, False)

        ventilationUnitNames = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)

        # refactor-2
        ventilationObjInst.setBaseList(ventilationUnits)
        ventilationObjInst.setBaseUnitNames(ventilationUnitNames)
        pop_dict_msg = populateBldgListObj(self.masterFloorDict, self.masterBuildingDict, pop_msg_area, None, None,
                                           ventilationUnits,
                                           ventilationUnitNames, ventilationUnitsDict, True, False)

        resultCode = pop_dict_msg.get("result")
        if pop_dict_msg == None or resultCode == "error":
            get_current_logger().error(
                f"{pop_msg_refid} Error processing [ {pop_msg_area} ] Area Section Return is {pop_dict_msg}")
        else:
            if (resultCode == "OK"):
                resiObjList = pop_dict_msg.get("data")

                # refactor-3
                masterFloorTemp = pop_dict_msg.get("MASTERFLOORDICTKEY", None)
                masterBldgTemp = pop_dict_msg.get("MASTERBUILDINGDICTKEY", None)
                ventilationObjInst.setBaseUnitDict(resiObjList)

                # add to swap masterfloor/bldgDict
                self.masterFloorDict = masterFloorTemp if (masterFloorTemp is not None) else self.masterFloorDict
                self.masterBuildingDict = masterBldgTemp if (masterBldgTemp is not None) else self.masterBuildingDict
                # combined objects
                self.combinedObjects[pop_msg_area] = ventilationObjInst

    def get_slabVoid_details(self):
        ##SLABCUTOUTVOID
        pop_msg_area = LayerMaster.SLABCUTOUTVOID.value
        pop_msg_refid = "2.3b"
        # refactor-1
        slabCutoutObjInst = ObjectByType(pop_msg_area)
        slabCutoutUnitsDict = slabCutoutObjInst.getBaseUnitDict()

        slabCutoutUnits = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, True, False)

        slabCutoutUnitNames = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)

        # refactor-2
        slabCutoutObjInst.setBaseList(slabCutoutUnits)
        slabCutoutObjInst.setBaseUnitNames(slabCutoutUnitNames)
        pop_dict_msg = process_slabcutoutvoid(self.masterFloorDict, self.masterBuildingDict, pop_msg_area, None, None,
                                              slabCutoutUnits,
                                              slabCutoutUnitNames, slabCutoutUnitsDict, True, False)

        resultCode = pop_dict_msg.get("result")
        if pop_dict_msg == None or resultCode == "error":
            get_current_logger().error(
                f"{pop_msg_refid} Error processing [ {pop_msg_area} ] Area Section Return is {pop_dict_msg}")
        else:
            if (resultCode == "OK"):
                resiObjList = pop_dict_msg.get("data")

                # refactor-3
                masterFloorTemp = pop_dict_msg.get("MASTERFLOORDICTKEY", None)
                masterBldgTemp = pop_dict_msg.get("MASTERBUILDINGDICTKEY", None)
                slabCutoutObjInst.setBaseUnitDict(resiObjList)

                # add to swap masterfloor/bldgDict
                self.masterFloorDict = masterFloorTemp if (masterFloorTemp is not None) else self.masterFloorDict
                self.masterBuildingDict = masterBldgTemp if (masterBldgTemp is not None) else self.masterBuildingDict
                # combined objects
                self.combinedObjects[pop_msg_area] = slabCutoutObjInst

    def get_resibua_details(self):
        ## RESIDENCE
        pop_msg_area = LayerMaster.RESIDENCE.value  #
        checkCnt = self.layerTypeDict.get(pop_msg_area, 0)

        if (checkCnt != 0 and checkCnt > 0):
            pop_msg_refid = "2.4"
            # refactor-1
            resiObjInst = ObjectByType(pop_msg_area)
            resiUnitsDict = resiObjInst.getBaseUnitDict()

            resiUnits = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, True, False)

            resiUnitNames = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)

            # refactor-2
            resiObjInst.setBaseList(resiUnits)
            resiObjInst.setBaseUnitNames(resiUnitNames)

            pop_dict_msg = populateBldgPolyListObj(self.masterFloorDict, pop_msg_area, resiUnits, resiUnitsDict, True,
                                                   None)

            resultCode = pop_dict_msg.get("result")
            if pop_dict_msg == None or resultCode == "error":
                get_current_logger().error(
                    f"{pop_msg_refid} Error processing [ {pop_msg_area} ] Area Section Return is {pop_dict_msg}")
            else:
                if (resultCode == "OK"):

                    resiObjList = pop_dict_msg.get("data")
                    # refactor-3
                    masterFloorTemp = pop_dict_msg.get("MASTERFLOORDICTKEY", None)

                    resiObjInst.setBaseUnitDict(resiObjList)

                    # add to swap masterfloor
                    self.masterFloorDict = masterFloorTemp if (masterFloorTemp is not None) else self.masterFloorDict

                    # combined objects
                    self.combinedObjects[pop_msg_area] = resiObjInst

    def get_commbua_details(self):
        ## COMMERCIAL
        pop_msg_area = LayerMaster.COMMERCIAL.value  #
        checkCnt = self.layerTypeDict.get(pop_msg_area, 0)

        if (checkCnt != 0 and checkCnt > 0):
            pop_msg_refid = "2.4"
            # refactor-1
            commObjInst = ObjectByType(pop_msg_area)
            commUnitsDict = commObjInst.getBaseUnitDict()

            commUnits = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, True, False)

            commUnitNames = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)

            # refactor-2
            commObjInst.setBaseList(commUnits)
            commObjInst.setBaseUnitNames(commUnitNames)

            pop_dict_msg = populateBldgPolyListObj(self.masterFloorDict, pop_msg_area, commUnits, commUnitsDict, True,
                                                   None)

            resultCode = pop_dict_msg.get("result")
            if pop_dict_msg == None or resultCode == "error":
                get_current_logger().error(
                    f"{pop_msg_refid} Error processing [ {pop_msg_area} ] Area Section Return is {pop_dict_msg}")
            else:
                if (resultCode == "OK"):

                    resiObjList = pop_dict_msg.get("data")
                    # refactor-3
                    masterFloorTemp = pop_dict_msg.get("MASTERFLOORDICTKEY", None)

                    commObjInst.setBaseUnitDict(resiObjList)

                    # add to swap masterfloor
                    self.masterFloorDict = masterFloorTemp if (masterFloorTemp is not None) else self.masterFloorDict

                    # combined objects
                    self.combinedObjects[pop_msg_area] = commObjInst

    def get_indbua_details(self):

        ## INDUSTRIAL
        pop_msg_area = LayerMaster.INDUSTRIAL.value  #
        pop_msg_area_list = [pop_msg_area, '_IndFAR']

        checkCnt = self.layerTypeDict.get(pop_msg_area, 0)

        if (checkCnt != 0 and checkCnt > 0):
            pop_msg_refid = "2.4"
            # refactor-1
            indvObjInst = ObjectByType(pop_msg_area)
            indvUnitsDict = indvObjInst.getBaseUnitDict()

            indvUnits = extractSubPlot(self.modelspace, pop_msg_area_list, LayerMaster.DWG_LWPOLYLINE.value, True, False)

            indvUnitNames = extractSubPlot(self.modelspace, pop_msg_area_list, LayerMaster.DWG_TEXT_MTEXT.value)

            # refactor-2
            indvObjInst.setBaseList(indvUnits)
            indvObjInst.setBaseUnitNames(indvUnitNames)

            pop_dict_msg = populateBldgPolyListObj(self.masterFloorDict, pop_msg_area, indvUnits, indvUnitsDict, True,
                                                   None)

            resultCode = pop_dict_msg.get("result")
            if pop_dict_msg == None or resultCode == "error":
                get_current_logger().error(
                    f"{pop_msg_refid} Error processing [ {pop_msg_area} ] Area Section Return is {pop_dict_msg}")
            else:
                if (resultCode == "OK"):

                    resiObjList = pop_dict_msg.get("data")
                    # refactor-3
                    masterFloorTemp = pop_dict_msg.get("MASTERFLOORDICTKEY", None)

                    indvObjInst.setBaseUnitDict(resiObjList)

                    # add to swap masterfloor
                    self.masterFloorDict = masterFloorTemp if (masterFloorTemp is not None) else self.masterFloorDict

                    # combined objects
                    self.combinedObjects[pop_msg_area] = indvObjInst

    def get_specialbua_details(self):
        pop_msg_area = LayerMaster.SPECIALUSE.value  #
        checkCnt = self.layerTypeDict.get(pop_msg_area, 0)

        if (checkCnt != 0 and checkCnt > 0):
            pop_msg_refid = "2.4"
            # refactor-1
            specialObjInst = ObjectByType(pop_msg_area)
            specialUseUnitsDict = specialObjInst.getBaseUnitDict()

            specialUseUnits = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, True, False)

            specialUseUnitNames = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)

            # refactor-2
            specialObjInst.setBaseList(specialUseUnits)
            specialObjInst.setBaseUnitNames(specialUseUnitNames)

            pop_dict_msg = populateBldgPolyListObj(self.masterFloorDict, pop_msg_area, specialUseUnits,
                                                   specialUseUnitsDict,
                                                   True, None)

            resultCode = pop_dict_msg.get("result")
            if pop_dict_msg == None or resultCode == "error":

                get_current_logger().error(
                    f"{pop_msg_refid} Error processing [ {pop_msg_area} ] Area Section Return is {pop_dict_msg}")
            else:
                if (resultCode == "OK"):

                    resiObjList = pop_dict_msg.get("data")
                    # refactor-3
                    masterFloorTemp = pop_dict_msg.get("MASTERFLOORDICTKEY", None)

                    specialObjInst.setBaseUnitDict(resiObjList)

                    # add to swap masterfloor
                    self.masterFloorDict = masterFloorTemp if (masterFloorTemp is not None) else self.masterFloorDict

                    # combined objects
                    self.combinedObjects[pop_msg_area] = specialObjInst

    def get_ramp_details(self):

        ## RAMP
        pop_msg_area = LayerMaster.RAMP.value  #
        pop_msg_refid = "2.5"

        # refactor-1
        rampObjInst = ObjectByType(pop_msg_area)
        rampUnitsDict = rampObjInst.getBaseUnitDict()

        rampUnits = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, True, False)

        rampUnitNames = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)

        # refactor-2
        rampObjInst.setBaseList(rampUnits)
        rampObjInst.setBaseUnitNames(rampUnitNames)

        pop_dict_msg = populateBldgListObj(self.masterFloorDict, self.masterBuildingDict, pop_msg_area, None, None, rampUnits,
                                           rampUnitNames, rampUnitsDict, True)

        resultCode = pop_dict_msg.get("result")
        if pop_dict_msg == None or resultCode == "error":
            get_current_logger().error(
                f"{pop_msg_refid} Error processing [ {pop_msg_area} ] Area Section Return is {pop_dict_msg}")
        else:
            if (resultCode == "OK"):

                resiObjList = pop_dict_msg.get("data")

                # refactor-3
                masterFloorTemp = pop_dict_msg.get("MASTERFLOORDICTKEY", None)
                masterBldgTemp = pop_dict_msg.get("MASTERBUILDINGDICTKEY", None)
                rampObjInst.setBaseUnitDict(resiObjList)

                # add to swap masterfloor/bldgDict
                self.masterFloorDict = masterFloorTemp if (masterFloorTemp is not None) else self.masterFloorDict
                self.masterBuildingDict = masterBldgTemp if (masterBldgTemp is not None) else self.masterBuildingDict
                # combined objects
                self.combinedObjects[pop_msg_area] = rampObjInst

    def get_floorinsection_details(self):

        ### FLOORINSECTION
        if (self.layerDict.get(LayerMaster.FLOORINSECTION.value, 0) != 0):

            pop_msg_area = LayerMaster.FLOORINSECTION.value  #
            pop_msg_refid = "2.9"

            # refactor-1
            floorInSectionObjInst = ObjectByType(pop_msg_area)
            floorInSectionUnitsDict = floorInSectionObjInst.getBaseUnitDict()

            floorInSectionUnits = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, False, False)

            floorInSectionUnitNames = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)

            # refactor-2
            floorInSectionObjInst.setBaseList(floorInSectionUnits)
            floorInSectionObjInst.setBaseUnitNames(floorInSectionUnitNames)

            pop_dict_msg = populateBldgListObj(self.masterFloorDict, self.masterBuildingDict, pop_msg_area, None, None,
                                               floorInSectionUnits, floorInSectionUnitNames,
                                               floorInSectionUnitsDict, False,
                                               False)

            resultCode = pop_dict_msg.get("result")
            if pop_dict_msg == None or resultCode == "error":
                get_current_logger().error(
                    f"{pop_msg_refid} Error processing [ {pop_msg_area} ] Area Section Return is {pop_dict_msg}")
            else:
                if (resultCode == "OK"):
                    resiObjList = pop_dict_msg.get("data")
                    # raise exception if count is 0
                    if (len(resiObjList) == 0):
                        msg = f'Unable to find any {pop_msg_area} entities and it is mandatory to proceed with Drawing. '
                        self.responsedict['responseCode'] = FAIL_CODE
                        self.responsedict['error_category'] = "INVALID FILE"
                        self.responsedict['errors'] = [msg]
                        self.responsedict['planType'] = 'Building'
                        self.responsedict['dwgExtract'] = []

                        get_current_logger().error(msg)
                        return self.responsedict

                    # refactor-3
                    masterFloorTemp = pop_dict_msg.get("MASTERFLOORDICTKEY", None)
                    masterBldgTemp = pop_dict_msg.get("MASTERBUILDINGDICTKEY", None)
                    floorInSectionObjInst.setBaseUnitDict(resiObjList)

                    # add to swap masterfloor/bldgDict
                    self.masterFloorDict = masterFloorTemp if (masterFloorTemp is not None) else self.masterFloorDict
                    self.masterBuildingDict = masterBldgTemp if (masterBldgTemp is not None) else self.masterBuildingDict
                    # combined objects
                    self.combinedObjects[pop_msg_area] = floorInSectionObjInst

    def get_parking_details(self):

        ### PARKING
        if (self.layerDict.get(LayerMaster.PARKING.value, 0) != 0):

            pop_msg_area = LayerMaster.PARKING.value  #
            pop_msg_refid = "2.10"
            # refactor-1
            parkingObjInst = ObjectByType(pop_msg_area)
            parkingUnitsDict = parkingObjInst.getBaseUnitDict()

            parkingUnits = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, False, False)

            parkingUnitNames = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)

            # refactor-2
            parkingObjInst.setBaseList(parkingUnits)
            parkingObjInst.setBaseUnitNames(parkingUnitNames)

            pop_dict_msg = populateBldgListObj(self.masterFloorDict, self.masterBuildingDict, pop_msg_area, None, None,
                                               parkingUnits,
                                               parkingUnitNames, parkingUnitsDict, True, False)

            resultCode = pop_dict_msg.get("result")
            if pop_dict_msg == None or resultCode == "error":
                get_current_logger().error(
                    f"{pop_msg_refid} Error processing [ {pop_msg_area} ] Area Section Return is {pop_dict_msg}")
            else:
                if (resultCode == "OK"):
                    resiObjList = pop_dict_msg.get("data")
                    # refactor-3
                    masterFloorTemp = pop_dict_msg.get("MASTERFLOORDICTKEY", None)
                    masterBldgTemp = pop_dict_msg.get("MASTERBUILDINGDICTKEY", None)
                    parkingObjInst.setBaseUnitDict(resiObjList)

                    # add to swap masterfloor/bldgDict
                    self.masterFloorDict = masterFloorTemp if (masterFloorTemp is not None) else self.masterFloorDict
                    self.masterBuildingDict = masterBldgTemp if (masterBldgTemp is not None) else self.masterBuildingDict

                    pop_dict_msg = populateBldgListObj(self.masterFloorDict, self.masterBuildingDict, pop_msg_area, None,
                                                       None,
                                                       parkingUnits, parkingUnitNames, parkingUnitsDict, False,
                                                       False)
                    resiObjList = pop_dict_msg.get("data")

                    get_current_logger().debug(f" PARKING 2nd run  {len(resiObjList)}")

                    # refactor-3
                    masterFloorTemp = pop_dict_msg.get("MASTERFLOORDICTKEY", None)
                    masterBldgTemp = pop_dict_msg.get("MASTERBUILDINGDICTKEY", None)
                    parkingObjInst.setBaseUnitDict(resiObjList)

                    # add to swap masterfloor/bldgDict
                    self.masterFloorDict = masterFloorTemp if (masterFloorTemp is not None) else self.masterFloorDict
                    self.masterBuildingDict = masterBldgTemp if (masterBldgTemp is not None) else self.masterBuildingDict

                    # combined objects
                    self.combinedObjects[pop_msg_area] = parkingObjInst

    def get_passage_details(self):

        if (self.layerDict.get(LayerMaster.PASSAGE.value, 0) != 0):

            pop_msg_area = LayerMaster.PASSAGE.value  #
            pop_msg_refid = "2.11"
            # refactor-1
            passageObjInst = ObjectByType(pop_msg_area)
            passageUnitsDict = passageObjInst.getBaseUnitDict()

            passageUnits = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, False, False)

            passageWithCenterLineProcessedList = mapCenterLinesWithinObjectList(passageUnits)

            passageWidthById = dict()

            if (passageWithCenterLineProcessedList is not None and len(passageWithCenterLineProcessedList) > 0):
                passageUnits = passageWithCenterLineProcessedList

                for tmpPassage in passageWithCenterLineProcessedList:

                    cListDict = tmpPassage.getMiscProps()
                    if (len(cListDict) > 0):
                        centerLineTxt = cListDict.get('centerline', 0)
                        if (centerLineTxt != 0):
                            centerList = getPointsAsListFromString(centerLineTxt)
                            # print ('Road Polygon ', str(tmpRoad.get_points()) )
                            polyStr = str(tmpPassage.get_points())[1:-1].translate(translation)

                            # create a ploygon
                            polyPoints = 'POLYGON ((' + polyStr + '))'

                            lwpoly = shapely.wkt.loads(polyPoints)

                            lpoints = list(lwpoly.exterior.coords)

                            min_Width = getMinWidthByCenterLine(lpoints, centerList)

                            passageWidthById[tmpPassage.handle] = float(min_Width) * 2

                self.combinedObjects['PASSAGE_WIDTHS'] = passageWidthById

            passageUnitNames = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)

            # refactor-2
            passageObjInst.setBaseList(passageUnits)
            passageObjInst.setBaseUnitNames(passageUnitNames)


            pop_dict_msg = populateBldgListObj(self.masterFloorDict, self.masterBuildingDict, pop_msg_area, None, None,
                                               passageUnits,
                                               passageUnitNames, passageUnitsDict, True, False)

            resultCode = pop_dict_msg.get("result")
            if pop_dict_msg == None or resultCode == "error":
                get_current_logger().error(
                    f"{pop_msg_refid} Error processing [ {pop_msg_area} ] Area Section Return is {pop_dict_msg}")
            else:
                if (resultCode == "OK"):

                    resiObjList = pop_dict_msg.get("data")
                    # refactor-3
                    masterFloorTemp = pop_dict_msg.get("MASTERFLOORDICTKEY", None)
                    masterBldgTemp = pop_dict_msg.get("MASTERBUILDINGDICTKEY", None)
                    passageObjInst.setBaseUnitDict(resiObjList)

                    # add to swap masterfloor/bldgDict
                    self.masterFloorDict = masterFloorTemp if (masterFloorTemp is not None) else self.masterFloorDict
                    self.masterBuildingDict = masterBldgTemp if (masterBldgTemp is not None) else self.masterBuildingDict
                    # combined objects
                    self.combinedObjects[pop_msg_area] = passageObjInst

    def get_lift_details(self):
        # LIFT
        if (self.layerDict.get(LayerMaster.LIFT.value, 0) != 0):

            pop_msg_area = LayerMaster.LIFT.value  #
            pop_msg_refid = "2.12"
            # refactor-1
            liftObjInst = ObjectByType(pop_msg_area)
            liftUnitsDict = liftObjInst.getBaseUnitDict()

            liftUnits = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, False, False)

            liftUnitNames = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)

            # refactor-2
            liftObjInst.setBaseList(liftUnits)
            liftObjInst.setBaseUnitNames(liftUnitNames)

            pop_dict_msg = populateBldgListObj(self.masterFloorDict, self.masterBuildingDict, pop_msg_area, None, None,
                                               liftUnits,
                                               liftUnitNames, liftUnitsDict, True, False)

            resultCode = pop_dict_msg.get("result")
            if pop_dict_msg == None or resultCode == "error":
                get_current_logger().error(
                    f"{pop_msg_refid} Error processing [ {pop_msg_area} ] Area Section Return is {pop_dict_msg}")
            else:
                if (resultCode == "OK"):
                    get_current_logger().info(f"{pop_msg_refid} Section [ {pop_msg_area} ] Area : Completed ")

                    resiObjList = pop_dict_msg.get("data")

                    # refactor-3
                    masterFloorTemp = pop_dict_msg.get("MASTERFLOORDICTKEY", None)
                    masterBldgTemp = pop_dict_msg.get("MASTERBUILDINGDICTKEY", None)
                    liftObjInst.setBaseUnitDict(resiObjList)

                    # add to swap masterfloor/bldgDict
                    self.masterFloorDict = masterFloorTemp if (masterFloorTemp is not None) else self.masterFloorDict
                    self.masterBuildingDict = masterBldgTemp if (masterBldgTemp is not None) else self.masterBuildingDict
                    # combined objects
                    self.combinedObjects[pop_msg_area] = liftObjInst

    def get_stailcase_details(self):

        # STAIRCASE
        if (self.layerDict.get(LayerMaster.STAIRCASE.value, 0) != 0):

            pop_msg_area = LayerMaster.STAIRCASE.value  #
            pop_msg_refid = "2.13"
            # refactor-1
            stairCaseObjInst = ObjectByType(pop_msg_area)
            stairCaseUnitsDict = stairCaseObjInst.getBaseUnitDict()

            stairCaseUnits = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, False, False)

            stairCaseUnitNames = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)
            # refactor-2
            stairCaseObjInst.setBaseList(stairCaseUnits)
            stairCaseObjInst.setBaseUnitNames(stairCaseUnitNames)

            pop_dict_msg = populateBldgListObj(self.masterFloorDict, self.masterBuildingDict, pop_msg_area, None, None,
                                               stairCaseUnits, stairCaseUnitNames, stairCaseUnitsDict, True, False)

            resultCode = pop_dict_msg.get("result")
            if pop_dict_msg == None or resultCode == "error":
                get_current_logger().error(
                    f"{pop_msg_refid} Error processing [ {pop_msg_area} ] Area Section Return is {pop_dict_msg}")
            else:
                if (resultCode == "OK"):
                    get_current_logger().info(f"{pop_msg_refid} Section [ {pop_msg_area} ] Area : Completed ")

                    resiObjList = pop_dict_msg.get("data")

                    # refactor-3
                    masterFloorTemp = pop_dict_msg.get("MASTERFLOORDICTKEY", None)
                    masterBldgTemp = pop_dict_msg.get("MASTERBUILDINGDICTKEY", None)
                    stairCaseObjInst.setBaseUnitDict(resiObjList)

                    # add to swap masterfloor/bldgDict
                    self.masterFloorDict = masterFloorTemp if (masterFloorTemp is not None) else self.masterFloorDict
                    self.masterBuildingDict = masterBldgTemp if (masterBldgTemp is not None) else self.masterBuildingDict
                    # combined objects
                    self.combinedObjects[pop_msg_area] = stairCaseObjInst

    def get_balcony_details(self):

        # BALCONY
        if (self.layerDict.get(LayerMaster.BALCONY.value, 0) != 0):

            pop_msg_area = LayerMaster.BALCONY.value  #
            pop_msg_refid = "2.13"

            # refactor-1
            balconyObjInst = ObjectByType(pop_msg_area)
            balconyUnitsDict = balconyObjInst.getBaseUnitDict()

            balconyUnits = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, False, False)

            balconyUnitNames = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)

            # refactor-2
            balconyObjInst.setBaseList(balconyUnits)
            balconyObjInst.setBaseUnitNames(balconyUnitNames)

            pop_dict_msg = populateBldgListObj(self.masterFloorDict, self.masterBuildingDict, pop_msg_area, None, None,
                                               balconyUnits,
                                               balconyUnitNames, balconyUnitsDict, True, False)

            resultCode = pop_dict_msg.get("result")
            if pop_dict_msg == None or resultCode == "error":
                get_current_logger().error(
                    f"{pop_msg_refid} Error processing [ {pop_msg_area} ] Area Section Return is {pop_dict_msg}")
            else:
                if (resultCode == "OK"):
                    get_current_logger().info(f"{pop_msg_refid} Section [ {pop_msg_area} ] Area : Completed ")

                    resiObjList = pop_dict_msg.get("data")

                    # refactor-3
                    masterFloorTemp = pop_dict_msg.get("MASTERFLOORDICTKEY", None)
                    masterBldgTemp = pop_dict_msg.get("MASTERBUILDINGDICTKEY", None)
                    balconyObjInst.setBaseUnitDict(resiObjList)

                    # add to swap masterfloor/bldgDict
                    self.masterFloorDict = masterFloorTemp if (masterFloorTemp is not None) else self.masterFloorDict
                    self.masterBuildingDict = masterBldgTemp if (masterBldgTemp is not None) else self.masterBuildingDict
                    # combined objects
                    self.combinedObjects[pop_msg_area] = balconyObjInst

    def get_plot_details(self):

        ### PLOT (Main Plot)
        if (self.layerDict.get(LayerMaster.PLOT.value, 0) != 0):

            pop_msg_area = LayerMaster.PLOT.value  #
            pop_msg_refid = "2.14"

            # refactor-1
            plotObjInst = ObjectByType(pop_msg_area)
            plotUnitDict = plotObjInst.getBaseUnitDict()

            plotUnits = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, False, False)

            plotUnitNames = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)

            # refactor-2
            plotObjInst.setBaseList(plotUnits)
            plotObjInst.setBaseUnitNames(plotUnitNames)

            get_current_logger().info(f"{pop_msg_refid} Section [ {pop_msg_area} ] Area : Starting ")

            pop_dict_msg = populateBldgPolyListObj(self.masterFloorDict, pop_msg_area, plotUnits, plotUnitDict, False,
                                                   None)

            resultCode = pop_dict_msg.get("result")
            if pop_dict_msg == None or resultCode == "error":
                get_current_logger().error(
                    f"{pop_msg_refid} Error processing [ {pop_msg_area} ] Area Section Return is {pop_dict_msg}")
            else:
                if (resultCode == "OK" or resultCode == "warning"):
                    get_current_logger().info(f"{pop_msg_refid} Section [ {pop_msg_area} ] Area : Completed ")
                    if (resultCode == "warning"):
                        self.warnings.append(pop_dict_msg.get("msg"))

                    resiObjList = pop_dict_msg.get("data")

                    # refactor-3
                    masterFloorTemp = pop_dict_msg.get("MASTERFLOORDICTKEY", None)
                    plotObjInst.setBaseUnitDict(resiObjList)

                    # add to swap masterfloor/bldgDict
                    self.masterFloorDict = masterFloorTemp if (masterFloorTemp is not None) else self.masterFloorDict
                    # combined objects
                    self.combinedObjects[pop_msg_area] = plotObjInst

    def get_netplot_details(self):

        if (self.layerDict.get(LayerMaster.NETPLOT.value, 0) != 0):

            # refactor-1
            plotUnitDict = self.combinedObjects.get(LayerMaster.PLOT.value).getBaseUnitDict() if self.combinedObjects.get(
                LayerMaster.PLOT.value, 0) != 0 else {}

            pop_msg_area = LayerMaster.NETPLOT.value  #
            pop_msg_refid = "2.15"
            # refactor-1
            netPlotObjInst = ObjectByType(pop_msg_area)
            netPlotDict = netPlotObjInst.getBaseUnitDict()

            netPlotUnits = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, False, False)

            netPlotNames = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)

            # refactor-2
            netPlotObjInst.setBaseList(netPlotUnits)
            netPlotObjInst.setBaseUnitNames(netPlotNames)

            get_current_logger().info(f"{pop_msg_refid} Section [ {pop_msg_area} ] Area : Starting ")

            pop_dict_msg = populateBldgPolyListObj(self.masterFloorDict, pop_msg_area, netPlotUnits, netPlotDict, False,
                                                   plotUnitDict)

            resultCode = pop_dict_msg.get("result")
            if pop_dict_msg == None or resultCode == "error":

                get_current_logger().error(
                    f"{pop_msg_refid} Error processing [ {pop_msg_area} ] Area Section Return is {pop_dict_msg}")
            else:
                if (resultCode == "OK"):
                    get_current_logger().info(f"{pop_msg_refid}  Section [ {pop_msg_area} ] Area : Completed ")

                    resiObjList = pop_dict_msg.get("data")

                    # refactor-3
                    masterFloorTemp = pop_dict_msg.get("MASTERFLOORDICTKEY", None)
                    netPlotObjInst.setBaseUnitDict(resiObjList)

                    # add to swap masterfloor/bldgDict
                    self.masterFloorDict = masterFloorTemp if (masterFloorTemp is not None) else self.masterFloorDict
                    # combined objects
                    self.combinedObjects[pop_msg_area] = netPlotObjInst

                    resiObjList = ''

    def get_proposedwork_details(self):
        ### PROPOSEDWORK
        if (self.layerDict.get(LayerMaster.PROPOSEDWORK.value, 0) != 0 or self.layerDict.get('_PropWork', 0) != 0):

            pop_msg_area = LayerMaster.PROPOSEDWORK.value  #

            pop_msg_refid = "2.16"
            pop_msg_area_list = [LayerMaster.PROPOSEDWORK.value, '_PropWork']
            # refactor-1
            proposedWorkObjInst = ObjectByType(pop_msg_area)
            proposedWorkDict = proposedWorkObjInst.getBaseUnitDict()

            netPlotDict = self.combinedObjects.get(LayerMaster.NETPLOT.value).getBaseUnitDict() if self.combinedObjects.get(
                LayerMaster.NETPLOT.value, 0) != 0 else {}

            proposedWorkUnits = extractSubPlot(self.modelspace, pop_msg_area_list, LayerMaster.DWG_LWPOLYLINE.value, False,
                                               False)

            proposedWorkUnitNames = extractSubPlot(self.modelspace, pop_msg_area_list, LayerMaster.DWG_TEXT_MTEXT.value)

            # refactor-2
            proposedWorkObjInst.setBaseList(proposedWorkUnits)
            proposedWorkObjInst.setBaseUnitNames(proposedWorkUnitNames)

            get_current_logger().info(f"{pop_msg_refid} Section [ {pop_msg_area} ] Area : Starting ")
            pop_dict_msg = populateBldgListObj(self.masterFloorDict, self.masterBuildingDict, pop_msg_area, netPlotDict, None,
                                               proposedWorkUnits, proposedWorkUnitNames, proposedWorkDict, False,
                                               False)

            resultCode = pop_dict_msg.get("result")
            if pop_dict_msg == None or resultCode == "error":
                get_current_logger().error(
                    f"{pop_msg_refid} Error processing [ {pop_msg_area} ] Area Section Return is {pop_dict_msg}")
            else:
                if (resultCode == "OK"):
                    get_current_logger().info(f"{pop_msg_refid} Section [ {pop_msg_area} ] Area : Completed ")

                    resiObjList = pop_dict_msg.get("data")

                    if (len(resiObjList) < len(proposedWorkUnitNames)):
                        msgtx = "  ".join(
                            [pop_msg_area, pop_msg_refid, ' count mismatch after processing expecting ', \
                             str(len(proposedWorkUnitNames)), " got ", str(len(resiObjList))])
                        self.warnings.append(msgtx)

                    # refactor-3
                    masterFloorTemp = pop_dict_msg.get("MASTERFLOORDICTKEY", None)
                    masterBldgTemp = pop_dict_msg.get("MASTERBUILDINGDICTKEY", None)
                    proposedWorkObjInst.setBaseUnitDict(resiObjList)

                    # add to swap masterfloor/bldgDict
                    self.masterFloorDict = masterFloorTemp if (masterFloorTemp is not None) else self.masterFloorDict
                    self.masterBuildingDict = masterBldgTemp if (masterBldgTemp is not None) else self.masterBuildingDict
                    # combined objects
                    self.combinedObjects[pop_msg_area] = proposedWorkObjInst

    def get_netplotFromareatable_details(self):

        direct_read_filename = os.path.join(self.dxf_dir, self.file_name)
        self.textElementsResultsDict = grepFromFile(direct_read_filename, TEXT_ELEMENTS_FROM_DWG)

        # PROPOSED COVERAGE
        proposedCoverageText = self.textElementsResultsDict.get("Proposed Coverage", 0)

        get_current_logger().debug(f'Coverage Text  {proposedCoverageText}')
        if (proposedCoverageText != 0 and len(proposedCoverageText) > 0):
            # there is % mentioned
            # get the float value
            proposedCoverageTmp = extract_dimensions_fromtext(proposedCoverageText[0], None, '%')
            if (float(proposedCoverageTmp) > 0):
                # use this value
                self.coverageAreaPercent = float(proposedCoverageTmp)
                get_current_logger().debug(f"Setting coverageAreaPercent  {self.coverageAreaPercent}")

        else:
            get_current_logger().error(
                "Coverage Area Not present in the Plan AREA Table. **** Will apply ProposedWorkArea **** ")

        coverageDict = {"COVERAGE_AREA_PERCENT": self.coverageAreaPercent}
        pop_msg_area = LayerMaster.AREATABLE.value
        self.combinedObjects[pop_msg_area] = coverageDict

    def get_propworkFromareatable_details(self):
        pop_msg_area = LayerMaster.AREATABLE.value #
        coverageDict = {"COVERAGE_AREA_PERCENT": self.coverageAreaPercent}

        self.combinedObjects[pop_msg_area] = coverageDict
        self.combinedObjects["PLAN_TEXT_ELEMENTS"] = self.textElementsResultsDict

        # COMPOUNDWALL
        if (self.layerDict.get(LayerMaster.COMPOUNDWALL.value, 0) != 0):

            pop_msg_area = LayerMaster.COMPOUNDWALL.value  #
            pop_msg_refid = "2.17"
            plotUnits = extractSubPlot(self.modelspace, "_Plot", LayerMaster.DWG_LWPOLYLINE.value, False, False)
            # refactor-1
            compoundWallObjInst = ObjectByType(pop_msg_area)
            compoundWallDict = compoundWallObjInst.getBaseUnitDict()

            compoundWallUnits = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, False, True)

            compoundWallNames = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value, False)

            # refactor-2
            compoundWallObjInst.setBaseList(compoundWallUnits)
            compoundWallObjInst.setBaseUnitNames(compoundWallNames)

            get_current_logger().info(f"{pop_msg_refid} Section [ {pop_msg_area} ] Area : Starting ")
            pop_dict_msg = populateBldgListObj(self.masterFloorDict, self.masterBuildingDict, pop_msg_area, plotUnits, None,
                                               compoundWallUnits, compoundWallNames, compoundWallDict, False, True)

            # populateBldgListObj (pop_msg_area, netPlotDict, None, existingStructUnits, existingStructUnitNames,   existingStructDict, False, False )

            resultCode = pop_dict_msg.get("result")
            if pop_dict_msg == None or resultCode == "error":
                get_current_logger().error(
                    f"{pop_msg_refid} Error processing [ {pop_msg_area} ] Area Section Return is {pop_dict_msg}")
            else:
                if (resultCode == "OK"):
                    get_current_logger().info(f"{pop_msg_refid} Section [ {pop_msg_area} ] Area : Completed ")

                    resiObjList = pop_dict_msg.get("data")

                    if (len(resiObjList) < len(compoundWallNames)):
                        msgtx = "  ".join(
                            [pop_msg_area, pop_msg_refid, ' count mismatch after processing expecting ', \
                             str(len(compoundWallNames)), " got ", str(len(resiObjList))])
                        self.warnings.append(msgtx)

                    # refactor-3
                    masterFloorTemp = pop_dict_msg.get("MASTERFLOORDICTKEY", None)
                    masterBldgTemp = pop_dict_msg.get("MASTERBUILDINGDICTKEY", None)
                    compoundWallObjInst.setBaseUnitDict(resiObjList)

                    # add to swap masterfloor/bldgDict
                    self.masterFloorDict = masterFloorTemp if (masterFloorTemp is not None) else self.masterFloorDict
                    self.masterBuildingDict = masterBldgTemp if (masterBldgTemp is not None) else self.masterBuildingDict
                    # combined objects
                    self.combinedObjects[pop_msg_area] = compoundWallObjInst

    def get_OrganizedOpenSpace_details(self):

        if (self.layerDict.get(LayerMaster.ORGOPENSPACE.value, 0) != 0):

            pop_msg_area = LayerMaster.ORGOPENSPACE.value  #
            pop_msg_refid = "2.18"
            # refactor-1
            totObjInst = ObjectByType(pop_msg_area)
            totUnitsDict = totObjInst.getBaseUnitDict()

            totUnits = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, True, False)

            totUnitNames = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)

            # refactor-2
            totObjInst.setBaseList(totUnits)
            totObjInst.setBaseUnitNames(totUnitNames)

            get_current_logger().info(f"{pop_msg_refid} Section [ {pop_msg_area} ] Area : Starting ")

            pop_dict_msg = populateBldgListObj(self.masterFloorDict, self.masterBuildingDict, pop_msg_area, None, None,
                                               totUnits,
                                               totUnitNames, totUnitsDict, False, False)

            resultCode = pop_dict_msg.get("result")
            if pop_dict_msg == None or resultCode == "error":
                get_current_logger().error(
                    f"{pop_msg_refid} Error processing [ {pop_msg_area} ] Area Section Return is {pop_dict_msg}")
            else:
                if (resultCode == "OK"):
                    get_current_logger().info(f"{pop_msg_refid} Section [ {pop_msg_area} ] Area : Completed ")

                    resiObjList = pop_dict_msg.get("data")

                    if (len(resiObjList) < len(totUnitNames)):
                        msgtx = "  ".join(
                            [pop_msg_area, pop_msg_refid, ' count mismatch after processing expecting ', \
                             str(len(totUnitNames)), " got ", str(len(resiObjList))])
                        self.warnings.append(msgtx)

                    # refactor-3
                    masterFloorTemp = pop_dict_msg.get("MASTERFLOORDICTKEY", None)
                    masterBldgTemp = pop_dict_msg.get("MASTERBUILDINGDICTKEY", None)
                    totObjInst.setBaseUnitDict(resiObjList)

                    # add to swap masterfloor/bldgDict
                    self.masterFloorDict = masterFloorTemp if (masterFloorTemp is not None) else self.masterFloorDict
                    self.masterBuildingDict = masterBldgTemp if (masterBldgTemp is not None) else self.masterBuildingDict
                    # combined objects
                    self.combinedObjects[pop_msg_area] = totObjInst

    def get_ExistingStructure_details(self):
        ### EXISTINGSTRUCTURE
        if (self.layerDict.get(LayerMaster.EXISTINGSTRUCTURE.value, 0) != 0):

            pop_msg_area = LayerMaster.EXISTINGSTRUCTURE.value  #

            existingStructObjInst = ObjectByType(pop_msg_area)
            existingStructDict = existingStructObjInst.getBaseUnitDict()
            pop_msg_refid = "2.15"

            netPlotDict = self.combinedObjects.get(
                LayerMaster.NETPLOT.value).getBaseUnitDict() if self.combinedObjects.get(
                LayerMaster.NETPLOT.value, 0) != 0 else {}

            existingStructUnits = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, False, False)

            existingStructUnitNames = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)

            # refactor-2
            existingStructObjInst.setBaseList(existingStructUnits)
            existingStructObjInst.setBaseUnitNames(existingStructUnitNames)

            get_current_logger().info(f"{pop_msg_refid} Section [ {pop_msg_area} ] Area : Starting ")

            pop_dict_msg = populateBldgListObj(self.masterFloorDict, self.masterBuildingDict, pop_msg_area, netPlotDict, None,
                                               existingStructUnits, existingStructUnitNames, existingStructDict,
                                               False,
                                               False)

            resultCode = pop_dict_msg.get("result")
            if pop_dict_msg == None or resultCode == "error":
                get_current_logger().error(
                    f"{pop_msg_refid} Error processing [ {pop_msg_area} ] Area Section Return is {pop_dict_msg}")
            else:
                if (resultCode == "OK"):
                    get_current_logger().info(f"{pop_msg_refid} Section [ {pop_msg_area} ] Area : Completed ")

                    resiObjList = pop_dict_msg.get("data")

                    if (len(resiObjList) < len(existingStructUnitNames)):
                        msgtx = "  ".join(
                            [pop_msg_area, pop_msg_refid, ' count mismatch after processing expecting ', \
                             str(len(existingStructUnitNames)), " got ", str(len(resiObjList))])
                        self.warnings.append(msgtx)

                    # refactor-3
                    masterFloorTemp = pop_dict_msg.get("MASTERFLOORDICTKEY", None)
                    masterBldgTemp = pop_dict_msg.get("MASTERBUILDINGDICTKEY", None)
                    existingStructObjInst.setBaseUnitDict(resiObjList)

                    # add to swap masterfloor/bldgDict
                    self.masterFloorDict = masterFloorTemp if (masterFloorTemp is not None) else self.masterFloorDict
                    self.masterBuildingDict = masterBldgTemp if (masterBldgTemp is not None) else self.masterBuildingDict
                    # combined objects
                    self.combinedObjects[pop_msg_area] = existingStructObjInst

    def get_ElectricLine_details(self):
        ### ELECTRICLINE
        if (self.layerDict.get(LayerMaster.ELECTRICLINE.value, 0) != 0):

            pop_msg_area = LayerMaster.ELECTRICLINE.value  #
            pop_msg_refid = "2.20"
            # refactor-1
            electricLinesObjInst = ObjectByType(pop_msg_area)
            electricLinesDict = electricLinesObjInst.getBaseUnitDict()

            electricLineUnits = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, False, False)

            electricLineUnitNames = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)
            # refactor-2
            electricLinesObjInst.setBaseList(electricLineUnits)
            electricLinesObjInst.setBaseUnitNames(electricLineUnitNames)

            get_current_logger().info(f"pop_msg_refid Section [ {pop_msg_area} ] Area : Starting ")
            pop_dict_msg = populateBldgListObj(self.masterFloorDict, self.masterBuildingDict, pop_msg_area, None, None,
                                               electricLineUnits, electricLineUnitNames, electricLinesDict, False,
                                               True)

            resultCode = pop_dict_msg.get("result")
            if pop_dict_msg == None or resultCode == "error":
                get_current_logger().error(
                    f"{pop_msg_refid} Error processing [ {pop_msg_area} ] Area Section Return is {pop_dict_msg}")
            else:
                if (resultCode == "OK"):
                    get_current_logger().info(f"{pop_msg_refid} Section [ {pop_msg_area} ] Area : Completed ")

                    resiObjList = pop_dict_msg.get("data")

                    if (len(resiObjList) < len(electricLineUnitNames)):
                        msgtx = "  ".join(
                            [pop_msg_area, pop_msg_refid, ' count mismatch after processing expecting ', \
                             str(len(electricLineUnitNames)), " got ", str(len(resiObjList))])
                        self.warnings.append(msgtx)

                    # refactor-3

                    electricLinesObjInst.setBaseUnitDict(resiObjList)

                    self.combinedObjects[pop_msg_area] = electricLinesObjInst

    def get_MainRoad_details(self):

        # MAIN ROAD
        pop_msg_area = LayerMaster.MAINROAD.value
        mainRoadObjInst = ObjectByType(pop_msg_area)
        mainRoadDict = mainRoadObjInst.getBaseUnitDict()
        mainRoadList = mainRoadObjInst.getBaseUnitFinalList()

        if (self.layerDict.get(LayerMaster.MAINROAD.value, 0) != 0):
            pop_msg_refid = "2.21"

            mainRoadAreaPlots = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, True, False)

            mainRoadNames = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)

            mainRoadObjInst.setBaseList(mainRoadAreaPlots)
            mainRoadObjInst.setBaseUnitNames(mainRoadNames)

            get_current_logger().info(f"{pop_msg_refid} Section [ {pop_msg_area} ] Area : Starting ")
            pop_dict_msg = populateIndivPolyListObj(pop_msg_area, mainRoadAreaPlots, mainRoadNames, mainRoadList,
                                                    mainRoadDict, None)

            resultCode = pop_dict_msg.get("result")

            if pop_dict_msg == None or resultCode == "error":
                get_current_logger().error(
                    f"{pop_msg_refid} Error processing [ {pop_msg_area} ] Area Section Return is {pop_dict_msg}")
            else:
                if (resultCode == "OK"):
                    get_current_logger().info(f"{pop_msg_refid} Section [ {pop_msg_area} ] Area : Completed ")
                    areaObjList = pop_dict_msg.get("data_list")
                    for araobj in areaObjList:
                        get_current_logger().debug(f"main road info {araobj}")

                    if (len(self.resiObjList) < len(mainRoadNames)):
                        msgtx = "  ".join(
                            [pop_msg_area, pop_msg_refid, ' count mismatch after processing expecting ', \
                             str(len(mainRoadNames)), " got ", str(len(self.resiObjList))])
                        self.warnings.append(msgtx)

                    # refactor-3
                    areaObjDict = pop_dict_msg.get("data_dict", None)

                    # overwrite with the data returned from function
                    mainRoadObjInst.setBaseUnitDict(areaObjDict)
                    mainRoadObjInst.setBaseUnitFinalList(areaObjList)

                    # combined objects
                    self.combinedObjects[pop_msg_area] = mainRoadObjInst

    def get_InternalRoad_details(self):

        pop_msg_area = LayerMaster.INTERNALROAD.value
        internalRoadObjInst = ObjectByType(pop_msg_area)

        if (self.layerDict.get(LayerMaster.INTERNALROAD.value, 0) != 0):

            internalRoadAreaPlots = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, True, False)

            internalRoadNames = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)

            internalRoadObjInst.setBaseList(internalRoadAreaPlots)
            internalRoadObjInst.setBaseUnitNames(internalRoadNames)

    def get_GridRoad_details(self):

        pop_msg_area = LayerMaster.GRIDROAD.value
        gridRoadObjInst = ObjectByType(pop_msg_area)

        if (self.layerDict.get(LayerMaster.GRIDROAD.value, 0) != 0):

            gridRoadAreaPlots = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, True, False)

            gridRoadNames = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)

            gridRoadObjInst.setBaseList(gridRoadAreaPlots)
            gridRoadObjInst.setBaseUnitNames(gridRoadNames)

    def get_Roadwidening_details(self):

        pop_msg_area = LayerMaster.ROADWIDENING.value
        pop_msg_refid = "1.2"
        reservedRoadObjInst = ObjectByType(pop_msg_area)
        reservedRoadDict = reservedRoadObjInst.getBaseUnitDict()
        reservedRoadList = reservedRoadObjInst.getBaseUnitFinalList()

        if (self.layerDict.get(LayerMaster.ROADWIDENING.value, False) != False):
            reservedRoadAreaPlots = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, True, False)

            reservedRoadNames = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)

            pop_dict_msg = populateIndivPolyListObj(pop_msg_area, reservedRoadAreaPlots, reservedRoadNames,
                                                    reservedRoadList, reservedRoadDict, None)
            resultCode = pop_dict_msg.get("result")
            if pop_dict_msg == None or resultCode == "error":
                get_current_logger().error(
                    f"{pop_msg_refid} Error processing [ {pop_msg_area} ] Area Section Return is {pop_dict_msg}")
            else:
                if (resultCode == "OK"):
                    get_current_logger().info(f"{pop_msg_refid} Section [ {pop_msg_area} ] Area : Completed ")
                    areaObjList = pop_dict_msg.get("data_list")

                    # refactor-3
                    areaObjDict = pop_dict_msg.get("data_dict", None)

                    # overwrite with the data returned from function
                    reservedRoadObjInst.setBaseUnitDict(areaObjDict)
                    reservedRoadObjInst.setBaseUnitFinalList(areaObjList)

                    # combined objects
                    self.combinedObjects[pop_msg_area] = reservedRoadObjInst

    def get_OpenLayout_details(self):

        if (self.layerDict.get(LayerMaster.OPENLAYOUT.value, 0) != 0):
            pop_msg_area = LayerMaster.OPENLAYOUT.value
            indivObjInst = ObjectByType(pop_msg_area)

            subPlots1 = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, True, False)

            pltNames = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)

            indivObjInst.setBaseList(subPlots1)
            indivObjInst.setBaseUnitNames(pltNames)

    def get_MarginLine_details(self):

        if (self.layerDict.get(LayerMaster.MARGINLINE.value, 0) != 0):
            pop_msg_area = LayerMaster.MARGINLINE.value
            marginObjInst = ObjectByType(pop_msg_area)

            marginPlots = extractSubPlot(self.modelspace, pop_msg_area, '*', True, False)

            marginObjInst.setBaseList(marginPlots)

            self.combinedObjects[pop_msg_area] = marginObjInst

    def get_plinth_details(self):
        if (self.layerDict.get(LayerMaster.EXISTING_PLINTH_AREA.value, 0) != 0):
            pop_msg_area = LayerMaster.EXISTING_PLINTH_AREA.value

            existPlinthObjInst = ObjectByType(pop_msg_area)
            existPlinthPlots = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, True, False)

            existPlinthObjInst.setBaseList(existPlinthPlots)

    def get_prop_plinth_details(self):

        if (self.layerDict.get(LayerMaster.PROPOSED_PLINTH_AREA.value, 0) != 0):
            pop_msg_area = LayerMaster.PROPOSED_PLINTH_AREA.value
            propPlinthObjInst = ObjectByType(pop_msg_area)

            propPlinthPlots = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, True, False)

            propPlinthObjInst.setBaseList(propPlinthPlots)

    def get_buaBeforeConssetion_details(self):
        pop_msg_area = LayerMaster.BUA_BEFORE_CONCESSION.value
        buaBeforeConObjInst = ObjectByType(pop_msg_area)

        if (self.layerDict.get(LayerMaster.BUA_BEFORE_CONCESSION.value, False) != False):
            buaBeforeConAreaPlots = extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, True, False)

            extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)

            buaBeforeConObjInst.setBaseList(buaBeforeConAreaPlots)

    def get_leftownersLand_details(self):
        pop_msg_area = LayerMaster.LEFTOVEROWNERSLAND.value

        ObjectByType(pop_msg_area)

        if (self.layerDict.get(LayerMaster.LEFTOVEROWNERSLAND.value, False) != False):

            extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, True,
                                                     False)

            extractSubPlot(self.modelspace, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)

    def process_BuildingReport(self):

        self.combinedObjects["MASTERFLOORDICTKEY"] = self.masterFloorDict
        self.combinedObjects["MASTERBUILDINGDICTKEY"] = self.masterBuildingDict
        self.combinedObjects["modelspace"] = self.modelspace

        self.combinedObjects["INPUT_FILE"] = self.file_name

        if (len(self.warnings) > 0):
            self.combinedObjects["DRAWING_ERRORS"] = "|".join(self.warnings)

        try:
            self.status_dict["StepName"] = "Generating Report Data ... "

            print("self.combinedObjects",self.combinedObjects)
            reportgen_obj=GenReportData(self.request_id,self.combinedObjects,self.file_name,self.dxf_dir,self.status_dict,self.requesttimeobj)
            res=reportgen_obj.getReport_details()

            get_current_logger().debug("genBuildingReport Output " + str(res))

            self.responsedict['planType'] = 'Building_Layout'
            self.responsedict['responseCode'] = res.get("responseCode")
            if (res["responseCode"] == FAIL_CODE):
                self.responsedict['error_category'] = "Problem Generating Report"
                self.responsedict['errors'] = res.get("errors", "")
                self.responsedict['dwgExtract'] = []
                self.status_dict["StepName"] = "Problem Generating Report."

            elif (res["responseCode"] == SUCCESS_CODE):
                self.responsedict['dwgExtract'] = res.get("dwgExtract", [])
                self.responsedict['error_category'] = ""
                self.responsedict['errors'] = ""

                self.status_dict["StepName"] = "Generated Report Data Completed."

            else:
                self.responsedict['error_category'] = "Failure code "
                self.responsedict['errors'] = ""

        except:
            # Get current system exception
            ex_type, ex_value, ex_traceback = sys.exc_info()

            # Extract unformatter stack traces as tuples
            trace_back = traceback.extract_tb(ex_traceback)

            # Format stacktrace
            stack_trace = list()

            for trace in trace_back:
                stack_trace.append(
                    "File : %s , Line : %d, Func.Name : %s, Statement : %s" % (
                        trace[0], trace[1], trace[2], trace[3]))

            get_current_logger().error(stack_trace)

            self.responsedict['responseCode'] = FAIL_CODE
            self.responsedict['error_category'] = "Failure code  - Server Error"
            self.responsedict['errors'] = ['Problem Generating Report']
            self.responsedict['errorList'] = str(stack_trace)
            self.responsedict['dwgExtract'] = []
            self.status_dict["StepName"] = "Problem Generating Report."

    def adding_basicdata(self):

        self.responsedict['requestid'] = self.request_id
        self.responsedict['input'] = self.dxf_file
        self.combinedObjects["INPUT_FILE"] = self.file_name
        self.combinedObjects["DWG_DIR"] = self.dwg_dir
        self.combinedObjects["DXFFILE_DIR"] = self.dxf_dir

    def analyzeAndcheckRequired_data(self):
        layerDict = dict()

        for layer in self.dxf_file.layers:
            layerDict[layer.dxf.name] = str(layer.is_on())

        # check mandatory open layout checks
        layers_check = []

        for opLay in MANDATORY_LAYERS_FOR_PLAN_TYPE['Building_Layout']:

            if (opLay not in layerDict):
                layers_check.append("Layer " + opLay + " is required but is not found. Layer names are case sensitive.")

            elif (layerDict.get(opLay, 'False') == 'False'):
                # problem with mandatory layers
                layers_check.append(" Layer " + opLay + " should be Visible but is " + layerDict.get(opLay, 'False'))

        # 09/09/2024 remove the check orig:  >0 flipped
        if (len(layers_check) > 0):
            self.responsedict['responseCode'] = FAIL_CODE
            self.responsedict['error_category'] = "MISSING LAYERS"
            self.responsedict['errors'] = "|".join(layers_check)
            self.responsedict['planType'] = 'Building_Layout'
            self.responsedict['dwgExtract'] = []
            # return  self.responsedict
            get_current_logger().info(self.responsedict)
            get_current_logger().error("|".join(layers_check))
            raise Exception("Layer Validation Error")

        dwgCountsDict = analyzeDrawing(self.modelspace)

        if (self.request_params is not None):
            self.request_params['drawing_filename'] = str(self.file_name[:-4])
            self.combinedObjects['request_params'] = self.request_params
            self.combinedObjects['dwg_layers'] = layerDict
            self.combinedObjects['modelspace'] = self.modelspace
            self.combinedObjects['dwg_counts'] = dwgCountsDict


    def execute_step(
            self,
            step_no,
            total_step,
            step_name,
            step_function
    ):

        try:

            start_time = time.time()

            get_current_logger().info("=" * 80)
            get_current_logger().info(
                f"Step{step_no}/{total_step} STARTED : {step_name}"
            )
            get_current_logger().info("=" * 80)

            # -----------------------------------
            # PROCESSING STATUS
            # -----------------------------------

            processing_steps_dict = dict()

            processing_steps_dict["CurrentStep"] = (
                f"{step_name} Processing ..."
            )

            processing_steps_dict["Progress"] = (
                self.progress
            )

            processing_steps_dict["Steps"] = (
                f"{step_no}/{total_step}"
            )

            processing_steps_dict["TotalTime"] = (
                "0.0 sec"
            )

            self.status_dict["Status"] = (
                "Processing ..."
            )

            self.status_dict["Step_data"] = (
                processing_steps_dict
            )

            # send_status(
            #     self.request_id,
            #     self.status_dict,
            #     self.requesttimeobj
            # )

            # IMPORTANT
            # Gives frontend render time
            # time.sleep(1)

            # -----------------------------------
            # EXECUTE STEP
            # -----------------------------------

            step_function()

            # -----------------------------------
            # PROGRESS CALCULATION
            # -----------------------------------

            self.progress = int(
                (step_no / total_step) * 100
            )

            main_completed_progress = (
                    self.main1min_progress +
                    int(
                        (step_no / total_step)
                        * (
                                self.main1max_progress
                                - self.main1min_progress
                        )
                    )
            )

            elapsed = round(
                time.time() - start_time,
                2
            )

            # -----------------------------------
            # COMPLETED STATUS
            # -----------------------------------

            completed_steps_dict = dict()

            completed_steps_dict["CurrentStep"] = (
                f"{step_name} Completed."
            )

            completed_steps_dict["Steps"] = (
                f"{step_no}/{total_step}"
            )

            completed_steps_dict["Progress"] = (
                self.progress
            )

            completed_steps_dict["TotalTime"] = (
                f"{elapsed} sec"
            )

            self.status_dict["Status"] = (
                "Processing ..."
            )

            self.status_dict["Progress"] = (
                main_completed_progress
            )

            self.status_dict["Step_data"] = (
                completed_steps_dict
            )

            # send_status(
            #     self.request_id,
            #     self.status_dict,
            #     self.requesttimeobj
            # )

            # time.sleep(0.5)

            get_current_logger().info(
                f"Step{step_no}/{total_step} "
                f"COMPLETED : {step_name} "
                f"| Time Taken : {elapsed} sec"
            )

        except Exception as e:

            elapsed = round(
                time.time() - start_time,
                2
            )

            error_msg = {
                "step": step_no,
                "step_name": step_name,
                "error": str(e),
                "time_taken": elapsed
            }

            self.errors.append(error_msg)

            get_current_logger().info("=" * 80)
            get_current_logger().info(
                f"{step_no} FAILED : {step_name}"
            )
            get_current_logger().info(
                f"ERROR : {str(e)}"
            )
            get_current_logger().info(
                traceback.format_exc()
            )
            get_current_logger().info("=" * 80)

            # -----------------------------------
            # FAILED STATUS
            # -----------------------------------

            failed_steps_dict = dict()

            failed_steps_dict["CurrentStep"] = (
                f"{step_name} Failed."
            )

            failed_steps_dict["Steps"] = (
                f"{step_no}/{total_step}"
            )

            failed_steps_dict["Progress"] = (
                self.progress
            )

            failed_steps_dict["TotalTime"] = (
                f"{elapsed} sec"
            )

            self.status_dict["Status"] = (
                "Failed"
            )

            self.status_dict["Progress"] = (
                self.progress
            )

            self.status_dict["Step_data"] = (
                failed_steps_dict
            )

            self.status_dict["Error"] = (
                self.responsedict.get(
                    "errors",
                    "DXF Processing Error"
                )
            )

            # send_status(
            #     self.request_id,
            #     self.status_dict,
            #     self.requesttimeobj
            # )

            raise

    def main(self):

        steps=[("BASIC_DATA",self.adding_basicdata),
         ("ANALYZING_DATA",self.analyzeAndcheckRequired_data),
         ("BUILDING_DETAILS",self.get_building_details),
         ("FLOOR_DETAILS",self.get_floor_details),
         ("CARPETAREA_DETAILS",self.get_carpetarea_details),
         ("ROOM_DETAILS", self.get_room_details),
         ("MORTGAGE_AREA_DETAILS",self.get_mortgagearea_details),
         ("ACCESSORYUSE_DETAILS",self.get_accessoryUsedetails),
         # ("COURTYARD_DETAILS",self.get_courtyard_details),
         ("VENTILATION_SHAFT_DETAILS",self.get_ventiShaft_details),
         ("SLABVOID_DETAILS",self.get_slabVoid_details),
         ("RESIBUA_DETAILS",self.get_resibua_details),
         ("COMMBUA_DETAILS",self.get_commbua_details),
         ("INDBUA_DETAILS",self.get_indbua_details),
         ("SPECIALUSE_DETAILS",self.get_specialbua_details),
         ("RAMP_DETAILS",self.get_ramp_details),
         ("FLOORINSECTION_DETAILS",self.get_floorinsection_details),
         ("PARKING_DETAILS",self.get_parking_details),
         ("PASSAGE_DETAILS",self.get_passage_details),
         ("LIFT_DETAILS",self.get_lift_details),
         ("STAIRCASE_DETAILS",self.get_stailcase_details),
         ("BALCONY_DETAILS",self.get_balcony_details),
         ("PLOT_DETAILS",self.get_plot_details),
         ("NETPLOT_DETAILS",self.get_netplot_details),
         ("PROPOSEDWORK_DETAILS",self.get_proposedwork_details),
         ("NETPLOT_FROM_AREATABLE",self.get_netplotFromareatable_details),
         ("PROPOSEDWORK_FROM_AREATABLE",self.get_propworkFromareatable_details),
         ("ORGANIZEDOPENSPACE_DETAILS",self.get_OrganizedOpenSpace_details),
         ("EXISTINGSTRUCTURE_DETAILS",self.get_ExistingStructure_details),
         ("ELECTRICLINE_DETAILS",self.get_ElectricLine_details),
         ("MAINROAD_DETAILS",self.get_MainRoad_details),
         ("INTERNALROAD_DETAILS",self.get_InternalRoad_details),
         ("GRIDROAD_DETAILS",self.get_GridRoad_details),
         ("ROAD_WIDENING_DETAILS",self.get_Roadwidening_details),
         ("OPENLAYOUT_DETAILS",self.get_OpenLayout_details),
         ("MARGINELINE_DETAILS",self.get_MarginLine_details),
         ("PLINTH_DETAILS",self.get_plinth_details),
         ("PROP_PLINTH_DETAILS",self.get_prop_plinth_details),
         ("BEFORE_CONSESSION_DETAILS",self.get_buaBeforeConssetion_details),
         ("LEFTOWNERSLAND_DETAILS",self.get_leftownersLand_details),
         ]

        total_steps = len(steps)

        get_current_logger().info("=" * 100)
        get_current_logger().info("BUILDING PROCESS STARTED")
        get_current_logger().info("=" * 100)

        for index, (step_name, step_function) in enumerate(steps, start=1):


            self.execute_step(
                index,
                total_steps,
                step_name,
                step_function
            )

        self.process_BuildingReport()


        return self.responsedict