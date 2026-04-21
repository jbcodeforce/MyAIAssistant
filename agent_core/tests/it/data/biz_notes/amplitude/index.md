# Amplitude Flink Opp

06/17/2025

* AE: Tony Palmer, SE Amanda Gilbert

## Account opportunity

*

## Context

[Amplitude ](https://amplitude.com/digital-analytics-platform) offers a Digital Analytics Platform to get customer insights.

* Some of their customers have latency issue. 50 minutes from sources to destination 
* Want to optimize cost
* They are exploring non-streaming solutions.
* A key operational pain point that was explicitly raised is the **difficulty of achieving balanced workloads across broker cores** in Redpanda. It looks RedPanda is not load-aware leading to hot spots on the cluster's brokers.
* Look to get long term partner relationship with Confluent: 
    * Tiered Streaming: Using Confluent for different data types across various latency tiers, such as slower, less critical data from data warehouses.
    * AI Collaboration: Exploring how to leverage Confluent's experience with AI-first companies to build out their own AI applications and best practices.

## EA Asks

* Is Flink a good platform to stream between clusters?.

## Architecture information

* Using two-stage architecture built around distinct Kafka-protocol clusters named **Kirby** (the primary ingress cluster (redPanda)) and **Portal** (a secondary fan-out cluster).
* Kirby: Redpanda on 21 [m7gd.16xlarge](https://aws.amazon.com/ec2/instance-types/m7g/) AWS EC2 instances.
* Portal:  self-managed Apache Kafka deployment running directly on EC2 instances: 150 i4i.4xlarge EC2 instances,  totaling approximately 2,500 cores. First problem: it is running at only ~15%. Need bigger machines to get the amount of locally attached disk storage that came with them.

* After AWS ALB, there are java apps running on EC2, that do compressions and produce to kafka
* Once data lands in the Kirby cluster, a series of internal Java-based processors perform "modification and enhancement on the data" and then produce the transformed messages into the Portal cluster.
* The five topics in the Kirby cluster are configured with three topics at 1024 partitions each and two topics at 256 partitions each.
* The Portal cluster then serves to "fan out the data for other purposes" to various downstream systems and business logic.
* Company is standardizing on Kubernetes for all new self-hosted services.
* Accepted Latency for Kirby cluster: An end-to-end P95 produce latency in the 20-40 milliseconds. This end-to-end number includes their own server-side application logic (compression, metrics). The raw produce latency reported by the Redpanda metric itself is only a single-digit millisecond figure (~2ms).
* Cost of Throughput: Higher produce latency would require them to run a larger, more expensive fleet of front-end producer servers to achieve the same total throughput.
* The data volume is "relatively sinusoidal" over a 24-hour period, directly corresponding to U.S. business hours and waning at night.
* Two topics account for approximately 97% of the total load.
* No partition is more than twice the size of another within a given topic.
* they have implemented their **own client-side throttling logic** on the producer side. 
*  For upgrades or migrations, they perform "full failovers" in a blue-green fashion.  They stand up a new cluster, stop writes to the old one, and redirect traffic to the new one. The systems and infrastructure to execute this are already in place
* They have no multi-region DR strategy currently in place.

## Challenges to move to CC

* Any cross-AWS-account networking solution would have "unacceptable" latencies.
* groups the two clusters to reduce latency.
* Need to get visibility of the transformation done
* Can we get a 1 minute 
* 
