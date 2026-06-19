import os

import ezdxf

from shapely.geometry import Point,Polygon

from shapely.geometry import LineString

import numpy as np

def get_mortgaged_subplots(msp):#folder:str,filename:str):

    returnValueDict=dict()
    print('starting get_mortgaged_subplots')
    if (msp is None):#folder is None or filename is None):
        returnValueDict['code']=99
        msg='Required inputs of msp is missing for method get_building_mortgage_carpetarea. Modelspace ' + str(msp) 
        returnValueDict['error']=msg

        return returnValueDict

    #dxf_path=os.path.join(folder,filename)

    try:

        #read_dxf=ezdxf.readfile(dxf_path)

        #msp=read_dxf.modelspace()

        for mortgage_polygon in msp.query('LWPOLYLINE[layer=="_MortgageArea"]'):

            if mortgage_polygon.closed==True:

                mortgage_id=mortgage_polygon.dxf.handle

                mortgage_polygon_pts=[mp[0:2] for mp in mortgage_polygon.get_points()]

                mortgage_polygon_points=Polygon(mortgage_polygon_pts)

                mortgage_list=[]

                for indivsubplot_entity in msp.query('*[layer=="_IndivSubPlot"]'):

                        if indivsubplot_entity.dxftype()=='TEXT':

                            indivsubplot_attribs=indivsubplot_entity.dxfattribs()

                            text_name= indivsubplot_attribs.get('text')

                            insert_indivsubplot=indivsubplot_attribs.get('insert')

                            indivsubplot_mtext_pts=[insert_indivsubplot[0],insert_indivsubplot[1]]

                            indivsubplot_mtext_points=Point(indivsubplot_mtext_pts)

                            if (mortgage_polygon_points.contains(indivsubplot_mtext_points)==True) or (mortgage_polygon_points.touches(indivsubplot_mtext_points)==True):

                                mortgage_list.append(text_name)

                        elif(indivsubplot_entity.dxftype()=='MTEXT'):

                            indivsubplot_attribs=indivsubplot_entity.dxfattribs()

                            text_name= indivsubplot_entity.plain_text()

                            filter_text=[int(s) for s in text_name.split() if s.isdigit()]

                            insert_indivsubplot=indivsubplot_attribs.get('insert')

                            indivsubplot_mtext_pts=[insert_indivsubplot[0],insert_indivsubplot[1]]

                            indivsubplot_mtext_points=Point(indivsubplot_mtext_pts)

                            if(mortgage_polygon_points.contains(indivsubplot_mtext_points)==True) or (mortgage_polygon_points.touches(indivsubplot_mtext_points)==True):
                                mortgage_list.append(str(filter_text[-1]))
        print('get_mortgaged_subplots completed')
        returnValueDict['code']=0
        returnValueDict['data']=mortgage_list
                

    except IOError as ioe:
        msg=f'Not a DXF file or a generic I/O error.' + str(ioe)
        returnValueDict['code']=99
        returnValueDict['error']=msg
        returnValueDict['data']=[]

        return returnValueDict
    except ezdxf.DXFStructureError as dse :
        msg=f'Invalid or corrupted DXF file.'+ str(dse)
        returnValueDict['code']=99
        returnValueDict['error']=msg
        returnValueDict['data']=[]
        
        return returnValueDict

    return returnValueDict




#path of the filename

#folder=r'E:\python'

#Pass extension - removed inside method

#filename='gone shyam sunder rao.dxf'                   # Here give only filename

#method returns a dict with handle

#response=check_subplot_in_mortgage(folder,filename)

#print('check subplot in mortgage Area:',response)