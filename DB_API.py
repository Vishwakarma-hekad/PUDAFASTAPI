import time
import httpx
from typing import Dict, Any, Optional
from logging_config import get_current_logger
from config import settings

class APIClientError(Exception):
    """Custom exception for API failures."""
    pass

def send_building_data(
    payload: Dict[str, Any],
    api_key: str,
    username: str,
    password: str,
    timeout: int = 120,
    retries: int = 3
) -> Optional[Dict[str, Any]]:

    headers = {
        "x-api-key": api_key,
        "username": username,
        "password": password,
        "Content-Type": "application/json",
    }

    last_error = None

    for attempt in range(1, retries + 1):
        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.post(settings.DBAPI_URL, headers=headers, json=payload)

            response.raise_for_status()

            get_current_logger().info(f"DB API Success (Attempt {attempt}): {response.status_code}")
            return response.json()

        except httpx.TimeoutException as exc:
            last_error = exc
            get_current_logger().warning(f"Timeout on attempt {attempt}/{retries}")

        except httpx.HTTPStatusError as exc:
            last_error = exc
            status = exc.response.status_code

            if status >= 500:
                # Retry on server errors
                get_current_logger().warning(f"Server error {status} on attempt {attempt}/{retries}")
            else:
                # Don't retry on client errors (4xx)
                get_current_logger().error(f"Client error {status}: {exc.response.text}")
                raise APIClientError(f"HTTP {status}: {exc.response.text}")

        except httpx.RequestError as exc:
            last_error = exc
            get_current_logger().error(f"Request error on attempt {attempt}/{retries}: {str(exc)}")

        except Exception as exc:
            get_current_logger().exception("Unexpected error in send_building_data")
            raise APIClientError(str(exc))

        # Backoff before retry (skip after last attempt)
        if attempt < retries:
            sleep_time = 2 * attempt  # 2s, 4s
            get_current_logger().info(f"Retrying in {sleep_time}s...")
            time.sleep(sleep_time)

    raise APIClientError(f"Failed after {retries} retries. Last error: {last_error}")