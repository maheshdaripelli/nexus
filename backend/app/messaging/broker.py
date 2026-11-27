import asyncio
import json
import ssl
import aio_pika
from pamqp.commands import Basic
from app.core.config import settings

EXCHANGE = "nexus.commands"
QUEUE = "nexus.email.invitation"
KEY = "email.invitation"
DLX = "nexus.dead"
DLQ = "nexus.email.invitation.dead"

async def connect():
    if not settings.RABBITMQ_URL.startswith("amqps://"):
        raise ValueError("Configure an AMQPS URL")
    return await aio_pika.connect_robust(
        settings.RABBITMQ_URL, timeout=10, ssl_context=ssl.create_default_context()
    )

async def topology(channel):
    exchange = await channel.declare_exchange(EXCHANGE, aio_pika.ExchangeType.DIRECT, durable=True)
    dead = await channel.declare_exchange(DLX, aio_pika.ExchangeType.DIRECT, durable=True)
    dlq = await channel.declare_queue(DLQ, durable=True)
    await dlq.bind(dead, routing_key=KEY)
    queue = await channel.declare_queue(QUEUE, durable=True, arguments={
        "x-dead-letter-exchange": DLX, "x-dead-letter-routing-key": KEY,
    })
    await queue.bind(exchange, routing_key=KEY)
    return exchange, queue

class Broker:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchange = None
        self.lock = asyncio.Lock()

    async def ready(self):
        async with self.lock:
            if self.connection is None or self.connection.is_closed:
                self.connection = await connect()
                self.channel = None
            if self.channel is None or self.channel.is_closed or self.exchange is None:
                self.channel = await self.connection.channel(publisher_confirms=True, on_return_raises=True)
                self.exchange, _ = await topology(self.channel)
            return self.exchange

    async def publish(self, invitation_id, token):
        exchange = await self.ready()
        result = await exchange.publish(aio_pika.Message(
            body=json.dumps({"invitation_id": str(invitation_id), "token": token}).encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            message_id=str(invitation_id),
        ), routing_key=KEY, mandatory=True, timeout=10)
        if not isinstance(result, Basic.Ack):
            raise RuntimeError("Publish not confirmed")

    async def close(self):
        if self.connection is not None:
            await self.connection.close()
