# ------------------------------------------------Modules-------------------------------------------------

# Converting UnLayered Data into Layered Data

import os
from shapely.geometry import LineString
from shapely.geometry import Point, Polygon
import ezdxf
import re

class MainRoadInternalRoadWidth:

    def split(self,start, end, seg):  # this function used for Spliting the lines

        x_delta = (end[0] - start[0]) / float(seg)

        y_delta = (end[1] - start[1]) / float(seg)

        points = []

        for i in range(1, seg):

            pts = (start[0] + i * x_delta, start[1] + i * y_delta)

            points.append(pts)

        return [start] + points + [end]

    def FindMainRoadWidth(self,mainroad_string):

        # Use regular expression to find floating-point values
        floating_values = re.findall(r'\d+\.\d+', mainroad_string)

        # Convert the extracted values to float
        floating_values = [float(value) for value in floating_values]

        #min_rect = mainroad_polygon.minimum_rotated_rectangle

        #x,y=min_rect.exterior.coords.xy

        #bound_dist=[LineString([(x[0],y[0]),(x[1],y[1])]).length,LineString([(x[1],y[1]),(x[2],y[2])]).length]

        return round(min(floating_values),2)

    def CalculateWidthOFPolygon(self,polygon_pts, center_line_pts):

        center_line_pts = [[center_line_pts[i], center_line_pts[i + 1]] for i in range(len(center_line_pts) - 1)]

        splitted_points = [self.split(center_line[0], center_line[1], 10) for center_line in center_line_pts]

        # print(splitted_points)

        polygon_line_pts = [[polygon_pts[i], polygon_pts[i + 1]] for i in range(len(polygon_pts) - 1)]
        # print(polygon_line_pts)
        polygon_width = []

        for center_pts in splitted_points[0][5:-4]:

            center_point = Point(center_pts)

            for polygon_line in polygon_line_pts:

                polygon_line_points = LineString(polygon_line)

                if round(center_point.distance(polygon_line_points), 1) > 1.0:

                    polygon_width.append(round(center_point.distance(polygon_line_points), 2) * 2)

        return min(polygon_width)

    # def calculate_min_width(self,polygon_vertices):
    #
    #     # Calculate the convex hull of the polygon
    #     hull = ConvexHull(polygon_vertices)
    #
    #     # Extract the vertices of the convex hull
    #     hull_vertices = np.array([polygon_vertices[i] for i in hull.vertices])
    #
    #     # Calculate the distances between opposite edges of the convex hull
    #     distances = []
    #     for i in range(len(hull_vertices) - 1):
    #         for j in range(i + 1, len(hull_vertices)):
    #             dist = np.linalg.norm(hull_vertices[i] - hull_vertices[j])
    #             distances.append(dist)
    #
    #     min_width = np.min(distances)
    #
    #     return round(min_width,2)

    # def FindInternalRoadWidth(self,internalroad_polygon,internalroad_center_line):
    #
    #     total_distance=[]
    #
    #     for vi_entity in internalroad_center_line.virtual_entities():
    #
    #         if vi_entity.dxftype()=='LINE':
    #
    #             start_point=[vi_entity.dxf.start[0],vi_entity.dxf.start[1]]
    #
    #             end_point=[vi_entity.dxf.end[0],vi_entity.dxf.end[1]]
    #
    #             split_into_segments=self.split(start_point,end_point,4)
    #
    #             splited_point=Point(split_into_segments[2:-2])
    #
    #             for polygon_line in internalroad_polygon.virtual_entities():
    #
    #                 if polygon_line.dxftype()=='LINE':
    #
    #                     polygon_line_start_point=[polygon_line.dxf.start[0],polygon_line.dxf.start[1]]
    #
    #                     polygon_line_end_point=[polygon_line.dxf.end[0],polygon_line.dxf.end[1]]
    #
    #                     polygon_line_points=LineString([polygon_line_start_point,polygon_line_end_point])
    #
    #                     if round(splited_point.distance(polygon_line_points),1)>1.0:
    #
    #                         total_distance.append(round(splited_point.distance(polygon_line_points),2))
    #
    #     return round(min(total_distance)*2,2)

    def InternalRoadData(self,InternalRoadEntities):

        internalroad_dict=dict()

        for internalroad_entity in InternalRoadEntities:

            if internalroad_entity.dxftype() == 'TEXT' or internalroad_entity.dxftype() == 'MTEXT':

                internalroad_id = internalroad_entity.dxf.handle
                #print(internalroad_id)
                internalroad_label = internalroad_entity.dxf.text if internalroad_entity.dxftype() == 'TEXT' else internalroad_entity.plain_text()

                internalroad_label_point = Point([internalroad_entity.dxf.insert[0], internalroad_entity.dxf.insert[1]])

                LabelContain_poly_center_line=[]

                for internalroad_polyline_entity in InternalRoadEntities:

                    internalroad_polyline_entity_id = internalroad_polyline_entity.dxf.handle

                    if internalroad_polyline_entity.dxftype() == 'LWPOLYLINE' and internalroad_polyline_entity.closed == True:

                        internalroad_polyline_points = Polygon([ip[0:2] for ip in internalroad_polyline_entity.get_points()])

                        if internalroad_polyline_points.contains(internalroad_label_point) == True or round(internalroad_polyline_points.distance(internalroad_label_point), 1) == 0.0:

                            for internalroad_center_polyline_entity in InternalRoadEntities:

                                if internalroad_center_polyline_entity.dxftype()=='LWPOLYLINE' and internalroad_center_polyline_entity.closed == False and str(internalroad_center_polyline_entity.dxf.linetype).lower()=='center':

                                    center_line_pts=[ircp[0:2] for ircp in internalroad_center_polyline_entity.get_points()]

                                    check_centerline_points_in_polygon=all(internalroad_polyline_points.contains(Point(center_pts)) == True or round(internalroad_polyline_points.distance(Point(center_pts)), 1) == 0.0 for center_pts in center_line_pts )== True

                                    if check_centerline_points_in_polygon:

                                        #print([ip[0:2] for ip in internalroad_polyline_entity.get_points()])
                                        # print(internalroad_id,internalroad_polyline_entity_id)
                                        LabelContain_poly_center_line.append([internalroad_polyline_entity_id,internalroad_label,internalroad_polyline_entity,internalroad_center_polyline_entity])

                if LabelContain_poly_center_line!=[] and len(LabelContain_poly_center_line)!=0:

                    for internalroad_data in LabelContain_poly_center_line:

                        internalroad_dict[internalroad_data[0]]=internalroad_data

        return internalroad_dict

    def MainRoadData(self,MainRoadEntities):

        mainroad_dict=dict()

        for mainroad_polyline_entity in MainRoadEntities:

            internalroad_polyline_entity_id = mainroad_polyline_entity.dxf.handle

            if mainroad_polyline_entity.dxftype() == 'LWPOLYLINE' and mainroad_polyline_entity.closed == True:

                mainroad_polyline_points = Polygon([mp[0:2] for mp in mainroad_polyline_entity.get_points()])
                #print([mp[0:2] for mp in mainroad_polyline_entity.get_points()])
                LabelContainPoly=[]

                for mainroad_entity in MainRoadEntities:

                    if mainroad_entity.dxftype()=='TEXT' or mainroad_entity.dxftype()=='MTEXT':

                        mainroad_id=mainroad_entity.dxf.handle

                        mainroad_label=mainroad_entity.dxf.text if mainroad_entity.dxftype()=='TEXT' else mainroad_entity.plain_text()

                        mainroad_label_point=Point([mainroad_entity.dxf.insert[0],mainroad_entity.dxf.insert[1]])

                        if mainroad_polyline_points.contains(mainroad_label_point)==True or round(mainroad_polyline_points.distance(mainroad_label_point),1)==0.0:

                            LabelContainPoly.append([internalroad_polyline_entity_id,mainroad_label,mainroad_polyline_entity])

                if LabelContainPoly!=[] and len(LabelContainPoly)!=0:

                    for mainroad_data in LabelContainPoly:

                        mainroad_dict[mainroad_data[0]]=mainroad_data

        return mainroad_dict

    def CalculateWidth(self, msp):

        returnResponse = dict()

        #ErrorMessage = []

        if (msp is None):

            returnResponse['code'] = -1

            returnResponse['errors'] = 'Missing Modelspace'

            return returnResponse

        try:

            print('Loading Modelspace File ...')

            MainRoad_data = msp.query('*[layer=="_MainRoad"]')

            MainRoadDict=self.MainRoadData(MainRoad_data)

            InternalRoad_data = msp.query('*[layer=="_InternalRoad"]')

            InternalRoadDict = self.InternalRoadData(InternalRoad_data)

            MainRoadTouchWithInternalRoad=[]

            for mroad_id_label_poly in MainRoadDict.values():

                mainroad_polygon_points=Polygon([mp[0:2] for mp in mroad_id_label_poly[2].get_points()])
                #print([mp[0:2] for mp in mroad_id_label_poly[2].get_points()])
                for iroad_id_label_poly_centerpoly in InternalRoadDict.values():

                    internalroad_polygon_points=Polygon([ip[0:2] for ip in iroad_id_label_poly_centerpoly[2].get_points()])
                    #print([ip[0:2] for ip in iroad_id_label_poly_centerpoly[2].get_points()])
                    if mainroad_polygon_points.touches(internalroad_polygon_points)==True or round(mainroad_polygon_points.distance(internalroad_polygon_points),1)==0.0:

                        internal_road_pts=[ip[0:2] for ip in iroad_id_label_poly_centerpoly[2].get_points()]

                        internalroad_width=self.CalculateWidthOFPolygon(internal_road_pts,iroad_id_label_poly_centerpoly[3])

                        MainRoadWidth=self.FindMainRoadWidth(mroad_id_label_poly[1]) if self.FindMainRoadWidth(mroad_id_label_poly[1]) is not None else 0.0

                        tmp_dict = dict()

                        tmp_dict['MAIN_ROAD_ID']=mroad_id_label_poly[0]

                        tmp_dict['MAIN_ROAD_LABEL']=mroad_id_label_poly[1]

                        tmp_dict['MAIN_ROAD_WIDTH']=str(MainRoadWidth)

                        tmp_dict['INTERNAL_ROAD_ID'] = iroad_id_label_poly_centerpoly[0]

                        tmp_dict['INTERNAL_ROAD_LABEL'] = iroad_id_label_poly_centerpoly[1]

                        tmp_dict['INTERNAL_ROAD_WIDTH'] = str(internalroad_width)

                        MainRoadTouchWithInternalRoad.append(tmp_dict)

            returnResponse['code'] = 0

            returnResponse['data'] = MainRoadTouchWithInternalRoad


        except IOError as ioe:

            errMsg = f'Not a DXF file or a generic I/O error.' + str(ioe)

            print(errMsg)

            #print(traceback.format_exc())

            returnResponse['code'] = 1

            returnResponse['errors'] = errMsg

            return returnResponse

        except ezdxf.DXFStructureError as dse:

            errMsg = f'Invalid or corrupted DXF file.' + str(dse)

            print(errMsg)

            #print(traceback.format_exc())

            returnResponse['code'] = 1

            returnResponse['errors'] = errMsg

            return returnResponse

        except Exception as excp:

            errMsg = f'Generic Exception .' + str(excp)

            print(errMsg)

            #print(traceback.format_exc())

            returnResponse['code'] = 1

            returnResponse['errors'] = errMsg

            return returnResponse

        finally:

            print('Processes completed ')

        return returnResponse


# --------------------------------------------------------------Input Of DXF File-----------------------------------------------
## folder="C:/Users/Viswa/Desktop/DXFAutoCad"
#folder = "E:/production_code/dxf_files/OpenLayout/"

#filename = "f2a09400bc22b4-TS_077878_2023.dxf"

#from datetime import datetime

#start_time = datetime.now()

#t1 = start_time.strftime("%H:%M:%S")

#first_start_time = datetime.strptime(t1, "%H:%M:%S")

#dxf_path = os.path.join(folder, filename)

#read_dxf = ezdxf.readfile(dxf_path)

#msp = read_dxf.modelspace()

#findingwidth = MainRoadInternalRoadWidth()

#response = findingwidth.CalculateWidth(msp)

#print(f'Width Of MainRoad And InternalRoad When Touch Both:{response}')

#end_time = datetime.now()

#t2 = end_time.strftime("%H:%M:%S")

#last_end_time = datetime.strptime(t2, "%H:%M:%S")

#total_time = last_end_time - first_start_time

#print(f'Total Time is:{total_time}')