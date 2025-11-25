# **DEPLOYING SPEED LAYER**
<br><br>


Using Kafka to deploying speed layer. Kafka is a queue, plays middle role between producers and consumers. Thanks to this queue storing the messages from producers temporarily, producers can send messages as much as possible but need not to care about the processing ability of consumers. 

## **===Step| 1**

Prepare for installing Kafka Operator:
* Create namespace for Kafka
    ```bash
    kubectl create namespace kafka
    ```

* Add link of repository of Kafka's operator( Kafka's operator is **Strimzi Operator**) to Helm store:
    ```bash
    helm repo add strimzi https://strimzi.io/charts/
    helm repo update
    ```

## **===Step| 2**
Install operator( strimzi operator):
```bash
# Install Strimzi Operator into Namespace 'kafka'
helm install strimzi-operator strimzi/strimzi-kafka-operator --namespace kafka

# Check if the operator pod has run successfully
kubectl get pods -n kafka
# --> The result should be 'strimzi-cluster-operator-...'
```

## **===Step| 3**

Define the design of Kafka: Create a `yaml` file to show our requirements of Kafka cluster ( name of cluster, namespace, how many zookeepers, how many brokers,...)
* Create a `yaml` file  
    ```bash
    sudo nano kafka.yaml
    ```
* In the `kafka.yaml` file, enter this content and save( parameters can be modified)
    ```
    # Config to create cluster
    apiVersion: kafka.strimzi.io/v1beta2
    kind: Kafka
    metadata:
        name: my-kafka-cluster
        namespace: kafka
    spec:
        kafka:
            version: 4.1.0
            listeners:
                # Listener to messages of Pods in K8s (such as Spark)
                - name: plain
                    port: 9092
                    type: internal
                    tls: false
                # Exteranl Listener to the output connection (optional)
                - name: external
                    port: 9094
                    type: nodeport # Use NodePort to access outside the K8s
                    tls: false
        entityOperator:
            topicOperator: {}
            userOperator: {}

    # Config to create brokers:
    apiVersion: kafka.strimzi.io/v1beta2
    kind: KafkaNodePool
    metadata:
        name: kafka-broker
        namespace: kafka
    spec:
        replicas: 3
        roles:
            - controller
            - broker
        storage:
            type: jbod
            volumes: 
                - id: 0
                type: persistent-claim
                size: 5Gi
    ```

## **===Step| 4**
Apply configuration:
```bash
kubectl apply -f kafka.yaml -n kafka
```

* Supervise the creation progress:
    ```bash
    # Get the state of Kafka Cluster
    kubectl get kafka -n kafka

    # Get the Pod Zookeeper and Kafka Broker being created
    kubectl get pods -n kafka
    ```

## **==Step| 5**
Create topics for data stream:
* Create a new `yaml` file to define topics in kafka:
    ```bash
    sudo nano kafka_topic.yaml
    ```
* Config the content of `yaml` file:
    ```yaml
    # kafka-topic.yaml
    apiVersion: kafka.strimzi.io/v1beta2
    kind: KafkaTopic
    metadata:
        name: raw-data-stream
        namespace: kafka
        labels:
            strimzi.io/cluster: my-kafka-cluster # Chỉ định Cluster Kafka nào sẽ tạo Topic này
    spec:
        partitions: 6  # number of partitions
        replicas: 3    # number of replicates( should be equal to the number of brokers)
    ```

* Apply the configuration:
    ```bash
    kubectl apply -f kafka-topic.yaml -n kafka
    ```

## **===Step| 6**

Test sending messages with kafka:

* When create a Kafka cluster successfully, **Strimzi** will provide a *service* to communicate with other pods in Kubernetes. *Service* is similar as the API: it is a public address known by other pods to access and send messages. To get the *service* of namespace <namespace>:
    ```bash
    kubectl get services -n <namespace>
    ```
    --> a table is shown which contains some field `NAME`, `TYPE`, `CLUSTER-IP`, `EXTERNAL-IP`, `PORT (s)`, `AGE`. The noticable row is one with the `NAME` including `bootstrap`. The service ( address) where the other pod can commnicate with kafka pod is created by concatnating 2 field: `NAME: PORT`( `PORT` is usually `9092`)

* Create a client pod, this pod will help us using the service of raw Kafka, including services for clients like *producer* and *customer*. Create the client pod in worker node only.
    ```bash
    kubectl run kafka-client --image=quay.io/strimzi/kafka:0.39.0-kafka-3.5.1 --namespace <namespace> --command -- sleep infinity
    ```

* Run pod and wait for the state being "Running"
    ```bash
    # to check if the pod is running
    kubectl get pod -n kafka
    ```
    --> The result should be a table with rows being the pods and their status in the namespace `kafka`, the columns are `NAME`, `READY`, `STATUS`, `RESTARTS`, `AGE`. And with the pod name `kafka-client`, the column `READY` should show `1/1` and the column `STATUS` should show `Running`. 

* Enter the shell inside the pod by:
    ```bash
    kubectl exec -it kafka-client -n kafka -- bash
    ```

Enter command `exit` to exit from the bash of client pod

* Open *consumer* and keep it running to waiting for the message: In the shell of the pod:
    ```bash
    /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server <service name: NAME: PORT>  --topic <topic name: here is raw-data-stream> --from-beginning
    ```
**NOTE:** `CTRL + C`  to exit

* Open *producer* to send messages: In the sell of the pod:
    ```bash
    /opt/kafka/bin/kafka-console-producer.sh --broker-list <service name: NAME: PORT> --topic <topic name: here is raw-data-stream>
    ```

**NOTE:** Input the text, `Enter` to send, `CTRL + C` to exit


