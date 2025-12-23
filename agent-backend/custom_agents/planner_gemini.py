from __future__ import annotations
import os
import asyncio
import json
from typing import Literal, List
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai

# Load API Key
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY") # Vẫn dùng biến này chứa Key Gemini như cũ
if not api_key:
    # Fallback cho trường hợp biến môi trường đặt tên khác
    api_key = os.getenv("GOOGLE_API_KEY")

genai.configure(api_key=api_key)

# 1. Define the structured output model (GIỮ NGUYÊN)
class ToolSelection(BaseModel):
    tools: list[Literal["search_db", "search_web"]]

# 2. Define the prompt (GIỮ NGUYÊN PROMPT GỐC CỦA TÁC GIẢ)
PROMPT = """You are a helpful real estate assistant. Given a user query in Vietnamese, choose from 2 tools based on their descriptions:
            - search_db: Retrieves real estate listings from the database relevant to the query.
            - search_web: Gathers general real estate information, such as price forecasts or project updates, based on the query.
            Select the appropriate tool(s) and return them as a list. Always choose at least 1 tool. Return only the list of tool names in the structured output format.
            You cannot and must not use or call the WebSearch tool, only return the tool names as specified.

            Examples:
            Input: Cho tôi các bài đăng chung cư mới nhất tại quận Thanh Xuân?
            Output: ["search_db"]

            Input: Tình hình dự án Vinhomes Smart City như thế nào rồi?
            Output: ["search_web"]

            Input: Lấy cho tôi các bài đăng nhà riêng có 2 phòng ngủ tại quận Thanh Xuân. Dự đoán giá nhà riêng tại khu vực Thanh Xuân trong 6 tháng tới.
            Output: ["search_db", "search_web"]
"""

# 3. CLASS PLANNER MỚI (DÙNG GEMINI NATIVE)
class GeminiPlannerAgent:
    def __init__(self, model_name="models/gemini-2.5-flash"):
        # Dùng model Pro cho Planner để đảm bảo logic tốt nhất
        self.model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=PROMPT,
            # Cấu hình ép kiểu JSON Output theo Schema của Pydantic
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=ToolSelection
            )
        )

    async def run(self, query: str) -> ToolSelection:
        """
        Hàm thực thi chính, trả về object ToolSelection
        """
        try:
            # Chạy async để không chặn luồng chính
            response = await self.model.generate_content_async(query)
            
            # Parse JSON từ Gemini thành Pydantic Model
            # Gemini trả về text JSON, ta load nó vào class ToolSelection
            result = ToolSelection.model_validate_json(response.text)
            return result
            
        except Exception as e:
            print(f"❌ Lỗi Planner Agent: {e}")
            # Fallback an toàn: Mặc định tìm kiếm Database nếu lỗi
            return ToolSelection(tools=["search_db"])

# Khởi tạo Agent (để các file khác import)
planner_agent = GeminiPlannerAgent()

# --- MAIN TEST ---
async def main():
    print("⏳ Testing Planner Agent")
    
    query = "Cho tôi các bài đăng nhà phố mới nhất tại quận Hoàn Kiếm có 3 tầng. Cho tôi thông tin về diện tích trung bình của các căn hộ Eco Park"
    print(f"User Query: {query}")
    
    # Gọi hàm run trực tiếp (không qua Runner nữa)
    result = await planner_agent.run(query)
    
    print("\n✅ Kết quả (JSON):")
    print(result.model_dump_json(indent=2))
    
    print("\n✅ Truy cập từng tool:")
    if result.tools:
        for tool in result.tools:
            print(f"- {tool}")

if __name__ == "__main__":
    asyncio.run(main())