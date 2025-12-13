# **DEPLOY AN APPLICATION ON K8S SYSTEM**
<br><br>

## **===1| General**

K8s is a tool of containers management. It manages pods whichs are considered as applications. Pod contains container which is the main core of the application including code, environment, libraries, tools,... 

To deploy an application on k8s, the application must be encapsulated into container and then deployed inside a pod of kubernete

## **===2| Encapsule the application**

Kafka system is running on Kubernete which manages its elements by the system of pods. Pod is an independent application like the apps on phone. Pods can also communicate with each other thanks to sending messages through pod service( public address). 

To send message to kafka system, the application must be run as a pod in Kubernet. Pod itself can run because it is a complete application, but not depend on the outside libraries like the python code file running on console. So that, firstly, we have to encapsule the producer programe into an application, which contains all things available for run independently.

* Suppose that the name of application file is `producer.py`, rename it into `main.py`

* Prepare file `requirements.txt`:
    * Create new `txt` file
    * List all the libraries that are used in code
    * Save the file into the same folder with the file `main.py`
      
* Prepare file `Dockerfile`:
    * Create new file and set the name `Dockerfile` without extension
    * In the file, config:
      ```Dockerfile
      # Base Image có sẵn Python và các công cụ cơ bản
      FROM python:3.10-slim-bullseye
      
      # 1. CÀI ĐẶT JAVA( OpenJDK 17) VÀ CÁC CÔNG CỤ CƠ BẢN
      RUN apt-get update && \
          apt-get install -y openjdk-17-jre-headless procps && \
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
      
      # 4. COPY CODE
      # Copy các file code của bạn vào Container
      COPY main.py .
      # (Nếu có các file code khác như config.py, hãy thêm vào đây)
      
      # 5. LỆNH CHẠY (ENTRYPOINT)
      # Lệnh này sẽ được thực thi khi Container khởi động
      CMD ["python3", "main.py"]
      ```
   * Save the file into the same folder with the file `main.py`
     
* Encapsule the Programe by Encapsuler: Encapsule by `Docker`: Docker has its core called `Docker Engine` and runs on operator system Linux. `Docker Desktop` is an application providing an interface for user to use `Docker Engine` easier, or user can use `Docker Engine` by CLI:
    * 1 - Install `Docker Desktop`
        * Access the link https://docs.docker.com/desktop/setup/install/windows-install/ and download Docker Desktop Installer for `Windows`
        * Follow the instruction to install `Docker Desktop`. In `Docker Desktop`, there is an engine named `Docker Engine` which is the most important part of the encapsulation
        * Confirm the installation: `docker --version`
        --> Because Docker runs on Linux, when Docker Desktop is installed and activated, tool WSL is automatically activated and installs Ubuntu in Windows. Then, the Docker Desktop will run on this virtual Ubuntu, but not directly on Windows.

    * 3 - Encapsule:
        * Open `Terminal` or `cmd`
        * Login in Docker Desktop, remember the username in Docker Desktop. Ensure the Docker Desktop running.
        * Run instruction to build image:
            ```shell
            docker build -t <lower case of usename of Docker Desktop>/<name of image>:<version: v1/v2/.../latest> `
               <path to folder containing file main.py>
            ```
            --> Wait for minutes, then, there will be an announcement of success. The image will be built and store in local device before being pushed to Docker Hub
        * Push image to docker hub, so that it can be access everywhere:
             ```shell
             docker push <lower case of usename of Docker Desktop>/<name of image>:<version: v1/v2/.../latest>
             ```
        * Confirm the image being pushed successfully:
            * Access `Docker Hub`
            * Sign in
            * This should show the docker image that we have built
## **===2| Deploy the application on Kubernete**

This step is to create and run a pod on Kubernete system, this pod run an container with the image built.

* [1] - Config the file `yaml`:

    * Create a file `yaml` on virtual machine:
        ```bash
        sudo nano kafka-test.yaml
        ```
    * Config the file:
        ```yaml
        apiVersion: apps/v1
        kind: Deployment             # Kind of resource, here using 'Deployment'
        metadata:                     
            name: name-of-deployment # example: kafka-producer-deployment
            namespace: namepace      # example: kafka
            labels:                  # --> label for managing deployment
                app: kafka-producer-management
        spec:
            replicas: 1                            # how many pods that this deployment runs
            selector:                              # define how the deployment find its pods
                matchLabels:                       # --> this means the deployment will find its pod by find the label matched
                    app: name_of_pod_need_to_found # example: kafka-producer  
            template:                     # define struct of a pod
                metadata:
                    labels:               # must be the same as the matchlabel
                        app: kafka-producer         # this must match the labels in selector.matchLabels
                spec:                                          
                    containers:                                                # Define the parameter for container in pod
                    - name: set_name_for_container                             # example: kafka-producer-container
                      image: image_in_docker_hub_that_encapsulates_applications # example: hdoan043/test-kafka:v1 
                    
                      # Đặt Biến Môi trường cho Kafka Broker
                      # Tên service Bootstrap Server của bạn là: my-cluster-kafka-bootstrap:9092
                      # (Dựa trên thông tin kết nối trong image_d5410d.png)
                      env:                                       # Set environment variables 
                      - name: name_of_environment_variable_1     # example: KAFKA_BROKERS
                        value: value_of_environment_variable_1   # example: my-cluster-kafka-bootstrap:9092
                      - name: name_of_environment_variable_2     # example: KAFKA_TOPIC
                        value: value_of_environmetn_variable_2   # example: my-topic  
                    
                      # Nếu producer.py của bạn chạy trong vòng lặp vô hạn, 
                      # Container luôn chạy (Running)
                      resources:                                 # Define resource
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
 
## **===3| Clean and free up storage**

Docker manages all of its data in file `C:\Users\Admin\AppData\Local\Docker\wsl\disk\docker_data.vhdx`. When building image, there are many packages downloaded and saved automatically, making the storage of docker larger, that means the file `docker_data.vhdx` will increase through the time. This may give bad effect on the performance of the local computer because the virtual memory of computer are soon used up. So, the storage need to be cleaned:

* Clean docker image:
  * Check the storage:
    ```bash
    docker system df
    ```
    ---> This shows a table indicating clearly the volume used for each part
    
  * Clean image:
    ```bash
    docker volume ls
    ```
    --> this shows all the volumes used by docker
    --> Clean them by:
    ```bash
    # Delete particular volumes
    docker volume rm <volume_name_1> <volume_name_2> ...
    # <volume_name_1>, <volume_name_2>,... are get by "docker volume ls"

    # Delete all volumes
    docker volume ls -q | Select-String "pack" | ForEach-Object { docker volume rm $_ }
    ```
  * Clean image:
    ```bash
    docker image prune -a --force
    ```
    --> This cleans all the images stored locally. They are saved in Docker Hub by push instruction before.
    
  * Recheck the storage:
    ```bash
    docker system df
    ```
    --> This should show that the storage for `Local volume` and `Images` are `0`

* Free storage: the file `docker_data.vhdx` is bigger through the time because of the automatically downloaded images and packages. Although the above step cleans the volume of docker, the file `docker_data.vhdx` can not be automatically shorten. So that we have to shorten it manually:
  * Open terminal and run:
    ```bash
    wsl --shutdown
    ```
  * Open `diskpart`:
    ```bash
    diskpart
    ```
    --> an other command screen is shown
  * Enter instruction:
    ```bash
    # [1] - Choose file that need to be shorten
    select vdisk file="C:\Users\Admin\AppData\Local\Docker\wsl\disk\docker_data.vhdx"

    # [2] - Change it to the mode read-only
    attach vdisk readonly
    # (!!!) If error: DiskPart has encountered an error: The process cannot access the file because it is being used by another process.
    # --> [2.1] CTRL + Shilf + ESC -> open Task Manager
    # --> [2.2] In the left bar, choose tab "Performance"
    # --> [2.3] In the top right corner, beside the button "Run new task": Click in to the icon of 3 dots -> click into "Resource Monitor"
    # --> [2.4] In the Resource Monitor window, choose tab "CPU"
    # --> [2.5] In the tab "CPU": search "docker_data.vhdx" in section "Associated Handles"
    # --> [2.6] Right click in the item shown and end process
    # --> [2.7] Retry instruction "attach vdisk readonly"

    # [3] - Compress file --> this will remove all of the redundant spaces which are left when cleaning volumes in step 1
    compact vdisk

    # [4] - Detach the file
    detach vdisk

    # [5] - quit
    exit
    ```
* Recheck the storage: open `File Explorer` --> the volume `C:\\` should contain more free storage



