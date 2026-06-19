import os

import ezdxf

from shapely.geometry import Point,Polygon,MultiPolygon

from shapely.geometry import LineString

import numpy as np

import shapely.geometry

from shapely.ops import unary_union
from timeit import default_timer as timer

def check_floor_wise_setbacks(msp):#folder:str,filename:str):

    returnValueDict=dict()

    resultsList=[]

    if (msp is None):#folder is None or filename is None):

        return resultsList

    #dxf_path=os.path.join(folder,filename)

    try:

        #read_dxf=ezdxf.readfile(dxf_path)

        #print('read file')

        #msp=read_dxf.modelspace()
        startTimer=timer()
        #For Proposed Work polygon
        txtPropWorkList=msp.query('TEXT[layer=="_ProposedWork"]')
        lwpolyPropWorkList=msp.query('LWPOLYLINE[layer=="_ProposedWork"]')
        insResiBuaList=msp.query('INSERT[layer=="_ResiBUAOutline"]')
        lwpolyResiBuaList=msp.query('LWPOLYLINE[layer=="_ResiBUAOutline"]')

        txtBldgList=msp.query('TEXT[layer=="_BuildingName"]')
        lwpolyBldgList=msp.query('LWPOLYLINE[layer=="_BuildingName"]')
        txtFloorList=msp.query('TEXT[layer=="_Floor"]')
        lwpolyFloorList=msp.query('LWPOLYLINE[layer=="_Floor"]')
        lwpolyCommBuaList=msp.query('LWPOLYLINE[layer=="_CommBUAOutline"]')
        lwpolyBalconyList=msp.query('LWPOLYLINE[layer=="_Balcony"]')
        insMarginLineList=msp.query('INSERT[layer=="_MarginLine"]')

        for prop_work_text in txtPropWorkList:#msp.query('TEXT[layer=="_ProposedWork"]'):

            prop_work_attrib=prop_work_text.dxfattribs()

            insert_prop_work=prop_work_attrib.get('insert')

            prop_work_name=prop_work_attrib.get('text')

            insert_prop_work_pts=[insert_prop_work[0],insert_prop_work[1]]

            np_insert_prop_work_pts=np.array(insert_prop_work_pts).round(1)

            abs_np_insert_prop_work_pts=abs(np_insert_prop_work_pts)

            prop_work_text_point=Point(abs_np_insert_prop_work_pts)

            for prop_work_polygon in lwpolyPropWorkList:#msp.query('LWPOLYLINE[layer=="_ProposedWork"]'):

                prop_work_polygon_pts=[pp[0:2] for pp in prop_work_polygon.get_points()]

                np_prop_work_polygon_pts=np.array(prop_work_polygon_pts).round(1)

                abs_np_prop_work_polygon_pts=abs(np_prop_work_polygon_pts)

                prop_work_polygon_point=Polygon(abs_np_prop_work_polygon_pts)

                if prop_work_polygon_point.contains(prop_work_text_point)==True or prop_work_polygon_point.touches(prop_work_text_point)==True:

                        filter_prop_name="".join(x for x in prop_work_name if x.isalpha())

                        prop_work_bounding_box=prop_work_polygon_point.minimum_rotated_rectangle

                        x,y=prop_work_bounding_box.exterior.coords.xy

                        prop_work_bounding_box_edge_length=(Point(x[0],y[0]).distance(Point(x[1],y[1])),Point(x[1],y[1]).distance(Point(x[2],y[2])))

                        np_prop_work_bounding_box_edge_length=np.array(prop_work_bounding_box_edge_length).round(0)

                        abs_np_prop_work_bounding_box_edge_length=abs(np_prop_work_bounding_box_edge_length)

                        #print(abs_np_prop_work_bounding_box_edge_length)

                        #resibua ref circle center points

                        for prop_resibua_insert in insResiBuaList:#msp.query('INSERT[layer=="_ResiBUAOutline"]'):

                            for prop_resibua_circle in prop_resibua_insert.virtual_entities():

                                if prop_resibua_circle.dxftype()=='CIRCLE':

                                    prop_resibua_circle_center=prop_resibua_circle.dxf.center

                                    prop_resibua_circle_center_pts=[prop_resibua_circle_center[0],prop_resibua_circle_center[1]]

                                    prop_np_resibua_circle_center_pts=np.array(prop_resibua_circle_center_pts).round(1)

                                    prop_abs_np_resibua_circle_center_pts=abs(prop_np_resibua_circle_center_pts)

                                    prop_resibua_circle_center_points=Point(prop_abs_np_resibua_circle_center_pts)

                                    if prop_work_polygon_point.contains(prop_resibua_circle_center_points)==True:

                                        #print(prop_abs_np_resibua_circle_center_pts)

                                        for building_text in txtBldgList:#msp.query('TEXT[layer=="_BuildingName"]'):

                                           building_text_attribs=building_text.dxfattribs()

                                           insert_building_text_pts=building_text_attribs.get('insert')

                                           building_text_name=building_text_attribs.get('text')

                                           building_text_pts=[insert_building_text_pts[0],insert_building_text_pts[1]]

                                           np_building_text_pts=np.array(building_text_pts).round(1)

                                           abs_np_building_text_pts=abs( np_building_text_pts)

                                           building_text_points=Point(abs_np_building_text_pts)

                                           for building_polygon in lwpolyBldgList:#msp.query('LWPOLYLINE[layer=="_BuildingName"]'):

                                               building_polygon_pts=[bp[0:2] for bp in building_polygon.get_points()]

                                               building_ref_id=building_polygon.dxf.handle

                                               np_building_polygon_pts=np.array(building_polygon_pts).round(1)

                                               abs_np_building_polygon_pts=abs(np_building_polygon_pts)

                                               building_polygon_points=Polygon(abs_np_building_polygon_pts)

                                               if building_polygon_points.contains(building_text_points)==True or building_polygon_points.touches(building_text_points)==True:

                                                   filter_building_name="".join(y for y in building_text_name if y.isalpha())

                                                   if filter_prop_name==filter_building_name:

                                                        #print(building_text_name)

                                                        building_value_dict=dict()
                                                        floor_value_list=[]

                                                        for floor_text in txtFloorList:#msp.query('TEXT[layer=="_Floor"]'):

                                                            floor_text_attrib=floor_text.dxfattribs()

                                                            if ('CELLAR' not in floor_text_attrib.get('text')) and ('BASEMENT' not in floor_text_attrib.get('text')) :

                                                                insert_floor_text=floor_text_attrib.get('insert')

                                                                floor_text_name=floor_text_attrib.get('text')

                                                                floor_text_pts=[insert_floor_text[0],insert_floor_text[1]]

                                                                np_floor_text_pts=np.array(floor_text_pts).round(1)

                                                                abs_np_floor_text_pts=abs(np_floor_text_pts)

                                                                floor_text_point=Point(abs_np_floor_text_pts)

                                                                for floor_polygon in lwpolyFloorList:#msp.query('LWPOLYLINE[layer=="_Floor"]'):

                                                                    floor_polygon_pts=[fp[0:2] for fp in floor_polygon.get_points()]

                                                                    floor_polygon_ref_id=floor_polygon.dxf.handle

                                                                    np_floor_polygon_pts=np.array(floor_polygon_pts).round(1)

                                                                    abs_np_floor_polygon_pts=abs(np_floor_polygon_pts)

                                                                    floor_polygon_point=Polygon(abs_np_floor_polygon_pts)

                                                                    if floor_polygon_point.contains(floor_text_point)==True or floor_polygon_point.touches(floor_text_point)==True :

                                                                        if building_polygon_points.contains(floor_polygon_point)==True:

                                                                             tot_front_data=[]

                                                                             tot_rear_data=[]

                                                                             tot_side1_data=[]

                                                                             tot_side2_data=[]

                                                                             #for CommercialBuaoutline layer

                                                                             for commbua_polygon in lwpolyCommBuaList:#msp.query('LWPOLYLINE[layer=="_CommBUAOutline"]'):

                                                                                 commbua_outline=[cp[0:2] for cp in commbua_polygon.get_points()]

                                                                                 np_commbua_outline=np.array(commbua_outline).round(1)

                                                                                 abs_np_commbua_outline=abs(np_commbua_outline)

                                                                                 commbua_outline_point=Polygon(abs_np_commbua_outline)

                                                                                 commbua_bounding_box=commbua_outline_point.minimum_rotated_rectangle

                                                                                 x2,y2=commbua_bounding_box.exterior.coords.xy

                                                                                 commbua_bounding_box_length=(Point(x2[0],y2[0]).distance(Point(x2[1],y2[1])),Point(x2[1],y2[1]).distance(Point(x2[2],y2[2])))

                                                                                 np_commbua_bounding_box_length=np.array(commbua_bounding_box_length).round(0)

                                                                                 # check commercial polygon in floor polygon

                                                                                 if floor_polygon_point.contains(commbua_outline_point)==True:

                                                                                     comm_list_balcony_polygon=[]

                                                                                     # for balcony layer

                                                                                     for comm_balcony_polygon in lwpolyBalconyList:#msp.query('LWPOLYLINE[layer=="_Balcony"]'):

                                                                                         comm_balcony_polygon_pts=[bp[0:2] for bp in comm_balcony_polygon.get_points()]

                                                                                         comm_np_balcony_polygon_pts=np.array(comm_balcony_polygon_pts).round(1)

                                                                                         abs_comm_np_balcony_polygon_pts=abs(comm_np_balcony_polygon_pts)

                                                                                         comm_balcony_polygon_points=Polygon(abs_comm_np_balcony_polygon_pts)

                                                                                         if floor_polygon_point.contains(comm_balcony_polygon_points)==True or floor_polygon_point.touches(comm_balcony_polygon_points)==True:

                                                                                             comm_list_balcony_polygon.append(comm_balcony_polygon_points)

                                                                                     #print(list_balcony_polygon)

                                                                                     comm_list_balcony_polygon_pts=MultiPolygon(comm_list_balcony_polygon)

                                                                                     comm_both_polygons=[commbua_outline_point,comm_list_balcony_polygon_pts]

                                                                                     #merge the polygon

                                                                                     comm_merge_polygon=unary_union(comm_both_polygons)

                                                                                     #print(merge_polygon.exterior.coords.xy)

                                                                                     #create bounding box
                                                                                     comm_merge_polygon_bounding_box=comm_merge_polygon.minimum_rotated_rectangle

                                                                                     x3,y3=comm_merge_polygon_bounding_box.exterior.coords.xy

                                                                                     #bounding box points

                                                                                     comm_merge_polygon_pts=[[x3[0],y3[0]],[x3[1],y3[1]],[x3[2],y3[2]],[x3[3],y3[3]],[x3[4],y3[4]]]

                                                                                     comm_np_merge_polygon_pts=np.array(comm_merge_polygon_pts).round(1)

                                                                                     comm_abs_np_merge_polygon_pts=abs(comm_np_merge_polygon_pts)

                                                                                     #bounding box length and width

                                                                                     comm_merge_polygon_bounding_box_edge_length=(Point(x3[0],y3[0]).distance(Point(x3[1],y3[1])),Point(x3[1],y3[1]).distance(Point(x3[2],y3[2])))

                                                                                     comm_np_merge_polygon_bounding_box_edge_length=np.array(comm_merge_polygon_bounding_box_edge_length).round(0)

                                                                                     abs_comm_np_merge_polygon_bounding_box_edge_length=abs(comm_np_merge_polygon_bounding_box_edge_length)

                                                                                     #print(np_merge_polygon_bounding_box_edge_length)

                                                                                     #check proposed_work bounding box length and width same as merge polygon bounding box

                                                                                     if round(abs_np_prop_work_bounding_box_edge_length[0],1)==round(abs_comm_np_merge_polygon_bounding_box_edge_length[0],1) and round(abs_np_prop_work_bounding_box_edge_length[1],1)==round(abs_comm_np_merge_polygon_bounding_box_edge_length[1],1):

                                                                                         print(f'{floor_text_name} Same floor polygon as proposed work polygon')

                                                                                     else:

                                                                                         comm_merge_polygonx_points=Polygon(comm_abs_np_merge_polygon_pts)

                                                                                         #resibua center points

                                                                                         for commbua_insert in insResiBuaList:#msp.query('INSERT[layer=="_ResiBUAOutline"]'):

                                                                                             for commbua_circle in commbua_insert.virtual_entities():

                                                                                                 if commbua_circle.dxftype()=='CIRCLE':

                                                                                                     commbua_circle_center=commbua_circle.dxf.center

                                                                                                     commbua_circle_center_pts=[commbua_circle_center[0],commbua_circle_center[1]]

                                                                                                     np_commbua_circle_center_pts=np.array(commbua_circle_center_pts).round(1)

                                                                                                     abs_np_commbua_circle_center_pts=abs(np_commbua_circle_center_pts)

                                                                                                     commbua_circle_center_points=Point(abs_np_commbua_circle_center_pts)

                                                                                                     if floor_polygon_point.contains(commbua_circle_center_points)==True:

                                                                                                         #print(floor_text_name)

                                                                                                         comm_both_points=[prop_abs_np_resibua_circle_center_pts,abs_np_commbua_circle_center_pts]

                                                                                                         comm_np_both_points=np.array(comm_both_points).round(1)

                                                                                                         #print(comm_np_both_points)

                                                                                                         comm_max_np_both_points=comm_np_both_points.max(axis=0)

                                                                                                         #print(max_np_both_points)

                                                                                                         comm_min_np_both_points=comm_np_both_points.min(axis=0)

                                                                                                         #print(min_np_both_points)

                                                                                                         comm_distance_both_points=comm_max_np_both_points-comm_min_np_both_points

                                                                                                         #print(distance_both_points)

                                                                                                         comm_np_distance_both_points=np.array(comm_distance_both_points).round(1)

                                                                                                         abs_comm_np_distance_both_points=abs(comm_np_distance_both_points)

                                                                                                         comm_merge_polygon_list_pts1=[]

                                                                                                         comm_merge_polygon_list_pts2=[]

                                                                                                         comm_merge_polygon_list_pts3=[]

                                                                                                         comm_merge_polygon_list_pts4=[]

                                                                                                         # merge_polygon convert into points

                                                                                                         for comm_merge_polygon_pts in comm_abs_np_merge_polygon_pts:

                                                                                                             #-------------------first quadrant--------------------------------

                                                                                                             comm_merge_polygon_x_pts1=comm_merge_polygon_pts[0]+abs_comm_np_distance_both_points[0]

                                                                                                             comm_merge_polygon_y_pts1=comm_merge_polygon_pts[1]+abs_comm_np_distance_both_points[1]

                                                                                                             comm_merge_polygon_pts1=[comm_merge_polygon_x_pts1,comm_merge_polygon_y_pts1]

                                                                                                             #---------------------second quadrant----------------------------

                                                                                                             comm_merge_polygon_x_pts2=comm_merge_polygon_pts[0]-abs_comm_np_distance_both_points[0]

                                                                                                             comm_merge_polygon_y_pts2=comm_merge_polygon_pts[1]-abs_comm_np_distance_both_points[1]

                                                                                                             comm_merge_polygon_pts2=[comm_merge_polygon_x_pts2,comm_merge_polygon_y_pts2]

                                                                                                             #---------------------Third quadrant----------------------------

                                                                                                             comm_merge_polygon_x_pts3=comm_merge_polygon_pts[0]+abs_comm_np_distance_both_points[0]

                                                                                                             comm_merge_polygon_y_pts3=comm_merge_polygon_pts[1]-abs_comm_np_distance_both_points[1]

                                                                                                             comm_merge_polygon_pts3=[comm_merge_polygon_x_pts3,comm_merge_polygon_y_pts3]

                                                                                                             #----------------------Fourth quadrant-------------------------

                                                                                                             comm_merge_polygon_x_pts4=comm_merge_polygon_pts[0]-abs_comm_np_distance_both_points[0]

                                                                                                             comm_merge_polygon_y_pts4=comm_merge_polygon_pts[1]+abs_comm_np_distance_both_points[1]

                                                                                                             comm_merge_polygon_pts4=[comm_merge_polygon_x_pts4,comm_merge_polygon_y_pts4]

                                                                                                             comm_merge_polygon_list_pts1.append(comm_merge_polygon_pts1)

                                                                                                             comm_merge_polygon_list_pts2.append(comm_merge_polygon_pts2)

                                                                                                             comm_merge_polygon_list_pts3.append(comm_merge_polygon_pts3)

                                                                                                             comm_merge_polygon_list_pts4.append(comm_merge_polygon_pts4)

                                                                                                         #----------------center points moving 1st quadrant---------

                                                                                                         comm_merge_polygon_center_x_pts1=abs_np_commbua_circle_center_pts[0]+abs_comm_np_distance_both_points[0]

                                                                                                         comm_merge_polygon_center_y_pts1=abs_np_commbua_circle_center_pts[1]+abs_comm_np_distance_both_points[1]

                                                                                                         comm_merge_polygon_center_pts1=[comm_merge_polygon_center_x_pts1,comm_merge_polygon_center_y_pts1]

                                                                                                         comm_np_merge_polygon_center_pts1=np.array(comm_merge_polygon_center_pts1).round(1)

                                                                                                         abs_comm_np_merge_polygon_center_pts1=abs(comm_np_merge_polygon_center_pts1)

                                                                                                         #print(abs_comm_np_merge_polygon_center_pts1)

                                                                                                         #comm_merge_polygon_center1_points=Point(abs_comm_np_merge_polygon_center_pts1)

                                                                                                         #------------center points moving 2nd quadrant--------------

                                                                                                         comm_merge_polygon_center_x_pts2=abs_np_commbua_circle_center_pts[0]-abs_comm_np_distance_both_points[0]

                                                                                                         comm_merge_polygon_center_y_pts2=abs_np_commbua_circle_center_pts[1]-abs_comm_np_distance_both_points[1]

                                                                                                         comm_merge_polygon_center_pts2=[comm_merge_polygon_center_x_pts2,comm_merge_polygon_center_y_pts2]

                                                                                                         comm_np_merge_polygon_center_pts2=np.array(comm_merge_polygon_center_pts2).round(1)

                                                                                                         abs_comm_np_merge_polygon_center_pts2=abs(comm_np_merge_polygon_center_pts2)

                                                                                                         #print(abs_comm_np_merge_polygon_center_pts2)

                                                                                                         #comm_merge_polygon_center2_points=Point(abs_comm_np_merge_polygon_center_pts2)

                                                                                                         #--------------center points moving 3rd quadrant-----------------

                                                                                                         comm_merge_polygon_center_x_pts3=abs_np_commbua_circle_center_pts[0]+abs_comm_np_distance_both_points[0]

                                                                                                         comm_merge_polygon_center_y_pts3=abs_np_commbua_circle_center_pts[1]-abs_comm_np_distance_both_points[1]

                                                                                                         comm_merge_polygon_center_pts3=[comm_merge_polygon_center_x_pts3,comm_merge_polygon_center_y_pts3]

                                                                                                         comm_np_merge_polygon_center_pts3=np.array(comm_merge_polygon_center_pts3).round(1)

                                                                                                         abs_comm_np_merge_polygon_center_pts3=abs(comm_np_merge_polygon_center_pts3)

                                                                                                         #print(abs_comm_np_merge_polygon_center_pts3)

                                                                                                         #comm_merge_polygon_center3_points=Point(abs_comm_np_merge_polygon_center_pts3)

                                                                                                         #-----------------center points moving 4th quadrant--------------

                                                                                                         comm_merge_polygon_center_x_pts4=abs_np_commbua_circle_center_pts[0]-abs_comm_np_distance_both_points[0]

                                                                                                         comm_merge_polygon_center_y_pts4=abs_np_commbua_circle_center_pts[1]+abs_comm_np_distance_both_points[1]

                                                                                                         comm_merge_polygon_center_pts4=[comm_merge_polygon_center_x_pts4,comm_merge_polygon_center_y_pts4]

                                                                                                         comm_np_merge_polygon_center_pts4=np.array(comm_merge_polygon_center_pts4).round(1)

                                                                                                         abs_comm_np_merge_polygon_center_pts4=abs(comm_np_merge_polygon_center_pts4)

                                                                                                         #print(abs_comm_np_merge_polygon_center_pts4)

                                                                                                         #comm_merge_polygon_center4_points=Point(abs_comm_np_merge_polygon_center_pts4)

                                                                                                         comm_np_merge_polygon_list_pts1=np.array(comm_merge_polygon_list_pts1).round(1)

                                                                                                         abs_comm_np_merge_polygon_list_pts1=abs(comm_np_merge_polygon_list_pts1)

                                                                                                         #comm_merge_polygon1_points=Polygon(abs_comm_np_merge_polygon_list_pts1)

                                                                                                         comm_np_merge_polygon_list_pts2=np.array(comm_merge_polygon_list_pts2).round(1)

                                                                                                         abs_comm_np_merge_polygon_list_pts2=abs(comm_np_merge_polygon_list_pts2)

                                                                                                         #print(abs_comm_np_merge_polygon_list_pts2)

                                                                                                         #comm_merge_polygon2_points=Polygon(abs_comm_np_merge_polygon_list_pts2)

                                                                                                         comm_np_merge_polygon_list_pts3=np.array(comm_merge_polygon_list_pts3).round(1)

                                                                                                         abs_comm_np_merge_polygon_list_pts3=abs(comm_np_merge_polygon_list_pts3)

                                                                                                         #comm_merge_polygon3_points=Polygon(abs_comm_np_merge_polygon_list_pts3)

                                                                                                         comm_np_merge_polygon_list_pts4=np.array(comm_merge_polygon_list_pts4).round(1)

                                                                                                         abs_comm_np_merge_polygon_list_pts4=abs(comm_np_merge_polygon_list_pts4)

                                                                                                         #comm_merge_polygon4_points=Polygon(abs_comm_np_merge_polygon_list_pts4)

                                                                                                         comm_list_of_center_pts=[abs_comm_np_merge_polygon_center_pts1, abs_comm_np_merge_polygon_center_pts2, abs_comm_np_merge_polygon_center_pts3, abs_comm_np_merge_polygon_center_pts4]

                                                                                                         comm_np_merge_polygon_list=[abs_comm_np_merge_polygon_list_pts1,abs_comm_np_merge_polygon_list_pts2,abs_comm_np_merge_polygon_list_pts3,abs_comm_np_merge_polygon_list_pts4]

                                                                                                         for merge_polygon_center_pts in comm_list_of_center_pts:

                                                                                                              if prop_abs_np_resibua_circle_center_pts[0]==merge_polygon_center_pts[0] and prop_abs_np_resibua_circle_center_pts[1]==merge_polygon_center_pts[1]:

                                                                                                                  merge_polygon_center_points=Point(merge_polygon_center_pts)

                                                                                                                 # print(merge_polygon_center_points)

                                                                                                                  for comm_merge_poly_pts in comm_np_merge_polygon_list:

                                                                                                                      comm_merge_poly_points=Polygon(comm_merge_poly_pts)

                                                                                                                      if comm_merge_poly_points.contains(merge_polygon_center_points)==True:

                                                                                                                          # for margin layer

                                                                                                                          for comm_margin_insert in insMarginLineList:#msp.query('INSERT[layer=="_MarginLine"]'):

                                                                                                                              comm_front_value_data=[]

                                                                                                                              comm_prop_front_value_data=[]

                                                                                                                              comm_rear_value_data=[]

                                                                                                                              comm_prop_rear_value_data=[]

                                                                                                                              comm_side1_value_data=[]

                                                                                                                              comm_prop_side1_value_data=[]

                                                                                                                              comm_side2_value_data=[]

                                                                                                                              comm_prop_side2_value_data=[]

                                                                                                                              for comm_margin_entity in comm_margin_insert.virtual_entities():

                                                                                                                                  if comm_margin_entity.dxftype()=='LINE':

                                                                                                                                    if comm_margin_entity.dxf.color==1:

                                                                                                                                          comm_f_margin_line_start_pts=[comm_margin_entity.dxf.start[0],comm_margin_entity.dxf.start[1]]

                                                                                                                                          comm_f_margin_line_end_pts=[comm_margin_entity.dxf.end[0],comm_margin_entity.dxf.end[1]]

                                                                                                                                          comm_f_margin_line_pts=[comm_f_margin_line_start_pts,comm_f_margin_line_end_pts]

                                                                                                                                          comm_f_np_margin_line_pts=np.array(comm_f_margin_line_pts).round(1)

                                                                                                                                          comm_f_abs_np_margin_line_pts=abs(comm_f_np_margin_line_pts)

                                                                                                                                          #print(abs_np_margin_line_pts)

                                                                                                                                          comm_f_margin_line_points=LineString(comm_f_abs_np_margin_line_pts)


                                                                                                                                          if abs(round(comm_merge_poly_points.distance(comm_f_margin_line_points),1))>0.0:

                                                                                                                                              comm_front_value_data.append(abs(round(comm_merge_poly_points.distance(comm_f_margin_line_points),1)))


                                                                                                                                          if abs(round(prop_work_polygon_point.distance(comm_f_margin_line_points),1))>0.0:

                                                                                                                                              comm_prop_front_value_data.append(abs(round(prop_work_polygon_point.distance(comm_f_margin_line_points),1)))

                                                                                                                                    elif(comm_margin_entity.dxf.color==6):

                                                                                                                                          comm_r_margin_line_start_pts=[comm_margin_entity.dxf.start[0],comm_margin_entity.dxf.start[1]]

                                                                                                                                          comm_r_margin_line_end_pts=[comm_margin_entity.dxf.end[0],comm_margin_entity.dxf.end[1]]

                                                                                                                                          comm_r_margin_line_pts=[comm_r_margin_line_start_pts,comm_r_margin_line_end_pts]

                                                                                                                                          comm_r_np_margin_line_pts=np.array(comm_r_margin_line_pts).round(1)

                                                                                                                                          comm_r_abs_np_margin_line_pts=abs(comm_r_np_margin_line_pts)

                                                                                                                                          #print(abs_np_margin_line_pts)

                                                                                                                                          comm_r_margin_line_points=LineString(comm_r_abs_np_margin_line_pts)

                                                                                                                                          if abs(round(comm_merge_poly_points.distance(comm_r_margin_line_points),1))>0.0:

                                                                                                                                              comm_rear_value_data.append(abs(round(comm_merge_poly_points.distance(comm_r_margin_line_points),1)))


                                                                                                                                          if abs(round(prop_work_polygon_point.distance(comm_r_margin_line_points),1))>0.0:

                                                                                                                                              comm_prop_rear_value_data.append(abs(round(prop_work_polygon_point.distance(comm_r_margin_line_points),1)))

                                                                                                                                    elif(comm_margin_entity.dxf.color==5):

                                                                                                                                            comm_s1_margin_line_start_pts=[comm_margin_entity.dxf.start[0],comm_margin_entity.dxf.start[1]]

                                                                                                                                            comm_s1_margin_line_end_pts=[comm_margin_entity.dxf.end[0],comm_margin_entity.dxf.end[1]]

                                                                                                                                            comm_s1_margin_line_pts=[comm_s1_margin_line_start_pts,comm_s1_margin_line_end_pts]

                                                                                                                                            comm_s1_np_margin_line_pts=np.array(comm_s1_margin_line_pts).round(1)

                                                                                                                                            comm_s1_abs_np_margin_line_pts=abs(comm_s1_np_margin_line_pts)

                                                                                                                                            #print(abs_np_margin_line_pts)

                                                                                                                                            comm_s1_margin_line_points=LineString(comm_s1_abs_np_margin_line_pts)

                                                                                                                                            if abs(round(comm_merge_poly_points.distance(comm_s1_margin_line_points),1))>0.0:

                                                                                                                                                comm_side1_value_data.append(abs(round(comm_merge_poly_points.distance(comm_s1_margin_line_points),1)))


                                                                                                                                            if abs(round(prop_work_polygon_point.distance(comm_s1_margin_line_points),1))>0.0:

                                                                                                                                                comm_prop_side1_value_data.append(abs(round(prop_work_polygon_point.distance(comm_s1_margin_line_points),1)))

                                                                                                                                    elif(comm_margin_entity.dxf.color==104):

                                                                                                                                            comm_s2_margin_line_start_pts=[comm_margin_entity.dxf.start[0],comm_margin_entity.dxf.start[1]]

                                                                                                                                            comm_s2_margin_line_end_pts=[comm_margin_entity.dxf.end[0],comm_margin_entity.dxf.end[1]]

                                                                                                                                            comm_s2_margin_line_pts=[comm_s2_margin_line_start_pts,comm_s2_margin_line_end_pts]

                                                                                                                                            comm_s2_np_margin_line_pts=np.array(comm_s2_margin_line_pts).round(1)

                                                                                                                                            comm_s2_abs_np_margin_line_pts=abs(comm_s2_np_margin_line_pts)

                                                                                                                                            #print(abs_np_margin_line_pts)

                                                                                                                                            comm_s2_margin_line_points=LineString(comm_s2_abs_np_margin_line_pts)

                                                                                                                                            if abs(round(comm_merge_poly_points.distance(comm_s2_margin_line_points),1))>0.0:

                                                                                                                                                comm_side2_value_data.append(abs(round(comm_merge_poly_points.distance(comm_s2_margin_line_points),1)))

                                                                                                                                            if abs(round(prop_work_polygon_point.distance(comm_s2_margin_line_points),1))>0.0:

                                                                                                                                                comm_prop_side2_value_data.append(abs(round(prop_work_polygon_point.distance(comm_s2_margin_line_points),1)))

                                                                                                                              if (comm_front_value_data !=[]) and (comm_prop_front_value_data !=[]):

                                                                                                                                  tot_front_data.append(abs(round(min(comm_prop_front_value_data)-min(comm_front_value_data),1)))

                                                                                                                              if (comm_rear_value_data !=[]) and (comm_prop_rear_value_data !=[]):

                                                                                                                                  tot_rear_data.append(abs(round(min(comm_prop_rear_value_data)-min(comm_rear_value_data),1)))

                                                                                                                              if (comm_side1_value_data !=[]) and (comm_prop_side1_value_data !=[]):

                                                                                                                                  tot_side1_data.append(abs(round(min(comm_prop_side1_value_data)-min(comm_side1_value_data),1)))

                                                                                                                              if (comm_side2_value_data !=[]) and (comm_prop_side2_value_data !=[]):

                                                                                                                                  tot_side2_data.append(abs(round(min(comm_prop_side2_value_data)-min(comm_side2_value_data),1)))

                                                                            #for resibuaoutline layer

                                                                             for ressibua_polygon in lwpolyResiBuaList:#msp.query('LWPOLYLINE[layer=="_ResiBUAOutline"]'):

                                                                                 ressibua_outline=[rp[0:2] for rp in ressibua_polygon.get_points()]

                                                                                 np_ressibua_outline=np.array(ressibua_outline).round(1)

                                                                                 abs_np_ressibua_outline=abs(np_ressibua_outline)

                                                                                 ressibua_outline_point=Polygon(abs_np_ressibua_outline)

                                                                                 resibua_bounding_box=ressibua_outline_point.minimum_rotated_rectangle

                                                                                 x1,y1=resibua_bounding_box.exterior.coords.xy

                                                                                 resibua_bounding_box_length=(Point(x1[0],y1[0]).distance(Point(x1[1],y1[1])),Point(x1[1],y1[1]).distance(Point(x1[2],y1[2])))

                                                                                 np_resibua_bounding_box_length=np.array(resibua_bounding_box_length).round(0)

                                                                                 if floor_polygon_point.contains(ressibua_outline_point)==True:

                                                                                     list_balcony_polygon=[]

                                                                                     for balcony_polygon in lwpolyBalconyList:#msp.query('LWPOLYLINE[layer=="_Balcony"]'):

                                                                                         balcony_polygon_pts=[bp[0:2] for bp in balcony_polygon.get_points()]

                                                                                         np_balcony_polygon_pts=np.array(balcony_polygon_pts).round(1)

                                                                                         abs_np_balcony_polygon_pts=abs(np_balcony_polygon_pts)

                                                                                         balcony_polygon_points=Polygon(abs_np_balcony_polygon_pts)

                                                                                         if (floor_polygon_point.contains(balcony_polygon_points)==True or ressibua_outline_point.touches(balcony_polygon_points)==True) :

                                                                                             list_balcony_polygon.append(balcony_polygon_points)

                                                                                     #print(list_balcony_polygon)

                                                                                     list_balcony_polygon_pts=MultiPolygon(list_balcony_polygon)

                                                                                     both_polygons=[ressibua_outline_point,list_balcony_polygon_pts]

                                                                                     merge_polygon=unary_union(both_polygons)

                                                                                     #print(merge_polygon.exterior.coords.xy)

                                                                                     merge_polygon_bounding_box=merge_polygon.minimum_rotated_rectangle

                                                                                     x1,y1=merge_polygon_bounding_box.exterior.coords.xy

                                                                                     merge_polygon_pts=[[x1[0],y1[0]],[x1[1],y1[1]],[x1[2],y1[2]],[x1[3],y1[3]],[x1[4],y1[4]]]

                                                                                     np_merge_polygon_pts=np.array(merge_polygon_pts).round(1)

                                                                                     abs_np_merge_polygon_pts=abs(np_merge_polygon_pts)

                                                                                     merge_polygon_bounding_box_edge_length=(Point(x1[0],y1[0]).distance(Point(x1[1],y1[1])),Point(x1[1],y1[1]).distance(Point(x1[2],y1[2])))

                                                                                     np_merge_polygon_bounding_box_edge_length=np.array(merge_polygon_bounding_box_edge_length).round(0)

                                                                                     abs_np_merge_polygon_bounding_box_edge_length=abs(np_merge_polygon_bounding_box_edge_length)

                                                                                     #print(np_merge_polygon_bounding_box_edge_length)

                                                                                     if round(abs_np_prop_work_bounding_box_edge_length[0])==round(abs_np_merge_polygon_bounding_box_edge_length[0]) and round(abs_np_prop_work_bounding_box_edge_length[1])==round(abs_np_merge_polygon_bounding_box_edge_length[1]):

                                                                                         print(f'{floor_text_name} Same floor polygon as proposed work polygon')

                                                                                     else:

                                                                                         merge_polygon_points=Polygon(abs_np_merge_polygon_pts)

                                                                                         for resibua_insert in insResiBuaList:#msp.query('INSERT[layer=="_ResiBUAOutline"]'):

                                                                                             for resibua_circle in resibua_insert.virtual_entities():

                                                                                                 if resibua_circle.dxftype()=='CIRCLE':

                                                                                                     resibua_circle_center=resibua_circle.dxf.center

                                                                                                     resibua_circle_center_pts=[resibua_circle_center[0],resibua_circle_center[1]]

                                                                                                     np_resibua_circle_center_pts=np.array(resibua_circle_center_pts).round(1)

                                                                                                     abs_np_resibua_circle_center_pts=abs(np_resibua_circle_center_pts)

                                                                                                     resibua_circle_center_points=Point(abs_np_resibua_circle_center_pts)

                                                                                                     if floor_polygon_point.contains(resibua_circle_center_points)==True:


                                                                                                         both_points=[prop_abs_np_resibua_circle_center_pts,abs_np_resibua_circle_center_pts]

                                                                                                         np_both_points=np.array(both_points).round(1)
                                                                                                         #print(np_both_points)
                                                                                                         max_np_both_points=np_both_points.max(axis=0)
                                                                                                         #print(max_np_both_points)
                                                                                                         min_np_both_points=np_both_points.min(axis=0)
                                                                                                         #print(min_np_both_points)
                                                                                                         distance_both_points=max_np_both_points-min_np_both_points
                                                                                                         #print(distance_both_points)
                                                                                                         np_distance_both_points=np.array(distance_both_points).round(1)

                                                                                                         abs_np_distance_both_points=abs(np_distance_both_points)

                                                                                                         merge_polygon_list_pts1=[]

                                                                                                         merge_polygon_list_pts2=[]

                                                                                                         merge_polygon_list_pts3=[]

                                                                                                         merge_polygon_list_pts4=[]

                                                                                                         for merge_polygon_pts in abs_np_merge_polygon_pts:

                                                                                                             merge_polygon_x_pts1=merge_polygon_pts[0]+abs_np_distance_both_points[0]

                                                                                                             merge_polygon_y_pts1=merge_polygon_pts[1]+abs_np_distance_both_points[1]

                                                                                                             merge_polygon_pts1=[merge_polygon_x_pts1,merge_polygon_y_pts1]

                                                                                                             merge_polygon_x_pts2=merge_polygon_pts[0]-abs_np_distance_both_points[0]

                                                                                                             merge_polygon_y_pts2=merge_polygon_pts[1]-abs_np_distance_both_points[1]

                                                                                                             merge_polygon_pts2=[merge_polygon_x_pts2,merge_polygon_y_pts2]

                                                                                                             merge_polygon_x_pts3=merge_polygon_pts[0]+abs_np_distance_both_points[0]

                                                                                                             merge_polygon_y_pts3=merge_polygon_pts[1]-abs_np_distance_both_points[1]

                                                                                                             merge_polygon_pts3=[merge_polygon_x_pts3,merge_polygon_y_pts3]

                                                                                                             merge_polygon_x_pts4=merge_polygon_pts[0]-abs_np_distance_both_points[0]

                                                                                                             merge_polygon_y_pts4=merge_polygon_pts[1]+abs_np_distance_both_points[1]

                                                                                                             merge_polygon_pts4=[merge_polygon_x_pts4,merge_polygon_y_pts4]

                                                                                                             merge_polygon_list_pts1.append(merge_polygon_pts1)

                                                                                                             merge_polygon_list_pts2.append(merge_polygon_pts2)

                                                                                                             merge_polygon_list_pts3.append(merge_polygon_pts3)

                                                                                                             merge_polygon_list_pts4.append(merge_polygon_pts4)


                                                                                                         resi_merge_polygon_center_x_pts1=abs_np_resibua_circle_center_pts[0]+abs_np_distance_both_points[0]

                                                                                                         resi_merge_polygon_center_y_pts1=abs_np_resibua_circle_center_pts[1]+abs_np_distance_both_points[1]

                                                                                                         resi_merge_polygon_center_pts1=[resi_merge_polygon_center_x_pts1,resi_merge_polygon_center_y_pts1]

                                                                                                         resi_np_merge_polygon_center_pts1=np.array(resi_merge_polygon_center_pts1).round(1)

                                                                                                         abs_resi_np_merge_polygon_center_pts1=abs(resi_np_merge_polygon_center_pts1)

                                                                                                         resi_merge_polygon_center_x_pts2=abs_np_resibua_circle_center_pts[0]-abs_np_distance_both_points[0]

                                                                                                         resi_merge_polygon_center_y_pts2=abs_np_resibua_circle_center_pts[1]-abs_np_distance_both_points[1]

                                                                                                         resi_merge_polygon_center_pts2=[resi_merge_polygon_center_x_pts2,resi_merge_polygon_center_y_pts2]

                                                                                                         resi_np_merge_polygon_center_pts2=np.array(resi_merge_polygon_center_pts2).round(1)

                                                                                                         abs_resi_np_merge_polygon_center_pts2=abs(resi_np_merge_polygon_center_pts2)

                                                                                                         resi_merge_polygon_center_x_pts3=abs_np_resibua_circle_center_pts[0]+abs_np_distance_both_points[0]

                                                                                                         resi_merge_polygon_center_y_pts3=abs_np_resibua_circle_center_pts[1]-abs_np_distance_both_points[1]

                                                                                                         resi_merge_polygon_center_pts3=[resi_merge_polygon_center_x_pts3,resi_merge_polygon_center_y_pts3]

                                                                                                         resi_np_merge_polygon_center_pts3=np.array(resi_merge_polygon_center_pts3).round(1)

                                                                                                         abs_resi_np_merge_polygon_center_pts3=abs(resi_np_merge_polygon_center_pts3)

                                                                                                         resi_merge_polygon_center_x_pts4=abs_np_resibua_circle_center_pts[0]-abs_np_distance_both_points[0]

                                                                                                         resi_merge_polygon_center_y_pts4=abs_np_resibua_circle_center_pts[1]+abs_np_distance_both_points[1]

                                                                                                         resi_merge_polygon_center_pts4=[resi_merge_polygon_center_x_pts4,resi_merge_polygon_center_y_pts4]

                                                                                                         resi_np_merge_polygon_center_pts4=np.array(resi_merge_polygon_center_pts4).round(1)

                                                                                                         abs_resi_np_merge_polygon_center_pts4=abs(resi_np_merge_polygon_center_pts4)

                                                                                                         np_merge_polygon_list_pts1=np.array(merge_polygon_list_pts1).round(1)

                                                                                                         abs_np_merge_polygon_list_pts1=abs(np_merge_polygon_list_pts1)

                                                                                                         #merge_polygon1_points=Polygon(abs_np_merge_polygon_list_pts1)

                                                                                                         np_merge_polygon_list_pts2=np.array(merge_polygon_list_pts2).round(1)

                                                                                                         abs_np_merge_polygon_list_pts2=abs(np_merge_polygon_list_pts2)

                                                                                                         #merge_polygon2_points=Polygon(abs_np_merge_polygon_list_pts2)

                                                                                                         np_merge_polygon_list_pts3=np.array(merge_polygon_list_pts3).round(1)

                                                                                                         abs_np_merge_polygon_list_pts3=abs(np_merge_polygon_list_pts3)

                                                                                                         #merge_polygon3_points=Polygon(abs_np_merge_polygon_list_pts3)

                                                                                                         np_merge_polygon_list_pts4=np.array(merge_polygon_list_pts4).round(1)

                                                                                                         abs_np_merge_polygon_list_pts4=abs( np_merge_polygon_list_pts4)

                                                                                                         ressi_list_of_center_pts=[ abs_resi_np_merge_polygon_center_pts1,abs_resi_np_merge_polygon_center_pts2,abs_resi_np_merge_polygon_center_pts3,abs_resi_np_merge_polygon_center_pts4]

                                                                                                         ressi_np_merge_polygon_list=[ abs_np_merge_polygon_list_pts1, abs_np_merge_polygon_list_pts2, abs_np_merge_polygon_list_pts3, abs_np_merge_polygon_list_pts4]

                                                                                                         for x_merge_polygon_center_pts in  ressi_list_of_center_pts:
                                                                                                             #print(x_merge_polygon_center_pts)
                                                                                                             if prop_abs_np_resibua_circle_center_pts[0]==x_merge_polygon_center_pts[0] and prop_abs_np_resibua_circle_center_pts[1]==x_merge_polygon_center_pts[1]:
                                                                                                            #      print(True)
                                                                                                                  x_merge_polygon_center_points=Point(x_merge_polygon_center_pts)

                                                                                                                  #print(x_merge_polygon_center_points)

                                                                                                                  for ressi_merge_poly_pts in ressi_np_merge_polygon_list:

                                                                                                                      ressi_merge_poly_points=Polygon(ressi_merge_poly_pts)

                                                                                                                      if ressi_merge_poly_points.contains(x_merge_polygon_center_points)==True:

                                                                                                                          #merge_polygon4_points=Polygon(abs_np_merge_polygon_list_pts4)
                                                                                                                          #print(merge_polygon4_points)
                                                                                                                          # for margin layer

                                                                                                                          for margin_insert in insMarginLineList:#msp.query('INSERT[layer=="_MarginLine"]'):

                                                                                                                               front_value_data=[]

                                                                                                                               prop_front_value_data=[]

                                                                                                                               rear_value_data=[]

                                                                                                                               prop_rear_value_data=[]

                                                                                                                               side1_value_data=[]

                                                                                                                               prop_side1_value_data=[]

                                                                                                                               side2_value_data=[]

                                                                                                                               prop_side2_value_data=[]

                                                                                                                               for margin_entity in margin_insert.virtual_entities():

                                                                                                                                   if margin_entity.dxftype()=='LINE':

                                                                                                                                       if margin_entity.dxf.color==1:

                                                                                                                                           f_margin_line_start_pts=[margin_entity.dxf.start[0],margin_entity.dxf.start[1]]

                                                                                                                                           f_margin_line_end_pts=[margin_entity.dxf.end[0],margin_entity.dxf.end[1]]

                                                                                                                                           f_margin_line_pts=[f_margin_line_start_pts,f_margin_line_end_pts]

                                                                                                                                           f_np_margin_line_pts=np.array(f_margin_line_pts).round(1)

                                                                                                                                           f_abs_np_margin_line_pts=abs(f_np_margin_line_pts)

                                                                                                                                           #print(abs_np_margin_line_pts)

                                                                                                                                           f_margin_line_points=LineString(f_abs_np_margin_line_pts)

                                                                                                                                           if abs(round(ressi_merge_poly_points.distance(f_margin_line_points),1))>0.0:

                                                                                                                                               front_value_data.append(abs(round(ressi_merge_poly_points.distance(f_margin_line_points),1)))

                                                                                                                                           if abs(round(prop_work_polygon_point.distance(f_margin_line_points),1))>0.0:

                                                                                                                                               prop_front_value_data.append(abs(round(prop_work_polygon_point.distance(f_margin_line_points),1)))

                                                                                                                                       elif(margin_entity.dxf.color==6):

                                                                                                                                           r_margin_line_start_pts=[margin_entity.dxf.start[0],margin_entity.dxf.start[1]]

                                                                                                                                           r_margin_line_end_pts=[margin_entity.dxf.end[0],margin_entity.dxf.end[1]]

                                                                                                                                           r_margin_line_pts=[r_margin_line_start_pts,r_margin_line_end_pts]

                                                                                                                                           r_np_margin_line_pts=np.array(r_margin_line_pts).round(1)

                                                                                                                                           r_abs_np_margin_line_pts=abs(r_np_margin_line_pts)

                                                                                                                                           #print(abs_np_margin_line_pts)

                                                                                                                                           r_margin_line_points=LineString(r_abs_np_margin_line_pts)

                                                                                                                                           if abs(round(ressi_merge_poly_points.distance(r_margin_line_points),1))>0.0:

                                                                                                                                               rear_value_data.append(abs(round(ressi_merge_poly_points.distance(r_margin_line_points),1)))

                                                                                                                                           if abs(round(prop_work_polygon_point.distance(r_margin_line_points),1))>0.0:

                                                                                                                                               prop_rear_value_data.append(abs(round(prop_work_polygon_point.distance(r_margin_line_points),1)))

                                                                                                                                       elif(margin_entity.dxf.color==5):

                                                                                                                                           s1_margin_line_start_pts=[margin_entity.dxf.start[0],margin_entity.dxf.start[1]]

                                                                                                                                           s1_margin_line_end_pts=[margin_entity.dxf.end[0],margin_entity.dxf.end[1]]

                                                                                                                                           s1_margin_line_pts=[s1_margin_line_start_pts,s1_margin_line_end_pts]

                                                                                                                                           s1_np_margin_line_pts=np.array(s1_margin_line_pts).round(1)

                                                                                                                                           s1_abs_np_margin_line_pts=abs(s1_np_margin_line_pts)

                                                                                                                                           #print(abs_np_margin_line_pts)

                                                                                                                                           s1_margin_line_points=LineString(s1_abs_np_margin_line_pts)

                                                                                                                                           if abs(round(ressi_merge_poly_points.distance(s1_margin_line_points),1))>0.0:

                                                                                                                                               side1_value_data.append(abs(round(ressi_merge_poly_points.distance(s1_margin_line_points),1)))

                                                                                                                                           if abs(round(prop_work_polygon_point.distance(s1_margin_line_points),1))>0.0:

                                                                                                                                               prop_side1_value_data.append(abs(round(prop_work_polygon_point.distance(s1_margin_line_points),1)))

                                                                                                                                       elif(margin_entity.dxf.color==104):

                                                                                                                                           s2_margin_line_start_pts=[margin_entity.dxf.start[0],margin_entity.dxf.start[1]]

                                                                                                                                           s2_margin_line_end_pts=[margin_entity.dxf.end[0],margin_entity.dxf.end[1]]

                                                                                                                                           s2_margin_line_pts=[s2_margin_line_start_pts,s2_margin_line_end_pts]

                                                                                                                                           s2_np_margin_line_pts=np.array(s2_margin_line_pts).round(1)

                                                                                                                                           s2_abs_np_margin_line_pts=abs(s2_np_margin_line_pts)

                                                                                                                                           #print(abs_np_margin_line_pts)

                                                                                                                                           s2_margin_line_points=LineString(s2_abs_np_margin_line_pts)

                                                                                                                                           if abs(round(ressi_merge_poly_points.distance(s2_margin_line_points),1))>0.0:

                                                                                                                                               side2_value_data.append(abs(round(ressi_merge_poly_points.distance(s2_margin_line_points),1)))


                                                                                                                                           if abs(round(prop_work_polygon_point.distance(s2_margin_line_points),1))>0.0:

                                                                                                                                               prop_side2_value_data.append(abs(round(prop_work_polygon_point.distance(s2_margin_line_points),1)))

                                                                                                                               if (front_value_data !=[]) and (prop_front_value_data !=[]):

                                                                                                                                   tot_front_data.append(abs(round(min(prop_front_value_data)-min(front_value_data),1)))

                                                                                                                               if (rear_value_data !=[]) and (prop_rear_value_data !=[]):

                                                                                                                                   tot_rear_data.append(abs(round(min(prop_rear_value_data)-min(rear_value_data),1)))

                                                                                                                               if (side1_value_data !=[]) and (prop_side1_value_data !=[]):

                                                                                                                                   tot_side1_data.append(abs(round(min(prop_side1_value_data)-min(side1_value_data),1)))

                                                                                                                               if (side2_value_data !=[]) and (prop_side2_value_data !=[]):

                                                                                                                                    tot_side2_data.append(abs(round(min(prop_side2_value_data)-min(side2_value_data),1)))

                                                                             tmpPropWorkDict=dict()
                                                                             tmpPropWorkDict['BUILDING_REFID']=building_ref_id
                                                                             tmpPropWorkDict['BUILDING_NAME']=building_text_attribs.get('text')

                                                                             tmpPropWorkDict['FLOOR_REFID']=floor_polygon_ref_id
                                                                             tmpPropWorkDict['FLOOR_NAME']=floor_text_attrib.get('text')
                                                                             #tmpPropWorkDict['TYPE']='FLOOR'

                                                                             if tot_front_data!=[]:
                                                                                tmpPropWorkDict['FRONT']=str(min(tot_front_data))
                                                                             else:
                                                                                 tmpPropWorkDict['FRONT']="0"

                                                                             if tot_rear_data!=[]:

                                                                                 tmpPropWorkDict['REAR']=str(min(tot_rear_data))
                                                                             else:
                                                                                 tmpPropWorkDict['REAR']="0"

                                                                             if tot_side1_data!=[]:

                                                                                 tmpPropWorkDict['SIDE1']=str(min(tot_side1_data))
                                                                             else:
                                                                                 tmpPropWorkDict['SIDE1']="0"

                                                                             if tot_side2_data!=[]:

                                                                                 tmpPropWorkDict['SIDE2']=str(min(tot_side2_data))
                                                                             else:
                                                                                 tmpPropWorkDict['SIDE2']="0"

                                                                             #building_value_dict[floor_polygon_ref_id]=tmpPropWorkDict
                                                                             resultsList.append(tmpPropWorkDict)

                                                        #building_tmpPropWorkDict=dict()

                                                        #building_tmpPropWorkDict[building_text_attribs.get('text')]=floor_value_list#building_value_dict

                                                        #returnValueDict[building_ref_id]=floor_value_list #building_tmpPropWorkDict
                                                        #resultsList.append(floor_value_list)





        #returnValueDict['results']=resultsList
    except IOError:

        print(f'Not a DXF file or a generic I/O error.')

        return resultsList

    except ezdxf.DXFStructureError:

        print(f'Invalid or corrupted DXF file.')

        return resultsList

    endTimer=timer()
    print('Transfer Of Setbacks Total Time Taken ', str(round(endTimer-startTimer,2)) , ' sec ') 

    return resultsList




#path of the filename

#folder=r'E:\production_code\dxf_files'

#Pass extension - removed inside method

#filename='120522--2 Res Apt Blocks (2).dxf'                   # Here give only filename
#filename='PALMGROVE_floorwise_setbacks.dxf'
#method returns a dict with handle

#response=check_floor_wise_setbacks(folder,filename)

#print ('Floor Wise Setbacks  Response ' , response )