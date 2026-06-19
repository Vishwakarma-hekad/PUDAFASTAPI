#-----------------------------------------------------Module------------------------------------

import os

import ezdxf

import numpy as np

from shapely.geometry import Point,Polygon

from shapely.geometry import LineString

from shapely import box

import time

class BalconyLengthAndWidth:

    def BoundingBox(self,coords):

        minx = min(coords, key=lambda x: x[0])

        miny = min(coords, key=lambda x: x[1])

        maxx = max(coords, key=lambda x: x[0])

        maxy = max(coords, key=lambda x: x[1])

        bbox = box(minx[0], miny[1], maxx[0], maxy[1])

        x, y = bbox.exterior.xy

        list_of_lines = [[[x[0], y[0]], [x[1], y[1]]], [[x[1], y[1]], [x[2], y[2]]], [[x[2], y[2]], [x[3], y[3]]],[[x[3], y[3]], [x[4], y[4]]]]

        return list_of_lines
    def BalconyWidth(self,BalconyPolygon):

        if len([bp[0:2] for bp in BalconyPolygon.get_points()])>=4:

            balcony_polygon_pts=[bp[0:2] for bp in BalconyPolygon.get_points()]

            bbox_data=self.BoundingBox(balcony_polygon_pts)

            balcony_data=[round(LineString(line).length,2) for line in bbox_data]

            if balcony_data!=[]:

                return min(balcony_data)
    def BalconyLength(self,BalconyPolygon):

        if len([bp[0:2] for bp in BalconyPolygon.get_points()])>=4:

            balcony_polygon_pts = [bp[0:2] for bp in BalconyPolygon.get_points()]

            bbox_data = self.BoundingBox(balcony_polygon_pts)

            balcony_data = [round(LineString(line).length,2) for line in bbox_data]

            if balcony_data != []:

                return max(balcony_data)
    def Floor_Layer(self,FloorData):

        FloorDict=dict()

        for Floor_entity in FloorData:

            if Floor_entity.dxftype()=='LWPOLYLINE':

                Floor_polygonID=Floor_entity.dxf.handle

                Floor_polygon_points=Polygon(np.array([fp[0:2] for fp in Floor_entity.get_points()]))

                FloorPolygonContainsLabel=[]

                for Floor_entity in FloorData:

                    if Floor_entity.dxftype()=='TEXT' or Floor_entity.dxftype()=='MTEXT':

                        FloorLabelProperties=Floor_entity.dxfattribs()

                        FloorLabelID=Floor_entity.dxf.handle

                        Floor_label=FloorLabelProperties.get('text') if Floor_entity.dxftype()=='TEXT' else Floor_entity.plain_text()

                        FloorLabel_insert=FloorLabelProperties.get('insert')

                        FloorLabel_point=Point(np.array([FloorLabel_insert[0],FloorLabel_insert[1]]))

                        if Floor_polygon_points.contains(FloorLabel_point)==True or Floor_polygon_points.touches(FloorLabel_point)==True or round(Floor_polygon_points.distance(FloorLabel_point),1)==0.0:

                            FloorPolygonContainsLabel.append([FloorLabelID,Floor_label,Floor_polygon_points])

                if FloorPolygonContainsLabel!=[] and len(FloorPolygonContainsLabel)>0:

                    for Floor in FloorPolygonContainsLabel:

                        FloorDict[Floor[0]]=[Floor[1],Floor[2]]
                else:

                    print(f'Missing Label Floor layer Polygon REF # {Floor_polygonID}')

        return FloorDict
    def Building_Layer(self,BuildingData):

        BuildingDict=dict()

        for building_entity in BuildingData:

            if building_entity.dxftype()=='LWPOLYLINE':

                Building_polygonID=building_entity.dxf.handle

                Building_polygon_points=Polygon(np.array([bp[0:2] for bp in building_entity.get_points()]))

                BuildingPolygonContainsLabel=[]

                for building_entity in BuildingData:

                    if building_entity.dxftype()=='TEXT' or building_entity.dxftype()=='MTEXT':

                        buildingLabelProperties=building_entity.dxfattribs()

                        BuildingLabelID=building_entity.dxf.handle

                        Building_label=buildingLabelProperties.get('text') if building_entity.dxftype()=='TEXT' else building_entity.plain_text()

                        BuildingLabel_insert=buildingLabelProperties.get('insert')

                        BuildingLabel_point=Point(np.array([BuildingLabel_insert[0],BuildingLabel_insert[1]]))

                        if Building_polygon_points.contains(BuildingLabel_point)==True or Building_polygon_points.touches(BuildingLabel_point)==True or round(Building_polygon_points.distance(BuildingLabel_point),1)==0.0:

                            BuildingPolygonContainsLabel.append([BuildingLabelID,Building_label,Building_polygon_points])

                if BuildingPolygonContainsLabel!=[] and len(BuildingPolygonContainsLabel)>0:

                    for building in BuildingPolygonContainsLabel:

                        BuildingDict[building[0]]=[building[1],building[2]]
                else:

                    print(f'Missing Label Building layer Polygon REF # {Building_polygonID}')

        return BuildingDict

    def FindBalconyLengthAndWidth(self,msp):

        returnValueList=[]

        if (msp is None):

            return returnValueList

        try:

            BuildingData=msp.query('*[layer=="_BuildingName"]')

            FloorData=msp.query('*[layer=="_Floor"]')

            BalconyData=msp.query('LWPOLYLINE[layer=="_Balcony"]')

            BuildingLayerDict=self.Building_Layer(BuildingData)

            FloorLayerDict = self.Floor_Layer(FloorData)

            for Building_ID,Building_NamePoly in BuildingLayerDict.items():

                for Floor_ID, Floor_NamePoly in FloorLayerDict.items():

                    if Building_NamePoly[1].contains(Floor_NamePoly[1])==True or Building_NamePoly[1].touches(Floor_NamePoly[1])==True or round(Building_NamePoly[1].distance(Floor_NamePoly[1]),1)==0.0:

                        for balcony_poly in BalconyData:

                            BalconyPolygonID=balcony_poly.dxf.handle

                            if len([bp[0:2] for bp in balcony_poly.get_points()])>3:

                                balcony_polygon_points=Polygon(np.array([bp[0:2] for bp in balcony_poly.get_points()]))

                                if Floor_NamePoly[1].contains(balcony_polygon_points)==True or Floor_NamePoly[1].touches(balcony_polygon_points)==True or round(Floor_NamePoly[1].distance(balcony_polygon_points),1)==0.0:

                                    Balcony_Length=self.BalconyLength(balcony_poly)

                                    Balcony_Width=self.BalconyWidth(balcony_poly)

                                    BalconyDict=dict()

                                    BalconyDict['BLDG_REF'] = Building_ID

                                    BalconyDict['BLDG_NAME'] = Building_NamePoly[0]

                                    BalconyDict['FLOOR_REF'] = Floor_ID

                                    BalconyDict['FLOOR_NAME'] = Floor_NamePoly[0]

                                    BalconyDict['BALCONY_REF']=BalconyPolygonID

                                    BalconyDict['BALCONY_LENGTH'] = Balcony_Length

                                    BalconyDict['BALCONY_WIDTH'] = Balcony_Width

                                    returnValueList.append(BalconyDict)

        except IOError:

            print(f'Not a DXF file or a generic I/O error.')

            return returnValueList

        except ezdxf.DXFStructureError:

             print(f'Invalid or corrupted DXF file.')

             return returnValueList

        return returnValueList


#-----------------------------------------------------Input of DXF file---------------------------------------------------------------

##path of the filename

#folder=r'E:\production_code\dxf_files'

##Pass extension - removed inside method

#filename='Project 382.dxf'                   # Here give only filename

##method returns a dict with handle

#start_time=time.time()

#dxf_path=os.path.join(folder,filename)

#read_dxf_file=ezdxf.readfile(dxf_path)

#msp=read_dxf_file.modelspace()

#response=BalconyLengthAndWidth()

#print(f'Check Balcony Length And Width Response:{response.FindBalconyLengthAndWidth(msp)}')

#end_time=time.time()

#print(f'Total time is:{round(end_time-start_time,2)}')