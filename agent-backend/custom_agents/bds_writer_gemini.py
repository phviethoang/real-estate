import os
import asyncio
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import google.generativeai as genai
import json
import re 
import ast
# 1. Cấu hình API
load_dotenv()
# Lấy API Key từ biến môi trường
api_key = os.getenv("OPENAI_API_KEY") 
genai.configure(api_key=api_key)

# 2. Định nghĩa Model (GIỮ NGUYÊN)
class RealEstateAdvice(BaseModel):
    real_estate_findings: str = Field(description="A markdown-formatted summary of listings and web-sourced information.")
    summary_real_estate_findings: str = Field(description="A concise summary of real_estate_findings, excluding links, with a maximum of 2000 characters.")
    analytics_and_advice: str = Field(description="Detailed analysis and investment recommendations provided by the advisor.")
    follow_up_questions: list[str] = Field(description="Suggested follow-up research topics or questions.")

# 3. Prompt (GIỮ NGUYÊN)
PROMPT = (
    "Bạn là một cố vấn đầu tư chuyên nghiệp chuyên về thị trường bất động sản. "
    "Bạn sẽ nhận được một câu hỏi đầu tư ban đầu cùng với dữ liệu sơ bộ.\n\n"
    "Nhiệm vụ của bạn là phân tích dữ liệu này, cung cấp một bản tóm tắt có cấu trúc về các phát hiện, và đưa ra "
    "lời khuyên đầu tư có thể thực hiện dựa trên câu hỏi được đưa ra. Sử dụng chuyên môn của bạn để đánh giá các cơ hội tiềm năng, "
    "so sánh các danh sách nếu có, đánh giá rủi ro, và làm nổi bật các yếu tố đầu tư quan trọng. "
    "Nếu có danh sách bất động sản, hãy trích dẫn liên kết của chúng và tóm tắt thông số kỹ thuật cùng các đặc điểm nổi bật của bất động sản ở định dạng markdown.\n\n"
    "Kết quả đầu ra phải được tổ chức tốt và BẮT BUỘC phải bao gồm các key sau, không được tự động sửa:\n"
    "1. 'real_estate_findings': Một phần markdown tóm tắt tất cả các phát hiện (danh sách và thông tin bên ngoài)\n"
    "2. 'summary_real_estate_findings': Một phần tóm tắt ngắn gọn của real_estate_findings, không bao gồm liên kết, tối đa 2000 characters\n"
    "3. 'analytics_and_advice': Một phần phân tích chi tiết và lời khuyên cá nhân hóa\n"
    "4. 'follow_up_questions': Một danh sách các câu hỏi tiếp theo để nghiên cứu thêm\n\n"
    "Chỉ trả lời bằng tiếng Việt."
)


# --- HÀM LÀM SẠCH TEXT (MỚI THÊM) ---
def clean_markdown_formatting(text: str) -> str:
    """
    Hàm này loại bỏ các ký tự Markdown gây rối mắt trong Console:
    - **Bold** -> Bold
    - * Bullet -> - Bullet
    """
    if not isinstance(text, str): return text
    
    # 1. Loại bỏ dấu in đậm (**text**) -> text
    text = text.replace("**", "")
    
    # 2. Đổi dấu gạch đầu dòng dạng sao (*) thành gạch ngang (-) cho gọn
    # Regex: Tìm dấu * ở đầu dòng hoặc sau xuống dòng, thay bằng -
    text = re.sub(r'(^|\n)\s*\*\s+', r'\1- ', text)
    
    # 3. Loại bỏ các dấu * còn sót lại nếu chúng không phải là bullet point
    # (Tùy chọn, nếu bạn muốn sạch bóng)
    # text = text.replace("*", "") 
    
    return text


# --- 4. HÀM CỨU DỮ LIỆU (MAGIC FUNCTION) ---
def clean_and_parse_json(text: str):
    """
    Hàm phân giải siêu mạnh:
    1. Thử json chuẩn.
    2. Thử ast.literal_eval (Hiểu được cú pháp Python Dict lỏng lẻo hơn JSON).
    3. Thử cắt gọt phần thừa.
    """
    # 1. Làm sạch cơ bản
    text = text.strip()
    # Loại bỏ Markdown code blocks ```json ... ```
    if "```" in text:
        text = re.sub(r"```json|```", "", text).strip()

    # 2. Thử Parse JSON Chuẩn
    try:
        return json.loads(text, strict=False) # strict=False giúp bỏ qua một số lỗi ký tự điều khiển
    except:
        pass

    # 3. Thử dùng AST (Cứu cánh cho lỗi 'Unterminated string' do xuống dòng)
    # Gemini đôi khi trả về format giống Python Dictionary hơn là JSON thuần
    try:
        # ast.literal_eval an toàn hơn eval()
        # Nó xử lý được cả: { 'key': "Line 1 \n Line 2" } mà JSON chuẩn bó tay
        return ast.literal_eval(text)
    except:
        pass

    # 4. Thử vá lỗi EOF (Cắt cụt)
    try:
        # Nếu thiếu ngoặc đóng, thử đóng lại bừa để lấy dữ liệu phần đầu
        if not text.endswith("}"):
            return json.loads(text + '"}', strict=False)
    except:
        pass

    return None


# 4. Class WriterAgent (Phiên bản Gemini Native - Đơn giản hóa)
class GeminiWriterAgent:
    def __init__(self, model_name="gemini-2.5-pro"):
        # Sử dụng gemini-1.5-flash (bản ổn định) hoặc gemini-2.0-flash-exp (bản mới nhất)
        self.model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=PROMPT,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                # response_schema=RealEstateAdvice, # <--- CHÌA KHÓA: Ép kiểu Pydantic trực tiếp tại đây
                temperature=0.3, # Giảm nhiệt độ để phân tích chuẩn xác hơn
                max_output_tokens=8192 # <--- QUAN TRỌNG: Tăng max token để tránh lỗi EOF khi viết báo cáo dài
            )
        )

    async def run(self, query: str, data_context: str):
        print(f"✍️ Writer đang viết báo cáo với {self.model.model_name}...")
        
        user_content = f"CÂU HỎI: {query}\n\nDỮ LIỆU ĐẦU VÀO:\n{data_context}"
        
        try:
            # Gọi API
            response = await self.model.generate_content_async(user_content)
            raw_text = response.text
            
            # --- XỬ LÝ AN TOÀN ---
            # Thay vì json.loads(response.text) ngay, ta dùng hàm clean
            data = clean_and_parse_json(raw_text)
            
            if data:
                # --- BƯỚC MỚI: CLEAN TEXT TRƯỚC KHI TRẢ VỀ ---
                # Chúng ta làm sạch từng trường text
                
                # 1. Lấy dữ liệu thô (Smart Mapping như cũ)
                findings = data.get("real_estate_findings", "")
                summary = (data.get("summary_real_estate_findings") or 
                           data.get("real_estate_findings_summary") or "")
                advice = (data.get("analytics_and_advice") or 
                          data.get("analysis_and_advice") or "")
                questions = data.get("follow_up_questions", [])

                # 2. Làm sạch (Xóa dấu **)
                cleaned_findings = clean_markdown_formatting(findings)
                cleaned_summary = clean_markdown_formatting(summary)
                cleaned_advice = clean_markdown_formatting(advice)
                
                # 3. Tạo Object trả về
                try:
                    return RealEstateAdvice(
                        real_estate_findings=cleaned_findings,
                        summary_real_estate_findings=cleaned_summary,
                        analytics_and_advice=cleaned_advice,
                        follow_up_questions=questions
                    )
                except Exception as ve:
                    print(f"⚠️ Validation Warning: {ve}")
                    return RealEstateAdvice(
                        real_estate_findings=cleaned_findings,
                        summary_real_estate_findings=cleaned_summary,
                        analytics_and_advice=cleaned_advice,
                        follow_up_questions=[]
                    )
            else:
                print(f"❌ Vẫn không parse được. Raw len: {len(raw_text)}")
                # In ra 100 ký tự đầu để debug
                print(f"❌ Head: {raw_text[:100]}...")
                return RealEstateAdvice(
                    real_estate_findings="Lỗi phân tích dữ liệu.",
                    summary_real_estate_findings="Error Parsing JSON",
                    analytics_and_advice=f"Raw Data (Copy thủ công): {raw_text[:2000]}...",
                    follow_up_questions=[]
                )
            
        except Exception as e:
            print(f"❌ Lỗi API/System: {e}")
            return None

# --- CHẠY THỬ ---
async def main():
    # 1. Mock Query: Sát với nhu cầu thực tế
    mock_query = "tìm cho tôi nhà riêng 2 tầng 2 phòng ngủ ở huyện hoài đức giá dưới 5 tỷ. tư vấn cho tôi các căn phù hợp nếu như tôi có ô tô "

    # 2. Mock Data: Dữ liệu chuẩn từ Database của bạn
    # Lưu ý: Python dùng 3 dấu nháy kép """ để chứa chuỗi nhiều dòng.
    # Dữ liệu này dạng String là RẤT TỐT cho Gemini đọc hiểu.
    mock_data = """
            #1
            🏠 Nhà 2 tầng dân xây an trai vân canh giá 4,5 tỷ về ở được ngay , dt 30 m2 gần đường ô tô ngã tư canh
            💰 4,500,000,000 VNĐ
            📍 Hoài Đức | Vân Canh
            🛠️  2 ngủ | 2 tầng | 30.0 m2
            📂 Nhà riêng
            🔗 Link: https://bds68.com.vn/ban-nha-rieng/ha-noi/hoai-duc/duong-an-trai/nha-2-tang-dan-xay-an-trai-van-canh-gia-45-ty-ve-o-duoc-ngay-dt-30m2-gan-duong-o-to-nga-tu-canh-pr28442765
            ----------------------------------------------------------------------
            #2
            🏠 Chỉ 4.5 tỷ sở hữu ngôi nhà 2 t , 2 pn , kiên cố , vân canh , gần trường c1 , c2 , chợ , gần bãi gửi xe ôtô
            💰 4,500,000,000 VNĐ
            📍 Hoài Đức | Vân Canh
            🛠️  2 ngủ | 2 tầng | 31.0 m2
            📂 Nhà riêng
            🔗 Link: https://bds68.com.vn/ban-nha-rieng/ha-noi/hoai-duc/duong-an-trai/chi-45-ty-so-huu-ngoi-nha-2t-2pn-kien-co-van-canh-gan-truong-c1-c2-cho-gan-bai-gui-xe-oto-pr28879757
            ----------------------------------------------------------------------
            #3
            🏠 Nhà rẻ nhất vân canh 30 m xây 2 tầng chỉ nhỉnh 4 tỷ
            💰 4,500,000,000 VNĐ
            📍 Hoài Đức | Vân Canh
            🛠️  2 ngủ | 2 tầng | 30.0 m2
            📂 Nhà riêng
            🔗 Link: https://bds68.com.vn/ban-nha-rieng/ha-noi/hoai-duc/xa-van-canh/nha-re-nhat-van-canh-30m-xay-2-tang-chi-nhinh-4-ty-pr28424152
            ----------------------------------------------------------------------
            #4
            🏠 Bán nhà riêng 2 tầng , diện tích 43 m2 tại xã di trạch
            💰 4,090,000,000 VNĐ
            📍 Hoài Đức | Di Trạch
            🛠️  2 ngủ | 2 tầng | 43.0 m2
            📂 Nhà riêng
            🔗 Link: https://bds68.com.vn/ban-nha-rieng/ha-noi/hoai-duc/xa-di-trach/ban-nha-rieng-2-tang-dien-tich-43-m2-tai-xa-di-trach-pr28236463
            ----------------------------------------------------------------------
            #5
            🏠 Nhỉnh 4 tỷ , có nhà 2.5 tầng ở vân canh , gần chợ vân canh , giáp đường trịnh văn bô
            💰 4,500,000,000 VNĐ
            📍 Hoài Đức | Vân Canh
            🛠️  2 ngủ | 2 tầng | 30.0 m2
            📂 Nhà riêng
            🔗 Link: https://bds68.com.vn/ban-nha-rieng/ha-noi/hoai-duc/duong-an-trai/nhinh-4-ty-co-nha-25-tang-o-van-canh-gan-cho-van-canh-giap-duong-trinh-van-bo-pr28950609
            ----------------------------------------------------------------------
            #6
            🏠 Bán nhà 2 tầng 2 ngủ quyết tiến 1 vân côn sơn đồng ô tô lùi tận cửa
            💰 3,500,000,000 VNĐ
            📍 Hoài Đức | Vân Côn
            🛠️  2 ngủ | 2 tầng | 42.0 m2
            📂 Nhà riêng
            🔗 Link: https://bds68.com.vn/ban-nha-rieng/ha-noi/hoai-duc/xa-van-con/ban-nha-2-tang-2-ngu--quyet-tien-1--van-con--son-dong--o-to-lui-tan-cua-pr29143149
        """
    
    current_model = "gemini-2.5-pro" 
    
    print(f"🚀 Đang chạy với model: {current_model}")
    agent = GeminiWriterAgent(model_name=current_model) 
    
    result = await agent.run(mock_query, mock_data)
    
    if result:
        print("\n✅ KẾT QUẢ PHÂN TÍCH:")
        print("=" * 60)
        
        # In phần tóm tắt findings để xem nó đọc được những nhà nào
        print("📝 TÓM TẮT DỮ LIỆU TÌM ĐƯỢC:")
        print(result.summary_real_estate_findings)
        print("-" * 60)
        
        # In phần lời khuyên chi tiết
        print(f"💡 LỜI KHUYÊN (Độ dài: {len(result.analytics_and_advice)} ký tự):")
        print(result.analytics_and_advice)
        print("-" * 60)
        
        # In câu hỏi follow-up
        print("❓ CÂU HỎI TIẾP THEO:")
        for q in result.follow_up_questions:
            print(f"  - {q}")

if __name__ == "__main__":
    asyncio.run(main())