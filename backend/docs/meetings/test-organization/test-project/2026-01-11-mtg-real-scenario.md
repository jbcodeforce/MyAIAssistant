Greg, Michael, Chris, + 8 people
meeting transcript
While Confluent provides metrics and some tracing, there are gaps in visibility when statements degrade.

Degrading statement - too many, too much state -> better observability - what can a customer can do on degraded. See my deeper dive

rder of joins matters because each join creates a materialized view that needs to be updated efficiently

possible to get visibility of internal operator state of degrated statement, query profiler is blind. Also the metrics are empty in QP even if the statement is running.

The team discussed issues with Kafka lag and data processing, including challenges with offset tracking and message counts. They explored problems with the Confluent Kafka connector and Debezium connector, particularly regarding upserts and append-only operations.

currently production 5,6 pipelines to search - 7 compute pols

even in kafka the consumer lag may reach a level and does not go down.

Kakfa Connector:

CDC debezium -> topic upsert -> to append

Complexity of the RBAC -

OpenSearch is one of the sink, and need a big json - could also be done in sink connector.

Problem of Java skill in the team - more Python knowledge.

The Debezium topic upsert issue can be found in this support issue: https://confluent.zendesk.com/agent/tickets/319543

TableAPI is trying to REST api - organizationId on cp-flink ? patch a statement.

confluent cli - completed and get the warning like result

https table api not supporting http, setting https goes to 443, but if we set https we can use our port.

apache-flink python support on cloud

obsersability

interceptor to get traces for end to end. Debezium CDC get

Lineage: data lineage not present - sql OSS