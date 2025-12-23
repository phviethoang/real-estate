from fastapi import FastAPI, Body, HTTPException
from worker import get_area_district, get_price_district, get_price_per_square_district, get_price_date, get_price_per_square_date, get_name_conversation, update_global_districts
from typing import Any
from auth import User, UserResponse, register_user, login_user, get_chat_by_id, get_chat_history, save_chat_history, users_collection
from manager_gemini import ResearchManager
import asyncio

app = FastAPI()

manager = ResearchManager(use_judge=True)

@app.post("/set_active_province/{province}")
def set_active_province_endpoint(province: str):
    success = update_global_districts(province)
    return {"status": "success" if success else "failed", "province": province}

# ... (Các API get_price giữ nguyên) ...
@app.get("/get_price_by_district/{listing_type}/{estate_type_index}")
def get_price_by_district(estate_type_index: str, listing_type: str):
    districts, avg_prices = get_price_district(estate_type_index, listing_type)
    return {"districts": districts, "avg_prices": avg_prices}

@app.get("/get_price_per_square_by_district/{listing_type}/{estate_type_index}")
def get_price_per_square_by_district(estate_type_index: str, listing_type: str):
    districts, avg_prices_per_square = get_price_per_square_district(estate_type_index, listing_type)
    return {"districts": districts, "avg_prices_per_square": avg_prices_per_square}

@app.get("/get_area_by_district/{listing_type}/{estate_type_index}")
def get_area_by_district(estate_type_index: str, listing_type: str):
    districts, avg_areas = get_area_district(estate_type_index, listing_type)
    return {"districts": districts, "avg_areas": avg_areas}

@app.get("/get_price_by_date/{listing_type}/{estate_type_index}/{selected_district}/{start_date}/{end_date}")
def get_price_by_date(estate_type_index: str, selected_district: str, start_date, end_date, listing_type: str):
    dates, avg_prices = get_price_date(estate_type_index, selected_district, start_date, end_date, listing_type)
    return {"dates": dates, "avg_prices": avg_prices}

@app.get("/get_price_per_square_by_date/{listing_type}/{estate_type_index}/{selected_district}/{start_date}/{end_date}")
def get_price_per_square_by_date(estate_type_index: str, selected_district: str, start_date, end_date, listing_type: str):
    dates, avg_prices_per_square = get_price_per_square_date(estate_type_index, selected_district, start_date, end_date, listing_type)
    return {"dates": dates, "avg_prices_per_square": avg_prices_per_square}


@app.post("/chat/")
async def chat(chats: Any = Body(...)):
    # 1. Lấy thông tin cơ bản
    # chats là danh sách toàn bộ lịch sử gửi từ frontend
    message = chats[-1]["content"]
    chat_id = chats[-1].get("chat_id", None)
    user_id = chats[-1].get("user_id", None)
    
    # 2. Lấy Ký ức dài hạn (Zep Memory)
    memory_context = ""
    try:
        # Kiểm tra manager.client tồn tại để tránh lỗi nếu chưa config Zep
        if chat_id and manager.client:
            memory = await manager.client.memory.get(session_id=chat_id)
            if memory and memory.context:
                memory_context = memory.context
                print(f"💡 [ZEP] Tìm thấy ngữ cảnh: {memory_context[:100]}...")
    except Exception as e:
        print(f"⚠️ [ZEP] Không lấy được memory (có thể do session mới): {e}")
    
    # 3. Xây dựng System Prompt (Kỹ thuật RAG)
    system_instruction = (
        "Bạn là trợ lý ảo bất động sản chuyên nghiệp tại Việt Nam.\n"
        "NHIỆM VỤ: Trả lời câu hỏi mới nhất của người dùng một cách chính xác, ngắn gọn.\n"
        "----------------\n"
        f"KÝ ỨC DÀI HẠN (THAM KHẢO):\n{memory_context}\n"
        "----------------\n"
        "LƯU Ý: Hãy ưu tiên câu hỏi hiện tại, chỉ sử dụng ký ức nếu nó liên quan trực tiếp."
    )
    
    # 4. Tái tạo danh sách tin nhắn để gửi cho Manager
    # Cấu trúc: [System Prompt] + [Lịch sử gần nhất] + [Câu hỏi mới nhất]
    messages_payload = [{"role": "system", "content": system_instruction}]

    if len(chats) > 1:
        messages_payload.extend(chats[-5:-1])
        
    # Thêm câu hỏi hiện tại của user vào cuối
    messages_payload.append({"role": "user", "content": message})
    
    # 5. Gọi Manager xử lý
    # Manager sẽ nhận được list messages đã có System Prompt chứa Memory
    report, answer = await manager.run(messages_payload, user_id, chat_id)

    # 6. Lưu cuộc hội thoại mới vào Zep (Chạy ngầm)
    if chat_id:
        # Tạo cặp câu hỏi - trả lời để lưu
        interaction_to_save = [
            {"role": "user", "content": message},
            {"role": "assistant", "content": answer}
        ]
        # Dùng create_task để không bắt User phải chờ bước lưu này
        asyncio.create_task(manager.add_memory(interaction_to_save, chat_id))
    
    # 7. Trả kết quả về Frontend
    return {
        "real_estate_findings": report.real_estate_findings, 
        "analytics_and_advice": report.analytics_and_advice, 
        "follow_up_questions": report.follow_up_questions
    }

@app.post("/chat/name_conversation")
async def get_name(messages: Any = Body(...)):
    name = await get_name_conversation(messages)
    return name

@app.post("/register")
async def register(user: User):
    result = register_user(user)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    else:
        if manager.client:
            try:
                await manager.client.user.add(
                    user_id=result["user_id"],
                    email=user.email,
                    first_name=user.name
                )
            except Exception as e:
                print(f"Lỗi tạo Zep User: {e}")
    return result

@app.post("/login")
def login(email: str = Body(...), password: str = Body(...)):
    print("=== Backend received login request ===")
    print(f"Email: {email}")
    user = login_user(email, password)
    if not user:
        print("Login failed")
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không đúng")
    print("Login successful")
    return user

# API endpoints cho chat history (Lưu vào MongoDB - OK)
@app.post("/chat/save")
async def save_chat(
    email: str = Body(...),
    chat_id: str = Body(...),
    chat_title: str = Body(...),
    messages: list = Body(...)
):
    result = save_chat_history(email, chat_id, chat_title, messages)
    return result

@app.get("/chat/history/{email}")
def get_user_chat_history(email: str):
    chats = get_chat_history(email)
    return {"chats": chats}

@app.get("/chat/{chat_id}")
def get_chat(chat_id: str):
    chat = get_chat_by_id(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Không tìm thấy cuộc hội thoại")
    return chat