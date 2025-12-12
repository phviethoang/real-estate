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
      
* Prepare file `project.toml`: This is for some application requiring Java to run
   * Create a file `project.toml`
   * Config:
     ```toml
     [_]
     schema-version = "0.2"
      
     [com.heroku.buildpacks.deb-packages]
     install = [
         "openjdk-17-jre-headless",
         "procps"
     ]
     ```
   * Save the file into the same folder with the file `main.py`

 * Prepare file `.python-version`:
   * Create a file `.python-version`
   * In the file, config the version of python:
     ```txt
     3.10
     ```
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
            ```shell
            pack build <lower case of usename of Docker Desktop>/<name of image>:<version: v1/v2/.../latest> `
                --path . `
                --builder heroku/builder:22 `
                --publish
            ```
            --> Wait for minutes, then, there will be an announcement of success
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

* Clean docker volume:
  * Check the storage:
    ```bash
    docker system df
    ```
    ---> This shows a table indicating clearly the volume used for each part
    
  * Clean volume:
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
  * Recheck the storage:
    ```bash
    docker system df
    ```
    --> This should show that the storage for `Local volume` is `0`

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

    # [3] - Compress file --> this will remove all of the redundant spaces which are left when cleaning volumes in step 1
    compact vdisk

    # [4] - Detach the file
    detach vdisk

    # [5] - quit
    exit
    ```
* Recheck the storage: open `File Explorer` --> the volume `C:\\` should contain more free storage
