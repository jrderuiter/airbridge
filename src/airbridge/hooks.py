from typing import AsyncGenerator, Iterable

from airflow.hooks.base import BaseHook

from .clients import RmqClient


class RabbitMqHook(BaseHook):
    def __init__(self, conn_id: str):
        self._conn_id = conn_id

        self._conn = None

    async def listen(self) -> AsyncGenerator[bytes, None]:
        client = self._get_client()
        async for message in client.listen():
            yield message

    async def publish(self, bodies: Iterable[bytes]):
        client = self._get_client()
        await client.publish(bodies)

    def _get_client(self) -> RmqClient:
        if self._conn is None:
            config = self.get_connection(self._conn_id)

            url = config.get_uri().split("/?")[0]  # Remove parameters from url.
            exchange_name = config.extra_dejson["exchange-name"]

            self._conn = RmqClient(url=url, exchange_name=exchange_name)

        return self._conn
