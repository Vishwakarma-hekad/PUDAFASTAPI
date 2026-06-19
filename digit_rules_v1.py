from durable.lang import ruleset,post,when_all,m,engine,when_any

from digit_utils_buildings import getBuildingSubTypes

##SECTION#1
### ERROR MESSAGES BY RULE 
purposecodeList= ['A-4', 'O-1', 'A-1', 'A-2', 'A-2a', 'A-3', 'A-5', 'A-6', 'I-1', 'S-1', 'S-2', 'S-3', 'S-4', 'S-5','S-6']
subtypesList=['STANDALONE', 'NON_HIGHRISE', 'HIGHRISE_MSBR', 'VILLAS_ROWHOUSING', 'GROUP_HOUSING'] #Not Applicable for OpenPlots 
allSubtypesList=getBuildingSubTypes() 

RULES_PARAMS=dict()

RULES_PARAMS['ts-mortgage']=r"Require a) plan_type: Open_Layout or Buidling_Layout and b) proposed_mortgage_factor \
			c) Building_Layout require plot_area and building_height params "

RULES_PARAMS['ts-splay']="Require a) 'Roadwidth' Abutting  b) 'length' of splay c) 'width' of splay "

RULES_PARAMS['ts-staircase']=r"Require a) 'purpose_code': Purpose codes valid values are " + str(purposecodeList) + \
		  "b) proposed_flight_width : float , c) proposed_tread_width :float d)proposed_riser_height : float values"

RULES_PARAMS['ts-setbacks']=r"Require a) 'subtype': Building Subtype valid values are " + str(subtypesList) + \
		  "b) site_area: float, c) proposed_bldg_height : float , d) proposed_abutting_road_width:float, e) proposed_front_setback:float f) proposed_side1_setback:float, g) proposed_side2_setback:float "

RULES_PARAMS['ts-org-openspace']=r"Require a) 'subtype': Building Subtype valid values are " + str(allSubtypesList) + \
		  "b) site_area: float, c) proposed_tot_factor :float, d) proposed_tot_width:float, e) proposed_tot_area:float, f) proposed_greenstrip_width :float "

RULES_PARAMS['ts-parking']=r"Require a) 'subtype': Building Subtype valid values are " + str(subtypesList) + \
		  "b) site_area: float, c) proposed_parking_factor:float, d) proposed_visitor_parking_factor:float  "

#PASSAGE RULES
#Fix 7/18/2022 Revised the min. passage width to 1.5
# Purpose code 			Description 											Passage Width in mt.
#	A-1,A-2,A-2a,A-4	Residential buildings, dwelling unit type						1.5
#	A-3					Residential buildings (hostels)									1.5
#	A-5,A-6,S-1,I-1		All other buildings including hotels							1.5
#	S-3,S-4,S-5			Assembly buildings like auditorium theatres and cinemas			2.0
# 	S-2					Hospital, Nursing Homes											2.4
with ruleset('ts-passage'):
	@when_all(m.plan_type == 'Building_Layout')
	def passage_width_checks(c):
		c.s.result=''
		results=dict()
		required_passage_width=1.5  #default
		invalidInput=False

		results['proposed_passage_width']=float(c.m.proposed_passage_width)
		results['plan_type']=c.m.plan_type
		results['authority']=c.m.authority
		#Fix 7/18/2022 Min Passage width set to 1.5
		if (c.m.purpose_code in ['A-1','A-2','A-2a','A-4'] ):
			rule_head='Residential buildings, dwelling unit type (Except Hostels)'
			required_passage_width=1.5
		#Fix 7/18/2022 Min Passage width set to 1.5
		elif (c.m.purpose_code in ['A-3'] ):
			rule_head='Residential buildings (Hostels)'
			required_passage_width=1.5

		elif (c.m.purpose_code in ['A-5','A-6','S-1','I-1','S-6'] ):
			rule_head='All other buildings including Hotels'
			required_passage_width=1.5

		elif (c.m.purpose_code in ['S-3','S-4','S-5'] ):
			rule_head='Assembly buildings like auditorium theatres and cinemas'
			required_passage_width=2.0

		elif (c.m.purpose_code in ['S-2'] ):
			rule_head='Hospital, Nursing Homes,etc.'
			required_passage_width=2.4

		else:
			rule_head='Unknown Purpose code # ' + str(c.m.purpose_code) +  '. Default value will be applied.'
			required_passage_width=1.5

		results['required_passage_width_min']=required_passage_width


		rule_txt="As per NBC within Authority {0} for {1} Min. Passage Width required is {2} mts.".format(
			c.m.authority,rule_head, required_passage_width)


		# print("rule proposed_passage_width ")
		if (float(c.m.proposed_passage_width) >= required_passage_width):
			results['status']="OK"
		else:
			results['status']="NOT OK"

		# print(str(results))
		results['zrule']=rule_txt
		c.s.result=results



# MORTGAGE RULES  
# OPEN_LAYOUT AND BUILDING_PLANS 

with ruleset('ts-mortgage'):
	""" based on Type, Size of Plot and Height of Building
		factor:
		type: Open_Layout, Building_Layout/GroupHousing/MSBR/etc
		a) if Open Layout :  15%

		b) if Buildings: Size of Plot <200 sq. mt. and Height of Building (excludes Stilt/cellar) <=7 mt.: 0 otherwise 10%
		Area <200 Sq. mt. and Height <=7 mt. :  0%  Exempted
		Area >200 Sq. mt. and Height >7 mt. :  10%

"""

	# @when_any(m.plan_type is None  or m.proposed_mortgage_factor is None or  m.plan_type not in ['Open_Layout','Building_Layout'] )
	# def invalid(c):
	# 	c.s.exception="Require plan_type [Open_Layout or Buidling_Layout] and proposed_mortgage_factor \
	# 		for Building_Layout require plot_area and building_height "
	# 	raise engine.MessageNotHandledException(c.s.exception)

	# # when the exception property exists
	# @when_all(+s.exception)
	# def invalid_input(c):
	# 	print(c.s.exception)
	# 	c.s.exception = None
	# 	results={"status":"ERROR", "msg" :"Missing values Roadwidth/splay len/splay width" + str(m.roadwidth.value) + "/" + str(m.length) + "/" + str(m.width)}
	# 	return results


	@when_all(m.plan_type=='Open_Layout' )
	def openlayout_mortgage(c):
		c.s.result=''
		results=dict()
		results['proposed_mortgage_factor']=float(c.m.proposed_mortgage_factor)
		results['plan_type']=c.m.plan_type
		results['required_mortgage_factor']=15.0

		# print("rule openlayout_mortgage ")
		if (float(c.m.proposed_mortgage_factor) >= float(results['required_mortgage_factor']) ):
			results['status']="OK"
		else:
			results['status']="NOT OK"

		# print(str(results))
		results['zrule']=r'As per Rule No.5, G.O.Ms.No.168. a) For Open Layout: Mortgage Required : 15% of Plotted Area.'
		c.s.result=results


	@when_all(m.plan_type=='Building_Layout' )
	def building_non_exempted_mortgage1(c):
		# print("rule building_non_exempted_mortage ")

		c.s.result=''
		results=dict()
		results['plan_type']=c.m.plan_type
		results['proposed_mortgage_factor'] = float(c.m.proposed_mortgage_factor)
		results['plot_area']=c.m.plot_area
		results['building_height']=c.m.building_height

		if (c.m.plot_area < 200 and c.m.building_height <= 7):
			mortgage_factor_required=0.0
		elif (c.m.plot_area >= 200 and c.m.building_height > 7):
			mortgage_factor_required=10.0
		elif (c.m.plot_area >= 200 and c.m.building_height <= 7):
			mortgage_factor_required=10.0
		else:
			mortgage_factor_required=10.0

		results['required_mortgage_factor'] = mortgage_factor_required
		if (c.m.proposed_mortgage_factor >= mortgage_factor_required ):
			results['status']="OK"

		else:
			results['status']="NOT OK"

		# print(str(results))
		results['zrule']=r"As per Rule No.5, G.O.Ms.No.168. a). For Building Plans: Based on Plot sizes below 200 sq.Mts and building height up to 7mt - Mortgage is exempted. b). Plot sizes > 200 sq.Mts and/or building height > 7 mt. Mortgage is 10% of BUA (built-up area)"
		c.s.result=results

#### STAIR CASE RULE SET --BEGIN

with ruleset('ts-staircase'):

	## VILLAS AND SINGLE OR TWO DWELLING UNITS
	@when_any(m.purpose_code.matches ('A-2.*' ) )
	def villas_or_single_dwelling_rules(c):
		# print("rule stairs ")
		c.s.result=''
		results=dict()
		results['purpose_code']=c.m.purpose_code
		results['proposed_flight_width'] =c.m.proposed_flight_width
		results['proposed_tread_width'] =c.m.proposed_tread_width
		results['proposed_riser_height']=c.m.proposed_riser_height

		if (c.m.authority == 'DTCP'):
			if (c.m.purpose_code in ['A-2a']):  #villas
				min_flight_width_required=0.75
				min_tread_width_required=0.25
				max_riser_height_required=0.19
			elif (c.m.purpose_code in ['A-2']): #singel or two dwellings
				min_flight_width_required=1.0
				min_tread_width_required=0.25
				max_riser_height_required=0.19
		else:
			if (c.m.purpose_code in ['A-2a']):  #villas
				min_flight_width_required=0.75
				min_tread_width_required=0.25
				max_riser_height_required=0.19
			elif (c.m.purpose_code in ['A-2']): #singel or two dwellings
				min_flight_width_required=1.0
				min_tread_width_required=0.25
				max_riser_height_required=0.19


		results['required_flight_width_min'] = min_flight_width_required
		results['required_tread_width_min'] =  min_tread_width_required
		results['required_riser_height_max'] = max_riser_height_required

		if (c.m.proposed_flight_width  >= min_flight_width_required and
			c.m.proposed_tread_width >= min_tread_width_required and
			c.m.proposed_riser_height <= max_riser_height_required  ):
			results['status']="OK"

		else:
			results['status']="NOT OK"

		results['zrule']=r"As per Rule No .5, G.O.Ms.No .168. Determined based on purpose code/usage of the building a) (Purpose Codes, MIN. Flight Width, MIN. Tread Width, MAX Riser Height) in meters #1 (A-2 Single or Two Dwelling Units, 1.0,.25,.19) #2 (A-2a Villas,.75,.25,19) b)Max No. of Risers Per Flight 12"
		c.s.result=results

	## ['A-1', 'A-4',  'A-3', 'N/A']): #lodgings, apartments homes, dormitories, default n/a
	@when_any( ( m.purpose_code==  'A-1') |  (m.purpose_code=='A-4') |
				 (m.purpose_code=='A-3') | (m.purpose_code == 'N/A' ) )
	def lodging_apartments_dorms_default_rules(c):
		# print("rule stairs ")
		c.s.result=''
		results=dict()
		results['purpose_code']=c.m.purpose_code
		results['proposed_flight_width'] =c.m.proposed_flight_width
		results['proposed_tread_width'] =c.m.proposed_tread_width
		results['proposed_riser_height']=c.m.proposed_riser_height

		if (c.m.authority == 'DTCP'):
			min_flight_width_required=1
			min_tread_width_required=0.25
			max_riser_height_required=0.19
		else:
			min_flight_width_required=1.25
			min_tread_width_required=0.25
			max_riser_height_required=0.19



		results['required_flight_width_min'] = min_flight_width_required
		results['required_tread_width_min'] =  min_tread_width_required
		results['required_riser_height_max'] = max_riser_height_required

		if (c.m.proposed_flight_width  >= min_flight_width_required and
			c.m.proposed_tread_width >= min_tread_width_required and
			c.m.proposed_riser_height <= max_riser_height_required  ):
			results['status']="OK"

		else:
			results['status']="NOT OK"

		results['zrule']=r"As per Rule No .5, G.O.Ms.No .168. Determined based on purpose code/usage of the building a) (Purpose Codes, MIN. Flight Width, MIN. Tread Width, MAX Riser Height) in meters #1 A-1 lodgings/ A-4 apartments homes/ A-3 Dormitories/Default Residential, 1.25, .25, .19) b)Max No. of Risers Per Flight 12 "
		c.s.result=results

	## #hotels, starred hotels, commerical shops
	@when_all( (m.purpose_code == 'A-5') |  (m.purpose_code ==  'A-6') | (m.purpose_code ==  'I-1') | (m.purpose_code ==  'S-5') )
	def hotels_starred_hotels_commercial_rules(c):
		# print("rule stairs ")
		c.s.result=''
		results=dict()
		results['purpose_code']=c.m.purpose_code
		results['proposed_flight_width'] =c.m.proposed_flight_width
		results['proposed_tread_width'] =c.m.proposed_tread_width
		results['proposed_riser_height']=c.m.proposed_riser_height


		min_flight_width_required=1.5
		min_tread_width_required=0.30
		max_riser_height_required=0.15

		results['required_flight_width_min'] = min_flight_width_required
		results['required_tread_width_min'] =  min_tread_width_required
		results['required_riser_height_max'] = max_riser_height_required

		if (c.m.proposed_flight_width  >= min_flight_width_required and
			c.m.proposed_tread_width >= min_tread_width_required and
			c.m.proposed_riser_height <= max_riser_height_required  ):
			results['status']="OK"

		else:
			results['status']="NOT OK"

		results['zrule']=r"As per Rule No .5, G.O.Ms.No .168. Determined based on purpose code/usage of the building a) (Purpose Codes, MIN. Flight Width, MIN. Tread Width, MAX Riser Height) in meters #1 A-5 Hotels/ A-6 Starred Hotels/ I-1 Commercial Shops, 1.5, .30, .15). b)Max No. of Risers Per Flight 12"
		c.s.result=results

	#Educational, hospitals, institutional,assembly,multiplexes
	#S-1 through S-5
	@when_all((m.purpose_code == 'S-1') |  (m.purpose_code ==  'S-2') | (m.purpose_code ==  'S-3') |
			(m.purpose_code == 'S-4') |  (m.purpose_code ==  'S-5')  )
	def edu_hospitals_institutes_etc_rules(c):
		# print("rule stairs ")
		c.s.result=''
		results=dict()
		results['purpose_code']=c.m.purpose_code
		results['proposed_flight_width'] =c.m.proposed_flight_width
		results['proposed_tread_width'] =c.m.proposed_tread_width
		results['proposed_riser_height']=c.m.proposed_riser_height
		results['authority']=c.m.authority


		min_flight_width_required=2.0
		min_tread_width_required=0.30
		max_riser_height_required=0.15

		results['required_flight_width_min'] = min_flight_width_required
		results['required_tread_width_min'] =  min_tread_width_required
		results['required_riser_height_max'] = max_riser_height_required

		if (c.m.proposed_flight_width  >= min_flight_width_required and
			c.m.proposed_tread_width >= min_tread_width_required and
			c.m.proposed_riser_height <= max_riser_height_required  ):
			results['status']="OK"

		else:
			results['status']="NOT OK"

		results['zrule']=r"As per Rule No .5, G.O.Ms.No .168. Determined based on purpose code/usage of the building a) (Purpose Codes, MIN. Flight Width, MIN. Tread Width, MAX Riser Height) in meters #1 S-1 Educational / S-2 Hospitals / S-3 Instittional /S-4 Assembly / S-5 Multiplexes /S-6 Podium Buildings=  2.0, .30, .15 b)Max No. of Risers Per Flight 12"
		c.s.result=results

### ORG. OPEN SPACE 
# 
# ____________________________________________________________________________________________________________________________
# Type of Plan/Building 	Net Plot Area	TOT Factor	 Green Strip			Min. TOT Width 		Min. TOT Area
# __Unit of Measure___________sq.mt__________%____________mt____________________mt__________________sq.mt_________________________
# Open Layout				 Any 			 7.5  		-					 	3					50 
# Small Buildings 			<500 sq. mt      0			1 mt. around boundary   0					0		
# Villas/Rowhouses(Overall)	Any				 7.5		0						3					50
# Standalone/Buildings		>500 sq mt. 	 10 		1 mt. around boundary   3					15
# GROUP Housing				<2000 sq. mt.	 5			1 mt. around boundary   3					15
# GROUP Housing 			>2000 sq. mt.	 10			1 mt. around boundary  	3					15

# inputs:
# subtype, sitearea
#outputs :
# returns the tot factor , green strip requirement, tot width, tot area requirements 

with ruleset('ts-org-openspace'):
	@when_all(( m.subtype ==  'SUBPLOTS' ) | (m.subtype == 'VILLAS_ROWHOUSING') )
	def open_layouts(c):
		# print(" org openspace rules  ")
		c.s.result=''
		results=dict()
		results['subtype']=c.m.subtype
		results['proposed_site_area'] =c.m.proposed_site_area
		results['proposed_tot_factor']=c.m.proposed_tot_factor
		results['proposed_tot_width']=c.m.proposed_tot_width
		results['proposed_tot_area']=c.m.proposed_tot_area
		results['proposed_greenstrip_width']=c.m.proposed_greenstrip_width

		rule_head="As per Rule No .5, G.O.Ms.No .168."
		if c.m.authority is not None and c.m.authority == 'DTCP':
			required_tot_factor=9
			required_tot_width=3.0
			required_tot_area=50.0
			required_greenstrip_width=0.0
			rule_head="As per Rule No .5, G.O.Ms.No .105."
		else:
			required_tot_factor=7.5
			required_tot_width=3.0
			required_tot_area=50.0
			required_greenstrip_width=0.0



		#rule_txt=""

		rule_txt="For Authority {0} and type {1} Min. Org. Openspace Required {2}% , each TOT space with a Min. width of {3} mt. and area of {4} sq.mt. Greenstrip width around boundary is {5} mt. i.e. Exempted".format(
			c.m.authority, c.m.subtype, required_tot_factor,required_tot_width,required_tot_area,required_greenstrip_width)

		results['required_tot_factor'] = required_tot_factor
		results['required_tot_width'] = required_tot_width
		results['required_tot_area']=required_tot_area
		results['required_greenstrip_width']= required_greenstrip_width

		if (c.m.proposed_tot_factor >= required_tot_factor and c.m.proposed_tot_width >= required_tot_width and
			c.m.proposed_tot_area >= required_tot_area and c.m.proposed_greenstrip_width >= required_greenstrip_width
		  ):
			results['status']="OK"
		else:
			results['status']="NOT OK"

		results['zrule']= rule_head + rule_txt

		c.s.result=results

	@when_all( (m.subtype == 'STANDALONE') | (m.subtype == 'NON_HIGHRISE') | (m.subtype ==  'HIGHRISE_MSBR')  )
	def buildings_layouts(c):
		# print(" org openspace rules  ")
		c.s.result=''
		results=dict()
		results['subtype']=c.m.subtype
		results['proposed_site_area'] =c.m.proposed_site_area
		results['proposed_tot_factor']=c.m.proposed_tot_factor
		results['proposed_tot_width']=c.m.proposed_tot_width
		results['proposed_tot_area']=c.m.proposed_tot_area
		results['proposed_greenstrip_width']=c.m.proposed_greenstrip_width

		area_250threshold=250
		area_750threshold=750
		area_4kthreshold=4000

		#if msbr greenstrip width is 2 m. else 1m
		if (c.m.subtype ==  'HIGHRISE_MSBR'):
			required_greenstrip_width=2.0
		else:
			required_greenstrip_width=1.0


		if (c.m.proposed_site_area <= area_750threshold ):
			required_tot_factor=0
			required_tot_width=0
			required_tot_area=0
			#required_greenstrip_width=1.0
			rule_txt="For {0} and Site Area upto {1} sq.mt. Min. Org. Openspace/Tot width and Tot area are Exempted. Greenstrip width around boundary is {2} mt. ".format(
			c.m.subtype, area_750threshold, required_greenstrip_width)

		elif (c.m.proposed_site_area > area_750threshold and c.m.proposed_site_area <= area_4kthreshold ):	#|  m.subtype == 'NON_HIGHRISE' disable 2/19
			required_tot_factor=5
			required_tot_width=3.0
			required_tot_area=15.0
			#required_greenstrip_width=1.0
			rule_txt="For {0} and Site Area between {1} and {2} sq.mt. Min. Org. Openspace Required {3}% , each TOT space with a Min. width of {4} mt. and area of {5} sq.mt. Greenstrip width around boundary is {6} mt. ".format(
			c.m.subtype,area_750threshold,area_4kthreshold, required_tot_factor,required_tot_width,required_tot_area,required_greenstrip_width)


		else:
			required_tot_factor=10
			required_tot_width=3.0
			required_tot_area=15.0
			#required_greenstrip_width=1.0
			rule_txt="For {0} and Site Area > {1} sq.mt. Min. Org. Openspace Required {2}% , each TOT space with a Min. width of {3} mt. and area of {4} sq.mt. Greenstrip width around boundary is {5} mt. ".format(
			c.m.subtype,area_4kthreshold, required_tot_factor,required_tot_width,required_tot_area,required_greenstrip_width)

		results['required_tot_factor'] = required_tot_factor
		results['required_tot_width'] = required_tot_width
		results['required_tot_area']=required_tot_area
		results['required_greenstrip_width']= required_greenstrip_width

		if (c.m.proposed_tot_factor >= required_tot_factor and c.m.proposed_tot_width >= required_tot_width and
			c.m.proposed_tot_area >= required_tot_area and c.m.proposed_greenstrip_width >= required_greenstrip_width
		  ):
			results['status']="OK"
		else:
			results['status']="NOT OK"

		results['zrule']="As per Rule No .5, G.O.Ms.No .168." + rule_txt

		c.s.result=results

	@when_all( (m.subtype ==  'GROUP_HOUSING' ) )
	def buildings_layouts(c):
		# print(" setback rules  ")
		c.s.result=''
		results=dict()
		results['subtype']=c.m.subtype
		results['proposed_site_area'] =c.m.proposed_site_area
		results['proposed_tot_factor']=c.m.proposed_tot_factor
		results['proposed_tot_width']=c.m.proposed_tot_width
		results['proposed_tot_area']=c.m.proposed_tot_area
		results['proposed_greenstrip_width']=c.m.proposed_greenstrip_width

		#based on site area <2000 @5%  >2000 10%
		if (c.m.proposed_site_area < 2000 ):
			required_tot_factor=5
		else:
			required_tot_factor=10
		#Fix changed 8/1 from 3,15 to 6,36 for cluster housing requirement
		required_tot_width=6.0
		required_tot_area=36.0
		required_greenstrip_width=1

		rule_txt=""


		rule_txt="For {0} Min. Org. Openspace Required {1}% , each TOT space with a Min. width of {2} mt. and area of {3} sq.mt. Greenstrip width around boundary is {4} mt.".format(
			c.m.subtype, required_tot_factor,required_tot_width,required_tot_area,required_greenstrip_width)

		results['required_tot_factor'] = required_tot_factor
		results['required_tot_width'] = required_tot_width
		results['required_tot_area']=required_tot_area
		results['required_greenstrip_width']= required_greenstrip_width

		if (c.m.proposed_tot_factor >= required_tot_factor and c.m.proposed_tot_width >= required_tot_width and
			c.m.proposed_tot_area >= required_tot_area and c.m.proposed_greenstrip_width >= required_greenstrip_width
		  ):
			results['status']="OK"
		else:
			results['status']="NOT OK"

		results['zrule']="As per Rule No .5, G.O.Ms.No .168." + rule_txt

		c.s.result=results

 
### PARKING RULES 
# ___________________________________________________________________________________________
# Type of Building 			Site Area 		% Customer Parking 		% Visitor Parking 	
# ___________________________________________________________________________________________
# Open Layout				Any 			0					0
# Small Buildings 			<200 sq. mt     0% BUA				0
# Villas/Rowhouses 			Any				0					0
# Standalone/Buildings		>200 sq mt. <750 30% BUA			0% of Visitor parking 
# GROUP Housing				Any				30% BUA				10% of Visitor parking 
# Default 					Any			 	30% BUA				0% of Visitor parking 
#v.1.0.4

#GHMC vs HMDA/Others 

# Category 1 ['Multiplexes','Shopping Malls','ITES'] & Location = GHMC Parking : 60% else 50%  
#

# Category 2 ['Hotels', 'Restaurants', 'Lodges', 'Cinema halls', \
#			  'Business buildings', 'Other Commercial buildings', 'Kalyana Mandapams', 'Offices','Non-Residential'] 
#			 & Location = GHMC Parking : 40% else 30%  

# Category 3 'Residential', 'Apartment Complexes', 'Hospitals', 'Institutional buildings', 'Industrial buildings', \
#			'Schools', 'Colleges', 'Other Educational Buildings' & 'Godowns', 'Others']
#			& Location = GHMC Parking : 30% else 20%  


with ruleset('ts-parking'):
	@when_all(( m.subtype ==  'SUBPLOTS' ) | (m.subtype == 'VILLAS_ROWHOUSING') and m.parking_category not in ['CAT1','CAT2', 'CAT3'] )
	def open_layouts(c):
		# print(" setback rules  ")
		c.s.result=''
		results=dict()
		results['subtype']=c.m.subtype
		results['proposed_site_area'] =c.m.proposed_site_area
		results['proposed_parking_factor']=c.m.proposed_parking_factor
		results['proposed_visitor_parking_factor']=c.m.proposed_visitor_parking_factor
		required_visitor_parking_factor=0
		required_parking_factor=0

		rule_txt=""

		if (c.m.subtype =='SUBPLOTS'):
			required_visitor_parking_factor=0
			required_parking_factor=0
			rule_txt="For type {0} Parking and Visitor Parking are Exempted".format(c.m.subtype)

		elif (c.m.subtype =='VILLAS_ROWHOUSING'):
			required_visitor_parking_factor=0
			required_parking_factor=0
			rule_txt="For type {0} Min. Parking Required {1}% and Visitor Parking is Exempted".format(c.m.subtype, required_parking_factor)

		results['required_parking_factor'] = required_parking_factor
		results['required_visitor_parking_factor'] = required_visitor_parking_factor

		if (c.m.proposed_parking_factor >= required_parking_factor and c.m.proposed_visitor_parking_factor >= required_visitor_parking_factor  ):
			results['status']="OK"
		else:
			results['status']="NOT OK"

		results['zrule']="As per Rule No .5, G.O.Ms.No .168." + rule_txt

		c.s.result=results

	@when_all( (m.subtype == 'STANDALONE') | (m.subtype == 'NON_HIGHRISE') | (m.subtype ==  'HIGHRISE_MSBR') | (m.subtype ==  'GROUP_HOUSING' ) and m.parking_category not in ['CAT1','CAT2', 'CAT3'])
	def buildings_layouts(c):
		# print(" setback rules  ")
		c.s.result=''
		results=dict()
		results['subtype']=c.m.subtype
		results['proposed_site_area'] =c.m.proposed_site_area
		results['proposed_parking_factor']=c.m.proposed_parking_factor
		results['proposed_visitor_parking_factor']=c.m.proposed_visitor_parking_factor
		required_parking_factor=30
		required_visitor_parking_factor=10

		rule_txt=""

		area_threshold=250
		area_threshold_visitor=750
		if (c.m.proposed_site_area <= area_threshold ):
			required_visitor_parking_factor=0
			required_parking_factor=0
			rule_txt="For type {0} and Site Area up to {1}  sq.mt. a) Min. Parking and Visitor Parking are Exempted".format(c.m.subtype, area_threshold)
		elif (c.m.proposed_site_area > area_threshold and c.m.proposed_site_area <= area_threshold_visitor  ):
			required_visitor_parking_factor=0
			required_parking_factor=30

			rule_txt="For type {0} and Site Area > {1} sq.mt. a) Min. Parking Required {2}% of Proposed BUA ".format(
						c.m.subtype, area_threshold, required_parking_factor)
		else:
			required_visitor_parking_factor=10
			required_parking_factor=30
			rule_txt="For type {0} and Site Area > {1} sq.mt. a) Min. Parking Required {2}% of Proposed BUA b) Visitor Parking Required {3}% of Min. Total Parking ".format(
						c.m.subtype, area_threshold, required_parking_factor,required_visitor_parking_factor)

		results['required_parking_factor'] = required_parking_factor
		results['required_visitor_parking_factor'] = required_visitor_parking_factor

		if (c.m.proposed_parking_factor >= required_parking_factor and c.m.proposed_visitor_parking_factor >= required_visitor_parking_factor  ):
			results['status']="OK"
		else:
			results['status']="NOT OK"

		results['zrule']="As per Rule No .5, G.O.Ms.No .168." + rule_txt

		c.s.result=results

	#GHMC vs HMDA/Others
	# Category 1 ['Multiplexes','Shopping Malls','ITES'] & Location = GHMC Parking : 60% else 50%
	#

	# Category 2 ['Hotels', 'Restaurants', 'Lodges', 'Cinema halls', \
	#			  'Business buildings', 'Other Commercial buildings', 'Kalyana Mandapams', 'Offices','Non-Residential']
	#			 & Location = GHMC Parking : 40% else 30%

	# Category 3 'Residential', 'Apartment Complexes', 'Hospitals', 'Institutional buildings', 'Industrial buildings', \
	#			'Schools', 'Colleges', 'Other Educational Buildings' & 'Godowns', 'Others']
	#			& Location = GHMC Parking : 30% else 20%
	#category value to be passed
	#location type to be passed GHMC, HMDA etc

	@when_all( (m.parking_category == 'CAT1') | (m.parking_category == 'CAT2') | (m.parking_category ==  'CAT3') )
	def location_buildings_layouts(c):
		# print(" setback rules  ")
		c.s.result=''
		results=dict()
		results['subtype']=c.m.subuse
		results['location']=c.m.location
		results['parking_category']=c.m.parking_category
		results['proposed_site_area'] =c.m.proposed_site_area
		results['proposed_parking_factor']=c.m.proposed_parking_factor
		results['proposed_visitor_parking_factor']=c.m.proposed_visitor_parking_factor
		required_parking_factor=30
		required_visitor_parking_factor=10

		rule_txt=""

		area_threshold=250
		area_threshold_visitor=750

		if (c.m.proposed_site_area <= area_threshold ):
			required_visitor_parking_factor=0
			required_parking_factor=0
			rule_txt="For type {0} and Site Area up to {1}  sq.mt. a) Min. Parking and Visitor Parking are Exempted".format(c.m.subuse, area_threshold)
		elif (c.m.proposed_site_area > area_threshold and c.m.proposed_site_area <= area_threshold_visitor and \
					 (c.m.location =='-' or c.m.location =='N/A')) :
			required_visitor_parking_factor=0
			required_parking_factor=30

			rule_txt="For type {0} and Site Area > {1} sq.mt. a) Min. Parking Required {2}% of Proposed BUA ".format(
						c.m.subuse, area_threshold, required_parking_factor)
		else:
			print('in location check for parking rule ', c.m.location, ' parking category ',c.m.parking_category )

			#check the location and parking category
			if (c.m.location == 'GHMC'):


				if (c.m.parking_category == 'CAT1'):
					required_visitor_parking_factor=10
					required_parking_factor=60
				elif (c.m.parking_category == 'CAT2'):
					required_visitor_parking_factor=10
					required_parking_factor=40
				elif (c.m.parking_category == 'CAT3'):
					required_visitor_parking_factor=10
					required_parking_factor=30
				else:
					required_visitor_parking_factor=10
					required_parking_factor=30

			elif (c.m.location == 'HMDA' or c.m.location == 'HMDA Core Area'):

				if (c.m.parking_category == 'CAT1'):

					required_visitor_parking_factor=10
					required_parking_factor=50
				elif (c.m.parking_category == 'CAT2'):
					required_visitor_parking_factor=10
					required_parking_factor=30
				elif (c.m.parking_category == 'CAT3'):
					required_visitor_parking_factor=10
					required_parking_factor=20
				else:
					required_visitor_parking_factor=10
					required_parking_factor=30
			else:
				print('error', 'Unable to determine the Rule for Parking Request, using default values for required_parking and visitor parking '\
						+ str(c.m.location) + str(c.m.subuse) + str(c.m.parking_category) + str(c.m.proposed_site_area) )

			rule_txt="For type {0} and location {1} and Site Area > {2} sq.mt. a) Min. Parking Required {3}% of Proposed BUA b) Visitor Parking Required {4}% of Min. Total Parking ".format(
						c.m.subuse, c.m.location , area_threshold, required_parking_factor, required_visitor_parking_factor)

		results['required_parking_factor'] = required_parking_factor
		results['required_visitor_parking_factor'] = required_visitor_parking_factor

		if (c.m.proposed_parking_factor >= required_parking_factor and c.m.proposed_visitor_parking_factor >= required_visitor_parking_factor  ):
			results['status']="OK"
		else:
			results['status']="NOT OK"

		results['zrule']="As per Rule No .5, G.O.Ms.No .168." + rule_txt

		c.s.result=results




## Setbacks
# Based on Building Height and Plot's (Main) Abutting Road Width

with ruleset('ts-setbacks'):
	"""
	# Site Area
	# Based on Building Height and Plot's (Main) Abutting Road Width
	abutting road	set back all round min.

	a)Type : High Rise or Multi-Storied Building
	building ht, abutting road , all round setbacks
	<=21 	12.2	7
	> 21 & <=24	12.2	8
	> 24 & <=27	18	9
	> 27 & <=30	18	10
	Sno Building Type	,building het & ,	abutting road,	F,  R,  S1, S2
	1	High Rise MSB	,<=21 				12.2,			7,	7,	7,	7
	2	High Rise MSB	,> 21 & <=24,		12.2,			8,	8,	8,	8
	3	High Rise MSB	,> 24 & <=27,		18,				9,	9,	9,	9
	4	High Rise MSB	,> 27 & <=30,		18,				10,	10,	10,	10
	5	Group Housing	,<12,				> 9 & <=12,		3,  1.5,1.5,1.5
	6	Group Housing	,<12,				> 12 & <=18		4,	2,	2,	2
	7	Group Housing	,<12,				>18				4.5,2.5,2.5,2.5
	8	Group Housing	,>12 andSiteArea<= 670,	>12&<=18  	Max (4, 1/4 of Bldging ht),	1/4 of Bldg Ht,	1/4 of Bldg Ht,	1/4 of Bldg Ht
	9	Group Housing	,>12,or SiteArea>670, 	>18	Max (4.5, 1/4 of Bldging ht)	1/4 of Bldg Ht,	1/4 of Bldg Ht,	1/4 of Bldg Ht
	10	Villas/RowHousing,		6,			-,				3,  1.5,0, 0
	11	Standalone	     <10,				9				1.5,1,	1,	1
	12	Non MSB/High Rise,					<18				8,	6,	6,	6

	1/15/21 Revised rules to be implemented.
table iii - page 64  standalone, group housing, non highrise (<18 mt) any purpose code.
table iv -  high rise MSBR (>18 mt. ) any purposecode
multiplex -- Page 108 GO 486 Jhanvi will confirm on the blank cells for front setbacks   :sitearea min. 3000 sq.mt. min. abutting road 18 mt.

	"""

	@when_all( ( m.subtype ==  'HIGHRISE_MSBR') | (m.subtype ==  'GROUP_HOUSING' and m.proposed_bldg_height > 18)  )
	def highrise_msb_rules(c):
		print("HIGHRISE_MSBR GROUP_HOUSING setback rules  ")
		c.s.result=''
		results=dict()
		results['subtype']=c.m.subtype
		results['proposed_bldg_height'] =c.m.proposed_bldg_height
		results['proposed_site_area'] =c.m.proposed_site_area
		results['proposed_abutting_road_width'] =c.m.proposed_abutting_road_width
		results['proposed_front_setback']=c.m.proposed_front_setback
		results['proposed_rear_setback']=c.m.proposed_rear_setback
		results['proposed_side1_setback']=c.m.proposed_side1_setback
		results['proposed_side2_setback']=c.m.proposed_side2_setback
		bldg_height_exceedlimits =False
		max_bldg_height_allowed=200

		#Bldg Height > 200 mt. Not Allowed
		if (c.m.proposed_bldg_height > max_bldg_height_allowed  ):
			bldg_height_exceedlimits =True  #sets status as NOT OK

		#min. required site area #common
		required_site_area=2000
		if (c.m.subtype ==  'GROUP_HOUSING' ):
			required_site_area=335

		if (c.m.proposed_bldg_height > 0 and  c.m.proposed_bldg_height <=21 ) :
			required_abutting_road_width=12
			required_front_setback=7
			required_rear_setback=7
			required_side1_setback=7
			required_side2_setback=7
			rule_txt="Bldg Height upto 21 mt. "
		elif (c.m.proposed_bldg_height >21 and c.m.proposed_bldg_height <=24 ) :
			required_abutting_road_width=12
			required_front_setback=8
			required_rear_setback=8
			required_side1_setback=8
			required_side2_setback=8
			rule_txt="Bldg Height > 21 mt. and <=24 "
		elif (c.m.proposed_bldg_height >24 and c.m.proposed_bldg_height <=27 ) :
			required_abutting_road_width=18
			required_front_setback=9
			required_rear_setback=9
			required_side1_setback=9
			required_side2_setback=9
			rule_txt="Bldg Height > 24 mt. and <=27 "
		elif (c.m.proposed_bldg_height > 27 and c.m.proposed_bldg_height <=30 ) :
			required_abutting_road_width=18
			required_front_setback=10
			required_rear_setback=10
			required_side1_setback=10
			required_side2_setback=10
			rule_txt="Bldg Height > 27 mt. and <=30 "
		elif (c.m.proposed_bldg_height > 30 and c.m.proposed_bldg_height <=35 ) :
			required_abutting_road_width=24
			required_front_setback=11
			required_rear_setback=11
			required_side1_setback=11
			required_side2_setback=11
			rule_txt="Bldg Height > 30 mt. and <=35 mt "
		elif (c.m.proposed_bldg_height > 35 and c.m.proposed_bldg_height <=40 ) :
			required_abutting_road_width=24
			required_front_setback=12
			required_rear_setback=12
			required_side1_setback=12
			required_side2_setback=12
			rule_txt="Bldg Height > 35 mt. and <=40 mt "
		elif (c.m.proposed_bldg_height > 40 and c.m.proposed_bldg_height <=45 ) :
			required_abutting_road_width=24
			required_front_setback=13
			required_rear_setback=13
			required_side1_setback=13
			required_side2_setback=13
			rule_txt="Bldg Height > 40 mt. and <=45 mt "
		elif (c.m.proposed_bldg_height > 45 and c.m.proposed_bldg_height <=50 ) :
			required_abutting_road_width=30
			required_front_setback=14
			required_rear_setback=14
			required_side1_setback=14
			required_side2_setback=14
			rule_txt="Bldg Height > 45 mt. and <=50 mt "
		elif (c.m.proposed_bldg_height > 50 and c.m.proposed_bldg_height <=55 ) :
			required_abutting_road_width=30
			required_front_setback=16
			required_rear_setback=16
			required_side1_setback=16
			required_side2_setback=16
			rule_txt="Bldg Height > 50 mt. and <=55 mt "
		elif (c.m.proposed_bldg_height > 55  and c.m.proposed_bldg_height <=70 ) :
			required_abutting_road_width=30
			required_front_setback=17
			required_rear_setback=17
			required_side1_setback=17
			required_side2_setback=17
			rule_txt="Bldg Height > 55 mt. and <=70 mt "
		elif (c.m.proposed_bldg_height > 70 and c.m.proposed_bldg_height <=120 ) :
			required_abutting_road_width=30
			required_front_setback=18
			required_rear_setback=18
			required_side1_setback=18
			required_side2_setback=18
			rule_txt="Bldg Height > 70 mt. and <=120 mt "
		elif (c.m.proposed_bldg_height > 120 ) :
			required_abutting_road_width=30
			required_front_setback=20
			required_rear_setback=20
			required_side1_setback=20
			required_side2_setback=20
			rule_txt="Bldg Height > 120 mt."

		rule_applicable="For Type of {0}, Site Area: {1} and {2} a) Requires Min. Abutting Road Width {3} mt. b) Requires  Min. Setbacks in mts. for front/rear/side1/sides are {4}/{5}/{6}/{7} ".format(\
			c.m.subtype,required_site_area, rule_txt, required_abutting_road_width ,required_front_setback,required_rear_setback,required_side1_setback,required_side2_setback)

		results['required_abutting_road_width'] =required_abutting_road_width
		results['required_site_area']=required_site_area
		results['required_front_setback'] = required_front_setback
		results['required_rear_setback'] =  required_rear_setback
		results['required_side1_setback'] = required_side1_setback
		results['required_side2_setback'] = required_side2_setback
		rule_txt=rule_applicable



		if (bldg_height_exceedlimits ==False and c.m.proposed_abutting_road_width  >= required_abutting_road_width and
			c.m.proposed_site_area >= required_site_area and
			c.m.proposed_front_setback >= required_front_setback and
			c.m.proposed_rear_setback >= required_rear_setback and
			c.m.proposed_side1_setback >= required_side1_setback and
			c.m.proposed_side2_setback >= required_side2_setback  ):
			results['status']="OK"
		else:
			results['status']="NOT OK"

		if (bldg_height_exceedlimits):
			results['status']="NOT OK"
			results['zrule']="As per Rule No .5, G.O.Ms.No .168. Bldg Height >" + str(max_bldg_height_allowed) + " mt. Not Allowed"
		else:
			results['zrule']="As per Rule No .5, G.O.Ms.No .168." + rule_applicable

		c.s.result=results

	@when_all(  m.subtype == 'VILLAS_ROWHOUSING' and m.proposed_bldg_height <=20 )
	def villas_rowhousing_non_msb_rules(c):
		print("VILLAS_ROWHOUSING setback rules  ")
		c.s.result=''
		results=dict()
		results['subtype']=c.m.subtype
		results['proposed_bldg_height'] =c.m.proposed_bldg_height
		results['proposed_site_area'] =c.m.proposed_site_area
		results['proposed_abutting_road_width'] =c.m.proposed_abutting_road_width
		results['proposed_front_setback']=c.m.proposed_front_setback
		results['proposed_rear_setback']=c.m.proposed_rear_setback
		results['proposed_side1_setback']=c.m.proposed_side1_setback
		results['proposed_side2_setback']=c.m.proposed_side2_setback
		bldg_height_exceedlimits =False
		setbackFailed=False
		max_bldg_height_allowed=11

		#Bldg Height > 30 mt. Not Allowed
		if (c.m.proposed_bldg_height > max_bldg_height_allowed  ):
			bldg_height_exceedlimits =True  #sets status as NOT OK

		#min. required site area #common
		required_site_area=125

		required_abutting_road_width=9
		required_front_setback=3
		required_rear_setback=1.5
		required_side1_setback=0
		required_side2_setback=0
		rule_txt="Villa/Row House G+2 Height upto 11 mt. "

		rule_applicable="For Type of {0}, Site Area: {1} and {2} a) Requires Min. Abutting Road Width {3} mt. b) Requires  Min. Setbacks in mts. for front/rear/side1/sides are {4}/{5}/{6}/{7} ".format(\
			c.m.subtype,required_site_area, rule_txt, required_abutting_road_width ,required_front_setback,required_rear_setback,required_side1_setback,required_side2_setback)

		results['required_abutting_road_width'] = required_abutting_road_width
		results['required_site_area']=required_site_area
		results['required_front_setback'] = required_front_setback
		results['required_rear_setback'] =  required_rear_setback
		results['required_side1_setback'] = required_side1_setback
		results['required_side2_setback'] = required_side2_setback
		rule_txt=rule_applicable


		if (bldg_height_exceedlimits == False and c.m.proposed_abutting_road_width  >= required_abutting_road_width and
			c.m.proposed_site_area >= required_site_area and
			c.m.proposed_front_setback >= required_front_setback and
			c.m.proposed_rear_setback >= required_rear_setback and
			c.m.proposed_side1_setback >= required_side1_setback and
			c.m.proposed_side2_setback >= required_side2_setback  ):
			results['status']="OK"
		else:
			results['status']="NOT OK"
			setbackFailed=True
		rule_base="As per Rule No .5, G.O.Ms.No .168. " + rule_applicable

		if (bldg_height_exceedlimits or setbackFailed):
			results['status']="NOT OK"

			if (setbackFailed):
				rule_base += ' Failed for Setbacks.'

			if (bldg_height_exceedlimits):
				rule_base += ' Failed for Building Height. '

			results['zrule']=rule_base

		else:
			results['zrule']=rule_base

		c.s.result=results

	@when_all(m.subtype !=  'VILLAS_ROWHOUSING' and ( (m.subtype ==  'STANDALONE' ) | (m.subtype ==  'NON_HIGHRISE' ) |  (m.subtype ==  'GROUP_HOUSING') and m.proposed_bldg_height <= 18  ))
	def group_housing_non_highrise_non_msb_rules(c):
		# print(" setback rules  ")
		print("STANDALONE  NON_HIGHRISE GROUP_HOUSING setback rules  ")
		c.s.result=''
		results=dict()
		results['subtype']=c.m.subtype
		results['proposed_bldg_height'] =c.m.proposed_bldg_height
		results['proposed_site_area'] =c.m.proposed_site_area
		results['proposed_abutting_road_width'] =c.m.proposed_abutting_road_width
		results['proposed_front_setback']=c.m.proposed_front_setback
		results['proposed_rear_setback']=c.m.proposed_rear_setback
		results['proposed_side1_setback']=c.m.proposed_side1_setback
		results['proposed_side2_setback']=c.m.proposed_side2_setback
		bldg_height_exceedlimits =False
		max_bldg_height_allowed=18
		required_abutting_road_width=9  #min. abutting width
		front_sb=1.5
		rear_sides_sb=3

		#page #58 TABLE-III ITPI 2020 Final GO RULES
		#max height/setbacks front and sides/rear based on site area
		#1
		if (c.m.proposed_site_area <= 50):
			max_bldg_height_allowed=7
			if (c.m.proposed_abutting_road_width <=18):
				front_sb=1.5
				rear_sides_sb=0
			else:
				front_sb=3.0
				rear_sides_sb=0
		#2
		elif (c.m.proposed_site_area > 50 and c.m.proposed_site_area <= 100):
			max_bldg_height_allowed=10
			if (c.m.proposed_abutting_road_width <=18 and c.m.proposed_bldg_height <=7 ):
				front_sb=1.5
				rear_sides_sb=0
			elif (c.m.proposed_abutting_road_width <=18 and c.m.proposed_bldg_height > 7 ):
				front_sb=3.0
				rear_sides_sb=0.0
			elif (c.m.proposed_abutting_road_width > 18 and c.m.proposed_bldg_height > 7 ):
				front_sb=3.0
				rear_sides_sb=0.5
			else:
				front_sb=3.0
				rear_sides_sb=0.5
		#3
		elif (c.m.proposed_site_area > 100 and c.m.proposed_site_area <= 200):
			max_bldg_height_allowed=10
			if (c.m.proposed_abutting_road_width <=18):
				front_sb=1.5
				rear_sides_sb=1.0
			else:
				front_sb=3.0
				rear_sides_sb=1.0

		#4
		elif (c.m.proposed_site_area > 200 and c.m.proposed_site_area <= 300):
			max_bldg_height_allowed=10
			if (c.m.proposed_abutting_road_width <=12 and c.m.proposed_bldg_height <=7 ):
				front_sb=2.0
				rear_sides_sb=1.0
			elif (c.m.proposed_abutting_road_width > 12 and c.m.proposed_abutting_road_width <=24 and c.m.proposed_bldg_height <=7 ):
				front_sb=3.0
				rear_sides_sb=1.0
			elif (c.m.proposed_abutting_road_width > 24 and c.m.proposed_abutting_road_width <=30 and c.m.proposed_bldg_height <=7 ):
				front_sb=4.0
				rear_sides_sb=1.0
			elif (c.m.proposed_abutting_road_width > 30 and c.m.proposed_bldg_height <=7 ):
				front_sb=5.0
				rear_sides_sb=1.0
			elif (c.m.proposed_abutting_road_width <=12 and c.m.proposed_bldg_height >7 ):
				front_sb=2.0
				rear_sides_sb=1.5
			elif (c.m.proposed_abutting_road_width > 12 and c.m.proposed_abutting_road_width <=24 and c.m.proposed_bldg_height > 7 ):
				front_sb=3.0
				rear_sides_sb=1.5
			elif (c.m.proposed_abutting_road_width > 24 and c.m.proposed_abutting_road_width <=30 and c.m.proposed_bldg_height >7 ):
				front_sb=5.0
				rear_sides_sb=1.5
			elif (c.m.proposed_abutting_road_width > 30 and c.m.proposed_bldg_height >7 ):
				front_sb=6.0
				rear_sides_sb=1.5



		#5
		elif (c.m.proposed_site_area > 300 and c.m.proposed_site_area <= 400):
			max_bldg_height_allowed=12
			if (c.m.proposed_abutting_road_width <=12 and c.m.proposed_bldg_height <=7 ):
				front_sb=3.0
				rear_sides_sb=1.5
			elif (c.m.proposed_abutting_road_width > 12 and c.m.proposed_abutting_road_width <=18 and c.m.proposed_bldg_height <=7 ):
				front_sb=4.0
				rear_sides_sb=1.5
			elif (c.m.proposed_abutting_road_width > 18 and c.m.proposed_abutting_road_width <=24 and c.m.proposed_bldg_height <=7 ):
				front_sb=5.0
				rear_sides_sb=1.5
			elif (c.m.proposed_abutting_road_width > 24 and c.m.proposed_abutting_road_width <=30 and c.m.proposed_bldg_height <=7 ):
				front_sb=6.0
				rear_sides_sb=1.5
			elif (c.m.proposed_abutting_road_width > 30 and c.m.proposed_bldg_height <=7 ):
				front_sb=7.50
				rear_sides_sb=1.0
			elif (c.m.proposed_abutting_road_width <=12 and c.m.proposed_bldg_height >7 ):
				front_sb=3.0
				rear_sides_sb=2.0
			elif (c.m.proposed_abutting_road_width > 12 and c.m.proposed_abutting_road_width <=18 and c.m.proposed_bldg_height > 7 ):
				front_sb=4.0
				rear_sides_sb=2.0
			elif (c.m.proposed_abutting_road_width > 18 and c.m.proposed_abutting_road_width <=24 and c.m.proposed_bldg_height >7 ):
				front_sb=5.0
				rear_sides_sb=2.0

			elif (c.m.proposed_abutting_road_width > 24 and c.m.proposed_abutting_road_width <=30 and c.m.proposed_bldg_height >7 ):
				front_sb=6.0
				rear_sides_sb=2.0
			elif (c.m.proposed_abutting_road_width > 30 and c.m.proposed_bldg_height >7 ):
				front_sb=7.5
				rear_sides_sb=2.0

		#6
		elif (c.m.proposed_site_area > 400 and c.m.proposed_site_area <= 500):
			max_bldg_height_allowed=12
			if (c.m.proposed_abutting_road_width <=12 and c.m.proposed_bldg_height <=7 ):
				front_sb=3.0
				rear_sides_sb=2
			elif (c.m.proposed_abutting_road_width > 12 and c.m.proposed_abutting_road_width <=18 and c.m.proposed_bldg_height <=7 ):
				front_sb=4.0
				rear_sides_sb=2
			elif (c.m.proposed_abutting_road_width > 18 and c.m.proposed_abutting_road_width <=24 and c.m.proposed_bldg_height <=7 ):
				front_sb=5.0
				rear_sides_sb=2
			elif (c.m.proposed_abutting_road_width > 24 and c.m.proposed_abutting_road_width <=30 and c.m.proposed_bldg_height <=7 ):
				front_sb=6.0
				rear_sides_sb=2
			elif (c.m.proposed_abutting_road_width > 30 and c.m.proposed_bldg_height <=7 ):
				front_sb=7.50
				rear_sides_sb=2
			elif (c.m.proposed_abutting_road_width <=12 and c.m.proposed_bldg_height >7 ):
				front_sb=3.0
				rear_sides_sb=2.5
			elif (c.m.proposed_abutting_road_width > 12 and c.m.proposed_abutting_road_width <=18 and c.m.proposed_bldg_height > 7 ):
				front_sb=4.0
				rear_sides_sb=2.5
			elif (c.m.proposed_abutting_road_width > 18 and c.m.proposed_abutting_road_width <=24 and c.m.proposed_bldg_height >7 ):
				front_sb=5.0
				rear_sides_sb=2.5

			elif (c.m.proposed_abutting_road_width > 24 and c.m.proposed_abutting_road_width <=30 and c.m.proposed_bldg_height >7 ):
				front_sb=6.0
				rear_sides_sb=2.5
			elif (c.m.proposed_abutting_road_width > 30 and c.m.proposed_bldg_height >7 ):
				front_sb=7.5
				rear_sides_sb=2.5
			else:
				front_sb=7.5
				rear_sides_sb=2.5

		#7
		elif (c.m.proposed_site_area > 500 and c.m.proposed_site_area <= 750):
			max_bldg_height_allowed=15

			if (c.m.proposed_abutting_road_width <=12 and c.m.proposed_bldg_height <=7 ):
				front_sb=3.0
				rear_sides_sb=2.5
			elif (c.m.proposed_abutting_road_width > 12 and c.m.proposed_abutting_road_width <=18 and c.m.proposed_bldg_height <=7 ):
				front_sb=4.0
				rear_sides_sb=2.5
			elif (c.m.proposed_abutting_road_width > 18 and c.m.proposed_abutting_road_width <=24 and c.m.proposed_bldg_height <=7 ):
				front_sb=5.0
				rear_sides_sb=2.5
			elif (c.m.proposed_abutting_road_width > 24 and c.m.proposed_abutting_road_width <=30 and c.m.proposed_bldg_height <=7 ):
				front_sb=6.0
				rear_sides_sb=2.5
			elif (c.m.proposed_abutting_road_width > 30 and c.m.proposed_bldg_height <=7 ):
				front_sb=7.50
				rear_sides_sb=2.5
			elif (c.m.proposed_abutting_road_width <=12 and c.m.proposed_bldg_height >7 and c.m.proposed_bldg_height <=12 ):
				front_sb=3.0
				rear_sides_sb=3.0
			elif (c.m.proposed_abutting_road_width > 12 and c.m.proposed_abutting_road_width <=18 and c.m.proposed_bldg_height > 7   and c.m.proposed_bldg_height <=12):
				front_sb=4.0
				rear_sides_sb=3.0
			elif (c.m.proposed_abutting_road_width > 18 and c.m.proposed_abutting_road_width <=24 and c.m.proposed_bldg_height >7  and c.m.proposed_bldg_height <=12 ):
				front_sb=5.0
				rear_sides_sb=3.0

			elif (c.m.proposed_abutting_road_width > 24 and c.m.proposed_abutting_road_width <=30 and c.m.proposed_bldg_height >7  and c.m.proposed_bldg_height <=12 ):
				front_sb=6.0
				rear_sides_sb=3.0
			elif (c.m.proposed_abutting_road_width > 30 and c.m.proposed_bldg_height >7  and c.m.proposed_bldg_height <=12 ):
				front_sb=7.5
				rear_sides_sb=3.0
			elif (c.m.proposed_abutting_road_width <=12 and c.m.proposed_bldg_height >12 ):
				front_sb=3.5
				rear_sides_sb=3.0
			elif (c.m.proposed_abutting_road_width > 12 and c.m.proposed_abutting_road_width <=18 and c.m.proposed_bldg_height > 12 ):
				front_sb=4.0
				rear_sides_sb=3.5
			elif (c.m.proposed_abutting_road_width > 18 and c.m.proposed_abutting_road_width <=24 and c.m.proposed_bldg_height >12 ):
				front_sb=5.0
				rear_sides_sb=3.5

			elif (c.m.proposed_abutting_road_width > 24 and c.m.proposed_abutting_road_width <=30 and c.m.proposed_bldg_height >12 ):
				front_sb=6.0
				rear_sides_sb=3.5
			elif (c.m.proposed_abutting_road_width > 30 and c.m.proposed_bldg_height > 12  ):
				front_sb=7.5
				rear_sides_sb=3.5
			else:
				front_sb=7.5
				rear_sides_sb=3.5

		#8
		elif (c.m.proposed_site_area > 750 and c.m.proposed_site_area <= 1000):
			max_bldg_height_allowed=18

			if (c.m.proposed_abutting_road_width <=12 and c.m.proposed_bldg_height <=7 ):
				front_sb=3.0
				rear_sides_sb=3.0
			elif (c.m.proposed_abutting_road_width > 12 and c.m.proposed_abutting_road_width <=18 and c.m.proposed_bldg_height <=7 ):
				front_sb=4.0
				rear_sides_sb=3.0
			elif (c.m.proposed_abutting_road_width > 18 and c.m.proposed_abutting_road_width <=24 and c.m.proposed_bldg_height <=7 ):
				front_sb=5.0
				rear_sides_sb=3.0
			elif (c.m.proposed_abutting_road_width > 24 and c.m.proposed_abutting_road_width <=30 and c.m.proposed_bldg_height <=7 ):
				front_sb=6.0
				rear_sides_sb=3.0
			elif (c.m.proposed_abutting_road_width > 30 and c.m.proposed_bldg_height <=7 ):
				front_sb=7.50
				rear_sides_sb=3.0
			elif (c.m.proposed_abutting_road_width <=12 and c.m.proposed_bldg_height >7 and c.m.proposed_bldg_height <=12 ):
				front_sb=3.0
				rear_sides_sb=3.5
			elif (c.m.proposed_abutting_road_width > 12 and c.m.proposed_abutting_road_width <=18 and c.m.proposed_bldg_height > 7   and c.m.proposed_bldg_height <=12):
				front_sb=4.0
				rear_sides_sb=3.5
			elif (c.m.proposed_abutting_road_width > 18 and c.m.proposed_abutting_road_width <=24 and c.m.proposed_bldg_height >7  and c.m.proposed_bldg_height <=12 ):
				front_sb=5.0
				rear_sides_sb=3.5

			elif (c.m.proposed_abutting_road_width > 24 and c.m.proposed_abutting_road_width <=30 and c.m.proposed_bldg_height >7  and c.m.proposed_bldg_height <=12 ):
				front_sb=6.0
				rear_sides_sb=3.5
			elif (c.m.proposed_abutting_road_width > 30 and c.m.proposed_bldg_height >7  and c.m.proposed_bldg_height <=12 ):
				front_sb=7.5
				rear_sides_sb=4.0
			elif (c.m.proposed_abutting_road_width <=12 and c.m.proposed_bldg_height >12 ):
				front_sb=3.5
				rear_sides_sb=4.0
			elif (c.m.proposed_abutting_road_width > 12 and c.m.proposed_abutting_road_width <=18 and c.m.proposed_bldg_height > 12 ):
				front_sb=4.0
				rear_sides_sb=4.0
			elif (c.m.proposed_abutting_road_width > 18 and c.m.proposed_abutting_road_width <=24 and c.m.proposed_bldg_height >12 ):
				front_sb=5.0
				rear_sides_sb=4.0

			elif (c.m.proposed_abutting_road_width > 24 and c.m.proposed_abutting_road_width <=30 and c.m.proposed_bldg_height >12 ):
				front_sb=6.0
				rear_sides_sb=4.0
			elif (c.m.proposed_abutting_road_width > 30 and c.m.proposed_bldg_height > 12  ):
				front_sb=7.5
				rear_sides_sb=4.0
			else:
				front_sb=7.5
				rear_sides_sb=4.0

		#9
		elif (c.m.proposed_site_area > 1000 and c.m.proposed_site_area <= 1500):
			max_bldg_height_allowed=18
			if (c.m.proposed_abutting_road_width <=12 and c.m.proposed_bldg_height <=7 ):
				front_sb=3.0
				rear_sides_sb=3.5
			elif (c.m.proposed_abutting_road_width > 12 and c.m.proposed_abutting_road_width <=18 and c.m.proposed_bldg_height <=7 ):
				front_sb=4.0
				rear_sides_sb=3.5
			elif (c.m.proposed_abutting_road_width > 18 and c.m.proposed_abutting_road_width <=24 and c.m.proposed_bldg_height <=7 ):
				front_sb=5.0
				rear_sides_sb=3.5
			elif (c.m.proposed_abutting_road_width > 24 and c.m.proposed_abutting_road_width <=30 and c.m.proposed_bldg_height <=7 ):
				front_sb=6.0
				rear_sides_sb=3.5
			elif (c.m.proposed_abutting_road_width > 30 and c.m.proposed_bldg_height <=7 ):
				front_sb=7.50
				rear_sides_sb=3.5
			elif (c.m.proposed_abutting_road_width <=12 and c.m.proposed_bldg_height >7 and c.m.proposed_bldg_height <=12 ):
				front_sb=3.0
				rear_sides_sb=4.0
			elif (c.m.proposed_abutting_road_width > 12 and c.m.proposed_abutting_road_width <=18 and c.m.proposed_bldg_height > 7   and c.m.proposed_bldg_height <=12):
				front_sb=4.0
				rear_sides_sb=4.0
			elif (c.m.proposed_abutting_road_width > 18 and c.m.proposed_abutting_road_width <=24 and c.m.proposed_bldg_height >7  and c.m.proposed_bldg_height <=12 ):
				front_sb=5.0
				rear_sides_sb=4.0

			elif (c.m.proposed_abutting_road_width > 24 and c.m.proposed_abutting_road_width <=30 and c.m.proposed_bldg_height >7  and c.m.proposed_bldg_height <=12 ):
				front_sb=6.0
				rear_sides_sb=4.0
			elif (c.m.proposed_abutting_road_width > 30 and c.m.proposed_bldg_height >12  and c.m.proposed_bldg_height <=15 ):
				front_sb=7.5
				rear_sides_sb=5.0
			elif (c.m.proposed_abutting_road_width <=12 and c.m.proposed_bldg_height >12 and c.m.proposed_bldg_height <=15 ):
				front_sb=3.0
				rear_sides_sb=5.0
			elif (c.m.proposed_abutting_road_width > 12 and c.m.proposed_abutting_road_width <=18 and c.m.proposed_bldg_height > 12   and c.m.proposed_bldg_height <=15):
				front_sb=4.0
				rear_sides_sb=5.0
			elif (c.m.proposed_abutting_road_width > 18 and c.m.proposed_abutting_road_width <=24 and c.m.proposed_bldg_height >12  and c.m.proposed_bldg_height <=15 ):
				front_sb=5.0
				rear_sides_sb=5.0

			elif (c.m.proposed_abutting_road_width > 24 and c.m.proposed_abutting_road_width <=30 and c.m.proposed_bldg_height >12  and c.m.proposed_bldg_height <=15 ):
				front_sb=6.0
				rear_sides_sb=5.0
			elif (c.m.proposed_abutting_road_width > 30 and c.m.proposed_bldg_height >12  and c.m.proposed_bldg_height <=15 ):
				front_sb=7.5
				rear_sides_sb=5.0

			elif (c.m.proposed_abutting_road_width <=12 and c.m.proposed_bldg_height >15 ):
				front_sb=3.0
				rear_sides_sb=6.0
			elif (c.m.proposed_abutting_road_width > 12 and c.m.proposed_abutting_road_width <=18 and c.m.proposed_bldg_height > 15 ):
				front_sb=4.0
				rear_sides_sb=6.0
			elif (c.m.proposed_abutting_road_width > 18 and c.m.proposed_abutting_road_width <=24 and c.m.proposed_bldg_height >15 ):
				front_sb=5.0
				rear_sides_sb=6.0

			elif (c.m.proposed_abutting_road_width > 24 and c.m.proposed_abutting_road_width <=30 and c.m.proposed_bldg_height >15 ):
				front_sb=6.0
				rear_sides_sb=6.0
			elif (c.m.proposed_abutting_road_width > 30 and c.m.proposed_bldg_height > 15  ):
				front_sb=7.5
				rear_sides_sb=6.0
			else:
				front_sb=7.5
				rear_sides_sb=6.0
		#10
		elif (c.m.proposed_site_area > 1500 and c.m.proposed_site_area <= 2500):
			max_bldg_height_allowed=18
			if (c.m.proposed_abutting_road_width <=12 and c.m.proposed_bldg_height <=7 ):
				front_sb=3.0
				rear_sides_sb=4.0
			elif (c.m.proposed_abutting_road_width > 12 and c.m.proposed_abutting_road_width <=18 and c.m.proposed_bldg_height <=7 ):
				front_sb=4.0
				rear_sides_sb=4.0
			elif (c.m.proposed_abutting_road_width > 18 and c.m.proposed_abutting_road_width <=24 and c.m.proposed_bldg_height <=7 ):
				front_sb=5.0
				rear_sides_sb=4.0
			elif (c.m.proposed_abutting_road_width > 24 and c.m.proposed_abutting_road_width <=30 and c.m.proposed_bldg_height <=7 ):
				front_sb=6.0
				rear_sides_sb=4.0
			elif (c.m.proposed_abutting_road_width > 30 and c.m.proposed_bldg_height <=7 ):
				front_sb=7.50
				rear_sides_sb=4.0
			elif (c.m.proposed_abutting_road_width <=12 and c.m.proposed_bldg_height >7 and c.m.proposed_bldg_height <=15 ):
				front_sb=3.0
				rear_sides_sb=5.0
			elif (c.m.proposed_abutting_road_width > 12 and c.m.proposed_abutting_road_width <=18 and c.m.proposed_bldg_height > 7   and c.m.proposed_bldg_height <=15):
				front_sb=4.0
				rear_sides_sb=5.0
			elif (c.m.proposed_abutting_road_width > 18 and c.m.proposed_abutting_road_width <=24 and c.m.proposed_bldg_height >7  and c.m.proposed_bldg_height <=15 ):
				front_sb=5.0
				rear_sides_sb=5.0

			elif (c.m.proposed_abutting_road_width > 24 and c.m.proposed_abutting_road_width <=30 and c.m.proposed_bldg_height >7  and c.m.proposed_bldg_height <=15 ):
				front_sb=6.0
				rear_sides_sb=5.0
			elif (c.m.proposed_abutting_road_width > 30 and c.m.proposed_bldg_height >7  and c.m.proposed_bldg_height <=15 ):
				front_sb=7.5
				rear_sides_sb=5.0
			elif (c.m.proposed_abutting_road_width <=12 and c.m.proposed_bldg_height >15):
				front_sb=3.0
				rear_sides_sb=6.0
			elif (c.m.proposed_abutting_road_width > 12 and c.m.proposed_abutting_road_width <=18 and c.m.proposed_bldg_height > 15 ):
				front_sb=4.0
				rear_sides_sb=6.0
			elif (c.m.proposed_abutting_road_width > 18 and c.m.proposed_abutting_road_width <=24 and c.m.proposed_bldg_height >15 ):
				front_sb=5.0
				rear_sides_sb=6.0

			elif (c.m.proposed_abutting_road_width > 24 and c.m.proposed_abutting_road_width <=30 and c.m.proposed_bldg_height >15 ):
				front_sb=6.0
				rear_sides_sb=6.0
			elif (c.m.proposed_abutting_road_width > 30 and c.m.proposed_bldg_height > 15  ):
				front_sb=7.5
				rear_sides_sb=6.0
			else:
				front_sb=7.5
				rear_sides_sb=6.0

		#11
		elif (c.m.proposed_site_area > 2500 ):
			max_bldg_height_allowed=18
			if (c.m.proposed_abutting_road_width <=12 and c.m.proposed_bldg_height <=7 ):
				front_sb=3.0
				rear_sides_sb=5.0
			elif (c.m.proposed_abutting_road_width > 12 and c.m.proposed_abutting_road_width <=18 and c.m.proposed_bldg_height <=7 ):
				front_sb=4.0
				rear_sides_sb=5.0
			elif (c.m.proposed_abutting_road_width > 18 and c.m.proposed_abutting_road_width <=24 and c.m.proposed_bldg_height <=7 ):
				front_sb=5.0
				rear_sides_sb=5.0
			elif (c.m.proposed_abutting_road_width > 24 and c.m.proposed_abutting_road_width <=30 and c.m.proposed_bldg_height <=7 ):
				front_sb=6.0
				rear_sides_sb=5.0
			elif (c.m.proposed_abutting_road_width > 30 and c.m.proposed_bldg_height <=7 ):
				front_sb=7.50
				rear_sides_sb=5.0
			elif (c.m.proposed_abutting_road_width <=12 and c.m.proposed_bldg_height >7 and c.m.proposed_bldg_height <=15 ):
				front_sb=3.0
				rear_sides_sb=6.0
			elif (c.m.proposed_abutting_road_width > 12 and c.m.proposed_abutting_road_width <=18 and c.m.proposed_bldg_height > 7   and c.m.proposed_bldg_height <=15):
				front_sb=4.0
				rear_sides_sb=6.0
			elif (c.m.proposed_abutting_road_width > 18 and c.m.proposed_abutting_road_width <=24 and c.m.proposed_bldg_height >7  and c.m.proposed_bldg_height <=15 ):
				front_sb=5.0
				rear_sides_sb=6.0

			elif (c.m.proposed_abutting_road_width > 24 and c.m.proposed_abutting_road_width <=30 and c.m.proposed_bldg_height >7  and c.m.proposed_bldg_height <=15 ):
				front_sb=6.0
				rear_sides_sb=6.0
			elif (c.m.proposed_abutting_road_width > 30 and c.m.proposed_bldg_height >7  and c.m.proposed_bldg_height <=15 ):
				front_sb=7.5
				rear_sides_sb=6.0
			elif (c.m.proposed_abutting_road_width <=12 and c.m.proposed_bldg_height >15):
				front_sb=3.0
				rear_sides_sb=7.0
			elif (c.m.proposed_abutting_road_width > 12 and c.m.proposed_abutting_road_width <=18 and c.m.proposed_bldg_height > 15 ):
				front_sb=4.0
				rear_sides_sb=7.0
			elif (c.m.proposed_abutting_road_width > 18 and c.m.proposed_abutting_road_width <=24 and c.m.proposed_bldg_height >15 ):
				front_sb=5.0
				rear_sides_sb=7.0

			elif (c.m.proposed_abutting_road_width > 24 and c.m.proposed_abutting_road_width <=30 and c.m.proposed_bldg_height >15 ):
				front_sb=6.0
				rear_sides_sb=7.0
			elif (c.m.proposed_abutting_road_width > 30 and c.m.proposed_bldg_height > 15  ):
				front_sb=7.5
				rear_sides_sb=7.0
			else:
				front_sb=7.5
				rear_sides_sb=7.0



		#Bldg Height > 18 mt. Not Allowed
		if (c.m.proposed_bldg_height > max_bldg_height_allowed  ):
			bldg_height_exceedlimits =True  #sets status as NOT OK

		#min. required site area #common
		if (m.subtype == 'STANDALONE'):
			required_site_area=50
		else:
			required_site_area=335



		rule_txt="Abutting Roadwidth " + str(c.m.proposed_abutting_road_width)

		required_front_setback=front_sb
		required_rear_setback=rear_sides_sb
		required_side1_setback=rear_sides_sb
		required_side2_setback=rear_sides_sb



		rule_applicable="For Type of {0}, Site Area: {1} and {2} a) Requires Min. Abutting Road Width {3} mt. b) Requires  Min. Setbacks in mts. for front/rear/side1/sides are {4}/{5}/{6}/{7} ".format(\
			c.m.subtype,required_site_area, rule_txt, required_abutting_road_width ,required_front_setback,required_rear_setback,required_side1_setback,required_side2_setback)

		results['required_abutting_road_width'] = required_abutting_road_width
		results['required_site_area']=required_site_area
		results['required_front_setback'] = required_front_setback
		results['required_rear_setback'] =  required_rear_setback
		results['required_side1_setback'] = required_side1_setback
		results['required_side2_setback'] = required_side2_setback
		rule_txt=rule_applicable

		if (bldg_height_exceedlimits == False and c.m.proposed_abutting_road_width  >= required_abutting_road_width and
			c.m.proposed_site_area >= required_site_area and
			c.m.proposed_front_setback >= required_front_setback and
			c.m.proposed_rear_setback >= required_rear_setback and
			c.m.proposed_side1_setback >= required_side1_setback and
			c.m.proposed_side2_setback >= required_side2_setback  ):
			results['status']="OK"
		else:
			results['status']="NOT OK"

		if (bldg_height_exceedlimits):
			results['status']="NOT OK"
			results['zrule']="As per Rule No .5, G.O.Ms.No .168. Bldg Height >" + str(max_bldg_height_allowed) + " mt. Not Allowed"
		else:
			results['zrule']="As per Rule No .5, G.O.Ms.No .168." + rule_applicable

		c.s.result=results

	

# SPLAY RULES 
with ruleset('ts-splay'):
	""" based on road width the splay requirement len, width changes
	   factor:  road width :
	   values to compare: len, width
	   road width	required len, width
	    < 12 		3, 3
	    >12 < 24 	4.5, 4.5
	    >24			6,6


	zrule-splay=[r'{As per Rule No.5, G.O.Ms.No.168}',
	r'Splay at road junctions, including "Y" junctions, shall be provided as follows. The area of such splay would be deemed to form part of the road junction. ',
	r'Road width (meters) -  Splay offset len and width (meters)',
	r'12 - 3x3  ',
	r'>=12 and <24 - 4.5x4.5  ',
	r'>=24 - 6x6  '
	]
	"""

	@when_all(m.roadwidth <0 or m.length <0 or m.width<0)
	def invalid(c):
		raise engine.MessageNotHandledException("Missing values")

	# # when the exception property exists
	# @when_all(+s.exception)
	# def invalid_input(c):
	# 	print(c.s.exception)
	# 	c.s.exception = None
	# 	results={"status":"ERROR", "msg" :"Missing values Roadwidth/splay len/splay width" + str(m.roadwidth.value) + "/" + str(m.length) + "/" + str(m.width)}
	# 	return results


	@when_all(m.roadwidth >= 0 and m.roadwidth <= 12 )
	def low_splay(c):
		c.s.result=''
		results=dict()
		results['abutting_roadwidth']=c.m.roadwidth
		results['required_length']=3
		results['required_width']=3

		# results['proposed_length']=c.m.length
		# results['proposed_width']=c.m.width
		if (c.m.length >= results['required_length'] and c.m.width >= results['required_width']):
			results['status']="OK"
		else:
			results['status']="NOT OK"

		# print(str(results))

		results['zrule']="As per Rule No.5, G.O.Ms.No.168, Splay at road junctions, including Y junctions, shall be provided as follows. The area of such splay would be deemed to form part of the road junction. Road width (meters) -  Splay offset len and width (meters) a) Road width <=12 - 3x3 b) Road width >12 and <=24 - 4.5x4.5  c)Road width >24 - 6x6  "

		c.s.result=results

	@when_all(m.roadwidth > 12 and m.roadwidth <= 24 )
	def med_splay(c):
		c.s.result=''
		results=dict()
		results['abutting_roadwidth']=c.m.roadwidth
		results['required_length']=4.5
		results['required_width']=4.5

		# results['proposed_length']=c.m.length
		# results['proposed_width']=c.m.width
		if (c.m.length >= results['required_length'] and c.m.width >= results['required_width']):
			results['status']="OK"

		else:
			results['status']="NOT OK"

		results['zrule']="As per Rule No.5, G.O.Ms.No.168, Splay at road junctions, including Y junctions, shall be provided as follows. The area of such splay would be deemed to form part of the road junction. Road width (meters) -  Splay offset len and width (meters) a) Road width <=12 - 3x3 b) Road width >12 and <=24 - 4.5x4.5  c)Road width >24 - 6x6  "
		# print(str(results))
		c.s.result=results

	@when_all(m.roadwidth > 24 )
	def high_splay(c):
		c.s.result=''
		results=dict()
		results['abutting_roadwidth']=c.m.roadwidth
		results['required_length']=6.0
		results['required_width']=6.0
		# results['zrule']=zrule
		# results['proposed_length']=c.m.length
		# results['proposed_width']=c.m.width
		if (c.m.length >= results['required_length'] and c.m.width >= results['required_width']):
			results['status']="OK"

		else:
			results['status']="NOT OK"
		results['zrule']="As per Rule No.5, G.O.Ms.No.168, Splay at road junctions, including Y junctions, shall be provided as follows. The area of such splay would be deemed to form part of the road junction. Road width (meters) -  Splay offset len and width (meters) a) Road width <=12 - 3x3 b) Road width >12 and <=24 - 4.5x4.5  c)Road width >24 - 6x6  "
		# print(str(results))
		c.s.result=results

#For Single Rule - mortgage will be at plan level
def callrule(ruleName,params):

	try:
		# post('ts-splay', { 'length':4.5, 'width':4.5})
		return post(ruleName, params)
	except Exception as ex:
		msg="Invalid inputs to process Rule - {0} :  {1} actual params - {2} ".format(ruleName, RULES_PARAMS[ruleName] , params)
		print(msg)
		results=dict()
		results={"status":"ERROR","msg":msg }
		return results

#For Batch of Objects for a given Rule - splay list will be more 
# def callBatch(ruleName,messages):
# 	allresults=[]
# 	try:
# 		messagesList=messages.get('splaylist')
# 		# post('ts-splay', { 'length':4.5, 'width':4.5})
# 		for msg in messagesList:
# 			print("processing " + str(msg) )
# 			tmp=callrule(ruleName, msg)
# 			print('results' + str(tmp))
# 			allresults.append(tmp)
# 			return allresults
# 	except Exception as ex:
# 		msg="Invalid inputs to process Rule - {0} :  {1} actual params - {2} ".format(ruleName, RULES_PARAMS[ruleName] , params)
# 		print(msg)
# 		results=dict()
# 		results={"status":"ERROR","msg":msg}
# 		return results