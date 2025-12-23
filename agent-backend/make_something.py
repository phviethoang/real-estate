import json
import time
import google.generativeai as genai
from tqdm import tqdm
import os

# --- CẤU HÌNH ---
API_KEY = "AIzaSyDhO5y6AkO8hiU_jr5PduWjfAqh3zJDLGU"  # <-- Thay API Key của bạn vào đây
INPUT_FILE = "../frontend/district_coords.json"
OUTPUT_FILE = "../frontend/district_coords_full.json"
BATCH_SIZE = 10  # Gửi 10 địa điểm mỗi lần để Gemini trả lời chính xác nhất

# Cấu hình Gemini
genai.configure(api_key=API_KEY)
# Dùng bản Flash cho nhanh và tiết kiệm, hoặc Pro nếu cần độ chính xác cao hơn
model = genai.GenerativeModel('gemini-2.5-flash') 

def load_data():
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Không tìm thấy file {INPUT_FILE}")
        exit()

def get_missing_items(data):
    """
    Quét toàn bộ file JSON để tìm các cặp Tỉnh - Huyện có giá trị là null.
    Trả về danh sách: [{'province': 'Hà Giang', 'district': 'Bắc Mê'}, ...]
    """
    missing = []
    for province, districts in data.items():
        if isinstance(districts, dict): # Đề phòng cấu trúc lạ
            for dist_name, coords in districts.items():
                if coords is None:
                    missing.append({
                        "province": province, 
                        "district": dist_name
                    })
    return missing

def clean_json_response(text):
    """Làm sạch chuỗi JSON trả về từ Gemini (bỏ markdown ```json)"""
    text = text.replace("```json", "").replace("```", "").strip()
    return text

def ask_gemini_coords(batch_items):
    """
    Gửi danh sách (Tỉnh, Huyện) sang Gemini để hỏi tọa độ.
    """
    
    # Tạo prompt rõ ràng, cung cấp cả Tỉnh để Gemini tìm chính xác
    prompt = f"""
    I have a list of districts in Vietnam that are missing GPS coordinates.
    Please provide the accurate latitude and longitude for the center of these specific districts within their respective provinces.

    INPUT DATA (List of Province and District):
    {json.dumps(batch_items, ensure_ascii=False)}

    INSTRUCTIONS:
    1. Return ONLY a valid JSON List.
    2. Each item in the list must contain: "province", "district", and "coords" [latitude, longitude].
    3. Coordinates must be numbers (floats).
    4. Do not wrap the output in markdown code blocks if possible, just raw JSON.

    EXAMPLE OUTPUT FORMAT:
    [
        {{"province": "Hà Giang", "district": "Bắc Mê", "coords": [22.7534, 105.1523]}},
        {{"province": "Hà Giang", "district": "Xín Mần", "coords": [22.5642, 104.5982]}}
    ]
    """

    try:
        response = model.generate_content(prompt)
        clean_text = clean_json_response(response.text)
        return json.loads(clean_text)
    except Exception as e:
        print(f"\n⚠️ Lỗi khi gọi Gemini hoặc Parse JSON: {e}")
        # In ra text lỗi để debug nếu cần
        # print(response.text if 'response' in locals() else "No response")
        return []

# --- MAIN PROGRAM ---
if __name__ == "__main__":
    # 1. Load dữ liệu gốc
    data = load_data()
    
    # 2. Tìm các điểm bị null
    missing_items = get_missing_items(data)
    total_missing = len(missing_items)
    
    print(f"🔍 Tìm thấy {total_missing} địa điểm bị NULL cần điền.")
    
    if total_missing == 0:
        print("✅ Dữ liệu đã đầy đủ!")
        exit()

    # 3. Chạy vòng lặp theo Batch
    updated_count = 0
    
    # Tqdm tạo thanh tiến trình
    for i in tqdm(range(0, total_missing, BATCH_SIZE), desc="Đang hỏi Gemini"):
        # Lấy ra 1 nhóm (ví dụ 15 cái)
        batch = missing_items[i : i + BATCH_SIZE]
        
        # Gọi Gemini
        results = ask_gemini_coords(batch)
        
        # Cập nhật kết quả vào biến `data` gốc
        for item in results:
            try:
                prov = item.get('province')
                dist = item.get('district')
                coords = item.get('coords')
                
                # Kiểm tra kỹ trước khi gán để đảm bảo đúng cấu trúc
                if prov in data and dist in data[prov] and isinstance(coords, list) and len(coords) == 2:
                    data[prov][dist] = coords
                    updated_count += 1
            except Exception:
                continue
        
        # Nghỉ 2 giây để tránh bị Google chặn vì spam request
        time.sleep(2)

    # 4. Lưu lại file mới (hoặc đè file cũ tùy bạn chỉnh tên OUTPUT_FILE)
    print("💾 Đang lưu file...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print(f"\n🎉 HOÀN TẤT! Đã điền thành công {updated_count}/{total_missing} địa điểm.")
    print(f"📂 Kết quả lưu tại: {OUTPUT_FILE}")
    
    # Kiểm tra lại xem còn sót cái nào không
    still_missing = get_missing_items(data)
    if still_missing:
        print(f"⚠️ Vẫn còn sót {len(still_missing)} địa điểm Gemini không tìm thấy.")
        # print(still_missing)