import os

import ezdxf

from shapely.geometry import Point,Polygon

from shapely.geometry import LineString

import numpy as np

import math

def rotate_point_wrt_center(point_to_be_rotated, angle, center_point=(0, 0)):

    angle = math.radians(angle)

    xnew = math.cos(angle) * (point_to_be_rotated[0] - center_point[0]) - math.sin(angle) * (
                point_to_be_rotated[1] - center_point[1]) + center_point[0]
    ynew = math.sin(angle) * (point_to_be_rotated[0] - center_point[0]) + math.cos(angle) * (
                point_to_be_rotated[1] - center_point[1]) + center_point[1]

    return (round(xnew, 2), round(ynew, 2))

def calculateAngle(P1X,P1Y,P2X,P2Y,P3X,P3Y):

        numerator = P2Y*(P1X-P3X) + P1Y*(P3X-P2X) + P3Y*(P2X-P1X)

        denominator = (P2X-P1X)*(P1X-P3X) + (P2Y-P1Y)*(P1Y-P3Y)

        ratio = numerator/denominator

        angleRad = math.atan(ratio)

        angleDeg = (angleRad*180)/math.pi

        if(angleDeg<0):

            angleDeg = round(180+angleDeg)

        return angleDeg

def check_cellar_setbacks(msp):

    returnValueDict=dict()

    if (msp is None):

        return returnValueDict

    #dxf_path=os.path.join(folder,filename)

    try:

        #read_dxf=ezdxf.readfile(dxf_path)

        print('cellar setback read file')

        #msp=read_dxf.modelspace()

        building_text_data=msp.query('TEXT MTEXT[layer=="_BuildingName"]')

        building_polygon_data=msp.query('LWPOLYLINE[layer=="_BuildingName"]')

        floor_text_data=msp.query('TEXT MTEXT[layer=="_Floor"]')

        floor_polygon_data=msp.query('LWPOLYLINE[layer=="_Floor"]')

        parking_text_data=msp.query('TEXT MTEXT[layer=="_Parking"]')

        parking_polygon_data=msp.query('LWPOLYLINE[layer=="_Parking"]')

        resibua_insert_data=msp.query('INSERT[layer=="_ResiBUAOutline"]')

        floor_insert_data=msp.query('INSERT[layer=="_Floor"]')

        proposed_text_data=msp.query('TEXT MTEXT[layer=="_ProposedWork"]')

        proposed_polygon_data=msp.query('LWPOLYLINE[layer=="_ProposedWork"]')

        margin_data=msp.query('*[layer=="_MarginLine"]')

        #for building text data

        for building_text in building_text_data:

            building_text_attribs=building_text.dxfattribs()

            building_text_insert=building_text_attribs.get('insert')

            building_text_name=building_text_attribs.get('text') if building_text.dxftype()=='TEXT' else building_text.plain_text()

            if building_text_name!='':

                building_text_pts=[building_text_insert[0],building_text_insert[1]]

                np_building_text_pts=np.array(building_text_pts)

                #abs_np_building_text_pts=abs(np_building_text_pts)

                building_text_point=Point(np_building_text_pts)

                for building_polygon in building_polygon_data:

                    building_polygon_pts=[bp[0:2] for bp in building_polygon.get_points()]

                    np_building_polygon_pts=np.array(building_polygon_pts)

                    #abs_np_building_polygon_pts=abs(np_building_polygon_pts)

                    building_polygon_points=Polygon(np_building_polygon_pts)

                    if building_polygon_points.contains(building_text_point)==True or building_polygon_points.touches(building_text_point)==True or round(building_polygon_points.distance(building_text_point),1)==0.0:

                        filter_building_name="".join(x for x in building_text_name if x.isalpha())

                        #print(filter_building_name)
                        #print('='*len(filter_building_name))

                        #floor text data

                        for floor_text in floor_text_data:

                            floor_text_attribs=floor_text.dxfattribs()

                            floor_text=floor_text_attribs.get('text') if floor_text.dxftype()=='TEXT' else floor_text.plain_text()

                            if ('cellar' in floor_text.lower()) or ('basement' in floor_text.lower()):

                                insert_floor_text_pts=floor_text_attribs.get('insert')

                                cellar_text_pts=[insert_floor_text_pts[0],insert_floor_text_pts[1]]

                                np_cellar_text_pts=np.array(cellar_text_pts).round(2)

                                #abs_np_cellar_text_pts=abs(np_cellar_text_pts)

                                cellar_text_point=Point(np_cellar_text_pts)

                                #floor polygon data

                                for floor_polygon in floor_polygon_data:

                                    floor_polygon_pts=[f[0:2] for f in floor_polygon.get_points()]

                                    refid=floor_polygon.dxf.handle

                                    np_floor_polygon_pts=np.array(floor_polygon_pts).round(2)

                                    #abs_np_floor_polygon_pts=abs(np_floor_polygon_pts)

                                    floor_polygon_point=Polygon(np_floor_polygon_pts)

                                    #check cellar floor text point in polygon

                                    if floor_polygon_point.contains(cellar_text_point)==True or floor_polygon_point.touches(cellar_text_point)==True or round(floor_polygon_point.distance(cellar_text_point),1)==0.0:

                                        if building_polygon_points.contains(floor_polygon_point)==True:
                                            #print(floor_text)
                                            #print('-'*len(floor_text))
                                            #parking text data

                                            for parking_text in parking_text_data:

                                                parking_text_attribs=parking_text.dxfattribs()

                                                parking_text_name=parking_text.text if parking_text.dxftype()=='MTEXT' else parking_text.dxf.text

                                                if parking_text_name=='PARKING' or parking_text_name=='Parking' or 'B' in parking_text_name:

                                                    insert_parking_text_pts=parking_text_attribs.get('insert')

                                                    parking_text_pts=[insert_parking_text_pts[0],insert_parking_text_pts[1]]

                                                    np_parking_text_pts=np.array(parking_text_pts).round(2)

                                                    #abs_np_parking_text_pts=abs(np_parking_text_pts)

                                                    parking_text_point=Point(np_parking_text_pts)

                                                    # parking polygon data

                                                    for parking_polygon in parking_polygon_data:

                                                        if len([p[0:2] for p in parking_polygon.get_points()])>3:

                                                            parking_polygon_pts=[p[0:2] for p in parking_polygon.get_points()]

                                                            np_parking_polygon_pts=np.array(parking_polygon_pts).round(2)

                                                            #abs_np_parking_polygon_pts=abs(np_parking_polygon_pts)

                                                            parking_polygon_point=Polygon(np_parking_polygon_pts)

                                                            #check parking text point in parking polygon points

                                                            if parking_polygon_point.contains(parking_text_point)==True:

                                                                #check parking polygon points in floor polygon points

                                                                if floor_polygon_point.contains(parking_polygon_point)==True:

                                                                    #print('parking polygon:',parking_polygon_point)

                                                                    #floor insert point for parking polygon

                                                                    for floor_insert_entity in floor_insert_data:

                                                                        floor_circle_entity=[entity for entity in floor_insert_entity.virtual_entities() if entity.dxftype()=='CIRCLE']

                                                                        floor_circle_center=floor_circle_entity[0].dxf.center

                                                                        floor_circle_center_pts=[floor_circle_center[0],floor_circle_center[1]]

                                                                        np_floor_circle_center_pts=np.array(floor_circle_center_pts)

                                                                        #abs_np_floor_circle_center_pts=abs(np_floor_circle_center_pts)

                                                                        floor_circle_center_point=Point(np_floor_circle_center_pts)

                                                                        #resibuaoutline insert point for parking

                                                                        for resibuaoutline_insert in resibua_insert_data:

                                                                            for resibuaoutline_entity in resibuaoutline_insert.virtual_entities():

                                                                                if resibuaoutline_entity.dxftype()=='CIRCLE':

                                                                                    circle_center_pts=resibuaoutline_entity.dxf.center

                                                                                    np_circle_center_pts=np.array([circle_center_pts[0],circle_center_pts[1]]).round(2)

                                                                                    #abs_np_circle_center_pts=abs(np_circle_center_pts)

                                                                                    circle_center_point=Point(np_circle_center_pts)

                                                                                    #check circle center point in parking_polygon_point

                                                                                    if parking_polygon_point.contains(circle_center_point)==True and parking_polygon_point.contains(floor_circle_center_point)==True:

                                                                                        #print(circle_center_point,floor_circle_center_point)

                                                                                        # for proposed work text data
                                                                                        for prop_work_text in proposed_text_data:

                                                                                            prop_work_text_attribs=prop_work_text.dxfattribs()

                                                                                            prop_work_text_insert=prop_work_text_attribs.get('insert')

                                                                                            prop_work_name=prop_work_text_attribs.get('text') if prop_work_text.dxftype()=='TEXT' else prop_work_text.plain_text()

                                                                                            prop_work_text_pts=[prop_work_text_insert[0],prop_work_text_insert[1]]

                                                                                            np_prop_work_text_pts=np.array(prop_work_text_pts).round(2)

                                                                                            #abs_np_prop_work_text_pts=abs(np_prop_work_text_pts)

                                                                                            prop_work_text_point=Point(np_prop_work_text_pts)

                                                                                            #proposed work polygon data

                                                                                            for prop_work_polygon in proposed_polygon_data:

                                                                                                prop_work_polygon_pts=[y[0:2] for y in prop_work_polygon.get_points()]

                                                                                                np_prop_work_polygon_pts=np.array(prop_work_polygon_pts).round(2)

                                                                                                #abs_np_prop_work_polygon_pts=abs(np_prop_work_polygon_pts)

                                                                                                prop_work_polygon_point=Polygon(np_prop_work_polygon_pts)

                                                                                                #check proposed work polygon contains proposed work text

                                                                                                if prop_work_polygon_point.contains(prop_work_text_point)==True or prop_work_polygon_point.touches(prop_work_text_point)==True:

                                                                                                    filter_prop_work_name="".join(y for y in prop_work_name if y.isalpha())

                                                                                                    #print(filter_building_name,filter_prop_work_name)

                                                                                                    if filter_building_name==filter_prop_work_name:

                                                                                                        #print(filter_building_name,filter_prop_work_name)

                                                                                                        #print('*'*len(filter_building_name),'*'*len(filter_prop_work_name))

                                                                                                        for margin_floor_insert in floor_insert_data:

                                                                                                            floor_circle_entity_margin=[ entity for entity in margin_floor_insert.virtual_entities() if entity.dxftype()=='CIRCLE']

                                                                                                            floor_margin_circle_center=floor_circle_entity_margin[0].dxf.center

                                                                                                            floor_margin_circle_center_pts=[floor_margin_circle_center[0],floor_margin_circle_center[1]]

                                                                                                            np_floor_margin_circle_center_pts=np.array(floor_margin_circle_center_pts).round(2)

                                                                                                            #abs_np_floor_margin_circle_center_pts=abs(np_floor_margin_circle_center_pts)

                                                                                                            floor_margin_circle_center_point=Point(np_floor_margin_circle_center_pts)

                                                                                                            #print(floor_margin_circle_center_point)

                                                                                                            for margin_resibuaoutline_insert in resibua_insert_data:

                                                                                                                for margin_resibuaoutline_entity in margin_resibuaoutline_insert.virtual_entities():

                                                                                                                    if margin_resibuaoutline_entity.dxftype()=='CIRCLE':

                                                                                                                        margin_circle_center_pts=margin_resibuaoutline_entity.dxf.center

                                                                                                                        np_margin_circle_center_pts=np.array([margin_circle_center_pts[0],margin_circle_center_pts[1]]).round(2)

                                                                                                                        #abs_np_margin_circle_center_pts=abs(np_margin_circle_center_pts)

                                                                                                                        margin_circle_center_point=Point(np_margin_circle_center_pts)

                                                                                                                        #plot_polygon contains circle center points

                                                                                                                        if (prop_work_polygon_point.contains(margin_circle_center_point)==True) and (prop_work_polygon_point.contains(floor_margin_circle_center_point)==True):

                                                                                                                                #print(margin_circle_center_point,floor_margin_circle_center_point)

                                                                                                                                np_both_pts=np.array([np_margin_circle_center_pts,np_circle_center_pts]).round(2)

                                                                                                                                #print(np_both_pts)

                                                                                                                                max_np_both_pts=np_both_pts.max(axis=0)

                                                                                                                                #print(f'maximum point=={max_np_both_pts}')

                                                                                                                                min_np_both_pts=np_both_pts.min(axis=0)

                                                                                                                                #print(f'minimum point==={min_np_both_pts}')

                                                                                                                                dist_both_pts=max_np_both_pts-min_np_both_pts

                                                                                                                                np_dist_both_pts=np.array(dist_both_pts).round(2)

                                                                                                                                #print("distance between proposed center to parking center",np_dist_both_pts)

                                                                                                                                #abs_np_dist_both_pts=abs(np_dist_both_pts)

                                                                                                                                #------------------------------First Quadrant Center Pts--------------------------------------------

                                                                                                                                parking_center_pts1_x=np_circle_center_pts[0]-np_dist_both_pts[0]

                                                                                                                                parking_center_pts1_y=np_circle_center_pts[1]+np_dist_both_pts[1]

                                                                                                                                parking_center_pts1=[parking_center_pts1_x,parking_center_pts1_y]

                                                                                                                                np_parking_center_pts1=np.array(parking_center_pts1).round(2)

                                                                                                                                #abs_np_parking_center_pts1=abs(np_parking_center_pts1)


                                                                                                                                #------------------------------Second Quadrant Center Pts--------------------------------------------

                                                                                                                                parking_center_pts2_x=np_circle_center_pts[0]+np_dist_both_pts[0]

                                                                                                                                parking_center_pts2_y=np_circle_center_pts[1]+np_dist_both_pts[1]

                                                                                                                                parking_center_pts2=[parking_center_pts2_x,parking_center_pts2_y]

                                                                                                                                np_parking_center_pts2=np.array(parking_center_pts2).round(2)

                                                                                                                                abs_np_parking_center_pts2=abs(np_parking_center_pts2)

                                                                                                                                #------------------------------Third Quadrant Center Pts--------------------------------------------

                                                                                                                                parking_center_pts3_x=np_circle_center_pts[0]-np_dist_both_pts[0]

                                                                                                                                parking_center_pts3_y=np_circle_center_pts[1]-np_dist_both_pts[1]

                                                                                                                                parking_center_pts3=[parking_center_pts3_x,parking_center_pts3_y]

                                                                                                                                np_parking_center_pts3=np.array(parking_center_pts3).round(2)

                                                                                                                                abs_np_parking_center_pts3=abs(np_parking_center_pts3)

                                                                                                                                #------------------------------Fourth Quadrant Center Pts--------------------------------------------

                                                                                                                                parking_center_pts4_x=np_circle_center_pts[0]+np_dist_both_pts[0]

                                                                                                                                parking_center_pts4_y=np_circle_center_pts[1]-np_dist_both_pts[1]

                                                                                                                                parking_center_pts4=[parking_center_pts4_x,parking_center_pts4_y]

                                                                                                                                np_parking_center_pts4=np.array(parking_center_pts4).round(2)

                                                                                                                                #abs_np_parking_center_pts4=abs(np_parking_center_pts4)

                                                                                                                                if (np_margin_circle_center_pts[0]==np_parking_center_pts1[0] and np_margin_circle_center_pts[1]==np_parking_center_pts1[1]) :

                                                                                                                                    moved_floor_circle_center_ptsx=np_floor_circle_center_pts[0]-np_dist_both_pts[0]

                                                                                                                                    moved_floor_circle_center_ptsy=np_floor_circle_center_pts[1]+np_dist_both_pts[1]

                                                                                                                                    moved_floor_circle_center_pts=[moved_floor_circle_center_ptsx,moved_floor_circle_center_ptsy]

                                                                                                                                    np_moved_floor_circle_center_pts=np.array(moved_floor_circle_center_pts).round(2)

                                                                                                                                    #abs_np_moved_floor_circle_center_pts=abs(np_moved_floor_circle_center_pts)

                                                                                                                                    #print(abs_np_floor_margin_circle_center_pts,abs_np_moved_floor_circle_center_pts)

                                                                                                                                    if np_floor_margin_circle_center_pts[0]==np_moved_floor_circle_center_pts[0] and np_floor_margin_circle_center_pts[1]==np_moved_floor_circle_center_pts[1]:

                                                                                                                                        #parking_polygon convert into points

                                                                                                                                        move_parking_polygon_pts=[]

                                                                                                                                        for parking_poly_pts in np_parking_polygon_pts:

                                                                                                                                            parking_poly_pts_x=parking_poly_pts[0]-np_dist_both_pts[0]

                                                                                                                                            parking_poly_pts_y=parking_poly_pts[1]+np_dist_both_pts[1]

                                                                                                                                            parking_poly_pts=[parking_poly_pts_x,parking_poly_pts_y]

                                                                                                                                            move_parking_polygon_pts.append(parking_poly_pts)

                                                                                                                                        np_move_parking_polygon_pts=np.array(move_parking_polygon_pts).round(2)

                                                                                                                                        #abs_np_move_parking_polygon_pts=abs(np_move_parking_polygon_pts)

                                                                                                                                        moved_parking_polygon_points=Polygon(np_move_parking_polygon_pts)

                                                                                                                                        front_data = []

                                                                                                                                        rear_data = []

                                                                                                                                        side1_data = []

                                                                                                                                        side2_data = []

                                                                                                                                        for insert in margin_data:

                                                                                                                                            if insert.dxftype()=='INSERT':

                                                                                                                                                for margin_entity in insert.virtual_entities():

                                                                                                                                                    if margin_entity.dxftype()=='LINE':

                                                                                                                                                        if margin_entity.dxf.color==1:

                                                                                                                                                            f_margin_line_start_pts=[margin_entity.dxf.start[0],margin_entity.dxf.start[1]]

                                                                                                                                                            f_margin_line_end_pts=[margin_entity.dxf.end[0],margin_entity.dxf.end[1]]

                                                                                                                                                            f_margin_line_pts=[f_margin_line_start_pts,f_margin_line_end_pts]

                                                                                                                                                            np_f_margin_line_pts=np.array(f_margin_line_pts).round(2)

                                                                                                                                                            #abs_np_f_margin_line_pts=abs(np_f_margin_line_pts)

                                                                                                                                                            f_margin_line_point=LineString(np_f_margin_line_pts)

                                                                                                                                                            front_data.append(round(f_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                                        elif(margin_entity.dxf.color==6):

                                                                                                                                                            r_margin_line_start_pts=[margin_entity.dxf.start[0],margin_entity.dxf.start[1]]

                                                                                                                                                            r_margin_line_end_pts=[margin_entity.dxf.end[0],margin_entity.dxf.end[1]]

                                                                                                                                                            r_margin_line_pts=[r_margin_line_start_pts,r_margin_line_end_pts]

                                                                                                                                                            np_r_margin_line_pts=np.array(r_margin_line_pts).round(2)

                                                                                                                                                            #abs_np_r_margin_line_pts=abs(np_r_margin_line_pts)

                                                                                                                                                            r_margin_line_point=LineString(np_r_margin_line_pts)

                                                                                                                                                            rear_data.append(round(r_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                                        elif(margin_entity.dxf.color==5):

                                                                                                                                                            s1_margin_line_start_pts=[margin_entity.dxf.start[0],margin_entity.dxf.start[1]]

                                                                                                                                                            s1_margin_line_end_pts=[margin_entity.dxf.end[0],margin_entity.dxf.end[1]]

                                                                                                                                                            s1_margin_line_pts=[s1_margin_line_start_pts,s1_margin_line_end_pts]

                                                                                                                                                            np_s1_margin_line_pts=np.array(s1_margin_line_pts).round(2)

                                                                                                                                                            #abs_np_s1_margin_line_pts=abs(np_s1_margin_line_pts)

                                                                                                                                                            s1_margin_line_point=LineString(np_s1_margin_line_pts)

                                                                                                                                                            side1_data.append(round(s1_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                                        elif(margin_entity.dxf.color==104 or margin_entity.dxf.color==3):

                                                                                                                                                            s2_margin_line_start_pts=[margin_entity.dxf.start[0],margin_entity.dxf.start[1]]

                                                                                                                                                            s2_margin_line_end_pts=[margin_entity.dxf.end[0],margin_entity.dxf.end[1]]

                                                                                                                                                            s2_margin_line_pts=[s2_margin_line_start_pts,s2_margin_line_end_pts]

                                                                                                                                                            np_s2_margin_line_pts=np.array(s2_margin_line_pts).round(2)

                                                                                                                                                            #abs_np_s2_margin_line_pts=abs(np_s2_margin_line_pts)

                                                                                                                                                            s2_margin_line_point=LineString(np_s2_margin_line_pts)

                                                                                                                                                            side2_data.append(round(s2_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                            elif insert.dxftype() == 'LINE':

                                                                                                                                                if insert.dxf.color == 1:

                                                                                                                                                    f_margin_line_start_pts = [insert.dxf.start[0],insert.dxf.start[1]]

                                                                                                                                                    f_margin_line_end_pts = [insert.dxf.end[0],insert.dxf.end[1]]

                                                                                                                                                    f_margin_line_pts = [f_margin_line_start_pts,f_margin_line_end_pts]

                                                                                                                                                    np_f_margin_line_pts = np.array(f_margin_line_pts).round(2)

                                                                                                                                                    # abs_np_f_margin_line_pts=abs(np_f_margin_line_pts)

                                                                                                                                                    f_margin_line_point = LineString(np_f_margin_line_pts)

                                                                                                                                                    front_data.append(round(f_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                                elif (insert.dxf.color == 6):

                                                                                                                                                    r_margin_line_start_pts = [insert.dxf.start[0],insert.dxf.start[1]]

                                                                                                                                                    r_margin_line_end_pts = [insert.dxf.end[0],insert.dxf.end[1]]

                                                                                                                                                    r_margin_line_pts = [r_margin_line_start_pts,r_margin_line_end_pts]

                                                                                                                                                    np_r_margin_line_pts = np.array(r_margin_line_pts).round(2)

                                                                                                                                                    # abs_np_r_margin_line_pts=abs(np_r_margin_line_pts)

                                                                                                                                                    r_margin_line_point = LineString(np_r_margin_line_pts)

                                                                                                                                                    rear_data.append(round(r_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                                elif (insert.dxf.color == 5):

                                                                                                                                                    s1_margin_line_start_pts = [insert.dxf.start[0],insert.dxf.start[1]]

                                                                                                                                                    s1_margin_line_end_pts = [insert.dxf.end[0],insert.dxf.end[1]]

                                                                                                                                                    s1_margin_line_pts = [s1_margin_line_start_pts,s1_margin_line_end_pts]

                                                                                                                                                    np_s1_margin_line_pts = np.array(s1_margin_line_pts).round(2)

                                                                                                                                                    # abs_np_s1_margin_line_pts=abs(np_s1_margin_line_pts)

                                                                                                                                                    s1_margin_line_point = LineString(np_s1_margin_line_pts)

                                                                                                                                                    side1_data.append(round(s1_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                                elif (insert.dxf.color == 104 or insert.dxf.color ==3):

                                                                                                                                                    s2_margin_line_start_pts = [insert.dxf.start[0],insert.dxf.start[1]]

                                                                                                                                                    s2_margin_line_end_pts = [insert.dxf.end[0],insert.dxf.end[1]]

                                                                                                                                                    s2_margin_line_pts = [s2_margin_line_start_pts,s2_margin_line_end_pts]

                                                                                                                                                    np_s2_margin_line_pts = np.array(s2_margin_line_pts).round(2)

                                                                                                                                                    # abs_np_s2_margin_line_pts=abs(np_s2_margin_line_pts)

                                                                                                                                                    s2_margin_line_point = LineString(np_s2_margin_line_pts)

                                                                                                                                                    side2_data.append(round(s2_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                        tmpPropWorkDict=dict()

                                                                                                                                        tmpPropWorkDict['BLDG_NAME']=building_text_name

                                                                                                                                        tmpPropWorkDict['NAME']=floor_text

                                                                                                                                        if front_data is not None:

                                                                                                                                            tmpPropWorkDict['FRONT']=str(min(front_data))

                                                                                                                                        if rear_data is not None:

                                                                                                                                            tmpPropWorkDict['REAR']=str(min(rear_data))

                                                                                                                                        if side1_data is not None:

                                                                                                                                            tmpPropWorkDict['SIDE1']=str(min(side1_data))

                                                                                                                                        if side2_data is not None:

                                                                                                                                            tmpPropWorkDict['SIDE2']=str(min(side2_data))

                                                                                                                                        returnValueDict[refid]=tmpPropWorkDict

                                                                                                                                    else:


                                                                                                                                        p1 = np_margin_circle_center_pts

                                                                                                                                        p2 = np_moved_floor_circle_center_pts

                                                                                                                                        p3 = np_floor_margin_circle_center_pts

                                                                                                                                        get_angle = calculateAngle(p1[1],p1[0],p2[1],p2[0],p3[1],p3[0])

                                                                                                                                        #parking_polygon convert into points

                                                                                                                                        move_parking_polygon_pts=[]

                                                                                                                                        for parking_poly_pts in np_parking_polygon_pts:

                                                                                                                                           parking_poly_pts_x=parking_poly_pts[0]-np_dist_both_pts[0]

                                                                                                                                           parking_poly_pts_y=parking_poly_pts[1]+np_dist_both_pts[1]

                                                                                                                                           parking_poly_pts=[parking_poly_pts_x,parking_poly_pts_y]

                                                                                                                                           move_parking_polygon_pts.append(parking_poly_pts)

                                                                                                                                        update_parking_polygon_pts = []

                                                                                                                                        for pts in move_parking_polygon_pts:

                                                                                                                                          update_parking_polygon_pts.append(rotate_point_wrt_center(pts,get_angle,[np_parking_center_pts4[0],np_parking_center_pts4[1]]))

                                                                                                                                        np_move_parking_polygon_pts=np.array(update_parking_polygon_pts).round(2)

                                                                                                                                        #abs_np_move_parking_polygon_pts=abs(np_move_parking_polygon_pts)

                                                                                                                                        moved_parking_polygon_points=Polygon(np_move_parking_polygon_pts)

                                                                                                                                        front_data = []

                                                                                                                                        rear_data = []

                                                                                                                                        side1_data = []

                                                                                                                                        side2_data = []

                                                                                                                                        for insert in margin_data:

                                                                                                                                           if insert.dxftype()=='INSERT':

                                                                                                                                                for margin_entity in insert.virtual_entities():

                                                                                                                                                    if margin_entity.dxftype()=='LINE':

                                                                                                                                                        if margin_entity.dxf.color==1:

                                                                                                                                                            f_margin_line_start_pts=[margin_entity.dxf.start[0],margin_entity.dxf.start[1]]

                                                                                                                                                            f_margin_line_end_pts=[margin_entity.dxf.end[0],margin_entity.dxf.end[1]]

                                                                                                                                                            f_margin_line_pts=[f_margin_line_start_pts,f_margin_line_end_pts]

                                                                                                                                                            np_f_margin_line_pts=np.array(f_margin_line_pts).round(2)

                                                                                                                                                            #abs_np_f_margin_line_pts=abs(np_f_margin_line_pts)

                                                                                                                                                            f_margin_line_point=LineString(np_f_margin_line_pts)

                                                                                                                                                            front_data.append(round(f_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                                        elif(margin_entity.dxf.color==6):

                                                                                                                                                            r_margin_line_start_pts=[margin_entity.dxf.start[0],margin_entity.dxf.start[1]]

                                                                                                                                                            r_margin_line_end_pts=[margin_entity.dxf.end[0],margin_entity.dxf.end[1]]

                                                                                                                                                            r_margin_line_pts=[r_margin_line_start_pts,r_margin_line_end_pts]

                                                                                                                                                            np_r_margin_line_pts=np.array(r_margin_line_pts).round(2)

                                                                                                                                                            #abs_np_r_margin_line_pts=abs(np_r_margin_line_pts)

                                                                                                                                                            r_margin_line_point=LineString(np_r_margin_line_pts)

                                                                                                                                                            rear_data.append(round(r_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                                        elif(margin_entity.dxf.color==5):

                                                                                                                                                            s1_margin_line_start_pts=[margin_entity.dxf.start[0],margin_entity.dxf.start[1]]

                                                                                                                                                            s1_margin_line_end_pts=[margin_entity.dxf.end[0],margin_entity.dxf.end[1]]

                                                                                                                                                            s1_margin_line_pts=[s1_margin_line_start_pts,s1_margin_line_end_pts]

                                                                                                                                                            np_s1_margin_line_pts=np.array(s1_margin_line_pts).round(2)

                                                                                                                                                            #abs_np_s1_margin_line_pts=abs(np_s1_margin_line_pts)

                                                                                                                                                            s1_margin_line_point=LineString(np_s1_margin_line_pts)

                                                                                                                                                            side1_data.append(round(s1_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                                        elif(margin_entity.dxf.color==104 or margin_entity.dxf.color==3):

                                                                                                                                                            s2_margin_line_start_pts=[margin_entity.dxf.start[0],margin_entity.dxf.start[1]]

                                                                                                                                                            s2_margin_line_end_pts=[margin_entity.dxf.end[0],margin_entity.dxf.end[1]]

                                                                                                                                                            s2_margin_line_pts=[s2_margin_line_start_pts,s2_margin_line_end_pts]

                                                                                                                                                            np_s2_margin_line_pts=np.array(s2_margin_line_pts).round(2)

                                                                                                                                                            #abs_np_s2_margin_line_pts=abs(np_s2_margin_line_pts)

                                                                                                                                                            s2_margin_line_point=LineString(np_s2_margin_line_pts)

                                                                                                                                                            side2_data.append(round(s2_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                           elif insert.dxftype()=='LINE':

                                                                                                                                               if insert.dxf.color==1:

                                                                                                                                                   f_margin_line_start_pts=[insert.dxf.start[0],insert.dxf.start[1]]

                                                                                                                                                   f_margin_line_end_pts=[insert.dxf.end[0],insert.dxf.end[1]]

                                                                                                                                                   f_margin_line_pts=[f_margin_line_start_pts,f_margin_line_end_pts]

                                                                                                                                                   np_f_margin_line_pts=np.array(f_margin_line_pts).round(2)

                                                                                                                                                   #abs_np_f_margin_line_pts=abs(np_f_margin_line_pts)

                                                                                                                                                   f_margin_line_point=LineString(np_f_margin_line_pts)

                                                                                                                                                   front_data.append(round(f_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                               elif(insert.dxf.color==6):

                                                                                                                                                       r_margin_line_start_pts=[insert.dxf.start[0],insert.dxf.start[1]]

                                                                                                                                                       r_margin_line_end_pts=[insert.dxf.end[0],insert.dxf.end[1]]

                                                                                                                                                       r_margin_line_pts=[r_margin_line_start_pts,r_margin_line_end_pts]

                                                                                                                                                       np_r_margin_line_pts=np.array(r_margin_line_pts).round(2)

                                                                                                                                                       #abs_np_r_margin_line_pts=abs(np_r_margin_line_pts)

                                                                                                                                                       r_margin_line_point=LineString(np_r_margin_line_pts)

                                                                                                                                                       rear_data.append(round(r_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                               elif(insert.dxf.color==5):

                                                                                                                                                       s1_margin_line_start_pts=[insert.dxf.start[0],insert.dxf.start[1]]

                                                                                                                                                       s1_margin_line_end_pts=[insert.dxf.end[0],insert.dxf.end[1]]

                                                                                                                                                       s1_margin_line_pts=[s1_margin_line_start_pts,s1_margin_line_end_pts]

                                                                                                                                                       np_s1_margin_line_pts=np.array(s1_margin_line_pts).round(2)

                                                                                                                                                       #abs_np_s1_margin_line_pts=abs(np_s1_margin_line_pts)

                                                                                                                                                       s1_margin_line_point=LineString(np_s1_margin_line_pts)

                                                                                                                                                       side1_data.append(round(s1_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                               elif(insert.dxf.color==104 or insert.dxf.color==3):

                                                                                                                                                       s2_margin_line_start_pts=[insert.dxf.start[0],insert.dxf.start[1]]

                                                                                                                                                       s2_margin_line_end_pts=[insert.dxf.end[0],insert.dxf.end[1]]

                                                                                                                                                       s2_margin_line_pts=[s2_margin_line_start_pts,s2_margin_line_end_pts]

                                                                                                                                                       np_s2_margin_line_pts=np.array(s2_margin_line_pts).round(2)

                                                                                                                                                       #abs_np_s2_margin_line_pts=abs(np_s2_margin_line_pts)

                                                                                                                                                       s2_margin_line_point=LineString(np_s2_margin_line_pts)

                                                                                                                                                       side2_data.append(round(s2_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                        tmpPropWorkDict=dict()

                                                                                                                                        tmpPropWorkDict['BLDG_NAME']=building_text_name

                                                                                                                                        tmpPropWorkDict['NAME']=floor_text

                                                                                                                                        if front_data is not None:

                                                                                                                                            tmpPropWorkDict['FRONT']=str(min(front_data))

                                                                                                                                        if rear_data is not None:

                                                                                                                                            tmpPropWorkDict['REAR']=str(min(rear_data))

                                                                                                                                        if side1_data is not None:

                                                                                                                                            tmpPropWorkDict['SIDE1']=str(min(side1_data))

                                                                                                                                        if side2_data is not None:

                                                                                                                                            tmpPropWorkDict['SIDE2']=str(min(side2_data))

                                                                                                                                        returnValueDict[refid]=tmpPropWorkDict

                                                                                                                                elif(np_margin_circle_center_pts[0]==np_parking_center_pts2[0] and np_margin_circle_center_pts[1]==np_parking_center_pts2[1]) :

                                                                                                                                    moved_floor_circle_center_ptsx=np_floor_circle_center_pts[0]+np_dist_both_pts[0]

                                                                                                                                    moved_floor_circle_center_ptsy=np_floor_circle_center_pts[1]+np_dist_both_pts[1]

                                                                                                                                    moved_floor_circle_center_pts=[moved_floor_circle_center_ptsx,moved_floor_circle_center_ptsy]

                                                                                                                                    np_moved_floor_circle_center_pts=np.array(moved_floor_circle_center_pts).round(2)

                                                                                                                                    #abs_np_moved_floor_circle_center_pts=abs(np_moved_floor_circle_center_pts)

                                                                                                                                    if np_floor_margin_circle_center_pts[0]==np_moved_floor_circle_center_pts[0] and np_floor_margin_circle_center_pts[1]==np_moved_floor_circle_center_pts[1]:

                                                                                                                                        #parking_polygon convert into points

                                                                                                                                        move_parking_polygon_pts=[]

                                                                                                                                        for parking_poly_pts in np_parking_polygon_pts:

                                                                                                                                            parking_poly_pts_x=parking_poly_pts[0]+np_dist_both_pts[0]

                                                                                                                                            parking_poly_pts_y=parking_poly_pts[1]+np_dist_both_pts[1]

                                                                                                                                            parking_poly_pts=[parking_poly_pts_x,parking_poly_pts_y]

                                                                                                                                            move_parking_polygon_pts.append(parking_poly_pts)

                                                                                                                                        np_move_parking_polygon_pts=np.array(move_parking_polygon_pts).round(2)

                                                                                                                                        #abs_np_move_parking_polygon_pts=abs(np_move_parking_polygon_pts)

                                                                                                                                        moved_parking_polygon_points=Polygon(np_move_parking_polygon_pts)

                                                                                                                                        front_data = []

                                                                                                                                        rear_data = []

                                                                                                                                        side1_data = []

                                                                                                                                        side2_data = []

                                                                                                                                        for insert in margin_data:

                                                                                                                                            if insert.dxftype()=='INSERT':

                                                                                                                                                for margin_entity in insert.virtual_entities():

                                                                                                                                                    if margin_entity.dxftype()=='LINE':

                                                                                                                                                        if margin_entity.dxf.color==1:

                                                                                                                                                            f_margin_line_start_pts=[margin_entity.dxf.start[0],margin_entity.dxf.start[1]]

                                                                                                                                                            f_margin_line_end_pts=[margin_entity.dxf.end[0],margin_entity.dxf.end[1]]

                                                                                                                                                            f_margin_line_pts=[f_margin_line_start_pts,f_margin_line_end_pts]

                                                                                                                                                            np_f_margin_line_pts=np.array(f_margin_line_pts).round(2)

                                                                                                                                                            #abs_np_f_margin_line_pts=abs(np_f_margin_line_pts)

                                                                                                                                                            f_margin_line_point=LineString(np_f_margin_line_pts)

                                                                                                                                                            front_data.append(round(f_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                                        elif(margin_entity.dxf.color==6):

                                                                                                                                                            r_margin_line_start_pts=[margin_entity.dxf.start[0],margin_entity.dxf.start[1]]

                                                                                                                                                            r_margin_line_end_pts=[margin_entity.dxf.end[0],margin_entity.dxf.end[1]]

                                                                                                                                                            r_margin_line_pts=[r_margin_line_start_pts,r_margin_line_end_pts]

                                                                                                                                                            np_r_margin_line_pts=np.array(r_margin_line_pts).round(2)

                                                                                                                                                            #abs_np_r_margin_line_pts=abs(np_r_margin_line_pts)

                                                                                                                                                            r_margin_line_point=LineString(np_r_margin_line_pts)

                                                                                                                                                            rear_data.append(round(r_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                                        elif(margin_entity.dxf.color==5):

                                                                                                                                                            s1_margin_line_start_pts=[margin_entity.dxf.start[0],margin_entity.dxf.start[1]]

                                                                                                                                                            s1_margin_line_end_pts=[margin_entity.dxf.end[0],margin_entity.dxf.end[1]]

                                                                                                                                                            s1_margin_line_pts=[s1_margin_line_start_pts,s1_margin_line_end_pts]

                                                                                                                                                            np_s1_margin_line_pts=np.array(s1_margin_line_pts).round(2)

                                                                                                                                                            #abs_np_s1_margin_line_pts=abs(np_s1_margin_line_pts)

                                                                                                                                                            s1_margin_line_point=LineString(np_s1_margin_line_pts)

                                                                                                                                                            side1_data.append(round(s1_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                                        elif(margin_entity.dxf.color==104 or margin_entity.dxf.color==3):

                                                                                                                                                            s2_margin_line_start_pts=[margin_entity.dxf.start[0],margin_entity.dxf.start[1]]

                                                                                                                                                            s2_margin_line_end_pts=[margin_entity.dxf.end[0],margin_entity.dxf.end[1]]

                                                                                                                                                            s2_margin_line_pts=[s2_margin_line_start_pts,s2_margin_line_end_pts]

                                                                                                                                                            np_s2_margin_line_pts=np.array(s2_margin_line_pts).round(2)

                                                                                                                                                            #abs_np_s2_margin_line_pts=abs(np_s2_margin_line_pts)

                                                                                                                                                            s2_margin_line_point=LineString(np_s2_margin_line_pts)

                                                                                                                                                            side2_data.append(round(s2_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                            elif insert.dxftype()=='LINE':

                                                                                                                                                if insert.dxf.color==1:

                                                                                                                                                    f_margin_line_start_pts=[insert.dxf.start[0],insert.dxf.start[1]]

                                                                                                                                                    f_margin_line_end_pts=[insert.dxf.end[0],insert.dxf.end[1]]

                                                                                                                                                    f_margin_line_pts=[f_margin_line_start_pts,f_margin_line_end_pts]

                                                                                                                                                    np_f_margin_line_pts=np.array(f_margin_line_pts).round(2)

                                                                                                                                                    #abs_np_f_margin_line_pts=abs(np_f_margin_line_pts)

                                                                                                                                                    f_margin_line_point=LineString(np_f_margin_line_pts)

                                                                                                                                                    front_data.append(round(f_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                                elif(insert.dxf.color==6):

                                                                                                                                                    r_margin_line_start_pts=[insert.dxf.start[0],insert.dxf.start[1]]

                                                                                                                                                    r_margin_line_end_pts=[insert.dxf.end[0],insert.dxf.end[1]]

                                                                                                                                                    r_margin_line_pts=[r_margin_line_start_pts,r_margin_line_end_pts]

                                                                                                                                                    np_r_margin_line_pts=np.array(r_margin_line_pts).round(2)

                                                                                                                                                    #abs_np_r_margin_line_pts=abs(np_r_margin_line_pts)

                                                                                                                                                    r_margin_line_point=LineString(np_r_margin_line_pts)

                                                                                                                                                    rear_data.append(round(r_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                                elif(insert.dxf.color==5):

                                                                                                                                                    s1_margin_line_start_pts=[insert.dxf.start[0],insert.dxf.start[1]]

                                                                                                                                                    s1_margin_line_end_pts=[insert.dxf.end[0],insert.dxf.end[1]]

                                                                                                                                                    s1_margin_line_pts=[s1_margin_line_start_pts,s1_margin_line_end_pts]

                                                                                                                                                    np_s1_margin_line_pts=np.array(s1_margin_line_pts).round(2)

                                                                                                                                                    #abs_np_s1_margin_line_pts=abs(np_s1_margin_line_pts)

                                                                                                                                                    s1_margin_line_point=LineString(np_s1_margin_line_pts)

                                                                                                                                                    side1_data.append(round(s1_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                                elif(insert.dxf.color==104 or insert.dxf.color==3):

                                                                                                                                                    s2_margin_line_start_pts=[insert.dxf.start[0],insert.dxf.start[1]]

                                                                                                                                                    s2_margin_line_end_pts=[insert.dxf.end[0],insert.dxf.end[1]]

                                                                                                                                                    s2_margin_line_pts=[s2_margin_line_start_pts,s2_margin_line_end_pts]

                                                                                                                                                    np_s2_margin_line_pts=np.array(s2_margin_line_pts).round(2)

                                                                                                                                                    #abs_np_s2_margin_line_pts=abs(np_s2_margin_line_pts)

                                                                                                                                                    s2_margin_line_point=LineString(np_s2_margin_line_pts)

                                                                                                                                                    side2_data.append(round(s2_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                        tmpPropWorkDict=dict()

                                                                                                                                        tmpPropWorkDict['BLDG_NAME']=building_text_name

                                                                                                                                        tmpPropWorkDict['NAME']=floor_text

                                                                                                                                        if front_data is not None:

                                                                                                                                            tmpPropWorkDict['FRONT']=str(min(front_data))

                                                                                                                                        if rear_data is not None:

                                                                                                                                            tmpPropWorkDict['REAR']=str(min(rear_data))

                                                                                                                                        if side1_data is not None:

                                                                                                                                            tmpPropWorkDict['SIDE1']=str(min(side1_data))

                                                                                                                                        if side2_data is not None:

                                                                                                                                            tmpPropWorkDict['SIDE2']=str(min(side2_data))

                                                                                                                                        returnValueDict[refid]=tmpPropWorkDict

                                                                                                                                    else:

                                                                                                                                        p1=np_margin_circle_center_pts

                                                                                                                                        p2=np_moved_floor_circle_center_pts

                                                                                                                                        p3=np_floor_margin_circle_center_pts

                                                                                                                                        get_angle=calculateAngle(p1[1],p1[0],p2[1],p2[0],p3[1],p3[0])

                                                                                                                                        #parking_polygon convert into points

                                                                                                                                        move_parking_polygon_pts=[]

                                                                                                                                        for parking_poly_pts in np_parking_polygon_pts:

                                                                                                                                           parking_poly_pts_x=parking_poly_pts[0]+np_dist_both_pts[0]

                                                                                                                                           parking_poly_pts_y=parking_poly_pts[1]+np_dist_both_pts[1]

                                                                                                                                           parking_poly_pts=[parking_poly_pts_x,parking_poly_pts_y]

                                                                                                                                           move_parking_polygon_pts.append(parking_poly_pts)

                                                                                                                                        update_parking_polygon_pts = []

                                                                                                                                        for pts in move_parking_polygon_pts:

                                                                                                                                          update_parking_polygon_pts.append(rotate_point_wrt_center(pts,get_angle,[np_parking_center_pts4[0],np_parking_center_pts4[1]]))

                                                                                                                                        np_move_parking_polygon_pts=np.array(update_parking_polygon_pts).round(2)

                                                                                                                                        #abs_np_move_parking_polygon_pts=abs(np_move_parking_polygon_pts)

                                                                                                                                        moved_parking_polygon_points=Polygon(np_move_parking_polygon_pts)

                                                                                                                                        front_data = []

                                                                                                                                        rear_data = []

                                                                                                                                        side1_data = []

                                                                                                                                        side2_data = []

                                                                                                                                        for insert in margin_data:

                                                                                                                                           if insert.dxftype()=='INSERT':

                                                                                                                                             for margin_entity in insert.virtual_entities():

                                                                                                                                                if margin_entity.dxftype()=='LINE':

                                                                                                                                                   if margin_entity.dxf.color==1:

                                                                                                                                                       f_margin_line_start_pts=[margin_entity.dxf.start[0],margin_entity.dxf.start[1]]

                                                                                                                                                       f_margin_line_end_pts=[margin_entity.dxf.end[0],margin_entity.dxf.end[1]]

                                                                                                                                                       f_margin_line_pts=[f_margin_line_start_pts,f_margin_line_end_pts]

                                                                                                                                                       np_f_margin_line_pts=np.array(f_margin_line_pts).round(2)

                                                                                                                                                       #abs_np_f_margin_line_pts=abs(np_f_margin_line_pts)

                                                                                                                                                       f_margin_line_point=LineString(np_f_margin_line_pts)

                                                                                                                                                       front_data.append(round(f_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                                   elif(margin_entity.dxf.color==6):

                                                                                                                                                       r_margin_line_start_pts=[margin_entity.dxf.start[0],margin_entity.dxf.start[1]]

                                                                                                                                                       r_margin_line_end_pts=[margin_entity.dxf.end[0],margin_entity.dxf.end[1]]

                                                                                                                                                       r_margin_line_pts=[r_margin_line_start_pts,r_margin_line_end_pts]

                                                                                                                                                       np_r_margin_line_pts=np.array(r_margin_line_pts).round(2)

                                                                                                                                                       #abs_np_r_margin_line_pts=abs(np_r_margin_line_pts)

                                                                                                                                                       r_margin_line_point=LineString(np_r_margin_line_pts)

                                                                                                                                                       rear_data.append(round(r_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                                   elif(margin_entity.dxf.color==5):

                                                                                                                                                       s1_margin_line_start_pts=[margin_entity.dxf.start[0],margin_entity.dxf.start[1]]

                                                                                                                                                       s1_margin_line_end_pts=[margin_entity.dxf.end[0],margin_entity.dxf.end[1]]

                                                                                                                                                       s1_margin_line_pts=[s1_margin_line_start_pts,s1_margin_line_end_pts]

                                                                                                                                                       np_s1_margin_line_pts=np.array(s1_margin_line_pts).round(2)

                                                                                                                                                       #abs_np_s1_margin_line_pts=abs(np_s1_margin_line_pts)

                                                                                                                                                       s1_margin_line_point=LineString(np_s1_margin_line_pts)

                                                                                                                                                       side1_data.append(round(s1_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                                   elif(margin_entity.dxf.color==104 or margin_entity.dxf.color==3):

                                                                                                                                                       s2_margin_line_start_pts=[margin_entity.dxf.start[0],margin_entity.dxf.start[1]]

                                                                                                                                                       s2_margin_line_end_pts=[margin_entity.dxf.end[0],margin_entity.dxf.end[1]]

                                                                                                                                                       s2_margin_line_pts=[s2_margin_line_start_pts,s2_margin_line_end_pts]

                                                                                                                                                       np_s2_margin_line_pts=np.array(s2_margin_line_pts).round(2)

                                                                                                                                                       #abs_np_s2_margin_line_pts=abs(np_s2_margin_line_pts)

                                                                                                                                                       s2_margin_line_point=LineString(np_s2_margin_line_pts)

                                                                                                                                                       side2_data.append(round(s2_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                           elif insert.dxftype()=='LINE':

                                                                                                                                                if insert.dxf.color==1:

                                                                                                                                                   f_margin_line_start_pts=[insert.dxf.start[0],insert.dxf.start[1]]

                                                                                                                                                   f_margin_line_end_pts=[insert.dxf.end[0],insert.dxf.end[1]]

                                                                                                                                                   f_margin_line_pts=[f_margin_line_start_pts,f_margin_line_end_pts]

                                                                                                                                                   np_f_margin_line_pts=np.array(f_margin_line_pts).round(2)

                                                                                                                                                   #abs_np_f_margin_line_pts=abs(np_f_margin_line_pts)

                                                                                                                                                   f_margin_line_point=LineString(np_f_margin_line_pts)

                                                                                                                                                   front_data.append(round(f_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                                elif(insert.dxf.color==6):

                                                                                                                                                   r_margin_line_start_pts=[insert.dxf.start[0],insert.dxf.start[1]]

                                                                                                                                                   r_margin_line_end_pts=[insert.dxf.end[0],insert.dxf.end[1]]

                                                                                                                                                   r_margin_line_pts=[r_margin_line_start_pts,r_margin_line_end_pts]

                                                                                                                                                   np_r_margin_line_pts=np.array(r_margin_line_pts).round(2)

                                                                                                                                                   #abs_np_r_margin_line_pts=abs(np_r_margin_line_pts)

                                                                                                                                                   r_margin_line_point=LineString(np_r_margin_line_pts)

                                                                                                                                                   rear_data.append(round(r_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                                elif(insert.dxf.color==5):

                                                                                                                                                   s1_margin_line_start_pts=[insert.dxf.start[0],insert.dxf.start[1]]

                                                                                                                                                   s1_margin_line_end_pts=[insert.dxf.end[0],insert.dxf.end[1]]

                                                                                                                                                   s1_margin_line_pts=[s1_margin_line_start_pts,s1_margin_line_end_pts]

                                                                                                                                                   np_s1_margin_line_pts=np.array(s1_margin_line_pts).round(2)

                                                                                                                                                   #abs_np_s1_margin_line_pts=abs(np_s1_margin_line_pts)

                                                                                                                                                   s1_margin_line_point=LineString(np_s1_margin_line_pts)

                                                                                                                                                   side1_data.append(round(s1_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                                elif(insert.dxf.color==104 or insert.dxf.color==3):

                                                                                                                                                   s2_margin_line_start_pts=[insert.dxf.start[0],insert.dxf.start[1]]

                                                                                                                                                   s2_margin_line_end_pts=[insert.dxf.end[0],insert.dxf.end[1]]

                                                                                                                                                   s2_margin_line_pts=[s2_margin_line_start_pts,s2_margin_line_end_pts]

                                                                                                                                                   np_s2_margin_line_pts=np.array(s2_margin_line_pts).round(2)

                                                                                                                                                   #abs_np_s2_margin_line_pts=abs(np_s2_margin_line_pts)

                                                                                                                                                   s2_margin_line_point=LineString(np_s2_margin_line_pts)

                                                                                                                                                   side2_data.append(round(s2_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                        tmpPropWorkDict=dict()

                                                                                                                                        tmpPropWorkDict['BLDG_NAME']=building_text_name

                                                                                                                                        tmpPropWorkDict['NAME']=floor_text

                                                                                                                                        if front_data is not None:

                                                                                                                                            tmpPropWorkDict['FRONT']=str(min(front_data))

                                                                                                                                        if rear_data is not None:

                                                                                                                                            tmpPropWorkDict['REAR']=str(min(rear_data))

                                                                                                                                        if side1_data is not None:

                                                                                                                                            tmpPropWorkDict['SIDE1']=str(min(side1_data))

                                                                                                                                        if side2_data is not None:

                                                                                                                                            tmpPropWorkDict['SIDE2']=str(min(side2_data))

                                                                                                                                        returnValueDict[refid]=tmpPropWorkDict

                                                                                                                                elif(np_margin_circle_center_pts[0]==np_parking_center_pts3[0] and np_margin_circle_center_pts[1]==np_parking_center_pts3[1]) :

                                                                                                                                    moved_floor_circle_center_ptsx=np_floor_circle_center_pts[0]-np_dist_both_pts[0]

                                                                                                                                    moved_floor_circle_center_ptsy=np_floor_circle_center_pts[1]-np_dist_both_pts[1]

                                                                                                                                    moved_floor_circle_center_pts=[moved_floor_circle_center_ptsx,moved_floor_circle_center_ptsy]

                                                                                                                                    np_moved_floor_circle_center_pts=np.array(moved_floor_circle_center_pts).round(2)

                                                                                                                                    #abs_np_moved_floor_circle_center_pts=abs(np_moved_floor_circle_center_pts)

                                                                                                                                    if np_floor_margin_circle_center_pts[0]==np_moved_floor_circle_center_pts[0] and np_floor_margin_circle_center_pts[1]==np_moved_floor_circle_center_pts[1]:

                                                                                                                                        #parking_polygon convert into points

                                                                                                                                        move_parking_polygon_pts=[]

                                                                                                                                        for parking_poly_pts in np_parking_polygon_pts:

                                                                                                                                            parking_poly_pts_x=parking_poly_pts[0]-np_dist_both_pts[0]

                                                                                                                                            parking_poly_pts_y=parking_poly_pts[1]-np_dist_both_pts[1]

                                                                                                                                            parking_poly_pts=[parking_poly_pts_x,parking_poly_pts_y]

                                                                                                                                            move_parking_polygon_pts.append(parking_poly_pts)

                                                                                                                                        np_move_parking_polygon_pts=np.array(move_parking_polygon_pts).round(2)

                                                                                                                                        #abs_np_move_parking_polygon_pts=abs(np_move_parking_polygon_pts)

                                                                                                                                        moved_parking_polygon_points=Polygon(np_move_parking_polygon_pts)

                                                                                                                                        front_data = []

                                                                                                                                        rear_data = []

                                                                                                                                        side1_data = []

                                                                                                                                        side2_data = []

                                                                                                                                        for insert in margin_data:

                                                                                                                                            if insert.dxftype()=='INSERT':

                                                                                                                                                for margin_entity in insert.virtual_entities():

                                                                                                                                                    if margin_entity.dxftype()=='LINE':

                                                                                                                                                        if margin_entity.dxf.color==1:

                                                                                                                                                            f_margin_line_start_pts=[margin_entity.dxf.start[0],margin_entity.dxf.start[1]]

                                                                                                                                                            f_margin_line_end_pts=[margin_entity.dxf.end[0],margin_entity.dxf.end[1]]

                                                                                                                                                            f_margin_line_pts=[f_margin_line_start_pts,f_margin_line_end_pts]

                                                                                                                                                            np_f_margin_line_pts=np.array(f_margin_line_pts).round(2)

                                                                                                                                                            #abs_np_f_margin_line_pts=abs(np_f_margin_line_pts)

                                                                                                                                                            f_margin_line_point=LineString(np_f_margin_line_pts)

                                                                                                                                                            front_data.append(round(f_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                                        elif(margin_entity.dxf.color==6):

                                                                                                                                                            r_margin_line_start_pts=[margin_entity.dxf.start[0],margin_entity.dxf.start[1]]

                                                                                                                                                            r_margin_line_end_pts=[margin_entity.dxf.end[0],margin_entity.dxf.end[1]]

                                                                                                                                                            r_margin_line_pts=[r_margin_line_start_pts,r_margin_line_end_pts]

                                                                                                                                                            np_r_margin_line_pts=np.array(r_margin_line_pts).round(2)

                                                                                                                                                            #abs_np_r_margin_line_pts=abs(np_r_margin_line_pts)

                                                                                                                                                            r_margin_line_point=LineString(np_r_margin_line_pts)

                                                                                                                                                            rear_data.append(round(r_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                                        elif(margin_entity.dxf.color==5):

                                                                                                                                                            s1_margin_line_start_pts=[margin_entity.dxf.start[0],margin_entity.dxf.start[1]]

                                                                                                                                                            s1_margin_line_end_pts=[margin_entity.dxf.end[0],margin_entity.dxf.end[1]]

                                                                                                                                                            s1_margin_line_pts=[s1_margin_line_start_pts,s1_margin_line_end_pts]

                                                                                                                                                            np_s1_margin_line_pts=np.array(s1_margin_line_pts).round(2)

                                                                                                                                                            #abs_np_s1_margin_line_pts=abs(np_s1_margin_line_pts)

                                                                                                                                                            s1_margin_line_point=LineString(np_s1_margin_line_pts)

                                                                                                                                                            side1_data.append(round(s1_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                                        elif(margin_entity.dxf.color==104 or margin_entity.dxf.color==3):

                                                                                                                                                            s2_margin_line_start_pts=[margin_entity.dxf.start[0],margin_entity.dxf.start[1]]

                                                                                                                                                            s2_margin_line_end_pts=[margin_entity.dxf.end[0],margin_entity.dxf.end[1]]

                                                                                                                                                            s2_margin_line_pts=[s2_margin_line_start_pts,s2_margin_line_end_pts]

                                                                                                                                                            np_s2_margin_line_pts=np.array(s2_margin_line_pts).round(2)

                                                                                                                                                            #abs_np_s2_margin_line_pts=abs(np_s2_margin_line_pts)

                                                                                                                                                            s2_margin_line_point=LineString(np_s2_margin_line_pts)

                                                                                                                                                            side2_data.append(round(s2_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                            elif insert.dxftype()=='LINE':

                                                                                                                                                    if insert.dxf.color==1:

                                                                                                                                                         f_margin_line_start_pts=[insert.dxf.start[0],insert.dxf.start[1]]

                                                                                                                                                         f_margin_line_end_pts=[insert.dxf.end[0],insert.dxf.end[1]]

                                                                                                                                                         f_margin_line_pts=[f_margin_line_start_pts,f_margin_line_end_pts]

                                                                                                                                                         np_f_margin_line_pts=np.array(f_margin_line_pts).round(2)

                                                                                                                                                         #abs_np_f_margin_line_pts=abs(np_f_margin_line_pts)

                                                                                                                                                         f_margin_line_point=LineString(np_f_margin_line_pts)

                                                                                                                                                         front_data.append(round(f_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                                    elif(insert.dxf.color==6):

                                                                                                                                                         r_margin_line_start_pts=[insert.dxf.start[0],insert.dxf.start[1]]

                                                                                                                                                         r_margin_line_end_pts=[insert.dxf.end[0],insert.dxf.end[1]]

                                                                                                                                                         r_margin_line_pts=[r_margin_line_start_pts,r_margin_line_end_pts]

                                                                                                                                                         np_r_margin_line_pts=np.array(r_margin_line_pts).round(2)

                                                                                                                                                         #abs_np_r_margin_line_pts=abs(np_r_margin_line_pts)

                                                                                                                                                         r_margin_line_point=LineString(np_r_margin_line_pts)

                                                                                                                                                         rear_data.append(round(r_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                                    elif(insert.dxf.color==5):

                                                                                                                                                          s1_margin_line_start_pts=[insert.dxf.start[0],insert.dxf.start[1]]

                                                                                                                                                          s1_margin_line_end_pts=[insert.dxf.end[0],insert.dxf.end[1]]

                                                                                                                                                          s1_margin_line_pts=[s1_margin_line_start_pts,s1_margin_line_end_pts]

                                                                                                                                                          np_s1_margin_line_pts=np.array(s1_margin_line_pts).round(2)

                                                                                                                                                          #abs_np_s1_margin_line_pts=abs(np_s1_margin_line_pts)

                                                                                                                                                          s1_margin_line_point=LineString(np_s1_margin_line_pts)

                                                                                                                                                          side1_data.append(round(s1_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                                    elif(insert.dxf.color==104 or insert.dxf.color==3):

                                                                                                                                                          s2_margin_line_start_pts=[insert.dxf.start[0],insert.dxf.start[1]]

                                                                                                                                                          s2_margin_line_end_pts=[insert.dxf.end[0],insert.dxf.end[1]]

                                                                                                                                                          s2_margin_line_pts=[s2_margin_line_start_pts,s2_margin_line_end_pts]

                                                                                                                                                          np_s2_margin_line_pts=np.array(s2_margin_line_pts).round(2)

                                                                                                                                                          #abs_np_s2_margin_line_pts=abs(np_s2_margin_line_pts)

                                                                                                                                                          s2_margin_line_point=LineString(np_s2_margin_line_pts)

                                                                                                                                                          side2_data.append(round(s2_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                        tmpPropWorkDict=dict()

                                                                                                                                        tmpPropWorkDict['BLDG_NAME']=building_text_name

                                                                                                                                        tmpPropWorkDict['NAME']=floor_text

                                                                                                                                        if front_data is not None:

                                                                                                                                            tmpPropWorkDict['FRONT']=str(min(front_data))

                                                                                                                                        if rear_data is not None:

                                                                                                                                            tmpPropWorkDict['REAR']=str(min(rear_data))

                                                                                                                                        if side1_data is not None:

                                                                                                                                            tmpPropWorkDict['SIDE1']=str(min(side1_data))

                                                                                                                                        if side2_data is not None:

                                                                                                                                            tmpPropWorkDict['SIDE2']=str(min(side2_data))

                                                                                                                                        returnValueDict[refid]=tmpPropWorkDict

                                                                                                                                    else:

                                                                                                                                        p1=np_margin_circle_center_pts

                                                                                                                                        p2=np_moved_floor_circle_center_pts

                                                                                                                                        p3=np_floor_margin_circle_center_pts

                                                                                                                                        get_angle=calculateAngle(p1[1],p1[0],p2[1],p2[0],p3[1],p3[0])

                                                                                                                                        #parking_polygon convert into points

                                                                                                                                        move_parking_polygon_pts=[]

                                                                                                                                        for parking_poly_pts in np_parking_polygon_pts:

                                                                                                                                           parking_poly_pts_x=parking_poly_pts[0]-np_dist_both_pts[0]

                                                                                                                                           parking_poly_pts_y=parking_poly_pts[1]-np_dist_both_pts[1]

                                                                                                                                           parking_poly_pts=[parking_poly_pts_x,parking_poly_pts_y]

                                                                                                                                           move_parking_polygon_pts.append(parking_poly_pts)

                                                                                                                                        update_parking_polygon_pts = []

                                                                                                                                        for pts in move_parking_polygon_pts:

                                                                                                                                          update_parking_polygon_pts.append(rotate_point_wrt_center(pts,get_angle,[np_parking_center_pts4[0],np_parking_center_pts4[1]]))

                                                                                                                                        np_move_parking_polygon_pts=np.array(update_parking_polygon_pts).round(2)

                                                                                                                                        #abs_np_move_parking_polygon_pts=abs(np_move_parking_polygon_pts)

                                                                                                                                        moved_parking_polygon_points=Polygon(np_move_parking_polygon_pts)

                                                                                                                                        front_data = []

                                                                                                                                        rear_data = []

                                                                                                                                        side1_data = []

                                                                                                                                        side2_data = []

                                                                                                                                        for insert in margin_data:

                                                                                                                                           if insert.dxftype()=='INSERT':

                                                                                                                                                for margin_entity in insert.virtual_entities():

                                                                                                                                                    if margin_entity.dxftype()=='LINE':

                                                                                                                                                        if margin_entity.dxf.color==1:

                                                                                                                                                            f_margin_line_start_pts=[margin_entity.dxf.start[0],margin_entity.dxf.start[1]]

                                                                                                                                                            f_margin_line_end_pts=[margin_entity.dxf.end[0],margin_entity.dxf.end[1]]

                                                                                                                                                            f_margin_line_pts=[f_margin_line_start_pts,f_margin_line_end_pts]

                                                                                                                                                            np_f_margin_line_pts=np.array(f_margin_line_pts).round(2)

                                                                                                                                                            #abs_np_f_margin_line_pts=abs(np_f_margin_line_pts)

                                                                                                                                                            f_margin_line_point=LineString(np_f_margin_line_pts)

                                                                                                                                                            front_data.append(round(f_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                                        elif(margin_entity.dxf.color==6):

                                                                                                                                                            r_margin_line_start_pts=[margin_entity.dxf.start[0],margin_entity.dxf.start[1]]

                                                                                                                                                            r_margin_line_end_pts=[margin_entity.dxf.end[0],margin_entity.dxf.end[1]]

                                                                                                                                                            r_margin_line_pts=[r_margin_line_start_pts,r_margin_line_end_pts]

                                                                                                                                                            np_r_margin_line_pts=np.array(r_margin_line_pts).round(2)

                                                                                                                                                            #abs_np_r_margin_line_pts=abs(np_r_margin_line_pts)

                                                                                                                                                            r_margin_line_point=LineString(np_r_margin_line_pts)

                                                                                                                                                            rear_data.append(round(r_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                                        elif(margin_entity.dxf.color==5):

                                                                                                                                                            s1_margin_line_start_pts=[margin_entity.dxf.start[0],margin_entity.dxf.start[1]]

                                                                                                                                                            s1_margin_line_end_pts=[margin_entity.dxf.end[0],margin_entity.dxf.end[1]]

                                                                                                                                                            s1_margin_line_pts=[s1_margin_line_start_pts,s1_margin_line_end_pts]

                                                                                                                                                            np_s1_margin_line_pts=np.array(s1_margin_line_pts).round(2)

                                                                                                                                                            #abs_np_s1_margin_line_pts=abs(np_s1_margin_line_pts)

                                                                                                                                                            s1_margin_line_point=LineString(np_s1_margin_line_pts)

                                                                                                                                                            side1_data.append(round(s1_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                                        elif(margin_entity.dxf.color==104 or margin_entity.dxf.color==3):

                                                                                                                                                            s2_margin_line_start_pts=[margin_entity.dxf.start[0],margin_entity.dxf.start[1]]

                                                                                                                                                            s2_margin_line_end_pts=[margin_entity.dxf.end[0],margin_entity.dxf.end[1]]

                                                                                                                                                            s2_margin_line_pts=[s2_margin_line_start_pts,s2_margin_line_end_pts]

                                                                                                                                                            np_s2_margin_line_pts=np.array(s2_margin_line_pts).round(2)

                                                                                                                                                            #abs_np_s2_margin_line_pts=abs(np_s2_margin_line_pts)

                                                                                                                                                            s2_margin_line_point=LineString(np_s2_margin_line_pts)

                                                                                                                                                            side2_data.append(round(s2_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                           elif insert.dxftype() == 'LINE':

                                                                                                                                               if insert.dxf.color == 1:

                                                                                                                                                   f_margin_line_start_pts = [insert.dxf.start[0],insert.dxf.start[1]]

                                                                                                                                                   f_margin_line_end_pts = [insert.dxf.end[0],insert.dxf.end[1]]

                                                                                                                                                   f_margin_line_pts = [f_margin_line_start_pts,f_margin_line_end_pts]

                                                                                                                                                   np_f_margin_line_pts = np.array(f_margin_line_pts).round(2)

                                                                                                                                                   # abs_np_f_margin_line_pts=abs(np_f_margin_line_pts)

                                                                                                                                                   f_margin_line_point = LineString(np_f_margin_line_pts)

                                                                                                                                                   front_data.append(round(f_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                               elif (insert.dxf.color == 6):

                                                                                                                                                   r_margin_line_start_pts = [insert.dxf.start[0],insert.dxf.start[1]]

                                                                                                                                                   r_margin_line_end_pts = [insert.dxf.end[0],insert.dxf.end[1]]

                                                                                                                                                   r_margin_line_pts = [r_margin_line_start_pts,r_margin_line_end_pts]

                                                                                                                                                   np_r_margin_line_pts = np.array(r_margin_line_pts).round(2)

                                                                                                                                                   # abs_np_r_margin_line_pts=abs(np_r_margin_line_pts)

                                                                                                                                                   r_margin_line_point = LineString(np_r_margin_line_pts)

                                                                                                                                                   rear_data.append(round(r_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                               elif (insert.dxf.color == 5):

                                                                                                                                                   s1_margin_line_start_pts = [insert.dxf.start[0],insert.dxf.start[1]]

                                                                                                                                                   s1_margin_line_end_pts = [insert.dxf.end[0],insert.dxf.end[1]]

                                                                                                                                                   s1_margin_line_pts = [s1_margin_line_start_pts,s1_margin_line_end_pts]

                                                                                                                                                   np_s1_margin_line_pts = np.array(s1_margin_line_pts).round(2)

                                                                                                                                                   # abs_np_s1_margin_line_pts=abs(np_s1_margin_line_pts)

                                                                                                                                                   s1_margin_line_point = LineString(np_s1_margin_line_pts)

                                                                                                                                                   side1_data.append(round(s1_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                               elif (insert.dxf.color == 104 or insert.dxf.color ==3):

                                                                                                                                                   s2_margin_line_start_pts = [insert.dxf.start[0],insert.dxf.start[1]]

                                                                                                                                                   s2_margin_line_end_pts = [insert.dxf.end[0],insert.dxf.end[1]]

                                                                                                                                                   s2_margin_line_pts = [s2_margin_line_start_pts,s2_margin_line_end_pts]

                                                                                                                                                   np_s2_margin_line_pts = np.array(s2_margin_line_pts).round(2)

                                                                                                                                                   # abs_np_s2_margin_line_pts=abs(np_s2_margin_line_pts)

                                                                                                                                                   s2_margin_line_point = LineString(np_s2_margin_line_pts)

                                                                                                                                                   side2_data.append(round(s2_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                        tmpPropWorkDict=dict()

                                                                                                                                        tmpPropWorkDict['BLDG_NAME']=building_text_name

                                                                                                                                        tmpPropWorkDict['NAME']=floor_text

                                                                                                                                        if front_data is not None:

                                                                                                                                            tmpPropWorkDict['FRONT']=str(min(front_data))

                                                                                                                                        if rear_data is not None:

                                                                                                                                            tmpPropWorkDict['REAR']=str(min(rear_data))

                                                                                                                                        if side1_data is not None:

                                                                                                                                            tmpPropWorkDict['SIDE1']=str(min(side1_data))

                                                                                                                                        if side2_data is not None:

                                                                                                                                            tmpPropWorkDict['SIDE2']=str(min(side2_data))

                                                                                                                                        returnValueDict[refid]=tmpPropWorkDict


                                                                                                                                elif(np_margin_circle_center_pts[0]==np_parking_center_pts4[0] and np_margin_circle_center_pts[1]==np_parking_center_pts4[1]):

                                                                                                                                    moved_floor_circle_center_ptsx=np_floor_circle_center_pts[0]+np_dist_both_pts[0]

                                                                                                                                    moved_floor_circle_center_ptsy=np_floor_circle_center_pts[1]-np_dist_both_pts[1]

                                                                                                                                    moved_floor_circle_center_pts=[moved_floor_circle_center_ptsx,moved_floor_circle_center_ptsy]

                                                                                                                                    np_moved_floor_circle_center_pts=np.array(moved_floor_circle_center_pts).round(2)

                                                                                                                                    #abs_np_moved_floor_circle_center_pts=abs(np_moved_floor_circle_center_pts)

                                                                                                                                    if np_floor_margin_circle_center_pts[0]==np_moved_floor_circle_center_pts[0] and np_floor_margin_circle_center_pts[1]==np_moved_floor_circle_center_pts[1]:

                                                                                                                                        #parking_polygon convert into points

                                                                                                                                        move_parking_polygon_pts=[]

                                                                                                                                        for parking_poly_pts in np_parking_polygon_pts:

                                                                                                                                            parking_poly_pts_x=parking_poly_pts[0]+np_dist_both_pts[0]

                                                                                                                                            parking_poly_pts_y=parking_poly_pts[1]-np_dist_both_pts[1]

                                                                                                                                            parking_poly_pts=[parking_poly_pts_x,parking_poly_pts_y]

                                                                                                                                            move_parking_polygon_pts.append(parking_poly_pts)

                                                                                                                                        np_move_parking_polygon_pts=np.array(move_parking_polygon_pts).round(2)

                                                                                                                                        #abs_np_move_parking_polygon_pts=abs(np_move_parking_polygon_pts)

                                                                                                                                        moved_parking_polygon_points=Polygon(np_move_parking_polygon_pts)

                                                                                                                                        front_data = []

                                                                                                                                        rear_data = []

                                                                                                                                        side1_data = []

                                                                                                                                        side2_data = []

                                                                                                                                        for insert in margin_data:

                                                                                                                                            if insert.dxftype()=='INSERT':

                                                                                                                                                for margin_entity in insert.virtual_entities():

                                                                                                                                                    if margin_entity.dxftype()=='LINE':

                                                                                                                                                        if margin_entity.dxf.color==1:

                                                                                                                                                            f_margin_line_start_pts=[margin_entity.dxf.start[0],margin_entity.dxf.start[1]]

                                                                                                                                                            f_margin_line_end_pts=[margin_entity.dxf.end[0],margin_entity.dxf.end[1]]

                                                                                                                                                            f_margin_line_pts=[f_margin_line_start_pts,f_margin_line_end_pts]

                                                                                                                                                            np_f_margin_line_pts=np.array(f_margin_line_pts).round(2)

                                                                                                                                                            #abs_np_f_margin_line_pts=abs(np_f_margin_line_pts)

                                                                                                                                                            f_margin_line_point=LineString(np_f_margin_line_pts)

                                                                                                                                                            front_data.append(round(f_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                                        elif(margin_entity.dxf.color==6):

                                                                                                                                                            r_margin_line_start_pts=[margin_entity.dxf.start[0],margin_entity.dxf.start[1]]

                                                                                                                                                            r_margin_line_end_pts=[margin_entity.dxf.end[0],margin_entity.dxf.end[1]]

                                                                                                                                                            r_margin_line_pts=[r_margin_line_start_pts,r_margin_line_end_pts]

                                                                                                                                                            np_r_margin_line_pts=np.array(r_margin_line_pts).round(2)

                                                                                                                                                            #abs_np_r_margin_line_pts=abs(np_r_margin_line_pts)

                                                                                                                                                            r_margin_line_point=LineString(np_r_margin_line_pts)

                                                                                                                                                            rear_data.append(round(r_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                                        elif(margin_entity.dxf.color==5):

                                                                                                                                                            s1_margin_line_start_pts=[margin_entity.dxf.start[0],margin_entity.dxf.start[1]]

                                                                                                                                                            s1_margin_line_end_pts=[margin_entity.dxf.end[0],margin_entity.dxf.end[1]]

                                                                                                                                                            s1_margin_line_pts=[s1_margin_line_start_pts,s1_margin_line_end_pts]

                                                                                                                                                            np_s1_margin_line_pts=np.array(s1_margin_line_pts).round(2)

                                                                                                                                                            #abs_np_s1_margin_line_pts=abs(np_s1_margin_line_pts)

                                                                                                                                                            s1_margin_line_point=LineString(np_s1_margin_line_pts)

                                                                                                                                                            side1_data.append(round(s1_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                                        elif(margin_entity.dxf.color==104 or margin_entity.dxf.color==3):

                                                                                                                                                            s2_margin_line_start_pts=[margin_entity.dxf.start[0],margin_entity.dxf.start[1]]

                                                                                                                                                            s2_margin_line_end_pts=[margin_entity.dxf.end[0],margin_entity.dxf.end[1]]

                                                                                                                                                            s2_margin_line_pts=[s2_margin_line_start_pts,s2_margin_line_end_pts]

                                                                                                                                                            np_s2_margin_line_pts=np.array(s2_margin_line_pts).round(2)

                                                                                                                                                            #abs_np_s2_margin_line_pts=abs(np_s2_margin_line_pts)

                                                                                                                                                            s2_margin_line_point=LineString(np_s2_margin_line_pts)

                                                                                                                                                            side2_data.append(round(s2_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                            elif(insert.dxftype()=='LINE'):

                                                                                                                                                if insert.dxf.color == 1:

                                                                                                                                                    f_margin_line_start_pts = [insert.dxf.start[0],insert.dxf.start[1]]

                                                                                                                                                    f_margin_line_end_pts = [insert.dxf.end[0],insert.dxf.end[1]]

                                                                                                                                                    f_margin_line_pts = [f_margin_line_start_pts,f_margin_line_end_pts]

                                                                                                                                                    np_f_margin_line_pts = np.array(f_margin_line_pts).round(2)

                                                                                                                                                    # abs_np_f_margin_line_pts=abs(np_f_margin_line_pts)

                                                                                                                                                    f_margin_line_point = LineString(np_f_margin_line_pts)

                                                                                                                                                    front_data.append(round(f_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                                elif (insert.dxf.color == 6):

                                                                                                                                                    r_margin_line_start_pts = [insert.dxf.start[0],insert.dxf.start[1]]

                                                                                                                                                    r_margin_line_end_pts = [insert.dxf.end[0],insert.dxf.end[1]]

                                                                                                                                                    r_margin_line_pts = [r_margin_line_start_pts,r_margin_line_end_pts]

                                                                                                                                                    np_r_margin_line_pts = np.array(r_margin_line_pts).round(2)

                                                                                                                                                    # abs_np_r_margin_line_pts=abs(np_r_margin_line_pts)

                                                                                                                                                    r_margin_line_point = LineString(np_r_margin_line_pts)

                                                                                                                                                    rear_data.append(round(r_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                                elif (insert.dxf.color == 5):

                                                                                                                                                    s1_margin_line_start_pts = [insert.dxf.start[0],insert.dxf.start[1]]

                                                                                                                                                    s1_margin_line_end_pts = [insert.dxf.end[0],insert.dxf.end[1]]

                                                                                                                                                    s1_margin_line_pts = [s1_margin_line_start_pts,s1_margin_line_end_pts]

                                                                                                                                                    np_s1_margin_line_pts = np.array(s1_margin_line_pts).round(2)

                                                                                                                                                    # abs_np_s1_margin_line_pts=abs(np_s1_margin_line_pts)

                                                                                                                                                    s1_margin_line_point = LineString(np_s1_margin_line_pts)

                                                                                                                                                    side1_data.append(round(s1_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                                elif (insert.dxf.color == 104 or insert.dxf.color ==3):

                                                                                                                                                    s2_margin_line_start_pts = [insert.dxf.start[0],insert.dxf.start[1]]

                                                                                                                                                    s2_margin_line_end_pts = [insert.dxf.end[0],insert.dxf.end[1]]

                                                                                                                                                    s2_margin_line_pts = [s2_margin_line_start_pts,s2_margin_line_end_pts]

                                                                                                                                                    np_s2_margin_line_pts = np.array(s2_margin_line_pts).round(2)

                                                                                                                                                    # abs_np_s2_margin_line_pts=abs(np_s2_margin_line_pts)

                                                                                                                                                    s2_margin_line_point = LineString(np_s2_margin_line_pts)

                                                                                                                                                    side2_data.append(round(s2_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                        tmpPropWorkDict=dict()

                                                                                                                                        tmpPropWorkDict['BLDG_NAME']=building_text_name

                                                                                                                                        tmpPropWorkDict['NAME']=floor_text

                                                                                                                                        if front_data is not None:

                                                                                                                                            tmpPropWorkDict['FRONT']=str(min(front_data))

                                                                                                                                        if rear_data is not None:

                                                                                                                                            tmpPropWorkDict['REAR']=str(min(rear_data))

                                                                                                                                        if side1_data is not None:

                                                                                                                                            tmpPropWorkDict['SIDE1']=str(min(side1_data))

                                                                                                                                        if side2_data is not None:

                                                                                                                                            tmpPropWorkDict['SIDE2']=str(min(side2_data))

                                                                                                                                        returnValueDict[refid]=tmpPropWorkDict

                                                                                                                                    else:

                                                                                                                                         move_parking_polygon_pts=[]

                                                                                                                                         for parking_poly_pts in np_parking_polygon_pts:

                                                                                                                                            parking_poly_pts_x=parking_poly_pts[0]+np_dist_both_pts[0]

                                                                                                                                            parking_poly_pts_y=parking_poly_pts[1]-np_dist_both_pts[1]

                                                                                                                                            parking_poly_pts=[parking_poly_pts_x,parking_poly_pts_y]

                                                                                                                                            move_parking_polygon_pts.append(parking_poly_pts)

                                                                                                                                         p1=np_margin_circle_center_pts

                                                                                                                                         p2=np_moved_floor_circle_center_pts

                                                                                                                                         p3=np_floor_margin_circle_center_pts

                                                                                                                                         get_angle=calculateAngle(p1[1],p1[0],p2[1],p2[0],p3[1],p3[0])

                                                                                                                                         update_parking_polygon_pts = []

                                                                                                                                         for pts in move_parking_polygon_pts:

                                                                                                                                            update_parking_polygon_pts.append(rotate_point_wrt_center(pts,get_angle,[np_parking_center_pts4[0],np_parking_center_pts4[1]]))

                                                                                                                                         np_move_parking_polygon_pts=np.array(update_parking_polygon_pts).round(2)

                                                                                                                                         #abs_np_move_parking_polygon_pts=abs(np_move_parking_polygon_pts)

                                                                                                                                         moved_parking_polygon_points=Polygon(np_move_parking_polygon_pts)

                                                                                                                                         front_data = []

                                                                                                                                         rear_data = []

                                                                                                                                         side1_data = []

                                                                                                                                         side2_data = []

                                                                                                                                         for insert in margin_data:

                                                                                                                                            if insert.dxftype()=='INSERT':

                                                                                                                                                for margin_entity in insert.virtual_entities():

                                                                                                                                                    if margin_entity.dxftype()=='LINE':

                                                                                                                                                        if margin_entity.dxf.color==1:

                                                                                                                                                            f_margin_line_start_pts=[margin_entity.dxf.start[0],margin_entity.dxf.start[1]]

                                                                                                                                                            f_margin_line_end_pts=[margin_entity.dxf.end[0],margin_entity.dxf.end[1]]

                                                                                                                                                            f_margin_line_pts=[f_margin_line_start_pts,f_margin_line_end_pts]

                                                                                                                                                            np_f_margin_line_pts=np.array(f_margin_line_pts).round(2)

                                                                                                                                                            #abs_np_f_margin_line_pts=abs(np_f_margin_line_pts)

                                                                                                                                                            f_margin_line_point=LineString(np_f_margin_line_pts)

                                                                                                                                                            front_data.append(round(f_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                                        elif(margin_entity.dxf.color==6):

                                                                                                                                                            r_margin_line_start_pts=[margin_entity.dxf.start[0],margin_entity.dxf.start[1]]

                                                                                                                                                            r_margin_line_end_pts=[margin_entity.dxf.end[0],margin_entity.dxf.end[1]]

                                                                                                                                                            r_margin_line_pts=[r_margin_line_start_pts,r_margin_line_end_pts]

                                                                                                                                                            np_r_margin_line_pts=np.array(r_margin_line_pts).round(2)

                                                                                                                                                            #abs_np_r_margin_line_pts=abs(np_r_margin_line_pts)

                                                                                                                                                            r_margin_line_point=LineString(np_r_margin_line_pts)

                                                                                                                                                            rear_data.append(round(r_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                                        elif(margin_entity.dxf.color==5):

                                                                                                                                                            s1_margin_line_start_pts=[margin_entity.dxf.start[0],margin_entity.dxf.start[1]]

                                                                                                                                                            s1_margin_line_end_pts=[margin_entity.dxf.end[0],margin_entity.dxf.end[1]]

                                                                                                                                                            s1_margin_line_pts=[s1_margin_line_start_pts,s1_margin_line_end_pts]

                                                                                                                                                            np_s1_margin_line_pts=np.array(s1_margin_line_pts).round(2)

                                                                                                                                                            #abs_np_s1_margin_line_pts=abs(np_s1_margin_line_pts)

                                                                                                                                                            s1_margin_line_point=LineString(np_s1_margin_line_pts)

                                                                                                                                                            side1_data.append(round(s1_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                                        elif(margin_entity.dxf.color==104 or margin_entity.dxf.color==3):

                                                                                                                                                            s2_margin_line_start_pts=[margin_entity.dxf.start[0],margin_entity.dxf.start[1]]

                                                                                                                                                            s2_margin_line_end_pts=[margin_entity.dxf.end[0],margin_entity.dxf.end[1]]

                                                                                                                                                            s2_margin_line_pts=[s2_margin_line_start_pts,s2_margin_line_end_pts]

                                                                                                                                                            np_s2_margin_line_pts=np.array(s2_margin_line_pts).round(2)

                                                                                                                                                            #abs_np_s2_margin_line_pts=abs(np_s2_margin_line_pts)

                                                                                                                                                            s2_margin_line_point=LineString(np_s2_margin_line_pts)

                                                                                                                                                            side2_data.append(round(s2_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                            elif insert.dxftype() == 'LINE':

                                                                                                                                                if insert.dxf.color == 1:

                                                                                                                                                    f_margin_line_start_pts = [insert.dxf.start[0],insert.dxf.start[1]]

                                                                                                                                                    f_margin_line_end_pts = [insert.dxf.end[0],insert.dxf.end[1]]

                                                                                                                                                    f_margin_line_pts = [f_margin_line_start_pts,f_margin_line_end_pts]

                                                                                                                                                    np_f_margin_line_pts = np.array(f_margin_line_pts).round(2)

                                                                                                                                                    # abs_np_f_margin_line_pts=abs(np_f_margin_line_pts)

                                                                                                                                                    f_margin_line_point = LineString(np_f_margin_line_pts)

                                                                                                                                                    front_data.append(round(f_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                                elif (insert.dxf.color == 6):

                                                                                                                                                    r_margin_line_start_pts = [insert.dxf.start[0],insert.dxf.start[1]]

                                                                                                                                                    r_margin_line_end_pts = [insert.dxf.end[0],insert.dxf.end[1]]

                                                                                                                                                    r_margin_line_pts = [r_margin_line_start_pts,r_margin_line_end_pts]

                                                                                                                                                    np_r_margin_line_pts = np.array(r_margin_line_pts).round(2)

                                                                                                                                                    # abs_np_r_margin_line_pts=abs(np_r_margin_line_pts)

                                                                                                                                                    r_margin_line_point = LineString(np_r_margin_line_pts)

                                                                                                                                                    rear_data.append(round(r_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                                elif (insert.dxf.color == 5):

                                                                                                                                                    s1_margin_line_start_pts = [insert.dxf.start[0],insert.dxf.start[1]]

                                                                                                                                                    s1_margin_line_end_pts = [insert.dxf.end[0],insert.dxf.end[1]]

                                                                                                                                                    s1_margin_line_pts = [s1_margin_line_start_pts,s1_margin_line_end_pts]

                                                                                                                                                    np_s1_margin_line_pts = np.array(s1_margin_line_pts).round(2)

                                                                                                                                                    # abs_np_s1_margin_line_pts=abs(np_s1_margin_line_pts)

                                                                                                                                                    s1_margin_line_point = LineString(np_s1_margin_line_pts)

                                                                                                                                                    side1_data.append(round(s1_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                                elif (insert.dxf.color == 104 or insert.dxf.color ==3):

                                                                                                                                                    s2_margin_line_start_pts = [insert.dxf.start[0],insert.dxf.start[1]]

                                                                                                                                                    s2_margin_line_end_pts = [insert.dxf.end[0],insert.dxf.end[1]]

                                                                                                                                                    s2_margin_line_pts = [s2_margin_line_start_pts,s2_margin_line_end_pts]

                                                                                                                                                    np_s2_margin_line_pts = np.array(s2_margin_line_pts).round(2)

                                                                                                                                                    # abs_np_s2_margin_line_pts=abs(np_s2_margin_line_pts)

                                                                                                                                                    s2_margin_line_point = LineString(np_s2_margin_line_pts)

                                                                                                                                                    side2_data.append(round(s2_margin_line_point.distance(moved_parking_polygon_points),2))

                                                                                                                                         tmpPropWorkDict=dict()

                                                                                                                                         tmpPropWorkDict['BLDG_NAME']=building_text_name

                                                                                                                                         tmpPropWorkDict['NAME']=floor_text

                                                                                                                                         if front_data is not None:

                                                                                                                                             tmpPropWorkDict['FRONT']=str(min(front_data))

                                                                                                                                         if rear_data is not None:

                                                                                                                                             tmpPropWorkDict['REAR']=str(min(rear_data))

                                                                                                                                         if side1_data is not None:

                                                                                                                                             tmpPropWorkDict['SIDE1']=str(min(side1_data))

                                                                                                                                         if side2_data is not None:

                                                                                                                                             tmpPropWorkDict['SIDE2']=str(min(side2_data))

                                                                                                                                         returnValueDict[refid]=tmpPropWorkDict


    except IndexError:

        print(f'Does not match any value')

        return returnValueDict

    except IOError:

        print(f'Not a DXF file or a generic I/O error.')

        return returnValueDict

    except ezdxf.DXFStructureError:

             print(f'Invalid or corrupted DXF file.')

             return returnValueDict

    return returnValueDict

def Polygon_touched_gl_line(gl_line,floorInSectionTEXTData,floorInSectionPolygonData):

    polygon_touch_gl_line_data=[]

    for FloorInSectionPolygon in floorInSectionPolygonData:

        FloorInSectionPolygon_points=Polygon(np.array([fisp[0:2] for fisp in FloorInSectionPolygon.get_points()]))

        for floorInSectiontext in floorInSectionTEXTData:

            floorInSectiontext_id=floorInSectiontext.dxf.handle

            floorInSectionText_properties=floorInSectiontext.dxfattribs()

            floorInSectionText=floorInSectionText_properties.get('text') if floorInSectiontext.dxftype()=='TEXT' else floorInSectiontext.plain_text()

            FloorINSectionText_pts=floorInSectionText_properties.get('insert')

            FloorINSectionText_point=Point(np.array([FloorINSectionText_pts[0],FloorINSectionText_pts[1]]))

            if FloorInSectionPolygon_points.contains(FloorINSectionText_point)==True or FloorInSectionPolygon_points.touches(FloorINSectionText_point)==True:

                if FloorInSectionPolygon_points.contains(gl_line)==True or round(FloorInSectionPolygon_points.distance(gl_line),1)==0.0:

                    polygon_touch_gl_line_data.append([floorInSectiontext_id,floorInSectionText,FloorInSectionPolygon_points])

    return polygon_touch_gl_line_data

def cellar_plinth_dist(msp):

   areturnValueDict=dict()

   aresultsList=[]

   if (msp is None):

       return aresultsList

   #dxf_path=os.path.join(folder,filename)

   try:

       #read_dxf=ezdxf.readfile(dxf_path)

       print('plinth dist read file')

       #msp=read_dxf.modelspace()

       building_text_data=msp.query('MTEXT TEXT[layer=="_BuildingName"]')

       building_polygon_data=msp.query('LWPOLYLINE[layer=="_BuildingName"]')

       section_polygon_data=msp.query('LWPOLYLINE[layer=="_Section"]')

       groun_level_line_data=msp.query('LWPOLYLINE[layer=="_GroundLevel"]')

       floor_in_section_text_data=msp.query('TEXT MTEXT[layer=="_FloorInSection"]')

       floor_in_section_polygon_data=msp.query('LWPOLYLINE[layer=="_FloorInSection"]')

       #Building text

       for building_text in building_text_data:

           building_text_attribs=building_text.dxfattribs()

           building_text_insert=building_text_attribs.get('insert')

           building_name=building_text_attribs.get('text') if building_text.dxftype()=='TEXT' else building_text.plain_text()

           if building_name!='':

                building_text_pts=[building_text_insert[0],building_text_insert[1]]

                np_building_text_pts=np.array(building_text_pts)

                building_text_point=Point(np_building_text_pts)

                #Building polygon data

                for building_polygon in building_polygon_data:

                    building_polygon_pts=[bp[0:2] for bp in building_polygon.get_points()]

                    building_ref_id=building_polygon.dxf.handle

                    np_building_polygon_pts=np.array(building_polygon_pts).round(1)

                    building_polygon_points=Polygon(np_building_polygon_pts)

                    #building polygon contains building text data

                    if building_polygon_points.contains(building_text_point)==True or building_polygon_points.touches(building_text_point)==True or round(building_polygon_points.distance(building_text_point),1)==0.0:

                         for section_polygon in section_polygon_data:

                            section_polygon_pts=[sp[0:2] for sp in section_polygon.get_points()]

                            np_section_polygon_pts=np.array(section_polygon_pts).round(1)

                            section_polygon_points=Polygon(np_section_polygon_pts)

                            if building_polygon_points.contains(section_polygon_points)==True:

                                #print(f'section polygon points=={section_polygon_points}')

                                #for ground level line data

                                for ground_level_line in groun_level_line_data:

                                    ground_level_line_pts=[gll[0:2] for gll in ground_level_line.get_points()]

                                    np_ground_level_line_pts=np.array(ground_level_line_pts).round(1)

                                    ground_level_line_points=LineString(np_ground_level_line_pts)

                                    # check section polygon points contains ground level line

                                    if section_polygon_points.contains(ground_level_line_points)==True:

                                        #print(f'Ground polygon points=={ground_level_line_points}')

                                        polygon_touch_to_gl_line = Polygon_touched_gl_line(ground_level_line_points,floor_in_section_text_data,floor_in_section_polygon_data)
                                        #for floor in section text data

                                        for floor_in_section_text in floor_in_section_text_data:

                                             floor_in_section_attribs=floor_in_section_text.dxfattribs()

                                             floor_in_section_name=floor_in_section_attribs.get('text') if floor_in_section_text.dxftype()=='TEXT' else floor_in_section_text.plain_text()

                                             #check only plinth floor data

                                             if 'plinth' in floor_in_section_name.lower():

                                                 floor_in_section_insert=floor_in_section_attribs.get('insert')

                                                 floor_insection_text_pts=[floor_in_section_insert[0],floor_in_section_insert[1]]

                                                 np_floor_insection_text_pts=np.array(floor_insection_text_pts).round(1)

                                                 abs_np_floor_in_section_point=Point(np_floor_insection_text_pts)

                                                 plinth_height_data=[]

                                                 for floor_in_section_polygon in floor_in_section_polygon_data:

                                                     floor_in_section_polygon_pts=[fsp[0:2] for fsp in floor_in_section_polygon.get_points()]

                                                     np_floor_in_section_polygon_pts=np.array(floor_in_section_polygon_pts).round(1)

                                                     floor_in_section_polygon_points=Polygon(np_floor_in_section_polygon_pts)

                                                     # check floor in section polygon data contains floor in section text

                                                     if floor_in_section_polygon_points.contains(abs_np_floor_in_section_point)==True or floor_in_section_polygon_points.touches(abs_np_floor_in_section_point)==True:

                                                         # check floor in section polygon contains section polygon

                                                         if section_polygon_points.contains(floor_in_section_polygon_points)==True:

                                                             #print(floor_in_section_name)

                                                             bounding_box=floor_in_section_polygon_points.minimum_rotated_rectangle

                                                             x, y =bounding_box.exterior.coords.xy

                                                             edge_length = (Point(x[0], y[0]).distance(Point(x[1], y[1])), Point(x[1], y[1]).distance(Point(x[2], y[2])))

                                                             plinth_floor_height = round(min(edge_length),1)

                                                             plinth_height_data.append(plinth_floor_height)

                                                             #print(plinth_floor_height)

                                                 if len(plinth_height_data)>0:

                                                     areturnValueDict[building_ref_id]=f'{building_name},{plinth_height_data[0]}'

                                             else:

                                                 if 'ground' in floor_in_section_name.lower() or 'stilt' in floor_in_section_name.lower():

                                                     floor_in_section_insert=floor_in_section_attribs.get('insert')

                                                     floor_insection_text_pts=[floor_in_section_insert[0],floor_in_section_insert[1]]

                                                     np_floor_insection_text_pts=np.array(floor_insection_text_pts).round(1)

                                                     abs_np_floor_in_section_point=Point(np_floor_insection_text_pts)

                                                     #print(abs_np_floor_in_section_point)

                                                     #for floor in section polygon data

                                                     floor_in_section_data=[]

                                                     for floor_in_section_polygon in floor_in_section_polygon_data:

                                                         floor_in_section_polygon_pts=[fsp[0:2] for fsp in floor_in_section_polygon.get_points()]

                                                         floor_in_section_id=floor_in_section_polygon.dxf.handle

                                                         np_floor_in_section_polygon_pts=np.array(floor_in_section_polygon_pts).round(1)

                                                         floor_in_section_polygon_points=Polygon(np_floor_in_section_polygon_pts)

                                                         # check floor in section polygon data contains floor in section text

                                                         if floor_in_section_polygon_points.contains(abs_np_floor_in_section_point)==True or floor_in_section_polygon_points.touches(abs_np_floor_in_section_point)==True:

                                                             # check floor in section polygon contains section polygon

                                                             if section_polygon_points.contains(floor_in_section_polygon_points)==True:

                                                                 gl_to_ground_floor_dist=round(ground_level_line_points.distance(floor_in_section_polygon_points),1)

                                                                 aTempDict=dict()

                                                                 aTempDict['BLDG_ID'] = building_ref_id

                                                                 aTempDict['BLDG_NAME'] = building_name

                                                                 aTempDict['FLOOR_SECTION_ID']=polygon_touch_to_gl_line[0][0]

                                                                 aTempDict['FLOOR_NAME']=polygon_touch_to_gl_line[0][1]

                                                                 aTempDict['GL_DISTANCE']=str(gl_to_ground_floor_dist)

                                                                 floor_in_section_data.append(aTempDict)

                                                     if len(floor_in_section_data)>0:

                                                         aresultsList.append(floor_in_section_data[0])


   except IndexError:

        print(f'Does not match any value')

        return aresultsList#areturnValueDict

   except IOError:

        print(f'Not a DXF file or a generic I/O error.')

        return aresultsList#areturnValueDict

   except ezdxf.DXFStructureError:

        print(f'Invalid or corrupted DXF file.')

        return aresultsList#areturnValueDict

   return aresultsList#areturnValueDict


##path of the filename

#folder=r'E:\production_code\dxf_files'

##Pass extension - removed inside method

#filename='22235.dxf'   # e give only filename

#dxf_path=os.path.join(folder,filename)

#dxf_file=ezdxf.readfile(dxf_path)

#msp=dxf_file.modelspace()

##method returns a dict with handle

#response1=check_cellar_setbacks(msp)

#response2=cellar_plinth_dist(msp)

#final_dict=dict()

#final_dict['Cellar Setbacks  Response']=response1

#final_dict['Plinth Height Response']=response2

#print(final_dict)