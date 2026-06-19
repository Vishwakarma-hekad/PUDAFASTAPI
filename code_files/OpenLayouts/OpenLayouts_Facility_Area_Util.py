
import os
import ezdxf
from datetime import datetime
from shapely.geometry import Polygon, Point, LineString
from convert_polygon_to_arc import polygon2arc

class Facilities_With_InternalRoad:

    def splitcnterLine(self, center_line_po1):
        num_points = len(center_line_po1)
        midpoint_index = num_points // 2
        center_line_part1 = center_line_po1[:midpoint_index]
        center_line_part2 = center_line_po1[midpoint_index:]
        return center_line_part1, center_line_part2

    def Facilities_Layer_Data(self, Facilities_Layer):
        Facilities = dict()
        Facilities_dict = dict()
        ErrorList = []
        for Facilities_poly in Facilities_Layer:
            if Facilities_poly.dxftype() == "LWPOLYLINE":
                Facilities_id = Facilities_poly.dxf.handle
                if Facilities_poly.closed:

                    check_facilityarc = any(
                        [entity.dxftype() == "ARC" for entity in Facilities_poly.virtual_entities()])

                    Facilities_poly_pts = polygon2arc.Polygon_Merger_ARC(Facilities_poly) if check_facilityarc else Polygon(
                        Facilities_poly.get_points("xy"))

                    # Facilities_poly_pts = Polygon([bp[0:2] for bp in Facilities_poly.get_points()])
                    Facilities_Area = round(Facilities_poly_pts.area, 2)

                    Facilities_list = []
                    for Facilities_text_poly in Facilities_Layer:
                        if Facilities_text_poly.dxftype() == "MTEXT" or Facilities_text_poly.dxftype() == "TEXT":
                            Facilities_text = Facilities_text_poly.dxf.text if Facilities_text_poly.dxftype() == "TEXT" else Facilities_text_poly.plain_text()

                            if Facilities_text != "":
                                Facilities_text_id = Facilities_poly.dxf.handle
                                Facilities_text_pts = Point(
                                    [Facilities_text_poly.dxf.insert[0], Facilities_text_poly.dxf.insert[1]])

                                if Facilities_poly_pts.contains(Facilities_text_pts) or Facilities_poly_pts.touches(
                                        Facilities_text_pts) or round(Facilities_poly_pts.distance(Facilities_text_pts),
                                                                      1) == 0.0:
                                    Facilities_list.append(
                                        [Facilities_text_id, Facilities_text, Facilities_poly_pts, Facilities_Area])

                    if not Facilities_list:
                        errors1 = f"Warning: Facilities polygon {Facilities_id} Missing Label "
                        ErrorList.append(errors1)

                    for Facilities_data in Facilities_list:
                        Facilities_dict[Facilities_data[0]] = Facilities_data[1:]

                else:
                    errors2 = f"Warning: Facilities Polygon Not Closed Properly {Facilities_id}"
                    ErrorList.append(errors2)



        Facilities["DATA"] = Facilities_dict
        Facilities["ERROR"] = ErrorList


        return Facilities

    def InternalRoad_Data(self, Internal_Road):

        InternalRoaddata_dict = dict()

        InternalRoad_Dict = dict()
        ErrorList = []

        for InternalRoad_entity_lw_poly in Internal_Road:
            if InternalRoad_entity_lw_poly.dxftype() == "LWPOLYLINE":
                if InternalRoad_entity_lw_poly.dxf.linetype != "CENTER" :
                    InternalRoad_Poly_id = InternalRoad_entity_lw_poly.dxf.handle
                    if InternalRoad_entity_lw_poly.closed :
                        InternalRoad_rad_po = [np[0:2]for np in InternalRoad_entity_lw_poly.get_points()]
                        InternalRoad_rad_poly_points = Polygon(InternalRoad_rad_po)
                        InternalRoad_list = []

                        for InternalRoad_text in Internal_Road:
                            if InternalRoad_text.dxftype() == "MTEXT" or InternalRoad_text.dxftype() == "TEXT":
                                InternalRoad_Name = InternalRoad_text.dxf.text if InternalRoad_text.dxftype() == "TEXT" else InternalRoad_text.plain_text()
                                InternalRoad_id = InternalRoad_text.dxf.handle
                                InternalRoad_point = (InternalRoad_text.dxf.insert.x,InternalRoad_text.dxf.insert.y)
                                InternalRoad_points_text = Point(InternalRoad_point)

                                if InternalRoad_rad_poly_points.contains(InternalRoad_points_text) == True or InternalRoad_rad_poly_points.touches(InternalRoad_points_text) == True or round(InternalRoad_rad_poly_points.distance(InternalRoad_points_text),1) == 0.0:
                                    for line_poly in Internal_Road:
                                        if line_poly.dxftype() == "LWPOLYLINE":
                                            if line_poly.dxf.linetype == "CENTER" and line_poly.closed == False:
                                                center_line_po = [cp[0:2]for cp in line_poly.get_points()]
                                                center_poly_list_contain = [ round(InternalRoad_rad_poly_points.distance(Point(center_line_points)),1) == 0.0 for center_line_points in center_line_po]

                                                if all(center_poly_list_contain) == True:
                                                    split_pts = self.splitcnterLine(center_line_po)[0]
                                                    center_poly_list_contain = [InternalRoad_rad_poly_points.contains(Point(center_line_points)) == True or round(InternalRoad_rad_poly_points.distance(Point(center_line_points)),1) == 0.0 for center_line_points in center_line_po]

                                                    if all(center_poly_list_contain) == True:
                                                        c_line_points = Point(split_pts[0])
                                                        Distance_Data = []

                                                        for vir_line in InternalRoad_entity_lw_poly.virtual_entities():
                                                            if vir_line.dxftype() == "LINE":
                                                                starts = (vir_line.dxf.start.x, vir_line.dxf.start.y)
                                                                ends = (vir_line.dxf.end.x, vir_line.dxf.end.y)
                                                                line_point = LineString([starts,ends])

                                                                if round(line_point.distance(c_line_points),1)!=0.0:
                                                                    all_dis= (round(line_point.distance(c_line_points),1))
                                                                    if all_dis>1.0:
                                                                        Distance_Data.append(all_dis)

                                                        Min_width = min(Distance_Data)*2
                                                        InternalRoad_list.append([InternalRoad_id,InternalRoad_Name,InternalRoad_rad_poly_points,Min_width])

                        if not InternalRoad_list:
                            errors1 = f"Warning:InternaRoad polygon {InternalRoad_Poly_id} Missing Label "
                            ErrorList.append(errors1)

                        for InternalRoadData in InternalRoad_list:
                            InternalRoad_Dict[InternalRoadData[0]] = InternalRoadData[1:]

                    else:
                        errors2 = f"Warning: Polygon Internal Road Not Closed Properly {InternalRoad_Poly_id}"
                        ErrorList.append(errors2)

        InternalRoaddata_dict["DATA"] = InternalRoad_Dict
        InternalRoaddata_dict["ERROR"] = ErrorList

        return InternalRoaddata_dict

    def FacilitiesTouchInternal(self, Facilities_data, InternalRoad_data):
        Width_list = []
        for Facilities_id, Facilities_poly in Facilities_data.items():
            Max_width = 0.0
            Entity_id = None
            Label_name = None

            for InternalRoad_id, InternalRoad_poly in InternalRoad_data.items():
                if round(Facilities_poly[1].distance(InternalRoad_poly[1]),1) == 0.0:
                    if InternalRoad_poly[2] > Max_width:
                        Max_width = max(Max_width,InternalRoad_poly[2])
                        Entity_id = InternalRoad_id
                        Label_name = InternalRoad_poly[0]

            Temp_Dict = dict()
            Temp_Dict["FACILITIES_ID"] = Facilities_id
            Temp_Dict["TYPE"] = "FACILITY"
            Temp_Dict["FACILITIES_LABEL"] = Facilities_poly[0]
            Temp_Dict["FACILITIES_AREA"] = Facilities_poly[2]
            Temp_Dict["INTERNALROAD_ID"] = Entity_id
            Temp_Dict["INTERNALROAD_LABEL"] = Label_name
            Temp_Dict["INTERNALROAD_WIDTH"] = Max_width
            Width_list.append(Temp_Dict)

        return Width_list

    def CheckFacilityValidation(self, msp):

        returnValuesDict = dict()
        ErrorList = []

        if msp is None:
            ErrorList.append("Facilities Check - Invalid Input , required Modelspace but is None")
            
            returnValuesDict['CODE'] = -1
            returnValuesDict['ERROR'] =ErrorList
            return returnValuesDict

        try:
            

            print("Loading DXF File Data...")
            Facilities_Layer = msp.query('*[layer =="_Facilities"]')
            Facilities_data = self.Facilities_Layer_Data(Facilities_Layer)

            Internal_Road = msp.query('*[layer =="_InternalRoad"]')
            InternalRoad_data = self.InternalRoad_Data(Internal_Road)

            ErrorList.extend(Facilities_data.get("ERROR",[]))
            ErrorList.extend(InternalRoad_data.get("ERROR",[]))

            width_list = self.FacilitiesTouchInternal(Facilities_data.get("DATA"), InternalRoad_data.get("DATA"))

            returnValuesDict["CODE"] = 0
            returnValuesDict["ERROR"] = ErrorList
            returnValuesDict["RESULTS"] = width_list

        except ezdxf.DXFStructureError as dse:
            errors = f'Invalid Or corrupted DXF File Generic Exception .' + str(dse)
            print(errors)
            ErrorList.append(errors)
            returnValuesDict["CODE"] = -1
            returnValuesDict["ERROR"] = ErrorList
            return returnValuesDict

        except Exception as excp:
            errors = (f'Not a DXF file or a generic I/O error.' + str(excp))
            print(errors)
            ErrorList.append(errors)
            returnValuesDict["CODE"] = -1
            returnValuesDict["ERROR"] = ErrorList
            return returnValuesDict

        return returnValuesDict


## Main Script
# start_time = datetime.now()
# folder = "D:/production_code_all/FacilityArea/File"
# filename = "suryapet 150 acrs modified peval layout drawing.dxf"
# print(f"FileName - {filename}")
# dxf_path = os.path.join(folder, filename)
# read_dxf = ezdxf.readfile(dxf_path)
# msp = read_dxf.modelspace()
# Data_Extractor = Facilities_With_InternalRoad()
# response = Data_Extractor.CheckFacilityValidation(msp)
# print(response)
# end_time = datetime.now()
# total_time = end_time - start_time
# print("=" * 100)
# print(f'Total Time is:{total_time}')
# print("=" * 100)
#