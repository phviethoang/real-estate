# **[Project BigData]Group 26 - Hệ thống thu thập, lưu trữ, xử lý dữ liệu bất động sản**

## **===1| General**

Our subject is to deploy a system of *Hệ thống thu thập, lưu trữ, xử lý dữ liệu bất động sản*. This is our official branch of project. The branch contains scripts and configuration files for Kubernete system.

## **===2| About our project**

We aim at deploying a system which can:
* Automatically crawl data from website `bds.com`
* Store data with availability ensurance
* Provide data for end user while ensuring low latency and data quality

In general, we decided to deploy system based on Lambda Architecture:

```txt
__________________
|   Data sources |                                                
|________________|
        |
        |                                                        
 _______V_________           _________________                                      ____________________
 | Crawler and   |           | Queue: Kafka  |                                      |  Datalake: MinIO |
 |  basic clean  |---------->|_______________|-----------------[Spark]------------->|__________________|
 |_______________|                    |                                                       | 
                                      |                                                       |                  
                                      |                                                       |    
                                [Spark Streaming]                                       [Spark Batch] 
                                      |                                                       |   
                                      |                                                       |
                                      |                                                       |   
                                      |                                                       |  
                                      |                    _________________                  | 
                                      |                    | Serving Layer:|                  |
                                      +------------------->| Elastic Search|<-----------------+
                                                           |_______________| 
                                                                    |
                                                                    |
                                                                    V
                                                                [ User]
```
## **===3| About our repository**

Our repositories contain scripts and configuration of the system which are:
* `Airflows`: folder contains code of airflow - which is responsible for scheduling
* `Config`: The folder of `yaml` file configing the Kubernete system
* `SparkJobs`: Scripts, requirements and Dockerfile of code Spark
* `crawlerbds`: Scripts, requirements of crawler
* `agent-backend` and `frontend`

