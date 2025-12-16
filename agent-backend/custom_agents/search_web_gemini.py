from __future__ import annotations
import os
import asyncio
from dotenv import load_dotenv
import google.generativeai as genai
from ddgs import DDGS # Thư viện search miễn phí

# Load API Key
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY") 
if not api_key:
    api_key = os.getenv("GOOGLE_API_KEY")

genai.configure(api_key=api_key)

INSTRUCTIONS = (
    "You are a real estate research assistant. Given a search term about real estate, you search the web "
    "for that term and produce a concise summary of results. Focus on real estate info like real estate posts, market trends, "
    "price forecasts, project updates, amenities around the property. Summary must be 2-3 paragraphs, under 300 words. Capture main points. "
    "Write succinctly, no complete sentences or good grammar needed. For someone synthesizing a real estate "
    "report, so focus on essence, ignore fluff. No extra commentary beyond summary. Just write about the query that you have the information about and ignore the query that you dont't have the information about. You must response in Vietnamese."
)

# --- ĐỊNH NGHĨA CÔNG CỤ TÌM KIẾM ---
def perform_web_search(query: str):
    """
    Tìm kiếm thông tin trên internet về bất động sản, thị trường, giá cả.
    Args:
        query: Từ khóa hoặc câu hỏi cần tìm kiếm.
    Returns:
        Danh sách các kết quả tìm kiếm bao gồm tiêu đề, link và tóm tắt.
    """
    print(f"🌍 Đang tìm kiếm trên web: '{query}'...")
    try:
        results = DDGS().text(query, max_results=5)
        if not results:
            return "Không tìm thấy kết quả nào."
        
        # Format kết quả thành chuỗi text để gửi lại cho Gemini
        formatted_results = ""
        for res in results:
            formatted_results += f"- Title: {res['title']}\n  Link: {res['href']}\n  Snippet: {res['body']}\n\n"
        return formatted_results
    except Exception as e:
        return f"Lỗi khi tìm kiếm: {str(e)}"

class GeminiWebSearchAgent:
    def __init__(self, model_name="models/gemini-2.5-flash"):
        # Cấu hình Function Calling
        # Chúng ta truyền trực tiếp hàm python vào, SDK sẽ tự chuyển đổi
        self.tools = [perform_web_search]

        self.model = genai.GenerativeModel(
            model_name=model_name,
            tools=self.tools,
            system_instruction=INSTRUCTIONS
        )
        
        # Kích hoạt chế độ tự động gọi hàm (Automatic Function Calling)
        # Gemini sẽ tự gọi hàm, lấy kết quả, và tổng hợp lại thành văn bản
        self.chat = self.model.start_chat(enable_automatic_function_calling=True)

    async def run(self, query: str) -> str:
        """
        Thực hiện tìm kiếm và tóm tắt
        """
        try:
            # Gửi tin nhắn, Gemini sẽ tự động kích hoạt tool perform_web_search nếu cần
            response = await self.chat.send_message_async(query)
            return response.text
            
        except Exception as e:
            print(f"❌ Lỗi Web Search Agent: {e}")
            return f"Không thể thực hiện tìm kiếm. Lỗi: {e}"

# Khởi tạo instance
search_agent = GeminiWebSearchAgent()

# --- MAIN TEST ---
async def main():
    print("⏳ Đang test Gemini Web Search (Function Calling)...")
    
    # Test query
    query = "Giá đất nền tại Đông Anh hiện nay biến động thế nào? Có nên đầu tư không?"
    
    result = await search_agent.run(query)
    
    print("\n✅ KẾT QUẢ TỔNG HỢP TỪ GEMINI:")
    print("-" * 60)
    print(result)
    print("-" * 60)

if __name__ == "__main__":
    asyncio.run(main())