#-------------------------------------------- Loading Module-----------------------------
import os
import ezdxf
import numpy as np
from shapely.geometry import Polygon,Point#,MultiPolygon
from shapely.ops import unary_union
#import matplotlib.pyplot as plt
class check_For_layersOverlapping:

    def Passage_layer(self, Passage_Data):

        passage_dict = dict()

        for entity in Passage_Data:

            if entity.dxftype() == 'TEXT' or entity.dxftype() == 'MTEXT':

                passage_id = entity.dxf.handle

                passage_properties = entity.dxfattribs()

                passage_name = passage_properties.get('text') if entity.dxftype() == 'TEXT' else entity.plain_text()

                passage_text_pts = passage_properties.get('insert')

                passage_text_point = Point(np.array([passage_text_pts[0], passage_text_pts[1]]))

                for poly_entity in Passage_Data:

                    if poly_entity.dxftype() == 'LWPOLYLINE':

                        if len([pp[0:2] for pp in poly_entity.get_points()]) >= 4:

                            passage_polygon_points = Polygon(np.array([pp[0:2] for pp in poly_entity.get_points()]))

                            if passage_polygon_points.contains(passage_text_point) == True or passage_polygon_points.touches(passage_text_point) == True or round(passage_polygon_points.distance(passage_text_point),1) == 0.0:

                                passage_dict[passage_id] = [passage_name, passage_polygon_points]

        return passage_dict

    def Staircase_layer(self, StairCase_Data):

        StairCase_dict = dict()

        for entity in StairCase_Data:

            if entity.dxftype() == 'TEXT' or entity.dxftype() == 'MTEXT':

                staircase_id = entity.dxf.handle

                staircase_properties = entity.dxfattribs()

                staircase_name = staircase_properties.get('text') if entity.dxftype() == 'TEXT' else entity.plain_text()

                staircase_text_pts = staircase_properties.get('insert')

                staircase_text_point = Point(np.array([staircase_text_pts[0], staircase_text_pts[1]]))

                for poly_entity in StairCase_Data:

                    if poly_entity.dxftype() == 'LWPOLYLINE':

                        if len([pp[0:2] for pp in poly_entity.get_points()]) >= 4:

                            staircase_polygon_points = Polygon(np.array([sp[0:2] for sp in poly_entity.get_points()]))

                            if staircase_polygon_points.contains(staircase_text_point) == True or staircase_polygon_points.touches(staircase_text_point) == True or round(staircase_polygon_points.distance(staircase_text_point),1) == 0.0:

                                StairCase_dict[staircase_id] = [staircase_name, staircase_polygon_points]

        return StairCase_dict

    def Floor_layer(self, Floor_Data):

        floor_dict = dict()

        for entity in Floor_Data:

            if entity.dxftype() == 'TEXT' or entity.dxftype() == 'MTEXT':

                floor_id = entity.dxf.handle

                floor_properties = entity.dxfattribs()

                floor_name = floor_properties.get('text') if entity.dxftype() == 'TEXT' else entity.plain_text()

                floor_text_pts = floor_properties.get('insert')

                floor_text_point = Point(np.array([floor_text_pts[0], floor_text_pts[1]]))

                for poly_entity in Floor_Data:

                    if poly_entity.dxftype() == 'LWPOLYLINE':

                        if len([fp[0:2] for fp in poly_entity.get_points()])>3:

                            floor_polygon_points = Polygon(np.array([fp[0:2] for fp in poly_entity.get_points()]))

                            if floor_polygon_points.contains(floor_text_point) == True or floor_polygon_points.touches(floor_text_point) == True or round(floor_polygon_points.distance(floor_text_point), 1) == 0.0:

                                floor_dict[floor_id] = [floor_name, floor_polygon_points]

        return floor_dict

    def Balcony_layer(self,Balcony_Data):

        balcony_dict = dict()

        for entity in Balcony_Data:

            if entity.dxftype() == 'TEXT' or entity.dxftype() == 'MTEXT':

                balcony_id = entity.dxf.handle

                balcony_properties = entity.dxfattribs()

                balcony_name = balcony_properties.get('text') if entity.dxftype() == 'TEXT' else entity.plain_text()

                balcony_text_pts = balcony_properties.get('insert')

                balcony_text_point = Point(np.array([balcony_text_pts[0], balcony_text_pts[1]]))

                for poly_entity in Balcony_Data:

                    if poly_entity.dxftype() == 'LWPOLYLINE':

                        balcony_polygon_points = Polygon(np.array([cap[0:2] for cap in poly_entity.get_points()]))

                        if balcony_polygon_points.contains(balcony_text_point) == True or balcony_polygon_points.touches(balcony_text_point) == True or round(balcony_polygon_points.distance(balcony_text_point), 1) == 0.0:

                            balcony_dict[balcony_id] = [balcony_name, balcony_polygon_points]

        return balcony_dict
    def MortgageArea_layer(self,MortgageArea_Data):

        mortgagearea_dict = dict()

        for entity in MortgageArea_Data:

            if entity.dxftype() == 'TEXT' or entity.dxftype() == 'MTEXT':

                mortgagearea_id = entity.dxf.handle

                mortgagearea_properties = entity.dxfattribs()

                mortgagearea_name = mortgagearea_properties.get('text') if entity.dxftype() == 'TEXT' else entity.plain_text()

                mortgagearea_text_pts = mortgagearea_properties.get('insert')

                mortgagearea_text_point = Point(np.array([mortgagearea_text_pts[0], mortgagearea_text_pts[1]]))

                for poly_entity in MortgageArea_Data:

                    if poly_entity.dxftype() == 'LWPOLYLINE':

                        mortgagearea_polygon_points = Polygon(np.array([cap[0:2] for cap in poly_entity.get_points()]))

                        if mortgagearea_polygon_points.contains(mortgagearea_text_point) == True or mortgagearea_polygon_points.touches(mortgagearea_text_point) == True or round(mortgagearea_polygon_points.distance(mortgagearea_text_point), 1) == 0.0:

                            mortgagearea_dict[mortgagearea_id] = [mortgagearea_name, mortgagearea_polygon_points]

        return mortgagearea_dict

    def Lift_layer(self,Lift_Data):

        lift_dict = dict()

        for entity in Lift_Data:

            if entity.dxftype() == 'TEXT' or entity.dxftype() == 'MTEXT':

                lift_id = entity.dxf.handle

                lift_properties = entity.dxfattribs()

                lift_name = lift_properties.get('text') if entity.dxftype() == 'TEXT' else entity.plain_text()

                lift_text_pts = lift_properties.get('insert')

                mortgagearea_text_point = Point(np.array([lift_text_pts[0], lift_text_pts[1]]))

                for poly_entity in Lift_Data:

                    if poly_entity.dxftype() == 'LWPOLYLINE':

                        lift_polygon_points = Polygon(np.array([cap[0:2] for cap in poly_entity.get_points()]))

                        if lift_polygon_points.contains(mortgagearea_text_point) == True or lift_polygon_points.touches(mortgagearea_text_point) == True or round(lift_polygon_points.distance(mortgagearea_text_point), 1) == 0.0:

                            lift_dict[lift_id] = [lift_name, lift_polygon_points]

        return lift_dict
    def FloorContainsBUA(self,floor_polygon_points,ResiBUAOutline_Data,CommBUAOutline_Data):

        TotalBUA_INFLOOR=[]

        for resibua_polygon in ResiBUAOutline_Data:

            if len([rp[0:2] for rp in resibua_polygon.get_points()])>3:

                resibua_polygon_points = Polygon(np.array([rp[0:2] for rp in resibua_polygon.get_points()]))

                if floor_polygon_points.contains(resibua_polygon_points)==True or round(floor_polygon_points.distance(resibua_polygon_points),1)==0.0:

                    TotalBUA_INFLOOR.append(resibua_polygon_points)

        for commbua_polygon in CommBUAOutline_Data:

            if len([cp[0:2] for cp in commbua_polygon.get_points()]) > 3:

                commbua_polygon_points = Polygon(np.array([cp[0:2] for cp in commbua_polygon.get_points()]))

                if floor_polygon_points.contains(commbua_polygon_points) == True or round(floor_polygon_points.distance(commbua_polygon_points), 1) == 0.0:

                    TotalBUA_INFLOOR.append(commbua_polygon_points)

        return TotalBUA_INFLOOR
    def ResiBUAOutline_layer(self, ResiBUAOutline_Data):

        resibua_dict = dict()

        for resibua_polygon in ResiBUAOutline_Data:

            resibua_poly_id = resibua_polygon.dxf.handle

            if len([rp[0:2] for rp in resibua_polygon.get_points()])>3:

                resibua_polygon_points = Polygon(np.array([rp[0:2] for rp in resibua_polygon.get_points()]))

                resibua_dict[resibua_poly_id] = resibua_polygon_points

        return resibua_dict
    def CommBUAOutline_layer(self,CommBUAOutline_Data):

        commbua_dict=dict()

        for commbua_polygon in CommBUAOutline_Data:

            commbua_poly_id=commbua_polygon.dxf.handle

            commbua_polygon_points=Polygon(np.array([cp[0:2] for cp in commbua_polygon.get_points()]))

            commbua_dict[commbua_poly_id]=commbua_polygon_points

        return commbua_dict

    def checkDeviations(self,msp):

        failedChecks=[]

        try:

            print('DXF File reading')

            balcony_data = msp.query('*[layer=="_Balcony"]')

            floor_data=msp.query('*[layer=="_Floor"]')

            passage_data=msp.query('*[layer=="_Passage"]')

            resibuaOutline_data= msp.query('LWPOLYLINE[layer=="_ResiBUAOutline"]')

            commBUAOutline_data=msp.query('LWPOLYLINE[layer=="_CommBUAOutline"]')

            MortgageArea_data = msp.query('*[layer=="_MortgageArea"]')

            Lift_data=msp.query('*[layer=="_Lift"]')

            Staircase_data=msp.query('*[layer=="_Staircase"]')

            floor_LayerDict=self.Floor_layer(floor_data)

            staircase_LayerDict= self.Staircase_layer(Staircase_data)

            lift_LayerDict= self.Lift_layer(Lift_data)

            balcony_LayerDict=self.Balcony_layer(balcony_data)

            mortgage_LayerDict=self.MortgageArea_layer(MortgageArea_data)

            passage_LayerDict=self.Passage_layer(passage_data)

            commBUA_LayerDict=self.CommBUAOutline_layer(commBUAOutline_data)

            #loop for floor_layer floor_poly[0]---->floor label,floor_poly[1]---->floor polygon

            for floor_poly in floor_LayerDict.values():

                # check for Resibua,CommBua in floor polygon

                if len(self.FloorContainsBUA(floor_poly[1],resibuaOutline_data,commBUAOutline_data))>0 and len(self.FloorContainsBUA(floor_poly[1],resibuaOutline_data,commBUAOutline_data))<=1:

                    # loop for ResiBuaOutline

                    for resibua_poly in self.ResiBUAOutline_layer(resibuaOutline_data).values():

                        #check if resibua in floor layer

                        if floor_poly[1].contains(resibua_poly)==True or round(floor_poly[1].distance(resibua_poly),1)==0.0:

                            #--------------------Staicase-------------------

                            FloorContainStaircase = []

                            #loop for StairCase Layer staircase_namepoly[0]--->staircase label,staircase_namepoly[1]----> staircase polygon

                            for staircase_namepoly in staircase_LayerDict.values():

                                # if staircase in resibua layer

                                if resibua_poly.contains(staircase_namepoly[1]) == True or resibua_poly.touches(staircase_namepoly[1]) == True or round(resibua_poly.distance(staircase_namepoly[1]),1) == 0.0 or floor_poly[1].contains(staircase_namepoly[1]) == True:

                                    FloorContainStaircase.append(staircase_namepoly[1])

                            # --------------------Lift-------------------

                            FloorContainLift=[]

                            #loop for lift layer lift_namepoly[0]--->lift label,lift_namepoly[1]--->lift polygon

                            for lift_namepoly in lift_LayerDict.values():

                                # if lift in resibua layer

                                if resibua_poly.contains(lift_namepoly[1]) == True or resibua_poly.touches(lift_namepoly[1]) == True or round(resibua_poly.distance(lift_namepoly[1]),1) ==0.0 or floor_poly[1].contains(lift_namepoly[1])==True:

                                    FloorContainLift.append(lift_namepoly[1])

                            # --------------------Balcony-------------------

                            tot_balconypoly_attched2resi=[]

                            # loop for Balcony layer balcony_namepoly[0]---> balcony label,balcony_namepoly[1]---> balcony polygon

                            for balcony_namepoly in balcony_LayerDict.values():

                                # if balcony in resibua layer

                                if resibua_poly.contains(balcony_namepoly[1]) == True or resibua_poly.touches(balcony_namepoly[1]) == True or round(resibua_poly.distance(balcony_namepoly[1]),1) ==0.0 or floor_poly[1].contains(balcony_namepoly[1])==True:

                                    tot_balconypoly_attched2resi.append(balcony_namepoly[1])

                            #loop for MortgageArea Layer in mortgage_namepoly[0]--> mortgage label,,mortgage_namepoly[1]--> mortgage polygon

                            for mortgage_namepoly in mortgage_LayerDict.values():

                                #if MortgageArea in Floor layer

                                if floor_poly[1].contains(mortgage_namepoly[1])==True:

                                    #----------------------------------------check Staircase,lift in Mortgage Area or not for resibua---------------------------

                                    #----------------------------StairCase in Mortgage Area--------------------

                                    MortgageContainsStaircase = []

                                    #loop for list of staircase in floor layer

                                    for staircase in FloorContainStaircase:

                                        MortgageContainsStaircasePolygonpts = []

                                        # loop for single point staircase from staircase polygon.

                                        for stairx,stairy in zip(staircase.exterior.xy[0],staircase.exterior.xy[1]):

                                            staircase_point=Point(stairx,stairy)

                                            #check if staircase point in MortgageArea then False otherwise True

                                            if mortgage_namepoly[1].contains(staircase_point)==True:

                                                MortgageContainsStaircasePolygonpts.append(False)

                                            else:

                                                MortgageContainsStaircasePolygonpts.append(True)

                                        MortgageContainsStaircase.append(all(MortgageContainsStaircasePolygonpts))

                                    #check any Staircase in Mortgage Area

                                    if all(MortgageContainsStaircase)==False:

                                        errorMsg=f'Failed-MortgageArea Contains ({MortgageContainsStaircase.count(False)}) Staircase in  {floor_poly[0]}'

                                        failedChecks.append(errorMsg)

                                        print(errorMsg)

                                    # ----------------------------Lift in Mortgage Area--------------------

                                    MortgageContainsLift=[]

                                    # loop for list of lift in floor layer

                                    for lift in FloorContainLift:

                                        MortgageContainsLiftpts=[]

                                        # loop for single point lift from lift polygon.

                                        for liftx,lifty in zip(lift.exterior.xy[0],lift.exterior.xy[1]):

                                            lift_point=Point(liftx,lifty)

                                            # check if lift point in MortgageArea then False otherwise True

                                            if mortgage_namepoly[1].contains(lift_point)==True:

                                                MortgageContainsLiftpts.append(False)

                                            else:

                                                MortgageContainsLiftpts.append(True)

                                        MortgageContainsLift.append(all(MortgageContainsLiftpts))

                                    # check any lift in Mortgage Area

                                    if all(MortgageContainsLift)==False:

                                        errorMsg=f'Failed-MortgageArea Contains ({MortgageContainsLift.count(False)}) lift in  {floor_poly[0]}'

                                        failedChecks.append(errorMsg)

                                        print(errorMsg)
                                        
                                    #----------Check MortgageArea Comming outside of Resibua or Not----------------

                                    contains_mortgage_pts_in_mergePolygon = []

                                    #loop for Mortgage single point for MortgageArea Polygon

                                    for x_point,y_point in zip(mortgage_namepoly[1].exterior.xy[0],mortgage_namepoly[1].exterior.xy[1]):

                                        mortgage_point=Point(x_point,y_point)

                                        #check if Mortgage Area Point in resibua Polygon if True otherwise false another check for balcony

                                        if resibua_poly.contains(mortgage_point)==True or resibua_poly.touches(mortgage_point)==True or round(resibua_poly.distance(mortgage_point),1)==0.0:

                                            contains_mortgage_pts_in_mergePolygon.append(True)

                                        else:

                                            mortgagePointContainsInBalcony=[]

                                            # if False then loop for balcony layer

                                            for balcony_p in tot_balconypoly_attched2resi:

                                                #check mortgage point in balcony the true otherwise False

                                                if balcony_p.contains(mortgage_point)==True or balcony_p.touches(mortgage_point)==True or round(balcony_p.distance(mortgage_point))==0:

                                                    mortgagePointContainsInBalcony.append(True)

                                                else:

                                                    mortgagePointContainsInBalcony.append(False)

                                            contains_mortgage_pts_in_mergePolygon.append(any(mortgagePointContainsInBalcony))

                                    #check Mortgage Area point coming outside of resibua layer

                                    if all(contains_mortgage_pts_in_mergePolygon)==False:

                                        errorMsg=f'Failed-MortgageArea For ResiBUAOutline in {floor_poly[0]}'

                                        failedChecks.append(errorMsg)

                                        print(errorMsg)

                            #----------------- Check Passage Comming Outside of resibua layer ---------------------------

                            #loop for passage layer passage floor_poly[0]-->passage label,floor_poly[1]-->passage polygon

                            for passage_namepoly in passage_LayerDict.values():

                                #check passage in floor layer

                                if floor_poly[1].contains(passage_namepoly[1]) == True:

                                    passageContainMortgagePolygon=[]

                                    #----------------------------------MortgageArea On Passage layer for Resibua------------------------------

                                    #loop for Mortgage layer mortgage_namepoly[0]--->MortgageArea Label,mortgage_namepoly[1]--->MortgageArea Polygon

                                    for mortgage_namepoly in self.MortgageArea_layer(MortgageArea_data).values():

                                        # check if Mortgage in floor layer

                                        if floor_poly[1].contains(mortgage_namepoly[1]) == True or round(floor_poly[1].distance(mortgage_namepoly[1]),1) == 0.0:

                                            PassageContainMortgagepts=[]

                                            # loop for mortgage point from MortgageArea Polygon

                                            for mortgage_x,mortgage_y in zip(mortgage_namepoly[1].exterior.xy[0],mortgage_namepoly[1].exterior.xy[1]):

                                                mortgage_point=Point(mortgage_x,mortgage_y)

                                                # MortgageArea Point in passage_namepoly if True then False otherwise True

                                                if passage_namepoly[1].contains(mortgage_point)==True:

                                                    PassageContainMortgagepts.append(False)

                                                else:

                                                    PassageContainMortgagepts.append(True)

                                            passageContainMortgagePolygon.append(all(PassageContainMortgagepts))

                                    #check if Mortgage Area on Passage layer

                                    if all(passageContainMortgagePolygon)==False:

                                        errorMsg = f'Failed:Passage Contain ({passageContainMortgagePolygon.count(False)}) MortgageArea in {floor_poly[0]}'
                                        failedChecks.append(errorMsg)
                                        print(errorMsg)

                                    #-------------------------------------------Passage comming Ouside for Resibua------------------------------------

                                    contains_Passage_pts_in_resiPolygon = []

                                    #loop for passage single point from passage polygon

                                    for x_point, y_point in zip(passage_namepoly[1].exterior.xy[0],passage_namepoly[1].exterior.xy[1]):

                                        passage_point = Point(x_point, y_point)

                                        # passage point in resibua layer then True otherwise False

                                        if resibua_poly.contains(passage_point) == True or resibua_poly.touches(passage_point) == True or round(resibua_poly.distance(passage_point),1) == 0.0:

                                            contains_Passage_pts_in_resiPolygon.append(True)

                                        else:

                                            contains_Passage_pts_in_resiPolygon.append(False)

                                    #check if passage comming outside of resibua layer

                                    if all(contains_Passage_pts_in_resiPolygon) == False:

                                        errorMsg=f'Failed-Passage For ResiBUAOutline in {floor_poly[0]}'
                                        failedChecks.append(errorMsg)
                                        print(errorMsg)

                    #loop for CommBuaOutline

                    for commbua_poly in commBUA_LayerDict.values():

                        # check if resibua in floor layer

                        if floor_poly[1].contains(commbua_poly) == True or round(floor_poly[1].distance(commbua_poly),1) == 0.0:

                            # --------------------Staicase-------------------

                            tot_StaircaseINCommAndFloor=[]

                            # loop for StairCase Layer staircase_namepoly[0]--->staircase label,staircase_namepoly[1]----> staircase polygon

                            for staircase_namepoly in staircase_LayerDict.values():

                                # if staircase in commbua layer

                                if commbua_poly.touches(staircase_namepoly[1]) == True or round(commbua_poly.distance(staircase_namepoly[1]), 1) == 0.0:

                                    tot_StaircaseINCommAndFloor.append(staircase_namepoly[1])

                            # --------------------Lift-------------------

                            tot_liftInCommAndResiFloor=[]

                            # loop for lift layer lift_namepoly[0]--->lift label,lift_namepoly[1]--->lift polygon

                            for lift_namepoly in lift_LayerDict.values():

                                # if lift in commbua layer

                                if commbua_poly.touches(lift_namepoly[1]) == True or round(commbua_poly.distance(lift_namepoly[1]), 1) == 0.0:

                                    tot_liftInCommAndResiFloor.append(lift_namepoly[1])

                            # --------------------Balcony-------------------

                            tot_balconypoly_attched2resi = []

                            # loop for Balcony layer balcony_namepoly[0]---> balcony label,balcony_namepoly[1]---> balcony polygon

                            for balcony_namepoly in balcony_LayerDict.values():

                                # if balcony in commbua layer

                                if commbua_poly.touches(balcony_namepoly[1]) == True or round(commbua_poly.distance(balcony_namepoly[1]), 1) == 0.0:

                                    tot_balconypoly_attched2resi.append(balcony_namepoly[1])

                            # loop for MortgageArea Layer in mortgage_namepoly[0]--> mortgage label,,mortgage_namepoly[1]--> mortgage polygon

                            for mortgage_namepoly in mortgage_LayerDict.values():

                                # if MortgageArea in Floor layer

                                if floor_poly[1].contains(mortgage_namepoly[1])==True:

                                    # ----------------------------------------check Staircase,lift in Mortgage Area or not for Commbua---------------------------

                                    # ----------------------------StairCase in Mortgage Area--------------------

                                    StaircaseContainsMortgageArea=[]

                                    # loop for list of staircase in floor layer

                                    for staircase in tot_StaircaseINCommAndFloor:

                                       StaircaseptsContainsMortgageArea=[]

                                       # loop for single point staircase from staircase polygon.

                                       for stair_x,stair_y in zip(staircase.exterior.xy[0],staircase.exterior.xy[1]):

                                           stair_point=Point(stair_x,stair_y)

                                           # check if staircase point in MortgageArea then False otherwise True

                                           if mortgage_namepoly[1].contains(stair_point)==True:

                                                StaircaseptsContainsMortgageArea.append(False)

                                           else:


                                               StaircaseptsContainsMortgageArea.append(True)

                                       StaircaseContainsMortgageArea.append(all(StaircaseptsContainsMortgageArea))

                                    # check any Staircase in Mortgage Area

                                    if all(StaircaseContainsMortgageArea)==False:

                                        errorMsg=f'Failed-MortgageArea Contains ({StaircaseContainsMortgageArea.count(False)}) Staircase in {floor_poly[0]}'
                                        failedChecks.append(errorMsg)
                                        print(errorMsg)

                                    # ----------------------------Lift in Mortgage Area--------------------

                                    lift_ContainsMortgageArea=[]

                                    # loop for list of lift in floor layer

                                    for lift in tot_liftInCommAndResiFloor:

                                       liftpts_ContainsMortgageArea=[]

                                       # loop for single point lift from lift polygon.

                                       for liftx,lifty in zip(lift.exterior.xy[0],lift.exterior.xy[1]):

                                            lift_point=Point(liftx,lifty)

                                            # check if lift point in MortgageArea then False otherwise True

                                            if mortgage_namepoly[1].contains(lift_point)==True:

                                                liftpts_ContainsMortgageArea.append(False)

                                            else:

                                                liftpts_ContainsMortgageArea.append(True)

                                       lift_ContainsMortgageArea.append(all(liftpts_ContainsMortgageArea))

                                    # check any Staircase in Mortgage Area

                                    if all(lift_ContainsMortgageArea)==False:

                                        errorMsg=f'Failed-MortgageArea Contains ({lift_ContainsMortgageArea.count(False)}) lift in {floor_poly[0]}'
                                        failedChecks.append(errorMsg)
                                        print(errorMsg)

                                    contains_mortgage_pts_in_commbuaPolygon=[]

                                    for x_point,y_point in zip(mortgage_namepoly[1].exterior.xy[0],mortgage_namepoly[1].exterior.xy[1]):

                                        mortgage_point=Point(x_point,y_point)

                                        if commbua_poly.contains(mortgage_point)==True or commbua_poly.touches(mortgage_point)==True or round(commbua_poly.distance(mortgage_point),1)==0.0:

                                            contains_mortgage_pts_in_commbuaPolygon.append(True)

                                        else:

                                            mortgagePointContainsInBalcony=[]

                                            for balcony_p in tot_balconypoly_attched2resi:

                                                if balcony_p.contains(mortgage_point)==True or balcony_p.touches(mortgage_point)==True or round(balcony_p.distance(mortgage_point))==0:

                                                    mortgagePointContainsInBalcony.append(True)

                                                else:

                                                    mortgagePointContainsInBalcony.append(False)

                                            if mortgagePointContainsInBalcony!=[]:

                                                contains_mortgage_pts_in_commbuaPolygon.append(any(mortgagePointContainsInBalcony))

                                    if all(contains_mortgage_pts_in_commbuaPolygon)==False:

                                        errorMsg=f'Failed-MortgageArea For CommBUAOutline in {floor_poly[0]}'
                                        failedChecks.append(errorMsg)
                                        print(errorMsg)

                            # ----------------- Check Passage Comming Outside of commbua layer ---------------------------

                            # loop for passage layer passage floor_poly[0]-->passage label,floor_poly[1]-->passage polygon

                            for passage_namepoly in passage_LayerDict.values():

                                # check passage in floor layer

                                if floor_poly[1].contains(passage_namepoly[1]) == True:

                                    # ----------------------------------MortgageArea On Passage layer for Commbua------------------------------

                                    passageContainMortgagePolygon=[]

                                    # loop for Mortgage layer mortgage_namepoly[0]--->MortgageArea Label,mortgage_namepoly[1]--->MortgageArea Polygon

                                    for mortgage_namepoly in self.MortgageArea_layer(MortgageArea_data).values():

                                        # check if Mortgage in floor layer

                                        if floor_poly[1].contains(mortgage_namepoly[1]) == True or round(floor_poly[1].distance(mortgage_namepoly[1]), 1) == 0.0:

                                            PassageContainMortgagepts = []

                                            # loop for mortgage point from MortgageArea Polygon

                                            for mortgage_x, mortgage_y in zip(mortgage_namepoly[1].exterior.xy[0],mortgage_namepoly[1].exterior.xy[1]):

                                                mortgage_point = Point(mortgage_x, mortgage_y)

                                                # MortgageArea Point in passage_namepoly if True then False otherwise True

                                                if passage_namepoly[1].contains(mortgage_point) == True:

                                                    PassageContainMortgagepts.append(False)
                                                else:

                                                    PassageContainMortgagepts.append(True)

                                            passageContainMortgagePolygon.append(all(PassageContainMortgagepts))

                                    # check if Mortgage Area on Passage layer

                                    if all(passageContainMortgagePolygon) == False:

                                        errorMsg =f'Failed:Passage Contain ({passageContainMortgagePolygon.count(False)}) MortgageArea in {floor_poly[0]}'
                                        failedChecks.append(errorMsg)
                                        print(errorMsg)
                                    # ---------------------------------- Passage layer Comming Ouside of CommBua------------------------------

                                    commPolyContainPassagePTS = []

                                    # loop for passage single point from passage polygon

                                    for x_point, y_point in zip(passage_namepoly[1].exterior.xy[0],passage_namepoly[1].exterior.xy[1]):

                                        comm_passagePoint = Point(x_point, y_point)

                                        # passage point in commbua layer then True otherwise False

                                        if commbua_poly.contains(comm_passagePoint) == True or commbua_poly.touches(comm_passagePoint) == True or round(commbua_poly.distance(comm_passagePoint), 1) == 0.0:

                                            commPolyContainPassagePTS.append(True)

                                        else:

                                            commPolyContainPassagePTS.append(False)

                                    # check if passage comming outside of commbua layer

                                    if all(commPolyContainPassagePTS) == False:

                                        errorMsg=f'Failed-Passage For CommBUAOutline in {floor_poly[0]}'
                                        failedChecks.append(errorMsg)
                                        print(errorMsg)

                # check for both Resibua and CommBua in floor polygon

                elif(len(self.FloorContainsBUA(floor_poly[1],resibuaOutline_data,commBUAOutline_data))>1):

                    #merging resibua and CommBUA Polygon

                    mergeCommANDResibua_polygon = unary_union(self.FloorContainsBUA(floor_poly[1],resibuaOutline_data,commBUAOutline_data))

                    #if merged then polygon then geometric type Polygon otherwise Geometry type MultiPolygon and its not merged,because its not joint properly

                    if mergeCommANDResibua_polygon.geom_type =='Polygon':

                        #check if merged polygon in floor

                        if floor_poly[1].contains(mergeCommANDResibua_polygon)==True or round(floor_poly[1].distance(mergeCommANDResibua_polygon),1)==0.0:

                            #------------------Staircase------------------------

                            tot_StaircaseContainsbothbuaAndfloor = []

                            #loop for staircase layer staircase_namepoly[0]-->staircase label,staircase_namepoly[1]-->staircase polygon

                            for staircase_namepoly in staircase_LayerDict.values():

                                #if staircase in merged Polygon

                                if mergeCommANDResibua_polygon.contains(staircase_namepoly[1]) == True or mergeCommANDResibua_polygon.touches(staircase_namepoly[1]) == True or round(mergeCommANDResibua_polygon.distance(staircase_namepoly[1])) == 0 or floor_poly[1].contains(staircase_namepoly[1]) == True:

                                    tot_StaircaseContainsbothbuaAndfloor.append(staircase_namepoly[1])

                            # ------------------Lift------------------------

                            tot_liftContainsbothbuaAndfloor=[]

                            # loop for lift layer lift_namepoly[0]-->lift label,lift_namepoly[1]-->lift polygon

                            for lift_namepoly in lift_LayerDict.values():

                                # if lift in merged Polygon

                                if mergeCommANDResibua_polygon.contains(lift_namepoly[1]) == True or mergeCommANDResibua_polygon.touches(lift_namepoly[1]) == True or round(mergeCommANDResibua_polygon.distance(lift_namepoly[1])) == 0 or floor_poly[1].contains(lift_namepoly[1]) == True:

                                    tot_liftContainsbothbuaAndfloor.append(lift_namepoly[1])

                            # ------------------Balcony------------------------

                            tot_balconypoly_attched2bothbua=[]

                            # loop for balcony layer balcony_namepoly[0]-->balcony label,balcony_namepoly[1]-->balcony polygon

                            for balcony_namepoly in balcony_LayerDict.values():

                                # if balcony in merged Polygon

                                if mergeCommANDResibua_polygon.contains(balcony_namepoly[1]) == True or mergeCommANDResibua_polygon.touches(balcony_namepoly[1]) == True or round(mergeCommANDResibua_polygon.distance(balcony_namepoly[1])) == 0 or floor_poly[1].contains(balcony_namepoly[1]) == True:

                                    tot_balconypoly_attched2bothbua.append(balcony_namepoly[1])

                            # loop for MortgageArea Layer in mortgage_namepoly[0]--> mortgage label,,mortgage_namepoly[1]--> mortgage polygon

                            for mortgage_namepoly in mortgage_LayerDict.values():

                                #check if mortgage layer in floor layer

                                if floor_poly[1].contains(mortgage_namepoly[1]) == True:

                                    #---------------------------------Staircase In Mortgage Area--------------------------------

                                    MortgageContainsStaircase = []

                                    #loop for list of staircases in floor

                                    for staircase in tot_StaircaseContainsbothbuaAndfloor:

                                        MortgageContainsStaircasepts=[]

                                        #loop for staircase single point from staircase polygon

                                        for stair_x,stair_y in zip(staircase.exterior.xy[0],staircase.exterior.xy[1]):

                                            stair_point=Point(stair_x,stair_y)

                                            # check if staircase point in MortgageArea layer

                                            if mortgage_namepoly[1].contains(stair_point)==True:

                                                MortgageContainsStaircasepts.append(False)

                                            else:

                                                MortgageContainsStaircasepts.append(True)


                                        MortgageContainsStaircase.append(all(MortgageContainsStaircasepts))

                                    #check  if Staircase in MortgageArea

                                    if all(MortgageContainsStaircase)==False:

                                        errorMSg=f'Failed-MortgageArea Contains ({MortgageContainsStaircase.count(False)}) Staircase in {floor_poly[0]}'
                                        failedChecks.append(errorMSg)
                                        print(errorMSg)
                                    # ---------------------------------Lift In Mortgage Area--------------------------------

                                    MortgageContainslift = []

                                    # loop for list of lift in floor

                                    for lift in tot_liftContainsbothbuaAndfloor:

                                        MortgageContainslift=[]

                                        # loop for lift single point from lift polygon

                                        for lift_x,lift_y in zip(lift.exterior.xy[0],lift.exterior.xy[1]):

                                            lift_point=Point(lift_x,lift_y)

                                            # check if lift point in MortgageArea layer

                                            if mortgage_namepoly[1].contains(lift_point)==True:

                                                MortgageContainslift.append(False)

                                            else:

                                                MortgageContainslift.append(True)

                                        MortgageContainslift.append(all(MortgageContainslift))

                                    # check  if Lift in MortgageArea

                                    if all(MortgageContainslift)==False:

                                        errorMsg=f'Failed-MortgageArea Contains ({MortgageContainslift.count(False)}) Lift in {floor_poly[0]}'
                                        failedChecks.append(errorMsg)
                                        print(errorMsg)

                                    contains_mortgage_pts_in_commANDresiPolygon = []

                                    for x_point, y_point in zip(mortgage_namepoly[1].exterior.xy[0],mortgage_namepoly[1].exterior.xy[1]):

                                        mortgage_point = Point(x_point, y_point)

                                        if mergeCommANDResibua_polygon.contains(mortgage_point) == True or mergeCommANDResibua_polygon.touches(mortgage_point) == True or round(mergeCommANDResibua_polygon.distance(mortgage_point)) == 0:

                                            contains_mortgage_pts_in_commANDresiPolygon.append(True)

                                        else:

                                            mortgagePointContainsInBalcony = []

                                            for balcony_p in tot_balconypoly_attched2bothbua:

                                                if balcony_p.contains(mortgage_point) == True or balcony_p.touches(mortgage_point) == True or round(balcony_p.distance(mortgage_point)) == 0:

                                                    mortgagePointContainsInBalcony.append(True)

                                                else:

                                                    mortgagePointContainsInBalcony.append(False)

                                            if mortgagePointContainsInBalcony != []:

                                                contains_mortgage_pts_in_commANDresiPolygon.append(any(mortgagePointContainsInBalcony))

                                    if all(contains_mortgage_pts_in_commANDresiPolygon) == False:

                                        errorMsg=f'Failed-MortgageArea For CommBUA and ResiBUA in {floor_poly[0]}'
                                        failedChecks.append(errorMsg)
                                        print(errorMsg)

                            # loop for Passage Layer in passage_namepoly[0]--> passage label,passage_namepoly[1]--> passage polygon

                            for passage_namepoly in passage_LayerDict.values():

                                # check if passage in floor layer

                                if floor_poly[1].contains(passage_namepoly[1]) == True:

                                    # ----------------------------------MortgageArea On Passage layer for Commbua------------------------------

                                    passageContainMortgagePolygon = []

                                    # loop for Mortgage layer mortgage_namepoly[0]--->MortgageArea Label,mortgage_namepoly[1]--->MortgageArea Polygon

                                    for mortgage_namepoly in self.MortgageArea_layer(MortgageArea_data).values():

                                        # check if Mortgage in floor layer

                                        if floor_poly[1].contains(mortgage_namepoly[1]) == True or round(floor_poly[1].distance(mortgage_namepoly[1]), 1) == 0.0:

                                            PassageContainMortgagepts = []

                                            # loop for mortgage point from MortgageArea Polygon

                                            for mortgage_x, mortgage_y in zip(mortgage_namepoly[1].exterior.xy[0],mortgage_namepoly[1].exterior.xy[1]):

                                                mortgage_point = Point(mortgage_x, mortgage_y)

                                                # MortgageArea Point in passage_namepoly if True then False otherwise True

                                                if passage_namepoly[1].contains(mortgage_point) == True:

                                                    PassageContainMortgagepts.append(False)
                                                else:

                                                    PassageContainMortgagepts.append(True)

                                            passageContainMortgagePolygon.append(all(PassageContainMortgagepts))

                                    # check if Mortgage Area on Passage layer

                                    if all(passageContainMortgagePolygon) == False:

                                        errorMsg = f'Failed:Passage Contain ({passageContainMortgagePolygon.count(False)}) MortgageArea in {floor_poly[0]}'
                                        failedChecks.append(errorMsg)
                                        print(errorMsg)

                                    # ---------------------------------- Passage layer Comming Ouside of BothBUA------------------------------

                                    contains_passage_pts_in_mergePolygon = []

                                    # loop for passage single point from passage polygon

                                    for x_point, y_point in zip(passage_namepoly[1].exterior.xy[0],passage_namepoly[1].exterior.xy[1]):

                                        passage_point = Point(x_point, y_point)

                                        #check if passage point in merged polygon then true other wise false

                                        if mergeCommANDResibua_polygon.contains(passage_point) == True or mergeCommANDResibua_polygon.touches(passage_point) == True or round(mergeCommANDResibua_polygon.distance(passage_point), 1) == 0.0:

                                            contains_passage_pts_in_mergePolygon.append(True)

                                        else:

                                            contains_passage_pts_in_mergePolygon.append(False)

                                    #check if passage comming ouside merged polygon

                                    if all(contains_passage_pts_in_mergePolygon) == False:

                                        errorMsg=f'Failed-Passage For Both Resi and Comm BUA in {floor_poly[0]}'
                                        failedChecks.append(errorMsg)
                                        print(errorMsg)
                    else:

                        print(f'ResibuaOutline and CommbuaOutline Does not Joined in this {floor_poly[0]}')

        except IOError:

            print(f'Not a DXF file or a generic I/O error.')

        except ezdxf.DXFStructureError:

            print(f'Invalid or corrupted DXF file.')

        finally:

            print('process complete Successfully')
            return failedChecks

#----------------------File Input Data------------------------------

# folder='E:/production_code/dxf_files'

# filename='GOLDEN HOMES PREDCR.dxf'

# read_dxf=ezdxf.readfile(os.path.join(folder,filename))

# msp=read_dxf.modelspace()

# response=check_For_layersOverlapping()

# print(response.checkDeviations(msp))