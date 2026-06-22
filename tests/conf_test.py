import os

os.environ["DWG_DIR"] = "./tests"
os.environ["DXF_DIR"] = "./tests"
os.environ["PROCESS_DWG_LOGDIR"] = "./logs"
os.environ["JSON_SUMMARY_DIR"] = "./json"
os.environ["SERVER_LOG_DIR"] = "./logs"
os.environ["DWG_PROCESS_LOG_DIR"] = "./logs"
os.environ["ODAFC_EXE_PATH"] = "ODAFileConverter"

os.environ["MY_API_KEY"] = "test_key"
os.environ["USER_NAME"] = "test_user"
os.environ["USER_PASSWORD"] = "test_password"

os.environ["DBAPI_URL"] = "http://localhost"
os.environ["DBAPI_KEY"] = "test"
os.environ["DBAPI_USERNAME"] = "test"
os.environ["DBAPI_PASSWORD"] = "test"
os.environ["API_BASE_URL"] = "http://localhost"