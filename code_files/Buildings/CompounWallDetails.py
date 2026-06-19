from shapely.geometry import Polygon,Point,LineString
import re
import math
class CompoundWallDetails:

    def __init__(self,msp):

        self.msp= msp
        self.wc_poly_entities=self.msp.query("LWPOLYLINE[layer=='_CompoundWall']")
        self.wc_text_entities=self.msp.query("TEXT MTEXT[layer=='_CompoundWall']")
        self.margins_entities=self.msp.query("LINE LWPOLYLINE INSERT[layer=='_MarginLine']")

    def layertextPolyDict(self):

        closed_polygons=[wall_poly for wall_poly in self.wc_poly_entities if wall_poly.closed and len(wall_poly.get_points("xy"))>3]

        center_polylines=[wall_center_line for wall_center_line in self.wc_poly_entities if not wall_center_line.closed and wall_center_line.dxf.linetype.lower()=="center"]

        res_dict=dict()
        for polygon in closed_polygons:
            check_arc=[ent for ent in polygon.virtual_entities() if ent.dxftype()=="ARC"]
            if len(check_arc)>1:
                continue
            polygon_points=Polygon(polygon.get_points("xy"))
            handle= polygon.dxf.handle
            asigned_label=None
            for text_entity in self.wc_text_entities:

                text= text_entity.dxf.text if text_entity.dxftype()=="TEXT" else text_entity.plain_text()

                text_point=Point(text_entity.dxf.insert[0],text_entity.dxf.insert[1])

                if "wall" in text.lower():
                    if polygon_points.contains(text_point):
                        asigned_label= text
                        break

            if not asigned_label:

                print(f"Missing Label For #REF ({handle}) Polygon")
                continue

            lst_center_polylines = [polyline for polyline in center_polylines if all(round(polygon_points.distance(Point(point)),1)==0.0 for point in polyline.get_points("xy"))]
            if not lst_center_polylines:
                print(f"Missing CenterLine For #REF ({handle}) Polygon")
                continue

            res_dict[handle]=(asigned_label,polygon_points,lst_center_polylines[0])

        return res_dict

    def getMargines(self):

        front_lines=[]
        rear_lines=[]
        side1_lines=[]
        side2_lines=[]
        for entity in self.margins_entities:

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

    def get_height(self,inputText: str, startDelimeter: None, endDelimeter: 'h'):

        height_value = 0.0

        if (inputText is None or len(inputText) == 0):

            return height_value
        else:
            # any digit patterns
            numeric_const_pattern = '[-+]? (?: (?: \d* \. \d+ ) | (?: \d+ \.? ) )(?: [Ee] [+-]? \d+ ) ?'
            rx = re.compile(numeric_const_pattern, re.VERBOSE)

            # check if u can find the start and end delimeters
            if (startDelimeter is not None and len(startDelimeter) > 0):
                start_idx = inputText.find(startDelimeter)
            else:
                start_idx = 0

            end_idx = inputText.find(endDelimeter)

            sub_text = inputText[start_idx:end_idx]

            height_tmp = rx.findall(sub_text)

            if (len(height_tmp) > 0):
                # return the index[0] value
                return height_tmp[0]
            else:

                print(f"Unable to extract height value from :: {inputText} - Returning default value {height_value}")
                return height_value

    def get_grill_height(self,polygon):

        for text_entity in self.wc_text_entities:

            text = text_entity.dxf.text if text_entity.dxftype() == "TEXT" else text_entity.plain_text()

            text_point = Point(text_entity.dxf.insert[0], text_entity.dxf.insert[1])

            if "grill" in text.lower():
                if polygon.contains(text_point):
                    return self.get_height(text,None,"h")

        return "0.0"

    # def get_sideofCw(self,margin_dict:dict,polygon,centerline):
    #
    #
    #     for side,lst_linestring in margin_dict.items():
    #
    #         for line in lst_linestring:
    #             if round(polygon.distance(line),1)==0.0:
    #                 return side
    #     return ""

    # def get_angle(self, lwpolyline):
    #     pts = list(lwpolyline.)
    #
    #     if len(pts) < 2:
    #         return None
    #
    #     x1, y1 = pts[0]
    #     x2, y2 = pts[-1]
    #
    #     return math.degrees(math.atan2(y2 - y1, x2 - x1))

    def get_angle(self, line: LineString):

        pts = list(line.coords)

        if len(pts) < 2:
            return None

        x1, y1 = pts[0]
        x2, y2 = pts[-1]

        return math.degrees(
            math.atan2(y2 - y1, x2 - x1)
        )

    def get_sideofCw(self, margin_dict: dict, polygon, centerline):

        center_angle = self.get_angle(centerline)

        for side, lst_linestring in margin_dict.items():

            for line in lst_linestring:

                # Touching check
                if round(polygon.distance(line), 1) == 0.0:

                    line_angle = self.get_angle(line)

                    angle_diff = abs(center_angle - line_angle)

                    if angle_diff > 180:
                        angle_diff = 360 - angle_diff

                    # Same direction (parallel)
                    if angle_diff < 10 or abs(angle_diff - 180) < 10:
                        return side

        return ""

    def get_WCdetails(self):
        res_lst=[]
        compoundwall_data=self.layertextPolyDict()
        print("Compound wall Data",len(compoundwall_data))
        margine_data=self.getMargines()
        print("Margine data",margine_data)
        for wall_id,wall_val in compoundwall_data.items():
            center_line=LineString(wall_val[2].get_points("xy"))
            wall_height=self.get_height(wall_val[0],None,"h")
            wall_length=round(center_line.length,2)
            grill_height= self.get_grill_height(wall_val[1])
            sideofcw=self.get_sideofCw(margine_data,wall_val[1],center_line)

            js_compoundWallInfo = dict()
            js_compoundWallInfo['COMPOUND_WALL_ID'] = wall_id
            js_compoundWallInfo['COMPOUND_WALL_NAME'] = wall_val[0]
            js_compoundWallInfo['C_WALL_HEIGHT'] = str(wall_height)
            js_compoundWallInfo['C_WALL_LENGTH'] = str(round(wall_length,2))
            js_compoundWallInfo['C_WALL_SIDE'] = sideofcw
            js_compoundWallInfo['GRILL_HEIGHT'] = grill_height

            res_lst.append(js_compoundWallInfo)
        return res_lst


# if __name__=="__main__":
#
#     import ezdxf
#     import os
#
#     folder_path="G:\MyProjects\BPConnectProject\BPConnectAPI\DXF_files"
#     file_name="7b21ddefa57e4005-pudaclubhouse.dxf"
#     try:
#         file_path=os.path.join(folder_path,file_name)
#         read_file=ezdxf.readfile(file_path)
#         msp=read_file.modelspace()
#
#         compoundwall_obj=CompoundWallDetails(msp)
#
#         print(f"RES:{compoundwall_obj.get_WCdetails()}")
#
#     except Exception as e:
#
#         print(e)