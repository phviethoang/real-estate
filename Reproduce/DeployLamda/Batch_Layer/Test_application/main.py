from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import StructType, StructField, StringType, IntegerType
import os

KAFKA_BOOTSTRAP_SERVER = os.getenv("KAFKA_BOOTSTRAP_SERVER", "my-cluster-kafka-bootstrap:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "my-topic")
DRIVER_MEMORY = os.getenv("SPARK_DRIVER_MEMORY", "2g")
MINIO_SERVICE = os.getenv("MINIO_HOST")
MINIO_USERNAME = os.getenv("MINIO_USER", "bigdata123")
MINIO_PASSWORD = os.getenv("MINIO_PASSWORD", "bigdata123")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "testbucket")


# Open spark session
print("[INIT] Start session...")
spark = SparkSession.builder \
        .appName("SparkStreaming")\
        .config("spark.driver.extraJavaOptions", "-Djava.security.properties=")\
        .config("spark.executor.extraJavaOptions", "-Djava.security.properties=")\
         \
        .config("spark.hadoop.fs.s3a.endpoint", MINIO_SERVICE) \
        .config("spark.hadoop.fs.s3a.access.key", MINIO_USERNAME) \
        .config("spark.hadoop.fs.s3a.secret.key", MINIO_PASSWORD) \
        .config("spark.hadoop.fs.s3a.path.style.access", "true") \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false") \
        .getOrCreate()
        
spark.sparkContext.setLogLevel("WARN")

print("[LOAD] Reading Kafka...")
df_raw = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVER)\
        .option("subscribe", KAFKA_TOPIC)\
        .option("startingOffsets", "earlies")\
        .load()
        
df_string = df_raw.selectExpr("CAST(key AS STRING)", "CAST(value AS STRING)")

print(f"Writing to MinIO at {MINIO_SERVICE} ...")

# --- 2. GHI VÀO ELASTICSEARCH (Sửa đoạn này) ---
try:
        query = df_string.writeStream \
                .format("parquet") \
                .option("path", "s3a://{}/kafka-data/".format(MINIO_BUCKET)) \
                .option("checkpointLocation", "s3a://{}/checkpoints/".format(MINIO_BUCKET)) \
                .outputMode("append") \
                .start()
        
        print("[DONE] Successfully write data into Elastic search at index: {}".format(MINIO_BUCKET))
        
        query.awaitTermination()

except Exception as e:
        print("[FAIL] Error when writing into ES: {}".format(e))
    
    # Lưu ý: Nếu ES có mật khẩu (X-Pack), thêm 2 dòng này:
    # .option("es.net.http.auth.user", "elastic") \
    # .option("es.net.http.auth.pass", "password_cua_ban") \