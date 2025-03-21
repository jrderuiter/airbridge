import asyncio
from typing import AsyncGenerator, Iterable, Optional

import aio_pika


class BrokerClient:
    async def listen(self) -> AsyncGenerator[bytes, None]:
        raise NotImplementedError()
        yield b""  # Make this a generator for pyright.

    async def publish(self, bodies: Iterable[bytes]):
        raise NotImplementedError()


class RmqClient(BrokerClient):
    def __init__(
        self,
        url: str,
        # host: str,
        # login: str,
        # password: str,
        exchange_name: str,
        listen_queue_name: Optional[str] = None,
        publish_mandatory: bool = False,
        loop=None,
    ):
        # TODO: Support for conn_id.
        self._url = url
        self._exchange_name = exchange_name
        self._listen_queue_name = listen_queue_name
        self._publish_mandatory = publish_mandatory
        self._loop = loop

    @classmethod
    def from_url(cls, url):
        raise NotImplementedError()

    async def listen(self) -> AsyncGenerator[bytes, None]:
        connection = await self._get_connection()

        async with connection:
            # Creating channel
            channel: aio_pika.abc.AbstractChannel = await connection.channel()

            exchange = await channel.declare_exchange(
                self._exchange_name,
                aio_pika.ExchangeType.FANOUT,
                durable=True,
                auto_delete=False,
            )

            # Declaring queue
            queue: aio_pika.abc.AbstractQueue = await channel.declare_queue(
                self._listen_queue_name, auto_delete=False
            )
            await queue.bind(exchange)

            async with queue.iterator() as queue_iter:
                # Cancel consuming after __aexit__
                async for message in queue_iter:
                    async with message.process():
                        yield message.body

    async def publish(self, bodies: Iterable[bytes]):
        if not self._exchange_name:
            raise ValueError("No exchange name configured")

        connection = await self._get_connection()

        async with connection:
            channel: aio_pika.abc.AbstractChannel = await connection.channel()

            exchange = await channel.declare_exchange(
                self._exchange_name,
                aio_pika.ExchangeType.FANOUT,
                durable=True,
                auto_delete=False,
            )

            for body in bodies:
                # TODO: Check result and handle errors (e.g. returns if Mandatory flag is set).
                await exchange.publish(
                    aio_pika.Message(body=body),
                    routing_key="dummy",
                    mandatory=self._publish_mandatory,
                )

    async def _get_connection(
        self,
    ):
        connection = await aio_pika.connect_robust(
            url=self._url,
            loop=self._loop or asyncio.get_running_loop(),
        )
        return connection
