# **DEPLOY SERVING LAYER**
<br><br>

Serving Layer is the layer directly providing information to users. Users need to know about information in history, but, storing in database like HDFS costs so much time and resources to retrieval. Therefore,Serving Layer is responsible for storing data more logically and providing algorithms of retrievaling faster. However, what serving layer stores can not replace the whole data in database( HDFS), serving layer only saves the data selected and processed by spark stream and spark batch, not all data. 

Here, use `Elastic Search` for serving layer.

#### **Structure of Elastic Search**

Elastic Search uses `Index` to store items related to each other. `Index` of Elastic Search is simillar with the `Topic` in Kafka.

What `Index` saves are `Document`s. They are *Json object* containing the information.

To visualize data in `Elastic search`, use `Kibana`. **Kibana** is a web application sending requests to Elastic Search for retrievaling and then receiving responses for visualization.

## **===1| Install operator**

**Operator** here is **ECK Operator**, for installing:

* Create namespace:
    ```bash
    kubectl create namespace elastic
    ```

* Install operator in **Master Node** of Kubernete system:
    ```bash
    # Install CRDs( Custom Resource Definition)
    kubectl create -f https://download.elastic.co/downloads/eck/2.10.0/crds.yaml -n elastic

    # Install operator
    kubectl apply -f https://download.elastic.co/downloads/eck/2.10.0/operator.yaml 
    ```
* Ensure the operator pod being created and running successfully:
    ```bash
    kubeclt  get pod -n elastic
    ```
    ---> The result should show the operator pod with status being `Running`
## **===2| Create elastic search pod**
Create configuration file `yaml` to set up `elastic search` 

* Create `yaml` file:
    ```bash
    sudo nano elastic.yaml
    ```
* Config the content in file:
    ```yaml
    # --- Elasticsearch Cluster ---
    apiVersion: elasticsearch.k8s.elastic.co/v1
    kind: Elasticsearch
    metadata:
        name: my-es-cluster
        namespace: elastic
    spec:
        version: 8.11.1
        http:
            tls:
                selfSignedCertificate:
                    disable: true # allow http instead of https
        nodeSets:
        - name: default
          count: 1 # CHỈ CHẠY 1 NODE
          config:
            # Tắt swap và mmap để tránh lỗi trên node nhỏ
            node.store.allow_mmap: false
          podTemplate:
            spec:
              containers:
              - name: elasticsearch
              # GIỚI HẠN TÀI NGUYÊN CỨNG
                resources:
                    limits:
                        memory: 2Gi
                    requests:
                        memory: 2Gi
                env:
                # Cấu hình Java Heap Size (Quan trọng nhất)
                - name: ES_JAVA_OPTS
                  value: "-Xms1g -Xmx1g"
          volumeClaimTemplates:
          - metadata:
                name: elasticsearch-data
            spec:
                accessModes:
                - ReadWriteOnce
                resources:
                    requests:
                        storage: 10Gi # Cấp 10GB ổ cứng
                storageClassName: gp3
    ```
* Apply the configuration:
    ```bash
    kubectl apply -f elastic.yaml -n elastic
    ```
* Waiting for a few minutes, ensure the pod being created:
    ```bash
    kubectl get pod -n elastic
    ```
    --> the result should show pod elastic with the status being `Running`

## **===3| Create Kibana pod**

* Create `yaml` file:
    ```bash
    sudo nano kibana.yaml
    ```
* Config the content in file:
    ```yaml
    apiVersion: kibana.k8s.elastic.co/v1
    kind: Kibana
    metadata:
        name: my-kibana
        namespace: kafka
    spec:
        version: 8.11.1
        count: 1
        elasticsearchRef:
            name: my-es-cluster
        http:
            # Mở cổng NodePort để truy cập từ bên ngoài
            service:
                spec:
                    type: NodePort
            tls:
                selfSignedCertificate:
                    disabled: true # Tắt HTTPS cho Kibana để truy cập dễ hơn (chỉ cho Lab)
    ```

* Apply the configuration:
    ```bash
    kubectl apply -f kibana.yaml -n elastic
    ```

* Confirm the creation:
    ```bash
    kubectl get pods -n elastic
    ```
    --> the result should show the in status `Running`

## **===4| Get the password and port**

To allow other pods to connect, elastic provides *service*. To get this:

* Get service, so that the spark can connect:
    ```bash
    kubectl get service -n elastic
    ```
    --> There are several services shown like:
    * `my-es-cluster-es-default`
    * `my-es-cluster-es-http`
    * `my-es-cluster-es-internal-http`
    * `my-es-cluster-es-transport`
    --> Remember `my-es-cluster-es-http`

* However, the service provided is just for pod in LAN to access, but not allow local application ( like local spark to access). So, the service needs to be exposed to a port of instance, so that elastic can listen to access from global including from local spark:
    ```bash
    # Expose service ES ra NodePort
    kubectl expose service <service_name> --type=NodePort --name=es-external -n elastic --dry-run=client -o yaml | kubectl apply -f -

    # Xem cổng
    kubectl get svc es-external -n kafka
    # --> This instruction will create new service name es-external with a map 'localport: publicport/TCP' like '9092:30878/TCP'
    ```
* Config security group to allow TCP request accessing the exposed port( like port `30878`)

To allow user can view data, **Kibana** provides *password* and *port*. To get these:

* Get password:
    * Password is stored in a "secret" - which is a resource of Kubernete. View all secrets in namespace:
        ```bash
        kubectl get secret -n elastic
        ```
        --> The result will show several of secret, the most important secret is the one with name being `<elastic_search_cluster_name>-es-elastic-user`
        --> Remember this secret
    * Get the password:
        ```bash
        kubectl get secret <secret_name> -n elastic -o go-template='{{.data.elastic | base64decode}}' && echo
        ```
        --> remember the password
* Get port:
    ```bash
    # View all ports
    kubectl get svc -n elastic
    ```
    --> The result shows several services with corresponding port
    --> The most important service is the one with name being `<kibana_name>-kb-http`, and its port is `localport: publicport/TCP` (like `5601:32302/TCP`)
    --> Remember the public port

## **===5| Config Security Group in AWS**

Config to allow TCP through the public port of elastic and kibana

## **===6| Check the creation**

* Access Kibana by: http://<PUBLIC_IP_NODE>:<PORT_KIBANA>
* Log in: username: `elastic`( default), password: the password at step 4
--> User should access Kibana successfully

## **===7| Test passing data from Spark to Elastic Search**

View file `SparkToES.md`

* Install `pyspark`
    ```bash
    pip install pyspark
    ```
* Add a new instruction to Dockerfile to download package of elasticsearch:
    ```Dockerfile
    RUN curl -o /usr/local/lib/python3.10/site-packages/pyspark/jars/elasticsearch-spark-30_2.12-8.13.4.jar https://repo1.maven.org/maven2/org/elasticsearch/elasticsearch-spark-30_2.12/8.13.4/elasticsearch-spark-30_2.12-8.13.4.jar
    ```

* Create file `spark-job.py` and config:
    ```python
    ES_HOST = "PUBLIC_IP_OF_INSTANCE"
    ES_PORT = "PUBLIC_PORT_OF_ELASTIC_SEARCH"
    ES_USER = "elastic"
    ES_PASS = "PASSWORD"
    ES_INDEX= "test_index" # Index that receives the data from spark
    DRIVER_MEMORY = os.getenv("SPARK_DRIVER_MEMORY", "1g") # Maximum memory for spark job, this is for ensuring the resource of the pod
    ```

* Initialize `Spark Session`
    ```python
    from pyspark.sql import SparkSession

    spark = SparkSession.builder \
                .appName("SparkStreaming")\
                .config("spark.driver.extraJavaOptions", "-Djava.security.properties=")\
                .config("spark.executor.extraJavaOptions", "-Djava.security.properties=")\
                .config("spark.driver.memory", DRIVER_MEMORY)\
                .getOrCreate()
    ```
* Create Dataframe before sending data to elastic search
    ```python
    raw_data = [["Alice", 25, "No"],["Chishiya", 25, "Doctor"]] 

    # [1] - create spark dataframe with list of data and list of columns
    df = spark.createDataFrame(raw_data, ["name", "age", "career"])

    # [2] - create spark dataframe from pandas dataframe
    import pandas as pd
    pd_df = pd.DataFrame([
        ["name", "age", "career"],
        raw_data
    ])
    df = spark.creteDataFrame(pd_df)

    # [3] - create spark dataframe with Schema (professional)
    from pyspark.sql.types import StructType, StructField, StringType, IntergerType

    # [3.1] - Define new schema( Define columns in SQL: name of column, type of data in column, is null,...)
    schema = StructType([
        StructField("name", StringType(), True),
        StructField("age", IntergerType(),True),
        StructField("career", StringType(),True)
    ])

    # [3.2] - Create dataframe with schema
    df = spark.createDataFrame(raw_data, schema = schema)
    ```

* Send data to Elastic Search:
    ```python
    try:
        result = df.writeStream\
            .format("org.elasticsearch.spark.sql")\
            .outputMode("append")\
            .option("es.resource", ES_INDEX)\
            .option("es.nodes",              ES_HOST)\
            .option("es.port",               ES_PORT)\
            .option("es.net.http.auth.user", ES_USER)\
            .option("es.net.http.auth.pass", ES_PASS)\
            .option("es.nodes.wan.only",     "true") \
            .option("checkpointLocation", "/tmp/spark-checkpoint-es") \ 
            .start()
        result.awaitTermination()
        print("[DONE] Successfully write data into elastic search with index {}".format(ES_INDEX))
    except Exception as e:
        print("[FAIL] Error when writing data: {}".format(e))
    ```

* Check the data is sent successfully:
    * Access the link `http://<PUBLIC_IP_OF_INSTANCE>:<PUBLIC_PORT_OF_ELASTIC_SEARCH>/<NAME_OF_INDEX>/_search
    * Input username and password if required
    * The data shoule be shown, that means spark has sent successfully and the Elastic Search can receive data

