import os
import ezdxf
import numpy as np
from shapely.geometry import Polygon,Point,LineString
import math
import json

def split(start,end,seg):  # this function used for Spliting the lines
    x_delta=(end[0]-start[0])/float(seg)
    y_delta=(end[1]-start[1])/float(seg)
    points=[]
    for i in range(1,seg):
        pts=[start[0]+i*x_delta,start[1]+i*y_delta]
        points.append(pts)
    return [start]+points+[end]

def check_ramp_width(ramp_cline,ramp_lwpolygon):

    ramp_lst_data=[]

    for ramp_cline1 in ramp_cline.virtual_entities():

        if  ramp_cline1.dxftype()=='LINE':

            start_ramp_cline1_pts=[ramp_cline1.dxf.start[0],ramp_cline1.dxf.start[1]]

            end_ramp_cline1_pts=[ramp_cline1.dxf.end[0],ramp_cline1.dxf.end[1]]

            cline1_pts=[start_ramp_cline1_pts,end_ramp_cline1_pts]

            np_ramp_cline1_points=np.array(cline1_pts).round(2)

            ramp_center_line1=LineString(np_ramp_cline1_points)

            split_center_line1=split(np_ramp_cline1_points[0],np_ramp_cline1_points[1],5)

            np_center_line1_pts=np.array(split_center_line1[2]).round(2)

            np_center_line1_point=Point(np_center_line1_pts)

            # ramp polygon converting into lines

            for ramp_lwpolygon_line in ramp_lwpolygon.virtual_entities():

                if ramp_lwpolygon_line.dxftype()=="LINE":

                    ramp_start_pts=[ramp_lwpolygon_line.dxf.start[0],ramp_lwpolygon_line.dxf.start[1]]

                    ramp_end_pts=[ramp_lwpolygon_line.dxf.end[0],ramp_lwpolygon_line.dxf.end[1]]

                    ramp_line=LineString([ramp_start_pts,ramp_end_pts])

                    if round(ramp_center_line1.distance(ramp_line))!=0:

                        ramp_lst_data.append(round(np_center_line1_point.distance(ramp_line),2))

    if ramp_lst_data!=[]:

            return min(ramp_lst_data)*2

def arc_angle_span_deg(start: float, end: float) -> float:
    """ Returns the counter clockwise angle from `start` to `end` in degrees.
    """
    # start == end is 0 by definition:
    if math.isclose(start, end):
        return 0.0

    # Special treatment for end angle == 180 deg:
    if not math.isclose(end, 360.0):
        end %= 360.0

    start %= 360.0

    if end < start:
        end += 360.0
    return end - start

def RampLENGTHandBuildingHeight(msp):

    areturnValueDict = dict()

    if (msp is None):

        return areturnValueDict

    try:

        print('read file for Ramp Length and Floor Height')

        building_text_data = msp.query('MTEXT TEXT[layer=="_BuildingName"]')

        building_polygon_data = msp.query('LWPOLYLINE[layer=="_BuildingName"]')

        section_polygon_data = msp.query('LWPOLYLINE[layer=="_Section"]')

        floor_in_section_text_data = msp.query('TEXT MTEXT[layer=="_FloorInSection"]')

        floor_in_section_polygon_data = msp.query('LWPOLYLINE[layer=="_FloorInSection"]')

        floor_text_data =msp.query('TEXT MTEXT[layer=="_Floor"]')

        floor_polygon_data=msp.query('LWPOLYLINE[layer=="_Floor"]')

        ramp_text_data =msp.query('TEXT MTEXT[layer=="_Ramp"]')

        ramp_polygon_data = msp.query('LWPOLYLINE[layer=="_Ramp"]')

        # Building text
        aFloorListTmp=[]
        rampRefDict=dict()

        for building_text in building_text_data:

            building_text_attribs = building_text.dxfattribs()

            building_text_insert = building_text_attribs.get('insert')

            building_name = building_text_attribs.get('text') if building_text.dxftype() == 'TEXT' else building_text.plain_text()

            building_text_pts = [building_text_insert[0], building_text_insert[1]]

            np_building_text_pts = np.array(building_text_pts)

            building_text_point = Point(np_building_text_pts)

            # Building polygon data

            for building_polygon in building_polygon_data:

                building_polygon_pts = [bp[0:2] for bp in building_polygon.get_points()]

                building_ref_id = building_polygon.dxf.handle

                np_building_polygon_pts = np.array(building_polygon_pts).round(1)

                building_polygon_points = Polygon(np_building_polygon_pts)

                # building polygon contains building text data

                if building_polygon_points.contains(building_text_point) == True or building_polygon_points.touches(building_text_point) == True or round(building_polygon_points.distance(building_text_point),1) == 0.0:

                    floor_dict=dict()

                    for floor_text in floor_text_data:

                        floor_text_attribs = floor_text.dxfattribs()

                        floor_text_insert = floor_text_attribs.get('insert')

                        floor_name = floor_text_attribs.get('text') if floor_text.dxftype() == 'TEXT' else floor_text.plain_text()

                        floor_text_pts = [floor_text_insert[0], floor_text_insert[1]]

                        np_floor_text_pts = np.array(floor_text_pts)

                        floor_text_point = Point(np_floor_text_pts)

                        for floor_polygon in floor_polygon_data:

                            floor_polygon_pts = [fp[0:2] for fp in floor_polygon.get_points()]

                            floor_ref_id = floor_polygon.dxf.handle

                            np_floor_polygon_pts = np.array(floor_polygon_pts).round(1)

                            floor_polygon_points = Polygon(np_floor_polygon_pts)

                            if floor_polygon_points.contains(floor_text_point) == True or floor_polygon_points.touches(floor_text_point) == True or round(floor_polygon_points.distance(floor_text_point), 1) == 0.0:

                                if building_polygon_points.contains(floor_polygon_points) == True or building_polygon_points.touches(floor_polygon_points) == True or round(building_polygon_points.distance(floor_polygon_points),1) == 0.0:

                                    ramp_dict=dict()

                                    for ramp_text in ramp_text_data:

                                        ramp_text_attribs = ramp_text.dxfattribs()

                                        ramp_text_insert = ramp_text_attribs.get('insert')

                                        ramp_name = ramp_text_attribs.get('text') if ramp_text.dxftype() == 'TEXT' else ramp_text.plain_text()

                                        ramp_text_pts = [ramp_text_insert[0], ramp_text_insert[1]]

                                        np_ramp_text_pts = np.array(ramp_text_pts)

                                        ramp_text_point = Point(np_ramp_text_pts)

                                        for ramp_polygon in ramp_polygon_data:

                                            if ramp_polygon.dxf.linetype!='CENTER':

                                                ramp_polygon_pts = [rp[0:2] for rp in ramp_polygon.get_points()]

                                                if len(ramp_polygon_pts)>=4:

                                                    ramp_ref_id = ramp_polygon.dxf.handle

                                                    np_ramp_polygon_pts = np.array(ramp_polygon_pts).round(1)

                                                    ramp_polygon_points = Polygon(np_ramp_polygon_pts)

                                                    if ramp_polygon_points.contains(ramp_text_point) == True or ramp_polygon_points.touches(ramp_text_point) == True or round(ramp_polygon_points.distance(ramp_text_point), 1) == 0.0:

                                                        if floor_polygon_points.contains(ramp_polygon_points) == True or floor_polygon_points.touches(ramp_polygon_points) == True or round(floor_polygon_points.distance(ramp_polygon_points), 1) == 0.0:

                                                            for ramp_center_line in ramp_polygon_data:

                                                                if ramp_center_line.dxf.linetype =='CENTER':

                                                                    ramp_center_line_pts = [[rcl[0],rcl[1],rcl[-1]] for rcl in ramp_center_line.get_points()]

                                                                    ramp_center_line_ref_id = ramp_polygon.dxf.handle

                                                                    np_ramp_center_line_pts = np.array(ramp_center_line_pts)

                                                                    ramp_center_line_points = LineString(np_ramp_center_line_pts)

                                                                    if ramp_polygon_points.contains(ramp_center_line_points) == True or ramp_polygon_points.touches(ramp_center_line_points) == True or round(ramp_polygon_points.distance(ramp_center_line_points),1) == 0.0:

                                                                        total_arc_length=[]

                                                                        for center_line_entity in ramp_center_line.virtual_entities():

                                                                            if center_line_entity.dxftype()=='LINE':

                                                                                line_length=LineString([[center_line_entity.dxf.start[0],center_line_entity.dxf.start[1]],[center_line_entity.dxf.end[0],center_line_entity.dxf.end[1]]]).length

                                                                                total_arc_length.append(line_length)

                                                                            elif(center_line_entity.dxftype()=='ARC'):

                                                                                start_angle=center_line_entity.dxf.start_angle

                                                                                end_angle=center_line_entity.dxf.end_angle

                                                                                arc_angle=arc_angle_span_deg(start_angle,end_angle)

                                                                                diameter=center_line_entity.dxf.radius

                                                                                new_arc_length = (math.pi * diameter) * (arc_angle / 180)

                                                                                total_arc_length.append(new_arc_length)

                                                                        #ramp_length=f'Ramp Length:{round(sum(map(float,total_arc_length)),2)}'
                                                                        #ramp_width=f'Ramp Width:{check_ramp_width(ramp_center_line,ramp_polygon)}'
                                                                        ramp_length=round(sum(map(float,total_arc_length)),2)
                                                                        ramp_width=check_ramp_width(ramp_center_line,ramp_polygon)

                                                                        ramp_dict[ramp_center_line_ref_id]=[ramp_name,ramp_length,ramp_width]
                                                                        rampDict = dict()
                                                                        rampDict['RAMP_REF_ID']=ramp_ref_id
                                                                        rampDict['RAMP_NAME_TEXT']=ramp_name
                                                                        rampDict['BLDG_NAME']=building_name
                                                                        rampDict['BLDG_REF_ID']=building_ref_id
                                                                        rampDict['BLDG_FLOOR_KEY']=building_name.strip()+"-"+floor_name.strip()
                                                                        rampDict['FLOOR_NAME']=floor_name
                                                                        rampDict['FLOOR_REF_ID']=floor_ref_id

                                                                        rampDict['RAMP_LENGTH']=ramp_length
                                                                        rampDict['RAMP_WIDTH']=ramp_width

                                                                        
                                                                        rampRefDict[ramp_ref_id]=rampDict
                                                                        
                                                                        

                                    if len(ramp_dict)>0:

                                        floor_dict[floor_ref_id]=[floor_name,ramp_dict]
                                        #print('Floor Dict ', floor_dict)

                    floor_inSectionDict = dict()

                    for section_polygon in section_polygon_data:

                        section_polygon_pts = [sp[0:2] for sp in section_polygon.get_points()]

                        np_section_polygon_pts = np.array(section_polygon_pts).round(1)

                        section_polygon_points = Polygon(np_section_polygon_pts)

                        if building_polygon_points.contains(section_polygon_points) == True:

                            for floor_in_section_polygon in floor_in_section_polygon_data:

                                floorINSectionID = floor_in_section_polygon.dxf.handle

                                floor_in_section_polygon_pts = [fsp[0:2] for fsp in
                                                                floor_in_section_polygon.get_points()]

                                np_floor_in_section_polygon_pts = np.array(floor_in_section_polygon_pts).round(1)

                                floor_in_section_polygon_points = Polygon(np_floor_in_section_polygon_pts)

                                floor_in_section_data=[]

                                for floor_in_section_text in floor_in_section_text_data:

                                    floor_in_section_attribs = floor_in_section_text.dxfattribs()

                                    floor_in_section_name = floor_in_section_attribs.get('text') if floor_in_section_text.dxftype() == 'TEXT' else floor_in_section_text.plain_text()

                                    if floor_in_section_name !='TDR Floor':

                                        floor_in_section_insert = floor_in_section_attribs.get('insert')

                                        floor_insection_text_pts = [floor_in_section_insert[0], floor_in_section_insert[1]]

                                        np_floor_insection_text_pts = np.array(floor_insection_text_pts).round(1)

                                        abs_np_floor_in_section_text_point = Point(np_floor_insection_text_pts)

                                        # check floor in section polygon data contains floor in section text

                                        if floor_in_section_polygon_points.contains(abs_np_floor_in_section_text_point) == True or \
                                        floor_in_section_polygon_points.touches(abs_np_floor_in_section_text_point) == True \
                                        or round(floor_in_section_polygon_points.distance(abs_np_floor_in_section_text_point),1) ==0.0:

                                            # check floor in section polygon contains section polygon

                                            if section_polygon_points.contains(floor_in_section_polygon_points) == True:

                                                floor_in_section_data.append(floor_in_section_name)
                                        #else:
                                        #    print('Floor doesnt contain label or touch ' , floor_in_section_name ,' label ' , floor_in_section_insert )

                                if floor_in_section_data==[] or  floor_in_section_data is None:

                                    print(f'Floor In Section Does Not Contain Any Label,On This Polygon ID{floorINSectionID} ')

                                elif(len(floor_in_section_data)>1):

                                    print(f'Floor In Section polygon id:{floorINSectionID} Contain More Than One Label name {[floor_in_section_data]}')

                                else:

                                    floor_inSectionDict[floorINSectionID] = [floor_in_section_data,floor_in_section_polygon_points]


                    if (floor_dict is not None and floor_inSectionDict is not None) or (floor_dict!={} and floor_inSectionDict!={}):

                        for floor_ID,floorNameRampLength in floor_dict.items():

                            for floorSECID,FloorNAMEPOLY in floor_inSectionDict.items():

                                if (str(floorNameRampLength[0]).lower() in str(FloorNAMEPOLY[0]).lower()) or (str(FloorNAMEPOLY[0]).lower() in str(floorNameRampLength[0]).lower()):

                                    bounding_box = FloorNAMEPOLY[1].minimum_rotated_rectangle

                                    x, y = bounding_box.exterior.coords.xy

                                    edge_length = (Point(x[0], y[0]).distance(Point(x[1], y[1])),Point(x[1], y[1]).distance(Point(x[2], y[2])))

                                    floor_height = f'Floor Height:{round(min(edge_length), 2)}'
                                    #print('Floor Height ', floor_height)

                                    floorNameRampLength.append(floor_height)

                        
                        areturnValueDict = rampRefDict
                    else:
                        print('Floor data is missing')

    except IndexError:

        print(f'Does not match any value')

        return areturnValueDict #json.dumps(areturnValueDict)  # areturnValueDict

    except IOError:

        print(f'Not a DXF file or a generic I/O error.')

        return areturnValueDict #return json.dumps(areturnValueDict)  # areturnValueDict

    except ezdxf.DXFStructureError:

        print(f'Invalid or corrupted DXF file.')

        return areturnValueDict #return json.dumps(areturnValueDict)  # areturnValueDict

    return areturnValueDict #return json.dumps(areturnValueDict)  # areturnValueDict


# # path of the filename
#
# folder=r'E:\production_code\dxf_files\FireBuildings'
#
# #Pass extension - removed inside method
#
# filename='HONERHOMESSUBMISSIONDRAWINGSTOWER9th july (1).dxf'   # Here give only filename
#
# dxf_path=os.path.join(folder,filename)
#
# dxf_file=ezdxf.readfile(dxf_path)
#
# msp=dxf_file.modelspace()
#
# response1=RampLENGTHandBuildingHeight(msp)
#
# print(response1)