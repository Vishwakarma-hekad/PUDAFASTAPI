import time
from logging_config import get_current_logger
from digit_domain import IndivSubPlot
from AnalyzeDrawingUtil import analyzeDrawingMsp
from digit_utils_buildings import (LayerMaster,DxfPoly,re_round,extract_dimensions_fromtext,
                                   extract_road_width_fromtext,removeSpecialChars,getMinWidthIrregularObjects,
                                   mapCenterLinesWithinObjectList,getPointsAsListFromString,getMinWidthByCenterLine)
from digit_utils_openlayout import (get_mortgagedSubplots4OpenLayout,checkBufferZoneWaterBodiesLocationWithPlot,
                                    checkMainAndInternalRoadWidthsInOpenLayout,isChildFullyWithinParentObject,
                                    isChildWithinParentObject,checkCommonLayersInOpenLayout,extractMaxRoadWidthFromDict,
                                    checkAmentiesSocialInfra_OpenLayouts,checkFacilities_OpenLayouts,getInternalRoadWidth)
import ezdxf
import math
import shapely
from shapely.geometry import Polygon,Point,LineString
from shapely.strtree import STRtree
from digit_rules_v1 import callrule
from datetime import datetime
import sys
import traceback

SUCCESS_CODE=0
FAIL_CODE=99

translation = {39: None}
MANDATORY_LAYERS_FOR_PLAN_TYPE= {
'Open_Layout' : ['_Plot', '_IndivSubPlot',  '_OrganizedOpenSpace',  '_InternalRoad'],
# 'OpenVillas_Layout':['_Plot', '_OrganizedOpenSpace', '_Floor', '_CarpetArea','_NetPlot', '_MarginLine','_FloorInSection' ,'_Room','_BuildingName','_Window','_Door'],
'Building_Layout' : ['_Floor', '_CarpetArea', '_OrganizedOpenSpace','_NetPlot', '_MarginLine','_FloorInSection' ,'_Room','_BuildingName','_Window','_Door']
 }
def extractAbuttingRoadForIndivPlot(layerName: str, handle: str, plot_poly, road_list):
    # to be used for debugging
    printVerbose = False
    debugHandleList = []  # ['8','19','P-29', 'P-28','P-147','P-161']
    if (handle is not None and handle in debugHandleList):
        printVerbose = True

    abuttingDict = dict()
    onlyCoversDict = dict()
    onlyIntersectsDict = dict()

    if (plot_poly is None or road_list ==[]):
        return abuttingDict

    get_current_logger().debug(f'layerName : {layerName} ,  handle : {handle} , plot : {plot_poly} , road list : {road_list}')

    roadIndx = 0

    for road in road_list:
        road_coords = list(road.polygon.exterior.coords)
        get_current_logger().debug(f'road coords : {road_coords}')
        roadObj = re_round(road_coords, 1)
        roadPoly = Polygon(roadObj)
        get_current_logger().debug(f'processing road  {roadPoly}')


        rPos = 0
        plot_coords = list(plot_poly.exterior.coords)
        rLen = len(plot_coords)

        plotList = re_round(plot_coords, 1)
        # loop each plot vertex
        for plotVertex in plotList:
            # print("processing rPos ", str(rPos))
            if (rPos == (rLen - 1)):
                rTarget = 0
            else:
                rTarget = rPos + 1

            line = LineString([Point(plotList[rPos]), Point(plotList[rTarget])])
            lineOrg = LineString([Point(plot_coords[rPos]), Point(plot_coords[rTarget])])


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

def extractAbuttingRoadForSplay(plot_poly, road_list):
    abuttingDict = dict()

    if (plot_poly is None or road_list==[]):
        return abuttingDict

    get_current_logger().debug(f' splay plot poly {plot_poly}   with master road list  {road_list}')
    plot_coords = list(plot_poly.exterior.coords)
    rLen = len(plot_coords)
    rPos = 0

    plotList = re_round(plot_coords, 1)
    # loop each plot vertex
    for plotVertex in plotList:
        # print("processing rPos ", str(rPos))
        if (rPos == (rLen - 1)):
            rTarget = 0
        else:
            rTarget = rPos + 1

        line = LineString([Point(plotList[rPos]), Point(plotList[rTarget])])
        lineOrg = LineString([Point(plot_coords[rPos]), Point(plot_coords[rTarget])])

        get_current_logger().debug(f'Splay line segment #  {line}')
        roadIndx = 0
        for road in road_list:

            road_coords = list(road.polygon.exterior.coords)
            get_current_logger().debug(f' road name # {road.name} handle # {road.handle}')

            roadObj = re_round(road_coords, 1)
            roadPoly = Polygon(roadObj)

            get_current_logger().debug(f'line intersects roadPoly  {line.intersects(roadPoly)}  road covers line {roadPoly.covers(line)}  line touches road  {line.touches(roadPoly)}')

            if (line.intersects(roadPoly) == True or roadPoly.covers(line) == True or line.touches(roadPoly) == True):

                if 'WIDENING' in road.name.upper():
                    width = float(road.width)
                    roadStr = "".join([str(width), " ", str(road.name).replace("|", '-'), "|", str(lineOrg.length)])
                else:
                    roadStr = "".join([str(road.name).replace("|", '-'), "|", str(lineOrg.length)])

                abuttingValue = abuttingDict.get(str(roadIndx), 0)
                get_current_logger().debug(f'ABUTTING VALUE CHECK **********  {abuttingValue}')
                if (abuttingValue != 0):

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
        get_current_logger().warning(f'Invalid layerToSearch - str or list with valid values is required but value is = {layerToSearch}')
        return retList

    qry_splots = msp.query(qry_str)

    get_current_logger().debug(
        'Search in layer: %s for objectType: %s found count: %s',
        layerToSearch,
        objectType,
        len(qry_splots)
    )

    # Coordinate.default_order = 'xy'

    if (len(qry_splots) == 0):
        return retList

    for entity in qry_splots:

        if (layerToSearch not in [LayerMaster.MARGINLINE.value,
                                  LayerMaster.INTERNALROAD.value] and onlyClosed == True and (entity.closed) == 0):

            continue
        if (layerToSearch not in [LayerMaster.MARGINLINE.value,
                                  LayerMaster.INTERNALROAD.value] and onlyOpen == True and (entity.closed) == 1):

            continue


        # BLOCK REFERENCE
        if entity.dxftype() == 'INSERT':

            polyObj = DxfPoly(layerToSearch, entity.dxftype(), entity.dxf.handle)

            for venty in entity.virtual_entities():

                if (venty.dxftype() == 'LINE'):

                    segLength = round(ezdxf.math.ConstructionLine(venty.dxf.start, venty.dxf.end).length(), 1)

                    if (layerToSearch == LayerMaster.MARGINLINE.value):
                        polyObj.add_Setback(venty.dxf.color, venty.dxf.start, venty.dxf.end, segLength)

            retList.append(polyObj)

        elif entity.dxftype() == LayerMaster.DWG_LWPOLYLINE.value:

            polyObj = DxfPoly(layerToSearch, entity.dxftype(), entity.dxf.handle)
            polyObj.setIsClosed(entity.closed)

            for i, point in enumerate(entity.get_points()):
                if entity.closed == 1 and i == 0:
                    startPoint = point
                    rawpoints = entity.get_points()
                    polyObj.set_rawpoints(rawpoints)

                xypoint = str(point[0]) + " " + str(point[1])

                polyObj.add_2dpoint(xypoint)

                if entity.closed == 1 and i + 1 == entity.__len__():

                    xypoint = str(startPoint[0]) + " " + str(startPoint[1])
                    polyObj.add_2dpoint(xypoint)

            for venty in entity.virtual_entities():

                polyObj.setColor(venty.dxf.color)
                # capture the steps
                if (venty.dxftype() == 'LINE'):

                    segLength = round(ezdxf.math.ConstructionLine(venty.dxf.start, venty.dxf.end).length(), 1)

                    # printLog('debug', 'segment length ' + str(segLength))
                    if (layerToSearch == LayerMaster.SPLAY.value):
                        polyObj.add_sideLenghts(segLength)

                if (venty.dxftype() == 'ARC'):

                    bulgeList = list(zip(*entity.get_points('xyb')))[2]
                    nonZeroBulge = [i for i in bulgeList if (i != 0.0)]

                    if (len(nonZeroBulge) > 0):

                        p1 = venty.start_point
                        p2 = venty.end_point

                        distanceP1P2 = math.sqrt(((p1[0] - p2[0]) ** 2) + ((p1[1] - p2[1]) ** 2))

                        # if splay check radius before adding to object
                        if (layerToSearch == LayerMaster.SPLAY.value):

                            polyObj.set_bulge_radius_angle_chordlen(nonZeroBulge[0], venty.dxf.radius,
                                                                    venty.dxf.start_angle, (distanceP1P2 / 2))
                        else:

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
            # print('special char '	, specialChar)
            if (specialChar > -1):
                text_str = text_str[specialChar + 1:]

                endTag = text_str.find('}')
                if (endTag > -1):

                    text_str = text_str[:endTag]

            pointObj = DxfPoly(layerToSearch, entity.dxftype(), text_str)
            pointObj.setIsClosed(1)

            xypoint = str(entity.dxf.insert.x) + " " + str(entity.dxf.insert.y)
            pointObj.add_2dpoint(xypoint)
            retList.append(pointObj)

    return retList


class GenOpenLayoutReport:

    def __init__(self,request_id,combinedObjects,file_name,Status_dict:dict,requesttimeobj):

        self.request_id= request_id
        self.combinedObjects= combinedObjects
        self.filename= file_name
        self.request_params= combinedObjects.get('request_params', {})
        self.modelspace=combinedObjects.get('modelspace', {})
        self.reportextract=[]
        self.responseDict=dict()
        self.Status_dict=Status_dict
        self.errors= []
        self.warnings=[]
        self.progress=0

        self.mainPlotArea = 0.0
        self.reservedRoadArea = 0.0
        self.totalNalaArea = 0.0
        self.totalGridRoadArea = 0.0
        self.totalBufferZoneArea = 0.0
        self.totalReservedArea= 0.0
        self.totalWaterBodiesArea = 0.0
        self.totalLeftoverOwnersLandArea= 0.0
        self.totalSurrenderToAuthorityArea = 0.0
        self.amentiyArea = 0.0
        self.socialInfraArea = 0.0
        self.totalGreenBeltArea =0.0
        self.totalCommonParkingArea = 0.0
        self.totalSplayArea = 0.0
        self.totalPlottedArea = 0.0
        self.totalUtilityArea = 0.0
        self.total_road_area =0.0
        self.totalMortgageArea =0.0
        self.totalNetLayoutArea= 0.0

        self.totalTotCount = 0
        self.totalGreenBeltCount = 0
        self.totalTotArea = 0
        self.requesttimeobj = requesttimeobj

        self.main2min_progress = 40
        self.main2max_progress = 80
        self.pipeline_start_time= time.time()


    def get_request_summary(self):
        dateTimeObj = datetime.now()
        timestampStr = dateTimeObj.strftime("%d-%b-%Y (%H:%M:%S.%f)")

        js_requestParamsSummary = self.request_params
        js_requestParamsSummary['ReportGeneratedDateTime'] = timestampStr

        self.reportextract.append({"REQUEST_SUMMARY": js_requestParamsSummary})

    def get_plot_summary(self):

        mainPlotList = self.combinedObjects.get(LayerMaster.PLOT.value).getBaseUnitFinalList() if self.combinedObjects.get(
            LayerMaster.PLOT.value, 0) != 0 else []

        reservedRoadList = self.combinedObjects.get(
            LayerMaster.ROADWIDENING.value).getBaseUnitFinalList() if self.combinedObjects.get(
            LayerMaster.ROADWIDENING.value, 0) != 0 else []

        for mnPlot in mainPlotList:
            self.mainPlotArea = self.mainPlotArea + mnPlot.area

        js_mainPlotSummary = dict()
        js_mainPlotSummary['MAIN_PLOT_AREA'] = str(round(self.mainPlotArea, 2))

        for rwidening in reservedRoadList:
            self.reservedRoadArea = self.reservedRoadArea + rwidening.area

        js_mainPlotSummary['ROAD_WIDENING_AREA'] = str(round(self.reservedRoadArea, 2))

        self.reportextract.append({"MAIN_PLOT_SUMMARY":js_mainPlotSummary})


    def get_netplot_summary(self):

        nalaRoadList = self.combinedObjects.get(
            LayerMaster.NALAROAD.value).getBaseUnitFinalList() if self.combinedObjects.get(LayerMaster.NALAROAD.value,
                                                                                      0) != 0 else []
        gridRoadList = self.combinedObjects.get(
            LayerMaster.GRIDROAD.value).getBaseUnitFinalList() if self.combinedObjects.get(LayerMaster.GRIDROAD.value,0) != 0 else []

        bufferZoneList = self.combinedObjects.get(
            LayerMaster.BUFFERZONE.value).getBaseUnitFinalList() if self.combinedObjects.get(
            LayerMaster.BUFFERZONE.value, 0) != 0 else []

        reservedAreaList = self.combinedObjects.get(
            LayerMaster.RESERVEDAREA.value).getBaseUnitFinalList() if self.combinedObjects.get(
            LayerMaster.RESERVEDAREA.value, 0) != 0 else []

        waterBodiesList = self.combinedObjects.get(
            LayerMaster.WATERBODIES.value).getBaseUnitFinalList() if self.combinedObjects.get(
            LayerMaster.WATERBODIES.value, 0) != 0 else []

        leftoverOwnersLandList = self.combinedObjects.get(
            LayerMaster.LEFTOVEROWNERSLAND.value).getBaseUnitFinalList() if self.combinedObjects.get(
            LayerMaster.LEFTOVEROWNERSLAND.value, 0) != 0 else []

        surrenderToAuthorityList = self.combinedObjects.get(
            LayerMaster.SURRENDERTOAUTH.value).getBaseUnitFinalList() if self.combinedObjects.get(
            LayerMaster.SURRENDERTOAUTH.value, 0) != 0 else []

        socialInfraList = self.combinedObjects.get(
            LayerMaster.SOCIALINFRA.value).getBaseUnitFinalList() if self.combinedObjects.get(
            LayerMaster.SOCIALINFRA.value, 0) != 0 else []

        totList = self.combinedObjects.get(LayerMaster.ORGOPENSPACE.value).getBaseUnitFinalList()

        parkingUnitsList = self.combinedObjects.get(
            LayerMaster.PARKING.value).getBaseUnitFinalList() if self.combinedObjects.get(LayerMaster.PARKING.value,
                                                                                     0) != 0 else []
        splayPlotList = self.combinedObjects.get(LayerMaster.SPLAY.value).getBaseUnitFinalList() if self.combinedObjects.get(
            LayerMaster.SPLAY.value, 0) != 0 else []

        mainPlotList = self.combinedObjects.get(
            LayerMaster.PLOT.value).getBaseUnitFinalList() if self.combinedObjects.get(
            LayerMaster.PLOT.value, 0) != 0 else []

        accessoryUnitsList = self.combinedObjects.get(
            LayerMaster.ACCESSORYUSE.value).getBaseUnitFinalList() if self.combinedObjects.get(
            LayerMaster.ACCESSORYUSE.value, 0) != 0 else []

        for nalaObj in nalaRoadList:
            self.totalNalaArea += float(nalaObj.area)

        for gridObj in gridRoadList:
            self.totalGridRoadArea += float(gridObj.area)

        for buffZoneObj in bufferZoneList:
            self.totalBufferZoneArea += float(buffZoneObj.area)


        for reservedAreaObj in reservedAreaList:
            result = isChildFullyWithinParentObject('ReservedArea', 'PLOT', reservedAreaObj, mainPlotList)
            if (result):
                self.totalReservedArea += float(reservedAreaObj.area)
            else:

                get_current_logger().error(f'Skipping - Reserved area as it is outside plot area handle# {reservedAreaObj.handle} , name = {reservedAreaObj.name},'
                                    f'area= {reservedAreaObj.area}')

        for waterBodiesObj in waterBodiesList:
            self.totalWaterBodiesArea += float(waterBodiesObj.area)

        for leftoverOwnerLandObj in leftoverOwnersLandList:
            self.totalLeftoverOwnersLandArea += float(leftoverOwnerLandObj.area)

        for surrenderToAuthObj in surrenderToAuthorityList:
            self.totalSurrenderToAuthorityArea += float(surrenderToAuthObj.area)

        for socObj in socialInfraList:
            # printLog('verbose', "SOCIALINFRA type ", socObj.name, " area ", socObj.area )
            if ("AMENITY" in socObj.name.upper()):
                self.amentiyArea += float(socObj.area)
            else:
                self.socialInfraArea += float(socObj.area)

        for por in totList:
            # print("ORG Open Space Type ", por.name,  ' area ' , por.area)
            if "belt" in str(por.name.lower()):  # or "strip" in str(por.name.lower()):
                self.totalGreenBeltArea += round(por.area, 2)
                self.totalGreenBeltCount += 1
            else:
                self.totalTotArea += round(por.area, 2)
                self.totalTotCount += 1

        for parkingObj in parkingUnitsList:

            self.totalCommonParkingArea += parkingObj.area

        for por in splayPlotList:

            self.totalSplayArea = self.totalSplayArea + (por.area)

        for accUseObj in accessoryUnitsList:
            self.totalUtilityArea = self.totalUtilityArea + accUseObj.area

        self.totalNetLayoutArea = self.mainPlotArea - (
                self.totalLeftoverOwnersLandArea + self.totalWaterBodiesArea + self.totalBufferZoneArea + \
                self.totalNalaArea + self.totalReservedArea + self.totalSurrenderToAuthorityArea + self.totalCommonParkingArea + self.totalGreenBeltArea + self.reservedRoadArea + self.totalSplayArea + self.socialInfraArea + self.amentiyArea)

        js_netPlotSummary = dict()
        js_netPlotSummary['TOTAL_LAYOUT_AREA'] = str(round(self.mainPlotArea, 2))
        js_netPlotSummary['NALA_AREA'] = str(round(self.totalNalaArea, 2))
        js_netPlotSummary['GRIDROAD_AREA'] = str(round(self.totalGridRoadArea, 2))
        js_netPlotSummary['BUFFERZONE_AREA'] = str(round(self.totalBufferZoneArea, 2))
        js_netPlotSummary['RESERVED_AREA'] = str(round(self.totalReservedArea, 2))

        js_netPlotSummary['WATERBODIES_AREA'] = str(round(self.totalWaterBodiesArea, 2))
        js_netPlotSummary['LEFTOVEROWNERSLAND_AREA'] = str(round(self.totalLeftoverOwnersLandArea, 2))

        js_netPlotSummary['ROAD_WIDENING_AREA'] = str(round(self.reservedRoadArea, 2))
        js_netPlotSummary['SURRENDER_TO_AUTHORITY'] = str(round(self.totalSurrenderToAuthorityArea, 2))
        js_netPlotSummary['SOCIAL_INFRASTRUCTURE'] = str(round(self.socialInfraArea, 2))
        js_netPlotSummary['AMENITY_AREA'] = str(round(self.amentiyArea, 2))
        js_netPlotSummary['GREEN_BELT_AREA'] = str(round(self.totalGreenBeltArea, 2))
        js_netPlotSummary['COMMON_PARKING_AREA'] = str(round(self.totalCommonParkingArea, 2))

        js_netPlotSummary['SPLAY_AREA'] = str(round(self.totalSplayArea, 2))
        js_netPlotSummary['NET_LAYOUT_AREA'] = str(round(self.totalNetLayoutArea, 2))
        js_netPlotSummary['TOTAL_UTILITY_AREA'] = str(round(self.totalUtilityArea, 2))


        self.reportextract.append({"NET_PLOT_SUMMARY": dict(sorted(js_netPlotSummary.items()))})

    def get_landusage_details(self):

        plotList = self.combinedObjects.get(LayerMaster.OPENLAYOUT.value).getBaseUnitFinalList() if self.combinedObjects.get(
            LayerMaster.OPENLAYOUT.value, 0) != 0 else []

        internalRoadList = self.combinedObjects.get(
            LayerMaster.INTERNALROAD.value).getBaseUnitFinalList() if self.combinedObjects.get(
            LayerMaster.INTERNALROAD.value, 0) != 0 else []

        for por in plotList:
            self.totalPlottedArea = self.totalPlottedArea + float(por.area)

        for por in internalRoadList:

            self.total_road_area += por.area

        js_landusageInfo = dict()

        js_landusageInfo['PLOTTED_AREA'] = str(round(self.totalPlottedArea, 2))
        js_landusageInfo['ORG_OPEN_SPACE_AREA'] = str(round(self.totalTotArea, 2))
        js_landusageInfo['SOCIAL_INFRASTRUCTURE'] = str(round(self.socialInfraArea, 2))
        js_landusageInfo['AMENITY_AREA'] = str(round(self.amentiyArea, 2))
        js_landusageInfo['UTILITY_AREA'] = str(round(self.totalUtilityArea, 2))
        js_landusageInfo['ROAD_AREA'] = str(round(self.total_road_area, 2))
        js_landusageInfo['SPLAY_AREA'] = str(round(self.totalSplayArea, 2))

        netPlottedArea = self.totalPlottedArea + self.totalTotArea + self.socialInfraArea + self.amentiyArea + self.total_road_area + self.totalUtilityArea + self.totalSplayArea
        js_landusageInfo['NET_PLOTTED_AREA'] = str(round(netPlottedArea, 2))
        js_landusageInfo[
            'NET_PLOTTED_AREA_CALC'] = 'Plotted Area + org. open space/Tot area + social infra area +  utility/amenity + road area + splay area '

        self.reportextract.append({"LAND_USAGE": dict(sorted(js_landusageInfo.items()))})

    def get_mortgage_summary(self):

        MORTGAGE_PERCENT_OPEN_LAYOUT = 0.15

        mortgagedList = self.combinedObjects.get(
            LayerMaster.MORTGAGEAREA.value).getBaseUnitFinalList() if self.combinedObjects.get(
            LayerMaster.MORTGAGEAREA.value, 0) != 0 else []

        for por in mortgagedList:

            self.totalMortgageArea = self.totalMortgageArea + por.area

        if (self.totalPlottedArea > 0):
            proposed_mortageFactor = float(round(self.totalMortgageArea / self.totalPlottedArea, 2))
        else:
            proposed_mortageFactor = 0


        js_mortgageInfo = dict()

        mtgruleResult = callrule('ts-mortgage',
                                 {'plan_type': 'Open_Layout', 'proposed_mortgage_factor': proposed_mortageFactor})
        mortgageResult = mtgruleResult["result"]

        required_mortageFactor = mortgageResult.get('required_mortgage_factor', MORTGAGE_PERCENT_OPEN_LAYOUT)

        mortgageRule = mortgageResult.get('zrule', 'N/A')

        min_mortgage_area_required = round((required_mortageFactor * self.totalPlottedArea) / 100, 2)

        if self.totalMortgageArea >= min_mortgage_area_required:
            statusValue = "OK"
        else:
            statusValue = "NOT OK"

        js_mortgageInfo['MORTGAGE_PERCENT_OPEN_LAYOUT'] = str(float(required_mortageFactor))
        js_mortgageInfo['REQUIRED_MIN_MORTGAGE_AREA'] = str(min_mortgage_area_required)
        js_mortgageInfo['PROPOSED_MORTGAGE_AREA'] = str(round(self.totalMortgageArea, 2))
        js_mortgageInfo['STATUS'] = statusValue
        js_mortgageInfo['APPLICABLE_RULE'] = mortgageRule

        self.reportextract.append({"MORTGAGE_SUMMARY": dict(sorted(js_mortgageInfo.items()))})

    def get_orgGreenStrip_summary(self):

        TOT_MIN_AREA_PERCENT = 0.075

        tot_min_total_required_area = round(TOT_MIN_AREA_PERCENT * self.totalNetLayoutArea, 2)

        if self.totalTotArea >= tot_min_total_required_area:
            statusValue = "OK"
        else:
            statusValue = "NOT OK"

        js_totSummary = dict()

        tot_percent = str(float(TOT_MIN_AREA_PERCENT * 100)) + " %"
        js_totSummary['REQUIRED_MIN_ORG_OPEN_SPACE_AREA_PERCENT'] = tot_percent
        js_totSummary['REQUIRED_MIN_ORG_OPEN_SPACE_AREA'] = str(tot_min_total_required_area)
        js_totSummary['NO_OF_ORG_OPEN_SPACES'] = str(self.totalTotCount)
        js_totSummary['PROPOSED_ORG_OPEN_SPACE_AREA'] = str(round(self.totalTotArea, 2))
        js_totSummary['STATUS'] = statusValue
        js_totSummary['RULE_APPLICABLE'] = "At least " + tot_percent + " of total plotted area "

        self.reportextract.append({"ORG_OPEN_SPACE_GREEN_STRIP_SUMMARY": dict(sorted(js_totSummary.items()))})

    def get_org_openspace_detail(self):
        js_totDetailList = []
        TOTPLOT_MIN_REQUIRED_AREA = 50.00
        TOTPLOT_MIN_REQUIRED_WIDTH = 3.00
        GREEN_STRIP_MIN_REQUIRED_WIDTH = 1.00
        GREEN_STRIP_MIN_REQUIRED_AREA = 0.0

        totList = self.combinedObjects.get(LayerMaster.ORGOPENSPACE.value).getBaseUnitFinalList()

        # 1/23/2024 - green belt
        js_greenBeltList = list()

        # detail
        for por in totList:
            js_totDetail = dict()
            js_greenBeltDetails = dict()

            if "belt" in str(por.name.lower()):  # or "strip" in str(por.name.lower()):
                js_greenBeltDetails['TYPE'] = 'GREEN BELT'
                min_area_to_check = 0
                min_width_to_check = 0

                if por.area >= min_area_to_check or por.width >= min_width_to_check:
                    statusValue = "OK"
                else:
                    statusValue = "Not OK"

                js_greenBeltDetails['NAME'] = str(por.name)
                js_greenBeltDetails['REQUIRED_MIN_AREA'] = str(min_area_to_check)
                js_greenBeltDetails['PROPOSED_AREA'] = str(por.area)
                js_greenBeltDetails['REQUIRED_MIN_WIDTH'] = str(min_width_to_check)
                js_greenBeltDetails['PROPOSED_WIDTH'] = str(por.width)
                js_greenBeltDetails['STATUS'] = statusValue
                js_greenBeltList.append(js_greenBeltDetails)


            else:  # other

                if "strip" in str(por.name.lower()):  # or "strip" in str(por.name.lower()):
                    js_totDetail['TYPE'] = 'GREEN STRIP'
                    min_area_to_check = GREEN_STRIP_MIN_REQUIRED_AREA
                    min_width_to_check = GREEN_STRIP_MIN_REQUIRED_WIDTH

                else:
                    js_totDetail['TYPE'] = 'TOT'
                    min_area_to_check = TOTPLOT_MIN_REQUIRED_AREA
                    min_width_to_check = TOTPLOT_MIN_REQUIRED_WIDTH

                if por.area >= min_area_to_check or por.width >= TOTPLOT_MIN_REQUIRED_WIDTH:
                    statusValue = "OK"
                else:
                    statusValue = "Not OK"

                js_totDetail['NAME'] = str(por.name)
                js_totDetail['REQUIRED_MIN_AREA'] = str(min_area_to_check)
                js_totDetail['PROPOSED_AREA'] = str(por.area)
                js_totDetail['REQUIRED_MIN_WIDTH'] = str(min_width_to_check)
                js_totDetail['PROPOSED_WIDTH'] = str(por.width)
                js_totDetail['STATUS'] = statusValue
                js_totDetailList.append(js_totDetail)

        self.reportextract.append({"ORG_OPEN_SPACE_DETAIL": [dict(sorted(dct.items())) for dct in js_totDetailList]})

    def get_green_belt_detail(self):

        # 1/23/2024 - green belt
        js_greenBeltList = list()

        totList = self.combinedObjects.get(LayerMaster.ORGOPENSPACE.value).getBaseUnitFinalList()

        # detail
        for por in totList:
            js_totDetail = dict()
            js_greenBeltDetails = dict()

            if "belt" in str(por.name.lower()):  # or "strip" in str(por.name.lower()):
                js_greenBeltDetails['TYPE'] = 'GREEN BELT'
                min_area_to_check = 0
                min_width_to_check = 0

                if por.area >= min_area_to_check or por.width >= min_width_to_check:
                    statusValue = "OK"
                else:
                    statusValue = "Not OK"

                js_greenBeltDetails['NAME'] = str(por.name)
                js_greenBeltDetails['REQUIRED_MIN_AREA'] = str(min_area_to_check)
                js_greenBeltDetails['PROPOSED_AREA'] = str(por.area)
                js_greenBeltDetails['REQUIRED_MIN_WIDTH'] = str(min_width_to_check)
                js_greenBeltDetails['PROPOSED_WIDTH'] = str(por.width)
                js_greenBeltDetails['STATUS'] = statusValue
                js_greenBeltList.append(js_greenBeltDetails)

        self.reportextract.append({"GREEN_BELT_DETAIL": js_greenBeltList})

    def get_splay_check_summary(self):

        widthOfRoad = 0
        splay_rule = ""

        splayPlotList = self.combinedObjects.get(
            LayerMaster.SPLAY.value).getBaseUnitFinalList() if self.combinedObjects.get(
            LayerMaster.SPLAY.value, 0) != 0 else []

        for por in splayPlotList:

            if (por.frontageList is not None and len(por.frontageList) > 0):

                ruleResult = callrule('ts-splay',
                                      {'roadwidth': widthOfRoad, 'length': por.length, 'width': widthOfRoad})
                splayResult = ruleResult["result"]
                get_current_logger().denug(f"rule result:\n {splayResult}")
                splay_rule = splayResult.get('zrule', 'N/A')

        js_splaySummary = dict()

        splayPlotList = self.combinedObjects.get(
            LayerMaster.SPLAY.value).getBaseUnitFinalList() if self.combinedObjects.get(
            LayerMaster.SPLAY.value, 0) != 0 else []

        js_splaySummary['TOTAL_NO_SPLAY_PLOTS'] = str(len(splayPlotList))
        js_splaySummary['TOTAL_SPLAY_AREA'] = str(round(self.totalSplayArea, 2))
        js_splaySummary['APPLICABLE_RULE'] = splay_rule

        self.reportextract.append({"SPLAY_CHECKS_SUMMARY": dict(sorted(js_splaySummary.items()))})

    def get_splay_details(self):

        js_splayInfoList = []

        widthOfRoad = 0

        splayPlotList = self.combinedObjects.get(
            LayerMaster.SPLAY.value).getBaseUnitFinalList() if self.combinedObjects.get(
            LayerMaster.SPLAY.value, 0) != 0 else []

        reservedRoadList = self.combinedObjects.get(
            LayerMaster.ROADWIDENING.value).getBaseUnitFinalList() if self.combinedObjects.get(
            LayerMaster.ROADWIDENING.value, 0) != 0 else []

        plotList = self.combinedObjects.get(
            LayerMaster.OPENLAYOUT.value).getBaseUnitFinalList() if self.combinedObjects.get(
            LayerMaster.OPENLAYOUT.value, 0) != 0 else []

        SPLAY_MIN_REQUIRED_LENGTH = 3
        SPLAY_MIN_REQUIRED_WIDTH = 3

        ## SUB PLOT CHECKS
        MIN_AREA_INDIV_PLOT = 50.0
        MIN_FRONTAGE_LENG_INDIV_PLOT = 6.0

        for por in splayPlotList:
            js_splayInfo = dict()
            splay_status = "Not OK"
            splay_req_length = SPLAY_MIN_REQUIRED_LENGTH
            splay_req_width = SPLAY_MIN_REQUIRED_WIDTH
            splayName = ''

            if (por.frontageList is not None and len(por.frontageList) > 0):
                splayInsidePlotResultDict = isChildWithinParentObject('Splay', 'Subplot', por, plotList)

                splayName = por.name

                if (splayInsidePlotResultDict is not None and splayInsidePlotResultDict.get('iswithin',
                                                                                            False) != False):
                    get_current_logger().debug(f'splay inside subplot result  {splayInsidePlotResultDict}')

                    splayName = splayInsidePlotResultDict.get('parentName', 'N/A')

                checkMaxFrontag = max(por.frontageList)
                frontage_index = por.frontageList.index(checkMaxFrontag)

                try:

                    if (round(float(checkMaxFrontag), 2) == por.length):
                        frontage_value = str(por.length)
                    else:
                        frontage_value = str(por.width)

                    status_value = "NOT OK"
                    # print("frontage " , frontage_value , "area ", por.area )
                    if (float(frontage_value) >= MIN_FRONTAGE_LENG_INDIV_PLOT and float(
                            por.area) >= MIN_AREA_INDIV_PLOT):
                        status_value = "OK"

                except ValueError as ve:
                    get_current_logger().error(
                        f"Problem processing frontage values {checkMaxFrontag} length /wdith {por.length} /{por.width} defaulting to as is ")
                    frontage_value = checkMaxFrontag
                    status_value = "NOT OK"

                # get abutting road
                abutting_value = por.abuttingRoadList[frontage_index]
                widthOfRoad = float(extract_dimensions_fromtext(str(abutting_value), None, "M"))

                get_current_logger().debug(f"abutting/width of road {abutting_value} / {widthOfRoad}")

                if (widthOfRoad == 0 or "WIDENING" in por.name.upper()):

                    for rl in reservedRoadList:
                        widthOfRoad = rl.width

                # to get splay dynamic rule based on road width
                # Rules Engine 11/22/2020
                ruleResult = callrule('ts-splay',
                                      {'roadwidth': widthOfRoad, 'length': por.length, 'width': widthOfRoad})
                splayResult = ruleResult["result"]
                get_current_logger().debug(f"rule result:\n {splayResult}")
                splay_req_length = splayResult['required_length']
                splay_req_width = splayResult['required_width']
                splay_status = splayResult.get('status', 'N/A')

            js_splayInfo['TYPE'] = 'SPLAY'
            js_splayInfo['SPLAY_PLOT'] = str(splayName)
            js_splayInfo['REFERENCE_ID'] = str(por.handle)
            js_splayInfo['ABUTTING_ROAD_WIDTH'] = str(widthOfRoad)
            js_splayInfo['SPLAY_AREA'] = str(round((por.area), 2))
            js_splayInfo['REQUIRED_MIN_LENGTH'] = str(splay_req_length)
            js_splayInfo['PROPOSED_LENGTH'] = str(por.length)
            js_splayInfo['REQUIRED_MIN_WIDTH'] = str(splay_req_width)
            js_splayInfo['PROPOSED_WIDTH'] = str(por.width)
            js_splayInfo['STATUS'] = str(splay_status)
            js_splayInfoList.append(js_splayInfo)

        self.reportextract.append({"SPLAY_DETAILS": js_splayInfoList})

    def get_mainRoad_details(self):

        js_mainRoadInfoList = []

        total_road_area = 0.0

        MAINROAD_MIN_REQUIRED_WIDTH = 18.00

        existing_startDelim = ''

        mainRoadList = self.combinedObjects.get(
            LayerMaster.MAINROAD.value).getBaseUnitFinalList() if self.combinedObjects.get(LayerMaster.MAINROAD.value,
                                                                                           0) != 0 else []

        mainPlotList = self.combinedObjects.get(
            LayerMaster.PLOT.value).getBaseUnitFinalList() if self.combinedObjects.get(
            LayerMaster.PLOT.value, 0) != 0 else []

        for por in mainRoadList:
            widthOfRoad = 0.0
            js_mainRoadInfo = dict()
            total_road_area += por.area
            roadInsidePlot = False
            mainRoadInsidePLOTResultDict = isChildFullyWithinParentObject('MainRoad', 'PLOT', por, mainPlotList)

            if (mainRoadInsidePLOTResultDict is not None and mainRoadInsidePLOTResultDict.get('iswithin',
                                                                                              False) != False):
                roadInsidePlot = True


            if (por.name.upper().find('EXISTING') > -1):
                existing_widthOfRoad = float(
                    extract_dimensions_fromtext(str(por.name), existing_startDelim, "EXISTING"))
            else:
                existing_widthOfRoad = 'N/A'

            get_current_logger().debug(f"Existing ROAD Width {existing_widthOfRoad}")

            try:

                widthOfRoad = float(extract_road_width_fromtext(por.name))
                get_current_logger().debug(f'widthOfRoad from extract_road_width_fromtext(): {widthOfRoad}')

            except:
                get_current_logger().error('Unable to extract extract_road_width_fromtext of road setting to -1 ')
                widthOfRoad = -1

            if (widthOfRoad <= 0.0):
                widthOfRoad = por.width

            get_current_logger().debug(f"road width {widthOfRoad}")

            statusValue = "Not OK"
            if (widthOfRoad >= MAINROAD_MIN_REQUIRED_WIDTH):
                statusValue = "OK"

            js_mainRoadInfo['ROAD_NAME'] = removeSpecialChars(por.name)
            js_mainRoadInfo['ROAD_WITHIN_PLOT'] = str(roadInsidePlot)
            js_mainRoadInfo['ROAD_LENGTH'] = str(por.length)
            js_mainRoadInfo['MAINROAD_MIN_REQUIRED_WIDTH'] = str(MAINROAD_MIN_REQUIRED_WIDTH)
            js_mainRoadInfo['ROAD_WIDTH'] = str(widthOfRoad)
            js_mainRoadInfo['EXISTING_ROAD_WIDTH'] = str(existing_widthOfRoad)
            js_mainRoadInfo['ROAD_AREA'] = str(por.area)

            js_mainRoadInfo['STATUS'] = statusValue
            js_mainRoadInfoList.append(js_mainRoadInfo)

        self.reportextract.append({"MAIN_ROADS_DETAILS": [dict(sorted(dct.items())) for dct in js_mainRoadInfoList]})

    def get_internalroad_details(self):

        js_internalRoadInfoList = []

        internalRoadDictDirect = self.combinedObjects.get('INTERNALROAD_WIDTHS_NEW', dict())
        INTERNALROAD_MIN_REQUIRED_WIDTH = 9.00
        total_road_area = 0.0

        internalRoadList = self.combinedObjects.get(
            LayerMaster.INTERNALROAD.value).getBaseUnitFinalList() if self.combinedObjects.get(
            LayerMaster.INTERNALROAD.value, 0) != 0 else []

        for por in internalRoadList:
            js_internalRoadInfo = dict()
            total_road_area += por.area

            try:

                # check if road is beyond 20 suspect for irregular shape
                if (por.width > 20 and por.isIrregularObject):
                    widthOfRoadCheckList = internalRoadDictDirect.get(por.handle, 0)
                    # printLog('verbose', 'Swapped widthOfRoad from Direct method : ' + str(widthOfRoadCheckList))
                else:
                    widthOfRoadCheckList = None

                if (widthOfRoadCheckList is None or len(widthOfRoadCheckList) < 2):
                    widthOfRoad = por.width  # round(float(getMinWidthIrregularObjects(por.polygon) ),2)
                else:
                    widthOfRoad = float(widthOfRoadCheckList[1])

                # printLog('verbose','widthOfRoad used : ' + str(widthOfRoad) )
                get_current_logger().debug(f'INTERNAL ROAD WIDTH MIN WIDTH Value {widthOfRoad} , POR.WIDTH,{por.width}')
            except:
                get_current_logger().error("Unable to extract internalRoadDictDirect  of road setting to -1")
                widthOfRoad = -1

            if (widthOfRoad <= 0.0):
                widthOfRoad = por.width

            get_current_logger().debug(f"road width {widthOfRoad}")

            statusValue = "Not OK"
            if (widthOfRoad >= INTERNALROAD_MIN_REQUIRED_WIDTH):
                statusValue = "OK"

            js_internalRoadInfo['ROAD_NAME'] = removeSpecialChars(por.name)
            js_internalRoadInfo['ROAD_HANDLE'] = str(por.handle)
            js_internalRoadInfo['ROAD_IRREGULAR_POLY'] = str(por.isIrregularObject)
            js_internalRoadInfo['ROAD_MIN_REQUIRED_LENGTH'] = '-'
            js_internalRoadInfo['ROAD_LENGTH'] = str(por.length)
            js_internalRoadInfo['INTERNALROAD_MIN_REQUIRED_WIDTH'] = str(INTERNALROAD_MIN_REQUIRED_WIDTH)
            js_internalRoadInfo['ROAD_WIDTH'] = str(widthOfRoad)
            js_internalRoadInfo['STATUS'] = statusValue
            js_internalRoadInfoList.append(js_internalRoadInfo)

        self.reportextract.append(
            {"INTERNAL_ROADS_DETAILS ": [dict(sorted(dct.items())) for dct in js_internalRoadInfoList]})

    def get_gridroad_details(self):

        # detail
        js_gridRoadInfoList = []
        total_grid_road_area = 0.0

        GRIDROAD_MIN_REQUIRED_WIDTH = 9.00

        gridRoadList = self.combinedObjects.get(
            LayerMaster.GRIDROAD.value).getBaseUnitFinalList() if self.combinedObjects.get(LayerMaster.GRIDROAD.value,
                                                                                           0) != 0 else []

        gridRoadDictDirect = self.combinedObjects.get('GRIDROAD_WIDTHS_NEW', dict())

        for por in gridRoadList:
            js_gridRoadInfo = dict()
            total_grid_road_area += por.area

            try:
                get_current_logger().debug(
                    f'Road name # {por.name} , Id# {por.handle} , width # {por.width}, len# {por.length},area# {por.area}, isIrregular {por.isIrregularObject}')
                # check the list response
                # check if road is beyond 20 suspect for irregular shape
                if (por.width > 20 and por.isIrregularObject):
                    widthOfRoadCheckList = gridRoadDictDirect.get(por.handle, 0)
                    # printLog('verbose', 'Swapped widthOfRoad from Direct method : ' + str(widthOfRoadCheckList))
                else:
                    widthOfRoadCheckList = None

                if (widthOfRoadCheckList is None or len(widthOfRoadCheckList) < 2):
                    widthOfRoad = por.width  # round(float(getMinWidthIrregularObjects(por.polygon) ),2)
                else:
                    widthOfRoad = float(widthOfRoadCheckList[1])

            except:
                get_current_logger().error(" Unable to extract internalRoadDictDirect  of road setting to -1 ")
                widthOfRoad = -1

            if (widthOfRoad <= 0.0):
                widthOfRoad = por.width

            get_current_logger().debug(f" road width  {widthOfRoad}")

            statusValue = "Not OK"
            if (widthOfRoad >= GRIDROAD_MIN_REQUIRED_WIDTH):
                statusValue = "OK"

            js_gridRoadInfo['ROAD_NAME'] = removeSpecialChars(por.name)
            js_gridRoadInfo['ROAD_HANDLE'] = str(por.handle)
            js_gridRoadInfo['ROAD_IRREGULAR_POLY'] = str(por.isIrregularObject)
            js_gridRoadInfo['ROAD_MIN_REQUIRED_LENGTH'] = '-'
            js_gridRoadInfo['ROAD_LENGTH'] = str(por.length)
            js_gridRoadInfo['GRIDROAD_MIN_REQUIRED_WIDTH'] = str(GRIDROAD_MIN_REQUIRED_WIDTH)
            js_gridRoadInfo['ROAD_WIDTH'] = str(widthOfRoad)
            js_gridRoadInfo['STATUS'] = statusValue
            js_gridRoadInfoList.append(js_gridRoadInfo)

        self.reportextract.append({"GRID_ROADS_DETAILS ": js_gridRoadInfoList})

    def get_subplot_summary(self):

        plotList = self.combinedObjects.get(LayerMaster.OPENLAYOUT.value).getBaseUnitFinalList() if self.combinedObjects.get(
            LayerMaster.OPENLAYOUT.value, 0) != 0 else []

        js_IndivSummary = dict()

        js_IndivSummary['TOTAL_PLOTS_NOS'] = str(len(plotList))
        js_IndivSummary['TOTAL_PLOTTED_AREA'] = str(round(self.totalPlottedArea, 2))

        self.reportextract.append({"SUB_PLOTS_SUMMARY": js_IndivSummary})

    def get_subplot_details(self):

        plotList = self.combinedObjects.get(
            LayerMaster.OPENLAYOUT.value).getBaseUnitFinalList() if self.combinedObjects.get(
            LayerMaster.OPENLAYOUT.value, 0) != 0 else []

        js_IndivInfoList = []

        ## SUB PLOT CHECKS
        MIN_AREA_INDIV_PLOT = 50.0
        MIN_FRONTAGE_LENG_INDIV_PLOT = 6.0

        for por in plotList:

            js_IndivInfo = dict()

            frontage_value = "0.0"
            abutting_value = "N/A"
            status_value = "NOT OK"
            if (por.frontageList is not None and len(por.frontageList) > 0):
                isRoadWidening = False

                resultWidening = 'WIDENING' in str(por.abuttingRoadList)

                if resultWidening:

                    # check if main road abuts or use max value
                    checkMaxFrontag = max(por.frontageList)
                    isRoadWidening = True

                else:
                    isRoadWidening = False
                    checkMaxFrontag = min(por.frontageList)

                frontage_index = por.frontageList.index(checkMaxFrontag)
                try:

                    if (por.isIrregularObject or isRoadWidening == True):
                        frontage_value = round(checkMaxFrontag, 2)
                    else:

                        if (round(float(checkMaxFrontag), 2) == por.length):

                            frontage_value = str(por.length)

                        else:
                            frontage_value = str(por.width)

                    # print("frontage " , frontage_value , "area ", por.area )
                    if (float(frontage_value) >= MIN_FRONTAGE_LENG_INDIV_PLOT and float(
                            por.area) >= MIN_AREA_INDIV_PLOT):
                        status_value = "OK"

                except ValueError as ve:
                    get_current_logger().error(
                        f"Problem processing frontage values {checkMaxFrontag} length /width {por.length} /{por.width} defaulting to as is ")
                    frontage_value = checkMaxFrontag
                    status_value = "NOT OK"

                # get abutting road
                abutting_value = por.abuttingRoadList[frontage_index]

            js_IndivInfo['PLOT'] = str(por.name)
            js_IndivInfo['ABUTTING_ROAD'] = str(abutting_value)
            js_IndivInfo['REQUIRED_MIN_PLOT_AREA'] = str(MIN_AREA_INDIV_PLOT)
            js_IndivInfo['PROPOSED_PLOT_AREA'] = str(por.area)
            js_IndivInfo['REQUIRED_FRONTAGE'] = str(MIN_FRONTAGE_LENG_INDIV_PLOT)
            js_IndivInfo['PROPOSED_FRONTAGE'] = str(frontage_value)
            js_IndivInfo['PLOT_LENGTH'] = str(por.length)
            js_IndivInfo['PLOT_WIDTH'] = str(por.width)
            js_IndivInfo['STATUS'] = str(status_value)
            js_IndivInfoList.append(js_IndivInfo)

        self.reportextract.append({"SUB_PLOTS_DETAILS": [dict(sorted(dct.items())) for dct in js_IndivInfoList]})

    def get_mortgage_plot_summary(self):

        mortgagedList = self.combinedObjects.get(
            LayerMaster.MORTGAGEAREA.value).getBaseUnitFinalList() if self.combinedObjects.get(
            LayerMaster.MORTGAGEAREA.value, 0) != 0 else []

        js_MortageSummary = dict()

        js_MortageSummary['TOTAL_MORTGAGE_PLOTS_NOS'] = str(len(mortgagedList))
        js_MortageSummary['TOTAL_MORTGAGE_AREA'] = str(round(self.totalMortgageArea, 2))

        self.reportextract.append({"MORTGAGE_PLOTS_SUMMARY": dict(sorted(js_MortageSummary.items()))})

    def get_mortgage_plot_details(self):

        js_mortgageInfoList = []

        mortgagedList = self.combinedObjects.get(
            LayerMaster.MORTGAGEAREA.value).getBaseUnitFinalList() if self.combinedObjects.get(
            LayerMaster.MORTGAGEAREA.value, 0) != 0 else []

        for por in mortgagedList:
            js_mortgagedInfo = dict()

            status_value = "OK"

            js_mortgagedInfo['MORTGAGED_PLOT'] = str(por.name)
            js_mortgagedInfo['PROPOSED_PLOT_AREA'] = str(por.area)
            js_mortgagedInfo['PLOT_LENGTH'] = str(por.length)
            js_mortgagedInfo['PLOT_WIDTH'] = str(por.width)
            js_mortgagedInfo['STATUS'] = str(status_value)
            js_mortgageInfoList.append(js_mortgagedInfo)

        self.reportextract.append({"MORTGAGE_PLOTS_DETAILS": [dict(sorted(dct.items())) for dct in js_mortgageInfoList]})

    def get4_group_details(self):

        js_buffer_dataList = list()
        js_leftoverownersland_dataList = list()
        js_notinpossession_dataList = list()
        js_waterbodies_dataList = list()

        try:

            bufferZoneResponse = checkBufferZoneWaterBodiesLocationWithPlot(self.modelspace)
            get_current_logger().debug(f'checkBufferZoneWaterBodiesLocationWithPlot:\n{bufferZoneResponse}')
            bzReturnCode = bufferZoneResponse.get('CODE', 99)
            if (bzReturnCode == 0):
                js_bufferZoneDictNew = bufferZoneResponse.get('RESULTS', dict())
                js_buffer_dataList = js_bufferZoneDictNew.get('BUFFER_DATA', [])
                js_leftoverownersland_dataList = js_bufferZoneDictNew.get('LEFTOVEROWNERSLAND_DATA', [])
                js_notinpossession_dataList = js_bufferZoneDictNew.get('NOTINPOSSESSION_DATA', [])
                js_waterbodies_dataList = js_bufferZoneDictNew.get('WATERBODIES_DATA', [])


            else:
                bzError = bufferZoneResponse.get('ERROR', 'Not Available')
                get_current_logger().error(f'PROBLEM >>>> GETTING BufferZone Response due to {bzError}')

        except Exception as excp:
            get_current_logger().exception(f'Problem running Buffer zone w/ plot checks:\n{excp}')

        self.reportextract.append({"BUFFER_ZONE_DETAILS": [dict(sorted(dct.items())) for dct in js_buffer_dataList]})

        self.reportextract.append(
            {"LEFTOVER_OWNERSLAND_DETAILS": [dict(sorted(dct.items())) for dct in js_leftoverownersland_dataList]})
        self.reportextract.append(
            {"NOT_IN_POSSESSION_DETAILS": [dict(sorted(dct.items())) for dct in js_notinpossession_dataList]})
        self.reportextract.append({"WATER_BODIES_DETAILS": [dict(sorted(dct.items())) for dct in js_waterbodies_dataList]})

    def get2_main_internal_road_width_details(self):

        js_mainAndInteralRoad_dataList = list()
        js_mainAndInteralRoad_Error = list()

        try:

            mainInternalRoadCheckResponse = checkMainAndInternalRoadWidthsInOpenLayout(self.modelspace)

            miRoadReturnCode = mainInternalRoadCheckResponse.get('CODE', 99)
            if (miRoadReturnCode == 0):
                js_mainAndInteralRoad_dataList = mainInternalRoadCheckResponse.get('RESULTS', [])

            else:
                js_mainAndInteralRoad_Error.append(mainInternalRoadCheckResponse.get('ERROR', 'Not Available'))
                get_current_logger().error(
                    f'PROBLEM >>>> GETTING checkMainAndInternalRoadWidthsInOpenLayout due to:\n{js_mainAndInteralRoad_Error}')

        except Exception as excp:
            get_current_logger().exception(f'Problem running checkMainAndInternalRoadWidthsInOpenLayout:\n{excp}')

        self.reportextract.append(
            {"MAIN_INTERNAL_ROAD_WIDTH_CHECKS": [dict(sorted(dct.items())) for dct in js_mainAndInteralRoad_dataList]})
        self.reportextract.append({"MAIN_INTERNAL_ROAD_WIDTH_CHECKS_ERRORS": js_mainAndInteralRoad_Error})

    def get_mortgage_plot_list_details(self):

        mortgagedSubplotsUnitsResponse = get_mortgagedSubplots4OpenLayout(self.modelspace)

        mortgagedSubplotsUnitsListDirect = mortgagedSubplotsUnitsResponse.get('MORTGAGED_SUBPLOTS_LIST', [])

        js_mortagedSubplotListN = []
        status_value = "OK"
        for idx, subplot in enumerate(mortgagedSubplotsUnitsListDirect):

            js_mortagedSubplotDictN = dict()
            js_mortagedSubplotDictN['Sno'] = str(idx + 1)
            js_mortagedSubplotDictN['SubPlotRef'] = str(subplot)
            js_mortagedSubplotDictN['Status'] = str(status_value)
            js_mortagedSubplotListN.append(js_mortagedSubplotDictN)

        self.reportextract.append({"MORTGAGE_PLOTS_LIST": [dict(sorted(dct.items())) for dct in js_mortagedSubplotListN]})

    def get4_groupbymortgage_subplot(self):

        js_mortgagePlotInfoList = []

        status_value = "OK"

        mortgagedList = self.combinedObjects.get(
            LayerMaster.MORTGAGEAREA.value).getBaseUnitFinalList() if self.combinedObjects.get(
            LayerMaster.MORTGAGEAREA.value, 0) != 0 else []

        plotList = self.combinedObjects.get(LayerMaster.OPENLAYOUT.value).getBaseUnitFinalList() if self.combinedObjects.get(
            LayerMaster.OPENLAYOUT.value, 0) != 0 else []

        totalSubplotMortagedArea = 0.0

        for mortarea in mortgagedList:
            mortlwpoly_coords = re_round(list(mortarea.polygon.exterior.coords), 2)
            mortlwpolyObjPoly = Polygon(mortlwpoly_coords)
            mortlwpoly = shapely.wkt.loads(str(mortarea.polygon))
            mortageLevelPlottedArea = 0.0
            for subplot in plotList:

                subplot_coords = re_round(list(subplot.polygon.exterior.coords), 2)
                subplotObjPoly = Polygon(subplot_coords)

                subplotlwpoly = shapely.wkt.loads(str(subplot.polygon))

                if (subplotObjPoly.within(mortlwpoly) or subplotObjPoly.within(mortlwpolyObjPoly) \
                        or subplotlwpoly.within(mortlwpoly)):
                    mortageLevelPlottedArea = mortageLevelPlottedArea + subplot.area
                    totalSubplotMortagedArea = totalSubplotMortagedArea + subplot.area

                    js_mortgagedInfo = dict()
                    js_mortgagedInfo['MORTGAGED_PLOT'] = str(subplot.name)
                    js_mortgagedInfo['PROPOSED_PLOT_AREA'] = str(subplot.area)
                    js_mortgagedInfo['PLOT_LENGTH'] = str(subplot.length)
                    js_mortgagedInfo['PLOT_WIDTH'] = str(subplot.width)
                    js_mortgagedInfo['STATUS'] = str(status_value)
                    js_mortgagePlotInfoList.append(js_mortgagedInfo)

            get_current_logger().debug(f'Mortage Area vs Subplotted Area {mortarea.name} '
                                f'mortaged area {mortarea.area} '
                                f'subplotted area {mortageLevelPlottedArea}')

        js_MortagePlotSummary = dict()

        js_MortagePlotSummary['TOTAL_MORTGAGE_SUBPLOTS_NOS'] = str(len(js_mortgagePlotInfoList))
        js_MortagePlotSummary['TOTAL_MORTGAGE_SUBPLOTS_AREA'] = str(round(totalSubplotMortagedArea, 2))

        self.reportextract.append({"MORTGAGE_SUBPLOTS_SUMMARY": dict(sorted(js_MortagePlotSummary.items()))})
        self.reportextract.append(
            {"MORTGAGE_SUBPLOTS_DETAILS": [dict(sorted(dct.items())) for dct in js_mortgagePlotInfoList]})

        self.reportextract.append(
            {"MORTGAGE_SUBPLOTS_SUMMARY_OVERLAP": dict()})  # js_MortagePlotSummaryOverlap ) )  #Fix 9/25 disabled
        self.reportextract.append({"MORTGAGE_SUBPLOTS_DETAILS_OVERLAP": []})  # js_mortgagePlotInfoListOverlap )

    def get_misc_socialinfra_checks(self):

        socialInfraList = self.combinedObjects.get(
            LayerMaster.SOCIALINFRA.value).getBaseUnitFinalList() if self.combinedObjects.get(
            LayerMaster.SOCIALINFRA.value, 0) != 0 else []

        totList = self.combinedObjects.get(LayerMaster.ORGOPENSPACE.value).getBaseUnitFinalList()

        accessoryUnitsList = self.combinedObjects.get(
            LayerMaster.ACCESSORYUSE.value).getBaseUnitFinalList() if self.combinedObjects.get(
            LayerMaster.ACCESSORYUSE.value, 0) != 0 else []

        js_socialInfraToOrgSpaceUtilityInfoList = []
        # socialInfraList totList
        for socObj in socialInfraList:
            js_socialInfraToOrgSpaceUtilityInfo = dict()

            for orgopenspace in totList:

                responseValue = doObjectsTouchEachOther(socObj.polygon, orgopenspace.polygon)
                if (responseValue is not None and responseValue == True):
                    js_socialInfraToOrgSpaceUtilityInfo['SOURCE_TYPE'] = 'SOCIALINFRA'
                    js_socialInfraToOrgSpaceUtilityInfo['SOURCE_NAME'] = socObj.name
                    js_socialInfraToOrgSpaceUtilityInfo['SOURCE_AREA'] = socObj.area
                    js_socialInfraToOrgSpaceUtilityInfo['TARGET_TYPE'] = 'ORG_OPEN_SPACE'
                    js_socialInfraToOrgSpaceUtilityInfo['TARGET_NAME'] = orgopenspace.name
                    js_socialInfraToOrgSpaceUtilityInfo['TARGET_AREA'] = orgopenspace.area
                    js_socialInfraToOrgSpaceUtilityInfo['STATUS'] = 'NOT OK'
                    js_socialInfraToOrgSpaceUtilityInfo[
                        'RULE_APPLICABLE'] = 'Social Infra should not touch Org. Open Space Areas'
                    js_socialInfraToOrgSpaceUtilityInfoList.append(js_socialInfraToOrgSpaceUtilityInfo)

            for utility in accessoryUnitsList:

                if (utility.name.upper() in "UTILITY"):

                    responseValue = doObjectsTouchEachOther(socObj.polygon, utility.polygon)
                    if (responseValue is not None and responseValue == True):
                        js_socialInfraToOrgSpaceUtilityInfo['SOURCE_TYPE'] = 'SOCIALINFRA'
                        js_socialInfraToOrgSpaceUtilityInfo['SOURCE_NAME'] = socObj.name
                        js_socialInfraToOrgSpaceUtilityInfo['SOURCE_AREA'] = socObj.area
                        js_socialInfraToOrgSpaceUtilityInfo['TARGET_TYPE'] = 'UTILITY'
                        js_socialInfraToOrgSpaceUtilityInfo['TARGET_NAME'] = utility.name
                        js_socialInfraToOrgSpaceUtilityInfo['TARGET_AREA'] = utility.area
                        js_socialInfraToOrgSpaceUtilityInfo['STATUS'] = 'NOT OK'
                        js_socialInfraToOrgSpaceUtilityInfo[
                            'RULE_APPLICABLE'] = 'Social Infra should not touch Utility Areas'
                        js_socialInfraToOrgSpaceUtilityInfoList.append(js_socialInfraToOrgSpaceUtilityInfo)

        self.reportextract.append({"MISC_CHECKS_SOCIALINFRA_OPENSPACE_UTILITY": js_socialInfraToOrgSpaceUtilityInfoList})

    def get_misc_internalroad_checks(self):

        internalRoadList = self.combinedObjects.get(
            LayerMaster.INTERNALROAD.value).getBaseUnitFinalList() if self.combinedObjects.get(
            LayerMaster.INTERNALROAD.value, 0) != 0 else []

        socialInfraList = self.combinedObjects.get(
            LayerMaster.SOCIALINFRA.value).getBaseUnitFinalList() if self.combinedObjects.get(
            LayerMaster.SOCIALINFRA.value, 0) != 0 else []

        accessoryUnitsList = self.combinedObjects.get(
            LayerMaster.ACCESSORYUSE.value).getBaseUnitFinalList() if self.combinedObjects.get(
            LayerMaster.ACCESSORYUSE.value, 0) != 0 else []

        js_internalRoadToUtilitySocialList = []
        # socialInfraList totList
        for internalRoad in internalRoadList:
            js_internalRoadToUtilitySocialInfo = dict()

            for socObj in socialInfraList:

                responseValue = doObjectsTouchEachOther(socObj.polygon, internalRoad.polygon)
                if (responseValue is not None and responseValue == True):
                    js_internalRoadToUtilitySocialInfo['SOURCE_TYPE'] = 'INTERNALROAD'
                    js_internalRoadToUtilitySocialInfo['SOURCE_NAME'] = internalRoad.name
                    js_internalRoadToUtilitySocialInfo['SOURCE_AREA'] = str(internalRoad.area)
                    js_internalRoadToUtilitySocialInfo['TARGET_TYPE'] = 'ORG_OPEN_SPACE'
                    js_internalRoadToUtilitySocialInfo['TARGET_NAME'] = socObj.name
                    js_internalRoadToUtilitySocialInfo['TARGET_AREA'] = str(socObj.area)
                    js_internalRoadToUtilitySocialInfo['STATUS'] = 'OK'
                    js_internalRoadToUtilitySocialInfo[
                        'RULE_APPLICABLE'] = 'Social Infra should touch atleast one internal road'
                    js_internalRoadToUtilitySocialList.append(js_internalRoadToUtilitySocialInfo)

            for utility in accessoryUnitsList:

                if (utility.name.upper() in "UTILITY"):

                    responseValue = doObjectsTouchEachOther(internalRoad.polygon, utility.polygon)
                    if (responseValue is not None and responseValue == True):
                        js_internalRoadToUtilitySocialInfo['SOURCE_TYPE'] = 'INTERNALROAD'
                        js_internalRoadToUtilitySocialInfo['SOURCE_NAME'] = internalRoad.name
                        js_internalRoadToUtilitySocialInfo['SOURCE_AREA'] = str(internalRoad.area)
                        js_internalRoadToUtilitySocialInfo['TARGET_TYPE'] = 'UTILITY'
                        js_internalRoadToUtilitySocialInfo['TARGET_NAME'] = utility.name
                        js_internalRoadToUtilitySocialInfo['TARGET_AREA'] = str(utility.area)
                        js_internalRoadToUtilitySocialInfo['STATUS'] = 'OK'
                        js_internalRoadToUtilitySocialInfo[
                            'RULE_APPLICABLE'] = 'Utility area should touch atleast one internal road'
                        js_internalRoadToUtilitySocialList.append(js_internalRoadToUtilitySocialInfo)

        self.reportextract.append({"MISC_CHECKS_INTERNALROAD_SOCIALINFRA_UTILITY": [dict(sorted(dct.items())) for dct in
                                                                               js_internalRoadToUtilitySocialList]})

    def get_misc_cycletrack_checks(self):

        js_cycleTrackList = []

        cycleTrackUnitsList = self.combinedObjects.get(
            LayerMaster.CYCLETRACK.value).getBaseUnitFinalList() if self.combinedObjects.get(
            LayerMaster.CYCLETRACK.value, 0) != 0 else []

        totList = self.combinedObjects.get(LayerMaster.ORGOPENSPACE.value).getBaseUnitFinalList()

        for por in cycleTrackUnitsList:

            cycleTrackInsideTOTResultDict = isChildWithinParentObject('CycleTrack', 'OrgOpenSpace', por, totList)

            if (cycleTrackInsideTOTResultDict is not None and cycleTrackInsideTOTResultDict.get('iswithin',
                                                                                                False) != False):
                statusValue = "OK"

            else:
                statusValue = "NOT OK"

            parentName = '-' if cycleTrackInsideTOTResultDict is None else cycleTrackInsideTOTResultDict.get(
                'parentName', 'N/A')

            js_cycleTrackInfo = dict()

            js_cycleTrackInfo['CYCLE_TRACK_NAME'] = str(por.name)
            js_cycleTrackInfo['REFERENCE_ID'] = str(por.handle)
            js_cycleTrackInfo['WITHIN'] = str(parentName)
            js_cycleTrackInfo['LENGTH'] = str(por.length)
            js_cycleTrackInfo['WIDTH'] = str(por.width)
            js_cycleTrackInfo['AREA'] = str(por.area)
            js_cycleTrackInfo['STATUS'] = str(statusValue)
            js_cycleTrackList.append(js_cycleTrackInfo)

        self.reportextract.append({"MISC_CHECKS_CYCLE_TRACK": [dict(sorted(dct.items())) for dct in js_cycleTrackList]})

    def get_misc_utilities_check(self):

        js_utilityMiscUnitsList = []

        utilityMiscUnitsList = self.combinedObjects.get(
            LayerMaster.UTILITY_MISC.value).getBaseUnitFinalList() if self.combinedObjects.get(
            LayerMaster.UTILITY_MISC.value, 0) != 0 else []
        accessoryUnitsList = self.combinedObjects.get(
            LayerMaster.ACCESSORYUSE.value).getBaseUnitFinalList() if self.combinedObjects.get(
            LayerMaster.ACCESSORYUSE.value, 0) != 0 else []

        for por in utilityMiscUnitsList:

            miscUtilInsideAccessoryResultDict = isChildWithinParentObject('Misc. Accessory', 'Utility', por,
                                                                          accessoryUnitsList)

            if (miscUtilInsideAccessoryResultDict is not None and miscUtilInsideAccessoryResultDict.get('iswithin',
                                                                                                        False) != False):
                statusValue = "OK"

            else:
                statusValue = "NOT OK"

            parentName = '-' if miscUtilInsideAccessoryResultDict is None else miscUtilInsideAccessoryResultDict.get(
                'parentName', 'N/A')

            js_utilityMiscInfo = dict()
            js_utilityMiscInfo['UTILITY_NAME'] = str(por.name)
            js_utilityMiscInfo['REFERENCE_ID'] = str(por.handle)
            js_utilityMiscInfo['WITHIN'] = str(parentName)

            js_utilityMiscInfo['LENGTH'] = str(por.length)
            js_utilityMiscInfo['WIDTH'] = str(por.width)
            js_utilityMiscInfo['AREA'] = str(por.area)

            js_utilityMiscInfo['STATUS'] = str(statusValue)

            js_utilityMiscUnitsList.append(js_utilityMiscInfo)

        self.reportextract.append(
            {"MISC_CHECKS_OF_UTILITIES": [dict(sorted(dct.items())) for dct in js_utilityMiscUnitsList]})

    def get_misc_socialinfra_amenity(self):
        checkAmentiesSocialInDrawingResponseList = []
        try:
            checkAmentiesSocialInDrawingResponse = checkAmentiesSocialInfra_OpenLayouts(self.modelspace)
            checkAmentiesSocialInDrawingResponseList = checkAmentiesSocialInDrawingResponse.get("RESULTS", [])

        except Exception as excp:
            errorMsg = f'problem running checkAmentiesSocialInfra  for OPEN LAYOUTS {excp}'
            get_current_logger().exception(errorMsg)

        self.reportextract.append({"MISC_CHECKS_OF_AMENITIES_SOCIALINFRA": [dict(sorted(dct.items())) for dct in
                                                                       checkAmentiesSocialInDrawingResponseList]})

    def get_misc_facility_area_check(self):

        checkFacilitiesInDrawingResponseList = []

        checkFacilitiesInDrawingResponseErrorsList = []
        try:

            checkFacilitiesInDrawingResponse = checkFacilities_OpenLayouts(self.modelspace)
            checkFacilitiesInDrawingResponseList = checkFacilitiesInDrawingResponse.get("RESULTS", [])

            errorDict = dict()
            errorDict["errors"] = str(checkFacilitiesInDrawingResponse.get("ERROR", []))
            checkFacilitiesInDrawingResponseErrorsList.append(errorDict)
            get_current_logger().debug(f'Response :\n{checkFacilitiesInDrawingResponse}')

        except Exception as excp:
            errorMsg = 'problem running checkFacilities  for OPEN LAYOUTS ' + str(excp)
            get_current_logger().exception(errorMsg)

        self.reportextract.append({"MISC_CHECKS_OF_FACILITY_AREA": checkFacilitiesInDrawingResponseList})
        self.reportextract.append({"MISC_CHECKS_OF_FACILITY_AREA_ERRORS": checkFacilitiesInDrawingResponseErrorsList})

    def get_common_layer_validation(self):

        checkCommonLayersInDrawingResponseDict = []
        try:

            checkCommonLayersInDrawingResponseDict = checkCommonLayersInOpenLayout(self.modelspace)

        except Exception as excp:
            errorMsg = f'problem running CommonValidationLayer  for OPEN LAYOUTS {excp}'
            get_current_logger().exception(errorMsg)

        self.reportextract.append({"DRAWING_COMMONLAYER_VALIDATIONS": dict(sorted(checkCommonLayersInDrawingResponseDict.items()))})

    def get_drawing_layers(self):

        try:

            self.reportextract.append({"DRAWING_LAYERS": dict(sorted(self.combinedObjects.get('dwg_layers',{}).items()))})

        except Exception as layerIssue:

            errorMsg = f'problem due to encoding issue in layer names - {self.combinedObjects.get("dwg_layers", 0)}'
            get_current_logger().exception(errorMsg)
            self.reportextract.append({"DRAWING_LAYERS": {}})

    def execute_step(self, step_no,total_step, step_name, step_function):

        try:
            start_time = time.time()
            get_current_logger().info("=" * 80)
            get_current_logger().info(f"Step{step_no}/{total_step} STARTED : {step_name}")
            get_current_logger().info("=" * 80)

            processing_steps_dict=dict()
            processing_steps_dict["CurrentStep"] = f"{step_name} Processing ..."
            processing_steps_dict["Progress"] = self.progress
            processing_steps_dict["Steps"] = f"{step_no}/{total_step}"
            self.Status_dict["Step_data"] = processing_steps_dict
            # send_status(self.request_id, self.Status_dict, self.requesttimeobj)

            # time.sleep(1)

            step_function()

            completed_progress = int(
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

            self.progress = completed_progress

            elapsed = round(time.time() - start_time, 2)
            completed_steps_dict= dict()
            completed_steps_dict["CurrentStep"] = f"{step_name} Completed."
            completed_steps_dict["TotalTime"] = f"{elapsed} sec"
            completed_steps_dict["Progress"] = self.progress
            completed_steps_dict["Steps"] = f"{step_no}/{total_step}"

            self.Status_dict["Step_data"] = completed_steps_dict
            self.Status_dict["Progress"] = main_completed_progress

            # send_status(self.request_id, self.Status_dict, self.requesttimeobj)

            get_current_logger().info(
                f"Step{step_no}/{total_step} COMPLETED : {step_name} | Time Taken : {elapsed} sec"
            )
            # time.sleep(0.5)

        except Exception as e:

            elapsed = round(time.time() - start_time, 2)

            error_msg = {
                "step": step_no,
                "step_name": step_name,
                "error": str(e),
                "time_taken": elapsed
            }

            self.errors.append(error_msg)

            get_current_logger().info("=" * 80)
            get_current_logger().info(f"{step_no} FAILED : {step_name}")
            get_current_logger().info(f"ERROR : {str(e)}")
            get_current_logger().info(traceback.format_exc())
            get_current_logger().info("=" * 80)

            failed_steps_dict= dict()
            self.Status_dict["Status"] = "Failed"
            failed_steps_dict["CurrentStep"] = f"{step_name} Processing ..."
            failed_steps_dict["Steps"] = f"{step_no}/{total_step}"
            failed_steps_dict["Progress"] = self.progress
            self.Status_dict["Step_data"] = failed_steps_dict
            self.Status_dict["Error"] = self.responseDict.get("errors","Problem Generating Report")
            # send_status(self.request_id,self.Status_dict,self.requesttimeobj)

    def get_details(self):

        steps=[
            ("Request Summary",self.get_request_summary),
            ("Plot Summary",self.get_plot_summary),
            ("NetPlot Summary",self.get_netplot_summary),
            ("Land Usage Details",self.get_landusage_details),
            ("Mortgage Summary",self.get_mortgage_summary),
            ("Organized Open Space And GrinStrip Summary",self.get_orgGreenStrip_summary),
            ("Organized Open Space Details",self.get_org_openspace_detail),
            ("Green Strip & Belt Details",self.get_green_belt_detail),
            ("Splay Check Summary",self.get_splay_check_summary),
            ("Splay Details",self.get_splay_details),
            ("Main Road Summary",self.get_mainRoad_details),
            ("Internal Details Summary",self.get_internalroad_details),
            ("GridRoad Details",self.get_gridroad_details),
            ("Sub Plot Summary",self.get_subplot_summary),
            ("Sub Plot Details",self.get_subplot_details),
            ("Mortgage Plot Summary",self.get_mortgage_plot_summary),
            ("Mortgage Plot Details",self.get_mortgage_plot_details),
            ("Buffer Zone, "
             "Left Owners Land, "
             "Not In Possession And "
             "Water Bodies Details",self.get4_group_details),
            ("Main And Internal Road Width Check",self.get2_main_internal_road_width_details),
            ("Mortgage Plot Details",self.get_mortgage_plot_list_details),
            ("Mortgage SubPlot And Overlap Details",self.get4_groupbymortgage_subplot),
            ("Misc SocialInfrastructure Checks",self.get_misc_socialinfra_checks),
            ("Misc InternalRoad Checks",self.get_misc_internalroad_checks),
            ("Misc Cycle Track Checks",self.get_misc_cycletrack_checks),
            ("Misc Utility Checks",self.get_misc_utilities_check),
            ("Misc SocialInfra & Amenity Checks",self.get_misc_socialinfra_amenity),
            ("Misc Facility Area Checks",self.get_misc_facility_area_check),
            ("Common Layer Validation",self.get_common_layer_validation),
            ("Drawing Layers",self.get_drawing_layers),
        ]

        total_steps=len(steps)

        for index, (step_name, step_function) in enumerate(steps, start=1):

            self.execute_step(
                index,
                total_steps,
                step_name,
                step_function
            )
        self.reportextract.append({"DRAWING_WARNINGS": self.combinedObjects.get('DWG_WARNINGS', [])})

        self.responseDict["responseCode"] = SUCCESS_CODE
        self.responseDict["dwgExtract"] = self.reportextract

        return self.responseDict

def populateIndivPolyListObj(layerName, subPlots, pltNames, plotList, plotDict, internalRoadList: None):
    if (layerName is None or subPlots is None or pltNames is None or plotList is None):
        error_msg = "One or more of required inputs are None. Returning error response for " + layerName

        get_current_logger().error("populateIndivPolyListObj :: " + error_msg)

        return {"result": "error", "msg": error_msg}

    get_current_logger().debug("list of polygons len " + str(len(subPlots)))
    get_current_logger().debug("list of labels len " + str(len(pltNames)))
    # iterate through subPlots
    processedPlotDict = dict()
    matchedPlotDict = dict()

    prepared_points= []
    point_map= {}

    # track unique coordinates
    unique_points = set()
    unique_polygons = set()

    for ptId in pltNames:

        xyP = ptId.get_points()[0].split(" ")

        x = round(float(xyP[0]), 2)
        y = round(float(xyP[1]), 2)

        # unique key
        key = (x, y)
        # skip duplicates
        if key in unique_points:

            get_current_logger().warning("Skip Duplicate Point object")
            continue

        unique_points.add(key)
        pt = Point(x, y)
        prepared_points.append(pt)
        point_map[key] = ptId

        # point_map[id(pt)] = ptId

    point_tree = STRtree(prepared_points)

    for plotObj in subPlots:

        get_current_logger().debug("Processsing handle # " + str(plotObj.handle) + " points : " + str(
            plotObj.get_points()) + " isclosed : " + str(plotObj.isClosed()))

        if (plotObj.handle not in processedPlotDict):
            processedPlotDict[plotObj.handle] = plotObj.handle
        else:
            continue

        if not plotObj.isClosed():
            get_current_logger().warning('Skip polyline not closed object')
            continue

        # create polygon key
        poly_key = tuple([
            tuple(map(lambda v: round(float(v), 2), p.split(" ")))
            for p in plotObj.get_points()
        ])

        # skip duplicate polygon
        if poly_key in unique_polygons:
            get_current_logger().warning('Skip Duplicate Polygon object')
            continue

        unique_polygons.add(poly_key)

        polyStr = str(plotObj.get_points())[1:-1].translate(translation)

        polyPoints = f'POLYGON (({polyStr}))'

        lwpoly = shapely.wkt.loads(polyPoints)

        candidate_points = point_tree.query(lwpoly)

        for idx in candidate_points:

            pt = prepared_points[idx]

            key = (round(pt.x, 2), round(pt.y, 2))
            ptId = point_map[key]

        # for ptId in pltNames:
        #
        #     get_current_logger().debug("point ID " + str(ptId.handle))
        #     xyP = ptId.get_points()[0].split(" ")
        #     xyP_Str = xyP[0], "-", xyP[1]
        #
        #     pt = Point(round(float(xyP[0]), 2), round(float(xyP[1]), 2))
        #     get_current_logger().debug(" point ID " + str(ptId.handle) + '  point ::: ' + str(xyP_Str))
        #
        #     if plotObj.isClosed() == False:
        #         server_logger.warning('polyline not closed object breaking loop')
        #         break
        #
        #     # polyStr = str(plotObj.get_points())[1:-1].translate(translation)
        #     # server_logger.debug(f"Polygon String coordates {polyStr}")
        #     # # create a ploygon
        #     # polyPoints = 'POLYGON ((' + polyStr + '))'
        #     #
        #     # lwpoly = shapely.wkt.loads(polyPoints)
        #     processedPlotDict[plotObj.handle] = round(lwpoly.area, 2)

            # or pt.distance(lwpoly) < 0.5
            if (lwpoly.contains(pt) or pt.touches(lwpoly) or pt.intersects(lwpoly)):

                matchedPlotDict[plotObj.handle] = ptId.handle

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
                get_current_logger().debug('area before ' + str(area_polygon))

                # if arc reduce segment area from polygon
                if (plotObj.hasBulge == True or plotObj.splayOverride == True):
                    seg_area = plotObj.get_segment()

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

def populateIndivPolyListObjNoNames(layerName, subPlots, plotList, plotDict, internalRoadList: None):
    if (layerName is None or subPlots is None or plotList is None):
        error_msg = "One or more of required inputs are None. Returning error response for {layerName}"
        get_current_logger().error("populateIndivPolyListObj :: " + error_msg)
        return {"result": "error", "msg": error_msg}

    get_current_logger().info(f"subplots len {len(subPlots)}")
    # iterate through subPlots
    unique_polygons=set()

    processedPlotDict = dict()

    for plotObj in subPlots:
        get_current_logger().debug("processsing handle # " + str(plotObj.handle) + " points : " + str(
            plotObj.get_points()) + " isclosed : " + str(plotObj.isClosed()))

        if (plotObj.handle not in processedPlotDict):
            processedPlotDict[plotObj.handle] = plotObj.handle
        else:
            continue

        if not plotObj.isClosed():
            get_current_logger().warning('Skip polyline not closed object')
            continue

        poly_key = tuple([
            tuple(map(lambda v: round(float(v), 2), p.split(" ")))
            for p in plotObj.get_points()
        ])

        if poly_key in unique_polygons:

            get_current_logger().warning("Skip polyline duplicate object")
            continue

        unique_polygons.add(plotObj)


        polyStr = str(plotObj.get_points())[1:-1].translate(translation)

        polyPoints = 'POLYGON ((' + polyStr + '))'

        lwpoly = shapely.wkt.loads(polyPoints)
        box = lwpoly.minimum_rotated_rectangle
        x, y = box.exterior.coords.xy

        # get length of bounding box edges
        edge_length = (Point(x[0], y[0]).distance(Point(x[1], y[1])), Point(x[1], y[1]).distance(Point(x[2], y[2])))
        # get length of polygon as the longest edge of the bounding box
        length = max(edge_length)
        # get width of polygon as the shortest edge of the bounding box
        width = min(edge_length)
        area_polygon = lwpoly.area

        # if arc reduce segment area from polygon
        if (plotObj.hasBulge == True):
            seg_area = plotObj.get_segment()
            bounding_box2d = ezdxf.math.BoundingBox2d([xy[0:2] for xy in list(plotObj.get_rawpoints())])

            width, length = bounding_box2d.size
            get_current_logger().debug(f"width and length dimensions {round(width, 2)} : {round(length, 2)}")

            if (seg_area < 0):
                area_polygon = area_polygon + seg_area
            else:
                area_polygon = area_polygon - seg_area

            get_current_logger().debug('segment area ' + str(seg_area) + ' splay area is now ' + str(area_polygon))

        if (layerName == "_Splay" or layerName == "_MainRoad" or layerName == "_InternalRoad" or layerName == "_RoadWidening" \
                or layerName == LayerMaster.EXISTING_PLINTH_AREA.value or layerName == LayerMaster.PROPOSED_PLINTH_AREA.value \
                or layerName == LayerMaster.BUA_BEFORE_CONCESSION.value or layerName == LayerMaster.TRANSFER_OF_SETBACKS.value) and plotObj.handle not in plotDict:

            p6 = IndivSubPlot(plotObj.handle, layerName, lwpoly, length, width, area_polygon, plotObj.handle)

            p6.setColor(str(plotObj.getColor()))

            # need this to check splay dimensions based on the road width -
            if (layerName == "_Splay"):
                bbox = lwpoly.bounds
                splayPoly = shapely.geometry.box(*bbox, ccw=True)
                abuttingroad_frontage = extractAbuttingRoadForSplay(splayPoly, internalRoadList, plotObj.handle)
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


class ProcessOpenLayout:

    def __init__(self,dxf_file,request_id,filename,layerDict,request_params,status_dict:dict,requesttimeobj):
        self.dxf_file=dxf_file
        self.msp = self.dxf_file.modelspace()
        self.request_id=request_id
        self.filename=filename
        self.responsedict = dict()
        self.combinedObjects = dict()
        self.warnings=[]
        self.errors=[]
        self.request_params=request_params
        self.status_dict=status_dict
        self.road_list=[]
        self.layerDict=layerDict
        self.progress=0
        self.requesttimeobj=requesttimeobj

        self.main1min_progress = 20
        self.main1max_progress = 40

    def layers_extract(self):
        self.layerDict = {layer.dxf.name: str(layer.is_on()) for layer in self.dxf_file.layers}

        return self.layerDict

    def check_layers(self):
        # check mandatory open layout checks
        layers_check = []

        for opLay in MANDATORY_LAYERS_FOR_PLAN_TYPE['Open_Layout']:
            if (opLay not in self.layerDict):
                layers_check.append(
                    "Layer " + opLay + " is required but is not found. Layer names are case sensitive. ")

            elif (self.layerDict.get(opLay, 'False') == 'False'):

                layers_check.append(" Layer " + opLay + " should be Visible but is " + self.layerDict.get(opLay, 'False'))

        return layers_check

    def MainRoad_details(self):

        pop_msg_area = LayerMaster.MAINROAD.value
        pop_msg_refid = "1.0"

        mainRoadObjInst = ObjectByType(pop_msg_area)
        mainRoadDict = mainRoadObjInst.getBaseUnitDict()
        mainRoadList = mainRoadObjInst.getBaseUnitFinalList()

        mainRoadAreaPlots = extractSubPlot(self.msp, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, True, False)

        mainRoadNames = extractSubPlot(self.msp, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)

        mainRoadObjInst.setBaseList(mainRoadAreaPlots)
        mainRoadObjInst.setBaseUnitNames(mainRoadNames)
        pop_dict_msg = populateIndivPolyListObj(pop_msg_area, mainRoadAreaPlots, mainRoadNames, mainRoadList,
                                                mainRoadDict,
                                                None)

        resultCode = pop_dict_msg.get("result")
        if pop_dict_msg == None or resultCode == "error":

            msgtx = "".join(
                [pop_msg_refid + ".4 Error processing [ ", pop_msg_area, " ] Area Section Return is ", pop_dict_msg])
            self.warnings.append(msgtx)
        else:
            if (resultCode == "OK"):

                areaObjList = pop_dict_msg.get("data_list")

                warnings = pop_dict_msg.get("warnings", None)

                if (warnings is not None and len(warnings) > 0):
                    countWarnings = len(warnings)
                    msgtx = "  ".join([pop_msg_area, ' count mismatch after processing expecting ',
                                       str(len(areaObjList) + countWarnings), " got ", str(len(areaObjList)),
                                       ' details ', " - ".join(warnings)])
                    self.warnings.append(msgtx)

                # refactor-3
                areaObjDict = pop_dict_msg.get("data_dict", None)

                # overwrite with the data returned from function
                mainRoadObjInst.setBaseUnitDict(areaObjDict)
                mainRoadObjInst.setBaseUnitFinalList(areaObjList)
                # combined objects
                self.combinedObjects[pop_msg_area] = mainRoadObjInst

    def GridRoad_details(self):
        pop_msg_area = LayerMaster.MAINROAD.value
        currentStep = "INTERNALROAD"
        internalRoadDirectResponse = dict()
        gridRoadDirectResponse = dict()
        try:
            internalRoadDirectResponse = getInternalRoadWidth(LayerMaster.INTERNALROAD.value,
                                                              self.msp)  # dxffile_dir, inputFilename )

            currentStep = "GRIDROAD"
            gridRoadDirectResponse = getInternalRoadWidth(LayerMaster.GRIDROAD.value, self.msp)

        except:
            msg = pop_msg_area + ", problem reading the road width using direct method for " + currentStep
            get_current_logger().error(msg)

            ex_type, ex_value, ex_traceback = sys.exc_info()

            # Extract unformatter stack traces as tuples
            trace_back = traceback.extract_tb(ex_traceback)

            # Format stacktrace
            stack_trace = list()

            for trace in trace_back:
                stack_trace.append(
                    "File : %s , Line : %d, Func.Name : %s, Statement : %s" % (trace[0], trace[1], trace[2], trace[3]))

            self.warnings.append(msg + " due to : " + str(ex_value))
            get_current_logger().debug(f"Stack trace : {stack_trace}")

        self.combinedObjects['INTERNALROAD_WIDTHS_NEW'] = internalRoadDirectResponse
        self.combinedObjects['GRIDROAD_WIDTHS_NEW'] = gridRoadDirectResponse

    def InternalRoad_details(self):

        pop_msg_area = LayerMaster.INTERNALROAD.value
        pop_msg_refid = "1.1"

        internalRoadObjInst = ObjectByType(pop_msg_area)
        internalRoadDict = internalRoadObjInst.getBaseUnitDict()
        internalRoadList = internalRoadObjInst.getBaseUnitFinalList()

        internalRoadAreaPlots = extractSubPlot(self.msp, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, False, False)

        roadWithCenterLineProcessedList = mapCenterLinesWithinObjectList(internalRoadAreaPlots)

        internalRoadWidthById = dict()

        if (roadWithCenterLineProcessedList is not None and len(roadWithCenterLineProcessedList) > 0):
            internalRoadAreaPlots = roadWithCenterLineProcessedList
            get_current_logger().debug(f'Final Roads with centre lines {len(roadWithCenterLineProcessedList)}')

            for tmpRoad in roadWithCenterLineProcessedList:
                cListDict = tmpRoad.getMiscProps()
                if (len(cListDict) > 0):
                    centerLineTxt = cListDict.get('centerline', 0)
                    if (centerLineTxt != 0):
                        centerList = getPointsAsListFromString(centerLineTxt)

                        polyStr = str(tmpRoad.get_points())[1:-1].translate(translation)

                        # create a ploygon
                        polyPoints = 'POLYGON ((' + polyStr + '))'

                        lwpoly = shapely.wkt.loads(polyPoints)

                        lpoints = list(lwpoly.exterior.coords)

                        min_Width = getMinWidthByCenterLine(lpoints, centerList)

                        internalRoadWidthById[tmpRoad.handle] = float(min_Width) * 2

            self.combinedObjects['INTERNALROAD_WIDTHS'] = internalRoadWidthById

        else:
            get_current_logger().error(" Unable to extract centre line for internal roads ")

        internalRoadNames = extractSubPlot(self.msp, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)

        internalRoadObjInst.setBaseList(internalRoadAreaPlots)
        internalRoadObjInst.setBaseUnitNames(internalRoadNames)

        pop_dict_msg = populateIndivPolyListObj(pop_msg_area, internalRoadAreaPlots, internalRoadNames,
                                                internalRoadList,
                                                internalRoadDict, None)

        resultCode = pop_dict_msg.get("result")
        if pop_dict_msg == None or resultCode == "error":
            get_current_logger().warning(
                f"{pop_msg_refid} Error processing {pop_msg_area} Area Section Return is {pop_dict_msg}")
        else:
            if (resultCode == "OK"):
                areaObjList = pop_dict_msg.get("data_list")

                # refactor-3
                areaObjDict = pop_dict_msg.get("data_dict", None)

                # overwrite with the data returned from function
                internalRoadObjInst.setBaseUnitDict(areaObjDict)
                internalRoadObjInst.setBaseUnitFinalList(areaObjList)

                # combined objects
                self.combinedObjects[pop_msg_area] = internalRoadObjInst

    def InternalGridRoad_details(self):

        pop_msg_area = LayerMaster.INTERNALROAD.value

        internalRoadAreaPlots = extractSubPlot(self.msp, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, False, False)

        roadWithCenterLineProcessedList = mapCenterLinesWithinObjectList(internalRoadAreaPlots)


        pop_msg_area = LayerMaster.GRIDROAD.value
        pop_msg_refid = "1.1.1"

        gridRoadObjInst = ObjectByType(pop_msg_area)
        gridRoadDict = gridRoadObjInst.getBaseUnitDict()
        gridRoadList = gridRoadObjInst.getBaseUnitFinalList()

        gridRoadAreaPlots = extractSubPlot(self.msp, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, False, False)

        groadWithCenterLineProcessedList = mapCenterLinesWithinObjectList(gridRoadAreaPlots)

        gridRoadWidthById = dict()

        if (groadWithCenterLineProcessedList is not None and len(groadWithCenterLineProcessedList) > 0):
            gridRoadAreaPlots = groadWithCenterLineProcessedList
            get_current_logger().debug(f'Final Roads with centre lines {len(roadWithCenterLineProcessedList)}')
            for tmpRoad in groadWithCenterLineProcessedList:

                cListDict = tmpRoad.getMiscProps()
                if (len(cListDict) > 0):
                    centerLineTxt = cListDict.get('centerline', 0)
                    if (centerLineTxt != 0):
                        centerList = getPointsAsListFromString(centerLineTxt)
                        # print ('Road Polygon ', str(tmpRoad.get_points()) )
                        polyStr = str(tmpRoad.get_points())[1:-1].translate(translation)

                        # create a ploygon
                        polyPoints = 'POLYGON ((' + polyStr + '))'

                        lwpoly = shapely.wkt.loads(polyPoints)

                        lpoints = list(lwpoly.exterior.coords)

                        min_Width = getMinWidthByCenterLine(lpoints, centerList)

                        gridRoadWidthById[tmpRoad.handle] = float(min_Width) * 2

            self.combinedObjects['GRIDROAD_WIDTHS'] = gridRoadWidthById

        else:
            get_current_logger().error(' Unable to extract centre line for grid roads ')

        gridRoadNames = extractSubPlot(self.msp, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)

        gridRoadObjInst.setBaseList(gridRoadAreaPlots)
        gridRoadObjInst.setBaseUnitNames(gridRoadNames)
        pop_dict_msg = populateIndivPolyListObj(pop_msg_area, gridRoadAreaPlots, gridRoadNames, gridRoadList,
                                                gridRoadDict,
                                                None)

        resultCode = pop_dict_msg.get("result")
        if pop_dict_msg == None or resultCode == "error":
            get_current_logger().warning(
                f"{pop_msg_refid} Error processing {pop_msg_area} Area Section Return is {pop_dict_msg}")
        else:
            if (resultCode == "OK"):
                areaObjList = pop_dict_msg.get("data_list")

                # refactor-3
                areaObjDict = pop_dict_msg.get("data_dict", None)

                # overwrite with the data returned from function
                gridRoadObjInst.setBaseUnitDict(areaObjDict)
                gridRoadObjInst.setBaseUnitFinalList(areaObjList)

                # combined objects
                self.combinedObjects[pop_msg_area] = gridRoadObjInst

    def Roadwidening_details(self):
        # ROADWIDENING
        pop_msg_area = LayerMaster.ROADWIDENING.value
        pop_msg_refid = "1.2"
        reservedRoadObjInst = ObjectByType(pop_msg_area)
        reservedRoadDict = reservedRoadObjInst.getBaseUnitDict()
        reservedRoadList = reservedRoadObjInst.getBaseUnitFinalList()

        if (self.layerDict.get(LayerMaster.ROADWIDENING.value, False) != False):

            reservedRoadAreaPlots = extractSubPlot(self.msp, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, True, False)

            reservedRoadNames = extractSubPlot(self.msp, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)

            pop_dict_msg = populateIndivPolyListObj(pop_msg_area, reservedRoadAreaPlots, reservedRoadNames,
                                                    reservedRoadList, reservedRoadDict, None)

            resultCode = pop_dict_msg.get("result", None)
            if resultCode == None or resultCode == "error":
                get_current_logger().warning(
                    f"{pop_msg_refid} Error processing {pop_msg_area} Area Section Return is {pop_dict_msg}")

            else:
                if (resultCode == "OK"):

                    areaObjList = pop_dict_msg.get("data_list")

                    # refactor-3
                    areaObjDict = pop_dict_msg.get("data_dict", None)

                    warnings = pop_dict_msg.get("warnings", None)
                    countWarnings = 0
                    if (warnings is not None and len(warnings) > 0):
                        countWarnings = len(warnings)
                        msgtx = "  ".join([pop_msg_area, ' count mismatch after processing expecting ',
                                           str(len(areaObjList) + countWarnings), " got ", str(len(areaObjList)),
                                           ' details ', " - ".join(warnings)])
                        self.warnings.append(msgtx)

                    # overwrite with the data returned from function
                    reservedRoadObjInst.setBaseUnitDict(areaObjDict)
                    reservedRoadObjInst.setBaseUnitFinalList(areaObjList)

                    # combined objects
                    self.combinedObjects[pop_msg_area] = reservedRoadObjInst

    def MainRoaddetails2(self):

        mainRoadList = self.combinedObjects.get(LayerMaster.MAINROAD.value).getBaseUnitFinalList() if self.combinedObjects.get(LayerMaster.MAINROAD.value,
                                                                                           0) != 0 else []

        reservedRoadList = self.combinedObjects.get(
            LayerMaster.ROADWIDENING.value).getBaseUnitFinalList() if self.combinedObjects.get(
            LayerMaster.ROADWIDENING.value, 0) != 0 else []

        internalRoadList = self.combinedObjects.get(
            LayerMaster.INTERNALROAD.value).getBaseUnitFinalList() if self.combinedObjects.get(
            LayerMaster.INTERNALROAD.value, 0) != 0 else []

        gridRoadList = self.combinedObjects.get(
            LayerMaster.GRIDROAD.value).getBaseUnitFinalList() if self.combinedObjects.get(LayerMaster.GRIDROAD.value,
                                                                                           0) != 0 else []

        # reset the roadwidening widths with main roads if they abut each other
        if (self.combinedObjects.get(LayerMaster.MAINROAD.value, 0) != 0):
            mnList = self.combinedObjects.get(LayerMaster.MAINROAD.value).getBaseUnitFinalList()
        else:
            mnList = []

        if (self.combinedObjects.get(LayerMaster.ROADWIDENING.value, 0) != 0):
            wideningList = self.combinedObjects.get(LayerMaster.ROADWIDENING.value).getBaseUnitFinalList()
        else:
            wideningList = []

        if (len(wideningList) > 0 and len(mnList) > 0):
            newList = []
            roadWideningProcessedDict = dict()  # Fix for duplicate roadwidening getting added 4/24/2022

            for rdWiden in wideningList:

                get_current_logger().debug(
                    f'RD Widening Handle/ Name /Area/Width /Poly. handle# {rdWiden.handle},{rdWiden.name},{rdWiden.area},{rdWiden.width}')

                for mainRd in mnList:
                    get_current_logger().debug(
                        f'MainRoad  Handle/Name /Area/Width /Poly.{mainRd.handle},{mainRd.name},{mainRd.area},{mainRd.width}')
                    get_current_logger().debug(
                        f'do these touch each other {doObjectsTouchEachOther(rdWiden.polygon, mainRd.polygon)}')
                    mnRoadWidth = float(extract_road_width_fromtext(mainRd.name))
                    if (mnRoadWidth > 0):
                        rdWiden.width = mnRoadWidth  # use mainroads width. discard roadwidening width 4/12/2022
                        if (roadWideningProcessedDict.get(rdWiden.handle, -99) == -99):
                            newList.append(rdWiden)
                            roadWideningProcessedDict[rdWiden.handle] = rdWiden
                    else:
                        if (roadWideningProcessedDict.get(rdWiden.handle, -99) == -99):
                            newList.append(rdWiden)
                            roadWideningProcessedDict[rdWiden.handle] = rdWiden

            if (len(newList) > 0):
                get_current_logger().warning('Overriding Abutting width of Road widening area.')
                # overwrite the layer
                RDObjInst = self.combinedObjects.get(LayerMaster.ROADWIDENING.value)
                RDObjInst.setBaseUnitFinalList(newList)
                self.combinedObjects[LayerMaster.ROADWIDENING.value] = RDObjInst
                # override the reservedRoadList with updated values - this will be used for concantenation in road_list object

                reservedRoadList = newList

        # Join Road Widening and Internal Roads for finding Abutting/frontage
        if (mainRoadList is not None and len(mainRoadList) > 0):
            self.road_list = mainRoadList
            get_current_logger().debug(f'main road list is appended to road list:{mainRoadList}')

        # Join Road Widening and Internal Roads for finding Abutting/frontage
        if (reservedRoadList is not None and len(reservedRoadList) > 0):
            self.road_list = self.road_list + reservedRoadList if self.road_list != [] else reservedRoadList
            get_current_logger().debug(f'reserved road list is appended to road list:{self.road_list}')

        if (internalRoadList is not None and len(internalRoadList) > 0):
            self.road_list = self.road_list + internalRoadList if self.road_list != None else internalRoadList

            get_current_logger().debug(f'internal road list appended to road_list :{self.road_list}')

        if (gridRoadList is not None and len(gridRoadList) > 0):
            self.road_list = self.road_list + gridRoadList if self.road_list != None else gridRoadList
            get_current_logger().debug(f'grid road list appended to road_list :{self.road_list}')

        get_current_logger().debug(f"road_list length {len(self.road_list)}")

    def IndivSubplot_details(self):

        pop_msg_area = LayerMaster.OPENLAYOUT.value
        pop_msg_refid = "1.3"
        indivObjInst = ObjectByType(pop_msg_area)
        plotDict = indivObjInst.getBaseUnitDict()
        plotList = indivObjInst.getBaseUnitFinalList()

        subPlots1 = extractSubPlot(self.msp, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, True, False)

        pltNames = extractSubPlot(self.msp, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)

        indivObjInst.setBaseList(subPlots1)
        indivObjInst.setBaseUnitNames(pltNames)

        # some drawings not returning text/mtext names for plots -
        if (len(pltNames) > 0):
            pop_dict_msg = populateIndivPolyListObj(pop_msg_area, subPlots1, pltNames, plotList, plotDict, self.road_list)

        else:

            pop_dict_msg = populateIndivPolyListObjNoNames(pop_msg_area, subPlots1, plotList, plotDict, self.road_list)

        resultCode = pop_dict_msg.get("result")
        if pop_dict_msg == None or resultCode == "error":
            get_current_logger().warning(
                f'{pop_msg_refid} Error processing {pop_msg_area} Area Section Return is {pop_dict_msg}')
        else:
            if (resultCode == "OK"):

                areaObjList = pop_dict_msg.get("data_list")

                # refactor-3
                areaObjDict = pop_dict_msg.get("data_dict", None)
                warnings = pop_dict_msg.get("warnings", None)

                if (warnings is not None and len(warnings) > 0):
                    countWarnings = len(warnings)
                    msgtx = "  ".join([pop_msg_area, ' count mismatch after processing expecting ',
                                       str(len(areaObjList) + countWarnings), " got ", str(len(areaObjList)),
                                       ' details ', " - ".join(warnings)])
                    self.warnings.append(msgtx)

                # overwrite with the data returned from function
                indivObjInst.setBaseUnitDict(areaObjDict)
                indivObjInst.setBaseUnitFinalList(areaObjList)

                # combined objects
                self.combinedObjects[pop_msg_area] = indivObjInst

    def MortgageArea_details(self):

        pop_msg_area = LayerMaster.MORTGAGEAREA.value
        pop_msg_refid = "1.4"
        mortgageObjInst = ObjectByType(pop_msg_area)
        mortgageDict = mortgageObjInst.getBaseUnitDict()
        mortgageList = mortgageObjInst.getBaseUnitFinalList()

        mortgagePlots = extractSubPlot(self.msp, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, True, False)

        mortgageNames = extractSubPlot(self.msp, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)

        mortgageObjInst.setBaseList(mortgagePlots)
        mortgageObjInst.setBaseUnitNames(mortgageNames)

        # some drawings not returning text/mtext names for plots -
        if (len(mortgageNames) > 0):
            pop_dict_msg = populateIndivPolyListObj(pop_msg_area, mortgagePlots, mortgageNames, mortgageList,
                                                    mortgageDict,
                                                    None)
        else:
            pop_dict_msg = populateIndivPolyListObjNoNames(pop_msg_area, mortgagePlots, mortgageList, mortgageDict,
                                                           None)

        resultCode = pop_dict_msg.get("result")
        if pop_dict_msg == None or resultCode == "error":
            get_current_logger().warning(
                f"{pop_msg_refid} Error processing {pop_msg_area} Area Section Return is {pop_dict_msg}")
        else:
            if (resultCode == "OK"):

                areaObjList = pop_dict_msg.get("data_list")

                # refactor-3
                areaObjDict = pop_dict_msg.get("data_dict", None)
                warnings = pop_dict_msg.get("warnings", None)

                if (warnings is not None and len(warnings) > 0):
                    countWarnings = len(warnings)
                    msgtx = "  ".join([pop_msg_area, ' count mismatch after processing expecting ',
                                       str(len(areaObjList) + countWarnings), " got ", str(len(areaObjList)),
                                       ' details ', " - ".join(warnings)])
                    self.warnings.append(msgtx)
                # overwrite with the data returned from function
                mortgageObjInst.setBaseUnitDict(areaObjDict)
                mortgageObjInst.setBaseUnitFinalList(areaObjList)

                # combined objects
                self.combinedObjects[pop_msg_area] = mortgageObjInst

    def NalaRoad_details(self):

        pop_msg_area = LayerMaster.NALAROAD.value
        pop_msg_refid = "1.5.1"
        nalaRoadObjInst = ObjectByType(pop_msg_area)
        nalaRoadDict = nalaRoadObjInst.getBaseUnitDict()
        nalaRoadList = nalaRoadObjInst.getBaseUnitFinalList()

        if (self.layerDict.get(LayerMaster.NALAROAD.value, False) != False):
            nalaRoadAreaPlots = extractSubPlot(self.msp, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, True, False)

            nalaRoadNames = extractSubPlot(self.msp, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)

            pop_dict_msg = populateIndivPolyListObj(pop_msg_area, nalaRoadAreaPlots, nalaRoadNames, nalaRoadList,
                                                    nalaRoadDict, None)

            resultCode = pop_dict_msg.get("result")
            if pop_dict_msg == None or resultCode == "error":

                get_current_logger().warning(
                    f"{pop_msg_refid} Error processing {pop_msg_area} Area Section Return is {pop_dict_msg}")
            else:
                if (resultCode == "OK"):

                    areaObjList = pop_dict_msg.get("data_list")

                    # refactor-3
                    areaObjDict = pop_dict_msg.get("data_dict", None)

                    warnings = pop_dict_msg.get("warnings", None)

                    if (warnings is not None and len(warnings) > 0):
                        countWarnings = len(warnings)
                        msgtx = "  ".join([pop_msg_area, ' count mismatch after processing expecting ',
                                           str(len(areaObjList) + countWarnings), " got ", str(len(areaObjList)),
                                           ' details ', " - ".join(warnings)])
                        self.warnings.append(msgtx)

                    # overwrite with the data returned from function
                    nalaRoadObjInst.setBaseUnitDict(areaObjDict)
                    nalaRoadObjInst.setBaseUnitFinalList(areaObjList)

                    # combined objects
                    self.combinedObjects[pop_msg_area] = nalaRoadObjInst

    def BufferZone_details(self):

        pop_msg_area = LayerMaster.BUFFERZONE.value
        pop_msg_refid = "1.5.2"
        buffZoneObjInst = ObjectByType(pop_msg_area)
        buffZoneDict = buffZoneObjInst.getBaseUnitDict()
        buffZoneList = buffZoneObjInst.getBaseUnitFinalList()

        if (self.layerDict.get(LayerMaster.BUFFERZONE.value, False) != False):
            buffZoneAreaPlots = extractSubPlot(self.msp, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, True, False)

            buffZoneNames = extractSubPlot(self.msp, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)

            pop_dict_msg = populateIndivPolyListObj(pop_msg_area, buffZoneAreaPlots, buffZoneNames, buffZoneList,
                                                    buffZoneDict, None)

            resultCode = pop_dict_msg.get("result")
            if pop_dict_msg == None or resultCode == "error":
                get_current_logger().warning(
                    f"{pop_msg_refid} Error processing {pop_msg_area} Area Section Return is {pop_dict_msg}")
            else:
                if (resultCode == "OK"):

                    areaObjList = pop_dict_msg.get("data_list")

                    # refactor-3
                    areaObjDict = pop_dict_msg.get("data_dict", None)

                    warnings = pop_dict_msg.get("warnings", None)

                    if (warnings is not None and len(warnings) > 0):
                        countWarnings = len(warnings)
                        msgtx = "  ".join([pop_msg_area, ' count mismatch after processing expecting ',
                                           str(len(areaObjList) + countWarnings), " got ", str(len(areaObjList)),
                                           ' details ', " - ".join(warnings)])
                        self.warnings.append(msgtx)

                    # overwrite with the data returned from function
                    buffZoneObjInst.setBaseUnitDict(areaObjDict)
                    buffZoneObjInst.setBaseUnitFinalList(areaObjList)

                    # combined objects
                    self.combinedObjects[pop_msg_area] = buffZoneObjInst

    def ReservedArea_details(self):

        pop_msg_area = LayerMaster.RESERVEDAREA.value
        pop_msg_refid = "1.5.2.1"
        reservedAreaObjInst = ObjectByType(pop_msg_area)
        reservedAreaDict = reservedAreaObjInst.getBaseUnitDict()
        reservedAreaList = reservedAreaObjInst.getBaseUnitFinalList()

        if (self.layerDict.get(LayerMaster.RESERVEDAREA.value, False) != False):
            reservedAreaPlots = extractSubPlot(self.msp, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, True, False)

            reservedAreaNames = extractSubPlot(self.msp, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)

            pop_dict_msg = populateIndivPolyListObj(pop_msg_area, reservedAreaPlots, reservedAreaNames,
                                                    reservedAreaList,
                                                    reservedAreaDict, None)

            resultCode = pop_dict_msg.get("result")
            if pop_dict_msg == None or resultCode == "error":
                get_current_logger().warning(
                    f"{pop_msg_refid} Error processing {pop_msg_area} Area Section Return is {pop_dict_msg}")
            else:
                if (resultCode == "OK"):

                    areaObjList = pop_dict_msg.get("data_list")

                    # refactor-3
                    areaObjDict = pop_dict_msg.get("data_dict", None)
                    warnings = pop_dict_msg.get("warnings", None)

                    if (warnings is not None and len(warnings) > 0):
                        msgtx = "  ".join([pop_msg_area, ' count mismatch after processing expecting ',
                                           str(len(areaObjList) + "countWarnings"), " got ", str(len(areaObjList)),
                                           ' details ', " - ".join(warnings)])
                        self.warnings.append(msgtx)

                    # overwrite with the data returned from function
                    reservedAreaObjInst.setBaseUnitDict(areaObjDict)
                    reservedAreaObjInst.setBaseUnitFinalList(areaObjList)

                    # combined objects
                    self.combinedObjects[pop_msg_area] = reservedAreaObjInst

    def WaterBodies_details(self):

        pop_msg_area = LayerMaster.WATERBODIES.value
        pop_msg_refid = "1.5.3"
        waterBodiesObjInst = ObjectByType(pop_msg_area)
        waterBodiesDict = waterBodiesObjInst.getBaseUnitDict()
        waterBodiesList = waterBodiesObjInst.getBaseUnitFinalList()

        if (self.layerDict.get(LayerMaster.WATERBODIES.value, False) != False):
            waterBodiesAreaPlots = extractSubPlot(self.msp, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, True, False)

            waterBodiesNames = extractSubPlot(self.msp, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)

            pop_dict_msg = populateIndivPolyListObj(pop_msg_area, waterBodiesAreaPlots, waterBodiesNames,
                                                    waterBodiesList,
                                                    waterBodiesDict, None)

            resultCode = pop_dict_msg.get("result")
            if pop_dict_msg == None or resultCode == "error":
                get_current_logger().warning(
                    f"{pop_msg_refid} Error processing {pop_msg_area} Area Section Return is {pop_dict_msg}.")
            else:
                if (resultCode == "OK"):

                    areaObjList = pop_dict_msg.get("data_list")

                    # refactor-3
                    areaObjDict = pop_dict_msg.get("data_dict", None)

                    warnings = pop_dict_msg.get("warnings", None)
                    if (warnings is not None and len(warnings) > 0):
                        msgtx = "  ".join([pop_msg_area, ' count mismatch after processing expecting ',
                                           str(len(areaObjList) + "countWarnings"), " got ", str(len(areaObjList)),
                                           ' details ', " - ".join(warnings)])
                        self.warnings.append(msgtx)

                    # overwrite with the data returned from function
                    waterBodiesObjInst.setBaseUnitDict(areaObjDict)
                    waterBodiesObjInst.setBaseUnitFinalList(areaObjList)

                    # combined objects
                    self.combinedObjects[pop_msg_area] = waterBodiesObjInst

    def LeftOwnersLand_details(self):
        pop_msg_area = LayerMaster.LEFTOVEROWNERSLAND.value
        pop_msg_refid = "1.5.4"
        leftoverOwnersObjInst = ObjectByType(pop_msg_area)
        leftoverOwnersDict = leftoverOwnersObjInst.getBaseUnitDict()
        leftoverOwnersList = leftoverOwnersObjInst.getBaseUnitFinalList()

        if (self.layerDict.get(LayerMaster.LEFTOVEROWNERSLAND.value, False) != False):
            leftoverOwnersAreaPlots = extractSubPlot(self.msp, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, True, False)

            leftoverOwnersNames = extractSubPlot(self.msp, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)

            pop_dict_msg = populateIndivPolyListObj(pop_msg_area, leftoverOwnersAreaPlots, leftoverOwnersNames,
                                                    leftoverOwnersList, leftoverOwnersDict, None)

            resultCode = pop_dict_msg.get("result")
            if pop_dict_msg == None or resultCode == "error":
                get_current_logger().warning(
                    f"{pop_msg_refid} Error processing {pop_msg_area} Area Section Return is {pop_dict_msg}")

            else:
                if (resultCode == "OK"):

                    areaObjList = pop_dict_msg.get("data_list")

                    # refactor-3
                    areaObjDict = pop_dict_msg.get("data_dict", None)

                    warnings = pop_dict_msg.get("warnings", None)
                    countWarnings = 0
                    if (warnings is not None and len(warnings) > 0):
                        countWarnings = len(warnings)
                        msgtx = "  ".join([pop_msg_area, ' count mismatch after processing expecting ',
                                           str(len(areaObjList) + countWarnings), " got ", str(len(areaObjList)),
                                           ' details ', " - ".join(warnings)])
                        self.warnings.append(msgtx)

                    # overwrite with the data returned from function
                    leftoverOwnersObjInst.setBaseUnitDict(areaObjDict)
                    leftoverOwnersObjInst.setBaseUnitFinalList(areaObjList)

                    # combined objects
                    self.combinedObjects[pop_msg_area] = leftoverOwnersObjInst

    def Surrendertoauth_Details(self):

        pop_msg_area = LayerMaster.SURRENDERTOAUTH.value
        pop_msg_refid = "1.5.5"
        surrenderToAuthorityObjInst = ObjectByType(pop_msg_area)
        surrenderToAuthorityDict = surrenderToAuthorityObjInst.getBaseUnitDict()
        surrenderToAuthorityList = surrenderToAuthorityObjInst.getBaseUnitFinalList()

        if (self.layerDict.get(LayerMaster.SURRENDERTOAUTH.value, False) != False):
            surrenderToAuthorityAreaPlots = extractSubPlot(self.msp, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, True,
                                                           False)

            surrenderToAuthorityNames = extractSubPlot(self.msp, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)

            pop_dict_msg = populateIndivPolyListObj(pop_msg_area, surrenderToAuthorityAreaPlots,
                                                    surrenderToAuthorityNames,
                                                    surrenderToAuthorityList, surrenderToAuthorityDict, None)

            resultCode = pop_dict_msg.get("result")
            if pop_dict_msg == None or resultCode == "error":
                get_current_logger().warning(
                    f"{pop_msg_refid} Error processing {pop_msg_area} Area Section Return is {pop_dict_msg}")
            else:
                if (resultCode == "OK"):

                    areaObjList = pop_dict_msg.get("data_list")

                    # refactor-3
                    areaObjDict = pop_dict_msg.get("data_dict", None)

                    warnings = pop_dict_msg.get("warnings", None)
                    countWarnings = 0
                    if (warnings is not None and len(warnings) > 0):
                        countWarnings = len(warnings)
                        msgtx = "  ".join([pop_msg_area, ' count mismatch after processing expecting ',
                                           str(len(areaObjList) + countWarnings), " got ", str(len(areaObjList)),
                                           ' details ', " - ".join(warnings)])
                        self.warnings.append(msgtx)

                    # overwrite with the data returned from function
                    surrenderToAuthorityObjInst.setBaseUnitDict(areaObjDict)
                    surrenderToAuthorityObjInst.setBaseUnitFinalList(areaObjList)

                    # combined objects
                    self.combinedObjects[pop_msg_area] = surrenderToAuthorityObjInst

    def Plot_details(self):

        pop_msg_area = LayerMaster.PLOT.value
        # pop_msg_refid = "1.6"
        mainPlotObjInst = ObjectByType(pop_msg_area)
        # mainPlotDict = mainPlotObjInst.getBaseUnitDict()
        mainPlotList = mainPlotObjInst.getBaseUnitFinalList()

        mainPlot = extractSubPlot(self.msp, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, True, False)

        mainPlotObjInst.setBaseList(mainPlot)

        mainPlotDict = dict()
        for plotObj in mainPlot:
            get_current_logger().debug(f"processsing {plotObj.handle}")
            polyStr = str(plotObj.get_points())[1:-1].translate(translation)

            polyPoints = 'POLYGON ((' + polyStr + '))'

            lwpoly = shapely.wkt.loads(polyPoints)
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
            # print ("Plot: " , plotObj.handle , " area: " , lwpoly.area, ", length: ", length,  ", width: ",  width , " , coordinates :", lwpoly)
            p6 = IndivSubPlot(plotObj.handle, "_Plot", lwpoly, length, width, lwpoly.area, plotObj.handle)
            if plotObj.handle not in mainPlotDict:
                mainPlotList.append(p6)
                mainPlotDict[plotObj.handle] = p6

            # overwrite with the data returned from function
        mainPlotObjInst.setBaseUnitDict(mainPlotDict)
        mainPlotObjInst.setBaseUnitFinalList(mainPlotList)

        # combined objects
        self.combinedObjects[pop_msg_area] = mainPlotObjInst

    def Splay_details(self):

        pop_msg_area = LayerMaster.SPLAY.value
        pop_msg_refid = "1.6.1"
        splayObjInst = ObjectByType(pop_msg_area)
        splayPlotDict = splayObjInst.getBaseUnitDict()
        splayPlotList = splayObjInst.getBaseUnitFinalList()

        # Optional Layers
        if (self.layerDict.get(pop_msg_area, "NA") == True):
            splayPlots = extractSubPlot(self.msp, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, True, False)

            splayPlotNames = extractSubPlot(self.msp, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)

            splayObjInst.setBaseList(splayPlots)
            splayObjInst.setBaseUnitNames(splayPlotNames)

            pop_dict_msg = populateIndivPolyListObj(pop_msg_area, splayPlots, splayPlotNames, splayPlotList,
                                                    splayPlotDict,
                                                    self.road_list)

            resultCode = pop_dict_msg.get("result")
            if pop_dict_msg == None or resultCode == "error":
                get_current_logger().warning(
                    f"{pop_msg_refid} Error processing {pop_msg_area} Area Section Return is {pop_dict_msg}")
            else:
                if (resultCode == "OK"):

                    areaObjList = pop_dict_msg.get("data_list")

                    # refactor-3
                    areaObjDict = pop_dict_msg.get("data_dict", None)

                    warnings = pop_dict_msg.get("warnings", None)
                    countWarnings = 0
                    if (warnings is not None and len(warnings) > 0):
                        countWarnings = len(warnings)
                        msgtx = "  ".join([pop_msg_area, ' count mismatch after processing expecting ',
                                           str(len(areaObjList) + countWarnings), " got ", str(len(areaObjList)),
                                           ' details ', " - ".join(warnings)])
                        self.warnings.append(msgtx)

                    # overwrite with the data returned from function
                    splayObjInst.setBaseUnitDict(areaObjDict)
                    splayObjInst.setBaseUnitFinalList(areaObjList)

                    # combined objects
                    self.combinedObjects[pop_msg_area] = splayObjInst

    def OrgOpenSpace_details(self):

        pop_msg_area = LayerMaster.ORGOPENSPACE.value
        pop_msg_refid = "1.7"
        totObjInst = ObjectByType(pop_msg_area)
        totDict = totObjInst.getBaseUnitDict()
        totList = totObjInst.getBaseUnitFinalList()

        totPlots = extractSubPlot(self.msp, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, True, False)

        totPlotNames = extractSubPlot(self.msp, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)

        totObjInst.setBaseList(totPlots)
        totObjInst.setBaseUnitNames(totPlotNames)

        pop_dict_msg = populateIndivPolyListObj(pop_msg_area, totPlots, totPlotNames, totList, totDict, None)

        resultCode = pop_dict_msg.get("result")
        if pop_dict_msg == None or resultCode == "error":
            get_current_logger().warning(
                f"{pop_msg_refid} Error processing {pop_msg_area} Area Section Return is {pop_dict_msg}")
        else:
            if (resultCode == "OK"):

                areaObjList = pop_dict_msg.get("data_list")

                # refactor-3
                areaObjDict = pop_dict_msg.get("data_dict", None)
                warnings = pop_dict_msg.get("warnings", None)
                countWarnings = 0
                if (warnings is not None and len(warnings) > 0):
                    countWarnings = len(warnings)
                    msgtx = "  ".join([pop_msg_area, ' count mismatch after processing expecting ',
                                       str(len(areaObjList) + countWarnings), " got ", str(len(areaObjList)),
                                       ' details ', " - ".join(warnings)])
                    self.warnings.append(msgtx)
                # overwrite with the data returned from function
                totObjInst.setBaseUnitDict(areaObjDict)
                totObjInst.setBaseUnitFinalList(areaObjList)

                # combined objects
                self.combinedObjects[pop_msg_area] = totObjInst

    def SocialInfraStructure_details(self):

        pop_msg_area = LayerMaster.SOCIALINFRA.value
        pop_msg_refid = "1.8"
        socObjInst = ObjectByType(pop_msg_area)
        socDict = socObjInst.getBaseUnitDict()
        socList = socObjInst.getBaseUnitFinalList()

        socPlots = extractSubPlot(self.msp, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, True, False)

        socPlotNames = extractSubPlot(self.msp, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)

        socObjInst.setBaseList(socPlots)
        socObjInst.setBaseUnitNames(socPlotNames)
        pop_dict_msg = populateIndivPolyListObj(pop_msg_area, socPlots, socPlotNames, socList, socDict, None)

        resultCode = pop_dict_msg.get("result")
        if pop_dict_msg == None or resultCode == "error":
            get_current_logger().warning(
                f"{pop_msg_refid} Error processing {pop_msg_area} Area Section Return is {pop_dict_msg}")
        else:
            if (resultCode == "OK"):
                areaObjList = pop_dict_msg.get("data_list")

                # refactor-3
                areaObjDict = pop_dict_msg.get("data_dict", None)

                # overwrite with the data returned from function
                socObjInst.setBaseUnitDict(areaObjDict)
                socObjInst.setBaseUnitFinalList(areaObjList)

                # combined objects
                self.combinedObjects[pop_msg_area] = socObjInst

    def AccessoryUse_details(self):

        pop_msg_area = LayerMaster.ACCESSORYUSE.value
        pop_msg_refid = "1.9"
        accObjInst = ObjectByType(pop_msg_area)
        accDict = accObjInst.getBaseUnitDict()
        accList = accObjInst.getBaseUnitFinalList()

        accPlots = extractSubPlot(self.msp, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, True, False)

        accPlotNames = extractSubPlot(self.msp, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)

        accObjInst.setBaseList(accPlots)
        accObjInst.setBaseUnitNames(accPlotNames)

        pop_dict_msg = populateIndivPolyListObj(pop_msg_area, accPlots, accPlotNames, accList, accDict, None)

        resultCode = pop_dict_msg.get("result")
        if pop_dict_msg == None or resultCode == "error":
            get_current_logger().warning(
                f"{pop_msg_refid} Error processing {pop_msg_area} Area Section Return is {pop_dict_msg}")
        else:
            if (resultCode == "OK"):

                areaObjList = pop_dict_msg.get("data_list")

                # refactor-3
                areaObjDict = pop_dict_msg.get("data_dict", None)

                warnings = pop_dict_msg.get("warnings", None)

                if (warnings is not None and len(warnings) > 0):
                    countWarnings = len(warnings)
                    msgtx = "  ".join([pop_msg_area, ' count mismatch after processing expecting ',
                                       str(len(areaObjList) + countWarnings), " got ", str(len(areaObjList)),
                                       ' details ', " - ".join(warnings)])
                    self.warnings.append(msgtx)

                # overwrite with the data returned from function
                accObjInst.setBaseUnitDict(areaObjDict)
                accObjInst.setBaseUnitFinalList(areaObjList)
                self.combinedObjects[pop_msg_area] = accObjInst

    def CycleTrack_details(self):

        pop_msg_area = LayerMaster.CYCLETRACK.value
        pop_msg_refid = "1.9.1"
        cyclObjInst = ObjectByType(pop_msg_area)
        cyclDict = cyclObjInst.getBaseUnitDict()
        cyclList = cyclObjInst.getBaseUnitFinalList()

        cyclPlots = extractSubPlot(self.msp, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, True, False)

        cyclPlotNames = extractSubPlot(self.msp, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)

        cyclObjInst.setBaseList(cyclPlots)
        cyclObjInst.setBaseUnitNames(cyclPlotNames)
        pop_dict_msg = populateIndivPolyListObj(pop_msg_area, cyclPlots, cyclPlotNames, cyclList, cyclDict, None)

        resultCode = pop_dict_msg.get("result")
        if pop_dict_msg == None or resultCode == "error":
            get_current_logger().warning(
                f"{pop_msg_refid} Error processing {pop_msg_area} Area Section Return is {pop_dict_msg}")
        else:
            if (resultCode == "OK"):

                areaObjList = pop_dict_msg.get("data_list")

                # refactor-3
                areaObjDict = pop_dict_msg.get("data_dict", None)

                warnings = pop_dict_msg.get("warnings", None)
                if (warnings is not None and len(warnings) > 0):
                    countWarnings = len(warnings)
                    msgtx = "  ".join([pop_msg_area, ' count mismatch after processing expecting ',
                                       str(len(areaObjList) + countWarnings), " got ", str(len(areaObjList)),
                                       ' details ', " - ".join(warnings)])
                    self.warnings.append(msgtx)

                # overwrite with the data returned from function
                cyclObjInst.setBaseUnitDict(areaObjDict)
                cyclObjInst.setBaseUnitFinalList(areaObjList)
                # combined objects
                self.combinedObjects[pop_msg_area] = cyclObjInst

    def Utility_Misc_details(self):

        pop_msg_area = LayerMaster.UTILITY_MISC.value
        pop_msg_refid = "1.9.2"
        umiscObjInst = ObjectByType(pop_msg_area)
        umiscDict = umiscObjInst.getBaseUnitDict()
        umiscList = umiscObjInst.getBaseUnitFinalList()

        umiscPlots = extractSubPlot(self.msp, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, True, False)

        umiscPlotNames = extractSubPlot(self.msp, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)

        umiscObjInst.setBaseList(umiscPlots)
        umiscObjInst.setBaseUnitNames(umiscPlotNames)

        pop_dict_msg = populateIndivPolyListObj(pop_msg_area, umiscPlots, umiscPlotNames, umiscList, umiscDict, None)

        resultCode = pop_dict_msg.get("result")
        if pop_dict_msg == None or resultCode == "error":
            get_current_logger().warning(
                f"{pop_msg_refid} Error processing {pop_msg_area} Area Section Return is {pop_dict_msg}")

        else:
            if (resultCode == "OK"):

                areaObjList = pop_dict_msg.get("data_list")

                warnings = pop_dict_msg.get("warnings", None)

                if (warnings is not None and len(warnings) > 0):
                    countWarnings = len(warnings)
                    msgtx = "  ".join([pop_msg_area, ' count mismatch after processing expecting ',
                                       str(len(areaObjList) + countWarnings), " got ", str(len(areaObjList)),
                                       ' details ', " - ".join(warnings)])
                    self.warnings.append(msgtx)

                # refactor-3
                areaObjDict = pop_dict_msg.get("data_dict", None)

                # overwrite with the data returned from function
                umiscObjInst.setBaseUnitDict(areaObjDict)
                umiscObjInst.setBaseUnitFinalList(areaObjList)

                # combined objects
                self.combinedObjects[pop_msg_area] = umiscObjInst

    def Parking_details(self):

        pop_msg_area = LayerMaster.PARKING.value  #
        pop_msg_refid = "1.9.3"
        # refactor-1
        parkingObjInst = ObjectByType(pop_msg_area)
        parkingUnitsDict = parkingObjInst.getBaseUnitDict()
        parkingUnitsList = parkingObjInst.getBaseUnitFinalList()

        parkingUnits = extractSubPlot(self.msp, pop_msg_area, LayerMaster.DWG_LWPOLYLINE.value, False, False)

        parkingUnitNames = extractSubPlot(self.msp, pop_msg_area, LayerMaster.DWG_TEXT_MTEXT.value)

        # refactor-2
        parkingObjInst.setBaseList(parkingUnits)
        parkingObjInst.setBaseUnitNames(parkingUnitNames)

        pop_dict_msg = populateIndivPolyListObj(pop_msg_area, parkingUnits, parkingUnitNames, parkingUnitsList,
                                                parkingUnitsDict, None)

        resultCode = pop_dict_msg.get("result")
        if pop_dict_msg == None or resultCode == "error":
            get_current_logger().warning(
                f"{pop_msg_refid} Error processing {pop_msg_area} Area Section Return is {pop_dict_msg}")
        else:
            if (resultCode == "OK"):

                areaObjList = pop_dict_msg.get("data_list")

                warnings = pop_dict_msg.get("warnings", None)

                if (warnings is not None and len(warnings) > 0):
                    countWarnings = len(warnings)
                    msgtx = "  ".join([pop_msg_area, ' count mismatch after processing expecting ',
                                       str(len(areaObjList) + countWarnings), " got ", str(len(areaObjList)),
                                       ' details ', " - ".join(warnings)])
                    self.warnings.append(msgtx)

                # refactor-3
                areaObjDict = pop_dict_msg.get("data_dict", None)

                # overwrite with the data returned from function
                parkingObjInst.setBaseUnitDict(areaObjDict)
                parkingObjInst.setBaseUnitFinalList(areaObjList)
                # combined objects
                self.combinedObjects[pop_msg_area] = parkingObjInst

    def getReport_data(self):
        self.status_dict["StepName"] = "Generating Report ..."
        # send_status(self.request_id, self.status_dict,self.requesttimeobj)
        try:

            # report_res = genOpenLayoutReport(self.request_id, self.combinedObjects, self.filename)
            genOpenLayoutReport_obj = GenOpenLayoutReport(self.request_id, self.combinedObjects, self.filename,self.status_dict,self.requesttimeobj)

            report_res= genOpenLayoutReport_obj.get_details()

            responseCode = report_res.get('responseCode', -1)
            if (responseCode == FAIL_CODE):
                self.responsedict['errors'] = report_res.get('errors', -1)
                self.responsedict['details'] = report_res.get('details', -1)

        except:
            # Get current system exception
            ex_type, ex_value, ex_traceback = sys.exc_info()

            # Extract unformatter stack traces as tuples
            trace_back = traceback.extract_tb(ex_traceback)

            # Format stacktrace
            stack_trace = list()

            for trace in trace_back:
                stack_trace.append(
                    "File : %s , Line : %d, Func.Name : %s, Statement : %s" % (trace[0], trace[1], trace[2], trace[3]))

            get_current_logger().exception(f"Exception type :{ex_type.__name__}")
            get_current_logger().exception(f"Exception message : {ex_value}")
            get_current_logger().exception(f"Stack trace :{stack_trace}")

            self.responsedict['error_category'] = "Failure code  - Server Error"
            self.responsedict['errors'] = ['Problem Generating Report']
            self.responsedict['errorList'] = str(stack_trace)

        self.responsedict['responseCode'] = responseCode
        self.responsedict['planType'] = 'Open_Layout'


        if (responseCode == FAIL_CODE):
            self.responsedict['error_category'] = "Problem processing report"
            self.responsedict['dwgExtract'] = []

            self.status_dict["Status"] = "Failed"
            self.status_dict["StepName"] = "Generating Report ..."
            self.status_dict["Error"] = "Problem processing report"
            # send_status(self.request_id, self.status_dict,self.requesttimeobj)


        elif (responseCode == SUCCESS_CODE):
            self.responsedict['dwgExtract'] = report_res.get('dwgExtract', [])  # checkOutput..
            self.responsedict['error_category'] = ""
            self.responsedict['errors'] = []

            self.status_dict["StepName"] = "Generating Report Completed."
            # send_status(self.request_id, self.status_dict,self.requesttimeobj)

        else:
            self.responsedict['error_category'] = "Misc Failure code  " + responseCode
            self.responsedict['errors'] = [report_res[1]]

        return self.responsedict

    def execute_step(self, step_no,total_step, step_name, step_function):

        try:
            start_time = time.time()
            get_current_logger().info("=" * 80)
            get_current_logger().info(f"Step{step_no}/{total_step} STARTED : {step_name}")
            get_current_logger().info("=" * 80)

            process_steps_dict=dict()
            process_steps_dict["CurrentStep"] = f"{step_name} Processing ..."
            process_steps_dict["Progress"] = self.progress
            process_steps_dict["Steps"] = f"{step_no}/{total_step}"
            process_steps_dict["StepExeTime"] = f"0.0 sec"
            self.status_dict["Step_data"] = process_steps_dict

            # send_status(self.request_id, self.status_dict, self.requesttimeobj)
            time.sleep(1)

            step_function()

            elapsed = round(time.time() - start_time, 2)

            completed_progress = int(
                (step_no / total_step) * 100
            )

            self.progress = completed_progress

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
            completed_steps_dict=dict()
            completed_steps_dict["Progress"]=completed_progress
            completed_steps_dict["CurrentStep"] = f"{step_name} Completed."
            completed_steps_dict["StepExeTime"] = f"{elapsed} sec"
            completed_steps_dict["Steps"] = f"{step_no}/{total_step}"
            self.status_dict["Step_data"] = completed_steps_dict
            self.status_dict["Progress"] = main_completed_progress
            # send_status(self.request_id, self.status_dict, self.requesttimeobj)

            get_current_logger().info(
                f"Step{step_no}/{total_step} COMPLETED : {step_name} | Time Taken : {elapsed} sec"
            )
            time.sleep(0.5)

        except Exception as e:

            elapsed = round(time.time() - start_time, 2)

            error_msg = {
                "step": step_no,
                "step_name": step_name,
                "error": str(e),
                "time_taken": elapsed
            }

            self.errors.append(error_msg)

            get_current_logger().info("=" * 80)
            get_current_logger().info(f"{step_no} FAILED : {step_name}")
            get_current_logger().info(f"ERROR : {str(e)}")
            get_current_logger().info(traceback.format_exc())
            get_current_logger().info("=" * 80)

            failed_steps_dict= dict()
            self.status_dict["Status"] = "Failed"
            failed_steps_dict["CurrentStep"] = f"{step_name} Processing ..."
            failed_steps_dict["Progress"] = self.progress
            failed_steps_dict["Steps"] = f"{step_no}/{total_step}"
            self.status_dict["Step_data"] = failed_steps_dict
            self.status_dict["Error"] = self.responsedict.get("errors","Dxf Processing Error")
            # send_status(self.request_id, self.status_dict, self.requesttimeobj)

    def layers_validate(self):

        layers_check = self.check_layers()
        if (len(layers_check) > 0):
            self.responsedict['responseCode'] = FAIL_CODE
            self.responsedict['error_category'] = "MISSING LAYERS "
            self.responsedict['errors'] = "|".join(layers_check)
            self.responsedict['planType'] = 'Open_Layout'
            self.responsedict['dwgExtract'] = []
            return self.responsedict

    def analyze_drawings(self):

        self.responsedict['requestid'] = self.request_id
        self.responsedict['input'] = self.filename

        dwgCountsDict = analyzeDrawing(self.msp)

        if (self.request_params is not None):
            self.request_params['drawing_filename'] = str(self.filename[:-4])
            self.combinedObjects['request_params'] = self.request_params
            self.combinedObjects['dwg_layers'] = self.layerDict
            self.combinedObjects['modelspace'] = self.msp
            self.combinedObjects['dwg_counts'] = dwgCountsDict

    def main(self):

        steps=[
            ("Analyzing Drawings",self.analyze_drawings),
            ("Layers Validation",self.layers_validate),
            ("Extracting Layers",self.layers_extract),
            ("MainRoad Details",self.MainRoad_details),
            ("GridRoad Details",self.GridRoad_details),
            ("InternalRoad Details",self.InternalRoad_details),
            ("InternalGridRoad Details",self.InternalGridRoad_details),
            ("RoadWidening Details",self.Roadwidening_details),
            ("MainRoad Details2",self.MainRoaddetails2),
            ("IndivSubplot Details",self.IndivSubplot_details),
            ("MortgageArea Details",self.MortgageArea_details),
            ("NalaRoad Details",self.NalaRoad_details),
            ("WaterBodies Details",self.WaterBodies_details),
            ("LeftOwnersLand Details",self.LeftOwnersLand_details),
            ("Surender to Authority Details",self.Surrendertoauth_Details),
            ("Plot Details",self.Plot_details),
            ("Splay Details",self.Splay_details),
            ("Organized Open Space Details",self.OrgOpenSpace_details),
            ("SocialInfra Structure Details",self.SocialInfraStructure_details),
            ("AccessoryUse Details",self.AccessoryUse_details),
            ("CycleTrack Details",self.CycleTrack_details),
            ("Utility Misc Details",self.Utility_Misc_details)
        ]

        ### PARKING
        if (self.layerDict.get(LayerMaster.PARKING.value, 0) != 0):

            steps.append(("Parking Details",self.Parking_details))

        total_steps = len(steps)

        for index, (step_name, step_function) in enumerate(steps, start=1):


            self.execute_step(
                index,
                total_steps,
                step_name,
                step_function
            )

        self.combinedObjects['DWG_WARNINGS'] = self.warnings

        report_data=self.getReport_data()

        return report_data