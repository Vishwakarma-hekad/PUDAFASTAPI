'''
DOCUMENTATION:  #Date 19_12_2025
-------------

Find total area of balcony,accessory,ventilation shaft,slabcutout void and refused area in resi bua,
commercial bua,ind bua and special use bua in floor wise of buildings.

steps:
1.iterate all layer of query entities.

ex:_BuildingName,_Floor,_ResiBUAOutline,_CommBUAOutline,_IndBUAOutline,_SpecialUseBUAOutline,_AccessoryUse,_Balcony,_VentilationShaft,_SlabCutoutVoid and _RefugeArea.

2.iterate all building text data and polygon data.

3.Check Building text data in building polygon or not, if yes.

4.iterate all floor text data and polygon data.

5.Check floor text data in floor polygon or not,if yes.

6.Check floor polygon in building polygon or not.if yes.

7.iterate ResiBUAOutline,CommBUAOutline,IndBUAOutline and _SpecialUseBUAOutline.

8.Check ResiBUAOutline polygon,CommBUAOutline polygon,IndBUAOutline polygon and SpecialUseBUAOutline polygon in floor polygon,if yes.

9.iterate AccessoryUse,Balcony,VentilationShaft,SlabCutoutVoid and RefugeArea.

10.Check AccessoryUse polygon,Balcony polygon,VentilationShaft polygon,SlabCutoutVoid polygon and RefugeArea polygon in ResiBUAOutline polygon,

    CommBUAOutline polygon,IndBUAOutline polygon and SpecialUseBUAOutline polygon.if yes

 11.calculate total area of balcony polygon,accessory polygon,ventilation polygon,slab cutout polygon and refuse area polygon add into balcony list,accessory list,
    ventilation list,slab cutout list and refuse area list.

 12.sum of all values of balcony list,ventilation list,accessory list,slab cutout list and refuse area list.This all value in to floor list.
'''
import os
import ezdxf
from shapely.geometry import LineString, Polygon, Point
import numpy as np
import re,math
from shapely.ops import unary_union, linemerge, polygonize,snap

def Parking_PolygonData(Parking_data, floor_polygon_points):
    max_area = 0.0
    poly_entity = None
    for parking_poly in Parking_data:

        if parking_poly.closed and len([pp[0:2] for pp in parking_poly.get_points()]) >= 3:

            parking_polygon_points = Polygon([pp[0:2] for pp in parking_poly.get_points()])

            if floor_polygon_points.contains(parking_polygon_points):

                parking_area = round(parking_polygon_points.area, 1)

                if parking_area > max_area:
                    max_area = parking_area
                    poly_entity = parking_poly
    return poly_entity



# def Polygon_Merger_ARC(Merger_polygon, arc_resolution=50):
#     # Extract points with bulge info
#     commbua_polygon_pts = list(Merger_polygon.get_points('xyb'))  # x, y, bulge
#
#     if len(commbua_polygon_pts) > 2:
#         boundary_points = []
#         has_arc = False
#
#         for i, (x1, y1, bulge) in enumerate(commbua_polygon_pts):
#             start = (x1, y1)
#             if not boundary_points or boundary_points[-1] != start:
#                 boundary_points.append(start)
#
#             # Next point (wrap around)
#             x2, y2, _ = commbua_polygon_pts[(i + 1) % len(commbua_polygon_pts)]
#             end = (x2, y2)
#
#             if abs(bulge) < 1e-9:
#                 # Straight segment
#                 boundary_points.append(end)
#             else:
#                 has_arc = True
#                 # Included angle
#                 theta = 4 * math.atan(bulge)
#
#                 # Chord length
#                 chord = math.hypot(x2 - x1, y2 - y1)
#
#                 # Radius (can be negative depending on bulge)
#                 r = chord / (2 * math.sin(theta / 2))
#
#                 # Midpoint of chord
#                 mx, my = (x1 + x2) / 2, (y1 + y2) / 2
#
#                 # Angle of chord
#                 alpha = math.atan2(y2 - y1, x2 - x1)
#
#                 # Distance from midpoint to center
#                 h = math.sqrt(abs(r ** 2 - (chord / 2) ** 2))
#
#                 # Center (sign depends on bulge)
#                 cx = mx - h * math.sin(alpha) * np.sign(bulge)
#                 cy = my + h * math.cos(alpha) * np.sign(bulge)
#
#                 # Start/end angles relative to center
#                 a1 = math.atan2(y1 - cy, x1 - cx)
#                 a2 = math.atan2(y2 - cy, x2 - cx)
#
#                 # Normalize sweep according to bulge sign
#                 if bulge > 0 and a2 < a1:
#                     a2 += 2 * math.pi
#                 elif bulge < 0 and a2 > a1:
#                     a2 -= 2 * math.pi
#
#                 # Interpolate arc
#                 arc_angles = np.linspace(a1, a2, arc_resolution)
#                 arc_pts = [(cx + abs(r) * math.cos(ang), cy + abs(r) * math.sin(ang)) for ang in arc_angles]
#
#                 # Merge arc points
#                 boundary_points.extend(arc_pts[1:])  # skip duplicate start
#
#         # Ensure closed polygon
#         if boundary_points[0] != boundary_points[-1]:
#             boundary_points.append(boundary_points[0])
#
#         # If no arc found → return plain lwpolyline polygon
#         if not has_arc:
#             boundary_points = [(x, y) for x, y, _ in commbua_polygon_pts]
#
#         return Polygon(boundary_points)

def convert_arc_to_linestring( arc_center, arc_radius, start_angle_deg, end_angle_deg):

    center_x = float(arc_center[0])
    center_y = float(arc_center[1])


    start_angle = float(start_angle_deg) % 360.0
    end_angle = float(end_angle_deg) % 360.0

    # Ensure counter-clockwise sweep
    if end_angle <= start_angle:
        end_angle += 360.0

    segment_count = max(256, int(arc_radius * 8))

    theta_values = np.deg2rad(np.linspace(start_angle, end_angle, segment_count))

    x_coords = center_x + arc_radius * np.cos(theta_values)
    y_coords = center_y + arc_radius * np.sin(theta_values)

    return LineString(np.column_stack((x_coords, y_coords)))
# -------------------------------------------------
# Merge LINE + ARC entities into Polygon
# -------------------------------------------------
def Polygon_Merger_ARC( dxf_entity):

    # -------------------------------------------------
    # STEP 3: ARC FOUND → Execute Your Existing Logic
    # -------------------------------------------------
    boundary_segments = []

    for entity in dxf_entity.virtual_entities():

        entity_type = entity.dxftype()

        # -------- LINE --------
        if entity_type == "LINE":

            start_point = entity.dxf.start
            end_point = entity.dxf.end

            line_segment = LineString([(start_point[0], start_point[1]),(end_point[0], end_point[1])])

            boundary_segments.append(line_segment)

        # -------- ARC --------
        elif entity_type == "ARC":

            arc_segment = convert_arc_to_linestring(
                entity.dxf.center,
                entity.dxf.radius,
                entity.dxf.start_angle,
                entity.dxf.end_angle
            )

            boundary_segments.append(arc_segment)

    if not boundary_segments:
        return Polygon()

    # -------------------------------------------------
    # Merge all segments
    # -------------------------------------------------
    merged_geometry = unary_union(boundary_segments)

    merged_geometry = snap(merged_geometry, merged_geometry, 1e-4)

    merged_geometry = linemerge(merged_geometry)

    # -------------------------------------------------
    # Create polygons
    # -------------------------------------------------
    polygon_list = list(polygonize(merged_geometry))

    if not polygon_list:
        # Fallback buffer method
        buffered_boundaries = unary_union([segment.buffer(0.001).boundary for segment in boundary_segments])
        polygon_list = list(polygonize(buffered_boundaries))

        if not polygon_list:
            return Polygon()

    # -------------------------------------------------
    # Detect outer boundary and holes
    # -------------------------------------------------
    polygon_list.sort(key=lambda poly: poly.area, reverse=True)

    outer_boundary = polygon_list[0]
    hole_boundaries = []

    for poly in polygon_list[1:]:
        if outer_boundary.contains(poly):
            hole_boundaries.append(poly.exterior.coords)

    final_polygon = Polygon(outer_boundary.exterior.coords,hole_boundaries)

    if not final_polygon.is_valid:
        final_polygon = final_polygon.buffer(0)

    return final_polygon

def checkString4AlphaDigits(nameOfFloor: str):
    nameOfFloor = nameOfFloor.upper()

    word2RemoveList = ['|', 'TYPICAL', 'FLOOR', 'PLAN']

    pIndex = nameOfFloor.find("|")

    if pIndex > -1:
        nameOfFloor = nameOfFloor[pIndex:].upper()

    for word2Remove in word2RemoveList:
        nameOfFloor = nameOfFloor.replace(word2Remove, "")

    nameOfFloor_Check = re.sub(r'|\s|\t|\,|\-|\*|', '', nameOfFloor)

    isAlpha = nameOfFloor_Check.isalpha()  # check if string is only alpha a-z
    isAlphaNum = nameOfFloor_Check.isalnum()  # check if string has digits and alpha
    isDigits = nameOfFloor_Check.isnumeric()  # only digits
    # print("check str",nameOfFloor_Check )
    # print ("  Alpha, isAlphaNum, has Digits ", isAlpha, isAlphaNum, isDigits)

    if (isDigits and isAlphaNum and not (isAlpha)):
        return "DIGITS"
    elif ((isAlpha and isAlphaNum) and not (isDigits)):
        return "ONLYTEXT"
    elif (isAlphaNum and not (isDigits and isAlpha)):
        return "ALPHANUM"
    else:
        print("unknown, default to ALPHA ")
        return "ONLYTEXT"
'''
BUILDINGS (A,B,C,D,E,F,G,H,I) or  BUILDINGS (A,B & C) or BUILDINGS (A & B),
BUILDINGS (1,2,3) or BUILDINGS (1-6)
'''
def DetermineBuildingNumbers(nameOfFloor: str):
    from num2words import num2words

    retVal = []

    # check if string has any digits otherwise just split the string

    word2RemoveList = ['|']

    # print("The original string is : " + nameOfFloor)

    if "|" in nameOfFloor:
        nameOfFloor = nameOfFloor[nameOfFloor.find("|"):].upper()

    # clean
    for word2Remove in word2RemoveList:
        nameOfFloor = nameOfFloor.replace(word2Remove, "")

    # translate
    if any(p in nameOfFloor for p in ["&", 'AND', ' ']) == True:
        nameOfFloor = nameOfFloor.replace("&", ',')
        nameOfFloor = nameOfFloor.replace("AND", ',')

    if '(' and ')' in nameOfFloor:

        start_index = nameOfFloor.find('(')

        end_index = nameOfFloor.find(')')

        before_filter_text = nameOfFloor[:start_index].upper()

        filter_text = nameOfFloor[start_index + 1:end_index].upper()

        if any(x in filter_text for x in ['AND', '&', ',', '-']) == True and any(
                y not in before_filter_text for y in ['AND', '&', ',', '-']) == True:

            typeOfString = checkString4AlphaDigits(filter_text)  # ALPHA, DIGITS, ALPHANUM

            print("determined type of string as : " + typeOfString)

            if ("DIGITS" in typeOfString):  # nameOfFloor is not None and hasDigits):

                # Convert String ranges to list
                # Using sum() + list comprehension + enumerate() + split()
                # print("The original string is : " + nameOfFloor)
                # remove spaces and alphabhets

                nameOfFloor = re.sub(r'[a-z]|[A-Z]|\s|\t|\|', '', nameOfFloor)

                # print("After removing spaces/alphabhets string is now : " + nameOfFloor)

                # extract the number ranges
                nameOfFloor = re.sub("[^0123456789\,\-]", "", nameOfFloor)

                if (nameOfFloor[0] == "-"):
                    nameOfFloor = nameOfFloor[1:]
                # print("The number range from string is : " + nameOfFloor)

                # printing original string
                # print("The string is :" + nameOfFloor)
                if (nameOfFloor[0] == ","):
                    nameOfFloor = nameOfFloor[1:]
                # print("The final string is :" + nameOfFloor)
                # Convert String ranges to list
                # Using sum() + list comprehension + enumerate() + split()
                res = sum(
                    ((list(range(*[int(b) + c for c, b in enumerate(a.split('-'))])) if ('-' in a or ' ' in a) else [a])
                     for a in re.split(',|\s', nameOfFloor)), [])
                # if '-' in a else [int(a)]) for a in nameOfFloor.split(',')), [])

                # printing result
                # print("List after conversion from string : " + str(res))

                # convert them to ordinal words 1 First 2 secound 4 fourth etc ...
                wordResults = []
                for numberOfFlr in res:
                    wordResults.append(before_filter_text + '(' + num2words(numberOfFlr, to='ordinal').upper() + ')')

                retVal = wordResults

            elif ("ALPHANUM" in typeOfString):

                nameOfFloor = re.sub(r'|\s|\t|\|', '', nameOfFloor)
                # print ("after cleanup:" + nameOfFloor.strip())

                if (nameOfFloor[0] == "-"):
                    nameOfFloor = nameOfFloor[1:]
                # print("The mixed word and number range is : " + nameOfFloor)

                wordResults = []

                for tok in nameOfFloor.split(","):
                    if (tok.isnumeric()):
                        asword = num2words(tok, to='ordinal').upper()
                        wordResults.append(asword)
                    else:
                        wordResults.append(tok)
                retVal = wordResults

            elif ("ONLYTEXT" in typeOfString):  # (not hasDigits and (","  in nameOfFloor or "-"  in nameOfFloor) ) :

                """ some have a words itself """

                wordResults = []

                if any(x in filter_text for x in ['AND', '&', ',']) == True and any(
                        y not in before_filter_text for y in ['AND', '&', ',']) == True:

                    filter_text = filter_text.replace('AND', ',')

                    filter_text = filter_text.replace('&', ',')

                    for nameStr in filter_text.split(","):
                        joined_bldg_text = before_filter_text + '(' + nameStr.strip() + ')'

                        wordResults.append(joined_bldg_text.upper())


                elif (any(x in before_filter_text for x in ['AND', '&', ',']) == True and any(
                        y not in filter_text.lower() for y in ['AND', '&', ',']) == True):

                    before_filter_text = before_filter_text.replace('AND', ',')

                    for nameStr in before_filter_text.split(","):
                        joined_bldg_text = nameStr + '(' + filter_text.strip() + ')'

                        wordResults.append(joined_bldg_text.upper())

                retVal = wordResults

        else:

            joint_filter_text = before_filter_text + "(" + filter_text.strip() + ")"

            retVal = [joint_filter_text]

    elif ('(' and ')' not in nameOfFloor and any(x in nameOfFloor for x in [',', 'AND', '&']) == True):

        filter_text = nameOfFloor

        wordResults = []

        for nameStr in filter_text.split(","):
            joined_bldg_text = nameStr.strip()

            wordResults.append(joined_bldg_text.upper())

        retVal = wordResults

    else:

        filter_text = nameOfFloor.strip()

        retVal = [filter_text]

    return retVal
# determineFloorNumbers logic
'''
TYPICAL - 3, 4, 5, 6, 7, 8 FLOOR PLAN
'''
def determineFloorNumbers(nameOfFloor: str):
    from num2words import num2words

    retVal = []

    import re
    # check if string has any digits otherwise just split the string

    word2RemoveList = ['|', 'TYPICAL', 'FLOOR', 'PLAN']

    # print("The original string is : " + nameOfFloor)

    if "|" in nameOfFloor:
        nameOfFloor = nameOfFloor[nameOfFloor.find("|"):].upper()

    # clean
    for word2Remove in word2RemoveList:
        nameOfFloor = nameOfFloor.replace(word2Remove, "")

    # translate
    if ("&" in nameOfFloor):
        nameOfFloor = nameOfFloor.replace("&", ',')

    typeOfString = checkString4AlphaDigits(nameOfFloor)  # ALPHA, DIGITS, ALPHANUM

    # print("determined type of string as : " + typeOfString)

    if ("DIGITS" in typeOfString):  # nameOfFloor is not None and hasDigits):

        # Convert String ranges to list
        # Using sum() + list comprehension + enumerate() + split()

        # print("The original string is : " + nameOfFloor)
        # remove spaces and alphabhets
        nameOfFloor = re.sub(r'[a-z]|[A-Z]|\s|\t|\|', '', nameOfFloor)

        # print("After removing spaces/alphabhets string is now : " + nameOfFloor)

        # extract the number ranges
        nameOfFloor = re.sub("[^0123456789\,\-]", "", nameOfFloor)

        if (nameOfFloor[0] == "-"):
            nameOfFloor = nameOfFloor[1:]
        # print("The number range from string is : " + nameOfFloor)

        # printing original string
        # print("The string is :" + nameOfFloor)
        if (nameOfFloor[0] == ","):
            nameOfFloor = nameOfFloor[1:]
        # print("The final string is :" + nameOfFloor)
        # Convert String ranges to list
        # Using sum() + list comprehension + enumerate() + split()
        res = sum(
            ((list(range(*[int(b) + c for c, b in enumerate(a.split('-'))])) if ('-' in a or ' ' in a) else [a]) for a
             in re.split(',|\s', nameOfFloor)), [])
        # if '-' in a else [int(a)]) for a in nameOfFloor.split(',')), [])

        # printing result
        # print("List after conversion from string : " + str(res))

        # convert them to ordinal words 1 First 2 secound 4 fourth etc ...
        wordResults = []
        for numberOfFlr in res:
            wordResults.append(num2words(numberOfFlr, to='ordinal').upper())

        retVal = wordResults

    elif ("ALPHANUM" in typeOfString):
        nameOfFloor = re.sub(r'|\s|\t|\|', '', nameOfFloor)
        # print ("after cleanup:" + nameOfFloor.strip())

        if (nameOfFloor[0] == "-"):
            nameOfFloor = nameOfFloor[1:]
        # print("The mixed word and number range is : " + nameOfFloor)

        wordResults = []

        for tok in nameOfFloor.split(","):
            if (tok.isnumeric()):
                asword = num2words(tok, to='ordinal').upper()
                wordResults.append(asword)
            else:
                wordResults.append(tok)
        retVal = wordResults

    elif ("ONLYTEXT" in typeOfString):  # (not hasDigits and (","  in nameOfFloor or "-"  in nameOfFloor) ) :
        """ some have a words itself """
        words2Remove = ['FLOOR', 'PLAN', 'TYPICAL']

        # print("The original string is : " + nameOfFloor)
        for toRemove in words2Remove:
            nameOfFloor = nameOfFloor.replace(toRemove, "")

        # remove spaces
        nameOfFloor = re.sub(r'|\s|\t|\|', '', nameOfFloor)
        if ("&" in nameOfFloor):
            nameOfFloor = nameOfFloor.replace("&", ',')
        # print("After removing spaces string is now : " + nameOfFloor)

        if (nameOfFloor[0] == "-"):
            nameOfFloor = nameOfFloor[1:]
        # print("The word-number range is : " + nameOfFloor)

        # printing original string
        # print("The string is :" + nameOfFloor)
        if (nameOfFloor[0] == ","):
            nameOfFloor = nameOfFloor[1:]
            # print("The final string is :" + nameOfFloor)

        wordResults = []
        for nameStr in nameOfFloor.split(","):
            wordResults.append(nameStr)

        retVal = wordResults

    return retVal

def ResiBuaOutLine_Layer(ResiBUAOutLine_data):
    ResiBUAOutLine_dict = dict()

    ErrorResiBuaOutLine_dict = dict()

    unique_polygons = {}

    for ResiBUAOutLine_entity in ResiBUAOutLine_data:

        if ResiBUAOutLine_entity.dxftype() == 'LWPOLYLINE' and ResiBUAOutLine_entity.closed and len(
                [resip[0:2] for resip in ResiBUAOutLine_entity.get_points()]) >= 3:

            ResiBUAOutLinePolygonID = ResiBUAOutLine_entity.dxf.handle

            vertices = tuple(ResiBUAOutLine_entity.get_points())

            if vertices in unique_polygons:

                ErrorResiBuaOutLine_dict[ResiBUAOutLinePolygonID] = str(
                    f"ResiBUAOutline Layer Found Duplicate Polygon Of {ResiBUAOutLinePolygonID}.")

            else:

                unique_polygons[vertices] = ResiBUAOutLine_entity

            has_arc=any([entity.dxftype() =="ARC"for entity in ResiBUAOutLine_entity.virtual_entities()])
            if has_arc:
                ResiBUAOutLine_polygon = Polygon_Merger_ARC(ResiBUAOutLine_entity)
            else:
                ResiBUAOutLine_polygon = Polygon(np.array([resip[0:2] for resip in ResiBUAOutLine_entity.get_points()]))

            ResiBUAOutLine_Label = "None"
            for ResiBUAOutLineTEXT_entity in ResiBUAOutLine_data:

                if ResiBUAOutLineTEXT_entity.dxftype() == 'TEXT' or ResiBUAOutLineTEXT_entity.dxftype() == 'MTEXT':

                    resibuaLabelProperties = ResiBUAOutLineTEXT_entity.dxfattribs()

                    resibua_label = resibuaLabelProperties.get(
                        'text') if ResiBUAOutLineTEXT_entity.dxftype() == 'TEXT' else ResiBUAOutLineTEXT_entity.plain_text()

                    filtered_label = resibua_label.lower().replace(' ', '')

                    if filtered_label != "resi" and filtered_label != "resibua":

                        resibuaLabel_insert = resibuaLabelProperties.get('insert')

                        resibuaLabel_point = Point(np.array([resibuaLabel_insert[0], resibuaLabel_insert[1]]))

                        if ResiBUAOutLine_polygon.contains(resibuaLabel_point) or ResiBUAOutLine_polygon.touches(
                                resibuaLabel_point) or round(ResiBUAOutLine_polygon.distance(resibuaLabel_point),
                                                             1) == 0.0:
                            ResiBUAOutLine_Label = resibua_label

            ResiBUAOutLine_dict[ResiBUAOutLinePolygonID] = [ResiBUAOutLine_entity, ResiBUAOutLine_Label]

    return [ErrorResiBuaOutLine_dict, ResiBUAOutLine_dict]

def CommBuaOutLine_Layer(CommBUAOutLine_data):
    CommBUAOutLine_dict = dict()

    ErrorCommBUAOutLine_dict = dict()

    unique_polygons = {}

    for CommBUAOutLine_entity in CommBUAOutLine_data:

        if CommBUAOutLine_entity.dxftype() == 'LWPOLYLINE' and CommBUAOutLine_entity.closed:

            CommBUAOutLinePolygonID = CommBUAOutLine_entity.dxf.handle

            vertices = tuple(CommBUAOutLine_entity.get_points())

            if vertices in unique_polygons:

                ErrorCommBUAOutLine_dict[CommBUAOutLinePolygonID] = str(
                    f"CommBUAOutline Layer Found Duplicate Polygon Of {CommBUAOutLinePolygonID}.")

            else:

                unique_polygons[vertices] = CommBUAOutLine_entity


            has_arc=any([entity.dxftype()=="ARC" for entity in CommBUAOutLine_entity.virtual_entities()])

            if has_arc:

                CommBUAOutLine_polygon = Polygon_Merger_ARC(CommBUAOutLine_entity)

            else:

                CommBUAOutLine_polygon = Polygon(np.array([commp[0:2] for commp in CommBUAOutLine_entity.get_points()]))

            CommBUAOutLine_Label = "None"
            for CommBuaOutLineTEXT_entity in CommBUAOutLine_data:

                if CommBuaOutLineTEXT_entity.dxftype() == 'TEXT' or CommBuaOutLineTEXT_entity.dxftype() == 'MTEXT':

                    commbuaLabelProperties = CommBuaOutLineTEXT_entity.dxfattribs()

                    commbua_label = commbuaLabelProperties.get(
                        'text') if CommBuaOutLineTEXT_entity.dxftype() == 'TEXT' else CommBuaOutLineTEXT_entity.plain_text()
                    filtered_label = commbua_label.lower().replace(' ', '')
                    if filtered_label != "comm" and filtered_label != "commbua":
                        commbuaLabel_insert = commbuaLabelProperties.get('insert')

                        commbuaLabel_point = Point(np.array([commbuaLabel_insert[0], commbuaLabel_insert[1]]))

                        if CommBUAOutLine_polygon.contains(
                                commbuaLabel_point) or CommBUAOutLine_polygon.touches(
                            commbuaLabel_point) or round(
                            CommBUAOutLine_polygon.distance(commbuaLabel_point), 1) == 0.0:
                            CommBUAOutLine_Label = commbua_label

            CommBUAOutLine_dict[CommBUAOutLinePolygonID] = [CommBUAOutLine_entity, CommBUAOutLine_Label]

    return [ErrorCommBUAOutLine_dict, CommBUAOutLine_dict]

def SpecialBuaOutLine_Layer(SpecialBUAOutLine_data):
    SpecialBUAOutLine_dict = dict()

    ErrorSpecialBUAOutLine_dict = dict()

    unique_polygons = {}

    for SpecialBUAOutLine_entity in SpecialBUAOutLine_data:

        if SpecialBUAOutLine_entity.dxftype() == 'LWPOLYLINE' and SpecialBUAOutLine_entity.closed:

            SpecialBUAOutLinePolygonID = SpecialBUAOutLine_entity.dxf.handle

            vertices = tuple(SpecialBUAOutLine_entity.get_points())

            if vertices in unique_polygons:

                ErrorSpecialBUAOutLine_dict[SpecialBUAOutLinePolygonID] = str(
                    f"SpecialUseBUAOutline Layer Found Duplicate Polygon Of {SpecialBUAOutLinePolygonID}.")

            else:

                unique_polygons[vertices] = SpecialBUAOutLine_entity

            has_arc= any([entity.dxftype()=="ARC" for entity in SpecialBUAOutLine_entity.virtual_entities()])
            if has_arc:
                SpecialBUAOutLine_polygon = Polygon_Merger_ARC(SpecialBUAOutLine_entity)
            else:
                SpecialBUAOutLine_polygon = Polygon(
                    np.array([speup[0:2] for speup in SpecialBUAOutLine_entity.get_points()]))

            SpecialBUAOutLine_Label = "None"
            for SpecialBUAOutLineTEXT_entity in SpecialBUAOutLine_data:

                if SpecialBUAOutLineTEXT_entity.dxftype() == 'TEXT' or SpecialBUAOutLineTEXT_entity.dxftype() == 'MTEXT':

                    specialbuaLabelProperties = SpecialBUAOutLineTEXT_entity.dxfattribs()

                    specialbua_label = specialbuaLabelProperties.get(
                        'text') if SpecialBUAOutLineTEXT_entity.dxftype() == 'TEXT' else SpecialBUAOutLineTEXT_entity.plain_text()
                    filtered_label = specialbua_label.lower().replace(' ', '')
                    if filtered_label != "special" and filtered_label != "specialbua":
                        specialbuaLabel_insert = specialbuaLabelProperties.get('insert')

                        specialbuaLabel_point = Point(np.array([specialbuaLabel_insert[0], specialbuaLabel_insert[1]]))

                        if SpecialBUAOutLine_polygon.contains(
                                specialbuaLabel_point) or SpecialBUAOutLine_polygon.touches(
                            specialbuaLabel_point) or round(
                            SpecialBUAOutLine_polygon.distance(specialbuaLabel_point), 1) == 0.0:
                            SpecialBUAOutLine_Label = specialbua_label

            SpecialBUAOutLine_dict[SpecialBUAOutLinePolygonID] = [SpecialBUAOutLine_entity, SpecialBUAOutLine_Label]

    return [ErrorSpecialBUAOutLine_dict, SpecialBUAOutLine_dict]

def IndBuaOutLine_Layer(IndBUAOutLine_data):
    IndBUAOutLine_dict = dict()

    ErrorIndBUAOutLine_dict = dict()

    unique_polygons = {}

    for IndBUAOutLine_entity in IndBUAOutLine_data:

        if IndBUAOutLine_entity.dxftype() == 'LWPOLYLINE':

            IndBUAOutLinePolygonID = IndBUAOutLine_entity.dxf.handle

            vertices = tuple(IndBUAOutLine_entity.get_points())

            if vertices in unique_polygons:

                ErrorIndBUAOutLine_dict[IndBUAOutLinePolygonID] = str(
                    f"IndBUAOutline Layer Found Duplicate Polygon Of {IndBUAOutLinePolygonID}.")

            else:

                unique_polygons[vertices] = IndBUAOutLine_entity

            has_arc=any([entity.dxftype()=="ARC" for entity in IndBUAOutLine_entity.virtual_entities()])
            if has_arc:
                IndBUAOutLine_polygon = Polygon_Merger_ARC(IndBUAOutLine_entity)
            else:
                IndBUAOutLine_polygon = Polygon(np.array([indp[0:2] for indp in IndBUAOutLine_entity.get_points()]))

            IndBUAOutLine_Label = "None"
            for IndBUAOutLineTEXT_entity in IndBUAOutLine_data:

                if IndBUAOutLineTEXT_entity.dxftype() == 'TEXT' or IndBUAOutLineTEXT_entity.dxftype() == 'MTEXT':

                    indbuaLabelProperties = IndBUAOutLineTEXT_entity.dxfattribs()

                    indbua_label = indbuaLabelProperties.get('text') if IndBUAOutLineTEXT_entity.dxftype() == 'TEXT' else IndBUAOutLineTEXT_entity.plain_text()

                    filtered_label = indbua_label.lower().replace(' ', '')

                    if filtered_label != "ind" and filtered_label != "indbua":
                        indbuaLabel_insert = indbuaLabelProperties.get('insert')

                        indbuaLabel_point = Point(np.array([indbuaLabel_insert[0], indbuaLabel_insert[1]]))

                        if IndBUAOutLine_polygon.contains(indbuaLabel_point) or IndBUAOutLine_polygon.touches(indbuaLabel_point) or round(IndBUAOutLine_polygon.distance(indbuaLabel_point), 1) == 0.0:

                            IndBUAOutLine_Label = indbua_label

            IndBUAOutLine_dict[IndBUAOutLinePolygonID] = [IndBUAOutLine_entity, IndBUAOutLine_Label]

    return [ErrorIndBUAOutLine_dict, IndBUAOutLine_dict]

def check_resibua_and_commbua_tot_area(msp):  # (folder:str,filename:str):

    returnValueDict = dict()

    resultsList = []

    if (msp is None):  # (folder is None) or (filename is None):
        returnValueDict['code'] = 99
        msg = 'Required inputs of msp is missing for method check_resibua_and_commbua_tot_area. Modelspace ' + str(msp)
        returnValueDict['error'] = msg

        return returnValueDict

    # dxf_path=os.path.join(folder,filename)

    try:

        # read_dxf=ezdxf.readfile(dxf_path)

        # msp=read_dxf.modelspace()

        building_name_data = msp.query('*[layer=="_BuildingName"]')

        floor_data = msp.query('*[layer=="_Floor"]')

        resibua_data = msp.query('TEXT MTEXT LWPOLYLINE[layer=="_ResiBUAOutline"]')
        resibua_layer_data = ResiBuaOutLine_Layer(resibua_data)
        # print("resibua layer data:", resibua_layer_data)

        commbua_data = msp.query('TEXT MTEXT LWPOLYLINE[layer=="_CommBUAOutline"]')
        commbua_layer_data = CommBuaOutLine_Layer(commbua_data)
        # print("commbua layer data:", commbua_layer_data)

        indbua_data = msp.query('TEXT MTEXT LWPOLYLINE[layer=="_IndBUAOutline"]')
        indbua_layer_data = IndBuaOutLine_Layer(indbua_data)
        # print("indbua layer data:", indbua_layer_data)

        special_usebua_data = msp.query('TEXT MTEXT LWPOLYLINE[layer=="_SpecialUseBUAOutline"]')
        special_usebua_layer_data = SpecialBuaOutLine_Layer(special_usebua_data)
        # print("specialbua layer data:", special_usebua_layer_data)

        # terrace_polygon_data = msp.query('LWPOLYLINE[layer=="_Terrace"]')

        accessory_use_polygon_data = msp.query('LWPOLYLINE[layer=="_AccessoryUse"]')

        balcony_polygon_data = msp.query('LWPOLYLINE[layer=="_Balcony"]')

        ventilation_shaft_polygon_data = msp.query('LWPOLYLINE[layer=="_VentilationShaft"]')

        slab_cutout_void_polygon_data = msp.query('LWPOLYLINE[layer=="_SlabCutoutVoid"]')

        refuge_area_polygon_data = msp.query('LWPOLYLINE[layer=="_RefugeArea"]')

        lift_area_polygon_data = msp.query('LWPOLYLINE[layer=="_Lift"]')

        staircase_area_polygon_data = msp.query('LWPOLYLINE[layer=="_StairCase"]')

        Parking_data = msp.query('LWPOLYLINE[layer=="_Parking"]')

        # iterate building text from building_name_data

        for building_text in building_name_data:

            if building_text.dxftype() == 'TEXT' or building_text.dxftype() == 'MTEXT':

                dxf_attribs = building_text.dxfattribs()

                building_name = dxf_attribs.get('text',
                                                building_text.dxf.text) if building_text.dxftype() == 'TEXT' else building_text.text

                if building_name != '':

                    splited_building_name = DetermineBuildingNumbers(building_name.upper())

                    for building_text_name in splited_building_name:

                        text_insert_pts = building_text.dxf.insert

                        building_name_point = Point([text_insert_pts[0], text_insert_pts[1]])

                        # iterate building polygon from building_name_data

                        for building_polygon in building_name_data:

                            if building_polygon.dxftype() == 'LWPOLYLINE':

                                building_polygon_id = building_polygon.dxf.handle

                                building_polygon_pts = [bp[0:2] for bp in building_polygon.get_points()]

                                if len(building_polygon_pts) >= 3:

                                    building_polygon_points = Polygon(building_polygon_pts)

                                    # check building text in building polygon or not

                                    if building_polygon_points.contains(
                                            building_name_point) or building_polygon_points.touches(
                                            building_name_point) or round(
                                            building_polygon_points.distance(building_name_point)) == 0:

                                        rmvspace_building_name = building_text_name.replace(' ', '')

                                        stripbuilding_name = rmvspace_building_name.strip()

                                        # iterate floor text data from floor data

                                        for floor_text in floor_data:

                                            if floor_text.dxftype() == 'TEXT' or floor_text.dxftype() == 'MTEXT':

                                                floor_label_id = floor_text.dxf.handle

                                                floor_dxf_attribs = floor_text.dxfattribs()

                                                floor_name = floor_dxf_attribs.get('text',
                                                                                   floor_text.dxf.text) if floor_text.dxftype() == 'TEXT' else floor_text.text

                                                floor_text_name = floor_name.lower().replace(" ", "")

                                                # print(floor_text_name)

                                                if 'typical' in floor_text_name:

                                                    filter_typical_floor = determineFloorNumbers(floor_text_name)

                                                    for n1 in filter_typical_floor:
                                                        floor_text_insert_pts = floor_dxf_attribs.get('insert')
                                                        floor_text_point = Point([floor_text_insert_pts[0], floor_text_insert_pts[1]])
                                                        # iterate floor polygon data from floor data
                                                        for floor_polygon in floor_data:
                                                            if floor_polygon.dxftype() == 'LWPOLYLINE':
                                                                # floor_polygon_id=floor_polygon.dxf.handle
                                                                floor_polygon_pts = [fp[0:2] for fp in floor_polygon.get_points()]
                                                                if len(floor_polygon_pts) >= 3:
                                                                    floor_polygon_points = Polygon(floor_polygon_pts)

                                                                    # check floor text in floor polygon or not
                                                                    if floor_polygon_points.contains(floor_text_point) or floor_polygon_points.touches(floor_text_point) or round(floor_polygon_points.distance(floor_text_point)) == 0:
                                                                        # check floor polygon in building polygon or not
                                                                        if building_polygon_points.contains(floor_polygon_points) or building_polygon_points.touches(floor_polygon_points):
                                                                            # print(floor_text_name)
                                                                            floor_list = []
                                                                            parking_polygon_data = Parking_PolygonData(Parking_data, floor_polygon_points)

                                                                            if parking_polygon_data is not None:
                                                                                park_hasArc=any([entity.dxftype()=="ARC" for entity in parking_polygon_data.virtual_entities()])
                                                                                if park_hasArc:

                                                                                    parking_polygon_points = Polygon_Merger_ARC(parking_polygon_data)

                                                                                else:
                                                                                    parking_polygon_points = Polygon(
                                                                                        parking_polygon_data.get_points("xy"))

                                                                                parking_balcony_area_list = []
                                                                                parking_accessory_area_list = []
                                                                                parking_ventilation_area_list = []
                                                                                parking_slab_cutout_area_list = []
                                                                                parking_refuge_area_list = []
                                                                                parking_lift_area_list = []
                                                                                parking_staircase_area_list = []

                                                                                # iterate balcony polygon from balcony_polygon_data
                                                                                for balcony_polygon in balcony_polygon_data:

                                                                                    balcony_hasarc=any([entity.dxftype()=="ARC" for entity in balcony_polygon.virtual_entities()])

                                                                                    balcony_polygon_pts= balcony_polygon.get_points("xy")
                                                                                    if len(balcony_polygon_pts)<3:
                                                                                        continue

                                                                                    balcony_polygon_points=Polygon_Merger_ARC(balcony_polygon) if balcony_hasarc else Polygon(balcony_polygon_pts)

                                                                                    # check balcony polygon in resibua polygon or not
                                                                                    if parking_polygon_points.contains(balcony_polygon_points) or parking_polygon_points.touches(
                                                                                        balcony_polygon_points) or round(parking_polygon_points.distance(balcony_polygon_points)) == 0:
                                                                                        balcony_area = round(balcony_polygon_points.area,2)
                                                                                        parking_balcony_area_list.append(balcony_area)

                                                                                # iterate accessory polygon from accessory_use_polygon_data
                                                                                for accessory_polygon in accessory_use_polygon_data:

                                                                                    acc_hasarc=any([entity.dxftype()=="ARC" for entity in accessory_polygon.virtual_entities()])

                                                                                    accessory_polygon_pts= accessory_polygon.get_points("xy")
                                                                                    if len(accessory_polygon_pts)<3:
                                                                                        continue

                                                                                    accessory_polygon_points = Polygon_Merger_ARC(accessory_polygon) if acc_hasarc else Polygon(accessory_polygon_pts)
                                                                                    # check accessory polygon in resibua_polygon or not
                                                                                    if parking_polygon_points.contains(accessory_polygon_points):
                                                                                        accessory_area = round(accessory_polygon_points.area,2)
                                                                                        parking_accessory_area_list.append(accessory_area)

                                                                                # iterate ventilation polygon from ventilation_shaft_polygon_data
                                                                                for ventilation_polygon in ventilation_shaft_polygon_data:
                                                                                    venti_hasarc=any([entity.dxftype()=="ARC" for entity in ventilation_polygon.virtual_entities()])

                                                                                    ventilation_polygon_pts= ventilation_polygon.get_points("xy")
                                                                                    if len(ventilation_polygon_pts)<3:
                                                                                        continue

                                                                                    ventilation_polygon_points = Polygon_Merger_ARC(ventilation_polygon) if venti_hasarc else Polygon(ventilation_polygon_pts)
                                                                                    # check ventilation polygon in resibua polygon or not
                                                                                    if parking_polygon_points.contains(ventilation_polygon_points):
                                                                                        ventilation_area = round(ventilation_polygon_points.area,2)
                                                                                        parking_ventilation_area_list.append(ventilation_area)

                                                                                # iterate slabcutoutvoid polygon from slab_cutout_void_polygon_data
                                                                                for slab_cutout_void_polygon in slab_cutout_void_polygon_data:
                                                                                    slab_hasarc=any([entity.dxftype()=="ARC" for entity in slab_cutout_void_polygon.virtual_entities()])

                                                                                    slab_cutout_polygon_pts= slab_cutout_void_polygon.get_points(
                                                                                        "xy")
                                                                                    if len(slab_cutout_polygon_pts)<3:
                                                                                        continue
                                                                                    slab_cutout_polygon_points = Polygon_Merger_ARC(slab_cutout_void_polygon) if slab_hasarc else Polygon(slab_cutout_polygon_pts)

                                                                                    # check slabcutoutvoid polygon in resibua polygon or not
                                                                                    if parking_polygon_points.contains(slab_cutout_polygon_points):
                                                                                        slab_cutout_area = round(slab_cutout_polygon_points.area,2)
                                                                                        parking_slab_cutout_area_list.append(slab_cutout_area)

                                                                                # iterate refuge_polygon from refuge_area_polygon_data
                                                                                for refuge_polygon in refuge_area_polygon_data:
                                                                                    refuge_hasarc=any([entity.dxftype()=="ARC" for entity in refuge_polygon.virtual_entities()])

                                                                                    refuge_polygon_pts= refuge_polygon.get_points("xy")
                                                                                    if len(refuge_polygon_pts)<3:
                                                                                        continue

                                                                                    refuge_polygon_points = Polygon_Merger_ARC(refuge_polygon) if refuge_hasarc else Polygon(refuge_polygon_pts)
                                                                                    # check refuge polygon in resibua polygon or not
                                                                                    # if parking_polygon_points.contains(refuge_polygon_points):
                                                                                    if parking_polygon_points.contains(refuge_polygon_points) == True or parking_polygon_points.touches(refuge_polygon_points) == True or round(parking_polygon_points.distance(refuge_polygon_points),2) == 0.0:
                                                                                        refuge_area = round(refuge_polygon_points.area,2)
                                                                                        parking_refuge_area_list.append(refuge_area)

                                                                                # iterate lift polygon in lift_area_polygon_data
                                                                                for lift_polygon in lift_area_polygon_data:
                                                                                    lift_hasarc=any([entity.dxftype()=="ARC" for entity in lift_polygon.virtual_entities()])
                                                                                    lift_polygon_pts= lift_polygon.get_points("xy")
                                                                                    if len(lift_polygon_pts)<3:
                                                                                        continue
                                                                                    lift_polygon_points = Polygon_Merger_ARC(lift_polygon) if lift_hasarc else Polygon(lift_polygon_pts)
                                                                                    # check lift polygon in terrace polygon or not
                                                                                    if parking_polygon_points.contains(lift_polygon_points):
                                                                                        lift_area = round(lift_polygon_points.area,2)
                                                                                        parking_lift_area_list.append(lift_area)

                                                                                # iterate staircase polygon in staircase_area_polygon_data
                                                                                for staircase_polygon in staircase_area_polygon_data:

                                                                                    pts = staircase_polygon.get_points("xy")

                                                                                    if len(pts) <= 2 or not staircase_polygon.closed:
                                                                                        continue

                                                                                    stair_hasarc = any(entity.dxftype() == "ARC" for entity in staircase_polygon.virtual_entities())

                                                                                    staircase_polygon_points = (Polygon_Merger_ARC(staircase_polygon) if stair_hasarc else Polygon(pts))

                                                                                    if parking_polygon_points.contains(staircase_polygon_points):

                                                                                        staircase_area = round(staircase_polygon_points.area,2)

                                                                                        parking_staircase_area_list.append(staircase_area)

                                                                                # for staircase_polygon in staircase_area_polygon_data:
                                                                                #
                                                                                #     if len(staircase_polygon.get_points(
                                                                                #             "xy")) <= 2:
                                                                                #         continue
                                                                                #
                                                                                #     stair_hasarc=any([entity.dxftype()=="ARC" for entity in staircase_polygon.virtual_entities()])
                                                                                #
                                                                                #     staircase_polygon_points = Polygon_Merger_ARC(staircase_polygon) if stair_hasarc else Polygon(staircase_polygon.get_points("xy"))
                                                                                #     # check staircase polygon in terrace polygon or not
                                                                                #     if parking_polygon_points.contains(staircase_polygon_points):
                                                                                #         staircase_area = round(staircase_polygon_points.area,2)
                                                                                #         parking_staircase_area_list.append(staircase_area)

                                                                                np_sum_of_parking_balcony_area = np.sum(parking_balcony_area_list).round(2)
                                                                                np_sum_of_parking_accessory_area = np.sum(parking_accessory_area_list).round(2)
                                                                                np_sum_of_parking_ventilation_area = np.sum(parking_ventilation_area_list).round(2)
                                                                                np_sum_of_parking_slab_cutout_area = np.sum(parking_slab_cutout_area_list).round(2)
                                                                                np_sum_of_parking_refuge_area = np.sum(parking_refuge_area_list).round(2)
                                                                                np_sum_of_parking_lift_area = np.sum(parking_lift_area_list).round(2)
                                                                                np_sum_of_parking_staircase_area = np.sum(parking_staircase_area_list).round(2)

                                                                                parkdict = dict()
                                                                                parkdict['PARKING_ACCESSORY'] = str(np_sum_of_parking_accessory_area)
                                                                                parkdict['PARKING_BALCONY'] = str(np_sum_of_parking_balcony_area)
                                                                                parkdict['PARKING_VENTILATION_SHAFT'] = str(np_sum_of_parking_ventilation_area)
                                                                                parkdict['PARKING_SLAB_CUTOUT_VOID'] = str(np_sum_of_parking_slab_cutout_area)
                                                                                parkdict['PARKING_REFUSE_AREA'] = str(np_sum_of_parking_refuge_area)
                                                                                parkdict['PARKING_LIFT_AREA'] = str(np_sum_of_parking_lift_area)
                                                                                parkdict['PARKING_STAIRCASE_AREA'] = str(np_sum_of_parking_staircase_area)
                                                                                floor_list.append(parkdict)

                                                                            # iterate resibua polygon from resibua_polygon_data

                                                                            totresibua_balcony_area = 0.0
                                                                            totresibua_accessory_area = 0.0
                                                                            totresibua_ventilation_area = 0.0
                                                                            totresibua_slab_cutout_area = 0.0
                                                                            totresibua_refuge_area = 0.0
                                                                            totresibua_lift_area = 0.0
                                                                            totresibua_staircase_area = 0.0
                                                                            occupancy_label = None
                                                                            for resibua_polygon in resibua_layer_data[1].values():

                                                                                resi_hasarc=any([entity.dxftype()=="ARC" for entity in resibua_polygon[0].virtual_entities()])

                                                                                resibua_polygon_pts= resibua_polygon[0].get_points("xy")
                                                                                if len(resibua_polygon_pts)<3:
                                                                                    continue
                                                                                # polygon merge with arc
                                                                                resibua_polygon_points = Polygon_Merger_ARC(resibua_polygon[0]) if resi_hasarc else Polygon(resibua_polygon_pts)

                                                                                # check resibua polygon in floor polygon or not
                                                                                if floor_polygon_points.contains(resibua_polygon_points) or floor_polygon_points.touches(resibua_polygon_points) or round(floor_polygon_points.distance(resibua_polygon_points)) == 0:
                                                                                    resibua_balcony_area_list = []
                                                                                    resibua_accessory_area_list = []
                                                                                    resibua_ventilation_area_list = []
                                                                                    resibua_slab_cutout_area_list = []
                                                                                    resibua_refuge_area_list = []
                                                                                    resibua_lift_area_list = []
                                                                                    resibua_staircase_area_list = []

                                                                                    # iterate balcony polygon from balcony_polygon_data
                                                                                    for balcony_polygon in balcony_polygon_data:
                                                                                        balc_hasarc= any([entity.dxftype()=="ARC" for entity in balcony_polygon.virtual_entities()])
                                                                                        balcony_polygon_pts=balcony_polygon.get_points("xy")
                                                                                        if len(balcony_polygon_pts)<3:
                                                                                            continue

                                                                                        balcony_polygon_points = Polygon_Merger_ARC(balcony_polygon) if balc_hasarc else Polygon(balcony_polygon_pts)
                                                                                        # check balcony polygon in resibua polygon or not
                                                                                        if resibua_polygon_points.contains(balcony_polygon_points) or resibua_polygon_points.touches(balcony_polygon_points) or round(resibua_polygon_points.distance(balcony_polygon_points)) == 0:
                                                                                            balcony_area = round(balcony_polygon_points.area,2)
                                                                                            resibua_balcony_area_list.append(balcony_area)

                                                                                    # iterate accessory polygon from accessory_use_polygon_data
                                                                                    for accessory_polygon in accessory_use_polygon_data:
                                                                                        acce_hasarc= any([entity.dxftype()=="ARC" for entity in accessory_polygon.virtual_entities()])
                                                                                        accessory_polygon_pts=accessory_polygon.get_points(
                                                                                            "xy")
                                                                                        if len(accessory_polygon_pts)<3:
                                                                                            continue
                                                                                        accessory_polygon_points = Polygon_Merger_ARC(accessory_polygon) if acce_hasarc else Polygon(accessory_polygon_pts)
                                                                                        # check accessory polygon in resibua_polygon or not
                                                                                        if resibua_polygon_points.contains(accessory_polygon_points):
                                                                                            accessory_area = round(accessory_polygon_points.area,2)
                                                                                            resibua_accessory_area_list.append(accessory_area)

                                                                                    # iterate ventilation polygon from ventilation_shaft_polygon_data
                                                                                    for ventilation_polygon in ventilation_shaft_polygon_data:

                                                                                        venti_hasarc=any([entity.dxftype()=="ARC" for entity in ventilation_polygon.virtual_entities()])
                                                                                        ventilation_polygon_pts= ventilation_polygon.get_points(
                                                                                            "xy")
                                                                                        if len(ventilation_polygon_pts)<3:
                                                                                            continue

                                                                                        ventilation_polygon_points = Polygon_Merger_ARC(
                                                                                            ventilation_polygon) if venti_hasarc else Polygon(ventilation_polygon_pts)
                                                                                        # check ventilation polygon in resibua polygon or not
                                                                                        if resibua_polygon_points.contains(ventilation_polygon_points):
                                                                                            ventilation_area = round(ventilation_polygon_points.area,2)
                                                                                            resibua_ventilation_area_list.append(ventilation_area)

                                                                                    # iterate slabcutoutvoid polygon from slab_cutout_void_polygon_data
                                                                                    for slab_cutout_void_polygon in slab_cutout_void_polygon_data:
                                                                                        slab_hasarc=any([entity.dxftype()=="ARC" for entity in slab_cutout_void_polygon.virtual_entities()])

                                                                                        slab_cutout_polygon_pts= slab_cutout_void_polygon.get_points(
                                                                                            "xy")
                                                                                        if len(slab_cutout_polygon_pts)<3:
                                                                                            continue

                                                                                        slab_cutout_polygon_points = Polygon_Merger_ARC(slab_cutout_void_polygon) if slab_hasarc else Polygon(slab_cutout_polygon_pts)
                                                                                        # check slabcutoutvoid polygon in resibua polygon or not
                                                                                        if resibua_polygon_points.contains(slab_cutout_polygon_points):
                                                                                            slab_cutout_area = round(slab_cutout_polygon_points.area, 2)
                                                                                            resibua_slab_cutout_area_list.append(slab_cutout_area)

                                                                                    # iterate refuge_polygon from refuge_area_polygon_data

                                                                                    for refuge_polygon in refuge_area_polygon_data:
                                                                                        refuge_hasarc= any([entity.dxftype()=="ARC" for entity in refuge_polygon.virtual_entities()])

                                                                                        refuge_polygon_pts= refuge_polygon.get_points("xy")
                                                                                        if len(refuge_polygon_pts)<3:
                                                                                            continue

                                                                                        refuge_polygon_points = Polygon_Merger_ARC(refuge_polygon) if refuge_hasarc else Polygon(refuge_polygon_pts)
                                                                                        # check refuge polygon in resibua polygon or not
                                                                                        # if resibua_polygon_points.contains(refuge_polygon_points):
                                                                                        if resibua_polygon_points.contains(refuge_polygon_points) == True or resibua_polygon_points.touches(refuge_polygon_points) == True or round(resibua_polygon_points.distance(refuge_polygon_points),2) == 0.0:
                                                                                            refuge_area = round(refuge_polygon_points.area,2)
                                                                                            resibua_refuge_area_list.append(refuge_area)

                                                                                    # iterate lift polygon in lift_area_polygon_data
                                                                                    for lift_polygon in lift_area_polygon_data:
                                                                                        lift_hasarc= any([entity.dxftype()=="ARC" for entity in lift_polygon.virtual_entities()])

                                                                                        lift_polygon_pts=lift_polygon.get_points("xy")
                                                                                        if len(lift_polygon_pts)<3:
                                                                                            continue

                                                                                        lift_polygon_points = Polygon_Merger_ARC(lift_polygon) if lift_hasarc else Polygon(lift_polygon_pts)
                                                                                        # check lift polygon in terrace polygon or not
                                                                                        if resibua_polygon_points.contains(lift_polygon_points):
                                                                                            lift_area = round(lift_polygon_points.area,2)
                                                                                            resibua_lift_area_list.append(lift_area)

                                                                                    # iterate staircase polygon in staircase_area_polygon_data
                                                                                    for staircase_polygon in staircase_area_polygon_data:

                                                                                        pts = staircase_polygon.get_points("xy")


                                                                                        if len(pts) <= 2 or not staircase_polygon.closed:
                                                                                            continue

                                                                                        stair_hasarc = any(entity.dxftype() == "ARC" for entity in staircase_polygon.virtual_entities())

                                                                                        staircase_polygon_points = (Polygon_Merger_ARC(staircase_polygon) if stair_hasarc else Polygon(pts))


                                                                                        # if len(staircase_polygon.get_points(
                                                                                        #         "xy")) <= 2:
                                                                                        #     continue
                                                                                        #
                                                                                        # stair_hasarc= any([entity.dxftype()=="ARC" for entity in staircase_polygon.virtual_entities()])
                                                                                        #
                                                                                        # staircase_polygon_points = Polygon_Merger_ARC(staircase_polygon) if stair_hasarc else Polygon(staircase_polygon.get_points("xy"))
                                                                                        # check staircase polygon in terrace polygon or not
                                                                                        if resibua_polygon_points.contains(staircase_polygon_points):
                                                                                            staircase_area = round(staircase_polygon_points.area,2)
                                                                                            resibua_staircase_area_list.append(staircase_area)

                                                                                    totresibua_balcony_area += np.sum(resibua_balcony_area_list).round(2)
                                                                                    totresibua_accessory_area += np.sum(resibua_accessory_area_list).round(2)
                                                                                    totresibua_ventilation_area += np.sum(resibua_ventilation_area_list).round(2)
                                                                                    totresibua_slab_cutout_area += np.sum(resibua_slab_cutout_area_list).round(2)
                                                                                    totresibua_refuge_area += np.sum(resibua_refuge_area_list).round(2)
                                                                                    totresibua_lift_area += np.sum(resibua_lift_area_list).round(2)
                                                                                    totresibua_staircase_area += np.sum(resibua_staircase_area_list).round(2)
                                                                                    occupancy_label = resibua_polygon[1]

                                                                            if any([
                                                                                totresibua_accessory_area,
                                                                                totresibua_balcony_area,
                                                                                totresibua_ventilation_area,
                                                                                totresibua_slab_cutout_area,
                                                                                totresibua_refuge_area,
                                                                                totresibua_lift_area,
                                                                                totresibua_staircase_area
                                                                            ]):
                                                                                residict = dict()
                                                                                residict['RESIBUA_OCCUPANCY_TYPE'] = occupancy_label
                                                                                residict['RESIBUA_ACCESSORY'] = str(round(totresibua_accessory_area, 2))
                                                                                residict['RESIBUA_BALCONY'] = str(round(totresibua_balcony_area, 2))
                                                                                residict['RESIBUA_VENTILATION_SHAFT'] = str(round(totresibua_ventilation_area,2))
                                                                                residict['RESIBUA_SLAB_CUTOUT_VOID'] = str(round(totresibua_slab_cutout_area,2))
                                                                                residict['RESIBUA_REFUSE_AREA'] = str(round(totresibua_refuge_area, 2))
                                                                                residict['RESIBUA_LIFT_AREA'] = str(round(totresibua_lift_area, 2))
                                                                                residict['RESIBUA_STAIRCASE_AREA'] = str(round(totresibua_staircase_area, 2))
                                                                                floor_list.append(residict)

                                                                            # iterate commbua polygon from commbua_polygon_data
                                                                            totcommbua_balcony_area = 0.0
                                                                            totcommbua_accessory_area = 0.0
                                                                            totcommbua_ventilation_area = 0.0
                                                                            totcommbua_slab_cutout_area = 0.0
                                                                            totcommbua_refuge_area = 0.0
                                                                            totcommbua_lift_area = 0.0
                                                                            totcommbua_staircase_area = 0.0
                                                                            occupancy_label = None

                                                                            for commbua_polygon in commbua_layer_data[1].values():
                                                                                # polygon merge with arc
                                                                                commbua_hasarc=any([entity.dxftype()=="ARC" for entity in commbua_polygon[0].virtual_entities()])

                                                                                commbua_polygon_pts= commbua_polygon[0].get_points("xy")
                                                                                if len(commbua_polygon_pts)<3:
                                                                                    continue

                                                                                commbua_polygon_points = Polygon_Merger_ARC(commbua_polygon[0]) if commbua_hasarc else Polygon(commbua_polygon_pts)

                                                                                # check commbua polygon in floor polygon or not

                                                                                if floor_polygon_points.contains(commbua_polygon_points) or floor_polygon_points.touches(commbua_polygon_points) or round(floor_polygon_points.distance(commbua_polygon_points)) == 0:

                                                                                    commbua_balcony_area_list = []
                                                                                    commbua_accessory_area_list = []
                                                                                    commbua_ventilation_area_list = []
                                                                                    commbua_slab_cutout_area_list = []
                                                                                    commbua_refuge_area_list = []
                                                                                    commbua_lift_area_list = []
                                                                                    commbua_staircase_area_list = []

                                                                                    # iterate balcony polygon from balcony_polygon_data
                                                                                    for balcony_polygon in balcony_polygon_data:
                                                                                        balc_hasarc= any([entity.dxftype()=="ARC" for entity in balcony_polygon.virtual_entities()])

                                                                                        balcony_polygon_pts=balcony_polygon.get_points("xy")
                                                                                        if len(balcony_polygon_pts)<3:
                                                                                            continue

                                                                                        balcony_polygon_points = Polygon_Merger_ARC(balcony_polygon) if balc_hasarc else Polygon(balcony_polygon_pts)
                                                                                        # check balcony polygon in commbua polygon or not
                                                                                        if commbua_polygon_points.contains(balcony_polygon_points) or commbua_polygon_points.touches(balcony_polygon_points) or round(commbua_polygon_points.distance(balcony_polygon_points)) == 0:
                                                                                            balcony_area = round(balcony_polygon_points.area,2)
                                                                                            commbua_balcony_area_list.append(balcony_area)

                                                                                    # iterate accessory polygon from accessory_use_polygon_data
                                                                                    for accessory_polygon in accessory_use_polygon_data:
                                                                                        acce_hasarc=any([entity.dxftype()=="ARC" for entity in accessory_polygon.virtual_entities()])

                                                                                        accessory_polygon_pts= accessory_polygon.get_points(
                                                                                            "xy")
                                                                                        if len(accessory_polygon_pts)<3:
                                                                                            continue

                                                                                        accessory_polygon_points = Polygon_Merger_ARC(accessory_polygon) if acce_hasarc else Polygon(accessory_polygon_pts)
                                                                                        # check accessory polygon in commbua_polygon or not
                                                                                        if commbua_polygon_points.contains(accessory_polygon_points):
                                                                                            accessory_area = round(accessory_polygon_points.area,2)
                                                                                            commbua_accessory_area_list.append(accessory_area)

                                                                                    # iterate ventilation polygon from ventilation_shaft_polygon_data

                                                                                    for ventilation_polygon in ventilation_shaft_polygon_data:
                                                                                        venti_hasarc= any([entity.dxftype()=="ARC" for entity in ventilation_polygon.virtual_entities()])

                                                                                        ventilation_polygon_pts=ventilation_polygon.get_points(
                                                                                            "xy")
                                                                                        if len(ventilation_polygon_pts)<3:
                                                                                            continue

                                                                                        ventilation_polygon_points = Polygon_Merger_ARC(ventilation_polygon) if venti_hasarc else Polygon(ventilation_polygon_pts)
                                                                                        # check ventilation polygon in commbua polygon or not
                                                                                        if commbua_polygon_points.contains(ventilation_polygon_points):
                                                                                            ventilation_area = round(ventilation_polygon_points.area,2)
                                                                                            commbua_ventilation_area_list.append(ventilation_area)

                                                                                    # iterate slabcutoutvoid polygon from slab_cutout_void_polygon_data
                                                                                    for slab_cutout_void_polygon in slab_cutout_void_polygon_data:
                                                                                        slab_hasarc= any([entity.dxftype()=="ARC" for entity in slab_cutout_void_polygon.virtual_entities()])

                                                                                        slab_cutout_polygon_pts=slab_cutout_void_polygon.get_points(
                                                                                            "xy")
                                                                                        if len(slab_cutout_polygon_pts)<3:
                                                                                            continue

                                                                                        slab_cutout_polygon_points = Polygon_Merger_ARC(slab_cutout_void_polygon) if slab_hasarc else Polygon(slab_cutout_polygon_pts)
                                                                                        # check slabcutoutvoid polygon in commbua polygon or not
                                                                                        if commbua_polygon_points.contains(slab_cutout_polygon_points):
                                                                                            slab_cutout_area = round(slab_cutout_polygon_points.area,2)
                                                                                            commbua_slab_cutout_area_list.append(slab_cutout_area)

                                                                                    # iterate refuge polygon in refuge_area_polygon_data
                                                                                    for refuge_polygon in refuge_area_polygon_data:
                                                                                        refuge_hasarc= any([entity.dxftype()=="ARC" for entity in refuge_polygon.virtual_entities()])
                                                                                        refuge_polygon_pts=refuge_polygon.get_points("xy")
                                                                                        if len(refuge_polygon_pts)<3:
                                                                                            continue
                                                                                        refuge_polygon_points = Polygon_Merger_ARC(refuge_polygon) if refuge_hasarc else Polygon(refuge_polygon_pts)
                                                                                        # check refuge polygon in commbua polygon or not
                                                                                        # if commbua_polygon_points.contains(refuge_polygon_points):
                                                                                        if commbua_polygon_points.contains(refuge_polygon_points) == True or commbua_polygon_points.touches(refuge_polygon_points) == True or round(
                                                                                            commbua_polygon_points.distance(refuge_polygon_points),2) == 0.0:
                                                                                            refuge_area = round(refuge_polygon_points.area,2)
                                                                                            commbua_refuge_area_list.append(refuge_area)

                                                                                    # iterate lift polygon in lift_area_polygon_data
                                                                                    for lift_polygon in lift_area_polygon_data:
                                                                                        lift_hasarc=any([entity.dxftype()=="ARC" for entity in lift_polygon.virtual_entities()])
                                                                                        lift_polygon_pts= lift_polygon.get_points("xy")
                                                                                        if len(lift_polygon_pts)<3:
                                                                                            continue

                                                                                        lift_polygon_points = Polygon_Merger_ARC(lift_polygon) if lift_hasarc else Polygon(lift_polygon_pts)
                                                                                        # check lift polygon in terrace polygon or not
                                                                                        if commbua_polygon_points.contains(lift_polygon_points):
                                                                                            lift_area = round(lift_polygon_points.area,2)
                                                                                            commbua_lift_area_list.append(lift_area)

                                                                                    # iterate staircase polygon in staircase_area_polygon_data
                                                                                    for staircase_polygon in staircase_area_polygon_data:
                                                                                        pts = staircase_polygon.get_points(
                                                                                            "xy")

                                                                                        if len(pts) <= 2 or not staircase_polygon.closed:
                                                                                            continue

                                                                                        stair_hasarc = any(
                                                                                            entity.dxftype() == "ARC"
                                                                                            for entity in
                                                                                            staircase_polygon.virtual_entities())

                                                                                        staircase_polygon_points = (
                                                                                            Polygon_Merger_ARC(
                                                                                                staircase_polygon) if stair_hasarc else Polygon(
                                                                                                pts))

                                                                                        # if len(staircase_polygon.get_points(
                                                                                        #         "xy")) <= 2:
                                                                                        #     continue
                                                                                        #
                                                                                        # stair_hasarc= any([entity.dxftype()=="ARC" for entity in staircase_polygon.virtual_entities()])
                                                                                        # staircase_polygon_points = Polygon_Merger_ARC(staircase_polygon) if stair_hasarc else Polygon(staircase_polygon.get_points("xy"))
                                                                                        # check staircase polygon in terrace polygon or not
                                                                                        if commbua_polygon_points.contains(staircase_polygon_points):
                                                                                            staircase_area = round(staircase_polygon_points.area,2)
                                                                                            commbua_staircase_area_list.append(staircase_area)

                                                                                    totcommbua_balcony_area += np.sum(commbua_balcony_area_list).round(2)
                                                                                    totcommbua_accessory_area += np.sum(commbua_accessory_area_list).round(2)
                                                                                    totcommbua_ventilation_area += np.sum(commbua_ventilation_area_list).round(2)
                                                                                    totcommbua_slab_cutout_area += np.sum(commbua_slab_cutout_area_list).round(2)
                                                                                    totcommbua_refuge_area += np.sum(commbua_refuge_area_list).round(2)
                                                                                    totcommbua_lift_area += np.sum(commbua_lift_area_list).round(2)
                                                                                    totcommbua_staircase_area += np.sum(commbua_staircase_area_list).round(2)
                                                                                    occupancy_label = commbua_polygon[1]

                                                                            if any([
                                                                                totcommbua_balcony_area,
                                                                                totcommbua_accessory_area,
                                                                                totcommbua_ventilation_area,
                                                                                totcommbua_slab_cutout_area,
                                                                                totcommbua_refuge_area,
                                                                                totcommbua_lift_area,
                                                                                totcommbua_staircase_area
                                                                            ]):
                                                                                commdict = dict()
                                                                                commdict['COMMBUA_OCCUPANCY_TYPE'] = occupancy_label
                                                                                commdict['COMMBUA_ACCESSORY'] = str(round(totcommbua_accessory_area, 2))
                                                                                commdict['COMMBUA_BALCONY'] = str(round(totcommbua_balcony_area, 2))
                                                                                commdict['COMMBUA_VENTILATION_SHAFT'] = str(round(totcommbua_ventilation_area, 2))
                                                                                commdict['COMMBUA_SLAB_CUTOUT_VOID'] = str(round(totcommbua_slab_cutout_area,2))
                                                                                commdict['COMMBUA_REFUSE_AREA'] = str(round(totcommbua_refuge_area, 2))
                                                                                commdict['COMMBUA_LIFT_AREA'] = str(round(totcommbua_lift_area, 2))
                                                                                commdict['COMMBUA_STAIRCASE_AREA'] = str(round(totcommbua_staircase_area, 2))
                                                                                floor_list.append(commdict)

                                                                            # iterate indbua polygon in indbua_polygon_data
                                                                            totindbua_balcony_area = 0.0
                                                                            totindbua_accessory_area = 0.0
                                                                            totindbua_ventilation_area = 0.0
                                                                            totindbua_slab_cutout_area = 0.0
                                                                            totindbua_refuge_area = 0.0
                                                                            totindbua_lift_area = 0.0
                                                                            totindbua_staircase_area = 0.0
                                                                            occupancy_label = None

                                                                            for indbua_polygon in indbua_layer_data[1].values():
                                                                                indbua_hasarc = any(
                                                                                    [entity.dxftype() == "ARC" for
                                                                                     entity in indbua_polygon[0].virtual_entities()])

                                                                                indbua_polygon_pts= indbua_polygon[0].get_points("xy")
                                                                                if len(indbua_polygon_pts)<3:
                                                                                    continue
                                                                                # polygon merge with arc
                                                                                indbua_polygon_points = Polygon_Merger_ARC(indbua_polygon[0]) if indbua_hasarc else Polygon(indbua_polygon_pts
                                                                                    )
                                                                                # check indbua polygon in floor polygon or not
                                                                                if floor_polygon_points.contains(indbua_polygon_points) == True or floor_polygon_points.touches(indbua_polygon_points) == True or round(floor_polygon_points.distance(indbua_polygon_points)) == 0:

                                                                                    indbua_balcony_area_list = []
                                                                                    indbua_accessory_area_list = []
                                                                                    indbua_ventilation_area_list = []
                                                                                    indabua_slab_cutout_area_list = []
                                                                                    indbua_refuge_area_list = []
                                                                                    indbua_lift_area_list = []
                                                                                    indbua_staircase_area_list = []

                                                                                    # iterate balcony polygon from balcony_polygon_data
                                                                                    for balcony_polygon in balcony_polygon_data:

                                                                                        balc_hasarc = any(
                                                                                            [entity.dxftype() == "ARC"
                                                                                             for
                                                                                             entity in balcony_polygon.virtual_entities()])

                                                                                        # polygon merge with arc

                                                                                        balcony_polygon_pts=balcony_polygon.get_points("xy")
                                                                                        if len(balcony_polygon_pts)<3:
                                                                                            continue

                                                                                        balcony_polygon_points = Polygon_Merger_ARC(balcony_polygon) if balc_hasarc else Polygon(balcony_polygon_pts)
                                                                                        # check balcony polygon in indbua polygon or not
                                                                                        if indbua_polygon_points.contains(balcony_polygon_points) or indbua_polygon_points.touches(balcony_polygon_points) or round(indbua_polygon_points.distance(balcony_polygon_points)) == 0:
                                                                                            balcony_area = round(balcony_polygon_points.area,2)
                                                                                            indbua_balcony_area_list.append(balcony_area)

                                                                                    # iterate accessory polygon from accessory_use_polygon_data
                                                                                    for accessory_polygon in accessory_use_polygon_data:

                                                                                        acc_hasarc = any(
                                                                                            [entity.dxftype() == "ARC"
                                                                                             for
                                                                                             entity in accessory_polygon.virtual_entities()])

                                                                                        accessory_polygon_pts=accessory_polygon.get_points(
                                                                                            "xy")
                                                                                        if len(accessory_polygon_pts)<3:
                                                                                            continue

                                                                                        accessory_polygon_points = Polygon_Merger_ARC(accessory_polygon) if acc_hasarc else Polygon(accessory_polygon_pts)
                                                                                        # check accessory polygon in indabua_polygon or not
                                                                                        if indbua_polygon_points.contains(accessory_polygon_points):
                                                                                            accessory_area = round(accessory_polygon_points.area,2)
                                                                                            indbua_accessory_area_list.append(accessory_area)

                                                                                    # iterate ventilation polygon from ventilation_shaft_polygon_data
                                                                                    for ventilation_polygon in ventilation_shaft_polygon_data:

                                                                                        venti_hasarc = any(
                                                                                            [entity.dxftype() == "ARC"
                                                                                             for
                                                                                             entity in
                                                                                             ventilation_polygon.virtual_entities()])

                                                                                        ventilation_polygon_pts= ventilation_polygon.get_points(
                                                                                            "xy")
                                                                                        if len(ventilation_polygon_pts)<3:
                                                                                            continue

                                                                                        ventilation_polygon_points = Polygon_Merger_ARC(ventilation_polygon) if venti_hasarc else Polygon(ventilation_polygon_pts)
                                                                                        # check ventilation polygon in indbua polygon or not
                                                                                        if indbua_polygon_points.contains(ventilation_polygon_points):
                                                                                            ventilation_area = round(ventilation_polygon_points.area,2)
                                                                                            indbua_ventilation_area_list.append(ventilation_area)

                                                                                    # iterate slabcutoutvoid polygon from slab_cutout_void_polygon_data

                                                                                    for slab_cutout_void_polygon in slab_cutout_void_polygon_data:
                                                                                        slab_hasarc = any(
                                                                                            [entity.dxftype() == "ARC"
                                                                                             for
                                                                                             entity in
                                                                                             slab_cutout_void_polygon.virtual_entities()])

                                                                                        slab_cutout_polygon_pts=slab_cutout_void_polygon.get_points(
                                                                                            "xy")
                                                                                        if len(slab_cutout_polygon_pts)<3:
                                                                                            continue

                                                                                        slab_cutout_polygon_points = Polygon_Merger_ARC(slab_cutout_void_polygon) if slab_hasarc else Polygon(slab_cutout_polygon_pts)
                                                                                        # check slabcutoutvoid polygon in indbua polygon or not
                                                                                        if indbua_polygon_points.contains(slab_cutout_polygon_points):
                                                                                            slab_cutout_area = round(slab_cutout_polygon_points.area,2)
                                                                                            indabua_slab_cutout_area_list.append(slab_cutout_area)

                                                                                    # iterate refuge polygon in refuge_area_polygon_data
                                                                                    for refuge_polygon in refuge_area_polygon_data:

                                                                                        refuge_hasarc = any(
                                                                                            [entity.dxftype() == "ARC"
                                                                                             for
                                                                                             entity in
                                                                                             refuge_polygon.virtual_entities()])

                                                                                        refuge_polygon_pts=refuge_polygon.get_points("xy")
                                                                                        if len(refuge_polygon_pts)<3:
                                                                                            continue

                                                                                        refuge_polygon_points = Polygon_Merger_ARC(refuge_polygon) if refuge_hasarc else Polygon(refuge_polygon_pts)
                                                                                        # check refuge polygon in indbua polygon or not
                                                                                        # if indbua_polygon_points.contains(refuge_polygon_points):
                                                                                        if indbua_polygon_points.contains(refuge_polygon_points) == True or indbua_polygon_points.touches(
                                                                                            refuge_polygon_points) == True or round(indbua_polygon_points.distance(refuge_polygon_points),2) == 0.0:
                                                                                            refuge_area = round(refuge_polygon_points.area,2)
                                                                                            indbua_refuge_area_list.append(refuge_area)

                                                                                    # iterate lift polygon in lift_area_polygon_data
                                                                                    for lift_polygon in lift_area_polygon_data:

                                                                                        lift_hasarc = any(
                                                                                            [entity.dxftype() == "ARC"
                                                                                             for
                                                                                             entity in
                                                                                             lift_polygon.virtual_entities()])
                                                                                        lift_polygon_pts= lift_polygon.get_pints("xy")
                                                                                        if len(lift_polygon_pts)<3:
                                                                                            continue
                                                                                        lift_polygon_points = Polygon_Merger_ARC(lift_polygon) if lift_hasarc else Polygon(lift_polygon_pts)
                                                                                        # check lift polygon in terrace polygon or not
                                                                                        if indbua_polygon_points.contains(lift_polygon_points):
                                                                                            lift_area = round(lift_polygon_points.area,2)
                                                                                            indbua_lift_area_list.append(lift_area)

                                                                                    # iterate staircase polygon in staircase_area_polygon_data
                                                                                    for staircase_polygon in staircase_area_polygon_data:
                                                                                        pts = staircase_polygon.get_points(
                                                                                            "xy")

                                                                                        if len(pts) <= 2 or not staircase_polygon.closed:
                                                                                            continue

                                                                                        stair_hasarc = any(
                                                                                            entity.dxftype() == "ARC"
                                                                                            for entity in
                                                                                            staircase_polygon.virtual_entities())

                                                                                        staircase_polygon_points = (
                                                                                            Polygon_Merger_ARC(
                                                                                                staircase_polygon) if stair_hasarc else Polygon(
                                                                                                pts))

                                                                                        # if len(staircase_polygon.get_points(
                                                                                        #         "xy")) <= 2:
                                                                                        #     continue
                                                                                        #
                                                                                        # stair_hasarc = any(
                                                                                        #     [entity.dxftype() == "ARC"
                                                                                        #      for
                                                                                        #      entity in
                                                                                        #      staircase_polygon.virtual_entities()])
                                                                                        #
                                                                                        # staircase_polygon_points = Polygon_Merger_ARC(staircase_polygon) if stair_hasarc else Polygon(staircase_polygon.get_points("xy"))
                                                                                        # check staircase polygon in terrace polygon or not
                                                                                        if indbua_polygon_points.contains(staircase_polygon_points):
                                                                                            staircase_area = round(staircase_polygon_points.area,2)
                                                                                            indbua_staircase_area_list.append(staircase_area)

                                                                                    totindbua_balcony_area += np.sum(indbua_balcony_area_list).round(2)
                                                                                    totindbua_accessory_area += np.sum(indbua_accessory_area_list).round(2)
                                                                                    totindbua_ventilation_area += np.sum(indbua_ventilation_area_list).round(2)
                                                                                    totindbua_slab_cutout_area += np.sum(indabua_slab_cutout_area_list).round(2)
                                                                                    totindbua_refuge_area += np.sum(indbua_refuge_area_list).round(2)
                                                                                    totindbua_lift_area += np.sum(indbua_lift_area_list).round(2)
                                                                                    totindbua_staircase_area += np.sum(indbua_staircase_area_list).round(2)
                                                                                    occupancy_label = indbua_polygon[1]

                                                                            if any([
                                                                                totindbua_balcony_area,
                                                                                totindbua_accessory_area,
                                                                                totindbua_ventilation_area,
                                                                                totindbua_slab_cutout_area,
                                                                                totindbua_refuge_area,
                                                                                totindbua_lift_area,
                                                                                totindbua_staircase_area
                                                                            ]):
                                                                                inddict = dict()
                                                                                inddict['INDBUA_OCCUPANCY_TYPE'] = occupancy_label
                                                                                inddict['INDBUA_ACCESSORY'] = str(round(totindbua_accessory_area, 2))
                                                                                inddict['INDBUA_BALCONY'] = str(round(totindbua_balcony_area, 2))
                                                                                inddict['INDBUA_VENTILATION_SHAFT'] = str(round(totindbua_ventilation_area,2))
                                                                                inddict['INDBUA_SLAB_CUTOUT_VOID'] = str(round(totindbua_slab_cutout_area,2))
                                                                                inddict['INDBUA_REFUSE_AREA'] = str(round(totindbua_refuge_area, 2))
                                                                                inddict['INDBUA_LIFT_AREA'] = str(round(totindbua_lift_area, 2))
                                                                                inddict['INDBUA_STAIRCASE_AREA'] = str(round(totindbua_staircase_area, 2))
                                                                                floor_list.append(inddict)

                                                                            # iterate special_usebua polygon in special_usebua_polygon_data

                                                                            totsplbua_balcony_area = 0.0
                                                                            totsplbua_accessory_area = 0.0
                                                                            totsplbua_ventilation_area = 0.0
                                                                            totsplbua_slab_cutout_area = 0.0
                                                                            totsplbua_refuge_area = 0.0
                                                                            totsplbua_lift_area = 0.0
                                                                            totsplbua_staircase_area = 0.0
                                                                            occupancy_label = None

                                                                            for special_usebua_polygon in special_usebua_layer_data[1].values():

                                                                                special_hasarc = any(
                                                                                    [entity.dxftype() == "ARC"
                                                                                     for
                                                                                     entity in
                                                                                     special_usebua_polygon[0].virtual_entities()])

                                                                                special_usebua_polygon_pts=special_usebua_polygon[0].get_points("xy")
                                                                                if len(special_usebua_polygon_pts)<3:
                                                                                    continue
                                                                                # polygon merge with arc
                                                                                special_usebua_polygon_points = Polygon_Merger_ARC(special_usebua_polygon[0]) if special_hasarc else Polygon(special_usebua_polygon_pts)
                                                                                # check indbua polygon in floor polygon or not

                                                                                if floor_polygon_points.contains(special_usebua_polygon_points) or floor_polygon_points.touches(special_usebua_polygon_points) or round(floor_polygon_points.distance(special_usebua_polygon_points)) == 0:
                                                                                    special_usebua_balcony_area_list = []
                                                                                    special_usebua_accessory_area_list = []
                                                                                    special_usebua_ventilation_area_list = []
                                                                                    special_usebua_slab_cutout_area_list = []
                                                                                    special_usebua_refuge_area_list = []
                                                                                    special_usebua_lift_area_list = []
                                                                                    special_usebua_staircase_area_list = []

                                                                                    # iterate balcony polygon from balcony_polygon_data
                                                                                    for balcony_polygon in balcony_polygon_data:

                                                                                        balc_hasarc = any(
                                                                                            [entity.dxftype() == "ARC"
                                                                                             for
                                                                                             entity in
                                                                                             balcony_polygon.virtual_entities()])

                                                                                        balcony_polygon_pts=balcony_polygon.get_points("xy")
                                                                                        if len(balcony_polygon_pts)<3:
                                                                                            continue

                                                                                        balcony_polygon_points = Polygon_Merger_ARC(balcony_polygon) if balc_hasarc else Polygon(balcony_polygon_pts)
                                                                                        # check balcony polygon in special usebua polygon or not
                                                                                        if special_usebua_polygon_points.contains(balcony_polygon_points) or special_usebua_polygon_points.touches(balcony_polygon_points) or round(special_usebua_polygon_points.distance(balcony_polygon_points)) == 0:
                                                                                            balcony_area = round(balcony_polygon_points.area,2)
                                                                                            special_usebua_balcony_area_list.append(balcony_area)

                                                                                    # iterate accessory polygon from accessory_use_polygon_data
                                                                                    for accessory_polygon in accessory_use_polygon_data:

                                                                                        acc_hasarc = any(
                                                                                            [entity.dxftype() == "ARC"
                                                                                             for
                                                                                             entity in
                                                                                             accessory_polygon.virtual_entities()])

                                                                                        accessory_polygon_pts= accessory_polygon.get_points(
                                                                                            "xy")
                                                                                        if len(accessory_polygon_pts)<3:
                                                                                            continue

                                                                                        accessory_polygon_points = Polygon_Merger_ARC(accessory_polygon) if acc_hasarc else Polygon(accessory_polygon_pts)
                                                                                        # check accessory polygon in special_usebua_polygon or not
                                                                                        if special_usebua_polygon_points.contains(accessory_polygon_points):
                                                                                            accessory_area = round(accessory_polygon_points.area,2)
                                                                                            special_usebua_accessory_area_list.append(accessory_area)

                                                                                    # iterate ventilation polygon from ventilation_shaft_polygon_data
                                                                                    for ventilation_polygon in ventilation_shaft_polygon_data:
                                                                                        venti_hasarc = any(
                                                                                            [entity.dxftype() == "ARC"
                                                                                             for
                                                                                             entity in
                                                                                             ventilation_polygon.virtual_entities()])

                                                                                        ventilation_polygon_pts= ventilation_polygon.get_points(
                                                                                            "xy")
                                                                                        if len(ventilation_polygon_pts)<3:
                                                                                            continue
                                                                                        ventilation_polygon_points = Polygon_Merger_ARC(ventilation_polygon) if venti_hasarc else Polygon(ventilation_polygon_pts)

                                                                                        # check ventilation polygon in special_usebua polygon or not
                                                                                        if special_usebua_polygon_points.contains(ventilation_polygon_points):
                                                                                            ventilation_area = round(ventilation_polygon_points.area,2)
                                                                                            special_usebua_ventilation_area_list.append(ventilation_area)

                                                                                    # iterate slabcutoutvoid polygon from slab_cutout_void_polygon_data
                                                                                    for slab_cutout_void_polygon in slab_cutout_void_polygon_data:

                                                                                        slab_hasarc = any(
                                                                                            [entity.dxftype() == "ARC"
                                                                                             for
                                                                                             entity in
                                                                                             slab_cutout_void_polygon.virtual_entities()])

                                                                                        slab_cutout_polygon_pts=slab_cutout_void_polygon.get_points(
                                                                                            "xy")
                                                                                        if len(slab_cutout_polygon_pts)<3:
                                                                                            continue

                                                                                        slab_cutout_polygon_points = Polygon_Merger_ARC(slab_cutout_void_polygon) if slab_hasarc else Polygon(slab_cutout_polygon_pts)
                                                                                        # check slabcutoutvoid polygon in special_usebua polygon or not
                                                                                        if special_usebua_polygon_points.contains(slab_cutout_polygon_points):
                                                                                            slab_cutout_area = round(slab_cutout_polygon_points.area,2)
                                                                                            special_usebua_slab_cutout_area_list.append(slab_cutout_area)

                                                                                    # iterate refuge polygon in refuge_area_polygon_data
                                                                                    for refuge_polygon in refuge_area_polygon_data:

                                                                                        refuge_hasarc = any(
                                                                                            [entity.dxftype() == "ARC"
                                                                                             for
                                                                                             entity in
                                                                                             refuge_polygon.virtual_entities()])

                                                                                        refuge_polygon_pts=refuge_polygon.get_points("xy")
                                                                                        if len(refuge_polygon_pts)<3:
                                                                                            continue

                                                                                        refuge_polygon_points = Polygon_Merger_ARC(refuge_polygon) if refuge_hasarc else Polygon(refuge_polygon_pts)
                                                                                        # check refuge polygon in special_usebua polygon or not
                                                                                        # if special_usebua_polygon_points.contains(refuge_polygon_points):
                                                                                        if special_usebua_polygon_points.contains(refuge_polygon_points) == True or special_usebua_polygon_points.touches(refuge_polygon_points) == True or round(special_usebua_polygon_points.distance(refuge_polygon_points),2) == 0.0:
                                                                                            refuge_area = round(refuge_polygon_points.area,2)
                                                                                            special_usebua_refuge_area_list.append(refuge_area)

                                                                                    # iterate lift polygon in lift_area_polygon_data
                                                                                    for lift_polygon in lift_area_polygon_data:

                                                                                        lift_hasarc = any(
                                                                                            [entity.dxftype() == "ARC"
                                                                                             for
                                                                                             entity in
                                                                                             lift_polygon.virtual_entities()])

                                                                                        lift_polygon_pts= lift_polygon.get_points("xy")
                                                                                        if len(lift_polygon_pts)<3:
                                                                                            continue

                                                                                        lift_polygon_points = Polygon_Merger_ARC(lift_polygon) if lift_hasarc else Polygon(lift_polygon_pts)
                                                                                         # check lift polygon in terrace polygon or not
                                                                                        if special_usebua_polygon_points.contains(lift_polygon_points):
                                                                                            lift_area = round(lift_polygon_points.area,2)
                                                                                            special_usebua_lift_area_list.append(lift_area)

                                                                                    # iterate staircase polygon in staircase_area_polygon_data
                                                                                    for staircase_polygon in staircase_area_polygon_data:
                                                                                        pts = staircase_polygon.get_points(
                                                                                            "xy")

                                                                                        if len(pts) <= 2 or not staircase_polygon.closed:
                                                                                            continue

                                                                                        stair_hasarc = any(
                                                                                            entity.dxftype() == "ARC"
                                                                                            for entity in
                                                                                            staircase_polygon.virtual_entities())

                                                                                        staircase_polygon_points = (
                                                                                            Polygon_Merger_ARC(
                                                                                                staircase_polygon) if stair_hasarc else Polygon(
                                                                                                pts))
                                                                                        # if len(staircase_polygon.get_points(
                                                                                        #         "xy")) <= 2:
                                                                                        #     continue
                                                                                        #
                                                                                        # stair_hasarc = any(
                                                                                        #     [entity.dxftype() == "ARC"
                                                                                        #      for
                                                                                        #      entity in
                                                                                        #      staircase_polygon.virtual_entities()])
                                                                                        #
                                                                                        # staircase_polygon_points = Polygon_Merger_ARC(staircase_polygon) if stair_hasarc else Polygon(staircase_polygon.get_points("xy"))

                                                                                        # check staircase polygon in terrace polygon or not
                                                                                        if special_usebua_polygon_points.contains(staircase_polygon_points):
                                                                                            staircase_area = round(staircase_polygon_points.area,2)
                                                                                            special_usebua_staircase_area_list.append(staircase_area)

                                                                                    totsplbua_balcony_area += np.sum(special_usebua_balcony_area_list).round(2)
                                                                                    totsplbua_accessory_area += np.sum(special_usebua_accessory_area_list).round(2)
                                                                                    totsplbua_ventilation_area += np.sum(special_usebua_ventilation_area_list).round(2)
                                                                                    totsplbua_slab_cutout_area += np.sum(special_usebua_slab_cutout_area_list).round(2)
                                                                                    totsplbua_refuge_area += np.sum(special_usebua_refuge_area_list).round(2)
                                                                                    totsplbua_lift_area += np.sum(special_usebua_lift_area_list).round(2)
                                                                                    totsplbua_staircase_area += np.sum(special_usebua_staircase_area_list).round(2)
                                                                                    occupancy_label = special_usebua_polygon[1]

                                                                            if any([
                                                                                totsplbua_balcony_area,
                                                                                totsplbua_accessory_area,
                                                                                totsplbua_ventilation_area,
                                                                                totsplbua_slab_cutout_area,
                                                                                totsplbua_refuge_area,
                                                                                totsplbua_lift_area,
                                                                                totsplbua_staircase_area
                                                                            ]):
                                                                                spldict = dict()

                                                                                spldict['SPECIAL_USEBUA_OCCUPANCY_TYPE'] = occupancy_label
                                                                                spldict['SPECIAL_USEBUA_ACCESSORY'] = str(round(totsplbua_accessory_area, 2))
                                                                                spldict['SPECIAL_USEBUA_BALCONY'] = str(round(totsplbua_balcony_area, 2))
                                                                                spldict['SPECIAL_USEBUA_VENTILATION_SHAFT'] = str(round(totsplbua_ventilation_area,2))
                                                                                spldict['SPECIAL_USEBUA_SLAB_CUTOUT_VOID'] = str(round(totsplbua_slab_cutout_area,2))
                                                                                spldict['SPECIAL_USEBUA_REFUSE_AREA'] = str(round(totsplbua_refuge_area, 2))
                                                                                spldict['SPECIAL_USEBUA_LIFT_AREA'] = str(round(totsplbua_lift_area, 2))
                                                                                spldict['SPECIAL_USEBUA_STAIRCASE_AREA'] = str(round(totsplbua_staircase_area, 2))
                                                                                floor_list.append(spldict)

                                                                            if floor_list != []:
                                                                                rspacefloor_name = n1 + ' FLOOR PLAN'
                                                                                stripfloor_name = rspacefloor_name.strip()
                                                                                floor_dict = dict()
                                                                                floor_dict['BLDG_NAME'] = stripbuilding_name
                                                                                floor_dict['BLDG_REFID'] = building_polygon_id
                                                                                floor_dict['FLOOR'] = stripfloor_name
                                                                                floor_dict['FLOOR_REFID'] = floor_label_id  # floor_polygon_id

                                                                                for dict_data in floor_list:
                                                                                    floor_dict.update(dict_data)
                                                                                if floor_dict != {}:
                                                                                    resultsList.append(
                                                                                        floor_dict)  # json.dumps(floor_dict))

                                                else:

                                                    floor_text_insert_pts = floor_dxf_attribs.get('insert')

                                                    np_floor_text_insert_pts = np.array([floor_text_insert_pts[0], floor_text_insert_pts[1]]).round(2)

                                                    floor_text_point = Point(np_floor_text_insert_pts)

                                                    # iterate floor polygon data from floor data

                                                    for floor_polygon in floor_data:

                                                        if floor_polygon.dxftype() == 'LWPOLYLINE':

                                                            # floor_polygon_id=floor_polygon.dxf.handle

                                                            floor_polygon_pts = [fp[0:2] for fp in floor_polygon.get_points()]

                                                            if len(floor_polygon_pts) >= 3:

                                                                floor_polygon_points = Polygon(floor_polygon_pts)
                                                                # check floor text in floor polygon or not
                                                                if floor_polygon_points.contains(floor_text_point) or floor_polygon_points.touches(floor_text_point) or round(floor_polygon_points.distance(floor_text_point)) == 0:
                                                                    # check floor polygon in building polygon or not
                                                                    if building_polygon_points.contains(floor_polygon_points) or building_polygon_points.touches(floor_polygon_points):
                                                                        # print("== Floor Polygon Area",floor_polygon_points.area)

                                                                        floor_list = []
                                                                        parking_polygon_data = Parking_PolygonData(Parking_data, floor_polygon_points)

                                                                        if parking_polygon_data is not None:
                                                                            parking_hasarc = any(
                                                                                [entity.dxftype() == "ARC"
                                                                                 for
                                                                                 entity in
                                                                                 parking_polygon_data.virtual_entities()])

                                                                            parking_polygon_points = Polygon_Merger_ARC(parking_polygon_data) if parking_hasarc else Polygon(parking_polygon_data.get_points("xy"))
                                                                            # print("== Parking Polygon Area",parking_polygon_points.area)
                                                                            parking_balcony_area_list = []
                                                                            parking_accessory_area_list = []
                                                                            parking_ventilation_area_list = []
                                                                            parking_slab_cutout_area_list = []
                                                                            parking_refuge_area_list = []
                                                                            parking_lift_area_list = []
                                                                            parking_staircase_area_list = []
                                                                            # iterate balcony polygon from balcony_polygon_data
                                                                            for balcony_polygon in balcony_polygon_data:

                                                                                balc_hasarc = any(
                                                                                    [entity.dxftype() == "ARC"
                                                                                     for
                                                                                     entity in
                                                                                     balcony_polygon.virtual_entities()])

                                                                                balcony_polygon_pts=balcony_polygon.get_points("xy")
                                                                                if len(balcony_polygon_pts)<3:
                                                                                    continue

                                                                                balcony_polygon_points = Polygon_Merger_ARC(balcony_polygon) if balc_hasarc else Polygon(balcony_polygon_pts)
                                                                                # check balcony polygon in resibua polygon or not
                                                                                if parking_polygon_points.contains(balcony_polygon_points) or parking_polygon_points.touches(balcony_polygon_points) or round(parking_polygon_points.distance(balcony_polygon_points)) == 0:
                                                                                    balcony_area = round(balcony_polygon_points.area,2)
                                                                                    parking_balcony_area_list.append(balcony_area)

                                                                            # iterate accessory polygon from accessory_use_polygon_data
                                                                            for accessory_polygon in accessory_use_polygon_data:
                                                                                acc_hasarc = any(
                                                                                    [entity.dxftype() == "ARC"
                                                                                     for
                                                                                     entity in
                                                                                     accessory_polygon.virtual_entities()])

                                                                                accessory_polygon_pts=accessory_polygon.get_points("xy")
                                                                                if len(accessory_polygon_pts)<3:
                                                                                    continue

                                                                                accessory_polygon_points = Polygon_Merger_ARC(accessory_polygon) if acc_hasarc else Polygon(accessory_polygon_pts)
                                                                                # check accessory polygon in resibua_polygon or not
                                                                                if parking_polygon_points.contains(accessory_polygon_points):
                                                                                    accessory_area = round(accessory_polygon_points.area,2)
                                                                                    parking_accessory_area_list.append(accessory_area)

                                                                            # iterate ventilation polygon from ventilation_shaft_polygon_data
                                                                            for ventilation_polygon in ventilation_shaft_polygon_data:
                                                                                venti_hasarc = any(
                                                                                    [entity.dxftype() == "ARC"
                                                                                     for
                                                                                     entity in
                                                                                     ventilation_polygon.virtual_entities()])

                                                                                ventilation_polygon_pts=ventilation_polygon.get_points("xy")
                                                                                if len(ventilation_polygon_pts)<3:
                                                                                    continue
                                                                                ventilation_polygon_points = Polygon_Merger_ARC(ventilation_polygon) if venti_hasarc else Polygon(ventilation_polygon_pts)
                                                                                # check ventilation polygon in resibua polygon or not
                                                                                if parking_polygon_points.contains(ventilation_polygon_points):
                                                                                    ventilation_area = round(ventilation_polygon_points.area,2)
                                                                                    parking_ventilation_area_list.append(ventilation_area)

                                                                            # iterate slabcutoutvoid polygon from slab_cutout_void_polygon_data
                                                                            for slab_cutout_void_polygon in slab_cutout_void_polygon_data:
                                                                                slab_hasarc = any(
                                                                                    [entity.dxftype() == "ARC"
                                                                                     for
                                                                                     entity in
                                                                                     slab_cutout_void_polygon.virtual_entities()])

                                                                                slab_cutout_polygon_pts= slab_cutout_void_polygon.get_points(
                                                                                    "xy")

                                                                                if len(slab_cutout_polygon_pts)<3:
                                                                                    continue

                                                                                slab_cutout_polygon_points = Polygon_Merger_ARC(slab_cutout_void_polygon) if slab_hasarc else Polygon(slab_cutout_polygon_pts)
                                                                                # check slabcutoutvoid polygon in resibua polygon or not
                                                                                if parking_polygon_points.contains(slab_cutout_polygon_points):
                                                                                    slab_cutout_area = round(slab_cutout_polygon_points.area,2)
                                                                                    parking_slab_cutout_area_list.append(slab_cutout_area)

                                                                            # iterate refuge_polygon from refuge_area_polygon_data
                                                                            for refuge_polygon in refuge_area_polygon_data:

                                                                                refuge_hasarc = any(
                                                                                    [entity.dxftype() == "ARC"
                                                                                     for
                                                                                     entity in
                                                                                     refuge_polygon.virtual_entities()])

                                                                                refuge_polygon_pts=refuge_polygon.get_points("xy")
                                                                                if len(refuge_polygon_pts)<3:
                                                                                    continue
                                                                                refuge_polygon_points = Polygon_Merger_ARC(refuge_polygon) if refuge_hasarc else Polygon(refuge_polygon_pts)
                                                                                # check refuge polygon in resibua polygon or not
                                                                                # if parking_polygon_points.contains(refuge_polygon_points):
                                                                                if parking_polygon_points.contains(refuge_polygon_points) == True or parking_polygon_points.touches(refuge_polygon_points) == True or round(
                                                                                    parking_polygon_points.distance(refuge_polygon_points),2) == 0.0:
                                                                                    refuge_area = round(refuge_polygon_points.area,2)
                                                                                    parking_refuge_area_list.append(refuge_area)

                                                                            # iterate lift polygon in lift_area_polygon_data
                                                                            for lift_polygon in lift_area_polygon_data:

                                                                                lift_hasarc = any(
                                                                                    [entity.dxftype() == "ARC"
                                                                                     for
                                                                                     entity in
                                                                                     lift_polygon.virtual_entities()])

                                                                                lift_polygon_pts= lift_polygon.get_points("xy")

                                                                                if len(lift_polygon_pts)<3:
                                                                                    continue

                                                                                lift_polygon_points = Polygon_Merger_ARC(lift_polygon) if lift_hasarc else Polygon(lift_polygon_pts)
                                                                                # check lift polygon in terrace polygon or not
                                                                                if parking_polygon_points.contains(lift_polygon_points):
                                                                                    lift_area = round(lift_polygon_points.area, 2)
                                                                                    parking_lift_area_list.append(lift_area)

                                                                            # iterate staircase polygon in staircase_area_polygon_data
                                                                            for staircase_polygon in staircase_area_polygon_data:

                                                                                pts = staircase_polygon.get_points("xy")

                                                                                if len(pts) <= 2 or not staircase_polygon.closed:
                                                                                    continue

                                                                                stair_hasarc = any(
                                                                                    entity.dxftype() == "ARC" for
                                                                                    entity in
                                                                                    staircase_polygon.virtual_entities())

                                                                                staircase_polygon_points = (
                                                                                    Polygon_Merger_ARC(
                                                                                        staircase_polygon)
                                                                                    if stair_hasarc
                                                                                    else Polygon(pts)
                                                                                )

                                                                                if parking_polygon_points.contains(
                                                                                        staircase_polygon_points):
                                                                                    staircase_area = round(
                                                                                        staircase_polygon_points.area,
                                                                                        2)
                                                                                    parking_staircase_area_list.append(
                                                                                        staircase_area)

                                                                            np_sum_of_parking_balcony_area = np.sum(parking_balcony_area_list).round(2)
                                                                            np_sum_of_parking_accessory_area = np.sum(parking_accessory_area_list).round(2)
                                                                            np_sum_of_parking_ventilation_area = np.sum(parking_ventilation_area_list).round(2)
                                                                            np_sum_of_parking_slab_cutout_area = np.sum(parking_slab_cutout_area_list).round(2)
                                                                            np_sum_of_parking_refuge_area = np.sum(parking_refuge_area_list).round(2)
                                                                            np_sum_of_parking_lift_area = np.sum(parking_lift_area_list).round(2)
                                                                            np_sum_of_parking_staircase_area = np.sum(parking_staircase_area_list).round(2)

                                                                            parkdict = dict()
                                                                            parkdict['PARKING_ACCESSORY'] = str(np_sum_of_parking_accessory_area)
                                                                            parkdict['PARKING_BALCONY'] = str(np_sum_of_parking_balcony_area)
                                                                            parkdict['PARKING_VENTILATION_SHAFT'] = str(np_sum_of_parking_ventilation_area)
                                                                            parkdict['PARKING_SLAB_CUTOUT_VOID'] = str(np_sum_of_parking_slab_cutout_area)
                                                                            parkdict['PARKING_REFUSE_AREA'] = str(np_sum_of_parking_refuge_area)
                                                                            parkdict['PARKING_LIFT_AREA'] = str(np_sum_of_parking_lift_area)
                                                                            parkdict['PARKING_STAIRCASE_AREA'] = str(np_sum_of_parking_staircase_area)

                                                                            floor_list.append(parkdict)

                                                                        # iterate resibua polygon from resibua_polygon_data
                                                                        totresibua_balcony_area = 0.0
                                                                        totresibua_accessory_area = 0.0
                                                                        totresibua_ventilation_area = 0.0
                                                                        totresibua_slab_cutout_area = 0.0
                                                                        totresibua_refuge_area = 0.0
                                                                        totresibua_lift_area = 0.0
                                                                        totresibua_staircase_area = 0.0
                                                                        occupancy_label = None

                                                                        for resibua_polygon in resibua_layer_data[1].values():
                                                                            # print(resibua_polygon)
                                                                            # polygon merge with arc

                                                                            resi_hasarc = any(
                                                                                [entity.dxftype() == "ARC"
                                                                                 for
                                                                                 entity in
                                                                                 resibua_polygon[0].virtual_entities()])

                                                                            resibua_polygon_pts= resibua_polygon[0].get_points("xy")
                                                                            if len(resibua_polygon_pts)<3:
                                                                                continue

                                                                            resibua_polygon_points = Polygon_Merger_ARC(resibua_polygon[0]) if resi_hasarc else Polygon(resibua_polygon_pts)
                                                                            # print("Resi Bua Area ==",resibua_polygon_points.area)
                                                                            # check resibua polygon in floor polygon or not

                                                                            if floor_polygon_points.contains(resibua_polygon_points) or floor_polygon_points.touches(resibua_polygon_points) or round(floor_polygon_points.distance(resibua_polygon_points)) == 0:
                                                                                resibua_balcony_area_list = []
                                                                                resibua_accessory_area_list = []
                                                                                resibua_ventilation_area_list = []
                                                                                resibua_slab_cutout_area_list = []
                                                                                resibua_refuge_area_list = []
                                                                                resibua_lift_area_list = []
                                                                                resibua_staircase_area_list = []

                                                                                # iterate balcony polygon from balcony_polygon_data
                                                                                for balcony_polygon in balcony_polygon_data:

                                                                                    balcony_hasarc = any(
                                                                                        [entity.dxftype() == "ARC"
                                                                                         for
                                                                                         entity in
                                                                                         balcony_polygon.virtual_entities()])

                                                                                    balcony_polygon_pts=balcony_polygon.get_points("xy")
                                                                                    if len(balcony_polygon_pts)<3:
                                                                                        continue

                                                                                    balcony_polygon_points = Polygon_Merger_ARC(balcony_polygon) if balcony_hasarc else Polygon(balcony_polygon_pts)
                                                                                    # check balcony polygon in resibua_polygon or not
                                                                                    if resibua_polygon_points.contains(balcony_polygon_points) or resibua_polygon_points.touches(balcony_polygon_points) or round(resibua_polygon_points.distance(balcony_polygon_points)) == 0:
                                                                                        balcony_area = round(balcony_polygon_points.area,2)
                                                                                        resibua_balcony_area_list.append(balcony_area)

                                                                                # iterate accessory polygon from accessory_use_polygon_data
                                                                                for accessory_polygon in accessory_use_polygon_data:

                                                                                    acc_hasarc = any(
                                                                                        [entity.dxftype() == "ARC"
                                                                                         for
                                                                                         entity in
                                                                                         accessory_polygon.virtual_entities()])

                                                                                    accessory_polygon_pts=accessory_polygon.get_points("xy")
                                                                                    if len(accessory_polygon_pts)<3:
                                                                                        continue

                                                                                    accessory_polygon_points = Polygon_Merger_ARC(accessory_polygon) if acc_hasarc else Polygon(accessory_polygon_pts)
                                                                                    # check accessory polygon in resibua_polygon or not
                                                                                    if resibua_polygon_points.contains(accessory_polygon_points):
                                                                                        accessory_area = round(accessory_polygon_points.area,2)
                                                                                        resibua_accessory_area_list.append(accessory_area)

                                                                                # iterate ventilation polygon from ventilation_shaft_polygon_data
                                                                                for ventilation_polygon in ventilation_shaft_polygon_data:
                                                                                    venti_hasarc = any(
                                                                                        [entity.dxftype() == "ARC"
                                                                                         for
                                                                                         entity in
                                                                                         ventilation_polygon.virtual_entities()])

                                                                                    ventilation_polygon_pts= ventilation_polygon.get_points("xy")
                                                                                    if len(ventilation_polygon_pts)<3:
                                                                                        continue
                                                                                    ventilation_polygon_points = Polygon_Merger_ARC(ventilation_polygon) if venti_hasarc else Polygon(ventilation_polygon_pts)
                                                                                    # check ventilation polygon in resibua polygon or not
                                                                                    if resibua_polygon_points.contains(ventilation_polygon_points):
                                                                                        ventilation_area = round(ventilation_polygon_points.area, 2)
                                                                                        resibua_ventilation_area_list.append(ventilation_area)

                                                                                # iterate slabcutoutvoid polygon from slab_cutout_void_polygon_data
                                                                                for slab_cutout_void_polygon in slab_cutout_void_polygon_data:

                                                                                    slab_hasarc = any(
                                                                                        [entity.dxftype() == "ARC"
                                                                                         for
                                                                                         entity in
                                                                                         slab_cutout_void_polygon.virtual_entities()])

                                                                                    slab_cutout_polygon_pts=slab_cutout_void_polygon.get_points(
                                                                                        "xy")
                                                                                    if len(slab_cutout_polygon_pts)<3:
                                                                                        continue

                                                                                    slab_cutout_polygon_points = Polygon_Merger_ARC(slab_cutout_void_polygon) if slab_hasarc else Polygon(slab_cutout_polygon_pts)
                                                                                    # check slabcutoutvoid polygon in resibua polygon or not
                                                                                    if resibua_polygon_points.contains(slab_cutout_polygon_points):
                                                                                        slab_cutout_area = round(slab_cutout_polygon_points.area,2)
                                                                                        resibua_slab_cutout_area_list.append(slab_cutout_area)

                                                                                # iterate refuge_polygon from refuge_area_polygon_data
                                                                                for refuge_polygon in refuge_area_polygon_data:

                                                                                    refuge_hasarc = any(
                                                                                        [entity.dxftype() == "ARC"
                                                                                         for
                                                                                         entity in
                                                                                         refuge_polygon.virtual_entities()])

                                                                                    refuge_polygon_pts=refuge_polygon.get_points("xy")
                                                                                    if len(refuge_polygon_pts)<3:
                                                                                        continue

                                                                                    refuge_polygon_points = Polygon_Merger_ARC(refuge_polygon) if refuge_hasarc else Polygon(refuge_polygon_pts)
                                                                                    # check refuge polygon in resibua polygon or not
                                                                                    # if resibua_polygon_points.contains(refuge_polygon_points):
                                                                                    if resibua_polygon_points.contains(refuge_polygon_points) == True or resibua_polygon_points.touches(refuge_polygon_points) == True or round(resibua_polygon_points.distance(refuge_polygon_points),2) == 0.0:
                                                                                        refuge_area = round(refuge_polygon_points.area,2)
                                                                                        resibua_refuge_area_list.append(refuge_area)

                                                                                # iterate lift polygon in lift_area_polygon_data

                                                                                for lift_polygon in lift_area_polygon_data:

                                                                                    lift_hasarc = any(
                                                                                        [entity.dxftype() == "ARC"
                                                                                         for
                                                                                         entity in
                                                                                         lift_polygon.virtual_entities()])

                                                                                    lift_polygon_pts=lift_polygon.get_points("xy")

                                                                                    if len(lift_polygon_pts)<3:
                                                                                        continue

                                                                                    lift_polygon_points = Polygon_Merger_ARC(lift_polygon) if lift_hasarc else Polygon(lift_polygon_pts)
                                                                                    # check lift polygon in terrace polygon or not
                                                                                    if resibua_polygon_points.contains(lift_polygon_points):
                                                                                        lift_area = round(lift_polygon_points.area,2)
                                                                                        resibua_lift_area_list.append(lift_area)

                                                                                # iterate staircase polygon in staircase_area_polygon_data
                                                                                for staircase_polygon in staircase_area_polygon_data:

                                                                                    pts = staircase_polygon.get_points(
                                                                                        "xy")

                                                                                    if len(pts) <= 2 or not staircase_polygon.closed:
                                                                                        continue

                                                                                    stair_hasarc = any(
                                                                                        entity.dxftype() == "ARC" for
                                                                                        entity in
                                                                                        staircase_polygon.virtual_entities())

                                                                                    staircase_polygon_points = (
                                                                                        Polygon_Merger_ARC(
                                                                                            staircase_polygon)
                                                                                        if stair_hasarc
                                                                                        else Polygon(pts)
                                                                                    )

                                                                                    # check staircase polygon in terrace polygon or not
                                                                                    if resibua_polygon_points.contains(staircase_polygon_points):
                                                                                        staircase_area = round(staircase_polygon_points.area,2)
                                                                                        resibua_staircase_area_list.append(staircase_area)

                                                                                totresibua_balcony_area += np.sum(resibua_balcony_area_list).round(2)
                                                                                totresibua_accessory_area += np.sum(resibua_accessory_area_list).round(2)
                                                                                totresibua_ventilation_area += np.sum(resibua_ventilation_area_list).round(2)
                                                                                totresibua_slab_cutout_area += np.sum(resibua_slab_cutout_area_list).round(2)
                                                                                totresibua_refuge_area += np.sum(resibua_refuge_area_list).round(2)
                                                                                totresibua_lift_area += np.sum(resibua_lift_area_list).round(2)
                                                                                totresibua_staircase_area += np.sum(resibua_staircase_area_list).round(2)
                                                                                occupancy_label = resibua_polygon[1]

                                                                        print("Adding Area....")
                                                                        if any([
                                                                            totresibua_accessory_area,
                                                                            totresibua_balcony_area,
                                                                            totresibua_ventilation_area,
                                                                            totresibua_slab_cutout_area,
                                                                            totresibua_refuge_area,
                                                                            totresibua_lift_area,
                                                                            totresibua_staircase_area]):

                                                                            residict = dict()

                                                                            residict['RESIBUA_OCCUPANCY_TYPE'] = occupancy_label
                                                                            residict['RESIBUA_ACCESSORY'] = str(round(totresibua_accessory_area, 2))
                                                                            residict['RESIBUA_BALCONY'] = str(round(totresibua_balcony_area, 2))
                                                                            residict['RESIBUA_VENTILATION_SHAFT'] = str(round(totresibua_ventilation_area, 2))
                                                                            residict['RESIBUA_SLAB_CUTOUT_VOID'] = str(round(totresibua_slab_cutout_area, 2))
                                                                            residict['RESIBUA_REFUSE_AREA'] = str(round(totresibua_refuge_area, 2))
                                                                            residict['RESIBUA_LIFT_AREA'] = str(round(totresibua_lift_area, 2))
                                                                            residict['RESIBUA_STAIRCASE_AREA'] = str(round(totresibua_staircase_area, 2))
                                                                            floor_list.append(residict)

                                                                        # iterate commbua polygon from commbua_polygon_data
                                                                        totcommbua_balcony_area = 0.0
                                                                        totcommbua_accessory_area = 0.0
                                                                        totcommbua_ventilation_area = 0.0
                                                                        totcommbua_slab_cutout_area = 0.0
                                                                        totcommbua_refuge_area = 0.0
                                                                        totcommbua_lift_area = 0.0
                                                                        totcommbua_staircase_area = 0.0
                                                                        occupancy_label = None

                                                                        for commbua_polygon in commbua_layer_data[1].values():
                                                                            # polygon merg with arc
                                                                            commbua_hasarc = any(
                                                                                [entity.dxftype() == "ARC"
                                                                                 for
                                                                                 entity in
                                                                                 commbua_polygon[0].virtual_entities()])

                                                                            commbua_polygon_pts=commbua_polygon[0].get_points("xy")

                                                                            if len(commbua_polygon_pts)<3:
                                                                                continue

                                                                            commbua_polygon_points = Polygon_Merger_ARC(commbua_polygon[0]) if commbua_hasarc else Polygon(commbua_polygon_pts)
                                                                            # print('--------------------------------')

                                                                            # check commbua polygon in floor polygon or not

                                                                            if floor_polygon_points.contains(commbua_polygon_points):

                                                                                commbua_balcony_area_list = []
                                                                                commbua_accessory_area_list = []
                                                                                commbua_ventilation_area_list = []
                                                                                commbua_slab_cutout_area_list = []
                                                                                commbua_refuge_area_list = []
                                                                                commbua_lift_area_list = []
                                                                                commbua_staircase_area_list = []

                                                                                # iterate balcony polygon from balcony_polygon_data
                                                                                for balcony_polygon in balcony_polygon_data:

                                                                                    balcony_hasarc = any(
                                                                                        [entity.dxftype() == "ARC"
                                                                                         for
                                                                                         entity in
                                                                                         balcony_polygon.virtual_entities()])
                                                                                    balcony_polygon_points= balcony_polygon.get_points("xy")
                                                                                    if len(balcony_polygon_points)<3:
                                                                                        continue
                                                                                    balcony_polygon_points = Polygon_Merger_ARC(balcony_polygon) if balcony_hasarc else Polygon(balcony_polygon_points)
                                                                                    # check balcony polygon in commbua polygon or not
                                                                                    if commbua_polygon_points.contains(balcony_polygon_points) or commbua_polygon_points.touches(balcony_polygon_points) or round(commbua_polygon_points.distance(balcony_polygon_points)) == 0:
                                                                                        balcony_area = round(balcony_polygon_points.area,2)
                                                                                        commbua_balcony_area_list.append(balcony_area)

                                                                                # iterate accessory polygon from accessory_use_polygon_data
                                                                                for accessory_polygon in accessory_use_polygon_data:

                                                                                    acce_hasarc = any(
                                                                                        [entity.dxftype() == "ARC"
                                                                                         for
                                                                                         entity in
                                                                                         accessory_polygon.virtual_entities()])

                                                                                    accessory_polygon_pts= accessory_polygon.get_points("xy")
                                                                                    if len(accessory_polygon_pts)<3:
                                                                                        continue

                                                                                    accessory_polygon_points = Polygon_Merger_ARC(accessory_polygon) if acce_hasarc else Polygon(accessory_polygon_pts)
                                                                                    # check accessory polygon in commbua_polygon or not
                                                                                    if commbua_polygon_points.contains(accessory_polygon_points):
                                                                                        accessory_area = round(accessory_polygon_points.area,2)
                                                                                        commbua_accessory_area_list.append(accessory_area)

                                                                                # iterate ventilation polygon from ventilation_shaft_polygon_data

                                                                                for ventilation_polygon in ventilation_shaft_polygon_data:

                                                                                    venti_hasarc = any(
                                                                                        [entity.dxftype() == "ARC"
                                                                                         for
                                                                                         entity in
                                                                                         ventilation_polygon.virtual_entities()])

                                                                                    ventilation_polygon_pts= ventilation_polygon.get_points("xy")
                                                                                    if len(ventilation_polygon_pts)<3:
                                                                                        continue
                                                                                    ventilation_polygon_points = Polygon_Merger_ARC(ventilation_polygon) if venti_hasarc else Polygon(ventilation_polygon_pts)
                                                                                    # check ventilation polygon in commbua polygon or not
                                                                                    if commbua_polygon_points.contains(ventilation_polygon_points):
                                                                                        ventilation_area = round(ventilation_polygon_points.area,2)
                                                                                        commbua_ventilation_area_list.append(ventilation_area)

                                                                                # iterate slabcutoutvoid polygon from slab_cutout_void_polygon_data
                                                                                for slab_cutout_void_polygon in slab_cutout_void_polygon_data:

                                                                                    slab_hasarc = any(
                                                                                        [entity.dxftype() == "ARC"
                                                                                         for
                                                                                         entity in
                                                                                         slab_cutout_void_polygon.virtual_entities()])

                                                                                    slab_cutout_void_pts=slab_cutout_void_polygon.get_points("xy")
                                                                                    if len(slab_cutout_void_pts)<3:
                                                                                        continue

                                                                                    slab_cutout_polygon_points = Polygon_Merger_ARC(slab_cutout_void_polygon) if slab_hasarc else Polygon(slab_cutout_void_pts)
                                                                                    # check slabcutoutvoid polygon in commbua polygon or not
                                                                                    if commbua_polygon_points.contains(slab_cutout_polygon_points):
                                                                                        slab_cutout_area = round(slab_cutout_polygon_points.area,2)
                                                                                        commbua_slab_cutout_area_list.append(slab_cutout_area)

                                                                                # iterate refuge polygon in refuge_area_polygon_data
                                                                                for refuge_polygon in refuge_area_polygon_data:

                                                                                    refuge_hasarc = any(
                                                                                        [entity.dxftype() == "ARC"
                                                                                         for
                                                                                         entity in
                                                                                         refuge_polygon.virtual_entities()])

                                                                                    refuge_polygon_pts= refuge_polygon.get_points("xy")

                                                                                    if len(refuge_polygon_pts)<3:
                                                                                        continue

                                                                                    refuge_polygon_points = Polygon_Merger_ARC(refuge_polygon) if refuge_hasarc else Polygon(refuge_polygon_pts)
                                                                                    # check refuge polygon in commbua polygon or not
                                                                                    # if commbua_polygon_points.contains(refuge_polygon_points):
                                                                                    if commbua_polygon_points.contains(refuge_polygon_points) == True or commbua_polygon_points.touches(refuge_polygon_points) == True or round(commbua_polygon_points.distance(refuge_polygon_points),2) == 0.0:
                                                                                        refuge_area = round(refuge_polygon_points.area,2)
                                                                                        commbua_refuge_area_list.append(refuge_area)

                                                                                # iterate lift polygon in lift_area_polygon_data
                                                                                for lift_polygon in lift_area_polygon_data:

                                                                                    lift_hasarc = any(
                                                                                        [entity.dxftype() == "ARC"
                                                                                         for
                                                                                         entity in
                                                                                         lift_polygon.virtual_entities()])

                                                                                    lift_polygon_pts= lift_polygon.get_points("xy")
                                                                                    if len(lift_polygon_pts)<3:
                                                                                        continue

                                                                                    lift_polygon_points = Polygon_Merger_ARC(lift_polygon) if lift_hasarc else Polygon(lift_polygon_pts)
                                                                                    # check lift polygon in terrace polygon or not
                                                                                    if commbua_polygon_points.contains(lift_polygon_points):
                                                                                        lift_area = round(lift_polygon_points.area,2)
                                                                                        commbua_lift_area_list.append(lift_area)

                                                                                # iterate staircase polygon in staircase_area_polygon_data
                                                                                for staircase_polygon in staircase_area_polygon_data:
                                                                                    pts = staircase_polygon.get_points(
                                                                                        "xy")

                                                                                    if len(pts) <= 2 or not staircase_polygon.closed:
                                                                                        continue

                                                                                    stair_hasarc = any(
                                                                                        entity.dxftype() == "ARC" for
                                                                                        entity in
                                                                                        staircase_polygon.virtual_entities())

                                                                                    staircase_polygon_points = (
                                                                                        Polygon_Merger_ARC(
                                                                                            staircase_polygon)
                                                                                        if stair_hasarc
                                                                                        else Polygon(pts)
                                                                                    )

                                                                                    # if len(staircase_polygon.get_points("xy"))<=2:
                                                                                    #     continue
                                                                                    # stair_hasarc = any(
                                                                                    #     [entity.dxftype() == "ARC"
                                                                                    #      for
                                                                                    #      entity in
                                                                                    #      staircase_polygon.virtual_entities()])
                                                                                    # staircase_polygon_points = Polygon_Merger_ARC(staircase_polygon) if stair_hasarc else Polygon(staircase_polygon.get_points("xy"))
                                                                                    # check staircase polygon in terrace polygon or not
                                                                                    if commbua_polygon_points.contains(staircase_polygon_points):
                                                                                        staircase_area = round(staircase_polygon_points.area,2)
                                                                                        commbua_staircase_area_list.append(staircase_area)

                                                                                totcommbua_balcony_area += np.sum(commbua_balcony_area_list).round(2)
                                                                                totcommbua_accessory_area += np.sum(commbua_accessory_area_list).round(2)
                                                                                totcommbua_ventilation_area += np.sum(commbua_ventilation_area_list).round(2)
                                                                                totcommbua_slab_cutout_area += np.sum(commbua_slab_cutout_area_list).round(2)
                                                                                totcommbua_refuge_area += np.sum(commbua_refuge_area_list).round(2)
                                                                                totcommbua_lift_area += np.sum(commbua_lift_area_list).round(2)
                                                                                totcommbua_staircase_area += np.sum(commbua_staircase_area_list).round(2)

                                                                                occupancy_label = commbua_polygon[1]

                                                                        if any([
                                                                            totcommbua_balcony_area,
                                                                            totcommbua_accessory_area,
                                                                            totcommbua_ventilation_area,
                                                                            totcommbua_slab_cutout_area,
                                                                            totcommbua_refuge_area,
                                                                            totcommbua_lift_area,
                                                                            totcommbua_staircase_area
                                                                        ]):
                                                                            commdict = dict()
                                                                            commdict['COMMBUA_OCCUPANCY_TYPE'] = occupancy_label
                                                                            commdict['COMMBUA_ACCESSORY'] = str(round(totcommbua_accessory_area, 2))
                                                                            commdict['COMMBUA_BALCONY'] = str(round(totcommbua_balcony_area, 2))
                                                                            commdict['COMMBUA_VENTILATION_SHAFT'] = str(round(totcommbua_ventilation_area, 2))
                                                                            commdict['COMMBUA_SLAB_CUTOUT_VOID'] = str(round(totcommbua_slab_cutout_area, 2))
                                                                            commdict['COMMBUA_REFUSE_AREA'] = str(round(totcommbua_refuge_area, 2))
                                                                            commdict['COMMBUA_LIFT_AREA'] = str(round(totcommbua_lift_area, 2))
                                                                            commdict['COMMBUA_STAIRCASE_AREA'] = str(round(totcommbua_staircase_area, 2))
                                                                            floor_list.append(commdict)

                                                                        # iterate indbua polygon in indbua_polygon_data
                                                                        totindbua_balcony_area = 0.0
                                                                        totindbua_accessory_area = 0.0
                                                                        totindbua_ventilation_area = 0.0
                                                                        totindbua_slab_cutout_area = 0.0
                                                                        totindbua_refuge_area = 0.0
                                                                        totindbua_lift_area = 0.0
                                                                        totindbua_staircase_area = 0.0
                                                                        occupancy_label = None

                                                                        for indbua_polygon in indbua_layer_data[1].values():

                                                                            indbua_hasarc = any(
                                                                                [entity.dxftype() == "ARC"
                                                                                 for
                                                                                 entity in
                                                                                 indbua_polygon.virtual_entities()])

                                                                            indbua_polygon_pts=indbua_polygon[0].get_points("xy")
                                                                            if len(indbua_polygon_pts)<3:
                                                                                continue
                                                                            # polygon merge with arc
                                                                            indbua_polygon_points = Polygon_Merger_ARC(indbua_polygon[0]) if indbua_hasarc else Polygon(indbua_polygon_pts)

                                                                            # check indbua polygon in floor polygon or not
                                                                            if floor_polygon_points.contains(indbua_polygon_points) or floor_polygon_points.touches(indbua_polygon_points) or round(floor_polygon_points.distance(indbua_polygon_points)) == 0:
                                                                                indbua_balcony_area_list = []
                                                                                indbua_accessory_area_list = []
                                                                                indbua_ventilation_area_list = []
                                                                                indabua_slab_cutout_area_list = []
                                                                                indbua_refuge_area_list = []
                                                                                indbua_lift_area_list = []
                                                                                indbua_staircase_area_list = []

                                                                                # iterate balcony polygon from balcony_polygon_data
                                                                                for balcony_polygon in balcony_polygon_data:

                                                                                    balcony_hasarc = any(
                                                                                        [entity.dxftype() == "ARC"
                                                                                         for
                                                                                         entity in
                                                                                         balcony_polygon.virtual_entities()])

                                                                                    balcony_polygon_pts= balcony_polygon.get_points("xy")
                                                                                    if len(balcony_polygon_pts)<3:
                                                                                        continue

                                                                                    balcony_polygon_points = Polygon_Merger_ARC(balcony_polygon) if balcony_hasarc else Polygon(balcony_polygon_pts)
                                                                                    # check balcony polygon in indbua polygon or not
                                                                                    if indbua_polygon_points.contains(balcony_polygon_points) or indbua_polygon_points.touches(balcony_polygon_points) or round(indbua_polygon_points.distance(balcony_polygon_points)) == 0:
                                                                                        balcony_area = round(balcony_polygon_points.area,2)
                                                                                        indbua_balcony_area_list.append(balcony_area)

                                                                                # iterate accessory polygon from accessory_use_polygon_data
                                                                                for accessory_polygon in accessory_use_polygon_data:
                                                                                    acc_hasarc = any(
                                                                                        [entity.dxftype() == "ARC"
                                                                                         for
                                                                                         entity in
                                                                                         accessory_polygon.virtual_entities()])

                                                                                    accessory_polygon_pts= accessory_polygon.get_points("xy")
                                                                                    if len(accessory_polygon_pts)<3:
                                                                                        continue

                                                                                    accessory_polygon_points = Polygon_Merger_ARC(accessory_polygon) if acc_hasarc else Polygon(accessory_polygon_pts)
                                                                                    # check accessory polygon in indabua_polygon or not
                                                                                    if indbua_polygon_points.contains(accessory_polygon_points):
                                                                                        accessory_area = round(accessory_polygon_points.area,2)
                                                                                        indbua_accessory_area_list.append(accessory_area)

                                                                                # iterate ventilation polygon from ventilation_shaft_polygon_data
                                                                                for ventilation_polygon in ventilation_shaft_polygon_data:

                                                                                    venti_hasarc = any(
                                                                                        [entity.dxftype() == "ARC"
                                                                                         for
                                                                                         entity in
                                                                                         ventilation_polygon.virtual_entities()])

                                                                                    ventilation_polygon_pts=ventilation_polygon.get_points("xy")
                                                                                    if len(ventilation_polygon_pts)<3:
                                                                                        continue

                                                                                    ventilation_polygon_points = Polygon_Merger_ARC(ventilation_polygon) if venti_hasarc else Polygon(ventilation_polygon_pts)
                                                                                    # check ventilation polygon in indbua polygon or not
                                                                                    if indbua_polygon_points.contains(ventilation_polygon_points):
                                                                                        ventilation_area = round(ventilation_polygon_points.area,2)
                                                                                        indbua_ventilation_area_list.append(ventilation_area)

                                                                                # iterate slabcutoutvoid polygon from slab_cutout_void_polygon_data
                                                                                for slab_cutout_void_polygon in slab_cutout_void_polygon_data:

                                                                                    slab_hasarc = any(
                                                                                        [entity.dxftype() == "ARC"
                                                                                         for
                                                                                         entity in
                                                                                         slab_cutout_void_polygon.virtual_entities()])

                                                                                    slab_cutout_polygon_pts= slab_cutout_void_polygon.get_points(
                                                                                        "xy")
                                                                                    if len(slab_cutout_polygon_pts)<3:
                                                                                        continue
                                                                                    slab_cutout_polygon_points = Polygon_Merger_ARC(slab_cutout_void_polygon) if slab_hasarc else Polygon(slab_cutout_polygon_pts)
                                                                                    # check slabcutoutvoid polygon in indbua polygon or not
                                                                                    if indbua_polygon_points.contains(slab_cutout_polygon_points):
                                                                                        slab_cutout_area = round(slab_cutout_polygon_points.area,2)
                                                                                        indabua_slab_cutout_area_list.append(slab_cutout_area)

                                                                                # iterate refuge polygon in refuge_area_polygon_data
                                                                                for refuge_polygon in refuge_area_polygon_data:

                                                                                    refuge_hasarc = any(
                                                                                        [entity.dxftype() == "ARC"
                                                                                         for
                                                                                         entity in
                                                                                         refuge_polygon.virtual_entities()])

                                                                                    refuge_polygon_pts= refuge_polygon.get_points("xy")
                                                                                    if len(refuge_polygon_pts)<3:
                                                                                        continue

                                                                                    refuge_polygon_points = Polygon_Merger_ARC(refuge_polygon) if refuge_hasarc else Polygon(refuge_polygon_pts)
                                                                                    # check refuge polygon in indbua polygon or not
                                                                                    # if indbua_polygon_points.contains(refuge_polygon_points):
                                                                                    if indbua_polygon_points.contains(refuge_polygon_points) == True or indbua_polygon_points.touches(refuge_polygon_points) == True or round(indbua_polygon_points.distance(refuge_polygon_points),2) == 0.0:
                                                                                        refuge_area = round(refuge_polygon_points.area,2)
                                                                                        indbua_refuge_area_list.append(refuge_area)

                                                                                # iterate lift polygon in lift_area_polygon_data
                                                                                for lift_polygon in lift_area_polygon_data:

                                                                                    lift_hasarc = any(
                                                                                        [entity.dxftype() == "ARC"
                                                                                         for
                                                                                         entity in
                                                                                         lift_polygon.virtual_entities()])

                                                                                    lift_polygon_pts=lift_polygon.get_points("xy")
                                                                                    if len(lift_polygon_pts)<3:
                                                                                        continue

                                                                                    lift_polygon_points = Polygon_Merger_ARC(lift_polygon) if lift_hasarc else Polygon(lift_polygon_pts)
                                                                                    # check lift polygon in terrace polygon or not
                                                                                    if indbua_polygon_points.contains(lift_polygon_points):
                                                                                        lift_area = round(lift_polygon_points.area,2)
                                                                                        indbua_lift_area_list.append(lift_area)

                                                                                # iterate staircase polygon in staircase_area_polygon_data
                                                                                for staircase_polygon in staircase_area_polygon_data:

                                                                                    pts = staircase_polygon.get_points(
                                                                                        "xy")

                                                                                    if len(pts) <= 2 or not staircase_polygon.closed:
                                                                                        continue

                                                                                    stair_hasarc = any(
                                                                                        entity.dxftype() == "ARC" for
                                                                                        entity in
                                                                                        staircase_polygon.virtual_entities())

                                                                                    staircase_polygon_points = (
                                                                                        Polygon_Merger_ARC(
                                                                                            staircase_polygon)
                                                                                        if stair_hasarc
                                                                                        else Polygon(pts)
                                                                                    )

                                                                                    # if len(staircase_polygon.get_points("xy"))<=2:
                                                                                    #     continue
                                                                                    #
                                                                                    # stair_hasarc = any(
                                                                                    #     [entity.dxftype() == "ARC"
                                                                                    #      for
                                                                                    #      entity in
                                                                                    #      staircase_polygon.virtual_entities()])
                                                                                    #
                                                                                    # staircase_polygon_points = Polygon_Merger_ARC(staircase_polygon) if stair_hasarc else staircase_polygon.get_points("xy")
                                                                                    # check staircase polygon in terrace polygon or not
                                                                                    if indbua_polygon_points.contains(staircase_polygon_points):
                                                                                        staircase_area = round(staircase_polygon_points.area,2)
                                                                                        indbua_staircase_area_list.append(staircase_area)

                                                                                totindbua_balcony_area += np.sum(indbua_balcony_area_list).round(2)
                                                                                totindbua_accessory_area += np.sum(indbua_accessory_area_list).round(2)
                                                                                totindbua_ventilation_area += np.sum(indbua_ventilation_area_list).round(2)
                                                                                totindbua_slab_cutout_area += np.sum(indabua_slab_cutout_area_list).round(2)
                                                                                totindbua_refuge_area += np.sum(indbua_refuge_area_list).round(2)
                                                                                totindbua_lift_area += np.sum(indbua_lift_area_list).round(2)
                                                                                totindbua_staircase_area += np.sum(indbua_staircase_area_list).round(2)
                                                                                occupancy_label = indbua_polygon[1]

                                                                        if any([
                                                                            totindbua_balcony_area,
                                                                            totindbua_accessory_area,
                                                                            totindbua_ventilation_area,
                                                                            totindbua_slab_cutout_area,
                                                                            totindbua_refuge_area,
                                                                            totindbua_lift_area,
                                                                            totindbua_staircase_area]):

                                                                            inddict = dict()

                                                                            inddict['INDBUA_OCCUPANCY_TYPE'] = occupancy_label
                                                                            inddict['INDBUA_ACCESSORY'] = str(round(totindbua_accessory_area, 2))
                                                                            inddict['INDBUA_BALCONY'] = str(round(totindbua_balcony_area, 2))
                                                                            inddict['INDBUA_VENTILATION_SHAFT'] = str(round(totindbua_ventilation_area, 2))
                                                                            inddict['INDBUA_SLAB_CUTOUT_VOID'] = str(round(totindbua_slab_cutout_area, 2))
                                                                            inddict['INDBUA_REFUSE_AREA'] = str(round(totindbua_refuge_area, 2))
                                                                            inddict['INDBUA_LIFT_AREA'] = str(round(totindbua_lift_area, 2))
                                                                            inddict['INDBUA_STAIRCASE_AREA'] = str(round(totindbua_staircase_area, 2))
                                                                            floor_list.append(inddict)

                                                                        # iterate special_usebua polygon in special_usebua_polygon_data
                                                                        totsplbua_balcony_area = 0.0
                                                                        totsplbua_accessory_area = 0.0
                                                                        totsplbua_ventilation_area = 0.0
                                                                        totsplbua_slab_cutout_area = 0.0
                                                                        totsplbua_refuge_area = 0.0
                                                                        totsplbua_lift_area = 0.0
                                                                        totsplbua_staircase_area = 0.0
                                                                        occupancy_label = None

                                                                        for special_usebua_polygon in special_usebua_layer_data[1].values():
                                                                            # polygon merge with arc
                                                                            special_hasarc = any(
                                                                                [entity.dxftype() == "ARC"
                                                                                 for
                                                                                 entity in
                                                                                 special_usebua_polygon[0].virtual_entities()])

                                                                            special_usebua_polygon_pts= special_usebua_polygon[0].get_points("xy")
                                                                            if len(special_usebua_polygon_pts)<3:
                                                                                continue

                                                                            special_usebua_polygon_points = Polygon_Merger_ARC(special_usebua_polygon[0]) if special_hasarc else Polygon(special_usebua_polygon_pts)


                                                                            # check indbua polygon in floor polygon or not
                                                                            if floor_polygon_points.contains(special_usebua_polygon_points):
                                                                                special_usebua_balcony_area_list = []
                                                                                special_usebua_accessory_area_list = []
                                                                                special_usebua_ventilation_area_list = []
                                                                                special_usebua_slab_cutout_area_list = []
                                                                                special_usebua_refuge_area_list = []
                                                                                special_usebua_lift_area_list = []
                                                                                special_usebua_staircase_area_list = []

                                                                                # iterate balcony polygon from balcony_polygon_data
                                                                                for balcony_polygon in balcony_polygon_data:

                                                                                    balcony_hasarc = any(
                                                                                        [entity.dxftype() == "ARC"
                                                                                         for
                                                                                         entity in
                                                                                         balcony_polygon.virtual_entities()])

                                                                                    balcony_polygon_pts= balcony_polygon.get_points("xy")
                                                                                    if len(balcony_polygon_pts)<3:
                                                                                        continue

                                                                                    balcony_polygon_points = Polygon_Merger_ARC(balcony_polygon) if balcony_hasarc else Polygon(balcony_polygon_pts)
                                                                                    # check balcony polygon in special usebua polygon or not
                                                                                    if special_usebua_polygon_points.contains(balcony_polygon_points) or special_usebua_polygon_points.touches(balcony_polygon_points) or round(special_usebua_polygon_points.distance(balcony_polygon_points)) == 0:
                                                                                        balcony_area = round(balcony_polygon_points.area,2)
                                                                                        special_usebua_balcony_area_list.append(balcony_area)

                                                                                # iterate accessory polygon from accessory_use_polygon_data
                                                                                for accessory_polygon in accessory_use_polygon_data:

                                                                                    acc_hasarc = any(
                                                                                        [entity.dxftype() == "ARC"
                                                                                         for
                                                                                         entity in
                                                                                         accessory_polygon.virtual_entities()])

                                                                                    accessory_polygon_pts= accessory_polygon.get_points("xy")
                                                                                    if len(accessory_polygon_pts)<3:
                                                                                        continue

                                                                                    accessory_polygon_points = Polygon_Merger_ARC(accessory_polygon) if acc_hasarc else Polygon(accessory_polygon_pts)
                                                                                    # check accessory polygon in special_usebua_polygon or not
                                                                                    if special_usebua_polygon_points.contains(accessory_polygon_points):
                                                                                        accessory_area = round(accessory_polygon_points.area,2)
                                                                                        special_usebua_accessory_area_list.append(accessory_area)

                                                                                # iterate ventilation polygon from ventilation_shaft_polygon_data
                                                                                for ventilation_polygon in ventilation_shaft_polygon_data:

                                                                                    ventilation_hasarc = any(
                                                                                        [entity.dxftype() == "ARC"
                                                                                         for
                                                                                         entity in
                                                                                         ventilation_polygon.virtual_entities()])

                                                                                    ventilation_polygon_pts= ventilation_polygon.get_points("xy")
                                                                                    if len(ventilation_polygon_pts)<3:
                                                                                        continue
                                                                                    ventilation_polygon_points = Polygon_Merger_ARC(ventilation_polygon) if ventilation_hasarc else Polygon(ventilation_polygon_pts)
                                                                                    # check ventilation polygon in special_usebua polygon or not
                                                                                    if special_usebua_polygon_points.contains(ventilation_polygon_points):
                                                                                        ventilation_area = round(ventilation_polygon_points.area,2)
                                                                                        special_usebua_ventilation_area_list.append(ventilation_area)

                                                                                # iterate slabcutoutvoid polygon from slab_cutout_void_polygon_data
                                                                                for slab_cutout_void_polygon in slab_cutout_void_polygon_data:
                                                                                    # slab_cutout_polygon_pts = [sp[0:2] for sp in slab_cutout_void_polygon.get_points()]

                                                                                    slab_hasarc = any(
                                                                                        [entity.dxftype() == "ARC"
                                                                                         for
                                                                                         entity in
                                                                                         slab_cutout_void_polygon.virtual_entities()])

                                                                                    slab_cutout_polygon_pts=slab_cutout_void_polygon.get_points(
                                                                                        "xy")
                                                                                    if len(slab_cutout_polygon_pts)<3:
                                                                                        continue

                                                                                    slab_cutout_polygon_points = Polygon_Merger_ARC(slab_cutout_void_polygon) if slab_hasarc else Polygon(slab_cutout_polygon_pts)
                                                                                    # check slabcutoutvoid polygon in special_usebua polygon or not
                                                                                    if special_usebua_polygon_points.contains(slab_cutout_polygon_points):
                                                                                        slab_cutout_area = round( slab_cutout_polygon_points.area, 2)
                                                                                        special_usebua_slab_cutout_area_list.append( slab_cutout_area)

                                                                                # iterate refuge polygon in refuge_area_polygon_data
                                                                                for refuge_polygon in refuge_area_polygon_data:

                                                                                    ventilation_hasarc = any(
                                                                                        [entity.dxftype() == "ARC"
                                                                                         for
                                                                                         entity in
                                                                                         refuge_polygon.virtual_entities()])

                                                                                    refuge_polygon_pts= refuge_polygon.get_points("xy")
                                                                                    if len(refuge_polygon_pts)<3:
                                                                                        continue

                                                                                    refuge_polygon_points = Polygon_Merger_ARC(refuge_polygon) if ventilation_hasarc else Polygon(refuge_polygon_pts)
                                                                                    # check refuge polygon in special_usebua polygon or not
                                                                                    # if special_usebua_polygon_points.contains(refuge_polygon_points):
                                                                                    if special_usebua_polygon_points.contains(refuge_polygon_points) or special_usebua_polygon_points.touches(refuge_polygon_points) or round(special_usebua_polygon_points.distance(refuge_polygon_points),2) == 0.0:
                                                                                        refuge_area = round(refuge_polygon_points.area,2)
                                                                                        special_usebua_refuge_area_list.append( refuge_area)

                                                                                # iterate lift polygon in lift_area_polygon_data
                                                                                for lift_polygon in lift_area_polygon_data:

                                                                                    lift_hasarc = any(
                                                                                        [entity.dxftype() == "ARC"
                                                                                         for
                                                                                         entity in
                                                                                         lift_polygon.virtual_entities()])

                                                                                    lift_polygon_pts=lift_polygon.get_points("xy")
                                                                                    if len(lift_polygon_pts)<3:
                                                                                        continue

                                                                                    lift_polygon_points = Polygon_Merger_ARC(lift_polygon) if lift_hasarc else Polygon(lift_polygon_pts)
                                                                                    # check lift polygon in terrace polygon or not
                                                                                    if special_usebua_polygon_points.contains(lift_polygon_points):
                                                                                        lift_area = round(lift_polygon_points.area,2)
                                                                                        special_usebua_lift_area_list.append(lift_area)

                                                                                # iterate staircase polygon in staircase_area_polygon_data
                                                                                for staircase_polygon in staircase_area_polygon_data:

                                                                                    pts = staircase_polygon.get_points(
                                                                                        "xy")

                                                                                    if len(pts) <= 2 or not staircase_polygon.closed:
                                                                                        continue

                                                                                    stair_hasarc = any(
                                                                                        entity.dxftype() == "ARC" for
                                                                                        entity in
                                                                                        staircase_polygon.virtual_entities())

                                                                                    staircase_polygon_points = (
                                                                                        Polygon_Merger_ARC(
                                                                                            staircase_polygon)
                                                                                        if stair_hasarc
                                                                                        else Polygon(pts)
                                                                                    )

                                                                                    # if len(staircase_polygon.get_points(
                                                                                    #         "xy")) <= 2:
                                                                                    #     continue
                                                                                    #
                                                                                    # stair_hasarc = any(
                                                                                    #     [entity.dxftype() == "ARC"
                                                                                    #      for
                                                                                    #      entity in
                                                                                    #      staircase_polygon.virtual_entities()])
                                                                                    #
                                                                                    # staircase_polygon_points = Polygon_Merger_ARC(staircase_polygon) if stair_hasarc else Polygon(staircase_polygon.get_points("xy"))
                                                                                    # check staircase polygon in terrace polygon or not
                                                                                    if special_usebua_polygon_points.contains(staircase_polygon_points):
                                                                                        staircase_area = round(staircase_polygon_points.area,2)
                                                                                        special_usebua_staircase_area_list.append(staircase_area)

                                                                                totsplbua_balcony_area += np.sum(special_usebua_balcony_area_list).round(2)
                                                                                totsplbua_accessory_area += np.sum(special_usebua_accessory_area_list).round(2)
                                                                                totsplbua_ventilation_area += np.sum(special_usebua_ventilation_area_list).round(2)
                                                                                totsplbua_slab_cutout_area += np.sum(special_usebua_slab_cutout_area_list).round(2)
                                                                                totsplbua_refuge_area += np.sum(special_usebua_refuge_area_list).round(2)
                                                                                totsplbua_lift_area += np.sum(special_usebua_lift_area_list).round(2)
                                                                                totsplbua_staircase_area += np.sum(special_usebua_staircase_area_list).round(2)

                                                                                occupancy_label = special_usebua_polygon[1]

                                                                        if any([
                                                                            totsplbua_balcony_area,
                                                                            totsplbua_accessory_area,
                                                                            totsplbua_ventilation_area,
                                                                            totsplbua_slab_cutout_area,
                                                                            totsplbua_refuge_area,
                                                                            totsplbua_lift_area,
                                                                            totsplbua_staircase_area
                                                                        ]):
                                                                            spldict = dict()
                                                                            spldict['SPECIAL_USEBUA_OCCUPANCY_TYPE'] = occupancy_label
                                                                            spldict['SPECIAL_USEBUA_ACCESSORY'] = str(round(totsplbua_accessory_area, 2))
                                                                            spldict['SPECIAL_USEBUA_BALCONY'] = str(round(totsplbua_balcony_area, 2))
                                                                            spldict['SPECIAL_USEBUA_VENTILATION_SHAFT'] = str(round(totsplbua_ventilation_area, 2))
                                                                            spldict['SPECIAL_USEBUA_SLAB_CUTOUT_VOID'] = str(round(totsplbua_slab_cutout_area, 2))
                                                                            spldict['SPECIAL_USEBUA_REFUSE_AREA'] = str(round(totsplbua_refuge_area, 2))
                                                                            spldict['SPECIAL_USEBUA_LIFT_AREA'] = str(round(totsplbua_lift_area, 2))
                                                                            spldict['SPECIAL_USEBUA_STAIRCASE_AREA'] = str(round(totsplbua_staircase_area, 2))
                                                                            floor_list.append(spldict)

                                                                        # for terrace_polygon in terrace_polygon_data:
                                                                        #
                                                                        #     #polygon merge with arc
                                                                        #
                                                                        #     terrace_polygon_points=Polygon_Merger_ARC(terrace_polygon)
                                                                        #
                                                                        #     #check indbua polygon in floor polygon or not
                                                                        #
                                                                        #     if floor_polygon_points.contains(terrace_polygon_points)==True or floor_polygon_points.touches(terrace_polygon_points)==True or round(floor_polygon_points.distance(terrace_polygon_points))==0:
                                                                        #
                                                                        #         terrace_balcony_area_list=[]
                                                                        #
                                                                        #         terrace_accessory_area_list=[]
                                                                        #
                                                                        #         terrace_ventilation_area_list=[]
                                                                        #
                                                                        #         terrace_slab_cutout_area_list=[]
                                                                        #
                                                                        #         terrace_refuge_area_list=[]
                                                                        #
                                                                        #         terrace_lift_area_list=[]
                                                                        #
                                                                        #         terrace_staircase_area_list=[]
                                                                        #
                                                                        #         #iterate balcony polygon from balcony_polygon_data
                                                                        #
                                                                        #         for balcony_polygon in balcony_polygon_data:
                                                                        #
                                                                        #             balcony_polygon_pts=[bp[0:2] for bp in balcony_polygon.get_points()]
                                                                        #
                                                                        #             if len(balcony_polygon_pts)>=3:
                                                                        #
                                                                        #                 np_balcony_polygon_pts=np.array(balcony_polygon_pts)
                                                                        #
                                                                        #                 balcony_polygon_points=Polygon(np_balcony_polygon_pts)
                                                                        #
                                                                        #                 #check balcony polygon in special usebua polygon or not
                                                                        #
                                                                        #                 if terrace_polygon_points.contains(balcony_polygon_points)==True or terrace_polygon_points.touches(balcony_polygon_points)==True or round(terrace_polygon_points.distance(balcony_polygon_points))==0:
                                                                        #
                                                                        #                     balcony_area=round(balcony_polygon_points.area,2)
                                                                        #
                                                                        #                     terrace_balcony_area_list.append(balcony_area)
                                                                        #
                                                                        #         #iterate accessory polygon from accessory_use_polygon_data
                                                                        #
                                                                        #         for accessory_polygon in accessory_use_polygon_data:
                                                                        #
                                                                        #             accessory_polygon_pts=[ap[0:2] for ap in accessory_polygon.get_points()]
                                                                        #
                                                                        #             if len(accessory_polygon_pts)>=3:
                                                                        #
                                                                        #                 np_accessory_polygon_pts=np.array(accessory_polygon_pts).round(2)
                                                                        #
                                                                        #                 accessory_polygon_points=Polygon(np_accessory_polygon_pts)
                                                                        #
                                                                        #                 #check accessory polygon in special_usebua_polygon or not
                                                                        #
                                                                        #                 if terrace_polygon_points.contains(accessory_polygon_points)==True or terrace_polygon_points.touches(accessory_polygon_points)==True or round(terrace_polygon_points.distance(accessory_polygon_points))==0:
                                                                        #
                                                                        #                     accessory_area=round(accessory_polygon_points.area,2)
                                                                        #
                                                                        #                     terrace_accessory_area_list.append(accessory_area)
                                                                        #
                                                                        #         #iterate ventilation polygon from ventilation_shaft_polygon_data
                                                                        #
                                                                        #         for ventilation_polygon in ventilation_shaft_polygon_data:
                                                                        #
                                                                        #             ventilation_polygon_pts=[vp[0:2] for vp in ventilation_polygon.get_points()]
                                                                        #
                                                                        #             if len(ventilation_polygon_pts)>=3:
                                                                        #
                                                                        #                 np_ventilation_polygon_pts=np.array(ventilation_polygon_pts).round(2)
                                                                        #
                                                                        #                 ventilation_polygon_points=Polygon(np_ventilation_polygon_pts)
                                                                        #
                                                                        #                 #check ventilation polygon in special_usebua polygon or not
                                                                        #
                                                                        #                 if terrace_polygon_points.contains(ventilation_polygon_points)==True or terrace_polygon_points.touches(ventilation_polygon_points)==True or round(terrace_polygon_points.distance(ventilation_polygon_points))==0:
                                                                        #
                                                                        #                     ventilation_area=round(ventilation_polygon_points.area,2)
                                                                        #
                                                                        #                     terrace_ventilation_area_list.append(ventilation_area)
                                                                        #
                                                                        #         #iterate slabcutoutvoid polygon from slab_cutout_void_polygon_data
                                                                        #
                                                                        #         for slab_cutout_void_polygon in slab_cutout_void_polygon_data:
                                                                        #
                                                                        #             slab_cutout_polygon_pts=[sp[0:2] for sp in slab_cutout_void_polygon.get_points()]
                                                                        #
                                                                        #             if len(slab_cutout_polygon_pts)>=3:
                                                                        #
                                                                        #                 np_slab_cutout_polygon_pts=np.array(slab_cutout_polygon_pts).round(2)
                                                                        #
                                                                        #                 slab_cutout_polygon_points=Polygon(np_slab_cutout_polygon_pts)
                                                                        #
                                                                        #                 #check slabcutoutvoid polygon in special_usebua polygon or not
                                                                        #
                                                                        #                 if terrace_polygon_points.contains(slab_cutout_polygon_points)==True or terrace_polygon_points.touches(slab_cutout_polygon_points)==True or round(terrace_polygon_points.distance(slab_cutout_polygon_points))==0:
                                                                        #
                                                                        #                     slab_cutout_area=round(slab_cutout_polygon_points.area,2)
                                                                        #
                                                                        #                     terrace_slab_cutout_area_list.append(slab_cutout_area)
                                                                        #
                                                                        #         #iterate refuge polygon in refuge_area_polygon_data
                                                                        #
                                                                        #         for refuge_polygon in refuge_area_polygon_data:
                                                                        #
                                                                        #             refuge_polygon_pts=[rp[0:2] for rp in refuge_polygon.get_points()]
                                                                        #
                                                                        #             if len(refuge_polygon_pts)>=3:
                                                                        #
                                                                        #                 np_refuge_polygon_pts=np.array(refuge_polygon_pts).round(2)
                                                                        #
                                                                        #                 refuge_polygon_points=Polygon(np_refuge_polygon_pts)
                                                                        #
                                                                        #                 #check refuge polygon in special_usebua polygon or not
                                                                        #
                                                                        #                 if terrace_polygon_points.contains(refuge_polygon_points)==True or terrace_polygon_points.touches(refuge_polygon_points)==True or round(terrace_polygon_points.distance(refuge_polygon_points))==0:
                                                                        #
                                                                        #                     refuge_area=round(refuge_polygon_points.area,2)
                                                                        #
                                                                        #                     terrace_refuge_area_list.append(refuge_area)
                                                                        #
                                                                        #         # iterate lift polygon in lift_area_polygon_data
                                                                        #
                                                                        #         for lift_polygon in lift_area_polygon_data:
                                                                        #
                                                                        #             lift_polygon_pts = [lp[0:2] for lp in lift_polygon.get_points()]
                                                                        #
                                                                        #             if len(lift_polygon_pts) >=3:
                                                                        #
                                                                        #                 np_lift_polygon_pts = np.array(lift_polygon_pts).round(2)
                                                                        #
                                                                        #                 lift_polygon_points = Polygon(np_lift_polygon_pts)
                                                                        #
                                                                        #                 # check lift polygon in terrace polygon or not
                                                                        #
                                                                        #                 if terrace_polygon_points.contains(lift_polygon_points) == True or terrace_polygon_points.touches(lift_polygon_points) == True or round(terrace_polygon_points.distance(lift_polygon_points)) == 0:
                                                                        #
                                                                        #                     lift_area = round(lift_polygon_points.area,2)
                                                                        #
                                                                        #                     terrace_lift_area_list.append(lift_area)
                                                                        #
                                                                        #         # iterate staircase polygon in staircase_area_polygon_data
                                                                        #
                                                                        #         for staircase_polygon in staircase_area_polygon_data:
                                                                        #
                                                                        #             staircase_polygon_pts = [sp[0:2] for sp in staircase_polygon.get_points()]
                                                                        #
                                                                        #             if len(staircase_polygon_pts) >=3 and staircase_polygon.closed==True:
                                                                        #
                                                                        #                 np_staircase_polygon_pts = np.array(staircase_polygon_pts).round(2)
                                                                        #
                                                                        #                 staircase_polygon_points = Polygon(np_staircase_polygon_pts)
                                                                        #
                                                                        #                 # check staircase polygon in terrace polygon or not
                                                                        #
                                                                        #                 if terrace_polygon_points.contains(staircase_polygon_points) == True or terrace_polygon_points.touches(staircase_polygon_points) == True or round(terrace_polygon_points.distance(staircase_polygon_points)) == 0:
                                                                        #
                                                                        #                     staircase_area = round(staircase_polygon_points.area,2)
                                                                        #
                                                                        #                     terrace_staircase_area_list.append(staircase_area)
                                                                        #
                                                                        #         np_sum_of_terrace_balcony_area=np.sum(terrace_balcony_area_list).round(2)
                                                                        #
                                                                        #         np_sum_of_terrace_accessory_area=np.sum(terrace_accessory_area_list).round(2)
                                                                        #
                                                                        #         np_sum_of_terrace_ventilation_area=np.sum(terrace_ventilation_area_list).round(2)
                                                                        #
                                                                        #         np_sum_of_terrace_slab_cutout_area=np.sum(terrace_slab_cutout_area_list).round(2)
                                                                        #
                                                                        #         np_sum_of_terrace_refuge_area=np.sum(terrace_refuge_area_list).round(2)
                                                                        #
                                                                        #         np_sum_of_terrace_lift_area = np.sum(terrace_lift_area_list).round(2)
                                                                        #
                                                                        #         np_sum_of_terrace_staircase_area = np.sum(terrace_staircase_area_list).round(2)
                                                                        #
                                                                        #         tmpworkdict=dict()
                                                                        #
                                                                        #         tmpworkdict['RESIBUA_ACCESSORY']=np_sum_of_terrace_accessory_area
                                                                        #
                                                                        #         tmpworkdict['RESIBUA_BALCONY']=np_sum_of_terrace_balcony_area
                                                                        #
                                                                        #         tmpworkdict['RESIBUA_VENTILATION_SHAFT']=np_sum_of_terrace_ventilation_area
                                                                        #
                                                                        #         tmpworkdict['RESIBUA_SLAB_CUTOUT_VOID']=np_sum_of_terrace_slab_cutout_area
                                                                        #
                                                                        #         tmpworkdict['RESIBUA_REFUGE_AREA']=np_sum_of_terrace_refuge_area
                                                                        #
                                                                        #         tmpworkdict['RESIBUA_LIFT_AREA'] = np_sum_of_terrace_lift_area
                                                                        #
                                                                        #         tmpworkdict['RESIBUA_STAIRCASE_AREA'] = np_sum_of_terrace_staircase_area
                                                                        #
                                                                        #
                                                                        #         if tmpworkdict!={}:
                                                                        #
                                                                        #             floor_list.append(tmpworkdict)

                                                                        if floor_list != []:
                                                                            floor_dict = dict()
                                                                            floor_dict['BLDG_NAME'] = stripbuilding_name
                                                                            floor_dict['BLDG_REFID'] = building_polygon_id
                                                                            floor_dict['FLOOR'] = floor_name
                                                                            floor_dict['FLOOR_REFID'] = floor_label_id  # floor_polygon_id

                                                                            for dict_data in floor_list:
                                                                                floor_dict.update(dict_data)

                                                                            if floor_dict != {}:
                                                                                resultsList.append(floor_dict)

    except IOError as ioe:
        msg = f'Not a DXF file or a generic I/O error.' + str(ioe) + ' filename ' + ""
        returnValueDict['code'] = 99
        returnValueDict['error'] = msg

        return returnValueDict
    except ezdxf.DXFStructureError as dse:
        msg = f'Invalid or corrupted DXF file.' + str(dse) + ' filename ' + ""
        returnValueDict['code'] = 99
        returnValueDict['error'] = msg

        return returnValueDict

    except UnicodeDecodeError:
        msg = 'Decoding error in DXF file:'
        print(msg)
        returnValueDict['code'] = 99
        returnValueDict['error'] = msg
        return returnValueDict

    returnValueDict['code'] = 0
    returnValueDict['data'] = resultsList
    return returnValueDict

# #
# # -------------------- Input of the file --------------------------------
# # path of the filename
#
# # folder='E:/production_code/dxf_files/Buildings'
# # folder=r"C:\Users\manisha\Desktop\building_height_files(26-11-25)\dxf_files"
# # folder=r"G:/MyProjects/FireBuildingsProject/FireBuildingsAPI/Dxf_files"
# folder="G:/MyProjects/BPConnectProject/BPConnectAPI/DXF_files/"
# # dxf_fileName="1f22ec3cc0dbd001-avenuesmall30426.dxf"
# # #Pass extension - removed inside method
# # folder=r"D:\Code_&_Files_Mahendra_Kumar\ProductionCode & File\DXF_Files\Fire_Building_file\DXF"
# # filename = '72 mts - 100% correct modified new drg-20-02-2025.dxf'  # Here give only filename
# filename = "89245a9a9ef41407-2261_pudadrg_new_final.dxf"  # Here give only filename
# from datetime import datetime
# start_time=datetime.now()
# t1=start_time.strftime("%H:%M:%S")
# first_start_time=datetime.strptime(t1,"%H:%M:%S")
# # #method returns a dict with handle
# dxf_path=os.path.join(folder,filename)
# read_dxf=ezdxf.readfile(dxf_path)
# msp=read_dxf.modelspace()
# response1=check_resibua_and_commbua_tot_area(msp)
# print(response1)
# end_time = datetime.now()
# t2 = end_time.strftime("%H:%M:%S")
# last_end_time = datetime.strptime(t2, "%H:%M:%S")
# total_time = last_end_time - first_start_time
# print(f'first func Total Time is:{total_time}')