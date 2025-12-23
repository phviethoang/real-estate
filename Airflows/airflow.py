from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from datetime import datetime, timedelta
import os

k8s_config = os.path.join("/","mnt","e","hung","project", "bigdata", "src", "airflows","config.yaml")
local_crawler = os.path.join("/","mnt","e","hung","project", "bigdata", "src", "crawlerbds","run_new.py")

default_args = {
    'owner': 'hdoan',                    # Any: who can modify DAG
    'retries': 1,                        # Number of retries if the task is fail
    'retry_delay': timedelta(minutes=5), # Delay between 2 retries
  }

with DAG(
    "Auto_crawl_and_batch_process",
    default_args=default_args,
    description='Local Crawler -> Remote Spark Batch',
    schedule='0 0 * * *',  # Chạy lúc 00:00 hàng ngày
    start_date=datetime(2023, 12, 21),
    catchup=False,
  ) as dag:
    # TASK 1: Schedule for local crawler
    # Use BashOperator to run application in local bash
    run_crawler = BashOperator(
          task_id = "run_local_crawler",
          bash_command = f"cd /mnt/e/hung/project/bigdata/src/crawlerbds && python {local_crawler}"
      )
    
    # TASK 2: Schedule for remote batch processing job in k8s
    # Use KubernetesPodOperator to run batch processing job in k8s
    run_spark_batch = KubernetesPodOperator(
        task_id="trigger_remote_spark_batch",
        name="spark-batch-job",
        namespace="application", # Namespace chứa MinIO/ES
        
        # Dùng Image v7 vừa build (có chứa code batch)
        image="hdoan043/sparkbatching:v3",
        image_pull_policy="Always",
        
        # Remote Control Config
        config_file=k8s_config,
        in_cluster=False,
        
        cmds=["spark-submit"],
        
        arguments=[
            "--master", "local[*]",
            "--driver-memory", "2g",
            
            # 2. Sửa đường dẫn file code cho khớp với Dockerfile
            # Dockerfile bạn dùng: COPY main.py . -> Nghĩa là file nằm ở /app/main.py
            "/app/main.py" 
        ],
        
        # Biến môi trường (Dùng tên Service nội bộ K8s vì Pod chạy trong K8s)
        env_vars={
            "ES_HOST": "my-es-cluster-es-http.elastic.svc.cluster.local",
            "ES_PORT": "9200",
            "ES_USER": "elastic",
            "ES_PASS": "83zobLJ9694Ww5qq982qcJYt",
            "MINIO_HOST": "http://minio-service.minio.svc.cluster.local:9000",
            "MINIO_USER": "bigdata123",
            "MINIO_PASSWORD": "bigdata123",
            "MINIO_BUCKET": "bds",
        },
        
        get_logs=True,
        is_delete_operator_pod=True # Chạy xong tự xóa Pod để tiết kiệm RAM cho cluster
      )
    
    # run task `run_crawler` first, after it done, run task `run_spark_batch` next
    run_crawler >> run_spark_batch