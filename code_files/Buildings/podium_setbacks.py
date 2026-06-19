import os

import ezdxf

from shapely.geometry import Point,Polygon

from shapely.geometry import LineString

import numpy as np

import math

import time

def split(start,end,seg):  # this function used for Spliting the lines

    x_delta=(end[0]-start[0])/float(seg)

    y_delta=(end[1]-start[1])/float(seg)

    points=[]

    for i in range(1,seg):

        pts=[start[0]+i*x_delta,start[1]+i*y_delta]

        points.append(pts)

    return [start]+points+[end]


def podium_regular_setbacks(msp):#folder:str,filename:str):

    resultsList=[]

    returnValueDict=dict()

    if (msp is None):#folder is None or filename is None):

        return returnValueDict

    #dxf_path=os.path.join(folder,filename)

    try:

        #read_dxf=ezdxf.readfile(dxf_path)

        print('Processing Podium Building Regular setbacks ')

        #msp=read_dxf.modelspace()

        # for proposed text data

        for prop_text in msp.query("TEXT[layer=='_ProposedWork']"):

            prop_text_attribs=prop_text.dxfattribs()

            insert_prop_text=prop_text_attribs.get('insert')

            prop_text_name=prop_text_attribs.get('text')

            prop_text_pts=[insert_prop_text[0],insert_prop_text[1]]

            np_insert_prop_text_pts=np.array(prop_text_pts).round(2)

            prop_text_point=Point(np_insert_prop_text_pts)

            for lwpolyline in msp.query("LWPOLYLINE[layer=='_ProposedWork']"):

                prop_pts=[x[0:2] for x in lwpolyline.get_points()]

                np_prop_pts=np.array(prop_pts).round(2)

                prop_poly1=Polygon(np_prop_pts)

                # check propposed name in proposed polygon

                if prop_poly1.contains(prop_text_point)==True:

                    refid=lwpolyline.dxf.handle

                    front_data=[]

                    rear_data=[]

                    side1_data=[]

                    side2_data=[]

                    front_coordinate_data=[]

                    rear_coordinate_data=[]

                    side1_coordinate_data=[]

                    side2_coordinate_data=[]

                    for tpl in lwpolyline.virtual_entities():

                        start_pts=tpl.dxf.start

                        end_pts=tpl.dxf.end

                        linex=[[start_pts[0],start_pts[1]],[end_pts[0],end_pts[1]]]

                        np_linex=np.array(linex).round(2)

                        min_np_linex=np_linex.min(axis=0)

                        #split_prop_line=split(linex[0],linex[1],2)

                        prop_line=LineString(np_linex)

                        for insert1 in msp.query("INSERT[layer=='_MarginLine']"):

                            lstf=[]

                            lstr=[]

                            lsts1=[]

                            lsts2=[]

                            for m_entity in insert1.virtual_entities():

                                # read only line

                                if m_entity.dxftype()=='LINE':

                                    if m_entity.dxf.color==1:

                                        m_line_start_pts=[m_entity.dxf.start[0],m_entity.dxf.start[1]]

                                        m_line_end_pts=[m_entity.dxf.end[0],m_entity.dxf.end[1]]

                                        m_line_pts=[m_line_start_pts,m_line_end_pts]

                                        np_m_line_pts=np.array(m_line_pts).round(2)

                                        margin_linef=LineString(np_m_line_pts)

                                        lstf.append(round(prop_line.distance(margin_linef),1))

                                        front_coordinate_data.append([linex,np_m_line_pts])

                                    elif(m_entity.dxf.color==6):

                                        m_line_start_pts=[m_entity.dxf.start[0],m_entity.dxf.start[1]]

                                        m_line_end_pts=[m_entity.dxf.end[0],m_entity.dxf.end[1]]

                                        m_line_pts=[m_line_start_pts,m_line_end_pts]

                                        np_m_line_pts=np.array(m_line_pts).round(2)

                                        margin_liner=LineString(np_m_line_pts)

                                        lstr.append(round(prop_line.distance(margin_liner),1))

                                        rear_coordinate_data.append([linex,np_m_line_pts])

                                    elif(m_entity.dxf.color==5):

                                        m_line_start_pts=[m_entity.dxf.start[0],m_entity.dxf.start[1]]

                                        m_line_end_pts=[m_entity.dxf.end[0],m_entity.dxf.end[1]]

                                        m_line_pts=[m_line_start_pts,m_line_end_pts]

                                        np_m_line_pts=np.array(m_line_pts).round(2)

                                        margin_lines1=LineString(np_m_line_pts)

                                        lsts1.append(round(prop_line.distance(margin_lines1),1))

                                        side1_coordinate_data.append([linex,np_m_line_pts])


                                    elif(m_entity.dxf.color==104):

                                        m_line_start_pts=[m_entity.dxf.start[0],m_entity.dxf.start[1]]

                                        m_line_end_pts=[m_entity.dxf.end[0],m_entity.dxf.end[1]]

                                        m_line_pts=[m_line_start_pts,m_line_end_pts]

                                        np_m_line_pts=np.array(m_line_pts).round(2)

                                        margin_lines2=LineString(np_m_line_pts)

                                        lsts2.append(round(prop_line.distance(margin_lines2),1))

                                        side2_coordinate_data.append([linex,np_m_line_pts])

                            if lstf!=[]:

                                front_data.append(min(lstf))

                            if lstr!=[]:

                                rear_data.append(min(lstr))

                            if lsts1!=[]:

                                side1_data.append(min(lsts1))

                            if lsts2!=[]:

                                side2_data.append(min(lsts2))

                    # for Front side  data

                    fline_pts_value=[]

                    fline_pts=[]

                    for fdata in front_coordinate_data:

                        f_prop_linex=LineString(fdata[0])

                        f_margin_linex=LineString(fdata[1])

                        #match minimum distance value proposed line to front line

                        if round(f_prop_linex.distance(f_margin_linex),1)==min(front_data):

                            # get match line of proposed line

                            f_np_prop_linex=np.array(fdata[0]).round(2)

                            # split this line

                            prop_line_splitf=split(f_np_prop_linex[0],f_np_prop_linex[1],4)

                            # remove first amd last point

                            for prop_splitf_pts in prop_line_splitf[1:-1]:

                                np_prop_splitf_pts=np.array(prop_splitf_pts).round(2)

                                prop_splitf_point=Point(np_prop_splitf_pts)

                                fline_pts_value.append(round(prop_splitf_point.distance(f_margin_linex),1))

                                fline_pts.append(np_prop_splitf_pts)

                    # for front side

                    for fdata_x in front_coordinate_data:

                        f_prop_linex_x=LineString(fdata_x[0])

                        f_margin_linex_x=LineString(fdata_x[1])

                        if round(f_prop_linex_x.distance(f_margin_linex_x),1)==min(front_data):

                            np_prop_linex_x=np.array(fdata_x[0]).round(2)

                            max_prop_linex_x=np_prop_linex_x.max(axis=0).round(2)

                            min_prop_linex_x=np_prop_linex_x.min(axis=0).round(2)

                            for x_fline_pts in fline_pts:

                                np_x_fline_pts=np.array(x_fline_pts).round(2)

                                x_fline_point=Point(np_x_fline_pts)

                                #check point in this line or not

                                if ((max_prop_linex_x[0]>=np_x_fline_pts[0] and min_prop_linex_x[0]<=np_x_fline_pts[0]) and (max_prop_linex_x[1]>=np_x_fline_pts[1] and min_prop_linex_x[1]<=np_x_fline_pts[1])):

                                    # match minmum distance of point to front line

                                    if round(x_fline_point.distance(f_margin_linex_x),1)==min(fline_pts_value):

                                        # y value is  equal

                                        if np_prop_linex_x[0,1]==np_prop_linex_x[1,1]:

                                           # proposed work polygon convert into lines

                                            for x_f_prop_line in lwpolyline.virtual_entities():

                                                x_f_prop_start_pts=[x_f_prop_line.dxf.start[0],x_f_prop_line.dxf.start[1]]

                                                x_f_prop_end_pts=[x_f_prop_line.dxf.end[0],x_f_prop_line.dxf.end[1]]

                                                x_prop_line=[x_f_prop_start_pts,x_f_prop_end_pts]

                                                np_x_prop_line=np.array(x_prop_line).round(2)

                                                #check this direction of all proposed line

                                                if np_x_prop_line[0,1]==np_prop_linex_x[0,1] and np_x_prop_line[1,1]==np_prop_linex_x[1,1]:

                                                    x_prop_work_line=LineString(np_x_prop_line)

                                                    min_np_x_prop_line=np_x_prop_line.min(axis=0)

                                                    max_np_x_prop_line=np_x_prop_line.max(axis=0)

                                                    # tot_lot polygon

                                                    for organized_open_space_text in msp.query('MTEXT[layer=="_OrganizedOpenSpace"]'):

                                                        if organized_open_space_text.text=='Tot-lot':

                                                            organized_attrib=organized_open_space_text.dxfattribs()

                                                            tot_lot_pts=organized_attrib['insert']

                                                            tot_lot_ptsx=[tot_lot_pts[0],tot_lot_pts[1]]

                                                            np_tot_lot_pts=np.array(tot_lot_ptsx).round(2)

                                                            tot_lot_coords=Point(np_tot_lot_pts)

                                                            for organized_open_space_poly in msp.query('LWPOLYLINE[layer=="_OrganizedOpenSpace"]'):

                                                                organized_open_space_poly_pts=[y[0:2] for y in organized_open_space_poly.get_points()]

                                                                np_organized_open_space_poly_pts=np.array(organized_open_space_poly_pts).round(2)

                                                                organized_space_poly=Polygon(np_organized_open_space_poly_pts)

                                                                for f_tot_lot_line in organized_open_space_poly.virtual_entities():

                                                                    start_f_tot_lot_line_pts=[f_tot_lot_line.dxf.start[0],f_tot_lot_line.dxf.start[1]]

                                                                    end_f_tot_lot_line_pts=[f_tot_lot_line.dxf.end[0],f_tot_lot_line.dxf.end[1]]

                                                                    f_tot_lot_line_pts=[start_f_tot_lot_line_pts,end_f_tot_lot_line_pts]

                                                                    np_f_tot_lot_line_pts=np.array(f_tot_lot_line_pts).round(2)

                                                                    split_np_f_tot_lot_line_pts=split(np_f_tot_lot_line_pts[0],np_f_tot_lot_line_pts[1],4)

                                                                    #check tot-lot text in polygon or not

                                                                    if organized_space_poly.contains(tot_lot_coords)==True:

                                                                        # tot-lot polygon convert into points

                                                                        for f_tot_pts in split_np_f_tot_lot_line_pts:

                                                                            np_f_tot_pts=np.array(f_tot_pts).round(2)

                                                                            np_f_tot_point=Point(np_f_tot_pts)

                                                                            #check propposed polygon to totlot polygon distance not 0

                                                                            if round(prop_poly1.distance(organized_space_poly))!=0:

                                                                                #tot-lot point in proposed line or not

                                                                                if (min_np_x_prop_line[0]<=np_f_tot_pts[0] and  max_np_x_prop_line[0]>=np_f_tot_pts[0]) or (min_np_x_prop_line[1]<=np_f_tot_pts[1] and  max_np_x_prop_line[1]>=np_f_tot_pts[1]):

                                                                                    front_data.append(round(np_f_tot_point.distance(x_prop_work_line),2))

                                                                                    #check propposed polygon to totlot polygon distance is 0

                                                                                elif(round(prop_poly1.distance(organized_space_poly))==0):

                                                                                    front_data.append(round(organized_space_poly.distance(f_margin_linex_x),2))

                                                    #This loop for front line to prop_work block

                                                    for fprop_work_poly in msp.query('LWPOLYLINE[layer=="_ProposedWork"]'):

                                                        fprop_poly_pts=[a[0:2] for a in fprop_work_poly.get_points()]

                                                        np_fprop_poly_pts=np.array(fprop_poly_pts).round(2)

                                                        fprop_poly=Polygon(np_fprop_poly_pts)

                                                         # proposed work polygon convert into points

                                                        for f_prop_pts in np_fprop_poly_pts:

                                                            np_f_prop_pts=np.array(f_prop_pts).round(2)

                                                            np_f_prop_point=Point(np_f_prop_pts)

                                                            # check proposed polygon to another proposed polygon not 0

                                                            if round(prop_poly1.distance(fprop_poly))!=0:

                                                                #check proposed polygon point in proposed polygon line

                                                                if (min_np_x_prop_line[0]<=np_f_prop_pts[0] and  max_np_x_prop_line[0]>=np_f_prop_pts[0]) or (min_np_x_prop_line[1]<=np_f_prop_pts[1] and  max_np_x_prop_line[1]>=np_f_prop_pts[1]):

                                                                    front_data.append(round(np_f_prop_point.distance(x_prop_work_line),2))

                                                                else:

                                                                    for f_prop_line in fprop_work_poly.virtual_entities():

                                                                        f_start_prop_pts=[f_prop_line.dxf.start[0],f_prop_line.dxf.start[1]]

                                                                        f_end_prop_pts=[f_prop_line.dxf.end[0],f_prop_line.dxf.end[1]]

                                                                        f_prop_line=[f_start_prop_pts,f_end_prop_pts]

                                                                        np_f_prop_line=np.array(f_prop_line).round(2)

                                                                        f_prop_linea=LineString(np_f_prop_line)

                                                                        max_np_f_prop_line=np_f_prop_line.max(axis=0).round(2)

                                                                        min_np_f_prop_line=np_f_prop_line.min(axis=0).round(2)

                                                                        for f_prop_line_pts in np_prop_linex_x:

                                                                            np_f_prop_line_pts=np.array(f_prop_line_pts).round(2)

                                                                            f_prop_line_point=Point(np_f_prop_line_pts)

                                                                            if (min_np_f_prop_line[0]<=np_f_prop_line_pts[0] and  max_np_f_prop_line[0]>=np_f_prop_line_pts[0]) or (min_np_f_prop_line[1]<=np_f_prop_line_pts[1] and  max_np_f_prop_line[1]>=np_f_prop_line_pts[1]):

                                                                                front_data.append(round(f_prop_line_point.distance(f_prop_linea),2))







                                        #used for x axis value is equal

                                        elif(np_prop_linex_x[0,0]==np_prop_linex_x[1,0]):

                                            for x_f_prop_line in lwpolyline.virtual_entities():

                                                x_f_prop_start_pts=[x_f_prop_line.dxf.start[0],x_f_prop_line.dxf.start[1]]

                                                x_f_prop_end_pts=[x_f_prop_line.dxf.end[0],x_f_prop_line.dxf.end[1]]

                                                x_prop_line=[x_f_prop_start_pts,x_f_prop_end_pts]

                                                np_x_prop_line=np.array(x_prop_line).round(2)

                                                if np_x_prop_line[0,0]==np_prop_linex_x[0,0] and np_x_prop_line[1,0]==np_prop_linex_x[1,0]:

                                                    x_prop_work_line=LineString(np_x_prop_line)

                                                    min_np_x_prop_line=np_x_prop_line.min(axis=0)

                                                    max_np_x_prop_line=np_x_prop_line.max(axis=0)

                                                    # tot lot data

                                                    for organized_open_space_text in msp.query('MTEXT[layer=="_OrganizedOpenSpace"]'):

                                                        if organized_open_space_text.text=='Tot-lot':

                                                            organized_attrib=organized_open_space_text.dxfattribs()

                                                            tot_lot_pts=organized_attrib['insert']

                                                            tot_lot_ptsx1=[tot_lot_pts[0],tot_lot_pts[1]]

                                                            np_tot_lot_pts=np.array(tot_lot_ptsx1).round(2)

                                                            tot_lot_coords=Point(np_tot_lot_pts)

                                                            for organized_open_space_poly in msp.query('LWPOLYLINE[layer=="_OrganizedOpenSpace"]'):

                                                                organized_open_space_poly_pts=[y[0:2] for y in organized_open_space_poly.get_points()]

                                                                np_organized_open_space_poly_pts=np.array(organized_open_space_poly_pts).round(2)

                                                                organized_space_poly=Polygon(np_organized_open_space_poly_pts)

                                                                for f_tot_lot_line in organized_open_space_poly.virtual_entities():

                                                                    start_f_tot_lot_line_pts=[f_tot_lot_line.dxf.start[0],f_tot_lot_line.dxf.start[1]]

                                                                    end_f_tot_lot_line_pts=[f_tot_lot_line.dxf.end[0],f_tot_lot_line.dxf.end[1]]

                                                                    f_tot_lot_line_ptsx2=[start_f_tot_lot_line_pts,end_f_tot_lot_line_pts]

                                                                    np_f_tot_lot_line_pts=np.array(f_tot_lot_line_ptsx2).round(2)

                                                                    split_np_f_tot_lot_line_pts=split(np_f_tot_lot_line_pts[0],np_f_tot_lot_line_pts[1],4)

                                                                    if organized_space_poly.contains(tot_lot_coords)==True:

                                                                        for f_tot_pts in split_np_f_tot_lot_line_pts:

                                                                            np_f_tot_pts=np.array(f_tot_pts).round(2)

                                                                            np_f_tot_point=Point(np_f_tot_pts)

                                                                            if round(prop_poly1.distance(organized_space_poly))!=0:

                                                                                if (min_np_x_prop_line[0]<=np_f_tot_pts[0] and  max_np_x_prop_line[0]>=np_f_tot_pts[0]) or (min_np_x_prop_line[1]<=np_f_tot_pts[1] and  max_np_x_prop_line[1]>=np_f_tot_pts[1]):

                                                                                    front_data.append(round(np_f_tot_point.distance(x_prop_work_line),2))


                                                                            elif(round(prop_poly1.distance(organized_space_poly))==0):

                                                                                front_data.append(round(organized_space_poly.distance(f_margin_linex_x),2))


                                                    #This loop for front line to prop_work block
                                                    for fprop_work_poly in msp.query('LWPOLYLINE[layer=="_ProposedWork"]'):

                                                        fprop_poly_pts=[a[0:2] for a in fprop_work_poly.get_points()]

                                                        np_fprop_poly_pts=np.array(fprop_poly_pts).round(2)

                                                        fprop_poly=Polygon(np_fprop_poly_pts)

                                                        for f_prop_pts in np_fprop_poly_pts:

                                                            np_f_prop_pts=np.array(f_prop_pts).round(2)

                                                            np_f_prop_point=Point(np_f_prop_pts)

                                                            if round(prop_poly1.distance(fprop_poly))!=0:

                                                                if (min_np_x_prop_line[0]<=np_f_prop_pts[0] and  max_np_x_prop_line[0]>=np_f_prop_pts[0]) or (min_np_x_prop_line[1]<=np_f_prop_pts[1] and  max_np_x_prop_line[1]>=np_f_prop_pts[1]):

                                                                    front_data.append(round(np_f_prop_point.distance(x_prop_work_line),2))

                                                                else:

                                                                    for f_prop_line in fprop_work_poly.virtual_entities():

                                                                        f_start_prop_pts=[f_prop_line.dxf.start[0],f_prop_line.dxf.start[1]]

                                                                        f_end_prop_pts=[f_prop_line.dxf.end[0],f_prop_line.dxf.end[1]]

                                                                        f_prop_line=[f_start_prop_pts,f_end_prop_pts]

                                                                        np_f_prop_line=np.array(f_prop_line).round(2)

                                                                        f_prop_linea=LineString(np_f_prop_line)

                                                                        max_np_f_prop_line=np_f_prop_line.max(axis=0).round(2)

                                                                        min_np_f_prop_line=np_f_prop_line.min(axis=0).round(2)

                                                                        for f_prop_line_pts in np_prop_linex_x:

                                                                            np_f_prop_line_pts=np.array(f_prop_line_pts).round(2)

                                                                            f_prop_line_point=Point(np_f_prop_line_pts)

                                                                            if (min_np_f_prop_line[0]<=np_f_prop_line_pts[0] and  max_np_f_prop_line[0]>=np_f_prop_line_pts[0]) or (min_np_f_prop_line[1]<=np_f_prop_line_pts[1] and  max_np_f_prop_line[1]>=np_f_prop_line_pts[1]):

                                                                                front_data.append(round(f_prop_line_point.distance(f_prop_linea),2))
                                    # Does not equal x and y value
                                    else:

                                        for fprop_work_poly in msp.query('LWPOLYLINE[layer=="_ProposedWork"]'):

                                            fprop_poly_pts=[b[0:2] for b in fprop_work_poly.get_points()]

                                            np_fprop_poly_pts=np.array(fprop_poly_pts).round(2)

                                            fprop_poly=Polygon(np_fprop_poly_pts)

                                            for f_prop_pts in fprop_poly_pts:

                                                np_f_prop_pts=np.array(f_prop_pts).round(2)

                                                f_prop_point=Point(np_f_prop_pts)

                                                if round(prop_poly1.distance(fprop_poly))!=0:

                                                    if (max_prop_linex_x[0]>=np_f_prop_pts[0] and min_prop_linex_x[0]<=np_f_prop_pts[0]) or (max_prop_linex_x[1]>=np_f_prop_pts[1] and min_prop_linex_x[1]<=np_f_prop_pts[1]):

                                                        front_data.append(round(f_prop_point.distance(f_prop_linex_x),2))

                                                    else:

                                                        for f_lwpolygon in msp.query('LWPOLYLINE[layer=="_ProposedWork"]'):

                                                            f_lwpolygon_pts=[p[0:2] for p in f_lwpolygon.get_points()]

                                                            np_f_lwpolygon_pts=np.array(f_lwpolygon_pts).round(2)

                                                            f_lwpolygon_poly=Polygon(np_f_lwpolygon_pts)

                                                            for f_prop_line in f_lwpolygon.virtual_entities():

                                                                f_prop_start_pts=[f_prop_line.dxf.start[0],f_prop_line.dxf.start[1]]

                                                                f_prop_end_pts=[f_prop_line.dxf.end[0],f_prop_line.dxf.end[1]]

                                                                f_prop_line_pts=[f_prop_start_pts,f_prop_end_pts]

                                                                np_f_prop_line_point=np.array(f_prop_line_pts).round(2)

                                                                f_prop_line_point=LineString(np_f_prop_line_point)

                                                                max_np_f_prop_line_point=np_f_prop_line_point.max(axis=0)

                                                                min_np_f_prop_line_point=np_f_prop_line_point.min(axis=0)

                                                                if round(f_lwpolygon_poly.distance(prop_poly1),1)!=0:

                                                                    if (max_np_f_prop_line_point[0]>=np_x_fline_pts[0] and min_np_f_prop_line_point[0]<=np_x_fline_pts[0]) or (max_np_f_prop_line_point[1]>=np_x_fline_pts[1] and min_np_f_prop_line_point[1]<=np_x_fline_pts[1]):

                                                                        front_data.append(round(x_fline_point.distance(f_prop_line_point),2))

                                                                    else:

                                                                        for x_f_lwpolygon_pts in np_f_lwpolygon_pts:

                                                                            np_x_f_lwpolygon_pts=np.array(x_f_lwpolygon_pts).round(2)

                                                                            x_f_lwpolygon_pts=Point(x_f_lwpolygon_pts)

                                                                            if (max_prop_linex_x[0]>=np_x_f_lwpolygon_pts[0] and min_prop_linex_x[0]<=np_x_f_lwpolygon_pts[0]) or (max_prop_linex_x[1]>=np_x_f_lwpolygon_pts[1] and min_prop_linex_x[1]<=np_x_f_lwpolygon_pts[1]):

                                                                                front_data.append(round(x_f_lwpolygon_pts.distance(f_prop_linex_x),2))



                    rline_pts_value=[]

                    rline_pts=[]

                    for rdata in rear_coordinate_data:

                        r_prop_linex=LineString(rdata[0])

                        r_margin_linex=LineString(rdata[1])

                        if round(r_prop_linex.distance(r_margin_linex),1)==min(rear_data):

                            r_np_prop_linex=np.array(rdata[0]).round(2)

                            prop_line_splitr=split(r_np_prop_linex[0],r_np_prop_linex[1],4)

                            for prop_splitr_pts in prop_line_splitr[1:-1]:

                                np_prop_splitr_pts=np.array(prop_splitr_pts).round(2)

                                prop_splitr_point=Point(np_prop_splitr_pts)

                                rline_pts_value.append(round(prop_splitr_point.distance(r_margin_linex),1))

                                rline_pts.append(np_prop_splitr_pts)

                    for rdata_x in rear_coordinate_data:

                        r_prop_linex_y=LineString(rdata_x[0])

                        r_margin_linex_y=LineString(rdata_x[1])

                        if round(r_prop_linex_y.distance(r_margin_linex_y),1)==min(rear_data):

                            np_prop_linex_y=np.array(rdata_x[0]).round(2)

                            max_prop_linex_y=np_prop_linex_y.max(axis=0).round(2)

                            min_prop_linex_y=np_prop_linex_y.min(axis=0).round(2)

                            for y_rline_pts in rline_pts:

                                np_y_rline_pts=np.array(y_rline_pts).round(2)

                                y_rline_point=Point(np_y_rline_pts)

                                if ((max_prop_linex_y[0]>=np_y_rline_pts[0] and min_prop_linex_y[0]<=np_y_rline_pts[0]) and (max_prop_linex_y[1]>=np_y_rline_pts[1] and min_prop_linex_y[1]<=np_y_rline_pts[1])):

                                    # check match value

                                    if round(y_rline_point.distance(r_margin_linex_y),1)==min(rline_pts_value):

                                        # used for y axis equal
                                        if np_prop_linex_y[0,1]==np_prop_linex_y[1,1]:

                                            for y_r_prop_line in lwpolyline.virtual_entities():

                                                y_r_prop_start_pts=[y_r_prop_line.dxf.start[0],y_r_prop_line.dxf.start[1]]

                                                y_r_prop_end_pts=[y_r_prop_line.dxf.end[0],y_r_prop_line.dxf.end[1]]

                                                y_prop_line=[y_r_prop_start_pts,y_r_prop_end_pts]

                                                np_y_prop_line=np.array(y_prop_line).round(2)

                                                if np_y_prop_line[0,1]==np_prop_linex_y[0,1] and np_y_prop_line[1,1]==np_prop_linex_y[1,1]:

                                                    y_prop_work_line=LineString(np_y_prop_line)

                                                    min_np_y_prop_line=np_y_prop_line.min(axis=0)

                                                    max_np_y_prop_line=np_y_prop_line.max(axis=0)

                                                    for organized_open_space_text in msp.query('MTEXT[layer=="_OrganizedOpenSpace"]'):

                                                        if organized_open_space_text.text=='Tot-lot':

                                                            organized_attrib=organized_open_space_text.dxfattribs()

                                                            tot_lot_pts=organized_attrib['insert']

                                                            tot_lot_ptsx3=[tot_lot_pts[0],tot_lot_pts[1]]

                                                            np_tot_lot_pts=np.array(tot_lot_ptsx3).round(2)

                                                            tot_lot_coords=Point(np_tot_lot_pts)

                                                            for organized_open_space_poly in msp.query('LWPOLYLINE[layer=="_OrganizedOpenSpace"]'):

                                                                organized_open_space_poly_pts=[y[0:2] for y in organized_open_space_poly.get_points()]

                                                                np_organized_open_space_poly_pts=np.array(organized_open_space_poly_pts).round(2)

                                                                organized_space_poly=Polygon(np_organized_open_space_poly_pts)

                                                                for r_tot_lot_line in organized_open_space_poly.virtual_entities():

                                                                    start_r_tot_lot_line_pts=[r_tot_lot_line.dxf.start[0],r_tot_lot_line.dxf.start[1]]

                                                                    end_r_tot_lot_line_pts=[r_tot_lot_line.dxf.end[0],r_tot_lot_line.dxf.end[1]]

                                                                    r_tot_lot_line_ptsx4=[start_r_tot_lot_line_pts,end_r_tot_lot_line_pts]

                                                                    np_r_tot_lot_line_pts=np.array(r_tot_lot_line_ptsx4).round(2)

                                                                    split_np_r_tot_lot_line_pts=split(np_r_tot_lot_line_pts[0],np_r_tot_lot_line_pts[1],4)


                                                                    if organized_space_poly.contains(tot_lot_coords)==True:

                                                                        for r_tot_pts in split_np_r_tot_lot_line_pts:

                                                                            np_r_tot_pts=np.array(r_tot_pts).round(2)

                                                                            np_r_tot_point=Point(np_r_tot_pts)

                                                                            if round(prop_poly1.distance(organized_space_poly))!=0:

                                                                                if (min_np_y_prop_line[0]<=np_r_tot_pts[0] and  max_np_y_prop_line[0]>=np_r_tot_pts[0]) or (min_np_y_prop_line[1]<=np_r_tot_pts[1] and  max_np_y_prop_line[1]>=np_r_tot_pts[1]):

                                                                                    rear_data.append(round(np_r_tot_point.distance(y_prop_work_line),2))

                                                                                else:
                                                                                    #tot lot polygon convert lines

                                                                                    for r_tot_line in organized_open_space_poly.virtual_entities():

                                                                                        r_tot_start_pts=[r_tot_line.dxf.start[0],r_tot_line.dxf.start[1]]

                                                                                        r_tot_end_pts=[r_tot_line.dxf.end[0],r_tot_line.dxf.end[1]]

                                                                                        r_tot_line_pts=[r_tot_start_pts,r_tot_end_pts]

                                                                                        np_r_tot_line_pts=np.array(r_tot_line_pts).round(2)

                                                                                        max_np_r_tot_line_pts=np_r_tot_line_pts.max(axis=0)

                                                                                        min_np_r_tot_line_pts=np_r_tot_line_pts.min(axis=0)

                                                                                        r_tot_line_point=LineString(np_r_tot_line_pts)

                                                                                        # proposed work line convert into points

                                                                                        for r_prop_work_pts in np_y_prop_line:

                                                                                            np_r_prop_work_pts=np.array(r_prop_work_pts).round(2)

                                                                                            r_prop_work_point=Point(np_r_prop_work_pts)

                                                                                            #check condition tot_lot line incluide proposed work points or not

                                                                                            if (max_np_r_tot_line_pts[0]>=np_r_prop_work_pts[0] and min_np_r_tot_line_pts[0]<=np_r_prop_work_pts[0]) or (max_np_r_tot_line_pts[1]>=np_r_prop_work_pts[1] and min_np_r_tot_line_pts[1]<=np_r_prop_work_pts[1]):

                                                                                                rear_data.append(round(r_prop_work_point.distance(r_tot_line_point),2))

                                                                            elif(round(prop_poly1.distance(organized_space_poly))==0):

                                                                                rear_data.append(round(organized_space_poly.distance(r_margin_linex_y),2))


                                                    #This loop for rear line to prop_work block

                                                    for rprop_work_poly in msp.query('LWPOLYLINE[layer=="_ProposedWork"]'):

                                                        rprop_poly_pts=[b[0:2] for b in rprop_work_poly.get_points()]

                                                        np_rprop_poly_pts=np.array(rprop_poly_pts).round(2)

                                                        rprop_poly=Polygon(np_rprop_poly_pts)

                                                        for rprop_work_poly_line in rprop_work_poly.virtual_entities():

                                                            start_rprop_work_poly_line_pts=[rprop_work_poly_line.dxf.start[0],rprop_work_poly_line.dxf.start[1]]

                                                            end_rprop_work_poly_line_pts=[rprop_work_poly_line.dxf.end[0],rprop_work_poly_line.dxf.end[1]]

                                                            rprop_work_poly_line_ptsx5=[start_rprop_work_poly_line_pts,end_rprop_work_poly_line_pts]

                                                            np_rprop_work_poly_line=np.array(rprop_work_poly_line_ptsx5).round(2)

                                                            split_np_rprop_work_poly_line=split(np_rprop_work_poly_line[0],np_rprop_work_poly_line[1],4)

                                                            for r_prop_pts in split_np_rprop_work_poly_line:

                                                                np_r_prop_pts=np.array(r_prop_pts).round(2)

                                                                np_r_prop_point=Point(np_r_prop_pts)

                                                                if round(prop_poly1.distance(rprop_poly))!=0:

                                                                    if (min_np_y_prop_line[0]<=np_r_prop_pts[0] and  max_np_y_prop_line[0]>=np_r_prop_pts[0]) or (min_np_y_prop_line[1]<=np_r_prop_pts[1] and  max_np_y_prop_line[1]>=np_r_prop_pts[1]):

                                                                        rear_data.append(round(np_r_prop_point.distance(y_prop_work_line),2))

                                        #used for x axis equal data

                                        elif(np_prop_linex_y[0,0]==np_prop_linex_y[1,0]):

                                            for y_r_prop_line in lwpolyline.virtual_entities():

                                                y_r_prop_start_pts=[y_r_prop_line.dxf.start[0],y_r_prop_line.dxf.start[1]]

                                                y_r_prop_end_pts=[y_r_prop_line.dxf.end[0],y_r_prop_line.dxf.end[1]]

                                                y_prop_line=[y_r_prop_start_pts,y_r_prop_end_pts]

                                                np_y_prop_line=np.array(y_prop_line).round(2)

                                                if np_y_prop_line[0,0]==np_prop_linex_y[0,0] and np_y_prop_line[1,0]==np_prop_linex_y[1,0]:

                                                    y_prop_work_line=LineString(np_y_prop_line)

                                                    min_np_y_prop_line=np_y_prop_line.min(axis=0)

                                                    max_np_y_prop_line=np_y_prop_line.max(axis=0)

                                                    for organized_open_space_text in msp.query('MTEXT[layer=="_OrganizedOpenSpace"]'):

                                                        if organized_open_space_text.text=='Tot-lot':

                                                            organized_attrib=organized_open_space_text.dxfattribs()

                                                            tot_lot_pts=organized_attrib['insert']

                                                            tot_lot_ptsx6=[tot_lot_pts[0],tot_lot_pts[1]]

                                                            np_tot_lot_pts=np.array(tot_lot_ptsx6).round(2)

                                                            tot_lot_coords=Point(np_tot_lot_pts)

                                                            for organized_open_space_poly in msp.query('LWPOLYLINE[layer=="_OrganizedOpenSpace"]'):

                                                                organized_open_space_poly_pts=[y[0:2] for y in organized_open_space_poly.get_points()]

                                                                np_organized_open_space_poly_pts=np.array(organized_open_space_poly_pts).round(2)

                                                                organized_space_poly=Polygon(np_organized_open_space_poly_pts)

                                                                if organized_space_poly.contains(tot_lot_coords)==True:

                                                                    for r_tot_pts in np_organized_open_space_poly_pts:

                                                                        np_r_tot_pts=np.array(r_tot_pts).round(2)

                                                                        np_r_tot_point=Point(np_r_tot_pts)

                                                                        if round(prop_poly1.distance(organized_space_poly))!=0:

                                                                            if (min_np_y_prop_line[0]<=np_r_tot_pts[0] and  max_np_y_prop_line[0]>=np_r_tot_pts[0]) or (min_np_y_prop_line[1]<=np_r_tot_pts[1] and  max_np_y_prop_line[1]>=np_r_tot_pts[1]):

                                                                                rear_data.append(round(np_r_tot_point.distance(y_prop_work_line),2))

                                                                            else:

                                                                                #tot lot polygon convert lines

                                                                                for r_tot_line in organized_open_space_poly.virtual_entities():

                                                                                    r_tot_start_pts=[r_tot_line.dxf.start[0],r_tot_line.dxf.start[1]]

                                                                                    r_tot_end_pts=[r_tot_line.dxf.end[0],r_tot_line.dxf.end[1]]

                                                                                    r_tot_line_pts=[r_tot_start_pts,r_tot_end_pts]

                                                                                    np_r_tot_line_pts=np.array(r_tot_line_pts).round(2)

                                                                                    max_np_r_tot_line_pts=np_r_tot_line_pts.max(axis=0)

                                                                                    min_np_r_tot_line_pts=np_r_tot_line_pts.min(axis=0)

                                                                                    r_tot_line_point=LineString(np_r_tot_line_pts)

                                                                                    # proposed work line convert into points

                                                                                    for r_prop_work_pts in np_y_prop_line:

                                                                                        np_r_prop_work_pts=np.array(r_prop_work_pts).round(2)

                                                                                        r_prop_work_point=Point(np_r_prop_work_pts)

                                                                                        #check condition tot_lot line incluide proposed work points or not

                                                                                        if (max_np_r_tot_line_pts[0]>=np_r_prop_work_pts[0] and min_np_r_tot_line_pts[0]<=np_r_prop_work_pts[0]) or (max_np_r_tot_line_pts[1]>=np_r_prop_work_pts[1] and min_np_r_tot_line_pts[1]<=np_r_prop_work_pts[1]):

                                                                                            rear_data.append(round(r_prop_work_point.distance(r_tot_line_point),2))

                                                                        elif(round(prop_poly1.distance(organized_space_poly))==0):

                                                                            rear_data.append(round(organized_space_poly.distance(r_margin_linex_y),2))

                                                    #This loop for rear line to prop_work block
                                                    for rprop_work_poly in msp.query('LWPOLYLINE[layer=="_ProposedWork"]'):

                                                        rprop_poly_pts=[b[0:2] for b in rprop_work_poly.get_points()]

                                                        np_rprop_poly_pts=np.array(rprop_poly_pts).round(2)

                                                        rprop_poly=Polygon(np_rprop_poly_pts)

                                                        for r_prop_pts in np_rprop_poly_pts:

                                                            np_r_prop_pts=np.array(r_prop_pts).round(2)

                                                            np_r_prop_point=Point(np_r_prop_pts)

                                                            if round(prop_poly1.distance(rprop_poly))!=0:

                                                                if (min_np_y_prop_line[0]<=np_r_prop_pts[0] and  max_np_y_prop_line[0]>=np_r_prop_pts[0]) or (min_np_y_prop_line[1]<=np_r_prop_pts[1] and  max_np_y_prop_line[1]>=np_r_prop_pts[1]):

                                                                    rear_data.append(round(np_r_prop_point.distance(y_prop_work_line),2))

                                                                else:

                                                                    for r_prop_line in rprop_work_poly.virtual_entities():

                                                                        r_start_prop_pts=[r_prop_line.dxf.start[0],r_prop_line.dxf.start[1]]

                                                                        r_end_prop_pts=[r_prop_line.dxf.end[0],r_prop_line.dxf.end[1]]

                                                                        r_prop_line=[r_start_prop_pts,r_end_prop_pts]

                                                                        np_r_prop_line=np.array(r_prop_line).round(2)

                                                                        r_prop_linea=LineString(np_r_prop_line)

                                                                        max_np_r_prop_line=np_r_prop_line.max(axis=0).round(2)

                                                                        min_np_r_prop_line=np_r_prop_line.min(axis=0).round(2)

                                                                        for r_prop_line_pts in np_prop_linex_y:

                                                                            np_r_prop_line_pts=np.array(r_prop_line_pts).round(2)

                                                                            r_prop_line_point=Point(np_r_prop_line_pts)

                                                                            if (min_np_r_prop_line[0]<=np_r_prop_line_pts[0] and  max_np_r_prop_line[0]>=np_r_prop_line_pts[0]) or (min_np_r_prop_line[1]<=np_r_prop_line_pts[1] and  max_np_r_prop_line[1]>=np_r_prop_line_pts[1]):

                                                                                rear_data.append(round(r_prop_line_point.distance(r_prop_linea),2))
                                        # x and y does not equal

                                        else:

                                            for rprop_work_poly in msp.query('LWPOLYLINE[layer=="_ProposedWork"]'):

                                                rprop_poly_pts=[b[0:2] for b in rprop_work_poly.get_points()]

                                                np_rprop_poly_pts=np.array(rprop_poly_pts).round(2)

                                                rprop_poly=Polygon(np_rprop_poly_pts)

                                                for r_prop_pts in rprop_poly_pts:

                                                    np_r_prop_pts=np.array(r_prop_pts).round(2)

                                                    r_prop_point=Point(np_r_prop_pts)

                                                    if round(prop_poly1.distance(rprop_poly))!=0:

                                                        if (max_prop_linex_y[0]>=np_r_prop_pts[0] and min_prop_linex_y[0]<=np_r_prop_pts[0]) or (max_prop_linex_y[1]>=np_r_prop_pts[1] and min_prop_linex_y[1]<=np_r_prop_pts[1]):

                                                            rear_data.append(round(r_prop_point.distance(r_prop_linex_y),2))
                                    else:

                                        for r_lwpolygon in msp.query('LWPOLYLINE[layer=="_ProposedWork"]'):

                                            r_lwpolygon_pts=[p[0:2] for p in r_lwpolygon.get_points()]

                                            np_r_lwpolygon_pts=np.array(r_lwpolygon_pts).round(2)

                                            r_lwpolygon_poly=Polygon(np_r_lwpolygon_pts)

                                            for r_prop_line in r_lwpolygon.virtual_entities():

                                                r_prop_start_pts=[r_prop_line.dxf.start[0],r_prop_line.dxf.start[1]]

                                                r_prop_end_pts=[r_prop_line.dxf.end[0],r_prop_line.dxf.end[1]]

                                                r_prop_line_pts=[r_prop_start_pts,r_prop_end_pts]

                                                np_r_prop_line_point=np.array(r_prop_line_pts).round(2)

                                                r_prop_line_point=LineString(np_r_prop_line_point)

                                                max_np_r_prop_line_point=np_r_prop_line_point.max(axis=0)

                                                min_np_r_prop_line_point=np_r_prop_line_point.min(axis=0)

                                                if round(r_lwpolygon_poly.distance(prop_poly1),1)!=0:

                                                    if (max_np_r_prop_line_point[0]>=np_y_rline_pts[0] and min_np_r_prop_line_point[0]<=np_y_rline_pts[0]) or (max_np_r_prop_line_point[1]>=np_y_rline_pts[1] and min_np_r_prop_line_point[1]<=np_y_rline_pts[1]):

                                                        rear_data.append(round(y_rline_point.distance(r_prop_line_point),2))

                    s1line_pts_value=[]

                    s1line_pts=[]

                    for s1data in side1_coordinate_data:

                        s1_prop_linex=LineString(s1data[0])

                        s1_margin_linex=LineString(s1data[1])

                        if round(s1_prop_linex.distance(s1_margin_linex),1)==min(side1_data):

                            s1_np_prop_linex=np.array(s1data[0]).round(2)

                            prop_line_splits1=split(s1_np_prop_linex[0],s1_np_prop_linex[1],4)

                            for prop_splits1_pts in prop_line_splits1[1:-1]:

                                np_prop_splits1_pts=np.array(prop_splits1_pts).round(2)

                                prop_splits1_point=Point(np_prop_splits1_pts)

                                s1line_pts_value.append(round(prop_splits1_point.distance(s1_margin_linex),1))

                                s1line_pts.append(np_prop_splits1_pts)

                    for s1data_x in side1_coordinate_data:

                        s1_prop_linex_x1=LineString(s1data_x[0])

                        s1_margin_linex_x1=LineString(s1data_x[1])

                        # match minimum proposed line to side1 data

                        if round(s1_prop_linex_x1.distance(s1_margin_linex_x1),1)==min(side1_data):

                            np_prop_linex_x1=np.array(s1data_x[0]).round(2)

                            max_prop_linex_x1=np_prop_linex_x1.max(axis=0).round(2)

                            min_prop_linex_x1=np_prop_linex_x1.min(axis=0).round(2)


                            for x1_s1line_pts in s1line_pts:

                                np_x1_s1line_pts=np.array(x1_s1line_pts).round(2)

                                x1_s1line_point=Point(np_x1_s1line_pts)

                                #check point in proposed line or not

                                if ((max_prop_linex_x1[0]>=np_x1_s1line_pts[0] and min_prop_linex_x1[0]<=np_x1_s1line_pts[0]) and (max_prop_linex_x1[1]>=np_x1_s1line_pts[1] and min_prop_linex_x1[1]<=np_x1_s1line_pts[1])):

                                    #match minimum proposed  point to side 1 line distance

                                    if round(x1_s1line_point.distance(s1_margin_linex_x1),1)==min(s1line_pts_value):

                                        # y value is  equal

                                        if np_prop_linex_x1[0,1]==np_prop_linex_x1[1,1]:

                                            #proposed polygon convert into lines

                                            for x1_s1_prop_line in lwpolyline.virtual_entities():

                                                x1_s1_prop_start_pts=[x1_s1_prop_line.dxf.start[0],x1_s1_prop_line.dxf.start[1]]

                                                x1_s1_prop_end_pts=[x1_s1_prop_line.dxf.end[0],x1_s1_prop_line.dxf.end[1]]

                                                x1_prop_line=[x1_s1_prop_start_pts,x1_s1_prop_end_pts]

                                                np_x1_prop_line=np.array(x1_prop_line).round(2)

                                                # check y value same as line

                                                if np_x1_prop_line[0,1]==np_prop_linex_x1[0,1] and np_x1_prop_line[1,1]==np_prop_linex_x1[1,1]:

                                                    x1_prop_work_line=LineString(np_x1_prop_line)

                                                    min_np_x1_prop_line=np_x1_prop_line.min(axis=0)

                                                    max_np_x1_prop_line=np_x1_prop_line.max(axis=0)

                                                    # tot_lot data

                                                    for organized_open_space_text in msp.query('MTEXT[layer=="_OrganizedOpenSpace"]'):

                                                        if organized_open_space_text.text=='Tot-lot':

                                                            organized_attrib=organized_open_space_text.dxfattribs()

                                                            tot_lot_pts=organized_attrib['insert']

                                                            tot_lot_ptsx7=[tot_lot_pts[0],tot_lot_pts[1]]

                                                            np_tot_lot_pts=np.array(tot_lot_ptsx7).round(2)

                                                            tot_lot_coords=Point(np_tot_lot_pts)

                                                            for organized_open_space_poly in msp.query('LWPOLYLINE[layer=="_OrganizedOpenSpace"]'):

                                                                organized_open_space_poly_pts=[y[0:2] for y in organized_open_space_poly.get_points()]

                                                                np_organized_open_space_poly_pts=np.array(organized_open_space_poly_pts).round(2)

                                                                organized_space_poly=Polygon(np_organized_open_space_poly_pts)

                                                                # check text data in totlot polygon

                                                                if organized_space_poly.contains(tot_lot_coords)==True:

                                                                    # totlot polygon convert into points

                                                                    for s1_tot_pts in np_organized_open_space_poly_pts:

                                                                        np_s1_tot_pts=np.array(s1_tot_pts).round(2)

                                                                        np_s1_tot_point=Point(np_s1_tot_pts)

                                                                        # check proposed polygon to totlot polygon distance is not 0

                                                                        if round(prop_poly1.distance(organized_space_poly))!=0:

                                                                            #check totlot point in minimum proposed line or not

                                                                            if (min_np_x1_prop_line[0]<=np_s1_tot_pts[0] and  max_np_x1_prop_line[0]>=np_s1_tot_pts[0]) or (min_np_x1_prop_line[1]<=np_s1_tot_pts[1] and  max_np_x1_prop_line[1]>=np_s1_tot_pts[1]):

                                                                                side1_data.append(round(np_s1_tot_point.distance(x1_prop_work_line),2))

                                                                            else:

                                                                                #tot lot polygon convert lines

                                                                                for s1_tot_line in organized_open_space_poly.virtual_entities():

                                                                                    s1_tot_start_pts=[s1_tot_line.dxf.start[0],s1_tot_line.dxf.start[1]]

                                                                                    s1_tot_end_pts=[s1_tot_line.dxf.end[0],s1_tot_line.dxf.end[1]]

                                                                                    s1_tot_line_pts=[s1_tot_start_pts,s1_tot_end_pts]

                                                                                    np_s1_tot_line_pts=np.array(s1_tot_line_pts).round(2)

                                                                                    max_np_s1_tot_line_pts=np_s1_tot_line_pts.max(axis=0)

                                                                                    min_np_s1_tot_line_pts=np_s1_tot_line_pts.min(axis=0)

                                                                                    s1_tot_line_point=LineString(np_s1_tot_line_pts)

                                                                                    # proposed work line convert into points

                                                                                    for s1_prop_work_pts in np_x1_prop_line:

                                                                                        np_s1_prop_work_pts=np.array(s1_prop_work_pts).round(2)

                                                                                        s1_prop_work_point=Point(np_s1_prop_work_pts)

                                                                                        #check proposed work point in totlot line

                                                                                        if (max_np_s1_tot_line_pts[0]>=np_s1_prop_work_pts[0] and min_np_s1_tot_line_pts[0]<=np_s1_prop_work_pts[0]) or (max_np_s1_tot_line_pts[1]>=np_s1_prop_work_pts[1] and min_np_s1_tot_line_pts[1]<=np_s1_prop_work_pts[1]):

                                                                                            side1_data.append(round(s1_prop_work_point.distance(s1_tot_line_point),2))

                                                                        #check totlot polygon and proposed polygon diatnce is 0

                                                                        elif(round(prop_poly1.distance(organized_space_poly))==0):

                                                                            side1_data.append(round(organized_space_poly.distance(s1_margin_linex_x1),2))

                                                    #This loop for side1 line to prop_work block

                                                    for s1prop_work_poly in msp.query('LWPOLYLINE[layer=="_ProposedWork"]'):

                                                        s1prop_poly_pts=[c[0:2] for c in s1prop_work_poly.get_points()]

                                                        np_s1prop_poly_pts=np.array(s1prop_poly_pts).round(2)

                                                        s1prop_poly=Polygon(np_s1prop_poly_pts)

                                                        for s1_prop_pts in np_s1prop_poly_pts:

                                                            np_s1_prop_pts=np.array(s1_prop_pts).round(2)

                                                            np_s1_prop_point=Point(np_s1_prop_pts)

                                                            #proposed polygon to proposed polygon is not 0

                                                            if round(prop_poly1.distance(s1prop_poly))!=0:

                                                                #proposed polygon point in minimum propposed line

                                                                if (min_np_x1_prop_line[0]<=np_s1_prop_pts[0] and  max_np_x1_prop_line[0]>=np_s1_prop_pts[0]) or (min_np_x1_prop_line[1]<=np_s1_prop_pts[1] and  max_np_x1_prop_line[1]>=np_s1_prop_pts[1]):

                                                                    side1_data.append(round(np_s1_prop_point.distance(x1_prop_work_line),2))

                                                                else:
                                                                    #propposed work polygon convert into line

                                                                    for s1_prop_line in s1prop_work_poly.virtual_entities():

                                                                        s1_start_prop_pts=[s1_prop_line.dxf.start[0],s1_prop_line.dxf.start[1]]

                                                                        s1_end_prop_pts=[s1_prop_line.dxf.end[0],s1_prop_line.dxf.end[1]]

                                                                        s1_prop_line=[s1_start_prop_pts,s1_end_prop_pts]

                                                                        np_s1_prop_line=np.array(s1_prop_line).round(2)

                                                                        s1_prop_linea=LineString(np_s1_prop_line)

                                                                        max_np_s1_prop_line=np_s1_prop_line.max(axis=0).round(2)

                                                                        min_np_s1_prop_line=np_s1_prop_line.min(axis=0).round(2)

                                                                        # minimum proposed work line convert into points

                                                                        for s1_prop_line_pts in np_prop_linex_x1:

                                                                            np_s1_prop_line_pts=np.array(s1_prop_line_pts).round(2)

                                                                            s1_prop_line_point=Point(np_s1_prop_line_pts)

                                                                            # minimum proposed work line points in proposed work line

                                                                            if (min_np_s1_prop_line[0]<=np_s1_prop_line_pts[0] and  max_np_s1_prop_line[0]>=np_s1_prop_line_pts[0]) or (min_np_s1_prop_line[1]<=np_s1_prop_line_pts[1] and  max_np_s1_prop_line[1]>=np_s1_prop_line_pts[1]):

                                                                                side1_data.append(round(s1_prop_line_point.distance(s1_prop_linea),2))

                                        #used for x axis equal data

                                        elif(np_prop_linex_x1[0,0]==np_prop_linex_x1[1,0]):

                                            for x1_s1_prop_line in lwpolyline.virtual_entities():

                                                x1_s1_prop_start_pts=[x1_s1_prop_line.dxf.start[0],x1_s1_prop_line.dxf.start[1]]

                                                x1_s1_prop_end_pts=[x1_s1_prop_line.dxf.end[0],x1_s1_prop_line.dxf.end[1]]

                                                x1_prop_line=[x1_s1_prop_start_pts,x1_s1_prop_end_pts]

                                                np_x1_prop_line=np.array(x1_prop_line).round(2)

                                                if np_x1_prop_line[0,0]==np_prop_linex_x1[0,0] and np_x1_prop_line[1,0]==np_prop_linex_x1[1,0]:

                                                    x1_prop_work_line=LineString(np_x1_prop_line)

                                                    min_np_x1_prop_line=np_x1_prop_line.min(axis=0)

                                                    max_np_x1_prop_line=np_x1_prop_line.max(axis=0)

                                                    for organized_open_space_text in msp.query('MTEXT[layer=="_OrganizedOpenSpace"]'):

                                                        if organized_open_space_text.text=='Tot-lot':

                                                            organized_attrib=organized_open_space_text.dxfattribs()

                                                            tot_lot_pts=organized_attrib['insert']

                                                            tot_lot_ptsx8=[tot_lot_pts[0],tot_lot_pts[1]]

                                                            np_tot_lot_pts=np.array(tot_lot_ptsx8).round(2)

                                                            tot_lot_coords=Point(np_tot_lot_pts)

                                                            for organized_open_space_poly in msp.query('LWPOLYLINE[layer=="_OrganizedOpenSpace"]'):

                                                                organized_open_space_poly_pts=[y[0:2] for y in organized_open_space_poly.get_points()]

                                                                np_organized_open_space_poly_pts=np.array(organized_open_space_poly_pts).round(2)

                                                                organized_space_poly=Polygon(np_organized_open_space_poly_pts)

                                                                if organized_space_poly.contains(tot_lot_coords)==True:

                                                                    for s1_tot_pts in np_organized_open_space_poly_pts:

                                                                        np_s1_tot_pts=np.array(s1_tot_pts).round(2)

                                                                        np_s1_tot_point=Point(np_s1_tot_pts)

                                                                        if round(prop_poly1.distance(organized_space_poly))!=0:

                                                                            if (min_np_x1_prop_line[0]<=np_s1_tot_pts[0] and  max_np_x1_prop_line[0]>=np_s1_tot_pts[0]) or (min_np_x1_prop_line[1]<=np_s1_tot_pts[1] and  max_np_x1_prop_line[1]>=np_s1_tot_pts[1]):

                                                                                side1_data.append(round(np_s1_tot_point.distance(x1_prop_work_line),2))

                                                                            else:

                                                                                #tot lot polygon convert lines

                                                                                for s1_tot_line in organized_open_space_poly.virtual_entities():

                                                                                    s1_tot_start_pts=[s1_tot_line.dxf.start[0],s1_tot_line.dxf.start[1]]

                                                                                    s1_tot_end_pts=[s1_tot_line.dxf.end[0],s1_tot_line.dxf.end[1]]

                                                                                    s1_tot_line_pts=[s1_tot_start_pts,s1_tot_end_pts]

                                                                                    np_s1_tot_line_pts=np.array(s1_tot_line_pts).round(2)

                                                                                    max_np_s1_tot_line_pts=np_s1_tot_line_pts.max(axis=0)

                                                                                    min_np_s1_tot_line_pts=np_s1_tot_line_pts.min(axis=0)

                                                                                    s1_tot_line_point=LineString(np_s1_tot_line_pts)

                                                                                    # proposed work line convert into points

                                                                                    for s1_prop_work_pts in np_x1_prop_line:

                                                                                        np_s1_prop_work_pts=np.array(s1_prop_work_pts).round(2)

                                                                                        s1_prop_work_point=Point(np_s1_prop_work_pts)

                                                                                        #check condition tot_lot line incluide proposed work points or not

                                                                                        if (max_np_s1_tot_line_pts[0]>=np_s1_prop_work_pts[0] and min_np_s1_tot_line_pts[0]<=np_s1_prop_work_pts[0]) or (max_np_s1_tot_line_pts[1]>=np_s1_prop_work_pts[1] and min_np_s1_tot_line_pts[1]<=np_s1_prop_work_pts[1]):

                                                                                            side1_data.append(round(s1_prop_work_point.distance(s1_tot_line_point),2))

                                                                        elif(round(prop_poly1.distance(organized_space_poly))==0):

                                                                            side1_data.append(round(organized_space_poly.distance(s1_margin_linex_x1),2))

                                                    #This loop for side1 line to prop_work block

                                                    for s1prop_work_poly in msp.query('LWPOLYLINE[layer=="_ProposedWork"]'):

                                                        s1prop_poly_pts=[c[0:2] for c in s1prop_work_poly.get_points()]

                                                        np_s1prop_poly_pts=np.array(s1prop_poly_pts).round(2)

                                                        s1prop_poly=Polygon(np_s1prop_poly_pts)

                                                        for s1_prop_pts in np_s1prop_poly_pts:

                                                            np_s1_prop_pts=np.array(s1_prop_pts).round(2)

                                                            np_s1_prop_point=Point(np_s1_prop_pts)

                                                            if round(prop_poly1.distance(s1prop_poly))!=0:

                                                                if (min_np_x1_prop_line[0]<=np_s1_prop_pts[0] and  max_np_x1_prop_line[0]>=np_s1_prop_pts[0]) or (min_np_x1_prop_line[1]<=np_s1_prop_pts[1] and  max_np_x1_prop_line[1]>=np_s1_prop_pts[1]):

                                                                    side1_data.append(round(np_s1_prop_point.distance(x1_prop_work_line),2))

                                                                else:

                                                                    for s1_prop_line in s1prop_work_poly.virtual_entities():

                                                                        s1_start_prop_pts=[s1_prop_line.dxf.start[0],s1_prop_line.dxf.start[1]]

                                                                        s1_end_prop_pts=[s1_prop_line.dxf.end[0],s1_prop_line.dxf.end[1]]

                                                                        s1_prop_line=[s1_start_prop_pts,s1_end_prop_pts]

                                                                        np_s1_prop_line=np.array(s1_prop_line).round(2)

                                                                        s1_prop_linea=LineString(np_s1_prop_line)

                                                                        max_np_s1_prop_line=np_s1_prop_line.max(axis=0).round(2)

                                                                        min_np_s1_prop_line=np_s1_prop_line.min(axis=0).round(2)

                                                                        for s1_prop_line_pts in np_prop_linex_x1:

                                                                            np_s1_prop_line_pts=np.array(s1_prop_line_pts).round(2)

                                                                            s1_prop_line_point=Point(np_s1_prop_line_pts)

                                                                            if (min_np_s1_prop_line[0]<=np_s1_prop_line_pts[0] and  max_np_s1_prop_line[0]>=np_s1_prop_line_pts[0]) or (min_np_s1_prop_line[1]<=np_s1_prop_line_pts[1] and  max_np_s1_prop_line[1]>=np_s1_prop_line_pts[1]):

                                                                                side1_data.append(round(s1_prop_line_point.distance(s1_prop_linea),2))


                    s2line_pts_value=[]

                    s2line_pts=[]

                    for s2data in side2_coordinate_data:

                        s2_prop_linex=LineString(s2data[0])

                        s2_margin_linex=LineString(s2data[1])

                        if round(s2_prop_linex.distance(s2_margin_linex),1)==min(side2_data):

                            s2_np_prop_linex=np.array(s2data[0]).round(2)

                            prop_line_splits2=split(s2_np_prop_linex[0],s2_np_prop_linex[1],4)

                            for prop_splits2_pts in prop_line_splits2[1:-1]:

                                np_prop_splits2_pts=np.array(prop_splits2_pts).round(2)

                                prop_splits2_point=Point(np_prop_splits2_pts)

                                s2line_pts_value.append(round(prop_splits2_point.distance(s2_margin_linex),2))

                                s2line_pts.append(np_prop_splits2_pts)

                    for s2data_x in side2_coordinate_data:

                        s2_prop_linex_y1=LineString(s2data_x[0])

                        s2_margin_linex_y1=LineString(s2data_x[1])

                        if round(s2_prop_linex_y1.distance(s2_margin_linex_y1),1)==min(side2_data):

                            np_prop_linex_y1=np.array(s2data_x[0]).round(2)

                            max_prop_linex_y1=np_prop_linex_y1.max(axis=0).round(2)

                            min_prop_linex_y1=np_prop_linex_y1.min(axis=0).round(2)


                            for y1_s2line_pts in s2line_pts:

                                np_y1_s2line_pts=np.array(y1_s2line_pts).round(2)

                                y1_s2line_point=Point(np_y1_s2line_pts)

                                if ((max_prop_linex_y1[0]>=np_y1_s2line_pts[0] and min_prop_linex_y1[0]<=np_y1_s2line_pts[0]) and (max_prop_linex_y1[1]>=np_y1_s2line_pts[1] and min_prop_linex_y1[1]<=np_y1_s2line_pts[1]))==True:

                                    if round(y1_s2line_point.distance(s2_margin_linex_y1),2)==min(s2line_pts_value):

                                        # used for y axis equal
                                        if np_prop_linex_y1[0,1]==np_prop_linex_y1[1,1]:

                                            for y1_s2_prop_line in lwpolyline.virtual_entities():

                                                y1_s2_prop_start_pts=[y1_s2_prop_line.dxf.start[0],y1_s2_prop_line.dxf.start[1]]

                                                y1_s2_prop_end_pts=[y1_s2_prop_line.dxf.end[0],y1_s2_prop_line.dxf.end[1]]

                                                y1_prop_line=[y1_s2_prop_start_pts,y1_s2_prop_end_pts]

                                                np_y1_prop_line=np.array(y1_prop_line).round(2)

                                                if np_y1_prop_line[0,1]==np_prop_linex_y1[0,1] and np_y1_prop_line[1,1]==np_prop_linex_y1[1,1]:

                                                    y1_prop_work_line=LineString(np_y1_prop_line)

                                                    min_np_y1_prop_line=np_y1_prop_line.min(axis=0)

                                                    max_np_y1_prop_line=np_y1_prop_line.max(axis=0)

                                                    for organized_open_space_text in msp.query('MTEXT[layer=="_OrganizedOpenSpace"]'):

                                                        if organized_open_space_text.text=='Tot-lot':

                                                            organized_attrib=organized_open_space_text.dxfattribs()

                                                            tot_lot_pts=organized_attrib['insert']

                                                            tot_lot_ptsx9=[tot_lot_pts[0],tot_lot_pts[1]]

                                                            np_tot_lot_pts=np.array(tot_lot_ptsx9).round(2)

                                                            tot_lot_coords=Point(np_tot_lot_pts)

                                                            for organized_open_space_poly in msp.query('LWPOLYLINE[layer=="_OrganizedOpenSpace"]'):

                                                                organized_open_space_poly_pts=[y[0:2] for y in organized_open_space_poly.get_points()]

                                                                np_organized_open_space_poly_pts=np.array(organized_open_space_poly_pts).round(2)

                                                                organized_space_poly=Polygon(np_organized_open_space_poly_pts)

                                                                if organized_space_poly.contains(tot_lot_coords)==True:

                                                                    for s2_tot_pts in np_organized_open_space_poly_pts:

                                                                        np_s2_tot_pts=np.array(s2_tot_pts).round(2)

                                                                        np_s2_tot_point=Point(np_s2_tot_pts)

                                                                        if round(prop_poly1.distance(organized_space_poly))!=0:

                                                                            if (min_np_y1_prop_line[0]<=np_s2_tot_pts[0] and  max_np_y1_prop_line[0]>=np_s2_tot_pts[0]) or (min_np_y1_prop_line[1]<=np_s2_tot_pts[1] and  max_np_y1_prop_line[1]>=np_s2_tot_pts[1]):

                                                                                side2_data.append(round(np_s2_tot_point.distance(y1_prop_work_line),2))

                                                                            else:

                                                                                #tot lot polygon convert lines

                                                                                for s2_tot_line in organized_open_space_poly.virtual_entities():

                                                                                    s2_tot_start_pts=[s2_tot_line.dxf.start[0],s2_tot_line.dxf.start[1]]

                                                                                    s2_tot_end_pts=[s2_tot_line.dxf.end[0],s2_tot_line.dxf.end[1]]

                                                                                    s2_tot_line_pts=[s2_tot_start_pts,s2_tot_end_pts]

                                                                                    np_s2_tot_line_pts=np.array(s2_tot_line_pts).round(2)

                                                                                    max_np_s2_tot_line_pts=np_s2_tot_line_pts.max(axis=0)

                                                                                    min_np_s2_tot_line_pts=np_s2_tot_line_pts.min(axis=0)

                                                                                    s2_tot_line_point=LineString(np_s2_tot_line_pts)

                                                                                    # proposed work line convert into points

                                                                                    for s2_prop_work_pts in np_y1_prop_line:

                                                                                        np_s2_prop_work_pts=np.array(s2_prop_work_pts).round(2)

                                                                                        s2_prop_work_point=Point(np_s2_prop_work_pts)

                                                                                        #check condition tot_lot line incluide proposed work points or not

                                                                                        if (max_np_s2_tot_line_pts[0]>=np_s2_prop_work_pts[0] and min_np_s2_tot_line_pts[0]<=np_s2_prop_work_pts[0]) or (max_np_s2_tot_line_pts[1]>=np_s2_prop_work_pts[1] and min_np_s2_tot_line_pts[1]<=np_s2_prop_work_pts[1]):

                                                                                            side2_data.append(round(s2_prop_work_point.distance(s2_tot_line_point),2))

                                                                        elif(round(prop_poly1.distance(organized_space_poly))==0):

                                                                            side2_data.append(round(organized_space_poly.distance(s2_margin_linex_y1),2))

                                                    #This loop for side2 line to prop_work block
                                                    for s2prop_work_poly in msp.query('LWPOLYLINE[layer=="_ProposedWork"]'):

                                                        s2prop_poly_pts=[d[0:2] for d in s2prop_work_poly.get_points()]

                                                        np_s2prop_poly_pts=np.array(s2prop_poly_pts).round(2)

                                                        s2prop_poly=Polygon(np_s2prop_poly_pts)

                                                        for s2_prop_pts in np_s2prop_poly_pts:

                                                            np_s2_prop_pts=np.array(s2_prop_pts).round(2)

                                                            np_s2_prop_point=Point(np_s2_prop_pts)

                                                            if round(prop_poly1.distance(s2prop_poly))!=0:

                                                                if (min_np_y1_prop_line[0]<=np_s2_prop_pts[0] and  max_np_y1_prop_line[0]>=np_s2_prop_pts[0]) or (min_np_y1_prop_line[1]<=np_s2_prop_pts[1] and  max_np_y1_prop_line[1]>=np_s2_prop_pts[1]):

                                                                    side2_data.append(round(np_s2_prop_point.distance(y1_prop_work_line),2))

                                                                else:

                                                                    for s2_prop_line in s2prop_work_poly.virtual_entities():

                                                                        s2_start_prop_pts=[s2_prop_line.dxf.start[0],s2_prop_line.dxf.start[1]]

                                                                        s2_end_prop_pts=[s2_prop_line.dxf.end[0],s2_prop_line.dxf.end[1]]

                                                                        s2_prop_line=[s2_start_prop_pts,s2_end_prop_pts]

                                                                        np_s2_prop_line=np.array(s2_prop_line).round(2)

                                                                        s2_prop_linea=LineString(np_s2_prop_line)

                                                                        max_np_s2_prop_line=np_s2_prop_line.max(axis=0).round(2)

                                                                        min_np_s2_prop_line=np_s2_prop_line.min(axis=0).round(2)

                                                                        for s2_prop_line_pts in np_prop_linex_y1:

                                                                            np_s2_prop_line_pts=np.array(s2_prop_line_pts).round(2)

                                                                            s2_prop_line_point=Point(np_s2_prop_line_pts)

                                                                            if (min_np_s2_prop_line[0]<=np_s2_prop_line_pts[0] and  max_np_s2_prop_line[0]>=np_s2_prop_line_pts[0]) or (min_np_s2_prop_line[1]<=np_s2_prop_line_pts[1] and  max_np_s2_prop_line[1]>=np_s2_prop_line_pts[1]):

                                                                                side2_data.append(round(s2_prop_line_point.distance(s2_prop_linea),2))

                                        #used for x axis equal data

                                        elif(np_prop_linex_y1[0,0]==np_prop_linex_y1[1,0]):

                                            for y1_s2_prop_line in lwpolyline.virtual_entities():

                                                y1_s2_prop_start_pts=[y1_s2_prop_line.dxf.start[0],y1_s2_prop_line.dxf.start[1]]

                                                y1_s2_prop_end_pts=[y1_s2_prop_line.dxf.end[0],y1_s2_prop_line.dxf.end[1]]

                                                y1_prop_line=[y1_s2_prop_start_pts,y1_s2_prop_end_pts]

                                                np_y1_prop_line=np.array(y1_prop_line).round(2)

                                                if np_y1_prop_line[0,0]==np_prop_linex_y1[0,0] and np_y1_prop_line[1,0]==np_prop_linex_y1[1,0]:

                                                    y1_prop_work_line=LineString(np_y1_prop_line)

                                                    min_np_y1_prop_line=np_y1_prop_line.min(axis=0)

                                                    max_np_y1_prop_line=np_y1_prop_line.max(axis=0)

                                                    for organized_open_space_text in msp.query('MTEXT[layer=="_OrganizedOpenSpace"]'):

                                                        if organized_open_space_text.text=='Tot-lot':

                                                            organized_attrib=organized_open_space_text.dxfattribs()

                                                            tot_lot_pts=organized_attrib['insert']

                                                            tot_lot_ptsx10=[tot_lot_pts[0],tot_lot_pts[1]]

                                                            np_tot_lot_pts=np.array(tot_lot_ptsx10).round(2)

                                                            tot_lot_coords=Point(np_tot_lot_pts)

                                                            for organized_open_space_poly in msp.query('LWPOLYLINE[layer=="_OrganizedOpenSpace"]'):

                                                                organized_open_space_poly_pts=[y[0:2] for y in organized_open_space_poly.get_points()]

                                                                np_organized_open_space_poly_pts=np.array(organized_open_space_poly_pts).round(2)

                                                                organized_space_poly=Polygon(np_organized_open_space_poly_pts)

                                                                if organized_space_poly.contains(tot_lot_coords)==True:

                                                                    for s2_tot_pts in np_organized_open_space_poly_pts:

                                                                        np_s2_tot_pts=np.array(s2_tot_pts).round(2)

                                                                        np_s2_tot_point=Point(np_s2_tot_pts)

                                                                        if round(prop_poly1.distance(organized_space_poly))!=0:

                                                                            if (min_np_y1_prop_line[0]<=np_s2_tot_pts[0] and  max_np_y1_prop_line[0]>=np_s2_tot_pts[0]) or (min_np_y1_prop_line[1]<=np_s2_tot_pts[1] and  max_np_y1_prop_line[1]>=np_s2_tot_pts[1]):

                                                                                side2_data.append(round(np_s2_tot_point.distance(y1_prop_work_line),2))

                                                                            else:
                                                                                #tot lot polygon convert lines

                                                                                for s2_tot_line in organized_open_space_poly.virtual_entities():

                                                                                    s2_tot_start_pts=[s2_tot_line.dxf.start[0],s2_tot_line.dxf.start[1]]

                                                                                    s2_tot_end_pts=[s2_tot_line.dxf.end[0],s2_tot_line.dxf.end[1]]

                                                                                    s2_tot_line_pts=[s2_tot_start_pts,s2_tot_end_pts]

                                                                                    np_s2_tot_line_pts=np.array(s2_tot_line_pts).round(2)

                                                                                    max_np_s2_tot_line_pts=np_s2_tot_line_pts.max(axis=0)

                                                                                    min_np_s2_tot_line_pts=np_s2_tot_line_pts.min(axis=0)

                                                                                    s2_tot_line_point=LineString(np_s2_tot_line_pts)

                                                                                    # proposed work line convert into points

                                                                                    for s2_prop_work_pts in np_y1_prop_line:

                                                                                        np_s2_prop_work_pts=np.array(s2_prop_work_pts).round(2)

                                                                                        s2_prop_work_point=Point(np_s2_prop_work_pts)

                                                                                        #check condition tot_lot line incluide proposed work points or not

                                                                                        if (max_np_s2_tot_line_pts[0]>=np_s2_prop_work_pts[0] and min_np_s2_tot_line_pts[0]<=np_s2_prop_work_pts[0]) or (max_np_s2_tot_line_pts[1]>=np_s2_prop_work_pts[1] and min_np_s2_tot_line_pts[1]<=np_s2_prop_work_pts[1]):

                                                                                            side2_data.append(round(s2_prop_work_point.distance(s2_tot_line_point),2))

                                                                        elif(round(prop_poly1.distance(organized_space_poly))==0):

                                                                            side2_data.append(round(organized_space_poly.distance(s2_margin_linex_y1),2))

                                                    #This loop for side2 line to prop_work block
                                                    for s2prop_work_poly in msp.query('LWPOLYLINE[layer=="_ProposedWork"]'):

                                                        s2prop_poly_pts=[d[0:2] for d in s2prop_work_poly.get_points()]

                                                        np_s2prop_poly_pts=np.array(s2prop_poly_pts).round(2)

                                                        s2prop_poly=Polygon(np_s2prop_poly_pts)

                                                        for s2_prop_pts in np_s2prop_poly_pts:

                                                            np_s2_prop_pts=np.array(s2_prop_pts).round(2)

                                                            s2_prop_point=Point(np_s2_prop_pts)

                                                            if round(prop_poly1.distance(s2prop_poly))!=0:

                                                                if (min_np_y1_prop_line[0]<=np_s2_prop_pts[0] and  max_np_y1_prop_line[0]>=np_s2_prop_pts[0]) or (min_np_y1_prop_line[1]<=np_s2_prop_pts[1] and  max_np_y1_prop_line[1]>=np_s2_prop_pts[1]):

                                                                    side2_data.append(round(s2_prop_point.distance(y1_prop_work_line),2))

                                                                else:

                                                                    for s2_prop_line in s2prop_work_poly.virtual_entities():

                                                                        s2_start_prop_pts=[s2_prop_line.dxf.start[0],s2_prop_line.dxf.start[1]]

                                                                        s2_end_prop_pts=[s2_prop_line.dxf.end[0],s2_prop_line.dxf.end[1]]

                                                                        s2_prop_line=[s2_start_prop_pts,s2_end_prop_pts]

                                                                        np_s2_prop_line=np.array(s2_prop_line).round(2)

                                                                        s2_prop_linea=LineString(np_s2_prop_line)

                                                                        max_np_s2_prop_line=np_s2_prop_line.max(axis=0).round(2)

                                                                        min_np_s2_prop_line=np_s2_prop_line.min(axis=0).round(2)

                                                                        for s2_prop_line_pts in np_prop_linex_y1:

                                                                            np_s2_prop_line_pts=np.array(s2_prop_line_pts).round(2)

                                                                            s2_prop_line_point=Point(np_s2_prop_line_pts)

                                                                            if (min_np_s2_prop_line[0]<=np_s2_prop_line_pts[0] and  max_np_s2_prop_line[0]>=np_s2_prop_line_pts[0]) or (min_np_s2_prop_line[1]<=np_s2_prop_line_pts[1] and  max_np_s2_prop_line[1]>=np_s2_prop_line_pts[1]):

                                                                                side2_data.append(round(s2_prop_line_point.distance(s2_prop_linea),2))

                    #info_data=[]

                    tmpPropWorkDict=dict()

                    tmpPropWorkDict['NAME']=prop_text_name

                    if front_data is not None:

                        tmpPropWorkDict['FRONT']=min(front_data)

                        #info_data.append(f'Front,{min(front_data)}')

                    if rear_data is not None:

                        tmpPropWorkDict['REAR']=min(rear_data)

                        #info_data.append(f'Rear,{min(rear_data)}')

                    if side1_data is not None:

                        tmpPropWorkDict['SIDE1']=min(side1_data)

                        #info_data.append(f'Side1,{min(side1_data)}')

                    if side2_data is not None:

                        tmpPropWorkDict['SIDE2']=min(side2_data)

                        #info_data.append(f'Side2,{min(side2_data)}')

                    #main_data=f'{name.dxf.text},{info_data}'
                    #print ('refid ', refid)

                    returnValueDict[refid]=tmpPropWorkDict

                    #resultsList.append(main_data)

    except IndexError:

               print(f'Didn"t have name of value')

               return returnValueDict

    except IOError:

            print(f'Not a DXF file or a generic I/O error.')

            return returnValueDict

    except ezdxf.DXFStructureError:

             print(f'Invalid or corrupted DXF file.')

             return returnValueDict

    return returnValueDict



def check_podium_setbacks(msp):#folder:str,filename:str):

    returnValueDict=dict()

    resultsList=[]

    if (msp is None):#folder is None or filename is None):

        return returnValueDict

    #dxf_path=os.path.join(folder,filename)

    try:

        #read_dxf=ezdxf.readfile(dxf_path)

        print('processing podium setbacks')

        #msp=read_dxf.modelspace()


        for building_text in msp.query('TEXT[layer=="_BuildingName"]'):

            building_text_attribs=building_text.dxfattribs()

            insert_building_text_pts=building_text_attribs.get('insert')

            building_name=building_text_attribs.get('text')

            building_text_pts=[insert_building_text_pts[0],insert_building_text_pts[1]]

            np_building_text_pts=np.array(building_text_pts).round(1)

            abs_np_building_text_pts=abs(np_building_text_pts)

            building_text_point=Point(abs_np_building_text_pts)

            # for building polygon

            for building_polygon in msp.query('LWPOLYLINE[layer=="_BuildingName"]'):

                building_polygon_pts=[bp[0:2] for bp in building_polygon.get_points()]

                building_ref_id= building_polygon.dxf.handle

                np_building_polygon_pts=np.array(building_polygon_pts).round(1)

                abs_np_building_polygon_pts=abs(np_building_polygon_pts)

                building_polygon_points=Polygon(abs_np_building_polygon_pts)

                #check building name in building polygon

                if building_polygon_points.contains(building_text_point)==True or building_polygon_points.touches(building_text_point)==True :

                    #print(building_name)

                    building_dict=dict()
                    building_list=[]

                    filter_building_name=" ".join(x for x in building_name if x.isalpha())

                    #print(filter_building_name)

                    #floor text data

                    for floor_text in msp.query('TEXT[layer=="_Floor"]'):

                        floor_text_attribs=floor_text.dxfattribs()

                        insert_floor_text_pts=floor_text_attribs.get('insert')

                        floor_name=floor_text_attribs.get('text')

                        floor_text_pts=[insert_floor_text_pts[0],insert_floor_text_pts[1]]

                        np_floor_text_pts=np.array(floor_text_pts).round(1)

                        abs_np_floor_text_pts=abs(np_floor_text_pts)

                        floor_text_point=Point(abs_np_floor_text_pts)

                        #floor polygon data

                        for floor_polygon in msp.query('LWPOLYLINE[layer=="_Floor"]'):

                            floor_polygon_pts=[fp[0:2] for fp in floor_polygon.get_points()]

                            ref_id = floor_polygon.dxf.handle

                            np_floor_polygon_pts=np.array(floor_polygon_pts).round(1)

                            abs_np_floor_polygon_pts=abs(np_floor_polygon_pts)

                            floor_polygon_points=Polygon(abs_np_floor_polygon_pts)

                            #check cellar floor text point in polygon

                            if floor_polygon_points.contains(floor_text_point)==True or  floor_polygon_points.touches(floor_text_point)==True:

                                #check floor polygon in building polygon

                                if building_polygon_points.contains(floor_polygon_points)==True:

                                    #print(floor_name)

                                    #use for podium polygon data

                                    for podium_polygon in msp.query('LWPOLYLINE[layer=="_Podium"]'):

                                        podium_polygon_pts=[pp[0:2] for pp in podium_polygon.get_points()]

                                        np_podium_polygon_pts=np.array(podium_polygon_pts).round(1)

                                        abs_np_podium_polygon_pts=abs(np_podium_polygon_pts)

                                        podium_polygon_points=Polygon(abs_np_podium_polygon_pts)

                                        #check podium polygon in floor polygon

                                        if floor_polygon_points.contains(podium_polygon_points)==True:

                                             #print(podium_polygon_points)

                                             #ResiBUAOutline center point use for podium polygon

                                             for podium_resibuaoutline_insert in msp.query('INSERT[layer=="_ResiBUAOutline"]'):

                                                 for podium_resibuaoutline_entity in podium_resibuaoutline_insert.virtual_entities():

                                                     if podium_resibuaoutline_entity.dxftype()=='CIRCLE':

                                                         podium_ressi_circle_center_pts=podium_resibuaoutline_entity.dxf.center

                                                         podium_ressi_np_circle_center_pts=np.array([podium_ressi_circle_center_pts[0],podium_ressi_circle_center_pts[1]]).round(1)

                                                         podium_ressi_abs_np_circle_center_pts=abs(podium_ressi_np_circle_center_pts)

                                                         podium_ressi_circle_center_point=Point(podium_ressi_abs_np_circle_center_pts)

                                                         #check ResiBUAOutline center points in podium polygon

                                                         if podium_polygon_points.contains(podium_ressi_circle_center_point)==True:

                                                              #print(True)

                                                              # for proposed work text data

                                                              for prop_work_text in msp.query('TEXT[layer=="_ProposedWork"]'):

                                                                  prop_work_text_attribs=prop_work_text.dxfattribs()

                                                                  insert_prop_work_text_pts=prop_work_text_attribs.get('insert')

                                                                  prop_work_name=prop_work_text_attribs.get('text')

                                                                  prop_work_text_pts=[insert_prop_work_text_pts[0],insert_prop_work_text_pts[1]]

                                                                  np_prop_work_text_pts=np.array(prop_work_text_pts).round(1)

                                                                  abs_np_prop_work_text_pts=abs(np_prop_work_text_pts)

                                                                  prop_work_text_point=Point(abs_np_prop_work_text_pts)

                                                                  for prop_work_polygon in msp.query('LWPOLYLINE[layer=="_ProposedWork"]'):

                                                                      prop_work_polygon_pts=[pwp[0:2] for pwp in prop_work_polygon.get_points()]

                                                                      np_prop_work_polygon_pts=np.array(prop_work_polygon_pts).round(1)

                                                                      abs_np_prop_work_polygon_pts=abs(np_prop_work_polygon_pts)

                                                                      prop_work_polygon_points=Polygon(abs_np_prop_work_polygon_pts)

                                                                      #check proposed work text name in proposed work polygon

                                                                      if prop_work_polygon_points.contains(prop_work_text_point)==True or prop_work_polygon_points.touches(prop_work_text_point)==True:

                                                                            #print(prop_work_name)

                                                                            for prop_work_resibuaoutline_insert in msp.query('INSERT[layer=="_ResiBUAOutline"]'):

                                                                                for prop_work_resibuaoutline_entity in prop_work_resibuaoutline_insert.virtual_entities():

                                                                                    if prop_work_resibuaoutline_entity.dxftype()=='CIRCLE':

                                                                                        prop_work_ressi_circle_center_pts=prop_work_resibuaoutline_entity.dxf.center

                                                                                        prop_work_ressi_np_circle_center_pts=np.array([prop_work_ressi_circle_center_pts[0],prop_work_ressi_circle_center_pts[1]]).round(1)

                                                                                        prop_work_ressi_abs_np_circle_center_pts=abs(prop_work_ressi_np_circle_center_pts)

                                                                                        prop_work_ressi_circle_center_point=Point(prop_work_ressi_abs_np_circle_center_pts)

                                                                                        #check resibua center points in proposed work

                                                                                        if prop_work_polygon_points.contains(prop_work_ressi_circle_center_point)==True or prop_work_polygon_points.touches(prop_work_ressi_circle_center_point)==True:

                                                                                             filter_prop_work_name=" ".join(y for y in prop_work_name if y.isalpha())

                                                                                             #print(filter_prop_work_name)

                                                                                             #print(True)

                                                                                             # match the proposed work name and building name

                                                                                             if filter_building_name==filter_prop_work_name:

                                                                                                 #print(True)

                                                                                                 #combine proposed work center points and podium center points

                                                                                                 both_center_pts=[podium_ressi_abs_np_circle_center_pts,prop_work_ressi_abs_np_circle_center_pts]

                                                                                                 np_both_center_pts=np.array(both_center_pts).round(1)

                                                                                                 abs_np_both_center_pts=abs( np_both_center_pts)

                                                                                                 #print(abs_np_both_center_pts)

                                                                                                 max_abs_np_both_center_pts=abs_np_both_center_pts.max(axis=0)

                                                                                                 min_abs_np_both_center_pts=abs_np_both_center_pts.min(axis=0)

                                                                                                 distance_both_pts= max_abs_np_both_center_pts-min_abs_np_both_center_pts

                                                                                                 np_distance_both_pts=np.array(distance_both_pts).round(1)

                                                                                                 abs_np_distance_both_pts=abs(np_distance_both_pts)

                                                                                                 #print(f'Distance={abs_np_distance_both_pts}')

                                                                                                 #print(podium_ressi_abs_np_circle_center_pts+abs_np_distance_both_pts)

                                                                                                 podium_list_pts1=[]

                                                                                                 podium_list_pts2=[]

                                                                                                 podium_list_pts3=[]

                                                                                                 podium_list_pts4=[]

                                                                                                 for podium_pts in abs_np_podium_polygon_pts:

                                                                                                        podium_pts1_x=podium_pts[0]+abs_np_distance_both_pts[0]

                                                                                                        podium_pts1_y=podium_pts[1]+abs_np_distance_both_pts[1]

                                                                                                        podium_pts1=[podium_pts1_x,podium_pts1_y]

                                                                                                        podium_pts2_x=podium_pts[0]-abs_np_distance_both_pts[0]

                                                                                                        podium_pts2_y=podium_pts[1]-abs_np_distance_both_pts[1]

                                                                                                        podium_pts2=[podium_pts2_x,podium_pts2_y]

                                                                                                        podium_pts3_x=podium_pts[0]+abs_np_distance_both_pts[0]

                                                                                                        podium_pts3_y=podium_pts[1]-abs_np_distance_both_pts[1]

                                                                                                        podium_pts3=[podium_pts3_x,podium_pts3_y]

                                                                                                        podium_pts4_x=podium_pts[0]-abs_np_distance_both_pts[0]

                                                                                                        podium_pts4_y=podium_pts[1]+abs_np_distance_both_pts[1]

                                                                                                        podium_pts4=[podium_pts4_x,podium_pts4_y]

                                                                                                        podium_list_pts1.append(podium_pts1)

                                                                                                        podium_list_pts2.append(podium_pts2)

                                                                                                        podium_list_pts3.append(podium_pts3)

                                                                                                        podium_list_pts4.append(podium_pts4)

                                                                                                 #------first quadranrt data------------------

                                                                                                 np_podium_list_pts1=np.array(podium_list_pts1).round(1)

                                                                                                 abs_np_podium_list_pts1=abs(np_podium_list_pts1)

                                                                                                 #-----------second quadrant data---------------

                                                                                                 np_podium_list_pts2=np.array(podium_list_pts2).round(1)

                                                                                                 abs_np_podium_list_pts2=abs(np_podium_list_pts2)

                                                                                                 #--------------Third quadrant data-------------

                                                                                                 np_podium_list_pts3=np.array(podium_list_pts3).round(1)

                                                                                                 abs_np_podium_list_pts3=abs(np_podium_list_pts3)

                                                                                                 #----------------Fourth quadrant data------------

                                                                                                 np_podium_list_pts4=np.array(podium_list_pts4).round(1)

                                                                                                 abs_np_podium_list_pts4=abs(np_podium_list_pts4)

                                                                                                 #-----------first quadrant center points data---------------

                                                                                                 podium_center_pts1_x=podium_ressi_abs_np_circle_center_pts[0]+abs_np_distance_both_pts[0]

                                                                                                 podium_center_pts1_y=podium_ressi_abs_np_circle_center_pts[1]+abs_np_distance_both_pts[1]

                                                                                                 podium_center_pts1=[podium_center_pts1_x,podium_center_pts1_y]

                                                                                                 np_podium_center_pts1=np.array(podium_center_pts1).round(1)

                                                                                                 abs_np_podium_center_pts1=abs(np_podium_center_pts1)

                                                                                                 #-----------Second quadrant center points data---------------

                                                                                                 podium_center_pts2_x=podium_ressi_abs_np_circle_center_pts[0]-abs_np_distance_both_pts[0]

                                                                                                 podium_center_pts2_y=podium_ressi_abs_np_circle_center_pts[1]-abs_np_distance_both_pts[1]

                                                                                                 podium_center_pts2=[podium_center_pts2_x,podium_center_pts2_y]

                                                                                                 np_podium_center_pts2=np.array(podium_center_pts2).round(1)

                                                                                                 abs_np_podium_center_pts2=abs(np_podium_center_pts2)

                                                                                                 #-----------Third quadrant center points data---------------

                                                                                                 podium_center_pts3_x=podium_ressi_abs_np_circle_center_pts[0]+abs_np_distance_both_pts[0]

                                                                                                 podium_center_pts3_y=podium_ressi_abs_np_circle_center_pts[1]-abs_np_distance_both_pts[1]

                                                                                                 podium_center_pts3=[podium_center_pts3_x,podium_center_pts3_y]

                                                                                                 np_podium_center_pts3=np.array(podium_center_pts3).round(1)

                                                                                                 abs_np_podium_center_pts3=abs(np_podium_center_pts3)

                                                                                                 #-----------Third quadrant center points data---------------

                                                                                                 podium_center_pts4_x=podium_ressi_abs_np_circle_center_pts[0]-abs_np_distance_both_pts[0]

                                                                                                 podium_center_pts4_y=podium_ressi_abs_np_circle_center_pts[1]+abs_np_distance_both_pts[1]

                                                                                                 podium_center_pts4=[podium_center_pts4_x,podium_center_pts4_y]

                                                                                                 np_podium_center_pts4=np.array(podium_center_pts4).round(1)

                                                                                                 abs_np_podium_center_pts4=abs(np_podium_center_pts4)

                                                                                                 list_podium_center_pts=[abs_np_podium_center_pts1,abs_np_podium_center_pts2,abs_np_podium_center_pts3,abs_np_podium_center_pts4]

                                                                                                 podium_list_pts=[abs_np_podium_list_pts1,abs_np_podium_list_pts2,abs_np_podium_list_pts3,abs_np_podium_list_pts4]

                                                                                                 # list of center points convert in to pts

                                                                                                 for p_center in list_podium_center_pts:

                                                                                                     if prop_work_ressi_abs_np_circle_center_pts[0]==p_center[0] and  prop_work_ressi_abs_np_circle_center_pts[1]==p_center[1]:

                                                                                                        p_center_point=Point(p_center)

                                                                                                        # list of polygon convert into polygon

                                                                                                        for p_polygon in podium_list_pts:

                                                                                                            p_polygon_points=Polygon(p_polygon)

                                                                                                            if p_polygon_points.contains(p_center_point)==True or p_polygon_points.touches(p_center_point)==True:

                                                                                                                #for margine line

                                                                                                                for margin_insert in msp.query('INSERT[layer=="_MarginLine"]'):

                                                                                                                     front_side=[]

                                                                                                                     rear_side=[]

                                                                                                                     side1=[]

                                                                                                                     side2=[]

                                                                                                                     for margin_entity in margin_insert.virtual_entities():

                                                                                                                         if margin_entity.dxftype()=='LINE':

                                                                                                                             if margin_entity.dxf.color==1:

                                                                                                                                 f_margin_line_start_pts=[margin_entity.dxf.start[0],margin_entity.dxf.start[1]]

                                                                                                                                 f_margin_line_end_pts=[margin_entity.dxf.end[0],margin_entity.dxf.end[1]]

                                                                                                                                 f_margin_line_pts=[f_margin_line_start_pts,f_margin_line_end_pts]

                                                                                                                                 f_np_margin_line_pts=np.array(f_margin_line_pts).round(1)

                                                                                                                                 f_abs_np_margin_line_pts=abs(f_np_margin_line_pts)

                                                                                                                                 f_margin_line_points=LineString(f_abs_np_margin_line_pts)

                                                                                                                                 front_side.append(round(f_margin_line_points.distance(p_polygon_points),1))

                                                                                                                             elif(margin_entity.dxf.color==6):

                                                                                                                                r_margin_line_start_pts=[margin_entity.dxf.start[0],margin_entity.dxf.start[1]]

                                                                                                                                r_margin_line_end_pts=[margin_entity.dxf.end[0],margin_entity.dxf.end[1]]

                                                                                                                                r_margin_line_pts=[r_margin_line_start_pts,r_margin_line_end_pts]

                                                                                                                                r_np_margin_line_pts=np.array(r_margin_line_pts).round(1)

                                                                                                                                r_abs_np_margin_line_pts=abs(r_np_margin_line_pts)

                                                                                                                                r_margin_line_points=LineString(r_abs_np_margin_line_pts)

                                                                                                                                rear_side.append(round(r_margin_line_points.distance(p_polygon_points),1))

                                                                                                                             elif(margin_entity.dxf.color==5):

                                                                                                                                s1_margin_line_start_pts=[margin_entity.dxf.start[0],margin_entity.dxf.start[1]]

                                                                                                                                s1_margin_line_end_pts=[margin_entity.dxf.end[0],margin_entity.dxf.end[1]]

                                                                                                                                s1_margin_line_pts=[s1_margin_line_start_pts,s1_margin_line_end_pts]

                                                                                                                                s1_np_margin_line_pts=np.array(s1_margin_line_pts).round(1)

                                                                                                                                s1_abs_np_margin_line_pts=abs(s1_np_margin_line_pts)

                                                                                                                                s1_margin_line_points=LineString(s1_abs_np_margin_line_pts)

                                                                                                                                side1.append(round(s1_margin_line_points.distance(p_polygon_points),1))

                                                                                                                             elif(margin_entity.dxf.color==104):

                                                                                                                                s2_margin_line_start_pts=[margin_entity.dxf.start[0],margin_entity.dxf.start[1]]

                                                                                                                                s2_margin_line_end_pts=[margin_entity.dxf.end[0],margin_entity.dxf.end[1]]

                                                                                                                                s2_margin_line_pts=[s2_margin_line_start_pts,s2_margin_line_end_pts]

                                                                                                                                s2_np_margin_line_pts=np.array(s2_margin_line_pts).round(1)

                                                                                                                                s2_abs_np_margin_line_pts=abs(s2_np_margin_line_pts)

                                                                                                                                s2_margin_line_points=LineString(s2_abs_np_margin_line_pts)

                                                                                                                                side2.append(round(s2_margin_line_points.distance(p_polygon_points),1))

                                                                                                                     tmpworkdict=dict()

                                                                                                                     tmpworkdict['NAME']=floor_name
                                                                                                                     tmpworkdict['HANDLE']=ref_id

                                                                                                                     if front_side!=[]:

                                                                                                                        tmpworkdict['FRONT']=min(front_side)

                                                                                                                     if rear_side!=[]:

                                                                                                                        tmpworkdict['REAR']=min(rear_side)

                                                                                                                     if side1!=[]:

                                                                                                                        tmpworkdict['SIDE1']=min(side1)

                                                                                                                     if side2!=[]:

                                                                                                                        tmpworkdict['SIDE2']=min(side2)

                                                                                                                     building_dict[ref_id]=tmpworkdict
                                                                                                                     building_list.append(tmpworkdict)

                    tmpbuilding_dict=dict()

                    if building_list!=[]:#building_dict!={}:

                        tmpbuilding_dict[building_name]=building_list#building_dict

                    if tmpbuilding_dict!={}:

                        returnValueDict[building_ref_id]=tmpbuilding_dict






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



def check_redius_of_Arc(msp):#folder:str,filename:str):

    returnValueDict=dict()

    resultsList=[]

    if (msp is None):#folder is None or filename is None):

        return returnValueDict

    #dxf_path=os.path.join(folder,filename)

    try:

        #read_dxf=ezdxf.readfile(dxf_path)

        print('Processing Podium Building  Arc radius ')

        #msp=read_dxf.modelspace()

        for building_text in msp.query('TEXT[layer=="_BuildingName"]'):

            building_text_attribs=building_text.dxfattribs()

            building_text_insert=building_text_attribs.get('insert')

            building_name=building_text_attribs.get('text')

            building_text_pts=[building_text_insert[0],building_text_insert[1]]

            np_building_text_pts=np.array(building_text_pts).round(1)

            building_text_point=Point(np_building_text_pts)

            for building_polygon in msp.query('LWPOLYLINE[layer=="_BuildingName"]'):

                building_polygon_pts=[bp[0:2] for bp in building_polygon.get_points()]

                building_ref_id=building_polygon.dxf.handle

                np_building_polygon_pts=np.array(building_polygon_pts).round(1)

                building_polygon_points=Polygon(np_building_polygon_pts)

                if building_polygon_points.contains(building_text_point)==True or building_polygon_points.touches(building_text_point)==True:

                    #print(building_name)

                    BuildingWorkDict=dict()

                    for floor_text in msp.query('TEXT[layer=="_Floor"]'):

                        floor_text_attribs=floor_text.dxfattribs()

                        floor_text_insert=floor_text_attribs.get('insert')

                        floor_name=floor_text_attribs.get('text')

                        floor_text_pts=[floor_text_insert[0],floor_text_insert[1]]

                        np_floor_text_pts=np.array(floor_text_pts).round(1)

                        floor_text_point=Point(np_floor_text_pts)

                        for floor_polygon in msp.query('LWPOLYLINE[layer=="_Floor"]'):

                            floor_polygon_pts=[fp[0:2] for fp in floor_polygon.get_points()]

                            floor_ref_id= floor_polygon.dxf.handle

                            np_floor_polygon_pts=np.array(floor_polygon_pts).round(1)

                            floor_polygon_points=Polygon(np_floor_polygon_pts)

                            if floor_polygon_points.contains(floor_text_point)==True or floor_polygon_points.touches(floor_text_point)==True:

                                if building_polygon_points.contains(floor_polygon_points)==True:

                                    #print(floor_name)

                                    floor_radius_list=[]

                                    for podium_polygon in msp.query('LWPOLYLINE[layer=="_Podium"]'):

                                        podium_polygon_pts=[pp[0:2] for pp in podium_polygon.get_points()]

                                        np_podium_polygon_pts=np.array(podium_polygon_pts).round(1)

                                        podium_polygon_points=Polygon(np_podium_polygon_pts)

                                        if floor_polygon_points.contains(podium_polygon_points)==True:

                                            for polygon_entity in  podium_polygon.virtual_entities():

                                                if polygon_entity.dxftype()=='ARC':

                                                    floor_radius_list.append(round(polygon_entity.dxf.radius,1))

                                    tmpFloorWorkDict=dict()

                                    if floor_radius_list!=[]:

                                        tmpFloorWorkDict[floor_name]=floor_radius_list

                                        BuildingWorkDict[floor_ref_id]=tmpFloorWorkDict

                    tmpBuildingWorkDict=dict()

                    if BuildingWorkDict!={}:

                        tmpBuildingWorkDict[building_name]=BuildingWorkDict

                        returnValueDict[building_ref_id]=tmpBuildingWorkDict

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



#path of the filename

# folder=r'E:\python'
# folder=r'C:\\Users\\esiva\\AppData\\Local\\Programs\\Python\\Python38-32\\myscripts\\flask-tabler\\app\\base\\testfiles\\'       
# #Pass extension - removed inside method

# filename='PALM GROVE (2).dxf'                   # Here give only filename
# filename='PALMGROVE_floorwise_setbacks.dxf'
# #method returns a dict with handle

# start_time=time.strftime('%H:%M:%S')

# print(f'Start time is:{start_time}')

# response1=check_podium_setbacks(folder,filename)

# response2=podium_regular_setbacks(folder,filename)

# response3=check_redius_of_Arc(folder,filename)

# combine_dict=dict()

# combine_dict['Podium Setbacks  Response']=response1

# combine_dict['Regular Setback Response']=response2

# combine_dict['Podium radius of Arc Response']=response3

# end_time=time.strftime('%H:%M:%S')

# print(f'End time is:{end_time}')

# print(combine_dict)