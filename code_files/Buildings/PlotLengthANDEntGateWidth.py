# ---------------------------------------------------Modules---------------------------------------------------------------
import os
import ezdxf
from shapely.geometry import Point, Polygon
from shapely.geometry import LineString
import numpy as np

#--------------------------Mahendra Bhai Code---------------------------------------------------------------------------
class Plot_Width_Depth:
    """
    Finding: Plot Width,Depth And Area
    """

    def calculate_width(self,line_blue,line_green):
        """ 1.We are checking distance Between side1 and side2
        2. returning Minimum Distance Between Side1 and side2
        3. We are getting Width of the plot from This
         """
        sub_dist = set()

        for blue in line_blue:

            for green in line_green:

                sub_dist.add(round(blue.distance(green),1))

        return min(sub_dist)

    def find_layer_distance(self,line_pink,line_blue,line_green):
        """
        1 . Here We are checking Rear Line With Side1 and Side2
        That witch Line is touching to rear line
        2.getting All Rear line if side1 and Side2 is touching
        """
        total_lines = []

        for pink in line_pink:

            for blue in line_blue:

                if round(pink.distance(blue),1) == 0.0:

                    total_lines.append(pink)

            for green in line_green:

                if round(pink.distance(green),1) == 0.0:

                    total_lines.append(pink)

        return total_lines

    def mainroad_touches_with_fnt_line(self,mainroad_poly,line_red):
        '''
        1. Here We are checking MainRoad Polygon with (MarginLine) Front Line
        that Front_line points touching To MainRoad Polygon if Touches we are Returning
        True otherwise False.
        '''

        lines_points = [round(mainroad_poly.distance(lines),1)== 0.0 for lines in line_red ]

        if len(lines_points) > 0:

            return True

        else:

            return False

    def mainroad_rear_lines_point(self,mainroad_poly,line_pink):
         """
         finding mainroad polygon touch with Front Margin line or Not

         :param mainroad_poly:
         :param line_pink:
         :return:
         """
         rear_list = []

         for lines in line_pink:

            rear_list.append(round(mainroad_poly.distance(lines),1))

         return max(rear_list)

    def MainRoadLayerData(self,_MainRoad_Entities):
        '''
        1.Checking MainRoad data and returning MainRoad ID ,MainRoad Text
        and MainRoad Polygon in The Form Of Dict
        '''
        mainroad_dict = {}

        for mainroad_lw_entity in _MainRoad_Entities:

            if (mainroad_lw_entity.dxftype() == "LWPOLYLINE" and mainroad_lw_entity.closed):

                mainroad_entity_point = [pp[0:2] for pp in mainroad_lw_entity.get_points()]

                mainroad_id = mainroad_lw_entity.dxf.handle

                mainroad_lw_points = Polygon(mainroad_entity_point)

                mainroad_data_content = []

                for mainroad_text_entity in _MainRoad_Entities:

                    if mainroad_text_entity.dxftype() in ["MTEXT", "TEXT"]:

                        mainroad_text = mainroad_text_entity.dxf.text if mainroad_text_entity.dxftype() == "TEXT" else mainroad_text_entity.plain_text()

                        mainroad_text_id = mainroad_text_entity.dxf.handle

                        mainroad_text_po = (mainroad_text_entity.dxf.insert.x, mainroad_text_entity.dxf.insert.y)

                        mainroad_text_point = Point(mainroad_text_po)


                        if (mainroad_lw_points.contains(mainroad_text_point) or

                                mainroad_lw_points.touches(mainroad_text_point) or

                                round(mainroad_lw_points.distance(mainroad_text_point)) == 0):

                            mainroad_data_content.append([mainroad_id, mainroad_text, mainroad_lw_points])

                if mainroad_data_content:

                    for mainroad_data in mainroad_data_content:

                        mainroad_dict[mainroad_data[0]] = mainroad_data[1:]
                else:

                    print(f"Missing {mainroad_id} Level Of polygon")


        return mainroad_dict

    def PlotLayerData(self,_Plot_entities):
        '''
        1.Checking Plot data and returning Plot ID ,Plot Text
        and Plot Polygon in The Form Of Dict
        '''
        plot_dict = dict()

        for plot_poly in _Plot_entities:

            if plot_poly.dxftype() == "LWPOLYLINE" and plot_poly.closed:

                plot_id = plot_poly.dxf.handle

                plot_poly_pts = Polygon([pp[0:2] for pp in plot_poly.get_points()])

                # print(plot_poly_pts)

                plot_list = []

                for plot_text in _Plot_entities:

                    if plot_text.dxftype() == "MTEXT" or plot_text.dxftype() == "TEXT":

                        plot_name = plot_text.dxf.text if plot_text.dxftype() == "TEXT" else plot_text.plain_text()

                        plot_text_id = plot_text.dxf.handle

                        plot_text_pts = Point([plot_text.dxf.insert[0],plot_text.dxf.insert[1]])

                        if plot_poly_pts.contains(plot_text_pts) == True or plot_poly_pts.touches(plot_text_pts) == True or round(plot_poly_pts.distance(plot_text_pts),1) == 0.0:

                            plot_list.append([plot_text_id,plot_name,plot_poly_pts])


                if plot_list != [] or plot_list is not None:

                    for plot_data in plot_list:

                        plot_dict[plot_data[0]] = plot_data[1:]

                else:

                    print(f"plot({plot_id}) doesn't found Any Text")

        return plot_dict

    def plot_check_margin_line(self,plot_polygon,line_pts):
        '''1.Checking Margin Line Points Width Plot Polygon That Plot Polygon
        Touching Margin Line Points or Not
        2. If Touching Return True otherwise False
         '''

        plot_check_margin_line = []

        for line_points in line_pts:

            if round(plot_polygon.distance(line_points),1) == 0.0:

                plot_check_margin_line.append(True)

        if all(plot_check_margin_line) == True:

            return True

        else:

            return False

    def Check_plot_area(self,plot_level_poly):
        """Finding Plot Area"""
        plot_area = round(plot_level_poly.area,2)

        return plot_area

    def File_Validation(self,msp):
        '''1. Providing FolderName And FileName
        2 Calling And Executing  All Function
        3. We are returning a Dict..
        4.in this Dict returning Plot ID , Plot Name
         , Plot Dept and Plot Width'''

        data_dict = dict()


        try:

            print("Loading DXF File Data...")

            # Loading Data from MainRoad Layer

            _MainRoad_entities = msp.query('*[layer == "_MainRoad"]')

            MainRoad_Data_Dict = self.MainRoadLayerData(_MainRoad_entities)

            # Loading Data from Plot Layer

            _Plot_entities = msp.query('*[layer == "_Plot"]')

            Plot_Data_Dict = self.PlotLayerData(_Plot_entities)

            # Loading Data from Margin Lines Layer

            Margin_line = msp.query('INSERT[ layer == "_MarginLine"]')

            all_data_list = []

            for marginline in Margin_line:

                line_red = []

                line_blue = []

                line_green = []

                line_pink = []

                for margin_lines in marginline.virtual_entities():

                    color = margin_lines.dxf.color

                    start_pts = (margin_lines.dxf.start.x,margin_lines.dxf.start.y)

                    end_pts = (margin_lines.dxf.end.x, margin_lines.dxf.end.y)

                    line_pts = LineString([start_pts,end_pts])

                    if color == 1:

                        line_red.append(line_pts)

                    elif color == 5:

                        line_blue.append(line_pts)

                    elif color == 6:

                        line_pink.append(line_pts)

                    elif color == 104:

                        line_green.append(line_pts)

                # Adding All Points Into Single variable

                all_lines = line_red+line_blue+line_green+line_pink

                for plot_id, plot_level_poly in Plot_Data_Dict.items():

                    plot_area = self.Check_plot_area(plot_level_poly[1])

                    # 1 sending two Argument After That making this function condition

                    if(self.plot_check_margin_line(plot_level_poly[1],all_lines)) == True:

                        for mairaod_id ,mainroad_poly in MainRoad_Data_Dict.items():

                            # 1 sending two Argument After That making this function condition

                            if self.mainroad_touches_with_fnt_line(mainroad_poly[1],line_red) == True:

                                depth = self.mainroad_rear_lines_point(mainroad_poly[1],line_pink)

                                width = self.calculate_width(line_blue,line_green)

                                dist_dict = dict()

                                dist_dict["PLOT_ID"] = plot_id

                                dist_dict["PLOT_NAME"] = plot_level_poly[0]

                                dist_dict["PLOT_DEPTH"] = depth

                                dist_dict["PLOT_WIDTH"] = width

                                dist_dict["PLOT_AREA"] = plot_area

                                all_data_list.append(dist_dict)

                            else:

                                print(f"MainRoad ({mairaod_id})Does Not Touches to Front Line")

                    else:

                        print(f"Margin_line does Not Touch to plot line")

            if all_data_list is not None or all_data_list !=[]:

                data_dict["code"] = 0

                data_dict["data"] = all_data_list

        except ezdxf.DXFStructureError as dse:

            print(f"Invalid or Corrupted DXF File :{dse}")

        except IOError as ieo:

            print(f"Not a DXF File Generating I/O Error:- {ieo}")

        return data_dict

class SegmentwisePlotLength_AND_EntGateWidth:

    """
    Finding Segmentwise Plot Length and Entry Gate Width
    -----------------------------------------------------
    """
    def EntGateWidth(self,entgatepolygon):

        """Finding Width Of Entry Gate"""

        bbox=entgatepolygon.minimum_rotated_rectangle

        x,y=bbox.boundary.coords.xy

        length_width=[Point([x[0],y[0]]).distance(Point([x[1],y[1]])),Point([x[1],y[1]]).distance(Point([x[2],y[2]])),Point([x[2],y[2]]).distance(Point([x[3],y[3]])),Point([x[3],y[3]]).distance(Point([x[4],y[4]]))]

        return round(min(length_width),2)

    def PlotSegmentLength(self,PlotPolygon):
        """Finding Length Of Plot Segments.
            ex:[p1-p2:10.20,p2-p3:40.10]
        """
        b = PlotPolygon.exterior.coords

        listlineString = [(f'p{lin + 1}-p{lin + 2}', b[lin:lin + 2]) for lin in range(len(b) - 2)] + [(f'p{len(b)-1}-p{1}', [b[-2], b[-1]])]

        listlineString = [[ls[0], round(LineString(ls[1]).length,2)] for ls in listlineString]

        return listlineString

    def AccessoryUse_layer(self, AccessoryUseData):

        """
        Finding Entry Gate Label and Polygon

        :param AccessoryUseData  of entities:
        :return dict of entry gate id,entry gate label and entry gate polygon:
        """

        AccessoryUseDict = dict()

        AccessoryUseContainLabels = []

        for AccessoryUse_entity in AccessoryUseData:

            if AccessoryUse_entity.dxftype() == 'TEXT' or AccessoryUse_entity.dxftype() == 'MTEXT':

                AccessoryUsetext_id = AccessoryUse_entity.dxf.handle

                AccessoryUse_Properties = AccessoryUse_entity.dxfattribs()

                AccessoryUse_name = AccessoryUse_Properties.get('text') if AccessoryUse_entity.dxftype() == 'TEXT' else AccessoryUse_entity.plain_text()

                if 'gate' in AccessoryUse_name.lower():

                    AccessoryUse_pts = AccessoryUse_Properties.get('insert')

                    AccessoryUsetextPoint = Point(np.array([AccessoryUse_pts[0], AccessoryUse_pts[1]]))

                    for AccessoryUse_entity in AccessoryUseData:

                        if AccessoryUse_entity.dxftype() == 'LWPOLYLINE' and AccessoryUse_entity.closed:

                            AccessoryUsePolygonPoints = Polygon(np.array([ap[0:2] for ap in AccessoryUse_entity.get_points()]))

                            if AccessoryUsePolygonPoints.contains(AccessoryUsetextPoint) == True or AccessoryUsePolygonPoints.touches(AccessoryUsetextPoint) == True or round(AccessoryUsePolygonPoints.distance(AccessoryUsetextPoint), 1) == 0.0:

                                AccessoryUseContainLabels.append([AccessoryUsetext_id, AccessoryUse_name, AccessoryUsePolygonPoints])

                    if AccessoryUseContainLabels != [] and len(AccessoryUseContainLabels) > 0:

                        for acessoryUse in AccessoryUseContainLabels:

                            AccessoryUseDict[acessoryUse[0]] = [acessoryUse[1], acessoryUse[2]]
                    else:

                        print(f'Missing Polygon OF Ent.Gate For AccessoryUse Layer #REF {AccessoryUsetext_id}.')

        return AccessoryUseDict

    def Plot_layer(self, PlotData):
        """
            Finding Plot Label and Polygon from PlotData

            :param PlotData  of entities:

            :return dict of entry gate id,entry gate label and entry gate polygon:
        """
        # PlotDict = dict()
        #
        # plotpolydata=[]
        #
        # for Plot_entity in PlotData:
        #
        #     if Plot_entity.dxftype() == 'LWPOLYLINE' and Plot_entity.closed:
        #
        #         PlotPolgonId = Plot_entity.dxf.handle
        #
        #         PlotPolygonPoints = Polygon(np.array([pp[0:2] for pp in Plot_entity.get_points()]))
        #
        #         plotpolydata.append(PlotPolygonPoints)
        #
        # plotlabeldata = []
        #
        # for Plot_entity in PlotData:
        #
        #     if Plot_entity.dxftype() == 'TEXT' or Plot_entity.dxftype() == 'MTEXT':
        #
        #         Plottext_id = Plot_entity.dxf.handle
        #
        #         Plot_Properties = Plot_entity.dxfattribs()
        #
        #         Plot_name = Plot_Properties.get('text') if Plot_entity.dxftype() == 'TEXT' else Plot_entity.plain_text()
        #
        #         plotlabeldata.append([Plottext_id,Plot_name])
        #
        # if (plotlabeldata != [] and plotpolydata!=[]) and (len(plotlabeldata)<2 and len(plotpolydata)<2):
        #     #print(plotlabeldata,plotpolydata)
        #
        #     PlotDict[plotlabeldata[0][0]] = [plotlabeldata[0][1], plotpolydata[0]]
        #
        # elif(len(plotlabeldata)>1 or len(plotpolydata)>1):
        #
        #     print(f'Finding More Than One Polygon or Label For Plot Layer.')
        #
        # else:
        #
        #     print(f'Missing Label For Plot Layer Polygon or Label.')
        #
        # return PlotDict

        plot_dict = dict()

        for plot_poly in PlotData:

            if plot_poly.dxftype() == "LWPOLYLINE" and plot_poly.closed:

                plot_id = plot_poly.dxf.handle

                plot_poly_pts = Polygon([pp[0:2] for pp in plot_poly.get_points()])

                # print(plot_poly_pts)

                plot_list = []

                for plot_text in PlotData:

                    if plot_text.dxftype() == "MTEXT" or plot_text.dxftype() == "TEXT":

                        plot_name = plot_text.dxf.text if plot_text.dxftype() == "TEXT" else plot_text.plain_text()

                        plot_text_id = plot_text.dxf.handle

                        plot_text_pts = Point([plot_text.dxf.insert[0], plot_text.dxf.insert[1]])

                        if plot_poly_pts.contains(plot_text_pts) == True or plot_poly_pts.touches(
                                plot_text_pts) == True or round(plot_poly_pts.distance(plot_text_pts), 1) == 0.0:
                            plot_list.append([plot_text_id, plot_name, plot_poly_pts])

                if plot_list != [] or plot_list is not None:

                    for plot_data in plot_list:
                        plot_dict[plot_data[0]] = plot_data[1:]

                else:

                    print(f"plot({plot_id})doesn't found Any Text")

        return plot_dict

    def FindPlotLength_And_EntGateWidth(self, msp):
        """
        :param msp:
         getting Modelspace information
        :return final list of plot segment length and entry gate width:
        ex:[{'PLOT_REF':st3,'PLOT_NAME':plot,p1-p2:30.34,p2-p3:40.34,'PLOT_WIDTH':10.24,'PLOT_DEPTH':12.34,'PLOT_AREA':34.56},
        {'ENTGATE_REF':34dt,'ENTGATE_NAME':'ent.gate','ENTGATE_WIDTH':0.2}]
        """

        returnValueList = []

        if (msp is None or msp is None):

            return returnValueList

        try:

            print('Load Dxf File')

            PlotData = msp.query('TEXT MTEXT LWPOLYLINE[layer=="_Plot"]')

            PlotDict = self.Plot_layer(PlotData)

            AccessoryUseData = msp.query('TEXT MTEXT LWPOLYLINE[layer=="_AccessoryUse"]')

            AccessoryUseDict = self.AccessoryUse_layer(AccessoryUseData)

            tmpPlotdict =dict()

            for handle_id,LabelPoly in PlotDict.items():

                tmpPlotdict['PLOT_REF']=handle_id

                tmpPlotdict['PLOT_NAME'] = LabelPoly[0]

                plot_lengthsegment = self.PlotSegmentLength(LabelPoly[1])

                for segment_labelLength in plot_lengthsegment:

                    tmpPlotdict[segment_labelLength[0]]=segment_labelLength[1]

            plot_area_width_depth=Plot_Width_Depth()

            return_plot_area_width_depth=plot_area_width_depth.File_Validation(msp)

            if return_plot_area_width_depth.get('data')!=[] or return_plot_area_width_depth.get('data') is not None:

                for data in return_plot_area_width_depth.get('data'):

                    tmpPlotdict['PLOT_WIDTH'] = data.get('PLOT_WIDTH')

                    tmpPlotdict['PLOT_DEPTH'] = data.get('PLOT_DEPTH')

                    tmpPlotdict['PLOT_AREA'] = data.get('PLOT_AREA')

            if tmpPlotdict!={} and len(tmpPlotdict)>0:

                returnValueList.append(tmpPlotdict)

            tmpentgatedict = dict()

            for handle_id,LabelPoly in AccessoryUseDict.items():

                gate_width=self.EntGateWidth(LabelPoly[1])

                tmpentgatedict['ENTGATE_REF'] = handle_id

                tmpentgatedict['ENTGATE_NAME'] = LabelPoly[0]

                tmpentgatedict['ENTGATE_WIDTH']= gate_width

            if tmpentgatedict!={} and len(tmpentgatedict)>0:

                returnValueList.append(tmpentgatedict)

        except IOError:

            print(f'Not a DXF file or a generic I/O error.')

            return returnValueList

        except ezdxf.DXFStructureError:

            print(f'Invalid or corrupted DXF file.')

            return returnValueList

        return returnValueList

# # -----------------------------------Input of file-----------------------------------------------------
# # from ReadDWGFile import readDWG_File
#
# # path of the filename
#
# folder = r'E:/production_code/dxf_files/Buildings'
#
# # Pass extension - removed inside method
#
# filename = 'st (1) (1).dxf'  # Here give only filename
#
# # method returns a dict with handle
#
# from datetime import datetime
#
# start_time = datetime.now()
#
# t1 = start_time.strftime("%H:%M:%S")
#
# first_start_time = datetime.strptime(t1,"%H:%M:%S")
#
# dxf_file = ezdxf.readfile(os.path.join(folder, filename))
#
# msp = dxf_file.modelspace()
#
# response = SegmentwisePlotLength_AND_EntGateWidth()
#
# print('Plot Length EntGate Width Response ', response.FindPlotLength_And_EntGateWidth(msp))
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