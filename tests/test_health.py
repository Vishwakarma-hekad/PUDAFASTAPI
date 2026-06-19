from fastapi.testclient import TestClient
from app import app
from config import settings
client= TestClient(app)

def test_server():
    headers = {
        "x-api-key": settings.MY_API_KEY,
        "username": settings.USER_NAME,
        "password": settings.USER_PASSWORD,
        "Content-Type": "application/json",
    }

    response=client.get("/",headers=headers)

    assert response.status_code==200
    assert response.json()["status"]=="Server Running..."