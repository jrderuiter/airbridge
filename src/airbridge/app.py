import asyncio
import logging
from pydantic import ValidationError

import typer

from .clients.airflow import AirflowClient
from .clients.rabbitmq import RmqConsumer
from .config import get_settings
from .model import BridgeDatasetEvent

cli = typer.Typer()


async def _loop():
    logger = logging.getLogger()

    settings = get_settings()

    if settings.airflow is None:
        raise ValueError("Missing Airflow settings (e.g. AIRBRIDGE__AIRFLOW__HOST, etc.)")

    rmq_client = RmqConsumer(
        host=settings.broker.host,
        login=settings.broker.login,
        password=settings.broker.password,
        exchange_name=settings.broker.exchange,
        queue_name=f"{settings.broker.queue_prefix}_{settings.general.instance_id}",
    )

    airflow_client = AirflowClient(
        host=settings.airflow.host,
        port=settings.airflow.port,
        login=settings.airflow.login,
        password=settings.airflow.password
    )

    instance_id = settings.general.instance_id

    async for message in rmq_client.listen():
        try:
            event = BridgeDatasetEvent.model_validate_json(message)
        except ValidationError:
            logger.error("Failed to parse message: %s", message)
            continue

        logger.debug("Recevied event: %s", event)

        if event.source != instance_id:
            logger.info(f"Forwarding event for dataset {event.dataset_uri} from {event.source} to {instance_id}")
            await airflow_client.create_dataset_event(event.dataset_uri, extra=event.extra)
        else:
            logger.info("Skipping own event")


@cli.command()
def main():
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(message)s',
    )
    asyncio.run(_loop())
