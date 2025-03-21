from typing import AsyncGenerator, Iterable

from pydantic import ValidationError

from .brokers import BrokerClient
from .model import AirbridgeDatasetEvent


class AirbridgeClient:
    def __init__(self, broker_client: BrokerClient):
        self._broker_client = broker_client

    async def listen(self) -> AsyncGenerator[AirbridgeDatasetEvent, None]:
        async for message in self._broker_client.listen():
            try:
                event = AirbridgeDatasetEvent.from_json(message)
                yield event

            except ValidationError:
                pass  # TODO: Logging

    async def publish(self, events: Iterable[AirbridgeDatasetEvent]):
        bodies = (event.model_dump_json().encode() for event in events)
        await self._broker_client.publish(bodies)
