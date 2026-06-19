import ezdxf
from shapely.geometry import Point, Polygon
from convert_polygon_to_arc import polygon2arc


class DXF_File_Data :


    def __init__(self):
        pass
    def plot_layer_entity(self,_Plot):

        plot_dict = dict()
        for plot_lw_entity in _Plot:
            if plot_lw_entity.dxftype() == "LWPOLYLINE" and plot_lw_entity.closed:

                check_plotarc=any([entity.dxftype()=="ARC" for entity in plot_lw_entity.virtual_entities()])

                plot_lw_ploy = polygon2arc(plot_lw_entity) if check_plotarc else Polygon(plot_lw_entity.get_points("xy"))

                plot_list = []

                for plot_text_entity in _Plot:
                    if plot_text_entity.dxftype() == "MTEXT" or plot_text_entity.dxftype() == "TEXT":
                        plot_text = plot_text_entity.dxf.text if plot_text_entity.dxftype() == "TEXT" else plot_text_entity.plain_text()
                        plot_id = plot_text_entity.dxf.handle
                        plot_points = (plot_text_entity.dxf.insert.x, plot_text_entity.dxf.insert.y)
                        plot_text_points = Point(plot_points)

                        if plot_lw_ploy.contains(plot_text_points) == True or plot_lw_ploy.touches(plot_text_points) == True or round(plot_lw_ploy.distance(plot_text_points),1) == 0.0 :
                            plot_list.append([plot_id,plot_text,plot_lw_ploy])

                if plot_list != []  or plot_list is None :
                    for plot_data in plot_list:
                        plot_dict[plot_data[0]] = plot_data[1:]

        return plot_dict
    #
    def _BufferZone_layer_entity(self,_BufferZone):

        buffer_zone_dict = dict()
        for buffer_zone_lw_entity in _BufferZone:

            if buffer_zone_lw_entity.dxftype() == "LWPOLYLINE" and buffer_zone_lw_entity.closed:

                check_bufferarc = any([entity.dxftype() == "ARC" for entity in buffer_zone_lw_entity.virtual_entities()])

                buffer_zone_lw_ploy = polygon2arc(buffer_zone_lw_entity) if check_bufferarc else Polygon(
                    buffer_zone_lw_entity.get_points("xy"))

                buffer_zone_list = []

                for buffer_zone_text_entity in _BufferZone:
                    if buffer_zone_text_entity.dxftype() == "MTEXT" or buffer_zone_text_entity.dxftype() == "TEXT":
                        buffer_zone_text = buffer_zone_text_entity.dxf.text if buffer_zone_text_entity.dxftype() == "TEXT" else buffer_zone_text_entity.plain_text()
                        buffer_zone_id = buffer_zone_text_entity.dxf.handle
                        buffer_zone_points = (
                        buffer_zone_text_entity.dxf.insert.x, buffer_zone_text_entity.dxf.insert.y)
                        buffer_zone_text_points = Point(buffer_zone_points)

                        if buffer_zone_lw_ploy.contains(
                                buffer_zone_text_points) == True or buffer_zone_lw_ploy.touches(
                                buffer_zone_text_points) == True or round(
                            buffer_zone_lw_ploy.distance(buffer_zone_text_points), 1) == 0.0:
                            buffer_zone_list.append([buffer_zone_id, buffer_zone_text, buffer_zone_text_points,buffer_zone_lw_ploy])

                if buffer_zone_list != [] or buffer_zone_list is None:
                    for buffer_zone_data in buffer_zone_list:
                        buffer_zone_dict[buffer_zone_data[0]] = buffer_zone_data[1:]

        return buffer_zone_dict

    def _LeftoverOwnersLand_layer_entity(self,_LeftoverOwnersLand):

        left_over_owners_land_zone_dict = dict()
        for left_over_owners_land_lw_entity in _LeftoverOwnersLand:

            if left_over_owners_land_lw_entity.dxftype() == "LWPOLYLINE" and left_over_owners_land_lw_entity.closed:

                check_leftover = any(
                    [entity.dxftype() == "ARC" for entity in left_over_owners_land_lw_entity.virtual_entities()])

                left_over_owners_land_lw_ploy = polygon2arc(left_over_owners_land_lw_entity) if check_leftover else Polygon(
                    left_over_owners_land_lw_entity.get_points("xy"))

                left_over_owners_land_list = []

                for left_over_owners_land_text_entity in _LeftoverOwnersLand:
                    if left_over_owners_land_text_entity.dxftype() == "MTEXT" or left_over_owners_land_text_entity.dxftype() == "TEXT":
                        left_over_owners_land_text = left_over_owners_land_text_entity.dxf.text if left_over_owners_land_text_entity.dxftype() == "TEXT" else left_over_owners_land_text_entity.plain_text()
                        left_over_owners_land_id = left_over_owners_land_text_entity.dxf.handle
                        left_over_owners_land_points = (
                            left_over_owners_land_text_entity.dxf.insert.x, left_over_owners_land_text_entity.dxf.insert.y)
                        left_over_owners_land_text_points = Point(left_over_owners_land_points)

                        if left_over_owners_land_lw_ploy.contains(
                                left_over_owners_land_text_points) == True or left_over_owners_land_lw_ploy.touches(
                            left_over_owners_land_text_points) == True or round(
                            left_over_owners_land_lw_ploy.distance(left_over_owners_land_text_points), 1) == 0.0:
                            left_over_owners_land_list.append([left_over_owners_land_id, left_over_owners_land_text, left_over_owners_land_text_points,left_over_owners_land_lw_ploy])

                if left_over_owners_land_list != [] or left_over_owners_land_list is None:
                    for left_over_owners_land_data in left_over_owners_land_list:
                        left_over_owners_land_zone_dict[left_over_owners_land_data[0]] = left_over_owners_land_data[1:]

        return left_over_owners_land_zone_dict

    def water_bodies_layer_entity(self,_WaterBodies):
        water_bodies_dict = dict()
        for water_bodies_lw_entity in _WaterBodies:
            if water_bodies_lw_entity.dxftype() == "LWPOLYLINE" and water_bodies_lw_entity.closed:

                check_wbarc = any(
                    [entity.dxftype() == "ARC" for entity in water_bodies_lw_entity.virtual_entities()])

                water_bodies_lw_ploy = polygon2arc(water_bodies_lw_entity) if check_wbarc else Polygon(
                    water_bodies_lw_entity.get_points("xy"))

                water_bodies_list = []

                for water_bodies_text_entity in _WaterBodies:
                    if water_bodies_text_entity.dxftype() == "MTEXT" or water_bodies_text_entity.dxftype() == "TEXT":
                        water_bodies_text = water_bodies_text_entity.dxf.text if water_bodies_text_entity.dxftype() == "TEXT" else water_bodies_text_entity.plain_text()
                        water_bodies_id = water_bodies_text_entity.dxf.handle
                        water_bodies_points = (water_bodies_text_entity.dxf.insert.x, water_bodies_text_entity.dxf.insert.y)
                        water_bodies_text_points = Point(water_bodies_points)

                        if water_bodies_lw_ploy.contains(water_bodies_text_points) == True or water_bodies_lw_ploy.touches(
                                water_bodies_text_points) == True or round(water_bodies_lw_ploy.distance(water_bodies_text_points), 1) == 0.0:
                            water_bodies_list.append([water_bodies_id, water_bodies_text, water_bodies_lw_ploy])

                if water_bodies_list != [] or water_bodies_list is None:
                    for water_bodies_data in water_bodies_list:
                        water_bodies_dict[water_bodies_data[0]] = water_bodies_data[1:]

        return water_bodies_dict


    def _notInPossession_layer_entity(self,_NotInPossession):

        _notInPossession_dict = dict()
        for _notInPossession_lw_entity in _NotInPossession:
            if _notInPossession_lw_entity.dxftype() == "LWPOLYLINE" and _notInPossession_lw_entity.closed:

                check_notrinpossarc = any(
                    [entity.dxftype() == "ARC" for entity in _notInPossession_lw_entity.virtual_entities()])

                _notInPossession_lw_ploy = polygon2arc(_notInPossession_lw_entity) if check_notrinpossarc else Polygon(
                    _notInPossession_lw_entity.get_points("xy"))

                _notInPossession_list = []

                for _notInPossession_text_entity in _NotInPossession:
                    if _notInPossession_text_entity.dxftype() == "MTEXT" or _notInPossession_text_entity.dxftype() == "TEXT":
                        _notInPossession_text = _notInPossession_text_entity.dxf.text if _notInPossession_text_entity.dxftype() == "TEXT" else _notInPossession_text_entity.plain_text()
                        _notInPossession_id = _notInPossession_text_entity.dxf.handle
                        _notInPossession_points = (_notInPossession_text_entity.dxf.insert.x, _notInPossession_text_entity.dxf.insert.y)
                        _notInPossession_text_points = Point(_notInPossession_points)

                        if _notInPossession_lw_ploy.contains(_notInPossession_text_points) == True or _notInPossession_lw_ploy.touches(
                                _notInPossession_text_points) == True or round(_notInPossession_lw_ploy.distance(_notInPossession_text_points), 1) == 0.0:
                            _notInPossession_list.append([_notInPossession_id, _notInPossession_text, _notInPossession_text_points,_notInPossession_lw_ploy])

                if _notInPossession_list != [] or _notInPossession_list is None:
                    for _notInPossession_data in _notInPossession_list:
                        _notInPossession_dict[_notInPossession_data[0]] = _notInPossession_data[1:]

        return _notInPossession_dict

    def Read_File_Data_DXF_File(self,msp):
        returnValueDict=dict()

        try:
            if (msp is None):
                returnValueDict['code']=-1
                msg='Required inputs of msp is missing for method get_building_mortgage_carpetarea. Modelspace ' + str(msp)
                returnValueDict['error']=msg

                return returnValueDict

            all_data_list= []
            _plot = msp.query('*[layer == "_Plot"]')
            _plot_file_data = self.plot_layer_entity(_plot)


            _BufferZone = msp.query('*[layer == "_BufferZone"]')
            _BufferZone_file_data = self._BufferZone_layer_entity(_BufferZone)

            _LeftoverOwnersLand = msp.query('*[layer == "_LeftoverOwnersLand"]')
            _LeftoverOwnersLand_file_data = self._LeftoverOwnersLand_layer_entity(_LeftoverOwnersLand)


            _WaterBodies = msp.query('*[layer == "_WaterBodies"]')
            _WaterBodies_file_data = self.water_bodies_layer_entity(_WaterBodies)

            _NotInPossession = msp.query('*[layer == "_NotInPossession"]')
            _NotInPossession_file_data = self._notInPossession_layer_entity(_NotInPossession)



            plot_dict = dict()
            for plot_id, plot_layer_poly in _plot_file_data.items():

                buffer_list = []
                for _buffer_id,_buffer_level_poly in _BufferZone_file_data.items():
                    _buffer_data = {}
                    _buffer_data['BUFFERZONE_ID'] = _buffer_id
                    _buffer_data['BUFFERZONE_NAME'] = _buffer_level_poly[0]
                    _buffer_data['BUFFERZONE_AREA'] = str(round(_buffer_level_poly[2].area, 2))
                    if plot_layer_poly[1].contains(_buffer_level_poly[1]) == True:
                        _buffer_data['BUFFERZONE_PLACEMENT'] = "Inside"
                    else:
                        _buffer_data['BUFFERZONE_PLACEMENT'] = "Outside"
                    buffer_list.append(_buffer_data)

                LeftoverOwnersLand_list = []
                for left_over_id,left_over_level_poly in _LeftoverOwnersLand_file_data.items():
                    In_side_left_over_data = {}
                    In_side_left_over_data['LEFTOVEROWNERSLAND_ID'] = left_over_id
                    In_side_left_over_data['LEFTOVEROWNERSLAND_LEVEL_NAME'] = left_over_level_poly[0]
                    In_side_left_over_data['LEFTOVEROWNERSLAND_AREA'] = str(round(left_over_level_poly[2].area, 2))
                    if plot_layer_poly[1].contains(left_over_level_poly[1]) == True:
                        In_side_left_over_data['LEFTOVEROWNERSLAND_PLACEMENT'] = "Inside"
                    else:
                        In_side_left_over_data['LEFTOVEROWNERSLAND_PLACEMENT'] = "Outside"
                    LeftoverOwnersLand_list.append(In_side_left_over_data)

                Water_boddies_list =[]
                for water_bodies_id,water_bodies_level_poly in _WaterBodies_file_data.items():
                    In_side_left_over_data = {}
                    In_side_left_over_data['WATERBODIES_ID'] = water_bodies_id
                    In_side_left_over_data['WATERBODIES_NAME'] = water_bodies_level_poly[0]
                    In_side_left_over_data["WATER_BODIES_AREA"] = str(round(water_bodies_level_poly[1].area,1))

                    if plot_layer_poly[1].contains(water_bodies_level_poly[1]) == True:
                        In_side_left_over_data['WATERBODIES_PLACEMENT'] = "Inside"
                    else:
                        In_side_left_over_data['WATERBODIES_PLACEMENT'] = "Outside"
                    Water_boddies_list.append(In_side_left_over_data)


                _notInPossession_list = []
                for _notInPossession_id, _notInPossession_level_poly in _NotInPossession_file_data.items():

                    In_side_left_over_data = {}
                    In_side_left_over_data['NOTINPOSSESSION_ID'] =_notInPossession_id
                    In_side_left_over_data['NOTINPOSSESSION_NAME'] = _notInPossession_level_poly[0]
                    In_side_left_over_data["NOTINPOSSESSION_AREA"] = str(round(_notInPossession_level_poly[2].area,1))

                    if plot_layer_poly[1].contains(_notInPossession_level_poly[1]) == True:
                        In_side_left_over_data['NOTINPOSSESSION_PLACEMENT'] = "Inside"
                    else:
                        In_side_left_over_data['NOTINPOSSESSION_PLACEMENT'] = "Outside"
                    _notInPossession_list.append(In_side_left_over_data)

                plot_dict['BUFFER_DATA']= buffer_list
                plot_dict['LEFTOVEROWNERSLAND_DATA'] = LeftoverOwnersLand_list
                plot_dict['WATERBODIES_DATA'] = Water_boddies_list
                plot_dict['NOTINPOSSESSION_DATA'] = _notInPossession_list
                # all_data_list.append(plot_dict)


                returnValueDict['code']=0
                returnValueDict['data']=plot_dict

        except ezdxf.DXFStructureError as dse:
                msg=f'Not a DXF file or a generic I/O error.' + str(dse)
                returnValueDict['code']=-1
                returnValueDict['error']=msg

        except IOError as ioe:
                msg=f'Invalid or corrupted DXF file.'+ str(ioe)
                returnValueDict['code']=-1
                returnValueDict['error']=msg

        return returnValueDict

# Main Program
#
# Data_Extractor = DXF_File_Data()
# print("="*60)
# print(f"File Execution Started..")
# print("="*60)
# # filename = "D:/All_ADS_file/open_layout_all_file/open_layout_DXF_file_with_layer/20032023_SKS_TANKIKELA_RAMJAN_(1)_MODIFIED_BPCLayer.dxf"
# filename = "D:/New_folder/dxf/DDDDDDlock_BPCLayer.dxf"
# doc = ezdxf.readfile(filename)
# modelspace = doc.modelspace()
# result = Data_Extractor.Read_File_Data_DXF_File(modelspace)
# print(result)
# print("="*60)
# print(f"File Execution Completed..")
# print("="*60)