import os
import json
import re
import glob
import pandas as pd
import numpy as np
from datetime import datetime
from elasticsearch import Elasticsearch, helpers
from tqdm import tqdm

# --- CẤU HÌNH ---
ES_HOST = "http://127.0.0.1:9200"
DATA_FOLDER = "../crawled_data" 
BATCH_SIZE = 2000

# 1. MAPPING CHÍNH XÁC 18 FILE CỦA BẠN VÀO INDEX
# Key là từ khóa trong tên file -> Value là tên Index
FILE_INDEX_MAPPING = {
    # --- NHÓM 1: NHÀ MẶT PHỐ (2 loại) ---
    # Logic: Cả "nhamatpho_batch" và "thuenhamatpho_batch" đều chứa chữ "nhamatpho"
    "nhamatpho": "nhamatpho_index",

    # --- NHÓM 2: NHÀ RIÊNG (3 loại) ---
    # "nharieng_batch" và "thuenharieng_batch" chứa "nharieng"
    "nharieng": "nharieng_index",
    # "thuenhatro_batch" chứa "nhatro"
    "nhatro": "nharieng_index",

    # --- NHÓM 3: CHUNG CƯ (2 loại) ---
    # Cả 2 file đều chứa chữ "chungcu"
    "chungcu": "chungcu_index",

    # --- NHÓM 4: BIỆT THỰ (QUAN TRỌNG: Cần thứ tự ưu tiên) ---
    # Đất biệt thự phải map riêng trước
    "datbietthu": "dat_index", 
    # Sau đó mới map biệt thự (nhà)
    "bietthu": "bietthu_index",

    # --- NHÓM 5: ĐẤT (Các loại đất còn lại - 3 loại) ---
    # datmatpho, datrieng, dattrangtrai đều chứa chữ "dat"
    # Lưu ý: "datbietthu" đã được xử lý ở trên nhờ logic ưu tiên chuỗi dài
    "dat": "dat_index",

    # --- NHÓM 6: KHÁC (8 loại còn lại) ---
    "khoxuong": "khac_index",   # Xử lý khoxuong_batch
    "thuekho": "khac_index",    # Xử lý thuekho_batch
    "vanphong": "khac_index",   # Xử lý thuevanphong_batch
    "cuahang": "khac_index",    # Xử lý thuecuahang_batch
    "nhadatkhac": "khac_index", # Xử lý nhadatkhac_batch
    "thuekhac": "khac_index"    # Xử lý thuekhac_batch
}


try:
    es = Elasticsearch(ES_HOST, request_timeout=60)
    if not es.ping(): raise Exception("Không kết nối được ES")
    print("-> Kết nối ES thành công.")
except Exception as e:
    print(f"Lỗi: {e}")
    exit()

# --- CÁC HÀM XỬ LÝ LOGIC (MÔ PHỎNG SPARK) ---

def clean_text_simple(text):
    """Mô phỏng: remove_special_chars + remove_duplicate_punctuation_sequence"""
    if not isinstance(text, str): return ""
    text = re.sub(r'[^\w\s.,?!%/-]', '', text) 
    return re.sub(r'\s+', ' ', text).strip()

def normalize_estate_type(etype):
    if not isinstance(etype, str): return "Khác"
    return etype.strip()

def flatten_address(row):
    addr = row.get('address', {})
    if isinstance(addr, dict):
        return pd.Series([addr.get('province'), addr.get('district')])
    return pd.Series([None, None])

def normalize_extra_infos(info_dict):
    """Mô phỏng: normalize_extra_infos_dict"""
    if not isinstance(info_dict, dict): return {}
    key_map = {
        'no_bedrooms': ['Số Phòng Ngủ', 'Số phòng ngủ :', 'phòng ngủ'],
        'no_bathrooms': ['Số Phòng Tắm', 'Số toilet :', 'phòng tắm', 'wc'],
        'front_road': ['Đường Trước Nhà'],
        'front_face': ['Mặt Tiền'],
        'no_floors': ['Số Tầng', 'Tầng :', 'số tầng'],
        'direction': ['Hướng Nhà', 'hướng'],
        'ultilization_square': ['Diện Tích Sử Dụng'],
        'yo_construction': ['Năm xây dựng'],
        'legal': ['Pháp lý', 'Giấy tờ pháp lý']
    }
    new_data = {}
    def extract_num(val):
        if isinstance(val, (int, float)): return float(val)
        if isinstance(val, str):
            clean = re.sub(r'[^\d.]', '', val.replace(',', '.'))
            try: return float(clean)
            except: return None
        return None

    for std_key, old_keys in key_map.items():
        val = None
        for k in info_dict.keys():
            if any(old_k.lower() in k.lower() for old_k in old_keys):
                val = info_dict[k]
                break
        if val is not None:
            if std_key == 'direction' or std_key == 'legal': 
                new_data[std_key] = str(val).strip()
            elif std_key in ['no_bedrooms', 'no_bathrooms', 'no_floors', 'yo_construction']:
                num = extract_num(val)
                if num is not None: new_data[std_key] = int(num)
            else: 
                new_data[std_key] = extract_num(val)
    return new_data

# --- HÀM MAIN ---

def run_etl():
    search_path = os.path.join(DATA_FOLDER, "**", "*batch.json*")
    files = glob.glob(search_path, recursive=True)
    print(f"Tìm thấy {len(files)} file dữ liệu.")
    
    for file_path in tqdm(files, desc="Đang xử lý file"):
        file_name = os.path.basename(file_path).lower()
        
        index_name = "bds_khac_index" 
        sorted_keys = sorted(FILE_INDEX_MAPPING.keys(), key=len, reverse=True)
        for key in sorted_keys:
            if key in file_name:
                index_name = FILE_INDEX_MAPPING[key]
                break

        try:
            try: df = pd.read_json(file_path, lines=True)
            except ValueError: df = pd.read_json(file_path)
        except Exception: continue
            
        if df.empty: continue

        # =========================================================
        # BƯỚC 1: XỬ LÝ CƠ BẢN (Text, Address, Extra Info)
        # =========================================================
        df['title'] = df['title'].apply(clean_text_simple)
        df['description'] = df['description'].apply(clean_text_simple)
        df['estate_type'] = df['estate_type'].apply(normalize_estate_type)
        df[['province', 'district']] = df.apply(flatten_address, axis=1)
        
        extra_info_list = df['extra_infos'].apply(normalize_extra_infos).tolist()
        extra_df = pd.DataFrame(extra_info_list)
        df = pd.concat([df.reset_index(drop=True), extra_df.reset_index(drop=True)], axis=1)
        
        # --- QUAN TRỌNG: XÓA CỘT extra_infos GỐC ĐỂ TIẾT KIỆM DB ---
        if 'extra_infos' in df.columns:
            df.drop(columns=['extra_infos'], inplace=True)

        # Chuyển đổi số
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        df['square'] = pd.to_numeric(df['square'], errors='coerce')
        
        # =========================================================
        # BƯỚC 2: KHỬ TRÙNG LẶP (Thay thế MinHashLSH của Spark)
        # =========================================================
        # Spark dùng MinHash (phức tạp), Pandas dùng drop_duplicates (hiệu quả cho 500MB)
        # Nếu Tiêu đề và Mô tả giống hệt nhau -> Coi là trùng -> Xóa
        initial_len = len(df)
        df.drop_duplicates(subset=['title', 'description'], keep='first', inplace=True)
        # print(f"Đã loại bỏ {initial_len - len(df)} bài đăng trùng lặp.")

        # =========================================================
        # BƯỚC 3: LỌC NHIỄU GIÁ (Mô phỏng get_detail_lower_upper_bound)
        # =========================================================
       # Tạo cột tạm để lọc
        df['temp_price_m2'] = df['price'] / df['square']
        
        filtered_dfs = []
        for etype, group in df.groupby('estate_type'):
            valid_rows = group.dropna(subset=['temp_price_m2'])
            if len(valid_rows) > 10:
                lower_p = valid_rows['temp_price_m2'].quantile(0.05)
                upper_p = valid_rows['temp_price_m2'].quantile(0.95)
                iqr = upper_p - lower_p
                upper_bound = upper_p + 5 * iqr
                lower_bound = max(0, lower_p - 5 * iqr)
                
                mask = (group['temp_price_m2'].isna()) | \
                       ((group['temp_price_m2'] >= lower_bound) & (group['temp_price_m2'] <= upper_bound))
                filtered_dfs.append(group[mask])
            else:
                filtered_dfs.append(group)
        
        if filtered_dfs:
            df = pd.concat(filtered_dfs)
            
        # Tạo cột chính thức price_per_m2
        df['price_per_m2'] = pd.to_numeric(df['temp_price_m2'], errors='coerce')
        # Xóa cột tạm
        if 'temp_price_m2' in df.columns: del df['temp_price_m2']
        
        df['created_at'] = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

        # =========================================================
        # BƯỚC 4: LOAD VÀO ES
        # =========================================================
        if not es.indices.exists(index=index_name):
            es.indices.create(index=index_name, body={
                "mappings": {
                    "properties": {
                       "estate_type": {"type": "keyword"},
                        "province": {"type": "keyword"},
                        "district": {"type": "keyword"},
                        "price": {"type": "double"},
                        "square": {"type": "float"},
                        "price_per_m2": {"type": "double"}, # Giữ lại theo yêu cầu
                        
                        "no_bedrooms": {"type": "integer"},
                        "no_bathrooms": {"type": "integer"},
                        "no_floors": {"type": "integer"},
                        "direction": {"type": "keyword"},
                        "legal": {"type": "keyword"}, # Thêm trường pháp lý
                        
                        "link": {"type": "keyword"},
                        "title": {"type": "text"},
                        "description": {"type": "text"},
                        "contact_info": {"type": "object"}
                    }
                }
            })

        def gen_data(df, idx):
            for _, row in df.iterrows():
                doc = row.where(pd.notnull(row), None).to_dict()
                doc_id = str(row['post_id']) if 'post_id' in row and pd.notnull(row['post_id']) else None
                action = {"_index": idx, "_source": doc}
                if doc_id: action["_id"] = doc_id
                yield action
        
        try:
            helpers.bulk(es, gen_data(df, index_name), chunk_size=BATCH_SIZE)
        except Exception as e:
            print(f"Lỗi import file {file_name}: {e}")

    print("HOÀN TẤT XỬ LÝ VÀ IMPORT DỮ LIỆU!")

if __name__ == "__main__":
    run_etl()