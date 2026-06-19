from fastapi import FastAPI,Form,File, UploadFile, Request, HTTPException,Depends,BackgroundTasks
from fastapi.concurrency import run_in_threadpool
from typing import Optional
from starlette.status import HTTP_401_UNAUTHORIZED
from digit_base import LayerMaster
import os
from starlette.responses import JSONResponse
from starlette import status
from config import settings
import uuid
import tempfile
from logging_config import get_server_logger, get_request_logger, close_request_logger, set_request_logger
import shutil
import json
import traceback
from process_file_new import processPlanBasedOnType
import sys
from timeit import default_timer as timer
from DB_API import send_building_data
from datetime import datetime
from DWG2DXF import convertDWGUtil_orig
from concurrent.futures import ThreadPoolExecutor
import asyncio

file_processor_pool = ThreadPoolExecutor(max_workers=4)

server_logger=get_server_logger()

app=FastAPI(title="BPConnectAPI")

os.makedirs(settings.DWG_DIR,exist_ok=True)
os.makedirs(settings.DXF_DIR,exist_ok=True)
os.makedirs(settings.JSON_SUMMARY_DIR, exist_ok=True)

PORT_BP_MAP = {
    8000: "BP1",
    8001: "BP2",
    8002: "BP3",
    8003: "BP4",
    8004: "BP5",
    8005: "BP6",
    8006: "BP7",
    8007: "BP8",
    8008: "BP9",
    8009: "BP10",
}

Status_Dict={}


def verify_headers(request: Request):
    api_key = request.headers.get("x-api-key")
    username = request.headers.get("username")
    password = request.headers.get("password")

    if not api_key or not username or not password:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Missing required authentication headers"
        )

    if (api_key != settings.MY_API_KEY or username != settings.USER_NAME
            or password != settings.USER_PASSWORD):
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid API key or credentials"
        )
    return True

@app.get("/")
async def test(authenticated: bool = Depends(verify_headers)):
    return {"status":"Server Running..."}

async def process_file(request_time, startTimer, applicationFormID, reference_id, portName, Dwg_Dir, Dxf_Dir,file_name,request_params):
    req_logger = get_request_logger(reference_id)

    req_logger.info(f"=== Request Started: {reference_id} ===")
    req_logger.info(f"File: {file_name}, AppID: {applicationFormID}")
    req_time_stamp = datetime.strptime(request_time, "%Y-%m-%d %H:%M:%S")
    status_dict = {
        "ReferenceId": reference_id,
        "Status": "Started",
        "StepName": "Initializing",
        "Progress": 0,
        "Executed_Time":0,
        "Estimated_Remaining_Time":0

    }
    results = {
        "ReferenceId": reference_id,
        "applicationFormId": applicationFormID,
        "serverName": portName,
        "code": "Failed",
        "error_msg": "",
        "csvReport": file_name.replace(".dxf", ".csv"),
        "jsonReport": file_name.replace(".dxf", ".json"),
        "layout": request_params.get("layout", ""),
        "reportExtract": []
    }

    try:
        req_logger.info(f"{file_name} File Processing started...")

        def _run_in_thread():
            set_request_logger(req_logger)  # ← must be inside thread
            try:
                return processPlanBasedOnType(
                    reference_id, Dwg_Dir, Dxf_Dir,
                    file_name, request_params, status_dict, req_time_stamp
                )
            finally:
                set_request_logger(None)  # ← clean up after done

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(file_processor_pool, _run_in_thread)

        # loop = asyncio.get_event_loop()
        # response = await loop.run_in_executor(file_processor_pool,processPlanBasedOnType,reference_id, Dwg_Dir, Dxf_Dir,
        #                                  file_name, request_params,status_dict,req_time_stamp)
        # print('====res', response)
        if (response.get('responseCode', -1) == 0):
            results['code'] = 'Completed'

            results['reportExtract'] =response.get("dwgExtract",[])

        else:
            errorList = response.get('errors', 'N/A')
            req_logger.error(errorList)
            endTimer = timer()

            errorStr = errorList.replace("\n","|")

            results['code'] = 'Failed'

            timetakenstr = str(round(endTimer - startTimer, 2)) + " sec "

            results['timetaken'] = timetakenstr

            results['error_msg'] = errorStr[:errorStr.find('exception')]

            req_logger.warning(f"Failed to saved JSON File")

    except:

        req_logger.error('Exception occured in processPlanBasedOnType ')
        ex_type, ex_value, ex_traceback = sys.exc_info()

        # Extract unformatter stack traces as tuples
        trace_back = traceback.extract_tb(ex_traceback)

        # Format stacktrace
        stack_trace = list()

        for trace in trace_back:
            errorDict = dict()
            fileName = trace[0]
            fileName = fileName.strip()
            stripFileName = fileName[fileName.rindex("\\") + 1:-3]
            errorDict['File'] = stripFileName
            errorDict['Line'] = trace[1]
            errorDict['Func.Name'] = trace[2]
            errorDict['Statement'] = trace[3]
            stack_trace.append(errorDict)
            # stack_trace.append("File : %s , Line : %d, Func.Name : %s, Statement : %s" % (stripFileName, trace[1], trace[2], trace[3]))

        req_logger.exception("Exception type : %s " % ex_type.__name__)
        req_logger.error("Exception message : %s" % ex_value)
        req_logger.error("Stack trace : %s" % stack_trace)

        respDict = dict()
        respDict['ReferenceId'] = reference_id
        respDict['requestTimeStamp'] = request_time
        respDict['responseTimestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # "%d/%m/%Y %H:%M:%S")
        respDict['code'] = "FAILED"
        respDict['error_msg'] = "Fatal error processing the request."
        return JSONResponse(respDict, status_code=400)

    finally:
        now = datetime.now()
        results["requestTimeStamp"] = req_time_stamp.strftime("%Y-%m-%d %H:%M:%S")
        results["responseTimestamp"] = now.strftime("%Y-%m-%d %H:%M:%S")
        results["svgfile"] = "N/A"
        results["timetaken"] = f"{(now - req_time_stamp).total_seconds():.2f} sec"

        try:

            # Save JSON
            json_path = os.path.join(settings.JSON_SUMMARY_DIR, file_name.replace(".dxf", ".json"))

            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=4)

            req_logger.info("JSON saved at %s", json_path)

            response = await run_in_threadpool(send_building_data,
                payload=results,
                api_key=settings.DBAPI_KEY,
                username=settings.DBAPI_USERNAME,
                password=settings.DBAPI_PASSWORD)
            req_logger.info("DB API RES: %s", response)

        except Exception as e:

            # status_dict["Status"] = "Failed"
            # status_dict["StepName"] = "Database saving failed"
            # update_status(ref_id, status_dict)
            req_logger.exception("DB API failed: %s", e)

        finally:

            req_logger.info(f"=== Request Finished: {reference_id} | Time: {results['timetaken']} ===")

            close_request_logger(reference_id)

def create_response(application_id,reference_id,file_name,status,message):

    respDict = dict()
    respDict['ApplicationFormId'] = application_id
    respDict['ReferenceId'] = reference_id
    respDict['input'] = file_name
    respDict['status'] = status
    respDict['Detail'] = message

    return respDict

@app.post("/api/drawingrequest/create",response_class=JSONResponse)
async def upload_file(request:Request,
        background_task: BackgroundTasks,
        authenticated: bool = Depends(verify_headers),
        layout: str = Form("N/A"),
        ulb :Optional[str] = Form(None),
        subtype:str = Form("N/A"),
        purposecode: str = Form("N/A"),
        user_name: str = Form("N/A"),
        location: str = Form("N/A"),
        sub_location: str = Form("N/A"),
        total_plotArea: str = Form("N/A"),
        is_underground_drain: str = Form("N/A"),
        deslugging_years: str = Form("N/A"),
        number_occupants: str = Form("N/A"),
        roadwiden_concession_setback: str = Form("N/A"),
        roadwiden_concession_additionalfloors: str = Form("N/A"),
        nala_concession_setback: str = Form("N/A"),
        nala_concession_additionalfloors: str = Form("N/A"),
        additional_mortgage_nala: str = Form("N/A"),
        utilize_tdr: str = Form("N/A"),
        tdr_no_floors: str = Form("N/A"),
        apply_for: str = Form("N/A"),
        authority: str = Form("N/A"),
        dwgfile: UploadFile = File(None),
        type_of_development: str = Form("N/A"),
        block_details: str = Form("[]"),
        use: str = Form("N/A"),
        subuse: str = Form("N/A"),
        applicationFormId: str = Form("N/A"),
        generate_svg: str = Form("false"),
        isGatedCommunity: bool = Form(False),
        runOnlyCombinedUtil: bool = Form(False),
        typeofplan:str= Form("PlanScrutiny"),
        ):


    ref_id = hex(uuid.uuid4().time)[2:-1] + datetime.now().strftime("%d")
    file_name=dwgfile.filename if dwgfile else ""
    server_logger.info(f"Request getting APP ID:{applicationFormId} REF ID:{ref_id} FileName:{file_name}")
    request_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    portName=PORT_BP_MAP.get(request.url.port,str(request.url.port))

    if not (user_name or dwgfile):

        msg = "Bad Request. username or dwgfile required parameters are missing."
        server_logger.error(msg)
        return JSONResponse(content=create_response(applicationFormId,ref_id,file_name
                            ,"Failed",msg),
                            status_code=status.HTTP_400_BAD_REQUEST)

    temp_filename= os.path.join(tempfile.gettempdir(),f"{ref_id}.dwg")
    try:

        if not dwgfile.filename.lower().endswith(".dwg"):

            msg = "File Extension not supported yet. Valid drawing extensions should be 'dwg'"
            server_logger(msg)
            return JSONResponse(content=create_response(applicationFormId,ref_id,file_name,"FAILED",msg),
                                status_code=status.HTTP_400_BAD_REQUEST)

        error_msg = ""
        if (layout not in LayerMaster.PLAN_CATEGORY_LIST.value):
            invalidLayout = True
            error_msg += ", Layout (Given): " + layout + " allowed values: " + str(
                LayerMaster.PLAN_CATEGORY_LIST.value.keys()).replace('dict_keys', '') + " "
        else:
            invalidLayout = False

        if (subtype not in LayerMaster.BUILDING_CATEGORY.value):
            invalidSubtype = True
            error_msg += ", Subtype (Given): " + subtype + " allowed values: " + str(
                LayerMaster.BUILDING_CATEGORY.value).replace('dict_keys', '') + " "
        else:
            invalidSubtype = False

        if (purposecode not in LayerMaster.PURPOSE_CODE_DESC_MAP.value.keys()):
            invalidPurposeCode = True
            error_msg += ", PurposeCode (Given): " + purposecode + " allowed values: " + str(
                LayerMaster.PURPOSE_CODE_DESC_MAP.value.keys()).replace('dict_keys', '') + ""
        else:
            invalidPurposeCode = False

        if (invalidPurposeCode or invalidLayout or invalidSubtype):
            msg = "One or more parameters have invalid Options." + error_msg
            server_logger.error(msg)
            return JSONResponse(content=create_response(applicationFormId,ref_id,file_name, "Failed", msg),
                                status_code=status.HTTP_400_BAD_REQUEST)

        file_basename = os.path.splitext(dwgfile.filename)[0].replace(" ", "_")
        file_name = f"{ref_id}-{file_basename}.dwg"

        saved_dwg_path = os.path.join(settings.DWG_DIR, file_name)

        def save_file(dwgfile,saved_dwg_path):
            # Save DWG file directly (streaming, memory-safe)
            with open(saved_dwg_path, "wb") as buffer:
                shutil.copyfileobj(dwgfile.file, buffer)

        await run_in_threadpool(save_file, dwgfile, saved_dwg_path)

        requestParams = dict()
        requestParams["ReportGeneratedDateTime"]="-"
        requestParams['additional_mortgage_nala'] = additional_mortgage_nala
        requestParams['applicationFormId'] = applicationFormId
        requestParams['apply_for'] = apply_for
        requestParams['authority'] = authority
        requestParams['block_details'] = "[]"
        requestParams['deslugging_years'] = deslugging_years
        requestParams['drawing_filename']=file_name
        requestParams['generate_svg'] = generate_svg
        requestParams['isGatedCommunity'] =  "True" if isGatedCommunity else "False"
        requestParams['is_underground_drain'] = is_underground_drain
        requestParams['layout'] = layout
        requestParams['location'] = location
        requestParams['nala_concession_additionalfloors'] = nala_concession_additionalfloors
        requestParams['nala_concession_setback'] = nala_concession_setback
        requestParams['number_occupants'] = number_occupants
        requestParams['purposecode'] = purposecode
        requestParams['purposedesc'] = "N/A"
        requestParams['referenceId'] = ref_id
        requestParams['roadwiden_concession_additionalfloors'] = roadwiden_concession_additionalfloors
        requestParams['roadwiden_concession_setback'] = roadwiden_concession_setback
        requestParams['runOnlyCombinedUtil'] = "True" if runOnlyCombinedUtil else "False"
        requestParams['sub_location'] = sub_location
        requestParams['subtype'] = subtype
        requestParams['subuse'] = subuse
        requestParams['tdr_no_floors'] = tdr_no_floors
        requestParams['total_plotArea'] = total_plotArea
        requestParams['type_of_development'] = type_of_development
        requestParams['typeofplan'] = typeofplan
        requestParams['ulb'] = typeofplan
        requestParams['use'] = use
        requestParams['username'] = user_name
        requestParams['utilize_tdr'] = utilize_tdr

        # converted_status = await convertDWGUtil_orig(settings.DWG_DIR, file_name, settings.DXF_DIR)

        loop = asyncio.get_event_loop()
        converted_status = await loop.run_in_executor(
            file_processor_pool,
            lambda: asyncio.run(convertDWGUtil_orig(settings.DWG_DIR, file_name, settings.DXF_DIR))
        )
        if converted_status.get("Status") != "Success":
            responseTimestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            msg = "DWG to DXF conversion failed."
            server_logger.error(msg)
            return JSONResponse(
                content=create_response(ref_id, file_name, request_time, "FAILED", responseTimestamp, msg),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        dxf_filename = converted_status.get("FileName")

        startTimer = timer()

        background_task.add_task(process_file,request_time, startTimer,applicationFormId,ref_id,portName,settings.DWG_DIR,
                                  settings.DXF_DIR,dxf_filename,requestParams)

        msg= "File received and processing started."

        server_logger.info(msg)

        server_logger.info(f"Request User Input Form Details Sent:\n{requestParams}")

        return JSONResponse(content=create_response(applicationFormId,ref_id,file_name, "Submitted", msg),
                            status_code=status.HTTP_200_OK)

    except Exception as e:

        msg= "Fatal error processing the request "
        server_logger.error(msg)
        server_logger.exception(f"Unexpected error while processing file RefId={ref_id}:\n {e} ")
        return JSONResponse(content=create_response(applicationFormId,ref_id,file_name , "Failed", msg),
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    finally:

        if os.path.exists(temp_filename):

            try:
                os.remove(temp_filename)
                server_logger.info(f"Deleted temporary file: {temp_filename}")

            except Exception as Cleanup_error:
                server_logger.warning(f"Could not delete temp file: {Cleanup_error}")