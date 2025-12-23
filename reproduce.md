# **Reproduce**

To reproduce the project, follow these step:

## **===1| Set up AWS Environment**

* Sign up a new AWS Account, the first time creating AWS account, user is offered 100$. This credit is enough for deploy project
* Create 2 or more instances with operating system being Ubuntu; instance type should be *m7i-flex*
* Create a new Policy providing permision to access EBS (Elastic Block Storage)
* Create a new IAM role attaching to the created Policy
* Attatch IAM role to ALL Instances
* In each security group of each instance: add new inbound rull: accept all request from other instance and all TCP request from outside.

## **===2| Set up Kubernete system**

See [Setup_Kubernete](https://github.com/phviethoang/real-estate/blob/main/docs/Setup_Kubenete/Setup_Kubernete.md)

## **===3| Deploy Lambda system**

* Deploy Streaming Layer: See [Speed_Layer](https://github.com/phviethoang/real-estate/tree/main/docs/DeployLamda/Speed_Layer)
* Deploy Batch Layer: See [Batch_Layer](https://github.com/phviethoang/real-estate/tree/main/docs/DeployLamda/Batch_Layer)
* Deploy Serving Layer: See [Serving_Layer](https://github.com/phviethoang/real-estate/tree/main/docs/DeployLamda/Serving_Layer)
* For scheduling: See [Scheduling](https://github.com/phviethoang/real-estate/tree/main/docs/DeployLamda/Schedule)

