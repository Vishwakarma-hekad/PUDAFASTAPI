from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):

    DWG_DIR:str
    DXF_DIR:str
    PROCESS_DWG_LOGDIR:str
    JSON_SUMMARY_DIR:str
    SERVER_LOG_DIR:str
    DWG_PROCESS_LOG_DIR:str
    ODAFC_EXE_PATH:str

    MY_API_KEY:str
    USER_NAME:str
    USER_PASSWORD:str

    DBAPI_URL:str
    DBAPI_KEY:str
    DBAPI_USERNAME:str
    DBAPI_PASSWORD:str

    API_BASE_URL:str

    class Config:

        env_file= ".env"
        case_sensitive= True

settings= Settings()