#!/bin/bash

# Crawler parameters
spider_name="bds_spider"
min_page=1
max_page=10000
jump_to_page=1
estate_type=2

# Kafka parameters
kafka_bootstrap_servers="34.72.171.207:9192,34.72.171.207:9292,34.72.171.207:9392"
kafka_topic="chungcu_batch"

# Danh sách tỉnh (slug: tên hiển thị)
declare -A provinces=(
    ["ha-giang"]="Hà Giang"
    ["cao-bang"]="Cao Bằng"
    ["bac-kan"]="Bắc Kạn"
    ["tuyen-quang"]="Tuyên Quang"
    ["lao-cai"]="Lào Cai"
    ["dien-bien"]="Điện Biên"
    ["lai-chau"]="Lai Châu"
    ["son-la"]="Sơn La"
    ["yen-bai"]="Yên Bái"
    ["hoa-binh"]="Hòa Bình"
    ["thai-nguyen"]="Thái Nguyên"
    ["lang-son"]="Lạng Sơn"
    ["quang-ninh"]="Quảng Ninh"
    ["bac-giang"]="Bắc Giang"
    ["phu-tho"]="Phú Thọ"
    ["vinh-phuc"]="Vĩnh Phúc"
    ["bac-ninh"]="Bắc Ninh"
    ["hai-duong"]="Hải Dương"
    ["hai-phong"]="Hải Phòng"
    ["hung-yen"]="Hưng Yên"
    ["thai-binh"]="Thái Bình"
    ["ha-nam"]="Hà Nam"
    ["nam-dinh"]="Nam Định"
    ["ninh-binh"]="Ninh Bình"
    ["thanh-hoa"]="Thanh Hóa"
    ["nghe-an"]="Nghệ An"
    ["ha-tinh"]="Hà Tĩnh"
    ["quang-binh"]="Quảng Bình"
    ["quang-tri"]="Quảng Trị"
    ["thua-thien-hue"]="Thừa Thiên Huế"
    ["da-nang"]="Đà Nẵng"
    ["quang-nam"]="Quảng Nam"
    ["quang-ngai"]="Quảng Ngãi"
    ["binh-dinh"]="Bình Định"
    ["phu-yen"]="Phú Yên"
    ["khanh-hoa"]="Khánh Hòa"
    ["ninh-thuan"]="Ninh Thuận"
    ["binh-thuan"]="Bình Thuận"
    ["kon-tum"]="Kon Tum"
    ["gia-lai"]="Gia Lai"
    ["dak-lak"]="Đắk Lắk"
    ["dak-nong"]="Đắk Nông"
    ["lam-dong"]="Lâm Đồng"
    ["binh-phuoc"]="Bình Phước"
    ["tay-ninh"]="Tây Ninh"
    ["binh-duong"]="Bình Dương"
    ["dong-nai"]="Đồng Nai"
    ["ba-ria-vung-tau"]="Bà Rịa - Vũng Tàu"
    ["tp-ho-chi-minh"]="TP. Hồ Chí Minh"
    ["long-an"]="Long An"
    ["tien-giang"]="Tiền Giang"
    ["ben-tre"]="Bến Tre"
    ["tra-vinh"]="Trà Vinh"
    ["vinh-long"]="Vĩnh Long"
    ["dong-thap"]="Đồng Tháp"
    ["an-giang"]="An Giang"
    ["kien-giang"]="Kiên Giang"
    ["can-tho"]="Cần Thơ"
    ["hau-giang"]="Hậu Giang"
    ["soc-trang"]="Sóc Trăng"
    ["bac-lieu"]="Bạc Liêu"
    ["ca-mau"]="Cà Mau"
)

# Chạy qua tất cả các tỉnh
for province in "${!provinces[@]}"; do
    echo "==============================="
    echo "Đang crawl: ${provinces[$province]} ($province)"
    echo "==============================="

    scrapy crawl "$spider_name" \
        -a min_page="$min_page" \
        -a max_page="$max_page" \
        -a province="$province" \
        -a jump_to_page="$jump_to_page" \
        -a estate_type="$estate_type" \
        -O "${spider_name}_${province}_${kafka_topic}.json" \
        -s DOWNLOAD_DELAY=5 \
        -s KAFKA_BOOTSTRAP_SERVERS="$kafka_bootstrap_servers" \
        -s KAFKA_TOPIC="$kafka_topic"

    echo "Hoàn thành: ${provinces[$province]}"
    echo ""
done

echo "Toàn bộ crawl đã hoàn tất!"
