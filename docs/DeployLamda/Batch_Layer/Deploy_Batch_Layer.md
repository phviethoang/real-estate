# **DEPLOY BATCH LAYER**    
<br><br>

Batch layer is responsible for saving raw data persistently. This ensures a back up version of data, and also provides a complete view of all data in history. Thanks to this storage, a batch processing job can be supplied with full data to process and can bring more accuracy result.

To deploy batch layer, `MinIO` is selected as the storage.

## **===1| Deploy MinIO**

`MinIO` is simple, its operator is usually used for complex management, but here, we only need to deploy a single pod.

* Create namespace:
    ```bash
    kubectl create namespace minio
    ```

* Create a file `yaml`:
    ```bash
    sudo nano minio.yaml
    ```

* Config:
    ```yaml
    apiVersion: apps/v1
    kind: Deployment
    metadata:
        name: minio-label
        namespace: minio
    spec:
        replicas: 1
        selector:
            matchLabels:
                app: minio
        template:
            metadata:
                labels:
                    app: minio
            spec:
                containers:
                -   name: minio-container
                    image: minio/minio:latest
                    args:
                    -   server
                    -   /data
                    -   --console-address
                    -   :9001
                    env:
                    -   name: MINIO_ROOT_USER       # must be exactly "MINIO_ROOT_USER"
                        value: "any_username"       # (>=3 characters) optional, this will set the username for minio
                    -   name: MINIO_ROOT_PASSWORD   # must be exactly "MINIO_ROOT_PASSWORD"
                        value: "any_password"       # (>=8 characters) optional, this will set the password for minio
                    ports:
                    -   containerPort: 9000
                    -   containerPort: 9001
                    volumeMounts:
                    -   name: data
                        mountPath: /data
                volumes:
                -   name: data
                    emptyDir: {}
    ```
* Save by `CTRL + S` and exit by `CTRL + X`
* Apply configuration:
    ```bash
    kubectl apply -f minio.yaml -n minio
    ```
* Confirm the pod created successfully:
    ```bash
    kubectl get pods -n minio
    ```
    --> The result should show the minio pod with the field `STATUS` being `Running` and the field `READY` being `1/1`


## **===2| Deploy Service for MinIO**

`MinIO` needs a service to communicate with other pods. Unlike `Kafka` or `ElasticSearch`, `MinIO` does not provide a service, so that the service is deployed seperately.

* Create a `yaml` file
    ```bash
    sudo nano minio-service.yaml
    ```
* Config:
    ```yaml
    apiVersion: v1
    kind: Service
    metadata:
        name: minio-service
        namespace: minio
    spec:
        selector:
            app: minio # This must refer to the name of the pod MinIO: name of the pod MinIO is the value in "spec.template.metadata.labels.app"
        ports:
        -   name: api
            port: 9000
            targetPort: 9000
        -   name: console
            port: 9001
            targetPort: 9001
        type: ClusterIP
    ```
* Save by `CTRL + S` and `CTRL + X` to quit
* Apply configuration :
    ```bash
    kubectl apply -f minio-service.yaml -n minio
    ```
* Confirm the service created successfully by:
    ```bash
    kubectl get svc -n minio
    ```
    --> the result should show the service with the name set in `yaml` file

## **===3| Access to interface of MinIO web**

`MinIO` also provides web to visualize the activies working with it. Expose the port of MinIO to public so that we can access the MinIO:
* Expose:
    ```bash
    kubectl port-forward service/<name of MinIO service: here is "minio-service"> <local port: example "9001">:<public port: "9001"> -n minio
    ```
* Access the web:
    * Access the link http://<PUBLIC_IP_OF_INSTANCE>:<EXPOSED_PORT>
    * Enter username: username config in `minio.yaml`
    * Enter passwork: password config in `minio.yaml`
    