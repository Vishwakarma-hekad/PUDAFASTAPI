import os
import ezdxf

def convertListToStr(inputList:list, delimeter:str=";"):

    returnValue=""

    if (inputList is None or len(inputList) == 0  ):
        return returnValue

    for itr in inputList :
        if (str(itr) == '--'):
            continue
        else:
            returnValue += str(itr) + delimeter

    return returnValue

def analyzeDrawing(folder:str,filename:str):

    returnValueDict={}

    resultsList=[]

    if (folder is None or filename is None):

        return returnValueDict

    dxf_path=os.path.join(folder,filename)

    try:

        read_dxf=ezdxf.readfile(dxf_path)

        print('read file')

        msp=read_dxf.modelspace()
        return analyzeDrawingMsp(msp)

    except IOError:

            print(f'Not a DXF file or a generic I/O error.')
            return returnValueDict

    except ezdxf.DXFStructureError:

            print(f'Invalid or corrupted DXF file.')
            return returnValueDict

def analyzeDrawingMsp(msp):

    returnValueDict={}

    if (msp is None):

        return returnValueDict

    try:


        group=msp.groupby(dxfattrib='layer')

        print('group',len(group))

        
        for layerName,entities in group.items():

            returnValueDict[layerName]=len(entities)


    except IOError:

            print(f'Not a DXF file or a generic I/O error.')
            return returnValueDict

    except ezdxf.DXFStructureError:

            print(f'Invalid or corrupted DXF file.')
            return returnValueDict

    return returnValueDict