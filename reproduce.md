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

See /real-estate/Reproduce/Setup_Kubernete/Setup_Kubernete.md

## **===3| Deploy Lambda system**

* Deploy Streaming Layer: See /real-estate/Reproduce/DeployLamda/Speed_Layer
* Deploy Batch Layer: See /real-estate/Reproduce/DeployLamda/Batch_Layer
* Deploy Serving Layer: See /real-estate/Reproduce/DeployLamda/Serving_Layer
* For scheduling: See /real-estate/Reproduce/DeployLamda/Schedule
