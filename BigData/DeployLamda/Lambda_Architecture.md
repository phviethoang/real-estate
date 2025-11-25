# **LAMBDA ARCHITECTURE**
<br><br>

## **WHAT IS LAMBDA ARCHITECTURE?**
---
In fact, data is usually required to be processed in real time ( process immediately). But sometimes, in order to provide more value and information, data should be collected first and then processed. These 2 requirements are conflict. 

**Lambda Architecture** is an architecture for processing big data efficiently with balancing between real-time processing and late processing.

## **LAMBDA ARCHITECTURE**
---
To serve both above requirements, Lambda architecture is designed with 3 layers:
* **Speed Layer**:
    * This is responsible for real-time processing
    * The accuracy provided is just acceptable but not high.
    * The speed is high -> low latecy

* **Batch Layer**:
    * This is responsible for process the whole history of data collected
    * The accuracy provided is absolutely high because it is provided through processing the whole history of data
    * High latency

* **Serving Layer**:
    * This is responsible for merging information of both 2 above layers to serve to end users.

## **DEPOLY LAMBDA ARCHITECTURE**
---
```txt
[1] - Ensuring enviroment
    --> Ensuring *persistant storage*
    --> Set up some additional packages

[2] - Deploying speed layer

```

**~~~ HOW TO DEPLOY APPLICATIONS IN KUBERNETE SYSTEMS? ~~~**

**Operator** is created for helping Kubernete system in deploying applications. It simplifies the installation, progress of setting up and manages configuration of the application. Each application has its own operator, and with different applications, their operators have different responsibility: Operator of Kafka is responsible for creating `StatefulSet`, `Service`,..., Operator of Spark is responsible for supervising the definations of `SparkApplication` and create, delete Pod Spark when being asked, Operator of Cassandra is responsible for automatically managing cluster. So that, users only need to interact with **Operator** instead of interact directly with the application. To work with an application in Kubernete:
* Install its operator through `helm install` --> this operator will run as kubernete pod and supervise kubernete API

* Define application: this is what the users requires about application. The requirements are defined by `yaml` file: for example, in Kafka, users write a file `Kafka.yaml` showing that the application should have 3 brokers. `yaml` file must declare which operator will read it, and thanks to that, the `kubectl` will help with forward this `yaml` file to the right operator( for example: `Kafka.yaml` has to clearly show that its operator is `Kafka Operator` so that the `kubectl` can forward the `Kafka.yaml` to `Kafka Operator`, not `Spark Operator`)

* Then, **Operator** will base on the `yaml` file to work: it will install, set up the application to satisfy the users'requirements. And the resources created by operator have to be known by `kubectl` for management( this progress will be automatic)

Operator is just installed in master node because it is a part of manager of Kubernete, it has to contact with the `kubectl`. The operator will be run as a pod in master node, this pod always run and supervise the work of application. The application ( main application which is supervised by operator) is created as pods and run in worker node with the worker nodes' resources.

**~~~ VISUALIZATION OF HOW THE OPERATOR WORKS ~~~**

```txt
                
_______________MASTER NODE__________________________
|                                                   |
|                           [Operator-1]<-------------------------[yaml file 1 from users]
|                                  |                |
|                [Kube scheduler]  |                |
|                           |      |                |                 
| [Kube controller manager] |      |                |
|               |           |      |  [Operator-2]<---------------[yaml file 2 from users]      
|               |           |      |       |        |  
|               V           V      V       |        |  
|              [ Kube api server  ]<-------+        | 
|________________________|__________________________|
                         |
              +----------+------------------------------+
              |                                         |
    __________|____________                     ________|___________
    |         V            |                    |       V           |           
    | [Application Pod -1] |                    |[Application Pod-1]|
    | [Application Pod -2] |                    |[Application Pod-2]| 
    |______WORKER NODE_____|                    |____WORKER NODE____|


_ [Operator-1] manages [Application Pod -1] in worker nodes
_ [Operator-2] manages [Application Pod -2] in worker nodes
....
```

## **===1| Ensuring environment**
---
### **____ 1.1 ____ Ensuring persistent storage**

#### ***~~~~[Step 1]~~~~* Allow pod to access volumes**
I deploy Kubernete system on cloud. The cloud platform like **AWS**, **GG Cloud**,... manages its resources by abstraction. This means: instead of providing a virtual machine with full equipments of disks, processors,... these cloud platforms provide separate abstractions for parts: class of processors( including many types of processors: `2G RAM`, `4G RAM`, ... ), class of disks( including many types of disks: `2G`, `4G`,...),... When initializing a virtual machine on cloud platform, we have to choose each type for different parts and combine them to construct a machine: choose `2G RAM`, `8G Storage`,... So that, parts of virtual machine are provided independently. 

Because of the above independent parts, by default, the cloud platform blocks the accessment from applications of virtual machine to disks for preventing the disks. This leads to that *pods* of nodes in *Kubernete* cannot access to the disk to manage the storage while *Kubernete pods* require permanent storage for running. So that, we have to set some rules to allow *pods* access the disk.

**~~~ AWS ~~~**

The cloud **AWS** has a system of virtual machines called **instance** - which contains many types of physical infrastructures to choose like RAM,..- and a system of storage called **EBS ( Elastic Block Store)**- which includes types of volume. In AWS, to set new rule for an instance to allow its applications access volumes, we have to follow these steps:
* 1 - Create new policy: this defines the policy which contains some rules and rights allowing access to EBS.
* 2 - Create new role and attach the policy: this defines the role which has the rights and has to follow the rules in policy
* 3 - Attach the role to the instance: this attachs the role to a particular instance, so that the instance can have the right in the policy to access EBS

#### ***~~~~[Step 2]~~~~* Connect pods to disks**

Allowing pods to access and manage storage in disk just means the pods are not blocked when using the storage, but not means they are able to access the storage. To help pods with accessing the volume, we have to install CSI Driver. 

**CSI Driver** is the interface that provided by Ubuntu to help applications in instances in **Cloud platforms** access the EBS through instructions of writing, deleting, reading data from EBS. This means when deploying Kubernete system in local machine, we do not need CSI Driver to access the volume because any applications in local machine can access the physical disks directly.

To install CSI Driver for **AWS**, run this instruction in nodes:

    ```bash
    kubectl apply -k "https://github.com/kubernetes-sigs/aws-ebs-csi-driver/deploy/kubernetes/overlays/stable/"
    ```

This instruction will install some necessary packages for CSI, set up CSI and defaultly create StorageClass

#### ***~~~~[Step 3]~~~~* Create default StorageClass**

**StorageClass** is a design provided by kubernete showing where the pods should ask for storage and how to provide storage to pods. StoreClass is created by default in the above step. 

* To check if the StoreClass has been created :
    ```bash
    kubectl get sc
    ```
    This instruction lists all the storeclass existed
* In case of there is no storeclass, we have to create StorageClass manually:
    * Create new file `yaml`
    ```bash
    sudo nano ebs-sc.yaml
    ```

    * In the `yaml` file, config:
        ```yaml
        # ebs-sc.yaml
        apiVersion: storage.k8s.io/v1
        kind: StorageClass
        metadata:
            name: gp3
            # Thiết lập làm mặc định để các Pod Kafka/Cassandra có thể sử dụng mà không cần chỉ định tên SC
            annotations:
                storageclass.kubernetes.io/is-default-class: "true" 
        provisioner: ebs.csi.aws.com # Tên Provisioner của AWS EBS CSI Driver
        volumeBindingMode: WaitForFirstConsumer
        parameters:
            type: gp3 # Loại ổ đĩa mới, hiệu suất cao của AWS
            fsType: ext4 # Định dạng hệ thống tệp
        ```

    * Apply new configuration:
        ```bash
        kubectl apply -f ebs-sc.yaml
        ```

    * Recheck:
        ```bash
        kubectl get sc
        ```

#### ***~~~~[Additional]~~~~* Visualization of the storage in cloud**
```txt

+-------------------------------------Virtual Machine-------------------------------------+ 
|     +--------------+                       +----Kubernete System------+                 |  
|     |    Pod       |---Ask for storage-----|-+                        |                 |                   
|     +--------------+                       | +--> [StorageClass]  ----------+           |             
|                                            |                          |     |           | 
|                                            +--------------------------+     |           |           
|                                                                             |           |
|                                                                    Supply instructions  |  
|                                                                     & indicate where to |
|                                                                       ask for storage   |  
|                                                                             |           |  
|                             +----Ubuntu Operator System------+              |           |
|                             |                                |              |           |
|                             |           [CSI Driver] <----------------------+           |       
|                             |                |               |                          |  
|                             +----------------|---------------+                          |  
+----------------------------------------------|------------------------------------------+
                                               |
                                        Ask for more volumes
                                               |
+-------Cloud Storage Volume-------------+     | Access is not be blocked
|                                        |     | because of IAM Role
|             [Volume]<------------------------+                          
|                                        |
+----------------------------------------+
```

### **____ 1.2 ____ Install some additional packages**

Install *Helm* for package management. This is similar as `apt` of Ubuntu, `npm` of Node.js. Run this instruction in master node:

```bash
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

## **===2| Deploying speed layer**

Using Kafka to deploying speed layer. Kafka is a queue, plays middle role between producers and consumers. Thanks to this queue storing the messages from producers temporarily, producers can send messages as much as possible but need not to care about the processing ability of consumers. 

To deploy **Kafka**: Read `Speed_Layer.md`

## **===3| Deploying batch layer**

