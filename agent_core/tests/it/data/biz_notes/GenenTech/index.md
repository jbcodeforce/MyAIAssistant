# GenenTech

[Genentech](https://www.gene.com/) 

## Products in scope

## Champion and team

* Benny : Lead technical operation team. App and platform supports. Confluent Kafka as a service for developers.
* Harry: Streaming TCS consultant, SDLC and tests, KSQL 

## Confluent:
* AE: 
* SE: Diana Mateescu

Erik Schultz 

## Use case

Work on a lot of Data. Lab is designed around analysis and not data. Data Streaming will be part of 

* Current Event streaming between applications to share async
* Data Streaming for AI model
* CP on EC2 but moving to k8s. 
* KSQL: entities from multi systems, track those entities across data systems, data domains, prioritization of work. Integration on legacy on registry. Domain transform
* Need to build pipeline to change data model
* 3 KSQL streams: CP Flink SQL  7.5.6

* Event Mesh: data lake - sources systems to data mesh - preparing domain. 

* Why it is important?
* Business Unit?
* What prior discussions regarding this use-case have happened in the account in the past?

## Context

## Architecture

* EU and US deployments (named JIRA and PIRA)
* 20 applications running on EKS - some are external systems. Opensearch, and mongodb are 
* Flink will run on k8s.
* 45 src and sink connectors - some supported by the community.
* REST API to write events to kafka 
* Microservices use  Kafka Stream to write events
* AWS MSK or SQS or Event Bridge : repartition rebalancing. 
* 


* What does the end-to-end architecture look like? What are the upstream sources and the downstream destinations? 
* Who is consuming the data and how (application, dashboards, etc.)?
* Do they need exactly-once semantics or is at-least once semantics acceptable?
* What is the expected throughput (messages/sec and bytes/sec)?
* Average message size?
* how many Flink statement forcasted?
* What are their expectations around processing lag during deployments and failure recovery?

## SE Flink goals

## Past Steps

## Next Steps

* [ ] Get their current KSQL 
* [ ] Get Testcases: How we compare the results need to be developed


## Sources of information