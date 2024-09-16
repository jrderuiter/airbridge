import asyncio

import aio_pika
import aio_pika.abc


class RmqPublisher:

    def __init__(self, host: str, exchange_name: str, login: str, password: str, loop=None):
        self._host = host
        self._exchange_name = exchange_name
        self._login = login
        self._password = password
        self._loop = loop

    async def publish(self, body: bytes):
        connection = await aio_pika.connect_robust(
            host=self._host, login=self._login, password=self._password, loop=self._loop or asyncio.get_running_loop()
        )

        async with connection:
            # Creating channel
            channel: aio_pika.abc.AbstractChannel = await connection.channel()

            exchange = await channel.declare_exchange(
                self._exchange_name, aio_pika.ExchangeType.FANOUT, durable=True, auto_delete=False
            )

            await exchange.publish(
                aio_pika.Message(body=body),
                routing_key="dummy",
            )


class RmqConsumer:

    def __init__(self, host: str, exchange_name: str, queue_name: str, login: str, password: str, loop=None):
        self._host = host
        self._exchange_name = exchange_name
        self._queue_name = queue_name
        self._login = login
        self._password = password
        self._loop = loop

    async def listen(self):
        connection = await aio_pika.connect_robust(
            host=self._host, login=self._login, password=self._password, loop=self._loop or asyncio.get_running_loop()
        )

        async with connection:
            # Creating channel
            channel: aio_pika.abc.AbstractChannel = await connection.channel()

            exchange = await channel.declare_exchange(
                self._exchange_name, aio_pika.ExchangeType.FANOUT, durable=True, auto_delete=False
            )

            # Declaring queue
            queue: aio_pika.abc.AbstractQueue = await channel.declare_queue(
                self._queue_name,
                auto_delete=False
            )
            await queue.bind(exchange)

            async with queue.iterator() as queue_iter:
                # Cancel consuming after __aexit__
                async for message in queue_iter:
                    async with message.process():
                        yield message.body
