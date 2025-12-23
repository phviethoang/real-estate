import json
import os
import subprocess
import time

# ===============================
# Cấu hình Crawler (Crawler parameters)
# ===============================
SPIDER_NAME = "bds68_spider"
MIN_PAGE = 1
MAX_PAGE = 1
JUMP_TO_PAGE = 1

# ===============================
# Cấu hình Kafka (Kafka parameters)
# ===============================
# Lưu ý: Hãy đảm bảo địa chỉ này chính xác với cấu hình của bạn
KAFKA_BOOTSTRAP_SERVERS = "18.175.97.243:31880"

# ===============================
# Danh sách loại bất động sản
# ===============================
# Index sẽ tự động chạy từ 0 tương ứng với thứ tự trong list
ESTATE_TYPES = [
    "nhamatpho",  # Index 0
    "nharieng",   # Index 1
    "chungcu",    # Index 2
    "bietthu",    # Index 3
    # Các loại khác (bỏ comment nếu muốn chạy)
    # "datbietthu_batch",
    # "datmatpho_batch",
    # ...
]

# File chứa danh sách tỉnh thành (đảm bảo file này nằm cùng thư mục)
PROVINCES_FILE = os.path.join("/", "mnt", "e", "hung", "project", "bigdata", "src", "crawlerbds", "provinces.json")
OUTPUT_ROOT_DIR = 'crawled_data'

def main():
    # 1. Kiểm tra và đọc file provinces.json
    if not os.path.exists(PROVINCES_FILE):
        print(f"❌ Lỗi: Không tìm thấy file '{PROVINCES_FILE}' tại thư mục hiện tại.")
        return

    try:
        with open(PROVINCES_FILE, 'r', encoding='utf-8') as f:
            provinces = json.load(f)
    except json.JSONDecodeError:
        print(f"❌ Lỗi: File '{PROVINCES_FILE}' không đúng định dạng JSON.")
        return

    total_provinces = len(provinces)

    # 2. Vòng lặp qua từng loại BĐS (Outer Loop)
    # enumerate giúp lấy cả index (0,1,2...) và giá trị (nhamatpho, nharieng...)
    for estate_type_idx, kafka_topic in enumerate(ESTATE_TYPES):
        print("=" * 50)
        print(f"▶️  Bắt đầu crawl loại BĐS: {kafka_topic} (estate_type = {estate_type_idx})")
        print("=" * 50)

        # 3. Vòng lặp qua từng tỉnh (Inner Loop)
        for count, province in enumerate(provinces, 1):
            slug = province.get('slug')
            name = province.get('name')

            if not slug:
                print(f"⚠️ Cảnh báo: Dữ liệu tỉnh thiếu slug, bỏ qua. (Data: {province})")
                continue

            print(f"[{count}/{total_provinces}] Đang crawl: {name} ({slug})")

            # Tạo thư mục output: crawled_data/{slug}
            output_dir = os.path.join(OUTPUT_ROOT_DIR, slug)
            os.makedirs(output_dir, exist_ok=True)

            # Đường dẫn file output JSON
            output_filename = f"{SPIDER_NAME}_{slug}_{kafka_topic}.json"
            output_path = os.path.join(output_dir, output_filename)

            # Xây dựng câu lệnh Scrapy
            # Tương đương với: scrapy crawl ... -a ... -s ...
            cmd = [
                "scrapy", "crawl", SPIDER_NAME,
                "-a", f"min_page={MIN_PAGE}",
                "-a", f"max_page={MAX_PAGE}",
                "-a", f"province={slug}",
                "-a", f"jump_to_page={JUMP_TO_PAGE}",
                "-a", f"estate_type={estate_type_idx}",
                "-O", output_path,          # -O viết hoa để ghi đè (overwrite), dùng -o để nối (append)
                "-s", "DOWNLOAD_DELAY=5",
                "-s", f"KAFKA_BOOTSTRAP_SERVERS={KAFKA_BOOTSTRAP_SERVERS}",
                "-s", f"KAFKA_TOPIC={kafka_topic}"
            ]

            # Thực thi lệnh
            try:
                # subprocess.run chờ lệnh chạy xong mới đi tiếp
                subprocess.run(cmd, check=True) 
                print(f"✅ Hoàn thành: {name}\n")
            except subprocess.CalledProcessError as e:
                print(f"❌ Lỗi khi chạy Scrapy cho {name}: {e}\n")
            except FileNotFoundError:
                print("❌ Lỗi: Không tìm thấy lệnh 'scrapy'. Hãy chắc chắn bạn đã kích hoạt môi trường ảo (virtualenv).\n")
                return

            # Sleep 2 giây giữa các lần crawl tỉnh
            time.sleep(2)

        print(f"🎯 Hoàn tất crawl cho loại BĐS: {kafka_topic}\n")

    print("🏁 Toàn bộ quá trình crawl đã hoàn tất!")

if __name__ == "__main__":
    main()