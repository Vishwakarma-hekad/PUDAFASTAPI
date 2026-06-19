import os
import ezdxf
from shapely.geometry import Point,Polygon
from shapely.geometry import LineString
import numpy as np

def dist_of_sept_tank(msp):#folder:str,filename:str):

    returnValueDict=dict()

    resultsList=[]

    if (msp is None):#folder is None or filename is None):

        return returnValueDict

    #dxf_path=os.path.join(folder,filename)

    try:

        #read_dxf=ezdxf.readfile(dxf_path)

        #print('read file')

        #msp=read_dxf.modelspace()

        for acessory_use_text in msp.query('MTEXT[layer=="_AccessoryUse"]'):

            accessory_use_attribs=acessory_use_text.dxfattribs()

            accessory_name=acessory_use_text.text

            if 'SEPTIC' in accessory_name.upper() or 'DISTRIBUTION' in accessory_name.upper() or  'TRANSFORMER' in accessory_name.upper() or 'SEWAGE'  in accessory_name.upper() or 'STP'  in accessory_name.upper() :

                accessory_use_insert=accessory_use_attribs.get('insert')

                accessory_use_text_pts=[accessory_use_insert[0],accessory_use_insert[1]]

                np_accessory_use_text_pts=np.array(accessory_use_text_pts).round(1)

                abs_np_accessory_use_text_pts=abs(np_accessory_use_text_pts)

                accessory_use_text_point=Point(abs_np_accessory_use_text_pts)

                for acessory_use_polygon in msp.query('LWPOLYLINE[layer=="_AccessoryUse"]'):

                    accessory_use_polygon_pts=[acp[0:2] for acp in acessory_use_polygon.get_points()]

                    accessory_use_id= acessory_use_polygon.dxf.handle

                    np_accessory_use_polygon_pts=np.array(accessory_use_polygon_pts).round(1)

                    np_accessory_use_polygon_pts=abs(np_accessory_use_polygon_pts)

                    accessory_use_polygon_points=Polygon(np_accessory_use_polygon_pts)

                    #check accessory polygon contains accessory text

                    if (accessory_use_polygon_points.contains(accessory_use_text_point)==True or accessory_use_polygon_points.touches(accessory_use_text_point)==True):

                        # for plot polygon

                        for plot_polygon in msp.query('LWPOLYLINE[layer=="_Plot"]'):

                            plot_polygon_pts=[pp[0:2] for pp in plot_polygon.get_points()]

                            np_plot_polygon_pts=np.array(plot_polygon_pts).round(2)

                            abs_np_plot_polygon_pts=abs(np_plot_polygon_pts)

                            plot_polygon_point=Polygon(abs_np_plot_polygon_pts)

                            if plot_polygon_point.contains(accessory_use_polygon_points)==True or plot_polygon_point.touches(accessory_use_polygon_points)==True or round(plot_polygon_point.distance(accessory_use_polygon_points))==0:
                                # for margin line

                                for margin_insert in msp.query('INSERT[layer=="_MarginLine"]'):

                                    Front_side=[]

                                    Rear_side=[]

                                    Side1=[]

                                    Side2=[]

                                    for margin_line in margin_insert.virtual_entities():

                                        if margin_line.dxftype()=='LINE':

                                            if margin_line.dxf.color==1:

                                                f_start_m_line_pts=[margin_line.dxf.start[0],margin_line.dxf.start[1]]

                                                f_end_m_line_pts=[margin_line.dxf.end[0],margin_line.dxf.end[1]]

                                                f_m_line_pts=[f_start_m_line_pts,f_end_m_line_pts]

                                                f_np_m_line_pts=np.array(f_m_line_pts).round(1)

                                                f_abs_np_m_line_pts=abs(f_np_m_line_pts)

                                                f_m_line_points=LineString(f_abs_np_m_line_pts)

                                                Front_side.append(round(f_m_line_points.distance(accessory_use_polygon_points),1))

                                            elif(margin_line.dxf.color==6):

                                                r_start_m_line_pts=[margin_line.dxf.start[0],margin_line.dxf.start[1]]

                                                r_end_m_line_pts=[margin_line.dxf.end[0],margin_line.dxf.end[1]]

                                                r_m_line_pts=[r_start_m_line_pts,r_end_m_line_pts]

                                                r_np_m_line_pts=np.array(r_m_line_pts).round(1)

                                                r_abs_np_m_line_pts=abs(r_np_m_line_pts)

                                                r_m_line_points=LineString(r_abs_np_m_line_pts)

                                                Rear_side.append(round(r_m_line_points.distance(accessory_use_polygon_points),1))

                                            elif(margin_line.dxf.color==5):

                                                s1_start_m_line_pts=[margin_line.dxf.start[0],margin_line.dxf.start[1]]

                                                s1_end_m_line_pts=[margin_line.dxf.end[0],margin_line.dxf.end[1]]

                                                s1_m_line_pts=[s1_start_m_line_pts,s1_end_m_line_pts]

                                                s1_np_m_line_pts=np.array(s1_m_line_pts).round(1)

                                                s1_abs_np_m_line_pts=abs(s1_np_m_line_pts)

                                                s1_m_line_points=LineString(s1_abs_np_m_line_pts)

                                                Side1.append(round(s1_m_line_points.distance(accessory_use_polygon_points),1))

                                            elif(margin_line.dxf.color==104):

                                                s2_start_m_line_pts=[margin_line.dxf.start[0],margin_line.dxf.start[1]]

                                                s2_end_m_line_pts=[margin_line.dxf.end[0],margin_line.dxf.end[1]]

                                                s2_m_line_pts=[s2_start_m_line_pts,s2_end_m_line_pts]

                                                s2_np_m_line_pts=np.array(s2_m_line_pts).round(1)

                                                s2_abs_np_m_line_pts=abs(s2_np_m_line_pts)

                                                s2_m_line_points=LineString(s2_abs_np_m_line_pts)

                                                Side2.append(round(s2_m_line_points.distance(accessory_use_polygon_points),1))

                                    tmpWorkDict=dict()

                                    if Front_side!=[]:

                                        tmpWorkDict['FRONT']=min(Front_side)

                                    if Rear_side!=[]:

                                        tmpWorkDict['REAR']=min(Rear_side)

                                    if Side1!=[]:

                                        tmpWorkDict['SIDE1']=min(Side1)

                                    if Side2!=[]:

                                        tmpWorkDict['SIDE2']=min(Side2)

                                dctvaly=tmpWorkDict.items()

                                min_dctvaly=min(dctvaly,key=lambda x: x[1])

                                returnValueDict[accessory_name]=min_dctvaly

                            else:
                                 # for building text data

                                 for building_text in msp.query('TEXT[layer=="_BuildingName"]'):

                                    building_text_attribs=building_text.dxfattribs()

                                    building_text_insert=building_text_attribs.get('insert')

                                    building_name=building_text_attribs.get('text')

                                    building_text_pts=[building_text_insert[0],building_text_insert[1]]

                                    np_building_text_pts=np.array(building_text_pts).round(1)

                                    abs_np_building_text_pts=abs(np_building_text_pts)

                                    building_text_point=Point(abs_np_building_text_pts)

                                    #building polygon data

                                    for building_polygon in msp.query('LWPOLYLINE[layer=="_BuildingName"]'):

                                        building_polygon_pts=[bp[0:2] for bp in building_polygon.get_points()]

                                        np_building_polygon_pts=np.array(building_polygon_pts).round(1)

                                        abs_np_building_polygon_pts=abs(np_building_polygon_pts)

                                        building_polygon_points=Polygon(abs_np_building_polygon_pts)

                                        #check building polygon contains building text data

                                        if building_polygon_points.contains(building_text_point)==True or building_polygon_points.touches(building_text_point)==True:

                                             filter_building_name="".join(x for x in building_name if x.isalpha())
                                             # Floor text data
                                             for floor_text in msp.query('TEXT[layer=="_Floor"]'):

                                                 floor_text_attribs=floor_text.dxfattribs()

                                                 floor_text_insert=floor_text_attribs.get('insert')

                                                 floor_name=floor_text_attribs.get('text')

                                                 # only cellar or Basement text data

                                                 if ('CELLAR' in floor_name) or ('BASEMENT' in floor_name):

                                                     floor_text_pts=[floor_text_insert[0],floor_text_insert[1]]

                                                     np_floor_text_pts=np.array(floor_text_pts).round(1)

                                                     abs_np_floor_text_pts=abs(np_floor_text_pts)

                                                     floor_text_point=Point(abs_np_floor_text_pts)

                                                     # Floor polygon data

                                                     for floor_polygon in msp.query('LWPOLYLINE[layer=="_Floor"]'):

                                                          floor_polygon_pts=[f[0:2] for f in floor_polygon.get_points()]

                                                          refid=floor_polygon.dxf.handle

                                                          np_floor_polygon_pts=np.array(floor_polygon_pts).round(1)

                                                          abs_np_floor_polygon_pts=abs(np_floor_polygon_pts)

                                                          floor_polygon_point=Polygon(abs_np_floor_polygon_pts)

                                                          #check floor polygon contains floor text data

                                                          if floor_polygon_point.contains(floor_text_point)==True or floor_polygon_point.touches(floor_text_point)==True:

                                                              #floor polygon contains accessory polygon

                                                              if floor_polygon_point.contains(accessory_use_polygon_points)==True:

                                                                  if building_polygon_points.contains(floor_polygon_point)==True:

                                                                    #for resibuaoutline circle center points

                                                                    for resibuaoutline_insert in msp.query('INSERT[layer=="_ResiBUAOutline"]'):

                                                                        for resibuaoutline_entity in resibuaoutline_insert.virtual_entities():

                                                                             if resibuaoutline_entity.dxftype()=='CIRCLE':

                                                                                circle_center_pts=resibuaoutline_entity.dxf.center

                                                                                np_circle_center_pts=np.array([circle_center_pts[0],circle_center_pts[1]]).round(1)

                                                                                abs_np_circle_center_pts=abs(np_circle_center_pts)

                                                                                circle_center_point=Point(abs_np_circle_center_pts)

                                                                                #check floor polygon contains resibuaoutline center points

                                                                                if floor_polygon_point.contains(circle_center_point)==True:

                                                                                    # for proposed work text data

                                                                                    for prop_work_text in msp.query('TEXT[layer=="_ProposedWork"]'):

                                                                                        prop_work_text_attribs=prop_work_text.dxfattribs()

                                                                                        prop_work_text_insert=prop_work_text_attribs.get('insert')

                                                                                        prop_work_name=prop_work_text_attribs.get('text')

                                                                                        prop_work_text_pts=[prop_work_text_insert[0],prop_work_text_insert[1]]

                                                                                        np_prop_work_text_pts=np.array(prop_work_text_pts).round(1)

                                                                                        abs_np_prop_work_text_pts=abs(np_prop_work_text_pts)

                                                                                        prop_work_text_point=Point(abs_np_prop_work_text_pts)

                                                                                        #proposed work polygon data

                                                                                        list_moved_polygon=[]

                                                                                        for prop_work_polygon in msp.query('LWPOLYLINE[layer=="_ProposedWork"]'):

                                                                                            prop_work_polygon_pts=[pwp[0:2] for pwp in prop_work_polygon.get_points()]

                                                                                            np_prop_work_polygon_pts=np.array(prop_work_polygon_pts).round(1)

                                                                                            abs_np_prop_work_polygon_pts=abs(np_prop_work_polygon_pts)

                                                                                            prop_work_polygon_points=Polygon(abs_np_prop_work_polygon_pts)

                                                                                            if prop_work_polygon_points.contains(prop_work_text_point)==True or prop_work_polygon_points.touches(prop_work_text_point)==True:

                                                                                                 for margin_resibuaoutline_insert in msp.query('INSERT[layer=="_ResiBUAOutline"]'):

                                                                                                     for margin_resibuaoutline_entity in margin_resibuaoutline_insert.virtual_entities():

                                                                                                        if margin_resibuaoutline_entity.dxftype()=='CIRCLE':

                                                                                                            margin_circle_center_pts=margin_resibuaoutline_entity.dxf.center

                                                                                                            np_margin_circle_center_pts=np.array([margin_circle_center_pts[0],margin_circle_center_pts[1]]).round(1)

                                                                                                            abs_np_margin_circle_center_pts=abs(np_margin_circle_center_pts)

                                                                                                            margin_circle_center_point=Point(abs_np_margin_circle_center_pts)

                                                                                                            if prop_work_polygon_points.contains(margin_circle_center_point)==True:

                                                                                                                filter_prop_work_name=filter_prop_work_name="".join(y for y in prop_work_name if y.isalpha())

                                                                                                                if filter_building_name==filter_prop_work_name:

                                                                                                                    np_both_pts=np.array([abs_np_margin_circle_center_pts,abs_np_circle_center_pts]).round(1)

                                                                                                                    max_np_both_pts=np_both_pts.max(axis=0)

                                                                                                                    min_np_both_pts=np_both_pts.min(axis=0)

                                                                                                                    dist_np_both_pts=max_np_both_pts-min_np_both_pts

                                                                                                                    np_dist_np_both_pts=np.array(dist_np_both_pts).round(1)

                                                                                                                    np_dist_np_both_pts=abs(np_dist_np_both_pts)

                                                                                                                    #-----------------First Quadrant center pts---------------------------
                                                                                                                    accessory_center_pts1_x=abs_np_circle_center_pts[0]-np_dist_np_both_pts[0]

                                                                                                                    accessory_center_pts1_y=abs_np_circle_center_pts[1]+np_dist_np_both_pts[1]

                                                                                                                    accessory_center_pts1=[accessory_center_pts1_x,accessory_center_pts1_y]

                                                                                                                    np_accessory_center_pts1=np.array(accessory_center_pts1).round(1)

                                                                                                                    abs_np_accessory_center_pts1=abs(np_accessory_center_pts1)

                                                                                                                    #-----------------Second Quadrant center pts---------------------------
                                                                                                                    accessory_center_pts2_x=abs_np_circle_center_pts[0]+np_dist_np_both_pts[0]

                                                                                                                    accessory_center_pts2_y=abs_np_circle_center_pts[1]+np_dist_np_both_pts[1]

                                                                                                                    accessory_center_pts2=[accessory_center_pts2_x,accessory_center_pts2_y]

                                                                                                                    np_accessory_center_pts2=np.array(accessory_center_pts2).round(1)

                                                                                                                    abs_np_accessory_center_pts2=abs(np_accessory_center_pts2)

                                                                                                                    #-----------------Third Quadrant center pts---------------------------
                                                                                                                    accessory_center_pts3_x=abs_np_circle_center_pts[0]-np_dist_np_both_pts[0]

                                                                                                                    accessory_center_pts3_y=abs_np_circle_center_pts[1]-np_dist_np_both_pts[1]

                                                                                                                    accessory_center_pts3=[accessory_center_pts3_x,accessory_center_pts3_y]

                                                                                                                    np_accessory_center_pts3=np.array(accessory_center_pts3).round(1)

                                                                                                                    abs_np_accessory_center_pts3=abs(np_accessory_center_pts3)

                                                                                                                    #-----------------Fourth Quadrant center pts---------------------------
                                                                                                                    accessory_center_pts4_x=abs_np_circle_center_pts[0]+np_dist_np_both_pts[0]

                                                                                                                    accessory_center_pts4_y=abs_np_circle_center_pts[1]-np_dist_np_both_pts[1]

                                                                                                                    accessory_center_pts4=[accessory_center_pts4_x,accessory_center_pts4_y]

                                                                                                                    np_accessory_center_pts4=np.array(accessory_center_pts4).round(1)

                                                                                                                    abs_np_accessory_center_pts4=abs(np_accessory_center_pts4)
                                                                                                                    #print(abs_np_accessory_center_pts1)
                                                                                                                    #print(abs_np_accessory_center_pts2)
                                                                                                                    #print(abs_np_accessory_center_pts3)
                                                                                                                    #print(abs_np_accessory_center_pts4)
                                                                                                                    #print('---------------------------')
                                                                                                                    if (abs_np_margin_circle_center_pts[0]==abs_np_accessory_center_pts1[0] and abs_np_margin_circle_center_pts[1]==abs_np_accessory_center_pts1[1]):

                                                                                                                        #accessory polygon convert into points

                                                                                                                        accessory_list_pts=[]

                                                                                                                        for accessory_pts in np_accessory_use_polygon_pts:

                                                                                                                            accessory_pts_x=accessory_pts[0]-np_dist_np_both_pts[0]

                                                                                                                            accessory_pts_y=accessory_pts[1]+np_dist_np_both_pts[1]

                                                                                                                            accessory_pts=[accessory_pts_x,accessory_pts_y]

                                                                                                                            accessory_list_pts.append(accessory_pts)

                                                                                                                        np_accessory_list_pts=np.array(accessory_list_pts).round(1)

                                                                                                                        abs_np_accessory_list_pts=abs(np_accessory_list_pts)

                                                                                                                        list_moved_polygon.append(abs_np_accessory_list_pts)

                                                                                                                    elif(abs_np_margin_circle_center_pts[0]==abs_np_accessory_center_pts2[0] and abs_np_margin_circle_center_pts[1]==abs_np_accessory_center_pts2[1]):

                                                                                                                        accessory_list_pts=[]

                                                                                                                        for accessory_pts in np_accessory_use_polygon_pts:

                                                                                                                            accessory_pts_x=accessory_pts[0]+np_dist_np_both_pts[0]

                                                                                                                            accessory_pts_y=accessory_pts[1]+np_dist_np_both_pts[1]

                                                                                                                            accessory_pts=[accessory_pts_x,accessory_pts_y]

                                                                                                                            accessory_list_pts.append(accessory_pts)

                                                                                                                        np_accessory_list_pts=np.array(accessory_list_pts).round(1)

                                                                                                                        abs_np_accessory_list_pts=abs(np_accessory_list_pts)

                                                                                                                        list_moved_polygon.append(abs_np_accessory_list_pts)

                                                                                                                    elif(abs_np_margin_circle_center_pts[0]==abs_np_accessory_center_pts3[0] and abs_np_margin_circle_center_pts[1]==abs_np_accessory_center_pts3[1]):

                                                                                                                        accessory_list_pts=[]

                                                                                                                        for accessory_pts in np_accessory_use_polygon_pts:

                                                                                                                            accessory_pts_x=accessory_pts[0]-np_dist_np_both_pts[0]

                                                                                                                            accessory_pts_y=accessory_pts[1]-np_dist_np_both_pts[1]

                                                                                                                            accessory_pts=[accessory_pts_x,accessory_pts_y]

                                                                                                                            accessory_list_pts.append(accessory_pts)

                                                                                                                        np_accessory_list_pts=np.array(accessory_list_pts).round(1)

                                                                                                                        abs_np_accessory_list_pts=abs(np_accessory_list_pts)

                                                                                                                        list_moved_polygon.append(abs_np_accessory_list_pts)

                                                                                                                    elif(abs_np_margin_circle_center_pts[0]==abs_np_accessory_center_pts4[0] and abs_np_margin_circle_center_pts[1]==abs_np_accessory_center_pts4[1]):

                                                                                                                        accessory_list_pts=[]

                                                                                                                        for accessory_pts in np_accessory_use_polygon_pts:

                                                                                                                            accessory_pts_x=accessory_pts[0]+np_dist_np_both_pts[0]

                                                                                                                            accessory_pts_y=accessory_pts[1]-np_dist_np_both_pts[1]

                                                                                                                            accessory_pts=[accessory_pts_x,accessory_pts_y]

                                                                                                                            accessory_list_pts.append(accessory_pts)

                                                                                                                        np_accessory_list_pts=np.array(accessory_list_pts).round(1)

                                                                                                                        abs_np_accessory_list_pts=abs(np_accessory_list_pts)

                                                                                                                        list_moved_polygon.append(abs_np_accessory_list_pts)



                                                                                        for moved_polygon_pts in list_moved_polygon:

                                                                                            accessory_moved_polygon_points=Polygon(moved_polygon_pts)

                                                                                            for insert in msp.query('INSERT[layer=="_MarginLine"]'):

                                                                                                front_data=[]

                                                                                                rear_data=[]

                                                                                                side1_data=[]

                                                                                                side2_data=[]

                                                                                                for margin_entity in insert.virtual_entities():

                                                                                                    if margin_entity.dxftype()=='LINE':

                                                                                                        if margin_entity.dxf.color==1:

                                                                                                            f_start_m_line_pts=[margin_entity.dxf.start[0],margin_entity.dxf.start[1]]

                                                                                                            f_end_m_line_pts=[margin_entity.dxf.end[0],margin_entity.dxf.end[1]]

                                                                                                            f_m_line_pts=[f_start_m_line_pts,f_end_m_line_pts]

                                                                                                            f_np_m_line_pts=np.array(f_m_line_pts).round(1)

                                                                                                            f_abs_np_m_line_pts=abs(f_np_m_line_pts)

                                                                                                            f_m_line_points=LineString(f_abs_np_m_line_pts)

                                                                                                            front_data.append(round(f_m_line_points.distance(accessory_moved_polygon_points),1))

                                                                                                        elif margin_entity.dxf.color==6:

                                                                                                            r_start_m_line_pts=[margin_entity.dxf.start[0],margin_entity.dxf.start[1]]

                                                                                                            r_end_m_line_pts=[margin_entity.dxf.end[0],margin_entity.dxf.end[1]]

                                                                                                            r_m_line_pts=[r_start_m_line_pts,r_end_m_line_pts]

                                                                                                            r_np_m_line_pts=np.array(r_m_line_pts).round(1)

                                                                                                            r_abs_np_m_line_pts=abs(r_np_m_line_pts)

                                                                                                            r_m_line_points=LineString(r_abs_np_m_line_pts)

                                                                                                            rear_data.append(round(r_m_line_points.distance(accessory_moved_polygon_points),1))

                                                                                                        elif margin_entity.dxf.color==5:

                                                                                                            s1_start_m_line_pts=[margin_entity.dxf.start[0],margin_entity.dxf.start[1]]

                                                                                                            s1_end_m_line_pts=[margin_entity.dxf.end[0],margin_entity.dxf.end[1]]

                                                                                                            s1_m_line_pts=[s1_start_m_line_pts,s1_end_m_line_pts]

                                                                                                            s1_np_m_line_pts=np.array(s1_m_line_pts).round(1)

                                                                                                            s1_abs_np_m_line_pts=abs(s1_np_m_line_pts)

                                                                                                            s1_m_line_points=LineString(s1_abs_np_m_line_pts)

                                                                                                            side1_data.append(round(s1_m_line_points.distance(accessory_moved_polygon_points),1))

                                                                                                        elif margin_entity.dxf.color==104:

                                                                                                            s2_start_m_line_pts=[margin_entity.dxf.start[0],margin_entity.dxf.start[1]]

                                                                                                            s2_end_m_line_pts=[margin_entity.dxf.end[0],margin_entity.dxf.end[1]]

                                                                                                            s2_m_line_pts=[s2_start_m_line_pts,s2_end_m_line_pts]

                                                                                                            s2_np_m_line_pts=np.array(s2_m_line_pts).round(1)

                                                                                                            s2_abs_np_m_line_pts=abs(s2_np_m_line_pts)

                                                                                                            s2_m_line_points=LineString(s2_abs_np_m_line_pts)

                                                                                                            side2_data.append(round(s2_m_line_points.distance(accessory_moved_polygon_points),1))

                                                                                                ctempWorkDict=dict()

                                                                                                if front_data!=[]:

                                                                                                    ctempWorkDict['FRONT']=min(front_data)

                                                                                                if rear_data!=[]:

                                                                                                    ctempWorkDict['REAR']=min(rear_data)

                                                                                                if side1_data!=[]:

                                                                                                    ctempWorkDict['SIDE1']=min(side1_data)

                                                                                                if side2_data!=[]:

                                                                                                    ctempWorkDict['SIDE2']=min(side2_data)

                                                                                                dctvalx=ctempWorkDict.items()

                                                                                                min_dctvalx=min(dctvalx,key=lambda x: x[1])

                                                                                                returnValueDict[accessory_name]=min_dctvalx




                                                #

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




# #path of the filename

# folder=r'E:\python'

# #Pass extension - removed inside method

# filename='1_cellar_vanajamam.dxf'                   # Here give only filename

# #method returns a dict with handle

# response=dist_of_sept_tank(folder,filename)

# print ('Minimum distance of Accessory ' , response )