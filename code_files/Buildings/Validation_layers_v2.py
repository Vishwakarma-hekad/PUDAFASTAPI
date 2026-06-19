#-------------------------------- Importing Model ---------------------------------------
import ezdxf

import numpy as np

from shapely.geometry import Polygon,Point,LineString

from shapely import LinearRing

import os

class CommonValidationLayers:

    def PlotTouchCMORN(self,Plot_LayerDict,WallCompound_Dict,OrganizedOpenSpace_LayerDict,MainRoad_LayerDict,NetPlot_LayerDict,RoadWidening_LayerDict):

        ErrorPlotTouchWallCompound=dict()

        for Plot_id,Plot_data in  Plot_LayerDict.items():

            for wall_id,wall_data in WallCompound_Dict.items():

                if Plot_data[1].touches(wall_data[1])==False and round(Plot_data[1].distance(wall_data[1]),1)>0.0:

                    ErrorMsg=f'Warning- {wall_data[0]} REF #({wall_id}) Does Not Touch With Plot Layer.'

                    ErrorPlotTouchWallCompound[wall_id]= ErrorMsg

            for OrganizedOpenSpace_id ,OrganizedOpenSpace_data in OrganizedOpenSpace_LayerDict.items():

                if Plot_data[1].contains(OrganizedOpenSpace_data[1])==False and round(Plot_data[1].distance(OrganizedOpenSpace_data[1]),1)>0.0:

                    ErrorMsg = f'Warning- {OrganizedOpenSpace_data[0]} REF # ({OrganizedOpenSpace_id}) Does Not Touch or Inside With Plot Layer.'

                    ErrorPlotTouchWallCompound[OrganizedOpenSpace_id] = ErrorMsg

            for mainroad_id,mainroad_data in MainRoad_LayerDict.items():

                if Plot_data[1].contains(mainroad_data[1]) == False and round(Plot_data[1].distance(mainroad_data[1]), 1) > 0.0:

                    MainroadwideningORNetplottouch=[]

                    for Netplot_id,Netplot_data in NetPlot_LayerDict.items():

                        if Plot_data[1].touches(Netplot_data[1])==True or round(Plot_data[1].distance(Netplot_data[1]),1)==0.0:

                            if mainroad_data[1].touches(Netplot_data[1])==True or round(mainroad_data[1].distance(Netplot_data[1]),1)==0.0:

                                MainroadwideningORNetplottouch.append(True)

                            else:

                                MainroadwideningORNetplottouch.append(False)

                    for RoadWidening_id, RoadWidening_data in RoadWidening_LayerDict.items():

                        if Plot_data[1].touches(RoadWidening_data[1]) == True or round(Plot_data[1].distance(RoadWidening_data[1]), 1) == 0.0:

                            if mainroad_data[1].touches(RoadWidening_data[1]) == True or round(mainroad_data[1].distance(RoadWidening_data[1]), 1) == 0.0:

                                MainroadwideningORNetplottouch.append(True)

                            else:

                                MainroadwideningORNetplottouch.append(False)

                    if any(MainroadwideningORNetplottouch)==False:

                        ErrorMsg=f'Warning- {mainroad_data[0]} REF# ({mainroad_id}) Does Not Touch With Plot Layer.'

                        ErrorPlotTouchWallCompound[mainroad_id]=ErrorMsg

            for Netplot_id,Netplot_data in NetPlot_LayerDict.items():

                if Plot_data[1].touches(Netplot_data[1])==True and round(Plot_data[1].distance(Netplot_data[1]),1)>0.0:

                    ErrorMsg=f'Warning- {Netplot_data[0]} REF # ({Netplot_id}) Does Not Touch With Plot Layer.'

                    ErrorPlotTouchWallCompound[Netplot_id]=ErrorMsg

            for RoadWidening_id, RoadWidening_data in RoadWidening_LayerDict.items():

                if Plot_data[1].touches(RoadWidening_data[1]) == True and round(Plot_data[1].distance(RoadWidening_data[1]),1) > 0.0:

                    ErrorMsg = f'Warning- {RoadWidening_data[0]} REF # ({RoadWidening_id}) Does Not Touch With Plot Layer.'

                    ErrorPlotTouchWallCompound[RoadWidening_id] = ErrorMsg

        return ErrorPlotTouchWallCompound

    def ProposedWorkContainsTwoDIRREFCIRCLE(self,ProposedWork_LayerDict,floorDIRREFCircleDict,ResiBUADIRREFCircleDict):

        ErrorProposedWorkContainsTwoDIRREFCIRCLE=dict()

        for proposedwork_id,proposedwork_data in ProposedWork_LayerDict.items():

            floorContainsFloorDirRefCircles=[]

            for floorcircle_id,floorcircle_point in floorDIRREFCircleDict.items():

                if proposedwork_data[1].contains(floorcircle_point)==True or proposedwork_data[1].touches(floorcircle_point)==True or round(proposedwork_data[1].distance(floorcircle_point),1)==0.0:

                    floorContainsFloorDirRefCircles.append(True)

            if floorContainsFloorDirRefCircles==[] and len(floorContainsFloorDirRefCircles)==0:

               ErrorMsg=f'Warning- {proposedwork_data[0]} REF # ({proposedwork_id}) Proposed Layer Missing Direction Reference Circle Of Floor Layer.'

               ErrorProposedWorkContainsTwoDIRREFCIRCLE[proposedwork_id]=ErrorMsg

            elif(len(floorContainsFloorDirRefCircles)>1):

                ErrorMsg = f'Warning- {proposedwork_data[0]} REF # ({proposedwork_id}) Proposed Layer Found More Than One Direction Reference Circle Of Floor Layer.'

                ErrorProposedWorkContainsTwoDIRREFCIRCLE[proposedwork_id] = ErrorMsg

            floorContainsResiDirRefCircles = []

            for resicircle_id, resicircle_point in ResiBUADIRREFCircleDict.items():

                if proposedwork_data[1].contains(resicircle_point) == True or proposedwork_data[1].touches(resicircle_point) == True or round(proposedwork_data[1].distance(resicircle_point), 1) == 0.0:

                    floorContainsResiDirRefCircles.append(True)

            if floorContainsResiDirRefCircles==[] and len(floorContainsResiDirRefCircles)==0:

                ErrorMsg = f'Warning- {proposedwork_data[0]} REF # ({proposedwork_id}) Proposed Layer Missing Direction Reference Circle Of ResiBUA Layer.'

                ErrorProposedWorkContainsTwoDIRREFCIRCLE[proposedwork_id] = ErrorMsg

            elif(len(floorContainsResiDirRefCircles)>1):

                ErrorMsg = f'Warning- {proposedwork_data[0]} REF # ({proposedwork_id}) Proposed Layer Found More Than One Direction Reference Circle Of ResiBUA Layer.'

                ErrorProposedWorkContainsTwoDIRREFCIRCLE[proposedwork_id] = ErrorMsg

        return ErrorProposedWorkContainsTwoDIRREFCIRCLE

    def FloorContainsTwoDIRREFCIRCLE(self,building_data,floorDIRREFCircleDict,ResiBUADIRREFCircleDict):

        ErrorFloorContainsTwoDIRREFCIRCLE=dict()

        BuildingName,Buildingdata=building_data[0],building_data[1]

        for floor_data in Buildingdata:

            floorContainsFloorDirRefCircles=[]

            for floorcircle_id,floorcircle_point in floorDIRREFCircleDict.items():

                if floor_data[2].contains(floorcircle_point)==True or floor_data[2].touches(floorcircle_point)==True or round(floor_data[2].distance(floorcircle_point),1)==0.0:

                    floorContainsFloorDirRefCircles.append(True)

            if floorContainsFloorDirRefCircles==[] and len(floorContainsFloorDirRefCircles)==0:

               ErrorMsg=f'Warning- {floor_data[1]} REF # ({floor_data[0]}) Missing Direction Reference Circle Of Floor Layer.'

               ErrorFloorContainsTwoDIRREFCIRCLE[floor_data[0]]=ErrorMsg

            elif(len(floorContainsFloorDirRefCircles)>1):
                #print(floorContainsFloorDirRefCircles)
                ErrorMsg = f'Warning- {floor_data[1]} REF # ({floor_data[0]}) Found More Than One Direction Reference Circle Of Floor Layer.'

                ErrorFloorContainsTwoDIRREFCIRCLE[floor_data[0]] = ErrorMsg

            floorContainsResiDirRefCircles = []

            for resicircle_id, resicircle_point in ResiBUADIRREFCircleDict.items():

                if floor_data[2].contains(resicircle_point) == True or floor_data[2].touches(resicircle_point) == True or round(floor_data[2].distance(resicircle_point), 1) == 0.0:

                    floorContainsResiDirRefCircles.append(True)

            if floorContainsResiDirRefCircles==[] and len(floorContainsResiDirRefCircles)==0:

                ErrorMsg = f'Warning- {floor_data[1]} REF # ({floor_data[0]}) Missing Direction Reference Circle Of ResiBUA Layer.'

                ErrorFloorContainsTwoDIRREFCIRCLE[floor_data[0]] = ErrorMsg

            elif(len(floorContainsResiDirRefCircles)>1):

                ErrorMsg = f'Warning- {floor_data[1]} REF # ({floor_data[0]}) Found More Than One Direction Reference Circle Of ResiBUA Layer.'

                ErrorFloorContainsTwoDIRREFCIRCLE[floor_data[0]] = ErrorMsg

        return ErrorFloorContainsTwoDIRREFCIRCLE

    def FloorContainsAnyLayer(self,building_data,ResiBua_Dict,CommBua_Dict,IndBua_Dict,SpecialBua_Dict,Parking_Dict,Terrace_Dict):

        buildingName,FloorData=building_data[0],building_data[1]

        ErrorfloorContainsLayer=dict()

        for floor_data in FloorData:

            floorContainsLayer=[]

            for resibua_poly in ResiBua_Dict[1].values():

                if floor_data[2].contains(resibua_poly)==True or floor_data[2].touches(resibua_poly)==True or round(floor_data[2].distance(resibua_poly),1)==0.0:

                    floorContainsLayer.append(True)

                else:

                    floorContainsLayer.append(True)

            for commbua_poly in CommBua_Dict[1].values():

                if floor_data[2].contains(commbua_poly) == True or floor_data[2].touches(commbua_poly) == True or round(floor_data[2].distance(commbua_poly), 1) == 0.0:

                    floorContainsLayer.append(True)

                else:

                    floorContainsLayer.append(True)

            for indbua_poly in IndBua_Dict[1].values():

                if floor_data[2].contains(indbua_poly) == True or floor_data[2].touches(indbua_poly) == True or round(floor_data[2].distance(indbua_poly), 1) == 0.0:

                    floorContainsLayer.append(True)

                else:

                    floorContainsLayer.append(True)

            for specialbua_poly in SpecialBua_Dict[1].values():

                if floor_data[2].contains(specialbua_poly) == True or floor_data[2].touches(specialbua_poly) == True or round(floor_data[2].distance(specialbua_poly), 1) == 0.0:

                    floorContainsLayer.append(True)

                else:

                    floorContainsLayer.append(True)

            for Parking_poly in Parking_Dict.values():

                if floor_data[2].contains(Parking_poly[1]) == True or floor_data[2].touches(Parking_poly[1]) == True or round(floor_data[2].distance(Parking_poly[1]), 1) == 0.0:

                    floorContainsLayer.append(True)

                else:

                    floorContainsLayer.append(False)

            for Terrace_poly in Terrace_Dict.values():

                if floor_data[2].contains(Terrace_poly[1]) == True or floor_data[2].touches(Terrace_poly[1]) == True or round(floor_data[2].distance(Terrace_poly[1]), 1) == 0.0:

                    floorContainsLayer.append(True)

                else:

                    floorContainsLayer.append(False)

            if floorContainsLayer!=[] and len(floorContainsLayer)>0:

                if any(floorContainsLayer)==False:

                    ErrorMsg=f'Warning- {floor_data[1]} REF # ({floor_data[0]}) Does Not Have Any ResiBUA,CommBUA,IndBUA,SpecialBUA,Parking Or Terrace Layer.'

                    ErrorfloorContainsLayer[floor_data[0]]=ErrorMsg

    def SectionContainsGroundLine(self,Building_Dict,SectionDict,Gl_line):

        ErrorBuildingsConGLineDict=dict()

        for Building_id,BuildingNamePoly in Building_Dict.items():

            BuildingsContainsGLine=[]

            for GLine_id, GLineNamePoly in Gl_line.items():

                if BuildingNamePoly[1].contains(GLineNamePoly[1])==True or BuildingNamePoly[1].touches(GLineNamePoly[1])==True or round(BuildingNamePoly[1].distance(GLineNamePoly[1]),1)==0.0:

                    BuildingsContainsGLine.append(GLineNamePoly[1])

            if BuildingsContainsGLine ==[] and len(BuildingsContainsGLine)==0:

                ErrorMsg=f'Warning- {BuildingNamePoly[0]} REF # ({Building_id}) Does Not Have Any GroundLevel layer'

                ErrorBuildingsConGLineDict[Building_id]=ErrorMsg

            else:

                for section_id, sectionNamePoly in SectionDict.items():

                    if BuildingNamePoly[1].contains(sectionNamePoly[1])==True or BuildingNamePoly[1].touches(sectionNamePoly[1])==True or round(BuildingNamePoly[1].distance(sectionNamePoly[1]),1)==0.0:

                        SectionContainGLine = []

                        for GLine_id, GLineNamePoly in Gl_line.items():

                            if sectionNamePoly[1].contains(GLineNamePoly[1]) == True or sectionNamePoly[1].touches(GLineNamePoly[1]) == True or round(sectionNamePoly[1].distance(GLineNamePoly[1]),1) == 0.0:

                                SectionContainGLine.append(GLineNamePoly[1])

                        if SectionContainGLine==[] and len(SectionContainGLine)==0:

                            ErrorMsg = f'Warning- Ground Level layer Have In  {BuildingNamePoly[0]} REF # ({Building_id}) But Does Not Have {sectionNamePoly[0]} ({section_id}) Layer.'

                            ErrorBuildingsConGLineDict[section_id]=ErrorMsg

        return ErrorBuildingsConGLineDict

    def SectionContainsFloorINSection(self,Building_Dict,SectionDict,FloorInSectionDict):

        ErrorBuildingsConFloorInSectionDict=dict()

        for Building_id,BuildingNamePoly in Building_Dict.items():

            BuildingsContainsFloorInSection=[]

            for FloorInSection_id, FloorInSectionNamePoly in FloorInSectionDict.items():

                if BuildingNamePoly[1].contains(FloorInSectionNamePoly[1])==True or BuildingNamePoly[1].touches(FloorInSectionNamePoly[1])==True or round(BuildingNamePoly[1].distance(FloorInSectionNamePoly[1]),1)==0.0:

                    BuildingsContainsFloorInSection.append(FloorInSectionNamePoly[1])

                    if BuildingsContainsFloorInSection==[] and len(BuildingsContainsFloorInSection)>0:

                        BuildingsContainsFloorInSection.append(FloorInSectionNamePoly[1])

            if BuildingsContainsFloorInSection ==[] and len(BuildingsContainsFloorInSection)==0:

                ErrorMsg=f'Warning- {BuildingNamePoly[0]} REF # ({Building_id}) Does Not Have Any FloorInSection'

                ErrorBuildingsConFloorInSectionDict.append(ErrorMsg)

            else:

                for section_id, sectionNamePoly in SectionDict.items():

                    if BuildingNamePoly[1].contains(sectionNamePoly[1])==True or BuildingNamePoly[1].touches(sectionNamePoly[1])==True or round(BuildingNamePoly[1].distance(sectionNamePoly[1]),1)==0.0:

                        SectionContainFloorInSection = []

                        for floor_in_section_polygon in BuildingsContainsFloorInSection:

                            if sectionNamePoly[1].contains(floor_in_section_polygon) == True or sectionNamePoly[1].touches(floor_in_section_polygon) == True or round(sectionNamePoly[1].distance(floor_in_section_polygon),1) == 0.0:

                                SectionContainFloorInSection.append(floor_in_section_polygon)

                        if SectionContainFloorInSection==[] and len(SectionContainFloorInSection)==0:

                            ErrorMsg = f'Warning- FloorInSection Have In {BuildingNamePoly[0]} REF # ({Building_id}) But Does Not Have {sectionNamePoly[0]} ({section_id}) Layer.'

                            ErrorBuildingsConFloorInSectionDict[section_id]=ErrorMsg

        return ErrorBuildingsConFloorInSectionDict

    def BuildingContainsSectionLayer(self,BuildingDict,SectionDict):

        BuidingContainsSecLayerErr=dict()

        BuidingContainsSecLayer= dict()

        for Building_id,BuildingNamePoly in BuildingDict.items():

            SectionInBuildings=[]

            for Section_id,SectionNamePoly in SectionDict.items():

                if BuildingNamePoly[1].contains(SectionNamePoly[1])==True or BuildingNamePoly[1].touches(SectionNamePoly[1])==True or round(BuildingNamePoly[1].distance(SectionNamePoly[1]),1)==0.0:

                    SectionInBuildings.append([Section_id, SectionNamePoly[0],SectionNamePoly[1]])

            if SectionInBuildings!=[] and len(SectionInBuildings)>0:

                for section in SectionInBuildings:

                    BuidingContainsSecLayer[Building_id]=section

            else:

                ErrorMsg=f'Warning- REF # {Building_id} ({BuildingNamePoly[0]}) Does Not Found Any Section Layer'

                BuidingContainsSecLayerErr[Building_id]=ErrorMsg

        for Section_id, SectionNamePoly in SectionDict.items():

            SectionINBUildings=[]

            for Building_id, BuildingNamePoly in BuildingDict.items():

                if BuildingNamePoly[1].contains(SectionNamePoly[1])==True or BuildingNamePoly[1].touches(SectionNamePoly[1])==True or round(BuildingNamePoly[1].distance(SectionNamePoly[1]),1)==0.0:

                    SectionINBUildings.append(SectionNamePoly[1])

            if SectionINBUildings==[] and len(SectionINBUildings)>0:

                ErrorMsg = f'{Section_id}({SectionNamePoly[0]}) Does Not Found In Any Building Layer'

                BuidingContainsSecLayerErr[Section_id] = ErrorMsg

        return [BuidingContainsSecLayerErr,BuidingContainsSecLayer]

    def BuildingContainsFloor(self,BuildingDict,FloorDict):

        ErrorBuildingContainsFloorDict=dict()

        BuildingContainsFloorDict=dict()

        #loop for Building Layer Building_id-->Building handle id,BuildingNamePoly[0]-->Building Label,BuildingNamePoly[1]-->Building polygon

        for Building_id,BuildingNamePoly in BuildingDict.items():

            BuildingContainsFloor=[]

            # loop for Floor Layer Floor_id-->Floor handle id,FloorNamePoly[0]-->Floor Label,BuildingNamePoly[1]-->Floor polygon

            for Floor_id,FloorNamePoly in FloorDict.items():

                if BuildingNamePoly[1].contains(FloorNamePoly[1])==True or BuildingNamePoly[1].touches(FloorNamePoly[1])==True or round(BuildingNamePoly[1].distance(FloorNamePoly[1]),1)==0.0:

                    BuildingContainsFloor.append([Floor_id,FloorNamePoly[0],FloorNamePoly[1]])

            if BuildingContainsFloor!=[] and len(BuildingContainsFloor)!=0:

                BuildingContainsFloorDict[Building_id]=[BuildingNamePoly[0],BuildingContainsFloor]

            else:

                ErrorBuildingContainsFloorDict[Building_id]=f'Warning- {BuildingNamePoly[0]} REF # ({Building_id}) Does Not Found Any Floor.'

        for Floor_id, FloorNamePoly in FloorDict.items():

            FloorInBuildings=[]

            for Building_id, BuildingNamePoly in BuildingDict.items():

                if BuildingNamePoly[1].contains(FloorNamePoly[1])==True or BuildingNamePoly[1].touches(FloorNamePoly[1])==True or round(BuildingNamePoly[1].distance(FloorNamePoly[1]),1)==0.0:

                    FloorInBuildings.append(BuildingNamePoly)

            if FloorInBuildings==[] and len(FloorInBuildings)==0:

                ErrorBuildingContainsFloorDict[Floor_id]=f'Warning- {FloorNamePoly[0]} REF # ({Floor_id}) Does Not Found In Any Buildings.'

        return [ErrorBuildingContainsFloorDict,BuildingContainsFloorDict]

    def PlotContainsProposedWork(self,Plot_LayerDict,ProposedWork_LayerDict):

        ErrorPlotContainsProposedWork=dict()

        for plot_id,plot_data in Plot_LayerDict.items():

            plotContainsProposedWork=[]

            for proposedWork_id ,proposedWork_data in ProposedWork_LayerDict.items():

                if plot_data[1].contains(proposedWork_data[1])==True or round(plot_data[1].distance(proposedWork_data[1]),1)==0.0:

                    plotContainsProposedWork.append(True)

                else:

                    plotContainsProposedWork.append(False)

            if plotContainsProposedWork==[] and len(plotContainsProposedWork)==0:

                if any(plotContainsProposedWork)==False:

                    ErrorMsg=f'Warning- {plot_data[0]} REF # ({plot_id}) layer Missing ProposedWork.'

                    ErrorPlotContainsProposedWork[plot_data[0]]=ErrorMsg

        return ErrorPlotContainsProposedWork

    def BuildingHeight(self,Building_data,FloorINSection_data):

        building_Height = []

        for buildig_id,BuildingNamePoly in Building_data.items():

            for floorisID,floorisNamePoly in FloorINSection_data.items():

                if 'terrace' in floorisNamePoly[0].lower():

                    if BuildingNamePoly[1].contains(floorisNamePoly[1]) == True or round(BuildingNamePoly[1].distance(floorisNamePoly[1]), 1) == 0.0:

                        for floorisID1, floorisNamePoly1 in FloorINSection_data.items():

                            if 'terrace' not in floorisNamePoly[0].lower() or 'basement' not in floorisNamePoly[0].lower() or 'plinth' not in floorisNamePoly[0].lower():

                                if BuildingNamePoly[1].contains(floorisNamePoly1[1])==True or round(BuildingNamePoly[1].distance(floorisNamePoly1[1]),1)==0.0:

                                    building_Height.append(round(floorisNamePoly[1].distance(floorisNamePoly1[1])))

        return building_Height

    def SpecialBuaOutLine_Layer(self, SpecialBUAOutLine_data):

        SpecialBUAOutLine_dict = dict()

        ErrorSpecialBUAOutLine_dict=dict()

        unique_polygons={}

        for SpecialBUAOutLine_entity in SpecialBUAOutLine_data:

            if SpecialBUAOutLine_entity.dxftype() == 'LWPOLYLINE':

                SpecialBUAOutLinePolygonID = SpecialBUAOutLine_entity.dxf.handle

                vertices = tuple(SpecialBUAOutLine_entity.get_points())

                if vertices in unique_polygons:

                    ErrorSpecialBUAOutLine_dict[SpecialBUAOutLinePolygonID] = str(f"SpecialUseBUAOutline Layer Found Duplicate Polygon Of {SpecialBUAOutLinePolygonID}.")

                else:

                    unique_polygons[vertices] = SpecialBUAOutLine_entity

                SpecialBUAOutLine_polygon = Polygon(np.array([speup[0:2] for speup in SpecialBUAOutLine_entity.get_points()]))

                SpecialBUAOutLine_dict[SpecialBUAOutLinePolygonID]=SpecialBUAOutLine_polygon

        return [ErrorSpecialBUAOutLine_dict,SpecialBUAOutLine_dict]

    def IndBuaOutLine_Layer(self, IndBUAOutLine_data):

        IndBUAOutLine_dict = dict()

        ErrorIndBUAOutLine_dict = dict()

        unique_polygons={}

        for IndBUAOutLine_entity in IndBUAOutLine_data:

            if IndBUAOutLine_entity.dxftype() == 'LWPOLYLINE':

                IndBUAOutLinePolygonID = IndBUAOutLine_entity.dxf.handle

                vertices = tuple(IndBUAOutLine_entity.get_points())

                if vertices in unique_polygons:

                    ErrorIndBUAOutLine_dict[IndBUAOutLinePolygonID] = str(f"IndBUAOutline Layer Found Duplicate Polygon Of {IndBUAOutLinePolygonID}.")

                else:

                    unique_polygons[vertices] = IndBUAOutLine_entity

                IndBUAOutLine_polygon = Polygon(np.array([indp[0:2] for indp in IndBUAOutLine_entity.get_points()]))

                IndBUAOutLine_dict[IndBUAOutLinePolygonID]=IndBUAOutLine_polygon

        return [ErrorIndBUAOutLine_dict,IndBUAOutLine_dict]

    def ResiBuaOutLine_Layer(self, ResiBUAOutLine_data):

        ResiBUAOutLine_dict = dict()

        ErrorResiBuaOutLine_dict = dict()

        unique_polygons={}

        for ResiBUAOutLine_entity in ResiBUAOutLine_data:

            if ResiBUAOutLine_entity.dxftype() == 'LWPOLYLINE':

                ResiBUAOutLinePolygonID = ResiBUAOutLine_entity.dxf.handle

                vertices = tuple(ResiBUAOutLine_entity.get_points())

                if vertices in unique_polygons:

                    ErrorResiBuaOutLine_dict[ResiBUAOutLinePolygonID] = str(f"ResiBUAOutline Layer Found Duplicate Polygon Of {ResiBUAOutLinePolygonID}.")

                else:

                    unique_polygons[vertices] = ResiBUAOutLine_entity

                ResiBUAOutLine_polygon = Polygon(np.array([resip[0:2] for resip in ResiBUAOutLine_entity.get_points()]))

                ResiBUAOutLine_dict[ResiBUAOutLinePolygonID]=ResiBUAOutLine_polygon

        return [ErrorResiBuaOutLine_dict,ResiBUAOutLine_dict]

    def CommBuaOutLine_Layer(self, CommBUAOutLine_data):

        CommBUAOutLine_dict = dict()

        ErrorCommBUAOutLine_dict=dict()

        unique_polygons={}

        for CommBUAOutLine_entity in CommBUAOutLine_data:

            if CommBUAOutLine_entity.dxftype() == 'LWPOLYLINE':

                CommBUAOutLinePolygonID = CommBUAOutLine_entity.dxf.handle

                vertices = tuple(CommBUAOutLine_entity.get_points())

                if vertices in unique_polygons:

                    ErrorCommBUAOutLine_dict[CommBUAOutLinePolygonID] = str(f"CommBUAOutline Layer Found Duplicate Polygon Of {CommBUAOutLinePolygonID}.")

                else:

                    unique_polygons[vertices] = CommBUAOutLine_entity

                CommBUAOutLine_polygon = Polygon(np.array([commp[0:2] for commp in CommBUAOutLine_entity.get_points()]))

                CommBUAOutLine_dict[CommBUAOutLinePolygonID]=CommBUAOutLine_polygon

        return [ErrorCommBUAOutLine_dict,CommBUAOutLine_dict]

    def Terrace_Layer(self, Terrace_data):

        ErrorTerrace_dict=dict()

        Terrace_dict = dict()

        unique_polygons={}

        for Terrace_entity in Terrace_data:

            if Terrace_entity.dxftype() == 'LWPOLYLINE':

                TerracePolygonID = Terrace_entity.dxf.handle

                Terrace_polygon = Polygon(np.array([tp[0:2] for tp in Terrace_entity.get_points()]))

                vertices = tuple(Terrace_entity.get_points())

                if vertices in unique_polygons:

                    #print(str(f"Terrace Layer Found Duplicate Polygon Of {TerracePolygonID}."))

                    ErrorTerrace_dict[TerracePolygonID] = str(f"Terrace Layer Found Duplicate Polygon Of {TerracePolygonID}.")

                else:

                    unique_polygons[vertices] = Terrace_entity

                TerracePolygonContainsLabel = []

                for Terrace_entity in Terrace_data:

                    if Terrace_entity.dxftype() == 'TEXT' or Terrace_entity.dxftype() == 'MTEXT':

                        Terrace_entity_text_properties = Terrace_entity.dxfattribs()

                        Terrace_Name = Terrace_entity_text_properties.get('text') if Terrace_entity.dxftype() == 'TEXT' else Terrace_entity.plain_text()

                        Terrace_text_pts = Terrace_entity_text_properties.get('insert')

                        Terrace_point = Point(np.array([Terrace_text_pts[0], Terrace_text_pts[1]]))

                        if Terrace_polygon.contains(Terrace_point) == True or Terrace_polygon.touches(Terrace_point) == True or round(Terrace_polygon.distance(Terrace_point),1) == 0.0:

                            TerracePolygonContainsLabel.append([Terrace_Name, Terrace_polygon])

                if TerracePolygonContainsLabel != [] and len(TerracePolygonContainsLabel) <=1:

                    for Terracenamepoly in TerracePolygonContainsLabel:

                        Terrace_dict[TerracePolygonID] = Terracenamepoly

                elif(len(TerracePolygonContainsLabel) >1):

                    ErrorTerrace_dict[TerracePolygonID] = str(f'Warning- Terrace Layer Polygon REF # ({TerracePolygonID}) Found More Than One Label')

                else:

                    ErrorTerrace_dict[TerracePolygonID] = str(f'Warning- Terrace Layer Polygon REF # ({TerracePolygonID})  Does Not Found Any Label')

        return [ErrorTerrace_dict,Terrace_dict]

    def Driveway_Layer(self, Driveway_data):

        ErrorDriveway_dict = dict()

        unique_polygons={}

        for Driveway_entity in Driveway_data:

            if Driveway_entity.dxftype() == 'LWPOLYLINE':

                Driveway_properties = Driveway_entity.dxfattribs()

                if Driveway_properties.get('linetype') != 'CENTER':

                    DrivewayPolygonID = Driveway_entity.dxf.handle

                    if len([dwp[0:2] for dwp in Driveway_entity.get_points()]) > 3:

                        Driveway_polygon = Polygon(np.array([dwp[0:2] for dwp in Driveway_entity.get_points()]))

                        vertices = tuple(Driveway_entity.get_points())

                        if vertices in unique_polygons:

                            ErrorDriveway_dict[DrivewayPolygonID] = str(f"Driveway Layer Found Duplicate Polygon Of {DrivewayPolygonID}.")

                        else:

                            unique_polygons[vertices] = Driveway_entity

                        DrivewayPolygonContainsLabel = []

                        for Driveway_entity in Driveway_data:

                            if Driveway_entity.dxftype() == 'TEXT' or Driveway_entity.dxftype() == 'MTEXT':

                                Driveway_text_properties = Driveway_entity.dxfattribs()

                                Driveway_Name = Driveway_text_properties.get('text') if Driveway_entity.dxftype() == 'TEXT' else Driveway_entity.plain_text()

                                Driveway_text_pts = Driveway_text_properties.get('insert')

                                Driveway_point = Point(np.array([Driveway_text_pts[0], Driveway_text_pts[1]]))

                                if Driveway_polygon.contains(Driveway_point) == True or Driveway_polygon.touches(Driveway_point) == True or round(Driveway_polygon.distance(Driveway_point),1) == 0.0:

                                    DrivewayPolygonContainsLabel.append(Driveway_Name)

                        ErrorBothNameANDCenterLineResponce = []

                        if DrivewayPolygonContainsLabel == [] and len(DrivewayPolygonContainsLabel) == 0:

                            ErrorBothNameANDCenterLineResponce.append(str(f'Warning- Driveway Layer Polygon REF # ({DrivewayPolygonID}) Does Not Found Any Label'))

                        elif(len(DrivewayPolygonContainsLabel) > 1):

                            ErrorBothNameANDCenterLineResponce.append(str(f'Warning- Driveway Layer Polygon REF # ({DrivewayPolygonID}) Found More Than One Label'))

                        DrivewayPolygonContainsCenterline = []

                        for Driveway_entity in Driveway_data:

                            if Driveway_entity.dxftype() == 'LWPOLYLINE':

                                Driveway_properties = Driveway_entity.dxfattribs()

                                if Driveway_properties.get('linetype') == 'CENTER':

                                    DrivewayCenterLinePoints = LineString(np.array([dwcl[0:2] for dwcl in Driveway_entity.get_points()]))

                                    if all(Driveway_polygon.touches(Point(point)) or Driveway_polygon.contains(Point(point)) or round(Driveway_polygon.distance(Point(point)),1) == 0.0 for point in DrivewayCenterLinePoints.coords) == True:
                                    #if Driveway_polygon.contains(DrivewayCenterLinePoints) == True or Driveway_polygon.touches(DrivewayCenterLinePoints) == True or round(Driveway_polygon.distance(DrivewayCenterLinePoints), 1) == 0.0:

                                        DrivewayPolygonContainsCenterline.append(DrivewayCenterLinePoints)

                        if DrivewayPolygonContainsCenterline == [] and len(DrivewayPolygonContainsCenterline) == 0:

                            ErrorBothNameANDCenterLineResponce.append(str(f'Warning- Driveway Layer Polygon REF # ({DrivewayPolygonID}) Does Not Found Any CenterLine'))

                        elif(len(DrivewayPolygonContainsCenterline) >1):

                            ErrorBothNameANDCenterLineResponce.append(str(f'Warning- Driveway Layer Polygon REF # ({DrivewayPolygonID}) Found More Than One CenterLine'))

                        ErrorDriveway_dict[DrivewayPolygonID] = ErrorBothNameANDCenterLineResponce

        return ErrorDriveway_dict

    def RefugeArea_Layer(self, RefugeArea_data):

        ErrorRefugeArea_dict=dict()

        unique_polygons={}

        for RefugeArea_entity in RefugeArea_data:

            if RefugeArea_entity.dxftype() == 'LWPOLYLINE':

                RefugeAreaPolygonID = RefugeArea_entity.dxf.handle

                RefugeArea_polygon = Polygon(np.array([rap[0:2] for rap in RefugeArea_entity.get_points()]))

                vertices = tuple(RefugeArea_entity.get_points())

                if vertices in unique_polygons:

                    ErrorRefugeArea_dict[RefugeAreaPolygonID] = str(f"RefugeArea Layer Found Duplicate Polygon Of {RefugeAreaPolygonID}.")

                else:

                    unique_polygons[vertices] = RefugeArea_entity

                RefugeAreaPolygonContainsLabel = []

                for RefugeArea_entity in RefugeArea_data:

                    if RefugeArea_entity.dxftype() == 'TEXT' or RefugeArea_entity.dxftype() == 'MTEXT':

                        RefugeArea_entity_text_properties = RefugeArea_entity.dxfattribs()

                        RefugeArea_Name = RefugeArea_entity_text_properties.get('text') if RefugeArea_entity.dxftype() == 'TEXT' else RefugeArea_entity.plain_text()

                        RefugeArea_text_pts = RefugeArea_entity_text_properties.get('insert')

                        RefugeArea_point = Point(np.array([RefugeArea_text_pts[0], RefugeArea_text_pts[1]]))

                        if RefugeArea_polygon.contains(RefugeArea_point) == True or RefugeArea_polygon.touches(RefugeArea_point) == True or round(RefugeArea_polygon.distance(RefugeArea_point),1) == 0.0:

                            RefugeAreaPolygonContainsLabel.append([RefugeArea_Name, RefugeArea_polygon])

                if RefugeAreaPolygonContainsLabel == [] and len(RefugeAreaPolygonContainsLabel) == 0:

                    ErrorRefugeArea_dict[RefugeAreaPolygonID] = str(f'Warning- RefugeArea Layer Polygon REF # ({RefugeAreaPolygonID}) Does Not Found Any Label')

                elif(len(RefugeAreaPolygonContainsLabel) >1):

                    ErrorRefugeArea_dict[RefugeAreaPolygonID] = str(f'Warning- RefugeArea Layer Polygon REF # ({RefugeAreaPolygonID}) Found More Than One Label')

        return ErrorRefugeArea_dict

    def CarpetArea_Layer(self, CarpetArea_data):

        ErrorCarpetArea_dict=dict()

        unique_polygons={}

        for CarpetArea_entity in CarpetArea_data:

            if CarpetArea_entity.dxftype() == 'LWPOLYLINE':

                CarpetAreaPolygonID = CarpetArea_entity.dxf.handle

                CarpetArea_polygon = Polygon(np.array([cap[0:2] for cap in CarpetArea_entity.get_points()]))

                vertices = tuple(CarpetArea_entity.get_points())

                if vertices in unique_polygons:

                    ErrorCarpetArea_dict[CarpetAreaPolygonID] = str(f"CarpetArea Layer Found Duplicate Polygon Of {CarpetAreaPolygonID}.")

                else:

                    unique_polygons[vertices] = CarpetArea_entity

                CarpetAreaPolygonContainsLabel = []

                for CarpetArea_entity in CarpetArea_data:

                    if CarpetArea_entity.dxftype() == 'TEXT' or CarpetArea_entity.dxftype() == 'MTEXT':

                        CarpetArea_entity_text_properties = CarpetArea_entity.dxfattribs()

                        CarpetArea_Name = CarpetArea_entity_text_properties.get('text') if CarpetArea_entity.dxftype() == 'TEXT' else CarpetArea_entity.plain_text()

                        CarpetArea_text_pts = CarpetArea_entity_text_properties.get('insert')

                        CarpetArea_point = Point(np.array([CarpetArea_text_pts[0], CarpetArea_text_pts[1]]))

                        if CarpetArea_polygon.contains(CarpetArea_point) == True or CarpetArea_polygon.touches(CarpetArea_point) == True or round(CarpetArea_polygon.distance(CarpetArea_point),1) == 0.0:

                            CarpetAreaPolygonContainsLabel.append([CarpetArea_Name, CarpetArea_polygon])

                if CarpetAreaPolygonContainsLabel == [] and len(CarpetAreaPolygonContainsLabel) == 0:

                    ErrorCarpetArea_dict[CarpetAreaPolygonID] = str(f'Warning- CarpetArea Polygon REF # ({CarpetAreaPolygonID}) Does Not Found Any Label')

                elif(len(CarpetAreaPolygonContainsLabel) >1):

                    ErrorCarpetArea_dict[CarpetAreaPolygonID] = str(f'Warning- CarpetArea Polygon REF # ({CarpetAreaPolygonID}) Found More Than One Label')

        return ErrorCarpetArea_dict

    def RoadWidening_Layer(self, RoadWidening_data):

        RoadWidening_dict = dict()

        ErrorRoadWidening_dict=dict()

        unique_polygons={}

        for RoadWidening_entity in RoadWidening_data:

            if RoadWidening_entity.dxftype() == 'LWPOLYLINE':

                RoadWideningPolygonID = RoadWidening_entity.dxf.handle

                RoadWidening_polygon = Polygon(np.array([rwp[0:2] for rwp in RoadWidening_entity.get_points()]))

                vertices = tuple(RoadWidening_entity.get_points())

                if vertices in unique_polygons:

                    ErrorRoadWidening_dict[RoadWideningPolygonID] = str(f"RoadWidening Layer Found Duplicate Polygon Of {RoadWideningPolygonID}.")

                else:

                    unique_polygons[vertices] = RoadWidening_entity

                RoadWideningPolygonContainsLabel = []

                for RoadWidening_entity in RoadWidening_data:

                    if RoadWidening_entity.dxftype() == 'TEXT' or RoadWidening_entity.dxftype() == 'MTEXT':

                        RoadWidening_entity_text_properties = RoadWidening_entity.dxfattribs()

                        RoadWidening_Name = RoadWidening_entity_text_properties.get('text') if RoadWidening_entity.dxftype() == 'TEXT' else RoadWidening_entity.plain_text()

                        RoadWidening_text_pts = RoadWidening_entity_text_properties.get('insert')

                        RoadWidening_point = Point(np.array([RoadWidening_text_pts[0], RoadWidening_text_pts[1]]))

                        if RoadWidening_polygon.contains(RoadWidening_point) == True or RoadWidening_polygon.touches(RoadWidening_point) == True or round(RoadWidening_polygon.distance(RoadWidening_point),1) == 0.0:

                            RoadWideningPolygonContainsLabel.append([RoadWidening_Name, RoadWidening_polygon])

                if RoadWideningPolygonContainsLabel != [] and len(RoadWideningPolygonContainsLabel) <= 1:

                    for RoadWideningnamepoly in RoadWideningPolygonContainsLabel:

                        RoadWidening_dict[RoadWideningPolygonID] = RoadWideningnamepoly

                elif(len(RoadWideningPolygonContainsLabel) > 1):

                    ErrorRoadWidening_dict[RoadWideningPolygonID] = str(f'Warning- RoadWidening Layer Polygon REF # ({RoadWideningPolygonID}) Found More Than One Label')

                else:

                    ErrorRoadWidening_dict[RoadWideningPolygonID] = str(f'Warning- RoadWidening Layer Polygon REF # ({RoadWideningPolygonID}) Does Not Found Any Label')

        return [ErrorRoadWidening_dict,RoadWidening_dict]

    def NetPlot_Layer(self, NetPlot_data):

        NetPlot_dict = dict()

        ErrorNetPlot_dict=dict()

        unique_polygons={}

        for NetPlot_entity in NetPlot_data:

            if NetPlot_entity.dxftype() == 'LWPOLYLINE':

                NetPlotPolygonID = NetPlot_entity.dxf.handle

                vertices = tuple(NetPlot_entity.get_points())

                if vertices in unique_polygons:

                    ErrorNetPlot_dict[NetPlotPolygonID] = str(f"NetPlot Layer Found Duplicate Polygon Of {NetPlotPolygonID}.")

                else:

                    unique_polygons[vertices] = NetPlot_entity

                NetPlot_polygon = Polygon(np.array([netpp[0:2] for netpp in NetPlot_entity.get_points()]))

                NetPlotPolygonContainsLabel = []

                for NetPlot_entity in NetPlot_data:

                    if NetPlot_entity.dxftype() == 'TEXT' or NetPlot_entity.dxftype() == 'MTEXT':

                        NetPlot_entity_text_properties = NetPlot_entity.dxfattribs()

                        NetPlot_Name = NetPlot_entity_text_properties.get('text') if NetPlot_entity.dxftype() == 'TEXT' else NetPlot_entity.plain_text()

                        NetPlot_text_pts = NetPlot_entity_text_properties.get('insert')

                        NetPlot_point = Point(np.array([NetPlot_text_pts[0], NetPlot_text_pts[1]]))

                        if NetPlot_polygon.contains(NetPlot_point) == True or NetPlot_polygon.touches(NetPlot_point) == True or round(NetPlot_polygon.distance(NetPlot_point),1) == 0.0:

                            NetPlotPolygonContainsLabel.append([NetPlot_Name, NetPlot_polygon])

                if NetPlotPolygonContainsLabel != [] and len(NetPlotPolygonContainsLabel) > 0:

                    for NetPlotnamepoly in NetPlotPolygonContainsLabel:

                        NetPlot_dict[NetPlotPolygonID] = NetPlotnamepoly

        return [ErrorNetPlot_dict,NetPlot_dict]

    def Section_Layer(self, Section_data):

        Section_dict = dict()

        ErrorSection_dict=dict()

        unique_polygons={}

        for Section_entity in Section_data:

            if Section_entity.dxftype() == 'LWPOLYLINE':

                SectionPolygonID = Section_entity.dxf.handle

                Section_polygon = Polygon(np.array([sp[0:2] for sp in Section_entity.get_points()]))

                vertices = tuple(Section_entity.get_points())

                if vertices in unique_polygons:

                    ErrorSection_dict[SectionPolygonID] = str(f"Section Layer Found Duplicate Polygon Of {SectionPolygonID}.")

                else:

                    unique_polygons[vertices] = Section_entity

                SectionPolygonContainsLabel = []

                for Section_entity in Section_data:

                    if Section_entity.dxftype() == 'TEXT' or Section_entity.dxftype() == 'MTEXT':

                        Section_entity_text_properties = Section_entity.dxfattribs()

                        Section_Name = Section_entity_text_properties.get('text') if Section_entity.dxftype() == 'TEXT' else Section_entity.plain_text()

                        Section_text_pts = Section_entity_text_properties.get('insert')

                        Section_point = Point(np.array([Section_text_pts[0], Section_text_pts[1]]))

                        if Section_polygon.contains(Section_point) == True or Section_polygon.touches(Section_point) == True or round(Section_polygon.distance(Section_point),1) == 0.0:

                            SectionPolygonContainsLabel.append([Section_Name, Section_polygon])

                if SectionPolygonContainsLabel != [] and len(SectionPolygonContainsLabel) <=1:

                    for Sectionnamepoly in SectionPolygonContainsLabel:

                        Section_dict[SectionPolygonID] = Sectionnamepoly

                elif(len(SectionPolygonContainsLabel) >1):

                    ErrorSection_dict[SectionPolygonID] = str(f'Warning- Section Layer Polygon REF # ({SectionPolygonID}) Found More Than One Label')

                else:

                    ErrorSection_dict[SectionPolygonID] = str(f'Warning- Section Layer Polygon REF # ({SectionPolygonID}) Does Not Found Any Label')

        return [ErrorSection_dict,Section_dict]

    def Ramp_Layer(self,Ramp_data):

        ErrorRamp_dict = dict()

        unique_polygons={}

        for Ramp_entity in Ramp_data:

            if Ramp_entity.dxftype() == 'LWPOLYLINE':

                Ramp_properties=Ramp_entity.dxfattribs()

                if Ramp_properties.get('linetype')!='CENTER':

                    RampPolygonID = Ramp_entity.dxf.handle

                    if len([rp[0:2] for rp in Ramp_entity.get_points()])>3:

                        Ramp_polygon = Polygon(np.array([rp[0:2] for rp in Ramp_entity.get_points()]))

                        vertices = tuple(Ramp_entity.get_points())

                        if vertices in unique_polygons:

                            ErrorRamp_dict[RampPolygonID] = str(f"Ramp Layer Found Duplicate Polygon Of {RampPolygonID}.")

                        else:

                            unique_polygons[vertices] = Ramp_entity

                        RampPolygonContainsLabel = []

                        for Ramp_entity in Ramp_data:

                            if Ramp_entity.dxftype() == 'TEXT' or Ramp_entity.dxftype() == 'MTEXT':

                                Ramp_text_properties = Ramp_entity.dxfattribs()

                                Ramp_Name = Ramp_text_properties.get('text') if Ramp_entity.dxftype() == 'TEXT' else Ramp_entity.plain_text()

                                Ramp_text_pts = Ramp_text_properties.get('insert')

                                Ramp_point = Point(np.array([Ramp_text_pts[0], Ramp_text_pts[1]]))

                                if Ramp_polygon.contains(Ramp_point) == True or Ramp_polygon.touches(Ramp_point) == True or round(Ramp_polygon.distance(Ramp_point), 1) == 0.0:

                                    RampPolygonContainsLabel.append(Ramp_Name)

                        ErrorBothNameANDCenterLineResponce=[]

                        if RampPolygonContainsLabel == [] and len(RampPolygonContainsLabel)==0:

                            ErrorBothNameANDCenterLineResponce.append(str(f'Warning- Ramp Layer Polygon REF # ({RampPolygonID}) Does Not Found Any Label'))

                        elif(len(RampPolygonContainsLabel)>1):

                            ErrorBothNameANDCenterLineResponce.append(str(f'Warning- Ramp Layer Polygon REF # ({RampPolygonID}) Found More Than One Label'))

                        RampPolygonContainsCenterline=[]

                        for Ramp_entity in Ramp_data:

                            if Ramp_entity.dxftype()=='LWPOLYLINE':

                                Ramp_properties=Ramp_entity.dxfattribs()

                                if Ramp_properties.get('linetype')=='CENTER':

                                    RampCenterLinePoints=LineString(np.array([rcl[0:2] for rcl in Ramp_entity.get_points()]))

                                    if all(Ramp_polygon.touches(Point(point)) or Ramp_polygon.contains(Point(point)) or round(Ramp_polygon.distance(Point(point)),1) == 0.0 for point in RampCenterLinePoints.coords) == True:

                                    #if Ramp_polygon.contains(RampCenterLinePoints) == True or Ramp_polygon.touches(RampCenterLinePoints) == True or round(Ramp_polygon.distance(RampCenterLinePoints), 1) == 0.0:

                                        RampPolygonContainsCenterline.append(RampCenterLinePoints)

                        if RampPolygonContainsCenterline==[] and len(RampPolygonContainsCenterline)==0:

                            ErrorBothNameANDCenterLineResponce.append(str(f'Warning-Ramp Layer Polygon REF # ({RampPolygonID}) Does Not Found Any CenterLine'))

                        elif(len(RampPolygonContainsCenterline)>1):

                            ErrorBothNameANDCenterLineResponce.append(str(f'Warning-Ramp Layer Polygon REF # ({RampPolygonID}) Found More Than One CenterLine'))

                        ErrorRamp_dict[RampPolygonID]=ErrorBothNameANDCenterLineResponce

        return ErrorRamp_dict

    def Passage_Layer(self,Passage_data):

        ErrorPassage_dict = dict()

        unique_polygons={}

        for Passage_entity in Passage_data:

            if Passage_entity.dxftype() == 'LWPOLYLINE':

                Passage_properties=Passage_entity.dxfattribs()

                if Passage_properties.get('linetype')!='CENTER':

                    PassagePolygonID = Passage_entity.dxf.handle

                    if len([pp[0:2] for pp in Passage_entity.get_points()])>3:

                        Passage_polygon = Polygon(np.array([pp[0:2] for pp in Passage_entity.get_points()]))

                        vertices = tuple(Passage_entity.get_points())

                        if vertices in unique_polygons:

                            ErrorPassage_dict[PassagePolygonID] = str(f"Passage Layer Found Duplicate Polygon Of {PassagePolygonID}.")

                        else:

                            unique_polygons[vertices] = Passage_entity

                        PassagePolygonContainsLabel = []

                        for Passage_entity in Passage_data:

                            if Passage_entity.dxftype() == 'TEXT' or Passage_entity.dxftype() == 'MTEXT':

                                Passage_text_properties = Passage_entity.dxfattribs()

                                Passage_Name = Passage_text_properties.get('text') if Passage_entity.dxftype() == 'TEXT' else Passage_entity.plain_text()

                                Passage_text_pts = Passage_text_properties.get('insert')

                                Passage_point = Point(np.array([Passage_text_pts[0], Passage_text_pts[1]]))

                                if Passage_polygon.contains(Passage_point) == True or Passage_polygon.touches(Passage_point) == True or round(Passage_polygon.distance(Passage_point), 1) == 0.0:

                                    PassagePolygonContainsLabel.append(Passage_Name)

                        BothNameANDCenterLineResponce = []

                        ErrorBothNameANDCenterLineResponce = []

                        if PassagePolygonContainsLabel == [] and len(PassagePolygonContainsLabel)==0:

                            ErrorBothNameANDCenterLineResponce.append(str(f'Warning- Passage Layer Polygon REF # ({PassagePolygonID}) Does Not Found Any Label'))

                        elif(len(PassagePolygonContainsLabel)>1):

                            ErrorBothNameANDCenterLineResponce.append(str(f'Warning- Passage Layer Polygon REF # ({PassagePolygonID}) Found More Than One Label'))

                        PassagePolygonContainsCenterline=[]

                        for Passage_entity in Passage_data:

                            if Passage_entity.dxftype()=='LWPOLYLINE':

                                Passage_properties=Passage_entity.dxfattribs()

                                if Passage_properties.get('linetype')=='CENTER':

                                    PassageCenterLinePoints=LineString(np.array([pcl[0:2] for pcl in Passage_entity.get_points()]))
                                    if all(Passage_polygon.touches(Point(point)) or Passage_polygon.contains(Point(point)) or round(Passage_polygon.distance(Point(point)),1) == 0.0 for point in PassageCenterLinePoints.coords) == True:
                                    #if Passage_polygon.contains(PassageCenterLinePoints) == True or Passage_polygon.touches(PassageCenterLinePoints) == True or round(Passage_polygon.distance(PassageCenterLinePoints), 1) == 0.0:

                                        PassagePolygonContainsCenterline.append(PassageCenterLinePoints)

                        if PassagePolygonContainsCenterline==[] and len(PassagePolygonContainsCenterline)==0:

                            ErrorBothNameANDCenterLineResponce.append(str(f'Warning- Passage Polygon REF # ({PassagePolygonID}) Does Not Found Any CenterLine'))

                        elif(len(PassagePolygonContainsCenterline)>1):

                            ErrorBothNameANDCenterLineResponce.append(str(f'Warning- Passage Polygon REF # ({PassagePolygonID}) Found More Than One CenterLine'))

                        ErrorPassage_dict[PassagePolygonID]=ErrorBothNameANDCenterLineResponce

        return ErrorPassage_dict

    def SlabCutOutVoid_Layer(self, SlabCutOutVoid_data):

        ErrorSlabCutOutVoid_dict = dict()

        unique_polygons={}

        for SlabCutOutVoid_entity in SlabCutOutVoid_data:

            if SlabCutOutVoid_entity.dxftype() == 'LWPOLYLINE':

                SlabCutOutVoidPolygonID = SlabCutOutVoid_entity.dxf.handle

                SlabCutOutVoid_polygon = Polygon(np.array([scovp[0:2] for scovp in SlabCutOutVoid_entity.get_points()]))

                vertices = tuple(SlabCutOutVoid_entity.get_points())

                if vertices in unique_polygons:

                    ErrorSlabCutOutVoid_dict[SlabCutOutVoidPolygonID] = str(f"SlabCutOutVoid Layer Found Duplicate Polygon Of {SlabCutOutVoidPolygonID}.")

                else:

                    unique_polygons[vertices] = SlabCutOutVoid_entity

                SlabCutOutVoidPolygonContainsLabel = []

                for SlabCutOutVoid_entity in SlabCutOutVoid_data:

                    if SlabCutOutVoid_entity.dxftype() == 'TEXT' or SlabCutOutVoid_entity.dxftype() == 'MTEXT':

                        SlabCutOutVoid_entity_text_properties = SlabCutOutVoid_entity.dxfattribs()

                        SlabCutOutVoid_Name = SlabCutOutVoid_entity_text_properties.get('text') if SlabCutOutVoid_entity.dxftype() == 'TEXT' else SlabCutOutVoid_entity.plain_text()

                        SlabCutOutVoid_text_pts = SlabCutOutVoid_entity_text_properties.get('insert')

                        SlabCutOutVoid_point = Point(np.array([SlabCutOutVoid_text_pts[0], SlabCutOutVoid_text_pts[1]]))

                        if SlabCutOutVoid_polygon.contains(SlabCutOutVoid_point) == True or SlabCutOutVoid_polygon.touches(SlabCutOutVoid_point) == True or round(SlabCutOutVoid_polygon.distance(SlabCutOutVoid_point),1) == 0.0:

                            SlabCutOutVoidPolygonContainsLabel.append([SlabCutOutVoid_Name, SlabCutOutVoid_polygon])

                if SlabCutOutVoidPolygonContainsLabel == [] and len(SlabCutOutVoidPolygonContainsLabel) == 0:

                    ErrorSlabCutOutVoid_dict[SlabCutOutVoidPolygonID] = str(f'Warning- SlabCutOutVoid Layer Polygon REF # ({SlabCutOutVoidPolygonID}) Polygon Does Not Found Any Label')

                elif(len(SlabCutOutVoidPolygonContainsLabel)>1):

                    ErrorSlabCutOutVoid_dict[SlabCutOutVoidPolygonID] = str(f'Warning- SlabCutOutVoid Layer Polygon REF # ({SlabCutOutVoidPolygonID}) Polygon Found More Than One Label')

        return ErrorSlabCutOutVoid_dict

    def Parking_Layer(self, Parking_data):

        Parking_dict = dict()

        ErrorParking_dict = dict()

        unique_polygons={}

        for Parking_entity in Parking_data:

            if Parking_entity.dxftype() == 'LWPOLYLINE':

                ParkingPolygonID = Parking_entity.dxf.handle

                vertices = tuple(Parking_entity.get_points())

                if vertices in unique_polygons:

                    ErrorParking_dict[ParkingPolygonID] = str(f"Parking Layer Found Duplicate Polygon or Label Of {ParkingPolygonID}.")

                else:

                    unique_polygons[vertices] = Parking_entity



                if any(Parking_entity.dxf.color==parkingcolor for parkingcolor in [63,64,65])==True:

                    if len([pp[0:2] for pp in Parking_entity.get_points()])>3:

                        Parking_polygon = Polygon(np.array([pp[0:2] for pp in Parking_entity.get_points()]))

                        ParkingPolygonContainsLabel = []

                        for Parking_entity in Parking_data:

                            if Parking_entity.dxftype() == 'TEXT' or Parking_entity.dxftype() == 'MTEXT':

                                Parking_entity_text_properties = Parking_entity.dxfattribs()

                                Parking_Name = Parking_entity_text_properties.get('text') if Parking_entity.dxftype() == 'TEXT' else Parking_entity.plain_text()

                                if any(stackp in Parking_Name.lower() for stackp in ['mech','stack'])==True and any(stacklc==Parking_entity.dxf.color for stacklc in [63,64,65])==True:

                                    Parking_text_pts = Parking_entity_text_properties.get('insert')

                                    Parking_point = Point(np.array([Parking_text_pts[0], Parking_text_pts[1]]))

                                    if Parking_polygon.contains(Parking_point) == True or Parking_polygon.touches(Parking_point) == True or round(Parking_polygon.distance(Parking_point),1) == 0.0:

                                        ParkingPolygonContainsLabel.append([Parking_Name, Parking_polygon])

                        if ParkingPolygonContainsLabel != [] and len(ParkingPolygonContainsLabel)>0:

                            for Parkingnamepoly in ParkingPolygonContainsLabel:

                                Parking_dict[ParkingPolygonID] = Parkingnamepoly

                        else:

                            ErrorParking_dict[ParkingPolygonID] = str(f'Warning- Parking (Stack Parking) Layer Polygon #REF ({ParkingPolygonID}) Does Not Found Any Stack Parking Label')

                else:

                    if len([pp[0:2] for pp in Parking_entity.get_points()])>3:

                        Parking_polygon = Polygon(np.array([pp[0:2] for pp in Parking_entity.get_points()]))

                        ParkingPolygonContainsLabel = []

                        for textParking_entity in Parking_data:

                            if textParking_entity.dxftype() == 'TEXT' or textParking_entity.dxftype() == 'MTEXT':

                                Parking_entity_text_properties = textParking_entity.dxfattribs()

                                Parking_Name = Parking_entity_text_properties.get('text') if textParking_entity.dxftype() == 'TEXT' else textParking_entity.plain_text()

                                Parking_text_pts = Parking_entity_text_properties.get('insert')

                                Parking_point = Point(np.array([Parking_text_pts[0], Parking_text_pts[1]]))

                                if Parking_polygon.contains(Parking_point) == True or Parking_polygon.touches(Parking_point) == True or round(Parking_polygon.distance(Parking_point),1) == 0.0:

                                    ParkingPolygonContainsLabel.append([Parking_Name, Parking_polygon])

                        if ParkingPolygonContainsLabel != [] and len(ParkingPolygonContainsLabel)==1:

                            for Parkingnamepoly in ParkingPolygonContainsLabel:

                                Parking_dict[ParkingPolygonID] = Parkingnamepoly

                        elif(ParkingPolygonContainsLabel != [] and len(ParkingPolygonContainsLabel)>1):

                             check_parking=[str(Parkingnamepoly[0].replace(' ','')).lower()=='parking' for Parkingnamepoly in ParkingPolygonContainsLabel]

                             if any(check_parking)!=True:

                                 ErrorParking_dict[ParkingPolygonID] = str(
                                     f'Warning- Parking Layer Polygon #REF ({ParkingPolygonID}) Does Not Found Any Parking Label')
                        else:

                            ErrorParking_dict[ParkingPolygonID] = str(f'Warning- Parking Layer Polygon #REF ({ParkingPolygonID}) Does Not Found Any Label')
        #print([ErrorParking_dict,Parking_dict])
        return [ErrorParking_dict,Parking_dict]

    def StairCase_Layer(self, StairCase_data):

        ErrorStairCase_dict = dict()

        unique_polygons={}

        for StairCase_entity in StairCase_data:

            if StairCase_entity.dxftype() == 'LWPOLYLINE':

                StairCasePolygonID = StairCase_entity.dxf.handle

                if len([sp[0:2] for sp in StairCase_entity.get_points()])>3:

                    StairCase_polygon=Polygon(LinearRing(np.array([sp[0:2] for sp in StairCase_entity.get_points()])))

                    vertices = tuple(StairCase_entity.get_points())

                    if vertices in unique_polygons:

                        ErrorStairCase_dict[StairCasePolygonID] = str(f" StairCase Layer Found Duplicate Polygon Of {StairCasePolygonID}.")

                    else:

                        unique_polygons[vertices] = StairCase_entity

                    StairCasePolygonContainsLabel = []

                    for StairCase_entity in StairCase_data:

                        if StairCase_entity.dxftype() == 'TEXT' or StairCase_entity.dxftype() == 'MTEXT':

                            StairCase_entity_text_properties = StairCase_entity.dxfattribs()

                            StairCase_Name = StairCase_entity_text_properties.get('text') if StairCase_entity.dxftype() == 'TEXT' else StairCase_entity.plain_text()
                            #print(StairCase_Name)
                            if any(stairtext in StairCase_Name.lower() for stairtext in ['staircase','stair case',' staircase','staircase '])==True:

                                StairCase_text_pts = StairCase_entity_text_properties.get('insert')

                                StairCase_point = Point(np.array([StairCase_text_pts[0], StairCase_text_pts[1]]))

                                if StairCase_polygon.contains(StairCase_point) == True or StairCase_polygon.touches(StairCase_point) == True or round(StairCase_polygon.distance(StairCase_point),1) == 0.0:

                                    StairCasePolygonContainsLabel.append([StairCase_Name, StairCase_polygon])

                    if StairCasePolygonContainsLabel == [] and len(StairCasePolygonContainsLabel) == 0:

                        ErrorStairCase_dict[StairCasePolygonID] = str(f'Warning- StairCase Layer Polygon REF # ({StairCasePolygonID}) Does Not Found Any Label')

                    elif(len(StairCasePolygonContainsLabel) >1):

                        ErrorStairCase_dict[StairCasePolygonID] = str(f'Warning- StairCase Layer Polygon REF # ({StairCasePolygonID}) Found More Than One Label')

        return ErrorStairCase_dict

    def Balcony_Layer(self, Balcony_data):

        ErrorBalcony_dict = dict()

        unique_polygons={}

        for Balcony_entity in Balcony_data:

            if Balcony_entity.dxftype() == 'LWPOLYLINE':

                BalconyPolygonID = Balcony_entity.dxf.handle

                Balcony_polygon = Polygon(np.array([bp[0:2] for bp in Balcony_entity.get_points()]))

                vertices = tuple(Balcony_entity.get_points())

                if vertices in unique_polygons:

                    ErrorBalcony_dict[BalconyPolygonID] = str(f"Balcony Layer Found Duplicate Polygon Of {BalconyPolygonID}.")

                else:

                    unique_polygons[vertices] = Balcony_entity


                BalconyPolygonContainsLabel = []

                for Balcony_entity in Balcony_data:

                    if Balcony_entity.dxftype() == 'TEXT' or Balcony_entity.dxftype() == 'MTEXT':

                        Balcony_entity_text_properties = Balcony_entity.dxfattribs()

                        Balcony_Name = Balcony_entity_text_properties.get('text') if Balcony_entity.dxftype() == 'TEXT' else Balcony_entity.plain_text()

                        Balcony_text_pts = Balcony_entity_text_properties.get('insert')

                        Balcony_point = Point(np.array([Balcony_text_pts[0], Balcony_text_pts[1]]))

                        if Balcony_polygon.contains(Balcony_point) == True or Balcony_polygon.touches(Balcony_point) == True or round(Balcony_polygon.distance(Balcony_point),1) == 0.0:

                            BalconyPolygonContainsLabel.append([Balcony_Name, Balcony_polygon])

                if BalconyPolygonContainsLabel == [] and len(BalconyPolygonContainsLabel) == 0:

                    ErrorBalcony_dict[BalconyPolygonID] = str(f'Warning- Balcony Layer Polygon REF # ({BalconyPolygonID}) Does Not Found Any Label')

                elif(len(BalconyPolygonContainsLabel)>1):

                    ErrorBalcony_dict[BalconyPolygonID] = str(f'Warning- Balcony Layer Polygon REF # ({BalconyPolygonID}) Found More Than One Label')

        return ErrorBalcony_dict

    def MortgageArea_Layer(self, MortgageArea_data):

        MortgageArea_dict = dict()

        ErrorMortgageArea_dict = dict()

        unique_polygons={}

        for MortgageArea_entity in MortgageArea_data:

            if MortgageArea_entity.dxftype() == 'LWPOLYLINE':

                MortgageAreaPolygonID = MortgageArea_entity.dxf.handle

                MortgageArea_polygon = Polygon(np.array([map[0:2] for map in MortgageArea_entity.get_points()]))

                vertices = tuple(MortgageArea_entity.get_points())

                if vertices in unique_polygons:

                    ErrorMortgageArea_dict[MortgageAreaPolygonID] = str(f"MortgageArea Layer Found Duplicate Polygon Of {MortgageAreaPolygonID}.")

                else:

                    unique_polygons[vertices] = MortgageArea_entity

                MortgageAreaPolygonContainsLabel = []

                for MortgageArea_entity in MortgageArea_data:

                    if MortgageArea_entity.dxftype() == 'TEXT' or MortgageArea_entity.dxftype() == 'MTEXT':

                        MortgageArea_entity_text_properties = MortgageArea_entity.dxfattribs()

                        MortgageArea_Name = MortgageArea_entity_text_properties.get('text') if MortgageArea_entity.dxftype() == 'TEXT' else MortgageArea_entity.plain_text()

                        MortgageArea_text_pts = MortgageArea_entity_text_properties.get('insert')

                        MortgageArea_point = Point(np.array([MortgageArea_text_pts[0], MortgageArea_text_pts[1]]))

                        if MortgageArea_polygon.contains(MortgageArea_point) == True or MortgageArea_polygon.touches(MortgageArea_point) == True or round(MortgageArea_polygon.distance(MortgageArea_point), 1) == 0.0:

                            MortgageAreaPolygonContainsLabel.append([MortgageArea_Name, MortgageArea_polygon])

                if MortgageAreaPolygonContainsLabel != [] and len(MortgageAreaPolygonContainsLabel) <=1:

                    for MortgageAreanamepoly in MortgageAreaPolygonContainsLabel:

                        MortgageArea_dict[MortgageAreaPolygonID] = MortgageAreanamepoly

                elif(len(MortgageAreaPolygonContainsLabel) > 1):

                    ErrorMortgageArea_dict[MortgageAreaPolygonID] = str(f'Warning- MortgageArea Layer Polygon REF # ({MortgageAreaPolygonID}) Found More Than One Label')

                else:

                    ErrorMortgageArea_dict[MortgageAreaPolygonID] = str(f'Warning- MortgageArea Layer Polygon REF # ({MortgageAreaPolygonID}) Does Not Found Any Label')

        return [ErrorMortgageArea_dict,MortgageArea_dict]

    def Lift_Layer(self, Lift_data):

        ErrorLift_dict=dict()

        unique_polygons={}

        for Lift_entity in Lift_data:

            if Lift_entity.dxftype() == 'LWPOLYLINE':

                LiftPolygonID = Lift_entity.dxf.handle

                Lift_polygon = Polygon(np.array([lp[0:2] for lp in Lift_entity.get_points()]))

                vertices = tuple(Lift_entity.get_points())

                if vertices in unique_polygons:

                    ErrorLift_dict[LiftPolygonID] = str(
                        f"Lift Layer Found Duplicate Polygon Of {LiftPolygonID}.")

                else:

                    unique_polygons[vertices] = Lift_entity

                LiftPolygonContainsLabel = []

                for Lift_entity in Lift_data:

                    if Lift_entity.dxftype() == 'TEXT' or Lift_entity.dxftype() == 'MTEXT':

                        Lift_entity_text_properties = Lift_entity.dxfattribs()

                        Lift_Name = Lift_entity_text_properties.get('text') if Lift_entity.dxftype() == 'TEXT' else Lift_entity.plain_text()

                        Lift_text_pts = Lift_entity_text_properties.get('insert')

                        Lift_point = Point(np.array([Lift_text_pts[0], Lift_text_pts[1]]))

                        if Lift_polygon.contains(Lift_point) == True or Lift_polygon.touches(Lift_point) == True or round(Lift_polygon.distance(Lift_point), 1) == 0.0:

                            LiftPolygonContainsLabel.append([Lift_Name, Lift_polygon])

                if LiftPolygonContainsLabel == [] and len(LiftPolygonContainsLabel) == 0:

                    ErrorLift_dict[LiftPolygonID] = str(f'Warning- Lift Layer Polygon REF # ({LiftPolygonID}) Does Not Found Any Label')

                elif(len(LiftPolygonContainsLabel) > 1):

                    ErrorLift_dict[LiftPolygonID] = str(f'Warning- Lift Layer Polygon REF # ({LiftPolygonID}) Found More Than One Label')

        return ErrorLift_dict

    def Window_Layer(self, Window_data):

        ErrorWindow_dict = dict()

        unique_polygons={}

        for Window_entity in Window_data:

            if Window_entity.dxftype() == 'LWPOLYLINE':

                WindowPolygonID = Window_entity.dxf.handle

                if len([wp[0:2] for wp in Window_entity.get_points()])>3:

                    Window_polygon = Polygon(np.array([wp[0:2] for wp in Window_entity.get_points()]))

                    vertices = tuple(Window_entity.get_points())

                    if vertices in unique_polygons:

                        ErrorWindow_dict[WindowPolygonID] = str(f"Window Layer Found Duplicate Polygon Of {WindowPolygonID}.")

                    else:

                        unique_polygons[vertices] = Window_entity

                    WindowPolygonContainsLabel = []

                    for Window_entity in Window_data:

                        if Window_entity.dxftype() == 'TEXT' or Window_entity.dxftype() == 'MTEXT':

                            Window_entity_text_properties = Window_entity.dxfattribs()

                            Window_Name = Window_entity_text_properties.get('text') if Window_entity.dxftype() == 'TEXT' else Window_entity.plain_text()

                            Window_text_pts = Window_entity_text_properties.get('insert')

                            Window_point = Point(np.array([Window_text_pts[0], Window_text_pts[1]]))

                            if Window_polygon.contains(Window_point) == True or Window_polygon.touches(Window_point) == True or round(Window_polygon.distance(Window_point),1) == 0.0:

                                WindowPolygonContainsLabel.append([Window_Name, Window_polygon])

                    if WindowPolygonContainsLabel == [] and len(WindowPolygonContainsLabel) == 0:

                        ErrorWindow_dict[WindowPolygonID] = str(f'Warning- Window Layer Polygon REF # ({WindowPolygonID}) Does Not Found Any Label')

                    elif(len(WindowPolygonContainsLabel)>1):

                        ErrorWindow_dict[WindowPolygonID] = str(f'Warning- Window Layer Polygon REF # ({WindowPolygonID}) Found More Than One Label')

        return ErrorWindow_dict

    def Door_Layer(self,Door_data):

        ErrorDoor_dict = dict()

        unique_polygons={}

        for Door_entity in Door_data:

            if Door_entity.dxftype() == 'LWPOLYLINE':

                DoorPolygonID = Door_entity.dxf.handle

                Door_polygon = Polygon(np.array([dp[0:2] for dp in Door_entity.get_points()]))

                vertices = tuple(Door_entity.get_points())

                if vertices in unique_polygons:

                    ErrorDoor_dict[DoorPolygonID] = str(f"Door Layer Found Duplicate Polygon Of {DoorPolygonID}.")

                else:

                    unique_polygons[vertices] = Door_entity

                DoorPolygonContainsLabel = []

                for Door_entity in Door_data:

                    if Door_entity.dxftype() == 'TEXT' or Door_entity.dxftype() == 'MTEXT':

                        Door_entity_text_properties = Door_entity.dxfattribs()

                        Door_Name = Door_entity_text_properties.get('text') if Door_entity.dxftype() == 'TEXT' else Door_entity.plain_text()

                        Door_text_pts = Door_entity_text_properties.get('insert')

                        Door_point = Point(np.array([Door_text_pts[0], Door_text_pts[1]]))

                        if Door_polygon.contains(Door_point) == True or Door_polygon.touches(Door_point) == True or round(Door_polygon.distance(Door_point),1) ==0.0:

                            DoorPolygonContainsLabel.append([Door_Name,Door_polygon])

                if DoorPolygonContainsLabel == [] and len(DoorPolygonContainsLabel) == 0:

                    ErrorDoor_dict[DoorPolygonID] = str(f'Warning- Door Layer Polygon ({DoorPolygonID}) Does Not Found Any Label')

                elif(len(DoorPolygonContainsLabel) > 1):

                    ErrorDoor_dict[DoorPolygonID] = str(f'Warning- Door Layer Polygon ({DoorPolygonID}) Found More Than One Label')

        return ErrorDoor_dict

    def Room_Layer(self,Room_data):

        Room_dict = dict()

        ErrorRoom_dict = dict()

        unique_polygons={}

        for Room_entity in Room_data:

            if Room_entity.dxftype() == 'LWPOLYLINE':

                RoomPolygonID = Room_entity.dxf.handle

                Room_polygon = Polygon(np.array([rp[0:2] for rp in Room_entity.get_points()]))

                vertices = tuple(Room_entity.get_points())

                if vertices in unique_polygons:

                    ErrorRoom_dict[RoomPolygonID] = str(f"Room Layer Found Duplicate Polygon Of {RoomPolygonID}.")

                else:

                    unique_polygons[vertices] = Room_entity

                RoomPolygonContainsLabel = []

                for Room_entity in Room_data:

                    if Room_entity.dxftype() == 'TEXT' or Room_entity.dxftype() == 'MTEXT':

                        Room_entity_text_properties = Room_entity.dxfattribs()

                        Room_Name = Room_entity_text_properties.get('text') if Room_entity.dxftype() == 'TEXT' else Room_entity.plain_text()

                        Room_text_pts = Room_entity_text_properties.get('insert')

                        Room_point = Point(np.array([Room_text_pts[0], Room_text_pts[1]]))

                        if Room_polygon.contains(Room_point) == True or Room_polygon.touches(Room_point) == True or round(Room_polygon.distance(Room_point), 1) == 0.0:

                            RoomPolygonContainsLabel.append([Room_Name,Room_polygon])

                if RoomPolygonContainsLabel != [] and len(RoomPolygonContainsLabel) > 0:

                    for Roomnamepoly in RoomPolygonContainsLabel:

                        Room_dict[RoomPolygonID] = Roomnamepoly

                else:

                    ErrorRoom_dict[RoomPolygonID] = str(f'Warning- Room Layer Polygon REF # ({RoomPolygonID}) Does Not Found Any Label')

        return [ErrorRoom_dict,Room_dict]

    def GroundLevel_Layer(self, GroundLevel_data):

        GroundLevel_dict = dict()

        ErrorGroundLevel_dict = dict()

        unique_polygons={}

        for GroundLevel_entity in GroundLevel_data:

            if GroundLevel_entity.dxftype() == 'LWPOLYLINE':

                GroundLevelPolygonID = GroundLevel_entity.dxf.handle

                GroundLevel_polygon = LineString(np.array([glp[0:2] for glp in GroundLevel_entity.get_points()]))

                vertices = tuple(GroundLevel_entity.get_points())

                if vertices in unique_polygons:

                    ErrorGroundLevel_dict[GroundLevelPolygonID] = str(f"GroundLevel Layer Found Duplicate Polyline Of {GroundLevelPolygonID}.")

                else:

                    unique_polygons[vertices] = GroundLevel_entity

                GroundLevelPolygonContainsLabel = []

                for GroundLevel_entity in GroundLevel_data:

                    if GroundLevel_entity.dxftype() == 'TEXT' or GroundLevel_entity.dxftype() == 'MTEXT':

                        GroundLevel_entity_text_properties = GroundLevel_entity.dxfattribs()

                        GroundLevel_Name = GroundLevel_entity_text_properties.get('text') if GroundLevel_entity.dxftype() == 'TEXT' else GroundLevel_entity.plain_text()

                        GroundLevel_text_pts = GroundLevel_entity_text_properties.get('insert')

                        GroundLevel_point = Point(np.array([GroundLevel_text_pts[0], GroundLevel_text_pts[1]]))

                        if GroundLevel_polygon.touches(GroundLevel_point) == True or round(GroundLevel_polygon.distance(GroundLevel_point)) ==0:

                            GroundLevelPolygonContainsLabel.append([GroundLevel_Name, GroundLevel_polygon])

                if GroundLevelPolygonContainsLabel != [] and len(GroundLevelPolygonContainsLabel)<=1:

                    for GroundLevelnamepoly in GroundLevelPolygonContainsLabel:

                        GroundLevel_dict[GroundLevelPolygonID] = GroundLevelnamepoly

                elif(len(GroundLevelPolygonContainsLabel)>1):

                    ErrorGroundLevel_dict[GroundLevelPolygonID] = str(f'Warning- GroundLevel Layer Line REF # ({GroundLevelPolygonID}) Found More Than One Label')

                else:

                    ErrorGroundLevel_dict[GroundLevelPolygonID] = str(f'Warning- GroundLevel Layer Line REF # ({GroundLevelPolygonID}) Does Not Found Any Label')

        return [ErrorGroundLevel_dict,GroundLevel_dict]

    def FloorInSection_Layer(self,FloorInSection_data):

        FloorInSection_dict = dict()

        ErrorFloorInSection_dict = dict()

        unique_polygons={}

        for FloorInSection_entity in FloorInSection_data:

            if FloorInSection_entity.dxftype() == 'LWPOLYLINE':

                FloorInSectionPolygonID = FloorInSection_entity.dxf.handle

                FloorInSection_polygon = Polygon(np.array([fisp[0:2] for fisp in FloorInSection_entity.get_points()]))

                vertices = tuple(FloorInSection_entity.get_points())

                if vertices in unique_polygons:

                    ErrorFloorInSection_dict[FloorInSectionPolygonID] = str(f"FloorInSection Layer Found Duplicate Polygon Of {FloorInSectionPolygonID}.")

                else:

                    unique_polygons[vertices] = FloorInSectionPolygonID

                FloorInSectionPolygonContainsLabel = []

                for FloorInSection_entity in FloorInSection_data:

                    if FloorInSection_entity.dxftype() == 'TEXT' or FloorInSection_entity.dxftype() == 'MTEXT':

                        FloorInSection_entity_text_properties = FloorInSection_entity.dxfattribs()

                        FloorInSection_Name = FloorInSection_entity_text_properties.get('text') if FloorInSection_entity.dxftype() == 'TEXT' else FloorInSection_entity.plain_text()

                        FloorInSection_text_pts = FloorInSection_entity_text_properties.get('insert')

                        FloorInSection_point = Point(np.array([FloorInSection_text_pts[0], FloorInSection_text_pts[1]]))

                        if FloorInSection_polygon.contains(FloorInSection_point) == True or FloorInSection_polygon.touches(FloorInSection_point) == True or round(FloorInSection_polygon.distance(FloorInSection_point), 1) == 0.0:

                            FloorInSectionPolygonContainsLabel.append([FloorInSection_Name,FloorInSection_polygon])

                if FloorInSectionPolygonContainsLabel != [] and len(FloorInSectionPolygonContainsLabel) > 0:

                    for FloorInSectionnamepoly in FloorInSectionPolygonContainsLabel:

                        FloorInSection_dict[FloorInSectionPolygonID] = FloorInSectionnamepoly

                elif (FloorInSectionPolygonContainsLabel != [] and len(FloorInSectionPolygonContainsLabel) > 1):

                    ErrorFloorInSection_dict[FloorInSectionPolygonID] = str(f'Warning- FloorInSection Layer Polygon REF # ({FloorInSectionPolygonID}) Contain More than One Label')

                else:

                    ErrorFloorInSection_dict[FloorInSectionPolygonID] = str(f'Warning- FloorInSection Layer Polygon REF # ({FloorInSectionPolygonID}) Does Not Found Any Label')

        return [ErrorFloorInSection_dict,FloorInSection_dict]

    def PrintAdditionalDetails_Layer(self,PrintAdditionalDetails_data):

        ErrorPrintAdditionalDetails_dict = dict()

        unique_polygons={}

        for PrintAdditionalDetails_entity in PrintAdditionalDetails_data:

            if PrintAdditionalDetails_entity.dxftype() == 'LWPOLYLINE':

                PrintAdditionalDetailsPolygonID = PrintAdditionalDetails_entity.dxf.handle

                PrintAdditionalDetails_polygon = Polygon(np.array([padp[0:2] for padp in PrintAdditionalDetails_entity.get_points()]))

                vertices = tuple(PrintAdditionalDetails_entity.get_points())

                if vertices in unique_polygons:

                    ErrorPrintAdditionalDetails_dict[PrintAdditionalDetailsPolygonID] = str(f"PrintAdditionalDetails Layer Found Duplicate Polygon Of {PrintAdditionalDetailsPolygonID}.")

                else:

                    unique_polygons[vertices] = PrintAdditionalDetailsPolygonID

                PrintAdditionalDetailsPolygonContainsLabel = []

                for PrintAdditionalDetails_entity in PrintAdditionalDetails_data:

                    if PrintAdditionalDetails_entity.dxftype() == 'TEXT' or PrintAdditionalDetails_entity.dxftype() == 'MTEXT':

                        PrintAdditionalDetails_entity_text_properties = PrintAdditionalDetails_entity.dxfattribs()

                        PrintAdditionalDetails_Name = PrintAdditionalDetails_entity_text_properties.get('text') if PrintAdditionalDetails_entity.dxftype() == 'TEXT' else PrintAdditionalDetails_entity.plain_text()

                        PrintAdditionalDetails_text_pts = PrintAdditionalDetails_entity_text_properties.get('insert')

                        PrintAdditionalDetails_point = Point(np.array([PrintAdditionalDetails_text_pts[0], PrintAdditionalDetails_text_pts[1]]))

                        if PrintAdditionalDetails_polygon.contains(PrintAdditionalDetails_point) == True or PrintAdditionalDetails_polygon.touches(PrintAdditionalDetails_point) == True or round(PrintAdditionalDetails_polygon.distance(PrintAdditionalDetails_point), 1) == 0.0:

                            PrintAdditionalDetailsPolygonContainsLabel.append([PrintAdditionalDetails_Name,PrintAdditionalDetails_polygon])

                if PrintAdditionalDetailsPolygonContainsLabel == [] and len(PrintAdditionalDetailsPolygonContainsLabel) == 0:

                    ErrorPrintAdditionalDetails_dict[PrintAdditionalDetailsPolygonID] = str(f'Warning- PrintAdditionalDetails Layer Polygon REF # ({PrintAdditionalDetailsPolygonID}) Does Not Found Any Label')

        return ErrorPrintAdditionalDetails_dict

    def WallCompound_Layer(self,WallCompound_data):

        ErrorWallCompound_dict = dict()

        WallCompound_dict = dict()

        unique_polygons={}

        for WallCompound_entity in WallCompound_data:

            if WallCompound_entity.dxftype() == 'LWPOLYLINE':

                WallCompound_properties=WallCompound_entity.dxfattribs()

                if WallCompound_properties.get('linetype')!='CENTER':

                    wallcompoundPolygonID = WallCompound_entity.dxf.handle

                    if len([wc[0:2] for wc in WallCompound_entity.get_points()])>3:

                        wallcompound_polygon = Polygon(np.array([wc[0:2] for wc in WallCompound_entity.get_points()]))

                        vertices = tuple(WallCompound_entity.get_points())

                        if vertices in unique_polygons:

                            ErrorWallCompound_dict[wallcompoundPolygonID] = str(f"WallCompound Layer Found Duplicate Polygon Of {wallcompoundPolygonID}.")

                        else:

                            unique_polygons[vertices] = WallCompound_entity

                        wallcompoundPolygonContainsLabel = []

                        for wallcompound_entity in WallCompound_data:

                            if wallcompound_entity.dxftype() == 'TEXT' or wallcompound_entity.dxftype() == 'MTEXT':

                                wallcompound_text_properties = wallcompound_entity.dxfattribs()

                                wallcompound_Name = wallcompound_text_properties.get('text') if wallcompound_entity.dxftype() == 'TEXT' else wallcompound_entity.plain_text()

                                wallcompound_text_pts = wallcompound_text_properties.get('insert')

                                wallcompound_point = Point(np.array([wallcompound_text_pts[0], wallcompound_text_pts[1]]))

                                if wallcompound_polygon.contains(wallcompound_point) == True or wallcompound_polygon.touches(wallcompound_point) == True or round(wallcompound_polygon.distance(wallcompound_point), 1) == 0.0:

                                    wallcompoundPolygonContainsLabel.append([wallcompound_Name,wallcompound_polygon])

                        ErrorBothNameANDCenterLineResponce = []

                        if wallcompoundPolygonContainsLabel != [] and len(wallcompoundPolygonContainsLabel)<=1:

                            for wallcompoundnamepoly in wallcompoundPolygonContainsLabel:

                                WallCompound_dict[wallcompoundPolygonID]=wallcompoundnamepoly

                        elif(len(wallcompoundPolygonContainsLabel)>1):

                            ErrorBothNameANDCenterLineResponce.append(str(f'Warning- WallCompound Layer Polygon REF # ({wallcompoundPolygonID}) Found More Than One Label'))

                        else:

                            ErrorBothNameANDCenterLineResponce.append(str(f'Warning- WallCompound Layer Polygon REF # ({wallcompoundPolygonID}) Does Not Found Any Label'))

                        wallcompoundPolygonContainsCenterline=[]

                        for wallcompound_entity in WallCompound_data:

                            if wallcompound_entity.dxftype()=='LWPOLYLINE':

                                wallcompound_properties=wallcompound_entity.dxfattribs()

                                if wallcompound_properties.get('linetype')=='CENTER':

                                    wallCompoundCenterLinePoints=LineString(np.array([wccl[0:2] for wccl in wallcompound_entity.get_points()]))
                                    if all(wallcompound_polygon.touches(Point(point)) or wallcompound_polygon.contains(Point(point)) or round(wallcompound_polygon.distance(Point(point)),1) == 0.0 for point in wallCompoundCenterLinePoints.coords) == True:
                                    #if wallcompound_polygon.contains(wallCompoundCenterLinePoints) == True or wallcompound_polygon.touches(wallCompoundCenterLinePoints) == True or round(wallcompound_polygon.distance(wallCompoundCenterLinePoints), 1) == 0.0:

                                        wallcompoundPolygonContainsCenterline.append(wallCompoundCenterLinePoints)

                        if wallcompoundPolygonContainsCenterline==[] and len(wallcompoundPolygonContainsCenterline)==0:

                            ErrorBothNameANDCenterLineResponce.append(str(f'Warning- WallCompound Layer Polygon REF # ({wallcompoundPolygonID}) Does Not Found Any CenterLine'))

                        elif(len(wallcompoundPolygonContainsCenterline)>1):

                            ErrorBothNameANDCenterLineResponce.append(
                                str(f'Warning- WallCompound Layer Polygon REF # ({wallcompoundPolygonID}) Found More Than One CenterLine'))

                        ErrorWallCompound_dict[wallcompoundPolygonID] = ErrorBothNameANDCenterLineResponce

        return [ErrorWallCompound_dict,WallCompound_dict]

    def Margin_Layer(self,Margin_data):

        Errormargin_dict={}

        tot_Front_SideColor = []

        tot_Rear_SideColor = []

        tot_Side1_Color = []

        tot_Side2_Color = []

        for margin_entity in Margin_data:

            if margin_entity.dxftype()=='INSERT':

                front_side=[]

                rear_side=[]

                side1=[]

                side2=[]

                for vir_entity in margin_entity.virtual_entities():

                    if vir_entity.dxftype()=='LINE':

                        if vir_entity.dxf.color==1:

                            front_side.append(vir_entity.dxf.color)

                        elif(vir_entity.dxf.color==6):

                            rear_side.append(vir_entity.dxf.color)

                        elif (vir_entity.dxf.color == 5):

                            side1.append(vir_entity.dxf.color)

                        elif(vir_entity.dxf.color == 104 or vir_entity.dxf.color == 3):

                            side2.append(vir_entity.dxf.color)

                    elif(vir_entity.dxftype()=='ARC'):

                        if vir_entity.dxf.color==1:

                            front_side.append(vir_entity.dxf.color)

                        elif(vir_entity.dxf.color==6):

                            rear_side.append(vir_entity.dxf.color)

                        elif (vir_entity.dxf.color == 5):

                            side1.append(vir_entity.dxf.color)

                        elif(vir_entity.dxf.color == 104 or vir_entity.dxf.color == 3):

                            side2.append(vir_entity.dxf.color)

                if front_side!=[] and  len(front_side)>0:

                    for front_color in front_side:

                        tot_Front_SideColor.append(front_color)

                if rear_side != [] and len(rear_side) > 0:

                    for rear_color in rear_side:

                        tot_Rear_SideColor.append(rear_color)

                if side1 != [] and len(side1) > 0:

                    for side1_color in side1:

                        tot_Side1_Color.append(side1_color)

                if side2 != [] and len(side2) > 0:

                    for side2_color in side2:

                        tot_Side2_Color.append(side2_color)

            elif(margin_entity.dxftype()=='LINE'):

                if (margin_entity.dxf.color==1):

                    tot_Front_SideColor.append(margin_entity.dxf.color)

                elif(margin_entity.dxf.color == 6):

                    tot_Rear_SideColor.append(margin_entity.dxf.color)

                elif (margin_entity.dxf.color == 5):

                    tot_Side1_Color.append(margin_entity.dxf.color)

                elif (margin_entity.dxf.color == 104 or margin_entity.dxf.color == 3):

                    tot_Side2_Color.append(margin_entity.dxf.color)

        if tot_Front_SideColor==[] and len(tot_Front_SideColor)==0:

            Errormargin_dict['FRONT']=str(f'Warning- Margin Layer Polygon does Not Get Red Color For Front Side')

        if tot_Rear_SideColor == [] and len(tot_Rear_SideColor)==0:

            Errormargin_dict['REAR'] = str(f'Warning- Margin Layer Polygon does Not Get Pink Color For Rear Side')

        if tot_Side1_Color == [] and len(tot_Side1_Color)==0:

            Errormargin_dict['SIDE1'] = str(f'Warning- Margin Layer Polygon does Not Get Blue Color For Side1')

        if tot_Side2_Color == [] and len(tot_Side2_Color)==0:

            Errormargin_dict['SIDE2'] = str(f'Warning- Margin Layer Polygon does Not Get Green Color For Side2')

        return Errormargin_dict

    def PlotAbuttingDetails_Layer(self,PlotAbuttingDetails_data):

        Errorplotabutting_dict=dict()

        unique_polygons={}

        for plotabutting_entity in PlotAbuttingDetails_data:

            if plotabutting_entity.dxftype() == 'LWPOLYLINE':

                plotabuttingPolygonID = plotabutting_entity.dxf.handle

                plotabutting_polygon = Polygon(np.array([pad[0:2] for pad in plotabutting_entity.get_points()]))

                vertices = tuple(plotabutting_entity.get_points())

                if vertices in unique_polygons:

                    Errorplotabutting_dict[plotabuttingPolygonID] = str(f"PlotAbuttingDetails Layer Found Duplicate Polygon Of {plotabuttingPolygonID}.")

                else:

                    unique_polygons[vertices] = plotabutting_entity

                plotabuttingPolygonContainsLabel = []

                for plotabutting_entity in PlotAbuttingDetails_data:

                    if plotabutting_entity.dxftype() == 'TEXT' or plotabutting_entity.dxftype() == 'MTEXT':

                        plotabutting_entity_text_properties = plotabutting_entity.dxfattribs()

                        plotabutting_Name = plotabutting_entity_text_properties.get('text') if plotabutting_entity.dxftype() == 'TEXT' else plotabutting_entity.plain_text()

                        plotabutting_text_pts = plotabutting_entity_text_properties.get('insert')

                        plotabutting_point = Point(np.array([plotabutting_text_pts[0], plotabutting_text_pts[1]]))

                        if plotabutting_polygon.contains(plotabutting_point) == True or plotabutting_polygon.touches(plotabutting_point) == True or round(plotabutting_polygon.distance(plotabutting_point), 1) == 0.0:

                            plotabuttingPolygonContainsLabel.append([plotabutting_Name,plotabutting_polygon])

                if plotabuttingPolygonContainsLabel == [] and len(plotabuttingPolygonContainsLabel) == 0:

                    Errorplotabutting_dict[plotabuttingPolygonID] = str(f'Warning- PlotAbuttingDetails layer Polygon REF # ({plotabuttingPolygonID}) Does Not Found Any Label')

        return Errorplotabutting_dict

    def MainRoad_Layer(self,MainRoad_data):

        mainroad_dict = dict()

        Errormainroad_dict = dict()

        unique_polygons={}

        for mainroad_entity in MainRoad_data:

            if mainroad_entity.dxftype() == 'LWPOLYLINE':

                mainroadPolygonID = mainroad_entity.dxf.handle

                mainroad_polygon = Polygon(np.array([mrp[0:2] for mrp in mainroad_entity.get_points()]))

                vertices = tuple(mainroad_entity.get_points())

                if vertices in unique_polygons:

                    Errormainroad_dict[mainroadPolygonID] = str(f"MainRoad Layer Found Duplicate Polygon Of {mainroadPolygonID}.")

                else:

                    unique_polygons[vertices] = mainroad_entity

                mainroadPolygonContainsLabel = []

                for mainroad_entity in MainRoad_data:

                    if mainroad_entity.dxftype() == 'TEXT' or mainroad_entity.dxftype() == 'MTEXT':

                        mainroad_entity_text_properties = mainroad_entity.dxfattribs()

                        mainroad_Name = mainroad_entity_text_properties.get('text') if mainroad_entity.dxftype() == 'TEXT' else mainroad_entity.plain_text()

                        mainroad_text_pts = mainroad_entity_text_properties.get('insert')

                        mainroad_point = Point(np.array([mainroad_text_pts[0], mainroad_text_pts[1]]))

                        if mainroad_polygon.contains(mainroad_point) == True or mainroad_polygon.touches(mainroad_point) == True or round(mainroad_polygon.distance(mainroad_point), 1) == 0.0:

                            mainroadPolygonContainsLabel.append([mainroad_Name,mainroad_polygon])

                if mainroadPolygonContainsLabel != [] and len(mainroadPolygonContainsLabel)<=1:

                    for mainroadnamepoly in mainroadPolygonContainsLabel:

                        mainroad_dict[mainroadPolygonID] = mainroadnamepoly

                elif(len(mainroadPolygonContainsLabel)>1):

                    Errormainroad_dict[mainroadPolygonID] = str(
                        f'Warning- MainRoad Layer Polygon REF # ({mainroadPolygonID}) Found More Than One Label')

                else:

                    Errormainroad_dict[mainroadPolygonID] = str(f'Warning- MainRoad Layer Polygon REF # ({mainroadPolygonID}) Does Not Found Any Label')

        return [Errormainroad_dict,mainroad_dict]

    def AccessoryUse_Layer(self,AccessoryUse_data):

        Erroraccessoryuse_dict = dict()

        unique_polygons={}

        for accessory_entity in AccessoryUse_data:

            if accessory_entity.dxftype() == 'LWPOLYLINE':

                accessoryPolygonID = accessory_entity.dxf.handle

                accessory_polygon = Polygon(np.array([ace[0:2] for ace in accessory_entity.get_points()]))

                vertices = tuple(accessory_entity.get_points())

                if vertices in unique_polygons:

                    Erroraccessoryuse_dict[accessoryPolygonID] = str(f"AccessoryUse Layer Found Duplicate Polygon Of {accessoryPolygonID}.")

                else:

                    unique_polygons[vertices] = accessory_entity

                accessoryPolygonContainsLabel = []

                for accessory_entity in AccessoryUse_data:

                    if accessory_entity.dxftype() == 'TEXT' or accessory_entity.dxftype() == 'MTEXT':

                        accessory_text_properties = accessory_entity.dxfattribs()

                        accessory_Name = accessory_text_properties.get('text') if accessory_entity.dxftype() == 'TEXT' else accessory_entity.plain_text()

                        accessory_text_pts = accessory_text_properties.get('insert')

                        accessory_point = Point(np.array([accessory_text_pts[0], accessory_text_pts[1]]))

                        if accessory_polygon.contains(accessory_point) == True or accessory_polygon.touches(accessory_point) == True or round(accessory_polygon.distance(accessory_point), 1) == 0.0:

                            accessoryPolygonContainsLabel.append([accessory_Name, accessory_polygon])

                if accessoryPolygonContainsLabel == [] and len(accessoryPolygonContainsLabel) == 0:

                    Erroraccessoryuse_dict[accessoryPolygonID] = str(f'Warning- AccessoryUse Layer Polygon REF # ({accessoryPolygonID}) Does Not Found Any Label')

                elif(len(accessoryPolygonContainsLabel) > 1):

                    Erroraccessoryuse_dict[accessoryPolygonID] = str(
                        f'Warning- AccessoryUse Layer Polygon REF # ({accessoryPolygonID}) Found More Than One Label')

        return Erroraccessoryuse_dict

    def OrganizedOpenSpace_Layer(self,OrganizedOpenSpace_data):

        organizedOpenspace_dict = dict()

        ErrororganizedOpenspace_dict = dict()

        unique_polygons={}

        for org_entity in OrganizedOpenSpace_data:

            if org_entity.dxftype() == 'LWPOLYLINE':

                orgPolygonID = org_entity.dxf.handle

                org_polygon = Polygon(np.array([org[0:2] for org in org_entity.get_points()]))

                vertices = tuple(org_entity.get_points())

                if vertices in unique_polygons:

                    ErrororganizedOpenspace_dict[orgPolygonID] = str(f" Organized OpenSpace Layer Found Duplicate Polygon Of {orgPolygonID}.")

                else:

                    unique_polygons[vertices] = org_entity

                orgPolygonContainsLabel = []

                for org_entity in OrganizedOpenSpace_data:

                    if org_entity.dxftype() == 'TEXT' or org_entity.dxftype() == 'MTEXT':

                        org_text_properties = org_entity.dxfattribs()

                        org_Name = org_text_properties.get('text') if org_entity.dxftype() == 'TEXT' else org_entity.plain_text()

                        org_text_pts = org_text_properties.get('insert')

                        org_point = Point(np.array([org_text_pts[0], org_text_pts[1]]))

                        if org_polygon.contains(org_point) == True or org_polygon.touches(org_point) == True or round(org_polygon.distance(org_point), 1) == 0.0:

                            orgPolygonContainsLabel.append([org_Name, org_polygon])

                if orgPolygonContainsLabel != [] and len(orgPolygonContainsLabel) <= 1:

                    for orgnampoly in orgPolygonContainsLabel:

                        organizedOpenspace_dict[orgPolygonID] = orgnampoly

                elif(len(orgPolygonContainsLabel) > 1):

                    ErrororganizedOpenspace_dict[orgPolygonID] = str(f'Warning- OrganizedOpenSpace Layer Polygon REF # ({orgPolygonID}) Found More Than One Label')

                else:

                    ErrororganizedOpenspace_dict[orgPolygonID] = str(f'Warning- OrganizedOpenSpace Layer Polygon REF # ({orgPolygonID}) Does Not Found Any Label')

        return [ErrororganizedOpenspace_dict,organizedOpenspace_dict]

    def Plot_Layer(self,Plot_Data):

        plot_dict=dict()

        Errorplot_dict=dict()

        unique_polygons={}

        for Plot_entity in Plot_Data:

            if Plot_entity.dxftype()=='LWPOLYLINE':

                plotPolygonID=Plot_entity.dxf.handle

                plot_polygon=Polygon(np.array([pp[0:2] for pp in Plot_entity.get_points()]))

                vertices = tuple(Plot_entity.get_points())

                if vertices in unique_polygons:

                    Errorplot_dict[plotPolygonID] = str(f" Plot Layer Found Duplicate Polygon Of {plotPolygonID}.")

                else:

                    unique_polygons[vertices] = Plot_entity

                plotPolygonContainsLabel=[]

                for Plot_entity in Plot_Data:

                    if Plot_entity.dxftype()=='TEXT' or Plot_entity.dxftype()=='MTEXT':

                        plot_text_properties=Plot_entity.dxfattribs()

                        plot_Name=plot_text_properties.get('text') if Plot_entity.dxftype()=='TEXT' else Plot_entity.plain_text()

                        plot_text_pts=plot_text_properties.get('insert')

                        plot_point=Point(np.array([plot_text_pts[0],plot_text_pts[1]]))

                        if plot_polygon.contains(plot_point)==True or plot_polygon.touches(plot_point)==True or round(plot_polygon.distance(plot_point),1)==0.0:

                            plotPolygonContainsLabel.append([plot_Name,plot_polygon])

                if plotPolygonContainsLabel!=[] and len(plotPolygonContainsLabel)<=1:

                    for plotnampoly in plotPolygonContainsLabel:

                        plot_dict[plotPolygonID]=plotnampoly

                elif(len(plotPolygonContainsLabel)>1):

                    Errorplot_dict[plotPolygonID] = str(f'Warning- Plot Layer Polygon REF # ({plotPolygonID}) Found More Than One Label')

                else:

                    Errorplot_dict[plotPolygonID] =str(f'Warning- Plot Layer Polygon REF # ({plotPolygonID}) Does Not Found Any Label')

        return [Errorplot_dict,plot_dict]

    def ProposedWork_Layer(self,ProposedWork_Data):

        propwork_dict=dict()

        Errorpropwork_dict=dict()

        unique_polygons={}

        for propwork_entity in ProposedWork_Data:

            if propwork_entity.dxftype()=='LWPOLYLINE':

                propworkPolygonID=propwork_entity.dxf.handle

                propwork_polygon=Polygon(np.array([pw[0:2] for pw in propwork_entity.get_points()]))

                vertices = tuple(propwork_entity.get_points())

                if vertices in unique_polygons:

                    Errorpropwork_dict[propworkPolygonID] = str(f"ProposedWork Layer Found Duplicate Polygon Of {propworkPolygonID}.")

                else:

                    unique_polygons[vertices] = propwork_entity

                propworkPolygonContainsLabel=[]

                for propwork_entity in ProposedWork_Data:

                    if propwork_entity.dxftype()=='TEXT' or propwork_entity.dxftype()=='MTEXT':

                        propwork_text_properties=propwork_entity.dxfattribs()

                        propwork_Name=propwork_text_properties.get('text') if propwork_entity.dxftype()=='TEXT' else propwork_entity.plain_text()

                        propwork_text_pts=propwork_text_properties.get('insert')

                        plot_point=Point(np.array([propwork_text_pts[0],propwork_text_pts[1]]))

                        if propwork_polygon.contains(plot_point)==True or propwork_polygon.touches(plot_point)==True or round(propwork_polygon.distance(plot_point),1)==0.0:

                            propworkPolygonContainsLabel.append([propwork_Name,propwork_polygon])

                if propworkPolygonContainsLabel!=[] and len(propworkPolygonContainsLabel)<=1:

                    for plotnampoly in propworkPolygonContainsLabel:

                        propwork_dict[propworkPolygonID]=plotnampoly

                elif(len(propworkPolygonContainsLabel)>1):

                    Errorpropwork_dict[propworkPolygonID] = str(f'Warning- ProposedWork Layer Polygon REF # ({propworkPolygonID}) Found More Than One Label')

                else:

                    Errorpropwork_dict[propworkPolygonID] =str(f'Warning- ProposedWork Layer Polygon REF # ({propworkPolygonID}) Does Not Found Any Label')

        return [Errorpropwork_dict,propwork_dict]

    def BuildingName_Layer(self,Building_Data):

        building_dict=dict()

        Errorbuilding_dict=dict()

        unique_polygons = {}

        for Building_entity in Building_Data:

            if Building_entity.dxftype()=='LWPOLYLINE':

                buildingPolygonID = Building_entity.dxf.handle

                building_polygon = Polygon(np.array([bp[0:2] for bp in Building_entity.get_points()]))

                vertices = tuple(Building_entity.get_points())

                if vertices in unique_polygons:

                    Errorbuilding_dict[buildingPolygonID]=str(f"Building Layer Found Duplicate Polygon Of {buildingPolygonID}.")

                else:

                    unique_polygons[vertices] = Building_entity

                BPolygonContainsLabel=[]

                for Building_entity in Building_Data:

                    if Building_entity.dxftype()=='TEXT' or Building_entity.dxftype()=='MTEXT':

                        building_text_properties=Building_entity.dxfattribs()
                        #print(building_text_properties)
                        Building_Name=building_text_properties.get('text') if Building_entity.dxftype()=='TEXT' else Building_entity.plain_text()

                        building_text_pts=building_text_properties.get('insert')

                        building_point=Point(np.array([building_text_pts[0],building_text_pts[1]]))

                        if building_polygon.contains(building_point)==True or building_polygon.touches(building_point)==True or round(building_polygon.distance(building_point),1)==0.0:

                            BPolygonContainsLabel.append([Building_Name,building_polygon])

                if BPolygonContainsLabel!=[] and len(BPolygonContainsLabel)<=1:

                    for buildingnampoly in BPolygonContainsLabel:

                        building_dict[buildingPolygonID]=buildingnampoly

                elif(len(BPolygonContainsLabel)>1):
                    #print(BPolygonContainsLabel)
                    Errorbuilding_dict[buildingPolygonID] = str(f'Warning- Building Layer Polygon REF # {buildingPolygonID} Found More Than One Label')

                else:

                    Errorbuilding_dict[buildingPolygonID] =str(f'Warning- Building Layer Polygon REF # {buildingPolygonID} Does Not Found Any Label')

        return [Errorbuilding_dict,building_dict]

    def FloorDIRREFCircle(self,Floor_Data):

        floorDirRefCircle_dict=dict()

        ErrorfloorDirRefCircle_dict=dict()

        for floor_entity in Floor_Data:

            floorDirRefCircle_Id=floor_entity.dxf.handle

            if floor_entity.dxftype()=='INSERT':

                floorrefcircle=[floor_vir_entity for floor_vir_entity in floor_entity.virtual_entities() if floor_vir_entity.dxftype()=='CIRCLE']

                center_point=Point([floorrefcircle[0].dxf.center[0],floorrefcircle[0].dxf.center[1]])

                floorDirRefCircle_dict[floorDirRefCircle_Id]=center_point

        if floorDirRefCircle_dict=={} and len(floorDirRefCircle_dict)==0:

            ErrorMsg=f'Warning- Did Not Get Any Direction Reference Circle From Floor Layer.'

            ErrorfloorDirRefCircle_dict['Error Msg']=ErrorMsg

        return [ErrorfloorDirRefCircle_dict,floorDirRefCircle_dict]

    def ResiBUADIRREFCircle(self, ResiBUA_Data):

        ResiBUADirRefCircle_dict = dict()

        ErrorResiBUADirRefCircle_dict = dict()

        for ResiBUA_entity in ResiBUA_Data:

            ResiBUADirRefCircle_Id = ResiBUA_entity.dxf.handle

            if ResiBUA_entity.dxftype() == 'INSERT':

                ResiBUArefcircle = [ResiBUA_vir_entity for ResiBUA_vir_entity in ResiBUA_entity.virtual_entities() if ResiBUA_vir_entity.dxftype() == 'CIRCLE']

                center_point = Point([ResiBUArefcircle[0].dxf.center[0], ResiBUArefcircle[0].dxf.center[1]])

                ResiBUADirRefCircle_dict[ResiBUADirRefCircle_Id] = center_point

        if ResiBUADirRefCircle_dict == {} and len(ResiBUADirRefCircle_dict) == 0:

            ErrorMsg = f'Warning- Did Not Get Any Direction Reference Circle From ResiBUA Layer.'

            ErrorResiBUADirRefCircle_dict['Error Msg'] = ErrorMsg

        return [ErrorResiBUADirRefCircle_dict, ResiBUADirRefCircle_dict]

    def Floor_Layer(self,Floor_Data):

        floor_dict=dict()

        Errorfloor_dict=dict()

        unique_polygons={}

        for Floor_entity in Floor_Data:

            if Floor_entity.dxftype()=='LWPOLYLINE':

                floorPolygonID=Floor_entity.dxf.handle

                floor_polygon=Polygon(np.array([fp[0:2] for fp in Floor_entity.get_points()]))

                vertices = tuple(Floor_entity.get_points())

                if vertices in unique_polygons:

                    Errorfloor_dict[floorPolygonID] = str(f"Floor Layer Found Duplicate Polygon Of {floorPolygonID}.")

                else:

                    unique_polygons[vertices] = Floor_entity

                FPolygonContainsLabel=[]

                for Floor_entity in Floor_Data:

                    if Floor_entity.dxftype()=='TEXT' or Floor_entity.dxftype()=='MTEXT':

                        floor_text_properties=Floor_entity.dxfattribs()

                        Floor_Name=floor_text_properties.get('text') if Floor_entity.dxftype()=='TEXT' else Floor_entity.plain_text()

                        floor_text_pts=floor_text_properties.get('insert')

                        floor_point=Point(np.array([floor_text_pts[0],floor_text_pts[1]]))

                        if floor_polygon.contains(floor_point)==True or floor_polygon.touches(floor_point)==True or round(floor_polygon.distance(floor_point),1)==0.0:

                            FPolygonContainsLabel.append([Floor_Name,floor_polygon])

                if FPolygonContainsLabel!=[] and len(FPolygonContainsLabel)<=1:

                    for floornampoly in FPolygonContainsLabel:

                        floor_dict[floorPolygonID]=floornampoly

                elif(len(FPolygonContainsLabel)>1):

                    Errorfloor_dict[floorPolygonID] = str(f'Warning- Floor Layer Polygon REF # ({floorPolygonID}) Found More Than One Label')

                else:

                    Errorfloor_dict[floorPolygonID] =str(f'Warning- Floor Layer Polygon REF # ({floorPolygonID}) Does Not Found Any Label')

        return [Errorfloor_dict,floor_dict]

    def performLayerChecks(self,msp):

        ErrorMessageList=[]

        try:

            if (msp is None):

                msg = 'Unable to check LayerChecks. Required input parameter is missing.'

                print(msg)

                ErrorMessageList.append(msg)

                return ErrorMessageList

            Building_data=msp.query("*[layer=='_BuildingName']")

            Floor_data = msp.query("*[layer=='_Floor']")

            Plot_data=msp.query("*[layer=='_Plot']")

            ProposedWork_data=msp.query("*[layer=='_ProposedWork']")

            OrganizedOpenSpace_data = msp.query("*[layer=='_OrganizedOpenSpace']")

            AccessoryUse_data = msp.query("*[layer=='_AccessoryUse']")

            MainRoad_data = msp.query("*[layer=='_MainRoad']")

            PlotAbuttingDetails_data=msp.query("*[layer=='_PlotAbuttingDetails']")

            Margin_data=msp.query("*[layer=='_MarginLine']")

            WallCompound_data=msp.query("*[layer=='_CompoundWall']")

            PrintAdditionalDetails_data = msp.query("*[layer=='_PrintAdditionalDetails']")

            FloorInSection_data=msp.query("*[layer=='_FloorInSection']")

            GroundLevel_data=msp.query("*[layer=='_GroundLevel']")

            Room_data = msp.query("*[layer=='_Room']")

            Door_data = msp.query("*[layer=='_Door']")

            Window_data = msp.query("*[layer=='_Window']")

            Lift_data = msp.query("*[layer=='_Lift']")

            MortgageArea_data = msp.query("*[layer=='_MortgageArea']")

            Balcony_data = msp.query("*[layer=='_Balcony']")

            StairCase_data=msp.query("*[layer=='_StairCase']")

            Parking_data=msp.query("*[layer=='_Parking']")

            SlabCutOutVoid_data = msp.query("*[layer=='_SlabCutoutVoid']")

            Passage_data = msp.query("*[layer=='_Passage']")

            Ramp_data = msp.query("*[layer=='_Ramp']")

            Section_data=msp.query("*[layer=='_Section']")

            Netplot_data = msp.query("*[layer=='_NetPlot']")

            Roadwidening_data = msp.query("*[layer=='_RoadWidening']")

            CarpetArea_data = msp.query("*[layer=='_CarpetArea']")

            RefugeArea_data = msp.query("*[layer=='_RefugeArea']")

            Driveway_data=msp.query("*[layer=='_Driveway']")

            Terrace_data = msp.query("*[layer=='_Terrace']")

            ResiBuaOutline_data = msp.query("*[layer=='_ResiBUAOutline']")

            CommBuaOutline_data = msp.query("*[layer=='_CommBUAOutline']")

            IndivBUAOutline_data=msp.query("*[layer=='_IndBUAOutline']")

            SpecialBUAOutline_data = msp.query("*[layer=='_SpecialBUAOutline']")

            BuildingName_LayerList=self.BuildingName_Layer(Building_data)

            Floor_LayerList = self.Floor_Layer(Floor_data)

            RefugeArea_LayerList=self.RefugeArea_Layer(RefugeArea_data)

            Plot_LayerList=self.Plot_Layer(Plot_data)

            ProposedWork_LayerList=self.ProposedWork_Layer(ProposedWork_data)

            OrganizedOpenSpace_LayerList=self.OrganizedOpenSpace_Layer(OrganizedOpenSpace_data)

            AccessoryUse_LayerList=self.AccessoryUse_Layer(AccessoryUse_data)

            MainRoad_LayerList=self.MainRoad_Layer(MainRoad_data)

            PlotAbuttingDetails_LayerList=self.PlotAbuttingDetails_Layer(PlotAbuttingDetails_data)

            Margin_LayerDict=self.Margin_Layer(Margin_data)

            WallCompound_LayerList=self.WallCompound_Layer(WallCompound_data)

            PrintAdditionalDetails_LayerList=self.PrintAdditionalDetails_Layer(PrintAdditionalDetails_data)

            FloorInSection_LayerList=self.FloorInSection_Layer(FloorInSection_data)

            GroundLevel_LayerList=self.GroundLevel_Layer(GroundLevel_data)

            Room_LayerList=self.Room_Layer(Room_data)

            Door_LayerList=self.Door_Layer(Door_data)

            Window_LayerList=self.Window_Layer(Window_data)

            Lift_LayerList=self.Lift_Layer(Lift_data)

            MortgageArea_LayerList=self.MortgageArea_Layer(MortgageArea_data)

            Balcony_LayerList=self.Balcony_Layer(Balcony_data)

            NetPlot_LayerList=self.NetPlot_Layer(Netplot_data)

            RoadWidening_LayerList = self.RoadWidening_Layer(Roadwidening_data)

            StairCase_LayerList=self.StairCase_Layer(StairCase_data)

            Parking_LayerList=self.Parking_Layer(Parking_data)

            SlabCutOutVoid_LayerList=self.SlabCutOutVoid_Layer(SlabCutOutVoid_data)

            Passage_LayerList=self.Passage_Layer(Passage_data)

            Ramp_LayerList=self.Ramp_Layer(Ramp_data)

            Section_LayerList=self.Section_Layer(Section_data)

            CarpetArea_LayerList=self.CarpetArea_Layer(CarpetArea_data)

            Driveway_LayerList=self.Driveway_Layer(Driveway_data)

            Terrace_LayerList=self.Terrace_Layer(Terrace_data)

            ResiBuaOutline_LayerDict=self.ResiBuaOutLine_Layer(ResiBuaOutline_data)

            CommBuaOutline_LayerDict = self.CommBuaOutLine_Layer(CommBuaOutline_data)

            IndBuaOutLine_LayerDict=self.IndBuaOutLine_Layer(IndivBUAOutline_data)

            SpecialBuaOutLine_LayerDict = self.SpecialBuaOutLine_Layer(SpecialBUAOutline_data)

            BuildingContainsFloorList=self.BuildingContainsFloor(BuildingName_LayerList[1],Floor_LayerList[1])

            BuildingContainsSectionList = self.BuildingContainsSectionLayer(BuildingName_LayerList[1], Section_LayerList[1])

            BuildingORSectionContainsFloorInSection=self.SectionContainsFloorINSection(BuildingName_LayerList[1],Section_LayerList[1],FloorInSection_LayerList[1])

            BuildingORContainsGroundlevelLine=self.SectionContainsGroundLine(BuildingName_LayerList[1],Section_LayerList[1],GroundLevel_LayerList[1])

            floorDIRREFCircle=self.FloorDIRREFCircle(Floor_data)

            ResiBUADIRREFCircle = self.ResiBUADIRREFCircle(ResiBuaOutline_data)

            if BuildingName_LayerList[0]!={} and len(BuildingName_LayerList[0])>0:

                for BuildingError_msg in BuildingName_LayerList[0].values():

                    ErrorMessageList.append(BuildingError_msg)

            if Floor_LayerList[0]!={} and len(Floor_LayerList[0])>0:

                for FloorError_msg in Floor_LayerList[0].values():

                    ErrorMessageList.append(FloorError_msg)

            if RefugeArea_LayerList!={} and len(RefugeArea_LayerList)>0:

                for RefugeError_msg in RefugeArea_LayerList.values():

                    ErrorMessageList.append(RefugeError_msg)

            if Plot_LayerList[0] != {} and len(Plot_LayerList[0]) > 0:

                for PlotError_msg in Plot_LayerList[0].values():

                    ErrorMessageList.append(PlotError_msg)

            if ProposedWork_LayerList[0] != {} and len(ProposedWork_LayerList[0]) > 0:

                for ProposedWorkError_msg in ProposedWork_LayerList[0].values():

                    ErrorMessageList.append(ProposedWorkError_msg)

            if OrganizedOpenSpace_LayerList[0] != {} and len(OrganizedOpenSpace_LayerList[0]) > 0:

                for OrganizedOpenSpaceError_msg in OrganizedOpenSpace_LayerList[0].values():

                    ErrorMessageList.append(OrganizedOpenSpaceError_msg)

            if AccessoryUse_LayerList!= {} and len(AccessoryUse_LayerList) > 0:

                for AccessoryUseError_msg in AccessoryUse_LayerList.values():

                    ErrorMessageList.append(AccessoryUseError_msg)

            if MainRoad_LayerList[0] != {} and len(MainRoad_LayerList[0]) > 0:

                for MainRoadError_msg in MainRoad_LayerList[0].values():

                    ErrorMessageList.append(MainRoadError_msg)

            if PlotAbuttingDetails_LayerList!= {} and len(PlotAbuttingDetails_LayerList) > 0:

                for PlotAbuttingDetailsError_msg in PlotAbuttingDetails_LayerList.values():

                    ErrorMessageList.append(PlotAbuttingDetailsError_msg)

            if Margin_LayerDict!= {} and len(Margin_LayerDict) > 0:

                for MarginError_msg in Margin_LayerDict.values():

                    ErrorMessageList.append(MarginError_msg)

            if WallCompound_LayerList[0]!= {} and len(WallCompound_LayerList[0]) > 0:

                for WallCompoundErrormsg in WallCompound_LayerList[0].values():

                    for MarginInnerError_msg in WallCompoundErrormsg:

                        ErrorMessageList.append(MarginInnerError_msg)

            if PrintAdditionalDetails_LayerList!= {} and len(PrintAdditionalDetails_LayerList) > 0:

                for PrintAdditionalDetailsError_msg in PrintAdditionalDetails_LayerList.values():

                    ErrorMessageList.append(PrintAdditionalDetailsError_msg)

            if FloorInSection_LayerList[0] != {} and len(FloorInSection_LayerList[0]) > 0:

                for FloorInSectionError_msg in FloorInSection_LayerList[0].values():

                    ErrorMessageList.append(FloorInSectionError_msg)

            if GroundLevel_LayerList[0] != {} and len(GroundLevel_LayerList[0]) > 0:

                for GroundLevelError_msg in GroundLevel_LayerList[0].values():

                    ErrorMessageList.append(GroundLevelError_msg)

            if Room_LayerList[0] != {} and len(Room_LayerList[0]) > 0:

                for RoomError_msg in Room_LayerList[0].values():

                    ErrorMessageList.append(RoomError_msg)

            if Door_LayerList!= {} and len(Door_LayerList) > 0:

                for DoorError_msg in Door_LayerList.values():

                    ErrorMessageList.append(DoorError_msg)

            if Window_LayerList!= {} and len(Window_LayerList) > 0:

                for WindowError_msg in Window_LayerList.values():

                    ErrorMessageList.append(WindowError_msg)

            if Lift_LayerList!= {} and len(Lift_LayerList) > 0:

                for LiftError_msg in Lift_LayerList.values():

                    ErrorMessageList.append(LiftError_msg)

            if MortgageArea_LayerList[0] != {} and len(MortgageArea_LayerList[0]) > 0:

                for MortgageAreaError_msg in MortgageArea_LayerList[0].values():

                    ErrorMessageList.append(MortgageAreaError_msg)

            if Balcony_LayerList!= {} and len(Balcony_LayerList) > 0:

                for BalconyError_msg in Balcony_LayerList.values():

                    ErrorMessageList.append(BalconyError_msg)

            if StairCase_LayerList!= {} and len(StairCase_LayerList) > 0:

                for StairCaseError_msg in StairCase_LayerList.values():

                    ErrorMessageList.append(StairCaseError_msg)

            if Parking_LayerList[0] != {} and len(Parking_LayerList[0]) > 0:

                for ParkingError_msg in Parking_LayerList[0].values():

                    ErrorMessageList.append(ParkingError_msg)

            if SlabCutOutVoid_LayerList!= {} and len(SlabCutOutVoid_LayerList) > 0:

                for SlabCutOutVoidError_msg in SlabCutOutVoid_LayerList.values():

                    ErrorMessageList.append(SlabCutOutVoidError_msg)

            if Passage_LayerList!= {} and len(Passage_LayerList) > 0:

                for PassageError_msg in Passage_LayerList.values():

                    for innerPassageError_msg in PassageError_msg:

                        ErrorMessageList.append(innerPassageError_msg)

            if Ramp_LayerList!= {} and len(Ramp_LayerList) > 0:

                for RampError_msg in Ramp_LayerList.values():

                    for innerRampError_msg in RampError_msg:

                        ErrorMessageList.append(innerRampError_msg)

            if Section_LayerList[0] != {} and len(Section_LayerList[0]) > 0:

                for SectionError_msg in Section_LayerList[0].values():

                    ErrorMessageList.append(SectionError_msg)

            if CarpetArea_LayerList!= {} and len(CarpetArea_LayerList) > 0:

                for CarpetAreaError_msg in CarpetArea_LayerList.values():

                    ErrorMessageList.append(CarpetAreaError_msg)

            if Driveway_LayerList!= {} and len(Driveway_LayerList)>0:

                for DrivewayError_msg in Driveway_LayerList.values():

                    for drivewayErrorMsg in DrivewayError_msg:

                        ErrorMessageList.append(drivewayErrorMsg)

            if NetPlot_LayerList[0]!={} and len(NetPlot_LayerList[0])>0:

                for NetPlot_msg in NetPlot_LayerList[0].values():

                    ErrorMessageList.append(NetPlot_msg)

            if RoadWidening_LayerList[0]!={} and len(RoadWidening_LayerList[0])>0:

                for RoadWideningError_msg in RoadWidening_LayerList[0].values():

                    ErrorMessageList.append(RoadWideningError_msg)

            if Terrace_LayerList[0] != {} and len(Terrace_LayerList[0]) > 0:

                for TerraceError_msg in Terrace_LayerList[0].values():
                    #print(Terrace_LayerList)
                    ErrorMessageList.append(TerraceError_msg)

            if ResiBuaOutline_LayerDict[0]!={} and len(ResiBuaOutline_LayerDict[0])>0:

                for ResiBuaOutline_msg in ResiBuaOutline_LayerDict[0].values():
                    #print(ResiBuaOutline_msg)
                    ErrorMessageList.append(ResiBuaOutline_msg)

            if CommBuaOutline_LayerDict[0] != {} and len(CommBuaOutline_LayerDict[0]) > 0:

                for CommBuaOutline_msg in CommBuaOutline_LayerDict[0].values():

                    ErrorMessageList.append(CommBuaOutline_msg)

            if IndBuaOutLine_LayerDict[0] != {} and len(IndBuaOutLine_LayerDict[0]) > 0:

                for IndBuaOutLine_msg in IndBuaOutLine_LayerDict[0].values():

                    ErrorMessageList.append(IndBuaOutLine_msg)

            if SpecialBuaOutLine_LayerDict[0] != {} and len(SpecialBuaOutLine_LayerDict[0]) > 0:

                for SpecialBuaOutLine_msg in SpecialBuaOutLine_LayerDict[0].values():

                    ErrorMessageList.append(SpecialBuaOutLine_msg)

            #-------------------------------------------------------Building Check Stepwise ----------------------------------------------------

            if BuildingORContainsGroundlevelLine!={} and len(BuildingORContainsGroundlevelLine)>0:

                for BuildingORContainsGroundlevelLineError_msg in BuildingORContainsGroundlevelLine.values():

                    ErrorMessageList.append(BuildingORContainsGroundlevelLineError_msg)

            if BuildingContainsFloorList[0]!= {} and len(BuildingContainsFloorList[0])>0:

                for BuildingContainsFloorError_msg in BuildingContainsFloorList[0].values():

                    ErrorMessageList.append(BuildingContainsFloorError_msg)

            if BuildingContainsFloorList[1]!= {} and len(BuildingContainsFloorList[1])>0:

                for Building_id,building_data in BuildingContainsFloorList[1].items():

                    FloorContainsLayer=self.FloorContainsAnyLayer(building_data,ResiBuaOutline_LayerDict,CommBuaOutline_LayerDict,IndBuaOutLine_LayerDict,SpecialBuaOutLine_LayerDict,Parking_LayerList[1],Terrace_LayerList[1])

                    if FloorContainsLayer is not None:

                        for FloorContainsLayerError in FloorContainsLayer.values():

                            ErrorMessageList.append(FloorContainsLayerError)


                    FloorContainsTwoDirREFCircle=self.FloorContainsTwoDIRREFCIRCLE(building_data,floorDIRREFCircle[1],ResiBUADIRREFCircle[1])

                    if FloorContainsTwoDirREFCircle is not None:

                        for FloorContainsTwoDirREFCircleError in FloorContainsTwoDirREFCircle.values():

                            ErrorMessageList.append(FloorContainsTwoDirREFCircleError)


            if BuildingContainsSectionList[0]!={} and len(BuildingContainsSectionList[0])>0:

                for BuildingContainsSectionError_msg in BuildingContainsSectionList[0].values():

                    ErrorMessageList.append(BuildingContainsSectionError_msg)

            if BuildingORSectionContainsFloorInSection!= {} and len(BuildingORSectionContainsFloorInSection) > 0:

                for BuildingContainsFloorInSectionError_msg in BuildingORSectionContainsFloorInSection.values():

                    ErrorMessageList.append(BuildingContainsFloorInSectionError_msg)

            # -------------------------------------------------------Siteplan Check Stepwise ----------------------------------------------------


            if Plot_LayerList[1] != {} and len(Plot_LayerList[1]) > 0 :

                PlotContainsProposedWork=self.PlotContainsProposedWork(Plot_LayerList[1],ProposedWork_LayerList[1])

                PlotTouchCMORN=self.PlotTouchCMORN(Plot_LayerList[1],WallCompound_LayerList[1],OrganizedOpenSpace_LayerList[1],MainRoad_LayerList[1],NetPlot_LayerList[1],RoadWidening_LayerList[1])

                if PlotContainsProposedWork is not None:

                    for ErrorPlotContainsProposedWork in PlotContainsProposedWork.values():

                        ErrorMessageList.append(ErrorPlotContainsProposedWork)

                if PlotTouchCMORN is not None:

                    for ErrorPlotTouchCMORN in PlotTouchCMORN.values():

                        ErrorMessageList.append(ErrorPlotTouchCMORN)

                for plot_id,PlotNamePoly in Plot_LayerList[1].items():

                    for ProposedWorkNamePoly in ProposedWork_LayerList[1].values():

                        ProposedWorkContainsTwoDirREfCircle=self.ProposedWorkContainsTwoDIRREFCIRCLE(ProposedWork_LayerList[1],floorDIRREFCircle[1],ResiBUADIRREFCircle[1])

                        if ProposedWorkContainsTwoDirREfCircle is not None:

                            for ProposedWorkContainsTwoDirREfCircle in ProposedWorkContainsTwoDirREfCircle.values():

                                ErrorMessageList.append(ProposedWorkContainsTwoDirREfCircle)

                        if PlotNamePoly[1].contains(ProposedWorkNamePoly[1])==True or round(PlotNamePoly[1].distance(ProposedWorkNamePoly[1]),1)==0.0:

                            for Building_id, BuildingNamePoly in BuildingName_LayerList[1].items():

                                filter_prop_name = "".join(x for x in ProposedWorkNamePoly[0] if x.isalpha())

                                filter_building_name="".join(x for x in BuildingNamePoly[0] if x.isalpha())

                                if filter_prop_name==filter_building_name:

                                    print('Matching Label:',(ProposedWorkNamePoly[0],BuildingNamePoly[0]))

                                    Building_Height = self.BuildingHeight(BuildingName_LayerList[1],FloorInSection_LayerList[1])

                                    if ResiBuaOutline_LayerDict!={} and len(ResiBuaOutline_LayerDict)>0:

                                        BuildingContainsResiBua = []

                                        for resiBUAPoly in ResiBuaOutline_LayerDict[1].values():

                                            if BuildingNamePoly[1].contains(resiBUAPoly)==True or round(BuildingNamePoly[1].distance(resiBUAPoly),1)==0.0:

                                                BuildingContainsResiBua.append(resiBUAPoly)

                                        if BuildingContainsResiBua!=[] and len(BuildingContainsResiBua)>0:

                                            BuildingContainsMortgageArea=[]

                                            for MortgageNamePoly in MortgageArea_LayerList[1].values():

                                                #if BuildingNamePoly[1].contains(MortgageNamePoly[1]) == True or round(BuildingNamePoly[1].distance(MortgageNamePoly[1]), 1) == 0.0:

                                                BuildingContainsMortgageArea.append(MortgageNamePoly[1])

                                            if (BuildingContainsMortgageArea==[] and len(BuildingContainsMortgageArea)==0) and max(Building_Height)>6:

                                                ErrorMSg=f'Warning-Allowed Mortgage Layer For Building REF# {Building_id} - {BuildingNamePoly[0]} For Buildings height:{max(Building_Height)}'

                                                ErrorMessageList.append(ErrorMSg)

                                            BuildingContainsParking=[]

                                            for ParkingNamePoly in Parking_LayerList[1].values():

                                                #if BuildingNamePoly[1].contains(ParkingNamePoly[1]) == True or round(BuildingNamePoly[1].distance(ParkingNamePoly[1]), 1) == 0.0:

                                                BuildingContainsParking.append(ParkingNamePoly[1])

                                            if (BuildingContainsParking==[] and len(BuildingContainsParking)==0) and round(PlotNamePoly[1].area)>=750:

                                                ErrorMsg=f'Warning-Allowed Parking Layer Building REF# {Building_id} - {BuildingNamePoly[0]} for Plot {round(PlotNamePoly[1].area)} sqmt.'

                                                ErrorMessageList.append(ErrorMsg)

                                            BuildingContainsStiltFloor1=[]

                                            for FloorNamePoly in Floor_LayerList[1].values():

                                                if 'stilt' in FloorNamePoly[0].lower():

                                                    if BuildingNamePoly[1].contains(FloorNamePoly[1]) == True or round(BuildingNamePoly[1].distance(FloorNamePoly[1]), 1) == 0.0:

                                                        BuildingContainsStiltFloor1.append(FloorNamePoly[1])

                                            if (BuildingContainsStiltFloor1!=[] and len(BuildingContainsStiltFloor1)) and round(PlotNamePoly[1].area)<200:

                                                ErrorMsg = f'Warning-Stilt Floor Not Allowed Building REF# {Building_id} - {BuildingNamePoly[0]} for Plot {round(PlotNamePoly[1].area)} sqmt.'

                                                ErrorMessageList.append(ErrorMsg)

                                            elif((BuildingContainsStiltFloor1!=[] and len(BuildingContainsStiltFloor1)) and round(PlotNamePoly[1].area)>200):

                                                for stilt_floor in BuildingContainsStiltFloor1:

                                                    StiltFloorContainsRoom=[]

                                                    for roomNamePoly in Room_LayerList[1].values():

                                                        if BuildingNamePoly[1].contains(roomNamePoly[1])==True or round(BuildingNamePoly[1].distance(roomNamePoly[1]),1)==0.0:

                                                            if stilt_floor.contains(roomNamePoly[1])==True or round(stilt_floor.distance(roomNamePoly[1]),1)==0.0:

                                                                StiltFloorContainsRoom.append(roomNamePoly[1])

                                                    if (StiltFloorContainsRoom!=[] and len(StiltFloorContainsRoom)>0):

                                                        ErrorMsg=f'Warning-Room Is Not Allowed in Stilt Floor - Building REF# {Building_id} {BuildingNamePoly[1]} For Plot {round(PlotNamePoly[1].area)}'

                                                        ErrorMessageList.append(ErrorMsg)

            if CommBuaOutline_LayerDict[1]!= {} and len(CommBuaOutline_LayerDict[1]) > 0:

                BuildingContainsCommBUA = []

                for CommBuaNamePoly in CommBuaOutline_LayerDict[1].values():

                        BuildingContainsCommBUA.append(CommBuaNamePoly)

                if BuildingContainsCommBUA != [] and len(BuildingContainsCommBUA) > 0:

                    BuildingContainsMortgageArea = []

                    for MortgageNamePoly in MortgageArea_LayerList[1].values():

                        BuildingContainsMortgageArea.append(MortgageNamePoly)

                    if BuildingContainsMortgageArea == [] and len(BuildingContainsMortgageArea) == 0:

                        ErrorMsg = f'Warning- MortgageArea Layer Allowed For Commercial Buildings.'

                        ErrorMessageList.append(ErrorMsg)

                    BuildingContainsParking = []

                    for ParkingNamePoly in Parking_LayerList[1].values():

                            BuildingContainsParking.append(ParkingNamePoly[1])

                    if BuildingContainsParking == [] and len(BuildingContainsParking) == 0:

                        ErrorMsg = f'Warning- Parking Layer Allowed For Commercial Buildings.'

                        ErrorMessageList.append(ErrorMsg)

        except IOError:

            print(f'Not a DXF file or a generic I/O error.')

            return ErrorMessageList

        except ezdxf.DXFStructureError:

            print(f'Invalid or corrupted DXF file.')

            return ErrorMessageList

        finally:

            print(f'Process Complete Successfully.')

        return ErrorMessageList

# #----------------------------------Input of File------------------------------------
# from datetime import datetime
#
# start_time = datetime.now()
#
# t1 = start_time.strftime("%H:%M:%S")
#
# first_start_time = datetime.strptime(t1, "%H:%M:%S")
#
# folder="E:/production_code/dxf_files/Buildings/"
#
# filename="2 blocks (1).dxf"
#
# dxf_file=ezdxf.readfile(os.path.join(folder,filename))
#
# msp=dxf_file.modelspace()
#
# obj=CommonValidationLayers()
#
# response=obj.performLayerChecks(msp)
#
# if response!=[] and len(response)>0:
#    print(len(response))
#    print(f'Error In This File:{response}')
#
# else:
#
#    print(f"Didn't Get Any Error In This File:{filename}.")
# end_time = datetime.now()
#
# t2 = end_time.strftime("%H:%M:%S")
#
# last_end_time = datetime.strptime(t2, "%H:%M:%S")
#
# total_time = last_end_time - first_start_time
#
# print(f'Total Time is:{total_time}')