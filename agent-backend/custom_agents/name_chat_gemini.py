from __future__ import annotations
import os
import asyncio
from dotenv import load_dotenv
import google.generativeai as genai

# Load API Key
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
genai.configure(api_key=api_key)

INSTRUCTIONS = """
You are a conversation title generator. 
Given a full conversation between a user and an assistant, generate a clear, concise, and relevant title that summarizes the main topic or purpose of the conversation. 
The title should be short (3 to 8 words), descriptive, and specific enough to distinguish the conversation from others. Avoid generic titles like "Chat" or "Help Request." Focus on what the conversation is truly about. 
Return only the title—no explanation, no punctuation beyond what's necessary.
"""

class GeminiNameAgent:
    def __init__(self, model_name="gemini-2.5-flash"):
        self.model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=INSTRUCTIONS
        )

    async def run(self, conversation_input):
        """
        conversation_input: Có thể là String hoặc List các tin nhắn
        """
        # 1. Xử lý input đầu vào thành chuỗi văn bản
        input_text = ""
        if isinstance(conversation_input, list):
            # Nếu là list chat history (từ frontend gửi lên), nối lại thành chuỗi
            for msg in conversation_input:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                input_text += f"{role}: {content}\n"
        else:
            # Nếu là string
            input_text = str(conversation_input)

        # 2. Gọi Gemini
        try:
            response = await self.model.generate_content_async(input_text)
            title = response.text.strip()
            # Loại bỏ dấu ngoặc kép nếu Gemini lỡ sinh ra (VD: "Tiêu đề")
            return title.replace('"', '').replace("'", "")
        except Exception as e:
            print(f"❌ Lỗi đặt tên chat: {e}")
            return "New Conversation" # Fallback nếu lỗi

# Khởi tạo Agent
name_agent = GeminiNameAgent()

# --- HÀM WRAPPER (Để giữ tương thích với code cũ gọi vào) ---
async def get_name(query):
    # print(f"Generating title for: {query}")
    result = await name_agent.run(query)
    return result

# --- MAIN TEST ---
async def main():
    # Test case giả lập hội thoại
    test_input = [
        {"role": "user", "content": "Cho tôi các bài đăng nhà phố mới nhất tại quận Hoàn Kiếm có 3 tầng"},
        {"role": "assistant", "content": "Dưới đây là danh sách nhà phố tại Hoàn Kiếm..."}
    ]
    
    print("⏳ Đang tạo tiêu đề...")
    result = await get_name(test_input)
    print(f"🏷️ Tiêu đề: {result}")

if __name__ == "__main__":
    asyncio.run(main())