import asyncio
import os
from typing import Optional

from airflow import DAG
from airflow.models import DagRun
from airflow.models.baseoperator import BaseOperator
from airflow.models.dataset import DatasetEvent
from airflow.utils.context import Context
from airflow.utils.session import create_session

from airbridge.hooks import AirbridgeHook
from airbridge.model import AirbridgeDatasetEvent, AirflowDatasetEvent


def emit_events(
    dag: DAG,
    task_id: str,
    conn_id: str,
):
    tasks_with_outlets = [task for task in dag.tasks if task.outlets]

    if tasks_with_outlets:
        publish_task = EmitEventOperator(task_id=task_id, conn_id=conn_id)
        publish_task.set_upstream(tasks_with_outlets)


class EmitEventOperator(BaseOperator):
    def __init__(
        self, conn_id: str, instance_id: Optional[str] = None, **kwargs
    ) -> None:
        super().__init__(**kwargs)

        if instance_id is None:
            try:
                instance_id = os.environ["AIRBRIDGE_INSTANCE_ID"]
            except KeyError:
                raise ValueError(
                    "An Airbridge instance ID must be provided, either via the source_id parameter"
                    " or via the AIRBRIDGE_INSTANCE_ID environment variable."
                )

        self.conn_id = conn_id
        self.instance_id = instance_id

    def execute(self, context: Context):
        upstream_airflow_events = _fetch_dataset_events(
            dag_run=context["dag_run"],  # type: ignore
            task_ids=set(context["task_instance"].task.upstream_task_ids),  # type: ignore
        )

        bridge_events = (
            AirbridgeDatasetEvent(
                dataset_uri=event.dataset_uri,
                extra=event.extra,
                source_id=self.instance_id,
            )
            for event in upstream_airflow_events
        )

        hook = AirbridgeHook(conn_id=self.conn_id)
        asyncio.run(hook.publish(bridge_events))


def _fetch_dataset_events(
    dag_run: DagRun, task_ids: set[str]
) -> list[AirflowDatasetEvent]:
    with create_session() as session:
        events = (
            session.query(DatasetEvent)
            .filter(
                DatasetEvent.source_run_id == dag_run.run_id,
                DatasetEvent.source_task_id.in_(task_ids),
            )  # type: ignore
            .all()
        )

        return [
            AirflowDatasetEvent(
                dataset_uri=event.dataset.uri,
                extra=event.extra,
            )
            for event in events
        ]
