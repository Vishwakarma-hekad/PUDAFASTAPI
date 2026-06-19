import os
import ezdxf
from shapely.geometry import Polygon
class CheckUtilityAndSocialInfrastructure:
    def InternalRoadData(self,internal_road):
        internal_road_dict = dict()
        internal_road_list = []
        for internal_road_poly_ps in internal_road:
            if internal_road_poly_ps.dxftype() == "LWPOLYLINE" and internal_road_poly_ps.closed == True:
                internalRoad_id = internal_road_poly_ps.dxf.handle
                internal_ps = [np[0:2] for np in internal_road_poly_ps.get_points()]
                internal_poly_points = Polygon(internal_ps)
                internal_road_list.append([internalRoad_id,internal_poly_points])
        if internal_road_list != [] or internal_road_list is not None:
            for internal_road_data in internal_road_list:
                internal_road_dict[internal_road_data[0]] = internal_road_data[1:]
        else:
            print(f"InternalRoad Not containing any Polygons")
        return internal_road_dict
    def AmenityLayerData(self, Amenity_datas):
        Amenity_dict = dict()
        Amenity_list = []
        for Amenity_road_poly_ps in Amenity_datas:
            if Amenity_road_poly_ps.dxftype() == "LWPOLYLINE" and Amenity_road_poly_ps.closed == True:
                Amenity_id = Amenity_road_poly_ps.dxf.handle
                Amenity_ps = [np[0:2] for np in Amenity_road_poly_ps.get_points()]
                Amenity_poly_points = Polygon(Amenity_ps)
                Amenity_list.append([Amenity_id,Amenity_poly_points])
        if Amenity_list != [] or Amenity_list is not None:
            for Amenity_data in Amenity_list:
                Amenity_dict[Amenity_data[0]] = Amenity_data[1:]
        else:
            print(f"Amenity Not containing any Polygons")
        return Amenity_dict
    def AccessoryUseData(self, AccessoryUse):
        AccessoryUse_dict = dict()
        AccessoryUse_list = []
        for AccessoryUse_road_poly_ps in AccessoryUse:
            if AccessoryUse_road_poly_ps.dxftype() == "LWPOLYLINE" and AccessoryUse_road_poly_ps.closed == True:
                AccessoryUse_id = AccessoryUse_road_poly_ps.dxf.handle
                AccessoryUse_ps = [np[0:2] for np in AccessoryUse_road_poly_ps.get_points()]
                AccessoryUse_poly_points = Polygon(AccessoryUse_ps)
                AccessoryUse_list.append([AccessoryUse_id,AccessoryUse_poly_points])
        if AccessoryUse_list != [] or AccessoryUse_list is not None:
            for internal_road_data in AccessoryUse_list:
                AccessoryUse_dict[internal_road_data[0]] = internal_road_data[1:]
        else:
            print(f"AccessoryUse Not containing any Polygons")
        return AccessoryUse_dict
    def OrganizedOpenSpaceData(self, OrganizedOpenSpace_datas):
        OrganizedOpenSpace_dict = dict()
        OrganizedOpenSpace_list = []
        for OrganizedOpenSpace_road_poly_ps in OrganizedOpenSpace_datas:
            if OrganizedOpenSpace_road_poly_ps.dxftype() == "LWPOLYLINE" and OrganizedOpenSpace_road_poly_ps.closed == True:
                OrganizedOpenSpace_id = OrganizedOpenSpace_road_poly_ps.dxf.handle
                OrganizedOpenSpace_ps = [np[0:2] for np in OrganizedOpenSpace_road_poly_ps.get_points()]
                OrganizedOpenSpace_poly_points = Polygon(OrganizedOpenSpace_ps)
                OrganizedOpenSpace_list.append([OrganizedOpenSpace_id,OrganizedOpenSpace_poly_points])
        if OrganizedOpenSpace_list != [] or OrganizedOpenSpace_list is not None:
            for OrganizedOpenSpace_data in OrganizedOpenSpace_list:
                OrganizedOpenSpace_dict[OrganizedOpenSpace_data[0]] = OrganizedOpenSpace_data[1:]
        else:
            print(f"OrganizedOpenSpace Not containing any Polygons")
        return OrganizedOpenSpace_dict
    def MainRoadData(self, MainRoad_datas):
        MainRoad_dict = dict()
        MainRoad_list = []
        for MainRoad_road_poly_ps in MainRoad_datas:
            if MainRoad_road_poly_ps.dxftype() == "LWPOLYLINE" and MainRoad_road_poly_ps.closed == True:
                MainRoad_id = MainRoad_road_poly_ps.dxf.handle
                MainRoad_ps = [np[0:2] for np in MainRoad_road_poly_ps.get_points()]
                MainRoad_poly_points = Polygon(MainRoad_ps)
                MainRoad_list.append([MainRoad_id,MainRoad_poly_points])
        if MainRoad_list != [] or MainRoad_list is not None:
            for MainRoad_data in MainRoad_list:
                MainRoad_dict[MainRoad_data[0]] = MainRoad_data[1:]
        else:
            print(f"MainRoad Not containing any Polygons")
        return MainRoad_dict
    def IndivSubPlotData(self, IndivSubPlot_datas):
        IndivSubPlot_dict = dict()
        IndivSubPlot_list = []
        for IndivSubPlot_poly_ps in IndivSubPlot_datas:
            if IndivSubPlot_poly_ps.dxftype() == "LWPOLYLINE" and IndivSubPlot_poly_ps.closed == True:
                IndivSubPlot_id = IndivSubPlot_poly_ps.dxf.handle
                IndivSubPlot_ps = [np[0:2] for np in IndivSubPlot_poly_ps.get_points()]
                IndivSubPlot_poly_points = Polygon(IndivSubPlot_ps)
                IndivSubPlot_list.append([IndivSubPlot_id,IndivSubPlot_poly_points])
        if IndivSubPlot_list != [] or IndivSubPlot_list is not None:
            for IndivSubPlot_data in IndivSubPlot_list:
                IndivSubPlot_dict[IndivSubPlot_data[0]] = IndivSubPlot_data[1:]
        else:
            print(f"IndivSubPlot Not containing any Polygons")
        return IndivSubPlot_dict
    def ValidationForAmenity(self,AmentityPolygon,ListOuterpoly):
        Amentity_dict = dict()
        amentityTouchOrganizedOpenSpace = []
        amentityTouchAccessoryUse = []
        amentityTouchInternalRoad = []
        amentityTouchMainRoad = []
        for list_poly in ListOuterpoly[0].values():
            if AmentityPolygon.contains(list_poly[0]) == True or AmentityPolygon.touches(list_poly[0]) == True or round(AmentityPolygon.distance(list_poly[0]),1) ==0.0:
                amentityTouchOrganizedOpenSpace.append(True)
        for list_poly in ListOuterpoly[1].values():
            if AmentityPolygon.contains(list_poly[0]) == True or AmentityPolygon.touches(list_poly[0]) == True or round(AmentityPolygon.distance(list_poly[0]),1) ==0.0:
                amentityTouchAccessoryUse.append(True)
        for list_poly in ListOuterpoly[2].values():
            if AmentityPolygon.contains(list_poly[0]) == True or AmentityPolygon.touches(list_poly[0]) == True or round(AmentityPolygon.distance(list_poly[0]),1) ==0.0:
                amentityTouchInternalRoad.append(True)
        for list_poly in ListOuterpoly[3].values():
            if AmentityPolygon.contains(list_poly[0]) == True or AmentityPolygon.touches(list_poly[0]) == True or round(AmentityPolygon.distance(list_poly[0]),1) ==0.0:
                amentityTouchMainRoad.append(True)
        if amentityTouchOrganizedOpenSpace !=[] and len(amentityTouchOrganizedOpenSpace) > 0:
            Amentity_dict["ORGANIZEDOPENSPACE"] = "True"
        else:
            Amentity_dict["ORGANIZEDOPENSPACE"] = "False"

        if amentityTouchAccessoryUse !=[] and len(amentityTouchAccessoryUse) > 0:
            Amentity_dict["ACCESSORYUSE"] = "True"
        else:
            Amentity_dict["ACCESSORYUSE"] = "False"

        if amentityTouchInternalRoad !=[] and len(amentityTouchInternalRoad) > 0:
            Amentity_dict["INTERNALROAD"] = "True"
        else:
            Amentity_dict["INTERNALROAD"] = "False"

        if amentityTouchMainRoad !=[] and len(amentityTouchMainRoad) > 0:
            Amentity_dict["MAINROAD"] = "True"
        else:
            Amentity_dict["MAINROAD"] = "False"

        return Amentity_dict
    def ValidationForUtility(self,UtilityPolygon,ListOuterpoly):
        Utility_dict = dict()
        UtilityTouchIndivsubplot = []
        UtilityTouchInternalRoad = []
        UtilityTouchMainRoad = []

        for list_poly in ListOuterpoly[0].values():
            if UtilityPolygon.contains(list_poly[0]) == True or UtilityPolygon.touches(list_poly[0]) == True or round(UtilityPolygon.distance(list_poly[0]),1) ==0.0:
                UtilityTouchIndivsubplot.append(True)
        for list_poly in ListOuterpoly[1].values():
            if UtilityPolygon.contains(list_poly[0]) == True or UtilityPolygon.touches(list_poly[0]) == True or round(UtilityPolygon.distance(list_poly[0]),1) ==0.0:
                UtilityTouchInternalRoad.append(True)
        for list_poly in ListOuterpoly[2].values():
            if UtilityPolygon.contains(list_poly[0]) == True or UtilityPolygon.touches(list_poly[0]) == True or round(UtilityPolygon.distance(list_poly[0]),1) ==0.0:
                UtilityTouchMainRoad.append(True)

        if UtilityTouchIndivsubplot !=[] and len(UtilityTouchIndivsubplot) > 0:
            Utility_dict["INDIVSUBPLOT"] = "True"
        else:
            Utility_dict["INDIVSUBPLOT"] = "False"

        if UtilityTouchInternalRoad !=[] and len(UtilityTouchInternalRoad) > 0:
            Utility_dict["INTERNALROAD"] = "True"
        else:
            Utility_dict["INTERNALROAD"] = "False"

        if UtilityTouchMainRoad !=[] and len(UtilityTouchMainRoad) > 0:
            Utility_dict["MAINROAD"] = "True"
        else:
            Utility_dict["MAINROAD"] = "False"

        return Utility_dict
    def CheckSocialInfoValidation(self,msp):
        returnValuesDict = dict()
        if (msp == None):
            returnValuesDict['CODE']=-1
            returnValuesDict['ERROR']="Social Utility Infra Check - Invalid Input , required Modelspace but is None"
            return returnValuesDict


        try:
            print("Loading DXF File Data...")

            internal_road = msp.query('*[layer =="_InternalRoad"]')
            internal_road_data = self.InternalRoadData(internal_road)

            Amenity = msp.query('*[layer =="_Amenity"]')
            Amenity_data = self.AmenityLayerData(Amenity)

            AccessoryUse = msp.query('*[layer =="_AccessoryUse"]')
            AccessoryUse_data = self.AccessoryUseData(AccessoryUse)

            OrganizedOpenSpace = msp.query('*[layer =="_OrganizedOpenSpace"]')
            OrganizedOpenSpace_data = self.OrganizedOpenSpaceData(OrganizedOpenSpace)

            MainRoad = msp.query('*[layer =="_MainRoad"]')
            MainRoad_data = self.MainRoadData(MainRoad)

            IndivSubPlot = msp.query('*[layer =="_IndivSubPlot"]')
            IndivSubPlot_data = self.IndivSubPlotData(IndivSubPlot)

            TotalAmenityData = []
            TotalUtilityData = []
            AllData=[]


            validationlistFor_amentity = [OrganizedOpenSpace_data,AccessoryUse_data,internal_road_data,MainRoad_data]
            for amentity_id ,amentitylablepoly in Amenity_data.items():
                print("checking amentitylablepoly  ", amentity_id )
                amentyDict=self.ValidationForAmenity(amentitylablepoly[0],validationlistFor_amentity)
                amentyDict["ID"]="AMENITY_" + str(amentity_id)
                amentyDict["TYPE"]="AMENITYCHECK" 
                #amentyDict["CHECKEDWITH"]="OrganizedOpenSpace, AccessoryUse, InternalRoad, MainRoad"
                AllData.append(amentyDict)#self.ValidationForAmenity(amentitylablepoly[0],validationlistFor_amentity))

            validationlistFor_utility = [IndivSubPlot_data,internal_road_data,MainRoad_data]
            for utility_id ,utilitylablepoly in AccessoryUse_data.items():
                print("checking utility_id  ", utility_id )
                utilDict=self.ValidationForUtility(utilitylablepoly[0],validationlistFor_utility)
                utilDict["ID"]="UTILITY_"+ str(utility_id)
                utilDict["TYPE"]="UTILITYCHECK"
                #utilDict["CHECKEDWITH"]="IndivSubPlot, InternalRoad, MainRoad"
                AllData.append(utilDict)

            #tempRespDict=dict()
            #tempRespDict["VAL_AMENITY"] = TotalAmenityData
            #tempRespDict["VAL_UTILITY"] = TotalUtilityData

            returnValuesDict["CODE"] = 0
            returnValuesDict["RESULTS"]=AllData

            

        except ezdxf.DXFStructureError as dse:
            
            print(f'Invalid Or corrupted DXF File Generic Exception .' + str(dse))
            returnValuesDict["CODE"] = -1
            returnValuesDict["ERROR"]=str(dse)

        except Exception as excp:

            print(f'Not a DXF file or a generic I/O error.' + str(excp))
            returnValuesDict["CODE"] = -1
            returnValuesDict["ERROR"]=str(excp)

        return returnValuesDict
# # ===============================================================================================
# from datetime import datetime
# start_time = datetime.now()
# t1 = start_time.strftime("%H:%M:%S")
# first_start_time = datetime.strptime(t1, "%H:%M:%S")
# folder = "D:/DXF_Files/Fire_Building_file/DXF"
# filename = "utility touch with induval plot 4.dxf"
# print(f"FileName - {filename}")
# dxf_path = os.path.join(folder, filename)
# read_dxf = ezdxf.readfile(dxf_path)
# msp= read_dxf.modelspace()
# Data_Extractor = CheckUtilityAndSocialInfrastructure()
# response = Data_Extractor.CheckValidation(msp)
# print(response)
# end_time = datetime.now()
# t2 = end_time.strftime("%H:%M:%S")
# last_end_time = datetime.strptime(t2, "%H:%M:%S")
# total_time = last_end_time - first_start_time
# print("="*100)
# print(f'Total Time is:{total_time}')
# print("="*100)