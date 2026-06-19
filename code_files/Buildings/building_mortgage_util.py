import ezdxf

from shapely.geometry import Point,Polygon

from convert_polygon_to_arc import polygon2arc


def get_building_mortgage_carpetarea(msp):

    returnValueDict=dict()

    if (msp is None):

        returnValueDict['code']=99

        msg='Required inputs of msp is missing for method get_building_mortgage_carpetarea. Modelspace ' + str(msp)

        returnValueDict['error']=msg

        return returnValueDict

    try:

        txtBldgList=msp.query('*[layer=="_BuildingName"]')

        lwpolyBldgList=msp.query('LWPOLYLINE[layer=="_BuildingName"]')

        txtFloorList=msp.query('*[layer=="_Floor"]')

        lwpolyFloorList=msp.query('LWPOLYLINE[layer=="_Floor"]')

        lwpolyMortgageList=msp.query('LWPOLYLINE[layer=="_MortgageArea"]')

        txtMortgageList=msp.query('*[layer=="_MortgageArea"]')

        txtCarpetAreaList=msp.query('*[layer=="_CarpetArea"]')

        lwpolyCarpetAreaList=msp.query('LWPOLYLINE[layer=="_CarpetArea"]')

        #Iterrating Buildinglayer text

        tot_list = []

        for building_text in txtBldgList:

            building_attribs=building_text.dxfattribs()

            if building_text.dxftype()=='TEXT' or building_text.dxftype()=='MTEXT':

                building_name=building_attribs.get('text') if building_text.dxftype()=='TEXT' else building_text.text

                building_text_insert=building_attribs.get('insert')

                building_text_pts=[building_text_insert[0],building_text_insert[1]]

                building_text_points=Point(building_text_pts)

                #Iterating Building layer Polygon

                for building_polygon in lwpolyBldgList:

                        building_polygon_pts=[bp[0:2] for bp in building_polygon.get_points()]

                        building_id=building_polygon.dxf.handle

                        building_polygon_points=Polygon(building_polygon_pts)

                        #check Building layer have text in polygon or not

                        if building_polygon_points.contains(building_text_points)==True or building_polygon_points.touches(building_text_points)==True:

                            build_list=[]
                            #iteratting Floor layer text

                            for floor_text in txtFloorList:

                                floor_text_attribs=floor_text.dxfattribs()

                                if floor_text.dxftype()=='TEXT' or floor_text.dxftype()=='MTEXT':

                                    floor_name=floor_text_attribs.get('text') if floor_text.dxftype()=='TEXT' else floor_text.text

                                    floor_insert_text=floor_text_attribs.get('insert')

                                    floor_text_pts=[floor_insert_text[0],floor_insert_text[1]]

                                    floor_text_point=Point(floor_text_pts)

                                    #iterating Floor layer polygon

                                    for floor_polygon in lwpolyFloorList:

                                        floor_polygon_pts=[fp[0:2] for fp in floor_polygon.get_points()]

                                        floor_id=floor_polygon.dxf.handle

                                        floor_polygon_points=Polygon(floor_polygon_pts)

                                        #check floor layer polygon have floor text or not

                                        if floor_polygon_points.contains(floor_text_point)==True or floor_polygon_points.touches(floor_text_point)==True :

                                            #check Building layer have floor layer or not

                                            if building_polygon_points.contains(floor_polygon_points)==True:
                                                #print(floor_name)
                                                floor_list = []
                                                #itterate Mortgage layer text

                                                for mortgage_text in txtMortgageList:

                                                    mortgage_text_attribs=mortgage_text.dxfattribs()

                                                    if mortgage_text.dxftype()=='TEXT' or mortgage_text.dxftype()=='MTEXT':

                                                        mortgage_name=mortgage_text_attribs.get('text') if mortgage_text.dxftype()=='TEXT' else mortgage_text.text

                                                        mortgage_insert_text=mortgage_text_attribs.get('insert')

                                                        mortgage_text_pts=[mortgage_insert_text[0],mortgage_insert_text[1]]

                                                        mortgage_text_point=Point(mortgage_text_pts)

                                                        #itterate MortgageArea layer polygon

                                                        for mortgage_polygon in lwpolyMortgageList:

                                                            #check mortgage polygon closed or not

                                                            if mortgage_polygon.closed==True:

                                                                if any([entity.dxftype()=="ARC" for entity in mortgage_polygon.virtual_entities()]):

                                                                    mortgage_polygon_points= polygon2arc.Polygon_Merger_ARC(mortgage_polygon)

                                                                else:
                                                                    mortgage_polygon_pts=[mp[0:2] for mp in mortgage_polygon.get_points()]

                                                                    mortgage_polygon_points=Polygon(mortgage_polygon_pts)

                                                                mortgage_polygon_area=round(mortgage_polygon_points.area,1)

                                                                # Mortgage polygon have labels or not

                                                                if (mortgage_polygon_points.contains(mortgage_text_point)==True):

                                                                    #floor layer have Mortgage polygon or not

                                                                    if floor_polygon_points.contains(mortgage_polygon_points)==True :

                                                                        # itterate CarpetArea layer text

                                                                        mortgage_list=[]

                                                                        for carpetarea_entity in txtCarpetAreaList:

                                                                            if carpetarea_entity.dxftype()=='TEXT' or carpetarea_entity.dxftype()=='MTEXT':

                                                                                carpetarea_attribs=carpetarea_entity.dxfattribs()

                                                                                text_name= carpetarea_attribs.get('text') if carpetarea_entity.dxftype()=='TEXT' else carpetarea_entity.plain_text()

                                                                                insert_carpetarea=carpetarea_attribs.get('insert')

                                                                                carpetarea_text_pts=[insert_carpetarea[0],insert_carpetarea[1]]

                                                                                carpetarea_text_points=Point(carpetarea_text_pts)

                                                                                #itterate the CarpetArea layer polygon

                                                                                for carpetarea_polygon in lwpolyCarpetAreaList:

                                                                                    carpetarea_polygon_pts=[cp[0:2] for cp in carpetarea_polygon.get_points()]

                                                                                    carpetarea_polygon_points=Polygon(carpetarea_polygon_pts)

                                                                                    #check carpetArea polygon have CarpetArea Text

                                                                                    if carpetarea_polygon_points.contains(carpetarea_text_points)==True:

                                                                                        #check MortgageArea have CarpetArea or not

                                                                                        if(mortgage_polygon_points.contains(carpetarea_polygon_points)==True) or (mortgage_polygon_points.intersects(carpetarea_polygon_points)==True) or (mortgage_polygon_points.touches(carpetarea_polygon_points)==True) or (round(mortgage_polygon_points.distance(carpetarea_polygon_points))==0):

                                                                                            carpeta_dict=dict()

                                                                                            carpeta_dict['BUILDING_NAME']=building_name

                                                                                            carpeta_dict['BUILDING_REFID']=building_id

                                                                                            carpeta_dict['FLOOR_REFID']=floor_id

                                                                                            carpeta_dict['FLOOR_NAME']=floor_name

                                                                                            carpeta_dict['MORTGAGED_CARPETAREA_REF']=text_name

                                                                                            carpeta_dict['MORTGAGED_NAME']=mortgage_name

                                                                                            carpeta_dict['MORTGAGED_AREA']=str(mortgage_polygon_area)

                                                                                            mortgage_list.append(carpeta_dict)
                                                                        if mortgage_list!=[]:

                                                                            for mortgage_data in mortgage_list:

                                                                                floor_list.append(mortgage_data)
                                                if floor_list!=[]:

                                                    for floor_data in floor_list:

                                                        build_list.append(floor_data)


                            if build_list!=[]:

                                tot_list.append(build_list)

        if tot_list != []:

            returnValueDict['code'] = 0

            tot_list_updated = [[{**bldg_data, 'BUILDING_COUNT': str(bld_count + 1)} for bldg_data in bld_data] for bld_count, bld_data in enumerate(tot_list)]

            returnValueDict['data'] = tot_list_updated[0]

    except IOError as ioe:
        msg=f'Not a DXF file or a generic I/O error.' + str(ioe)
        returnValueDict['code']=99
        returnValueDict['error']=msg

        return returnValueDict
    except ezdxf.DXFStructureError as dse :
        msg=f'Invalid or corrupted DXF file.'+ str(dse)
        returnValueDict['code']=99
        returnValueDict['error']=msg
        
        return returnValueDict
    
    return returnValueDict

# # ---------------------------------------------Input Of File----------------------------------
# import ezdxf
#
# read_dxf=ezdxf.readfile("E:/production_code/dxf_files/ba674a09750742-gatedCommunity_Elegance_Gundlapochampalli.dxf")
#
# msp=read_dxf.modelspace()
#
# print(get_building_mortgage_carpetarea(msp))