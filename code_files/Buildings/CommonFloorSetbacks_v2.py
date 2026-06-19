# ---------------------------------------------------Modules---------------------------------------------------------------
import os
import ezdxf
from shapely.geometry import Point, Polygon
from shapely.geometry import LineString
import numpy as np
from shapely.ops import unary_union,linemerge
class CommomFloorSetbacks:
    def MergeMultipolygonObject(self, MultiPolygonobject):

        exterior_rings = [polygon.exterior for polygon in MultiPolygonobject.geoms]
        # print(exterior_rings)
        singlepolygon = Polygon(shell=[point for ring in exterior_rings for point in ring.coords])
        # print(singlepolygon)
        return singlepolygon
    def DistPropjoinedtotlot2marginanotherProp(self, totlot_poly, Marginline, ListProposedPoly):

        margin_xpts, margin_ypts = Marginline.coords.xy

        np_margin_line_pts = np.array([[margin_xpts[0], margin_ypts[0]], [margin_xpts[1], margin_ypts[1]]])

        max_margin_line_pts = np_margin_line_pts.max(axis=0)

        min_margin_line_pts = np_margin_line_pts.min(axis=0)

        dist_min_margin_line_pts = max_margin_line_pts - min_margin_line_pts

        totlot_polyboundary = totlot_poly.boundary.coords

        # prop_line_points = [LineString([[propsed_polyboundary[0][i],propsed_polyboundary[1][i]],[propsed_polyboundary[0][i+1],propsed_polyboundary[1][i+1]]]) for i in range(len(propsed_polyboundary[0])-1)]
        tot_lineb = [LineString(totlot_polyboundary[k:k + 2]) for k in range(len(totlot_polyboundary) - 1)]

        totlot_line_points = [LineString(list(ls.coords)) for ls in tot_lineb]

        totlot_line2margindist = [totlot_line.distance(Marginline) for totlot_line in totlot_line_points]

        if totlot_line2margindist != []:

            totlottoprop1dist = []

            if dist_min_margin_line_pts[0] > dist_min_margin_line_pts[1]:

                for totlot_linex in totlot_line_points:

                    if round(totlot_linex.distance(Marginline), 1) == round(min(totlot_line2margindist), 1):

                        totlot_ptsX, totlot_ptsY = totlot_linex.coords.xy

                        np_totlot_linepts = np.array(
                            [(totlot_ptsX[0], totlot_ptsY[0]), (totlot_ptsX[1], totlot_ptsY[1])])

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

                                        if (max_np_totlot_linepts[0] > splitpts[0] and min_np_totlot_linepts[0] < splitpts[0]) and (max_np_totlot_linepts[1] > splitpts[1] and min_np_totlot_linepts[1] <splitpts[1]):

                                            splittotpts.append(True)

                                        else:

                                            splittotpts.append(False)

                                    list_ofpropline.append(any(splittotpts))

                                if any(list_ofpropline) == True:

                                    if round(totlot_linex.distance(proposed1[1]), 1) != 0.0:
                                        totlottoprop1dist.append(totlot_linex.distance(proposed1[1]))

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

                                proposed1_lineb = [LineString(proposed1_polyboundary[k:k + 2]) for k in range(len(proposed1_polyboundary) - 1)]

                                prop_line_points = [list(ls.coords) for ls in proposed1_lineb]

                                for prop1line in prop_line_points:

                                    splitline2points = self.splitLinetopoints(prop1line[0], prop1line[1], 100)

                                    splittotpts = []

                                    for splitpts in splitline2points[10:-10]:

                                        if (max_np_totlot_linepts[1] > splitpts[1] and min_np_totlot_linepts[1] <
                                            splitpts[1]) and (max_np_totlot_linepts[0] > splitpts[0] and min_np_totlot_linepts[0] < splitpts[0]):

                                            splittotpts.append(True)
                                        else:
                                            splittotpts.append(False)

                                    list_ofpropline.append(splittotpts)

                                if any(list_ofpropline) == True:

                                    if round(totlot_linex.distance(proposed1[1]), 1) != 0.0:
                                        totlottoprop1dist.append(totlot_linex.distance(proposed1[1]))

            if totlottoprop1dist != [] or len(totlottoprop1dist) > 0:
                return totlottoprop1dist
    def DistPropjoinedtotlot2marginanotherTotLot(self, totlot_poly, Marginline, ListTotLotPoly):

        margin_xpts, margin_ypts = Marginline.coords.xy

        np_margin_line_pts = np.array([[margin_xpts[0], margin_ypts[0]], [margin_xpts[1], margin_ypts[1]]])

        max_margin_line_pts = np_margin_line_pts.max(axis=0)

        min_margin_line_pts = np_margin_line_pts.min(axis=0)

        dist_min_margin_line_pts = max_margin_line_pts - min_margin_line_pts

        totlot_polyboundary = totlot_poly.boundary.coords

        totlot_lineb = [LineString(totlot_polyboundary[k:k + 2]) for k in range(len(totlot_polyboundary) - 1)]

        totlot_line_points = [LineString(list(ls.coords)) for ls in totlot_lineb]

        totlot_line2margindist = [totlot_line.distance(Marginline) for totlot_line in totlot_line_points]

        if totlot_line2margindist != []:

            totlottototlotdist = []

            if dist_min_margin_line_pts[0] > dist_min_margin_line_pts[1]:

                for totlot_linex in totlot_line_points:

                    if round(totlot_linex.distance(Marginline), 1) == round(min(totlot_line2margindist), 1):

                        totlot_ptsX, totlot_ptsY = totlot_linex.coords.xy

                        np_totlot_linepts = np.array([(totlot_ptsX[0], totlot_ptsY[0]), (totlot_ptsX[1], totlot_ptsY[1])])

                        max_np_totlot_linepts = np_totlot_linepts.max(axis=0)

                        min_np_totlot_linepts = np_totlot_linepts.min(axis=0)

                        dist_np_totlot_linepts = max_np_totlot_linepts - min_np_totlot_linepts

                        if dist_np_totlot_linepts[0] > dist_np_totlot_linepts[1]:

                            # print(np_prop_linepts)

                            for totlot in ListTotLotPoly:

                                list_oftotlotline = []

                                totlot_polyboundary = totlot.boundary.coords

                                totlot_lineb = [LineString(totlot_polyboundary[k:k + 2]) for k in range(len(totlot_polyboundary) - 1)]

                                totlot_line_points = [list(ls.coords) for ls in totlot_lineb]

                                for totlotline in totlot_line_points:

                                    splitline2points = self.splitLinetopoints(totlotline[0], totlotline[1], 50)

                                    splittotpts = []

                                    for splitpts in splitline2points[10:-10]:

                                        if (max_np_totlot_linepts[0] > splitpts[0] and min_np_totlot_linepts[0] < splitpts[0]) or (max_np_totlot_linepts[1] > splitpts[1] and min_np_totlot_linepts[1] < splitpts[1]):

                                            splittotpts.append(True)
                                        else:
                                            splittotpts.append(False)

                                    list_oftotlotline.append(any(splittotpts))

                                if any(list_oftotlotline) == True:

                                    if totlot_linex.distance(totlot) != 0.0:
                                        totlottototlotdist.append(totlot_linex.distance(totlot))

            elif (dist_min_margin_line_pts[0] < dist_min_margin_line_pts[1]):

                for totlot_linex in totlot_line_points:

                    if round(totlot_linex.distance(Marginline), 1) == round(min(totlot_line2margindist), 1):

                        totlot_ptsX, totlot_ptsY = totlot_linex.coords.xy

                        np_totlot_linepts = np.array([(totlot_ptsX[0], totlot_ptsY[0]), (totlot_ptsX[1], totlot_ptsY[1])])

                        max_np_totlot_linepts = np_totlot_linepts.max(axis=0)

                        min_np_totlot_linepts = np_totlot_linepts.min(axis=0)

                        dist_np_totlot_linepts = max_np_totlot_linepts - min_np_totlot_linepts

                        if dist_np_totlot_linepts[0] < dist_np_totlot_linepts[1]:

                            for totlot in ListTotLotPoly:

                                list_oftotlotline = []

                                totlot_polyboundary = totlot.boundary.coords

                                totlot_lineb = [LineString(totlot_polyboundary[k:k + 2]) for k in range(len(totlot_polyboundary) - 1)]

                                totlot_line_points = [list(ls.coords) for ls in totlot_lineb]

                                for totlotline in totlot_line_points:

                                    splitline2points = self.splitLinetopoints(totlotline[0], totlotline[1], 50)

                                    splittotpts = []

                                    for splitpts in splitline2points[10:-10]:

                                        if (max_np_totlot_linepts[1] >= splitpts[1] and splitpts[1] <= min_np_totlot_linepts[1]) or (max_np_totlot_linepts[0] > splitpts[0] and min_np_totlot_linepts[0] < splitpts[0]):

                                            splittotpts.append(True)
                                        else:
                                            splittotpts.append(False)

                                    list_oftotlotline.append(any(splittotpts))

                                if any(list_oftotlotline) == True:

                                    if round(totlot_linex.distance(totlot), 1) != 0.0:
                                        # print(prop_linex.distance(totlot))
                                        totlottototlotdist.append(totlot_linex.distance(totlot))

            if totlottototlotdist != [] or len(totlottototlotdist) > 0:
                return totlottototlotdist
    # checking common polygon have totlot or not
    def BounboxNotContainTotLot(self, propsed_poly, ListtotlotPoly):

        BoundboxNotContaintotlot = []

        for totlot_poly in ListtotlotPoly:

            if propsed_poly.contains(totlot_poly) == False and propsed_poly.touches(totlot_poly) == False and round(propsed_poly.distance(totlot_poly), 1) != 0.0:
                BoundboxNotContaintotlot.append(totlot_poly)

        return BoundboxNotContaintotlot
    # common polygon have proposedwork or not
    def BounboxNotContainProp(self, propsed_poly, ListProposedPoly):

        BoundboxNotContainprop = []

        for proposed1_poly in ListProposedPoly:

            if propsed_poly.contains(proposed1_poly[1]) == False and propsed_poly.touches(proposed1_poly[1]) == False and round(propsed_poly.distance(proposed1_poly[1]), 1) != 0.0:
                BoundboxNotContainprop.append(proposed1_poly)

        return BoundboxNotContainprop
    # split points from line
    def splitLinetopoints(self, start, end, seg):  # this function used for Spliting the lines

        x_delta = (end[0] - start[0]) / float(seg)

        y_delta = (end[1] - start[1]) / float(seg)

        points = []

        for i in range(1, seg):

            pts = [start[0] + i * x_delta, start[1] + i * y_delta]

            points.append(pts)

        return [start] + points + [end]
    # calculate min distance between margin line and propowork if proposed between them
    def DistProp2marginanotherProp(self, propsed_poly, Marginline, ListProposedPoly):

        margin_xpts, margin_ypts = Marginline.coords.xy

        np_margin_line_pts = np.array([[margin_xpts[0], margin_ypts[0]], [margin_xpts[1], margin_ypts[1]]])

        max_margin_line_pts = np_margin_line_pts.max(axis=0)

        min_margin_line_pts = np_margin_line_pts.min(axis=0)

        dist_min_margin_line_pts = max_margin_line_pts - min_margin_line_pts

        propsed_polyboundary = propsed_poly.boundary.coords if isinstance(propsed_poly.boundary,LineString or Polygon) else propsed_poly.geoms[0]

        # prop_line_points = [LineString([[propsed_polyboundary[0][i],propsed_polyboundary[1][i]],[propsed_polyboundary[0][i+1],propsed_polyboundary[1][i+1]]]) for i in range(len(propsed_polyboundary[0])-1)]
        prop_lineb = [LineString(propsed_polyboundary[k:k + 2]) for k in range(len(propsed_polyboundary) - 1)]

        prop_line_points = [LineString(list(ls.coords)) for ls in prop_lineb]

        prop_line2margindist = [prop_line.distance(Marginline) for prop_line in prop_line_points]

        if prop_line2margindist != []:

            proptoprop1dist = []

            if dist_min_margin_line_pts[0] > dist_min_margin_line_pts[1]:

                for prop_linex in prop_line_points:

                    if round(prop_linex.distance(Marginline), 1) == round(min(prop_line2margindist), 1):

                        prop_ptsX, prop_ptsY = prop_linex.coords.xy

                        np_prop_linepts = np.array([(prop_ptsX[0], prop_ptsY[0]), (prop_ptsX[1], prop_ptsY[1])])

                        max_np_prop_linepts = np_prop_linepts.max(axis=0)

                        min_np_prop_linepts = np_prop_linepts.min(axis=0)

                        dist_np_prop_linepts = max_np_prop_linepts - min_np_prop_linepts

                        if dist_np_prop_linepts[0] > dist_np_prop_linepts[1]:

                            for proposed1 in ListProposedPoly:

                                list_ofpropline = []

                                proposed1_polyboundary = proposed1[1].boundary.coords

                                proposed1_lineb = [LineString(proposed1_polyboundary[k:k + 2]) for k in range(len(proposed1_polyboundary) - 1)]

                                prop_line_points = [list(ls.coords) for ls in proposed1_lineb]

                                for prop1line in prop_line_points:

                                    splitline2points = self.splitLinetopoints(prop1line[0], prop1line[1], 100)

                                    splittotpts = []

                                    for splitpts in splitline2points[10:-10]:

                                        if (max_np_prop_linepts[0] > splitpts[0] and min_np_prop_linepts[0] < splitpts[0]) and (max_np_prop_linepts[1] > splitpts[1] and min_np_prop_linepts[1] <splitpts[1]):

                                            splittotpts.append(True)

                                    list_ofpropline.append(any(splittotpts))

                                if any(list_ofpropline) == True:

                                    if round(prop_linex.distance(proposed1[1]), 1) != 0.0:
                                        proptoprop1dist.append(prop_linex.distance(proposed1[1]))

            elif (dist_min_margin_line_pts[0] < dist_min_margin_line_pts[1]):

                for prop_linex in prop_line_points:

                    if round(prop_linex.distance(Marginline), 1) == round(min(prop_line2margindist), 1):

                        prop_ptsX, prop_ptsY = prop_linex.coords.xy

                        np_prop_linepts = np.array([(prop_ptsX[0], prop_ptsY[0]), (prop_ptsX[1], prop_ptsY[1])])

                        max_np_prop_linepts = np_prop_linepts.max(axis=0)

                        min_np_prop_linepts = np_prop_linepts.min(axis=0)

                        dist_np_prop_linepts = max_np_prop_linepts - min_np_prop_linepts

                        if dist_np_prop_linepts[0] < dist_np_prop_linepts[1]:

                            for proposed1 in ListProposedPoly:

                                list_ofpropline = []

                                proposed1_polyboundary = proposed1[1].boundary.coords

                                proposed1_lineb = [LineString(proposed1_polyboundary[k:k + 2]) for k in range(len(proposed1_polyboundary) - 1)]

                                prop_line_points = [list(ls.coords) for ls in proposed1_lineb]

                                for prop1line in prop_line_points:

                                    splitline2points = self.splitLinetopoints(prop1line[0], prop1line[1], 100)

                                    splittotpts = []

                                    for splitpts in splitline2points[10:-10]:

                                        if (max_np_prop_linepts[1] > splitpts[1] and min_np_prop_linepts[1] < splitpts[1]) and (max_np_prop_linepts[0] > splitpts[0] and min_np_prop_linepts[0] < splitpts[0]):

                                            splittotpts.append(True)
                                        else:
                                            splittotpts.append(False)

                                    list_ofpropline.append(splittotpts)

                                if any(list_ofpropline) == True:

                                    if round(prop_linex.distance(proposed1[1]), 1) != 0.0:
                                        proptoprop1dist.append(prop_linex.distance(proposed1[1]))

            if proptoprop1dist != [] or len(proptoprop1dist) > 0:
                return proptoprop1dist
    # calculate min distance between margin line and propowork if totlot between them
    def DistProp2marginanotherTotLot(self, propsed_poly, Marginline, ListTotLotPoly):

        margin_xpts, margin_ypts = Marginline.coords.xy

        np_margin_line_pts = np.array([[margin_xpts[0], margin_ypts[0]], [margin_xpts[1], margin_ypts[1]]])

        max_margin_line_pts = np_margin_line_pts.max(axis=0)

        min_margin_line_pts = np_margin_line_pts.min(axis=0)

        dist_min_margin_line_pts = max_margin_line_pts - min_margin_line_pts

        propsed_polyboundary = propsed_poly.boundary.coords

        prop_lineb = [LineString(propsed_polyboundary[k:k + 2]) for k in range(len(propsed_polyboundary) - 1)]

        prop_line_points = [LineString(list(ls.coords)) for ls in prop_lineb]

        prop_line2margindist = [prop_line.distance(Marginline) for prop_line in prop_line_points]

        if prop_line2margindist != []:

            proptototlotdist = []

            if dist_min_margin_line_pts[0] > dist_min_margin_line_pts[1]:

                for prop_linex in prop_line_points:

                    if round(prop_linex.distance(Marginline), 1) == round(min(prop_line2margindist), 1):

                        prop_ptsX, prop_ptsY = prop_linex.coords.xy

                        np_prop_linepts = np.array([(prop_ptsX[0], prop_ptsY[0]), (prop_ptsX[1], prop_ptsY[1])])

                        max_np_prop_linepts = np_prop_linepts.max(axis=0)

                        min_np_prop_linepts = np_prop_linepts.min(axis=0)

                        dist_np_prop_linepts = max_np_prop_linepts - min_np_prop_linepts

                        if dist_np_prop_linepts[0] > dist_np_prop_linepts[1]:

                            # print(np_prop_linepts)

                            for totlot in ListTotLotPoly:

                                list_oftotlotline = []

                                totlot_polyboundary = totlot.boundary.coords

                                totlot_lineb = [LineString(totlot_polyboundary[k:k + 2]) for k in range(len(totlot_polyboundary) - 1)]

                                totlot_line_points = [list(ls.coords) for ls in totlot_lineb]

                                for totlotline in totlot_line_points:

                                    splitline2points = self.splitLinetopoints(totlotline[0], totlotline[1], 50)

                                    splittotpts = []

                                    for splitpts in splitline2points[10:-10]:

                                        if (max_np_prop_linepts[0] > splitpts[0] and min_np_prop_linepts[0] < splitpts[ 0]) or (max_np_prop_linepts[1] > splitpts[1] and min_np_prop_linepts[1] < splitpts[1]):

                                            splittotpts.append(True)
                                        else:
                                            splittotpts.append(False)

                                    list_oftotlotline.append(any(splittotpts))

                                if any(list_oftotlotline) == True:

                                    if prop_linex.distance(totlot) != 0.0:
                                        proptototlotdist.append(prop_linex.distance(totlot))

            elif (dist_min_margin_line_pts[0] < dist_min_margin_line_pts[1]):

                for prop_linex in prop_line_points:

                    if round(prop_linex.distance(Marginline), 1) == round(min(prop_line2margindist), 1):

                        prop_ptsX, prop_ptsY = prop_linex.coords.xy

                        np_prop_linepts = np.array([(prop_ptsX[0], prop_ptsY[0]), (prop_ptsX[1], prop_ptsY[1])])

                        max_np_prop_linepts = np_prop_linepts.max(axis=0)

                        min_np_prop_linepts = np_prop_linepts.min(axis=0)

                        dist_np_prop_linepts = max_np_prop_linepts - min_np_prop_linepts

                        if dist_np_prop_linepts[0] < dist_np_prop_linepts[1]:

                            for totlot in ListTotLotPoly:

                                list_oftotlotline = []

                                totlot_polyboundary = totlot.boundary.coords

                                totlot_lineb = [LineString(totlot_polyboundary[k:k + 2]) for k in range(len(totlot_polyboundary) - 1)]

                                totlot_line_points = [list(ls.coords) for ls in totlot_lineb]

                                for totlotline in totlot_line_points:

                                    splitline2points = self.splitLinetopoints(totlotline[0], totlotline[1], 50)

                                    splittotpts = []

                                    for splitpts in splitline2points[10:-10]:

                                        if (max_np_prop_linepts[1] >= splitpts[1] and splitpts[1] <= min_np_prop_linepts[1]) or (  max_np_prop_linepts[0] > splitpts[0] and min_np_prop_linepts[0] < splitpts[0]):

                                            splittotpts.append(True)
                                        else:
                                            splittotpts.append(False)

                                    list_oftotlotline.append(any(splittotpts))

                                if any(list_oftotlotline) == True:

                                    if round(prop_linex.distance(totlot), 1) != 0.0:
                                        # print(prop_linex.distance(totlot))
                                        proptototlotdist.append(prop_linex.distance(totlot))

            if proptototlotdist != [] or len(proptototlotdist) > 0:
                return proptototlotdist
    # joined proposed work and totlot if touched
    def TotLotJointWidthProposedWork(self, MergedPolygon, TotlotPolygon):

        totlotJoinedMergedPolygon = []

        for TotlotPoly in TotlotPolygon:

            if MergedPolygon.touches(TotlotPoly) == True or round(MergedPolygon.distance(TotlotPoly), 1) == 0.0:
                totlotJoinedMergedPolygon.append(TotlotPoly)

        if totlotJoinedMergedPolygon != [] and len(totlotJoinedMergedPolygon) > 0:
            return totlotJoinedMergedPolygon
    # check totlot in plot
    def TotLotINPlot(self, PlotDict, OrganizedOpenSpaceDict):

        TotLotINPlot = []

        for Plot_id, PlotNamePoly in PlotDict.items():

            for Org_id, OrgNamePoly in OrganizedOpenSpaceDict.items():

                if ('tot lot' in OrgNamePoly[0].lower()) or ('tot-lot' in OrgNamePoly[0].lower()):

                    if PlotNamePoly[1].contains(OrgNamePoly[1]) == True or PlotNamePoly[1].touches(OrgNamePoly[1]) == True or round(PlotNamePoly[1].distance(OrgNamePoly[1]), 1) == 0.0:
                        TotLotINPlot.append(OrgNamePoly[1])

        if TotLotINPlot != [] and len(TotLotINPlot) > 0:
            return TotLotINPlot
    # --------------checking labes in polygon or not------------
    def Plot_layer(self, PlotData):

        PlotDict = dict()

        for Plot_entity in PlotData:

            if Plot_entity.dxftype() == 'LWPOLYLINE':

                PlotPolgonId = Plot_entity.dxf.handle

                PlotPolygonPoints = Polygon(np.array([pp[0:2] for pp in Plot_entity.get_points()]))

                PlotContainLabels = []

                for Plot_entity in PlotData:

                    if Plot_entity.dxftype() == 'TEXT' or Plot_entity.dxftype() == 'MTEXT':

                        Plottext_id = Plot_entity.dxf.handle

                        Plot_Properties = Plot_entity.dxfattribs()

                        Plot_name = Plot_Properties.get('text') if Plot_entity.dxftype() == 'TEXT' else Plot_entity.plain_text()

                        Plot_name = Plot_name.strip().replace(" ", "")

                        if "plot" in Plot_name.lower():

                            Plot_pts = Plot_Properties.get('insert')

                            PlottextPoint = Point(np.array([Plot_pts[0], Plot_pts[1]]))

                            if PlotPolygonPoints.contains(PlottextPoint) == True or PlotPolygonPoints.touches(PlottextPoint) == True or round(PlotPolygonPoints.distance(PlottextPoint),1) == 0.0:
                                PlotContainLabels.append([Plottext_id, Plot_name, PlotPolygonPoints])

                if PlotContainLabels != [] and len(PlotContainLabels) > 0:

                    for Plot in PlotContainLabels:
                        PlotDict[Plot[0]] = [Plot[1], Plot[2]]

                else:

                    print(f'Missing Label For Plot Layer Polygon ({PlotPolgonId}).')

        return PlotDict
    def OrganizedOpenSpace_layer(self, OrganizedOpenSpaceData):

        OrganizedOpenSpaceDict = dict()

        for OrganizedOpenSpace_entity in OrganizedOpenSpaceData:

            if OrganizedOpenSpace_entity.dxftype() == 'LWPOLYLINE':

                OrganizedOpenSpacePolgonId = OrganizedOpenSpace_entity.dxf.handle

                OrganizedOpenSpacePolygonPoints = Polygon( np.array([orgp[0:2] for orgp in OrganizedOpenSpace_entity.get_points()]))

                OrganizedOpenSpaceContainLabels = []

                for OrganizedOpenSpace_entity in OrganizedOpenSpaceData:

                    if OrganizedOpenSpace_entity.dxftype() == 'TEXT' or OrganizedOpenSpace_entity.dxftype() == 'MTEXT':

                        OrganizedOpenSpacetext_id = OrganizedOpenSpace_entity.dxf.handle

                        OrganizedOpenSpace_Properties = OrganizedOpenSpace_entity.dxfattribs()

                        OrganizedOpenSpace_name = OrganizedOpenSpace_Properties.get(
                            'text') if OrganizedOpenSpace_entity.dxftype() == 'TEXT' else OrganizedOpenSpace_entity.plain_text()

                        OrganizedOpenSpace_pts = OrganizedOpenSpace_Properties.get('insert')

                        OrganizedOpenSpacetextPoint = Point(
                            np.array([OrganizedOpenSpace_pts[0], OrganizedOpenSpace_pts[1]]))

                        if OrganizedOpenSpacePolygonPoints.contains(
                                OrganizedOpenSpacetextPoint) == True or OrganizedOpenSpacePolygonPoints.touches(
                                OrganizedOpenSpacetextPoint) == True or round(
                                OrganizedOpenSpacePolygonPoints.distance(OrganizedOpenSpacetextPoint), 1) == 0.0:
                            OrganizedOpenSpaceContainLabels.append(
                                [OrganizedOpenSpacetext_id, OrganizedOpenSpace_name, OrganizedOpenSpacePolygonPoints])

                if OrganizedOpenSpaceContainLabels != [] and len(OrganizedOpenSpaceContainLabels) > 0:

                    for OrganizedOpenSpace in OrganizedOpenSpaceContainLabels:
                        OrganizedOpenSpaceDict[OrganizedOpenSpace[0]] = [OrganizedOpenSpace[1], OrganizedOpenSpace[2]]

                else:

                    print(f'Missing Label For OrganizedOpenSpace Layer Polygon ({OrganizedOpenSpacePolgonId}).')

        return OrganizedOpenSpaceDict
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

                            front_line_points = LineString(np.array([(vir_entity.dxf.start[0], vir_entity.dxf.start[1]), (vir_entity.dxf.end[0], vir_entity.dxf.end[1])]))

                            Front_data.append(front_line_points)

                        elif (vir_entity.dxf.color == 6):

                            rear_line_points = LineString(np.array([(vir_entity.dxf.start[0], vir_entity.dxf.start[1]), (vir_entity.dxf.end[0], vir_entity.dxf.end[1])]))

                            Rear_data.append(rear_line_points)


                        elif (vir_entity.dxf.color == 5):

                            side1_line_points = LineString(np.array([(vir_entity.dxf.start[0], vir_entity.dxf.start[1]),(vir_entity.dxf.end[0], vir_entity.dxf.end[1])]))

                            Side1_data.append(side1_line_points)

                        elif (vir_entity.dxf.color == 104 or vir_entity.dxf.color == 3):

                            side2_line_points = LineString(np.array([(vir_entity.dxf.start[0], vir_entity.dxf.start[1]),(vir_entity.dxf.end[0], vir_entity.dxf.end[1])]))

                            Side2_data.append(side2_line_points)

                    elif (vir_entity.dxftype() == 'ARC'):

                        if vir_entity.dxf.color == 1:

                            front_arc_points = LineString(np.array([(vir_entity.start_point[0], vir_entity.start_point[1]),(vir_entity.end_point[0], vir_entity.end_point[1])]))

                            Front_data.append(front_arc_points)

                        elif (vir_entity.dxf.color == 6):

                            rear_arc_points = LineString(np.array([(vir_entity.start_point[0], vir_entity.start_point[1]),(vir_entity.end_point[0], vir_entity.end_point[1])]))


                            Rear_data.append(rear_arc_points)

                        elif (vir_entity.dxf.color == 5):

                            side1_arc_points = LineString(np.array([(vir_entity.start_point[0], vir_entity.start_point[1]),(vir_entity.end_point[0], vir_entity.end_point[1])]))

                            Side1_data.append(side1_arc_points)

                        elif (vir_entity.dxf.color == 104 or vir_entity.dxf.color == 3):

                            side2_arc_points = LineString(np.array([(vir_entity.start_point[0], vir_entity.start_point[1]),(vir_entity.end_point[0], vir_entity.end_point[1])]))

                            Side2_data.append(side2_arc_points)

            elif (margin_entity.dxftype() == 'LINE'):

                if margin_entity.dxf.color == 1:

                    front_line_points = LineString(np.array([(margin_entity.dxf.start[0], margin_entity.dxf.start[1]),(margin_entity.dxf.end[0], margin_entity.dxf.end[1])]))

                    Front_data.append(front_line_points)

                elif (margin_entity.dxf.color == 6):

                    rear_line_points = LineString(np.array([(margin_entity.dxf.start[0], margin_entity.dxf.start[1]),(margin_entity.dxf.end[0], margin_entity.dxf.end[1])]))

                    Rear_data.append(rear_line_points)

                elif (margin_entity.dxf.color == 5):

                    side1_line_points = LineString(np.array([(margin_entity.dxf.start[0], margin_entity.dxf.start[1]),(margin_entity.dxf.end[0], margin_entity.dxf.end[1])]))

                    Side1_data.append(side1_line_points)

                elif (margin_entity.dxf.color == 104 or margin_entity.dxf.color == 3):

                    side2_line_points = LineString(np.array([(margin_entity.dxf.start[0], margin_entity.dxf.start[1]),(margin_entity.dxf.end[0], margin_entity.dxf.end[1])]))

                    Side2_data.append(side2_line_points)

            elif (margin_entity.dxftype() == 'ARC'):

                if margin_entity.dxf.color == 1:

                    front_arc_points = LineString(np.array([(margin_entity.start_point[0], margin_entity.start_point[1]),(margin_entity.end_point[0], margin_entity.end_point[1])]))

                    Front_data.append(front_arc_points)

                elif (margin_entity.dxf.color == 6):

                    rear_arc_points = LineString(np.array([(margin_entity.start_point[0], margin_entity.start_point[1]),(margin_entity.end_point[0], margin_entity.end_point[1])]))

                    Rear_data.append(rear_arc_points)

                elif (margin_entity.dxf.color == 5):

                    side1_arc_points = LineString(np.array([(margin_entity.start_point[0], margin_entity.start_point[1]),(margin_entity.end_point[0], margin_entity.end_point[1])]))

                    Side1_data.append(side1_arc_points)

                elif (margin_entity.dxf.color == 104 or margin_entity.dxf.color == 3):

                    side2_arc_points = LineString(np.array([(margin_entity.start_point[0], margin_entity.start_point[1]),(margin_entity.end_point[0], margin_entity.end_point[1])]))

                    Side2_data.append(side2_arc_points)

        if Front_data != [] and len(Front_data) > 0:

            MarginDict['FRONT'] = Front_data

        else:

            print('Missing Front of Red line for Margin layer')

        if Rear_data != [] and len(Rear_data) > 0:

            MarginDict['REAR'] = Rear_data

        else:

            print('Missing Rear of Pink line for Margin layer')

        if Side1_data != [] and len(Side1_data) > 0:

            MarginDict['SIDE1'] = Side1_data

        else:

            print('Missing Side1 of Blue line for Margin layer')

        if Side2_data != [] and len(Side2_data) > 0:

            MarginDict['SIDE2'] = Side2_data

        else:

            print('Missing Side2 of Green line for Margin layer')


        return MarginDict
    def ParkingINFloor(self, Floor_polygon, list_of_Parking):

        ParkingPolygonContainsFloor = []

        for parking_id, ParkingNamePoly in list_of_Parking.items():

            if 'parking' in ParkingNamePoly[0].lower():

                if Floor_polygon.contains(ParkingNamePoly[1]) == True or Floor_polygon.touches(ParkingNamePoly[1]) == True or round(Floor_polygon.distance(ParkingNamePoly[1]), 1) == 0.0:
                    ParkingPolygonContainsFloor.append(ParkingNamePoly[1])

        if ParkingPolygonContainsFloor != [] and len(ParkingPolygonContainsFloor) > 0:
            return ParkingPolygonContainsFloor[0]
    def Parking_layer(self, ParkingData):

        ParkingDict = dict()

        for Parking_entity in ParkingData:

            if Parking_entity.dxftype() == 'LWPOLYLINE':

                ParkingPolgonId = Parking_entity.dxf.handle

                if len([pp[0:2] for pp in Parking_entity.get_points()]) > 3:

                    ParkingPolygonPoints = Polygon(np.array([pp[0:2] for pp in Parking_entity.get_points()]))

                    ParkingContainLabels = []

                    for Parking_entity in ParkingData:

                        if Parking_entity.dxftype() == 'TEXT' or Parking_entity.dxftype() == 'MTEXT':

                            Parkingtext_id = Parking_entity.dxf.handle

                            Parking_Properties = Parking_entity.dxfattribs()

                            Parking_name = Parking_Properties.get(
                                'text') if Parking_entity.dxftype() == 'TEXT' else Parking_entity.plain_text()

                            Parking_pts = Parking_Properties.get('insert')

                            ParkingtextPoint = Point(np.array([Parking_pts[0], Parking_pts[1]]))

                            if ParkingPolygonPoints.contains(ParkingtextPoint) == True or ParkingPolygonPoints.touches(ParkingtextPoint) == True or round(ParkingPolygonPoints.distance(ParkingtextPoint),1) == 0.0:
                                ParkingContainLabels.append([Parkingtext_id, Parking_name, ParkingPolygonPoints])

                    if ParkingContainLabels != [] and len(ParkingContainLabels) > 0:

                        for Parking in ParkingContainLabels:
                            ParkingDict[Parking[0]] = [Parking[1], Parking[2]]

                    else:

                        print(f'Missing Label For Parking layer Polygon ({ParkingPolgonId}).')

        return ParkingDict
    def ResiDirRefCircleINFloor(self, FloorNamePoly, Resibua_DirRefCircle):

        DirRefCircleInProposedWork = []

        for entity in Resibua_DirRefCircle:

            for ent in entity.virtual_entities():

                if ent.dxftype() == 'CIRCLE':

                    Resibua_center_point = Point(np.array([ent.dxf.center[0], ent.dxf.center[1]]))

                    if FloorNamePoly[1].contains(Resibua_center_point) == True or FloorNamePoly[1].touches(Resibua_center_point) == True or round(FloorNamePoly[1].distance(Resibua_center_point),1) == 0.0:
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

                    if ProposedWorkNamePoly[1].contains(Resibua_center_point) == True or ProposedWorkNamePoly[1].touches(Resibua_center_point) == True or round(ProposedWorkNamePoly[1].distance(Resibua_center_point), 1) == 0.0:
                        DirRefCircleInProposedWork.append(Resibua_center_point)

        if DirRefCircleInProposedWork != [] and len(DirRefCircleInProposedWork) > 0:

            return DirRefCircleInProposedWork[0]

        else:

            print(f'Missing Resibua Direction Refrence Circle in {ProposedWorkNamePoly[0]} ProposedWork Layer.')
    def BUATypeINFloor(self, Floor_polygon, list_of_BUA):

        listBUAinFloor = []

        for Bua in list_of_BUA:

            for BuaPolygon in Bua:

                if len([BUAp[0:2] for BUAp in BuaPolygon.get_points()]) > 3:

                    bua_polygon = Polygon(np.array([BUAp[0:2] for BUAp in BuaPolygon.get_points()]))

                    if Floor_polygon.contains(bua_polygon) == True or Floor_polygon.touches(bua_polygon) == True or round(Floor_polygon.distance(bua_polygon), 1) == 0.0:
                        listBUAinFloor.append(bua_polygon)

        if (len(listBUAinFloor) > 0 and len(listBUAinFloor) < 1) or listBUAinFloor != []:

            return listBUAinFloor[0]

        elif ((listBUAinFloor != [] and len(listBUAinFloor) > 1) or listBUAinFloor != []):

            return unary_union(listBUAinFloor)
    def Floor_layer(self, FloorData):

        FloorDict = dict()

        for Floor_entity in FloorData:

            if Floor_entity.dxftype() == 'LWPOLYLINE':

                FloorPolgonId = Floor_entity.dxf.handle

                FloorPolygonPoints = Polygon(np.array([fp[0:2] for fp in Floor_entity.get_points()]))

                FloorContainLabels = []

                for Floor_entity in FloorData:

                    if Floor_entity.dxftype() == 'TEXT' or Floor_entity.dxftype() == 'MTEXT':

                        Floortext_id = Floor_entity.dxf.handle

                        Floor_Properties = Floor_entity.dxfattribs()

                        Floor_name = Floor_Properties.get(
                            'text') if Floor_entity.dxftype() == 'TEXT' else Floor_entity.plain_text()

                        Floor_pts = Floor_Properties.get('insert')

                        FloortextPoint = Point(np.array([Floor_pts[0], Floor_pts[1]]))

                        if FloorPolygonPoints.contains(FloortextPoint) == True or FloorPolygonPoints.touches(FloortextPoint) == True or round(FloorPolygonPoints.distance(FloortextPoint), 1) == 0.0:
                            FloorContainLabels.append([Floortext_id, Floor_name, FloorPolygonPoints])

                if FloorContainLabels != [] and len(FloorContainLabels) > 0:

                    for BuildingName in FloorContainLabels:
                        FloorDict[BuildingName[0]] = [BuildingName[1], BuildingName[2]]

                else:

                    print(f'Missing Label For Floor Layer Polygon ({FloorPolgonId}).')

        return FloorDict
    def BuildingName_layer(self, BuildingNameData):

        BuildingNameDict = dict()

        for BuildingName_entity in BuildingNameData:

            if BuildingName_entity.dxftype() == 'LWPOLYLINE':

                BuildingNamePolgonId = BuildingName_entity.dxf.handle

                BuildingNamePolygonPoints = Polygon(np.array([bp[0:2] for bp in BuildingName_entity.get_points()]))

                BuildingNameContainLabels = []

                for BuildingName_entity in BuildingNameData:

                    if BuildingName_entity.dxftype() == 'TEXT' or BuildingName_entity.dxftype() == 'MTEXT':

                        BuildingNametext_id = BuildingName_entity.dxf.handle

                        BuildingName_Properties = BuildingName_entity.dxfattribs()

                        BuildingName_name = BuildingName_Properties.get(
                            'text') if BuildingName_entity.dxftype() == 'TEXT' else BuildingName_entity.plain_text()

                        if BuildingName_name != '':

                            BuildingName_pts = BuildingName_Properties.get('insert')

                            BuildingNametextPoint = Point(np.array([BuildingName_pts[0], BuildingName_pts[1]]))

                            if BuildingNamePolygonPoints.contains(BuildingNametextPoint) == True or BuildingNamePolygonPoints.touches(BuildingNametextPoint) == True or round(BuildingNamePolygonPoints.distance(BuildingNametextPoint), 1) == 0.0:
                                BuildingNameContainLabels.append([BuildingNametext_id, BuildingName_name, BuildingNamePolygonPoints])

                if BuildingNameContainLabels != [] and len(BuildingNameContainLabels) > 0:

                    for BuildingName in BuildingNameContainLabels:
                        BuildingNameDict[BuildingName[0]] = [BuildingName[1], BuildingName[2]]

                else:

                    print(f'Missing Label For BuildingName Layer Polygon ({BuildingNamePolgonId}).')

        return BuildingNameDict
    #==============================================================================
    def DirectionslabelWithmarginLines(self,proposedTouchLabels,margin_line):

        min_distance = float("inf")
        closest_label = None

        for proposed_label in proposedTouchLabels:
            proposed_label_pts = Point([proposed_label.dxf.insert[0], proposed_label.dxf.insert[1]])

            proposed_name = proposed_label.dxf.text if proposed_label.dxftype() == "TEXT" else proposed_label.plain_text()

            distance = round(margin_line.distance(proposed_label_pts), 1)

            if distance != 0.0 and distance < min_distance:
                min_distance = distance
                closest_label = proposed_name


        return closest_label
    def Bounding_Box_TouchWith_DirectionsLabel(self,ListOfDirectionLabel,MargePolygon):

        proposed_entity = []
        for proposed_label in ListOfDirectionLabel:
            proposed_label_pts = Point([proposed_label.dxf.insert[0],proposed_label.dxf.insert[1]])
            if MargePolygon.touches(proposed_label_pts) == True or round(MargePolygon.distance(proposed_label_pts),1) == 0.0:

                proposed_entity.append(proposed_label)

        return proposed_entity
    def ProposedWorkDirections_label(self,ProposedWorkData):

        proposedDirection_Entity = []

        for proposed_label in ProposedWorkData:

            if proposed_label.dxftype() == "TEXT" or proposed_label.dxftype() == "MTEXT" :

                proposed_name = proposed_label.dxf.text if proposed_label.dxftype() == "TEXT" else proposed_label.plain_text()

                proposed_name1 = proposed_name.lower().replace(" ","")

                if proposed_name1 !="" and any(proposed_name1 == proposedworks for proposedworks in ["south","north","east","west"]) == True:

                    proposedDirection_Entity.append(proposed_label)

        return proposedDirection_Entity
        #print(proposedDirection_Entity)
    #==============================================================================
    def ProposedWork_layer(self, ProposedWorkData):

        ProposedWorkDict = dict()

        for proposedWork_entity in ProposedWorkData:

            if proposedWork_entity.dxftype() == 'LWPOLYLINE':

                ProposeWorkPolgonId = proposedWork_entity.dxf.handle

                ProposedWorkPolygonPoints = Polygon(np.array([pwp[0:2] for pwp in proposedWork_entity.get_points()]))

                ProposedWorkContainLabels = []

                for proposedWork_entity in ProposedWorkData:

                    if proposedWork_entity.dxftype() == 'TEXT' or proposedWork_entity.dxftype() == 'MTEXT':

                        proposedworktext_id = proposedWork_entity.dxf.handle

                        proposerwork_Properties = proposedWork_entity.dxfattribs()

                        proposedwork_name = proposerwork_Properties.get('text') if proposedWork_entity.dxftype() == 'TEXT' else proposedWork_entity.plain_text()
                        proposedwork_name1 = proposedwork_name.lower().replace(" ","")
                        if proposedwork_name1 != '' and any(proposedwork_name1 == proposedname for proposedname in ["east","west","north","south"]) == False :

                            proposedwork_pts = proposerwork_Properties.get('insert')

                            proposedWorktextPoint = Point(np.array([proposedwork_pts[0], proposedwork_pts[1]]))

                            if ProposedWorkPolygonPoints.contains( proposedWorktextPoint) == True or ProposedWorkPolygonPoints.touches( proposedWorktextPoint) == True or round(ProposedWorkPolygonPoints.distance(proposedWorktextPoint), 1) == 0.0:
                                ProposedWorkContainLabels.append([proposedworktext_id, proposedwork_name, ProposedWorkPolygonPoints])

                if ProposedWorkContainLabels != [] and len(ProposedWorkContainLabels) > 0:

                    for proposedWork in ProposedWorkContainLabels:
                        ProposedWorkDict[proposedWork[0]] = [proposedWork[1], proposedWork[2]]

                else:

                    print(f'Missing Label For ProposedWork layer Polygon ({ProposeWorkPolgonId}).')

        return ProposedWorkDict
    # calculating Common setbacks
    def FloorSebacks(self, msp):

        returnValueList = []

        if (msp is None):

            return returnValueList

        try:

            print('read Dxf file FloorSebacks')

            ProposedWorkData = msp.query('*[layer=="_ProposedWork"]')


            BuildingNameData = msp.query('*[layer=="_BuildingName"]')

            FloorData = msp.query('*[layer=="_Floor"]')

            commbua_Data = msp.query('LWPOLYLINE[layer=="_CommBUAOutline"]')

            resibua_Data = msp.query('LWPOLYLINE[layer=="_ResiBUAOutline"]')

            indivbua_Data = msp.query('LWPOLYLINE[layer=="_IndBUAOutline"]')

            specialbua_Data = msp.query('LWPOLYLINE[layer=="_SpecialUseBUAOutline"]')

            MarginData = msp.query('*[layer=="_MarginLine"]')

            resibuaDIRREFCircle_data = msp.query('INSERT[layer=="_ResiBUAOutline"]')

            ParkingData = msp.query('*[layer=="_Parking"]')

            OrganizedOpenSpaceData = msp.query('*[layer=="_OrganizedOpenSpace"]')

            PlotData = msp.query('*[layer=="_Plot"]')

            ProposedWorkLayerDict = self.ProposedWork_layer(ProposedWorkData)


            ProposedLabeldata = self.ProposedWorkDirections_label(ProposedWorkData)


            # print(ProposedWorkLayerDict)
            BuildingNameLayerDict = self.BuildingName_layer(BuildingNameData)
            # print(BuildingNameLayerDict)
            FloorLayerDict = self.Floor_layer(FloorData)

            ParkingLayerDict = self.Parking_layer(ParkingData)

            MarginLayerDict = self.MarginLineLayer(MarginData)

            OrganizedOpenSpaceDataLayerDict = self.OrganizedOpenSpace_layer(OrganizedOpenSpaceData)

            PlotDict = self.Plot_layer(PlotData)

            TotLotINPlotList = self.TotLotINPlot(PlotDict, OrganizedOpenSpaceDataLayerDict)

            # get proposed work text query from proposed_work_data_list

            for ProposedWork_id, ProposedWorkNamePoly in ProposedWorkLayerDict.items():

                # print(ProposedWork_id,ProposedWorkNamePoly)
                propresibuaDIRREFCircle = self.ResiDirRefCircleINProposedWork(ProposedWorkNamePoly,resibuaDIRREFCircle_data)

                # print('Proposed Work ref circle',propresibuaDIRREFCircle)

                Filter_ProposedWork_Name = "".join(x for x in ProposedWorkNamePoly[0] if x.isalpha())

                for Building_id, BuildingNamePoly in BuildingNameLayerDict.items():

                    Filter_Building_Name = "".join(y for y in BuildingNamePoly[0] if y.isalpha())

                    if Filter_ProposedWork_Name == Filter_Building_Name:
                        print(ProposedWorkNamePoly[0], BuildingNamePoly[0])
                        # print('Matched labels:',(ProposedWorkNamePoly[0],BuildingNamePoly[0]))

                        ContainsResiBUAANDPARKING = []

                        for Floor_id, FloorNamePoly in FloorLayerDict.items():

                            if any(words in FloorNamePoly[0].lower() for words in ['cellar', 'basement']) == False:

                                if BuildingNamePoly[1].contains(FloorNamePoly[1]) == True or BuildingNamePoly[1].touches(FloorNamePoly[1]) == True or round( BuildingNamePoly[1].distance(FloorNamePoly[1]), 1) == 0.0:

                                    floorresibuaDIRREFCircle = self.ResiDirRefCircleINFloor(FloorNamePoly,resibuaDIRREFCircle_data)

                                    FloorContainsParking = self.ParkingINFloor(FloorNamePoly[1], ParkingLayerDict)

                                    FloorContainsBUA = self.BUATypeINFloor(Floor_polygon=FloorNamePoly[1],list_of_BUA=[resibua_Data, commbua_Data,indivbua_Data, specialbua_Data])

                                    # print(FloorNamePoly[0])

                                    # print('distance', propresibuaDIRREFCircle.distance(floorresibuaDIRREFCircle))

                                    propcenter_x, propcenter_y = propresibuaDIRREFCircle.coords.xy

                                    floorcenter_x, floorcenter_y = floorresibuaDIRREFCircle.coords.xy

                                    propFloorCenter_pts = [(propcenter_x[0], propcenter_y[0]),(floorcenter_x[0], floorcenter_y[0])]

                                    BothCenter_pts = np.array(propFloorCenter_pts)

                                    maxBothCenter_pts = BothCenter_pts.max(axis=0)

                                    minBothCenter_pts = BothCenter_pts.min(axis=0)

                                    # print(BothCenter_pts)
                                    # print('max',maxBothCenter_pts)
                                    # print('min', minBothCenter_pts)

                                    DistProp2FloorCeterpts = maxBothCenter_pts - minBothCenter_pts

                                    # print('Distance',DistProp2FloorCeterpts)

                                    # --------------------------------first Quadrant For Floor Center Points--------------------------------

                                    Floorcenterpts1stQuadrant = [round(floorcenter_x[0] + DistProp2FloorCeterpts[0], 3),
                                                                 round(floorcenter_y[0] + DistProp2FloorCeterpts[1], 3)]

                                    # print('First Quadrant Floor Center points',Floorcenterpts1stQuadrant)
                                    # --------------------------------Second Quadrant For Floor Center Points--------------------------------

                                    Floorcenterpts2ndQuadrant = [round(floorcenter_x[0] - DistProp2FloorCeterpts[0], 3),
                                                                 round(floorcenter_y[0] - DistProp2FloorCeterpts[1], 3)]
                                    # print('Second Quadrant Floor Center points', Floorcenterpts2ndQuadrant)
                                    # --------------------------------Third Quadrant For Floor Center Points--------------------------------

                                    Floorcenterpts3rdQuadrant = [round(floorcenter_x[0] + DistProp2FloorCeterpts[0], 3),
                                                                 round(floorcenter_y[0] - DistProp2FloorCeterpts[1], 3)]
                                    # print('Third Quadrant Floor Center points', Floorcenterpts3rdQuadrant)
                                    # --------------------------------Fourth Quadrant For Floor Center Points--------------------------------

                                    Floorcenterpts4thQuadrant = [round(floorcenter_x[0] - DistProp2FloorCeterpts[0], 3),
                                                                 round(floorcenter_y[0] + DistProp2FloorCeterpts[1], 3)]
                                    # print('Fourth Quadrant Floor Center points', Floorcenterpts4thQuadrant)

                                    # --------------------------------First Quadrant For Parking layer Resibua layer,Commbua layer--------------------------------

                                    Proposed_WorkCenterPts = [round(propcenter_x[0], 3), round(propcenter_y[0], 3)]

                                    if (Floorcenterpts1stQuadrant == Proposed_WorkCenterPts):

                                        # ---------------------------------Moving Bua Polygon from floor to proposed work for first Quadrant-----------------------------

                                        print('Matched First Quadrant')

                                        if FloorContainsBUA is not None:

                                            Moved_BUAPolygon_pts = []

                                            for BUAX_pts, BUAY_pts in zip(FloorContainsBUA.exterior.xy[0], FloorContainsBUA.exterior.xy[1]):
                                                BUA_pts = [BUAX_pts + DistProp2FloorCeterpts[0],
                                                           BUAY_pts + DistProp2FloorCeterpts[1]]

                                                Moved_BUAPolygon_pts.append(BUA_pts)

                                            MovedBuaPolygonPoints = Polygon(np.array(Moved_BUAPolygon_pts))

                                            ContainsResiBUAANDPARKING.append(MovedBuaPolygonPoints)

                                        # ---------------------------------Moving Parking Polygon from floor to proposed work for first Quadrant-----------------------------
                                        if FloorContainsParking is not None:

                                            Moved_ParkingPolygon_pts = []

                                            for ParkingX_pts, ParkingY_pts in zip(FloorContainsParking.exterior.xy[0],
                                                                                  FloorContainsParking.exterior.xy[1]):
                                                Parking_pts = [ParkingX_pts + DistProp2FloorCeterpts[0],
                                                               ParkingY_pts + DistProp2FloorCeterpts[1]]

                                                Moved_ParkingPolygon_pts.append(Parking_pts)

                                            MovedParkingPolygonPoints = Polygon(np.array(Moved_ParkingPolygon_pts))

                                            ContainsResiBUAANDPARKING.append(MovedParkingPolygonPoints)

                                    elif (Floorcenterpts2ndQuadrant == Proposed_WorkCenterPts):

                                        print('Matched Second Quadrant')

                                        # ---------------------------------Moving Bua Polygon from floor to proposed work for Second Quadrant-----------------------------
                                        if FloorContainsBUA is not None:
                                            # print(FloorContainsBUA)
                                            Moved_BUAPolygon_pts = []

                                            for BUAX_pts, BUAY_pts in zip(FloorContainsBUA.exterior.xy[0],
                                                                          FloorContainsBUA.exterior.xy[1]):
                                                BUA_pts = [BUAX_pts - DistProp2FloorCeterpts[0],
                                                           BUAY_pts - DistProp2FloorCeterpts[1]]

                                                Moved_BUAPolygon_pts.append(BUA_pts)
                                            # print(Moved_BUAPolygon_pts)
                                            # MovedBuaPolygonPoints = Polygon(np.array(Moved_BUAPolygon_pts))
                                            MovedBuaPolygonPoints = Polygon(Moved_BUAPolygon_pts)
                                            # print(MovedBuaPolygonPoints)
                                            ContainsResiBUAANDPARKING.append(MovedBuaPolygonPoints)

                                        # ---------------------------------Moving Parking Polygon from floor to proposed work for Second Quadrant-----------------------------
                                        if FloorContainsParking is not None:

                                            Moved_ParkingPolygon_pts = []

                                            for ParkingX_pts, ParkingY_pts in zip(FloorContainsParking.exterior.xy[0],
                                                                                  FloorContainsParking.exterior.xy[1]):
                                                Parking_pts = [ParkingX_pts - DistProp2FloorCeterpts[0],
                                                               ParkingY_pts - DistProp2FloorCeterpts[1]]

                                                Moved_ParkingPolygon_pts.append(Parking_pts)

                                            MovedParkingPolygonPoints = Polygon(np.array(Moved_ParkingPolygon_pts))

                                            ContainsResiBUAANDPARKING.append(MovedParkingPolygonPoints)

                                    elif (Floorcenterpts3rdQuadrant == Proposed_WorkCenterPts):

                                        print('Matched Third Quadrant')

                                        # ---------------------------------Moving Bua Polygon from floor to proposed work for Second Quadrant-----------------------------
                                        if FloorContainsBUA is not None:

                                            Moved_BUAPolygon_pts = []

                                            for BUAX_pts, BUAY_pts in zip(FloorContainsBUA.exterior.xy[0],
                                                                          FloorContainsBUA.exterior.xy[1]):
                                                BUA_pts = [BUAX_pts + DistProp2FloorCeterpts[0],
                                                           BUAY_pts - DistProp2FloorCeterpts[1]]

                                                Moved_BUAPolygon_pts.append(BUA_pts)

                                            MovedBuaPolygonPoints = Polygon(np.array(Moved_BUAPolygon_pts))

                                            ContainsResiBUAANDPARKING.append(MovedBuaPolygonPoints)

                                        # ---------------------------------Moving Parking Polygon from floor to proposed work for Second Quadrant-----------------------------

                                        if FloorContainsParking is not None:

                                            Moved_ParkingPolygon_pts = []

                                            for ParkingX_pts, ParkingY_pts in zip(FloorContainsParking.exterior.xy[0],
                                                                                  FloorContainsParking.exterior.xy[1]):
                                                Parking_pts = [ParkingX_pts + DistProp2FloorCeterpts[0],
                                                               ParkingY_pts - DistProp2FloorCeterpts[1]]

                                                Moved_ParkingPolygon_pts.append(Parking_pts)

                                            MovedParkingPolygonPoints = Polygon(np.array(Moved_ParkingPolygon_pts))

                                            ContainsResiBUAANDPARKING.append(MovedParkingPolygonPoints)

                                    elif (Floorcenterpts4thQuadrant == Proposed_WorkCenterPts):

                                        print('Matched Fourth Quadrant')

                                        # ---------------------------------Moving Bua Polygon from floor to proposed work for Second Quadrant-----------------------------
                                        if FloorContainsBUA is not None:

                                            Moved_BUAPolygon_pts = []

                                            for BUAX_pts, BUAY_pts in zip(FloorContainsBUA.exterior.xy[0],
                                                                          FloorContainsBUA.exterior.xy[1]):
                                                BUA_pts = [BUAX_pts - DistProp2FloorCeterpts[0],
                                                           BUAY_pts + DistProp2FloorCeterpts[1]]

                                                Moved_BUAPolygon_pts.append(BUA_pts)

                                            MovedBuaPolygonPoints = Polygon(np.array(Moved_BUAPolygon_pts))

                                            ContainsResiBUAANDPARKING.append(MovedBuaPolygonPoints)

                                        # ---------------------------------Moving Parking Polygon from floor to proposed work for Second Quadrant-----------------------------

                                        if FloorContainsParking is not None:

                                            Moved_ParkingPolygon_pts = []

                                            for ParkingX_pts, ParkingY_pts in zip(FloorContainsParking.exterior.xy[0],
                                                                                  FloorContainsParking.exterior.xy[1]):
                                                Parking_pts = [ParkingX_pts - DistProp2FloorCeterpts[0],
                                                               ParkingY_pts + DistProp2FloorCeterpts[1]]

                                                Moved_ParkingPolygon_pts.append(Parking_pts)

                                            MovedParkingPolygonPoints = Polygon(np.array(Moved_ParkingPolygon_pts))

                                            ContainsResiBUAANDPARKING.append(MovedParkingPolygonPoints)

                                    else:

                                        print('Does Not Matched in Any Quadrant')

                        # print(ContainsResiBUAANDPARKING)
                        xMergeMultiPolygons = unary_union(ContainsResiBUAANDPARKING)
                        proposedTouchLabels = self.Bounding_Box_TouchWith_DirectionsLabel(ProposedLabeldata,ProposedWorkNamePoly[1])

                        # MergeMultiPolygons = xMergeMultiPolygons if isinstance(xMergeMultiPolygons, Polygon) else self.MergeMultipolygonObject(xMergeMultiPolygons)
                        MergeMultiPolygons = xMergeMultiPolygons if xMergeMultiPolygons.geom_type == 'Polygon' else self.MergeMultipolygonObject(xMergeMultiPolygons)

                        sidesOfPolygonDict = dict()

                        if TotLotINPlotList is not None:

                            totjoinedWithprop = self.TotLotJointWidthProposedWork(MergeMultiPolygons, TotLotINPlotList)

                            BoundingBoxNotContainprop = self.BounboxNotContainProp(MergeMultiPolygons,ProposedWorkLayerDict.values())

                            BoundingBoxNotContaintotlot = self.BounboxNotContainTotLot(MergeMultiPolygons,TotLotINPlotList)

                            for Margin_side, Margin_lines in MarginLayerDict.items():

                                SidesOFValue = []

                                for margin_line in Margin_lines:

                                    if self.DistProp2marginanotherProp(MergeMultiPolygons, margin_line,BoundingBoxNotContainprop) is not None:
                                        SidesOFValue.append(min(self.DistProp2marginanotherProp(MergeMultiPolygons, margin_line,BoundingBoxNotContainprop)))

                                    if self.DistProp2marginanotherTotLot(MergeMultiPolygons, margin_line,BoundingBoxNotContaintotlot) is not None:
                                        SidesOFValue.append(min(self.DistProp2marginanotherTotLot(MergeMultiPolygons, margin_line,BoundingBoxNotContaintotlot)))

                                    if totjoinedWithprop is not None:

                                        propjoinedtotlotsetbacks = []

                                        for totlot_polygon in totjoinedWithprop:

                                            if self.DistPropjoinedtotlot2marginanotherProp(totlot_polygon, margin_line,BoundingBoxNotContainprop) is not None:
                                                propjoinedtotlotsetbacks.append(min(self.DistPropjoinedtotlot2marginanotherProp(totlot_polygon,margin_line,BoundingBoxNotContainprop)))

                                            if self.DistPropjoinedtotlot2marginanotherTotLot(totlot_polygon, margin_line,BoundingBoxNotContaintotlot) is not None:
                                                propjoinedtotlotsetbacks.append(min(self.DistPropjoinedtotlot2marginanotherTotLot(totlot_polygon, margin_line, BoundingBoxNotContaintotlot)))

                                            propjoinedtotlotsetbacks.append(totlot_polygon.distance(margin_line))

                                        if propjoinedtotlotsetbacks != [] and len(propjoinedtotlotsetbacks) > 0:
                                            SidesOFValue.append(min(propjoinedtotlotsetbacks))

                                    SidesOFValue.append(MergeMultiPolygons.distance(margin_line))

                                    # TouchesMargin = self.DirectionslabelWithmarginLines(proposedTouchLabels,margin_line)
                                    # DirectionOdSides.append(TouchesMargin)
                                # print(Margin_side,DirectionOdSides)

                                margin_line_merge = linemerge(Margin_lines)
                                TouchesMargin = self.DirectionslabelWithmarginLines(proposedTouchLabels,margin_line_merge)

                                sidesOfPolygonDict[str(Margin_side)+"_DIR"] =(str(TouchesMargin)).upper()

                                if SidesOFValue != [] and len(SidesOFValue) > 0:

                                    sidesOfPolygonDict[Margin_side] = str(round(min(SidesOFValue), 2))
                        else:

                            sidesOfPolygonDict = dict()

                            BoundingBoxNotContainprop = self.BounboxNotContainProp(MergeMultiPolygons,ProposedWorkLayerDict.values())

                            for Margin_side, Margin_lines in MarginLayerDict.items():

                                SidesOFValue = []

                                for margin_line in Margin_lines:

                                    if self.DistProp2marginanotherProp(MergeMultiPolygons, margin_line,BoundingBoxNotContainprop) is not None:
                                        SidesOFValue.append( min(self.DistProp2marginanotherProp(MergeMultiPolygons, margin_line, BoundingBoxNotContainprop)))

                                    SidesOFValue.append(MergeMultiPolygons.distance(margin_line))

                                margin_line_merge = linemerge(Margin_lines)
                                TouchesMargin = self.DirectionslabelWithmarginLines(proposedTouchLabels,margin_line_merge)

                                sidesOfPolygonDict[str(Margin_side)+"_DIR"] = (str(TouchesMargin)).upper()

                                if SidesOFValue != [] and len(SidesOFValue) > 0:
                                    sidesOfPolygonDict[Margin_side] = str(round(min(SidesOFValue), 2))

                        if sidesOfPolygonDict != {} and len(sidesOfPolygonDict) > 0:

                            sidesOfPolygonDict['NAME'] = ProposedWorkNamePoly[0]
                            sidesOfPolygonDict['BLDG_REF'] = Building_id

                            returnValueList.append(sidesOfPolygonDict)

        except IndexError:

            pass

        except AttributeError:

            pass

        except IOError:

            print(f'Not a DXF file or a generic I/O error.')

            return returnValueList

        except ezdxf.DXFStructureError:

            print(f'Invalid or corrupted DXF file.')

            return returnValueList

        return returnValueList


# # -----------------------------------Input of file-----------------------------------------------------
# # from ReadDWGFile import readDWG_File
# # path of the filename
# # folder = r'E:/production_code/dxf_files/Buildings'
# # Pass extension - removed inside method
# # filename = 'PREDCR Maram Sanction drawing - 12-04-2022_1_2.dxf'  # Here give only filename
# # folder=r'E:/production_code/dxf_files/Buildings'
# # Pass extension - removed inside method
# folder = "D:/ProductionCode & File/DXF_Files/Building_all_fils/building_dxf_file"
# filename = "2 blocks (1) (1).dxf"
#
#
# # filename = "2 cellar drg.dxf"
# from datetime import datetime
#
# start_time = datetime.now()
#
# t1 = start_time.strftime("%H:%M:%S")
#
# first_start_time = datetime.strptime(t1, "%H:%M:%S")
#
# dxf_file = ezdxf.readfile(os.path.join(folder, filename))
# print(f"FileName:- {filename}")
# msp = dxf_file.modelspace()
#
# response = CommomFloorSetbacks()
#
# print('Common Floor Setbacks  Response ', response.FloorSebacks(msp))
#
# end_time = datetime.now()
#
# t2 = end_time.strftime("%H:%M:%S")
#
# last_end_time = datetime.strptime(t2, "%H:%M:%S")
#
# total_time = last_end_time - first_start_time
#
# print(f'Total Time is:{total_time}')
