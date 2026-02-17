# ABCD


Consumer amd Community Bank - Dallas

## Products in scope

* CC & CP Flink
* Tableflow

## Champion and team

Matt TheBuilder(confluent champion)

ABCD is already a Confluent Cloud customer with dedicated Kafka clusters and operates mature, production-scale Flink applications including real-time offer aggregation (1.5B events/day) and lending eligibility determination systems.

* Kadwa
* Vadakattu
* Andalam 
* George

Runs on OSS Flink with a Custom DSL on top of DataStream

## Confluent:
* AE: Tom 
* SE: Chris
* Martin: PM Tableflow
* 

## Use case

ABCD Consumer and Community Banking (CCB) Continuum group is evaluating Confluent Cloud Flink as a platform for their stream processing workloads. The Continuum team currently operates production Flink applications built using a custom Domain-Specific Language (DSL) on top of the Apache Flink DataStream API.

**This evaluation focuses on determining whether Confluent Cloud Flink's SQL and Table API can effectively express their existing processing patterns, enabling migration from their custom DSL to standard, maintainable APIs.**


## Context

* CA at Matt Hawk (confluent champion): 2000 apps on Kafka - PaaS
* Need to Standardize on Flink. Consumer bank runs Flink oss
* **Portability**: cloud and on-premise 
* 2 PoCs: one for CC & CP
* DRI () leading a CP Flink PoC (Robert is helping)
* CC Flink PoC (consumer bank) - 3 weeks ( from now to end-)
* 2026 plannification
* [13 items to address to plan PoC](https://docs.google.com/document/d/1-RJzeg-pBeLt7FVFoTE8Y_kr9kBCzHMlVumyD1NUbrI/edit?tab=t.0)
* 2 days sessions: + Hands on (CCB Continuum)
* PoC Feature comparison between CC - OSS Flink
* Chase card tx app: Sapian rule engine - Pay over time - With Cassanda embedded in Flink
* CP flink will be operational first. 
* TableFlow 
* AWS - EKS
* Multi regions and multi cloud

* To Do
    * Review 13 points and build a plan for PoC/ how to test / success criteria - Enablement / Practices
    * Clarify on the how.


## Architecture

### Current Environment:
* Open-source Apache Flink on AWS EKS (ABCD Atlas infrastructure)
* Custom DSL built on top of Flink DataStream API
* Gaia Kafka Clusters (Confluent Platform) in ABCD-managed Data Centers
* Monitoring via Prometheus and Splunk
ABCD is already a Confluent Cloud customer with dedicated Kafka clusters and operates mature, production-scale Flink applications including real-time offer aggregation (1.5B events/day) and lending eligibility determination systems.

* Glue catalog replication
* S3 bucket replication has 15 min latency.
* Currently write to one region as active, replicate to the others. The other region is also active for other apps. For Flink OSS, they replicate checkpoints.

### Future

* No need to do active/passive, RTO at 0 but not RPO. Kafka source of trusth
* Kubernetes Operator not being part of their platform. 
* Instrastructure focus not business use cases
* How to solve in CP ? Tableflow will be done in the future, but not features at the same level.  Warpstream will be the tableflow for CP. But the support for upsert will not be done quickly. Warpstream can push data to iceberg, but catalog is not there. But we can push to 
* Need to have parity of features.
* Cluster link between CP and CC kafka, and also private linking.
* What is the lake house. 
* CP flink - Datastream api asset (?) 

## Past Steps

* PoC done by ABCD
* Integration Storage S3 for Tableflow 
* IAM static access is a no-go - AWS IAM Role or secret key-secret
* Tableflow synch to Glue Catalog with the database name being the kafka cluster id and table being the topic
* Tableflow has an elevate access control on AWS Glue.
=> need to change the database name mapped to the cluster and not the clusterid - AWS Glue table and database should be defined upfront.
=> Compact


## Next Steps

* Multi-regions
* Catalog integration
* 1/21 & 1/22: workshop session. 
    * Day 1: Enablement/discussion sessions - Confluent listening to ABCD requirements, whiteboarding 
    * Day 2: Hands-on POC testing scenarios. Topics: Self-managed Flink vs Confluent Cloud Flink, HA across AZs, multi-region for DR, metrics/monitoring, TableFlow integration patterns


* [x] OSS Flink on EKS versus Confluent Cloud Flink
* [x] Platform Resiliency Strategies - high availability (multi-AZ), multi-region, and disaster recovery
* [ ] Best practices for error detection, reporting, and automated recovery in managed Flink
* [ ] Metrics and Monitoring Integration
* [x] Data Lake Integration Patterns
* [x] Schema Evolution Processes
* [ ] Trusted Data Quality (TDQ) Capabilities

* [ ] Hands-on: UDF deployed and executing in CC Flink
* [ ] Hands-on: Iceberg Integration with Tableflow
* [ ] Hands-on: CEP features with relevant use cases (pattern detection, event sequences
* [ ] Hands-on: Stateful Processing: aggregation with windowing for Fraud detection
* [ ] Hands-on: Exactly-Once Semantics and Reconciliation
* [ ] Hands-on: Validate CDC source connectors for Aurora Postgres and Cassandra
* [ ] Be able to demonstrate CP deployment.
* [ ] Review flink role RBAC

## Subjects they want to cover

### Platform Integration & Operations

* Evaluate Flink Deployment Options: Compare managed and serverless Flink models for compute parity and operational fit.
* Assess Platform Resiliency Strategies: Review approaches for high availability (multi-AZ) and disaster recovery (multi-region).
* Review Exception and Error Handling Mechanisms: Discuss best practices for error detection, reporting, and automated recovery.
* Explore Metrics and Monitoring Integration: Identify methods to integrate Confluent metrics with ABCD tools (Prometheus, Splunk) for alerting and log management.
* Discuss Data Lake Integration Patterns: Examine direct write approaches to Data Lake (Glue, Iceberg) and ensure interoperability.
* Identify Approaches for Custom Transformations: Discuss support and implementation patterns for “bring your own transform.”
* Examine Iceberg Integration Scenarios: Review writing from Confluent Tableflow to Data Lake, reading from Spark, and IRC options (Glue, Polaris).
* Deep-Dive into Complex Event Processing (CEP) Capabilities: Explore supported CEP features and relevant use cases.
* Analyze Stateful Processing for Advanced Use Cases: Focus on stateful processing requirements, such as fraud detection.
* Understand Recon and Exactly-Once Processing: Review mechanisms for achieving exactly-once semantics and reconciliation workflows.
* Clarify Schema Evolution Processes: Gain insights into schema evolution, compatibility, and migration strategies.
* Discuss Change Data Capture (CDC) Connector Support: Review available source connectors for Aurora Postgres and Cassandra.
* Review Trusted Data Quality (TDQ) Capabilities: Discuss platform support for data quality measurement, reporting, and reconciliation

## Workshop notes 01/21

* Databricks is managed by CDO 
* Iceberg Table is CBB
* 200 current stream jobs 
* Design time vs runtime separation
    * schema evolution must be governed with design time valdiations and approvals
    * tableflow must not create new tables or datbases
    * tableflow could not change table schema no alter
    * tableflow to access a custom credential token
    * need to have fine grained RBAC/ABAC controls at the table level
* CC writing runtime data -> fine
* For topic there is a first step to define all the metadata and then later create the topic in the cluster
* create iceberg. 
* How to reuse an existing iceberg tables? 
* Glue and Unity catalog is bi-direction
* Nsaming convention between kafka and iceberg tables are different
* Design of the iceberg table up front - model registry - logical model to n physical models: iceberg, kafka are different physical models. 
* In AWS there is a storage account and a catalog account.
* Lake formation is used for autho and authorization.
* There is a any oAuth support in CP done, needs to the same for CC. not just IAM model. Moving from OAuth. 
* Confluent S3 connector has oauth support
* Client side encryption is done for a field in the schema - no support of all records encryption.This is done at the SerDes level. But they need decryption at write for iceberg table. 
* there will be the concept of catalog of catalogs. 
* Bi-direction catalog synch is to report create table. second SLA. Schema evolution 
* Creation table is done at design time - 
* Datastream Flink logic is doing dedup - transformation for flattening. Gaia KS kafka but will be migrate to CC. 
* Application decryption at the record level, and some has at the field level.
* SLA for flink and kafka topic
* TTL how far tableflow is behind. 
* Iceberg lookup and join from Flink
* TDQ: kafka schema validation - Hive table validation too
* dbt does not seem to be accepted
* currently spark job is own by the owner/tenant of the job, so it needs to have their own iam role to assume remote role.
* iam role per platform is fine but how to be able to report who was running this streaming to write to a s3 bucket.


## Sources of information