# Airbridge

Airflow extension for sharing dataset events across multiple Airflow instances (effectively "bridging" the instances). This allows you to have separate Airflow instances per team, domain, etc. but still have those teams schedule workflows to run whenever other team(s) update their datasets.

## Overview

Airbridge works by forwarding (emitting) dataset events to a central message broker, where these events can be shared with other Airflow instances:

```mermaid
graph LR
  airflow1(Airflow A)
	airflow2(Airflow B)
  airflow3(Airflow C)
	broker(Broker)

	airflow1 -->|Send event| broker
  broker -->|Receive event| airflow2
  broker -->|Receive event| airflow3
```

To forward dataset events to the broker, we use a custom Airflow operator (the `EmitEventOperator`), which automatically forwards any events from upstream tasks to the broker (see the example section for a full code example):

```python
create_dataset_1 = PythonOperator(
    task_id="create_dataset",
    python_callable=lambda: print("Hello world!"),
    outlets=[output_dataset_1],
)

emit_events = EmitEventOperator(task_id="emit_events", conn_id="test")
create_dataset_1 >> emit_events
```

The forwarded events are then picked up by a sidecar container (one per Airflow instance), which listens to the broker and pushes any forwarded events to its corresponding Airflow instance via the Airflow REST API:

```mermaid
graph TB
  airflow1(Airflow A)
	airflow2(Airflow B)
	broker(Broker)
	operator[EmitEventOperator]
	sidecar[Sidecar container]

	airflow1 -->|Trigger| operator
	operator -->|Publish events on exchange| broker

	broker -->|Listen for events on exchange queue| sidecar
	sidecar -->|Push events via REST API| airflow2
```

## Example

To see how this works in practice, let's assume we have two teams: `Team A` and `Team B`. Each of these teams has their own Airflow instance, `Airflow A` and `Airflow B`. Team A is responsible for creating a specific dataset (dataset 1), which Team B wants to consume downstream in one of their DAGs.

To create the dataset, Team A creates the following DAG in Airflow A:

```python
import pendulum
from airflow import DAG
from airflow.datasets import Dataset
from airflow.operators.python import PythonOperator

from airbridge.operators import EmitEventOperator

# Create a dataset reference.
output_dataset_1 = Dataset("local://team_a/dataset_1")

with DAG(
    dag_id="create_datasets",
    schedule=None,
    start_date=pendulum.yesterday(tz="UTC"),
) as dag:
    # Create/update the dataset.
    create_dataset_1 = PythonOperator(
        task_id="create_dataset_1",
        python_callable=lambda: print("Hello world!"),
        outlets=[output_dataset_1],
    )

    # Forward dataset events to the central broker.
    emit_events = EmitEventOperator(task_id="emit_events", conn_id="airbridge_broker")
    create_dataset_1 >> emit_events
```

This DAG simulates the creation of a single dataset, which is tracked under the URI `local://team_a/dataset_1`. The DAG also uses the `EmitEventOperator` to forward the dataset event to the central broker with connection id `test` (see the deployment section below for more details on how to configure this connection).

Altogether this ensures that the broker receives an event whenever the dataset `local://team_a/dataset_1` is updated.

On Team B's side, they can create a regular Airflow DAG that references the dataset from Team A and uses the dataset reference to schedule their DAG:

```python
import pendulum
from airflow import DAG
from airflow.datasets import Dataset
from airflow.operators.python import PythonOperator

input_dataset = Dataset("local://team_a/dataset_1")

with DAG(
    dag_id="process_data_from_team_a",
    schedule=[input_dataset],
    start_date=pendulum.yesterday(tz="UTC"),
):
    PythonOperator(
        task_id="hello_world",
        python_callable=lambda: print("Hello world!"),
    )
```

This DAG runs in their own Airflow instance (Airflow B) and will be triggered whenever a dataset event belonging to the dataset `local://team_a/dataset_1` is received from the broker.

## Demo

To try this out in practice, we've provided a Docker Compose stack for you to run locally. This stack will spin up two Airflow instances together with a local message queue (RabbitMQ) as broker.

If you have [`go-task`](https://taskfile.dev/) installed, you can start the Docker stack using the following command:

```
task start
```

After the Docker commands have finished running, you should be able to reach the following two Airflow instances:

* Team A's instance at http://localhost:8080.
* Team B's instance at http://localhost:8081.

Open both Airflow instances in your browser, logging in using credentials `airflow`/`airflow`. (You may have to open each instance in it's own browser or browser profile).

The Docker stack includes several example DAGs, including:

* A `create_datasets_a` DAG, owned by the `Team A` instance.
* An `process_data_from_team_a` DAG, which is part of the `Team B` instance.

The `create_datasets_a` DAG in the `Team A` will update an example dataset called `local://team_a/dataset_1`, which should in trigger the `process_data_from_team_a` DAG in the `Team B` Airflow instance.

Try this out by triggering a manual run of the `create_datasets_a` DAG from Airflow A and viewing the results in Airflow B.

## Deployment

To deploy Airbridge, you first need to deploy a supported message broker such as RabbitMQ. For an example on how to do this with Docker, see our example in `docker/rabbitmq/docker-compose.yaml`.

Next, you need to build a Docker image for Airflow containing Airflow, Airbridge, and any other Python dependencies you may need.

Once you have this image, you need to make a couple of changes to your existing Airflow deployment:

1. Make sure you use this image when deploying Airflow. For an example of how to do this with Docker Compose, see our example in `docker/airflow/docker-compose.overrides.yaml`.
2. Configure an Airflow connection for the `EmitEventOperator` operator to use when connecting to the broker. For example, using environment variables (which is generally not recommended for security reasons) you do this by adding the following environment variable: `AIRFLOW_CONN_AIRBRIDGE_BROKER=amqp://rabbit:rabbit@rabbitmq:5672/?exchange_name=airbridge`. This creates a connection `airbridge_broker` which you can use with the `EmitEventOperator`.
3. (Optional) Set an Airbridge instance ID for the Airflow instance using the `AIRBRIDGE_INSTANCE_ID` environment variable. Note that this ID should be unique per Airflow instance, as it's used to prevent Airflow instances from receiving their own forwarded events. If you don't configure this environment variable, you can also pass it manually to the operator.
4. Finally, to forward events from the broker to the Airflow instances, you need to setup a sidecar container for each Airflow instance. This sidecar needs to be configured with the same broker URL and exchange name as you used for configuring the operator. Besides this, you also need to pass the Airbridge instance ID of the corresponding Airflow instance (configured in the previous step) and the URL at which the sidecar can reach the Airflow instance. For example, using Docker Compose we end up with the following configuration:

```yaml
services:
  airflow-airbridge:
    image: airflow_airbridge
    build:
      context: ../../
      dockerfile: ./docker/airflow/Dockerfile
    entrypoint: airbridge
    command: |
      --instance-id ${AIRBRIDGE_INSTANCE_ID}
      --broker-url amqp://rabbit:rabbit@rabbitmq:5672
      --exchange-name airbridge
      --airflow-url http://airflow:airflow@airflow-webserver:8080/
    restart: on-failure
    networks:
      - default
      - rabbitmq
```

## FAQ

### Why didn't you use Airflow listeners for sending events instead of the `EmitEventOperator`?

Initially we tried using Airflow listeners for forwarding events. This was quite a nice setup, as it allows you to 'magically' forward events without requiring users to make any changes to their DAGs.

However, a drawback of this approach is that if the listener fails to send an event to the broker, you need to re-run the entire task to retry sending of the event. For long tasks, this is far from ideal. Moreover, failures in listeners are less transparent to debug than a dedicated task, which led us to favor this approach.

If we can alleviate these concerns we're definitely open to exploring the listener route further.
