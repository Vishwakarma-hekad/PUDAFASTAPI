from fastapi.testclient import TestClient
from app import app
client= TestClient(app)

MY_API_KEY="X7kP@92Lm#SecureAPIKey_2026_Vishwa"
USER_NAME="BPConnectUser"
USER_PASSWORD="BPConnect@123"

def test_server():
    headers = {
        "x-api-key": MY_API_KEY,
        "username": USER_NAME,
        "password": USER_PASSWORD,
        "Content-Type": "application/json",
    }

    response=client.get("/",headers=headers)

    assert response.status_code==200
    assert response.json()["status"]=="Server Running..."