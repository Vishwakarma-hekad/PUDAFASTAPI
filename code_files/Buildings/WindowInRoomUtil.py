import os
import ezdxf
import re
from shapely.geometry import Point,Polygon
import numpy as np
from datetime import datetime


class CheckWindowsINRoom:

	def Window_Height(self, text_data, window_label):
		# print(text_data, window_label)
		height = 0.0

		window_label = window_label.lower()

		for insert_entity in text_data:

			for entity in insert_entity.virtual_entities():

				if entity.dxftype() == 'MTEXT' or entity.dxftype() == 'TEXT':

					data_string = entity.dxf.text if entity.dxftype() == 'TEXT' else entity.plain_text()

					data_string = data_string.lower()

					# print(data_string)
					# Split data_string into lines

					lines = data_string.strip().split('\n')

					# Parse each line to extract key-value pairs
					data = {}
					for line in lines:
						key_value_pairs = line.split(', ')
						key = key_value_pairs[0].split(': ')[0]
						values = {pair.split(': ')[0]: float(pair.split(': ')[1]) for pair in key_value_pairs[1:]}
						data[key] = values
					# print(data)
					if data.get(window_label) is not None:
						# print(data.values())
						for x, value in data.items():

							if x == window_label:
								height = value.get('height')
		return height

	def BuildingName_layer(self, BuildingName_data):

		BuildingName_dict = dict()

		for BuildingName_entity in BuildingName_data:

			if BuildingName_entity.dxftype() == 'LWPOLYLINE':

				if len([fp[0:2] for fp in BuildingName_entity.get_points()]) > 3:

					BuildingName_polygon = Polygon(np.array([fp[0:2] for fp in BuildingName_entity.get_points()]))

					for BuildingName_entity in BuildingName_data:

						if BuildingName_entity.dxftype() == 'TEXT' or BuildingName_entity.dxftype() == 'MTEXT':

							BuildingName_id = BuildingName_entity.dxf.handle

							BuildingName_properties = BuildingName_entity.dxfattribs()

							BuildingName_text = BuildingName_properties.get(
								'text') if BuildingName_entity.dxftype() == 'TEXT' else BuildingName_entity.plain_text()

							BuildingName_text_pts = BuildingName_properties.get('insert')

							BuildingName_text_point = Point(
								np.array([BuildingName_text_pts[0], BuildingName_text_pts[1]]))

							if BuildingName_polygon.contains(
									BuildingName_text_point) == True or BuildingName_polygon.touches(
									BuildingName_text_point) == True or round(
								BuildingName_polygon.distance(BuildingName_text_point),
								1) == 0.0:
								BuildingName_dict[BuildingName_id] = [BuildingName_text, BuildingName_polygon]
		return BuildingName_dict

	def Floor_layer(self, Floor_data):

		floor_dict = dict()

		for floor_entity in Floor_data:

			if floor_entity.dxftype() == 'LWPOLYLINE':

				if len([fp[0:2] for fp in floor_entity.get_points()]) > 3:

					floor_polygon = Polygon(np.array([fp[0:2] for fp in floor_entity.get_points()]))

					for floor_entity in Floor_data:

						if floor_entity.dxftype() == 'TEXT' or floor_entity.dxftype() == 'MTEXT':

							floor_id = floor_entity.dxf.handle

							floor_properties = floor_entity.dxfattribs()

							floor_text = floor_properties.get(
								'text') if floor_entity.dxftype() == 'TEXT' else floor_entity.plain_text()

							floor_text_pts = floor_properties.get('insert')

							floor_text_point = Point(np.array([floor_text_pts[0], floor_text_pts[1]]))

							if floor_polygon.contains(floor_text_point) == True or floor_polygon.touches(
									floor_text_point) == True or round(floor_polygon.distance(floor_text_point),
																	   1) == 0.0:
								floor_dict[floor_id] = [floor_text, floor_polygon]
		return floor_dict

	def CarpetArea_layer(self, CarpetArea_data):

		CarpetArea_dict = dict()

		for CarpetArea_entity in CarpetArea_data:

			if CarpetArea_entity.dxftype() == 'LWPOLYLINE':

				if len([fp[0:2] for fp in CarpetArea_entity.get_points()]) > 3:

					CarpetArea_polygon = Polygon(np.array([fp[0:2] for fp in CarpetArea_entity.get_points()]))

					for CarpetArea_entity in CarpetArea_data:

						if CarpetArea_entity.dxftype() == 'TEXT' or CarpetArea_entity.dxftype() == 'MTEXT':

							CarpetArea_id = CarpetArea_entity.dxf.handle

							CarpetArea_properties = CarpetArea_entity.dxfattribs()

							CarpetArea_text = CarpetArea_properties.get(
								'text') if CarpetArea_entity.dxftype() == 'TEXT' else CarpetArea_entity.plain_text()

							CarpetArea_text_pts = CarpetArea_properties.get('insert')

							CarpetArea_text_point = Point(np.array([CarpetArea_text_pts[0], CarpetArea_text_pts[1]]))

							if CarpetArea_polygon.contains(CarpetArea_text_point) == True or CarpetArea_polygon.touches(
									CarpetArea_text_point) == True or round(
									CarpetArea_polygon.distance(CarpetArea_text_point), 1) == 0.0:
								CarpetArea_dict[CarpetArea_id] = [CarpetArea_text, CarpetArea_polygon]

		return CarpetArea_dict

	def Room_layer(self,Room_data):

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
				if polygon.contains(text_point) or polygon.touches(text_point) or round(polygon.distance(text_point),1) == 0.0:
					last_text = text  # same as your old logic

			if last_text:

				room_dict[poly_id] = [last_text, polygon]
			else:
				print(f'Room Polygon({poly_id}) Does Not contain Any Name')

		return room_dict

	def Window_layer(self, Window_data):

		window_dict = dict()

		for window_entity in Window_data:

			if window_entity.dxftype() == 'LWPOLYLINE':

				if len([wp[0:2] for wp in window_entity.get_points()]) > 3:

					windowpolygonID = window_entity.dxf.handle

					window_polygon = Polygon(np.array([wp[0:2] for wp in window_entity.get_points()]))

					window_containtext = []

					for window_entity in Window_data:

						if window_entity.dxftype() == 'TEXT' or window_entity.dxftype() == 'MTEXT':

							window_properties = window_entity.dxfattribs()

							window_text = window_properties.get(
								'text') if window_entity.dxftype() == 'TEXT' else window_entity.plain_text()

							window_text_pts = window_properties.get('insert')

							window_text_point = Point(np.array([window_text_pts[0], window_text_pts[1]]))

							if window_polygon.contains(window_text_point) == True or window_polygon.touches(
									window_text_point) == True or round(window_polygon.distance(window_text_point),
																		1) == 0.0:
								window_containtext.append([window_text, window_polygon])

					if window_containtext != [] and len(window_containtext) > 0:

						for windowtextpoly in window_containtext:
							window_dict[windowpolygonID] = windowtextpoly
					else:

						print(f'Window Polygon({windowpolygonID}) not Contain Any Name ')

		return window_dict

	def CheckWindowInRoom(self, msp):

		returnValuDict = dict()

		if msp is None:
			return returnValuDict

		try:

			building_data = msp.query('*[layer=="_BuildingName"]')

			BuildingNameDict = self.BuildingName_layer(building_data)

			room_data = msp.query('*[layer=="_Room"]')

			RoomDict = self.Room_layer(room_data)

			window_data = msp.query('*[layer=="_Window"]')

			WindowDict = self.Window_layer(window_data)

			floor_data = msp.query('*[layer=="_Floor"]')

			FloorDict = self.Floor_layer(floor_data)

			carpetarea_data = msp.query('*[layer=="_CarpetArea"]')

			CarpetAreaDict = self.CarpetArea_layer(carpetarea_data)

			printadditiondetals_data = msp.query('INSERT[layer=="_PrintAdditionalDetail"]')

			resultsList = []

			for Building_id, BuildingNamepoly in BuildingNameDict.items():

				for floor_id, floorNamepoly in FloorDict.items():

					if BuildingNamepoly[1].contains(floorNamepoly[1]) == True:

						FloorContainsRoom = []

						for room_id, roomNamePoly in RoomDict.items():

							if floorNamepoly[1].contains(roomNamePoly[1]) == True:
								FloorContainsRoom.append((room_id, roomNamePoly))

						FloorContainsWindows = []

						for window_id, windowNamePoly in WindowDict.items():

							if floorNamepoly[1].contains(windowNamePoly[1]) == True:
								FloorContainsWindows.append([window_id, windowNamePoly])

						if (FloorContainsRoom != [] and len(FloorContainsRoom) > 0) and (
								FloorContainsWindows != [] and len(FloorContainsWindows) > 0):

							for room_id, floorRoom in FloorContainsRoom:

								for CarpetArea_id, CarpetAreaNamePoly in CarpetAreaDict.items():

									if CarpetAreaNamePoly[1].contains(floorRoom[1]) == True or round(
											CarpetAreaNamePoly[1].distance(floorRoom[1]), 1) == 0.0:

										Room_Area = round(floorRoom[1].area, 2)

										room_joinedWindow = []

										for floorWindow in FloorContainsWindows:

											fwindowID, fwindowNamePoly = floorWindow[0], floorWindow[1]

											if floorRoom[1].touches(fwindowNamePoly[1]) == True or round(
													floorRoom[1].distance(fwindowNamePoly[1]), 1) == 0.0:
												room_joinedWindow.append([fwindowID, fwindowNamePoly])

										if room_joinedWindow != [] and len(room_joinedWindow) > 0:

											count = 1

											for attachedWindowData in room_joinedWindow:
												Joinwindow_id, joinwindowNamePoly = attachedWindowData[0], \
												attachedWindowData[1]

												window_heightdata = self.Window_Height(printadditiondetals_data,
																					   joinwindowNamePoly[0])

												window_height = 0.0 if window_heightdata is None else window_heightdata

												window_length = round(joinwindowNamePoly[1].length / 2, 2)

												window_area = round(window_length * window_height, 2)

												tmpdict = dict()

												tmpdict["BUILDING_ID"] = str(Building_id)

												tmpdict["BUILDING_LABEL"] = str(BuildingNamepoly[0])

												tmpdict["FLOOR_ID"] = str(floor_id)

												tmpdict["FLOOR_LABEL"] = str(floorNamepoly[0])

												tmpdict["CARPETAREA_ID"] = str(CarpetArea_id)

												tmpdict["CARPETAREA_LABEL"] = str(CarpetAreaNamePoly[0])

												tmpdict["ROOM_ID"] = str(room_id)

												tmpdict["ROOM_LABEL"] = str(floorRoom[0]).replace('\n', '')

												tmpdict["ROOM_AREA"] = str(Room_Area)

												tmpdict["WINDOW_ID"] = str(Joinwindow_id)

												tmpdict["WINDOW_LABEL"] = str(joinwindowNamePoly[0])

												tmpdict["WINDOW_LENGTH"] = str(window_length)

												tmpdict["WINDOW_AREA"] = str(window_area)

												tmpdict["WINDOW_TOUCHED_COUNT"] = str(count)

												resultsList.append(tmpdict)

												count += 1

										else:

											print(
												f'Any Window/Ventilation not attached to this {floorRoom[0]} in {CarpetAreaNamePoly[0]} of {floorNamepoly[0]} ')

			if resultsList != [] and len(resultsList) > 0:
				# print(len(resultsList))
				returnValuDict['code'] = 0
				returnValuDict['data'] = resultsList

			else:

				returnValuDict['code'] = 1
				returnValuDict['data'] = resultsList

		except IOError:

			print(f'Not a DXF file or a generic I/O error.')

			return returnValuDict

		except ezdxf.DXFStructureError:
			print(f'Invalid or corrupted DXF file.')
			return returnValuDict

		finally:
			print('Process Complete Successfully ')

		return returnValuDict


# #path of the filename
# folder=r"C:\Users\manisha\Desktop\building_height_files(26-11-25)\setback(04-03-26)_files\dxf_files"
#
# filename="CH.dxf"
#
# file_path=os.path.join(folder,filename)
#
# start_time=datetime.now()
#
# t1 = start_time.strftime("%H:%M:%S")
#
# first_start_time=datetime.strptime(t1,"%H:%M:%S")
#
# read_dxf=ezdxf.readfile(file_path)
#
# msp=read_dxf.modelspace()
#
# response=CheckWindowsINRoom().CheckWindowInRoom(msp)
#
# end_time=datetime.now()
#
# t2=end_time.strftime("%H:%M:%S")
#
# last_end_time=datetime.strptime(t2,"%H:%M:%S")
#
# total_time=last_end_time-first_start_time
#
# print (f'Room and Windows Response:\n{response}\nTotal Time is:{total_time}')