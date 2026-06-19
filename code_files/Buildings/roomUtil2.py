import os.path

import ezdxf
from datetime import datetime

import numpy as np

from shapely.geometry import Polygon,Point

def Floor_layer(Floor_data):

	floor_dict = dict()

	for floor_entity in Floor_data:

		if floor_entity.dxftype() == 'LWPOLYLINE':

			if len([fp[0:2] for fp in floor_entity.get_points()])>3:

				floor_polygon = Polygon(np.array([fp[0:2] for fp in floor_entity.get_points()]))

				for floor_entity in Floor_data:

					if floor_entity.dxftype() == 'TEXT' or floor_entity.dxftype() == 'MTEXT':

						floor_id = floor_entity.dxf.handle

						floor_properties = floor_entity.dxfattribs()

						floor_text = floor_properties.get('text') if floor_entity.dxftype() == 'TEXT' else floor_entity.plain_text()

						floor_text_pts = floor_properties.get('insert')

						floor_text_point = Point(np.array([floor_text_pts[0], floor_text_pts[1]]))

						if floor_polygon.contains(floor_text_point) == True or floor_polygon.touches(floor_text_point) == True or round(floor_polygon.distance(floor_text_point), 1) == 0.0:

							floor_dict[floor_id] = [floor_text, floor_polygon]
	return floor_dict

def Room_layer(Room_data):

    room_dict = {}

    polygons = []
    texts = []

    # STEP 1: Separate polygons and texts (ONLY ONCE)
    for entity in Room_data:

        if entity.dxftype() == 'LWPOLYLINE':
            pts = [rp[0:2] for rp in entity.get_points()]
            if len(pts) > 3:
                polygons.append((entity.dxf.handle, Polygon(pts)))

        elif entity.dxftype() in ['TEXT', 'MTEXT']:
            props = entity.dxfattribs()

            text = props.get('text') if entity.dxftype() == 'TEXT' else entity.plain_text()

            # CLEAN TEXT (your logic)
            text = text.replace('^J', ' ')
            text = text.replace('\\Pa', ' ')
            text = text.replace('\\P', ',')
            text = text.replace("\n", '')

            insert = props.get('insert')
            if insert:
                point = Point(insert[0], insert[1])
                texts.append((text, point))

    #  STEP 2: Match polygon with text (FAST)
    for poly_id, polygon in polygons:

        #  Bounding box (VERY FAST FILTER)
        minx, miny, maxx, maxy = polygon.bounds

        last_text = None

        for text, text_point in texts:

            # ⚡ Fast reject (90% cases skip here)
            if not (minx <= text_point.x <= maxx and miny <= text_point.y <= maxy):
                continue

            # Actual check
            if polygon.contains(text_point) or polygon.touches(text_point) or round(polygon.distance(text_point),1)==0.0:
                last_text = text   # same as your old logic

        if last_text:
            room_dict[poly_id] = [last_text, polygon]
        else:
            print(f'Room Polygon({poly_id}) Does Not contain Any Name')

    return room_dict

def Window_layer(Window_data):

	window_dict = dict()

	for window_entity in Window_data:

		if window_entity.dxftype() == 'LWPOLYLINE':

			if len([wp[0:2] for wp in window_entity.get_points()])>3:

				windowpolygonID=window_entity.dxf.handle

				window_polygon = Polygon(np.array([wp[0:2] for wp in window_entity.get_points()]))

				window_containtext=[]

				for window_entity in Window_data:

					if window_entity.dxftype() == 'TEXT' or window_entity.dxftype() == 'MTEXT':

						window_properties = window_entity.dxfattribs()

						window_text = window_properties.get('text') if window_entity.dxftype() == 'TEXT' else window_entity.plain_text()

						window_text_pts = window_properties.get('insert')

						window_text_point = Point(np.array([window_text_pts[0], window_text_pts[1]]))

						if window_polygon.contains(window_text_point) == True or window_polygon.touches(window_text_point) == True or round(window_polygon.distance(window_text_point), 1) == 0.0:

							window_containtext.append([window_text, window_polygon])

				if window_containtext!=[] and len(window_containtext)>0:

					for windowtextpoly in window_containtext:

						window_dict[windowpolygonID] = windowtextpoly
				else:

					print(f'Window Polygon({windowpolygonID}) not Contain Any Name ')

	return window_dict

def window_check(msp):

	date_format="%Y-%m-%d %H:%M:%S"

	duplicateList=[]
	errorList=[]

	returnValueDict=dict()

	if (msp is None):

		return returnValueDict

	try:

		print('read file')

		print("===loading room layer")
		room_data=msp.query('*[layer=="_Room"]')

		print("====== loading window layer")
		window_data=msp.query('*[layer=="_Window"]')

		print("====== loading floor layer")
		floor_data=msp.query('*[layer=="_Floor"]')

		print('---- processing floor data')
		floorDataDict=Floor_layer(floor_data)

		print('-----processing room data')
		roomDataDict=Room_layer(room_data)

		print('-------processing window data')
		windowDataDict=Window_layer(window_data)

		for floor_id,floorNamepoly in floorDataDict.items():

			FloorContainsRoom=[]

			for room_id,roomNamePoly in roomDataDict.items():

				if floorNamepoly[1].contains(roomNamePoly[1])==True:

					FloorContainsRoom.append(roomNamePoly)

			FloorContainsWindows=[]

			for window_id,windowNamePoly in windowDataDict.items():

				if floorNamepoly[1].contains(windowNamePoly[1])==True:

					FloorContainsWindows.append([window_id,windowNamePoly])

			if (FloorContainsRoom!=[] and len(FloorContainsRoom)>0) and (FloorContainsWindows!=[] and len(FloorContainsWindows)>0):

				for floorRoom in FloorContainsRoom:

					room_joinedWindow = []

					for floorWindow in FloorContainsWindows:

						fwindowID,fwindowNamePoly=floorWindow[0],floorWindow[1]

						if floorRoom[1].touches(fwindowNamePoly[1])==True or round(floorRoom[1].distance(fwindowNamePoly[1]),1)==0.0:

								room_joinedWindow.append([fwindowID,fwindowNamePoly])

					if room_joinedWindow!=[] or len(room_joinedWindow)>0:

						for attachedWindowData in room_joinedWindow:

							Joinwindow_id,joinwindowNamePoly=attachedWindowData[0],attachedWindowData[1]

							if (returnValueDict.get(Joinwindow_id, 0) == 0):

								returnValueDict[Joinwindow_id] = f'{floorRoom[0]},{joinwindowNamePoly[0]},{round(joinwindowNamePoly[1].length/2,2)}'

							else:

								duplicateList.append(f"Duplicate Room {floorRoom[0]} with same Reference# {Joinwindow_id}")

					else:

						errorList.append(f'No Window/Ventilation not attached to this {floorRoom[0]} in {floorNamepoly[0]}')

	except IOError:

		print(f'Not a DXF file or a generic I/O error.')
		return returnValueDict

	except ezdxf.DXFStructureError:
		print(f'Invalid or corrupted DXF file.')
		return returnValueDict

	finally:

		print('Process Complete Successfully ')

		if (len(duplicateList)> 0):

			returnValueDict['duplicateList']=duplicateList

		if (len(errorList) > 0):

			returnValueDict['errorList']=errorList

	return returnValueDict

# #path of the filename
# # folder=r"C:\Users\manisha\Desktop\building_height_files(26-11-25)\setback(04-03-26)_files\dxf_files"
# folder=r"G:\MyProjects\BPConnectProject\BPConnectAPI\DXF_files"
#
# filename="a45fba5b8831c02-1562925ab6855401-3205pudafinal.dxf"
# #Pass extension - removed inside method
# start_time=datetime.now()
# t1 = start_time.strftime("%H:%M:%S")
#
# first_start_time=datetime.strptime(t1,"%H:%M:%S")
#
# #method returns a dict with handle
#
# dxf_file=ezdxf.readfile(os.path.join(folder,filename))
#
# msp=dxf_file.modelspace()
#
# response=window_check(msp)
#
# print ('Room and Windows Response ' , response )
# end_time=datetime.now()
#
# t2=end_time.strftime("%H:%M:%S")
#
# last_end_time=datetime.strptime(t2,"%H:%M:%S")
#
# total_time=last_end_time-first_start_time
# print(f'Total Time is:{total_time}')