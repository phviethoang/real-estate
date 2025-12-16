from pymongo import MongoClient
import bcrypt
from typing import Optional, Dict, List
from pydantic import BaseModel

class User(BaseModel):
    name: str
    email: str
    password: str

class UserResponse(BaseModel):
    name: str
    email: str

# Kết nối MongoDB
client = MongoClient("mongodb+srv://phucnh0703:hoangphuc0703@cluster0.8tjiz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["agentbds"]
users_collection = db["account"]

# Collection cho chat history
chat_history_collection = db["chathistory"]

def hash_password(password: str) -> str:
    """Mã hóa mật khẩu sử dụng bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Xác thực mật khẩu"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def register_user(user: User) -> Dict:
    """Đăng ký người dùng mới"""
    # Kiểm tra email đã tồn tại chưa
    if users_collection.find_one({"email": user.email}):
        return {"error": "Email đã tồn tại"}
    
    # Mã hóa mật khẩu
    hashed_password = hash_password(user.password)
    
    # Tạo user mới
    user_dict = user.dict()
    user_dict["password"] = hashed_password
    
    # Lưu vào database
    result = users_collection.insert_one(user_dict)
    
    return {"message": "Đăng ký thành công", "user_id": str(result.inserted_id)}

def login_user(email: str, password: str) -> Optional[UserResponse]:
    """Đăng nhập người dùng"""
    user = users_collection.find_one({"email": email})
    
    if not user:
        return None
    
    if not verify_password(password, user["password"]):
        return None
    
    return UserResponse(name=user["name"], email=user["email"])

def save_chat_history(email: str, chat_id: str, chat_title: str, messages: list) -> Dict:
    """Lưu hoặc cập nhật lịch sử chat"""
    chat_data = {
        "email": email,
        "chat_id": chat_id,
        "chat_title": chat_title,
        "messages": messages
    }
    
    # Kiểm tra xem chat đã tồn tại chưa
    existing_chat = chat_history_collection.find_one({"chat_id": chat_id})
    
    if existing_chat:
        # Cập nhật chat hiện có
        chat_history_collection.update_one(
            {"chat_id": chat_id},
            {"$set": chat_data}
        )
        return {"message": "Cập nhật lịch sử chat thành công", "is_new": False}
    else:
        # Tạo chat mới
        chat_history_collection.insert_one(chat_data)
        return {"message": "Lưu lịch sử chat thành công", "is_new": True}

def get_chat_history(email: str) -> List[Dict]:
    """Lấy lịch sử chat của người dùng"""
    chats = list(chat_history_collection.find(
        {"email": email},
        {"_id": 0, "email": 0}  # Loại bỏ _id và email từ kết quả
    ))
    return chats[::-1]

def get_chat_by_id(chat_id: str) -> Optional[Dict]:
    """Lấy thông tin chi tiết của một cuộc chat"""
    chat = chat_history_collection.find_one(
        {"chat_id": chat_id},
        {"_id": 0, "email": 0}  # Loại bỏ _id và email từ kết quả
    )
    return chat 