import ezdxf

import numpy as np

from shapely.geometry import Point,Polygon,LineString

from convert_polygon_to_arc import polygon2arc

class VentilationWidthANDArea:

    def VentilationShaft_Layer(self,VentilationData):

        VentilationDict=dict()

        for vshaft_entity in VentilationData:

            if vshaft_entity.dxftype()=='LWPOLYLINE' and vshaft_entity.closed:

                vshaft_polygonID=vshaft_entity.dxf.handle

                checkArcPolygon= any([entity.dxftype()=="ARC" for entity in vshaft_entity.virtual_entities()])

                if checkArcPolygon:

                    vshaft_polygon_points=polygon2arc.Polygon_Merger_ARC(vshaft_entity)
                else:

                    vshaft_polygon_points=Polygon(np.array([vp[0:2] for vp in vshaft_entity.get_points()]))

                VentilationPolygonContainsLabel=[]

                for vshaft_entity in VentilationData:

                    if vshaft_entity.dxftype()=='TEXT' or vshaft_entity.dxftype()=='MTEXT':

                        vshaftLabelProperties=vshaft_entity.dxfattribs()

                        vshaftLabelID=vshaft_entity.dxf.handle

                        vshaft_label=vshaftLabelProperties.get('text') if vshaft_entity.dxftype()=='TEXT' else vshaft_entity.plain_text()

                        vshaftLabel_insert=vshaftLabelProperties.get('insert')

                        vshaftLabel_point=Point(np.array([vshaftLabel_insert[0],vshaftLabel_insert[1]]))

                        if vshaft_polygon_points.contains(vshaftLabel_point)==True or vshaft_polygon_points.touches(vshaftLabel_point)==True or round(vshaft_polygon_points.distance(vshaftLabel_point),1)==0.0:

                            VentilationPolygonContainsLabel.append([vshaftLabelID,vshaft_label,vshaft_polygon_points])

                if VentilationPolygonContainsLabel!=[] and len(VentilationPolygonContainsLabel)>0:

                    for ventilation in VentilationPolygonContainsLabel:

                        VentilationDict[ventilation[0]]=[ventilation[1],ventilation[2]]
                else:

                    print(f'Missing Label Floor layer Polygon REF # {vshaft_polygonID}')

        return VentilationDict
    def Floor_Layer(self,FloorData):

        FloorDict=dict()

        for Floor_entity in FloorData:

            if Floor_entity.dxftype()=='LWPOLYLINE' and Floor_entity.closed:

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

            if building_entity.dxftype()=='LWPOLYLINE' and building_entity.closed:

                Building_polygonID=building_entity.dxf.handle

                Building_polygon_points=Polygon(np.array([bp[0:2] for bp in building_entity.get_points()]))

                BuildingPolygonContainsLabel=[]

                for building_entity in BuildingData:

                    if building_entity.dxftype()=='TEXT' or building_entity.dxftype()=='MTEXT':

                        buildingLabelProperties=building_entity.dxfattribs()

                        BuildingLabelID=building_entity.dxf.handle

                        Building_label=buildingLabelProperties.get('text') if building_entity.dxftype()=='TEXT' else building_entity.plain_text()

                        if Building_label!='' and len(Building_label)>1:

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

    def VentilationWidth(self,VentilationPolygon):

        b = VentilationPolygon.boundary.coords

        linestrings = [LineString(b[k:k + 2]) for k in range(len(b) - 1)]

        polygon_linestring=[round(ls.distance(ls1),2) for ls in linestrings
                            for ls1 in linestrings if round(ls.distance(ls1),1)>=1.0]

        return min(polygon_linestring)

    def FindVentilationWidthANDArea(self,msp):

        returnValueList=[]

        if (msp is None):

            return returnValueList

        try:

            BuildingData=msp.query('TEXT MTEXT LWPOLYLINE [layer=="_BuildingName"]')

            FloorData=msp.query('TEXT MTEXT LWPOLYLINE [layer=="_Floor"]')

            VentilationData=msp.query('TEXT MTEXT LWPOLYLINE [layer=="_VentilationShaft"]')

            BuildingLayerDict=self.Building_Layer(BuildingData)

            FloorLayerDict = self.Floor_Layer(FloorData)

            VentilationLayerDict=self.VentilationShaft_Layer(VentilationData)

            for Building_ID,Building_NamePoly in BuildingLayerDict.items():

                for Floor_ID, Floor_NamePoly in FloorLayerDict.items():

                    if Building_NamePoly[1].contains(Floor_NamePoly[1])==True or Building_NamePoly[1].touches(Floor_NamePoly[1])==True or round(Building_NamePoly[1].distance(Floor_NamePoly[1]),1)==0.0:

                        for Ventilation_id,Ventilation_labelpoly in VentilationLayerDict.items():

                             if Floor_NamePoly[1].contains(Ventilation_labelpoly[1])==True or Floor_NamePoly[1].touches(Ventilation_labelpoly[1])==True or round(Floor_NamePoly[1].distance(Ventilation_labelpoly[1]),1)==0.0:

                                 Ventilation_area=round(Ventilation_labelpoly[1].area,2)

                                 ventilation_width=self.VentilationWidth(Ventilation_labelpoly[1])

                                 VentilationDict=dict()

                                 VentilationDict['BLDG_REF'] = Building_ID

                                 VentilationDict['BLDG_NAME'] = Building_NamePoly[0]

                                 VentilationDict['FLOOR_REF'] = Floor_ID

                                 VentilationDict['FLOOR_NAME'] = Floor_NamePoly[0]

                                 VentilationDict['VSHAFT_REF']=Ventilation_id

                                 VentilationDict['VSHAFT_NAME']=str(Ventilation_labelpoly[0])

                                 VentilationDict['WIDTH'] = ventilation_width

                                 VentilationDict['AREA'] =Ventilation_area

                                 returnValueList.append(VentilationDict)
        except IOError:

            print(f'Not a DXF file or a generic I/O error.')

            return returnValueList

        except ezdxf.DXFStructureError:

             print(f'Invalid or corrupted DXF file.')

             return returnValueList

        return returnValueList


# #-----------------------------------------------------Input of DXF file---------------------------------------------------------------
#
# #path of the filename
#
# folder="E:/production_code/dxf_files/FireBuildings/"
#
# #Pass extension - removed inside method
#
# filename='msb preval new modified (1) (1).dxf' # Here give only filename
#
# #method returns a dict with handle
#
# dxf_path=os.path.join(folder,filename)
#
# read_dxf_file=ezdxf.readfile(dxf_path)
#
# msp=read_dxf_file.modelspace()
#
# response=VentilationWidthANDArea()
#
# print(f'Check Ventilation Width And Area Response:{response.FindVentilationWidthANDArea(msp)}')