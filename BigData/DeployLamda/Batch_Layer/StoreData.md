# **STORE DATA INTO MINIO**
<br><br>

The pipeline of data is : Producer -> Kafka -> Minio. So, what connects `Kafka` and `Minio` to store data? There are several ways but here `Kafka Connection` will be used.

`Kafka Connection` is created to support `Kafka`: it plays role of deliver to transport data from `Kafka`- which is just a queue, not able to forward data - to `MinIO`.

<br>

###    **Pipeline**
* **[1] - Install plugin S3**
* **[2] - Deploy Infrastructure for kafka connection**
* [3] -

<br>

## **===1| Install plugin S3**

`Kafka Connection` requires plugin `S3` to work. However, Operator of Kafka - Strimzi Operator- is not equiped with `S3` by default, so plugin `S3` must be installed manually. The idea is that `S3` will be included in a container, that means we have to build an image encapsulate `S3` and push it to Docker Hub

* Create a file `Dockerfile` with no extension and config:
    ```Dockerfile
    # Giai đoạn 1: Giữ nguyên
    FROM confluentinc/cp-kafka-connect:7.5.0 AS builder
    RUN confluent-hub install --no-prompt confluentinc/kafka-connect-s3:10.5.0 \
        --component-dir /usr/share/confluent-hub-components

    # --- Giai đoạn 2: SỬA DÒNG NÀY ---
    # Dùng bản 3.7.1 chắc chắn tồn tại
    FROM quay.io/strimzi/kafka:0.48.0-kafka-4.0.0 
    USER root:root

    # Copy plugin (Giữ nguyên)
    RUN mkdir -p /opt/kafka/plugins/s3-sink
    COPY --from=builder /usr/share/confluent-hub-components/confluentinc-kafka-connect-s3 /opt/kafka/plugins/s3-sink

    USER 1001
    ```
* Build by:
    ```shell
    docker build -t <username_of_docker>/<name_of_image>:<tag: v1,v1,...> <path_to_folder_containing_dockerfile>
    ```
* Push into Docker Hub
    ```shell
    docker push <username_of_docker>/<name_of_image>:<tag: v1,v1,...>
    ```

## **===2| Deploy infrastructure for Kafka Connection**

Operator of Kafka - Strimzi Operator - needs to know some information to create Kafka Connection. 

* Create a `yaml` file:
    ```bash
    sudo nano kafka-connection-config.yaml
    ```
* Config:
    ```yaml
    apiVersion: kafka.strimzi.io/v1beta2
    kind: KafkaConnect
    metadata:
        name: my-connect-cluster                        # name of kafka-connection pod
        namespace: kafka
        annotations:
            strimzi.io/use-connector-resources: "true"
    spec:
        version: 4.0.0
        replicas: 1
        image: <username_of_docker>/<image_name>:<tag> # the image encapsulating S3
        bootstrapServers: name_of_kafka_service:port   # this is the service and port provided by kafka, kafka connection can know where to get data from
        readinessProbe:
            initialDelaySeconds: 60
            timeoutSeconds: 10
        livenessProbe:
            initialDelaySeconds: 60
            timeoutSeconds: 10
        config:
            key.converter: org.apache.kafka.connect.json.JsonConverter
            value.converter: org.apache.kafka.connect.json.JsonConverter
            key.converter.schemas.enable: false
            value.converter.schemas.enable: false
            group.id: connect-cluster
    ```
* Save file by `CTRL + S` and `CTRL + X` to quit
* Apply configuration:
    ```bash
    kubectl apply -f kafka-connection-config.yaml
    ```
* Confirm by:
    ```bash
    kubectl get pod -n kafka
    ```
    --> The result list should include the pod that we have created with the field `STATUS` being `Running` and the field `READY` being `1/1`

## **===3| Deploy job**
This is to allow the data can flow automatically from source ( Kafka) to destination( MinIO)

* Create a `yaml` file:
    ```bash
    sudo nano kafka-connection.yaml
    ```
* Config:
    ```yaml
    apiVersion: kafka.strimzi.io/v1beta2
    kind: KafkaConnector
    metadata:
        name: kafka-connection
        namespace: kafka
        labels:
            strimzi.io/cluster: my-connect-cluster # This must be the same as the name of KafkaConnection pod in step 2
    spec:
        class: io.confluent.connect.s3.S3SinkConnector
        tasksMax: 1
        config:
            topics: my-topic             # source topic that data comes from
            s3.bucket.name: data-lake   # the name of destination bucket in MinIO that the data reaches to
            store.url: http://<name_of_minio_service>:<internal_port> 
            # <name_of_minio_service> is the name of service that we have created and provided for MinIO pod, 
            # <internal_port> is the port that is defined in service and used for communicating with other pod
            storage.class: io.confluent.connect.s3.storage.S3Storage
            format.class: io.confluent.connect.s3.format.json.JsonFormat
            aws.access.key.id: <username_of_minio>
            aws.secret.access.key: <password_of_minio>
    ```
* Save file by `CTRL + S` and quit by `CTRL + X`
* Apply configuration:
    ```bash
    kubectl apply -f kafka-connection.yaml -n kafka
    ```





