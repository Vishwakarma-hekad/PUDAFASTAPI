import os

import ezdxf

from shapely.geometry import Point,Polygon,MultiPolygon

from shapely.geometry import LineString

import numpy as np

import shapely.geometry

from shapely.ops import unary_union

def Travelled_Distance(msp):#folder:str,filename:str):

    returnValueDict=dict()

    resultsList=[]

    if (msp is None ):#folder is None or filename is None):

        return returnValueDict

    try:


        #dxf_path=os.path.join(folder,filename)
        #read_dxf=ezdxf.readfile(dxf_path)

        #print('read file')

        #msp=read_dxf.modelspace()

        for building_text in msp.query('TEXT[layer=="_BuildingName"]'):



            building_text_attrib=building_text.dxfattribs()



            insert_building_text=building_text_attrib.get('insert')



            building_text_name=building_text_attrib.get('text')



            insert_building_text_pts=[insert_building_text[0],insert_building_text[1]]



            np_insert_building_text_pts=np.array(insert_building_text_pts).round(1)



            abs_np_insert_building_text_pts=abs(np_insert_building_text_pts)



            building_text_point=Point(abs_np_insert_building_text_pts)



            for building_polygon in msp.query('LWPOLYLINE[layer=="_BuildingName"]'):



                building_polygon_pts=[bp[0:2] for bp in building_polygon.get_points()]



                building_ref_id=building_polygon.dxf.handle



                np_building_polygon_pts=np.array(building_polygon_pts).round(1)



                abs_np_building_polygon_pts=abs(np_building_polygon_pts)



                building_polygon_points=Polygon(abs_np_building_polygon_pts)



                if (building_polygon_points.touches(building_text_point)==True) or (building_polygon_points.contains(building_text_point)==True) or (round(building_text_point.distance(building_polygon_points))==0):



                    building_dict=dict()



                    #print(True)



                    #For floor text data



                    for floor_text in msp.query('TEXT[layer=="_Floor"]'):



                        floor_text_attrib=floor_text.dxfattribs()



                        insert_floor_text=floor_text_attrib.get('insert')



                        floor_text_name=floor_text_attrib.get('text')



                        insert_floor_text_pts=[insert_floor_text[0],insert_floor_text[1]]



                        np_insert_floor_text_pts=np.array(insert_floor_text_pts).round(1)



                        abs_np_insert_floor_text_pts=abs(np_insert_floor_text_pts)



                        floor_text_point=Point(abs_np_insert_floor_text_pts)



                        #floor polygon data



                        for floor_polygon in msp.query('LWPOLYLINE[layer=="_Floor"]'):



                            floor_polygon_pts=[fp[0:2]for fp in floor_polygon.get_points()]



                            floor_ref_id=floor_polygon.dxf.handle



                            np_floor_polygon_pts=np.array(floor_polygon_pts).round(1)



                            abs_np_floor_polygon_pts=abs(np_floor_polygon_pts)



                            floor_polygon_points=Polygon(abs_np_floor_polygon_pts)



                            #check floor_text in floor_polygon

                            if building_polygon_points.contains(floor_polygon_points)==True:



                                if floor_polygon_points.contains(floor_text_point)==True or floor_polygon_points.touches(floor_text_point)==True:



                                    #print(floor_text_name)



                                    tot_stair_data=[]



                                    # for resibuaOutline layer



                                    for resibua_polygon in msp.query('LWPOLYLINE[layer=="_ResiBUAOutline"]'):



                                        resibua_polygon_pts=[rp[0:2] for rp in resibua_polygon.get_points()]



                                        np_resibua_polygon_pts=np.array(resibua_polygon_pts).round(1)



                                        abs_np_resibua_polygon_pts=abs(np_resibua_polygon_pts)



                                        resibua_polygon_points=Polygon(abs_np_resibua_polygon_pts)



                                        if floor_polygon_points.contains(resibua_polygon_points)==True:



                                            ressi_bounding_box=resibua_polygon_points.minimum_rotated_rectangle



                                            ressi_x,ressi_y=ressi_bounding_box.exterior.coords.xy



                                            ressi_bounding_box_pts=[[ressi_x[0],ressi_y[0]],[ressi_x[1],ressi_y[1]],[ressi_x[2],ressi_y[2]],[ressi_x[3],ressi_y[3]]]



                                            ressi_np_bounding_box_pts=np.array(ressi_bounding_box_pts).round(1)



                                            ressi_abs_np_bounding_box_pts=abs(ressi_np_bounding_box_pts)



                                            for ressi_stair_polygon in msp.query('LWPOLYLINE[layer=="_StairCase"]'):



                                                ressi_stair_polygon_pts=[ressi_sp[0:2] for ressi_sp in ressi_stair_polygon.get_points()]



                                                ressi_np_stair_polygon_pts=np.array(ressi_stair_polygon_pts).round(1)



                                                ressi_abs_np_stair_polygon_pts=abs(ressi_np_stair_polygon_pts)



                                                if len(ressi_abs_np_stair_polygon_pts)>=4:



                                                    ressi_stair_polygon_points=Polygon(ressi_abs_np_stair_polygon_pts)



                                                    if floor_polygon_points.contains(ressi_stair_polygon_points)==True:



                                                        resibua_to_stair_dst=[]



                                                        for resibua_pts in ressi_abs_np_bounding_box_pts:



                                                            resibua_point=Point(resibua_pts)



                                                            resibua_to_stair_dst.append(round(ressi_stair_polygon_points.distance(resibua_point),1))



                                                        if resibua_to_stair_dst!=[]:



                                                            tot_stair_data.append(min(resibua_to_stair_dst))



                                    #for commbuaoutline layer



                                    for commbua_polygon in msp.query('LWPOLYLINE[layer=="_CommBUAOutline"]'):



                                        commbua_polygon_pts=[cp[0:2] for cp in commbua_polygon.get_points()]



                                        np_commbua_polygon_pts=np.array(commbua_polygon_pts).round(1)



                                        abs_np_commbua_polygon_pts=abs(np_commbua_polygon_pts)



                                        commbua_polygon_points=Polygon(abs_np_commbua_polygon_pts)



                                        if floor_polygon_points.contains(commbua_polygon_points)==True:



                                            comm_bounding_box=commbua_polygon_points.minimum_rotated_rectangle



                                            comm_x,comm_y=comm_bounding_box.exterior.coords.xy



                                            comm_bounding_box_pts=[[comm_x[0],comm_y[0]],[comm_x[1],comm_y[1]],[comm_x[2],comm_y[2]],[comm_x[3],comm_y[3]]]



                                            comm_np_bounding_box_pts=np.array(comm_bounding_box_pts).round(1)



                                            comm_abs_np_bounding_box_pts=abs(comm_np_bounding_box_pts)



                                            for comm_stair_polygon in msp.query('LWPOLYLINE[layer=="_StairCase"]'):



                                                comm_stair_polygon_pts=[comm_sp[0:2] for comm_sp in comm_stair_polygon.get_points()]



                                                comm_np_stair_polygon_pts=np.array(comm_stair_polygon_pts).round(1)



                                                comm_abs_np_stair_polygon_pts=abs(comm_np_stair_polygon_pts)



                                                if len(comm_abs_np_stair_polygon_pts)>=4:



                                                    comm_stair_polygon_points=Polygon(comm_abs_np_stair_polygon_pts)



                                                    if floor_polygon_points.contains(comm_stair_polygon_points)==True:



                                                        commbua_to_stair_dst=[]



                                                        for commbua_pts in comm_abs_np_bounding_box_pts:



                                                            commbua_point=Point(commbua_pts)



                                                            commbua_to_stair_dst.append(round(comm_stair_polygon_points.distance(commbua_point),1))



                                                        if commbua_to_stair_dst!=[]:



                                                            tot_stair_data.append(min(commbua_to_stair_dst))



                                    tmpPropWorkDict=dict()



                                    if tot_stair_data !=[]:



                                        tmpPropWorkDict[floor_text_name]=tot_stair_data



                                        if tmpPropWorkDict!={}:



                                            building_dict[floor_ref_id]=tmpPropWorkDict



                    building_tmpworkdict=dict()



                    if building_dict!={}:



                        building_tmpworkdict[building_text_name]=building_dict



                    if building_tmpworkdict!={}:



                        returnValueDict[building_ref_id]=building_tmpworkdict

    except IOError:



        print(f'Not a DXF file or a generic I/O error.')



        return returnValueDict



    except ezdxf.DXFStructureError:



             print(f'Invalid or corrupted DXF file.')



             return returnValueDict



    return returnValueDict









#path of the filename



#folder=r'E:\python'

#folder=r'C:\\Users\\esiva\\AppData\\Local\\Programs\\Python\\Python38-32\\myscripts\\flask-tabler\\app\\base\\testfiles\\'                 


#Pass extension - removed inside method



#filename='TDR_SULOCHANA_stairdistance.dxf'                   # Here give only filename
#filename='vijayalaxmi_stairdistance.dxf' 


#method returns a dict with handle


# dxf_path=os.path.join(folder,filename)
# read_dxf=ezdxf.readfile(dxf_path)


# print('read file')



# msp=read_dxf.modelspace()

# response=Travelled_Distance(msp)



# print ('Travelled Distance ' , response )