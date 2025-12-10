# **KUBERNET( K8S) DEPLOYMENT**
<BR><BR>

## **INSTRODUCTION**
---

Kubernet or K8s is a tool of managing the activities of a group of nodes. It is responsible for managing: which nodes are dead, how to balance the load of nodes in a cluster,.... And the management is automatic and more believable than manual management.


## **HOW DOES THE KUBERNET MANAGE NODES?**
---

Kubernet is exactly a tool of containers management. This means Kubernet supervises and controls the container running in each node to ensure the work of the whole cluster. 

*Container* is an application which encapsulates fully environment, tools,.... serving for the running. Therefore, containers can be run imediately as an application without manual installing outside tools or libraries like deploying an open-source code. Like applications, there are many types of containers: *Kafka container*, *Spark container*,....

To run containers, in each node must be equiped with the *container runtime*. And kubernet interacts with the *container runtime* to controls all of the containers in each node.

```txt
                                +--------------+
                                |   Kubernet   |
                                +--------------+
                                        |
                +-----------------------+--------------------+
                |                                            |           
+---------------|----------------+          +----------------|---------------+
|   +---Container Runtime----+   |          |   +---Container Runtime----+   |
|   |  +-----------+         |   |          |   |  +-----------+         |   |
|   |  | Kafka     |         |   |          |   |  | Kafka     |         |   |
|   |  | container |         |   |          |   |  | container |         |   |
|   |  +-----------+         |   |          |   |  +-----------+         |   |
|   |       +-----------+    |   |          |   |       +-----------+    |   |
|   |       | Spark     |    |   |          |   |       | Spark     |    |   |
|   |       | container |    |   |          |   |       | container |    |   |
|   |       +-----------+    |   |          |   |       +-----------+    |   |
|   +------------------------+   |          |   +------------------------+   |
+----------NODE------------------+          +----------NODE------------------+

```

## **ELEMENTS OF KUBERNET**
---
The above section only describes the general way to manage nodes in a cluster of Kubernet. In fact, the whole Kubernet system contains more complex elements.

### [1] Control Plane

This is the manager of the whole Kubernet system. It is responsible for scheduling, load balancing,..... 

Control Plane contains:
* `etcd`          : Data structure key-value saves the current configuration state( not data) of the whole cluster. The data and its version or replications is stored in worker nodes.
* `Kube scheduler`: Is responsible for fault tolerance and scheduling for nodes
* `Kube controller manager` : Is responsible for data synchronization
* `Kube apiserver`: is an interface which helps `Kube scheduler` and `Kube controller manager` to communicate with `etcd`

### [2] Worker Node

This is a single node in Kubernet system where the containers are run.

A Worker Node includes:
* `Kubelet` : usually reports its state to `Kube api server` so that `Kube api server` can keep `etcd` up-to-date
* `Kube-proxy`: keep the load balance service of Kubernet work.
* `Container Runtime`: to run container in each node

### Visualization

```txt
            +----------CONTROL PLANE----------+
            |    +-----------+     +--------+ |                     
    +----------> | kube      |---->|  etcd  | |           
    |       |    |  apiserver|     +--------+ |                     
    |       |    +-----------+ <---+          |            
    |       |         ^            |          |  
    |       |   +-----|-----+    +-|--------+ |             
    |       |   | kube      |    | kube     | |
    |       |   | scheduler |    | controler| |
    |       |   + ----------+    +----------+ |
    |       +---------------------------------+
    |    
    |       +----------WORKER NODE------------+
    |       |   +----------+     +----------+ |    
    +---------->| kubelet  |---->| Container| |
            |   +----------+     |  Runtime | |
            |                    +----------+ |
            |   +-----------+                 |
            |   | kube proxy|                 |
            |   +-----------+                 |
            +---------------------------------+
```
## **PIPELINE**

* | 1 | --> Set up Linux 
    * --> Create virtual machines with operating system Linux
            (This virtual machines play roles of master node and worker nodes)
    * --> Start Ubuntu
    * --> Set up Kernel in each node
* | 2 | --> Install cores for Kubernet system 
    * --> Install container runtime in each node
    * --> Install Kubernet cores
* | 3 | --> Set up master node
* | 4 | --> Set up worker node

## **===1| Set up Linux**

### **[SET UP LINUX] | Create Ubuntu virtual machines**

Windows supports us with simulating the operating system Ubuntu by the application **HyperV**. This creates and manages virtual machines. 

**[1] Enable `Hyper-V`**
* Open `PowerShell` as administrator.
* Run this instruction to enable `Hyper-V`
    ```bash
    Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All
    ```
* Restart device if required
    
**[2] Config network connection** 
* After restarting, open **Hyper-V Manager**
* In the left column, choose *ADMIN* or other accounts --> some options will be shown in the right column
* In the right column: 
    * --> Click **Virtual Switch Manager...**
    * --> Choose **External**
    * --> Click **Create Virtual Switch** to create new switch
    * --> Set the name : For example: `k8s Bridge`
    * --> Choose External network adapter: This should be the real network adapter of the physical device. To know the adapter of device: Control Panel -> Network

        Tick **"Allow management operating system to share this network adapter"**
    * --> Click **Apply** to apply configuration to all

**[3] Download an image of Ubuntu**
Hyper-V is a programe helping with deploying virtual machines, but not responsible for the operating system of each virtual machine. To set up the operating system for each virtual machine, we need to separately download an image of operating system. In this step, we have to install OS Linux, so I choose the version **ISO Ubuntu Server 22.04 LTS**. This is Ubuntu for server with only CLI but not graphic interface, so it is lighter.

* Access https://releases.ubuntu.com/jammy/
* Download version 	`ubuntu-22.04.5-live-server-amd64.iso`
* Do not run this `.iso` file. Instead, this file should be run by Hyper - V to set up an operating system

**[4] Create virtual machines**
* In the left column, choose *ADMIN* or other accounts --> some options will be shown in the right column
* In the right column: **New** -> **Virtual machine**
* Set the name for the new virtual machine
* Generation: Choose the second generation
* Memory: at least 2048 MB( 2GB)
* Config network: Choose the virtual network that has been created 
* Hard disk: Creat new virtual hard disk with size of 25GB
* Set up OS:At step *Installation Option*: --> Choose *Install an operating system from a bootable image file* --> browse to `ISO Ubuntu Server 22.04 LTS` that has been downloaded
* **Create**

**[5] Start virtual machine**
In the right column, a section corresponding to the virtual machine has been created -> Click **Start** to run virtual machine, **Shut down** to turn off virtual machine

* If the virtual machine can not be started because of the shortage of memory: 
        * In the section of virtual machine, open **Setting**
        * In setting tab, choose tab **Memory**
        * Set the RAM smaller( 2048 MB ~ 2GB)
        * In section **Dynamic Memory**, set minimum RAM smaller(521 MB), set maximum RAM smaller( 4096 MB ~ 4 GB)
        * Click **Apply** and **OK**

### **[SET UP LINUX] | Start Ubuntu**

* In the right column of Hyper V Manager, in the section of virtual machine -> Click **Start** to run Virtual Machine:

* After the virtual machine run, choose `Connect` to connect with the virtual machine and show the console of Ubuntu Server

* At the first time connecting, we have to set up to installation somethings:

    * [1] - Choose **Try or Install Ubuntu Server** by `UP` and `DOWN` key, `Enter` to tick the selection -> Next step
    * [2] - Select Language and Keyboard -> Next step
    * [3] - Network Configuration: This will show some default network configurations:
        * Name of network interface: `eth0`
        * IP: This is the IP which is automatically provided to virtual machine by Router through DHCP
        
        -> Next step
    * [4] - Set up storage: choose **Use An Entire Disk** and confirm that the size of the disk is the same as the size set up -> **Done** to move to next step
    * [5] - Set up user information:
        * Name
        * Server name
        * Username
        * Password
    * [6] - Install OpenSSH server
    * [7] - Choose the base to install: choose **Ubuntu Server (minimized)**
    * [8] - Choose **Featured server snap**: do not select any options and click **Done**
    * [9] - Install --> this will take a long period of time( ~ > 2h)
    * [10] - After install, the logs are shown and there are 2 options: `View full logs` and `Reboot now`. Click `Reboot now` to start Ubuntu 
    * [11] - Log in with username and password at the above step. Start entering the first Linux instructions.

### **[SET UP LINUX] | Set up Kernel in each node**

* Run and set up Ubuntu in each node
* Turn off SWAP. SWAP is the virtual memory of Linux. If RAM is full, some of data will be stored in virtual memory instead. Therefore, cache of RAM seems to be larger. However, in fact, the data stored in SWAP is more slowly written and read than in real RAM. So that, in order to ensure the performance in cluster, Kubernet requires to turn off the SWAP:

    In Ubuntu console window, run instruction:
    ```bash
    # Turn off SWAP temporarily( SWAP is automatically turned on whenever the device is started)
    sudo swapoff -a
    # Turn of SWAP forever
    sudo sed -i '/ swap / s/^\(.*\)$/#\1/g' /etc/fstab
    ```
* Turn on module `overlay` and module `br_netfilter`. `overlay` is a layering file system( it uses many layers to manage files), this is the platform where the Kubernet bases on to manage files in cluster for effectively storing, reading and writing. `br_netfilter` allows network communication. 

    Open configuration file and config:
    ```bash
    # Open configuration file
    cat <<EOF | sudo tee /etc/modules-load.d/k8s.conf
    overlay
    br_netfilter
    EOF

    sudo modprobe overlay
    sudo modprobe br_netfilter
    ```
* Config the network variables: Open configuration file and config parameter `sysctl`:
    ```bash 
    # Cấu hình tham số sysctl cho mạng Kubernetes
    cat <<EOF | sudo tee /etc/sysctl.d/99-kubernetes.conf
    net.bridge.bridge-nf-call-iptables  = 1
    net.bridge.bridge-nf-call-ip6tables = 1
    net.ipv4.ip_forward                 = 1
    EOF

    sudo sysctl --system
    ```
## **===2| Set up cores for Kubernet system**

This step must be done in all nodes. This will install the necessary modules for master and worker nodes deployment including `kube api server`, `kube scheduler`, `etcd`, `kube controller manager`, `kubelet`, `kube proxy`, `container runtime`
### **[1] Install Container Runtime**

**Docker** is one of the Container Runtimes, it is used to run container. But here, we will use `Containerd` because it is lighter than Docker and is the current standard of Kubernet.

* Linux uses `apt` to install modules in Internet. Update `apt` and install necessary packages:
    ```bash
    sudo apt update
    sudo apt install -y ca-certificates curl gnupg
    ```
* Verify that what we have downloaded is unchanged by the third side: Run
    ```bash
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    ```
* `apt` can download the modules with their repositoris listed in Ubuntu store. Therefore, in order to use `apt` to install `Containerd`, we have to add the its repository to Ubuntu store.

    Run this instruction to set up repository for `Containerd`:
    ```bash
    echo \
    "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
    "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    ```

* Install `Containerd`:
    ```bash
    sudo apt update
    sudo apt install -y containerd.io
    ```

* Set up `Containerd`:
    ```bash
    # Create a default configuration file for containerd
    sudo containerd config default | sudo tee /etc/containerd/config.toml

    # Open file and set the value of parameter `SysteCgroup` from `false` to `true`. This is for avoiding conflict between Containerd and Kubernet
    sudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/g' /etc/containerd/config.toml

    # Restart Containerd so that it can read and apply the new configuration
    sudo systemctl restart containerd
    ```
### **[2] Install Kubernet cores**

Install Kubernet cores : `kubelet`, `kubeadm`, `kubectl`. by the similar way to installing `containerd`:

* Install and set up key for repository of kubernet
    ```bash
    curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.28/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
    echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.28/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list
    ```

* Install packages
    ```bash
    sudo apt update
    sudo apt install -y kubelet kubeadm kubectl
    sudo apt-mark hold kubelet kubeadm kubectl
    ```

## **===3| Set up master node**

This must be set up in the master node

* Initialize Cluster in the master node
    ```bash
    sudo kubeadm init --pod-network-cidr=10.244.0.0/16 --apiserver-advertise-address=<IP_OF_MASTER_NODE>
    ```
* Config Kubectl: when initialize cluster, a block of instructions is provided. Run these instructions to config file `kubectl`:
    ```bash
    mkdir -p $HOME/.kube
    sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
    sudo chown $(id -u):$(id -g) $HOME/.kube/config
    ```
* Set up a pod network:
    ```bash
    kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml
    ```

* To allow the worker node join the cluster, master node of a cluster has to create unique *join command*. Run:
    ```bash
    sudo kubeadm token create --print-join-command
    ```
    --> This will create an instruction `kubeadm join <MASTER_IP>:<PORT> --token <TOKEN> --discovery-token-ca-cert-hash <HASH>`

## **===4| Set up worker node**

* Get the file `admin.conf` from the master node:
  * Set up to allow all traffic between master node and worker node
  * Open a port in worker node to receive file from master node:
    ```bash
    sudo sh -c 'nc -l -p <port: here is 1234> > /etc/kubernetes/admin.conf'
    ```
  * Send file in master node:
    ```bash
    sudo sh -c 'nc <IP_WORKER_NODE> <port: here is 1234> < /etc/kubernetes/admin.conf'
    ```
  * Waiting for a few minutes, then close the port in worker node by `CTRL + C`
    --> the port in master node is also closed automatically
  * Check if the file is sent:
    ```bash
    # Check file existed
    ls /etc/kubernetes
    # --> the result should show a list of files and folders including file 'admin.conf'

    # Check the content of file
    sudo cat /etc/kubernetes/admin.conf
    # --> the file should be exactly the same as the file '/etc/kubernetes/admin.conf' in master node
    ```
    
* Config Kubectl:
  ```bash
  mkdir -p $HOME/.kube
  sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
  sudo chown $(id -u):$(id -g) $HOME/.kube/config
  ```
  
* Join cluster: Run the instruction at the above step to join cluster

* Confirm in master node:
    ```bash
    kubectl get nodes
    ```







