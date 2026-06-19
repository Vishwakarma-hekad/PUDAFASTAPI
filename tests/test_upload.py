from fastapi.testclient import TestClient
from app import app

client = TestClient(app)
MY_API_KEY="X7kP@92Lm#SecureAPIKey_2026_Vishwa"
USER_NAME="BPConnectUser"
USER_PASSWORD="BPConnect@123"

HEADERS = {
    "x-api-key": MY_API_KEY,
    "username": USER_NAME,
    "password": USER_PASSWORD
}

def test_real_dwg_upload():

    with open("tests/Jaswitha West Kondapur.dwg", "rb") as f:

        response = client.post(
            "/api/drawingrequest/create",
            headers=HEADERS,
            files={
                "dwgfile": (
                    "Jaswitha West Kondapur.dwg",
                    f,
                    "application/octet-stream"
                )
            },
            data={
                    "layout": "Building",
                    "subtype": "STANDALONE",
                    "ulb": "Hyderabad",
                    "purposecode": "A-4",
                    "applicationFormId": "3459",
                    "runOnlyCombinedUtil": "True",
                    "user_name":"tsbpass-user1",
                }
        )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "Submitted"
    assert "ReferenceId" in data

# def test_invalid_extension():
#
#     files = {
#         "dwgfile": (
#             "test.txt",
#             b"dummy content",
#             "text/plain"
#         )
#     }
#
#     data = {
#         "layout": "Building",
#         "subtype": "STANDALONE",
#         "ulb": "Hyderabad",
#         "purposecode": "A-4",
#         "applicationFormId": "3459",
#         "runOnlyCombinedUtil": "True",
#         "user_name":"tsbpass-user1",
#     }
#
#     response = client.post(
#         "/api/drawingrequest/create",
#         headers=HEADERS,
#         files=files,
#         data=data
#     )
#
#     assert response.status_code == 400