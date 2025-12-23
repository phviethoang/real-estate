# **STORE DATA INTO MINIO**
<br><br>

The pipeline of data is : Producer -> Kafka -> Minio. So, what connects `Kafka` and `Minio` to store data? There are several ways but here `Spark streaming` will be used.

`Spark Streaming` will be deployed similarly as the one transporting data from Kafka to Elastic Search
<br>

###    **Pipeline**
* **[1] - Code spark**
* **[2] - Deploy application**

<br>

## **===1| Code Spark**

### ***Code Spark***

* Import:
    ```python
    from pyspark.sql.functions import from_json, col
    from pyspark.sql.types import StructType, StructField, StringType, IntegerType
    ```
* Get information:
    ```python
    KAFKA_BOOTSTRAP = 
    KAFKA_TOPIC = 
    MINIO_SERVICE = 
    MINIO_USERNAME = 
    MINIO_PASSWORD =
    BUCKET_NAME =  
    DRIVER_MEMORY = 
    ```
* Open a spark session:
    ```python
    spark = SparkSession.builder \
                .appName("SparkStreaming")\
                .config("spark.driver.extraJavaOptions", "-Djava.security.properties=")\
                .config("spark.executor.extraJavaOptions", "-Djava.security.properties=")\
                .config("spark.driver.memory", DRIVER_MEMORY)\
                \
                .config("spark.hadoop.fs.s3a.endpoint", MINIO_SERVICE) \
                .config("spark.hadoop.fs.s3a.access.key", MINIO_USERNAME) \
                .config("spark.hadoop.fs.s3a.secret.key", MINIO_PASSWORD) \
                .config("spark.hadoop.fs.s3a.path.style.access", "true") \
                .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
                .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false") \
                .getOrCreate()
    ```
* Read data from Kafka:
    ```python
    df_kafka = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP) \
        .option("subscribe", KAFKA_TOPIC) \
        .option("startingOffsets", "earliest") \
        .load()
    ```
* Parse data:
    ```python
    # Basic parse: parse string to string
    df_processed = df_kafka.selectExpr("CAST(key AS STRING)", "CAST(value AS STRING)")

    # (Tùy chọn) Nếu dữ liệu là JSON, bạn có thể parse struct tại đây
    # Create schema
    schema = StructType([StructField("name", StringType()), StructField("age", IntegerType())])
    # Parse to schema
    df_parsed = df_processed.select(from_json(col("value"), schema).alias("data")).select("data.*")
    ```

* Save to MinIO:
    ```python
    query = df_processed.writeStream \
        .format("parquet") \
        .option("path", "s3a://{}/kafka-data/".format(BUCKET_NAME)) \
        .option("checkpointLocation", "s3a://{}/checkpoints/".format(BUCKET_NAME)) \
        .outputMode("append") \
        .start()
    ```
* Close minio:
    ```python
    query.awaitTermination()
    ```

### ***Encapsulate***

* Dockerfile:
    ```Dockerfile
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
        curl -fL -o /usr/local/lib/python3.10/site-packages/pyspark/jars/elasticsearch-spark-30_2.12-8.13.4.jar https://repo1.maven.org/maven2/org/elasticsearch/elasticsearch-spark-30_2.12/8.13.4/elasticsearch-spark-30_2.12-8.13.4.jar

    # 4. COPY CODE
    # Copy các file code của bạn vào Container
    COPY main.py .
    # (Nếu có các file code khác như config.py, hãy thêm vào đây)

    # 5. LỆNH CHẠY (ENTRYPOINT)
    # Lệnh này sẽ được thực thi khi Container khởi động
    CMD ["python3", "main.py"]
    ```
* Build and push to Docker Hub with name: `username/image_name:tag_name`

## **===2| Deploy in Kubernete**

* Create a `yaml` file:
    ```bash
    sudo nano spark-to-minio.yaml
    ```
* Config:
    View `Config/test-spark-streaming.yaml`
* Save file by `CTRL + S` and `CTRL + X` to quit
* Apply configuration:
    ```bash
    kubectl apply -f spark-to-minio.yaml
    ```
* Confirm by:
    ```bash
    kubectl get pod -n kafka
    ```
    --> The result list should include the pod that we have created with the field `STATUS` being `Running` and the field `READY` being `1/1`


