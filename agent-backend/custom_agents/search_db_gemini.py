from __future__ import annotations
import os
import asyncio
import json
from typing import List, Any
from dotenv import load_dotenv

import google.generativeai as genai

# Import các hàm query
from .elasticsearch_queries import search_posts, search_posts_strict 
from .agent_type import Post, Address, ContactInfo, ExtraInfos, FunctionArgs

# Load biến môi trường
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("Thiếu API Key")

genai.configure(api_key=api_key)

# --- 1. HÀM HELPER MAP DATA (GIỮ NGUYÊN) ---
def map_es_result_to_post(result: dict) -> Post:
    addr = result.get("address", {}) or {}
    contact = result.get("contact_info", {}) or {}
    
    raw_post_id = result.get("post_id")
    safe_post_id = str(raw_post_id) if raw_post_id is not None else ""
    
    raw_id = result.get("id")
    safe_id = str(raw_id) if raw_id is not None else None

    safe_ward = addr.get("ward")
    if safe_ward is None:
        safe_ward = ""

    safe_price = result.get("price") or 0.0
    safe_price_m2 = result.get("price_per_m2") or 0.0
    safe_square = result.get("square") or 0.0

    return Post(
        address=Address(
            district=result.get("district"),
            full_address=addr.get("full_address"),
            province=result.get("province"),
            ward=safe_ward
        ),
        contact_info=ContactInfo(
            name=contact.get("name"),
            phone=contact.get("phone", [])
        ),
        description=result.get("description"),
        estate_type=result.get("estate_type"),
        extra_infos=ExtraInfos(
            direction=result.get("direction"),
            front_face=result.get("front_face"),
            front_road=result.get("front_road"),
            no_bathrooms=result.get("no_bathrooms"),
            no_bedrooms=result.get("no_bedrooms"),
            no_floors=result.get("no_floors"),
            ultilization_square=result.get("ultilization_square"), 
            yo_construction=result.get("yo_construction"),
            legal=result.get("legal")
        ),
        id=safe_id, 
        link=result.get("link"),
        post_date=result.get("post_date"),
        created_at=result.get("created_at"),
        post_id=safe_post_id,
        price=safe_price,
        price_per_square=safe_price_m2, 
        square=safe_square,
        title=result.get("title")
    )

# --- 2. CLASS AGENT ---
class GeminiSearchAgent:
    def __init__(self, model_name="models/gemini-2.5-flash"):
        self.tools = [search_posts, search_posts_strict]
        
        self.system_instruction = """
       Bạn là chuyên gia BĐS. Nhiệm vụ: Query dữ liệu chính xác từ Database.
        
        QUY TẮC BẮT BUỘC:
        1. Xử lý GIÁ TIỀN (Quan trọng):
           - "tỷ", "tỉ" -> nhân 1,000,000,000.
           - "triệu", "tr" -> nhân 1,000,000.
           
           * LOGIC NÂNG CAO:
           - "nhỏ hơn 4 tỷ", "dưới 4 tỷ", "tối đa 4 tỷ" -> Gán max_price=4000000000.
           - "lớn hơn 3 tỷ", "trên 3 tỷ" -> Gán min_price=3000000000.
           - "từ 3 đến 5 tỷ" -> Gán min_price=3000000000, max_price=5000000000.
           - "khoảng 3 tỷ", "tầm 3 tỷ" -> Gán price=3000000000 (để hệ thống tự tính khoảng).

        2. Xử lý ĐỊA ĐIỂM:
           - "Quận Thanh Xuân" -> district="Thanh Xuân"
        
        3. CHIẾN THUẬT:
           - Ưu tiên dùng `search_posts_strict` cho các câu hỏi cụ thể.
        """
        
        self.model = genai.GenerativeModel(
            model_name=model_name,
            tools=self.tools,
            system_instruction=self.system_instruction
        )

    def run(self, query: str) -> List[Post]:
        chat = self.model.start_chat(enable_automatic_function_calling=False)
        print(f"User: {query}")
        
        try:
            response = chat.send_message(query)
        except Exception as e:
            print(f"Lỗi API: {e}")
            return []
        
        try:
            part = response.parts[0]
            if part.function_call:
                fc = part.function_call
                fname = fc.name
                # Lấy tham số thô
                fargs = {k: v for k, v in fc.args.items()}
                
                print(f"🤖 Gemini gọi hàm: {fname}")
                print(f"📦 Tham số gốc: {fargs}")
                
                # --- BƯỚC QUAN TRỌNG NHẤT: CLEAN DATA ---
                clean_args = self._sanitize_args(fargs)
                print(f"✨ Tham số đã xử lý: {clean_args}")
                # ----------------------------------------

                raw_results = []
                try:
                    if fname == 'search_posts':
                        raw_results = search_posts(**clean_args)
                    elif fname == 'search_posts_strict':
                        raw_results = search_posts_strict(**clean_args)
                        # Fallback nếu strict rỗng
                        if not raw_results:
                            print("Strict rỗng, fallback sang thường...")
                            raw_results = search_posts(**clean_args)
                except Exception as e:
                    print(f"Lỗi thực thi hàm search: {e}")
                    return []

                print(f"-> DB trả về {len(raw_results)} kết quả.")
                
                result_posts = []
                for item in raw_results:
                    try:
                        result_posts.append(map_es_result_to_post(item))
                    except:
                        continue
                return result_posts

        except Exception as e:
            print(f"Lỗi xử lý: {e}")
            
        return []

    def _sanitize_args(self, args: dict) -> dict:
        """
        Hàm rửa sạch dữ liệu:
        1. Ép kiểu Float -> Int cho các trường số nguyên (phòng ngủ, tầng...)
        2. Lowercase Estate Type để khớp index map.
        3. Xử lý District (List/String/Chữ Quận).
        """
        new_args = args.copy()

        # 1. Ép kiểu Int cho các trường đếm (Fix lỗi 2.0 -> 2)
        int_fields = ['no_bedrooms', 'no_bathrooms', 'no_floors']
        for field in int_fields:
            if field in new_args and new_args[field] is not None:
                try:
                    new_args[field] = int(new_args[field])
                except:
                    pass

        # # 2. Xử lý Estate Type (Fix lỗi 'Chung cư' -> 'chung cư')
        # if 'estate_type' in new_args:
        #     et = new_args['estate_type']
        #     if isinstance(et, list):
        #         new_args['estate_type'] = [x.lower() for x in et]
        #     elif isinstance(et, str):
        #         new_args['estate_type'] = [et.lower()]

        # 3. Xử lý District (Fix lỗi chuỗi/list và chữ 'Quận')
        if 'district' in new_args:
            raw = new_args['district']
            # Đảm bảo luôn là List
            if isinstance(raw, str):
                dist_list = [raw]
            else:
                dist_list = raw # Giả sử là list
            
            # Clean chữ
            cleaned = []
            for d in dist_list:
                c = d.replace("Quận ", "").replace("Huyện ", "").strip()
                cleaned.append(c)
            
            new_args['district'] = cleaned

        # 4. Ép giá trị về số thực
        for p_field in ['price', 'min_price', 'max_price']:
            if p_field in new_args and new_args[p_field] is not None:
                try:
                    new_args[p_field] = float(new_args[p_field])
                except:
                    pass
            
        return new_args


# --- MAIN TEST (INTERACTIVE MODE - ĐÃ FIX LỖI UTF-8) ---
import sys

if __name__ == "__main__":
    # 1. ÉP BUỘC TERMINAL DÙNG UTF-8 (Fix lỗi surrogate)
    try:
        if sys.stdin.encoding.lower() != 'utf-8':
            print(f"⚠️ Cảnh báo: Terminal encoding là {sys.stdin.encoding}, đang chuyển sang utf-8...")
            sys.stdin.reconfigure(encoding='utf-8')
        if sys.stdout.encoding.lower() != 'utf-8':
            sys.stdout.reconfigure(encoding='utf-8')
    except Exception as e:
        print(f"⚠️ Không thể cấu hình encoding: {e}")

    try:
        print("⏳ Đang khởi tạo Gemini Agent...")
        agent = GeminiSearchAgent()
        print("\n" + "="*70)
        print("🤖  GEMINI REAL ESTATE AGENT - CHẾ ĐỘ TƯƠNG TÁC")
        print("="*70)

        while True:
            try:
                # Nhập liệu
                query = input("\n💬 Nhập câu hỏi: ").strip()
            except UnicodeDecodeError:
                print("❌ Lỗi đọc ký tự tiếng Việt từ bàn phím. Hãy thử chạy lệnh: export PYTHONIOENCODING=utf-8")
                continue

            if query.lower() in ["exit", "quit", "q"]:
                print("👋 Tạm biệt!")
                break
            
            if not query:
                continue

            # 2. VỆ SINH CHUỖI INPUT (Lọc bỏ ký tự lỗi trước khi gửi API)
            try:
                # Encode và Decode lại để loại bỏ ký tự surrogate (\udcc6...)
                query = query.encode('utf-8', 'ignore').decode('utf-8')
            except Exception:
                pass

            print(f"🚀 Đang xử lý: '{query}'")

            try:
                posts = agent.run(query)
                
                print(f"\n✅ TÌM THẤY: {len(posts)} bài đăng.")
                print("-" * 70)

                if not posts:
                    print("📭 Không có kết quả phù hợp.")
                    continue

                for i, p in enumerate(posts, 1):
                    # Xử lý an toàn cho extra_infos
                    try:
                        bedrooms = p.extra_infos.no_bedrooms if p.extra_infos else "N/A"
                        floors = p.extra_infos.no_floors if p.extra_infos else "N/A"
                    except:
                        bedrooms = "N/A"
                        floors = "N/A"

                    price_str = f"{p.price:,.0f}" if p.price else "Thỏa thuận"
                    
                    print(f"#{i}")
                    print(f"   🏠 {p.title}")
                    print(f"   💰 {price_str} VNĐ")
                    print(f"   📍 {p.address.district} | {p.address.ward}")
                    print(f"   🛠️  {bedrooms} ngủ | {floors} tầng | {p.square} m2")
                    print(f"   📂 {p.estate_type}")
                    print(f"   🔗 Link: {p.link}")
                    print("-" * 70)

            except Exception as e:
                print(f"❌ LỖI XỬ LÝ: {e}")

    except KeyboardInterrupt:
        print("\n\n👋 Đã dừng.")