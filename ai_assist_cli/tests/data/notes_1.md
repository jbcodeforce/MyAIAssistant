# Company_a

## Team

* Praveen Thakrar: Customer Success Technical Architect
* Thad Martin: AE
* Dave Kline: Staff SE

## Company_a

* John: architect - Flink 
* Casey: ETP architect - More Kafka
* nathan
* Raghu 

## Products

* CC flink
* CP flink
* CP customer for years. 2% of CC only. Million$ in CP. 

## Use cases: 

Claim processing opt, vehicle telematics

## Context

* interested by CC and CPF
* Highly technical team asking for a PoC
* Recommended account team engage STS to help get a CPF POC environment stood up separately from their existing CP footprint. No significant CPF deal size expected right now.
* Two other competitors evaluated, but came back to us.
* Renewal for january
* PoC to complete by October


## Technology stack

* AWS, MSK (shared service team - limited)
* Snowflake
* Confluent may be out - competitive - MSK take out
* Kubernetes
* Red Pandas may have be there
* OSS Kafka and CP
* Iceberg as a sink 
* EKS for dev cluster is now up and running: 11/07.

## Concerns to assess

* Skill level on k8s and Flink: CP Flink may be a no go if no k8s skill
* Risk they get our knowledge and still move to MSF
* PoC should be done on CC to make them get better at Flink

## Past steps

* Define a PoC, CC, CPF on EKS? 
* Architect wants to: Postgresql -> MSK -> Flink -> Iceberg  (fit for purpose goal)
* Data to / from on MSK currently
* More willing to do self managed
* Does not seem to have Flink skill. 
* Analytics data
* Meeting 11/07: secure hand check with confluent cli. TLS on ELB with target group to cmf pod (HTTP traffic). confluent cli to ELB certificate. [ ] Need to open a ticket to support. 

## Next steps

* [] Shared best practices on cluster management in CP, HA, checkpointing, 
* [] RBAC integration with CP, and then get prescription to manage resources for Flink

## Discovery call

* MSK was just for PoC but not mandatory, our team is working 
* Goal to produce locally and consume globaly. Be able to manage. Cluster linking is not manageable.
* CP Flink, vs CC Flink (out of scope) Biggest one: strong confluent cloud dependency on kafka, and not supporting external connectors from Flink.

* Evalutation: Solution needs to work, (AWS services not documentation), simple infrastructure management, not acquired while we are evaluating them. 
* Next generation of event processing at Company_a.
* SQS integration: streams are coming MSK, CDC to MSK, or CDC to a native connector
* JDBC based integration, REST API.
* Kubernetes: EKS auto mode. EBS, EFS, Ingress, EKS, GKS, AKS
* Applications running, and stream processing done before.
* Abstract to manage flink infrastructure: operator, and RDF. But flink app side, Java based Flink app. Developer experience.

* Documentation of how to manage CP Flink: deployment on EKS, 

* Shared responsibility model?
    
    * version management
    * kubernetes resources

* Missing best practice: cluster, HA,  
* Roadmap presentation by Robert - rough edges on SQL
* EKS deployment

### Authentication

* CMF deployment -> error messages
* CP 8.1 - Flink - EKS 

## Questions

! * demo an end-to-end flow on the architecture: components list, devops, monitoring, HA, and app deployment. 
* 12/02: Call with Raghu Manchi for CMF errors




