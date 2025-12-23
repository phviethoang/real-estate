from typing import List, Dict, Optional, Any
import requests
import streamlit as st


BASE_URL = "http://localhost:8000"
def get_response(messages: Any) -> Dict:
    endpoint = f"{BASE_URL}/chat/"
    headers = {"Content-Type": "application/json"}

    # Thêm chat_id vào message cuối cùng nếu có
    if messages and isinstance(messages, list):
        last_message = messages[-1]
        if isinstance(last_message, dict) and "chat_id" not in last_message:
            last_message["chat_id"] = st.session_state.current_chat_id

    try:
        response = requests.post(
            endpoint,
            json=messages,
            headers=headers
        )
        response.raise_for_status()
        for message in messages:
            if isinstance(message, dict) and "chat_id" in message:
                message.pop("chat_id")

            if isinstance(message, dict) and "user_id" in message:
                message.pop("user_id")

        return response.json()

    except requests.exceptions.HTTPError as http_err:
        raise ValueError(f"HTTP error occurred: {http_err} - Status code: {response.status_code}")
    except requests.exceptions.ConnectionError:
        raise ValueError("Failed to connect to the server. Please check your network or the server status.")
    except requests.exceptions.Timeout:
        raise ValueError("Request timed out. Please try again later.")
    except requests.exceptions.JSONDecodeError:
        raise ValueError("Invalid JSON response from server.")
    except requests.exceptions.RequestException as req_err:
        raise ValueError(f"An error occurred while making the request: {req_err}")

def get_conversation_name(messages: Any) -> Dict:
    endpoint = f"{BASE_URL}/chat/name_conversation"
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(
            endpoint,
            json=messages,
            headers=headers
        )
        response.raise_for_status()

        return str(response.json())

    except requests.exceptions.HTTPError as http_err:
        raise ValueError(f"HTTP error occurred: {http_err} - Status code: {response.status_code}")
    except requests.exceptions.ConnectionError:
        raise ValueError("Failed to connect to the server. Please check your network or the server status.")
    except requests.exceptions.Timeout:
        raise ValueError("Request timed out. Please try again later.")
    except requests.exceptions.JSONDecodeError:
        raise ValueError("Invalid JSON response from server.")
    except requests.exceptions.RequestException as req_err:
        raise ValueError(f"An error occurred while making the request: {req_err}")

def save_chat_history_api(email: str, chat_id: str, chat_title: str, messages: list) -> Dict:
    try:
        response = requests.post(
            f"{BASE_URL}/chat/save",
            json={
                "email": email,
                "chat_id": chat_id,
                "chat_title": chat_title,
                "messages": messages
            }
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": "Có lỗi xảy ra khi lưu lịch sử chat"}

def get_chat_history_api(email: str) -> List[Dict]:
    try:
        response = requests.get(f"{BASE_URL}/chat/history/{email}")
        response.raise_for_status()
        return response.json()["chats"]
    except requests.exceptions.RequestException as e:
        return []

def get_chat_by_id_api(chat_id: str) -> Optional[Dict]:
    try:
        response = requests.get(f"{BASE_URL}/chat/{chat_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return None