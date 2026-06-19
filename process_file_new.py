
from digit_domain import BuildingName, Floor, BldgBaseObj,IndivSubPlot
from digit_utils_openlayout import extractMaxRoadWidthFromDict

from AnalyzeDrawingUtil import analyzeDrawingMsp
from digit_utils_buildings import (re_round, LayerMaster, getMinWidthIrregularObjects,
                                   extract_dimensions_fromtext, calc_gradient, DxfPoly, extractStairsHeightInfo)

import shapely.wkt
import re
import sys
import os
import math
import ezdxf
from shapely.geometry import Polygon, LineString,Point
from logging_config import get_current_logger
from ProcessOpenLayout import ProcessOpenLayout
from BuildingProcess import ProcessBuilding

import logging
logging.getLogger("ezdxf").setLevel(logging.ERROR)

SUCCESS_CODE=0
FAIL_CODE=99
MANDATORY_LAYERS_FOR_PLAN_TYPE= {
'Open_Layout' : ['_Plot', '_IndivSubPlot',  '_OrganizedOpenSpace',  '_InternalRoad'],
# 'OpenVillas_Layout':['_Plot', '_OrganizedOpenSpace', '_Floor', '_CarpetArea','_NetPlot', '_MarginLine','_FloorInSection' ,'_Room','_BuildingName','_Window','_Door'],
'Building_Layout' : ['_Floor', '_CarpetArea', '_OrganizedOpenSpace','_NetPlot', '_MarginLine','_FloorInSection' ,'_Room','_BuildingName','_Window','_Door']
 }
TEXT_ELEMENTS_FROM_DWG ={"Proposed Coverage" : ""}  #disabled others
translation = {39: None}

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

def doObjectsTouchEachOther(sourcePoly, targetPoly):
    if (sourcePoly is None or targetPoly is None):
        return False

    try:

        target_coords = list(targetPoly.exterior.coords)
        targetObj = re_round(target_coords, 2)
        targetPoly = Polygon(targetObj)

        source_plot_coords = list(sourcePoly.exterior.coords)

        sourceList = re_round(source_plot_coords, 2)
        sourceObj = Polygon(sourceList)

        if (sourceObj.touches(targetPoly) or sourceObj.intersects(targetPoly)):
            return True
        else:
            return False
    except:
        get_current_logger().exception(' Unable to check if objects are touching - returning False ')
        return False


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
            # if (ptId.handle in ['29','33','45']):
            #	logLevel='verbose'
            get_current_logger().debug("point ID " + str(ptId.handle))
            xyP = ptId.get_points()[0].split(" ")
            # need this for splay layer for uniqueness of point. you can have multiple splays in a plot
            xyP_Str = xyP[0], "-", xyP[1]
            # @TO DO : Fix bulge for arc
            # bulge = xyP[4]
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

def populateBldgPolyListObj(masterFloorDict, layerName, dxfOfObjs, objectTDict, updateMasterFloor: True, parent: None):

    parentList = [LayerMaster.AREATABLE.value \
        , LayerMaster.ORGOPENSPACE.value]
    debugLevel = 'debug'

    if (layerName in ['_ResiBUAOutline']):
        debugLevel = 'verbose'

    if (layerName is None or dxfOfObjs is None):
        error_msg = "One or more required inputs for the method are empty, returning error response "
        get_current_logger().error(" populateBldgPolyListObj  :: " + error_msg)
        return {"result": "error", "msg": error_msg}

    skippedList = []

    # iterate through subPlots
    processedObjectTDict = dict()
    for plotObj in dxfOfObjs:
        if (plotObj.handle not in processedObjectTDict):
            processedObjectTDict[plotObj.handle] = plotObj.handle
        else:
            continue

        get_current_logger().debug(f"Layer {layerName} processsing : {plotObj.handle} points {plotObj.get_points()} updateMasterFloor Flag : {updateMasterFloor}")

        polyStr = str(plotObj.get_points())[1:-1].translate(translation)
        get_current_logger().debug(f"polyStr Polygon = {polyStr}")
        polyPoints = 'POLYGON ((' + polyStr + '))'
        get_current_logger().debug(polyPoints)
        lwpoly = None
        try:
            lwpoly = shapely.wkt.loads(polyPoints)
            # get minimum bounding box around polygon
            box = lwpoly.minimum_rotated_rectangle
            get_current_logger().debug(f"box type {type(box)}")
            get_current_logger().debug(debugLevel, " value " + str(box))
        except:
            ex_type, ex_value, ex_traceback = sys.exc_info()

            s_msg = "Problem processing Layer -" + layerName + "  DXF handle -" + plotObj.handle + " Skipping record due to " + str(
                ex_value)
            print(s_msg)
            skippedList.append(s_msg)

            break

        # print( '\t matched ' + ptId.handle + " (x,y) " + str(xyP) + " polyObj#  handle : "  + plotObj.handle + " points: "  +  str(plotObj.get_points()) )

        # get coordinates of polygon vertices
        x, y = box.exterior.coords.xy

        # get length of bounding box edges
        edge_length = (Point(x[0], y[0]).distance(Point(x[1], y[1])), Point(x[1], y[1]).distance(Point(x[2], y[2])))
        # get length of polygon as the longest edge of the bounding box
        length = max(edge_length)
        # get width of polygon as the shortest edge of the bounding box
        width = min(edge_length)
        height = width if layerName == LayerMaster.FLOORINSECTION.value else 0.0
        # reset width
        if layerName == LayerMaster.FLOORINSECTION.value:
            width = 0.0

        get_current_logger().debug(f"Plot: {plotObj.handle} area: {lwpoly.area} length: {length} height:{height} width: {width} coordinates :{lwpoly}")

        # loop through each object list and see where this object belongs
        if (layerName not in parentList and updateMasterFloor == True and masterFloorDict != None and len(
                masterFloorDict) > 0):
            for flrId, floorObj in masterFloorDict.items():
                get_current_logger().debug('checking floor# ', flrId)
                # check which floor this object belongs to
                fpolygon = floorObj.fpolygon
                if (fpolygon.contains(lwpoly)):
                    get_current_logger().debug(" Object " + plotObj.handle + " is with in floor  " + floorObj.fname)

                    p5 = BldgBaseObj(flrId, None, plotObj.handle, layerName, lwpoly, length, width, height, lwpoly.area,
                                     plotObj.handle)
                    floorObj.add_tofloor(layerName, p5)

                    # replace the Floor Obj with updatedFloor Obj
                    masterFloorDict[flrId] = floorObj
                    # flooridx = flooridx + 1
                    if plotObj.handle not in objectTDict:
                        objectTDict[plotObj.handle] = p5
                    # if match found exit the loop without checking other points
                    break  # if you can find the first floor obj , it will not be part of two floors.
        elif (layerName not in parentList and updateMasterFloor == False):

            p5 = BldgBaseObj(plotObj.handle, None, plotObj.handle, layerName, lwpoly, length, width, height,
                             lwpoly.area, plotObj.handle)
            if plotObj.handle not in objectTDict:
                objectTDict[plotObj.handle] = p5
                # if match found exit the loop without checking other points
                break  # if you can find the first floor obj , it will not be part of two floors.

        elif (parent is not None and layerName in parentList and plotObj.handle not in objectTDict):
            # Main table logic goes here
            # check if current lwpoly is part of the parent and map it in layername
            parentName = ""
            for parentKey, parentValue in parent.items():
                if (parentValue.polygon.contains(lwpoly)):
                    get_current_logger().error("Object is part of the Parent " + parentValue.name)
                    parentName = parentKey + "|" + plotObj.handle
                    p5 = BldgBaseObj(parentName, None, plotObj.handle, layerName, lwpoly, length, width, height,
                                     lwpoly.area, plotObj.handle)
                    objectTDict[plotObj.handle] = p5

                    break  # single object can belong to 1 parent
        else:
            get_current_logger().warning("Unhandled condition ")
    processedObjectTDict = ''
    if (len(skippedList) == 0):
        resultStatus = "OK"
        return {"result": resultStatus, "data": objectTDict, "masterFloorDict": masterFloorDict}

    else:
        resultStatus = "warning"
        return {"result": resultStatus, "data": objectTDict, "masterFloorDict": masterFloorDict,
                "msg": str(skippedList)}


""" poplulate the <IndivSubPlot> type of objects List and Dict for
a given Layer from Plot of Objects"""
"***  for specific plot types need to find the mtext like plot # within the plot  ***"


def populateIndivPolyListObjNoNames(layerName, subPlots, plotList, plotDict, internalRoadList: None):
    if (layerName is None or subPlots is None or plotList is None):
        error_msg = "One or more of required inputs are None. Returning error response for {layerName}"
        get_current_logger().error(" populateIndivPolyListObj :: " + error_msg)
        return {"result": "error", "msg": error_msg}

    get_current_logger().info(f"subplots len {len(subPlots)}")
    # iterate through subPlots
    processedPlotDict = dict()

    for plotObj in subPlots:
        get_current_logger().debug("processsing handle # " + str(plotObj.handle) + " points : " + str(
            plotObj.get_points()) + " isclosed : " + str(plotObj.isClosed()))

        if (plotObj.handle not in processedPlotDict):
            processedPlotDict[plotObj.handle] = plotObj.handle
        else:

            continue


        if plotObj.isClosed() == False:
            get_current_logger().warning('polyline not closed object breaking loop')
            break

        polyStr = str(plotObj.get_points())[1:-1].translate(translation)
        # printLog ('debug', "Polygon String coordates " , polyStr)
        # create a ploygon
        polyPoints = 'POLYGON ((' + polyStr + '))'

        lwpoly = shapely.wkt.loads(polyPoints)
        isIrregularObject = False

        # get minimum bounding box around polygon
        box = lwpoly.minimum_rotated_rectangle
        # get coordinates of polygon vertices
        x, y = box.exterior.coords.xy
        # get length of bounding box edges
        edge_length = (Point(x[0], y[0]).distance(Point(x[1], y[1])), Point(x[1], y[1]).distance(Point(x[2], y[2])))
        # get length of polygon as the longest edge of the bounding box
        length = max(edge_length)
        # get width of polygon as the shortest edge of the bounding box
        width = min(edge_length)
        # printLog('debug', "Matched point : "  +  str(xyP_Str) + " with Plot: " , ptId.handle , " area: " , lwpoly.area, ", length: ", length,  ", width: ",  width ," , coordinates :", str(lwpoly))

        area_polygon = lwpoly.area
        get_current_logger().debug(' area before ' + str(area_polygon))

        # if arc reduce segment area from polygon
        if (plotObj.hasBulge == True):
            seg_area = plotObj.get_segment()
            bounding_box2d = ezdxf.math.BoundingBox2d([xy[0:2] for xy in list(plotObj.get_rawpoints())])

            get_current_logger().debug("box dimensions " + str(bounding_box2d.size))
            width, length = bounding_box2d.size
            get_current_logger().debug(f"width and length dimensions {round(width, 2)} : {round(length, 2)}")

            if (seg_area < 0):
                area_polygon = area_polygon + seg_area
            else:
                area_polygon = area_polygon - seg_area

            get_current_logger().debug('segment area ' + str(seg_area) + ' splay area is now ' + str(area_polygon))

        if (
                layerName == "_Splay" or layerName == "_MainRoad" or layerName == "_InternalRoad" or layerName == "_RoadWidening" \
                or layerName == LayerMaster.EXISTING_PLINTH_AREA.value or layerName == LayerMaster.PROPOSED_PLINTH_AREA.value \
                or layerName == LayerMaster.BUA_BEFORE_CONCESSION.value or layerName == LayerMaster.TRANSFER_OF_SETBACKS.value) and plotObj.handle not in plotDict:
            p6 = IndivSubPlot(plotObj.handle, layerName, lwpoly, length, width, area_polygon, plotObj.handle)
            # set color since 10/30/2022 for identifiying the transfer of setbacks by color
            print('verbose', 'Color of object ', str(plotObj.getColor()))

            p6.setColor(str(plotObj.getColor()))

            # need this to check splay dimensions based on the road width -
            if (layerName == "_Splay"):
                bbox = lwpoly.bounds
                splayPoly = shapely.geometry.box(*bbox, ccw=True)
                get_current_logger().debug(f"SPLAY handle# {plotObj.handle}")
                abuttingroad_frontage = extractAbuttingRoadForSplay(splayPoly, internalRoadList, plotObj.handle)
                get_current_logger().debug(f"SPLAY abutting ******* {abuttingroad_frontage}")
                p6.add_frontage_abuttingroad(abuttingroad_frontage)

            plotList.append(p6)
            plotDict[plotObj.handle] = p6

        elif (layerName == "_IndivSubPlot") and plotObj.handle not in plotDict:
            abuttingroad_frontage = extractAbuttingRoadForIndivPlot(layerName, ' blank ', lwpoly, internalRoadList,
                                                                    plotObj.handle)
            get_current_logger().debug("abutting frontage value " + str(abuttingroad_frontage))
            p6 = IndivSubPlot(plotObj.handle, layerName, lwpoly, length, width, area_polygon, plotObj.handle)
            p6.add_frontage_abuttingroad(abuttingroad_frontage)
            plotList.append(p6)
            plotDict[plotObj.handle] = p6

    return {"result": "OK", "data_dict": plotDict, "data_list": plotList}


def parse_points_fast(raw_points):
    cleaned = []

    for pt in raw_points:
        try:
            # 🔥 fast split (no regex, no heavy ops)
            x_str, y_str = pt.split()
            cleaned.append((float(x_str), float(y_str)))
        except Exception:
            # skip bad values like ".", "", None
            continue

    return cleaned

def get_length_width(lwpoly):
    """
    Compute accurate length and width of a polygon
    using minimum rotated rectangle.

    Returns:
        (length, width)
    """

    # Safety check
    if lwpoly is None or lwpoly.is_empty:
        return 0.0, 0.0

    try:
        # Get rotated rectangle
        rect = lwpoly.minimum_rotated_rectangle
        coords = list(rect.exterior.coords)

        # Need at least 3 points
        if len(coords) < 3:
            return 0.0, 0.0

        # First 3 points define 2 edges
        p0 = Point(coords[0])
        p1 = Point(coords[1])
        p2 = Point(coords[2])

        # Edge lengths
        edge1 = p0.distance(p1)
        edge2 = p1.distance(p2)

        # Assign properly
        if edge1 >= edge2:
            length = edge1
            width = edge2
        else:
            length = edge2
            width = edge1

        return round(length, 2), round(width, 2)

    except Exception as e:
        # fallback (safe mode)
        minx, miny, maxx, maxy = lwpoly.bounds
        dx = maxx - minx
        dy = maxy - miny

        length = max(dx, dy)
        width = min(dx, dy)

        return round(length, 2), round(width, 2)


def populateBldgListObj(masterFloorDict, masterBuildingDict, layerName, parent: None, subtype: None, dxfOfObjs,
                        dxfOfObjNames, objectTDict, updateMasterFloor: bool = True, ignoreClosedFlag: bool = False):

    parentList = [LayerMaster.EXISTINGSTRUCTURE.value, \
                  LayerMaster.PROPOSEDWORK.value, LayerMaster.COMPOUNDWALL.value]

    debugLayerList = [
        'dummy']  # ,LayerMaster.ROOM.value LayerMaster.FLOORINSECTION.value, LayerMaster.PARKING.value LayerMaster.MORTGAGEAREA.value
    if (layerName in debugLayerList):
        debugLevel = 'verbose'
        print('Overriding log level to ** ' + debugLevel)

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
                    # print( '\t matched ' + ptId.handle + " (x,y) " + str(xyP) + " polyObj#  handle : "  + objToProcess.handle + " points: "  +  str(objToProcess.get_points()) )
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
                        # printLog('debug', 'arc  ' + str(p1) + " to : " + str(p2) + "distance: " + str(distanceP1P2))
                        # printLog('debug', 'arc radius ' + str(venty.dxf.radius))
                        # printLog('debug',
                        #          'arc angle ' + str(venty.dxf.start_angle) + " end angle " + str(venty.dxf.end_angle))

                        # if splay check radius before adding to object
                        if (layerToSearch == LayerMaster.SPLAY.value):
                            # if (venty.dxf.radius <= 50):
                            # pass chord len which is half of distanceP1P2
                            polyObj.set_bulge_radius_angle_chordlen(nonZeroBulge[0], venty.dxf.radius,
                                                                    venty.dxf.start_angle, (distanceP1P2 / 2))
                        else:
                            # pass chord len which is half of distanceP1P2
                            polyObj.set_bulge_radius_angle_chordlen(nonZeroBulge[0], venty.dxf.radius,
                                                                    venty.dxf.start_angle, (distanceP1P2 / 2))

                    else:
                        # printLog('warning', 'not handled for ' + venty.dxftype() == 'ARC')
                        get_current_logger().warning('not handled for ' + venty.dxftype() == 'ARC')

                retList.append(polyObj)

        if entity.dxftype() == 'TEXT' or entity.dxftype() == 'MTEXT':
            text_str = ""
            if (entity.dxftype() == 'TEXT'):
                text_str = entity.dxf.text
            # printLog ('debug', '\t Text : attributes ht, width, rotation ', str(entity.dxf.height), ' , ', str(entity.dxf.width), ', ', str(entity.dxf.rotation), ', ', entity.dxf.style)

            else:
                text_str = entity.text
            # printLog ('debug', '\t MText : attributes char height , width, direction : ', str(entity.dxf.char_height), ',', str(entity.dxf.width), ',',  entity.dxf.text_direction,   )

            # check for special chars and clean them
            specialChar = text_str.find(';')
            # print('special char '	, specialChar)
            if (specialChar > -1):
                text_str = text_str[specialChar + 1:]
                # print('special char is removed  now ', text_str)
                # check if it has } tag
                endTag = text_str.find('}')
                if (endTag > -1):
                    # print('end tag removed string  is now ', text_str)
                    text_str = text_str[:endTag]

            pointObj = DxfPoly(layerToSearch, entity.dxftype(), text_str)
            pointObj.setIsClosed(1)

            # printLog('debug', '\tText - Location: ', text_str, "=", entity.dxf.insert)
            xypoint = str(entity.dxf.insert.x) + " " + str(entity.dxf.insert.y)
            pointObj.add_2dpoint(xypoint)
            retList.append(pointObj)

    return retList

def getLayerCount(msp, layerToSearch, objectType):
	""" Returns the count of Objects for a given layer """
	qry_str = objectType +  '[layer==\"' + layerToSearch + '\"]'
	# printLog ('debug', '**** QRY STR ' + qry_str )

	qry_splots = msp.query(qry_str)

	# printLog ('debug', '\t Search in layer:' + layerToSearch +  ' for objectype: ' + objectType + ' found count # ', len(qry_splots)  )
	return len(qry_splots)

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

# ==============================
# STAIRCASE PROCESSING (PURE PYTHON)
# ==============================

def process_staircase(
    floorInSection_df,
    stairCaseUnitsDict,
    stairsRiserTreaddf,
    floorNameMapping,
    required_staircaseFlightWidth,
    required_staircaseTreadWidth,
    required_staircaseRiserHeight,
    STAIRCASE_RISER_ALLOWED_COUNT
):

    # ==============================
    # STEP 1: Floor Data Mapping
    # ==============================
    floorInSectionData = {}

    for item in floorInSection_df:
        parent = item.get("parent", "").replace(" ", "")
        name = item.get("name", "").replace(" ", "")
        key = f"{parent}|{name}"
        floorInSectionData[key] = item.get("height", 0)

    floorInSectionSortedDict = dict(sorted(floorInSectionData.items()))

    # ==============================
    # STEP 2: Stair Raw Data
    # ==============================
    stair_list = [fs.get_dict() for fs in stairCaseUnitsDict.values()]

    # ==============================
    # STEP 3: Prepare Base Stair Report
    # ==============================
    stair_for_report = []

    for stair in stair_list:
        stair_for_report.append({
            "handle": stair.get("handle"),
            "stairId": stair.get("handle"),
            "Floor": stair.get("parent", "").replace("|", "-"),
            "Stair Name": stair.get("name"),
            "FLIGHT_WIDTH_METERS_REQUIRED": round(required_staircaseFlightWidth, 2),
            "FLIGHT_WIDTH_METERS_PROPOSED": round(stair.get("width", 0) / 2, 2)
        })

    # ==============================
    # STEP 4: Stair → Floor Mapping
    # ==============================
    stairIdFloorData = {}

    for stair in stair_list:
        stairIdFloorData[stair.get("handle")] = stair.get("parent", "").replace(" ", "")

    # ==============================
    # STEP 5: Extract Height Info
    # ==============================
    stairsHeightResult = extractStairsHeightInfo(
        floorInSectionSortedDict,
        floorNameMapping,
        stairIdFloorData
    )

    stairsData = stairsHeightResult.get("data", {})

    # ==============================
    # STEP 6: Final Merge + Calculation
    # ==============================
    final_result = []

    for stair in stair_for_report:

        stair_id = stair["stairId"]

        if stair_id not in stairsData:
            continue

        height = stairsData[stair_id]

        # find matching riser/tread data
        match = next((x for x in stairsRiserTreaddf if x["stairId"] == stair_id), None)

        if not match:
            continue

        tread_required = round(required_staircaseTreadWidth, 2)
        tread_proposed = round(match.get("tread_width", 0), 2)

        riser_height_perm = round(required_staircaseRiserHeight, 2)

        riser_height_prop = round(
            height / match.get("riser_count", 1) / match.get("no_of_flights", 1), 2
        )

        riser_allowed = STAIRCASE_RISER_ALLOWED_COUNT
        riser_proposed = match.get("riser_count", 0)

        raw_riser = match.get("raw_riser_count", 0)

        raw_riser_height = round(height / raw_riser, 2) if raw_riser else 0

        # ==============================
        # STATUS CHECK
        # ==============================
        status = "OK" if (
            stair["FLIGHT_WIDTH_METERS_PROPOSED"] >= stair["FLIGHT_WIDTH_METERS_REQUIRED"] and
            tread_proposed >= tread_required and
            riser_height_prop <= riser_height_perm and
            riser_proposed <= riser_allowed
        ) else "NOT OK"

        # ==============================
        # FINAL OUTPUT (SAME FORMAT)
        # ==============================
        final_result.append({
            **stair,
            "TREAD_WIDTH_METERS_REQUIRED": tread_required,
            "TREAD_WIDTH_METERS_PROPOSED": tread_proposed,
            "RISER_HEIGHT_METERS_PERMISSIBLE": riser_height_perm,
            "RISER_HEIGHT_METERS_PROPOSED": riser_height_prop,
            "RISER_NO_ONFLIGHT_PERMISSIBLE": riser_allowed,
            "RISER_NO_ONFLIGHT_PROPOSED": riser_proposed,
            "RAW_RISER_NO_PROPOSED": raw_riser,
            "RAW_RISER_HEIGHT_METERS_PROPOSED": raw_riser_height,
            "FLOOR_HEIGHT_PROPOSED": round(height, 2),
            "Status": status
        })

    return final_result


'''
 checks is a polygon is inside another polygon
return Floor Name or "N/A" (not found)

'''
# def extractAbuttingRoadForSplay
# loop through each splay find max abutting road and take that for calculation -

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

def processPlanBasedOnType(requestId, dwg_dir, dxffile_dir,inputFilename,
                           request_params: dict,status_dict,req_dttime_obj):


    from digit_utils_buildings import LayerMaster
    layerDict = dict()
    layerTypeDict = dict()
    response = dict()
    exception_msg = ""
    dwg = None
    msp = None
    ## READ Drawing FILE ##
    try:
        dxf_path=os.path.join(dxffile_dir,inputFilename)
        # get_current_logger().info(f"Reading DXF {dxf_path} File...")
        get_current_logger().info(f"Reading DXF {dxf_path} File...")
        status_dict["StepName"]=f"Reading {inputFilename} File ..."
        status_dict["Progress"]=12


        dwg = ezdxf.readfile(dxf_path)
        msp = dwg.modelspace()
        # get_current_logger().debug(f"Loaded ModelSpace From That {dxf_path} File.")
        get_current_logger().debug(f"Loaded ModelSpace From That {dxf_path} File.")

    except FileNotFoundError as fnf_error:
        msg=f"File doesnt exist {inputFilename} exception : {str(fnf_error)}"
        exception_msg=msg
        # server_logger.error(msg)
        get_current_logger().error(msg)

    except ezdxf.lldxf.const.DXFStructureError as dxerror:

        msg=f"Problem parsing the DXF file  : {str(dxerror)}"
        exception_msg=msg
        # server_logger.error(msg)
        get_current_logger().error(msg)

        # status_dict["Status"]= "Failed"
        # status_dict["Error"]= "Problem parsing the DXF file"

    if (request_params is None and inputFilename is None):

        msg=f"Missing or Invalid Request Parameters or InputFile."
        exception_msg = msg
        # server_logger.error(msg)
        get_current_logger().error(msg)

        request_params['drawing_filename'] = str(inputFilename[:-4])

    # 1 check if file is readable
    if (len(exception_msg) > 0):
        response['responseCode'] = FAIL_CODE
        response['error_category'] = "INVALID FILE"
        response['errors'] = exception_msg
        response['planType'] = ''
        response['dwgExtract'] = []
        # server_logger.error(f"InValid File:{exception_msg}.")
        get_current_logger().error(f"InValid File:{exception_msg}.")
        return response

    # server_logger.info('Extracting layers and Store Into Global layerDict...')
    get_current_logger().info('Extracting layers and Store Into Global layerDict...')
    # status_dict["StepName"]="Extracting layers ..."
    # status_dict["Progress"]=14

    for layer in dwg.layers:
        get_current_logger().debug(f"{layer.dxf.name} on {layer.is_on()}")
        layerDict[layer.dxf.name] = layer.is_on()

    # server_logger.info('Done .Extracting layers and Store Into Global layerDict.')
    get_current_logger().info('Done .Extracting layers and Store Into Global layerDict.')

    # server_logger.info("Checking PlanType Based Upon User and Files ...")
    get_current_logger().info("Checking PlanType Based Upon User and Files ...")

    # status_dict["StepName"]="Checking PlanType Based Upon User and Files ..."
    # status_dict["Progress"]=16


    checkLayerType = ['_IndFAR', LayerMaster.RESIDENCE.value, LayerMaster.INDUSTRIAL.value,
      LayerMaster.COMMERCIAL.value, LayerMaster.SPECIALUSE.value, LayerMaster.OPENLAYOUT.value]
    # server_logger.info(checkLayerType)
    if ((request_params.get('typeofplan', 0) != 'FireScrutiny')):
        # server_logger.info("Counting the LWPOLYLINE LayerWise...")
        get_current_logger().info("Counting the LWPOLYLINE LayerWise...")
        for layToCheck in checkLayerType:
            get_current_logger().info(f"{layToCheck}=={layerDict.get(layToCheck, 0)}")
            if (layerDict.get(layToCheck, 0) != 0 and layerDict[layToCheck] == True):
                cnt = getLayerCount(msp, layToCheck, LayerMaster.DWG_LWPOLYLINE.value)

                layerTypeDict[layToCheck] = cnt
            else:
                layerTypeDict[layToCheck] = 0

        # server_logger.info("Done.Counting the LWPOLYLINE LayerWise.")
        get_current_logger().info("Done.Counting the LWPOLYLINE LayerWise.")

    # server_logger.info(f"PlanType:{request_params.get('typeofplan', 0)},Layout:{request_params.get('layout', 0)}")
    get_current_logger().info(f"PlanType:{request_params.get('typeofplan', 0)},Layout:{request_params.get('layout', 0)}")

    if ((request_params.get('typeofplan', 0) != 'FirePlanScrutiny') and (
            request_params.get('layout', 0) == 'OpenLayout') and (
            layerTypeDict.get(LayerMaster.OPENLAYOUT.value, 0) > 0)):

        # server_logger.info(f'Processing That {inputFilename} File For OpenLayout...\n Calling that "processOpenLayout" Function')
        get_current_logger().info(f'Processing That {inputFilename} File For OpenLayout...\n Calling that "processOpenLayout" Function')

        # status_dict["StepName"]="Open Layout Processing ..."
        # status_dict["Progress"]=20

        openlayout_obj=ProcessOpenLayout(dwg,requestId,inputFilename,layerDict,request_params,status_dict,req_dttime_obj)

        return openlayout_obj.main()
        # return processOpenLayout(dwg, requestId, dwg_dir, dxffile_dir,json_req_dir ,inputFilename, request_params)

    if ((request_params.get('typeofplan', 0) != 'FirePlanScrutiny') and request_params.get('layout',0) == 'Building' and
            (layerTypeDict.get(LayerMaster.RESIDENCE.value, 0) > 0 or layerTypeDict.get(LayerMaster.COMMERCIAL.value,
                                                                                      0) > 0 \
           or layerTypeDict.get(LayerMaster.SPECIALUSE.value, 0) > 0 or layerTypeDict.get(LayerMaster.INDUSTRIAL.value,
                                                                                          0) > 0 \
           or layerTypeDict.get('_IndFAR', 0) > 0) \
            ):


        # server_logger.info(f'Processing That {inputFilename} File For Buildings...\n Calling that "processBuilding" Function')
        get_current_logger().info(f'Processing That {inputFilename} File For Buildings...\n Calling that "processBuilding" Function')

        status_dict["StepName"]="Building Layout Processing ..."
        status_dict["Progress"]=20

        process_bldg_obj = ProcessBuilding(dwg, requestId, inputFilename, dxffile_dir, layerDict, layerTypeDict,
                                           dwg_dir, request_params,status_dict,req_dttime_obj)

        get_status_data = process_bldg_obj.main()
        return get_status_data

        # return processBuilding(dwg, requestId, dwg_dir, dxffile_dir, json_req_dir, inputFilename, request_params)

    else:
        # server_logger.error(
        #     f"Unable to determine plan type for file {inputFilename}. "
        #     f"Expected types: Building or OpenLayout."
        # )
        get_current_logger().error(
            f"Unable to determine plan type for file {inputFilename}. "
            f"Expected types: Building or OpenLayout."
        )
        try:

            clean_layers = str(layerTypeDict).replace("'", "")
            exception_msg = (
                f"Unknown Layout, unable to determine the plan type.\n"
                f"Valid Layers: {LayerMaster.OPENLAYOUT.value} or "
                f"{LayerMaster.RESIDENCE.value} or "
                f"{LayerMaster.COMMERCIAL.value} or "
                f"{LayerMaster.INDUSTRIAL.value} or "
                f"{LayerMaster.SPECIALUSE.value} or _IndFAR.\n"
                f"Detected Layers: {clean_layers}\n"
                f"Unable to continue."
            )

            # server_logger.error(exception_msg)
            get_current_logger().error(exception_msg)

        except Exception as Exct:

            # server_logger.error('exception occured due to ' + str(Exct))
            get_current_logger().error('exception occured due to ' + str(Exct))

    if (len(exception_msg) > 0):
        response['responseCode'] = FAIL_CODE
        response['error_category'] = "Un Supported Plan"
        response['errors'] = exception_msg
        response['planType'] = ''
        response['dwgExtract'] = []

        # server_logger.debug(f"{inputFilename} Un Supported Plan Type.")
        get_current_logger().debug(f"{inputFilename} Un Supported Plan Type.")

        # status_dict["Status"] = "Failed"
        # status_dict["Error"] =exception_msg

        return response

# if __name__=="__main__":
#     DWG_DIR = "G:\MyProjects\FireBuildingsProject\FireBuildingsAPI\Dwg_files"
#     DXF_DIR = "G:/MyProjects/BPConnectProject/BPConnectAPI/DXF_files"
#     dxf_fileName = "90f6b268033d6b21-UD30Acre_(1).dxf"
#     request_params = {
#         "layout": "OpenLayout",
#         "subtype": "SUBPLOTS",
#         "purposecode": "O-1",
#         "typeofplan": "Hyderabad",
#         "username": "tsbpass-user1",
#     }
#     res = processPlanBasedOnType("xyz", DWG_DIR, DXF_DIR,dxf_fileName,request_params,{})
#     print(res)

# if __name__=="__main__":
#     DWG_DIR="G:\MyProjects\FireBuildingsProject\FireBuildingsAPI\Dwg_files"
#
#     DXF_DIR="G:/MyProjects/BPConnectProject/BPConnectAPI/DXF_files/"
#     dxf_fileName="4cef8950c634ca25-sap_ff.dxf"
#
#     request_params={
#                 "layout": "Building",
#                 "subtype": "STANDALONE",
#                 "purposecode": "A-4",
#                 "typeofplan": "Hyderabad",
#                 "username": "tsbpass-user1",
#                 "runOnlyCombinedUtil":"True"
#             }
#     res=processPlanBasedOnType("xyz",DWG_DIR,DXF_DIR,dxf_fileName,request_params,{},datetime.now())
#     print(res)
# #
# if __name__=="__main__":
#     DWG_DIR="G:\MyProjects\FireBuildingsProject\FireBuildingsAPI\Dwg_files"
#
#     DXF_DIR="G:/MyProjects/BPConnectProject/BPConnectAPI/DXF_files/"
#     dxf_fileName="6f19c3964568f717-45291_Resi_-_comm_2B_2_with_BUA_COn_(1).dxf"
#     request_params={
#                 "layout": "Building",
#                 "subtype": "STANDALONE",
#                 "purposecode": "A-4",
#                 "typeofplan": "Hyderabad",
#                 "username": "tsbpass-user1",
#             }
#     res=processPlanBasedOnType("xyz",DWG_DIR,DXF_DIR,DXF_DIR,dxf_fileName,request_params)
#     print(res)


# def generate_dxf(folder,filename,common_setbacks):
#
#     gen_dxf=modify_dxf.MODYFY_DXF()
#
#     gen_data=gen_dxf.generateDxf(folder,filename,commonSetbacks=common_setbacks)
#
#     return g