from typing import AsyncGenerator, Iterable, Optional

from airflow.hooks.base import BaseHook

from .brokers import RmqClient
from .client import AirbridgeClient
from .model import AirbridgeDatasetEvent


class AirbridgeHook(BaseHook):
    def __init__(self, conn_id: str):
        self._conn_id = conn_id

        self._client: Optional[AirbridgeClient] = None

    async def listen(self) -> AsyncGenerator[AirbridgeDatasetEvent, None]:
        async for event in self._get_client().listen():
            yield event

    async def publish(self, events: Iterable[AirbridgeDatasetEvent]):
        await self._get_client().publish(events)

    def _get_client(self) -> AirbridgeClient:
        if self._client is None:
            config = self.get_connection(self._conn_id)

            url = config.get_uri().split("/?")[0]  # Remove parameters from url.
            exchange_name = config.extra_dejson["exchange_name"]

            self._client = AirbridgeClient(
                broker_client=RmqClient(url=url, exchange_name=exchange_name),
            )

        return self._client
