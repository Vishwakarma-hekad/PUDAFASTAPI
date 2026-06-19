#Deployed Date 29-4-2026
import os
from shapely import box
from shapely.geometry import Point,Polygon,LineString
import numpy as np
import re
import sys
import ezdxf
from shapely.ops import unary_union,nearest_points
import math
import traceback
import logging
from shapely.ops import linemerge
from shapely.lib import make_valid

# Configure logging once (ideally in main or a config file)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S', # removes milliseconds if not needed
    stream=sys.stdout
)
logging.captureWarnings(True)

class CommonFloorSetbacks:

    def __init__(self, BuildingNameLayerDict, FloorLayerDict, ProposedWorkLayerDict, commbua_Data, resibua_Data,
                 indivbua_Data, specialbua_Data, MarginLayerDict, resibuaDIRREFCircle_data, ParkingLayerDict,
                 OrganizedOpenSpaceDataLayerDict,ExistingStructureDict, PlotDict,flinsectiondict,sectiondict,gl_dict):

        self.BuildingNameLayerDict = BuildingNameLayerDict
        self.FloorLayerDict = FloorLayerDict
        self.ProposedWorkLayerDict = ProposedWorkLayerDict
        self.commbua_Data = commbua_Data
        self.resibua_Data = resibua_Data
        self.indivbua_Data = indivbua_Data
        self.specialbua_Data = specialbua_Data
        self.MarginLayerDict = MarginLayerDict
        self.resibuaDIRREFCircle_data = resibuaDIRREFCircle_data
        self.ParkingLayerDict = ParkingLayerDict
        self.OrganizedOpenSpaceDataLayerDict = OrganizedOpenSpaceDataLayerDict
        self.ExistingStructureDict = ExistingStructureDict
        self.PlotDict = PlotDict
        self.flinsectiondict = flinsectiondict
        self.sectiondict = sectiondict
        self.gl_dict = gl_dict

    def clean_outside_brackets(self, text):
        # Split by parts inside brackets
        parts = re.split(r'(\(.*?\))', text)

        # Process parts outside and inside brackets
        modified_parts = [
            re.sub(r'[^A-Za-z]+', '', part) if not (part.startswith('(') and part.endswith(')')) else part.replace(' ',
                                                                                                                   '')
            for part in parts
        ]

        # Remove spaces inside brackets
        modified_parts = [part if not (part.startswith('(') and part.endswith(')')) else re.sub(r'\s+', '', part) for
                          part in modified_parts]

        return ''.join(modified_parts).strip()

    def point_between_segments(self, pt, pline, mline):
        # Build quadrilateral polygon
        quad = Polygon([pline[0], pline[1], mline[1], mline[0]])

        # Check if point is inside or touches edge
        return quad.contains(Point(pt)) or quad.touches(Point(pt))

    def Bounding_Box_TouchWith_DirectionsLabel(self, ListOfDirectionLabel, MargePolygon):

        proposed_entity = []
        if ListOfDirectionLabel is not None:

            for proposed_label in ListOfDirectionLabel:

                proposed_label_pts = Point([proposed_label.dxf.insert[0], proposed_label.dxf.insert[1]])

                if MargePolygon.touches(proposed_label_pts) == True or round(MargePolygon.distance(proposed_label_pts),
                                                                             1) == 0.0:
                    proposed_entity.append(proposed_label)

        return proposed_entity

    def MergeMultipolygonObject(self, MultiPolygonobject):

        exterior_rings = [polygon.exterior for polygon in MultiPolygonobject.geoms]

        singlepolygon = Polygon(shell=[point for ring in exterior_rings for point in ring.coords])

        return singlepolygon

    def DistPropjoinedtotlot2marginanotherProp(self, totlot_poly, Marginline, ListProposedPoly):

        margin_xpts, margin_ypts = Marginline.coords.xy

        np_margin_line_pts = np.array([[margin_xpts[0], margin_ypts[0]], [margin_xpts[1], margin_ypts[1]]])

        max_margin_line_pts = np_margin_line_pts.max(axis=0)

        min_margin_line_pts = np_margin_line_pts.min(axis=0)

        dist_min_margin_line_pts = max_margin_line_pts - min_margin_line_pts

        totlot_polyboundary = totlot_poly.boundary.coords

        tot_lineb = [LineString(totlot_polyboundary[k:k + 2]) for k in range(len(totlot_polyboundary) - 1)]

        totlot_line_points = [LineString(list(ls.coords)) for ls in tot_lineb]

        totlot_line2margindist = [totlot_line.distance(Marginline) for totlot_line in totlot_line_points]

        if totlot_line2margindist:

            totlottoprop1dist = []

            if dist_min_margin_line_pts[0] > dist_min_margin_line_pts[1]:

                for totlot_linex in totlot_line_points:

                    if round(totlot_linex.distance(Marginline), 1) == round(min(totlot_line2margindist), 1):

                        totlot_ptsX, totlot_ptsY = totlot_linex.coords.xy

                        np_totlot_linepts = np.array([(totlot_ptsX[0], totlot_ptsY[0]), (totlot_ptsX[1], totlot_ptsY[1])])

                        max_np_totlot_linepts = np_totlot_linepts.max(axis=0)

                        min_np_totlot_linepts = np_totlot_linepts.min(axis=0)

                        dist_np_prop_linepts = max_np_totlot_linepts - min_np_totlot_linepts

                        if dist_np_prop_linepts[0] > dist_np_prop_linepts[1]:

                            for proposed1 in ListProposedPoly:

                                list_ofpropline = []

                                proposed1_polyboundary = proposed1[1].boundary.coords

                                proposed1_lineb = [LineString(proposed1_polyboundary[k:k + 2]) for k in
                                                   range(len(proposed1_polyboundary) - 1)]

                                prop_line_points = [list(ls.coords) for ls in proposed1_lineb]

                                for prop1line in prop_line_points:

                                    splitline2points = self.splitLinetopoints(prop1line[0], prop1line[1], 100)

                                    splittotpts = []

                                    for splitpts in splitline2points[10:-10]:

                                        if (max_np_totlot_linepts[0] > splitpts[0] and min_np_totlot_linepts[0] <
                                            splitpts[0]) and (
                                                max_np_totlot_linepts[1] > splitpts[1] and min_np_totlot_linepts[1] <
                                                splitpts[1]):

                                            splittotpts.append(True)

                                        else:

                                            splittotpts.append(False)

                                    list_ofpropline.append(any(splittotpts))

                                if any(list_ofpropline) == True:

                                    p1, p2 = nearest_points(totlot_linex, proposed1[1])
                                    dist = round(p1.distance(p2),2)

                                    if dist > 0.0:
                                        totlottoprop1dist.append((dist, (p1.coords[0], p2.coords[0])))

            elif (dist_min_margin_line_pts[0] < dist_min_margin_line_pts[1]):

                for totlot_linex in totlot_line_points:

                    if round(totlot_linex.distance(Marginline), 1) == round(min(totlot_line2margindist), 1):

                        totlot_ptsX, totlot_ptsY = totlot_linex.coords.xy

                        np_totlot_linepts = np.array(
                            [(totlot_ptsX[0], totlot_ptsY[0]), (totlot_ptsX[1], totlot_ptsY[1])])

                        max_np_totlot_linepts = np_totlot_linepts.max(axis=0)

                        min_np_totlot_linepts = np_totlot_linepts.min(axis=0)

                        dist_np_totlot_linepts = max_np_totlot_linepts - min_np_totlot_linepts

                        if dist_np_totlot_linepts[0] < dist_np_totlot_linepts[1]:

                            for proposed1 in ListProposedPoly:

                                list_ofpropline = []

                                proposed1_polyboundary = proposed1[1].boundary.coords

                                proposed1_lineb = [LineString(proposed1_polyboundary[k:k + 2]) for k in
                                                   range(len(proposed1_polyboundary) - 1)]

                                prop_line_points = [list(ls.coords) for ls in proposed1_lineb]

                                for prop1line in prop_line_points:

                                    splitline2points = self.splitLinetopoints(prop1line[0], prop1line[1], 100)

                                    splittotpts = []

                                    for splitpts in splitline2points[10:-10]:

                                        if (max_np_totlot_linepts[1] > splitpts[1] and min_np_totlot_linepts[1] <
                                            splitpts[
                                                1]) and (
                                                max_np_totlot_linepts[0] > splitpts[0] and min_np_totlot_linepts[0] <
                                                splitpts[0]):

                                            splittotpts.append(True)
                                        else:
                                            splittotpts.append(False)

                                    list_ofpropline.append(splittotpts)

                                if any(list_ofpropline) == True:

                                    p1, p2 = nearest_points(totlot_linex, proposed1[1])
                                    dist = round(p1.distance(p2),2)

                                    if dist > 0.0:
                                        totlottoprop1dist.append((dist, (p1.coords[0], p2.coords[0])))

            if totlottoprop1dist:
                return totlottoprop1dist

    def BounboxNotContainTotLot(self, propsed_poly, ListtotlotPoly):

        BoundboxNotContaintotlot = []

        for totlot_poly in ListtotlotPoly:

            if propsed_poly.contains(totlot_poly) == False and propsed_poly.touches(totlot_poly) == False and round(
                    propsed_poly.distance(totlot_poly), 1) != 0.0:
                BoundboxNotContaintotlot.append(totlot_poly)

        return BoundboxNotContaintotlot

    # common polygon have proposedwork or not
    def BounboxNotContainProp(self, propsed_poly, ListProposedPoly):

        return [proposed1_poly for proposed1_poly in ListProposedPoly
                if round(propsed_poly.distance(proposed1_poly[1]), 1) != 0.0]

    # split points from line
    def splitLinetopoints(self, start, end, seg):  # this function used for Spliting the lines

        x_delta = (end[0] - start[0]) / float(seg)

        y_delta = (end[1] - start[1]) / float(seg)

        points = []

        for i in range(1, seg):
            pts = [start[0] + i * x_delta, start[1] + i * y_delta]

            points.append(pts)

        return [start] + points + [end]

    def DistProp2marginanotherProp(self, proposed_poly, margin_line, list_proposed_polys):

        """
            Find distances from the margin-aligned edge(s) of a proposed polygon
            to other proposed polygons.

            Parameters
            ----------
            proposed_poly : shapely.geometry.Polygon
                The polygon being measured.
            margin_line : shapely.geometry.LineString
                Reference line that defines orientation (horizontal/vertical).
            list_proposed_polys : list of tuple
                Other proposed polygons, given as (id, Polygon).

            Returns
            -------
            list of float
                Non-zero distances between the closest margin-aligned edge of
                `proposed_poly` and overlapping edges of other polygons.
        """

        margin_x, margin_y = margin_line.coords.xy
        np_margin_line_pts = np.array([[margin_x[0], margin_y[0]], [margin_x[1], margin_y[1]]])

        # Determine orientation of the margin line
        max_margin = np_margin_line_pts.max(axis=0)
        min_margin = np_margin_line_pts.min(axis=0)
        margin_span = max_margin - min_margin

        # Get boundary lines of the proposed polygon
        boundary = proposed_poly.boundary
        coords = boundary.coords if boundary.geom_type == "LineString" else boundary.geoms[0].coords
        proposed_lines = [LineString(coords[i:i + 2]) for i in range(len(coords) - 1)]

        # Compute distance of each line segment to the margin
        line_to_margin_dists = [line.distance(margin_line) for line in proposed_lines]

        result_distances = []

        if not line_to_margin_dists:
            return []

        # Determine whether margin is more horizontal or vertical
        horizontal_margin = margin_span[0] > margin_span[1]

        # Find the line(s) on proposed_poly that are closest to the margin
        min_dist = min(line_to_margin_dists)
        closest_lines = [
            line for line, dist in zip(proposed_lines, line_to_margin_dists)
            if round(dist, 1) == round(min_dist, 1)
        ]

        for closest_line in closest_lines:
            line_x, line_y = closest_line.coords.xy
            np_line_pts = np.array([(line_x[0], line_y[0]), (line_x[1], line_y[1])])
            max_line = np_line_pts.max(axis=0)
            min_line = np_line_pts.min(axis=0)
            line_span = max_line - min_line

            line_is_horizontal = line_span[0] > line_span[1]

            # Check if orientation of this line matches the margin
            if line_is_horizontal == horizontal_margin:
                for _, other_poly in list_proposed_polys:
                    other_coords = other_poly.boundary.coords
                    other_lines = [LineString(other_coords[i:i + 2]) for i in range(len(other_coords) - 1)]

                    for segment in other_lines:
                        # Split the other polygon's line into points
                        split_points = self.splitLinetopoints(segment.coords[0], segment.coords[1], 100)

                        # Ignore edge points to avoid boundary artifacts
                        trimmed_points = split_points[10:-10]
                        points_within_bbox = [
                            pt for pt in trimmed_points
                            if min_line[0] < pt[0] < max_line[0] and min_line[1] < pt[1] < max_line[1]
                        ]

                        if points_within_bbox:
                            # Find nearest points between the line and the other polygon
                            p1, p2 = nearest_points(closest_line, other_poly)
                            dist = round(p1.distance(p2),2)

                            if dist > 0.0:
                                result_distances.append((dist, (p1.coords[0], p2.coords[0])))
                                # result_distances.append(dist)

        return result_distances

    def angle_between_lines(self,line1, line2):
        """Return the absolute angle difference (in degrees) between two lines."""

        def line_angle(l):
            x0, y0 = l.coords[0]
            x1, y1 = l.coords[1]
            return np.degrees(np.arctan2(y1 - y0, x1 - x0))

        ang1 = line_angle(line1)
        ang2 = line_angle(line2)
        diff = abs(ang1 - ang2) % 180  # %180 because lines can be opposite
        return min(diff, 180 - diff)  # smallest angle difference

    def DistProp2marginanotherTotLot(self,proposed_poly, margin_line, list_totlot_polys):

        # Get bounding box coordinates
        minx, miny, maxx, maxy = proposed_poly.bounds

        # Create bounding box polygon
        bbox_poly = Polygon([
            (minx, miny),
            (maxx, miny),
            (maxx, maxy),
            (minx, maxy)
        ])
        pt1, pt2 = nearest_points(proposed_poly, margin_line)

        # Step 2: compute vector
        dx = pt2.x - pt1.x
        dy = pt2.y - pt1.y

        # Polygon coordinates as numpy array
        poly_coords = np.array(bbox_poly.exterior.coords)

        # Step 3: check dominant axis
        if abs(dx) >= abs(dy):
            # Extend along x-axis
            # Find two polygon vertices closest to pt1.x
            distances = np.abs(poly_coords[:, 0] - pt1.x)
            nearest_idxs = distances.argsort()[:2]  # two closest points
            nearest_side = poly_coords[nearest_idxs]
            # Build rectangle along x-axis
            min_y_side, max_y_side = nearest_side[:, 1].min(), nearest_side[:, 1].max()
            rectangle_polygon = Polygon([
                (pt1.x, min_y_side),
                (pt2.x, min_y_side),
                (pt2.x, max_y_side),
                (pt1.x, max_y_side)
            ])

        else:

            # Extend along y-axis
            distances = np.abs(poly_coords[:, 1] - pt1.y)
            nearest_idxs = distances.argsort()[:2]
            nearest_side = poly_coords[nearest_idxs]
            min_x_side, max_x_side = nearest_side[:, 0].min(), nearest_side[:, 0].max()
            rectangle_polygon = Polygon([
                (min_x_side, pt1.y),
                (max_x_side, pt1.y),
                (max_x_side, pt2.y),
                (min_x_side, pt2.y)
            ])
        dist_pts = []
        # Get intersecting polygons
        for tot_poly in list_totlot_polys:

            if rectangle_polygon.intersects(tot_poly):

                intersect_polygon = rectangle_polygon.intersection(tot_poly)
                # print("intersection polygon",intersect_polygon)
                p1, p2 = nearest_points(proposed_poly, intersect_polygon)

                dist = round(p1.distance(p2),2)
                pts1 = (p1.x,p1.y)
                pts2 = (p2.x,p2.y)

                if dist > 0.0:
                    dist_pts.append((dist,(pts1,pts2)))

        return dist_pts

    def TotLotJointWidthProposedWork(self, MergedPolygon, TotlotPolygon):

        return [TotlotPoly for TotlotPoly in TotlotPolygon
                if round(MergedPolygon.distance(TotlotPoly), 1) == 0.0]

    # check totlot in plot
    def TotLotINPlot(self, PlotDict, OrganizedOpenSpaceDict, ESDict):

        TotLotINPlot = []

        for Plot_id, PlotNamePoly in PlotDict.items():

            for Org_id, OrgNamePoly in OrganizedOpenSpaceDict.items():

                if ('tot lot' in OrgNamePoly[0].lower()) or ('tot-lot' in OrgNamePoly[0].lower()):

                    if PlotNamePoly[1].contains(OrgNamePoly[1]) == True or PlotNamePoly[1].touches(
                            OrgNamePoly[1]) == True or round(PlotNamePoly[1].distance(OrgNamePoly[1]), 1) == 0.0:
                        TotLotINPlot.append(OrgNamePoly[1])

            for es_id, esnamepoly in ESDict.items():

                if PlotNamePoly[1].contains(esnamepoly[1]) or round(PlotNamePoly[1].distance(esnamepoly[1]), 1) == 0.0:
                    TotLotINPlot.append(esnamepoly[1])

        if TotLotINPlot:
            return TotLotINPlot

    def ParkingINFloor(self, Floor_polygon, list_of_Parking):

        ParkingPolygonContainsFloor = []

        for parking_id, ParkingNamePoly in list_of_Parking.items():
            park_label=ParkingNamePoly[0].lower().replace(" ","")
            if park_label == "parking":

                if Floor_polygon.contains(ParkingNamePoly[1]) == True or Floor_polygon.touches(
                        ParkingNamePoly[1]) == True or round(Floor_polygon.distance(ParkingNamePoly[1]), 1) == 0.0:
                    ParkingPolygonContainsFloor.append(ParkingNamePoly[1])

        if ParkingPolygonContainsFloor != [] and len(ParkingPolygonContainsFloor) > 0:

            return ParkingPolygonContainsFloor[0]

    def ResiDirRefCircleINFloor(self, FloorNamePoly, Resibua_DirRefCircle):

        DirRefCircleInProposedWork = []

        for entity in Resibua_DirRefCircle:

            for ent in entity.virtual_entities():

                if ent.dxftype() == 'CIRCLE':

                    Resibua_center_point = Point(np.array([ent.dxf.center[0], ent.dxf.center[1]]))

                    if FloorNamePoly[1].contains(Resibua_center_point) == True or FloorNamePoly[1].touches(
                            Resibua_center_point) == True or round(FloorNamePoly[1].distance(Resibua_center_point),
                                                                   1) == 0.0:
                        DirRefCircleInProposedWork.append(Resibua_center_point)

        if DirRefCircleInProposedWork != [] and len(DirRefCircleInProposedWork) > 0:

            return DirRefCircleInProposedWork[0]

        else:

            print(f'Missing Resibua Direction Refrence Circle in {FloorNamePoly[0]}')

    def ResiDirRefCircleINProposedWork(self, ProposedWorkNamePoly, Resibua_DirRefCircle):

        DirRefCircleInProposedWork = []

        for entity in Resibua_DirRefCircle:

            for ent in entity.virtual_entities():

                if ent.dxftype() == 'CIRCLE':

                    Resibua_center_point = Point(np.array([ent.dxf.center[0], ent.dxf.center[1]]))

                    if ProposedWorkNamePoly[1].contains(Resibua_center_point) == True or round(
                            ProposedWorkNamePoly[1].distance(Resibua_center_point), 1) == 0.0:
                        DirRefCircleInProposedWork.append(Resibua_center_point)

        if DirRefCircleInProposedWork != [] and len(DirRefCircleInProposedWork) > 0:

            return DirRefCircleInProposedWork[0]

        else:

            print(f'Missing Resibua Direction Refrence Circle in {ProposedWorkNamePoly[0]} ProposedWork Layer.')

    def BUATypeINFloor(self, Floor_polygon, list_of_BUA):
        listBUAinFloor = []

        for Bua in list_of_BUA:

            if Bua is not None:

                for BuaPolygon in Bua:

                    if len([BUAp[0:2] for BUAp in BuaPolygon[0].get_points()]) > 3:

                        bua_polygon = Polygon(np.array([BUAp[0:2] for BUAp in BuaPolygon[0].get_points()]))

                        if Floor_polygon.contains(bua_polygon) == True or Floor_polygon.touches(
                                bua_polygon) == True or round(Floor_polygon.distance(bua_polygon), 1) == 0.0:
                            listBUAinFloor.append(bua_polygon)

        if (len(listBUAinFloor) > 0 and len(listBUAinFloor) < 1) or listBUAinFloor != []:

            return listBUAinFloor[0]

        elif ((listBUAinFloor != [] and len(listBUAinFloor) > 1) or listBUAinFloor != []):

            return unary_union(listBUAinFloor)

    def get_floors_within_5_9m(self, building_poly):

        result = []
        errorResult = []

        for section_id, section_val in self.sectiondict.items():
            section_poly = section_val[1]
            if building_poly.contains(section_poly):
                # Collect floors inside section
                floors = []
                for floor_id, floor_val in self.flinsectiondict.items():
                    if section_poly.contains(floor_val[1]):
                        floors.append((floor_val[0], floor_val[1],floor_val[2]))  # (name, polygon)

                # Collect GL inside section
                gls = []
                for gl_id, gl_val in self.gl_dict.items():
                    if section_poly.contains(gl_val[1]):
                        gls.append(gl_val[1])  # LineString

                if not gls or not floors:
                    continue

                gl_y = gls[0].coords[0][1]  # Use Y of first GL

                list_upper_floor=[]

                for fname,fpoly,fpt in floors:

                    yfpt=fpt.y

                    if yfpt > gl_y:

                        logging.info(f"UPPER FLOOR: {fname}")
                        list_upper_floor.append((fname,fpoly))

                    else:
                        logging.info(f"LOWER FLOOR: {fname}")

                sorted_floors = sorted(list_upper_floor, key=lambda x: x[1].distance(gls[0]))

                if not sorted_floors:

                    Errormsg= "Did Not Found Upper Floors."
                    logging.warning(Errormsg)
                    errorResult.append(Errormsg)

                tot_height = 0.0
                last_y = gl_y

                for sfname,sfpoly in sorted_floors:
                    sfname_clean = sfname.lower()
                    # Skip podium
                    if "podium" in sfname_clean:
                        print(" Skipped (podium):", sfname)
                        continue

                    maxy = sfpoly.bounds[3]
                    height = maxy - last_y

                    clean_name = sfname_clean.replace("floor", "").replace(" ", "")

                    # Skip due to height crossing
                    if tot_height + height > 5.9:
                        print(" Skipped (height limit crossed):", sfname)
                        result.append(clean_name)
                        break

                    tot_height += height

                    result.append(clean_name)
                    last_y = maxy

                    # maxy = sfpoly.bounds[3]
                    # height = maxy - last_y
                    #
                    # tot_height += height
                    # sfname=sfname.lower().replace("floor","").replace(" ","")
                    # result.append(sfname)
                    #
                    # if tot_height > 5.9:
                    #     break
                    #
                    # last_y = maxy

        return result,errorResult

    def checkString4AlphaDigits(self,nameOfFloor: str):

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

        if (isDigits and isAlphaNum and not (isAlpha)):
            return "DIGITS"
        elif ((isAlpha and isAlphaNum) and not (isDigits)):
            return "ONLYTEXT"
        elif (isAlphaNum and not (isDigits and isAlpha)):
            return "ALPHANUM"
        else:
            print("unknown, default to ALPHA ")
            return "ONLYTEXT"

    def determineFloorNumbers(self, nameOfFloor: str):

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

        typeOfString = self.checkString4AlphaDigits(nameOfFloor)  # ALPHA, DIGITS, ALPHANUM

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
                ((list(range(*[int(b) + c for c, b in enumerate(a.split('-'))])) if ('-' in a or ' ' in a) else [a]) for
                 a
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

    def getFloorSebacks(self,default_setbacks):

        returnValueList = []

        try:
            TotLotINPlotList = self.TotLotINPlot(self.PlotDict, self.OrganizedOpenSpaceDataLayerDict,
                                                 self.ExistingStructureDict)

            for ProposedWork_id, ProposedWorkNamePoly in self.ProposedWorkLayerDict.items():

                propresibuaDIRREFCircle = self.ResiDirRefCircleINProposedWork(ProposedWorkNamePoly,
                                                                              self.resibuaDIRREFCircle_data)
                if propresibuaDIRREFCircle:

                    Filter_ProposedWork_Name = self.clean_outside_brackets(ProposedWorkNamePoly[0])

                    for Building_id, BuildingNamePoly in self.BuildingNameLayerDict.items():

                        Filter_Building_Name = self.clean_outside_brackets(BuildingNamePoly[0])

                        if Filter_ProposedWork_Name == Filter_Building_Name:

                            logging.info(f'Matched labels:{(ProposedWorkNamePoly[0], BuildingNamePoly[0])}')

                            getbuildingheight_data, errormsg = self.get_floors_within_5_9m(BuildingNamePoly[1])

                            logging.info(f"Taking Setbacks From {getbuildingheight_data} Floor.")

                            ContainsResiBUAANDPARKING = []

                            for Floor_id, FloorNamePoly in self.FloorLayerDict.items():

                                floor_name = FloorNamePoly[0].lower().replace(" ", "").replace("floorplan", "")

                                if "typical" in floor_name:

                                    typical_floor = sorted(self.determineFloorNumbers(floor_name))

                                    if typical_floor:
                                        floor_name = typical_floor[0].lower()

                                    else:

                                        ErrorMsg = "Does Not Typical extracted properly."
                                        logging.warning(ErrorMsg)
                                        # ErrorReturnValueList.append(ErrorMsg)

                                lower_floor_text = any(
                                    words in FloorNamePoly[0].lower() for words in ['cellar', 'basement'])

                                if not lower_floor_text and any(floor_name in flabel for flabel in getbuildingheight_data):

                                    if BuildingNamePoly[1].contains(FloorNamePoly[1]) or round(
                                            BuildingNamePoly[1].distance(FloorNamePoly[1]), 1) == 0.0:

                                        floorresibuaDIRREFCircle = self.ResiDirRefCircleINFloor(FloorNamePoly,
                                                                                                self.resibuaDIRREFCircle_data)

                                        FloorContainsParking = self.ParkingINFloor(FloorNamePoly[1], self.ParkingLayerDict)

                                        FloorContainsBUA = self.BUATypeINFloor(Floor_polygon=FloorNamePoly[1],
                                                                               list_of_BUA=[self.resibua_Data,
                                                                                            self.commbua_Data,
                                                                                            self.indivbua_Data,
                                                                                            self.specialbua_Data])

                                        propcenter_x, propcenter_y = propresibuaDIRREFCircle.coords.xy

                                        floorcenter_x, floorcenter_y = floorresibuaDIRREFCircle.coords.xy

                                        propFloorCenter_pts = [(propcenter_x[0], propcenter_y[0]),
                                                               (floorcenter_x[0], floorcenter_y[0])]

                                        BothCenter_pts = np.array(propFloorCenter_pts)

                                        maxBothCenter_pts = BothCenter_pts.max(axis=0)

                                        minBothCenter_pts = BothCenter_pts.min(axis=0)

                                        DistProp2FloorCeterpts = maxBothCenter_pts - minBothCenter_pts

                                        # --------------------------------first Quadrant For Floor Center Points--------------------------------

                                        Floorcenterpts1stQuadrant = [round(floorcenter_x[0] + DistProp2FloorCeterpts[0], 3),
                                                                     round(floorcenter_y[0] + DistProp2FloorCeterpts[1], 3)]

                                        # --------------------------------Second Quadrant For Floor Center Points--------------------------------

                                        Floorcenterpts2ndQuadrant = [round(floorcenter_x[0] - DistProp2FloorCeterpts[0], 3),
                                                                     round(floorcenter_y[0] - DistProp2FloorCeterpts[1], 3)]

                                        # --------------------------------Third Quadrant For Floor Center Points--------------------------------

                                        Floorcenterpts3rdQuadrant = [round(floorcenter_x[0] + DistProp2FloorCeterpts[0], 3),
                                                                     round(floorcenter_y[0] - DistProp2FloorCeterpts[1], 3)]

                                        # --------------------------------Fourth Quadrant For Floor Center Points--------------------------------

                                        Floorcenterpts4thQuadrant = [round(floorcenter_x[0] - DistProp2FloorCeterpts[0], 3),
                                                                     round(floorcenter_y[0] + DistProp2FloorCeterpts[1], 3)]

                                        # --------------------------------First Quadrant For Parking layer Resibua layer,Commbua layer--------------------------------

                                        Proposed_WorkCenterPts = [round(propcenter_x[0], 3), round(propcenter_y[0], 3)]

                                        if (Floorcenterpts1stQuadrant == Proposed_WorkCenterPts):

                                            # ---------------------------------Moving Bua Polygon from floor to proposed work for first Quadrant-----------------------------

                                            logging.info('Matched First Quadrant')

                                            if FloorContainsBUA:

                                                Moved_BUAPolygon_pts = []

                                                for BUAX_pts, BUAY_pts in zip(FloorContainsBUA.exterior.xy[0],
                                                                              FloorContainsBUA.exterior.xy[1]):
                                                    BUA_pts = [BUAX_pts + DistProp2FloorCeterpts[0],
                                                               BUAY_pts + DistProp2FloorCeterpts[1]]

                                                    Moved_BUAPolygon_pts.append(BUA_pts)

                                                MovedBuaPolygonPoints = Polygon(np.array(Moved_BUAPolygon_pts))

                                                ContainsResiBUAANDPARKING.append(MovedBuaPolygonPoints)

                                            # ---------------------------------Moving Parking Polygon from floor to proposed work for first Quadrant-----------------------------
                                            if FloorContainsParking:

                                                Moved_ParkingPolygon_pts = []

                                                for ParkingX_pts, ParkingY_pts in zip(FloorContainsParking.exterior.xy[0],
                                                                                      FloorContainsParking.exterior.xy[1]):
                                                    Parking_pts = [ParkingX_pts + DistProp2FloorCeterpts[0],
                                                                   ParkingY_pts + DistProp2FloorCeterpts[1]]

                                                    Moved_ParkingPolygon_pts.append(Parking_pts)

                                                MovedParkingPolygonPoints = Polygon(np.array(Moved_ParkingPolygon_pts))

                                                ContainsResiBUAANDPARKING.append(MovedParkingPolygonPoints)

                                        elif (Floorcenterpts2ndQuadrant == Proposed_WorkCenterPts):

                                            logging.info('Matched Second Quadrant')

                                            # ---------------------------------Moving Bua Polygon from floor to proposed work for Second Quadrant-----------------------------
                                            if FloorContainsBUA:

                                                Moved_BUAPolygon_pts = []

                                                for BUAX_pts, BUAY_pts in zip(FloorContainsBUA.exterior.xy[0],
                                                                              FloorContainsBUA.exterior.xy[1]):
                                                    BUA_pts = [BUAX_pts - DistProp2FloorCeterpts[0],
                                                               BUAY_pts - DistProp2FloorCeterpts[1]]

                                                    Moved_BUAPolygon_pts.append(BUA_pts)

                                                MovedBuaPolygonPoints = Polygon(np.array(Moved_BUAPolygon_pts))

                                                ContainsResiBUAANDPARKING.append(MovedBuaPolygonPoints)

                                            # ---------------------------------Moving Parking Polygon from floor to proposed work for Second Quadrant-----------------------------
                                            if FloorContainsParking:

                                                Moved_ParkingPolygon_pts = []

                                                for ParkingX_pts, ParkingY_pts in zip(FloorContainsParking.exterior.xy[0],
                                                                                      FloorContainsParking.exterior.xy[1]):
                                                    Parking_pts = [ParkingX_pts - DistProp2FloorCeterpts[0],
                                                                   ParkingY_pts - DistProp2FloorCeterpts[1]]

                                                    Moved_ParkingPolygon_pts.append(Parking_pts)

                                                MovedParkingPolygonPoints = Polygon(np.array(Moved_ParkingPolygon_pts))

                                                ContainsResiBUAANDPARKING.append(MovedParkingPolygonPoints)


                                        elif (Floorcenterpts3rdQuadrant == Proposed_WorkCenterPts):

                                            logging.info('Matched Third Quadrant')

                                            # ---------------------------------Moving Bua Polygon from floor to proposed work for Second Quadrant-----------------------------
                                            if FloorContainsBUA:

                                                Moved_BUAPolygon_pts = []

                                                for BUAX_pts, BUAY_pts in zip(FloorContainsBUA.exterior.xy[0],
                                                                              FloorContainsBUA.exterior.xy[1]):
                                                    BUA_pts = [BUAX_pts + DistProp2FloorCeterpts[0],
                                                               BUAY_pts - DistProp2FloorCeterpts[1]]

                                                    Moved_BUAPolygon_pts.append(BUA_pts)

                                                MovedBuaPolygonPoints = Polygon(np.array(Moved_BUAPolygon_pts))

                                                ContainsResiBUAANDPARKING.append(MovedBuaPolygonPoints)

                                            # ---------------------------------Moving Parking Polygon from floor to proposed work for Second Quadrant-----------------------------

                                            if FloorContainsParking:

                                                Moved_ParkingPolygon_pts = []

                                                for ParkingX_pts, ParkingY_pts in zip(FloorContainsParking.exterior.xy[0],
                                                                                      FloorContainsParking.exterior.xy[1]):
                                                    Parking_pts = [ParkingX_pts + DistProp2FloorCeterpts[0],
                                                                   ParkingY_pts - DistProp2FloorCeterpts[1]]

                                                    Moved_ParkingPolygon_pts.append(Parking_pts)

                                                MovedParkingPolygonPoints = Polygon(np.array(Moved_ParkingPolygon_pts))

                                                ContainsResiBUAANDPARKING.append(MovedParkingPolygonPoints)


                                        elif (Floorcenterpts4thQuadrant == Proposed_WorkCenterPts):

                                            logging.info('Matched Fourth Quadrant')

                                            # ---------------------------------Moving Bua Polygon from floor to proposed work for Second Quadrant-----------------------------
                                            if FloorContainsBUA:

                                                Moved_BUAPolygon_pts = []

                                                for BUAX_pts, BUAY_pts in zip(FloorContainsBUA.exterior.xy[0],
                                                                              FloorContainsBUA.exterior.xy[1]):
                                                    BUA_pts = [BUAX_pts - DistProp2FloorCeterpts[0],
                                                               BUAY_pts + DistProp2FloorCeterpts[1]]

                                                    Moved_BUAPolygon_pts.append(BUA_pts)

                                                MovedBuaPolygonPoints = Polygon(np.array(Moved_BUAPolygon_pts))

                                                ContainsResiBUAANDPARKING.append(MovedBuaPolygonPoints)

                                            # ---------------------------------Moving Parking Polygon from floor to proposed work for Second Quadrant-----------------------------

                                            if FloorContainsParking:

                                                Moved_ParkingPolygon_pts = []

                                                for ParkingX_pts, ParkingY_pts in zip(FloorContainsParking.exterior.xy[0],
                                                                                      FloorContainsParking.exterior.xy[1]):
                                                    Parking_pts = [ParkingX_pts - DistProp2FloorCeterpts[0],
                                                                   ParkingY_pts + DistProp2FloorCeterpts[1]]

                                                    Moved_ParkingPolygon_pts.append(Parking_pts)

                                                MovedParkingPolygonPoints = Polygon(np.array(Moved_ParkingPolygon_pts))

                                                ContainsResiBUAANDPARKING.append(MovedParkingPolygonPoints)

                                        else:

                                            logging.warning('Does Not Matched in Any Quadrant')

                            ContainsResiBUAANDPARKING.append(ProposedWorkNamePoly[1])
                            fixed_geometries = [resiparkxgeom.buffer(0) for resiparkxgeom in ContainsResiBUAANDPARKING]
                            xMergeMultiPolygons = unary_union(fixed_geometries)

                            MergeMultiPolygons = xMergeMultiPolygons if xMergeMultiPolygons.geom_type == 'Polygon' else self.MergeMultipolygonObject(
                                xMergeMultiPolygons)

                            sidesOfPolygonDict = dict()

                            if TotLotINPlotList:

                                totjoinedWithprop = self.TotLotJointWidthProposedWork(MergeMultiPolygons, TotLotINPlotList)

                                BoundingBoxNotContainprop = self.BounboxNotContainProp(MergeMultiPolygons,
                                                                                       self.ProposedWorkLayerDict.values())

                                BoundingBoxNotContaintotlot = self.BounboxNotContainTotLot(MergeMultiPolygons,
                                                                                           TotLotINPlotList)

                                for Margin_side, Margin_lines in self.MarginLayerDict.items():

                                    SidesOFValue = []

                                    sideline = linemerge(Margin_lines)

                                    if sideline.geom_type == "MultiLineString":

                                        sideline = LineString([pt for geom in sideline.geoms for pt in geom.coords])


                                    prop_Between_prop2margin = self.DistProp2marginanotherProp(MergeMultiPolygons,
                                                                                               sideline,
                                                                           BoundingBoxNotContainprop)

                                    if prop_Between_prop2margin:
                                        SidesOFValue.append(
                                            min(prop_Between_prop2margin,key=lambda x: x[0]))

                                    tlES_Between_Margin2Prop = self.DistProp2marginanotherTotLot(MergeMultiPolygons,
                                                                                                 sideline,
                                                                          BoundingBoxNotContaintotlot)

                                    if tlES_Between_Margin2Prop:
                                        SidesOFValue.append(
                                            min(tlES_Between_Margin2Prop,key=lambda x: x[0]))

                                    if totjoinedWithprop:

                                        propjoinedtotlotsetbacks = []

                                        for totlot_polygon in totjoinedWithprop:

                                            tlES_JoinedWITH_prop2Anotherprop = self.DistPropjoinedtotlot2marginanotherProp(totlot_polygon, sideline,
                                                                                           BoundingBoxNotContainprop)

                                            if tlES_JoinedWITH_prop2Anotherprop:
                                                propjoinedtotlotsetbacks.append(
                                                    min(tlES_JoinedWITH_prop2Anotherprop,key=lambda x: x[0]))

                                            tlES_JoinedWITH_prop2AnothertlES=self.DistProp2marginanotherTotLot(totlot_polygon,
                                                                                                               sideline,
                                                                                                               BoundingBoxNotContaintotlot)

                                            if tlES_JoinedWITH_prop2AnothertlES:
                                                propjoinedtotlotsetbacks.append(
                                                    min(tlES_JoinedWITH_prop2AnothertlES,key=lambda x: x[0]))

                                            pjt1, pjt2 = nearest_points(totlot_polygon, sideline)
                                            propjoinedtotlotsetbacks.append((round(pjt1.distance(pjt2),2), (pjt1.coords[0], pjt2.coords[0])))

                                            if propjoinedtotlotsetbacks:
                                                SidesOFValue.append(min(propjoinedtotlotsetbacks,key=lambda x: x[0]))

                                    p1, p2 = nearest_points(MergeMultiPolygons, sideline)
                                    SidesOFValue.append((round(p1.distance(p2),2), (p1.coords[0], p2.coords[0])))

                                    if SidesOFValue:
                                        sidesOfPolygonDict[str(Margin_side)] = min(SidesOFValue,key=lambda x: x[0])

                            else:

                                sidesOfPolygonDict = dict()

                                BoundingBoxNotContainprop = self.BounboxNotContainProp(MergeMultiPolygons,
                                                                                       self.ProposedWorkLayerDict.values())

                                for Margin_side, Margin_lines in self.MarginLayerDict.items():

                                    SidesOFValue = []

                                    sideline = linemerge(Margin_lines)

                                    if sideline.geom_type == "MultiLineString":
                                        sideline = LineString([pt for geom in sideline.geoms for pt in geom.coords])

                                    prop_between_prop2margin1 = self.DistProp2marginanotherProp(MergeMultiPolygons, sideline,
                                                                       BoundingBoxNotContainprop)

                                    if prop_between_prop2margin1:
                                        SidesOFValue.append(
                                            min(prop_between_prop2margin1,key=lambda x: x[0]))

                                    pt1, pt2 = nearest_points(MergeMultiPolygons, sideline)
                                    SidesOFValue.append(
                                        (round(pt1.distance(pt2),2), (pt1.coords[0], pt2.coords[0])))

                                    if SidesOFValue:
                                        sidesOfPolygonDict[str(Margin_side)] = min(SidesOFValue,key=lambda x: x[0])

                            if sidesOfPolygonDict:

                                if default_setbacks:

                                    if default_setbacks.get("FRONT_VALUE") and default_setbacks.get("FRONT_PTS"):

                                        sidesOfPolygonDict["FRONT"] = (default_setbacks.get("FRONT_VALUE"),default_setbacks.get("FRONT_PTS"))

                                    if default_setbacks.get("REAR_VALUE") and default_setbacks.get("REAR_PTS"):

                                        sidesOfPolygonDict["REAR"] = (default_setbacks.get("REAR_VALUE"), default_setbacks.get("REAR_PTS"))

                                    if default_setbacks.get("SIDE1_VALUE") and default_setbacks.get("SIDE1_PTS"):

                                        sidesOfPolygonDict["SIDE1"] = (
                                        default_setbacks.get("SIDE1_VALUE"), default_setbacks.get("SIDE1_PTS"))

                                    if default_setbacks.get("SIDE2_VALUE") and default_setbacks.get("SIDE2_PTS"):

                                        sidesOfPolygonDict["SIDE2"] = (
                                        default_setbacks.get("SIDE2_VALUE"), default_setbacks.get("SIDE2_PTS"))

                                returnValueList.append(sidesOfPolygonDict)

                            break
        except Exception as e:
            logging.error(e)
            pass

        return returnValueList

class Dim_TD_and_DC:

    def __init__(self, b_id, b_name, f_id, f_name, f_poly, st_data, p_data, ft_data, fd_data):
        self.b_id = b_id
        self.b_name = b_name
        self.f_id = f_id
        self.f_name = f_name
        self.f_poly = f_poly
        self.st_data = st_data
        self.p_data = p_data
        self.ft_data = ft_data
        self.fd_data = fd_data

    def stair_touch_passage(self, stair_polygon, stair_id, stair_label, fd_points):

        passage_min_map = {}  # keep only min distance per passage

        for passage_id, passage_values in self.p_data.items():
            passage_polygon = passage_values[1]

            if self.f_poly.contains(passage_polygon):

                for point, poly_p, name in fd_points:

                    # Case 1: Staircase is very close to passage (<= 0.4m)
                    # Case 2: Fire door point directly touches passage
                    if round(stair_polygon.distance(passage_polygon), 1) <= 0.4 or (
                            point and round(point.distance(passage_polygon), 1) == 0.0):
                        # Extract passage center line points
                        center_line_pts = [xy[0:2] for xy in passage_values[2].get_points()]

                        min_stair_pt = None  # Closest point on stair polygon
                        min_dist = float("inf")  # Minimum distance
                        min_center_pts = None
                        if point is None:
                            # Case: Stair polygon → Passage centerline distance
                            for cpts in center_line_pts:
                                center_point = Point(cpts)
                                dist = stair_polygon.distance(center_point)
                                if dist < min_dist:
                                    min_dist = dist
                                    # Interpolate to find exact nearest point on stair boundary
                                    min_stair_pt = stair_polygon.exterior.interpolate(
                                        stair_polygon.exterior.project(center_point)
                                    )
                                    min_stair_pt = Point((min_stair_pt.x, min_stair_pt.y))  # always tuple
                                    min_center_pts = Point((center_point.x, center_point.y))
                        else:
                            # Case: Fire door point → Passage centerline distance
                            for cpts1 in center_line_pts:
                                center_point1 = Point(cpts1)
                                dist1 = point.distance(center_point1)
                                if dist1 < min_dist:
                                    min_dist = dist1
                                    min_stair_pt = point
                                    min_stair_pt = Point((min_stair_pt.x, min_stair_pt.y))  # always tuple
                                    min_center_pts = center_point1


                        # If a valid minimum point and distance found
                        if min_stair_pt and min_dist != float("inf"):
                            dc_res = {
                                "BLDG_ID": self.b_id,
                                "BLDG_LABEL": self.b_name,
                                "FLOOR_ID": self.f_id,
                                "FLOOR_LABEL": self.f_name,
                                "STAIR_ID": stair_id,
                                "STAIR_LABEL": stair_label,
                                "PASSAGE_ID": passage_id,
                                "PASSAGE_LABEL": passage_values[0],
                                "DC_DISTANCE": str(round(min_dist, 2)),
                                "START_POINT":min_stair_pt,
                                "END_POINT":min_center_pts
                            }

                            # Keep only the smallest distance per passage
                            if (
                                    passage_id not in passage_min_map
                                    or float(dc_res["DC_DISTANCE"]) < float(passage_min_map[passage_id]["DC_DISTANCE"])
                            ):
                                passage_min_map[passage_id] = dc_res

        # Return only the most minimum per passage
        stair_touch_passage = list(passage_min_map.values())
        return stair_touch_passage

    def stair_in_ftower(self, stair_polygon):
        fire_doors = []
        ft_polygon = None

        for ft_values in self.ft_data.values():
            if ft_values[-1].contains(stair_polygon) or round(ft_values[-1].distance(stair_polygon), 1) == 0.0:

                ft_polygon = ft_values[-1]

        if ft_polygon:
            for fd_values in self.fd_data.values():
                fd_label = fd_values[0].lower().replace(" ", "")

                if "firedoor" in fd_label or "exitdoor" in fd_label or "fireeixtdoor" in fd_label:
                    if round(ft_polygon.distance(fd_values[1]), 1) == 0.0:

                        fire_doors.append([fd_values[-2], fd_values[1], fd_label])


            return fire_doors, ft_polygon

        return fire_doors, ft_polygon

    def firedoor_touch_stair(self, stair_polygon):
        """Check if fire door touches staircase directly (when no fire tower)."""
        fire_doors = []
        stair_list = []

        for fd_values in self.fd_data.values():
            fd_label = fd_values[0].lower().replace(" ", "")

            if "firedoor" in fd_label or "exitdoor" in fd_label or "fireeixtdoor" in fd_label:

                if stair_polygon.contains(fd_values[1]) or round(stair_polygon.distance(fd_values[1]), 1) == 0.0:

                    fire_doors.append([fd_values[-2], fd_values[1], fd_label])

        # Return fire doors if found, else empty list
        return fire_doors if fire_doors else stair_list

    def get_dc(self):
        td_and_dc_map = {}  # Store minimum DC result per passag

        for stair_id,stair_values in self.st_data.items():
            stair_polygon = stair_values[1]
            # Ensure the staircase lies within the floor boundary
            if self.f_poly.contains(stair_polygon):
                fd_points, ft_polygon = self.stair_in_ftower(stair_polygon)

                if fd_points:
                    stair_data = self.stair_touch_passage(ft_polygon, stair_id, stair_values[0], fd_points)

                else:
                    fd_points_direct = self.firedoor_touch_stair(stair_polygon)
                    stair_data = []

                    if fd_points_direct:
                        # Found direct fire door connection
                        stair_data = self.stair_touch_passage(stair_polygon, stair_id, stair_values[0], fd_points_direct)
                    else:

                        # Case 3: No fire tower & no fire door — check staircase directly with passages
                        for passage_id, passage_values in self.p_data.items():
                            passage_polygon = passage_values[1]
                            # Only check passages inside this floor and near stair (<= 0.4m)
                            if self.f_poly.contains(passage_polygon) and round(stair_polygon.distance(passage_polygon),
                                                                               1) <= 0.4:
                                # Measure distance between stair and passage centerline
                                center_line_pts = [xy[0:2] for xy in passage_values[2].get_points()]
                                min_dist = float("inf")
                                center_pt = None
                                stair_pt = None
                                for cpts in center_line_pts:
                                    center_point = Point(cpts)
                                    dist = stair_polygon.distance(center_point)
                                    if dist < min_dist:
                                        min_dist = dist
                                        center_pt = center_point
                                        min_stair_pt = stair_polygon.exterior.interpolate(
                                            stair_polygon.exterior.project(center_point)
                                        )
                                        stair_pt = Point((min_stair_pt.x, min_stair_pt.y))

                                if min_dist != float("inf"):
                                    dc_res = {
                                        "BLDG_ID": self.b_id,
                                        "BLDG_LABEL": self.b_name,
                                        "FLOOR_ID": self.f_id,
                                        "FLOOR_LABEL": self.f_name,
                                        "STAIR_ID": stair_id,
                                        "STAIR_LABEL": stair_values[0],
                                        "PASSAGE_ID": passage_id,
                                        "PASSAGE_LABEL": passage_values[0],
                                        "DC_DISTANCE": str(round(min_dist, 2)),
                                        "START_POINT": stair_pt,
                                        "END_POINT": center_pt
                                    }

                                    # Keep only minimum DC distance per passage
                                    if (
                                            passage_id not in td_and_dc_map
                                            or float(dc_res["DC_DISTANCE"]) < float(
                                        td_and_dc_map[passage_id]["DC_DISTANCE"])
                                    ):
                                        td_and_dc_map[passage_id] = dc_res

                for res in stair_data:
                    pid = res["PASSAGE_ID"]
                    if pid not in td_and_dc_map or float(res["DC_DISTANCE"]) < float(td_and_dc_map[pid]["DC_DISTANCE"]):
                        td_and_dc_map[pid] = res

        point_list=[]
        for res in td_and_dc_map.values():
            td_and_dc=(res.get("START_POINT"),res.get('END_POINT'))
            point_list.append(td_and_dc)
        # print('---',self.f_name,point_list)
        return point_list

class MODYFY_DXF:

    def CalculateWidthOFPolygon(self,polygon_pts,center_line_pts):

        center_line_pts=[[center_line_pts[i], center_line_pts[i + 1]] for i in range(len(center_line_pts) - 1)]

        polygon_line_pts = [[polygon_pts[i], polygon_pts[i + 1]] for i in range(len(polygon_pts) - 1)]

        polygon_width=[]

        for center_line in center_line_pts:

            center_line_points=LineString(center_line)

            for polygon_line in polygon_line_pts:

                polygon_line_points=LineString(polygon_line)

                if round(center_line_points.distance(polygon_line_points))!=0:

                    polygon_width.append(round(center_line_points.distance(polygon_line_points),2)*2)

        return min(polygon_width)

    def add_area_text(self, msp, text, layer_name, insert_point,
                      height, width_factor, color=1):

        txt = msp.add_text(text, dxfattribs={
            "style": "OpenSans",
            "layer": str(layer_name),
            "color": color,
            "height": height,
            "width": width_factor,
        })

        # Set text insertion point
        txt.dxf.insert = insert_point

        return txt

    def add_aligned_dim_entity(self, msp, dim_start_pts, dim_end_pts, dist, dim_text,
                               lname, lcolor, dim_h, dimasz,style):

        override = {
            "dimtxt": dim_h,
            "dimasz": dimasz,
            "dimclrd": lcolor,
            "dimclrt": 0,
            "dimtxsty": "Standard",
            "dimscale": 1,
            "dimexo": 0.0,
            "dimexe": 0.0,
        }

        dim = msp.add_aligned_dim(
            p1=dim_start_pts,
            p2=dim_end_pts,
            distance=dist,
            text=str(dim_text),
            dimstyle=style,
            dxfattribs={"layer": lname, "color": lcolor},
            override=override,
        )

        return dim

    def split(self,start, end, seg):  # this function used for Spliting the lines

        x_delta = (end[0] - start[0]) / float(seg)

        y_delta = (end[1] - start[1]) / float(seg)

        points = []

        for i in range(1, seg):

            pts = [start[0] + i * x_delta, start[1] + i * y_delta]

            points.append(pts)

        return [start] + points + [end]

    def clean_specialChars(self,inputName: str):

        if (inputName is None or len(inputName) == 0):

            return ''

        inputName = inputName.replace(' ', '_')
        inputName = inputName.replace('(', '')
        inputName = inputName.replace(')', '')
        inputName = inputName.replace('[', '')
        inputName = inputName.replace(']', '')
        inputName = inputName.replace(',', '')
        inputName = inputName.replace("'", "")
        inputName = inputName.replace('"', '')
        inputName = inputName.replace('-', '_')
        inputName = inputName.replace('%%U', '_')
        inputName = inputName.replace('%U', '_')
        inputName = inputName.replace('%', '_')

        return inputName

    def proposed_to_TOTLOT_dist(self,organized_openspace_data_list,plot_polygon_points,prop_entity,polygon_points,prop_polygon_tot):

         final_min_tot_2_prop_pts = []

         for organized_open_space_text in organized_openspace_data_list:

            if organized_open_space_text.dxftype() == 'TEXT' or organized_open_space_text.dxftype() == 'MTEXT':

                organized_open_space_attribs = organized_open_space_text.dxfattribs()

                organized_open_space_name = organized_open_space_attribs.get('text',organized_open_space_text.dxf.text) if organized_open_space_text.dxftype() == 'TEXT' else organized_open_space_text.plain_text()

                if ('TOT-LOT' in organized_open_space_name) or ('Tot-Lot' in organized_open_space_name) or ('Tot-lot' in organized_open_space_name) or ('tot-lot' in organized_open_space_name) or ('Tot lot' in organized_open_space_name) or ('tot lot' in organized_open_space_name):

                    organized_open_space_insert = organized_open_space_attribs.get('insert')

                    organized_open_space_insert_pts = [organized_open_space_insert[0],organized_open_space_insert[1]]

                    np_organized_open_space_insert_pts = np.array(organized_open_space_insert_pts)

                    organized_open_space_text_point = Point(np_organized_open_space_insert_pts)

                    for organized_open_space_polygon in organized_openspace_data_list:

                        if organized_open_space_polygon.dxftype() == 'LWPOLYLINE':

                            organized_open_space_polygon_pts = [op[0:2] for op in organized_open_space_polygon.get_points()]

                            if len(organized_open_space_polygon_pts) <= 2:
                                continue

                            np_organized_open_space_polygon_pts = np.array(organized_open_space_polygon_pts)

                            organized_open_space_polygon_points = Polygon(np_organized_open_space_polygon_pts)

                            if organized_open_space_polygon_points.contains(organized_open_space_text_point)  or organized_open_space_polygon_points.touches(organized_open_space_text_point)  or round(organized_open_space_polygon_points.distance(organized_open_space_text_point),1)==0.0:

                                if organized_open_space_polygon_points.touches(polygon_points) != True and round(organized_open_space_polygon_points.distance(polygon_points),1) != 0.0:

                                    if plot_polygon_points.contains(organized_open_space_polygon_points)  or plot_polygon_points.touches(organized_open_space_polygon_points)  or round(plot_polygon_points.distance(organized_open_space_polygon_points),1) == 0.0:

                                        if prop_polygon_tot>1:

                                            prop_distance_line_pts = []

                                            prop_distance_line_value = []

                                            for prop_line in prop_entity.virtual_entities():

                                                if prop_line.dxftype() == 'LINE':

                                                    prop_line_start_pts = [prop_line.dxf.start[0],prop_line.dxf.start[1]]

                                                    prop_line_end_pts = [prop_line.dxf.end[0],prop_line.dxf.end[1]]

                                                    prop_line_pts = [prop_line_start_pts,prop_line_end_pts]

                                                    prop_line_points = LineString(prop_line_pts)

                                                    tot_lot_distance_line_pts = []

                                                    tot_lot_distance_line_value = []

                                                    for tot_lot_line in organized_open_space_polygon.virtual_entities():

                                                        if tot_lot_line.dxftype()=='LINE':

                                                            tot_lot_line_start_pts = [tot_lot_line.dxf.start[0],tot_lot_line.dxf.start[1]]

                                                            tot_lot_line_end_pts = [tot_lot_line.dxf.end[0],tot_lot_line.dxf.end[1]]

                                                            tot_lot_line_pts = [tot_lot_line_start_pts,tot_lot_line_end_pts]

                                                            tot_lot_line_points = LineString(tot_lot_line_pts)

                                                            if round(prop_line_points.distance(tot_lot_line_points)) != 0:

                                                                tot_lot_distance_line_pts.append([prop_line_pts,tot_lot_line_pts])

                                                                tot_lot_distance_line_value.append(round(prop_line_points.distance(tot_lot_line_points),2))

                                                        elif(tot_lot_line.dxftype()=='ARC'):

                                                            tot_lot_arc_start_pts = [tot_lot_line.start_point[0],tot_lot_line.start_point[1]]

                                                            tot_lot_arc_end_pts = [tot_lot_line.end_point[0],tot_lot_line.end_point[1]]

                                                            tot_lot_arc_pts = [tot_lot_arc_start_pts,tot_lot_arc_end_pts]

                                                            tot_lot_arc_points = LineString(tot_lot_arc_pts)

                                                            if round(prop_line_points.distance(tot_lot_arc_points)) != 0:

                                                                tot_lot_distance_line_pts.append([prop_line_pts, tot_lot_arc_pts])

                                                                tot_lot_distance_line_value.append(round(prop_line_points.distance(tot_lot_arc_points), 2))

                                                    if tot_lot_distance_line_pts != []:

                                                        for tot_line_pts in tot_lot_distance_line_pts:

                                                            tot_line_points1 = LineString(tot_line_pts[0])

                                                            tot_line_points2 = LineString(tot_line_pts[1])

                                                            if round(tot_line_points1.distance(tot_line_points2),2) == min(tot_lot_distance_line_value):

                                                                prop_distance_line_pts.append(tot_line_pts)

                                                                prop_distance_line_value.append(round(tot_line_points1.distance(tot_line_points2),2))

                                            if prop_distance_line_pts != []:

                                                duplicate_line_pts = []

                                                duplicate_line_value = []

                                                for prop_dist_line_pts in prop_distance_line_pts:

                                                    prop_line_points1 = LineString(prop_dist_line_pts[0])

                                                    prop_line_points2 = LineString(prop_dist_line_pts[1])

                                                    if round(prop_line_points1.distance(prop_line_points2),2) == min(prop_distance_line_value):

                                                        duplicate_line_pts.append(prop_dist_line_pts)

                                                        duplicate_line_value.append(round(prop_line_points1.distance(prop_line_points2),2))

                                                if duplicate_line_pts != []:

                                                    split_line_pts1 = self.split(duplicate_line_pts[0][0][0],duplicate_line_pts[0][0][1], 20)

                                                    split_line_pts2 = self.split(duplicate_line_pts[0][1][0],duplicate_line_pts[0][1][1], 20)

                                                    tot_prop_line_distance_value = []

                                                    tot_prop_line_distance_pts = []

                                                    for prop_line1 in split_line_pts1:

                                                        prop_line1_point1 = Point(prop_line1)

                                                        for prop_line2 in split_line_pts2:

                                                            prop_line2_point2 = Point(prop_line2)

                                                            tot_prop_line_distance_value.append(round(prop_line1_point1.distance(prop_line2_point2),2))

                                                            tot_prop_line_distance_pts.append([prop_line1,prop_line2])

                                                    if tot_prop_line_distance_pts != []:

                                                        duplicate_pts = []

                                                        duplicate_value = []

                                                        for prop_pts in tot_prop_line_distance_pts:

                                                            tot_prop_point1 = Point(prop_pts[0])

                                                            tot_prop_point2 = Point(prop_pts[1])

                                                            if round(tot_prop_point1.distance(tot_prop_point2),2) == min(tot_prop_line_distance_value):

                                                                duplicate_pts.append(prop_pts)

                                                                duplicate_value.append(round(tot_prop_point1.distance(tot_prop_point2),2))

                                                        if duplicate_pts != []:

                                                            final_min_tot_2_prop_pts.append([duplicate_pts[0][0],duplicate_pts[0][1]])
                                        else:

                                            prop_distance_line_pts = []

                                            prop_distance_line_value = []

                                            for prop_line in prop_entity.virtual_entities():

                                                if prop_line.dxftype() == 'LINE':

                                                    prop_line_start_pts = [prop_line.dxf.start[0],prop_line.dxf.start[1]]

                                                    prop_line_end_pts = [prop_line.dxf.end[0],prop_line.dxf.end[1]]

                                                    prop_line_pts = [prop_line_start_pts,prop_line_end_pts]

                                                    prop_line_points = LineString(prop_line_pts)

                                                    tot_lot_distance_line_pts = []

                                                    tot_lot_distance_line_value = []

                                                    for tot_lot_line in organized_open_space_polygon.virtual_entities():

                                                        if tot_lot_line.dxftype()=='LINE':

                                                            tot_lot_line_start_pts = [tot_lot_line.dxf.start[0],tot_lot_line.dxf.start[1]]

                                                            tot_lot_line_end_pts = [tot_lot_line.dxf.end[0],tot_lot_line.dxf.end[1]]

                                                            tot_lot_line_pts = [tot_lot_line_start_pts,tot_lot_line_end_pts]

                                                            tot_lot_line_points = LineString(tot_lot_line_pts)

                                                            if round(prop_line_points.distance(tot_lot_line_points)) != 0:

                                                                tot_lot_distance_line_pts.append([prop_line_pts,tot_lot_line_pts])

                                                                tot_lot_distance_line_value.append(round(prop_line_points.distance(tot_lot_line_points),2))

                                                        elif(tot_lot_line.dxftype()=='ARC'):

                                                            tot_lot_arc_start_pts = [tot_lot_line.start_point[0],tot_lot_line.start_point[1]]

                                                            tot_lot_arc_end_pts = [tot_lot_line.end_point[0],tot_lot_line.end_point[1]]

                                                            tot_lot_arc_pts = [tot_lot_arc_start_pts,tot_lot_arc_end_pts]

                                                            tot_lot_arc_points = LineString(tot_lot_arc_pts)

                                                            if round(prop_line_points.distance(tot_lot_arc_points)) != 0:

                                                                tot_lot_distance_line_pts.append([prop_line_pts, tot_lot_arc_pts])

                                                                tot_lot_distance_line_value.append(round(prop_line_points.distance(tot_lot_arc_points), 2))

                                                    if tot_lot_distance_line_pts != []:

                                                        for tot_line_pts in tot_lot_distance_line_pts:

                                                            tot_line_points1 = LineString(tot_line_pts[0])

                                                            tot_line_points2 = LineString(tot_line_pts[1])

                                                            if round(tot_line_points1.distance(tot_line_points2),2) == min(tot_lot_distance_line_value):

                                                                prop_distance_line_pts.append(tot_line_pts)

                                                                prop_distance_line_value.append(round(tot_line_points1.distance(tot_line_points2),2))

                                            if prop_distance_line_pts != []:

                                                duplicate_line_pts = []

                                                duplicate_line_value = []

                                                for prop_dist_line_pts in prop_distance_line_pts:

                                                    prop_line_points1 = LineString(prop_dist_line_pts[0])

                                                    prop_line_points2 = LineString(prop_dist_line_pts[1])

                                                    if round(prop_line_points1.distance(prop_line_points2),2) == min(prop_distance_line_value):

                                                        duplicate_line_pts.append(prop_dist_line_pts)

                                                        duplicate_line_value.append(round(prop_line_points1.distance(prop_line_points2),2))

                                                if duplicate_line_pts != []:

                                                    split_line_pts1 = self.split(duplicate_line_pts[0][0][0],duplicate_line_pts[0][0][1], 20)

                                                    split_line_pts2 = self.split(duplicate_line_pts[0][1][0],duplicate_line_pts[0][1][1], 20)

                                                    tot_prop_line_distance_value = []

                                                    tot_prop_line_distance_pts = []

                                                    for prop_line1 in split_line_pts1:

                                                        prop_line1_point1 = Point(prop_line1)

                                                        for prop_line2 in split_line_pts2:

                                                            prop_line2_point2 = Point(prop_line2)

                                                            tot_prop_line_distance_value.append(round(prop_line1_point1.distance(prop_line2_point2),2))

                                                            tot_prop_line_distance_pts.append([prop_line1,prop_line2])

                                                    if tot_prop_line_distance_pts != []:

                                                        duplicate_pts = []

                                                        duplicate_value = []

                                                        for prop_pts in tot_prop_line_distance_pts:

                                                            tot_prop_point1 = Point(prop_pts[0])

                                                            tot_prop_point2 = Point(prop_pts[1])

                                                            if round(tot_prop_point1.distance(tot_prop_point2),2) == min(tot_prop_line_distance_value):

                                                                duplicate_pts.append(prop_pts)

                                                                duplicate_value.append(round(tot_prop_point1.distance(tot_prop_point2),2))

                                                        if duplicate_pts != []:

                                                            final_min_tot_2_prop_pts.append([duplicate_pts[0][0],duplicate_pts[0][1]])
         return final_min_tot_2_prop_pts

    def proposed_to_proposed_dist(self,entities,polygon_points,prop_entity):

         for prop1_entity in entities:

            if prop1_entity.dxftype() == 'LWPOLYLINE':

                prop1_polygon_pts = [pp[0:2] for pp in prop1_entity.get_points()]

                if len(prop1_polygon_pts)<=2:
                    continue

                prop1_polygon_points = Polygon(prop1_polygon_pts)

                if polygon_points.contains(prop1_polygon_points) != True and polygon_points.touches(prop1_polygon_points) != True and round(polygon_points.distance(prop1_polygon_points)) != 0:

                    prop_line_distance_value = []

                    prop_line_distance_pts = []

                    for prop_line in prop_entity.virtual_entities():

                        if prop_line.dxftype() == 'LINE':

                            prop_line_start_pts = [prop_line.dxf.start[0],prop_line.dxf.start[1]]

                            prop_line_end_pts = [prop_line.dxf.end[0],prop_line.dxf.end[1]]

                            prop_line_pts = [prop_line_start_pts,prop_line_end_pts]

                            prop_line_points = LineString(prop_line_pts)

                            prop1_line_distance_value = []

                            prop1_line_distance_pts = []

                            for prop1_line in prop1_entity.virtual_entities():

                                if prop1_line.dxftype() == 'LINE':

                                    prop1_line_start_pts = [prop1_line.dxf.start[0],prop1_line.dxf.start[1]]

                                    prop1_line_end_pts = [prop1_line.dxf.end[0],prop1_line.dxf.end[1]]

                                    prop1_line_pts = [prop1_line_start_pts,prop1_line_end_pts]

                                    prop1_line_points = LineString(prop1_line_pts)

                                    if round(prop_line_points.distance(prop1_line_points)) != 0:

                                        prop1_line_distance_value.append(round(prop_line_points.distance(prop1_line_points),2))

                                        prop1_line_distance_pts.append([prop_line_pts, prop1_line_pts])

                            if prop1_line_distance_pts != []:

                                for prop_line_p in prop1_line_distance_pts:

                                    prop_linex_pts = LineString(prop_line_p[0])

                                    prop_liney_pts = LineString(prop_line_p[1])

                                    if round(prop_linex_pts.distance(prop_liney_pts),2) == min(prop1_line_distance_value):

                                        prop_line_distance_value.append(round(prop_linex_pts.distance(prop_liney_pts),2))

                                        prop_line_distance_pts.append(prop_line_p)

                    if prop_line_distance_pts != []:

                        duplicate_line_pts = []

                        duplicate_line_value = []

                        for tot_prop_line in prop_line_distance_pts:

                            tot_prop_line_point1 = LineString(tot_prop_line[0])

                            tot_prop_line_point2 = LineString(tot_prop_line[1])

                            if round(tot_prop_line_point1.distance(tot_prop_line_point2),2) == min(prop_line_distance_value):

                                duplicate_line_pts.append(tot_prop_line)

                                duplicate_line_value.append(round(tot_prop_line_point1.distance(tot_prop_line_point2),2))

                        if duplicate_line_pts != []:

                            split_line_pts1 = self.split(duplicate_line_pts[0][0][0],duplicate_line_pts[0][0][1],20)

                            split_line_pts2 = self.split(duplicate_line_pts[0][1][0],duplicate_line_pts[0][1][1],20)

                            tot_prop_line_distance_value = []

                            tot_prop_line_distance_pts = []

                            for prop_line1 in split_line_pts1:

                                prop_line1_point1 = Point(prop_line1)

                                for prop_line2 in split_line_pts2:

                                    prop_line2_point2 = Point(prop_line2)

                                    tot_prop_line_distance_value.append(round(prop_line1_point1.distance(prop_line2_point2),2))

                                    tot_prop_line_distance_pts.append([prop_line1, prop_line2])

                            if tot_prop_line_distance_pts != []:

                                duplicate_pts = []

                                duplicate_value = []

                                for prop_pts in tot_prop_line_distance_pts:

                                    tot_prop_point1 = Point(prop_pts[0])

                                    tot_prop_point2 = Point(prop_pts[1])

                                    if round(tot_prop_point1.distance(tot_prop_point2),2) == min(tot_prop_line_distance_value):

                                        duplicate_pts.append(prop_pts)

                                        duplicate_value.append(round(tot_prop_point1.distance(tot_prop_point2),2))

                                if duplicate_pts != []:

                                    return [duplicate_pts[0][0],duplicate_pts[0][1]]

    def proposed_to_margin_dist(self,prop_entity,margin_data_list,plot_polygon_points,):

         all_side_min_dim=[]

         prop_front_min_distance_value0 = []

         front_proposed_polygon_pts0 = []

         prop_front_min_distance_value1 = []

         front_proposed_polygon_pts1 = []

         prop_rear_min_distance_value0 = []

         rear_proposed_polygon_pts0 = []

         prop_rear_min_distance_value1 = []

         rear_proposed_polygon_pts1 = []

         prop_side1_min_distance_value0 = []

         side1_proposed_polygon_pts0 = []

         prop_side1_min_distance_value1 = []

         side1_proposed_polygon_pts1 = []

         prop_side2_min_distance_value0 = []

         side2_proposed_polygon_pts0 = []

         prop_side2_min_distance_value1 = []

         side2_proposed_polygon_pts1 = []

         for prop_line_entity in prop_entity.virtual_entities():

            if prop_line_entity.dxftype() == 'LINE':

                prop_line_entity_start_pts = [prop_line_entity.dxf.start[0],prop_line_entity.dxf.start[1]]

                prop_line_entity_end_pts = [prop_line_entity.dxf.end[0],prop_line_entity.dxf.end[1]]

                prop_line_pts = [prop_line_entity_start_pts,prop_line_entity_end_pts]

                prop_line_points = LineString(prop_line_pts)

                for margin_entity in margin_data_list:

                    if margin_entity.dxftype() == 'INSERT':

                        front_line_distance_value = []

                        front_distance_of_line_pts = []

                        rear_distance_of_line_pts = []

                        rear_line_distance_value = []

                        side1_distance_of_line_pts = []

                        side1_line_distance_value = []

                        side2_distance_of_line_pts = []

                        side2_line_distance_value = []

                        for vir_entity in margin_entity.virtual_entities():

                            if vir_entity.dxftype() == 'LINE':

                                if vir_entity.dxf.color == 1:

                                    front_line_start_pts = [vir_entity.dxf.start[0],vir_entity.dxf.start[1]]

                                    front_line_end_pts = [vir_entity.dxf.end[0],vir_entity.dxf.end[1]]

                                    front_line_pts = [front_line_start_pts,front_line_end_pts]

                                    front_line_points = LineString(front_line_pts)

                                    if plot_polygon_points.contains(front_line_points)  or plot_polygon_points.touches(front_line_points)  or round(plot_polygon_points.distance(front_line_points)) == 0:

                                        front_distance_of_line_pts.append([prop_line_pts, front_line_pts])

                                        front_line_distance_value.append(round(prop_line_points.distance(front_line_points),2))

                                if vir_entity.dxf.color == 6:

                                    rear_line_start_pts = [vir_entity.dxf.start[0],vir_entity.dxf.start[1]]

                                    rear_line_end_pts = [vir_entity.dxf.end[0],vir_entity.dxf.end[1]]

                                    rear_line_pts = [rear_line_start_pts,rear_line_end_pts]

                                    rear_line_points = LineString(rear_line_pts)

                                    if plot_polygon_points.contains(rear_line_points)  or plot_polygon_points.touches(rear_line_points)  or round(plot_polygon_points.distance(rear_line_points)) == 0:

                                        rear_distance_of_line_pts.append([prop_line_pts, rear_line_pts])

                                        rear_line_distance_value.append(round(prop_line_points.distance(rear_line_points),2))

                                if vir_entity.dxf.color == 104:

                                    side1_line_start_pts = [vir_entity.dxf.start[0],vir_entity.dxf.start[1]]

                                    side1_line_end_pts = [vir_entity.dxf.end[0],vir_entity.dxf.end[1]]

                                    side1_line_pts = [side1_line_start_pts,side1_line_end_pts]

                                    side1_line_points = LineString(side1_line_pts)

                                    if plot_polygon_points.contains(side1_line_points)  or plot_polygon_points.touches(side1_line_points)  or round(plot_polygon_points.distance(side1_line_points)) == 0:

                                        side1_distance_of_line_pts.append([prop_line_pts, side1_line_pts])

                                        side1_line_distance_value.append(round(prop_line_points.distance(side1_line_points),2))

                                if vir_entity.dxf.color == 5:

                                    side2_line_start_pts = [vir_entity.dxf.start[0],vir_entity.dxf.start[1]]

                                    side2_line_end_pts = [vir_entity.dxf.end[0],vir_entity.dxf.end[1]]

                                    side2_line_pts = [side2_line_start_pts,side2_line_end_pts]

                                    side2_line_points = LineString(side2_line_pts)

                                    if plot_polygon_points.contains(side2_line_points)  or plot_polygon_points.touches(side2_line_points)  or round(plot_polygon_points.distance(side2_line_points)) == 0:

                                        side2_distance_of_line_pts.append([prop_line_pts, side2_line_pts])

                                        side2_line_distance_value.append(round(prop_line_points.distance(side2_line_points),2))

                        if front_distance_of_line_pts != []:

                            for line_pts in front_distance_of_line_pts:

                                line1_points = LineString(line_pts[0])

                                line2_points = LineString(line_pts[1])

                                pdata = sorted(set(front_line_distance_value))

                                if round(line1_points.distance(line2_points),2) == pdata[0]:

                                    prop_front_min_distance_value0.append(pdata[0])

                                    front_proposed_polygon_pts0.append([line_pts[0], line_pts[1]])

                                elif round(line1_points.distance(line2_points),2) == pdata[1]:

                                    prop_front_min_distance_value1.append(pdata[1])

                                    front_proposed_polygon_pts1.append([line_pts[0], line_pts[1]])

                        if rear_distance_of_line_pts != []:

                            for line_pts in rear_distance_of_line_pts:

                                line1_points = LineString(line_pts[0])

                                line2_points = LineString(line_pts[1])

                                pdata = sorted(set(rear_line_distance_value))

                                if round(line1_points.distance(line2_points),2) == pdata[0]:

                                    prop_rear_min_distance_value0.append(pdata[0])

                                    rear_proposed_polygon_pts0.append([line_pts[0], line_pts[1]])

                                elif round(line1_points.distance(line2_points),2) == pdata[1]:

                                    prop_rear_min_distance_value1.append(pdata[1])

                                    rear_proposed_polygon_pts1.append([line_pts[0], line_pts[1]])

                        if side1_distance_of_line_pts != []:

                            for line_pts in side1_distance_of_line_pts:

                                line1_points = LineString(line_pts[0])

                                line2_points = LineString(line_pts[1])

                                pdata = sorted(set(side1_line_distance_value))

                                if round(line1_points.distance(line2_points),2) == pdata[0]:

                                    prop_side1_min_distance_value0.append(pdata[0])

                                    side1_proposed_polygon_pts0.append([line_pts[0], line_pts[1]])

                                elif (round(line1_points.distance(line2_points),2) == pdata[1]):

                                    prop_side1_min_distance_value1.append(pdata[1])

                                    side1_proposed_polygon_pts1.append([line_pts[0], line_pts[1]])

                        if side2_distance_of_line_pts != []:

                            for line_pts in side2_distance_of_line_pts:

                                line1_points = LineString(line_pts[0])

                                line2_points = LineString(line_pts[1])

                                pdata = sorted(set(side2_line_distance_value))

                                if round(line1_points.distance(line2_points),2) == pdata[0]:

                                    prop_side2_min_distance_value0.append(pdata[0])

                                    side2_proposed_polygon_pts0.append([line_pts[0], line_pts[1]])

                                elif round(line1_points.distance(line2_points),2) == pdata[1]:

                                    prop_side2_min_distance_value1.append(pdata[1])

                                    side2_proposed_polygon_pts1.append([line_pts[0],line_pts[1]])

         if front_proposed_polygon_pts0 != []:

            duplicate_line_pts = []

            for prop_linex in front_proposed_polygon_pts0:

                prop_line1 = LineString(prop_linex[0])

                prop_line2 = LineString(prop_linex[1])

                xdata = sorted(set(prop_front_min_distance_value0))

                if round(prop_line1.distance(prop_line2),2) == xdata[0]:

                    duplicate_line_pts.append([prop_linex[0], prop_linex[1]])

            if duplicate_line_pts != []:

                min_prop_line_split_data = self.split(duplicate_line_pts[0][0][0],duplicate_line_pts[0][0][1], 50)

                min_margin_line_split_data = self.split(duplicate_line_pts[0][1][0],duplicate_line_pts[0][1][1], 50)

                point_distance = []

                point_pts_data = []

                for prop_pts in min_prop_line_split_data:

                    prop_line_point = Point(prop_pts)

                    for margin_pts in min_margin_line_split_data:

                        margin_line_point = Point(margin_pts)

                        point_distance.append(round(prop_line_point.distance(margin_line_point), 2))

                        point_pts_data.append([prop_pts, margin_pts])

                final_point_data = []

                final_distance = []

                for point in point_pts_data:

                    prop_point1 = Point(point[0])

                    prop_point2 = Point(point[1])

                    if round(prop_point1.distance(prop_point2), 2) == min(point_distance):

                        final_point_data.append([point[0], point[1]])

                if final_point_data!=[]:

                    all_side_min_dim.append([final_point_data[0][0],final_point_data[0][1]])

         if front_proposed_polygon_pts1 != []:

            duplicate_line_pts = []

            for prop_linex in front_proposed_polygon_pts1:

                prop_line1 = LineString(prop_linex[0])

                prop_line2 = LineString(prop_linex[1])

                xdata = sorted(set(prop_front_min_distance_value1))

                if round(prop_line1.distance(prop_line2),2) == xdata[0]:

                    duplicate_line_pts.append([prop_linex[0], prop_linex[1]])

            if duplicate_line_pts != []:

                min_prop_line_split_data = self.split(duplicate_line_pts[0][0][0],duplicate_line_pts[0][0][1], 50)

                min_margin_line_split_data = self.split(duplicate_line_pts[0][1][0],duplicate_line_pts[0][1][1], 50)

                point_distance = []

                point_pts_data = []

                for prop_pts in min_prop_line_split_data:

                    prop_line_point = Point(prop_pts)

                    for margin_pts in min_margin_line_split_data:

                        margin_line_point = Point(margin_pts)

                        point_distance.append(round(prop_line_point.distance(margin_line_point), 2))

                        point_pts_data.append([prop_pts, margin_pts])

                final_point_data = []

                final_distance = []

                for point in point_pts_data:

                    prop_point1 = Point(point[0])

                    prop_point2 = Point(point[1])

                    if round(prop_point1.distance(prop_point2), 2) == min(point_distance):

                        final_point_data.append([point[0], point[1]])

                        final_distance.append(min(point_distance))

                if final_point_data!=[]:

                    all_side_min_dim.append([final_point_data[0][0],final_point_data[0][1]])

         if rear_proposed_polygon_pts0 != []:

            duplicate_line_pts = []

            for prop_linex in rear_proposed_polygon_pts0:

                prop_line1 = LineString(prop_linex[0])

                prop_line2 = LineString(prop_linex[1])

                xdata=sorted(set(prop_rear_min_distance_value0))

                if round(prop_line1.distance(prop_line2),2) == xdata[0]:

                    duplicate_line_pts.append([prop_linex[0], prop_linex[1]])

            if duplicate_line_pts != []:

                min_prop_line_split_data = self.split(duplicate_line_pts[0][0][0],duplicate_line_pts[0][0][1], 50)

                min_margin_line_split_data = self.split(duplicate_line_pts[0][1][0],duplicate_line_pts[0][1][1], 50)

                point_distance = []

                point_pts_data = []

                for prop_pts in min_prop_line_split_data:

                    prop_line_point = Point(prop_pts)

                    for margin_pts in min_margin_line_split_data:

                        margin_line_point = Point(margin_pts)

                        point_distance.append(round(prop_line_point.distance(margin_line_point),2))

                        point_pts_data.append([prop_pts, margin_pts])

                final_point_data = []

                final_distance = []

                for point in point_pts_data:

                    prop_point1 = Point(point[0])

                    prop_point2 = Point(point[1])

                    if round(prop_point1.distance(prop_point2), 2) == min(point_distance):

                        final_point_data.append([point[0], point[1]])

                        final_distance.append(min(point_distance))

                if final_point_data!=[]:

                    all_side_min_dim.append([final_point_data[0][0],final_point_data[0][1]])

         if rear_proposed_polygon_pts1 != []:

            duplicate_line_pts = []

            for prop_linex in rear_proposed_polygon_pts1:

                prop_line1 = LineString(prop_linex[0])

                prop_line2 = LineString(prop_linex[1])

                xdata=sorted(set(prop_rear_min_distance_value1))

                if round(prop_line1.distance(prop_line2),2) == xdata[0]:

                    duplicate_line_pts.append([prop_linex[0], prop_linex[1]])

            if duplicate_line_pts != []:

                min_prop_line_split_data = self.split(duplicate_line_pts[0][0][0],duplicate_line_pts[0][0][1], 50)

                min_margin_line_split_data = self.split(duplicate_line_pts[0][1][0],duplicate_line_pts[0][1][1], 50)

                point_distance = []

                point_pts_data = []

                for prop_pts in min_prop_line_split_data:

                    prop_line_point = Point(prop_pts)

                    for margin_pts in min_margin_line_split_data:

                        margin_line_point = Point(margin_pts)

                        point_distance.append(round(prop_line_point.distance(margin_line_point), 2))

                        point_pts_data.append([prop_pts, margin_pts])

                final_point_data = []

                final_distance = []

                for point in point_pts_data:

                    prop_point1 = Point(point[0])

                    prop_point2 = Point(point[1])

                    if round(prop_point1.distance(prop_point2), 2) == min(point_distance):

                        final_point_data.append([point[0], point[1]])

                        final_distance.append(min(point_distance))

                if final_point_data!=[]:

                    all_side_min_dim.append([final_point_data[0][0],final_point_data[0][1]])

         if side1_proposed_polygon_pts0 != []:

            duplicate_line_pts = []

            for prop_linex in side1_proposed_polygon_pts0:

                prop_line1 = LineString(prop_linex[0])

                prop_line2 = LineString(prop_linex[1])

                xdata = sorted(set(prop_side1_min_distance_value0))

                if round(prop_line1.distance(prop_line2),2) == xdata[0]:

                    duplicate_line_pts.append([prop_linex[0], prop_linex[1]])

            if duplicate_line_pts != []:

                min_prop_line_split_data = self.split(duplicate_line_pts[0][0][0],duplicate_line_pts[0][0][1], 50)

                min_margin_line_split_data = self.split(duplicate_line_pts[0][1][0],duplicate_line_pts[0][1][1], 50)

                point_distance = []

                point_pts_data = []

                for prop_pts in min_prop_line_split_data:

                    prop_line_point = Point(prop_pts)

                    for margin_pts in min_margin_line_split_data:

                        margin_line_point = Point(margin_pts)

                        point_distance.append(round(prop_line_point.distance(margin_line_point), 2))

                        point_pts_data.append([prop_pts, margin_pts])

                final_point_data = []

                final_distance = []

                for point in point_pts_data:

                    prop_point1 = Point(point[0])

                    prop_point2 = Point(point[1])

                    if round(prop_point1.distance(prop_point2), 2) == min(point_distance):

                        final_point_data.append([point[0], point[1]])

                        final_distance.append(min(point_distance))

                if final_point_data!=[]:

                    all_side_min_dim.append([final_point_data[0][0],final_point_data[0][1]])

         if side1_proposed_polygon_pts1 != []:

            duplicate_line_pts = []

            for prop_linex in side1_proposed_polygon_pts1:

                prop_line1 = LineString(prop_linex[0])

                prop_line2 = LineString(prop_linex[1])

                xdata = sorted(set(prop_side1_min_distance_value1))

                if round(prop_line1.distance(prop_line2),2) == xdata[0]:

                    duplicate_line_pts.append([prop_linex[0], prop_linex[1]])

            if duplicate_line_pts != []:

                min_prop_line_split_data = self.split(duplicate_line_pts[0][0][0],duplicate_line_pts[0][0][1], 50)

                min_margin_line_split_data = self.split(duplicate_line_pts[0][1][0],duplicate_line_pts[0][1][1], 50)

                point_distance = []

                point_pts_data = []

                for prop_pts in min_prop_line_split_data:

                    prop_line_point = Point(prop_pts)

                    for margin_pts in min_margin_line_split_data:

                        margin_line_point = Point(margin_pts)

                        point_distance.append(round(prop_line_point.distance(margin_line_point), 2))

                        point_pts_data.append([prop_pts, margin_pts])

                final_point_data = []

                final_distance = []

                for point in point_pts_data:

                    prop_point1 = Point(point[0])

                    prop_point2 = Point(point[1])

                    if round(prop_point1.distance(prop_point2), 2) == min(point_distance):

                        final_point_data.append([point[0], point[1]])

                        final_distance.append(min(point_distance))

                if final_point_data!=[]:

                    all_side_min_dim.append([final_point_data[0][0],final_point_data[0][1]])

         if side2_proposed_polygon_pts0 != []:

            duplicate_line_pts = []

            for prop_linex in side2_proposed_polygon_pts0:

                prop_line1 = LineString(prop_linex[0])

                prop_line2 = LineString(prop_linex[1])

                xdata = sorted(set(prop_side2_min_distance_value0))

                if round(prop_line1.distance(prop_line2),2) == xdata[0]:

                    duplicate_line_pts.append([prop_linex[0], prop_linex[1]])

            if duplicate_line_pts != []:

                min_prop_line_split_data = self.split(duplicate_line_pts[0][0][0],duplicate_line_pts[0][0][1], 50)

                min_margin_line_split_data = self.split(duplicate_line_pts[0][1][0],duplicate_line_pts[0][1][1], 50)

                point_distance = []

                point_pts_data = []

                for prop_pts in min_prop_line_split_data:

                    prop_line_point = Point(prop_pts)

                    for margin_pts in min_margin_line_split_data:

                        margin_line_point = Point(margin_pts)

                        point_distance.append(round(prop_line_point.distance(margin_line_point), 2))

                        point_pts_data.append([prop_pts, margin_pts])

                final_point_data = []

                final_distance = []

                for point in point_pts_data:

                    prop_point1 = Point(point[0])

                    prop_point2 = Point(point[1])

                    if round(prop_point1.distance(prop_point2), 2) == min(point_distance):

                        final_point_data.append([point[0], point[1]])

                        final_distance.append(min(point_distance))

                if final_point_data!=[]:

                    all_side_min_dim.append([final_point_data[0][0],final_point_data[0][1]])

         if side2_proposed_polygon_pts1 != []:

            duplicate_line_pts = []

            for prop_linex in side2_proposed_polygon_pts1:

                prop_line1 = LineString(prop_linex[0])

                prop_line2 = LineString(prop_linex[1])

                xdata = sorted(set(prop_side2_min_distance_value1))

                if round(prop_line1.distance(prop_line2),2) == xdata[0]:

                    duplicate_line_pts.append([prop_linex[0], prop_linex[1]])

            if duplicate_line_pts != []:

                min_prop_line_split_data = self.split(duplicate_line_pts[0][0][0],duplicate_line_pts[0][0][1], 50)

                min_margin_line_split_data = self.split(duplicate_line_pts[0][1][0],duplicate_line_pts[0][1][1], 50)

                point_distance = []

                point_pts_data = []

                for prop_pts in min_prop_line_split_data:

                    prop_line_point = Point(prop_pts)

                    for margin_pts in min_margin_line_split_data:

                        margin_line_point = Point(margin_pts)

                        point_distance.append(round(prop_line_point.distance(margin_line_point), 2))

                        point_pts_data.append([prop_pts, margin_pts])

                final_point_data = []

                final_distance = []

                for point in point_pts_data:

                    prop_point1 = Point(point[0])

                    prop_point2 = Point(point[1])

                    if round(prop_point1.distance(prop_point2), 2) == min(point_distance):

                        final_point_data.append([point[0], point[1]])

                        final_distance.append(min(point_distance))

                if final_point_data!=[]:

                    all_side_min_dim.append([final_point_data[0][0],final_point_data[0][1]])

         return all_side_min_dim
    #Use for upper floor like ex:- FIRST,SECOND or TYPICAL

    def get_unique_line_segments(self,entity):
        segments = []
        for line in entity.virtual_entities():
            if line.dxftype() == "LINE":
                start = (round(line.dxf.start[0], 4), round(line.dxf.start[1], 4))
                end = (round(line.dxf.end[0], 4), round(line.dxf.end[1], 4))

                # Normalize order so duplicates are removed
                seg = tuple(sorted([start, end]))
                segments.append(seg)

        # Deduplicate
        return list(set(segments))

    def ScallingForUpperFloor(self,msp,group,floor_polygon_points):
        all_dims = []
        for lname, entities in group.items():

            if lname in ("_Lift","_ArchProjection","_Balcony","_Pathway","_Room","_StairCase"):

                for entity in entities:

                    if (entity.dxftype() == 'LWPOLYLINE'):

                        entity_polygon_pts = [ep[0:2] for ep in entity.get_points()]

                        np_entity_polygon_pts = np.array(entity_polygon_pts)

                        if entity.is_closed:

                            if len(np_entity_polygon_pts) > 2:

                                entity_polygon_points = Polygon(np_entity_polygon_pts)

                                if floor_polygon_points.contains(entity_polygon_points):

                                    segments = self.get_unique_line_segments(entity)

                                    for seg in segments:
                                        p1, p2 = seg

                                        length = LineString([p1, p2]).length

                                        # choose dimension size
                                        if length > 1:
                                            dim1 = self.add_aligned_dim_entity(
                                                    msp,
                                                    dim_start_pts=p1,
                                                    dim_end_pts=p2,
                                                    dist=0.08,
                                                    dim_text=round(length, 2),
                                                    lname=lname,
                                                    lcolor=0,
                                                    dim_h=0.05,
                                                    dimasz=0.03,
                                                    style = "EZDXF_L"
                                                )
                                            all_dims.append(dim1)
                                        else:
                                            if round(length) > 0:
                                                dim2 = self.add_aligned_dim_entity(
                                                    msp,
                                                    dim_start_pts=p1,
                                                    dim_end_pts=p2,
                                                    dist=0.08,
                                                    dim_text=round(length, 2),
                                                    lname=lname,
                                                    lcolor=0,
                                                    dim_h=0.03,
                                                    dimasz=0.02,
                                                    style="EZDXF_M"
                                                )
                                                all_dims.append(dim2)

                        else:

                            if len(np_entity_polygon_pts) == 4:

                                polygon_points = Polygon(np_entity_polygon_pts)

                                if floor_polygon_points.contains(polygon_points):

                                    segments = self.get_unique_line_segments(entity)

                                    for seg in segments:
                                        p1, p2 = seg

                                        length = LineString([p1, p2]).length

                                        # choose dimension size
                                        if length > 1:
                                            dim1 = self.add_aligned_dim_entity(
                                                msp,
                                                dim_start_pts=p1,
                                                dim_end_pts=p2,
                                                dist=0.08,
                                                dim_text=round(length, 2),
                                                lname=lname,
                                                lcolor=0,
                                                dim_h=0.05,
                                                dimasz=0.03,
                                                style="EZDXF_L"
                                            )
                                            all_dims.append(dim1)
                                        else:
                                            if round(length) > 0:
                                                dim2 = self.add_aligned_dim_entity(
                                                    msp,
                                                    dim_start_pts=p1,
                                                    dim_end_pts=p2,
                                                    dist=0.08,
                                                    dim_text=round(length, 2),
                                                    lname=lname,
                                                    lcolor=0,
                                                    dim_h=0.03,
                                                    dimasz=0.02,
                                                    style="EZDXF_M"
                                                )
                                                all_dims.append(dim2)

                            elif (len(np_entity_polygon_pts) >= 3):

                                entity_polygon_pts = Polygon(np_entity_polygon_pts)

                                if floor_polygon_points.contains(entity_polygon_pts):

                                    segments = self.get_unique_line_segments(entity)

                                    for seg in segments:
                                        p1, p2 = seg

                                        length = LineString([p1, p2]).length

                                        # choose dimension size
                                        if length > 1:
                                            dim1 = self.add_aligned_dim_entity(
                                                msp,
                                                dim_start_pts=p1,
                                                dim_end_pts=p2,
                                                dist=0.08,
                                                dim_text=round(length, 2),
                                                lname=lname,
                                                lcolor=0,
                                                dim_h=0.05,
                                                dimasz=0.03,
                                                style="EZDXF_L"
                                            )
                                            all_dims.append(dim1)
                                        else:
                                            if round(length) > 0:
                                                dim2 = self.add_aligned_dim_entity(
                                                    msp,
                                                    dim_start_pts=p1,
                                                    dim_end_pts=p2,
                                                    dist=0.08,
                                                    dim_text=round(length, 2),
                                                    lname=lname,
                                                    lcolor=0,
                                                    dim_h=0.03,
                                                    dimasz=0.02,
                                                    style="EZDXF_M"
                                                )
                                                all_dims.append(dim2)

                            else:

                                line_points = LineString(np_entity_polygon_pts)

                                if floor_polygon_points.contains(line_points):

                                    segments = self.get_unique_line_segments(entity)

                                    for seg in segments:
                                        p1, p2 = seg

                                        length = LineString([p1, p2]).length

                                        # choose dimension size
                                        if length > 1:
                                            dim1 = self.add_aligned_dim_entity(
                                                msp,
                                                dim_start_pts=p1,
                                                dim_end_pts=p2,
                                                dist=0.08,
                                                dim_text=round(length, 2),
                                                lname=lname,
                                                lcolor=0,
                                                dim_h=0.05,
                                                dimasz=0.03,
                                                style="EZDXF_L"
                                            )
                                            all_dims.append(dim1)
                                        else:

                                            if round(length) > 0:
                                                dim2 = self.add_aligned_dim_entity(
                                                    msp,
                                                    dim_start_pts=p1,
                                                    dim_end_pts=p2,
                                                    dist=0.08,
                                                    dim_text=round(length, 2),
                                                    lname=lname,
                                                    lcolor=0,
                                                    dim_h=0.03,
                                                    dimasz=0.02,
                                                    style="EZDXF_M"
                                                )
                                                all_dims.append(dim2)

                    elif (entity.dxftype() == 'LINE'):

                        line_start_pts = [entity.dxf.start[0], entity.dxf.start[1]]

                        line_end_pts = [entity.dxf.end[0], entity.dxf.end[1]]

                        line_pts = [line_start_pts, line_end_pts]

                        np_line_pts = np.array(line_pts)

                        line_length = LineString(np_line_pts).length

                        if round(line_length) > 1:

                            all_dims.append(self.add_aligned_dim_entity(
                                msp,
                                dim_start_pts=np_line_pts[0],
                                dim_end_pts=np_line_pts[1],
                                dist=0.08,
                                dim_text=round(line_length, 2),
                                lname=lname,
                                lcolor=0,
                                dim_h=0.05,
                                dimasz=0.03,
                                style="EZDXF_L"
                            ))

                        else:

                            if round(line_length) > 0:
                                all_dims.append(self.add_aligned_dim_entity(
                                    msp,
                                    dim_start_pts=np_line_pts[0],
                                    dim_end_pts=np_line_pts[1],
                                    dist=0.05,
                                    dim_text=round(line_length, 2),
                                    lname=lname,
                                    lcolor=0,
                                    dim_h=0.03,
                                    dimasz=0.02,
                                    style="EZDXF_M"
                                ))

            elif (lname == "_Passage" or lname == "_Ramp"):

                for entity in entities:

                    if (entity.dxftype() == 'LWPOLYLINE'):

                        entity_polygon_pts = [ep[0:2] for ep in entity.get_points()]

                        np_entity_polygon_pts = np.array(entity_polygon_pts)

                        if entity.is_closed:

                            if len(np_entity_polygon_pts) > 2:

                                entity_polygon_points = Polygon(np_entity_polygon_pts)

                                if floor_polygon_points.contains(entity_polygon_points):

                                    for line_entity in entity.virtual_entities():

                                        if line_entity.dxftype() == 'LINE':

                                            line_start_pts = [line_entity.dxf.start[0], line_entity.dxf.start[1]]

                                            line_end_pts = [line_entity.dxf.end[0], line_entity.dxf.end[1]]

                                            line_pts = [line_start_pts, line_end_pts]

                                            np_line_pts = np.array(line_pts)

                                            line_length = LineString(np_line_pts).length

                                            if round(line_length) > 1:

                                                all_dims.append(self.add_aligned_dim_entity(
                                                    msp,
                                                    dim_start_pts=np_line_pts[0],
                                                    dim_end_pts=np_line_pts[1],
                                                    dist=0.1,
                                                    dim_text=round(line_length, 2),
                                                    lname=lname,
                                                    lcolor=0,
                                                    dim_h=0.08,
                                                    dimasz=0.05,
                                                    style="EZDXF_XL"
                                                ))

                                            else:

                                                if round(line_length) > 0:
                                                    all_dims.append(self.add_aligned_dim_entity(
                                                        msp,
                                                        dim_start_pts=np_line_pts[0],
                                                        dim_end_pts=np_line_pts[1],
                                                        dist=0.1,
                                                        dim_text=round(line_length, 2),
                                                        lname=lname,
                                                        lcolor=0,
                                                        dim_h=0.05,
                                                        dimasz=0.03,
                                                        style="EZDXF_M"
                                                    ))

                        else:

                            if len(np_entity_polygon_pts) == 4:

                                polygon_points = Polygon(np_entity_polygon_pts)

                                if floor_polygon_points.contains(polygon_points):

                                    segments = self.get_unique_line_segments(entity)

                                    for seg in segments:
                                        p1, p2 = seg

                                        length = LineString([p1, p2]).length

                                        # choose dimension size
                                        if length > 1:
                                            dim1 = self.add_aligned_dim_entity(
                                                msp,
                                                dim_start_pts=p1,
                                                dim_end_pts=p2,
                                                dist=0.1,
                                                dim_text=round(length, 2),
                                                lname=lname,
                                                lcolor=0,
                                                dim_h=0.08,
                                                dimasz=0.05,
                                                style="EZDXF_XL"
                                            )
                                            all_dims.append(dim1)
                                        else:

                                            if round(length) > 0:
                                                dim2 = self.add_aligned_dim_entity(
                                                    msp,
                                                    dim_start_pts=p1,
                                                    dim_end_pts=p2,
                                                    dist=0.1,
                                                    dim_text=round(length, 2),
                                                    lname=lname,
                                                    lcolor=0,
                                                    dim_h=0.05,
                                                    dimasz=0.03,
                                                    style="EZDXF_M"
                                                )
                                                all_dims.append(dim2)

                            elif (len(np_entity_polygon_pts) >= 3):

                                entity_polygon_pts = Polygon(np_entity_polygon_pts)

                                if floor_polygon_points.contains(entity_polygon_pts):

                                    # polygon convert into lines

                                    for line_entity in entity.virtual_entities():

                                        if line_entity.dxftype() == 'LINE':

                                            line_start_pts = [line_entity.dxf.start[0], line_entity.dxf.start[1]]

                                            line_end_pts = [line_entity.dxf.end[0], line_entity.dxf.end[1]]

                                            line_pts = [line_start_pts, line_end_pts]

                                            np_line_pts = np.array(line_pts)

                                            line_length = LineString(np_line_pts).length

                                            if round(line_length) > 1:

                                                all_dims.append(self.add_aligned_dim_entity(
                                                    msp,
                                                    dim_start_pts=np_line_pts[0],
                                                    dim_end_pts=np_line_pts[1],
                                                    dist=0.1,
                                                    dim_text=round(line_length, 2),
                                                    lname=lname,
                                                    lcolor=0,
                                                    dim_h=0.08,
                                                    dimasz=0.05,
                                                    style="EZDXF_XL"
                                                ))

                                            else:

                                                if round(line_length) > 0:
                                                    all_dims.append(self.add_aligned_dim_entity(
                                                        msp,
                                                        dim_start_pts=np_line_pts[0],
                                                        dim_end_pts=np_line_pts[1],
                                                        dist=0.1,
                                                        dim_text=round(line_length, 2),
                                                        lname=lname,
                                                        lcolor=0,
                                                        dim_h=0.05,
                                                        dimasz=0.03,
                                                        style="EZDXF_M"
                                                    ))


                                        elif line_entity.dxftype() == 'ARC':
                                            center_pts = (line_entity.dxf.center[0], line_entity.dxf.center[1])

                                            center_point = Point(center_pts)

                                            r = line_entity.dxf.radius

                                            start_pts = line_entity.start_point

                                            start_point = Point(start_pts)

                                            if floor_polygon_points.contains(center_point) and floor_polygon_points.contains(start_point):

                                                all_dims.append(self.add_aligned_dim_entity(msp, center_pts, start_pts,
                                                                                         0, f"Radius: {round(r, 2)}", lname,
                                                                                         0, 0.1, 0.08,"EZDXF_XL"))

                            else:

                                line_points = LineString(np_entity_polygon_pts)

                                if floor_polygon_points.contains(line_points):

                                    segments = self.get_unique_line_segments(entity)

                                    for seg in segments:
                                        p1, p2 = seg

                                        length = LineString([p1, p2]).length

                                        # choose dimension size
                                        if length > 1:
                                            dim1 = self.add_aligned_dim_entity(
                                                msp,
                                                dim_start_pts=p1,
                                                dim_end_pts=p2,
                                                dist=0.1,
                                                dim_text=round(length, 2),
                                                lname=lname,
                                                lcolor=0,
                                                dim_h=0.08,
                                                dimasz=0.05,
                                                style="EZDXF_XL"
                                            )
                                            all_dims.append(dim1)
                                        else:

                                            if round(length) > 0:
                                                dim2 = self.add_aligned_dim_entity(
                                                    msp,
                                                    dim_start_pts=p1,
                                                    dim_end_pts=p2,
                                                    dist=0.1,
                                                    dim_text=round(length, 2),
                                                    lname=lname,
                                                    lcolor=0,
                                                    dim_h=0.05,
                                                    dimasz=0.03,
                                                    style="EZDXF_M"
                                                )
                                                all_dims.append(dim2)

            elif lname in ("_Parking","_Podium","_ResiBUAOutline","_SpecialUseBUAOutline","_CommBUAOutline"):

                for entity in entities:

                    if (entity.dxftype() == 'LWPOLYLINE'):

                        entity_polygon_pts = [ep[0:2] for ep in entity.get_points()]

                        np_entity_polygon_pts = np.array(entity_polygon_pts)

                        if entity.is_closed:

                            if len(np_entity_polygon_pts) > 2:

                                entity_polygon_points = Polygon(np_entity_polygon_pts)

                                if floor_polygon_points.contains(entity_polygon_points):

                                    segments = self.get_unique_line_segments(entity)

                                    for seg in segments:
                                        p1, p2 = seg

                                        length = LineString([p1, p2]).length

                                        # choose dimension size
                                        if length > 1:
                                            dim1 = self.add_aligned_dim_entity(
                                                msp,
                                                dim_start_pts=p1,
                                                dim_end_pts=p2,
                                                dist=0.1,
                                                dim_text=round(length, 2),
                                                lname=lname,
                                                lcolor=0,
                                                dim_h=0.1,
                                                dimasz=0.08,
                                                style="EZDXF_XXL"
                                            )
                                            all_dims.append(dim1)
                                        else:

                                            if round(length) > 0:
                                                dim2 = self.add_aligned_dim_entity(
                                                    msp,
                                                    dim_start_pts=p1,
                                                    dim_end_pts=p2,
                                                    dist=0.1,
                                                    dim_text=round(length, 2),
                                                    lname=lname,
                                                    lcolor=0,
                                                    dim_h=0.08,
                                                    dimasz=0.05,
                                                    style="EZDXF_XL"
                                                )
                                                all_dims.append(dim2)

                                    minx = min(entity_polygon_pts, key=lambda x: x[0])

                                    miny = min(entity_polygon_pts, key=lambda x: x[1])

                                    maxx = max(entity_polygon_pts, key=lambda x: x[0])

                                    maxy = max(entity_polygon_pts, key=lambda x: x[1])

                                    poly = round(Polygon(np_entity_polygon_pts).area)

                                    bbox = box(minx[0], miny[1], maxx[0], maxy[1])

                                    if poly != round(bbox.area):

                                        x, y = bbox.exterior.coords.xy

                                        polygon_lines = [[[x[0], y[0]], [x[1], y[1]]], [[x[1], y[1]], [x[2], y[2]]],
                                                         [[x[2], y[2]], [x[3], y[3]]], [[x[3], y[3]], [x[4], y[4]]]]

                                        for line in polygon_lines:

                                            line_length = LineString(line).length

                                            if round(line_length) > 0:
                                                all_dims.append(self.add_aligned_dim_entity(
                                                    msp,
                                                    dim_start_pts=line[0],
                                                    dim_end_pts=line[1],
                                                    dist=-0.5,
                                                    dim_text=round(line_length, 2),
                                                    lname=lname,
                                                    lcolor=0,
                                                    dim_h=0.3,
                                                    dimasz=0.1,
                                                    style="EZDXF_XXXL"
                                                ))

                        else:

                            if (len(np_entity_polygon_pts) >= 3):

                                entity_polygon_pts1 = Polygon(np_entity_polygon_pts)

                                if floor_polygon_points.contains(entity_polygon_pts1):

                                    segments = self.get_unique_line_segments(entity)

                                    for seg in segments:
                                        p1, p2 = seg

                                        length = LineString([p1, p2]).length

                                        # choose dimension size
                                        if length > 1:
                                            dim1 = self.add_aligned_dim_entity(
                                                msp,
                                                dim_start_pts=p1,
                                                dim_end_pts=p2,
                                                dist=0.1,
                                                dim_text=round(length, 2),
                                                lname=lname,
                                                lcolor=0,
                                                dim_h=0.1,
                                                dimasz=0.08,
                                                style="EZDXF_XXL"
                                            )
                                            all_dims.append(dim1)
                                        else:

                                            if round(length) > 0:
                                                dim2 = self.add_aligned_dim_entity(
                                                    msp,
                                                    dim_start_pts=p1,
                                                    dim_end_pts=p2,
                                                    dist=0.1,
                                                    dim_text=round(length, 2),
                                                    lname=lname,
                                                    lcolor=0,
                                                    dim_h=0.08,
                                                    dimasz=0.05,
                                                    style="EZDXF_XL"
                                                )
                                                all_dims.append(dim2)

                                    minx = min(entity_polygon_pts, key=lambda x: x[0])

                                    miny = min(entity_polygon_pts, key=lambda x: x[1])

                                    maxx = max(entity_polygon_pts, key=lambda x: x[0])

                                    maxy = max(entity_polygon_pts, key=lambda x: x[1])

                                    poly = round(Polygon(entity_polygon_pts).area)

                                    bbox = box(minx[0], miny[1], maxx[0], maxy[1])

                                    if poly != round(bbox.area):

                                        x, y = bbox.exterior.coords.xy

                                        polygon_lines = [[[x[0], y[0]], [x[1], y[1]]], [[x[1], y[1]], [x[2], y[2]]],
                                                         [[x[2], y[2]], [x[3], y[3]]], [[x[3], y[3]], [x[4], y[4]]]]

                                        for line in polygon_lines:

                                            line_length = LineString(line).length

                                            if round(line_length) > 0:
                                                all_dims.append(self.add_aligned_dim_entity(
                                                    msp,
                                                    dim_start_pts=line[0],
                                                    dim_end_pts=line[1],
                                                    dist=-0.5,
                                                    dim_text=round(line_length, 2),
                                                    lname=lname,
                                                    lcolor=0,
                                                    dim_h=0.3,
                                                    dimasz=0.1,
                                                    style="EZDXF_XXXL"
                                                ))

                            else:

                                line_points = LineString(np_entity_polygon_pts)

                                if floor_polygon_points.contains(line_points):

                                    segments = self.get_unique_line_segments(entity)

                                    for seg in segments:
                                        p1, p2 = seg

                                        length = LineString([p1, p2]).length

                                        # choose dimension size
                                        if length > 1:
                                            dim1 = self.add_aligned_dim_entity(
                                                msp,
                                                dim_start_pts=p1,
                                                dim_end_pts=p2,
                                                dist=0.1,
                                                dim_text=round(length, 2),
                                                lname=lname,
                                                lcolor=0,
                                                dim_h=0.1,
                                                dimasz=0.08,
                                                style="EZDXF_XXL"
                                            )
                                            all_dims.append(dim1)
                                        else:

                                            if round(length) > 0:
                                                dim2 = self.add_aligned_dim_entity(
                                                    msp,
                                                    dim_start_pts=p1,
                                                    dim_end_pts=p2,
                                                    dist=0.1,
                                                    dim_text=round(length, 2),
                                                    lname=lname,
                                                    lcolor=0,
                                                    dim_h=0.08,
                                                    dimasz=0.05,
                                                    style="EZDXF_XL"
                                                )
                                                all_dims.append(dim2)

            elif lname in ("_Amenity","_BufferZone","_LeftoverOwnersLand",'_MortgageArea',"_NalaRoad","_NotInPossession",
                           "_OrganizedOpenSpace","_RefugeArea","_ReservedArea","_RoadWidening","_SurrenderToAuthority",
                           "_WaterBodies"):

                for entity in entities:

                    if entity.dxftype() in ('MTEXT','TEXT'):

                        entity_mtext_attribs = entity.dxfattribs()

                        entity_insert_mtext = entity_mtext_attribs.get('insert')

                        entity_insert_pts = [entity_insert_mtext[0], entity_insert_mtext[1]]

                        np_entity_insert_pts = np.array(entity_insert_pts)

                        entity_polygon_pointsx = Point(np_entity_insert_pts)

                        if floor_polygon_points.contains(entity_polygon_pointsx):

                            for polygon_entity in entities:

                                if polygon_entity.dxftype() == 'LWPOLYLINE':

                                    entity_polygon_pts = [pe[0:2] for pe in polygon_entity.get_points()]

                                    np_entity_polygon_pts = np.array(entity_polygon_pts)

                                    if len(np_entity_polygon_pts) <= 2:
                                        continue

                                    polygon_points = Polygon(np_entity_polygon_pts)

                                    if floor_polygon_points.contains(polygon_points):

                                        if polygon_points.contains(entity_polygon_pointsx) or polygon_points.touches(
                                                entity_polygon_pointsx) or round(
                                                polygon_points.distance(entity_polygon_pointsx)) == 0:

                                            if len(np_entity_polygon_pts) == 4:

                                                segments = self.get_unique_line_segments(polygon_entity)

                                                for seg in segments:
                                                    p1, p2 = seg

                                                    length = LineString([p1, p2]).length

                                                    # choose dimension size
                                                    if length > 1:
                                                        dim1 = self.add_aligned_dim_entity(
                                                            msp,
                                                            dim_start_pts=p1,
                                                            dim_end_pts=p2,
                                                            dist=-0.3,
                                                            dim_text=round(length, 2),
                                                            lname=lname,
                                                            lcolor=0,
                                                            dim_h=0.1,
                                                            dimasz=0.08,
                                                            style="EZDXF_XXL"
                                                        )
                                                        all_dims.append(dim1)
                                                    else:

                                                        if round(length) > 0:
                                                            dim2 = self.add_aligned_dim_entity(
                                                                msp,
                                                                dim_start_pts=p1,
                                                                dim_end_pts=p2,
                                                                dist=-0.3,
                                                                dim_text=round(length, 2),
                                                                lname=lname,
                                                                lcolor=0,
                                                                dim_h=0.08,
                                                                dimasz=0.05,
                                                                style="EZDXF_XL"
                                                            )
                                                            all_dims.append(dim2)

                                            else:

                                                polygon_pts = Polygon(np_entity_polygon_pts)

                                                polygon_area = round(polygon_pts.area, 1)

                                                mtext = f'A:{polygon_area}sqmt'

                                                text_dir_pts = [np_entity_insert_pts[0], np_entity_insert_pts[1] - 0.5]

                                                # self.add_area_mtext_entity(msp, mtext, lname, text_dir_pts,
                                                #                                    0.2, 0.1, 1, 1)
                                                self.add_area_text(msp, mtext, lname, text_dir_pts,
                                                                           0.2, 0.3, 1)

                                                segments = self.get_unique_line_segments(polygon_entity)

                                                for seg in segments:
                                                    p1, p2 = seg

                                                    length = LineString([p1, p2]).length

                                                    # choose dimension size
                                                    if length > 1:
                                                        dim1 = self.add_aligned_dim_entity(
                                                            msp,
                                                            dim_start_pts=p1,
                                                            dim_end_pts=p2,
                                                            dist=-0.3,
                                                            dim_text=round(length, 2),
                                                            lname=lname,
                                                            lcolor=0,
                                                            dim_h=0.1,
                                                            dimasz=0.08,
                                                            style="EZDXF_XXL"
                                                        )
                                                        all_dims.append(dim1)
                                                    else:

                                                        if round(length) > 0:
                                                            dim2 = self.add_aligned_dim_entity(
                                                                msp,
                                                                dim_start_pts=p1,
                                                                dim_end_pts=p2,
                                                                dist=-0.3,
                                                                dim_text=round(length, 2),
                                                                lname=lname,
                                                                lcolor=0,
                                                                dim_h=0.08,
                                                                dimasz=0.05,
                                                                style="EZDXF_XL"
                                                            )
                                                            all_dims.append(dim2)

            elif (lname == "_Terrace"):

                for entity in entities:

                    if (entity.dxftype() == 'LWPOLYLINE'):

                        if entity.is_closed:

                            entity_polygon_pts = [ep[0:2] for ep in entity.get_points()]

                            if len(entity_polygon_pts) > 2:

                                entity_polygon_points = Polygon(entity_polygon_pts)

                                if floor_polygon_points.contains(entity_polygon_points):

                                    segments = self.get_unique_line_segments(entity)

                                    for seg in segments:
                                        p1, p2 = seg

                                        length = LineString([p1, p2]).length

                                        # choose dimension size
                                        if length > 1:
                                            dim1 = self.add_aligned_dim_entity(
                                                msp,
                                                dim_start_pts=p1,
                                                dim_end_pts=p2,
                                                dist=0.1,
                                                dim_text=round(length, 2),
                                                lname=lname,
                                                lcolor=0,
                                                dim_h=0.08,
                                                dimasz=0.05,
                                                style="EZDXF_XL"
                                            )
                                            all_dims.append(dim1)
                                        else:

                                            if round(length) > 0:
                                                dim2 = self.add_aligned_dim_entity(
                                                    msp,
                                                    dim_start_pts=p1,
                                                    dim_end_pts=p2,
                                                    dist=-0.3,
                                                    dim_text=round(length, 2),
                                                    lname=lname,
                                                    lcolor=0,
                                                    dim_h=0.05,
                                                    dimasz=0.03,
                                                    style="EZDXF_L"
                                                )
                                                all_dims.append(dim2)


                                    minx = min(entity_polygon_pts, key=lambda x: x[0])

                                    miny = min(entity_polygon_pts, key=lambda x: x[1])

                                    maxx = max(entity_polygon_pts, key=lambda x: x[0])

                                    maxy = max(entity_polygon_pts, key=lambda x: x[1])

                                    bbox = box(minx[0], miny[1], maxx[0], maxy[1])

                                    x, y = bbox.exterior.coords.xy

                                    polygon_lines = [[[x[0], y[0]], [x[1], y[1]]], [[x[1], y[1]], [x[2], y[2]]],
                                                     [[x[2], y[2]], [x[3], y[3]]], [[x[3], y[3]], [x[4], y[4]]]]

                                    for line in polygon_lines:

                                        line_length = LineString(line).length

                                        if round(line_length) > 0:
                                            all_dims.append(self.add_aligned_dim_entity(
                                                msp,
                                                dim_start_pts=line[0],
                                                dim_end_pts=line[1],
                                                dist=-0.5,
                                                dim_text=round(line_length, 2),
                                                lname=lname,
                                                lcolor=0,
                                                dim_h=0.3,
                                                dimasz=0.1,
                                                style="EZDXF_XXXL"
                                            ))

                        else:

                            entity_polygon_pts = [ep[0:2] for ep in entity.get_points()]

                            np_entity_polygon_pts = np.array(entity_polygon_pts)

                            if len(np_entity_polygon_pts) >= 3:

                                entity_polygon_length = [ep[0:2] for ep in entity.get_points()]

                                np_entity_polygon_length = np.array(entity_polygon_length)

                                entity_polygon_points = Polygon(np_entity_polygon_length)

                                if floor_polygon_points.contains(entity_polygon_points):

                                    if len(np_entity_polygon_length) >= 4:

                                        entity_polygon_pts = [ep[0:2] for ep in entity.get_points()]

                                        minx = min(entity_polygon_pts, key=lambda x: x[0])

                                        miny = min(entity_polygon_pts, key=lambda x: x[1])

                                        maxx = max(entity_polygon_pts, key=lambda x: x[0])

                                        maxy = max(entity_polygon_pts, key=lambda x: x[1])

                                        bbox = box(minx[0], miny[1], maxx[0], maxy[1])

                                        x, y = bbox.exterior.coords.xy

                                        polygon_lines = [[[x[0], y[0]], [x[1], y[1]]], [[x[1], y[1]], [x[2], y[2]]],
                                                         [[x[2], y[2]], [x[3], y[3]]], [[x[3], y[3]], [x[4], y[4]]]]

                                        for line in polygon_lines:

                                            line_length = LineString(line).length
                                            if round(line_length) > 0:
                                                all_dims.append(self.add_aligned_dim_entity(
                                                    msp,
                                                    dim_start_pts=line[0],
                                                    dim_end_pts=line[1],
                                                    dist=-0.5,
                                                    dim_text=round(line_length, 2),
                                                    lname=lname,
                                                    lcolor=0,
                                                    dim_h=0.3,
                                                    dimasz=0.1,
                                                    style="EZDXF_XXXL"
                                                ))

            elif lname in ("_AccessoryUse","_ExistingStructure","_SlabCutoutVoid","_Splay",
                           "_VentilationShaft"):

               for entity in entities:

                   if (entity.dxftype() == 'LWPOLYLINE'):

                       if entity.is_closed:

                           entity_polygon_pts = [ep[0:2] for ep in entity.get_points()]

                           if len(entity_polygon_pts) > 2:

                               entity_polygon_points = Polygon(entity_polygon_pts)

                               if floor_polygon_points.contains(entity_polygon_points):

                                   segments = self.get_unique_line_segments(entity)

                                   for seg in segments:
                                       p1, p2 = seg

                                       length = LineString([p1, p2]).length

                                       # choose dimension size
                                       if length > 1:
                                           dim1 = self.add_aligned_dim_entity(
                                               msp,
                                               dim_start_pts=p1,
                                               dim_end_pts=p2,
                                               dist=0.1,
                                               dim_text=round(length, 2),
                                               lname=lname,
                                               lcolor=0,
                                               dim_h=0.08,
                                               dimasz=0.05,
                                               style="EZDXF_XL"
                                           )
                                           all_dims.append(dim1)
                                       else:

                                           if round(length) > 0:
                                               dim2 = self.add_aligned_dim_entity(
                                                   msp,
                                                   dim_start_pts=p1,
                                                   dim_end_pts=p2,
                                                   dist=0.1,
                                                   dim_text=round(length, 2),
                                                   lname=lname,
                                                   lcolor=0,
                                                   dim_h=0.05,
                                                   dimasz=0.03,
                                                   style="EZDXF_L"
                                               )
                                               all_dims.append(dim2)

                       else:

                           entity_polygon_length = [ep[0:2] for ep in entity.get_points()]

                           if len(entity_polygon_length) > 3:

                               np_entity_polygon_length = np.array(entity_polygon_length)

                               entity_polygon_points = Polygon(np_entity_polygon_length)

                               if floor_polygon_points.contains(entity_polygon_points):

                                   if len(np_entity_polygon_length) > 3:

                                       segments = self.get_unique_line_segments(entity)

                                       for seg in segments:
                                           p1, p2 = seg

                                           length = LineString([p1, p2]).length

                                           # choose dimension size
                                           if length > 1:
                                               dim1 = self.add_aligned_dim_entity(
                                                   msp,
                                                   dim_start_pts=p1,
                                                   dim_end_pts=p2,
                                                   dist=0.1,
                                                   dim_text=round(length, 2),
                                                   lname=lname,
                                                   lcolor=0,
                                                   dim_h=0.08,
                                                   dimasz=0.05,
                                                   style="EZDXF_XL"
                                               )
                                               all_dims.append(dim1)
                                           else:

                                               if round(length) > 0:
                                                   dim2 = self.add_aligned_dim_entity(
                                                       msp,
                                                       dim_start_pts=p1,
                                                       dim_end_pts=p2,
                                                       dist=0.1,
                                                       dim_text=round(length, 2),
                                                       lname=lname,
                                                       lcolor=0,
                                                       dim_h=0.05,
                                                       dimasz=0.03,
                                                       style="EZDXF_L"
                                                   )
                                                   all_dims.append(dim2)

            elif lname in ('_Amalgamation',"_EWS","_LIG"):

               for entity in entities:

                   if (entity.dxftype() == 'LWPOLYLINE'):

                       entity_polygon_pts = [ep[0:2] for ep in entity.get_points()]

                       np_entity_polygon_pts = np.array(entity_polygon_pts)

                       if len(np_entity_polygon_pts) <= 2:
                           continue

                       polygon_points = Polygon(np_entity_polygon_pts)

                       if floor_polygon_points.contains(polygon_points):

                           if len(entity_polygon_pts) > 2:

                               polygon_pts = Polygon(np_entity_polygon_pts)

                               polygon_area = round(polygon_pts.area, 1)

                               mtext = f'A:{polygon_area}sqmt'

                               polygon_centroid = polygon_pts.centroid.xy

                               polygon_centroid_pts = [polygon_centroid[0], polygon_centroid[1]]

                               np_polygon_centroid_pts = np.array(polygon_centroid_pts)

                               # self.add_area_mtext_entity(msp, mtext, lname, np_polygon_centroid_pts, 0.2,
                               #                                    0.1, 1, 1)
                               self.add_area_text(msp, mtext, lname, np_polygon_centroid_pts, 0.2,
                                                                  0.3, 1)

                               segments = self.get_unique_line_segments(entity)

                               for seg in segments:
                                   p1, p2 = seg

                                   length = LineString([p1, p2]).length

                                   # choose dimension size
                                   if length > 1:
                                       dim1 = self.add_aligned_dim_entity(
                                           msp,
                                           dim_start_pts=p1,
                                           dim_end_pts=p2,
                                           dist=0.1,
                                           dim_text=round(length, 2),
                                           lname=lname,
                                           lcolor=0,
                                           dim_h=0.08,
                                           dimasz=0.05,
                                           style="EZDXF_XL"
                                       )
                                       all_dims.append(dim1)
                                   else:

                                       if round(length) > 0:
                                           dim2 = self.add_aligned_dim_entity(
                                               msp,
                                               dim_start_pts=p1,
                                               dim_end_pts=p2,
                                               dist=0.1,
                                               dim_text=round(length, 2),
                                               lname=lname,
                                               lcolor=0,
                                               dim_h=0.05,
                                               dimasz=0.03,
                                               style="EZDXF_L"
                                           )
                                           all_dims.append(dim2)

        return all_dims

    # Use for upper floor like ex:- _SitePlan or _Plot
    def ScallingForSitePlan(self,msp,group,sp_poly):
        all_dims = []
        for lname, entities in group.items():

            if lname in ("_Lift","_ArchProjection","_Balcony","_Parking","_Passage","_Pathway","_Podium","_StairCase"):

                for entity in entities:

                    if (entity.dxftype() == 'LWPOLYLINE'):

                        entity_attribs = entity.dxfattribs()

                        entity_polygon_pts = [ep[0:2] for ep in entity.get_points()]

                        if entity_attribs.get('linetype') != "CENTER":

                            if len(entity_polygon_pts) == 4:

                                polygon_points = Polygon(entity_polygon_pts)

                                if sp_poly.contains(polygon_points):

                                    x, y = Polygon(entity_polygon_pts).exterior.xy

                                    entity_polygon_points = []

                                    for x1, y1 in zip(x, y):

                                        entity_polygon_points.append([x1, y1])

                                    segments = self.get_unique_line_segments(entity)

                                    for seg in segments:
                                        p1, p2 = seg

                                        length = LineString([p1, p2]).length

                                        # choose dimension size
                                        if length > 1:
                                            dim1 = self.add_aligned_dim_entity(
                                                msp,
                                                dim_start_pts=p1,
                                                dim_end_pts=p2,
                                                dist=-0.2,
                                                dim_text=round(length, 2),
                                                lname=lname,
                                                lcolor=0,
                                                dim_h=0.05,
                                                dimasz=0.03,
                                                style="EZDXF_L"
                                            )
                                            all_dims.append(dim1)
                                        else:
                                            if round(length) > 0:
                                                dim2 = self.add_aligned_dim_entity(
                                                    msp,
                                                    dim_start_pts=p1,
                                                    dim_end_pts=p2,
                                                    dist=0.08,
                                                    dim_text=round(length, 2),
                                                    lname=lname,
                                                    lcolor=0,
                                                    dim_h=0.03,
                                                    dimasz=0.02,
                                                    style="EZDXF_M"
                                                )
                                                all_dims.append(dim2)

                            elif (len(entity_polygon_pts) >= 3):

                                np_entity_polygon_pts = np.array(entity_polygon_pts)

                                entity_polygon_pts = Polygon(np_entity_polygon_pts)

                                if sp_poly.contains(entity_polygon_pts) or sp_poly.touches(entity_polygon_pts) :

                                    x, y = Polygon(np_entity_polygon_pts).exterior.xy

                                    entity_polygon_points = []

                                    for x1, y1 in zip(x, y):

                                        entity_polygon_points.append([x1, y1])

                                    segments = self.get_unique_line_segments(entity)

                                    for seg in segments:
                                        p1, p2 = seg

                                        length = LineString([p1, p2]).length

                                        # choose dimension size
                                        if length > 1:
                                            dim1 = self.add_aligned_dim_entity(
                                                msp,
                                                dim_start_pts=p1,
                                                dim_end_pts=p2,
                                                dist=-0.2,
                                                dim_text=round(length, 2),
                                                lname=lname,
                                                lcolor=0,
                                                dim_h=0.05,
                                                dimasz=0.03,
                                                style="EZDXF_L"
                                            )
                                            all_dims.append(dim1)
                                        else:
                                            if round(length) > 0:
                                                dim2 = self.add_aligned_dim_entity(
                                                    msp,
                                                    dim_start_pts=p1,
                                                    dim_end_pts=p2,
                                                    dist=0.1,
                                                    dim_text=round(length, 2),
                                                    lname=lname,
                                                    lcolor=0,
                                                    dim_h=0.03,
                                                    dimasz=0.02,
                                                    style="EZDXF_M"
                                                )
                                                all_dims.append(dim2)

                            else:

                                np_entity_polygon_pts = np.array(entity_polygon_pts)

                                line_points = LineString(np_entity_polygon_pts)

                                if sp_poly.contains(line_points)  or sp_poly.touches(line_points) :

                                    x, y = LineString(np_entity_polygon_pts).coords.xy

                                    line_points = []

                                    for x1, y1 in zip(x, y):

                                        line_points.append([x1, y1])

                                    np_line_points = np.array(line_points)

                                    line_length = LineString(np_line_points).length

                                    if round(line_length) > 1:

                                        all_dims.append(self.add_aligned_dim_entity(
                                            msp,
                                            dim_start_pts=np_line_points[0],
                                            dim_end_pts=np_line_points[1],
                                            dist=-0.2,
                                            dim_text=round(line_length, 2),
                                            lname=lname,
                                            lcolor=0,
                                            dim_h=0.05,
                                            dimasz=0.03,
                                            style="EZDXF_L"
                                        ))

                                    else:

                                        if round(line_length) > 0:
                                            all_dims.append(self.add_aligned_dim_entity(
                                                msp,
                                                dim_start_pts=np_line_points[0],
                                                dim_end_pts=np_line_points[1],
                                                dist=0.2,
                                                dim_text=round(line_length, 2),
                                                lname=lname,
                                                lcolor=0,
                                                dim_h=0.1,
                                                dimasz=0.1,
                                                style="EZDXF_M"
                                            ))

            elif lname == "_Ramp":

                for entity in entities:

                    if (entity.dxftype() == 'LWPOLYLINE'):

                        entity_attribs = entity.dxfattribs()

                        entity_polygon_pts = [ep[0:2] for ep in entity.get_points()]

                        if entity_attribs.get('linetype') != "CENTER":

                            if len(entity_polygon_pts) == 4:

                                polygon_points = Polygon(entity_polygon_pts)

                                if sp_poly.contains(polygon_points):

                                    x, y = Polygon(entity_polygon_pts).exterior.xy

                                    entity_polygon_points = []

                                    for x1, y1 in zip(x, y):

                                        entity_polygon_points.append([x1, y1])

                                    segments = self.get_unique_line_segments(entity)

                                    for seg in segments:
                                        p1, p2 = seg

                                        length = LineString([p1, p2]).length

                                        # choose dimension size
                                        if length > 1:
                                            dim1 = self.add_aligned_dim_entity(
                                                msp,
                                                dim_start_pts=p1,
                                                dim_end_pts=p2,
                                                dist=0.08,
                                                dim_text=round(length, 2),
                                                lname=lname,
                                                lcolor=0,
                                                dim_h=0.05,
                                                dimasz=0.03,
                                                style="EZDXF_L"
                                            )
                                            all_dims.append(dim1)
                                        else:
                                            if round(length) > 0:
                                                dim2 = self.add_aligned_dim_entity(
                                                    msp,
                                                    dim_start_pts=p1,
                                                    dim_end_pts=p2,
                                                    dist=0.08,
                                                    dim_text=round(length, 2),
                                                    lname=lname,
                                                    lcolor=0,
                                                    dim_h=0.05,
                                                    dimasz=0.03,
                                                    style="EZDXF_L"
                                                )
                                                all_dims.append(dim2)

                            elif (len(entity_polygon_pts) >= 3):

                                np_entity_polygon_pts = np.array(entity_polygon_pts)

                                entity_polygon_pts = Polygon(np_entity_polygon_pts)

                                if sp_poly.contains(entity_polygon_pts):

                                    x, y = Polygon(np_entity_polygon_pts).exterior.xy

                                    entity_polygon_points = []

                                    for x1, y1 in zip(x, y):

                                        entity_polygon_points.append([x1, y1])

                                    segments = self.get_unique_line_segments(entity)

                                    for seg in segments:
                                        p1, p2 = seg

                                        length = LineString([p1, p2]).length

                                        # choose dimension size
                                        if length > 1:
                                            dim1 = self.add_aligned_dim_entity(
                                                msp,
                                                dim_start_pts=p1,
                                                dim_end_pts=p2,
                                                dist=0.08,
                                                dim_text=round(length, 2),
                                                lname=lname,
                                                lcolor=0,
                                                dim_h=0.05,
                                                dimasz=0.03,
                                                style="EZDXF_L"
                                            )
                                            all_dims.append(dim1)
                                        else:
                                            if round(length) > 0:
                                                dim2 = self.add_aligned_dim_entity(
                                                    msp,
                                                    dim_start_pts=p1,
                                                    dim_end_pts=p2,
                                                    dist=0.08,
                                                    dim_text=round(length, 2),
                                                    lname=lname,
                                                    lcolor=0,
                                                    dim_h=0.05,
                                                    dimasz=0.03,
                                                    style="EZDXF_M"
                                                )
                                                all_dims.append(dim2)

                            else:

                                np_entity_polygon_pts = np.array(entity_polygon_pts)

                                line_points = LineString(np_entity_polygon_pts)

                                if sp_poly.contains(line_points):

                                    x, y = LineString(np_entity_polygon_pts).coords.xy

                                    line_points = []

                                    for x1, y1 in zip(x, y):

                                        line_points.append([x1, y1])

                                    np_line_points = np.array(line_points)

                                    line_length = LineString(np_line_points).length

                                    if round(line_length) > 1:

                                        all_dims.append(self.add_aligned_dim_entity(msp,
                                                                    dim_start_pts=np_line_points[0],
                                                                    dim_end_pts=np_line_points[1],
                                                                    dist=-0.3,
                                                                    dim_text=round(line_length, 2),
                                                                    lname=lname,
                                                                    lcolor=0,
                                                                    dim_h=0.1,
                                                                    dimasz=0.05,style="EZDXF_L"))

                                    else:

                                        if round(line_length) > 0:

                                            all_dims.append(self.add_aligned_dim_entity(msp,
                                                                        dim_start_pts=np_line_points[0],
                                                                        dim_end_pts=np_line_points[1],
                                                                        dist=0.1,
                                                                        dim_text=round(line_length, 2),
                                                                        lname=lname,
                                                                        lcolor=0,
                                                                        dim_h=0.1,
                                                                        dimasz=0.1,style="EZDXF_M"))

                        else:
                            for entity in entities:

                                if entity.dxftype() == 'ARC':
                                    center_pts = (entity.dxf.center[0], entity.dxf.center[1])
                                    center_point = Point(center_pts)
                                    r = entity.dxf.radius
                                    start_pts = entity.start_point
                                    start_point = Point(start_pts)

                                    if sp_poly.contains(center_point) and sp_poly.contains(start_point):

                                        all_dims.append(self.add_aligned_dim_entity(msp, center_pts, start_pts,
                                                                                 0, f"Radius: {round(r, 2)}", lname,
                                                                                 0, 0.2, 0.1,"EZDXF_XXL"))

                                elif entity.dxftype() == "LINE":

                                    line_pts = (entity.dxf.start[0],entity.dxf.start[1]),(entity.dxf.end[0],entity.dxf.end[1])

                                    line_points = LineString(line_pts)

                                    if sp_poly.contains(line_points):

                                        line_length = round(line_points.length,2)

                                        all_dims.append(self.add_aligned_dim_entity(msp, line_pts[0],line_pts[1] ,
                                                                                 0.1, line_length, lname,
                                                                                 0, 0.2, 0.1,"EZDXF_XXL"))

            elif lname=="_Plot":

                for entity in entities:

                    if (entity.dxftype() == 'LWPOLYLINE'):

                        entity_attribs = entity.dxfattribs()

                        entity_polygon_pts = [ep[0:2] for ep in entity.get_points()]

                        if entity_attribs.get('linetype') != "CENTER":

                            if len(entity_polygon_pts) == 4:

                                polygon_points = Polygon(entity_polygon_pts)

                                if sp_poly.contains(polygon_points):

                                    x, y = Polygon(entity_polygon_pts).exterior.xy

                                    entity_polygon_points = []

                                    for x1, y1 in zip(x, y):

                                        entity_polygon_points.append([x1, y1])

                                    segments = self.get_unique_line_segments(entity)

                                    for seg in segments:
                                        p1, p2 = seg

                                        length = LineString([p1, p2]).length

                                        # choose dimension size
                                        if length > 1:
                                            dim1 = self.add_aligned_dim_entity(
                                                msp,
                                                dim_start_pts=p1,
                                                dim_end_pts=p2,
                                                dist=0.08,
                                                dim_text=round(length, 2),
                                                lname=lname,
                                                lcolor=0,
                                                dim_h=0.3,
                                                dimasz=0.1,
                                                style="EZDXF_XXXL"
                                            )
                                            all_dims.append(dim1)
                                        else:
                                            if round(length) > 0:
                                                dim2 = self.add_aligned_dim_entity(
                                                    msp,
                                                    dim_start_pts=p1,
                                                    dim_end_pts=p2,
                                                    dist=0.08,
                                                    dim_text=round(length, 2),
                                                    lname=lname,
                                                    lcolor=0,
                                                    dim_h=0.05,
                                                    dimasz=0.03,
                                                    style="EZDXF_XXL"
                                                )
                                                all_dims.append(dim2)

                            elif (len(entity_polygon_pts) >= 3):

                                np_entity_polygon_pts = np.array(entity_polygon_pts)

                                entity_polygon_pts = Polygon(np_entity_polygon_pts)

                                if sp_poly.contains(entity_polygon_pts):

                                    x, y = Polygon(np_entity_polygon_pts).exterior.xy

                                    entity_polygon_points = []

                                    for x1, y1 in zip(x, y):

                                        entity_polygon_points.append([x1, y1])

                                    segments = self.get_unique_line_segments(entity)

                                    for seg in segments:
                                        p1, p2 = seg

                                        length = LineString([p1, p2]).length

                                        # choose dimension size
                                        if length > 1:
                                            dim1 = self.add_aligned_dim_entity(
                                                msp,
                                                dim_start_pts=p1,
                                                dim_end_pts=p2,
                                                dist=-0.6,
                                                dim_text=round(length, 2),
                                                lname=lname,
                                                lcolor=0,
                                                dim_h=0.3,
                                                dimasz=0.1,
                                                style="EZDXF_XXXL"
                                            )
                                            all_dims.append(dim1)
                                        else:
                                            if round(length) > 0:
                                                dim2 = self.add_aligned_dim_entity(
                                                    msp,
                                                    dim_start_pts=p1,
                                                    dim_end_pts=p2,
                                                    dist=-0.2,
                                                    dim_text=round(length, 2),
                                                    lname=lname,
                                                    lcolor=0,
                                                    dim_h=0.2,
                                                    dimasz=0.08,
                                                    style="EZDXF_XXL"
                                                )
                                                all_dims.append(dim2)
                            else:

                                np_entity_polygon_pts = np.array(entity_polygon_pts)

                                line_points = LineString(np_entity_polygon_pts)

                                if sp_poly.contains(line_points):

                                    x, y = LineString(np_entity_polygon_pts).coords.xy

                                    line_points = []

                                    for x1, y1 in zip(x, y):

                                        line_points.append([x1, y1])

                                    np_line_points = np.array(line_points)

                                    line_length = LineString(np_line_points).length

                                    if round(line_length) > 1:

                                        all_dims.append(self.add_aligned_dim_entity(
                                            msp,
                                            dim_start_pts=line_points[0],
                                            dim_end_pts=line_points[1],
                                            dist=-0.6,
                                            dim_text=round(line_length, 2),
                                            lname=lname,
                                            lcolor=0,
                                            dim_h=0.3,
                                            dimasz=0.1,
                                            style="EZDXF_XXXL"
                                        ))

                                    else:

                                        if round(line_length) > 0:

                                            all_dims.append(self.add_aligned_dim_entity(
                                                msp,
                                                dim_start_pts=line_points[0],
                                                dim_end_pts=line_points[1],
                                                dist=-0.2,
                                                dim_text=round(line_length, 2),
                                                lname=lname,
                                                lcolor=0,
                                                dim_h=0.2,
                                                dimasz=0.08,
                                                style="EZDXF_XXL"
                                            ))

            elif lname in ("_NalaRoad","_RefuseArea","_ReservedArea","_RoadWidening","_WaterBodies","_BufferZone"):

                for entity in entities:

                    if (entity.dxftype() == 'LWPOLYLINE'):

                        entity_polygon_pts = [ep[0:2] for ep in entity.get_points()]

                        np_entity_polygon_pts = np.array(entity_polygon_pts)

                        if len(np_entity_polygon_pts)<=2:
                            continue

                        polygon_points = Polygon(np_entity_polygon_pts)

                        if sp_poly.contains(polygon_points):

                            if len(np_entity_polygon_pts) == 4:

                                x, y = Polygon(np_entity_polygon_pts).exterior.xy

                                entity_polygon_points = []

                                for x1, y1 in zip(x, y):

                                    entity_polygon_points.append([x1, y1])

                                np_entity_polygon_points = np.array(entity_polygon_points)

                                polygon_pts = Polygon(np_entity_polygon_points)

                                polygon_area = round(polygon_pts.area, 1)

                                mtext = f'A:{polygon_area}sqmt'

                                xa, ya = polygon_pts.centroid.xy

                                polygon_centroid_pts = [xa[0], ya[0]]

                                np_polygon_centroid_pts = np.array(polygon_centroid_pts)

                                # self.add_area_mtext_entity(msp,mtext,lname,np_polygon_centroid_pts,0.4,0.1,1,1)
                                self.add_area_text(msp,mtext,lname,np_polygon_centroid_pts,0.2,0.3,1)

                                segments = self.get_unique_line_segments(entity)

                                for seg in segments:
                                    p1, p2 = seg

                                    length = LineString([p1, p2]).length

                                    # choose dimension size
                                    if length > 1:
                                        dim1 = self.add_aligned_dim_entity(
                                            msp,
                                            dim_start_pts=p1,
                                            dim_end_pts=p2,
                                            dist=0.2,
                                            dim_text=round(length, 2),
                                            lname=lname,
                                            lcolor=0,
                                            dim_h=0.1,
                                            dimasz=0.08,
                                            style="EZDXF_XL"
                                        )
                                        all_dims.append(dim1)
                                    else:
                                        if round(length) > 0:
                                            dim2 = self.add_aligned_dim_entity(
                                                msp,
                                                dim_start_pts=p1,
                                                dim_end_pts=p2,
                                                dist=0.1,
                                                dim_text=round(length, 2),
                                                lname=lname,
                                                lcolor=0,
                                                dim_h=0.08,
                                                dimasz=0.05,
                                                style="EZDXF_L"
                                            )
                                            all_dims.append(dim2)

                            else:

                                x, y = Polygon(np_entity_polygon_pts).exterior.xy

                                entity_polygon_points = []

                                for x1, y1 in zip(x, y):

                                    entity_polygon_points.append([x1, y1])

                                np_entity_polygon_points = np.array(entity_polygon_points)

                                polygon_pts = Polygon(np_entity_polygon_points)

                                polygon_area = round(polygon_pts.area, 1)

                                mtext = f'A:{polygon_area}sqmt'

                                xa, ya = polygon_pts.centroid.xy

                                polygon_centroid_pts = [xa[0], ya[0]]

                                np_polygon_centroid_pts = np.array(polygon_centroid_pts)

                                # self.add_area_mtext_entity(msp,mtext,lname,np_polygon_centroid_pts,0.4,0.1,1,1)
                                self.add_area_text(msp,mtext,lname,np_polygon_centroid_pts,0.2,0.3,1)

                                segments = self.get_unique_line_segments(entity)

                                for seg in segments:
                                    p1, p2 = seg

                                    length = LineString([p1, p2]).length

                                    # choose dimension size
                                    if length > 1:
                                        dim1 = self.add_aligned_dim_entity(
                                            msp,
                                            dim_start_pts=p1,
                                            dim_end_pts=p2,
                                            dist=-0.2,
                                            dim_text=round(length, 2),
                                            lname=lname,
                                            lcolor=0,
                                            dim_h=0.1,
                                            dimasz=0.08,
                                            style="EZDXF_XXL"
                                        )
                                        all_dims.append(dim1)
                                    else:
                                        if round(length) > 0:
                                            dim2 = self.add_aligned_dim_entity(
                                                msp,
                                                dim_start_pts=p1,
                                                dim_end_pts=p2,
                                                dist=-0.2,
                                                dim_text=round(length, 2),
                                                lname=lname,
                                                lcolor=0,
                                                dim_h=0.08,
                                                dimasz=0.05,
                                                style="EZDXF_XL"
                                            )
                                            all_dims.append(dim2)


            elif lname == "_OrganizedOpenSpace":

                for entity in entities:

                    if entity.dxftype() in ('MTEXT','TEXT'):

                        entity_mtext_attribs = entity.dxfattribs()

                        entity_insert_mtext = entity_mtext_attribs.get('insert')

                        entity_insert_pts = [entity_insert_mtext[0], entity_insert_mtext[1]]

                        np_entity_insert_pts = np.array(entity_insert_pts)

                        entity_text_points = Point(np_entity_insert_pts)

                        if sp_poly.contains(entity_text_points):

                            for polygon_entity in entities:

                                if (polygon_entity.dxftype() == 'LWPOLYLINE'):

                                    entity_polygon_pts = [pe[0:2] for pe in polygon_entity.get_points()]

                                    np_entity_polygon_pts = np.array(entity_polygon_pts)

                                    if len(np_entity_polygon_pts)<=2:
                                        continue

                                    polygon_points = Polygon(np_entity_polygon_pts)

                                    if sp_poly.contains(polygon_points):

                                        if (polygon_points.contains(entity_text_points)  or
                                                polygon_points.touches(entity_text_points)  or
                                                round(polygon_points.distance(entity_text_points),1) == 0.0):

                                            if len(np_entity_polygon_pts) == 4:

                                                x, y = Polygon(np_entity_polygon_pts).exterior.xy

                                                entity_polygon_points = []

                                                for x1, y1 in zip(x, y):

                                                    entity_polygon_points.append([x1, y1])

                                                np_entity_polygon_points = np.array(entity_polygon_points)

                                                polygon_pts = Polygon(np_entity_polygon_points)

                                                polygon_area = round(polygon_pts.area, 1)

                                                mtext = f'A:{polygon_area}sqmt'

                                                polygon_centroid_pts = [entity_insert_pts[0],entity_insert_pts[1] + 0.5]

                                                np_polygon_centroid_pts = np.array(polygon_centroid_pts)

                                                # self.add_area_mtext_entity(msp,mtext,lname,np_polygon_centroid_pts,0.15,0.15,1,1)
                                                self.add_area_text(msp,mtext,lname,np_polygon_centroid_pts,0.2,0.3,1)

                                                segments = self.get_unique_line_segments(polygon_entity)

                                                for seg in segments:
                                                    p1, p2 = seg

                                                    length = LineString([p1, p2]).length

                                                    # choose dimension size
                                                    if length > 1:
                                                        dim1 = self.add_aligned_dim_entity(
                                                            msp,
                                                            dim_start_pts=p1,
                                                            dim_end_pts=p2,
                                                            dist=-0.2,
                                                            dim_text=round(length, 2),
                                                            lname=lname,
                                                            lcolor=0,
                                                            dim_h=0.1,
                                                            dimasz=0.05,
                                                            style="EZDXF_XXL"
                                                        )
                                                        all_dims.append(dim1)
                                                    else:
                                                        if round(length) > 0:
                                                            dim2 = self.add_aligned_dim_entity(
                                                                msp,
                                                                dim_start_pts=p1,
                                                                dim_end_pts=p2,
                                                                dist=0.2,
                                                                dim_text=round(length, 2),
                                                                lname=lname,
                                                                lcolor=0,
                                                                dim_h=0.08,
                                                                dimasz=0.05,
                                                                style="EZDXF_XL"
                                                            )
                                                            all_dims.append(dim2)

                                            else:

                                                x, y = Polygon(np_entity_polygon_pts).exterior.xy

                                                entity_polygon_points = []

                                                for x1, y1 in zip(x, y):

                                                    entity_polygon_points.append([x1, y1])

                                                np_entity_polygon_points = np.array(entity_polygon_points)

                                                polygon_pts = Polygon(np_entity_polygon_points)

                                                polygon_area = round(polygon_pts.area, 1)

                                                mtext = f'A:{polygon_area}sqmt'

                                                polygon_centroid_pts = [entity_insert_pts[0],entity_insert_pts[1] + 0.5]

                                                np_polygon_centroid_pts = np.array(polygon_centroid_pts)

                                                # self.add_area_mtext_entity(msp,mtext,lname,np_polygon_centroid_pts,0.15,0.15,1,1)
                                                self.add_area_text(msp,mtext,lname,np_polygon_centroid_pts,0.2,0.3,1)

                                                segments = self.get_unique_line_segments(polygon_entity)

                                                for seg in segments:
                                                    p1, p2 = seg

                                                    length = LineString([p1, p2]).length

                                                    # choose dimension size
                                                    if length > 1:
                                                        dim1 = self.add_aligned_dim_entity(
                                                            msp,
                                                            dim_start_pts=p1,
                                                            dim_end_pts=p2,
                                                            dist=-0.2,
                                                            dim_text=round(length, 2),
                                                            lname=lname,
                                                            lcolor=0,
                                                            dim_h=0.1,
                                                            dimasz=0.08,
                                                            style="EZDXF_XL"
                                                        )
                                                        all_dims.append(dim1)
                                                    else:
                                                        if round(length) > 0:
                                                            dim2 = self.add_aligned_dim_entity(
                                                                msp,
                                                                dim_start_pts=p1,
                                                                dim_end_pts=p2,
                                                                dist=0.1,
                                                                dim_text=round(length, 2),
                                                                lname=lname,
                                                                lcolor=0,
                                                                dim_h=0.08,
                                                                dimasz=0.05,
                                                                style="EZDXF_L"
                                                            )
                                                            all_dims.append(dim2)

            elif lname in ("_AccessoryUse","_ExistingStructure","_InternalRoad","_SlabCutoutVoid","_Splay"):

                for entity in entities:

                    if (entity.dxftype() == 'LWPOLYLINE'):

                        entity_attribs = entity.dxfattribs()

                        if entity_attribs.get('linetype') == 'CENTER':

                            if entity.is_closed :

                                entity_polygon_pts = [[ep[0], ep[1], ep[-1]] for ep in entity.get_points()]

                                if len(entity_polygon_pts)<=2:
                                    continue

                                entity_polygon_points = Polygon(entity_polygon_pts)

                                if sp_poly.contains(entity_polygon_points):

                                    segments = self.get_unique_line_segments(entity)

                                    for seg in segments:
                                        p1, p2 = seg

                                        length = LineString([p1, p2]).length

                                        # choose dimension size
                                        if length > 1:
                                            dim1 = self.add_aligned_dim_entity(
                                                msp,
                                                dim_start_pts=p1,
                                                dim_end_pts=p2,
                                                dist=0.08,
                                                dim_text=round(length, 2),
                                                lname=lname,
                                                lcolor=0,
                                                dim_h=0.07,
                                                dimasz=0.05,
                                                style="EZDXF_XXL"
                                            )
                                            all_dims.append(dim1)
                                        else:
                                            if round(length) > 0:
                                                dim2 = self.add_aligned_dim_entity(
                                                    msp,
                                                    dim_start_pts=p1,
                                                    dim_end_pts=p2,
                                                    dist=0.08,
                                                    dim_text=round(length, 2),
                                                    lname=lname,
                                                    lcolor=0,
                                                    dim_h=0.05,
                                                    dimasz=0.02,
                                                    style="EZDXF_XL"
                                                )
                                                all_dims.append(dim2)


                        else:

                            entity_polygon_length = [ep[0:2] for ep in entity.get_points()]

                            if len(entity_polygon_length)>3:

                                np_entity_polygon_length = np.array(entity_polygon_length)

                                entity_polygon_points = Polygon(np_entity_polygon_length)

                                if sp_poly.contains(entity_polygon_points):

                                    if len(entity_polygon_length) == 4:

                                        segments = self.get_unique_line_segments(entity)

                                        for seg in segments:
                                            p1, p2 = seg

                                            length = LineString([p1, p2]).length

                                            # choose dimension size
                                            if length > 1:
                                                dim1 = self.add_aligned_dim_entity(
                                                    msp,
                                                    dim_start_pts=p1,
                                                    dim_end_pts=p2,
                                                    dist=0.1,
                                                    dim_text=round(length, 2),
                                                    lname=lname,
                                                    lcolor=0,
                                                    dim_h=0.08,
                                                    dimasz=0.05,
                                                    style="EZDXF_XL"
                                                )
                                                all_dims.append(dim1)
                                            else:
                                                if round(length) > 0:
                                                    dim2 = self.add_aligned_dim_entity(
                                                        msp,
                                                        dim_start_pts=p1,
                                                        dim_end_pts=p2,
                                                        dist=0.08,
                                                        dim_text=round(length, 2),
                                                        lname=lname,
                                                        lcolor=0,
                                                        dim_h=0.05,
                                                        dimasz=0.03,
                                                        style="EZDXF_L"
                                                    )
                                                    all_dims.append(dim2)

                                    else:

                                        entity_polygon_pts = [[ep[0], ep[1], ep[-1]] for ep in entity.get_points()]

                                        if len(entity_polygon_pts)<=2:
                                            continue

                                        polygon_points = Polygon(entity_polygon_pts)

                                        if sp_poly.contains(polygon_points):

                                            entity_polygon_pts.append(entity_polygon_pts[0])

                                            segments = self.get_unique_line_segments(entity)

                                            for seg in segments:
                                                p1, p2 = seg

                                                length = LineString([p1, p2]).length

                                                # choose dimension size
                                                if length > 1:
                                                    dim1 = self.add_aligned_dim_entity(
                                                        msp,
                                                        dim_start_pts=p1,
                                                        dim_end_pts=p2,
                                                        dist=0.1,
                                                        dim_text=round(length, 2),
                                                        lname=lname,
                                                        lcolor=0,
                                                        dim_h=0.08,
                                                        dimasz=0.05,
                                                        style="EZDXF_XL"
                                                    )
                                                    all_dims.append(dim1)
                                                else:
                                                    if round(length) > 0:
                                                        dim2 = self.add_aligned_dim_entity(
                                                            msp,
                                                            dim_start_pts=p1,
                                                            dim_end_pts=p2,
                                                            dist=0.08,
                                                            dim_text=round(length, 2),
                                                            lname=lname,
                                                            lcolor=0,
                                                            dim_h=0.05,
                                                            dimasz=0.03,
                                                            style="EZDXF_L"
                                                        )
                                                        all_dims.append(dim2)

            elif lname == "_ProposedWork":

                for prop_entity in entities:

                    if (prop_entity.dxftype() == 'LWPOLYLINE'):

                        entity_attribs = prop_entity.dxfattribs()

                        if entity_attribs.get('linetype') == 'CENTER':

                            if prop_entity.is_closed :

                                entity_polygon_pts = [[ep[0], ep[1], ep[-1]] for ep in prop_entity.get_points()]

                                np_entity_polygon_pts=np.array(entity_polygon_pts)

                                if len(np_entity_polygon_pts)<=2:
                                    continue

                                entity_polygon_points = Polygon(np_entity_polygon_pts)

                                if sp_poly.contains(entity_polygon_points):

                                    segments = self.get_unique_line_segments(prop_entity)

                                    for seg in segments:
                                        p1, p2 = seg

                                        length = LineString([p1, p2]).length

                                        # choose dimension size
                                        if length > 1:
                                            dim1 = self.add_aligned_dim_entity(
                                                msp,
                                                dim_start_pts=p1,
                                                dim_end_pts=p2,
                                                dist=0.1,
                                                dim_text=round(length, 2),
                                                lname=lname,
                                                lcolor=0,
                                                dim_h=0.08,
                                                dimasz=0.05,
                                                style="EZDXF_XXL"
                                            )
                                            all_dims.append(dim1)
                                        else:
                                            if round(length) > 0:
                                                dim2 = self.add_aligned_dim_entity(
                                                    msp,
                                                    dim_start_pts=p1,
                                                    dim_end_pts=p2,
                                                    dist=0.08,
                                                    dim_text=round(length, 2),
                                                    lname=lname,
                                                    lcolor=0,
                                                    dim_h=0.05,
                                                    dimasz=0.03,
                                                    style="EZDXF_XL"
                                                )
                                                all_dims.append(dim2)
                        else:

                            entity_polygon_length = [ep[0:2] for ep in prop_entity.get_points()]

                            np_entity_polygon_length = np.array(entity_polygon_length)

                            if len(np_entity_polygon_length)<=2:
                                continue

                            entity_polygon_points = Polygon(np_entity_polygon_length)

                            if sp_poly.contains(entity_polygon_points):

                                if len(entity_polygon_length) == 4:

                                    segments = self.get_unique_line_segments(prop_entity)

                                    for seg in segments:
                                        p1, p2 = seg

                                        length = LineString([p1, p2]).length

                                        # choose dimension size
                                        if length > 1:
                                            dim1 = self.add_aligned_dim_entity(
                                                msp,
                                                dim_start_pts=p1,
                                                dim_end_pts=p2,
                                                dist=0.1,
                                                dim_text=round(length, 2),
                                                lname=lname,
                                                lcolor=0,
                                                dim_h=0.08,
                                                dimasz=0.05,
                                                style="EZDXF_XXL"
                                            )
                                            all_dims.append(dim1)
                                        else:
                                            if round(length) > 0:
                                                dim2 = self.add_aligned_dim_entity(
                                                    msp,
                                                    dim_start_pts=p1,
                                                    dim_end_pts=p2,
                                                    dist=0.08,
                                                    dim_text=round(length, 2),
                                                    lname=lname,
                                                    lcolor=0,
                                                    dim_h=0.05,
                                                    dimasz=0.03,
                                                    style="EZDXF_XL"
                                                )
                                                all_dims.append(dim2)

                                else:

                                    entity_polygon_pts = [[ep[0], ep[1], ep[-1]] for ep in prop_entity.get_points()]

                                    if len(entity_polygon_pts)<=2:
                                        continue

                                    polygon_points = Polygon(entity_polygon_pts)

                                    if sp_poly.contains(polygon_points):

                                        segments = self.get_unique_line_segments(prop_entity)

                                        for seg in segments:
                                            p1, p2 = seg

                                            length = LineString([p1, p2]).length

                                            # choose dimension size
                                            if length > 1:
                                                dim1 = self.add_aligned_dim_entity(
                                                    msp,
                                                    dim_start_pts=p1,
                                                    dim_end_pts=p2,
                                                    dist=0.1,
                                                    dim_text=round(length, 2),
                                                    lname=lname,
                                                    lcolor=0,
                                                    dim_h=0.08,
                                                    dimasz=0.05,
                                                    style="EZDXF_XXL"
                                                )
                                                all_dims.append(dim1)
                                            else:
                                                if round(length) > 0:
                                                    dim2 = self.add_aligned_dim_entity(
                                                        msp,
                                                        dim_start_pts=p1,
                                                        dim_end_pts=p2,
                                                        dist=0.08,
                                                        dim_text=round(length, 2),
                                                        lname=lname,
                                                        lcolor=0,
                                                        dim_h=0.05,
                                                        dimasz=0.03,
                                                        style="EZDXF_XL"
                                                    )
                                                    all_dims.append(dim2)

            elif lname == "_MainRoad":

                for entity in entities:

                    if entity.dxftype() in ('MTEXT','TEXT'):

                        mtext_entity_attribs = entity.dxfattribs()

                        entity_insert_mtext = mtext_entity_attribs.get('insert')

                        entity_insert_pts = [entity_insert_mtext[0], entity_insert_mtext[1]]

                        np_entity_insert_pts = np.array(entity_insert_pts)

                        entity_insert_points = Point(np_entity_insert_pts)

                        for polygon_entity in entities:

                            if polygon_entity.dxftype() == 'LWPOLYLINE':

                                entity_polygon_pts = [pe[0:2] for pe in polygon_entity.get_points()]

                                if len(entity_polygon_pts) == 4:
                                    polygon_points = Polygon(entity_polygon_pts)

                                    if sp_poly.contains(polygon_points):

                                        if (polygon_points.contains(entity_insert_points)
                                                or polygon_points.touches(entity_insert_points) or
                                                round(polygon_points.distance(entity_insert_points)) == 0):

                                            x, y = Polygon(polygon_points).exterior.xy

                                            entity_polygon_points = []

                                            for x1, y1 in zip(x, y):

                                                entity_polygon_points.append([x1, y1])

                                            np_entity_polygon_points = np.array(entity_polygon_points)

                                            polygon_pts = Polygon(np_entity_polygon_points)

                                            polygon_area = round(polygon_pts.area, 1)

                                            mtext = f'A:{polygon_area}sqmt'

                                            polygon_centroid_pts = [entity_insert_pts[0],entity_insert_pts[1] - 0.5]

                                            np_polygon_centroid_pts = np.array(polygon_centroid_pts)

                                            # self.add_area_mtext_entity(msp, mtext, lname,
                                            #                             np_polygon_centroid_pts, 0.15, 0.1, 1, 1)

                                            self.add_area_text(msp, mtext, lname,
                                                                        np_polygon_centroid_pts, 0.2, 0.3, 1)

                                else:

                                    if polygon_entity.is_closed :

                                        entity_polygon_ptsx = [pe[0:2] for pe in polygon_entity.get_points()]
                                        if len(entity_polygon_ptsx)<=2:
                                            continue

                                        polygon_points = Polygon(entity_polygon_ptsx)

                                        if sp_poly.contains(polygon_points):

                                            if polygon_points.contains(entity_insert_points)  or polygon_points.touches(entity_insert_points)  or round(polygon_points.distance(entity_insert_points)) == 0:

                                                x, y = polygon_points.exterior.xy

                                                entity_polygon_points = []

                                                for x1, y1 in zip(x, y):

                                                    entity_polygon_points.append([x1, y1])

                                                np_entity_polygon_points = np.array(entity_polygon_points)

                                                polygon_pts = Polygon(np_entity_polygon_points)

                                                polygon_area = round(polygon_pts.area, 1)

                                                mtext = f'A:{polygon_area}sqmt'

                                                polygon_centroid_pts = [entity_insert_pts[0],entity_insert_pts[1] - 0.5]

                                                np_polygon_centroid_pts = np.array(polygon_centroid_pts)

                                                # self.add_area_mtext_entity(msp, mtext, lname,
                                                #                             np_polygon_centroid_pts, 0.15, 0.1,
                                                #                             1, 1)

                                                self.add_area_text(msp, mtext, lname,
                                                                            np_polygon_centroid_pts, 0.2, 0.3,
                                                                            1)

                                                segments = self.get_unique_line_segments(polygon_entity)

                                                for seg in segments:
                                                    p1, p2 = seg

                                                    length = LineString([p1, p2]).length

                                                    # choose dimension size
                                                    if length > 1:
                                                        dim1 = self.add_aligned_dim_entity(
                                                            msp,
                                                            dim_start_pts=p1,
                                                            dim_end_pts=p2,
                                                            dist=0.08,
                                                            dim_text=round(length, 2),
                                                            lname=lname,
                                                            lcolor=0,
                                                            dim_h=0.08,
                                                            dimasz=0.05,
                                                            style="EZDXF_XL"
                                                        )
                                                        all_dims.append(dim1)
                                                    else:
                                                        if round(length) > 0:
                                                            dim2 = self.add_aligned_dim_entity(
                                                                msp,
                                                                dim_start_pts=p1,
                                                                dim_end_pts=p2,
                                                                dist=0.08,
                                                                dim_text=round(length, 2),
                                                                lname=lname,
                                                                lcolor=0,
                                                                dim_h=0.05,
                                                                dimasz=0.03,
                                                                style="EZDXF_L"
                                                            )
                                                            all_dims.append(dim2)

                                    else:

                                        segments = self.get_unique_line_segments(polygon_entity)

                                        for seg in segments:
                                            p1, p2 = seg

                                            length = LineString([p1, p2]).length

                                            # choose dimension size
                                            if length > 1:
                                                dim1 = self.add_aligned_dim_entity(
                                                    msp,
                                                    dim_start_pts=p1,
                                                    dim_end_pts=p2,
                                                    dist=0.1,
                                                    dim_text=round(length, 2),
                                                    lname=lname,
                                                    lcolor=0,
                                                    dim_h=0.08,
                                                    dimasz=0.05,
                                                    style="EZDXF_XL"
                                                )
                                                all_dims.append(dim1)
                                            else:
                                                if round(length) > 0:
                                                    dim2 = self.add_aligned_dim_entity(
                                                        msp,
                                                        dim_start_pts=p1,
                                                        dim_end_pts=p2,
                                                        dist=0.08,
                                                        dim_text=round(length, 2),
                                                        lname=lname,
                                                        lcolor=0,
                                                        dim_h=0.05,
                                                        dimasz=0.03,
                                                        style="EZDXF_L"
                                                    )
                                                    all_dims.append(dim2)

        return all_dims

    # Use for Down floor like ex:- Basement,Stilt or Cellar
    def ScallingForDownFloor(self,msp,group,floor_polygon_points):

         all_dims = []
         for lname, entities in group.items():

            # This condition use for only dimension
            if lname in ("_Lift","_ArchProjection","_Balcony","_Pathway","_Plot","_Podium","_Room","_StairCase"):

                for entity in entities:

                    if (entity.dxftype() == 'LWPOLYLINE'):

                        entity_polygon_pts = [ep[0:2] for ep in entity.get_points()]

                        if entity.is_closed :

                            if len(entity_polygon_pts)>2:

                                entity_polygon_points = Polygon(entity_polygon_pts)

                                if floor_polygon_points.contains(entity_polygon_points):

                                    segments = self.get_unique_line_segments(entity)

                                    for seg in segments:
                                        p1, p2 = seg

                                        length = LineString([p1, p2]).length

                                        # choose dimension size
                                        if length > 1:
                                            dim1 = self.add_aligned_dim_entity(
                                                msp,
                                                dim_start_pts=p1,
                                                dim_end_pts=p2,
                                                dist=0.08,
                                                dim_text=round(length, 2),
                                                lname=lname,
                                                lcolor=0,
                                                dim_h=0.05,
                                                dimasz=0.03,
                                                style="EZDXF_L"
                                            )
                                            all_dims.append(dim1)
                                        else:
                                            if round(length) > 0:
                                                dim2 = self.add_aligned_dim_entity(
                                                    msp,
                                                    dim_start_pts=p1,
                                                    dim_end_pts=p2,
                                                    dist=0.08,
                                                    dim_text=round(length, 2),
                                                    lname=lname,
                                                    lcolor=0,
                                                    dim_h=0.05,
                                                    dimasz=0.03,
                                                    style="EZDXF_L"
                                                )
                                                all_dims.append(dim2)


                        else:

                            polygon_points = LineString(entity_polygon_pts)

                            if floor_polygon_points.contains(polygon_points):

                                segments = self.get_unique_line_segments(entity)

                                for seg in segments:
                                    p1, p2 = seg

                                    length = LineString([p1, p2]).length

                                    # choose dimension size
                                    if length > 1:
                                        dim1 = self.add_aligned_dim_entity(
                                            msp,
                                            dim_start_pts=p1,
                                            dim_end_pts=p2,
                                            dist=0.08,
                                            dim_text=round(length, 2),
                                            lname=lname,
                                            lcolor=0,
                                            dim_h=0.05,
                                            dimasz=0.03,
                                            style="EZDXF_L"
                                        )
                                        all_dims.append(dim1)
                                    else:
                                        if round(length) > 0:
                                            dim2 = self.add_aligned_dim_entity(
                                                msp,
                                                dim_start_pts=p1,
                                                dim_end_pts=p2,
                                                dist=0.08,
                                                dim_text=round(length, 2),
                                                lname=lname,
                                                lcolor=0,
                                                dim_h=0.05,
                                                dimasz=0.03,
                                                style="EZDXF_L"
                                            )
                                            all_dims.append(dim2)

            elif lname in ("_Ramp","_Passage"):

                for entity in entities:

                    if (entity.dxftype() == 'LWPOLYLINE'):

                        entity_polygon_pts = [ep[0:2] for ep in entity.get_points()]

                        if entity.is_closed :

                            if len(entity_polygon_pts)>2:

                                entity_polygon_points = Polygon(entity_polygon_pts)

                                if floor_polygon_points.contains(entity_polygon_points):

                                    segments = self.get_unique_line_segments(entity)

                                    for seg in segments:
                                        p1, p2 = seg

                                        length = LineString([p1, p2]).length

                                        # choose dimension size
                                        if length > 1:
                                            dim1 = self.add_aligned_dim_entity(
                                                msp,
                                                dim_start_pts=p1,
                                                dim_end_pts=p2,
                                                dist=0.1,
                                                dim_text=round(length, 2),
                                                lname=lname,
                                                lcolor=0,
                                                dim_h=0.08,
                                                dimasz=0.05,
                                                style="EZDXF_XXL"
                                            )
                                            all_dims.append(dim1)

                                        else:
                                            if round(length) > 0:
                                                dim2 = self.add_aligned_dim_entity(
                                                    msp,
                                                    dim_start_pts=p1,
                                                    dim_end_pts=p2,
                                                    dist=0.08,
                                                    dim_text=round(length, 2),
                                                    lname=lname,
                                                    lcolor=0,
                                                    dim_h=0.05,
                                                    dimasz=0.03,
                                                    style="EZDXF_XL"
                                                )
                                                all_dims.append(dim2)
                        else:

                            polygon_points = LineString(entity_polygon_pts)

                            if floor_polygon_points.contains(polygon_points):

                                segments = self.get_unique_line_segments(entity)

                                for seg in segments:
                                    p1, p2 = seg

                                    length = LineString([p1, p2]).length

                                    # choose dimension size
                                    if length > 1:
                                        dim1 = self.add_aligned_dim_entity(
                                            msp,
                                            dim_start_pts=p1,
                                            dim_end_pts=p2,
                                            dist=0.1,
                                            dim_text=round(length, 2),
                                            lname=lname,
                                            lcolor=0,
                                            dim_h=0.08,
                                            dimasz=0.05,
                                            style="EZDXF_XXL"
                                        )
                                        all_dims.append(dim1)
                                    else:
                                        if round(length) > 0:
                                            dim2 = self.add_aligned_dim_entity(
                                                msp,
                                                dim_start_pts=p1,
                                                dim_end_pts=p2,
                                                dist=0.08,
                                                dim_text=round(length, 2),
                                                lname=lname,
                                                lcolor=0,
                                                dim_h=0.05,
                                                dimasz=0.03,
                                                style="EZDXF_XL"
                                            )
                                            all_dims.append(dim2)

            elif lname in ("_Parking","_ResiBUAOutline","_SpecialUseBUAOutline","_CommBUAOutline"):

                for entity in entities:

                    if (entity.dxftype() == 'LWPOLYLINE'):

                        entity_polygon_pts = [ep[0:2] for ep in entity.get_points()]

                        np_entity_polygon_pts = np.array(entity_polygon_pts)

                        if entity.is_closed:

                            if len(np_entity_polygon_pts)>3:

                                entity_polygon_points = Polygon(np_entity_polygon_pts)

                                if floor_polygon_points.contains(entity_polygon_points):

                                    segments = self.get_unique_line_segments(entity)

                                    for seg in segments:
                                        p1, p2 = seg

                                        length = LineString([p1, p2]).length

                                        # choose dimension size
                                        if length > 1:
                                            dim1 = self.add_aligned_dim_entity(
                                                msp,
                                                dim_start_pts=p1,
                                                dim_end_pts=p2,
                                                dist=0.08,
                                                dim_text=round(length, 2),
                                                lname=lname,
                                                lcolor=0,
                                                dim_h=0.08,
                                                dimasz=0.05,
                                                style="EZDXF_XL"
                                            )
                                            all_dims.append(dim1)
                                        else:
                                            if round(length) > 0:
                                                dim2 = self.add_aligned_dim_entity(
                                                    msp,
                                                    dim_start_pts=p1,
                                                    dim_end_pts=p2,
                                                    dist=0.08,
                                                    dim_text=round(length, 2),
                                                    lname=lname,
                                                    lcolor=0,
                                                    dim_h=0.05,
                                                    dimasz=0.03,
                                                    style="EZDXF_L"
                                                )
                                                all_dims.append(dim2)


                                    poly = round(Polygon(entity_polygon_pts).area)

                                    minx = min(entity_polygon_pts, key=lambda x: x[0])

                                    miny = min(entity_polygon_pts, key=lambda x: x[1])

                                    maxx = max(entity_polygon_pts, key=lambda x: x[0])

                                    maxy = max(entity_polygon_pts, key=lambda x: x[1])

                                    bbox = box(minx[0],miny[1],maxx[0],maxy[1])

                                    if poly != round(bbox.area):

                                       x, y = bbox.exterior.coords.xy

                                       polygon_lines = [[[x[0], y[0]],[x[1], y[1]]],[[x[1], y[1]],[x[2], y[2]]],[[x[2], y[2]],[x[3], y[3]]],[[x[3], y[3]],[x[4], y[4]]]]

                                       for line in polygon_lines:

                                           line_length = LineString(line).length

                                           if round(line_length) > 0:
                                               all_dims.append(self.add_aligned_dim_entity(
                                                   msp,
                                                   dim_start_pts=line[0],
                                                   dim_end_pts=line[1],
                                                   dist=0.1,
                                                   dim_text=round(line_length, 2),
                                                   lname=lname,
                                                   lcolor=0,
                                                   dim_h=0.15,
                                                   dimasz=0.08,
                                                   style="EZDXF_XXXL"
                                               ))

                        else:

                            if len(np_entity_polygon_pts)>3:

                                line_points = LineString(np_entity_polygon_pts)

                                if floor_polygon_points.contains(line_points)  or floor_polygon_points.touches(line_points) :

                                    segments = self.get_unique_line_segments(entity)

                                    for seg in segments:
                                        p1, p2 = seg

                                        length = LineString([p1, p2]).length

                                        # choose dimension size
                                        if length > 1:
                                            dim1 = self.add_aligned_dim_entity(
                                                msp,
                                                dim_start_pts=p1,
                                                dim_end_pts=p2,
                                                dist=0.08,
                                                dim_text=round(length, 2),
                                                lname=lname,
                                                lcolor=0,
                                                dim_h=0.08,
                                                dimasz=0.03,
                                                style="EZDXF_XL"
                                            )
                                            all_dims.append(dim1)
                                        else:
                                            if round(length) > 0:
                                                dim2 = self.add_aligned_dim_entity(
                                                    msp,
                                                    dim_start_pts=p1,
                                                    dim_end_pts=p2,
                                                    dist=0.08,
                                                    dim_text=round(length, 2),
                                                    lname=lname,
                                                    lcolor=0,
                                                    dim_h=0.05,
                                                    dimasz=0.03,
                                                    style="EZDXF_XL"
                                                )
                                                all_dims.append(dim2)

                                    minx = min(entity_polygon_pts, key=lambda x: x[0])

                                    miny = min(entity_polygon_pts, key=lambda x: x[1])

                                    maxx = max(entity_polygon_pts, key=lambda x: x[0])

                                    maxy = max(entity_polygon_pts, key=lambda x: x[1])

                                    poly = round(Polygon(entity_polygon_pts).area)

                                    bbox =box(minx[0],miny[1],maxx[0],maxy[1])

                                    if poly != round(bbox.area):

                                        x, y = bbox.exterior.coords.xy

                                        polygon_lines = [[[x[0], y[0]],[x[1], y[1]]],[[x[1], y[1]],[x[2], y[2]]],[[x[2], y[2]],[x[3], y[3]]],[[x[3], y[3]],[x[4], y[4]]]]

                                        for line in polygon_lines:

                                            line_length = LineString(line).length

                                            if round(line_length) > 0:
                                                all_dims.append(self.add_aligned_dim_entity(
                                                    msp,
                                                    dim_start_pts=line[0],
                                                    dim_end_pts=line[1],
                                                    dist=0.1,
                                                    dim_text=round(line_length, 2),
                                                    lname=lname,
                                                    lcolor=0,
                                                    dim_h=0.15,
                                                    dimasz=0.08,
                                                    style="EZDXF_XXXL"
                                                ))

            elif lname in ("_Amenity","_BufferZone","_LeftoverOwnersLand",'_MortgageArea',"_NalaRoad",
                           "_NotInPossession","_OrganizedOpenSpace","_RefuseArea","_ReservedArea","_RoadWidening",
                           "_SurrenderToAuthority","_WaterBodies"):

                for entity in entities:

                    if entity.dxftype() in ('MTEXT','TEXT'):

                        entity_mtext_attribs = entity.dxfattribs()

                        entity_insert_mtext = entity_mtext_attribs.get('insert')

                        entity_insert_pts = [entity_insert_mtext[0],entity_insert_mtext[1]]

                        np_entity_insert_pts = np.array(entity_insert_pts)

                        entity_polygon_pointsx = Point(np_entity_insert_pts)

                        if floor_polygon_points.contains(entity_polygon_pointsx):

                            # iterate polygon entities:
                            for polygon_entity in entities:

                                if polygon_entity.dxftype() == 'LWPOLYLINE':

                                    entity_polygon_pts = [pe[0:2] for pe in polygon_entity.get_points()]

                                    np_entity_polygon_pts = np.array(entity_polygon_pts)

                                    if len(np_entity_polygon_pts)<=2:
                                        continue

                                    polygon_points = Polygon(np_entity_polygon_pts)

                                    if floor_polygon_points.contains(polygon_points):

                                        if polygon_points.touches(entity_polygon_pointsx)  or round(polygon_points.distance(entity_polygon_pointsx)) == 0:

                                            if polygon_entity.is_closed:

                                                if len(entity_polygon_pts)>2:

                                                    polygon_pts = Polygon(np_entity_polygon_pts)

                                                    polygon_area = round(polygon_pts.area,1)

                                                    mtext = f'A:{polygon_area}sqmt'

                                                    area_text_dir = [entity_insert_pts[0],entity_insert_pts[1] - 0.5]

                                                    # self.add_area_mtext_entity(msp, mtext, lname, area_text_dir,
                                                    #                         0.2, 0.1, 1, 1)

                                                    self.add_area_text(msp, mtext, lname, area_text_dir,
                                                                            0.2, 0.3, 1)

                                                    segments = self.get_unique_line_segments(polygon_entity)

                                                    for seg in segments:
                                                        p1, p2 = seg

                                                        length = LineString([p1, p2]).length

                                                        # choose dimension size
                                                        if length > 1:
                                                            dim1 = self.add_aligned_dim_entity(
                                                                msp,
                                                                dim_start_pts=p1,
                                                                dim_end_pts=p2,
                                                                dist=0.1,
                                                                dim_text=round(length, 2),
                                                                lname=lname,
                                                                lcolor=0,
                                                                dim_h=0.08,
                                                                dimasz=0.05,
                                                                style="EZDXF_XL"
                                                            )
                                                            all_dims.append(dim1)
                                                        else:
                                                            if round(length) > 0:
                                                                dim2 = self.add_aligned_dim_entity(
                                                                    msp,
                                                                    dim_start_pts=p1,
                                                                    dim_end_pts=p2,
                                                                    dist=0.1,
                                                                    dim_text=round(length, 2),
                                                                    lname=lname,
                                                                    lcolor=0,
                                                                    dim_h=0.05,
                                                                    dimasz=0.03,
                                                                    style="EZDXF_L"
                                                                )
                                                                all_dims.append(dim2)

                                            else:

                                                if len(np_entity_polygon_pts)>2:

                                                    polygon_pts = Polygon(np_entity_polygon_pts)

                                                    polygon_area = round(polygon_pts.area,1)

                                                    mtext = f'A:{polygon_area}sqmt'

                                                    text_dir_pts = [np_entity_insert_pts[0],np_entity_insert_pts[1] - 0.5]

                                                    # self.add_area_mtext_entity(msp, mtext, lname, text_dir_pts,
                                                    #                                    1.0, 0.2, 1, 1)

                                                    self.add_area_text(msp, mtext, lname, text_dir_pts,
                                                                                       0.2, 0.3, 1)

                                                    segments = self.get_unique_line_segments(polygon_entity)

                                                    for seg in segments:
                                                        p1, p2 = seg

                                                        length = LineString([p1, p2]).length

                                                        # choose dimension size
                                                        if length > 1:
                                                            dim1 = self.add_aligned_dim_entity(
                                                                msp,
                                                                dim_start_pts=p1,
                                                                dim_end_pts=p2,
                                                                dist=0.1,
                                                                dim_text=round(length, 2),
                                                                lname=lname,
                                                                lcolor=0,
                                                                dim_h=0.08,
                                                                dimasz=0.05,
                                                                style="EZDXF_XL"
                                                            )
                                                            all_dims.append(dim1)
                                                        else:
                                                            if round(length) > 0:
                                                                dim2 = self.add_aligned_dim_entity(
                                                                    msp,
                                                                    dim_start_pts=p1,
                                                                    dim_end_pts=p2,
                                                                    dist=0.08,
                                                                    dim_text=round(length, 2),
                                                                    lname=lname,
                                                                    lcolor=0,
                                                                    dim_h=0.05,
                                                                    dimasz=0.03,
                                                                    style="EZDXF_L"
                                                                )
                                                                all_dims.append(dim2)

            elif lname in ("_AccessoryUse","_ExistingStructure","_InternalRoad","_SlabCutoutVoid","_Splay","_Terrace","_VentilationShaft"):

                for entity in entities:

                    if (entity.dxftype() == 'LWPOLYLINE'):

                        if entity.is_closed :

                            entity_polygon_pts = [ep[0:2] for ep in entity.get_points()]

                            if len(entity_polygon_pts)>2:

                                entity_polygon_points = Polygon(entity_polygon_pts)

                                if floor_polygon_points.contains(entity_polygon_points):

                                    segments = self.get_unique_line_segments(entity)

                                    for seg in segments:
                                        p1, p2 = seg

                                        length = LineString([p1, p2]).length

                                        # choose dimension size
                                        if length > 1:
                                            dim1 = self.add_aligned_dim_entity(
                                                msp,
                                                dim_start_pts=p1,
                                                dim_end_pts=p2,
                                                dist=0.08,
                                                dim_text=round(length, 2),
                                                lname=lname,
                                                lcolor=0,
                                                dim_h=0.08,
                                                dimasz=0.05,
                                                style="EZDXF_XL"
                                            )
                                            all_dims.append(dim1)
                                        else:
                                            if round(length) > 0:
                                                dim2 = self.add_aligned_dim_entity(
                                                    msp,
                                                    dim_start_pts=p1,
                                                    dim_end_pts=p2,
                                                    dist=0.08,
                                                    dim_text=round(length, 2),
                                                    lname=lname,
                                                    lcolor=0,
                                                    dim_h=0.05,
                                                    dimasz=0.03,
                                                    style="EZDXF_L"
                                                )
                                                all_dims.append(dim2)

                        else:

                            entity_polygon_pts = [ep[0:2] for ep in entity.get_points()]

                            np_entity_polygon_pts = np.array(entity_polygon_pts)

                            if len(np_entity_polygon_pts)>2:

                                polygon_points = Polygon(np_entity_polygon_pts)

                                if floor_polygon_points.contains(polygon_points):

                                    if len(np_entity_polygon_pts) == 4:

                                        segments = self.get_unique_line_segments(entity)

                                        for seg in segments:
                                            p1, p2 = seg

                                            length = LineString([p1, p2]).length

                                            # choose dimension size
                                            if length > 1:
                                                dim1 = self.add_aligned_dim_entity(
                                                    msp,
                                                    dim_start_pts=p1,
                                                    dim_end_pts=p2,
                                                    dist=0.08,
                                                    dim_text=round(length, 2),
                                                    lname=lname,
                                                    lcolor=0,
                                                    dim_h=0.08,
                                                    dimasz=0.05,
                                                    style="EZDXF_XL"
                                                )
                                                all_dims.append(dim1)
                                            else:
                                                if round(length) > 0:
                                                    dim2 = self.add_aligned_dim_entity(
                                                        msp,
                                                        dim_start_pts=p1,
                                                        dim_end_pts=p2,
                                                        dist=0.08,
                                                        dim_text=round(length, 2),
                                                        lname=lname,
                                                        lcolor=0,
                                                        dim_h=0.05,
                                                        dimasz=0.03,
                                                        style="EZDXF_L"
                                                    )
                                                    all_dims.append(dim2)
                                    else:

                                        segments = self.get_unique_line_segments(entity)

                                        for seg in segments:
                                            p1, p2 = seg

                                            length = LineString([p1, p2]).length

                                            # choose dimension size
                                            if length > 1:
                                                dim1 = self.add_aligned_dim_entity(
                                                    msp,
                                                    dim_start_pts=p1,
                                                    dim_end_pts=p2,
                                                    dist=0.08,
                                                    dim_text=round(length, 2),
                                                    lname=lname,
                                                    lcolor=0,
                                                    dim_h=0.08,
                                                    dimasz=0.05,
                                                    style="EZDXF_XL"
                                                )
                                                all_dims.append(dim1)
                                            else:
                                                if round(length) > 0:
                                                    dim2 = self.add_aligned_dim_entity(
                                                        msp,
                                                        dim_start_pts=p1,
                                                        dim_end_pts=p2,
                                                        dist=0.08,
                                                        dim_text=round(length, 2),
                                                        lname=lname,
                                                        lcolor=0,
                                                        dim_h=0.05,
                                                        dimasz=0.03,
                                                        style="EZDXF_L"
                                                    )
                                                    all_dims.append(dim2)

            elif (lname == '_Amalgamation' or lname == "_EWS" or lname == "_LIG"):

                for entity in entities:

                    if (entity.dxftype() == 'LWPOLYLINE'):

                        entity_polygon_pts = [ep[0:2] for ep in entity.get_points()]

                        np_entity_polygon_pts = np.array(entity_polygon_pts)

                        if len(np_entity_polygon_pts)<=2:
                            continue

                        polygon_points = Polygon(np_entity_polygon_pts)

                        if floor_polygon_points.contains(polygon_points)  or floor_polygon_points.touches(polygon_points) :

                            if len(entity_polygon_pts) == 4:

                                polygon_pts = Polygon(np_entity_polygon_pts)

                                polygon_area = round(polygon_pts.area, 1)

                                mtext = f'A:{polygon_area}sqmt'

                                polygon_centroid = polygon_pts.centroid.xy

                                polygon_centroid_pts = [polygon_centroid[0],polygon_centroid[1]]

                                np_polygon_centroid_pts = np.array(polygon_centroid_pts)

                                # self.add_area_mtext_entity(msp, mtext, lname, np_polygon_centroid_pts, 0.2, 0.1,
                                #                                    1, 1)

                                self.add_area_text(msp, mtext, lname, np_polygon_centroid_pts, 0.2, 0.3,
                                                                   1)

                                segments = self.get_unique_line_segments(entity)

                                for seg in segments:
                                    p1, p2 = seg

                                    length = LineString([p1, p2]).length

                                    # choose dimension size
                                    if length > 1:
                                        dim1 = self.add_aligned_dim_entity(
                                            msp,
                                            dim_start_pts=p1,
                                            dim_end_pts=p2,
                                            dist=0.08,
                                            dim_text=round(length, 2),
                                            lname=lname,
                                            lcolor=0,
                                            dim_h=0.08,
                                            dimasz=0.05,
                                            style="EZDXF_XL"
                                        )
                                        all_dims.append(dim1)
                                    else:
                                        if round(length) > 0:
                                            dim2 = self.add_aligned_dim_entity(
                                                msp,
                                                dim_start_pts=p1,
                                                dim_end_pts=p2,
                                                dist=0.08,
                                                dim_text=round(length, 2),
                                                lname=lname,
                                                lcolor=0,
                                                dim_h=0.05,
                                                dimasz=0.03,
                                                style="EZDXF_L"
                                            )
                                            all_dims.append(dim2)

                            else:

                                polygon_pts = Polygon(np_entity_polygon_pts)

                                polygon_area = round(polygon_pts.area, 1)

                                mtext = f'A:{polygon_area}sqmt'

                                polygon_centroid = polygon_pts.centroid.xy

                                polygon_centroid_pts = [polygon_centroid[0],polygon_centroid[1]]

                                np_polygon_centroid_pts = np.array(polygon_centroid_pts)

                                # self.add_area_mtext_entity(msp, mtext, lname, np_polygon_centroid_pts, 0.2, 0.1,
                                #                                    1, 1)

                                self.add_area_text(msp, mtext, lname, np_polygon_centroid_pts, 0.2, 0.3,
                                                                   1)

                                segments = self.get_unique_line_segments(entity)

                                for seg in segments:
                                    p1, p2 = seg

                                    length = LineString([p1, p2]).length

                                    # choose dimension size
                                    if length > 1:
                                        dim1 = self.add_aligned_dim_entity(
                                            msp,
                                            dim_start_pts=p1,
                                            dim_end_pts=p2,
                                            dist=0.08,
                                            dim_text=round(length, 2),
                                            lname=lname,
                                            lcolor=0,
                                            dim_h=0.08,
                                            dimasz=0.05,
                                            style="EZDXF_XL"
                                        )
                                        all_dims.append(dim1)
                                    else:
                                        if round(length) > 0:
                                            dim2 = self.add_aligned_dim_entity(
                                                msp,
                                                dim_start_pts=p1,
                                                dim_end_pts=p2,
                                                dist=0.08,
                                                dim_text=round(length, 2),
                                                lname=lname,
                                                lcolor=0,
                                                dim_h=0.05,
                                                dimasz=0.03,
                                                style="EZDXF_L"
                                            )
                                            all_dims.append(dim2)

         return all_dims

    def BuildingName_Layer(self, Building_Data):

        building_dict = dict()

        unique_polygons = {}

        for Building_entity in Building_Data:

            if Building_entity.dxftype() == 'LWPOLYLINE' and Building_entity.closed:

                points=list(Building_entity.get_points())

                if len(points)<=2:
                    continue

                buildingPolygonID = Building_entity.dxf.handle

                building_polygon = Polygon(np.array([bp[0:2] for bp in Building_entity.get_points()]))

                vertices = tuple(Building_entity.get_points())

                if vertices in unique_polygons:

                    logging.info(
                        f"Building Layer Found Duplicate Polygon Of {buildingPolygonID}.")

                else:

                    unique_polygons[vertices] = Building_entity

                BPolygonContainsLabel = []

                for Building_entity in Building_Data:

                    if Building_entity.dxftype() == 'TEXT' or Building_entity.dxftype() == 'MTEXT':

                        building_text_properties = Building_entity.dxfattribs()

                        Building_Name = building_text_properties.get(
                            'text') if Building_entity.dxftype() == 'TEXT' else Building_entity.plain_text()
                        if Building_Name != '':
                            building_text_pts = building_text_properties.get('insert')

                            building_point = Point(np.array([building_text_pts[0], building_text_pts[1]]))

                            if building_polygon.contains(building_point)  or building_polygon.touches(
                                    building_point)  or round(building_polygon.distance(building_point),
                                                                     1) == 0.0:
                                BPolygonContainsLabel.append([Building_Name, building_polygon])
                                break

                if BPolygonContainsLabel != [] and len(BPolygonContainsLabel) <= 1:

                    for buildingnampoly in BPolygonContainsLabel:
                        building_dict[buildingPolygonID] = buildingnampoly

                elif (len(BPolygonContainsLabel) > 1):

                    logging.warning(
                        f'Building Layer Polygon REF # {buildingPolygonID} Found More Than One Label')

                else:

                    logging.warning(
                        f'Building Layer Polygon REF # {buildingPolygonID} Does Not Found Any Label')

        return building_dict

    def Floor_Layer(self, Floor_Data):

        floor_dict = dict()

        unique_polygons = {}

        for Floor_entity in Floor_Data:

            if Floor_entity.dxftype() == 'LWPOLYLINE' and Floor_entity.closed and len(
                    [fp[0:2] for fp in Floor_entity.get_points()]) >= 3:

                floorPolygonID = Floor_entity.dxf.handle

                floor_polygon = Polygon(np.array([fp[0:2] for fp in Floor_entity.get_points()]))

                vertices = tuple(Floor_entity.get_points())

                if vertices in unique_polygons:

                    logging.warning(f"Floor Layer Found Duplicate Polygon Of {floorPolygonID}.")

                else:

                    unique_polygons[vertices] = Floor_entity

                FPolygonContainsLabel = []

                for Floor_entity in Floor_Data:

                    if Floor_entity.dxftype() == 'TEXT' or Floor_entity.dxftype() == 'MTEXT':
                        floor_label_id= Floor_entity.dxf.handle
                        floor_text_properties = Floor_entity.dxfattribs()

                        Floor_Name = floor_text_properties.get(
                            'text') if Floor_entity.dxftype() == 'TEXT' else Floor_entity.plain_text()

                        if Floor_Name != '':

                            floor_text_pts = floor_text_properties.get('insert')

                            floor_point = Point(np.array([floor_text_pts[0], floor_text_pts[1]]))

                            if floor_polygon.contains(floor_point)  or floor_polygon.touches(
                                    floor_point)  or round(floor_polygon.distance(floor_point), 1) == 0.0:
                                FPolygonContainsLabel.append([floor_label_id,Floor_Name, floor_polygon])
                                break

                if FPolygonContainsLabel != [] and len(FPolygonContainsLabel) <= 1:

                    for floornampoly in FPolygonContainsLabel:
                        floor_dict[floornampoly[0]] = floornampoly[1:]

                elif (len(FPolygonContainsLabel) > 1):

                    logging.warning(
                        f'Floor Layer Polygon REF # ({floorPolygonID}) Found More Than One Label')

                else:

                    logging.warning(
                        f'Floor Layer Polygon REF # ({floorPolygonID}) Does Not Found Any Label')

        return floor_dict

    def ProposedWork_Layer(self, ProposedWork_Data):

        propwork_dict = dict()
        unique_polygons = {}

        for propworkpoly_entity in ProposedWork_Data:

            if propworkpoly_entity.dxftype() == 'LWPOLYLINE' and propworkpoly_entity.closed:

                points=list(propworkpoly_entity.get_points())

                if len(points)<=2:
                    continue

                propworkPolygonID = propworkpoly_entity.dxf.handle

                propwork_polygon = Polygon(np.array([pw[0:2] for pw in propworkpoly_entity.get_points()]))

                vertices = tuple(propworkpoly_entity.get_points())

                if vertices in unique_polygons:

                    logging.warning(
                        f"ProposedWork Layer Found Duplicate Polygon Of {propworkPolygonID}.")
                else:

                    unique_polygons[vertices] = propworkpoly_entity

                propworkPolygonContainsLabel = []

                for propwork_entity in ProposedWork_Data:

                    if propwork_entity.dxftype() == 'TEXT' or propwork_entity.dxftype() == 'MTEXT':

                        propwork_text_properties = propwork_entity.dxfattribs()

                        propwork_Name = propwork_text_properties.get(
                            'text') if propwork_entity.dxftype() == 'TEXT' else propwork_entity.plain_text()

                        proposedwork_name1 = propwork_Name.lower().replace(" ", "")

                        if propwork_Name != '' and any(proposedwork_name1 == proposedname for proposedname in
                                                       ["east", "west", "north", "south"]) == False:

                            propwork_text_pts = propwork_text_properties.get('insert')

                            plot_point = Point(np.array([propwork_text_pts[0], propwork_text_pts[1]]))

                            if propwork_polygon.contains(plot_point)  or propwork_polygon.touches(
                                    plot_point)  or round(propwork_polygon.distance(plot_point), 1) == 0.0:
                                propworkPolygonContainsLabel.append(
                                    [propwork_Name, propwork_polygon, propwork_entity, propworkpoly_entity])
                                break
                if propworkPolygonContainsLabel != [] and len(propworkPolygonContainsLabel) <= 1:

                    for plotnampoly in propworkPolygonContainsLabel:
                        propwork_dict[propworkPolygonID] = plotnampoly

                elif (len(propworkPolygonContainsLabel) > 1):

                    logging.warning(
                        f'ProposedWork Layer Polygon REF # ({propworkPolygonID}) Found More Than One Label')

                else:

                    logging.warning(
                        f'ProposedWork Layer Polygon REF # ({propworkPolygonID}) Does Not Found Any Label')

        return propwork_dict

    def ResiBuaOutLine_Layer(self, ResiBUAOutLine_data):

        ResiBUAOutLine_dict = dict()

        unique_polygons = {}

        for ResiBUAOutLine_entity in ResiBUAOutLine_data:

            if ResiBUAOutLine_entity.dxftype() == 'LWPOLYLINE' and ResiBUAOutLine_entity.closed and len(
                    [resip[0:2] for resip in ResiBUAOutLine_entity.get_points()]) >= 3:

                ResiBUAOutLinePolygonID = ResiBUAOutLine_entity.dxf.handle

                vertices = tuple(ResiBUAOutLine_entity.get_points())

                if vertices in unique_polygons:

                    logging.warning(
                        f"ResiBUAOutline Layer Found Duplicate Polygon Of {ResiBUAOutLinePolygonID}.")

                else:

                    unique_polygons[vertices] = ResiBUAOutLine_entity

                ResiBUAOutLine_polygon = Polygon(np.array([resip[0:2] for resip in ResiBUAOutLine_entity.get_points()]))

                ResiBUAOutLine_Label = "None"
                for ResiBUAOutLineTEXT_entity in ResiBUAOutLine_data:

                    if ResiBUAOutLineTEXT_entity.dxftype() == 'TEXT' or ResiBUAOutLineTEXT_entity.dxftype() == 'MTEXT':

                        resibuaLabelProperties = ResiBUAOutLineTEXT_entity.dxfattribs()

                        resibua_label = resibuaLabelProperties.get(
                            'text') if ResiBUAOutLineTEXT_entity.dxftype() == 'TEXT' else ResiBUAOutLineTEXT_entity.plain_text()
                        filtered_label = resibua_label.lower().replace(' ', '')
                        if filtered_label != "resi" or filtered_label != "resibua":
                            resibuaLabel_insert = resibuaLabelProperties.get('insert')

                            resibuaLabel_point = Point(np.array([resibuaLabel_insert[0], resibuaLabel_insert[1]]))

                            if ResiBUAOutLine_polygon.contains(
                                    resibuaLabel_point)  or ResiBUAOutLine_polygon.touches(
                                    resibuaLabel_point)  or round(
                                    ResiBUAOutLine_polygon.distance(resibuaLabel_point), 1) == 0.0:
                                ResiBUAOutLine_Label = resibua_label

                ResiBUAOutLine_dict[ResiBUAOutLinePolygonID] = [ResiBUAOutLine_polygon, ResiBUAOutLine_entity,
                                                                ResiBUAOutLine_Label]

        return ResiBUAOutLine_dict

    def CommBuaOutLine_Layer(self, CommBUAOutLine_data):

        CommBUAOutLine_dict = dict()

        unique_polygons = {}

        for CommBUAOutLine_entity in CommBUAOutLine_data:

            if CommBUAOutLine_entity.dxftype() == 'LWPOLYLINE' and CommBUAOutLine_entity.closed:

                CommBUAOutLinePolygonID = CommBUAOutLine_entity.dxf.handle

                vertices = tuple(CommBUAOutLine_entity.get_points())

                if len(vertices)<=2:
                    continue

                if vertices in unique_polygons:

                    logging.warning(
                        f"CommBUAOutline Layer Found Duplicate Polygon Of {CommBUAOutLinePolygonID}.")

                else:

                    unique_polygons[vertices] = CommBUAOutLine_entity


                CommBUAOutLine_polygon = Polygon(np.array([commp[0:2] for commp in CommBUAOutLine_entity.get_points()]))

                CommBUAOutLine_Label = "None"
                for CommBuaOutLineTEXT_entity in CommBUAOutLine_data:

                    if CommBuaOutLineTEXT_entity.dxftype() == 'TEXT' or CommBuaOutLineTEXT_entity.dxftype() == 'MTEXT':

                        commbuaLabelProperties = CommBuaOutLineTEXT_entity.dxfattribs()

                        commbua_label = commbuaLabelProperties.get(
                            'text') if CommBuaOutLineTEXT_entity.dxftype() == 'TEXT' else CommBuaOutLineTEXT_entity.plain_text()
                        filtered_label = commbua_label.lower().replace(' ', '')
                        if filtered_label != "comm" or filtered_label != "commbua":
                            commbuaLabel_insert = commbuaLabelProperties.get('insert')

                            commbuaLabel_point = Point(np.array([commbuaLabel_insert[0], commbuaLabel_insert[1]]))

                            if CommBUAOutLine_polygon.contains(
                                    commbuaLabel_point)  or CommBUAOutLine_polygon.touches(
                                commbuaLabel_point)  or round(
                                CommBUAOutLine_polygon.distance(commbuaLabel_point), 1) == 0.0:
                                CommBUAOutLine_Label = commbua_label

                CommBUAOutLine_dict[CommBUAOutLinePolygonID] = [CommBUAOutLine_polygon, CommBUAOutLine_entity,
                                                                CommBUAOutLine_Label]

        return CommBUAOutLine_dict

    def SpecialBuaOutLine_Layer(self, SpecialBUAOutLine_data):

        SpecialBUAOutLine_dict = dict()

        unique_polygons = {}

        for SpecialBUAOutLine_entity in SpecialBUAOutLine_data:

            if SpecialBUAOutLine_entity.dxftype() == 'LWPOLYLINE' and SpecialBUAOutLine_entity.closed:

                SpecialBUAOutLinePolygonID = SpecialBUAOutLine_entity.dxf.handle

                vertices = tuple(SpecialBUAOutLine_entity.get_points())

                if len(vertices)<=2:
                    continue

                if vertices in unique_polygons:

                    logging.warning(
                        f"SpecialUseBUAOutline Layer Found Duplicate Polygon Of {SpecialBUAOutLinePolygonID}.")

                else:

                    unique_polygons[vertices] = SpecialBUAOutLine_entity

                SpecialBUAOutLine_polygon = Polygon(
                    np.array([speup[0:2] for speup in SpecialBUAOutLine_entity.get_points()]))

                SpecialBUAOutLine_Label = "None"
                for SpecialBUAOutLineTEXT_entity in SpecialBUAOutLine_data:

                    if SpecialBUAOutLineTEXT_entity.dxftype() == 'TEXT' or SpecialBUAOutLineTEXT_entity.dxftype() == 'MTEXT':

                        specialbuaLabelProperties = SpecialBUAOutLineTEXT_entity.dxfattribs()

                        specialbua_label = specialbuaLabelProperties.get(
                            'text') if SpecialBUAOutLineTEXT_entity.dxftype() == 'TEXT' else SpecialBUAOutLineTEXT_entity.plain_text()
                        filtered_label = specialbua_label.lower().replace(' ', '')
                        if filtered_label != "special" or filtered_label != "specialbua":
                            specialbuaLabel_insert = specialbuaLabelProperties.get('insert')

                            specialbuaLabel_point = Point(
                                np.array([specialbuaLabel_insert[0], specialbuaLabel_insert[1]]))

                            if SpecialBUAOutLine_polygon.contains(
                                    specialbuaLabel_point)  or SpecialBUAOutLine_polygon.touches(
                                specialbuaLabel_point)  or round(
                                SpecialBUAOutLine_polygon.distance(specialbuaLabel_point), 1) == 0.0:
                                SpecialBUAOutLine_Label = specialbua_label

                SpecialBUAOutLine_dict[SpecialBUAOutLinePolygonID] = [SpecialBUAOutLine_polygon,
                                                                      SpecialBUAOutLine_entity, SpecialBUAOutLine_Label]

        return SpecialBUAOutLine_dict

    def IndBuaOutLine_Layer(self, IndBUAOutLine_data):

        IndBUAOutLine_dict = dict()

        unique_polygons = {}

        for IndBUAOutLine_entity in IndBUAOutLine_data:

            if IndBUAOutLine_entity.dxftype() == 'LWPOLYLINE':

                IndBUAOutLinePolygonID = IndBUAOutLine_entity.dxf.handle

                vertices = tuple(IndBUAOutLine_entity.get_points())

                if len(vertices)<=2:
                    continue

                if vertices in unique_polygons:

                    logging.warning(
                        f"IndBUAOutline Layer Found Duplicate Polygon Of {IndBUAOutLinePolygonID}.")

                else:

                    unique_polygons[vertices] = IndBUAOutLine_entity

                IndBUAOutLine_polygon = Polygon(np.array([indp[0:2] for indp in IndBUAOutLine_entity.get_points()]))

                IndBUAOutLine_Label = "None"
                for IndBUAOutLineTEXT_entity in IndBUAOutLine_data:

                    if IndBUAOutLineTEXT_entity.dxftype() == 'TEXT' or IndBUAOutLineTEXT_entity.dxftype() == 'MTEXT':

                        indbuaLabelProperties = IndBUAOutLineTEXT_entity.dxfattribs()

                        indbua_label = indbuaLabelProperties.get(
                            'text') if IndBUAOutLineTEXT_entity.dxftype() == 'TEXT' else IndBUAOutLineTEXT_entity.plain_text()

                        filtered_label = indbua_label.lower().replace(' ', '')

                        if filtered_label != "ind" or filtered_label != "indbua":
                            indbuaLabel_insert = indbuaLabelProperties.get('insert')

                            indbuaLabel_point = Point(
                                np.array([indbuaLabel_insert[0], indbuaLabel_insert[1]]))

                            if IndBUAOutLine_polygon.contains(
                                    indbuaLabel_point)  or IndBUAOutLine_polygon.touches(
                                indbuaLabel_point)  or round(
                                IndBUAOutLine_polygon.distance(indbuaLabel_point), 1) == 0.0:
                                IndBUAOutLine_Label = indbua_label

                IndBUAOutLine_dict[IndBUAOutLinePolygonID] = [IndBUAOutLine_polygon, IndBUAOutLine_entity,
                                                              IndBUAOutLine_Label]

        return IndBUAOutLine_dict

    def MarginLineLayer(self, MarginData):

        MarginDict = dict()

        Front_data = []

        Rear_data = []

        Side1_data = []

        Side2_data = []

        for margin_entity in MarginData:

            if margin_entity.dxftype() == 'INSERT':

                for vir_entity in margin_entity.virtual_entities():

                    if vir_entity.dxftype() == 'LINE':

                        if vir_entity.dxf.color == 1:

                            front_line_points = LineString(np.array([(vir_entity.dxf.start[0], vir_entity.dxf.start[1]),
                                                                     (vir_entity.dxf.end[0], vir_entity.dxf.end[1])]))

                            Front_data.append(front_line_points)

                        elif (vir_entity.dxf.color == 6):

                            rear_line_points = LineString(np.array([(vir_entity.dxf.start[0], vir_entity.dxf.start[1]),
                                                                    (vir_entity.dxf.end[0], vir_entity.dxf.end[1])]))

                            Rear_data.append(rear_line_points)


                        elif (vir_entity.dxf.color == 5):

                            side1_line_points = LineString(np.array([(vir_entity.dxf.start[0], vir_entity.dxf.start[1]),
                                                                     (vir_entity.dxf.end[0], vir_entity.dxf.end[1])]))

                            Side1_data.append(side1_line_points)

                        elif (vir_entity.dxf.color == 104 or vir_entity.dxf.color == 3):

                            side2_line_points = LineString(np.array([(vir_entity.dxf.start[0], vir_entity.dxf.start[1]),
                                                                     (vir_entity.dxf.end[0], vir_entity.dxf.end[1])]))

                            Side2_data.append(side2_line_points)

                    elif (vir_entity.dxftype() == 'ARC'):

                        if vir_entity.dxf.color == 1:

                            front_arc_points = LineString(
                                np.array([(vir_entity.start_point[0], vir_entity.start_point[1]),
                                          (vir_entity.end_point[0], vir_entity.end_point[1])]))

                            Front_data.append(front_arc_points)

                        elif (vir_entity.dxf.color == 6):

                            rear_arc_points = LineString(
                                np.array([(vir_entity.start_point[0], vir_entity.start_point[1]),
                                          (vir_entity.end_point[0], vir_entity.end_point[1])]))

                            Rear_data.append(rear_arc_points)


                        elif (vir_entity.dxf.color == 5):

                            side1_arc_points = LineString(
                                np.array([(vir_entity.start_point[0], vir_entity.start_point[1]),
                                          (vir_entity.end_point[0], vir_entity.end_point[1])]))

                            Side1_data.append(side1_arc_points)

                        elif (vir_entity.dxf.color == 104 or vir_entity.dxf.color == 3):

                            side2_arc_points = LineString(
                                np.array([(vir_entity.start_point[0], vir_entity.start_point[1]),
                                          (vir_entity.end_point[0], vir_entity.end_point[1])]))

                            Side2_data.append(side2_arc_points)

            elif (margin_entity.dxftype() == 'LINE'):

                if margin_entity.dxf.color == 1:

                    front_line_points = LineString(np.array([(margin_entity.dxf.start[0], margin_entity.dxf.start[1]),
                                                             (margin_entity.dxf.end[0], margin_entity.dxf.end[1])]))

                    Front_data.append(front_line_points)

                elif (margin_entity.dxf.color == 6):

                    rear_line_points = LineString(np.array([(margin_entity.dxf.start[0], margin_entity.dxf.start[1]),
                                                            (margin_entity.dxf.end[0], margin_entity.dxf.end[1])]))

                    Rear_data.append(rear_line_points)


                elif (margin_entity.dxf.color == 5):

                    side1_line_points = LineString(np.array([(margin_entity.dxf.start[0], margin_entity.dxf.start[1]),
                                                             (margin_entity.dxf.end[0], margin_entity.dxf.end[1])]))

                    Side1_data.append(side1_line_points)

                elif (margin_entity.dxf.color == 104 or margin_entity.dxf.color == 3):

                    side2_line_points = LineString(np.array([(margin_entity.dxf.start[0], margin_entity.dxf.start[1]),
                                                             (margin_entity.dxf.end[0], margin_entity.dxf.end[1])]))

                    Side2_data.append(side2_line_points)

            elif (margin_entity.dxftype() == 'ARC'):

                if margin_entity.dxf.color == 1:

                    front_arc_points = LineString(
                        np.array([(margin_entity.start_point[0], margin_entity.start_point[1]),
                                  (margin_entity.end_point[0], margin_entity.end_point[1])]))

                    Front_data.append(front_arc_points)

                elif (margin_entity.dxf.color == 6):

                    rear_arc_points = LineString(
                        np.array([(margin_entity.start_point[0], margin_entity.start_point[1]),
                                  (margin_entity.end_point[0], margin_entity.end_point[1])]))

                    Rear_data.append(rear_arc_points)


                elif (margin_entity.dxf.color == 5):

                    side1_arc_points = LineString(
                        np.array([(margin_entity.start_point[0], margin_entity.start_point[1]),
                                  (margin_entity.end_point[0], margin_entity.end_point[1])]))

                    Side1_data.append(side1_arc_points)

                elif (margin_entity.dxf.color == 104 or margin_entity.dxf.color == 3):

                    side2_arc_points = LineString(
                        np.array([(margin_entity.start_point[0], margin_entity.start_point[1]),
                                  (margin_entity.end_point[0], margin_entity.end_point[1])]))

                    Side2_data.append(side2_arc_points)

        if len(Front_data) > 0:

            MarginDict['FRONT'] = Front_data

        else:

            logging.warning(f'Margin Layer Polygon does Not Get Red Color For Front Side')

        if len(Rear_data) > 0:

            MarginDict['REAR'] = Rear_data

        else:

            logging.warning(f'Margin Layer Polygon does Not Get Pink Color For Rear Side')

        if len(Side1_data) > 0:

            MarginDict['SIDE1'] = Side1_data

        else:

            logging.warning(f'Margin Layer Polygon does Not Get Blue Color For Side1')

        if len(Side2_data) > 0:

            MarginDict['SIDE2'] = Side2_data

        else:

            logging.warning(f'Margin Layer Polygon does Not Get Green Color For Side2')

        return MarginDict

    def Parking_Layer(self, Parking_data):

        Parking_dict = dict()

        unique_polygons = {}

        for Parkingpoly_entity in Parking_data:

            if Parkingpoly_entity.dxftype() == 'LWPOLYLINE' and Parkingpoly_entity.closed:

                ParkingPolygonID = Parkingpoly_entity.dxf.handle

                vertices = tuple(Parkingpoly_entity.get_points())

                if vertices in unique_polygons:

                        logging.warning(
                        f"Parking Layer Found Duplicate Polygon or Label Of {ParkingPolygonID}.")

                else:

                    unique_polygons[vertices] = Parkingpoly_entity

                if any(Parkingpoly_entity.dxf.color == parkingcolor for parkingcolor in [63, 64, 65]) :

                    if len([pp[0:2] for pp in Parkingpoly_entity.get_points()]) > 3:

                        Parking_polygon_pts = [pp[0:2] for pp in Parkingpoly_entity.get_points()]

                        Parking_polygon = Polygon(Parking_polygon_pts)

                        ParkingPolygonContainsLabel = []

                        for Parking_entity in Parking_data:

                            if Parking_entity.dxftype() == 'TEXT' or Parking_entity.dxftype() == 'MTEXT':

                                Parking_entity_text_properties = Parking_entity.dxfattribs()

                                Parking_Name = Parking_entity_text_properties.get(
                                    'text') if Parking_entity.dxftype() == 'TEXT' else Parking_entity.plain_text()

                                if any(stackp in Parking_Name.lower() for stackp in ['mech', 'stack'])  and any(
                                        stacklc == Parking_entity.dxf.color for stacklc in [63, 64, 65]) :

                                    Parking_text_pts = Parking_entity_text_properties.get('insert')

                                    Parking_point = Point([Parking_text_pts[0], Parking_text_pts[1]])

                                    if Parking_polygon.contains(Parking_point)  or round(
                                            Parking_polygon.distance(Parking_point),
                                            1) == 0.0:
                                        ParkingPolygonContainsLabel.append(
                                            [Parking_Name, Parking_polygon, Parkingpoly_entity])
                                        break

                        if len(ParkingPolygonContainsLabel) > 0:

                            for Parkingnamepoly in ParkingPolygonContainsLabel:
                                Parking_dict[ParkingPolygonID] = Parkingnamepoly

                        else:

                            logging.warning(
                                f'Parking (Stack Parking) Layer Polygon #REF ({ParkingPolygonID}) Does Not Found Any Stack Parking Label')

                else:

                    if len([pp[0:2] for pp in Parkingpoly_entity.get_points()]) > 3:

                        Parking_polygon_pts = [pp[0:2] for pp in Parkingpoly_entity.get_points()]

                        Parking_polygon = Polygon(Parking_polygon_pts)

                        ParkingPolygonContainsLabel = []

                        for textParking_entity in Parking_data:

                            if textParking_entity.dxftype() == 'TEXT' or textParking_entity.dxftype() == 'MTEXT':
                                parking_label_id = textParking_entity.dxf.handle
                                Parking_entity_text_properties = textParking_entity.dxfattribs()

                                Parking_Name = Parking_entity_text_properties.get(
                                    'text') if textParking_entity.dxftype() == 'TEXT' else textParking_entity.plain_text()

                                Parking_text_pts = Parking_entity_text_properties.get('insert')

                                Parking_point = Point([Parking_text_pts[0], Parking_text_pts[1]])

                                if Parking_polygon.contains(Parking_point) :
                                    ParkingPolygonContainsLabel.append(
                                        [Parking_Name, Parking_polygon, Parkingpoly_entity, parking_label_id])
                                    # break
                        if len(ParkingPolygonContainsLabel) == 1:

                            for Parkingnamepoly in ParkingPolygonContainsLabel:

                                Parking_dict[Parkingnamepoly[3]] = [Parkingnamepoly[0], Parkingnamepoly[1],
                                                                    Parkingnamepoly[2]]

                        elif (len(ParkingPolygonContainsLabel) > 1):

                            check_parking = [str(Parkingnamepoly[0].replace(' ', '')).lower() == 'parking' for
                                             Parkingnamepoly in ParkingPolygonContainsLabel]

                            if any(check_parking) == False:
                                logging.warning(
                                    f'Parking Layer Polygon #REF ({ParkingPolygonID}) Does Not Found Any Label')
                            for Parkingnamepoly in ParkingPolygonContainsLabel:
                                Parking_dict[Parkingnamepoly[3]] = [Parkingnamepoly[0], Parkingnamepoly[1],
                                                                    Parkingnamepoly[2]]
                        else:

                            logging.warning(
                                f'Parking Layer Polygon #REF ({ParkingPolygonID}) Does Not Found Any Label')

        return Parking_dict

    def OrganizedOpenSpace_Layer(self, OrganizedOpenSpace_data):

        organizedOpenspace_dict = dict()

        unique_polygons = {}

        for org_polyentity in OrganizedOpenSpace_data:

            if org_polyentity.dxftype() == 'LWPOLYLINE' and org_polyentity.closed:

                orgPolygonID = org_polyentity.dxf.handle

                points=list(org_polyentity.get_points())

                if len(points)<=2:
                    continue

                org_polygon = Polygon(np.array([org[0:2] for org in org_polyentity.get_points()]))

                if not org_polygon.is_valid:
                    org_polygon = make_valid(org_polygon)

                vertices = tuple(org_polyentity.get_points())

                if vertices in unique_polygons:

                    logging.warning(
                        f" Organized OpenSpace Layer Found Duplicate Polygon Of {orgPolygonID}.")

                else:

                    unique_polygons[vertices] = org_polyentity

                orgPolygonContainsLabel = []

                for org_entity in OrganizedOpenSpace_data:

                    if org_entity.dxftype() == 'TEXT' or org_entity.dxftype() == 'MTEXT':

                        org_text_properties = org_entity.dxfattribs()

                        org_Name = org_text_properties.get(
                            'text') if org_entity.dxftype() == 'TEXT' else org_entity.plain_text()

                        org_text_pts = org_text_properties.get('insert')

                        org_point = Point(np.array([org_text_pts[0], org_text_pts[1]]))

                        if org_polygon.contains(org_point)  or org_polygon.touches(org_point)  or round(
                                org_polygon.distance(org_point), 1) == 0.0:
                            orgPolygonContainsLabel.append([org_Name, org_polygon, org_polyentity])
                            break
                if len(orgPolygonContainsLabel) > 0 and len(orgPolygonContainsLabel) <= 1:

                    for orgnampoly in orgPolygonContainsLabel:
                        organizedOpenspace_dict[orgPolygonID] = orgnampoly

                elif (len(orgPolygonContainsLabel) > 1):

                    logging.warning(
                        f'OrganizedOpenSpace Layer Polygon REF # ({orgPolygonID}) Found More Than One Label')

                else:

                    logging.warning(
                        f'OrganizedOpenSpace Layer Polygon REF # ({orgPolygonID}) Does Not Found Any Label')

        return organizedOpenspace_dict

    def Plot_Layer(self, Plot_Data):

        plot_dict = dict()

        unique_polygons = {}

        for Plot_entity in Plot_Data:

            if Plot_entity.dxftype() == 'LWPOLYLINE' and Plot_entity.closed:

                plotPolygonID = Plot_entity.dxf.handle

                points=list(Plot_entity.get_points())

                if len(points)<=2:
                    continue

                plot_polygon = Polygon(np.array([pp[0:2] for pp in Plot_entity.get_points()]))

                vertices = tuple(Plot_entity.get_points())

                if vertices in unique_polygons:

                    logging.warning(f"Plot Layer Found Duplicate Polygon Of {plotPolygonID}.")

                else:

                    unique_polygons[vertices] = Plot_entity

                plotPolygonContainsLabel = []

                for Plot_entity in Plot_Data:

                    if Plot_entity.dxftype() == 'TEXT' or Plot_entity.dxftype() == 'MTEXT':

                        plot_text_properties = Plot_entity.dxfattribs()

                        plot_Name = plot_text_properties.get(
                            'text') if Plot_entity.dxftype() == 'TEXT' else Plot_entity.plain_text()

                        plot_Namex = plot_Name.strip().replace(' ', '')

                        if 'plot' == plot_Namex.lower():

                            plot_text_pts = plot_text_properties.get('insert')

                            plot_point = Point(np.array([plot_text_pts[0], plot_text_pts[1]]))

                            if plot_polygon.contains(plot_point)  or round(plot_polygon.distance(plot_point),
                                                                                  1) == 0.0:
                                plotPolygonContainsLabel.append([plot_Name, plot_polygon])
                                break
                if plotPolygonContainsLabel != [] and len(plotPolygonContainsLabel) <= 1:

                    for plotnampoly in plotPolygonContainsLabel:
                        plot_dict[plotPolygonID] = plotnampoly

                elif (len(plotPolygonContainsLabel) > 1):

                    logging.warning(
                        f'Plot Layer Polygon REF # ({plotPolygonID}) Found More Than One Label')

                else:

                    logging.warning(
                        f'Plot Layer Polygon REF # ({plotPolygonID}) Does Not Found Any Label')

        return plot_dict

    def Section_Layer(self, Section_data):

        Section_dict = dict()

        ErrorSection_dict = dict()

        unique_polygons = {}

        for Section_entity in Section_data:

            if Section_entity.dxftype() == 'LWPOLYLINE' and Section_entity.closed:

                SectionPolygonID = Section_entity.dxf.handle

                points=list(Section_entity.get_points())

                if len(points)<=2:
                    continue

                Section_polygon = Polygon(np.array([sp[0:2] for sp in Section_entity.get_points()]))

                vertices = tuple(Section_entity.get_points())

                if vertices in unique_polygons:

                    ErrorSection_dict[SectionPolygonID] = str(
                        f"Section Layer Found Duplicate Polygon Of {SectionPolygonID}.")

                else:

                    unique_polygons[vertices] = Section_entity

                SectionPolygonContainsLabel = []

                for Section_entity in Section_data:

                    if Section_entity.dxftype() == 'TEXT' or Section_entity.dxftype() == 'MTEXT':

                        Section_entity_text_properties = Section_entity.dxfattribs()

                        Section_Name = Section_entity_text_properties.get(
                            'text') if Section_entity.dxftype() == 'TEXT' else Section_entity.plain_text()
                        # print(Section_Name)

                        Section_text_pts = Section_entity_text_properties.get('insert')

                        Section_point = Point(np.array([Section_text_pts[0], Section_text_pts[1]]))

                        if Section_polygon.contains(Section_point) == True or Section_polygon.touches(
                                Section_point) == True or round(Section_polygon.distance(Section_point), 1) == 0.0:
                            SectionPolygonContainsLabel.append([Section_Name, Section_polygon])
                            break
                if SectionPolygonContainsLabel != [] and len(SectionPolygonContainsLabel) <= 1:

                    for Sectionnamepoly in SectionPolygonContainsLabel:
                        Section_dict[SectionPolygonID] = Sectionnamepoly

                elif (len(SectionPolygonContainsLabel) > 1):

                    ErrorSection_dict[SectionPolygonID] = str(
                        f'Warning- Section Layer Polygon REF # ({SectionPolygonID}) Found More Than One Label')

                else:

                    ErrorSection_dict[SectionPolygonID] = str(
                        f'Warning- Section Layer Polygon REF # ({SectionPolygonID}) Does Not Found Any Label')
        # print(Section_dict)
        return [ErrorSection_dict, Section_dict]

    def FloorInSection_Layer(self, FloorInSection_data):

        FloorInSection_dict = dict()

        ErrorFloorInSection_dict = dict()

        unique_polygons = {}

        for FloorInSection_entity in FloorInSection_data:

            if FloorInSection_entity.dxftype() == 'LWPOLYLINE' and FloorInSection_entity.closed:

                FloorInSectionPolygonID = FloorInSection_entity.dxf.handle

                points=list(FloorInSection_entity.get_points())

                if len(points)<=2:
                    continue

                FloorInSection_polygon = Polygon(np.array([fisp[0:2] for fisp in FloorInSection_entity.get_points()]))

                vertices = tuple(FloorInSection_entity.get_points())

                if vertices in unique_polygons:

                    ErrorFloorInSection_dict[FloorInSectionPolygonID] = str(
                        f"FloorInSection Layer Found Duplicate Polygon Of {FloorInSectionPolygonID}.")

                else:

                    unique_polygons[vertices] = FloorInSectionPolygonID

                FloorInSectionPolygonContainsLabel = []

                for FloorInSection_entity in FloorInSection_data:

                    if FloorInSection_entity.dxftype() == 'TEXT' or FloorInSection_entity.dxftype() == 'MTEXT':

                        FloorInSection_entity_text_properties = FloorInSection_entity.dxfattribs()

                        FloorInSection_Name = FloorInSection_entity_text_properties.get(
                            'text') if FloorInSection_entity.dxftype() == 'TEXT' else FloorInSection_entity.plain_text()

                        if FloorInSection_Name.lower().replace(" ","") == "":

                            continue

                        FloorInSection_text_pts = FloorInSection_entity_text_properties.get('insert')

                        FloorInSection_point = Point(np.array([FloorInSection_text_pts[0], FloorInSection_text_pts[1]]))

                        if FloorInSection_polygon.contains(
                                FloorInSection_point) == True or FloorInSection_polygon.touches(
                                FloorInSection_point) == True or round(
                                FloorInSection_polygon.distance(FloorInSection_point), 1) == 0.0:
                            FloorInSectionPolygonContainsLabel.append([FloorInSection_Name, FloorInSection_polygon,FloorInSection_point])
                            break
                if FloorInSectionPolygonContainsLabel != [] and len(FloorInSectionPolygonContainsLabel) > 0:

                    for FloorInSectionnamepoly in FloorInSectionPolygonContainsLabel:
                        FloorInSection_dict[FloorInSectionPolygonID] = FloorInSectionnamepoly

                elif (FloorInSectionPolygonContainsLabel != [] and len(FloorInSectionPolygonContainsLabel) > 1):

                    ErrorFloorInSection_dict[FloorInSectionPolygonID] = str(
                        f'Warning- FloorInSection Layer Polygon REF # ({FloorInSectionPolygonID}) Contain More than One Label')

                else:

                    ErrorFloorInSection_dict[FloorInSectionPolygonID] = str(
                        f'Warning- FloorInSection Layer Polygon REF # ({FloorInSectionPolygonID}) Does Not Found Any Label')

        return [ErrorFloorInSection_dict, FloorInSection_dict]

    def GroundLevel_Layer(self, GroundLevel_data):

        GroundLevel_dict = dict()

        ErrorGroundLevel_dict = dict()

        unique_polygons = {}

        for GroundLevel_entity in GroundLevel_data:

            GroundLevelPolygonID = GroundLevel_entity.dxf.handle
            ground_line = None
            ground_entity = None
            if GroundLevel_entity.dxftype() == 'LWPOLYLINE' and not GroundLevel_entity.closed:
                ground_entity = GroundLevel_entity

                ground_line = LineString(GroundLevel_entity.get_points("xy"))

                vertices = tuple(GroundLevel_entity.get_points("xy"))

                if vertices in unique_polygons:

                    ErrorGroundLevel_dict[GroundLevelPolygonID] = str(
                        f"GroundLevel Layer Found Duplicate Polyline Of {GroundLevelPolygonID}.")

                else:

                    unique_polygons[vertices] = GroundLevel_entity

            elif GroundLevel_entity.dxftype() == 'LINE':
                ground_entity = GroundLevel_entity

                line_pts = [(GroundLevel_entity.dxf.start[0], GroundLevel_entity.dxf.start[1]),
                            (GroundLevel_entity.dxf.end[0], GroundLevel_entity.dxf.end[1])]

                ground_line = LineString(line_pts)

                vertices = tuple(line_pts)

                if vertices in unique_polygons:

                    ErrorGroundLevel_dict[GroundLevelPolygonID] = str(
                        f"GroundLevel Layer Found Duplicate Polyline Of {GroundLevelPolygonID}.")

                else:

                    unique_polygons[vertices] = GroundLevel_entity

            if ground_line:

                GroundLevelPolygonContainsLabel = []

                for GroundLeveltext_entity in GroundLevel_data:

                    if GroundLeveltext_entity.dxftype() == 'TEXT' or GroundLeveltext_entity.dxftype() == 'MTEXT':

                        GroundLevel_entity_text_properties = GroundLeveltext_entity.dxfattribs()

                        GroundLevel_Name = GroundLevel_entity_text_properties.get(
                            'text') if GroundLeveltext_entity.dxftype() == 'TEXT' else GroundLeveltext_entity.plain_text()

                        GroundLevel_text_pts = GroundLevel_entity_text_properties.get('insert')

                        GroundLevel_point = Point(np.array([GroundLevel_text_pts[0], GroundLevel_text_pts[1]]))

                        if ground_line.touches(GroundLevel_point) or round(
                                ground_line.distance(GroundLevel_point)) == 0:
                            GroundLevelPolygonContainsLabel.append([GroundLevel_Name, ground_line, ground_entity])
                            break
                if GroundLevelPolygonContainsLabel and len(GroundLevelPolygonContainsLabel) <= 1:

                    for GroundLevelnamepoly in GroundLevelPolygonContainsLabel:
                        GroundLevel_dict[GroundLevelPolygonID] = GroundLevelnamepoly

                elif (len(GroundLevelPolygonContainsLabel) > 1):

                    ErrorGroundLevel_dict[GroundLevelPolygonID] = str(
                        f'Warning- GroundLevel Layer Line REF # ({GroundLevelPolygonID}) Found More Than One Label')

                else:

                    ErrorGroundLevel_dict[GroundLevelPolygonID] = str(
                        f'Warning- GroundLevel Layer Line REF # ({GroundLevelPolygonID}) Does Not Found Any Label')

        return [ErrorGroundLevel_dict, GroundLevel_dict]

    def ExistingStructure(self,queries):

        ErrorDict = dict()
        ValueDict = dict()
        for query in queries:

            if query.dxftype() == "LWPOLYLINE" and query.closed:
                polygon_id = query.dxf.handle
                polygon_pts = query.get_points("xy")

                if len(polygon_pts)<2:
                # if len(polygon_pts) < 3:
                    continue

                polygon_points = Polygon(polygon_pts)

                text_label = None
                text_point = None
                for query1 in queries:

                    if query1.dxftype() in ("TEXT","MTEXT"):

                        text_point = Point(query1.dxf.insert[0],query1.dxf.insert[1])

                        if polygon_points.contains(text_point) or round(polygon_points.distance(text_point),1) == 0.0:

                            text_label = query1.dxf.text if query1.dxftype() =="TEXT" else query1.plain_text()

                            break

                if text_label and text_point:
                    ValueDict[polygon_id] = (text_label,polygon_points,query)

                else:

                    ErrorDict[polygon_id] = f'Warning- Door Layer Polygon ({polygon_id}) Does Not Found Any Label'

        return ErrorDict, ValueDict

    def FireDrivewayLayerDict(self, FireDrivewayData):

        FireDrivewayDict = dict()
        try:
            text_entities=[FireDriveway_text for FireDriveway_text in FireDrivewayData if FireDriveway_text.dxftype() in ('TEXT', 'MTEXT')]
            polygon_entities=[FireDriveway_poly for FireDriveway_poly in FireDrivewayData if FireDriveway_poly.dxftype() == 'LWPOLYLINE' and FireDriveway_poly.closed]
            center_polylines = [FireDriveway_poly for FireDriveway_poly in FireDrivewayData if FireDriveway_poly.dxftype() == 'LWPOLYLINE' and not FireDriveway_poly.closed]

            for FireDriveway_text in text_entities:

                FireDriveway_Label = FireDriveway_text.dxf.text if FireDriveway_text.dxftype() == 'TEXT' else FireDriveway_text.plain_text()

                FireDriveway_Label_ID = FireDriveway_text.dxf.handle

                FireDrivewayLabel_point = Point([FireDriveway_text.dxf.insert[0], FireDriveway_text.dxf.insert[1]])

                FireDrivewaypolygons= []

                for FireDriveway_poly in polygon_entities:
                    try:
                        FireDrivewayPoly_ID = FireDriveway_poly.dxf.handle

                        FireDriveway_polygon_pts=[bp[0:2] for bp in FireDriveway_poly.get_points()]

                        if len(FireDriveway_polygon_pts)<3:
                            continue

                        FireDriveway_polygon_points = Polygon(FireDriveway_polygon_pts)

                        if FireDriveway_polygon_points.contains(FireDrivewayLabel_point) or round(FireDriveway_polygon_points.distance(FireDrivewayLabel_point),1)==0.0:

                            FireDrivewaypolygons.append([FireDrivewayPoly_ID, FireDriveway_Label, FireDriveway_polygon_points,FireDriveway_poly])

                    except Exception:
                        logging.error(traceback.print_exc())
                        continue

                if FireDrivewaypolygons:

                    for FireDriveway_data in FireDrivewaypolygons:

                        list_center_entities = []

                        for cen_line_entity in center_polylines:

                            if str(cen_line_entity.dxf.linetype).lower() == "center":

                                center_line =[True if round(FireDriveway_data[2].distance(Point(pts)),1)==0.0 else False for pts in cen_line_entity.get_points("xy")]
                                if all(center_line):
                                    list_center_entities.append(cen_line_entity)

                        if not list_center_entities:

                            logging.warning(f"Missing CenterLine in #REF({FireDriveway_data[0]}) of {FireDriveway_data[1]}.")

                        holse_polygons=[]

                        for FireDriveway_holes in polygon_entities:
                            try:
                                holes_poly_pts=[fdh_pts[0:2] for fdh_pts in FireDriveway_holes.get_points()]
                                if len(holes_poly_pts)<3:
                                    continue
                                holse_polygon=Polygon(holes_poly_pts)

                                if FireDriveway_data[2].contains(holse_polygon) and not FireDriveway_data[2].equals(holse_polygon):

                                    holse_polygons.append(holse_polygon)
                            except Exception:
                                logging.error(traceback.print_exc())
                                continue

                        if holse_polygons:
                            holsex_polygon=Polygon(shell=FireDriveway_data[2].exterior.coords, holes=[inner_polygon.exterior.coords for inner_polygon in holse_polygons])

                            FireDrivewayDict[FireDriveway_data[0]] =(FireDriveway_data[1],holsex_polygon,FireDriveway_data[3],list_center_entities)

                        else:

                            FireDrivewayDict[FireDriveway_data[0]] = (FireDriveway_data[1], FireDriveway_data[2],FireDriveway_data[3],list_center_entities)
                else:
                    logging.warning(f'LABEL #REF ({FireDriveway_Label_ID}) Missing Label')

        except Exception:
            logging.error(traceback.print_exc())
        return FireDrivewayDict

    def Modfy_TextMtext_FloorInSection_Layer(self, FloorInSection_data, scale_factor=2, fixed_height=0.4, fixed_width_factor=None):
        """
        FLOORINSECTION layer ke TEXT aur MTEXT ka font size aur width modify karega.
        :param FloorInSection_data: (list) entities jo FLOORINSECTION layer se nikali gayi hain
        :param scale_factor: (float) size kitna multiply karna hai (default=2)
        :param fixed_height: (float) agar fixed height set karna hai to yeh use hoga
        :param fixed_width_factor: (float) agar fixed width factor/width dena hai to yeh use hoga
        """

        for FloorInSection_entity in FloorInSection_data:

            # --- TEXT ---
            if FloorInSection_entity.dxftype() == 'TEXT':
                # Height
                if fixed_height:
                    FloorInSection_entity.dxf.height = fixed_height
                else:
                    FloorInSection_entity.dxf.height *= scale_factor

                # Width (width_factor)
                if fixed_width_factor:
                    FloorInSection_entity.dxf.width = fixed_width_factor
                else:
                    FloorInSection_entity.dxf.width *= scale_factor

            # --- MTEXT ---
            elif FloorInSection_entity.dxftype() == 'MTEXT':
                # Height
                if fixed_height:
                    FloorInSection_entity.dxf.char_height = fixed_height
                else:
                    FloorInSection_entity.dxf.char_height *= scale_factor

                # Width (column width)
                if fixed_width_factor:
                    FloorInSection_entity.dxf.width = fixed_width_factor

                elif FloorInSection_entity.dxf.width > 0:  # only if already set
                    FloorInSection_entity.dxf.width *= scale_factor

    def Modify_TextMtext_GLSection_Layer(self, GroundLevel_data, scale_factor=1, fixed_height=0.5, fixed_width_factor=None):
                                         # fixed_width_factor=None):
        """
        GROUNDLEVEL layer ke TEXT aur MTEXT ka font size aur width modify karega.
        """

        for GroundLevel_entity in GroundLevel_data:
            # --- TEXT ---
            if GroundLevel_entity.dxftype() == "TEXT":
                # Height
                if fixed_height:
                    GroundLevel_entity.dxf.height = fixed_height
                else:
                    GroundLevel_entity.dxf.height *= scale_factor

                # Width (Width Factor)
                if fixed_width_factor:
                    GroundLevel_entity.dxf.width = fixed_width_factor
                else:
                    GroundLevel_entity.dxf.width *= scale_factor

            # --- MTEXT ---
            elif GroundLevel_entity.dxftype() == "MTEXT":
                # Height
                if fixed_height:
                    GroundLevel_entity.dxf.char_height = fixed_height
                else:
                    GroundLevel_entity.dxf.char_height *= scale_factor

                # Width (column width)
                if fixed_width_factor:
                    GroundLevel_entity.dxf.width = fixed_width_factor
                elif GroundLevel_entity.dxf.width > 0:
                    GroundLevel_entity.dxf.width *= scale_factor

    def Modify_TextMtext_LiftInSection_Layer(self,Lift_data, SectionLayerDict, scale_factor=0, fixed_height=0.3, fixed_width_factor=None):

        for Section_id,section_values in SectionLayerDict.items():
            section_polygon=section_values[1]

            for Lift_entity in Lift_data:
                if Lift_entity.dxftype() == 'TEXT' or Lift_entity.dxftype() == 'MTEXT':
                    Lift_Label = Lift_entity.dxf.text if Lift_entity.dxftype() == 'TEXT' else Lift_entity.plain_text()
                    lift_po = [Lift_entity.dxf.insert[0], Lift_entity.dxf.insert[1]]
                    lift_point = Point(lift_po)

                    if section_polygon.contains(lift_point):
                        # --- TEXT ---
                        if Lift_entity.dxftype() == "TEXT":
                            # Height
                            if fixed_height:
                                Lift_entity.dxf.height = fixed_height
                            else:
                                Lift_entity.dxf.height *= scale_factor

                            # Width (Width Factor)
                            if fixed_width_factor:
                                Lift_entity.dxf.width = fixed_width_factor
                            else:
                                Lift_entity.dxf.width *= scale_factor

                        # --- MTEXT ---
                        elif Lift_entity.dxftype() == "MTEXT":
                            # Height
                            if fixed_height:
                                Lift_entity.dxf.char_height = fixed_height
                            else:
                                Lift_entity.dxf.char_height *= scale_factor

                            # Width (column width)
                            if fixed_width_factor:
                                Lift_entity.dxf.width = fixed_width_factor
                            elif Lift_entity.dxf.width > 0:
                                Lift_entity.dxf.width *= scale_factor

    def Modify_TextMtext_StaircaseSection_Layer(self,staircase_data, SectionLayerDict, scale_factor=1, fixed_height=0.6, fixed_width_factor=None):
        for Section_id,section_values in SectionLayerDict.items():
            section_polygon=section_values[1]

            for staircase_entity in staircase_data:
                if staircase_entity.dxftype() == 'TEXT' or staircase_entity.dxftype() == 'MTEXT':
                    staircase_Label = staircase_entity.dxf.text if staircase_entity.dxftype() == 'TEXT' else staircase_entity.plain_text()
                    staircase_po = [staircase_entity.dxf.insert[0], staircase_entity.dxf.insert[1]]
                    staircase_point = Point(staircase_po)

                    if section_polygon.contains(staircase_point):
                        # --- TEXT ---
                        if staircase_entity.dxftype() == "TEXT":
                            # Height
                            if fixed_height:
                                staircase_entity.dxf.height = fixed_height
                            else:
                                staircase_entity.dxf.height *= scale_factor

                            # Width (Width Factor)
                            if fixed_width_factor:
                                staircase_entity.dxf.width = fixed_width_factor
                            else:
                                staircase_entity.dxf.width *= scale_factor

                        # --- MTEXT ---
                        elif staircase_entity.dxftype() == "MTEXT":
                            # Height
                            if fixed_height:
                                staircase_entity.dxf.char_height = fixed_height
                            else:
                                staircase_entity.dxf.char_height *= scale_factor

                            # Width (column width)
                            if fixed_width_factor:
                                staircase_entity.dxf.width = fixed_width_factor
                            elif staircase_entity.dxf.width > 0:
                                staircase_entity.dxf.width *= scale_factor

    def DimeOf_FloorBuildingHeight(self, FloorInSectionDict, GroundLevelDict, SectionLayerDict):

        start_end_point = []
        Terrace_Polygon = None
        # max_gl_points =[]

        for Section_id, section_values in SectionLayerDict.items():
            section_polygon = section_values[1]
            terrace_inSection = False
            flSEction_Polygon = []

            for FlSection_id, FlSection_values in FloorInSectionDict.items():
                FlSection_polygon = FlSection_values[1]

                if section_polygon.contains(FlSection_polygon):
                    flsection_label = FlSection_values[0]
                    flsection_name = flsection_label.lower()
                    minx, miny, maxx, maxy = FlSection_polygon.bounds
                    start_end_point.append(((minx, miny), (minx, maxy)))  # 2-point tuple
                    flSEction_Polygon.append(FlSection_values[1])

                    if "terrace" in flsection_name:
                        Terrace_Polygon = FlSection_values[1]
                        terrace_inSection = True

            if terrace_inSection:

                for GLevel_id, GLevel_values in GroundLevelDict.items():

                    GLevel_linepo = GLevel_values[1]
                    GLine_length = GLevel_linepo.length

                    # -------- If GL line is not inside section polygon skip --------
                    if not section_polygon.contains(GLevel_linepo):
                        continue

                    # -------- FIND TOUCHING FLOOR POLYGON --------
                    touching_floor_polygon = None

                    for FlSection_id, FlSection_values in FloorInSectionDict.items():

                        floor_poly = FlSection_values[1]

                        if round(floor_poly.distance(GLevel_linepo), 1) == 0 or floor_poly.touches(GLevel_linepo):
                            touching_floor_polygon = floor_poly
                            break

                    if touching_floor_polygon is None:
                        continue

                    # -------- FLOOR POLYGON WIDTH --------
                    minx, miny, maxx, maxy = touching_floor_polygon.bounds
                    flsection_polygon_width = maxx - minx

                    # -------- CONDITION TO EXTEND --------
                    if GLine_length <= flsection_polygon_width:

                        coords = list(GLevel_linepo.coords)
                        (x1, y1) = coords[0]
                        (x2, y2) = coords[1]

                        # -------- FIND TRUE LEFT/RIGHT POINTS --------
                        # Right side will be extended
                        if x1 < x2:
                            left_x, left_y = x1, y1
                            right_x, right_y = x2, y2
                        else:
                            left_x, left_y = x2, y2
                            right_x, right_y = x1, y1

                        # -------- FLOOR POLYGON RIGHT-SIDE BOUNDARY --------
                        poly_right_x = maxx

                        # -------- FINAL EXTENDED POINT --------
                        stop_x = poly_right_x
                        stop_y = right_y

                        # -------- FINAL LINE = (ORIGINAL LEFT → STOP POINT) --------
                        final_line = [(left_x, left_y), (stop_x, stop_y)]

                        # -------- UPDATE DXF ENTITY --------
                        gl_entity = GLevel_values[2]

                        if gl_entity.dxftype() == "LINE":
                            gl_entity.dxf.start = final_line[0]
                            gl_entity.dxf.end = final_line[1]

                        elif gl_entity.dxftype() == "LWPOLYLINE":
                            gl_entity.set_points(final_line)

                        # -------- TERRACE NEAREST LOGIC --------
                        final_line_geom = LineString(final_line)

                        minx_t, miny_t, maxx_t, maxy_t = Terrace_Polygon.bounds
                        terrace_corner = Point(maxx_t, miny_t)

                        dimension_x = maxx_t
                        # Select GL Y (nearest Y from extended line)
                        coords = list(final_line_geom.coords)
                        (x1, y1) = coords[0]
                        (x2, y2) = coords[1]

                        if abs(y1 - terrace_corner.y) < abs(y2 - terrace_corner.y):
                            gl_y = y1
                        else:
                            gl_y = y2

                        new_gl_terrace_point = [
                            (dimension_x, terrace_corner.y),  # terrace point
                            (dimension_x, gl_y)  # GL point
                        ]

                        start_end_point.append(new_gl_terrace_point)

                    else:
                        # ------------------- NO EXTEND ----------------------
                        minx, miny, maxx, maxy = Terrace_Polygon.bounds
                        dim_x = maxx
                        # terrace right-bottom
                        terrace_y = miny
                        # fix GL point vertically
                        coords = list(GLevel_linepo.coords)
                        (gx1, gy1) = coords[0]
                        (gx2, gy2) = coords[1]
                        # choose closer Y
                        if abs(gy1 - terrace_y) < abs(gy2 - terrace_y):
                            gl_y = gy1
                        else:
                            gl_y = gy2
                        gl_terrace_point = [
                            (dim_x, terrace_y),
                            (dim_x, gl_y)
                        ]
                        start_end_point.append(gl_terrace_point)

            else:
                max_distance = 0.0
                max_polygon = None
                max_gline = None

                for flsection_poly in flSEction_Polygon:
                    # Compute width of this floor polygon
                    minx, miny, maxx, maxy = flsection_poly.bounds
                    flsection_polygon_width = maxx - minx

                    for GLevel_id, GLevel_values in GroundLevelDict.items():
                        GLevel_linepo = GLevel_values[1]
                        GLine_length = GLevel_linepo.length

                        # ------------------- IF GL is small → extend first -------------------
                        if GLine_length <= flsection_polygon_width:
                            coords = list(GLevel_linepo.coords)
                            (x1, y1) = coords[0]
                            (x2, y2) = coords[1]

                            # -------- FIND TRUE LEFT/RIGHT POINTS --------
                            # Right side will be extended
                            if x1 < x2:
                                left_x, left_y = x1, y1
                                right_x, right_y = x2, y2
                            else:
                                left_x, left_y = x2, y2
                                right_x, right_y = x1, y1

                            # -------- FLOOR POLYGON RIGHT-SIDE BOUNDARY --------
                            poly_right_x = maxx

                            # -------- FINAL EXTENDED POINT --------
                            stop_x = poly_right_x
                            stop_y = right_y

                            # -------- FINAL LINE = (ORIGINAL LEFT → STOP POINT) --------
                            final_line = [(left_x, left_y), (stop_x, stop_y)]

                            # -------- UPDATE DXF ENTITY --------
                            gl_entity = GLevel_values[2]

                            if gl_entity.dxftype() == "LINE":
                                gl_entity.dxf.start = final_line[0]
                                gl_entity.dxf.end = final_line[1]

                            elif gl_entity.dxftype() == "LWPOLYLINE":
                                gl_entity.set_points(final_line)

                            # -------- TERRACE NEAREST LOGIC --------
                            final_line_geom = LineString(final_line)

                            # distance based on extended GL
                            distance = round(final_line_geom.distance(flsection_poly), 1)

                            if distance > max_distance:
                                max_distance = distance
                                max_polygon = flsection_poly
                                max_gline = final_line_geom  # <-- STORE EXTENDED LINE HERE

                        # ------------------- IF GL already long → use original line -------------------
                        else:
                            distance = round(GLevel_linepo.distance(flsection_poly),1)
                            if distance > max_distance:
                                max_distance = distance
                                max_polygon = flsection_poly
                                max_gline = GLevel_linepo  # <-- STORE ORIGINAL GL LINE

                if max_distance > 0 and max_polygon and max_gline:
                    minx, miny, maxx, maxy = max_polygon.bounds
                    dim_x = maxx
                    top_point = (dim_x, maxy)

                    # select nearest GL Y
                    coords = list(max_gline.coords)
                    (gx1, gy1) = coords[0]
                    (gx2, gy2) = coords[1]

                    if abs(gy1 - maxy) < abs(gy2 - maxy):
                        gl_y = gy1
                    else:
                        gl_y = gy2

                    bottom_point = (dim_x, gl_y)

                    max_gl_terrace_point = [top_point, bottom_point]
                    start_end_point.append(max_gl_terrace_point)

        return start_end_point

    def Siteplan_Layer(self, SitePlan_Data):

        siteplan_dict = dict()

        unique_polygons = {}

        for Siteplan_entity in SitePlan_Data:

            if Siteplan_entity.dxftype() == 'LWPOLYLINE' and Siteplan_entity.closed:

                points = list(Siteplan_entity.get_points())

                if len(points) <= 2:
                    continue

                SitePlanPolygonID = Siteplan_entity.dxf.handle

                siteplan_polygon = Polygon(np.array([bp[0:2] for bp in Siteplan_entity.get_points()]))

                siteplan_coord = list(siteplan_polygon.exterior.coords)
                # print("Siteplan", siteplan_coord)

                vertices = tuple(Siteplan_entity.get_points())

                if vertices in unique_polygons:
                    logging.info(
                        f"Building Layer Found Duplicate Polygon Of {SitePlanPolygonID}.")

                else:
                    unique_polygons[vertices] = Siteplan_entity

                SitePlanPolygonContainsLabel = []

                for Siteplan_entity in SitePlan_Data:

                    if Siteplan_entity.dxftype() == 'TEXT' or Siteplan_entity.dxftype() == 'MTEXT':

                        siteplan_text_properties = Siteplan_entity.dxfattribs()


                        SitePlan_Name = siteplan_text_properties.get(
                            'text') if Siteplan_entity.dxftype() == 'TEXT' else Siteplan_entity.plain_text()

                        # print(SitePlan_Name)
                        if SitePlan_Name != '':
                            siteplan_text_pts = siteplan_text_properties.get('insert')

                            siteplan_point = Point(np.array([siteplan_text_pts[0], siteplan_text_pts[1]]))

                            if siteplan_polygon.contains(siteplan_point) or siteplan_polygon.touches(
                                    siteplan_point) or round(siteplan_polygon.distance(siteplan_point),
                                                             1) == 0.0:
                                SitePlanPolygonContainsLabel.append([SitePlan_Name, siteplan_polygon])
                                break

                if SitePlanPolygonContainsLabel != [] and len(SitePlanPolygonContainsLabel) <= 1:

                    for siteplannampoly in SitePlanPolygonContainsLabel:
                        siteplan_dict[SitePlanPolygonID] = siteplannampoly

                elif (len(SitePlanPolygonContainsLabel) > 1):

                    logging.warning(
                        f'Building Layer Polygon REF # {SitePlanPolygonID} Found More Than One Label')

                else:

                    logging.warning(
                        f'Building Layer Polygon REF # {SitePlanPolygonID} Does Not Found Any Label')

        return siteplan_dict

    def PrintAdditionalDetail_Layer(self,PrintAdditionalDetail_Data):

        padetail_dict = dict()

        unique_polygons = {}

        for PrintAdditionalDetail_entity in PrintAdditionalDetail_Data:

            if PrintAdditionalDetail_entity.dxftype() == 'LWPOLYLINE' and PrintAdditionalDetail_entity.closed:

                points=list(PrintAdditionalDetail_entity.get_points())

                if len(points) <=2:
                    continue

                PADetailPolygonID = PrintAdditionalDetail_entity.dxf.handle

                PADetail_polygon = Polygon(np.array([bp[0:2] for bp in PrintAdditionalDetail_entity.get_points()]))

                vertices = tuple(PrintAdditionalDetail_entity.get_points())

                if vertices in unique_polygons:
                    logging.info(
                        f"Building Layer Found Duplicate Polygon Of {PADetailPolygonID}.")

                else:
                    unique_polygons[vertices] = PrintAdditionalDetail_entity

                PADetailPolygonContainsLabel=[]

                for PrintAdditionalDetail_entity in PrintAdditionalDetail_Data:

                    if PrintAdditionalDetail_entity.dxftype() == 'TEXT' or PrintAdditionalDetail_entity.dxftype() == 'MTEXT':

                        Padetail_text_properties = PrintAdditionalDetail_entity.dxfattribs()

                        PADetail_Name = Padetail_text_properties.get(
                            'text') if PrintAdditionalDetail_entity.dxftype() == 'TEXT' else PrintAdditionalDetail_entity.plain_text()
                        if PADetail_Name != '':
                            padetail_text_pts = Padetail_text_properties.get('insert')

                            padetail_point = Point(np.array([padetail_text_pts[0], padetail_text_pts[1]]))

                            if PADetail_polygon.contains(padetail_point) or PADetail_polygon.touches(
                                    padetail_point) or round(PADetail_polygon.distance(padetail_point),
                                                             1) == 0.0:
                                PADetailPolygonContainsLabel.append([PADetail_Name, PADetail_polygon])
                                break

                if PADetailPolygonContainsLabel != [] and len(PADetailPolygonContainsLabel) <= 1:

                    for padetailnampoly in PADetailPolygonContainsLabel:
                        padetail_dict[PADetailPolygonID] = padetailnampoly

                elif (len(PADetailPolygonContainsLabel) > 1):

                    logging.warning(
                        f'Building Layer Polygon REF # {PADetailPolygonID} Found More Than One Label')

                else:

                    logging.warning(
                        f'Building Layer Polygon REF # {PADetailPolygonID} Does Not Found Any Label')

        return padetail_dict

    def draw_boundingbox_bsp(self, BuildingLayerDict, SitePlan_LayerDict, PrintAdditionalDetail_LayerDict, msp):
        # Step 1: Collect all bounding boxes in one list
        all_bboxes = []

        def add_bbox(poly):
            minx, miny, maxx, maxy = poly.bounds
            bbox = Polygon([
                (minx, miny),
                (maxx, miny),
                (maxx, maxy),
                (minx, maxy),
                (minx, miny)
            ])
            all_bboxes.append(bbox)
            return bbox

        # Buildings
        for building_id, building_values in BuildingLayerDict.items():
            building_polygon = building_values[1]
            add_bbox(building_polygon)

        # SitePlan
        for sitep_id, sitep_values in SitePlan_LayerDict.items():
            siteplan_polygon = sitep_values[1]
            add_bbox(siteplan_polygon)

        # PrintAdditionalDetails
        for pad_id, pad_values in PrintAdditionalDetail_LayerDict.items():
            pad_polygon = pad_values[1]
            add_bbox(pad_polygon)

        # Step 2: Delete entities outside all bounding boxes
        for entity in list(msp):
            # Skip polygons themselves if needed
            if entity.dxftype() in ['LWPOLYLINE', 'POLYLINE', 'LINE', 'TEXT', 'MTEXT', 'ARC', 'POINT', 'INSERT',
                                    'CIRCLE', 'DIMENSION', 'HATCH']:

                x = y = None
                pt = None
                # Get a representative point for the entity
                if entity.dxftype() == 'LINE':
                    x, y = entity.dxf.start[0], entity.dxf.start[1]
                elif entity.dxftype() == 'POINT':
                    x, y = entity.dxf.location[0], entity.dxf.location[1]
                elif entity.dxftype() == "TEXT":
                    x, y = entity.dxf.insert[0], entity.dxf.insert[1]
                elif entity.dxftype() == "MTEXT":
                    x, y = entity.dxf.insert[0], entity.dxf.insert[1]

                elif entity.dxftype() == 'ARC':
                    x, y = entity.dxf.center[0], entity.dxf.center[1]

                elif entity.dxftype() == "INSERT":
                    bname = entity.dxf.name.lower()
                    lname = entity.dxf.layer
                    if (lname=="_PrintAdditionalDetail" and "north" in bname):
                        continue
                    elif(lname=="_MarginLine" and "margin" in bname):
                        continue
                    else:
                        x, y = entity.dxf.insert[0], entity.dxf.insert[1]

                elif entity.dxftype() == "CIRCLE":
                    x, y = entity.dxf.center[0], entity.dxf.center[1]

                elif entity.dxftype() == "LWPOLYLINE":
                    x, y, *_ = entity[0]

                elif entity.dxftype() == "POLYLINE":
                    v = entity[0]  # DXFVertex
                    x, y, z = v.dxf.location

                elif entity.dxftype() == 'DIMENSION':

                    if hasattr(entity.dxf, "defpoint"):
                        x, y = entity.dxf.defpoint[0], entity.dxf.defpoint[1]


                elif entity.dxftype() == 'HATCH':
                    # Handle hatch using its boundary paths
                    try:
                        boundary_points = []
                        for path in entity.paths:
                            for edge in path.edges:
                                if edge.EDGE_TYPE == "LineEdge":
                                    boundary_points.append(edge.start)
                                    boundary_points.append(edge.end)
                                elif edge.EDGE_TYPE == "ArcEdge":
                                    boundary_points.append(edge.center)
                        if boundary_points:
                            hatch_poly = Polygon(boundary_points)
                            if not hatch_poly.is_empty:
                                x, y = hatch_poly.centroid.x, hatch_poly.centroid.y
                            else:
                                x, y = boundary_points[0]
                    except Exception:
                        pass


                else:
                    continue
                if x is not None and y is not None:
                    pt = Point(x, y)

                if pt is None:
                    continue
                
                # FIX: Don't delete Podium even if outside bounding boxes
                if entity.dxftype() != 'DIMENSION' and hasattr(entity, 'dxf') and hasattr(entity.dxf, 'layer'):
                    if entity.dxf.layer == "_Podium":
                        continue  # Skip deletion for Podium
                
                # If the point is not inside any bounding box → delete entity
                if not any(bbox.covers(pt) for bbox in all_bboxes):
                    msp.delete_entity(entity)

    def active_layers(self,doc):
        for layer in doc.layers:
            if layer.is_off():
                layer.on()  # turn it on
            if layer.is_locked():
                layer.unlock()  # unlock it
            if layer.is_frozen():
                layer.thaw()  # unfreeze it
        return True

    def DimOf_FireDoor_Width(self,firedoor_data):
        fdoor_points=[]
        for firedoor_entity in firedoor_data:

            if firedoor_entity.dxftype() == 'LWPOLYLINE' and firedoor_entity.closed:
                poly_pts = [(pt[0], pt[1]) for pt in firedoor_entity.get_points()]

                if len(poly_pts) <= 2:
                    continue

                # polygon banao
                fdoor_polygon = Polygon(poly_pts)

                minx, miny, maxx, maxy = fdoor_polygon.bounds

                # fdoor_points.append(((minx, miny), (maxx, miny)))
                width = maxx - minx
                height = maxy - miny

                if width >= height:
                    fdoor_points.append(((minx, miny), (maxx, miny)))  # horizontal line (longer side)
                else:
                    fdoor_points.append(((minx, miny), (minx, maxy)))  # vertical line (longer side)

        return fdoor_points

    def DimOf_Window_Width(self,window_data):
        window_points=[]
        for window_entity in window_data:

            if window_entity.dxftype() == 'LWPOLYLINE' and window_entity.closed:
                poly_pts = [(pt[0], pt[1]) for pt in window_entity.get_points()]

                if len(poly_pts) <= 2:
                    continue

                # polygon banao
                window_polygon = Polygon(poly_pts)

                minx, miny, maxx, maxy = window_polygon.bounds

                # fdoor_points.append(((minx, miny), (maxx, miny)))
                width = maxx - minx
                height = maxy - miny

                if width >= height:
                    window_points.append(((minx, miny), (maxx, miny)))  # horizontal line (longer side)
                else:
                    window_points.append(((minx, miny), (minx, maxy)))  # vertical line (longer side)

        return window_points

    def StairCaseLayerBlockData(self, StairCase):
        StairCaseList = []
        try:
            for stair_entity in StairCase:
                try:
                    if stair_entity.dxftype() != 'INSERT':
                        continue

                    # --- ✅ Skip mirrored blocks ---
                    xscale = stair_entity.dxf.get("xscale", 1.0)
                    yscale = stair_entity.dxf.get("yscale", 1.0)
                    if xscale < 0 or yscale < 0:
                        # logging.warning(f"Skipping mirrored block [{stair_entity.dxf.handle}] (xscale={xscale}, yscale={yscale})")
                        continue
                    # --------------------------------

                    block_id_stair = stair_entity.dxf.handle

                    arc_points = []
                    lines = []
                    text_names = []
                    intersection_points = []

                    virtual_ents = list(stair_entity.virtual_entities())

                    for entity in virtual_ents:
                        if entity.dxftype() == 'ARC':
                            center = Point(entity.dxf.center.x, entity.dxf.center.y)
                            radius = entity.dxf.radius
                            start_angle = entity.dxf.start_angle
                            end_angle = entity.dxf.end_angle

                            if end_angle < start_angle:
                                end_angle += 360

                            num_segments = 24
                            angle_step = (end_angle - start_angle) / num_segments
                            for i in range(num_segments + 1):
                                angle = start_angle + i * angle_step
                                x = center.x + radius * math.cos(math.radians(angle))
                                y = center.y + radius * math.sin(math.radians(angle))
                                arc_points.append((x, y))

                        elif entity.dxftype() == 'LINE':
                            start = (entity.dxf.start.x, entity.dxf.start.y)
                            end = (entity.dxf.end.x, entity.dxf.end.y)
                            lines.append(LineString([start, end]))

                    # Find intersection points between unique line pairs
                    for i in range(len(lines)):
                        for j in range(i + 1, len(lines)):
                            line1 = lines[i]
                            line2 = lines[j]

                            if line1.equals(line2):
                                continue

                            if line1.intersects(line2) or line1.touches(line2):
                                inter = line1.intersection(line2)
                                if inter.geom_type == 'Point':
                                    intersection_points.append(Point(inter.x, inter.y))

                    # Construct stair polygon from arc points
                    arc_polygon = None
                    if len(arc_points) >= 3:
                        try:
                            arc_polygon = Polygon(arc_points)
                        except Exception:
                            arc_polygon = None

                    # Get max distance from intersection point to arc point
                    max_distance = 0.0
                    max_arc_point = None
                    max_ip_point = None
                    if arc_points and intersection_points:
                        for ip in intersection_points:
                            for ap in arc_points:
                                ap_point = Point(ap)
                                dist = round(ip.distance(ap_point), 2)
                                if dist > max_distance:
                                    max_distance = dist
                                    max_arc_point = ap_point
                                    max_ip_point = ip

                    # logging.info(f"[{block_id_stair}] Max distance: {max_distance}")

                    inter_point = intersection_points[0] if intersection_points else None
                    if arc_polygon and inter_point:
                        stair_arc_line = unary_union(lines)
                        StairCaseList.append([
                            arc_points,
                            max_ip_point,
                            max_arc_point,
                            intersection_points[0],
                            arc_polygon,
                            stair_arc_line
                        ])

                except Exception as e:
                    logging.error(f"Error in StairCaseLayerBlockData (loop): {e}")
        except Exception as e:
            logging.error(f"Error in StairCaseLayerBlockData: {e}")

        return StairCaseList

    def FireDoorBlockLayer(self, FireDoor):
        FireDoorList = []
        try:
            for fired_entity in FireDoor:

                if fired_entity.dxftype() == 'INSERT':

                    block_id_fired = fired_entity.dxf.handle

                    insertion_point = Point(fired_entity.dxf.insert.x, fired_entity.dxf.insert.y)

                    for entity in fired_entity.virtual_entities():
                        # Process geometry entities (ARC and LINE)
                        if entity.dxftype() == 'LWPOLYLINE' and entity.closed:
                            fired_arc_points = []
                            Linestring = []
                            for sub_entity in entity.virtual_entities():
                                if sub_entity.dxftype() == 'ARC':

                                    center = Point(sub_entity.dxf.center.x, sub_entity.dxf.center.y)
                                    radius = sub_entity.dxf.radius
                                    start_angle = sub_entity.dxf.start_angle
                                    end_angle = sub_entity.dxf.end_angle

                                    # Create points along the arc
                                    num_segments = 12  # More segments for smoother arc
                                    angle_step = (end_angle - start_angle) / num_segments

                                    for i in range(num_segments + 1):
                                        angle = start_angle + i * angle_step
                                        x = center.x + radius * math.cos(math.radians(angle))
                                        y = center.y + radius * math.sin(math.radians(angle))
                                        fired_arc_points.append((x, y))
                                        # print(polygon_points_fired)

                                elif sub_entity.dxftype() == 'LINE':
                                    # Add LINE points
                                    start = (sub_entity.dxf.start.x, sub_entity.dxf.start.y)
                                    end = (sub_entity.dxf.end.x, sub_entity.dxf.end.y)
                                    fired_arc_points.extend([start, end])
                                    Linestring.append(LineString([start, end]))
                                    # print("=====",Linestring)

                            f_door_polygon = Polygon(fired_arc_points)
                            if not f_door_polygon.is_valid:
                                continue
                                # f_door_polygon = make_valid(f_door_polygon)

                            block_txt_fired=None

                            for entity in fired_entity.virtual_entities():
                                if entity.dxftype() in ('TEXT', 'MTEXT'):
                                    text = entity.dxf.text if entity.dxftype() == 'TEXT' else entity.plain_text()
                                    final_text= text.lower().replace(" ", "").replace("\n", "")
                                    if "firedooropening" in final_text:
                                        block_txt_fired=text
                                        break
                            fire_arc_line = unary_union(Linestring)
                            if block_txt_fired:
                                FireDoorList.append([f_door_polygon,fired_arc_points,fire_arc_line])

        except Exception:
            logging.error(traceback.print_exc())
        return FireDoorList

    def find_min_length(self,*args):
        min_length = float('inf')

        for line in args[0]:
            length = round(line.length, 2)

            if length < min_length:
                min_length = length

        return round(min_length, 2) if min_length != float('inf') else 0.0

    def StairCaseLayer(self, staircase_query):
        StairCaseDict = {}
        try:
            for entity in staircase_query:
                if entity.dxftype() == "LWPOLYLINE" and entity.closed:

                    staircase_p = [pp[0:2] for pp in entity.get_points()]
                    if len(staircase_p) < 3:
                        continue
                    staircase_polygon = Polygon(staircase_p)
                    # print(staircase_polygon)

                    for text_entity in staircase_query:
                        if text_entity.dxftype() in ["TEXT", "MTEXT"]:
                            staircase_name = text_entity.dxf.text if text_entity.dxftype() == "TEXT" else text_entity.plain_text()
                            staircase_text = staircase_name.lower().replace(" ", "")
                            if "staircase" in staircase_text and "wall" not in staircase_text and "pump" not in staircase_text:

                                staircase_po = [text_entity.dxf.insert[0], text_entity.dxf.insert[1]]
                                staircase_point = Point(staircase_po)

                                if staircase_polygon.contains(staircase_point):
                                    # print(staircase_name)
                                    staircase_id = text_entity.dxf.handle

                                    line_list = []

                                    for line_entity in staircase_query:

                                        if line_entity.dxftype() == "LINE" and line_entity.dxf.color != 161:
                                            line_pts = [(line_entity.dxf.start[0], line_entity.dxf.start[1]),
                                                        (line_entity.dxf.end[0], line_entity.dxf.end[1])]
                                            staircaseLine = LineString(line_pts)

                                            list1 = [round(staircase_polygon.distance(Point(x)), 1) == 0.0 for x in line_pts]

                                            if all(list1):
                                                line_list.append(staircaseLine)


                                        elif line_entity.dxftype() == "LWPOLYLINE" and not line_entity.closed and line_entity.dxf.color != 161:

                                            staircase_polyline = LineString([pp[0:2] for pp in line_entity.get_points()])

                                            list2 = [round(staircase_polygon.distance(Point(x)), 1) == 0.0 for x in
                                                     line_entity.get_points("xy")]

                                            if all(list2):
                                                line_list.append(staircase_polyline
                                                                 )

                                    StairCaseDict[staircase_id] = (staircase_name, staircase_polygon)
        except Exception:
            logging.error(traceback.print_exc())

        return StairCaseDict

    def Check_staircase_overlapping(self,StairCaseLayerBlockDataDict,FireDoorBlockLayerDict,StairCaseLayerDict):
        Over_Lapping = []

        for stair_values in StairCaseLayerBlockDataDict:

            stair_arc_poly = stair_values[4]
            stair_arc_point= stair_values[0]
            stair_arc_line = stair_values[5]
            stair_intersection_points = stair_values[3]

            for stair_id ,stair_values1 in StairCaseLayerDict.items():

                stair_polygon = stair_values1[1]

                if stair_polygon.contains(stair_arc_poly) or stair_polygon.intersects(stair_arc_poly):

                    for fired_values in FireDoorBlockLayerDict:
                        fire_arc_line = fired_values[2]
                        fire_polygon = fired_values[0]
                        fire_arc_point=fired_values[1]

                        if stair_polygon.intersects(fire_polygon):

                            if stair_arc_poly.intersects(fire_polygon):
                                p_stair, p_fire = nearest_points(stair_intersection_points, fire_polygon)
                                Over_Lapping.append([p_stair,p_fire])


        return Over_Lapping

    def firedriveway(self, query):
        lst_arc = []
        for entity in query:
            if entity.dxftype() == "ARC":
                center_pts = (entity.dxf.center[0], entity.dxf.center[1])
                start_pts = entity.start_point
                lst_arc.append((center_pts, start_pts))

            elif entity.dxftype() == "LWPOLYLINE" and str(entity.dxf.linetype).lower() == "center":

                for vir_entity in entity.virtual_entities():
                    if vir_entity.dxftype() == "ARC":
                        center_pts1 = (vir_entity.dxf.center[0], vir_entity.dxf.center[1])
                        start_pts1 = vir_entity.start_point
                        lst_arc.append((center_pts1, start_pts1))

            elif entity.dxftype() == "LWPOLYLINE" and entity.closed:

                for vir_entity in entity.virtual_entities():
                    if vir_entity.dxftype() == "ARC":
                        center_pts1 = (vir_entity.dxf.center[0], vir_entity.dxf.center[1])
                        end_pts1 = vir_entity.end_point
                        lst_arc.append((center_pts1, end_pts1))

        return lst_arc

    def fd_width(self,fd_lw_e,lw_cen_entity):

        fd_width = []
        for fd_cline in lw_cen_entity:

            for vir_cline in fd_cline.virtual_entities():

                if vir_cline.dxftype() == 'LINE':

                    cline_pts = [(vir_cline.dxf.start[0],vir_cline.dxf.start[1]),(vir_cline.dxf.end[0], vir_cline.dxf.end[1])]

                    split_center_line = self.split(cline_pts[0], cline_pts[1], 5)[2]

                    for lwpolygon_line in fd_lw_e.virtual_entities():
                        if lwpolygon_line.dxftype() =="LINE":

                            fd_start_pts = [lwpolygon_line.dxf.start[0], lwpolygon_line.dxf.start[1]]

                            fd_end_pts = [lwpolygon_line.dxf.end[0], lwpolygon_line.dxf.end[1]]

                            fd_line = LineString([fd_start_pts, fd_end_pts])

                            if round(Point(split_center_line).distance(fd_line)) != 0:

                                p1, p2 = nearest_points(Point(split_center_line), fd_line)
                                dist = round(p1.distance(p2), 2)

                                if dist > 0.0:
                                    fd_width.append((dist, (p1.coords[0], p2.coords[0])))
        return fd_width

    def passage_layer(self,passage_data):
        error_passage_dict = {}
        unique_polygons = {}
        error_passage_list = []

        polygon_entities=[entity for entity in passage_data if entity.dxftype() == 'LWPOLYLINE' and entity.closed]
        text_entities=[label_entity for label_entity in passage_data if label_entity.dxftype() in ('TEXT', 'MTEXT')]

        for entity in polygon_entities:
            try:
                props = entity.dxfattribs()
                if props.get('linetype') != 'CENTER':
                    polygon_id = entity.dxf.handle
                    points = [pt[0:2] for pt in entity.get_points()]

                    if len(points) > 3:
                        polygon = Polygon(points)
                        vertices = tuple(entity.get_points())

                        if vertices in unique_polygons:
                            error_passage_dict[polygon_id] = (
                                f"Passage Layer Found Duplicate Polygon Of {polygon_id}."
                            )
                            logging.warning(f"Passage Layer Found Duplicate Polygon Of {polygon_id}.")
                        else:
                            unique_polygons[vertices] = entity

                        polygon_labels = []

                        for label_entity in text_entities:
                            label_props = label_entity.dxfattribs()
                            label_text = (
                                label_props.get('text') if label_entity.dxftype() == 'TEXT'
                                else label_entity.plain_text()
                            )
                            label_point = Point(label_props.get('insert'))

                            if polygon.contains(label_point) or round(
                                    polygon.distance(label_point), 1) == 0.0:

                                centerlines = [
                                    e for e in passage_data
                                    if e.dxftype() == 'LWPOLYLINE'
                                       and e.dxf.linetype == 'CENTER'
                                       and all(round(polygon.distance(Point(p)), 1) == 0.0
                                               for p in e.get_points('xy'))
                                ]

                                if len(centerlines) == 1:
                                    polygon_labels.append(
                                        [polygon_id, label_text, polygon, centerlines[0]]
                                    )
                                elif len(centerlines) == 0:
                                    logging.warning(f'Passage Polygon REF#({polygon_id}) Does Not Contain Any CenterLine')
                                    error_passage_list.append(
                                        f'Warning - Passage Polygon REF#({polygon_id}) Does Not Contain Any CenterLine'
                                    )
                                elif len(centerlines) > 1:
                                    logging.warning(f'Passage Polygon #REF({polygon_id}) Contains Multiple CenterLines')
                                    error_passage_list.append(
                                        f'Warning - Passage Polygon #REF({polygon_id}) Contains Multiple CenterLines'
                                    )
                                break  # Only one label per polygon

                        if len(polygon_labels) == 1:
                            error_passage_dict[polygon_labels[0][0]] = polygon_labels[0][1:]
                        elif len(polygon_labels) == 0:
                            logging.warning(f'Warning - Passage Polygon REF#({polygon_id}) Has No Label')
                        elif len(polygon_labels) > 1:
                            logging.warning(f'Warning - Passage Polygon REF#({polygon_id}) Has Multiple Labels')
            except Exception:
                logging.error(traceback.print_exc())
                continue

        return error_passage_dict

    def PolygonContainPoint(self,poly, point):
        try:
            return poly.contains(point) or round( poly.distance(point), 1) == 0.0
        except Exception:
            logging.error(traceback.print_exc())

    def FireTowerLayer(self, FireTowerData):

        FireTowerDict = dict()
        try:
            polygon_entities=[FireTower_poly for FireTower_poly in FireTowerData if FireTower_poly.dxftype() == 'LWPOLYLINE' and FireTower_poly.closed ]
            text_entities=[FireTower_text for FireTower_text in FireTowerData if FireTower_text.dxftype() in ("TEXT","MTEXT")]

            for FireTower_poly in polygon_entities:

                try:
                    FireTowerPoly_ID = FireTower_poly.dxf.handle

                    poly_pts=[fp[0:2] for fp in FireTower_poly.get_points()]

                    if len(poly_pts)<3:
                        continue

                    FireTower_polygon_points = Polygon(poly_pts)

                    FireTowerContainsLabel = []

                    for FireTower_text in text_entities:

                        FireTower_Label = FireTower_text.dxf.text if FireTower_text.dxftype() == 'TEXT' else FireTower_text.plain_text()

                        if FireTower_Label=="":
                            continue

                        FireTower_Label_ID = FireTower_text.dxf.handle

                        FireTowerLabel_point = Point([FireTower_text.dxf.insert[0], FireTower_text.dxf.insert[1]])

                        if self.PolygonContainPoint(poly=FireTower_polygon_points,point=FireTowerLabel_point):

                            FireTowerContainsLabel.append([FireTower_Label_ID, FireTower_Label,FireTower_polygon_points])

                    if FireTowerContainsLabel:

                        for FireTower_data in FireTowerContainsLabel:

                            FireTowerDict[FireTower_data[0]] = FireTower_data[1:]
                    else:

                        logging.warning(f'Polygon #REF ({FireTowerPoly_ID}) Missing Label')

                except Exception:
                    logging.error(traceback.print_exc())
                    continue

        except Exception:
            logging.error(traceback.print_exc())
        return FireTowerDict

    def FireDoorLayer(self, FireDoorData):

        FireDoorDict = dict()
        try:

            polygon_entities=[FireDoor_poly for FireDoor_poly in FireDoorData if FireDoor_poly.dxftype() == 'LWPOLYLINE'
                              and FireDoor_poly.closed]
            text_entities = [FireDoor_text for FireDoor_text in FireDoorData if FireDoor_text.dxftype() in ('TEXT', 'MTEXT')]

            for FireDoor_poly in polygon_entities:
                try:
                    FireDoorPoly_ID = FireDoor_poly.dxf.handle
                    FireDoor_polygon_pts=[fdp[0:2] for fdp in FireDoor_poly.get_points()]

                    if len(FireDoor_polygon_pts)<3:
                        continue

                    FireDoor_polygon_points = Polygon(FireDoor_polygon_pts)

                    fire_door_width = max([round(LineString([[line.dxf.start[0], line.dxf.start[1]], [line.dxf.end[0], line.dxf.end[1]]]).length,2) for line in FireDoor_poly.virtual_entities() if line.dxftype() == 'LINE'])

                    FireDoorContainsLabel = []

                    for FireDoor_text in text_entities:

                        FireDoor_Label = FireDoor_text.dxf.text if FireDoor_text.dxftype() == 'TEXT' else FireDoor_text.plain_text()

                        if FireDoor_Label=="":
                            continue

                        FireDoor_Label_ID = FireDoor_text.dxf.handle

                        FireDoorLabel_point = Point([FireDoor_text.dxf.insert[0], FireDoor_text.dxf.insert[1]])

                        if self.PolygonContainPoint(poly=FireDoor_polygon_points,point=FireDoorLabel_point):

                            FireDoorContainsLabel.append([FireDoor_Label_ID, FireDoor_Label, FireDoor_polygon_points,FireDoorLabel_point, fire_door_width])

                    if FireDoorContainsLabel:

                        for FireDoor_data in FireDoorContainsLabel:

                            FireDoorDict[FireDoor_data[0]] = FireDoor_data[1:]
                    else:
                        logging.warning(f'Polygon #REF ({FireDoorPoly_ID}) Missing Label')

                except Exception:
                    logging.error(traceback.print_exc())
                    continue

        except Exception:
            logging.error(traceback.print_exc())
        return FireDoorDict

    def Modfy_TextMtext_Floor_Layer(self, Floor_Data, scale_factor=2, fixed_height=1.0,fixed_width_factor=None):

        for Floor_entity in Floor_Data:

            # --- TEXT ---
            if Floor_entity.dxftype() == 'TEXT':
                # Height
                if fixed_height:
                    Floor_entity.dxf.height = fixed_height
                else:
                    Floor_entity.dxf.height *= scale_factor

                # Width (width_factor)
                if fixed_width_factor:
                    Floor_entity.dxf.width = fixed_width_factor
                else:
                    Floor_entity.dxf.width *= scale_factor

            # --- MTEXT ---
            elif Floor_entity.dxftype() == 'MTEXT':
                # Height
                if fixed_height:
                    Floor_entity.dxf.char_height = fixed_height
                else:
                    Floor_entity.dxf.char_height *= scale_factor

                # Width (column width)
                if fixed_width_factor:
                    Floor_entity.dxf.width = fixed_width_factor

                elif Floor_entity.dxf.width > 0:  # only if already set
                    Floor_entity.dxf.width *= scale_factor

    def clean_dxf(self,doc):
        msp = doc.modelspace()
        # Remove zero-length lines
        for e in list(msp.query("LINE")):
            if e.dxf.start == e.dxf.end:
                msp.delete_entity(e)

        # Flatten all geometry (remove Z)
        for e in msp:
            if hasattr(e.dxf, "insert"):
                x, y, *_ = e.dxf.insert
                e.dxf.insert = (x, y, 0)

            if e.dxftype() == "LWPOLYLINE":
                pts = [(x, y, 0, *rest[3:]) if len(rest) > 2 else (x, y, 0)
                       for x, y, *rest in e.get_points()]
                e.set_points(pts)

            if e.dxftype() == "LINE":
                sx, sy, *_ = e.dxf.start
                ex, ey, *_ = e.dxf.end
                e.dxf.start = (sx, sy, 0)
                e.dxf.end = (ex, ey, 0)

        # Purge unused elements (1.0.3 supports this)
        doc.purge()
        # doc.linetypes.purge()
        # doc.styles.purge()
        # doc.dimstyles.purge()
        # doc.appids.purge()
        # doc.block_records.purge()

    def generateDxf(self,folder:str,filename:str,commonSetbacks:{}):

        self.folder = folder

        self.filename = filename

        read_dxf =None

        try:
            dxf_path = os.path.join(self.folder, self.filename)

            read_dxf = ezdxf.readfile(dxf_path)

            units = read_dxf.header.get("$INSUNITS", 0)

            # Convert to meters ONLY
            if units != 6:

                read_dxf.header["$INSUNITS"] = 6
                units = 6

            # ----------- NEW LOGIC END -----------------
            if units == 6:

                logging.info("Loading DXF File ...")
                msp = read_dxf.modelspace()
                # --- Ensure consistent DIMSCALE and MEASUREMENT ---
                read_dxf.header["$DIMSCALE"] = 1
                read_dxf.header["$MEASUREMENT"] = 1  # 1 = metric

                # --- Ensure "Standard" text style height = 0 ---
                if "Standard" in read_dxf.styles:
                    std_style = read_dxf.styles.get("Standard")
                    std_style.dxf.height = 0

                if "OpenSans" not in read_dxf.styles:
                    read_dxf.styles.add("OpenSans", font="OpenSans.ttf")

                def setup_dimstyle(name, txt, asz):
                    if name not in read_dxf.dimstyles:
                        read_dxf.dimstyles.new(name)
                    ds = read_dxf.dimstyles.get(name)

                    ds.set_dxf_attrib("dimtxt", txt)  # text height
                    ds.set_dxf_attrib("dimasz", asz)  # arrow size
                    ds.set_dxf_attrib("dimscale", 1)
                    ds.set_dxf_attrib("dimgap", 0)
                    ds.set_dxf_attrib("dimexe", 0.02)
                    ds.set_dxf_attrib("dimexo", 0.02)

                    # IMPORTANT FIX FOR ROTATION
                    ds.set_dxf_attrib("dimtad", 0)  # center text
                    ds.set_dxf_attrib("dimtih", 0)  # do NOT force horizontal inside
                    ds.set_dxf_attrib("dimtoh", 0)  # do NOT force horizontal outside
                    ds.set_dxf_attrib("dimtix", 1)  # align text to dimension, rotate clockwise

                    ds.set_dxf_attrib("dimtxsty", "Standard")

                    return ds

                # double extra large = 0.3m text, 0.1m arrows for bounding box
                setup_dimstyle("EZDXF_XXXL", 0.3, 0.1)

                # double extra large = 0.3m text, 0.1m arrows for bounding box
                setup_dimstyle("EZDXF_XXL", 0.1, 0.08)

                # extra large = 0.08m text, 0.05m arrows
                setup_dimstyle("EZDXF_XL", 0.08, 0.05)

                # large = 0.05m text, 0.03m arrows
                setup_dimstyle("EZDXF_L", 0.05, 0.03)

                # medium = 0.03m text, 0.02m arrows
                setup_dimstyle("EZDXF_M", 0.03, 0.02)

                # small = 0.02m text, 0.15m arrows
                setup_dimstyle("EZDXF_S", 0.02, 0.015)

                def render_template(style):

                    temp = msp.add_aligned_dim(
                        p1=(0, 0),
                        p2=(1, 0),
                        distance=0.05,
                        dimstyle=style,
                    )

                    temp.render()  # only ONCE per dimstyle

                render_template("EZDXF_S")
                render_template("EZDXF_M")
                render_template("EZDXF_L")
                render_template("EZDXF_XL")
                render_template("EZDXF_XXL")

                group = msp.groupby(dxfattrib='layer')
                building_query = msp.query('TEXT MTEXT LWPOLYLINE [layer=="_BuildingName"]')
                floor_query = msp.query('TEXT MTEXT LWPOLYLINE [layer=="_Floor"]')
                proposed_work_query = msp.query('TEXT MTEXT LWPOLYLINE [layer=="_ProposedWork"]')
                resibua_query = msp.query('LWPOLYLINE TEXT MTEXT[layer=="_ResiBUAOutline"]')
                commbua_query = msp.query('LWPOLYLINE TEXT MTEXT[layer=="_CommBUAOutline"]')
                indbua_query = msp.query('LWPOLYLINE TEXT MTEXT[layer=="_IndBUAOutline"]')
                specialbua_query = msp.query('LWPOLYLINE TEXT MTEXT[layer=="_SpecialUseBUAOutline"]')
                marginline_query = msp.query('INSERT LINE ARC[layer=="_MarginLine"]')
                resibuaDIRREFCircle_query = msp.query('INSERT[layer=="_ResiBUAOutline"]')
                parking_query = msp.query('LWPOLYLINE TEXT MTEXT [layer=="_Parking"]')
                orgopenspace_query = msp.query('LWPOLYLINE TEXT MTEXT[layer=="_OrganizedOpenSpace"]')
                plot_query = msp.query('LWPOLYLINE TEXT MTEXT[layer=="_Plot"]')
                section_query = msp.query('LWPOLYLINE TEXT MTEXT [layer=="_Section"]')
                floorinsection_query = msp.query('LWPOLYLINE TEXT MTEXT [layer=="_FloorInSection"]')
                groundlevel_query = msp.query('LWPOLYLINE TEXT MTEXT LINE[layer=="_GroundLevel"]')
                existingstructure_query = msp.query('LWPOLYLINE TEXT MTEXT[layer=="_ExistingStructure"]')

                lift_query = msp.query('LWPOLYLINE TEXT MTEXT[layer=="_Lift"]')
                staircase_query = msp.query('LWPOLYLINE TEXT MTEXT [layer=="_StairCase"]')
                padatail_query = msp.query('LWPOLYLINE TEXT MTEXT [layer=="_PrintAdditionalDetail"]')
                siteplan_query = msp.query('LWPOLYLINE TEXT MTEXT[layer=="_SitePlan"]')
                firedoor_query = msp.query('LWPOLYLINE TEXT MTEXT[layer=="_Fire Door"]')
                window_query = msp.query('LWPOLYLINE TEXT MTEXT[layer=="_Window"]')
                StairCaseBlock_query = msp.query('INSERT[layer=="_StairCase"]')
                firedriveway_query = msp.query('*[layer=="_Fire Driveway"]')
                FireDoorBlock_query = msp.query('INSERT[layer=="_Fire Door"]')
                stairOverlapping_query = msp.query('*[layer=="_StairCase"]')
                PassageEntities = msp.query('TEXT MTEXT LWPOLYLINE[layer=="_Passage"]')
                FireTower_query = msp.query('*[layer=="_FireTower"]')

                BuildingLayerDict = self.BuildingName_Layer(building_query)
                FloorLayerDict = self.Floor_Layer(floor_query)
                ProposedWorkLayerDict = self.ProposedWork_Layer(proposed_work_query)
                MarginLayerDict = self.MarginLineLayer(marginline_query)
                ParkingLayerDict = self.Parking_Layer(parking_query)
                OrganizedOpenSpaceDataLayerDict = self.OrganizedOpenSpace_Layer(orgopenspace_query)
                PlotDict = self.Plot_Layer(plot_query)
                SectionLayerDict = self.Section_Layer(section_query)
                FloorInSectionDict = self.FloorInSection_Layer(floorinsection_query)
                GroundLevelDict = self.GroundLevel_Layer(groundlevel_query)
                FireDrivewayDict = self.FireDrivewayLayerDict(firedriveway_query)

                ExistingStructure_dict = self.ExistingStructure(existingstructure_query)

                ResiBUA_LayerDict = self.ResiBuaOutLine_Layer(resibua_query)
                commBUA_LayerDict = self.CommBuaOutLine_Layer(commbua_query)
                IndBuaOutLine_LayerDict = self.IndBuaOutLine_Layer(indbua_query)
                SpecialBuaOutLine_LayerDict = self.SpecialBuaOutLine_Layer(specialbua_query)

                self.Modfy_TextMtext_Floor_Layer(floor_query)
                self.Modfy_TextMtext_FloorInSection_Layer(floorinsection_query)
                self.Modify_TextMtext_GLSection_Layer(groundlevel_query)
                self.Modify_TextMtext_LiftInSection_Layer(lift_query,SectionLayerDict[1])
                self.Modify_TextMtext_StaircaseSection_Layer(staircase_query,SectionLayerDict[1])
                DimeOf_FloorBuildingHeight_Dict = self.DimeOf_FloorBuildingHeight(FloorInSectionDict[1],GroundLevelDict[1],SectionLayerDict[1])

                SitePlan_LayerDict = self.Siteplan_Layer(siteplan_query)
                PrintAdditionalDetail_LayerDict = self.PrintAdditionalDetail_Layer(padatail_query)
                DimOf_FireDoor_WidthDict = self.DimOf_FireDoor_Width(firedoor_query)
                DimOf_Window_WidthDict = self.DimOf_Window_Width(window_query)

                FireDoorBlockLayerDict = self.FireDoorBlockLayer(FireDoorBlock_query)
                StairCaseLayerBlockDataDict = self.StairCaseLayerBlockData(StairCaseBlock_query)

                StairCaseLayerDict = self.StairCaseLayer(stairOverlapping_query)
                Check_staircase_overlappingDict = self.Check_staircase_overlapping(StairCaseLayerBlockDataDict,FireDoorBlockLayerDict,StairCaseLayerDict)

                passage_layerDict = self.passage_layer(PassageEntities)
                FireTowerLayerDict = self.FireTowerLayer(FireTower_query)
                FireDoorLayerDict = self.FireDoorLayer(firedoor_query)

                resibua_polygon_data = [resibua[1:] for resibua in ResiBUA_LayerDict.values()] if len(ResiBUA_LayerDict) > 0 else []
                commbua_polygon_data = [commbua[1:] for commbua in commBUA_LayerDict.values()] if len(commBUA_LayerDict) > 0 else []
                indbua_polygon_data = [indbua[1:] for indbua in IndBuaOutLine_LayerDict.values()] if len(IndBuaOutLine_LayerDict) > 0 else []
                specialbua_polygon_data = [splbua[1:] for splbua in SpecialBuaOutLine_LayerDict.values()] if len(SpecialBuaOutLine_LayerDict) > 0 else []

                #for buildings
                for building_id,building_values in BuildingLayerDict.items():

                    logging.info(f"Processing {building_values[0]} Data ...")

                    for floor_id, floor_values in FloorLayerDict.items():

                        logging.info(f"Processing {floor_values[0]} Data ...")

                        floor_label = floor_values[0]

                        floor_polygon = floor_values[1]

                        if building_values[1].contains(floor_polygon):

                            if any(word in floor_label.lower() for word in ['basement', 'stilt', 'cellar']):

                                floor_polygon_area = round(floor_polygon.area)

                                logging.info(f'{floor_label} Area:{floor_polygon_area}')

                                self.ScallingForDownFloor(msp,group,floor_polygon)

                            else:

                                self.ScallingForUpperFloor(msp,group,floor_polygon)

                        logging.info(f"Processed {floor_values[0]} Data.")

                    logging.info(f"Processed {building_values[0]} Data.")

                # ---------This code for Site plan--------------------

                if SitePlan_LayerDict:

                    for sp_id,sp_values in SitePlan_LayerDict.items():

                        logging.info(f"Processing {sp_values[0]} Data...")

                        self.ScallingForSitePlan(msp,group,sp_values[1])

                        logging.info(f"Processed {sp_values[0]} Data.")

                        logging.info("Processing FireDriveWay WIDTH ARC Dimentions.")
                        fireturning_rad_dim = self.firedriveway(firedriveway_query)

                        if fireturning_rad_dim:
                            for dim_pts in fireturning_rad_dim:
                                start_pts = dim_pts[0]
                                end_pts = dim_pts[1]

                                if sp_values[1].contains(Point(start_pts)) and sp_values[1].contains(
                                        Point(end_pts)):
                                    turn_rad = round(Point(start_pts).distance(Point(end_pts)), 1)
                                    if turn_rad > 0.0:
                                        self.add_aligned_dim_entity(msp, start_pts, end_pts, 0, f"Radius:{turn_rad}", 0,
                                                                    0, 0.3,
                                                                    0.1,"EZDXF_XXL")

                        for fd_id, fd_data in FireDrivewayDict.items():

                            cen_lines = fd_data[3]

                            fdrive_width = self.fd_width(fd_data[2], cen_lines)

                            if fdrive_width:

                                dist, dim_pts = min(fdrive_width, key=lambda x: x[0])
                                # print("Fire driveway width:", dist)
                                if dist > 0.0:
                                    # Original points
                                    p1 = dim_pts[0]  # point to extend
                                    p2 = dim_pts[1]  # fixed point

                                    # Vector from p2 → p1
                                    dx = p1[0] - p2[0]
                                    dy = p1[1] - p2[1]
                                    length = (dx ** 2 + dy ** 2) ** 0.5

                                    if length != 0:
                                        # Scale factor (we want double the distance)
                                        scale = (dist * 2) / length
                                        # Extend p1 outward along the same line
                                        new_p1 = (p2[0] + dx * scale, p2[1] + dy * scale)
                                        new_p2 = p2
                                        double_dist = dist * 2
                                    else:
                                        new_p1 = new_p2 = p1
                                        double_dist = 0

                                    # print("New extended points:", new_p1, new_p2)
                                    if sp_values[1].contains(Point(new_p1)) and sp_values[1].contains(
                                            Point(new_p2)):
                                        if double_dist > 0.0:
                                            # Example usage in your dimension entity
                                            self.add_aligned_dim_entity(
                                                msp,
                                                new_p1,
                                                new_p2,
                                                0,
                                                double_dist,
                                                0,
                                                2,
                                                0.1,
                                                0.05,
                                                style="EZDXF_XL"
                                            )

                        logging.info("Processed FireDriveWay WIDTH ARC Dimentions.")

                        logging.info(f"Processed {sp_values[0]} Data .")

                # ---------This is the Common Floor Setbacks code------
                logging.info("Processing Common Floor Setbacks...")

                commonfloorsetbacks_obj1=CommonFloorSetbacks(BuildingLayerDict, FloorLayerDict, ProposedWorkLayerDict,
                                                    commbua_polygon_data, resibua_polygon_data, indbua_polygon_data,
                                                    specialbua_polygon_data, MarginLayerDict, resibuaDIRREFCircle_query,
                                                    ParkingLayerDict, OrganizedOpenSpaceDataLayerDict,ExistingStructure_dict[1],
                                                    PlotDict,FloorInSectionDict[1],SectionLayerDict[1],GroundLevelDict[1])

                setback_value=commonfloorsetbacks_obj1.getFloorSebacks(commonSetbacks)

                logging.info(f"Common Floor Setbacks: {setback_value}")

                for side_data in setback_value:

                    for side_key,side_val in side_data.items():

                        side_dist=round(side_val[0],2)

                        start_point=side_val[1][0]

                        end_point=side_val[1][1]

                        if side_dist > 0.0:

                            self.add_aligned_dim_entity(msp,start_point,end_point,0.1,side_dist,0,0,0.5,0.1,"EZDXF_XXL")

                logging.info("Processed Common Floor Setbacks-MMR.")

                logging.info("Processing Floor and Building Height Dimentions.")

                for dim_line_pts in DimeOf_FloorBuildingHeight_Dict:
                    # dim_line_pts might be wrapped in extra tuple/list
                    if len(dim_line_pts) == 1 and isinstance(dim_line_pts[0], (list, tuple)):
                        dim_line_pts = dim_line_pts[0]

                    p1, p2 = dim_line_pts
                    floor_dis = round(Point(p1).distance(Point(p2)), 2)
                    # print("==+",floor_dis)
                    if floor_dis > 0.0:
                        self.add_aligned_dim_entity(msp, p1, p2, abs(0.8), floor_dis, 0, 0, 0.3, 0.1,"EZDXF_XXXL")

                logging.info("Processed Floor and Building Height Dimentions.")

                logging.info("Processing Fire Door Width Dimentions.")

                for fd_line_pts in DimOf_FireDoor_WidthDict:
                    p1 = fd_line_pts[0]
                    p2 = fd_line_pts[1]

                    fd_dist = round(Point(p1).distance(Point(p2)), 1)

                    if fd_dist > 0.0:

                        self.add_aligned_dim_entity(msp, p1, p2, 0, fd_dist, 0, 0, 0.05, 0.05,"EZDXF_L")

                logging.info("Processed Fire Door Width Dimentions.")

                logging.info("Processing Staircase Overlapping Fire Door Dimentions.")

                for overlape_line_pts in Check_staircase_overlappingDict:
                    p1 = overlape_line_pts[0].coords[0]
                    p2 = overlape_line_pts[1].coords[0]

                    overlape_dis = round(Point(p1).distance(Point(p2)), 2)

                    if overlape_dis > 0.0:

                        self.add_aligned_dim_entity(msp, p1, p2, 0, overlape_dis, 0, 0, 0.1, 0.05,"EZDXF_XL")

                for arc_line_dis in StairCaseLayerBlockDataDict:
                    p1 = arc_line_dis[1].coords[0]
                    p2 = arc_line_dis[2].coords[0]

                    arc_dis = round(Point(p1).distance(Point(p2)), 1)

                    if arc_dis > 0.0:

                        self.add_aligned_dim_entity(msp, p1, p2, 0, arc_dis, 0, 0, 0.1, 0.05,"EZDXF_XL")

                logging.info("Processed Staircase Overlapping Fire Door Dimentions.")

                logging.info("Processing DEAD END CORRIDOR Dimentions.")

                for build_id, build_value in BuildingLayerDict.items():
                    build_poly = build_value[1]
                    for floor_id, FloorData in FloorLayerDict.items():
                        floor_poly = FloorData[1]
                        if build_poly.contains(floor_poly):
                            td_dc_data = Dim_TD_and_DC(build_id, build_value[1], floor_id, FloorData[0], FloorData[1],
                                                       StairCaseLayerDict,
                                                       passage_layerDict, FireTowerLayerDict, FireDoorLayerDict)

                            get_dc_data = td_dc_data.get_dc()
                            # print(FloorData[0], get_dc_data)
                            if get_dc_data:
                                for dim_line_pts in get_dc_data:
                                    if dim_line_pts:
                                        p1 = dim_line_pts[0].coords[0]

                                        p2 = dim_line_pts[1].coords[0]

                                        td_dc_dis = round(Point(p1).distance(Point(p2)), 2)

                                        if td_dc_dis > 0.0:

                                            self.add_aligned_dim_entity(msp, p1, p2, 0, td_dc_dis, "_Travel Distance", 2, 0.1,
                                                                    0.05,"EZDXF_XL")

                logging.info("Processed DEAD END CORRIDOR Dimentions.")

                logging.info("Processing Windows Width Dimentions.")

                for wd_line_pts in DimOf_Window_WidthDict:
                    p1 = wd_line_pts[0]
                    p2 = wd_line_pts[1]

                    wd_dist = round(Point(p1).distance(Point(p2)), 1)

                    if wd_dist > 0.0:

                        self.add_aligned_dim_entity(msp, p1, p2, 0, wd_dist, 0, 0, 0.05, 0.05,"EZDXF_XL")

                logging.info("Processed Windows Width Dimentions.")

                logging.info("Processing Deleting Entities.")
                # self.clean_dxf(read_dxf)
                self.draw_boundingbox_bsp(BuildingLayerDict, SitePlan_LayerDict, PrintAdditionalDetail_LayerDict, msp)
                logging.info("Processed Deleting Entities.")

            else:

                text = "-Dimensions are not compatible in the drawing as the UNITS of the drawing are not in meters/mts. "
                msp1 = read_dxf.modelspace()
                PropWork_query = msp1.query("TEXT MTEXT [layer == '_ProposedWork']")

                if PropWork_query:
                    text_points = [(PropWork_query[0].dxf.insert[0],PropWork_query[0].dxf.insert[1])]
                    text_label = PropWork_query[0].dxf.text if PropWork_query[0].dxftype()=="TEXT" else PropWork_query[0].plain_text()
                    # self.add_area_mtext_entity(msp1,text_label+text,"_ProposedWork",text_points[0],30,500,1)
                    self.add_area_text(msp1,text_label+text,"_ProposedWork",text_points[0],30,500,1)
                else:
                    logging.warning(f"❌ Missing Proposed Work Text or Mtext Entities")

                logging.warning(f"❌ Skipping file '{dxf_path}' — not in meters,inches or milimeters (INSUNITS={units})")

        except ezdxf.lldxf.const.DXFTableEntryError as e:
            logging.error(f"DXF Table Entry Error: {e}")

        except IOError:
            msg = f'Not a DXF file or a generic I/O error.' + ' filename ' + str(filename)
            logging.error(f'IO Error:{msg}')

        except ezdxf.DXFStructureError:

            msg = f'Invalid or corrupted DXF file.' + ' filename ' + str(filename)
            logging.error(f'DXF Structure Error{msg}')

        finally:

            if read_dxf:
                try:
                    self.active_layers(read_dxf)
                    read_dxf.save()
                    logging.info(f"✅ DXF file saved successfully: {filename}")
                except Exception as e:
                    logging.error(f"❌ Error saving DXF file '{filename}': {e}")
            else:
                logging.error(f"❌ Failed to save DXF file — no valid DXF document object found for '{filename}'.")

# #path of the filename
# folder=r"C:\Users\swaroop\Downloads"
# # folder = r"D:\Code_&_Files_Mahendra_Kumar\ProductionCode & File\DXF_Files\Fire_Building_file\DXF"
# # folder = r"E:\production_code\dxf_files\generate_dxf_files"
# #Here give only filename
#
# filename="BLOCK-B (1).dxf"
#
# #method returns a dict with handlesx
#
# from datetime import datetime
#
# start_time=datetime.now()
#
# t1 = start_time.strftime("%H:%M:%S")
#
# first_start_time=datetime.strptime(t1,"%H:%M:%S")
#
# response=MODYFY_DXF()
#
# response.generateDxf(folder,filename,commonSetbacks={})
#
# end_time=datetime.now()
#
# t2=end_time.strftime("%H:%M:%S")
#
# last_end_time=datetime.strptime(t2,"%H:%M:%S")
#
# total_time=last_end_time-first_start_time
#
# logging.info(f'Total Time is:{total_time}')