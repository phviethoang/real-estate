# Base Image có sẵn Python và các công cụ cơ bản
FROM python:3.10-slim-bullseye

# 1. CÀI ĐẶT JAVA( OpenJDK 17) VÀ CÁC CÔNG CỤ CƠ BẢN
RUN apt-get update && \
    apt-get install -y openjdk-17-jre-headless procps curl && \
    rm -rf /var/lib/apt/lists/*

# 2. THIẾT LẬP BIẾN MÔI TRƯỜNG CHO JAVA (FIX LỖI JAVA_HOME)
# /usr/lib/jvm/java-17-openjdk-amd64 là đường dẫn chuẩn sau khi apt-get install
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH

# 3. CÀI ĐẶT CÁC THƯ VIỆN PYTHON (PYSPARK)
# Thiết lập thư mục làm việc trong Container
WORKDIR /app

# Copy file requirements.txt vào thư mục làm việc
COPY requirements.txt .

# Cài đặt thư viện (Bao gồm pyspark)
RUN pip install --no-cache-dir -r requirements.txt

RUN curl -fL -o /usr/local/lib/python3.10/site-packages/pyspark/jars/spark-sql-kafka-0-10_2.12-3.4.1.jar https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/3.4.1/spark-sql-kafka-0-10_2.12-3.4.1.jar && \
    curl -fL -o /usr/local/lib/python3.10/site-packages/pyspark/jars/spark-token-provider-kafka-0-10_2.12-3.4.1.jar https://repo1.maven.org/maven2/org/apache/spark/spark-token-provider-kafka-0-10_2.12/3.4.1/spark-token-provider-kafka-0-10_2.12-3.4.1.jar && \
    curl -fL -o /usr/local/lib/python3.10/site-packages/pyspark/jars/kafka-clients-3.3.2.jar https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.3.2/kafka-clients-3.3.2.jar && \
    curl -fL -o /usr/local/lib/python3.10/site-packages/pyspark/jars/commons-pool2-2.11.1.jar https://repo1.maven.org/maven2/org/apache/commons/commons-pool2/2.11.1/commons-pool2-2.11.1.jar && \
    # ElasticSearch giữ nguyên (tương thích tốt với Spark 3.4)
    curl -fL -o /usr/local/lib/python3.10/site-packages/pyspark/jars/elasticsearch-spark-30_2.12-8.13.4.jar https://repo1.maven.org/maven2/org/elasticsearch/elasticsearch-spark-30_2.12/8.13.4/elasticsearch-spark-30_2.12-8.13.4.jar \
    curl -fL -o /usr/local/lib/python3.10/site-packages/pyspark/jars/hadoop-aws-3.3.4.jar https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar && \
    curl -fL -o /usr/local/lib/python3.10/site-packages/pyspark/jars/aws-java-sdk-bundle-1.12.262.jar https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.262/aws-java-sdk-bundle-1.12.262.jar

# 4. COPY CODE
# Copy các file code của bạn vào Container
COPY main.py .
# (Nếu có các file code khác như config.py, hãy thêm vào đây)

# 5. LỆNH CHẠY (ENTRYPOINT)
# Lệnh này sẽ được thực thi khi Container khởi động
CMD ["python3", "main.py"]