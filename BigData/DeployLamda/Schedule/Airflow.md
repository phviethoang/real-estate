# **SCHEDULE - AIRFLOW**

Crawler which gets data from data sources( like webs) should not be always run because of resources waste. Insteads, it is more appropriate to schedule the crawler to run periodly for getting the up-to-date news.

Simillarly, batch processing is also a heavy job which requires to load all of history, so it should be scheduled to run periodly, too.

The tool for scheduling used here is `Airflow`.

#### **How does Airflow can control the pod in K8s?**

## **===1| Install Airflow**

* Create virtual environment
  ```bash
  # Create virtual environment airflow
  python -m venv airflow

  # Activate
  .\airflow\scripts\activate
  ```

* Install Airflow
  ```bash
  pip install "apache-airflow[cncf.kubernetes]" pandas requests
  ```

* Init :
  ```bash
  export AIRFLOW_HOME=~/airflow
  airflow db init
  airflow users create --username <set_username> ` # Any, unimportant, but should be easy to remember
    --firstname <set_firstname>`                   # Any, unimportant
    --lastname <set_lastname>`                     # Any, unimportant
    --role <set_role:Admin>                        # Must be Admin to have right to controll Airflow
    --email <set_email>                            # Any, unimportant
    --password <set_password>                      # Any, unimportant, but should be easy to remember
  ```

* Run airflow:
  ```bash
  airflow schedule
  airflow webserver -p <port: 8080> # This will allow to access an interface of Airflow in port 8080,
                                    # with this interface, we can run DAG that airflow manages
  ```
## **===2| Prepare for controlling**

To let `Airflow` can control k8s and run batch processing job, it must be provided with permission. To get permission in k8s system:
* In master node, open file `/etc/kubernetes/admin.conf`, and copy its content
* Create a file `config`( or `config.yaml` or `config.conf`,.... no matter what the extension is) in local and paste the content
* Find the line :`server: http://192.168.x.x:6443` --> change to `server: http://<public_ip_of_ec2>:6443`
* Save file

To let `Airflow` run batch processing job, the job must be built to be a Docker image. The main idea is that `Airflow` accesses to k8s and periodly create new batch processing job with the image built, but not rerun the current pod

## **===3| Logic of scheduling**

In this step, we will determine which is run first, which is run later, how often they are run,.... Create a python file and code:
* Import:
  ```python
  from airflow import DAG
  from airflow.operators.bash import BashOperator
  from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
  from datetime import datetime, timedelta
  ```
* Config: Get preparation
  ```python
  k8s_config = <path_to_local_config_file_in_step_2>
  local_crawler = <path_to_local_code_crawler>

  default_args = {
    'owner': 'hdoan',                    # Any: who can modify DAG
    'retries': 1,                        # Number of retries if the task is fail
    'retry_delay': timedelta(minutes=5), # Delay between 2 retries
  }
  ```
* Define logic: A job in airflow is defined with a DAG: (DAG name, description, ....)
  ```python
  # Define DAG
  with DAG(
    <name_of_dag>,
    default_args=default_args,
    description='Local Crawler -> Remote Spark Batch',
    schedule_interval='0 0 * * *',  # Chạy lúc 00:00 hàng ngày
    start_date=datetime(2023, 12, 21),
    catchup=False,
  ) as dag:
    # TASK 1: Schedule for local crawler
    # Use BashOperator to run application in local bash
    run_crawler = BashOperator(
          task_id = "run_local_crawler",
          bash_command = f" python {local_crawler}"
      )
    # TASK 2: Schedule for remote batch processing job in k8s
    # Use KubernetesPodOperator to run batch processing job in k8s
    run_spark_batch = KubernetesPodOperator(
        task_id="trigger_remote_spark_batch",
        name="spark-batch-job",
        namespace="application", # Namespace chứa MinIO/ES
        
        # Dùng Image v7 vừa build (có chứa code batch)
        image="hdoan043/sparkstreaming:v7",
        image_pull_policy="Always",
        
        # Remote Control Config
        config_file=KUBE_CONFIG_PATH,
        in_cluster=False,
        
        cmds=["spark-submit"],
        arguments=[
            "--master", "local[*]",
            "--driver-memory", "2g",
            "/app/batch_processing.py" # Code đã nằm trong image nhờ lệnh COPY ở Bước 1
        ],
        
        # Biến môi trường (Dùng tên Service nội bộ K8s vì Pod chạy trong K8s)
        env_vars={
            "MINIO_HOST": "http://minio-service.minio.svc.cluster.local:9000",
            "MINIO_USER": "bigdata123",
            "MINIO_PASSWORD": "bigdata123",
            "MINIO_BUCKET": "bds",
            "ES_HOST": "http://my-es-cluster-es-http.elastic.svc.cluster.local",
            "ES_PORT": "9200",
            "ES_USER": "elastic",
            "ES_PASS": "83zobLJ9694Ww5qq982qcJYt",
        },
        
        get_logs=True,
        is_delete_operator_pod=True # Chạy xong tự xóa Pod để tiết kiệm RAM cho cluster
      )
      run_crawler >> run_spark_batch
    ```
## **===4| Check and run**

* Access `localhost:8080` --> access the Airflow interface
* Find the DAG with the name `<name_of_dag>`
* Click `ON`
* Click `TriggerDAG`
* Monitor: click task `trigger_<task_name>` --> `Logs`
  --> If log of the code batch processing job is shown, the batch processing job is run successfully.

