#------------------------------------------------Modules-------------------------------------------------

from shapely.geometry import Point,Polygon

from shapely.geometry import LineString

import numpy as np
import ezdxf

class ValidationLayersForOpenLayout:

    def LayersOverlappingWithEachOther(self,accessoryUsedata,amenitydata,internalroaddata,bufferzonedata,subplotsdata,orgnizedopenspacedata,roadwideningdata,nalawideningdata,watterbodiesdata):

        Error_OverlappingWithEachOther=[]

        if accessoryUsedata!=[]:

            for accessory_data in accessoryUsedata:

                if str(accessory_data[1].lower()).replace(' ','')=='utility':

                    #print(accessory_data[1])

                    utility_polygon_points=Polygon([ap[0:2] for ap in accessory_data[2].get_points()])

                    overlapping_on_accessorydata=[amenitydata,internalroaddata,bufferzonedata,subplotsdata,orgnizedopenspacedata, roadwideningdata, nalawideningdata, watterbodiesdata]

                    for overlap_layer in overlapping_on_accessorydata:

                        for layer_data in overlap_layer:

                            ovelap_polygon_points=[utility_polygon_points.contains(Point(ol[0:2])) for ol in layer_data[2].get_points()]

                            if ovelap_polygon_points.count(True)>=2:

                                ErrorMsg=f'Warning:{layer_data[1]} REF ({layer_data[0]}) Overlapping On {accessory_data[1]} ({accessory_data[0]})'

                                Error_OverlappingWithEachOther.append(ErrorMsg)

        if(amenitydata!=[]):

            for amenity_data in amenitydata:

                amenity_polygon_points = Polygon([ap[0:2] for ap in amenity_data[2].get_points()])

                overlapping_on_amenitydata = [internalroaddata, bufferzonedata, subplotsdata,orgnizedopenspacedata, roadwideningdata, nalawideningdata,watterbodiesdata]

                for overlap_layer in overlapping_on_amenitydata:

                    for layer_data in overlap_layer:

                        ovelap_polygon_points = [amenity_polygon_points.contains(Point(ol[0:2])) == True for ol in layer_data[2].get_points()]

                        if ovelap_polygon_points.count(True) >= 2:

                            ErrorMsg = f'Warning:{layer_data[1]} REF ({layer_data[0]}) Overlapping On {amenity_data[1]} ({amenity_data[0]})'

                            Error_OverlappingWithEachOther.append(ErrorMsg)

                for accessory_data in accessoryUsedata:

                    if str(accessory_data[1].lower()).replace(' ','')=='utility':

                        accessory_polygon_points = [amenity_polygon_points.contains(Point(ap[0:2])) == True for ap in accessory_data[2].get_points()]

                        if accessory_polygon_points.count(True) >= 2:

                            ErrorMsg = f'Warning:{accessory_data[1]} REF ({accessory_data[0]}) Overlapping On {amenity_data[1]} ({amenity_data[0]})'

                            Error_OverlappingWithEachOther.append(ErrorMsg)

        if (internalroaddata != []):

            for internalroad_data in internalroaddata:

                internalroad_polygon_points = Polygon([ip[0:2] for ip in internalroad_data[2].get_points()])

                overlapping_on_internalroaddata = [amenitydata, bufferzonedata, subplotsdata, orgnizedopenspacedata,roadwideningdata, nalawideningdata, watterbodiesdata]

                for overlap_layer in overlapping_on_internalroaddata:

                    for layer_data in overlap_layer:

                        ovelap_polygon_points = [internalroad_polygon_points.contains(Point(ol[0:2])) == True for ol in layer_data[2].get_points()]

                        if ovelap_polygon_points.count(True) >= 2:

                            ErrorMsg = f'Warning:{layer_data[1]} REF ({layer_data[0]}) Overlapping On {internalroad_data[1]} ({internalroad_data[0]})'

                            Error_OverlappingWithEachOther.append(ErrorMsg)

                for accessory_data in accessoryUsedata:

                    if str(accessory_data[1].lower()).replace(' ', '') == 'utility':

                        accessory_polygon_points = [internalroad_polygon_points.contains(Point(ap[0:2])) == True for ap in accessory_data[2].get_points()]

                        if accessory_polygon_points.count(True) >= 2:

                            ErrorMsg = f'Warning:{accessory_data[1]} REF ({accessory_data[0]}) Overlapping On {internalroad_data[1]} ({internalroad_data[0]})'

                            Error_OverlappingWithEachOther.append(ErrorMsg)

        if (bufferzonedata != []):

            for bufferzone_data in bufferzonedata:

                bufferzone_polygon_points = Polygon([bp[0:2] for bp in bufferzone_data[2].get_points()])

                overlapping_on_amenitydata = [amenitydata, internalroaddata, subplotsdata, orgnizedopenspacedata,roadwideningdata, nalawideningdata, watterbodiesdata]

                for overlap_layer in overlapping_on_amenitydata:

                    for layer_data in overlap_layer:

                        ovelap_polygon_points = [bufferzone_polygon_points.contains(Point(ol[0:2])) == True for ol in layer_data[2].get_points()]

                        if ovelap_polygon_points.count(True) >= 2:

                            ErrorMsg = f'Warning:{layer_data[1]} REF ({layer_data[0]}) Overlapping On {bufferzone_data[1]} ({bufferzone_data[0]})'

                            Error_OverlappingWithEachOther.append(ErrorMsg)

                for accessory_data in accessoryUsedata:

                    if str(accessory_data[1].lower()).replace(' ', '') == 'utility':

                        accessory_polygon_points = [bufferzone_polygon_points.contains(Point(ap[0:2])) == True for ap in accessory_data[2].get_points()]

                        if accessory_polygon_points.count(True) >= 2:

                            ErrorMsg = f'Warning:{accessory_data[1]} REF ({accessory_data[0]}) Overlapping On {bufferzone_data[1]} ({bufferzone_data[0]})'

                            Error_OverlappingWithEachOther.append(ErrorMsg)

        if (subplotsdata != []):

            for subplot_data in subplotsdata:

                subplot_polygon_points = Polygon([sp[0:2] for sp in subplot_data[2].get_points()])

                overlapping_on_subplotdata = [amenitydata, internalroaddata, bufferzonedata, orgnizedopenspacedata,roadwideningdata, nalawideningdata, watterbodiesdata]

                for overlap_layer in overlapping_on_subplotdata:

                    for layer_data in overlap_layer:

                        ovelap_polygon_points = [subplot_polygon_points.contains(Point(ol[0:2])) == True for ol in layer_data[2].get_points()]

                        if ovelap_polygon_points.count(True) >= 2:

                            ErrorMsg = f'Warning:{layer_data[1]} REF ({layer_data[0]}) Overlapping On {subplot_data[1]} ({subplot_data[0]})'

                            Error_OverlappingWithEachOther.append(ErrorMsg)

                for accessory_data in accessoryUsedata:

                    if str(accessory_data[1].lower()).replace(' ', '') == 'utility':

                        accessory_polygon_points = [subplot_polygon_points.contains(Point(ap[0:2])) == True for ap in accessory_data[2].get_points()]

                        if accessory_polygon_points.count(True) >= 2:
                            ErrorMsg = f'Warning:{accessory_data[1]} REF ({accessory_data[0]}) Overlapping On {subplot_data[1]} ({subplot_data[0]})'

                            Error_OverlappingWithEachOther.append(ErrorMsg)

        if (orgnizedopenspacedata != []):

            for organizedopenspace_data in orgnizedopenspacedata:

                organizedopenspace_polygon_points = Polygon([op[0:2] for op in organizedopenspace_data[2].get_points()])

                overlapping_on_organizedopenspacedata = [amenitydata, internalroaddata, bufferzonedata, subplotsdata,roadwideningdata, nalawideningdata, watterbodiesdata]

                for overlap_layer in overlapping_on_organizedopenspacedata:

                    for layer_data in overlap_layer:

                        ovelap_polygon_points = [organizedopenspace_polygon_points.contains(Point(ol[0:2])) for ol in layer_data[2].get_points()]

                        if ovelap_polygon_points.count(True) >= 2:

                            ErrorMsg = f'Warning:{layer_data[1]} REF ({layer_data[0]}) Overlapping On {organizedopenspace_data[1]} ({organizedopenspace_data[0]})'

                            Error_OverlappingWithEachOther.append(ErrorMsg)

                for accessory_data in accessoryUsedata:

                    if str(accessory_data[1].lower()).replace(' ', '') == 'utility':

                        accessory_polygon_points = [organizedopenspace_polygon_points.contains(Point(ap[0:2])) for ap in accessory_data[2].get_points()]

                        if accessory_polygon_points.count(True) >= 2:

                            ErrorMsg = f'Warning:{accessory_data[1]} REF ({accessory_data[0]}) Overlapping On {organizedopenspace_data[1]} ({organizedopenspace_data[0]})'

                            Error_OverlappingWithEachOther.append(ErrorMsg)

        if (roadwideningdata != []):

            for roadwidening_data in roadwideningdata:

                roadwidening_polygon_points = Polygon([rp[0:2] for rp in roadwidening_data[2].get_points()])

                overlapping_on_roadwidening = [amenitydata, internalroaddata, bufferzonedata, subplotsdata,orgnizedopenspacedata, nalawideningdata, watterbodiesdata]

                for overlap_layer in overlapping_on_roadwidening:

                    for layer_data in overlap_layer:

                        ovelap_polygon_points = [roadwidening_polygon_points.contains(Point(ol[0:2])) == True for ol in layer_data[2].get_points()]

                        if ovelap_polygon_points.count(True) >= 2:

                            ErrorMsg = f'Warning:{layer_data[1]} REF ({layer_data[0]}) Overlapping On {roadwidening_data[1]} ({roadwidening_data[0]})'

                            Error_OverlappingWithEachOther.append(ErrorMsg)

                for accessory_data in accessoryUsedata:

                    if str(accessory_data[1].lower()).replace(' ', '') == 'utility':

                        accessory_polygon_points = [roadwidening_polygon_points.contains(Point(ap[0:2])) == True for ap in accessory_data[2].get_points()]

                        if accessory_polygon_points.count(True) >= 2:

                            ErrorMsg = f'Warning:{accessory_data[1]} REF ({accessory_data[0]}) Overlapping On {roadwidening_data[1]} ({roadwidening_data[0]})'

                            Error_OverlappingWithEachOther.append(ErrorMsg)

        if (nalawideningdata != []):

            for nalawidening_data in nalawideningdata:

                nalawidening_polygon_points = Polygon([np[0:2] for np in nalawidening_data[2].get_points()])

                overlapping_on_nalawidening = [amenitydata, internalroaddata, bufferzonedata, subplotsdata,
                                               orgnizedopenspacedata, roadwideningdata, watterbodiesdata]

                for overlap_layer in overlapping_on_nalawidening:

                    for layer_data in overlap_layer:

                        ovelap_polygon_points = [nalawidening_polygon_points.contains(Point(ol[0:2])) == True for ol in
                                                 layer_data[2].get_points()]

                        if ovelap_polygon_points.count(True) >= 2:

                            ErrorMsg = f'Warning:{layer_data[1]} REF ({layer_data[0]}) Overlapping On {nalawidening_data[1]} ({nalawidening_data[0]})'

                            Error_OverlappingWithEachOther.append(ErrorMsg)

                for accessory_data in accessoryUsedata:

                    if str(accessory_data[1].lower()).replace(' ', '') == 'utility':

                        accessory_polygon_points = [nalawidening_polygon_points.contains(Point(ap[0:2])) == True for ap in accessory_data[2].get_points()]

                        if accessory_polygon_points.count(True) >= 2:

                            ErrorMsg = f'Warning:{accessory_data[1]} REF ({accessory_data[0]}) Overlapping On {nalawidening_data[1]} ({nalawidening_data[0]})'

                            Error_OverlappingWithEachOther.append(ErrorMsg)

        if (watterbodiesdata != []):

            for watterbodies_data in watterbodiesdata:

                watterbodies_polygon_points = Polygon([wp[0:2] for wp in watterbodies_data[2].get_points()])

                overlapping_on_watterbodies = [amenitydata, internalroaddata, bufferzonedata, subplotsdata,
                                               orgnizedopenspacedata, roadwideningdata, nalawideningdata]

                for overlap_layer in overlapping_on_watterbodies:

                    for layer_data in overlap_layer:

                        ovelap_polygon_points = [watterbodies_polygon_points.contains(Point(ol[0:2])) == True for ol in layer_data[2].get_points()]

                        if ovelap_polygon_points.count(True) >= 2:

                            ErrorMsg = f'Warning:{layer_data[1]} REF ({layer_data[0]}) Overlapping On {watterbodies_data[1]} ({watterbodies_data[0]})'

                            Error_OverlappingWithEachOther.append(ErrorMsg)

                for accessory_data in accessoryUsedata:

                    if str(accessory_data[1].lower()).replace(' ', '') == 'utility':

                        accessory_polygon_points = [watterbodies_polygon_points.contains(Point(ap[0:2])) == True for ap in accessory_data[2].get_points()]

                        if accessory_polygon_points.count(True) >= 2:

                            ErrorMsg = f'Warning:{accessory_data[1]} REF ({accessory_data[0]}) Overlapping On {watterbodies_data[1]} ({watterbodies_data[0]})'

                            Error_OverlappingWithEachOther.append(ErrorMsg)
        #print(Error_OverlappingWithEachOther)

        return Error_OverlappingWithEachOther

    def CycletrackabovetenacrsINPlot(self,PlotlayerDict,CycletracklayerDict):

        ErrorWaterBodiesDict=dict()

        for plot in PlotlayerDict.values():

            plot_polygon_points=Polygon(np.array([pp[0:2] for pp in plot[2].get_points()]))

            plot_area=round(round(plot_polygon_points.area,2)/4046.86,1)

            if plot_area>=10.0:

                cycletrackContainplotabvtenacr=[]

                for cycletrack in CycletracklayerDict.values():

                    cycletrack_polygon_points = Polygon(np.array([cp[0:2] for cp in cycletrack[2].get_points()]))

                    if cycletrack_polygon_points.contains(cycletrack_polygon_points)==True or cycletrack_polygon_points.touches(cycletrack_polygon_points)==True or round(cycletrack_polygon_points.distance(cycletrack_polygon_points),1)==0.0:

                        cycletrackContainplotabvtenacr.append(True)

                if cycletrackContainplotabvtenacr==[] and len(cycletrackContainplotabvtenacr)==0:

                    ErrorMsg = f'Warning:{plot[1]} ({plot[0]}) Missing Cycletrack Layer for {plot_area} acre Required For Above 10 acre.'

                    ErrorWaterBodiesDict[plot[0]] = ErrorMsg

        return ErrorWaterBodiesDict

    def RoadWideningTouchAnyOne(self,RoadWideningLayerDict,NetPlotLayerDict,PlotLayerDict,WallCompoundDict,OrganizedOpenSpaceDict,BufferZoneDict):

        ErrorWaterBodiesDict=dict()

        for roadwidening in RoadWideningLayerDict.values():
            #print(roadwidening)
            roadwidening_polygon_points=Polygon(np.array([rwp[0:2] for rwp in roadwidening[2].get_points()]))

            RoadWideningTouchWithAnyOne=[]

            for netplot in NetPlotLayerDict.values():

                netplot_polygon_points = Polygon(np.array([np[0:2] for np in netplot.get_points()]))

                if roadwidening_polygon_points.touches(netplot_polygon_points)==True or round(roadwidening_polygon_points.distance(netplot_polygon_points),1)==0.0:

                    RoadWideningTouchWithAnyOne.append(True)

                else:

                    RoadWideningTouchWithAnyOne.append(False)

            for plot in PlotLayerDict.values():
                #print(plot)
                plot_polygon_points = Polygon(np.array([pp[0:2] for pp in plot[2].get_points()]))

                if roadwidening_polygon_points.touches(plot_polygon_points)==True or round(roadwidening_polygon_points.distance(plot_polygon_points),1)==0.0:

                    RoadWideningTouchWithAnyOne.append(True)

                else:

                    RoadWideningTouchWithAnyOne.append(False)

            for wallcompound in WallCompoundDict.values():

                wallcompound_polygon_points = Polygon(np.array([wcp[0:2] for wcp in wallcompound.get_points()]))

                if roadwidening_polygon_points.touches(wallcompound_polygon_points) == True or round(roadwidening_polygon_points.distance(wallcompound_polygon_points), 1) == 0.0:

                    RoadWideningTouchWithAnyOne.append(True)

                else:

                    RoadWideningTouchWithAnyOne.append(False)

            for organizedopenspace in OrganizedOpenSpaceDict.values():
                
                organizedopenspace_polygon_points = Polygon(np.array([orgp[0:2] for orgp in organizedopenspace[2].get_points()]))

                if roadwidening_polygon_points.touches(organizedopenspace_polygon_points) == True or round(roadwidening_polygon_points.distance(organizedopenspace_polygon_points), 1) == 0.0:

                    RoadWideningTouchWithAnyOne.append(True)

                else:

                    RoadWideningTouchWithAnyOne.append(False)

            for bufferzone in BufferZoneDict.values():
                
                bufferzone_polygon_points = Polygon(np.array([bzp[0:2] for bzp in bufferzone[2].get_points()]))

                if roadwidening_polygon_points.touches(bufferzone_polygon_points) == True or round(roadwidening_polygon_points.distance(bufferzone_polygon_points), 1) == 0.0:

                    RoadWideningTouchWithAnyOne.append(True)

                else:

                    RoadWideningTouchWithAnyOne.append(False)

            if RoadWideningTouchWithAnyOne!=[] or len(RoadWideningTouchWithAnyOne)>0:

                if any(RoadWideningTouchWithAnyOne)==False:

                    ErrorMsg=f'Warning:{roadwidening[1]} ({roadwidening[0]}) Does Not Touch With Plot,NetPlot,WallCompound,OrganizedOpenSpace Or BufferZone Layer.'

                    ErrorWaterBodiesDict[roadwidening[0]]=ErrorMsg

        return ErrorWaterBodiesDict

    def WaterBodiesTouchAnyOne(self,WaterBodiesLayerDict,NetPlotLayerDict,PlotLayerDict,WallCompoundDict,OrganizedOpenSpaceDict,BufferZoneDict):

        ErrorWaterBodiesDict=dict()

        for waterbodies in WaterBodiesLayerDict.values():

            waterbodies_polygon_points=Polygon(np.array([wbp[0:2] for wbp in waterbodies[2].get_points()]))

            WaterBodiesTouchWithAnyOne=[]

            for netplot in NetPlotLayerDict.values():

                netplot_polygon_points = Polygon(np.array([np[0:2] for np in netplot[2].get_points()]))

                if waterbodies_polygon_points.touches(netplot_polygon_points)==True or round(waterbodies_polygon_points.distance(netplot_polygon_points),1)==0.0:

                    WaterBodiesTouchWithAnyOne.append(True)

                else:

                    WaterBodiesTouchWithAnyOne.append(False)

            for plot in PlotLayerDict.values():

                plot_polygon_points = Polygon(np.array([pp[0:2] for pp in plot[2].get_points()]))

                if waterbodies_polygon_points.touches(plot_polygon_points)==True or round(waterbodies_polygon_points.distance(plot_polygon_points),1)==0.0:

                    WaterBodiesTouchWithAnyOne.append(True)

                else:

                    WaterBodiesTouchWithAnyOne.append(False)

            for wallcompound in WallCompoundDict.values():

                wallcompound_polygon_points = Polygon(np.array([wcp[0:2] for wcp in wallcompound[2].get_points()]))

                if waterbodies_polygon_points.touches(wallcompound_polygon_points) == True or round(waterbodies_polygon_points.distance(wallcompound_polygon_points), 1) == 0.0:

                    WaterBodiesTouchWithAnyOne.append(True)

                else:

                    WaterBodiesTouchWithAnyOne.append(False)

            for organizedopenspace in OrganizedOpenSpaceDict.values():

                organizedopenspace_polygon_points = Polygon(np.array([orgp[0:2] for orgp in organizedopenspace[2].get_points()]))

                if waterbodies_polygon_points.touches(organizedopenspace_polygon_points) == True or round(waterbodies_polygon_points.distance(organizedopenspace_polygon_points), 1) == 0.0:

                    WaterBodiesTouchWithAnyOne.append(True)

                else:

                    WaterBodiesTouchWithAnyOne.append(False)

            for bufferzone in BufferZoneDict.values():

                bufferzone_polygon_points = Polygon(np.array([bzp[0:2] for bzp in bufferzone[2].get_points()]))

                if waterbodies_polygon_points.touches(bufferzone_polygon_points) == True or round(waterbodies_polygon_points.distance(bufferzone_polygon_points), 1) == 0.0:

                    WaterBodiesTouchWithAnyOne.append(True)

                else:

                    WaterBodiesTouchWithAnyOne.append(False)

            if WaterBodiesTouchWithAnyOne!=[] or len(WaterBodiesTouchWithAnyOne)>0:

                if any(WaterBodiesTouchWithAnyOne)==False:

                    ErrorMsg=f'Warning:{waterbodies[1]} ({waterbodies[0]}) Does Not Touch With Plot,NetPlot,WallCompound,OrganizedOpenSpace Or BufferZone Layer.'

                    ErrorWaterBodiesDict[waterbodies[0]]=ErrorMsg

        return ErrorWaterBodiesDict

    def SplayWithSubplotLayer(self,SplayDict,SubPlotDict):

        ErrorSplayLayerDict=dict()

        for splay in SplayDict.values():

            splay_polygon_points=Polygon(np.array([sp[0:2] for sp in splay[2].get_points()]))

            SplayWithSubplot=[]

            for subplot in SubPlotDict.values():

                subplot_polygon_points=Polygon(np.array([spp[0:2] for spp in subplot[2].get_points()]))

                if splay_polygon_points.touches(subplot_polygon_points)==True or round(splay_polygon_points.distance(subplot_polygon_points),1)==0.0:

                    SplayWithSubplot.append(True)

                else:

                    SplayWithSubplot.append(False)

            if SplayWithSubplot!=[] and len(SplayWithSubplot)>0:

                if any(SplayWithSubplot)==False:

                    ErrorMsg=f'Warning:{splay[1]} ({splay[0]}) Does Not Touch With SubPlot Layer.'

                    ErrorSplayLayerDict[splay[0]]=ErrorMsg

        return ErrorSplayLayerDict

    def NetPlotWithPlotLayer(self,NetPlotLayerDict,PlotLayerDict):

        ErrorNetPlotLayerDict=dict()

        for netplot in NetPlotLayerDict.values():

            netplot_polygon_points=Polygon(np.array([nnp[0:2] for nnp in netplot[2].get_points()]))

            NetplotTouchPlot=[]

            for plot in PlotLayerDict.values():

                plot_polygon_points=Polygon(np.array([np[0:2] for np in plot[2].get_points()]))

                if netplot_polygon_points.touches(plot_polygon_points)==True or round(netplot_polygon_points.distance(plot_polygon_points),1)==0.0:

                    NetplotTouchPlot.append(True)

                else:

                    NetplotTouchPlot.append(False)

            if NetplotTouchPlot!=[] and len(NetplotTouchPlot)>0:

                if any(NetplotTouchPlot)==False:

                    ErrorMsg=f'Warning:{netplot[1]} ({netplot[0]}) Does Not Touch With Plot Layer.'

                    ErrorNetPlotLayerDict[netplot[0]]=ErrorMsg

        return ErrorNetPlotLayerDict

    def OrganizedOpenSpaceOverlap(self,OrganizedOpenSpaceDict,MortgageAreaDict, AccessoryUseDict, InternalRoadDict,MainRoadDict, NalaWideningDict,PlotDict,AmenityDict,BufferZoneDict,RoadWideningDict):

        OrganizedOpenSpaceErrorDict=dict()

        for organizedopenspace in OrganizedOpenSpaceDict.values():

            organizedopenspace_polygon_points=Polygon(np.array([orgp[0:2] for orgp in organizedopenspace[2].get_points()]))

            OrganizedOpenSpaceOverlap=[]

            for accessoryuse in AccessoryUseDict.values():

                accessoryuse_polygon_points = np.array([ap[0:2] for ap in accessoryuse[2].get_points()])

                OrgContainsAccessoryUse=[]

                for accessorypts in accessoryuse_polygon_points:

                    accessoryuse_Point=Point(accessorypts)

                    if organizedopenspace_polygon_points.contains(accessoryuse_Point)==True:

                        OrgContainsAccessoryUse.append(True)

                    else:

                        OrgContainsAccessoryUse.append(False)

                if OrgContainsAccessoryUse!=[] and len(OrgContainsAccessoryUse)>0:

                    if any(OrgContainsAccessoryUse)==True and OrgContainsAccessoryUse.count(True)>2:

                        ErrorMsg=f'Warning:OrganizedOpenSpace Layer Overlapping on {accessoryuse[1]} ({accessoryuse[0]}).'

                        OrganizedOpenSpaceOverlap.append(ErrorMsg)

            for internalroad in InternalRoadDict.values():

                internalroad_polygon_points = np.array([irp[0:2] for irp in internalroad[2].get_points()])

                OrgContaininternalroad=[]

                for internalroad_polygon_pts in internalroad_polygon_points:

                    internalroad_point=Point(internalroad_polygon_pts)

                    if organizedopenspace_polygon_points.contains(internalroad_point)==True :

                        OrgContaininternalroad.append(True)

                    else:

                        OrgContaininternalroad.append(False)

                if OrgContaininternalroad!=[] and len(OrgContaininternalroad)>0:

                   if any(OrgContaininternalroad)==True and OrgContaininternalroad.count(True)>2:

                        ErrorMsg = f'Warning:OrganizedOpenSpace Layer Overlapping on {internalroad[1]} ({internalroad[0]}).'

                        OrganizedOpenSpaceOverlap.append(ErrorMsg)

            for mainroad in MainRoadDict.values():

                mainroad_polygon_points = np.array([mrp[0:2] for mrp in mainroad[2].get_points()])

                OrgContainMainroad=[]

                for mainroadpts in mainroad_polygon_points:

                    mainroad_Point=Point(mainroadpts)

                    if organizedopenspace_polygon_points.contains(mainroad_Point)==True:

                        OrgContainMainroad.append(True)

                    else:

                        OrgContainMainroad.append(False)

                if OrgContainMainroad!=[] and len(OrgContainMainroad)>0:

                    if any(OrgContainMainroad) == True and OrgContainMainroad.count(True)>2:

                        ErrorMsg = f'Warning:OrganizedOpenSpace Layer Overlapping on {mainroad[1]} ({mainroad[0]}).'

                        OrganizedOpenSpaceOverlap.append(ErrorMsg)

            for nalawidening in NalaWideningDict.values():

                nalawidening_polygon_points = np.array([nwp[0:2] for nwp in nalawidening[2].get_points()])

                orgContainNalaWidening=[]

                for nalawideningpts in nalawidening_polygon_points:

                    nalawideningPoint=Point(nalawideningpts)

                    if organizedopenspace_polygon_points.contains(nalawideningPoint) == True:

                        orgContainNalaWidening.append(True)

                    else:

                        orgContainNalaWidening.append(False)

                if orgContainNalaWidening!=[] and len(orgContainNalaWidening)>0:

                    if any(orgContainNalaWidening)==True and orgContainNalaWidening.count(True)>2:

                        ErrorMsg = f'Warning:OrganizedOpenSpace Layer Overlapping on {nalawidening[1]} ({nalawidening[0]}).'

                        OrganizedOpenSpaceOverlap.append(ErrorMsg)

            for plot in PlotDict.values():

                plot_polygon_points = np.array([pp[0:2] for pp in plot[2].get_points()])

                OrgContainplot=[]

                for plotpts in plot_polygon_points:

                    if organizedopenspace_polygon_points.contains(Point(plotpts))==True:

                        OrgContainplot.append(True)

                    else:

                        OrgContainplot.append(False)


                if OrgContainplot!=[] and len(OrgContainplot)>0:

                    if any(OrgContainplot)==True and OrgContainplot.count(True)>2:

                        ErrorMsg = f'Warning:{plot[1]} ({plot[0]}) Overlapping on OrganizedOpenSpace Layer.'

                        OrganizedOpenSpaceOverlap.append(ErrorMsg)

            for amenity in AmenityDict.values():

                amenity_polygon_points = np.array([amp[0:2] for amp in amenity[2].get_points()])

                orgcontainamenity=[]

                for amenitypts in amenity_polygon_points:

                    amenity_Point=Point(amenitypts)

                    if organizedopenspace_polygon_points.contains(amenity_Point)==True:

                        orgcontainamenity.append(True)

                    else:

                        orgcontainamenity.append(False)

                if orgcontainamenity!=[] and len(orgcontainamenity)>0:

                    if any(orgcontainamenity)==True and orgcontainamenity.count(True)>2:

                        ErrorMsg = f'Warning:OrganizedOpenSpace Layer Overlapping on {amenity[1]} ({amenity[0]}).'

                        OrganizedOpenSpaceOverlap.append(ErrorMsg)

            for mortgagearea in MortgageAreaDict.values():

                mortgagearea_polygon_points = np.array([mortp[0:2] for mortp in mortgagearea[2].get_points()])

                orgContainMorgage=[]

                for mortgageareapts in mortgagearea_polygon_points:

                    mortgageareapts=Point(mortgageareapts)

                    if organizedopenspace_polygon_points.contains(mortgageareapts) == False:

                        orgContainMorgage.append(True)

                    else:

                        orgContainMorgage.append(False)

                if orgContainMorgage!=[] and len(orgContainMorgage)>0:

                    if any(orgContainMorgage)==True and orgContainMorgage.count(True)>2:

                        ErrorMsg = f'Warning:OrganizedOpenSpace Layer Overlapping on {mortgagearea[1]} ({mortgagearea[0]}).'

                        OrganizedOpenSpaceOverlap.append(ErrorMsg)

            for bufferzone in BufferZoneDict.values():

                bufferzone_polygon_points = np.array([bfp[0:2] for bfp in bufferzone[2].get_points()])

                orgContainBufferzone=[]

                for bufferzonepts in bufferzone_polygon_points:

                    bufferzonepoint=Point(bufferzonepts)

                    if organizedopenspace_polygon_points.contains(bufferzonepoint)==True:

                        orgContainBufferzone.append(True)

                    else:

                        orgContainBufferzone.append(False)

                if orgContainBufferzone!=[] and len(orgContainBufferzone)>0:

                    if any(orgContainBufferzone) == True and orgContainBufferzone.count(True)>2:

                        ErrorMsg = f'Warning:{bufferzone[1]} ({bufferzone[0]}) Overlapping on OrganizedOpenSpace Layer.'

                        OrganizedOpenSpaceOverlap.append(ErrorMsg)

            for roadwidening in RoadWideningDict.values():

                roadwidening_polygon_points = np.array([rwp[0:2] for rwp in roadwidening[2].get_points()])

                orgContainroadwidening=[]

                for roadwideningpts in roadwidening_polygon_points:

                    roadwidening_point=Point(roadwideningpts)

                    if organizedopenspace_polygon_points.contains(roadwidening_point)==True:

                        orgContainroadwidening.append(True)

                    else:

                        orgContainroadwidening.append(False)

                if orgContainroadwidening!=[] and len(orgContainroadwidening)>0:

                    if any(orgContainroadwidening) == True and orgContainroadwidening.count(True)>2:

                        ErrorMsg = f'Warning:{roadwidening[1]} ({roadwidening[0]}) Overlapping on OrganizedOpenSpace Layer.'

                        OrganizedOpenSpaceOverlap.append(ErrorMsg)

            if OrganizedOpenSpaceOverlap!=[] and len(OrganizedOpenSpaceOverlap)>0:

                for overlap_org_error in OrganizedOpenSpaceOverlap:

                    OrganizedOpenSpaceErrorDict[organizedopenspace[0]]=overlap_org_error

        #print(OrganizedOpenSpaceErrorDict)
        return OrganizedOpenSpaceErrorDict

    def MortgageAreaOverlap(self,MortgageAreaDict, AccessoryUseDict, InternalRoadDict,MainRoadDict, NalaWideningDict,PlotDict,AmenityDict,OrganizedOpenSpaceDict,BufferZoneDict,RoadWideningDict):

        MortgageAreaErrorDict=dict()

        for mortgagearea in MortgageAreaDict.values():

            mortgagearea_polygon_points=Polygon(np.array([mp[0:2] for mp in mortgagearea[2].get_points()]))

            MortgageOverlap=[]

            for accessoryuse in AccessoryUseDict.values():

                accessoryuse_polygon_points = np.array([ap[0:2] for ap in accessoryuse[2].get_points()])

                mortgageContainAccessoryUse=[]

                for accessoryusepts in accessoryuse_polygon_points:

                    accessoryuse_point=Point(accessoryusepts)

                    if mortgagearea_polygon_points.contains(accessoryuse_point)==True:

                        mortgageContainAccessoryUse.append(True)

                    else:

                        mortgageContainAccessoryUse.append(False)

                if mortgageContainAccessoryUse!=[] and len(mortgageContainAccessoryUse)>0:

                    if any(mortgageContainAccessoryUse)==True and mortgageContainAccessoryUse.count(True)>2:

                        ErrorMsg=f'Warning:Mortgage Layer Overlapping on {accessoryuse[1]} ({accessoryuse[0]}).'

                        MortgageOverlap.append(ErrorMsg)

            for internalroad in InternalRoadDict.values():

                internalroad_polygon_points =np.array([irp[0:2] for irp in internalroad[2].get_points()])

                MortgagecontainInternalroad=[]

                for internalroad in internalroad_polygon_points:

                    internalroad_point=Point(internalroad)

                    if mortgagearea_polygon_points.contains(internalroad_point)==True:

                        MortgagecontainInternalroad.append(True)

                    else:

                        MortgagecontainInternalroad.append(False)

                if MortgagecontainInternalroad!=[] and len(MortgagecontainInternalroad)>0:

                    if any(MortgagecontainInternalroad) == True and MortgagecontainInternalroad.count(True)>2:

                        ErrorMsg = f'Warning:Mortgage Layer Overlapping on {internalroad[1]} ({internalroad[0]}).'

                        MortgageOverlap.append(ErrorMsg)

            for mainroad in MainRoadDict.values():

                mainroad_polygon_pts=[mrp[0:2] for mrp in mainroad[2].get_points()]

                mainroad_polygon_points = Polygon(np.array(mainroad_polygon_pts))

                mortgagecontainmainroad=[]

                for mainroadpts in mainroad_polygon_pts:

                    mainroad_point=Point(mainroadpts)

                    if mortgagearea_polygon_points.contains(mainroad_point) == True:

                        mortgagecontainmainroad.append(True)

                    else:

                        mortgagecontainmainroad.append(False)

                if mortgagecontainmainroad!=[] and len(mortgagecontainmainroad)>0:

                    if any(mortgagecontainmainroad) == True and mortgagecontainmainroad.count(True)>2:

                        ErrorMsg = f'Warning:Mortgage Layer Overlapping on {mainroad[1]} ({mainroad[0]}).'

                        MortgageOverlap.append(ErrorMsg)

            for nalawidening in NalaWideningDict.values():

                nalawidening_polygon_points = np.array([nwp[0:2] for nwp in nalawidening[2].get_points()])

                mortgageContainnalawidening=[]

                for nalawideningpts in nalawidening_polygon_points:

                    nalawidening_point=Point(nalawideningpts)

                    if mortgagearea_polygon_points.contains(nalawidening_point)==True:

                        mortgageContainnalawidening.append(True)

                    else:

                        mortgageContainnalawidening.append(False)

                if mortgageContainnalawidening!=[] and len(mortgageContainnalawidening)>0:

                    if any(mortgageContainnalawidening) == True and mortgageContainnalawidening.count(True)>2:

                        ErrorMsg = f'Warning:Mortgage Layer Overlapping on {nalawidening[1]} ({nalawidening[0]}).'

                        MortgageOverlap.append(ErrorMsg)

            for plot in PlotDict.values():

                plot_polygon_points = np.array([pp[0:2] for pp in plot[2].get_points()])

                mortgageContainplot=[]

                for plotpts in plot_polygon_points:

                    plot_point=Point(plotpts)

                    if mortgagearea_polygon_points.contains(plot_point) == True:

                        mortgageContainplot.append(True)

                    else:

                        mortgageContainplot.append(False)

                if mortgageContainplot!=[] and len(mortgageContainplot)>0:

                    if any(mortgageContainplot)==True and mortgageContainplot.count(True)>2:

                        ErrorMsg = f'Warning:Mortgage Layer Overlapping on {plot[1]} ({plot[0]}).'

                        MortgageOverlap.append(ErrorMsg)

            for amenity in AmenityDict.values():

                amenity_polygon_points = np.array([amp[0:2] for amp in amenity[2].get_points()])

                mortgagecontainamenity=[]

                for amenitypts in amenity_polygon_points:

                    amenity_point=Point(amenitypts)

                    if mortgagearea_polygon_points.intersects(amenity_point) == True:

                        mortgagecontainamenity.append(True)

                    else:

                        mortgagecontainamenity.append(False)

                if mortgagecontainamenity!=[] and len(mortgagecontainamenity)>0:

                    if any(mortgagecontainamenity) == True and mortgagecontainamenity.count(True)>2:

                        ErrorMsg = f'Warning:Mortgage Layer Overlapping on {amenity[1]} ({amenity[0]}).'

                        MortgageOverlap.append(ErrorMsg)

            for organizedOpenspace in OrganizedOpenSpaceDict.values():

                organizedOpenspace_polygon_points = np.array([orgp[0:2] for orgp in organizedOpenspace[2].get_points()])

                mortgagecontainorganizedopenspace=[]

                for organizedopenspacepts in organizedOpenspace_polygon_points:

                    organizedopenspace_point=Point(organizedopenspacepts)

                    if mortgagearea_polygon_points.contains(organizedopenspace_point) ==True:

                        mortgagecontainorganizedopenspace.append(True)

                    else:

                        mortgagecontainorganizedopenspace.append(False)

                if mortgagecontainorganizedopenspace!=[] and len(mortgagecontainorganizedopenspace)>0:

                    if any(mortgagecontainorganizedopenspace) == True and mortgagecontainorganizedopenspace.count(True)>2:

                        ErrorMsg = f'Warning:Mortgage Layer Overlapping on {organizedOpenspace[1]} ({organizedOpenspace[0]}).'

                        MortgageOverlap.append(ErrorMsg)

            for bufferzone in BufferZoneDict.values():

                bufferzone_polygon_points =np.array([bfp[0:2] for bfp in bufferzone[2].get_points()])

                mortgagecontainbufferzone=[]

                for bufferzonepts in bufferzone_polygon_points:

                    bufferzone_point=Point(bufferzonepts)

                    if mortgagearea_polygon_points.contains(bufferzone_point) == True:

                        mortgagecontainbufferzone.append(True)

                    else:

                        mortgagecontainbufferzone.append(False)

                if mortgagecontainbufferzone!=[] and len(mortgagecontainbufferzone)>0:

                    if any(mortgagecontainbufferzone)==True and mortgagecontainbufferzone.count(True)>2:

                        ErrorMsg = f'Warning:Mortgage Layer Overlapping on {bufferzone[1]} ({bufferzone[0]}).'

                        MortgageOverlap.append(ErrorMsg)

            for roadwidening in RoadWideningDict.values():

                roadwidening_polygon_points =np.array([rwp[0:2] for rwp in roadwidening[2].get_points()])

                mortgageContainroadwidening=[]

                for roadwideningpts in roadwidening_polygon_points:

                    roadwidening_point=Point(roadwideningpts)

                    if mortgagearea_polygon_points.contains(roadwidening_point) == True:

                        mortgageContainroadwidening.append(True)

                    else:

                        mortgageContainroadwidening.append(False)

                if mortgageContainroadwidening!=[] and len(mortgageContainroadwidening)>0:

                    if any(mortgageContainroadwidening) == True and mortgageContainroadwidening.count(True)>2:

                        ErrorMsg = f'Warning:Mortgage Layer Overlapping on {roadwidening[1]} ({roadwidening[0]}).'

                        MortgageOverlap.append(ErrorMsg)

            if MortgageOverlap!=[] and len(MortgageOverlap)>0:

                for MortgageLayerOverlapErrorMsg in MortgageOverlap:

                    MortgageAreaErrorDict[mortgagearea[0]]=MortgageLayerOverlapErrorMsg

        return MortgageAreaErrorDict

    def MainRoadtouchPCRN(self,MainRoadLayerDict,PlotLayerDict,WallCompoundLayerDict,RoadWideningsLayerDict,NalaWideningsLayerDict):

        ErrorMainRoad=dict()

        for mainroad in MainRoadLayerDict.values():

            mainroad_polygon_points=Polygon(np.array([mrp[0:2] for mrp in mainroad[2].get_points()]))

            TouchMainRoad=[]

            for plot in PlotLayerDict.values():

                plot_polygon_points=Polygon(np.array([pp[0:2] for pp in plot[2].get_points()]))

                if mainroad_polygon_points.contains(plot_polygon_points)==True or mainroad_polygon_points.touches(plot_polygon_points)==True or round(mainroad_polygon_points.distance(plot_polygon_points),1)==0.0:

                    TouchMainRoad.append(True)

                else:

                    TouchMainRoad.append(False)

            for wallcompound in WallCompoundLayerDict.values():

                wallcompound_polygon_points = Polygon(np.array([wcp[0:2] for wcp in wallcompound[2].get_points()]))

                if mainroad_polygon_points.contains(wallcompound_polygon_points) == True or mainroad_polygon_points.touches(wallcompound_polygon_points) == True or round(mainroad_polygon_points.distance(wallcompound_polygon_points),1) == 0.0:

                    TouchMainRoad.append(True)

                else:

                    TouchMainRoad.append(False)

            for roadwidening in RoadWideningsLayerDict.values():

                wallcompound_polygon_points = Polygon(np.array([rwp[0:2] for rwp in roadwidening[2].get_points()]))

                if mainroad_polygon_points.contains(wallcompound_polygon_points) == True or mainroad_polygon_points.touches(wallcompound_polygon_points) == True or round(mainroad_polygon_points.distance(wallcompound_polygon_points),1) == 0.0:

                    TouchMainRoad.append(True)

                else:

                    TouchMainRoad.append(False)


            for nalawidening in NalaWideningsLayerDict.values():

                nalawidening_polygon_points = Polygon(np.array([nwp[0:2] for nwp in nalawidening[2].get_points()]))

                if mainroad_polygon_points.contains(nalawidening_polygon_points) == True or mainroad_polygon_points.touches(nalawidening_polygon_points) == True or round(mainroad_polygon_points.distance(nalawidening_polygon_points),1) == 0.0:

                    TouchMainRoad.append(True)

                else:

                    TouchMainRoad.append(False)

            if TouchMainRoad!=[] and len(TouchMainRoad)>0:

                if any(TouchMainRoad)==False:

                    ErrorMsg=f'Warning: {mainroad[0]} ({mainroad[1]}) Does Not Touch with Plot,WallCompound,RoadWidening,NalaWidening Layers.'

                    ErrorMainRoad[mainroad[0]]=ErrorMsg

        return ErrorMainRoad
    def NalaWidening_Layer(self,NalaWideningData):

        NalaWideningDict=dict()

        ErrorNalaWideningDict=dict()

        unique_polygons={}

        for NalaWidening_entity in NalaWideningData:

            if NalaWidening_entity.dxftype()=='LWPOLYLINE':

                NalaWidening_PolygonID = NalaWidening_entity.dxf.handle

                if NalaWidening_entity.closed:

                    vertices = tuple(NalaWidening_entity.get_points())

                    if vertices in unique_polygons:

                        ErrorNalaWideningDict[NalaWidening_PolygonID] = str(
                            f"NalaWidening Layer Found Duplicate Polygon Of {NalaWidening_PolygonID}.")

                    else:

                        unique_polygons[vertices] = NalaWidening_entity

                    NalaWidening_polygon_points=Polygon(np.array([nwp[0:2] for nwp in NalaWidening_entity.get_points()]))

                    NalaWideningPolygonContainLabel=[]

                    for NalaWidening_entity1 in NalaWideningData:

                        NalaWidening_text_properties=NalaWidening_entity1.dxfattribs()

                        if NalaWidening_entity1.dxftype()=='TEXT' or NalaWidening_entity1.dxftype()=='MTEXT':

                            NalaWidening_labelID=NalaWidening_entity1.dxf.handle

                            NalaWidening_label= NalaWidening_text_properties.get('text') if NalaWidening_entity1.dxftype()=='TEXT' else NalaWidening_entity1.plain_text()

                            NalaWidening_label_pts=NalaWidening_text_properties.get('insert')

                            NalaWidening_label_point=Point(np.array([NalaWidening_label_pts[0],NalaWidening_label_pts[1]]))

                            if NalaWidening_polygon_points.contains(NalaWidening_label_point)==True or NalaWidening_polygon_points.touches(NalaWidening_label_point)==True or round(NalaWidening_polygon_points.distance(NalaWidening_label_point),1)==0.0:

                                NalaWideningPolygonContainLabel.append([NalaWidening_labelID,NalaWidening_label,NalaWidening_entity])

                    if NalaWideningPolygonContainLabel!=[] and len(NalaWideningPolygonContainLabel)<=1:

                        for NalaWidening in NalaWideningPolygonContainLabel:

                            NalaWideningDict[NalaWidening_PolygonID]=NalaWidening

                    elif(len(NalaWideningPolygonContainLabel)>1):

                        ErrorMsg = f'Warning:NalaWidening Layer Polygon({NalaWidening_PolygonID}) Found More Than One Label.'

                        ErrorNalaWideningDict[NalaWidening_PolygonID] = ErrorMsg

                    else:

                        ErrorMsg=f'Warning:NalaWidening Layer Polygon({NalaWidening_PolygonID}) Does Not Have Label.'

                        ErrorNalaWideningDict[NalaWidening_PolygonID]=ErrorMsg
                else:

                    ErrorMsg = f'Warning:RoadWidening Layer Polygon({NalaWidening_PolygonID}) Does Not Closed Properly.'

                    ErrorNalaWideningDict[NalaWidening_PolygonID] = ErrorMsg

        return [ErrorNalaWideningDict,NalaWideningDict]

    def InternalRoadNotIntersect(self,InternalRoadLayerDict,MainRoadLayerDict,RoadWideningLayerDict,ExistingInternalRoadLayerDict,OrganizedOpenSpaceLayerDict,SubplotsLayerDict,ParkingLayerDict,AccessoryUseLayerDict):

        InternalRoadErrorDict=dict()

        for internalRoad in InternalRoadLayerDict.values():

            internalRoad_polygon_points=Polygon(np.array([irp[0:2] for irp in internalRoad[2].get_points()]))

            internalRoadOverlap=[]

            for mainroad in MainRoadLayerDict.values():

                mainRoad_polygon_points=np.array([mrp[0:2] for mrp in mainroad[2].get_points()])

                internalRoadContainMainRoad=[]

                for mainroadpts in mainRoad_polygon_points:

                    mainroad_point=Point(mainroadpts)

                    if internalRoad_polygon_points.contains(mainroad_point)==True:

                        internalRoadContainMainRoad.append(True)

                    else:

                        internalRoadContainMainRoad.append(False)

                if internalRoadContainMainRoad!=[] and len(internalRoadContainMainRoad)>0:

                    if any(internalRoadContainMainRoad)==True and internalRoadContainMainRoad.count(True)>2:

                        ErrorMsg=f'Warning:InternalRoad Layer Overlaping on {mainroad[1]}({mainroad[0]}).'

                        internalRoadOverlap.append(ErrorMsg)

            for roadwidening in RoadWideningLayerDict.values():

                roadwidening_polygon_points = np.array([rwp[0:2] for rwp in roadwidening[2].get_points()])

                internalroadContainRoadwidening=[]

                for roadwideningpts in roadwidening_polygon_points:

                    roadwidening_point=Point(roadwideningpts)

                    if internalRoad_polygon_points.contains(roadwidening_point)==True:

                        internalroadContainRoadwidening.append(True)

                    else:

                        internalroadContainRoadwidening.append(False)

                if internalroadContainRoadwidening!=[] and len(internalroadContainRoadwidening)>0:

                    if any(internalroadContainRoadwidening) == True and internalroadContainRoadwidening.count(True)>2:

                        ErrorMsg = f'Warning:InternalRoad Layer Overlaping on{roadwidening[1]}({roadwidening[0]}).'

                        internalRoadOverlap.append(ErrorMsg)

            for ExistingInternalRoad in ExistingInternalRoadLayerDict.values():

                existinginternalroad_polygon_points = np.array([eirp[0:2] for eirp in ExistingInternalRoad[2].get_points()])

                internalroadContainExistingInternalRoad=[]

                for existinginternalRoadpts in existinginternalroad_polygon_points:

                    existinginternalRoadPoint=Point(existinginternalRoadpts)

                    if internalRoad_polygon_points.contains(existinginternalRoadPoint)==True:

                        internalroadContainExistingInternalRoad.append(True)

                    else:

                        internalroadContainExistingInternalRoad.append(False)

                if internalroadContainExistingInternalRoad!=[] and len(internalroadContainExistingInternalRoad)>0:

                    if any(internalroadContainExistingInternalRoad) == True and internalroadContainExistingInternalRoad.count(True)>2:

                        ErrorMsg = f'Warning:InternalRoad Layer Overlaping on {ExistingInternalRoad[1]}({ExistingInternalRoad[0]}).'

                        internalRoadOverlap.append(ErrorMsg)

            for OrganizedOpenSpace in OrganizedOpenSpaceLayerDict.values():

                OrganizedOpenSpace_polygon_points =np.array([orgp[0:2] for orgp in OrganizedOpenSpace[2].get_points()])

                internaroadContainOrganizedOpenSpace=[]

                for Organizedopenspacepts in OrganizedOpenSpace_polygon_points:

                    Organizedopenspace_point=Point(Organizedopenspacepts)

                    if internalRoad_polygon_points.contains(Organizedopenspace_point)==True:

                        internaroadContainOrganizedOpenSpace.append(True)

                    else:

                        internaroadContainOrganizedOpenSpace.append(False)

                if internaroadContainOrganizedOpenSpace!=[] and len(internaroadContainOrganizedOpenSpace)>0:

                    if any(internaroadContainOrganizedOpenSpace) == True and internaroadContainOrganizedOpenSpace.count(True)>2:

                        ErrorMsg = f'Warning:InternalRoad Layer Overlaping on {OrganizedOpenSpace[1]}({OrganizedOpenSpace[0]}).'

                        internalRoadOverlap.append(ErrorMsg)

            for subplots in SubplotsLayerDict.values():

                subplots_polygon_points =np.array([subp[0:2] for subp in subplots[2].get_points()])

                internalroadContainsubplots=[]

                for subplotpts in subplots_polygon_points:

                    subplot_point=Point(subplotpts)

                    if internalRoad_polygon_points.contains(subplot_point)==True:

                        internalroadContainsubplots.append(True)

                    else:

                        internalroadContainsubplots.append(False)

                if internalroadContainsubplots!=[] and len(internalroadContainsubplots)>0:

                    if any(internalroadContainsubplots) == True and (internalroadContainsubplots.count(True)>2):

                        ErrorMsg = f'Warning:InternalRoad Layer Overlaping on Subplot Layer {subplots[1]} ({subplots[0]}).'

                        internalRoadOverlap.append(ErrorMsg)

            for parking in ParkingLayerDict.values():

                parking_polygon_points = np.array([parkp[0:2] for parkp in parking[2].get_points()])

                internalroadContainParking=[]

                for parkingpts in parking_polygon_points:

                    parking_point=Point(parkingpts)

                    if internalRoad_polygon_points.contains(parking_point)==True:

                        internalroadContainParking.append(True)

                    else:

                        internalroadContainParking.append(False)

                if internalroadContainParking!=[] and len(internalroadContainParking)>0:

                    if any(internalroadContainParking) == True and internalroadContainParking.count(True)>2:

                        ErrorMsg = f'Warning:InternalRoad Layer Overlaping on {parking[1]}({parking[0]}).'

                        internalRoadOverlap.append(ErrorMsg)

            for accessory in AccessoryUseLayerDict.values():

                accessory_polygon_points = np.array([ap[0:2] for ap in accessory[2].get_points()])

                internalroadContainaccessory=[]

                for accessorypts in accessory_polygon_points:

                    accessory_point=Point(accessorypts)

                    if internalRoad_polygon_points.contains(accessory_point) == True:

                        internalroadContainaccessory.append(True)

                    else:

                        internalroadContainaccessory.append(False)

                if internalroadContainaccessory!=[] and len(internalroadContainaccessory)>0:

                    if any(internalroadContainaccessory) == True and internalroadContainaccessory.count(True)>2:

                        ErrorMsg = f'Warning:InternalRoad Layer Overlaping on {accessory[1]}({accessory[0]}).'

                        internalRoadOverlap.append(ErrorMsg)

            if internalRoadOverlap!=[] and len(internalRoadOverlap)>0:

                InternalRoadErrorDict[internalRoad[0]]=internalRoadOverlap

        return InternalRoadErrorDict
    def RoadWidening_Layer(self,RoadWideningData):

        RoadWideningDict=dict()

        ErrorRoadWideningDict=dict()

        unique_polygons={}

        for RoadWidening_entity in RoadWideningData:

            if RoadWidening_entity.dxftype()=='LWPOLYLINE':

                RoadWidening_PolygonID = RoadWidening_entity.dxf.handle

                if RoadWidening_entity.closed:

                    vertices = tuple(RoadWidening_entity.get_points())

                    if vertices in unique_polygons:

                        ErrorRoadWideningDict[RoadWidening_PolygonID] = str(
                            f"RoadWidening Layer Found Duplicate Polygon Of {RoadWidening_PolygonID}.")

                    else:

                        unique_polygons[vertices] = RoadWidening_entity

                    RoadWidening_polygon_points=Polygon(np.array([rwp[0:2] for rwp in RoadWidening_entity.get_points()]))

                    RoadWideningPolygonContainLabel=[]

                    for RoadWidening_entity1 in RoadWideningData:

                        RoadWidening_text_properties=RoadWidening_entity1.dxfattribs()

                        if RoadWidening_entity1.dxftype()=='TEXT' or RoadWidening_entity1.dxftype()=='MTEXT':

                            RoadWidening_labelID=RoadWidening_entity1.dxf.handle

                            RoadWidening_label= RoadWidening_text_properties.get('text') if RoadWidening_entity1.dxftype()=='TEXT' else RoadWidening_entity1.plain_text()

                            RoadWidening_label_pts=RoadWidening_text_properties.get('insert')

                            RoadWidening_label_point=Point(np.array([RoadWidening_label_pts[0],RoadWidening_label_pts[1]]))

                            if RoadWidening_polygon_points.contains(RoadWidening_label_point)==True or RoadWidening_polygon_points.touches(RoadWidening_label_point)==True or round(RoadWidening_polygon_points.distance(RoadWidening_label_point),1)==0.0:

                                RoadWideningPolygonContainLabel.append([RoadWidening_labelID,RoadWidening_label,RoadWidening_entity])

                    if RoadWideningPolygonContainLabel!=[] and len(RoadWideningPolygonContainLabel)<=1:

                        for RoadWidening in RoadWideningPolygonContainLabel:

                            RoadWideningDict[RoadWidening_PolygonID]=RoadWidening

                    elif(len(RoadWideningPolygonContainLabel)>1):

                        ErrorMsg = f'Warning:RoadWidening Layer Polygon({RoadWidening_PolygonID}) Found More Than One Label.'

                        ErrorRoadWideningDict[RoadWidening_PolygonID] = ErrorMsg

                    else:

                        ErrorMsg=f'Warning:RoadWidening Layer Polygon({RoadWidening_PolygonID}) Does Not Have Label.'

                        ErrorRoadWideningDict[RoadWidening_PolygonID]=ErrorMsg
                else:

                    ErrorMsg = f'Warning:RoadWidening Layer Polygon({RoadWidening_PolygonID}) Does Not Closed Properly.'

                    ErrorRoadWideningDict[RoadWidening_PolygonID] = ErrorMsg

        return [ErrorRoadWideningDict,RoadWideningDict]
    def Parking_Layer(self,ParkingData):

        ParkingDict=dict()

        ErrorParkingDict=dict()

        unique_polygons={}

        for Parking_entity in ParkingData:

            if Parking_entity.dxftype()=='LWPOLYLINE':

                Parking_PolygonID = Parking_entity.dxf.handle

                if Parking_entity.closed:

                    vertices = tuple(Parking_entity.get_points())

                    if vertices in unique_polygons:

                        ErrorParkingDict[Parking_PolygonID] = str(
                            f"Parking Layer Found Duplicate Polygon Of {Parking_PolygonID}.")

                    else:

                        unique_polygons[vertices] = Parking_entity

                    Parking_polygon_points=Polygon(np.array([pp[0:2] for pp in Parking_entity.get_points()]))

                    ParkingPolygonContainLabel=[]

                    for Parking_entity1 in ParkingData:

                        Parking_text_properties=Parking_entity1.dxfattribs()

                        if Parking_entity1.dxftype()=='TEXT' or Parking_entity1.dxftype()=='MTEXT':

                            Parking_labelID=Parking_entity1.dxf.handle

                            Parking_label= Parking_text_properties.get('text') if Parking_entity1.dxftype()=='TEXT' else Parking_entity1.plain_text()

                            Parking_label_pts=Parking_text_properties.get('insert')

                            Parking_label_point=Point(np.array([Parking_label_pts[0],Parking_label_pts[1]]))

                            if Parking_polygon_points.contains(Parking_label_point)==True or Parking_polygon_points.touches(Parking_label_point)==True or round(Parking_polygon_points.distance(Parking_label_point),1)==0.0:

                                ParkingPolygonContainLabel.append([Parking_labelID,Parking_label,Parking_entity])

                    if ParkingPolygonContainLabel!=[] and len(ParkingPolygonContainLabel)<=1:

                        for Parking in ParkingPolygonContainLabel:

                            ParkingDict[Parking_PolygonID]=Parking

                    elif(len(ParkingPolygonContainLabel)>1):

                        ErrorMsg = f'Warning:Parking Layer Polygon({Parking_PolygonID}) Found More Than One Label.'

                        ErrorParkingDict[Parking_PolygonID] = ErrorMsg

                    else:

                        ErrorMsg=f'Warning:Parking Layer Polygon({Parking_PolygonID}) Does Not Have Label.'

                        ErrorParkingDict[Parking_PolygonID]=ErrorMsg
                else:

                    ErrorMsg = f'Warning:Parking Layer Polygon({Parking_PolygonID}) Does Not Closed Properly.'

                    ErrorParkingDict[Parking_PolygonID] = ErrorMsg

        return [ErrorParkingDict,ParkingDict]
    def OrganizedOpenSpace_Layer(self,OrganizedOpenSpaceData):

        OrganizedOpenSpaceDict=dict()

        ErrorOrganizedOpenSpaceDict=dict()

        unique_polygons={}

        for OrganizedOpenSpace_entity in OrganizedOpenSpaceData:

            if OrganizedOpenSpace_entity.dxftype()=='LWPOLYLINE':

                OrganizedOpenSpace_PolygonID = OrganizedOpenSpace_entity.dxf.handle

                if OrganizedOpenSpace_entity.closed:

                    vertices = tuple(OrganizedOpenSpace_entity.get_points())

                    if vertices in unique_polygons:

                        ErrorOrganizedOpenSpaceDict[OrganizedOpenSpace_PolygonID] = str(
                            f"OrganizedOpenSpace Layer Found Duplicate Polygon Of {OrganizedOpenSpace_PolygonID}.")

                    else:

                        unique_polygons[vertices] = OrganizedOpenSpace_entity

                    OrganizedOpenSpace_polygon_points=Polygon(np.array([orgp[0:2] for orgp in OrganizedOpenSpace_entity.get_points()]))

                    OrganizedOpenSpacePolygonContainLabel=[]

                    for OrganizedOpenSpace_entity1 in OrganizedOpenSpaceData:

                        OrganizedOpenSpace_text_properties=OrganizedOpenSpace_entity1.dxfattribs()

                        if OrganizedOpenSpace_entity1.dxftype()=='TEXT' or OrganizedOpenSpace_entity1.dxftype()=='MTEXT':

                            OrganizedOpenSpace_labelID=OrganizedOpenSpace_entity1.dxf.handle

                            OrganizedOpenSpace_label= OrganizedOpenSpace_text_properties.get('text') if OrganizedOpenSpace_entity1.dxftype()=='TEXT' else OrganizedOpenSpace_entity1.plain_text()

                            OrganizedOpenSpace_label_pts=OrganizedOpenSpace_text_properties.get('insert')

                            OrganizedOpenSpace_label_point=Point(np.array([OrganizedOpenSpace_label_pts[0],OrganizedOpenSpace_label_pts[1]]))

                            if OrganizedOpenSpace_polygon_points.contains(OrganizedOpenSpace_label_point)==True or OrganizedOpenSpace_polygon_points.touches(OrganizedOpenSpace_label_point)==True or round(OrganizedOpenSpace_polygon_points.distance(OrganizedOpenSpace_label_point),1)==0.0:

                                OrganizedOpenSpacePolygonContainLabel.append([OrganizedOpenSpace_labelID,OrganizedOpenSpace_label,OrganizedOpenSpace_entity])

                    if OrganizedOpenSpacePolygonContainLabel!=[] and len(OrganizedOpenSpacePolygonContainLabel)<=1:

                        for OrganizedOpenSpace in OrganizedOpenSpacePolygonContainLabel:

                            OrganizedOpenSpaceDict[OrganizedOpenSpace_PolygonID]=OrganizedOpenSpace


                    elif(len(OrganizedOpenSpacePolygonContainLabel)>1):

                        ErrorMsg = f'Warning:OrganizedOpenSpace Layer Polygon({OrganizedOpenSpace_PolygonID}) Found More Than One Label.'

                        ErrorOrganizedOpenSpaceDict[OrganizedOpenSpace_PolygonID] = ErrorMsg

                    else:

                        ErrorMsg=f'Warning:OrganizedOpenSpace Layer Polygon({OrganizedOpenSpace_PolygonID}) Does Not Have Label.'

                        ErrorOrganizedOpenSpaceDict[OrganizedOpenSpace_PolygonID]=ErrorMsg
                else:

                    ErrorMsg = f'Warning:OrganizedOpenSpace Layer Polygon({OrganizedOpenSpace_PolygonID}) Does Not Closed Properly.'

                    ErrorOrganizedOpenSpaceDict[OrganizedOpenSpace_PolygonID] = ErrorMsg
        #print([ErrorOrganizedOpenSpaceDict,OrganizedOpenSpaceDict])
        return [ErrorOrganizedOpenSpaceDict,OrganizedOpenSpaceDict]

    def RoadstouchORContainsPlot(self,plotDict,InternalRoadDict,MainRoadDict,ExistingInternalRoadDict):

        plotErrorDict=dict()

        for plot in plotDict.values():

            plot_polygon_points=Polygon(np.array([pp[0:2] for pp in plot[2].get_points()]))

            plottouchRoads=[]

            for InternalRoads in InternalRoadDict.values():

                internalroads_polygon_points = Polygon(np.array([irp[0:2] for irp in InternalRoads[2].get_points()]))

                if plot_polygon_points.intersects(internalroads_polygon_points)==True :

                    ErrorMsg=f'Warning:{InternalRoads[1]} ({InternalRoads[0]}) Overlapping on Plot Layer.'

                    plottouchRoads.append(ErrorMsg)

            for ExistingInternalRoad in ExistingInternalRoadDict.values():

                ExistingInternalRoad_polygon_points = Polygon(np.array([erp[0:2] for erp in ExistingInternalRoad[2].get_points()]))

                if plot_polygon_points.intersects(ExistingInternalRoad_polygon_points)==True:

                    ErrorMsg = f'Warning:{ExistingInternalRoad[1]} ({ExistingInternalRoad[0]}) Overlapping on Plot Layer.'

                    plottouchRoads.append(ErrorMsg)

            for MainRoad in MainRoadDict.values():

                MainRoad_polygon_points = Polygon(np.array([mrp[0:2] for mrp in MainRoad[2].get_points()]))

                if plot_polygon_points.intersects(MainRoad_polygon_points) == True:

                    ErrorMsg = f'Warning:{MainRoad[1]} ({MainRoad[0]}) Overlapping on Plot Layer.'

                    plottouchRoads.append(ErrorMsg)

            if plottouchRoads!=[] and len(plottouchRoads)>0:

                if any(plottouchRoads)==False:

                    ErrorMsg=f'Warning:{plot[1]} ({plot[0]}) Does Not Touch Any Roads.'

                    plotErrorDict[plot[0]]=ErrorMsg

        return plotErrorDict

    def SubplotsToucheRoads(self,SubplotsDict,InternalRoadDict,MainRoadDict,ExistingInternalRoadDict):

        SubplotsErrorDict=dict()

        for subplot in SubplotsDict.values():

            subplot_polygon_points=Polygon(np.array([subp[0:2] for subp in subplot[2].get_points()]))

            SubplottouchRoads=[]

            for InternalRoads in InternalRoadDict.values():

                internalroads_polygon_points = Polygon(np.array([irp[0:2] for irp in InternalRoads[2].get_points()]))

                if subplot_polygon_points.touches(internalroads_polygon_points)==True or round(subplot_polygon_points.distance(internalroads_polygon_points),1)==0.0:

                    SubplottouchRoads.append(True)

                else:

                    SubplottouchRoads.append(False)

            for ExistingInternalRoad in ExistingInternalRoadDict.values():

                ExistingInternalRoad_polygon_points = Polygon(np.array([erp[0:2] for erp in ExistingInternalRoad[2].get_points()]))

                if subplot_polygon_points.touches(ExistingInternalRoad_polygon_points) == True or round(subplot_polygon_points.distance(ExistingInternalRoad_polygon_points), 1) == 0.0:

                    SubplottouchRoads.append(True)

                else:

                    SubplottouchRoads.append(False)

            for MainRoad in MainRoadDict.values():

                MainRoad_polygon_points = Polygon(np.array([mrp[0:2] for mrp in MainRoad[2].get_points()]))

                if subplot_polygon_points.touches(MainRoad_polygon_points) == True or round(subplot_polygon_points.distance(MainRoad_polygon_points), 1) == 0.0:

                    SubplottouchRoads.append(True)

                else:

                    SubplottouchRoads.append(False)

            if SubplottouchRoads!=[] and len(SubplottouchRoads)>0:

                if any(SubplottouchRoads)==False:

                    ErrorMsg=f'Warning:{subplot[1]} ({subplot[0]}) Does Not Touch Any Roads.'

                    SubplotsErrorDict[subplot[0]]=ErrorMsg

        return SubplotsErrorDict
    def ExistingInternalRoad_Layer(self,ExistingInternalRoadData):

        ExistingInternalRoadDict=dict()

        ErrorExistingInternalRoadDict=dict()

        unique_polygons={}

        for ExistingInternalRoad_entity in ExistingInternalRoadData:

            if ExistingInternalRoad_entity.dxftype()=='LWPOLYLINE':

                ExistingInternalRoad_PolygonID = ExistingInternalRoad_entity.dxf.handle

                if ExistingInternalRoad_entity.closed:

                    vertices = tuple(ExistingInternalRoad_entity.get_points())

                    if vertices in unique_polygons:

                        ErrorExistingInternalRoadDict[ExistingInternalRoad_PolygonID] = str(
                            f"ExistingInternalRoad Layer Found Duplicate Polygon Of {ExistingInternalRoad_PolygonID}.")

                    else:

                        unique_polygons[vertices] = ExistingInternalRoad_entity

                    ExistingInternalRoad_polygon_points=Polygon(np.array([Mp[0:2] for Mp in ExistingInternalRoad_entity.get_points()]))

                    ExistingInternalRoadPolygonContainLabel=[]

                    for ExistingInternalRoad_entity1 in ExistingInternalRoadData:

                        ExistingInternalRoad_text_properties=ExistingInternalRoad_entity1.dxfattribs()

                        if ExistingInternalRoad_entity1.dxftype()=='TEXT' or ExistingInternalRoad_entity1.dxftype()=='MTEXT':

                            ExistingInternalRoad_labelID=ExistingInternalRoad_entity1.dxf.handle

                            ExistingInternalRoad_label= ExistingInternalRoad_text_properties.get('text') if ExistingInternalRoad_entity1.dxftype()=='TEXT' else ExistingInternalRoad_entity1.plain_text()

                            ExistingInternalRoad_label_pts=ExistingInternalRoad_text_properties.get('insert')

                            ExistingInternalRoad_label_point=Point(np.array([ExistingInternalRoad_label_pts[0],ExistingInternalRoad_label_pts[1]]))

                            if ExistingInternalRoad_polygon_points.contains(ExistingInternalRoad_label_point)==True or ExistingInternalRoad_polygon_points.touches(ExistingInternalRoad_label_point)==True or round(ExistingInternalRoad_polygon_points.distance(ExistingInternalRoad_label_point),1)==0.0:

                                ExistingInternalRoadPolygonContainLabel.append([ExistingInternalRoad_labelID,ExistingInternalRoad_label,ExistingInternalRoad_entity])

                    if ExistingInternalRoadPolygonContainLabel!=[] and len(ExistingInternalRoadPolygonContainLabel)<=1:

                        for ExistingInternalRoad in ExistingInternalRoadPolygonContainLabel:

                            ExistingInternalRoadDict[ExistingInternalRoad_PolygonID]=ExistingInternalRoad


                    elif(len(ExistingInternalRoadPolygonContainLabel)>1):

                        ErrorMsg = f'Warning:ExistingInternalRoad Layer Polygon({ExistingInternalRoad_PolygonID}) Found More Than One Label.'

                        ErrorExistingInternalRoadDict[ExistingInternalRoad_PolygonID] = ErrorMsg

                    else:

                        ErrorMsg=f'Warning:ExistingInternalRoad Layer Polygon({ExistingInternalRoad_PolygonID}) Does Not Have Label.'

                        ErrorExistingInternalRoadDict[ExistingInternalRoad_PolygonID]=ErrorMsg
                else:

                    ErrorMsg = f'Warning:ExistingInternalRoad Layer Polygon({ExistingInternalRoad_PolygonID}) Does Not Closed Properly.'

                    ErrorExistingInternalRoadDict[ExistingInternalRoad_PolygonID] = ErrorMsg

        return [ErrorExistingInternalRoadDict,ExistingInternalRoadDict]
    def Subplots_Layer(self,SubplotsData):

        SubplotsDict=dict()

        ErrorSubplotsDict=dict()

        unique_polygons={}

        for Subplots_entity in SubplotsData:

            if Subplots_entity.dxftype()=='LWPOLYLINE':

                Subplots_PolygonID = Subplots_entity.dxf.handle

                if Subplots_entity.closed:

                    vertices = tuple(Subplots_entity.get_points())

                    if vertices in unique_polygons:

                        ErrorSubplotsDict[Subplots_PolygonID] = str(
                            f"SubPlot Layer Found Duplicate Polygon Of {Subplots_PolygonID}.")

                    else:

                        unique_polygons[vertices] = Subplots_entity

                    Subplots_polygon_points=Polygon(np.array([subp[0:2] for subp in Subplots_entity.get_points()]))

                    SubplotsPolygonContainLabel=[]

                    for Subplots_entity1 in SubplotsData:

                        Subplots_text_properties=Subplots_entity1.dxfattribs()

                        if Subplots_entity1.dxftype()=='TEXT' or Subplots_entity1.dxftype()=='MTEXT':

                            Subplots_labelID=Subplots_entity1.dxf.handle

                            Subplots_label= Subplots_text_properties.get('text') if Subplots_entity1.dxftype()=='TEXT' else Subplots_entity1.plain_text()

                            Subplots_label_pts=Subplots_text_properties.get('insert')

                            Subplots_label_point=Point(np.array([Subplots_label_pts[0],Subplots_label_pts[1]]))

                            if Subplots_polygon_points.contains(Subplots_label_point)==True or Subplots_polygon_points.touches(Subplots_label_point)==True or round(Subplots_polygon_points.distance(Subplots_label_point),1)==0.0:

                                SubplotsPolygonContainLabel.append([Subplots_labelID,Subplots_label,Subplots_entity])

                    if SubplotsPolygonContainLabel!=[] and len(SubplotsPolygonContainLabel)<=1:

                        for Subplots in SubplotsPolygonContainLabel:

                            SubplotsDict[Subplots_PolygonID]=Subplots


                    elif(len(SubplotsPolygonContainLabel)>1):

                        ErrorMsg = f'Warning:Subplots Layer Polygon({Subplots_PolygonID}) Found More Than One Label.'

                        ErrorSubplotsDict[Subplots_PolygonID] = ErrorMsg

                    else:

                        ErrorMsg=f'Warning:Subplots Layer Polygon({Subplots_PolygonID}) Does Not Have Label.'

                        ErrorSubplotsDict[Subplots_PolygonID]=ErrorMsg
                else:

                    ErrorMsg = f'Warning:Subplots Layer Polygon({Subplots_PolygonID}) Does Not Closed Properly.'

                    ErrorSubplotsDict[Subplots_PolygonID] = ErrorMsg

        return [ErrorSubplotsDict,SubplotsDict]

    def ValidForAccessoryUse(self,AccessoryUseDict,WallCompoundDict,PlotDict):

        ErrorAccessorydict=dict()

        for accessory_data in AccessoryUseDict.values():

            accessoryuse_polygon = Polygon(np.array([ap[0:2] for ap in accessory_data[2].get_points()]))

            # When there is a gate, you need to have a compound wall.

            if any(words in accessory_data[1].lower() for words in ['gate','ent'])==True:

                EntGateTouchWallCompound = []

                for WallCompound in WallCompoundDict.values():

                    wallcompound_polygon = Polygon(np.array([wcp[0:2] for wcp in WallCompound[2].get_points()]))

                    if accessoryuse_polygon.touches(wallcompound_polygon) == True or round(accessoryuse_polygon.distance(wallcompound_polygon), 1) == 0.0:

                        EntGateTouchWallCompound.append(True)

                    else:

                        EntGateTouchWallCompound.append(False)

                if any(EntGateTouchWallCompound)==False:

                    ErrorMsg = f'Warning:{accessory_data[1]}({accessory_data[0]}) Not Have in WallCompound Layer.'

                    ErrorAccessorydict[accessory_data[0]] = ErrorMsg

            elif(any(words in accessory_data[1].lower() for words in ['rain water harvesting'])):

                harwestingINplot=[]

                for plot_data in PlotDict.values():

                    plot_polygon = Polygon(np.array([pp[0:2] for pp in plot_data[2].get_points()]))

                    if plot_polygon.contains(accessoryuse_polygon)==True or plot_polygon.touches(accessoryuse_polygon)==True or round(plot_polygon.distance(accessoryuse_polygon),1)==0.0:

                        harwestingINplot.append(True)

                    else:

                        harwestingINplot.append(False)

                if any(harwestingINplot)==False:

                    ErrorMsg=f'Warning:{accessory_data[1]}({accessory_data[0]}) Not Have in Plot Layer.'

                    ErrorAccessorydict[accessory_data[0]]=ErrorMsg

            elif (any(words in accessory_data[1].lower() for words in ['percolation well','percolation pit'])):

                percolationINplot = []

                for plot_data in PlotDict.values():

                    plot_polygon = Polygon(np.array([pp[0:2] for pp in plot_data[2].get_points()]))

                    if plot_polygon.contains(accessoryuse_polygon) == True or plot_polygon.touches(accessoryuse_polygon) == True or round(plot_polygon.distance(accessoryuse_polygon),1) == 0.0:

                        percolationINplot.append(True)

                    else:

                        percolationINplot.append(False)

                if any(harwestingINplot) == False:

                    ErrorMsg = f'Warning:{accessory_data[1]}({accessory_data[0]}) Not Have in Plot Layer.'

                    ErrorAccessorydict[accessory_data[0]] = ErrorMsg


            elif (any(words in accessory_data[1].lower() for words in ['sewage treatment plan','stp'])):

                STPINplot = []

                for plot_data in PlotDict.values():

                    plot_polygon = Polygon(np.array([pp[0:2] for pp in plot_data[2].get_points()]))

                    if plot_polygon.contains(accessoryuse_polygon) == True or plot_polygon.touches(accessoryuse_polygon) == True or round(plot_polygon.distance(accessoryuse_polygon),1) == 0.0:

                        STPINplot.append(True)

                    else:

                        STPINplot.append(False)

                if any(STPINplot) == False:

                    ErrorMsg = f'Warning:{accessory_data[1]}({accessory_data[0]}) Not Have in Plot Layer.'

                    ErrorAccessorydict[accessory_data[0]] = ErrorMsg


            elif (any(words in accessory_data[1].lower() for words in ['utility'])):

                UtilityINplot = []

                for plot_data in PlotDict.values():

                    plot_polygon = Polygon(np.array([pp[0:2] for pp in plot_data[2].get_points()]))

                    if plot_polygon.contains(accessoryuse_polygon) == True or plot_polygon.touches(accessoryuse_polygon) == True or round(plot_polygon.distance(accessoryuse_polygon),1) == 0.0:

                        UtilityINplot.append(True)

                    else:

                        UtilityINplot.append(False)

                if any(UtilityINplot) == False:

                    ErrorMsg = f'Warning:{accessory_data[1]}({accessory_data[0]}) Not Have in Plot Layer.'

                    ErrorAccessorydict[accessory_data[0]] = ErrorMsg

        wallcompoundENTGATE=[]

        for WallCompound_data in WallCompoundDict.values():

           wall_compound_polygon=Polygon(np.array([wcp[0:2] for wcp in WallCompound_data[2].get_points()]))

           for accessoryuse in AccessoryUseDict.values():

               if any(words in accessoryuse[1].lower() for words in ['ent','gate'])==True:

                    accessoryuse_polygon = Polygon(np.array([ap[0:2] for ap in accessoryuse[2].get_points()]))

                    if wall_compound_polygon.touches(accessoryuse_polygon)==True or round(wall_compound_polygon.distance(accessoryuse_polygon),1)==0.0:

                        wallcompoundENTGATE.append(True)

                    else:

                        wallcompoundENTGATE.append(False)

        if wallcompoundENTGATE!=[] and len(wallcompoundENTGATE)>0:

            if any(wallcompoundENTGATE)==False:

                ErrorMsg = f'Warning:WallCompound Layer Not Have in ENT.GATE Layer.'

                ErrorAccessorydict['ENTGATE'] = ErrorMsg


        return ErrorAccessorydict

    def WaterBodies_Layer(self,WaterBodiesData):

        WaterBodiesDict=dict()

        ErrorWaterBodiesDict=dict()

        unique_polygons={}

        for WaterBodies_entity in WaterBodiesData:

            if WaterBodies_entity.dxftype()=='LWPOLYLINE':

                WaterBodies_PolygonID = WaterBodies_entity.dxf.handle

                if WaterBodies_entity.closed:

                    vertices = tuple(WaterBodies_entity.get_points())

                    if vertices in unique_polygons:

                        ErrorWaterBodiesDict[WaterBodies_PolygonID] = str(
                            f"WaterBodies Layer Found Duplicate Polygon Of {WaterBodies_PolygonID}.")

                    else:

                        unique_polygons[vertices] = WaterBodies_entity

                    WaterBodies_polygon_points=Polygon(np.array([wbp[0:2] for wbp in WaterBodies_entity.get_points()]))

                    WaterBodiesPolygonContainLabel=[]

                    for WaterBodies_entity1 in WaterBodiesData:

                        WaterBodies_text_properties=WaterBodies_entity1.dxfattribs()

                        if WaterBodies_entity1.dxftype()=='TEXT' or WaterBodies_entity1.dxftype()=='MTEXT':

                            WaterBodies_labelID=WaterBodies_entity1.dxf.handle

                            WaterBodies_label= WaterBodies_text_properties.get('text') if WaterBodies_entity1.dxftype()=='TEXT' else WaterBodies_entity1.plain_text()

                            WaterBodies_label_pts=WaterBodies_text_properties.get('insert')

                            WaterBodies_label_point=Point(np.array([WaterBodies_label_pts[0],WaterBodies_label_pts[1]]))

                            if WaterBodies_polygon_points.contains(WaterBodies_label_point)==True or WaterBodies_polygon_points.touches(WaterBodies_label_point)==True or round(WaterBodies_polygon_points.distance(WaterBodies_label_point),1)==0.0:

                                WaterBodiesPolygonContainLabel.append([WaterBodies_labelID,WaterBodies_label,WaterBodies_entity])

                    if WaterBodiesPolygonContainLabel!=[] and len(WaterBodiesPolygonContainLabel)<=1:

                        for WaterBodies in WaterBodiesPolygonContainLabel:

                            WaterBodiesDict[WaterBodies_PolygonID]=WaterBodies


                    elif(len(WaterBodiesPolygonContainLabel)>1):

                        ErrorMsg = f'Warning:WaterBodies Layer Polygon({WaterBodies_PolygonID}) Found More Than One Label.'

                        ErrorWaterBodiesDict[WaterBodies_PolygonID] = ErrorMsg

                    else:

                        ErrorMsg=f'Warning:WaterBodies Layer Polygon({WaterBodies_PolygonID}) Does Not Have Label.'

                        ErrorWaterBodiesDict[WaterBodies_PolygonID]=ErrorMsg
                else:

                    ErrorMsg = f'Warning:WaterBodies Layer Polygon({WaterBodies_PolygonID}) Does Not Closed Properly.'

                    ErrorWaterBodiesDict[WaterBodies_PolygonID] = ErrorMsg

        return [ErrorWaterBodiesDict,WaterBodiesDict]
    def BufferZone_Layer(self,BufferZoneData):

        BufferZoneDict=dict()

        ErrorBufferZoneDict=dict()

        unique_polygons={}

        for BufferZone_entity in BufferZoneData:

            if BufferZone_entity.dxftype()=='LWPOLYLINE':

                BufferZone_PolygonID = BufferZone_entity.dxf.handle

                if BufferZone_entity.closed:

                    vertices = tuple(BufferZone_entity.get_points())

                    if vertices in unique_polygons:

                        ErrorBufferZoneDict[BufferZone_PolygonID] = str(
                            f"BufferZone Layer Found Duplicate Polygon Of {BufferZone_PolygonID}.")

                    else:

                        unique_polygons[vertices] = BufferZone_entity

                    BufferZone_polygon_points=Polygon(np.array([bzp[0:2] for bzp in BufferZone_entity.get_points()]))

                    BufferZonePolygonContainLabel=[]

                    for BufferZone_entity1 in BufferZoneData:

                        BufferZone_text_properties=BufferZone_entity1.dxfattribs()

                        if BufferZone_entity1.dxftype()=='TEXT' or BufferZone_entity1.dxftype()=='MTEXT':

                            BufferZone_labelID=BufferZone_entity1.dxf.handle

                            BufferZone_label= BufferZone_text_properties.get('text') if BufferZone_entity1.dxftype()=='TEXT' else BufferZone_entity1.plain_text()

                            BufferZone_label_pts=BufferZone_text_properties.get('insert')

                            BufferZone_label_point=Point(np.array([BufferZone_label_pts[0],BufferZone_label_pts[1]]))

                            if BufferZone_polygon_points.contains(BufferZone_label_point)==True or BufferZone_polygon_points.touches(BufferZone_label_point)==True or round(BufferZone_polygon_points.distance(BufferZone_label_point),1)==0.0:

                                BufferZonePolygonContainLabel.append([BufferZone_labelID,BufferZone_label,BufferZone_entity])

                    if BufferZonePolygonContainLabel!=[] and len(BufferZonePolygonContainLabel)<=1:

                        for BufferZone in BufferZonePolygonContainLabel:

                            BufferZoneDict[BufferZone_PolygonID]=BufferZone

                    elif(len(BufferZonePolygonContainLabel)>1):

                        ErrorMsg = f'Warning:BufferZone Layer Polygon({BufferZone_PolygonID}) Found More Than One Label.'

                        ErrorBufferZoneDict[BufferZone_PolygonID] = ErrorMsg

                    else:

                        ErrorMsg=f'Warning:BufferZone Layer Polygon({BufferZone_PolygonID}) Does Not Have Label.'

                        ErrorBufferZoneDict[BufferZone_PolygonID]=ErrorMsg
                else:

                    ErrorMsg = f'Warning:BufferZone Layer Polygon({BufferZone_PolygonID}) Does Not Closed Properly.'

                    ErrorBufferZoneDict[BufferZone_PolygonID] = ErrorMsg

        return [ErrorBufferZoneDict,BufferZoneDict]
    def NetPlot_Layer(self,NetPlotData):

        NetPlotDict=dict()

        ErrorNetPlotDict=dict()

        unique_polygons={}

        for NetPlot_entity in NetPlotData:

            if NetPlot_entity.dxftype()=='LWPOLYLINE':

                NetPlot_PolygonID = NetPlot_entity.dxf.handle

                if NetPlot_entity.closed:

                    vertices = tuple(NetPlot_entity.get_points())

                    if vertices in unique_polygons:

                        ErrorNetPlotDict[NetPlot_PolygonID] = str(f"NetPlot Layer Found Duplicate Polygon Of {NetPlot_PolygonID}.")

                    else:

                        unique_polygons[vertices] = NetPlot_entity

                    NetPlot_polygon_points=Polygon(np.array([npp[0:2] for npp in NetPlot_entity.get_points()]))

                    NetPlotPolygonContainLabel=[]

                    for NetPlot_entity1 in NetPlotData:

                        NetPlot_text_properties=NetPlot_entity1.dxfattribs()

                        if NetPlot_entity1.dxftype()=='TEXT' or NetPlot_entity1.dxftype()=='MTEXT':

                            NetPlot_labelID=NetPlot_entity1.dxf.handle

                            NetPlot_label= NetPlot_text_properties.get('text') if NetPlot_entity1.dxftype()=='TEXT' else NetPlot_entity1.plain_text()

                            NetPlot_label_pts=NetPlot_text_properties.get('insert')

                            NetPlot_label_point=Point(np.array([NetPlot_label_pts[0],NetPlot_label_pts[1]]))

                            if NetPlot_polygon_points.contains(NetPlot_label_point)==True or NetPlot_polygon_points.touches(NetPlot_label_point)==True or round(NetPlot_polygon_points.distance(NetPlot_label_point),1)==0.0:

                                NetPlotPolygonContainLabel.append([NetPlot_labelID,NetPlot_label,NetPlot_entity])

                    if NetPlotPolygonContainLabel!=[] and len(NetPlotPolygonContainLabel)<=1:

                        for NetPlot in NetPlotPolygonContainLabel:

                            NetPlotDict[NetPlot_PolygonID]=NetPlot

                    elif(len(NetPlotPolygonContainLabel)>1):

                        ErrorMsg=f'Warning:NetPlot Layer Polygon({NetPlot_PolygonID}) Found More Than One Label.'

                        ErrorNetPlotDict[NetPlot_PolygonID]=ErrorMsg
                else:

                    ErrorMsg = f'Warning:Plot Layer Polygon({NetPlot_PolygonID}) Does Not Closed Properly.'

                    ErrorNetPlotDict[NetPlot_PolygonID] = ErrorMsg

        return [ErrorNetPlotDict,NetPlotDict]
    def Plot_Layer(self,PlotData):

        PlotDict=dict()

        ErrorPlotDict=dict()

        unique_polygons={}

        for Plot_entity in PlotData:

            if Plot_entity.dxftype()=='LWPOLYLINE':

                Plot_PolygonID = Plot_entity.dxf.handle

                if Plot_entity.closed:

                    vertices = tuple(Plot_entity.get_points())

                    if vertices in unique_polygons:

                        ErrorPlotDict[Plot_PolygonID] = str(
                            f"Plot Layer Found Duplicate Polygon Of {Plot_PolygonID}.")

                    else:

                        unique_polygons[vertices] = Plot_entity

                    Plot_polygon_points=Polygon(np.array([pp[0:2] for pp in Plot_entity.get_points()]))

                    PlotPolygonContainLabel=[]

                    for Plot_entity1 in PlotData:

                        Plot_text_properties=Plot_entity1.dxfattribs()

                        if Plot_entity1.dxftype()=='TEXT' or Plot_entity1.dxftype()=='MTEXT':

                            Plot_labelID=Plot_entity1.dxf.handle

                            Plot_label= Plot_text_properties.get('text') if Plot_entity1.dxftype()=='TEXT' else Plot_entity1.plain_text()

                            Plot_label_pts=Plot_text_properties.get('insert')

                            Plot_label_point=Point(np.array([Plot_label_pts[0],Plot_label_pts[1]]))

                            if Plot_polygon_points.contains(Plot_label_point)==True or Plot_polygon_points.touches(Plot_label_point)==True or round(Plot_polygon_points.distance(Plot_label_point),1)==0.0:

                                PlotPolygonContainLabel.append([Plot_labelID,Plot_label,Plot_entity])

                    if PlotPolygonContainLabel!=[] and len(PlotPolygonContainLabel)<=1:

                        for Plot in PlotPolygonContainLabel:

                            PlotDict[Plot_PolygonID]=Plot


                    elif(len(PlotPolygonContainLabel)>1):

                        ErrorMsg = f'Warning:Plot Layer Polygon({Plot_PolygonID}) Found More Than One Label.'

                        ErrorPlotDict[Plot_PolygonID] = ErrorMsg

                    else:

                        ErrorMsg=f'Warning:Plot Layer Polygon({Plot_PolygonID}) Does Not Have Label.'

                        ErrorPlotDict[Plot_PolygonID]=ErrorMsg
                else:

                    ErrorMsg = f'Warning:Plot Layer Polygon({Plot_PolygonID}) Does Not Closed Properly.'

                    ErrorPlotDict[Plot_PolygonID] = ErrorMsg

        return [ErrorPlotDict,PlotDict]
    def Splay_Layer(self,SplayData):

        SplayDict=dict()

        ErrorSplayDict=dict()

        unique_polygons={}

        for Splay_entity in SplayData:

            if Splay_entity.dxftype()=='LWPOLYLINE':

                Splay_PolygonID = Splay_entity.dxf.handle

                if Splay_entity.closed:

                    vertices = tuple(Splay_entity.get_points())

                    if vertices in unique_polygons:

                        ErrorSplayDict[Splay_PolygonID] = str(
                            f"Splay Layer Found Duplicate Polygon Of {Splay_PolygonID}.")

                    else:

                        unique_polygons[vertices] = Splay_entity

                    Splay_polygon_points=Polygon(np.array([sp[0:2] for sp in Splay_entity.get_points()]))

                    SplayPolygonContainLabel=[]

                    for Splay_entity1 in SplayData:

                        Splay_text_properties=Splay_entity1.dxfattribs()

                        if Splay_entity1.dxftype()=='TEXT' or Splay_entity1.dxftype()=='MTEXT':

                            Splay_labelID=Splay_entity1.dxf.handle

                            Splay_label= Splay_text_properties.get('text') if Splay_entity1.dxftype()=='TEXT' else Splay_entity1.plain_text()

                            Splay_label_pts=Splay_text_properties.get('insert')

                            Splay_label_point=Point(np.array([Splay_label_pts[0],Splay_label_pts[1]]))

                            if Splay_polygon_points.contains(Splay_label_point)==True or Splay_polygon_points.touches(Splay_label_point)==True or round(Splay_polygon_points.distance(Splay_label_point),1)==0.0:

                                SplayPolygonContainLabel.append([Splay_labelID,Splay_label,Splay_entity])

                    if SplayPolygonContainLabel!=[] and len(SplayPolygonContainLabel)<=1:

                        for Splay in SplayPolygonContainLabel:

                            SplayDict[Splay_PolygonID]=Splay


                    elif(len(SplayPolygonContainLabel)>1):

                        ErrorMsg = f'Warning:Splay Layer Polygon({Splay_PolygonID}) Found More Than One Label.'

                        ErrorSplayDict[Splay_PolygonID] = ErrorMsg

                    else:

                        ErrorMsg=f'Warning:Splay Layer Polygon({Splay_PolygonID}) Does Not Have Label.'

                        ErrorSplayDict[Splay_PolygonID]=ErrorMsg
                else:

                    ErrorMsg = f'Warning:Splay Layer Polygon({Splay_PolygonID}) Does Not Closed Properly.'

                    ErrorSplayDict[Splay_PolygonID] = ErrorMsg

        return [ErrorSplayDict,SplayDict]
    def Amalgamation_Layer(self,AmalgamationData):

        AmalgamationDict=dict()

        ErrorAmalgamationDict=dict()

        unique_polygons={}

        for Amalgamation_entity in AmalgamationData:

            if Amalgamation_entity.dxftype()=='LWPOLYLINE':

                Amalgamation_PolygonID = Amalgamation_entity.dxf.handle

                if Amalgamation_entity.closed:

                    vertices = tuple(Amalgamation_entity.get_points())

                    if vertices in unique_polygons:

                        ErrorAmalgamationDict[Amalgamation_PolygonID] = str(
                            f"Amalgamation Layer Found Duplicate Polygon Of {Amalgamation_PolygonID}.")

                    else:

                        unique_polygons[vertices] = Amalgamation_entity

                    Amalgamation_polygon_points=Polygon(np.array([Amp[0:2] for Amp in Amalgamation_entity.get_points()]))

                    AmalgamationPolygonContainLabel=[]

                    for Amalgamation_entity1 in AmalgamationData:

                        Amalgamation_text_properties=Amalgamation_entity1.dxfattribs()

                        if Amalgamation_entity1.dxftype()=='TEXT' or Amalgamation_entity1.dxftype()=='MTEXT':

                            Amalgamation_labelID=Amalgamation_entity1.dxf.handle

                            Amalgamation_label= Amalgamation_text_properties.get('text') if Amalgamation_entity1.dxftype()=='TEXT' else Amalgamation_entity1.plain_text()

                            Amalgamation_label_pts=Amalgamation_text_properties.get('insert')

                            Amalgamation_label_point=Point(np.array([Amalgamation_label_pts[0],Amalgamation_label_pts[1]]))

                            if Amalgamation_polygon_points.contains(Amalgamation_label_point)==True or Amalgamation_polygon_points.touches(Amalgamation_label_point)==True or round(Amalgamation_polygon_points.distance(Amalgamation_label_point),1)==0.0:

                                AmalgamationPolygonContainLabel.append([Amalgamation_labelID,Amalgamation_label,Amalgamation_entity])

                    if AmalgamationPolygonContainLabel!=[] and len(AmalgamationPolygonContainLabel)<=1:

                        for Amalgamation in AmalgamationPolygonContainLabel:

                            AmalgamationDict[Amalgamation_PolygonID]=Amalgamation

                    elif(len(AmalgamationPolygonContainLabel)>1):

                        ErrorMsg = f'Warning:Amalgamation Layer Polygon({Amalgamation_PolygonID}) Found More Than One Label.'

                        ErrorAmalgamationDict[Amalgamation_PolygonID] = ErrorMsg

                    else:

                        ErrorMsg=f'Warning:Amalgamation Layer Polygon({Amalgamation_PolygonID}) Does Not Have Label.'

                        ErrorAmalgamationDict[Amalgamation_PolygonID]=ErrorMsg
                else:

                    ErrorMsg = f'Warning:Amalgamation Layer Polygon({Amalgamation_PolygonID}) Does Not Closed Properly.'

                    ErrorAmalgamationDict[Amalgamation_PolygonID] = ErrorMsg

        return [ErrorAmalgamationDict,AmalgamationDict]

    def AmenityJoinedIntORMain(self,Amenitydict,InternalRoadDict,MainRoadDict):

        ErrorDict=dict()

        for Amenity_values in Amenitydict.values():

            Amenity_polygon_points=Polygon(np.array([Ap[0:2] for Ap in Amenity_values[2].get_points()]))

            AmenityTouchIntORMain=[]

            for InternalRoad_values in InternalRoadDict.values():

                InternalRoad_polygon_points = Polygon(np.array([irp[0:2] for irp in InternalRoad_values[2].get_points()]))

                if Amenity_polygon_points.touches(InternalRoad_polygon_points)==True or round(Amenity_polygon_points.distance(InternalRoad_polygon_points),1)==0.0:

                    AmenityTouchIntORMain.append(True)
                else:
                    AmenityTouchIntORMain.append(False)

            for MainRoad_values in MainRoadDict.values():

                MainRoad_polygon_points = Polygon(np.array([mrp[0:2] for mrp in MainRoad_values[2].get_points()]))

                if Amenity_polygon_points.touches(MainRoad_polygon_points) == True or round(Amenity_polygon_points.distance(MainRoad_polygon_points), 1) == 0.0:

                    AmenityTouchIntORMain.append(True)
                else:
                    AmenityTouchIntORMain.append(False)

            if any(AmenityTouchIntORMain)==False:

                ErrorMsg=f'Warning:Amenity Layer {Amenity_values[2]} ({Amenity_values[0]}) Does Not Touch to MainRoad OR InternalRoad Layer.'

                ErrorDict[Amenity_values[0]]=ErrorMsg

        return ErrorDict
    def MainRoad_Layer(self,MainRoadData):

        MainRoadDict=dict()

        ErrorMainRoadDict=dict()

        unique_polygons={}

        for MainRoad_entity in MainRoadData:

            if MainRoad_entity.dxftype()=='LWPOLYLINE':

                MainRoad_PolygonID = MainRoad_entity.dxf.handle

                if MainRoad_entity.closed:

                    vertices = tuple(MainRoad_entity.get_points())

                    if vertices in unique_polygons:

                        ErrorMainRoadDict[MainRoad_PolygonID] = str(
                            f"MainRoad Layer Found Duplicate Polygon Of {MainRoad_PolygonID}.")

                    else:

                        unique_polygons[vertices] = MainRoad_entity

                    MainRoad_polygon_points=Polygon(np.array([Mp[0:2] for Mp in MainRoad_entity.get_points()]))

                    MainRoadPolygonContainLabel=[]

                    for MainRoad_entity1 in MainRoadData:

                        MainRoad_text_properties=MainRoad_entity1.dxfattribs()

                        if MainRoad_entity1.dxftype()=='TEXT' or MainRoad_entity1.dxftype()=='MTEXT':

                            MainRoad_labelID=MainRoad_entity1.dxf.handle

                            MainRoad_label= MainRoad_text_properties.get('text') if MainRoad_entity1.dxftype()=='TEXT' else MainRoad_entity1.plain_text()

                            MainRoad_label_pts=MainRoad_text_properties.get('insert')

                            MainRoad_label_point=Point(np.array([MainRoad_label_pts[0],MainRoad_label_pts[1]]))

                            if MainRoad_polygon_points.contains(MainRoad_label_point)==True or MainRoad_polygon_points.touches(MainRoad_label_point)==True or round(MainRoad_polygon_points.distance(MainRoad_label_point),1)==0.0:

                                MainRoadPolygonContainLabel.append([MainRoad_labelID,MainRoad_label,MainRoad_entity])

                    if MainRoadPolygonContainLabel!=[] and len(MainRoadPolygonContainLabel)<=1:

                        for MainRoad in MainRoadPolygonContainLabel:

                            MainRoadDict[MainRoad_PolygonID]=MainRoad


                    elif(len(MainRoadPolygonContainLabel)>1):

                        ErrorMsg = f'Warning:MainRoad Layer Polygon({MainRoad_PolygonID}) Found More Than One Label.'

                        ErrorMainRoadDict[MainRoad_PolygonID] = ErrorMsg

                    else:

                        ErrorMsg=f'Warning:MainRoad Layer Polygon({MainRoad_PolygonID}) Does Not Have Label.'

                        ErrorMainRoadDict[MainRoad_PolygonID]=ErrorMsg
                else:

                    ErrorMsg = f'Warning:MainRoad Layer Polygon({MainRoad_PolygonID}) Does Not Closed Properly.'

                    ErrorMainRoadDict[MainRoad_PolygonID] = ErrorMsg

        return [ErrorMainRoadDict,MainRoadDict]
    def InternalRoad_Layer(self,InternalRoadData):

        InternalRoadDict=dict()

        ErrorInternalRoadDict=dict()

        unique_polygons={}

        for InternalRoad_entity in InternalRoadData:

            if InternalRoad_entity.dxftype()=='LWPOLYLINE':

                InternalRoad_polygon_properties = InternalRoad_entity.dxfattribs()

                InternalRoad_PolygonID = InternalRoad_entity.dxf.handle

                if InternalRoad_polygon_properties.get('linetype')!='CENTER':

                    if InternalRoad_entity.closed:

                        vertices = tuple(InternalRoad_entity.get_points())

                        if vertices in unique_polygons:

                            ErrorInternalRoadDict[InternalRoad_PolygonID] = str(
                                f"InternalRoad Layer Found Duplicate Polygon Of {InternalRoad_PolygonID}.")

                        else:

                            unique_polygons[vertices] = InternalRoad_entity

                        InternalRoad_polygon_points=Polygon(np.array([irp[0:2] for irp in InternalRoad_entity.get_points()]))

                        InternalRoadPolygonContainLabel=[]

                        InternalRoadPolygonCenterline = []

                        for InternalRoad_entity1 in InternalRoadData:

                            InternalRoad_text_properties=InternalRoad_entity1.dxfattribs()

                            if InternalRoad_entity1.dxftype()=='TEXT' or InternalRoad_entity1.dxftype()=='MTEXT':

                                InternalRoad_labelID=InternalRoad_entity1.dxf.handle

                                InternalRoad_label= InternalRoad_text_properties.get('text') if InternalRoad_entity1.dxftype()=='TEXT' else InternalRoad_entity1.plain_text()

                                InternalRoad_label_pts=InternalRoad_text_properties.get('insert')

                                InternalRoad_label_point=Point(np.array([InternalRoad_label_pts[0],InternalRoad_label_pts[1]]))

                                if InternalRoad_polygon_points.contains(InternalRoad_label_point)==True or InternalRoad_polygon_points.touches(InternalRoad_label_point)==True or round(InternalRoad_polygon_points.distance(InternalRoad_label_point),1)==0.0:

                                    InternalRoadPolygonContainLabel.append([InternalRoad_labelID,InternalRoad_label,InternalRoad_entity])

                        if InternalRoadPolygonContainLabel!=[] and len(InternalRoadPolygonContainLabel)<=1:

                            for InternalRoad in InternalRoadPolygonContainLabel:

                                InternalRoadDict[InternalRoad_PolygonID]=InternalRoad

                        elif(len(InternalRoadPolygonContainLabel)>1):

                            ErrorMsg = f'Warning:InternalRoad Layer Polygon({InternalRoad_PolygonID}) Found More Than One Label.'

                            ErrorInternalRoadDict[InternalRoad_PolygonID] = ErrorMsg

                        else:

                            ErrorMsg=f'Warning:InternalRoad Layer Polygon({InternalRoad_PolygonID}) Does Not Have Label.'

                            ErrorInternalRoadDict[InternalRoad_PolygonID]=ErrorMsg

                        for InternalRoadcline_entity in InternalRoadData:

                            if InternalRoadcline_entity.dxftype()=='LWPOLYLINE':

                                InternalRoadcline_properties = InternalRoadcline_entity.dxfattribs()

                                if InternalRoadcline_properties.get('linetype')=='CENTER':

                                    InternalRoadclineID=InternalRoadcline_entity.dxf.handle

                                    InternalRoadcline_points=LineString(np.array([iclp[0:2] for iclp in InternalRoadcline_entity.get_points()]))
                                    if all(InternalRoad_polygon_points.touches(Point(point)) or InternalRoad_polygon_points.contains(Point(point)) or round(InternalRoad_polygon_points.distance(Point(point)),1) == 0.0 for point in InternalRoadcline_points.coords) == True:
                                    #if InternalRoad_polygon_points.contains(InternalRoadcline_points)==True or InternalRoad_polygon_points.touches(InternalRoadcline_points)==True or round(InternalRoad_polygon_points.distance(InternalRoadcline_points),1)==0.0:

                                        InternalRoadPolygonCenterline.append([InternalRoadclineID,InternalRoadcline_entity,InternalRoad_entity])

                        if InternalRoadPolygonCenterline == [] and len(InternalRoadPolygonCenterline) == 0:

                            ErrorMsg = f'Warning:InternalRoad Layer Polygon({InternalRoad_PolygonID}) Does Not Have CenterLine.'

                            ErrorInternalRoadDict[InternalRoad_PolygonID] = ErrorMsg

                        elif(len(InternalRoadPolygonCenterline) > 1):

                            ErrorMsg = f'Warning:InternalRoad Layer Polygon({InternalRoad_PolygonID}) Found More Than One CenterLine.'

                            ErrorInternalRoadDict[InternalRoad_PolygonID] = ErrorMsg

                    else:

                        ErrorMsg = f'Warning:InternalRoad Layer Polygon({InternalRoad_PolygonID}) Does Not Closed Properly.'

                        ErrorInternalRoadDict[InternalRoad_PolygonID] = ErrorMsg

                elif(InternalRoad_polygon_properties.get('linetype')=='CENTER'):

                    InternalRoad_centerline_points = LineString(np.array([icp[0:2] for icp in InternalRoad_entity.get_points()]))

                    CenterlineTouchInternalRoadpolygon=[]

                    for InternalRoad_entity in InternalRoadData:

                        if InternalRoad_entity.dxftype() == 'LWPOLYLINE':

                            InternalRoad_polygon_properties = InternalRoad_entity.dxfattribs()

                            InternalRoad_PolygonID = InternalRoad_entity.dxf.handle

                            if InternalRoad_polygon_properties.get('linetype')!= 'CENTER':

                                if InternalRoad_entity.closed:

                                    InternalRoad_polygon_points = Polygon(np.array([icp[0:2] for icp in InternalRoad_entity.get_points()]))
                                    if all(InternalRoad_polygon_points.touches(Point(point)) or InternalRoad_polygon_points.contains(Point(point)) or round(InternalRoad_polygon_points.distance(Point(point)),1) == 0.0 for point in InternalRoad_centerline_points.coords) == True:
                                    #if InternalRoad_polygon_points.contains(InternalRoad_centerline_points)==True or InternalRoad_polygon_points.touches(InternalRoad_centerline_points)==True or round(InternalRoad_polygon_points.distance(InternalRoad_centerline_points),1)==0.0:

                                        CenterlineTouchInternalRoadpolygon.append([InternalRoad_PolygonID,InternalRoad_centerline_points,InternalRoad_polygon_points])

                    if CenterlineTouchInternalRoadpolygon==[] and len(CenterlineTouchInternalRoadpolygon)==0:

                        ErrorMsg = f'Warning:InternalRoad Layer Centerline ({InternalRoad_PolygonID}) Does Not Have Any Polygon.'

                        ErrorInternalRoadDict[InternalRoad_PolygonID] = ErrorMsg


                    elif(len(CenterlineTouchInternalRoadpolygon)>1):

                        ErrorMsg = f'Warning:InternalRoad Layer Centerline ({InternalRoad_PolygonID}) Found More Than One Polygon.'

                        ErrorInternalRoadDict[InternalRoad_PolygonID] = ErrorMsg

                else:

                    ErrorMsg = f'Warning:InternalRoad Layer Polygon({InternalRoad_PolygonID}) Does Not Get Polyline Type.'

                    ErrorInternalRoadDict[InternalRoad_PolygonID] = ErrorMsg


        return [ErrorInternalRoadDict,InternalRoadDict]
    def Amenity_Layer(self,AmenityData):

        AmenityDict=dict()

        ErrorAmenityDict=dict()

        unique_polygons={}

        for Amenity_entity in AmenityData:

            if Amenity_entity.dxftype()=='LWPOLYLINE':

                Amenity_PolygonID = Amenity_entity.dxf.handle

                if Amenity_entity.closed:

                    vertices = tuple(Amenity_entity.get_points())

                    if vertices in unique_polygons:

                        ErrorAmenityDict[Amenity_PolygonID] = str(
                            f"Amenity Layer Found Duplicate Polygon Of {Amenity_PolygonID}.")

                    else:

                        unique_polygons[vertices] = Amenity_entity

                    Amenity_polygon_points=Polygon(np.array([Ap[0:2] for Ap in Amenity_entity.get_points()]))

                    AmenityPolygonContainLabel=[]

                    for Amenity_entity1 in AmenityData:

                        Amenity_text_properties=Amenity_entity1.dxfattribs()

                        if Amenity_entity1.dxftype()=='TEXT' or Amenity_entity1.dxftype()=='MTEXT':

                            Amenity_labelID=Amenity_entity1.dxf.handle

                            Amenity_label= Amenity_text_properties.get('text') if Amenity_entity1.dxftype()=='TEXT' else Amenity_entity1.plain_text()

                            Amenity_label_pts=Amenity_text_properties.get('insert')

                            Amenity_label_point=Point(np.array([Amenity_label_pts[0],Amenity_label_pts[1]]))

                            if Amenity_polygon_points.contains(Amenity_label_point)==True or Amenity_polygon_points.touches(Amenity_label_point)==True or round(Amenity_polygon_points.distance(Amenity_label_point),1)==0.0:

                                AmenityPolygonContainLabel.append([Amenity_labelID,Amenity_label,Amenity_entity])

                    if AmenityPolygonContainLabel!=[] and len(AmenityPolygonContainLabel)<=1:

                        for Amenity in AmenityPolygonContainLabel:

                            AmenityDict[Amenity_PolygonID]=Amenity

                    elif(len(AmenityPolygonContainLabel)>1):

                        ErrorMsg = f'Warning:Amenity Layer Polygon({Amenity_PolygonID}) Found More Than One Label.'

                        ErrorAmenityDict[Amenity_PolygonID] = ErrorMsg

                    else:

                        ErrorMsg=f'Warning:Amenity Layer Polygon({Amenity_PolygonID}) Does Not Have Label.'

                        ErrorAmenityDict[Amenity_PolygonID]=ErrorMsg
                else:

                    ErrorMsg = f'Warning:Amenity Layer Polygon({Amenity_PolygonID}) Does Not Closed Properly.'

                    ErrorAmenityDict[Amenity_PolygonID] = ErrorMsg

        return [ErrorAmenityDict,AmenityDict]
    def MortgageArea_Layer(self,MortgageAreaData):

        MortgageAreaDict=dict()

        ErrorMortgageAreaDict=dict()

        unique_polygons={}

        for MortgageArea_entity in MortgageAreaData:

            if MortgageArea_entity.dxftype()=='LWPOLYLINE':

                MortgageArea_PolygonID = MortgageArea_entity.dxf.handle

                if MortgageArea_entity.closed:

                    vertices = tuple(MortgageArea_entity.get_points())

                    if vertices in unique_polygons:

                        ErrorMortgageAreaDict[MortgageArea_PolygonID] = str(
                            f"MortgageArea Layer Found Duplicate Polygon Of {MortgageArea_PolygonID}.")

                    else:

                        unique_polygons[vertices] = MortgageArea_entity

                    MortgageArea_polygon_points=Polygon(np.array([map[0:2] for map in MortgageArea_entity.get_points()]))

                    MortgageAreaPolygonContainLabel=[]

                    for MortgageArea_entity1 in MortgageAreaData:

                        MortgageArea_text_properties=MortgageArea_entity1.dxfattribs()

                        if MortgageArea_entity1.dxftype()=='TEXT' or MortgageArea_entity1.dxftype()=='MTEXT':

                            MortgageArea_labelID=MortgageArea_entity1.dxf.handle

                            MortgageArea_label= MortgageArea_text_properties.get('text') if MortgageArea_entity1.dxftype()=='TEXT' else MortgageArea_entity1.plain_text()

                            MortgageArea_label_pts=MortgageArea_text_properties.get('insert')

                            MortgageArea_label_point=Point(np.array([MortgageArea_label_pts[0],MortgageArea_label_pts[1]]))

                            if MortgageArea_polygon_points.contains(MortgageArea_label_point)==True or MortgageArea_polygon_points.touches(MortgageArea_label_point)==True or round(MortgageArea_polygon_points.distance(MortgageArea_label_point),1)==0.0:

                                MortgageAreaPolygonContainLabel.append([MortgageArea_labelID,MortgageArea_label,MortgageArea_entity])

                    if MortgageAreaPolygonContainLabel!=[] and len(MortgageAreaPolygonContainLabel)<=1:

                        for MortgageArea in MortgageAreaPolygonContainLabel:

                            MortgageAreaDict[MortgageArea_PolygonID]=MortgageArea


                    elif(len(MortgageAreaPolygonContainLabel)>1):

                        ErrorMsg = f'Warning:MortgageArea Layer Polygon({MortgageArea_PolygonID}) Found More Than One Label.'

                        ErrorMortgageAreaDict[MortgageArea_PolygonID] = ErrorMsg

                    else:

                        ErrorMsg=f'Warning:MortgageArea Layer Polygon({MortgageArea_PolygonID}) Does Not Have Label.'

                        ErrorMortgageAreaDict[MortgageArea_PolygonID]=ErrorMsg
                else:

                    ErrorMsg = f'Warning:MortgageArea Layer Polygon({MortgageArea_PolygonID}) Does Not Closed Properly.'

                    ErrorMortgageAreaDict[MortgageArea_PolygonID] = ErrorMsg

        return [ErrorMortgageAreaDict,MortgageAreaDict]
    def AccessoryUse_Layer(self,AccessoryUseData):

        AccessoryUseDict=dict()

        ErrorAccessoryUseDict=dict()

        unique_polygons={}

        for AccessoryUse_entity in AccessoryUseData:

            if AccessoryUse_entity.dxftype()=='LWPOLYLINE':

                AccessoryUse_PolygonID = AccessoryUse_entity.dxf.handle

                if AccessoryUse_entity.closed:

                    vertices = tuple(AccessoryUse_entity.get_points())

                    if vertices in unique_polygons:

                        ErrorAccessoryUseDict[AccessoryUse_PolygonID] = str(
                            f"AccessoryUse Layer Found Duplicate Polygon Of {AccessoryUse_PolygonID}.")

                    else:

                        unique_polygons[vertices] = AccessoryUse_entity

                    AccessoryUse_polygon_points=Polygon(np.array([ap[0:2] for ap in AccessoryUse_entity.get_points()]))

                    AccessoryUsePolygonContainLabel=[]

                    for AccessoryUse_entity1 in AccessoryUseData:

                        AccessoryUse_text_properties=AccessoryUse_entity1.dxfattribs()

                        if AccessoryUse_entity1.dxftype()=='TEXT' or AccessoryUse_entity1.dxftype()=='MTEXT':

                            AccessoryUse_labelID=AccessoryUse_entity1.dxf.handle

                            AccessoryUse_label= AccessoryUse_text_properties.get('text') if AccessoryUse_entity1.dxftype()=='TEXT' else AccessoryUse_entity1.plain_text()

                            AccesorUse_label_pts=AccessoryUse_text_properties.get('insert')

                            AccessoryUse_label_point=Point(np.array([AccesorUse_label_pts[0],AccesorUse_label_pts[1]]))

                            if AccessoryUse_polygon_points.contains(AccessoryUse_label_point)==True or AccessoryUse_polygon_points.touches(AccessoryUse_label_point)==True or round(AccessoryUse_polygon_points.distance(AccessoryUse_label_point),1)==0.0:

                                AccessoryUsePolygonContainLabel.append([AccessoryUse_labelID,AccessoryUse_label,AccessoryUse_entity])

                    if AccessoryUsePolygonContainLabel!=[] and len(AccessoryUsePolygonContainLabel)<=1:

                        for Accessory in AccessoryUsePolygonContainLabel:

                            AccessoryUseDict[AccessoryUse_PolygonID]=Accessory

                    elif(len(AccessoryUsePolygonContainLabel)>1):

                        ErrorMsg = f'Warning:AccessoryUse Layer Polygon({AccessoryUse_PolygonID}) Found More Than One Label.'

                        ErrorAccessoryUseDict[AccessoryUse_PolygonID] = ErrorMsg

                    else:

                        ErrorMsg=f'Warning:AccessoryUse Layer Polygon({AccessoryUse_PolygonID}) Does Not Have Label.'

                        ErrorAccessoryUseDict[AccessoryUse_PolygonID]=ErrorMsg
                else:

                    ErrorMsg = f'Warning:AccessoryUse Layer Polygon({AccessoryUse_PolygonID}) Does Not Closed Properly.'

                    ErrorAccessoryUseDict[AccessoryUse_PolygonID] = ErrorMsg

        return [ErrorAccessoryUseDict,AccessoryUseDict]
    def WallCompound_Layer(self,WallCompoundData):

        WallCompoundDict=dict()

        ErrorWallCompoundDict=dict()

        unique_polygons={}

        for WallCompound_entity in WallCompoundData:

            if WallCompound_entity.dxftype()=='LWPOLYLINE':

                WallCompound_polygon_properties = WallCompound_entity.dxfattribs()

                WallCompound_PolygonID = WallCompound_entity.dxf.handle

                if WallCompound_polygon_properties.get('linetype').lower()!='center':

                    if WallCompound_entity.closed:

                        vertices = tuple(WallCompound_entity.get_points())

                        if vertices in unique_polygons:

                            ErrorWallCompoundDict[WallCompound_PolygonID] = str(f"WallCompound Layer Found Duplicate Polygon Of {WallCompound_PolygonID}.")

                        else:

                            unique_polygons[vertices] = WallCompound_entity

                        WallCompound_polygon_points=Polygon(np.array([wcp[0:2] for wcp in WallCompound_entity.get_points()]))

                        WallCompoundPolygonContainLabel=[]

                        WallCompoundPolygonCenterline = []

                        for WallCompound_entity1 in WallCompoundData:

                            WallCompound_text_properties=WallCompound_entity1.dxfattribs()

                            if WallCompound_entity1.dxftype()=='TEXT' or WallCompound_entity1.dxftype()=='MTEXT':

                                WallCompound_labelID=WallCompound_entity1.dxf.handle

                                WallCompound_label= WallCompound_text_properties.get('text') if WallCompound_entity1.dxftype()=='TEXT' else WallCompound_entity1.plain_text()

                                WallCompound_label_pts=WallCompound_text_properties.get('insert')

                                WallCompound_label_point=Point(np.array([WallCompound_label_pts[0],WallCompound_label_pts[1]]))

                                if WallCompound_polygon_points.contains(WallCompound_label_point)==True or WallCompound_polygon_points.touches(WallCompound_label_point)==True or round(WallCompound_polygon_points.distance(WallCompound_label_point),1)==0.0:

                                    WallCompoundPolygonContainLabel.append([WallCompound_labelID,WallCompound_label,WallCompound_entity])

                        if WallCompoundPolygonContainLabel!=[] and len(WallCompoundPolygonContainLabel)<=1:

                            WallCompoundDict[WallCompound_PolygonID]=WallCompoundPolygonContainLabel


                        elif(len(WallCompoundPolygonContainLabel)>1):

                            ErrorMsg = f'Warning:WallCompound Layer Polygon({WallCompound_PolygonID}) Found More Than One Label.'

                            ErrorWallCompoundDict[WallCompound_PolygonID] = ErrorMsg

                        else:

                            ErrorMsg=f'Warning:WallCompound Layer Polygon({WallCompound_PolygonID}) Does Not Have Label.'

                            ErrorWallCompoundDict[WallCompound_PolygonID]=ErrorMsg


                        for WallCompoundcline_entity in WallCompoundData:

                            if WallCompoundcline_entity.dxftype()=='LWPOLYLINE':

                                WallCompoundcline_properties = WallCompoundcline_entity.dxfattribs()

                                if WallCompoundcline_properties.get('linetype').lower()=='center':

                                    WallCompoundclineID=WallCompoundcline_entity.dxf.handle

                                    WallCompoundcline_points=LineString(np.array([wclp[0:2] for wclp in WallCompoundcline_entity.get_points()]))
                                    if all(WallCompound_polygon_points.touches(Point(point)) or WallCompound_polygon_points.contains(Point(point)) or round(WallCompound_polygon_points.distance(Point(point)),1) == 0.0 for point in WallCompoundcline_points.coords) == True:
                                    #if WallCompound_polygon_points.contains(WallCompoundcline_points)==True or WallCompound_polygon_points.touches(WallCompoundcline_points)==True or round(WallCompound_polygon_points.distance(WallCompoundcline_points),1)==0.0:

                                        WallCompoundPolygonCenterline.append([WallCompoundclineID,WallCompoundcline_entity,WallCompound_entity])

                        if WallCompoundPolygonCenterline == [] and len(WallCompoundPolygonCenterline) == 0:

                            ErrorMsg = f'Warning:WallCompound Layer Polygon({WallCompound_PolygonID}) Does Not Have CenterLine.'

                            ErrorWallCompoundDict[WallCompound_PolygonID] = ErrorMsg

                        elif(len(WallCompoundPolygonCenterline) > 1):

                            ErrorMsg = f'Warning:WallCompound Layer Polygon({WallCompound_PolygonID}) Found More Than One CenterLine.'

                            ErrorWallCompoundDict[WallCompound_PolygonID] = ErrorMsg

                    else:

                        ErrorMsg = f'Warning:WallCompound Layer Polygon({WallCompound_PolygonID}) Does Not Closed Properly.'

                        ErrorWallCompoundDict[WallCompound_PolygonID] = ErrorMsg

                elif(WallCompound_polygon_properties.get('linetype').lower()=='center'):

                    WallCompound_centerline_points = LineString(np.array([wcp[0:2] for wcp in WallCompound_entity.get_points()]))

                    CenterlineTouchWallCompoundpolygon=[]

                    for WallCompound_entity in WallCompoundData:

                        if WallCompound_entity.dxftype() == 'LWPOLYLINE':

                            WallCompound_polygon_properties = WallCompound_entity.dxfattribs()

                            WallCompound_PolygonID = WallCompound_entity.dxf.handle

                            if WallCompound_polygon_properties.get('linetype').lower() != 'center':

                                if WallCompound_entity.closed:

                                    WallCompound_polygon_points = Polygon(np.array([wcp[0:2] for wcp in WallCompound_entity.get_points()]))

                                    if all(WallCompound_polygon_points.touches(Point(point)) or WallCompound_polygon_points.contains(Point(point)) or round(WallCompound_polygon_points.distance(Point(point)),1) == 0.0 for point in WallCompound_centerline_points.coords) == True:

                                    #if WallCompound_polygon_points.contains(WallCompound_centerline_points)==True or WallCompound_polygon_points.touches(WallCompound_centerline_points)==True or round(WallCompound_polygon_points.distance(WallCompound_centerline_points),1)==0.0:

                                        CenterlineTouchWallCompoundpolygon.append([WallCompound_PolygonID,WallCompound_centerline_points,WallCompound_polygon_points])

                    if CenterlineTouchWallCompoundpolygon==[] and len(CenterlineTouchWallCompoundpolygon)==0:

                        ErrorMsg = f'Warning:WallCompound Layer Centerline ({WallCompound_PolygonID}) Does Not Have Any Polygon.'

                        ErrorWallCompoundDict[WallCompound_PolygonID] = ErrorMsg


                    elif(len(CenterlineTouchWallCompoundpolygon)>1):

                        ErrorMsg = f'Warning:WallCompound Layer Centerline ({WallCompound_PolygonID}) Found More Than One Polygon.'

                        ErrorWallCompoundDict[WallCompound_PolygonID] = ErrorMsg

                else:

                    ErrorMsg = f'Warning:WallCompound Layer Polygon({WallCompound_PolygonID}) Does Not Get Polyline Type.'

                    ErrorWallCompoundDict[WallCompound_PolygonID] = ErrorMsg


        return [ErrorWallCompoundDict,WallCompoundDict]
    def CycleTrack_Layer(self,CycleTrackData):

        CycleTrackDict = dict()

        ErrorCycleTrackDict = dict()

        unique_polygons = {}

        for CycleTrack_entity in CycleTrackData:

            if CycleTrack_entity.dxftype() == 'LWPOLYLINE':

                CycleTrack_PolygonID = CycleTrack_entity.dxf.handle

                if CycleTrack_entity.closed:

                    vertices = tuple(CycleTrack_entity.get_points())

                    if vertices in unique_polygons:

                            ErrorCycleTrackDict[CycleTrack_PolygonID] = str(f"CycleTrack Layer Found Duplicate Polygon Of {CycleTrack_PolygonID}.")

                    else:

                        unique_polygons[vertices] = CycleTrack_entity

                    CycleTrack_polygon_points = Polygon(np.array([cp[0:2] for cp in CycleTrack_entity.get_points()]))

                    CycleTrackPolygonContainLabel = []

                    for CycleTrack_entity1 in CycleTrackData:

                        CycleTrack_text_properties = CycleTrack_entity1.dxfattribs()

                        if CycleTrack_entity1.dxftype() == 'TEXT' or CycleTrack_entity1.dxftype() == 'MTEXT':

                            CycleTrack_labelID = CycleTrack_entity1.dxf.handle

                            CycleTrack_label = CycleTrack_text_properties.get('text') if CycleTrack_entity1.dxftype() == 'TEXT' else CycleTrack_entity1.plain_text()

                            CycleTrack_label_pts = CycleTrack_text_properties.get('insert')

                            CycleTrack_label_point = Point(np.array([CycleTrack_label_pts[0], CycleTrack_label_pts[1]]))

                            if CycleTrack_polygon_points.contains(CycleTrack_label_point) == True or CycleTrack_polygon_points.touches(CycleTrack_label_point) == True or round(CycleTrack_polygon_points.distance(CycleTrack_label_point), 1) <= 2.0:

                                    CycleTrackPolygonContainLabel.append([CycleTrack_labelID, CycleTrack_label, CycleTrack_entity])

                    if CycleTrackPolygonContainLabel != [] and len(CycleTrackPolygonContainLabel) >= 1:

                        for CycleTrack in CycleTrackPolygonContainLabel:

                            CycleTrackDict[CycleTrack_PolygonID] = CycleTrack

                    else:

                        ErrorMsg = f'Warning:CycleTrack Layer Polygon({CycleTrack_PolygonID}) Does Not Have Label.'

                        ErrorCycleTrackDict[CycleTrack_PolygonID] = ErrorMsg
                else:

                    ErrorMsg = f'Warning:CycleTrack Layer Polygon({CycleTrack_PolygonID}) Does Not Closed Properly.'

                    ErrorCycleTrackDict[CycleTrack_PolygonID] = ErrorMsg

        return [ErrorCycleTrackDict, CycleTrackDict]
    def ValLayersOpenLayout(self,msp):

        ErrorMessageList=[]

        if (msp is None):

            return ErrorMessageList

        try:

            AccessoryUse_data = msp.query('*[layer=="_AccessoryUse"]')

            WallCompound_data = msp.query('*[layer=="_WallCompound"]')

            Amenity_data = msp.query('*[layer=="_Amenity"]')

            InternalRoad_data = msp.query('*[layer=="_InternalRoad"]')

            MainRoad_data = msp.query('*[layer=="_MainRoad"]')

            Amalgamation_data = msp.query('*[layer=="_Amalgamation"]')

            Plot_data = msp.query('*[layer=="_Plot"]')

            BufferZone_data = msp.query('*[layer=="_BufferZone"]')

            Subplots_data = msp.query('*[layer=="_IndivSubPlot"]')

            ExistingInternalRoad_data = msp.query('*[layer=="_ExistingInternalRoad"]')

            OrganizedOpenSpace_data = msp.query('*[layer=="_OrganizedOpenSpace"]')

            RoadWidening_data = msp.query('*[layer=="_RoadWidening"]')

            NalaWidening_data = msp.query('*[layer=="_NalaWidening"]')

            Parking_data = msp.query('*[layer=="_Parking"]')

            MortgageArea_data = msp.query('*[layer=="_MortgageArea"]')

            Netplot_data = msp.query('*[layer=="_NetPlot"]')

            Splay_data = msp.query('*[layer=="_Splay"]')

            WaterBodies_data = msp.query('*[layer=="_WaterBodies"]')

            CycleTrack_data = msp.query('*[layer=="_Cycletrack"]')

            AccessoryUseLayerDict=self.AccessoryUse_Layer(AccessoryUse_data)

            WallCompoundLayerDict = self.WallCompound_Layer(WallCompound_data)

            AmenityLayerDict = self.Amenity_Layer(Amenity_data)

            InternalRoadLayerDict = self.InternalRoad_Layer(InternalRoad_data)

            MainRoadLayerDict = self.MainRoad_Layer(MainRoad_data)

            AmalgamationLayerDict = self.Amalgamation_Layer(Amalgamation_data)

            PlotLayerDict = self.Plot_Layer(Plot_data)

            BufferZoneLayerDict = self.BufferZone_Layer(BufferZone_data)

            SubplotsLayerDict = self.Subplots_Layer(Subplots_data)

            ExistingInternalRoadLayerDict = self.ExistingInternalRoad_Layer(ExistingInternalRoad_data)

            OrganizedOpenSpaceLayerDict = self.OrganizedOpenSpace_Layer(OrganizedOpenSpace_data)

            RoadWideningLayerDict = self.RoadWidening_Layer(RoadWidening_data)

            NalaWideningLayerDict = self.NalaWidening_Layer(NalaWidening_data)

            ParkingLayerDict = self.Parking_Layer(Parking_data)

            MortgageAreaLayerDict=self.MortgageArea_Layer(MortgageArea_data)

            NetPlotLayerList = self.NetPlot_Layer(Netplot_data)

            SplayLayerList=self.Splay_Layer(Splay_data)

            WaterBodiesLayerList = self.Splay_Layer(WaterBodies_data)

            cycletracklayerList=self.CycleTrack_Layer(CycleTrack_data)


            #-------------------------------------------------Check Labels And Center Line--------------------------------------------------------------------------------

            if AccessoryUseLayerDict[0]!={} and len(AccessoryUseLayerDict[0])>0:

                for acessoryError in AccessoryUseLayerDict[0].values():

                    ErrorMessageList.append(acessoryError)

            if WallCompoundLayerDict[0] != {} and len(WallCompoundLayerDict[0]) > 0:

                for WallCompoundError in WallCompoundLayerDict[0].values():

                    ErrorMessageList.append(WallCompoundError)

            if AmenityLayerDict[0] != {} and len(AmenityLayerDict[0]) > 0:

                for AmenityError in AmenityLayerDict[0].values():

                    ErrorMessageList.append(AmenityError)

            if InternalRoadLayerDict[0] != {} and len(InternalRoadLayerDict[0]) > 0:

                for InternalRoadError in InternalRoadLayerDict[0].values():

                    ErrorMessageList.append(InternalRoadError)

            if MainRoadLayerDict[0] != {} and len(MainRoadLayerDict[0]) > 0:

                for MainRoadError in MainRoadLayerDict[0].values():

                    ErrorMessageList.append(MainRoadError)

            if AmalgamationLayerDict[0] != {} and len(AmalgamationLayerDict[0]) > 0:

                for AmalgamationError in AmalgamationLayerDict[0].values():

                    ErrorMessageList.append(AmalgamationError)

            if PlotLayerDict[0] != {} and len(PlotLayerDict[0]) > 0:

                for PlotErrorlist in PlotLayerDict[0].values():

                    ErrorMessageList.append(PlotErrorlist)

            if BufferZoneLayerDict[0] != {} and len(BufferZoneLayerDict[0]) > 0:

                for BufferZoneError in BufferZoneLayerDict[0].values():

                    ErrorMessageList.append(BufferZoneError)

            if SubplotsLayerDict[0] != {} and len(SubplotsLayerDict[0]) > 0:

                for SubplotsError in SubplotsLayerDict[0].values():

                    ErrorMessageList.append(SubplotsError)

            if ExistingInternalRoadLayerDict[0] != {} and len(ExistingInternalRoadLayerDict[0]) > 0:

                for ExistingInternalRoadError in ExistingInternalRoadLayerDict[0].values():

                    ErrorMessageList.append(ExistingInternalRoadError)

            if OrganizedOpenSpaceLayerDict[0] != {} and len(OrganizedOpenSpaceLayerDict[0]) > 0:

                for OrganizedOpenSpaceError in OrganizedOpenSpaceLayerDict[0].values():

                    ErrorMessageList.append(OrganizedOpenSpaceError)

            if RoadWideningLayerDict[0] != {} and len(RoadWideningLayerDict[0]) > 0:

                for RoadWideningError in RoadWideningLayerDict[0].values():

                    ErrorMessageList.append(RoadWideningError)

            if NalaWideningLayerDict[0] != {} and len(NalaWideningLayerDict[0]) > 0:

                for NalaWideningErrorlist in NalaWideningLayerDict[0].values():

                    ErrorMessageList.append(NalaWideningErrorlist)

            if ParkingLayerDict[0] != {} and len(ParkingLayerDict[0]) > 0:

                for ParkingError in ParkingLayerDict[0].values():

                    ErrorMessageList.append(ParkingError)

            if MortgageAreaLayerDict[0] != {} and len(MortgageAreaLayerDict[0]) > 0:

                for MortgageAreaError in MortgageAreaLayerDict[0].values():

                    ErrorMessageList.append(MortgageAreaError)

            if NetPlotLayerList[0] != {} and len(NetPlotLayerList[0]) > 0:

                for NetPlotError in NetPlotLayerList[0].values():

                    ErrorMessageList.append(NetPlotError)

            if SplayLayerList[0] != {} and len(SplayLayerList[0]) > 0:

                for SplayError in SplayLayerList[0].values():

                    ErrorMessageList.append(SplayError)

            if WaterBodiesLayerList[0] != {} and len(WaterBodiesLayerList[0]) > 0:

                for WaterBodiesError in WaterBodiesLayerList[0].values():

                    ErrorMessageList.append(WaterBodiesError)

            if cycletracklayerList[0] !={} and len(cycletracklayerList[0]) > 0:

                for cycletrackError in cycletracklayerList[0].values():

                    ErrorMessageList.append(cycletrackError)

            #--------------------------------------------check for Accessory Use----------------------------------------

            #When there is a gate, you need to have a compound wall.
            # If there is a compound wall there needs to be a gate.
            # Rain water harvesting and the below four should also be in plot layer and no other layer.
            # (ii) Percolation Well or Percolation Pit (iii) Sewage Treatment Plant (vi) Fire Control Room xiii) Utility

            ValidForAccessoryUse=self.ValidForAccessoryUse(AccessoryUseLayerDict[1],WallCompoundLayerDict[1],PlotLayerDict[1])

            if ValidForAccessoryUse is not None:

                for ErrorAccessoryUse in ValidForAccessoryUse.values():

                    ErrorMessageList.append(ErrorAccessoryUse)

            #--------------------------------------check for Amenity Joined with Internal Road or MainRoad Layer ----------------------------------------------------

            #Amenity layer should always touch main road layer or InternalRoad Layer.

            AmenityJoinedIntORMain = self.AmenityJoinedIntORMain(AmenityLayerDict[1], InternalRoadLayerDict[1],MainRoadLayerDict[1])

            if AmenityJoinedIntORMain is not None:

                for AmenityError in AmenityJoinedIntORMain.values():

                    ErrorMessageList.append(AmenityError)


            #----------------------------------------Check for Subplot ,totlot, touched with InternalRoad Layer------------------------------------

            #Internal road should always touch such IndSub plot area.  This layer should be within plot line layer.Internal Road can touch  Splay, tot-lot, utility ,amenities;
            #Internal road Entity can also touch  one of following entities :
            #MainRoad
            #RoadWidening,ExistingInternalRoad

            SubplottouchRoads=self.SubplotsToucheRoads(SubplotsLayerDict[1],InternalRoadLayerDict[1],MainRoadLayerDict[1],ExistingInternalRoadLayerDict[1])

            if SubplottouchRoads is not None:

                for SubplottouchRoadsError in SubplottouchRoads.values():

                    ErrorMessageList.append(SubplottouchRoadsError)


            RoadstouchORContainsPlot= self.RoadstouchORContainsPlot(PlotLayerDict[1],InternalRoadLayerDict[1],MainRoadLayerDict[1],ExistingInternalRoadLayerDict[1])

            if RoadstouchORContainsPlot is not None:

                for RoadstouchORContainsPlotError in RoadstouchORContainsPlot.values():

                    ErrorMessageList.append(RoadstouchORContainsPlotError)


            #Internal Road  entity should not intersect (overlap) with following entities :
            # MainRoad,InternalRoad,RoadWidening,ExistingInternalRoad,OrganizedOpenSpace,IndivSubPlot,Parking,AccessoryUse

            InternalRoadNotIntersect=self.InternalRoadNotIntersect(InternalRoadLayerDict[1],MainRoadLayerDict[1],RoadWideningLayerDict[1],ExistingInternalRoadLayerDict[1],OrganizedOpenSpaceLayerDict[1],SubplotsLayerDict[1],ParkingLayerDict[1],AccessoryUseLayerDict[1])

            if InternalRoadNotIntersect is not None:

                for InternalRoadNotIntersectError in InternalRoadNotIntersect.values():

                    ErrorMessageList.append(InternalRoadNotIntersectError)

            #-----------------------------------------MainRoad Layer Touch for plot ,Compound wall, road widening, nalawidening--------------------------------

            #Main Road should touch any one of the following.plot ,Compound wall, road widening, nalawidening

            MainRoadtouchPCRN=self.MainRoadtouchPCRN(MainRoadLayerDict[1],PlotLayerDict[1],WallCompoundLayerDict[1],RoadWideningLayerDict[1],NalaWideningLayerDict[1])

            if MainRoadtouchPCRN is not None:

                for MainRoadtouchPCRNError in MainRoadtouchPCRN.values():

                    ErrorMessageList.append(MainRoadtouchPCRNError)

            #-----------------------------------------MortgageArea Overlap Only on SubPlots--------------------------------------

            #Mortgage layer should overlap only ind.sub plots.And nothing else.

            MortgageAreaOverlap = self.MortgageAreaOverlap(MortgageAreaLayerDict[1], AccessoryUseLayerDict[1], InternalRoadLayerDict[1],MainRoadLayerDict[1], NalaWideningLayerDict[1],PlotLayerDict[1],AmenityLayerDict[1],OrganizedOpenSpaceLayerDict[1],BufferZoneLayerDict[1],RoadWideningLayerDict[1])

            if MortgageAreaOverlap is not None:

                for MortgageAreaOverlapError in MortgageAreaOverlap.values():

                    ErrorMessageList.append(MortgageAreaOverlapError)

            # -----------------------------------------OrganizedOpenSpace Does Not Overlap On Any Layers--------------------------------------

            #Organised Open Space layer should be in net plot layer and should not overlap other layer.

            OrganizedOpenSpaceOverlap = self.OrganizedOpenSpaceOverlap(OrganizedOpenSpaceLayerDict[1],MortgageAreaLayerDict[1], AccessoryUseLayerDict[1],InternalRoadLayerDict[1],MainRoadLayerDict[1], NalaWideningLayerDict[1],PlotLayerDict[1], AmenityLayerDict[1], BufferZoneLayerDict[1],RoadWideningLayerDict[1])

            if OrganizedOpenSpaceOverlap is not None:

                for OrganizedOpenSpaceOverlapError in OrganizedOpenSpaceOverlap.values():

                        ErrorMessageList.append(OrganizedOpenSpaceOverlapError)

            #-----------------------------------------------Netplot Layer Always Within Plot layer---------------------------------------------

            #Netplot is always within plotlayer.

            NetplotWithPlotLayer=self.NetPlotWithPlotLayer(NetPlotLayerList[1],PlotLayerDict[1])

            if NetplotWithPlotLayer is not None:

                for NetplotWithPlotLayerError in OrganizedOpenSpaceOverlap.values():

                    ErrorMessageList.append(NetplotWithPlotLayerError)

            #-------------------------------------------------Splay Always With SubPlot Layer--------------------------------------------------------

            SplayWithSubplotlayer=self.SplayWithSubplotLayer(SplayLayerList[1],SubplotsLayerDict[1])

            if SplayWithSubplotlayer is not None:

                for SplayWithSubplotlayerError in SplayWithSubplotlayer.values():

                    ErrorMessageList.append(SplayWithSubplotlayerError)


            #----------------------------------------WaterBodies Touch With Any One-------------------------------------------------------------------

            #If Water bodies layer is present it should be touched with any one of these,netplot, plot ,Compound wall, organised open space, buffer areas.

            WaterBodiesTouchAnyOne=self.WaterBodiesTouchAnyOne(WaterBodiesLayerList[1],NetPlotLayerList[1],PlotLayerDict[1],WallCompoundLayerDict[1],OrganizedOpenSpaceLayerDict[1],BufferZoneLayerDict[1])

            if WaterBodiesTouchAnyOne is not None:

                for WaterBodiesTouchAnyOneError in WaterBodiesTouchAnyOne.values():

                    ErrorMessageList.append(WaterBodiesTouchAnyOneError)


            #---------------------------------------------RoadWidening Touch With Any One------------------------------------------------------------

            #If Road widening layer is present it should be  touched  with any one of these,   netplot, plot ,Compound wall, organised open space, buffer areas

            RoadWideningTouchAnyOne = self.RoadWideningTouchAnyOne(RoadWideningLayerDict[1], NetPlotLayerList[1],PlotLayerDict[1], WallCompoundLayerDict[1],OrganizedOpenSpaceLayerDict[1], BufferZoneLayerDict[1])

            if RoadWideningTouchAnyOne is not None:

                for RoadWideningTouchAnyOneError in RoadWideningTouchAnyOne.values():

                        ErrorMessageList.append(RoadWideningTouchAnyOneError)


            # if plot above 10 acres plot cycletrack should be mandatory

            cycletrackabvtenacre = self.CycletrackabovetenacrsINPlot(PlotLayerDict[1], cycletracklayerList[1])

            if cycletrackabvtenacre is not None:

                for cycletrackabvtenacreError in cycletrackabvtenacre.values():

                    ErrorMessageList.append(cycletrackabvtenacreError)


            accessoryUsedata=AccessoryUseLayerDict[1].values()

            amenitydata=AmenityLayerDict[1].values()

            internalroaddata=InternalRoadLayerDict[1].values()

            bufferzonedata=BufferZoneLayerDict[1].values()

            subplotsdata=SubplotsLayerDict[1].values()

            orgnizedopenspacedata=OrganizedOpenSpaceLayerDict[1].values()

            roadwideningdata=RoadWideningLayerDict[1].values()

            nalawideningdata=NalaWideningLayerDict[1].values()

            watterbodiesdata=WaterBodiesLayerList[1].values()

            Overlapping_layers=self.LayersOverlappingWithEachOther(accessoryUsedata,amenitydata,internalroaddata,bufferzonedata,subplotsdata,orgnizedopenspacedata,roadwideningdata,nalawideningdata,watterbodiesdata)

            if Overlapping_layers is not None or Overlapping_layers!=[]:

                ErrorMessageList.extend(Overlapping_layers)

        except IOError as ioe:

            print(f'Not a DXF file or a generic I/O error.' + str(ioe))

            return ErrorMessageList

        except ezdxf.DXFStructureError as dse:

            print(f'Invalid or corrupted DXF file.' + str(dse))

            return ErrorMessageList

        finally:

            print('Process Complete Sucessfully')

        return ErrorMessageList

#--------------------------------------------------------------Input Of DXF File-----------------------------------------------

#import os

#import ezdxf

#floder="E:/production_code/dxf_files/"

#filename="cycle_track_fff (2).dxf"

#dxf_path=os.path.join(floder,filename)

#read_dxf = ezdxf.readfile(dxf_path)

#msp = read_dxf.modelspace()

#Openlayout=ValidationLayersForOpenLayout()

#OpenLayoutResponce=Openlayout.ValLayersOpenLayout(msp)

#if OpenLayoutResponce!=[] and len(OpenLayoutResponce)>0:

#    print(f'OpenLayout {filename} Error Responce:{OpenLayoutResponce}')

#else:
#    print(f"Did Not Have Any Error in {filename}.")