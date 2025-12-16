from  fastapi import FastAPI, Body, HTTPException
from worker import get_area_district, get_price_district, get_price_per_square_district, get_price_date, get_price_per_square_date, get_name_conversation
from typing import Any
from auth import User, UserResponse, register_user, login_user, get_chat_by_id,get_chat_history,save_chat_history, users_collection
from manager import ResearchManager
app = FastAPI()
manager = ResearchManager()

@app.get("/get_price_by_district/{estate_type_index}")
def get_price_by_district(estate_type_index: str):
    districts, avg_prices = get_price_district(estate_type_index)
    return {"districts": districts, "avg_prices": avg_prices}

@app.get("/get_price_per_square_by_district/{estate_type_index}")
def get_price_per_square_by_district(estate_type_index: str):
    districts, avg_prices_per_square = get_price_per_square_district(estate_type_index)
    return {"districts": districts, "avg_prices_per_square": avg_prices_per_square}

@app.get("/get_area_by_district/{estate_type_index}")
def get_area_by_district(estate_type_index: str):
    districts, avg_areas = get_area_district(estate_type_index)
    return {"districts": districts, "avg_areas": avg_areas}

@app.get("/get_price_by_date/{estate_type_index}/{selected_district}")
def get_price_by_date(estate_type_index: str, selected_district: str):
    dates, avg_prices = get_price_date(estate_type_index, selected_district)
    return {"dates": dates, "avg_prices": avg_prices}

@app.get("/get_price_per_square_by_date/{estate_type_index}/{selected_district}")
def get_price_per_square_by_date(estate_type_index: str, selected_district: str):
    dates, avg_prices_per_square = get_price_per_square_date(estate_type_index, selected_district)
    return {"dates": dates, "avg_prices_per_square": avg_prices_per_square}

@app.post("/chat/")
async def chat(chats: Any = Body(...)):
    message = chats[-1]["content"]
    chat_id = chats[-1].get("chat_id", None)
    user_id = chats[-1].get("user_id", None)
    # print(message)
    
    # Lấy memory context nếu có chat_id
    memory_context = ""
    try:
        if chat_id:
            memory = await manager.client.memory.get(chat_id)
            # graph = await manager.client.graph.search(user_id=user_id, query=message)
            # print(f"Graph: {graph}")
            if memory:
                memory_context = memory.context
                with open("note.txt", "w", encoding="utf-8") as f:
                    f.write((str(memory_context)))
    except Exception as e:
        print(f"Đã xảy ra lỗi: {e}")
    
    # Tạo system prompt với memory context và chat history
    system_prompt = f"You are a helpful real estate agents system. Answer the question based on query, previous messages and long term memories. \nMemories:\n{memory_context}."
    # print(system_prompt)
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(chats[-5:-1])
    messages.append({"role": "user", "content": message})
    report, answer = await manager.run(messages, user_id, chat_id)
    add_assistant_response = report.analytics_and_advice
    final_messages=[]
    final_messages.append({"role": "user", "content": message})
    final_messages.append({"role": "assistant", "content": add_assistant_response})
    if chat_id:
        await manager.add_memory(final_messages, chat_id)
    
    return {"real_estate_findings": report.real_estate_findings, "analytics_and_advice": report.analytics_and_advice, "follow_up_questions": report.follow_up_questions}

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
        # Thêm user vào Zep
        await manager.client.user.add(
            user_id=result["user_id"],
            email=user.email,
            first_name=user.name
        )
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

# API endpoints cho chat history
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
