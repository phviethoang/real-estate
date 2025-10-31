import json
import glob
import os

all_data = []
output_file = "/home3/myntt/Project/BigData/crawler/src/crawlerbds/crawled_data/chungcu/bds_spider_all_chungcu_batch.json"
files = glob.glob("/home3/myntt/Project/BigData/crawler/src/crawlerbds/crawled_data/chungcu/bds_spider_*_chungcu_batch.json")
print(f"Tìm thấy {len(files)} file JSON để gộp.")

for file in files:
    with open(file, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            if isinstance(data, list):
                all_data.extend(data)
            else:
                all_data.append(data)
        except json.JSONDecodeError:
            print(f"Lỗi khi đọc {file}")

with open(output_file, "w", encoding="utf-8") as out:
    json.dump(all_data, out, ensure_ascii=False, indent=2)

file_size = os.path.getsize(output_file)  # đơn vị: byte
print(f"Dung lượng file '{output_file}': {file_size / (1024*1024):.2f} MB")
print(f"Tổng số bản ghi: {len(all_data)}")
