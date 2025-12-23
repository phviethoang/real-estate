
import re
import requests
from typing import List, Dict, Optional

BASE_URL = "http://localhost:8000"

def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def register_api(name: str, email: str, password: str) -> Dict:
    try:
        response = requests.post(
            f"{BASE_URL}/register",
            json={
                "name": name,
                "email": email,
                "password": password
            }
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if e.response is not None and e.response.status_code == 400:
            return {"error": e.response.json()["detail"]}
        return {"error": "Có lỗi xảy ra khi đăng ký"}

def login_api(email: str, password: str) -> Optional[Dict]:
    try:
        response = requests.post(
            f"{BASE_URL}/login",
            json={
                "email": email,
                "password": password
            }
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if e.response is not None and e.response.status_code == 401:
            return None
        return None