# Airbridge

## Description

Proof-of-concept implementation for forwarding (dataset) events between Airflow instances.

## Overview

Overall architecture:

```mermaid
graph LR
	airflow1(Airflow 1)
	airflow2(Airflow 2)
	broker(Broker)

	airflow1 -->|Send events to| broker
	broker -->|Pull events from| airflow1

	airflow2 -->|Send events to| broker
	broker -->|Pull events from| airflow2
```

Which is implemented as:

```mermaid
graph LR
	airflow1(Airflow 1)
	airflow2(Airflow 2)
	broker(Broker)
	listener[Airflow listener]
	sidecar[Sidecar container]

	listener -->|Listens for dataset events| airflow1
	listener -->|Publishes events on exchange| broker

	sidecar -->|Listens for events on exchange queue| broker
	sidecar -->|Pushes events via REST API| airflow2


```

## Usage

We've created a local Docker-based stack for trying out Airbridge locally. This stack will spin up two Airflow instances together with a local message queue (RabbitMQ).

If you have [`go-task`](https://taskfile.dev/) installed, you can start the Docker stack using the following command:

```
task start
```

After the Docker commands have finished running, you should be able to reach the following two Airflow instances:

* A 'publisher' instance at http://localhost:8080.
* A 'consumer' instance at http://localhost:8081.

Open both Airflow's in your browser, logging in using credentials `airflow`/`airflow`. (You may have to open each instance in it's own browser or browser profile).

## Example

The Docker stack includes two example DAGs:

* An `example_publisher` DAG, owned by the `publisher` instance.
* An `example_consumer` DAG, which is part of the `consumer` instance.

The `example_publisher` DAG will update an example dataset called `my_favorite_dataset`, which should in trigger the `example_consumer` DAG in the `consumer` Airflow instance.

Try this out by triggering a manual run of the `example_publisher` DAG.
