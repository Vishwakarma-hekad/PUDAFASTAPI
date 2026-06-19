from shapely.geometry import LineString,Polygon,Point
from ezdxf.entities.mtext import plain_mtext
import math
import numpy as np
from shapely.ops import unary_union


class CourtYardDetails:

    def __init__(self,msp):

        self.msp=msp
        self.courtyard_textquery= self.msp.query("TEXT MTEXT[layer=='_Courtyard']")
        self.courtyard_polyquery= self.msp.query("LWPOLYLINE[layer=='_Courtyard']")
        self.margins_queries= self.msp.query("LINE LWPOLYLINE INSERT[layer=='_MarginLine']")
        self.resiinsert_query= self.msp.query("INSERT[layer=='_ResiBUAOutline']")
        self.floorinsert_query= self.msp.query("INSERT[layer=='_Floor']")
        self.proposedworktext_query= self.msp.query("TEXT MTEXT[layer=='_ProposedWork']")
        self.proposedworkpoly_query= self.msp.query("LWPOLYLINE[layer=='_ProposedWork']")
        self.floortext_query = self.msp.query("TEXT MTEXT[layer=='_Floor']")
        self.floorpoly_query = self.msp.query("LWPOLYLINE[layer=='_Floor']")
        self.bldgtext_query = self.msp.query("TEXT MTEXT[layer=='_BuildingName']")
        self.bldgpoly_query = self.msp.query("LWPOLYLINE[layer=='_BuildingName']")

        self.buapoly_query= self.msp.query("LWPOLYLINE[layer=='_ResiBUAOutline'| layer=='_CommBUAOutline'| "
                                           "layer=='_SpecialBUAOutline' | layer=='_IndBUAOutline']")

    def getMargines(self):

        front_lines=[]
        rear_lines=[]
        side1_lines=[]
        side2_lines=[]
        for entity in self.margins_queries:

            if entity.dxftype()=="LWPOLYLINE":

                if entity.dxf.color==1:
                    front_lines.append(LineString(entity.get_points("xy")))
                elif entity.dxf.color==6:
                    rear_lines.append(LineString(entity.get_points("xy")))
                elif entity.dxf.color in (104,3):
                    side1_lines.append(LineString(entity.get_points("xy")))
                elif entity.dxf.color==5:
                    side2_lines.append(LineString(entity.get_points("xy")))

            elif entity.dxftype()=="LINE":

                if entity.dxf.color==1:
                    front_lines.append(LineString([(entity.dxf.start[0],entity.dxf.start[1]),(entity.dxf.end[0],entity.dxf.end[1])]))
                elif entity.dxf.color==6:
                    rear_lines.append(LineString([(entity.dxf.start[0],entity.dxf.start[1]),(entity.dxf.end[0],entity.dxf.end[1])]))
                elif entity.dxf.color in (104,3):
                    side1_lines.append(LineString([(entity.dxf.start[0],entity.dxf.start[1]),(entity.dxf.end[0],entity.dxf.end[1])]))
                elif entity.dxf.color==5:
                    side2_lines.append(LineString([(entity.dxf.start[0],entity.dxf.start[1]),(entity.dxf.end[0],entity.dxf.end[1])]))


            elif entity.dxftype()=="INSERT":

                for vir_entity in entity.virtual_entities():

                    if vir_entity.dxftype()=="LINE":

                        if vir_entity.dxf.color == 1:
                            front_lines.append(LineString(
                                [(vir_entity.dxf.start[0], vir_entity.dxf.start[1]), (vir_entity.dxf.end[0], vir_entity.dxf.end[1])]))
                        elif vir_entity.dxf.color == 6:
                            rear_lines.append(LineString(
                                [(vir_entity.dxf.start[0], vir_entity.dxf.start[1]), (vir_entity.dxf.end[0], vir_entity.dxf.end[1])]))
                        elif vir_entity.dxf.color in (104, 3):
                            side1_lines.append(LineString(
                                [(vir_entity.dxf.start[0], vir_entity.dxf.start[1]), (vir_entity.dxf.end[0], vir_entity.dxf.end[1])]))
                        elif vir_entity.dxf.color == 5:
                            side2_lines.append(LineString(
                                [(vir_entity.dxf.start[0], vir_entity.dxf.start[1]), (vir_entity.dxf.end[0], vir_entity.dxf.end[1])]))

                    elif vir_entity.dxftype()=="LWPOLYLINE":

                        if vir_entity.dxf.color == 1:
                            front_lines.append(LineString(vir_entity.get_points("xy")))
                        elif vir_entity.dxf.color == 6:
                            rear_lines.append(LineString(vir_entity.get_points("xy")))
                        elif vir_entity.dxf.color in (104, 3):
                            side1_lines.append(LineString(vir_entity.get_points("xy")))
                        elif vir_entity.dxf.color == 5:
                            side2_lines.append(LineString(vir_entity.get_points("xy")))

        return {
            "FRONT":front_lines,
            "REAR":rear_lines,
            "SIDE1":side1_lines,
            "SIDE2":side2_lines,
        }

    def layertextPolyDict(self,text_entities,polyentities):

        closed_polygons=[cy_poly for cy_poly in polyentities if cy_poly.closed and len(cy_poly.get_points("xy"))>3]

        res_dict=dict()
        for polygon in closed_polygons:
            check_arc=[ent for ent in polygon.virtual_entities() if ent.dxftype()=="ARC"]
            if len(check_arc)>1:
                continue
            polygon_points=Polygon(polygon.get_points("xy"))
            handle= polygon.dxf.handle
            asigned_label=None
            for text_entity in text_entities:

                text= text_entity.dxf.text if text_entity.dxftype()=="TEXT" else text_entity.plain_text()

                text_point=Point(text_entity.dxf.insert[0],text_entity.dxf.insert[1])
                if polygon_points.contains(text_point):
                    asigned_label= text
                    break

            if not asigned_label:

                print(f"Missing Label For #REF ({handle}) Polygon")
                continue

            res_dict[handle]=(asigned_label,polygon_points)

        return res_dict

    def clean_text_mtext_label(self,text_label: str):

        text = plain_mtext(text_label)
        text = text.strip().replace("\n", " ")
        return text

    def get_lengthAndWidth(self, polygon):
        if polygon.is_empty or polygon.area == 0:
            return 0.0, 0.0

        rect = polygon.minimum_rotated_rectangle
        if not hasattr(rect, "exterior"):  # Point or LineString fallback
            return 0.0, 0.0

        coords = list(rect.exterior.coords)
        edge1 = math.hypot(coords[1][0] - coords[0][0],
                           coords[1][1] - coords[0][1])
        edge2 = math.hypot(coords[2][0] - coords[1][0],
                           coords[2][1] - coords[1][1])
        return round(max(edge1, edge2),2), round(min(edge1, edge2),2)

    # def get_angle(self, line: LineString):
    #
    #     pts = list(line.coords)
    #
    #     if len(pts) < 2:
    #         return None
    #
    #     x1, y1 = pts[0]
    #     x2, y2 = pts[-1]
    #
    #     return math.degrees(
    #         math.atan2(y2 - y1, x2 - x1)
    #     )
    #
    # def get_sideofCy(self, margin_dict: dict, polygon):
    #
    #     center_angle = self.get_angle(centerline)
    #
    #     for side, lst_linestring in margin_dict.items():
    #
    #         for line in lst_linestring:
    #
    #             # Touching check
    #             if round(polygon.distance(line), 1) == 0.0:
    #
    #                 line_angle = self.get_angle(line)
    #
    #                 angle_diff = abs(center_angle - line_angle)
    #
    #                 if angle_diff > 180:
    #                     angle_diff = 360 - angle_diff
    #
    #                 # Same direction (parallel)
    #                 if angle_diff < 10 or abs(angle_diff - 180) < 10:
    #                     return side
    #
    #     return ""

    def get_angle(self, line: LineString):
        pts = list(line.coords)
        if len(pts) < 2:
            return None
        x1, y1 = pts[0]
        x2, y2 = pts[-1]
        return math.degrees(math.atan2(y2 - y1, x2 - x1))

    def get_polygon_angle(self, polygon):
        # Orientation = angle of the longest edge of the min rotated rectangle
        rect = polygon.minimum_rotated_rectangle
        coords = list(rect.exterior.coords)
        best_len, best_angle = -1, None
        for i in range(len(coords) - 1):
            x1, y1 = coords[i]
            x2, y2 = coords[i + 1]
            length = math.hypot(x2 - x1, y2 - y1)
            if length > best_len:
                best_len = length
                best_angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
        return best_angle

    def get_sideofCy(self, margin_dict: dict, polygon):
        polygon_angle = self.get_polygon_angle(polygon)
        if polygon_angle is None:
            return ""

        for side, lst_linestring in margin_dict.items():
            for line in lst_linestring:
                # Touching check
                if round(polygon.distance(line), 1) <= 0.2:
                    line_angle = self.get_angle(line)
                    if line_angle is None:
                        continue

                    angle_diff = abs(polygon_angle - line_angle)
                    if angle_diff > 180:
                        angle_diff = 360 - angle_diff

                    # Same direction (parallel, allowing 180° flip)
                    if angle_diff < 10 or abs(angle_diff - 180) < 10:
                        return side

        return ""

    def get_dir_ref_circle(self,polygon):

        resibua_center_pts = None
        floor_center_pts = None
        for resi_insert in self.resiinsert_query:

            for resi_vir_entity in resi_insert.virtual_entities():

                if resi_vir_entity.dxftype() == "CIRCLE":

                    resi_center_pts = (resi_vir_entity.dxf.center[0], resi_vir_entity.dxf.center[1])
                    resi_center_point = Point(resi_center_pts)

                    if polygon.contains(resi_center_point):
                        resibua_center_pts = resi_center_pts

        for floor_insert in self.floorinsert_query:

            for floor_vir_entity in floor_insert.virtual_entities():

                if floor_vir_entity.dxftype() == "CIRCLE":

                    floor_center_pts = (floor_vir_entity.dxf.center[0], floor_vir_entity.dxf.center[1])
                    floor_center_point = Point(floor_center_pts)

                    if polygon.contains(floor_center_point):
                        floor_center_pts = floor_center_pts
                        break

        return [resibua_center_pts,floor_center_pts]

    def get_bua_polygons(self,polygon):

        lst_bua_polygon=[]
        for bua_poly in self.buapoly_query:
            if not bua_poly.closed or len(bua_poly.get_points("xy"))<3:
                continue

            bua_polygon=Polygon(bua_poly.get_points("xy"))

            if polygon.contains(bua_polygon):
                lst_bua_polygon.append(bua_polygon)

        return lst_bua_polygon

    def get_matched_data(self,prop_label):
        prop_label=prop_label.lower().replace(" ","")
        bldg_data = self.layertextPolyDict(self.bldgtext_query, self.bldgpoly_query)

        for bldg_id,bldg_values in bldg_data.items():

            bldg_label=bldg_values[0].lower().replace(" ","")

            if prop_label == bldg_label:

                return bldg_id,bldg_values

        return None,()

    def get_moved_floor_topw_poly(self):
        prop_matched_dict=dict()
        proposedWork_data=self.layertextPolyDict(self.proposedworktext_query,self.proposedworkpoly_query)

        floor_data=self.layertextPolyDict(self.floortext_query,self.floorpoly_query)


        for pw_id,pw_values in proposedWork_data.items():

            get_pwdir_ref_circles=self.get_dir_ref_circle(pw_values[1])

            if not get_pwdir_ref_circles:

                print(f"Missing Direction Ref Ref Circle in #REF ({pw_id}) {pw_values[0]} _ProposedWork Layer.")

            bldg_id,bldg_values = self.get_matched_data(pw_values[0])

            if bldg_id is None or bldg_values==():
                print(f"{pw_values[0]} Not matching with Any _BuildingName Labels")
                continue

            pwresiPoint,pwfloorPoint=Point(get_pwdir_ref_circles[0]),Point(get_pwdir_ref_circles[1])

            propcenter_x, propcenter_y = pwresiPoint.coords.xy

            moved_floor_polygons=[]

            for floor_id,floor_values in floor_data.items():

                if bldg_values[1].contains(floor_values[1]):

                    get_bua_polygon=self.get_bua_polygons(floor_values[1])
                    bua_Polygon=None

                    if len(get_bua_polygon)==1:

                        bua_Polygon=get_bua_polygon[0]

                    elif len(get_bua_polygon)>1:

                        merged_polygons=[poly.buffer(0.2) for poly in get_bua_polygon]

                        bua_Polygon=unary_union(merged_polygons)

                    else:
                        print(f"Bua Polygon Not Found in #REF ({floor_id}) {floor_values[0]}")


                    if bua_Polygon:

                        get_flrdir_ref_circles = self.get_dir_ref_circle(bua_Polygon)

                        flrresiPoint, flrfloorPoint = Point(get_flrdir_ref_circles[0]), Point(get_flrdir_ref_circles[1])

                        flrcenter_x, flrcenter_y = flrresiPoint.coords.xy

                        propFloorCenter_pts = [(propcenter_x[0], propcenter_y[0]), (flrcenter_x[0], flrcenter_y[0])]

                        BothCenter_pts = np.array(propFloorCenter_pts)

                        maxBothCenter_pts = BothCenter_pts.max(axis=0)

                        minBothCenter_pts = BothCenter_pts.min(axis=0)

                        DistProp2FloorCeterpts = maxBothCenter_pts - minBothCenter_pts

                        print('Distance',DistProp2FloorCeterpts)

                        # --------------------------------first Quadrant For Floor Center Points--------------------------------

                        Floorcenterpts1stQuadrant = [round(flrcenter_x[0] + DistProp2FloorCeterpts[0], 3),
                                                     round(flrcenter_y[0] + DistProp2FloorCeterpts[1], 3)]

                        # print('First Quadrant Floor Center points',Floorcenterpts1stQuadrant)
                        # --------------------------------Second Quadrant For Floor Center Points--------------------------------

                        Floorcenterpts2ndQuadrant = [round(flrcenter_x[0] - DistProp2FloorCeterpts[0], 3),
                                                     round(flrcenter_y[0] - DistProp2FloorCeterpts[1], 3)]
                        # print('Second Quadrant Floor Center points', Floorcenterpts2ndQuadrant)
                        # --------------------------------Third Quadrant For Floor Center Points--------------------------------

                        Floorcenterpts3rdQuadrant = [round(flrcenter_x[0] + DistProp2FloorCeterpts[0], 3),
                                                     round(flrcenter_y[0] - DistProp2FloorCeterpts[1], 3)]
                        # print('Third Quadrant Floor Center points', Floorcenterpts3rdQuadrant)
                        # --------------------------------Fourth Quadrant For Floor Center Points--------------------------------

                        Floorcenterpts4thQuadrant = [round(flrcenter_x[0] - DistProp2FloorCeterpts[0], 3),
                                                     round(flrcenter_y[0] + DistProp2FloorCeterpts[1], 3)]
                        # print('Fourth Quadrant Floor Center points', Floorcenterpts4thQuadrant)

                        Proposed_WorkCenterPts = [round(propcenter_x[0], 3), round(propcenter_y[0], 3)]
                        print("xy",Proposed_WorkCenterPts,Floorcenterpts4thQuadrant)
                        if (Floorcenterpts1stQuadrant == Proposed_WorkCenterPts):

                            # ---------------------------------Moving Bua Polygon from floor to proposed work for first Quadrant-----------------------------

                            print('Matched First Quadrant')

                            if bua_Polygon is not None:

                                Moved_BUAPolygon_pts = []

                                for BUAX_pts, BUAY_pts in zip(bua_Polygon.exterior.xy[0],
                                                              bua_Polygon.exterior.xy[1]):
                                    BUA_pts = [BUAX_pts + DistProp2FloorCeterpts[0], BUAY_pts + DistProp2FloorCeterpts[1]]

                                    Moved_BUAPolygon_pts.append(BUA_pts)

                                MovedBuaPolygonPoints = Polygon(Moved_BUAPolygon_pts)
                                moved_floor_polygons.append(MovedBuaPolygonPoints)

                        elif (Floorcenterpts2ndQuadrant == Proposed_WorkCenterPts):

                            print('Matched Second Quadrant')

                            # ---------------------------------Moving Bua Polygon from floor to proposed work for Second Quadrant-----------------------------
                            if bua_Polygon is not None:

                                Moved_BUAPolygon_pts = []

                                for BUAX_pts, BUAY_pts in zip(bua_Polygon.exterior.xy[0],
                                                              bua_Polygon.exterior.xy[1]):
                                    BUA_pts = [BUAX_pts - DistProp2FloorCeterpts[0], BUAY_pts - DistProp2FloorCeterpts[1]]

                                    Moved_BUAPolygon_pts.append(BUA_pts)

                                MovedBuaPolygonPoints = Polygon(Moved_BUAPolygon_pts)
                                moved_floor_polygons.append(MovedBuaPolygonPoints)


                        elif (Floorcenterpts3rdQuadrant == Proposed_WorkCenterPts):

                            print('Matched Third Quadrant')

                            # ---------------------------------Moving Bua Polygon from floor to proposed work for Second Quadrant-----------------------------
                            if bua_Polygon is not None:

                                Moved_BUAPolygon_pts = []

                                for BUAX_pts, BUAY_pts in zip(bua_Polygon.exterior.xy[0],
                                                              bua_Polygon.exterior.xy[1]):
                                    BUA_pts = [BUAX_pts + DistProp2FloorCeterpts[0], BUAY_pts - DistProp2FloorCeterpts[1]]

                                    Moved_BUAPolygon_pts.append(BUA_pts)

                                MovedBuaPolygonPoints = Polygon(Moved_BUAPolygon_pts)
                                moved_floor_polygons.append(MovedBuaPolygonPoints)

                        elif (Floorcenterpts4thQuadrant == Proposed_WorkCenterPts):

                            print('Matched Fourth Quadrant')

                            # ---------------------------------Moving Bua Polygon from floor to proposed work for Second Quadrant-----------------------------
                            if bua_Polygon is not None:
                                print("bua_Polygon",bua_Polygon)
                                Moved_BUAPolygon_pts = []

                                for BUAX_pts, BUAY_pts in zip(bua_Polygon.exterior.xy[0],
                                                              bua_Polygon.exterior.xy[1]):

                                    BUA_pts = [BUAX_pts - DistProp2FloorCeterpts[0], BUAY_pts + DistProp2FloorCeterpts[1]]

                                    Moved_BUAPolygon_pts.append(BUA_pts)

                                MovedBuaPolygonPoints = Polygon(Moved_BUAPolygon_pts)

                                moved_floor_polygons.append(MovedBuaPolygonPoints)
                        else:

                            print('Does Not Matched in Any Quadrant')

            prop_matched_dict[pw_id]=unary_union([moved_poly.buffer(0.2) for moved_poly in moved_floor_polygons])

        return prop_matched_dict

    def get_construction_type(self,polygon,lst_moved_polygons):
        MIN_AREA=2.0
        for moved_poly in lst_moved_polygons:
            inter = polygon.intersection(moved_poly)
            if polygon.intersects(moved_poly) and inter.area>MIN_AREA:
                return "yes"
        return "no"

    def get_courtyard_details(self):

        courtyard_data= self.layertextPolyDict(self.courtyard_textquery,self.courtyard_polyquery)
        margine_data= self.getMargines()
        lst_moved_flr_polygons=self.get_moved_floor_topw_poly()

        lst_courtyard=[]
        for courtyard_id,courtyard_values in courtyard_data.items():
            js_courtyard = dict()
            plain_label = self.clean_text_mtext_label(courtyard_values[0])
            length, width= self.get_lengthAndWidth(courtyard_values[1])
            sideofpolygon=self.get_sideofCy(margine_data,courtyard_values[1])
            js_courtyard['COURTYARD_NAME'] = plain_label
            js_courtyard['COURTYARD_LENGTH'] = str(length)
            js_courtyard['COURTYARD_WIDTH'] = str(width)
            js_courtyard['COURTYARD_AREA'] = str(round(courtyard_values[1].area,2))
            js_courtyard['COURTYARD_SIDE'] =sideofpolygon
            js_courtyard['COURTYARD_CONSTRUCTION_TYPE'] =self.get_construction_type(courtyard_values[1],lst_moved_flr_polygons.values())

            lst_courtyard.append(js_courtyard)
        # print(lst_courtyard)
        return lst_courtyard


# if __name__=="__main__":
#     import os
#     import ezdxf
#
#     folder_path=r"G:\MyProjects\BPConnectProject\DXF_files"
#     filename="de611674b6a5cd15-PLOTNO9130PUDA.dxf"
#     try:
#         dxf_path=os.path.join(folder_path,filename)
#         dxf_file=ezdxf.readfile(dxf_path)
#         msp=dxf_file.modelspace()
#         courtyard_obj=CourtYardDetails(msp)
#         result= courtyard_obj.get_courtyard_details()
#         print("Result Of CourtYard:",result)
#     except Exception as e:
#
#         print(f"Error While Processing CourtYard Details: {e}")