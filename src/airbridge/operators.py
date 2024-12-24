import asyncio

from airflow.models import DagRun
from airflow.models.baseoperator import BaseOperator
from airflow.models.dataset import DatasetEvent
from airflow.utils.context import Context
from airflow.utils.session import create_session

from airbridge.hooks import RabbitMqHook
from airbridge.model import AirflowDatasetEvent, BridgeDatasetEvent


class RmqPublishEventOperator(BaseOperator):
    def __init__(self, conn_id: str, source_id: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.conn_id = conn_id
        self.source_id = source_id

    def execute(self, context: Context):
        upstream_events = _fetch_dataset_events(
            dag_run=context["dag_run"],  # type: ignore
            task_ids=set(context["task_instance"].task.upstream_task_ids),  # type: ignore
        )

        # TODO: Make this serialization configurable?
        bridge_event_bodies = (
            BridgeDatasetEvent(
                source_id=self.source_id,
                dataset_uri=event.dataset_uri,
                extra=event.extra,
            )
            .model_dump_json()
            .encode()
            for event in upstream_events
        )

        hook = RabbitMqHook(conn_id=self.conn_id)
        asyncio.run(hook.publish(bridge_event_bodies))


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
