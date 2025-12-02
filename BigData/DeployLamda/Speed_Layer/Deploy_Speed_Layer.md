# **DEPLOY SPEED LAYER**
<br><br>

Here, we use Kafka for speed layer

## **===1| Set up Kafka**

See `Set_up_Kafka.md` to know

## **===2| Deploy application**

We have an application which plays role of producer to provide data for consumer application. And `Kafka` is a queue, which is responsible for temporarily storing data so that the producer can produce and send message unlimitedly without caring about the processing ability of the producer.

For sending and receiving messages in Kafka system, which is deployed in Kubenete, Kafka system provides an public address. This address is known by other pods in Kubernete so that they can send the message to the Kafka pod. 

Topic is also the important part in sending messages. The final destination of sending progress of producer is NOT the Kafka address, but the topic. The Kafka address is the physical gateway for communication among pods, while the topic is responsible for the logical managements: 
* The messages `basketball`, `football`, `messi`,... will be sent to topic `Sport`, the messages `AI`, `ML`, `NLP`, `CV`,... will be sent to topic `AI`,... but first, they must go through the gateway which is the Kafka public address

```txt
            data   
 Producer --------> [Kafka:public address] --------> Consumer
               Store    |   ^
             data from  |   | Provide data for
             Producer   V   |   Consumer
                    [Kafka system]
                 _________|___________
                 |        |          |
            Topic 1    Topic 2     Topic 3
```
In order to send messages to Kafka pod's address, producer application has to be coded with module `kafka`:
* Install module: `pip install kafka`
* Prepare for sending message:
    ```python
    from kafka import KafkaProducer
    import json

    # Config Bootstrap service( Kafka address)
    BOOTSTRAP_SERVERS = 'my-cluster-kafka-bootstrap:9092'
    TOPIC_NAME = 'my-topic'

    # Initialize Producer
    producer = KafkaProducer(
        bootstrap_servers=[BOOTSTRAP_SERVERS], # the address receiving messages
        value_serializer = lambda v: json.dumps(v).encode('utf-8') # type of data sent: here is json format
    )
    ```
* Send messages to kafka address:
    ```python
    # message
    # ( in json format or simple string )
    # ( if in json or complex format, the consumer application must have some mechanism to read)
    message = "Hello"

    # send to kafka address
    future = producer.send(
        TOPIC_NAME, 
        value=message
    )

* Wait and confirm that the message has reached the destination:
    ```python
    try: 
        record_metadata = future.get(timeout=10)
        print("Messages are sent to parition: {}".format(record_metadata))
    except Exception as e:
        print(e)
    ```

* End the sending progress:
    ```python
    producer.flush()
    producer.close()
    ```
## **===3| Encapsule the application**

Kafka system is running on Kubernete which manages its elements by the system of pods. Pod is an independent application like the apps on phone. Pods can also communicate with each other thanks to sending messages through pod service( public address). 

To send message to kafka system, the application must be run as a pod in Kubernet. Pod itself can run because it is a complete application, but not depend on the outside libraries like the python code file running on console. So that, firstly, we have to encapsule the producer programe into an application, which contains all things available for run independently.

* Suppose that the name of application file is `producer.py`, rename it into `main.py`

* Prepare file `requirements.txt`:
    * Create new `txt` file
    * List all the libraries that are used in code
    * Save the file into the same folder with the file `main.py`

* Encapsule the Programe by Encapsuler: Encapsule by `Docker` and `pack`
    * 1 - Install `Docker Desktop`
        * Access the link https://docs.docker.com/desktop/setup/install/windows-install/ and download Docker Desktop Installer for `Windows`
        * Follow the instruction to install `Docker Desktop`. In `Docker Desktop`, there is an engine named `Docker Engine` which is the most important part of the encapsulation
        * Confirm the installation: `docker --version`

    * 2 - Install `pack`:
        * Open `PowerShell` as administrator
        * Install `pack` by : `choco install pack`
        * Confirm the installation: `pack version`

    * 3 - Encapsule:
        * Open `Terminal` or `cmd`
        * Change to the working directory which contains the file `main.py`, `requirements.txt` and `Procfile`
        * Login in Docker Desktop, remember the username in Docker Desktop. Ensure the Docker Desktop running.
        * Run instruction:
            ```bash
            pack build <lower case of usename of Docker Desktop>/<name of image>:<version: v1/v2/.../latest> \
                --builder gcr.io/buildpacks/builder:v1 \
                --publish \
                --env GOOGLE_ENTRYPOINT="python main.py"
            ```
            --> Wait for minutes, then, there will be an announcement of success
        * Confirm the image being pushed successfully:
            * Access `Docker Hub`
            * Sign in
            * This should show the docker image that we have built
## **===4| Deploy the application on Kubernete**

This step is to create and run a pod on Kubernete system, this pod run an container with the image built.

* [1] - Config the file `yaml`:

    * Create a file `yaml` on virtual machine:
        ```bash
        sudo nano kafka-test.yaml
        ```
    * Config the file:
        ```yaml
        apiVersion: apps/v1
        kind: Deployment
        metadata:
            name: kafka-producer-deployment
            namespace: kafka  # Đảm bảo triển khai trong Namespace Kafka
            labels:
                app: kafka-producer
        spec:
            replicas: 1
            selector:
                matchLabels:
                    app: kafka-producer
            template:
                metadata:
                    labels:
                        app: kafka-producer
                spec:
                    containers:
                    - name: kafka-producer-container
                    # THAY THẾ: Sử dụng image bạn vừa push lên Docker Hub (hoặc Registry khác)
                      image: hdoan043/test-kafka:v1 
                    
                      # Đặt Biến Môi trường cho Kafka Broker
                      # Tên service Bootstrap Server của bạn là: my-cluster-kafka-bootstrap:9092
                      # (Dựa trên thông tin kết nối trong image_d5410d.png)
                      env:
                      - name: KAFKA_BROKERS
                        value: my-cluster-kafka-bootstrap:9092
                      - name: KAFKA_TOPIC
                        value: my-topic  # Thay thế bằng topic của bạn (ví dụ: raw-data-stream hoặc my-topic)
                    
                      # Nếu producer.py của bạn chạy trong vòng lặp vô hạn, 
                      # Container luôn chạy (Running)
                      resources:
                        limits:
                            memory: "128Mi"
                            cpu: "500m"
                        requests:
                            memory: "64Mi"
                            cpu: "250m"
        ```
    * Save the file by `CTRL + S`, exit by `CTRL + X`
* [2] - Apply the configuration:
    ```bash
    kubectl apply -f kafka-test.yaml -n <namespace>
    ```

    * Confirm by:
        ```bash
        kubectl get pod -n <namespace>
        ```
        --> The result should show the pod that we have configed and the status should be `Running`
    * When successfully created, the new pod will automatically run the container inside. Note that the container is non-interactive, this means we can not input text to it like in the console. 

## **===5| Deploy kafka application in local**

In this case: kubernete system where the kafa is deployed on is runnong on a group of instances on AWS. The target of this step is to make a Kafka producer application in local can send message to the kafka topic in remote Kafka topic on instances.

The progress of sending message to Kafka is shown in the figure:

```txt

               _______________REMOTE INSTANCE__________________
               |            ________________                  |                             
               | +----(2)-->|  Bootstrap   |-------+          |                                                        
               | |          |____port______|<--+   |          |                                         
               | |            |                |   |          |                                     
    +-->[ public_ip ]<---(3)--+                |  (2)         |           
    |    |  ^  |   |       ____________       (3)  |          |
    |   (3) |  |   |       |  Broker  |        |   V          |                     
    |    |  |  |   +-(4)-->|____port__|---->[Kafka Brokers]   |                                            
   (1)   |  |  |______________________________________________| 
    |    | (4)
    |    |  |
    |    v  |  _________LOCAL PRODUCER APPLICATION_____________                                               
    +----------|______________________________________________| 

    _ (1): Local producer sends data to the Kafka topic through the public ip at the bootstrap port for the 1st time
    _ (2): The data then is forward to KRaft which is managing the Kafka brokers
    _ (3): The KRaft sends back the response to the local producer application. 
           The response contains the metadata of the Kafka cluster: the brokers, topics, and the advertised port. 
           This is the port for helping the producer to send messages to brokers without through the bootstrap port
    _ (4): Finally, the producer application in local send directly message to Kafka topic through the received port
```

So that: we have to config:
* Add rule in security group of EC2( firewall) to allow all the TCP request( from source: `0.0.0.0/0`) to go through all port( this is for ensuring the instance can receive data from outside at the step (1) and (4)) 
* Config the broker use the `public_ip` of instance( not their private ip by default) as advertised address:
    * In the file config the cluster: add the `advirtisedHost` for each broker
        ```yaml
        spec:
            kafka:
                listeners:
                - name: external
                port: 9094
                type: nodeport
                tls: false
                # THÊM CẤU HÌNH configuration VÀ overrides Ở ĐÂY
                configuration:
                    bootstrap:
                        # Cấu hình địa chỉ quảng cáo cho Bootstrap Service
                        alternativeNames: ["3.10.139.221"] # (Tùy chọn, giúp client verify)
                    brokers:
                    # Cấu hình riêng cho TỪNG Broker để quảng cáo Public IP
                    - broker: 0
                    advertisedHost: "3.10.139.221"
                    - broker: 1
                    advertisedHost: "3.10.139.221"
                    - broker: 2
                    advertisedHost: "3.10.139.221"
        ```
    * Apply the configuration:
        ```bash
        kubectl apply -f <config_file_yaml> -n <namespace>
        ```
* At producer application local, the destination for sending message is `public_ip:<port>`
