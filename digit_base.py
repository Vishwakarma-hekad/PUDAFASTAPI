from enum import Flag
from datetime import datetime

class LayerMaster(Flag):


	DWG_TEXT_MTEXT='TEXT or MTEXT'
	DWG_LWPOLYLINE='LWPOLYLINE'
	DWG_LWPOLY_CIRCLE='LWPOLYLINE or CIRCLE'
	DWG_ONLY_CLOSED_T=True
	DWG_ONLY_OPEN_T=True
	DWG_ONLY_CLOSED_F=False
	DWG_ONLY_OPEN_F=False
	
	## Building type can be existing or proposed 
	#existing - dont need to check for specific rules need only to extract dimensions of area/amenities 
	BLDG_TYPE_EXISTING = 'EXISTING'
	#Rules to be applied for proposed work layer elements 
	BLDG_TYPE_PROPOSED = 'PROPOSED'
	
	# type of plan 
	#residencial property 
	RESIDENCE = '_ResiBUAOutline' 
	#industrial 
	INDUSTRIAL = '_IndBUAOutline' 
	#commercial 
	COMMERCIAL = '_CommBUAOutline' 
	#special use : movie theatres etc 
	SPECIALUSE = '_SpecialUseBUAOutline' 

	#Oct 2022 	“_BUABeforeConcession” 
	BUA_BEFORE_CONCESSION ='_BUABeforeConcession'
	
	#plan_category 
	PLAN_CATEGORY_LIST={'Building': 'Buildings', 
						'OpenLayout':'OpenLayout', 
						'Industrial':'Industrial (Commercial)', 
						'SpecialUse':'SpecialUse (Hospitals, Educational, Multiplexes,Podium Buildings)',
						'OpenVillas_Layout':'OpenVillas_Layout' }
	
	#GLOBAL ACTIONS 
	#10/8/2023
	ACTION_CREATELAYERS_DWG_CMD='CreateLayersFromDwg'
	ACTION_GATED_COMMUNITY_SETBACKS_CMD='GatedCommunitySetbacks'   #if called explicitly
	ACTION_OTHER_CMD='Other'
	ACTION_NA_DEFAULT_CMD='NA'   #Default to bypass for internal calls 
	ACTION_FIRE_CMD='FirePlanScrutiny'   #02/01/2024

	#DRAWING_ACTIONS_SUPPORTED TYPES #10/8/2023 09/30/2023 
	#BUILDING_ACTIONS_LIST=['CreateLayersFromDwg','GatedCommunitySetbacks','Other', ACTION_FIRE_CMD]
	BUILDING_ACTIONS_LIST=[ACTION_CREATELAYERS_DWG_CMD, ACTION_GATED_COMMUNITY_SETBACKS_CMD,
							 ACTION_OTHER_CMD, ACTION_NA_DEFAULT_CMD,ACTION_FIRE_CMD]

	#DRAWING_ACTIONS_SUPPORTED TYPES #10/8/2023 09/30/2023 
	OPENLAYOUT_ACTIONS_LIST=[ACTION_CREATELAYERS_DWG_CMD,
							 ACTION_OTHER_CMD, ACTION_NA_DEFAULT_CMD]

	#DRAWING_ACTIONS_SUPPORTED TYPES 09/30/2023 
	DRAWING_ACTIONS_TYPE={'Building': BUILDING_ACTIONS_LIST , 
						'OpenLayout':OPENLAYOUT_ACTIONS_LIST }


	# To determine the MAX HEIGHTS #purposeCode to Name Mapping To determine the Stairs and abutting and setbacks 
	BUILDING_CATEGORY=[ 'STANDALONE', 'SUBPLOTS', 'NON_HIGHRISE', 'HIGHRISE_MSBR', 'VILLAS_ROWHOUSING', 'GROUP_HOUSING']
	
	#purposeCode to Name Mapping To determine the Stairs and abutting and setbacks  
	PURPOSE_CODE_DESC_MAP= {'A-4':'Apartment Homes',  'O-1':'Open Plots', 'A-1':'Lodging and Rooms',	'A-2':'One or Two Dwelling Units',
		'A-2a':'Villas/Rowhouses',	'A-3':'Dormitories', 'A-5':'Hotels', 'A-6':'Starred Hotels', 	
		'I-1':'Commerical Shops', 'S-1':'Educational',  'S-2':'Hospitals', 
		'S-3':'Institutional', 'S-4':'Assembly', 'S-5':'Multiplexes' ,'S-6':'Podium Buildings'
	}

	AUTHORITY_LIST=['HMDA']
	USE_LIST=['RESIDENTIAL','COMMERCIAL', 'INDUSTRIAL', 'INSTITUTIONAL_EDUCATIONAL', 'ASSEMBLY']
	HMDARESIDENTIAL=['Boarding', 'Bungalow', 'Dharamshalas', 'Dormitories', 'Farm House', 'Group Housing', 'Hostel', 'Individual Row House', 'Low income group and EWS Housing', 'Other reseidential Building', 'Residential Bldg/Apartment', 'Row House', 'Semidetached', 'Staff Quarters', 'Villa']
	HMDACOMMERCIAL=['3 Star Hotel', '4 Star Hotel', '5 Star Hotel', 'Bakery', 'Bank', 'Bio-Technology(BT) Park', 'Booth', 'Business Office', 'Call Centers', 'Cold Storage', 'Commerical Bldg', 'Convinience Shops', 'Corporate Commerical', 'Corporate Office', 'Court House', 'Cyber CafÃ©', 'Departmental Store', 'Gas Godown', 'Godowns', 'Good Storage', 'Holiday Resort', 'Hotel', 'IT Office', 'Information-Technology IT', 'Junk Yard', 'Kiosk', 'Lodging', 'Market', 'Office', 'Other Commerical Building', 'Parking Building (Parking Plaza)', 'Parlor', 'Pathological Lab', 'Petrol Filling Station(With Service Bay)', 'Petrol Filling Station(Without Service Bay)', 'Petrol Pump', 'Professional Office', 'Public Liabrary', 'Restaurant / Cafeteria', 'Retail Shop', 'Safe Deposite Vault', 'Service Station', 'Service or Repair establishments', 'Shop', 'Shop and Office', 'Shopping Center', 'Shopping Mall', 'Showroom', 'Store', 'Supermarkets', 'Traning Institute', 'Ware House', 'Wending Booth', 'Wholesale Commerical Market', 'Parking Complex (Parking Lot)']
	AUTH_USE_SUBUSE_MAP= {'HMDA_RESIDENTIAL':HMDARESIDENTIAL, 'HMDA_COMMERCIAL':HMDACOMMERCIAL , 'HMDA_INDUSTRIAL': 'Assembly Plant',
						 'HMDA_INSTITUTIONAL_EDUCATIONAL':	'Educational building', 'HMDA_ASSEMBLY':	'Multiplex'}
	LOCATION_CODE_DESC_MAP={'HMDA':'Extended area of Erstwhile HUDA (HMDA)', 
							'HUDA':'Erstwhile Hyderabad Urban Development Authority (HUDA)',
							'HADA':'Erstwhile Hyderabad Airport Development Authority (HADA)',
							'CDA':'Erstwhile Cyberabad Development Authority (CDA)',
							'ORRGC':'Outer Ring Road Growth Corridor (ORRGC)',
							'GHMC':'Erstwhile Municipal Corporation of Hyderabad Area(HMDA Core Area)'}

	SUBLOCATION_LIST=['1)New Areas/Approved layout Areas', '2)Congested Areas', '3)Settlement (Gram Kahntam/Abadi)', '4)Gram Panchayat With Revenue Survey'] 



	TRANSFORMER_MIN_REQUIRED_NO=1
	SOLAR_HEATER_MIN_REQUIRED_NO=1
	WASTER_WATER_MIN_REQUIRED_NO=1

	RULES_FOR_PLAN_TYPE={ 
		SPECIALUSE : ['HOSPITALS', 'HOTELS', 'NURSING HOMES'] }
	ACCESSORY_MANDATORY_RULES_BY_TYPE={
							
							'RESIDENTIAL' : 
								{'Distribution Transformers' : TRANSFORMER_MIN_REQUIRED_NO},
						 	
						 	'SPECIALUSE' : 
								{ 
							 	'Solar Water Heater' : SOLAR_HEATER_MIN_REQUIRED_NO , 
							 	'Waste Water Recyling' : WASTER_WATER_MIN_REQUIRED_NO },

							'INDUSTRIAL' : 
								{ 
							 	'Solar Water Heater' : SOLAR_HEATER_MIN_REQUIRED_NO , 
							 	'Waste Water Recyling' : WASTER_WATER_MIN_REQUIRED_NO },

							'COMMERCIAL' : 
								{ 
							 	'Solar Water Heater' : SOLAR_HEATER_MIN_REQUIRED_NO , 
							 	'Waste Water Recyling' : WASTER_WATER_MIN_REQUIRED_NO }
							}

	#PLOT Type 
	OPENLAYOUT = '_IndivSubPlot'
				  
	#REQUEST_PARAMS
	REQUEST_PARAMS='request_params'

	#Floor Area Ratio or Floor Space Index 1.5 etc 
	RESIFAR = '_ResiFAR'  

	#Elevation and Sectional Floors 
	SECTION = '_Section'
	SECTIONALITEM = '_SectionalItem'
	SECTIONLINE = '_SectionLine'

	BUILDINGNAME = '_BuildingName'

	FLOOR = '_Floor'
	FLOORINSECTION = '_FloorInSection'

	WINDOW = '_Window'
	DOOR = '_Door'
	COLUMN = '_Column'
	
	LIG = '_Lig'  #low income group 
	PROPOSEDWORK = '_ProposedWork'
	CARPETAREA = '_CarpetArea'
	ROOM = '_Room'

	SEWAGELINE = '_SewageLine'
	SLABCUTOUTVOID = '_SlabCutoutVoid'
	SANITATION = '_Sanitation'
	
	# can have 1 or more of : pathway, parking, accessory, stair , lift 
	PATHWAY = '_Pathway'
	PASSAGE = '_Passage'
	STAIRCASE ='_StairCase'
	RAMP = '_Ramp' 
	BALCONY = '_Balcony' 
	PARKING = '_Parking'
	LIFT = '_Lift'
	DOUBLE_HEIGHT= '_DoubleHeight'

	MORTGAGEAREA = '_MortgageArea'
	
	#Fix 5/12 Added for Final Approved Layouts 
	CYCLETRACK='_Cycletrack'
	UTILITY_MISC='_UMisic'

	#deductions from BUA Accessory use and Ventilation shaft 
	ACCESSORYUSE = '_AccessoryUse'
	VENTILATIONSHAFT = '_VentilationShaft'
	
	ORGOPENSPACE = '_OrganizedOpenSpace'
	GREENSTRIP= 'Green Strip'
	COMPOUNDWALL = '_CompoundWall'

	NETPLOT = '_NetPlot'
	PLOT = '_Plot'
	SPLAY = '_Splay'
	AREATABLE='_AREATABLE'
	MAINROAD = '_MainRoad'
	INTERNALROAD = '_InternalRoad'
	ROADWIDENING = '_RoadWidening'
	GRIDROAD='_GridRoad'	#Fix 8/22/2022
	SOCIALINFRA='_Amenity'
	MARGINLINE='_MarginLine'
	
	FRONTSETBACK='FRONT'  #color index 1 
	REARSETBACK='REAR'  #color index 6 
	SIDE1TSETBACK='SIDE1' #color index 104 
	SIDE2SETBACK='SIDE2'  #color index 5

	GROUNDLEVEL = '_GroundLevel'
	
	#floor types stilt/basement (where parking is primarily there)
	STILT_FLOOR = 'STILT'
	PARKING_FLOOR = 'PARKING'
	CELLAR_FLOOR = 'CELLAR'
	BASEMENT_FLOOR ='BASEMENT'
	#valid types of floor 
	
	# Normal floor has dwelling units, apartments, 
	# can have 1 or more of : passage, balcony, accessory, stair , lift 
	NORMAL_FLOOR = 'FLOOR'
	#In some cases this is present which has restaraunt, gym, etc 
	MEZAINE_FLOOR = 'MEZZAINE'
	TYPICAL_FLOOR = 'TYPICAL'
	# Terrace - normally no Built UpArea except lift and machine room 
	TERRACE_FLOOR = 'TERRACE'
	
	#TRANSFER OF SETBACKS Fix 6/20/2022
	#
	EXISTING_PLINTH_AREA='_Existingplintharea'
	PROPOSED_PLINTH_AREA='_ProposedPlintharea'

	## EXTERNAL STRUCTURES 
	RAILINE = '_RailLine'
	ELECTRICLINE = '_ElectricLine'
	EXISTINGSTRUCTURE = '_ExistingStructure'

	WATERBODIES = '_WaterBodies'
	WATERLINE = '_WaterLine'
	#OPEN LAYOUT 
	NALAROAD = '_NalaRoad'
	BUFFERZONE= '_BufferZone'

	RESERVEDAREA = '_ReservedArea'
	REFUGEAREA = '_RefugeArea'
	SURRENDERTOAUTH = '_SurrenderToAuthority'
	LEFTOVEROWNERSLAND= '_LeftoverOwnersLand'
	COURTYARD= '_Courtyard'

	#Transfer Of Setbacks Layers Oct 2022 
	TRANSFER_OF_SETBACKS='_TransferOfSetback'
	 

	# #PDF Queues
	# PDF_GEN_REQUEST_QUEUE='bpconnect_pdf_task_queue'
	# PDF_GEN_RESPONSE_QUEUE='bpconnect_pdf_resp_queue'
	#
	# #PDF GatedCommunity
	# PDF_GATED_COMMUNITY_LAYOUT_NAME='GatedCommunity'

acad2odaMap = { 'AC1004' : 'ACAD9', 'AC1006' : 'ACAD10', 'AC1009 ' : 'ACAD12', 'AC1012 ' : 'ACAD13', 'AC1014 ' : 'ACAD14', 
'AC1015 ' : 'ACAD2000', 'AC1018 ' : 'ACAD2004', 'AC1021 ' : 'ACAD2007', 'AC1024' : 'ACAD2010','AC1027' : 'ACAD2013', 'AC1032' : 'ACAD2018'}

# #toggle to 1 to disable logging for the level
# printLayers=0
# printEntities=0
# printDebug=1
# printWarning=0
# printVerbose=0

# JSON_SEP= ","
#
#
#
# def printLog(level, *msg):
#
# 	date_time = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
#
# 	if (printDebug == 0 and level == "debug"):
# 		print(date_time + " : [" + level + "] " +  str(msg))
# 	elif (printWarning == 0 and level == "warning"):
# 		print(date_time + " : [" + level + "] " +  str(msg))
# 	elif (printVerbose == 0 and level == "verbose"):
# 		print(date_time + " : [" + level + "] " +  str(msg))
# 	elif (level =="error" or level == "info"):
# 		print(date_time + " : [" + level + "] " + str(msg))
# 	else:
# 		return