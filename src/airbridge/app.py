import asyncio
import logging
import sys

import httpx
import structlog
import typer
from pydantic import ValidationError

from .clients import RmqClient
from .model import BridgeDatasetEvent

cli = typer.Typer()


@cli.command()
def main(
    instance_id: str = typer.Option(...),
    broker_url: str = typer.Option(...),
    exchange_name: str = typer.Option(...),
    airflow_url: str = typer.Option(...),
):
    _configure_logging()
    asyncio.run(
        _loop(
            instance_id=instance_id,
            broker_url=broker_url,
            exchange_name=exchange_name,
            airflow_url=airflow_url,
        )
    )


def _configure_logging():
    # General logging settings.
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.WARNING,
    )

    # Configure our logging level to a lower level.
    logging.getLogger("airbridge").setLevel(logging.INFO)

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


async def _loop(
    instance_id: str, broker_url: str, exchange_name: str, airflow_url: str
):
    logger = structlog.get_logger()

    broker_client = RmqClient(url=broker_url, exchange_name=exchange_name)
    airflow_client = AirflowClient(url=airflow_url)

    async for message in broker_client.listen():
        try:
            event = BridgeDatasetEvent.model_validate_json(message)
        except ValidationError:
            logger.error("event_parsing_failed", message=message)
            continue

        if event.source != instance_id:
            await airflow_client.create_dataset_event(
                dataset_uri=event.dataset_uri, extra=event.extra
            )
            logger.info(
                "event_forwarded",
                dataset_uri=event.dataset_uri,
                source_id=event.source,
                extra=event.extra,
            )
        else:
            logger.info(
                "event_skipped",
                dataset_uri=event.dataset_uri,
                source_id=event.source,
                extra=event.extra,
            )


class AirflowClient:
    def __init__(self, url: str):
        self._url = url
        self._logger = structlog.get_logger()

    async def create_dataset_event(
        self, dataset_uri, extra=None, raise_not_found: bool = False
    ):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._url}/api/v1/datasets/events",
                json={"dataset_uri": dataset_uri, "extra": extra or {}},
            )

            if not response.is_success:
                if raise_not_found or not (
                    response.status_code == 404
                    and response.json()["title"] == "Dataset not found"
                ):
                    response.raise_for_status()
