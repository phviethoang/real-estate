# #!/bin/bash

# # Crawler parameters
# spider_name="bds68_spider"
# min_page=1
# max_page=10000
# province="ho-chi-minh"
# jump_to_page=1
# estate_type=0 # 0: nhamatpho, 1: nharieng, 2: chungcu, 3: bietthu


# # Kafka parameters
# kafka_bootstrap_servers="34.72.171.207:9192,34.72.171.207:9292,34.72.171.207:9392"
# kafka_topic="nhatmatpho_batch"  #nhamatpho_batch, nharieng_batch, chungcu_batch, bietthu_batch

# # Run crawler
# scrapy crawl "$spider_name" \
#     -a min_page="$min_page" \
#     -a max_page="$max_page" \
#     -a province="$province" \
#     -a jump_to_page="$jump_to_page" \
#     -a estate_type="$estate_type" \
#     -O "${spider_name}_${province}_${kafka_topic}.json" \
#     -s DOWNLOAD_DELAY=5 \
#     -s KAFKA_BOOTSTRAP_SERVERS="$kafka_bootstrap_servers" \
#     -s KAFKA_TOPIC="$kafka_topic"


#CRAWL TOÀN BỘ CÁC TỈNH ĐỐI VỚI 1 ESTATE TYPE
#!/bin/bash

# # Crawler parameters
# spider_name="bds68_spider"
# min_page=1
# max_page=10000
# jump_to_page=1
# estate_type=3 # 0: nhamatpho, 1: nharieng, 2: chungcu, 3: bietthu

# # Kafka parameters
# kafka_bootstrap_servers="34.72.171.207:9192,34.72.171.207:9292,34.72.171.207:9392"
# kafka_topic="bietthu_batch"  #nhamatpho_batch, nharieng_batch, chungcu_batch, bietthu_batch

# # Đếm tổng số tỉnh
# total=$(jq length provinces.json)
# count=0

# # Lặp qua từng tỉnh trong file JSON
# jq -c '.[]' provinces.json | while read -r province; do
#   count=$((count + 1))
#   slug=$(echo "$province" | jq -r '.slug')
#   name=$(echo "$province" | jq -r '.name')

#   echo "[${count}/${total}] Đang crawl: $name ($slug)"
#   mkdir -p "crawled_data/$slug"

#   scrapy crawl "$spider_name" \
#     -a min_page="$min_page" \
#     -a max_page="$max_page" \
#     -a province="$slug" \
#     -a jump_to_page="$jump_to_page" \
#     -a estate_type="$estate_type" \
#     -O "crawled_data/${slug}/${spider_name}_${slug}_${kafka_topic}.json" \
#     -s DOWNLOAD_DELAY=5 \
#     -s KAFKA_BOOTSTRAP_SERVERS="$kafka_bootstrap_servers" \
#     -s KAFKA_TOPIC="$kafka_topic"

#   echo "✅ Hoàn thành: $name"
#   echo ""
#   sleep 2
# done

# echo "Toàn bộ crawl đã hoàn tất!"


#CRAWL TOÀN BỘ CÁC TỈNH ĐỐI VỚI TOÀN BỘ CÁC ESTATE TYPE

#tmux bigdata: 4-9
#tmux bigdata2: 10-12
#tmux bigdata3: 13-17
#!/bin/bash

# ===============================
# Crawler parameters
# ===============================
spider_name="bds68_spider"
min_page=1
max_page=10000
jump_to_page=1

# ===============================
# Kafka parameters
# ===============================
kafka_bootstrap_servers="34.72.171.207:9192,34.72.171.207:9292,34.72.171.207:9392"

# ===============================
# Danh sách loại bất động sản
# ===============================
declare -a estate_types=(
  # "nhamatpho_batch"     #0
  # "nharieng_batch"      #1
  # "chungcu_batch"       #2
  # "bietthu_batch"       #3
  # "datbietthu_batch"    #4
  # "datmatpho_batch"     #5
  # "datrieng_batch"      #6
  # "dattrangtrai_batch"  #7
  # "khoxuong_batch"      #8
  # "nhadatkhac_batch"    #9
  # "thuechungcu_batch"   #10
  # "thuenharieng_batch"  #11
  # "thuenhamatpho_batch" #12
  "thuevanphong_batch"  #13
  "thuecuahang_batch"   #14
  "thuekho_batch"       #15
  "thuenhatro_batch"    #16
  "thuekhac_batch"      #17
)

# ===============================
# Crawl toàn bộ loại BĐS
# ===============================
estate_type=13

for kafka_topic in "${estate_types[@]}"; do
  echo "=========================================="
  echo "▶️  Bắt đầu crawl loại BĐS: $kafka_topic (estate_type = $estate_type)"
  echo "=========================================="

  # Đếm tổng số tỉnh
  total=$(jq length provinces.json)
  count=0

  # Lặp qua từng tỉnh trong file JSON
  jq -c '.[]' provinces.json | while read -r province; do
    count=$((count + 1))
    slug=$(echo "$province" | jq -r '.slug')
    name=$(echo "$province" | jq -r '.name')

    echo "[${count}/${total}] Đang crawl: $name ($slug)"
    mkdir -p "crawled_data/$slug"

    scrapy crawl "$spider_name" \
      -a min_page="$min_page" \
      -a max_page="$max_page" \
      -a province="$slug" \
      -a jump_to_page="$jump_to_page" \
      -a estate_type="$estate_type" \
      -O "crawled_data/${slug}/${spider_name}_${slug}_${kafka_topic}.json" \
      -s DOWNLOAD_DELAY=5 \
      -s KAFKA_BOOTSTRAP_SERVERS="$kafka_bootstrap_servers" \
      -s KAFKA_TOPIC="$kafka_topic"

    echo "✅ Hoàn thành: $name"
    echo ""
    sleep 2
  done

  echo "🎯 Hoàn tất crawl cho loại BĐS: $kafka_topic"
  echo ""
  estate_type=$((estate_type + 1))
done

echo "🏁 Toàn bộ crawl đã hoàn tất cho tất cả các loại BĐS!"
