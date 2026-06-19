'''
DOCUMENTATION:
-------------

1.Find minimum width of polygon ,maximum width of polygon and area of polygon of transfer setbacks layer.Find side of setbacks.

step:
----
1.Find proposed work layer of polygon and text.

2.check proposed work text in proposed work polygon or not.

3.Find transfer of setback layers of polygon and text.

4.check transfer of setbacks text in transfer of setbacks of polygon.

5.Find maximum width ,minimum width and area of transfer setbacks of polygon.


'''

import ezdxf

from shapely.geometry import Point,Polygon

from shapely.geometry import LineString
from timeit import default_timer as timer

import numpy as np
from convert_polygon_to_arc import polygon2arc
#msp
def transfer_setbacks(msp):#(msp):#folder:str,filename:str):

    returnValueDict={}

    resultsList=[]

    if (msp is None): #(msp):#folder is None or filename is None):

        return returnValueDict

    #dxf_path=os.path.join(folder,filename)
    

    try:

        #read_dxf=ezdxf.readfile(dxf_path)

        
        #print('read file')

        print('read file')

        #msp=read_dxf.modelspace()


        #get proposed work layer
        startTimer=timer()


        txtPropWorkList= msp.query('*[layer=="_ProposedWork"]')
        lwpolyPropWorkList= msp.query('LWPOLYLINE[layer=="_ProposedWork"]')
        txtTransferSetbackList=msp.query('*[layer=="_TransferOfSetback"]')
        lwpolyTransferSetbackList=msp.query('LWPOLYLINE[layer=="_TransferOfSetback"]')

        for proposed_text in txtPropWorkList:#msp.query('*[layer=="_ProposedWork"]'):

             if proposed_text.dxftype()=='TEXT' or proposed_text.dxftype()=='MTEXT':

                 building_name=proposed_text.dxf.text if proposed_text.dxftype()=='TEXT' else proposed_text.text

                 dxf_attribs=proposed_text.dxfattribs()

                 insert_pts=dxf_attribs.get('insert')

                 text_pts=[insert_pts[0],insert_pts[1]]

                 np_text_pts=np.array(text_pts).round(2)

                 text_points=Point(np_text_pts)

                 for proposed_polygon in lwpolyPropWorkList:#msp.query('LWPOLYLINE[layer=="_ProposedWork"]'):

                     proposed_polygon_pts=[pp[0:2] for pp in proposed_polygon.get_points()]

                     np_proposed_polygon_pts=np.array(proposed_polygon_pts).round(2)

                     proposed_polygon_points=Polygon(np_proposed_polygon_pts)

                     if proposed_polygon_points.contains(text_points)==True or proposed_polygon_points.touches(text_points)==True or (round(proposed_polygon_points.distance(text_points))==0):
                          position_data=[]

                          front_side_data=[]

                          rear_side_data=[]

                          side1_data=[]

                          side2_data=[]

                          for ts_entity in txtTransferSetbackList:#msp.query('*[layer=="_TransferOfSetback"]'):

                              if ts_entity.dxftype()=='TEXT' or ts_entity.dxftype()=='MTEXT':

                                  ts_name=ts_entity.dxf.text if ts_entity.dxftype()=='TEXT' else ts_entity.text

                                  ts_attribs=ts_entity.dxfattribs()

                                  ts_insert_pts=ts_attribs.get('insert')

                                  ts_pts=[ts_insert_pts[0],ts_insert_pts[1]]

                                  np_ts_pts=np.array(ts_pts).round(2)

                                  ts_points=Point(np_ts_pts)

                                  for ts_polygon in lwpolyTransferSetbackList:#msp.query('LWPOLYLINE[layer=="_TransferOfSetback"]'):
                                      #print(ts_polygon.dxf.color)
                                      #print(ts_polygon)
                                      if ts_polygon.dxf.color==1:

                                          ts_polygon_pts=[tp[0:2] for tp in ts_polygon.get_points()]

                                          checkArc= any([entity.dxftype()=="ARC" for entity in ts_polygon.virtual_entities()])
                                          if checkArc:
                                              ts_polygon_points=polygon2arc(ts_polygon)
                                          else:

                                              np_ts_polygon_pts=np.array(ts_polygon_pts).round(2)

                                              ts_polygon_points=Polygon(np_ts_polygon_pts)

                                          if ts_polygon_points.contains(ts_points)==True or ts_polygon_points.touches(ts_points)==True or round(ts_polygon_points.distance(ts_points))==0:

                                              if proposed_polygon_points.touches(ts_polygon_points)==True or proposed_polygon_points.contains(ts_polygon_points)==True or round(proposed_polygon_points.distance(ts_polygon_points))==0:

                                                  # get minimum bounding box around polygon
                                                  box = ts_polygon_points.minimum_rotated_rectangle

                                                  # get coordinates of polygon vertices
                                                  x, y = box.exterior.coords.xy

                                                  # get length of bounding box edges
                                                  edge_length = (Point(x[0], y[0]).distance(Point(x[1], y[1])), Point(x[1], y[1]).distance(Point(x[2], y[2])))

                                                  # get width of polygon as the shortest edge of the bounding box

                                                  width = round(min(edge_length),2)

                                                  width2_list=[]

                                                  for vir_entity in ts_polygon.virtual_entities():

                                                      if vir_entity.dxftype()=='LINE':

                                                          vir_start_line_pts=[vir_entity.dxf.start[0],vir_entity.dxf.start[1]]

                                                          vir_end_line_pts=[vir_entity.dxf.end[0],vir_entity.dxf.end[1]]

                                                          vir_line_pts=[vir_start_line_pts,vir_end_line_pts]

                                                          np_vir_line_pts=np.array(vir_line_pts).round(2)

                                                          line_points=LineString(np_vir_line_pts)

                                                          line_length=round(line_points.length)

                                                          if line_length>0:

                                                              for vir_entity1 in ts_polygon.virtual_entities():

                                                                  if vir_entity1.dxftype()=='LINE':

                                                                      vir_start_line1_pts=[vir_entity1.dxf.start[0],vir_entity1.dxf.start[1]]

                                                                      vir_end_line1_pts=[vir_entity1.dxf.end[0],vir_entity1.dxf.end[1]]

                                                                      vir_line1_pts=[vir_start_line1_pts,vir_end_line1_pts]

                                                                      np_vir_line1_pts=np.array(vir_line1_pts).round(2)

                                                                      line1_points=LineString(np_vir_line1_pts)

                                                                      line1_length=round(line1_points.length)

                                                                      if line1_length>0:

                                                                          if round(line_points.distance(line1_points))>0:

                                                                              width2_list.append(round(line_points.distance(line1_points),2))
                                                  if width2_list!=[]:

                                                      ts_polygon_area=round(ts_polygon_points.area,2)

                                                      ts_dict=dict()

                                                      #ts_dict[ts_name]={'AREA':ts_polygon_area,'MAX WIDTH':width,'MIN WIDTH':min(width2_list)}
                                                      ts_dict['POSITION']='FRONT'
                                                      ts_dict['TRANSFER_SETBACK_TYPE']=str(ts_name)
                                                      ts_dict['AREA']=ts_polygon_area
                                                      ts_dict['MAX_WIDTH']=width
                                                      ts_dict['MIN_WIDTH']=min(width2_list)

                                                      #front_side_data.append(ts_dict)
                                                      position_data.append(ts_dict)


                                      elif(ts_polygon.dxf.color==6):

                                          checkArc = any(
                                              [entity.dxftype() == "ARC" for entity in ts_polygon.virtual_entities()])
                                          if checkArc:
                                              ts_polygon_points = polygon2arc(ts_polygon)
                                          else:

                                              ts_polygon_pts=[tp[0:2] for tp in ts_polygon.get_points()]

                                              np_ts_polygon_pts=np.array(ts_polygon_pts).round(2)

                                              ts_polygon_points=Polygon(np_ts_polygon_pts)

                                          if ts_polygon_points.contains(ts_points)==True or ts_polygon_points.touches(ts_points)==True or round(ts_polygon_points.distance(ts_points))==0:

                                              if proposed_polygon_points.touches(ts_polygon_points)==True or proposed_polygon_points.contains(ts_polygon_points)==True or round(proposed_polygon_points.distance(ts_polygon_points))==0:

                                                  # get minimum bounding box around polygon
                                                  box = ts_polygon_points.minimum_rotated_rectangle

                                                  # get coordinates of polygon vertices
                                                  x, y = box.exterior.coords.xy

                                                  # get length of bounding box edges
                                                  edge_length = (Point(x[0], y[0]).distance(Point(x[1], y[1])), Point(x[1], y[1]).distance(Point(x[2], y[2])))

                                                  # get width of polygon as the shortest edge of the bounding box

                                                  width = round(min(edge_length),2)

                                                  width2_list=[]

                                                  for vir_entity in ts_polygon.virtual_entities():

                                                      if vir_entity.dxftype()=='LINE':

                                                          vir_start_line_pts=[vir_entity.dxf.start[0],vir_entity.dxf.start[1]]

                                                          vir_end_line_pts=[vir_entity.dxf.end[0],vir_entity.dxf.end[1]]

                                                          vir_line_pts=[vir_start_line_pts,vir_end_line_pts]

                                                          np_vir_line_pts=np.array(vir_line_pts).round(2)

                                                          line_points=LineString(np_vir_line_pts)

                                                          line_length=round(line_points.length)

                                                          if line_length>0:

                                                              for vir_entity1 in ts_polygon.virtual_entities():

                                                                  if vir_entity1.dxftype()=='LINE':

                                                                      vir_start_line1_pts=[vir_entity1.dxf.start[0],vir_entity1.dxf.start[1]]

                                                                      vir_end_line1_pts=[vir_entity1.dxf.end[0],vir_entity1.dxf.end[1]]

                                                                      vir_line1_pts=[vir_start_line1_pts,vir_end_line1_pts]

                                                                      np_vir_line1_pts=np.array(vir_line1_pts).round(2)

                                                                      line1_points=LineString(np_vir_line1_pts)

                                                                      line1_length=round(line1_points.length)

                                                                      if line1_length>0:

                                                                          if round(line_points.distance(line1_points))>0:

                                                                              width2_list.append(round(line_points.distance(line1_points),2))
                                                  if width2_list!=[]:

                                                      ts_polygon_area=round(ts_polygon_points.area,2)

                                                      ts_dict=dict()

                                                      #ts_dict[ts_name]={'AREA':ts_polygon_area,'MAX WIDTH':width,'MIN WIDTH':min(width2_list)}
                                                      ts_dict['POSITION']='REAR'
                                                      ts_dict['TRANSFER_SETBACK_TYPE']=str(ts_name)
                                                      ts_dict['AREA']=ts_polygon_area
                                                      ts_dict['MAX_WIDTH']=width
                                                      ts_dict['MIN_WIDTH']=min(width2_list)

                                                      #rear_side_data.append(ts_dict)
                                                      position_data.append(ts_dict)


                                      elif(ts_polygon.dxf.color==5):

                                          checkArc = any(
                                              [entity.dxftype() == "ARC" for entity in ts_polygon.virtual_entities()])
                                          if checkArc:
                                              ts_polygon_points = polygon2arc(ts_polygon)
                                          else:

                                              ts_polygon_pts=[tp[0:2] for tp in ts_polygon.get_points()]

                                              np_ts_polygon_pts=np.array(ts_polygon_pts).round(2)

                                              ts_polygon_points=Polygon(np_ts_polygon_pts)

                                          if ts_polygon_points.contains(ts_points)==True or ts_polygon_points.touches(ts_points)==True or round(ts_polygon_points.distance(ts_points))==0:

                                              if proposed_polygon_points.touches(ts_polygon_points)==True or proposed_polygon_points.contains(ts_polygon_points)==True or round(proposed_polygon_points.distance(ts_polygon_points))==0:

                                                  # get minimum bounding box around polygon
                                                  box = ts_polygon_points.minimum_rotated_rectangle

                                                  # get coordinates of polygon vertices
                                                  x, y = box.exterior.coords.xy

                                                  # get length of bounding box edges
                                                  edge_length = (Point(x[0], y[0]).distance(Point(x[1], y[1])), Point(x[1], y[1]).distance(Point(x[2], y[2])))

                                                  # get width of polygon as the shortest edge of the bounding box

                                                  width = round(min(edge_length),2)

                                                  width2_list=[]

                                                  for vir_entity in ts_polygon.virtual_entities():

                                                      if vir_entity.dxftype()=='LINE':

                                                          vir_start_line_pts=[vir_entity.dxf.start[0],vir_entity.dxf.start[1]]

                                                          vir_end_line_pts=[vir_entity.dxf.end[0],vir_entity.dxf.end[1]]

                                                          vir_line_pts=[vir_start_line_pts,vir_end_line_pts]

                                                          np_vir_line_pts=np.array(vir_line_pts).round(2)

                                                          line_points=LineString(np_vir_line_pts)

                                                          line_length=round(line_points.length)

                                                          if line_length>0:

                                                              for vir_entity1 in ts_polygon.virtual_entities():

                                                                  if vir_entity1.dxftype()=='LINE':

                                                                      vir_start_line1_pts=[vir_entity1.dxf.start[0],vir_entity1.dxf.start[1]]

                                                                      vir_end_line1_pts=[vir_entity1.dxf.end[0],vir_entity1.dxf.end[1]]

                                                                      vir_line1_pts=[vir_start_line1_pts,vir_end_line1_pts]

                                                                      np_vir_line1_pts=np.array(vir_line1_pts).round(2)

                                                                      line1_points=LineString(np_vir_line1_pts)

                                                                      line1_length=round(line1_points.length)

                                                                      if line1_length>0:

                                                                          if round(line_points.distance(line1_points))>0:

                                                                              width2_list.append(round(line_points.distance(line1_points),2))
                                                  if width2_list!=[]:

                                                      ts_polygon_area=round(ts_polygon_points.area,2)

                                                      ts_dict=dict()

                                                      #ts_dict[ts_name]={'AREA':ts_polygon_area,'MAX WIDTH':width,'MIN WIDTH':min(width2_list)}
                                                      ts_dict['POSITION']='SIDE1'
                                                      ts_dict['TRANSFER_SETBACK_TYPE']=str(ts_name)
                                                      ts_dict['AREA']=ts_polygon_area
                                                      ts_dict['MAX_WIDTH']=width
                                                      ts_dict['MIN_WIDTH']=min(width2_list)

                                                      #side1_data.append(ts_dict)
                                                      position_data.append(ts_dict)

                                      elif(ts_polygon.dxf.color==104):

                                          checkArc = any(
                                              [entity.dxftype() == "ARC" for entity in ts_polygon.virtual_entities()])
                                          if checkArc:
                                              ts_polygon_points = polygon2arc(ts_polygon)
                                          else:

                                              ts_polygon_pts=[tp[0:2] for tp in ts_polygon.get_points()]

                                              np_ts_polygon_pts=np.array(ts_polygon_pts).round(2)

                                              ts_polygon_points=Polygon(np_ts_polygon_pts)

                                          if ts_polygon_points.contains(ts_points)==True or ts_polygon_points.touches(ts_points)==True or round(ts_polygon_points.distance(ts_points))==0:

                                              if proposed_polygon_points.touches(ts_polygon_points)==True or proposed_polygon_points.contains(ts_polygon_points)==True or round(proposed_polygon_points.distance(ts_polygon_points))==0:

                                                  # get minimum bounding box around polygon
                                                  box = ts_polygon_points.minimum_rotated_rectangle

                                                  # get coordinates of polygon vertices
                                                  x, y = box.exterior.coords.xy

                                                  # get length of bounding box edges
                                                  edge_length = (Point(x[0], y[0]).distance(Point(x[1], y[1])), Point(x[1], y[1]).distance(Point(x[2], y[2])))

                                                  # get width of polygon as the shortest edge of the bounding box

                                                  width = round(min(edge_length),2)

                                                  width2_list=[]

                                                  for vir_entity in ts_polygon.virtual_entities():

                                                      if vir_entity.dxftype()=='LINE':

                                                          vir_start_line_pts=[vir_entity.dxf.start[0],vir_entity.dxf.start[1]]

                                                          vir_end_line_pts=[vir_entity.dxf.end[0],vir_entity.dxf.end[1]]

                                                          vir_line_pts=[vir_start_line_pts,vir_end_line_pts]

                                                          np_vir_line_pts=np.array(vir_line_pts).round(2)

                                                          line_points=LineString(np_vir_line_pts)

                                                          line_length=round(line_points.length)

                                                          if line_length>0:

                                                              for vir_entity1 in ts_polygon.virtual_entities():

                                                                  if vir_entity1.dxftype()=='LINE':

                                                                      vir_start_line1_pts=[vir_entity1.dxf.start[0],vir_entity1.dxf.start[1]]

                                                                      vir_end_line1_pts=[vir_entity1.dxf.end[0],vir_entity1.dxf.end[1]]

                                                                      vir_line1_pts=[vir_start_line1_pts,vir_end_line1_pts]

                                                                      np_vir_line1_pts=np.array(vir_line1_pts).round(2)

                                                                      line1_points=LineString(np_vir_line1_pts)

                                                                      line1_length=round(line1_points.length)

                                                                      if line1_length>0:

                                                                          if round(line_points.distance(line1_points))>0:

                                                                              width2_list.append(round(line_points.distance(line1_points),2))
                                                  if width2_list!=[]:

                                                      ts_polygon_area=round(ts_polygon_points.area,2)

                                                      ts_dict=dict()
                                                      ts_dict['POSITION']='SIDE2'
                                                      ts_dict['TRANSFER_SETBACK_TYPE']=str(ts_name)
                                                      ts_dict['AREA']=ts_polygon_area
                                                      ts_dict['MAX_WIDTH']=width
                                                      ts_dict['MIN_WIDTH']=min(width2_list)

                                                      position_data.append(ts_dict)
                                                      #side2_data.append(ts_dict)
                          tmpwork_Dict=dict()
                          if position_data !=[]:

                            resultsList.append({building_name:position_data})
                          endTimer=timer()
                          print('Transfer Of Setbacks Total Time Taken ', str(round(endTimer-startTimer,2)) , ' sec ') 

                          # if front_side_data!=[]:

                          #     tmpwork_Dict['FRONT']=front_side_data

                          # if rear_side_data!=[]:

                          #     tmpwork_Dict['REAR']=rear_side_data

                          # if side1_data!=[]:

                          #     tmpwork_Dict['SIDE1']=side1_data

                          # if side2_data!=[]:

                          #    tmpwork_Dict['SIDE2']=side2_data

                          # if tmpwork_Dict!={}:
                          #     resultsList.append({building_name:tmpwork_Dict})

                              #returnValueDict[building_name]=tmpwork_Dict




    except IOError:

            print(f'Not a DXF file or a generic I/O error.')
            return []

    except ezdxf.DXFStructureError:

             print(f'Invalid or corrupted DXF file.')
             return []

    return resultsList#returnValueDict




# #path of the filename

# folder=r'E:\production_code\dxf_files'

# # #Pass extension - removed inside method

# filename='NewResi Transfer From Side 1 to Side 2 (2).dxf'                   # Here give only filename

# #method returns a dict with handle

# response=transfer_setbacks(folder,filename)

# print(f'Transfer of Setbacks:{response}')